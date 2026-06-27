from kafka import KafkaConsumer
import json
import os

consumer = KafkaConsumer(
    'risk-alerts',
    bootstrap_servers=os.getenv("KAFKA_BOOTSTRAP_SERVERS"),
    auto_offset_reset='earliest',
    group_id='risk-group',
    value_deserializer=lambda x: json.loads(x.decode('utf-8'))
)

for message in consumer:

    data = message.value

    print("RISK ALERT RECEIVED:", data)