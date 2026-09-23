from kafka import KafkaConsumer
import snowflake.connector
import json
import os
from dotenv import load_dotenv

load_dotenv()

conn = snowflake.connector.connect(
    account=os.getenv("SNOWFLAKE_ACCOUNT"),
    user=os.getenv("SNOWFLAKE_USER"),
    password=os.getenv("SNOWFLAKE_PASSWORD"),
    warehouse=os.getenv("SNOWFLAKE_WAREHOUSE"),
    database=os.getenv("SNOWFLAKE_DATABASE"),
    schema=os.getenv("SNOWFLAKE_SCHEMA"),
)
cursor = conn.cursor()

consumer = KafkaConsumer(
    'ecommerce_events',
    bootstrap_servers='localhost:9092',
    value_deserializer=lambda v: json.loads(v.decode('utf-8')),
    auto_offset_reset='earliest',
    group_id='snowflake-loader-group'
)

print("Consumer started. Listening for events... (Ctrl+C to stop)")

for message in consumer:
    event = message.value
    cursor.execute(
        "INSERT INTO RAW_EVENTS (EVENT_DATA) SELECT PARSE_JSON(%s)",
        (json.dumps(event),)
    )
    print(f"Loaded: {event['event_type']} - {event['product_name']}")
