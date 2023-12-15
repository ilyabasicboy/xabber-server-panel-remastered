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

        users = User.objects.filter(status='ACTIVE')

        self.update_circle()

        context = {
            'circle': self.circle,
            'users': users,
        }

        return self.render_to_response(context)

    def update_circle(self):

        # add member by jid
        add_member = self.request.POST.get('add_member')
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
        members = self.request.POST.getlist('members')
        if members:
            users = User.objects.filter(id__in=members)
            self.circle.members.set(users)

        # send data to server if members was changed
        if add_member or members:
            self.request.user.api.srg_user_add_api(
                {
                    'circle': self.circle.circle,
                    'host': self.circle.host,
                    'members': self.circle.get_members_list
                }
            )

        self.circle.save()


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
        if 'contacts' in self.request.POST and contacts:
            if isinstance(contacts, list):
                contacts = ','.join(contacts)
            self.circle.subscribes = contacts

        self.circle.save()