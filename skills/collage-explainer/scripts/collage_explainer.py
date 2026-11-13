#!/usr/bin/env python3
"""Collage explainer: a faceless talking-avatar reel in the "paper collage + app windows" style.

Top ~60% of the frame: a collage scene (cloud sky, torn-paper hills, gingham, spotlight) with
numbered chapter cards, app windows that type, notification rows, a departure board, a film strip,
stickers and a little pixel mascot. Bottom: your cartoon avatar (pose per scene), bobbing while
the voice plays. Captions: 1-2 words at a time in white italic serif, synced to Whisper word times.

  python3 collage_explainer.py plan.json out.mp4

plan.json keys:
  voice (wav), words (whisper json, optional), avatar_dir, fps, captions [[t0,t1,"text"],...],
  scenes [{t0, t1, bg, pose, items:[{type, t, ...}]}]
Item types: chapter, window, notifs, prompt, board, filmstrip, stencil, pill, sticker, phone, poster.
Made with Claude for @aitricksbysumit (style learned from a reel by @vibha.in.progress; own code).
"""
import json, math, os, random, subprocess, sys
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H = 1080, 1920
HERE = os.path.dirname(os.path.abspath(__file__))
FD = os.environ.get('COLLAGE_FONTS', os.path.join(HERE, '..', 'fonts'))
F = {'serif_i': 'PlayfairDisplay-Italic.ttf', 'serif': 'PlayfairDisplay.ttf', 'sans': 'Montserrat.ttf', 'heavy': 'ArchivoBlack-Regular.ttf',
     'stencil': 'Anton-Regular.ttf', 'mono': 'SpaceMono-Bold.ttf', 'marker': 'PermanentMarker-Regular.ttf', 'inter': 'Inter.ttf'}
_fc = {}


def font(k, s):
    key = (k, int(s))
    if key not in _fc: _fc[key] = ImageFont.truetype(os.path.join(FD, F[k]), int(s))
    return _fc[key]


def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def ease_out(u): u = clamp(u); return 1 - (1 - u) ** 3
def ease_io(u): u = clamp(u); return u * u * (3 - 2 * u)
def back_out(u):
    u = clamp(u); c1 = 1.70158; c3 = c1 + 1; return 1 + c3 * (u - 1) ** 3 + c1 * (u - 1) ** 2


def rr(w, h, r, fill, outline=None, width=0):
    im = Image.new('RGBA', (int(w), int(h)), (0, 0, 0, 0))
    ImageDraw.Draw(im).rounded_rectangle([0, 0, int(w) - 1, int(h) - 1], int(r), fill=fill, outline=outline, width=width)
    return im


def shadow(im, blur=16, off=(0, 14), a=110):
    pad = blur * 3
    out = Image.new('RGBA', (im.width + pad * 2, im.height + pad * 2), (0, 0, 0, 0))
    sh = Image.new('RGBA', im.size, (20, 10, 30, 255)); sh.putalpha(im.getchannel('A').point(lambda v: v * a // 255))
    out.alpha_composite(sh, (pad + off[0], pad + off[1])); out = out.filter(ImageFilter.GaussianBlur(blur))
    out.alpha_composite(im, (pad, pad)); return out


def place(base, im, cx, cy, s=1.0, rot=0.0, a=1.0):
    if s <= 0.01 or a <= 0.01: return
    if s != 1: im = im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))), Image.BICUBIC)
    if rot: im = im.rotate(rot, Image.BICUBIC, expand=True)
    if a < 1: im = im.copy(); im.putalpha(im.getchannel('A').point(lambda v: int(v * a)))
    base.alpha_composite(im, (int(cx - im.width / 2), int(cy - im.height / 2))) if (cx - im.width / 2 >= 0 and cy - im.height / 2 >= 0 and cx + im.width / 2 <= W and cy + im.height / 2 <= H) else _paste_clip(base, im, int(cx - im.width / 2), int(cy - im.height / 2))


def _paste_clip(base, im, x, y):
    x0, y0, x1, y1 = max(0, x), max(0, y), min(W, x + im.width), min(H, y + im.height)
    if x1 <= x0 or y1 <= y0: return
    base.alpha_composite(im.crop((x0 - x, y0 - y, x1 - x, y1 - y)), (x0, y0))


def text(s, k, size, col=(255, 255, 255), stroke=0, scol=(0, 0, 0)):
    f = font(k, size); bb = f.getbbox(s, stroke_width=stroke)
    im = Image.new('RGBA', (bb[2] - bb[0] + 8, bb[3] - bb[1] + 8), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((4 - bb[0], 4 - bb[1]), s, font=f, fill=col + (255,) if len(col) == 3 else col, stroke_width=stroke, stroke_fill=scol)
    return im


def wrap(s, k, size, maxw):
    f = font(k, size); out = []; cur = ''
    for w in s.split():
        t = (cur + ' ' + w).strip()
        if f.getlength(t) > maxw and cur: out.append(cur); cur = w
        else: cur = t
    out.append(cur); return out


# ---------------- backgrounds (procedural, cached) -----------------
_bg = {}


def paper_tex(h, w, seed=1, amt=10):
    r = np.random.default_rng(seed).normal(0, 1, (h // 4, w // 4)).astype(np.float32)
    return cv2.resize(cv2.GaussianBlur(r, (0, 0), 1.2), (w, h))[..., None] * amt


def bg_sky():
    if 'sky' in _bg: return _bg['sky']
    y = np.linspace(0, 1, H)[:, None, None]
    a = np.float32([96, 165, 235]) * (1 - y) + np.float32([196, 226, 250]) * y
    a = a * np.ones((1, W, 1), np.float32)
    lay = np.zeros((H, W), np.float32); rng = np.random.default_rng(3)
    for _ in range(26):
        cx, cy = rng.uniform(-100, W + 100), rng.uniform(80, H * 0.75); s = rng.uniform(60, 170)
        for k in range(7):
            cv2.ellipse(lay, (int(cx + rng.uniform(-1.6, 1.6) * s), int(cy + rng.uniform(-0.4, 0.3) * s)), (int(s * rng.uniform(0.6, 1.1)), int(s * rng.uniform(0.45, 0.7))), 0, 0, 360, 1.0, -1)
    lay = cv2.GaussianBlur(lay, (0, 0), 18); lay = np.clip(lay * 1.4, 0, 1)[..., None]
    a = a * (1 - lay) + np.float32([252, 252, 255]) * lay - lay * (np.linspace(0, 1, H)[:, None, None] * 0)
    _bg['sky'] = np.clip(a + paper_tex(H, W, 2, 3), 0, 255).astype(np.uint8); return _bg['sky']


def bg_paper_hills(dusk=False):
    k = 'hills' + str(dusk)
    if k in _bg: return _bg[k]
    top = np.float32([242, 214, 170] if dusk else [226, 230, 236]); bot = np.float32([214, 146, 120] if dusk else [210, 222, 232])
    y = np.linspace(0, 1, H)[:, None, None]; a = (top * (1 - y) + bot * y) * np.ones((1, W, 1), np.float32)
    im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).convert('RGBA'); d = ImageDraw.Draw(im)
    d.ellipse([W * 0.08, H * 0.16, W * 0.3, H * 0.28], fill=(240, 196, 70, 255) if not dusk else (238, 120, 70, 255))
    rng = random.Random(5)
    for cy, sc in ((H * 0.12, 1.0), (H * 0.22, 0.8)):  # paper clouds
        for i in range(3):
            x0 = rng.uniform(0.35, 0.85) * W; w = rng.uniform(160, 260) * sc
            for j in range(4): d.ellipse([x0 + j * w * 0.22 - w * 0.3, cy - w * 0.12 - (j % 2) * 18, x0 + j * w * 0.22 + w * 0.1, cy + w * 0.08], fill=(250, 250, 248, 255))
    cols = [(150, 176, 110), (112, 150, 84), (86, 124, 70), (60, 98, 56)]
    for i, col in enumerate(cols):
        base = H * (0.38 + i * 0.07); pts = [(0, H)]
        for x in range(0, W + 40, 40):
            pts.append((x, base + 60 * math.sin(x / (180 + i * 40) + i * 1.7) + rng.uniform(-6, 6)))
        pts.append((W, H)); d.polygon(pts, fill=col + (255,))
        d.line(pts[1:-1], fill=(250, 248, 240, 255), width=4)  # torn paper edge
    a = np.asarray(im.convert('RGB')).astype(np.float32) + paper_tex(H, W, 7, 6)
    _bg[k] = np.clip(a, 0, 255).astype(np.uint8); return _bg[k]


def bg_gingham(col=(150, 190, 240)):
    k = ('ging', col)
    if k in _bg: return _bg[k]
    a = np.full((H, W, 3), 250, np.float32); s = 54
    xs = ((np.arange(W) // s) % 2 == 0)[None, :]; ys = ((np.arange(H) // s) % 2 == 0)[:, None]
    c = np.float32(col)
    a[xs & ys] = c; a[(xs ^ ys)] = (c + 250) / 2
    _bg[k] = np.clip(a + paper_tex(H, W, 9, 4), 0, 255).astype(np.uint8); return _bg[k]


def bg_asset(path):
    if path in _bg: return _bg[path]
    im = Image.open(path).convert('RGB'); s = max(W / im.width, H / im.height)
    im = im.resize((int(im.width * s) + 1, int(im.height * s) + 1), Image.LANCZOS)
    l, t = (im.width - W) // 2, (im.height - H) // 2
    _bg[path] = np.asarray(im.crop((l, t, l + W, t + H))); return _bg[path]


def background(name, t, plan):
    if name == 'sky': a = bg_sky()
    elif name == 'hills': a = bg_paper_hills(False)
    elif name == 'dusk': a = bg_paper_hills(True)
    elif name.startswith('gingham'): a = bg_gingham({'gingham': (150, 190, 240), 'gingham-pink': (244, 170, 190), 'gingham-yellow': (246, 214, 120)}.get(name, (150, 190, 240)))
    else: a = bg_asset(os.path.join(plan['avatar_dir'], name))
    # slow drift so it never feels static
    dx = 14 * math.sin(t * 0.35); M = np.float32([[1.03, 0, -W * 0.015 + dx], [0, 1.03, -H * 0.015]])
    return Image.fromarray(cv2.warpAffine(a, M, (W, H), borderMode=cv2.BORDER_REFLECT)).convert('RGBA')


# ---------------- items -----------------
PINK = (236, 72, 120); YEL = (255, 204, 0); GREEN = (88, 214, 120); INK = (24, 24, 28)


def chapter_card(n, title, tag='Chapter'):
    w, h = 820, 330
    im = rr(w, h, 34, (255, 253, 246, 255)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, w - 1, 58], 34, fill=YEL + (255,)); d.rectangle([0, 34, w, 58], fill=YEL + (255,))
    d.text((26, 12), '< Notes', font=font('inter', 30), fill=(90, 70, 0, 255))
    t = f'{tag} {n}'; d.text((w - 26 - font('inter', 28).getlength(t), 14), t, font=font('inter', 28), fill=(90, 70, 0, 255))
    d.rounded_rectangle([34, 92, 214, 300], 26, fill=PINK + (255,))
    nt = text(str(n), 'heavy', 150, (255, 255, 255)); im.alpha_composite(nt, (124 - nt.width // 2, 196 - nt.height // 2))
    y = 110
    for line in wrap(title, 'heavy', 54, 560)[:3]:
        d.text((246, y), line, font=font('heavy', 54), fill=INK + (255,)); y += 66
    return shadow(im)


def window_card(title, lines, typed=1.0, label=None, w=900, h=560, cursor_t=None):
    im = rr(w, h, 30, (255, 255, 255, 255)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, w - 1, 70], 30, fill=(242, 240, 234, 255)); d.rectangle([0, 40, w, 70], fill=(242, 240, 234, 255))
    for i, c in enumerate(((255, 95, 87), (254, 188, 46), (40, 200, 64))): d.ellipse([28 + i * 34, 24, 50 + i * 34, 46], fill=c + (255,))
    d.text((w / 2 - font('inter', 30).getlength(title) / 2, 18), title, font=font('inter', 30), fill=(70, 70, 76, 255))
    total = sum(len(l) for l in lines); n = int(total * clamp(typed)); y = 100
    for l in lines:
        k = max(0, min(len(l), n)); n -= len(l)
        if k:
            d.text((40, y), l[:k], font=font('inter', 38), fill=INK + (255,))
        y += 58
        if y > h - 60: break
    if label:
        p = pill(label, 30, GREEN, INK); im.alpha_composite(p, (w - p.width - 24, h - p.height - 20))
    return shadow(im)


def pill(s, size, bg, fg, k='heavy'):
    t = text(s, k, size, fg); w, h = t.width + size * 0.9, t.height + size * 0.5
    im = rr(w, h, h / 2, bg + (255,)); im.alpha_composite(t, (int((w - t.width) / 2), int((h - t.height) / 2))); return im


def notif_row(app, msg, col=(37, 211, 102)):
    w, h = 860, 120
    im = rr(w, h, 28, (255, 255, 255, 245)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([20, 18, 104, 102], 22, fill=col + (255,))
    d.text((126, 16), app, font=font('heavy', 32), fill=INK + (255,)); d.text((126, 62), msg, font=font('inter', 32), fill=(80, 80, 86, 255))
    d.text((w - 90, 18), 'now', font=font('inter', 26), fill=(150, 150, 156, 255))
    return shadow(im, 10, (0, 8), 90)


def board(rows, t, t0):
    w, h = 900, 120 + 92 * len(rows)
    im = rr(w, h, 24, (22, 22, 26, 255)); d = ImageDraw.Draw(im)
    d.text((34, 24), 'DEPARTURES', font=font('mono', 40), fill=YEL + (255,))
    chars = ' ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789:'
    for r, row in enumerate(rows):
        y = 100 + r * 92
        for c, ch in enumerate(row[:22]):
            x = 34 + c * 38; settle = t0 + 0.08 * c + 0.25 * r
            d.rounded_rectangle([x, y, x + 34, y + 70], 6, fill=(40, 40, 46, 255))
            if t < settle + 0.5:
                rnd = random.Random(int(t * 30) + c * 7 + r * 13); ch2 = chars[rnd.randrange(len(chars))] if t >= t0 else ' '
            else: ch2 = ch
            d.text((x + 5, y + 8), ch2, font=font('mono', 46), fill=(250, 240, 200, 255))
            d.line([(x, y + 35), (x + 34, y + 35)], fill=(0, 0, 0, 255), width=2)
    return shadow(im)


_th = {}


def thumb(path, w, h):
    k = (path, w, h)
    if k not in _th:
        im = Image.open(path).convert('RGB'); s = max(w / im.width, h / im.height)
        im = im.resize((int(im.width * s) + 1, int(im.height * s) + 1)); l, t = (im.width - w) // 2, (im.height - h) // 2
        _th[k] = im.crop((l, t, l + w, t + h)).convert('RGBA')
    return _th[k]


def filmstrip(paths, t, t0, speed=220):
    fh, fw = 300, 230; n = len(paths)
    strip = Image.new('RGBA', (W + fw * 2, fh + 90), (18, 18, 20, 255)); d = ImageDraw.Draw(strip)
    off = int(((t - t0) * speed) % fw)
    for i in range(-1, strip.width // fw + 1):
        x = i * fw - off + 10
        im = thumb(paths[(i + int((t - t0) * speed) // fw) % n], fw - 20, fh)
        strip.alpha_composite(im, (x, 45)) if x >= 0 and x + im.width <= strip.width else _clip_into(strip, im, x, 45)
        for hy in (12, fh + 58): d.rounded_rectangle([x + 20, hy, x + 60, hy + 22], 4, fill=(240, 240, 236, 255)); d.rounded_rectangle([x + 120, hy, x + 160, hy + 22], 4, fill=(240, 240, 236, 255))
    return strip


def _clip_into(dst, im, x, y):
    x0, x1 = max(0, x), min(dst.width, x + im.width)
    if x1 > x0: dst.alpha_composite(im.crop((x0 - x, 0, x1 - x, im.height)), (x0, y))


def phone(frame_rgb, w=420):
    h = int(w * 2.05); im = rr(w + 28, h + 28, 64, (20, 20, 24, 255))
    sc = Image.fromarray(frame_rgb).convert('RGBA'); s = max(w / sc.width, h / sc.height)
    sc = sc.resize((int(sc.width * s) + 1, int(sc.height * s) + 1)); l, t = (sc.width - w) // 2, (sc.height - h) // 2; sc = sc.crop((l, t, l + w, t + h))
    m = Image.new('L', (w, h), 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, w - 1, h - 1], 52, fill=255); sc.putalpha(m)
    im.alpha_composite(sc, (14, 14)); return shadow(im, 20, (0, 16), 130)


def mascot(t):
    px = [
        '..XXXX..', '.XOOOOX.', 'XOWOOWOX', 'XOOOOOOX', 'XOOPPOOX', '.XOOOOX.', '.X.XX.X.', '.X....X.']
    s = 9; im = Image.new('RGBA', (8 * s, 8 * s), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    cols = {'X': (60, 30, 20), 'O': (236, 132, 86), 'W': (255, 255, 255), 'P': (200, 60, 70)}
    blink = int(t * 1.3) % 6 == 0
    for y, row in enumerate(px):
        for x, ch in enumerate(row):
            if ch == '.': continue
            c = cols['O'] if (ch == 'W' and blink) else cols[ch]
            d.rectangle([x * s, y * s, x * s + s - 1, y * s + s - 1], fill=c + (255,))
    return im


def sticker(path, w):
    im = Image.open(path).convert('RGBA'); bb = im.getchannel('A').point(lambda v: 255 if v > 20 else 0).getbbox()
    if bb: im = im.crop(bb)
    s = w / im.width; return im.resize((int(im.width * s), int(im.height * s)), Image.LANCZOS)


def poster(title, sub, handle):
    w, h = 900, 560; im = rr(w, h, 30, (255, 252, 240, 255)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([30, 30, 230, 80], 14, fill=GREEN + (255,)); d.text((52, 38), 'FREE · LIVE', font=font('heavy', 28), fill=INK + (255,))
    y = 110
    for line in wrap(title, 'heavy', 84, 820)[:2]:
        d.text((34, y), line, font=font('heavy', 84), fill=INK + (255,)); y += 96
    d.text((34, y + 10), sub, font=font('inter', 36), fill=(70, 70, 76, 255))
    p = pill(handle, 36, PINK, (255, 255, 255)); im.alpha_composite(p, (34, h - p.height - 34))
    return shadow(im)


# ---------------- avatar -----------------
_av = {}


def avatar(plan, pose, t, talking):
    p = os.path.join(plan['avatar_dir'], pose)
    if p not in _av:
        im = Image.open(p).convert('RGBA'); bb = im.getchannel('A').point(lambda v: 255 if v > 20 else 0).getbbox(); im = im.crop(bb)
        s = H * plan.get('avatar_height', 0.43) / im.height; _av[p] = im.resize((int(im.width * s), int(im.height * s)), Image.LANCZOS)
    im = _av[p]
    sy = 1 + (0.012 * abs(math.sin(t * 11)) if talking else 0.004 * math.sin(t * 2))
    im2 = im.resize((im.width, int(im.height * sy)), Image.BICUBIC)
    return im2


# ---------------- frame -----------------
def captions_at(plan, t):
    for c0, c1, txt in plan['_chunks']:
        if c0 <= t < c1: return txt, c0
    return None, None


def build_chunks(plan):
    words = json.load(open(plan['words'])) if plan.get('words') else []
    ww = [w for s in words for w in s['words']]
    out = []
    for c0, c1, line in plan['captions']:
        toks = line.split(); n = len(toks)
        wt = [w for w in ww if c0 - 0.05 <= w[0] < c1]
        starts = []
        for i in range(n):
            if wt: starts.append(wt[min(len(wt) - 1, int(i * len(wt) / n))][0])
            else: starts.append(c0 + (c1 - c0) * i / n)
        starts = sorted(starts)
        i = 0
        while i < n:
            k = 2 if (i + 1 < n and len(toks[i]) + len(toks[i + 1]) <= 11) else 1
            s0 = starts[i]; s1 = starts[i + k] if i + k < n else c1
            out.append((s0, s1, ' '.join(toks[i:i + k]))); i += k
    plan['_chunks'] = out


def frame(plan, t):
    sc = [s for s in plan['scenes'] if s['t0'] <= t < s['t1']]
    sc = sc[0] if sc else plan['scenes'][-1]
    base = background(sc['bg'], t, plan)
    lt = t - sc['t0']; talking = captions_at(plan, t)[0] is not None
    # avatar (behind captions, in front of scene items placed low)
    for it in sc.get('items', []):
        if it.get('layer', 'top') != 'back': continue
        draw_item(base, it, t, sc, plan)
    av = avatar(plan, sc.get('pose', '01_avatar_wave.png'), t, talking)
    k = back_out(lt / 0.45) if sc['t0'] > 0 else 1
    ay = H - av.height / 2 + 30 + (1 - clamp(k)) * 420
    sh = Image.new('RGBA', (av.width, 80), (0, 0, 0, 0)); ImageDraw.Draw(sh).ellipse([av.width * 0.15, 10, av.width * 0.85, 70], fill=(0, 0, 0, 90))
    place(base, sh.filter(ImageFilter.GaussianBlur(12)), W / 2, H - 30)
    place(base, av, W / 2, ay)
    for it in sc.get('items', []):
        if it.get('layer', 'top') == 'back': continue
        draw_item(base, it, t, sc, plan)
    # mascot
    m = mascot(t); place(base, m, W * 0.86, H * 0.86 + 10 * math.sin(t * 3.2))
    # caption
    txt, c0 = captions_at(plan, t)
    if txt:
        im = text(txt, 'serif_i', 88, (255, 255, 255))
        sh2 = Image.new('RGBA', (im.width + 60, im.height + 60), (0, 0, 0, 0)); sh2.alpha_composite(im, (30, 30))
        blk = Image.new('RGBA', sh2.size, (0, 0, 0, 255)); blk.putalpha(sh2.getchannel('A').filter(ImageFilter.GaussianBlur(10)).point(lambda v: min(255, v * 2)))
        e = back_out((t - c0) / 0.18)
        place(base, blk, W / 2, plan.get('caption_y', 0.6) * H, 0.9 + 0.1 * e, 0, 0.55)
        place(base, im, W / 2, plan.get('caption_y', 0.6) * H, 0.9 + 0.1 * e)
    # hard cut flash
    for s in plan['scenes']:
        d = t - s['t0']
        if 0 <= d < 0.12 and s['t0'] > 0:
            base = Image.blend(base, Image.new('RGBA', (W, H), (255, 255, 255, 255)), 0.7 * (1 - d / 0.12))
    if t < 0.15: base = Image.blend(Image.new('RGBA', (W, H), (0, 0, 0, 255)), base, t / 0.15)
    return base.convert('RGB')


_rec = {}


def draw_item(base, it, t, sc, plan):
    t0 = sc['t0'] + it.get('t', 0); t1 = sc['t0'] + it['t_end'] if 't_end' in it else sc['t1']
    if t < t0 or t > t1 + 0.2: return
    u = t - t0; a = 1 - clamp((t - t1) / 0.2) if t > t1 else 1
    e = back_out(u / 0.4); x, y = it.get('x', 0.5) * W, it.get('y', 0.3) * H; rot = it.get('rot', 0) + 1.2 * math.sin(t * 1.4 + x)
    ty = it['type']
    if ty == 'chapter':
        im = _cache(it, lambda: chapter_card(it['n'], it['title'], it.get('tag', 'Chapter')))
        place(base, im, x, y + (1 - clamp(e)) * 120, 0.85 + 0.15 * clamp(e), rot, a)
    elif ty == 'window':
        typed = clamp((u - 0.3) / it.get('type_dur', 1.6))
        im = window_card(it['title'], it['lines'], typed, it.get('label') if typed >= 1 else None, it.get('w', 900), it.get('h', 560))
        place(base, im, x, y, 0.85 + 0.15 * clamp(e), rot * 0.5, a)
    elif ty == 'notifs':
        for i, (app, msg) in enumerate(it['rows']):
            ti = t0 + i * it.get('gap', 0.45)
            if t < ti: continue
            ei = back_out((t - ti) / 0.35); im = _cache((it, i), lambda app=app, msg=msg: notif_row(app, msg))
            place(base, im, x + (1 - clamp(ei)) * 600, y + i * 140, 0.95, 0, a)
    elif ty == 'board':
        place(base, board(it['rows'], t, t0 + 0.2), x, y, 0.85 + 0.15 * clamp(e), 0, a)
    elif ty == 'filmstrip':
        place(base, filmstrip(it['images'], t, t0), x, y, 1, it.get('rot', -4), a)
    elif ty in ('stencil', 'pill'):
        if ty == 'stencil': im = _cache(it, lambda: text(it['text'], 'stencil', it.get('size', 120), (255, 255, 255), 6, (0, 0, 0)))
        else: im = _cache(it, lambda: pill(it['text'], it.get('size', 52), tuple(it.get('bg', GREEN)), tuple(it.get('fg', INK))))
        place(base, im, x, y, clamp(e) if ty == 'pill' else 0.9 + 0.1 * clamp(e), it.get('rot', 0), a)
    elif ty == 'sticker':
        im = _cache(it, lambda: sticker(os.path.join(plan['avatar_dir'], it['file']), it.get('w', 220)))
        place(base, im, x, y + 8 * math.sin(t * 2 + x), clamp(e), rot + it.get('rot', 0), a)
    elif ty == 'phone':
        fr = it['frames']; srcs = sorted(os.listdir(fr)); k = int(clamp(u / max(0.1, (t1 - t0))) * (len(srcs) - 1))
        p = os.path.join(fr, srcs[k])
        if p not in _rec:
            if len(_rec) > 40: _rec.clear()
            _rec[p] = cv2.cvtColor(cv2.imread(p), cv2.COLOR_BGR2RGB)
        place(base, phone(_rec[p], it.get('w', 400)), x, y + (1 - clamp(e)) * 200, 1, it.get('rot', 4), a)
    elif ty == 'poster':
        im = _cache(it, lambda: poster(it['title'], it.get('sub', ''), it.get('handle', '')))
        place(base, im, x, y, 0.85 + 0.15 * clamp(e), rot * 0.4, a)


_ic = {}


def _cache(key, fn):
    k = json.dumps(key, sort_keys=True, default=str) if not isinstance(key, tuple) else json.dumps(key[0], sort_keys=True, default=str) + str(key[1])
    if k not in _ic: _ic[k] = fn()
    return _ic[k]


# ---------------- sound -----------------
def sfx_mix(plan, out_wav):
    SR = 44100
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', plan['voice'], '-ac', '1', '-ar', str(SR), '-f', 'f32le', '-'], capture_output=True).stdout
    vo = np.frombuffer(raw, np.float32).copy(); T = plan['duration']; N = int(T * SR)
    vo = np.pad(vo, (0, max(0, N - len(vo))))[:N]; vo = vo / (np.abs(vo).max() + 1e-6) * 0.85
    mix = np.zeros(N, np.float32); rng = np.random.default_rng(3)
    def add(t, s, g):
        i = int(t * SR); e = min(N, i + len(s))
        if 0 <= i < N: mix[i:e] += s[:e - i] * g
    def click():
        n = int(SR * 0.05); x = np.arange(n) / SR; return np.sin(2 * np.pi * 2200 * x) * np.exp(-x * 120)
    def pop():
        n = int(SR * 0.16); x = np.arange(n) / SR; f = 500 + 900 * np.exp(-x * 30); return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-x * 22)
    def bell():
        n = int(SR * 0.9); x = np.arange(n) / SR; return (np.sin(2 * np.pi * 1318 * x) + 0.5 * np.sin(2 * np.pi * 1976 * x)) * np.exp(-x * 6)
    def impact():
        n = int(SR * 0.5); x = np.arange(n) / SR; return np.sin(2 * np.pi * (60 + 80 * np.exp(-x * 25)) * x) * np.exp(-x * 8) + rng.standard_normal(n) * np.exp(-x * 50) * 0.3
    add(0.05, impact(), 0.5)
    for s in plan['scenes'][1:]: add(s['t0'], click(), 0.35)
    for s in plan['scenes']:
        for it in s.get('items', []):
            tt = s['t0'] + it.get('t', 0)
            if it['type'] == 'chapter': add(tt, bell(), 0.22)
            elif it['type'] == 'notifs':
                for i in range(len(it['rows'])): add(tt + i * it.get('gap', 0.45), pop(), 0.2)
            elif it['type'] == 'window':
                k = tt + 0.3
                while k < tt + 0.3 + it.get('type_dur', 1.6): add(k, click() * 0.5, 0.25); k += rng.uniform(0.06, 0.13)
            else: add(tt, pop(), 0.18)
    x = np.arange(N) / SR; pad = np.zeros(N, np.float32)
    for i, t0 in enumerate(np.arange(0, T, 3.2)):
        ch = [(261.6, 329.6, 392), (220, 261.6, 329.6), (174.6, 220, 261.6), (196, 246.9, 293.7)][i % 4]
        s = int(t0 * SR); e = min(N, int((t0 + 3.8) * SR)); xx = np.arange(e - s) / SR; env = np.minimum(1, xx / 0.8) * np.minimum(1, (3.8 - xx) / 1.2)
        for f in ch: pad[s:e] += np.sin(2 * np.pi * f * xx) * env * 0.3
    out = vo + mix * 0.32 + pad * 0.04; out = np.tanh(out * 1.05); out = out / np.abs(out).max() * 0.92
    st = (np.stack([out, out], 1) * 32767).astype(np.int16)
    import wave
    w = wave.open(out_wav, 'wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(st.tobytes()); w.close()


def render(plan, out):
    build_chunks(plan); T = plan['duration']; fps = plan.get('fps', 30)
    wav = out + '.mix.wav'; sfx_mix(plan, wav)
    enc = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(fps), '-i', '-', '-i', wav,
                            '-map', '0:v', '-map', '1:a', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '18', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k', '-shortest', out], stdin=subprocess.PIPE)
    for i in range(int(T * fps)): enc.stdin.write(np.asarray(frame(plan, i / fps)).tobytes())
    enc.stdin.close(); enc.wait(); os.remove(wav)


if __name__ == '__main__':
    plan = json.load(open(sys.argv[1]))
    if len(sys.argv) > 3 and sys.argv[3] == '--stills':
        build_chunks(plan)
        ts = [float(x) for x in sys.argv[4].split(',')]
        ims = [frame(plan, t).resize((270, 480)) for t in ts]
        M = Image.new('RGB', (min(8, len(ims)) * 270, ((len(ims) + 7) // 8) * 480))
        for i, im in enumerate(ims): M.paste(im, ((i % 8) * 270, (i // 8) * 480))
        M.save(sys.argv[2])
    else:
        render(plan, sys.argv[2])
