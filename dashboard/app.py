import streamlit as st
import pandas as pd
import snowflake.connector
import os
from dotenv import load_dotenv
import plotly.graph_objects as go

load_dotenv(dotenv_path="../.env")

st.set_page_config(
    page_title="Clickstream Intelligence",
    page_icon="🛒",
    layout="wide"
)

# ---- Custom CSS: Amazon-inspired palette ----
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Amazon+Ember:wght@400;700&family=Inter:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        background-color: #EAEDED;
    }

    .stApp {
        background-color: #EAEDED;
    }

    .top-bar {
        background-color: #131921;
        padding: 1.2rem 1.5rem;
        border-radius: 8px;
        margin-bottom: 1.5rem;
    }

    .brand-title {
        font-size: 1.8rem;
        font-weight: 700;
        color: #FFFFFF;
    }

    .brand-title span {
        color: #FF9900;
    }

    .subtitle {
        color: #DDDDDD;
        font-size: 0.95rem;
        margin-top: 0.2rem;
    }

    .metric-card {
        background: #FFFFFF;
        border: 1px solid #DDDDDD;
        border-radius: 8px;
        padding: 1.2rem 1.5rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.08);
    }

    .metric-label {
        color: #565959;
        font-size: 0.8rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        font-weight: 600;
    }

    .metric-value {
        color: #0F1111;
        font-size: 2rem;
        font-weight: 700;
        margin-top: 0.3rem;
    }

    .metric-accent {
        color: #FF9900;
    }

    .section-header {
        font-size: 1.3rem;
        font-weight: 700;
        color: #0F1111;
        margin-top: 2rem;
        margin-bottom: 1rem;
        padding-bottom: 0.5rem;
        border-bottom: 3px solid #FF9900;
        display: inline-block;
    }

    [data-testid="stDataFrame"] {
        background-color: #FFFFFF;
        border-radius: 8px;
        border: 1px solid #DDDDDD;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def get_connection():
    return snowflake.connector.connect(
        account=os.getenv("SNOWFLAKE_ACCOUNT"),
        user=os.getenv("SNOWFLAKE_USER"),
        password=os.getenv("SNOWFLAKE_PASSWORD"),
        warehouse=os.getenv("SNOWFLAKE_WAREHOUSE"),
        database=os.getenv("SNOWFLAKE_DATABASE"),
        schema="ANALYTICS",
    )

conn = get_connection()

# ---- Header bar (Amazon navy) ----
st.markdown("""
<div class="top-bar">
    <div class="brand-title">🛒 Click<span>stream</span> Intelligence</div>
    <div class="subtitle">Real-time visibility into customer browsing and purchase behavior</div>
</div>
""", unsafe_allow_html=True)

# ---- Data ----
sessions_df = pd.read_sql("SELECT * FROM fct_sessions", conn)

total_sessions = len(sessions_df)
total_viewed = int(sessions_df['VIEWED'].sum())
total_cart = int(sessions_df['ADDED_TO_CART'].sum())
total_purchased = int(sessions_df['PURCHASED'].sum())
total_revenue = sessions_df['SESSION_REVENUE'].sum()
purchase_rate = round((total_purchased / total_cart) * 100, 1) if total_cart else 0

# ---- Metric cards ----
col1, col2, col3, col4, col5 = st.columns(5)
metrics = [
    (col1, "Total Sessions", f"{total_sessions:,}", False),
    (col2, "Added to Cart", f"{total_cart:,}", False),
    (col3, "Purchases", f"{total_purchased:,}", False),
    (col4, "Cart → Purchase Rate", f"{purchase_rate}%", True),
    (col5, "Total Revenue", f"${total_revenue:,.0f}", True),
]
for col, label, value, accent in metrics:
    value_class = "metric-value metric-accent" if accent else "metric-value"
    with col:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">{label}</div>
            <div class="{value_class}">{value}</div>
        </div>
        """, unsafe_allow_html=True)

# # ---- Funnel chart ----
st.markdown('<div class="section-header">Conversion Funnel</div>', unsafe_allow_html=True)

fig = go.Figure(go.Funnel(
    y=["Viewed", "Added to Cart", "Purchased"],
    x=[total_viewed, total_cart, total_purchased],
    textinfo="value+percent initial",
    marker={"color": ["#232F3E", "#FF9900", "#FFC266"]},
    connector={"line": {"color": "#DDDDDD", "width": 1}},
    hovertemplate="<b>%{y}</b><br>%{x} sessions<extra></extra>",
))
fig.update_layout(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font_color="#0F1111",
    height=400,
    margin=dict(t=20, b=20),
    hoverlabel=dict(
        bgcolor="#232F3E",
        font_size=13,
        font_color="#FFFFFF",
        font_family="Inter"
    )
)
st.plotly_chart(fig, use_container_width=True)

# ---- Recent sessions ----
st.markdown('<div class="section-header">Recent Sessions</div>', unsafe_allow_html=True)
st.dataframe(
    sessions_df.sort_values("SESSION_START", ascending=False).head(20),
    use_container_width=True,
    hide_index=True
)

# ---- Top users ----
st.markdown('<div class="section-header">Top Customers by Activity</div>', unsafe_allow_html=True)
users_df = pd.read_sql("SELECT * FROM fct_users ORDER BY TOTAL_SESSIONS DESC LIMIT 10", conn)
st.dataframe(users_df, use_container_width=True, hide_index=True)

# ---- AI Session Intent ----
st.markdown('<div class="section-header">🤖 AI-Classified Session Intent</div>', unsafe_allow_html=True)

intent_df = pd.read_sql("""
    SELECT si.session_id, si.intent, si.reasoning, si.classified_at,
           s.viewed_product, s.purchased_product
    FROM SESSION_INTENT si
    JOIN fct_sessions s ON si.session_id = s.session_id
    ORDER BY si.classified_at DESC
""", conn)

if len(intent_df) > 0:
    intent_col1, intent_col2 = st.columns([1, 2])

    with intent_col1:
        intent_counts = intent_df['INTENT'].value_counts().reset_index()
        intent_counts.columns = ["Intent", "Count"]

        intent_colors = {
            "browsing": "#B0C4DE",
            "comparison_shopping": "#FFC266",
            "abandoned_cart": "#FF9900",
            "ready_to_buy": "#232F3E",
            "unclassified": "#DDDDDD"
        }
        colors = [intent_colors.get(i, "#999999") for i in intent_counts["Intent"]]

        fig3 = go.Figure(go.Pie(
            labels=intent_counts["Intent"],
            values=intent_counts["Count"],
            marker=dict(colors=colors),
            hole=0.5,
            hovertemplate="<b>%{label}</b><br>%{value} sessions (%{percent})<extra></extra>",
        ))
        fig3.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            font_color="#0F1111",
            height=320,
            margin=dict(t=20, b=20),
            showlegend=True,
            legend=dict(font=dict(color="#0F1111", size=13)),
            hoverlabel=dict(bgcolor="#232F3E", font_color="#FFFFFF", font_family="Inter")
        )
        st.plotly_chart(fig3, use_container_width=True)

    with intent_col2:
        st.markdown('<p style="color:#0F1111; font-size:1.05rem; font-weight:700; margin-bottom:1rem;">Recent classifications with AI reasoning:</p>', unsafe_allow_html=True)
        for _, row in intent_df.head(6).iterrows():
            st.markdown(f"""
            <div class="metric-card" style="margin-bottom: 0.6rem; padding: 0.8rem 1.2rem;">
                <span style="background:{intent_colors.get(row['INTENT'], '#999')}; color:#0F1111; padding:2px 10px; border-radius:12px; font-size:0.75rem; font-weight:700; text-transform:uppercase;">{row['INTENT']}</span>
                <div style="margin-top:0.5rem; color:#565959; font-size:0.9rem;">{row['REASONING']}</div>
            </div>
            """, unsafe_allow_html=True)
else:
    st.info("No sessions classified yet. Run `classify_intent.py` to generate AI intent labels.")

# ---- Anomaly Detection ----
st.markdown('<div class="section-header">🚩 Flagged Anomalies</div>', unsafe_allow_html=True)

anomalies_df = pd.read_sql("""
    SELECT session_id, user_id, anomaly_type, ai_reasoning, flagged_at
    FROM SESSION_ANOMALIES
    ORDER BY flagged_at DESC
""", conn)

if len(anomalies_df) > 0:
    anomaly_col1, anomaly_col2 = st.columns([1, 2])

    with anomaly_col1:
        st.markdown(f"""
        <div class="metric-card" style="border-left: 4px solid #D13212;">
            <div class="metric-label">Total Flags</div>
            <div class="metric-value" style="color:#D13212;">{len(anomalies_df)}</div>
        </div>
        """, unsafe_allow_html=True)

        type_counts = anomalies_df['ANOMALY_TYPE'].value_counts().reset_index()
        type_counts.columns = ["Type", "Count"]
        st.markdown("<br>", unsafe_allow_html=True)
        for _, row in type_counts.iterrows():
            st.markdown(f"""
            <div style="display:flex; justify-content:space-between; padding:0.5rem 0; border-bottom:1px solid #DDDDDD;">
                <span style="color:#0F1111; font-size:0.9rem;">{row['Type']}</span>
                <span style="color:#D13212; font-weight:700;">{row['Count']}</span>
            </div>
            """, unsafe_allow_html=True)

    with anomaly_col2:
        for _, row in anomalies_df.iterrows():
            identifier = f"Session {row['SESSION_ID'][:8]}..." if pd.notna(row['SESSION_ID']) else f"User {row['USER_ID'][:8]}..."
            st.markdown(f"""
            <div class="metric-card" style="margin-bottom: 0.6rem; padding: 0.8rem 1.2rem; border-left: 3px solid #D13212;">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <span style="font-weight:700; color:#0F1111; font-size:0.9rem;">{row['ANOMALY_TYPE']}</span>
                    <span style="color:#565959; font-size:0.75rem;">{identifier}</span>
                </div>
                <div style="margin-top:0.5rem; color:#565959; font-size:0.9rem;">{row['AI_REASONING']}</div>
            </div>
            """, unsafe_allow_html=True)
else:
    st.success(" No anomalies detected — all sessions look normal.")