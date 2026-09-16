#!/usr/bin/env python3
"""Static site generator: data/parks.json + templates/ + content/ -> dist/.

Usage: python3 build.py
"""
import json
import os
import re
import shutil
from datetime import date

import config

ROOT = os.path.dirname(os.path.abspath(__file__))
DIST = os.path.join(ROOT, "dist")
TODAY = date.today().isoformat()


def render(tpl, mapping):
    out = tpl
    for k, v in mapping.items():
        out = out.replace("{{" + k + "}}", v)
    return out


def strip_tags(html):
    text = re.sub(r"<[^>]+>", " ", html)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def extract_faqs(content_html):
    """Pull (question, answer) pairs out of <details><summary>Q</summary><p>A</p></details>."""
    faqs = []
    for m in re.finditer(r"<details><summary>(.*?)</summary>\s*<p>(.*?)</p>\s*</details>", content_html, re.S):
        q = strip_tags(m.group(1))
        a = strip_tags(m.group(2))
        if q and a:
            faqs.append((q, a))
    return faqs


def jsonld_webpage(url, name, desc, faqs):
    data = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "WebPage",
                "@id": url,
                "url": url,
                "name": name,
                "description": desc,
                "isPartOf": {"@type": "WebSite", "name": config.SITE_NAME, "url": config.BASE_URL + "/"},
                "inLanguage": "en",
            }
        ],
    }
    if faqs:
        data["@graph"].append({
            "@type": "FAQPage",
            "mainEntity": [
                {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}}
                for q, a in faqs
            ],
        })
    return json.dumps(data, ensure_ascii=False, indent=2)


def nav_html():
    return "".join(
        f'<a href="{href}">{label}</a>' for label, href in config.NAV_LINKS
    )


def write_page(rel_path, title, meta_desc, content_html, og_title=None, extra_js=""):
    """rel_path like 'index.html' or 'parks/zion/index.html'."""
    url = config.BASE_URL + "/" + rel_path.replace("index.html", "")
    if not url.endswith("/"):
        url += "/"
    # root index special-case: rel_path 'index.html' -> BASE_URL + '/'
    if rel_path == "index.html":
        url = config.BASE_URL + "/"
    faqs = extract_faqs(content_html)
    page = render(
        open(os.path.join(ROOT, "templates", "base.html"), encoding="utf-8").read(),
        {
            "title": title,
            "meta_desc": meta_desc,
            "canonical": url,
            "site_name": config.SITE_NAME,
            "og_title": og_title or title,
            "jsonld": jsonld_webpage(url, title, meta_desc, faqs),
            "nav_links": nav_html(),
            "content": content_html,
            "extra_js": extra_js,
        },
    )
    # sanity: no unreplaced placeholders
    leftover = re.findall(r"\{\{\w+\}\}", page)
    assert not leftover, f"unreplaced placeholders in {rel_path}: {leftover}"
    dest = os.path.join(DIST, rel_path)
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    with open(dest, "w", encoding="utf-8") as fh:
        fh.write(page)
    return url


# ---------------------------------------------------------------- park pages

WHY_TEMPLATES = [
    "<p>{name} earns its place on every collector's list for one simple reason: {h0_lower}. {intro2} Most visitors arrive with a short list of must-sees and leave with a longer list of reasons to return — that is the mark of a park worth checking off.</p>",
    "<p>What sets {name} apart is {h0_lower}. {intro2} It is the rare park that satisfies both the box-checker racing the clock and the slow traveler who wants to linger, which is why it shows up on so many collectors' highlight reels.</p>",
    "<p>Collectors remember {name} for {h0_lower}. {intro2} Whether you have an hour or a week, the park delivers the kind of moments that make the 63-park quest worthwhile.</p>",
]

CHECKOFF_TEMPLATES = [
    "<p>When you visit, make these your non-negotiables: {highlights}. Each one is a story you will tell later — and each one makes the check mark on your list feel earned. Stamp your <a href=\"/passport-book/\">passport book</a> at the visitor center, then tap the park off on the <a href=\"/\">main checklist</a> before you leave the parking lot.</p>",
    "<p>Build your day around the highlights: {highlights}. Work them in order of light and crowds — popular viewpoints at opening time, big trails midday, scenic drives at golden hour. Do not forget the <a href=\"/passport-stamps/\">cancellation stamp</a> at the visitor center; future you will be glad the book was in the daypack.</p>",
    "<p>The essential circuit covers {highlights}. Even a short visit can touch most of them if you plan around the park's geography rather than wandering. Log the visit on your <a href=\"/tracker/\">tracker</a> the same evening while the details are fresh.</p>",
]

PLAN_TEMPLATES = [
    "<p>Give {name} the time it deserves: a rushed half-day works for the highlights, but a full day lets the park breathe. Mornings bring the best light and the thinnest crowds at popular viewpoints. Check current conditions on <a href=\"https://www.nps.gov\" rel=\"noopener\">nps.gov</a> before you go — road openings, timed-entry requirements, and seasonal closures change yearly. If you are clustering parks, see which other {state_list} parks you still need on the <a href=\"/visited-map/\">visited map</a> and build the loop from there.</p>",
    "<p>Plan around the park's rhythm: arrive early for trailheads, carry more water than you expect to need, and keep the <a href=\"/park-planner/\">trip planner</a> method in mind — cluster nearby parks, match the season, book constrained lodging first. {name} pairs naturally with its {state_list} neighbors below, making it an efficient addition to a regional loop.</p>",
    "<p>A little planning goes a long way at {name}. Weekdays beat weekends, mornings beat afternoons, and the shoulder seasons beat peak summer on crowds. Before you go, mark the park's neighbors below on your <a href=\"/interactive-map/\">interactive map</a> — {state_list} holds more than most travelers realize, and one well-built loop can check off several parks at once.</p>",
]

FAQ_TEMPLATES = [
    ("Is {name} worth visiting?", "Yes — it is one of the 63 U.S. national parks, each selected for exceptional natural or cultural significance. Highlights include {h0_lower} and {h1_lower}."),
    ("How much time do I need at {name}?", "A focused half-day covers the headline sights ({h0_lower}); a full day lets you hike and linger. Multi-day visitors can pair it with nearby {state_list} parks."),
    ("When is the best time to visit {name}?", "It depends on the park's climate and your tolerance for crowds — shoulder seasons are the collector's sweet spot at most parks. Check current conditions on nps.gov before finalizing dates."),
]


def build_park_page(park, all_parks, idx):
    name = park["name"]
    slug = park["slug"]
    states = park["state_names"]
    state_codes = park["states"]
    state_list = " and ".join(states)
    h = park["highlights"]
    h0_lower = h[0][0].lower() + h[0][1:]
    intro2 = park["intro"].split(". ")[1] if ". " in park["intro"] else park["intro"]
    highlights_str = "; ".join(h)

    # same-state parks (share any state code), excluding self
    same_state = [
        p for p in all_parks
        if p["slug"] != slug and set(p["states"]) & set(state_codes)
    ]
    same_state_links = "".join(
        f'<a href="/parks/{p["slug"]}/">{p["name"]} National Park</a>' for p in same_state
    ) or "<p>None — this is the only national park in its state/territory.</p>"

    v = idx % 3
    why = WHY_TEMPLATES[v].format(name=name, h0_lower=h0_lower, intro2=intro2)
    checkoff = CHECKOFF_TEMPLATES[v].format(highlights=highlights_str)
    plan = PLAN_TEMPLATES[v].format(name=name, state_list=state_list)
    faqs_html = "".join(
        f"<details><summary>{q.format(name=name, h0_lower=h0_lower, h1_lower=h[1][0].lower() + h[1][1:], state_list=state_list)}</summary>"
        f"<p>{a.format(name=name, h0_lower=h0_lower, h1_lower=h[1][0].lower() + h[1][1:], state_list=state_list)}</p></details>"
        for q, a in FAQ_TEMPLATES
    )

    content = f"""
<div class="wrap">
<nav class="breadcrumb" aria-label="Breadcrumb"><a href="/">Home</a> › <a href="/#checklist">All 63 Parks</a> › {name} National Park</nav>
<article class="article">
<h1>{name} National Park: Checklist &amp; Visitor Guide</h1>
<div class="park-hero-meta">
<span class="tag">📍 {", ".join(states)}</span>
<span class="tag">🗺️ {park["region"]} region</span>
<span class="tag">⭐ Best for: {park["best_for"]}</span>
</div>
<div class="park-toggle-big" data-npp="park-toggle" data-slug="{slug}"></div>
<p class="lead">{park["intro"]}</p>
<h2>Why {name} Belongs on Your Checklist</h2>
{why}
<h2>What to Check Off at {name}</h2>
<ul>
{"".join(f"<li><strong>{x}</strong></li>" for x in h)}
</ul>
{checkoff}
<h2>Planning Your Visit to {name}</h2>
{plan}
<h2>More National Parks in {state_list}</h2>
<p>Knock out several parks in one regional loop:</p>
<div class="related-grid">{same_state_links}</div>
<div class="faq" aria-label="Frequently asked questions">
<h2>{name} FAQ</h2>
{faqs_html}
</div>
</article>
<article class="article">
<h2>Track {name} With the Whole Toolkit</h2>
<ul>
<li><a href="/">Main national park checklist</a> — check off {name} and see your level</li>
<li><a href="/check-off/">Check off national parks</a> — the full 63-park tick list</li>
<li><a href="/park-planner/">Trip planner</a> — build a {state_list} road trip</li>
<li><a href="/visited-map/">Visited parks map</a> — see your {state_list} progress</li>
</ul>
</article>
</div>
"""
    title = f"{name} National Park Checklist & Visitor Guide | {config.SITE_NAME}"
    desc = (f"Visiting {name} National Park? Highlights, what to check off, planning tips, "
            f"and more parks in {state_list}. Check it off your 63-park list.")
    return write_page(f"parks/{slug}/index.html", title, desc, content)


# ---------------------------------------------------------------- main

def main():
    if os.path.exists(DIST):
        shutil.rmtree(DIST)
    os.makedirs(DIST)

    parks = json.load(open(os.path.join(ROOT, "data", "parks.json"), encoding="utf-8"))
    assert len(parks) == 63, f"expected 63 parks, got {len(parks)}"

    # assets
    shutil.copytree(os.path.join(ROOT, "assets", "css"), os.path.join(DIST, "assets", "css"))
    shutil.copytree(os.path.join(ROOT, "assets", "js"), os.path.join(DIST, "assets", "js"))

    # parks-data.js (shared dataset for all interactive widgets)
    slim = [{"name": p["name"], "slug": p["slug"], "states": p["states"]} for p in parks]
    with open(os.path.join(DIST, "assets", "js", "parks-data.js"), "w", encoding="utf-8") as fh:
        fh.write("window.NPP_PARKS=" + json.dumps(slim, ensure_ascii=False) + ";\n")
        fh.write("window.NPP_CONFIG=" + json.dumps({
            "domain": config.SITE_DOMAIN,
            "siteName": config.SITE_NAME,
        }, ensure_ascii=False) + ";\n")

    urls = []

    # home
    home = open(os.path.join(ROOT, "content", "home.html"), encoding="utf-8").read()
    urls.append(write_page(
        "index.html",
        f"National Park Checklist: Check Off All 63 U.S. National Parks | {config.SITE_NAME}",
        "Free interactive national park checklist for all 63 U.S. national parks. Check off visited parks, earn levels and badges, track streaks, and generate share cards — no signup.",
        home,
    ))

    # variants
    variant_meta = {
        "check-off": ("Check Off National Parks: Interactive 63-Park Tick-Box List",
                      "Check off every U.S. national park you've visited with this free interactive tick-box list. All 63 parks, progress syncs across the site, no signup."),
        "tracker": ("National Park Tracker: Log & Track Your 63-Park Progress",
                    "Free national park tracker: log your visits across all 63 U.S. national parks and follow your stats, levels, badges, and streaks over time."),
        "counter": ("National Park Counter: How Many of the 63 Have You Visited?",
                    "How many national parks have you visited? Tap the ones you've been to and get your definitive count out of 63 — free, no signup."),
        "visited-map": ("Visited National Parks Map: Mark Your 63-Park Journey",
                        "Mark the national parks you've visited and view your journey state by state. Free interactive visited-parks map for all 63 U.S. national parks."),
        "interactive-map": ("Interactive National Park Map: Explore All 63 Parks",
                            "Explore all 63 U.S. national parks with this free interactive map: filter by state, search by name, and mark the parks you've visited."),
        "passport-stamps": ("National Park Passport Stamps: Complete Cancellation Guide",
                            "The complete guide to national park passport cancellation stamps: how the program works, where to find stamp stations, and how to build your collection."),
        "passport-book": ("National Park Passport Book: The Collector's Guide",
                          "Everything about the official Passport To Your National Parks book: editions, annual sticker sets, where to buy, and how collectors use it."),
        "park-planner": ("National Park Trip Planner: Turn Your Checklist Into an Itinerary",
                         "Plan your national park road trip from your checklist: the great park clusters, season-matching, expedition-tier parks, and budgeting."),
    }
    for slug, keyword in config.VARIANTS:
        body = open(os.path.join(ROOT, "content", "variants", slug + ".html"), encoding="utf-8").read()
        title, desc = variant_meta[slug]
        title = f"{title} | {config.SITE_NAME}"
        urls.append(write_page(f"{slug}/index.html", title, desc, body))

    # park pages
    for i, park in enumerate(parks):
        urls.append(build_park_page(park, parks, i))

    # quiz
    quiz = open(os.path.join(ROOT, "content", "quiz.html"), encoding="utf-8").read()
    urls.append(write_page(
        "quiz/index.html",
        f"National Park Trivia Quiz: 10 Questions for Park Nerds | {config.SITE_NAME}",
        "Test your national park knowledge with 10 interactive trivia questions. Instant answers with explanations, best score saved — free, no signup.",
        quiz,
    ))

    # sitemap.xml
    sm = ['<?xml version="1.0" encoding="UTF-8"?>',
          '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.0.9">']
    for u in urls:
        sm.append(f"  <url><loc>{u}</loc><lastmod>{TODAY}</lastmod><changefreq>weekly</changefreq></url>")
    sm.append("</urlset>")
    with open(os.path.join(DIST, "sitemap.xml"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(sm))

    # robots.txt
    with open(os.path.join(DIST, "robots.txt"), "w", encoding="utf-8") as fh:
        fh.write(f"User-agent: *\nAllow: /\nSitemap: {config.BASE_URL}/sitemap.xml\n")

    print(f"built {len(urls)} pages -> {DIST}")


if __name__ == "__main__":
    main()
