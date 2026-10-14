"""Build animated tech-stack SVGs (light + dark) from skillicons.dev icons.

Run: /usr/bin/python3 scripts/build_tech_stack.py
"""
from pathlib import Path

from marquee import Item, Row, fetch_data_uri, render

ROWS = [
    # (items, scroll direction: -1 = left, 1 = right, seconds per loop)
    ([("swift", "Swift"), ("go", "Go"), ("ts", "TypeScript"), ("python", "Python"),
      ("react", "React"), ("nextjs", "Next.js"), ("threejs", "Three.js"), ("tauri", "Tauri")], -1, 22),
    ([("postgres", "PostgreSQL"), ("redis", "Redis"), ("docker", "Docker"), ("kubernetes", "Kubernetes"),
      ("cloudflare", "Cloudflare"), ("gcp", "GCP"), ("linux", "Linux"), ("neovim", "Neovim")], 1, 26),
]
THEMES = {"dark": ("dark", "#8b949e"), "light": ("light", "#57606a")}
OUT_DIR = Path(__file__).resolve().parent.parent / "assets"


def main() -> None:
    OUT_DIR.mkdir(exist_ok=True)
    for key, (icon_theme, label_color) in THEMES.items():
        rows = [
            Row(tuple(Item(fetch_data_uri(f"https://skillicons.dev/icons?i={slug}&theme={icon_theme}", "image/svg+xml"), label)
                      for slug, label in items), direction, seconds)
            for items, direction, seconds in ROWS
        ]
        path = OUT_DIR / f"tech-stack-{key}.svg"
        path.write_text(render(rows, label_color))
        print(f"wrote {path.name} ({path.stat().st_size // 1024}K)")


if __name__ == "__main__":
    main()
