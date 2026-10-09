"""Flat-illustration backgrounds in Durga Maa red & yellow (procedural, no stock images)."""
import math, numpy as np, cv2
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H = 1188, 2112            # 10 % larger than 1080x1920 for slow zoom / drift
rng = np.random.default_rng(21)
YY, XX = np.mgrid[0:H, 0:W].astype(np.float32)

def hexc(h): h = h.lstrip('#'); return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], np.float32)
def vgrad(stops):
    """stops: [(y_frac, '#hex'), ...] -> HxWx3 float"""
    ys = np.array([s[0] for s in stops]); cs = np.array([hexc(s[1]) for s in stops])
    t = np.linspace(0, 1, H)
    col = np.stack([np.interp(t, ys, cs[:, k]) for k in range(3)], 1)
    return np.repeat(col[:, None, :], W, 1)

def ridge(base, amp, rough=0.55, seed=0, octaves=7):
    r = np.random.default_rng(seed); n = 2 ** octaves + 1; y = np.zeros(n); step = n - 1; a = 1.0
    y[0], y[-1] = r.uniform(-1, 1), r.uniform(-1, 1)
    while step > 1:
        h = step // 2
        for i in range(h, n, step): y[i] = (y[i - h] + y[i + h]) / 2 + r.uniform(-a, a)
        a *= rough; step = h
    y = (y - y.min()) / (y.max() - y.min() + 1e-6)
    return base - amp * np.interp(np.linspace(0, n - 1, W), np.arange(n), y)

def fill_below(img, top, color, alpha=1.0):
    m = (YY >= top[None, :]).astype(np.float32)
    m = cv2.GaussianBlur(m, (0, 0), 1.2)[..., None] * alpha
    return img * (1 - m) + hexc(color) * m

def sun(img, cx, cy, r, color, glow=3.0, ga=0.55):
    d = np.sqrt((XX - cx) ** 2 + (YY - cy) ** 2)
    disk = np.clip((r - d) / 2.5, 0, 1)[..., None]
    g = np.exp(-(d / (r * glow)) ** 2)[..., None] * ga
    img = img + (hexc(color) - img) * g
    return img * (1 - disk) + hexc(color) * disk

def grain(img, amt=3):
    return np.clip(img + rng.normal(0, amt, (H, W, 1)), 0, 255)

def paper(img, amt=0.025):
    n = cv2.resize(rng.random((H // 16, W // 16)).astype(np.float32), (W, H), interpolation=cv2.INTER_CUBIC)
    return img * (1 - amt + amt * 2 * n[..., None])

def to_pil(img): return Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))

def snowcap(img, top, color='#fff6e0', depth=90, seed=1):
    r = np.random.default_rng(seed)
    cap = top + depth * (0.55 + 0.45 * np.sin(np.linspace(0, 40, W) + r.uniform(0, 6))) * 0.6
    m = ((YY >= top[None, :]) & (YY < cap[None, :])).astype(np.float32)
    # only on high peaks
    hi = (top < np.percentile(top, 45)).astype(np.float32)[None, :]
    m = cv2.GaussianBlur(m * hi, (0, 0), 1.5)[..., None]
    return img * (1 - m) + hexc(color) * m

def birds(d, n, x0, y0, spread, col, size=14, seed=3):
    r = np.random.default_rng(seed)
    for _ in range(n):
        x = x0 + r.uniform(-spread, spread); y = y0 + r.uniform(-spread * 0.4, spread * 0.4); s = size * r.uniform(0.6, 1.2)
        d.line([(x - s, y - s * 0.3), (x, y), (x + s, y - s * 0.3)], fill=col, width=3)

# ---------------------------------------------------------------- scenes
def scene_cave():
    img = vgrad([(0, '#7a0a12'), (0.35, '#c4161c'), (0.6, '#f0682a'), (0.78, '#ffc23a'), (1, '#ffd56a')])
    img = sun(img, W * 0.72, H * 0.30, 95, '#ffe08a', glow=4, ga=0.45)
    t1 = ridge(H * 0.62, 380, seed=4); img = fill_below(img, t1, '#a3121b')
    img = snowcap(img, t1, '#ffd9b0', 70, seed=4)
    t2 = ridge(H * 0.74, 300, seed=8); img = fill_below(img, t2, '#6e0b12')
    # cave mouth in the front mountain, glowing gold from inside
    cx, cy = W * 0.5, H * 0.80
    d = np.sqrt(((XX - cx) / 170) ** 2 + ((YY - cy) / 210) ** 2)
    arch = ((d < 1) & (YY < cy + 120)).astype(np.float32)
    arch = cv2.GaussianBlur(arch, (0, 0), 2)[..., None]
    inner = np.exp(-(((XX - cx) / 120) ** 2 + ((YY - (cy + 40)) / 150) ** 2))[..., None]
    cave = hexc('#2a0306') * (1 - inner) + hexc('#ffcf4a') * inner
    img = img * (1 - arch) + cave * arch
    glow = np.exp(-(((XX - cx) / 330) ** 2 + ((YY - cy) / 330) ** 2))[..., None] * 0.35
    img = img + (hexc('#ffb52e') - img) * glow * (1 - arch)
    t3 = ridge(H * 0.95, 140, seed=11); img = fill_below(img, t3, '#3d0508')
    im = to_pil(grain(paper(img)))
    d = ImageDraw.Draw(im)
    # small temple flags on the cave top
    for k, x in enumerate([cx - 40, cx + 60]):
        y = cy - 230; d.line([(x, y), (x, y - 120)], fill=(60, 10, 10), width=5)
        d.polygon([(x, y - 120), (x + 70, y - 100), (x, y - 78)], fill=(255, 200, 40) if k else (230, 30, 30))
    birds(d, 7, W * 0.3, H * 0.33, 160, (90, 10, 15))
    return im

def scene_mountains():
    img = vgrad([(0, '#ffe7a3'), (0.4, '#ffc23a'), (0.62, '#f78a2a'), (1, '#c4161c')])
    img = sun(img, W * 0.5, H * 0.52, 150, '#fff3c8', glow=3.2, ga=0.6)
    for base, amp, col, s in [(0.58, 300, '#f2a640', 2), (0.66, 320, '#e5702f', 5), (0.75, 330, '#cf3a24', 9), (0.85, 300, '#9e1219', 13), (0.95, 220, '#5c0910', 17)]:
        t = ridge(H * base, amp, seed=s); img = fill_below(img, t, col)
    im = to_pil(grain(paper(img)))
    birds(ImageDraw.Draw(im), 9, W * 0.62, H * 0.36, 200, (120, 30, 20))
    return im

def scene_snow_falls():
    img = vgrad([(0, '#fff2c4'), (0.45, '#ffd25e'), (1, '#f39a2b')])
    t1 = ridge(H * 0.50, 520, rough=0.6, seed=31); img = fill_below(img, t1, '#d9452a')
    img = snowcap(img, t1, '#fffaf0', 150, seed=31)
    t2 = ridge(H * 0.70, 300, seed=33); img = fill_below(img, t2, '#a3121b')
    img = snowcap(img, t2, '#ffe9d6', 60, seed=33)
    # waterfall on the right cliff
    x0 = W * 0.70; top = int(t2[int(x0)]) + 10
    fall = ((XX > x0 - 55) & (XX < x0 + 55) & (YY > top) & (YY < H * 0.9)).astype(np.float32)
    streak = 0.88 + 0.12 * np.sin(XX * 0.12 + np.sin(YY * 0.01) * 3)
    fall = cv2.GaussianBlur(fall, (0, 0), 6) * streak
    img = img * (1 - fall[..., None]) + hexc('#fff8ea') * fall[..., None]
    mist = np.exp(-(((XX - x0) / 210) ** 2 + ((YY - H * 0.9) / 90) ** 2))[..., None] * 0.8
    img = img + (hexc('#fff6e6') - img) * mist
    t3 = ridge(H * 0.97, 160, seed=37); img = fill_below(img, t3, '#5c0910')
    return to_pil(grain(paper(img)))

def scene_garlands():
    """festive font-display page: deep red paper, marigold garlands, bells and a diya row"""
    img = vgrad([(0, '#8d0b14'), (0.5, '#b5121b'), (1, '#7a0a12')])
    img = paper(img, 0.03)
    im = to_pil(grain(img, 5)); d = ImageDraw.Draw(im)
    # thin gold frame like a font specimen card
    d.rectangle([40, 40, W - 40, H - 40], outline=(255, 205, 70), width=4)
    d.rectangle([58, 58, W - 58, H - 58], outline=(255, 205, 70), width=1)
    # marigold garland arcs (toran)
    for row, (sag, y0) in enumerate([(140, 120), (100, 230)]):
        n = 9
        for k in range(n):
            xa, xb = W * k / n, W * (k + 1) / n
            for j in range(16):
                u = j / 15; x = xa + (xb - xa) * u; y = y0 + sag * math.sin(math.pi * u)
                c = (255, 150 + 40 * ((j + row) % 2), 20) if row == 0 else (255, 205, 40)
                r = 15 - row * 3
                d.ellipse([x - r, y - r, x + r, y + r], fill=c, outline=(200, 90, 10))
            # hanging string with a bell
            x = xb; d.line([(x, y0), (x, y0 + 120 + 40 * row)], fill=(255, 190, 60), width=3)
            by = y0 + 120 + 40 * row
            d.pieslice([x - 22, by - 10, x + 22, by + 34], 180, 360, fill=(255, 196, 50))
            d.rectangle([x - 22, by + 11, x + 22, by + 18], fill=(230, 160, 30))
    # diya row at the bottom
    base = H - 260
    for k in range(7):
        x = W * (k + 0.5) / 7
        d.pieslice([x - 60, base - 40, x + 60, base + 40], 0, 180, fill=(196, 92, 30), outline=(120, 40, 10), width=3)
        d.ellipse([x - 14, base - 72, x + 14, base - 8], fill=(255, 200, 60))
        d.ellipse([x - 7, base - 58, x + 7, base - 18], fill=(255, 245, 200))
    arr = np.array(im).astype(np.float32)
    for k in range(7):                              # flame glow
        x = W * (k + 0.5) / 7
        g = np.exp(-(((XX - x) / 70) ** 2 + ((YY - (base - 45)) / 70) ** 2))[..., None] * 0.55
        arr = arr + (hexc('#ffcf5a') - arr) * g
    return to_pil(arr)

def scene_wind():
    img = vgrad([(0, '#ffeab0'), (0.5, '#ffc84a'), (1, '#f08a2a')])
    t1 = ridge(H * 0.66, 260, seed=51); img = fill_below(img, t1, '#e0582a')
    t2 = ridge(H * 0.78, 220, seed=52); img = fill_below(img, t2, '#b31c1e')
    t3 = ridge(H * 0.92, 160, seed=53); img = fill_below(img, t3, '#6e0b12')
    im = to_pil(grain(paper(img))); d = ImageDraw.Draw(im)
    # wind swirls
    for k in range(7):
        y = H * (0.44 + 0.03 * k); x0 = rng.uniform(-100, 300); pts = []
        for j in range(60):
            x = x0 + j * 14; pts.append((x, y + 18 * math.sin(j / 6 + k)))
        d.line(pts, fill=(255, 250, 235), width=4)
        ex, ey = pts[-1]; d.arc([ex - 40, ey - 40, ex + 20, ey + 20], 270, 180, fill=(255, 250, 235), width=4)
    # pole with fluttering red/yellow chunri flags on the hill
    px = int(W * 0.78); py = int(t2[px]) + 5
    d.line([(px, py), (px, py - 520)], fill=(70, 15, 15), width=8)
    top = py - 500; L = 420
    up = [(px - i * L / 12, top + 10 * math.sin(i * 0.9) + i * 9) for i in range(13)]
    lo = [(px - i * L / 12, top + 190 - i * 6 + 10 * math.sin(i * 0.9 + 0.6)) for i in range(12, -1, -1)]
    d.polygon(up + lo, fill=(255, 196, 40))
    up2 = [(px - i * (L - 40) / 12, top + 14 + 10 * math.sin(i * 0.9) + i * 9) for i in range(13)]
    lo2 = [(px - i * (L - 40) / 12, top + 176 - i * 6 + 10 * math.sin(i * 0.9 + 0.6)) for i in range(12, -1, -1)]
    d.polygon(up2 + lo2, fill=(214, 26, 32))
    return im

def trishul(d, cx, top, s, col):
    w = 16 * s
    d.rectangle([cx - w / 2, top + 160 * s, cx + w / 2, top + 700 * s], fill=col)       # shaft
    d.polygon([(cx, top), (cx - 26 * s, top + 70 * s), (cx - 10 * s, top + 190 * s), (cx + 10 * s, top + 190 * s), (cx + 26 * s, top + 70 * s)], fill=col)
    for side in (-1, 1):
        pts = []
        for i in range(21):
            u = i / 20; x = cx + side * (30 + 110 * math.sin(u * math.pi * 0.5)) * s; y = top + (230 - 170 * u ** 1.6) * s
            pts.append((x, y))
        pts += [(cx + side * 150 * s, top + 40 * s), (cx + side * 110 * s, top + 70 * s)]
        for i in range(20, -1, -1):
            u = i / 20; x = cx + side * (30 + 80 * math.sin(u * math.pi * 0.5)) * s; y = top + (250 - 150 * u ** 1.6) * s
            pts.append((x, y))
        d.polygon(pts, fill=col)
    d.rectangle([cx - 60 * s, top + 230 * s, cx + 60 * s, top + 262 * s], fill=col)
    # damru-ish knot ribbons
    d.polygon([(cx, top + 300 * s), (cx + 120 * s, top + 360 * s), (cx + 40 * s, top + 330 * s)], fill=(230, 30, 30))

def scene_trishul():
    img = vgrad([(0, '#5c0910'), (0.3, '#a3121b'), (0.55, '#ef5a26'), (0.72, '#ffc23a'), (1, '#ffe6a0')])
    img = sun(img, W * 0.5, H * 0.50, 230, '#ffe08a', glow=2.6, ga=0.65)
    # sun rays
    ang = np.arctan2(YY - H * 0.5, XX - W * 0.5); rays = (np.sin(ang * 18) > 0.6).astype(np.float32)
    rays = rays * np.exp(-((np.sqrt((XX - W / 2) ** 2 + (YY - H / 2) ** 2)) / 900) ** 2)
    img = img + (hexc('#ffe9a8') - img) * (rays * 0.22)[..., None]
    t1 = ridge(H * 0.70, 260, seed=61); img = fill_below(img, t1, '#b31c1e')
    # central peak
    peak = H * 0.62 + np.abs(XX[0] - W / 2) * 0.9
    t2 = np.maximum(np.minimum(ridge(H * 0.80, 140, seed=63), peak), 0); img = fill_below(img, t2, '#6e0b12')
    im = to_pil(grain(paper(img))); d = ImageDraw.Draw(im)
    trishul(d, W / 2, H * 0.62 - 700 * 0.75, 0.75, (60, 6, 10))
    return im

def scene_page_red():
    """font display page: red paper, faint mandala watermark, gold frame"""
    img = vgrad([(0, '#b5121b'), (1, '#8d0b14')]); img = paper(img, 0.03)
    r = np.sqrt((XX - W / 2) ** 2 + (YY - H * 0.58) ** 2); a = np.arctan2(YY - H * 0.58, XX - W / 2)
    m = np.zeros((H, W), np.float32)
    for k, (rad, petals) in enumerate([(220, 12), (330, 16), (440, 24), (560, 32)]):
        m += np.exp(-((r - rad * (1 + 0.08 * np.cos(a * petals))) / 6) ** 2)
    m += np.exp(-((r - 120) / 5) ** 2)
    img = img + (hexc('#ffcf4a') - img) * (np.clip(m, 0, 1) * 0.28)[..., None]
    im = to_pil(grain(img, 5)); d = ImageDraw.Draw(im)
    d.rectangle([40, 40, W - 40, H - 40], outline=(255, 205, 70), width=4)
    d.rectangle([58, 58, W - 58, H - 58], outline=(255, 205, 70), width=1)
    return im

if __name__ == '__main__':
    for name, fn in [('cave', scene_cave), ('mountains', scene_mountains), ('snow', scene_snow_falls), ('garlands', scene_garlands),
                     ('wind', scene_wind), ('trishul', scene_trishul), ('page', scene_page_red)]:
        fn().save(f'bg_{name}.png'); print(name)
