from kafka import KafkaProducer
import json
import time
import random
import uuid
from datetime import datetime

producer = KafkaProducer(
    bootstrap_servers='localhost:9092',
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

PRODUCTS = [
    {"product_id": "P001", "name": "Wireless Headphones", "price": 79.99},
    {"product_id": "P002", "name": "Running Shoes", "price": 59.99},
    {"product_id": "P003", "name": "Coffee Maker", "price": 45.00},
    {"product_id": "P004", "name": "Yoga Mat", "price": 25.00},
    {"product_id": "P005", "name": "Backpack", "price": 39.99},
]

# A fixed pool of 50 fake "customers" — reused across many visits,
# so the same user_id can show up in multiple separate sessions
USER_IDS = [str(uuid.uuid4()) for _ in range(50)]

def generate_event(user_id, session_id, event_type):
    product = random.choice(PRODUCTS)
    return {
        "event_id": str(uuid.uuid4()),
        "user_id": user_id,
        "session_id": session_id,
        "event_type": event_type,
        "product_id": product["product_id"],
        "product_name": product["name"],
        "price": product["price"],
        "timestamp": datetime.utcnow().isoformat()
    }

def simulate_user_session():
    user_id = random.choice(USER_IDS)   # may repeat — same person, new visit
    session_id = str(uuid.uuid4())      # always unique — one specific visit

    view_event = generate_event(user_id, session_id, "view")
    producer.send('ecommerce_events', view_event)
    print(f"User {user_id[:8]} | Sent: {view_event['event_type']} - {view_event['product_name']}")

    if random.random() < 0.4:
        time.sleep(random.uniform(1, 3))
        cart_event = generate_event(user_id, session_id, "add_to_cart")
        producer.send('ecommerce_events', cart_event)
        print(f"User {user_id[:8]} | Sent: {cart_event['event_type']} - {cart_event['product_name']}")

        if random.random() < 0.5:
            time.sleep(random.uniform(1, 3))
            purchase_event = generate_event(user_id, session_id, "purchase")
            producer.send('ecommerce_events', purchase_event)
            print(f"User {user_id[:8]} | Sent: {purchase_event['event_type']} - {purchase_event['product_name']}")

if __name__ == "__main__":
    print("Starting event simulator... (Ctrl+C to stop)")
    while True:
        simulate_user_session()
        producer.flush()
        time.sleep(random.uniform(0.5, 2))
