from django import forms
from django.contrib.auth.hashers import make_password
from datetime import datetime

from xabber_server_panel.base_modules.users.models import User


class UserForm(forms.ModelForm):

    class Meta:
        fields = '__all__'
        model = User

    # fields to combine date and time to expires
    expires_date = forms.DateField(
        required=False
    )
    expires_time = forms.TimeField(
        required=False
    )

    def save(self, commit=True):

        """ Customized to fix password saving """

        instance = super().save(commit=False)
        password = self.cleaned_data.get('password')

        if password:
            instance.password = make_password(password)  # Hash the password
        if commit:
            instance.save()
        return instance

    def clean(self):

        """
            Customized to:
             * validate unique together username and host
             * combine expires date and time
        """

        cleaned_data = super().clean()

        # validate unique together username and host
        username = cleaned_data.get("username")
        host = cleaned_data.get("host")

        if username and host:
            if User.objects.filter(username=username, host=host).exists():
                self.add_error('username', "A user with that username and host already exists.")

        # combine expires
        expires_date = cleaned_data.get("expires_date")
        expires_time = cleaned_data.get("expires_time")

        if expires_date and expires_time:
            # Combine date and time
            expires_datetime = datetime.combine(expires_date, expires_time)
            cleaned_data["expires"] = expires_datetime

        return cleaned_data