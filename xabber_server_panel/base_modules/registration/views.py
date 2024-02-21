from django.views.generic import TemplateView
from django.http import HttpResponseNotFound, HttpResponseRedirect, JsonResponse
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import reverse, loader
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from datetime import datetime

from xabber_server_panel.base_modules.config.models import VirtualHost
from xabber_server_panel.base_modules.config.utils import make_xmpp_config
from xabber_server_panel.utils import reload_ejabberd_config
from xabber_server_panel.base_modules.users.decorators import permission_admin
from xabber_server_panel.api.utils import get_api

from .models import RegistrationSettings


class RegistrationList(LoginRequiredMixin, TemplateView):
    template_name = 'registration/list.html'
    app = 'registration'

    @permission_admin
    def get(self, request, *args, **kwargs):
        hosts = request.user.get_allowed_hosts()
        api = get_api(request)

        context = {
            'hosts': hosts,
        }

        if hosts.exists():
            host = request.GET.get('host', request.session.get('host'))

            if not hosts.filter(name=host):
                host = hosts.first().name

            # write current host on session
            request.session['host'] = host

            context['curr_host'] = host

            host_obj = hosts.filter(name=host).first()
            settings, created = RegistrationSettings.objects.get_or_create(
                host=host_obj
            )

            keys = api.get_keys(
                {"host": host}
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
        host_name = request.POST.get('host')
        hosts = VirtualHost.objects.all()
        self.host = hosts.filter(name=host_name).first()
        self.status = request.POST.get('status', 'disabled')
        self.api = get_api(request)
        self.keys = []

        self.context = {
            'hosts': hosts,
            'curr_host': host_name
        }

        if self.host:
            self.update_settings()
            make_xmpp_config()
            reload_ejabberd_config()

            if self.status == 'link' and not self.keys:
                return HttpResponseRedirect(
                    reverse(
                        'registration:create',
                        kwargs={'vhost_id': self.host.id}
                    )
                )

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


class RegistrationCreate(LoginRequiredMixin, TemplateView):
    template_name = 'registration/create.html'
    app = 'registration'

    @permission_admin
    def get(self, request, vhost_id, *args, **kwargs):

        try:
            host = VirtualHost.objects.get(id=vhost_id)
        except ObjectDoesNotExist:
            return HttpResponseNotFound

        context = {
            'host': host
        }

        return self.render_to_response(context)

    @permission_admin
    def post(self, request, vhost_id, *args, **kwargs):
        try:
            host = VirtualHost.objects.get(id=vhost_id)
        except ObjectDoesNotExist:
            return HttpResponseNotFound

        expires_date = self.request.POST.get('expires_date')
        expires_time = self.request.POST.get('expires_time')
        try:
            # combine date and time
            expires_date = datetime.strptime(expires_date, '%Y-%m-%d')
            expires_time = datetime.strptime(expires_time, '%H:%M').time()
            expires = int(datetime.combine(expires_date, expires_time).timestamp())
        except:
            expires = None

        api = get_api(request)

        description = request.POST.get('description')
        if expires:
            api.create_key(
                {
                    "host": host.name,
                     "expire": expires,
                     "description": description
                }
            )
            messages.success(request, 'Registration key created successfully.')
            return HttpResponseRedirect(
                reverse('registration:list') + f'?host={host.name}'
            )

        context = {
            'host': host
        }

        make_xmpp_config()
        reload_ejabberd_config()
        return self.render_to_response(context)


class RegistrationChange(LoginRequiredMixin, TemplateView):
    template_name = 'registration/change.html'
    app = 'registration'

    @permission_admin
    def get(self, request, vhost_id, key, *args, **kwargs):

        try:
            host = VirtualHost.objects.get(id=vhost_id)
        except ObjectDoesNotExist:
            return HttpResponseNotFound

        api = get_api(request)

        context = {
            'host': host,
            "key": key
        }

        # get key data
        keys = api.get_keys({"host": host}).get('keys')
        key_data_list = [obj for obj in keys if obj['key'] == key]
        key_data = key_data_list[0] if key_data_list else None

        if key_data:
            # timestamp to datetime
            expire = datetime.fromtimestamp(key_data['expire'])

            expire_date = expire.strftime('%Y-%m-%d')  # Format date as 'YYYY-MM-DD'
            expire_time = expire.strftime('%H:%M')

            context['expire_date'] = expire_date
            context['expire_time'] = expire_time
            context['description'] = key_data['description']

        return self.render_to_response(context)

    @permission_admin
    def post(self, request, vhost_id, key, *args, **kwargs):
        try:
            host = VirtualHost.objects.get(id=vhost_id)
        except ObjectDoesNotExist:
            return HttpResponseNotFound

        expires_date = self.request.POST.get('expires_date')
        expires_time = self.request.POST.get('expires_time')
        try:
            # combine date and time
            expires_date = datetime.strptime(expires_date, '%Y-%m-%d')
            expires_time = datetime.strptime(expires_time, '%H:%M').time()
            expires = int(datetime.combine(expires_date, expires_time).timestamp())
        except:
            expires = None

        api = get_api(request)

        description = request.POST.get('description')
        if expires:
            api.change_key(
                {
                    "host": host.name,
                     "expire": expires,
                     "description": description
                },
                key
            )
            messages.success(request, 'Registration key changed successfully.')
            return HttpResponseRedirect(
                reverse('registration:list') + f'?host={host.name}'
            )

        context = {
            'host': host
        }

        make_xmpp_config()
        reload_ejabberd_config()
        return self.render_to_response(context)


class RegistrationDelete(LoginRequiredMixin, TemplateView):
    app = 'registration'

    @permission_admin
    def get(self, request, vhost_id, key, *args, **kwargs):

        try:
            host = VirtualHost.objects.get(id=vhost_id)
        except ObjectDoesNotExist:
            return HttpResponseNotFound

        api = get_api(request)

        api.delete_key({"host": host.name}, key=key)
        messages.success(request, 'Registration key deleted successfully.')
        return HttpResponseRedirect(
            reverse('registration:list') + f'?host={host.name}'
        )


class RegistrationUrl(LoginRequiredMixin, TemplateView):
    template_name = 'registration/url.html'
    app = 'registration'

    @permission_admin
    def get(self, request, id, *args, **kwargs):
        try:
            settings = RegistrationSettings.objects.get(id=id)
        except ObjectDoesNotExist:
            return HttpResponseNotFound

        context = {
            'settings': settings
        }
        return self.render_to_response(context)

    @permission_admin
    def post(self, request, id, *args, **kwargs):
        try:
            settings = RegistrationSettings.objects.get(id=id)
        except ObjectDoesNotExist:
            return HttpResponseNotFound

        url = request.POST.get('url')
        all = request.POST.get('all')

        if url:
            if all:
                RegistrationSettings.objects.all().update(url=url)
            else:
                settings.url = url
                settings.save()

            messages.success(request, 'Web client url changed successfully.')
            return HttpResponseRedirect(
                reverse('registration:list') + f'?host={settings.host.name}'
            )

        context = {
            'settings': settings
        }
        return self.render_to_response(context)