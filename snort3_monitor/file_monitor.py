import os
import sys
import time
import json
import django
from django.core.exceptions import ValidationError
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from datetime import datetime


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "snort3_monitor.settings")
django.setup()


from event.models import Event, Rule


class Handler(FileSystemEventHandler):
    def __init__(self):
        self.last_reference_point = None
        self.update_reference_point()

    def update_reference_point(self):
        try:
            latest_timestamp = Event.objects.latest('timestamp').timestamp

            if latest_timestamp:
                self.last_reference_point = latest_timestamp.strftime('%Y-%m-%d %H:%M:%S.%f')

        except Event.DoesNotExist:
            pass

    def on_created(self, event):
        if event.src_path.endswith('alert_json.txt'):
            print('created')
            self.process_alerts(event.src_path)

    def on_modified(self, event):
        if event.src_path.endswith('alert_json.txt'):
            print('modified')
            self.process_alerts(event.src_path)

    def process_alerts(self, file_path):
        with open(file_path, 'r') as input_file:
            all_lines = input_file.readlines()

            reference_point_index = None
            if self.last_reference_point:
                for i, line in enumerate(all_lines):
                    try:
                        alert_data = json.loads(line)
                        timestamp = datetime.strptime(alert_data['timestamp'], '%y/%m/%d-%H:%M:%S.%f')
                        formatted_timestamp = timestamp.strftime('%Y-%m-%d %H:%M:%S.%f')
                        if formatted_timestamp == self.last_reference_point:
                            reference_point_index = i + 1
                            break
                    except (json.JSONDecodeError, KeyError, ValueError, ValidationError):
                        pass

            new_content = all_lines[reference_point_index:] if reference_point_index is not None else all_lines

            for line in new_content:
                try:
                    alert_data = json.loads(line)
                    timestamp = datetime.strptime(alert_data['timestamp'], '%y/%m/%d-%H:%M:%S.%f')
                    alert_data['timestamp'] = timestamp
                    timest = alert_data['timestamp']
                    src_addr = alert_data.get('src_addr', None)
                    src_port = alert_data.get('src_port', None)
                    dst_addr = alert_data.get('dst_addr', None)
                    dst_port = alert_data.get('dst_port', None)
                    proto = alert_data.get('proto', None)
                    rule_id = f'{alert_data["sid"]}/{alert_data["rev"]}'
                    rule_inst = Rule.objects.get(id=rule_id)

                    Event.objects.create(rule_id=rule_inst, timestamp=timest, src_addr=src_addr, src_port=src_port,
                                         dst_addr=dst_addr, dst_port=dst_port, proto=proto)

                except (json.JSONDecodeError, ValueError, ValidationError) as e:
                    print(f"Error processing alert: {line}")
                    print(f"Error details: {e}")

        self.update_reference_point()


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
        observer.stop()
    observer.join()
