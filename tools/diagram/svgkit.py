"""tools/diagram/ の図で共通に使う部品と見た目。

どの図も同じ配色・文字の大きさにそろえる（ダークモード対応込み）。
座標は図ごとのスクリプトで手で決める。
"""

from pathlib import Path
from xml.sax.saxutils import escape

IMG_DIR = Path(__file__).resolve().parents[2] / "site" / "assets" / "img"

BOX_H = 40

STYLE = """
svg { --ink:#1d272e; --muted:#56616a; --line:#b3b3a6; --soft:#e3e3db; --paper:#f3f4f1; --acc:#1f5fa8; }
@media (prefers-color-scheme: dark) {
  svg { --ink:#e7eae6; --muted:#a4adb3; --line:#3d464d; --soft:#232b31; --paper:#1a2127; --acc:#6aa5ec; }
}
text { font-family: "BIZ UDPGothic", "Hiragino Sans", "Yu Gothic UI", "Meiryo", sans-serif; fill: var(--ink); }
.bg { fill: var(--paper); }
.box { fill: var(--soft); stroke: var(--muted); stroke-width: 1; }
.box.ctrl { stroke: var(--acc); stroke-width: 1.8; }
.grp { fill: none; stroke: var(--line); stroke-width: 1.2; stroke-dasharray: 5 4; }
.t { font-size: 11.5px; font-weight: 700; }
.s { font-size: 9.5px; fill: var(--muted); }
.gname { font-size: 12px; font-weight: 700; }
.gcode { font-size: 10px; font-weight: 400; fill: var(--muted); }
.gpow { font-size: 9px; fill: var(--muted); }
.lbl { font-size: 9px; fill: var(--muted); }
.lbl.acc { fill: var(--acc); }
.leg { font-size: 10px; fill: var(--muted); }
.x { font-size: 16px; font-weight: 700; fill: var(--acc); }
polyline { fill: none; stroke-linejoin: round; stroke-linecap: round; }
.wire { stroke: var(--ink); stroke-width: 1.3; }
.wifi { stroke: var(--acc); stroke-width: 1.5; stroke-dasharray: 5 3; }
.mech { stroke: var(--muted); stroke-width: 1.5; stroke-dasharray: 1.5 3; }
#a path { fill: var(--ink); }
"""


class Diagram:
    def __init__(self, width, height, title):
        self.w, self.h, self.title = width, height, title
        self.parts = []

    def text(self, x, y, s, cls, anchor="middle", extra=""):
        self.parts.append(
            f'<text x="{x}" y="{y}" class="{cls}" text-anchor="{anchor}"{extra}>{escape(s)}</text>'
        )

    def box(self, x, y, w, title, sub, ctrl=False):
        cls = "box ctrl" if ctrl else "box"
        self.parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{BOX_H}" rx="4" class="{cls}"/>')
        cx = x + w / 2
        self.text(cx, y + 17, title, "t")
        self.text(cx, y + 31, sub, "s")

    def line(self, points, cls="wire", start=False, end=True):
        d = " ".join(f"{x},{y}" for x, y in points)
        marks = ""
        if cls == "wire":
            if start:
                marks += ' marker-start="url(#a)"'
            if end:
                marks += ' marker-end="url(#a)"'
        self.parts.append(f'<polyline points="{d}" class="{cls}"{marks}/>')

    def group(self, top, bottom, name, code="", power="", x=4, w=348):
        self.parts.append(
            f'<rect x="{x}" y="{top}" width="{w}" height="{bottom - top}" rx="8" class="grp"/>'
        )
        right = x + w - 10
        tspan = f'<tspan class="gcode" dx="6">{escape(code)}</tspan>' if code else ""
        self.parts.append(
            f'<text x="{right}" y="{top + 18}" class="gname" text-anchor="end">{escape(name)}{tspan}</text>'
        )
        if power:
            self.text(right, bottom - 7, power, "gpow", anchor="end")

    def write(self, filename):
        svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.w} {self.h}" width="{self.w}" height="{self.h}" role="img" aria-labelledby="title">
<title id="title">{escape(self.title)}</title>
<style>{STYLE}</style>
<defs><marker id="a" viewBox="0 0 8 8" refX="7" refY="4" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M0,0.5 L8,4 L0,7.5 z"/></marker></defs>
<rect width="{self.w}" height="{self.h}" class="bg"/>
{chr(10).join(self.parts)}
</svg>
"""
        out = IMG_DIR / filename
        out.write_text(svg, encoding="utf-8", newline="\n")
        print(f"wrote {out}")
