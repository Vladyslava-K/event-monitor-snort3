FROM mshulha/snort3-python3:0.3

COPY event-monitor-snort3 /usr/src/event-monitor-snort3

WORKDIR /usr/src/event-monitor-snort3

COPY configs /usr/src/event-monitor-snort3/configs
COPY local_settings.py snort3_monitor/snort3_monitor/

RUN mkdir log_files && \
    mkdir snort_logs

RUN pip install -r requirements.txt
RUN /usr/local/bin/pulledpork/pulledpork.py -c configs/initial_pulledpork.conf

ENV PYTHONPATH="/usr/src/event-monitor-snort3/"

COPY wait-for-it.sh /usr/src/event-monitor-snort3/wait-for-it.sh
RUN chmod +x /usr/src/event-monitor-snort3/wait-for-it.sh

ADD configs/crontab /etc/cron.d/my-cron-file
RUN crontab /etc/cron.d/my-cron-file

EXPOSE 8000
