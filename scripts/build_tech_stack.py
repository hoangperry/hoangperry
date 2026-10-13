"""Build animated tech-stack SVGs (light + dark) from skillicons.dev icons.

Layout: two infinite marquee rows scrolling in opposite directions, edges
faded with a mask, each icon gently bobbing. Icons are embedded as base64
data URIs so internal ids never collide and the file is self-contained.
Run: /usr/bin/python3 scripts/build_tech_stack.py
"""
import base64
import urllib.request
from pathlib import Path

ROWS = [
    # (items, scroll direction: -1 = left, 1 = right, seconds per loop)
    ([("swift", "Swift"), ("go", "Go"), ("ts", "TypeScript"), ("python", "Python"),
      ("react", "React"), ("nextjs", "Next.js"), ("threejs", "Three.js"), ("tauri", "Tauri")], -1, 22),
    ([("postgres", "PostgreSQL"), ("redis", "Redis"), ("docker", "Docker"), ("kubernetes", "Kubernetes"),
      ("cloudflare", "Cloudflare"), ("gcp", "GCP"), ("linux", "Linux"), ("neovim", "Neovim")], 1, 26),
]
ICON = 56
CELL_W = 112
ROW_H = 100
PAD_Y = 14
VIEW_W = 800
BOB_SECONDS = 2.4
THEMES = {"dark": ("dark", "#8b949e"), "light": ("light", "#57606a")}
OUT_DIR = Path(__file__).resolve().parent.parent / "assets"


def fetch_icon(slug: str, theme: str) -> str:
    url = f"https://skillicons.dev/icons?i={slug}&theme={theme}"
    req = urllib.request.Request(url, headers={"User-Agent": "tech-stack-builder"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        if resp.status != 200:
            raise RuntimeError(f"{url} -> HTTP {resp.status}")
        return base64.b64encode(resp.read()).decode()


def cell(x: float, slug_data: str, label: str, delay: float) -> str:
    return (
        f'<g transform="translate({x},0)"><g class="bob" style="animation-delay:{delay:.2f}s">'
        f'<image x="{(CELL_W - ICON) / 2}" width="{ICON}" height="{ICON}" href="data:image/svg+xml;base64,{slug_data}"/>'
        f'<text x="{CELL_W / 2}" y="{ICON + 20}" text-anchor="middle">{label}</text>'
        f"</g></g>"
    )


def build(theme_key: str) -> str:
    icon_theme, label_color = THEMES[theme_key]
    height = len(ROWS) * ROW_H + PAD_Y
    rows_svg, keyframes = [], []
    for r, (items, direction, seconds) in enumerate(ROWS):
        icons = [(fetch_icon(slug, icon_theme), label) for slug, label in items]
        loop_w = len(items) * CELL_W
        # Repeat the set enough times to always cover the viewport while shifting by one loop.
        copies = VIEW_W // loop_w + 2
        cells = "".join(
            cell(c * loop_w + i * CELL_W, data, label, (i * 0.3) % BOB_SECONDS)
            for c in range(copies) for i, (data, label) in enumerate(icons)
        )
        start, end = (0, -loop_w) if direction < 0 else (-loop_w, 0)
        keyframes.append(
            f"@keyframes row{r} {{ from {{ transform: translateX({start}px); }} to {{ transform: translateX({end}px); }} }}"
            f" .row{r} {{ animation: row{r} {seconds}s linear infinite; }}"
        )
        rows_svg.append(f'<g transform="translate(0,{r * ROW_H + PAD_Y})"><g class="row{r}">{cells}</g></g>')
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{VIEW_W}" height="{height}" viewBox="0 0 {VIEW_W} {height}">
<defs>
<linearGradient id="fade" x1="0" x2="1" y1="0" y2="0">
<stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".12" stop-color="#fff" stop-opacity="1"/>
<stop offset=".88" stop-color="#fff" stop-opacity="1"/><stop offset="1" stop-color="#fff" stop-opacity="0"/>
</linearGradient>
<mask id="edges"><rect width="{VIEW_W}" height="{height}" fill="url(#fade)"/></mask>
</defs>
<style>
text {{ font: 600 12px -apple-system, 'Segoe UI', Helvetica, Arial, sans-serif; fill: {label_color}; }}
.bob {{ animation: bob {BOB_SECONDS}s ease-in-out infinite; }}
@keyframes bob {{ 0%, 100% {{ transform: translateY(0); }} 50% {{ transform: translateY(-8px); }} }}
{' '.join(keyframes)}
@media (prefers-reduced-motion: reduce) {{ .bob, .row0, .row1 {{ animation: none; }} }}
</style>
<g mask="url(#edges)">{''.join(rows_svg)}</g>
</svg>
"""


def main() -> None:
    OUT_DIR.mkdir(exist_ok=True)
    for key in THEMES:
        path = OUT_DIR / f"tech-stack-{key}.svg"
        path.write_text(build(key))
        print(f"wrote {path.name} ({path.stat().st_size // 1024}K)")


if __name__ == "__main__":
    main()
