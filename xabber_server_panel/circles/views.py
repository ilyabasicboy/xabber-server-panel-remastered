from django.shortcuts import render, reverse
from django.views.generic import TemplateView
from django.http import HttpResponseNotFound, HttpResponseRedirect
from django.core.exceptions import ObjectDoesNotExist

from xabber_server_panel.circles.models import Circle
from xabber_server_panel.dashboard.models import VirtualHost
from xabber_server_panel.users.models import User

from .forms import CircleForm


class CircleList(TemplateView):
    template_name = 'circles/list.html'

    def get(self, request, *args, **kwargs):

        hosts = VirtualHost.objects.all()
        circles = Circle.objects.all()

        if hosts.exists():
            host = request.GET.get('host', hosts.first().name)
            circles = circles.filter(host=host)

        context = {
            'circles': circles,
            'hosts': hosts
        }

        if request.is_ajax():
            return render(request, 'circles/parts/circle_list.html', context)
        return self.render_to_response(context)


class CircleCreate(TemplateView):
    template_name = 'circles/create.html'

    def get(self, request, *args, **kwargs):

        form = CircleForm()
        context = {
            'form': form,
            'hosts': VirtualHost.objects.all(),
        }
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):

        form = CircleForm(request.POST)

        if form.is_valid():
            circle = form.save()
            return HttpResponseRedirect(
                reverse(
                    'circles:detail',
                    kwargs={'id': circle.id}
                )
            )

        context = {
            'form': form,
            'hosts': VirtualHost.objects.all(),
        }
        return self.render_to_response(context)


class CircleDetail(TemplateView):

    template_name = 'circles/detail.html'

    def get(self, request, id, *args, **kwargs):

        try:
            circle = Circle.objects.get(id=id)
        except ObjectDoesNotExist:
            return HttpResponseNotFound

        users = User.objects.filter(status='ACTIVE')
        circles = Circle.objects.filter(host=circle.host)

        context = {
            'circle': circle,
            'users': users,
            'circles': circles
        }

        return self.render_to_response(context)

    def post(self, request, id, *args, **kwargs):

        try:
            self.circle = Circle.objects.get(id=id)
        except ObjectDoesNotExist:
            return HttpResponseNotFound

        self.request_data = dict(request.POST)

        delete = request.POST.get('delete')
        if delete:
            self.circle.delete()
            return HttpResponseRedirect(reverse('circles:list'))

        users = User.objects.filter(status='ACTIVE')
        circles = Circle.objects.filter(host=self.circle.host)

        self.update_circle()

        context = {
            'circle': self.circle,
            'users': users,
            'circles': circles
        }

        return self.render_to_response(context)

    def update_circle(self):

        name = self.request_data.get('name')
        if name:
            self.circle.name = name

        description = self.request_data.get('description')
        self.circle.description = description

        # add member by jid
        add_member = self.request_data.get('add_member')
        if add_member:
            try:
                username, host = add_member.split('@')
            except:
                print('jid is incorrect')

            user = User.objects.filter(username=username, host=host).first()
            if user:
                self.circle.members.add(user)
            else:
                print('user is undefined')

        # select multiple members
        members = self.request_data.get('members')
        if members:
            users = User.objects.filter(id__in=members)
            self.circle.members.set(users)

        # shared contacts logic
        contacts = self.request_data.get('contacts')
        if 'contacts' in self.request_data and contacts:
            print(contacts)
            if isinstance(contacts, list):
                contacts = ','.join(contacts)
            self.circle.subscribes = contacts

        self.circle.save()