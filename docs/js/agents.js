/* Agent directory — season filtering + name search.
   Filters the .agent tiles by the active season pill and the search text.
   Both conditions must match for a tile to show. */
(function () {
  var grid = document.getElementById('agent-grid');
  var seasons = document.getElementById('seasons');
  var search = document.getElementById('agent-search');
  var empty = document.getElementById('agents-empty');
  if (!grid || !seasons) return;

  var tiles = Array.prototype.slice.call(grid.querySelectorAll('.agent'));
  var activeSeason = 'all';

  function apply() {
    var q = (search && search.value ? search.value : '').trim().toLowerCase();
    var shown = 0;

    tiles.forEach(function (tile) {
      var tileSeasons = (tile.getAttribute('data-seasons') || '').split(/\s+/);
      var name = (tile.getAttribute('data-name') || '').toLowerCase();

      var seasonOk = activeSeason === 'all' || tileSeasons.indexOf(activeSeason) !== -1;
      var nameOk = q === '' || name.indexOf(q) !== -1;
      var show = seasonOk && nameOk;

      tile.hidden = !show;
      if (show) shown++;
    });

    if (empty) empty.hidden = shown !== 0;
  }

  // Season pills
  seasons.addEventListener('click', function (e) {
    var btn = e.target.closest('.season');
    if (!btn) return;
    activeSeason = btn.getAttribute('data-season') || 'all';
    seasons.querySelectorAll('.season').forEach(function (b) {
      b.classList.toggle('is-active', b === btn);
    });
    apply();
  });

  // Name search
  if (search) search.addEventListener('input', apply);
})();
