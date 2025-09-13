"""
Celery configuration for IABANK project.
"""

import os

from celery import Celery

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("iabank")

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object("django.conf:settings", namespace="CELERY")

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

# Configure periodic tasks
app.conf.beat_schedule = {
    "update-iof-rates": {
        "task": "iabank.operations.tasks.update_iof_rates",
        "schedule": 86400.0,  # Daily
    },
    "calculate-overdue-interest": {
        "task": "iabank.operations.tasks.calculate_overdue_interest",
        "schedule": 3600.0,  # Hourly
    },
    "generate-daily-reports": {
        "task": "iabank.finance.tasks.generate_daily_reports",
        "schedule": 86400.0,  # Daily
    },
}
app.conf.timezone = "America/Sao_Paulo"


@app.task(bind=True)
def debug_task(self):
    print(f"Request: {self.request!r}")
