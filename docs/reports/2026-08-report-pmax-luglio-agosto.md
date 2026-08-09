# Report Campagne Performance Max — Test Luglio / Agosto 2026

**Periodo:** 1 luglio – 9 agosto 2026 (40 giorni)
**Perimetro:** 4 campagne Performance Max in fase di test
**Fonte:** export Google Ads "Report sulle campagne" (1/07 – 9/08/2026)
**Confronto:** export precedente 1–24 luglio 2026
**Valuta:** EUR

---

## 1. Sintesi esecutiva

Il test PMax sui 40 giorni chiude con **€6.151,98 di valore di conversione a fronte
di €7.083,09 di spesa**: **ROAS 0,87**, cioè **−€931,11**.

Il dato aggregato però nasconde l'unica cosa che conta in questo report — il test
non è andato male in modo uniforme, **si è rotto a metà**:

| | Giorni | Spesa | Spesa/gg | Valore | Valore/gg | ROAS |
|---|---:|---:|---:|---:|---:|---:|
| **1–24 luglio** | 24 | € 2.496,46 | € 104,02 | € 5.356,20 | € 223,17 | **2,15** |
| **25 luglio – 9 agosto** | 16 | € 4.586,63 | € 286,66 | € 795,78 | € 49,74 | **0,17** |
| **Totale periodo** | 40 | € 7.083,09 | € 177,08 | € 6.151,98 | € 153,80 | **0,87** |

**Nei 16 giorni dello scale la spesa giornaliera è cresciuta del 176% e il valore
giornaliero è calato del 78%.** Il ROAS è passato da 2,15 a 0,17: un fattore 12,6
di peggioramento.

Il valore della conversione marginale è crollato da **€241,49 a €39,79**, mentre il
CPA marginale è salito a **€229,33**. Tradotto: **nell'ultima fase ogni conversione
acquistata è costata circa 5,8 volte quello che vale.**

Questa è la conclusione del test: **il modello PMax funziona, lo scale così com'è
stato eseguito no.** Non serve spegnere PMax — serve tornare al perimetro e alla
configurazione che a luglio davano ROAS 2,15, prima di riaprire i budget.

---

## 2. Verdetto del test: cosa ha funzionato e cosa no

Il test aveva 4 campagne. Solo una ha prodotto un risultato utilizzabile.

| Campagna | Budget/gg | Valore conv. | % valore | Conv. | Valore/conv. | Verdetto |
|---|---:|---:|---:|---:|---:|---|
| **PMAX \| ITALIA \| AMBULANZA \| PURCHASE \| APP** | € 130 | **€ 4.999,36** | **81,3%** | 17,83 | **€ 280,39** | ✅ **Validata** |
| PMAX \| PIEMONTE \| AMBULANZA \| PURCHASE \| APP | € 130 | € 767,28 | 12,5% | 7,67 | € 100,04 | ⚠️ Non validata |
| PMAX \| ITALIA \| AEREO \| PURCHASE | € 50 | € 280,73 | 4,6% | 12,01 | € 23,37 | ⚠️ Non validata |
| PMAX \| LOMBARDIA \| AMBULANZA \| PURCHASE \| APP | € 150 | € 104,62 | 1,7% | 4,67 | € 22,40 | ❌ **Da chiudere** |
| **Totale** | **€ 460** | **€ 6.151,98** | 100% | 42,18 | € 145,85 | |

Tre letture:

**1. Una campagna su quattro fa l'81,3% del valore.**
`PMAX | ITALIA | AMBULANZA | PURCHASE | APP` produce €280,39 di valore per
conversione: **2,8 volte** la seconda campagna e **12,5 volte** la peggiore. È
l'unica che merita budget.

**2. L'allocazione del budget è esattamente invertita rispetto al risultato.**
Lombardia ha **il budget più alto dell'account PMax (€150/gg)** e genera l'1,7% del
valore. Piemonte ha lo stesso budget di Italia (€130/gg) per il 15% del suo valore.
Il 60,9% del budget PMax (€280 su €460) è su campagne che valgono il 14,2%.

**3. La verticale è confermata, la geografia no.**
Le tre campagne AMBULANZA + APP valgono insieme €5.871,26, il **95,4%** del totale;
AEREO il 4,6%. Ma dentro AMBULANZA il gradiente è brutale: Italia €4.999, Piemonte
€767, Lombardia €105. **Le regionali non replicano il nazionale** — e non è un
problema di budget, perché ne hanno quanto o più di Italia.

### Il test in una riga

> Su €7.083 di spesa, la spesa massima compatibile con un ROAS 2 sarebbe stata
> **€3.076**. Ne è stata spesa **2,3 volte tanto**. Anche solo per andare in
> pareggio (ROAS 1) il tetto era €6.152.

---

## 3. Dove si è rotto: analisi dei due tempi

Confronto tra i primi 24 giorni e i 16 successivi, per campagna.

| Campagna | Valore/gg 1–24 lug | Valore/gg 25/7–9/8 | Variazione | Valore/conv. prima | Valore/conv. dopo |
|---|---:|---:|---:|---:|---:|
| **ITALIA \| AMBULANZA \| APP** | € 188,42 | € 29,83 | **−84,2%** | € 430,67 | **€ 65,11** |
| PIEMONTE \| AMBULANZA \| APP | € 28,23 | € 5,62 | **−80,1%** | € 135,48 | € 33,66 |
| LOMBARDIA \| AMBULANZA \| APP | € 2,29 | € 3,11 | +36,0% | € 20,47 | € 25,00 |
| ITALIA \| AEREO | € 4,24 | € 11,18 | +163,4% | € 25,46 | € 22,33 |

Il quadro è netto e va letto al contrario di come sembra:

- **Le due campagne che funzionavano sono quelle che sono crollate.** Italia
  Ambulanza perde l'84% del valore giornaliero, Piemonte l'80%.
- **Le due campagne "in crescita" crescono in volume, non in valore.** AEREO
  aggiunge 8,01 conversioni — più di ogni altra campagna nel periodo — ma da €22,33
  l'una. Lombardia idem a €25,00.
- **Il valore per conversione è collassato su tutta la linea, verso una banda
  €22–65.** Anche Italia Ambulanza, che a luglio valeva €430,67 a conversione, nella
  seconda fase scende a €65,11.

**La lettura è una sola: il sistema ha smesso di comprare conversioni di valore e ha
iniziato a comprare conversioni a basso valore, ovunque.** Non è un problema di una
singola campagna: è un problema di segnale di ottimizzazione.

---

## 4. La causa più probabile: la strategia di offerta

Confronto della configurazione tra i due export.

| Campagna | Budget lug → ora | Strategia lug → ora | Punteggio ott. lug → ora |
|---|---|---|---:|
| ITALIA \| AMBULANZA \| APP | € 100 → **€ 130** | CPA target → **CPA target** | 83,47 → **77,94** |
| PIEMONTE \| AMBULANZA \| APP | € 80 → **€ 130** | CPA target → **CPA target** | 86,89 → **77,55** |
| LOMBARDIA \| AMBULANZA \| APP | € 80 → **€ 150** | CPA target → **CPA target** | 86,89 → 86,89 |
| ITALIA \| AEREO | € 80 → **€ 50** | CPA target → **Max valore conv.** | 83,14 → **87,71** |

Due fatti si sommano:

**1. Le tre campagne AMBULANZA girano su CPA target su un obiettivo a valore.**
Il CPA target ottimizza il **numero** di conversioni a un costo bersaglio: al
sistema è indifferente se una conversione vale €430 o €22. Con budget aumentati del
30–88%, l'algoritmo ha fatto esattamente il suo lavoro — ha comprato più
conversioni, le più facili da ottenere, quindi le meno preziose. È coerente al 100%
con quello che mostrano i dati: **+20 conversioni nella seconda fase, a €39,79
medi di valore contro i €241,49 della prima.**

**2. I budget sono stati alzati prima di validare.** Il budget PMax passa da €340 a
€460/gg (+35%), con l'aumento più grande — da €80 a €150 — proprio sulla campagna
peggiore dell'account (Lombardia). Aumentare il budget su una strategia a CPA target
amplia la platea verso conversioni più economiche: il crollo del valore per
conversione era il risultato prevedibile.

> **Nota metodologica:** questa è la spiegazione più coerente con i dati
> disponibili, non una certezza. Va confermata guardando in piattaforma il valore
> del CPA target impostato e la data delle modifiche di budget. Se il CPA target è
> stato alzato insieme ai budget, la conferma è chiusa.

Il punteggio di ottimizzazione conferma il peggioramento dove è avvenuto: Italia
−5,5 punti, Piemonte −9,3. L'unica campagna migliorata (AEREO, +4,6) è anche l'unica
passata a **Massimizza il valore di conversione**.

---

## 5. Qualità del traffico: 3 milioni di impressioni, 42 conversioni

| Metrica | 1–24 luglio | 25/7 – 9/8 | Totale periodo |
|---|---:|---:|---:|
| Impressioni | 1.137.535 | 1.867.505 | **3.005.040** |
| Clic | 24.409 | 40.827 | **65.236** |
| CTR | 2,15% | 2,19% | 2,17% |
| CPC medio | € 0,10 | € 0,11 | € 0,11 |
| Conversioni | 22,18 | 20,00 | 42,18 |
| **Tasso di conversione** | **0,091%** | **0,049%** | **0,065%** |

**Il tasso di conversione si è dimezzato mentre il volume di traffico raddoppiava.**
Sono stati comprati 40.827 clic aggiuntivi per 20 conversioni: **1 conversione ogni
2.041 clic.**

Il confronto economico più diretto: nel periodo un clic PMax **rende €0,094 e costa
€0,109**. Ogni clic è in perdita prima ancora di guardare il resto.

Il dato di engagement lo conferma: **28,12 secondi medi per sessione su PMax contro
67,55 sulla Search** — meno della metà. A 65.000 clic e €0,11 di CPC, il canale sta
comprando inventory Display/Video a bassissima intensità di intento, non traffico
qualificato. Per un servizio ad alta urgenza come l'ambulanza, questo traffico non
ha valore.

**Quota impressioni:** PMax è al 24,03%, con il **67,48% perso per ranking** e
l'**8,49% per budget**. La leva non è il budget — è la qualità di asset e segnali.

---

## 6. Il contesto: l'account complessivo

Il test PMax non è isolato. Il quadro account nello stesso periodo:

| | Spesa | % spesa | Valore conv. | % valore | ROAS | Netto |
|---|---:|---:|---:|---:|---:|---:|
| **Performance Max** | € 7.083,09 | 37,2% | € 6.151,98 | 83,9% | **0,87** | −€ 931,11 |
| **Search** | € 11.933,33 | 62,8% | € 1.175,70 | 16,1% | **0,10** | −€ 10.757,63 |
| **Totale account** | € 19.016,42 | 100% | € 7.327,68 | 100% | **0,39** | **−€ 11.688,74** |

Rispetto al report di luglio (ROAS account 0,62), **l'account è peggiorato a 0,39**.
Dei €11.688,74 di perdita totale, **€7.854,27 sono maturati nei soli ultimi 16
giorni**: la perdita giornaliera è passata da €159,77 a €490,89.

**La Search resta il buco più grande in valore assoluto:** €11.933 di spesa per
€1.176 di valore. Continua a produrre conversioni-chiamata da €1 — 857,81 su 914,29
conversioni totali dell'account, il **93,8%** — a un costo di **€13,91 per
chiamata**, contro una soglia di pareggio di €13,54.

Sulle sole conversioni che generano fatturato (56,47 in 40 giorni), il **CPA reale
dell'account è €336,75 contro un valore medio di €114,57: −€222,18 per ogni
vendita** (a luglio era −€117,78).

Le azioni **Purchase, Booking GMV, Niino Sign-up e Conversazione avviata restano a
0,00 ovunque**: quattro azioni di conversione su otto continuano a non registrare
nulla.

---

## 7. Cosa è migliorato

Non tutto è peggiorato, e va detto:

| # | Miglioramento | Evidenza |
|---|---|---|
| 1 | **Problemi conversioni offline risolti** | A luglio tutte le PMax segnalavano "i problemi relativi ai dati sulle conversioni offline influiscono sul rendimento". Nell'export attuale **non compare più su nessuna campagna** |
| 2 | **Fine apprendimento strategia di offerta** | AEREO non è più in fase di apprendimento |
| 3 | **Concentrazione confermata** | La verticale AMBULANZA + APP tiene il 95,4% del valore: la scelta di prodotto è corretta |

Restano invece aperti, e peggiorati:

| # | Problema | Dove |
|---|---|---|
| 1 | **Gruppi di asset limitati dalle norme** | **Tutte e 4 le campagne**, come a luglio. Nessun progresso in 40 giorni |
| 2 | **Efficacia dell'annuncio scadente** | **Nuovo**: Piemonte e Lombardia. Sono le due regionali che non replicano il nazionale |
| 3 | **Limitazione da budget** | AEREO (€50/gg) è l'unica limitata dal budget — ed è quella con il valore/conv. più basso |
| 4 | **4 azioni di conversione a zero** | Account, invariato da luglio |
| 5 | **Costo per campagna assente nell'export** | La colonna "Costo" è a 0 su tutte le righe campagna, come nell'export precedente |

Il punto 1 è quello che pesa di più: **la campagna che genera l'81% del valore gira
da 40 giorni con la maggior parte dei gruppi di asset bloccati dalle norme.** È la
prima cosa da sbloccare, e non è ancora stata toccata.

---

## 8. Piano operativo

### Immediato (entro 48 ore) — fermare l'emorragia

| # | Azione | Dato che la giustifica |
|---|---|---|
| 1 | **Mettere in pausa `PMAX \| LOMBARDIA \| AMBULANZA \| PURCHASE \| APP`** | Budget più alto dell'account PMax (€150/gg) per l'1,7% del valore ed efficacia annuncio scadente |
| 2 | **Riportare i budget ai livelli pre-scale** | Italia €130 → €100, Piemonte €130 → €50. A €104/gg il canale faceva ROAS 2,15; a €287/gg fa 0,17 |
| 3 | **Passare `ITALIA \| AMBULANZA` da CPA target a "Massimizza il valore di conversione"** | Il CPA target su un obiettivo a valore è l'errore strutturale del test: ha comprato volume a €39,79/conv. |
| 4 | **Non toccare AEREO** | È limitata dal budget ma vale €23,37 a conversione: aumentarne il budget replicherebbe l'errore |

Impatto atteso: **PMax da €287/gg a circa €150/gg**, con il budget concentrato sulla
sola campagna validata. Non si tratta di ridurre l'investimento, ma di rimetterlo
dove produceva.

### Settimana 1–2 — sbloccare la leva vera

5. **Risolvere i gruppi di asset limitati dalle norme su tutte e 4 le campagne.**
   È l'unico problema segnalato da 40 giorni consecutivi e mai risolto, e riguarda la
   campagna che porta l'81% del valore.
6. **Rifare gli asset di Piemonte** (efficacia annuncio scadente): titoli,
   descrizioni e immagini della campagna Italia, adattati alla geografia. Non
   riattivare Lombardia finché Piemonte non torna sopra €100 di valore/conv.
7. **Verificare in piattaforma il valore del CPA target impostato e lo storico delle
   modifiche.** Se il CPA target è stato alzato con i budget, è la conferma della
   diagnosi del §4.
8. **Escludere le placement Display/Video a basso intento**, o quantomeno misurarle:
   65.236 clic a 0,065% di conversione e 28 secondi di sessione non sono traffico
   utile.

### Settimana 3–4 — riprendere lo scale, ma con una regola

9. **Riaprire il budget di `ITALIA | AMBULANZA` solo a step del +20%**, e solo dopo
   due settimane consecutive con ROAS ≥ 2 e valore/conversione ≥ €200.
10. **Riportare la Search sotto controllo:** €11.933 per €1.176 di valore non è
    sostenibile. Prima decisione da prendere: quanto vale davvero una chiamata
    offline, contro la soglia di pareggio di **€13,54**.

### Regole operative da fissare adesso

- **Il KPI di validazione è il valore per conversione, non il numero di
  conversioni.** Tutto il crollo di questo test è invisibile se si guarda il conteggio
  conversioni (+20 nella seconda fase, il periodo peggiore).
- **Nessun aumento di budget su campagne a CPA target con obiettivo a valore.**
- **Soglia di stop automatica:** se il valore/conversione settimanale scende sotto
  **€150**, il budget si congela lo stesso giorno — senza aspettare il consuntivo
  mensile. Con questa regola il crollo sarebbe stato intercettato dopo 5–7 giorni
  invece che dopo 16.
- **Una campagna nuova parte a €30–50/gg** e non viene scalata prima di 20
  conversioni a valore.

### Proiezione della sola riallocazione

Concentrando €150/gg sulla campagna validata e mantenendo il suo valore/conversione
storico:

| | Ultimi 16 gg (reale) | Scenario riallocato (30 gg) |
|---|---:|---:|
| Spesa PMax | € 4.586,63 (€ 286,66/gg) | ≈ € 4.500 (€ 150/gg) |
| Valore conv. | € 795,78 | **≈ € 9.000** |
| ROAS | 0,17 | **≈ 2,0** |

Stima a efficienza costante e quindi ottimistica: presuppone il ritorno al valore per
conversione di luglio, che dipende dai punti 3, 5 e 6 del piano. Serve a dimensionare
l'ordine di grandezza — **il recupero del ROAS non richiede più budget, richiede meno
budget messo meglio.**

---

## 9. Dati ancora da recuperare

| Dato | Perché serve |
|---|---|
| **Costo per singola campagna** | Ancora a 0 nell'export: il ROAS per campagna resta stimabile solo per quota di budget. È il dato che manca per decidere con certezza su Piemonte e AEREO |
| **Valore e storico del CPA target** | Chiude la diagnosi del §4 |
| **Date esatte delle modifiche di budget** | Per collocare con precisione il punto di rottura dentro i 16 giorni |
| **Ripartizione placement PMax** (Search/Shopping/Display/Video/Discovery) | Per capire dove finiscono i 3 milioni di impressioni |
| **Valore offline reale di una chiamata** | Confronto con la soglia di pareggio Search di €13,54 |
| **Motivo dello zero su Purchase, Booking GMV, Sign-up, Conversazione avviata** | 4 azioni su 8 non registrano nulla da almeno 40 giorni |

---

## Appendice A — Metriche complete per canale (1/07 – 9/08/2026)

| Metrica | Performance Max | Search | Account |
|---|---:|---:|---:|
| Costo | € 7.083,09 | € 11.933,33 | € 19.016,42 |
| Valore conv. | € 6.151,98 | € 1.175,70 | € 7.327,68 |
| **ROAS** | **0,87** | **0,10** | **0,39** |
| Netto | −€ 931,11 | −€ 10.757,63 | −€ 11.688,74 |
| Impressioni | 3.005.040 | 61.018 | 3.066.058 |
| Clic | 65.236 | 4.973 | 70.209 |
| CTR | 2,17% | 8,15% | 2,29% |
| CPC medio | € 0,11 | € 2,40 | € 0,27 |
| Conversioni | 42,18 | 872,11 | 914,29 |
| Tasso conversione | 0,065% | 17,54% | 1,30% |
| Costo/conv. | € 167,93 | € 13,68 | € 20,80 |
| Valore/conv. | € 145,85 | € 1,35 | € 8,01 |
| Quota impr. ricerca | 24,03% | 63,12% | 43,38% |
| QI persa (ranking) | 67,48% | 36,34% | 52,06% |
| QI persa (budget) | 8,49% | 0,54% | 4,56% |
| Coinvolgimento medio (GA4) | 28,12 s | 67,55 s | 36,49 s |

Nota: i tassi di conversione in tabella sono ricalcolati su conversioni/clic e
differiscono dai valori riportati nell'export (0,01% PMax, 0,16% account), che
risultano incoerenti con le colonne di origine.

## Appendice B — Conversioni per azione, account (1/07 – 9/08/2026)

| Azione di conversione | Conversioni | % | Valore | Valore/conv. |
|---|---:|---:|---:|---:|
| Click-to-call | 531,30 | 58,1% | € 531,33 | € 1,00 |
| Calls from ads | 326,51 | 35,7% | € 326,51 | € 1,00 |
| **Niino Revenue** | 53,47 | 5,8% | **€ 6.363,40** | € 119,01 |
| Niino revenue via Call | 3,00 | 0,3% | € 106,45 | € 35,48 |
| Purchase | 0,00 | 0% | € 0,00 | — |
| Booking GMV | 0,00 | 0% | € 0,00 | — |
| Niino Sign-up | 0,00 | 0% | € 0,00 | — |
| Conversazione avviata | 0,00 | 0% | € 0,00 | — |
| **Totale** | **914,29** | 100% | **€ 7.327,68** | € 8,01 |

Di cui su Performance Max: Niino Revenue 39,18 conv. / €6.045,53 · Niino revenue via
Call 3,00 conv. / €106,45. **Tutte le 857,81 conversioni-chiamata da €1 arrivano
dalla Search.**

## Appendice C — Stato delle campagne PMax

Tutte e 4 le campagne risultano **"Idoneo (limitato)"**: nessuna gira a piena
capacità.

| Campagna | Motivi dello stato |
|---|---|
| ITALIA \| AEREO \| PURCHASE | limitato dal budget; la maggior parte dei gruppi di asset è limitata dalle norme |
| ITALIA \| AMBULANZA \| PURCHASE \| APP | la maggior parte dei gruppi di asset è limitata dalle norme |
| PIEMONTE \| AMBULANZA \| PURCHASE \| APP | la maggior parte dei gruppi di asset è limitata dalle norme; l'efficacia dell'annuncio è scadente |
| LOMBARDIA \| AMBULANZA \| PURCHASE \| APP | la maggior parte dei gruppi di asset è limitata dalle norme; l'efficacia dell'annuncio è scadente |

## Appendice D — Metodo di calcolo del confronto tra i due periodi

I valori della fase 25/7 – 9/8 non sono presenti nell'export: sono ottenuti per
differenza tra l'export 1/07–9/08 e l'export 1/07–24/07 già analizzato nel report di
luglio. Il metodo è valido per costi, valori, conversioni, clic e impressioni, che
sono metriche cumulative. Non è applicabile a percentuali e medie (CTR, quota
impressioni, punteggio di ottimizzazione), che nel report sono citate solo come
valori di periodo.

I ROAS per singola campagna sono stimati ripartendo la spesa PMax in proporzione al
budget giornaliero, perché la colonna "Costo" è a zero su tutte le righe campagna:
sono indicativi e non sostituiscono un re-export con il costo per campagna.
