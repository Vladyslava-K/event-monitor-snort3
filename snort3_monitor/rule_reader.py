import json
import os
import sys

import django
from django.db.utils import IntegrityError

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "snort3_monitor.settings")
django.setup()

from event.models import Rule


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

    def on_created(self, event):
        """
        Handle the on_created event.

        Args:
            event (FileSystemEvent): The file system event object.
        """
        if event.src_path.endswith('snort_rules.json') and not self.file_processed:
            self.process_rules(event.src_path)
            self.file_processed = True
            self.observer.stop()

    @staticmethod
    def process_rules(file_path):
        """
        Process rules from a JSON file and store them in the database.

        Args:
            file_path (str): The path to the JSON file.
        """
        with open(file_path, 'r') as input_file:
            all_lines = input_file.readlines()

            for line in all_lines:
                rule_data = json.loads(line)
                sid = rule_data["sid"]
                rev = rule_data["rev"]
                action = rule_data["action"]
                msg = rule_data["msg"]
                jsn = line

                try:
                    Rule.objects.create(sid=sid, rev=rev, action=action, msg=msg, json=jsn)
                except IntegrityError:
                    pass


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
