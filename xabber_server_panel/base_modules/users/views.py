from django.shortcuts import reverse, loader
from django.views.generic import TemplateView
from django.http import HttpResponseNotFound, HttpResponseRedirect, JsonResponse
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages

from xabber_server_panel.base_modules.config.models import VirtualHost
from xabber_server_panel.base_modules.circles.models import Circle
from xabber_server_panel.utils import get_user_data_for_api
from xabber_server_panel.base_modules.users.decorators import permission_read, permission_write, permission_admin
from xabber_server_panel.api.utils import get_api

from .models import User, CustomPermission, get_apps_choices
from .forms import UserForm
from .utils import check_users, block_user, ban_user, unblock_user, set_expires


class CreateUser(LoginRequiredMixin, TemplateView):

    template_name = 'users/create.html'
    app = 'users'

    @permission_write
    def get(self, request, *args, **kwargs):

        context = {
            'hosts': VirtualHost.objects.all(),
            'form': UserForm()
        }

        return self.render_to_response(context)

    @permission_write
    def post(self, request, *args, **kwargs):

        form = UserForm(request.POST)
        self.api = get_api(request)

        if form.is_valid():
            user = form.save()
            self.create_user_api(user, form.cleaned_data)
            messages.success(request, 'User created successfully.')
            return HttpResponseRedirect(
                reverse(
                    'users:detail',
                    kwargs={
                        'id': user.id
                    }
                )
            )

        context = {
            'hosts': VirtualHost.objects.all(),
            'form': form
        }
        return self.render_to_response(context)

    def create_user_api(self, user, cleaned_data):
        self.api.create_user(
            get_user_data_for_api(user, cleaned_data.get('password'))
        )
        if user.is_admin:
            self.api.set_admin(
                {
                    "username": cleaned_data['username'],
                    "host": cleaned_data['host']
                }
            )


class UserDetail(LoginRequiredMixin, TemplateView):

    template_name = 'users/detail.html'
    app = 'users'

    @permission_read
    def get(self, request, id, *args, **kwargs):
        try:
            user = User.objects.get(id=id)
        except ObjectDoesNotExist:
            return HttpResponseNotFound

        circles = Circle.objects.filter(host=user.host)

        context = {
            'user': user,
            'circles': circles,
        }
        return self.render_to_response(context)

    @permission_write
    def post(self, request, id, *args, **kwargs):
        try:
            self.user = User.objects.get(id=id)
        except ObjectDoesNotExist:
            return HttpResponseNotFound

        self.api = get_api(request)

        self.errors = []
        self.circles = Circle.objects.filter(host=self.user.host)

        # update user params
        self.update_user()

        if self.errors:
            for error in self.errors:
                messages.error(request, error)
        else:
            messages.success(request, 'User changed successfully.')

        context = {
            'user': self.user,
            'circles': self.circles
        }
        return self.render_to_response(context)

    def update_user(self):

        password = self.request.POST.get('password')
        confirm_password = self.request.POST.get('confirm_password')
        if password and confirm_password:

            # Check user auth backend
            if self.user.auth_backend_is_ldap:
                self.errors += ['User auth backend is "ldap". Password cant be changed.']

            elif password == confirm_password:

                self.api.change_password_api(
                    {
                        'password': password,
                        'username': self.user.username,
                        'host': self.user.host
                    }
                )

                # Change the user's password
                self.user.set_password(password)

            else:
                self.errors += ['Password is incorrect.']

        # set expires if its provided
        # BEFORE CHANGE STATUS!!!
        if 'expires' in self.request.POST:
            expires = self.request.POST.get('expires')
            set_expires(self.api, self.user, expires)

        status = self.request.POST.get('status')
        if status and self.user.status != status:
            self.change_status(status)

        self.user.save()

    def change_status(self, status):

        """ Change status and send data to server """

        if status == 'BLOCKED':
            reason = self.request.POST.get('reason')
            if self.request.user != self.user:
                block_user(self.api, self.user, reason)
            else:
                self.errors += ['You can not block yourself.']

        elif status == 'BANNED' and not self.user.auth_backend_is_ldap:
            if self.request.user != self.user:
                ban_user(self.api, self.user)
            else:
                self.errors += ['You can not ban yourself.']

        elif status == 'ACTIVE':
            unblock_user(self.api, self.user)


class UserBlock(LoginRequiredMixin, TemplateView):
    app = 'users'

    @permission_write
    def get(self, request, id, *args, **kwargs):
        try:
            user = User.objects.get(id=id)
        except ObjectDoesNotExist:
            return HttpResponseNotFound

        api = get_api(request)

        reason = self.request.GET.get('reason')
        block_user(api, user, reason)
        return HttpResponseRedirect(reverse('users:list'))


class UserUnBlock(LoginRequiredMixin, TemplateView):
    app = 'users'

    @permission_write
    def get(self, request, id, *args, **kwargs):
        try:
            user = User.objects.get(id=id)
        except ObjectDoesNotExist:
            return HttpResponseNotFound

        api = get_api(request)

        unblock_user(api, user)
        return HttpResponseRedirect(reverse('users:list'))


class UserDelete(LoginRequiredMixin, TemplateView):
    app = 'users'

    @permission_write
    def get(self, request, id, *args, **kwargs):

        try:
            user = User.objects.get(id=id)
        except ObjectDoesNotExist:
            return HttpResponseNotFound

        api = get_api(request)

        if user.auth_backend_is_ldap:
            messages.error(request, 'User auth backend is "ldap". User cant be deleted.')
        elif user.full_jid != request.user.full_jid:
            user.delete()
            api.unregister_user(
                {
                    'username': user.username,
                    'host': user.host
                }
            )
            messages.success(request, 'User deleted successfully.')
        else:
            messages.error(request, 'You can not delete yourself.')
        return HttpResponseRedirect(reverse('users:list'))


class UserVcard(LoginRequiredMixin, TemplateView):

    template_name = 'users/vcard.html'
    app = 'users'

    @permission_read
    def get(self, request, id, *args, **kwargs):
        try:
            user = User.objects.get(id=id)
        except ObjectDoesNotExist:
            return HttpResponseNotFound

        context = {
            'user': user,
        }
        return self.render_to_response(context)

    @permission_write
    def post(self, request, id, *args, **kwargs):
        try:
            self.user = User.objects.get(id=id)
        except ObjectDoesNotExist:
            return HttpResponseNotFound

        self.api = get_api(request)

        # update user params
        self.update_user()

        messages.success(request, 'User changed successfully.')

        context = {
            'user': self.user,
        }
        return self.render_to_response(context)

    def update_user(self):
        self.user.nickname = self.request.POST.get('nickname')

        self.user.first_name = self.request.POST.get('first_name')

        self.user.last_name = self.request.POST.get('last_name')

        self.api.set_vcard(
            get_user_data_for_api(self.user)
        )

        self.user.save()


class UserCircles(LoginRequiredMixin, TemplateView):

    template_name = 'users/circles.html'
    app = 'users'

    @permission_read
    def get(self, request, id, *args, **kwargs):
        try:
            user = User.objects.get(id=id)
        except ObjectDoesNotExist:
            return HttpResponseNotFound

        self.circles = Circle.objects.filter(host=user.host)

        context = {
            'user': user,
            'circles': self.circles
        }
        return self.render_to_response(context)

    @permission_write
    def post(self, request, id, *args, **kwargs):
        try:
            self.user = User.objects.get(id=id)
        except ObjectDoesNotExist:
            return HttpResponseNotFound

        self.circles = Circle.objects.filter(host=self.user.host)
        self.api = get_api(request)

        # update user params
        self.update_user()

        messages.success(self.request, 'User changed successfully.')

        context = {
            'user': self.user,
            'circles': self.circles
        }
        return self.render_to_response(context)

    def update_user(self):
        # change circles in db and send data to server
        circles = self.request.POST.getlist('circles', [])

        new_circles = set(map(int, circles))
        existing_circles = set(self.user.circles.values_list('id', flat=True))

        # Added circles id list
        ids_to_add = new_circles - existing_circles

        # Removed circles id list
        ids_to_delete = existing_circles - new_circles

        # add circles
        circles_to_add = self.circles.filter(id__in=ids_to_add)
        for circle in circles_to_add:
            self.api.add_circle_members(
                {
                    'circle': circle.circle,
                    'host': circle.host,
                    'members': [self.user.full_jid]
                }
            )

        # delete circles
        circles_to_delete = self.circles.filter(id__in=ids_to_delete)
        for circle in circles_to_delete:
            self.api.del_circle_members(
                {
                    'circle': circle.circle,
                    'host': circle.host,
                    'members': [self.user.full_jid]
                }
            )
        self.user.circles.set(circles)

        self.user.save()


class UserList(LoginRequiredMixin, TemplateView):

    template_name = 'users/list.html'
    app = 'users'

    @permission_read
    def get(self, request, *args, **kwargs):
        hosts = request.user.get_allowed_hosts()
        self.users = User.objects.none()
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
            check_users(api, host)

            self.users = User.objects.filter(host=host)

        context['users'] = self.users.order_by('username')

        if request.is_ajax():
            html = loader.render_to_string('users/parts/user_list.html', context, request)
            response_data = {
                'html': html,
                'items_count': self.users.count(),
            }
            return JsonResponse(response_data)

        return self.render_to_response(context)


class UserPermissions(LoginRequiredMixin, TemplateView):
    template_name = 'users/permissions.html'
    app = 'users'

    @permission_admin
    def get(self, request, id, *args, **kwargs):
        try:
            user = User.objects.get(id=id)
        except ObjectDoesNotExist:
            return HttpResponseNotFound

        # check if user change himself
        if user == request.user:
            messages.error(request, 'You cant change self permissions.')
            return HttpResponseRedirect(reverse('home'))

        permissions = {
            app[0]: CustomPermission.objects.filter(app=app[0])
            for app in get_apps_choices()
        }

        context = {
            'user': user,
            'permissions': permissions
        }
        return self.render_to_response(context)

    @permission_admin
    def post(self, request, id, *args, **kwargs):
        try:
            self.user = User.objects.get(id=id)
        except ObjectDoesNotExist:
            return HttpResponseNotFound

        # check if user change himself
        if self.user == request.user:
            messages.error(request, 'You cant change self permissions.',)
            return HttpResponseRedirect(reverse('home'))

        self.api = get_api(request)

        self.update_permissions()

        messages.success(self.request, 'Permissions changed successfully.')

        permissions = {
            app[0]: CustomPermission.objects.filter(app=app[0])
            for app in get_apps_choices()
        }

        context = {
            'user': self.user,
            'permissions': permissions
        }
        return self.render_to_response(context)

    def update_permissions(self):

        is_admin = self.request.POST.get('is_admin', False)

        permission_id_list = []

        for app in get_apps_choices():
            app_permission_id_list = self.request.POST.getlist(f'permissions_{app[0]}', [])
            permission_id_list += app_permission_id_list

        permission_list = CustomPermission.objects.filter(id__in=permission_id_list)

        self.user.is_admin = True if is_admin else False

        self.user.permissions.set(permission_list)

        self.user.save()

        if is_admin:
            self.api.set_admin(
                {
                    "username": self.user.username,
                    "host": self.user.host
                }
            )
        else:
            self.api.del_admin(
                {
                    "username": self.user.username,
                    "host": self.user.host,
                }
            )

            permissions = self.get_permissions_dict()

            self.api.set_permissions(
                {
                    "username": self.user.username,
                    "host": self.user.host,
                    "permissions": permissions,
                }
            )

    def get_permissions_dict(self):

        """
            Create permissions dict depending on selected user permissions
        """

        permissions = {}

        circles_read = self.user.permissions.filter(app='circles', permission='read').exists()
        circles_write = self.user.permissions.filter(app='circles', permission='write').exists()
        if circles_write:
            permissions['circles'] = 'write'
        elif circles_read:
            permissions['circles'] = 'read'
        else:
            permissions['circles'] = 'forbidden'

        dashboard_read = self.user.permissions.filter(app='dashboard', permission='read').exists()
        dashboard_write = self.user.permissions.filter(app='dashboard', permission='write').exists()
        if dashboard_write:
            permissions['server'] = 'write'
        elif dashboard_read:
            permissions['server'] = 'read'
        else:
            permissions['server'] = 'forbidden'

        groups_read = self.user.permissions.filter(app='groups', permission='read').exists()
        groups_write = self.user.permissions.filter(app='groups', permission='write').exists()
        if groups_write:
            permissions['groups'] = 'write'
        elif groups_read:
            permissions['groups'] = 'read'
        else:
            permissions['groups'] = 'forbidden'

        users_read = self.user.permissions.filter(app='users', permission='read').exists()
        users_write = self.user.permissions.filter(app='users', permission='write').exists()
        if users_write:
            permissions['users'] = 'write'
            permissions['vcard'] = 'write'
        elif users_read:
            permissions['users'] = 'read'
            permissions['vcard'] = 'read'
        else:
            permissions['users'] = 'forbidden'
            permissions['vcard'] = 'forbidden'

        return permissions