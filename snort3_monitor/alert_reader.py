import json
import logging
import os
import sys
import time
from datetime import datetime

import django
from django.core.exceptions import ValidationError
from django.utils.timezone import make_aware

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "snort3_monitor.settings")
django.setup()

from event.models import Event, Rule


alert_reader_logger = logging.getLogger(__name__)
alert_reader_logger.setLevel(logging.INFO)

f_handler = logging.FileHandler('../log/alert_reader.log')
f_handler.setLevel(logging.INFO)
f_format = logging.Formatter('%(levelname)s - %(asctime)s - %(message)s')
f_handler.setFormatter(f_format)
alert_reader_logger.addHandler(f_handler)


class Handler(FileSystemEventHandler):
    """
    Event handler to track the update of the alert_json.txt file and write new Snort events to the database

    Attributes:
    - lines_count (int): indicates the last saved line
    - lines_count_file_path (str): path to txt-file for saving lines_count in case of program restart
    """
    def __init__(self):
        self.lines_count = 0
        self.lines_count_file_path = '../snort_logs/lines_count.txt'
        self.upload_lines_count(self.lines_count_file_path)

    def on_created(self, event):
        if event.src_path.endswith('alert_json.txt'):
            alert_reader_logger.info('alert_json.txt was created')
            self.process_alerts(event.src_path)

    def on_modified(self, event):
        if event.src_path.endswith('alert_json.txt'):
            alert_reader_logger.info('alert_json.txt was modified')
            self.process_alerts(event.src_path)

    def upload_lines_count(self, file_path):
        """Read last saved lines_count from file"""
        if os.path.exists(file_path):
            with open(file_path, 'r') as file:
                self.lines_count = int(file.readline())
                alert_reader_logger.info(f'Lines count file was read. Current position - line {self.lines_count}')

    def process_alerts(self, file_path):
        """Reads alert data from lines_count to end, updates lines_count, saves alert data to DB"""
        with open(file_path, 'r') as input_file:
            all_lines = input_file.readlines()

        new_content = all_lines[self.lines_count:]
        self.lines_count = len(all_lines)

        for line in new_content:
            try:
                alert_data = json.loads(line)

                rules_by_sid = Rule.objects.filter(sid=alert_data["sid"]).order_by('-rev')  # get all rules with sid
                rule = rules_by_sid[0]  # get rule with the biggest rev
                timestamp = make_aware(datetime.strptime(alert_data['timestamp'], '%y/%m/%d-%H:%M:%S.%f'))

                Event.objects.create(rule_id=rule, timestamp=timestamp, src_addr=alert_data['src_addr'],
                                     src_port=alert_data.get('src_port'), dst_addr=alert_data['dst_addr'],
                                     dst_port=alert_data.get('dst_port'), proto=alert_data['proto'])

            except (json.JSONDecodeError, ValueError, ValidationError) as e:
                alert_reader_logger.error(f"Error processing alert: {line}")
                alert_reader_logger.error(f"Error details: {e}")
        alert_reader_logger.info('DB updated')


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else '../snort_logs/'
    event_handler = Handler()
    observer = Observer()
    observer.schedule(event_handler, path, recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        alert_reader_logger.info('KeyboardInterrupt')
        observer.stop()
    finally:
        lines_count = event_handler.lines_count
        with open('../snort_logs/lines_count.txt', 'w') as file:
            file.write(str(lines_count))
    observer.join()
