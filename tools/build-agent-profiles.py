#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build-agent-profiles — emit the brokerage agent profile pages for the three
agents who also have a solo-site mockup.

    python3 tools/build-agent-profiles.py

Output is plain static HTML in the exact shape of the hand-written
docs/agent-dean-laird.html, so tools/review-manifest.py treats these pages
like their siblings. Dean, Martin and Jon stay hand-written; only the three
listed in AGENTS below are generated, because they share the extra "Solo site"
section that links into docs/<agent>/.

Bios and figures come from each agent's profile page on thegrouprealestatess.com.
Listing cards carry an optional `href`, which turns the card into a link with a
"View listing" affordance — that is how a card reaches a property detail page
inside the agent's solo site.

Safe to re-run: it overwrites the three pages from the data below.
"""
import os

DOCS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs")

NAV = '''    <nav class="nav">
      <div class="nav__brand">
        <a href="index.html"><img class="nav__logo" src="assets/svg/logo.svg" alt="The Group" /></a>
        <span class="nav__loc">Steamboat Springs, CO</span>
      </div>
      <div class="nav__links">
        <a href="index.html#agents">The People</a>
        <a href="index.html#buyers">Buyers Now</a>
        <a href="index.html#life">Lifestyle</a>
        <a href="index.html#guides">How We Work</a>
        <a href="property-search.html">Search</a>
      </div>
    </nav>'''

FOOTER = '''  <!-- ============================ FOOTER ============================ -->
  <footer class="footer footer--home" id="footer" data-review="Footer">
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
        <p class="footer__copy">&copy; 2026 The Group Real Estate LLC. All rights reserved.</p>
        <p class="footer__disc">Information deemed reliable but not guaranteed by the MLS. The data relating to real estate for sale on this web site comes in part from Information and Real Estate Services, LLC under Summit MLS Rules, and is provided for limited non-commercial use. Information is provided exclusively for consumers' personal use and may not be used for any purpose other than to identify prospective properties consumers may be interested in purchasing. Real estate listings held by other brokerage firms are included in this site and detailed information about them includes the name of the listing brokers. Listing broker has attempted to offer accurate data, but buyers are advised to confirm all items. Listing data is updated every 15 minutes or less. Before purchasing investment property be sure to consult with your legal and tax advisor. The Group, Real Estate LLC cannot make any guarantees about return on investment.</p>
      </div>
    </div>
  </footer>

  <!-- Review overlay: add ?review=1 to any page to switch it on -->
  <script src="js/review-manifest.js" defer></script>
  <script src="js/review.js" defer></script>

</body>
</html>
'''

CHIP = {"Active": "listing__chip", "Pending": "listing__chip listing__chip--pending",
        "Sold": "listing__chip listing__chip--sold"}


def listing(x, sold=False):
    cls = "listing listing--sold" if sold else "listing"
    specs = (f'\n            <span class="listing__specs">{x["specs"]}</span>'
             if x.get("specs") else "")
    # A card with an href becomes a link and gains the "View listing"
    # affordance, the same way agent-martin-dragnev.html links its Skyview card.
    tag, attrs, go = "article", "", ""
    if x.get("href"):
        tag = "a"
        attrs = f' href="{x["href"]}"'
        go = ('\n            <span class="listing__go">View listing '
              '<span aria-hidden="true">&rarr;</span></span>')
    return f'''        <{tag} class="{cls}"{attrs}>
          <div class="listing__img"><span class="{CHIP[x["status"]]}">{x["status"]}</span><img src="{x["img"]}" alt="{x.get("alt", x["addr"])}" loading="lazy" /></div>
          <div class="listing__body">
            <span class="listing__price">{x["price"]}</span>{specs}
            <span class="listing__addr">{x["addr"]}</span>
            <span class="listing__rep">{x["rep"]}</span>{go}
          </div>
        </{tag}>'''


def page(a):
    facts = "\n".join(
        f'            <li><span class="agentfacts__k">{k}</span><span class="agentfacts__v">{v}</span></li>'
        for k, v in a["facts"])
    about = "\n".join(f"          <p>{p}</p>" for p in a["about"])
    creds = "\n".join(f'            <li><b>{k}</b><span>{v}</span></li>' for k, v in a["creds"])
    solo_cards = "\n".join(
        f'''        <a class="pub" href="{c["href"]}">
          <p class="pub__k">{c["k"]}</p>
          <h3 class="pub__title">{c["title"]}</h3>
          <p class="pub__desc">{c["desc"]}</p>
          <span class="pub__more">Open <span>&rarr;</span></span>
        </a>''' for c in a["solo_cards"])
    actives = "\n".join(listing(x) for x in a["active"])
    solds = "\n".join(listing(x, sold=True) for x in a["sold"])
    f = a["first"]
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <meta name="robots" content="noindex, nofollow, noarchive, noimageindex" />
  <title>{a["name"]} &mdash; The Group, Steamboat Springs</title>
  <meta name="description" content="{a["desc"]}" />
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Marcellus&family=Inter:wght@300;400;500&display=swap" rel="stylesheet" />
  <link rel="stylesheet" href="css/styles.css" />
  <link rel="stylesheet" href="css/guide-page.css" />
  <link rel="stylesheet" href="css/review.css" />
</head>
<body>

  <!-- ============================ AGENT HEAD ============================ -->
  <div class="pagehead" id="s-page-header" data-review="Page header">
{NAV}
    <div class="pagehead__inner agenthead">
      <a class="crumb" href="index.html#agents"><span>&larr;</span> The People</a>
      <div class="agenthead__grid">
        <div class="agenthead__photo"><img src="assets/agents/{a["slug"]}.jpg" alt="{a["name"]}" /></div>
        <div class="agenthead__body">
          <p class="eyebrow eyebrow--bright">{a["role"]} &middot; Steamboat Springs</p>
          <h1 class="h2">{a["name"]}</h1>
          <p class="agenthead__lede">{a["lede"]}</p>
          <ul class="agentfacts">
{facts}
          </ul>
          <div class="agenthead__actions">
            <a class="pill-btn pill-btn--light" href="#ask">Ask {f} a question <span>&rarr;</span></a>
            <a class="link-gold link-gold--bright" href="#listings">See the listings <span>&rarr;</span></a>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- ============================ ABOUT ============================ -->
  <section class="section bg-cream" id="s-about" data-review="About">
    <div class="container">
      <div class="lead-grid">
        <div class="lead-head">
          <p class="eyebrow">About</p>
          <h2 class="h2">{a["about_title"]}</h2>
        </div>
        <div class="prose">
{about}
        </div>
      </div>
    </div>
  </section>

  <!-- ============================ MY LISTINGS ============================ -->
  <section class="section bg-white" id="listings" data-review="My Listings">
    <div class="container">
      <div class="sec-head">
        <div>
          <p class="eyebrow">My Listings</p>
          <h2 class="h2">Currently on the market with {f}.</h2>
        </div>
        <a class="link-gold" href="property-search.html">Search all listings <span>&rarr;</span></a>
      </div>
      <p class="mls-note"><b>Placeholder view.</b> Live MLS / IDX results (IRES &amp; Summit MLS) connect here in production. The cards below carry {f}'s real active listings as of August 2026.</p>
      <div class="listings">
{actives}
      </div>
    </div>
  </section>

  <!-- ============================ MY SOLDS ============================ -->
  <section class="section bg-cream" id="s-my-solds" data-review="My Solds">
    <div class="container">
      <p class="eyebrow">My Solds</p>
      <h2 class="h2">Recently closed.</h2>
      <div class="listings">
{solds}
      </div>
    </div>
  </section>

  <!-- ============================ CREDENTIALS ============================ -->
  <section class="section bg-dark" id="s-{a["creds_id"]}" data-review="{a["creds_label"]}">
    <div class="container">
      <div class="lead-grid">
        <div class="lead-head">
          <p class="eyebrow">{a["creds_label"]}</p>
          <h2 class="h2">{a["creds_title"]}</h2>
        </div>
        <div>
          <ul class="creds">
{creds}
          </ul>
        </div>
      </div>
    </div>
  </section>

  <!-- ============================ SOLO SITE ============================ -->
  <section class="section bg-white" id="s-solo-site" data-review="Solo Site">
    <div class="container">
      <div class="sec-head">
        <div>
          <p class="eyebrow">Solo site</p>
          <h2 class="h2">{a["solo_title"]}</h2>
        </div>
        <a class="link-gold" href="{a["solo_href"]}">Open the mockup <span>&rarr;</span></a>
      </div>
      <p class="mls-note">{a["solo_note"]}</p>
      <div class="pubs__grid" style="margin-top:clamp(30px,4vw,44px)">
{solo_cards}
      </div>
    </div>
  </section>

  <!-- ============================ ASK ============================ -->
  <section class="section inquire" id="ask" data-review="Get In Touch">
    <div class="container">
      <div class="inquire__grid">
        <div class="inquire__intro">
          <p class="eyebrow">Get In Touch</p>
          <h2 class="h2">Ask {f} <br class="brk" />a question.</h2>
          <p class="lede">Buying, selling, or just getting the lay of the valley &mdash; send a note and {f} will come back to you directly.</p>
        </div>
        <form class="form" onsubmit="return false">
          <div class="field"><label for="a-name">Your name *</label><input id="a-name" type="text" placeholder="Jane Buyer" /></div>
          <div class="field"><label for="a-phone">Phone</label><input id="a-phone" type="tel" placeholder="Optional" /></div>
          <div class="field field--full"><label for="a-email">Email *</label><input id="a-email" type="email" placeholder="you@email.com" /></div>
          <div class="field field--full"><label for="a-msg">What can {f} help with? *</label><textarea id="a-msg" placeholder="Tell us what you are looking for in the valley."></textarea></div>
          <div class="form__submit"><button class="pill-btn" type="submit">Send to {f} <span>&rarr;</span></button></div>
        </form>
      </div>
    </div>
  </section>

{FOOTER}'''


AGENTS = [
# ---------------------------------------------------------------- Ashley
dict(
  slug="ashley-walcher", name="Ashley Walcher", first="Ashley",
  role="Broker Associate",
  desc="Ashley Walcher, Broker Associate at The Group in Steamboat Springs. 160 transactions and $120M in volume since 2016; top 40 producing agent in Routt County.",
  lede="Passionate, sharp and dynamic &mdash; and a second-generation broker. 160 transactions and $120&nbsp;million in volume since 2016.",
  facts=[
    ("Direct",  '<a href="tel:+13036684689">303.668.4689</a>'),
    ("Office",  '<a href="tel:+19708708800">970.870.8800</a>'),
    ("Website", '<a href="ashley-walcher/index.html">ashleywalcher.com</a>'),
    ("Office",  '509 Lincoln Ave,<br />Steamboat Springs'),
  ],
  about_title="A real estate family, and a love for the outdoors.",
  about=[
    "Ashley comes from a real estate family with a love for the outdoors and a passion for this industry, both of which motivate her. Her parents are longtime successful industry experts and she credits them for preparing her for her dynamic real estate career.",
    "With her father a well known, reputable <strong>Denver broker of 20 years</strong>, and her mother honored in the <strong>top 40 mortgage brokers in the nation</strong>, it is no doubt that they instilled her with the right skills, industry knowledge and instincts to provide superior service to her clients. This one-of-a-kind family experience gives Ashley the confidence that she can personally help every client find their dream home in Colorado, like she has been so grateful to also find.",
    "Since 2016 she has closed over 160 transactions representing $120 million in sales volume. Selling more than $15 million annually for the past five years, she ranks among the top 40 producing agents in Routt County. Her colleagues also elected her to serve on the Advisory Board at The Group Real Estate in Steamboat.",
    "Whether you are hoping to find a permanent residence or a second home, let Ashley help you. Allow her years of active community involvement, family industry connections and social networking assist you in finding the right property for you and your family.",
  ],
  active=[
    dict(status="Active",  price="$2,675,000", specs="4 Bd &middot; 4 Ba &middot; 1,934 SF",
         addr="1750 Medicine Springs Drive, #6303, Steamboat Springs",
         rep="Offered by Ashley Walcher &middot; The Group",
         img="ashley-walcher/assets/l-medicine-springs.jpg"),
    dict(status="Pending", price="$1,890,000", specs="3 Bd &middot; 2 Ba &middot; 36+ Acres",
         addr="31575 Kestrel Lane, Steamboat Springs",
         rep="Offered by Ashley Walcher &middot; The Group",
         img="ashley-walcher/assets/l-kestrel.jpg"),
    dict(status="Active",  price="$1,400,000", specs="4 Bd &middot; 3 Ba &middot; 3,018 SF",
         addr="30650 Reinsman Court, Oak Creek",
         rep="Offered by Ashley Walcher &middot; The Group",
         img="ashley-walcher/assets/l-reinsman.jpg"),
  ],
  sold=[
    dict(status="Sold", price="$9,075,000", specs="7 Bd &middot; 7 Ba &middot; 4,838 SF",
         addr="2410 Ski Trail Lane, #2301 &amp; 2302, Steamboat Springs",
         rep="Closed &middot; Ashley Walcher, The Group",
         img="ashley-walcher/assets/s-ski-trail.jpg"),
    dict(status="Sold", price="$2,770,000", specs="3 Bd &middot; 4 Ba &middot; 3,618 SF",
         addr="43750 Diamondback Way, Steamboat Springs",
         rep="Closed &middot; Ashley Walcher, The Group",
         img="ashley-walcher/assets/s-diamondback.jpg"),
    dict(status="Sold", price="$2,395,000", specs="4 Bd &middot; 4 Ba &middot; 1,921 SF",
         addr="2525 Village Drive, #2E, Steamboat Springs",
         rep="Closed &middot; Ashley Walcher, The Group",
         img="ashley-walcher/assets/s-village-2e.jpg"),
  ],
  creds_id="designations-recognition", creds_label="Designations &amp; Recognition",
  creds_title="A record kept by the numbers.",
  creds=[
    ("2026",       "Elected by colleagues to the Advisory Board, The Group Real Estate, Steamboat Springs."),
    ("2026",       "Ranked among the top 40 producing agents in Routt County."),
    ("2022&ndash;26", "More than $15 million in annual sales volume, five consecutive years."),
    ("160",        "Closed transactions since 2016, representing $120 million in volume."),
    ("2016",       "Licensed in Colorado."),
    ("Family",     "Second-generation broker: father a Denver broker of 20+ years, mother among the nation's top 40 mortgage brokers."),
  ],
  solo_cards=[
    dict(k="Homepage", title="ashleywalcher.com", href="ashley-walcher/index.html",
         desc="Ten pages in the 1000WATT look &amp; feel &mdash; hero, numbers, reviews, featured listings and all eleven submarkets."),
    dict(k="Editorial", title="The Journal", href="ashley-walcher/journal.html",
         desc="Her own submarket reporting. The only agent in the set who writes it, and the strongest content on any of the six source sites."),
    dict(k="Places", title="Eleven neighborhoods", href="ashley-walcher/neighborhoods.html",
         desc="Mountain Area through South Routt, with her own photography and a read on what each one actually trades on."),
  ],
  solo_title="Ashley also runs her own site.",
  solo_href="ashley-walcher/index.html",
  solo_note="<b>Mockup.</b> Her live site at ashleywalcher.com has been ported into the 1000WATT look &amp; feel &mdash; ten pages, including a Journal carrying her own submarket reporting, and all eleven Routt County neighborhoods. The <b>Website</b> link above opens that mockup rather than the production site.",
),
# ---------------------------------------------------------------- Lauren
dict(
  slug="lauren-bloom", name="Lauren Bloom", first="Lauren",
  role="Broker Associate &amp; Partner",
  desc="Lauren Bloom, Broker Associate and Partner at The Group in Steamboat Springs. 120+ transactions and $60M+ closed; land acquisition, rural development and ranch sales.",
  lede="Land acquisition, rural development, investment property and Routt County ranch sales &mdash; with twenty years of design and horticulture behind the read on every parcel.",
  facts=[
    ("Direct",  '<a href="tel:+19702917727">970.291.7727</a>'),
    ("Office",  '<a href="tel:+19708708800">970.870.8800</a>'),
    ("Website", '<a href="lauren-bloom/index.html">realestatebybloom.com</a>'),
    ("Office",  '509 Lincoln Ave,<br />Steamboat Springs'),
  ],
  about_title="From landscape design to land acquisition.",
  about=[
    "Lauren Bloom is a Broker Associate and Partner with The Group Real Estate, recognized for her results-driven approach and deep expertise in the Steamboat Springs and Routt County markets. A Colorado native who relocated from Golden to Steamboat in 2021, Lauren brings a unique blend of professionalism, precision and passion to every transaction.",
    "Licensed since 2020, she has closed <strong>more than 120 transactions totaling over $60 million</strong> in Routt and Mesa counties &mdash; spanning everything from rural parcels to luxury estates. In 2025 alone, Lauren completed over 40 transactions and $20 million in sales.",
    "Before entering real estate, Lauren built a distinguished 20-year career as an award-winning landscape designer and horticulturist, earning statewide recognition for her transformative projects. She and her husband owned a Denver-based design-build firm that was featured in national publications and consistently ranked among Colorado's top landscape companies. This creative foundation provides her clients a rare advantage when evaluating land potential, navigating site development, or envisioning sustainable, environmentally aligned properties across the Yampa Valley.",
    "Lauren specializes in <strong>land acquisition, rural development, investment properties, and Routt County single-family home and ranch sales</strong>. With an office in Steamboat and a ranchette in South Routt she remains deeply connected to the ranching community she calls home. As a sponsor of the Steamboat Springs Pro Rodeo and a farm producer for the Community Agriculture Alliance, Lauren is actively engaged in the community that defines Routt County.",
    "Clients value her straightforward communication, sharp negotiation skills and hands-on guidance through the region's complex zoning and permitting processes. Her mission is simple: to deliver a real estate experience defined by trust, strategy and exceptional results.",
  ],
  active=[
    dict(status="Active",  price="$1,947,000", specs="38.08 Acres &middot; Land &middot; Oak Creek",
         addr="TBD Silverado Road, Oak Creek",
         rep="Offered by Lauren Bloom &middot; The Group",
         img="lauren-bloom/assets/nb-phippsburg-yampa.jpg",
         alt="TBD Silverado Road, Oak Creek \u2014 representative South Routt mountain country",
         href="lauren-bloom/property-tbd-silverado-road.html"),
    dict(status="Active",  price="$1,695,000", specs="4 Bd &middot; 3 Ba &middot; 3,742 SF",
         addr="31575 Buckingham Lane, Steamboat Springs",
         rep="Offered by Lauren Bloom &middot; The Group",
         img="assets/listings/bear-drive-1.jpg"),
    dict(status="Pending", price="$1,875,000", specs="3 Bd &middot; 3 Ba &middot; 1,809 SF",
         addr="27055 Whitewood Drive E, Steamboat Springs",
         rep="Offered by Lauren Bloom &middot; The Group",
         img="assets/listings/hinton-lane.jpg"),
  ],
  sold=[
    dict(status="Sold", price="$3,500,000", specs="4 Bd &middot; 4 Ba &middot; 2,272 SF",
         addr="2085 Ski Time Square Drive, #124, Steamboat Springs",
         rep="Closed &middot; Lauren Bloom, The Group",
         img="assets/listings/medicine-springs.jpg"),
    dict(status="Sold", price="$2,125,000", specs="4 Bd &middot; 4 Ba &middot; 2,560 SF",
         addr="27409 Winchester Court, Steamboat Springs",
         rep="Closed &middot; Lauren Bloom, The Group",
         img="assets/listings/canyon-court-1.jpg"),
    dict(status="Sold", price="$1,050,000", specs="2 Bd &middot; 1 Ba &middot; 1,113 SF",
         addr="21185 County Road 16, Oak Creek",
         rep="Closed &middot; Lauren Bloom, The Group",
         img="assets/listings/boulder-court.jpg"),
  ],
  creds_id="designations-recognition", creds_label="Designations &amp; Recognition",
  creds_title="A record kept by the numbers, and by the neighbours.",
  creds=[
    ("2025",       "Over 40 closed transactions and $20 million in volume &mdash; her strongest year to date."),
    ("120+",       "Closed transactions since 2020, totaling over $60 million in Routt and Mesa counties."),
    ("Partner",    "Partner, The Group Real Estate."),
    ("2020",       "Licensed in Colorado; relocated from Golden to Routt County in 2021."),
    ("Ongoing",    "Sponsor, Steamboat Springs Pro Rodeo."),
    ("Ongoing",    "Farm producer, Community Agriculture Alliance."),
    ("2001&ndash;21", "Award-winning landscape designer and horticulturist; co-owner of a Denver design-build firm ranked among Colorado's top landscape companies."),
  ],
  solo_cards=[
    dict(k="Homepage", title="realestatebybloom.com", href="lauren-bloom/index.html",
         desc="Ten pages in the 1000WATT look &amp; feel &mdash; hero, numbers, twenty reviews with their submarkets, and six areas of expertise."),
    dict(k="Resources", title="Preferred contacts", href="lauren-bloom/resources.html",
         desc="Twenty-one Routt County title companies, lenders, land-loan sources, surveyors and insurers, plus a working mortgage calculator."),
    dict(k="Inventory", title="Portfolio", href="lauren-bloom/properties.html",
         desc="For sale, pending and sold behind status tabs, plus her video tours for out-of-state buyers."),
  ],
  solo_title="Lauren also runs her own site.",
  solo_href="lauren-bloom/index.html",
  solo_note="<b>Mockup.</b> Her live site at realestatebybloom.com has been ported into the 1000WATT look &amp; feel &mdash; ten pages, including her preferred-contacts directory of twenty-one Routt County vendors and a working mortgage calculator. The <b>Website</b> link above opens that mockup rather than the production site.",
),
# ---------------------------------------------------------------- Matt
dict(
  slug="matt-eidt", name="Matt Eidt", first="Matt",
  role="Broker Associate &amp; Partner",
  desc="Matt Eidt, Broker Associate and Partner at The Group in Steamboat Springs. Realtor since 2012, Steamboat local since 2007, nine-time Best of the Boat Best Real Estate Agent.",
  lede="Residential, commercial and investment property. Nine-time &ldquo;Best of the Boat&rdquo; Best Real Estate Agent, and the youngest owner in the history of the firm.",
  facts=[
    ("Direct",  '<a href="tel:+19708190827">970.819.0827</a>'),
    ("Office",  '<a href="tel:+19708708800">970.870.8800</a>'),
    ("Website", '<a href="matt-eidt/index.html">owntheboat.com</a>'),
    ("Office",  '509 Lincoln Ave,<br />Steamboat Springs'),
  ],
  about_title="Built on fairness, integrity and legendary service.",
  about=[
    "Since becoming a Realtor&reg; in 2012, Matt has built his business on fairness, integrity, and a commitment to providing legendary service. A Steamboat local since 2007, he has a deep-rooted connection to the community, and lives in downtown Steamboat Springs with his young daughter, son and wife.",
    "His dedication to real estate has earned him significant recognition, including being the <strong>youngest owner in the history of Colorado Group Realty</strong> (now The Group Real Estate), receiving the prestigious Twenty-Under-40 award, and being named <strong>&ldquo;Best of the Boat, Best Real Estate Agent&rdquo; for nine years</strong>.",
    "Beyond real estate, Matt is actively involved in the community, having served on the boards of Steamboat Creates, Group Gives Charitable Foundation, Yampa Valley Gives, and the Steamboat Springs Lions Club and Young Professionals Network.",
    "With a business degree and a background in sales and <strong>professional photography</strong>, he brings a unique blend of creativity and market expertise to every transaction. His deep understanding of Steamboat Springs' complex real estate market makes him an invaluable resource for buyers and sellers alike, whether in residential, commercial, or investment properties.",
    "Matt's professional drive, extensive market knowledge and strong community ties have made him a trusted expert in Steamboat real estate. Whether you're purchasing your first mountain home or selling a luxury property, you won't find a more honest, effective and personalized approach.",
  ],
  active=[
    dict(status="Active", price="$375,000", specs="Condominium &middot; Oak Creek",
         addr="23800 County Road 16, #508, Oak Creek",
         rep="Offered by Matt Eidt &middot; The Group",
         img="matt-eidt/assets/l-cr16-508.jpg"),
  ],
  sold=[
    dict(status="Sold", price="$3,050,000", specs="Buy side",
         addr="2020 Bear Drive, Steamboat Springs",
         rep="Buyer represented by Matt Eidt &middot; listed by Dean Laird, The Group",
         img="matt-eidt/assets/s-bear-drive.jpg"),
    dict(status="Sold", price="$2,329,060", specs="Listing side",
         addr="2315 Storm Meadows Drive, #3, Steamboat Springs",
         rep="Listed &amp; sold by Matt Eidt, The Group",
         img="matt-eidt/assets/s-storm-meadows.jpg"),
    dict(status="Sold", price="$1,440,000", specs="Listing side",
         addr="35 Butcherknife Alley, Steamboat Springs",
         rep="Listed &amp; sold by Matt Eidt, The Group",
         img="matt-eidt/assets/s-butcherknife.jpg"),
  ],
  creds_id="recognition-service", creds_label="Recognition &amp; Service",
  creds_title="Nine years running, voted by the town he lives in.",
  creds=[
    ("9&times;",  "&ldquo;Best of the Boat, Best Real Estate Agent&rdquo; &mdash; voted by the Steamboat community, nine years."),
    ("Twenty",    "Recipient of the Twenty-Under-40 award."),
    ("Youngest",  "Youngest owner in the history of Colorado Group Realty, now The Group Real Estate."),
    ("Board",     "Steamboat Creates &mdash; the valley's arts and creative-industries council."),
    ("Board",     "Group Gives Charitable Foundation, the brokerage's giving arm."),
    ("Board",     "Yampa Valley Gives."),
    ("Board",     "Steamboat Springs Lions Club, and the Young Professionals Network."),
    ("2012",      "Licensed in Colorado; a Steamboat resident since 2007."),
  ],
  solo_cards=[
    dict(k="Homepage", title="owntheboat.com", href="matt-eidt/index.html",
         desc="Six pages in the 1000WATT look &amp; feel &mdash; the short shape, leaning on the brokerage pages rather than duplicating them."),
    dict(k="Specialty", title="Commercial &amp; investment", href="matt-eidt/commercial.html",
         desc="Downtown retail, Copper Ridge industrial, and short-term-rental underwriting on real occupancy rather than projections."),
    dict(k="Inventory", title="Listing side / buy side", href="matt-eidt/properties.html",
         desc="Solds grouped by which side he represented &mdash; roughly half are buy-side, the fact a buyer most wants to know."),
  ],
  solo_title="Matt also runs his own site.",
  solo_href="matt-eidt/index.html",
  solo_note="<b>Mockup.</b> His live site at owntheboat.com has been ported into the 1000WATT look &amp; feel &mdash; six pages, including a commercial and investment page, and solds grouped by which side of the table he represented. The <b>Website</b> link above opens that mockup rather than the production site.",
),
]

for a in AGENTS:
    dest = os.path.join(DOCS, f"agent-{a['slug']}.html")
    with open(dest, "w", encoding="utf-8") as fh:
        fh.write(page(a))
    print("wrote", os.path.basename(dest))
