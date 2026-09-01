/* =========================================================
   AGENT SITE — the two interactive blocks.

   Both are progressive: with JS off, the listing tabs show
   the first status set and the calculator shows its fields.
   ========================================================= */
(function () {
  'use strict';

  /* ---------- Listing status tabs (For Sale / Pending / Sold) ---------- */
  document.querySelectorAll('[data-tabs]').forEach(function (bar) {
    var tabs = Array.prototype.slice.call(bar.querySelectorAll('.tab'));
    tabs.forEach(function (tab) {
      tab.addEventListener('click', function () {
        tabs.forEach(function (t) {
          var panel = document.getElementById(t.getAttribute('aria-controls'));
          var on = t === tab;
          t.classList.toggle('is-active', on);
          t.setAttribute('aria-selected', on ? 'true' : 'false');
          if (panel) panel.hidden = !on;
        });
      });
    });
  });

  /* ---------- Mortgage calculator ---------- */
  var USD = new Intl.NumberFormat('en-US', {
    style: 'currency', currency: 'USD', maximumFractionDigits: 0
  });

  function num(el) {
    return parseFloat(String(el ? el.value : '').replace(/[^0-9.]/g, '')) || 0;
  }

  document.querySelectorAll('[data-calc]').forEach(function (form) {
    var f = function (sel) { return form.querySelector(sel); };
    var price = f('[data-calc-price]'), down = f('[data-calc-down]'),
        rate  = f('[data-calc-rate]'),  term = f('[data-calc-term]');
    var pay = f('[data-calc-pay]'), loanOut = f('[data-calc-loan]'),
        dpOut = f('[data-calc-dp]'),  intOut = f('[data-calc-int]');

    function run() {
      var p = num(price), dp = p * (num(down) / 100), loan = Math.max(p - dp, 0);
      var n = Math.max(num(term), 1) * 12, i = num(rate) / 100 / 12;
      var m = i > 0
        ? loan * i / (1 - Math.pow(1 + i, -n))
        : loan / n;

      pay.textContent = loan > 0 ? USD.format(m) : '—';
      loanOut.textContent = USD.format(loan);
      dpOut.textContent = USD.format(dp);
      intOut.textContent = USD.format(Math.max(m * n - loan, 0));
    }

    [price, down, rate, term].forEach(function (el) {
      if (el) el.addEventListener('input', run);
    });
    run();
  });
})();
