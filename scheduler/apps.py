from __future__ import unicode_literals

from django.apps import AppConfig
try:
    from django.db.models.functions import Now
except ImportError:
    from django.utils.timezone import now as Now
from django.utils.translation import ugettext_lazy as _


class SchedulerConfig(AppConfig):
    name = 'scheduler'
    verbose_name = _('Django RQ Scheduler')

    def ready(self):
        try:
            self.reschedule_repeatable_jobs()
            self.reschedule_scheduled_jobs()
        except:
            # Django isn't ready yet, example a management command is being
            # executed
            pass

    def reschedule_repeatable_jobs(self):
        RepeatableJob = self.get_model('RepeatableJob')
        jobs = RepeatableJob.objects.filter(enabled=True)
        self.reschedule_jobs(jobs)

    def reschedule_scheduled_jobs(self):
        ScheduledJob = self.get_model('ScheduledJob')
        jobs = ScheduledJob.objects.filter(
            enabled=True, scheduled_time__lte=Now())
        self.reschedule_jobs(jobs)

    def reschedule_jobs(self, jobs):
        for job in jobs:
            if job.is_scheduled() is False:
                job.save()
