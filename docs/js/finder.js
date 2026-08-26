/* SEARCH section — "When You're Ready To Look"
   Option pills drive a single display line: hovering an option previews its
   blurb in place of the old search field; the display links to the active
   (or hovered) option. Progressive enhancement — the option links work on
   their own if this script never runs. */
(function () {
  var finder = document.getElementById('finder');
  if (!finder) return;
  var opts = Array.prototype.slice.call(finder.querySelectorAll('.finder-opt'));
  var display = document.getElementById('finderDisplay');
  var text = document.getElementById('finderText');
  if (!display || !text || !opts.length) return;

  var active = finder.querySelector('.finder-opt.is-active') || opts[0];

  function apply(opt) {
    text.textContent = opt.getAttribute('data-blurb') || '';
    display.setAttribute('href', opt.getAttribute('href'));
    if (opt.hasAttribute('target')) { display.setAttribute('target', opt.getAttribute('target')); }
    else { display.removeAttribute('target'); }
    if (opt.hasAttribute('rel')) { display.setAttribute('rel', opt.getAttribute('rel')); }
    else { display.removeAttribute('rel'); }
  }

  function setActive(opt) {
    opts.forEach(function (o) { o.classList.remove('is-active'); });
    opt.classList.add('is-active');
    active = opt;
    apply(opt);
  }

  apply(active);

  opts.forEach(function (opt) {
    opt.addEventListener('mouseenter', function () { apply(opt); });
    opt.addEventListener('focus', function () { apply(opt); });
    opt.addEventListener('mouseleave', function () { apply(active); });
    opt.addEventListener('blur', function () { apply(active); });
    opt.addEventListener('click', function () { setActive(opt); });
  });
})();
