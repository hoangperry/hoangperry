"""Build animated tech-stack SVGs (light + dark) from skillicons.dev icons.

Icons are embedded as base64 data URIs so their internal ids never collide,
and the result is fully self-contained for GitHub's image proxy.
Run: python3 scripts/build_tech_stack.py
"""
import base64
import urllib.request
from pathlib import Path

STACK = [
    ("swift", "Swift"), ("go", "Go"), ("ts", "TypeScript"), ("python", "Python"),
    ("react", "React"), ("nextjs", "Next.js"), ("threejs", "Three.js"), ("tauri", "Tauri"),
    ("postgres", "PostgreSQL"), ("redis", "Redis"), ("docker", "Docker"), ("kubernetes", "Kubernetes"),
    ("cloudflare", "Cloudflare"), ("gcp", "GCP"), ("linux", "Linux"), ("neovim", "Neovim"),
]
PER_ROW = 8
ICON = 56
CELL_W = 96
CELL_H = 104
PAD_TOP = 18
WAVE_SECONDS = 2.4
THEMES = {"dark": ("dark", "#8b949e"), "light": ("light", "#57606a")}
OUT_DIR = Path(__file__).resolve().parent.parent / "assets"


def fetch_icon(slug: str, theme: str) -> str:
    url = f"https://skillicons.dev/icons?i={slug}&theme={theme}"
    req = urllib.request.Request(url, headers={"User-Agent": "tech-stack-builder"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        if resp.status != 200:
            raise RuntimeError(f"{url} -> HTTP {resp.status}")
        return base64.b64encode(resp.read()).decode()


def build(theme_key: str) -> str:
    icon_theme, label_color = THEMES[theme_key]
    rows = (len(STACK) + PER_ROW - 1) // PER_ROW
    width, height = PER_ROW * CELL_W, rows * CELL_H + PAD_TOP
    cells = []
    for i, (slug, label) in enumerate(STACK):
        col, row = i % PER_ROW, i // PER_ROW
        x = col * CELL_W + (CELL_W - ICON) / 2
        y = row * CELL_H + PAD_TOP
        # Delay follows a diagonal so the wave rolls across both rows.
        delay = (col + row * 2) * 0.12
        data = fetch_icon(slug, icon_theme)
        cells.append(
            f'<g transform="translate({x},{y})">'
            f'<g class="pop" style="animation-delay:{i * 0.06:.2f}s">'
            f'<g class="bob" style="animation-delay:{delay:.2f}s">'
            f'<image width="{ICON}" height="{ICON}" href="data:image/svg+xml;base64,{data}"/>'
            f'<text x="{ICON / 2}" y="{ICON + 20}" text-anchor="middle">{label}</text>'
            f"</g></g></g>"
        )
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
<style>
text {{ font: 600 12px -apple-system, 'Segoe UI', Helvetica, Arial, sans-serif; fill: {label_color}; }}
.pop {{ opacity: 0; transform-box: fill-box; transform-origin: center; animation: pop .5s cubic-bezier(.34,1.56,.64,1) forwards; }}
.bob {{ animation: bob {WAVE_SECONDS}s ease-in-out infinite; }}
@keyframes pop {{ from {{ opacity: 0; transform: scale(.4); }} to {{ opacity: 1; transform: scale(1); }} }}
@keyframes bob {{ 0%, 100% {{ transform: translateY(0); }} 50% {{ transform: translateY(-9px); }} }}
@media (prefers-reduced-motion: reduce) {{ .pop, .bob {{ animation: none; opacity: 1; }} }}
</style>
{''.join(cells)}
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
