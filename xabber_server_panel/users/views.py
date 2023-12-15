from django.shortcuts import render, reverse, loader
from django.views.generic import TemplateView
from django.http import HttpResponseNotFound, HttpResponseRedirect, JsonResponse
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone

from xabber_server_panel.dashboard.models import VirtualHost
from xabber_server_panel.circles.models import Circle
from xabber_server_panel.utils import get_user_data_for_api

from datetime import datetime

from .models import User
from .forms import UserForm


class CreateUser(TemplateView):

    template_name = 'users/create.html'

    def get(self, request, *args, **kwargs):

        context = {
            'hosts': VirtualHost.objects.all(),
            'form': UserForm()
        }

        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):

        form = UserForm(request.POST)

        if form.is_valid():
            user = form.save()
            self.create_user_api(user, form.cleaned_data)

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


class UserDetail(TemplateView):

    template_name = 'users/detail.html'

    def get(self, request, id, *args, **kwargs):
        try:
            user = User.objects.get(id=id)
        except ObjectDoesNotExist:
            return HttpResponseNotFound

        delete = kwargs.get('delete')
        if delete:
            if user.full_jid != request.user.full_jid:
                user.delete()
                request.user.api.unregister_user(
                    {
                        'username': user.username,
                        'host': user.host
                    }
                )
            else:
                print('You can not delete yourself')
            return HttpResponseRedirect(reverse('users:list'))

        circles = Circle.objects.filter(host=user.host)

        context = {
            'user': user,
            'circles': circles,
        }
        return self.render_to_response(context)

    def post(self, request, id, *args, **kwargs):
        try:
            self.user = User.objects.get(id=id)
        except ObjectDoesNotExist:
            return HttpResponseNotFound

        self.circles = Circle.objects.filter(host=self.user.host)

        # update user params
        self.update_user()

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
        try:
            expires_datetime = datetime.strptime(expires, '%Y-%m-%d')
            self.user.expires = expires_datetime.replace(tzinfo=timezone.utc)
        except Exception as e:
            print(e)
            self.user.expires = None
            pass

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


class UserVcard(TemplateView):

    template_name = 'users/vcard.html'

    def get(self, request, id, *args, **kwargs):
        try:
            user = User.objects.get(id=id)
        except ObjectDoesNotExist:
            return HttpResponseNotFound

        context = {
            'user': user,
        }
        return self.render_to_response(context)

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
        self.user.nickname = self.request.POST.get('nickname')

        self.user.first_name = self.request.POST.get('first_name')

        self.user.last_name = self.request.POST.get('last_name')

        self.request.user.api.edit_user_vcard(
            get_user_data_for_api(self.user)
        )

        self.user.save()


class UserSecurity(TemplateView):

    template_name = 'users/security.html'

    def get(self, request, id, *args, **kwargs):
        try:
            user = User.objects.get(id=id)
        except ObjectDoesNotExist:
            return HttpResponseNotFound

        context = {
            'user': user,
        }
        return self.render_to_response(context)

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

        self.user.save()

        self.request.user.api.change_password_api(
            {
                'password': password,
                'username': self.user.username,
                'host': self.user.host
            }
        )


class UserCircles(TemplateView):

    template_name = 'users/circles.html'

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

    def post(self, request, id, *args, **kwargs):
        try:
            self.user = User.objects.get(id=id)
        except ObjectDoesNotExist:
            return HttpResponseNotFound

        self.circles = Circle.objects.filter(host=self.user.host)

        # update user params
        self.update_user()

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


class UserList(TemplateView):

    template_name = 'users/list.html'

    def get(self, request, *args, **kwargs):
        hosts = VirtualHost.objects.all()
        self.users = User.objects.all()

        context = {
            'hosts': hosts,
        }

        if hosts.exists():
            host = request.GET.get('host', request.session.get('host', hosts.first().name))
            request.session['host'] = host
            context['curr_host'] = host
            self.check_users(host)

            self.users = self.users.filter(host=host)

        context['users'] = self.users

        if request.is_ajax():
            html = loader.render_to_string('users/parts/user_list.html', context, request)
            response_data = {
                'html': html,
                'items_count': self.users.count(),
            }
            return JsonResponse(response_data)

        return self.render_to_response(context)

    def check_users(self, host):

        """
            Check registered users and create
            if it doesn't exist in django db
        """

        try:
            registered_users = self.request.user.api.xabber_registered_users({"host": host}).get('users')
        except:
            registered_users = []

        if registered_users:
            # Get a list of existing usernames from the User model
            existing_usernames = self.users.values_list('username', flat=True)

            # get registered usernames list
            registered_usernames = [user['username'] for user in registered_users]

            # Filter the user_list to exclude existing usernames
            unknown_users = [user for user in registered_users if user['username'] not in existing_usernames]

            # create in db unknown users
            if unknown_users:
                users_to_create = [
                    User(
                        username=user['username'],
                        host=host,
                        auth_backend=user['backend']
                    )
                    for user in unknown_users
                ]
                User.objects.bulk_create(users_to_create)

            # get unregistered users in db and delete
            users_to_delete = User.objects.filter(host=host).exclude(username__in=registered_usernames)
            if users_to_delete:
                users_to_delete.delete()

        self.users = User.objects.all()