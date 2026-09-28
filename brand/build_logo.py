"""Generate the VentureClap logo files (SVG + PNG) from one set of geometry.

Run: venv/Scripts/python build_logo.py <out_dir>
"""
import math
import sys
from pathlib import Path

from fontTools.pens.basePen import BasePen
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import OverlapMode, instantiateVariableFont
from PIL import Image, ImageDraw

OUT = Path(sys.argv[1])
HERE = Path(__file__).parent

BLACK = "#0B0B0D"
GREEN = "#2EE59D"
GREEN_DARK = "#0A8F57"
GOLD = "#F5B82E"
WHITE = "#FFFFFF"

THEMES = {
    "dark": dict(board=GREEN, arm=WHITE, arm_stripe=BLACK, bar_stripe=BLACK, text=BLACK,
                 slash=GOLD, slash_edge=BLACK, hinge=BLACK, hinge_ring=WHITE,
                 word1=WHITE, word2=GREEN),
    "light": dict(board=GREEN_DARK, arm=BLACK, arm_stripe=WHITE, bar_stripe=BLACK, text=BLACK,
                  slash=GOLD, slash_edge=BLACK, hinge=WHITE, hinge_ring=BLACK,
                  word1=BLACK, word2=GREEN_DARK),
}

# ---- Mark geometry (64x64 units) -------------------------------------------
ANGLE = -18  # clapper arm swing, degrees
HINGE = (6.0, 25.0)  # arm pivots on its bottom-left corner
ARM = (6.0, 18.0, 52.0, 7.0)  # x, y, w, h (before rotation)
BAR = (6.0, 25.5, 52.0, 6.0)
BODY = (6.0, 32.5, 52.0, 29.5)
STRIPE_W, STRIPE_SLANT, STRIPE_STEP, STRIPE_START = 7.0, 4.5, 14.0, 12.0


def stripes(x, y, w, h):
    """Parallelogram stripes across a bar, clipped to the bar's width."""
    polys = []
    sx = x + STRIPE_START
    while sx + STRIPE_W <= x + w:
        polys.append([(sx, y), (sx + STRIPE_W, y), (sx + STRIPE_W - STRIPE_SLANT, y + h), (sx - STRIPE_SLANT, y + h)])
        sx += STRIPE_STEP
    return polys


def rot(pts, deg=ANGLE, c=HINGE):
    a = math.radians(deg)
    ca, sa = math.cos(a), math.sin(a)
    return [(c[0] + (px - c[0]) * ca - (py - c[1]) * sa, c[1] + (px - c[0]) * sa + (py - c[1]) * ca) for px, py in pts]


def rect_pts(x, y, w, h):
    return [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]


# ---- Font -> paths ------------------------------------------------------------
# REMOVE merges overlapping contours so every renderer fills letters the same way (needs skia-pathops).
font = instantiateVariableFont(TTFont(HERE / "InterTight.ttf"), {"wght": 800}, overlap=OverlapMode.REMOVE)
glyphs = font.getGlyphSet()
cmap = font.getBestCmap()
UPM = font["head"].unitsPerEm
CAP = font["OS/2"].sCapHeight


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


def layout(text, size, x, baseline, tracking=0.0):
    """Return [(glyph_name, transform)] placing text with its baseline at `baseline`."""
    s = size / UPM
    out, pen_x = [], x
    for ch in text:
        g = cmap[ord(ch)]
        out.append((g, (s, 0, 0, -s, pen_x, baseline)))
        pen_x += glyphs[g].width * s + tracking
    return out, pen_x - tracking - x


def svg_path(g, tf):
    p = SVGPathPen(glyphs)
    glyphs[g].draw(TransformPen(p, tf))
    return p.getCommands()


def flat_polys(g, tf):
    p = FlatPen(glyphs)
    glyphs[g].draw(TransformPen(p, tf))
    return p.polys


# V/C inside the board: fit the cap height to the board, center it.
VC_SIZE = 25.0
_, vc_w = layout("V/C", VC_SIZE, 0, 0, tracking=-0.6)
vc_x = BODY[0] + (BODY[2] - vc_w) / 2
vc_base = BODY[1] + BODY[3] / 2 + (CAP * VC_SIZE / UPM) / 2
VC, _ = layout("V/C", VC_SIZE, vc_x, vc_base, tracking=-0.6)


# ---- SVG output -----------------------------------------------------------------
def poly_d(pts):
    return "M" + "L".join(f"{x:.2f} {y:.2f}" for x, y in pts) + "Z"


def mark_svg(t, dx=0.0):
    th = THEMES[t]
    arm = rot(rect_pts(*ARM))
    arm_stripes = [rot(p) for p in stripes(*ARM)]
    bx, by, bw, bh = BAR
    ox, oy, ow, oh = BODY
    parts = [
        f'<g transform="translate({dx} 0)">',
        f'<rect x="{bx}" y="{by}" width="{bw}" height="{bh}" rx="1.5" fill="{th["board"]}"/>',
        f'<path d="{"".join(poly_d(p) for p in stripes(*BAR))}" fill="{th["bar_stripe"]}"/>',
        f'<rect x="{ox}" y="{oy}" width="{ow}" height="{oh}" rx="5" fill="{th["board"]}"/>',
        f'<path d="{poly_d(arm)}" fill="{th["arm"]}" stroke="{th["arm"]}" stroke-width="1" stroke-linejoin="round"/>',
        f'<path d="{"".join(poly_d(p) for p in arm_stripes)}" fill="{th["arm_stripe"]}"/>',
        f'<circle cx="{HINGE[0] + 2}" cy="{HINGE[1] - 0.5}" r="2.6" fill="{th["hinge"]}" stroke="{th["hinge_ring"]}" stroke-width="1.4"/>',
    ]
    for g, tf in VC:
        if g == cmap[ord("/")]:
            parts.append(f'<path d="{svg_path(g, tf)}" fill="{th["slash"]}" stroke="{th["slash_edge"]}" stroke-width="1.6" paint-order="stroke" stroke-linejoin="round"/>')
        else:
            parts.append(f'<path d="{svg_path(g, tf)}" fill="{th["text"]}"/>')
    parts.append("</g>")
    return "\n  ".join(parts)


def write_svg(name, body, w, h, label="VentureClap"):
    (OUT / name).write_text(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w:.0f} {h:.0f}" role="img" aria-label="{label}">\n  {body}\n</svg>\n',
        encoding="utf-8",
    )


WORD_SIZE = 38.0
TEXT_X = 70
word1, w1 = layout("Venture", WORD_SIZE, TEXT_X, 47, tracking=-1.0)
word2, w2 = layout("Clap", WORD_SIZE, TEXT_X + w1 - 0.6, 47, tracking=-1.0)
LOCKUP_W = TEXT_X + w1 + w2 + 4

for t, suffix in (("dark", ""), ("light", "-light")):
    th = THEMES[t]
    write_svg(f"logo-mark{suffix}.svg", mark_svg(t), 64, 64, "VentureClap V/C")
    words = "".join(svg_path(g, tf) for g, tf in word1)
    words2 = "".join(svg_path(g, tf) for g, tf in word2)
    write_svg(
        f"logo{suffix}.svg",
        mark_svg(t) + f'\n  <path d="{words}" fill="{th["word1"]}"/>\n  <path d="{words2}" fill="{th["word2"]}"/>',
        LOCKUP_W, 64,
    )


# ---- PNG output (8x supersampled) --------------------------------------------------
def render_mark(px, theme="dark", bg=None, pad=0.0):
    """Render the mark to a px*px PNG. `pad` is the fraction of empty margin per side."""
    th = THEMES[theme]
    ss = 8
    big = px * ss
    img = Image.new("RGBA", (big, big), bg or (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    inner = big * (1 - 2 * pad)
    k = inner / 64
    off = big * pad

    def m(pts):
        return [(off + x * k, off + y * k) for x, y in pts]

    bx, by, bw, bh = BAR
    d.rounded_rectangle([off + bx * k, off + by * k, off + (bx + bw) * k, off + (by + bh) * k], radius=1.5 * k, fill=th["board"])
    for p in stripes(*BAR):
        d.polygon(m(p), fill=th["bar_stripe"])
    ox, oy, ow, oh = BODY
    d.rounded_rectangle([off + ox * k, off + oy * k, off + (ox + ow) * k, off + (oy + oh) * k], radius=5 * k, fill=th["board"])
    d.polygon(m(rot(rect_pts(*ARM))), fill=th["arm"])
    for p in stripes(*ARM):
        d.polygon(m(rot(p)), fill=th["arm_stripe"])
    hx, hy, r = off + (HINGE[0] + 2) * k, off + (HINGE[1] - 0.5) * k, 2.6 * k
    d.ellipse([hx - r, hy - r, hx + r, hy + r], fill=th["hinge"], outline=th["hinge_ring"], width=max(1, round(1.4 * k)))
    for g, tf in VC:
        for poly in flat_polys(g, tf):
            if g == cmap[ord("/")]:
                d.polygon(m(poly), fill=th["slash"], outline=th["slash_edge"], width=max(1, round(0.8 * k)))
            else:
                d.polygon(m(poly), fill=th["text"])
    return img.resize((px, px), Image.LANCZOS)


# ---- Favicon: simplified for 16-32px (board + striped top, big V/C, no swinging arm) ----
FAV_BAR = (2.0, 3.0, 60.0, 11.0)
FAV_BODY = (2.0, 16.0, 60.0, 46.0)
FAV_SIZE = 36.0
_, fw = layout("V/C", FAV_SIZE, 0, 0, tracking=-1.5)
FAV_VC, _ = layout("V/C", FAV_SIZE, FAV_BODY[0] + (FAV_BODY[2] - fw) / 2,
                   FAV_BODY[1] + FAV_BODY[3] / 2 + (CAP * FAV_SIZE / UPM) / 2, tracking=-1.5)


def fav_stripes():
    x, y, w, h = FAV_BAR
    return [[(sx, y), (sx + 9, y), (sx + 4, y + h), (sx - 5, y + h)] for sx in (12, 28, 44, 60) if sx - 5 < x + w]


def favicon_svg():
    th = THEMES["dark"]
    bx, by, bw, bh = FAV_BAR
    ox, oy, ow, oh = FAV_BODY
    clip = f'<clipPath id="b"><rect x="{bx}" y="{by}" width="{bw}" height="{bh}" rx="3"/></clipPath>'
    parts = [
        f"<defs>{clip}</defs>",
        f'<rect x="{bx}" y="{by}" width="{bw}" height="{bh}" rx="3" fill="{th["arm"]}"/>',
        f'<path clip-path="url(#b)" d="{"".join(poly_d(p) for p in fav_stripes())}" fill="{BLACK}"/>',
        f'<rect x="{ox}" y="{oy}" width="{ow}" height="{oh}" rx="7" fill="{th["board"]}"/>',
    ]
    for g, tf in FAV_VC:
        fill = GOLD if g == cmap[ord("/")] else BLACK
        extra = f' stroke="{BLACK}" stroke-width="2" paint-order="stroke"' if fill == GOLD else ""
        parts.append(f'<path d="{svg_path(g, tf)}" fill="{fill}"{extra}/>')
    return "\n  ".join(parts)


def render_favicon(px):
    ss = 8
    big = px * ss
    k = big / 64
    img = Image.new("RGBA", (big, big), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    bx, by, bw, bh = FAV_BAR
    band = Image.new("RGBA", (big, big), (0, 0, 0, 0))
    bd = ImageDraw.Draw(band)
    bd.rectangle([0, 0, big, big], fill=WHITE)
    for p in fav_stripes():
        bd.polygon([(x * k, y * k) for x, y in p], fill=BLACK)
    mask = Image.new("L", (big, big), 0)
    ImageDraw.Draw(mask).rounded_rectangle([bx * k, by * k, (bx + bw) * k, (by + bh) * k], radius=3 * k, fill=255)
    img.paste(band, (0, 0), mask)
    ox, oy, ow, oh = FAV_BODY
    d.rounded_rectangle([ox * k, oy * k, (ox + ow) * k, (oy + oh) * k], radius=7 * k, fill=GREEN)
    for g, tf in FAV_VC:
        for poly in flat_polys(g, tf):
            pts = [(x * k, y * k) for x, y in poly]
            if g == cmap[ord("/")]:
                d.polygon(pts, fill=GOLD, outline=BLACK, width=round(1.0 * k))
            else:
                d.polygon(pts, fill=BLACK)
    return img.resize((px, px), Image.LANCZOS)


write_svg("favicon.svg", favicon_svg(), 64, 64, "VentureClap")
render_mark(1080, bg=BLACK, pad=0.16).convert("RGB").save(OUT / "avatar-1080.png")
render_mark(180, bg=BLACK, pad=0.08).convert("RGB").save(OUT / "apple-touch-icon.png")
render_favicon(32).save(OUT / "favicon-32.png")
render_favicon(16).save(OUT / "favicon-16.png")
print("wrote", sorted(p.name for p in OUT.iterdir()))
