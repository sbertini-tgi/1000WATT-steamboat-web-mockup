/* Blog — in-page category filter (no separate category pages). */
(function () {
  var bar = document.getElementById('blogFilter');
  if (!bar) return;
  var posts = Array.prototype.slice.call(document.querySelectorAll('.post'));
  var count = document.getElementById('blogCount');
  var empty = document.getElementById('blogEmpty');

  function apply(cat) {
    var n = 0;
    posts.forEach(function (p) {
      var cats = (p.getAttribute('data-cats') || '').split(' ');
      var show = cat === 'all' || cats.indexOf(cat) >= 0;
      p.hidden = !show;
      if (show) n++;
    });
    if (count) count.textContent = n + (n === 1 ? ' story' : ' stories');
    if (empty) empty.hidden = n !== 0;
  }

  bar.addEventListener('click', function (e) {
    var b = e.target.closest('button');
    if (!b) return;
    Array.prototype.forEach.call(bar.querySelectorAll('button'), function (x) { x.classList.remove('is-active'); });
    b.classList.add('is-active');
    apply(b.getAttribute('data-cat'));
  });

  apply('all');
})();
