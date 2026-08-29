/* The Group — mock interactions: header state, reveals, count-ups, nav */
(function () {
  'use strict';

  /* sticky header: transparent over hero -> solid on scroll */
  var header = document.getElementById('siteHeader');
  function onScroll() {
    if (header) header.classList.toggle('is-solid', window.scrollY > 40);
  }
  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();

  /* mobile nav */
  var nav = document.querySelector('.main-nav');
  var toggle = document.querySelector('.nav-toggle');
  var close = document.querySelector('.nav-close');
  if (toggle && nav) toggle.addEventListener('click', function () { nav.classList.add('is-open'); });
  if (close && nav) close.addEventListener('click', function () { nav.classList.remove('is-open'); });

  /* scroll reveals */
  var io = new IntersectionObserver(function (entries) {
    entries.forEach(function (e) {
      if (e.isIntersecting) {
        e.target.classList.add('is-in');
        io.unobserve(e.target);
      }
    });
  }, { threshold: 0.14, rootMargin: '0px 0px -6% 0px' });
  document.querySelectorAll('[data-reveal], [data-reveal-stagger]').forEach(function (el) { io.observe(el); });

  /* count-up stat numbers: <span data-count="50" data-prefix="" data-suffix="">50</span> */
  var fmt = function (n) { return n.toLocaleString('en-US'); };
  var cio = new IntersectionObserver(function (entries) {
    entries.forEach(function (e) {
      if (!e.isIntersecting) return;
      cio.unobserve(e.target);
      var el = e.target;
      var raw = el.getAttribute('data-count');
      var target = parseFloat(raw);
      var decimals = (raw.split('.')[1] || '').length;
      var prefix = el.getAttribute('data-prefix') || '';
      var suffix = el.getAttribute('data-suffix') || '';
      var dur = 1800, t0 = null;
      function tick(t) {
        if (!t0) t0 = t;
        var p = Math.min((t - t0) / dur, 1);
        var eased = 1 - Math.pow(1 - p, 4);
        var v = target * eased;
        el.textContent = prefix + (decimals ? v.toFixed(decimals) : fmt(Math.round(v))) + suffix;
        if (p < 1) requestAnimationFrame(tick);
      }
      requestAnimationFrame(tick);
    });
  }, { threshold: 0.6 });
  document.querySelectorAll('[data-count]').forEach(function (el) { cio.observe(el); });

  /* hero search is decorative in this mock — route to the buy page */
  document.querySelectorAll('form[data-mock-search]').forEach(function (f) {
    f.addEventListener('submit', function (ev) {
      ev.preventDefault();
      window.location.href = f.getAttribute('data-mock-search');
    });
  });

  /* mock form submit feedback */
  document.querySelectorAll('form[data-mock-form]').forEach(function (f) {
    f.addEventListener('submit', function (ev) {
      ev.preventDefault();
      var btn = f.querySelector('.btn');
      if (btn) { btn.textContent = 'Received — thank you'; btn.disabled = true; }
    });
  });
})();
