from django import forms
from django.contrib.admin.widgets import FilteredSelectMultiple

from xabber_server_panel.base_modules.users.models import User

from .models import Circle


class CircleForm(forms.ModelForm):

    class Meta:
        fields = '__all__'
        model = Circle

    autoshare = forms.BooleanField(
        required=False
    )

    def save(self, commit=True):
        """
            Customized to use circle instead of name
            if name is not provided
        """

        instance = super().save(commit=False)

        # Check if the "name" field is empty
        if not instance.name:
            # Set "name" value from the "circle" field
            instance.name = self.cleaned_data.get('circle')

        autoshare = self.cleaned_data.get('autoshare')
        if autoshare:
            instance.subscribes = self.cleaned_data.get('circle')

        if commit:
            instance.save()

        return instance

    def clean(self):

        """
            Customized to:
             * validate unique together circle and host
        """

        cleaned_data = super().clean()

        # validate unique together username and host
        circle = cleaned_data.get("circle")
        host = cleaned_data.get("host")

        if circle and host:
            if Circle.objects.filter(circle=circle, host=host).exists():
                self.add_error('circle', "A circle with that circle and host already exists.")


        return cleaned_data


class MembersForm(forms.Form):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['members'].choices = [(user.id, user.full_jid) for user in User.objects.all()]

    members = forms.MultipleChoiceField(
        widget=FilteredSelectMultiple('members', False)
    )