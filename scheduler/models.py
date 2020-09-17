from __future__ import unicode_literals

import importlib
from datetime import timedelta

import croniter
import django_rq
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.templatetags.tz import utc
from django.utils.encoding import python_2_unicode_compatible
from django.utils.timezone import now
from django.utils.translation import ugettext_lazy as _
from model_utils import Choices
from model_utils.models import TimeStampedModel

RQ_SCHEDULER_INTERVAL = getattr(settings, "DJANGO_RQ_SCHEDULER_INTERVAL", 60)


@python_2_unicode_compatible
class BaseJob(TimeStampedModel):

    name = models.CharField(_('name'), max_length=128, unique=True)
    callable = models.CharField(_('callable'), max_length=2048)
    enabled = models.BooleanField(_('enabled'), default=True)
    queue = models.CharField(_('queue'), max_length=16)
    job_id = models.CharField(
        _('job id'), max_length=128, editable=False, blank=True, null=True)
    repeat = models.PositiveIntegerField(_('repeat'), blank=True, null=True)
    timeout = models.IntegerField(
        _('timeout'), blank=True, null=True,
        help_text=_(
            'Timeout specifies the maximum runtime, in seconds, for the job '
            'before it\'ll be considered \'lost\'. Blank uses the default '
            'timeout.'
        )
    )
    result_ttl = models.IntegerField(
        _('result ttl'), blank=True, null=True,
        help_text=_('The TTL value (in seconds) of the job result. -1: '
                    'Result never expires, you should delete jobs manually. '
                    '0: Result gets deleted immediately. >0: Result expires '
                    'after n seconds.')
    )

    def __str__(self):
        return self.name

    def callable_func(self):
        path = self.callable.split('.')
        module = importlib.import_module('.'.join(path[:-1]))
        func = getattr(module, path[-1])
        if callable(func) is False:
            raise TypeError("'{}' is not callable".format(self.callable))
        return func

    def clean(self):
        self.clean_callable()
        self.clean_queue()

    def clean_callable(self):
        try:
            self.callable_func()
        except TypeError as e:
            raise ValidationError({
                'callable': ValidationError(
                    _('Invalid callable, must be importable'), code='invalid')
            })

    def clean_queue(self):
        queue_keys = settings.RQ_QUEUES.keys()
        if self.queue not in queue_keys:
            raise ValidationError({
                'queue': ValidationError(
                    _('Invalid queue, must be one of: {}'.format(
                        ', '.join(queue_keys))), code='invalid')
            })

    def is_scheduled(self):
        if not self.job_id:
            return False
        return self.job_id in self.scheduler()
    is_scheduled.short_description = _('is scheduled?')
    is_scheduled.boolean = True

    def save(self, **kwargs):
        self.schedule()
        super(BaseJob, self).save(**kwargs)

    def delete(self, **kwargs):
        self.unschedule()
        super(BaseJob, self).delete(**kwargs)

    def scheduler(self):
        return django_rq.get_scheduler(self.queue, interval=RQ_SCHEDULER_INTERVAL)

    def is_schedulable(self):
        if self.job_id:
            return False
        return self.enabled

    def schedule(self):
        self.unschedule()
        if self.is_schedulable() is False:
            return False

    def unschedule(self):
        if self.is_scheduled():
            self.scheduler().cancel(self.job_id)
        self.job_id = None
        return True

    class Meta:
        abstract = True


class ScheduledTimeMixin(models.Model):

    scheduled_time = models.DateTimeField(_('scheduled time'))

    def schedule_time_utc(self):
        return utc(self.scheduled_time)

    class Meta:
        abstract = True


class ScheduledJob(ScheduledTimeMixin, BaseJob):
    repeat = None

    def schedule(self):
        result = super(ScheduledJob, self).schedule()
        if self.scheduled_time < now():
            return False
        if result is False:
            return False
        kwargs = dict()
        if self.timeout:
            kwargs['timeout'] = self.timeout
        if self.result_ttl is not None:
            kwargs['job_result_ttl'] = self.result_ttl
        job = self.scheduler().enqueue_at(
            self.schedule_time_utc(),
            self.callable_func(),
            **kwargs
        )
        self.job_id = job.id
        return True

    class Meta:
        verbose_name = _('Scheduled Job')
        verbose_name_plural = _('Scheduled Jobs')
        ordering = ('name', )


class RepeatableJob(ScheduledTimeMixin, BaseJob):

    UNITS = Choices(
        ('seconds', _('seconds')),
        ('minutes', _('minutes')),
        ('hours', _('hours')),
        ('days', _('days')),
        ('weeks', _('weeks')),
    )

    interval = models.PositiveIntegerField(_('interval'))
    interval_unit = models.CharField(
        _('interval unit'), max_length=12, choices=UNITS, default=UNITS.hours
    )

    def clean(self):
        super(RepeatableJob, self).clean()
        self.clean_interval_unit()
        self.clean_result_ttl()

    def clean_interval_unit(self):
        if RQ_SCHEDULER_INTERVAL > self.interval_seconds():
            raise ValidationError(
                _("Job interval is set lower than %(queue)r queue's interval."),
                code='invalid',
                params={'queue': self.queue})
        if self.interval_seconds() % RQ_SCHEDULER_INTERVAL:
            raise ValidationError(
                _("Job interval is not a multiple of rq_scheduler's interval frequency: %(interval)ss"),
                code='invalid',
                params={'interval': RQ_SCHEDULER_INTERVAL})

    def clean_result_ttl(self):
        """
        Throws an error if there are repeats left to run and the result_ttl won't last until the next scheduled time.
        :return:
        """
        if self.result_ttl != -1 and self.result_ttl < self.interval_seconds() and self.repeat:
            raise ValidationError(
                _("Job result_ttl must be either indefinite (-1) or "
                  "longer than the interval, %(interval)s seconds, to ensure rescheduling."),
                code='invalid',
                params={'interval': self.interval_seconds()},)

    def interval_display(self):
        return '{} {}'.format(self.interval, self.get_interval_unit_display())

    def interval_seconds(self):
        kwargs = {
            self.interval_unit: self.interval,
        }
        return timedelta(**kwargs).total_seconds()

    def _prevent_duplicate_runs(self):
        """
        Counts the number of repeats lapsed between scheduled time and now
        and decrements that amount from the repeats remaining and updates the scheduled time to the next repeat.
        :return:
        """
        while self.scheduled_time < now() and self.repeat and self.repeat > 0:
            self.scheduled_time += timedelta(seconds=self.interval_seconds())
            self.repeat -= 1

    def schedule(self):
        result = super(RepeatableJob, self).schedule()
        self._prevent_duplicate_runs()
        if self.scheduled_time < now():
            return False
        if result is False:
            return False
        kwargs = dict(
            interval=self.interval_seconds(),
            repeat=self.repeat
        )
        if self.timeout:
            kwargs['timeout'] = self.timeout
        if self.result_ttl is not None:
            kwargs['result_ttl'] = self.result_ttl
        job = self.scheduler().schedule(
            self.schedule_time_utc(),
            self.callable_func(),
            **kwargs
        )
        self.job_id = job.id
        return True

    class Meta:
        verbose_name = _('Repeatable Job')
        verbose_name_plural = _('Repeatable Jobs')
        ordering = ('name', )


class CronJob(BaseJob):
    result_ttl = None

    cron_string = models.CharField(
        _('cron string'), max_length=64,
        help_text=_('Define the schedule in a crontab like syntax. Times are in UTC.')
    )

    def clean(self):
        super(CronJob, self).clean()
        self.clean_cron_string()

    def clean_cron_string(self):
        try:
            croniter.croniter(self.cron_string)
        except ValueError as e:
            raise ValidationError({
                'cron_string': ValidationError(
                    _(str(e)), code='invalid')
            })

    def schedule(self):
        result = super(CronJob, self).schedule()
        if result is False:
            return False
        kwargs = dict(
            repeat=self.repeat
        )
        if self.timeout:
            kwargs['timeout'] = self.timeout
        job = self.scheduler().cron(
            self.cron_string,
            self.callable_func(),
            **kwargs
        )
        self.job_id = job.id
        return True

    class Meta:
        verbose_name = _('Cron Job')
        verbose_name_plural = _('Cron Jobs')
        ordering = ('name', )
