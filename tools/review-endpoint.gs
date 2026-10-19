/**
 * Review endpoint — Steamboat mockup
 * =================================================================
 * Receives section reviews from the mockup's review overlay and
 * upserts them into the "Web Mockup Feedback" spreadsheet.
 *
 * ONE-TIME SETUP
 *   1. Open the spreadsheet → Extensions → Apps Script.
 *   2. Delete whatever is in Code.gs and paste this whole file in.
 *   3. Run  setup  once (choose it in the toolbar dropdown, press Run,
 *      and grant the permissions it asks for). This builds the header
 *      row, the Status dropdown and the colour rules.
 *   4. Deploy → New deployment → Web app
 *        Execute as ............ Me
 *        Who has access ........ Anyone          <-- must be "Anyone"
 *      Copy the /exec URL it gives you.
 *   5. Paste that URL into ENDPOINT at the top of docs/js/review.js.
 *
 * AFTER EDITING THIS FILE you must Deploy → Manage deployments →
 * (pencil) → Version: New version, or the live URL keeps running the
 * old code.
 *
 * WHAT THE TEAM OWNS
 *   Columns J, K and L (Status / Owner / Notes) are never written by
 *   this script. Reviewers own A–I; you own J–L.
 *
 * PAGES TAB (sign-off tracker)
 *   Run  buildPagesTab  from the editor to (re)build a "Pages" tab: one
 *   row per page in the live review manifest, with formulas that roll
 *   the Reviews tab up into a stage per page. Re-run it whenever pages
 *   are added — the team columns (Sign-off owner … Notes) are kept.
 *   It runs from the editor only, so no new deployment is needed.
 * =================================================================
 */

var SHEET_ID = '1Or0nSVzPaKYc9baAadx2v887wXSCKTrfPRmGI8JsO9Y';
var TAB      = 'Reviews';

var HEADERS = [
  'Key', 'Updated', 'Reviewer', 'Page', 'Section', 'Label',
  'Verdict', 'Comment', 'Link',        // <- written by the overlay
  'Status', 'Owner', 'Team notes'      // <- yours, never overwritten
];
var LOCKED_FROM = 9;                   // columns A..I are the overlay's

var STATUSES = ['Open', 'In progress', 'Fixed', "Won't do", 'Duplicate'];


/* ---------------------------------------------------------------
   Sheet plumbing
   --------------------------------------------------------------- */

function book_() {
  return SpreadsheetApp.openById(SHEET_ID);
}

function tab_() {
  var ss = book_();
  var sh = ss.getSheetByName(TAB);
  if (!sh) {
    // Reuse a lone empty default tab rather than leaving it behind.
    var only = ss.getSheets();
    if (only.length === 1 && only[0].getLastRow() === 0) {
      sh = only[0].setName(TAB);
    } else {
      sh = ss.insertSheet(TAB);
    }
  }
  if (sh.getLastRow() === 0) {
    sh.getRange(1, 1, 1, HEADERS.length).setValues([HEADERS]);
  }
  return sh;
}

/** Run this once by hand after pasting the script. */
function setup() {
  var sh = tab_();
  var head = sh.getRange(1, 1, 1, HEADERS.length);

  head.setValues([HEADERS])
      .setFontWeight('bold')
      .setBackground('#2f2f2f')
      .setFontColor('#f4f2ec');
  sh.setFrozenRows(1);
  sh.setFrozenColumns(1);

  var widths = [230, 150, 130, 210, 160, 190, 100, 420, 300, 110, 120, 300];
  for (var i = 0; i < widths.length; i++) sh.setColumnWidth(i + 1, widths[i]);

  // Key is an implementation detail — keep it out of the way.
  sh.hideColumns(1);

  var body = sh.getRange(2, 1, Math.max(sh.getMaxRows() - 1, 1), HEADERS.length);
  body.setVerticalAlignment('top').setWrap(true);

  // Status dropdown, defaulted by the rules below rather than forced.
  sh.getRange(2, 10, Math.max(sh.getMaxRows() - 1, 1), 1).setDataValidation(
    SpreadsheetApp.newDataValidation()
      .requireValueInList(STATUSES, true)
      .setAllowInvalid(false)
      .build()
  );

  // Colour the verdict column so the sheet reads at a glance.
  var verdicts = sh.getRange(2, 7, Math.max(sh.getMaxRows() - 1, 1), 1);
  sh.setConditionalFormatRules([
    SpreadsheetApp.newConditionalFormatRule()
      .whenTextEqualTo('Needs work').setBackground('#f6e2cf').setFontColor('#8a4d12')
      .setRanges([verdicts]).build(),
    SpreadsheetApp.newConditionalFormatRule()
      .whenTextEqualTo('Approved').setBackground('#dfeada').setFontColor('#3d5c33')
      .setRanges([verdicts]).build()
  ]);

  SpreadsheetApp.flush();
  return 'Ready — now Deploy → New deployment → Web app.';
}


/**
 * Wipe every review row, keeping the header, formatting and dropdowns.
 * Run it by hand from the editor when a revision goes out and you want
 * the team to review from a clean slate. Reviewers' browsers keep their
 * own copy, so anyone still marked up will re-sync on their next visit —
 * tell them to press "Clear my review" on the dashboard first.
 */
function resetSheet() {
  var sh = tab_();
  var last = sh.getLastRow();
  if (last > 1) sh.deleteRows(2, last - 1);
  SpreadsheetApp.flush();
  return 'Cleared ' + Math.max(last - 1, 0) + ' row(s).';
}


/* ---------------------------------------------------------------
   Pages tab: one row per page, rolled up from Reviews
   --------------------------------------------------------------- */

var SITE      = 'https://sbertini-tgi.github.io/1000WATT-steamboat-web-mockup/';
var MANIFEST  = SITE + 'js/review-manifest.js';
var PAGES_TAB = 'Pages';

var PAGE_HEADERS = [
  'Group', 'Page', 'Title', 'Sections',                        // A–D  from the manifest
  'Reviewed', 'Needs work', 'Open items', 'Awaiting re-review', // E–H  formulas
  'Approved', 'Reviewers', 'Last review', 'Stage',              // I–L  formulas
  'Sign-off owner', 'Signed off', 'NoCo Tribus port',           // M–Q  yours, kept on rebuild
  'Steamboat Tribus port', 'Notes'
];
var PAGE_TEAM_FROM = 13;               // column M onward is the team's
var PORT_STATUSES  = ['Not started', 'In progress', 'Ported', 'Live'];
var STAGES = ['Not started', 'In review', 'Revising', 'Re-review',
              'Ready for sign-off', 'Signed off'];

/**
 * Run by hand. Pulls the page list from the published review manifest,
 * rebuilds the Pages tab and keeps whatever the team typed in M–Q.
 *
 * How a page's stage is worked out (column L), first match wins:
 *   Signed off ......... a date is entered in "Signed off"
 *   Not started ........ no section has a verdict yet
 *   Revising ........... a Needs work item is Open / In progress / blank
 *   Re-review .......... every Needs work item is marked Fixed, waiting
 *                        for the reviewer to look again
 *   In review .......... some sections still have no verdict
 *   Ready for sign-off . every section approved (Won't do / Duplicate
 *                        items don't block)
 */
function buildPagesTab() {
  var manifest = fetchManifest_();
  var ss = book_();
  var sh = ss.getSheetByName(PAGES_TAB) || ss.insertSheet(PAGES_TAB);

  // Keep the team's columns, keyed by page file.
  var kept = {};
  var teamWidth = PAGE_HEADERS.length - PAGE_TEAM_FROM + 1;
  if (sh.getLastRow() > 1) {
    var old = sh.getRange(2, 1, sh.getLastRow() - 1, PAGE_HEADERS.length).getValues();
    for (var i = 0; i < old.length; i++) {
      var cols = old[i].slice(PAGE_TEAM_FROM - 1);
      if (old[i][1] && cols.join('') !== '') kept[String(old[i][1])] = cols;
    }
  }

  sh.clear();
  sh.clearConditionalFormatRules();
  sh.getRange(1, 1, sh.getMaxRows(), sh.getMaxColumns()).clearDataValidations();

  var pages = manifest.pages;
  var n = pages.length;
  var R = function (col) { return TAB + '!$' + col + '$2:$' + col; };
  var blocking = R('G') + '="Needs work", ' + R('J') + '<>"Won\'t do", ' + R('J') + '<>"Duplicate"';

  var rows = [], links = [], team = [];
  for (var p = 0; p < n; p++) {
    var pg = pages[p], r = p + 2, me = R('D') + '=$B' + r;
    rows.push([
      pg.group,
      pg.file,
      pg.title,
      pg.blocks.length,
      '=IFERROR(ROWS(UNIQUE(FILTER(' + R('E') + ', ' + me + ', ' + R('G') + '<>"Comment"))), 0)',
      '=IFERROR(ROWS(UNIQUE(FILTER(' + R('E') + ', ' + me + ', ' + blocking + '))), 0)',
      '=COUNTIFS(' + R('D') + ', $B' + r + ', ' + R('G') + ', "Needs work", ' +
        R('J') + ', "<>Fixed", ' + R('J') + ', "<>Won\'t do", ' + R('J') + ', "<>Duplicate")',
      '=COUNTIFS(' + R('D') + ', $B' + r + ', ' + R('G') + ', "Needs work", ' + R('J') + ', "Fixed")',
      '=E' + r + '-F' + r,
      '=IFERROR(TEXTJOIN(", ", TRUE, UNIQUE(FILTER(' + R('C') + ', ' + me + '))), "")',
      '=IFERROR(MAX(FILTER(' + R('B') + ', ' + me + ')), "")',
      '=IFS(N' + r + '<>"", "Signed off", E' + r + '=0, "Not started", G' + r + '>0, "Revising", ' +
        'H' + r + '>0, "Re-review", E' + r + '<D' + r + ', "In review", TRUE, "Ready for sign-off")'
    ]);
    links.push([SpreadsheetApp.newRichTextValue().setText(pg.file).setLinkUrl(SITE + pg.file).build()]);
    team.push(kept[pg.file] || blanks_(teamWidth));
    delete kept[pg.file];
  }

  // Pages that left the manifest but carry team notes stay at the bottom.
  var orphans = Object.keys(kept);
  for (var o = 0; o < orphans.length; o++) {
    var ro = n + 2 + o;
    rows.push(['(removed)', orphans[o], '', 0, 0, 0, 0, 0, 0, '', '',
               '=IF(N' + ro + '<>"", "Signed off", "Removed from site")']);
    links.push([SpreadsheetApp.newRichTextValue().setText(orphans[o]).build()]);
    team.push(kept[orphans[o]]);
  }
  var total = rows.length;

  // Header, body, links, team columns.
  sh.getRange(1, 1, 1, PAGE_HEADERS.length).setValues([PAGE_HEADERS])
    .setFontWeight('bold').setBackground('#2f2f2f').setFontColor('#f4f2ec').setWrap(true);
  sh.getRange(1, PAGE_TEAM_FROM, 1, teamWidth).setBackground('#5b4a33');
  sh.getRange(2, 1, total, rows[0].length).setValues(rows);
  sh.getRange(2, 2, total, 1).setRichTextValues(links);
  sh.getRange(2, PAGE_TEAM_FROM, total, teamWidth).setValues(team);

  sh.getRange('A1').setNote('Source: review manifest, ' + MANIFEST + ', fetched ' +
    Utilities.formatDate(new Date(), ss.getSpreadsheetTimeZone(), 'yyyy-MM-dd HH:mm z') +
    '. Rebuild with buildPagesTab in Extensions → Apps Script.');
  sh.getRange(1, PAGE_TEAM_FROM).setNote('Columns M–Q are filled in by the team and are kept when the tab is rebuilt.');
  sh.getRange('L1').setNote(
    'Signed off: a date is in Signed off.\n' +
    'Not started: no verdicts yet.\n' +
    'Revising: a Needs work item is still open.\n' +
    'Re-review: every Needs work item is marked Fixed.\n' +
    'In review: some sections have no verdict yet.\n' +
    'Ready for sign-off: every section approved.');

  // Formats and dropdowns.
  sh.getRange(2, 11, total, 1).setNumberFormat('m/d/yyyy');
  sh.getRange(2, 14, total, 1).setNumberFormat('m/d/yyyy').setDataValidation(
    SpreadsheetApp.newDataValidation().requireDate().setAllowInvalid(false).build());
  sh.getRange(2, 15, total, 2).setDataValidation(
    SpreadsheetApp.newDataValidation().requireValueInList(PORT_STATUSES, true).setAllowInvalid(false).build());
  sh.getRange(2, 1, total, PAGE_HEADERS.length).setVerticalAlignment('top');
  sh.getRange(2, 4, total, 6).setHorizontalAlignment('center');

  var widths = [100, 280, 200, 80, 80, 90, 80, 100, 80, 180, 95, 140, 130, 95, 130, 150, 300];
  for (var w = 0; w < widths.length; w++) sh.setColumnWidth(w + 1, widths[w]);
  sh.setFrozenRows(1);
  sh.setFrozenColumns(2);

  // Colour the stage so the tab reads at a glance.
  var stage = sh.getRange(2, 12, total, 1);
  var colours = {
    'Signed off':         ['#c9dcc1', '#2c4a24'],
    'Ready for sign-off': ['#dfeada', '#3d5c33'],
    'Re-review':          ['#e3e8f1', '#34496b'],
    'Revising':           ['#f6e2cf', '#8a4d12'],
    'In review':          ['#f5efd6', '#6b5a1e'],
    'Not started':        ['#eeeeee', '#666666']
  };
  sh.setConditionalFormatRules(Object.keys(colours).map(function (k) {
    return SpreadsheetApp.newConditionalFormatRule().whenTextEqualTo(k)
      .setBackground(colours[k][0]).setFontColor(colours[k][1]).setRanges([stage]).build();
  }));

  // Summary to the right: pages per stage, and section totals.
  var S = 19;  // column S
  var last = total + 1;
  var summary = [['Stage', 'Pages']];
  for (var s = 0; s < STAGES.length; s++) {
    summary.push([STAGES[s], '=COUNTIF($L$2:$L$' + last + ', S' + (s + 2) + ')']);
  }
  var t = STAGES.length + 3;
  summary.push(['', ''], ['Sections', 'Count'],
    ['Total',    '=SUM($D$2:$D$' + last + ')'],
    ['Reviewed', '=SUM($E$2:$E$' + last + ')'],
    ['Approved', '=SUM($I$2:$I$' + last + ')'],
    ['Approved, % of total', '=IF(T' + (t + 1) + '=0, 0, T' + (t + 3) + '/T' + (t + 1) + ')']);
  sh.getRange(1, S, summary.length, 2).setValues(summary);
  sh.getRange(1, S, 1, 2).setFontWeight('bold').setBackground('#2f2f2f').setFontColor('#f4f2ec');
  sh.getRange(t, S, 1, 2).setFontWeight('bold').setBackground('#2f2f2f').setFontColor('#f4f2ec');
  sh.getRange(t + 4, S + 1).setNumberFormat('0.0%');
  sh.setColumnWidth(S - 1, 30);
  sh.setColumnWidth(S, 160);
  sh.setColumnWidth(S + 1, 70);

  SpreadsheetApp.flush();
  return 'Pages tab built: ' + n + ' pages' +
    (orphans.length ? ', ' + orphans.length + ' removed page(s) kept for their notes.' : '.');
}

function blanks_(k) {
  var a = [];
  while (a.length < k) a.push('');
  return a;
}

/** The manifest is a JS file ("window.REVIEW_MANIFEST = {...};"). */
function fetchManifest_() {
  var res = UrlFetchApp.fetch(MANIFEST, { muteHttpExceptions: true });
  if (res.getResponseCode() !== 200) {
    throw new Error('Could not fetch ' + MANIFEST + ' (HTTP ' + res.getResponseCode() + ')');
  }
  var src = res.getContentText();
  return JSON.parse(src.slice(src.indexOf('{'), src.lastIndexOf('}') + 1));
}


/* ---------------------------------------------------------------
   Write: the overlay POSTs here
   --------------------------------------------------------------- */

function doPost(e) {
  var lock = LockService.getScriptLock();
  try {
    // Two reviewers can easily save in the same second.
    lock.waitLock(25000);
  } catch (err) {
    return json_({ ok: false, error: 'busy' });
  }

  try {
    var payload = JSON.parse((e && e.postData && e.postData.contents) || '{}');
    var items = payload.items || [];
    if (!items.length) return json_({ ok: true, written: 0 });

    var sh = tab_();
    var last = sh.getLastRow();

    // Existing keys → row number.
    var index = {};
    if (last > 1) {
      var keys = sh.getRange(2, 1, last - 1, 1).getValues();
      for (var i = 0; i < keys.length; i++) {
        if (keys[i][0]) index[String(keys[i][0])] = i + 2;
      }
    }

    var appended = [], written = 0;
    for (var j = 0; j < items.length; j++) {
      var it = items[j];
      if (!it || !it.page || !it.id) continue;
      var reviewer = String(payload.reviewer || it.reviewer || 'Anonymous').slice(0, 120);
      var key = reviewer + '|' + it.page + '#' + it.id;
      var row = [
        key,
        it.t ? new Date(Number(it.t)) : new Date(),
        reviewer,
        String(it.page),
        String(it.id),
        String(it.label || ''),
        it.v === 'ok' ? 'Approved' : (it.v === 'fix' ? 'Needs work' : 'Comment'),
        String(it.n || ''),
        String(it.url || '')
      ];
      if (index[key]) {
        // Update A..I only — the team's columns are left untouched.
        sh.getRange(index[key], 1, 1, LOCKED_FROM).setValues([row]);
      } else {
        appended.push(row);
        index[key] = -1;   // don't append the same key twice in one batch
      }
      written++;
    }

    if (appended.length) {
      sh.getRange(sh.getLastRow() + 1, 1, appended.length, LOCKED_FROM).setValues(appended);
    }
    SpreadsheetApp.flush();
    return json_({ ok: true, written: written, at: Date.now() });

  } catch (err) {
    return json_({ ok: false, error: String(err) });
  } finally {
    lock.releaseLock();
  }
}


/* ---------------------------------------------------------------
   Read: the overlay and dashboard GET here (JSONP)
   --------------------------------------------------------------- */

function doGet(e) {
  var p = (e && e.parameter) || {};
  try {
    var sh = tab_();
    var last = sh.getLastRow();
    var rows = [];

    if (last > 1) {
      var vals = sh.getRange(2, 1, last - 1, HEADERS.length).getValues();
      for (var i = 0; i < vals.length; i++) {
        var r = vals[i];
        if (!r[0]) continue;
        if (p.reviewer && String(r[2]) !== p.reviewer) continue;
        rows.push({
          key:      String(r[0]),
          t:        r[1] instanceof Date ? r[1].getTime() : Number(r[1]) || 0,
          reviewer: String(r[2]),
          page:     String(r[3]),
          id:       String(r[4]),
          label:    String(r[5]),
          v:        r[6] === 'Approved' ? 'ok' : (r[6] === 'Needs work' ? 'fix' : ''),
          n:        String(r[7] || ''),
          status:   String(r[9] || ''),
          owner:    String(r[10] || '')
        });
      }
    }
    return reply_(p.callback, { ok: true, rows: rows, at: Date.now() });

  } catch (err) {
    return reply_(p.callback, { ok: false, error: String(err) });
  }
}


/* ---------------------------------------------------------------
   Helpers
   --------------------------------------------------------------- */

function json_(obj) {
  return ContentService.createTextOutput(JSON.stringify(obj))
    .setMimeType(ContentService.MimeType.JSON);
}

/** Apps Script cannot answer a CORS preflight, so reads come back as
    JSONP when a callback is supplied. Plain JSON otherwise, which is
    handy for poking the URL in a browser tab. */
function reply_(callback, obj) {
  if (!callback || !/^[A-Za-z_$][\w$]*$/.test(callback)) return json_(obj);
  return ContentService
    .createTextOutput(callback + '(' + JSON.stringify(obj) + ');')
    .setMimeType(ContentService.MimeType.JAVASCRIPT);
}
