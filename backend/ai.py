# Placeholder — udfyldes i Trin 3
import os

import anthropic

from models import TraeningEntry


def generér_råd(entries: list[TraeningEntry], exercise: str | None = None) -> str:
    """
    Send træningshistorik til Anthropic API og returnér personlige råd.
    Hvis exercise er angivet, fokuseres rådet på den pågældende øvelse.
    """
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    # Byg en tekstopsummering af brugerens historik
    historik_linjer = [
        f"{e.dato} | {e.exercise} | {e.sets} sæt × {e.reps} reps @ {e.weight} kg"
        for e in entries[-30:]  # Seneste 30 entries
    ]
    historik_tekst = "\n".join(historik_linjer)

    fokus = f" med fokus på øvelsen '{exercise}'" if exercise else ""
    prompt = (
        f"Du er en erfaren personlig træner. Her er brugerens seneste træningslog:\n\n"
        f"{historik_tekst}\n\n"
        f"Giv konkrete og personlige træningsråd på dansk{fokus}. "
        f"Vær specifik og baser dine råd på den faktiske historik."
    )

    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=512,
        messages=[{"role": "user", "content": prompt}],
    )

    # Udtræk kun tekstblokke — mypy kræver eksplicit typecheck
    for block in message.content:
        if block.type == "text":
            return block.text
    return "Ingen svar modtaget fra AI."
