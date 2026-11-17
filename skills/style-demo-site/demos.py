"""Trending reel-style demos (540x960, 30fps, 8s) with the AI avatar.
Usage: python3 demos.py [style ...]   -> media/<style>.mp4 + .jpg poster
"""
import sys, math, subprocess, os, random
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS, DUR = 540, 960, 30, 8.0
N = int(FPS * DUR)
OUT = os.path.join(os.path.dirname(__file__), 'site', 'media')
os.makedirs(OUT, exist_ok=True)
FD = '/root/.claude/skills/reel-effects-55/fonts/'
A = '/home/claude/intro/assets/'

def font(name, size, var=None):
    p = {'anton': FD + 'Anton-Regular.ttf', 'mont': FD + 'Montserrat.ttf',
         'play': FD + 'PlayfairDisplay.ttf', 'playi': FD + 'PlayfairDisplay-Italic.ttf',
         'archivo': FD + 'ArchivoBlack-Regular.ttf', 'iseri': FD + 'InstrumentSerif-Italic.ttf',
         'kaushan': '/home/claude/amrita/fonts/KaushanScript-Regular.ttf',
         'bebas': '/home/claude/reel-editor-skills/skills/reel-editor/fonts/bebas-neue-400.ttf'}[name]
    f = ImageFont.truetype(p, size)
    if var:
        try: f.set_variation_by_name(var)
        except Exception: pass
    return f

def ease(t): t = max(0, min(1, t)); return 1 - (1 - t) ** 3
def back(t):
    t = max(0, min(1, t)); c = 1.7; return 1 + (c + 1) * (t - 1) ** 3 + c * (t - 1) ** 2

_av = {}
def avatar(name, h):
    k = (name, h)
    if k not in _av:
        im = Image.open(A + name if '/' not in name else name).convert('RGBA')
        im = im.crop(im.getbbox())
        _av[k] = im.resize((int(im.width * h / im.height), h), Image.LANCZOS)
    return _av[k]

def paste_avatar(img, name, h, cx, bottom, scale=1.0, dy=0):
    a = avatar(name, h)
    if scale != 1.0:
        a = a.resize((int(a.width * scale), int(a.height * scale)), Image.LANCZOS)
    img.alpha_composite(a, (int(cx - a.width / 2), int(bottom - a.height + dy)))

def bg(name, blur=0, dark=0.0):
    im = Image.open(A + name).convert('RGB').resize((W, H), Image.LANCZOS)
    if blur: im = im.filter(ImageFilter.GaussianBlur(blur))
    if dark: im = Image.blend(im, Image.new('RGB', (W, H), 'black'), dark)
    return im.convert('RGBA')

def grad(c1, c2):
    y = np.linspace(0, 1, H)[:, None, None]
    arr = (np.array(c1) * (1 - y) + np.array(c2) * y) * np.ones((1, W, 1))
    return Image.fromarray(arr.astype('uint8')).convert('RGBA')

def text_layer(txt, f, fill, anchor_xy, anchor='mm', glow=None, glow_r=10, stroke=0, stroke_fill=None, alpha=255):
    L = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(L)
    d.text(anchor_xy, txt, font=f, fill=fill, anchor=anchor, stroke_width=stroke, stroke_fill=stroke_fill)
    if glow:
        G = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(G).text(anchor_xy, txt, font=f, fill=glow, anchor=anchor, stroke_width=stroke + 3, stroke_fill=glow)
        G = G.filter(ImageFilter.GaussianBlur(glow_r)); G.alpha_composite(L); L = G
    if alpha < 255:
        a = np.array(L); a[..., 3] = (a[..., 3] * (alpha / 255)).astype('uint8'); L = Image.fromarray(a)
    return L

def tag(img, label):
    """small corner label: style name"""
    d = ImageDraw.Draw(img); f = font('mont', 18, 'Bold')
    w = d.textlength(label, font=f)
    d.rounded_rectangle((16, 16, 16 + w + 24, 50), 17, fill=(0, 0, 0, 150))
    d.text((28, 33), label, font=f, fill='white', anchor='lm')

def frosted(base, box, r=22, tint=(255, 255, 255, 60), blur=14):
    x0, y0, x1, y1 = [int(v) for v in box]
    reg = base.crop((x0, y0, x1, y1)).filter(ImageFilter.GaussianBlur(blur))
    m = Image.new('L', reg.size, 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, *reg.size), r, fill=255)
    base.paste(reg, (x0, y0), m)
    ov = Image.new('RGBA', base.size, (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
    d.rounded_rectangle(box, r, fill=tint, outline=(255, 255, 255, 120), width=2)
    base.alpha_composite(ov)

# ---------------------------------------------------------------- styles
def s_text_behind(i, t):
    img = grad((18, 22, 38), (60, 30, 80))
    words = [('STOP', 0.0), ('SCROLL', 2.8), ('KARO', 5.4)]
    cur = [w for w in words if t >= w[1]][-1]
    k = ease((t - cur[1]) / 0.6)
    f = font('anton', 230 if len(cur[0]) <= 4 else 168)
    y = 520 + (1 - k) * 260
    img.alpha_composite(text_layer(cur[0], f, (255, 214, 64), (W / 2, y), alpha=int(255 * min(1, k * 1.5))))
    bob = math.sin(t * 6) * 3
    paste_avatar(img, '02_avatar_arms_crossed.png', 620, W / 2, H + 40, dy=bob)
    f2 = font('mont', 30, 'ExtraBold')
    img.alpha_composite(text_layer('word head ke peeche', f2, 'white', (W / 2, 880), stroke=3, stroke_fill='black'))
    tag(img, 'TEXT BEHIND HEAD'); return img

def s_glass(i, t):
    img = grad((40, 20, 110), (230, 90, 120))
    d0 = ImageDraw.Draw(img)
    for cx, cy, r, c in [(420, 200, 150, (255, 180, 60, 255)), (120, 560, 120, (60, 220, 255, 255)), (460, 640, 90, (255, 90, 200, 255))]:
        d0.ellipse((cx - r, cy - r, cx + r, cy + r), fill=c)
    img = img.filter(ImageFilter.GaussianBlur(40))
    paste_avatar(img, '06_avatar_thumbs_up.png', 540, 410, H + 30, dy=math.sin(t * 5) * 3)
    cards = [(0.3, (30, 120, 330, 250), '1.2M', 'views', 1_200_000), (1.4, (30, 270, 330, 400), '+38%', 'reach', 38),
             (2.5, (30, 420, 330, 550), '4.2K', 'naye followers', 4200)]
    for st, box, big, small, val in cards:
        k = back((t - st) / 0.7)
        if t < st: continue
        dx = (1 - k) * -360
        b = (box[0] + dx, box[1], box[2] + dx, box[3])
        frosted(img, b, tint=(255, 255, 255, 70))
        cnt = min(1, (t - st) / 1.2)
        if big.endswith('%'): s = f'+{int(val * cnt)}%'
        elif big.endswith('M'): s = f'{val * cnt / 1e6:.1f}M'
        else: s = f'{val * cnt / 1e3:.1f}K'
        d = ImageDraw.Draw(img)
        d.text((b[0] + 24, b[1] + 22), s, font=font('mont', 52, 'Black'), fill='white')
        d.text((b[0] + 26, b[1] + 88), small, font=font('mont', 22, 'SemiBold'), fill=(235, 240, 255))
    if t > 3.8:
        k = ease((t - 3.8) / 0.6); b = (30, 590, 330, 650)
        frosted(img, b, tint=(255, 255, 255, 70))
        d = ImageDraw.Draw(img); d.rounded_rectangle((50, 612, 50 + 250 * k, 628), 8, fill=(120, 255, 170))
    tag(img, 'LIQUID GLASS CARDS'); return img

_wall_cache = {}
def s_wall(i, t):
    img = Image.new('RGBA', (W, H), (14, 14, 20, 255)); d = ImageDraw.Draw(img)
    LW = [(0, 60), (250, 260), (250, 640), (0, 860)]; RW = [(290, 260), (W, 60), (W, 860), (290, 640)]
    d.polygon(LW, fill=(232, 224, 208)); d.polygon(RW, fill=(214, 205, 188))
    d.polygon([(250, 260), (290, 260), (290, 640), (250, 640)], fill=(200, 190, 172))
    d.polygon([(0, 860), (250, 640), (290, 640), (W, 860), (W, H), (0, H)], fill=(60, 52, 48))
    lines_l = ['AI', 'SE', 'EDIT'][:1 + int(t / 0.9)] if t < 2.7 else ['AI', 'SE', 'EDIT']
    lines_r = ['DEEWAR', 'PAR', 'LIKHO'][:max(0, int((t - 2.8) / 0.8) + 1)] if t > 2.8 else []
    def wall_text(lines, quad, col, fsize):
        T = Image.new('RGBA', (600, 900), (0, 0, 0, 0)); td = ImageDraw.Draw(T)
        f = font('anton', fsize)
        for k, ln in enumerate(lines): td.text((300, 160 + k * (fsize + 10)), ln, font=f, fill=col, anchor='mm')
        src = np.float32([[0, 0], [600, 0], [600, 900], [0, 900]])
        M = cv2.getPerspectiveTransform(src, np.float32(quad))
        return Image.fromarray(cv2.warpPerspective(np.array(T), M, (W, H)))
    if lines_l: img.alpha_composite(wall_text(lines_l, [(0, 60), (250, 260), (250, 640), (0, 860)], (30, 30, 34, 235), 210))
    if lines_r: img.alpha_composite(wall_text(lines_r, [(290, 260), (W, 60), (W, 860), (290, 640)], (200, 40, 40, 235), 150))
    sh = Image.new('RGBA', (W, H), (0, 0, 0, 0)); ImageDraw.Draw(sh).ellipse((170, 905, 370, 945), fill=(0, 0, 0, 120))
    img.alpha_composite(sh.filter(ImageFilter.GaussianBlur(8)))
    paste_avatar(img, '04_avatar_shrug.png', 500, W / 2, 930, dy=math.sin(t * 5) * 2)
    tag(img, 'WALL TEXT'); return img

def s_karaoke(i, t):
    img = bg('23_bg_black_spotlight.png')
    paste_avatar(img, 'ama/cz/avatar_mic_voiceover.png'.replace('ama/', '/home/claude/ama/'), 600, W / 2, H - 120, dy=math.sin(t * 7) * 3)
    words = 'yeh caption har shabd ke saath chalta hai bilkul aise'.split()
    per = 0.42; idx = min(len(words) - 1, int(t / per))
    group = idx // 3; chunk = words[group * 3: group * 3 + 3]
    f = font('mont', 46, 'Black')
    d = ImageDraw.Draw(img)
    widths = [d.textlength(w.upper(), font=f) for w in chunk]; gap = 16
    while sum(widths) + gap * (len(chunk) - 1) > W - 60:
        f = ImageFont.truetype(f.path, f.size - 3); f.set_variation_by_name('Black')
        widths = [d.textlength(w.upper(), font=f) for w in chunk]
    x = W / 2 - (sum(widths) + gap * (len(chunk) - 1)) / 2; y = 770
    for j, w in enumerate(chunk):
        gi = group * 3 + j
        if gi == idx:
            pk = back((t - gi * per) / 0.18)
            pad = 8
            d.rounded_rectangle((x - pad, y - 34 - 4 * pk, x + widths[j] + pad, y + 34 + 4 * pk), 10, fill=(255, 214, 0))
            d.text((x, y), w.upper(), font=f, fill='black', anchor='lm')
        else:
            col = 'white' if gi < idx else (255, 255, 255, 150)
            d.text((x, y), w.upper(), font=f, fill=col, anchor='lm', stroke_width=3, stroke_fill='black')
        x += widths[j] + gap
    tag(img, 'KARAOKE CAPTIONS'); return img

def s_glitch(i, t):
    poses = ['01_avatar_wave.png', '03_avatar_point_up.png', '04_avatar_shrug.png', '06_avatar_thumbs_up.png']
    cols = [(255, 60, 90), (40, 40, 48), (255, 214, 0), (20, 200, 160)]
    seg = int(t / 1.0) % 4; lt = t % 1.0
    img = Image.new('RGBA', (W, H), cols[seg] + (255,))
    words = ['STOP', 'THIS', 'IS', 'VIRAL'][seg]
    tc = 'white' if seg in (0, 1, 3) else 'black'
    img.alpha_composite(text_layer(words, font('anton', 200), tc, (W / 2, 300)))
    paste_avatar(img, poses[seg], 600, W / 2, H + 20, scale=1 + 0.08 * ease(lt / 0.3))
    a = np.array(img.convert('RGB'))
    if lt < 0.14 or lt > 0.9:
        s = 14
        a = np.dstack([np.roll(a[..., 0], s, 1), a[..., 1], np.roll(a[..., 2], -s, 1)])
        for _ in range(5):
            y0 = random.randint(0, H - 40); h = random.randint(8, 40)
            a[y0:y0 + h] = np.roll(a[y0:y0 + h], random.randint(-60, 60), 1)
    if lt > 0.9:
        shift = int((lt - 0.9) / 0.1 * W); a = np.roll(a, -shift, 1)
        a = cv2.blur(a, (61, 1))
    img = Image.fromarray(a).convert('RGBA')
    tag(img, 'GLITCH CUTS'); return img

def s_editorial(i, t):
    img = grad((8, 8, 12), (30, 26, 40))
    paste_avatar(img, '02_avatar_arms_crossed.png', 640, W / 2, H + 60, dy=math.sin(t * 4) * 2)
    veil = Image.new('RGBA', (W, H), (0, 0, 0, 0)); vd = ImageDraw.Draw(veil)
    for y in range(400):
        vd.line((0, y, W, y), fill=(0, 0, 0, int(220 * (1 - y / 400))))
    img.alpha_composite(veil)
    pairs = [(0.0, 'MAIN', 'kehta hoon'), (2.9, 'EDITING', 'ek kala hai'), (5.5, 'AUR AI', 'mera brush')]
    cur = [p for p in pairs if t >= p[0]][-1]; k = ease((t - cur[0]) / 0.7)
    blur = (1 - k) * 8
    L = text_layer(cur[1], font('mont', 78, 'ExtraBold'), 'white', (W / 2, 170), glow=(255, 255, 255, 140), glow_r=12, alpha=int(255 * k))
    L2 = text_layer(cur[2], font('playi', 62), (255, 236, 200), (W / 2, 255), glow=(255, 220, 160, 120), glow_r=10, alpha=int(255 * ease((t - cur[0] - 0.25) / 0.6)))
    if blur > 0.5: L = L.filter(ImageFilter.GaussianBlur(blur)); L2 = L2.filter(ImageFilter.GaussianBlur(blur))
    img.alpha_composite(L); img.alpha_composite(L2)
    tag(img, 'EDITORIAL FONT MIX'); return img

def s_neon(i, t):
    img = Image.new('RGBA', (W, H), (6, 4, 18, 255))
    d = ImageDraw.Draw(img)
    for x in range(0, W, 30): d.line((x, 600, W / 2 + (x - W / 2) * 3, H), fill=(80, 30, 140, 120))
    for k in range(8):
        y = 600 + (k ** 1.6) * 7 + (t * 40 % 30); d.line((0, y, W, y), fill=(80, 30, 140, 120))
    flick = 1.0 if (int(t * 20) % 17) not in (3, 4) or t > 2 else 0.25
    a1 = int(255 * flick)
    img.alpha_composite(text_layer('AI', font('bebas', 220), (255, 230, 250), (W / 2, 210), glow=(255, 40, 200, 255), glow_r=18, alpha=a1))
    if t > 1.2:
        img.alpha_composite(text_layer('EDIT KARO', font('bebas', 110), (220, 255, 255), (W / 2, 360), glow=(0, 220, 255, 255), glow_r=16, alpha=int(255 * ease((t - 1.2) / 0.4))))
    av = avatar('01_avatar_wave.png', 480).copy()
    rim = av.split()[3].filter(ImageFilter.GaussianBlur(10))
    g = Image.new('RGBA', av.size, (255, 40, 200, 0)); g.putalpha(rim.point(lambda v: min(255, v * 2)))
    x = int(W / 2 - av.width / 2); y = int(H + 20 - av.height + math.sin(t * 5) * 3)
    img.alpha_composite(g, (x - 6, y)); img.alpha_composite(av, (x, y))
    tag(img, 'NEON GLOW'); return img

def s_punch(i, t):
    img = bg('22_bg_yellow_waves.png')
    beats = [0.0, 1.6, 3.2, 4.8, 6.4]
    b = max(x for x in beats if x <= t); lt = t - b
    z = 1 + (0.32 if beats.index(b) % 2 else 0.0) * ease(lt / 0.15)
    base = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    paste_avatar(base, '03_avatar_point_up.png', 640, W / 2, H + 20)
    if z != 1:
        bw, bh = int(W * z), int(H * z)
        base = base.resize((bw, bh), Image.LANCZOS).crop(((bw - W) // 2, int((bh - H) * 0.3), (bw - W) // 2 + W, int((bh - H) * 0.3) + H))
    img.alpha_composite(base)
    stickers = ['YEH', 'DEKHO', 'ZOOM', 'PUNCH', 'BOOM']
    s = stickers[beats.index(b)]; k = back(lt / 0.25)
    St = Image.new('RGBA', (360, 140), (0, 0, 0, 0)); sd = ImageDraw.Draw(St)
    f = font('archivo', 64); w = sd.textlength(s, font=f)
    sd.rounded_rectangle((180 - w / 2 - 20, 25, 180 + w / 2 + 20, 115), 18, fill='white', outline='black', width=5)
    sd.text((180, 70), s, font=f, fill='black', anchor='mm')
    St = St.rotate(-6 + 12 * (beats.index(b) % 2), expand=True, resample=Image.BICUBIC)
    sc = max(0.01, k); St = St.resize((max(1, int(St.width * sc)), max(1, int(St.height * sc))))
    img.alpha_composite(St, (int(W / 2 - St.width / 2), int(700 - St.height / 2)))
    if lt < 0.08:
        img.alpha_composite(Image.new('RGBA', (W, H), (255, 255, 255, int(160 * (1 - lt / 0.08)))))
    tag(img, 'PUNCH-IN + STICKERS'); return img

def s_counter(i, t):
    img = grad((10, 30, 60), (10, 80, 90))
    k = ease(min(1, t / 4.5)); val = int(100000 * k)
    s = f'{val:,}'.replace(',', ',')
    # split-flap tiles
    digits = list(f'{val:06d}'); f = font('anton', 96)
    x0 = W / 2 - (6 * 74 + 5 * 8) / 2
    d = ImageDraw.Draw(img)
    for j, ch in enumerate(digits):
        x = x0 + j * 82
        d.rounded_rectangle((x, 170, x + 74, 300), 10, fill=(20, 20, 26))
        d.line((x, 235, x + 74, 235), fill=(0, 0, 0), width=3)
        d.text((x + 37, 236), ch, font=f, fill=(255, 220, 90), anchor='mm')
    d.text((W / 2, 340), 'FOLLOWERS', font=font('mont', 34, 'Black'), fill='white', anchor='mm')
    if t > 4.5:
        random.seed(int(t * 30))
        for _ in range(40):
            cx = random.randint(0, W); cy = int((random.random() * 500 + (t - 4.5) * 300) % 900)
            d.rectangle((cx, cy, cx + 8, cy + 14), fill=random.choice([(255, 90, 120), (255, 220, 90), (90, 220, 255), (140, 255, 150)]))
        img.alpha_composite(text_layer('1 LAKH!', font('kaushan', 90), 'white', (W / 2, 450), glow=(255, 220, 90, 200), glow_r=14, alpha=int(255 * ease((t - 4.5) / 0.4))))
    paste_avatar(img, '06_avatar_thumbs_up.png', 470, W / 2, H + 20, dy=math.sin(t * 6) * 3)
    tag(img, 'COUNTER / SPLIT-FLAP'); return img

def s_comments(i, t):
    img = bg('27_bg_white_clean.png')
    paste_avatar(img, '04_avatar_shrug.png', 560, W / 2, H + 30, dy=math.sin(t * 5) * 3)
    items = [(0.3, 'rahul.edits', 'Bhai ye edit kisne kiya??'), (1.6, 'pinky_reels', 'Mujhe bhi aisi reel chahiye'),
             (2.9, 'jassi.music', 'Rate kya hai paaji?'), (4.2, 'aitricksbysumit', 'DM karo "EDIT" 🎬'.replace(' 🎬', ''))]
    y = 90
    for st, user, msg in items:
        if t < st: continue
        k = back((t - st) / 0.45)
        box = Image.new('RGBA', (470, 96), (0, 0, 0, 0)); bd = ImageDraw.Draw(box)
        mine = user == 'aitricksbysumit'
        bd.rounded_rectangle((0, 0, 469, 95), 22, fill=(0, 132, 255) if mine else (255, 255, 255), outline=(220, 220, 228), width=2)
        bd.ellipse((14, 22, 64, 72), fill=(255, 140, 60) if not mine else (255, 255, 255))
        bd.text((80, 30), user, font=font('mont', 20, 'Bold'), fill=(255, 255, 255) if mine else (40, 40, 48), anchor='lm')
        bd.text((80, 64), msg, font=font('mont', 24, 'SemiBold'), fill='white' if mine else (20, 20, 24), anchor='lm')
        sc = max(0.05, k); bx = box.resize((int(470 * sc), int(96 * sc)))
        img.alpha_composite(bx, (int(W / 2 - bx.width / 2), int(y + 48 - bx.height / 2)))
        y += 112
    tag(img, 'COMMENT POP-UPS'); return img

STYLES = {'text_behind': s_text_behind, 'glass': s_glass, 'wall': s_wall, 'karaoke': s_karaoke,
          'glitch': s_glitch, 'editorial': s_editorial, 'neon': s_neon, 'punch': s_punch,
          'counter': s_counter, 'comments': s_comments}

def render(name, sample=None):
    fn = STYLES[name]
    if sample is not None:
        fn(0, sample).convert('RGB').save(f'/tmp/sample_{name}.jpg'); return
    tmp = f'{OUT}/{name}.tmp.mp4'
    p = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                          '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '24', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', tmp], stdin=subprocess.PIPE)
    random.seed(1)
    for i in range(N):
        p.stdin.write(np.array(fn(i, i / FPS).convert('RGB')).tobytes())
    p.stdin.close(); p.wait()
    if p.returncode == 0:
        os.replace(tmp, f'{OUT}/{name}.mp4')
        fn(0, 4.6).convert('RGB').save(f'{OUT}/{name}.jpg', quality=85)

if __name__ == '__main__':
    args = sys.argv[1:]
    if args and args[0] == '--sample':
        t = float(args[1])
        for n in (args[2:] or STYLES): render(n, sample=t)
    else:
        for n in (args or STYLES): render(n)
