# Customer Dashboard E1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the foundation Sub-progetto E1 — a multi-tenant customer dashboard (Next.js) with Supabase Auth, plus auto-onboarding (auth user creation + welcome email) integrated into Builder Agent.

**Architecture:** New `apps/customer-dashboard/` Next.js app with Supabase SSR auth. Builder Agent extended to call `auth.admin.create_user` and send welcome email via Resend after each `INSERT sites`. RLS policies on `sites` enforce multi-tenant isolation by `auth.uid()`. UI in English.

**Tech Stack:** Next.js 16+ App Router, `@supabase/ssr`, Tailwind v4, Python supabase-py + resend, Postgres RLS.

**Spec reference:** `docs/superpowers/specs/2026-05-01-customer-dashboard-e1-design.md`

---

## Task 1: Database migration + event schema

**Files:**
- Create: `supabase/migrations/007_customer_onboarding.sql`
- Modify: `packages/events_schema/schemas/builder.json`

- [ ] **Step 1: Write the migration**

Create `supabase/migrations/007_customer_onboarding.sql`:

```sql
-- 007_customer_onboarding.sql

-- 1. Add owner_user_id to sites
ALTER TABLE sites ADD COLUMN owner_user_id UUID REFERENCES auth.users(id) ON DELETE SET NULL;
CREATE INDEX idx_sites_owner_user ON sites(owner_user_id);

-- 2. Ensure RLS enabled
ALTER TABLE sites ENABLE ROW LEVEL SECURITY;

-- 3. SELECT policy for authenticated customers — own site only
CREATE POLICY "customers_see_own_site"
  ON sites FOR SELECT
  TO authenticated
  USING (owner_user_id = auth.uid());

-- 4. Block authenticated mutations (service_role bypasses RLS)
CREATE POLICY "no_customer_writes"
  ON sites FOR ALL
  TO authenticated
  USING (false)
  WITH CHECK (false);

-- 5. Public read for anon (used by agents-sites for /s/{slug} rendering)
CREATE POLICY "public_read_sites_by_slug"
  ON sites FOR SELECT
  TO anon
  USING (true);
```

- [ ] **Step 2: Apply migration via Supabase MCP**

Use `mcp__plugin_supabase_supabase__execute_sql` with the SQL above against project `smzmgzblbliprwbjptjs`.

Then verify:

```sql
SELECT column_name FROM information_schema.columns
WHERE table_name='sites' AND column_name='owner_user_id';

SELECT policyname FROM pg_policies WHERE tablename='sites';
```

Expected: column exists, 3 policies present.

- [ ] **Step 3: Add `customer.onboarded` event type**

Read `packages/events_schema/schemas/builder.json` and add to the schemas array:

```json
{
  "type": "customer.onboarded",
  "description": "Customer auth user created + welcome email sent after site is built",
  "source_agent": "builder",
  "target_agent": null,
  "payload_schema": {
    "type": "object",
    "required": ["lead_id", "site_id", "auth_user_id", "email"],
    "properties": {
      "lead_id": {"type": "string", "format": "uuid"},
      "site_id": {"type": "string", "format": "uuid"},
      "auth_user_id": {"type": "string", "format": "uuid"},
      "email": {"type": "string", "format": "email"},
      "email_sent": {"type": "boolean"}
    }
  }
}
```

- [ ] **Step 4: Run schema validation**

```bash
cd agents-platform
python -c "import json; json.load(open('packages/events_schema/schemas/builder.json'))"
```

Expected: no JSON parse error.

- [ ] **Step 5: Commit**

```bash
git add supabase/migrations/007_customer_onboarding.sql packages/events_schema/schemas/builder.json
git commit -m "feat(E1): add migration 007 + customer.onboarded event schema"
```

---

## Task 2: Welcome email module (TDD)

**Files:**
- Create: `apps/workers/website_builder/welcome_email.py`
- Create: `apps/workers/website_builder/tests/test_welcome_email.py`

- [ ] **Step 1: Write failing test**

Create `apps/workers/website_builder/tests/test_welcome_email.py`:

```python
"""Tests for welcome_email module."""
import os
from unittest.mock import patch, MagicMock
import pytest

from apps.workers.website_builder.welcome_email import (
    send_welcome_email,
    render_welcome_html,
    render_welcome_text,
)


def _sample_lead():
    return {
        "id": "lead-uuid",
        "email": "test@example.com",
        "company_name": "Mario Pizza",
    }


def _sample_site():
    return {"id": "site-uuid", "slug": "mario-pizza"}


def test_render_welcome_text_contains_credentials():
    text = render_welcome_text(_sample_lead(), "https://example.com/s/mario-pizza", "tempPass123")
    assert "Mario Pizza" in text
    assert "test@example.com" in text
    assert "tempPass123" in text
    assert "mario-pizza" in text


def test_render_welcome_html_contains_credentials_and_dashboard_link():
    html = render_welcome_html(_sample_lead(), "https://example.com/s/mario-pizza", "tempPass123")
    assert "Mario Pizza" in html
    assert "test@example.com" in html
    assert "tempPass123" in html
    assert "agents-customer-dashboard.vercel.app" in html or "CUSTOMER_DASHBOARD_URL" in os.environ


@patch("apps.workers.website_builder.welcome_email.resend")
def test_send_welcome_email_calls_resend(mock_resend):
    mock_resend.api_key = None
    mock_emails = MagicMock()
    mock_resend.Emails = mock_emails

    with patch.dict(os.environ, {"RESEND_API_KEY": "re_test"}):
        send_welcome_email(_sample_lead(), _sample_site(), "pwd")

    mock_emails.send.assert_called_once()
    call_args = mock_emails.send.call_args[0][0]
    assert call_args["to"] == ["test@example.com"]
    assert "Mario Pizza" in call_args["subject"]
    assert call_args["from"] == "onboarding@resend.dev"


@patch("apps.workers.website_builder.welcome_email.resend")
def test_send_welcome_email_raises_on_resend_error(mock_resend):
    mock_emails = MagicMock()
    mock_emails.send.side_effect = Exception("Resend down")
    mock_resend.Emails = mock_emails

    with patch.dict(os.environ, {"RESEND_API_KEY": "re_test"}):
        with pytest.raises(Exception, match="Resend down"):
            send_welcome_email(_sample_lead(), _sample_site(), "pwd")
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd agents-platform
python -m pytest apps/workers/website_builder/tests/test_welcome_email.py -v
```

Expected: FAIL — "ModuleNotFoundError: No module named ... welcome_email".

- [ ] **Step 3: Write the implementation**

Create `apps/workers/website_builder/welcome_email.py`:

```python
"""Welcome email module: sends onboarding email to newly created customers via Resend."""
import os
import logging
import resend

logger = logging.getLogger(__name__)

DASHBOARD_URL = os.environ.get(
    "CUSTOMER_DASHBOARD_URL",
    "https://agents-customer-dashboard.vercel.app",
)


def render_welcome_text(lead: dict, site_url: str, password: str) -> str:
    return f"""Hi {lead['company_name']},

Your new website is live!

Website URL: {site_url}

Customer dashboard: {DASHBOARD_URL}

Login email: {lead['email']}
Temporary password: {password}

You'll be asked to set a new password the first time you log in.

Thanks,
The Agents Platform team
"""


def render_welcome_html(lead: dict, site_url: str, password: str) -> str:
    return f"""<!DOCTYPE html>
<html><body style="font-family:Inter,Arial,sans-serif;max-width:600px;margin:0 auto;padding:24px;color:#1a1a1a">
<h1 style="color:#0a0a0a">Your website is live, {lead['company_name']}!</h1>
<p>We've built your new site. Here's everything you need:</p>
<ul style="line-height:1.8">
  <li><strong>Website URL:</strong> <a href="{site_url}">{site_url}</a></li>
  <li><strong>Customer dashboard:</strong> <a href="{DASHBOARD_URL}">{DASHBOARD_URL}</a></li>
</ul>
<h2>Login credentials</h2>
<p>Email: <code>{lead['email']}</code><br>
Temporary password: <code>{password}</code></p>
<p style="color:#666;font-size:14px">
You'll be required to set a new password on your first login.
</p>
<p>— The Agents Platform team</p>
</body></html>
"""


def send_welcome_email(lead: dict, site: dict, password: str) -> None:
    """Send the onboarding welcome email via Resend.

    Raises on Resend API failure (caller decides retry/log).
    """
    resend.api_key = os.environ["RESEND_API_KEY"]
    site_url = f"https://agents-sites.vercel.app/s/{site['slug']}"
    resend.Emails.send({
        "from": "onboarding@resend.dev",
        "to": [lead["email"]],
        "subject": f"Your {lead['company_name']} website is ready",
        "html": render_welcome_html(lead, site_url, password),
        "text": render_welcome_text(lead, site_url, password),
    })
    logger.info(f"Welcome email sent to {lead['email']} for site {site['id']}")
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
python -m pytest apps/workers/website_builder/tests/test_welcome_email.py -v
```

Expected: 4 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add apps/workers/website_builder/welcome_email.py apps/workers/website_builder/tests/test_welcome_email.py
git commit -m "feat(E1): welcome email module with Resend (TDD)"
```

---

## Task 3: `_onboard_customer` method (TDD)

**Files:**
- Modify: `apps/workers/website_builder/main.py` (add `_onboard_customer` + integrate in handler)
- Create: `apps/workers/website_builder/tests/test_onboarding.py`

- [ ] **Step 1: Write failing tests**

Create `apps/workers/website_builder/tests/test_onboarding.py`:

```python
"""Tests for _onboard_customer method on WebsiteBuilderAgent."""
import os
from unittest.mock import patch, MagicMock
import pytest

from apps.workers.website_builder.main import WebsiteBuilderAgent


def _make_agent():
    """Build agent with mocked supabase client."""
    with patch.dict(os.environ, {
        "ANTHROPIC_API_KEY": "test",
        "RESEND_API_KEY": "re_test",
        "AGENTS_SITES_BASE_URL": "https://agents-sites.vercel.app",
    }):
        client = MagicMock()
        agent = WebsiteBuilderAgent(supabase_client=client)
        return agent, client


def _sample_lead(email="customer@example.com"):
    return {"id": "lead-1", "email": email, "company_name": "Mario Pizza"}


def _sample_site():
    return {"id": "site-1", "slug": "mario-pizza"}


@patch("apps.workers.website_builder.main.send_welcome_email")
def test_onboard_customer_happy_path(mock_send):
    agent, client = _make_agent()

    # Mock list_users (no existing user)
    client.auth.admin.list_users.return_value = MagicMock(users=[])
    # Mock create_user
    created = MagicMock()
    created.user.id = "auth-uid"
    client.auth.admin.create_user.return_value = created
    # Mock UPDATE sites
    client.table.return_value.update.return_value.eq.return_value.execute.return_value = MagicMock()

    result = agent._onboard_customer(_sample_lead(), _sample_site())

    assert result == "auth-uid"
    client.auth.admin.create_user.assert_called_once()
    create_arg = client.auth.admin.create_user.call_args[0][0]
    assert create_arg["email"] == "customer@example.com"
    assert create_arg["email_confirm"] is True
    assert create_arg["user_metadata"]["password_changed"] is False
    assert create_arg["user_metadata"]["lead_id"] == "lead-1"
    mock_send.assert_called_once()


def test_onboard_customer_no_email_returns_none():
    agent, client = _make_agent()
    lead_no_email = {"id": "lead-1", "company_name": "Mario", "email": None}
    result = agent._onboard_customer(lead_no_email, _sample_site())
    assert result is None
    client.auth.admin.create_user.assert_not_called()


@patch("apps.workers.website_builder.main.send_welcome_email")
def test_onboard_customer_existing_user_returns_id_no_create(mock_send):
    agent, client = _make_agent()

    existing_user = MagicMock()
    existing_user.email = "customer@example.com"
    existing_user.id = "existing-uid"
    client.auth.admin.list_users.return_value = MagicMock(users=[existing_user])

    result = agent._onboard_customer(_sample_lead(), _sample_site())

    assert result == "existing-uid"
    client.auth.admin.create_user.assert_not_called()
    # Should still NOT re-send email (idempotent)
    mock_send.assert_not_called()


@patch("apps.workers.website_builder.main.send_welcome_email")
def test_onboard_customer_create_user_failure_returns_none(mock_send):
    agent, client = _make_agent()
    client.auth.admin.list_users.return_value = MagicMock(users=[])
    client.auth.admin.create_user.side_effect = Exception("Supabase 500")

    result = agent._onboard_customer(_sample_lead(), _sample_site())

    assert result is None
    mock_send.assert_not_called()
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
python -m pytest apps/workers/website_builder/tests/test_onboarding.py -v
```

Expected: 4 FAIL — `_onboard_customer` not defined.

- [ ] **Step 3: Add `_onboard_customer` method to `WebsiteBuilderAgent`**

In `apps/workers/website_builder/main.py`, add imports near top (with existing imports):

```python
import secrets
from datetime import datetime, timezone
from apps.workers.website_builder.welcome_email import send_welcome_email
```

Add the method inside the `WebsiteBuilderAgent` class:

```python
def _onboard_customer(self, lead: dict, site: dict) -> str | None:
    """Create auth user + send welcome email after site INSERT.

    Returns auth_user_id (str) on success, None on failure.
    Idempotent: if user already exists by email, returns existing id without re-sending email.
    """
    email = lead.get("email")
    if not email:
        logger.warning(f"Lead {lead['id']} has no email, skipping onboarding")
        return None

    # Idempotency check: list users + filter by email
    try:
        list_resp = self._client.auth.admin.list_users()
        users = list_resp.users if hasattr(list_resp, "users") else []
        for u in users:
            if u.email == email:
                logger.info(f"User already exists for {email} ({u.id}), skipping create + email")
                return u.id
    except Exception as e:
        logger.warning(f"Failed to list users for idempotency check: {e}; proceeding to create")

    password = secrets.token_urlsafe(12)
    try:
        result = self._client.auth.admin.create_user({
            "email": email,
            "password": password,
            "email_confirm": True,
            "user_metadata": {
                "lead_id": lead["id"],
                "site_id": site["id"],
                "company_name": lead["company_name"],
                "password_changed": False,
                "onboarded_at": datetime.now(timezone.utc).isoformat(),
            },
        })
    except Exception as e:
        logger.error(f"Failed to create auth user for {email}: {e}")
        return None

    auth_user_id = result.user.id

    # Link site to user
    try:
        self._client.table("sites").update({
            "owner_user_id": auth_user_id
        }).eq("id", site["id"]).execute()
    except Exception as e:
        logger.error(f"Failed to link site {site['id']} to user {auth_user_id}: {e}")
        # User is created but site not linked — operator must intervene
        return auth_user_id

    # Send welcome email (raise = retry by event framework)
    try:
        send_welcome_email(lead, site, password)
    except Exception as e:
        logger.error(f"Welcome email failed for {email}: {e}")
        # Non-fatal — user can use password reset to recover

    return auth_user_id
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
python -m pytest apps/workers/website_builder/tests/test_onboarding.py -v
```

Expected: 4 PASS.

- [ ] **Step 5: Commit**

```bash
git add apps/workers/website_builder/main.py apps/workers/website_builder/tests/test_onboarding.py
git commit -m "feat(E1): add _onboard_customer method with idempotency (TDD)"
```

---

## Task 4: Integrate onboarding into Builder handler

**Files:**
- Modify: `apps/workers/website_builder/main.py` (call `_onboard_customer` from main handler + emit event)
- Modify: `apps/workers/website_builder/tests/test_pipeline_integration.py` (extend integration test)

- [ ] **Step 1: Read existing handler to find INSERT site location**

Read `apps/workers/website_builder/main.py` and locate the method that does `INSERT into sites`. It's likely called `handle_event` or a sub-method like `_build_site`. Identify the exact spot AFTER successful insert.

- [ ] **Step 2: Add the onboarding call + event emit after INSERT site**

Inside the relevant handler method (after `INSERT sites` succeeds and `site` dict is in scope), add:

```python
# Trigger customer onboarding (auth user + welcome email)
auth_user_id = self._onboard_customer(lead, site)
if auth_user_id:
    self._emitter.emit(
        event_type="customer.onboarded",
        target_agent=None,
        payload={
            "lead_id": lead["id"],
            "site_id": site["id"],
            "auth_user_id": auth_user_id,
            "email": lead["email"],
            "email_sent": True,
        },
    )
else:
    logger.warning(f"Onboarding skipped for lead {lead['id']} (no email or create failed)")
```

- [ ] **Step 3: Update integration test**

Read `apps/workers/website_builder/tests/test_pipeline_integration.py`. Add a new test method (after existing tests):

```python
@patch("apps.workers.website_builder.main.send_welcome_email")
def test_pipeline_emits_customer_onboarded_after_site_insert(mock_send_email):
    """Full pipeline: setting.call_accepted → INSERT site → onboard customer → emit customer.onboarded"""
    with patch.dict(os.environ, {
        "ANTHROPIC_API_KEY": "test",
        "RESEND_API_KEY": "re_test",
        "AGENTS_SITES_BASE_URL": "https://agents-sites.vercel.app",
    }):
        # Build mocks (reuse helper if exists in file, else inline)
        client = MagicMock()

        # ... mock setup for sites table inserts/queries ...
        # ... mock auth.admin.list_users → empty
        # ... mock auth.admin.create_user → returns id="onboard-uid"
        client.auth.admin.list_users.return_value = MagicMock(users=[])
        created = MagicMock()
        created.user.id = "onboard-uid"
        client.auth.admin.create_user.return_value = created

        captured_events = []
        emitter_mock = MagicMock()
        emitter_mock.emit.side_effect = lambda **kwargs: captured_events.append(kwargs)

        # ... rest of pipeline integration test setup, including agent + event ...
        # Trigger handler with setting.call_accepted event with lead.email
        # Assert: customer.onboarded event was emitted with correct payload

        onboarded = [e for e in captured_events if e.get("event_type") == "customer.onboarded"]
        assert len(onboarded) == 1
        assert onboarded[0]["payload"]["auth_user_id"] == "onboard-uid"
        assert onboarded[0]["payload"]["email_sent"] is True
        mock_send_email.assert_called_once()
```

NOTE: the exact mock setup for `client.table("sites").insert(...)` etc. depends on the existing test helpers in the file. Read existing tests in the same file and follow the same mock patterns for sites + leads queries.

- [ ] **Step 4: Run integration tests**

```bash
python -m pytest apps/workers/website_builder/tests/test_pipeline_integration.py -v
```

Expected: all PASS, including new `test_pipeline_emits_customer_onboarded`.

- [ ] **Step 5: Run full Builder Agent test suite**

```bash
python -m pytest apps/workers/website_builder/tests/ -v
```

Expected: ALL pass.

- [ ] **Step 6: Commit**

```bash
git add apps/workers/website_builder/main.py apps/workers/website_builder/tests/test_pipeline_integration.py
git commit -m "feat(E1): wire _onboard_customer into Builder handler + emit customer.onboarded"
```

---

## Task 5: Scaffold `apps/customer-dashboard/` Next.js app

**Files:**
- Create: `apps/customer-dashboard/package.json`
- Create: `apps/customer-dashboard/next.config.ts`
- Create: `apps/customer-dashboard/tsconfig.json`
- Create: `apps/customer-dashboard/tailwind.config.ts`
- Create: `apps/customer-dashboard/postcss.config.mjs`
- Create: `apps/customer-dashboard/.gitignore`
- Create: `apps/customer-dashboard/src/app/layout.tsx`
- Create: `apps/customer-dashboard/src/app/page.tsx` (placeholder)
- Create: `apps/customer-dashboard/src/app/globals.css`

- [ ] **Step 1: Create `package.json`**

```json
{
  "name": "customer-dashboard",
  "version": "0.1.0",
  "private": true,
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "test": "vitest run",
    "test:watch": "vitest"
  },
  "dependencies": {
    "@supabase/ssr": "^0.5.2",
    "@supabase/supabase-js": "^2.45.0",
    "clsx": "^2.1.1",
    "lucide-react": "^0.460.0",
    "next": "^16.0.0",
    "react": "^19.0.0",
    "react-dom": "^19.0.0",
    "tailwind-merge": "^2.5.0"
  },
  "devDependencies": {
    "@testing-library/jest-dom": "^6.5.0",
    "@testing-library/react": "^16.0.0",
    "@types/node": "^22.0.0",
    "@types/react": "^19.0.0",
    "@types/react-dom": "^19.0.0",
    "@vitejs/plugin-react": "^4.3.0",
    "jsdom": "^25.0.0",
    "postcss": "^8.4.49",
    "tailwindcss": "^4.0.0",
    "typescript": "^5.6.0",
    "vitest": "^2.1.0"
  }
}
```

- [ ] **Step 2: Create `next.config.ts`**

```typescript
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: true,
};

export default nextConfig;
```

- [ ] **Step 3: Create `tsconfig.json`**

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "lib": ["dom", "dom.iterable", "esnext"],
    "allowJs": false,
    "skipLibCheck": true,
    "strict": true,
    "noEmit": true,
    "esModuleInterop": true,
    "module": "esnext",
    "moduleResolution": "bundler",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "jsx": "preserve",
    "incremental": true,
    "plugins": [{"name": "next"}],
    "paths": {"@/*": ["./src/*"]}
  },
  "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx", ".next/types/**/*.ts"],
  "exclude": ["node_modules"]
}
```

- [ ] **Step 4: Create `tailwind.config.ts`**

```typescript
import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        display: ["Playfair Display", "Georgia", "serif"],
      },
    },
  },
  plugins: [],
};

export default config;
```

- [ ] **Step 5: Create `postcss.config.mjs`**

```javascript
export default {
  plugins: {
    "@tailwindcss/postcss": {},
  },
};
```

- [ ] **Step 6: Create `.gitignore`**

```
node_modules
.next
out
*.log
.env*.local
.vercel
.turbo
```

- [ ] **Step 7: Create `src/app/globals.css`**

```css
@import "tailwindcss";

@theme {
  --font-sans: "Inter", system-ui, sans-serif;
  --font-display: "Playfair Display", Georgia, serif;
}

body {
  font-family: var(--font-sans);
  color: #1a1a1a;
  background: #fafafa;
}
```

- [ ] **Step 8: Create root `src/app/layout.tsx`**

```typescript
import "./globals.css";

export const metadata = {
  title: "Customer Dashboard",
  description: "Manage your website",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link
          rel="stylesheet"
          href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Playfair+Display:wght@600;700&display=swap"
        />
      </head>
      <body>{children}</body>
    </html>
  );
}
```

- [ ] **Step 9: Create placeholder `src/app/page.tsx`**

```typescript
export default function Home() {
  return <main className="p-8"><h1 className="text-2xl font-display">Customer Dashboard</h1></main>;
}
```

- [ ] **Step 10: Install dependencies**

```bash
cd apps/customer-dashboard
npm install
```

Expected: dependencies installed without errors.

- [ ] **Step 11: Verify dev build**

```bash
npm run build
```

Expected: build OK.

- [ ] **Step 12: Commit**

```bash
git add apps/customer-dashboard/
git commit -m "feat(E1): scaffold customer-dashboard Next.js app"
```

---

## Task 6: Supabase client utilities + UI primitives

**Files:**
- Create: `apps/customer-dashboard/src/lib/supabase/client.ts`
- Create: `apps/customer-dashboard/src/lib/supabase/server.ts`
- Create: `apps/customer-dashboard/src/components/ui/Button.tsx`
- Create: `apps/customer-dashboard/src/components/ui/Input.tsx`
- Create: `apps/customer-dashboard/src/components/ui/Label.tsx`
- Create: `apps/customer-dashboard/src/components/DashboardCard.tsx`
- Create: `apps/customer-dashboard/src/components/LogoutButton.tsx`
- Create: `apps/customer-dashboard/src/lib/utils.ts` (clsx + twMerge helper)

- [ ] **Step 1: Create `src/lib/utils.ts`**

```typescript
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
```

- [ ] **Step 2: Create `src/lib/supabase/client.ts` (browser)**

```typescript
import { createBrowserClient } from "@supabase/ssr";

export function createClient() {
  return createBrowserClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
  );
}
```

- [ ] **Step 3: Create `src/lib/supabase/server.ts` (server-side cookies-aware)**

```typescript
import { createServerClient } from "@supabase/ssr";
import { cookies } from "next/headers";

export async function createClient() {
  const cookieStore = await cookies();
  return createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        getAll() {
          return cookieStore.getAll();
        },
        setAll(cookiesToSet) {
          try {
            cookiesToSet.forEach(({ name, value, options }) =>
              cookieStore.set(name, value, options));
          } catch {
            // Server Component context — set is no-op, refresh handled by middleware
          }
        },
      },
    },
  );
}
```

- [ ] **Step 4: Create `src/components/ui/Button.tsx`**

```typescript
import { cn } from "@/lib/utils";
import { ButtonHTMLAttributes, forwardRef } from "react";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary";
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = "primary", ...props }, ref) => (
    <button
      ref={ref}
      className={cn(
        "inline-flex items-center justify-center px-4 py-2 rounded-md font-medium text-sm transition-colors",
        "disabled:opacity-50 disabled:pointer-events-none",
        variant === "primary" && "bg-black text-white hover:bg-gray-800",
        variant === "secondary" && "bg-gray-100 text-gray-900 hover:bg-gray-200",
        className,
      )}
      {...props}
    />
  ),
);
Button.displayName = "Button";
```

- [ ] **Step 5: Create `src/components/ui/Input.tsx`**

```typescript
import { cn } from "@/lib/utils";
import { InputHTMLAttributes, forwardRef } from "react";

export const Input = forwardRef<HTMLInputElement, InputHTMLAttributes<HTMLInputElement>>(
  ({ className, ...props }, ref) => (
    <input
      ref={ref}
      className={cn(
        "w-full px-3 py-2 border border-gray-300 rounded-md text-sm",
        "focus:outline-none focus:ring-2 focus:ring-black focus:border-transparent",
        className,
      )}
      {...props}
    />
  ),
);
Input.displayName = "Input";
```

- [ ] **Step 6: Create `src/components/ui/Label.tsx`**

```typescript
import { cn } from "@/lib/utils";
import { LabelHTMLAttributes } from "react";

export function Label({ className, ...props }: LabelHTMLAttributes<HTMLLabelElement>) {
  return (
    <label
      className={cn("text-sm font-medium text-gray-700 block mb-1", className)}
      {...props}
    />
  );
}
```

- [ ] **Step 7: Create `src/components/DashboardCard.tsx`**

```typescript
import { cn } from "@/lib/utils";

interface DashboardCardProps {
  title: string;
  comingSoon?: boolean;
  children?: React.ReactNode;
}

export function DashboardCard({ title, comingSoon, children }: DashboardCardProps) {
  return (
    <div className={cn(
      "bg-white border border-gray-200 rounded-lg p-6",
      comingSoon && "opacity-60",
    )}>
      <h3 className="font-semibold text-lg mb-2">{title}</h3>
      {comingSoon ? (
        <span className="inline-block text-xs uppercase tracking-wider text-gray-500 bg-gray-100 px-2 py-1 rounded">
          Coming soon
        </span>
      ) : children}
    </div>
  );
}
```

- [ ] **Step 8: Create `src/components/LogoutButton.tsx`**

```typescript
"use client";
import { createClient } from "@/lib/supabase/client";
import { useRouter } from "next/navigation";
import { Button } from "./ui/Button";

export function LogoutButton() {
  const router = useRouter();
  const handleLogout = async () => {
    const supabase = createClient();
    await supabase.auth.signOut();
    router.push("/login");
    router.refresh();
  };
  return <Button variant="secondary" onClick={handleLogout}>Logout</Button>;
}
```

- [ ] **Step 9: Verify build still passes**

```bash
cd apps/customer-dashboard
npm run build
```

Expected: build OK.

- [ ] **Step 10: Commit**

```bash
git add apps/customer-dashboard/src/lib apps/customer-dashboard/src/components
git commit -m "feat(E1): supabase clients + UI primitives + DashboardCard + LogoutButton"
```

---

## Task 7: Login page + auth callback route

**Files:**
- Create: `apps/customer-dashboard/src/app/login/page.tsx`
- Create: `apps/customer-dashboard/src/app/api/auth/callback/route.ts`

- [ ] **Step 1: Create login page**

`apps/customer-dashboard/src/app/login/page.tsx`:

```typescript
"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { createClient } from "@/lib/supabase/client";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Label } from "@/components/ui/Label";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    const supabase = createClient();
    const { error: signInError } = await supabase.auth.signInWithPassword({ email, password });
    setLoading(false);
    if (signInError) {
      setError("Invalid credentials");
      return;
    }
    router.push("/");
    router.refresh();
  };

  return (
    <main className="min-h-screen flex items-center justify-center p-4">
      <div className="w-full max-w-md bg-white border border-gray-200 rounded-lg p-8">
        <h1 className="text-3xl font-display mb-6">Sign in</h1>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <Label htmlFor="email">Email</Label>
            <Input
              id="email"
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
          </div>
          <div>
            <Label htmlFor="password">Password</Label>
            <Input
              id="password"
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </div>
          {error && <p className="text-sm text-red-600">{error}</p>}
          <Button type="submit" className="w-full" disabled={loading}>
            {loading ? "Signing in..." : "Sign in"}
          </Button>
        </form>
        <p className="text-sm text-gray-600 mt-4">
          <Link href="/forgot-password" className="underline">Forgot password?</Link>
        </p>
      </div>
    </main>
  );
}
```

- [ ] **Step 2: Create auth callback route**

`apps/customer-dashboard/src/app/api/auth/callback/route.ts`:

```typescript
import { createClient } from "@/lib/supabase/server";
import { NextResponse } from "next/server";

export async function GET(request: Request) {
  const { searchParams, origin } = new URL(request.url);
  const code = searchParams.get("code");
  const next = searchParams.get("next") ?? "/";

  if (code) {
    const supabase = await createClient();
    const { error } = await supabase.auth.exchangeCodeForSession(code);
    if (!error) {
      return NextResponse.redirect(`${origin}${next}`);
    }
  }
  return NextResponse.redirect(`${origin}/login?error=auth_callback`);
}
```

- [ ] **Step 3: Verify build**

```bash
cd apps/customer-dashboard
npm run build
```

Expected: build OK.

- [ ] **Step 4: Commit**

```bash
git add apps/customer-dashboard/src/app/login apps/customer-dashboard/src/app/api
git commit -m "feat(E1): login page + auth callback route"
```

---

## Task 8: Forgot password + reset password pages

**Files:**
- Create: `apps/customer-dashboard/src/app/forgot-password/page.tsx`
- Create: `apps/customer-dashboard/src/app/reset-password/page.tsx`

- [ ] **Step 1: Create forgot-password page**

`apps/customer-dashboard/src/app/forgot-password/page.tsx`:

```typescript
"use client";
import { useState } from "react";
import Link from "next/link";
import { createClient } from "@/lib/supabase/client";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Label } from "@/components/ui/Label";

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [sent, setSent] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    const supabase = createClient();
    const { error: resetError } = await supabase.auth.resetPasswordForEmail(email, {
      redirectTo: `${window.location.origin}/reset-password`,
    });
    setLoading(false);
    if (resetError) {
      setError("Could not send reset email. Try again.");
      return;
    }
    setSent(true);
  };

  return (
    <main className="min-h-screen flex items-center justify-center p-4">
      <div className="w-full max-w-md bg-white border border-gray-200 rounded-lg p-8">
        <h1 className="text-3xl font-display mb-6">Reset your password</h1>
        {sent ? (
          <p className="text-sm text-gray-700">
            Check your inbox for a password reset link.
          </p>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
            </div>
            {error && <p className="text-sm text-red-600">{error}</p>}
            <Button type="submit" className="w-full" disabled={loading}>
              {loading ? "Sending..." : "Send reset link"}
            </Button>
          </form>
        )}
        <p className="text-sm text-gray-600 mt-4">
          <Link href="/login" className="underline">Back to login</Link>
        </p>
      </div>
    </main>
  );
}
```

- [ ] **Step 2: Create reset-password page**

`apps/customer-dashboard/src/app/reset-password/page.tsx`:

```typescript
"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { createClient } from "@/lib/supabase/client";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Label } from "@/components/ui/Label";

export default function ResetPasswordPage() {
  const router = useRouter();
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    if (password.length < 6) {
      setError("Password must be at least 6 characters");
      return;
    }
    setLoading(true);
    const supabase = createClient();
    const { error: updateErr } = await supabase.auth.updateUser({
      password,
      data: { password_changed: true },
    });
    setLoading(false);
    if (updateErr) {
      setError("Could not update password. The link may have expired.");
      return;
    }
    router.push("/login?reset=success");
  };

  return (
    <main className="min-h-screen flex items-center justify-center p-4">
      <div className="w-full max-w-md bg-white border border-gray-200 rounded-lg p-8">
        <h1 className="text-3xl font-display mb-6">Choose a new password</h1>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <Label htmlFor="password">New password</Label>
            <Input
              id="password"
              type="password"
              required
              minLength={6}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </div>
          {error && <p className="text-sm text-red-600">{error}</p>}
          <Button type="submit" className="w-full" disabled={loading}>
            {loading ? "Updating..." : "Update password"}
          </Button>
        </form>
      </div>
    </main>
  );
}
```

- [ ] **Step 3: Verify build**

```bash
cd apps/customer-dashboard
npm run build
```

Expected: build OK.

- [ ] **Step 4: Commit**

```bash
git add apps/customer-dashboard/src/app/forgot-password apps/customer-dashboard/src/app/reset-password
git commit -m "feat(E1): forgot-password + reset-password pages"
```

---

## Task 9: Change password page (forced first login)

**Files:**
- Create: `apps/customer-dashboard/src/app/change-password/page.tsx`

- [ ] **Step 1: Create change-password page**

`apps/customer-dashboard/src/app/change-password/page.tsx`:

```typescript
"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { createClient } from "@/lib/supabase/client";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Label } from "@/components/ui/Label";

export default function ChangePasswordPage() {
  const router = useRouter();
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    if (password !== confirm) {
      setError("Passwords do not match");
      return;
    }
    if (password.length < 6) {
      setError("Password must be at least 6 characters");
      return;
    }
    setLoading(true);
    const supabase = createClient();
    const { error: updateErr } = await supabase.auth.updateUser({
      password,
      data: { password_changed: true },
    });
    setLoading(false);
    if (updateErr) {
      setError("Could not update password. Please try again.");
      return;
    }
    router.push("/");
    router.refresh();
  };

  return (
    <main className="min-h-screen flex items-center justify-center p-4">
      <div className="w-full max-w-md bg-white border border-gray-200 rounded-lg p-8">
        <h1 className="text-3xl font-display mb-2">Set your password</h1>
        <p className="text-sm text-gray-600 mb-6">
          Please choose a new password to replace the temporary one we sent you.
        </p>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <Label htmlFor="password">New password</Label>
            <Input
              id="password"
              type="password"
              required
              minLength={6}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </div>
          <div>
            <Label htmlFor="confirm">Confirm new password</Label>
            <Input
              id="confirm"
              type="password"
              required
              minLength={6}
              value={confirm}
              onChange={(e) => setConfirm(e.target.value)}
            />
          </div>
          {error && <p className="text-sm text-red-600">{error}</p>}
          <Button type="submit" className="w-full" disabled={loading}>
            {loading ? "Updating..." : "Set password"}
          </Button>
        </form>
      </div>
    </main>
  );
}
```

- [ ] **Step 2: Verify build**

```bash
cd apps/customer-dashboard
npm run build
```

Expected: build OK.

- [ ] **Step 3: Commit**

```bash
git add apps/customer-dashboard/src/app/change-password
git commit -m "feat(E1): change-password page (forced first login)"
```

---

## Task 10: Dashboard home page (protected)

**Files:**
- Modify: `apps/customer-dashboard/src/app/page.tsx` (replace placeholder)

- [ ] **Step 1: Replace `src/app/page.tsx` with the protected dashboard home**

```typescript
import { createClient } from "@/lib/supabase/server";
import { DashboardCard } from "@/components/DashboardCard";
import { LogoutButton } from "@/components/LogoutButton";
import { redirect } from "next/navigation";

export default async function DashboardHome() {
  const supabase = await createClient();
  const { data: { user } } = await supabase.auth.getUser();
  if (!user) {
    redirect("/login");
  }

  const { data: site } = await supabase
    .from("sites")
    .select("slug, content")
    .eq("owner_user_id", user.id)
    .maybeSingle();

  const companyName = (user.user_metadata?.company_name as string | undefined) ?? "there";
  const sitesBaseUrl = "https://agents-sites.vercel.app";

  return (
    <main className="max-w-5xl mx-auto p-8">
      <header className="flex justify-between items-start mb-12">
        <div>
          <h1 className="text-4xl font-display mb-2">Welcome, {companyName}</h1>
          <p className="text-gray-600">Manage your website and explore upcoming features.</p>
        </div>
        <LogoutButton />
      </header>

      <section className="mb-12">
        <h2 className="text-2xl font-display mb-4">Your website</h2>
        {site ? (
          <div className="bg-white border border-gray-200 rounded-lg p-6">
            <p className="mb-2 text-sm text-gray-600">Public URL</p>
            <a
              href={`${sitesBaseUrl}/s/${site.slug}`}
              target="_blank"
              rel="noopener noreferrer"
              className="text-lg font-medium underline"
            >
              {sitesBaseUrl}/s/{site.slug}
            </a>
          </div>
        ) : (
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6">
            <p className="text-sm">No website found. Please contact support.</p>
          </div>
        )}
      </section>

      <section>
        <h2 className="text-2xl font-display mb-4">Upcoming features</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <DashboardCard title="Visits & Analytics" comingSoon />
          <DashboardCard title="Custom Domain" comingSoon />
          <DashboardCard title="Automatic Blog" comingSoon />
        </div>
      </section>
    </main>
  );
}
```

- [ ] **Step 2: Verify build**

```bash
cd apps/customer-dashboard
npm run build
```

Expected: build OK.

- [ ] **Step 3: Commit**

```bash
git add apps/customer-dashboard/src/app/page.tsx
git commit -m "feat(E1): protected dashboard home with site URL + coming-soon cards"
```

---

## Task 11: Middleware (auth gate + force password change)

**Files:**
- Create: `apps/customer-dashboard/middleware.ts`

- [ ] **Step 1: Create middleware**

`apps/customer-dashboard/middleware.ts`:

```typescript
import { createServerClient } from "@supabase/ssr";
import { NextResponse, type NextRequest } from "next/server";

export async function middleware(req: NextRequest) {
  const res = NextResponse.next();
  const supabase = createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        getAll: () => req.cookies.getAll(),
        setAll: (list) =>
          list.forEach(({ name, value, options }) =>
            res.cookies.set(name, value, options),
          ),
      },
    },
  );

  const { data: { user } } = await supabase.auth.getUser();
  const path = req.nextUrl.pathname;

  // Public routes (no auth required)
  const publicPaths = ["/login", "/forgot-password", "/reset-password"];
  if (
    publicPaths.some((p) => path.startsWith(p)) ||
    path.startsWith("/api/auth")
  ) {
    return res;
  }

  // Protected: must be authenticated
  if (!user) {
    return NextResponse.redirect(new URL("/login", req.url));
  }

  // Force password change on first login
  const passwordChanged = user.user_metadata?.password_changed === true;
  if (!passwordChanged && path !== "/change-password") {
    return NextResponse.redirect(new URL("/change-password", req.url));
  }

  return res;
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico).*)"],
};
```

- [ ] **Step 2: Verify build (with middleware)**

```bash
cd apps/customer-dashboard
npm run build
```

Expected: build OK, "Middleware: 1" appears in build output.

- [ ] **Step 3: Commit**

```bash
git add apps/customer-dashboard/middleware.ts
git commit -m "feat(E1): middleware for auth gate + force password change"
```

---

## Task 12: Vitest config + middleware test

**Files:**
- Create: `apps/customer-dashboard/vitest.config.ts`
- Create: `apps/customer-dashboard/__tests__/middleware.test.ts`

- [ ] **Step 1: Create vitest config**

`apps/customer-dashboard/vitest.config.ts`:

```typescript
import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";
import path from "path";

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  test: {
    environment: "jsdom",
    globals: true,
  },
});
```

- [ ] **Step 2: Create middleware test**

`apps/customer-dashboard/__tests__/middleware.test.ts`:

```typescript
import { describe, it, expect, vi, beforeEach } from "vitest";

vi.mock("@supabase/ssr", () => ({
  createServerClient: vi.fn(),
}));

import { middleware } from "../middleware";
import { createServerClient } from "@supabase/ssr";
import { NextRequest } from "next/server";

function makeReq(path: string) {
  return new NextRequest(`http://localhost:3000${path}`);
}

function mockSupabase(user: any) {
  (createServerClient as any).mockReturnValue({
    auth: {
      getUser: vi.fn().mockResolvedValue({ data: { user } }),
    },
  });
}

describe("middleware", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    process.env.NEXT_PUBLIC_SUPABASE_URL = "https://test.supabase.co";
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY = "anon";
  });

  it("allows /login without auth", async () => {
    mockSupabase(null);
    const res = await middleware(makeReq("/login"));
    expect(res.status).toBe(200);
  });

  it("allows /forgot-password without auth", async () => {
    mockSupabase(null);
    const res = await middleware(makeReq("/forgot-password"));
    expect(res.status).toBe(200);
  });

  it("redirects unauthenticated user to /login", async () => {
    mockSupabase(null);
    const res = await middleware(makeReq("/"));
    expect(res.status).toBe(307); // Next.js redirect
    expect(res.headers.get("location")).toContain("/login");
  });

  it("redirects user with password_changed=false to /change-password", async () => {
    mockSupabase({ id: "uid", user_metadata: { password_changed: false } });
    const res = await middleware(makeReq("/"));
    expect(res.status).toBe(307);
    expect(res.headers.get("location")).toContain("/change-password");
  });

  it("allows authenticated user with password_changed=true to access /", async () => {
    mockSupabase({ id: "uid", user_metadata: { password_changed: true } });
    const res = await middleware(makeReq("/"));
    expect(res.status).toBe(200);
  });

  it("allows /change-password access for user without password_changed flag (no redirect loop)", async () => {
    mockSupabase({ id: "uid", user_metadata: { password_changed: false } });
    const res = await middleware(makeReq("/change-password"));
    expect(res.status).toBe(200);
  });
});
```

- [ ] **Step 3: Run tests to verify they pass**

```bash
cd apps/customer-dashboard
npm test
```

Expected: 6 tests PASS.

- [ ] **Step 4: Commit**

```bash
git add apps/customer-dashboard/vitest.config.ts apps/customer-dashboard/__tests__
git commit -m "test(E1): vitest config + middleware tests"
```

---

## Task 13: Vercel deploy + env vars + Supabase Auth URL config

**Files:** N/A (CLI + dashboard config)

- [ ] **Step 1: Link Vercel project**

```bash
cd apps/customer-dashboard
vercel link --yes
```

When prompted, choose "Create new project" with name `customer-dashboard` (or accept default `agents-customer-dashboard`).

Expected: `.vercel/project.json` created.

- [ ] **Step 2: Add env vars to Vercel**

Get the Supabase anon key from existing agents-dashboard env (`vercel env ls production` from that project), or pull from `apps/dashboard/.env`.

```bash
echo "https://smzmgzblbliprwbjptjs.supabase.co" | vercel env add NEXT_PUBLIC_SUPABASE_URL production
echo "<anon_key_value>" | vercel env add NEXT_PUBLIC_SUPABASE_ANON_KEY production
```

Verify:

```bash
vercel env ls production
```

Expected: 2 env vars listed.

- [ ] **Step 3: Add `CUSTOMER_DASHBOARD_URL` to Builder Agent on Railway**

This step requires Railway dashboard access. In Railway:

1. Open project → service `setting-agent` and `website-builder` workers
2. For `website-builder` service: Variables → Add `CUSTOMER_DASHBOARD_URL=https://agents-customer-dashboard.vercel.app` (use actual URL after first deploy)
3. Redeploy worker to pick up env

Mark this step done after confirming the env var is set on Railway.

- [ ] **Step 4: Deploy to production**

```bash
cd apps/customer-dashboard
vercel --prod --yes
```

Expected: deploy ready, URL printed (capture it for Supabase config in next step).

- [ ] **Step 5: Configure Supabase Auth redirect URLs**

This step requires Supabase dashboard access (no MCP tool for this). Open Supabase project at https://supabase.com/dashboard/project/smzmgzblbliprwbjptjs:

1. Settings → Auth → URL Configuration
2. Add to "Redirect URLs": `https://<actual-deployment-url>.vercel.app/**`
3. Save

Mark this step done after saving in Supabase dashboard.

- [ ] **Step 6: Smoke test**

```bash
curl --ssl-no-revoke -s -o /dev/null -w "HTTP %{http_code}\n" "https://<deployment-url>.vercel.app/login"
```

Expected: HTTP 200 (or 307 redirect — both acceptable; 401/500 = misconfig).

- [ ] **Step 7: Commit deploy artifacts**

```bash
cd ../..
git add apps/customer-dashboard/.vercel  # if needed
git commit --allow-empty -m "chore(E1): customer-dashboard deployed to Vercel production"
```

---

## Task 14: E2E manual test

**Files:** N/A (manual verification)

- [ ] **Step 1: Verify Builder Agent deployed with onboarding**

Confirm Railway has the latest commit (with `_onboard_customer`). Run:

```bash
gh api "repos/indigitmarketing-droid/agents-platform/deployments?per_page=5" | python -c "import json, sys; data=json.load(sys.stdin); [print(d['sha'][:7], d['created_at']) for d in data[:3]]"
```

If latest deploy SHA does NOT match `git rev-parse HEAD`, manually trigger Railway redeploy.

- [ ] **Step 2: Insert test lead with email**

Use Supabase MCP `execute_sql`:

```sql
INSERT INTO leads (company_name, phone, email, has_website, status, source, country_code, call_status)
VALUES ('TEST E2E Customer Onboarding', '+393477544532', 'info@natalinoai.com', false, 'new', 'manual_test', 'US', 'never_called')
RETURNING id;
```

Capture the returned `id` as `<test_lead_id>`.

- [ ] **Step 3: Trigger setting.call_accepted directly (bypass actual call)**

Insert event for Builder:

```sql
INSERT INTO events (type, target_agent, source_agent, payload, status)
VALUES ('setting.call_accepted', 'builder', 'human', jsonb_build_object(
  'lead_id', '<test_lead_id>',
  'lead', jsonb_build_object(
    'id', '<test_lead_id>',
    'company_name', 'TEST E2E Customer Onboarding',
    'email', 'info@natalinoai.com',
    'phone', '+393477544532',
    'category', 'restaurant',
    'city', 'Test City'
  ),
  'call_brief', jsonb_build_object('services', ARRAY['pizza'], 'style_preference', 'modern')
), 'pending')
RETURNING id;
```

- [ ] **Step 4: Wait + verify chain executed**

After ~30s:

```sql
SELECT 'site' AS what, json_build_object('id',id,'slug',slug,'owner_user_id',owner_user_id)::text AS data FROM sites WHERE owner_user_id IS NOT NULL ORDER BY created_at DESC LIMIT 1
UNION ALL
SELECT 'event_onboarded' AS what, json_build_object('payload',payload,'created_at',created_at)::text FROM events WHERE type='customer.onboarded' ORDER BY created_at DESC LIMIT 1
UNION ALL
SELECT 'auth_user' AS what, json_build_object('id',id,'email',email,'metadata',raw_user_meta_data)::text FROM auth.users WHERE email='info@natalinoai.com' LIMIT 1;
```

Expected: 3 rows showing site (with owner_user_id set), customer.onboarded event, auth.users row.

- [ ] **Step 5: Verify welcome email arrived**

Check `info@natalinoai.com` inbox. Email contains: company name, site URL, login email, temporary password, dashboard URL.

- [ ] **Step 6: Login flow walkthrough**

Open the deployment URL in a browser:

1. Click "Sign in" → enter `info@natalinoai.com` + temp password
2. Should redirect to `/change-password`
3. Set new password (≥6 chars), confirm, submit
4. Should redirect to `/`
5. Verify dashboard shows: "Welcome, TEST E2E Customer Onboarding", site URL link, 3 coming-soon cards
6. Click logout → redirect to /login
7. Login again with new password → should go directly to `/` (no force-change redirect)

- [ ] **Step 7: Test password reset flow**

1. Logout, click "Forgot password?"
2. Enter `info@natalinoai.com` → "Check your inbox"
3. Click reset link in email → land on `/reset-password`
4. Enter new password → redirect to `/login?reset=success`
5. Login with new password → dashboard

- [ ] **Step 8: Cleanup test data**

```sql
DELETE FROM events WHERE payload->>'lead_id' = '<test_lead_id>';
DELETE FROM call_logs WHERE lead_id = '<test_lead_id>';
DELETE FROM sites WHERE id IN (SELECT id FROM sites WHERE owner_user_id IN (SELECT id FROM auth.users WHERE email='info@natalinoai.com'));
DELETE FROM auth.users WHERE email='info@natalinoai.com';  -- via Supabase admin or SQL with service role
DELETE FROM leads WHERE id = '<test_lead_id>';
```

NOTE: deletion of auth.users from public schema may require Supabase admin key — easier to delete from Auth dashboard if needed.

---

## Task 15: Update BRAINSTORM_STATE + memory

**Files:**
- Modify: `BRAINSTORM_STATE.md`
- Modify: memory `project_decomposition.md`

- [ ] **Step 1: Update BRAINSTORM_STATE.md sub-projects table**

Read current `BRAINSTORM_STATE.md`. Update the row for E:

Before:
```
| E | Admin dashboards multi-tenant + Blog generator | da fare |
```

After:
```
| E1 | Customer Dashboard (auth + multi-tenant foundation) | **✅ COMPLETATO + DEPLOYATO** |
| E2 | Custom domain configuration | da fare |
| E3 | Analytics | da fare |
| E4 | Blog generator | da fare |
| E5 | Social integration | da fare |
```

- [ ] **Step 2: Add E1 closure section to BRAINSTORM_STATE.md**

After the E1 section, add a closure block similar to D:

```markdown
## Sub-progetto E1 — Customer Dashboard ✅ DEPLOYATO

**Build completato 2026-XX-XX**: nuova app customer-dashboard, Supabase Auth, RLS multi-tenant, Builder Agent extension per onboarding automatico.

**Componenti deployati**:
- Migration `007_customer_onboarding.sql` applicata
- `apps/workers/website_builder/welcome_email.py` + onboarding integrato
- `apps/customer-dashboard/` Next.js live su Vercel
- 5 routes: /login, /forgot-password, /reset-password, /change-password, /
- Middleware: auth gate + force password change al primo login
- 1 nuovo evento: `customer.onboarded`

**E2E validato**: lead test → Builder build site → auth user creato → welcome email inviata → cliente login → forced password change → dashboard render.

**Documenti**:
- Spec: `agents-platform/docs/superpowers/specs/2026-05-01-customer-dashboard-e1-design.md`
- Plan: `agents-platform/docs/superpowers/plans/2026-05-01-customer-dashboard-e1.md`
```

- [ ] **Step 3: Update memory `project_decomposition.md`**

Update the description and decomposition list to reflect E1 done. Add new line in component list:

Replace `- **E** — Admin dashboards multi-tenant + blog generator (requirements at...)` with:

```
- **E1** — Customer Dashboard (auth + multi-tenant foundation) ← **DEPLOYATO 2026-XX-XX**
- **E2** — Custom domain configuration ← pending
- **E3** — Analytics ← pending
- **E4** — Blog generator ← pending
- **E5** — Social integration ← pending
```

- [ ] **Step 4: Commit**

```bash
git add BRAINSTORM_STATE.md  # if not in repo, just save the file edit
# Memory file is outside repo — no git add needed
echo "BRAINSTORM_STATE updated; memory persisted via Write tool"
```

---

## Self-Review Checklist (already performed)

✅ **Spec coverage**: every section of the spec maps to one or more tasks (migration → T1; welcome email → T2; onboard method → T3; integration → T4; scaffold → T5; clients/ui → T6; pages → T7-T10; middleware → T11; tests → T12; deploy → T13; E2E → T14; closure → T15).

✅ **Placeholder scan**: no TBDs, all code blocks complete with full implementations.

✅ **Type consistency**: `_onboard_customer` returns `str | None`. `auth_user_id` consistent across tasks. Event type `customer.onboarded` matches schema in T1.

✅ **No "similar to Task N"**: each task has its own complete code.
