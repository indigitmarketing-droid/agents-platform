# Pilota Spesa & Profitto — Google Ads Script

Script unico per **Google Ads** (`Strumenti → Azioni collettive → Script`) che
automatizza tre cose:

| # | Obiettivo | Cosa fa lo script |
|---|-----------|-------------------|
| 1 | **Pilotare la spesa sulle keyword** | Mette in pausa le keyword che spendono senza portare conversioni e abbassa il bid dove si perde. |
| 2 | **Escludere il brand da Performance Max** | Crea/aggiorna una lista di parole chiave a corrispondenza inversa con i termini del brand e la applica a PMax (e a Search/Shopping non-brand). |
| 3 | **Biddare a profitto/margine** | Applica un margine ai valori conversione, calcola il profitto e alza i bid dove il profitto è più alto. |

Il file dello script è [`pilota-spesa-e-profitto.js`](./pilota-spesa-e-profitto.js).

---

## Installazione (5 minuti)

1. Accedi a **Google Ads** con l'account su cui vuoi far girare lo script.
2. Vai su **Strumenti → Azioni collettive → Script**.
3. Clicca **`+`** per creare un nuovo script.
4. Cancella il codice di esempio e **incolla tutto** il contenuto di
   `pilota-spesa-e-profitto.js`.
5. Clicca **Autorizza** e concedi i permessi richiesti.
6. **Configura** il blocco `CONFIG` in cima al file (vedi sotto). In particolare
   inserisci i **termini del brand** e la tua **email**.
7. Clicca **Anteprima**: lo script gira in modalità di sola lettura e ti manda un
   report via email/log **senza modificare nulla** (`DRY_RUN: true`).
8. Controlla il report. Quando sei soddisfatto, imposta `CONFIG.DRY_RUN = false`
   e clicca **Salva**.
9. Clicca **Pianifica** e scegli la frequenza consigliata: **una volta al giorno**
   (es. la mattina presto).

> ⚠️ **Sicurezza:** finché `DRY_RUN` è `true` lo script **non modifica nulla**,
> ti mostra solo cosa farebbe. Tienilo a `true` per il primo giro.

---

## Configurazione

Tutto si regola nel blocco `CONFIG` all'inizio del file.

### Generale
```js
DRY_RUN: true,                          // true = simula; false = applica davvero
EMAIL:   'indigit.marketing@gmail.com', // dove arriva il report
DATE_RANGE: 'LAST_30_DAYS',             // finestra di analisi
```

### Modulo 1 — Controllo spesa keyword
```js
spend: {
  enabled: true,
  minCostToEvaluate: 10,          // ignora keyword con spesa irrisoria
  pauseIfZeroConvAboveCost: 50,   // 0 conversioni + spesa oltre questa soglia => PAUSA
  minClicksForZeroConvPause: 15   // ...e almeno 15 click (ha avuto traffico)
}
```

### Modulo 2 — Esclusione brand su Performance Max
```js
brand: {
  enabled: true,
  terms: ['ilmiobrand', 'il mio brand'],   // <<< I TUOI TERMINI DI MARCA
  matchType: 'phrase',                      // 'phrase' | 'exact' | 'broad'
  negativeListName: 'BRAND - Esclusioni (script)',
  applyToPerformanceMax: true,              // applica a tutte le PMax
  applyToSearchShopping: true,              // applica anche a Search/Shopping
  brandCampaignNameContains: ['Brand', 'BRAND', 'Marca'] // campagne di marca da NON escludere
}
```

**Come funziona:** lo script crea una **lista di parole chiave escluse condivisa**
con i termini del brand e la applica alle campagne. Le campagne il cui nome
contiene una delle stringhe in `brandCampaignNameContains` **vengono saltate**,
così la tua campagna Search di marca continua a intercettare il brand mentre PMax
smette di cannibalizzarlo.

> **Limite tecnico di Google Ads Scripts:** l'API degli Script **non può**
> aggiungere parole chiave escluse direttamente dentro alcune campagne Performance
> Max. Quando succede, lo script **te lo segnala nel report** con l'elenco delle
> PMax da sistemare a mano (bastano 30 secondi per campagna: *Campagna PMax →
> Impostazioni → Parole chiave escluse a livello di campagna*).

### Modulo 3 — Bidding a profitto/margine
```js
profit: {
  enabled: true,
  defaultMargin: 0.35,                 // margine lordo medio (35%)
  marginByCampaignContains: {          // margine specifico per certe campagne
    // 'Outlet':  0.15,
    // 'Premium': 0.55
  },
  minConversions: 1,       // conversioni minime per considerare "profittevole"
  minCostToAct:   15,      // spesa minima per intervenire sui bid
  targetPoas:     1.6,     // POAS obiettivo: alza i bid se raggiunto
  minPoas:        1.0,     // sotto il break-even: abbassa i bid
  bidStepUpPct:   0.12,    // +12% CPC sui vincitori
  bidStepDownPct: 0.15,    // -15% CPC sui perdenti
  maxCpc:         3.00,    // tetto CPC
  minCpc:         0.05,    // pavimento CPC
  onlyManualCpc:  true     // tocca il CPC solo su campagne Manual CPC
}
```

**Il concetto chiave — POAS invece di ROAS.** Google Ads conosce solo il *valore*
conversione (fatturato), non il *margine*. Lo script applica il tuo margine e
ragiona sul **profitto**:

```
profitto lordo = valore_conversione × margine
POAS           = profitto lordo / spesa
profitto netto = profitto lordo − spesa
```

- **POAS ≥ `targetPoas`** (es. 1,6) → la keyword genera margine ampio → **alza il CPC**.
- **POAS < `minPoas`** (1,0 = pareggio) → la keyword perde soldi → **abbassa il CPC**.
- **0 conversioni** con spesa alta → **pausa** (Modulo 1).

Così i bid crescono dove arrivano le conversioni **più profittevoli**, non dove
arriva solo tanto fatturato a basso margine.

> Sulle campagne in **Smart Bidding** (Massimizza valore, tROAS, tCPA…) il CPC del
> singolo termine **non è modificabile**: lo script quindi **etichetta** le keyword
> come `PROFITTO (script)` / `PERDITA (script)` così puoi vederle e agire sulle
> strategie/target. Le keyword in perdita senza conversioni vengono comunque messe
> in pausa.

---

## Cosa ricevi nel report (email + log)

- Numero di keyword analizzate e, per ciascuna categoria, l'elenco con la
  motivazione: keyword **messe in pausa**, **CPC aumentato** (con vecchio→nuovo
  CPC), **CPC ridotto**, keyword **solo etichettate**.
- Stato dell'**esclusione brand**: lista creata/aggiornata, campagne a cui è stata
  applicata, campagne di marca saltate e — se necessario — le **PMax da sistemare
  a mano**.
- Eventuali avvisi/errori.

## Etichette create automaticamente

- `PROFITTO (script)` — keyword profittevoli
- `PERDITA (script)` — keyword in perdita
- `PAUSA-SCRIPT` — messe in pausa dallo script

Puoi filtrare per queste etichette nell'interfaccia di Google Ads per un controllo
rapido.

---

## Note tecniche

- Il valore conversione **non è esposto** dall'oggetto `Stats` degli Script,
  perciò lo script legge le metriche via **GAQL** (`AdsApp.report` su `keyword_view`).
- Il modulo keyword agisce **solo su campagne Search** (`advertising_channel_type =
  SEARCH`) e su keyword/ad group/campagne **attive**.
- Ogni modifica è protetta da `DRY_RUN` ed eseguita con `try/catch`: un errore su un
  modulo non blocca gli altri.
- Testato con una simulazione dell'API Google Ads su scenari reali (pausa,
  bid up/down, Smart Bidding, esclusione brand, PMax non associabile).

## Personalizzazioni frequenti

| Voglio… | Modifica |
|---------|----------|
| Analizzare gli ultimi 7 giorni | `DATE_RANGE: 'LAST_7_DAYS'` |
| Essere più aggressivo sulle pause | abbassa `pauseIfZeroConvAboveCost` |
| Alzare i bid solo sui top | alza `targetPoas` (es. 2.0) |
| Passi più cauti sui bid | riduci `bidStepUpPct` / `bidStepDownPct` |
| Solo report, nessuna azione sui bid | `profit.onlyManualCpc: true` + campagne in Smart Bidding |
| Non toccare Search/Shopping col brand | `brand.applyToSearchShopping: false` |
