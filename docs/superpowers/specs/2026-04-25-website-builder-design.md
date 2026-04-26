# Sub-progetto C — Website Builder Agent (Reale)

**Data**: 2026-04-25 (v1) → 2026-04-26 (v2 — premium + lead capture)
**Stato**: v1 approvato e deployato. v2 (sezione 12) approvata, pending implementation.
**Scope**: Sostituire `builder_stub` con un agente reale che genera siti web personalizzati per i lead accettati dal Setting Agent. I siti vengono renderizzati dinamicamente da un nuovo progetto Next.js (`agents-sites`) leggendo i dati da Supabase.

**v2 add**: i siti devono essere ULTRA PREMIUM, struttura Problema/Beneficio/Soluzione, e i form di contatto devono inviare i lead all'email del cliente proprietario del sito.

---

## 1. Contesto

Sub-progetto C della piattaforma agenti AI. Sub-progetti A e B sono già live. Adesso sostituiamo `builder_stub` con un agente reale che:

- Riceve `setting.call_accepted` dal Setting Agent (oggi stub, domani Sub-progetto D)
- Analizza il target (categoria + brief di chiamata se disponibile)
- Sceglie un template tra 3 (`hospitality`, `service`, `generic`)
- Genera copy via Claude
- Salva il sito in Supabase
- Emette `builder.website_ready` con l'URL pubblico

Il rendering del sito è gestito da un **nuovo progetto Vercel** (`apps/agents-sites/`), che legge i dati dal DB e renderizza dinamicamente.

---

## 2. Decisioni architetturali

| Aspetto | Scelta | Motivazione |
|---|---|---|
| Generazione siti | **Template multipli + Claude sceglie** (3 template) | Equilibrio tra varietà e lavoro upfront; pattern usato da Durable.co |
| Hosting siti | **Path-based su Vercel free** (`agents-sites.vercel.app/s/{slug}`) | Zero costi, zero gestione domini per noi; il custom domain è self-service in Sub-progetto E |
| Analisi target | **Categoria del lead (template) + call_brief (copy)** con graceful degradation | Funziona anche con Setting stub; migliora automaticamente quando D sarà reale |
| Storage siti | **Database-driven** (JSONB in Supabase, no file generati) | Aggiornamenti istantanei, zero filesystem, zero rebuild per cliente |
| Asset/immagini MVP | **Hot-link Unsplash** in `image_url` | Zero asset upload necessario per MVP; Sub-progetto E aggiungerà upload custom |
| Renderer stack | **Nuovo progetto Next.js separato** (`apps/agents-sites/`) | Separazione di responsabilità: dashboard ≠ siti pubblici |
| Trigger | **Solo su `setting.call_accepted`** dal Setting Agent | Evita generazioni inutili; Builder è passivo |

### Mappatura categoria → template (statica)

| Categoria | template_kind |
|---|---|
| `restaurant` | `hospitality` |
| `fitness_centre` | `hospitality` |
| `hairdresser` | `service` |
| `beauty` | `service` |
| `dentist` | `service` |
| `photographer` | `service` |
| (altre) | `generic` |

Claude sceglie SOLO la palette colori, non il template (riduce rischio di scelte sbagliate).

---

## 3. Architettura di sistema

```
┌─────────────────────────────────────────────────────┐
│  SETTING AGENT (D futuro / oggi stub)               │
│  ↓ emette                                            │
│  setting.call_accepted {lead_id, lead, call_brief?} │
└────────────────────┬────────────────────────────────┘
                     │ via events table (Supabase)
                     ▼
┌─────────────────────────────────────────────────────┐
│  WEBSITE BUILDER AGENT (Python worker, Railway)     │
│  Sostituisce builder_stub                            │
│                                                      │
│  Pipeline interno:                                   │
│  1. Riceve setting.call_accepted                     │
│  2. target_analyzer (categoria → template kind +     │
│     Claude per palette colori)                       │
│  3. copy_generator (Claude genera content JSON)      │
│  4. slug_generator (slug univoco, dedup -2/-3)       │
│  5. INSERT in `sites` table                          │
│  6. Emette builder.website_ready {site_url}          │
└────────────────────┬────────────────────────────────┘
                     │
                     ▼
            ┌──────────────────┐
            │  SUPABASE        │
            │  • sites (NUOVA) │
            │  • leads         │
            │  • events        │
            └────────┬─────────┘
                     │ realtime + reads
                     ▼
┌─────────────────────────────────────────────────────┐
│  AGENTS-SITES (Next.js, NUOVO Vercel project)       │
│  Renderer dinamico per i siti dei clienti           │
│                                                      │
│  Route: /s/[slug] → fetch site → render template    │
│  Niente logica AI/business — solo lettura + render  │
│  URL: agents-sites.vercel.app/s/{slug}              │
└─────────────────────────────────────────────────────┘
```

### Principi

- **Database-driven website**: i siti sono righe in `sites`, non file generati. Il renderer legge dinamicamente.
- **Defensive rendering**: ogni primitive (Hero, ServicesList, ContactBlock) gestisce graceful campi mancanti.
- **Graceful degradation pipeline**: il `call_brief` è opzionale → C funziona anche senza, migliora con.
- **Separazione progetti Vercel**: dashboard (`agents-dashboard`) ≠ siti clienti (`agents-sites`).

---

## 4. Struttura del codice

### Modifiche e nuovi file

```
agents-platform/
├── apps/
│   ├── workers/
│   │   ├── builder_stub/              # ← RIMOSSO
│   │   └── website_builder/            # ← NUOVO
│   │       ├── __init__.py
│   │       ├── main.py                 # BuilderAgent
│   │       ├── claude_client.py        # Anthropic SDK wrapper
│   │       ├── target_analyzer.py      # template_kind + colors
│   │       ├── copy_generator.py       # content JSON
│   │       ├── slug_generator.py       # slug univoco
│   │       └── tests/
│   │           ├── test_slug_generator.py
│   │           ├── test_target_analyzer.py
│   │           ├── test_copy_generator.py
│   │           └── test_pipeline_integration.py
│   ├── dashboard/                      # esiste, no modifiche in C
│   └── agents-sites/                   # ← NUOVO Next.js project
│       ├── src/
│       │   ├── app/
│       │   │   ├── s/[slug]/
│       │   │   │   └── page.tsx
│       │   │   ├── layout.tsx
│       │   │   └── globals.css
│       │   ├── components/
│       │   │   ├── templates/
│       │   │   │   ├── HospitalityTemplate.tsx
│       │   │   │   ├── ServiceTemplate.tsx
│       │   │   │   └── GenericTemplate.tsx
│       │   │   └── primitives/
│       │   │       ├── Hero.tsx
│       │   │       ├── ServicesList.tsx
│       │   │       ├── About.tsx
│       │   │       └── ContactBlock.tsx
│       │   └── lib/
│       │       └── supabase.ts
│       ├── package.json
│       ├── next.config.js
│       └── tailwind.config.ts
├── packages/
│   └── events_schema/
│       └── schemas/
│           └── setting.json            # update: call_accepted con call_brief
└── supabase/
    └── migrations/
        └── 004_sites.sql               # NUOVA
```

---

## 5. Componenti

### 5.1 BuilderAgent (`main.py`)

Eredita da `BaseAgent`. Gestisce solo `setting.call_accepted`.

```python
class BuilderAgent(BaseAgent):
    def __init__(self, **kwargs):
        super().__init__(agent_id="builder", **kwargs)
        self._claude = create_anthropic_client()

    async def handle_event(self, event: dict) -> list[dict]:
        if event.get("type") != "setting.call_accepted":
            return []

        payload = event["payload"]
        lead = payload["lead"]
        call_brief = payload.get("call_brief")  # opzionale

        # 1. Emit build_started
        self._emitter.emit(
            event_type="builder.build_started",
            payload={"lead_id": payload["lead_id"]},
        )

        # 2. Analyze target
        target = analyze_target(lead["category"], call_brief, self._claude)

        # 3. Generate copy
        content = generate_copy(target["template_kind"], lead, call_brief, self._claude)

        # 4. Generate unique slug
        slug = generate_unique_slug(lead["name"], self._client)

        # 5. Insert site (base URL configurable via env)
        sites_base = os.environ.get("AGENTS_SITES_BASE_URL", "https://agents-sites.vercel.app")
        site_url = f"{sites_base}/s/{slug}"
        self._client.table("sites").insert({
            "lead_id": payload["lead_id"],
            "slug": slug,
            "template_kind": target["template_kind"],
            "category": lead["category"],
            "colors": target["colors"],
            "content": content,
            "published_url": site_url,
        }).execute()

        # 6. Emit website_ready
        return [{
            "type": "builder.website_ready",
            "target_agent": "setting",
            "payload": {
                "lead_id": payload["lead_id"],
                "site_url": site_url,
            },
        }]
```

### 5.2 `target_analyzer.py`

```python
TEMPLATE_KIND_MAP = {
    "restaurant": "hospitality",
    "fitness_centre": "hospitality",
    "hairdresser": "service",
    "beauty": "service",
    "dentist": "service",
    "photographer": "service",
}

def analyze_target(category: str, call_brief: dict | None, claude_client) -> dict:
    """
    Returns:
        {
          "template_kind": "hospitality"|"service"|"generic",
          "colors": {"primary": "#xx", "accent": "#xx", "text": "#xx", "background": "#xx"},
        }
    """
    template_kind = TEMPLATE_KIND_MAP.get(category, "generic")
    colors = _generate_palette(category, call_brief, claude_client)
    return {"template_kind": template_kind, "colors": colors}


def _generate_palette(category, call_brief, claude_client) -> dict:
    # Prompt Claude for a 4-color palette suitable for the category
    # Validate output is valid hex colors
    # Fallback to category-default palette if Claude fails
```

### 5.3 `copy_generator.py`

```python
TEMPLATE_CONTENT_SCHEMA = {
    "hospitality": ["hero", "services", "about", "contacts"],
    "service": ["hero", "about", "services", "contacts"],
    "generic": ["hero", "about", "contacts"],
}

def generate_copy(template_kind, lead, call_brief, claude_client) -> dict:
    """
    Builds prompt with category, lead info, optional brief.
    Calls Claude with response_format=json.
    Validates output against template schema.
    Retries up to 3 times on JSON parse error.
    """
```

Prompt structure:
```
Sei un copywriter italiano per piccole attività locali.
Genera un sito web per:
- Categoria: {category}
- Nome: {company_name}
- Città: {city}
{if call_brief:}
- Note dalla chiamata: {call_brief.custom_requests}
- Servizi: {call_brief.services}
- Stile: {call_brief.style_preference}
{endif}

Output JSON con questi campi: {template_schema}
Tono professionale, orientato alla conversione.
```

### 5.4 `slug_generator.py`

```python
from slugify import slugify

def generate_unique_slug(company_name: str, supabase_client) -> str:
    base = slugify(company_name, lowercase=True)
    candidate = base
    n = 2
    while _slug_exists(candidate, supabase_client):
        candidate = f"{base}-{n}"
        n += 1
    return candidate

def _slug_exists(slug: str, supabase_client) -> bool:
    result = supabase_client.table("sites").select("id").eq("slug", slug).execute()
    return bool(result.data)
```

### 5.5 Next.js renderer — `app/s/[slug]/page.tsx`

```tsx
import { notFound } from "next/navigation";
import { supabase } from "@/lib/supabase";
import { HospitalityTemplate } from "@/components/templates/HospitalityTemplate";
import { ServiceTemplate } from "@/components/templates/ServiceTemplate";
import { GenericTemplate } from "@/components/templates/GenericTemplate";

const TEMPLATES = {
  hospitality: HospitalityTemplate,
  service: ServiceTemplate,
  generic: GenericTemplate,
};

export const revalidate = 60; // 1 min cache

export default async function SitePage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  const { data: site } = await supabase
    .from("sites")
    .select("*")
    .eq("slug", slug)
    .maybeSingle();

  if (!site) notFound();

  const Template = TEMPLATES[site.template_kind] ?? GenericTemplate;

  const styleVars = {
    "--site-primary": site.colors.primary,
    "--site-accent": site.colors.accent,
    "--site-text": site.colors.text,
    "--site-bg": site.colors.background,
  } as React.CSSProperties;

  return (
    <main style={styleVars} className="min-h-screen bg-[var(--site-bg)] text-[var(--site-text)]">
      <Template content={site.content} />
    </main>
  );
}
```

### 5.6 Templates: composizione di primitives

```tsx
// HospitalityTemplate.tsx
export function HospitalityTemplate({ content }: { content: SiteContent }) {
  return (
    <>
      <Hero {...content.hero} variant="image-bg" />
      <ServicesList items={content.services ?? []} variant="grid" />
      <About {...content.about} />
      <ContactBlock {...content.contacts} variant="map" />
    </>
  );
}

// ServiceTemplate.tsx
export function ServiceTemplate({ content }: { content: SiteContent }) {
  return (
    <>
      <Hero {...content.hero} variant="centered-text" />
      <About {...content.about} />
      <ServicesList items={content.services ?? []} variant="list-with-prices" />
      <ContactBlock {...content.contacts} variant="form" />
    </>
  );
}

// GenericTemplate.tsx — fallback minimale
export function GenericTemplate({ content }: { content: SiteContent }) {
  return (
    <>
      <Hero {...content.hero} variant="centered-text" />
      <About {...content.about} />
      <ContactBlock {...content.contacts} variant="simple" />
    </>
  );
}
```

### 5.7 Primitives: defensive rendering

Ogni primitive accetta i campi tutti opzionali e ha fallback per campi mancanti:

```tsx
export function Hero({
  headline,
  subheadline,
  cta_text,
  image_url,
  variant = "centered-text",
}: {
  headline?: string;
  subheadline?: string;
  cta_text?: string;
  image_url?: string;
  variant?: "centered-text" | "image-bg";
}) {
  if (!headline) return null;
  // render...
}
```

---

## 6. Data Model

### Migration `004_sites.sql`

```sql
CREATE TABLE sites (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    lead_id UUID NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
    slug TEXT NOT NULL UNIQUE,
    template_kind TEXT NOT NULL CHECK (template_kind IN ('hospitality','service','generic')),
    category TEXT NOT NULL,
    colors JSONB NOT NULL DEFAULT '{}'::jsonb,
    content JSONB NOT NULL DEFAULT '{}'::jsonb,
    published_url TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (lead_id)
);

CREATE INDEX idx_sites_slug ON sites(slug);
CREATE INDEX idx_sites_category ON sites(category);

ALTER PUBLICATION supabase_realtime ADD TABLE sites;

CREATE TRIGGER sites_updated_at
    BEFORE UPDATE ON sites
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();
```

### Struttura JSONB `content`

```json
{
  "hero": {
    "headline": "string",
    "subheadline": "string",
    "cta_text": "string",
    "image_url": "string (Unsplash CDN)"
  },
  "services": [
    {"title": "string", "description": "string", "price": "string (optional)"}
  ],
  "about": {
    "title": "string",
    "body": "string"
  },
  "contacts": {
    "phone": "string",
    "email": "string (optional)",
    "address": "string (optional)",
    "opening_hours": "string (optional)"
  }
}
```

### Struttura JSONB `colors`

```json
{
  "primary": "#8B4513",
  "accent": "#D4A574",
  "text": "#2C2C2C",
  "background": "#FAF7F2"
}
```

### Schema events update

`packages/events_schema/schemas/setting.json` aggiornato:

```json
"setting.call_accepted": {
  "type": "object",
  "properties": {
    "lead_id": { "type": "string" },
    "lead": {
      "type": "object",
      "properties": {
        "name": { "type": "string" },
        "phone": { "type": "string" },
        "email": { "type": "string" },
        "category": { "type": "string" },
        "city": { "type": "string" }
      },
      "required": ["name", "phone"]
    },
    "call_brief": {
      "type": "object",
      "properties": {
        "custom_requests": { "type": "string" },
        "services": { "type": "array", "items": {"type": "string"} },
        "target_audience": { "type": "string" },
        "style_preference": { "type": "string" },
        "opening_hours": { "type": "string" }
      }
    }
  },
  "required": ["lead_id", "lead"]
}
```

`call_brief` non è required (graceful degradation).

---

## 7. Data Flow

```
1. setting.call_accepted ricevuto da BuilderAgent
   payload: {lead_id, lead, call_brief?}
   ↓
2. emit builder.build_started {lead_id}
   ↓
3. analyze_target(lead.category, call_brief)
   - mapping statico → template_kind
   - Claude → palette colori (4 hex)
   ↓
4. generate_copy(template_kind, lead, call_brief)
   - Prompt Claude con context completo
   - Parse JSON response
   - Validate vs schema template
   - Retry max 3 su parse error
   ↓
5. generate_unique_slug(lead.name)
   - slugify(name) → "pizzeria-da-mario"
   - Check DB, append -2, -3 se collisione
   ↓
6. INSERT in sites
   ↓
7. emit builder.website_ready {lead_id, site_url}
   target_agent: "setting"
   ↓
8. (Setting Agent riceve → richiama il lead per follow-up vendita)
```

---

## 8. Error Handling

### Claude API failures
- Rate limit → retry con backoff esponenziale (5s, 15s, 45s)
- JSON malformato → 3 retry totali, poi `FatalError` → dead_letter
- Timeout → ritento

### Slug collisions
- Risolto da `generate_unique_slug` con suffisso numerico
- DB UNIQUE constraint come safety net (race condition → catch + retry)

### Categoria non mappata
- Fallback automatico a `template_kind = "generic"`

### Render failures (Next.js)
- Mai eccezioni nel renderer
- Ogni primitive gestisce campi mancanti con fallback (es. Hero ritorna null se manca headline)
- Pagina sempre visibile, anche se incompleta

### Lead già con sito
- DB UNIQUE su `lead_id` previene doppia generazione
- Se evento `setting.call_accepted` arriva per lead con sito già esistente → log warning, skip

---

## 9. Testing

### Unit tests Python

| File | Cosa testa |
|---|---|
| `test_slug_generator.py` | Slug base, escape caratteri, dedup con suffisso |
| `test_target_analyzer.py` | Mapping categoria → template, fallback "generic", validazione palette |
| `test_copy_generator.py` | Mock Claude, content JSON valido, gestione brief mancante |
| `test_pipeline_integration.py` | E2E con mock Anthropic + mock Supabase |

### Component tests Next.js

| File | Cosa testa |
|---|---|
| `Hero.test.tsx` | Render con campi mancanti |
| `ServicesList.test.tsx` | Array vuoto, lista lunga |
| `ContactBlock.test.tsx` | Senza phone, senza address |
| `templates/*.test.tsx` | Snapshot dei 3 template |

### E2E manuale (post-deploy)

Trigger `setting.call_accepted` da MCP SQL → verifica:
1. Riga in `sites` creata
2. URL `agents-sites.vercel.app/s/{slug}` raggiungibile
3. Sito renderizzato correttamente per ogni `template_kind`

---

## 10. Deployment

### Migration Supabase
Applicata via MCP `apply_migration` con file `004_sites.sql`.

### Railway: sostituzione `builder_stub`
1. Push codice nuovo (`apps/workers/website_builder/`)
2. Update start command: `python -m apps.workers.builder_stub.main` → `python -m apps.workers.website_builder.main`
3. Aggiungere env vars:
   - `ANTHROPIC_API_KEY` (non c'era prima per builder_stub)
   - `AGENTS_SITES_BASE_URL` (es. `https://agents-sites-growth-agent.vercel.app`) — settato dopo il deploy Vercel
4. Auto-restart on push

### Vercel: nuovo progetto `agents-sites`
1. Import GitHub repo, root: `apps/agents-sites/`
2. Env vars: `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY`
3. Deploy automatico da push

URL risultante: tipo `agents-sites-{org}.vercel.app/s/{slug}`. Quando avrai un dominio, lo aggiungi su Vercel.

### Dipendenze nuove

**Python** (`requirements.txt`):
```
anthropic>=0.40
python-slugify>=8.0
```

**Next.js** (nuovo progetto, `apps/agents-sites/package.json`):
```json
{
  "dependencies": {
    "next": "^16",
    "react": "^19",
    "react-dom": "^19",
    "@supabase/supabase-js": "^2"
  }
}
```

---

## 11. Vincoli e decisioni future

- **Asset/immagini**: hot-link Unsplash per MVP, no upload custom (rimandato a Sub-progetto E)
- **Edit del sito**: non disponibile in C (solo creazione iniziale). Editing self-service → Sub-progetto E
- **Custom domain**: non gestito in C (default subdomain Vercel free). Self-service via dashboard cliente → Sub-progetto E
- **Analytics visite**: non in C, nemmeno tracking lato server. Sub-progetto E aggiungerà counter visite (Plausible o Vercel Analytics)
- **Re-generation**: se l'utente vuole un sito diverso, oggi va eliminato manualmente da DB e ritrigerato l'evento. Re-gen dalla dashboard → futuro
- **A/B testing template**: non disponibile, ogni lead ottiene una sola generazione

---

## 12. v2 — Premium copy + Lead capture (richiesta utente 2026-04-26)

Questa sezione estende lo scope della v1 con 3 nuovi requisiti dichiarati dall'utente:

### 12.1 Sito ULTRA PREMIUM

I siti generati devono comunicare **valore alto, autorità, professionalità**. Non possono sembrare "templatati" o generici. Il design deve trasmettere "questi sono professionisti che valgono il prezzo".

**Implementazione**:
- **Tipografia premium**: usare font Google sans-serif moderni (Inter per UI, Playfair Display o Fraunces per heading di brand)
- **Spacing generoso**: padding verticale 80-128px tra sezioni, max-width contenuto 1200px
- **Animazioni soft on-scroll**: fade-in + translate-y leggero quando le sezioni entrano in viewport (Intersection Observer)
- **Gradient overlay sui hero** invece di colori piatti (quando ha image_url)
- **Hover states su CTA**: scale 1.02 + shadow espansa
- **Micro-elementi premium**: divider sottili, icon set coerente (lucide-react), badge "trusted by..." se applicabile
- **Dark mode-ready** (anche se non attivato di default — palette già supportano accent contrastante)

**Vincolo**: nessun template "stockphoto-heavy" o "Wix-vibes". Stile più vicino a Linear, Stripe, Apple-product-page.

### 12.2 Struttura Problema → Beneficio → Soluzione

Il copy generato da Claude deve seguire un framework di conversione esplicito invece di "About generico":

**Schema content v2** (sostituisce le sezioni "about" generiche):

```json
{
  "hero": {
    "headline": "string (promessa di valore in 1 riga)",
    "subheadline": "string (chiarimento + per chi è)",
    "cta_text": "string (azione, es. 'Richiedi un preventivo')",
    "cta_link": "#contact (anchor al form)",
    "image_url": "string"
  },
  "problem": {
    "title": "string (es. 'Il problema che risolviamo')",
    "body": "string (descrizione del pain point del visitatore)",
    "bullets": ["pain1", "pain2", "pain3"]
  },
  "benefits": {
    "title": "string (es. 'Cosa ottieni')",
    "items": [
      {"title": "Beneficio 1", "description": "string", "icon": "string opzionale"},
      {"title": "Beneficio 2", "description": "string"},
      {"title": "Beneficio 3", "description": "string"}
    ]
  },
  "solution": {
    "title": "string (es. 'Come funziona')",
    "body": "string (la soluzione: chi siamo / cosa offriamo concretamente)",
    "cta_text": "string (es. 'Inizia ora')",
    "cta_link": "#contact"
  },
  "services": [...],            // come v1, opzionale
  "contacts": {                  // METADATA, NON form fields
    "phone": "...",
    "address": "...",
    "opening_hours": "..."
  }
}
```

**Prompt Claude v2**: include il framework PBS esplicitamente:
```
Genera testi italiani per un sito web seguendo il framework Problema → Beneficio → Soluzione.

PROBLEMA: identifica il pain point principale del cliente target di {category}.
BENEFICI: 3 risultati concreti che ottengono lavorando con {company_name}.
SOLUZIONE: come {company_name} risolve il problema in modo unico.

Tono: professionale, sicuro, orientato alla conversione. Niente "Chi siamo" generico.
Ogni CTA deve linkare a "#contact" (anchor del form).
```

### 12.3 Form di contatto reale → email del cliente

Il `ContactBlock` non è più solo "display di telefono/email" ma include un **form HTML reale** che inoltra le submissions all'**email del lead proprietario del sito**.

**Architettura form submission**:

```
Visitatore del sito (es. cerca pizzeria a Milano)
  └─> compila form su https://agents-sites.vercel.app/s/pizzeria-mario
        └─> POST /api/contact-form { site_id, name, message, contact }
              └─> Server-side:
                    1. Recupera site → lead_id → leads.email (il PROPRIETARIO)
                    2. Salva submission in tabella `site_submissions`
                    3. Invia email a leads.email con il messaggio
                    4. Emette evento `site.lead_received` (per dashboard analytics)
              └─> Risposta {ok: true} → form mostra "Grazie, ti ricontatteremo"
```

**Nuova tabella `site_submissions`**:
```sql
CREATE TABLE site_submissions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    site_id UUID NOT NULL REFERENCES sites(id) ON DELETE CASCADE,
    visitor_name TEXT,
    visitor_email TEXT,
    visitor_phone TEXT,
    message TEXT NOT NULL,
    forwarded_to_email TEXT NOT NULL,  -- email del cliente
    forwarded_at TIMESTAMPTZ,
    forward_error TEXT,                 -- se invio fallito
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_submissions_site ON site_submissions(site_id, created_at DESC);
```

**Servizio email**: usiamo **Resend** (resend.com) — free tier 3000 email/mese, integrazione Next.js semplice. Alternative: SendGrid, Postmark.

**Nuovo API route `apps/agents-sites/src/app/api/contact-form/route.ts`**:
- POST riceve `{site_id, visitor_name, visitor_email, visitor_phone, message}`
- Carica `site` da DB → segue `lead_id` → carica `leads.email`
- Se `leads.email` mancante → invia a fallback admin email + log warning
- Invia email tramite Resend al proprietario, con corpo formattato:
  ```
  Subject: [{site_name}] Nuovo contatto da: {visitor_name}
  Body:
    Nome: {visitor_name}
    Email: {visitor_email}
    Telefono: {visitor_phone}
    
    Messaggio:
    {message}
    
    --
    Inviato da {published_url}
  ```
- INSERT in `site_submissions`
- Emette `site.lead_received` (per metriche dashboard)

**Edge case lead.email mancante**: durante OSM scraping molti lead non hanno `email`. Quando un lead accetta in chiamata (Sub-progetto D), il Setting Agent **deve raccogliere e salvare l'email del cliente**. Se non c'è → fallback a un'email admin (la nostra) + warning.

### 12.4 Modifiche ai template (rendering side)

I 3 template (`HospitalityTemplate`, `ServiceTemplate`, `GenericTemplate`) ricevono nuove primitive:
- **Problem**: section con titolo + body + bullets (con icon ❌ o "•")
- **Benefits**: grid di card (3-4 colonne desktop, 1 mobile) con icon + title + description
- **Solution**: section narrativa + CTA prominente
- **ContactForm** (sostituisce `ContactBlock` con form vero): input name/email/phone/message + submit

Tutti i CTA in hero, solution, e header (se aggiunto) puntano a `#contact` → smooth-scroll alla section form.

### 12.5 Nuove dipendenze

**Next.js (agents-sites)**:
- `resend` (npm) — email API
- `react-hook-form` + `zod` — form validation lato client

**Env vars nuove (Vercel agents-sites prod)**:
- `RESEND_API_KEY` — da resend.com (signup necessario)
- `FROM_EMAIL` — es. `noreply@agentsplatform.app` (o un indirizzo Resend gratuito tipo `onboarding@resend.dev` per MVP)
- `ADMIN_FALLBACK_EMAIL` — se lead.email mancante

### 12.6 Test aggiuntivi v2

| Test | Cosa verifica |
|---|---|
| `test_copy_generator_v2.py` | Output Claude include problem/benefits/solution con bullets |
| `apps/agents-sites/src/app/api/contact-form/route.test.ts` | Lookup site→lead→email, invio Resend mockato, INSERT submission |
| `ContactForm.test.tsx` | Render form, validation, success/error states |

### 12.7 Migration v2

```sql
-- 005_site_submissions.sql
CREATE TABLE site_submissions (...);
CREATE INDEX ...;
ALTER PUBLICATION supabase_realtime ADD TABLE site_submissions;
```

E un seed update (opzionale): per i siti già generati con content v1 (schema "about" only), Claude può rigenerare il content nella v2 quando l'utente lo decide. Per ora si convive: se `content.problem` esiste → render v2, sennò → render v1.

### 12.8 Riepilogo cambiamenti vs v1

| Aspetto | v1 | v2 |
|---|---|---|
| Copy structure | Hero + Services + About + Contacts | Hero + Problem + Benefits + Solution + Services (opt) + Contacts |
| ContactBlock | Display info | Form HTML reale |
| Form submissions | N/A | Salvate in `site_submissions`, inviate a `lead.email` via Resend |
| Premium look | Standard Tailwind | Tipografia + animazioni + spacing generoso |
| Schema events | Stesso v1 | + `site.lead_received` quando arriva una submission |
