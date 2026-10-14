"""Shared renderer for pseudo-3D orbit SVGs.

Items travel around tilted elliptical rings: large and sharp in front, small
and faded behind. Each item is drawn twice, in a back layer and a front layer,
and the two copies cross-fade at the ring's sides. That keeps depth ordering
correct around the centre piece, which SVG cannot reorder at runtime.
Images live once in <defs> and are reused, so the doubling costs no size.
"""
import base64
import math
import time
import urllib.request
from dataclasses import dataclass

WIDTH = 800
ICON = 52
STEPS = 24  # keyframes per revolution; multiple of 4 so the sides land on a step
BACK_SCALE = 0.5
BACK_OPACITY = 0.45
FETCH_ATTEMPTS = 3


@dataclass(frozen=True)
class Item:
    data_uri: str
    label: str
    rounded: bool = False


@dataclass(frozen=True)
class Ring:
    items: tuple
    rx: float
    ry: float
    seconds: int
    clockwise: bool = True


@dataclass(frozen=True)
class Theme:
    label: str
    core_fill: str
    core_glow: str
    core_text: str


def fetch_data_uri(url: str, mime: str) -> str:
    """Download an image as a data URI, retrying transient network errors."""
    req = urllib.request.Request(url, headers={"User-Agent": "profile-orbit-builder"})
    for attempt in range(1, FETCH_ATTEMPTS + 1):
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return f"data:{mime};base64,{base64.b64encode(resp.read()).decode()}"
        except OSError as err:  # URLError, HTTPError and socket timeouts
            if attempt == FETCH_ATTEMPTS:
                raise RuntimeError(f"failed to fetch {url}: {err}") from err
            time.sleep(2 * attempt)
    raise AssertionError("unreachable")


def _keyframes(name: str, ring: Ring, cx: float, cy: float, front: bool) -> str:
    frames = []
    for step in range(STEPS + 1):
        theta = 2 * math.pi * step / STEPS
        depth = math.cos(theta)  # 1 = nearest the viewer, -1 = farthest
        x = cx + ring.rx * math.sin(theta)
        y = cy + ring.ry * depth
        scale = BACK_SCALE + (1 - BACK_SCALE) * (depth + 1) / 2
        is_front = depth > 1e-9 or (abs(depth) <= 1e-9 and front)
        opacity = (1 if is_front else 0) if front else (0 if is_front else BACK_OPACITY)
        frames.append(
            f"{100 * step / STEPS:.3f}% {{ transform: translate({x:.1f}px,{y:.1f}px) scale({scale:.3f}); opacity: {opacity}; }}"
        )
    return f"@keyframes {name} {{ {' '.join(frames)} }}"


def _layer(ring_idx: int, ring: Ring, front: bool) -> str:
    anim = f"r{ring_idx}{'f' if front else 'b'}"
    direction = "normal" if ring.clockwise else "reverse"
    count = len(ring.items)
    out = []
    for i, item in enumerate(ring.items):
        # Odd rings start half a slot later so items on different rings never line up.
        delay = -ring.seconds * (i + 0.5 * (ring_idx % 2)) / count
        out.append(
            f'<g style="animation: {anim} {ring.seconds}s linear {delay:.2f}s infinite {direction}">'
            f'<use href="#i{ring_idx}_{i}" x="{-ICON / 2}" y="{-ICON / 2}"/>'
            f'<text y="{ICON / 2 + 16}" text-anchor="middle">{item.label}</text></g>'
        )
    return "".join(out)


def _core(cx: float, cy: float, theme: Theme, core_uri: str, core_text: str) -> str:
    size = 84
    inner = (
        f'<image x="{cx - size / 2}" y="{cy - size / 2}" width="{size}" height="{size}" clip-path="url(#coreclip)" href="{core_uri}"/>'
        if core_uri
        else f'<circle cx="{cx}" cy="{cy}" r="{size / 2}" fill="{theme.core_fill}"/>'
        f'<text class="core" x="{cx}" y="{cy + 9}" text-anchor="middle">{core_text}</text>'
    )
    return (
        f'<circle class="pulse" cx="{cx}" cy="{cy}" r="{size / 2 + 6}" fill="{theme.core_glow}"/>'
        f'<circle class="pulse late" cx="{cx}" cy="{cy}" r="{size / 2 + 6}" fill="{theme.core_glow}"/>'
        f"{inner}"
    )


def render(rings: list, theme: Theme, core_uri: str = "", core_text: str = "") -> str:
    outer_ry = max(r.ry for r in rings)
    height = int(2 * outer_ry + ICON + 70)
    cx, cy = WIDTH / 2, height / 2 - 6
    defs = "".join(
        f'<image id="i{r}_{i}" width="{ICON}" height="{ICON}"{" clip-path=" + chr(34) + "url(#round)" + chr(34) if item.rounded else ""} href="{item.data_uri}"/>'
        for r, ring in enumerate(rings) for i, item in enumerate(ring.items)
    )
    keyframes = " ".join(
        _keyframes(f"r{r}{suffix}", ring, cx, cy, suffix == "f")
        for r, ring in enumerate(rings) for suffix in ("b", "f")
    )
    # Paint order: outer rings' backs, inner backs, core, inner fronts, outer fronts.
    order = sorted(range(len(rings)), key=lambda r: -rings[r].rx)
    backs = "".join(_layer(r, rings[r], False) for r in order)
    fronts = "".join(_layer(r, rings[r], True) for r in reversed(order))
    return f"""<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="{WIDTH}" height="{height}" viewBox="0 0 {WIDTH} {height}">
<defs>
<clipPath id="round" clipPathUnits="objectBoundingBox"><rect width="1" height="1" rx=".24"/></clipPath>
<clipPath id="coreclip" clipPathUnits="objectBoundingBox"><circle cx=".5" cy=".5" r=".5"/></clipPath>
{defs}
</defs>
<style>
text {{ font: 600 12px -apple-system, 'Segoe UI', Helvetica, Arial, sans-serif; fill: {theme.label}; }}
text.core {{ font: 700 26px ui-monospace, 'SF Mono', Menlo, monospace; fill: {theme.core_text}; }}
.pulse {{ transform-box: fill-box; transform-origin: center; animation: pulse 2.8s ease-out infinite; }}
.late {{ animation-delay: 1.4s; }}
@keyframes pulse {{ 0% {{ transform: scale(1); opacity: .55; }} 100% {{ transform: scale(1.9); opacity: 0; }} }}
{keyframes}
@media (prefers-reduced-motion: reduce) {{ * {{ animation-play-state: paused !important; }} }}
</style>
{backs}
{_core(cx, cy, theme, core_uri, core_text)}
{fronts}
</svg>
"""
