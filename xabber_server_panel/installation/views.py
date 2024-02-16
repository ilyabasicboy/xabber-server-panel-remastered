from django.views.generic import TemplateView
from django.http import HttpResponseRedirect
from django.shortcuts import reverse
from django.contrib.auth import login

from xabber_server_panel.utils import server_installed
from xabber_server_panel.base_modules.config.models import VirtualHost
from xabber_server_panel.custom_auth.forms import ApiAuthenticationForm

from .forms import InstallationForm
from .utils import install_cmd, create_circles, load_predefined_config


class Steps(TemplateView):

    template_name = 'installation/steps.html'

    def get(self, request, *args, **kwargs):

        # if server_installed():
        #     return HttpResponseRedirect(reverse('root'))

        context = {
            'form': InstallationForm(),
            'step': '1'
        }

        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):

        self.form = InstallationForm(request.POST)

        previous = request.POST.get('previous')
        if previous:
            return self.render_to_response({
                "form": self.form,
                'step': previous
            })

        context = {}

        if self.form.is_valid():
            try:
                success, message = install_cmd(request, data=self.form.cleaned_data)
            except Exception as e:
                success, message = False, e
                print(e)

            if not success:
                return self.render_to_response({
                    "form": self.form,
                    "installation_error": message,
                    'step': '4'
                })

            create_circles(self.form.cleaned_data)
            self.login_admin()
            return HttpResponseRedirect(reverse('installation:success'))

        else:
            if self.form.step_1_errors():
                context['step'] = '1'
            elif self.form.step_2_errors():
                context['step'] = '2'
            elif self.form.step_3_errors():
                context['step'] = '3'

        context['form'] = self.form


        return self.render_to_response(context)

    def login_admin(self):
        data = {
            'username': f"{self.form.cleaned_data.get('username')}@{self.form.cleaned_data.get('host')}",
            'password': self.form.cleaned_data.get('password')
        }

        auth_form = ApiAuthenticationForm(data, request=self.request)

        if auth_form.is_valid():
            login(self.request, auth_form.user)


class Quick(TemplateView):

    template_name = 'installation/quick.html'

    def get(self, request, *args, **kwargs):

        # if server_installed():
        #     return HttpResponseRedirect(reverse('root'))

        data = load_predefined_config()

        context = {
            'form': InstallationForm(data)
        }

        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        data = load_predefined_config()
        data['username'] = request.POST.get('username')
        data['password'] = request.POST.get('password')

        self.form = InstallationForm(data)

        if self.form.is_valid():
            try:
                success, message = install_cmd(request, data=self.form.cleaned_data)
            except Exception as e:
                success, message = False, e
                print(e)

            if not success:
                return self.render_to_response({
                    "form": self.form,
                    "installation_error": message
                })

            create_circles(self.form.cleaned_data)
            self.login_admin()
            return HttpResponseRedirect(reverse('installation:success'))

        context = {
            "form": self.form
        }

        return self.render_to_response(context)

    def login_admin(self):
        data = {
            'username': f"{self.form.cleaned_data.get('username')}@{self.form.cleaned_data.get('host')}",
            'password': self.form.cleaned_data.get('password')
        }

        auth_form = ApiAuthenticationForm(data, request=self.request)

        if auth_form.is_valid():
            login(self.request, auth_form.user)


class Success(TemplateView):
    template_name = 'installation/success.html'

    def get(self, request, *args, **kwargs):
        return self.render_to_response(
            {
                'host': VirtualHost.objects.first()
            }
        )