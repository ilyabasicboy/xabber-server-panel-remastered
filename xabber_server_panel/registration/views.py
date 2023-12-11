from django.views.generic import TemplateView
from django.http import HttpResponseNotFound, HttpResponseRedirect
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import reverse, render
from datetime import datetime

from xabber_server_panel.dashboard.models import VirtualHost

from .models import RegistrationSettings


class RegistrationList(TemplateView):
    template_name = 'registration/list.html'

    def get(self, request, *args, **kwargs):
        hosts = VirtualHost.objects.all()
        host_name = request.GET.get('host')
        self.host = hosts.filter(name=host_name).first() if host_name else hosts.first()

        self.context = {
            'hosts': hosts,
        }

        if self.host:
            self.get_context()

        if request.is_ajax():
            return render(request, 'registration/parts/registration_list.html', self.context)

        return self.render_to_response(self.context)

    def post(self, request, *args, **kwargs):
        host_name = request.POST.get('host')
        hosts = VirtualHost.objects.all()
        self.host = hosts.filter(name=host_name).first()
        self.status = request.POST.get('status', 'disabled')

        self.context = {
            'hosts': hosts,
        }

        if self.host:
            self.update_settings()

        return self.render_to_response(self.context)

    def get_context(self):
        settings, created = RegistrationSettings.objects.get_or_create(
            host=self.host
        )
        keys = self.request.user.api.get_keys(
            {"host": self.host.name}
        ).get('keys')
        self.context['settings'] = settings
        self.context['keys'] = keys

    def update_settings(self):
        settings, created = RegistrationSettings.objects.update_or_create(
            host=self.host,
            defaults={
                'status': self.status
            }
        )
        self.context['settings'] = settings

        if self.status == 'link':
            keys = self.request.user.api.get_keys(
                {"host": self.host.name}
            ).get('keys')
            self.context['keys'] = keys


class RegistrationCreate(TemplateView):
    template_name = 'registration/create.html'

    def get(self, request, vhost_id, *args, **kwargs):

        try:
            host = VirtualHost.objects.get(id=vhost_id)
        except ObjectDoesNotExist:
            return HttpResponseNotFound

        context = {
            'host': host
        }

        return self.render_to_response(context)

    def post(self, request, vhost_id, *args, **kwargs):
        try:
            host = VirtualHost.objects.get(id=vhost_id)
        except ObjectDoesNotExist:
            return HttpResponseNotFound

        try:
            expire = request.POST.get('expire')
            expire = int(datetime.strptime(expire, '%Y-%m-%d').timestamp())
        except:
            expire = None

        description = request.POST.get('description')
        if expire:
            response = request.user.api.create_key(
                {
                    "host": host.name,
                     "expire": expire,
                     "description": description
                }
            )
            return HttpResponseRedirect(
                reverse('registration:list') + f'?host={host.name}'
            )

        context = {
            'host': host
        }
        return self.render_to_response(context)


class RegistrationUrl(TemplateView):
    template_name = 'registration/url.html'

    def get(self, request, id, *args, **kwargs):
        try:
            settings = RegistrationSettings.objects.get(id=id)
        except ObjectDoesNotExist:
            return HttpResponseNotFound

        context = {
            'settings': settings
        }
        return self.render_to_response(context)

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
            return HttpResponseRedirect(
                reverse('registration:list') + f'?host={settings.host.name}'
            )

        context = {
            'settings': settings
        }
        return self.render_to_response(context)