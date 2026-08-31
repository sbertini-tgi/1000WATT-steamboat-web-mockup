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
