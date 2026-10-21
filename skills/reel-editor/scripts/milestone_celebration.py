"""milestone_celebration.py — 10 s follower-milestone reel (e.g. 1K) from two Instagram screenshots.
Gold "1K" hero on frame 0 -> flies up as header; profile card pops in (ease-out-back) with a pulsing ring on the
followers count + sticker; dashboard card pops in with row highlights + "1.2M VIEWS" / "+547 NEW" pop-up pills;
"शुक्रिया" finale. Glitter twinkles, falling confetti, gold particle bursts on every pop, maroon/gold loop background.
usage: python3 milestone_celebration.py profile.png dashboard.jpg background.png out.mp4 [preview_t ...]
Edit the CROP / HL boxes (source-pixel coords) and the text constants for a new milestone.
NEVER commit the screenshots (personal media)."""
import sys, math, subprocess, numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import os, types
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import still_loops as loops                    # maroon/gold particle background loop
PROFILE, DASH, BG, OUTF = sys.argv[1:5]
loops.ARGS = types.SimpleNamespace(image=BG)

W, H, FPS, DUR = 1080, 1920, 30, 10.0
F = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'fonts') + '/'
GOLD = (255, 205, 110); CREAM = (255, 244, 225)
R = np.random.default_rng(3)

f900 = lambda s: ImageFont.truetype(F + 'montserrat-900.ttf', s)
f700 = lambda s: ImageFont.truetype(F + 'montserrat-700.ttf', s)
fdev = lambda s: ImageFont.truetype(F + 'deva/baloo-2-devanagari-800.ttf', s, layout_engine=ImageFont.Layout.RAQM)
fgv = ImageFont.truetype(F + 'great-vibes-400.ttf', 120)


def eob(x):                                     # ease-out-back
    x = min(max(x, 0), 1); c1 = 1.9; c3 = c1 + 1
    return 1 + c3 * (x - 1) ** 3 + c1 * (x - 1) ** 2


def eio(x):
    x = min(max(x, 0), 1); return x * x * (3 - 2 * x)


def gold_text(txt, font, glow=18, grad=((255, 236, 170), (232, 160, 50)), stroke=0):
    bb = font.getbbox(txt, stroke_width=stroke); pad = glow * 3
    w, h = bb[2] - bb[0] + 2 * pad, bb[3] - bb[1] + 2 * pad
    m = Image.new('L', (w, h), 0)
    ImageDraw.Draw(m).text((pad - bb[0], pad - bb[1]), txt, font=font, fill=255, stroke_width=stroke, stroke_fill=255)
    g = np.linspace(0, 1, h)[:, None, None]
    col = (np.array(grad[0]) * (1 - g) + np.array(grad[1]) * g) * np.ones((1, w, 1))
    fill = Image.fromarray(col.astype(np.uint8)).convert('RGBA'); fill.putalpha(m)
    out = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    if glow:
        gl = Image.new('RGBA', (w, h), (255, 170, 60, 0)); gl.putalpha(m.filter(ImageFilter.GaussianBlur(glow)).point(lambda v: int(v * 0.9)))
        sh = Image.new('RGBA', (w, h), (0, 0, 0, 0)); sh.putalpha(m.filter(ImageFilter.GaussianBlur(8)).point(lambda v: int(v * 0.7)))
        out.alpha_composite(sh, (4, 8)); out.alpha_composite(gl)
    out.alpha_composite(fill)
    return out


def plain_text(txt, font, fill, shadow=True):
    bb = font.getbbox(txt); pad = 24
    im = Image.new('RGBA', (bb[2] - bb[0] + 2 * pad, bb[3] - bb[1] + 2 * pad), (0, 0, 0, 0))
    if shadow:
        s = Image.new('RGBA', im.size, (0, 0, 0, 0))
        ImageDraw.Draw(s).text((pad - bb[0] + 3, pad - bb[1] + 5), txt, font=font, fill=(0, 0, 0, 190))
        im.alpha_composite(s.filter(ImageFilter.GaussianBlur(5)))
    ImageDraw.Draw(im).text((pad - bb[0], pad - bb[1]), txt, font=font, fill=fill)
    return im


def card(path, box, width, hl):
    """crop screenshot -> rounded card with gold border; hl = list of boxes (source coords) -> card coords."""
    im = Image.open(path).convert('RGB').crop(box)
    s = width / im.width; im = im.resize((width, int(im.height * s)), Image.LANCZOS)
    w, h = im.size; b = 8
    out = Image.new('RGBA', (w + 2 * b + 60, h + 2 * b + 60), (0, 0, 0, 0))
    sh = Image.new('RGBA', out.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle((30, 42, 30 + w + 2 * b, 42 + h + 2 * b), 44, fill=(0, 0, 0, 200))
    out.alpha_composite(sh.filter(ImageFilter.GaussianBlur(18)))
    ImageDraw.Draw(out).rounded_rectangle((30, 30, 30 + w + 2 * b, 30 + h + 2 * b), 44, fill=GOLD + (255,))
    m = Image.new('L', (w, h), 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, w, h), 38, fill=255)
    out.paste(im, (30 + b, 30 + b), m)
    boxes = [((x0 - box[0]) * s + 30 + b, (y0 - box[1]) * s + 30 + b, (x1 - box[0]) * s + 30 + b, (y1 - box[1]) * s + 30 + b)
             for x0, y0, x1, y1 in hl]
    return out, boxes


C_PROF, HL_PROF = card(PROFILE, (0, 350, 1179, 1030), 960, [(570, 495, 815, 625)])
C_DASH, HL_DASH = card(DASH, (0, 470, 1179, 1290), 960, [(30, 880, 1150, 980), (30, 1030, 1150, 1125)])


def pill(txt, bg=(245, 166, 35), fg=(40, 8, 0), size=54):
    f = f900(size); bb = f.getbbox(txt); w, h = bb[2] - bb[0] + 70, bb[3] - bb[1] + 44
    im = Image.new('RGBA', (w + 40, h + 40), (0, 0, 0, 0))
    s = Image.new('RGBA', im.size, (0, 0, 0, 0)); ImageDraw.Draw(s).rounded_rectangle((20, 28, 20 + w, 28 + h), h // 2, fill=(0, 0, 0, 170))
    im.alpha_composite(s.filter(ImageFilter.GaussianBlur(8)))
    d = ImageDraw.Draw(im); d.rounded_rectangle((20, 20, 20 + w, 20 + h), h // 2, fill=bg + (255,), outline=(255, 245, 210, 255), width=4)
    d.text((20 + 35 - bb[0], 20 + 22 - bb[1]), txt, font=f, fill=fg)
    return im


T_1K = gold_text('1K', f900(430), glow=30)
T_FOL = gold_text('FOLLOWERS', f900(84), glow=12, grad=((255, 250, 235), (255, 214, 140)))
T_FAM = gold_text('1K FAMILY', f900(92), glow=14)
P_VIEWS, P_NEW, P_1000 = pill('1.2M VIEWS'), pill('+547 NEW'), pill('1,000!', bg=(255, 236, 170))
T_SHUK = gold_text('शुक्रिया', fdev(190), glow=22)
def mix(segs, fill):
    ims = [plain_text(t, f, fill) for t, f in segs]
    w = sum(i.width - 48 for i in ims) + 48; h = max(i.height for i in ims)
    out = Image.new('RGBA', (w, h), (0, 0, 0, 0)); x = 0
    base = max(f.getbbox(t)[3] for t, f in segs)
    for (t, f), i in zip(segs, ims):
        out.alpha_composite(i, (x, h - i.height - (base - f.getbbox(t)[3]))); x += i.width - 48
    return out
T_PARI = mix([('1000 ', f700(62)), ('लोगों के परिवार का', fdev(64))], CREAM)
T_TY = gold_text('Thank you for the love', fgv, glow=10, grad=((255, 248, 230), (255, 214, 150)))
T_HANDLE = plain_text('@aitricksbysumit', f700(40), (255, 255, 255, 235))
T_GOAL = plain_text('Target tha 500 … pahunch gaye 1000', f700(40), CREAM)


def place(cv, im, cx, cy, sc=1.0, a=1.0, rot=0):
    if sc <= 0.02 or a <= 0.01: return
    if sc != 1: im = im.resize((max(1, int(im.width * sc)), max(1, int(im.height * sc))), Image.BILINEAR)
    if rot: im = im.rotate(rot, resample=Image.BICUBIC, expand=True)
    if a < 1: im = im.copy(); im.putalpha(im.getchannel('A').point(lambda v: int(v * a)))
    cv.alpha_composite(im, (int(cx - im.width / 2), int(cy - im.height / 2)))


# ---------------- particles ----------------
NS = 110
gx, gy = R.uniform(0, W, NS), R.uniform(0, H, NS); gf, gp, gs = R.uniform(0.6, 2.2, NS), R.uniform(0, 6.3, NS), R.uniform(10, 26, NS)
NC = 170
CC = [(255, 205, 110), (245, 166, 35), (255, 250, 240), (236, 72, 120), (255, 120, 60), (180, 120, 255)]
cx0, cy0 = R.uniform(0, W, NC), R.uniform(-H, 0, NC); cv_ = R.uniform(180, 380, NC); cw_ = R.uniform(0, 6.3, NC)
cr, crs = R.uniform(0, 6.3, NC), R.uniform(-6, 6, NC); ccol = R.integers(0, len(CC), NC); csz = R.uniform(10, 22, NC)
BURSTS = [(0.12, W / 2, 820, 70), (2.25, None, 'prof', 50), (5.55, None, 'd0', 45), (6.35, None, 'd1', 45), (7.95, W / 2, 900, 80)]
BP = {}


def glitter(L, t, dens=1.0):
    for k in range(int(NS * dens)):
        b = max(0.0, math.sin(2 * math.pi * gf[k] * t + gp[k])) ** 6
        if b < 0.05: continue
        x, y, s = int(gx[k]), int(gy[k]), gs[k] * (0.6 + 0.4 * b)
        cv2.line(L, (int(x - s), y), (int(x + s), y), (b, b * .85, b * .55), 2, cv2.LINE_AA)
        cv2.line(L, (x, int(y - s)), (x, int(y + s)), (b, b * .85, b * .55), 2, cv2.LINE_AA)
        cv2.circle(L, (x, y), 3, (b, b, b * .8), -1, cv2.LINE_AA)


def confetti(arr, t, start, amount):
    n = int(NC * amount)
    for k in range(n):
        tt = t - start
        if tt < 0: continue
        y = cy0[k] + cv_[k] * tt * 1.6 + 300
        if y < -40 or y > H + 40: continue
        x = cx0[k] + 40 * math.sin(tt * 2.3 + cw_[k])
        a = cr[k] + crs[k] * tt; s = csz[k]; sq = abs(math.cos(tt * 5 + cw_[k]))
        pts = np.array([[math.cos(a) * s - math.sin(a) * s * .45 * sq, math.sin(a) * s + math.cos(a) * s * .45 * sq] for a in [a, a + math.pi]])
        p = np.array([[x + dx * sgn, y + dy * sgn] for sgn in (1, -1) for dx, dy in [(math.cos(a) * s, math.sin(a) * s)]] )
        ca, sa = math.cos(a), math.sin(a)
        quad = np.array([[x + ca * s - sa * s * .45 * sq, y + sa * s + ca * s * .45 * sq], [x + ca * s + sa * s * .45 * sq, y + sa * s - ca * s * .45 * sq],
                         [x - ca * s + sa * s * .45 * sq, y - sa * s - ca * s * .45 * sq], [x - ca * s - sa * s * .45 * sq, y - sa * s + ca * s * .45 * sq]], np.int32)
        cv2.fillConvexPoly(arr, quad, CC[ccol[k]], cv2.LINE_AA)


def bursts(L, t, anchors):
    for i, (t0, x, y, n) in enumerate(BURSTS):
        if isinstance(y, str): x, y = anchors.get(y, (None, None))
        if x is None: continue
        tt = t - t0
        if tt < 0 or tt > 1.3: continue
        if i not in BP:
            r = np.random.default_rng(i); BP[i] = (r.uniform(0, 6.3, n), r.uniform(380, 1100, n), r.uniform(3, 8, n))
        ang, sp, sz = BP[i]
        fade = (1 - tt / 1.3) ** 1.5
        for k in range(n):
            px = x + math.cos(ang[k]) * sp[k] * tt * (1 - tt * 0.35)
            py = y + math.sin(ang[k]) * sp[k] * tt * (1 - tt * 0.35) + 420 * tt * tt
            c = (fade, fade * 0.82, fade * 0.45)
            cv2.circle(L, (int(px), int(py)), int(sz[k]), c, -1, cv2.LINE_AA)


def frame(t, bgf):
    cv = Image.fromarray((np.clip(bgf * 0.85, 0, 1) * 255).astype(np.uint8)).convert('RGBA')
    anchors = {}
    # ---- 1K hero (visible on frame 0), then flies up to become the header
    k = eio((t - 1.25) / 0.45)
    if t < 1.25:
        sc = 1 + 0.04 * math.sin(t * 7) + 0.12 * max(0, 1 - t / 0.25)
        place(cv, T_1K, W / 2, 800, sc)
        place(cv, T_FOL, W / 2, 1080, 1, 1)
        place(cv, T_GOAL, W / 2, 1200, 1, eio((t - 0.45) / 0.4) * (1 - eio((t - 1.05) / 0.2)))
    elif t < 7.7:
        place(cv, T_1K, W / 2, 800 + (300 - 800) * k, 1 + (0.38 - 1) * k, 1 - k * (t < 1.7) * 0.0)
        place(cv, T_FOL, W / 2, 1080 + (470 - 1080) * k, 1 + (0.6 - 1) * k, 1)
    # ---- profile card
    if 1.5 <= t < 4.75:
        a = eob((t - 1.5) / 0.5); out = eio((t - 4.45) / 0.3)
        sc = a * (1 - out); cy = 1020
        place(cv, C_PROF, W / 2, cy, sc, 1, rot=-3 * (1 - eio((t - 1.5) / 0.6)))
        x0, y0, x1, y1 = HL_PROF[0]
        hx = W / 2 + ((x0 + x1) / 2 - C_PROF.width / 2) * sc; hy = cy + ((y0 + y1) / 2 - C_PROF.height / 2) * sc
        anchors['prof'] = (hx, hy)
        if t > 2.1 and sc > 0.5:
            p = 0.5 + 0.5 * math.sin((t - 2.1) * 9)
            ring = Image.new('RGBA', cv.size, (0, 0, 0, 0)); rw, rh = (x1 - x0) * sc / 2 + 14 + 8 * p, (y1 - y0) * sc / 2 + 12 + 8 * p
            ImageDraw.Draw(ring).rounded_rectangle((hx - rw, hy - rh, hx + rw, hy + rh), 30, outline=(255, 214, 110, 255), width=8)
            cv.alpha_composite(ring.filter(ImageFilter.GaussianBlur(1.2)))
            place(cv, P_1000, hx + 120, cy - C_PROF.height * sc / 2 + 10, eob((t - 2.25) / 0.35) * (1 - out), 1, rot=6)
    # ---- dashboard card with two pop-up stickers
    if 4.75 <= t < 7.85:
        a = eob((t - 4.75) / 0.5); out = eio((t - 7.5) / 0.3)
        sc = a * (1 - out); cy = 1080
        place(cv, C_DASH, W / 2, cy, sc, 1, rot=3 * (1 - eio((t - 4.75) / 0.6)))
        for i, (x0, y0, x1, y1) in enumerate(HL_DASH):
            hx = W / 2 + ((x0 + x1) / 2 - C_DASH.width / 2) * sc; hy = cy + ((y0 + y1) / 2 - C_DASH.height / 2) * sc
            anchors['d%d' % i] = (W / 2 + (x1 - C_DASH.width / 2) * sc - 120, hy)
            ts = 5.5 + 0.8 * i
            if t > ts and sc > 0.5:
                hl = Image.new('RGBA', cv.size, (0, 0, 0, 0))
                ImageDraw.Draw(hl).rounded_rectangle((W / 2 + (x0 - C_DASH.width / 2) * sc, hy - (y1 - y0) * sc / 2,
                                                      W / 2 + (x1 - C_DASH.width / 2) * sc, hy + (y1 - y0) * sc / 2), 22,
                                                     outline=(255, 214, 110, int(255 * min(1, (t - ts) / 0.2))), width=7)
                cv.alpha_composite(hl)
                place(cv, [P_VIEWS, P_NEW][i], W / 2 + (230 if i == 0 else -220), hy - 120 if i == 0 else hy + 120,
                      eob((t - ts) / 0.35) * (1 - out), 1, rot=-7 if i == 0 else 6)
    # ---- thank-you finale
    if t >= 7.75:
        place(cv, T_SHUK, W / 2, 760, eob((t - 7.75) / 0.5))
        place(cv, T_PARI, W / 2, 935, 1, eio((t - 8.15) / 0.4))
        place(cv, T_TY, W / 2, 1070, 1, eio((t - 8.5) / 0.5))
        place(cv, T_FAM, W / 2, 1260, eob((t - 8.9) / 0.45))
        place(cv, T_HANDLE, W / 2, 1400, 1, eio((t - 9.1) / 0.4))
    arr = np.asarray(cv.convert('RGB')).copy()
    confetti(arr, t, 0.0, 0.55); confetti(arr, t, 7.75, 1.0) if t > 7.75 else None
    L = np.zeros((H, W, 3), np.float32)
    glitter(L, t, 1.0); bursts(L, t, anchors)
    L = cv2.GaussianBlur(L, (0, 0), 1.0) + cv2.GaussianBlur(L, (0, 0), 6) * 1.5
    out = arr.astype(np.float32) / 255
    out = 1 - (1 - out) * (1 - np.clip(L * np.array([1, 0.92, 0.75], np.float32), 0, 1))
    if t < 0.12: out = out + (0.12 - t) / 0.12 * 0.12               # flash on the very first beat
    return np.clip(out, 0, 1)


def bg_frames():
    while True:
        for f in loops.outro_frames(6.0): yield f


if __name__ == '__main__':
    if len(sys.argv) > 5:
        g = bg_frames(); bgf = next(g)
        for ts in sys.argv[5:]:
            Image.fromarray((frame(float(ts), bgf) * 255).astype(np.uint8)).resize((540, 960)).save(f'prev_{ts}.jpg')
        sys.exit()
    p = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS),
                          '-i', '-', '-f', 'lavfi', '-i', 'anullsrc=r=44100:cl=stereo', '-shortest', '-c:v', 'libx264', '-preset', 'slow',
                          '-crf', '19', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-movflags', '+faststart', OUTF], stdin=subprocess.PIPE)
    g = bg_frames()
    for i in range(int(DUR * FPS)):
        p.stdin.write((frame(i / FPS, next(g)) * 255 + 0.5).astype(np.uint8).tobytes())
    p.stdin.close(); p.wait(); print('done')
