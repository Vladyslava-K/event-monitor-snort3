FROM mshulha/snort3-python3:0.1

COPY event-monitor-snort3 /usr/src/event-monitor-snort3

WORKDIR /usr/src/event-monitor-snort3

COPY configs /usr/src/event-monitor-snort3/configs

COPY local_settings.py snort3_monitor/snort3_monitor/

RUN mkdir log_files && \
    mkdir snort_logs

RUN pip install -r requirements.txt

RUN /usr/local/bin/pulledpork/pulledpork.py -c configs/pulledpork.conf

COPY wait-for-it.sh /usr/src/event-monitor-snort3/wait-for-it.sh
COPY start.sh /usr/src/event-monitor-snort3/start.sh

RUN chmod +x /usr/src/event-monitor-snort3/wait-for-it.sh && \
    chmod +x /usr/src/event-monitor-snort3/start.sh

EXPOSE 8000