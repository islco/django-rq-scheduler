from django.forms import ModelForm, ValidationError
from django.utils.timezone import now


class JobAdminForm(ModelForm):

    def clean_scheduled_time(self):
        data = self.cleaned_data['scheduled_time']
        if data < now():
            raise ValidationError("Scheduled time has to be in the future")
        return data
