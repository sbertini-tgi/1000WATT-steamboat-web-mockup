#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build-community-pages — the eleven community drill-down pages.

Run from the repo root after editing tools/communities.json:

    python3 tools/build-community-pages.py
    python3 tools/review-manifest.py      # relists the pages in review.html

Writes docs/community-<slug>.html for every entry. The copy, map pin and
listing snapshot were lifted from the production pages
(thegrouprealestatess.com/communities/<slug>/); headline, blurb, pull quote
and photo-placeholder label are new for the mockup. A community with no
"search" block (South Routt, as on production) gets no listings section.
"""
import os, json, math, html

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS = os.path.join(ROOT, "docs")
DATA = json.load(open(os.path.join(ROOT, "tools", "communities.json"), encoding="utf-8"))
ALL = DATA["communities"]

def e(s):
    return html.escape(str(s), quote=True)

def money(n):
    return "${:,}".format(n)

def addr(s):
    # production feeds the occasional ALL-CAPS street name ("105 HILLSIDE Drive")
    return " ".join(w.capitalize() if w.isupper() and len(w) > 2 else w for w in s.split())

ARROW = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4"><path d="M5 12h14M13 6l6 6-6 6"/></svg>'

NAV = """    <nav class="nav">
      <div class="nav__brand">
        <a href="index.html"><img class="nav__logo" src="assets/svg/logo.svg" alt="The Group" /></a>
        <span class="nav__loc">Steamboat Springs, CO</span>
      </div>
      <div class="nav__links">
        <a href="index.html#agents">The People</a>
        <a href="index.html#buyers">Buyers Now</a>
        <a href="index.html#life">Lifestyle</a>
        <a href="index.html#guides">How We Work</a>
        <a href="index.html#ready">Search</a>
      </div>
    </nav>"""

FOOTER = """  <footer class="footer footer--home" id="footer" data-review="Footer">
    <div class="footer__box">
      <hr class="footer__rule" />
      <div class="footer__inner">
      <a href="about-the-group-steamboat.html">About Us</a>
      <a href="privacy-policy.html">Privacy</a>
      <a href="contact.html">Contact</a>
      <a href="readme.html">Readme</a>
      </div>
      <hr class="footer__rule" />
      <div class="footer__fine">
        <p class="footer__copy">© 2026 The Group Real Estate LLC. All rights reserved.</p>
        <p class="footer__disc">Information deemed reliable but not guaranteed by the MLS. The data relating to real estate for sale on this web site comes in part from Information and Real Estate Services, LLC under Summit MLS Rules, and is provided for limited non-commercial use. Information is provided exclusively for consumers' personal use and may not be used for any purpose other than to identify prospective properties consumers may be interested in purchasing. Real estate listings held by other brokerage firms are included in this site and detailed information about them includes the name of the listing brokers. Listing broker has attempted to offer accurate data, but buyers are advised to confirm all items. Listing data is updated every 15 minutes or less. Before purchasing investment property be sure to consult with your legal and tax advisor. The Group, Real Estate LLC cannot make any guarantees about return on investment.</p>
      </div>
    </div>
  </footer>"""


def paras_html(ps, indent="          "):
    return "\n".join('%s<p>%s</p>' % (indent, e(p)) for p in ps)


def listing_card(l):
    specs = ["%s Bd" % l["beds"]]
    ba = l["baths"] + (0.5 if l["half"] else 0)
    specs.append(("%g Ba" % ba) if ba else None)
    if l["sqft"]:
        specs.append("{:,} SF".format(l["sqft"]))
    specs = " · ".join(s for s in specs if s)
    rep = "Offered by %s" % l["agent"] + (" · %s" % l["firm"] if l["firm"] else "")
    return ('        <article class="listing"><div class="listing__img ph" data-label="Listing photo"></div>'
            '<div class="listing__body"><span class="listing__price">%s</span><span class="listing__specs">%s</span>'
            '<span class="listing__addr">%s, %s</span><span class="listing__rep">%s</span></div></article>'
            % (money(l["price"]), e(specs), e(addr(l["address"])), e(l["city"]), e(rep)))


def listings_section(c):
    q = c.get("search")
    if not q:
        return ""
    chips = ['Area: %s' % q["area"]]
    if q["min"] >= 1000:
        chips.append("Price: $%sK+" % format(q["min"] // 1000, ","))
    else:
        chips.append("Price")
    chips += ["Beds", "Type: %s" % q["type"] if q.get("type") else "Type"]
    chip_html = "\n".join('        <button class="filter" type="button">%s <span>▾</span></button>' % e(x) for x in chips)
    cards = "\n".join(listing_card(l) for l in c["listings"])
    return """
  <!-- ============================ LISTINGS ============================ -->
  <section class="section bg-cream" id="s-listings" data-review="Listings">
    <div class="container">
      <div class="sec-head">
        <div>
          <p class="eyebrow">For Sale in {name}</p>
          <h2 class="h2">What&rsquo;s on the market now.</h2>
        </div>
        <a class="link-gold" href="property-search.html">View all {name} listings <span>→</span></a>
      </div>
      <div class="searchbar">
        <div class="searchbar__input">
          <svg class="search__icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="11" cy="11" r="7"/><path d="M21 21l-4.3-4.3"/></svg>
          <input type="text" value="{area}" aria-label="Search location or MLS number" />
        </div>
{chips}
        <a class="pill-btn" href="property-search.html">Search <span>→</span></a>
      </div>
      <p class="mls-note"><b>Placeholder view.</b> Live MLS / IDX results connect here in production, pre-filtered the way the current page is (active listings, MLS area &ldquo;{area}&rdquo;). The cards are a snapshot of that page from {snap}, shown without photos.</p>
      <div class="listings">
{cards}
      </div>
    </div>
  </section>
""".format(name=e(c["name"]), area=e(q["area"]), chips=chip_html, cards=cards, snap=e(DATA["snapshot"]))


def nearby(i):
    picks = [ALL[(i + k) % len(ALL)] for k in (1, 2, 3)]
    out = []
    for c in picks:
        out.append('        <a class="comm" href="community-%s.html"><div class="comm__img"><img src="%s" alt="%s" loading="lazy" /></div>'
                   '<div class="comm__body"><h3 class="comm__name">%s</h3><p class="comm__blurb">%s</p>'
                   '<span class="comm__more">Explore %s <span>→</span></span></div></a>'
                   % (c["slug"], e(c["card"]), e(c["name"]), e(c["name"]), e(c["blurb"]), e(c["name"])))
    return "\n".join(out)


def page(i, c):
    ps = c["paras"]
    k = max(1, math.ceil(len(ps) / 2))
    intro, rest = ps[:k], ps[k:]
    lead, intro_body = intro[0], intro[1:]
    maps_q = "%s,%s" % (c["lat"], c["lng"])
    embed = "https://maps.google.com/maps?q=%s&amp;z=%d&amp;output=embed" % (maps_q, c["zoom"])
    gmaps = "https://www.google.com/maps/search/?api=1&amp;query=%s" % maps_q
    rest_html = paras_html(rest, "            ") if rest else ""

    return """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <meta name="robots" content="noindex, nofollow, noarchive, noimageindex" />
  <title>{name} — Communities — The Group, Steamboat Springs</title>
  <meta name="description" content="{blurb}" />
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Marcellus&family=Inter:wght@300;400;500&display=swap" rel="stylesheet" />
  <link rel="stylesheet" href="css/styles.css" />
  <link rel="stylesheet" href="css/guide-page.css" />
  <link rel="stylesheet" href="css/review.css" />
</head>
<body>
  <!-- Generated by tools/build-community-pages.py from tools/communities.json. Edit those, not this. -->

  <!-- ============================ HERO ============================ -->
  <header class="ihero ihero--photo" id="s-hero" data-review="Hero">
    <img class="ihero__bg" src="{hero}" alt="{name}, Steamboat Springs" />
    <div class="ihero__scrim"></div>

{nav}

    <div class="ihero__inner">
      <a class="crumb" href="communities.html"><span>←</span> Communities</a>
      <h1 class="h1">{name}</h1>
      <p class="lede">{blurb}</p>
    </div>
  </header>

  <!-- ============================ OVERVIEW ============================ -->
  <section class="section bg-cream" id="s-overview" data-review="Overview">
    <div class="container">
      <div class="lead-grid">
        <div class="lead-head">
          <p class="eyebrow">Living in {name}</p>
          <h2 class="h2">{headline}</h2>
        </div>
        <div class="prose prose--story">
          <p class="prose__lead">{lead}</p>
{intro}
        </div>
      </div>
    </div>
  </section>

  <!-- ============================ STORY ============================ -->
  <section class="section bg-white" id="s-story" data-review="Story">
    <div class="container">
      <figure class="cquote">
        <blockquote class="pull">&ldquo;{pull}&rdquo;</blockquote>
      </figure>
      <div class="split{split_mod}">
        <div class="split__img ph" data-label="Photo — {photo}"></div>
        <div class="split__copy prose">
{rest}
        </div>
      </div>
    </div>
  </section>

  <!-- ============================ MAP ============================ -->
  <section class="section section--map bg-white" id="s-map" data-review="Map">
    <div class="container">
      <div class="sec-head">
        <div>
          <p class="eyebrow">On the Map</p>
          <h2 class="h2">Where {name} sits.</h2>
        </div>
        <a class="link-gold" href="{gmaps}" target="_blank" rel="noopener">Open in Google Maps <span>→</span></a>
      </div>
      <div class="map map--wide">
        <iframe src="{embed}" title="Map of {name}, Steamboat Springs" loading="lazy" referrerpolicy="no-referrer-when-downgrade"></iframe>
      </div>
    </div>
  </section>
{listings}
  <!-- ============================ NEARBY ============================ -->
  <section class="section bg-white" id="s-nearby" data-review="Nearby">
    <div class="container">
      <div class="sec-head">
        <div>
          <p class="eyebrow">Keep Exploring</p>
          <h2 class="h2">More corners of the valley.</h2>
        </div>
        <a class="link-gold" href="communities.html">All communities <span>→</span></a>
      </div>
      <div class="commgrid">
{nearby}
      </div>
    </div>
  </section>

  <!-- ============================ CTA ============================ -->
  <section class="band" id="s-find-your-corner" data-review="Find Your Corner">
    <img class="band__bg" src="assets/img/topo-5.svg" alt="Topographic contour placeholder" />
    <div class="band__scrim"></div>
    <div class="container">
      <p class="eyebrow eyebrow--bright">{name}</p>
      <h2 class="h2">Know the neighborhood. Then find the home.</h2>
      <p class="lede">Talk to a broker who lives where you&rsquo;re looking &mdash; they&rsquo;ll tell you what the listings won&rsquo;t.</p>
      <div class="band__actions">
        <a class="pill-btn pill-btn--light" href="contact.html">Talk to a broker <span>→</span></a>
        <a class="link-gold link-gold--bright" href="property-search.html">Search homes <span>→</span></a>
      </div>
    </div>
  </section>

  <!-- ============================ FOOTER ============================ -->
{footer}

  <!-- Review overlay: add ?review=1 to any page to switch it on -->
  <script src="js/review-manifest.js" defer></script>
  <script src="js/review.js" defer></script>

</body>
</html>
""".format(
        name=e(c["name"]), blurb=e(c["blurb"]), hero=e(c["hero"]), nav=NAV,
        headline=e(c["headline"]), lead=e(lead), intro=paras_html(intro_body),
        pull=e(c["pull"]), photo=e(c["photo"]), rest=rest_html,
        split_mod=" split--rev" if i % 2 else "",
        embed=embed, gmaps=gmaps, listings=listings_section(c),
        nearby=nearby(i), footer=FOOTER)


if __name__ == "__main__":
    for i, c in enumerate(ALL):
        path = os.path.join(DOCS, "community-%s.html" % c["slug"])
        open(path, "w", encoding="utf-8").write(page(i, c))
        print("wrote", os.path.relpath(path, ROOT))
