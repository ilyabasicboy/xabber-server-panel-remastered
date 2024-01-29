from django.shortcuts import render, reverse, loader
from django.views.generic import TemplateView
from django.http import HttpResponseNotFound, HttpResponseRedirect, JsonResponse
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.utils import timezone

from xabber_server_panel.dashboard.models import VirtualHost
from xabber_server_panel.circles.models import Circle
from xabber_server_panel.utils import get_user_data_for_api
from xabber_server_panel.users.decorators import permission_read, permission_write

from datetime import datetime

from .models import User, CustomPermission
from .forms import UserForm
from .utils import check_users


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
        self.request.user.api.create_user(
            get_user_data_for_api(user, cleaned_data.get('password'))
        )
        if user.is_admin:
            user.api.xabber_set_admin(
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

        self.circles = Circle.objects.filter(host=self.user.host)

        # update user params
        self.update_user()

        messages.success(request, 'User changed successfully.')

        context = {
            'user': self.user,
            'circles': self.circles
        }
        return self.render_to_response(context)

    def update_user(self):

        status = self.request.POST.get('status')
        if status and self.user.status != status:
            self.change_status(status)

        # set expires if its provided
        if 'expires' in self.request.POST:
            self.change_expires()

        self.user.save()

    def change_expires(self):
        """ Change user expires and send data to server """

        expires = self.request.POST.get('expires')
        if expires:
            try:
                expires_datetime = datetime.strptime(expires, '%Y-%m-%d')
                self.user.expires = expires_datetime.replace(tzinfo=timezone.utc)
            except Exception as e:
                messages.error(self.request, e)
                self.user.expires = None
        else:
            self.user.expires = None

        # send data to server
        data = {
            "host": self.user.host,
            "username": self.user.username
        }
        if self.user.status == 'EXPIRED':
            if not self.user.is_expired:
                self.user.api.unblock_user(data)
                self.user.status = 'ACTIVE'
        elif self.user.is_active:
            if self.user.is_expired:
                data['reason'] = "Your account has expired"
                self.user.api.block_user(data)
                self.user.status = 'EXPIRED'

    def change_status(self, status):

        """ Change status and send data to server """

        data = {
            "username": self.user.username,
             "host": self.user.host,
        }
        if status == 'SUSPENDED':
            data['reason'] = self.request.POST.get('reason')
            self.user.api.block_user(data)
            self.user.status = status

        elif status == 'EXPIRED':
            data['reason'] = "Your account has expired"
            self.user.api.block_user(data)
            self.user.status = status

        elif status == 'BANNED':
            if not self.user.is_active:
                self.user.api.unblock_user(data)

            self.user.api.ban_user(data)

            self.user.status = status

        elif status == 'ACTIVE':
            if self.user.status == 'SUSPENDED':
                self.user.api.unblock_user(data)
                if self.user.is_expired:
                    self.user.expires = None

                self.user.status = status

            if self.user.status == 'BANNED':
                self.user.api.unban_user(data)

                if self.user.is_expired:
                    data['reason'] = "Your account has expired"
                    self.user.api.block_user(data)
                    self.user.status = 'EXPIRED'
                else:
                    self.user.status = status


class UserDelete(LoginRequiredMixin, TemplateView):
    app = 'users'

    @permission_write
    def get(self, request, id, *args, **kwargs):

        try:
            user = User.objects.get(id=id)
        except ObjectDoesNotExist:
            return HttpResponseNotFound

        if user.full_jid != request.user.full_jid:
            user.delete()
            request.user.api.unregister_user(
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

        self.request.user.api.edit_user_vcard(
            get_user_data_for_api(self.user)
        )

        self.user.save()


class UserSecurity(LoginRequiredMixin, TemplateView):

    template_name = 'users/security.html'
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

        # update user params
        self.update_user()

        context = {
            'user': self.user,
        }
        return self.render_to_response(context)

    def update_user(self):
        password = self.request.POST.get('password')
        confirm_password = self.request.POST.get('confirm_password')
        if password and confirm_password:
            if password == confirm_password:
                # Change the user's password
                self.user.set_password(password)
                messages.success(self.request, 'Password changed successfully.')
            else:
                messages.error(self.request, 'Password is incorrect.')

        self.user.save()

        self.request.user.api.change_password_api(
            {
                'password': password,
                'username': self.user.username,
                'host': self.user.host
            }
        )


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
            self.user.api.srg_user_add_api(
                {
                    'circle': circle.circle,
                    'host': circle.host,
                    'members': [self.user.full_jid]
                }
            )

        # delete circles
        circles_to_delete = self.circles.filter(id__in=ids_to_delete)
        for circle in circles_to_delete:
            self.user.api.srg_user_del_api(
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
            check_users(request.user, host)

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

    @permission_read
    def get(self, request, id, *args, **kwargs):
        try:
            user = User.objects.get(id=id)
        except ObjectDoesNotExist:
            return HttpResponseNotFound

        permissions = {
            app[0]: CustomPermission.objects.filter(app=app[0])
            for app in CustomPermission.APPS
        }

        context = {
            'user': user,
            'permissions': permissions
        }
        return self.render_to_response(context)

    @permission_write
    def post(self, request, id, *args, **kwargs):
        try:
            self.user = User.objects.get(id=id)
        except ObjectDoesNotExist:
            return HttpResponseNotFound

        self.update_permissions()

        messages.success(self.request, 'Permissions changed successfully.')

        permissions = {
            app[0]: CustomPermission.objects.filter(app=app[0])
            for app in CustomPermission.APPS
        }

        context = {
            'user': self.user,
            'permissions': permissions
        }
        return self.render_to_response(context)

    def update_permissions(self):

        is_admin = self.request.POST.get('is_admin', False)

        permission_id_list = []

        for app in CustomPermission.APPS:
            app_permission_id_list = self.request.POST.getlist(f'permissions_{app[0]}', [])
            permission_id_list += app_permission_id_list

        permission_list = CustomPermission.objects.filter(id__in=permission_id_list)

        self.user.is_admin = True if is_admin else False

        self.user.permissions.set(permission_list)

        self.user.save()

        if is_admin:
            self.request.user.api.xabber_set_admin(
                {
                    "username": self.user.username,
                    "host": self.user.host
                }
            )
        else:
            self.request.user.api.xabber_del_admin(
                {
                    "username": self.user.username,
                    "host": self.user.host,
                }
            )

            permissions = self.get_permissions_dict()

            self.request.user.api.xabber_set_permissions(
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