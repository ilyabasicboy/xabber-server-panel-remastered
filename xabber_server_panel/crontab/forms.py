from django import forms

from .models import CronJob


class CronJobForm(forms.ModelForm):

    class Meta:
        model = CronJob
        fields = '__all__'