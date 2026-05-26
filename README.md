# Fitnesstracker

Webapplikation til at logge træningspas og følge fremgang over tid.

## Krav
- Docker Desktop

## Kom i gang

1. Kopiér `.env.example` til `.env` og indsæt din Anthropic API-nøgle
2. Kør applikationen:

```bash
docker compose up
```

3. Åbn browseren:
   - Frontend: http://localhost:8501
   - Backend API: http://localhost:8000/docs

## Stop applikationen

```bash
docker compose down
```

## Teknologier
- **Frontend:** Streamlit
- **Backend:** FastAPI
- **Data:** Pandas, NumPy, Matplotlib
- **AI:** Anthropic API (Claude)
- **Test:** Pytest, Mypy, Ruff
- **Infra:** Docker Compose
