/* =========================================================
   REVIEW OVERLAY  —  section-by-section sign-off for the team.

   Turn it on by adding ?review=1 to any page. Once on it stays on
   (stored in this browser) until "Exit review" is clicked, so the
   reviewer can click around the whole site without losing it.

   Notes live in localStorage under one key, on one origin, so a
   reviewer's marks follow them across all pages. Nothing is sent
   anywhere until they press "Email my review" or "Copy all".

   Exposes window.TGReview for review.html (the dashboard) to reuse.
   ========================================================= */
(function () {
  'use strict';

  /* ---- Where "Email my review" is addressed. Blank = reviewer
          picks their own recipient. -------------------------------- */
  var MAIL_TO = 'sbertini@thegroupinc.com';

  /* ---- Shared Google Sheet.  Paste the Apps Script web-app /exec URL
          here (see tools/review-endpoint.gs). While it is blank the
          overlay works exactly as before: notes stay in the browser and
          go out by email. Once it is set, every mark also syncs to the
          team sheet and the dashboard can show everyone's review. ---- */
  var ENDPOINT = 'https://script.google.com/macros/s/AKfycbzOPmBTqeBCVv-Li_vuivta0fhwQ2z8ExSjRsfZlIbAlzPI9wXvVS79_4Wa_G4zaAKi/exec';

  var KEY = 'tg-review:v1';
  var MANIFEST = window.REVIEW_MANIFEST || { pages: [] };

  /* ---------- storage ---------- */
  function load() {
    var d = { on: false, reviewer: '', items: {}, sent: 0, out: {} };
    try {
      var raw = localStorage.getItem(KEY);
      if (raw) {
        var p = JSON.parse(raw);
        if (p && typeof p === 'object') {
          d.on = !!p.on; d.reviewer = p.reviewer || '';
          d.items = p.items || {}; d.sent = p.sent || 0;
          d.out = p.out || {};
        }
      }
    } catch (e) { /* private window, blocked storage — carry on empty */ }
    return d;
  }
  function save(d) {
    try { localStorage.setItem(KEY, JSON.stringify(d)); } catch (e) {}
  }

  /* ---------- which page are we on ---------- */
  function pageKey() {
    var path = location.pathname;
    var p = /\/$/.test(path) || path === '' ? path + 'index.html' : path;
    var best = '';
    MANIFEST.pages.forEach(function (pg) {
      if (p.length >= pg.file.length &&
          p.slice(-(pg.file.length + 1)) === '/' + pg.file &&
          pg.file.length > best.length) best = pg.file;
    });
    return best || p.split('/').pop() || 'index.html';
  }
  function siteRoot() {
    var file = pageKey();
    var i = location.pathname.lastIndexOf(file);
    return location.origin + (i > -1 ? location.pathname.slice(0, i) : '/');
  }

  /* ---------- digest ---------- */
  var VERDICT = { ok: 'APPROVED', fix: 'NEEDS WORK' };

  function titleFor(file) {
    for (var i = 0; i < MANIFEST.pages.length; i++) {
      if (MANIFEST.pages[i].file === file) return MANIFEST.pages[i].title;
    }
    return file;
  }
  function labelFor(file, id) {
    for (var i = 0; i < MANIFEST.pages.length; i++) {
      if (MANIFEST.pages[i].file !== file) continue;
      var bs = MANIFEST.pages[i].blocks;
      for (var j = 0; j < bs.length; j++) if (bs[j].id === id) return bs[j].label;
    }
    return id;
  }

  function digest(state) {
    var d = state || load();
    var root = siteRoot();
    var byPage = {};
    Object.keys(d.items).forEach(function (k) {
      var it = d.items[k];
      if (!it || (!it.v && !(it.n || '').trim())) return;
      var cut = k.indexOf('#');
      var file = k.slice(0, cut), id = k.slice(cut + 1);
      (byPage[file] = byPage[file] || []).push({ id: id, v: it.v, n: (it.n || '').trim() });
    });

    var order = MANIFEST.pages.map(function (p) { return p.file; });
    var files = Object.keys(byPage).sort(function (a, b) {
      var ia = order.indexOf(a), ib = order.indexOf(b);
      return (ia < 0 ? 99 : ia) - (ib < 0 ? 99 : ib);
    });

    var out = ['# The Group — Steamboat mockup review', ''];
    out.push('Reviewer: ' + (d.reviewer || '(unnamed)'));
    out.push('Date: ' + new Date().toLocaleString());
    var n = files.reduce(function (a, f) { return a + byPage[f].length; }, 0);
    out.push('Sections marked: ' + n);
    out.push('');

    if (!n) { out.push('_No sections marked yet._'); return out.join('\n'); }

    files.forEach(function (file) {
      out.push('## ' + titleFor(file) + '  (' + file + ')');
      var ids = MANIFEST.pages.filter(function (p) { return p.file === file; })[0];
      ids = ids ? ids.blocks.map(function (b) { return b.id; }) : [];
      byPage[file].sort(function (a, b) { return ids.indexOf(a.id) - ids.indexOf(b.id); });
      byPage[file].forEach(function (it) {
        out.push('- [' + (VERDICT[it.v] || 'COMMENT') + '] ' + labelFor(file, it.id));
        if (it.n) it.n.split('\n').forEach(function (line) { out.push('      ' + line); });
        out.push('      ' + root + file + '#' + it.id);
      });
      out.push('');
    });
    return out.join('\n');
  }

  function counts(state, file) {
    var d = state || load(), ok = 0, fix = 0, noted = 0;
    Object.keys(d.items).forEach(function (k) {
      if (file && k.slice(0, k.indexOf('#')) !== file) return;
      var it = d.items[k];
      if (!it) return;
      if (it.v === 'ok') ok++;
      else if (it.v === 'fix') fix++;
      if ((it.n || '').trim()) noted++;
    });
    return { ok: ok, fix: fix, noted: noted };
  }

  function unsentCount(state) {
    var d = state || load(), n = 0;
    Object.keys(d.items).forEach(function (k) {
      var it = d.items[k];
      if (it && it.t && it.t > (d.sent || 0)) n++;
    });
    return n;
  }

  /* ---------- clipboard + mail ---------- */
  function copy(text) {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      return navigator.clipboard.writeText(text);
    }
    return new Promise(function (res, rej) {
      try {
        var ta = document.createElement('textarea');
        ta.value = text;
        ta.style.cssText = 'position:fixed;top:-2000px;left:-2000px';
        document.body.appendChild(ta); ta.select();
        document.execCommand('copy'); document.body.removeChild(ta); res();
      } catch (e) { rej(e); }
    });
  }

  function markSent() { var d = load(); d.sent = Date.now(); save(d); }

  /* Mail clients choke on very long mailto: bodies, so past a safe
     length we put the review on the clipboard and send a short note. */
  function mail(toast) {
    var d = load();
    var text = digest(d);
    var subj = 'Steamboat mockup review — ' + (d.reviewer || 'feedback');
    var url = 'mailto:' + encodeURIComponent(MAIL_TO) +
              '?subject=' + encodeURIComponent(subj) + '&body=' + encodeURIComponent(text);
    if (url.length < 1900) {
      markSent();
      window.location.href = url;
      if (toast) toast('Opening your email — the review is in the message body.');
      return;
    }
    copy(text).then(function () {
      markSent();
      window.location.href = 'mailto:' + encodeURIComponent(MAIL_TO) +
        '?subject=' + encodeURIComponent(subj) +
        '&body=' + encodeURIComponent('(Review copied to your clipboard — paste it here with Cmd/Ctrl-V.)');
      if (toast) toast('Review copied. Paste it into the email that just opened.');
    })['catch'](function () {
      if (toast) toast('Could not copy automatically — use "Copy all" instead.');
    });
  }

  /* =========================================================
     Sync to the shared Google Sheet.

     Apps Script cannot answer a CORS preflight, so this writes
     fire-and-forget (no-cors POST, which the browser sends without a
     preflight) and then reads the sheet back over JSONP to confirm the
     row actually landed. Anything unconfirmed stays in the outbox and
     is retried, so a dropped connection or a closed laptop does not
     lose a note. localStorage remains the source of truth locally.
     ========================================================= */
  var sync = (function () {
    var inFlight = false, timer = null, poll = null;
    var last = { at: 0, ok: null };

    function enabled() { return !!ENDPOINT; }

    /* JSONP: a <script> tag is not subject to CORS, unlike fetch. */
    function jsonp(params, cb) {
      var name = 'rvcb' + Math.random().toString(36).slice(2);
      var s = document.createElement('script');
      var done = false, timeout;
      function cleanup() {
        clearTimeout(timeout);
        try { delete window[name]; } catch (e) { window[name] = undefined; }
        if (s.parentNode) s.parentNode.removeChild(s);
      }
      window[name] = function (data) { done = true; cleanup(); cb(null, data); };
      s.onerror = function () { if (!done) { cleanup(); cb(new Error('network')); } };
      timeout = setTimeout(function () { if (!done) { cleanup(); cb(new Error('timeout')); } }, 25000);
      var q = ['callback=' + name];
      Object.keys(params || {}).forEach(function (k) {
        q.push(encodeURIComponent(k) + '=' + encodeURIComponent(params[k]));
      });
      s.src = ENDPOINT + (ENDPOINT.indexOf('?') > -1 ? '&' : '?') + q.join('&');
      document.head.appendChild(s);
    }

    function pending(d) { return Object.keys((d || load()).out || {}).length; }

    /* An unnamed reviewer would land in the sheet as "Anonymous" and be
       impossible to follow up with, so hold the outbox until they say
       who they are. */
    function blocked(d) { return !(d || load()).reviewer.trim(); }

    function payloadFor(d, keys) {
      var root = siteRoot();
      return keys.map(function (k) {
        var cut = k.indexOf('#'), page = k.slice(0, cut), id = k.slice(cut + 1);
        var it = d.items[k] || { v: '', n: '', t: Date.now() };
        return {
          page: page, id: id, label: labelFor(page, id),
          v: it.v || '', n: it.n || '', t: it.t || Date.now(),
          url: root + page + '#' + id
        };
      });
    }

    function flush(cb) {
      var d = load();
      if (!enabled() || inFlight || blocked(d)) { cb && cb(null, 0); return; }
      var keys = Object.keys(d.out || {});
      if (!keys.length) { cb && cb(null, 0); return; }
      if (navigator.onLine === false) { cb && cb(new Error('offline'), 0); return; }

      inFlight = true;
      emit();
      var body = JSON.stringify({ reviewer: d.reviewer, items: payloadFor(d, keys) });

      fetch(ENDPOINT, {
        method: 'POST', mode: 'no-cors', cache: 'no-store',
        headers: { 'Content-Type': 'text/plain;charset=utf-8' },
        body: body
      }).then(function () {
        /* The response is opaque, so confirm by reading the sheet. */
        setTimeout(function () { confirm_(keys, cb); }, 700);
      })['catch'](function (err) {
        inFlight = false; last = { at: Date.now(), ok: false };
        emit(); cb && cb(err, 0);
      });
    }

    function confirm_(keys, cb) {
      var d = load();
      jsonp({ reviewer: d.reviewer }, function (err, res) {
        inFlight = false;
        if (err || !res || !res.ok) {
          last = { at: Date.now(), ok: false }; emit(); cb && cb(err || new Error('bad reply'), 0);
          return;
        }
        var seen = {};
        (res.rows || []).forEach(function (r) { seen[r.page + '#' + r.id] = r; });

        var now = load(), cleared = 0;
        keys.forEach(function (k) {
          var mine = now.items[k], theirs = seen[k];
          if (!theirs) return;
          var want = mine ? (mine.t || 0) : 0;
          /* Sheets round-trips the timestamp through a Date; allow a
             second of slack rather than demanding an exact match. */
          if (!mine || theirs.t >= want - 1000) { delete now.out[k]; cleared++; }
        });
        save(now);
        last = { at: Date.now(), ok: true };
        emit(); cb && cb(null, cleared);
      });
    }

    /** Everyone's rows, for the dashboard. */
    function pull(cb) {
      if (!enabled()) { cb(new Error('no endpoint')); return; }
      jsonp({}, function (err, res) {
        if (err) return cb(err);
        if (!res || !res.ok) return cb(new Error(res && res.error || 'bad reply'));
        cb(null, res.rows || []);
      });
    }

    function queue(key) {
      var d = load();
      d.out = d.out || {};
      d.out[key] = 1;
      save(d);
      emit();
      clearTimeout(timer);
      timer = setTimeout(function () { flush(); }, 1500);
    }

    var listeners = [];
    function emit() { listeners.forEach(function (f) { try { f(status()); } catch (e) {} }); }
    function onChange(f) { listeners.push(f); }

    function status() {
      var d = load();
      return {
        enabled: enabled(), pending: pending(d), blocked: blocked(d),
        busy: inFlight, ok: last.ok, at: last.at
      };
    }

    function start() {
      if (!enabled()) return;
      flush();
      clearInterval(poll);
      poll = setInterval(function () { if (pending()) flush(); }, 30000);
      window.addEventListener('online', function () { flush(); });
      document.addEventListener('visibilitychange', function () {
        if (!document.hidden && pending()) flush();
      });
    }

    return { enabled: enabled, flush: flush, pull: pull, queue: queue,
             pending: pending, status: status, onChange: onChange, start: start };
  })();

  var API = {
    load: load, save: save, digest: digest, counts: counts, unsentCount: unsentCount,
    copy: copy, mail: mail, markSent: markSent, pageKey: pageKey, siteRoot: siteRoot,
    manifest: MANIFEST, MAIL_TO: MAIL_TO, endpoint: ENDPOINT, sync: sync,
    labelFor: labelFor, titleFor: titleFor,
    set: function (file, id, patch) {
      var d = load(), k = file + '#' + id;
      var it = d.items[k] || { v: '', n: '' };
      if ('v' in patch) it.v = patch.v;
      if ('n' in patch) it.n = patch.n;
      it.t = Date.now();
      if (!it.v && !(it.n || '').trim()) delete d.items[k]; else d.items[k] = it;
      save(d);
      sync.queue(k);
      return d;
    },
    clearAll: function () {
      var d = load(), keys = Object.keys(d.items);
      d.items = {}; d.sent = 0; d.out = {};
      /* If the sheet is live, push the clears too — otherwise the
         reviewer wipes their browser and their old rows live on. */
      if (sync.enabled()) keys.forEach(function (k) { d.out[k] = 1; });
      save(d);
      if (sync.enabled()) sync.flush();
      return d;
    },
    setOn: function (on) { var d = load(); d.on = !!on; save(d); return d; }
  };
  window.TGReview = API;
  sync.start();

  /* =========================================================
     Overlay — only mounts on pages that have reviewable blocks.
     ========================================================= */
  function mount() {
    var blocks = [].slice.call(document.querySelectorAll('[data-review]'));
    if (!blocks.length) return;

    var state = load();
    var q = new URLSearchParams(location.search);
    if (q.has('review')) {
      state.on = q.get('review') !== '0';
      save(state);
    }
    if (!state.on) return;

    var FILE = pageKey();
    document.documentElement.classList.add('rv-on');

    /* ---- badges ---- */
    var badges = [];
    blocks.forEach(function (el, i) {
      el.classList.add('rv-block');
      if (!el.id) el.id = 'rv-block-' + (i + 1);
      var b = document.createElement('button');
      b.type = 'button';
      b.className = 'rv-badge';
      b.setAttribute('aria-label', 'Review section: ' + el.getAttribute('data-review'));
      b.innerHTML = '<span class="rv-badge__dot"></span>' +
                    '<span class="rv-badge__n">§' + (i + 1) + '</span> ' +
                    esc(el.getAttribute('data-review'));
      b.addEventListener('click', function (ev) { ev.preventDefault(); open(i); });
      b.addEventListener('mouseenter', function () { el.classList.add('is-target'); });
      b.addEventListener('mouseleave', function () { el.classList.remove('is-target'); });
      el.appendChild(b);
      badges.push(b);
    });

    function esc(s) {
      return String(s == null ? '' : s).replace(/[&<>"]/g, function (c) {
        return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c];
      });
    }

    /* ---- toolbar ---- */
    var bar = el('div', 'rv-bar');
    bar.innerHTML =
      '<span class="rv-bar__brand">Review mode</span>' +
      '<input class="rv-who" type="text" placeholder="Your name" aria-label="Your name" />' +
      '<span class="rv-bar__stat" data-rv-stat></span>' +
      '<button class="rv-btn rv-btn--go" data-rv="mail">Email my review</button>' +
      '<button class="rv-btn" data-rv="copy">Copy all</button>' +
      '<a class="rv-btn" data-rv="dash" href="#">Dashboard</a>' +
      '<button class="rv-btn rv-btn--quiet" data-rv="off">Exit</button>';
    document.body.appendChild(bar);

    var scrim = el('div', 'rv-scrim');
    var drawer = el('aside', 'rv-drawer');
    drawer.setAttribute('role', 'dialog');
    drawer.setAttribute('aria-label', 'Section review');
    drawer.innerHTML =
      '<div class="rv-drawer__head">' +
        '<button class="rv-close" type="button" aria-label="Close">×</button>' +
        '<p class="rv-drawer__k" data-rv-k></p>' +
        '<h2 class="rv-drawer__title" data-rv-title></h2>' +
        '<code class="rv-drawer__id" data-rv-id></code>' +
      '</div>' +
      '<div class="rv-drawer__body">' +
        '<div class="rv-verdicts">' +
          '<button class="rv-verdict" type="button" data-v="ok"  aria-pressed="false">✓ Approve</button>' +
          '<button class="rv-verdict" type="button" data-v="fix" aria-pressed="false">✎ Needs work</button>' +
        '</div>' +
        '<label class="rv-label" for="rv-note">Comment</label>' +
        '<textarea class="rv-note" id="rv-note" placeholder="What should change here?"></textarea>' +
        '<p class="rv-saved" data-rv-saved>Saved automatically in this browser.</p>' +
        '<p class="rv-label" style="margin-bottom:8px">Link to this section</p>' +
        '<button class="rv-btn" type="button" data-rv="link">Copy section link</button>' +
      '</div>' +
      '<div class="rv-drawer__foot">' +
        '<span class="rv-step">' +
          '<button class="rv-btn rv-btn--quiet" type="button" data-rv="prev">← Prev</button>' +
          '<span data-rv-step></span>' +
          '<button class="rv-btn rv-btn--quiet" type="button" data-rv="next">Next →</button>' +
        '</span>' +
        '<button class="rv-btn rv-btn--go" type="button" data-rv="done">Done</button>' +
      '</div>';
    document.body.appendChild(scrim);
    document.body.appendChild(drawer);

    var toast = el('div', 'rv-toast');
    document.body.appendChild(toast);

    function el(tag, cls) { var n = document.createElement(tag); n.className = cls; return n; }
    function $(sel, root) { return (root || document).querySelector(sel); }

    var who = $('.rv-who', bar);
    var noteEl = $('.rv-note', drawer);
    var stepEl = $('[data-rv-step]', drawer);
    var savedEl = $('[data-rv-saved]', drawer);
    var current = -1, toastTimer = null, saveTimer = null;

    who.value = state.reviewer || '';
    who.addEventListener('input', function () {
      var d = load(); d.reviewer = who.value; save(d);
    });

    $('[data-rv="dash"]', bar).setAttribute('href', rel('review.html'));

    function rel(file) {
      var depth = FILE.split('/').length - 1;
      return (depth ? '../'.repeat(depth) : '') + file;
    }

    function say(msg) {
      toast.textContent = msg;
      toast.classList.add('is-open');
      clearTimeout(toastTimer);
      toastTimer = setTimeout(function () { toast.classList.remove('is-open'); }, 4200);
    }

    function syncBit() {
      var s = sync.status();
      if (!s.enabled) return '';
      if (s.blocked)  return ' &middot; <b>add your name to sync</b>';
      if (s.busy)     return ' &middot; <span class="rv-sync">saving&hellip;</span>';
      if (s.pending)  return ' &middot; <b>' + s.pending + ' waiting to sync</b>';
      if (s.ok === false) return ' &middot; <b>sync failed &mdash; will retry</b>';
      if (s.ok) return ' &middot; <span class="rv-sync is-ok">saved to the team sheet</span>';
      return '';
    }

    function refresh() {
      var d = load();
      var c = counts(d, FILE);
      var todo = blocks.length - c.ok - c.fix;
      /* With the sheet live the email is a courtesy, not the delivery
         mechanism, so the "unsent" nudge only applies without it. */
      var unsent = sync.enabled() ? 0 : unsentCount(d);
      $('[data-rv-stat]', bar).innerHTML =
        '<i>' + c.ok + ' approved</i> &middot; <u>' + c.fix + ' need work</u> &middot; ' +
        '<b>' + todo + '</b> to go on this page' +
        (unsent ? ' &middot; <b>' + unsent + ' unsent</b>' : '') +
        syncBit();
      $('[data-rv="mail"]', bar).classList.toggle('is-nudge', unsent > 0);
      blocks.forEach(function (b, i) {
        var it = d.items[FILE + '#' + b.id] || {};
        badges[i].setAttribute('data-v', it.v || '');
        var has = badges[i].querySelector('.rv-badge__note');
        if ((it.n || '').trim() && !has) {
          var s = document.createElement('span');
          s.className = 'rv-badge__note'; s.textContent = '✎';
          badges[i].appendChild(s);
        } else if (!(it.n || '').trim() && has) { has.remove(); }
      });
    }

    function open(i) {
      current = i;
      var block = blocks[i];
      var d = load();
      var it = d.items[FILE + '#' + block.id] || {};
      $('[data-rv-k]', drawer).textContent = titleFor(FILE);
      $('[data-rv-title]', drawer).textContent = block.getAttribute('data-review');
      $('[data-rv-id]', drawer).textContent = FILE + '#' + block.id;
      noteEl.value = it.n || '';
      [].forEach.call(drawer.querySelectorAll('.rv-verdict'), function (b) {
        b.setAttribute('aria-pressed', String(b.getAttribute('data-v') === it.v));
      });
      stepEl.textContent = (i + 1) + ' of ' + blocks.length;
      savedEl.classList.remove('is-on');
      drawer.classList.add('is-open');
      scrim.classList.add('is-open');
      /* Put the top of the section just below the viewport top rather than
         centring it — sections here are often taller than the screen, and
         the reviewer wants to see where the section starts. */
      var calm = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
      var top = Math.max(0, block.getBoundingClientRect().top + window.pageYOffset - 78);
      try { window.scrollTo({ top: top, behavior: calm ? 'auto' : 'smooth' }); }
      catch (err) { window.scrollTo(0, top); }
      setTimeout(function () { noteEl.focus({ preventScroll: true }); }, 280);
    }

    function close() {
      drawer.classList.remove('is-open');
      scrim.classList.remove('is-open');
      current = -1;
      refresh();
    }

    function put(patch) {
      if (current < 0) return;
      API.set(FILE, blocks[current].id, patch);
      savedEl.textContent = 'Saved.';
      savedEl.classList.add('is-on');
      refresh();
    }

    noteEl.addEventListener('input', function () {
      clearTimeout(saveTimer);
      savedEl.textContent = 'Saving…';
      savedEl.classList.remove('is-on');
      saveTimer = setTimeout(function () { put({ n: noteEl.value }); }, 420);
    });

    [].forEach.call(drawer.querySelectorAll('.rv-verdict'), function (b) {
      b.addEventListener('click', function () {
        var pressed = b.getAttribute('aria-pressed') === 'true';
        var v = pressed ? '' : b.getAttribute('data-v');
        [].forEach.call(drawer.querySelectorAll('.rv-verdict'), function (o) {
          o.setAttribute('aria-pressed', String(!pressed && o === b));
        });
        put({ v: v });
      });
    });

    drawer.addEventListener('click', function (e) {
      var t = e.target.closest('[data-rv], .rv-close');
      if (!t) return;
      var a = t.getAttribute('data-rv');
      if (t.classList.contains('rv-close') || a === 'done') close();
      else if (a === 'prev' && current > 0) open(current - 1);
      else if (a === 'next' && current < blocks.length - 1) open(current + 1);
      else if (a === 'link') {
        copy(siteRoot() + FILE + '#' + blocks[current].id)
          .then(function () { say('Section link copied.'); })
          ['catch'](function () { say('Could not copy the link.'); });
      }
    });

    bar.addEventListener('click', function (e) {
      var t = e.target.closest('[data-rv]');
      if (!t) return;
      var a = t.getAttribute('data-rv');
      if (a === 'off') {
        API.setOn(false);
        location.href = location.pathname + location.hash;
      } else if (a === 'copy') {
        copy(digest()).then(function () { markSent(); refresh(); say('Full review copied to your clipboard.'); })
          ['catch'](function () { say('Could not copy — try "Email my review".'); });
      } else if (a === 'mail') {
        mail(say);
        setTimeout(refresh, 400);
      }
    });

    sync.onChange(function () { refresh(); });

    scrim.addEventListener('click', close);
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && current > -1) close();
    });

    /* Deep link: /page.html?review=1#s-agents opens that section. */
    if (location.hash) {
      var want = location.hash.slice(1);
      blocks.forEach(function (b, i) { if (b.id === want) setTimeout(function () { open(i); }, 420); });
    }

    /* Another tab edited the same review — keep the badges honest. */
    window.addEventListener('storage', function (e) { if (e.key === KEY) refresh(); });

    refresh();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', mount);
  } else { mount(); }
})();
