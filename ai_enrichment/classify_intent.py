import snowflake.connector
import ollama
import os
import json
from dotenv import load_dotenv

load_dotenv(dotenv_path="../.env")

conn = snowflake.connector.connect(
    account=os.getenv("SNOWFLAKE_ACCOUNT"),
    user=os.getenv("SNOWFLAKE_USER"),
    password=os.getenv("SNOWFLAKE_PASSWORD"),
    warehouse=os.getenv("SNOWFLAKE_WAREHOUSE"),
    database=os.getenv("SNOWFLAKE_DATABASE"),
    schema="ANALYTICS",
)
cursor = conn.cursor()

# Create a table to hold AI-classified intent, if it doesn't exist yet
cursor.execute("""
    CREATE TABLE IF NOT EXISTS SESSION_INTENT (
        session_id STRING,
        intent STRING,
        reasoning STRING,
        classified_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
    )
""")

# Pull sessions that haven't been classified yet
cursor.execute("""
    SELECT s.session_id, s.viewed, s.added_to_cart, s.purchased,
           s.viewed_product, s.purchased_product, s.session_duration_seconds
    FROM fct_sessions s
    LEFT JOIN SESSION_INTENT si ON s.session_id = si.session_id
    WHERE si.session_id IS NULL
    LIMIT 20
""")
sessions = cursor.fetchall()

print(f"Found {len(sessions)} unclassified sessions.")

def classify_session(session_id, viewed, added_to_cart, purchased, viewed_product, purchased_product, duration):
    prompt = f"""You are analyzing an e-commerce user session. Classify the user's intent based on this behavior:

- Viewed a product: {"Yes" if viewed else "No"} ({viewed_product})
- Added to cart: {"Yes" if added_to_cart else "No"}
- Purchased: {"Yes" if purchased else "No"} ({purchased_product})
- Session duration: {duration} seconds

Classify this session into EXACTLY ONE of these categories:
- browsing (viewed only, no cart activity)
- comparison_shopping (viewed but didn't commit, short session)
- abandoned_cart (added to cart but did not purchase)
- ready_to_buy (purchased, or added to cart with a longer engaged session)

Respond in this exact JSON format, nothing else:
{{"intent": "one_of_the_four_labels", "reasoning": "one short sentence explaining why"}}
"""

    response = ollama.chat(
        model="llama3.2",
        messages=[{"role": "user", "content": prompt}]
    )

    content = response["message"]["content"].strip()

    try:
        result = json.loads(content)
        return result["intent"], result["reasoning"]
    except (json.JSONDecodeError, KeyError):
        return "unclassified", f"Could not parse model response: {content[:100]}"

for session in sessions:
    session_id, viewed, added_to_cart, purchased, viewed_product, purchased_product, duration = session

    intent, reasoning = classify_session(
        session_id, viewed, added_to_cart, purchased,
        viewed_product, purchased_product, duration
    )

    cursor.execute(
        "INSERT INTO SESSION_INTENT (session_id, intent, reasoning) VALUES (%s, %s, %s)",
        (session_id, intent, reasoning)
    )

    print(f"Session {session_id[:8]}... → {intent}")

conn.commit()
print("Done classifying sessions.")
