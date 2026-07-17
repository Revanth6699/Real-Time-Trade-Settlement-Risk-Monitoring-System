FROM prom/prometheus:v3.5.0

COPY prometheus.yml /etc/prometheus/prometheus.yml
COPY alerts.yml /etc/prometheus/alerts.yml

EXPOSE 9090

CMD [
  "--config.file=/etc/prometheus/prometheus.yml",
  "--storage.tsdb.path=/prometheus",
  "--web.enable-lifecycle"
]