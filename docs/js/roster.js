/* All-agents roster (agents.html) — name search plus three dropdowns:
   All Brokers (individuals and teams) / Teams only, last-name initial,
   and language (English matches everyone).
   Typing a name overrides the dropdowns: it searches the whole roster.
   Otherwise every dropdown must match for a tile to show.
   "Clear filters" resets all four fields. */
(function () {
  var grid = document.getElementById('roster-grid');
  if (!grid) return;
  var bar = document.querySelector('.pbar--roster');
  var search = document.getElementById('roster-search');
  var kind = document.getElementById('roster-kind');
  var initial = document.getElementById('roster-initial');
  var lang = document.getElementById('roster-lang');
  var count = document.getElementById('roster-count');
  var empty = document.getElementById('roster-empty');
  var clear = document.getElementById('roster-clear');
  var tiles = Array.prototype.slice.call(grid.querySelectorAll('.agent'));

  function apply() {
    var q = (search && search.value || '').trim().toLowerCase();
    var k = kind ? kind.value : 'all';
    var i = initial ? initial.value : '';
    var l = lang ? lang.value : '';
    var shown = 0;
    tiles.forEach(function (tile) {
      var ok = q
        ? (tile.getAttribute('data-name') || '').toLowerCase().indexOf(q) !== -1
        : (k === 'all' || tile.getAttribute('data-kind') === k) &&
          (!i || tile.getAttribute('data-initial') === i) &&
          (!l || (' ' + tile.getAttribute('data-langs') + ' ').indexOf(' ' + l + ' ') !== -1);
      tile.hidden = !ok;
      if (ok) shown++;
    });
    var noun = !q && k === 'team' ? (shown === 1 ? 'team' : 'teams') : (shown === 1 ? 'broker' : 'brokers');
    if (count) count.textContent = 'Showing ' + shown + ' ' + noun + (q ? ' matching “' + search.value.trim() + '”' : '');
    if (empty) empty.hidden = shown !== 0;
    if (bar) bar.classList.toggle('is-name-search', !!q);
    if (clear) clear.hidden = !(q || k !== 'all' || i || l);
  }

  function reset() {
    if (search) search.value = '';
    if (kind) kind.value = 'all';
    if (initial) initial.value = '';
    if (lang) lang.value = '';
    apply();
    if (search) search.focus();
  }

  [kind, initial, lang].forEach(function (el) { if (el) el.addEventListener('change', apply); });
  if (search) search.addEventListener('input', apply);
  if (clear) clear.addEventListener('click', reset);
  apply();
})();
