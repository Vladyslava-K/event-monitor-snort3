import os
import json
import subprocess
import django
import logging

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "snort3_monitor.settings")
django.setup()

from event.models import Rule


logging.basicConfig(level=logging.ERROR,
                    filename='log_files/rule_reader.log',
                    filemode='a',
                    format='{asctime} - {name} - {levelname} - {message}',
                    style='{'
                    )


def rule_reader():
    """
    Executes Snort command, processes the output, and writes entries to the database.
    Deletes the temporary output file after processing.
    """
    output_file_path = 'rules/snort_rules.json'
    command = f'snort -c configs/custom_snort.lua --dump-rule-meta > {output_file_path}'

    try:
        subprocess.run(command, check=True, shell=True)
        print('Snort command executed successfully.')
    except subprocess.CalledProcessError as e:
        logging.error('Error while dumping Snort rules to json:', e.stderr)

    process_and_write_to_db(output_file_path)


def process_and_write_to_db(output_file_path):
    """
    Reads the Snort rules from the specified file, extracts relevant data,
    and writes entries to the Rule model in the Django database.
    Deletes the temporary output file after processing.
    """
    with open(output_file_path, 'r', encoding='utf-8', errors='replace') as f:
        all_lines = f.readlines()

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
            except Exception as e:
                logging.error(f"Error writing to DB: {e}")

        print('Entries were written to DB')

        os.remove(output_file_path)

        print('snort_rules.json was deleted')


if __name__ == "__main__":
    rule_reader()
