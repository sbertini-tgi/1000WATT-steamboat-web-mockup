#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
review-manifest — wire the section review overlay into the mockup.

Run from the repo root, any time sections are added, removed or renamed:

    python3 tools/review-manifest.py

For every page under docs/ (mapping documents and review.html excluded) it:

  1. finds each reviewable block — <section>, the hero <header>, the
     .pagehead bar and the <footer>;
  2. gives it a stable, human-readable id (#s-my-listings) unless it already
     has one, plus data-review="My Listings" for the label the team sees;
  3. makes sure the page links css/review.css and loads js/review.js;
  4. rewrites docs/js/review-manifest.js, which drives review.html.

Safe to re-run: ids that already exist are left alone and nothing is
double-injected. Labels come from each block's eyebrow, falling back to its
heading; OVERRIDE_BY_INDEX below fixes the handful that read badly.
"""
import re, os, io, json, glob, html

DOCS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs")
SKIP = {"review.html", "mapping-guide.html", "steamboat-to-1000watt-mapping.html",
        "noco-to-1000watt-mapping.html", "steamboat-to-noco-mapping.html"}

OPEN_RE = re.compile(r'<(?P<tag>section|header|footer|div)(?P<attrs>\s[^>]*)?>', re.I)
TEXT_RE = re.compile(r"<[^>]+>")
EYEBROW_RE = re.compile(r'<p class="eyebrow[^"]*"[^>]*>(.*?)</p>', re.I | re.S)
HEAD_RE = re.compile(r'<h[1-3][^>]*>(.*?)</h[1-3]>', re.I | re.S)

# Labels that need a human touch (block class/eyebrow -> label)
# Blocks whose auto-derived label reads badly get a human one.
OVERRIDE_BY_INDEX = {
    ("index.html", 0): "Hero",
    ("index.html", 3): "The People",
    ("index.html", 9): "Awards",
    ("index.html", 7): "GroupGives",
    ("property-search.html", 1): "Listing results",
    ("search/commercial.html", 2): "Listing results",
    ("communities.html", 2): "Neighborhoods",
    ("contact.html", 1): "Office locations",
    ("blog.html", 1): "Story grid",
    ("readme.html", 1): "Guide index",
    ("property-2175-bear-drive.html", 1): "Listing detail",
    ("property-1382-skyview-lane.html", 1): "Listing detail",
    ("property-33855-canyon-court.html", 1): "Listing detail",
    ("about-the-group-steamboat.html", 4): "Our Offices",
}
OVERRIDE = {}

def clean(t):
    return re.sub(r"\s+", " ", html.unescape(TEXT_RE.sub(" ", t))).strip()

STOP = ("the","a","an","of","and","to","for","with","on","in")
def slugify(s, maxwords=3):
    s = s.lower().replace("\u2019", "").replace("'", "").replace("&", " and ")
    s = re.sub(r"[^a-z0-9\s-]", " ", s)
    words = [w for w in s.split() if w not in STOP]
    return "-".join(words[:maxwords]) or "block"

def classes_of(attrs):
    m = re.search(r'class="([^"]*)"', attrs or "")
    return m.group(1).split() if m else []

def reviewable(tag, attrs):
    tag, cl = tag.lower(), classes_of(attrs)
    if tag == "section": return True
    if tag == "header" and ({"hero","ihero"} & set(cl)): return True
    if tag == "footer" and "footer" in cl: return True
    if tag == "div" and "pagehead" in cl: return True
    return False

ROBOTS = '<meta name="robots" content="noindex, nofollow, noarchive, noimageindex" />'
NOINDEX = "  %s\n" % ROBOTS
VIEWPORT_RE = re.compile(r'^\s*<meta name="viewport"[^>]*>\n', re.M)
ROBOTS_RE = re.compile(r'<meta name="robots"[^>]*>')

def stamp_noindex():
    """Keep every page in docs/ out of the search index.

    This is a public repo published to GitHub Pages, and the mockup carries real
    agents' names, photographs and phone numbers. A robots.txt cannot do the job
    here: crawlers only read it from the host root (sbertini-tgi.github.io/
    robots.txt), which a project-pages repo does not control. The per-page meta
    is therefore the only mechanism that actually applies, so it is enforced
    here rather than left to whoever adds the next page.

    Normalises rather than merely adds: a weaker directive already on a page (a
    bare noindex, say) is replaced, and duplicates are collapsed. Covers every
    .html under docs/, including the pages the review overlay skips and the
    pre-1000watt reference mockup. Writes only on a real change, so it is
    idempotent and safe to run on every invocation.
    """
    n = 0
    for path in sorted(glob.glob(os.path.join(DOCS, "**", "*.html"), recursive=True)):
        src = open(path, encoding="utf-8").read()
        # Strip every existing robots meta, taking its whole line with it.
        out = re.sub(r'^[ \t]*<meta name="robots"[^>]*>[ \t]*\n', "", src, flags=re.M)
        out = ROBOTS_RE.sub("", out)          # any left inline, mid-line
        m = VIEWPORT_RE.search(out)
        if not m:
            print("  ! no <meta viewport> to anchor to:", os.path.relpath(path, DOCS))
            continue
        out = out[:m.end()] + NOINDEX + out[m.end():]
        if out != src:
            open(path, "w", encoding="utf-8").write(out)
            n += 1
    return n


def pages():
    fs = sorted(glob.glob(os.path.join(DOCS, "*.html")))
    fs += sorted(glob.glob(os.path.join(DOCS, "search", "*.html")))
    # Agent sites are any docs/<agent>/ directory holding a content.json — they are
    # generated by tools/build-agent-site.py, which already stamps ids and
    # data-review labels, so they pass through untouched and only get listed in the
    # manifest so review.html can reach them. Discovered, not hardcoded: adding an
    # agent needs no edit here.
    for cj in sorted(glob.glob(os.path.join(DOCS, "*", "content.json"))):
        fs += sorted(glob.glob(os.path.join(os.path.dirname(cj), "*.html")))
    for p in fs:
        if os.path.basename(p) not in SKIP:
            yield os.path.relpath(p, DOCS).replace(os.sep, "/"), p

def analyse(src, name):
    hits = [m for m in OPEN_RE.finditer(src) if reviewable(m.group("tag"), m.group("attrs") or "")]
    out, used = [], set()
    for i, m in enumerate(hits):
        tag, attrs = m.group("tag").lower(), m.group("attrs") or ""
        cl = classes_of(attrs)
        stop = hits[i+1].start() if i + 1 < len(hits) else len(src)
        body = src[m.end():stop]
        existing = re.search(r'\bid="([^"]+)"', attrs)
        existing = existing.group(1) if existing else None

        # --- human label ---
        label = None
        if tag == "header":
            label = "Hero"
        elif tag == "footer":
            label = "Footer"
        elif tag == "div":
            label = "Page header"
        else:
            eb = EYEBROW_RE.search(body)
            hd = HEAD_RE.search(body)
            eb_t = clean(eb.group(1)) if eb else ""
            hd_t = clean(hd.group(1)) if hd else ""
            # an eyebrow of 1-2 words that just repeats the page name is weak; prefer heading then
            label = eb_t if len(eb_t) >= 3 else hd_t
            if not label: label = " ".join(cl[1:2]) or "Section"
        if (name, i) in OVERRIDE_BY_INDEX:
            label = OVERRIDE_BY_INDEX[(name, i)]
        label = label[:48].rstrip(" .,—-")

        # --- id ---
        if existing:
            ident = existing
        else:
            base = "s-" + slugify(label)
            ident, n = base, 2
            while ident in used:
                ident, n = "%s-%d" % (base, n), n + 1
        used.add(ident)
        out.append(dict(id=ident, label=label, tag=tag, new=existing is None,
                        insert_at=m.end() - 1, attrs=attrs))
    return out


TITLES = {
    "index.html": "Home",
    "about-the-group-steamboat.html": "About The Group",
    "blog.html": "Stories",
    "communities.html": "Communities",
    "contact.html": "Contact",
    "how-we-work-with-buyers.html": "How We Work With Buyers",
    "how-we-work-with-sellers.html": "How We Work With Sellers",
    "leading-re.html": "Leading Real Estate Companies",
    "luxury-portfolio-international.html": "Luxury Portfolio International",
    "market-report.html": "Market Report",
    "new-developments.html": "New Developments",
    "privacy-policy.html": "Privacy Policy",
    "property-search.html": "Property Search",
    "readme.html": "Site Guide",
    "real-estate-insider.html": "The Real Estate Insider",
    "search/commercial.html": "Commercial Search",
    "agent-dean-laird.html": "Dean Laird",
    "agent-jon-kowalsky.html": "Jon Kowalsky",
    "agent-martin-dragnev.html": "Martin Dragnev",
    "agent-ashley-walcher.html": "Ashley Walcher",
    "agent-lauren-bloom.html": "Lauren Bloom",
    "agent-matt-eidt.html": "Matt Eidt",
    "property-2175-bear-drive.html": "2175 Bear Drive",
    "property-1382-skyview-lane.html": "1382/1384 Skyview Lane",
    "property-33855-canyon-court.html": "33855 Canyon Court",
}

def agent_dirs():
    return {os.path.basename(os.path.dirname(cj))
            for cj in glob.glob(os.path.join(DOCS, "*", "content.json"))}

AGENT_DIRS = agent_dirs()

PAGE_NAMES = {
    "index.html": "Home", "about.html": "About", "properties.html": "Portfolio",
    "neighborhoods.html": "Neighborhoods", "testimonials.html": "Reviews",
    "buyers.html": "Buyers", "sellers.html": "Sellers",
    "home-valuation.html": "Home Valuation", "resources.html": "Resources",
    "journal.html": "Journal", "contact.html": "Contact",
}

def agent_title(name):
    """"lauren-bloom/about.html" -> "Lauren Bloom — About"."""
    folder, _, page = name.partition("/")
    who = " ".join(w.capitalize() for w in folder.split("-"))
    return "%s \u2014 %s" % (who, PAGE_NAMES.get(page, page[:-5].replace("-", " ").title()))
GROUP = {  # dashboard grouping
    "index.html": "Home", "readme.html": "Home",
    "agent-dean-laird.html": "Agents", "agent-martin-dragnev.html": "Agents",
    "agent-jon-kowalsky.html": "Agents",
    "agent-ashley-walcher.html": "Agents", "agent-lauren-bloom.html": "Agents",
    "agent-matt-eidt.html": "Agents",
    "property-2175-bear-drive.html": "Listings", "property-1382-skyview-lane.html": "Listings",
    "property-33855-canyon-court.html": "Listings", "property-search.html": "Listings",
    "search/commercial.html": "Listings",
}

def attr(s):
    return html.escape(str(s), quote=True)

stamped = stamp_noindex()

manifest, stats = [], {"pages": 0, "blocks": 0, "new_ids": 0}

for name, path in pages():
    src = open(path, encoding="utf-8").read()
    blocks = analyse(src, name)
    if not blocks:
        continue
    prefix = "../" * (name.count("/"))

    # --- stamp attributes, back to front so offsets stay valid ---
    for b in reversed(blocks):
        add = ' data-review="%s"' % attr(b["label"])
        if b["new"]:
            add = ' id="%s"%s' % (b["id"], add)
            stats["new_ids"] += 1
        if 'data-review=' in b["attrs"]:      # idempotent re-runs
            continue
        src = src[:b["insert_at"]] + add + src[b["insert_at"]:]

    # --- stylesheet in <head> ---
    css = '  <link rel="stylesheet" href="%scss/review.css" />\n' % prefix
    if 'css/review.css' not in src:
        m = None
        for m in re.finditer(r'^\s*<link rel="stylesheet"[^>]*>\n', src, re.M):
            pass                                   # last stylesheet link
        if m:
            src = src[:m.end()] + css + src[m.end():]

    # --- scripts before </body> ---
    js = ('\n  <!-- Review overlay: add ?review=1 to any page to switch it on -->\n'
          '  <script src="%sjs/review-manifest.js" defer></script>\n'
          '  <script src="%sjs/review.js" defer></script>\n' % (prefix, prefix))
    if 'js/review.js' not in src:
        src = src.replace('\n</body>', js + '\n</body>', 1)

    open(path, "w", encoding="utf-8").write(src)

    folder = name.partition("/")[0] if "/" in name else ""
    is_agent = folder in AGENT_DIRS
    manifest.append({
        "file": name,
        "title": agent_title(name) if is_agent else TITLES.get(name, name),
        "group": "Agent Sites" if is_agent else GROUP.get(name, "Pages"),
        "blocks": [{"id": b["id"], "label": b["label"]} for b in blocks],
    })
    stats["pages"] += 1
    stats["blocks"] += len(blocks)

order = ["Home", "Agents", "Listings", "Agent Sites", "Pages"]
manifest.sort(key=lambda p: (order.index(p["group"]) if p["group"] in order else 9, p["file"]))

out = io.StringIO()
out.write("/* Generated by tools/review-manifest — every reviewable block on the site.\n")
out.write("   Re-run the generator after adding or renaming a section. */\n")
out.write("window.REVIEW_MANIFEST = ")
out.write(json.dumps({"blocks": stats["blocks"], "pages": manifest}, indent=2, ensure_ascii=False))
out.write(";\n")
open(os.path.join(DOCS, "js", "review-manifest.js"), "w", encoding="utf-8").write(out.getvalue())

print("pages wired: %(pages)d   blocks: %(blocks)d   new ids: %(new_ids)d" % stats)
print("noindex meta stamped on %d page(s)" % stamped)
