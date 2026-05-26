# Kodegennemgang — Fitnesstracker

Dette dokument forklarer præcist hvad hver del af koden gør. Til eget brug inden eksamen.

---

## Arkitektur overblik

```
Bruger → Streamlit (frontend) → FastAPI (backend) → JSON-fil (data)
                                       ↓
                               Anthropic API (AI)
```

Streamlit og FastAPI kører i hver sin Docker-container. De taler sammen via HTTP — Streamlit kalder FastAPI's endepunkter, og FastAPI læser/skriver data til en delt JSON-fil.

---

## Backend

### `models.py` — Datamodeller med Pydantic

Pydantic er et bibliotek der validerer data automatisk. Når du definerer en klasse der arver fra `BaseModel`, sørger Pydantic for at de rigtige typer er til stede og kaster en fejl hvis de ikke er.

**`TraeningEntry`** er et komplet træningspas med alle felter — inkl. `id` (genereret automatisk med `uuid4()`) og `dato`. Bruges til at sende data *ud* af systemet.

**`TraeningInput`** er det brugeren sender *ind* — uden `id` og uden dato-generering, det sker i `data.py`. `Field(gt=0)` betyder "greater than 0", så negative sæt eller reps er ikke mulige.

**`PersonligtRekord`** og **`UgentligVolumen`** er svar-modeller til statistik-endepunkterne. FastAPI bruger dem til at validere at svaret har den rigtige form inden det sendes til Streamlit.

**`AiInput`** indeholder kun ét valgfrit felt — `exercise`. Hvis det er `None` genereres et generelt råd, ellers fokuserer AI'en på den specifikke øvelse.

---

### `data.py` — Læsning og skrivning til JSON

Her bor al kontakt med selve datafilen. Resten af koden importerer herfra — ingen andre filer rører JSON-filen direkte.

**`DATA_PATH`** er stien til JSON-filen inde i Docker-containeren (`/app/data/traening.json`). Den mappe er monteret som et *volume* i `docker-compose.yml`, så data overlever selv om containeren genstarter.

**`_indlæs_rå()`** (med underscore = privat funktion) åbner filen og parser JSON til en Python-liste af dicts. Hvis filen ikke findes endnu returneres en tom liste i stedet for en fejl.

**`_gem_rå()`** skriver en liste af dicts tilbage til filen som pænt-indenteret JSON. `default=str` betyder at typer som `date` der ikke er direkte JSON-serialiserbare automatisk konverteres til strenge.

**`indlæs_som_dataframe()`** bygger en Pandas DataFrame fra de rå data. `pd.to_datetime(...).dt.date` sikrer at dato-kolonnen altid er et `date`-objekt og ikke en streng. Denne funktion bruges af `stats.py` til beregninger.

**`hent_alle()`** returnerer data som en liste af `TraeningEntry`-objekter i stedet for rå dicts. `**entry` er Python-syntaks for "pak dict'en ud som keyword-argumenter" — det svarer til `TraeningEntry(id=..., dato=..., exercise=..., ...)`.

**`tilføj_entry()`** modtager et `TraeningInput`, opretter et `TraeningEntry` (som genererer et nyt id), indlæser den eksisterende fil, tilføjer den nye entry og gemmer det hele tilbage. Den returnerer det gemte entry så FastAPI kan sende det tilbage til Streamlit.

**`hent_øvelser()`** og **`hent_for_øvelse()`** er hjælpefunktioner til at filtrere data — bruges primært fra `stats.py` og frontend-siderne.

---

### `stats.py` — Beregninger med NumPy og Pandas

Her sker den egentlige dataanalyse. Alle funktioner bruger data fra `data.py` og returnerer enten modeller eller en base64-streng.

**`beregn_personlige_rekorder()`** grupperer DataFrame'en per øvelse med `df.groupby("exercise")`. For hver gruppe finder `idxmax()` rækken med den højeste vægt og returnerer den som en `PersonligtRekord`.

**`beregn_ugentlig_volumen()`** beregner den samlede træningsmængde per uge. Volumen er en anerkendt metrik inden for styrketræning: `sæt × gentagelser × vægt`. `dt.strftime("%G-W%V")` formaterer datoen til ISO-ugenummer (fx `"2024-W03"`), som Streamlit bruger som label i søjlediagrammet. `.tail(12)` begrænser til de seneste 12 uger.

**`generer_fremgangsgraf()`** laver en linjegraf over maks. løftet vægt per dag for én øvelse. Matplotlib tegner grafen i hukommelsen (ikke til disk) via `io.BytesIO()` — en fil-lignende buffer der kun eksisterer i RAM. Grafen gemmes som PNG i bufferen, læses ud og kodes til base64 (tekst). Det gør det muligt at sende billedet som JSON over HTTP og vise det i Streamlit med `st.image()`. `matplotlib.use("Agg")` øverst i filen fortæller Matplotlib at den ikke skal forsøge at åbne et grafvindue (det ville crashe i en server/Docker-kontekst).

**`samlet_statistik()`** bruger NumPy direkte til `np.mean()` og `np.max()`. `.to_numpy()` konverterer Pandas-kolonnen til et rent NumPy array inden beregningerne, hvilket er god praksis når man vil bruge NumPy-funktioner.

---

### `ai.py` — Integration med Anthropic API

**`generér_råd()`** tager en liste af `TraeningEntry`-objekter og bygger en prompt. Den tager de seneste 30 entries (ikke alle, for at holde prompten kort og undgå høje omkostninger) og formaterer dem som én linje per entry.

Prompten instruerer modellen til at agere personlig træner og beder specifikt om svar på dansk. Modellen der bruges er `claude-haiku-4-5-20251001` — Haiku er hurtig og billig, og passer til dette use case.

`client.messages.create()` er det faktiske API-kald. Svaret indeholder en liste af content-blokke (API'et kan returnere tekst, tool-brug, billeder osv.). Vi looper igennem og returnerer den første blok med `type == "text"`. Det er nødvendigt fordi Mypy ikke ved med sikkerhed hvilken bloktype der kommer tilbage, og vi skal håndtere det eksplicit.

API-nøglen hentes fra miljøvariablen `ANTHROPIC_API_KEY`, som sættes i `.env`-filen og injiceres i Docker-containeren via `env_file` i `docker-compose.yml`.

---

### `main.py` — FastAPI endepunkter

FastAPI bruger *decorators* (`@app.get(...)`, `@app.post(...)`) til at binde Python-funktioner til HTTP-ruter. Når en request rammer en rute, kører den tilknyttede funktion og returnerer et svar.

**`response_model=`** fortæller FastAPI hvilken Pydantic-model svaret skal valideres mod — FastAPI filtrerer automatisk felter fra der ikke er en del af modellen, og returnerer en fejl hvis et påkrævet felt mangler.

**`status_code=201`** på POST-ruten signalerer "Created" i stedet for det normale "200 OK" — det er korrekt HTTP-semantik når man opretter en ny ressource.

**`HTTPException`** bruges til at returnere fejl med den rigtige HTTP-statuskode. 404 = ikke fundet, 400 = ugyldig request. FastAPI konverterer disse til JSON-fejlsvar automatisk.

Ruterne er opdelt i tre grupper med `tags=` — det giver en pæn opdeling i den automatisk genererede API-dokumentation på `/docs`.

---

## Frontend

### `app.py` — Startside

Definerer den globale Streamlit-konfiguration (`set_page_config`) med titel og ikon. Streamlit bruger filnavne i `pages/`-mappen til automatisk at bygge en navigationsmenu i venstre side — hvert filnavn bliver et menupunkt.

### `pages/1_Log_træning.py`

`st.form()` samler alle inputfelter i én blok og sender dem samlet ved submit — uden form ville hver ændring i et felt trigge en re-render. `st.columns(3)` laver tre kolonner side om side til sæt, reps og vægt. Ved submit bygges en dict og sendes som JSON til `POST /traening` via `requests.post()`. `res.raise_for_status()` kaster en fejl hvis HTTP-statuskoden er 4xx eller 5xx.

### `pages/2_Fremgang.py`

Henter øvelsenavne fra `GET /traening/øvelser` og viser dem i en dropdown (`st.selectbox`). Når brugeren vælger en øvelse, hentes grafen fra `GET /graf/{exercise}` som en base64-streng, dekodes med `base64.b64decode()`, pakkes ind i `io.BytesIO()` og åbnes som billede med `PIL.Image.open()`. Streamlit viser det med `st.image()`.

### `pages/3_Statistik.py`

Henter personlige rekorder fra `GET /stats/rekorder` og viser dem med `st.metric()` — en Streamlit-komponent der viser en stor talværdi med en label. Ugentlig volumen hentes fra `GET /stats/volumen` og vises som søjlediagram med Streamlits indbyggede `st.bar_chart()` — den tager en dict med labels som nøgler og værdier som tal.

### `pages/4_AI_råd.py`

Samme øvelse-dropdown som fremgangssiden. Hvis brugeren vælger "Alle øvelser" sendes `exercise: null` til API'et, ellers sendes øvelsens navn. `st.spinner()` viser en loading-animation mens AI'en svarer, da Anthropic-kaldet kan tage et par sekunder.

---

## Tests

### `tests/test_data.py`

Tester `data.py`'s funktioner med en rigtig (midlertidig) JSON-fil. `@pytest.fixture` er en funktion der køres automatisk før hvert test og leverer testdata — her oprettes en tom JSON-fil i en midlertidig mappe (`tmp_path` er en built-in pytest fixture). `patch.object(data, "DATA_PATH", temp_json)` erstatter den rigtige fil-sti med test-stien så vi ikke roder med rigtige data.

### `tests/test_stats.py`

Tester `stats.py`'s beregningslogik uden at røre filsystemet. `unittest.mock.patch` erstatter funktioner midlertidigt — `patch("stats.indlæs_som_dataframe", return_value=lav_test_df())` gør at når `beregn_personlige_rekorder()` kalder `indlæs_som_dataframe()` internt, får den vores testdata i stedet for at læse filen. Det isolerer testen til kun at teste beregningslogikken.

`pytest.approx()` bruges til float-sammenligninger. I stedet for `assert 82.5 == 82.5000000001` (som ville fejle) bruges `assert value == pytest.approx(82.5)` der tillader en lille margin.

---

## Infra

### `docker-compose.yml`

Definerer to services: `backend` og `frontend`. `volumes: - ./data:/app/data` monterer den lokale `data/`-mappe ind i backend-containeren på stien `/app/data` — det er her JSON-filen lever, og det sikrer at data ikke forsvinder når containeren genstarter. `depends_on: backend` sikrer at frontend-containeren ikke starter før backend er oppe. `API_URL=http://backend:8000` bruger Docker's interne DNS — containere kan finde hinanden på service-navne inden for samme Compose-netværk.

### `pyproject.toml`

Samler konfiguration for alle tre kvalitetsværktøjer ét sted. `pythonpath = ["backend"]` under pytest gør at tests kan importere backend-moduler direkte. `strict = true` under mypy slår alle mypy-regler til, inkl. krav om type hints på alle funktioner.
