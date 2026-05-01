# Sub-progetto E1 — Customer Dashboard (Auth + Multi-tenant Foundation)

**Data**: 2026-05-01
**Stato**: Design approvato dall'utente, scope ridotto dopo discovery del flusso payment.
**Sub-progetto**: E1 (foundation di E — Customer dashboards)

> **Scope update (2026-05-01)**: il flusso di onboarding (auth.user creation + welcome email) è stato spostato a **Sub-progetto F1 (Stripe Payments)** perché l'onboarding dashboard avviene **dopo il pagamento**, non dopo il build del sito. E1 è ora puro frontend skeleton + Supabase Auth setup. Vedi sezione "Flusso completo platform" in fondo per l'architettura end-to-end.

---

## 1. Contesto e scope

Il Sub-progetto E originale è decomposto in 5 sub-progetti consecutivi:

- **E1** (questo doc) — Auth + multi-tenant dashboard skeleton
- E2 — Custom domain configuration
- E3 — Analytics
- E4 — Blog generator
- E5 — Social integration

**E1 è il foundation della UI cliente**: costruisce l'app Next.js `agents-customer-dashboard` con login, password reset, change-password forced, route protection e RLS schema. Non gestisce l'onboarding (creazione auth.user) — quello è F1.

### Goals di E1

- App `agents-customer-dashboard` Next.js deployata su Vercel
- Pagine: login, forgot-password, reset-password, change-password, dashboard home
- Middleware: route protection + force password change su flag `password_changed=false`
- RLS multi-tenant su `sites`: customer vede solo proprio sito via `auth.uid()`
- Schema migration con campi future-proof per F1: `payment_status`, `published_at`
- UI in **English** (test market USA)

### Non-goals di E1 (deferred)

- ❌ Auth.user creation + welcome email → **F1 (Stripe webhook handler)**
- ❌ Stripe Checkout + payment flow → **F1**
- ❌ 48h grace period + cleanup cron → **F1**
- ❌ WhatsApp messaging delle credenziali / payment link → **F2**
- ❌ Site-ready call (secondo agente ElevenLabs) → **D-Phase2**
- ❌ Custom domain configuration → **E2**
- ❌ Analytics dashboard → **E3**
- ❌ Blog generator → **E4**
- ❌ Social integration → **E5**

### Lingua

UI customer-dashboard in **English** (test market USA). i18n con next-intl è feature futura quando si torna su mercato Italia.

---

## 2. Architettura

```
                     ┌─────────────────────────────┐
                     │  Supabase                    │
                     │  ┌──────────────┐  ┌───────┐ │
                     │  │ auth.users    │  │ sites │ │
                     │  └──────────────┘  └───────┘ │
                     │                              │
                     │  RLS:                        │
                     │  • authenticated → own site  │
                     │  • anon → all (for /s/{slug})│
                     └─────────────────────────────┘
                                  ▲
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

1. **Builder Agent NON viene modificato in E1**. Continua a inserire site con `owner_user_id=NULL`. F1 lo popolerà dopo Stripe webhook payment.

2. **Customer dashboard è un'app Next.js stateless**. Tutto il dato vive in Supabase. RLS fa il filtering — il middleware Next.js verifica solo che ci sia una sessione valida.

3. **E1 è valido stand-alone**: l'app può essere testata e2e senza F1 (creando manualmente auth.users + sites tramite Supabase admin per test).

---

## 3. Data model

### Migration: `007_customer_onboarding.sql`

```sql
-- 007_customer_onboarding.sql

-- 1. Add owner_user_id to sites (populated by F1 after payment)
ALTER TABLE sites ADD COLUMN owner_user_id UUID REFERENCES auth.users(id) ON DELETE SET NULL;
CREATE INDEX idx_sites_owner_user ON sites(owner_user_id);

-- 2. Add payment fields (used by F1, default values future-proof E1)
ALTER TABLE sites ADD COLUMN published_at TIMESTAMPTZ DEFAULT NOW();
ALTER TABLE sites ADD COLUMN payment_status TEXT DEFAULT 'unpaid'
  CHECK (payment_status IN ('unpaid', 'paid', 'expired'));
CREATE INDEX idx_sites_payment_grace ON sites(payment_status, published_at);

-- 3. Ensure RLS enabled
ALTER TABLE sites ENABLE ROW LEVEL SECURITY;

-- 4. SELECT policy for authenticated customers — own site only
CREATE POLICY "customers_see_own_site"
  ON sites FOR SELECT
  TO authenticated
  USING (owner_user_id = auth.uid());

-- 5. Block authenticated mutations (service_role bypasses RLS)
CREATE POLICY "no_customer_writes"
  ON sites FOR ALL
  TO authenticated
  USING (false)
  WITH CHECK (false);

-- 6. Public read for anon (used by agents-sites for /s/{slug} rendering)
CREATE POLICY "public_read_sites_by_slug"
  ON sites FOR SELECT
  TO anon
  USING (true);
```

### `auth.users.user_metadata` schema (popolato da F1)

Quando F1 (Stripe webhook) crea il nuovo utente:

```typescript
{
  lead_id: "uuid",            // FK al lead originale
  site_id: "uuid",            // FK al sito che il customer possiede
  company_name: "string",     // per personalizzazione UI
  password_changed: false,    // flag per force-redirect al primo login
  onboarded_at: "ISO 8601",   // audit
  stripe_customer_id: "cus_..."  // per future operations Stripe
}
```

E1 legge questo metadata. F1 lo scrive.

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
  const supabase = await createClient();
  const { data: { user } } = await supabase.auth.getUser();
  if (!user) redirect("/login");

  const { data: site } = await supabase
    .from("sites")
    .select("slug, content")
    .eq("owner_user_id", user.id)
    .maybeSingle();

  return (
    <main>
      <h1>Welcome, {user.user_metadata?.company_name}</h1>
      <section>
        <h2>Your website</h2>
        <p>URL: <a href={`https://agents-sites.vercel.app/s/${site?.slug}`}>
          agents-sites.vercel.app/s/{site?.slug}
        </a></p>
      </section>
      <section className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-8">
        <DashboardCard title="Visits & Analytics" comingSoon />
        <DashboardCard title="Custom Domain" comingSoon />
        <DashboardCard title="Automatic Blog" comingSoon />
      </section>
      <LogoutButton />
    </main>
  );
}
```

### D) Dipendenze nuove (E1 only)

- App Next.js: `@supabase/ssr@^0.5`, `@supabase/supabase-js@^2.45`, `lucide-react`, `clsx`, `tailwind-merge`
- No changes to Python workers in E1 (Builder Agent extension è in F1)

---

## 5. Data Flow + State Machines (E1 only)

### Flow 1 — Login utente esistente

```
Cliente apre dashboard URL → /login (no session)
   ↓ inserisce email + password
Supabase Auth verifica → JWT in cookie
   ↓
Middleware controlla user_metadata.password_changed
   ├── false → redirect /change-password
   │              ↓ cliente sceglie nuova password
   │           supabase.auth.updateUser({password, data: {password_changed: true}})
   │              ↓ redirect /
   └── true → render dashboard /
```

### Flow 2 — Password reset

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

### Onboarding flow (per documentazione — implementato in F1)

```
Builder finisce site → site INSERT con owner_user_id=NULL, payment_status='unpaid'
   ↓
[D-Phase2] Setting Agent secondo agente ElevenLabs chiama lead → vende $349
   ↓
[F2] Worker invia WhatsApp con Stripe Checkout link
   ↓
Cliente clicca link → Stripe Checkout → paga
   ↓
Stripe webhook payment.succeeded → [F1 handler]:
   1. INSERT auth.users with metadata
   2. UPDATE sites SET owner_user_id=<uid>, payment_status='paid'
   3. Send welcome email (Resend) with credentials
   ↓
Cliente apre email → click dashboard URL → /login (E1 entrata in scena)
   ↓
Force password change → dashboard home
```

E1 entra in gioco solo dopo che F1 ha completato l'onboarding. Senza F1, la dashboard può essere testata manualmente creando auth.users via Supabase admin.

### Error handling matrix (E1 only)

| Step | Failure mode | Comportamento |
|---|---|---|
| Cliente login con password sbagliata | Supabase 400 | "Invalid credentials" |
| Cliente non cambia password | N/A | Forced redirect ogni request finché flag=true |
| RLS rifiuta query | N/A | dashboard mostra "No website found — contact support" |
| Sito eliminato (F1 cleanup) ma user esiste | `ON DELETE SET NULL` | dashboard mostra "No website found" — F1 dovrebbe anche eliminare auth.user |

---

## 6. Testing strategy

### Test unit TypeScript (customer-dashboard)

`apps/customer-dashboard/__tests__/middleware.test.ts`:
- Path pubbliche bypass auth
- User non autenticato → redirect /login
- User autenticato + password_changed=false → redirect /change-password
- User autenticato + password_changed=true → render `/`
- /change-password no redirect-loop quando flag=false

### Test E2E manuale (post-deploy)

1. Manualmente crea un auth.user via Supabase dashboard:
   - Email: test@example.com
   - Password: temp123
   - User metadata: `{password_changed: false, company_name: "Test Co"}`
2. Manualmente UPDATE un site con `owner_user_id=<test-uid>`
3. Browser → /login
4. Inserisci credenziali → redirect a /change-password
5. Cambia password → redirect a /
6. Verifica: "Welcome, Test Co" + URL sito + 3 cards
7. Logout → /login → re-login → / direttamente
8. Test password reset: /forgot-password → email → reset link → nuova password → login

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

### Env vars (E1 only)

| Var | Scope | Valore |
|---|---|---|
| `NEXT_PUBLIC_SUPABASE_URL` | customer-dashboard Vercel | `https://smzmgzblbliprwbjptjs.supabase.co` |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | customer-dashboard Vercel | (anon key esistente) |

### Supabase Auth config (critico)

Settings → Auth → URL Configuration → aggiungere:
`https://agents-customer-dashboard.vercel.app/**`

ai "Redirect URLs allowed" — necessario per password reset link.

### Rollout plan

1. Apply migration `007_customer_onboarding.sql`
2. Scaffold customer-dashboard (code + tests)
3. Deploy customer-dashboard su Vercel + Supabase URL config
4. E2E test (manual auth.user creation)
5. Update BRAINSTORM_STATE + memory

---

## 8. Observability

- **Vercel function logs** del customer-dashboard mostrano middleware redirects (utile per debug "why is user stuck on /change-password")
- **Supabase Auth Logs** (`auth.audit_log_entries`) traccia ogni login/logout/password reset

---

## 9. Open questions per implementation phase

| # | Question | Default decision |
|---|---|---|
| 1 | Branding/UI | Match agents-sites premium (Inter + Playfair) |
| 2 | Logout UX | Bottone in dashboard, no conferma modal |
| 3 | Password complexity | Default Supabase ≥6 chars, no validation custom |
| 4 | Session lifetime | Default Supabase (1h access + 30d refresh) |
| 5 | Multi-site future | Schema attuale 1:1 customer:site, espandibile |

---

## 10. Flusso completo platform (riferimento, parte di E1 in grassetto)

```
┌───────────────────────────────────────────────────────────────────────┐
│                                                                         │
│  B (Scraping) ─→ leads in DB                                           │
│                                                                         │
│  D-Phase1 (Setting cold call) ─→ lead.call_status=accepted              │
│                                                                         │
│  C (Builder) ─→ INSERT sites (published_at=NOW, payment_status='unpaid')│
│                                                                         │
│  D-Phase2 (Setting site-ready call, secondo agente ElevenLabs)          │
│            ─→ chiama stesso lead, vende $349                            │
│            ─→ trigger F2: invio WhatsApp con Stripe Checkout link       │
│                                                                         │
│  F1 (Stripe Checkout + webhook):                                        │
│       │                                                                 │
│       ├─ paga in 48h →                                                  │
│       │   payment.succeeded webhook:                                    │
│       │     • CREATE auth.user with metadata                            │
│       │     • UPDATE sites SET owner_user_id, payment_status='paid'     │
│       │     • Send welcome email with dashboard credentials             │
│       │       ↓                                                         │
│       │  *** E1 entra in scena ***                                      │
│       │   Cliente clicca link in email → login → change password →      │
│       │   dashboard home con URL sito + coming-soon cards               │
│       │                                                                 │
│       └─ non paga in 48h → cleanup cron:                                │
│           • DELETE FROM sites WHERE payment_status='unpaid' AND          │
│             published_at < NOW() - 48h                                  │
│                                                                         │
└───────────────────────────────────────────────────────────────────────┘
```

**E1 scope = il box grassetto sopra**: la customer dashboard quando il cliente clicca il link nella welcome email post-pagamento.

---

## 11. Riferimenti

- Requirements originali: `docs/superpowers/specs/sub-project-E-requirements.md`
- Spec Builder Agent (esistente, non modificato in E1): `docs/superpowers/specs/2026-04-25-website-builder-design.md`
- Spec Setting Agent: `docs/superpowers/specs/2026-04-28-setting-agent-design.md`
- Stato infra: `BRAINSTORM_STATE.md`
- Sub-progetti F1/F2/D-Phase2: da brainstormare dopo E1 deploy
