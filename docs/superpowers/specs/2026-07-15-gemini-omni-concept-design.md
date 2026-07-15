# Concetto "Gemini Omni" — Studio di fattibilità e design

**Data**: 2026-07-15
**Stato**: Bozza (studio di fattibilità — non ancora approvato)
**Scope**: Valutare se e come portare il concetto **Omni** (modello nativamente multimodale e real-time, in stile Gemini Live / GPT-4o) dentro `agents-platform`, e proporre un design concreto innestato sul codice esistente.

---

## 1. Che cos'è il concetto "Omni"

**Omni** (Gemini Omni, GPT-4o "omni") = **un unico modello nativamente multimodale e real-time**:

- Ascolta, ragiona e parla dentro lo **stesso modello**, senza incatenare STT → LLM → TTS come servizi separati.
- Conversazione parlata a **bassa latenza** (le cosiddette *Live API* voce-a-voce), con barge-in e comprensione nativa di tono/emozione.
- Accetta più modalità in input (testo, audio, immagini, video) e produce output in più modalità.

La domanda dell'utente — *"è possibile creare lo stesso concetto di Gemini Omni?"* — si traduce in: **possiamo dare alla piattaforma un'esperienza Omni?** La risposta è **sì**, con tre possibili interpretazioni (§3). Questo documento raccomanda la strada A.

---

## 2. Com'è fatta la piattaforma oggi

Pipeline di 3 agenti event-driven, con Supabase come bus di eventi (`events` table) e `BaseAgent` (`packages/agent_framework/base_agent.py`) che fa polling degli eventi `pending`.

| Agente | Cosa fa | AI / provider oggi |
|---|---|---|
| **Scraping** (`apps/workers/scraping_worker`) | trova lead (attività locali) da OpenStreetMap/Overpass | nessun LLM |
| **Setting** (`apps/workers/setting_agent`) | cold call + sales call, SMS, Stripe | **ElevenLabs** Conv AI (voce) + **Twilio** (telefonia) + **Claude** (analisi transcript) |
| **Website Builder** (`apps/workers/website_builder`) | genera il sito (template + copy) | **Claude** |

### Punto chiave: oggi la voce NON è "omni"

Il percorso vocale del **Setting Agent** è una *catena* di servizi, non un modello unico:

```
Setting Agent → ElevenLabs Conv AI (STT + LLM + TTS gestiti da ElevenLabs) → Twilio → 📞 lead
                                                                                   │
                             a fine chiamata: webhook → transcript → Claude analizza (async)
```

- La conversazione real-time è **delegata a ElevenLabs** (che internamente orchestra STT→LLM→TTS).
- Il "ragionamento" della piattaforma (analisi transcript, generazione copy) è **Claude**, ma gira **a chiamata finita**, non durante la conversazione.

Quindi: un'esperienza conversazionale real-time **esiste già** (via ElevenLabs), ma non è un singolo modello multimodale nativo → non è "Omni" in senso letterale.

---

## 3. Tre interpretazioni di "creare il concetto Omni"

| # | Interpretazione | "Omni" significa | Dove tocca il codice | Sforzo | Rischio |
|---|---|---|---|---|---|
| **A** ⭐ | **Agente vocale Omni real-time** | multimodale nativo voce-a-voce | `setting_agent` (sostituisce/affianca `elevenlabs_client.py`) | Medio | Medio (nuovo vendor, tocca il path di produzione) |
| **B** | **Un unico agente "tuttofare"** | onnisciente, un cervello per l'intero funnel | refactor di `BaseAgent` + i 3 worker | Alto | Alto (riscrive l'architettura) |
| **C** | **Assistente Omni in dashboard** | chat multimodale (testo/voce/immagini) | `apps/dashboard` (`AgentChat.tsx`, `/api/chat`) | Basso-medio | Basso (superficie isolata) |

**Raccomandazione: Strada A.** È l'interpretazione letterale di "Gemini Omni" (omni = *omni-modale* real-time) e cade esattamente dove la piattaforma ha già la voce. B è un refactoring architetturale che non è ciò che "Omni" descrive. C è utile ma marginale rispetto al core business (le telefonate di vendita).

Il resto del documento dettaglia la **Strada A**; B e C sono schizzate in Appendice.

---

## 4. Strada A — Setting Agent con voce Omni nativa (Gemini Live)

### 4.1 Idea

Sostituire (o affiancare dietro feature-flag) lo stack **ElevenLabs Conv AI** con un modello **voce-a-voce nativo real-time** — la **Gemini Live API** di Google — mantenendo **Twilio** per la linea telefonica PSTN.

Un solo modello ascolta l'audio del lead, ragiona e risponde in tempo reale, con la persona di vendita nel system prompt. Il transcript continua a essere analizzato a fine chiamata (o, opzione avanzata, il modello stesso emette l'esito con tool-calling durante la conversazione).

### 4.2 Perché Gemini e non Claude

| Provider | Voce-a-voce real-time nativa? | Nota |
|---|---|---|
| **Gemini (Live API)** | ✅ Sì | È letteralmente il "Gemini Omni" richiesto |
| **OpenAI (Realtime API)** | ✅ Sì | Alternativa equivalente (GPT Realtime) |
| **Claude (Anthropic)** | ❌ Non oggi | Testo + visione/documenti; nessuna voce-a-voce real-time nativa |
| **ElevenLabs (attuale)** | ⚠️ "Quasi" | Real-time ma è una *catena* STT→LLM→TTS, non un modello unico |

⚠️ **Nota onesta**: tutta la piattaforma gira su **Claude**. L'Omni vocale *letterale* richiede un **secondo provider** (Google), con una nuova chiave API e una nuova dipendenza — non è un semplice cambio di modello. Va deciso consapevolmente (vedi §8, decisioni aperte).

### 4.3 Architettura proposta

```
┌─────────────────────────────────────────────────────────┐
│  SETTING AGENT (Railway, Python)                        │
│  • BaseAgent (invariato)                                │
│  • gemini_live_client.py  ← NUOVO (sostituisce el.abs)  │
│  • media bridge: audio Twilio  ⇄  Gemini Live (WS)      │
└───────────────┬─────────────────────────────────────────┘
                │  Twilio Media Streams (WebSocket, audio μ-law 8kHz)
                ▼
┌─────────────────────────────────────────────────────────┐
│  TWILIO  (invariato: number +16627075199)               │
└───────────────┬─────────────────────────────────────────┘
                │ PSTN
                ▼
          📞 LEAD (US business)

        (in parallelo, streaming bidirezionale)
                ▲
                │  audio in ⇄ audio out (real-time)
┌───────────────┴─────────────────────────────────────────┐
│  GEMINI LIVE API (Google, WebSocket)                    │
│  • modello Omni: ascolta+ragiona+parla                  │
│  • system prompt = persona di vendita                   │
│  • (opz.) tool-calling → esito chiamata in-conversation │
└─────────────────────────────────────────────────────────┘
```

Differenza chiave rispetto a oggi: con ElevenLabs, ElevenLabs gestisce sia il collegamento a Twilio sia il ciclo STT/LLM/TTS. Con Gemini Live, **il nostro worker diventa il "media bridge"**: ponte tra lo stream audio Twilio e il WebSocket Gemini. Più controllo, più responsabilità (gestione audio real-time).

### 4.4 Impatto sul codice esistente

| File | Modifica |
|---|---|
| `apps/workers/setting_agent/gemini_live_client.py` | **NUOVO** — client WebSocket Gemini Live (session, invio audio, ricezione audio, tool-calls) |
| `apps/workers/setting_agent/media_bridge.py` | **NUOVO** — ponte Twilio Media Streams ⇄ Gemini Live (transcodifica μ-law↔PCM, buffering) |
| `apps/workers/setting_agent/main.py` | `_trigger_call_for_lead` / `_handle_site_ready`: dietro flag `VOICE_PROVIDER=gemini`, instrada su Gemini invece di `self._elevenlabs.trigger_outbound_call` |
| `apps/dashboard/src/app/api/webhooks/elevenlabs/route.ts` | affiancato da un handler per lo stream Gemini (o il worker riceve il media stream direttamente) |
| `.env.example` | aggiungere `GOOGLE_API_KEY`, `VOICE_PROVIDER`, `GEMINI_LIVE_MODEL` |
| `apps/workers/setting_agent/tests/` | nuovi test per client + bridge (mock WebSocket) |

**Feature flag** `VOICE_PROVIDER` (`elevenlabs` | `gemini`): permette rollout graduale e rollback immediato senza toccare la logica di business (lead picking, compliance, Stripe, SMS restano identici). L'astrazione naturale è un'interfaccia `VoiceProvider` con `trigger_outbound_call()` implementata da entrambi i client.

### 4.5 Cosa NON cambia

Tutta la logica di business è indipendente dal provider vocale e resta invariata:
- `lead_picker.py`, `compliance.py` (DNC + business hours), scheduler batch 10/giorno
- analisi transcript con **Claude** (`transcript_analyzer.py`, `sales_analyzer.py`)
- Stripe checkout + SMS Twilio + routing eventi (`setting.call_accepted` → builder, ecc.)

---

## 5. Provider, costi, variabili d'ambiente

| Voce | ElevenLabs (oggi) | Gemini Live (proposto) |
|---|---|---|
| Modello | STT+LLM+TTS orchestrati | modello Omni unico |
| Fatturazione | al minuto/carattere | a token audio in/out |
| Latenza | buona | tipicamente più bassa (nativo) |
| Naturalezza | alta (voci top EN) | alta, + comprensione nativa tono |
| Controllo | basso (black box) | alto (siamo noi il bridge) |
| Vendor | già attivo | **nuovo** (Google) |

Nuove env vars (bozza):

```bash
# Voice provider selection
VOICE_PROVIDER=elevenlabs        # elevenlabs | gemini

# Google Gemini Live (per VOICE_PROVIDER=gemini)
GOOGLE_API_KEY=your-google-key
GEMINI_LIVE_MODEL=gemini-live-...    # id modello Live da confermare a implementazione
```

> ⚠️ **Prezzi e ID modello vanno verificati alla documentazione Google al momento dell'implementazione** — non li fisso qui per non riportare numeri obsoleti.

---

## 6. Trade-off e rischi

**Pro**
- Concetto Omni *letterale*: un modello che ascolta, ragiona e parla.
- Latenza potenzialmente inferiore, conversazione più naturale.
- Più controllo sul flusso audio (possibile tool-calling in-conversation → esito senza analisi post-hoc).

**Contro / rischi**
- **Secondo vendor** (Google) accanto a Claude: nuova chiave, nuova dipendenza, superficie operativa in più.
- **Media bridging real-time è non banale**: gestire audio μ-law 8kHz Twilio ↔ PCM Gemini, jitter, barge-in, riconnessioni. È la parte tecnicamente più delicata (oggi ce la nasconde ElevenLabs).
- Tocca il **percorso di produzione** delle telefonate → serve feature-flag + rollout gestito.
- La qualità voce EN di ElevenLabs è già "top-tier" (vedi design D): il guadagno va **misurato**, non dato per scontato.

**Alternativa pragmatica**: se l'obiettivo è "esperienza conversazionale migliore" più che "Omni per etichetta", si può **restare su ElevenLabs** (che è già quasi-omni) e investire su prompt/voci. L'Omni-Gemini ha senso se si vuole la proprietà tecnica del modello unico e il tool-calling in-conversation.

---

## 7. Piano di implementazione a fasi (Strada A)

1. **Fase 0 — Spike isolato**: script standalone che apre una sessione Gemini Live, invia audio da file, riceve audio. Nessun Twilio. Valida modello + latenza + costo.
2. **Fase 1 — Media bridge**: `gemini_live_client.py` + `media_bridge.py` con test su WebSocket mockato. Twilio Media Streams ⇄ Gemini su una chiamata di test verso un numero interno.
3. **Fase 2 — Integrazione dietro flag**: `VOICE_PROVIDER=gemini` in `main.py`, riuso di tutta la logica di business. Rollout su 1–2 chiamate/giorno.
4. **Fase 3 — Tool-calling in-conversation (opz.)**: il modello emette l'esito (accepted/rejected) durante la chiamata → riduce/elimina l'analisi Claude post-hoc.
5. **Fase 4 — A/B e decisione**: confronto ElevenLabs vs Gemini su conversione/qualità/costo; si sceglie il default.

---

## 8. Decisioni aperte (da confermare con l'utente)

1. **Vendor**: si accetta di introdurre **Google/Gemini** come secondo provider accanto a Claude? (Alternativa: OpenAI Realtime, oppure restare su ElevenLabs.)
2. **Sostituzione o affiancamento**: Gemini rimpiazza ElevenLabs o convivono dietro flag? (Raccomandato: convivono → rollback facile.)
3. **Scope**: solo cold call, solo sales call, o entrambe?
4. **Output atteso**: fermarsi a questo design, o procedere allo **spike di Fase 0**?

---

## Appendice A — Strada B (agente "Omni" tuttofare)

Un solo agente con function-calling/tools che orchestra scraping → sito → vendita da un unico cervello (Claude con tools), invece dei 3 worker specializzati. "Omni" = onnisciente, non multimodale. Comporta un refactor profondo di `BaseAgent` e del routing eventi; alto rischio, basso ritorno rispetto all'architettura attuale che già funziona. **Sconsigliato ora.**

## Appendice B — Strada C (assistente Omni in dashboard)

Estendere `AgentChat.tsx` + `/api/chat` per accettare input multimodale (testo/voce/immagini) e rispondere. Superficie isolata, basso rischio, utile come "copilota" operativo interno sulla dashboard, ma marginale rispetto al core (le telefonate). Buon candidato come **secondo step**, dopo A.
