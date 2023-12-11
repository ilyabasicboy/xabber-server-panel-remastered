from django.shortcuts import reverse, render
from django.views.generic import TemplateView
from django.http import HttpResponseRedirect, HttpResponse
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings
from django.core import management
from django.apps import apps
from collections import OrderedDict
from ldap3 import Server, Connection, ALL
from django.template.utils import get_app_template_dirs

from xabber_server_panel.dashboard.models import VirtualHost
from xabber_server_panel.users.models import User
from xabber_server_panel.utils import host_is_valid, update_ejabberd_config

from .models import LDAPSettings, LDAPServer
from .forms import LDAPSettingsForm

import tarfile
import shutil
import os
import re


class ConfigList(TemplateView):
    template_name = 'config/tabs.html'

    def get(self, request, *args, **kwargs):
        context = self.get_context_data()

        if request.is_ajax():
            return render(request, 'config/parts/ldap_fields.html', context)

        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        self.form = LDAPSettingsForm(request.POST)

        host_id = self.request.POST.get('host')

        try:
            self.host = VirtualHost.objects.get(id=host_id)
        except ObjectDoesNotExist:
            self.form.add_error(
                'host', 'Host does not exists'
            )

        self.server_list = self.clean_server_list()
        if self.form.is_valid():
            self.update_or_create_ldap()
            # update_ejabberd_config()
            return HttpResponseRedirect(
                reverse('config:tabs')
            )

        return self.render_to_response(self.get_context_data())

    def get_context_data(self, **kwargs):
        hosts = VirtualHost.objects.all()
        admins = User.objects.filter(is_admin=True)
        form = self.form if hasattr(self, 'form') else LDAPSettingsForm()
        host = self.request.GET.get('host', hosts.first())
        ldap_settings = LDAPSettings.objects.filter(host=host).first()

        context = {
            'hosts': hosts,
            'admins': admins,
            'form': form,
            'ldap_settings': ldap_settings
        }
        return context

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


class CreateHost(TemplateView):
    template_name = 'config/host_create.html'

    def post(self, request, *args, **kwargs):
        host_name = request.POST.get('host')

        if host_is_valid(host_name):
            VirtualHost.objects.create(
                name=host_name
            )

            return HttpResponseRedirect(
                reverse('config:tabs')
            )

        context = {
        }
        return self.render_to_response(context)


class ManageAdmins(TemplateView):
    template_name = 'config/manage_admins.html'

    def get(self, request, *args, **kwargs):
        users = User.objects.all()

        context = {
            'users': users
        }
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        request_data = dict(request.POST)
        users = User.objects.all()
        admins = request_data.get('admins', [])

        users.filter(id__in=admins).update(is_admin=True)
        users.exclude(id__in=admins).update(is_admin=False)
        return HttpResponseRedirect(
            reverse('config:tabs')
        )


class Modules(TemplateView):

    def post(self, request, *args, **kwargs):
        uploaded_file = request.FILES.get('file')

        if uploaded_file:
            try:
                # Создание временной папки для распаковки
                temp_extract_dir = os.path.join(settings.BASE_DIR, 'temp_extract')
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

                        # Добавление 'panel' в INSTALLED_APPS
                        with open(os.path.join(target_path, 'apps.py'), 'a') as apps_file:
                            apps_file.write("\n\nfrom django.apps import AppConfig\n\n"
                                            "class PanelConfig(AppConfig):\n"
                                            f"    name = '{target_path}'\n")

                        # Внесение изменений в settings.py
                        settings.INSTALLED_APPS.append(f'{target_path}')

                    # Удаление временной папки
                    shutil.rmtree(temp_extract_dir)

                    print(HttpResponse("Модуль успешно добавлен и настроен."))
            except Exception as e:
                # Удаление временной папки в случае ошибки
                shutil.rmtree(temp_extract_dir, ignore_errors=True)
                print(HttpResponse(f"Ошибка при обработке архива: {str(e)}"))

        return HttpResponseRedirect(
            reverse('config:tabs')
        )