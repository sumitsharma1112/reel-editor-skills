"""still_loops.py — turn still images into seamless, reusable 9:16 loop clips (no AI video needed).

Every effect is periodic in time with period T, so frame T == frame 0 and the clip loops forever.
Tricks used:
  * periodic noise   N(t) = A*cos(2πt/T) + B*sin(2πt/T)   (A, B = smooth random fields)
  * crossfade drift  F(t) = (1-t/T)*L(v*t) + (t/T)*L(v*(t-T))  -> a drifting layer that loops
  * lifespan cycling age = (t - birth) mod T                  -> particles / drops that loop

usage:
  python3 still_loops.py smoke  smoke_on_black.png loop_smoke.mp4        # incense smoke on pure black (tip ~86% down)
  python3 still_loops.py moon   moon_clouds.png    loop_moon.mp4
  python3 still_loops.py rain   rain_window.png    loop_rain.mp4
  python3 still_loops.py outro  maroon_gold.png    loop_outro_bg.mp4
  python3 still_loops.py follow maroon_gold.png    outro_follow.mp4 --handle @aitricksbysumit --line "ऐसी और रील्स के लिए"
Options: --seconds T (loop length; defaults smoke/rain/outro 6, moon 8, follow 5)
Start images: generate 9:16 stills in ChatGPT/any image model with an empty area for text; no text in the image.
"""
import sys, subprocess, math, numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 1080, 1920, 30
import os, argparse
FONTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'fonts') + '/'
ARGS = None
rng = np.random.default_rng(7)


def load(p):
    im = Image.open(ARGS.image).convert('RGB').resize((W, H), Image.LANCZOS)
    return np.asarray(im).astype(np.float32) / 255.0


def smooth_field(scale, h=H, w=W, seed=None):
    """smooth random field in [-1,1], feature size ~ scale px (tileable, FFT low-pass)."""
    r = np.random.default_rng(seed)
    z = r.standard_normal((h, w)).astype(np.float32)
    fy = np.fft.fftfreq(h)[:, None]; fx = np.fft.fftfreq(w)[None, :]
    g = np.exp(-((fx ** 2 + fy ** 2) * (scale ** 2)) * 2.0)
    f = np.real(np.fft.ifft2(np.fft.fft2(z) * g)).astype(np.float32)
    return f / (np.abs(f).max() + 1e-9)


def fbm(h, w, seed, beta=1.9):
    """tileable cloud texture in [0,1]."""
    r = np.random.default_rng(seed)
    z = r.standard_normal((h, w))
    fy = np.fft.fftfreq(h)[:, None]; fx = np.fft.fftfreq(w)[None, :]
    k = np.sqrt(fx ** 2 + fy ** 2); k[0, 0] = 1
    f = np.real(np.fft.ifft2(np.fft.fft2(z) / k ** beta))
    f = (f - f.min()) / (f.max() - f.min())
    return f.astype(np.float32)


def writer(name, dur):
    return subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24',
                             '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-preset', 'slow',
                             '-crf', '19', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', ARGS.out],
                            stdin=subprocess.PIPE)


def emit(p, f):
    p.stdin.write((np.clip(f, 0, 1) * 255 + 0.5).astype(np.uint8).tobytes())


GX, GY = np.meshgrid(np.arange(W, dtype=np.float32), np.arange(H, dtype=np.float32))


def warp(img, dx, dy):
    return cv2.remap(img, GX + dx, GY + dy, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)


# ---------------------------------------------------------------- smoke
def smoke(T=6.0):
    img = load('g_smoke.png')
    tip = int(H * 0.865)                                   # incense tip — below it nothing moves
    yy = np.clip((tip - GY) / tip, 0, 1)                   # 0 at tip, 1 at top
    amp = (yy ** 1.3) * 46.0                               # wisps sway more as they rise
    Ax, Bx = smooth_field(260, seed=1), smooth_field(260, seed=2)
    Ay, By = smooth_field(320, seed=3), smooth_field(320, seed=4)
    Cx, Dx = smooth_field(110, seed=5), smooth_field(110, seed=6)
    p = writer('loop_smoke.mp4', T)
    n = int(T * FPS)
    for i in range(n):
        th = 2 * math.pi * i / n
        c, s = math.cos(th), math.sin(th)
        dx = amp * (Ax * c + Bx * s) + amp * 0.35 * (Cx * math.cos(2 * th) + Dx * math.sin(2 * th))
        # upward travelling ripple: phase moves up the column once per loop
        dx += amp * 0.35 * np.sin(GY / 210.0 * 2 * math.pi + th)
        dy = amp * 0.45 * (Ay * c + By * s) + yy * 10 * math.sin(th)
        f = warp(img, dx, dy)
        f *= 1.0 + 0.05 * math.sin(th * 2)                 # soft breathing glow
        emit(p, f)
    p.stdin.close(); p.wait()


# ---------------------------------------------------------------- moon
def moon(T=8.0):
    img = load('g_moon.png')
    lum = img.mean(2)
    # where the existing clouds are (mid-bright, not the moon disc)
    cloud = np.clip((lum - 0.10) / 0.35, 0, 1) * np.clip((0.85 - lum) / 0.2, 0, 1)
    cloud = cv2.GaussianBlur(cloud, (0, 0), 6)
    Ax, Bx = smooth_field(220, seed=11), smooth_field(220, seed=12)
    # drifting mist layer: tileable fbm, wider than frame
    mist = fbm(H // 2, W, seed=13)
    mist = cv2.resize(mist, (W, H), interpolation=cv2.INTER_CUBIC)
    mist = np.clip((mist - 0.45) / 0.4, 0, 1) ** 1.6
    sky = np.clip(1.0 - GY / (H * 0.62), 0, 1) ** 0.7       # mist mostly in the upper sky
    tint = np.array([0.78, 0.84, 1.0], np.float32)
    # moon glow pulse
    mm = (lum > 0.82).astype(np.float32)
    ys, xs = np.nonzero(mm)
    cx, cy = (xs.mean(), ys.mean()) if len(xs) else (W * 0.58, H * 0.2)
    glow = np.exp(-(((GX - cx) ** 2 + (GY - cy) ** 2) / (2 * 230.0 ** 2)))[..., None]
    # twinkling stars (lower-half sky stays clean for text)
    ns = 70
    sx = rng.uniform(20, W - 20, ns); sy = rng.uniform(15, H * 0.45, ns)
    sph = rng.uniform(0, 2 * math.pi, ns); sk = rng.integers(1, 3, ns); sb = rng.uniform(0.25, 0.8, ns)
    v = W / T * 0.5                                         # px per second of mist drift
    p = writer('loop_moon.mp4', T)
    n = int(T * FPS)
    for i in range(n):
        t = i / FPS; th = 2 * math.pi * i / n
        a = t / T
        m = (1 - a) * np.roll(mist, int(round(v * t)), axis=1) + a * np.roll(mist, int(round(v * (t - T))), axis=1)
        dx = cloud * 14 * (Ax * math.cos(th) + Bx * math.sin(th)) + cloud * 10 * math.sin(th)
        f = warp(img, dx, dx * 0.25)
        f = 1 - (1 - f) * (1 - (m * sky * 0.22)[..., None] * tint)      # screen the mist
        f = f + glow * 0.06 * (0.5 + 0.5 * math.sin(th))
        st = np.zeros((H, W), np.float32)
        for k in range(ns):
            b = sb[k] * (0.5 + 0.5 * math.sin(th * sk[k] + sph[k])) ** 3
            cv2.circle(st, (int(sx[k]), int(sy[k])), 2, float(b), -1, cv2.LINE_AA)
        st = cv2.GaussianBlur(st, (0, 0), 1.2) * 1.6
        f = f + st[..., None] * np.array([0.9, 0.95, 1.0], np.float32)
        emit(p, f)
    p.stdin.close(); p.wait()


# ---------------------------------------------------------------- rain on window
def rain(T=6.0):
    img = load('g_rain.png')
    soft = cv2.GaussianBlur(img, (0, 0), 3)
    lum = img.mean(2)
    hi = cv2.GaussianBlur(np.clip((lum - 0.45) / 0.4, 0, 1), (0, 0), 8)[..., None]
    Ab, Bb = smooth_field(90, seed=21), smooth_field(90, seed=22)
    nd = 34                                                  # sliding drops alive at any time
    birth = rng.uniform(0, T, nd); life = rng.uniform(1.6, 3.4, nd)
    x0 = rng.uniform(40, W - 40, nd); y0 = rng.uniform(-80, H * 0.55, nd)
    spd = rng.uniform(260, 620, nd); rad = rng.uniform(7, 15, nd)
    wob = rng.uniform(0, 2 * math.pi, nd)
    # static beads that slowly "pop in" and stay
    nb = 260
    bx = rng.uniform(0, W, nb); by = rng.uniform(0, H, nb); br = rng.uniform(2, 6, nb); bt = rng.uniform(0, T, nb)
    p = writer('loop_rain.mp4', T)
    n = int(T * FPS)
    for i in range(n):
        t = i / FPS; th = 2 * math.pi * i / n
        hgt = np.zeros((H, W), np.float32)
        for k in range(nb):                                  # beads fade in and out on their own cycle
            age = (t - bt[k]) % T
            a = math.sin(math.pi * age / T) ** 0.5
            cv2.circle(hgt, (int(bx[k]), int(by[k])), int(br[k]), float(a), -1, cv2.LINE_AA)
        for k in range(nd):
            age = (t - birth[k]) % T
            if age > life[k]: continue
            ease = age / life[k]
            y = y0[k] + spd[k] * age * (0.6 + 0.4 * ease)
            x = x0[k] + 9 * math.sin(age * 3 + wob[k])
            fade = min(1, age / 0.15) * min(1, (life[k] - age) / 0.3)
            cv2.ellipse(hgt, (int(x), int(y)), (int(rad[k]), int(rad[k] * 1.35)), 0, 0, 360, float(fade), -1, cv2.LINE_AA)
            tl = int(min(260, spd[k] * age * 0.5))           # wet trail behind the drop
            for j in range(0, tl, 14):
                r = max(1, int(rad[k] * 0.35 * (1 - j / (tl + 1))))
                cv2.circle(hgt, (int(x + 3 * math.sin((y - j) / 40)), int(y - j - rad[k])), r, float(fade * 0.8), -1, cv2.LINE_AA)
        hgt = cv2.GaussianBlur(hgt, (0, 0), 2.2)
        gx = cv2.Sobel(hgt, cv2.CV_32F, 1, 0, ksize=3); gy = cv2.Sobel(hgt, cv2.CV_32F, 0, 1, ksize=3)
        f = warp(soft * 0.5 + img * 0.5, -gx * 55, -gy * 55)     # lens refraction inside drops
        f = img * (1 - np.clip(hgt * 3, 0, 1)[..., None]) + f * np.clip(hgt * 3, 0, 1)[..., None]
        spec = np.clip(-(gx + gy) * 1.6, 0, 1)[..., None]       # light from top-left
        rim = np.clip((gx + gy) * 1.2, 0, 1)[..., None]
        f = f + spec * 0.55 - rim * 0.18
        f = f + hi * img * 0.16 * (Ab * math.cos(th) + Bb * math.sin(th))[..., None]   # bokeh shimmer
        emit(p, f)
    p.stdin.close(); p.wait()


# ---------------------------------------------------------------- outro background
def outro_frames(T=6.0):
    img = load('g_outro.png')
    np_ = 150
    px = rng.uniform(0, W, np_); py = rng.uniform(0, H, np_); pb = rng.uniform(0, T, np_)
    pr = rng.uniform(1.5, 5.5, np_); pv = rng.uniform(40, 160, np_); pw = rng.uniform(0, 6.28, np_)
    col = np.array([1.0, 0.78, 0.42], np.float32)
    cg = np.exp(-(((GX - W / 2) ** 2) / (2 * 380.0 ** 2) + ((GY - H * 0.45) ** 2) / (2 * 560.0 ** 2)))[..., None]
    n = int(T * FPS)
    for i in range(n):
        t = i / FPS; th = 2 * math.pi * i / n
        L = np.zeros((H, W), np.float32)
        for k in range(np_):
            age = (t - pb[k]) % T
            a = math.sin(math.pi * age / T) ** 1.5
            x = px[k] + 18 * math.sin(age * 1.3 + pw[k]); y = py[k] - pv[k] * age
            cv2.circle(L, (int(x), int(y % H)), int(pr[k]), float(a), -1, cv2.LINE_AA)
        L = cv2.GaussianBlur(L, (0, 0), 2.5) * 1.4 + cv2.GaussianBlur(L, (0, 0), 14) * 1.2
        f = img * (1 + 0.07 * math.sin(th)) + cg * 0.05 * (0.5 + 0.5 * math.sin(th))
        f = 1 - (1 - f) * (1 - L[..., None] * col * 0.75)
        yield f


def outro(T=6.0):
    p = writer('loop_outro_bg.mp4', T)
    for f in outro_frames(T): emit(p, f)
    p.stdin.close(); p.wait()


# ---------------------------------------------------------------- follow end-card (on outro bg)
def ease_out_back(x):
    c1 = 1.70158; c3 = c1 + 1
    return 1 + c3 * (x - 1) ** 3 + c1 * (x - 1) ** 2


def clamp01(x): return max(0.0, min(1.0, x))


def text_layer(txt, font, fill, stroke=0, stroke_fill=(0, 0, 0), shadow=True):
    bb = font.getbbox(txt, stroke_width=stroke)
    w, h = bb[2] - bb[0] + 60, bb[3] - bb[1] + 60
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    if shadow:
        sh = Image.new('RGBA', (w, h), (0, 0, 0, 0))
        ImageDraw.Draw(sh).text((30 - bb[0] + 4, 30 - bb[1] + 6), txt, font=font, fill=(0, 0, 0, 170), stroke_width=stroke)
        im = Image.alpha_composite(im, sh.filter(ImageFilter.GaussianBlur(8)))
        d = ImageDraw.Draw(im)
    d.text((30 - bb[0], 30 - bb[1]), txt, font=font, fill=fill, stroke_width=stroke, stroke_fill=stroke_fill)
    return im


def follow(T=5.0, handle='@aitricksbysumit', line='ऐसी और रील्स के लिए'):
    fv = ImageFont.truetype(FONTS + 'great-vibes-400.ttf', 190)
    fh = ImageFont.truetype(FONTS + 'playfair-display-700.ttf', 66)
    fb = ImageFont.truetype(FONTS + 'poppins-700.ttf', 50)
    fd = ImageFont.truetype(FONTS + 'deva/baloo-2-devanagari-800.ttf', 54, layout_engine=ImageFont.Layout.RAQM)
    L_follow = text_layer('Follow', fv, (255, 214, 140, 255))
    L_handle = text_layer(handle, fh, (255, 248, 235, 255))
    L_hindi = text_layer(line, fd, (255, 236, 205, 255))
    bw, bh = 470, 112

    def button(label, on):
        im = Image.new('RGBA', (bw + 60, bh + 60), (0, 0, 0, 0))
        sh = Image.new('RGBA', im.size, (0, 0, 0, 0))
        ImageDraw.Draw(sh).rounded_rectangle((30, 38, 30 + bw, 38 + bh), 56, fill=(0, 0, 0, 150))
        im = Image.alpha_composite(im, sh.filter(ImageFilter.GaussianBlur(10)))
        d = ImageDraw.Draw(im)
        if on:
            d.rounded_rectangle((30, 30, 30 + bw, 30 + bh), 56, fill=(245, 166, 35, 255))
        else:
            d.rounded_rectangle((30, 30, 30 + bw, 30 + bh), 56, fill=(40, 10, 12, 230), outline=(255, 214, 140, 255), width=4)
        tb = fb.getbbox(label)
        tw = tb[2] - tb[0] + (0 if on else 58)               # room for a drawn tick (font has no ✓ glyph)
        x0 = 30 + (bw - tw) / 2
        d.text((x0 - tb[0], 30 + (bh - (tb[3] - tb[1])) / 2 - tb[1]), label, font=fb,
               fill=(40, 8, 0, 255) if on else (255, 236, 205, 255))
        if not on:
            cx = x0 + tb[2] - tb[0] + 22; cy = 30 + bh / 2
            d.line([(cx, cy + 2), (cx + 11, cy + 13), (cx + 32, cy - 12)], fill=(245, 166, 35, 255), width=7, joint='curve')
        return im
    B_on, B_done = button('FOLLOW', True), button('FOLLOWING', False)

    def place(canvas, layer, cx, cy, scale=1.0, alpha=1.0):
        if alpha <= 0 or scale <= 0.01: return
        l = layer
        if abs(scale - 1) > 1e-3:
            l = layer.resize((max(1, int(layer.width * scale)), max(1, int(layer.height * scale))), Image.LANCZOS)
        if alpha < 1:
            a = l.getchannel('A').point(lambda v: int(v * alpha)); l = l.copy(); l.putalpha(a)
        canvas.alpha_composite(l, (int(cx - l.width / 2), int(cy - l.height / 2)))

    p = writer('outro_follow.mp4', T)
    frames = outro_frames(6.0)
    n = int(T * FPS)
    for i in range(n):
        t = i / FPS
        bg = next(frames)
        cv = Image.fromarray((np.clip(bg, 0, 1) * 255).astype(np.uint8)).convert('RGBA')
        k = clamp01((t - 0.15) / 0.55)
        place(cv, L_follow, W / 2, 760 - 40 * (1 - k), 0.7 + 0.3 * ease_out_back(k) if k > 0 else 0, k)
        k = clamp01((t - 0.55) / 0.45)
        place(cv, L_handle, W / 2, 905 + 30 * (1 - k), 1.0, k)
        k = clamp01((t - 0.85) / 0.45)
        place(cv, L_hindi, W / 2, 1000 + 25 * (1 - k), 1.0, k)
        tap = 2.6
        k = clamp01((t - 1.3) / 0.4)
        bs = ease_out_back(k) if k > 0 else 0
        if t >= tap - 0.12 and t < tap: bs *= 0.92                         # press-in
        place(cv, B_on if t < tap else B_done, W / 2, 1160, bs, 1.0)
        if tap <= t < tap + 0.7:                                          # tap ripple
            r = (t - tap) / 0.7
            rip = Image.new('RGBA', cv.size, (0, 0, 0, 0))
            rr = 40 + 260 * r
            ImageDraw.Draw(rip).ellipse((W / 2 - rr, 1160 - rr * 0.45, W / 2 + rr, 1160 + rr * 0.45),
                                        outline=(255, 220, 160, int(220 * (1 - r))), width=6)
            cv.alpha_composite(rip)
        emit(p, np.asarray(cv.convert('RGB')).astype(np.float32) / 255)
    p.stdin.close(); p.wait()


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('kind', choices=['smoke', 'moon', 'rain', 'outro', 'follow'])
    ap.add_argument('image'); ap.add_argument('out')
    ap.add_argument('--seconds', type=float)
    ap.add_argument('--handle', default='@aitricksbysumit')
    ap.add_argument('--line', default='ऐसी और रील्स के लिए')
    ARGS = ap.parse_args()
    fn = dict(smoke=smoke, moon=moon, rain=rain, outro=outro, follow=follow)[ARGS.kind]
    kw = {'T': ARGS.seconds} if ARGS.seconds else {}
    if ARGS.kind == 'follow': kw.update(handle=ARGS.handle, line=ARGS.line)
    fn(**kw); print('wrote', ARGS.out)
