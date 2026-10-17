"""Kitaab Likhunga — trending maroon faceless-couple reel. Word-by-word Cormorant italic shayari captions; the
rhyme word of each misra (kitaab / gulaab / sharaab / nawaab / adaab / jannat / jawaab) blooms big in gold Great
Vibes script with a glow. Hook from frame 0: most striking image (veiled bride + rose), first word already on,
gold kicker line. Soft crossfades, slow Ken Burns, candle flicker, falling rose petals, gold dust, vignette, grain."""
import numpy as np, cv2, subprocess, sys, math
from PIL import Image, ImageDraw, ImageFont, ImageFilter
D = '/home/claude/raft/kitaab/'
SRC = '/root/.claude/uploads/7e7fbd2a-05f7-5789-85d7-a95bbba90e41/f270fc1a-igexport-Dc1Uj3YT5K0.mp4'
FD = '/home/claude/reel-editor-skills/skills/reel-editor/fonts/'
W, H, FPS = 1080, 1920, 30
DUR = 33.5
rng = np.random.default_rng(11)

SHOTS = [(0.0, 3), (1.9, 1), (3.6, 2), (5.0, 4), (7.2, 5), (10.0, 6), (12.9, 7), (16.0, 8), (18.0, 9), (19.6, 10),
         (22.5, 11), (27.0, 12), (28.8, 13), (30.6, 14)]
UNITS = [(0.0, 3.9, 'Jab bhi tere baare mein *kitaab likhunga'), (5.0, 7.2, 'Main tere honton ko *gulaab likhunga'),
         (7.2, 9.9, 'Teri aankhon ko *sharaab likhunga'), (10.0, 12.9, 'Likhunga tujhe rani pariyon ki'),
         (12.9, 15.9, 'Aur phir khud ko *nawaab likhunga'), (16.0, 19.4, 'Saliqa sikhaya jaayega mohabbat ka jab kahin'),
         (19.4, 22.3, 'Tere har andaaz ko *adaab likhunga'), (22.6, 26.6, 'Hoga sawaal *jannat ka jab kahin'),
         (27.2, 30.4, 'Main teri baahon ko *jawaab likhunga'), (30.6, 33.3, 'Jab bhi tere baare mein *kitaab likhunga')]

# ---------------- images
IMG = {}
def img(n):
    if n not in IMG:
        im = cv2.imread(D + f'img/{n:02d}.png')
        IMG[n] = cv2.resize(im, (int(W * 1.12), int(H * 1.12)), interpolation=cv2.INTER_LANCZOS4).astype(np.float32)
    return IMG[n]

def shot(k, t):
    st, n = SHOTS[k]; en = SHOTS[k + 1][0] if k + 1 < len(SHOTS) else DUR
    u = (t - st) / (en - st); im = img(n); MH, MW = im.shape[:2]
    z = 1.0 + 0.08 * u if k % 2 == 0 else 1.08 - 0.07 * u
    if k == 0: z = 1.10 - 0.10 * (1 - (1 - min(1, t / 1.6)) ** 3) + 0.02 * u      # hook: gentle pull-back reveal
    cw, ch = W / z, H / z; cx = MW / 2 + 18 * (u - 0.5) * (1 if k % 3 else -1); cy = MH / 2 - 10 * (u - 0.5)
    s = W / cw; M = np.float32([[s, 0, -(cx - cw / 2) * s], [0, s, -(cy - ch / 2) * s]])
    f = cv2.warpAffine(im, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    warm = np.clip((f.sum(2) - 520) / 180, 0, 1)                                  # candle / lamp flicker
    fl = 1 + 0.06 * math.sin(t * 13 + n) + 0.04 * math.sin(t * 23 + 2 * n)
    return f * (1 + (fl - 1) * warm[..., None])

XF = 0.3
def base(t):
    k = max(j for j, s in enumerate(SHOTS) if s[0] <= t)
    f = shot(k, t)
    if k > 0 and t - SHOTS[k][0] < XF:
        a = (t - SHOTS[k][0]) / XF; a = a * a * (3 - 2 * a)
        f = shot(k - 1, t) * (1 - a) + f * a
    return f

# ---------------- atmosphere
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
VIG = (1 - 0.45 * np.clip(((xx - W / 2) / (W * 0.75)) ** 2 + ((yy - H * 0.5) / (H * 0.7)) ** 2, 0, 1))[..., None]
TOPSH = (1 - 0.35 * np.clip(1 - np.abs(yy - 600) / 360, 0, 1))[..., None]        # soft dark band under captions
NP = 16
PET = [dict(x=rng.uniform(0, W), y=rng.uniform(-H, H), vy=rng.uniform(60, 120), sw=rng.uniform(25, 60), f=rng.uniform(0.5, 1.2),
            ph=rng.uniform(0, 6.3), r=rng.uniform(12, 22), rot=rng.uniform(0, 360), vr=rng.uniform(-90, 90),
            col=[(40, 30, 150), (55, 40, 175), (35, 25, 120)][rng.integers(0, 3)]) for _ in range(NP)]
DUST = np.c_[rng.uniform(0, W, 70), rng.uniform(0, H, 70), rng.uniform(0.5, 1.5, 70), rng.uniform(0, 6.3, 70)]
GR = [rng.normal(0, 4, (H, W, 1)).astype(np.float32) for _ in range(4)]

def atmos(f, t, i):
    L = np.zeros((H // 2, W // 2), np.float32)
    for x, y, s, p in DUST:
        cv2.circle(L, (int((x + 20 * math.sin(t * 0.6 + p)) / 2), int(((y - t * 30 * s) % H) / 2)), int(1 + s * 0.7),
                   0.3 + 0.7 * (0.5 + 0.5 * math.sin(t * 2.5 + p)), -1, cv2.LINE_AA)
    L = cv2.resize(cv2.GaussianBlur(L, (0, 0), 0.9), (W, H))
    f = f + L[..., None] * np.array([120, 200, 255.]) + cv2.GaussianBlur(L, (0, 0), 5)[..., None] * np.array([60, 140, 230.])
    P = np.zeros((H, W, 3), np.float32); PA = np.zeros((H, W), np.float32)
    for p in PET:
        y = ((p['y'] + p['vy'] * t) % (H + 200)) - 100; x = p['x'] + p['sw'] * math.sin(t * p['f'] + p['ph'])
        ang = p['rot'] + p['vr'] * t; sq = abs(math.cos(math.radians(ang) * 1.3)) * 0.7 + 0.3
        ax = (int(p['r']), max(2, int(p['r'] * 0.6 * sq)))
        cv2.ellipse(P, (int(x), int(y)), ax, ang, 0, 360, p['col'], -1, cv2.LINE_AA)
        cv2.ellipse(PA, (int(x), int(y)), ax, ang, 0, 360, 0.9, -1, cv2.LINE_AA)
    PA = cv2.GaussianBlur(PA, (0, 0), 1.0)[..., None]
    f = f * (1 - PA) + cv2.GaussianBlur(P, (0, 0), 1.0) * PA
    return f * VIG * TOPSH + GR[i % 4]

# ---------------- captions
FN = ImageFont.truetype(FD + 'cormorant-garamond-700i.ttf', 78)
FS = ImageFont.truetype(FD + 'great-vibes-400.ttf', 190)
FK = ImageFont.truetype(FD + 'cormorant-700i.ttf', 50)
CREAM, GOLD = (250, 236, 214), (255, 206, 120)

def layout(text):
    """returns list of word dicts with sprite + position; special word on its own line in script."""
    words = text.split(); out = []; lines = []; cur = []
    for w in words:
        if w.startswith('*'):
            if cur: lines.append(cur); cur = []
            lines.append([w]); continue
        cur.append(w)
        if len(' '.join(cur)) > 21: lines.append(cur); cur = []
    if cur: lines.append(cur)
    d = ImageDraw.Draw(Image.new('L', (8, 8)))
    hts = [215 if l[0].startswith('*') else 96 for l in lines]
    y = 610 - sum(hts) // 2
    for l, hh in zip(lines, hts):
        if l[0].startswith('*'):
            w = l[0][1:]; tw = d.textlength(w, font=FS); out.append(dict(w=w, sp=True, x=(W - tw) / 2, y=y - 10)); y += hh; continue
        sp = d.textlength(' ', font=FN); ws = [d.textlength(w, font=FN) for w in l]; x = (W - sum(ws) - sp * (len(l) - 1)) / 2
        for w, wl in zip(l, ws): out.append(dict(w=w, sp=False, x=x, y=y)); x += wl + sp
        y += hh
    return out

_spr = {}
def sprite(w, sp):
    if (w, sp) not in _spr:
        f = FS if sp else FN; d = ImageDraw.Draw(Image.new('L', (8, 8)))
        tw = int(d.textlength(w, font=f)) + 80; th = 290 if sp else 140
        im = Image.new('RGBA', (tw, th)); ox, oy = 40, 20
        sh = Image.new('RGBA', im.size); ImageDraw.Draw(sh).text((ox, oy), w, font=f, fill=(20, 0, 0, 220), stroke_width=6, stroke_fill=(20, 0, 0, 220))
        im = Image.alpha_composite(im, sh.filter(ImageFilter.GaussianBlur(8)))
        if sp:
            gl = Image.new('RGBA', im.size); ImageDraw.Draw(gl).text((ox, oy), w, font=f, fill=(255, 170, 60, 200), stroke_width=4, stroke_fill=(255, 170, 60, 200))
            im = Image.alpha_composite(im, gl.filter(ImageFilter.GaussianBlur(14)))
        ImageDraw.Draw(im).text((ox, oy), w, font=f, fill=(GOLD if sp else CREAM) + (255,))
        a = np.asarray(im, np.float32); _spr[(w, sp)] = (a[..., 2::-1].copy(), a[..., 3:] / 255, ox, oy)
    return _spr[(w, sp)]

UL = []
for st, en, txt in UNITS:
    items = layout(txt); ws = [max(3, len(it['w'])) * (1.6 if it['sp'] else 1) for it in items]
    span = (en - st) * 0.82; t = st
    for it, wgt in zip(items, ws): it['t'] = t; t += span * wgt / sum(ws)
    UL.append((st, en, items))

def paste(f, L, A, x, y, a, sc=1.0):
    if sc != 1.0:
        L = cv2.resize(L, None, fx=sc, fy=sc); A = cv2.resize(A, (L.shape[1], L.shape[0]))[..., None] if A.ndim == 3 else A
        if A.ndim == 2: A = A[..., None]
    h, w = A.shape[:2]; x, y = int(x), int(y)
    x0, y0, x1, y1 = max(0, x), max(0, y), min(W, x + w), min(H, y + h)
    if x1 <= x0 or y1 <= y0: return
    Ls, As = L[y0 - y:y1 - y, x0 - x:x1 - x], A[y0 - y:y1 - y, x0 - x:x1 - x] * a
    f[y0:y1, x0:x1] = f[y0:y1, x0:x1] * (1 - As) + Ls * As

def captions(f, t):
    for st, en, items in UL:
        if not (st <= t < en + 0.35): continue
        out = 1.0 if t < en else max(0, 1 - (t - en) / 0.35)
        fin = min(1, (t - st) / 0.25) if st > 0 else 1.0                       # whole misra visible (dim) at once
        for it in items:
            lt = t - it['t']
            L, A, ox, oy = sprite(it['w'], it['sp'])
            lo = 0.55 if st == 0 else 0.32; a = (lo + (1 - lo) * min(1, max(0, lt) / 0.15)) * out * fin              # karaoke: dim -> bright when sung
            if it['sp']:
                sc = 1.0 if lt < 0 else 1.0 + 0.16 * math.sin(math.pi * min(1, lt / 0.5))
                cx = it['x'] - ox + L.shape[1] / 2; cy = it['y'] - oy + L.shape[0] / 2
                paste(f, L, A, cx - L.shape[1] * sc / 2, cy - L.shape[0] * sc / 2, a, sc)
            else:
                paste(f, L, A, it['x'] - ox, it['y'] - oy, a)
    return f

def kicker():
    s = 'sirf usko bhejna jiske liye ye likha hai'
    d = ImageDraw.Draw(Image.new('L', (8, 8))); tw = d.textlength(s, font=FK)
    im = Image.new('RGBA', (W, 90)); x = (W - tw) / 2
    sh = Image.new('RGBA', im.size); ImageDraw.Draw(sh).text((x, 14), s, font=FK, fill=(20, 0, 0, 230), stroke_width=5, stroke_fill=(20, 0, 0, 230))
    im = Image.alpha_composite(im, sh.filter(ImageFilter.GaussianBlur(6))); dr = ImageDraw.Draw(im)
    dr.text((x, 14), s, font=FK, fill=GOLD + (255,))
    dr.line((x, 78, x + tw, 78), fill=GOLD + (150,), width=2)
    a = np.asarray(im, np.float32); return a[..., 2::-1].copy(), a[..., 3:] / 255
KL, KA = kicker(); KY = 225; KEND = 3.6

def handle():
    f = ImageFont.truetype(FD + 'montserrat-700.ttf', 27); im = Image.new('RGBA', (W, 60))
    sh = Image.new('RGBA', im.size); ImageDraw.Draw(sh).text((56, 12), '@aitricksbysumit', font=f, fill=(0, 0, 0, 200), stroke_width=4, stroke_fill=(0, 0, 0, 200))
    im = Image.alpha_composite(im, sh.filter(ImageFilter.GaussianBlur(5))); d = ImageDraw.Draw(im)
    d.rectangle((40, 11, 45, 43), fill=(255, 190, 110, 235)); d.text((56, 12), '@aitricksbysumit', font=f, fill=(255, 255, 255, 225))
    a = np.asarray(im, np.float32); return a[..., 2::-1].copy(), a[..., 3:] / 255
HL, HA = handle(); HY = 1330

def frame(i):
    t = i / FPS
    f = atmos(base(t), t, i)
    if t < KEND: paste(f, KL, KA, 0, KY, min(1, (KEND - t) / 0.4))
    f = captions(f, t)
    paste(f, HL, HA, 0, HY, 0.9)
    if t > DUR - 0.5: f *= max(0, (DUR - t) / 0.5)
    return np.clip(f, 0, 255).astype(np.uint8)

if __name__ == '__main__':
    if len(sys.argv) > 1:
        for s in sys.argv[1:]: cv2.imwrite(D + f'p_{s}.png', cv2.resize(frame(int(float(s) * FPS)), (360, 640)))
        sys.exit()
    p = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                          '-i', SRC, '-map', '0:v', '-map', '1:a', '-shortest', '-c:v', 'libx264', '-crf', '20', '-maxrate', '7M',
                          '-bufsize', '14M', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart',
                          D + 'Kitaab_Likhunga_Reel.mp4'], stdin=subprocess.PIPE)
    for i in range(int(DUR * FPS)): p.stdin.write(frame(i).tobytes())
    p.stdin.close(); p.wait(); print('done')
