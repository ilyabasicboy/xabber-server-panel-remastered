from django.shortcuts import reverse, loader
from django.views.generic import TemplateView
from django.http import HttpResponseNotFound, HttpResponseRedirect, JsonResponse
from django.core.exceptions import ObjectDoesNotExist
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin

from xabber_server_panel.base_modules.circles.models import Circle
from xabber_server_panel.base_modules.users.models import User
from xabber_server_panel.base_modules.users.utils import check_users
from xabber_server_panel.base_modules.users.decorators import permission_read, permission_write
from xabber_server_panel.api.utils import get_api
from xabber_server_panel.utils import get_error_messages

from .forms import CircleForm
from .utils import check_circles


class CircleList(LoginRequiredMixin, TemplateView):
    template_name = 'circles/list.html'

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
            check_circles(
                get_api(request),
                host
            )

            self.circles = Circle.objects.filter(host=host).exclude(circle=host)

            context['hosts'] = hosts
            context['circles'] = self.circles.order_by('id')

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

    @permission_write
    def get(self, request, *args, **kwargs):

        form = CircleForm()
        context = {
            'form': form,
            'hosts': request.user.get_allowed_hosts(),
            'current_host': request.session.get('host'),
        }
        return self.render_to_response(context)

    @permission_write
    def post(self, request, *args, **kwargs):

        form = CircleForm(request.POST)
        api = get_api(request)

        if form.is_valid():

            circle = form.save()
            autoshare = form.cleaned_data.get('autoshare')
            name = form.cleaned_data.get('name')
            # use circle if name is not provided
            if not name:
                name = form.cleaned_data.get('circle')

            api.create_circle(
                {
                    'circle': form.cleaned_data.get('circle'),
                    'host': form.cleaned_data.get('host'),
                    'name': name,
                    'displayed_groups': [circle.circle] if autoshare else [],
                    'description': form.cleaned_data.get('description'),
                }
            )

            if circle.all_users:
                api.add_circle_members(
                    {
                        'circle': circle.circle,
                        'host': circle.host,
                        'grouphost': circle.host,
                        'members': ['@all@']
                    }
                )

            # check server errors
            error_messages = get_error_messages(request)
            if not error_messages:
                messages.success(request, 'Circle created successfully.')
                return HttpResponseRedirect(
                    reverse(
                        'circles:detail',
                        kwargs={'id': circle.id}
                    )
                )

        context = {
            'form': form,
            'hosts': request.user.get_allowed_hosts(),
        }
        return self.render_to_response(context)


class CircleDetail(LoginRequiredMixin, TemplateView):

    template_name = 'circles/detail.html'

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

        # check server errors
        error_messages = get_error_messages(request)
        if not error_messages:
            messages.success(request, 'Circle changed successfully.')

        context = {
            'circle': self.circle,
        }

        return self.render_to_response(context)

    def update_circle(self):
        api = get_api(self.request)

        # set name
        name = self.request.POST.get('name')
        self.circle.name = name

        # set description
        description = self.request.POST.get('description')
        self.circle.description = description

        # set all users
        all_users = self.request.POST.get('all_users')
        if not self.circle.all_users and all_users:
            api.add_circle_members(
                {
                    'circle': self.circle.circle,
                    'host': self.circle.host,
                    'grouphost': self.circle.host,
                    'members': ['@all@']
                }
            )
            self.circle.all_users = True

        elif self.circle.all_users and not all_users:
            api.del_circle_members(
                {
                    'circle': self.circle.circle,
                    'host': self.circle.host,
                    'grouphost': self.circle.host,
                    'members': ['@all@']
                }
            )
            self.circle.all_users = False

        # send data to server
        api.create_circle(
            {
                'circle': self.circle.circle,
                'host': self.circle.host,
                'name': name,
                'description': description,
                'displayed_groups': self.circle.get_subscribes,
                'all_users': self.circle.all_users
            }
        )

        self.circle.save()


class CirclesDelete(LoginRequiredMixin, TemplateView):

    @permission_write
    def get(self, request, id, *args, **kwargs):

        try:
            circle = Circle.objects.get(id=id)
        except ObjectDoesNotExist:
            return HttpResponseNotFound

        api = get_api(request)

        circle.delete()
        api.delete_circle(
            {
                'circle': circle.circle,
                'host': circle.host
            }
        )
        return HttpResponseRedirect(reverse('circles:list'))


class CircleMembers(LoginRequiredMixin, TemplateView):
    template_name = 'circles/members.html'

    @permission_read
    def get(self, request, id, *args, **kwargs):

        try:
            self.circle = Circle.objects.get(id=id)
        except ObjectDoesNotExist:
            return HttpResponseNotFound

        self.api = get_api(request)

        check_users(self.api, self.circle.host)
        self.check_members()

        users = User.objects.filter(status='ACTIVE', host=self.circle.host)

        context = {
            'circle': self.circle,
            'users': users,
        }

        return self.render_to_response(context)

    @permission_write
    def post(self, request, id, *args, **kwargs):

        try:
            self.circle = Circle.objects.get(id=id)
        except ObjectDoesNotExist:
            return HttpResponseNotFound

        self.api = get_api(request)

        self.check_members()

        self.users = User.objects.filter(status='ACTIVE', host=self.circle.host)

        self.members_api()

        context = {
            'circle': self.circle,
            'users': self.users,
        }

        return self.render_to_response(context)

    def members_api(self):

        self.members = self.request.POST.getlist('members')

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
            self.api.add_circle_members(
                {
                    'circle': self.circle.circle,
                    'host': self.circle.host,
                    'members': [member.full_jid]
                }
            )

        # delete circles
        members_to_delete = self.users.filter(id__in=ids_to_delete)
        for member in members_to_delete:
            self.api.del_circle_members(
                {
                    'circle': self.circle.circle,
                    'host': self.circle.host,
                    'members': [member.full_jid]
                }
            )

        self.circle.members.set(members)
        self.circle.save()

        # check server errors
        error_messages = get_error_messages(self.request)
        if not error_messages:
            messages.success(self.request, 'Members changed successfully.')

    def check_members(self):

        """ Sync member list from server """

        server_members_list = self.api.get_circle_members(
            {
                'circle': self.circle.circle,
                'host': self.circle.host
            }
        ).get('members', [])

        # get server members list
        server_members = []
        for member_jid in server_members_list:
            username, host = member_jid.split('@')
            member = User.objects.filter(username=username, host=host).first()
            if member:
                server_members += [member.id]
            else:
                self.api.del_circle_members(
                    {
                        'circle': self.circle.circle,
                        'host': self.circle.host,
                        'members': [member_jid]
                    }
                )

        # set members from server
        self.circle.members.set(server_members)


class DeleteMember(LoginRequiredMixin, TemplateView):

    @permission_write
    def get(self, request, circle_id, member_id, *args, **kwargs):

        try:
            circle = Circle.objects.get(id=circle_id)
        except ObjectDoesNotExist:
            return HttpResponseNotFound

        try:
            member = User.objects.get(id=member_id)
        except ObjectDoesNotExist:
            return HttpResponseNotFound

        api = get_api(request)

        members = circle.members.exclude(id=member_id)
        circle.members.set(members)

        response = api.del_circle_members(
            {
                'circle': circle.circle,
                'host': circle.host,
                'members': [member.full_jid]
            }
        )

        if not response.get('errors'):
            messages.success(self.request, 'Member deleted successfully.')
        return HttpResponseRedirect(reverse('circles:members', kwargs={'id': circle.id}))


class CircleShared(LoginRequiredMixin, TemplateView):

    template_name = 'circles/shared.html'

    @permission_read
    def get(self, request, id, *args, **kwargs):

        try:
            circle = Circle.objects.get(id=id)
        except ObjectDoesNotExist:
            return HttpResponseNotFound

        circles = Circle.objects.filter(host=circle.host).exclude(circle=circle.host)

        context = {
            'circle': circle,
            'circles': circles,
        }

        return self.render_to_response(context)

    @permission_write
    def post(self, request, id, *args, **kwargs):

        try:
            self.circle = Circle.objects.get(id=id)
        except ObjectDoesNotExist:
            return HttpResponseNotFound

        circles = Circle.objects.filter(host=self.circle.host).exclude(circle=self.circle.host)
        self.api = get_api(request)

        self.update_circle()

        if not self.response.get('errors'):
            messages.success(self.request, 'Shared contacts changed successfully.')

        context = {
            'circle': self.circle,
            'circles': circles
        }

        return self.render_to_response(context)

    def update_circle(self):

        # shared contacts logic
        contacts = self.request.POST.getlist('contacts', [])
        str_contacts = ','.join(contacts)

        self.response = self.api.create_circle(
            {
                'circle': self.circle.circle,
                'host': self.circle.host,
                'name': self.circle.name,
                'description': self.circle.description,
                'displayed_groups': contacts,
                'all_users': self.circle.all_users
            }
        )
        self.circle.subscribes = str_contacts

        self.circle.save()