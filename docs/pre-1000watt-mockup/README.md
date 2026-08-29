# The Group Real Estate — Website Mock

A static, clickable design mock for the rebranded thegroupinc.com. Open `index.html` directly in a
browser, or serve the folder (`python3 -m http.server`) for best results.

## Pages

| File | Page |
|---|---|
| `index.html` | Homepage — brand-led hero with integrated search |
| `sell.html` | Sell — process, marketing, The Vault, AI, LPI, negotiation |
| `buy.html` | Buy — buyer journey, first-time/new-construction, mortgage, relocation |
| `about.html` | About — Mastery positioning, 50-year timeline, ownership, GroupGives |
| `communities.html` | Communities — featured NoCo towns + full 14-town index + Steamboat |
| `agents.html` | Find an Agent — filterable grid, ownership story |
| `property.html` | Property detail template — 2222 Dominic Ct, Severance (real listing data) |

## Design system

- **Palette:** 2023/24 brand standards — Deep Blue `#003B5C`, Bright Blue `#00AED6`, Ice Cap
  `#00B2A9`, Sunshine `#F1BE48`, Charcoal `#2F2F2C` — executed per the brand book's luxury
  guidance (generous white space, one accent per layout, large photography) with a warm off-white
  `#FAF8F4` influenced by the 1000WATT visual strategy.
- **Type (stand-ins):** Google Fonts **Fraunces** stands in for **Ivy Mode** (headlines) and
  **Archivo** stands in for **Acumin** (UI/body). For production, load the licensed faces via
  Adobe Fonts and swap the two `font-family` tokens in `css/main.css`.
- **Motifs:** Continental Divide ridge-line section dividers (1000WATT); letterspaced micro-labels.
- **Motion:** page-fade view transitions, slow-ease scroll reveals, gentle hero drift, count-up
  stats, restrained hover scaling. Honors `prefers-reduced-motion`.
- **Voice:** 1000WATT messaging platform — "Practiced. Proven. Yours.", Mastery/Ownership/
  Confidence expressions, copy adapted from the Luxury Listing Guide Outline v2 and the Tribus
  staging site.

## Placeholders & sources

- **Listing photos / data:** real active listings hotlinked from the Tribus staging site's MLS
  feed (images-v3-mlsgrid.displet.com). MLS image URLs can expire — re-point or download as needed.
- **Landscape/office photos:** hotlinked from storage.mytribus.com (staging site assets).
- **Logo:** hotlinked from thegroupinc.com (white version produced via CSS filter).
- **Agent names/portraits:** fictional; portraits are brand-color placeholder blocks by design.
- **Interior gallery shots on `property.html`:** representative placeholders, not the listed home.
- Property cards all route to the single `property.html` template; footer resource links and
  community links are stubs (`#`).
