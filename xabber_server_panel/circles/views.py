from django.shortcuts import reverse, loader
from django.views.generic import TemplateView
from django.http import HttpResponseNotFound, HttpResponseRedirect, JsonResponse
from django.core.exceptions import ObjectDoesNotExist
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin

from xabber_server_panel.circles.models import Circle
from xabber_server_panel.dashboard.models import VirtualHost
from xabber_server_panel.users.models import User
from xabber_server_panel.users.decorators import permission_read, permission_write

from .forms import CircleForm
from .utils import check_circles


class CircleList(LoginRequiredMixin, TemplateView):
    template_name = 'circles/list.html'
    app = 'circles'

    @permission_read
    def get(self, request, *args, **kwargs):

        hosts = request.user.get_allowed_hosts()
        self.circles = Circle.objects.none()
        context = {}

        if hosts.exists():
            host = request.GET.get('host', request.session.get('host'))

            if not hosts.filter(name=host):
                host = hosts.first().name

            # write current host on session
            request.session['host'] = host

            context['curr_host'] = host

            # check circles from server
            check_circles(request.user, host)

            self.circles = Circle.objects.filter(host=host)

            context['hosts'] = hosts
            context['circles'] = self.circles.order_by('circle')

        if request.is_ajax():
            html = loader.render_to_string('circles/parts/circle_list.html', context, request)
            response_data = {
                'html': html,
                'items_count': self.circles.count(),
            }
            return JsonResponse(response_data)
        return self.render_to_response(context)


class CircleCreate(LoginRequiredMixin, TemplateView):
    template_name = 'circles/create.html'
    app = 'circles'

    @permission_write
    def get(self, request, *args, **kwargs):

        form = CircleForm()
        context = {
            'form': form,
            'hosts': VirtualHost.objects.all(),
        }
        return self.render_to_response(context)

    @permission_write
    def post(self, request, *args, **kwargs):

        form = CircleForm(request.POST)

        if form.is_valid():
            circle = form.save()
            self.request.user.api.create_group(
                {
                    'group': form.cleaned_data.get('circle'),
                    'host': form.cleaned_data.get('host'),
                    'name': form.cleaned_data.get('name'),
                    'description': form.cleaned_data.get('description'),
                    'displayed_groups': None
                }
            )
            messages.success(request, 'Circle created successfully.')
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


class CircleDetail(LoginRequiredMixin, TemplateView):

    template_name = 'circles/detail.html'
    app = 'circles'

    @permission_read
    def get(self, request, id, *args, **kwargs):

        try:
            circle = Circle.objects.get(id=id)
        except ObjectDoesNotExist:
            return HttpResponseNotFound

        context = {
            'circle': circle,
        }

        return self.render_to_response(context)

    @permission_write
    def post(self, request, id, *args, **kwargs):

        try:
            self.circle = Circle.objects.get(id=id)
        except ObjectDoesNotExist:
            return HttpResponseNotFound

        self.update_circle()

        messages.success(request, 'Circle changed successfully.')
        context = {
            'circle': self.circle,
        }

        return self.render_to_response(context)

    def update_circle(self):

        name = self.request.POST.get('name')
        self.circle.name = name

        description = self.request.POST.get('description')
        self.circle.description = description
        self.request.user.api.create_group(
            {
                'group': self.circle.circle,
                'host': self.circle.host,
                'name': name,
                'description': description,
                'displayed_groups': self.circle.get_subscribes
            }
        )

        self.circle.save()


class CirclesDelete(LoginRequiredMixin, TemplateView):

    app = 'circles'

    @permission_write
    def get(self, request, id, *args, **kwargs):

        try:
            circle = Circle.objects.get(id=id)
        except ObjectDoesNotExist:
            return HttpResponseNotFound

        circle.delete()
        self.request.user.api.delete_group(
            {
                'circle': circle.circle,
                'host': circle.host
            }
        )
        return HttpResponseRedirect(reverse('circles:list'))


class CircleMembers(LoginRequiredMixin, TemplateView):
    template_name = 'circles/members.html'
    app = 'circles'

    @permission_read
    def get(self, request, id, *args, **kwargs):

        try:
            circle = Circle.objects.get(id=id)
        except ObjectDoesNotExist:
            return HttpResponseNotFound

        users = User.objects.filter(status='ACTIVE')

        context = {
            'circle': circle,
            'users': users,
        }

        return self.render_to_response(context)

    @permission_write
    def post(self, request, id, *args, **kwargs):

        try:
            self.circle = Circle.objects.get(id=id)
        except ObjectDoesNotExist:
            return HttpResponseNotFound

        self.users = User.objects.filter(status='ACTIVE')

        self.update_circle()

        context = {
            'circle': self.circle,
            'users': self.users,
        }

        return self.render_to_response(context)

    def update_circle(self):

        # add member by jid
        self.add_member = self.request.POST.get('add_member')
        self.members = self.request.POST.getlist('members')

        if self.add_member:
            self.add_member_api()
        # select multiple members
        else:
            self.members_api()

        # send data to server if members was changed
        self.circle.save()

    def add_member_api(self):
        try:
            username, host = self.add_member.split('@')
        except:
            messages.error(self.request, 'Jid is incorrect.')
            return

        user = User.objects.filter(username=username, host=host).first()
        if user:
            self.circle.members.add(user)
            messages.success(self.request, 'Member added successfully.')
        else:
            messages.error(self.request, 'User is undefined.')
            return

        self.request.user.api.srg_user_add_api(
            {
                'circle': self.circle.circle,
                'host': self.circle.host,
                'members': [self.add_member]
            }
        )

    def members_api(self):
        members = User.objects.filter(id__in=self.members)

        new_members = set(map(int, self.members))
        existing_members = set(self.circle.members.values_list('id', flat=True))

        # Added circles id list
        ids_to_add = new_members - existing_members

        # Removed circles id list
        ids_to_delete = existing_members - new_members

        # add circles
        members_to_add = self.users.filter(id__in=ids_to_add)
        for member in members_to_add:
            self.request.user.api.srg_user_add_api(
                {
                    'circle': self.circle.circle,
                    'host': self.circle.host,
                    'members': [member.full_jid]
                }
            )

        # delete circles
        members_to_delete = self.users.filter(id__in=ids_to_delete)
        for member in members_to_delete:
            self.request.user.api.srg_user_del_api(
                {
                    'circle': self.circle.circle,
                    'host': self.circle.host,
                    'members': [member.full_jid]
                }
            )

        self.circle.members.set(members)
        messages.success(self.request, 'Members changed successfully.')


class DeleteMember(LoginRequiredMixin, TemplateView):
    app = 'circles'

    @permission_write
    def get(self, request, circle_id, member_id, *args, **kwargs):

        try:
            circle = Circle.objects.get(id=circle_id)
        except ObjectDoesNotExist:
            return HttpResponseNotFound

        members = circle.members.exclude(id=member_id)
        circle.members.set(members)
        self.request.user.api.delete_group(
            {
                'circle': circle.circle,
                'host': circle.host
            }
        )
        messages.success(self.request, 'Member deleted successfully.')
        return HttpResponseRedirect(reverse('circles:members', kwargs={'id': circle.id}))


class CircleShared(LoginRequiredMixin, TemplateView):

    template_name = 'circles/shared.html'
    app = 'circles'

    @permission_read
    def get(self, request, id, *args, **kwargs):

        try:
            circle = Circle.objects.get(id=id)
        except ObjectDoesNotExist:
            return HttpResponseNotFound

        circles = Circle.objects.filter(host=circle.host)

        context = {
            'circle': circle,
            'circles': circles
        }

        return self.render_to_response(context)

    @permission_write
    def post(self, request, id, *args, **kwargs):

        try:
            self.circle = Circle.objects.get(id=id)
        except ObjectDoesNotExist:
            return HttpResponseNotFound

        circles = Circle.objects.filter(host=self.circle.host)

        self.update_circle()

        messages.success(self.request, 'Shared contacts changed successfully.')

        context = {
            'circle': self.circle,
            'circles': circles
        }

        return self.render_to_response(context)

    def update_circle(self):

        # shared contacts logic
        contacts = self.request.POST.getlist('contacts')
        if isinstance(contacts, list):
            str_contacts = ','.join(contacts)
        self.request.user.api.create_group(
            {
                'group': self.circle.circle,
                'host': self.circle.host,
                'name': self.circle.name,
                'description': self.circle.description,
                'displayed_groups': contacts
            }
        )
        self.circle.subscribes = str_contacts

        self.circle.save()