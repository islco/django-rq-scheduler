from django.contrib import admin
from django.utils.translation import ugettext_lazy as _

from scheduler.models import RepeatableJob, ScheduledJob


@admin.register(ScheduledJob)
class ScheduledJobAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'job_id', 'is_scheduled', 'scheduled_time', 'enabled')
    list_filter = ('enabled', )
    list_editable = ('enabled', )

    readonly_fields = ('job_id', )
    fieldsets = (
        (None, {
            'fields': ('name', 'callable', 'enabled', ),
        }),
        (_('RQ Settings'), {
            'fields': ('queue', 'job_id', ),
        }),
        (_('Scheduling'), {
            'fields': (
                'scheduled_time',
                'timeout',
            ),
        }),
    )


@admin.register(RepeatableJob)
class RepeatableJobAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'job_id', 'is_scheduled', 'scheduled_time', 'interval_display',
        'enabled')
    list_filter = ('enabled', )
    list_editable = ('enabled', )

    readonly_fields = ('job_id', )
    fieldsets = (
        (None, {
            'fields': ('name', 'callable', 'enabled', ),
        }),
        (_('RQ Settings'), {
            'fields': ('queue', 'job_id', ),
        }),
        (_('Scheduling'), {
            'fields': (
                'scheduled_time',
                ('interval', 'interval_unit', ),
                'repeat',
                'timeout',
            ),
        }),
    )
