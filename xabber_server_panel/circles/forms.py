from django import forms
from .models import Circle


class CircleForm(forms.ModelForm):

    class Meta:
        fields = '__all__'
        model = Circle