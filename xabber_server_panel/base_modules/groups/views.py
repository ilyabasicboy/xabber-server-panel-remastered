from django.views.generic import TemplateView
from django.shortcuts import loader, reverse
from django.http import JsonResponse, HttpResponseRedirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages

from xabber_server_panel.base_modules.users.decorators import permission_read, permission_write
from xabber_server_panel.api.utils import get_api
from xabber_server_panel.utils import host_is_valid


class GroupList(LoginRequiredMixin, TemplateView):

    template_name = 'groups/list.html'
    app = 'groups'

    @permission_read
    def get(self, request, *args, **kwargs):
        hosts = request.user.get_allowed_hosts()
        api = get_api(request)

        if hosts.exists():
            host = request.GET.get('host', request.session.get('host'))

            if not hosts.filter(name=host):
                host = hosts.first().name

            # write current host on session
            request.session['host'] = host
        else:
            host = ''

        chats = api.get_groups(
            {
                "host": host
            }
        ).get('groups')

        context = {
            'groups': chats,
            'hosts': hosts,
            'curr_host': host
        }

        if request.is_ajax():
            html = loader.render_to_string('groups/parts/groups_list.html', context, request)
            response_data = {
                'html': html,
                'items_count': len(chats),
            }
            return JsonResponse(response_data)
        return self.render_to_response(context)


class GroupCreate(LoginRequiredMixin, TemplateView):

    template_name = 'groups/create.html'
    app = 'groups'

    @permission_write
    def get(self, request, *args, **kwargs):
        hosts = request.user.get_allowed_hosts()

        context = {
            'hosts': hosts,
            'current_host': request.session.get('host')
        }
        return self.render_to_response(context)

    @permission_write
    def post(self, request, *args, **kwargs):
        api = get_api(request)
        localpart = request.POST.get('localpart')
        name = request.POST.get('name')
        host = request.POST.get('host')
        privacy = request.POST.get('privacy', 'public')
        index = request.POST.get('index', 'none')
        membership = request.POST.get('membership', 'open')

        response = api.create_group({
            "localpart": localpart,
            "host": host,
            "owner": f"{localpart}@{host}",
            "name": name,
            "privacy": privacy,
            "index": index,
            "membership": membership
        })

        # Check api errors
        if not response.get('errors'):
            messages.success(request, 'Group created successfully')

        return HttpResponseRedirect(reverse('groups:list'))


class GroupDelete(LoginRequiredMixin, TemplateView):

    app = 'groups'

    @permission_write
    def get(self, request, owner, *args, **kwargs):
        api = get_api(request)

        try:
            localpart, host = owner.split('@')
        except:
            localpart, host = None, None

        if localpart and host and host_is_valid(host):
            response = api.delete_group(
                {
                    'localpart': localpart,
                    'host': host
                }
            )

            if not response.get('errors'):
                messages.success(request, 'Group deleted successfully')

        return HttpResponseRedirect(reverse('groups:list'))