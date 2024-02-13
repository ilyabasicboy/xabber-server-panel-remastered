from django import forms
from django.contrib.auth.hashers import make_password

from xabber_server_panel.base_modules.users.models import User


class UserForm(forms.ModelForm):

    class Meta:
        fields = '__all__'
        model = User

    def save(self, commit=True):

        """ rewrited method to fix password saving """

        instance = super().save(commit=False)
        password = self.cleaned_data.get('password')

        if password:
            instance.password = make_password(password)  # Hash the password
        if commit:
            instance.save()
        return instance