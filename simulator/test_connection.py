from kafka import KafkaProducer
import json

producer = KafkaProducer(
    bootstrap_servers='localhost:9092',
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

producer.send('ecommerce_events', {"test": "hello kafka"})
producer.flush()
print("Message sent successfully!")
