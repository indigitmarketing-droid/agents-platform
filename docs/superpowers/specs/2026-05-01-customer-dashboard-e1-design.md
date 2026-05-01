# Sub-progetto E1 — Customer Dashboard (Auth + Multi-tenant Foundation)

**Data**: 2026-05-01
**Stato**: Design approvato dall'utente, pronto per writing-plans
**Sub-progetto**: E1 (foundation di E — Customer dashboards)

---

## 1. Contesto e scope

Il Sub-progetto E originale comprende 5 features distinte (auth multi-tenant, custom domain, analytics, blog generator, social integration). Per gestire la complessità è decomposto in 5 sub-progetti consecutivi:

- **E1** (questo doc) — Auth + multi-tenant dashboard skeleton
- E2 — Custom domain configuration
- E3 — Analytics
- E4 — Blog generator
- E5 — Social integration

**E1 è il foundation**: senza login multi-tenant, le altre features non hanno casa. Ogni cliente ha un account auth, vede solo il suo sito, e la dashboard ha placeholder per le features future.

### Goals di E1

- Cliente con sito generato da Builder può loggarsi con email + password ricevute via email
- Cliente vede solo i propri dati (multi-tenant via Supabase RLS)
- Forced password change al primo login (sicurezza)
- Onboarding 100% agent-orchestrato (no human in the loop)
- Foundation per E2-E5: layout dashboard estendibile

### Non-goals di E1 (deferred)

- ❌ Custom domain configuration (E2)
- ❌ Analytics dashboard (E3)
- ❌ Blog generator (E4)
- ❌ Social integration (E5)
- ❌ WhatsApp delivery delle credenziali (lasciato a D2 future)
- ❌ Password complexity rules custom (default Supabase ≥6 chars)
- ❌ Email "From" su dominio custom (Resend free tier `noreply@resend.dev` finché non registriamo dominio)
- ❌ Modifica email cliente o profilo (read-only in MVP)

---

## 2. Architettura

```
┌──────────────────────────────────────────────────────────┐
│  Builder Agent (Railway worker, esistente esteso)         │
│  • riceve setting.call_accepted                            │
│  • genera sito → INSERT sites + content                    │
│  • NEW: _onboard_customer() → auth.admin.createUser        │
│  • NEW: send welcome email via Resend                      │
│  • NEW: emit customer.onboarded event                      │
└──────────────────────────────────────────────────────────┘
                          │
                          ▼
        ┌─────────────────────────────────────┐
        │  Supabase                            │
        │  ┌──────────────┐  ┌──────────────┐ │
        │  │ auth.users    │  │ public.sites │ │
        │  │ (Supabase OOB)│  │ owner_user_id│ │
        │  └──────────────┘  └──────────────┘ │
        │  RLS: owner_user_id = auth.uid()    │
        └─────────────────────────────────────┘
                          ▲
                          │
                          │ JWT in cookies
                          │
┌──────────────────────────────────────────────────────────┐
│  agents-customer-dashboard (Vercel, NUOVA app)            │
│                                                             │
│  Routes:                                                    │
│  • /login           — email + password                     │
│  • /forgot-password — Supabase password reset email        │
│  • /reset-password  — landing dal link email               │
│  • /change-password — forced redirect al primo login       │
│  • /                — dashboard home (welcome + site URL)   │
│  • /api/auth/callback — Supabase auth code exchange         │
│                                                             │
│  Middleware: route protection + force password change       │
│  Components: shadcn-style (matching agents-sites premium)   │
└──────────────────────────────────────────────────────────┘
```

### Punti chiave

1. **Builder Agent estende il proprio handler** dopo `INSERT sites`. Niente nuovo worker. L'onboarding è atomic con la creazione del sito.

2. **Customer dashboard è un'app Next.js stateless**. Tutto il dato vive in Supabase. RLS fa il filtering — il middleware Next.js verifica solo che ci sia una sessione valida.

3. **Zero coupling tra dashboard e altri agent**. Se uno worker muore, il cliente continua a vedere il suo sito. La dashboard è puro frontend per leggere `sites` filtrati per RLS.

---

## 3. Data model

### Migration: `007_customer_onboarding.sql`

```sql
-- 1. Estendi sites con owner_user_id
ALTER TABLE sites ADD COLUMN owner_user_id UUID REFERENCES auth.users(id) ON DELETE SET NULL;
CREATE INDEX idx_sites_owner_user ON sites(owner_user_id);

-- 2. Abilita RLS su sites (verifica se già attiva)
ALTER TABLE sites ENABLE ROW LEVEL SECURITY;

-- 3. Policy: cliente loggato vede SOLO il proprio sito
CREATE POLICY "customers_see_own_site"
  ON sites FOR SELECT
  TO authenticated
  USING (owner_user_id = auth.uid());

-- 4. Policy: nessuna mutation lato customer
-- (Service role bypassa automaticamente RLS, quindi Builder Agent non è bloccato)
CREATE POLICY "no_customer_writes"
  ON sites FOR ALL
  TO authenticated
  USING (false)
  WITH CHECK (false);

-- 5. Policy speciale per agents-sites (rendering pubblico /s/{slug})
-- agents-sites usa anon key per rendering. Manteniamo accesso pubblico in sola lettura.
-- Nota implementazione: verificare se esistono già policy anon su sites prima di applicare;
-- se sì, fare DROP della vecchia + CREATE per evitare collisioni di nome.
CREATE POLICY "public_read_sites_by_slug"
  ON sites FOR SELECT
  TO anon
  USING (true);
```

### `auth.users.user_metadata` schema

Quando Builder crea un nuovo utente:

```typescript
{
  lead_id: "uuid",            // FK al lead originale
  site_id: "uuid",            // FK al sito creato
  company_name: "string",     // per personalizzazione UI
  password_changed: false,    // flag per force-redirect al primo login
  onboarded_at: "ISO 8601"    // audit
}
```

### Nuovo event type

`customer.onboarded` aggiunto a `packages/events_schema/schemas/builder.json`:

```json
{
  "type": "customer.onboarded",
  "source_agent": "builder",
  "target_agent": null,
  "payload": {
    "lead_id": "uuid",
    "site_id": "uuid",
    "auth_user_id": "uuid",
    "email": "string",
    "email_sent": true
  }
}
```

### Lead lifecycle status (esteso)

`leads.status` (esistente, default 'new') estesa con:

- `accepted` — call risolto positivo
- `site_published` — sito creato (Builder OK)
- `customer_onboarded` — auth user esiste + email inviata

(`call_status` resta separato e specifico al Setting Agent.)

### Idempotency design

Builder potrebbe ri-eseguire un evento; ogni step deve essere idempotente:

| Step | Idempotency strategy |
|---|---|
| INSERT sites | UNIQUE constraint su `lead_id` (verificare schema) → o UPSERT su slug |
| `auth.admin.createUser` | Catch 422 email duplicata → ritorna user esistente |
| Send welcome email | Lookup `customer.onboarded` event con stesso `auth_user_id` → skip se trovato |
| INSERT customer.onboarded event | Dedupe via auth_user_id |

---

## 4. Componenti

### A) Next.js app `apps/customer-dashboard/`

```
apps/customer-dashboard/
├── package.json
├── next.config.ts
├── tailwind.config.ts        # match agents-sites theme (Inter + Playfair)
├── tsconfig.json
├── middleware.ts              # auth gate + force password redirect
└── src/
    ├── app/
    │   ├── layout.tsx
    │   ├── globals.css
    │   ├── page.tsx           # / → dashboard home (protected)
    │   ├── login/page.tsx
    │   ├── forgot-password/page.tsx
    │   ├── reset-password/page.tsx
    │   ├── change-password/page.tsx
    │   └── api/auth/callback/route.ts
    ├── components/
    │   ├── ui/                # button, input, label primitives
    │   ├── DashboardCard.tsx  # placeholder card "Coming soon"
    │   └── LogoutButton.tsx
    └── lib/
        └── supabase/
            ├── client.ts
            ├── server.ts
            └── middleware.ts
```

### B) Middleware (file critico)

```typescript
// middleware.ts
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
        setAll: (list) => list.forEach(({ name, value, options }) =>
          res.cookies.set(name, value, options)),
      },
    }
  );

  const { data: { user } } = await supabase.auth.getUser();
  const path = req.nextUrl.pathname;

  const publicPaths = ["/login", "/forgot-password", "/reset-password"];
  if (publicPaths.some(p => path.startsWith(p)) || path.startsWith("/api/auth")) {
    return res;
  }

  if (!user) {
    return NextResponse.redirect(new URL("/login", req.url));
  }

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

### C) Dashboard home `/`

```typescript
// src/app/page.tsx (server component)
export default async function DashboardHome() {
  const supabase = createServerClient(/* ... */);
  const { data: { user } } = await supabase.auth.getUser();
  const { data: site } = await supabase
    .from("sites")
    .select("slug, content")
    .eq("owner_user_id", user!.id)
    .single();

  return (
    <main>
      <h1>Benvenuto, {user!.user_metadata?.company_name}</h1>
      <section>
        <h2>Il tuo sito</h2>
        <p>URL: <a href={`https://agents-sites.vercel.app/s/${site!.slug}`}>
          agents-sites.vercel.app/s/{site!.slug}
        </a></p>
      </section>
      <section className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-8">
        <DashboardCard title="Visite & Analytics" comingSoon />
        <DashboardCard title="Dominio personalizzato" comingSoon />
        <DashboardCard title="Blog automatico" comingSoon />
      </section>
      <LogoutButton />
    </main>
  );
}
```

### D) Builder Agent extension

`apps/workers/website_builder/main.py` — nuovo metodo:

```python
def _onboard_customer(self, lead: dict, site: dict) -> str | None:
    """Create auth user + send welcome email. Returns auth_user_id or None on failure."""
    if not lead.get("email"):
        logger.warning(f"Lead {lead['id']} has no email, skipping onboarding")
        return None

    # Idempotency: check if user already exists by email
    existing_users = self._client.auth.admin.list_users()
    for u in existing_users.users if hasattr(existing_users, "users") else []:
        if u.email == lead["email"]:
            logger.info(f"User already exists for {lead['email']}, skipping create")
            return u.id

    password = secrets.token_urlsafe(12)
    try:
        result = self._client.auth.admin.create_user({
            "email": lead["email"],
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
        logger.error(f"Failed to create auth user for {lead['email']}: {e}")
        return None

    auth_user_id = result.user.id
    self._client.table("sites").update({
        "owner_user_id": auth_user_id
    }).eq("id", site["id"]).execute()

    self._send_welcome_email(lead, site, password)
    return auth_user_id
```

E nel main handler dopo `INSERT site`:

```python
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
```

### E) Welcome email module

`apps/workers/website_builder/welcome_email.py`:

```python
from resend import Resend
import os

DASHBOARD_URL = os.environ.get(
    "CUSTOMER_DASHBOARD_URL",
    "https://agents-customer-dashboard.vercel.app"
)

def send_welcome_email(lead: dict, site: dict, password: str):
    resend = Resend(api_key=os.environ["RESEND_API_KEY"])
    site_url = f"https://agents-sites.vercel.app/s/{site['slug']}"
    resend.emails.send({
        "from": "onboarding@resend.dev",
        "to": [lead["email"]],
        "subject": f"Il tuo sito {lead['company_name']} è pronto",
        "html": _render_welcome_html(lead, site_url, password),
        "text": _render_welcome_text(lead, site_url, password),
    })
```

Body HTML/text contiene: nome cliente, URL sito generato, URL dashboard, email login, password temporanea, istruzione "cambia password al primo accesso".

### F) Dipendenze nuove

- App Next.js: `@supabase/ssr@^0.5`, `@supabase/supabase-js@^2.45`, `lucide-react`, `clsx`, `tailwind-merge`
- Builder Agent Python: nessuna nuova (resend già usato in agents-sites; supabase-py copre auth admin)

---

## 5. Data Flow + State Machines

### Flow 1 — Onboarding

```
Setting Agent emit setting.call_accepted (target=builder)
                       ↓
Builder Agent picks event
   1. _build_site_content() → Claude PBS copy + theme
   2. INSERT into sites
   3. _onboard_customer():
       a. check user exists by email
       b. auth.admin.create_user
       c. UPDATE sites.owner_user_id
       d. send welcome email via Resend
   4. emit customer.onboarded
                       ↓
Cliente riceve email con: URL sito, URL dashboard, email + password temp
```

### Flow 2 — Primo login

```
Cliente apre dashboard URL → /login (no session)
   ↓ inserisce email + password temp
Supabase Auth verifica → JWT in cookie
   ↓
Middleware controlla user_metadata.password_changed
   ├── false → redirect /change-password
   │              ↓ cliente sceglie nuova password
   │           supabase.auth.updateUser({password, data: {password_changed: true}})
   │              ↓ redirect /
   └── true → render dashboard /
```

### Flow 3 — Password reset

```
/forgot-password → email submission
   ↓
supabase.auth.resetPasswordForEmail(email, {redirectTo: <DASHBOARD_URL>/reset-password})
   ↓
Supabase manda email con link magic
   ↓
Cliente clicca → /reset-password?code=xxx
   ↓
Server exchange code → JWT in cookie
   ↓
Form per nuova password → updateUser({password})
   ↓
redirect /login
```

### State Machine: lead lifecycle (esteso)

```
scraped → never_called → called → accepted → [BUILDER]
                              ↘ rejected     site_published
                              ↘ unclear         ↓
                                              customer_onboarded
```

### Error handling matrix

| Step | Failure mode | Retry | User-visible |
|---|---|---|---|
| Builder INSERT site | DB error | Sì (retry framework) | No |
| `auth.admin.create_user` | Email duplicata | No (treat as success) | No |
| `auth.admin.create_user` | Network/Supabase down | Sì (RetryableError) | No |
| UPDATE site.owner_user_id | DB error | Sì (idempotente) | No |
| Resend send email | API down 5xx | Sì max 3 | No |
| Resend send email | Email invalid 4xx | No (FatalError, log) | Cliente non riceve email — operator alert |
| Cliente login con password temp | wrong password | No | "Credenziali non valide" |
| Cliente non cambia password | Middleware redirect loop | N/A | Forced redirect ogni request |

### Edge cases

1. **Lead senza email**: `_onboard_customer` ritorna `None`, log warning, sito orfano (`owner_user_id=null`). Operator può associare manualmente.

2. **Email duplicata cross-lead**: secondo onboarding trova user esistente; se ha già un `site_id` in metadata diverso, log error e non collegare (operator decide).

3. **Email delivery fail post user creation**: user esiste in auth ma cliente non ha credenziali. Operator può fare password reset dal Supabase dashboard.

4. **Cliente cambia email**: NON supportato in MVP (campo immutable).

5. **Sito eliminato ma user esiste**: `ON DELETE SET NULL` su owner_user_id → cliente vede "Sito non trovato — contatta supporto".

---

## 6. Testing strategy

### Test unit Python (Builder Agent)

`apps/workers/website_builder/tests/test_onboarding.py`:
- `_onboard_customer` happy path
- lead senza email → return None
- email duplicata → ritorna user esistente, non duplica
- Resend fail 5xx → retry
- Resend fail 4xx → log + non rilancia

### Test unit TypeScript (customer-dashboard)

`apps/customer-dashboard/__tests__/middleware.test.ts`:
- Path pubbliche bypass auth
- User non autenticato → redirect /login
- User autenticato + password_changed=false → redirect /change-password
- User autenticato + password_changed=true → render

`apps/customer-dashboard/__tests__/onboarding.test.ts`:
- Login form invio credenziali
- forgot-password invoca resetPasswordForEmail
- change-password updateUser + flag aggiornato

### Test integration Python

Estensione `apps/workers/website_builder/tests/test_pipeline_integration.py`:
- Caso completo: setting.call_accepted con lead.email → check sites.owner_user_id valorizzato + customer.onboarded emesso + Resend mock chiamato

### Test E2E manuale (post-deploy)

1. Trigger `setting.force_call` su lead test → conversation `accepted` (mock o real)
2. Builder esegue → site creato
3. Verifica email arriva (a `indigit.marketing@gmail.com` finché Resend domain unverified)
4. Click link dashboard → /login
5. Inserisci credenziali → redirect a /change-password
6. Cambia password → redirect a /
7. Vedi welcome + URL sito + 3 cards "Coming soon"
8. Logout → /login
9. Re-login con nuova password → / direttamente

---

## 7. Deployment

### Nuovo progetto Vercel

```bash
cd apps/customer-dashboard
vercel link --yes
vercel env add NEXT_PUBLIC_SUPABASE_URL production
vercel env add NEXT_PUBLIC_SUPABASE_ANON_KEY production
vercel --prod
```

URL prodotto default: `https://agents-customer-dashboard.vercel.app`.

### Env vars

| Var | Scope | Valore |
|---|---|---|
| `NEXT_PUBLIC_SUPABASE_URL` | customer-dashboard Vercel | `https://smzmgzblbliprwbjptjs.supabase.co` |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | customer-dashboard Vercel | (anon key esistente) |
| `CUSTOMER_DASHBOARD_URL` | Builder Agent Railway | `https://agents-customer-dashboard.vercel.app` |

Builder Agent ha già `RESEND_API_KEY` + `SUPABASE_SERVICE_KEY` + `SUPABASE_URL`.

### Supabase Auth config (critico)

Settings → Auth → URL Configuration → aggiungere:
`https://agents-customer-dashboard.vercel.app/**`

ai "Redirect URLs allowed" — necessario per password reset link.

### Rollout plan

1. Apply migration `007_customer_onboarding.sql`
2. Builder Agent extension (code + tests + deploy Railway)
3. customer-dashboard scaffold (code + tests)
4. Deploy customer-dashboard su Vercel + Supabase URL config
5. E2E test
6. Update BRAINSTORM_STATE + memory

---

## 8. Observability

- **Eventi `customer.onboarded`** in `events` table = audit trail principale
- **Vercel function logs** del customer-dashboard mostrano middleware redirects (debug "user stuck on /change-password")
- **Resend dashboard** mostra delivery status welcome email (open rate, bounce)
- **Supabase Auth Logs** (`auth.audit_log_entries`) traccia ogni login/logout/reset

---

## 9. Open questions per implementation phase

| # | Question | Default decision |
|---|---|---|
| 1 | Email "From" address | `noreply@resend.dev` (free tier) finché dominio agentsplatform.app registrato |
| 2 | Branding/UI | Match agents-sites premium (Inter + Playfair) |
| 3 | Logout UX | Bottone in dashboard, no conferma modal |
| 4 | Password complexity | Default Supabase ≥6 chars, no validation custom |
| 5 | Session lifetime | Default Supabase (1h access + 30d refresh) |
| 6 | Multi-site future | Schema attuale 1:1 customer:site, espandibile |

---

## 10. Riferimenti

- Requirements originali: `docs/superpowers/specs/sub-project-E-requirements.md`
- Spec Builder Agent (estendiamo): `docs/superpowers/specs/2026-04-25-website-builder-design.md`
- Spec Setting Agent (precedente cycle): `docs/superpowers/specs/2026-04-28-setting-agent-design.md`
- Stato infra: `BRAINSTORM_STATE.md`
