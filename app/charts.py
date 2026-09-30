"""Static SVG charts for the React client, which has no chart widget yet."""

import math
from html import escape

LINE = "#1f6feb"
GRID = "#e5e7eb"
INK = "#57606a"
FONT = "font-family='Roboto, Helvetica, Arial, sans-serif' font-size='12'"


def nice_max(value):
    if value <= 0:
        return 1
    step = 10 ** math.floor(math.log10(value))
    for m in (1, 2, 2.5, 5, 10):
        if value <= m * step:
            return m * step
    return 10 * step


def line_svg(xs, ys, unit="", width=680, height=260):
    """One series over categorical x labels: 2px line, 8px markers, 4 recessive gridlines, peak labeled."""
    left, right, top, bottom = 44, 16, 18, 58
    w, h = width - left - right, height - top - bottom
    top_value = nice_max(max(ys, default=0))
    n = max(len(xs), 1)
    x = lambda i: left + (w * i / (n - 1) if n > 1 else w / 2)
    y = lambda v: top + h - h * v / top_value
    parts = [f"<svg xmlns='http://www.w3.org/2000/svg' width='{width}' height='{height}' "
             f"viewBox='0 0 {width} {height}'><rect width='100%' height='100%' fill='white'/>"]
    for k in range(5):
        v = top_value * k / 4
        gy = y(v)
        parts.append(f"<line x1='{left}' x2='{left + w}' y1='{gy:.1f}' y2='{gy:.1f}' stroke='{GRID}'/>")
        parts.append(f"<text x='{left - 6}' y='{gy + 4:.1f}' text-anchor='end' fill='{INK}' {FONT}>"
                     f"{v:g}{escape(unit)}</text>")
    every = max(1, math.ceil(n / 16))
    for i, label in enumerate(xs):
        if i % every == 0 or i == n - 1:
            lx, ly = x(i), top + h + 12
            parts.append(f"<text x='{lx:.1f}' y='{ly}' text-anchor='end' fill='{INK}' {FONT} "
                         f"transform='rotate(-45 {lx:.1f} {ly})'>{escape(str(label))}</text>")
    if ys:
        points = " ".join(f"{x(i):.1f},{y(v):.1f}" for i, v in enumerate(ys))
        parts.append(f"<polyline points='{points}' fill='none' stroke='{LINE}' stroke-width='2' "
                     f"stroke-linejoin='round' stroke-linecap='round'/>")
        for i, v in enumerate(ys):
            parts.append(f"<circle cx='{x(i):.1f}' cy='{y(v):.1f}' r='4' fill='{LINE}' stroke='white' "
                         f"stroke-width='2'/>")
        peak = max(range(len(ys)), key=ys.__getitem__)
        px, py = x(peak), y(ys[peak])
        anchor = "end" if px > left + 0.8 * w else "start" if px < left + 0.2 * w else "middle"
        parts.append(f"<text x='{px:.1f}' y='{max(py - 9, 11):.1f}' text-anchor='{anchor}' fill='#1f2328' "
                     f"{FONT}>peak {ys[peak]:.1f}{escape(unit)} ({escape(str(xs[peak]))})</text>")
    parts.append("</svg>")
    return "".join(parts)
