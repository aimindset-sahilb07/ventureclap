"""Generate the VentureClap logo files (SVG + PNG).

Serif V/C monogram (Cormorant Garamond) with a brass slash that runs past the
full height of the letters, plus a spaced-caps wordmark (Inter).

Needs, next to this script: CormorantGaramond.ttf and Inter.ttf (variable fonts
from github.com/google/fonts: ofl/cormorantgaramond, ofl/inter).
Run: python build_logo.py <out_dir>        (pip install fonttools skia-pathops pillow)
"""
import math
import sys
from pathlib import Path

from fontTools.pens.basePen import BasePen
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import OverlapMode, instantiateVariableFont
from PIL import Image, ImageChops, ImageDraw

OUT = Path(sys.argv[1])
HERE = Path(__file__).parent

FOREST = "#0F2A22"
IVORY = "#F4F1EA"
BRASS = "#C9A35A"
BRASS_DEEP = "#A8823A"  # brass on light backgrounds
BLACK = "#0B0B0D"

THEMES = {
    "dark": dict(letters=IVORY, slash=BRASS, word=IVORY),
    "light": dict(letters=FOREST, slash=BRASS_DEEP, word=FOREST),
}


# ---- Fonts ------------------------------------------------------------------------
def load(file, axes):
    # REMOVE merges overlapping contours so every renderer fills letters the same way.
    f = instantiateVariableFont(TTFont(HERE / file), axes, overlap=OverlapMode.REMOVE)
    return f, f.getGlyphSet(), f.getBestCmap(), f["head"].unitsPerEm


SERIF = {w: load("CormorantGaramond.ttf", {"wght": w}) for w in (500, 700)}
SANS = load("Inter.ttf", {"wght": 400, "opsz": 14})


class FlatPen(BasePen):
    """Flatten outlines into polygons (for Pillow)."""

    def __init__(self, gs):
        super().__init__(gs)
        self.polys, self.cur = [], []

    def _moveTo(self, p):
        self.cur = [p]

    def _lineTo(self, p):
        self.cur.append(p)

    def _curveToOne(self, p1, p2, p3):
        p0 = self.cur[-1]
        for i in range(1, 13):
            t = i / 12
            mt = 1 - t
            self.cur.append(tuple(mt**3 * a + 3 * mt * mt * t * b + 3 * mt * t * t * c + t**3 * d for a, b, c, d in zip(p0, p1, p2, p3)))

    def _qCurveToOne(self, p1, p2):
        p0 = self.cur[-1]
        for i in range(1, 9):
            t = i / 8
            mt = 1 - t
            self.cur.append(tuple(mt * mt * a + 2 * mt * t * b + t * t * c for a, b, c in zip(p0, p1, p2)))

    def _closePath(self):
        if self.cur:
            self.polys.append(self.cur)
        self.cur = []

    _endPath = _closePath


class Glyph:
    """One placed glyph: font data + transform (font units -> logo units, y down)."""

    def __init__(self, font, ch, size, x, baseline):
        _, gs, cmap, upm = font
        self.gs, self.name = gs, cmap[ord(ch)]
        s = size / upm
        self.tf = (s, 0, 0, -s, x, baseline)
        self.advance = gs[self.name].width * s

    def _draw(self, pen):
        self.gs[self.name].draw(TransformPen(pen, self.tf))

    def svg(self):
        p = SVGPathPen(self.gs)
        self._draw(p)
        return p.getCommands()

    def polys(self):
        p = FlatPen(self.gs)
        self._draw(p)
        return p.polys

    def bounds(self):
        p = BoundsPen(self.gs)
        self._draw(p)
        return p.bounds  # xmin, ymin, xmax, ymax (y down)


def text_run(font, text, size, x, baseline, tracking=0.0):
    out, pen = [], x
    for ch in text:
        g = Glyph(font, ch, size, pen, baseline)
        out.append(g)
        pen += g.advance + tracking
    return out, pen - tracking - x


# ---- Monogram geometry ---------------------------------------------------------------
def monogram(weight=500, size=48.0, stroke=1.6, clear=4.5, angle=17.0, ext=0.12):
    """Lay out V / C. Returns glyphs, slash polygon and bounds (x0, y0, x1, y1)."""
    font = SERIF[weight]
    base = size  # baseline y; letters sit above it
    V = Glyph(font, "V", size, 0, base)
    vb = V.bounds()
    top, bottom = vb[1], vb[3]
    h = bottom - top
    y_top, y_bot = top - ext * h, bottom + ext * h

    a = math.radians(angle)
    n = (math.cos(a), math.sin(a))  # unit normal pointing right of the slash line

    def side(pt, c):
        return (pt[0] - c[0]) * n[0] + (pt[1] - c[1]) * n[1]

    mid_y = (y_top + y_bot) / 2
    # Slash centre: just right of the V with `clear` units of space.
    v_pts = [p for poly in V.polys() for p in poly]
    cx = max(p[0] + (p[1] - mid_y) * math.tan(a) for p in v_pts) + clear / math.cos(a) + stroke / 2 / math.cos(a)
    centre = (cx, mid_y)
    assert all(side(p, centre) <= -clear for p in v_pts)

    # C: shift right until every point clears the slash by `clear`.
    C0 = Glyph(font, "C", size, 0, base)
    c_min = min(side(p, centre) for poly in C0.polys() for p in poly)
    C = Glyph(font, "C", size, (clear + stroke / 2 - c_min) / n[0], base)

    half = (y_bot - y_top) / 2
    d = (math.sin(a), -math.cos(a))  # direction up along the slash
    t = (cx + d[0] * half / math.cos(a), mid_y + d[1] * half / math.cos(a))
    b = (cx - d[0] * half / math.cos(a), mid_y - d[1] * half / math.cos(a))
    w = (n[0] * stroke / 2, n[1] * stroke / 2)
    slash = [(t[0] - w[0], t[1] - w[1]), (t[0] + w[0], t[1] + w[1]), (b[0] + w[0], b[1] + w[1]), (b[0] - w[0], b[1] - w[1])]

    xs = [p[0] for p in slash] + [V.bounds()[0], C.bounds()[2]]
    ys = [p[1] for p in slash]
    return dict(glyphs=[V, C], slash=slash, bounds=(min(xs), min(ys), max(xs), max(ys)), cap=(top, bottom))


MARK = monogram()
FAV = monogram(weight=700, stroke=4.6, clear=2.6, ext=0.08)


# ---- SVG helpers ----------------------------------------------------------------------
def poly_d(pts):
    return "M" + "L".join(f"{x:.2f} {y:.2f}" for x, y in pts) + "Z"


def fmt(v):
    return f"{v:.2f}".rstrip("0").rstrip(".")


def mark_svg(m, th, dx, dy, k=1.0):
    g = f'<g transform="translate({fmt(dx)} {fmt(dy)}) scale({fmt(k)})">'
    letters = "".join(gl.svg() for gl in m["glyphs"])
    return (f'{g}<path d="{letters}" fill="{th["letters"]}"/>'
            f'<path d="{poly_d(m["slash"])}" fill="{th["slash"]}"/></g>')


def word_svg(run, colour):
    return f'<path d="{"".join(g.svg() for g in run)}" fill="{colour}"/>'


def write_svg(name, w, h, body, label="VentureClap"):
    (OUT / name).write_text(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {fmt(w)} {fmt(h)}" role="img" aria-label="{label}">\n  {body}\n</svg>\n',
        encoding="utf-8",
    )


# ---- Layouts ---------------------------------------------------------------------------
PAD = 2.0
mx0, my0, mx1, my1 = MARK["bounds"]
MW, MH = mx1 - mx0, my1 - my0
cap_top, cap_bot = MARK["cap"]
SANS_CAP_RATIO = SANS[0]["OS/2"].sCapHeight / SANS[3]

# Horizontal lockup: monogram left, wordmark vertically centred on the letters.
WORD_SIZE = 13.0
H_GAP = 16.0
H_W0 = PAD + MW + H_GAP
h_base = PAD - my0 + (cap_top + cap_bot) / 2 + SANS_CAP_RATIO * WORD_SIZE / 2
H_WORD, h_len = text_run(SANS, "VENTURECLAP", WORD_SIZE, H_W0, h_base, 0.32 * WORD_SIZE)
H_W, H_H = H_W0 + h_len + PAD, MH + 2 * PAD

# Stacked lockup: monogram centred above the wordmark.
S_SIZE = 11.0
S_GAP = 14.0
S_CAP = SANS_CAP_RATIO * S_SIZE
_, s_len = text_run(SANS, "VENTURECLAP", S_SIZE, 0, 0, 0.32 * S_SIZE)
S_W = max(MW, s_len) + 2 * PAD
S_WORD, _ = text_run(SANS, "VENTURECLAP", S_SIZE, (S_W - s_len) / 2, PAD + MH + S_GAP + S_CAP, 0.32 * S_SIZE)
S_H = PAD + MH + S_GAP + S_CAP + PAD

for theme, suffix in (("dark", ""), ("light", "-light")):
    th = THEMES[theme]
    write_svg(f"logo-mark{suffix}.svg", MW + 2 * PAD, MH + 2 * PAD, mark_svg(MARK, th, PAD - mx0, PAD - my0), "VentureClap V/C")
    write_svg(f"logo{suffix}.svg", H_W, H_H, mark_svg(MARK, th, PAD - mx0, PAD - my0) + "\n  " + word_svg(H_WORD, th["word"]))
    write_svg(f"logo-stacked{suffix}.svg", S_W, S_H,
              mark_svg(MARK, th, (S_W - MW) / 2 - mx0, PAD - my0) + "\n  " + word_svg(S_WORD, th["word"]))

# Favicon: forest rounded square, heavier monogram.
fx0, fy0, fx1, fy1 = FAV["bounds"]
FK = 56 / max(fx1 - fx0, fy1 - fy0)
write_svg("favicon.svg", 64, 64,
          f'<rect width="64" height="64" rx="12" fill="{FOREST}"/>\n  '
          + mark_svg(FAV, THEMES["dark"], 32 - (fx0 + fx1) / 2 * FK, 32 - (fy0 + fy1) / 2 * FK, FK))


# ---- PNG rendering ----------------------------------------------------------------------
def render(px, m, fill_frac, bg=FOREST, radius=0.0, ss=8):
    """Monogram centred on a px*px square; `fill_frac` = share of the square it spans."""
    big = px * ss
    img = Image.new("RGBA", (big, big), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 0, big - 1, big - 1], radius=radius * big, fill=bg)
    x0, y0, x1, y1 = m["bounds"]
    k = big * fill_frac / max(x1 - x0, y1 - y0)
    ox = big / 2 - (x0 + x1) / 2 * k
    oy = big / 2 - (y0 + y1) / 2 * k

    def tr(poly):
        return [(ox + x * k, oy + y * k) for x, y in poly]

    mask = Image.new("1", (big, big), 0)
    for gl in m["glyphs"]:
        for poly in gl.polys():
            layer = Image.new("1", (big, big), 0)
            ImageDraw.Draw(layer).polygon(tr(poly), fill=1)
            mask = ImageChops.logical_xor(mask, layer)
    img.paste(Image.new("RGBA", (big, big), IVORY), (0, 0), mask.convert("L"))
    d.polygon(tr(m["slash"]), fill=BRASS)
    return img.resize((px, px), Image.LANCZOS)


if __name__ == "__main__":
    render(1080, MARK, 0.52).convert("RGB").save(OUT / "avatar-1080.png")
    render(180, MARK, 0.62).convert("RGB").save(OUT / "apple-touch-icon.png")
    render(32, FAV, 56 / 64, radius=12 / 64).save(OUT / "favicon-32.png")
    render(16, FAV, 60 / 64, radius=10 / 64).save(OUT / "favicon-16.png")
    print("wrote", sorted(p.name for p in OUT.iterdir() if not p.name.startswith("_")))
