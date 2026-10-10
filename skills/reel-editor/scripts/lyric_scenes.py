"""Lyric scenes (reference style): one screen = 1-3 words; big Devanagari calligraphy + small rounded roman
words, each fading in blur -> sharp with a small rise, over illustrated backgrounds with slow zoom/drift and
crossfades. Edit LINES (start, end, scene, "word:D word:r | next screen ...") and SC (anchor + colours).
Backgrounds: python devotional_backgrounds.py (writes bg_*.png in the current folder).
  python lyric_scenes.py --audio song.mp4 --out lyric.mp4

Original note: Reference-style lyric video: big Devanagari calligraphy words + small rounded roman words, appearing
one by one (blur -> sharp, small rise), over illustrated red/yellow Durga scenes with slow zoom."""
import math, subprocess, numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 1080, 1920, 30
import os
FD = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'fonts')
DV = os.path.join(FD, 'deva') + '/'
BIG = DV + 'amita-devanagari-700.ttf'
SMALL = os.path.join(FD, 'quicksand-500.ttf')
DUR = 67.6

SC = {   # scene: anchor, big colour, small colour
    'cave': ((540, 560), (255, 214, 90), (255, 241, 214)),
    'page': ((540, 760), (255, 207, 74), (255, 241, 214)),
    'trishul': ((540, 400), (255, 214, 90), (255, 241, 214)),
    'mountains': ((540, 600), (163, 18, 27), (122, 10, 18)),
    'snow': ((500, 1120), (255, 246, 224), (255, 255, 255)),
    'garlands': ((540, 920), (255, 207, 74), (255, 241, 214)),
    'wind': ((540, 520), (163, 18, 27), (122, 10, 18)),
}
CHORUS1 = "गुफ़ा:D Suhani:r | Vich:r भवानी:D | Aap:r वसदी:D"
CHORUS2 = "माता:D Meri:r | Mata Meri:r संगतां:D Nu:r | दिल:D De Haal:r दसदी:D"
LINES = [  # start, end, scene, tokens
    (0.0, 6.5, 'cave', CHORUS1), (6.5, 13.0, 'page', CHORUS2),
    (13.0, 19.6, 'trishul', CHORUS1), (19.6, 26.3, 'cave', CHORUS2),
    (26.3, 29.6, 'mountains', "माँ:D Pahadan De:r | माँ:D पहाड़ां:D | Sohne:r नज़ारे:D"),
    (29.6, 32.8, 'mountains', "पहाड़ां:D Sohne Nazare:r"),
    (32.8, 36.0, 'snow', "किते:D बरफ़ां:D | Kite:r फुहारे:D"),
    (36.0, 39.3, 'snow', "Kite Barfan:r फुहारे:D"),
    (39.3, 42.5, 'garlands', "नच्चां:D Gavan:r | Aundiyan:r मावां:D"),
    (42.5, 45.8, 'garlands', "Nachan Gavan:r मावां:D"),
    (45.8, 52.3, 'wind', "दिल:D Moh Leya:r | ठंडियां:D | हवावां:D Ke...:r"),
    (52.3, 58.8, 'cave', CHORUS1), (58.8, 65.4, 'page', CHORUS2),
    (65.4, DUR, 'trishul', "जय:D Mata Di:r"),
]

def syl(w):
    c = sum(1 for ch in w if 'क' <= ch <= 'ह' or 'ऄ' <= ch <= 'औ' or (ch.isascii() and ch.lower() in 'aeiou'))
    return max(1, c)

def render_word(s, kind, col):
    if kind == 'D':
        fp = DV + 'yatra-one-devanagari-400.ttf' if 'च्च' in s else BIG     # Amita draws च्च like ज्ज
        size = 310 if fp == BIG else 270; ft = ImageFont.truetype(fp, size, layout_engine=ImageFont.Layout.RAQM)
        while ft.getlength(s) > 900: size -= 8; ft = ImageFont.truetype(fp, size, layout_engine=ImageFont.Layout.RAQM)
    else:
        size = 86; ft = ImageFont.truetype(SMALL, size)
    b = ft.getbbox(s); p = 40
    im = Image.new('RGBA', (b[2] - b[0] + 2 * p, b[3] - b[1] + 2 * p))
    ImageDraw.Draw(im).text((p - b[0], p - b[1]), s, font=ft, fill=col)
    sh = Image.new('RGBA', im.size, (0, 0, 0, 0)); sh.putalpha(im.split()[3].point(lambda v: int(v * 0.28)))
    out = Image.new('RGBA', im.size); out.alpha_composite(sh.filter(ImageFilter.GaussianBlur(9)), (0, 5)); out.alpha_composite(im)
    return np.array(out)

def layout(tokens, anchor, cb, cs):
    """returns list of (layer, x, y) relative to frame, in token order"""
    items = [(t, k, render_word(t, k, cb if k == 'D' else cs)) for t, k in tokens]
    placed = []; y = 0; row = -1; lead = []; last = None
    for t, k, L in items:
        h, w = L.shape[:2]
        if k == 'D':
            row += 1; off = [-50, 70, -20][row % 3]
            x = off - w / 2
            yy = y if last is None else y - 40
            placed.append([L, x, yy]); last = placed[-1]; y = yy + h - 70
            for Ls in lead:                                   # leading small words sit above-left of this big word
                Ls[1] = x + 30; Ls[2] = yy - Ls[0].shape[0] + 40
            lead = []
        else:
            if last is None:
                placed.append([L, 0, 0]); lead.append(placed[-1])
            else:
                lx, ly = last[1] + last[0].shape[1] - 50, last[2] + last[0].shape[0] * 0.18
                if lx + w > 520:
                    lx, ly = last[1] + last[0].shape[1] * 0.5 - w / 2, last[2] + last[0].shape[0] - 70
                    y = ly + h - 10                                    # next big word goes below this one
                placed.append([L, lx, ly])
    if lead and last is None:                                   # only small words on this screen
        x = -sum(p[0].shape[1] for p in lead) / 2
        for p in lead: p[1] = x; p[2] = 0; x += p[0].shape[1] - 40
    xs0 = min(p[1] for p in placed); xs1 = max(p[1] + p[0].shape[1] for p in placed)
    ys0 = min(p[2] for p in placed); ys1 = max(p[2] + p[0].shape[0] for p in placed)
    s = min(1.0, 1000 / (xs1 - xs0))
    cx, cy = (xs0 + xs1) / 2, (ys0 + ys1) / 2
    out = []
    for L, x, y in placed:
        if s < 1: L = cv2.resize(L, (int(L.shape[1] * s), int(L.shape[0] * s)), interpolation=cv2.INTER_AREA)
        out.append((L, anchor[0] + (x - cx) * s, anchor[1] + (y - cy) * s))
    return out

def paste(f, L, x, y, a):
    if a <= 0.003: return
    h, w = L.shape[:2]; x0, y0 = int(x), int(y)
    xa, ya, xb, yb = max(0, x0), max(0, y0), min(W, x0 + w), min(H, y0 + h)
    if xa >= xb or ya >= yb: return
    l = L[ya - y0:yb - y0, xa - x0:xb - x0].astype(np.float32); al = l[..., 3:4] / 255 * a
    f[ya:yb, xa:xb] = f[ya:yb, xa:xb] * (1 - al) + l[..., 2::-1] * al

# ---------------- build the timeline of screens
SCREENS = []          # (t_in_list, t_out, scene, placed)
for st, en, scene, spec in LINES:
    anchor, cb, cs = SC[scene]
    import re
    screens = [[(w.strip(), k) for w, k in re.findall(r'(\S.*?):([Dr])(?=\s|$)', part.strip())] for part in spec.split('|')]
    # tokens can contain spaces in roman phrases written with spaces -> re-join small consecutive words
    fixed = []
    for scr in screens:
        out = []
        for w, k in scr:
            out.append((w, k))
        fixed.append(out)
    allt = [tk for scr in fixed for tk in scr]
    weights = [syl(w) for w, _ in allt]; tot = sum(weights)
    a0, a1 = st + 0.12, en - 0.45
    times = []; acc = 0
    for wt in weights: times.append(a0 + (a1 - a0) * acc / tot); acc += wt
    i = 0
    for si, scr in enumerate(fixed):
        tins = times[i:i + len(scr)]; i += len(scr)
        tout = times[i] - 0.05 if i < len(times) else en
        SCREENS.append((tins, tout, scene, layout(scr, anchor, cb, cs)))

BG = {k: cv2.imread(f'bg_{k}.png') for k in SC}
def bg_frame(scene, t, t0, t1):
    img = BG[scene]; u = (t - t0) / max(0.1, (t1 - t0))
    z = 1.0 + 0.05 * u; hh, ww = img.shape[:2]
    cw, ch = int(W * 1.1 / z), int(H * 1.1 / z)
    x0 = int((ww - cw) / 2 + 20 * math.sin(u * 2)); y0 = int((hh - ch) / 2)
    return cv2.resize(img[y0:y0 + ch, x0:x0 + cw], (W, H), interpolation=cv2.INTER_LINEAR).astype(np.float32)

# scene spans (merge consecutive lines with the same scene)
SPANS = []
for st, en, scene, _ in LINES:
    if SPANS and SPANS[-1][2] == scene and abs(SPANS[-1][1] - st) < 0.01: SPANS[-1][1] = en
    else: SPANS.append([st, en, scene])

rng = np.random.default_rng(5)
DUST = np.stack([rng.uniform(0, W, 70), rng.uniform(0, H, 70), rng.uniform(1.5, 4, 70), rng.uniform(0.2, 0.9, 70)], 1)

def frame(t):
    k = max(i for i, s in enumerate(SPANS) if s[0] <= t + 1e-6)
    st, en, sc = SPANS[k]
    f = bg_frame(sc, t, st, en)
    if k > 0 and t - st < 0.45:                                  # crossfade from previous scene
        ps, pe, psc = SPANS[k - 1]; a = (t - st) / 0.45
        f = bg_frame(psc, t, ps, pe) * (1 - a) + f * a
    # golden dust / snow
    for x, y, r, sp in DUST:
        if sc == 'snow':
            yy = (y + t * 90 * sp) % H; xx = x + 25 * math.sin(t * sp + y); col = (255, 255, 255)
        else:
            yy = (y - t * 30 * sp) % H; xx = x + 15 * math.sin(t * sp * 2 + x); col = (120, 220, 255)
        cv2.circle(f, (int(xx), int(yy)), int(r), col, -1, cv2.LINE_AA) if sc == 'snow' else \
            cv2.circle(f, (int(xx), int(yy)), int(r * 0.7), (150, 225, 255), -1, cv2.LINE_AA)
    for tins, tout, sc2, placed in SCREENS:
        if t < tins[0] - 0.01 or t > tout + 0.3: continue
        fo = 1.0 if t <= tout else max(0, 1 - (t - tout) / 0.3)
        for (L, x, y), ti in zip(placed, tins):
            if t < ti: continue
            u = min(1, (t - ti) / 0.4); e = 1 - (1 - u) ** 3
            Lb = L if u >= 1 else cv2.GaussianBlur(L, (0, 0), 0.1 + 10 * (1 - e))
            dy = 26 * (1 - e) - (12 * (1 - fo))
            paste(f, Lb, x, y + dy, e * fo)
    if t > DUR - 1.2: f = f * max(0, (DUR - t) / 1.2)
    return np.clip(f, 0, 255).astype(np.uint8)

if __name__ == '__main__':
    import sys
    import argparse
    if len(sys.argv) > 1 and sys.argv[1] == '--stills':
        for t in [float(x) for x in sys.argv[2:]]: cv2.imwrite(f'st_{t}.png', frame(t))
        sys.exit()
    ap = argparse.ArgumentParser(); ap.add_argument('--audio', default='att.mp4'); ap.add_argument('--out', default='lyric.mp4')
    a = ap.parse_args()
    n = int(DUR * FPS)
    pr = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                           '-ss', '0', '-i', a.audio, '-map', '0:v', '-map', '1:a', '-t', f'{DUR}',
                           '-af', f'afade=t=out:st={DUR - 1.5}:d=1.5,loudnorm=I=-14:TP=-1.5', '-c:v', 'libx264', '-crf', '20',
                           '-maxrate', '3M', '-bufsize', '6M', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k',
                           '-movflags', '+faststart', a.out], stdin=subprocess.PIPE)
    for i in range(n):
        pr.stdin.write(frame(i / FPS).tobytes())
    pr.stdin.close(); pr.wait(); print('done')
