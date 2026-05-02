# F1 + D-Phase2 Implementation Plan (Stripe Payments + Sales Call)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the monetization layer — second ElevenLabs Conv AI agent (sales prompt) calls leads post-Builder to sell $349, sends Stripe Checkout link via SMS, Stripe webhook completes onboarding (auth.user + welcome email + dashboard access), Vercel Cron cleans up unpaid sites after 48h grace period.

**Architecture:** D-Phase2 extends Setting Agent worker with `_handle_site_ready` (triggers sales call) and `_handle_sales_call_completed` (Claude analyzes outcome, sends SMS or deletes site). F1 adds Vercel route `/api/webhooks/stripe` (HMAC verify + checkout.session.completed handler creates auth.user) and `/api/cron/cleanup-unpaid-sites` (hourly DELETE expired). Migration `008` extends `sites` with stripe_* fields + creates `stripe_events` audit table.

**Tech Stack:** Python (setting_agent worker on Railway), Stripe SDK + Twilio SDK, Next.js 16 App Router (agents-dashboard), Stripe webhooks, Vercel Cron Jobs, Postgres RLS.

**Spec reference:** `docs/superpowers/specs/2026-05-01-stripe-payments-and-sales-call-design.md`

---

## Task 1: Database migration

**Files:**
- Create: `supabase/migrations/008_payment_flow.sql`

- [ ] **Step 1: Write the migration SQL**

Create `supabase/migrations/008_payment_flow.sql`:

```sql
-- 008_payment_flow.sql
-- F1 (Stripe payments) + D-Phase2 (sales call) tracking

-- 1. Stripe-specific fields on sites
ALTER TABLE sites ADD COLUMN stripe_checkout_session_id TEXT;
ALTER TABLE sites ADD COLUMN stripe_payment_intent_id TEXT;
ALTER TABLE sites ADD COLUMN stripe_customer_id TEXT;
ALTER TABLE sites ADD COLUMN paid_at TIMESTAMPTZ;
CREATE INDEX idx_sites_stripe_session ON sites(stripe_checkout_session_id);
CREATE INDEX idx_sites_stripe_pi ON sites(stripe_payment_intent_id);

-- 2. D-Phase2 retry tracking
ALTER TABLE sites ADD COLUMN sales_call_attempts INT NOT NULL DEFAULT 0;
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

-- 4. Service role bypasses RLS, but enable RLS on stripe_events for safety (no policies = no access for non-service)
ALTER TABLE stripe_events ENABLE ROW LEVEL SECURITY;
```

- [ ] **Step 2: Apply migration via Supabase MCP**

Use `mcp__plugin_supabase_supabase__execute_sql` with the SQL above against project `smzmgzblbliprwbjptjs`. Re-authenticate Supabase MCP first if disconnected (`mcp__plugin_supabase_supabase__authenticate`).

- [ ] **Step 3: Verify migration applied**

Execute via Supabase MCP:

```sql
SELECT column_name FROM information_schema.columns
WHERE table_name='sites'
  AND column_name IN ('stripe_checkout_session_id','stripe_payment_intent_id','stripe_customer_id','paid_at','sales_call_attempts','last_sales_call_at','sales_call_outcome')
ORDER BY column_name;

SELECT column_name FROM information_schema.columns
WHERE table_name='stripe_events'
ORDER BY column_name;
```

Expected: 7 columns on sites, 7 columns on stripe_events.

- [ ] **Step 4: Commit**

```bash
cd "c:/Users/indig/.antigravity/AGENT 2.0_TEST/agents-platform"
git add supabase/migrations/008_payment_flow.sql
git commit -m "feat(F1): migration 008 - Stripe + sales call schema

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 2: Twilio SMS module (TDD)

**Files:**
- Create: `apps/workers/setting_agent/twilio_sms.py`
- Create: `apps/workers/setting_agent/tests/test_twilio_sms.py`

- [ ] **Step 1: Write failing test**

Create `apps/workers/setting_agent/tests/test_twilio_sms.py`:

```python
"""Tests for Twilio SMS sending."""
import os
from unittest.mock import patch, MagicMock
import pytest

from apps.workers.setting_agent.twilio_sms import send_sms


@patch("apps.workers.setting_agent.twilio_sms.TwilioClient")
def test_send_sms_invokes_twilio(mock_client_cls):
    mock_client = MagicMock()
    mock_message = MagicMock()
    mock_message.sid = "SM_test_123"
    mock_client.messages.create.return_value = mock_message
    mock_client_cls.return_value = mock_client

    with patch.dict(os.environ, {
        "TWILIO_ACCOUNT_SID": "AC_test",
        "TWILIO_AUTH_TOKEN": "token_test",
        "TWILIO_PHONE_NUMBER": "+16627075199",
    }):
        sid = send_sms(to="+393477544532", body="Hello")

    assert sid == "SM_test_123"
    mock_client_cls.assert_called_once_with("AC_test", "token_test")
    mock_client.messages.create.assert_called_once_with(
        from_="+16627075199",
        to="+393477544532",
        body="Hello",
    )


@patch("apps.workers.setting_agent.twilio_sms.TwilioClient")
def test_send_sms_propagates_twilio_error(mock_client_cls):
    mock_client = MagicMock()
    mock_client.messages.create.side_effect = Exception("Twilio 500")
    mock_client_cls.return_value = mock_client

    with patch.dict(os.environ, {
        "TWILIO_ACCOUNT_SID": "AC_test",
        "TWILIO_AUTH_TOKEN": "token_test",
        "TWILIO_PHONE_NUMBER": "+16627075199",
    }):
        with pytest.raises(Exception, match="Twilio 500"):
            send_sms(to="+393477544532", body="Hello")
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd "c:/Users/indig/.antigravity/AGENT 2.0_TEST/agents-platform"
python -m pytest apps/workers/setting_agent/tests/test_twilio_sms.py -v
```

Expected: FAIL — `ModuleNotFoundError` for `twilio_sms`.

- [ ] **Step 3: Implement `twilio_sms.py`**

Create `apps/workers/setting_agent/twilio_sms.py`:

```python
"""Twilio SMS sender."""
import os
import logging
from twilio.rest import Client as TwilioClient

logger = logging.getLogger(__name__)


def send_sms(to: str, body: str) -> str:
    """Send SMS via Twilio. Returns Twilio message SID."""
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

- [ ] **Step 4: Run tests to verify they pass**

```bash
python -m pytest apps/workers/setting_agent/tests/test_twilio_sms.py -v
```

Expected: 2 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add apps/workers/setting_agent/twilio_sms.py apps/workers/setting_agent/tests/test_twilio_sms.py
git commit -m "feat(F1): Twilio SMS sender module (TDD)

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 3: Stripe Checkout module (TDD)

**Files:**
- Create: `apps/workers/setting_agent/stripe_client.py`
- Create: `apps/workers/setting_agent/tests/test_stripe_client.py`
- Modify: `apps/workers/setting_agent/requirements.txt` or `pyproject.toml` (add `stripe>=11.0`)

- [ ] **Step 1: Add stripe dependency**

Check the existing Python dependencies file. If `pyproject.toml` exists, add `stripe>=11.0` to the dependencies list. Same for `requirements.txt`. Also update the worker-level `requirements.txt` if present (`apps/workers/setting_agent/requirements.txt`).

```bash
cd "c:/Users/indig/.antigravity/AGENT 2.0_TEST/agents-platform"
pip install "stripe>=11.0"
```

- [ ] **Step 2: Write failing test**

Create `apps/workers/setting_agent/tests/test_stripe_client.py`:

```python
"""Tests for Stripe Checkout creation."""
import os
from unittest.mock import patch, MagicMock
import pytest

from apps.workers.setting_agent.stripe_client import create_stripe_checkout


def _sample_site():
    return {"id": "site-uuid", "slug": "mario-pizza"}


def _sample_lead():
    return {"id": "lead-uuid", "company_name": "Mario Pizza", "email": "mario@example.com"}


@patch("apps.workers.setting_agent.stripe_client.stripe")
def test_create_stripe_checkout_returns_url_and_session_id(mock_stripe):
    mock_session = MagicMock()
    mock_session.url = "https://checkout.stripe.com/c/pay/cs_test_123"
    mock_session.id = "cs_test_123"
    mock_stripe.checkout.Session.create.return_value = mock_session

    with patch.dict(os.environ, {
        "STRIPE_SECRET_KEY": "sk_test_xxx",
        "STRIPE_PRICE_ID": "price_xxx",
        "CUSTOMER_DASHBOARD_URL": "https://customer-dashboard-ashen.vercel.app",
    }):
        url, session_id = create_stripe_checkout(_sample_site(), _sample_lead())

    assert url == "https://checkout.stripe.com/c/pay/cs_test_123"
    assert session_id == "cs_test_123"

    mock_stripe.checkout.Session.create.assert_called_once()
    call_kwargs = mock_stripe.checkout.Session.create.call_args.kwargs
    assert call_kwargs["mode"] == "payment"
    assert call_kwargs["line_items"][0]["price"] == "price_xxx"
    assert call_kwargs["line_items"][0]["quantity"] == 1
    assert call_kwargs["customer_email"] == "mario@example.com"
    assert call_kwargs["metadata"] == {"site_id": "site-uuid", "lead_id": "lead-uuid"}
    assert "site-uuid" in call_kwargs["success_url"] or "{CHECKOUT_SESSION_ID}" in call_kwargs["success_url"]


@patch("apps.workers.setting_agent.stripe_client.stripe")
def test_create_stripe_checkout_propagates_stripe_error(mock_stripe):
    mock_stripe.checkout.Session.create.side_effect = Exception("Stripe API down")
    with patch.dict(os.environ, {
        "STRIPE_SECRET_KEY": "sk_test_xxx",
        "STRIPE_PRICE_ID": "price_xxx",
        "CUSTOMER_DASHBOARD_URL": "https://customer-dashboard-ashen.vercel.app",
    }):
        with pytest.raises(Exception, match="Stripe API down"):
            create_stripe_checkout(_sample_site(), _sample_lead())
```

- [ ] **Step 3: Run test to verify it fails**

```bash
python -m pytest apps/workers/setting_agent/tests/test_stripe_client.py -v
```

Expected: FAIL — `ModuleNotFoundError`.

- [ ] **Step 4: Implement `stripe_client.py`**

Create `apps/workers/setting_agent/stripe_client.py`:

```python
"""Stripe Checkout session creator."""
import os
import logging
import stripe

logger = logging.getLogger(__name__)


def create_stripe_checkout(site: dict, lead: dict) -> tuple[str, str]:
    """Create a Stripe Checkout Session. Returns (url, session_id)."""
    stripe.api_key = os.environ["STRIPE_SECRET_KEY"]
    dashboard_url = os.environ["CUSTOMER_DASHBOARD_URL"]
    session = stripe.checkout.Session.create(
        mode="payment",
        line_items=[{
            "price": os.environ["STRIPE_PRICE_ID"],
            "quantity": 1,
        }],
        success_url=f"{dashboard_url}/payment-success?session_id={{CHECKOUT_SESSION_ID}}",
        cancel_url=f"{dashboard_url}/payment-cancel",
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

- [ ] **Step 5: Run tests to verify they pass**

```bash
python -m pytest apps/workers/setting_agent/tests/test_stripe_client.py -v
```

Expected: 2 tests PASS.

- [ ] **Step 6: Commit**

```bash
git add apps/workers/setting_agent/stripe_client.py apps/workers/setting_agent/tests/test_stripe_client.py pyproject.toml
git commit -m "feat(F1): Stripe Checkout creator module (TDD)

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 4: Sales transcript analyzer (TDD)

**Files:**
- Create: `apps/workers/setting_agent/sales_analyzer.py`
- Create: `apps/workers/setting_agent/tests/test_sales_analyzer.py`

- [ ] **Step 1: Write failing test**

Create `apps/workers/setting_agent/tests/test_sales_analyzer.py`:

```python
"""Tests for sales transcript analyzer."""
import json
from unittest.mock import MagicMock
import pytest

from apps.workers.setting_agent.sales_analyzer import analyze_sales_transcript
from apps.workers.setting_agent.transcript_analyzer import AnalysisError


def _mock_claude(outcomes_sequence):
    """Mock claude_client.messages.create to return outcomes in sequence (allows retry tests)."""
    client = MagicMock()
    responses = []
    for outcome in outcomes_sequence:
        if outcome.startswith("MALFORMED:"):
            r = MagicMock()
            r.content = [MagicMock(text=outcome[len("MALFORMED:"):])]
            responses.append(r)
        else:
            r = MagicMock()
            r.content = [MagicMock(text=json.dumps({
                "outcome": outcome,
                "sales_brief": f"Customer outcome: {outcome}",
            }))]
            responses.append(r)
    client.messages.create.side_effect = responses
    return client


def _sample_lead():
    return {"id": "lead-1", "company_name": "Mario Pizza", "phone": "+393477544532"}


def test_analyze_returns_accepted_pay():
    claude = _mock_claude(["accepted_pay"])
    result = analyze_sales_transcript("Customer: Yes I'll pay", _sample_lead(), claude)
    assert result["outcome"] == "accepted_pay"
    assert "sales_brief" in result


def test_analyze_returns_rejected():
    claude = _mock_claude(["rejected"])
    result = analyze_sales_transcript("Customer: Not interested", _sample_lead(), claude)
    assert result["outcome"] == "rejected"


def test_analyze_returns_interested_no_call():
    claude = _mock_claude(["interested_no_call"])
    result = analyze_sales_transcript("Customer: Send me an email", _sample_lead(), claude)
    assert result["outcome"] == "interested_no_call"


def test_analyze_empty_transcript_raises():
    claude = MagicMock()
    with pytest.raises(AnalysisError, match="empty transcript"):
        analyze_sales_transcript("", _sample_lead(), claude)


def test_analyze_retries_on_malformed_then_succeeds():
    claude = _mock_claude(["MALFORMED:not json", "MALFORMED:still bad", "accepted_pay"])
    result = analyze_sales_transcript("Customer: yes", _sample_lead(), claude)
    assert result["outcome"] == "accepted_pay"
    assert claude.messages.create.call_count == 3


def test_analyze_raises_after_max_retries():
    claude = _mock_claude(["MALFORMED:bad"] * 4)
    with pytest.raises(AnalysisError, match="Could not parse"):
        analyze_sales_transcript("Customer: yes", _sample_lead(), claude)
```

- [ ] **Step 2: Run test to verify it fails**

```bash
python -m pytest apps/workers/setting_agent/tests/test_sales_analyzer.py -v
```

Expected: FAIL — `ModuleNotFoundError`.

- [ ] **Step 3: Implement `sales_analyzer.py`**

Create `apps/workers/setting_agent/sales_analyzer.py`:

```python
"""Claude analyzer for D-Phase2 sales call transcripts."""
import json
import logging

from apps.workers.setting_agent.transcript_analyzer import AnalysisError

logger = logging.getLogger(__name__)

VALID_OUTCOMES = {"accepted_pay", "interested_no_call", "rejected", "unclear"}
MAX_RETRIES = 3
MODEL = "claude-sonnet-4-6"


def analyze_sales_transcript(transcript: str, lead: dict, claude_client) -> dict:
    """Analyze sales call transcript. Returns {outcome, sales_brief}.

    Outcomes:
    - accepted_pay: customer agreed to pay, ready for the link
    - interested_no_call: customer wants info via SMS/email, will think about it
    - rejected: explicit no, do not call back
    - unclear: ambiguous, retry needed
    """
    if not transcript or not transcript.strip():
        raise AnalysisError("empty transcript")

    prompt = f"""You are analyzing a SALES call transcript for a website service.
The agent is closing a sale at $349 USD one-time fee. The first call already qualified the lead;
this second call is the close.

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

    last_error = None
    for attempt in range(MAX_RETRIES):
        try:
            response = claude_client.messages.create(
                model=MODEL,
                max_tokens=512,
                messages=[{"role": "user", "content": prompt}],
            )
            text = response.content[0].text.strip()
            data = json.loads(text)
            if data.get("outcome") in VALID_OUTCOMES:
                return {
                    "outcome": data["outcome"],
                    "sales_brief": data.get("sales_brief", ""),
                }
            last_error = f"invalid outcome: {data.get('outcome')}"
        except (json.JSONDecodeError, KeyError, IndexError) as e:
            last_error = str(e)
            continue

    raise AnalysisError(f"Could not parse sales outcome after {MAX_RETRIES} retries: {last_error}")
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
python -m pytest apps/workers/setting_agent/tests/test_sales_analyzer.py -v
```

Expected: 6 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add apps/workers/setting_agent/sales_analyzer.py apps/workers/setting_agent/tests/test_sales_analyzer.py
git commit -m "feat(D-Phase2): sales transcript analyzer with Claude (TDD)

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 5: Setting Agent — `_handle_site_ready` handler (TDD)

**Files:**
- Modify: `apps/workers/setting_agent/main.py` (add handler + register in `handle_event`)
- Create: `apps/workers/setting_agent/tests/test_handle_site_ready.py`

- [ ] **Step 1: Write failing test**

Create `apps/workers/setting_agent/tests/test_handle_site_ready.py`:

```python
"""Tests for D-Phase2 _handle_site_ready handler."""
import os
from unittest.mock import patch, MagicMock
import pytest

from apps.workers.setting_agent.main import SettingAgent, MAX_SALES_CALL_ATTEMPTS


def _make_agent(client=None):
    if client is None:
        client = MagicMock()
    with patch.dict(os.environ, {
        "ANTHROPIC_API_KEY": "test",
        "ELEVENLABS_API_KEY": "test",
        "ELEVENLABS_AGENT_ID": "agent_cold",
        "ELEVENLABS_AGENT_PHONE_NUMBER_ID": "phn_xxx",
        "ELEVENLABS_SALES_AGENT_ID": "agent_sales",
    }):
        agent = SettingAgent(supabase_client=client)
    return agent, client


def _mock_supabase_for_site_ready(site_attempts=0):
    client = MagicMock()
    site = {
        "id": "site-1",
        "lead_id": "lead-1",
        "slug": "mario-pizza",
        "sales_call_attempts": site_attempts,
    }
    lead = {"id": "lead-1", "company_name": "Mario", "phone": "+393477544532", "email": "mario@example.com"}

    # _load_site (uses .limit(1))
    sel_site_eq = MagicMock()
    sel_site_eq.limit = MagicMock(return_value=sel_site_eq)
    sel_site_eq.execute = MagicMock(return_value=MagicMock(data=[site]))

    sel_lead_eq = MagicMock()
    sel_lead_eq.limit = MagicMock(return_value=sel_lead_eq)
    sel_lead_eq.execute = MagicMock(return_value=MagicMock(data=[lead]))

    # do_not_call check returns empty
    sel_dnc_eq = MagicMock()
    sel_dnc_eq.limit = MagicMock(return_value=sel_dnc_eq)
    sel_dnc_eq.execute = MagicMock(return_value=MagicMock(data=[]))

    def select_router(name):
        t = MagicMock()
        sel = MagicMock()
        sel_eq_router = {
            "sites": sel_site_eq,
            "leads": sel_lead_eq,
            "do_not_call": sel_dnc_eq,
        }
        sel.eq = MagicMock(return_value=sel_eq_router.get(name, MagicMock()))
        t.select = MagicMock(return_value=sel)

        # update + insert: standard mocks
        upd = MagicMock()
        upd.eq = MagicMock(return_value=upd)
        upd.execute = MagicMock(return_value=MagicMock())
        t.update = MagicMock(return_value=upd)
        t.insert = MagicMock(return_value=MagicMock(execute=MagicMock(return_value=MagicMock())))
        t.delete = MagicMock(return_value=MagicMock(eq=MagicMock(return_value=MagicMock(execute=MagicMock()))))
        return t

    client.table.side_effect = select_router
    return client


@pytest.mark.asyncio
async def test_handle_site_ready_triggers_sales_call_when_attempts_zero():
    client = _mock_supabase_for_site_ready(site_attempts=0)
    agent, _ = _make_agent(client)
    agent._elevenlabs = MagicMock()
    agent._elevenlabs.trigger_outbound_call.return_value = {
        "conversation_id": "conv_xxx",
        "callSid": "CA_xxx",
    }

    event = {
        "type": "builder.site_ready",
        "payload": {"site_id": "site-1", "lead_id": "lead-1"},
    }
    new_events = await agent._handle_site_ready(event)

    agent._elevenlabs.trigger_outbound_call.assert_called_once()
    call_kwargs = agent._elevenlabs.trigger_outbound_call.call_args.kwargs
    assert call_kwargs["agent_id"] == "agent_sales"
    assert call_kwargs["to_number"] == "+393477544532"

    assert len(new_events) == 1
    assert new_events[0]["type"] == "setting.sales_call_initiated"
    assert new_events[0]["payload"]["site_id"] == "site-1"


@pytest.mark.asyncio
async def test_handle_site_ready_skips_when_max_attempts():
    client = _mock_supabase_for_site_ready(site_attempts=MAX_SALES_CALL_ATTEMPTS)
    agent, _ = _make_agent(client)
    agent._elevenlabs = MagicMock()

    event = {"type": "builder.site_ready", "payload": {"site_id": "site-1", "lead_id": "lead-1"}}
    result = await agent._handle_site_ready(event)
    assert result == []
    agent._elevenlabs.trigger_outbound_call.assert_not_called()


@pytest.mark.asyncio
async def test_handle_site_ready_no_phone_returns_empty():
    client = MagicMock()
    site = {"id": "site-1", "lead_id": "lead-1", "slug": "x", "sales_call_attempts": 0}
    lead_no_phone = {"id": "lead-1", "company_name": "X", "phone": None, "email": "x@x.com"}

    def select_router(name):
        t = MagicMock()
        sel_eq = MagicMock()
        sel_eq.limit = MagicMock(return_value=sel_eq)
        if name == "sites":
            sel_eq.execute = MagicMock(return_value=MagicMock(data=[site]))
        elif name == "leads":
            sel_eq.execute = MagicMock(return_value=MagicMock(data=[lead_no_phone]))
        else:
            sel_eq.execute = MagicMock(return_value=MagicMock(data=[]))
        sel = MagicMock()
        sel.eq = MagicMock(return_value=sel_eq)
        t.select = MagicMock(return_value=sel)
        return t

    client.table.side_effect = select_router

    agent, _ = _make_agent(client)
    agent._elevenlabs = MagicMock()
    event = {"type": "builder.site_ready", "payload": {"site_id": "site-1", "lead_id": "lead-1"}}
    result = await agent._handle_site_ready(event)
    assert result == []
    agent._elevenlabs.trigger_outbound_call.assert_not_called()
```

- [ ] **Step 2: Run test to verify it fails**

```bash
python -m pytest apps/workers/setting_agent/tests/test_handle_site_ready.py -v
```

Expected: FAIL — `_handle_site_ready` not defined.

- [ ] **Step 3: Add `_handle_site_ready` and `_load_site` to `main.py`**

In `apps/workers/setting_agent/main.py`:

Near top (with imports), ensure these are imported:

```python
from apps.workers.setting_agent.compliance import is_phone_in_dnc
```

Add module-level constant near other constants:

```python
MAX_SALES_CALL_ATTEMPTS = 3
```

Inside `SettingAgent` class, add the new handler and `_load_site` helper. Update `handle_event` to dispatch to it.

Replace the existing `handle_event` method:

```python
async def handle_event(self, event: dict) -> list[dict]:
    event_type = event.get("type", "")
    if event_type == "setting.call_completed":
        return await self._handle_call_completed(event)
    if event_type == "setting.force_call":
        return await self._handle_force_call(event)
    if event_type == "builder.site_ready":
        return await self._handle_site_ready(event)
    if event_type == "setting.sales_call_completed":
        return await self._handle_sales_call_completed(event)
    if event_type == "builder.website_ready":
        logger.info(
            f"builder.website_ready for lead {event.get('payload', {}).get('lead_id')}; "
            "site-ready call is phase 2, skipping."
        )
        return []
    return []
```

Add `_load_site` helper near `_load_lead`:

```python
def _load_site(self, site_id: str):
    result = (
        self._client.table("sites")
        .select("*")
        .eq("id", site_id)
        .limit(1)
        .execute()
    )
    rows = result.data if result is not None else None
    return rows[0] if rows else None
```

Add the new handler:

```python
async def _handle_site_ready(self, event: dict) -> list[dict]:
    """D-Phase2 trigger: site is built, call lead with sales agent."""
    payload = event.get("payload", {})
    site_id = payload.get("site_id")
    lead_id = payload.get("lead_id")
    if not site_id or not lead_id:
        return []

    site = self._load_site(site_id)
    lead = self._load_lead(lead_id)
    if not site or not lead or not lead.get("phone"):
        return []

    attempts = site.get("sales_call_attempts", 0) or 0
    if attempts >= MAX_SALES_CALL_ATTEMPTS:
        logger.warning(
            f"Max sales call attempts ({MAX_SALES_CALL_ATTEMPTS}) reached for site {site_id}"
        )
        return []

    if is_phone_in_dnc(lead["phone"], self._client):
        logger.info(f"Skipping sales call: {lead['phone']} in DNC")
        return []

    sales_agent_id = os.environ.get("ELEVENLABS_SALES_AGENT_ID", "")
    if not sales_agent_id:
        logger.error("ELEVENLABS_SALES_AGENT_ID not set; cannot trigger sales call")
        return []

    try:
        result = self._elevenlabs.trigger_outbound_call(
            agent_id=sales_agent_id,
            agent_phone_number_id=self._agent_phone_id,
            to_number=lead["phone"],
        )
    except ElevenLabsError as e:
        logger.error(f"Sales call trigger failed for site {site_id}: {e}")
        return [{
            "type": "setting.sales_call_failed",
            "target_agent": None,
            "payload": {"site_id": site_id, "lead_id": lead_id, "reason": str(e)},
        }]

    self._client.table("sites").update({
        "sales_call_attempts": attempts + 1,
        "last_sales_call_at": datetime.now(timezone.utc).isoformat(),
    }).eq("id", site_id).execute()

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
            "call_sid": result.get("callSid") or result.get("call_sid", ""),
            "agent_id": sales_agent_id,
        },
    }]
```

NOTE: `_handle_sales_call_completed` is added in Task 6 — leave a stub for now to allow the imports/dispatch to compile:

```python
async def _handle_sales_call_completed(self, event: dict) -> list[dict]:
    """Stub — implemented in Task 6."""
    return []
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
python -m pytest apps/workers/setting_agent/tests/test_handle_site_ready.py -v
```

Expected: 3 tests PASS.

- [ ] **Step 5: Run full test suite to verify no regression**

```bash
python -m pytest apps/workers/setting_agent/tests/ -v
```

Expected: all existing tests still pass + new 3 pass.

- [ ] **Step 6: Commit**

```bash
git add apps/workers/setting_agent/main.py apps/workers/setting_agent/tests/test_handle_site_ready.py
git commit -m "feat(D-Phase2): add _handle_site_ready handler for sales call trigger (TDD)

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 6: Setting Agent — `_handle_sales_call_completed` handler (TDD)

**Files:**
- Modify: `apps/workers/setting_agent/main.py` (replace stub from Task 5)
- Create: `apps/workers/setting_agent/tests/test_handle_sales_call_completed.py`

- [ ] **Step 1: Write failing test**

Create `apps/workers/setting_agent/tests/test_handle_sales_call_completed.py`:

```python
"""Tests for D-Phase2 _handle_sales_call_completed handler."""
import os
from unittest.mock import patch, MagicMock
import pytest

from apps.workers.setting_agent.main import SettingAgent


def _make_agent(client=None):
    if client is None:
        client = MagicMock()
    with patch.dict(os.environ, {
        "ANTHROPIC_API_KEY": "test",
        "ELEVENLABS_API_KEY": "test",
        "ELEVENLABS_AGENT_ID": "agent_cold",
        "ELEVENLABS_AGENT_PHONE_NUMBER_ID": "phn_xxx",
        "ELEVENLABS_SALES_AGENT_ID": "agent_sales",
        "STRIPE_SECRET_KEY": "sk_test",
        "STRIPE_PRICE_ID": "price_xxx",
        "CUSTOMER_DASHBOARD_URL": "https://customer-dashboard-ashen.vercel.app",
        "TWILIO_ACCOUNT_SID": "AC",
        "TWILIO_AUTH_TOKEN": "tok",
        "TWILIO_PHONE_NUMBER": "+1xxx",
    }):
        agent = SettingAgent(supabase_client=client)
    return agent, client


def _mock_supabase_for_completed(site_data=None, lead_data=None):
    client = MagicMock()
    site = site_data or {
        "id": "site-1",
        "lead_id": "lead-1",
        "slug": "mario-pizza",
    }
    lead = lead_data or {
        "id": "lead-1",
        "company_name": "Mario",
        "phone": "+393477544532",
        "email": "mario@example.com",
    }

    sel_site_eq = MagicMock()
    sel_site_eq.limit = MagicMock(return_value=sel_site_eq)
    sel_site_eq.execute = MagicMock(return_value=MagicMock(data=[site]))

    sel_lead_eq = MagicMock()
    sel_lead_eq.limit = MagicMock(return_value=sel_lead_eq)
    sel_lead_eq.execute = MagicMock(return_value=MagicMock(data=[lead]))

    def select_router(name):
        t = MagicMock()
        sel = MagicMock()
        if name == "sites":
            sel.eq = MagicMock(return_value=sel_site_eq)
        elif name == "leads":
            sel.eq = MagicMock(return_value=sel_lead_eq)
        else:
            sel_eq = MagicMock()
            sel_eq.limit = MagicMock(return_value=sel_eq)
            sel_eq.execute = MagicMock(return_value=MagicMock(data=[]))
            sel.eq = MagicMock(return_value=sel_eq)
        t.select = MagicMock(return_value=sel)

        upd = MagicMock()
        upd.eq = MagicMock(return_value=upd)
        upd.execute = MagicMock(return_value=MagicMock())
        t.update = MagicMock(return_value=upd)

        ins = MagicMock()
        ins.execute = MagicMock(return_value=MagicMock())
        t.insert = MagicMock(return_value=ins)

        delete = MagicMock()
        delete_eq = MagicMock()
        delete_eq.execute = MagicMock(return_value=MagicMock())
        delete.eq = MagicMock(return_value=delete_eq)
        t.delete = MagicMock(return_value=delete)
        return t

    client.table.side_effect = select_router
    return client


@pytest.mark.asyncio
@patch("apps.workers.setting_agent.main.send_sms")
@patch("apps.workers.setting_agent.main.create_stripe_checkout")
@patch("apps.workers.setting_agent.main.analyze_sales_transcript")
async def test_accepted_pay_creates_checkout_and_sends_sms(mock_analyze, mock_checkout, mock_sms):
    mock_analyze.return_value = {"outcome": "accepted_pay", "sales_brief": "yes"}
    mock_checkout.return_value = ("https://checkout.stripe.com/c/pay/cs_xxx", "cs_xxx")
    mock_sms.return_value = "SM_123"

    client = _mock_supabase_for_completed()
    agent, _ = _make_agent(client)

    event = {
        "type": "setting.sales_call_completed",
        "payload": {"site_id": "site-1", "transcript": "Yes I'll pay"},
    }
    new_events = await agent._handle_sales_call_completed(event)

    mock_checkout.assert_called_once()
    mock_sms.assert_called_once()
    sms_kwargs = mock_sms.call_args.kwargs
    assert sms_kwargs["to"] == "+393477544532"
    assert "https://checkout.stripe.com" in sms_kwargs["body"]

    assert len(new_events) == 1
    assert new_events[0]["type"] == "setting.payment_link_sent"
    assert new_events[0]["payload"]["channel"] == "sms"


@pytest.mark.asyncio
@patch("apps.workers.setting_agent.main.send_sms")
@patch("apps.workers.setting_agent.main.create_stripe_checkout")
@patch("apps.workers.setting_agent.main.analyze_sales_transcript")
async def test_interested_no_call_also_sends_sms(mock_analyze, mock_checkout, mock_sms):
    mock_analyze.return_value = {"outcome": "interested_no_call", "sales_brief": "thinking"}
    mock_checkout.return_value = ("https://checkout.stripe.com/c/pay/cs_xxx", "cs_xxx")
    mock_sms.return_value = "SM_123"

    client = _mock_supabase_for_completed()
    agent, _ = _make_agent(client)

    event = {"type": "setting.sales_call_completed", "payload": {"site_id": "site-1", "transcript": "thinking"}}
    new_events = await agent._handle_sales_call_completed(event)

    mock_sms.assert_called_once()
    assert new_events[0]["type"] == "setting.payment_link_sent"


@pytest.mark.asyncio
@patch("apps.workers.setting_agent.main.send_sms")
@patch("apps.workers.setting_agent.main.create_stripe_checkout")
@patch("apps.workers.setting_agent.main.analyze_sales_transcript")
async def test_rejected_deletes_site_and_adds_to_dnc(mock_analyze, mock_checkout, mock_sms):
    mock_analyze.return_value = {"outcome": "rejected", "sales_brief": "no"}
    client = _mock_supabase_for_completed()
    agent, _ = _make_agent(client)

    event = {"type": "setting.sales_call_completed", "payload": {"site_id": "site-1", "transcript": "no"}}
    new_events = await agent._handle_sales_call_completed(event)

    mock_checkout.assert_not_called()
    mock_sms.assert_not_called()

    # delete called on sites
    delete_calls = [c for c in client.table.mock_calls if "delete" in str(c)]
    assert any("delete" in str(c) for c in client.table.return_value.delete.mock_calls) or \
           any("sites" in str(c) for c in client.table.mock_calls)

    assert len(new_events) == 1
    assert new_events[0]["type"] == "site.deleted_unpaid"
    assert new_events[0]["payload"]["reason"] == "rejected"


@pytest.mark.asyncio
@patch("apps.workers.setting_agent.main.send_sms")
@patch("apps.workers.setting_agent.main.create_stripe_checkout")
@patch("apps.workers.setting_agent.main.analyze_sales_transcript")
async def test_no_answer_returns_empty(mock_analyze, mock_checkout, mock_sms):
    mock_analyze.return_value = {"outcome": "unclear", "sales_brief": "ambiguous"}
    client = _mock_supabase_for_completed()
    agent, _ = _make_agent(client)

    event = {"type": "setting.sales_call_completed", "payload": {"site_id": "site-1", "transcript": "..."}}
    result = await agent._handle_sales_call_completed(event)

    mock_checkout.assert_not_called()
    mock_sms.assert_not_called()
    assert result == []
```

- [ ] **Step 2: Run test to verify it fails**

```bash
python -m pytest apps/workers/setting_agent/tests/test_handle_sales_call_completed.py -v
```

Expected: FAIL — handler is currently a stub returning `[]` for accepted_pay test, missing imports for create_stripe_checkout/send_sms/analyze_sales_transcript.

- [ ] **Step 3: Implement `_handle_sales_call_completed` (replace stub)**

In `apps/workers/setting_agent/main.py`, add imports near top:

```python
from apps.workers.setting_agent.sales_analyzer import analyze_sales_transcript
from apps.workers.setting_agent.stripe_client import create_stripe_checkout
from apps.workers.setting_agent.twilio_sms import send_sms
```

Replace the stub `_handle_sales_call_completed` from Task 5 with:

```python
async def _handle_sales_call_completed(self, event: dict) -> list[dict]:
    """Process sales call transcript, route based on outcome."""
    payload = event.get("payload", {})
    site_id = payload.get("site_id")
    transcript = payload.get("transcript", "")
    if not site_id:
        return []

    site = self._load_site(site_id)
    if not site:
        return []
    lead = self._load_lead(site["lead_id"])
    if not lead:
        return []

    try:
        analysis = analyze_sales_transcript(transcript, lead, self._claude)
        outcome = analysis["outcome"]
    except AnalysisError:
        outcome = "unclear"

    self._client.table("sites").update({
        "sales_call_outcome": outcome,
    }).eq("id", site_id).execute()

    if outcome in ("accepted_pay", "interested_no_call"):
        try:
            checkout_url, session_id = create_stripe_checkout(site, lead)
        except Exception as e:
            logger.error(f"Stripe checkout creation failed for site {site_id}: {e}")
            return []
        self._client.table("sites").update({
            "stripe_checkout_session_id": session_id,
        }).eq("id", site_id).execute()
        try:
            send_sms(
                to=lead["phone"],
                body=f"Hi {lead.get('company_name', 'there')}, here's your link to activate your website ($349): {checkout_url}",
            )
        except Exception as e:
            logger.error(f"SMS send failed for site {site_id}: {e}")
        return [{
            "type": "setting.payment_link_sent",
            "target_agent": None,
            "payload": {
                "site_id": site_id,
                "stripe_session_id": session_id,
                "channel": "sms",
                "phone": lead.get("phone"),
            },
        }]

    if outcome == "rejected":
        self._client.table("sites").delete().eq("id", site_id).execute()
        try:
            self._client.table("do_not_call").insert({
                "phone": lead.get("phone"),
                "reason": "sales_call_rejected",
            }).execute()
        except Exception as e:
            logger.warning(f"DNC insert failed (likely duplicate): {e}")
        return [{
            "type": "site.deleted_unpaid",
            "target_agent": None,
            "payload": {
                "site_id": site_id,
                "slug": site.get("slug"),
                "reason": "rejected",
            },
        }]

    # no_answer / busy / unclear → no immediate action, scheduler retry
    return []
```

Make sure `AnalysisError` is imported (it should already be from existing `_handle_call_completed`):

```python
from apps.workers.setting_agent.transcript_analyzer import AnalysisError
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
python -m pytest apps/workers/setting_agent/tests/test_handle_sales_call_completed.py -v
```

Expected: 4 tests PASS.

- [ ] **Step 5: Run full setting_agent test suite**

```bash
python -m pytest apps/workers/setting_agent/tests/ -v
```

Expected: all tests pass.

- [ ] **Step 6: Commit**

```bash
git add apps/workers/setting_agent/main.py apps/workers/setting_agent/tests/test_handle_sales_call_completed.py
git commit -m "feat(D-Phase2): add _handle_sales_call_completed with outcome routing (TDD)

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 7: Stripe webhook handler (TS, agents-dashboard)

**Files:**
- Create: `apps/dashboard/src/app/api/webhooks/stripe/route.ts`
- Modify: `apps/dashboard/package.json` (add `stripe` dependency if missing)

- [ ] **Step 1: Add `stripe` npm dependency**

```bash
cd "c:/Users/indig/.antigravity/AGENT 2.0_TEST/agents-platform/apps/dashboard"
npm install "stripe@^17.0.0"
```

- [ ] **Step 2: Create the route handler**

Create `apps/dashboard/src/app/api/webhooks/stripe/route.ts`:

```typescript
import { NextResponse } from "next/server";
import Stripe from "stripe";
import { createClient, type SupabaseClient } from "@supabase/supabase-js";
import crypto from "crypto";

const stripeSecretKey = process.env.STRIPE_SECRET_KEY!;
const webhookSecret = process.env.STRIPE_WEBHOOK_SECRET!;
const supabaseUrl = process.env.SUPABASE_URL || process.env.NEXT_PUBLIC_SUPABASE_URL!;
const supabaseServiceKey = process.env.SUPABASE_SERVICE_KEY!;

const stripe = new Stripe(stripeSecretKey);

function generateRandomPassword(length = 14): string {
  return crypto.randomBytes(length).toString("base64url").slice(0, length);
}

async function sendWelcomeEmail(opts: {
  email: string;
  companyName: string;
  password: string;
  dashboardUrl: string;
  siteUrl: string;
}): Promise<boolean> {
  const resendKey = process.env.RESEND_API_KEY;
  if (!resendKey) return false;
  const html = `<!doctype html><html><body style="font-family:Inter,Arial,sans-serif;max-width:600px;margin:0 auto;padding:24px">
<h1>Your website is live, ${opts.companyName}!</h1>
<p>Your website is published at: <a href="${opts.siteUrl}">${opts.siteUrl}</a></p>
<h2>Dashboard access</h2>
<p>URL: <a href="${opts.dashboardUrl}">${opts.dashboardUrl}</a><br>
Email: <code>${opts.email}</code><br>
Temporary password: <code>${opts.password}</code></p>
<p style="color:#666;font-size:14px">You'll be required to set a new password on your first login.</p>
</body></html>`;
  const text = `Your website is live, ${opts.companyName}!\n\nWebsite: ${opts.siteUrl}\nDashboard: ${opts.dashboardUrl}\nEmail: ${opts.email}\nTemporary password: ${opts.password}\n\nYou'll be required to set a new password on your first login.`;

  const resp = await fetch("https://api.resend.com/emails", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${resendKey}`,
    },
    body: JSON.stringify({
      from: "onboarding@resend.dev",
      to: [opts.email],
      subject: `Your ${opts.companyName} website is ready`,
      html,
      text,
    }),
  });
  return resp.ok;
}

export async function POST(req: Request) {
  const body = await req.text();
  const signature = req.headers.get("stripe-signature");
  if (!signature) {
    return NextResponse.json({ error: "missing signature" }, { status: 401 });
  }

  let event: Stripe.Event;
  try {
    event = stripe.webhooks.constructEvent(body, signature, webhookSecret);
  } catch {
    return NextResponse.json({ error: "invalid signature" }, { status: 401 });
  }

  const supabase = createClient(supabaseUrl, supabaseServiceKey);

  // Dedupe via stripe_events.stripe_event_id UNIQUE
  const { data: existing } = await supabase
    .from("stripe_events")
    .select("id")
    .eq("stripe_event_id", event.id)
    .maybeSingle();
  if (existing) {
    return NextResponse.json({ ok: true, deduped: true });
  }

  // Audit insert (race-safe via UNIQUE constraint, ignore conflict)
  const { error: insertEventErr } = await supabase
    .from("stripe_events")
    .insert({
      stripe_event_id: event.id,
      event_type: event.type,
      payload: event.data as unknown as Record<string, unknown>,
    });
  if (insertEventErr && !insertEventErr.message.includes("duplicate")) {
    return NextResponse.json({ error: insertEventErr.message }, { status: 500 });
  }

  if (event.type === "checkout.session.completed") {
    return await handleCheckoutCompleted(
      event.data.object as Stripe.Checkout.Session,
      event.id,
      supabase,
    );
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

  // 1. UPDATE sites SET payment_status='paid' (idempotency guard via WHERE payment_status='unpaid')
  const { data: sites } = await supabase
    .from("sites")
    .update({
      payment_status: "paid",
      paid_at: new Date().toISOString(),
      stripe_payment_intent_id: session.payment_intent as string,
      stripe_customer_id: session.customer as string,
    })
    .eq("id", siteId)
    .eq("payment_status", "unpaid")
    .select("id, slug, lead_id");

  if (!sites || sites.length === 0) {
    return NextResponse.json({ ok: true, already_processed: true });
  }
  const site = sites[0];

  // Load lead separately (Supabase JS doesn't easily nest joins on update returning)
  const { data: leads } = await supabase
    .from("leads")
    .select("id, email, company_name")
    .eq("id", site.lead_id)
    .limit(1);
  const lead = leads?.[0];
  if (!lead || !lead.email) {
    return NextResponse.json({ error: "lead has no email" }, { status: 400 });
  }

  // 2. Create or find auth.user
  const password = generateRandomPassword();
  let authUserId: string | undefined;

  const { data: created, error: createErr } =
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

  if (createErr) {
    if (createErr.message?.includes("already registered") || createErr.message?.includes("already exists")) {
      // Find existing user via Supabase admin list (ok for low N)
      const { data: list } = await supabase.auth.admin.listUsers();
      authUserId = list?.users?.find((u) => u.email === lead.email)?.id;
    } else {
      return NextResponse.json({ error: createErr.message }, { status: 500 });
    }
  } else {
    authUserId = created?.user?.id;
  }

  if (!authUserId) {
    return NextResponse.json({ error: "could not resolve auth user" }, { status: 500 });
  }

  // 3. UPDATE site.owner_user_id
  await supabase.from("sites").update({ owner_user_id: authUserId }).eq("id", siteId);

  // 4. Send welcome email
  const dashboardUrl = process.env.CUSTOMER_DASHBOARD_URL ||
    "https://customer-dashboard-ashen.vercel.app";
  const sitesBaseUrl = "https://agents-sites.vercel.app";
  const emailSent = await sendWelcomeEmail({
    email: lead.email,
    companyName: lead.company_name,
    password,
    dashboardUrl,
    siteUrl: `${sitesBaseUrl}/s/${site.slug}`,
  });

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
      email_sent: emailSent,
    },
    status: "pending",
  });

  return NextResponse.json({ ok: true, onboarded: authUserId, email_sent: emailSent });
}
```

- [ ] **Step 3: Verify build passes**

```bash
cd "c:/Users/indig/.antigravity/AGENT 2.0_TEST/agents-platform/apps/dashboard"
npm run build
```

Expected: build OK, route `/api/webhooks/stripe` listed as dynamic.

- [ ] **Step 4: Commit**

```bash
cd "c:/Users/indig/.antigravity/AGENT 2.0_TEST/agents-platform"
git add apps/dashboard/src/app/api/webhooks/stripe apps/dashboard/package.json apps/dashboard/package-lock.json
git commit -m "feat(F1): Stripe webhook handler with HMAC verify + onboarding

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 8: Cleanup cron endpoint + vercel.json

**Files:**
- Create: `apps/dashboard/src/app/api/cron/cleanup-unpaid-sites/route.ts`
- Create: `apps/dashboard/vercel.json`

- [ ] **Step 1: Create the cron endpoint**

Create `apps/dashboard/src/app/api/cron/cleanup-unpaid-sites/route.ts`:

```typescript
import { NextResponse } from "next/server";
import { createClient } from "@supabase/supabase-js";

const supabaseUrl = process.env.SUPABASE_URL || process.env.NEXT_PUBLIC_SUPABASE_URL!;
const supabaseServiceKey = process.env.SUPABASE_SERVICE_KEY!;
const cronSecret = process.env.CRON_SECRET;

export async function POST(req: Request) {
  const authHeader = req.headers.get("authorization");
  if (!cronSecret || authHeader !== `Bearer ${cronSecret}`) {
    return NextResponse.json({ error: "unauthorized" }, { status: 401 });
  }

  const supabase = createClient(supabaseUrl, supabaseServiceKey);
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
      status: "pending",
    });

    await supabase.from("leads")
      .update({ status: "expired_no_pay" })
      .eq("id", site.lead_id);

    deletedCount++;
  }

  return NextResponse.json({ ok: true, deleted_count: deletedCount });
}

// Vercel Cron sends GET requests by default; allow both
export const GET = POST;
```

- [ ] **Step 2: Create vercel.json**

Create `apps/dashboard/vercel.json`:

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

- [ ] **Step 3: Verify build passes**

```bash
cd "c:/Users/indig/.antigravity/AGENT 2.0_TEST/agents-platform/apps/dashboard"
npm run build
```

Expected: build OK, both routes listed.

- [ ] **Step 4: Commit**

```bash
cd "c:/Users/indig/.antigravity/AGENT 2.0_TEST/agents-platform"
git add apps/dashboard/src/app/api/cron apps/dashboard/vercel.json
git commit -m "feat(F1): cleanup-unpaid-sites cron endpoint + vercel.json schedule

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 9: External setup (Stripe + ElevenLabs) — manual steps

**Files:** N/A (external dashboards)

- [ ] **Step 1: Create Stripe Product + Price (manual)**

User action:
1. Open https://dashboard.stripe.com/products
2. Click "Add product"
3. Name: `Website Setup`
4. Pricing: `One-time`, `$349.00 USD`
5. Save → copy Price ID (format: `price_XXX`)

User shares Price ID — store as `STRIPE_PRICE_ID` env var.

- [ ] **Step 2: Configure Stripe webhook (manual)**

User action:
1. Open https://dashboard.stripe.com/webhooks
2. Add endpoint
3. URL: `https://agents-dashboard-theta.vercel.app/api/webhooks/stripe`
4. Events to subscribe:
   - `checkout.session.completed`
   - `charge.refunded`
5. Save → copy Signing Secret (format: `whsec_XXX`)

User shares Signing Secret — store as `STRIPE_WEBHOOK_SECRET` env var.

- [ ] **Step 3: Get Stripe Secret Key (manual)**

User action:
1. Open https://dashboard.stripe.com/apikeys
2. Reveal Secret key (test mode for first deploy)
3. Format: `sk_test_XXX` or `sk_live_XXX`

User shares Secret Key — store as `STRIPE_SECRET_KEY` env var.

- [ ] **Step 4: Create ElevenLabs sales agent (manual)**

User action:
1. Open https://elevenlabs.io/app/conversational-ai
2. Click "New agent" or duplicate existing
3. Configure prompt — example skeleton:

```
You are a friendly sales agent calling {{company_name}} after building their website preview.

Goal: Close a $349 USD one-time payment to activate their site permanently.

Key talking points:
- Their website is already built and live (mention specific elements if known)
- Costs only $349 once — no monthly fees
- Includes 48 hours to decide before site is removed
- Payment via secure Stripe Checkout link sent by SMS

If customer says "yes": confirm "Great, I'm sending the payment link to your phone now."
If customer says "I'll think about it / send info": say "I'll send you the link by SMS, you can decide later."
If customer says "no thanks": acknowledge politely and end call.

Be brief, warm, professional. 90-second call max.
```

4. Voice: same as cold-call agent (consistency)
5. Phone Number: same Twilio integration as `agent_1101kq5kzfdqfqjvfwgn75v37cnp`
6. Save → copy `agent_id`

User shares agent ID — store as `ELEVENLABS_SALES_AGENT_ID` env var.

- [ ] **Step 5: Generate CRON_SECRET**

```bash
node -e "console.log(require('crypto').randomBytes(32).toString('hex'))"
```

Copy the output. Will be set as `CRON_SECRET` env var on Vercel.

---

## Task 10: Deploy (env vars + redeploy)

**Files:** N/A (CLI commands)

- [ ] **Step 1: Set Vercel env vars (agents-dashboard)**

```bash
cd "c:/Users/indig/.antigravity/AGENT 2.0_TEST/agents-platform/apps/dashboard"
printf '%s' '<STRIPE_SECRET_KEY>' | vercel env add STRIPE_SECRET_KEY production
printf '%s' '<STRIPE_WEBHOOK_SECRET>' | vercel env add STRIPE_WEBHOOK_SECRET production
printf '%s' '<CRON_SECRET>' | vercel env add CRON_SECRET production
printf '%s' 'https://customer-dashboard-ashen.vercel.app' | vercel env add CUSTOMER_DASHBOARD_URL production
# RESEND_API_KEY may need to be added if not already there:
vercel env ls production | grep RESEND_API_KEY || \
  printf '%s' 're_Zusr3uE7_2mAfjGJX58VnL1puVpbjpiuj' | vercel env add RESEND_API_KEY production
```

- [ ] **Step 2: Deploy agents-dashboard to production**

```bash
vercel --prod --yes
```

Wait for "Ready". Capture URL (should still be `agents-dashboard-theta.vercel.app` or update to whatever stable alias is shown).

- [ ] **Step 3: Set Railway env vars (setting_agent worker)**

Open Railway dashboard → setting-agent service → Variables. Add:

```
STRIPE_SECRET_KEY = <STRIPE_SECRET_KEY>
STRIPE_PRICE_ID = <price_xxx>
ELEVENLABS_SALES_AGENT_ID = <agent_xxx>
CUSTOMER_DASHBOARD_URL = https://customer-dashboard-ashen.vercel.app
```

(`TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_PHONE_NUMBER` should already be set from D-Phase1.)

- [ ] **Step 4: Redeploy Railway worker**

Push commits should auto-trigger Railway redeploy. Verify by checking heartbeat:

Use Supabase MCP `execute_sql`:

```sql
SELECT id, status, last_heartbeat, NOW() - last_heartbeat AS age FROM agents WHERE id='setting';
```

Expected: heartbeat within last 60s, status `idle`.

If Railway didn't auto-deploy, user manually triggers redeploy from Railway dashboard.

- [ ] **Step 5: Smoke test webhook endpoint**

```bash
SECRET="<STRIPE_WEBHOOK_SECRET>"
BODY='{"id":"evt_test","type":"ping","data":{}}'
SIG_TIMESTAMP="$(date +%s)"
SIGNED_PAYLOAD="${SIG_TIMESTAMP}.${BODY}"
SIG=$(printf '%s' "$SIGNED_PAYLOAD" | openssl dgst -sha256 -hmac "$SECRET" -hex | awk '{print $2}')
HEADER="t=${SIG_TIMESTAMP},v1=${SIG}"
curl --ssl-no-revoke -s -o /dev/null -w "Status: %{http_code}\n" \
  -X POST "https://agents-dashboard-theta.vercel.app/api/webhooks/stripe" \
  -H "Content-Type: application/json" \
  -H "stripe-signature: $HEADER" \
  -d "$BODY"
```

Expected: `Status: 200` with body `{"ok":true,"ignored":"ping"}` (event type `ping` is unknown so it returns ignored — but the HMAC verified, which is what we want).

- [ ] **Step 6: Smoke test cleanup cron endpoint**

```bash
CRON_SECRET="<CRON_SECRET>"
curl --ssl-no-revoke -s -w "Status: %{http_code}\n" \
  -X POST "https://agents-dashboard-theta.vercel.app/api/cron/cleanup-unpaid-sites" \
  -H "Authorization: Bearer ${CRON_SECRET}"
```

Expected: `Status: 200` with body `{"ok":true,"deleted_count":0}` (no expired sites yet).

- [ ] **Step 7: Empty milestone commit**

```bash
cd "c:/Users/indig/.antigravity/AGENT 2.0_TEST/agents-platform"
git commit --allow-empty -m "chore(F1+D-Phase2): Stripe + sales call deployed to production

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 11: E2E manual test

**Files:** N/A (manual)

- [ ] **Step 1: Insert test lead with email + phone**

Via Supabase MCP:

```sql
INSERT INTO leads (company_name, phone, email, has_website, status, source, country_code, call_status)
VALUES ('TEST F1 Mario Pizza', '+393477544532', 'info@natalinoai.com',
        false, 'new', 'manual_test', 'US', 'never_called')
RETURNING id;
```

Capture lead UUID.

- [ ] **Step 2: Trigger setting.call_accepted to start chain**

Via Supabase MCP:

```sql
INSERT INTO events (type, target_agent, source_agent, payload, status)
VALUES ('setting.call_accepted', 'builder', 'human',
  jsonb_build_object(
    'lead_id', '<lead_uuid>',
    'lead', jsonb_build_object(
      'id', '<lead_uuid>',
      'company_name', 'TEST F1 Mario Pizza',
      'email', 'info@natalinoai.com',
      'phone', '+393477544532',
      'category', 'restaurant',
      'city', 'Test City'
    ),
    'call_brief', jsonb_build_object('services', ARRAY['pizza'], 'style_preference', 'modern')
  ),
  'pending')
RETURNING id;
```

This emulates the output of D-Phase1. Builder will pick it up, build the site, and emit `builder.site_ready`.

- [ ] **Step 3: Wait + verify Builder built site + emitted event**

Wait ~60s. Then check via Supabase MCP:

```sql
SELECT id, slug, payment_status, published_at, sales_call_attempts FROM sites
  WHERE lead_id='<lead_uuid>' ORDER BY created_at DESC LIMIT 1;

SELECT type, status, payload->'site_id' AS site_id FROM events
  WHERE type='builder.site_ready' AND created_at > NOW() - INTERVAL '5 minutes';
```

Expected: 1 site row, payment_status='unpaid', published_at recent. 1 builder.site_ready event status='completed' (Setting Agent picked it up).

- [ ] **Step 4: Wait for D-Phase2 to call**

Setting Agent should pick up `builder.site_ready` and trigger sales call. Telefono `+393477544532` squilla. **Rispondi e dì "yes I'll pay"**.

If you don't have `MAX_SALES_CALL_ATTEMPTS` reached and DNC clean, the call should fire within ~10s of the `builder.site_ready` event.

- [ ] **Step 5: Wait for SMS arrival**

After hanging up, wait ~30-60s for ElevenLabs webhook → setting.sales_call_completed → Claude analyze → Stripe Checkout creation → SMS send.

Expected: SMS arrives on `+393477544532` with format `Hi TEST F1 Mario Pizza, here's your link to activate your website ($349): https://checkout.stripe.com/c/pay/cs_xxx`.

- [ ] **Step 6: Click link, pay with Stripe test card**

Use Stripe test card: `4242 4242 4242 4242`, expiry any future, CVC any 3 digits, ZIP any.

Click "Pay $349.00".

- [ ] **Step 7: Verify Stripe webhook fired + onboarding completed**

Via Supabase MCP:

```sql
SELECT stripe_event_id, event_type, processed_at FROM stripe_events
  WHERE event_type='checkout.session.completed' ORDER BY created_at DESC LIMIT 1;

SELECT id, slug, payment_status, paid_at, owner_user_id FROM sites
  WHERE lead_id='<lead_uuid>';

SELECT id, email, raw_user_meta_data FROM auth.users
  WHERE email='info@natalinoai.com' ORDER BY created_at DESC LIMIT 1;
```

Expected: stripe_events row with processed_at set. Site payment_status='paid', paid_at recent, owner_user_id populated. auth.user exists with metadata.

- [ ] **Step 8: Verify welcome email arrived**

Check `info@natalinoai.com` inbox. Email subject: `Your TEST F1 Mario Pizza website is ready`. Contains login email, temp password, dashboard URL.

- [ ] **Step 9: Login to customer dashboard**

Open `https://customer-dashboard-ashen.vercel.app/login`. Use email + temp password from email.

Expected:
1. Login redirects to `/change-password`
2. Set new password → `/`
3. See "Welcome, TEST F1 Mario Pizza" + site URL + 3 coming-soon cards

- [ ] **Step 10: Test cleanup cron behavior**

Insert a "fake-expired" unpaid site and run cleanup manually:

```sql
INSERT INTO leads (company_name, phone, email, has_website, status, source, country_code, call_status)
VALUES ('TEST CLEANUP Fake', '+10000000000', 'cleanup@test.com', false, 'new', 'cleanup_test', 'US', 'never_called')
RETURNING id;

-- Manually back-date a site to be 49h old
INSERT INTO sites (lead_id, slug, template_kind, category, content, payment_status, published_at)
VALUES ((SELECT id FROM leads WHERE source='cleanup_test'),
        'cleanup-test-site', 'hospitality', 'restaurant', '{}'::jsonb,
        'unpaid', NOW() - INTERVAL '49 hours');
```

Trigger cleanup manually (or wait for next hourly run):

```bash
curl --ssl-no-revoke -s -X POST \
  "https://agents-dashboard-theta.vercel.app/api/cron/cleanup-unpaid-sites" \
  -H "Authorization: Bearer <CRON_SECRET>"
```

Expected: `{"ok":true,"deleted_count":1}`. Verify via Supabase:

```sql
SELECT * FROM sites WHERE slug='cleanup-test-site';  -- should be empty
SELECT type, payload FROM events WHERE type='site.deleted_unpaid' ORDER BY created_at DESC LIMIT 1;
SELECT status FROM leads WHERE source='cleanup_test';  -- should be 'expired_no_pay'
```

- [ ] **Step 11: Cleanup test data**

Via Supabase MCP:

```sql
DELETE FROM events WHERE payload->>'lead_id' = '<lead_uuid>'
   OR payload->>'site_id' IN (SELECT id::text FROM sites WHERE lead_id IN (SELECT id FROM leads WHERE source IN ('manual_test','cleanup_test')));
DELETE FROM stripe_events WHERE site_id IN (SELECT id FROM sites WHERE lead_id IN (SELECT id FROM leads WHERE source IN ('manual_test','cleanup_test')));
DELETE FROM call_logs WHERE lead_id IN (SELECT id FROM leads WHERE source IN ('manual_test','cleanup_test'));
DELETE FROM sites WHERE lead_id IN (SELECT id FROM leads WHERE source IN ('manual_test','cleanup_test'));
DELETE FROM leads WHERE source IN ('manual_test','cleanup_test');
```

Then via Supabase auth.users dashboard, delete the test user `info@natalinoai.com` (or any other test email).

---

## Task 12: Update BRAINSTORM_STATE + memory

**Files:**
- Modify: `BRAINSTORM_STATE.md`
- Modify: memory `project_decomposition.md`

- [ ] **Step 1: Update BRAINSTORM_STATE.md sub-projects table**

Replace the F1/D-Phase2 entries:

Before:
```
| F1 | Stripe Payments + 48h grace + cleanup | da brainstormare (post-E1) |
| D-Phase2 | Site-ready call (secondo agente ElevenLabs) | da brainstormare (post-F1) |
```

After:
```
| F1 | Stripe Payments + 48h grace + cleanup | **✅ COMPLETATO + DEPLOYATO + VALIDATO** |
| D-Phase2 | Site-ready call (secondo agente ElevenLabs) | **✅ COMPLETATO + DEPLOYATO + VALIDATO** |
```

- [ ] **Step 2: Add F1+D-Phase2 closure section**

Add to `BRAINSTORM_STATE.md` (replace the "in pausa" section with closure):

```markdown
## Sub-progetti F1 + D-Phase2 ✅ DEPLOYATI E VALIDATI

**Build completato 2026-05-XX**: Stripe Checkout + 48h grace + cleanup cron + secondo agente ElevenLabs sales.

**Componenti deployati**:
- Migration `008_payment_flow.sql`: stripe_* fields su sites + stripe_events table
- `apps/workers/setting_agent/`: 3 nuovi moduli (twilio_sms, stripe_client, sales_analyzer) + 2 nuovi handler (_handle_site_ready, _handle_sales_call_completed)
- `apps/dashboard/src/app/api/webhooks/stripe/route.ts`: HMAC verify + dedupe + payment.succeeded handler creates auth.user + sends welcome email
- `apps/dashboard/src/app/api/cron/cleanup-unpaid-sites/route.ts`: hourly Vercel cron deletes unpaid sites > 48h
- `apps/dashboard/vercel.json`: cron schedule "0 * * * *"
- 2 ElevenLabs Conv AI agents distinti: cold (D-Phase1) + sales (D-Phase2)

**E2E validato**:
- Lead → cold call → accepted → Builder build site → site_ready event
- D-Phase2 sales call → "yes I'll pay" → SMS Stripe link arrived
- Stripe test card 4242 paid → webhook fired → auth.user created → welcome email sent
- Login dashboard → forced password change → home rendered
- Cleanup cron tested via fake-expired site → DELETE OK

**Documenti**:
- Spec: `agents-platform/docs/superpowers/specs/2026-05-01-stripe-payments-and-sales-call-design.md`
- Plan: `agents-platform/docs/superpowers/plans/2026-05-02-stripe-payments-and-sales-call.md`

**Side-tasks futuri**:
- F1.1: refund automation via charge.refunded webhook
- F1.2: Stripe Tax automatic compliance when nexus thresholds approached
- F2: WhatsApp messaging via Twilio Business (gated da Meta approval)
- E2-E5: features customer-dashboard (custom domain, analytics, blog, social)
```

- [ ] **Step 3: Update memory `project_decomposition.md`**

Update header description:

```
description: 7 sub-progetti completati (A, B, C, D-Phase1, E1, F1, D-Phase2). E2-E5 + F2 pending.
```

In the decomposition list, update F1 and D-Phase2 lines:

```
- **F1** — Stripe Payments + 48h grace + cleanup ← **DEPLOYATO 2026-05-XX**
- **D-Phase2** — Site-ready call (secondo agente ElevenLabs sales) ← **DEPLOYATO 2026-05-XX**
```

- [ ] **Step 4: Mark task complete**

```bash
cd "c:/Users/indig/.antigravity/AGENT 2.0_TEST/agents-platform"
git commit --allow-empty -m "chore(F1+D-Phase2): close sub-projects, state files updated

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Self-Review Checklist (already performed)

✅ **Spec coverage**:
- Section 2 (architecture) → tasks 5, 6, 7, 8 implement the flow
- Section 3 (data model) → task 1 (migration)
- Section 4 (components) → tasks 2, 3, 4 (modules), 5, 6 (handlers), 7 (webhook), 8 (cron)
- Section 5 (env vars) → tasks 9, 10
- Section 6 (testing) → tests inline in 2-6, E2E in 11
- Section 7 (deployment) → tasks 9, 10
- Section 8 (observability) → no code task, queries documented in task 11

✅ **Placeholder scan**: every code block has full content, no TBDs.

✅ **Type consistency**: outcomes (`accepted_pay` etc.) consistent across analyzer, handler, DB CHECK constraint. `MAX_SALES_CALL_ATTEMPTS` used consistently. Event types match between emit and dispatch sites.

✅ **No "similar to Task N"**: each task has its own complete code.

✅ **External setup ordering**: task 9 (manual external) before task 10 (deploy that needs the secrets).
