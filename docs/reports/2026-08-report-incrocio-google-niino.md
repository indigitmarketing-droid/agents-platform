# Report Incrociato — Google Ads vs Dati Niino · Luglio 2026

**Fonti incrociate:**
- **Niino Advertising Performance Report** — 1 luglio → 31 luglio 2026 (generato 14/08/2026)
- **Google Ads, export campagne** — 1–24 luglio, 1 luglio–9 agosto (PMax e Search)

**Valuta:** EUR

---

## Avvertenza sui periodi

Le fonti non coprono la stessa finestra temporale. Ogni confronto in questo report
dichiara quale periodo usa:

| Fonte | Periodo | Giorni |
|---|---|---:|
| PDF Niino | 1–31 luglio 2026 | 31 |
| CSV Google Ads (primo export) | 1–24 luglio 2026 | 24 |
| CSV Google Ads (PMax e Search) | 1 luglio – 9 agosto 2026 | 40 |

Dove il confronto richiede una riproporzione, è indicata esplicitamente. **I confronti
esatti — quelli che non richiedono stime — sono segnalati come tali e sono la spina
dorsale del report.**

---

## 1. Sintesi esecutiva

Il report Niino contiene **il dato che mancava in tutti e tre gli export Google Ads:
il costo per campagna**. Con quello, e con i ricavi reali, tre domande rimaste aperte
si chiudono tutte insieme — e la risposta ribalta la lettura fatta finora.

### Le tre risposte

| Domanda aperta | Risposta dai dati Niino |
|---|---|
| **Quanto vale davvero una chiamata?** | **€3,36 di fee netta.** Ne costa **€19,03**. Serve **5,7×** il valore attuale per il pareggio |
| **Click-to-call e Calls from ads si sovrappongono?** | **Sì, quasi integralmente.** Google Ads conta **+59,6%** di chiamate rispetto a quelle reali |
| **Qual è il ROAS per campagna?** | **Una sola campagna su 22 è in profitto.** `PMAX \| ITALIA \| AMBULANZA` (+€1.474). Tutte le altre perdono |

### Il quadro reale di luglio: due ROAS, due letture

L'account va letto su **due metriche distinte, che non si sostituiscono a vicenda**:

| Metrica | Formula | Cosa misura | Luglio |
|---|---|---|---:|
| **ROAS** | GMV net booked / spesa | il transato intermediato dalla piattaforma | **4,59×** |
| **ROAS Fee Niino** | fee netta / spesa | il ricavo che resta a Niino | **0,53×** |

| Voce | Valore |
|---|---:|
| Spesa performance | € 13.938 |
| GMV net booked | € 63.969 |
| **ROAS** | **4,59×** |
| Fee Niino netta | € 7.007 |
| **ROAS Fee Niino** | **0,53×** |
| Take rate effettivo | 10,95% |
| **Margine netto** (fee − spesa) | **−€ 6.931** |

**Le due metriche raccontano due fatti entrambi veri:** la piattaforma sta
intermediando 4,59 euro di transato per ogni euro speso in advertising — è un dato di
scala reale e positivo — ma di quel transato Niino trattiene il 10,95%, e su quella
base l'account perde 47 centesimi per ogni euro speso.

**Il rapporto tra le due è il take rate effettivo**, e sarà la chiave di lettura del
capitolo 7: dove le due metriche divergono più del normale, il problema non è il
volume ma il tipo di corsa che la campagna porta.

### Dove si concentra la perdita

| Gruppo | Spesa | % spesa | GMV net | **ROAS** | Fee netta | **ROAS Fee** | Take rate | Margine |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| **Search Chiamata** (12 campagne) | € 7.670 | 50,9% | € 9.814 | **1,28×** | € 1.356 | **0,18×** | 13,8% | **−€ 6.314** |
| Performance Max (4 campagne) | € 4.845 | 32,1% | € 47.575 | **9,82×** | € 4.653 | **0,96×** | 9,8% | −€ 192 |
| Search Purchase (3 campagne) | € 1.422 | 9,4% | € 4.016 | 2,82× | € 647 | 0,45× | 16,1% | −€ 775 |
| Brand (2 campagne) | € 944 | 6,3% | € 620 | 0,66× | € 100 | 0,11× | 16,1% | −€ 844 |
| Partner (1 campagna) | € 195 | 1,3% | € 410 | 2,10× | € 28 | 0,14× | 6,8% | −€ 167 |
| **Totale campagne con spesa** | **€ 15.076** | 100% | **€ 62.435** | **4,14×** | **€ 6.784** | **0,45×** | 10,9% | **−€ 8.292** |

**Il gruppo Search Chiamata assorbe il 50,9% della spesa e produce il 76% della
perdita.** Performance Max, con un terzo della spesa, è sostanzialmente in pareggio.

Le due metriche insieme mostrano una cosa che nessuna delle due mostra da sola:
**Performance Max intermedia 9,82× ma trattiene solo il 9,8%, mentre Search Purchase
intermedia 2,82× e trattiene il 16,1%.** PMax porta corse molto più grandi ma a
marginalità più bassa.

Questa è la conferma — con i dati reali — di quello che i tre report su Google Ads
avevano indicato lavorando solo sui proxy: **il budget è sul canale sbagliato.**

---

## 2. Verifica di attendibilità: le due fonti coincidono

Prima di incrociare i numeri, va verificato che descrivano la stessa realtà. Il test
più netto disponibile è la spesa sui 24 giorni coperti da entrambe le fonti.

| Fonte | Spesa Google 1–24 luglio |
|---|---:|
| PDF Niino (somma del trend giornaliero) | € 9.968,02 |
| CSV Google Ads (totale account) | € 9.969,35 |
| **Scarto** | **€ 1,33 — 0,01%** |

**Le due fonti coincidono praticamente al centesimo.** Questo è il risultato più
importante del capitolo, perché stabilisce che tutto ciò che segue è un confronto
reale e non un artefatto di dati disallineati.

**Corollario diretto:** i problemi che emergono nel resto del report **non sono
problemi di raccolta dati.** La spesa passa correttamente; è la *configurazione delle
conversioni* dentro Google Ads a essere incompleta. È una differenza importante,
perché indica dove intervenire.

### Conferma dell'accelerazione di spesa

Il trend giornaliero del PDF conferma — e supera — quanto rilevato nel report PMax:

| Periodo | Spesa Google/giorno |
|---|---:|
| 1–15 luglio | € 392,99 |
| 16–31 luglio | € 523,23 |
| 1–24 luglio | € 415,33 |
| **25–31 luglio** | **€ 614,07** |

L'ultima settimana di luglio gira a **+47,9%** al giorno rispetto alle prime tre. Il
report PMax stimava €567/giorno per la finestra 25/7–9/8: il dato reale sulla sola
coda di luglio è **€614,07**. **L'accelerazione è stata più forte di quanto stimato.**

---

## 3. Il ribaltamento: ROAS reale per campagna

Con il costo per campagna finalmente disponibile, ecco il quadro che i tre report
precedenti non potevano calcolare. Ordinato per margine (fee netta − spesa).

| Campagna | Gruppo | Spesa | Pren. nette | GMV net | **ROAS** | Fee netta | **ROAS Fee** | **Margine** |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| **PMAX \| ITALIA \| AMBULANZA \| PURCHASE \| APP** | PMax | € 1.729 | 14 | € 37.752 | **21,83×** | € 3.203 | **1,85×** | **+€ 1.474** |
| SEARCH \| ANZIANI \| MILANO \| PURCHASE | S. Purchase | € 91 | 2 | € 288 | 3,16× | € 47 | 0,52× | −€ 44 |
| SEARCH \| AMBULANZA \| CHIAMATA \| VARESE 2 | S. Chiamata | € 158 | 1 | € 105 | 0,67× | € 21 | 0,13× | −€ 137 |
| SEARCH \| AMBULANZA \| CHIAMATA \| PALERMO | S. Chiamata | € 298 | 5 | € 998 | 3,35× | € 149 | 0,50× | −€ 149 |
| SEARCH \| AMBULANZA \| CHIAMATA \| BARI | S. Chiamata | € 182 | 1 | € 140 | 0,77× | € 23 | 0,13× | −€ 159 |
| SEARCH \| AMBULANZA \| PURCHASE \| ROMA | S. Purchase | € 434 | 13 | € 1.514 | 3,49× | € 268 | 0,62× | −€ 166 |
| sconto-doctorapp (Partnership) | Partner | € 195 | 2 | € 410 | 2,10× | € 28 | 0,14× | −€ 167 |
| SEARCH \| MILANO \| DIMISSIONI \| CHIAMATA | S. Chiamata | € 588 | 8 | € 3.289 | **5,59×** | € 420 | 0,71× | −€ 168 |
| PMAX \| PIEMONTE \| AMBULANZA \| PURCHASE \| APP | PMax | € 1.246 | 14 | € 6.730 | **5,40×** | € 1.035 | 0,83× | −€ 211 |
| SEARCH \| AMBULANZA \| CHIAMATA \| AGRIGENTO | S. Chiamata | € 228 | 1 | € 110 | 0,48× | € 13 | 0,06× | −€ 215 |
| SN - 1225 - Brand | Brand | € 329 | 4 | € 620 | 1,88× | € 100 | 0,30× | −€ 229 |
| PMAX \| ITALIA \| AEREO \| PURCHASE | PMax | € 604 | 8 | € 2.107 | 3,49× | € 273 | 0,45× | −€ 331 |
| SEARCH \| AMBULANZA \| CHIAMATA \| BOLOGNA | S. Chiamata | € 449 | 5 | € 636 | 1,42× | € 94 | 0,21× | −€ 355 |
| SEARCH \| AMBULANZA \| CHIAMATA \| TORINO | S. Chiamata | € 636 | 6 | € 847 | 1,33× | € 131 | 0,21× | −€ 505 |
| SEARCH \| AMBULANZA \| PURCHASE \| MILANO | S. Purchase | € 897 | 15 | € 2.214 | 2,47× | € 332 | 0,37× | −€ 565 |
| IG - FOLLERS (Meta) | Brand | € 615 | 0 | € 0 | 0,00× | € 0 | 0,00× | −€ 615 |
| SEARCH \| CHIAMATA \| LUNGA PERCORRENZA *(in pausa)* | S. Chiamata | € 755 | 0 | € 0 | 0,00× | € 0 | 0,00× | −€ 755 |
| SEARCH \| AMBULANZA \| CHIAMATA \| MILANO | S. Chiamata | € 984 | 4 | € 1.036 | 1,05× | € 126 | 0,13× | −€ 858 |
| SEARCH \| AMBULANZA \| CHIAMATA \| ROMA | S. Chiamata | € 984 | 3 | € 445 | 0,45× | € 71 | 0,07× | −€ 913 |
| SEARCH \| CHIAMATA \| LUNGA PERCORRENZA *(attiva)* | S. Chiamata | € 1.241 | 6 | € 1.476 | 1,19× | € 202 | 0,16× | −€ 1.039 |
| SEARCH \| AMBULANZA \| CHIAMATA \| PUGLIA | S. Chiamata | € 1.167 | 5 | € 732 | 0,63× | € 106 | 0,09× | −€ 1.061 |
| **PMAX \| LOMBARDIA \| AMBULANZA \| PURCHASE \| APP** | PMax | € 1.266 | 7 | € 986 | **0,78×** | € 142 | **0,11×** | **−€ 1.124** |
| **Totale** | | **€ 15.076** | **124** | **€ 62.435** | **4,14×** | **€ 6.784** | **0,45×** | **−€ 8.292** |

### Cinque letture

**1. Una campagna su 22 produce margine.** `PMAX | ITALIA | AMBULANZA | PURCHASE |
APP` genera +€1.474 con €1.729 di spesa. È l'unica. Tutte le altre 21 campagne
dell'account, insieme, perdono €9.766.

**2. Le cinque campagne peggiori bruciano €4.995 di margine.** Lombardia (−€1.124),
Puglia (−€1.061), Lunga Percorrenza attiva (−€1.039), Roma chiamata (−€913), Milano
chiamata (−€858). Insieme spendono **€5.642 — il 37,4% del budget dell'account — per
€647 di fee.**

**3. `SEARCH | CHIAMATA | LUNGA PERCORRENZA` in pausa ha comunque speso €755 senza
produrre nulla.** Zero prenotazioni, zero fee. È spesa completamente persa e va
verificata: una campagna in pausa che spende €755 in un mese è un'anomalia da
chiarire in piattaforma.

**4. Le priorità dei report precedenti sono confermate, con una eccezione.** Agrigento,
Varese 2 e Bari — che il report Search indicava da chiudere per volumi insufficienti —
sono effettivamente in fondo alla classifica. Ma **Lombardia, che il report PMax
indicava da chiudere, risulta la campagna peggiore in assoluto dell'intero account**:
−€1.124 di margine, ROAS Fee 0,11×. La decisione era giusta; l'urgenza era
sottostimata.

**5. Il ticket medio di `ITALIA | AMBULANZA` è fuori scala.** €37.752 di GMV netto su
14 prenotazioni nette fanno **€2.697 per prenotazione**, contro una media account di
€481. La campagna che regge il conto economico dell'account **poggia su pochi
trasferimenti ad altissimo valore**: con 14 prenotazioni, il risultato è concentrato e
volatile. Va monitorato mensilmente, non trattato come una base stabile.

---

## 4. Le chiamate: la domanda aperta ha una risposta, ed è negativa

Il report Search si fermava qui: *"finché una chiamata non ha un valore, la Search non
è ottimizzabile"*. Il PDF fornisce il valore.

### Il doppio conteggio è confermato

Confronto tra le conversioni-chiamata di Google Ads (riproporzionate da 40 a 31
giorni) e le chiamate realmente registrate da Niino sul canale `google_ads`:

| Fonte | Chiamate (31 gg) | Scarto vs reale |
|---|---:|---:|
| Google Ads — **Click-to-call** | 397,7 | **−1,3%** |
| Google Ads — Calls from ads | 245,6 | — |
| Google Ads — **totale conversioni chiamata** | **643,3** | **+59,6%** |
| **Niino — chiamate reali da google_ads** | **403** | — |

**Click-to-call da solo coincide con il dato reale entro l'1,3%.** L'aggiunta di
*Calls from ads* gonfia il conteggio del 59,6%: **le 245,6 conversioni di "Calls from
ads" sono, in sostanza, la stessa telefonata contata una seconda volta.**

Il sospetto sollevato nel report Search — rapporto tra le due azioni da 9% a 144% tra
campagne — trova qui la conferma quantitativa. **Il CPA target di 11 campagne sta
ottimizzando contro un denominatore gonfiato del 60%.**

### Quanto vale e quanto costa una chiamata

| | Valore |
|---|---:|
| Spesa gruppo Search Chiamata (luglio) | € 7.670 |
| Chiamate reali da google_ads | 403 |
| **Costo per chiamata reale** | **€ 19,03** |
| Fee netta generata dal gruppo | € 1.356 |
| **Fee netta per chiamata** | **€ 3,36** |
| **Gap per chiamata** | **−€ 15,67** |
| Prenotazioni nette dal gruppo | 45 |
| Tasso chiamata → prenotazione netta | **11,2%** |

**Una chiamata costa €19,03 e produce €3,36 di ricavo netto per Niino. Serve 5,7 volte
il valore attuale perché il gruppo vada in pareggio.**

Due precisazioni che vanno nella stessa direzione:

- La soglia di pareggio stimata nel report Search era **€13,53 per chiamata**, calcolata
  sul conteggio Google Ads. Con le chiamate reali il costo effettivo è **€19,03**:
  la soglia era sottostimata del 29%, esattamente perché il denominatore era gonfiato.
- Il tasso di conversione chiamata → prenotazione (**11,2%**) è invece **molto migliore**
  del 3,10% stimato nel report di luglio, perché Google Ads vede solo un terzo delle
  prenotazioni. **Le chiamate convertono bene; il problema è che costano troppo per
  quello che valgono.**

Questo cambia la natura della decisione: non serve migliorare la conversione delle
chiamate — serve **ridurre di 5 volte il costo di acquisizione**, oppure spostare il
budget. Sul canale Search, con volume di ricerca limitato e CPC medio a €2,40, la prima
strada non è percorribile.

---

## 5. Cosa Google Ads non vede

Le quattro azioni di conversione ferme a 0,00 in tutti e tre gli export corrispondono
a eventi che **esistono e sono misurati da Niino**:

| Azione in Google Ads | Valore in Google Ads | Realtà (PDF, luglio) |
|---|---:|---|
| **Purchase** | 0,00 | **180 prenotazioni lorde** (46 purchases da KPI piattaforma) |
| **Booking GMV** | € 0,00 | **€ 71.621 di GMV booked** |
| **Niino Sign-up** | 0,00 | **426 nuovi utenti**, di cui 320 da Google |
| **Conversazione avviata** | 0,00 | **1.108 chiamate** + 18 WhatsApp |

**Google Ads sta ottimizzando alla cieca su 4 azioni su 8.** Le strategie automatiche
— CPA target su 14 campagne, Massimizza valore su una — non possono ottimizzare verso
segnali che non ricevono.

Questo si lega direttamente alla diagnosi del report PMax: il CPA target sulle campagne
AMBULANZA ha comprato volume a basso valore perché **l'unico segnale di valore che
riceve è "Niino Revenue", e nemmeno quello è completo** (§6).

### Le cancellazioni: il 26% delle conversioni non esiste

Google Ads conta la prenotazione, non la cancellazione. Nel periodo:

| | Valore |
|---|---:|
| Prenotazioni lorde | 180 |
| Cancellate | **47** |
| **Tasso di cancellazione** | **26,11%** |
| Prenotazioni nette | 133 |

Il tasso varia enormemente per campagna, e **la variazione non è casuale**:

| Campagna | Cancellazioni |
|---|---:|
| SEARCH \| AMBULANZA \| CHIAMATA \| VARESE 2 | **67%** |
| SN - 1225 - Brand | 50% |
| SEARCH \| AMBULANZA \| CHIAMATA \| TORINO | 40% |
| PMAX \| ITALIA \| AEREO | 38% |
| SEARCH \| AMBULANZA \| CHIAMATA \| PUGLIA | 38% |
| PMAX \| PIEMONTE \| AMBULANZA | 33% |
| PMAX \| ITALIA \| AMBULANZA | **18%** |
| SEARCH \| AMBULANZA \| PURCHASE \| ROMA | **0%** |

**Le campagne regionali PMax cancellano il doppio della campagna nazionale** (33% e 13%
contro 18%). Il report PMax attribuiva il divario Piemonte/Lombardia agli asset e alle
norme: i dati mostrano che **una parte del divario è a valle, sulla qualità della
prenotazione**, non sulla campagna.

Nessuna di queste informazioni rientra in Google Ads. Finché non rientra, **ogni CPA
target è impostato su un numeratore che include il 26% di prenotazioni che non
avverranno.**

---

## 6. Quanto è affidabile il segnale su cui Google ottimizza

L'unica azione che porta valore economico in Google Ads è **Niino Revenue**. Il
confronto con la fee reale mostra che il segnale è **corretto in aggregato e inaffidabile
per campagna**.

Confronto tra il valore Niino Revenue di Google Ads (1/7–9/8, 40 giorni) e la fee netta
del PDF riproporzionata sullo stesso numero di giorni:

| Campagna | Google Ads | Fee reale (riprop.) | Copertura |
|---|---:|---:|---:|
| SEARCH \| ANZIANI \| MILANO \| PURCHASE | € 86,14 | € 60,65 | **142%** |
| PMAX \| ITALIA \| AMBULANZA \| PURCHASE \| APP | € 4.920,16 | € 4.132,90 | **119%** |
| PMAX \| ITALIA \| AEREO \| PURCHASE | € 253,48 | € 352,26 | 72% |
| PMAX \| PIEMONTE \| AMBULANZA \| PURCHASE \| APP | € 767,28 | € 1.335,48 | 57% |
| PMAX \| LOMBARDIA \| AMBULANZA \| PURCHASE \| APP | € 104,62 | € 183,23 | 57% |
| SEARCH \| AMBULANZA \| PURCHASE \| MILANO | € 177,41 | € 428,39 | 41% |
| SEARCH \| AMBULANZA \| PURCHASE \| ROMA | € 54,31 | € 345,81 | **16%** |
| **Totale** | **€ 6.363,40** | **€ 6.838,71** | **93%** |

> La riproporzione 31 → 40 giorni assume un ritmo costante, che sappiamo non esserlo:
> il valore è crollato nella finestra di agosto. Le percentuali per campagna sono quindi
> indicative. **Lo scarto tra le campagne, però, è troppo ampio per essere spiegato dalla
> sola riproporzione**, ed è il punto che conta.

**In aggregato il segnale copre il 93% della fee reale: buono. Per campagna oscilla tra
il 16% e il 142%: inutilizzabile.**

Le conseguenze sono concrete e spiegano i report precedenti:

- Google Ads **sovrastima Italia Ambulanza (119%) e sottostima le regionali (57%)**.
  L'algoritmo riceve il segnale che il nazionale rende il doppio di quanto rende
  davvero rispetto alle regionali, e alloca di conseguenza.
- Su `SEARCH | AMBULANZA | PURCHASE | ROMA` Google Ads vede **il 16% del valore reale**.
  Il report Search classificava questa campagna come la peggiore del gruppo Purchase e
  ne raccomandava la sospensione: **con i dati reali è la seconda migliore del gruppo**
  (ROAS Fee 0,62×, 0% di cancellazioni, CPA netto €33). **Quella raccomandazione era
  sbagliata, ed era sbagliata perché il dato in Google Ads era falso.**

---

## 7. ROAS e ROAS Fee Niino: due metriche, due domande

Le due metriche rispondono a domande diverse e **vanno lette insieme, mai una al posto
dell'altra**:

| Metrica | Formula | Risponde a | Luglio |
|---|---|---|---:|
| **ROAS** | GMV net booked / spesa | *Quanto transato genera l'advertising?* | **4,59×** |
| **ROAS Fee Niino** | fee netta / spesa | *Quanto ne resta a Niino?* | **0,53×** |

Il primo misura la **scala della piattaforma**: quanto volume di corse l'advertising
mette in moto. È il numero che descrive la crescita del marketplace e che conta per il
posizionamento e per i fornitori.

Il secondo misura la **sostenibilità economica**: Niino trattiene il take rate — nel
periodo il **10,95%** — e su quella base l'advertising deve ripagarsi. Il margine lo
dice senza ambiguità: **fee €7.007 − spesa performance €13.938 = −€6.931.** Includendo
tutta la spesa (€14.882, con Meta e brand), la perdita di luglio è **−€7.875**.

### Il rapporto tra le due è il take rate effettivo

Qui sta il valore di tenerle separate: **il take rate non è uniforme tra campagne, e
varia dal 6,8% al 20,0%.**

| Campagna | **ROAS** | **ROAS Fee** | Take rate effettivo |
|---|---:|---:|---:|
| SEARCH \| AMBULANZA \| CHIAMATA \| VARESE 2 | 0,67× | 0,13× | **20,0%** |
| SEARCH \| AMBULANZA \| PURCHASE \| ROMA | 3,49× | 0,62× | 17,7% |
| SEARCH \| AMBULANZA \| CHIAMATA \| BARI | 0,77× | 0,13× | 16,4% |
| SEARCH \| ANZIANI \| MILANO \| PURCHASE | 3,16× | 0,52× | 16,3% |
| SEARCH \| AMBULANZA \| CHIAMATA \| ROMA | 0,45× | 0,07× | 16,0% |
| SEARCH \| AMBULANZA \| CHIAMATA \| TORINO | 1,33× | 0,21× | 15,5% |
| PMAX \| PIEMONTE \| AMBULANZA | 5,40× | 0,83× | 15,4% |
| SEARCH \| AMBULANZA \| PURCHASE \| MILANO | 2,47× | 0,37× | 15,0% |
| PMAX \| LOMBARDIA \| AMBULANZA | 0,78× | 0,11× | 14,4% |
| PMAX \| ITALIA \| AEREO | 3,49× | 0,45× | 13,0% |
| SEARCH \| MILANO \| DIMISSIONI \| CHIAMATA | 5,59× | 0,71× | 12,8% |
| **PMAX \| ITALIA \| AMBULANZA** | **21,83×** | **1,85×** | **8,5%** |
| sconto-doctorapp (Partnership) | 2,10× | 0,14× | 6,8% |
| **Media account** | **4,59×** | **0,53×** | **10,95%** |

Tre conseguenze operative:

**1. `PMAX | ITALIA | AMBULANZA` ha il ROAS più alto dell'account e il take rate più
basso tra le campagne che producono.** 21,83× di transato con l'8,5% trattenuto: porta
corse molto grandi — €2.697 di ticket medio contro €481 di media account — su cui Niino
guadagna proporzionalmente meno. **È comunque l'unica campagna in profitto**, ma il suo
ROAS di 21,83× non va letto come "vale 21 volte quello che costa": vale 1,85 volte.

**2. Le campagne con take rate alto hanno ticket bassi.** Varese 2 al 20% e Bari al
16,4% trattengono molto su corse piccole (€105 e €140 di GMV totale nel mese): la
marginalità percentuale è ottima, il volume è irrilevante. **Non è una leva di crescita.**

**3. Il take rate è un criterio di selezione a sé.** A parità di ROAS Fee, la campagna
con take rate più alto è più difendibile: dipende meno dal ticket medio, quindi è meno
volatile. `SEARCH | AMBULANZA | PURCHASE | ROMA` (3,49× / 0,62× / 17,7%, 0%
cancellazioni) è il profilo più solido dell'account dopo Italia Ambulanza.

### Regola operativa

> **Entrambe le metriche vanno riportate su ogni campagna, ogni mese.**
>
> - Il **ROAS** dice se la campagna porta volume alla piattaforma.
> - Il **ROAS Fee Niino** dice se si ripaga. La soglia di pareggio è **1,0×**.
> - Il loro **rapporto** dice che tipo di corse porta.
>
> Oggi l'account è a ROAS 4,59× e ROAS Fee 0,53×: **la piattaforma cresce e
> l'advertising perde.** Una sola campagna su 22 sta sopra 1,0× di ROAS Fee.

---

## 8. Incoerenze interne al report Niino

Tre punti da correggere nel PDF stesso, perché incidono sui KPI di testata.

**1. Tre valori diversi di "spesa performance".**

| Dove | Valore | Composizione |
|---|---:|---|
| Pagina 1, dettaglio KPI | € 13.938 | Google, con AEREO e ANZIANI classificate come performance |
| Pagina 14, split piattaforma | € 13.243 | Google, con AEREO e ANZIANI classificate come brand |
| Pagina 14, riepilogo | € 13.858 | € 13.243 Google + € 615 Meta |

Lo scarto di **€695** è esattamente `SEARCH | ANZIANI | MILANO | PURCHASE` (€91,24) +
`PMAX | ITALIA | AEREO | PURCHASE` (€603,95): **due campagne classificate come brand
in una sezione e come performance in un'altra.**

**2. ROAS e ROAS Fee usano denominatori diversi.**

- ROAS 4,59× = 63.969 / **13.938**
- ROAS Fee 0,53× = 7.007 / **13.243**

Con lo stesso denominatore sarebbero 4,59× / 0,50× oppure 4,83× / 0,53×. Il margine
netto (−€6.931) usa 13.938. **Vanno allineati**: la scelta corretta dipende da come si
classificano AEREO e ANZIANI, ma deve essere una sola.

**3. L'obiettivo "costo per corsa" è calcolato sulle prenotazioni lorde.**

| Base | Calcolo | Risultato | vs target € 104 |
|---|---|---:|---:|
| Lorde (come nel PDF) | 14.882 / 180 | € 83 | **−20,5%** ✅ |
| **Nette** (base usata in Obiettivi) | 14.882 / 133 | **€ 112** | **+7,6%** ❌ |

La tabella Obiettivi BP dichiara **"Corse nette prenotate 180"**, ma 180 sono le lorde;
le nette sono 133 (lo dice la riconciliazione a pagina 5, che riporta anche "CPA blended
€112"). **Sulla base netta il target di CPA non è battuto del 20%: è mancato dell'8%.**

Stesso effetto sul CPU: €31 (spesa performance / 426) contro €35 (spesa totale / 426).

---

## 9. Correzioni ai report precedenti

I dati reali confermano l'impianto dei tre report su Google Ads e correggono tre punti.

| Report | Conclusione precedente | Con i dati Niino |
|---|---|---|
| PMax (luglio) | "PMax è profittevole, ROAS 2,15" | **PMax è a ROAS Fee 0,96× — in pareggio, non in profitto.** Il 2,15 era calcolato su un valore Google Ads che sovrastima la fee di circa il 50% |
| Search | "Sospendere `SEARCH \| AMBULANZA \| PURCHASE \| ROMA`" | **Da mantenere.** È la seconda migliore del gruppo Purchase (ROAS Fee 0,62×, 0% cancellazioni). Google Ads ne vedeva il 16% del valore |
| Search | "Soglia di pareggio €13,53 per chiamata" | **€19,03.** La soglia era sottostimata del 29% per via del doppio conteggio |
| Luglio | "Tasso chiamata → vendita 3,10%" | **11,2%.** Google Ads vede circa un terzo delle prenotazioni |
| PMax | "Chiudere Lombardia" | **Confermato e urgente.** È la peggiore dell'intero account: −€1.124 di margine |

**La direzione strategica indicata dai tre report resta valida — spostare budget dalla
Search a PMax Italia Ambulanza — ma la magnitudine cambia: PMax non è un canale in
profitto da scalare, è un canale in pareggio da rendere profittevole prima di
scalarlo.**

---

## 10. Piano operativo rivisto

### Priorità 0 — misurazione (questa settimana, costo zero)

| # | Azione | Impatto |
|---|---|---|
| 1 | **Rimuovere "Calls from ads" dalle conversioni di offerta** (tenerla come metrica di osservazione) | Elimina il 60% di doppio conteggio su cui 11 campagne stanno ottimizzando |
| 2 | **Importare in Google Ads le 4 azioni a zero** — prenotazione, GMV, signup, conversazione | Restituisce alle strategie automatiche i segnali che oggi non vedono |
| 3 | **Importare le cancellazioni come conversione negativa o correggere il valore a posteriori** | Toglie dal numeratore il 26% di prenotazioni che non avverranno |
| 4 | **Verificare l'attribuzione di Niino Revenue per campagna** | Copertura dal 16% al 142%: il segnale di valore per campagna oggi non è affidabile |

Nessuna richiede budget. **Senza queste quattro, ogni ottimizzazione successiva agisce
su dati che sappiamo essere sbagliati.**

### Priorità 1 — tagli (entro 7 giorni)

| # | Azione | Margine luglio |
|---|---|---:|
| 5 | **Chiudere `PMAX \| LOMBARDIA \| AMBULANZA`** | −€ 1.124 |
| 6 | **Chiudere `SEARCH \| AMBULANZA \| CHIAMATA \| PUGLIA`** | −€ 1.061 |
| 7 | **Verificare e chiudere `SEARCH \| CHIAMATA \| LUNGA PERCORRENZA`** (entrambe: attiva e in pausa) | −€ 1.794 |
| 8 | **Chiudere `SEARCH \| AMBULANZA \| CHIAMATA \| ROMA` e `\| MILANO`** | −€ 1.771 |
| 9 | **Chiudere Agrigento, Bari, Varese 2** (già indicate nel report Search) | −€ 511 |
| 10 | **Rivedere `IG - FOLLERS`**: €615 di spesa, zero prenotazioni, zero fee | −€ 615 |
| | **Totale margine recuperabile** | **≈ € 6.876/mese** |

Le campagne dei punti 5–9 valgono insieme **€6.965 di spesa mensile per €704 di fee**.
Chiuderle **non riduce il fatturato in modo apprezzabile** e riporta il margine
dell'account vicino al pareggio.

### Priorità 2 — concentrazione (settimane 2–4)

11. **Portare il budget liberato su `PMAX | ITALIA | AMBULANZA | PURCHASE | APP`**, a
    step del +20% ogni due settimane, verificando il ROAS Fee a ogni step. È l'unica
    campagna sopra 1,0×.
12. **Passarla da CPA target a Massimizza il valore di conversione**, come già indicato
    nel report PMax — ma **solo dopo** il punto 2 della Priorità 0, altrimenti ottimizza
    su un valore incompleto.
13. **Tenere `SEARCH | AMBULANZA | PURCHASE | ROMA` e `MILANO | DIMISSIONI`**: sono le
    due Search meno in perdita (0,62× e 0,71×) e le uniche con margine di recupero
    realistico.
14. **Ricostruire Piemonte sul modello Italia** e affrontare il 33% di cancellazioni,
    che è un problema a valle della campagna.

### La soglia da fissare adesso

> **Ogni campagna va giudicata su entrambe le metriche, riportate affiancate:**
>
> - **ROAS Fee Niino ≥ 1,0×** è la condizione di sopravvivenza della campagna;
>   **≥ 1,5×** è la condizione per aumentarne il budget.
> - **Il ROAS** resta il criterio per valutare il contributo alla crescita della
>   piattaforma, e il suo rapporto con il ROAS Fee segnala il tipo di corse portate.
>
> A luglio, su 22 campagne, **una** superava 1,0× di ROAS Fee.

---

## 11. Dati ancora da recuperare

| Dato | Perché serve |
|---|---|
| **Perché una campagna in pausa ha speso €755** | `SEARCH \| CHIAMATA \| LUNGA PERCORRENZA` in pausa: spesa senza alcun risultato |
| **Metodo di calcolo dell'LTV (€312)** | LTV/CPU 10,1× è l'unica metrica che giustifica la spesa attuale, a fronte di un margine mensile di −€6.931. Va verificata la coerenza dei due orizzonti temporali |
| **Regola di attribuzione di Niino Revenue** | Copertura per campagna dal 16% al 142% |
| **Classificazione brand/performance di AEREO e ANZIANI** | Determina quale dei tre valori di spesa performance è quello corretto |
| **Export Google Ads con costo per campagna** | Resta utile per il monitoraggio settimanale: oggi il costo per campagna arriva solo dal report Niino, con un mese di ritardo |
| **Dettaglio delle 46 "purchases" della sezione KPI piattaforma** | Non coincide né con le 180 lorde né con le 133 nette |

---

## Appendice A — Riconciliazione delle fonti

| Voce | PDF Niino | CSV Google Ads | Scarto |
|---|---:|---:|---:|
| Spesa Google 1–24 luglio | € 9.968,02 | € 9.969,35 | **0,01%** |
| Spesa Google 25–31 luglio | € 4.298,52 | non disponibile | — |
| Spesa Google luglio (31 gg) | € 14.266,54 | non disponibile | — |
| Impressioni Google luglio | 2.498.125 | non disponibile | — |
| Clic Google luglio | 56.498 | non disponibile | — |
| Valore conversione / fee netta | € 7.007 (fee, 31 gg) | € 6.363,40 (Niino Revenue, 40 gg) | vedi §6 |
| Chiamate da google_ads | 403 (31 gg) | 643,3 riproporzionate | **+59,6%** |

## Appendice B — Funnel completo (PDF, luglio)

| Step | Meta | Google | Totale |
|---|---:|---:|---:|
| Impressioni | 0 | 2.497.573 | 2.497.573 |
| Clic | 0 | 56.373 | 56.373 |
| Sessioni landing | 169 | 35.109 | 43.372 |
| Intenti CTA | 31 | 2.115 | 2.942 |
| Preventivi e bozze | 40 | 1.064 | 1.203 |
| Registrazioni | 9 | 320 | 426 |
| **Prenotazioni** | 0 | **125** | **180** |
| GMV | — | — | € 71.621 |

Tassi di passaggio su Google: clic → sessione **62,3%**, sessione → CTA **6,0%**,
CTA → bozza **50,3%**, bozza → registrazione **30,1%**, registrazione → prenotazione
**39,1%**. Il collo di bottiglia è **sessione → intento CTA**: su 35.109 sessioni solo
2.115 esprimono un intento.

## Appendice C — Metriche di piattaforma (PDF, luglio)

| Metrica | Google | Meta | Totale |
|---|---:|---:|---:|
| Spesa | € 14.266,53 | € 615,22 | € 14.881,75 |
| Impressioni | 2.498.125 | 143.089 | 2.641.214 |
| Clic | 56.498 | 4.887 | 61.385 |
| CTR | 2,26% | 3,42% | 2,32% |
| CPC | € 0,25 | € 0,13 | € 0,24 |
| Prenotazioni attribuite | 125 | 0 | 180 |

**Meta ha speso €615,22 e prodotto zero prenotazioni, zero registrazioni e 169 sessioni
di landing.** Il CTR del 3,42% è il più alto dell'account e non si traduce in nulla a
valle.

## Appendice D — Note di metodo

**Raggruppamento delle campagne.** Il PDF classifica `PMAX | ITALIA | AEREO` e
`SEARCH | ANZIANI | MILANO | PURCHASE` come campagne brand (pagina 16) ma le conteggia
tra le performance nei KPI di pagina 1. In questo report sono raggruppate secondo la
loro natura e coerentemente con gli export Google Ads: AEREO tra le PMax, ANZIANI tra
le Search Purchase. Il gruppo "Brand" contiene quindi solo `SN - 1225 - Brand` e
`IG - FOLLERS`.

**Totali.** La somma delle campagne con spesa (€15.076, fee €6.784) differisce dai
totali di account del PDF (spesa performance €13.938, fee netta €7.007) perché include
brand e partner ed esclude le prenotazioni non attribuite a campagne con spesa. Gli
scarti sono dichiarati dove rilevanti.

**Riproporzioni.** Ogni confronto tra periodi diversi è riproporzionato linearmente sui
giorni e sempre segnalato. Le riproporzioni assumono un ritmo costante: dove il ritmo è
noto come variabile — la coda di agosto — il limite è dichiarato nel testo.

**Chiamate reali.** Le 403 chiamate sono quelle registrate da Niino sul canale
`google_ads` nella tabella Canali del PDF. Includono le chiamate da tutte le campagne
Google, non solo dal gruppo Chiamata: il costo per chiamata di €19,03, calcolato sulla
sola spesa del gruppo Chiamata, è quindi una stima **prudente per difetto**.
