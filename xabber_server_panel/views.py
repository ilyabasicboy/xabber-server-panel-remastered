from django.shortcuts import reverse, loader
from django.db.models import Q
from django.http import HttpResponseRedirect, JsonResponse
from django.views.generic import TemplateView
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
                module = f'modules.{rp.module}'

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

        object = request.GET.get('object')
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
                group_list = [group for group in groups if text in group.get('name', '') or text in group.get('owner', '')]
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
