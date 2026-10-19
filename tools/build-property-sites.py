#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build-property-sites — the stand-alone single-property sites.

Run from the repo root after editing tools/property-sites.json:

    python3 tools/build-property-sites.py
    python3 tools/review-manifest.py

Writes docs/<prefix>.html for each site, where <prefix> is the production
subdomain (1240hawksnestlanena.thegrouprealestatess.com -> 1240hawksnestlanena.html).
The listing record was lifted from each production site's embedded MLS data;
photos are saved under docs/assets/listings/sites/<prefix>/ (NN.jpg full,
NN-t.jpg thumbnail). Production's section order is kept — hero, description,
broker, details, video, photos, map, request info — restyled in 1000WATT.
"""
import os, re, json, html
from datetime import datetime, timezone, timedelta

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS = os.path.join(ROOT, "docs")
DATA = json.load(open(os.path.join(ROOT, "tools", "property-sites.json"), encoding="utf-8"))

def _num(v):
    # the MLS record sends many numbers as strings ("1730.0")
    if isinstance(v, str) and re.fullmatch(r"-?\d+(\.\d+)?", v):
        f = float(v)
        return int(f) if f.is_integer() else f
    return v
for _s in DATA["sites"]:
    for _g in _s["facts"].values():
        for _k in list(_g):
            _g[_k] = _num(_g[_k])

# Display names where the MLS street line reads badly
STREET = {"24agrizzlyct24a": "24A Grizzly Court"}
GROUP_COUNT = 9            # photos shown before "Show all"
MT = timezone(timedelta(hours=-6))   # Mountain Daylight Time for open-house times

def e(s):
    return html.escape(str(s), quote=True)

def money(n):
    return "${:,}".format(int(n))

def phone(p):
    d = re.sub(r"\D", "", p or "")
    return ("%s.%s.%s" % (d[:3], d[3:6], d[6:]), "+1" + d) if len(d) == 10 else (p or "", "")

def words(v):
    """'SteamRoom' -> 'Steam Room'; lists and booleans made readable."""
    if isinstance(v, bool):
        return "Yes" if v else "No"
    if isinstance(v, float):
        v = int(v) if v.is_integer() else v
    if isinstance(v, int):
        return "{:,}".format(v) if v >= 10000 else str(v)
    s = str(v)
    s = ", ".join(re.sub(r"(?<=[a-z])(?=[A-Z])", " ", part.strip()) for part in s.split(","))
    return s.replace("Mountain(s)", "Mountains").replace("( s)", "(s)")

def date(iso, fmt="%b %-d, %Y"):
    return datetime.strptime(iso[:10], "%Y-%m-%d").strftime(fmt) if iso else ""

ARROW = '<span aria-hidden="true">&rarr;</span>'


def specs(s):
    f, out = s["facts"], []
    st, ch = f["structure"], f["characteristics"]
    if st.get("bedrooms_total"):
        out.append((st["bedrooms_total"], "Bedrooms"))
    if st.get("bathrooms_total_integer"):
        out.append((st["bathrooms_total_integer"], "Bathrooms"))
    if st.get("living_area") and s["type"] == "Residential":
        out.append(("{:,}".format(int(st["living_area"])), "Square feet"))
    if ch.get("lot_size_acres"):
        out.append((("%.2f" % ch["lot_size_acres"]).rstrip("0").rstrip("."), "Acres"))
    if f["tax"].get("zoning_description") and s["type"] != "Residential":
        out.append((f["tax"]["zoning_description"], "Zoning"))
    if st.get("year_built") and s["type"] == "Residential":
        out.append((st["year_built"], "Year built"))
    if st.get("garage_spaces"):
        out.append((int(st["garage_spaces"]), "Car garage"))
    return out


def detail_groups(s):
    f = s["facts"]
    st, ch, ut, hoa, tax, eq, biz = (f["structure"], f["characteristics"], f["utility"], f["hoa"],
                                     f["tax"], f["equipment"], f["business"])
    kind = s["type"] + (" — " + s["subtype"] if s["subtype"] else "")
    G = []
    def grp(name, rows):
        rows = [(k, v) for k, v in rows if v not in (None, "", [], {})]
        if rows:
            G.append((name, rows))
    grp("Essential", [
        ("Property type", kind),
        ("Status", s["status"]),
        ("MLS #", s["mls"]),
        ("List price", money(s["price"])),
        ("Square feet", "{:,}".format(int(st["living_area"])) if st.get("living_area") and s["type"] == "Residential" else None),
        ("Bedrooms", st.get("bedrooms_total")),
        ("Bathrooms (full)", st.get("bathrooms_full")),
        ("Bathrooms (¾)", st.get("bathrooms_three_quarter")),
        ("Bathrooms (half)", st.get("bathrooms_half")),
        ("Lot size", "%s acres" % words(ch["lot_size_acres"]) if ch.get("lot_size_acres") else None),
        ("Business type", biz.get("business_type")),
    ])
    grp("Interior", [
        ("Interior features", st.get("interior_features") and words(st["interior_features"])),
        ("Flooring", st.get("flooring")),
        ("Fireplace", st.get("fireplace_features") and ("%s · %s" % (st["fireplaces_total"], st["fireplace_features"]) if st.get("fireplaces_total") else st["fireplace_features"])),
        ("Appliances", eq.get("appliances") and words(eq["appliances"])),
        ("Spa", ch.get("spa_features") and words(ch["spa_features"])),
        ("Furnished", ch.get("furnished")),
        ("Levels", st.get("levels")),
        ("Basement", st.get("basement")),
        ("Accessibility", st.get("accessibility_features")),
        ("Doors", st.get("door_features")),
    ])
    grp("Utilities", [
        ("Heating", st.get("heating")),
        ("Cooling", st.get("cooling") and words(st["cooling"])),
        ("Utilities", ut.get("utilities")),
        ("Electric", ut.get("electric") and words(ut["electric"])),
        ("Water", ut.get("water_source")),
        ("Sewer", ut.get("sewer")),
    ])
    grp("Construction", [
        ("Year built", st.get("year_built") if s["type"] == "Residential" else None),
        ("Condition", st.get("property_condition")),
        ("Style", st.get("architectural_style")),
        ("Materials", st.get("construction_materials")),
        ("Roof", st.get("roof") if s["type"] == "Residential" else None),
    ])
    grp("Exterior", [
        ("Garage", st.get("garage_spaces") and "%d spaces · attached" % st["garage_spaces"] if st.get("attached_garage_y_n") else st.get("garage_spaces")),
        ("Parking", st.get("parking_features")),
        ("Patio / porch", st.get("patio_and_porch_features")),
        ("Lot features", ch.get("lot_features") and words(ch["lot_features"])),
        ("View", ch.get("view") and words(ch["view"])),
        ("Road", " · ".join(x for x in (ch.get("road_surface_type"), ch.get("road_responsibility")) if x)),
        ("Current use", ch.get("current_use")),
        ("Fencing", ch.get("fencing")),
        ("Horses", ch.get("horse_amenities")),
        ("Road frontage", ch.get("road_frontage_type")),
        ("Community", ch.get("community_features") and words(ch["community_features"]).replace("Trails Paths", "Trails / paths")),
    ])
    grp("Location", [
        ("Subdivision", s["subdivision"].title() if s.get("subdivision") and s["subdivision"] not in ("OTHER", "OUT OF AREA") else None),
        ("MLS area", s["area"] if s.get("area") not in (None, "Other") else None),
        ("County", s.get("county")),
        ("Legal", tax.get("tax_legal_description")),
    ])
    sc = s.get("schools") or {}
    grp("Schools", [
        ("Elementary", sc.get("elementary_school")),
        ("Middle", sc.get("middle_or_junior_school")),
        ("High", sc.get("high_school")),
    ])
    grp("Financial", [
        ("Annual taxes", tax.get("tax_annual_amount") and "%s (%s)" % (money(tax["tax_annual_amount"]), tax.get("tax_year", "")) if tax.get("tax_annual_amount") else None),
        ("HOA", ("%s / %s" % (money(hoa["association_fee"]), hoa.get("association_fee_frequency", "").lower())) if hoa.get("association_fee") else ("None" if "association_fee" in hoa else None)),
        ("Pets allowed", hoa.get("pets_allowed")),
        ("Zoning", tax.get("zoning_description")),
        ("Parcel #", tax.get("parcel_number") if str(tax.get("parcel_number", "1")) != "1" else None),
    ])
    grp("Dates", [
        ("On market", date(s.get("onMarket"))),
        ("Days on market", s.get("dom")),
        ("Original price", money(s["originalPrice"]) if s["originalPrice"] != s["price"] else None),
    ])
    return G


def page(s):
    slug = s["slug"]
    street = STREET.get(slug, s["street"])
    city_line = "%s, %s %s" % (s["city"], s["state"], s["zip"])
    a = s["agent"]
    tel_txt, tel_href = phone(a["phone"])
    a_photo = "assets/agents/%s.jpg" % a["slug"] if a.get("slug") else ""
    a_href = a.get("profile") or "agent-%s.html" % a["slug"] if a.get("profile") or (a.get("slug") and os.path.exists(os.path.join(DOCS, "agent-%s.html" % a["slug"]))) \
        else "https://thegrouprealestatess.com/agents/%s/" % a.get("slug", "")
    first = a["name"].split()[0]
    photos = s["photos"]
    base = "assets/listings/sites/%s/" % slug
    hero = base + "%02d.jpg" % photos[0]["n"]

    # remarks -> paragraphs: MLS remarks come as one block; break every ~3 sentences
    sents = re.split(r"(?<=[.!?])\s+(?=[A-Z])", s["remarks"])
    lead, rest = sents[0], sents[1:]
    paras, cur = [], []
    for x in rest:
        cur.append(x)
        if len(" ".join(cur)) > 340:
            paras.append(" ".join(cur)); cur = []
    if cur:
        paras.append(" ".join(cur))

    sp = specs(s)
    spec_html = "\n".join('        <div class="spec"><div class="spec__v">%s</div><div class="spec__k">%s</div></div>' % (e(v), e(k)) for v, k in sp)
    chips = " &middot; ".join("%s %s" % (e(v), e(k.lower() if k not in ("Zoning",) else k)) for v, k in sp[:4])

    # open houses still to come (relative to the snapshot date)
    snap = datetime.strptime(DATA["snapshot"], "%Y-%m-%d").replace(tzinfo=MT)
    upcoming, upcoming_bar = [], []
    for o in s.get("openHouses") or []:
        st_ = datetime.fromisoformat(o["start"].replace("Z", "+00:00")).astimezone(MT)
        en_ = datetime.fromisoformat(o["end"].replace("Z", "+00:00")).astimezone(MT)
        if st_ >= snap:
            upcoming.append("%s · %s–%s" % (st_.strftime("%a, %b %-d"), st_.strftime("%-I:%M"), en_.strftime("%-I:%M %p")))
            upcoming_bar.append((st_, en_))
    open_html = ""
    def hm(t):
        return t.strftime("%-I %p") if t.minute == 0 else t.strftime("%-I:%M %p")
    def span(a_, b_):
        a_s, b_s = hm(a_), hm(b_)
        return (a_s[:-3] if a_s[-2:] == b_s[-2:] else a_s) + "–" + b_s
    def gcal(a_, b_):
        z = lambda t: t.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        q = "action=TEMPLATE&text=" + ("Open house: %s" % street).replace(" ", "+") + "&dates=%s/%s" % (z(a_), z(b_)) + \
            "&location=" + ("%s, %s" % (street, city_line)).replace(" ", "+").replace(",", "%2C")
        return "https://calendar.google.com/calendar/render?" + q
    ohbar = ""
    if upcoming_bar:
        items = []
        for k, (a_, b_) in enumerate(upcoming_bar):
            items.append('<li class="ohbar__date%s"><time datetime="%s">%s · %s</time><a class="ohbar__cal" href="%s" target="_blank" rel="noopener" aria-label="Add %s to calendar">+ Calendar</a></li>'
                         % (" is-more" if k else "", a_.isoformat(), a_.strftime("%a, %b %-d"), span(a_, b_), e(gcal(a_, b_)), a_.strftime("%A, %B %-d")))
        more = ('<button class="ohbar__more" type="button" aria-expanded="false" aria-controls="ohbar-list">+%d more <span aria-hidden="true">▾</span></button>' % (len(items) - 1)) if len(items) > 1 else ""
        ohbar = """  <!-- ============================ OPEN HOUSE BAR ============================ -->
  <aside class="ohbar" id="s-open-house" data-review="Open house" aria-label="Open house">
    <div class="ohbar__inner">
      <span class="ohbar__k"><span class="ohbar__dot" aria-hidden="true"></span>Open house</span>
      <ul class="ohbar__list" id="ohbar-list">%s</ul>
      %s
      <a class="ohbar__link" href="https://www.google.com/maps/dir/?api=1&amp;destination=%s,%s" target="_blank" rel="noopener">Directions <span aria-hidden="true">&rarr;</span></a>
    </div>
  </aside>
""" % ("".join(items), more, s["lat"], s["lng"])
    if upcoming:
        open_html = '<div class="sps-open"><span class="mini-k">Open house</span>%s</div>' % "".join("<b>%s</b>" % e(u) for u in upcoming)

    gal = []
    for i, ph in enumerate(photos):
        cap = ph["caption"] or "%s — photo %d" % (street, i + 1)
        gal.append('        <button class="sps-ph%s" type="button" data-full="%s%02d.jpg" data-i="%d" aria-label="Open photo %d of %d">'
                   '<img src="%s%02d-t.jpg" alt="%s" loading="lazy" /></button>'
                   % (" is-more" if i >= GROUP_COUNT else "", base, ph["n"], i, i + 1, len(photos), base, ph["n"], e(cap)))
    more_btn = ('<button class="pill-btn sps-more" type="button" id="sps-more">Show all %d photos %s</button>' % (len(photos), ARROW)
                if len(photos) > GROUP_COUNT else "")

    groups = detail_groups(s)
    groups_html = "\n".join(
        '        <div class="sps-group">\n          <p class="eyebrow">%s</p>\n          <table class="dtable">\n%s\n          </table>\n        </div>'
        % (e(name), "\n".join("            <tr><td>%s</td><td>%s</td></tr>" % (e(k), e(words(v) if not isinstance(v, str) else v)) for k, v in rows))
        for name, rows in groups)

    hist = s.get("priceHistory") or []
    hist_html = ""
    if s["originalPrice"] != s["price"] or len(hist) > 1:
        items = ['<li>%s <span>Listed %s</span></li>' % (money(s["originalPrice"]), e(date(s["onMarket"])))]
        items += ['<li>%s <span>%s</span></li>' % (money(h["price"]), e(date(h["date"]))) for h in hist if h["price"] != s["originalPrice"]]
        hist_html = """
        <div class="sps-group">
          <p class="eyebrow">Price history</p>
          <ul class="pricehist">
            %s
          </ul>
        </div>""" % "\n            ".join(items)

    tour = ""
    is3d = "view-3d" in (s.get("virtualTour") or "") or "matterport" in (s.get("virtualTour") or "")
    tour_label = "3D Tour" if is3d else "Video"
    if s.get("virtualTour"):
        tour = """
  <!-- ============================ VIDEO / 3D TOUR ============================ -->
  <section class="band sps-tour" id="tour" data-review="{label}">
    <img class="band__bg" src="{img}" alt="" />
    <div class="band__scrim"></div>
    <div class="container">
      <p class="eyebrow eyebrow--bright">{label}</p>
      <h2 class="h2">{title}</h2>
      <p class="lede">{lede}</p>
      <div class="band__actions"><a class="pill-btn pill-btn--solid" href="{url}" target="_blank" rel="noopener">{cta} <span aria-hidden="true">&#8599;</span></a></div>
    </div>
  </section>
""".format(img=e(base + "%02d.jpg" % photos[min(2, len(photos) - 1)]["n"]), url=e(s["virtualTour"]), label=tour_label,
           title="Walk through it before you fly in." if is3d else "See it the way it feels.",
           lede=("Every room of %s, in a self-guided 3D tour." if is3d else "The video tour of %s, from the listing team.") % e(street),
           cta="Open the 3D tour" if is3d else "Watch the video")

    maps_q = "%s,%s" % (s["lat"], s["lng"])
    nav_links = [("overview", "Overview"), ("details", "Details")] + ([("tour", tour_label)] if tour else []) + \
                [("photos", "Photos"), ("location", "Location")]
    nav_html = "\n".join('        <a href="#%s">%s</a>' % (h, t) for h, t in nav_links)
    ptype = s["subtype"] if s["type"] == "Residential" and s["subtype"] else {"Land": "Land", "Commercial Sale": "Commercial"}.get(s["type"], s["type"])

    return """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <meta name="robots" content="noindex, nofollow, noarchive, noimageindex" />
  <title>{street}, {city_line} — The Group</title>
  <meta name="description" content="{price} · {chips_plain}. {city_line}. Listed by {agent} of The Group." />
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Marcellus&family=Inter:wght@300;400;500&display=swap" rel="stylesheet" />
  <link rel="stylesheet" href="css/styles.css" />
  <link rel="stylesheet" href="css/guide-page.css" />
  <link rel="stylesheet" href="css/property-site.css" />
  <link rel="stylesheet" href="css/review.css" />
</head>
<body class="sps">
{ohbar}  <!-- Generated by tools/build-property-sites.py from tools/property-sites.json. Edit those, not this.
       Stand-alone property site; production: {source} -->

  <!-- ============================ HERO ============================ -->
  <header class="sps-hero" id="s-hero" data-review="Hero">
    <img class="sps-hero__bg" src="{hero}" alt="{street}, {city}" />
    <div class="sps-hero__scrim"></div>
    <nav class="nav sps-nav" aria-label="On this page">
      <div class="nav__brand">
        <img class="nav__logo" src="assets/svg/logo.svg" alt="The Group" />
        <span class="nav__loc">{street}</span>
      </div>
      <div class="nav__links">
{nav_html}
        <a class="sps-nav__cta" href="#contact">Request info</a>
      </div>
    </nav>
    <div class="sps-hero__inner">
      <div>
        <p class="eyebrow eyebrow--bright">{status} &middot; {ptype}</p>
        <h1 class="h1">{street}</h1>
        <p class="sps-hero__city">{city_line}</p>
      </div>
      <div class="sps-hero__right">
        <div class="sps-hero__price">{price}</div>
        <p class="sps-hero__chips">{chips}</p>
      </div>
    </div>
  </header>

  <!-- ============================ OVERVIEW ============================ -->
  <section class="section bg-cream" id="overview" data-review="Overview">
    <div class="container">
      <div class="specstrip specstrip--sps">
{spec_html}
      </div>
      <div class="propcols sps-cols">
        <div>
          <p class="eyebrow">The Property</p>
          <div class="prose prose--story sps-remarks">
            <p class="prose__lead">{lead}</p>
{paras}
          </div>
        </div>
        <aside class="agentcard sps-agent">
          <div class="agentcard__top">
            <div class="agentcard__photo">{agent_img}</div>
            <div>
              <span class="agentcard__k">Offered by</span>
              <a class="agentcard__name" href="{a_href}">{agent}</a>
              <span class="agentcard__role">{office_label}</span>
            </div>
          </div>
          <ul class="sps-agent__lines">
            <li><span class="mini-k">Phone</span><a href="tel:{tel_href}">{tel}</a></li>
            <li><span class="mini-k">Email</span><a href="mailto:{email}">{email}</a></li>
          </ul>
          {open_html}
          <a class="pill-btn sps-agent__cta" href="#contact">Request more info {arrow}</a>
        </aside>
      </div>
    </div>
  </section>

  <!-- ============================ DETAILS ============================ -->
  <section class="section bg-white" id="details" data-review="Property details">
    <div class="container">
      <div class="sec-head">
        <div>
          <p class="eyebrow">Property Details</p>
          <h2 class="h2">The particulars.</h2>
        </div>
        <span class="sps-src">{board} &middot; MLS #{mls}</span>
      </div>
      <div class="sps-groups">
{groups}{hist}
      </div>
    </div>
  </section>
{tour}
  <!-- ============================ PHOTOS ============================ -->
  <section class="section bg-cream" id="photos" data-review="Photos">
    <div class="container">
      <div class="sec-head">
        <div>
          <p class="eyebrow">Photos</p>
          <h2 class="h2">{nphotos_word}</h2>
        </div>
      </div>
      <div class="sps-gallery{gal_mod}" id="sps-gallery">
{gallery}
      </div>
      {more_btn}
    </div>
  </section>

  <!-- ============================ MAP ============================ -->
  <section class="section bg-white" id="location" data-review="Location">
    <div class="container">
      <div class="sec-head">
        <div>
          <p class="eyebrow">Location</p>
          <h2 class="h2">{city}, {county} County.</h2>
        </div>
        <a class="link-gold" href="https://www.google.com/maps/dir/?api=1&amp;destination={maps_q}" target="_blank" rel="noopener">Get directions <span>&rarr;</span></a>
      </div>
      <div class="map map--wide">
        <iframe src="https://maps.google.com/maps?q={maps_q}&amp;z=14&amp;output=embed" title="Map of {street}" loading="lazy" referrerpolicy="no-referrer-when-downgrade"></iframe>
      </div>
      {directions}
    </div>
  </section>

  <!-- ============================ REQUEST INFO ============================ -->
  <section class="section bg-dark sps-contact" id="contact" data-review="Request info">
    <div class="container">
      <div class="lead-grid">
        <div class="lead-head">
          <p class="eyebrow">Request More Info</p>
          <h2 class="h2">Ask {first} anything about {street}.</h2>
          <p class="lede">Showings, disclosures, HOA documents, or what the neighbors are like &mdash; {first} will get back to you directly.</p>
          <p class="sps-contact__tel"><a href="tel:{tel_href}">{tel}</a><br /><a href="mailto:{email}">{email}</a></p>
        </div>
        <form class="form sps-form" onsubmit="return false">
          <div class="field"><label for="f-first">First name *</label><input id="f-first" type="text" autocomplete="given-name" /></div>
          <div class="field"><label for="f-last">Last name *</label><input id="f-last" type="text" autocomplete="family-name" /></div>
          <div class="field"><label for="f-phone">Phone</label><input id="f-phone" type="tel" autocomplete="tel" /></div>
          <div class="field"><label for="f-email">Email *</label><input id="f-email" type="email" autocomplete="email" /></div>
          <div class="field field--full"><label for="f-msg">Message</label><textarea id="f-msg" placeholder="I&rsquo;d like to know more about {street}&hellip;"></textarea></div>
          <div class="form__submit"><button class="pill-btn pill-btn--solid" type="submit">Send {arrow}</button></div>
        </form>
      </div>
    </div>
  </section>

  <!-- ============================ FOOTER ============================ -->
  <footer class="footer footer--home" id="footer" data-review="Footer">
    <div class="footer__box">
      <hr class="footer__rule" />
      <div class="footer__inner">
      <a href="index.html">{brand}</a>
      <a href="property-search.html">More listings</a>
      <a href="contact.html">Contact</a>
      </div>
      <hr class="footer__rule" />
      <div class="footer__fine">
        <p class="footer__copy">&copy; 2026 The Group Real Estate LLC. All rights reserved. Listing courtesy of {agent}, {office}.</p>
        <p class="footer__disc">Information deemed reliable but not guaranteed by the MLS. Listing data from {board}, MLS #{mls}, as of {snap}. Buyers are advised to confirm all items.</p>
      </div>
    </div>
  </footer>

  <!-- Lightbox -->
  <div class="sps-lb" id="sps-lb" hidden role="dialog" aria-modal="true" aria-label="Photo viewer">
    <button class="sps-lb__close" type="button" aria-label="Close">&times;</button>
    <button class="sps-lb__nav sps-lb__prev" type="button" aria-label="Previous photo">&larr;</button>
    <figure class="sps-lb__fig"><img alt="" /><figcaption></figcaption></figure>
    <button class="sps-lb__nav sps-lb__next" type="button" aria-label="Next photo">&rarr;</button>
  </div>

  <script src="js/property-site.js" defer></script>
  <!-- Review overlay: add ?review=1 to any page to switch it on -->
  <script src="js/review-manifest.js" defer></script>
  <script src="js/review.js" defer></script>
</body>
</html>
""".format(
        street=e(street), city=e(s["city"]), county=e(s.get("county") or ""), city_line=e(city_line),
        price=money(s["price"]), status=e(s["status"]), ptype=e(ptype), hero=e(hero), source=e(s["sourceUrl"]),
        chips=chips, chips_plain=re.sub(r"&middot;", "·", chips), nav_html=nav_html,
        spec_html=spec_html, lead=e(lead),
        paras="\n".join("            <p>%s</p>" % e(p) for p in paras),
        agent_img='<img src="%s" alt="%s" />' % (e(a_photo), e(a["name"])) if a_photo else "",
        a_href=e(a_href), agent=e(a["name"]), office_label=e(a.get("officeLabel") or "The Group"), office=e(a["office"] or "The Group"),
        tel=e(tel_txt), tel_href=e(tel_href), email=e(a["email"]), first=e(first),
        open_html=open_html, ohbar=ohbar, arrow=ARROW, board=e(s["board"] or "MLS"), mls=e(s["mls"]),
        groups=groups_html, hist=hist_html, tour=tour,
        nphotos_word="%d photographs." % len(photos) if len(photos) > 3 else "A closer look.",
        gal_mod=" sps-gallery--few" if len(photos) <= 3 else "",
        gallery="\n".join(gal), more_btn=more_btn, maps_q=maps_q,
        directions='<p class="sps-directions"><span class="mini-k">Directions</span>%s</p>' % e(s["directions"]) if s.get("directions") else "",
        snap=e(DATA["snapshot"]),
        brand="The Group &middot; Steamboat Springs" if s["state"] == "CO" and "Steamboat" in (a.get("officeLabel") or "Steamboat") else "The Group Real Estate")


if __name__ == "__main__":
    for s in DATA["sites"]:
        path = os.path.join(DOCS, "%s.html" % s["slug"])
        open(path, "w", encoding="utf-8").write(page(s))
        print("wrote", os.path.relpath(path, ROOT))
