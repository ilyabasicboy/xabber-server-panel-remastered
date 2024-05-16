from django.shortcuts import reverse, loader
from django.db.models import Q
from django.http import HttpResponseRedirect, JsonResponse
from django.views.generic import TemplateView, View
from django.contrib.auth.mixins import LoginRequiredMixin

from xabber_server_panel.base_modules.config.models import RootPage
from xabber_server_panel.base_modules.users.models import User
from xabber_server_panel.base_modules.circles.models import Circle
from xabber_server_panel.base_modules.circles.utils import check_circles
from xabber_server_panel.base_modules.users.utils import check_users
from xabber_server_panel.base_modules.config.utils import get_modules
from xabber_server_panel.api.utils import get_api
from xabber_server_panel.mixins import ServerStartedMixin

import importlib


class Root(TemplateView):

    def get(self, request, *args, **kwargs):

        # redirect to module root
        rp = RootPage.objects.first()
        modules = get_modules()

        if rp and rp.module:
            if rp.module != 'home' and rp.module in modules:
                module = 'modules.%s' % rp.module

                # return current root module view
                try:
                    module_view = importlib.import_module(module).views.RootView.as_view()
                    return module_view(request)
                except(AttributeError, ModuleNotFoundError):
                    pass

        return HttpResponseRedirect(
            reverse('home')
        )


class HomePage(LoginRequiredMixin, TemplateView):

    template_name = 'home.html'

    def get(self, request, *args, **kwargs):
        context = {}
        return self.render_to_response(context, **kwargs)


class Search(ServerStartedMixin, LoginRequiredMixin, TemplateView):

    template_name = 'search.html'

    def get(self, request, *args, **kwargs):
        try:
            text = request.GET.get('search', '').strip()
        except:
            text = ''

        host = request.current_host
        api = get_api(request)

        context = {}

        if host:
            # check circles from server
            check_circles(api, host.name)

            circles = Circle.objects.filter(
                Q(circle__contains=text, host=host.name)
                | Q(name__contains=text, host=host.name)
            ).exclude(circle=host.name).order_by('circle')
            context['circles'] = circles

            # check users from server
            check_users(api, host.name)

            users = User.objects.filter(
                Q(username__contains=text, host=host.name)
                | Q(first_name__contains=text, host=host.name)
                | Q(last_name__contains=text, host=host.name)
            ).order_by('username')
            context['users'] = users

            # get group list
            groups = api.get_groups(
                {
                    "host": host.name
                }
            ).get('groups')

            if groups:
                group_list = [group for group in groups if text in group.get('name', '')]
                context['groups'] = group_list

        if request.is_ajax():
            if object == 'users':
                template = 'users/parts/user_list.html'
            elif object == 'circles':
                template = 'circles/parts/circle_list.html'
            elif object == 'groups':
                template = 'groups/parts/groups_list.html'
            else:
                template = 'parts/search_list.html'
            html = loader.render_to_string(template, context, request)
            response_data = {
                'html': html,
            }
            return JsonResponse(response_data)

        return self.render_to_response(context, **kwargs)


class Suggestions(ServerStartedMixin, LoginRequiredMixin, TemplateView):

    template_name = 'parts/dropdown_field.html'

    def get(self, request, *args, **kwargs):

        try:
            self.text = request.GET.get('text', '').strip()
        except:
            self.text = ''

        if self.text.count('@') == 1:
            # Split the search string into local part and host
            self.localpart, self.host_part = self.text.split('@')
        else:
            self.localpart = self.host_part = None

        try:
            self.objects = request.GET.get('objects').split(',')
        except:
            self.objects = []

        type = request.GET.get('type')

        if type == 'search':
            self.template_name = 'parts/dropdown_search.html'

        self.hosts = request.hosts.values_list('name', flat=True)

        self.api = get_api(request)

        self.context = {}

        response_data = {}
        if self.hosts and self.text:
            if 'circles' in self.objects:
                self.search_circles()

            if 'users' in self.objects:
                self.search_users()

            if 'groups' in self.objects:
                self.search_groups()

            html = loader.render_to_string(self.template_name, self.context)

            response_data['html'] = html

        return JsonResponse(response_data)

    def search_circles(self):
        # create circles query
        q = Q()
        if self.localpart or self.host_part:
            q |= Q(
                circle__contains=self.localpart,
                host__startswith=self.host_part,
                host__in=self.hosts
            )
        else:
            q |= Q(
                circle__contains=self.text,
                host__in=self.hosts
            )
            q |= Q(
                host__contains=self.text,
                host__in=self.hosts
            )
            q |= Q(
                name__contains=self.text,
                host__in=self.hosts
            )

        circles = Circle.objects.only('id', 'circle', 'host').filter(q).order_by('circle', 'host')
        circles = circles.exclude(circle__in=self.hosts)
        self.context['circles'] = circles[:10]

    def search_users(self):
        q = Q()
        if self.localpart or self.host_part:
            q |= Q(
                username__contains=self.localpart,
                host__startswith=self.host_part,
                host__in=self.hosts
            )
        else:
            q |= Q(username__contains=self.text, host__in=self.hosts)
            q |= Q(host__contains=self.text, host__in=self.hosts)
            q |= Q(first_name__contains=self.text, host__in=self.hosts)
            q |= Q(last_name__contains=self.text, host__in=self.hosts)

        users = User.objects.only('id', 'username', 'host').filter(q).order_by('username', 'host')
        self.context['users'] = users[:10]

    def search_groups(self):
        group_list = []

        for host in self.hosts:
            # get group list
            groups = self.api.get_groups(
                {
                    "host": host
                }
            ).get('groups')

            if groups:
                for group in groups:
                    if self.text in group.get('name', ''):
                        group_list += [group]

                self.context['groups'] = group_list[:10]