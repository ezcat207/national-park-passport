# Site configuration. All URLs, titles and branding flow from here.
# NOTE: SITE_DOMAIN is a placeholder — the user has not chosen the final
# domain yet (design.md section 11). Replace this one value when decided,
# rebuild, and redeploy.

SITE_NAME = "National Park Passport"
SITE_DOMAIN = "nationalparkpassport.com"  # PLACEHOLDER — TBD by user
BASE_URL = f"https://{SITE_DOMAIN}"

DEFAULT_OG_IMAGE = f"{BASE_URL}/assets/img/og-default.png"

NAV_LINKS = [
    ("Checklist", "/"),
    ("Check Off", "/check-off/"),
    ("Tracker", "/tracker/"),
    ("Maps", "/visited-map/"),
    ("Passport Stamps", "/passport-stamps/"),
    ("Passport Book", "/passport-book/"),
    ("Trip Planner", "/park-planner/"),
    ("Trivia Quiz", "/quiz/"),
]

# Variant pages: slug -> (target keyword, nav label)
VARIANTS = [
    ("check-off", "check off national parks"),
    ("tracker", "national park tracker"),
    ("counter", "national park counter"),
    ("visited-map", "visited national parks map"),
    ("interactive-map", "interactive national park map"),
    ("passport-stamps", "national park passport stamps"),
    ("passport-book", "national park passport book"),
    ("park-planner", "national park trip planner"),
]
