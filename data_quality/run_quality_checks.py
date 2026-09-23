import snowflake.connector
import ollama
import os
import json
from dotenv import load_dotenv
from datetime import datetime

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
    CREATE TABLE IF NOT EXISTS DATA_QUALITY_LOG (
        check_name STRING,
        status STRING,
        details STRING,
        ai_explanation STRING,
        checked_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
    )
""")

def ai_explain(check_name, details):
    prompt = f"""A data pipeline quality check produced this result:

Check: {check_name}
Details: {details}

In one short, plain-English sentence, explain the likely cause of this issue
to a non-technical stakeholder. If it's not actually a problem, say so briefly.
"""
    response = ollama.chat(model="llama3.2", messages=[{"role": "user", "content": prompt}])
    return response["message"]["content"].strip()

def log_result(check_name, status, details, needs_explanation=False):
    ai_explanation = ai_explain(check_name, details) if needs_explanation else None
    cursor.execute(
        "INSERT INTO DATA_QUALITY_LOG (check_name, status, details, ai_explanation) VALUES (%s, %s, %s, %s)",
        (check_name, status, details, ai_explanation)
    )
    icon = "✅" if status == "PASS" else "⚠️"
    print(f"{icon} {check_name}: {status} — {details}")
    if ai_explanation:
        print(f"   AI explanation: {ai_explanation}")

# --- Check 1: Null critical fields in raw events ---
cursor.execute("""
    SELECT COUNT(*) FROM ECOMMERCE_PIPELINE.RAW.RAW_EVENTS
    WHERE EVENT_DATA:event_type IS NULL OR EVENT_DATA:session_id IS NULL
""")
null_count = cursor.fetchone()[0]
if null_count > 0:
    log_result("Null critical fields", "FAIL", f"{null_count} raw events missing event_type or session_id", needs_explanation=True)
else:
    log_result("Null critical fields", "PASS", "No missing critical fields found")

# --- Check 2: Duplicate event_ids ---
cursor.execute("""
    SELECT COUNT(*) FROM (
        SELECT EVENT_DATA:event_id AS eid, COUNT(*) as c
        FROM ECOMMERCE_PIPELINE.RAW.RAW_EVENTS
        GROUP BY eid
        HAVING COUNT(*) > 1
    )
""")
dup_count = cursor.fetchone()[0]
if dup_count > 0:
    log_result("Duplicate events", "FAIL", f"{dup_count} duplicate event_id(s) found", needs_explanation=True)
else:
    log_result("Duplicate events", "PASS", "No duplicate events found")

# --- Check 3: Sessions with impossible negative duration ---
cursor.execute("""
    SELECT COUNT(*) FROM fct_sessions WHERE session_duration_seconds < 0
""")
neg_duration = cursor.fetchone()[0]
if neg_duration > 0:
    log_result("Negative session duration", "FAIL", f"{neg_duration} sessions with negative duration", needs_explanation=True)
else:
    log_result("Negative session duration", "PASS", "All session durations are valid")

# --- Check 4: Unusual spike in null-intent (unclassified) AI sessions ---
cursor.execute("""
    SELECT COUNT(*) FROM SESSION_INTENT WHERE intent = 'unclassified'
""")
unclassified_count = cursor.fetchone()[0]
if unclassified_count > 3:
    log_result("AI classification failures", "FAIL", f"{unclassified_count} sessions the AI could not classify", needs_explanation=True)
else:
    log_result("AI classification failures", "PASS", f"{unclassified_count} unclassified sessions (within normal range)")

conn.commit()
print("\nData quality checks complete.")
