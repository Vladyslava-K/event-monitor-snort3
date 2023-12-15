# event-monitor-snort3

[![Lint](https://github.com/Vladyslava-K/event-monitor-snort3/workflows/Lint/badge.svg)](https://github.com/Vladyslava-K/event-monitor-snort3/actions?query=workflow%3ALint)

1. Check that you have Docker and Docker Compose installed.
2. Clone repository.
3. Move 'docker' folder out of the repository folder.
4. Move repository folder 'event-monitor-snort3' to docker/serv
5. Amend config files in folder 'configs' if necessary.
6. From the 'docker' folder run 'docker-compose up --build'

For testing, it has local rule to catch anything on dst_port 80, so:
1. Pull nginx image from docker hub 'docker pull nginx'
2. Run it on the same network as main project:
'docker run -d --name http-server-container --network=full_project_snort_network -p 8080:80 nginx'
3. From server container access nginx server with 'curl http://http-server-container:80' (run several times and wait a bit)

Snort will catch these events, alert_reader will read them and store to DB, Djando/DRF project will provide access via 
API by routes described in Open API Specification.

Project scheme:
<img width="2389" alt="Screenshot 2023-11-20 at 16 50 46" src="https://github.com/maksym-shulha/event-monitor-snort3/assets/123635020/e497a301-304d-48b6-931c-396b315ddcbe">
