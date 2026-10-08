"""Crimson 'Aerochrome' grade: luminance tritone black/maroon -> crimson -> peach -> white,
skies and foliage glow red, crushed blacks, bloom, vignette, grain. Keeps the audio.

  python crimson_grade.py --in clip.mp4 --out clip_red.mp4 [--strength 1.0]
"""
import argparse, os, sys, subprocess, numpy as np, cv2
sys.path.insert(0, os.path.dirname(__file__))
from common import load_frames, probe_size

STOPS = [(0.0, (8, 2, 6)), (0.18, (22, 10, 70)), (0.45, (36, 34, 214)), (0.72, (150, 170, 250)), (1.0, (245, 248, 255))]  # BGR


def lut():
    x = np.linspace(0, 1, 256)
    out = np.zeros((256, 3), np.float32)
    for c in range(3):
        out[:, c] = np.interp(x, [s[0] for s in STOPS], [s[1][c] for s in STOPS])
    return out


def grade(f, L, strength, vig, rng):
    fl = f.astype(np.float32)
    b, g, r = fl[..., 0], fl[..., 1], fl[..., 2]
    lum = 0.25 * r + 0.45 * g + 0.30 * b            # blue/green weighted -> sky & leaves go bright red
    lum = np.clip((lum - 18) * 1.15, 0, 255)
    o = L[lum.astype(np.uint8)]
    o = fl * (1 - strength) + o * strength
    hi = np.clip(o - 170, 0, 255)
    o += cv2.GaussianBlur(hi, (0, 0), 18) * 0.6
    o *= vig
    o += rng.normal(0, 4, o.shape[:2])[..., None]
    return np.clip(o, 0, 255).astype(np.uint8)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--in', dest='inp', required=True)
    p.add_argument('--out', required=True)
    p.add_argument('--strength', type=float, default=1.0)
    a = p.parse_args()
    F = load_frames(a.inp, max_side=1920)
    h, w = F.shape[1:3]
    yy, xx = np.mgrid[0:h, 0:w]
    vig = np.clip(1 - 0.45 * (((xx - w / 2) / (w / 2)) ** 2 + ((yy - h / 2) / (h / 2)) ** 2), 0.35, 1)[..., None]
    L, rng = lut(), np.random.default_rng(1)
    cmd = ['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{w}x{h}', '-r', '30', '-i', '-',
           '-i', a.inp, '-map', '0:v', '-map', '1:a?', '-c:v', 'libx264', '-crf', '18', '-pix_fmt', 'yuv420p',
           '-c:a', 'aac', '-shortest', '-movflags', '+faststart', a.out]
    pr = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for f in F:
        pr.stdin.write(grade(f, L, a.strength, vig, rng).tobytes())
    pr.stdin.close(); pr.wait()
    print('done', a.out)


if __name__ == '__main__':
    main()
