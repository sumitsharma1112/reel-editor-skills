"""Travel / cinematic title kit: 20 hand-lettering title styles for reels and covers,
rebuilt with free Google fonts (see fonts.md for the mapping and install).

Each style is a list of layers. A layer = one line of text with its own font, size, colour,
position and effects. Text is passed per style, so the same look works for any place name.

  python title_kit.py --style brush_grunge --text "KUM|BHE" --bg photo.jpg --out title.png
  python title_kit.py --sheet --out styles_sheet.jpg          # preview of all styles
  # in code:  from title_kit import render;  overlay = render('script_kicker', ['Dhanushkodi', 'The last land'])

Overlay is a transparent 1080x1920 RGBA PIL image. Text sits in the top third (safe zone).
"""
import argparse, math, os, random
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops

FONT_DIR = os.environ.get('REEL_FONTS', os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'fonts'))
W, H = 1080, 1920
WHITE, CREAM, YELLOW, SOFTYEL, SKY, CHAR = (255, 255, 255), (246, 236, 200), (255, 214, 74), (249, 239, 160), (143, 211, 244), (70, 74, 74)


def F(name, size):
    return ImageFont.truetype(os.path.join(FONT_DIR, name), int(size))


# ---------- effects ----------
def distress(im, amount=0.35, seed=1, streaks=False):
    """Grunge: speckle holes + cracks cut out of the alpha (KUMBHE / Maharashtra / Spitiful look)."""
    rnd = np.random.default_rng(seed)
    a = np.array(im.split()[3]).astype(np.float32)
    h, w = a.shape
    n = rnd.random((h // 3 + 1, w // 3 + 1))
    n = np.kron(n, np.ones((3, 3)))[:h, :w]
    holes = n < amount * 0.25
    m = Image.new('L', (w, h), 255)
    d = ImageDraw.Draw(m)
    for _ in range(int(25 * amount * (w * h) / 4e5) + 3):   # cracks
        x, y = rnd.integers(0, w), rnd.integers(0, h)
        L, ang = rnd.integers(20, 140), rnd.uniform(0, math.pi)
        d.line([(x, y), (x + L * math.cos(ang), y + L * math.sin(ang))], fill=0, width=int(rnd.integers(1, 3)))
    if streaks:                                             # dry-brush horizontal streaks (Langza)
        for _ in range(int(h / 6)):
            y = rnd.integers(0, h); x = rnd.integers(0, w)
            d.line([(x, y), (x + rnd.integers(40, 260), y + rnd.integers(-4, 4))], fill=0, width=2)
    a = a * (np.array(m) / 255.0) * (~holes)
    im.putalpha(Image.fromarray(a.astype(np.uint8)))
    return im


def shadow(im, off=(0, 8), blur=14, alpha=0.45, color=(0, 0, 0)):
    sh = Image.new('RGBA', im.size, color + (0,))
    sh.putalpha(im.split()[3].point(lambda v: int(v * alpha)))
    sh = sh.filter(ImageFilter.GaussianBlur(blur))
    out = Image.new('RGBA', (im.width + abs(off[0]) + 4 * blur, im.height + abs(off[1]) + 4 * blur))
    ox, oy = 2 * blur, 2 * blur
    out.alpha_composite(sh, (ox + off[0], oy + off[1])); out.alpha_composite(im, (ox, oy))
    return out


def hard_shadow(im, off=(10, 10), color=(0, 0, 0)):
    """Offset solid shadow (yellow MODES look)."""
    sh = Image.new('RGBA', im.size, color + (0,)); sh.putalpha(im.split()[3])
    out = Image.new('RGBA', (im.width + off[0], im.height + off[1]))
    out.alpha_composite(sh, off); out.alpha_composite(im, (0, 0))
    return out


def text_img(s, font, size, color, spacing=0, stroke=0):
    ft = F(font, size)
    if spacing:                                          # letter-spaced caps (JODHPUR / MOUNTAIN)
        chars = [text_img(c, font, size, color, 0, stroke) for c in s]
        wsum = sum(c.width for c in chars) + spacing * (len(s) - 1)
        hmax = max(c.height for c in chars)
        im = Image.new('RGBA', (wsum, hmax)); x = 0
        for c in chars:
            im.alpha_composite(c, (x, hmax - c.height)); x += c.width + spacing
        return im
    b = ft.getbbox(s, stroke_width=stroke)
    im = Image.new('RGBA', (b[2] - b[0] + 20, b[3] - b[1] + 20))
    ImageDraw.Draw(im).text((10 - b[0], 10 - b[1]), s, font=ft, fill=color, stroke_width=stroke, stroke_fill=color)
    return im


def fit_w(im, maxw):
    if im.width > maxw:
        im = im.resize((maxw, int(im.height * maxw / im.width)), Image.LANCZOS)
    return im


# ---------- styles ----------
# layer keys: t (text index), font, size, color, x, y (centre, px on 1080x1920), maxw, rot, spacing,
#             distress, streaks, shadow, hard, stroke
STYLES = {
    'brush_grunge': dict(desc='Dry-brush caps, grunge cracks, stacked (KUMBHE)', sample=['KUM', 'BHE'], layers=[
        dict(t=0, font='permanent-marker-400.ttf', size=330, color=WHITE, x=540, y=420, rot=4, distress=0.45, shadow=1),
        dict(t=1, font='permanent-marker-400.ttf', size=330, color=WHITE, x=560, y=700, rot=4, distress=0.45, shadow=1)]),
    'marker_stack': dict(desc='Rounded marker hand-lettering, 2 lines (Wild Walker)', sample=['Wild', 'Walker'], layers=[
        dict(t=0, font='caveat-brush-400.ttf', size=300, color=WHITE, x=600, y=430, rot=-4),
        dict(t=1, font='caveat-brush-400.ttf', size=300, color=WHITE, x=500, y=660, rot=-4)]),
    'swash_serif': dict(desc='Victorian swash serif + small sans note (Typography on story)', sample=['Typography', 'On story'], light=1, layers=[
        dict(t=0, font='berkshire-swash-400.ttf', size=190, color=WHITE, x=540, y=420, maxw=1000, shadow=1),
        dict(t=1, font='montserrat-500.ttf', size=58, color=(20, 20, 20), x=760, y=560)]),
    'bold_script': dict(desc='Bold brush script, 2 stacked lines (Spirit Birds / Kerala Tales)', sample=['Spirit', 'Birds'], layers=[
        dict(t=0, font='kaushan-script-400.ttf', size=250, color=WHITE, x=540, y=420, rot=-6),
        dict(t=1, font='kaushan-script-400.ttf', size=250, color=WHITE, x=600, y=650, rot=-6)]),
    'circle_badge': dict(desc='Dry brush script inside a hand-drawn circle (Discover Tamil Nadu)', sample=['Discover', 'Tamil', 'nadu'], circle=(540, 560, 380), layers=[
        dict(t=0, font='mr-dafoe-400.ttf', size=170, color=WHITE, x=540, y=330, rot=-6, distress=0.2),
        dict(t=1, font='mr-dafoe-400.ttf', size=300, color=WHITE, x=540, y=540, rot=-6, distress=0.2),
        dict(t=2, font='mr-dafoe-400.ttf', size=300, color=WHITE, x=560, y=740, rot=-6, distress=0.2)]),
    'casual_script': dict(desc='Heavy casual script (Kerala Tales)', sample=['Kerala', 'Tales'], layers=[
        dict(t=0, font='leckerli-one-400.ttf', size=260, color=WHITE, x=540, y=430, rot=-5),
        dict(t=1, font='leckerli-one-400.ttf', size=230, color=WHITE, x=600, y=660, rot=-5)]),
    'distressed_script': dict(desc='Elegant script with scratched texture (Spitiful)', sample=['Spitiful'], layers=[
        dict(t=0, font='parisienne-400.ttf', size=260, color=WHITE, x=540, y=520, maxw=1000, distress=0.35)]),
    'stacked_story': dict(desc='Bouncy script stacked word-by-word with soft depth (The Himachal Stories)', sample=['the', 'Hima', 'chal', 'Stories'], layers=[
        dict(t=0, font='dancing-script-700.ttf', size=170, color=WHITE, x=640, y=300, shadow=1),
        dict(t=1, font='dancing-script-700.ttf', size=300, color=WHITE, x=520, y=470, shadow=1),
        dict(t=2, font='dancing-script-700.ttf', size=300, color=WHITE, x=580, y=670, shadow=1),
        dict(t=3, font='dancing-script-700.ttf', size=200, color=WHITE, x=560, y=860, shadow=1)]),
    'western_grunge': dict(desc='Retro western caps, distressed, small kicker (Finding Maharashtra)', sample=['FINDING', 'MAHA', 'RASHTRA'], layers=[
        dict(t=0, font='rye-400.ttf', size=90, color=WHITE, x=540, y=330, distress=0.3),
        dict(t=1, font='rye-400.ttf', size=230, color=WHITE, x=540, y=500, distress=0.45),
        dict(t=2, font='rye-400.ttf', size=230, color=WHITE, x=540, y=720, maxw=1000, distress=0.45)]),
    'classic_caps': dict(desc='Classic Roman serif caps + soft shadow, placed behind subject (LADAKH)', sample=['LADAKH'], layers=[
        dict(t=0, font='cinzel-900.ttf', size=230, color=WHITE, x=540, y=480, maxw=960, shadow=1)]),
    'fast_brush': dict(desc='Fast dry-brush script with streaks (Langza)', sample=['Langza'], layers=[
        dict(t=0, font='mr-dafoe-400.ttf', size=340, color=WHITE, x=540, y=500, maxw=1000, rot=-3, distress=0.15, streaks=1)]),
    'swash_plus_tiny_script': dict(desc='Swash serif + tiny signature script tucked at the first letter (Effects Typography)', sample=['Typography', 'Effects'], layers=[
        dict(t=0, font='berkshire-swash-400.ttf', size=190, color=WHITE, x=560, y=460, maxw=980, shadow=1),
        dict(t=1, font='mrs-saint-delafield-400.ttf', size=130, color=WHITE, x=200, y=340)]),
    'kicker_serif': dict(desc='Soft heavy display serif in pastel yellow + small caps kicker inside it (Take better Framing)', sample=['Framing', 'TAKE BETTER'], layers=[
        dict(t=0, font='abril-fatface-400.ttf', size=260, color=SOFTYEL, x=550, y=470, maxw=960),
        dict(t=1, font='cinzel-700.ttf', size=40, color=WHITE, x=610, y=392, spacing=5)]),
    'brush_caps_badge': dict(desc='Rough brush caps + spaced sans subtitle + mountain icon line (GOD\'S MOUNTAIN)', sample=["GOD'S", 'MOUNTAIN'], icon=(540, 690), light=1, layers=[
        dict(t=0, font='permanent-marker-400.ttf', size=230, color=CHAR, x=540, y=430, maxw=900, distress=0.2),
        dict(t=1, font='montserrat-700.ttf', size=62, color=CHAR, x=540, y=600, spacing=22)]),
    'script_over_block': dict(desc='Thin script kicker + giant yellow condensed caps with hard black shadow (Gimbel MODES)', sample=['Gimbel', 'MODES'], doodles=1, layers=[
        dict(t=1, font='anton-400.ttf', size=330, color=(255, 238, 60), x=540, y=560, maxw=900, hard=1),
        dict(t=0, font='sacramento-400.ttf', size=170, color=WHITE, x=560, y=330, stroke=1)]),
    'bubbly_fun': dict(desc='Bubbly rounded hand font with sparkle strokes (Life is a Highway)', sample=['Life is a', 'Highway'], sparkle=1, layers=[
        dict(t=0, font='chewy-400.ttf', size=170, color=WHITE, x=540, y=430, rot=-4),
        dict(t=1, font='chewy-400.ttf', size=200, color=WHITE, x=540, y=600, rot=-4)]),
    'caps_signature': dict(desc='Bold sans caps in yellow + thin signature script crossing it (Hemkund Sahib Gurudwara)', sample=['HEMKUND SAHIB', 'Gurudwara'], layers=[
        dict(t=0, font='montserrat-900.ttf', size=120, color=YELLOW, x=560, y=420, maxw=900),
        dict(t=1, font='mrs-saint-delafield-400.ttf', size=170, color=WHITE, x=740, y=520)]),
    'calligraphy_kicker': dict(desc='Cream calligraphic script + tiny sans kicker inside its loop (Dhanushkodi The last land)', sample=['Dhanushkodi', 'The last land'], layers=[
        dict(t=0, font='great-vibes-400.ttf', size=230, color=CREAM, x=540, y=470, maxw=1000, stroke=2),
        dict(t=1, font='montserrat-500.ttf', size=40, color=WHITE, x=470, y=405)]),
    'spaced_caps_signature': dict(desc='Wide letter-spaced bold caps in scene colour + signature script overlap (JODHPUR Blue City)', sample=['JODHPUR', 'Blue City'], layers=[
        dict(t=0, font='montserrat-900.ttf', size=130, color=SKY, x=540, y=430, maxw=1000, spacing=34),
        dict(t=1, font='mrs-saint-delafield-400.ttf', size=170, color=WHITE, x=700, y=530)]),
    'script_word_kicker': dict(desc='Yellow handwritten script + small clean sans kicker, above subject (Cinematic Adiyogi)', sample=['Adiyogi', 'Cinematic'], layers=[
        dict(t=0, font='ruthie-400.ttf', size=330, color=(250, 215, 70), x=540, y=520, maxw=900, stroke=1),
        dict(t=1, font='montserrat-500.ttf', size=56, color=WHITE, x=640, y=345, shadow=1)]),
}


def _circle(d, cx, cy, r):
    for a0, a1 in [(200, 330), (345, 520)]:
        d.arc([cx - r, cy - r * 0.95, cx + r, cy + r * 0.95], a0, a1, fill=WHITE, width=9)


def _icon(d, x, y):
    d.line([(x - 260, y), (x - 70, y)], fill=CHAR, width=4); d.line([(x + 70, y), (x + 260, y)], fill=CHAR, width=4)
    d.polygon([(x - 70, y + 6), (x - 25, y - 45), (x, y - 15), (x + 25, y - 60), (x + 70, y + 6)], fill=CHAR)


def _sparkle(d, x0, x1, y):
    for x, s in [(x0, -1), (x1, 1)]:
        for k, ang in enumerate([-35, 0, 35]):
            a = math.radians(ang + (180 if s < 0 else 0))
            d.line([(x + 30 * math.cos(a), y + 30 * math.sin(a)), (x + 80 * math.cos(a), y + 80 * math.sin(a))], fill=WHITE, width=12)


def _doodles(d):
    d.arc([-200, -260, 360, 220], 10, 80, fill=(255, 238, 60), width=8)
    for k in range(12):
        a = k * math.pi / 6
        d.line([(900 + 45 * math.cos(a), 1050 + 45 * math.sin(a)), (900 + 75 * math.cos(a), 1050 + 75 * math.sin(a))], fill=(255, 238, 60), width=8)


def render(style, texts=None, w=W, h=H, seed=1):
    st = STYLES[style]
    texts = texts or st['sample']
    sx = w / W
    out = Image.new('RGBA', (w, h))
    d = ImageDraw.Draw(out)
    if 'circle' in st: _circle(d, *[v * sx for v in st['circle']])
    if 'icon' in st: _icon(d, st['icon'][0] * sx, st['icon'][1] * sx)
    if st.get('doodles'): _doodles(d)
    for i, L in enumerate(st['layers']):
        if L['t'] >= len(texts): continue
        im = text_img(texts[L['t']], L['font'], L['size'] * sx, L['color'], int(L.get('spacing', 0) * sx), L.get('stroke', 0))
        im = fit_w(im, int(L.get('maxw', 1000) * sx))
        if L.get('distress'): im = distress(im, L['distress'], seed + i, L.get('streaks'))
        if L.get('rot'): im = im.rotate(L['rot'], expand=True, resample=Image.BICUBIC)
        if L.get('hard'): im = hard_shadow(im, (int(12 * sx), int(12 * sx)))
        if L.get('shadow'): im = shadow(im)
        out.alpha_composite(im, (int(L['x'] * sx - im.width / 2), int(L['y'] * sx - im.height / 2)))
    if st.get('sparkle'):
        _sparkle(ImageDraw.Draw(out), 120 * sx, 960 * sx, 400 * sx)
    return out


def on_bg(overlay, bg=None, top_dark=True):
    """Composite over a photo (cover-fit) or a moody gradient; darken the top for readability."""
    if bg:
        b = Image.open(bg).convert('RGB'); s = max(W / b.width, H / b.height)
        b = b.resize((int(b.width * s), int(b.height * s))); b = b.crop(((b.width - W) // 2, (b.height - H) // 2, (b.width - W) // 2 + W, (b.height - H) // 2 + H))
    else:
        y = np.linspace(0, 1, H)[:, None, None]
        b = Image.fromarray((np.array([30, 40, 60]) * (1 - y) + np.array([90, 110, 90]) * y).repeat(W, 1).astype(np.uint8))
    b = b.convert('RGBA')
    if top_dark:
        g = Image.new('RGBA', (W, H)); a = (np.clip(1 - np.linspace(0, 1, H) / 0.55, 0, 1) * 120).astype(np.uint8)
        g.putalpha(Image.fromarray(np.repeat(a[:, None], W, 1))); b.alpha_composite(g)
    b.alpha_composite(overlay.resize(b.size))
    return b.convert('RGB')


def sheet(out, cols=5):
    names = list(STYLES)
    tw, th = 360, 640
    rows = math.ceil(len(names) / cols)
    S = Image.new('RGB', (cols * tw, rows * (th + 50)), (15, 15, 18))
    d = ImageDraw.Draw(S); lab = F('montserrat-700.ttf', 22)
    rng = random.Random(3)
    for i, n in enumerate(names):
        hue = np.array([rng.randint(20, 90), rng.randint(40, 110), rng.randint(50, 120)])
        if STYLES[n].get('light'): hue = np.array([215, 215, 210])
        y = np.linspace(0, 1, H)[:, None, None]
        bg = Image.fromarray((hue * (1 - y) + hue[::-1] * 0.6 * y).repeat(W, 1).astype(np.uint8)).convert('RGBA')
        bg.alpha_composite(render(n))
        S.paste(bg.convert('RGB').resize((tw, th), Image.LANCZOS).crop((0, 0, tw, th)), ((i % cols) * tw, (i // cols) * (th + 50)))
        d.text(((i % cols) * tw + 10, (i // cols) * (th + 50) + th + 12), n, font=lab, fill=(230, 230, 230))
    S.save(out, quality=92)


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--style', choices=list(STYLES))
    p.add_argument('--text', help="lines separated by |, e.g. 'Kerala|Tales'")
    p.add_argument('--bg'); p.add_argument('--png', action='store_true', help='save transparent overlay only')
    p.add_argument('--sheet', action='store_true'); p.add_argument('--out', required=True)
    a = p.parse_args()
    if a.sheet:
        sheet(a.out)
    else:
        ov = render(a.style, a.text.split('|') if a.text else None)
        (ov if a.png else on_bg(ov, a.bg)).save(a.out)
    print('saved', a.out)
