"""Film-burn hook intro (trending 'Save it, it will be useful' style).

The first N seconds of a finished reel are replaced by a black hook card:
- orange/amber film-burn light leaks with sprocket-hole edges sweep and flicker,
- the song's first words appear as a big serif lyric (letter-by-letter fade + flicker),
- top-right Instagram glyph pops in, then the handle and song credit type in, and the
  glyph turns into the Instagram gradient,
- at the end a full-frame burn flash wipes into the video, which continues in sync.
Audio is untouched (the song keeps playing from 0), so the lyric matches the sound.

Usage:
  python film_burn_hook.py in.mp4 out.mp4 --lyric "Ohne kadi gallan" --hook 2.2 \
      --handle @aitricksbysumit --credit "Song name" [--top "Save it, it will be useful"]
"""
import argparse, subprocess, math, os
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__)); FD = os.path.join(HERE, '..', 'fonts')

def burn_layer(W, H, t, rng_seed=7):
    """Return HxW float [0,1] of light-leak intensity at time t."""
    r = np.random.default_rng(rng_seed)
    L = np.zeros((H // 4, W // 4), np.float32); h, w = L.shape
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    for k in range(4):
        sp = r.uniform(0.6, 1.4); ph = r.uniform(0, 6.3); cy = r.uniform(0.2, 0.8) * h
        on = max(0.0, math.sin(t * sp * 3.2 + ph)) ** 1.5 * (0.75 + 0.25 * math.sin(t * 23 + k))
        if on < 0.02: continue
        cx = ((t * sp * 0.6 + r.uniform(0, 1)) % 1.4 - 0.2) * w
        bw, bh = w * r.uniform(0.35, 0.7), h * r.uniform(0.12, 0.3)
        blob = np.exp(-(((xx - cx) / bw) ** 2 + ((yy - cy) / bh) ** 4))
        # sprocket-hole edge on the left of the blob
        holes = ((np.floor(yy / (h * 0.035)) % 2) == 0) & (np.abs(xx - (cx - bw * 0.55)) < w * 0.025)
        blob = blob * (1 - 0.8 * holes * (blob > 0.3))
        L = np.maximum(L, blob * on)
    L = cv2.GaussianBlur(L, (0, 0), 1.5)
    return cv2.resize(L, (W, H), interpolation=cv2.INTER_LINEAR)

def burn_colour(I):
    # dark red -> orange -> pale yellow as intensity rises (BGR)
    I = np.clip(I, 0, 1)[..., None]
    c1, c2, c3 = np.array([0, 30, 170.]), np.array([0, 110, 255.]), np.array([90, 210, 255.])
    return np.where(I < 0.5, c1 + (c2 - c1) * (I / 0.5), c2 + (c3 - c2) * ((I - 0.5) / 0.5)) * np.minimum(1, I * 1.6)

def text_rgba(W, txt, font, size, fill, align='center', pad=10):
    f = ImageFont.truetype(os.path.join(FD, font), size); im = Image.new('RGBA', (W, int(size * 1.5) + pad)); d = ImageDraw.Draw(im)
    tw = d.textlength(txt, font=f); x = (W - tw) / 2 if align == 'center' else (W - tw - 48)
    d.text((x, pad // 2), txt, font=f, fill=fill)
    a = np.asarray(im, np.float32); return a[..., 2::-1], a[..., 3:] / 255

def ig_glyph(s, gradient):
    im = Image.new('RGBA', (s, s)); d = ImageDraw.Draw(im); lw = max(3, s // 12)
    d.rounded_rectangle((lw, lw, s - lw, s - lw), s // 4, outline=(255, 255, 255, 255), width=lw)
    d.ellipse((s * 0.3, s * 0.3, s * 0.7, s * 0.7), outline=(255, 255, 255, 255), width=lw)
    d.ellipse((s * 0.7, s * 0.2, s * 0.8, s * 0.3), fill=(255, 255, 255, 255))
    a = np.asarray(im, np.float32)
    if gradient:
        g = np.linspace(0, 1, s)[None, :, None] * 0.5 + np.linspace(0, 1, s)[:, None, None] * 0.5
        col = np.array([255, 200, 60.]) * (1 - g) + np.array([220, 40, 140.]) * g    # RGB yellow->pink
        a[..., :3] = col
    return a[..., 2::-1], a[..., 3:] / 255

def lyric_layer(W, txt, size):
    f = ImageFont.truetype(os.path.join(FD, 'cormorant-700i.ttf'), size)
    out = []
    x = (W - ImageDraw.Draw(Image.new('L', (1, 1))).textlength(txt, font=f)) / 2
    for i in range(len(txt)):
        im = Image.new('L', (W, int(size * 1.6))); ImageDraw.Draw(im).text((x, 0), txt[:i + 1], font=f, fill=255)
        prev = Image.new('L', (W, int(size * 1.6))); ImageDraw.Draw(prev).text((x, 0), txt[:i], font=f, fill=255) if i else None
        out.append((np.asarray(im, np.float32) / 255, np.asarray(prev, np.float32) / 255))
    return out

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('inp'); ap.add_argument('out')
    ap.add_argument('--lyric', default=''); ap.add_argument('--hook', type=float, default=2.2)
    ap.add_argument('--handle', default='@aitricksbysumit'); ap.add_argument('--credit', default='')
    ap.add_argument('--top', default=''); ap.add_argument('--size', type=int, default=110)
    ap.add_argument('--title', default='', help="title mode: gold serif line, e.g. 'The Beauty of'")
    ap.add_argument('--cycle', default='', help='title mode: word that flickers through fonts, e.g. Waiting')
    A = ap.parse_args()
    if A.title:
        return title_mode(A)
    cap = cv2.VideoCapture(A.inp); W, H = int(cap.get(3)), int(cap.get(4)); FPS = cap.get(5)
    LY = lyric_layer(W, A.lyric, A.size); ly_y = int(H * 0.45)
    TOP = text_rgba(W, A.top, 'montserrat-500.ttf', 34, (235, 235, 235, 255)) if A.top else None
    HND = text_rgba(W, A.handle, 'montserrat-700.ttf', 30, (255, 255, 255, 255), 'right')
    CRD = text_rgba(W, A.credit, 'montserrat-500.ttf', 26, (170, 170, 170, 255), 'right') if A.credit else None
    G0, G1 = ig_glyph(64, False), ig_glyph(64, True); gx, gy = W - 48 - 64, int(H * 0.2)
    p = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                          '-i', A.inp, '-map', '0:v', '-map', '1:a?', '-shortest', '-c:v', 'libx264', '-crf', '19', '-pix_fmt', 'yuv420p',
                          '-c:a', 'copy', '-movflags', '+faststart', A.out], stdin=subprocess.PIPE)
    i = 0; hook = A.hook; flash = 0.35
    while True:
        ok, f = cap.read()
        if not ok: break
        t = i / FPS; f = f.astype(np.float32)
        if t < hook + flash:
            card = np.zeros_like(f)
            B = np.clip(burn_layer(W, H, t) * 1.35, 0, 1)
            card = card + burn_colour(B)
            # lyric: letter by letter over the first 70% of the hook, slight flicker
            u = min(1, t / (hook * 0.7)); n = int(u * len(LY))
            if n > 0:
                cur, prev = LY[min(n, len(LY)) - 1]; part = (u * len(LY)) % 1 if n < len(LY) else 1
                m = prev + (cur - prev) * part
                fl = 0.88 + 0.12 * math.sin(t * 40)
                h_ = m.shape[0]; card[ly_y:ly_y + h_] = card[ly_y:ly_y + h_] * (1 - m[..., None]) + np.array([235, 245, 255.]) * m[..., None] * fl
            if TOP is not None:
                L, Aa = TOP; y = int(H * 0.235) - 80; card[y:y + L.shape[0]] = card[y:y + L.shape[0]] * (1 - Aa) + L * Aa
            if t > 0.3:
                G = G1 if t > hook * 0.6 else G0; s = min(1, (t - 0.3) / 0.15)
                L, Aa = G; Aa = Aa * s; card[gy:gy + 64, gx:gx + 64] = card[gy:gy + 64, gx:gx + 64] * (1 - Aa) + L * Aa
            for k, (lay, t0) in enumerate(((HND, 0.55), (CRD, 0.8))):
                if lay is None or t < t0: continue
                L, Aa = lay; y = gy + 80 + k * 40; wcut = int(W * min(1, (t - t0) / 0.4))
                Aa = Aa.copy(); Aa[:, : W - wcut] *= 0                          # typing from the right edge feel
                card[y:y + L.shape[0]] = card[y:y + L.shape[0]] * (1 - Aa) + L * Aa
            if t >= hook:                                                     # burn flash wipe into the video
                v = (t - hook) / flash
                fl = math.sin(math.pi * v)
                full = burn_colour(np.clip(burn_layer(W, H, t + 3.1) * 0.6 + 0.5, 0, 1))
                mix = min(1, v * 1.3)
                card = card * (1 - mix) + f * mix
                card = card * (1 - 0.6 * fl) + full * 0.6 * fl
            f = card
        p.stdin.write(np.clip(f, 0, 255).astype(np.uint8).tobytes()); i += 1
    p.stdin.close(); p.wait()

CYCLE_FONTS = ['permanent-marker-400.ttf', 'great-vibes-400.ttf', 'anton-400.ttf', 'caveat-brush-400.ttf', 'cinzel-700.ttf',
               'mr-dafoe-400.ttf', 'bebas-neue-400.ttf', 'sacramento-400.ttf', 'kaushan-script-400.ttf']

def title_mode(A):
    """Second hook variant: burn flashes on black, gold 'The Beauty of' + a word that flickers through fonts,
    then the video fades up under the title (title lingers 0.6 s over the footage)."""
    cap = cv2.VideoCapture(A.inp); W, H = int(cap.get(3)), int(cap.get(4)); FPS = cap.get(5)
    sc = min(W, H) / 1080
    T, TA = text_rgba(W, A.title, 'cormorant-700i.ttf', int(64 * sc), (235, 200, 90, 255))
    cyc = [text_rgba(W, A.cycle, f, int(56 * sc), (255, 255, 255, 255)) for f in CYCLE_FONTS]
    ty = int(H * 0.46) - T.shape[0]; cy = int(H * 0.46) + 4
    hook = A.hook; fade = 0.6
    p = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                          '-i', A.inp, '-map', '0:v', '-map', '1:a?', '-shortest', '-c:v', 'libx264', '-crf', '19', '-pix_fmt', 'yuv420p',
                          '-c:a', 'copy', '-movflags', '+faststart', A.out], stdin=subprocess.PIPE)
    i = 0
    while True:
        ok, f = cap.read()
        if not ok: break
        t = i / FPS; f = f.astype(np.float32)
        if t < hook + fade:
            card = burn_colour(np.clip(burn_layer(W, H, t * 1.4) * 1.4, 0, 1)) * max(0, 1 - t / (hook * 0.8))
            if t >= hook:
                v = (t - hook) / fade; card = card * (1 - v) + f * v
            ta = min(1, t / 0.4) * (1 - max(0, (t - hook - fade * 0.4) / (fade * 0.6)))
            if ta > 0:
                card[ty:ty + T.shape[0]] = card[ty:ty + T.shape[0]] * (1 - TA * ta) + T * TA * ta
                if t > 0.5:
                    k = int((t - 0.5) / 0.14)
                    L, LA = cyc[-1] if t > hook * 0.85 else cyc[k % len(cyc)]
                    card[cy:cy + L.shape[0]] = card[cy:cy + L.shape[0]] * (1 - LA * ta) + L * LA * ta
            f = card
        p.stdin.write(np.clip(f, 0, 255).astype(np.uint8).tobytes()); i += 1
    p.stdin.close(); p.wait()

if __name__ == '__main__':
    main()
