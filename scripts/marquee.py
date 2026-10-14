"""Shared renderer for animated marquee SVGs (infinite scrolling rows).

Each row scrolls left or right forever, edges fade out through a mask, and
every item bobs gently. Images are embedded as base64 data URIs so the SVG is
self-contained and works through GitHub's image proxy.
"""
import base64
import time
import urllib.request
from dataclasses import dataclass

VIEW_W = 800
CELL_W = 112
ROW_H = 100
PAD_Y = 14
ICON = 56
BOB_SECONDS = 2.4
FETCH_ATTEMPTS = 3


@dataclass(frozen=True)
class Item:
    data_uri: str
    label: str
    rounded: bool = False


@dataclass(frozen=True)
class Row:
    items: tuple
    direction: int  # -1 scrolls left, 1 scrolls right
    seconds: int


def fetch_data_uri(url: str, mime: str) -> str:
    """Download an image and return it as a data URI, retrying transient network errors."""
    req = urllib.request.Request(url, headers={"User-Agent": "profile-marquee-builder"})
    for attempt in range(1, FETCH_ATTEMPTS + 1):
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return f"data:{mime};base64,{base64.b64encode(resp.read()).decode()}"
        except OSError as err:  # covers URLError, HTTPError and socket timeouts
            if attempt == FETCH_ATTEMPTS:
                raise RuntimeError(f"failed to fetch {url}: {err}") from err
            time.sleep(2 * attempt)
    raise AssertionError("unreachable")


def _cell(x: float, item: Item, delay: float) -> str:
    clip = ' clip-path="url(#round)"' if item.rounded else ""
    return (
        f'<g transform="translate({x},0)"><g class="bob" style="animation-delay:{delay:.2f}s">'
        f'<image x="{(CELL_W - ICON) / 2}" width="{ICON}" height="{ICON}"{clip} href="{item.data_uri}"/>'
        f'<text x="{CELL_W / 2}" y="{ICON + 20}" text-anchor="middle">{item.label}</text>'
        f"</g></g>"
    )


def render(rows: list, label_color: str) -> str:
    height = len(rows) * ROW_H + PAD_Y
    rows_svg, styles = [], []
    for r, row in enumerate(rows):
        loop_w = len(row.items) * CELL_W
        # Enough copies to cover the viewport while the row shifts by one full loop.
        copies = VIEW_W // loop_w + 2
        cells = "".join(
            _cell(c * loop_w + i * CELL_W, item, (i * 0.3) % BOB_SECONDS)
            for c in range(copies) for i, item in enumerate(row.items)
        )
        start, end = (0, -loop_w) if row.direction < 0 else (-loop_w, 0)
        styles.append(
            f"@keyframes row{r} {{ from {{ transform: translateX({start}px); }} to {{ transform: translateX({end}px); }} }}"
            f" .row{r} {{ animation: row{r} {row.seconds}s linear infinite; }}"
        )
        rows_svg.append(f'<g transform="translate(0,{r * ROW_H + PAD_Y})"><g class="row{r}">{cells}</g></g>')
    row_classes = ", ".join(f".row{r}" for r in range(len(rows)))
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{VIEW_W}" height="{height}" viewBox="0 0 {VIEW_W} {height}">
<defs>
<linearGradient id="fade" x1="0" x2="1" y1="0" y2="0">
<stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".12" stop-color="#fff" stop-opacity="1"/>
<stop offset=".88" stop-color="#fff" stop-opacity="1"/><stop offset="1" stop-color="#fff" stop-opacity="0"/>
</linearGradient>
<mask id="edges"><rect width="{VIEW_W}" height="{height}" fill="url(#fade)"/></mask>
<clipPath id="round" clipPathUnits="objectBoundingBox"><rect width="1" height="1" rx=".24"/></clipPath>
</defs>
<style>
text {{ font: 600 12px -apple-system, 'Segoe UI', Helvetica, Arial, sans-serif; fill: {label_color}; }}
.bob {{ animation: bob {BOB_SECONDS}s ease-in-out infinite; }}
@keyframes bob {{ 0%, 100% {{ transform: translateY(0); }} 50% {{ transform: translateY(-8px); }} }}
{' '.join(styles)}
@media (prefers-reduced-motion: reduce) {{ .bob, {row_classes} {{ animation: none; }} }}
</style>
<g mask="url(#edges)">{''.join(rows_svg)}</g>
</svg>
"""
