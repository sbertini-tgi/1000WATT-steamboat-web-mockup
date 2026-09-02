# 1000WATT Steamboat — Web Mockup

A static, editorial rebrand mockup for **The Group · Steamboat Springs**, in the 1000WATT
look & feel, plus a content-mapping framework that maps the current production site
([thegrouprealestatess.com](https://thegrouprealestatess.com)) onto the new design.

This is a **mockup / working prototype**, kept separate from future production web development.

## Contents

The publishable website lives in [`docs/`](docs/):

- [`docs/index.html`](docs/index.html) — the new editorial homepage mockup.
- **Agent sites** in the same look & feel, each generated from one `content.json` by
  [`tools/build-agent-site.py`](tools/build-agent-site.py):
  [`docs/lauren-bloom/`](docs/lauren-bloom/) (10 pages),
  [`docs/ashley-walcher/`](docs/ashley-walcher/) (10 pages) and
  [`docs/matt-eidt/`](docs/matt-eidt/) (6 pages).
- [`docs/content-mapping-framework.html`](docs/content-mapping-framework.html) — production → new-site
  content mapping framework. Not linked from the homepage; open it directly.
- `docs/css/`, `docs/js/`, `docs/assets/` — styles, scripts, images, and self-hosted fonts.

## Agent sites

[`agent-site-sections.md`](agent-site-sections.md) catalogues the 23 content section
blocks used across the six custom agent sites (three on Luxury Presence, three on Tribus)
and maps each one to its 1000WATT equivalent. Three are ported as reference
implementations — one Luxury Presence site with the richest content set (Lauren), one
with a real blog (Ashley), and one brokerage-platform site, which is a much shorter shape
(Matt).

Each agent's content lives in one JSON file, organised by section block. Rebuild after
editing it:

```
python3 tools/build-agent-site.py docs/lauren-bloom/content.json
python3 tools/review-manifest.py          # discovers agent folders; relists them in review.html
```

The three brokerage-side profile pages for those agents
(`docs/agent-lauren-bloom.html` and siblings) come from a second generator, because
they carry an extra "Solo site" section linking into the agent's folder:

```
python3 tools/build-agent-profiles.py
```

Dean, Martin and Jon stay hand-written. A listing card on any of these pages gains an
`href` to become a link into a property detail page.

Porting another agent means copying the JSON, swapping the copy, and running the builder
— no HTML and no CSS. Shared blocks (the closing band, the contact form, the quicklinks
row) are declared once and referenced as `{"type": "$band"}`, and copy can interpolate
`{{agent.first}}` so one string works for any agent. The second port needed one new block
type and the third needed none; §4 of the catalogue has the record.

## Keeping it out of search results

Every page under `docs/` carries:

```html
<meta name="robots" content="noindex, nofollow, noarchive, noimageindex" />
```

This is enforced, not left to whoever adds the next page:
`tools/build-agent-site.py` emits it, and `tools/review-manifest.py` normalises it
across all 63 pages on every run (replacing weaker directives, collapsing
duplicates, writing only on a real change).

**`docs/robots.txt` is present but inert at the current URL.** Crawlers only read
robots.txt from the host root — `sbertini-tgi.github.io/robots.txt` — which a
*project* Pages repo does not control. The per-page meta tags are what actually
apply. The file is there so the rule is already right if a custom domain is ever
attached.

Note that `noindex` asks well-behaved crawlers not to index; it does not make the
site private. Anything genuinely sensitive should stay out of `docs/` (as
`specs/` already does, via `.gitignore`).

## Serving it as a website (GitHub Pages)

This is a public repo, configured to publish from the **`docs/` folder**:

**Settings → Pages → Build and deployment → Source: "Deploy from a branch" → Branch: `main` / `docs` → Save.**

Live at: **https://sbertini-tgi.github.io/1000WATT-steamboat-web-mockup/**
(the framework page at `…/content-mapping-framework.html`).
