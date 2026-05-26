import pytest
import pandas as pd
from datetime import date, timedelta
from unittest.mock import patch

import stats


def lav_test_df() -> pd.DataFrame:
    """Returnér en lille test-DataFrame med to øvelser over to uger."""
    return pd.DataFrame([
        {"id": "1", "dato": date(2024, 1, 1), "exercise": "Bænkpres", "sets": 3, "reps": 10, "weight": 80.0},
        {"id": "2", "dato": date(2024, 1, 8), "exercise": "Bænkpres", "sets": 3, "reps": 10, "weight": 85.0},
        {"id": "3", "dato": date(2024, 1, 1), "exercise": "Squat",    "sets": 4, "reps": 8,  "weight": 100.0},
    ])


# ── Personlige rekorder ────────────────────────────────────────────────────────

def test_personlig_rekord_returnerer_højeste_vægt() -> None:
    """Rekord skal være den højeste vægt logget for øvelsen."""
    with patch("stats.indlæs_som_dataframe", return_value=lav_test_df()):
        rekorder = stats.beregn_personlige_rekorder()

    bænk = next(r for r in rekorder if r.exercise == "Bænkpres")
    squat = next(r for r in rekorder if r.exercise == "Squat")

    assert bænk.max_weight == 85.0
    assert squat.max_weight == 100.0


def test_personlig_rekord_tom_dataframe() -> None:
    """Tom DataFrame skal returnere en tom liste — ingen crash."""
    with patch("stats.indlæs_som_dataframe", return_value=pd.DataFrame()):
        rekorder = stats.beregn_personlige_rekorder()

    assert rekorder == []


def test_personlig_rekord_antal_matcher_øvelser() -> None:
    """Der skal være præcis én rekord per unik øvelse."""
    with patch("stats.indlæs_som_dataframe", return_value=lav_test_df()):
        rekorder = stats.beregn_personlige_rekorder()

    assert len(rekorder) == 2


# ── Ugentlig volumen ───────────────────────────────────────────────────────────

def test_ugentlig_volumen_total() -> None:
    """Samlet volumen skal stemme: (3×10×80) + (3×10×85) + (4×8×100) = 8150."""
    with patch("stats.indlæs_som_dataframe", return_value=lav_test_df()):
        volumen = stats.beregn_ugentlig_volumen()

    total = sum(v.volumen for v in volumen)
    assert total == pytest.approx(8150.0)


def test_ugentlig_volumen_tom_dataframe() -> None:
    """Tom DataFrame skal returnere en tom liste."""
    with patch("stats.indlæs_som_dataframe", return_value=pd.DataFrame()):
        volumen = stats.beregn_ugentlig_volumen()

    assert volumen == []


def test_ugentlig_volumen_maks_12_uger() -> None:
    """Funktionen må maksimalt returnere 12 uger."""
    # Lav data over 15 uger
    start = date(2024, 1, 1)
    rækker = [
        {"id": str(i), "dato": start + timedelta(weeks=i), "exercise": "Bænkpres",
         "sets": 3, "reps": 10, "weight": 80.0}
        for i in range(15)
    ]
    df = pd.DataFrame(rækker)
    with patch("stats.indlæs_som_dataframe", return_value=df):
        volumen = stats.beregn_ugentlig_volumen()

    assert len(volumen) <= 12


# ── Samlet statistik ───────────────────────────────────────────────────────────

def test_samlet_statistik_beregner_korrekt() -> None:
    """Gennemsnit, maks og totaler skal beregnes korrekt."""
    df = lav_test_df()
    bænk_df = df[df["exercise"] == "Bænkpres"].copy()

    with patch("stats.hent_for_øvelse", return_value=bænk_df):
        statistik = stats.samlet_statistik("Bænkpres")

    assert statistik["max_vægt"] == 85.0
    assert statistik["gennemsnit_vægt"] == pytest.approx(82.5)
    assert statistik["total_sæt"] == 6       # 3 + 3
    assert statistik["total_løft"] == 60     # (3×10) + (3×10)


def test_samlet_statistik_ukendt_øvelse() -> None:
    """Ukendt øvelse skal returnere en tom dict."""
    with patch("stats.hent_for_øvelse", return_value=pd.DataFrame()):
        statistik = stats.samlet_statistik("Ukendt")

    assert statistik == {}
