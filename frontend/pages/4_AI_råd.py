import streamlit as st
import requests
import os

API_URL = os.environ.get("API_URL", "http://localhost:8000")

st.title("AI-træningsråd")
st.write("Få personlige råd baseret på din træningshistorik.")

# Hent øvelser til valgfrit filter
try:
    res = requests.get(f"{API_URL}/traening/øvelser")
    res.raise_for_status()
    øvelser = ["Alle øvelser"] + res.json()
except requests.RequestException:
    øvelser = ["Alle øvelser"]

valgt = st.selectbox("Fokusér på én øvelse (valgfrit)", øvelser)

if st.button("Generér råd"):
    exercise = None if valgt == "Alle øvelser" else valgt
    with st.spinner("Henter råd fra AI..."):
        try:
            res = requests.post(f"{API_URL}/ai/raad", json={"exercise": exercise})
            res.raise_for_status()
            råd = res.json()["råd"]
            st.success("Her er dine personlige træningsråd:")
            st.write(råd)
        except requests.RequestException as e:
            st.error(f"Kunne ikke hente råd: {e}")
