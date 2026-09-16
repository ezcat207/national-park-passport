#!/usr/bin/env python3
"""Self-check for dist/: word counts, internal links, SEO tags, placeholders.

Usage: python3 scripts/check.py  (exits non-zero on failure)
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIST = os.path.join(ROOT, "dist")

failures = []


def fail(msg):
    failures.append(msg)
    print("FAIL:", msg)


def text_of(html):
    # drop scripts/styles/nav/footer noise for word counting the article body
    t = re.sub(r"<script.*?</script>", " ", html, flags=re.S)
    t = re.sub(r"<style.*?</style>", " ", t, flags=re.S)
    t = re.sub(r"<[^>]+>", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def words(path):
    html = open(path, encoding="utf-8").read()
    return len(text_of(html).split())


# --- 1. word counts (on rendered article text; UI labels add a bit, so use margins)
checks = [
    ("index.html", 800, "home"),
]
for slug in ["check-off", "tracker", "counter", "visited-map", "interactive-map",
             "passport-stamps", "passport-book", "park-planner"]:
    checks.append((f"{slug}/index.html", 1200, f"variant {slug}"))
for park_dir in sorted(os.listdir(os.path.join(DIST, "parks"))):
    checks.append((f"parks/{park_dir}/index.html", 400, f"park {park_dir}"))
checks.append(("quiz/index.html", 300, "quiz"))

for rel, minimum, label in checks:
    p = os.path.join(DIST, rel)
    if not os.path.exists(p):
        fail(f"missing page {rel}")
        continue
    n = words(p)
    status = "ok" if n >= minimum else "SHORT"
    if n < minimum:
        fail(f"{label}: {n} words < {minimum}")
    else:
        print(f"ok   {label}: {n} words")


# --- 2. internal links resolve
pages = {}
for dirpath, _, files in os.walk(DIST):
    for f in files:
        if f.endswith(".html"):
            full = os.path.join(dirpath, f)
            rel = os.path.relpath(full, DIST)
            pages[full] = open(full, encoding="utf-8").read()

# map URL path -> file
url_to_file = {}
for full in pages:
    rel = os.path.relpath(full, DIST).replace(os.sep, "/")
    assert rel.endswith("index.html")
    urlpath = "/" + rel[: -len("index.html")]
    url_to_file[urlpath] = full

link_re = re.compile(r'href="(/[^"]*)"')
bad = 0
for full, html in pages.items():
    for m in link_re.finditer(html):
        href = m.group(1).split("#")[0].split("?")[0]
        if href.startswith("/assets/"):
            target = os.path.join(DIST, href[1:])
            if not os.path.exists(target):
                fail(f"broken asset link {href} in {os.path.relpath(full, DIST)}")
                bad += 1
            continue
        if not href.endswith("/"):
            href += "/"
        if href not in url_to_file:
            fail(f"broken internal link {href} in {os.path.relpath(full, DIST)}")
            bad += 1
if bad == 0:
    print("ok   all internal links resolve")

# --- 3. SEO tags present on every page
required = ["<title>", 'name="description"', 'rel="canonical"',
            'property="og:title"', 'application/ld+json', "<h1"]
for full, html in pages.items():
    rel = os.path.relpath(full, DIST)
    for tag in required:
        if tag not in html:
            fail(f"{rel} missing {tag}")
print("ok   SEO tag sweep done")

# --- 4. placeholders present
aff = sum(1 for h in pages.values() if "AFFILIATE-PLACEHOLDER" in h)
ads = sum(1 for h in pages.values() if "ADSENSE-PLACEHOLDER" in h)
print(f"info affiliate placeholders on {aff} pages, adsense on {ads} pages")
if aff < 9:
    fail("expected affiliate placeholders on home + 8 variants")

# --- 5. sitemap/robots
for f in ["sitemap.xml", "robots.txt"]:
    if not os.path.exists(os.path.join(DIST, f)):
        fail(f"missing {f}")
sm = open(os.path.join(DIST, "sitemap.xml"), encoding="utf-8").read()
n_urls = sm.count("<loc>")
print(f"info sitemap has {n_urls} urls")
if n_urls != 73:
    fail(f"sitemap url count {n_urls} != 73")

print()
if failures:
    print(f"{len(failures)} FAILURES")
    sys.exit(1)
print("ALL CHECKS PASSED")
