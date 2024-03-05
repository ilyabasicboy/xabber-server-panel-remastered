from django import forms

from xabber_server_panel.utils import jid_form_validation, host_form_validation


class GroupForm(forms.Form):

    localpart = forms.CharField(
        required=True
    )

    host = forms.CharField(
        validators=[host_form_validation],
        required=True
    )

    name = forms.CharField(
        required=True
    )

    owner = forms.CharField(
        required=True,
        validators=[jid_form_validation]
    )

    privacy = forms.ChoiceField(
        widget=forms.RadioSelect,
        initial='public',
        choices=[
            ('public', 'public'),
            ('incognito', 'incognito'),
        ]
    )

    index = forms.ChoiceField(
        widget=forms.RadioSelect,
        initial='none',
        choices=[
            ('none', 'none'),
            ('local', 'local'),
            ('global', 'global'),
        ]
    )

    membership = forms.ChoiceField(
        widget=forms.RadioSelect,
        initial='open',
        choices=[
            ('open', 'open'),
            ('member-only', 'member-only'),
        ]
    )

