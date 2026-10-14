"""Build an animated marquee of organizations this user has contributed to.

The org list comes from GitHub's own public "Activity overview" fragment on the
profile page, so it matches exactly what GitHub shows to visitors.
Run: python3 scripts/build_contributed_orgs.py
"""
import re
import sys
import urllib.request
from pathlib import Path

from orbit import Item, Ring, Theme, fetch_data_uri, render

USER = "hoangperry"
# Own company and GitHub's discussion forum are not open-source contributions.
SKIP = {"kamilabs-ai", "community"}
FRAGMENT_URL = f"https://github.com/{USER}?action=show&controller=profiles&tab=contributions&user_id={USER}"
THEMES = {
    "dark": Theme(label="#8b949e", core_fill="#161b22", core_glow="#58a6ff", core_text="#58a6ff"),
    "light": Theme(label="#57606a", core_fill="#f6f8fa", core_glow="#0969da", core_text="#0969da"),
}
OUT_DIR = Path(__file__).resolve().parent.parent / "assets"
SECONDS_PER_ORG = 2.8


def fetch_orgs() -> list:
    req = urllib.request.Request(FRAGMENT_URL, headers={"User-Agent": "Mozilla/5.0", "X-Requested-With": "XMLHttpRequest"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        html = resp.read().decode("utf-8", "replace")
    found = re.findall(r"[?&](?:amp;)?org=([A-Za-z0-9_.-]+)", html)
    return [org for org in dict.fromkeys(found) if org not in SKIP]


def main() -> int:
    orgs = fetch_orgs()
    if not orgs:
        # Keep the previous SVGs instead of publishing an empty strip.
        print("no organizations found; leaving existing assets untouched", file=sys.stderr)
        return 1
    print("orgs:", ", ".join(orgs))
    items = tuple(Item(fetch_data_uri(f"https://github.com/{org}.png?size=112", "image/png"), f"@{org}", rounded=True) for org in orgs)
    ring = Ring(items, 335, 112, round(len(items) * SECONDS_PER_ORG))
    avatar = fetch_data_uri(f"https://github.com/{USER}.png?size=168", "image/png")
    OUT_DIR.mkdir(exist_ok=True)
    for key, theme in THEMES.items():
        path = OUT_DIR / f"contributed-orgs-{key}.svg"
        path.write_text(render([ring], theme, core_uri=avatar))
        print(f"wrote {path.name} ({path.stat().st_size // 1024}K)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
