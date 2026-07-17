FROM prom/alertmanager:v0.28.1

COPY alertmanager.yml /etc/alertmanager/alertmanager.yml

EXPOSE 9093

CMD [
  "--config.file=/etc/alertmanager/alertmanager.yml",
  "--storage.path=/alertmanager"
]