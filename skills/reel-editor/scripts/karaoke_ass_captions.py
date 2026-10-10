"""Karaoke caption video from a word-timed ASS file (phonetic stretch: Prem ka raaaaang).
Parse the ASS (Lyric events with the active word in the accent colour, Preview events = next line) to
events.json, then render: warm black velvet bg + breathing light + drifting gold dust + soft bokeh,
Cormorant Garamond Bold Italic, sung words ivory, upcoming words 47% alpha, active word gold with double
glow and a 10% pop for 0.22 s, next line small below. Output silent MP4 (add the song in-app).

Original: Sansoon Ki Mala – phonetic-stretch karaoke caption video (timings from the user's ASS file)."""
import json, math, subprocess, numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 1080, 1920, 30
DUR = 47.0
F_BIG = __import__('os').path.join(__import__('os').path.dirname(__file__), '..', 'fonts', 'cormorant-700i.ttf')
F_SMALL = __import__('os').path.join(__import__('os').path.dirname(__file__), '..', 'fonts', 'cormorant-600i.ttf')
GOLD = (242, 196, 109); IVORY = (250, 242, 226); DIM = (250, 242, 226)
ev = json.load(open('events.json'))
LY = [e for e in ev if e['k'] == 'lyr']; PV = [e for e in ev if e['k'] == 'prev']
rng = np.random.default_rng(3)

# ---------- background: warm black velvet, breathing light, drifting gold dust
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
base = np.zeros((H, W, 3), np.float32)
r = np.sqrt(((xx - W / 2) / W) ** 2 + ((yy - H * 0.5) / H) ** 2)
glow = np.exp(-(r / 0.36) ** 2)[..., None]
BG0 = np.array([8, 5, 6], np.float32); BG1 = np.array([92, 44, 14], np.float32)   # RGB
NP = 140
dust = np.stack([rng.uniform(0, W, NP), rng.uniform(0, H, NP), rng.uniform(1.5, 5.5, NP),
                 rng.uniform(8, 28, NP), rng.uniform(0, 6.28, NP)], 1)

def background(t):
    b = 0.85 + 0.15 * math.sin(t * 0.9)
    img = BG0 + (BG1 - BG0) * glow * b
    img = img.copy()
    for x, y, s, sp, ph in dust:
        yy_ = (y - t * sp) % (H + 40) - 20; xx_ = x + 18 * math.sin(t * 0.4 + ph)
        a = 0.35 + 0.35 * math.sin(t * 1.7 + ph)
        cv2.circle(img, (int(xx_), int(yy_)), int(s), (242 * a, 196 * a, 109 * a), -1, cv2.LINE_AA)
    for k in range(7):                                  # big soft bokeh
        bx = (0.15 + 0.12 * k) * W + 60 * math.sin(t * 0.3 + k); by = (H * (0.2 + 0.1 * (k % 6)) - t * 12 * (1 + k % 3)) % H
        cv2.circle(BOK, (int(bx), int(by)), 60 + 12 * (k % 3), 1, -1, cv2.LINE_AA)
    bk = cv2.GaussianBlur(BOK, (0, 0), 18); BOK[:] = 0
    img += bk[..., None] * np.array([242, 170, 80], np.float32) * 0.22
    return img
BOK = np.zeros((H, W), np.float32)

# ---------- text
_fc = {}
def font(path, size):
    k = (path, size)
    if k not in _fc: _fc[k] = ImageFont.truetype(path, size)
    return _fc[k]

def line_layout(words, size):
    ft = font(F_BIG, size); sp = ft.getlength(' ')
    ws = [ft.getlength(w['w']) for w in words]
    return ft, ws, sp

def fit_lines(words, size0, maxw=960):
    """greedy wrap into <=2 lines, shrink until it fits"""
    size = size0
    while True:
        ft, ws, sp = line_layout(words, size)
        lines, cur, cw = [], [], 0
        for i, w in enumerate(ws):
            if cur and cw + sp + w > maxw: lines.append(cur); cur, cw = [], 0
            cw = cw + (sp if cur else 0) + w; cur.append(i)
        lines.append(cur)
        if (len(lines) <= 3 and all(sum(ws[i] for i in l) + sp * (len(l) - 1) <= maxw for l in lines)) or size < 50:
            return ft, ws, sp, lines, size
        size -= 4

def draw_words(words, size0, act_age, alpha):
    ft, ws, sp, lines, size = fit_lines(words, size0)
    lh = int(size * 1.12); tot = lh * len(lines)
    lay = Image.new('RGBA', (W, tot + 200)); d = ImageDraw.Draw(lay)
    glow_l = Image.new('RGBA', lay.size); g = ImageDraw.Draw(glow_l)
    act_box = None
    for li, l in enumerate(lines):
        lw = sum(ws[i] for i in l) + sp * (len(l) - 1); x = (W - lw) / 2; y = 100 + li * lh
        for i in l:
            w = words[i]
            if w['active']:
                col = GOLD + (255,); g.text((x, y), w['w'], font=ft, fill=GOLD + (255,)); act_box = (x, y, ws[i])
            elif w['sung']:
                col = IVORY + (255,)
            else:
                col = DIM + (120,)
            d.text((x, y), w['w'], font=ft, fill=col)
            x += ws[i] + sp
    out = Image.new('RGBA', lay.size)
    out.alpha_composite(glow_l.filter(ImageFilter.GaussianBlur(26))); out.alpha_composite(glow_l.filter(ImageFilter.GaussianBlur(26)))
    out.alpha_composite(glow_l.filter(ImageFilter.GaussianBlur(8)))
    out.alpha_composite(lay)
    a = np.array(out).astype(np.float32); a[..., 3] *= alpha
    # pop: active word slightly bigger for the first 0.18 s
    return a, tot, act_box, size

def comp(img, L, y0):
    h = L.shape[0]; ya, yb = max(0, y0), min(H, y0 + h)
    if yb <= ya: return
    l = L[ya - y0:yb - y0]; al = l[..., 3:4] / 255
    img[ya:yb] = img[ya:yb] * (1 - al) + l[..., :3] * al

def small(text, alpha):
    ft = font(F_SMALL, 60); b = ft.getbbox(text); im = Image.new('RGBA', (W, b[3] + 40))
    ImageDraw.Draw(im).text(((W - ft.getlength(text)) / 2, 10), text, font=ft, fill=IVORY + (int(120 * alpha),))
    return np.array(im).astype(np.float32)

def scale_at(L, cx, cy, s):
    if abs(s - 1) < 0.004: return L
    M = cv2.getRotationMatrix2D((cx, cy), 0, s)
    return cv2.warpAffine(L, M, (L.shape[1], L.shape[0]), flags=cv2.INTER_LINEAR)

def frame(t):
    img = background(t)
    e = next((e for e in LY if e['st'] <= t < e['en']), None)
    if e is not None:
        # fade in/out from \fad
        a = 1.0
        if e['fad']:
            fi, fo = e['fad'][0] / 1000, e['fad'][1] / 1000
            if fi: a = min(a, (t - e['st']) / fi)
            if fo: a = min(a, (e['en'] - t) / fo)
        # age of the currently active word (for the pop)
        ai = next((i for i, w in enumerate(e['words']) if w['active']), None)
        age = 1.0
        if ai is not None:
            t0 = e['st']
            for p in reversed(LY[:LY.index(e)]):
                pi = next((i for i, w in enumerate(p['words']) if w['active']), None)
                if pi != ai or len(p['words']) != len(e['words']): break
                t0 = p['st']
            age = t - t0
        L, tot, box, size = draw_words(e['words'], int(e['fs'] * 2.6), age, max(0, min(1, a)))
        if box is not None and age < 0.22:
            s = 1 + 0.10 * math.sin(math.pi * min(1, age / 0.22))
            L = scale_at(L, box[0] + box[2] / 2, box[1] + size * 0.6, s)
        y0 = int(H * 0.47 - tot / 2) - 100
        comp(img, L, y0)
        p = next((p for p in PV if p['st'] <= t < p['en']), None)
        if p is not None:
            pa = min(1, (t - p['st']) / 0.2, (p['en'] - t) / 0.15)
            comp(img, small(p['text'], max(0, pa)), y0 + 100 + tot + 60)
    # soft vignette + film grain
    img = img * (1 - 0.35 * np.clip(r * 1.6 - 0.2, 0, 1))[..., None]
    img += rng.normal(0, 3.5, (H // 4, W // 4, 1)).repeat(4, 0).repeat(4, 1)
    return np.clip(img, 0, 255).astype(np.uint8)

if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        for t in map(float, sys.argv[1:]): cv2.imwrite(f'st_{t}.png', cv2.cvtColor(frame(t), cv2.COLOR_RGB2BGR))
        sys.exit()
    pr = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                           '-f', 'lavfi', '-i', 'anullsrc=r=44100:cl=stereo', '-shortest', '-c:v', 'libx264', '-crf', '20', '-maxrate', '4M',
                           '-bufsize', '8M', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-movflags', '+faststart',
                           'karaoke_captions.mp4'], stdin=subprocess.PIPE)
    for i in range(int(DUR * FPS)):
        pr.stdin.write(frame(i / FPS).tobytes())
    pr.stdin.close(); pr.wait(); print('done')
