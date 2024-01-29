from django.shortcuts import reverse, render, loader
from django.views.generic import TemplateView
from django.http import HttpResponseRedirect, HttpResponseNotFound, JsonResponse
from django.conf import settings
from ldap3 import Server, Connection, ALL
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.core import management
from django.apps import apps

from xabber_server_panel.dashboard.models import VirtualHost
from xabber_server_panel.circles.models import Circle
from xabber_server_panel.users.models import User
from xabber_server_panel.config.utils import update_ejabberd_config, make_xmpp_config
from xabber_server_panel.utils import host_is_valid, get_system_group_suffix, update_app_list
from xabber_server_panel.users.decorators import permission_read, permission_write, permission_admin

from .models import LDAPSettings, LDAPServer, RootPage
from .forms import LDAPSettingsForm

import tarfile
import shutil
import os
import re


class ConfigRoot(LoginRequiredMixin, TemplateView):
    app = 'settings'

    @permission_read
    def get(self, request, *args, **kwargs):

        if request.user.is_admin:
            return HttpResponseRedirect(reverse('config:hosts'))

        return HttpResponseRedirect(reverse('config:ldap'))


class Hosts(LoginRequiredMixin, TemplateView):
    template_name = 'config/hosts.html'
    app = 'settings'

    @permission_admin
    def get(self, request, *args, **kwargs):
        hosts = VirtualHost.objects.all()

        context = {
            'hosts': hosts,
        }
        return self.render_to_response(context)


class DeleteHost(LoginRequiredMixin, TemplateView):

    app = 'settings'

    @permission_admin
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

        messages.success(request, 'Host deleted successfully.')
        host.delete()
        update_ejabberd_config()
        return HttpResponseRedirect(
                reverse('config:hosts')
            )


class DetailHost(LoginRequiredMixin, TemplateView):
    template_name = 'config/host_detail.html'
    app = 'settings'

    @permission_admin
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
    app = 'settings'

    @permission_admin
    def get(self, request, *args, **kwargs):
        context = {
            "hosts": VirtualHost.objects.all()
        }
        return self.render_to_response(context)

    @permission_admin
    def post(self, request, *args, **kwargs):
        host = request.POST.get('host')

        if host_is_valid(host):
            VirtualHost.objects.create(
                name=host
            )
            self.create_everybody_group(request, host)
            update_ejabberd_config()

            messages.success(request, 'Vhost created successfully.')
            return HttpResponseRedirect(
                reverse('config:hosts')
            )

        messages.error(request, 'Host is invalid.')
        return self.render_to_response({})

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
    app = 'settings'

    @permission_admin
    def get(self, request, *args, **kwargs):
        admins = User.objects.filter(is_admin=True)
        users = User.objects.all()
        context = {
            'admins': admins,
            'users': users
        }
        return self.render_to_response(context)

    @permission_admin
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
        messages.success(request, 'Admins changed successfully.')
        update_ejabberd_config()
        context = {
            'admins': users.filter(id__in=admins),
            'users': users
        }
        return self.render_to_response(context)


class Ldap(LoginRequiredMixin, TemplateView):
    template_name = 'config/ldap.html'
    app = 'settings'

    @permission_read
    def get(self, request, *args, **kwargs):
        hosts = request.user.get_allowed_hosts()
        host_id = request.GET.get('host')
        session_host = request.session.get('host')

        context = {
            'hosts': hosts
        }

        if hosts:
            # get host obj
            host = None
            if host_id:
                host = hosts.filter(id=host_id).first()
            elif session_host:
                host = hosts.filter(name=session_host).first()

            if not host:
                host = hosts.first()

            # write current host on session
            request.session['host'] = host.name
            context['curr_host'] = host.name

            ldap_settings = LDAPSettings.objects.filter(host=host).first()
            context['ldap_settings'] = ldap_settings

        if request.is_ajax():
            html = loader.render_to_string('config/parts/ldap_fields.html', context, request)
            response_data = {
                'html': html
            }
            return JsonResponse(response_data)
        return self.render_to_response(context)

    @permission_write
    def post(self, request, *args, **kwargs):
        self.form = LDAPSettingsForm(request.POST)
        hosts = request.user.get_allowed_hosts()
        host_id = request.POST.get('host')

        context = {
            'hosts': hosts,
            'form': self.form
        }

        if hosts:
            # get host obj
            self.host = None
            if host_id:
                self.host = hosts.filter(id=host_id).first()

            if not self.host:
                self.host = hosts.first()

            context['curr_host'] = self.host.name

        self.server_list = self.clean_server_list()
        if self.form.is_valid():
            self.update_or_create_ldap()
            update_ejabberd_config()
            messages.success(request, 'Ldap changed successfully.')
        else:
            messages.error(request, 'Form data is incorrect.')

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
    app = 'settings'

    @permission_admin
    def get(self, request, *args, **kwargs):
        # print(settings.INSTALLED_APPS)
        return self.render_to_response({})

    @permission_admin
    def post(self, request, *args, **kwargs):
        uploaded_file = request.FILES.get('file')

        if uploaded_file:
            temp_extract_dir = os.path.join(settings.BASE_DIR, 'temp_extract')

            try:
                # Create temporary dir for unpack
                os.makedirs(temp_extract_dir, exist_ok=True)

                # Unpack archieve in temporary dir
                with tarfile.open(fileobj=uploaded_file, mode='r:gz') as tar:
                    tar.extractall(temp_extract_dir)

                # Get nested dir inside 'panel'
                panel_path = os.path.join(temp_extract_dir, 'panel')
                if os.path.isdir(panel_path):
                    # Copy module in modules dir
                    for module_dir in os.listdir(panel_path):
                        app_name = f'modules.{module_dir}'

                        if not apps.is_installed(app_name):
                            target_path = os.path.join(settings.MODULES_DIR, module_dir)
                            module_path = os.path.join(panel_path, module_dir)
                            shutil.copytree(module_path, target_path)

                            # Append app in settings.py
                            settings.INSTALLED_APPS += [app_name]

                            # update app list
                            update_app_list(settings.INSTALLED_APPS)

                            # migrate db if module has migrations
                            if os.path.exists(os.path.join(target_path, 'migrations', '__init__.py')):
                                management.call_command('migrate', module_dir, interactive=False)

                            if not settings.DEBUG:
                                management.call_command('collectstatic', '--noinput', interactive=False)

                    # Delete temporary dir
                    shutil.rmtree(temp_extract_dir)

                    make_xmpp_config()
                    messages.success(request, 'Module added successfully.')
            except Exception as e:
                print(e)
                # Delete temporary dir
                shutil.rmtree(temp_extract_dir, ignore_errors=True)
                messages.error(request, 'Archieve reading error.')

        return self.render_to_response({})


class DeleteModule(LoginRequiredMixin, TemplateView):
    app = 'settings'

    @permission_admin
    def get(self, request, module, *args, **kwargs):

        module_path = os.path.join(settings.MODULES_DIR, module)
        app_name = f'modules.{module}'

        if os.path.isdir(module_path) and apps.is_installed(app_name):

            # migrate db if module has migrations
            if os.path.exists(os.path.join(module_path, 'migrations', '__init__.py')):
                management.call_command('migrate', module, 'zero', interactive=True)

            if not settings.DEBUG:
                management.call_command('collectstatic', '--noinput', interactive=False)

            shutil.rmtree(module_path)

            settings.INSTALLED_APPS.remove(app_name)

            # update app list
            update_app_list(settings.INSTALLED_APPS)

            make_xmpp_config()
            messages.success(request, 'Module deleted successfully.')
            return HttpResponseRedirect(reverse('config:modules'))
        else:
            return HttpResponseNotFound


class RootPageView(LoginRequiredMixin, TemplateView):
    template_name = 'config/root_page.html'
    app = 'settings'

    @permission_read
    def get(self, request, *args, **kwargs):
        return self.render_to_response({})

    @permission_write
    def post(self, request, *args, **kwargs):

        module = request.POST.get('module', 'home')
        root_page = RootPage.objects.first()
        if root_page:
            root_page.module = module
            root_page.save()
        else:
            RootPage.objects.create(module=module)

        messages.success(request, 'Root changed successfully.')

        return self.render_to_response({})
