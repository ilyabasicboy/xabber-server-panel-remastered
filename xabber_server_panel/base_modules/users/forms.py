from django import forms
from xabber_server_panel.base_modules.users.models import User


class UserForm(forms.ModelForm):

    class Meta:
        fields = '__all__'
        model = User