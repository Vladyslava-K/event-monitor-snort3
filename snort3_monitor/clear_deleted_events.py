"""Script for clearing events marked as deleted (is_deleted=True)"""

import logging
import os

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "snort3_monitor.settings")
django.setup()

from event.models import Event

cron_logger = logging.getLogger("__name__")
cron_logger.setLevel(logging.INFO)

# f_handler = logging.FileHandler('../log_files/cron.log')
#  relative path does not work because the program runs from the cron location
f_handler = logging.FileHandler('/usr/src/event-monitor-snort3/log_files/cron.log')
f_handler.setLevel(logging.INFO)
f_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
f_handler.setFormatter(f_format)

cron_logger.addHandler(f_handler)


if __name__ == '__main__':
    cron_logger.info('The script has been started')
    try:
        amount_deleted_events = Event.objects.filter(is_deleted=True).delete()
        cron_logger.info(f'Deleted {amount_deleted_events[0]} events')
    except Exception as e:
        cron_logger.error(f'An error occurred during script operation {e}')
