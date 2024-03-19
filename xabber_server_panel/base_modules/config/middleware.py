from django.utils.deprecation import MiddlewareMixin

from xabber_server_panel.base_modules.config.models import VirtualHost


class VirtualHostMiddleware(MiddlewareMixin):

    def process_request(self, request):

        if request.user.is_authenticated:
            hosts = VirtualHost.objects.all()

            if hosts:
                # set host list
                if not request.user.is_admin:
                    hosts = hosts.filter(name=request.user.host)

                request.hosts = hosts

                # set current host
                session_host = request.session.get("host")

                try:
                    request.current_host = VirtualHost.objects.filter(id=session_host).first()
                except:
                    request.current_host = hosts.first()