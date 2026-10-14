"""Build the animated 3D-orbit tech-stack SVGs (light + dark).

Run from scripts/: python3 build_tech_stack.py
"""
from pathlib import Path

from orbit import Item, Ring, Theme, fetch_data_uri, render

# (items, horizontal radius, vertical radius, seconds per revolution, clockwise)
RINGS = [
    ([("swift", "Swift"), ("go", "Go"), ("ts", "TypeScript"), ("python", "Python"),
      ("react", "React"), ("nextjs", "Next.js"), ("threejs", "Three.js"), ("tauri", "Tauri")], 200, 72, 18, False),
    ([("postgres", "PostgreSQL"), ("redis", "Redis"), ("docker", "Docker"), ("kubernetes", "Kubernetes"),
      ("cloudflare", "Cloudflare"), ("gcp", "GCP"), ("linux", "Linux"), ("neovim", "Neovim")], 345, 122, 26, True),
]
THEMES = {
    "dark": ("dark", Theme(label="#8b949e", core_fill="#161b22", core_glow="#2ea043", core_text="#3fb950")),
    "light": ("light", Theme(label="#57606a", core_fill="#f6f8fa", core_glow="#2da44e", core_text="#1a7f37")),
}
OUT_DIR = Path(__file__).resolve().parent.parent / "assets"


def main() -> None:
    OUT_DIR.mkdir(exist_ok=True)
    for key, (icon_theme, theme) in THEMES.items():
        rings = [
            Ring(tuple(Item(fetch_data_uri(f"https://skillicons.dev/icons?i={slug}&theme={icon_theme}", "image/svg+xml"), label)
                       for slug, label in items), rx, ry, seconds, clockwise)
            for items, rx, ry, seconds, clockwise in RINGS
        ]
        path = OUT_DIR / f"tech-stack-{key}.svg"
        path.write_text(render(rings, theme, core_text="&lt;/&gt;"))
        print(f"wrote {path.name} ({path.stat().st_size // 1024}K)")


if __name__ == "__main__":
    main()
