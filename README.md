# National Park Passport

A gamified, fully static checklist site for visiting all 63 U.S. national parks.
Tool pages earn search traffic; affiliate placements earn revenue.

> **Status:** MVP (2026-09-16). Design doc: [`design.md`](./design.md)
> （中文背景与成功假设见 [`成功假设与事实判断.md`](./成功假设与事实判断.md)）
>
> ⚠️ **Domain is a placeholder.** `SITE_DOMAIN` in `config.py` is currently
> `nationalparkpassport.com` (TBD — user to decide). Replace that one value,
> rebuild, and redeploy when the real domain is chosen.

## What it is

- **Home (`/`)** — interactive 63-park checklist: tap to check off, search,
  filter by state, sort A–Z/by state. Stats panel with count X/63, level
  (Explorer → Adventurer → Ranger → Legend), achievement badges, visit streak,
  3-step first-visit onboarding, canvas share-card generator (PNG download,
  domain watermark). All state in `localStorage` — no signup, no backend.
- **8 variant pages** — `/check-off/`, `/tracker/`, `/counter/`,
  `/visited-map/`, `/interactive-map/`, `/passport-stamps/`, `/passport-book/`,
  `/park-planner/` — one target keyword each, ≥1200 words of differentiated
  copy, simplified check-off tool sharing the same saved progress.
- **63 park pages** (`/parks/{slug}/`) — ≥400 words each, highlights, planning
  tips, same-state internal links, per-park check-off button.
- **`/quiz/`** — 10-question interactive national park trivia, best score saved.
- **SEO** — per-page title/H1/keyword, meta description, OG tags, canonical,
  JSON-LD (`WebPage` + `FAQPage`), internal link mesh, `sitemap.xml`,
  `robots.txt`.
- **Monetization placeholders** — `AFFILIATE-PLACEHOLDER` (styled product-card
  boxes, links TBD) and `ADSENSE-PLACEHOLDER` (styled ad slots).

## Project layout

```
config.py               # site name, domain (PLACEHOLDER), nav, variant list
data/parks.json         # 63 parks: name/slug/states/region/intro/highlights
templates/base.html     # page shell (head SEO, header, footer)
content/home.html       # homepage article + tool markup (≥800 words)
content/variants/*.html # 8 variant pages (≥1200 words each)
content/quiz.html       # quiz intro + question data
assets/css/style.css    # outdoor theme, mobile-first, no framework
assets/js/app.js        # checklist/stats/badges/streak/share/quiz engine
build.py                # static generator -> dist/
scripts/check.py        # self-check: word counts, links, SEO tags, sitemap
scripts/push_to_github.py  # bulk push via GitHub Contents API
scripts/deploy_pages.py    # Cloudflare Pages Direct Upload (3-step flow)
dist/                   # build output (generated, deployed to Pages)
```

## Build & check

```bash
python3 build.py          # generates dist/ (73 pages)
python3 scripts/check.py # word counts, internal links, SEO tags, placeholders
```

## Deploy

```bash
# GitHub (public repo backup) — uses stored custom.github credential
python3 scripts/push_to_github.py

# Cloudflare Pages — uses stored custom.cloudflare credential
python3 scripts/deploy_pages.py
```

`deploy_pages.py` implements the verified Direct Upload flow:
1. `GET .../pages/projects/{name}/upload-token` → short-lived JWT
2. `POST https://api.cloudflare.com/client/v4/pages/assets/upload`
   (JSON array of `{key: sha256[:32], value: base64, metadata, base64: true}`,
   `Authorization: Bearer <jwt>`)
3. `POST .../pages/projects/{name}/deployments` (multipart: `manifest` +
   `branch=main`, account-token auth)

Credentials are injected at request time via the skill-creator
`dynamic_credentials` helper — never printed or written to disk.

## Conventions

- Site content is **English**; docs/notes may be Chinese.
- Park descriptions are conservative: no invented established-dates or areas.
  When a fact is uncertain, it is omitted, not fabricated.
- One page = one keyword. Variant pages must keep differentiated copy
  (title/H1/intro/FAQ all differ) to avoid duplicate-content issues.
- `dist/` is generated — never edit it by hand; change source and rebuild.
