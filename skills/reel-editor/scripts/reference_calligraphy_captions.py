"""reference_calligraphy_captions.py — copy a reference reel's scattered Devanagari calligraphy lyric captions onto another
video with the SAME audio (check offset = 0 first), frame-matched.  Example spec = "Lag ja gale" (Best of Lata Mangeshkar) reel.
Workflow: find scene cuts (frame diff) -> 5 fps timestamped contact sheets -> 40 px grid on the final frame of each group ->
fill GROUPS: word, box (x0,y0,x1,y1 on the 720x1280 reference; scaled x1.5), colour, glow, reveal ('fade' | 'burn'), t0, t1,
swash bezier curves (tapered stroke, ring terminal). Rozha One squeezed into the measured box gives the tall condensed look.
'burn' = noisy dissolve with glitter on the front; groups leave with the reference scene crossfade; frame 0 = finished first
group (cover); intro = darkened frames + warm light-leak flashes + Kalam "Best of" fade / name burn.
usage: python3 reference_calligraphy_captions.py target.mov out.mp4 [preview_t ...]"""
import sys, math, subprocess, numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont

W, H, FPS, K = 1080, 1920, 30, 1.5
import os
SRC, OUT = sys.argv[1], sys.argv[2]
HERE = os.path.dirname(os.path.abspath(__file__))
FD = os.path.join(HERE, '..', 'fonts', 'deva', 'rozha-one-devanagari-400.ttf')
FL = os.path.join(HERE, '..', 'fonts', 'kalam-latin-700.ttf')

YEL = ((255, 214, 80), (255, 170, 20)); MINT = ((215, 250, 232), (150, 230, 200)); WHT = ((255, 252, 242), (255, 255, 255))
CRM = ((240, 230, 192), (120, 100, 60)); IYEL = ((255, 196, 60), (255, 150, 0))

# (text, box x0,y0,x1,y1 in ref px, colour, glow strength, reveal, t0, t1, swashes[[4 ctrl pts] , ring_at_end])
GROUPS = [
    dict(on=2.80, off=5.55, words=[
        ('लगजा', (130, 395, 413, 490), YEL, 1.0, 'fade', 2.90, 3.35, [[(262, 358), (285, 280), (370, 268), (372, 398)], [(172, 486), (220, 610), (160, 650), (92, 540)]]),
        ('गले', (434, 545, 603, 640), YEL, 1.0, 'burn', 4.55, 5.00, [[(588, 636), (612, 735), (540, 778), (474, 690)]])]),
    dict(on=5.55, off=7.85, words=[
        ('के', (135, 165, 243, 295), YEL, 1.0, 'fade', 5.62, 5.95, [[(168, 205), (140, 158), (108, 148), (92, 166)]]),
        ('फीर', (232, 244, 482, 445), YEL, 1.0, 'burn', 6.35, 6.95, [[(438, 410), (455, 488), (505, 478), (513, 500)]]),
        ('ये', (477, 532, 596, 690), YEL, 1.0, 'fade', 7.05, 7.35, [[(500, 548), (470, 520), (430, 518), (402, 533)]])]),
    dict(on=7.85, off=14.65, words=[
        ('हसी', (85, 372, 258, 512), MINT, 0.8, 'fade', 7.95, 8.50, [[(236, 380), (275, 330), (298, 300), (284, 296)]]),
        ('रात', (258, 120, 432, 266), MINT, 0.8, 'burn', 9.35, 9.90, [[(405, 262), (472, 330), (420, 425), (345, 305)]]),
        ('हो', (302, 532, 432, 717), MINT, 0.8, 'fade', 10.35, 10.85, []),
        ('नाहो', (378, 405, 628, 608), MINT, 0.8, 'burn', 11.75, 12.30, [[(565, 602), (605, 645), (645, 622), (628, 598)]])]),
    dict(on=14.70, off=19.15, words=[
        ('सायद', (67, 190, 297, 300), WHT, 0.75, 'fade', 14.85, 15.30, [[(272, 300), (300, 345), (238, 348), (250, 318)]]),
        ('फीर', (238, 337, 460, 520), IYEL, 1.0, 'fade', 15.80, 16.30, [[(245, 425), (150, 320), (38, 420), (44, 494)], [(452, 488), (470, 545), (503, 540), (492, 522)]]),
        ('इस', (449, 559, 640, 690), IYEL, 1.0, 'fade', 16.50, 16.90, [[(628, 690), (652, 742), (600, 742), (610, 722)]]),
        ('जनम', (107, 537, 400, 651), WHT, 0.75, 'burn', 17.25, 17.75, [[(112, 600), (70, 560), (108, 520), (140, 538)]])]),
    dict(on=19.20, off=99, words=[
        ('मुलाकात', (74, 100, 590, 262), CRM, 0.35, 'burn', 19.65, 20.45, [[(232, 262), (252, 425), (120, 432), (95, 318)], [(560, 262), (642, 385), (540, 452), (410, 318)]]),
        ('हो', (503, 530, 622, 717), CRM, 0.35, 'fade', 21.50, 22.00, [[(600, 700), (640, 705), (625, 728), (603, 716)]]),
        ('नाहो', (313, 836, 606, 1091), CRM, 0.35, 'burn', 22.75, 23.25, [[(590, 1052), (622, 1102), (562, 1112), (546, 1094)]])]),
]
INTRO = [('Best of', (81, 385, 353, 472), 'fade', 0.35, 0.62), ('Lata', (282, 516, 418, 575), 'burn', 1.15, 1.62),
         ('Mangeshkar', (284, 630, 649, 706), 'burn', 1.18, 1.66)]
INTRO_OFF = 2.78
ORANGE = ((255, 196, 50), (255, 140, 0))


def bez(p, n=120):
    p = np.array(p, float) * K; t = np.linspace(0, 1, n)[:, None]
    return ((1 - t) ** 3) * p[0] + 3 * ((1 - t) ** 2) * t * p[1] + 3 * (1 - t) * t * t * p[2] + t ** 3 * p[3]


def word_mask(txt, box, font_path, sw, SW=6):
    """text squeezed into the measured box (keeps the tall condensed look) + tapered swashes with ring ends."""
    x0, y0, x1, y1 = [v * K for v in box]
    f = ImageFont.truetype(font_path, 260, layout_engine=ImageFont.Layout.RAQM)
    bb = f.getbbox(txt, stroke_width=SW)
    im = Image.new('L', (bb[2] - bb[0] + 20, bb[3] - bb[1] + 20), 0)
    ImageDraw.Draw(im).text((10 - bb[0], 10 - bb[1]), txt, font=f, fill=255, stroke_width=SW, stroke_fill=255)
    im = im.resize((int(x1 - x0), int(y1 - y0)), Image.LANCZOS)
    m = np.zeros((H, W), np.float32)
    m[int(y0):int(y0) + im.height, int(x0):int(x0) + im.width] = np.asarray(im, np.float32) / 255
    for s in sw:
        pts = bez(s); n = len(pts)
        for i in range(n - 1):
            wdt = 3 + 19 * math.sin(math.pi * (0.15 + 0.7 * i / n))          # thick in the middle, hairline ends
            cv2.line(m, tuple(np.int32(pts[i])), tuple(np.int32(pts[i + 1])), 1.0, max(1, int(wdt)), cv2.LINE_AA)
        cv2.circle(m, tuple(np.int32(pts[-1])), 11, 1.0, 4, cv2.LINE_AA)        # little ring terminal
    return np.clip(m, 0, 1)


def make_layer(mask, col, glow):
    fill, gcol = np.array(col[0], np.float32) / 255, np.array(col[1], np.float32) / 255
    yy = np.linspace(0, 1, H)[:, None, None]
    g = cv2.GaussianBlur(mask, (0, 0), 14) * glow + cv2.GaussianBlur(mask, (0, 0), 40) * glow * 0.6
    sh = np.clip(cv2.GaussianBlur(mask, (0, 0), 9) * 0.85, 0, 0.8)
    noise = cv2.GaussianBlur(np.random.default_rng(int(mask.sum()) % 999).random((H, W)).astype(np.float32), (0, 0), 7)
    noise = (noise - noise.min()) / (noise.max() - noise.min())
    return dict(m=mask, fill=fill, g=g, gcol=gcol, sh=sh, noise=noise, ys=np.nonzero(mask.sum(1))[0], xs=np.nonzero(mask.sum(0))[0])


def ease(x): x = min(max(x, 0), 1); return x * x * (3 - 2 * x)


def compose(base, L, a, kind, p):
    """a = overall opacity, p = reveal progress."""
    if a <= 0 or p <= 0: return base
    y0, y1 = max(0, L['ys'][0] - 120), min(H, L['ys'][-1] + 120); x0, x1 = max(0, L['xs'][0] - 120), min(W, L['xs'][-1] + 120)
    sl = (slice(y0, y1), slice(x0, x1))
    m, g, sh = L['m'][sl], L['g'][sl], L['sh'][sl]
    spark = None
    if kind == 'fade':
        al = ease(p) * a
        if p < 1: m = cv2.GaussianBlur(m, (0, 0), 0.1 + 4 * (1 - p))
    else:                                                   # burn-in: noisy dissolve + glitter on the front
        nz = L['noise'][sl]; thr = p * 1.12
        vis = np.clip((thr - nz) / 0.04, 0, 1)
        front = np.clip(1 - np.abs(nz - thr) / 0.025, 0, 1) * (p < 1)
        spark = cv2.dilate(front * (cv2.dilate(L['m'][sl], np.ones((9, 9), np.uint8)) > 0), np.ones((3, 3), np.uint8))
        m, g, sh = m * vis, g * (0.3 + 0.7 * p), sh * vis
        al = a
    b = base[sl]
    b = b * (1 - sh[..., None] * al)                                         # soft dark shadow under the text
    b = 1 - (1 - b) * (1 - np.clip(g[..., None] * L['gcol'] * al, 0, 1))      # glow (screen)
    b = b * (1 - m[..., None] * al) + L['fill'] * m[..., None] * al          # fill
    if spark is not None:
        b = np.clip(b + spark[..., None] * np.array([1, .95, .8], np.float32) * 1.2 * a, 0, 1)
    base[sl] = b
    return base


def leak(t):
    """warm light-leak flashes of the reference intro."""
    keys = [(0.13, 0.0), (0.2, 0.75), (0.4, 0.95), (0.6, 0.6), (0.72, 0.0), (1.55, 0.0), (1.63, 0.8), (1.8, 0.95), (2.0, 0.7), (2.1, 0.0)]
    for (ta, va), (tb, vb) in zip(keys, keys[1:]):
        if ta <= t < tb: return va + (vb - va) * (t - ta) / (tb - ta)
    return 0.0


print('building layers', flush=True)
LAY = []
for gi, gdef in enumerate(GROUPS):
    for (txt, box, col, glow, kind, t0, t1, sw) in gdef['words']:
        LAY.append(dict(L=make_layer(word_mask(txt, box, FD, sw), col, glow), kind=kind, t0=t0, t1=t1, on=gdef['on'], off=gdef['off'], g=gi))
ILAY = [dict(L=make_layer(word_mask(txt, box, FL, [], SW=3), ORANGE, 1.2), kind=k, t0=t0, t1=t1) for txt, box, k, t0, t1 in INTRO]
YY, XX = np.mgrid[0:H, 0:W].astype(np.float32)
LEAK = np.clip(1 - np.sqrt(((XX - W * 0.2) / (W * 0.9)) ** 2 + ((YY - H * 0.15) / (H * 0.7)) ** 2), 0, 1)[..., None]


def frame(img, t):
    f = img.astype(np.float32) / 255
    if t < 0.1:                                             # cover frame = finished first group (thumbnail hook)
        for l in LAY:
            if l['g'] == 0: f = compose(f, l['L'], 1, 'fade', 1)
        return f
    if t < INTRO_OFF:
        dk = 0.86 * ease((t - 0.1) / 0.08) * (1 - ease((t - INTRO_OFF + 0.06) / 0.06))
        f = f * (1 - dk)
        lv = leak(t)
        if lv > 0:
            col = np.array([1.0, 0.45, 0.12]) if (t < 0.3 or 1.55 < t < 1.7) else (np.array([1.0, 0.95, 0.85]) if (0.3 < t < 0.5 or 1.7 < t < 1.9) else np.array([0.75, 0.12, 0.05]))
            f = 1 - (1 - f) * (1 - LEAK * col * lv)
        for l in ILAY:
            p = (t - l['t0']) / (l['t1'] - l['t0'])
            if p > 0: f = compose(f, l['L'], 1, l['kind'], min(1, p))
        return f
    for l in LAY:
        if not (l['on'] - 0.01 <= t < l['off'] + 0.2): continue
        p = (t - l['t0']) / (l['t1'] - l['t0'])
        a = 1 - ease((t - l['off']) / 0.2)                  # leaves with the scene crossfade
        if p > 0: f = compose(f, l['L'], a, l['kind'], min(1, p))
    return f


def frames():
    c = cv2.VideoCapture(SRC)
    while True:
        ok, x = c.read()
        if not ok: return
        yield cv2.cvtColor(x, cv2.COLOR_BGR2RGB)


if __name__ == '__main__':
    if len(sys.argv) > 3:
        want = {int(round(float(s) * FPS)): s for s in sys.argv[3:]}
        for i, img in enumerate(frames()):
            if i in want:
                Image.fromarray((frame(img, i / FPS) * 255).astype(np.uint8)).resize((360, 640)).save(f'pv_{want[i]}.jpg')
            if i > max(want): break
        sys.exit()
    p = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                          '-i', SRC, '-map', '0:v', '-map', '1:a', '-c:v', 'libx264', '-preset', 'slow', '-crf', '19', '-pix_fmt', 'yuv420p',
                          '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', OUT], stdin=subprocess.PIPE)
    for i, img in enumerate(frames()):
        p.stdin.write((frame(img, i / FPS) * 255 + 0.5).astype(np.uint8).tobytes())
        if i % 150 == 0: print(i, flush=True)
    p.stdin.close(); p.wait(); print('done')
