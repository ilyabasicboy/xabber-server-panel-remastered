from django.views.generic import TemplateView
from django.http import HttpResponseRedirect, JsonResponse
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import reverse, loader, Http404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from datetime import datetime

from xabber_server_panel.base_modules.config.models import VirtualHost
from xabber_server_panel.base_modules.config.utils import make_xmpp_config
from xabber_server_panel.utils import reload_ejabberd_config, get_error_messages, validate_link
from xabber_server_panel.base_modules.users.decorators import permission_admin
from xabber_server_panel.api.utils import get_api
from xabber_server_panel.mixins import ServerStartedMixin

from .models import RegistrationSettings


class RegistrationList(ServerStartedMixin, LoginRequiredMixin, TemplateView):

    """ Render list of registration keys if registration is link """

    template_name = 'registration/list.html'

    @permission_admin
    def get(self, request, *args, **kwargs):
        host = request.current_host
        api = get_api(request)

        context = {}

        if host:
            settings, created = RegistrationSettings.objects.get_or_create(
                host=host
            )

            keys = api.get_keys(
                {"host": host.name}
            ).get('keys')

            context['settings'] = settings
            context['keys'] = keys

        if request.is_ajax():
            html = loader.render_to_string('registration/parts/registration_list.html', context, request)
            response_data = {
                'html': html
            }
            return JsonResponse(response_data)

        return self.render_to_response(context)

    @permission_admin
    def post(self, request, *args, **kwargs):
        self.host = request.current_host
        self.status = request.POST.get('status', 'disabled')
        self.api = get_api(request)
        self.keys = []

        self.context = {}

        if self.host:
            self.update_settings()
            make_xmpp_config()
            reload_ejabberd_config()

            if self.status == 'link' and not self.keys:
                return HttpResponseRedirect(
                    reverse(
                        'registration:create',
                    )
                )

            # check api errors
            error_messages = get_error_messages(request)
            if not error_messages:
                messages.success(request, 'Registration changed successfully.')

        return self.render_to_response(self.context)

    def update_settings(self):
        settings, created = RegistrationSettings.objects.update_or_create(
            host=self.host,
            defaults={
                'status': self.status
            }
        )
        self.context['settings'] = settings

        if self.status == 'link':
            self.keys = self.api.get_keys(
                {"host": self.host.name}
            ).get('keys')
            self.context['keys'] = self.keys


class RegistrationCreate(ServerStartedMixin, LoginRequiredMixin, TemplateView):

    """ Create registration key """

    template_name = 'registration/create.html'

    @permission_admin
    def get(self, request, *args, **kwargs):
        context = {}
        return self.render_to_response(context)

    @permission_admin
    def post(self, request, *args, **kwargs):
        host = request.current_host

        if host:
            expires_date = self.request.POST.get('expires_date')
            expires_time = self.request.POST.get('expires_time')
            expires = 0

            if expires_date:
                try:
                    # set default time if it's not provided
                    if not expires_time:
                        expires_time = '12:00'

                    # combine date and time
                    expires_date = datetime.strptime(expires_date, '%Y-%m-%d')
                    expires_time = datetime.strptime(expires_time, '%H:%M').time()
                    expires = int(datetime.combine(expires_date, expires_time).timestamp())
                except:
                    pass

            api = get_api(request)

            description = request.POST.get('description')

            response = api.create_key(
                {
                    "host": host.name,
                     "expire": expires,
                     "description": description
                }
            )

            make_xmpp_config()
            reload_ejabberd_config()

            # check api errors
            if not response.get('errors'):
                messages.success(request, 'Registration key created successfully.')

        return HttpResponseRedirect(
            reverse('registration:list')
        )


class RegistrationChange(ServerStartedMixin, LoginRequiredMixin, TemplateView):

    """ Change registration key """

    template_name = 'registration/change.html'

    @permission_admin
    def get(self, request, key, *args, **kwargs):
        host = request.current_host

        api = get_api(request)

        context = {
            "key": key
        }

        if host:
            # get key data
            keys = api.get_keys({"host": host.name}).get('keys')
            key_data_list = [obj for obj in keys if obj['key'] == key]
            key_data = key_data_list[0] if key_data_list else None

            if key_data.get('expire'):
                # timestamp to datetime
                expire = datetime.fromtimestamp(key_data.get('expire'))

                expire_date = expire.strftime('%Y-%m-%d')  # Format date as 'YYYY-MM-DD'
                expire_time = expire.strftime('%H:%M')

                context['expire_date'] = expire_date
                context['expire_time'] = expire_time
                context['description'] = key_data['description']

        return self.render_to_response(context)

    @permission_admin
    def post(self, request, key, *args, **kwargs):

        host = request.current_host

        expires_date = self.request.POST.get('expires_date')
        expires_time = self.request.POST.get('expires_time')

        expires = 0

        if expires_date:
            # combine date and time
            expires_date = datetime.strptime(expires_date, '%Y-%m-%d')

            # check expires time
            if not expires_time:
                expires_time = '12:00'

            expires_time = datetime.strptime(expires_time, '%H:%M').time()
            expires = int(datetime.combine(expires_date, expires_time).timestamp())

        api = get_api(request)

        description = request.POST.get('description')

        if host:
            response = api.change_key(
                {
                    "host": host.name,
                     "expire": expires,
                     "description": description
                },
                key
            )

            make_xmpp_config()
            reload_ejabberd_config()

            if not response.get('errors'):
                messages.success(request, 'Registration key changed successfully.')

        return HttpResponseRedirect(
            reverse('registration:list')
        )


class RegistrationDelete(ServerStartedMixin, LoginRequiredMixin, TemplateView):

    """ Delete registration key """

    @permission_admin
    def get(self, request, key, *args, **kwargs):

        host = request.current_host

        api = get_api(request)

        if host:
            response = api.delete_key({"host": host.name}, key=key)

            # check api errors
            if not response.get('errors'):
                messages.success(request, 'Registration key deleted successfully.')

        return HttpResponseRedirect(
            reverse('registration:list')
        )


class RegistrationUrl(ServerStartedMixin, LoginRequiredMixin, TemplateView):

    """ Change web client url"""

    template_name = 'registration/url.html'

    @permission_admin
    def get(self, request, id, *args, **kwargs):
        try:
            settings = RegistrationSettings.objects.get(id=id)
        except ObjectDoesNotExist:
            raise Http404

        context = {
            'settings': settings
        }
        return self.render_to_response(context)

    @permission_admin
    def post(self, request, id, *args, **kwargs):
        try:
            settings = RegistrationSettings.objects.get(id=id)
        except ObjectDoesNotExist:
            raise Http404

        url = request.POST.get('url')
        all = request.POST.get('all')

        if url and validate_link(url):
            if all:
                RegistrationSettings.objects.all().update(url=url)
            else:
                settings.url = url
                settings.save()

            messages.success(request, 'Web client url changed successfully.')
            return HttpResponseRedirect(
                reverse('registration:list')
            )
        else:
            messages.error(request, 'Url is incorrect.')

        context = {
            'settings': settings
        }
        return self.render_to_response(context)