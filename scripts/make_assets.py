"""Generate the graphics for the GitHub profile README (Mohammed-Sufiyan/Mohammed-Sufiyan).

usage: python profile_assets.py <profile_repo_dir> <fonts_dir> <portfolio_site_dir> <injury_time_repo>
Text is converted to outlines, so the SVGs look identical everywhere (GitHub can't load web fonts in <img>).
"""
import io
import os
import shutil
import sys
from xml.sax.saxutils import escape

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer
from PIL import Image, ImageDraw, ImageFilter

REPO, FONTS, SITE, INJ = sys.argv[1:5]
OUT = os.path.join(REPO, "assets")
os.makedirs(OUT, exist_ok=True)

# portfolio palette (site/styles.css)
DARK = dict(bg="#0D0E1A", bg2="#151732", card="#171930", ink="#F4F1EA", ink2="#A9A8B8",
            blue="#7C8CFF", orange="#FF6B35", lime="#C6FF3D", accent="#C6FF3D", grid="#2A2D52")
LIGHT = dict(bg="#FAF6EE", bg2="#F2ECDF", card="#FFFFFF", ink="#16161D", ink2="#55545E",
             blue="#1F3BFF", orange="#FF5A1F", lime="#C6FF3D", accent="#1F3BFF", grid="#E2D9C6")
REDUCED = "@media (prefers-reduced-motion: reduce) { * { animation: none !important; } }"


def load(name, wght=None):
    f = TTFont(os.path.join(FONTS, name))
    if wght is not None:
        f = instancer.instantiateVariableFont(f, {"wght": wght})
    return f


SERIF = load("InstrumentSerif-Italic.ttf")
MONO = load("JetBrainsMono[wght].ttf", 500)
MONO_B = load("JetBrainsMono[wght].ttf", 700)
SANS_B = load("InterTight[wght].ttf", 800)
SANS_M = load("InterTight[wght].ttf", 600)


def glyphs(font, text, size, x, y, spacing=0.0):
    """Return ([(char, d, x_start, advance)], total_width) with text outlined at baseline y."""
    gs, cmap, hmtx = font.getGlyphSet(), font.getBestCmap(), font["hmtx"]
    s = size / font["head"].unitsPerEm
    out, cx = [], x
    for ch in text:
        g = cmap.get(ord(ch))
        if g is None:
            g = cmap[ord("?")]
        adv = hmtx[g][0] * s
        pen = SVGPathPen(gs, ntos=lambda v: f"{v:.1f}".rstrip("0").rstrip("."))
        gs[g].draw(TransformPen(pen, (s, 0, 0, -s, cx, y)))
        out.append((ch, pen.getCommands(), cx, adv))
        cx += adv + spacing
    return out, cx - x - spacing


def text(font, txt, size, x, y, spacing=0.0, anchor="start"):
    _, w = glyphs(font, txt, size, 0, 0, spacing)
    if anchor == "middle":
        x -= w / 2
    elif anchor == "end":
        x -= w
    gl, w = glyphs(font, txt, size, x, y, spacing)
    return "".join(d for _, d, _, _ in gl if d), w


def write(name, svg):
    with open(os.path.join(OUT, name), "w", encoding="utf-8", newline="\n") as f:
        f.write(svg)
    print(f"{name:28s} {len(svg) // 1024:4d} KB")


def football(r, dark_patch="#16161D"):
    """A classic ball centred on 0,0."""
    import math
    def pent(cx, cy, rr, rot=-90):
        pts = [(cx + rr * math.cos(math.radians(rot + 72 * k)), cy + rr * math.sin(math.radians(rot + 72 * k))) for k in range(5)]
        return "M" + "L".join(f"{a:.1f},{b:.1f}" for a, b in pts) + "Z"
    patches = [pent(0, 0, r * 0.36)]
    lines = []
    for k in range(5):
        a = math.radians(-90 + 72 * k)
        patches.append(pent(r * 1.02 * math.cos(a), r * 1.02 * math.sin(a), r * 0.36, -90 + 72 * k + 36))
        lines.append(f"M{r*0.36*math.cos(a):.1f},{r*0.36*math.sin(a):.1f}L{r*0.68*math.cos(a):.1f},{r*0.68*math.sin(a):.1f}")
    cid = f"ball{int(r)}"
    return (f'<clipPath id="{cid}"><circle r="{r}"/></clipPath>'
            f'<circle r="{r}" fill="#FFFFFF"/>'
            f'<g clip-path="url(#{cid})" fill="{dark_patch}"><path d="{"".join(patches)}"/>'
            f'<path d="{"".join(lines)}" stroke="{dark_patch}" stroke-width="{r*0.07:.1f}"/></g>'
            f'<circle r="{r - 0.75}" fill="none" stroke="{dark_patch}" stroke-width="1.5"/>')


# ------------------------------------------------------------------ banner
def banner(P, mode):
    W, H = 1280, 400
    hello, _ = text(MONO, "// hello, world. I'm", 22, 98, 118)
    first, wf = glyphs(SERIF, "Mohammed ", 124, 92, 236)
    last, wl = glyphs(SERIF, "Sufiyan", 124, 92 + wf, 236)
    name_end = 92 + wf + wl
    tag, _ = text(MONO, "AI/ML developer  ·  Python  ·  FastAPI  ·  football models  ·  Flutter apps", 20, 98, 318)
    seven, _ = text(SANS_B, "07", 300, 1236, 340, anchor="end")
    sticker, _ = text(MONO_B, "INJURY TIME FC  ·  NO. 07", 13, 0, 5, spacing=1.2, anchor="middle")

    letters = []
    for i, (ch, d, _, _) in enumerate(first + last):
        if not d:
            continue
        col = P["ink"] if i < len(first) else P["orange"]
        letters.append(f'<path class="l" style="--d:{0.25 + i * 0.09:.2f}s" d="{d}" fill="{col}" stroke="{col}" pathLength="1"/>')

    swoosh_w = wl + 10
    sx = 92 + wf + 6
    swoosh = f"M{sx:.0f},262 C{sx + swoosh_w * 0.3:.0f},250 {sx + swoosh_w * 0.7:.0f},254 {sx + swoosh_w:.0f},246"
    marker = P["lime"] if mode == "dark" else P["lime"]
    ball_x = min(name_end + 120, 1080)

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="Hi, I'm Mohammed Sufiyan. ML engineer, Python, FastAPI, football models, Flutter apps.">
<title>Mohammed Sufiyan</title>
<defs>
  <pattern id="dots" width="28" height="28" patternUnits="userSpaceOnUse"><circle cx="2" cy="2" r="1.3" fill="{P['grid']}"/></pattern>
  <filter id="blur" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="60"/></filter>
  <linearGradient id="fade" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{P['bg']}" stop-opacity="0"/><stop offset="1" stop-color="{P['bg']}"/></linearGradient>
  <clipPath id="card"><rect width="{W}" height="{H}" rx="22"/></clipPath>
</defs>
<style>
  .glow {{ animation: drift 14s ease-in-out infinite alternate; transform-box: fill-box; transform-origin: center; }}
  .g2 {{ animation-duration: 18s; animation-delay: -6s; }}
  .g3 {{ animation-duration: 11s; animation-delay: -3s; }}
  @keyframes drift {{ from {{ transform: translate(-40px, -20px) scale(1); }} to {{ transform: translate(50px, 30px) scale(1.15); }} }}
  .l {{ stroke-width: 1.4; stroke-dasharray: 1; fill-opacity: 1; stroke-dashoffset: 0;
        animation: draw 1.3s ease-out var(--d) both, fillin .6s ease-out calc(var(--d) + .7s) both; }}
  @keyframes draw {{ from {{ stroke-dashoffset: 1; }} to {{ stroke-dashoffset: 0; }} }}
  @keyframes fillin {{ from {{ fill-opacity: 0; }} to {{ fill-opacity: 1; }} }}
  .fade {{ animation: up .8s ease-out both; }}
  @keyframes up {{ from {{ opacity: 0; transform: translateY(12px); }} to {{ opacity: 1; transform: none; }} }}
  .swoosh {{ stroke-dasharray: 1; animation: draw .7s ease-out 2.2s both; }}
  .roll {{ animation: roll 2.2s cubic-bezier(.2,.75,.25,1) 1.4s both; }}
  @keyframes roll {{ from {{ transform: translateX(-{ball_x + 80}px); }} to {{ transform: none; }} }}
  .spin {{ transform-box: fill-box; transform-origin: center; animation: spin 2.2s cubic-bezier(.2,.75,.25,1) 1.4s both; }}
  @keyframes spin {{ from {{ transform: rotate(-1080deg); }} to {{ transform: none; }} }}
  .bounce {{ animation: bounce 2.6s ease-in-out 3.8s infinite; }}
  @keyframes bounce {{ 0%, 55%, 100% {{ transform: none; }} 70% {{ transform: translateY(-34px); }} 85% {{ transform: translateY(0); }} 92% {{ transform: translateY(-8px); }} }}
  .shadow {{ transform-box: fill-box; transform-origin: center; animation: shadow 2.6s ease-in-out 3.8s infinite; }}
  @keyframes shadow {{ 0%, 55%, 100% {{ transform: none; opacity: .35; }} 70% {{ transform: scale(.6); opacity: .15; }} 85% {{ transform: none; opacity: .35; }} }}
  .sticker {{ animation: wobble 5s ease-in-out 3s infinite; transform-box: fill-box; transform-origin: center; }}
  @keyframes wobble {{ 0%, 80%, 100% {{ transform: rotate(-6deg); }} 85% {{ transform: rotate(-10deg) scale(1.06); }} 90% {{ transform: rotate(-3deg) scale(1.06); }} }}
  {REDUCED}
</style>
<g clip-path="url(#card)">
  <rect width="{W}" height="{H}" fill="{P['bg']}"/>
  <rect width="{W}" height="{H}" fill="url(#dots)"/>
  <g filter="url(#blur)" opacity="{'.55' if mode == 'dark' else '.32'}">
    <circle class="glow" cx="160" cy="40" r="170" fill="{P['blue']}"/>
    <circle class="glow g2" cx="1120" cy="110" r="160" fill="{P['orange']}"/>
    <circle class="glow g3" cx="720" cy="430" r="150" fill="{P['lime']}"/>
  </g>
  <path d="{seven}" fill="none" stroke="{P['ink2']}" stroke-opacity=".22" stroke-width="2"/>
  <rect y="{H - 90}" width="{W}" height="90" fill="url(#fade)" opacity=".7"/>

  <path class="fade" style="animation-delay:.1s" d="{hello}" fill="{P['accent']}"/>
  <path class="swoosh" d="{swoosh}" fill="none" stroke="{marker}" stroke-width="14" stroke-linecap="round" opacity="{'.9' if mode == 'dark' else '1'}" pathLength="1"/>
  {''.join(letters)}
  <path class="fade" style="animation-delay:2.4s" d="{tag}" fill="{P['ink2']}"/>

  <g transform="translate({ball_x},342)">
    <ellipse class="shadow" cx="0" cy="26" rx="22" ry="5" fill="{P['ink']}" opacity=".35"/>
    <g class="roll"><g class="bounce"><g class="spin">{football(24)}</g></g></g>
  </g>

  <g transform="translate(1110,62)">
    <g class="sticker fade" style="animation-delay:2.8s">
      <rect x="-118" y="-17" width="236" height="34" rx="17" fill="{P['lime']}"/>
      <path d="{sticker}" fill="#16161D"/>
    </g>
  </g>
</g>
<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="22" fill="none" stroke="{P['grid']}"/>
</svg>"""
    write(f"banner-{mode}.svg", svg)


# ------------------------------------------------------------------ typing line
PHRASES = [
    "building football prediction models",
    "turning messy data into good decisions",
    "shipping FastAPI backends & Flutter apps",
    "making people laugh while coding",
]


def typing(P, mode):
    """Typewriter line using SMIL (works in GitHub's <img> rendering, unlike CSS transforms on clip paths)."""
    W, H, size = 900, 52, 24
    per, T = 5.0, 5.0 * len(PHRASES)
    adv = MONO["hmtx"][MONO.getBestCmap()[ord("a")]][0] * size / MONO["head"].unitsPerEm
    body = []
    for i, ph in enumerate(PHRASES):
        full = "> " + ph
        n = len(full)
        x0 = (W - n * adv) / 2
        prompt, _ = text(MONO_B, ">", size, x0, 34)
        rest, _ = text(MONO, ph, size, x0 + 2 * adv, 34)
        t0, t_in, t_hold, t_out = i * per, 1.9, 4.0, 0.6
        # (time, chars visible) pairs, discrete
        frames = [(0.0, 0)]
        frames += [(t0 + t_in * k / n, k) for k in range(1, n + 1)]
        frames += [(t0 + t_hold + t_out * k / n, n - k) for k in range(1, n + 1)]
        frames = sorted({round(t / T, 5): c for t, c in frames if t < T}.items())
        if frames[0][0] != 0:
            frames.insert(0, (0.0, 0))
        kt = ";".join(f"{t:g}" for t, _ in frames)
        widths = ";".join(f"{c * adv:.1f}" for _, c in frames)
        xs = ";".join(f"{x0 + c * adv + 2:.1f}" for _, c in frames)
        on_a, on_b = t0 / T, min((t0 + t_hold + t_out + 0.05) / T, 0.99999)
        vis_kt = "0;" + (f"{on_a:g};" if on_a > 0 else "") + f"{on_b:g}"
        vis = ("hidden;" if on_a > 0 else "") + "visible;hidden"
        if on_a == 0:
            vis_kt, vis = f"0;{on_b:g}", "visible;hidden"
        body.append(
            f'<clipPath id="p{i}"><rect x="{x0 - 1:.1f}" y="0" width="0" height="{H}">'
            f'<animate attributeName="width" dur="{T}s" repeatCount="indefinite" calcMode="discrete" keyTimes="{kt}" values="{widths}"/></rect></clipPath>'
            f'<g clip-path="url(#p{i})"><path d="{prompt}" fill="{P["accent"]}"/><path d="{rest}" fill="{P["ink2"]}"/></g>'
            f'<rect x="{x0 + 2:.1f}" y="12" width="{adv * 0.55:.1f}" height="28" fill="{P["orange"]}" visibility="hidden">'
            f'<animate attributeName="x" dur="{T}s" repeatCount="indefinite" calcMode="discrete" keyTimes="{kt}" values="{xs}"/>'
            f'<animate attributeName="visibility" dur="{T}s" repeatCount="indefinite" calcMode="discrete" keyTimes="{vis_kt}" values="{vis}"/>'
            f'<animate attributeName="opacity" dur="0.9s" repeatCount="indefinite" calcMode="discrete" keyTimes="0;0.5" values="1;0"/></rect>')
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="{escape('; '.join(PHRASES), {'"': '&quot;'})}">
<title>{escape(' · '.join(PHRASES))}</title>
{''.join(body)}
</svg>"""
    write(f"typing-{mode}.svg", svg)


# ------------------------------------------------------------------ player card
STATS = [("92", "PYT"), ("90", "DAT"), ("88", "MOD"), ("86", "API"), ("82", "APP"), ("99", "FUN")]


def player_card():
    W, H = 420, 600
    cx = W / 2
    shape = f"M30,70 Q30,26 74,22 L150,16 Q{cx},0 {W - 150},16 L{W - 74},22 Q{W - 30},26 {W - 30},70 L{W - 30},470 Q{W - 30},520 {cx},{H - 20} Q30,520 30,470 Z"
    rating, _ = text(SANS_B, "91", 66, 74, 118)
    pos, _ = text(SANS_M, "ML", 24, 82, 148, spacing=1)
    mono, _ = text(SERIF, "MS", 150, cx + 22, 268, anchor="middle")
    name, _ = text(SANS_B, "SUFIYAN", 40, cx, 352, spacing=2, anchor="middle")
    crest, _ = text(MONO_B, "IT", 15, 102, 205, anchor="middle")
    num, _ = text(SANS_B, "07", 22, 102, 252, anchor="middle")
    foot, _ = text(MONO_B, "INJURY TIME FC  ·  MATCH FIT", 10, cx, 524, spacing=1.2, anchor="middle")
    stats = []
    for i, (v, k) in enumerate(STATS):
        col, row = i // 3, i % 3
        x = 96 if col == 0 else 250
        y = 408 + row * 40
        vp, _ = text(SANS_B, v, 26, x, y)
        kp, _ = text(SANS_M, k, 20, x + 46, y, spacing=1)
        stats.append(f'<g class="stat" style="animation-delay:{0.4 + i * 0.12:.2f}s"><path d="{vp}" fill="#C6FF3D"/><path d="{kp}" fill="#F4F1EA"/></g>')
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="Player card: Sufiyan, rating 91, position ML. Python 92, Data 90, Modelling 88, APIs 86, Apps 82, Fun 99.">
<title>Player card: Sufiyan, 91 ML</title>
<defs>
  <linearGradient id="bd" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#C6FF3D"/><stop offset=".5" stop-color="#7C8CFF"/><stop offset="1" stop-color="#FF6B35"/></linearGradient>
  <linearGradient id="bgc" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#1E2142"/><stop offset="1" stop-color="#0D0E1A"/></linearGradient>
  <radialGradient id="halo" cx=".5" cy=".38" r=".5"><stop offset="0" stop-color="#7C8CFF" stop-opacity=".45"/><stop offset="1" stop-color="#7C8CFF" stop-opacity="0"/></radialGradient>
  <linearGradient id="shine" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".5" stop-color="#fff" stop-opacity=".22"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>
  <clipPath id="cc"><path d="{shape}"/></clipPath>
  <pattern id="hex" width="22" height="38" patternUnits="userSpaceOnUse"><path d="M11,0 L22,6.5 L22,19 L11,25.5 L0,19 L0,6.5Z M11,25.5 L11,38" fill="none" stroke="#7C8CFF" stroke-opacity=".08"/></pattern>
</defs>
<style>
  .float {{ animation: float 6s ease-in-out infinite; }}
  @keyframes float {{ 0%, 100% {{ transform: translateY(0); }} 50% {{ transform: translateY(-6px); }} }}
  .sweep {{ animation: sweep 5s ease-in-out 1s infinite; }}
  @keyframes sweep {{ 0% {{ transform: translateX(-520px) skewX(-20deg); }} 40%, 100% {{ transform: translateX(560px) skewX(-20deg); }} }}
  .stat {{ animation: pop .5s cubic-bezier(.2,1.4,.4,1) both; transform-box: fill-box; transform-origin: center; }}
  @keyframes pop {{ from {{ opacity: 0; transform: scale(.6); }} to {{ opacity: 1; transform: none; }} }}
  {REDUCED}
</style>
<g class="float">
  <path d="{shape}" fill="url(#bgc)" stroke="url(#bd)" stroke-width="7" stroke-linejoin="round"/>
  <g clip-path="url(#cc)">
    <rect width="{W}" height="{H}" fill="url(#hex)"/>
    <circle cx="{cx + 22}" cy="225" r="150" fill="url(#halo)"/>
    <path d="{mono}" fill="#F4F1EA"/>
    <rect class="sweep" x="0" y="-40" width="140" height="{H + 80}" fill="url(#shine)"/>
  </g>
  <path d="{rating}" fill="#C6FF3D"/>
  <path d="{pos}" fill="#F4F1EA"/>
  <circle cx="102" cy="200" r="20" fill="none" stroke="#FF6B35" stroke-width="2.5"/>
  <path d="{crest}" fill="#FF6B35"/>
  <path d="{num}" fill="#A9A8B8"/>
  <line x1="70" y1="370" x2="{W - 70}" y2="370" stroke="url(#bd)" stroke-width="2"/>
  <path d="{name}" fill="#F4F1EA"/>
  <line x1="{cx}" y1="384" x2="{cx}" y2="494" stroke="#2A2D52" stroke-width="2"/>
  {''.join(stats)}
  <path d="{foot}" fill="#A9A8B8"/>
</g>
</svg>"""
    write("player-card.svg", svg)


# ------------------------------------------------------------------ project covers (1280 x 800 webp)
def phones_cover(name, shots, bg1, bg2):
    W, H = 1280, 800
    img = Image.new("RGB", (W, H), bg1)
    glow = Image.new("RGB", (W, H), bg1)
    d = ImageDraw.Draw(glow)
    d.ellipse((W * .55, -200, W * 1.2, H * .7), fill=bg2)
    d.ellipse((-200, H * .45, W * .45, H * 1.4), fill="#2A2D52")
    img = Image.blend(img, glow.filter(ImageFilter.GaussianBlur(120)), 0.9)
    ph_h = 680
    ims = [Image.open(s).convert("RGB") for s in shots]
    ims = [im.resize((int(im.width * ph_h / im.height), ph_h), Image.LANCZOS) for im in ims]
    gap = 46
    total = sum(im.width for im in ims) + gap * (len(ims) - 1)
    x = (W - total) // 2
    for i, im in enumerate(ims):
        y = (H - ph_h) // 2 + (0 if i == len(ims) // 2 else 26)
        r = 34
        mask = Image.new("L", im.size, 0)
        ImageDraw.Draw(mask).rounded_rectangle((0, 0, im.width - 1, im.height - 1), r, fill=255)
        sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(sh).rounded_rectangle((x + 8, y + 18, x + im.width + 8, y + im.height + 18), r, fill=(0, 0, 0, 120))
        img = Image.alpha_composite(img.convert("RGBA"), sh.filter(ImageFilter.GaussianBlur(18))).convert("RGB")
        frame = Image.new("RGB", (im.width + 12, im.height + 12), "#0B0C16")
        fm = Image.new("L", frame.size, 0)
        ImageDraw.Draw(fm).rounded_rectangle((0, 0, frame.width - 1, frame.height - 1), r + 6, fill=255)
        img.paste(frame, (x - 6, y - 6), fm)
        img.paste(im, (x, y), mask)
        x += im.width + gap
    img.save(os.path.join(OUT, name), "WEBP", quality=82, method=6)
    print(f"{name:28s} {os.path.getsize(os.path.join(OUT, name)) // 1024:4d} KB")


def portfolio_cover():
    W, H = 1280, 800
    og = Image.open(os.path.join(SITE, "assets", "brand", "og-image.jpg")).convert("RGB")
    img = Image.new("RGB", (W, H), "#0D0E1A")
    og = og.resize((W, int(og.height * W / og.width)), Image.LANCZOS)
    if og.height < H:
        bgimg = og.resize((int(og.width * H / og.height), H), Image.LANCZOS).filter(ImageFilter.GaussianBlur(40))
        img.paste(bgimg, ((W - bgimg.width) // 2, 0))
        img.paste(og, (0, (H - og.height) // 2))
    else:
        img.paste(og, (0, (H - og.height) // 2))
    img.save(os.path.join(OUT, "cover-portfolio.webp"), "WEBP", quality=84, method=6)
    print(f"{'cover-portfolio.webp':28s} {os.path.getsize(os.path.join(OUT, 'cover-portfolio.webp')) // 1024:4d} KB")


for P, mode in ((DARK, "dark"), (LIGHT, "light")):
    banner(P, mode)
    typing(P, mode)
player_card()
apps = os.path.join(SITE, "assets", "apps")
phones_cover("cover-tapsy.webp", [os.path.join(apps, f) for f in ("tapsy-2-tap-popup.webp", "tapsy-1-wallet.webp", "tapsy-3-card-designer.webp")], "#0D0E1A", "#3B2A7A")
phones_cover("cover-fleet.webp", [os.path.join(apps, f) for f in ("fleet-2-receipt-scan.webp", "fleet-1-live-map.webp", "fleet-3-dashboard.webp")], "#0D0E1A", "#7A3A1F")
portfolio_cover()
shutil.copy(os.path.join(INJ, "docs", "readme", "tour.webp"), os.path.join(OUT, "cover-injury-time.webp"))
print("cover-injury-time.webp copied")
