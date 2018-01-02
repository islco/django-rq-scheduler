from django import forms
from django.utils import timezone


class RepeatableJobAdminForm(forms.ModelForm):

    def clean_scheduled_time(self):
        data = self.cleaned_data['scheduled_time']
        if data < timezone.now():
            raise forms.ValidationError("Scheduled time has to be in the future")
        return data
