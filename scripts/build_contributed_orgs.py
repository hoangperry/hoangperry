"""Write the list of organizations this user has contributed to into README.md.

The org list comes from GitHub's own public "Activity overview" fragment on the
profile page, so it matches exactly what GitHub shows to visitors. The list is
written between the ORGS markers in README.md.
Run from scripts/: python3 build_contributed_orgs.py
"""
import re
import sys
import urllib.request
from pathlib import Path

USER = "hoangperry"
# Own company and GitHub's discussion forum are not open-source contributions.
SKIP = {"kamilabs-ai", "community"}
FRAGMENT_URL = f"https://github.com/{USER}?action=show&controller=profiles&tab=contributions&user_id={USER}"
README = Path(__file__).resolve().parent.parent / "README.md"
START, END = "<!-- ORGS:START -->", "<!-- ORGS:END -->"


def fetch_orgs() -> list:
    req = urllib.request.Request(FRAGMENT_URL, headers={"User-Agent": "Mozilla/5.0", "X-Requested-With": "XMLHttpRequest"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        html = resp.read().decode("utf-8", "replace")
    found = re.findall(r"[?&](?:amp;)?org=([A-Za-z0-9_.-]+)", html)
    return [org for org in dict.fromkeys(found) if org not in SKIP]


def render_list(orgs: list) -> str:
    return "\n".join(
        f'- <img src="https://github.com/{org}.png?size=40" width="16" height="16" /> [@{org}](https://github.com/{org})'
        for org in orgs
    )


def main() -> int:
    orgs = fetch_orgs()
    if not orgs:
        # Keep the previous list instead of publishing an empty one.
        print("no organizations found; leaving README untouched", file=sys.stderr)
        return 1
    text = README.read_text()
    if START not in text or END not in text:
        print(f"markers {START} / {END} missing from README.md", file=sys.stderr)
        return 1
    block = f"{START}\n{render_list(orgs)}\n{END}"
    README.write_text(re.sub(re.escape(START) + r".*?" + re.escape(END), lambda _: block, text, flags=re.S))
    print("orgs:", ", ".join(orgs))
    return 0


if __name__ == "__main__":
    sys.exit(main())
