from __future__ import unicode_literals

from django.conf import settings
from django.contrib import admin, messages
from django.templatetags.tz import utc
from django.utils.timezone import now
from django.utils.translation import ugettext_lazy as _

from scheduler.models import CronJob, RepeatableJob, ScheduledJob

QUEUES = [(key, key) for key in settings.RQ_QUEUES.keys()]


class JobAdmin(admin.ModelAdmin):
    actions = ['delete_model', 'disable_selected', 'enable_selected', 'run_job_now']
    list_filter = ('enabled', )
    list_display = ('enabled', 'name', 'job_id', 'is_scheduled',)
    list_display_links = ('name',)
    readonly_fields = ('job_id', )
    fieldsets = (
        (None, {
            'fields': ('name', 'callable', 'enabled',),
        }),
        (_('RQ Settings'), {
            'fields': ('queue', 'job_id',),
        }),
    )

    def get_actions(self, request):
        actions = super(JobAdmin, self).get_actions(request)
        actions.pop('delete_selected', None)
        return actions

    def get_form(self, request, obj=None, **kwargs):
        queue_field = self.model._meta.get_field('queue')
        queue_field.choices = QUEUES
        return super(JobAdmin, self).get_form(request, obj, **kwargs)

    def delete_model(self, request, queryset):
        rows_deleted = 0
        for obj in queryset.all().iterator():
            obj.delete()
            rows_deleted += 1
        if rows_deleted == 1:
            message_bit = "1 job was"
        else:
            message_bit = "%s jobs were" % rows_deleted

        level = messages.WARNING if not rows_deleted else messages.INFO
        self.message_user(request, "%s successfully deleted." % message_bit, level=level)
    delete_model.short_description = _("Delete selected %(verbose_name_plural)s")
    delete_model.allowed_permissions = ('delete',)

    def disable_selected(self, request, queryset):
        rows_updated = 0
        for obj in queryset.filter(enabled=True).iterator():
            obj.enabled = False
            obj.save()
            rows_updated += 1
        if rows_updated == 1:
            message_bit = "1 job was"
        else:
            message_bit = "%s jobs were" % rows_updated

        level = messages.WARNING if not rows_updated else messages.INFO
        self.message_user(request, "%s successfully disabled." % message_bit, level=level)
    disable_selected.short_description = _("Disable selected %(verbose_name_plural)s")
    disable_selected.allowed_permissions = ('change',)

    def enable_selected(self, request, queryset):
        rows_updated = 0
        for obj in queryset.filter(enabled=False).iterator():
            obj.enabled = True
            obj.save()
            rows_updated += 1
        if rows_updated == 1:
            message_bit = "1 job was"
        else:
            message_bit = "%s jobs were" % rows_updated
        level = messages.WARNING if not rows_updated else messages.INFO
        self.message_user(request, "%s successfully enabled." % message_bit, level=level)
    enable_selected.short_description = _("Enable selected %(verbose_name_plural)s")
    enable_selected.allowed_permissions = ('change',)

    def run_job_now(self, request, queryset):
        job_names = []
        for obj in queryset:
            kwargs = dict(timeout=obj.timeout)
            if hasattr(obj, 'result_ttl') and obj.result_ttl is not None:
                kwargs['job_result_ttl'] = obj.result_ttl
            obj.scheduler().enqueue_at(utc(now()), obj.callable_func(), **kwargs)
            job_names.append(obj.name)
        self.message_user(request, "The following jobs have been run: %s" % ', '.join(job_names))
    run_job_now.short_description = "Run now"
    run_job_now.allowed_permissions = ('change',)


@admin.register(ScheduledJob)
class ScheduledJobAdmin(JobAdmin):
    list_display = JobAdmin.list_display + ('scheduled_time',)

    fieldsets = JobAdmin.fieldsets + (
        (_('Scheduling'), {
            'fields': (
                'scheduled_time',
                'timeout',
                'result_ttl'
            ),
        }),
    )


@admin.register(RepeatableJob)
class RepeatableJobAdmin(JobAdmin):
    list_display = JobAdmin.list_display + ('scheduled_time', 'interval_display')

    fieldsets = JobAdmin.fieldsets + (
        (_('Scheduling'), {
            'fields': (
                'scheduled_time',
                ('interval', 'interval_unit', ),
                'repeat',
                'timeout',
                'result_ttl',
            ),
        }),
    )


@admin.register(CronJob)
class CronJobAdmin(JobAdmin):
    list_display = JobAdmin.list_display + ('cron_string',)

    fieldsets = JobAdmin.fieldsets + (
        (_('Scheduling'), {
            'fields': (
                'cron_string',
                'repeat',
                'timeout',
            ),
        }),
    )
