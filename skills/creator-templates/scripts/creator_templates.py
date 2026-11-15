"""Creator-style templates (learned from watching @vibha.in.progress reels, Nov 2026; own code and design).
  compare   - RAW vs EDITED split cards on a dark textured board
  proof     - stats dashboard card + 2-line headline + speaker card + side word captions
  chatcmd   - chat app mock: a /command is typed, 'working' line, then the result goes full screen
  news      - newspaper page where a highlighter sweeps over the key sentence
Usage: python3 creator_templates.py plan.json out.mp4      (see example_plan.json)
"""
import numpy as np, cv2, math, subprocess, sys, json, os, textwrap
from PIL import Image, ImageDraw, ImageFont
W, H, FPS = 1080, 1920, 30
FD = os.environ.get('REEL_FONTS', '/home/claude/effects/fonts/')
F = lambda n, s: ImageFont.truetype(FD + n, s)
BOLD, SERIF, PLAY, MONO, INTER = 'ArchivoBlack-Regular.ttf', 'InstrumentSerif-Italic.ttf', 'PlayfairDisplay.ttf', 'SpaceMono-Bold.ttf', 'Inter.ttf'
ease = lambda u: 1 - (1 - min(max(u, 0), 1)) ** 3
def back(u, s=1.7): u = min(max(u, 0), 1); return 1 + (s + 1) * (u - 1) ** 3 + s * (u - 1) ** 2

class Clip:
    """video file (or still image) read frame by frame, looped"""
    def __init__(s, path):
        s.img = None; s.cap = None
        if path.lower().endswith(('.png', '.jpg', '.jpeg')): s.img = cv2.cvtColor(cv2.imread(path), cv2.COLOR_BGR2RGB)
        else: s.cap = cv2.VideoCapture(path); s.i = -1; s.last = None
    def at(s, t):
        if s.img is not None: return s.img
        i = int(t * (s.cap.get(cv2.CAP_PROP_FPS) or 30))
        if i != s.i + 1: s.cap.set(cv2.CAP_PROP_POS_FRAMES, i)
        ok, f = s.cap.read(); s.i = i
        if ok: s.last = cv2.cvtColor(f, cv2.COLOR_BGR2RGB)
        return s.last

def cover(img, w, h):
    ih, iw = img.shape[:2]; sc = max(w / iw, h / ih); r = cv2.resize(img, (int(iw * sc) + 1, int(ih * sc) + 1))
    y = (r.shape[0] - h) // 2; x = (r.shape[1] - w) // 2; return r[y:y + h, x:x + w]

def rr(w, h, r):
    m = Image.new('L', (w, h), 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, w - 1, h - 1], r, fill=255); return m

def card(fr, img, x, y, w, h, r=36, shadow=True):
    """paste img as rounded card on PIL frame"""
    if shadow:
        sh = Image.new('RGBA', (w + 80, h + 80), (0, 0, 0, 0)); ImageDraw.Draw(sh).rounded_rectangle([40, 50, w + 40, h + 50], r, fill=(0, 0, 0, 120))
        from PIL import ImageFilter; fr.alpha_composite(sh.filter(ImageFilter.GaussianBlur(18)), (x - 40, y - 40))
    im = Image.fromarray(cover(img, w, h)).convert('RGBA'); im.putalpha(rr(w, h, r)); fr.alpha_composite(im, (x, y))

def pill(d, text, cx, cy, font, bg, fg, pad=(22, 10), r=10):
    b = d.textbbox((0, 0), text, font=font); w, h = b[2] - b[0], b[3] - b[1]
    d.rounded_rectangle([cx - w / 2 - pad[0], cy - h / 2 - pad[1], cx + w / 2 + pad[0], cy + h / 2 + pad[1]], r, fill=bg)
    d.text((cx - w / 2 - b[0], cy - h / 2 - b[1]), text, font=font, fill=fg)

def texture(col, seed=1, amt=10):
    rng = np.random.default_rng(seed); n = rng.normal(0, amt, (H // 2, W // 2, 1)); n = cv2.resize(n, (W, H))[..., None]
    yy = np.linspace(1.08, 0.82, H)[:, None, None]
    return Image.fromarray(np.clip(np.array(col, np.float32) * yy + n, 0, 255).astype(np.uint8)).convert('RGBA')

# ---------------------------------------------------------------- 1. compare
_bg = {}
def t_compare(p, t, cl):
    if 'cmp' not in _bg: _bg['cmp'] = texture(p.get('bg', (74, 48, 30)), 2, 12)
    fr = _bg['cmp'].copy(); d = ImageDraw.Draw(fr)
    a = ease(t / 0.5); f1 = F(INTER, 46); f2 = F(BOLD, 62)
    for i, (s, f) in enumerate([(p['title'][0].upper(), f1), (p['title'][1].upper(), f2)]):
        sp = 8 if i == 0 else 4; w = sum(d.textlength(c, font=f) + sp for c in s); x = (W - w) / 2
        for c in s: d.text((x, 395 + i * 70 - (1 - a) * 30), c, font=f, fill=(245, 236, 222, int(255 * a))); x += d.textlength(c, font=f) + sp
    cw, ch, gap = 470, 836, 30; x0 = (W - 2 * cw - gap) // 2; y0 = 640
    for i, key in enumerate(['raw', 'edited']):
        u = ease((t - 0.25 - i * 0.2) / 0.6); yy = int(y0 + (1 - back((t - 0.25 - i * 0.2) / 0.7)) * 500)
        if u <= 0: continue
        card(fr, cl[key].at(t), x0 + i * (cw + gap), yy, cw, ch)
        lab, bg, fg = (p.get('labels', ['RAW', 'EDITED BY AI'])[i], (20, 20, 20), (255, 255, 255)) if i == 0 else (p.get('labels', ['RAW', 'EDITED BY AI'])[1], (255, 205, 60), (20, 20, 20))
        pill(d, lab, x0 + i * (cw + gap) + cw / 2, yy - 44, F(MONO, 28), bg, fg)
    if t > 1.0:
        s = p.get('strip', ''); n = int((t - 1.0) / 0.035); pill(d, s[:n] or ' ', W / 2, 1560, F(MONO, 32), (250, 248, 240), (30, 30, 30), (24, 14), 4)
    return fr

# ---------------------------------------------------------------- 2. proof
def t_proof(p, t, cl):
    if 'pr' not in _bg:
        g = np.zeros((H, W, 3), np.float32); c0, c1 = np.array(p.get('bg0', (255, 240, 236))), np.array(p.get('bg1', (250, 205, 225)))
        g[:] = c0 + (c1 - c0) * np.linspace(0, 1, H)[:, None, None]; _bg['pr'] = Image.fromarray(g.astype(np.uint8)).convert('RGBA')
    fr = _bg['pr'].copy(); d = ImageDraw.Draw(fr)
    # speaker card bottom
    card(fr, cl['speaker'].at(t), 60, 960, 960, 900, 44)
    # dashboard card
    a = back(t / 0.6); cy = int(250 - (1 - a) * 500); cx0, cw, chh = 80, 920, 520
    d.rounded_rectangle([cx0, cy, cx0 + cw, cy + chh], 30, fill=(18, 20, 24))
    d.text((cx0 + 36, cy + 26), p.get('card_title', 'Summary'), font=F(BOLD, 34), fill=(255, 255, 255))
    st = p['stats']; hot = p.get('hot', 0)
    for i, (k, v) in enumerate(st[:4]):
        bx = cx0 + 36 + (i % 2) * 432; by = cy + 100 + (i // 2) * 200
        u = ease((t - 0.5 - i * 0.12) / 0.8)
        if i == hot:
            gl = 0.5 + 0.5 * math.sin(t * 5); d.rounded_rectangle([bx - 4, by - 4, bx + 416 + 4, by + 180 + 4], 20, outline=(60, 230, 130, int(120 + 135 * gl)), width=6)
        d.rounded_rectangle([bx, by, bx + 416, by + 180], 16, fill=(34, 37, 43))
        d.text((bx + 22, by + 18), k, font=F(INTER, 28), fill=(170, 175, 185))
        num = v
        try:
            n = float(str(v).replace(',', '')); num = f'{int(n * u):,}' if n == int(n) else f'{n * u:.1f}' + ''
        except ValueError: pass
        d.text((bx + 22, by + 70), str(num), font=F(BOLD, 60), fill=(255, 255, 255))
    # headline
    u = ease((t - 0.3) / 0.4); f = F(BOLD, 58)
    w = d.textlength(p['headline'][0], font=f); d.text(((W - w) / 2, 800 - (1 - u) * 20), p['headline'][0], font=f, fill=(20, 20, 20, int(255 * u)))
    if t > 0.5: pill(d, p['headline'][1], W / 2, 905, F(BOLD, 42), tuple(p.get('accent', (240, 60, 120))), (255, 255, 255), (22, 12), 8)
    # side word captions
    for c0, c1, wd in p.get('words', []):
        if c0 <= t < c1:
            s = back((t - c0) / 0.18); f = F(BOLD, int(64 * (0.7 + 0.3 * s))); d.text((110, 1010), wd, font=f, fill=(255, 255, 255), stroke_width=6, stroke_fill=(20, 20, 20))
    return fr

# ---------------------------------------------------------------- 3. chat command
def t_chatcmd(p, t, cl):
    T1 = p.get('type_end', 1.6); T2 = p.get('result_at', 2.6)
    fr = Image.new('RGBA', (W, H), (26, 25, 23, 255)); d = ImageDraw.Draw(fr)
    d.text((W / 2 - d.textlength(p.get('app', 'Assistant'), font=F(BOLD, 40)) / 2, 150), p.get('app', 'Assistant'), font=F(BOLD, 40), fill=(240, 236, 228))
    cmd = p['command']; n = int(len(cmd) * min(1, t / T1)); f = F(INTER, 46)
    if t < T1 + 0.25:
        g = p.get('greeting', 'How can I help you?'); w = d.textlength(g, font=F(SERIF, 76)); d.text(((W - w) / 2, 620), g, font=F(SERIF, 76), fill=(235, 228, 215))
        d.rounded_rectangle([60, 900, W - 60, 1130], 40, fill=(48, 46, 42)); d.text((100, 940), cmd[:n] + ('|' if int(t * 4) % 2 == 0 else ''), font=f, fill=(232, 130, 90))
        d.ellipse([W - 170, 1030, W - 100, 1100], fill=(217, 119, 87)); d.polygon([(W - 135, 1048), (W - 152, 1074), (W - 118, 1074)], fill=(255, 255, 255))
        # keyboard
        ky = 1220; rows = ['QWERTYUIOP', 'ASDFGHJKL', 'ZXCVBNM']; cur = cmd[n - 1].upper() if 0 < n <= len(cmd) and t < T1 else ''
        d.rectangle([0, ky - 30, W, H], fill=(40, 40, 42))
        for r, row in enumerate(rows):
            kw = 98; x = (W - len(row) * kw) / 2
            for c in row:
                on = c == cur; d.rounded_rectangle([x + 5, ky + r * 140, x + kw - 5, ky + r * 140 + 120], 14, fill=(250, 250, 250) if on else (96, 96, 100))
                d.text((x + kw / 2 - d.textlength(c, font=F(INTER, 44)) / 2, ky + r * 140 + 32), c, font=F(INTER, 44), fill=(20, 20, 20) if on else (255, 255, 255)); x += kw
    else:
        # sent bubble + working line
        w = d.textlength(cmd, font=f); u = ease((t - T1 - 0.25) / 0.3)
        d.rounded_rectangle([W - w - 130, 300 + (1 - u) * 600, W - 60, 392 + (1 - u) * 600], 30, fill=(70, 46, 36)); d.text((W - w - 95, 316 + (1 - u) * 600), cmd, font=f, fill=(232, 130, 90))
        dots = '.' * (1 + int(t * 3) % 3); d.text((70, 450), p.get('working', 'Working') + dots, font=F(INTER, 36), fill=(170, 165, 155))
    if t > T2 - 0.05:
        u = ease((t - T2) / 0.5); res = cl['result'].at(max(0, t - T2))
        w0, h0, x0, y0 = 620, 1102, 70, 520
        w = int(w0 + (W - w0) * u); h = int(h0 + (H - h0) * u); x = int(x0 * (1 - u)); y = int(y0 * (1 - u))
        card(fr, res, x, y, w, h, int(36 * (1 - u)) + 1, shadow=u < 0.95)
    return fr

# ---------------------------------------------------------------- 4. news highlight
def t_news(p, t, cl):
    if 'nw' not in _bg: _bg['nw'] = texture((236, 228, 210), 5, 7)
    fr = _bg['nw'].copy(); d = ImageDraw.Draw(fr); ink = (28, 24, 20)
    z = 1.0
    d.text((80, 150), p.get('dateline', 'SPECIAL EDITION'), font=F(MONO, 24), fill=(90, 80, 70))
    f = F(PLAY, 120); w = d.textlength(p['paper'], font=f); d.text(((W - w) / 2, 190), p['paper'], font=f, fill=ink, stroke_width=2, stroke_fill=ink)
    d.line([70, 350, W - 70, 350], fill=ink, width=5); d.line([70, 362, W - 70, 362], fill=ink, width=2)
    y = 400; f = F(PLAY, 84)
    for ln in textwrap.wrap(p['headline'], 22): d.text((80, y), ln, font=f, fill=ink, stroke_width=1, stroke_fill=ink); y += 98
    y += 30; f = F(PLAY, 50); key = p.get('highlight', ''); body = p['body']; s0 = body.find(key); pos = 0
    hu = ease((t - p.get('hl_at', 1.0)) / p.get('hl_dur', 1.4)); done = int(len(key) * hu)
    for ln in textwrap.wrap(body, 38):
        st = body.find(ln, pos); pos = st + len(ln); x = 80
        for i, c in enumerate(ln):
            gi = st + i; cwid = d.textlength(c, font=f)
            if s0 >= 0 and s0 <= gi < s0 + done: d.rectangle([x - 1, y + 6, x + cwid + 1, y + 62], fill=tuple(p.get('hl_col', (255, 120, 220))) + (150,) if False else tuple(p.get('hl_col', (245, 130, 220))))
            x += cwid
        d.text((80, y), ln, font=f, fill=ink); y += 70
    if 'photo' in cl and y < H - 500: card(fr, cl['photo'].at(t), 80, y + 40, W - 160, min(700, H - y - 140), 6, False)
    # slow push-in
    a = np.asarray(fr.convert('RGB')); zz = 1 + 0.06 * min(t, 5) / 5
    M = np.float32([[zz, 0, W / 2 * (1 - zz)], [0, zz, 700 * (1 - zz)]]); return Image.fromarray(cv2.warpAffine(a, M, (W, H), borderMode=cv2.BORDER_REPLICATE))

TPL = {'compare': t_compare, 'proof': t_proof, 'chatcmd': t_chatcmd, 'news': t_news}

def main(plan_path, out):
    plan = json.load(open(plan_path)); base = os.path.dirname(os.path.abspath(plan_path))
    R = lambda q: q if os.path.isabs(q) else os.path.join(base, q)
    args = ['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-']
    if plan.get('audio'): args += ['-i', R(plan['audio']), '-map', '0:v', '-map', '1:a', '-c:a', 'aac', '-shortest']
    enc = subprocess.Popen(args + ['-c:v', 'libx264', '-preset', 'veryfast', '-crf', '18', '-pix_fmt', 'yuv420p', out], stdin=subprocess.PIPE)
    for sc in plan['scenes']:
        cl = {k: Clip(R(v)) for k, v in sc.get('clips', {}).items()}; _bg.clear()
        for i in range(int(sc['dur'] * FPS)):
            fr = TPL[sc['template']](sc, i / FPS, cl); enc.stdin.write(np.asarray(fr.convert('RGB')).tobytes())
    enc.stdin.close(); enc.wait()

if __name__ == '__main__': main(sys.argv[1], sys.argv[2])
