import pytest
from datetime import date
from unittest.mock import patch
from pathlib import Path

import data
from models import TraeningInput


@pytest.fixture
def temp_json(tmp_path: Path) -> Path:
    """Opret en midlertidig tom JSON-datafil til hvert test."""
    fil = tmp_path / "traening.json"
    fil.write_text("[]", encoding="utf-8")
    return fil


# ── Tilføj og hent ─────────────────────────────────────────────────────────────

def test_tilføj_entry_gemmes_korrekt(temp_json: Path) -> None:
    """Et gemt entry skal kunne hentes tilbage med samme værdier."""
    with patch.object(data, "DATA_PATH", temp_json):
        inp = TraeningInput(dato=date(2024, 1, 15), exercise="Bænkpres", sets=3, reps=10, weight=80.0)
        entry = data.tilføj_entry(inp)

        alle = data.hent_alle()

    assert len(alle) == 1
    assert alle[0].id == entry.id
    assert alle[0].exercise == "Bænkpres"
    assert alle[0].weight == 80.0


def test_flere_entries_gemmes(temp_json: Path) -> None:
    """Flere entries skal akkumuleres i filen."""
    with patch.object(data, "DATA_PATH", temp_json):
        for vægt in [60.0, 70.0, 80.0]:
            data.tilføj_entry(
                TraeningInput(dato=date(2024, 1, 1), exercise="Squat", sets=3, reps=5, weight=vægt)
            )
        alle = data.hent_alle()

    assert len(alle) == 3


def test_hent_alle_tom_fil(temp_json: Path) -> None:
    """Tom JSON-fil skal returnere en tom liste — ingen crash."""
    with patch.object(data, "DATA_PATH", temp_json):
        alle = data.hent_alle()

    assert alle == []


# ── Øvelser ────────────────────────────────────────────────────────────────────

def test_hent_øvelser_sorteret(temp_json: Path) -> None:
    """Øvelser skal returneres alfabetisk sorteret."""
    with patch.object(data, "DATA_PATH", temp_json):
        for navn in ["Squat", "Bænkpres", "Dødløft"]:
            data.tilføj_entry(
                TraeningInput(dato=date(2024, 1, 1), exercise=navn, sets=3, reps=10, weight=100.0)
            )
        øvelser = data.hent_øvelser()

    assert øvelser == ["Bænkpres", "Dødløft", "Squat"]


def test_hent_øvelser_ingen_dubletter(temp_json: Path) -> None:
    """Samme øvelse logget to gange må kun optræde én gang i listen."""
    with patch.object(data, "DATA_PATH", temp_json):
        for _ in range(3):
            data.tilføj_entry(
                TraeningInput(dato=date(2024, 1, 1), exercise="Bænkpres", sets=3, reps=10, weight=80.0)
            )
        øvelser = data.hent_øvelser()

    assert øvelser == ["Bænkpres"]


# ── Filter per øvelse ──────────────────────────────────────────────────────────

def test_hent_for_øvelse_filtrerer_korrekt(temp_json: Path) -> None:
    """hent_for_øvelse skal kun returnere rækker for den valgte øvelse."""
    with patch.object(data, "DATA_PATH", temp_json):
        data.tilføj_entry(TraeningInput(dato=date(2024, 1, 1), exercise="Bænkpres", sets=3, reps=10, weight=80.0))
        data.tilføj_entry(TraeningInput(dato=date(2024, 1, 1), exercise="Squat",    sets=4, reps=8,  weight=100.0))
        df = data.hent_for_øvelse("Bænkpres")

    assert len(df) == 1
    assert df.iloc[0]["exercise"] == "Bænkpres"
