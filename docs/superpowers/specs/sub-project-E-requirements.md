# Sub-progetto E — Requisiti raccolti (placeholder)

**Stato**: Requisiti raccolti dall'utente, brainstorming formale **non ancora fatto**.
**Data ultima modifica**: 2026-04-25

Questo documento raccoglie le richieste esplicite dell'utente per Sub-progetto E (Multi-tenant admin dashboards + Blog generator). Verrà trasformato in design spec quando inizierà il brainstorming formale per E (dopo C e D).

---

## Requisiti dashboard cliente (per ogni sito generato dal Sub-progetto C)

### Accesso e credenziali

- Ogni sito web creato per un cliente deve avere una **dashboard personale dedicata** (dietro login)
- Login con **email + password standard** (auto-generata) fornita al cliente
- Le credenziali vengono inviate al cliente tramite **email + WhatsApp**
- Il cliente può cambiare la password al primo accesso

### Funzionalità della dashboard cliente

1. **Configurazione dominio personalizzato**
   - Il cliente può puntare un dominio proprio (es. `pizzeriamario.it`) al sito
   - Il sito di default resta accessibile dal sub-dominio gratuito (es. `pizzeria-mario.agentsplatform.app`)
   - Verifica DNS automatica + SSL automatico (Let's Encrypt o similar)

2. **Insight visite al sito**
   - Numero visite (giornaliere, settimanali, mensili)
   - Sorgenti traffico (diretto, social, ricerca)
   - Pagine più viste
   - Dispositivi (mobile vs desktop)
   - Geolocalizzazione visitatori (paese/città)

3. **Implicito**: il cliente NON può modificare i contenuti del sito direttamente in C. Editing siti e gestione blog → da definire in E.

### URL e accessibilità

- **Sub-dominio gratuito**: ogni sito viene creato con un URL standard `{slug}.agentsplatform.app` (gratis, default)
- **Custom domain (opzionale)**: il cliente può aggiungerne uno suo dalla dashboard

---

## Requisiti già noti per Sub-progetto E (dal brief originale)

- Blog generator: 30 giorni di articoli gratuiti per cliente che acquista
- Collegamento profili social Instagram/Facebook integrati nel sito
- Multi-tenant: ogni cliente vede solo il suo sito/dati

---

## Decisioni di scope (da Sub-progetto C)

Sub-progetto C **NON include**:
- ❌ Admin dashboard per cliente
- ❌ Login cliente
- ❌ Dominio custom
- ❌ Analytics/insights
- ❌ Editing del sito da parte del cliente

Sub-progetto C **include**:
- ✅ Generazione del sito iniziale (template + copy)
- ✅ Hosting al sub-dominio gratuito (`{slug}.agentsplatform.app`)
- ✅ URL pubblico restituito al Setting Agent

---

## Quando sarà brainstormato

Dopo:
- Sub-progetto C — Website Builder Agent
- Sub-progetto D — Voice + WhatsApp Agent

Quando arriviamo al brainstorming formale per E, useremo questo documento come input e creeremo il design spec definitivo `2026-XX-XX-multi-tenant-admin-design.md`.
