"""Mahakal — Bam Lahiri format: 24 full-frame 9:16 living paintings, slow intro (one image per half-line),
flash cuts on the MAHAKAL drop, then ONE IMAGE PER SANSKRIT WORD (current word glows saffron in the tiny centred
Devanagari line), masked flow + particles + fire flicker, @aitricksbysumit top-left."""
import numpy as np, cv2, subprocess, sys, math, os
from PIL import Image, ImageDraw, ImageFont, ImageFilter
os.environ.setdefault('U2NET_HOME', '/root/.rembg/models/u2net')
D = '/home/claude/raft/mahakal/'
SRC = '/root/.claude/uploads/7e7fbd2a-05f7-5789-85d7-a95bbba90e41/9e979846-Video-30296.mp4'
FD = '/home/claude/reel-editor-skills/skills/reel-editor/fonts/'
W, H, FPS = 1080, 1920, 30
MW, MH = int(W * 1.12), int(H * 1.12)
DUR = 24.26
rng = np.random.default_rng(7)

L1, L2, L3, L4 = 'कर्ता करे न कर सके', 'शिव करे सो होय', 'तीनों लोक नौ खंड में', 'महाकाल से बड़ा न कोय'
G = ['गंगवार', 'चंडधार', 'मंडियं', 'मयादियांग']
B = ['भालचंद्र', 'दिप्त', 'लाल', 'ज्वालियम्']
K = ['कंकणं', 'भुजंग', 'मौलि', 'मालियम्']
# (start, image, line-words, highlighted word index or None, flow, particles, mode)  mode: dip | flash | cut
SEG = [
 (0.00, 1, [L1], None, 'swirl', 'snow', 'dip'),
 (1.44, 2, [L1], None, 'swirl', 'spray', 'dip'),
 (3.04, 3, [L2], None, None, 'motes', 'dip'),
 (4.31, 4, [L2], None, 'up', 'motes', 'dip'),
 (5.60, 5, [L3], None, 'swirl', 'motes', 'dip'),
 (6.87, 6, [L3], None, 'swirl', 'snow', 'dip'),
 (8.14, 7, [L4], None, None, 'embers', 'dip'),
 (9.09, 8, [L4], None, 'swirl', 'motes', 'dip'),
 (10.30, 9, ['महाकाल'], None, 'swirl', 'embers', 'flash'),
 (11.25, 10, ['महाकाल'], None, 'up', 'embers', 'flash'),
 (12.54, 11, ['महाकाल'], None, 'swirl', 'embers', 'flash'),
 (13.40, 12, ['महाकाल'], None, 'up', 'embers', 'flash'),
 (14.07, 13, G, 0, 'up', 'spray', 'flash'),
 (14.87, 14, G, 1, 'up', 'spray', 'cut'),
 (15.74, 15, G, 2, 'up', 'spray', 'cut'),
 (16.60, 16, G, 3, 'swirl', 'motes', 'cut'),
 (17.44, 17, B, 0, None, 'snow', 'flash'),
 (18.22, 18, B, 1, 'swirl', 'motes', 'cut'),
 (18.88, 19, B, 2, None, 'embers', 'cut'),
 (19.69, 20, B, 3, 'up', 'embers', 'cut'),
 (20.56, 21, K, 0, None, 'motes', 'flash'),
 (21.54, 22, K, 1, 'swirl', 'motes', 'cut'),
 (22.21, 23, K, 2, 'swirl', 'motes', 'cut'),
 (23.23, 24, K, 3, 'swirl', 'embers', 'cut'),
]

def load(n):
    im = cv2.imread(D + f'img/{n:02d}.png'); h, w = im.shape[:2]
    ch = int(w * H / W)
    if ch <= h: y0 = (h - ch) // 2; crop = im[y0:y0 + ch]
    else: cw = int(h * W / H); x0 = (w - cw) // 2; crop = im[:, x0:x0 + cw]
    img = cv2.resize(crop, (MW, MH), interpolation=cv2.INTER_LANCZOS4).astype(np.float32)
    mp = D + f'm_{n:02d}.png'
    if not os.path.exists(mp):
        from rembg import remove, new_session
        remove(Image.fromarray(cv2.cvtColor(crop, cv2.COLOR_BGR2RGB)), session=new_session('u2net'), only_mask=True).save(mp)
    m = cv2.resize(cv2.imread(mp, 0), (MW, MH)).astype(np.float32) / 255
    return img, cv2.GaussianBlur(np.clip(m * 1.4, 0, 1), (0, 0), 10)

def smooth_noise(sh, s):
    n = cv2.GaussianBlur(rng.normal(0, 1, sh).astype(np.float32), (0, 0), s); return n / n.std()
PAD = 800
NX, NY = smooth_noise((MH + PAD, MW + PAD), 45), smooth_noise((MH + PAD, MW + PAD), 45)
yy, xx = np.mgrid[0:MH, 0:MW].astype(np.float32)
PN = 90
PX, PY = rng.uniform(0, MW, PN), rng.uniform(0, MH, PN); PS = rng.uniform(0.5, 1.5, PN); PP = rng.uniform(0, 6.3, PN)
PCOL = {'motes': (140, 215, 255), 'embers': (40, 140, 255), 'snow': (255, 250, 245), 'spray': (240, 240, 230)}

def particles(t, kind):
    L = np.zeros((MH // 2, MW // 2), np.float32)
    for x, y, s, p in zip(PX, PY, PS, PP):
        if kind == 'snow': px, py, r = x + 30 * math.sin(t * 0.8 + p), (y + t * 90 * s) % MH, 2 + 2 * s
        elif kind == 'embers': px, py, r = x + 25 * math.sin(t * 1.5 + p), (y - t * 160 * s) % MH, 1.5 + 1.5 * s
        elif kind == 'spray': px, py, r = x + 20 * math.sin(t + p), (y + t * 260 * s) % MH, 1 + s
        else: px, py, r = x + 20 * math.sin(t * 0.6 + p), (y - t * 35 * s) % MH, 1.5 + 1.5 * s
        cv2.circle(L, (int(px / 2), int(py / 2)), max(1, int(round(r / 2))), 0.5 + 0.5 * math.sin(t * 3 + p * 2), -1, cv2.LINE_AA)
    return cv2.resize(cv2.GaussianBlur(L, (0, 0), 0.8), (MW, MH))

CACHE = {}
def assets(k):
    if k not in CACHE: CACHE.clear(); CACHE[k] = load(SEG[k][1])
    return CACHE[k]

def card(k, t):
    st, n, words, hi, flow, pk, mode = SEG[k]; en = SEG[k + 1][0] if k + 1 < len(SEG) else DUR
    img, m = assets(k); lt = t - st; u = lt / (en - st)
    if flow:
        a = int(lt * 30)
        if flow == 'up': dx = NX[PAD - a:PAD - a + MH, 100:100 + MW] * 4; dy = NY[PAD - a:PAD - a + MH, 100:100 + MW] * 8
        else: dx = NX[a:a + MH, a // 2:a // 2 + MW] * 7; dy = NY[a:a + MH, a // 2:a // 2 + MW] * 7
        f = cv2.remap(img, xx + dx * (1 - m), yy + dy * (1 - m), cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    else: f = img.copy()
    warm = np.clip((f[..., 2] - f[..., 0] - 60) / 120, 0, 1)            # fire / third-eye flicker
    fl = 1 + 0.12 * math.sin(lt * 17) + 0.07 * math.sin(lt * 29 + 1)
    f = f * (1 + (fl - 1) * warm[..., None])
    P = particles(t, pk); c = np.array(PCOL[pk], np.float32)
    f = f * (1 - P[..., None] * 0.6) + c * P[..., None] + c * cv2.GaussianBlur(P, (0, 0), 4)[..., None] * 0.6
    fast = mode != 'dip'
    z = (1.0 + (0.10 if not fast else 0.07) * u) if k % 2 == 0 else (1.10 - 0.08 * u)
    z *= 1 + (0.09 if fast else 0.035) * max(0, 1 - lt / (0.2 if fast else 0.35))  # entry punch
    cw, ch = W / z, H / z; cx = MW / 2 + 20 * (u - 0.5) * (1 if k % 3 else -1); cy = MH / 2
    s_ = W / cw; M = np.float32([[s_, 0, -(cx - cw / 2) * s_], [0, s_, -(cy - ch / 2) * s_]])
    out = cv2.warpAffine(f, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    if mode == 'dip':
        dip = min(1, (en - t) / 0.15) if k == 0 else min(1, lt / 0.15, (en - t) / 0.15)
        out *= max(0, dip)
    elif mode == 'flash' and lt < 0.12: out = out + 170 * (1 - lt / 0.12)
    elif lt < 0.05: out = out + 70 * (1 - lt / 0.05)
    return out, words, hi, lt

def handle():
    im = Image.new('RGBA', (W, 60)); f = ImageFont.truetype(FD + 'montserrat-700.ttf', 27)
    sh = Image.new('RGBA', im.size); ImageDraw.Draw(sh).text((56, 12), '@aitricksbysumit', font=f, fill=(0, 0, 0, 200), stroke_width=4, stroke_fill=(0, 0, 0, 200))
    im = Image.alpha_composite(im, sh.filter(ImageFilter.GaussianBlur(5))); d = ImageDraw.Draw(im)
    d.rectangle((40, 11, 45, 43), fill=(255, 120, 30, 235)); d.text((56, 12), '@aitricksbysumit', font=f, fill=(255, 255, 255, 230))
    a = np.asarray(im, np.float32); return a[..., [2, 1, 0]], a[..., 3:] / 255
HD, HA = handle(); HY = 460

_cf = ImageFont.truetype(FD + 'deva/baloo-2-devanagari-600.ttf', 46); _cc = {}
def cap_layer(words, hi):
    key = (tuple(words), hi)
    if key not in _cc:
        im = Image.new('RGBA', (W, 140)); d = ImageDraw.Draw(im); sp = d.textlength(' ', font=_cf)
        ws = [d.textlength(w, font=_cf) for w in words]; x = (W - sum(ws) - sp * (len(words) - 1)) / 2
        sh = Image.new('RGBA', im.size); ds = ImageDraw.Draw(sh); xs = []
        for w, wl in zip(words, ws): ds.text((x, 40), w, font=_cf, fill=(0, 0, 0, 230), stroke_width=7, stroke_fill=(0, 0, 0, 230)); xs.append(x); x += wl + sp
        im = Image.alpha_composite(sh.filter(ImageFilter.GaussianBlur(7)), im); d = ImageDraw.Draw(im)
        if hi is not None:                                               # saffron glow behind the sung word
            gl = Image.new('RGBA', im.size); ImageDraw.Draw(gl).text((xs[hi], 40), words[hi], font=_cf, fill=(255, 140, 20, 255), stroke_width=6, stroke_fill=(255, 140, 20, 255))
            im = Image.alpha_composite(im, gl.filter(ImageFilter.GaussianBlur(10))); d = ImageDraw.Draw(im)
        for j, (w, x0) in enumerate(zip(words, xs)):
            d.text((x0, 40), w, font=_cf, fill=(255, 214, 120, 255) if j == hi else (255, 255, 255, 255 if hi is None else 200))
        a = np.asarray(im, np.float32); _cc[key] = (a[..., [2, 1, 0]], a[..., 3:] / 255)
    return _cc[key]
CAP_Y = int(H * 0.60)

def frame(i):
    t = i / FPS
    k = max(j for j, s in enumerate(SEG) if s[0] <= t)
    fr, words, hi, lt = card(k, t)
    L, A = cap_layer(words, hi)
    same = k == 0 or SEG[k - 1][2] == words
    a = A if same else A * min(1, lt / 0.15)
    fr[CAP_Y:CAP_Y + 140] = fr[CAP_Y:CAP_Y + 140] * (1 - a) + L * a
    fr[HY:HY + 60] = fr[HY:HY + 60] * (1 - HA) + HD * HA
    if t > DUR - 0.4: fr *= max(0, (DUR - t) / 0.4)
    return np.clip(fr, 0, 255).astype(np.uint8)

if __name__ == '__main__':
    for s in SEG: load(s[1])
    if len(sys.argv) > 1:
        for s in sys.argv[1:]: cv2.imwrite(D + f'p_{s}.png', cv2.resize(frame(int(float(s) * FPS)), (360, 640)))
        sys.exit()
    p = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                          '-i', SRC, '-map', '0:v', '-map', '1:a', '-shortest', '-c:v', 'libx264', '-crf', '20', '-maxrate', '8M',
                          '-bufsize', '16M', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart',
                          D + 'Mahakal_Bam_Lahiri_Style.mp4'], stdin=subprocess.PIPE)
    for i in range(int(DUR * FPS)): p.stdin.write(frame(i).tobytes())
    p.stdin.close(); p.wait(); print('done')
