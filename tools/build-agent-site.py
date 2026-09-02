#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build-agent-site — turn one agent's content.json into a static 1000WATT site.

    python3 tools/build-agent-site.py docs/lauren-bloom/content.json

The JSON carries *only content*: no markup, no class names, no layout. Every
section is one entry in `pages[].blocks` with a `type` drawn from the closed
registry below, which mirrors the block catalogue in /agent-site-sections.md.
Porting another agent means copying the JSON, swapping the copy, and running
this again — no HTML and no CSS.

Three conveniences keep the JSON short:

  * `shared` blocks + `{"type": "$name"}` references, for the sections that
    repeat on every page (the closing band, the contact form, the quicklinks
    row). Declared once, used everywhere.
  * `{{agent.first}}`-style interpolation, so "Work with Lauren" / "Ask Lauren
    a question" / "Send to Lauren" are one template string that works
    unchanged for the next agent.
  * a per-block `bg` of cream / white / dark, so rhythm is a content decision
    rather than a code change.

Copy is treated as trusted authored HTML — write &mdash;, &reg; and <strong>
straight into the JSON.

Generated pages carry stable #s-* ids and data-review labels, so the section
review overlay (docs/js/review.js) works on them exactly as on the brokerage
pages. Re-run tools/review-manifest.py afterwards to list them in review.html.
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

STOP = ("the", "a", "an", "of", "and", "to", "for", "with", "on", "in", "my", "your")


def slugify(s, maxwords=4):
    s = re.sub(r"<[^>]+>", " ", s or "")
    s = s.lower().replace("’", "").replace("'", "").replace("&amp;", " and ")
    s = re.sub(r"&[a-z]+;", " ", s)
    s = re.sub(r"[^a-z0-9\s-]", " ", s)
    words = [w for w in s.split() if w not in STOP]
    return "-".join(words[:maxwords]) or "block"


# ---------------------------------------------------------------- templating
class Ctx(dict):
    """Interpolation source for {{agent.first}} and friends."""

    def resolve(self, path):
        cur = self
        for part in path.split("."):
            if not isinstance(cur, dict) or part not in cur:
                raise KeyError(path)
            cur = cur[part]
        return cur


TOKEN = re.compile(r"\{\{\s*([a-zA-Z0-9_.]+)\s*\}\}")


def T(value, ctx):
    """Interpolate {{…}} through any nested structure."""
    if isinstance(value, str):
        return TOKEN.sub(lambda m: str(ctx.resolve(m.group(1))), value)
    if isinstance(value, list):
        return [T(v, ctx) for v in value]
    if isinstance(value, dict):
        return {k: T(v, ctx) for k, v in value.items()}
    return value


# ---------------------------------------------------------------- fragments
ARROW = '<span aria-hidden="true">&rarr;</span>'

# .search__icon and .vid__play svg carry the sizing; without a class an inline
# SVG with only a viewBox expands to fill its flex parent.
ICON_SEARCH = (
    '<svg class="search__icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
    'stroke-width="1.4" aria-hidden="true">'
    '<circle cx="11" cy="11" r="7"/><path d="M20 20l-4.2-4.2"/></svg>'
)
ICON_PLAY = '<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M8 5l12 7-12 7z"/></svg>'


def actions(items, light=False):
    """A row of CTAs: the first is a pill, the rest are gold text links."""
    out = []
    for i, a in enumerate(items or []):
        cls = "pill-btn pill-btn--light" if (light and i == 0) else "pill-btn"
        if i == 0:
            out.append(f'<a class="{cls}" href="{a["href"]}">{a["label"]} {ARROW}</a>')
        else:
            link = "link-gold link-gold--bright" if light else "link-gold"
            out.append(f'<a class="{link}" href="{a["href"]}">{a["label"]} {ARROW}</a>')
    return "".join(out)


def facts(items, dark=False):
    k, v = ("agentfacts__k", "agentfacts__v") if dark else ("afacts__k", "afacts__v")
    lis = "".join(
        f'<li><span class="{k}">{f["label"]}</span>'
        f'<span class="{v}">{f["value"]}</span></li>'
        for f in items or []
    )
    return f'<ul class="{"agentfacts" if dark else "afacts"}">{lis}</ul>'


def eyebrow(block, bright=False):
    if not block.get("eyebrow"):
        return ""
    cls = "eyebrow eyebrow--bright" if bright else "eyebrow"
    return f'<p class="{cls}">{block["eyebrow"]}</p>'


def heading(block, tag="h2", cls="h2"):
    if not block.get("title"):
        return ""
    return f'<{tag} class="{cls}">{block["title"]}</{tag}>'


def lede(block, key="lede"):
    return f'<p class="lede">{block[key]}</p>' if block.get(key) else ""


def paragraphs(block):
    ps = "".join(f"<p>{p}</p>" for p in block.get("paragraphs", []))
    return f'<div class="prose">{ps}</div>' if ps else ""


def sec_head(block, more=None):
    """Eyebrow + heading on the left, an optional link on the right."""
    right = (
        f'<a class="link-gold" href="{more["href"]}">{more["label"]} {ARROW}</a>'
        if more
        else ""
    )
    return (
        f'<div class="sec-head"><div>{eyebrow(block)}{heading(block)}</div>{right}</div>'
    )


# ---------------------------------------------------------------- blocks
BLOCKS = {}


def block(name, bg="cream"):
    def wrap(fn):
        fn.default_bg = bg
        BLOCKS[name] = fn
        return fn

    return wrap


@block("hero", bg=None)
def b_hero(b, site):
    search = ""
    if b.get("search"):
        s = b["search"]
        search = (
            f'<a class="hero__search" href="{s["href"]}">{ICON_SEARCH}'
            f'<span>{s["placeholder"]}</span><em>{s["label"]}</em></a>'
        )
    acts = ""
    if b.get("actions"):
        btns = []
        for i, a in enumerate(b["actions"]):
            cls = "pill-btn pill-btn--gold" if i == 0 else "pill-btn"
            btns.append(f'<a class="{cls}" href="{a["href"]}">{a["label"]} {ARROW}</a>')
        acts = f'<div class="hero__actions">{"".join(btns)}</div>'
    return (
        f'<img class="hero__bg" src="{b["image"]}" alt="{b.get("alt","")}" />'
        f'<div class="hero__scrim"></div>'
        f"{nav_html(site, on_hero=True)}"
        f'<div class="hero__inner">'
        f"{eyebrow(b, bright=True)}"
        f'<h1 class="h1 hero__title">{b["title"]}</h1>'
        f"{lede(b)}{acts}{search}"
        f"</div>"
    )


@block("pagehead", bg=None)
def b_pagehead(b, site):
    crumb = ""
    if b.get("crumb"):
        crumb = (
            f'<a class="crumb" href="{b["crumb"]["href"]}">'
            f'<span>&larr;</span> {b["crumb"]["label"]}</a>'
        )
    return (
        f"{nav_html(site)}"
        f'<div class="pagehead__inner">{crumb}'
        f"{eyebrow(b, bright=True)}{heading(b, 'h1')}{lede(b)}"
        f"</div>"
    )


@block("gallery", bg=None)
def b_gallery(b, site):
    """Property photography: one lead image and a stack beside it."""
    side = "".join(
        f'<div class="g-item"><img src="{x["src"]}" alt="{x["alt"]}" loading="lazy" /></div>'
        for x in b.get("side", [])
    )
    count = f'<span class="g-count">{b["count"]}</span>' if b.get("count") else ""
    return (
        f'<div class="gallery">'
        f'<div class="gallery__main"><div class="g-item">'
        f'<img src="{b["main"]["src"]}" alt="{b["main"]["alt"]}" />{count}'
        f"</div></div>"
        f'<div class="gallery__side">{side}</div>'
        f"</div>"
    )


@block("listing-detail", bg="cream")
def b_listing_detail(b, site):
    """A single property: price head, spec strip, copy, MLS table, agent card."""
    specs = "".join(
        f'<div class="spec"><div class="spec__v">{x["v"]}</div>'
        f'<div class="spec__k">{x["k"]}</div></div>'
        for x in b["specs"]
    )
    rows = "".join(f"<tr><td>{k}</td><td>{v}</td></tr>" for k, v in b["details"])
    hist = "".join(
        f'<li>{h["price"]} <span>{h["date"]}</span></li>' for h in b.get("history", [])
    )
    hist_block = (
        f'<div style="margin-top:clamp(40px,5vw,64px)">'
        f'<p class="eyebrow">Price history</p>'
        f'<ul class="pricehist">{hist}</ul></div>'
        if hist else ""
    )
    map_block = (
        f'<div style="margin-top:clamp(40px,5vw,64px)">'
        f'<p class="eyebrow">Location</p>'
        f'<div class="ph map-ph" data-label="{b["map"]}"></div></div>'
        if b.get("map") else ""
    )
    note = f'<p class="mls-note">{b["note"]}</p>' if b.get("note") else ""
    a = b["agent"]
    fields = "".join(
        f'<div class="field"><label for="{f["id"]}">{f["label"]}</label>'
        + (f'<textarea id="{f["id"]}" placeholder="{f.get("placeholder","")}"></textarea>'
           if f["kind"] == "textarea" else
           f'<input id="{f["id"]}" type="{f["kind"]}" placeholder="{f.get("placeholder","")}" />')
        + "</div>"
        for f in a["fields"]
    )
    return (
        f'<div class="phead"><div>'
        f'<p class="phead__status">{b["status"]}</p>'
        f'<h1 class="h2">{b["title"]}</h1>'
        f'<p class="phead__city">{b["city"]}</p></div>'
        f'<div class="phead__right">'
        f'<div class="phead__price">{b["price"]}</div>'
        f'<a class="pill-btn" href="{b["action"]["href"]}">{b["action"]["label"]} {ARROW}</a>'
        f"</div></div>"
        f'<div class="specstrip">{specs}</div>'
        f'<div class="propcols" style="margin-top:clamp(40px,5vw,66px)"><div>'
        f'{eyebrow(b)}'
        f'<h2 class="h3" style="margin:16px 0 22px">{b["heading"]}</h2>'
        f'{paragraphs(b)}{note}'
        f'<div style="margin-top:clamp(40px,5vw,64px)">'
        f'<p class="eyebrow">Details</p><table class="dtable">{rows}</table></div>'
        f"{hist_block}{map_block}</div>"
        f'<aside class="agentcard" id="showing">'
        f'<div class="agentcard__top">'
        f'<div class="agentcard__photo"><img src="{a["photo"]}" alt="{a["name"]}" /></div><div>'
        f'<span class="agentcard__k">Listed by</span>'
        f'<a class="agentcard__name" href="{a["href"]}">{a["name"]}</a>'
        f'<span class="agentcard__role">{a["role"]}</span></div></div>'
        f'<p>{a["blurb"]}</p>'
        f'<form class="form" onsubmit="return false">{fields}'
        f'<div class="form__submit">'
        f'<button class="pill-btn" type="submit">{a["submit"]} {ARROW}</button></div></form>'
        f'<span class="agentcard__tel">{a["tel"]}</span>'
        f"</aside></div>"
    )


@block("agent-intro", bg="cream")
def b_agent_intro(b, site):
    rev = " aintro--rev" if b.get("reverse") else ""
    role = f'<p class="aintro__role">{b["role"]}</p>' if b.get("role") else ""
    acts = (
        f'<div class="aintro__actions">{actions(b["actions"])}</div>'
        if b.get("actions")
        else ""
    )
    fx = facts(b["facts"]) if b.get("facts") else ""
    # Family B agents often supply a cut-out headshot on a plain studio ground.
    # Cropping that to fill a 4:5 frame decapitates it, so `fit: "contain"`
    # letterboxes it against the studio colour instead.
    fit = " aintro__photo--contain" if b.get("fit") == "contain" else ""
    return (
        f'<div class="aintro{rev}">'
        f'<div><div class="aintro__photo{fit}">'
        f'<img src="{b["image"]}" alt="{b.get("alt","")}" /></div>{role}</div>'
        f'<div class="aintro__copy">{eyebrow(b)}{heading(b)}'
        f"{paragraphs(b)}{fx}{acts}</div>"
        f"</div>"
    )


@block("agent-header", bg=None)
def b_agent_header(b, site):
    """Dark portrait header — the About page's opener."""
    crumb = ""
    if b.get("crumb"):
        crumb = (
            f'<a class="crumb" href="{b["crumb"]["href"]}">'
            f'<span>&larr;</span> {b["crumb"]["label"]}</a>'
        )
    acts = (
        f'<div class="agenthead__actions">{actions(b["actions"], light=True)}</div>'
        if b.get("actions")
        else ""
    )
    return (
        f"{nav_html(site)}"
        f'<div class="pagehead__inner agenthead">{crumb}'
        f'<div class="agenthead__grid">'
        f'<div class="agenthead__photo'
        f'{" agenthead__photo--contain" if b.get("fit") == "contain" else ""}">'
        f'<img src="{b["image"]}" alt="{b.get("alt","")}" /></div>'
        f'<div class="agenthead__body">{eyebrow(b, bright=True)}'
        f'<h1 class="h2">{b["title"]}</h1>'
        f'{f"""<p class="agenthead__lede">{b["lede"]}</p>""" if b.get("lede") else ""}'
        f'{facts(b["facts"], dark=True) if b.get("facts") else ""}'
        f"{acts}</div></div></div>"
    )


@block("prose", bg="cream")
def b_prose(b, site):
    return (
        f'<div class="lead-grid"><div class="lead-head">'
        f"{eyebrow(b)}{heading(b)}{lede(b)}</div>"
        f"<div>{paragraphs(b)}{ _list_extras(b) }</div></div>"
    )


def _list_extras(b):
    if not b.get("checks"):
        return ""
    lis = "".join(f"<li>{c}</li>" for c in b["checks"])
    return f'<ul class="checks">{lis}</ul>'


@block("stats", bg="white")
def b_stats(b, site):
    cells = "".join(
        f'<div class="stat"><div class="stat__n">{s["n"]}</div>'
        f'<div class="stat__l">{s["label"]}</div></div>'
        for s in b["items"]
    )
    cols = len(b["items"])
    head = f"{eyebrow(b)}{heading(b)}{lede(b)}"
    return f'{head}<div class="stats stats--{cols}">{cells}</div>'


@block("creds", bg="dark")
def b_creds(b, site):
    lis = "".join(f'<li><b>{c["year"]}</b><span>{c["text"]}</span></li>' for c in b["items"])
    return (
        f'<div class="lead-grid"><div class="lead-head">{eyebrow(b)}{heading(b)}{lede(b)}</div>'
        f'<div><ul class="creds">{lis}</ul></div></div>'
    )


@block("testimonials", bg="white")
def b_testimonials(b, site):
    layout = b.get("layout", "slider")
    # `place` is optional: Lauren's reviews carry a submarket ("Hayden Seller"),
    # Ashley's carry only a role, and some feeds carry neither.
    cards = "".join(
        f'<figure class="quote"><div class="quote__mark">&ldquo;</div>'
        f'<blockquote class="quote__body">{q["quote"]}</blockquote>'
        f'<figcaption class="quote__by">'
        f'<span class="quote__name">{q["name"]}</span>'
        f'{f"""<span class="quote__place">{q["place"]}</span>""" if q.get("place") else ""}'
        f"</figcaption></figure>"
        for q in b["items"]
    )
    more = b.get("more")
    return (
        f"{sec_head(b, more)}{lede(b)}"
        f'<div class="quotes quotes--{layout}">{cards}</div>'
    )


def _listing(item):
    chip_cls = {
        "Sold": "listing__chip listing__chip--sold",
        "Pending": "listing__chip listing__chip--pending",
    }.get(item["status"], "listing__chip")
    img = (
        f'<img src="{item["image"]}" alt="{item["address"]}" loading="lazy" />'
        if item.get("image")
        else ""
    )
    inner_img = f'<div class="listing__img ph" data-label="Listing photo">' if not img else '<div class="listing__img">'
    go = (
        f'<span class="listing__go">View listing {ARROW}</span>'
        if item.get("href")
        else ""
    )
    body = (
        f'<div class="listing__body">'
        f'<span class="listing__price">{item["price"]}</span>'
        f'{f"""<span class="listing__specs">{item["specs"]}</span>""" if item.get("specs") else ""}'
        f'<span class="listing__addr">{item["address"]}</span>'
        f'<span class="listing__rep">{item["rep"]}</span>{go}</div>'
    )
    card = (
        f'{inner_img}<span class="{chip_cls}">{item["status"]}</span>{img}</div>{body}'
    )
    sold = " listing--sold" if item["status"] == "Sold" else ""
    if item.get("href"):
        return f'<a class="listing{sold}" href="{item["href"]}">{card}</a>'
    return f'<article class="listing{sold}">{card}</article>'


@block("listings", bg="white")
def b_listings(b, site):
    groups = b.get("groups") or [{"label": "", "items": b["items"]}]
    note = f'<p class="mls-note">{b["note"]}</p>' if b.get("note") else ""
    head = sec_head(b, b.get("more"))
    if len(groups) == 1:
        grid = f'<div class="listings">{"".join(_listing(i) for i in groups[0]["items"])}</div>'
        return f"{head}{note}{grid}"
    gid = slugify(b.get("title") or "listings")
    tabs, panels = [], []
    for i, g in enumerate(groups):
        pid = f"{gid}-{slugify(g['label'], 2)}"
        active = " is-active" if i == 0 else ""
        tabs.append(
            f'<button class="tab{active}" type="button" role="tab" '
            f'aria-controls="{pid}" aria-selected="{"true" if i == 0 else "false"}">'
            f'{g["label"]}<span class="tab__n">{len(g["items"])}</span></button>'
        )
        panels.append(
            f'<div class="tabpanel" id="{pid}" role="tabpanel"{"" if i == 0 else " hidden"}>'
            f'<div class="listings">{"".join(_listing(x) for x in g["items"])}</div></div>'
        )
    return (
        f"{head}{note}"
        f'<div class="tabs" role="tablist" data-tabs>{"".join(tabs)}</div>'
        f'{"".join(panels)}'
    )


@block("search", bg="cream")
def b_search(b, site):
    pills = "".join(
        f'<a class="filter" href="{f["href"]}">{f["label"]} <span>&rsaquo;</span></a>'
        for f in b.get("filters", [])
    )
    return (
        f"{eyebrow(b)}{heading(b)}{lede(b)}"
        f'<form class="searchbar" onsubmit="return false">'
        f'<span class="searchbar__input">{ICON_SEARCH}'
        f'<input type="search" aria-label="Search listings" placeholder="{b["placeholder"]}" /></span>'
        f"{pills}"
        f'<button class="pill-btn" type="submit">{b.get("submit","Search")} {ARROW}</button>'
        f"</form>"
        f'{f"""<p class="mls-note">{b["note"]}</p>""" if b.get("note") else ""}'
    )


@block("quicklinks", bg="cream")
def b_quicklinks(b, site):
    cards = "".join(
        f'<a class="guide" href="{c["href"]}">'
        f'<p class="guide__cat">{c["k"]}</p>'
        f'<h3 class="guide__title">{c["title"]}</h3>'
        f'<p class="guide__body">{c["desc"]}</p>'
        f'<span class="link-gold">{c.get("cta","Read it")} {ARROW}</span></a>'
        for c in b["items"]
    )
    # A class, not an inline style: inline styles beat the responsive media
    # queries and would strand a three-up row on a phone.
    cols = len(b["items"])
    return (
        f'<div class="guides__grid"><div class="guides__lead">'
        f"{eyebrow(b)}{heading(b)}{lede(b)}</div>"
        f'<div class="guide-cards guide-cards--{cols}">{cards}</div></div>'
    )


@block("neighborhoods", bg="cream")
def b_neighborhoods(b, site):
    cards = "".join(
        f'<a class="comm" href="{n["href"]}">'
        f'<div class="comm__img"><img src="{n["image"]}" alt="{n["name"]}" loading="lazy" /></div>'
        f'<div class="comm__body"><h3 class="comm__name">{n["name"]}</h3>'
        f'<p class="comm__blurb">{n["blurb"]}</p></div></a>'
        for n in b["items"]
    )
    return f'{sec_head(b, b.get("more"))}{lede(b)}<div class="commgrid">{cards}</div>'


@block("steps", bg="white")
def b_steps(b, site):
    lis = "".join(
        f'<li class="step"><div class="step__n">{i+1:02d}</div>'
        f'<div class="step__b"><h3>{s["title"]}</h3><p>{s["body"]}</p></div></li>'
        for i, s in enumerate(b["steps"])
    )
    return f'{eyebrow(b)}{heading(b)}{lede(b)}<ol class="steps">{lis}</ol>'


@block("valuation", bg="dark")
def b_valuation(b, site):
    lis = "".join(f"<li>{p}</li>" for p in b["points"])
    return (
        f'<div class="val__grid"><div>{eyebrow(b)}{heading(b)}{lede(b)}</div>'
        f'<div><ul class="checks">{lis}</ul>'
        f'<div class="agenthead__actions">{actions(b["actions"], light=True)}</div>'
        f"</div></div>"
    )


@block("directory", bg="white")
def b_directory(b, site):
    groups = []
    for g in b["groups"]:
        lis = "".join(
            f'<li><a class="dir__link" href="{v["href"]}" target="_blank" rel="noopener">'
            f'<span class="dir__co">{v["name"]}</span>'
            f'<span class="dir__go">{v.get("note","Visit")} {ARROW}</span></a></li>'
            for v in g["items"]
        )
        groups.append(
            f'<div class="dir__group"><div class="dir__head">'
            f'<h3 class="dir__name">{g["name"]}</h3>'
            f'<span class="dir__count">{len(g["items"])} '
            f'{"listing" if len(g["items"]) == 1 else "options"}</span></div>'
            f'<ul class="dir__list">{lis}</ul></div>'
        )
    return f'{eyebrow(b)}{heading(b)}{lede(b)}<div class="dir">{"".join(groups)}</div>'


@block("videos", bg="cream")
def b_videos(b, site):
    cards = "".join(
        f'<a class="vid" href="{v["href"]}" target="_blank" rel="noopener">'
        f'<div class="vid__frame ph" data-label="">'
        f'<span class="vid__play">{ICON_PLAY}</span></div>'
        f'<div class="vid__body"><span class="vid__meta">{v["meta"]}</span>'
        f'<span class="vid__title">{v["title"]}</span></div></a>'
        for v in b["items"]
    )
    return f'{sec_head(b, b.get("more"))}{lede(b)}<div class="vids">{cards}</div>'


@block("posts", bg="white")
def b_posts(b, site):
    """Editorial. Some agents publish; most link to the brokerage blog instead."""
    cards = "".join(
        f'<article class="post">'
        f'<p class="post__cat">{a["cat"]}</p>'
        f'<h3 class="post__title"><a href="{a["href"]}"'
        f'{" target=_blank rel=noopener" if a["href"].startswith("http") else ""}>{a["title"]}</a></h3>'
        f'<p class="post__date">{a["date"]}</p>'
        f'<p class="post__excerpt">{a["excerpt"]}</p>'
        f'<a class="post__more" href="{a["href"]}"'
        f'{" target=_blank rel=noopener" if a["href"].startswith("http") else ""}>'
        f"Continue reading {ARROW}</a></article>"
        for a in b["items"]
    )
    return f'{sec_head(b, b.get("more"))}{lede(b)}<div class="blog-grid">{cards}</div>'


@block("locals", bg="dark")
def b_locals(b, site):
    lis = "".join(
        f'<li><span class="locals__k">{l["k"]}</span>'
        f'<span class="locals__v">{l["v"]}</span></li>'
        for l in b["items"]
    )
    return f'{eyebrow(b)}{heading(b)}{lede(b)}<ul class="locals">{lis}</ul>'


@block("calculator", bg="cream")
def b_calculator(b, site):
    return (
        f"{eyebrow(b)}{heading(b)}{lede(b)}"
        f'<form class="calc" data-calc onsubmit="return false">'
        f'<div class="calc__fields">'
        f'<div class="field"><label for="calc-price">Home price</label>'
        f'<input id="calc-price" data-calc-price type="text" inputmode="numeric" value="{b["price"]}" /></div>'
        f'<div class="field"><label for="calc-down">Down payment (%)</label>'
        f'<input id="calc-down" data-calc-down type="text" inputmode="decimal" value="{b["down"]}" /></div>'
        f'<div class="field"><label for="calc-rate">Interest rate (%)</label>'
        f'<input id="calc-rate" data-calc-rate type="text" inputmode="decimal" value="{b["rate"]}" /></div>'
        f'<div class="field"><label for="calc-term">Term (years)</label>'
        f'<input id="calc-term" data-calc-term type="text" inputmode="numeric" value="{b["term"]}" /></div>'
        f"</div>"
        f'<div class="calc__out"><span class="calc__k">Estimated monthly principal &amp; interest</span>'
        f'<p class="calc__pay" data-calc-pay>&mdash;</p>'
        f'<ul class="calc__rows">'
        f'<li><span>Loan amount</span><b data-calc-loan>&mdash;</b></li>'
        f'<li><span>Down payment</span><b data-calc-dp>&mdash;</b></li>'
        f'<li><span>Total interest</span><b data-calc-int>&mdash;</b></li>'
        f"</ul></div></form>"
        f'{f"""<p class="mls-note">{b["note"]}</p>""" if b.get("note") else ""}'
    )


@block("newsletter", bg="dark")
def b_newsletter(b, site):
    return (
        f'<div class="lead-grid"><div class="lead-head">{eyebrow(b)}{heading(b)}{lede(b)}</div>'
        f'<div><form class="form" onsubmit="return false">'
        f'<div class="field"><label for="nl-name">First name</label>'
        f'<input id="nl-name" type="text" placeholder="Optional" /></div>'
        f'<div class="field"><label for="nl-email">Email *</label>'
        f'<input id="nl-email" type="email" placeholder="you@email.com" /></div>'
        f'<div class="form__submit">'
        f'<button class="pill-btn pill-btn--light" type="submit">{b.get("submit","Subscribe")} {ARROW}</button></div>'
        f'<p class="form__consent">{b["disclosure"]}</p>'
        f"</form></div></div>"
    )


@block("band", bg=None)
def b_band(b, site):
    return (
        f'<img class="band__bg" src="{b["image"]}" alt="" />'
        f'<div class="band__scrim"></div>'
        f'<div class="container">{eyebrow(b, bright=True)}{heading(b)}{lede(b)}'
        f'<div class="band__actions">{actions(b["actions"], light=True)}</div></div>'
    )


@block("form", bg="cream")
def b_form(b, site):
    fields = []
    for f in b["fields"]:
        fid = "f-" + slugify(f["label"], 3)
        full = " field--full" if f.get("full") else ""
        req = " *" if f.get("required") else ""
        if f["kind"] == "textarea":
            ctrl = f'<textarea id="{fid}" placeholder="{f.get("placeholder","")}"></textarea>'
        elif f["kind"] == "select":
            opts = "".join(f'<option>{o}</option>' for o in f["options"])
            ctrl = (
                f'<select id="{fid}"><option value="" disabled selected>'
                f'{f.get("placeholder","Choose one")}</option>{opts}</select>'
            )
        else:
            ctrl = (
                f'<input id="{fid}" type="{f["kind"]}" '
                f'placeholder="{f.get("placeholder","")}" />'
            )
        fields.append(
            f'<div class="field{full}"><label for="{fid}">{f["label"]}{req}</label>{ctrl}</div>'
        )
    consent = (
        f'<p class="form__consent">{b["disclosure"]}</p>' if b.get("disclosure") else ""
    )
    return (
        f'<div class="container"><div class="inquire__grid"><div class="inquire__intro">'
        f"{eyebrow(b)}{heading(b)}{lede(b)}"
        f'{facts(b["facts"]) if b.get("facts") else ""}</div>'
        f'<form class="form" onsubmit="return false">{"".join(fields)}'
        f'<div class="form__submit">'
        f'<button class="pill-btn" type="submit">{b["submit"]} {ARROW}</button></div>'
        f"{consent}</form></div></div>"
    )


# ---------------------------------------------------------------- chrome
def nav_html(site, on_hero=False):
    links = "".join(
        f'<a href="{l["href"]}">{l["label"]}</a>' for l in site["nav"]
    )
    a = site["agent"]
    return (
        f'<nav class="nav">'
        f'<div class="nav__brand">'
        f'<a href="{site["home"]}"><img class="nav__logo" src="../assets/svg/logo.svg" alt="The Group" /></a>'
        f'<span class="nav__rule"></span>'
        f'<a class="nav__agent" href="index.html">{a["name"]}</a>'
        f"</div>"
        f'<div class="nav__links">{links}</div>'
        f'<a class="nav__tel" href="tel:{a["tel"]}">{a["phone"]}</a>'
        f"</nav>"
    )


def footer_html(site):
    a = site["agent"]
    f_ = site["footer"]
    cols = "".join(
        f'<div class="footer__col">{facts(c["facts"])}</div>' for c in f_["columns"]
    )
    links = "".join(f'<a href="{l["href"]}">{l["label"]}</a>' for l in f_["links"])
    social = "".join(
        f'<a href="{s["href"]}" target="_blank" rel="noopener">{s["label"]}</a>'
        for s in f_.get("social", [])
    )
    return (
        f'<footer class="footer footer--home" id="footer" data-review="Footer">'
        f'<div class="footer__box">'
        f'<div class="footer__agent">'
        f'<div class="footer__lock">'
        f'<p class="footer__name">{a["name"]}</p>'
        f'<span class="footer__role">{a["role"]}</span></div>'
        f"{cols}"
        f'{f"""<div class="footer__col"><span class="afacts__k">Follow</span>"""
          f"""<div class="footer__social" style="margin-top:12px">{social}</div></div>""" if social else ""}'
        f"</div>"
        f'<hr class="footer__rule" />'
        f'<div class="footer__inner">{links}</div>'
        f'<hr class="footer__rule" />'
        f'<div class="footer__fine">'
        f'<p class="footer__copy">{f_["copyright"]}</p>'
        f'<p class="footer__disc">{f_["disclaimer"]}</p>'
        f"</div></div></footer>"
    )


# ---------------------------------------------------------------- assembly
BG_CLASS = {"cream": "bg-cream", "white": "bg-white", "dark": "bg-dark"}

# Blocks that are their own full-bleed wrapper rather than a .section.
WRAPPERS = {
    "hero": ("header", "hero"),
    "pagehead": ("div", "pagehead"),
    "agent-header": ("div", "pagehead"),
    "band": ("section", "band"),
    "form": ("section", "section inquire"),
    "gallery": ("div", "bg-cream"),
}

# Blocks in WRAPPERS render their own inner wrapper, so render_block must not
# add the automatic .container — the renderer is responsible for it.


def render_block(b, site, seen):
    kind = b["type"]
    if kind not in BLOCKS:
        raise SystemExit(f"unknown block type: {kind!r}")
    fn = BLOCKS[kind]
    inner = fn(b, site)

    label = b.get("label") or re.sub(r"<[^>]+>", "", b.get("eyebrow") or b.get("title") or kind)
    label = re.sub(r"\s+", " ", label).strip()
    bid = b.get("id") or "s-" + slugify(label)
    n = 2
    while bid in seen:
        bid, n = f"{bid}-{n}", n + 1
    seen.add(bid)

    tag, cls = WRAPPERS.get(kind, (None, None))
    if tag is None:
        bg = b.get("bg", fn.default_bg) or "cream"
        tag, cls = "section", f"section {BG_CLASS[bg]}"
        inner = f'<div class="container">{inner}</div>'
    elif b.get("bg"):
        cls = f"{cls} {BG_CLASS[b['bg']]}"
    if kind == "pagehead" and b.get("slim"):
        cls = f"{cls} pagehead--slim"
    if kind == "listing-detail":
        cls = cls.replace("section ", "section section--pdetail ", 1)
    attrs = f' id="{bid}" data-review="{label}"'
    return f"  <{tag} class=\"{cls}\"{attrs}>\n{inner}\n  </{tag}>\n"


HEAD = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <meta name="robots" content="noindex, nofollow, noarchive, noimageindex" />
  <title>{title}</title>
  <meta name="description" content="{desc}" />
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Marcellus&family=Inter:wght@300;400;500&display=swap" rel="stylesheet" />
  <link rel="stylesheet" href="../css/styles.css" />
  <link rel="stylesheet" href="../css/guide-page.css" />
  <link rel="stylesheet" href="../css/agent-site.css" />
  <link rel="stylesheet" href="../css/review.css" />
</head>
<body>

"""

TAIL = """
  <script src="js/agent-site.js" defer></script>
  <!-- Review overlay: add ?review=1 to any page to switch it on -->
  <script src="../js/review-manifest.js" defer></script>
  <script src="../js/review.js" defer></script>

</body>
</html>
"""


def build(path):
    with open(path, encoding="utf-8") as fh:
        raw = json.load(fh)

    ctx = Ctx({"agent": raw["agent"], "site": raw.get("site", {})})
    site = T({k: v for k, v in raw.items() if k != "pages"}, ctx)
    shared = site.get("shared", {})
    outdir = os.path.dirname(os.path.abspath(path))

    written = []
    for page in raw["pages"]:
        page = T(page, ctx)
        seen = set()
        body = []
        for b in page["blocks"]:
            if b["type"].startswith("$"):
                ref = shared.get(b["type"][1:])
                if ref is None:
                    raise SystemExit(f'unknown shared block: {b["type"]}')
                b = {**ref, **{k: v for k, v in b.items() if k != "type"}}
            body.append(render_block(b, site, seen))
        html = (
            HEAD.format(title=page["title"], desc=page.get("desc", ""))
            + "".join(body)
            + footer_html(site)
            + TAIL
        )
        dest = os.path.join(outdir, page["file"])
        with open(dest, "w", encoding="utf-8") as fh:
            fh.write(html)
        written.append((page["file"], len(page["blocks"])))

    rel = os.path.relpath(outdir, ROOT)
    print(f"{rel}/ — {len(written)} pages")
    for f, n in written:
        print(f"  {f:<26} {n} blocks")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: build-agent-site.py <path/to/content.json>")
    build(sys.argv[1])
