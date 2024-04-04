from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.conf import settings

from .models import CronJob
from .utils import CustomCrontab


@receiver(post_save, sender=CronJob)
def add_cron_job(sender, instance, created, **kwargs):
    crontab = CustomCrontab()
    crontab.remove_jobs()
    crontab.add_jobs()


@receiver(post_delete, sender=CronJob)
def add_cron_job(sender, instance, created, **kwargs):
    crontab = CustomCrontab()
    crontab.remove_jobs()
    crontab.add_jobs()

