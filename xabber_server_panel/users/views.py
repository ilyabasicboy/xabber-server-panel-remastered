from django.shortcuts import render, reverse
from django.views.generic import TemplateView
from django.http import HttpResponseNotFound, HttpResponseRedirect
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone

from xabber_server_panel.dashboard.models import VirtualHost
from xabber_server_panel.circles.models import Circle

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
            {
                'username': cleaned_data.get('username'),
                'host': cleaned_data.get('host'),
                'password': cleaned_data.get('password'),
                'nickname': cleaned_data.get('nickname'),
                'first_name': cleaned_data.get('first_name'),
                'last_name': cleaned_data.get('last_name'),
                'photo': None,
                'is_admin': cleaned_data.get('is_admin'),
                'expires': cleaned_data.get('expires'),
                'vcard': {
                    'nickname': cleaned_data.get('nickname'),
                    'n': {
                        'given': cleaned_data.get('first_name'),
                        'family': cleaned_data.get('last_name')
                    },
                    'photo': {'type': '', 'binval': ''}
                }
            }
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

        circles = Circle.objects.filter(host=user.host)

        context = {
            'user': user,
            'circles': circles
        }
        return self.render_to_response(context)

    def post(self, request, id, *args, **kwargs):
        try:
            self.user = User.objects.get(id=id)
        except ObjectDoesNotExist:
            return HttpResponseNotFound

        delete = request.POST.get('delete')
        if delete:
            self.user.delete()
            return HttpResponseRedirect(reverse('users:list'))

        self.circles = Circle.objects.filter(host=self.user.host)

        # update user params
        self.update_user()

        context = {
            'user': self.user,
            'circles': self.circles
        }
        return self.render_to_response(context)

    def update_user(self):
        if 'nickname' in self.request.POST:
            self.user.nickname = self.request.POST.get('nickname')

        if 'first_name' in self.request.POST:
            self.user.first_name = self.request.POST.get('first_name')

        if 'last_name' in self.request.POST:
            self.user.last_name = self.request.POST.get('last_name')

        status = self.request.POST.get('status')
        if status and self.user.status != status:
            self.change_status(status)

        # set expires if its provided
        if 'expires' in self.request.POST:
            self.change_expires()

        # change circles in db and send data to server
        circles = self.request.POST.getlist('circles', [])
        self.change_circles(circles)

        password = self.request.POST.get('password')
        confirm_password = self.request.POST.get('confirm_password')
        if password and confirm_password:
            self.change_password(password, confirm_password)

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

    def change_circles(self, circles):

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

    def change_password(self, password, confirm_password):
        if password == confirm_password:
            # Change the user's password
            self.user.set_password(password)


class UserList(TemplateView):

    template_name = 'users/list.html'

    def get(self, request, *args, **kwargs):
        hosts = VirtualHost.objects.all()
        self.users = User.objects.all()

        if hosts.exists():
            host = request.GET.get('host', hosts.first().name)

            self.check_users(host)

            users = self.users.filter(host=host)

        context = {
            'hosts': hosts,
            'users': users,
        }

        if request.is_ajax():
            return render(request, 'users/parts/user_list.html', context)

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

            # Filter the user_list to exclude existing usernames
            unknown_users = [user for user in registered_users if user['username'] not in existing_usernames]

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

                self.users = User.objects.all()