/* Stand-alone property sites — "Show all photos" and a simple lightbox
   (click a photo; arrows / Esc on the keyboard). */
(function () {
  var gallery = document.getElementById('sps-gallery');
  var more = document.getElementById('sps-more');
  var lb = document.getElementById('sps-lb');
  if (!gallery || !lb) return;

  if (more) more.addEventListener('click', function () {
    gallery.classList.add('is-open');
    more.remove();
  });

  var shots = Array.prototype.slice.call(gallery.querySelectorAll('.sps-ph'));
  var img = lb.querySelector('img');
  var cap = lb.querySelector('figcaption');
  var current = 0, opener = null;

  function show(i) {
    current = (i + shots.length) % shots.length;
    var b = shots[current];
    img.src = b.getAttribute('data-full');
    img.alt = b.querySelector('img').alt;
    cap.textContent = (current + 1) + ' / ' + shots.length + (/photo \d+$/.test(img.alt) ? '' : ' · ' + img.alt);
  }
  function open(i) {
    opener = document.activeElement;
    show(i);
    lb.hidden = false;
    document.body.style.overflow = 'hidden';
    lb.querySelector('.sps-lb__close').focus();
  }
  function close() {
    lb.hidden = true;
    document.body.style.overflow = '';
    if (opener) opener.focus();
  }

  shots.forEach(function (b, i) { b.addEventListener('click', function () { open(i); }); });
  lb.querySelector('.sps-lb__close').addEventListener('click', close);
  lb.querySelector('.sps-lb__prev').addEventListener('click', function () { show(current - 1); });
  lb.querySelector('.sps-lb__next').addEventListener('click', function () { show(current + 1); });
  lb.addEventListener('click', function (e) { if (e.target === lb) close(); });
  document.addEventListener('keydown', function (e) {
    if (lb.hidden) return;
    if (e.key === 'Escape') close();
    else if (e.key === 'ArrowLeft') show(current - 1);
    else if (e.key === 'ArrowRight') show(current + 1);
  });
})();

/* Open-house bar: "+N more" reveals the later dates on small screens. */
(function () {
  var bar = document.querySelector('.ohbar');
  var btn = bar && bar.querySelector('.ohbar__more');
  if (!btn) return;
  var label = btn.innerHTML;
  btn.addEventListener('click', function () {
    var open = bar.classList.toggle('is-open');
    btn.setAttribute('aria-expanded', open ? 'true' : 'false');
    btn.innerHTML = open ? 'Fewer <span aria-hidden="true">▴</span>' : label;
  });
})();
