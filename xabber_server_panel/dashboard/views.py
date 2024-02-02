from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import logout
from django.shortcuts import HttpResponseRedirect, reverse

from xabber_server_panel.utils import is_ejabberd_started, start_ejabberd, restart_ejabberd, stop_ejabberd
from xabber_server_panel.users.decorators import permission_read, permission_write
from xabber_server_panel.config.utils import check_hosts


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard/dashboard.html'
    app = 'dashboard'

    @permission_read
    def get(self, request, *args, **kwargs):
        check_hosts(request.user)

        context = {
            'data': self.get_users_data(),
            'started': is_ejabberd_started()
        }
        return self.render_to_response(context)

    @permission_write
    def post(self, request, *args, **kwargs):
        check_hosts(request.user)

        if request.user.is_admin:
            start = request.POST.get('start')
            restart = request.POST.get('restart')
            stop = request.POST.get('stop')

            if start:
                start_ejabberd()
                logout(request)
                next = reverse('dashboard')
                return HttpResponseRedirect(
                    reverse(
                        'custom_auth:login'
                    ) + f'?next={next}'
                )
            elif restart:
                restart_ejabberd()
            elif stop:
                stop_ejabberd()

        context = {
            'data': self.get_users_data(),
            'started': is_ejabberd_started()
        }
        return self.render_to_response(context)

    def get_users_data(self):
        hosts = self.request.user.get_allowed_hosts()

        data = {
            'hosts': [
                {
                    'host': host.name,
                    'total': self.request.user.api.get_users_count({"host": host.name}).get('count'),
                    'online': self.request.user.api.stats_host({"host": host.name}).get('count')
                }
                 for host in hosts
            ],
        }

        total_count = 0
        online_count = 0

        for entry in data['hosts']:
            total_count += entry.get('total', 0) or 0
            online_count += entry.get('online', 0) or 0

        data['total'] = total_count
        data['online'] = online_count

        return data