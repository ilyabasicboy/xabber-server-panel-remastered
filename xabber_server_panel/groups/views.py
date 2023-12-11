from django.shortcuts import render
from django.views.generic import TemplateView
from django.conf import settings

from xabber_server_panel.dashboard.models import VirtualHost


class GroupList(TemplateView):

    template_name = 'groups/list.html'

    def get(self, request, *args, **kwargs):
        hosts = VirtualHost.objects.all()

        if hosts.exists():
            host = request.GET.get('host', hosts.first().name)
        else:
            host = ''

        chats = request.user.api.xabber_registered_chats(
            {
                "host": host
            }
        ).get('groups')
        context = {
            'groups': chats,
            'hosts': hosts
        }

        if request.is_ajax():
            return render(request, 'groups/parts/groups_list.html', context)
        return self.render_to_response(context)