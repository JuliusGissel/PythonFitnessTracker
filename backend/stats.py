import base64
import io
from typing import Any

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from data import hent_for_øvelse, indlæs_som_dataframe
from models import PersonligtRekord, UgentligVolumen

# Brug non-interaktiv backend så Matplotlib ikke forsøger at åbne et vindue
matplotlib.use("Agg")


def beregn_personlige_rekorder() -> list[PersonligtRekord]:
    """Returner den højeste løftede vægt per øvelse (personlig rekord)."""
    df = indlæs_som_dataframe()
    if df.empty:
        return []

    rekorder: list[PersonligtRekord] = []
    for exercise, gruppe in df.groupby("exercise"):
        idx = gruppe["weight"].idxmax()
        række = gruppe.loc[idx]
        rekorder.append(
            PersonligtRekord(
                exercise=str(exercise),
                max_weight=float(række["weight"]),
                dato=række["dato"],
            )
        )
    return rekorder


def beregn_ugentlig_volumen() -> list[UgentligVolumen]:
    """
    Beregn samlet volumen (sæt × gentagelser × vægt) per uge.
    Returnerer de seneste 12 uger, sorteret ældst til nyest.
    """
    df = indlæs_som_dataframe()
    if df.empty:
        return []

    df["dato"] = pd.to_datetime(df["dato"])
    df["volumen"] = df["sets"].astype(float) * df["reps"].astype(float) * df["weight"]
    df["uge"] = df["dato"].dt.strftime("%G-W%V")  # ISO-ugenummer

    ugentlig = (
        df.groupby("uge")["volumen"]
        .sum()
        .reset_index()
        .sort_values("uge")
        .tail(12)
    )

    return [
        UgentligVolumen(uge=str(row["uge"]), volumen=float(row["volumen"]))
        for _, row in ugentlig.iterrows()
    ]


def generer_fremgangsgraf(exercise: str) -> str:
    """
    Generér en Matplotlib-graf over maksimal løftet vægt per dato for én øvelse.
    Returnerer grafen som base64-kodet PNG-streng.
    """
    df = hent_for_øvelse(exercise)
    if df.empty:
        raise ValueError(f"Ingen data fundet for øvelsen '{exercise}'")

    df["dato"] = pd.to_datetime(df["dato"])

    # Beregn max vægt per dato med NumPy via groupby
    daglig_max = df.groupby("dato")["weight"].apply(np.max).reset_index()
    daglig_max.columns = pd.Index(["dato", "max_weight"])

    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(daglig_max["dato"], daglig_max["max_weight"], marker="o", color="#4f8ef7", linewidth=2)
    ax.fill_between(daglig_max["dato"], daglig_max["max_weight"], alpha=0.1, color="#4f8ef7")
    ax.set_title(f"Fremgang — {exercise}", fontsize=14)
    ax.set_xlabel("Dato")
    ax.set_ylabel("Maks. vægt (kg)")
    ax.grid(True, linestyle="--", alpha=0.5)
    fig.tight_layout()

    # Konvertér til base64 så Streamlit kan vise den uden filsystem
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=100)
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("utf-8")


def samlet_statistik(exercise: str) -> dict[str, Any]:
    """
    Returnér en opsummering for én øvelse:
    gennemsnitsvægt, maksimal vægt og samlet antal sæt.
    """
    df = hent_for_øvelse(exercise)
    if df.empty:
        return {}

    weights = df["weight"].to_numpy()
    return {
        "exercise": exercise,
        "gennemsnit_vægt": round(float(np.mean(weights)), 1),
        "max_vægt": float(np.max(weights)),
        "total_sæt": int(df["sets"].sum()),
        "total_løft": int((df["sets"] * df["reps"]).sum()),
    }
