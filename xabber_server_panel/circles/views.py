from django.shortcuts import render, reverse, loader
from django.views.generic import TemplateView
from django.http import HttpResponseNotFound, HttpResponseRedirect, JsonResponse
from django.core.exceptions import ObjectDoesNotExist

from xabber_server_panel.circles.models import Circle
from xabber_server_panel.dashboard.models import VirtualHost
from xabber_server_panel.users.models import User

from .forms import CircleForm


class CircleList(TemplateView):
    template_name = 'circles/list.html'

    def get(self, request, *args, **kwargs):

        hosts = VirtualHost.objects.all()
        self.circles = Circle.objects.all()
        context = {}

        if hosts.exists():
            host = request.GET.get('host', request.session.get('host', hosts.first().name))
            request.session['host'] = host
            context['curr_host'] = host

            # check circles from server
            self.check_circles(host)
            self.circles = self.circles.filter(host=host)

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

    def check_circles(self, host):
        """
            Check registered circles and create
            if it doesn't exist in django db
        """
        try:
            registered_circles = self.request.user.api.get_groups({"host": host}).get('circles')
        except:
            registered_circles = []

        if registered_circles:
            # Get a list of existing circles from the Circle model
            existing_circles = self.circles.values_list('circle', flat=True)

            # Filter the circle list to exclude existing circles
            unknown_circles = [circle for circle in registered_circles if circle not in existing_circles]

            if unknown_circles:
                circles_to_create = [
                    Circle(
                        circle=circle,
                        host=host,
                    )
                    for circle in unknown_circles
                ]
                Circle.objects.bulk_create(circles_to_create)

            # get unregistered circles in db and delete
            circles_to_delete = Circle.objects.filter(host=host).exclude(circle__in=registered_circles)
            if circles_to_delete:
                circles_to_delete.delete()

            self.circles = Circle.objects.all()


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

        delete = kwargs.get('delete')
        if delete:
            circle.delete()
            self.request.user.api.delete_group(
                {
                    'circle': circle.circle,
                    'host': circle.host
                }
            )
            return HttpResponseRedirect(reverse('circles:list'))

        context = {
            'circle': circle,
        }

        return self.render_to_response(context)

    def post(self, request, id, *args, **kwargs):

        try:
            self.circle = Circle.objects.get(id=id)
        except ObjectDoesNotExist:
            return HttpResponseNotFound

        self.update_circle()

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


class CircleMembers(TemplateView):
    template_name = 'circles/members.html'

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
            print('jid is incorrect')

        user = User.objects.filter(username=username, host=host).first()
        if user:
            self.circle.members.add(user)
        else:
            print('user is undefined')

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


class CircleShared(TemplateView):

    template_name = 'circles/shared.html'

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

    def post(self, request, id, *args, **kwargs):

        try:
            self.circle = Circle.objects.get(id=id)
        except ObjectDoesNotExist:
            return HttpResponseNotFound

        circles = Circle.objects.filter(host=self.circle.host)

        self.update_circle()

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

        print({
                'group': self.circle.circle,
                'host': self.circle.host,
                'name': self.circle.name,
                'description': self.circle.description,
                'displayed_groups': contacts
            })
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