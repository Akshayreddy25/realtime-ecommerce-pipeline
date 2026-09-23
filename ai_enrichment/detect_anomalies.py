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

cursor.execute("""
    CREATE TABLE IF NOT EXISTS SESSION_ANOMALIES (
        session_id STRING,
        user_id STRING,
        anomaly_type STRING,
        ai_reasoning STRING,
        flagged_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
    )
""")

def ai_reason_about_anomaly(anomaly_type, details):
    prompt = f"""A behavioral anomaly was detected in an e-commerce session:

Anomaly type: {anomaly_type}
Details: {details}

In one short sentence, explain why this pattern is suspicious and what it
might indicate (e.g., bot activity, automated script, fraud risk, or a false alarm).
"""
    response = ollama.chat(model="llama3.2", messages=[{"role": "user", "content": prompt}])
    return response["message"]["content"].strip()

def flag_anomaly(session_id, user_id, anomaly_type, details):
    reasoning = ai_reason_about_anomaly(anomaly_type, details)
    cursor.execute(
        "INSERT INTO SESSION_ANOMALIES (session_id, user_id, anomaly_type, ai_reasoning) VALUES (%s, %s, %s, %s)",
        (session_id, user_id, anomaly_type, reasoning)
    )
    identifier = f"session {session_id[:8]}..." if session_id else f"user {user_id[:8]}..."
    print(f"🚩 {anomaly_type} | {identifier}")
    print(f"   AI reasoning: {reasoning}")

# --- Pattern 1: Superhuman speed (purchase within 2 seconds of viewing) ---
cursor.execute("""
    SELECT session_id, user_id, session_duration_seconds
    FROM fct_sessions
    WHERE purchased = 1 AND session_duration_seconds <= 2
""")
fast_sessions = cursor.fetchall()
for session_id, user_id, duration in fast_sessions:
    flag_anomaly(
        session_id, user_id, "Superhuman session speed",
        f"Session went from view to purchase in {duration} seconds"
    )

# --- Pattern 2: Abnormally high session count per user ---
cursor.execute("""
    SELECT user_id, total_sessions
    FROM fct_users
    WHERE total_sessions > (SELECT AVG(total_sessions) + 2 * STDDEV(total_sessions) FROM fct_users)
""")
high_activity_users = cursor.fetchall()
for user_id, total_sessions in high_activity_users:
    flag_anomaly(
        None, user_id, "Abnormally high session count",
        f"User has {total_sessions} sessions, far above the average"
    )

# --- Pattern 3: Perfect conversion rate at scale ---
cursor.execute("""
    SELECT user_id, total_sessions, purchase_rate
    FROM fct_users
    WHERE purchase_rate = 1.0 AND total_sessions >= 3
""")
perfect_converters = cursor.fetchall()
for user_id, total_sessions, purchase_rate in perfect_converters:
    flag_anomaly(
        None, user_id, "Perfect conversion rate",
        f"User purchased in all {total_sessions} of their sessions (100% conversion)"
    )

conn.commit()
total_flags = len(fast_sessions) + len(high_activity_users) + len(perfect_converters)
print(f"\nAnomaly detection complete. {total_flags} anomalies flagged.")
