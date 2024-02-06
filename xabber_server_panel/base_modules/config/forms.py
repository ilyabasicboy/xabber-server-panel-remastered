from django import forms
from .models import LDAPSettings


class LDAPSettingsForm(forms.ModelForm):

    class Meta:
        fields = '__all__'
        model = LDAPSettings

    server_list = forms.CharField(
        required=False,
        label='Server list',
        widget=forms.Textarea(
            attrs={
                'placeholder': 'ldap1.example.org\n'
                               'ldap2.example.org\n'
                               'ldap3.example.org'
            }
        ),
        help_text='Enter the each server name from a new line'
    )