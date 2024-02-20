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

    def clean(self):

        """ Customized to add username and host unique error to username field """

        cleaned_data = super().clean()
        username = cleaned_data.get("username")
        host = cleaned_data.get("host")

        if username and host:
            if User.objects.filter(username=username, host=host).exists():
                self.add_error('username', "A user with that username and host already exists.")

        return cleaned_data