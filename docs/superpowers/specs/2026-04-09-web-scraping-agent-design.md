# Sub-progetto B — Web Scraping Agent (Reale)

**Data**: 2026-04-09
**Stato**: Approvato
**Scope**: Sostituire lo `scraping_stub` con un agente reale che usa OpenStreetMap (Overpass API) per trovare lead B2B (piccole attività senza sito web), con scheduling per fuso orario e configurazione dinamica dalla dashboard.

---

## 1. Contesto

Questo è il Sub-progetto B della piattaforma agenti AI. Il Sub-progetto A è già deployato (https://agents-dashboard-theta.vercel.app) con tre stub agent che simulano il flusso. Ora sostituiamo lo `scraping_stub` con un agente reale che:

- Trova attività su OpenStreetMap via Overpass API
- Filtra automaticamente quelle **senza sito web**
- Si attiva alle **9:00 locali in ogni fuso orario** configurato
- Salva i lead in Supabase + emette eventi `scraping.lead_found` per il Setting Agent
- È **configurabile dalla dashboard** (categorie + città + timezone)

Il Sub-progetto B mantiene la stessa interfaccia eventi del Sub-progetto A — il Setting Agent e il Builder Agent continuano a funzionare senza modifiche.

---

## 2. Decisioni architetturali

| Aspetto | Scelta | Motivazione |
|---|---|---|
| Fonte dati | OpenStreetMap + Overpass API | Open source, gratuito, query "no website" nativa, no vendor lock-in |
| Sync esterno | Nessuno (solo Supabase + Excel export esistente) | Sheets/Drive aggiungono complessità senza valore aggiuntivo per l'MVP |
| Categorie target | Configurabili da dashboard | Permette modifiche senza redeploy; iniziali fornite da utente |
| Scheduling | Loop interno al worker (no cron esterno) | Semplifica deploy, debug, e single source of truth |
| Trigger time | 9:00 locali in ogni timezone configurato | Massimizza probabilità di risposta del lead |
| Dedup | Per `osm_id` (univoco e stabile) | Pattern "external ID as natural key" |
| Retry Overpass | Backoff esponenziale + mirror fallback | Overpass pubblica ha limiti e downtime occasionali |
| Phone normalization | Libreria `phonenumbers` → E.164 | Setting Agent richiede formato standard per chiamare |

### Categorie iniziali (decise dall'utente)

| Categoria | Tag OSM |
|---|---|
| Ristoranti | `amenity=restaurant` |
| Parrucchieri | `shop=hairdresser` |
| Estetiste | `shop=beauty` |
| Dentisti | `amenity=dentist` |
| Palestre | `leisure=fitness_centre` |
| Fotografi | `craft=photographer` |

---

## 3. Architettura di sistema

```
┌──────────────────────────────────────────────────┐
│  DASHBOARD (Next.js, esistente)                  │
│  └─ Nuova pagina /scraping-config                │
│       (CRUD scraping_targets)                    │
└────────────────────────┬─────────────────────────┘
                         │ INSERT/UPDATE
                         ▼
                  ┌──────────────┐
                  │   SUPABASE   │
                  │              │
                  │ • events     │
                  │ • leads      │ ← esteso (osm_id, category, city, lat/lng)
                  │ • scraping_  │ ← NUOVA
                  │   targets    │
                  │ • scraping_  │ ← NUOVA
                  │   runs       │
                  └──────┬───────┘
                         │ poll target_agent="scraping"
                         ▼
┌──────────────────────────────────────────────────┐
│  SCRAPING WORKER (Python, Railway)               │
│  ↳ Sostituisce scraping_stub                     │
│                                                   │
│  Loop interni concorrenti:                       │
│  ├─ _heartbeat_loop (ereditato da BaseAgent)     │
│  ├─ _poll_events    (ereditato — trigger manuali)│
│  └─ _scheduler_loop (NUOVO — controlla 9am TZ)   │
│                                                   │
│  Per ogni target attivo a 9am locale:            │
│    1. Costruisce query Overpass                  │
│    2. Chiama Overpass (rate limit 2 concurrent)  │
│    3. Normalizza numeri telefono                 │
│    4. Filtra dedup per osm_id                    │
│    5. INSERT in `leads`                          │
│    6. INSERT evento `scraping.lead_found`        │
└────────────────────────┬─────────────────────────┘
                         │ HTTPS
                         ▼
              ┌──────────────────────┐
              │  Overpass API         │
              │  overpass-api.de      │
              │  (con mirror fallback)│
              └──────────────────────┘
```

### Principi

- **Zero modifiche al Sub-progetto A**: stessa interfaccia eventi, stesso `BaseAgent`, stessa dashboard. Solo scraping_stub viene sostituito.
- **Scheduler interno al worker**: niente cron esterni, niente race conditions tra processi.
- **Idempotenza**: dedup per osm_id + check "già eseguito oggi" prima di triggerare.

---

## 4. Struttura del codice

### Modifiche e nuovi file

```
agents-platform/
├── apps/
│   ├── workers/
│   │   ├── scraping_stub/         # ← RIMOSSO
│   │   └── scraping_worker/        # ← NUOVO
│   │       ├── __init__.py
│   │       ├── main.py             # Entrypoint, ScrapingAgent
│   │       ├── overpass_client.py  # HTTP client per Overpass
│   │       ├── query_builder.py    # Costruisce query Overpass
│   │       ├── phone_normalizer.py # E.164 normalization
│   │       ├── scheduler.py        # Logic per "9am in TZ"
│   │       └── tests/
│   │           ├── test_query_builder.py
│   │           ├── test_phone_normalizer.py
│   │           ├── test_scheduler.py
│   │           ├── test_dedup.py
│   │           └── test_pipeline_integration.py
│   └── dashboard/
│       └── src/
│           ├── app/
│           │   ├── scraping-config/
│           │   │   └── page.tsx           # NUOVA pagina
│           │   └── api/scraping/
│           │       ├── targets/route.ts   # GET, POST
│           │       ├── targets/[id]/route.ts # PATCH, DELETE
│           │       └── run-now/route.ts   # POST trigger manuale
│           ├── components/scraping/
│           │   ├── AddTargetForm.tsx
│           │   ├── TargetsTable.tsx
│           │   ├── TargetRow.tsx
│           │   └── StatsBar.tsx
│           ├── hooks/
│           │   └── useScrapingTargets.ts  # CRUD + Realtime
│           └── lib/
│               ├── scraping-categories.ts # Lista categorie OSM
│               └── timezone-lookup.ts     # città → TZ
└── supabase/
    └── migrations/
        └── 003_scraping_targets.sql       # NUOVA migration
```

---

## 5. Componenti

### 5.1 `scraping_worker/main.py` — ScrapingAgent

Eredita da `BaseAgent`. Aggiunge `_scheduler_loop()` come terzo task in `start()`:

```python
async def start(self) -> None:
    self._running = True
    self._emitter.set_status("idle")
    self._emitter.send_heartbeat()
    self._emitter.emit("system.agent_online", {"agent_id": self.agent_id})
    await asyncio.gather(
        self._heartbeat_loop(),
        self._poll_events(),
        self._scheduler_loop(),  # NUOVO
    )
```

`handle_event()` gestisce due tipi di evento:
- `scraping.trigger` (manuale dalla dashboard) → esegue tutti i target attivi subito
- `scraping.run_target` (interno, generato dallo scheduler) → esegue un singolo target

### 5.2 `overpass_client.py`

```python
class OverpassClient:
    PRIMARY = "https://overpass-api.de/api/interpreter"
    MIRRORS = [
        "https://overpass.kumi.systems/api/interpreter",
        "https://overpass.private.coffee/api/interpreter",
    ]

    def __init__(self):
        self._semaphore = asyncio.Semaphore(2)
        self._current_endpoint = self.PRIMARY

    async def query(self, ql_query: str, max_retries: int = 3) -> list[dict]:
        """Esegue una query Overpass QL. Backoff esponenziale, mirror fallback."""
```

### 5.3 `query_builder.py`

```python
def build_no_website_query(category_type: str, category: str, city: str) -> str:
    """
    Costruisce query Overpass QL per attività SENZA sito web in una città.
    Esempio output:
        [out:json][timeout:60];
        area["name"="Milano"]["place"="city"]->.searchArea;
        (node["amenity"="restaurant"][!"website"]["phone"](area.searchArea););
        out body 100;
    """
```

### 5.4 `phone_normalizer.py`

```python
def normalize_phone(raw: str, country_code: str = "IT") -> str | None:
    """
    Normalizza numero a E.164 usando phonenumbers (libphonenumber).
    Gestisce:
      - Spazi, trattini, parentesi
      - Numeri multipli separati da / o ;
      - Prefisso internazionale o solo locale
    Ritorna None se numero non valido.
    """
```

### 5.5 `scheduler.py`

```python
class TimezoneScheduler:
    TRIGGER_HOUR = 9
    WINDOW_MINUTES = 5  # Tolleranza per "9:00"

    def get_targets_to_run(
        self, targets: list[Target], now_utc: datetime
    ) -> list[Target]:
        """Filtra i target che dovrebbero girare adesso."""
        # 1. Convert now_utc to target.timezone
        # 2. Check if hour == 9 and minute < 5
        # 3. Check if last_run_at is on a different LOCAL date
```

### 5.6 Dashboard `scraping-config/page.tsx`

Layout: Header → StatsBar → AddTargetForm → TargetsTable → Bulk actions

Componenti:
- **StatsBar**: 4 metriche (target attivi, lead oggi, prossimo run, run di oggi)
- **AddTargetForm**: dropdown categoria, input città, dropdown country, dropdown timezone (auto-suggerito), pulsante Add
- **TargetsTable**: lista target con toggle on/off, last run, leads count, delete

### 5.7 Hook `useScrapingTargets.ts`

```typescript
export function useScrapingTargets() {
  // Carica iniziale + subscribe Realtime su scraping_targets
  // Espone: targets, addTarget(), updateTarget(), deleteTarget(), runNow()
}
```

---

## 6. Data Model

### Migration `003_scraping_targets.sql`

```sql
-- Configurazione target di scraping
CREATE TABLE scraping_targets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    category TEXT NOT NULL,             -- es. "restaurant"
    category_type TEXT NOT NULL CHECK (category_type IN ('amenity','shop','craft','leisure','office')),
    city TEXT NOT NULL,
    country_code TEXT NOT NULL,         -- ISO-2: IT, FR, US
    timezone TEXT NOT NULL,             -- IANA: Europe/Rome
    enabled BOOLEAN NOT NULL DEFAULT true,
    last_run_at TIMESTAMPTZ,
    total_leads_found INT NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (category, city, country_code)
);

CREATE INDEX idx_targets_enabled ON scraping_targets(enabled, last_run_at);

-- Storico esecuzioni
CREATE TABLE scraping_runs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    target_id UUID NOT NULL REFERENCES scraping_targets(id) ON DELETE CASCADE,
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    status TEXT NOT NULL DEFAULT 'running' CHECK (status IN ('running','completed','failed')),
    leads_found INT NOT NULL DEFAULT 0,
    leads_new INT NOT NULL DEFAULT 0,
    error TEXT
);

CREATE INDEX idx_runs_target ON scraping_runs(target_id, started_at DESC);

-- Estendi leads (campi nullable, non distruttivo)
ALTER TABLE leads
    ADD COLUMN osm_id TEXT,
    ADD COLUMN category TEXT,
    ADD COLUMN city TEXT,
    ADD COLUMN country_code TEXT,
    ADD COLUMN latitude NUMERIC(9,6),
    ADD COLUMN longitude NUMERIC(9,6);

CREATE UNIQUE INDEX idx_leads_osm_id ON leads(osm_id) WHERE osm_id IS NOT NULL;

-- Realtime per dashboard
ALTER PUBLICATION supabase_realtime ADD TABLE scraping_targets;
ALTER PUBLICATION supabase_realtime ADD TABLE scraping_runs;
```

---

## 7. Data Flow

### Flusso scheduled (alle 9:00 locali)

```
1. Worker._scheduler_loop tick (ogni 60s)
   └─> Per ogni target enabled in scraping_targets:
       ├─ Calcola ora locale del target
       ├─ Se hour==9 && minute<5 && last_run_at non è oggi locale:
       │   └─> emit("scraping.run_target", {target_id})

2. Worker.handle_event("scraping.run_target")
   └─> Carica target da DB
   └─> INSERT scraping_runs (status='running')
   └─> Costruisce query Overpass (query_builder)
   └─> Chiama Overpass (overpass_client, semaphore)
   └─> Per ogni risultato:
       ├─ Normalizza phone (E.164)
       ├─ Skip se phone non valido
       ├─ Skip se osm_id già in leads
       ├─ INSERT in leads
       └─> emit("scraping.lead_found", {lead_id, lead, target_id})
   └─> UPDATE scraping_runs (status='completed', leads_found, leads_new)
   └─> UPDATE scraping_targets (last_run_at=now, total_leads_found+=N)

3. Setting agent (esistente) riceve scraping.lead_found
   └─> [pipeline esistente continua identica]
```

### Flusso trigger manuale

```
1. User clicca "Esegui ora" su scraping-config page
   └─> POST /api/scraping/run-now
       └─> INSERT events(type='scraping.trigger', target_agent='scraping')

2. Worker.handle_event("scraping.trigger")
   └─> Carica TUTTI i target enabled
   └─> Per ognuno: emit("scraping.run_target") (gestito come sopra)
```

---

## 8. Error Handling

### Rate limit Overpass (HTTP 429)

```python
async def query(self, ql_query: str):
    async with self._semaphore:  # max 2 concurrent
        for attempt in range(3):
            try:
                return await self._fetch(self._current_endpoint, ql_query)
            except RateLimitError:
                wait = 5 * (3 ** attempt)  # 5s, 15s, 45s
                await asyncio.sleep(wait)
            except EndpointDownError:
                self._switch_to_mirror()
        raise FatalError("Overpass unreachable after retries")
```

### FatalError → dead letter

Già gestito da `BaseAgent.process_event`:
- Marca evento `dead_letter`
- Aggiorna `scraping_runs.status = 'failed'` + `error`
- Emette `system.error` per dashboard

### Phone non valido

Skip silenzioso (logga warning). Il lead NON viene salvato — il Setting Agent ha bisogno di un telefono per chiamare.

### Città non trovata da Overpass

Overpass restituisce array vuoto se `area["name"="..."]` non matcha. Trattato come "0 lead trovati" (success, non errore).

---

## 9. Testing

### Unit tests

| File | Cosa testa |
|---|---|
| `test_query_builder.py` | Query OSM costruite correttamente per categorie/città |
| `test_phone_normalizer.py` | Numeri IT, FR, US, multipli, malformati |
| `test_scheduler.py` | Trigger giusto al timezone giusto, idempotenza |
| `test_dedup.py` | Skip se osm_id esiste, insert nuovo se no |

### Integration test

| File | Cosa testa |
|---|---|
| `test_pipeline_integration.py` | Mock Overpass → verifica lead in DB + eventi emessi |

Mock via `pytest-httpx`. Risposte JSON pre-registrate da query reali (catturate manualmente la prima volta).

### Comandi

```bash
# Unit
pytest apps/workers/scraping_worker/tests/ -v

# Integration
pytest apps/workers/scraping_worker/tests/test_pipeline_integration.py -v

# Tutti
pytest apps/workers/ -v
```

---

## 10. Deployment

### Dipendenze nuove (requirements.txt)

```
phonenumbers>=8.13
httpx>=0.28
```

### Migration Supabase

Lanciata via MCP `apply_migration` o `psql` con il file `003_scraping_targets.sql`.

### Railway

Il servizio `scraping-worker` esistente viene **rinominato** (o ricreato) con start command:
```
python -m apps.workers.scraping_worker.main
```

Env vars già presenti (SUPABASE_URL, SUPABASE_SERVICE_KEY) bastano. Nessuna chiave Google necessaria.

### Vercel (dashboard)

Auto-deploy on push. Le nuove API routes `/api/scraping/*` non richiedono env vars aggiuntive.

---

## 11. Schema eventi — modifiche

Aggiungere a `packages/events_schema/schemas/scraping.json`:

```json
"scraping.run_target": {
  "type": "object",
  "properties": {
    "target_id": { "type": "string" }
  },
  "required": ["target_id"]
}
```

Evento interno (worker → se stesso) generato dallo scheduler per processare un singolo target. NON usato dalla dashboard, ma definito nello schema per consistenza.

Lo schema TypeScript (`apps/dashboard/src/types/events.ts`) viene rigenerato eseguendo:
```bash
python packages/events_schema/generate.py
```

---

## 12. Vincoli e decisioni future

- **Lo `scraping_stub` viene rimosso** dal repo. Se serve testare senza Overpass, si può aggiungere un `OVERPASS_MOCK=1` env var che restituisce lead finti.
- **Categorie aggiuntive**: Sub-progetto B parte con 6 categorie. L'utente le aggiunge dalla UI quando vuole.
- **Query OSM più sofisticate** (es. fasce orarie, popolazione minima città, raggio km): rinviato a future iterazioni.
- **Multi-mirror Overpass automatico**: prima usa primario, switcha solo on error. Nessuna selezione round-robin.
- **Bulk import lead**: in scope futuro, per ora insert one-by-one.
