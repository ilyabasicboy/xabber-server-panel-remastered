from django.shortcuts import reverse, render, loader
from django.views.generic import TemplateView
from django.http import HttpResponseRedirect, HttpResponseNotFound, JsonResponse
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings
from ldap3 import Server, Connection, ALL
from django.contrib.auth.mixins import LoginRequiredMixin

from xabber_server_panel.dashboard.models import VirtualHost
from xabber_server_panel.circles.models import Circle
from xabber_server_panel.users.models import User
from xabber_server_panel.config.utils import update_ejabberd_config, make_xmpp_config
from xabber_server_panel.utils import host_is_valid, get_system_group_suffix

from .models import LDAPSettings, LDAPServer, RootPage
from .forms import LDAPSettingsForm

import tarfile
import shutil
import os
import re


class Hosts(LoginRequiredMixin, TemplateView):
    template_name = 'config/hosts.html'

    def get(self, request, *args, **kwargs):
        hosts = VirtualHost.objects.all()

        context = {
            'hosts': hosts,
        }
        return self.render_to_response(context)


class DeleteHost(LoginRequiredMixin, TemplateView):

    def get(self, request, id, *args, **kwargs):

        try:
            host = VirtualHost.objects.get(id=id)
        except VirtualHost.DoesNotExist:
            return HttpResponseNotFound

        users = User.objects.filter(host=host.name)
        for user in users:
            request.user.api.unregister_user(
                {
                    'username': user.username,
                    'host': host.name
                }
            )
        users.delete()

        circles = Circle.objects.filter(host=host.name)
        for circle in circles:
            request.user.api.delete_group(
                {
                    'circle': circle.circle,
                    'host': host.name
                }
            )
        circles.delete()

        host.delete()
        update_ejabberd_config()
        return HttpResponseRedirect(
                reverse('config:hosts')
            )


class DetailHost(LoginRequiredMixin, TemplateView):
    template_name = 'config/host_detail.html'

    def get(self, request, id, *args, **kwargs):

        try:
            host = VirtualHost.objects.get(id=id)
        except VirtualHost.DoesNotExist:
            return HttpResponseNotFound

        context = {
            'host': host
        }
        return self.render_to_response(context)


class CreateHost(LoginRequiredMixin, TemplateView):
    template_name = 'config/host_create.html'

    def get(self, request, *args, **kwargs):
        context = {
            "hosts": VirtualHost.objects.all()
        }
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        host = request.POST.get('host')

        if host_is_valid(host):
            VirtualHost.objects.create(
                name=host
            )
            self.create_everybody_group(request, host)
            update_ejabberd_config()
            return HttpResponseRedirect(
                reverse('config:hosts')
            )

        context = {
        }
        return self.render_to_response(context)

    def create_everybody_group(self, request, host):
        request.user.api.srg_create_api(
            {
                'group': host,
                'host': host,
                'name': settings.EJABBERD_DEFAULT_GROUP_NAME,
                'description': settings.EJABBERD_DEFAULT_GROUP_DESCRIPTION,
                'display': []
            }
        )
        request.user.api.srg_user_add_api(
            {
                'members': ['@all@'],
                'host': host,
                'circle': host
            }
        )

        circle = Circle.objects.create(
            circle=host,
            host=host,
            name=settings.EJABBERD_DEFAULT_GROUP_NAME,
            description=settings.EJABBERD_DEFAULT_GROUP_DESCRIPTION,
            prefix=get_system_group_suffix()
        )


class Admins(LoginRequiredMixin, TemplateView):
    template_name = 'config/admins.html'

    def get(self, request, *args, **kwargs):
        admins = User.objects.filter(is_admin=True)
        users = User.objects.all()
        context = {
            'admins': admins,
            'users': users
        }
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        request_data = dict(request.POST)
        users = User.objects.all()
        admins = request_data.get('admins', [])

        admins_to_add = users.filter(id__in=admins, is_admin=False)
        for user in admins_to_add:
            request.user.api.xabber_set_admin(
                {
                    "username": user.username,
                    "host": user.host
                }
            )

        admins_to_add.update(is_admin=True)

        admins_to_delete = users.exclude(id__in=admins, is_admin=True)
        for user in admins_to_delete:
            request.user.api.xabber_del_admin(
                {
                    "username": user.username,
                    "host": user.host,
                }
            )

        admins_to_delete.update(is_admin=False)

        update_ejabberd_config()
        context = {
            'admins': users.filter(id__in=admins),
            'users': users
        }
        return self.render_to_response(context)


class Ldap(LoginRequiredMixin, TemplateView):
    template_name = 'config/ldap.html'

    def get(self, request, *args, **kwargs):
        hosts = VirtualHost.objects.all()

        context = {
            'hosts': hosts
        }

        if hosts:
            host_id = self.request.GET.get('host')

            if host_id:
                host = hosts.filter(id=host_id).first()
            else:
                host = hosts.first()

            ldap_settings = LDAPSettings.objects.filter(host=host).first()
            context['ldap_settings'] = ldap_settings

        if request.is_ajax():
            html = loader.render_to_string('config/parts/ldap_fields.html', context, request)
            response_data = {
                'html': html
            }
            return JsonResponse(response_data)
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        self.form = LDAPSettingsForm(request.POST)
        hosts = VirtualHost.objects.all()

        context = {
            'hosts': hosts,
            'form': self.form
        }

        host_id = self.request.POST.get('host')

        try:
            self.host = VirtualHost.objects.get(id=host_id)
            context['curr_host'] = self.host.name
        except ObjectDoesNotExist:
            self.form.add_error(
                'host', 'Host does not exists'
            )

        self.server_list = self.clean_server_list()
        if self.form.is_valid():
            self.update_or_create_ldap()
            update_ejabberd_config()

        return self.render_to_response(context)

    def clean_server_list(self):
        server_list_data = self.request.POST.get('server_list')

        # Split the input strings by commas, semicolons, and line breaks
        server_list = re.split(r'[;,\n]+', server_list_data.strip())

        # Remove empty strings
        server_list = [server.strip() for server in server_list if server.strip()]

        invalid_server_list = []
        for server_name in server_list:
            server = Server(server_name, get_info=ALL)
            conn = Connection(server)
            try:
                conn.bind()
            except Exception:
                invalid_server_list.append(server_name)

        if invalid_server_list:
            self.form.add_error(
                'server_list', 'Invalid server list: {}.'.format(', '.join(invalid_server_list))
            )

        return server_list

    def update_or_create_ldap(self):
        # prepare data to update excluding special fields
        defaults = {
            key: self.form.cleaned_data.get(key) for key in self.form.fields.keys() if key not in ['host', 'server_list']
        }

        # update settings
        ldap_settings, created = LDAPSettings.objects.update_or_create(
            host=self.host,
            defaults=defaults
        )

        # create new servers
        for server in self.server_list:
            LDAPServer.objects.get_or_create(
                server=server, settings=ldap_settings
            )

        # delete old servers
        ldap_settings.servers.exclude(server__in=self.server_list).delete()


class Modules(LoginRequiredMixin, TemplateView):
    template_name = 'config/modules.html'

    def get(self, request, *args, **kwargs):
        return self.render_to_response({})

    def post(self, request, *args, **kwargs):
        uploaded_file = request.FILES.get('file')

        if uploaded_file:
            temp_extract_dir = os.path.join(settings.BASE_DIR, 'temp_extract')

            try:
                # Создание временной папки для распаковки
                os.makedirs(temp_extract_dir, exist_ok=True)

                # Распаковка архива во временную папку
                with tarfile.open(fileobj=uploaded_file, mode='r:gz') as tar:
                    tar.extractall(temp_extract_dir)

                # Получение вложенной папки внутри 'panel'
                panel_path = os.path.join(temp_extract_dir, 'panel')
                if os.path.isdir(panel_path):
                    # Копирование содержимого в modules
                    for module_dir in os.listdir(panel_path):
                        target_path = os.path.join(settings.MODULES_DIR, module_dir)
                        module_path = os.path.join(panel_path, module_dir)
                        shutil.copytree(module_path, target_path)

                        # Внесение изменений в settings.py
                        settings.INSTALLED_APPS.append(f'{target_path}')
                    # Удаление временной папки
                    shutil.rmtree(temp_extract_dir)

                    make_xmpp_config()
                    print("Модуль успешно добавлен и настроен.")
            except Exception as e:
                # Удаление временной папки в случае ошибки
                shutil.rmtree(temp_extract_dir, ignore_errors=True)
                print(f"Ошибка при обработке архива: {str(e)}")

        return self.render_to_response({})


class DeleteModule(LoginRequiredMixin, TemplateView):

    def get(self, request, module, *args, **kwargs):

        module_path = os.path.join(settings.MODULES_DIR, module)
        if os.path.isdir(module_path):
            shutil.rmtree(module_path)

            make_xmpp_config()
            return HttpResponseRedirect(reverse('config:modules'))
        else:
            return HttpResponseNotFound


class RootPageView(LoginRequiredMixin, TemplateView):
    template_name = 'config/root_page.html'

    def get(self, request, *args, **kwargs):
        return self.render_to_response({})

    def post(self, request, *args, **kwargs):

        module = request.POST.get('module', 'home')
        root_page = RootPage.objects.first()
        if root_page:
            root_page.module = module
            root_page.save()
        else:
            RootPage.objects.create(module=module)

        return self.render_to_response({})
