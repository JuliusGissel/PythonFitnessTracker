import os

import requests
import streamlit as st

API_URL = os.environ.get("API_URL", "http://localhost:8000")

st.set_page_config(
    page_title="Fitnesstracker",
    layout="centered",
)

st.title("Fitnesstracker")

# ── Personlige rekorder ────────────────────────────────────────────────────────
st.subheader("Personlige rekorder")
try:
    res = requests.get(f"{API_URL}/stats/rekorder")
    res.raise_for_status()
    rekorder = res.json()
    if rekorder:
        for r in rekorder:
            st.metric(label=r["exercise"], value=f"{r['max_weight']} kg", help=f"Sat {r['dato']}")
    else:
        st.info("Ingen data endnu. Log dit første træningspas under 'Log træning'.")
except requests.RequestException as e:
    st.error(f"Fejl: {e}")

st.divider()

# ── Ugentlig volumen ───────────────────────────────────────────────────────────
st.subheader("Ugentlig volumen (seneste 12 uger)")
try:
    res = requests.get(f"{API_URL}/stats/volumen")
    res.raise_for_status()
    volumen = res.json()
    if volumen:
        uger = [v["uge"] for v in volumen]
        værdier = [v["volumen"] for v in volumen]
        st.bar_chart(dict(zip(uger, værdier)))
    else:
        st.info("Ingen data endnu.")
except requests.RequestException as e:
    st.error(f"Fejl: {e}")
