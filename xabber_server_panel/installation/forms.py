from django import forms
from xabber_server_panel.utils import host_is_valid


def host_validation(value):
    # Define a regular expression for the host format: 'example.com'
    if not host_is_valid(value):
        raise forms.ValidationError("Invalid host format.")


class InstallationForm(forms.Form):

    host = forms.CharField(
        max_length=128,
        label='XMPP host',
        widget=forms.TextInput(attrs={'placeholder': 'example.com'}),
        validators=[host_validation]
    )
    username = forms.CharField(
        max_length=100,
        label='Username',
        widget=forms.TextInput(attrs={'placeholder': 'admin'})
    )
    password = forms.CharField(
        max_length=100,
        label='Password',
        widget=forms.PasswordInput(
            render_value=True,
            attrs={'placeholder': 'Password'}
        )
    )
    db_host = forms.CharField(
        max_length=100,
        label='Database server name',
        widget=forms.TextInput(attrs={'placeholder': 'localhost'})
    )
    db_name = forms.CharField(
        max_length=100,
        label='Database name',
        widget=forms.TextInput(attrs={'placeholder': 'xabberserver'})
    )
    db_user = forms.CharField(
        max_length=100,
        label='Database user',
        widget=forms.TextInput(attrs={'placeholder': 'admin'}),
    )
    db_user_pass = forms.CharField(
        max_length=100,
        required=False,
        label='Database user password',
        widget=forms.PasswordInput(render_value=True, attrs={'placeholder': 'Password'})
    )

    def step_1_errors(self):
        return 'host' in self.errors.keys()

    def step_2_errors(self):
        return any(field in self.errors.keys() for field in ['username', 'password'])

    def step_3_errors(self):
        return any(field in self.errors.keys() for field in ['server_name', 'db_name', 'db_user'])