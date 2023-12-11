from django.views.generic import TemplateView

from xabber_server_panel.users.models import User
from xabber_server_panel.utils import is_ejabberd_started, start_ejabberd, restart_ejabberd, stop_ejabberd

from .models import VirtualHost


class DashboardView(TemplateView):
    page_section = 'dashboard'
    template_name = 'dashboard/dashboard.html'

    def get_users_data(self):
        hosts = VirtualHost.objects.all()

        data = {
            'hosts': {
                host.name: User.objects.filter(host=host.name).count() for host in hosts
            },
            'users': User.objects.all().count()
        }
        return data

    def get(self, request, *args, **kwargs):

        context = {
            'data': self.get_users_data(),
            'started': is_ejabberd_started()
        }
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):

        if request.user.django_user.is_admin:
            start = request.POST.get('start')
            restart = request.POST.get('restart')
            stop = request.POST.get('stop')

            if start:
                start_ejabberd()
            elif restart:
                restart_ejabberd()
            elif stop:
                stop_ejabberd()

        context = {
            'data': self.get_users_data(),
            'started': is_ejabberd_started()
        }
        return self.render_to_response(context)