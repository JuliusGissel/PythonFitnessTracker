import streamlit as st
import requests
import os
import base64
from PIL import Image
import io

API_URL = os.environ.get("API_URL", "http://localhost:8000")

st.title("Fremgang")

# Hent liste af øvelser
try:
    res = requests.get(f"{API_URL}/traening/øvelser")
    res.raise_for_status()
    øvelser = res.json()
except requests.RequestException:
    øvelser = []

if not øvelser:
    st.info("Ingen træningsdata endnu. Log dit første træningspas.")
else:
    valgt = st.selectbox("Vælg øvelse", øvelser)

    if valgt:
        try:
            res = requests.get(f"{API_URL}/graf/{valgt}")
            res.raise_for_status()
            img_b64 = res.json()["image_base64"]
            img = Image.open(io.BytesIO(base64.b64decode(img_b64)))
            st.image(img, use_column_width=True)
        except requests.RequestException as e:
            st.error(f"Kunne ikke hente graf: {e}")
