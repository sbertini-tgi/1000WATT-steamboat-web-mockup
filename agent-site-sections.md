# Agent Site Sections

A catalogue of the content section blocks used across The Group's Steamboat agent
websites, and the 1000WATT block that replaces each one.

The point of this file is **reuse**. Every agent site is the same twenty-odd blocks in a
different order with different copy. Catalogue the blocks once, express each agent's
content as *data* about those blocks, and porting the next agent becomes a content job
rather than a design job.

- **Source sites analysed** — six, in two platform families (below).
- **Blocks identified** — 25, plus nav/footer chrome.
- **Ported** — three, one from each of the two families:
  [`docs/lauren-bloom/`](docs/lauren-bloom/) (11 pages, incl. a property detail),
  [`docs/ashley-walcher/`](docs/ashley-walcher/) (10 pages),
  [`docs/matt-eidt/`](docs/matt-eidt/) (6 pages).
- **Built by** — [`tools/build-agent-site.py`](tools/build-agent-site.py) from one
  `content.json` per agent. See §4 for what each additional port actually cost.

---

## 1. The source sites

### Family A — Luxury Presence (hosted, template-driven)

| Agent | Site | Notes |
|---|---|---|
| Ashley Walcher | [ashleywalcher.com](https://ashleywalcher.com) | Video hero, stats row, Instagram feed, blog |
| Lauren Bloom | [realestatebybloom.com](https://realestatebybloom.com) | Deepest content set: guides, preferred contacts, video gallery |
| Dianne Bertini | [liveinsteamboatsprings.com](https://liveinsteamboatsprings.com) | Most voice-forward; "hoverable" narrative sections |

Luxury Presence builds pages out of a fixed vocabulary of named section components.
Reading the DOM gives you the vocabulary directly — every page is
`<section class="solid-section|image-section|video-section is-font-color-* is-background-color-*">`
wrapping one component div:

```
video-section          → full-bleed video hero
gallery-component      → 3-up card row ("Find your dream home with Lauren")
company-stats          → numeric proof row
testimonials-section   → rotating quote slider
properties-slider      → For Sale / Sold / For Lease tabbed inventory
home-valuation         → "How much is your home worth" + 3 benefits
featured-neighborhoods-grid
newsletter-signup
work-with-us           → parallax closing CTA band
instagram-feed
agent-card             → "Meet <agent>" teaser
stats-list-container
neighborhoods-slider
hoverable-section      → narrative copy block (Dianne only)
```

The three sites differ **only** in which of those components are switched on, their
order, and the copy. Ashley adds `stats-list-container` and `instagram-feed`; Dianne
swaps the card row for two `hoverable-section` narrative blocks; Lauren carries the
richest interior pages (buyer's/seller's guides, preferred contacts, video gallery).

### Family B — Tribus / The Group (brokerage platform)

| Agent | Site | Notes |
|---|---|---|
| Martin Dragnev & Holly Martin | [realestateofsteamboat.com](https://realestateofsteamboat.com) | Team site; development microsites |
| Scott & Pete Wither | [steamboatsprings-homes.com](https://steamboatsprings-homes.com) | Same template, thinner content |
| Matt Eidt | [owntheboat.com](https://owntheboat.com) | Same template + a bio block above the fold |

Family B is a much shorter, MLS-first template. Homepage is always:

```
property-search-slim   → MLS search bar (Properties / Agents tabs)
[bio section]          → optional; Matt has one, Martin/Wither do not
featured-properties    → "Active Listings"  + View All
featured-properties    → "Our Solds" / "My Solds" + View All
testimonials           → Testimonial Tree feed
contact form
```

Shared nav across all three: Meet The Team · Sell with The Group · Search / New Listings
/ Solds · Market Report · The Insider · Blog. Those brokerage-level pages already exist
in the 1000WATT mockup (`market-report.html`, `real-estate-insider.html`, `blog.html`,
`how-we-work-with-sellers.html`), so an agent site should **link to them, not duplicate
them**. That is the single biggest content decision in this port.

### What both families share

Every one of the six sites, stripped to content, is:

1. an opener that says who the agent is and where they work,
2. a proof block (stats, or a wall of reviews, or both),
3. inventory (active, sold, sometimes leased),
4. places (neighbourhoods / areas of expertise),
5. an education block (buyer's guide, seller's guide, valuation),
6. a conversion block (form, newsletter),
7. chrome (nav, footer, disclaimers).

---

## 2. The block catalogue

Block ids are the `type` values understood by `tools/build-agent-site.py`. "Renders as"
names the CSS component in `docs/css/styles.css`, `docs/css/guide-page.css`, or the new
`docs/css/agent-site.css`.

### Openers

#### `hero`
Full-bleed image or video, agent name, positioning line, one or two CTAs. Optionally a
search entry across the bottom.
- **Seen on** — all six. Family A uses looping video; Family B uses a static band.
- **Data** — `image`, `eyebrow`, `title`, `lede`, `actions[]`, `search?`
- **Renders as** — `.hero` / `.hero__bg` / `.hero__scrim` (existing homepage hero)
- **Note** — Luxury Presence sets the agent's *name* as the hero H1 and the positioning
  line below it. Keep that: the name is the brand on an agent site, unlike the
  brokerage homepage where the place is the brand.

#### `pagehead`
Interior page header: breadcrumb back to home, eyebrow, title, optional lede.
- **Seen on** — every interior page of all six sites.
- **Data** — `crumb`, `eyebrow`, `title`, `lede?`
- **Renders as** — `.pagehead` / `.pagehead__inner`

### Agent identity

#### `agent-intro`
Portrait beside a short bio and a contact-facts list. The "Meet <agent>" teaser on the
homepage and the header of the About page are the same block at two lengths.
- **Seen on** — all six (`agent-card` in Family A; the bio `<section>` on owntheboat).
- **Data** — `image`, `eyebrow`, `title`, `role`, `paragraphs[]`, `facts[]`,
  `actions[]`, `fit?`
- **Renders as** — `.agenthead__grid` / `.agentfacts` (existing agent profile pages)
- **Note** — Portrait supply differs by family. Luxury Presence agents provide
  environmental portraits that crop well; the brokerage agents provide cut-out studio
  headshots on white, which `object-fit: cover` decapitates. `fit: "contain"`
  letterboxes those against a matching studio ground instead.

#### `stats`
Row of 2–4 big numbers with labels. Lauren: 120+ closed sales · $60M+ total sold ·
$10K–$3.5M price range. Ashley: $120M total value · $15M+ annual volume · 10 years ·
160 closed sales.
- **Seen on** — Ashley, Lauren. Absent from Family B.
- **Data** — `items[] {n, label}`
- **Renders as** — `.stats` / `.stat__n` / `.stat__l`

#### `creds`
Dated list of designations, awards and rankings.
- **Seen on** — Martin (in prose). Strongest fit for The Group's award-heavy agents.
- **Data** — `items[] {year, text}`
- **Renders as** — `.creds`

#### `prose`
Eyebrow + heading in the left column, long-form copy in the right. The workhorse for
biography, area narrative, and Dianne's `hoverable-section` voice blocks.
- **Seen on** — all six.
- **Data** — `eyebrow`, `title`, `paragraphs[]`
- **Renders as** — `.lead-grid` / `.prose`

### Social proof

#### `testimonials`
Client quotes with an attribution line. Two layouts from the same data:
`slider` (homepage, 3-up) and `wall` (the Testimonials page, all of them).
- **Seen on** — all six. Family A hand-curates; Family B pipes in Testimonial Tree.
- **Data** — `layout`, `items[] {quote, name, place?}`
- **Note** — Lauren's attributions carry the *submarket* ("STAGECOACH BUYER",
  "HAYDEN SELLER"). That is unusually good content — it proves geographic range while
  it proves service. Preserve the submarket, don't flatten it to a name.
  Ashley's carry a role only ("Buyer"), and Matt's a first name only, so `place` is
  optional. Where it is missing the port says so on the page rather than papering over
  it — see `testimonials.html` on both of those sites.

### Inventory

#### `listings`
Property cards: status chip, price, beds/baths/SF, address, "offered by" line. Groups
into tabs when there is more than one status set.
- **Seen on** — all six, usually twice (active, then sold).
- **Data** — `groups[] {label, items[] {status, price, specs?, address, rep, image, href}}`
- **Renders as** — `.listings` / `.listing` / `.listing__chip` (existing)
- **Note** — In production this is IDX/MLS output, not authored content. The block
  should carry a visible placeholder note, the way the existing agent pages do.
- **Note** — `specs` is optional: Family B cards publish price, address and listing
  broker with no beds/baths at all. Matt's port turns that constraint into an asset by
  grouping his solds into **listing side** and **buy side** — derivable from the
  "offered by" line, and more useful on a solds wall than bedroom counts. Roughly half
  his closings are buy-side, which no other agent site in the set surfaces.

#### `gallery`
A property's photography: one lead image with a stack beside it, and a count chip.
- **Seen on** — every property detail page on all six sites.
- **Data** — `count?`, `main {src, alt}`, `side[] {src, alt}`
- **Renders as** — `.gallery` / `.gallery__main` / `.gallery__side` / `.g-item` / `.g-count`

#### `listing-detail`
One property, in full: price head, spec strip, marketing copy, the MLS field table,
price history, a map placeholder, and the listing agent's card with a showing-request
form.
- **Seen on** — all six. Luxury Presence and Tribus both render this from the IDX feed.
- **Data** — `status`, `title`, `city`, `price`, `action`, `specs[] {v, k}`,
  `eyebrow`, `heading`, `paragraphs[]`, `note?`, `details[] [k, v]`, `history[]?`,
  `map?`, `agent {photo, name, href, role, blurb, fields[], submit, tel}`
- **Renders as** — `.section--pdetail` / `.phead` / `.specstrip` / `.propcols` /
  `.dtable` / `.pricehist` / `.agentcard` (all existing, from the brokerage property
  pages)
- **Note** — Pair it with a `pagehead` carrying `slim: true`, a `gallery` above, and a
  `band` + `listings` below for the "selling one of these?" and "keep looking" tails.
  The MLS field table is where a listing earns trust, so prefer more rows to fewer:
  well permit, access, zoning and topography matter more on land than bedroom counts.
  Where the source listing's own photography cannot be reproduced, say so in the
  `note` **and** choose stand-ins that do not contradict the listing — a photograph
  with a house in it on an unimproved-land listing is worse than no photograph.

#### `search`
MLS search entry — a field, a few filter pills, a submit.
- **Seen on** — all six. Family B puts it directly under the nav.
- **Renders as** — `.searchbar` (existing) or `.finder` on the homepage

#### `quicklinks`
A 2–4 card row pointing at the next useful page: Buyer's Guide / Home Search /
Seller's Guide. Luxury Presence calls it `gallery-component` and repeats it at the foot
of most interior pages.
- **Seen on** — Ashley, Lauren, Dianne. Cheap and effective; keep it.
- **Data** — `items[] {k, title, desc, href}`
- **Renders as** — `.guide-cards` / `.guide` or `.pubs__grid` / `.pub`

### Places

#### `neighborhoods`
Photo cards for each area, name over or under the image, "Learn more".
- **Seen on** — all three Family A sites; Family B defers to the brokerage
  `communities.html`.
- **Data** — `items[] {name, blurb, image, href}`
- **Renders as** — `.commgrid` / `.comm` (existing communities page)

#### Interior area page — *not a block type*
The interior area page: welcome copy, curated local links (dining, golf, trails), a
demographics panel, a schools table, nearby-area links. Catalogued for completeness;
deliberately **not** implemented as a builder block (see the note).
- **Seen on** — Lauren, Ashley, Dianne (all Luxury Presence boilerplate, US Census fed).
- **Note** — The demographics and schools panels are vendor data, not agent content.
  Worth a decision before production: they add SEO surface and almost no brand value,
  and they date badly. The 1000WATT port keeps the *curated local links* — the part
  that is actually the agent's knowledge — as the `locals` block, and drops the Census
  panels. Add per-area pages later if the SEO case is made; nothing here depends on it.

#### `locals`
The agent's own curated area knowledge as a key/value list — where to eat, which trail,
which school district, who plows. The one part of an area page a vendor feed cannot
produce.
- **Data** — `items[] {k, v}`
- **Renders as** — `.locals`

### Education & conversion

#### `steps`
Numbered process guide. Lauren's Buyer's Guide is 10 steps; her Seller's Guide is 8.
Every Luxury Presence site ships the identical stock copy.
- **Seen on** — Ashley, Lauren, Dianne (verbatim identical text on all three).
- **Data** — `steps[] {title, body}`
- **Renders as** — `.steps` / `.step__n` / `.step__b`
- **Note** — Because the copy is stock and shared, this is the block most worth
  rewriting once at brokerage level and inheriting. The mockup's
  `how-we-work-with-buyers.html` already does a better job in fewer steps. Recommend
  agent sites link to it rather than carry their own 10-step stock guide; the port keeps
  a short 4-step version in Lauren's voice as the middle path.

#### `valuation`
"How much is your home worth?" — three benefit lines (Instant Property Valuation ·
Expert Advice · Sell For More) and a CTA into the valuation tool.
- **Seen on** — Ashley, Lauren, Dianne.
- **Data** — `title`, `points[]`, `action`
- **Renders as** — `.checks` + `.pill-btn` on `.bg-dark`

#### `directory`
Grouped list of preferred vendors — title companies, mortgage, land loans, surveying,
rental management, insurance.
- **Seen on** — Lauren only, and it is the best content on any of the six sites: it is
  specific, local, hard to fake, and useful to a real buyer. Strongly recommend
  promoting it to a pattern other agents adopt.
- **Data** — `groups[] {name, items[] {name, href, note?}}`
- **Renders as** — `.readme-grid` / `.readme__file` adapted, in `agent-site.css`

#### `posts`
Editorial cards — category, headline, date, excerpt, "continue reading".
- **Seen on** — Ashley only, and it is the strongest content on any of the six sites:
  six pages of original submarket reporting ("Fish Creek isn't one market. It's a road
  with three price points."). Dianne and Lauren have no blog; Family B links to the
  brokerage blog.
- **Data** — `items[] {cat, date, title, excerpt, href}`
- **Renders as** — `.blog-grid` / `.post` (existing `blog.html` components)
- **Note** — This is the one block where an agent writing for themselves clearly beats
  inheriting brokerage copy, because the value *is* the local specificity. Where an
  agent does not write, link the brokerage blog rather than syndicating stock posts.

#### `videos`
Property tour and market videos as cards.
- **Seen on** — Lauren (dedicated page), Ashley (YouTube links only).
- **Data** — `items[] {title, meta, href}`

#### `calculator`
Mortgage calculator.
- **Seen on** — Ashley, Lauren, Dianne (stock Luxury Presence widget).

#### `newsletter`
Email capture — "Receive exclusive listings in your inbox" — plus TCPA consent copy.
- **Seen on** — Ashley, Lauren, Dianne.
- **Data** — `title`, `lede`, `disclosure`
- **Renders as** — `.subscribe` (existing blog page)

#### `band`
Full-bleed closing CTA. Luxury Presence's `work-with-us`: "Work with <agent>", one
paragraph, one button. Appears at the foot of *every* interior page.
- **Seen on** — all three Family A sites, every page.
- **Data** — `image`, `eyebrow`, `title`, `lede`, `actions[]`
- **Renders as** — `.band` / `.band__bg` / `.band__scrim` (existing)

#### `form`
Contact form. Lauren's adds a "What are you interested in?" select
(Buying / Selling / Investing / Area Information) — a genuinely useful routing field.
- **Seen on** — all six.
- **Data** — `fields[]`, `submit`, `disclosure`
- **Renders as** — `.inquire__grid` / `.form` / `.field` (existing)

#### `social`
Instagram feed grid.
- **Seen on** — Ashley, Dianne. Skipped in the port: it needs a live API and adds no
  design signal to a mockup.

### Chrome

#### `nav`
Agent name or brokerage logo, and the agent's phone. Luxury Presence hides everything
behind a hamburger even on desktop; Family B uses a conventional bar.
- **Port decision** — keep The Group logo *and* the agent's name, so an agent site
  reads as part of the brokerage rather than a detached personal brand.

#### `footer`
Agent contact block (phone, email, office address), site links, MLS/fair-housing
disclaimer, copyright.
- **Renders as** — `.footer--home` / `.footer__box` (existing)

---

## 3. Reuse model

`tools/build-agent-site.py` reads one JSON file per agent and writes static pages. The
JSON is *only* content — no markup, no classes:

```json
{
  "agent": { "name": "Lauren Bloom", "role": "Broker Associate & Partner", … },
  "nav":   [ { "label": "About", "href": "about.html" }, … ],
  "shared": { "band": { … }, "form": { … } },
  "pages": [
    { "file": "index.html", "title": "…", "blocks": [
        { "type": "hero",   "image": "assets/hero.jpg", "title": "Lauren Bloom", … },
        { "type": "stats",  "items": [ … ] },
        { "type": "$band" }
    ] }
  ]
}
```

Three mechanics make it reusable:

1. **Block types are closed.** Adding an agent never means writing HTML — only choosing
   from the 22 types above and filling in copy.
2. **`shared` + `$name` references.** Blocks that repeat on every page (the closing
   band, the contact form, the quicklinks row) are declared once and referenced as
   `{"type": "$band"}`. This is exactly how Luxury Presence's `work-with-us` behaves,
   and it is why their sites stay consistent.
3. **`agent.*` interpolation.** Copy can say `{{agent.first}}` and
   `{{agent.phone}}`; the builder substitutes. So "Work with Lauren" / "Ask Lauren a
   question" / "Send to Lauren" all come from one template string that works unchanged
   for Ashley or Matt.

### Porting the next agent

```bash
cp docs/lauren-bloom/content.json docs/ashley-walcher/content.json
# edit agent{}, swap copy, drop blocks she doesn't have, add the ones she does
python3 tools/build-agent-site.py docs/ashley-walcher/content.json
python3 tools/review-manifest.py     # discovers the new folder; no edit needed
```

Blocks with no per-agent content simply get omitted from `pages[].blocks`.

---

## 4. What the ports actually cost

The honest test of a reuse model is the second and third use of it, so here is the record.

| | Lauren Bloom | Ashley Walcher | Matt Eidt |
|---|---|---|---|
| Family | Luxury Presence | Luxury Presence | Tribus / brokerage |
| Pages | 10 | 10 | 6 |
| Reviewable blocks | 66 | 71 | 34 |
| New block types | 22 (the initial set) | **1** (`posts`) | **0** |
| Later additions | `gallery`, `listing-detail` (property page) | — | — |
| New CSS components | the initial set | 0 | 1 (`fit: contain`) |
| Builder changes | — | `place` optional | `specs` optional, `fit` option |

**Lauren** established the set. **Ashley** needed exactly one new block type — `posts`,
for her blog, which no other agent in the set has — and it reused the existing
`blog.html` styling rather than adding any. **Matt** needed no new block types at all;
his site is a different *selection* and a different *shape* (six pages, no
neighbourhoods, no valuation page, no newsletter), which is what the model is for.

A fourth pass added a **property detail page** to Lauren's site (TBD Silverado Road,
her $1,947,000 38-acre Oak Creek parcel). That needed two new block types — `gallery`
and `listing-detail` — and again **no new CSS**: the brokerage property pages already
had every component, so the blocks are a data-driven wrapper over `.phead`,
`.specstrip`, `.propcols`, `.dtable` and `.agentcard`. A `slim: true` flag on
`pagehead` covers the shallow header those pages use above a gallery.

The three earlier changes to the builder were all the same kind of thing: a field that
one agent has and another does not. `place` on a testimonial, `specs` on a listing, and a
portrait that must letterbox rather than crop. Each was a two-line change and each
made the model more general, not less.

Three shared fixes came out of the ports and now benefit every agent:

- **Hero legibility.** The first hero was tuned to one photograph. The second broke it —
  small gold type over bright snow measured 1.6:1 against a 4.5:1 requirement. The fix
  is a scrim sized to the *copy block* rather than to the viewport, masked so its top
  edge dissolves, which now measures ≥5.5:1 on both heroes and does not depend on what
  the next agent's photograph looks like.
- **No inline layout styles.** Column counts are emitted as classes (`.stats--4`,
  `.guide-cards--3`), because inline `grid-template-columns` beats the responsive media
  queries and stranded a three-up row on phones.
- **Discovered, not listed.** `review-manifest.py` finds agent sites by globbing for
  `docs/*/content.json` and derives their titles, so adding an agent needs no edit to
  the tooling.

### Content that should live at brokerage level, not per agent

The audit's clearest finding: a large share of every Family A site is stock copy
duplicated verbatim across agents. Recommend these live once, at brokerage level, and be
linked from agent sites:

| Duplicated content | Already in the mockup as |
|---|---|
| 10-step buyer's guide (stock) | `how-we-work-with-buyers.html` |
| 8-step seller's guide (stock) | `how-we-work-with-sellers.html` |
| Neighbourhood demographics / schools | `communities.html` |
| Market statistics | `market-report.html` |
| Editorial / blog | `blog.html`, `real-estate-insider.html` |
| MLS & fair-housing disclaimers | shared footer |

What genuinely belongs to the agent, and should be the focus of any agent site: their
bio, their numbers, their listings and solds, their reviews (with submarkets), their
areas of expertise, their preferred vendors, and their video work.
