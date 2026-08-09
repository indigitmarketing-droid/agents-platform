# Report Campagne Search — Luglio / Agosto 2026

**Periodo:** 1 luglio – 9 agosto 2026 (40 giorni)
**Perimetro:** 14 campagne sulla rete di ricerca, divise in due gruppi con due
sistemi di misurazione diversi
**Fonte:** export Google Ads "Report sulle campagne" (1/07 – 9/08/2026)
**Valuta:** EUR

---

## 1. Sintesi esecutiva

La Search assorbe **€11.951,31, il 62,8% della spesa dell'account**, e produce
**€1.177,70 di valore, il 16,1% del totale**: **ROAS 0,10**, cioè **−€10.773,61**.

Ma il ROAS della Search non è un dato reale, ed è il punto di partenza di tutto il
report. Dei €1.177,70 di "valore":

| Componente | Valore | Cos'è davvero |
|---|---:|---|
| **Fatturato tracciato** (Niino Revenue) | € 317,86 | Ricavo vero, dalle 3 campagne Purchase |
| **Chiamate valorizzate €1** | € 859,81 | Un conteggio, non un ricavo |
| **Totale "valore conv."** | **€ 1.177,70** | Un numero che somma euro e pezzi |

**Su €11.951,31 di spesa, il fatturato realmente tracciato è €317,86: il 2,66%.**
Tutto il resto sono 859,81 chiamate, contate a €1 l'una per convenzione.

Questo significa che **ROAS, valore/costo e costo/conversione della Search non sono
interpretabili così come sono**: mescolano due gruppi di campagne che misurano cose
diverse. Il report li tiene separati dall'inizio alla fine.

| Gruppo | Campagne | Budget/gg | Cosa misura | Output 40 gg |
|---|---:|---:|---|---|
| **Search Purchase** | 3 | € 420 | Valore + CPA | € 317,86 · 14,30 conv. |
| **Search Chiamata** | 11 | € 1.520 | Solo conversioni + CPA | 830,11 chiamate |
| **Totale** | **14** | **€ 1.940** | | |

Le tre conclusioni del periodo:

1. **Il gruppo Purchase non regge economicamente.** €317,86 di fatturato in 40
   giorni — €7,95 al giorno — a fronte di €420/giorno di budget nominale.
2. **Il gruppo Chiamata è tutto il volume dell'account** (830 conversioni su 844) ma
   **non è valutabile finché non si assegna un valore reale a una chiamata.** La
   soglia di pareggio è **€13,53 per chiamata**.
3. **Il vero problema è strutturale: 14 campagne per €299/giorno di spesa reale.**
   13 su 14 sono limitate dal volume di ricerca. L'account è frammentato oltre la
   soglia in cui gli algoritmi di offerta possono funzionare.

---

## 2. Il problema di misurazione: due sistemi che non si possono sommare

Le due famiglie di campagne rispondono a domande diverse:

- Le **Purchase** dichiarano un valore economico per conversione. Sono valutabili con
  il ROAS.
- Le **Chiamata** dichiarano solo quante conversioni e a che costo. Il "valore" di €1
  che compare nell'export è una convenzione di conteggio, **non un ricavo**.

Sommarle produce tre errori concreti, tutti presenti nei KPI attuali dell'account:

| KPI riportato | Valore | Perché è fuorviante |
|---|---:|---|
| ROAS Search | 0,10 | Il 73% del "valore" al numeratore non è fatturato |
| Costo/conv. Search | € 13,67 | Media tra chiamate a €1 e vendite a €22 |
| Tasso conv. Search | 17,55% | Gonfiato dalle conversioni-chiamata, che scattano su un clic |

**Il costo/conversione di €13,67 è il numero più pericoloso del report**, perché
sembra buono. In realtà descrive quasi esclusivamente il costo di una chiamata: sul
fatturato vero il costo per conversione è tra **€42 e €181** (§3), contro un valore
medio di €22,23.

### Il sospetto di doppio conteggio

Il gruppo Chiamata registra **due azioni distinte** sulla stessa telefonata:
**Click-to-call** (513,16 conv.) e **Calls from ads** (326,51 conv.). Sono azioni
diverse — il clic sul pulsante e la chiamata effettivamente tracciata — ma **la
stessa telefonata può generarle entrambe**.

Il rapporto tra le due varia in modo che non è spiegabile con la sola performance:

| Campagna | Click-to-call | Calls from ads | Rapporto CFA/CTC |
|---|---:|---:|---:|
| AMBULANZA \| CHIAMATA \| BARI | 27,67 | 2,50 | **9%** |
| AMBULANZA \| CHIAMATA \| AGRIGENTO | 6,00 | 1,00 | 17% |
| AMBULANZA \| CHIAMATA \| ROMA | 89,46 | 19,99 | 22% |
| MILANO \| DIMISSIONI \| CHIAMATA | 71,83 | 30,00 | 42% |
| AMBULANZA \| CHIAMATA \| BOLOGNA | 44,99 | 20,00 | 44% |
| CHIAMATA \| LUNGA PERCORRENZA \| SARDEGNA | 52,50 | 28,00 | 53% |
| AMBULANZA \| CHIAMATA \| PUGLIA | 88,33 | 69,47 | 79% |
| AMBULANZA \| CHIAMATA \| PALERMO | 19,00 | 18,00 | 95% |
| AMBULANZA \| CHIAMATA \| MILANO | 71,91 | 77,49 | 108% |
| AMBULANZA \| CHIAMATA \| TORINO | 33,47 | 39,00 | **117%** |
| AMBULANZA \| CHIAMATA \| VARESE 2 | 8,00 | 11,50 | **144%** |

**Da 9% a 144%: uno scarto di 16 volte tra campagne dello stesso account, dello
stesso servizio e con lo stesso setup.** O la configurazione di tracciamento
differisce tra campagne, o le due azioni si sovrappongono in modo variabile. In
entrambi i casi **il conteggio delle chiamate non è confrontabile tra campagne**, e
il KPI su cui si sta ottimizzando l'intero gruppo è instabile.

Questa è la prima cosa da verificare in piattaforma, prima di qualsiasi decisione di
budget: se c'è sovrapposizione, il numero reale di chiamate è **inferiore a 859,81**
e il costo per chiamata è **superiore a €13,90**.

---

## 3. Gruppo Purchase: 3 campagne, €317,86 in 40 giorni

Sono le uniche campagne Search che dichiarano un valore economico.

| Campagna | Budget/gg | Valore conv. | Conv. | Valore/conv. | Punt. ott. |
|---|---:|---:|---:|---:|---:|
| SEARCH \| AMBULANZA \| PURCHASE \| MILANO | € 120 | € 177,41 | 9,30 | € 19,08 | 64,54 |
| SEARCH \| ANZIANI \| MILANO \| PURCHASE | € 150 | € 86,14 | 3,00 | € 28,71 | 60,39 |
| SEARCH \| AMBULANZA \| PURCHASE \| ROMA | € 150 | € 54,31 | 2,00 | € 27,16 | 64,54 |
| **Totale** | **€ 420** | **€ 317,86** | **14,30** | **€ 22,23** | |

### Il costo non c'è nell'export, ma la conclusione non cambia

La colonna "Costo" è a zero su tutte le righe di campagna, come nei due export
precedenti. Il costo del gruppo si può però delimitare tra due ipotesi opposte:

| Ipotesi | Costo stimato | CPA reale | ROAS |
|---|---:|---:|---:|
| **A** — spesa proporzionale al budget (21,6% della Search) | € 2.587,40 | € 180,94 | **0,12** |
| **B** — le chiamate costano il CPA medio Search (€13,67), il resto è Purchase | € 603,71 | € 42,22 | **0,53** |

**Le due ipotesi sono agli estremi opposti e portano alla stessa decisione: il gruppo
Purchase è sotto il pareggio in entrambi i casi.** Il costo reale è da qualche parte
in mezzo; l'incertezza non cambia il verdetto, quindi non vale la pena aspettare il
re-export per agire.

Per andare in pareggio (ROAS 1) queste tre campagne potevano spendere al massimo
**€317,86 in 40 giorni**, cioè **€7,95 al giorno in tre**. Hanno €420/giorno di
budget disponibile.

### Il confronto che pesa di più

Le campagne Purchase della Search e la migliore campagna PMax registrano **la stessa
azione di conversione** (Niino Revenue):

| | Valore per conversione |
|---|---:|
| PMAX \| ITALIA \| AMBULANZA \| PURCHASE \| APP | **€ 280,39** |
| Gruppo Search Purchase | **€ 22,23** |

**Una conversione Search vale 12,6 volte meno di una conversione PMax, a parità di
azione tracciata.** Non è una differenza di efficienza pubblicitaria: è una
differenza di cosa viene venduto. La Search intercetta richieste di servizi molto più
piccoli, oppure l'attribuzione di valore sui due canali non è omogenea. **Va chiarito
quale delle due, perché nel primo caso il canale è strutturalmente inadatto
all'obiettivo Purchase e va riconvertito, nel secondo il dato è semplicemente
sbagliato.**

---

## 4. Gruppo Chiamata: 11 campagne, 830 conversioni

Qui si misura solo volume e costo per conversione. Non essendoci un costo per
campagna nell'export, l'unico indicatore di efficienza relativa disponibile è
**quante conversioni ogni campagna produce per €100 di budget giornaliero**.

| Campagna | Budget/gg | Conv. | Conv./gg | Conv. per €100 budget | Punt. ott. |
|---|---:|---:|---:|---:|---:|
| AMBULANZA \| CHIAMATA \| ROMA | € 120 | 109,45 | 2,74 | **91,2** | 57,77 |
| AMBULANZA \| CHIAMATA \| PUGLIA | € 200 | **157,80** | 3,95 | **78,9** | 58,56 |
| AMBULANZA \| CHIAMATA \| PALERMO | € 50 | 37,00 | 0,93 | 74,0 | 61,64 |
| AMBULANZA \| CHIAMATA \| TORINO | € 100 | 72,47 | 1,81 | 72,5 | 64,54 |
| AMBULANZA \| CHIAMATA \| BOLOGNA | € 100 | 64,99 | 1,62 | 65,0 | 61,64 |
| CHIAMATA \| LUNGA PERCORRENZA \| SARDEGNA | € 130 | 80,50 | 2,01 | 61,9 | 70,63 |
| AMBULANZA \| CHIAMATA \| MILANO | € 270 | 149,40 | 3,73 | 55,3 | 58,56 |
| MILANO \| DIMISSIONI \| CHIAMATA | **€ 280** | 101,83 | 2,55 | 36,4 | 57,09 |
| AMBULANZA \| CHIAMATA \| BARI | € 100 | 30,17 | 0,75 | 30,2 | 61,64 |
| AMBULANZA \| CHIAMATA \| VARESE 2 | € 120 | 19,50 | 0,49 | **16,3** | 61,64 |
| AMBULANZA \| CHIAMATA \| AGRIGENTO | € 50 | 7,00 | 0,17 | **14,0** | 53,64 |
| **Totale** | **€ 1.520** | **830,11** | **20,75** | 54,6 | |

Tre osservazioni:

**1. Il budget più alto del gruppo è sulla campagna meno efficiente della fascia
alta.** `MILANO | DIMISSIONI | CHIAMATA` ha €280/giorno — il budget più alto di tutta
la Search — e produce 36,4 conversioni per €100 di budget, contro le 91,2 di Roma con
meno della metà del budget.

**2. Tre campagne sono sotto la soglia di rilevanza statistica.** Agrigento (7,00
conversioni in 40 giorni, 0,17 al giorno), Varese 2 (19,50) e Bari (30,17) valgono
insieme il 6,8% delle conversioni del gruppo e occupano €270/giorno di budget. A
questi volumi nessuna strategia automatica può ottimizzare.

**3. Agrigento è l'unica campagna dell'account senza limitazioni — e la peggiore.**
È l'unica con stato **"Idoneo"** pulito e l'unica su **Massimizza conversioni**
invece che su CPA target. Non è limitata perché non ha un vincolo di CPA da
rispettare: produce 7 conversioni in 40 giorni con il punteggio di ottimizzazione più
basso dell'account (53,64). **Lo stato "Idoneo" qui non è un segnale positivo.**

### La soglia che decide tutto

Attribuendo alla Search l'intero costo al netto del fatturato Purchase:

> **Ogni chiamata deve valere almeno €13,53 di margine reale perché la Search vada in
> pareggio.** Se la stessa telefonata è contata due volte (§2), la soglia sale in
> proporzione.

Questa è l'unica domanda che rende valutabile il 98% delle conversioni dell'account.
Finché non ha risposta, **non esiste un criterio per decidere se il gruppo Chiamata
vada scalato o chiuso** — e nessuna ottimizzazione di dettaglio ha senso.

---

## 5. Il problema strutturale: 14 campagne per €299 al giorno

È il dato che spiega i punteggi di ottimizzazione bassi e la lentezza di tutto
l'account.

| | Valore |
|---|---:|
| Budget nominale Search | **€ 1.940/giorno** |
| Spesa reale Search | **€ 298,78/giorno** |
| **Utilizzo del budget** | **15,4%** |
| Quota impressioni persa per budget | **0,54%** |
| Campagne con "volume di ricerca limitato" | **13 su 14** |
| Clic per campagna al giorno | **8,9** |
| Impressioni per campagna al giorno | **109** |

Il quadro è inequivocabile: **il budget non è mai stato il vincolo di questa Search.**
Con lo 0,54% di quota impressioni persa per budget, il denaro disponibile non viene
speso perché **non c'è abbastanza domanda da intercettare** con la struttura attuale.

Le conseguenze pratiche:

- **Le strategie automatiche non hanno dati per funzionare.** Una campagna con 8,9
  clic e 1,5 conversioni al giorno non fornisce a un CPA target il volume minimo per
  uscire dall'apprendimento. Il punteggio di ottimizzazione medio della Search è
  **61,2** (min 53,64 – max 70,63), contro **77–88 su PMax**.
- **Il budget nominale è un rischio, non una risorsa.** €1.940/giorno di budget
  configurato contro €299 spesi non produce risparmio se ridotto — la spesa è già
  limitata dal volume — ma **espone l'account a una spesa 6,5 volte superiore** se la
  domanda dovesse salire (picco stagionale, allargamento keyword, cambio di
  strategia). Va allineato per controllo del rischio.
- **La frammentazione geografica non è giustificata dai volumi.** 11 campagne
  chiamata su 11 geografie diverse, quando l'intero gruppo genera 20,75 conversioni
  al giorno.

### Il secondo vincolo: la strategia di offerta

Quattro campagne riportano **"limitata dal tipo di strategia di offerta"**: Puglia,
Milano, Roma e Milano Dimissioni. Sono **le quattro maggiori produttrici di
conversioni del gruppo**:

| | Valore |
|---|---:|
| Campagne limitate dalla strategia di offerta | 4 su 14 |
| Conversioni prodotte | **518,48** (62,5% del gruppo Chiamata) |
| Budget occupato | € 870/giorno (44,8% della Search) |

**Il 62,5% delle chiamate arriva da campagne che Google segnala come frenate dal CPA
target**, non dal budget. È qui che si trova il margine di crescita del volume, non
negli aumenti di budget — che sull'85% inutilizzato non produrrebbero alcun effetto.

---

## 6. Il quadro d'insieme dell'account

| | Spesa | % spesa | Valore conv. | % valore | ROAS | Netto |
|---|---:|---:|---:|---:|---:|---:|
| **Search** | € 11.951,31 | 62,8% | € 1.177,70 | 16,1% | **0,10** | −€ 10.773,61 |
| **Performance Max** | € 7.091,15 | 37,2% | € 6.151,98 | 83,9% | **0,87** | −€ 939,17 |
| **Totale account** | € 19.042,46 | 100% | € 7.329,69 | 100% | **0,38** | **−€ 11.712,77** |

**La Search assorbe il 62,8% della spesa e genera il 2,66% di fatturato tracciato
rispetto a quanto costa.** Anche assegnando alle 859,81 chiamate un valore generoso,
il canale resta lontano dal pareggio: servirebbero **€13,53 di margine per chiamata**
solo per non perdere denaro.

Il confronto con l'analisi PMax dello stesso periodo chiude il cerchio: PMax perde
€939,17 su €7.091,15 (ROAS 0,87), la Search perde €10.773,61 su €11.951,31. **Il 92%
della perdita dell'account viene dalla Search.**

---

## 7. Piano operativo

### Priorità 0 — prima di ogni decisione di budget (questa settimana)

| # | Azione | Perché |
|---|---|---|
| 1 | **Quantificare il margine reale di una chiamata** | Soglia di pareggio: **€13,53**. È l'unico numero che rende valutabile il 98% delle conversioni dell'account |
| 2 | **Verificare la sovrapposizione tra Click-to-call e Calls from ads** | Rapporto tra le due azioni da 9% a 144% tra campagne: il conteggio chiamate non è confrontabile |
| 3 | **Chiarire perché una conversione Purchase vale €22 su Search e €280 su PMax** | Stessa azione tracciata: o i canali vendono cose diverse, o l'attribuzione di valore è sbagliata |

Nessuna delle tre richiede budget. Tutte e tre condizionano ogni decisione successiva.

### Priorità 1 — struttura (settimane 1–2)

| # | Azione | Dato che la giustifica |
|---|---|---|
| 4 | **Consolidare le 11 campagne Chiamata in 3–4 macro-campagne** (per macro-area o per servizio) | 8,9 clic e 1,5 conversioni al giorno per campagna: sotto la soglia di funzionamento delle strategie automatiche |
| 5 | **Chiudere `AMBULANZA \| CHIAMATA \| AGRIGENTO`** | 7,00 conversioni in 40 giorni, 14,0 per €100 di budget, punteggio 53,64: il peggiore su ogni metrica |
| 6 | **Assorbire Varese 2 e Bari nel consolidamento** | Insieme ad Agrigento: 6,8% delle conversioni per €270/giorno di budget |
| 7 | **Allineare i budget alla spesa reale**: Search da €1.940 a ~€450/giorno | Utilizzo al 15,4% con QI persa per budget allo 0,54%. Non è un risparmio — è controllo del rischio |
| 8 | **Rivedere il CPA target sulle 4 campagne limitate dalla strategia di offerta** | Producono il 62,5% delle chiamate e sono frenate dal bid, non dal budget: è l'unica leva di volume reale |

### Priorità 2 — gruppo Purchase (settimane 2–3)

| # | Azione | Dato che la giustifica |
|---|---|---|
| 9 | **Sospendere `SEARCH \| AMBULANZA \| PURCHASE \| ROMA`** | €54,31 di valore in 40 giorni (€1,36/giorno) con €150/giorno di budget |
| 10 | **Consolidare Milano Purchase e Anziani Milano in una sola campagna a €100/giorno** | Insieme fanno €263,55 in 40 giorni; separate non raggiungono il volume per ottimizzare |
| 11 | **Decidere se la Search debba avere campagne Purchase** | Tetto di spesa per il pareggio: €317,86 in 40 giorni sull'intero gruppo. Con il valore/conv. attuale di €22,23 il canale non regge l'obiettivo |

### Regole operative

- **Non si confrontano campagne Purchase e campagne Chiamata con lo stesso KPI.** Le
  prime si giudicano a ROAS, le seconde a costo per chiamata **contro il margine reale
  di una chiamata**, non contro €1.
- **Il costo/conversione della Search (€13,67) non va usato come KPI di account:**
  descrive il costo di una chiamata, non quello di una vendita.
- **Nessuna campagna nuova sotto le 30 conversioni/mese attese.** Sotto quella soglia
  si aggiunge frammentazione, non copertura.
- **Il budget di una campagna limitata dal volume di ricerca non va aumentato:** non
  produce spesa aggiuntiva. La leva è keyword, bid strategy o consolidamento.

### Cosa aspettarsi

Il consolidamento **non riduce la spesa** — la spesa è già limitata dalla domanda, non
dal budget. Produce tre effetti diversi:

1. **Volume di dati per campagna 3–4 volte superiore**, quindi strategie automatiche
   in grado di uscire dall'apprendimento;
2. **Punteggio di ottimizzazione in risalita** dalla fascia 53–71 verso quella di
   PMax (77–88);
3. **Esposizione di budget ridotta da €1.940 a ~€450/giorno**, con la stessa spesa
   effettiva.

Il recupero economico vero, invece, dipende interamente dalla Priorità 0: **finché
una chiamata non ha un valore, la Search non è ottimizzabile — è solo misurabile.**

---

## 8. Dati ancora da recuperare

| Dato | Perché serve |
|---|---|
| **Costo per singola campagna** | Terzo export consecutivo con "Costo" a zero sulle righe campagna: senza, nessun ROAS o CPA per campagna è calcolabile |
| **Margine reale per chiamata** | Confronto con la soglia di pareggio di €13,53 |
| **Configurazione di Click-to-call e Calls from ads** | Verificare la sovrapposizione e uniformare il tracciamento tra campagne |
| **Valore del CPA target per campagna** | Le 4 campagne che fanno il 62,5% delle chiamate sono limitate dal bid |
| **Scomposizione del valore Niino Revenue per canale** | Capire perché la stessa azione vale €22 su Search e €280 su PMax |
| **Conversioni fuori dalle 14 campagne filtrate** | 29,69 conversioni (€29,69) del totale Ricerca non appartengono a nessuna delle campagne in export |

---

## Appendice A — Tutte le campagne Search (1/07 – 9/08/2026)

| Campagna | Gruppo | Budget/gg | Conv. | Valore | Strategia | Punt. ott. | Motivi dello stato |
|---|---|---:|---:|---:|---|---:|---|
| AMBULANZA \| CHIAMATA \| PUGLIA | Chiamata | € 200 | 157,80 | € 157,81 | CPA target | 58,56 | strategia di offerta; volume di ricerca |
| AMBULANZA \| CHIAMATA \| MILANO | Chiamata | € 270 | 149,40 | € 149,40 | CPA target | 58,56 | strategia di offerta; volume di ricerca |
| AMBULANZA \| CHIAMATA \| ROMA | Chiamata | € 120 | 109,45 | € 109,45 | CPA target | 57,77 | strategia di offerta; volume di ricerca |
| MILANO \| DIMISSIONI \| CHIAMATA | Chiamata | € 280 | 101,83 | € 101,83 | CPA target | 57,09 | strategia di offerta; volume di ricerca |
| CHIAMATA \| LUNGA PERCORRENZA \| SARDEGNA | Chiamata | € 130 | 80,50 | € 80,50 | CPA target | 70,63 | volume di ricerca limitato |
| AMBULANZA \| CHIAMATA \| TORINO | Chiamata | € 100 | 72,47 | € 72,47 | CPA target | 64,54 | volume di ricerca limitato |
| AMBULANZA \| CHIAMATA \| BOLOGNA | Chiamata | € 100 | 64,99 | € 64,99 | CPA target | 61,64 | volume di ricerca limitato |
| AMBULANZA \| CHIAMATA \| PALERMO | Chiamata | € 50 | 37,00 | € 37,00 | CPA target | 61,64 | volume di ricerca limitato |
| AMBULANZA \| CHIAMATA \| BARI | Chiamata | € 100 | 30,17 | € 30,17 | CPA target | 61,64 | volume di ricerca limitato |
| AMBULANZA \| CHIAMATA \| VARESE 2 | Chiamata | € 120 | 19,50 | € 19,50 | CPA target | 61,64 | volume di ricerca limitato |
| AMBULANZA \| CHIAMATA \| AGRIGENTO | Chiamata | € 50 | 7,00 | € 7,00 | Massimizza conversioni | 53,64 | — (Idoneo) |
| SEARCH \| AMBULANZA \| PURCHASE \| MILANO | Purchase | € 120 | 9,30 | € 177,41 | CPA target | 64,54 | volume di ricerca limitato |
| SEARCH \| ANZIANI \| MILANO \| PURCHASE | Purchase | € 150 | 3,00 | € 86,14 | CPA target | 60,39 | volume di ricerca limitato |
| SEARCH \| AMBULANZA \| PURCHASE \| ROMA | Purchase | € 150 | 2,00 | € 54,31 | CPA target | 64,54 | volume di ricerca limitato |
| **Totale campagne filtrate** | | **€ 1.940** | **844,42** | **€ 1.148,01** | | 61,2 medio | 13 su 14 limitate |

## Appendice B — Metriche complete per canale (1/07 – 9/08/2026)

| Metrica | Search | Performance Max | Account |
|---|---:|---:|---:|
| Costo | € 11.951,31 | € 7.091,15 | € 19.042,46 |
| Valore conv. | € 1.177,70 | € 6.151,98 | € 7.329,69 |
| **ROAS** | **0,10** | **0,87** | **0,38** |
| Netto | −€ 10.773,61 | −€ 939,17 | −€ 11.712,77 |
| Impressioni | 61.092 | 3.008.739 | 3.069.831 |
| Clic | 4.982 | 65.420 | 70.402 |
| CTR | 8,15% | 2,17% | 2,29% |
| CPC medio | € 2,40 | € 0,11 | € 0,27 |
| Conversioni | 874,11 | 42,18 | 916,29 |
| Costo/conv. | € 13,67 | € 168,12 | € 20,78 |
| Quota impr. ricerca | 63,15% | 24,06% | 43,34% |
| QI persa (ranking) | 36,31% | 67,35% | 52,04% |
| QI persa (budget) | 0,54% | 8,59% | 4,62% |
| QI superiore rete di ricerca | 43,52% | — | 43,52% |
| Coinvolgimento medio (GA4) | 67,55 s | 28,12 s | 36,49 s |

## Appendice C — Conversioni per azione, Search

| Azione di conversione | Conversioni | Valore | Valore/conv. | Gruppo |
|---|---:|---:|---:|---|
| Click-to-call | 513,16 | € 513,19 | € 1,00 | Chiamata |
| Calls from ads | 316,96 | € 316,96 | € 1,00 | Chiamata |
| **Niino Revenue** | **14,30** | **€ 317,86** | **€ 22,23** | Purchase |
| Purchase | 0,00 | € 0,00 | — | — |
| Booking GMV | 0,00 | € 0,00 | — | — |
| Niino Sign-up | 0,00 | € 0,00 | — | — |
| **Totale campagne filtrate** | **844,42** | **€ 1.148,01** | € 1,36 | |
| Fuori dalle 14 campagne | 29,69 | € 29,69 | € 1,00 | — |
| **Totale rete di ricerca** | **874,11** | **€ 1.177,70** | € 1,35 | |

Le azioni **Purchase, Booking GMV e Niino Sign-up sono a 0,00 su tutte le campagne**,
come nei due export precedenti. La campagna `SEARCH | MILANO | DIMISSIONI | CHIAMATA`
ha l'azione Purchase configurata e a zero.

## Appendice D — Note di metodo

**Costo per campagna.** La colonna "Costo" è a zero su tutte le righe di campagna: i
costi per gruppo sono stimati e sempre dichiarati come tali. Le due ipotesi del §3
sono volutamente agli estremi per mostrare che la conclusione non dipende dalla stima.

**Conversioni per €100 di budget (§4).** È un indicatore di efficienza *relativa*, non
un ROAS: mette in rapporto l'output di una campagna con il budget che le è stato
assegnato. È utilizzabile perché tutte le campagne del gruppo sono limitate dal volume
e non dal budget, quindi il budget misura l'intenzione di allocazione, non la spesa.

**Scarto rispetto all'export PMax.** Questo export è stato generato poco dopo quello
Performance Max dello stesso giorno: i totali di account differiscono di €26,04
(Search +€17,98, PMax +€8,06, +2,00 conversioni Search). È il normale consolidamento
dei dati infragiornalieri e non incide su nessuna delle conclusioni.

**Conversioni fuori perimetro.** Il totale rete di ricerca (874,11 conv. / €1.177,70)
supera il totale delle campagne filtrate (844,42 / €1.148,01) di 29,69 conversioni,
tutte di tipo chiamata. Provengono da campagne non incluse in questo export,
verosimilmente sospese o rimosse nel periodo.
