from django_crontab.crontab import Crontab

from .models import CronJob

import sys

string_type = basestring if sys.version_info[0] == 2 else str  # flake8: noqa


class CustomCrontab(Crontab):

    """
        Customized for add crontab jobs from db
    """

    def add_jobs(self):
        """
        Adds all jobs defined in CRONJOBS setting to internal buffer
        """
        for job_object in CronJob.objects.all():
            job = job_object.get_job()
            # differ format and find job's suffix
            if len(job) > 2 and isinstance(job[2], string_type):
                # format 1 job
                job_suffix = job[2]
            elif len(job) > 4:
                job_suffix = job[4]
            else:
                job_suffix = ''

            self.crontab_lines.append(self.settings.CRONTAB_LINE_PATTERN % {
                'time': job[0],
                'comment': self.settings.CRONTAB_COMMENT,
                'command': ' '.join(filter(None, [
                    self.settings.COMMAND_PREFIX,
                    self.settings.PYTHON_EXECUTABLE,
                    self.settings.DJANGO_MANAGE_PATH,
                    'crontab', 'run',
                    self.__hash_job(job),
                    '--settings=%s' % self.settings.DJANGO_SETTINGS_MODULE if self.settings.DJANGO_SETTINGS_MODULE else '',
                    job_suffix,
                    self.settings.COMMAND_SUFFIX
                ]))
            })
            if self.verbosity >= 1:
                print('  adding cronjob: (%s) -> %s' % (self.__hash_job(job), job))