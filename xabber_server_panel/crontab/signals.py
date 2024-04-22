from django.db.models.signals import post_save, pre_delete, post_delete, pre_save
from django.dispatch import receiver

from .models import CronJob
from .crontab import Crontab


@receiver(pre_save, sender=CronJob)
def pre_save_cron_job(sender, *args, **kwargs):
    with Crontab() as crontab:
        try:
            crontab.remove_jobs()
        except:
            pass


@receiver(post_save, sender=CronJob)
def post_save_cron_job(sender, instance, created, **kwargs):
    with Crontab() as crontab:
        crontab.add_jobs()


@receiver(pre_delete, sender=CronJob)
def pre_delete_cron_job(sender, *args, **kwargs):
    with Crontab() as crontab:
        try:
            crontab.remove_jobs()
        except:
            pass


@receiver(post_delete, sender=CronJob)
def post_delete_cron_job(sender, *args, **kwargs):
    with Crontab() as crontab:
        crontab.add_jobs()

