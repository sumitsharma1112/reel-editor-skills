#!/usr/bin/env python3
"""(tilt_intro.py) Tilt-your-phone intro for a rotated (tilt-view) reel.
Usage: python3 -I intro.py <scale> <out_dir> <scene_image>
scale 1 -> 1080x1920, scale 2 -> 2160x3840.
The phone starts portrait showing the scene sideways (as the reel is), then rotates
90 degrees counter-clockwise so the scene stands upright. Text pops/slams in.
"""
import sys, math, os
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

S = int(sys.argv[1]); OUT = sys.argv[2]; SCENE = sys.argv[3]
os.makedirs(OUT, exist_ok=True)
W, H = 1080 * S, 1920 * S
FPS, DUR = 24, 2.8
N = int(DUR * FPS)
import pathlib
F = str(pathlib.Path(__file__).resolve().parent.parent / 'fonts') + '/'
GOLD = (252, 207, 0); SAFFRON = (232, 137, 43); CREAM = (255, 244, 220)

def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def out_cubic(u): return 1 - (1 - u) ** 3
def out_back(u, k=2.2):
    u = clamp(u); return 1 + (k + 1) * (u - 1) ** 3 + k * (u - 1) ** 2
def in_out_cubic(u):
    u = clamp(u); return 4 * u ** 3 if u < .5 else 1 - (-2 * u + 2) ** 3 / 2

# ---------- background ----------
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
top = np.array([22, 6, 4], np.float32); bot = np.array([78, 24, 8], np.float32)
g = (yy / H)[..., None]
bg = top * (1 - g) + bot * g
d = np.sqrt(((xx - W / 2) / (760 * S)) ** 2 + ((yy - 760 * S) / (760 * S)) ** 2)
glow = np.clip(1 - d, 0, 1)[..., None] ** 2 * 0.55
bg = bg * (1 - glow) + np.array(SAFFRON, np.float32) * glow
v = np.sqrt(((xx - W / 2) / (W * .8)) ** 2 + ((yy - H / 2) / (H * .72)) ** 2)
bg *= np.clip(1.15 - v * .55, .35, 1)[..., None]
BG = Image.fromarray(np.clip(bg, 0, 255).astype(np.uint8)).convert('RGBA')

# ---------- phone ----------
PW, PH = 420 * S, 840 * S
scene = Image.open(SCENE).convert('RGB').rotate(-90, expand=True)  # sideways, like the reel
sw, sh = PW - 32 * S, PH - 32 * S
r = max(sw / scene.width, sh / scene.height)
scene = scene.resize((int(scene.width * r) + 1, int(scene.height * r) + 1), Image.LANCZOS)
l = (scene.width - sw) // 2; t = (scene.height - sh) // 2
scene = scene.crop((l, t, l + sw, t + sh))
phone = Image.new('RGBA', (PW, PH), (0, 0, 0, 0))
pd = ImageDraw.Draw(phone)
pd.rounded_rectangle((0, 0, PW - 1, PH - 1), 64 * S, fill=(14, 14, 16, 255), outline=GOLD + (255,), width=5 * S)
mask = Image.new('L', (sw, sh), 0)
ImageDraw.Draw(mask).rounded_rectangle((0, 0, sw - 1, sh - 1), 48 * S, fill=255)
phone.paste(scene, (16 * S, 16 * S), mask)
pd.rounded_rectangle((PW // 2 - 46 * S, 26 * S, PW // 2 + 46 * S, 44 * S), 9 * S, fill=(8, 8, 8, 255))
PCX, PCY = W // 2, 760 * S

# ---------- text layers ----------
def text_layer(txt, font, fill, shadow=True, glow=None, spacing=0):
    tmp = ImageDraw.Draw(Image.new('RGBA', (4, 4)))
    if spacing:
        wsum = sum(tmp.textlength(c, font=font) for c in txt) + spacing * (len(txt) - 1)
    else:
        wsum = tmp.textlength(txt, font=font)
    asc, desc = font.getmetrics()
    pad = 60 * S
    w, h = int(wsum) + pad * 2, asc + desc + pad * 2
    lay = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    def draw(img, col, off=(0, 0)):
        dd = ImageDraw.Draw(img)
        if spacing:
            x = pad + off[0]
            for c in txt:
                dd.text((x, pad + off[1]), c, font=font, fill=col)
                x += dd.textlength(c, font=font) + spacing
        else:
            dd.text((pad + off[0], pad + off[1]), txt, font=font, fill=col)
    if glow:
        gl = Image.new('RGBA', (w, h), (0, 0, 0, 0)); draw(gl, glow + (200,))
        lay = Image.alpha_composite(lay, gl.filter(ImageFilter.GaussianBlur(22 * S)))
    if shadow:
        sh_ = Image.new('RGBA', (w, h), (0, 0, 0, 0)); draw(sh_, (0, 0, 0, 190), (0, 8 * S))
        lay = Image.alpha_composite(lay, sh_.filter(ImageFilter.GaussianBlur(7 * S)))
    top_ = Image.new('RGBA', (w, h), (0, 0, 0, 0)); draw(top_, fill + (255,))
    return Image.alpha_composite(lay, top_)

L1 = text_layer('TILT', ImageFont.truetype(F + 'anton-400.ttf', 330 * S), CREAM, glow=SAFFRON, spacing=10 * S)
L2 = text_layer('YOUR PHONE', ImageFont.truetype(F + 'anton-400.ttf', 150 * S), GOLD, spacing=8 * S)
L3 = text_layer('FOR THE FULL CINEMATIC VIEW', ImageFont.truetype(F + 'montserrat-700.ttf', 40 * S), (255, 244, 220), shadow=True, spacing=7 * S)

def place(base, lay, cx, cy, scale=1.0, alpha=1.0, angle=0):
    if alpha <= 0.001 or scale <= 0.001: return base
    im = lay
    if abs(scale - 1) > 0.002:
        im = im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))), Image.LANCZOS)
    if angle: im = im.rotate(angle, resample=Image.BICUBIC, expand=True)
    if alpha < 0.999:
        a = im.getchannel('A').point(lambda p: int(p * alpha)); im = im.copy(); im.putalpha(a)
    tmp = Image.new('RGBA', base.size, (0, 0, 0, 0))
    tmp.paste(im, (int(cx - im.width / 2), int(cy - im.height / 2)), im)
    return Image.alpha_composite(base, tmp)

# petals
rng = np.random.RandomState(7)
PET = [(rng.uniform(0, W), rng.uniform(0, H), rng.uniform(70, 160) * S, rng.uniform(9, 20) * S, rng.uniform(0, 360)) for _ in range(16)]

def arrow_layer(alpha):
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); dd = ImageDraw.Draw(lay)
    R = 520 * S; col = GOLD + (int(255 * alpha),)
    for a0, a1 in ((285, 355), (105, 175)):
        dd.arc((PCX - R, PCY - R, PCX + R, PCY + R), a0, a1, fill=col, width=14 * S)
        th = math.radians(a0)
        px, py = PCX + R * math.cos(th), PCY + R * math.sin(th)
        dx, dy = math.sin(th), -math.cos(th); nx, ny = math.cos(th), math.sin(th)
        tip = (px + dx * 44 * S, py + dy * 44 * S)
        b1 = (px + nx * 30 * S, py + ny * 30 * S); b2 = (px - nx * 30 * S, py - ny * 30 * S)
        dd.polygon([tip, b1, b2], fill=col)
    return lay

for i in range(N):
    t = i / FPS
    fr = BG.copy()
    # petals drifting up
    pl = Image.new('RGBA', (W, H), (0, 0, 0, 0)); pdr = ImageDraw.Draw(pl)
    for (x0, y0, sp, sz, rot) in PET:
        y = (y0 - sp * t) % H; x = x0 + 18 * S * math.sin(t * 1.6 + rot)
        pdr.ellipse((x - sz, y - sz * .55, x + sz, y + sz * .55), fill=(255, 176, 52, 120))
    fr = Image.alpha_composite(fr, pl)
    # phone pop + rotate
    pop = out_back((t - 0.12) / 0.30)
    ang = 0.0
    if t >= 0.55:
        u = (t - 0.55) / 0.80
        ang = 90 * in_out_cubic(u) if u < 1 else 90
        if t >= 1.35:  # tiny settle overshoot
            ang = 90 + 4 * math.sin(clamp((t - 1.35) / 0.25) * math.pi) * (1 - clamp((t - 1.35) / 0.25))
    # arrows
    aa = clamp((t - .30) / .2) * (1 - clamp((t - 1.25) / .3)) * (0.75 + 0.25 * math.sin(t * 14))
    if aa > 0.01: fr = Image.alpha_composite(fr, arrow_layer(clamp(aa)))
    fr = place(fr, phone, PCX, PCY, scale=pop, angle=ang)
    # texts
    s1 = 2.2 - 1.2 * out_cubic((t - 0.62) / 0.12) if t >= .62 else 0
    a1 = clamp((t - .62) / .04)
    if t >= .74: s1 = 1 + 0.012 * math.sin((t - .74) * 5)
    fr = place(fr, L1, W / 2, 1385 * S, scale=s1, alpha=a1)
    s2 = out_back((t - 0.98) / 0.28) if t >= .98 else 0
    fr = place(fr, L2, W / 2, 1610 * S, scale=s2, alpha=clamp((t - .98) / .08))
    a3 = clamp((t - 1.45) / .35)
    fr = place(fr, L3, W / 2, 1765 * S + (1 - out_cubic(a3)) * 24 * S, alpha=a3)
    # fade out
    fo = clamp((t - 2.5) / 0.3)
    if fo > 0:
        blk = Image.new('RGBA', (W, H), (0, 0, 0, int(255 * fo))); fr = Image.alpha_composite(fr, blk)
    fr.convert('RGB').save(f'{OUT}/f_{i:04d}.png', compress_level=1)
print('frames', N)

# ---------- sfx (synth) ----------
sr = 48000; n = int(DUR * sr); au = np.zeros(n, np.float32)
def add(start, sig, gain=1.0):
    i0 = int(start * sr); i1 = min(n, i0 + len(sig)); au[i0:i1] += sig[:i1 - i0] * gain
def tone(f0, f1, dur, decay):
    tt = np.arange(int(dur * sr)) / sr; f = f0 + (f1 - f0) * (tt / dur)
    return np.sin(2 * np.pi * np.cumsum(f) / sr) * np.exp(-tt * decay)
def noise_swell(dur, lo, hi):
    tt = np.arange(int(dur * sr)) / sr
    x = np.random.RandomState(3).randn(len(tt)).astype(np.float32)
    # crude band-pass via moving-average difference
    k1 = int(sr / hi); k2 = int(sr / lo)
    a = np.convolve(x, np.ones(max(1, k1)) / max(1, k1), 'same'); b = np.convolve(x, np.ones(max(1, k2)) / max(1, k2), 'same')
    y = a - b; env = np.sin(np.pi * np.clip(tt / dur, 0, 1)) ** 2
    return y / (np.abs(y).max() + 1e-6) * env
add(0.12, tone(520, 920, 0.18, 14), 0.35)                      # phone pop
add(0.55, noise_swell(0.8, 250, 3500), 0.30)                   # whoosh while rotating
add(0.62, tone(110, 55, 0.30, 11), 0.75)                       # slam thud
add(0.62, np.random.RandomState(5).randn(int(.05 * sr)).astype(np.float32) * np.exp(-np.arange(int(.05 * sr)) / sr * 90), 0.25)
add(0.98, tone(700, 1100, 0.14, 16), 0.35)                     # pop line 2
for fq, dl in ((1318.5, 0.0), (1760.0, 0.05), (2093.0, 0.10)):  # chime when phone lands
    add(1.38 + dl, tone(fq, fq, 0.9, 5.5), 0.14)
au *= np.clip(1 - np.clip((np.arange(n) / sr - 2.5) / 0.3, 0, 1), 0, 1)
au = au / (np.abs(au).max() + 1e-6) * 0.7
import wave
st = (np.stack([au, au], 1) * 32767).astype('<i2')
with wave.open(os.path.join(OUT, 'intro.wav'), 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(sr); w.writeframes(st.tobytes())
print('wav ok')
