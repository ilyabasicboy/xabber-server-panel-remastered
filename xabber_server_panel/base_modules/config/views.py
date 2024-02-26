from django.shortcuts import reverse, loader
from django.views.generic import TemplateView
from django.http import HttpResponseRedirect, HttpResponseNotFound, JsonResponse
from django.template.utils import get_app_template_dirs
from django.conf import settings
from ldap3 import Server, Connection, ALL
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.core import management
from django.apps import apps

from xabber_server_panel.base_modules.config.models import VirtualHost
from xabber_server_panel.base_modules.circles.models import Circle
from xabber_server_panel.base_modules.users.models import User
from xabber_server_panel.base_modules.config.utils import update_ejabberd_config, make_xmpp_config, check_hosts
from xabber_server_panel.utils import host_is_valid, get_system_group_suffix, update_app_list, reload_server
from xabber_server_panel.base_modules.users.decorators import permission_read, permission_write, permission_admin
from xabber_server_panel.api.utils import get_api
from xabber_server_panel.utils import get_error_messages, restart_ejabberd

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

        api = get_api(request)

        check_hosts(api)

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

        api = get_api(request)

        users = User.objects.filter(host=host.name)
        for user in users:
            api.unregister_user(
                {
                    'username': user.username,
                    'host': host.name
                }
            )
        users.delete()

        circles = Circle.objects.filter(host=host.name)
        for circle in circles:
            api.delete_circle(
                {
                    'circle': circle.circle,
                    'host': host.name
                }
            )
        circles.delete()

        # check api errors
        error_messages = get_error_messages(request)
        if not error_messages:
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
        self.api = get_api(request)

        if host_is_valid(host):
            VirtualHost.objects.create(
                name=host
            )

            # update config after creating new host
            update_ejabberd_config()

            # create groups after update config
            self.create_everybody_group(request, host)

            return HttpResponseRedirect(
                reverse('config:hosts')
            )

        messages.error(request, 'Host is invalid.')
        return self.render_to_response({})

    def create_everybody_group(self, request, host):
        response = self.api.create_circle(
            {
                'circle': host,
                'host': host,
                'name': settings.EJABBERD_DEFAULT_GROUP_NAME,
                'description': settings.EJABBERD_DEFAULT_GROUP_DESCRIPTION,
                'all_users': True
            }
        )

        Circle.objects.create(
            circle=host,
            host=host,
            name=settings.EJABBERD_DEFAULT_GROUP_NAME,
            description=settings.EJABBERD_DEFAULT_GROUP_DESCRIPTION,
            prefix=get_system_group_suffix(),
            all_users=True
        )

        # check api errors
        if not response.get('errors'):
            messages.success(request, 'Vhost created successfully.')


class Admins(LoginRequiredMixin, TemplateView):
    template_name = 'config/admins.html'
    app = 'settings'

    @permission_admin
    def get(self, request, *args, **kwargs):
        admins = User.objects.filter(is_admin=True)

        # exclude authenticated user because he cant change self status
        users = User.objects.exclude(id=request.user.id)
        context = {
            'admins': admins,
            'users': users
        }
        return self.render_to_response(context)

    @permission_admin
    def post(self, request, *args, **kwargs):
        request_data = dict(request.POST)

        # exclude authenticated user because he cant change self status
        users = User.objects.exclude(id=request.user.id)

        admins = request_data.get('admins', [])
        api = get_api(request)

        admins_to_add = users.filter(id__in=admins, is_admin=False)
        for user in admins_to_add:
            user.permissions.set([])
            api.set_admin(
                {
                    "username": user.username,
                    "host": user.host
                }
            )

        admins_to_add.update(is_admin=True)

        admins_to_delete = users.exclude(id__in=admins).filter(is_admin=True)
        for user in admins_to_delete:
            api.del_admin(
                {
                    "username": user.username,
                    "host": user.host,
                }
            )

        admins_to_delete.update(is_admin=False)

        # check api errors
        error_messages = get_error_messages(request)
        if not error_messages:
            messages.success(request, 'Admins changed successfully.')

        update_ejabberd_config()
        context = {
            'admins': User.objects.filter(is_admin=True),
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
            restart_ejabberd()

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
        return self.render_to_response({})

    @permission_admin
    def post(self, request, *args, **kwargs):
        self.uploaded_file = request.FILES.get('file')

        if self.uploaded_file:
            self.handle_upload()

        return self.render_to_response({})

    def handle_upload(self):
        temp_extract_dir = os.path.join(settings.BASE_DIR, 'temp_extract')

        try:
            # Create temporary dir for unpack
            os.makedirs(temp_extract_dir, exist_ok=True)

            # Unpack archieve in temporary dir
            with tarfile.open(fileobj=self.uploaded_file, mode='r:gz') as tar:
                tar.extractall(temp_extract_dir)

            # Get nested dir inside 'panel'
            panel_path = os.path.join(temp_extract_dir, 'panel')
            if os.path.isdir(panel_path):

                # Copy module in modules dir
                for module_dir in os.listdir(panel_path):
                    app_name = f'modules.{module_dir}'
                    self.install_module(panel_path, module_dir, app_name)

                # create permissions for new modules
                management.call_command('update_permissions')

                # Delete temporary dir
                shutil.rmtree(temp_extract_dir)

                make_xmpp_config()
                get_app_template_dirs.cache_clear()

                reload_server()

                messages.success(self.request, 'Module added successfully.')
        except Exception as e:
            # Delete temporary dir
            shutil.rmtree(temp_extract_dir, ignore_errors=True)
            messages.error(self.request, e)

    def install_module(self, panel_path, module_dir, app_name):

        target_path = os.path.join(settings.MODULES_DIR, module_dir)
        module_path = os.path.join(panel_path, module_dir)

        if os.path.exists(target_path):
            shutil.rmtree(target_path)

        shutil.copytree(module_path, target_path)

        if not apps.is_installed(app_name):
            # Append app in settings.py
            settings.INSTALLED_APPS += [app_name]

            # update app list
            update_app_list(settings.INSTALLED_APPS)

        # migrate db if module has migrations
        if os.path.exists(os.path.join(target_path, 'migrations', '__init__.py')):
            management.call_command('migrate', module_dir, interactive=False)

        if not settings.DEBUG:
            management.call_command('collectstatic', '--noinput', interactive=False)


class DeleteModule(LoginRequiredMixin, TemplateView):
    app = 'settings'

    @permission_admin
    def get(self, request, module, *args, **kwargs):
        module_path = os.path.join(settings.MODULES_DIR, module)
        app_name = f'modules.{module}'

        if os.path.isdir(module_path) and apps.is_installed(app_name):
            self.hande_delete(module_path, module, app_name)

            messages.success(request, 'Module deleted successfully.')
            return HttpResponseRedirect(reverse('config:modules'))
        else:
            return HttpResponseNotFound

    def hande_delete(self, module_path, module, app_name):

        # migrate db if module has migrations
        if os.path.exists(os.path.join(module_path, 'migrations', '__init__.py')):
            management.call_command('migrate', module, 'zero', interactive=True)

        if not settings.DEBUG:
            management.call_command('collectstatic', '--noinput', interactive=False)

        shutil.rmtree(module_path)

        settings.INSTALLED_APPS.remove(app_name)

        # update app list
        update_app_list(settings.INSTALLED_APPS)

        management.call_command('update_permissions')
        make_xmpp_config()

        reload_server()


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
