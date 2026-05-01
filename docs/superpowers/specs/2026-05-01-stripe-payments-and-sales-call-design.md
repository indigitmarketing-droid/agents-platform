# Sub-progetti F1 (Stripe Payments) + D-Phase2 (Sales Call) — Design

**Data**: 2026-05-01
**Stato**: Design approvato dall'utente. Plan + execution pending (sessione successiva).
**Sub-progetti**: F1 + D-Phase2 (bundled, tightly coupled)

---

## 1. Contesto e scope

**Bundling rationale**: D-Phase2 vende il sito ($349) → F1 riceve il pagamento → completa l'onboarding cliente. I due sub-progetti formano la pipeline di monetizzazione completa. Implementarli separatamente significherebbe avere F1 senza trigger e D-Phase2 senza outcome.

### Goals

- **D-Phase2**: secondo agente ElevenLabs Conv AI che chiama lead post-Builder con prompt "vendita" — conferma interesse, vende $349, manda link via SMS
- **F1**: Stripe Checkout one-time payment + webhook handler + cleanup cron 48h grace + auto-onboarding (auth.user + welcome email post-pagamento)

### Non-goals (deferred)

- ❌ WhatsApp delivery del link → **F2** (gated da Twilio Business approval Meta)
- ❌ Refund automatico → operatore manuale via Stripe dashboard, F1.1 future
- ❌ Stripe Tax automatic → MVP minimum compliance ($349 inclusivo, gestione fiscale offline)
- ❌ Subscription / recurring billing → modello $349 una tantum, no rinnovi
- ❌ Multi-currency → solo USD per test market USA

---

## 2. Architettura end-to-end

```
Builder finisce sito (esistente, no modifiche in D-Phase2/F1)
   ↓ INSERT sites (payment_status='unpaid', published_at=NOW())
   ↓ emit builder.site_ready (target=setting)
   ↓
Setting Agent / D-Phase2 _handle_site_ready:
   ↓ Uses SECOND ElevenLabs agent (ELEVENLABS_SALES_AGENT_ID, sales prompt)
   ↓ trigger_outbound_call(stesso lead, stesso numero Twilio, agent_id=sales)
   ↓ INSERT call_logs(call_type='sales', status='initiated')
   ↓ UPDATE sites SET sales_call_attempts++, last_sales_call_at=NOW()
   ↓ emit setting.sales_call_initiated
   ↓
[Telefonata]
   ↓ Call ends → webhook ElevenLabs → /api/webhooks/elevenlabs
   ↓ INSERT setting.sales_call_completed event (target=setting)
   ↓
Setting Agent _handle_sales_call_completed:
   ↓ Claude analyze transcript con sales-specific prompt
   ↓ outcome = 'accepted_pay' | 'interested_no_call' | 'rejected' | 'no_answer' | 'busy' | 'unclear'
   ↓
   ┌─ accepted_pay or interested_no_call:
   │    create_stripe_checkout(site, lead) → checkout_url + session_id
   │    UPDATE sites SET stripe_checkout_session_id=...
   │    send_sms(lead.phone, "Ecco il link: <checkout_url>")
   │    emit setting.payment_link_sent
   ├─ rejected:
   │    DELETE sites WHERE id=site_id (no aspetta 48h)
   │    INSERT do_not_call (compliance)
   │    emit site.deleted_unpaid (reason='rejected')
   ├─ no_answer / busy:
   │    no action — scheduler retry next batch (max 3 attempts)
   ├─ unclear:
   │    no action — retry next batch
   ↓

[Cliente clicca link SMS]
   ↓ Stripe Checkout (UI Stripe-hosted, sicuro)
   ↓ Customer paga con carta
   ↓
Stripe webhook payment.succeeded → /api/webhooks/stripe (Vercel agents-dashboard)
   ↓ Verifica HMAC Stripe (webhook signing secret)
   ↓ Dedupe via stripe_events.stripe_event_id UNIQUE
   ↓ Per checkout.session.completed:
     1. UPDATE sites SET payment_status='paid', paid_at=NOW(), stripe_payment_intent_id, stripe_customer_id
     2. CREATE auth.user via Supabase admin con metadata
     3. UPDATE sites.owner_user_id
     4. Send welcome email (Resend) con dashboard credentials
     5. INSERT customer.onboarded event
   ↓
Cliente clicca link in welcome email → E1 customer-dashboard login (✅ già live)
   ↓ Force password change → dashboard home

Parallelamente: Cleanup cron Vercel (every hour, 0 * * * *)
   ↓ /api/cron/cleanup-unpaid-sites (auth via CRON_SECRET)
   ↓ DELETE FROM sites WHERE payment_status='unpaid' AND published_at < NOW() - 48h
   ↓ UPDATE leads SET status='expired_no_pay' for those leads
   ↓ emit site.deleted_unpaid event per each
```

### Punti architetturali chiave

1. **Secondo agente ElevenLabs** (`ELEVENLABS_SALES_AGENT_ID`) — stesso codice infra di D-Phase1, solo prompt diverso ("vendita" vs "qualifica"). Stesso numero Twilio outbound (+16627075199).

2. **Stripe webhook handler in agents-dashboard Vercel** — pattern identico a `/api/webhooks/elevenlabs`: HMAC verify, dedupe, INSERT event, UPDATE row, emit follow-up event. Usa `Stripe.webhooks.constructEvent` per HMAC verification (NO custom code).

3. **Cleanup cron via Vercel Cron Jobs** — non Railway worker. Ragione: cron orario di poche righe SQL non merita un worker dedicato. `vercel.json` declarative + 1 endpoint = zero ops overhead.

4. **Idempotency by design** — Stripe re-invia webhook fino a 3 giorni se 4xx/5xx. Dedupe via `stripe_events.stripe_event_id UNIQUE` previene double-process. Tutte le UPDATE usano clausole `WHERE` che le rendono idempotenti.

---

## 3. Data model

### Migration: `008_payment_flow.sql`

```sql
-- 008_payment_flow.sql
-- F1 (Stripe payments) + D-Phase2 (sales call) tracking

-- 1. Stripe-specific fields su sites
ALTER TABLE sites ADD COLUMN stripe_checkout_session_id TEXT;
ALTER TABLE sites ADD COLUMN stripe_payment_intent_id TEXT;
ALTER TABLE sites ADD COLUMN stripe_customer_id TEXT;
ALTER TABLE sites ADD COLUMN paid_at TIMESTAMPTZ;
CREATE INDEX idx_sites_stripe_session ON sites(stripe_checkout_session_id);
CREATE INDEX idx_sites_stripe_pi ON sites(stripe_payment_intent_id);

-- 2. D-Phase2 retry tracking
ALTER TABLE sites ADD COLUMN sales_call_attempts INT DEFAULT 0;
ALTER TABLE sites ADD COLUMN last_sales_call_at TIMESTAMPTZ;
ALTER TABLE sites ADD COLUMN sales_call_outcome TEXT
  CHECK (sales_call_outcome IS NULL OR sales_call_outcome IN
    ('accepted_pay', 'interested_no_call', 'rejected', 'no_answer', 'busy', 'unclear'));

-- 3. Stripe events table (audit + dedupe + replay)
CREATE TABLE stripe_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    stripe_event_id TEXT UNIQUE NOT NULL,
    event_type TEXT NOT NULL,
    payload JSONB NOT NULL,
    site_id UUID REFERENCES sites(id) ON DELETE SET NULL,
    processed_at TIMESTAMPTZ,
    error TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_stripe_events_type ON stripe_events(event_type, created_at DESC);
CREATE INDEX idx_stripe_events_site ON stripe_events(site_id);
```

### Nuovi event types (events table)

| Type | Source | Target | Payload chiave |
|---|---|---|---|
| `builder.site_ready` | builder | setting | `{lead_id, site_id, slug, phone}` |
| `setting.sales_call_initiated` | setting | null | `{lead_id, site_id, call_sid, agent_id}` |
| `setting.sales_call_completed` | setting | null | `{lead_id, site_id, outcome, transcript_excerpt}` |
| `setting.payment_link_sent` | setting | null | `{site_id, channel='sms', stripe_session_id}` |
| `customer.onboarded` | dashboard | null | `{site_id, auth_user_id, email_sent, paid_at}` |
| `site.deleted_unpaid` | cron \| setting | null | `{site_id, slug, reason='48h_grace_expired' \| 'rejected'}` |

### State machine sites

```
unpaid (just published, 48h grace started)
  ↓
  ├─→ sales_call_attempts=1..3 (D-Phase2 attempts)
  │     ↓ accepted_pay → SMS sent, stripe_checkout_session_id populated, waiting for payment
  │     ↓ interested_no_call → SMS sent (same as accepted_pay technically)
  │     ↓ rejected → DELETE site immediately + DNC compliance
  │     ↓ no_answer/busy/unclear → retry next day (max 3)
  ↓
  ├─→ Stripe payment.succeeded → payment_status='paid', paid_at=NOW(),
  │      owner_user_id (post auth.user create), site permanente
  ↓
  └─→ 48h elapsed without payment → cleanup cron DELETE site, lead.status='expired_no_pay'
```

### Auth.users metadata (post-payment)

```typescript
{
  lead_id: "uuid",
  site_id: "uuid",
  company_name: "string",
  password_changed: false,
  onboarded_at: "ISO 8601",
  stripe_customer_id: "cus_...",
  paid_at: "ISO 8601"
}
```

### Idempotency design

| Step | Strategy |
|---|---|
| Stripe webhook delivery | Stripe retry 3 days. Dedupe via `stripe_events.stripe_event_id UNIQUE` |
| `auth.admin.create_user` | Already idempotent (existing user → return existing id) |
| UPDATE site payment_status | `WHERE payment_status='unpaid'` clause prevents double-update |
| Send welcome email | Check existing `customer.onboarded` event for site_id |
| Cleanup cron | Multiple runs safe — only deletes still-unpaid past grace |

---

## 4. Componenti

### A) Stripe webhook handler (Vercel)

`apps/dashboard/src/app/api/webhooks/stripe/route.ts`:

```typescript
import { NextResponse } from "next/server";
import Stripe from "stripe";
import { createClient, type SupabaseClient } from "@supabase/supabase-js";

const stripe = new Stripe(process.env.STRIPE_SECRET_KEY!);
const webhookSecret = process.env.STRIPE_WEBHOOK_SECRET!;
const supabaseUrl = process.env.SUPABASE_URL!;
const supabaseServiceKey = process.env.SUPABASE_SERVICE_KEY!;

export async function POST(req: Request) {
  const body = await req.text();
  const signature = req.headers.get("stripe-signature");

  let event: Stripe.Event;
  try {
    event = stripe.webhooks.constructEvent(body, signature!, webhookSecret);
  } catch {
    return NextResponse.json({ error: "invalid signature" }, { status: 401 });
  }

  const supabase = createClient(supabaseUrl, supabaseServiceKey);

  // Dedupe
  const { data: existing } = await supabase
    .from("stripe_events").select("id")
    .eq("stripe_event_id", event.id).maybeSingle();
  if (existing) return NextResponse.json({ ok: true, deduped: true });

  // Audit insert
  await supabase.from("stripe_events").insert({
    stripe_event_id: event.id,
    event_type: event.type,
    payload: event.data,
  });

  if (event.type === "checkout.session.completed") {
    return await handleCheckoutCompleted(
      event.data.object as Stripe.Checkout.Session, event.id, supabase);
  }
  if (event.type === "charge.refunded") {
    return NextResponse.json({ ok: true, deferred: "F1.1 refund handler" });
  }
  return NextResponse.json({ ok: true, ignored: event.type });
}

async function handleCheckoutCompleted(
  session: Stripe.Checkout.Session,
  eventId: string,
  supabase: SupabaseClient,
) {
  const siteId = session.metadata?.site_id;
  if (!siteId) {
    return NextResponse.json({ error: "no site_id metadata" }, { status: 400 });
  }

  // 1. UPDATE site payment_status='paid'
  const { data: site } = await supabase
    .from("sites").update({
      payment_status: "paid",
      paid_at: new Date().toISOString(),
      stripe_payment_intent_id: session.payment_intent as string,
      stripe_customer_id: session.customer as string,
    })
    .eq("id", siteId)
    .eq("payment_status", "unpaid")  // idempotency guard
    .select("*, leads!inner(*)")
    .maybeSingle();

  if (!site) {
    // Either site not found or already paid — both OK
    return NextResponse.json({ ok: true, already_processed: true });
  }

  const lead = site.leads;
  if (!lead?.email) {
    return NextResponse.json({ error: "lead has no email" }, { status: 400 });
  }

  // 2. CREATE auth.user
  const password = generateRandomPassword();
  const { data: { user }, error: createErr } =
    await supabase.auth.admin.createUser({
      email: lead.email,
      password,
      email_confirm: true,
      user_metadata: {
        lead_id: lead.id,
        site_id: siteId,
        company_name: lead.company_name,
        password_changed: false,
        onboarded_at: new Date().toISOString(),
        stripe_customer_id: session.customer,
        paid_at: new Date().toISOString(),
      },
    });

  // Handle existing user (idempotent)
  let authUserId = user?.id;
  if (createErr && createErr.message.includes("already registered")) {
    const { data: existing } = await supabase.auth.admin
      .listUsers({ page: 1, perPage: 1, /* filter by email — manual loop */ });
    authUserId = existing?.users.find((u) => u.email === lead.email)?.id;
  }

  if (!authUserId) {
    return NextResponse.json({ error: "user creation failed" }, { status: 500 });
  }

  // 3. UPDATE site.owner_user_id
  await supabase.from("sites").update({ owner_user_id: authUserId }).eq("id", siteId);

  // 4. Send welcome email
  await sendWelcomeEmail({ lead, site, password });

  // 5. Mark stripe_event processed + emit customer.onboarded
  await supabase.from("stripe_events").update({
    processed_at: new Date().toISOString(),
    site_id: siteId,
  }).eq("stripe_event_id", eventId);

  await supabase.from("events").insert({
    type: "customer.onboarded",
    source_agent: "dashboard",
    payload: {
      site_id: siteId,
      auth_user_id: authUserId,
      email: lead.email,
      paid_at: new Date().toISOString(),
    },
  });

  return NextResponse.json({ ok: true, onboarded: authUserId });
}
```

### B) Setting Agent / D-Phase2 extension

In `apps/workers/setting_agent/main.py`:

```python
MAX_SALES_CALL_ATTEMPTS = 3

async def handle_event(self, event: dict) -> list[dict]:
    event_type = event.get("type", "")
    if event_type == "setting.call_completed":
        return await self._handle_call_completed(event)
    if event_type == "setting.force_call":
        return await self._handle_force_call(event)
    if event_type == "builder.site_ready":   # NEW
        return await self._handle_site_ready(event)
    if event_type == "setting.sales_call_completed":   # NEW
        return await self._handle_sales_call_completed(event)
    return []

async def _handle_site_ready(self, event: dict) -> list[dict]:
    """D-Phase2 trigger: site is built, call lead to sell."""
    payload = event["payload"]
    site_id = payload["site_id"]
    lead_id = payload["lead_id"]

    site = self._load_site(site_id)
    lead = self._load_lead(lead_id)
    if not site or not lead or not lead.get("phone"):
        return []

    attempts = site.get("sales_call_attempts", 0)
    if attempts >= MAX_SALES_CALL_ATTEMPTS:
        logger.warning(f"Max sales call attempts ({MAX_SALES_CALL_ATTEMPTS}) reached for site {site_id}")
        return []

    # Check business hours, DNC, etc. (riusa logica esistente)
    if is_phone_in_dnc(lead["phone"], self._client):
        return []

    sales_agent_id = os.environ["ELEVENLABS_SALES_AGENT_ID"]
    try:
        result = self._elevenlabs.trigger_outbound_call(
            agent_id=sales_agent_id,
            agent_phone_number_id=self._agent_phone_id,
            to_number=lead["phone"],
        )
    except ElevenLabsError as e:
        logger.error(f"Sales call trigger failed for site {site_id}: {e}")
        return [{"type": "setting.sales_call_failed", "payload": {"site_id": site_id, "reason": str(e)}}]

    # UPDATE sites tracking
    self._client.table("sites").update({
        "sales_call_attempts": attempts + 1,
        "last_sales_call_at": datetime.now(timezone.utc).isoformat(),
    }).eq("id", site_id).execute()

    # INSERT call_logs (call_type='sales')
    self._client.table("call_logs").insert({
        "lead_id": lead_id,
        "call_type": "sales",
        "agent_id": sales_agent_id,
        "phone": lead["phone"],
        "status": "initiated",
        "conversation_id": result.get("conversation_id"),
        "call_sid": result.get("callSid") or result.get("call_sid"),
    }).execute()

    return [{
        "type": "setting.sales_call_initiated",
        "target_agent": None,
        "payload": {
            "lead_id": lead_id,
            "site_id": site_id,
            "call_sid": result.get("callSid") or result.get("call_sid"),
            "agent_id": sales_agent_id,
        },
    }]


async def _handle_sales_call_completed(self, event: dict) -> list[dict]:
    """Process sales call transcript, send Stripe link if accepted."""
    payload = event["payload"]
    site_id = payload["site_id"]
    transcript = payload["transcript"]

    site = self._load_site(site_id)
    if not site:
        return []
    lead = self._load_lead(site["lead_id"])

    try:
        analysis = analyze_sales_transcript(transcript, lead, self._claude)
    except AnalysisError:
        outcome = "unclear"
    else:
        outcome = analysis["outcome"]

    self._client.table("sites").update({"sales_call_outcome": outcome}).eq("id", site_id).execute()

    if outcome in ("accepted_pay", "interested_no_call"):
        try:
            checkout_url, session_id = create_stripe_checkout(site, lead)
        except Exception as e:
            logger.error(f"Stripe checkout creation failed for site {site_id}: {e}")
            return []
        # Save session_id on site
        self._client.table("sites").update({
            "stripe_checkout_session_id": session_id,
        }).eq("id", site_id).execute()
        # Send SMS via Twilio
        try:
            send_sms(
                to=lead["phone"],
                body=f"Hi {lead['company_name']}, here's your link to activate your website ($349): {checkout_url}",
            )
        except Exception as e:
            logger.error(f"SMS send failed: {e}")
        return [{
            "type": "setting.payment_link_sent",
            "payload": {
                "site_id": site_id,
                "stripe_session_id": session_id,
                "channel": "sms",
                "phone": lead["phone"],
            },
        }]

    if outcome == "rejected":
        # Delete site immediately + DNC
        self._client.table("sites").delete().eq("id", site_id).execute()
        self._client.table("do_not_call").insert({
            "phone": lead["phone"],
            "reason": "sales_call_rejected",
        }).execute()
        return [{
            "type": "site.deleted_unpaid",
            "payload": {"site_id": site_id, "slug": site.get("slug"), "reason": "rejected"},
        }]

    # no_answer / busy / unclear — no action, retry next batch (max 3)
    return []
```

### C) Sales transcript analyzer

Nuovo modulo `apps/workers/setting_agent/sales_analyzer.py`:

```python
import json
from apps.workers.setting_agent.transcript_analyzer import AnalysisError

VALID_OUTCOMES = {"accepted_pay", "interested_no_call", "rejected", "unclear"}


def analyze_sales_transcript(transcript: str, lead: dict, claude_client, max_retries=3) -> dict:
    """Returns {outcome, sales_brief}."""
    if not transcript or not transcript.strip():
        raise AnalysisError("empty transcript")

    prompt = f"""You are analyzing a SALES call transcript for a website service.
The agent is closing a sale at $349 USD one-time fee.

Transcript:
{transcript}

Customer info:
- Company: {lead.get('company_name', '?')}
- Phone: {lead.get('phone', '?')}

Classify the outcome as ONE of:
- accepted_pay: customer agreed to pay, ready to receive the link
- interested_no_call: customer said "send me info / I'll think about it / send to my email"
- rejected: explicit "no", do not call back, not interested
- unclear: ambiguous, retry needed

Respond ONLY with valid JSON: {{"outcome": "...", "sales_brief": "1-sentence summary"}}"""

    for attempt in range(max_retries):
        response = claude_client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=512,
            messages=[{"role": "user", "content": prompt}],
        )
        try:
            data = json.loads(response.content[0].text.strip())
            if data.get("outcome") in VALID_OUTCOMES:
                return data
        except (json.JSONDecodeError, KeyError, IndexError):
            continue

    raise AnalysisError(f"Could not parse sales outcome after {max_retries} retries")
```

### D) Stripe Checkout creator

Nuovo modulo `apps/workers/setting_agent/stripe_client.py`:

```python
import os
import stripe
import logging

logger = logging.getLogger(__name__)


def _get_stripe_client():
    stripe.api_key = os.environ["STRIPE_SECRET_KEY"]
    return stripe


def create_stripe_checkout(site: dict, lead: dict) -> tuple[str, str]:
    """Returns (checkout_url, session_id)."""
    client = _get_stripe_client()
    session = client.checkout.Session.create(
        mode="payment",
        line_items=[{
            "price": os.environ["STRIPE_PRICE_ID"],
            "quantity": 1,
        }],
        success_url=f"{os.environ['CUSTOMER_DASHBOARD_URL']}/payment-success?session_id={{CHECKOUT_SESSION_ID}}",
        cancel_url=f"{os.environ['CUSTOMER_DASHBOARD_URL']}/payment-cancel",
        customer_email=lead.get("email"),
        metadata={
            "site_id": site["id"],
            "lead_id": lead["id"],
        },
        payment_intent_data={
            "metadata": {"site_id": site["id"], "lead_id": lead["id"]},
        },
    )
    logger.info(f"Stripe Checkout created: site={site['id']} session={session.id}")
    return session.url, session.id
```

### E) SMS via Twilio

Nuovo modulo `apps/workers/setting_agent/twilio_sms.py`:

```python
import os
import logging
from twilio.rest import Client as TwilioClient

logger = logging.getLogger(__name__)


def send_sms(to: str, body: str) -> str:
    """Send SMS via Twilio. Returns message SID."""
    client = TwilioClient(
        os.environ["TWILIO_ACCOUNT_SID"],
        os.environ["TWILIO_AUTH_TOKEN"],
    )
    message = client.messages.create(
        from_=os.environ["TWILIO_PHONE_NUMBER"],
        to=to,
        body=body,
    )
    logger.info(f"SMS sent: to={to} sid={message.sid}")
    return message.sid
```

### F) Cleanup cron endpoint

`apps/dashboard/src/app/api/cron/cleanup-unpaid-sites/route.ts`:

```typescript
import { NextResponse } from "next/server";
import { createClient } from "@supabase/supabase-js";

export async function POST(req: Request) {
  const authHeader = req.headers.get("authorization");
  if (authHeader !== `Bearer ${process.env.CRON_SECRET}`) {
    return NextResponse.json({ error: "unauthorized" }, { status: 401 });
  }

  const supabase = createClient(
    process.env.SUPABASE_URL!,
    process.env.SUPABASE_SERVICE_KEY!,
  );

  const cutoff = new Date(Date.now() - 48 * 3600 * 1000).toISOString();

  const { data: expired, error: fetchErr } = await supabase
    .from("sites")
    .select("id, slug, lead_id")
    .eq("payment_status", "unpaid")
    .lt("published_at", cutoff);

  if (fetchErr) {
    return NextResponse.json({ error: fetchErr.message }, { status: 500 });
  }

  let deletedCount = 0;
  for (const site of expired ?? []) {
    const { error: delErr } = await supabase
      .from("sites").delete().eq("id", site.id);
    if (delErr) continue;

    await supabase.from("events").insert({
      type: "site.deleted_unpaid",
      source_agent: "cron",
      payload: {
        site_id: site.id,
        slug: site.slug,
        reason: "48h_grace_expired",
      },
    });

    await supabase.from("leads")
      .update({ status: "expired_no_pay" })
      .eq("id", site.lead_id);

    deletedCount++;
  }

  return NextResponse.json({ ok: true, deleted_count: deletedCount });
}
```

### G) `vercel.json` (cron config)

`apps/dashboard/vercel.json`:

```json
{
  "crons": [
    {
      "path": "/api/cron/cleanup-unpaid-sites",
      "schedule": "0 * * * *"
    }
  ]
}
```

---

## 5. Env vars

| Var | Scope | Esempio |
|---|---|---|
| `STRIPE_SECRET_KEY` | dashboard Vercel + Railway worker | `sk_live_...` or `sk_test_...` |
| `STRIPE_WEBHOOK_SECRET` | dashboard Vercel | `whsec_...` |
| `STRIPE_PRICE_ID` | Railway worker | `price_...` (pre-created $349 product) |
| `CRON_SECRET` | dashboard Vercel | random 32-char hex |
| `TWILIO_ACCOUNT_SID` | Railway worker | esistente (D-Phase1) |
| `TWILIO_AUTH_TOKEN` | Railway worker | esistente |
| `TWILIO_PHONE_NUMBER` | Railway worker | `+16627075199` esistente |
| `ELEVENLABS_SALES_AGENT_ID` | Railway worker | nuovo agente Conv AI da creare |
| `CUSTOMER_DASHBOARD_URL` | Railway worker | `https://customer-dashboard-ashen.vercel.app` |

---

## 6. Testing strategy

### Unit tests Python

- `test_sales_analyzer.py` — Claude returns each outcome correctly (mock Claude)
- `test_stripe_client.py` — checkout session creation passes correct metadata
- `test_twilio_sms.py` — SMS send invokes Twilio API with right params
- `test_setting_sales_handlers.py`:
  - `_handle_site_ready` triggers call when attempts < 3, skips when >= 3
  - `_handle_sales_call_completed` outcome=accepted → SMS sent
  - outcome=rejected → site DELETED + DNC INSERT
  - outcome=no_answer → no action

### Unit tests TypeScript

- `test_stripe_webhook.ts` — HMAC verify rejects bad signature, dedupe via stripe_events, checkout.session.completed → auth.user create + UPDATE site
- `test_cleanup_cron.ts` — auth check 401 on bad token, finds + deletes expired, emits events

### Integration test

Estendi `test_pipeline_integration.py` con full flow:
1. `setting.call_accepted` → Builder mock builds + emits `builder.site_ready`
2. D-Phase2 mock: triggers ElevenLabs (mock) + INSERT call_logs
3. `setting.sales_call_completed` con outcome=accepted (mock Claude)
4. Mock Stripe Checkout creation
5. Mock SMS send (assert called with phone + URL)
6. Simulate Stripe webhook payment.succeeded
7. Mock auth.user create + welcome email
8. Assert: site.payment_status='paid', site.owner_user_id set, customer.onboarded event emitted

### E2E manual

1. Trigger lead test (real lead + email + phone) → real D-Phase1 cold call → accepted
2. Builder builds real site → emits builder.site_ready
3. Real D-Phase2 sales call (you answer, say "yes I'll pay")
4. SMS arrives on +393477544532 with Stripe TEST checkout URL
5. Click link → Stripe test card 4242 4242 4242 4242 → pay
6. Stripe webhook fires → check Vercel function logs
7. Welcome email arrives at lead's email → click dashboard link
8. Login → forced password change → dashboard home

### E2E test cleanup behavior

1. Insert test lead (email valid)
2. Manually INSERT site row with `published_at = NOW() - INTERVAL '49 hours'`, `payment_status='unpaid'`
3. Trigger cleanup cron (manual POST con CRON_SECRET)
4. Assert: site DELETED, lead.status='expired_no_pay', site.deleted_unpaid event present

---

## 7. Deployment plan

1. Apply migration `008_payment_flow.sql` via Supabase MCP
2. Stripe setup (manual, 10 min):
   - Create Product "Website Setup" + Price $349 USD one-time
   - Save `price_id` in Railway env
   - Create webhook endpoint pointing to `https://agents-dashboard-theta.vercel.app/api/webhooks/stripe`
   - Subscribe to `checkout.session.completed` + `charge.refunded`
   - Save `webhook_signing_secret` in Vercel env
3. ElevenLabs Conv AI setup (manual, 5 min):
   - Create new sales agent with prompt focused on closing the $349 sale
   - Save `agent_id` in Railway env
4. Code deploy:
   - Add Python deps `stripe`, `twilio` (both already in for D-Phase1)
   - Implement F1 + D-Phase2 modules per plan
   - Deploy setting-agent worker on Railway
   - Deploy agents-dashboard on Vercel (incl. cron + webhook)
5. Set all env vars on Railway + Vercel
6. E2E test: real call flow + Stripe test mode card 4242
7. Switch Stripe to live mode for production

---

## 8. Observability

- **`stripe_events` table** = audit trail completo (every webhook received, processed_at, errors)
- **`events` table** filtri per type=`customer.onboarded` o `site.deleted_unpaid` = funnel metrics
- **Vercel function logs** = webhook handler successes/errors + cron runs
- **Stripe dashboard** = payment volume, churn (unpaid sites cleaned up), refunds
- **Twilio dashboard** = SMS delivery success rate

---

## 9. Open questions per implementation phase

| # | Question | Default decision |
|---|---|---|
| 1 | Stripe Tax automatic vs MVP | MVP minimum compliance ($349 inclusive, deferred) |
| 2 | Sales agent voice ElevenLabs | Reuse same voice di D-Phase1 o nuova? Default: stessa voce, prompt diverso |
| 3 | Sales call business hours | Stesse di D-Phase1 (US 8-21 ET, lun-sab) |
| 4 | SMS template lingua | English (test market USA), italiano future quando pivot IT |
| 5 | Stripe success_url branding | `customer-dashboard-ashen.vercel.app/payment-success` simple page (TBD design) |
| 6 | Refund handling | Manual via Stripe dashboard for MVP. F1.1 will add `charge.refunded` automation |

---

## 10. Riferimenti

- Spec E1 (foundation): `docs/superpowers/specs/2026-05-01-customer-dashboard-e1-design.md`
- Spec Setting Agent (D-Phase1): `docs/superpowers/specs/2026-04-28-setting-agent-design.md`
- Spec Builder Agent: `docs/superpowers/specs/2026-04-25-website-builder-design.md`
- Stato infra: `BRAINSTORM_STATE.md`
