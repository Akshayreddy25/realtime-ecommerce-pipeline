# Real-Time E-commerce Clickstream Intelligence Pipeline

**Stack:** Kafka · Snowflake · dbt · Python · Streamlit · Ollama (LLM)

A real-time data pipeline that streams simulated e-commerce user events (product views, cart activity, purchases) through Kafka into Snowflake, models session- and user-level analytics with dbt, and uses a locally-run LLM to classify customer intent, explain data quality issues, and flag suspicious behavioral patterns — all surfaced through a live dashboard.

## Overview

This project simulates the core data infrastructure a real e-commerce company relies on: capturing continuous user behavior, transforming it into business-ready analytics, and layering AI on top to extract judgment calls that pure SQL logic can't make — customer intent, anomaly reasoning, and plain-English explanations of data quality issues.

## Architecture
Event Simulator (Python)
│
▼
Kafka Topic (ecommerce_events)
│
▼
Kafka Consumer (Python) ──► Snowflake (RAW schema)
│
▼
dbt staging model (stg_events)
│
▼
┌─────────────────┴─────────────────┐
▼ ▼
fct_sessions (dbt) fct_users (dbt)
│ │
└─────────────────┬─────────────────┘
▼
AI Enrichment Layer (Ollama, local LLM)
├── Session intent classification
├── Data quality issue explanations
└── Anomaly / bot-behavior detection
│
▼
Streamlit Dashboard


## Features

**Real-time ingestion** — a Python event simulator generates realistic e-commerce sessions (view → cart → purchase funnel with configurable drop-off rates) and streams them through Kafka.

**Dimensional modeling** — dbt transforms raw JSON events into clean, queryable tables:
- `stg_events` — flattened event-level data
- `fct_sessions` — one row per session, with funnel flags and revenue
- `fct_users` — one row per user, aggregating behavior across all their sessions

**AI-powered session intent classification** — a local LLM (Ollama, Llama 3.2) reads each session's behavior and classifies it as `browsing`, `comparison_shopping`, `abandoned_cart`, or `ready_to_buy`, with a one-sentence explanation for each label.

**AI-explained data quality monitoring** — automated checks for null critical fields, duplicate events, and invalid session data; failures are explained in plain English by the LLM rather than surfaced as raw error counts.

**AI-powered anomaly detection** — flags statistically unusual behavior (superhuman session speed, abnormally high session counts, perfect conversion rates) as potential bot or fraud activity, with LLM-generated reasoning for each flag.

**Live dashboard** — a Streamlit app displaying real-time funnel metrics, top products, AI-classified intent breakdown, and flagged anomalies with reasoning.

## Tech Stack

| Layer | Tool |
|---|---|
| Event streaming | Apache Kafka (Docker) |
| Data warehouse | Snowflake |
| Transformation | dbt |
| AI enrichment | Ollama (Llama 3.2, local) |
| Dashboard | Streamlit, Plotly |
| Language | Python |

## Project Structure

realtime-ecommerce-pipeline/
├── simulator/ # Event generator (Kafka producer)
├── consumer/ # Kafka → Snowflake loader
├── dbt_project/ # dbt models (staging + marts)
├── ai_enrichment/ # Intent classification + anomaly detection
├── data_quality/ # Automated quality checks with AI explanations
├── dashboard/ # Streamlit app
├── docker/ # Kafka docker-compose config
└── sql/ # Snowflake setup scripts


## Setup

**Prerequisites:** Docker, Python 3.11, a Snowflake account, Ollama

```bash
# 1. Clone and set up environment
git clone https://github.com/Akshayreddy25/realtime-ecommerce-pipeline.git
cd realtime-ecommerce-pipeline
python3.11 -m venv environment
source environment/bin/activate
pip install -r requirements.txt

# 2. Start Kafka
cd docker && docker compose up -d && cd ..

# 3. Configure Snowflake credentials
cp .env.example .env   # then fill in your credentials

# 4. Build dbt models
cd dbt_project && dbt run && cd ..

# 5. Run the pipeline (in separate terminals)
python simulator/event_simulator.py
python consumer/kafka_to_snowflake.py

# 6. Run AI enrichment
python ai_enrichment/classify_intent.py
python ai_enrichment/detect_anomalies.py
python data_quality/run_quality_checks.py

# 7. Launch the dashboard
cd dashboard && streamlit run app.py
```

## Why This Architecture

Real e-commerce platforms need to react to customer behavior in real time — a company can't wait for a nightly batch job to catch a fraud pattern or a bot attack. This project demonstrates that end-to-end capability: ingesting high-volume behavioral data, modeling it into business-ready tables, and using AI to make judgment calls (intent, anomaly reasoning) that static SQL rules can't — all running on infrastructure that scales to production patterns (Kafka for streaming, dbt for governed transformation, a cloud warehouse for storage and compute).