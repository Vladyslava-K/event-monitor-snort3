import logging
from datetime import datetime

from db_config import perf_monitor
import json


logging.basicConfig(
    level=logging.ERROR,
    filename='/usr/src/event-monitor-snort3/log_files/perf_monitor_listener.log',
    filemode='a',
    format='{asctime} - {name} - {levelname} - {message}',
    style='{'
)


def read_perf_monitor_logs():
    """
       Read performance monitor logs from a JSON file and insert into the database.
    """
    try:
        with open('/usr/src/event-monitor-snort3/snort_logs/perf_monitor_base.json', 'r') as file:
            json_content = file.read()
            if not json_content.endswith(']'):
                json_content += ']'

            json_data = json.loads(json_content)

            for document in json_data:
                document['timestamp'] = datetime.utcfromtimestamp(document['timestamp'])
                if not perf_monitor.find_one({'timestamp': document.get('timestamp')}):
                    perf_monitor.insert_one(document)

    except FileNotFoundError:
        logging.error("File not found. Please check the file path.")
    except json.JSONDecodeError:
        logging.error("Error decoding JSON. Please check the file content.")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")


if __name__ == '__main__':
    read_perf_monitor_logs()
