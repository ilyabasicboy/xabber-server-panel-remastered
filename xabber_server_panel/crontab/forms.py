from django import forms
from ast import literal_eval
from django.core.exceptions import ValidationError
import json

from .models import CronJob


class CronJobForm(forms.ModelForm):

    class Meta:
        model = CronJob
        fields = '__all__'

    def clean_args(self):
        args = self.cleaned_data.get('args')
        if args:
            args = args.strip()
            try:
                args_list = literal_eval(args)
                if not isinstance(args_list, list):
                    raise ValidationError('Args must be in the format of a list.')
            except (ValueError, SyntaxError):
                raise ValidationError('Invalid format for args. Must be a valid Python list.')
        return args

    def clean_kwargs(self):
        kwargs = self.cleaned_data.get('kwargs')
        if kwargs:
            kwargs = kwargs.strip()
            try:
                json.loads(kwargs)
            except json.JSONDecodeError:
                raise ValidationError('Invalid format for kwargs. Must be a valid JSON string.')
        return kwargs