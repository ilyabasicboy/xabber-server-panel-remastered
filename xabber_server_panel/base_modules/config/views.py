from django.shortcuts import reverse, loader, render, Http404
from django.views.generic import TemplateView, View
from django.http import HttpResponseRedirect, JsonResponse
from django.template.utils import get_app_template_dirs
from django.conf import settings
from ldap3 import Server, Connection, ALL
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.core import management
from django.apps import apps
from importlib import import_module

from xabber_server_panel.base_modules.config.models import VirtualHost, Module
from xabber_server_panel.base_modules.circles.models import Circle
from xabber_server_panel.base_modules.users.models import User
from xabber_server_panel.base_modules.users.utils import check_users
from xabber_server_panel.base_modules.config.utils import update_ejabberd_config, make_xmpp_config, check_hosts, get_srv_records, check_hosts_dns, check_modules
from xabber_server_panel.utils import host_is_valid, get_system_group_suffix, update_app_list, reload_server
from xabber_server_panel.base_modules.users.decorators import permission_read, permission_write, permission_admin
from xabber_server_panel.api.utils import get_api
from xabber_server_panel.utils import get_error_messages, restart_ejabberd, is_ejabberd_started

from .models import LDAPSettings, LDAPServer, RootPage
from .forms import LDAPSettingsForm

import tarfile
import shutil
import os
import re


class ConfigRoot(LoginRequiredMixin, TemplateView):

    @permission_read
    def get(self, request, *args, **kwargs):

        if request.user.is_admin:
            return HttpResponseRedirect(reverse('config:hosts'))

        return HttpResponseRedirect(reverse('config:ldap'))


class Hosts(LoginRequiredMixin, TemplateView):
    template_name = 'config/hosts.html'

    @permission_admin
    def get(self, request, *args, **kwargs):

        api = get_api(request)

        check_hosts(api)

        context = {}
        return self.render_to_response(context)


class DeleteHost(LoginRequiredMixin, TemplateView):

    @permission_admin
    def get(self, request, id, *args, **kwargs):

        try:
            host = VirtualHost.objects.get(id=id)
        except VirtualHost.DoesNotExist:
            raise Http404

        if request.user.host == host.name:
            messages.error(request, "You can't delete self host!")
            return HttpResponseRedirect(
                reverse('config:hosts')
            )

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
            messages.success(request, f'Host "{host.name}" deleted successfully.')

        host.delete()
        update_ejabberd_config()
        return HttpResponseRedirect(
                reverse('config:hosts')
            )


class DetailHost(LoginRequiredMixin, TemplateView):
    template_name = 'config/host_detail.html'

    @permission_admin
    def get(self, request, id, *args, **kwargs):

        try:
            host = VirtualHost.objects.get(id=id)
        except VirtualHost.DoesNotExist:
            raise Http404

        context = {
            'host': host
        }
        return self.render_to_response(context)


class CreateHost(LoginRequiredMixin, TemplateView):
    template_name = 'config/host_create.html'

    @permission_admin
    def get(self, request, *args, **kwargs):
        context = {}
        return self.render_to_response(context)

    @permission_admin
    def post(self, request, *args, **kwargs):
        host = request.POST.get('host')
        self.api = get_api(request)

        # check virtualhost already exists
        vh_check = VirtualHost.objects.filter(name=host).exists()

        if host_is_valid(host) and not vh_check:

            # check srv records
            check_dns = False
            records = get_srv_records(host)
            if not 'error' in records:
                check_dns = True

            VirtualHost.objects.create(
                name=host,
                check_dns=check_dns
            )

            # update config after creating new host
            update_ejabberd_config()

            # create groups after update config
            self.create_everybody_group(request, host)

            # check api errors
            error_messages = get_error_messages(request)
            if not error_messages:
                messages.success(request, f'Virtual host "{host}" created successfully.')

            return HttpResponseRedirect(
                reverse('config:hosts')
            )

        messages.error(request, f'Host "{host}" is invalid or already exists.')
        return self.render_to_response({})

    def create_everybody_group(self, request, host):

        try:
            Circle.objects.create(
                circle=host,
                host=host,
                name=settings.EJABBERD_DEFAULT_GROUP_NAME,
                description=settings.EJABBERD_DEFAULT_GROUP_DESCRIPTION,
                prefix=get_system_group_suffix(),
                all_users=True
            )
        except Exception as e:
            messages.error(request, e)
            return

        self.api.create_circle(
            {
                'circle': host,
                'host': host,
                'name': settings.EJABBERD_DEFAULT_GROUP_NAME,
                'description': settings.EJABBERD_DEFAULT_GROUP_DESCRIPTION,
                'all_users': True
            }
        )


class CheckDnsRecords(View):

    def get(self, request):
        check_hosts_dns()
        return render(request, 'config/parts/host_list.html')


class Admins(LoginRequiredMixin, TemplateView):
    template_name = 'config/admins.html'

    @permission_admin
    def get(self, request, *args, **kwargs):
        api = get_api(request)

        for host in VirtualHost.objects.all():
            check_users(api, host.name)

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

    @permission_read
    def get(self, request, *args, **kwargs):

        host = request.current_host

        context = {}

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

        context = {
            'form': self.form
        }

        self.server_list = self.clean_server_list()
        if self.form.is_valid():
            self.update_or_create_ldap()
            update_ejabberd_config()

            if is_ejabberd_started():
                restart_ejabberd()

            messages.success(request, 'Ldap settings changed successfully.')
        else:
            for error in self.form.errors.values():
                messages.error(request, f'{error}')

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
            host=self.request.current_host,
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
        self.temp_extract_dir = os.path.join(settings.BASE_DIR, 'temp_extract')

        try:
            # Create temporary dir for unpack
            os.makedirs(self.temp_extract_dir, exist_ok=True)

            # Unpack archieve in temporary dir
            with tarfile.open(fileobj=self.uploaded_file, mode='r:gz') as tar:
                tar.extractall(self.temp_extract_dir)

            module_name, version = self.check_version()

            # Get nested dir inside 'panel'
            panel_path = os.path.join(self.temp_extract_dir, 'panel')
            module_path = os.path.join(panel_path, module_name)

            if os.path.isdir(module_path):

                # Copy module in modules dir
                self.install_module(panel_path, module_name)

                # after installation actions
                self.after_install(module_name, version)

                messages.success(self.request, 'Modules added successfully.')
            else:
                raise Exception('Module folder is missed.')
        except Exception as e:
            # Delete temporary dir
            shutil.rmtree(self.temp_extract_dir, ignore_errors=True)
            messages.error(self.request, e)

    def install_module(self, panel_path, module_dir):

        app_name = f'modules.{module_dir}'

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

    def check_version(self):

        # read module spec
        spec_path = os.path.join(self.temp_extract_dir, 'module.spec')
        if os.path.exists(spec_path):
            with open(spec_path, 'r') as file:
                content = file.read()
        else:
            raise Exception('Module spec information is missed.')

        name_match = re.search(r'NAME\s*=\s*([^\n]+)', content)
        version_match = re.search(r'VERSION\s*=\s*([^\n]+)', content)

        if name_match and version_match:
            module_name = name_match.group(1).strip().lower()
            version = version_match.group(1).strip().lower()
        else:
            raise Exception('Module spec is incorrect.')

        module = Module.objects.filter(name=module_name).first()
        if module:

            # check version if module already installed
            try:
                installed_version = tuple(map(int, module.version.split('.')))
                new_version = tuple(map(int, version.split('.')))
            except ValueError:
                raise Exception("Invalid version format.")

            if new_version < installed_version:
                raise Exception("You have a newer module version.")
            elif new_version == installed_version:
                raise Exception("You already have this module.")

        return module_name, version

    def after_install(self, module_name, version):

        # get module verbose name
        try:
            module_app = import_module('.apps', package=f'modules.{module_name}')
        except:
            module_app = None

        verbose_name = ''
        if module_app:
            module_config = getattr(module_app, 'ModuleConfig', None)

            if module_config:
                verbose_name = getattr(module_config, 'verbose_name', module_name)

        # update module info
        Module.objects.update_or_create(
            name=module_name,
            defaults={
                'version': version,
                'verbose_name': verbose_name
            }
        )

        # create permissions for new modules
        management.call_command('update_permissions')

        # Delete temporary dir
        shutil.rmtree(self.temp_extract_dir)

        make_xmpp_config()
        get_app_template_dirs.cache_clear()

        reload_server()


class DeleteModule(LoginRequiredMixin, TemplateView):

    @permission_admin
    def get(self, request, module, *args, **kwargs):
        module_path = os.path.join(settings.MODULES_DIR, module)
        app_name = f'modules.{module}'

        if os.path.isdir(module_path) and apps.is_installed(app_name):
            self.hande_delete(module_path, module, app_name)

            messages.success(request, f'Module "{module}" deleted successfully.')
            return HttpResponseRedirect(reverse('config:modules'))
        else:
            raise Http404

    def hande_delete(self, module_path, module, app_name):

        # migrate db if module has migrations
        if os.path.exists(os.path.join(module_path, 'migrations', '__init__.py')):
            management.call_command('migrate', module, 'zero', interactive=True)

        if not settings.DEBUG:
            management.call_command('collectstatic', '--noinput', interactive=False)

        shutil.rmtree(module_path)

        # delete module info
        Module.objects.filter(name=module).delete()

        settings.INSTALLED_APPS.remove(app_name)

        # update app list
        update_app_list(settings.INSTALLED_APPS)

        management.call_command('update_permissions')
        make_xmpp_config()

        reload_server()


class RootPageView(LoginRequiredMixin, TemplateView):
    template_name = 'config/root_page.html'

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

        messages.success(request, 'Root page changed successfully.')

        return self.render_to_response({})


class ChangeHost(View):

    def post(self, request, *args, **kwargs):
        host_id = request.POST.get('host')

        try:
            host = VirtualHost.objects.get(id=host_id)
        except VirtualHost.DoesNotExist:
            raise Http404

        request.session['host'] = host_id

        referer = request.META.get('HTTP_REFERER')
        if referer:
            # If there is a referer, redirect to it
            return HttpResponseRedirect(referer)
        else:
            return HttpResponseRedirect(reverse('home'))