from django.shortcuts import render, reverse
from django.views.generic import TemplateView
from django.http import HttpResponseNotFound, HttpResponseRedirect
from django.core.exceptions import ObjectDoesNotExist

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
        self.request_data = dict(request.POST)

        try:
            self.user = User.objects.get(id=id)
        except ObjectDoesNotExist:
            return HttpResponseNotFound

        delete = request.POST.get('delete')
        if delete:
            self.user.delete()
            return HttpResponseRedirect(reverse('users:list'))

        # update user params
        self.update_user()

        circles = Circle.objects.filter(host=self.user.host)

        context = {
            'user': self.user,
            'circles': circles
        }
        return self.render_to_response(context)

    def update_user(self):
        if 'nickname' in self.request.POST:
            self.user.nickname = self.request.POST.get('nickname')

        if 'first_name' in self.request.POST:
            self.user.first_name = self.request.POST.get('first_name')

        if 'last_name' in self.request.POST:
            self.user.last_name = self.request.POST.get('last_name')

        expires = self.request_data.get('expires')

        if expires:
            try:
                self.user.expires = datetime.strptime(expires, '%Y-%m-%d')
            except:
                pass

        circles = self.request_data.get('circles', [])
        self.user.circles.set(circles)

        password = self.request_data.get('password')
        confirm_password = self.request_data.get('confirm_password')
        if password and confirm_password:
            self.change_password(password, confirm_password)

        self.user.save()

    def change_password(self, password, confirm_password):
        if password == confirm_password:
            # Change the user's password
            self.user.set_password(password)


class UserList(TemplateView):

    template_name = 'users/list.html'

    def get(self, request, *args, **kwargs):
        hosts = VirtualHost.objects.all()
        users = User.objects.all()

        if hosts.exists():
            host = request.GET.get('host', hosts.first().name)
            users = users.filter(host=host)

        context = {
            'hosts': hosts,
            'users': users,
        }

        if request.is_ajax():
            return render(request, 'users/parts/user_list.html', context)

        return self.render_to_response(context)