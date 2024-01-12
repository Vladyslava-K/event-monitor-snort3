from .db_config import perf_monitor
import json


with open('../../snort_logs/perf_monitor_base.json', 'r') as file:
    json_content = file.read()
    if not json_content.endswith(']'):
        json_content += ']'

    json_data = json.loads(json_content)

    for document in json_data:
        perf_monitor.insert_one(document)
