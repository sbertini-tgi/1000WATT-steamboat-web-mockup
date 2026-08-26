/* LIFESTYLE strip — hovering a tile updates the "No. 0X · place" meta line and
   the vertical label, matching the reference. Static default is tile 01. */
(function () {
  var strip = document.getElementById('lifeStrip');
  var meta = document.getElementById('lifeMeta');
  var vlabel = document.getElementById('lifeVlabel');
  if (!strip || !meta || !vlabel) return;
  var tiles = Array.prototype.slice.call(strip.querySelectorAll('.life-tile'));
  if (!tiles.length) return;
  var def = tiles[0];

  function apply(t) {
    meta.textContent = 'No. ' + t.getAttribute('data-no') + ' · ' + t.getAttribute('data-place');
    vlabel.textContent = t.getAttribute('data-label');
  }

  tiles.forEach(function (t) {
    t.setAttribute('tabindex', '0');
    t.addEventListener('mouseenter', function () { apply(t); });
    t.addEventListener('focus', function () { apply(t); });
  });
  strip.addEventListener('mouseleave', function () { apply(def); });
})();
