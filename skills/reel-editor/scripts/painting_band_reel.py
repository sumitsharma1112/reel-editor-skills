"""Meri Maa Ke Barabar Koi Nahi – 9:16 reel from 8 ChatGPT lyric paintings (16:9 strips),
sharp band in the middle over a blurred, darkened copy of the same painting, slow zoom, soft crossfades."""
import subprocess, numpy as np, cv2

D = './'   # folder with hd/Maa_Image_{1..8}_FullHD_16x9.png
AUD = 'song.mp4'
W, H, FPS, DUR = 1080, 1920, 30, 43.7
STRIP = {1: (269, 810), 2: (268, 810), 3: (275, 804), 4: (274, 804), 5: (286, 793), 6: (286, 793), 7: (256, 824), 8: (256, 824)}
# (image, start) – lyric timings; last chorus alternates 8 / 5 / 8
SEQ = [(1, 0.0), (2, 5.0), (3, 11.0), (4, 14.0), (5, 18.0), (6, 24.0), (7, 27.0), (8, 29.0), (5, 33.5), (8, 38.0)]
XF = 0.45

def load(i):
    a = cv2.cvtColor(cv2.imread(D + f'hd/Maa_Image_{i}_FullHD_16x9.png'), cv2.COLOR_BGR2RGB)
    y0, y1 = STRIP[i]; s = a[y0 + 4:y1 - 4, 4:-4]
    band_h = int(W * s.shape[0] / s.shape[1])
    band = cv2.resize(s, (W, band_h), interpolation=cv2.INTER_LANCZOS4)
    # background: same painting, cover-cropped to 9:16, heavy blur, darkened, warm
    sc = H / s.shape[0]; big = cv2.resize(s, (int(s.shape[1] * sc), H), interpolation=cv2.INTER_LINEAR)
    x0 = int(big.shape[1] * 0.18); bg = big[:, x0:x0 + W]
    bg = cv2.GaussianBlur(bg, (0, 0), 38).astype(np.float32) * 0.42
    return band.astype(np.float32), bg
IM = {i: load(i) for i in {s[0] for s in SEQ}}

yy = np.linspace(-1, 1, H)[:, None]; VIG = (1 - 0.45 * yy ** 2)[..., None]

def scene(i, t_local):
    band, bg = IM[i]
    z = 1.0 + 0.04 * min(1, t_local / 6)                       # slow push-in
    bh, bw = band.shape[:2]
    b = cv2.resize(band, (int(bw * z), int(bh * z)), interpolation=cv2.INTER_LINEAR)
    cx = b.shape[1] - W; b = b[:, cx:cx + W]   # anchor right so lyric text never gets cut
    img = bg.copy() * VIG
    y0 = (H - b.shape[0]) // 2
    # soft feathered top/bottom edges of the band
    m = np.ones((b.shape[0], 1, 1), np.float32); f = 24
    m[:f, 0, 0] = np.linspace(0, 1, f); m[-f:, 0, 0] = np.linspace(1, 0, f)
    img[y0:y0 + b.shape[0]] = img[y0:y0 + b.shape[0]] * (1 - m) + b * m
    return img

def frame(t):
    k = max(j for j, (_, s) in enumerate(SEQ) if s <= t)
    i, s = SEQ[k]; img = scene(i, t - s)
    if k + 1 < len(SEQ) and t > SEQ[k + 1][1] - XF:            # crossfade into next
        a = (t - (SEQ[k + 1][1] - XF)) / XF
        img = img * (1 - a) + scene(SEQ[k + 1][0], 0) * a
    if t < 0.6: img *= t / 0.6
    if t > DUR - 1.2: img *= max(0, (DUR - t) / 1.2)
    return np.clip(img, 0, 255).astype(np.uint8)

if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        for t in map(float, sys.argv[1:]): cv2.imwrite(D + f'f_{t}.jpg', cv2.cvtColor(frame(t), cv2.COLOR_RGB2BGR))
        sys.exit()
    p = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                          '-i', AUD, '-map', '0:v', '-map', '1:a', '-af', 'loudnorm=I=-14:TP=-1.5', '-shortest',
                          '-c:v', 'libx264', '-crf', '19', '-maxrate', '4M', '-bufsize', '8M', '-pix_fmt', 'yuv420p',
                          '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart', D + 'Meri_Maa_Ke_Barabar.mp4'], stdin=subprocess.PIPE)
    for n in range(int(DUR * FPS)): p.stdin.write(frame(n / FPS).tobytes())
    p.stdin.close(); p.wait(); print('done')
