from django import forms


class InstallationForm(forms.Form):

    def __init__(self, *args, **kwargs):
        self.step_errors = {}
        super(InstallationForm, self).__init__(*args, **kwargs)

    host = forms.CharField(
        max_length=128,
        label='XMPP host',
        widget=forms.TextInput(attrs={'placeholder': 'example.com'}),
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

    def validate_1_step(self):
        self._validate_field('host')
        return not self.step_1_errors()

    def validate_2_step(self):
        self._validate_field('username')
        self._validate_field('password')
        return not self.step_2_errors()

    def validate_3_step(self):
        self._validate_field('db_host')
        self._validate_field('db_name')
        self._validate_field('db_user')
        self._validate_field('db_user_pass')
        return not self.step_3_errors()

    def _validate_field(self, field_name):

        """ Validate concrete form field by field name """

        field = self.fields.get(field_name)
        data = self.data.get(field_name, '')
        if field:
            try:
                field.clean(data)
            except forms.ValidationError as e:
                self.step_errors[field_name] = e

    def step_1_errors(self):
        return 'host' in self.step_errors.keys()

    def step_2_errors(self):
        return any(field in self.step_errors.keys() for field in ['username', 'password'])

    def step_3_errors(self):
        return any(field in self.step_errors.keys() for field in ['server_name', 'db_name', 'db_user'])