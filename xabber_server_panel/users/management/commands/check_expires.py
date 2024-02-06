from django.core.management.base import BaseCommand
from django.utils import timezone
from xabber_server_panel.users.models import User


class Command(BaseCommand):
    help = 'Check and update user status based on expiration'

    def handle(self, *args, **options):
        # Get the current date and time
        current_time = timezone.now()

        # Filter users whose expires field is less than the current time
        expired_users = User.objects.filter(expires__lt=current_time)

        # Update the status of expired users to 'EXPIRED'
        expired_users.update(status='EXPIRED')
