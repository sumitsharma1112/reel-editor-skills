"""Example 3 s hook intro ("Apni travel photo ko BORING (struck) se STUNNING kaise banayein?" over blurred raw photos)
and 3.6 s outro ("Aise aur FONTS & STYLES ke liye" + animated FOLLOW -> FOLLOWING button). Edit the texts/paths for a new series;
uses the helpers from travel_titles.py. Concatenate intro + clips + outro with ffmpeg concat."""
import math, subprocess, numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import travel_titles as make
W, H, FPS = 1080, 1920, 30
F = lambda f, s: ImageFont.truetype('/home/claude/fonts/' + f, s)
EM = ImageFont.truetype('/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf', 109)
def emoji(ch, size):
    t = Image.new('RGBA', (160, 160)); ImageDraw.Draw(t).text((10, 10), ch, font=EM, embedded_color=True)
    t = t.crop(t.getbbox()); r = size / max(t.size); return t.resize((int(t.width * r), int(t.height * r)), Image.LANCZOS)
def txt(s, f, size, col):
    m = make.mask_text(s, f, size); im = Image.new('RGBA', m.size, col + (0,)); im.putalpha(m); return make.shadow(im, (0, 6), 12, 0.7)[0]
def grad(s, f, size, stops, w=None):
    m = make.mask_text(s, f, size)
    if w: m = make.fit(m, w)
    return make.shadow(make.fill(m, stops, shine=0.35), (0, 8), 14, 0.7)[0]
def spring(t): return 0 if t <= 0 else 1 - math.exp(-7 * t) * math.cos(12 * t)
def put(c, im, cx, cy, sc=1.0, a=1.0):
    if sc <= 0.02 or a <= 0: return
    s = im.resize((max(1, int(im.width * sc)), max(1, int(im.height * sc))), Image.LANCZOS)
    if a < 1: s.putalpha(s.split()[3].point(lambda v: int(v * a)))
    c.alpha_composite(s, (int(cx - s.width / 2), int(cy - s.height / 2)))
def writer(path):
    return subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                             '-c:v', 'libx264', '-crf', '19', '-pix_fmt', 'yuv420p', path], stdin=subprocess.PIPE)
SUN = [(0, (255, 236, 160)), (0.45, (255, 128, 88)), (1, (222, 48, 118))]
GOLD = [(0, (255, 246, 200)), (0.5, (255, 200, 70)), (1, (214, 110, 18))]
# ---------------- intro 3.2 s: raw photos flicker behind, BORING -> STUNNING
raws = [Image.open(f'base_{k}.png').convert('RGB') for k in ['trevi', 'pattaya', 'colo', 'salz', 'golden', 'sissu']]
raws = [Image.fromarray((np.array(r.filter(ImageFilter.GaussianBlur(6))) * 0.45).astype(np.uint8)).convert('RGBA') for r in raws]
L1 = txt('Apni travel photo ko', 'montserrat-700.ttf', 70, (255, 255, 255))
BOR = txt('BORING', 'anton-400.ttf', 230, (200, 200, 200))
SE = txt('se', 'mrs-saint-delafield-400.ttf', 170, (255, 255, 255))
STN = grad('STUNNING', 'anton-400.ttf', 300, SUN, 980)
L3 = txt('kaise banayein?', 'montserrat-700.ttf', 76, (255, 255, 255))
SPK = emoji('✨', 90); DOWN = emoji('👇', 110)
p = writer('intro.mp4')
for n in range(int(3.2 * FPS)):
    t = n / FPS; c = raws[min(5, int(t / 0.45)) % 6].copy() if t < 2.7 else raws[2].copy()
    put(c, L1, W / 2, 470, a=min(1, t / 0.2))
    if t < 1.3:
        put(c, BOR, W / 2, 680, sc=spring(t - 0.15))
        if t > 0.75:                                            # red strike-through
            d = ImageDraw.Draw(c); w = BOR.width * 0.8 * min(1, (t - 0.75) / 0.2)
            d.line([(W / 2 - BOR.width * 0.4, 690), (W / 2 - BOR.width * 0.4 + w, 670)], fill=(235, 30, 40), width=18)
    else:
        u = t - 1.3; sb = 0.42
        put(c, BOR, W / 2 - 110, 600, sc=sb, a=0.75); d = ImageDraw.Draw(c)
        d.line([(W / 2 - 110 - BOR.width * sb * 0.42, 604), (W / 2 - 110 + BOR.width * sb * 0.42, 594)], fill=(235, 30, 40), width=9)
        put(c, SE, W / 2 + 120, 610, a=1)
        put(c, STN, W / 2, 770, sc=(2.0 - 1.0 * spring(u)) if u < 0.12 else spring(u) * (1 + 0.02 * math.sin(t * 6)))
        put(c, SPK, W / 2 + STN.width / 2 - 20, 650, sc=spring(u - 0.2)); put(c, SPK, W / 2 - STN.width / 2 + 30, 900, sc=spring(u - 0.3))
    put(c, L3, W / 2, 1010, sc=spring(t - 1.6))
    put(c, DOWN, W / 2, 1180 + 20 * math.sin(t * 9), a=min(1, max(0, (t - 2.0) / 0.2)))
    arr = np.array(c.convert('RGB')).astype(np.float32)
    if abs(t - 1.3) < 0.07: arr = arr * 0.5 + 127
    p.stdin.write(np.clip(arr, 0, 255).astype(np.uint8).tobytes())
p.stdin.close(); p.wait()
# ---------------- outro 3.6 s: follow for more fonts & styles
bg = Image.open('/mnt/user-data/outputs/Travel_Titles/6_Sissu.jpg').convert('RGB').filter(ImageFilter.GaussianBlur(14))
bg = Image.fromarray((np.array(bg) * 0.42).astype(np.uint8)).convert('RGBA')
O1 = txt('Aise aur', 'montserrat-700.ttf', 74, (255, 255, 255))
O2 = grad('FONTS', 'anton-400.ttf', 260, GOLD, 760); O3 = txt('&', 'abril-fatface-400.ttf', 120, (255, 255, 255))
O4 = grad('STYLES', 'anton-400.ttf', 260, SUN, 820); O5 = txt('ke liye', 'montserrat-700.ttf', 74, (255, 255, 255))
HAND = emoji('👆', 120); ft = F('archivo-black-400.ttf', 66)
p = writer('outro.mp4')
for n in range(int(3.6 * FPS)):
    t = n / FPS; c = bg.copy()
    put(c, O1, W / 2, 380, a=min(1, t / 0.2)); put(c, O2, W / 2, 560, sc=spring(t - 0.1))
    put(c, O3, W / 2, 720, a=min(1, max(0, (t - 0.4) / 0.2))); put(c, O4, W / 2, 870, sc=spring(t - 0.45))
    put(c, O5, W / 2, 1040, a=min(1, max(0, (t - 0.8) / 0.2)))
    if t > 1.0:
        k = spring(t - 1.0); pressed = t > 2.1; press = 1 - 0.12 * math.exp(-max(0, t - 2.1) / 0.08) if pressed else 1
        bw, bh = 600 * k * press, 160 * k * press; cx, cy = W / 2, 1250; d = ImageDraw.Draw(c)
        if bw > 10:
            d.rounded_rectangle([cx - bw / 2, cy - bh / 2, cx + bw / 2, cy + bh / 2], bh / 2, fill=(60, 60, 70) if pressed else (0, 149, 246), outline=(255, 255, 255), width=5)
            lab = 'FOLLOWING' if pressed else 'FOLLOW'; lb = ft.getbbox(lab)
            if k > 0.6: d.text((cx - (lb[2] - lb[0]) / 2, cy - (lb[3] - lb[1]) / 2 - lb[1]), lab, font=ft, fill=(255, 255, 255))
        if not pressed: put(c, HAND, cx + 240, cy + 130 + 30 * math.sin(t * 16))
        elif t - 2.1 < 0.6:
            for a_ in range(0, 360, 30):
                r = 330 + 520 * (t - 2.1); x = cx + r * math.cos(math.radians(a_)); y = cy + r * 0.5 * math.sin(math.radians(a_))
                d.ellipse([x - 10, y - 10, x + 10, y + 10], fill=[(255, 200, 70), (255, 90, 120), (120, 220, 255)][a_ // 30 % 3])
    arr = np.array(c.convert('RGB')).astype(np.float32)
    if t > 3.3: arr *= (3.6 - t) / 0.3
    p.stdin.write(np.clip(arr, 0, 255).astype(np.uint8).tobytes())
p.stdin.close(); p.wait(); print('io done')
