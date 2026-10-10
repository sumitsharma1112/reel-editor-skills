"""Reference-style lyric video: big Devanagari calligraphy words + small rounded roman words, appearing
one by one (blur -> sharp, small rise), over illustrated red/yellow Durga scenes with slow zoom."""
import math, subprocess, numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 1080, 1920, 30
DV = '/home/claude/reel-editor-skills/skills/reel-editor/fonts/deva/'
BIG = DV + 'amita-devanagari-700.ttf'
SMALL = '/home/claude/raft/lyric/fnt/quicksand-500.ttf'
DUR = 73.0
LAST = 69.0

NAVY = (30, 43, 87)
SC = {   # scene: anchor, big colour, small colour  (ChatGPT backgrounds, soft pastel skies)
    'cave': ((540, 470), NAVY, NAVY),
    'page': ((540, 430), NAVY, NAVY),
    'trishul': ((610, 380), NAVY, NAVY),
    'mountains': ((540, 470), NAVY, NAVY),
    'snow': ((540, 430), NAVY, NAVY),
    'garlands': ((540, 270), NAVY, NAVY),
    'wind': ((540, 430), NAVY, NAVY),
}
CHORUS1 = "गुफ़ा:D Suhani:r | Vich:r भवानी:D | Aap:r वसदी:D"
CHORUS2 = "माता:D Meri:r | Mata Meri:r सबदे:D | दिलां:D De Haal:r दसदी:D"
LINES = [  # start, end, scene, tokens  (timings from the user's SRT)
    (0.5, 6.0, 'cave', CHORUS1), (6.1, 13.2, 'page', CHORUS2),
    (13.3, 19.0, 'trishul', CHORUS1), (19.1, 26.5, 'cave', CHORUS2),
    (26.8, 32.4, 'mountains', "माँ:D Pahadan De:r | माँ:D पहाड़ां:D | Sohne:r नज़ारे:D"),
    (32.5, 36.4, 'mountains', "माँ:D Pahadan De:r | सोहणे:D नज़ारे:D"),
    (36.5, 40.0, 'snow', "किते:D बरफ़ां:D | Te Kite:r फुहारे:D"),
    (40.1, 43.4, 'snow', "Kite Barfan Te:r | किते:D फुहारे:D"),
    (43.5, 47.4, 'garlands', "Ho:r नच्चा:D Gava:r | Te Aunsiyan:r पावाँ:D"),
    (47.5, 50.9, 'garlands', "नच्चा:D Gava Te:r | Aunsiyan:r पावाँ:D"),
    (51.0, 54.3, 'wind', "दिल:D Moh Leya:r | ठंडियां:D | हवावां:D Ke:r"),
    (54.4, 59.3, 'cave', CHORUS1), (59.4, 66.5, 'page', CHORUS2),
    (66.6, DUR, 'trishul', "जय:D Mata Di:r"),
]

def syl(w):
    c = sum(1 for ch in w if 'क' <= ch <= 'ह' or 'ऄ' <= ch <= 'औ' or (ch.isascii() and ch.lower() in 'aeiou'))
    return max(1, c)

import sys as _s; _s.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from deva_kit import swash
def render_word(s, kind, col):
    if kind == 'D':
        fp = DV + 'yatra-one-devanagari-400.ttf' if 'च्च' in s else BIG     # Amita draws च्च like ज्ज
        size = 300 if fp == BIG else 260; ft = ImageFont.truetype(fp, size, layout_engine=ImageFont.Layout.RAQM)
        while ft.getlength(s) > 760: size -= 8; ft = ImageFont.truetype(fp, size, layout_engine=ImageFont.Layout.RAQM)
        b = ft.getbbox(s); p = 30
        im = Image.new('RGBA', (b[2] - b[0] + 2 * p, b[3] - b[1] + 2 * p))
        ImageDraw.Draw(im).text((p - b[0], p - b[1]), s, font=ft, fill=col)
        im = swash(im.crop(im.getbbox()), col + (255,), side='right', reach=0.28, drop=0.32, width=max(6, size // 22))
    else:                                                    # sketchy double-outline roman, like the reference
        size = 92; ft = ImageFont.truetype(SMALL, size)
        b = ft.getbbox(s); p = 20
        im = Image.new('RGBA', (b[2] - b[0] + 2 * p, b[3] - b[1] + 2 * p))
        for dx, dy in [(0, 0), (2, -2), (-1, 2)]:
            lay = Image.new('RGBA', im.size); d = ImageDraw.Draw(lay)
            d.text((p - b[0] + dx, p - b[1] + dy), s, font=ft, fill=col + (255,), stroke_width=2, stroke_fill=col + (255,))
            core = Image.new('L', im.size, 0); ImageDraw.Draw(core).text((p - b[0] + dx, p - b[1] + dy), s, font=ft, fill=255)
            core = core.filter(ImageFilter.MinFilter(3))
            a = np.array(lay.split()[3]).astype(np.int16) - np.array(core).astype(np.int16) * 0.85
            lay.putalpha(Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)))
            im.alpha_composite(lay)
    pad = Image.new('RGBA', (im.width + 40, im.height + 40)); pad.alpha_composite(im, (20, 20)); im = pad
    sh = Image.new('RGBA', im.size, (255, 255, 255, 0)); sh.putalpha(im.split()[3].point(lambda v: int(v * 0.35)))
    out = Image.new('RGBA', im.size); out.alpha_composite(sh.filter(ImageFilter.GaussianBlur(10))); out.alpha_composite(im)
    return np.array(out)

def layout(tokens, anchor, cb, cs, maxh=560):
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
    s = min(1.0, 1000 / (xs1 - xs0), maxh / (ys1 - ys0))
    cx, cy = (xs0 + xs1) / 2, (ys0 + ys1) / 2
    top = anchor[1] - (cy - ys0) * s
    shift = max(0, 190 - top)
    out = []
    for L, x, y in placed:
        if s < 1: L = cv2.resize(L, (int(L.shape[1] * s), int(L.shape[0] * s)), interpolation=cv2.INTER_AREA)
        out.append((L, anchor[0] + (x - cx) * s, anchor[1] + (y - cy) * s + shift))
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
    if not spec.strip(): continue
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
        SCREENS.append((tins, tout, scene, layout(scr, anchor, cb, cs, 380 if scene == 'garlands' else 540)))

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
    if SPANS and SPANS[-1][2] == scene and abs(SPANS[-1][1] - st) < 0.5: SPANS[-1][1] = en
    else: SPANS.append([st, en, scene])

SPANS[0][0] = 0.0
rng = np.random.default_rng(5)
DUST = np.stack([rng.uniform(0, W, 70), rng.uniform(0, H, 70), rng.uniform(1.5, 4, 70), rng.uniform(0.2, 0.9, 70)], 1)

def outro_layer():
    im = Image.new('RGBA', (W, 900)); d = ImageDraw.Draw(im)
    f1 = ImageFont.truetype(SMALL.replace('500', '700'), 62); f2 = ImageFont.truetype(SMALL.replace('500', '700'), 50)
    emo = ImageFont.truetype('/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf', 109)
    lines = [('Which song or', f1, NAVY), ('bhajan should I', f1, NAVY), ('make a caption', f1, NAVY),
             ('video for next?', f1, NAVY), ('', f2, None), ('Tell me in the', f2, NAVY), ('comments!', f2, NAVY)]
    y = 40
    for txt, ft, col in lines:
        if txt:
            w = ft.getlength(txt); d.text(((W - w) / 2, y), txt, font=ft, fill=col)
        y += 100 if ft is f1 else 60
    e = Image.new('RGBA', (140, 140)); ImageDraw.Draw(e).text((0, 0), '\U0001F447', font=emo, embedded_color=True)
    e = e.crop(e.getbbox()).resize((96, 96)); im.alpha_composite(e, ((W - 96) // 2, y + 70))
    sh = Image.new('RGBA', im.size, (0, 0, 0, 0)); sh.putalpha(im.split()[3].point(lambda v: int(v * 0.3)))
    out = Image.new('RGBA', im.size); out.alpha_composite(sh.filter(ImageFilter.GaussianBlur(9)), (0, 5)); out.alpha_composite(im)
    return np.array(out)
OUTRO = outro_layer()

def frame(t):
    k = max(i for i, s in enumerate(SPANS) if s[0] <= t + 1e-6)
    st, en, sc = SPANS[k]
    f = bg_frame(sc, t, st, en)
    if k > 0 and t - st < 0.45:                                  # crossfade from previous scene
        ps, pe, psc = SPANS[k - 1]; a = (t - st) / 0.45
        f = bg_frame(psc, t, ps, pe) * (1 - a) + f * a
    # golden dust / snow
    for x, y, r, sp in (DUST if sc == 'snow' else []):
        if sc == 'snow':
            yy = (y + t * 90 * sp) % H; xx = x + 25 * math.sin(t * sp + y); col = (255, 255, 255)
        else:
            yy = (y - t * 30 * sp) % H; xx = x + 15 * math.sin(t * sp * 2 + x); col = (120, 220, 255)
        cv2.circle(f, (int(xx), int(yy)), int(r), col, -1, cv2.LINE_AA) if sc == 'snow' else \
            cv2.circle(f, (int(xx), int(yy)), int(r * 0.7), (150, 225, 255), -1, cv2.LINE_AA)
    for tins, tout, sc2, placed in SCREENS:
        if t < tins[0] - 0.01 or t > tout + 0.6: continue
        fo = 1.0 if t <= tout else max(0, 1 - (t - tout) / 0.6)
        for (L, x, y), ti in zip(placed, tins):
            if t < ti: continue
            u = min(1, (t - ti) / 0.6); e = u * u * (3 - 2 * u)
            paste(f, L, x, y, e * fo)
    if t >= LAST + 0.3:
        u = min(1, (t - LAST - 0.3) / 0.5); e = 1 - (1 - u) ** 3
        paste(f, OUTRO, 240, 600, u * u * (3 - 2 * u))
    if t > DUR - 0.8: f = f * max(0, (DUR - t) / 0.8)
    return np.clip(f, 0, 255).astype(np.uint8)

if __name__ == '__main__':
    import sys, argparse
    if len(sys.argv) > 1 and sys.argv[1] == '--stills':
        for t in [float(x) for x in sys.argv[2:]]: cv2.imwrite(f'st_{t}.png', frame(t))
        sys.exit()
    AUDIO = sys.argv[sys.argv.index('--audio') + 1] if '--audio' in sys.argv else 'song.mp4'
    OUT = sys.argv[sys.argv.index('--out') + 1] if '--out' in sys.argv else 'lyric.mp4'
    n = int(DUR * FPS)
    pr = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                           '-ss', '0', '-i', AUDIO, '-map', '0:v', '-map', '1:a', '-t', f'{DUR}',
                           '-af', f'apad,afade=t=out:st={LAST - 0.5}:d=3.5,loudnorm=I=-14:TP=-1.5', '-c:v', 'libx264', '-crf', '20',
                           '-maxrate', '3M', '-bufsize', '6M', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k',
                           '-movflags', '+faststart', OUT], stdin=subprocess.PIPE)
    for i in range(n):
        pr.stdin.write(frame(i / FPS).tobytes())
    pr.stdin.close(); pr.wait(); print('done')
