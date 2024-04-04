from django.db import models


class CronJob(models.Model):
    schedule = models.CharField(max_length=100)
    command = models.CharField(max_length=255)

    def __str__(self):
        return self.command

    def get_job(self):
        return (self.schedule, 'django.core.management.call_command', [self.command], '>> /tmp/scheduled_job.log')

