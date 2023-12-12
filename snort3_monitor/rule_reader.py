import json
import os
import sys

import django

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "snort3_monitor.settings")
django.setup()

from event.models import Rule


log_file_path = '../rules/integrity_errors.json'

error_data = []


class Handler(FileSystemEventHandler):
    """Custom event handler for file system events."""

    def __init__(self, observer):
        """
        Initialize the Handler.

        Args:
            observer (Observer): The watchdog observer instance.
        """
        super(Handler, self).__init__()
        self.observer = observer
        self.file_processed = False

    def on_modified(self, event):
        """
        Handle the on_updated event.

        Args:
            event (FileSystemEvent): The file system event object.
        """
        if event.src_path.endswith('snort_rules.json') and not self.file_processed:
            self.process_rules(event.src_path)
            self.file_processed = True
            self.observer.stop()
            os.remove(event.src_path)

    @staticmethod
    def process_rules(file_path):
        """
        Process rules from a JSON file and store them in the database.

        Args:
            file_path (str): The path to the JSON file.
        """
        with open(file_path, 'r', encoding='utf-8', errors='replace') as input_file:
            all_lines = input_file.readlines()

            for line in all_lines:
                rule_data = json.loads(line)
                gid = rule_data["gid"]
                sid = rule_data["sid"]
                rev = rule_data["rev"]
                action = rule_data["action"]
                msg = rule_data["msg"]
                jsn = line

                try:
                    Rule.objects.create(gid=gid, sid=sid, rev=rev, action=action, msg=msg, json=jsn)
                except Exception:
                    error_data.append(line)

        with open(log_file_path, 'w', encoding='utf-8') as error_file:
            for index, item in enumerate(error_data):
                if index > 0:
                    error_file.write(',\n')
                json.dump(item, error_file)


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else '../rules/'
    observer = Observer()
    event_handler = Handler(observer)
    observer.schedule(event_handler, path, recursive=False)
    observer.start()
    try:
        while observer.is_alive():
            observer.join(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
