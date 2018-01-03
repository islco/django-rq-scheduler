from __future__ import unicode_literals

from django.contrib import admin
from django.utils.translation import ugettext_lazy as _

from scheduler.models import RepeatableJob, ScheduledJob
from scheduler.forms import JobAdminForm


class QueueMixin(object):
    form = JobAdminForm
    actions = ['delete_model']

    def get_actions(self, request):
        actions = super(QueueMixin, self).get_actions(request)
        del actions['delete_selected']
        return actions

    def delete_model(self, request, obj):
        if hasattr(obj, 'all'):
            for o in obj.all():
                o.delete()
        else:
            obj.delete()
    delete_model.short_description = _("Delete selected %(verbose_name_plural)s")


@admin.register(ScheduledJob)
class ScheduledJobAdmin(QueueMixin, admin.ModelAdmin):
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
            'description': _('Please be aware: Scheduled Time has to be in the future.'),
        }),
    )


@admin.register(RepeatableJob)
class RepeatableJobAdmin(QueueMixin, admin.ModelAdmin):
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
            'description': _('Please be aware: Scheduled Time has to be in the future.'),
        }),
    )
