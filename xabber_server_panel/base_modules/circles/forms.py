from django import forms
from django.http import QueryDict

from .models import Circle


class CircleForm(forms.ModelForm):

    class Meta:
        fields = '__all__'
        model = Circle

    def save(self, commit=True):
        instance = super().save(commit=False)

        # Check if the "name" field is empty
        if not instance.name:
            # Set "name" value from the "circle" field
            instance.name = self.cleaned_data['circle']

        if commit:
            instance.save()

        return instance

