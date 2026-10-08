"""Hindi (Devanagari) title kit: calligraphic / display Hindi word + small English meaning,
rebuilt with free Google fonts (see fonts/fonts.md). Needs Pillow with raqm (complex shaping).

  python deva_kit.py --style calligraphy_swash --text "भारत|INDIA" --bg photo.jpg --out t.jpg
  python deva_kit.py --sheet --out deva_sheet.jpg
  python deva_kit.py --style latin_shirorekha --text "Mangalmay|A TRIBUTE TO INDIA" --out t.jpg

Effects: swash tail (tapered curve out of the last letter), hairline (thin diagonal stroke through
the word), shirorekha extension (headline bar runs past the word), chalk, grunge, and an English
meaning line in small letter-spaced caps under the word.
"""
import argparse, math, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from title_kit import distress, shadow, text_img as latin_text, W, H

BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'fonts')
DEVA = os.path.join(BASE, 'deva')
CREAM, MAROON, RED, BROWN, WHITE, MAGENTA = (246, 236, 214), (150, 28, 20), (155, 26, 18), (62, 38, 28), (255, 255, 255), (222, 30, 110)


def dtext(s, font, size, color):
    ft = ImageFont.truetype(os.path.join(DEVA, font), int(size), layout_engine=ImageFont.Layout.RAQM)
    b = ft.getbbox(s)
    pad = int(size * 0.6)
    im = Image.new('RGBA', (b[2] - b[0] + 2 * pad, b[3] - b[1] + 2 * pad))
    ImageDraw.Draw(im).text((pad - b[0], pad - b[1]), s, font=ft, fill=color)
    return im.crop(im.getbbox())


def headline(im):
    """Find the shirorekha (top bar): (y0, y1, x0, x1) of the widest ink rows in the top half."""
    a = np.array(im.split()[3]) > 128
    h = a.shape[0]
    rows = a[: int(h * 0.55)].sum(1)
    if rows.max() == 0:
        return None
    y = int(rows.argmax())
    band = np.where(rows > rows.max() * 0.7)[0]
    band = band[(band >= y - 40) & (band <= y + 40)]
    xs = np.where(a[y])[0]
    return int(band.min()), int(band.max()), int(xs.min()), int(xs.max())


def extend_bar(im, left=0, right=0, color=WHITE):
    hb = headline(im)
    if not hb:
        return im
    y0, y1, x0, x1 = hb
    out = Image.new('RGBA', (im.width + left + right, im.height))
    out.alpha_composite(im, (left, 0))
    ImageDraw.Draw(out).rectangle([x0 + left - left, y0, x1 + left + right, y1], fill=color)
    if left:
        ImageDraw.Draw(out).rectangle([0, y0, x0 + left, y1], fill=color)
    return out


def swash(im, color, side='right', reach=0.55, drop=0.45, width=None):
    """Tapered calligraphic tail sweeping out from the bottom of the word (भारत / रंगाम / मोक्ष look)."""
    w0 = width or max(6, im.height // 9)
    ext = int(im.width * reach)
    out = Image.new('RGBA', (im.width + ext, int(im.height * (1 + drop))))
    ox = 0 if side == 'right' else ext
    out.alpha_composite(im, (ox, 0))
    d = ImageDraw.Draw(out)
    if side == 'right':
        p0 = (ox + im.width * 0.62, im.height * 0.92); p1 = (ox + im.width * 0.78, im.height * (1 + drop * 0.9))
        p2 = (ox + im.width * 1.05, im.height * (1 + drop * 0.55)); p3 = (out.width - 4, im.height * 0.98)
    else:
        p0 = (ox + im.width * 0.3, im.height * 0.92); p1 = (ox + im.width * 0.15, im.height * (1 + drop * 0.9))
        p2 = (ox - ext * 0.4, im.height * (1 + drop * 0.6)); p3 = (4, im.height * 0.8)
    n = 120
    pts = []
    for i in range(n + 1):
        t = i / n
        x = (1 - t) ** 3 * p0[0] + 3 * (1 - t) ** 2 * t * p1[0] + 3 * (1 - t) * t ** 2 * p2[0] + t ** 3 * p3[0]
        y = (1 - t) ** 3 * p0[1] + 3 * (1 - t) ** 2 * t * p1[1] + 3 * (1 - t) * t ** 2 * p2[1] + t ** 3 * p3[1]
        pts.append((x, y, w0 * (1 - t) ** 0.8 + 1))
    for (x, y, r) in pts:
        d.ellipse([x - r / 2, y - r / 2, x + r / 2, y + r / 2], fill=color)
    return out


def hairline(im, color, x=0.38, width=3):
    """Thin diagonal stroke through the word, extending past it (नवोन्मेष / अभिनंदन / निशागंध)."""
    pad = im.height // 3
    out = Image.new('RGBA', (im.width + pad, im.height + pad))
    out.alpha_composite(im, (0, 0))
    out2 = Image.new('RGBA', (out.width, out.height + pad)); out2.alpha_composite(out, (0, pad)); out = out2
    x0 = im.width * x
    ImageDraw.Draw(out).line([(x0 - im.height * 0.35, 0), (x0 + im.height * 0.75, out.height - 2)], fill=color, width=width)
    return out


def chalk(im, seed=2):
    """Chalk-on-blackboard texture: rough edges + speckle (कलामयी)."""
    rnd = np.random.default_rng(seed)
    a = np.array(im.split()[3]).astype(np.float32)
    n = rnd.random(a.shape)
    a = a * (0.55 + 0.45 * (n > 0.35))
    sh = np.roll(a, rnd.integers(-2, 3), 1) * 0.5
    a = np.clip(np.maximum(a, sh) * (rnd.random(a.shape) > 0.08), 0, 255)
    im.putalpha(Image.fromarray(a.astype(np.uint8)))
    return im


def kicker(s, color, size=42, spacing=3, maxw=900):
    k = latin_text(s.upper(), 'montserrat-500.ttf', size, color, spacing)
    return k if k.width <= maxw else k.resize((maxw, int(k.height * maxw / k.width)), Image.LANCZOS)


# hero = (font, size, color); fx = list of effects; bg = background colour for the preview sheet
STYLES = {
    'grunge_danger': dict(desc='Torn grunge Hindi, white (संकटभाव)', sample=['संकटभाव', 'Feeling of danger'], hero=('yatra-one-devanagari-400.ttf', 230, WHITE), fx=['grunge'], bg=(20, 70, 40)),
    'chalk': dict(desc='Chalk handwriting on black (कलामयी)', sample=['कलामयी', 'Artistic'], hero=('kalam-devanagari-700.ttf', 250, (235, 235, 235)), fx=['chalk'], bg=(15, 15, 15)),
    'heavy_calligraphy': dict(desc='Very heavy calligraphic, white on photo (मृदुल / जीत)', sample=['मृदुल', 'Pure'], hero=('eczar-devanagari-800.ttf', 300, WHITE), fx=[], bg=(230, 110, 40)),
    'rounded_mono': dict(desc='Rounded monoline, friendly (परिवर्तन / सृजन)', sample=['परिवर्तन', 'Transformation'], hero=('baloo-2-devanagari-600.ttf', 250, WHITE), fx=[], bg=(240, 150, 40)),
    'sharp_hairline': dict(desc='Sharp display + diagonal hairlines, magenta (नवोन्मेष)', sample=['नवोन्मेष', 'Innovation'], hero=('eczar-devanagari-800.ttf', 250, MAGENTA), fx=['hairline'], bg=(12, 10, 16)),
    'thin_geometric_swash': dict(desc='Thin geometric line + long left swash (गुलज़ार)', sample=['गुलज़ार', 'Blooming'], hero=('poppins-devanagari-300.ttf', 260, WHITE), fx=['bar', 'swash_left'], bg=(220, 110, 40)),
    'calligraphy_swash': dict(desc='Bold calligraphy with a long tail (भारत / रंगाम)', sample=['भारत', 'India'], hero=('rozha-one-devanagari-400.ttf', 290, RED), fx=['swash'], bg=CREAM),
    'bold_hairline': dict(desc='Heavy calligraphy + hairline stroke, cream on red (अभिनंदन / विरासत)', sample=['अभिनंदन', 'Congratulations'], hero=('rozha-one-devanagari-400.ttf', 250, CREAM), fx=['hairline'], bg=RED),
    'mono_bar': dict(desc='Thin monoline with extended headline bar, cream on red (उत्तराखंड)', sample=['उत्तराखंड', 'Uttarakhand'], hero=('gotu-devanagari-400.ttf', 220, CREAM), fx=['bar'], bg=RED),
    'rounded_swash': dict(desc='Rounded thick monoline with tail (शब्दमाला)', sample=['शब्दमाला', 'Garland of words'], hero=('baloo-2-devanagari-600.ttf', 230, CREAM), fx=['swash_left', 'bar'], bg=RED),
    'flowing_calligraphy': dict(desc='Flowing pen calligraphy + swash (मोक्षप्राप्ती / अदाएँ / श्रृंगार / नज़ाकत)', sample=['श्रृंगार', 'Adornment'], hero=('amita-devanagari-700.ttf', 260, BROWN), fx=['swash'], bg=(222, 205, 170)),
    'flowing_light': dict(desc='Lighter pen calligraphy (अदाकारी)', sample=['अदाकारी', 'Acting'], hero=('amita-devanagari-400.ttf', 260, MAROON), fx=['bar'], bg=CREAM),
    'textured_heavy': dict(desc='Heavy serif Hindi with inner texture + ornaments (हिन्दी)', sample=['हिन्दी', 'Hindi'], hero=('eczar-devanagari-800.ttf', 300, (120, 30, 22)), fx=['grain', 'ornaments'], bg=(240, 226, 205)),
    'jain_script': dict(desc='Old manuscript style (Jaini Purva)', sample=['विरासत', 'Heritage'], hero=('jaini-purva-devanagari-400.ttf', 280, BROWN), fx=[], bg=(222, 205, 170)),
    'latin_shirorekha': dict(desc='English word dressed like Hindi: headline bar + swash (Mangalmay / Qasira / Chintaron)', sample=['mangalmay', 'A calligraphic tribute to India'], hero=('akshar-latin-700.ttf', 200, (25, 25, 25)), fx=['latin_bar', 'swash'], bg=(236, 232, 222)),
    'signature_outro': dict(desc='Signature script + wide spaced caps + handle (outro: Tha / IF YOU ENJOY MY CONTENT)', sample=['Thank you', 'If you enjoy my content:'], hero=None, fx=['signature'], bg=(228, 226, 222)),
}


def render(style, texts=None, w=W, h=H, y=560):
    st = STYLES[style]
    texts = texts or st['sample']
    out = Image.new('RGBA', (W, H))
    if 'signature' in st['fx']:
        sig = latin_text(texts[0], 'mrs-saint-delafield-400.ttf', 220, (20, 20, 20))
        out.alpha_composite(sig, (W // 2 - sig.width // 2 - 120, y - sig.height // 2))
        k = kicker(texts[1], (20, 20, 20), 34, 8, 860)
        out.alpha_composite(k, (W // 2 - k.width // 2, y + 330))
        return out.resize((w, h)) if (w, h) != (W, H) else out
    font, size, color = st['hero']
    im = dtext(texts[0], font, size, color)
    if 'latin_bar' in st['fx']:
        a = np.array(im.split()[3]) > 128
        rows = a.sum(1); xh = int(np.where(rows > rows.max() * 0.35)[0].min())   # top of x-height
        bar = max(10, size // 12)
        im2 = Image.new('RGBA', (im.width + 60, im.height + bar)); im2.alpha_composite(im, (30, bar))
        ImageDraw.Draw(im2).rectangle([0, xh, im2.width, xh + bar], fill=color); im = im2
    if 'bar' in st['fx']:
        im = extend_bar(im, left=int(size * 0.1), right=int(size * 0.25), color=color)
    if 'grunge' in st['fx']:
        im = distress(im, 0.5, 3)
    if 'chalk' in st['fx']:
        im = chalk(im)
    if 'grain' in st['fx']:
        a = np.array(im).astype(np.float32); n = np.random.default_rng(1).normal(1, 0.18, a.shape[:2])
        a[..., :3] = np.clip(a[..., :3] * n[..., None], 0, 255); im = Image.fromarray(a.astype(np.uint8))
    if 'hairline' in st['fx']:
        im = hairline(im, color)
    if 'swash' in st['fx']:
        im = swash(im, color, 'right')
    if 'swash_left' in st['fx']:
        im = swash(im, color, 'left', reach=0.35, drop=0.35)
    if im.width > 980:
        im = im.resize((980, int(im.height * 980 / im.width)), Image.LANCZOS)
    if color == WHITE:
        im = shadow(im, (0, 6), 12, 0.35)
    out.alpha_composite(im, (W // 2 - im.width // 2, y - im.height // 2))
    if 'ornaments' in st['fx']:
        d = ImageDraw.Draw(out)
        for cx in (W // 2 - im.width // 2 - 40, W // 2 + im.width // 2 + 40):
            for a in range(0, 360, 90):
                r = math.radians(a); d.ellipse([cx + 22 * math.cos(r) - 10, y + 22 * math.sin(r) - 10, cx + 22 * math.cos(r) + 10, y + 22 * math.sin(r) + 10], fill=color)
    if len(texts) > 1 and texts[1]:
        kc = color if color != WHITE else WHITE
        k = kicker(texts[1], kc)
        out.alpha_composite(k, (W // 2 - k.width // 2, y + im.height // 2 + 70))
    return out.resize((w, h)) if (w, h) != (W, H) else out


def sheet(out, cols=4):
    names = list(STYLES)
    tw, th = 450, 560
    rows = math.ceil(len(names) / cols)
    S = Image.new('RGB', (cols * tw, rows * (th + 46)), (15, 15, 18))
    d = ImageDraw.Draw(S); lab = ImageFont.truetype(os.path.join(BASE, 'montserrat-700.ttf'), 22)
    for i, n in enumerate(names):
        bg = Image.new('RGBA', (W, H), STYLES[n]['bg'] + (255,))
        bg.alpha_composite(render(n))
        tile = bg.convert('RGB').crop((0, 160, W, 160 + int(W * th / tw))).resize((tw, th), Image.LANCZOS)
        S.paste(tile, ((i % cols) * tw, (i // cols) * (th + 46)))
        d.text(((i % cols) * tw + 10, (i // cols) * (th + 46) + th + 10), n, font=lab, fill=(230, 230, 230))
    S.save(out, quality=92)


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--style', choices=list(STYLES)); p.add_argument('--text', help="'हिंदी शब्द|ENGLISH MEANING'")
    p.add_argument('--bg'); p.add_argument('--png', action='store_true'); p.add_argument('--sheet', action='store_true')
    p.add_argument('--out', required=True)
    a = p.parse_args()
    if a.sheet:
        sheet(a.out)
    else:
        from title_kit import on_bg
        ov = render(a.style, a.text.split('|') if a.text else None)
        if a.png:
            ov.save(a.out)
        elif a.bg:
            on_bg(ov, a.bg, top_dark=False).save(a.out)
        else:
            b = Image.new('RGBA', (W, H), STYLES[a.style]['bg'] + (255,)); b.alpha_composite(ov); b.convert('RGB').save(a.out)
    print('saved', a.out)
