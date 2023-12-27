from django.views.generic import TemplateView
from django.shortcuts import loader
from django.http import JsonResponse

from xabber_server_panel.dashboard.models import VirtualHost


class GroupList(TemplateView):

    template_name = 'groups/list.html'

    def get(self, request, *args, **kwargs):
        hosts = VirtualHost.objects.all()

        if hosts.exists():
            host = request.GET.get('host', request.session.get('host', hosts.first().name))

            # write current host on session
            request.session['host'] = host
        else:
            host = ''

        chats = request.user.api.xabber_registered_chats(
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