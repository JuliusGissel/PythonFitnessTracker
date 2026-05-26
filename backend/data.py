import json
from pathlib import Path
from typing import Any

import pandas as pd

from models import TraeningEntry, TraeningInput

DATA_PATH = Path("/app/data/traening.json")


def _indlæs_rå() -> list[dict[str, Any]]:
    """Indlæs rå JSON-data fra fil."""
    if not DATA_PATH.exists():
        return []
    with open(DATA_PATH, encoding="utf-8") as f:
        result: list[dict[str, Any]] = json.load(f)
        return result


def _gem_rå(data: list[dict[str, Any]]) -> None:
    """Gem rå JSON-data til fil."""
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)


def indlæs_som_dataframe() -> pd.DataFrame:
    """Returner alle træningspas som en Pandas DataFrame."""
    data = _indlæs_rå()
    if not data:
        return pd.DataFrame(columns=["id", "dato", "exercise", "sets", "reps", "weight"])
    df = pd.DataFrame(data)
    df["dato"] = pd.to_datetime(df["dato"]).dt.date
    return df


def hent_alle() -> list[TraeningEntry]:
    """Returner alle træningspas som en liste af TraeningEntry."""
    data = _indlæs_rå()
    return [TraeningEntry(**entry) for entry in data]


def tilføj_entry(input: TraeningInput) -> TraeningEntry:
    """Gem ét nyt træningspas og returnér det med genereret id."""
    entry = TraeningEntry(**input.model_dump())
    data = _indlæs_rå()
    data.append(entry.model_dump())
    _gem_rå(data)
    return entry


def hent_øvelser() -> list[str]:
    """Returner en sorteret liste af unikke øvelsesnavne."""
    df = indlæs_som_dataframe()
    if df.empty:
        return []
    return sorted(df["exercise"].unique().tolist())


def hent_for_øvelse(exercise: str) -> pd.DataFrame:
    """Filtrer DataFrame til kun at indeholde én øvelse, sorteret efter dato."""
    df = indlæs_som_dataframe()
    if df.empty:
        return df
    return df[df["exercise"] == exercise].sort_values("dato")
