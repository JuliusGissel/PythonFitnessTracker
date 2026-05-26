import streamlit as st
import requests
import os
from datetime import date

API_URL = os.environ.get("API_URL", "http://localhost:8000")

st.title("Log træning")

with st.form("log_form"):
    dato = st.date_input("Dato", value=date.today())
    exercise = st.text_input("Øvelse", placeholder="fx Bænkpres")
    col1, col2, col3 = st.columns(3)
    sets = col1.number_input("Sæt", min_value=1, value=3)
    reps = col2.number_input("Gentagelser", min_value=1, value=10)
    weight = col3.number_input("Vægt (kg)", min_value=0.0, value=60.0, step=2.5)
    submitted = st.form_submit_button("Gem træningspas")

if submitted:
    if not exercise.strip():
        st.error("Udfyld øvelsens navn.")
    else:
        payload = {
            "dato": str(dato),
            "exercise": exercise.strip(),
            "sets": sets,
            "reps": reps,
            "weight": weight,
        }
        try:
            res = requests.post(f"{API_URL}/traening", json=payload)
            res.raise_for_status()
            st.success(f"Gemt: {exercise} — {sets}×{reps} @ {weight} kg")
        except requests.RequestException as e:
            st.error(f"Kunne ikke gemme: {e}")
