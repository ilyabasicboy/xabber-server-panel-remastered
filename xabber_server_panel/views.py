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
from xabber_server_panel.utils import get_modules


class Root(TemplateView):

    def get(self, request, *args, **kwargs):

        # redirect to module root
        rp = RootPage.objects.first()
        modules = get_modules()
        if rp and rp.module:
            if rp.module != 'home' and rp.module in modules:
                return HttpResponseRedirect(
                    reverse(f'{rp.module}:root')
                )

        return HttpResponseRedirect(
            reverse('home')
        )


class HomePage(LoginRequiredMixin, TemplateView):

    template_name = 'home.html'

    def get(self, request, *args, **kwargs):
        context = {}
        return self.render_to_response(context, **kwargs)


class Search(LoginRequiredMixin, TemplateView):

    template_name = 'search.html'

    def get(self, request, *args, **kwargs):
        text = request.GET.get('text', '')
        object = request.GET.get('object')

        hosts = request.user.get_allowed_hosts()

        context = {
            'hosts': hosts
        }

        if hosts:
            # get host name
            host = request.GET.get('host', request.session.get('host'))
            if not host:
                host = hosts.first().name

            # set current host in session
            request.session['host'] = host
            context['curr_host'] = host

            # check circles from server
            check_circles(request.user, host)

            circles = Circle.objects.filter(
                Q(circle__contains=text, host=host)
                | Q(name__contains=text, host=host)
            ).order_by('circle')
            context['circles'] = circles

            # check users from server
            check_users(request.user.api, host)

            users = User.objects.filter(
                Q(username__contains=text, host=host)
                | Q(first_name__contains=text, host=host)
                | Q(last_name__contains=text, host=host)
            ).order_by('username')
            context['users'] = users

            # get group list
            groups = request.user.api.get_groups(
                {
                    "host": host
                }
            ).get('groups')

            # filter groups by text
            groups = [group for group in groups if text in group.get('name', '') or text in group.get('owner', '')]
            context['groups'] = groups

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
