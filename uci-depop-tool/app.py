import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import os

st.set_page_config(page_title="UCI Depop Booth Optimizer", layout="centered")
st.title("🧵 UCI Depop Booth Optimizer")

@st.cache_data
def load_kpi():
    return pd.read_csv("data/kpi_weekly.csv")

kpi = load_kpi()
uci_row = kpi[kpi['School'] == 'UCIrvine'].iloc[0]

with st.sidebar:
    st.subheader("Latest UCI KPIs")
    st.metric("QR Scans", int(uci_row['QR Code Scan']))
    st.metric("App Installs", int(uci_row['App Install']))
    st.metric("Sign-Ups", int(uci_row['Sign-Up']))
    conv = uci_row['Sign-Up'] / uci_row['QR Code Scan']
    st.metric("Conversion (QR→Sign-Up)", f"{conv:.1%}")

st.header("1. Add upcoming UCI events")
with st.form("event_form"):
    name = st.text_input("Event name")
    date = st.date_input("Date", min_value=datetime.today())
    start = st.time_input("Start time")
    end = st.time_input("End time")
    location = st.text_input("Location")
    category = st.selectbox("Category", ["Fashion/Resale", "Club Fair", "Academic", "Sports", "Other"])
    expected = st.slider("Expected attendance", 0, 2000, 200)
    submitted = st.form_submit_button("Save event")

EVENT_FILE = "data/events_manual.csv"
if submitted:
    new = pd.DataFrame([{
        "name": name, "date": date.strftime("%Y-%m-%d"),
        "start": start.strftime("%H:%M"), "end": end.strftime("%H:%M"),
        "location": location, "category": category, "expected": expected
    }])
    new.to_csv(EVENT_FILE, mode="a", header=not os.path.exists(EVENT_FILE), index=False)
    st.success("Event saved.")

if os.path.exists(EVENT_FILE):
    events = pd.read_csv(EVENT_FILE)
    events["datetime"] = pd.to_datetime(events["date"] + " " + events["start"])
else:
    events = pd.DataFrame(columns=["name","date","start","end","location","category","expected","datetime"])

def score_event(row):
    base = row["expected"]
    if row["category"] == "Fashion/Resale": base *= 1.5
    elif row["category"] == "Club Fair":   base *= 1.2
    if row["datetime"].weekday() in [1,2,3] and 11 <= row["datetime"].hour <= 14: base *= 1.3
    return int(base)

if not events.empty:
    events["score"] = events.apply(score_event, axis=1)

st.header("2. Top 3 booth recommendations (next 7 days)")
if events.empty:
    st.info("No events yet — add some above.")
else:
    future = events[events["datetime"] >= datetime.now()]
    top3 = future.nlargest(3, "score")[["date","start","end","location","category","score"]]
    st.dataframe(top3, use_container_width=True)

st.header("3. KPI trend (manual until multi-week file)")
weeks = ["Week 9", "Week 10"]
qr    = [uci_row["QR Code Scan"], uci_row["QR Code Scan"]+20]
installs = [uci_row["App Install"], uci_row["App Install"]+5]
signups  = [uci_row["Sign-Up"], uci_row["Sign-Up"]+10]
trend = pd.DataFrame({"Week": weeks, "QR": qr, "Installs": installs, "Sign-Ups": signups})
fig = px.line(trend, x="Week", y=["QR","Installs","Sign-Ups"], markers=True,
              title="UCI Weekly KPIs (dummy Week 10 for demo)")
st.plotly_chart(fig, use_container_width=True)
st.caption("Replace the dummy Week-10 numbers with real data when you get next CSV.")
