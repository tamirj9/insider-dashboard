import streamlit as st
import psycopg2
import pandas as pd
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta

# Load environment variables
load_dotenv()

# Database connection
def get_connection():
    return psycopg2.connect(os.getenv("DATABASE_URL"))

# Fetch transactions
def fetch_data():
    conn = get_connection()
    query = """
        SELECT 
            t.transaction_date,
            i.name AS insider_name,
            isr.company_name,
            t.transaction_code,
            t.shares,
            t.price_per_share,
            t.total_value
        FROM transactions t
        JOIN insiders i ON t.insider_id = i.insider_id
        JOIN issuers isr ON t.company_id = isr.company_id
        ORDER BY t.transaction_date DESC
    """
    df = pd.read_sql(query, conn)
    conn.close()
    return df

# Fetch AI summaries
def fetch_summaries():
    conn = get_connection()
    query = """
        SELECT 
            isr.company_name,
            a.summary_text,
            a.summary_date
        FROM ai_summaries a
        JOIN issuers isr ON a.company_id = isr.company_id
        ORDER BY a.summary_date DESC
    """
    df = pd.read_sql(query, conn)
    conn.close()
    return df

# Streamlit App
st.set_page_config(page_title="Insider Trading Dashboard", layout="wide")

st.markdown("<h1 style='text-align: center; color: crimson;'>📈 Insider Trading Dashboard</h1>", unsafe_allow_html=True)
st.markdown("---")

# Fetch data
transactions = fetch_data()
summaries = fetch_summaries()

# Sidebar Filters
st.sidebar.header("🔎 Filters")

# Company Filter
companies = transactions['company_name'].unique()
selected_company = st.sidebar.selectbox("Select Company:", ["All"] + list(companies))

# Date Range Filter
days_filter = st.sidebar.selectbox("Show transactions from:", ["All time", "Last 7 days", "Last 30 days", "Last 90 days"])
today = datetime.today()

if days_filter == "Last 7 days":
    start_date = today - timedelta(days=7)
elif days_filter == "Last 30 days":
    start_date = today - timedelta(days=30)
elif days_filter == "Last 90 days":
    start_date = today - timedelta(days=90)
else:
    start_date = None

# Filter Transactions
filtered_transactions = transactions.copy()

if selected_company != "All":
    filtered_transactions = filtered_transactions[filtered_transactions['company_name'] == selected_company]

if start_date:
    filtered_transactions = filtered_transactions[pd.to_datetime(filtered_transactions['transaction_date']) >= start_date]

# Display Transactions
st.subheader("📜 Recent Insider Transactions")
st.dataframe(filtered_transactions, use_container_width=True)

# 📥 Download filtered transactions
csv = filtered_transactions.to_csv(index=False).encode('utf-8')
st.download_button(
    label="📥 Download CSV",
    data=csv,
    file_name='insider_transactions.csv',
    mime='text/csv'
)

st.markdown("---")

# 📊 Chart: Total Shares Bought per Company
st.subheader("📊 Total Insider Shares Bought by Company")
shares_chart = filtered_transactions.groupby('company_name')['shares'].sum().sort_values(ascending=False)
st.bar_chart(shares_chart)

st.markdown("---")

# 🧠 Display AI Summaries
st.subheader("🧠 AI Generated Company Summaries")

# Filter Summaries
filtered_summaries = summaries.copy()
if selected_company != "All":
    filtered_summaries = filtered_summaries[filtered_summaries['company_name'] == selected_company]

for idx, row in filtered_summaries.iterrows():
    company_name = row['company_name']
    summary_text = row['summary_text']
    
    # Simple sentiment coloring
    if "buy" in summary_text.lower() or "positive" in summary_text.lower():
        st.success(f"**{company_name}:** {summary_text}")
    else:
        st.error(f"**{company_name}:** {summary_text}")

st.markdown("---")

# Footer
st.markdown(
    "<div style='text-align: center; font-size: 0.9em;'>"
    "© 2025 Insider Trading Dashboard | Version 1.0"
    "</div>",
    unsafe_allow_html=True
)