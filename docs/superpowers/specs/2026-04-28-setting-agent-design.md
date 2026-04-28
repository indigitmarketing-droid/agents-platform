# Sub-progetto D — Setting Agent (Voice MVP)

**Data**: 2026-04-28
**Stato**: Approvato
**Scope**: Sostituire `setting_stub` con un agente di vendita vocale reale. L'agente fa cold call a lead B2B (small businesses senza sito web) tramite ElevenLabs Conversational AI + Twilio, analizza il transcript con Claude, e triggera il Builder Agent quando il lead accetta la proposta. MVP focalizzato sul **mercato US** (test strategico) con limite **10 chiamate/giorno**.

---

## 1. Contesto

Sub-progetto D della piattaforma agenti AI. Sub-progetti A, B, C già live e funzionanti. Adesso sostituiamo `setting_stub` con un agente reale che:

- Riceve lead da `leads` table (popolata dallo Scraping Agent)
- Triggera chiamate vocali tramite ElevenLabs Conv AI + Twilio
- Riceve il transcript via webhook a fine chiamata
- Usa Claude per estrarre `outcome` (accepted/rejected/unclear) + `call_brief` (custom_requests, services, style_preference, ecc.)
- Emette `setting.call_accepted` (con call_brief) → triggera Builder
- Mantiene compliance light (do_not_call interno + business hours US)

Test market: **USA**. Decisione strategica dopo i primi risultati.

---

## 2. Decisioni architetturali

| Aspetto | Scelta | Motivazione |
|---|---|---|
| Provider voice | ElevenLabs Conversational AI (Creator €22/mese) | Account utente già configurato; qualità voice EN top-tier |
| Telephony | Twilio (account già attivo, US number `+16627075199`) | Standard SIP trunk integration con ElevenLabs |
| Rate limit MVP | **10 chiamate/giorno** | Cap per controllare costi e validare prima di scalare |
| Mercato test | **USA** (lingua inglese, lead in country_code='US') | Decisione strategica: voice EN ElevenLabs è più matura, mercato più grande, TCPA gestibile in light mode |
| Result extraction | Claude analyze su transcript completo | Pattern già usato in C v2; flessibile per outcome+brief estratto in un solo prompt |
| Scheduling | Batch giornaliero alle **10am ET**, FIFO | Semplice, prevedibile, business hours US standard |
| Compliance | LIGHT: skip RPO/DNC API, internal `do_not_call` | Adatto a 10/giorno; full compliance in fase 2 quando volumi giustificano integrazione DNC API |
| Tipi chiamata MVP | **Solo cold call** (1 agente) | Site-ready call deferred a fase 2 dopo validazione del cold call flow |
| Webhook receiver | `agents-dashboard` Vercel (`/api/webhooks/elevenlabs`) | Già ha SUPABASE_SERVICE_KEY, è il control plane naturale |
| Worker | `setting_agent` Python su Railway, sostituisce `setting_stub` | Stesso pattern degli altri agenti, eredita BaseAgent |

### Credenziali utente

| Cosa | Valore |
|---|---|
| ElevenLabs Agent ID | `agent_1101kq5kzfdqfqjvfwgn75v37cnp` |
| Twilio Phone Number | `+16627075199` |
| Twilio Account SID | `AC8e2563d616965772c92f17558e0ff545` |
| ElevenLabs API Key | (segreto, env var) |
| Twilio Auth Token | (segreto, env var) |
| ElevenLabs Webhook Secret | (segreto, configurato in ElevenLabs dashboard) |
| ElevenLabs Agent Phone Number ID | (UUID, ottenuto dopo configurazione Twilio in ElevenLabs dashboard) |

---

## 3. Architettura di sistema

```
┌──────────────────────────────────────────────────────┐
│  ELEVENLABS (cloud)                                  │
│  • Conv AI Agent: agent_1101kq5kzfdqfqjvfwgn75v37cnp │
│  • System prompt + voce + LLM gestiti da utente      │
└────────┬─────────────────────────────────────────────┘
         │ outbound SIP via Twilio
         ▼
┌──────────────────────────────────────────────────────┐
│  TWILIO (cloud)                                      │
│  • Account: AC8e2563...                              │
│  • Number: +16627075199                              │
└────────┬─────────────────────────────────────────────┘
         │ PSTN dial-out
         ▼
   📞 LEAD (US business)
         │ conversazione (ElevenLabs gestisce tutto)
         ▼
┌──────────────────────────────────────────────────────┐
│  ELEVENLABS termina → POST webhook                   │
└────────┬─────────────────────────────────────────────┘
         │ HTTPS POST con HMAC signature
         ▼
┌──────────────────────────────────────────────────────┐
│  AGENTS-DASHBOARD (Vercel — esistente)               │
│  NUOVO: /api/webhooks/elevenlabs                     │
│   1. Verify HMAC signature                           │
│   2. UPDATE call_logs                                │
│   3. INSERT events (setting.call_completed)          │
│   4. Dedup guard (evita doppia analisi)              │
└────────┬─────────────────────────────────────────────┘
         │ realtime
         ▼
┌──────────────────────────────────────────────────────┐
│  SUPABASE                                            │
│  • leads (esiste, esteso con call_status)            │
│  • events (esiste)                                   │
│  • call_logs (NUOVA)                                 │
│  • do_not_call (NUOVA)                               │
└────────┬─────────────────────────────────────────────┘
         │ poll
         ▼
┌──────────────────────────────────────────────────────┐
│  SETTING WORKER (Python, Railway)                    │
│  Sostituisce setting_stub                            │
│                                                       │
│  Loop concorrenti:                                   │
│  ├─ _heartbeat_loop (ereditato)                      │
│  ├─ _poll_events (ereditato)                         │
│  ├─ _scheduler_batch_loop  ← NUOVO                   │
│  └─ _orphan_cleanup_loop   ← NUOVO                   │
│                                                       │
│  Gestione eventi:                                    │
│  • setting.call_completed → Claude analyze →         │
│    emit accepted/rejected/unclear                    │
│  • builder.website_ready → log only (phase 2)        │
└──────────────────────────────────────────────────────┘
```

### Principi

- **Black box ElevenLabs**: tu gestisci prompt/voce/comportamento dell'agente nella loro dashboard. Il nostro codice non interviene durante la chiamata, solo prima (trigger) e dopo (analyze).
- **Pattern doppia evento per chiamata**: `setting.call_initiated` (al trigger) → `setting.call_completed` (dal webhook) → `setting.call_accepted/rejected/unclear` (dopo Claude).
- **Defensive denormalization**: `call_status`, `last_called_at`, `call_attempts` su `leads` permettono query veloci dello scheduler senza JOIN su call_logs.
- **Compliance audit trail**: ogni chiamata loggata in `call_logs` + eventi corrispondenti = dimostrabilità in caso di reclamo.

---

## 4. Struttura del codice

### Modifiche e nuovi file

```
agents-platform/
├── apps/
│   ├── workers/
│   │   ├── setting_stub/                # ← RIMOSSO
│   │   └── setting_agent/                # ← NUOVO
│   │       ├── __init__.py
│   │       ├── main.py                   # SettingAgent + entrypoint
│   │       ├── claude_client.py          # Anthropic SDK wrapper
│   │       ├── elevenlabs_client.py      # API wrapper outbound call
│   │       ├── lead_picker.py            # FIFO + DNC + cooldown
│   │       ├── transcript_analyzer.py    # Claude analyze → outcome+brief
│   │       ├── compliance.py             # US business hours check
│   │       └── tests/
│   │           ├── test_lead_picker.py
│   │           ├── test_compliance.py
│   │           ├── test_transcript_analyzer.py
│   │           ├── test_elevenlabs_client.py
│   │           └── test_pipeline_integration.py
│   └── dashboard/
│       └── src/
│           └── app/
│               └── api/
│                   └── webhooks/
│                       └── elevenlabs/
│                           └── route.ts   # POST handler con HMAC verify
├── packages/
│   └── events_schema/
│       └── schemas/
│           └── setting.json               # update: call_initiated, call_completed, call_failed
└── supabase/
    └── migrations/
        └── 006_call_logs.sql              # NUOVA
```

---

## 5. Componenti

### 5.1 SettingAgent (`main.py`)

Eredita `BaseAgent`. Aggiunge 2 task asyncio: `_scheduler_batch_loop` e `_orphan_cleanup_loop`.

```python
class SettingAgent(BaseAgent):
    SCHEDULER_TICK_SECONDS = 60
    BATCH_HOUR_LOCAL = 10
    BATCH_TIMEZONE = "America/New_York"
    DAILY_CALL_LIMIT = 10
    ORPHAN_CHECK_INTERVAL = 3600
    ORPHAN_THRESHOLD_MINUTES = 30

    def __init__(self, **kwargs):
        super().__init__(agent_id="setting", **kwargs)
        self._claude = create_anthropic_client()
        self._elevenlabs = create_elevenlabs_client()
        self._last_batch_date = None  # In-memory guard contro doppio run nello stesso giorno

    async def handle_event(self, event):
        if event.get("type") == "setting.call_completed":
            return await self._handle_call_completed(event)
        if event.get("type") == "builder.website_ready":
            logger.info("builder.website_ready received; site-ready call is phase 2")
            return []
        return []

    async def start(self):
        # Same as BaseAgent.start but adds 2 extra loops
        ...
        await asyncio.gather(
            self._heartbeat_loop(),
            self._poll_events(),
            self._scheduler_batch_loop(),
            self._orphan_cleanup_loop(),
        )
```

### 5.2 `lead_picker.py`

```python
def pick_leads_for_batch(supabase_client, limit: int = 10) -> list[dict]:
    """
    Select leads for cold calling.

    Filter:
      - call_status = 'never_called'
      - call_attempts < 3
      - has_website = false
      - country_code = 'US'
      - phone IS NOT NULL
      - phone NOT IN (SELECT phone FROM do_not_call)
      - last_called_at IS NULL OR last_called_at < NOW() - INTERVAL '24 hours'

    Order: FIFO by created_at.
    """
```

### 5.3 `compliance.py`

```python
US_BUSINESS_HOURS_START = 8   # 8am
US_BUSINESS_HOURS_END = 21     # 9pm
US_TIMEZONE = "America/New_York"

def is_within_business_hours(now_utc: datetime, tz: str = US_TIMEZONE) -> bool:
    """Check if it's currently within legal calling hours."""
    local = now_utc.astimezone(ZoneInfo(tz))
    if local.weekday() == 6:  # Sunday
        return False
    return US_BUSINESS_HOURS_START <= local.hour < US_BUSINESS_HOURS_END

def is_phone_in_dnc(phone: str, supabase_client) -> bool:
    """Check internal do_not_call table."""
    result = supabase_client.table("do_not_call").select("phone").eq("phone", phone).maybeSingle().execute()
    return result.data is not None
```

### 5.4 `elevenlabs_client.py`

```python
class ElevenLabsClient:
    BASE_URL = "https://api.elevenlabs.io/v1"

    def __init__(self, api_key: str):
        self._api_key = api_key

    def trigger_outbound_call(
        self,
        agent_id: str,
        agent_phone_number_id: str,
        to_number: str,
    ) -> dict:
        """
        POST /v1/convai/twilio/outbound_call
        Returns: {success, conversation_id, callSid}
        Raises: ElevenLabsError on HTTP error or success=false.
        """
        headers = {"xi-api-key": self._api_key, "Content-Type": "application/json"}
        body = {
            "agent_id": agent_id,
            "agent_phone_number_id": agent_phone_number_id,
            "to_number": to_number,
        }
        response = httpx.post(f"{self.BASE_URL}/convai/twilio/outbound_call", json=body, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()
        if not data.get("success"):
            raise ElevenLabsError(f"Outbound call failed: {data}")
        return data
```

### 5.5 `transcript_analyzer.py`

```python
def analyze_transcript(transcript: str, lead: dict, claude_client) -> dict:
    """
    Use Claude to extract from transcript:
      - outcome: 'accepted' | 'rejected' | 'unclear'
      - opt_out: bool
      - call_brief: dict (custom_requests, services, style_preference, etc.) — only if accepted

    Returns: {outcome, opt_out, call_brief}
    Raises: AnalysisError after 3 retries with malformed JSON.
    """
```

Prompt strutturato (in inglese per coerenza con conversation US):
```
You are analyzing a sales call transcript (English) for a website-rebuild service.
Lead: {lead.name}, {lead.category}, {lead.city}.

Extract:
1. outcome: "accepted" | "rejected" | "unclear"
   - accepted: lead agreed to receive a free website demo
   - rejected: lead declined / not interested
   - unclear: ambiguous, requires human review
2. opt_out: true if lead said "don't call again" or similar
3. call_brief (only if accepted, otherwise null):
   - custom_requests: specific things they asked
   - services: services they offer
   - style_preference: design preference (modern/classic/etc.)
   - target_audience: who they serve
   - opening_hours: if mentioned

Output ONLY valid JSON, no prose, no markdown.

Transcript:
{transcript}
```

### 5.6 Webhook receiver (Next.js)

`apps/dashboard/src/app/api/webhooks/elevenlabs/route.ts`:

```typescript
import { NextResponse } from "next/server";
import { createClient } from "@supabase/supabase-js";
import crypto from "crypto";

const WEBHOOK_SECRET = process.env.ELEVENLABS_WEBHOOK_SECRET!;
const supabase = createClient(process.env.SUPABASE_URL!, process.env.SUPABASE_SERVICE_KEY!);

function verifyHmac(body: string, signature: string | null): boolean {
  if (!signature) return false;
  const computed = crypto.createHmac("sha256", WEBHOOK_SECRET).update(body).digest("hex");
  return crypto.timingSafeEqual(Buffer.from(computed), Buffer.from(signature));
}

export async function POST(req: Request) {
  const body = await req.text();
  const signature = req.headers.get("x-elevenlabs-signature");
  if (!verifyHmac(body, signature)) {
    return NextResponse.json({error: "invalid signature"}, {status: 401});
  }

  const payload = JSON.parse(body);
  const { conversation_id, status, transcript, duration_seconds, audio_url } = payload;

  // Dedupe guard
  const existing = await supabase
    .from("events")
    .select("id")
    .eq("type", "setting.call_completed")
    .filter("payload->>conversation_id", "eq", conversation_id)
    .maybeSingle();
  if (existing.data) {
    return NextResponse.json({ok: true, deduped: true});
  }

  // UPDATE call_logs
  const { data: callLog } = await supabase
    .from("call_logs")
    .update({
      status: "completed",
      transcript,
      duration_seconds,
      audio_url,
      ended_at: new Date().toISOString(),
    })
    .eq("conversation_id", conversation_id)
    .select("lead_id")
    .single();

  if (!callLog) {
    return NextResponse.json({error: "call_log not found"}, {status: 404});
  }

  // INSERT event
  await supabase.from("events").insert({
    type: "setting.call_completed",
    source_agent: "dashboard",
    target_agent: "setting",
    payload: {
      lead_id: callLog.lead_id,
      conversation_id,
      transcript,
      duration_seconds,
      audio_url,
    },
    status: "pending",
  });

  return NextResponse.json({ok: true});
}
```

---

## 6. Data Model

### Migration `006_call_logs.sql`

```sql
-- 006_call_logs.sql

CREATE TABLE call_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    lead_id UUID NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
    call_type TEXT NOT NULL CHECK (call_type IN ('cold_call', 'site_ready_call')),
    agent_id TEXT NOT NULL,
    call_sid TEXT,
    conversation_id TEXT,
    phone TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'initiated'
        CHECK (status IN ('initiated', 'in_progress', 'completed', 'failed', 'no_answer', 'busy')),
    outcome TEXT CHECK (outcome IN ('accepted', 'rejected', 'unclear')),
    transcript TEXT,
    duration_seconds INT,
    audio_url TEXT,
    call_brief JSONB,
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    ended_at TIMESTAMPTZ,
    analyzed_at TIMESTAMPTZ,
    error TEXT
);

CREATE INDEX idx_call_logs_lead ON call_logs(lead_id, started_at DESC);
CREATE INDEX idx_call_logs_status ON call_logs(status);
CREATE INDEX idx_call_logs_call_sid ON call_logs(call_sid) WHERE call_sid IS NOT NULL;
CREATE INDEX idx_call_logs_conversation ON call_logs(conversation_id) WHERE conversation_id IS NOT NULL;

CREATE TABLE do_not_call (
    phone TEXT PRIMARY KEY,
    reason TEXT NOT NULL CHECK (reason IN ('lead_request', 'manual', 'invalid_number', 'dnc_api_match', 'max_attempts')),
    added_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    notes TEXT
);

ALTER TABLE leads
    ADD COLUMN call_status TEXT NOT NULL DEFAULT 'never_called'
        CHECK (call_status IN ('never_called','called','accepted','rejected','do_not_call')),
    ADD COLUMN last_called_at TIMESTAMPTZ,
    ADD COLUMN call_attempts INT NOT NULL DEFAULT 0;

CREATE INDEX idx_leads_call_status ON leads(call_status, last_called_at);

ALTER PUBLICATION supabase_realtime ADD TABLE call_logs;
ALTER PUBLICATION supabase_realtime ADD TABLE do_not_call;
```

### Schema events update

`packages/events_schema/schemas/setting.json` aggiornato:

```json
"setting.call_initiated": {
  "type": "object",
  "properties": {
    "lead_id": { "type": "string" },
    "call_sid": { "type": "string" },
    "call_type": { "type": "string", "enum": ["cold_call", "site_ready_call"] }
  },
  "required": ["lead_id", "call_sid", "call_type"]
},
"setting.call_completed": {
  "type": "object",
  "properties": {
    "lead_id": { "type": "string" },
    "conversation_id": { "type": "string" },
    "transcript": { "type": "string" },
    "duration_seconds": { "type": "integer" },
    "audio_url": { "type": "string" }
  },
  "required": ["lead_id", "conversation_id", "transcript"]
},
"setting.call_failed": {
  "type": "object",
  "properties": {
    "lead_id": { "type": "string" },
    "reason": { "type": "string" },
    "call_sid": { "type": "string" }
  },
  "required": ["lead_id", "reason"]
}
```

`setting.call_accepted` (esistente) — aggiornato per includere `call_brief` opzionale (compatibility con C v2).

---

## 7. Data Flow

### State machines

**Lead state**:
```
never_called → called → accepted | rejected | do_not_call
                ↑                         ↓
                └──── retry within ──────┘
                      24h window
                      if call_attempts < 3
```

**Call state (call_logs)**:
```
initiated → completed → outcome set (accepted/rejected/unclear)
   │
   ├──► failed (technical error)
   ├──► no_answer
   └──► busy
```

### Flusso 1 — Batch giornaliero (10am ET)

```
1. _scheduler_batch_loop tick (every 60s)
   └─> Check: today's date != self._last_batch_date
   └─> Check: ora ET == 10:00 ± 5 min
   └─> Check: business hours OK
   └─> All true → procedi

2. lead_picker.pick_leads_for_batch(limit=10)
   → returns up to 10 leads matching filter

3. self._last_batch_date = today

4. Per ogni lead:
   a. is_phone_in_dnc(lead.phone)? → skip if yes
   b. INSERT call_logs (lead_id, call_type='cold_call', agent_id, phone, status='initiated')
   c. UPDATE leads SET call_status='called', last_called_at=NOW(), call_attempts++
   d. try:
        result = elevenlabs.trigger_outbound_call(agent_id, agent_phone_number_id, lead.phone)
        UPDATE call_logs SET conversation_id=result.conversation_id, call_sid=result.call_sid
        emit('setting.call_initiated', {lead_id, call_sid: result.call_sid, call_type: 'cold_call'})
      except ElevenLabsError as e:
        UPDATE call_logs SET status='failed', error=str(e)
        UPDATE leads SET call_status='never_called' (revert; call_attempts già incrementato resta)
        emit('setting.call_failed', {lead_id, reason: str(e)})
        continue (next lead)
```

### Flusso 2 — Webhook arriva

(vedi codice route.ts in 5.6)

### Flusso 3 — Worker analizza

```
1. _poll_events vede 'setting.call_completed'
2. Load call_logs WHERE conversation_id = ?
3. Load lead WHERE id = ?
4. Claude analyze_transcript → {outcome, opt_out, call_brief}
5. UPDATE call_logs SET outcome, call_brief, analyzed_at=NOW()
6. UPDATE leads SET call_status = outcome (or 'do_not_call' if opt_out)
7. If opt_out: INSERT do_not_call (phone, reason='lead_request')
8. Emit:
   - 'accepted' → setting.call_accepted (target='builder', payload={lead_id, lead, call_brief})
   - 'rejected' → setting.call_rejected (no target, just log)
   - 'unclear' → setting.call_unclear (manual review needed)
```

### Flusso 4 — Orphan cleanup

```
Every hour:
1. Find call_logs WHERE status='initiated' AND started_at < NOW() - 30min
2. Per ogni orphan:
   a. Try elevenlabs.get_conversation(conversation_id)
   b. Se conv.status='done' e transcript presente:
      → simula webhook (UPDATE call_logs + INSERT event setting.call_completed)
   c. Se conv.status in ('failed', 'no_answer', 'busy'):
      → UPDATE call_logs SET status=conv.status
      → UPDATE leads SET call_status='never_called' (per retry)
   d. Se conv non esiste / errore API:
      → log warning, lascia orphan (verrà riprovato next hour)
```

---

## 8. Error Handling

### Errori al trigger
Se `elevenlabs.trigger_outbound_call()` fallisce: UPDATE call_logs status='failed', revert lead.call_status='never_called', emit `setting.call_failed`, continua col prossimo lead.

### Webhook orfani
`_orphan_cleanup_loop` riconcilia chiamate stuck in 'initiated' >30min via API ElevenLabs.

### Retry policy
| Outcome | Lead next state | Re-batch? |
|---|---|---|
| accepted | accepted | mai più |
| rejected | rejected | mai più |
| unclear | never_called (attempts++) | domani |
| no_answer | never_called (attempts++) | dopo 24h cooldown |
| busy | never_called (attempts++) | dopo 24h cooldown |
| failed | never_called (attempts++) | dopo 24h cooldown |
| call_attempts >= 3 | do_not_call (reason='max_attempts') | mai più |

### Idempotenza webhook
Dedupe guard nel route.ts: prima dell'INSERT events, check se già esiste un evento `setting.call_completed` con stesso `conversation_id` nel payload. Se sì, return 200 senza re-process.

### Compliance audit
- Ogni chiamata loggata in `call_logs` con timestamp, transcript, durata
- `do_not_call` table mantiene opt-out permanenti
- `call_attempts` previene spam involontario

### Errori Claude (transcript_analyzer)
3 retry su JSON malformato. Dopo 3 fallimenti: marca call_logs.outcome='unclear', emit `setting.call_unclear` per review manuale (non blocchiamo il pipeline).

---

## 9. Testing

### Unit tests Python

| File | Cosa testa |
|---|---|
| `test_lead_picker.py` | Filter FIFO, exclusion DNC, attempts<3, 24h cooldown, country_code='US' |
| `test_compliance.py` | Business hours US (8-21 ET), Sunday skip, weekday detection |
| `test_transcript_analyzer.py` | Mock Claude, parsing outcome, opt_out detection, call_brief estratto |
| `test_elevenlabs_client.py` | Mock httpx, payload format, error handling |
| `test_pipeline_integration.py` | E2E con mock: batch tick → leads picked → trigger calls → webhook → analyze → emit accepted |

### Webhook test (vitest in dashboard)

| Test | Cosa verifica |
|---|---|
| `route.test.ts` | HMAC verify pass/fail, dedupe duplicate events, UPDATE call_logs + INSERT events |

### E2E manuale post-deploy

1. INSERT lead nel DB con tuo numero + email + country_code='US'
2. Trigger manuale del batch (o aspetta 10am ET)
3. Verifica:
   - Telefonata arriva
   - Agente parla, tu rispondi "yes"
   - Riagganci
4. Verifica DB: `call_logs` completed, transcript ok, eventi accepted, lead.call_status='accepted', site generato dal Builder

---

## 10. Deployment

### Migration Supabase
`006_call_logs.sql` applicata via Supabase MCP.

### Railway: sostituzione setting_stub

1. Push codice nuovo (`apps/workers/setting_agent/`)
2. Update start command Railway service `setting-worker`:
   `python -m apps.workers.setting_stub.main` → `python -m apps.workers.setting_agent.main`
3. Aggiungi env vars al servizio:
   - `ANTHROPIC_API_KEY` (per Claude analyze)
   - `ELEVENLABS_API_KEY` (segreto da dashboard ElevenLabs)
   - `ELEVENLABS_AGENT_ID = agent_1101kq5kzfdqfqjvfwgn75v37cnp`
   - `ELEVENLABS_AGENT_PHONE_NUMBER_ID` (UUID interno ElevenLabs, ottenuto dopo configurazione Twilio nella loro dashboard)
   - `TWILIO_ACCOUNT_SID = AC8e2563d616965772c92f17558e0ff545`
   - `TWILIO_AUTH_TOKEN` (segreto)
   - `TWILIO_PHONE_NUMBER = +16627075199`

### Vercel agents-dashboard: webhook env vars
Aggiungi:
- `ELEVENLABS_WEBHOOK_SECRET` (lo configuri in ElevenLabs dashboard sotto webhook → ti dà signing secret)

### ElevenLabs dashboard setup

1. Conv AI → tuo agente → Phone Numbers → Connect Twilio:
   - Inserisci Account SID + Auth Token + Phone Number `+16627075199`
   - Salva → ElevenLabs ti restituisce un `agent_phone_number_id` (UUID)
   - Copia → Railway env var
2. Conv AI → tuo agente → Webhooks (o Conversation events):
   - URL: `https://agents-dashboard-theta.vercel.app/api/webhooks/elevenlabs`
   - Events: `conversation.ended`
   - Copia signing secret → Vercel env var

### Dipendenze nuove

**Python (`requirements.txt`)**:
```
twilio>=9.0   # per fallback/admin se serve
```
ElevenLabs lo chiamiamo via httpx puro (già installato).

### Dashboard "Calls" panel (opzionale, fase 2)

Pagina `/calls` nella dashboard agents-dashboard che mostra:
- Counter chiamate oggi/settimana
- Outcome breakdown (accepted/rejected/unclear %)
- Lista ultime 20 chiamate con transcript link
- Counter lead in DNC

Non bloccante per il MVP, lo aggiungiamo dopo la prima validazione.

---

## 11. Vincoli e decisioni future

- **Site-ready call (phase 2)**: secondo agente ElevenLabs per chiamare il lead quando il Builder ha completato il sito. Trigger su `builder.website_ready`.
- **WhatsApp follow-up (Sub-progetto D2)**: messaggi cadenzati a 1d/15d/30d. Richiede WhatsApp Business API + template approval Meta.
- **Compliance full**: integrare DNC API ufficiale USA + state-specific compliance + call recording disclosure obbligatoria.
- **Pivot Italia**: se il test US non dà risultati, switch a IT richiede solo cambio voce ElevenLabs + numero Twilio italiano + traduzione prompt analyzer + compliance RPO.
- **Multi-lingua**: per supportare entrambi mercati simultaneamente, il prompt analyzer e il system prompt agente devono diventare language-aware.
- **Re-call dopo X giorni**: per "unclear" outcome, ora aspettiamo 24h. In futuro: schedulare re-call esplicitamente con delay configurabile.
- **Smart timing**: chiamare specifiche categorie a orari ottimali (es. ristoranti dopo le 14:00). Non in MVP.
- **Cap dinamico**: invece di 10/giorno fisso, scalare in base a outcome positivi (es. 20/giorno se conversion > 30%). Logica futura.
