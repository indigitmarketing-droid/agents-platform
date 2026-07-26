# Report Campagne — Luglio 2026

**Periodo:** 1–24 luglio 2026
**Fonti:** export Google Ads "Report sulle campagne" (1–24/07/2026) + note operative di Luigi (24/07/2026)
**Valuta:** EUR

---

## 1. Sintesi esecutiva

Luglio produce **€6.134,88 di valore di conversione a fronte di €9.969,35 di spesa**:
**ROAS 0,62**, cioè **−€3.834,47** netti sull'investimento pubblicitario, prima di
qualsiasi costo del venduto.

Il dato però nasconde due account che convivono e vanno letti separatamente:

| | Spesa | % spesa | Valore conv. | % valore | ROAS |
|---|---:|---:|---:|---:|---:|
| **Performance Max** | € 2.496,46 | 25,0% | € 5.356,20 | 87,3% | **2,15** |
| **Search** | € 7.472,89 | 75,0% | € 778,68 | 12,7% | **0,10** |
| **Totale account** | € 9.969,35 | 100% | € 6.134,88 | 100% | **0,62** |

**PMax è profittevole (+€2.859,74). Search perde €6.694,21.**
Il 75% del budget è allocato sul canale che genera il 12,7% del valore.

Questo è il singolo fatto più importante del mese: non serve trovare nuove leve,
serve **spostare il budget da Search a PMax**.

---

## 2. Verifica delle note operative sui dati

Le note del 24/07 sono in gran parte confermate, con due correzioni sostanziali.

| Affermazione | Verdetto | Dato |
|---|---|---|
| "ROAS in aumento" | ⚠️ **Parzialmente** | ROAS PMax 2,15 (ottimo). ROAS account 0,62 → l'account **non è in profitto** |
| "Mese migliore" | ✅ Plausibile | €6.134,88 di valore generato, ma senza dato di giugno non è verificabile |
| "PMax ha tasso di conversione più alto" | ❌ **Da correggere** | Tasso conv.: Search **16,90%** vs PMax **0,09%**. PMax vince sul **valore**, non sul tasso |
| "Validato App in modo automatico" | ⚠️ **Da verificare** | Tutte le campagne segnalano "problemi relativi ai dati sulle conversioni offline". Le azioni Purchase, Booking GMV, Niino Sign-up e Conversazione avviata sono a **0,00 ovunque** |
| "Ad agosto raddoppiamo" | ✅ Sostenibile | Ma solo su PMax: PMax spende il 31% del budget disponibile e perde il 18,20% di quota impressioni per limiti di budget |

### La correzione che conta

PMax non converte di più — **converte molto meglio**:

| | Conversioni "revenue" | Valore | Valore medio per conversione |
|---|---:|---:|---:|
| **PMax** | 21,18 | € 5.328,95 | **€ 251,60** |
| **Search** | 14,30 | € 317,86 | **€ 22,23** |

Ogni conversione a valore di PMax vale **11,3 volte** una di Search. La decisione
di puntare su PMax è corretta; la motivazione va riformulata, perché usare
"tasso di conversione" come criterio porterebbe a concludere l'opposto.

---

## 3. Il problema: il 92,7% delle conversioni non è fatturato

Scomposizione delle 497,29 conversioni dell'account per azione:

| Azione di conversione | Conversioni | % | Valore | Valore/conv. |
|---|---:|---:|---:|---:|
| Click-to-call | 259,63 | 52,2% | € 259,63 | € 1,00 |
| Calls from ads | 201,18 | 40,5% | € 201,18 | € 1,00 |
| **Niino Revenue** | 35,47 | 7,1% | **€ 5.646,82** | € 159,20 |
| Niino revenue via Call | 1,00 | 0,2% | € 27,25 | € 27,25 |
| Purchase / Booking GMV / Sign-up / Conversazione avviata | 0,00 | 0% | € 0,00 | — |
| **Totale** | **497,29** | 100% | **€ 6.134,88** | € 12,34 |

**460,81 conversioni su 497,29 (92,7%) sono chiamate valorizzate €1 ciascuna.**
Le conversioni che portano fatturato reale sono **36,47**, il 7,3% del totale.

Conseguenza diretta sui KPI: il "Costo/conv." di €20,05 riportato da Google Ads è
un numero fuorviante, perché mediato su conversioni-chiamata da €1. Il **CPA reale
sulle conversioni a fatturato è €273,36**, contro un valore medio per conversione
di €155,58. **Si perdono €117,78 su ogni vendita.**

### Dove finiscono le chiamate

Tutte le 460,81 chiamate arrivano da Search, che le paga **€16,22 l'una**.
Di queste, solo 14,30 diventano fatturato: **tasso chiamata → vendita del 3,10%**.

Perché la Search vada in pareggio, **ogni chiamata deve valere almeno €15,53 di
margine reale** (spesa Search meno fatturato già tracciato, diviso il numero di
chiamate). Questa è la verifica da fare prima di qualsiasi decisione: se il valore
offline di una chiamata è sotto quella soglia, la Search sta bruciando budget.

---

## 4. Analisi per campagna

> **Limite dell'export:** la colonna "Costo" è a zero su tutte le righe di campagna;
> la spesa compare solo nei totali. Le campagne sono quindi ordinabili per valore
> generato, **non per ROAS**. Serve un re-export con il costo per campagna per
> chiudere l'analisi.

| Campagna | Budget/gg | Valore conv. | % valore | Conv. | Valore/conv. |
|---|---:|---:|---:|---:|---:|
| **PMAX \| ITALIA \| AMBULANZA \| PURCHASE \| APP** | € 100 | **€ 4.522,08** | **79,7%** | 10,50 | **€ 430,67** |
| PMAX \| PIEMONTE \| AMBULANZA \| PURCHASE \| APP | € 80 | € 677,41 | 11,9% | 5,00 | € 135,48 |
| SEARCH \| AMBULANZA \| PURCHASE \| MILANO | € 120 | € 177,41 | 3,1% | 9,30 | € 19,08 |
| PMAX \| ITALIA \| AEREO \| PURCHASE | € 80 | € 101,85 | 1,8% | 4,00 | € 25,46 |
| SEARCH \| ANZIANI \| MILANO \| PURCHASE | € 120 | € 86,14 | 1,5% | 3,00 | € 28,71 |
| PMAX \| LOMBARDIA \| AMBULANZA \| PURCHASE \| APP | € 80 | € 54,87 | 1,0% | 2,68 | € 20,47 |
| SEARCH \| AMBULANZA \| PURCHASE \| ROMA | € 150 | € 54,31 | 1,0% | 2,00 | € 27,16 |
| **Totale** | **€ 730** | **€ 5.674,07** | 100% | 36,48 | € 155,54 |

### Tre letture

**1. Una sola campagna fa l'80% del risultato.**
`PMAX | ITALIA | AMBULANZA | PURCHASE | APP` genera €4.522,08 con un valore medio
per conversione di €430,67 — il triplo della seconda campagna — con un budget di
soli €100/giorno. È il modello da replicare e da finanziare per primo.

**2. La verticale AMBULANZA + APP è il prodotto che funziona.**
Le tre campagne PMax "AMBULANZA | PURCHASE | APP" (Italia, Piemonte, Lombardia)
valgono insieme €5.254,36, il **92,6%** del valore totale. AEREO e ANZIANI sono
marginali. La geografia conta: Italia €4.522, Piemonte €677, Lombardia €55.

**3. Le tre campagne Search hanno il budget più alto e il ritorno più basso.**
€390/giorno di budget (53,4% del totale) per €317,86 di fatturato in 24 giorni.
La Search di Roma ha il budget più alto dell'account (€150/gg) e il valore più
basso (€54,31).

---

## 5. Budget: l'allocazione è invertita

| | Budget/gg | Spesa reale/gg | Utilizzo | QI persa per budget |
|---|---:|---:|---:|---:|
| Performance Max | € 340 (46,6%) | € 104,02 | **31%** | **18,20%** |
| Search | € 390 (53,4%) | € 311,37 | **80%** | 0,89% |

Il quadro è netto:

- **PMax usa solo il 31% del budget che ha e perde comunque il 18,20% di quota
  impressioni per limiti di budget.** Le due cose insieme significano che la
  spesa è frenata a monte, non dal budget nominale: i gruppi di asset sono
  **limitati dalle norme** (segnalato su *tutte* le campagne PMax). Il canale che
  funziona sta girando a un terzo della sua capacità.
- **Search usa l'80% del budget** e ha una quota impressioni persa per budget
  quasi nulla: sta spendendo tutto quello che può, sul canale in perdita.

C'è inoltre il **60,43% di quota impressioni persa per ranking su PMax** e una
quota impressioni complessiva del 21,37%: spazio di crescita ampio, una volta
sbloccati gli asset.

---

## 6. Problemi tecnici bloccanti

Rilevati direttamente dai "Motivi dello stato" dell'export. Tutte le campagne
risultano **"Idoneo (limitato)"** — nessuna sta girando a piena capacità.

| # | Problema | Dove | Impatto |
|---|---|---|---|
| 1 | **Gruppi di asset limitati dalle norme** | Tutte le campagne PMax | Frena il canale che genera l'87% del valore. **Priorità massima** |
| 2 | **Problemi dati conversioni offline** | Tutte le campagne | Il ROAS reale è probabilmente sottostimato; mina anche la "validazione automatica App" |
| 3 | **Volume di ricerca limitato** | Tutte le campagne Search | Il budget Search non è spendibile in modo efficiente: keyword troppo strette |
| 4 | **4 azioni di conversione a zero** | Account | Purchase, Booking GMV, Niino Sign-up, Conversazione avviata: **0,00 ovunque** → tracciamento verosimilmente rotto |
| 5 | Apprendimento strategia di offerta | PMAX \| ITALIA \| AEREO | Dati non ancora stabilizzati |
| 6 | Punteggio di ottimizzazione basso | SEARCH \| ANZIANI \| MILANO: 52,31 · SEARCH \| MILANO: 61,64 · SEARCH \| ROMA: 72,56 | PMax sta a 83–87 |

Il punto 1 è la leva più grande del mese: **la campagna che porta l'80% del
fatturato sta girando con la maggior parte dei gruppi di asset bloccati dalle norme.**

---

## 7. L'obiettivo "20–25 al giorno": il dato lo chiarisce

Su 24 giorni:

| | Totale | Al giorno |
|---|---:|---:|
| Conversioni totali | 497,29 | **20,72** |
| di cui chiamate | 460,81 | 19,20 |
| **di cui vendite (revenue)** | **36,47** | **1,52** |
| Spesa | € 9.969,35 | € 415,39 |

L'obiettivo "20–25 al giorno" risulta **già raggiunto se misurato in conversioni
totali** (20,72/giorno) — ma **il 92,7% sono chiamate, non vendite**. Se il target
sono le vendite, il livello attuale è 1,52/giorno e serve un fattore **13,2×**.

Questa è la distinzione che decide tutta la strategia di agosto, e va fissata
prima di aprire i budget.

### Il vincolo, confermato dai numeri

> "Possiamo avere pure quei volumi se scateno le ads, ma la CPA aumenta."

I dati lo confermano in modo preciso: il volume di conversioni **è già lì**, ma è
volume di chiamate a €16,22 l'una che converte in vendita solo nel 3,10% dei casi.
Aumentare la spesa Search moltiplica le chiamate, non il fatturato. **Il volume non
è il problema: il problema è la qualità del volume.**

---

## 8. Piano Agosto 2026

### Priorità immediate (settimana 1)

| # | Azione | Perché | Impatto atteso |
|---|---|---|---|
| 1 | **Sbloccare i gruppi di asset PMax limitati dalle norme** | Il canale a ROAS 2,15 gira al 31% della capacità | Il più alto dell'intero piano |
| 2 | **Sistemare il tracciamento delle conversioni offline** | 4 azioni su 8 sono a zero; il ROAS è cieco | Rende affidabile ogni decisione successiva |
| 3 | **Definire il valore reale di una chiamata** | Soglia di pareggio Search: **€15,53/chiamata** | Decide se la Search va tagliata o tenuta |
| 4 | **Ridurre il budget Search del 50%** (€390 → €195/gg) | ROAS 0,10, −€6.694 nel mese | ~€2.900/mese liberati |
| 5 | **Spostare il budget liberato su PMax AMBULANZA + APP** | ROAS 2,15, valore/conv. €430 sulla campagna Italia | A ROAS costante: ~+€6.200 di valore |

### Scale (settimane 2–4)

6. **Raddoppiare il budget di `PMAX | ITALIA | AMBULANZA | PURCHASE | APP`** (€100 → €200/gg), verificando la tenuta del ROAS a ogni step.
7. **Replicare la struttura Italia sulle regionali** Piemonte e Lombardia, oggi molto sotto (€135 e €20 di valore/conv. contro €431).
8. **Valutare la sospensione di `SEARCH | AMBULANZA | PURCHASE | ROMA`** — budget più alto dell'account (€150/gg), valore più basso (€54,31).
9. **Mantenere la struttura test → validazione → scale** su ogni nuova campagna: è il presidio contro la crescita della CPA in fase di scale.

### Regole operative

- **Soglia di stop:** se durante lo scale il ROAS PMax scende sotto **1,5**, si congela l'aumento di budget e si torna in validazione, senza aspettare fine mese.
- **KPI di riferimento:** ROAS ≥ 2 e CPA sulle **conversioni a fatturato** (non sul dato Google Ads mediato sulle chiamate).
- **Niente scale su campagne non validate:** l'aumento di budget si applica solo a ciò che ha già dimostrato ROAS in target.

### Proiezione a budget invariato

Riallocando €195/giorno da Search a PMax e mantenendo il ROAS 2,15:

| | Oggi (24 gg) | Agosto riallocato (31 gg) |
|---|---:|---:|
| Spesa | € 9.969 | ≈ € 12.900 (invariata su base giornaliera) |
| Valore conv. | € 6.135 | **≈ € 18.000** |
| ROAS | 0,62 | **≈ 1,40** |

Stima a efficienza costante, quindi ottimistica: in fase di scale il ROAS
tipicamente scende. Serve però a dimensionare il potenziale — **la sola
riallocazione porta l'account dalla perdita al profitto, senza spendere un euro
in più.**

---

## 9. Dati ancora da recuperare

| Dato | Perché serve |
|---|---|
| **Costo per singola campagna** | L'export ha Costo = 0 su tutte le righe campagna: impossibile calcolare il ROAS per campagna |
| **Confronto giugno 2026** | Verificare "ROAS in aumento" e "mese migliore" |
| **Margine reale per prodotto** | Fissare la soglia di ROAS di profitto (qui assunta a 2) |
| **Valore offline di una chiamata** | Confrontarlo con la soglia di pareggio di €15,53 |
| **Unità di misura del target 20–25/giorno** | Chiamate (già raggiunto) o vendite (serve 13,2×) |

---

## Appendice A — Metriche complete per canale

| Metrica | Search | Performance Max | Account |
|---|---:|---:|---:|
| Costo | € 7.472,89 | € 2.496,46 | € 9.969,35 |
| Valore conv. | € 778,68 | € 5.356,20 | € 6.134,88 |
| **ROAS** | **0,10** | **2,15** | **0,62** |
| Impressioni | 35.893 | 1.137.535 | 1.173.428 |
| Clic | 2.811 | 24.409 | 27.220 |
| CTR | 7,83% | 2,15% | 2,32% |
| CPC medio | € 2,66 | € 0,10 | € 0,37 |
| Conversioni | 475,11 | 22,18 | 497,29 |
| Tasso conversione | 16,90% | 0,09% | 1,83% |
| Costo/conv. | € 15,73 | € 112,56 | € 20,05 |
| Quota impr. ricerca | 62,41% | 21,37% | 51,18% |
| QI persa (ranking) | 36,70% | 60,43% | 43,20% |
| QI persa (budget) | 0,89% | 18,20% | 5,63% |
| Coinvolgimento medio (GA4) | 70,44 s | 26,82 s | 42,89 s |

Nota: il tasso di conversione dell'account calcolato sui dati (1,83%) differisce
dal valore riportato nell'export (0,21%); in tabella è indicato il valore
calcolato, coerente con conversioni e clic.

## Appendice B — Note operative originali (24/07/2026)

> Questo mese però abbiamo di positivo molto — ROAS in aumento — mese migliore —
> validato App in modo automatico — e scoperto PMax che hanno un tasso di
> conversione più alto. Ora ad agosto raddoppiamo, se luglio è andato così.

> L'obiettivo è questo: per arrivare a 20-25 al giorno dobbiamo andare le ads in
> profitto. Perché possiamo avere pure quei volumi se scateno le ads, ma la CPA
> aumenta. E per fare questo dobbiamo seguire questa struttura test e validare
> campagna.
