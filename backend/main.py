from typing import Any

from fastapi import FastAPI, HTTPException

import ai
import data
import stats
from models import AiInput, PersonligtRekord, TraeningEntry, TraeningInput, UgentligVolumen

app = FastAPI(
    title="Fitnesstracker API",
    description="Backend til logning og analyse af træningspas",
    version="1.0.0",
)


# ── Træningspas ────────────────────────────────────────────────────────────────

@app.get("/traening", response_model=list[TraeningEntry], tags=["Træning"])
def hent_alle_traening() -> list[TraeningEntry]:
    """Hent alle loggede træningspas."""
    return data.hent_alle()


@app.post("/traening", response_model=TraeningEntry, status_code=201, tags=["Træning"])
def log_traening(input: TraeningInput) -> TraeningEntry:
    """Log ét nyt træningspas."""
    return data.tilføj_entry(input)


@app.get("/traening/øvelser", response_model=list[str], tags=["Træning"])
def hent_øvelser() -> list[str]:
    """Hent en liste af alle øvelsesnavne der er logget."""
    return data.hent_øvelser()


# ── Statistik ──────────────────────────────────────────────────────────────────

@app.get("/stats/rekorder", response_model=list[PersonligtRekord], tags=["Statistik"])
def personlige_rekorder() -> list[PersonligtRekord]:
    """Hent personlig rekord (højeste vægt) per øvelse."""
    return stats.beregn_personlige_rekorder()


@app.get("/stats/volumen", response_model=list[UgentligVolumen], tags=["Statistik"])
def ugentlig_volumen() -> list[UgentligVolumen]:
    """Hent ugentlig samlet volumen (sæt × reps × vægt) for de seneste 12 uger."""
    return stats.beregn_ugentlig_volumen()


@app.get("/stats/{exercise}", tags=["Statistik"])
def statistik_for_øvelse(exercise: str) -> dict[str, Any]:
    """Hent gennemsnit, maks og totaler for én øvelse."""
    result = stats.samlet_statistik(exercise)
    if not result:
        raise HTTPException(status_code=404, detail=f"Ingen data for øvelsen '{exercise}'")
    return result


# ── Grafer ─────────────────────────────────────────────────────────────────────

@app.get("/graf/{exercise}", tags=["Grafer"])
def fremgangsgraf(exercise: str) -> dict[str, Any]:
    """
    Generér en graf over maksimal løftet vægt over tid for én øvelse.
    Returnerer en base64-kodet PNG.
    """
    try:
        grafdata = stats.generer_fremgangsgraf(exercise)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return {"image_base64": grafdata}


# ── AI ─────────────────────────────────────────────────────────────────────────

@app.post("/ai/raad", tags=["AI"])
def ai_raad(input: AiInput) -> dict[str, Any]:
    """
    Generér personlige træningsråd baseret på brugerens historik.
    Sender data til Anthropic API og returnerer anbefalinger.
    """
    alle_entries = data.hent_alle()
    if not alle_entries:
        raise HTTPException(status_code=400, detail="Ingen træningsdata at basere råd på")

    råd = ai.generér_råd(alle_entries, exercise=input.exercise)
    return {"råd": råd}
