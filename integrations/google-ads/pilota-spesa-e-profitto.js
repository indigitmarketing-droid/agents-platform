/**
 * ============================================================================
 *  PILOTA SPESA & PROFITTO  —  Google Ads Script
 * ============================================================================
 *
 *  Script unico che copre 3 obiettivi:
 *
 *   1) CONTROLLO SPESA KEYWORD
 *      Mette in pausa (o riduce il bid) delle keyword che bruciano budget
 *      senza portare conversioni / profitto.
 *
 *   2) ESCLUSIONE BRAND SU PERFORMANCE MAX
 *      Crea/aggiorna una lista di parole chiave a corrispondenza inversa con
 *      i termini del brand e la applica a PMax (e, opzionalmente, a
 *      Search/Shopping) così che PMax NON intercetti le ricerche di marca.
 *      NB: l'API degli Script di Google Ads NON permette di aggiungere
 *      negative direttamente dentro PMax. Lo script usa quindi la lista
 *      condivisa e — dove l'API non consente l'associazione automatica —
 *      segnala nel report le campagne PMax da sistemare a mano.
 *
 *   3) BIDDING A PROFITTO / MARGINE
 *      Google Ads conosce il VALORE conversione (fatturato) ma non il
 *      MARGINE. Lo script applica un margine (globale o per campagna),
 *      calcola il profitto lordo e il POAS (Profit On Ad Spend) e:
 *        • alza il CPC dove il profitto è alto (solo campagne Manual CPC);
 *        • abbassa il CPC / mette in pausa dove si perde;
 *        • etichetta i "vincitori" e i "perdenti" (utile anche con Smart
 *          Bidding, dove il CPC del singolo termine non è modificabile).
 *
 *  SICUREZZA
 *    Alla prima esecuzione lo script gira in DRY_RUN (nessuna modifica reale,
 *    solo log). Controlla il report via email/log, poi imposta
 *    CONFIG.DRY_RUN = false per rendere operative le modifiche.
 *
 *  INSTALLAZIONE
 *    Google Ads → Strumenti → Azioni collettive → Script → [+] →
 *    incolla questo file → Autorizza → Anteprima → Pianifica (es. ogni giorno).
 *    Vedi README.md per la guida passo-passo.
 * ============================================================================
 */

// ===========================================================================
//  CONFIGURAZIONE  —  modifica SOLO questo blocco
// ===========================================================================
var CONFIG = {

  // --- Sicurezza --------------------------------------------------------
  DRY_RUN: true,                       // true = simula, non modifica nulla.
  EMAIL:   'indigit.marketing@gmail.com', // email per il riepilogo (vuoto = no email)
  DATE_RANGE: 'LAST_30_DAYS',          // finestra di analisi (costante GAQL)

  // --- MODULO 1: Controllo spesa keyword --------------------------------
  spend: {
    enabled: true,
    minCostToEvaluate:      10,   // valuta solo keyword con spesa >= (valuta account)
    pauseIfZeroConvAboveCost: 50, // 0 conversioni + spesa oltre soglia => PAUSA
    minClicksForZeroConvPause: 15 // ...e almeno N click (ha avuto traffico a sufficienza)
  },

  // --- MODULO 2: Esclusione brand su Performance Max --------------------
  brand: {
    enabled: true,
    // >>> INSERISCI QUI I TERMINI DEL TUO BRAND <<<
    terms: [
      'ilmiobrand',
      'il mio brand'
    ],
    matchType: 'phrase',                       // 'phrase' | 'exact' | 'broad'
    negativeListName: 'BRAND - Esclusioni (script)',
    applyToPerformanceMax: true,               // applica a tutte le PMax
    applyToSearchShopping: true,               // applica anche a Search/Shopping non-brand
    // Campagne che DEVONO continuare a intercettare il brand (campagne di marca):
    // se il nome contiene una di queste stringhe la lista NON viene applicata.
    brandCampaignNameContains: ['Brand', 'BRAND', 'Marca']
  },

  // --- MODULO 3: Bidding a profitto / margine ---------------------------
  profit: {
    enabled: true,
    defaultMargin: 0.35,                 // margine lordo medio (35%)
    // Override del margine per campagne il cui nome contiene la chiave:
    marginByCampaignContains: {
      // 'Outlet':  0.15,
      // 'Premium': 0.55
    },
    minConversions:     1,      // conversioni minime per considerare "profittevole"
    minCostToAct:       15,     // spesa minima per intervenire sui bid
    targetPoas:         1.6,    // POAS obiettivo: (valore*margine)/costo. >= => alza bid
    minPoas:            1.0,    // sotto il break-even => abbassa bid
    bidStepUpPct:       0.12,   // +12% CPC sui vincitori
    bidStepDownPct:     0.15,   // -15% CPC sui perdenti
    maxCpc:             3.00,   // tetto CPC (valuta account)
    minCpc:             0.05,   // pavimento CPC
    onlyManualCpc:      true    // modifica il CPC solo su campagne Manual CPC
  }
};

// Etichette applicate dallo script (create automaticamente)
var LABELS = {
  WIN:    'PROFITTO (script)',
  LOSS:   'PERDITA (script)',
  PAUSED: 'PAUSA-SCRIPT'
};

// Costanti GAQL per la finestra temporale accettate dallo script
var VALID_DATE_RANGES = [
  'TODAY', 'YESTERDAY', 'LAST_7_DAYS', 'LAST_14_DAYS', 'LAST_30_DAYS',
  'LAST_BUSINESS_WEEK', 'THIS_WEEK_SUN_TODAY', 'THIS_WEEK_MON_TODAY',
  'LAST_WEEK_SUN_SAT', 'LAST_WEEK_MON_SUN', 'THIS_MONTH', 'LAST_MONTH'
];


// ===========================================================================
//  MAIN
// ===========================================================================
function main() {
  var report = new RunReport();
  try {
    validateConfig(report);

    report.currency = AdsApp.currentAccount().getCurrencyCode();
    report.accountName = AdsApp.currentAccount().getName();
    report.timeZone = AdsApp.currentAccount().getTimeZone();
    report.dryRun = CONFIG.DRY_RUN;

    // Ogni modulo è isolato: un errore in uno non blocca gli altri.
    if (CONFIG.spend.enabled || CONFIG.profit.enabled) {
      try { optimizeKeywords(report); }
      catch (e) { report.warnings.push('Modulo keyword interrotto: ' + e); }
    }
    if (CONFIG.brand.enabled) {
      try { excludeBrandFromPmax(report); }
      catch (e) { report.warnings.push('Modulo brand interrotto: ' + e); }
    }
  } catch (e) {
    report.fatalError = String(e) + (e && e.stack ? '\n' + e.stack : '');
    Logger.log('ERRORE FATALE: ' + report.fatalError);
  }

  var text = report.render();
  Logger.log(text);
  sendEmail(report, text);
}


// ===========================================================================
//  MODULO 1 + 3:  Ottimizzazione keyword (spesa + profitto)
//  Un unico passaggio sui dati keyword decide, per ciascuna: PAUSA / BID- /
//  BID+ / ETICHETTA / NESSUNA AZIONE.
// ===========================================================================
function optimizeKeywords(report) {
  var rows = fetchKeywordMetrics();
  report.keywordsAnalyzed = rows.length;

  // 1) Decide l'azione per ogni keyword ---------------------------------
  var actions = [];       // { row, action, reason, newCpc, label }
  for (var i = 0; i < rows.length; i++) {
    var d = decideKeywordAction(rows[i]);
    if (d.action !== 'KEEP') actions.push(d);
  }

  // 2) Recupera gli oggetti Keyword (in blocchi) per applicare le modifiche
  var pairs = actions.map(function (a) {
    return [Number(a.row.adGroupId), Number(a.row.criterionId)];
  });
  var kwByKey = fetchKeywordObjects(pairs);

  // 3) Applica le azioni ------------------------------------------------
  for (var j = 0; j < actions.length; j++) {
    var a = actions[j];
    var kw = kwByKey[a.row.adGroupId + '_' + a.row.criterionId];
    if (!kw) { continue; } // keyword non più selezionabile (rimossa nel frattempo)
    applyKeywordAction(kw, a, report);
  }
}

/**
 * Estrae metriche per keyword via GAQL (l'oggetto Stats degli Script NON
 * espone il valore conversione, quindi si usa un report).
 * Restituisce un array di oggetti "row" già normalizzati.
 */
function fetchKeywordMetrics() {
  var query =
    'SELECT ' +
    '  campaign.name, campaign.bidding_strategy_type, ' +
    '  ad_group.id, ad_group.name, ' +
    '  ad_group_criterion.criterion_id, ' +
    '  ad_group_criterion.keyword.text, ' +
    '  ad_group_criterion.keyword.match_type, ' +
    '  metrics.cost_micros, metrics.clicks, ' +
    '  metrics.conversions, metrics.conversions_value ' +
    'FROM keyword_view ' +
    'WHERE segments.date DURING ' + CONFIG.DATE_RANGE + ' ' +
    "  AND campaign.status = 'ENABLED' " +
    "  AND ad_group.status = 'ENABLED' " +
    "  AND ad_group_criterion.status = 'ENABLED' " +
    "  AND campaign.advertising_channel_type = 'SEARCH'";

  var out = [];
  var iter = AdsApp.report(query).rows();
  while (iter.hasNext()) {
    var r = iter.next();
    var campaignName = r['campaign.name'];
    var cost = microsToCurrency(r['metrics.cost_micros']);
    out.push({
      campaignName:  campaignName,
      biddingType:   r['campaign.bidding_strategy_type'],
      adGroupId:     String(r['ad_group.id']),
      adGroupName:   r['ad_group.name'],
      criterionId:   String(r['ad_group_criterion.criterion_id']),
      text:          r['ad_group_criterion.keyword.text'],
      matchType:     r['ad_group_criterion.keyword.match_type'],
      cost:          cost,
      clicks:        Number(r['metrics.clicks']),
      conversions:   Number(r['metrics.conversions']),
      convValue:     Number(r['metrics.conversions_value']),
      margin:        marginForCampaign(campaignName)
    });
  }
  return out;
}

/**
 * Cuore della logica: dato lo storico della keyword decide cosa fare.
 */
function decideKeywordAction(row) {
  var p = CONFIG.profit;
  var s = CONFIG.spend;

  var grossProfit = row.convValue * row.margin;          // margine lordo generato
  var poas = row.cost > 0 ? grossProfit / row.cost : 0;  // Profit On Ad Spend
  var netProfit = grossProfit - row.cost;
  var isManual = String(row.biddingType) === 'MANUAL_CPC';

  var base = {
    row: row, grossProfit: grossProfit, poas: poas,
    netProfit: netProfit, isManual: isManual,
    action: 'KEEP', reason: '', newCpc: null, label: null
  };

  // (A) MODULO 1 — spesa senza conversioni => PAUSA
  if (s.enabled &&
      row.conversions === 0 &&
      row.cost >= s.pauseIfZeroConvAboveCost &&
      row.clicks >= s.minClicksForZeroConvPause) {
    base.action = 'PAUSE';
    base.label = LABELS.PAUSED;
    base.reason = 'Spesa ' + money(row.cost) + ' con 0 conversioni (' +
                  row.clicks + ' click).';
    return base;
  }

  // Da qui in giù serve una spesa minima per intervenire
  if (!p.enabled || row.cost < p.minCostToAct) {
    return base;
  }

  // (B) MODULO 3 — perdita: profitto lordo sotto il break-even => BID-
  if (poas < p.minPoas) {
    base.label = LABELS.LOSS;
    base.reason = 'POAS ' + poas.toFixed(2) + ' < ' + p.minPoas +
                  ' (perdita netta ' + money(netProfit) + ').';
    base.action = (isManual || !p.onlyManualCpc) ? 'BID_DOWN' : 'LABEL';
    return base;
  }

  // (C) MODULO 3 — vincitore: POAS alto e conversioni sufficienti => BID+
  if (poas >= p.targetPoas && row.conversions >= p.minConversions) {
    base.label = LABELS.WIN;
    base.reason = 'POAS ' + poas.toFixed(2) + ' >= ' + p.targetPoas +
                  ' (profitto netto ' + money(netProfit) + ').';
    base.action = (isManual || !p.onlyManualCpc) ? 'BID_UP' : 'LABEL';
    return base;
  }

  return base; // zona neutra: nessuna azione
}

/**
 * Applica concretamente l'azione decisa alla keyword (rispettando DRY_RUN).
 */
function applyKeywordAction(kw, a, report) {
  var p = CONFIG.profit;

  if (a.label) { ensureAndApplyLabel(kw, a.label); }

  if (a.action === 'PAUSE') {
    mutate(function () { kw.pause(); });
    report.paused.push(describeKw(a));
    return;
  }

  if (a.action === 'BID_UP' || a.action === 'BID_DOWN') {
    var current = safeGetCpc(kw);
    if (current === null) { // strategia non manuale: niente CPC modificabile
      report.labelledOnly.push(describeKw(a));
      return;
    }
    var factor = a.action === 'BID_UP'
      ? (1 + p.bidStepUpPct)
      : (1 - p.bidStepDownPct);
    var newCpc = clamp(round2(current * factor), p.minCpc, p.maxCpc);
    if (newCpc === current) { return; } // già al tetto/pavimento
    a.newCpc = newCpc;
    a.oldCpc = current;
    var ok = mutate(function () { kw.bidding().setCpc(newCpc); });
    if (ok) {
      (a.action === 'BID_UP' ? report.bidUp : report.bidDown).push(describeKw(a));
    } else {
      report.labelledOnly.push(describeKw(a));
    }
    return;
  }

  if (a.action === 'LABEL') {
    report.labelledOnly.push(describeKw(a));
  }
}


// ===========================================================================
//  MODULO 2:  Esclusione del brand da Performance Max (e Search/Shopping)
// ===========================================================================
function excludeBrandFromPmax(report) {
  var terms = CONFIG.brand.terms
    .map(function (t) { return String(t).trim(); })
    .filter(function (t) { return t.length > 0; });

  if (terms.length === 0) {
    report.brandNotes.push('Nessun termine brand configurato: modulo saltato.');
    return;
  }

  // 1) Lista negativa condivisa (creata/aggiornata) --------------------
  var list = getOrCreateNegativeList(CONFIG.brand.negativeListName, terms, report);
  if (!list) { return; }

  // 2) Applica alle Performance Max ------------------------------------
  if (CONFIG.brand.applyToPerformanceMax) {
    var pmaxIt = AdsApp.performanceMaxCampaigns()
      .withCondition("campaign.status = 'ENABLED'").get();
    while (pmaxIt.hasNext()) {
      var pmax = pmaxIt.next();
      attachListToCampaign(pmax, list, report, 'PMax');
    }
  }

  // 3) Applica a Search/Shopping (escludendo le campagne brand) --------
  if (CONFIG.brand.applyToSearchShopping) {
    attachToStandard(AdsApp.campaigns(), list, report, 'Search/Display');
    if (typeof AdsApp.shoppingCampaigns === 'function') {
      attachToStandard(AdsApp.shoppingCampaigns(), list, report, 'Shopping');
    }
  }
}

function attachToStandard(selector, list, report, kind) {
  var it = selector.withCondition("campaign.status = 'ENABLED'").get();
  while (it.hasNext()) {
    var c = it.next();
    if (isBrandCampaign(c.getName())) {
      report.brandSkipped.push(c.getName() + ' (campagna di marca)');
      continue;
    }
    attachListToCampaign(c, list, report, kind);
  }
}

/**
 * Crea la lista negativa se non esiste e vi aggiunge i termini brand mancanti.
 */
function getOrCreateNegativeList(name, terms, report) {
  var list = null;
  var it = AdsApp.negativeKeywordLists().get();
  while (it.hasNext()) {
    var l = it.next();
    if (l.getName() === name) { list = l; break; }
  }

  if (!list) {
    if (CONFIG.DRY_RUN) {
      // In dry-run non creiamo nulla, ma restituiamo una lista "virtuale" così
      // da poter comunque mostrare a quali campagne verrebbe applicata.
      report.brandNotes.push('[DRY-RUN] Creerei la lista negativa "' + name +
        '" con i termini: ' + terms.join(', '));
      return { getName: function () { return name; }, __virtual: true };
    }
    var built = AdsApp.newNegativeKeywordListBuilder().withName(name).build();
    if (!built.isSuccessful()) {
      report.brandNotes.push('Impossibile creare la lista negativa: ' +
        built.getErrors().join('; '));
      return null;
    }
    list = built.getResult();
    report.brandNotes.push('Lista negativa "' + name + '" creata.');
  }

  // Sincronizza i termini brand solo su una lista reale.
  if (typeof list.negativeKeywords === 'function') {
    var existing = {};
    var negIt = list.negativeKeywords().get();
    while (negIt.hasNext()) {
      existing[stripMatch(negIt.next().getText()).toLowerCase()] = true;
    }

    var toAdd = [];
    for (var i = 0; i < terms.length; i++) {
      if (!existing[terms[i].toLowerCase()]) {
        toAdd.push(formatNegative(terms[i], CONFIG.brand.matchType));
      }
    }

    if (toAdd.length > 0) {
      var ok = mutate(function () { list.addNegativeKeywords(toAdd); });
      report.brandNotes.push('Termini brand aggiunti alla lista: ' + toAdd.join(', '));
      if (!ok) {
        report.brandNotes.push('ATTENZIONE: aggiunta termini alla lista fallita.');
      }
    }
  }
  return list;
}

/**
 * Associa la lista negativa a una campagna, se non già associata.
 * Per PMax l'API degli Script potrebbe non supportare l'associazione: in tal
 * caso la campagna viene segnalata per l'intervento manuale.
 */
function attachListToCampaign(campaign, list, report, kind) {
  var name = campaign.getName();

  // Feature-detection: non tutte le entità espongono i metodi delle liste.
  if (typeof campaign.addNegativeKeywordList !== 'function') {
    report.brandManual.push(kind + ' » ' + name +
      ' (API Script non supporta le liste negative su questa campagna)');
    return;
  }

  // Evita duplicati se possibile
  try {
    if (typeof campaign.negativeKeywordLists === 'function') {
      var existing = campaign.negativeKeywordLists().get();
      while (existing.hasNext()) {
        if (existing.next().getName() === list.getName()) {
          report.brandAlreadyOn.push(kind + ' » ' + name);
          return;
        }
      }
    }
  } catch (e) { /* alcune entità non permettono la lettura: si prosegue */ }

  var ok = mutate(function () { campaign.addNegativeKeywordList(list); });
  if (ok) {
    report.brandApplied.push(kind + ' » ' + name);
  } else if (!CONFIG.DRY_RUN) {
    report.brandManual.push(kind + ' » ' + name +
      ' (associazione automatica non riuscita: applicare la lista a mano)');
  } else {
    report.brandApplied.push('[DRY-RUN] ' + kind + ' » ' + name);
  }
}


// ===========================================================================
//  HELPER
// ===========================================================================

/** Esegue una modifica solo se non siamo in DRY_RUN. Ritorna true se applicata. */
function mutate(fn) {
  if (CONFIG.DRY_RUN) { return true; } // simulazione: consideriamo "ok"
  try { fn(); return true; }
  catch (e) { Logger.log('Modifica non riuscita: ' + e); return false; }
}

/** Legge il CPC manuale corrente; null se la strategia non è manuale. */
function safeGetCpc(kw) {
  try {
    var cpc = kw.bidding().getCpc();
    return (cpc === null || cpc === undefined) ? null : cpc;
  } catch (e) { return null; }
}

function ensureAndApplyLabel(entity, name) {
  if (CONFIG.DRY_RUN) { return; } // in dry-run non creiamo/applichiamo etichette
  try { AdsApp.createLabel(name); } catch (e) { /* già esistente */ }
  try { entity.applyLabel(name); } catch (e) { /* già applicata o non applicabile */ }
}

function marginForCampaign(campaignName) {
  var map = CONFIG.profit.marginByCampaignContains || {};
  for (var key in map) {
    if (map.hasOwnProperty(key) && campaignName.indexOf(key) !== -1) {
      return map[key];
    }
  }
  return CONFIG.profit.defaultMargin;
}

function isBrandCampaign(name) {
  var list = CONFIG.brand.brandCampaignNameContains || [];
  for (var i = 0; i < list.length; i++) {
    if (name.indexOf(list[i]) !== -1) { return true; }
  }
  return false;
}

/** Recupera gli oggetti Keyword a blocchi di 10.000 (limite withIds). */
function fetchKeywordObjects(pairs) {
  var map = {};
  for (var start = 0; start < pairs.length; start += 10000) {
    var chunk = pairs.slice(start, start + 10000);
    if (chunk.length === 0) { continue; }
    var it = AdsApp.keywords().withIds(chunk).get();
    while (it.hasNext()) {
      var kw = it.next();
      map[kw.getAdGroup().getId() + '_' + kw.getId()] = kw;
    }
  }
  return map;
}

function formatNegative(term, matchType) {
  var t = stripMatch(term);
  if (matchType === 'exact')  { return '[' + t + ']'; }
  if (matchType === 'broad')  { return t; }
  return '"' + t + '"'; // phrase (default)
}

function stripMatch(term) {
  return String(term).replace(/^[\[\"]+|[\]\"]+$/g, '').trim();
}

function microsToCurrency(micros) {
  return Number(micros || 0) / 1000000;
}

function clamp(v, lo, hi) { return Math.max(lo, Math.min(hi, v)); }
function round2(v) { return Math.round(v * 100) / 100; }
function money(v) { return Number(v).toFixed(2); }

function describeKw(a) {
  var extra = '';
  if (a.action === 'BID_UP' || a.action === 'BID_DOWN') {
    extra = '  CPC ' + money(a.oldCpc) + ' → ' + money(a.newCpc);
  }
  return '[' + a.row.campaignName + '] "' + a.row.text + '" (' +
    a.row.matchType + ')  ' + a.reason + extra;
}

function validateConfig(report) {
  if (VALID_DATE_RANGES.indexOf(CONFIG.DATE_RANGE) === -1) {
    report.warnings.push('DATE_RANGE "' + CONFIG.DATE_RANGE +
      '" non valido: uso LAST_30_DAYS.');
    CONFIG.DATE_RANGE = 'LAST_30_DAYS';
  }
  if (CONFIG.brand.enabled &&
      (!CONFIG.brand.terms || CONFIG.brand.terms.length === 0)) {
    report.warnings.push('Modulo brand attivo ma nessun termine configurato.');
  }
}


// ===========================================================================
//  REPORT / EMAIL
// ===========================================================================
function RunReport() {
  this.dryRun = true;
  this.currency = '';
  this.accountName = '';
  this.timeZone = '';
  this.keywordsAnalyzed = 0;

  this.paused = [];
  this.bidUp = [];
  this.bidDown = [];
  this.labelledOnly = [];

  this.brandApplied = [];
  this.brandAlreadyOn = [];
  this.brandManual = [];
  this.brandSkipped = [];
  this.brandNotes = [];

  this.warnings = [];
  this.fatalError = null;
}

RunReport.prototype.render = function () {
  var L = [];
  L.push('==================================================');
  L.push(' PILOTA SPESA & PROFITTO — ' + this.accountName);
  L.push(' Modalità: ' + (this.dryRun ? 'DRY-RUN (nessuna modifica)' : 'LIVE'));
  L.push(' Periodo: ' + CONFIG.DATE_RANGE + '  Valuta: ' + this.currency);
  L.push('==================================================');

  if (this.fatalError) {
    L.push('');
    L.push('!!! ERRORE FATALE !!!');
    L.push(this.fatalError);
    return L.join('\n');
  }

  L.push('');
  L.push('KEYWORD ANALIZZATE: ' + this.keywordsAnalyzed);
  L.push('  • In pausa (spesa senza conversioni): ' + this.paused.length);
  L.push('  • CPC aumentato (profittevoli):       ' + this.bidUp.length);
  L.push('  • CPC ridotto (in perdita):           ' + this.bidDown.length);
  L.push('  • Solo etichettate (Smart Bidding):   ' + this.labelledOnly.length);

  L.push(section('PAUSA — spesa senza conversioni', this.paused));
  L.push(section('CPC AUMENTATO — vincitori a profitto', this.bidUp));
  L.push(section('CPC RIDOTTO — in perdita', this.bidDown));
  L.push(section('ETICHETTATE (CPC non modificabile: Smart Bidding)', this.labelledOnly));

  L.push('');
  L.push('----- ESCLUSIONE BRAND SU PMAX -----');
  for (var i = 0; i < this.brandNotes.length; i++) { L.push('  ' + this.brandNotes[i]); }
  L.push(section('Lista brand APPLICATA a', this.brandApplied));
  L.push(section('Già applicata (nessuna azione)', this.brandAlreadyOn));
  L.push(section('Campagne di marca ESCLUSE dallo script', this.brandSkipped));
  if (this.brandManual.length) {
    L.push('');
    L.push('  ⚠️  DA SISTEMARE A MANO (l\'API Script non associa le negative qui):');
    for (var m = 0; m < this.brandManual.length; m++) {
      L.push('     - ' + this.brandManual[m]);
    }
    L.push('     → In Google Ads apri la campagna PMax → Impostazioni →');
    L.push('       "Parole chiave escluse a livello di campagna" e incolla i');
    L.push('       termini brand, oppure applica la lista negativa condivisa.');
  }

  if (this.warnings.length) {
    L.push('');
    L.push('----- AVVISI -----');
    for (var w = 0; w < this.warnings.length; w++) { L.push('  ! ' + this.warnings[w]); }
  }

  if (this.dryRun) {
    L.push('');
    L.push('NB: DRY-RUN attivo. Per applicare davvero le modifiche imposta');
    L.push('    CONFIG.DRY_RUN = false e ripianifica lo script.');
  }
  return L.join('\n');
};

function section(title, items) {
  if (!items || items.length === 0) { return ''; }
  var out = ['', '----- ' + title + ' (' + items.length + ') -----'];
  var max = Math.min(items.length, 100); // evita email/log enormi
  for (var i = 0; i < max; i++) { out.push('  • ' + items[i]); }
  if (items.length > max) { out.push('  ... e altre ' + (items.length - max)); }
  return out.join('\n');
}

function sendEmail(report, text) {
  if (!CONFIG.EMAIL) { return; }
  try {
    var subject = 'Google Ads — Pilota Spesa & Profitto (' +
      (report.dryRun ? 'DRY-RUN' : 'LIVE') + ') — ' + report.accountName;
    MailApp.sendEmail({
      to: CONFIG.EMAIL,
      subject: subject,
      body: text
    });
  } catch (e) {
    Logger.log('Invio email non riuscito: ' + e);
  }
}
