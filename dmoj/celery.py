import logging
import socket

from celery import Celery
from celery.schedules import crontab
from celery.signals import task_failure

app = Celery('dmoj')

from django.conf import settings  # noqa: E402, I202, django must be imported here
app.config_from_object(settings, namespace='CELERY')

if hasattr(settings, 'CELERY_BROKER_URL'):
    app.conf.broker_url = settings.CELERY_BROKER_URL
if hasattr(settings, 'CELERY_RESULT_BACKEND'):
    app.conf.result_backend = settings.CELERY_RESULT_BACKEND

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()

# Logger to enable reporting of errors.
logger = logging.getLogger('judge.celery')

# Load periodic tasks
app.conf.beat_schedule = {
    'daily-queue-time-stats': {
        'task': 'judge.tasks.webhook.queue_time_stats',
        'schedule': crontab(minute=0, hour=0),
        'options': {
            'expires': 60 * 60 * 24,
        },
    },
}


@task_failure.connect()
def celery_failure_log(sender, task_id, exception, traceback, *args, **kwargs):
    logger.error('Celery Task %s: %s on %s', sender.name, task_id, socket.gethostname(),  # noqa: G201
                 exc_info=(type(exception), exception, traceback))
