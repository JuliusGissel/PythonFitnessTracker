import uuid
from datetime import date

from pydantic import BaseModel, Field


class TraeningEntry(BaseModel):
    """Et enkelt træningssæt logget af brugeren."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    dato: date
    exercise: str
    sets: int = Field(gt=0)
    reps: int = Field(gt=0)
    weight: float = Field(ge=0)


class TraeningInput(BaseModel):
    """Input fra brugeren — uden id og dato (genereres automatisk)."""

    dato: date
    exercise: str
    sets: int = Field(gt=0)
    reps: int = Field(gt=0)
    weight: float = Field(ge=0)


class PersonligtRekord(BaseModel):
    """Personlig rekord for én øvelse."""

    exercise: str
    max_weight: float
    dato: date


class UgentligVolumen(BaseModel):
    """Samlet volumen (sæt × gentagelser × vægt) for én uge."""

    uge: str  # ISO-format: "2024-W03"
    volumen: float


class AiInput(BaseModel):
    """Data sendt til AI-endepunktet."""

    exercise: str | None = None  # Ingen = generel anbefaling
