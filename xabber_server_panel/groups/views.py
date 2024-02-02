from django.views.generic import TemplateView
from django.shortcuts import loader
from django.http import JsonResponse
from django.contrib.auth.mixins import LoginRequiredMixin

from xabber_server_panel.users.decorators import permission_read


class GroupList(LoginRequiredMixin, TemplateView):

    template_name = 'groups/list.html'
    app = 'groups'

    @permission_read
    def get(self, request, *args, **kwargs):
        hosts = request.user.get_allowed_hosts()

        if hosts.exists():
            host = request.GET.get('host', request.session.get('host'))

            if not hosts.filter(name=host):
                host = hosts.first().name

            # write current host on session
            request.session['host'] = host
        else:
            host = ''

        chats = request.user.api.get_groups(
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