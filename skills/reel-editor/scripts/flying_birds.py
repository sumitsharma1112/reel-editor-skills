"""Flying birds overlay ('aasmaan mein udte panchi') for still paintings / photos.

A procedural flock of bird silhouettes: each bird has two curved wings that flap, glides now and
then, bobs on a sine path and crosses the sky; far birds are smaller, paler and slower (depth).
Optional sky-only placement (keeps birds above a y-limit).

Library:   from flying_birds import Flock;  f = Flock(W, H, n=14, sky_y=(0.08, 0.45));  frame = f.draw(frame_bgr_float, t)
CLI:       python flying_birds.py image.jpg out.mp4 --dur 8 --n 14 --sky 0.08 0.45 [--push 0.05]
"""
import math, sys, argparse, subprocess
import numpy as np, cv2

class Flock:
    def __init__(self, W, H, n=14, sky_y=(0.08, 0.45), seed=4, direction=1, colour=(28, 26, 30)):
        r = np.random.default_rng(seed); self.W, self.H, self.dir = W, H, direction
        self.b = []
        for k in range(n):
            depth = r.uniform(0.35, 1.0)                                      # 1 = near
            self.b.append(dict(depth=depth, size=W * 0.028 * depth + 6,
                               speed=W * (0.05 + 0.10 * depth), y=H * r.uniform(*sky_y),
                               x0=r.uniform(-0.3, 1.0) * W, flap=r.uniform(5.5, 8.5), ph=r.uniform(0, 6.3),
                               bob=r.uniform(6, 18) * depth, glide=r.uniform(0, 6.3)))
        self.col = np.array(colour, np.float32)

    def _wing_pts(self, cx, cy, s, a, side, tilt):
        # wing from body outwards: shoulder -> elbow -> tip, angle a (rad, + = up)
        e = (cx + side * s * 0.55, cy - s * 0.55 * math.sin(a) * 0.9 - s * 0.05)
        tip = (cx + side * s * 1.15, cy - s * 1.0 * math.sin(a * 1.25) + s * 0.12)
        pts = []
        for u in np.linspace(0, 1, 9):                      # upper edge
            x = (1 - u) ** 2 * cx + 2 * (1 - u) * u * e[0] + u * u * tip[0]
            y = (1 - u) ** 2 * cy + 2 * (1 - u) * u * (e[1] - s * 0.12) + u * u * tip[1]
            pts.append((x, y))
        for u in np.linspace(1, 0, 9):                      # lower edge, thinner
            x = (1 - u) ** 2 * cx + 2 * (1 - u) * u * e[0] + u * u * tip[0]
            y = (1 - u) ** 2 * (cy + s * 0.12) + 2 * (1 - u) * u * (e[1] + s * 0.06) + u * u * tip[1]
            pts.append((x, y))
        c, sn = math.cos(tilt), math.sin(tilt)
        return np.array([((x - cx) * c - (y - cy) * sn + cx, (x - cx) * sn + (y - cy) * c + cy) for x, y in pts], np.float32)

    def mask(self, t):
        m = np.zeros((self.H, self.W), np.float32); a_ = np.zeros_like(m)
        span = self.W * 1.6
        for b in self.b:
            x = ((b['x0'] + b['speed'] * t) % span) - self.W * 0.3
            if self.dir < 0: x = self.W - x
            y = b['y'] + b['bob'] * math.sin(t * 1.3 + b['ph'])
            gl = 0.5 + 0.5 * math.sin(t * 0.5 + b['glide'])                    # occasional glide
            amp = 0.95 if gl < 0.7 else 0.25
            a = amp * math.sin(t * b['flap'] + b['ph']) + (0.15 if gl >= 0.7 else 0)
            s = b['size']; tilt = 0.12 * math.sin(t * 0.9 + b['ph']) * self.dir
            for side in (-1, 1):
                p = self._wing_pts(x, y, s, a, side, tilt)
                cv2.fillPoly(m, [np.round(p * 4).astype(np.int32)], 1.0, cv2.LINE_AA, shift=2)
            cv2.ellipse(m, (int(x), int(y + s * 0.05)), (max(1, int(s * 0.22)), max(1, int(s * 0.1))), math.degrees(tilt), 0, 360, 1.0, -1, cv2.LINE_AA)
            # depth fade: far birds lighter
            cv2.circle(a_, (int(x), int(y)), int(s * 1.4), 0.45 + 0.55 * b['depth'], -1)
        return cv2.GaussianBlur(m, (0, 0), 0.6) * np.clip(cv2.GaussianBlur(a_, (0, 0), 3) + 0.3, 0, 1)

    def draw(self, img, t):
        m = self.mask(t)[..., None]
        return img * (1 - m * 0.88) + self.col * m * 0.88

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('image'); ap.add_argument('out')
    ap.add_argument('--dur', type=float, default=8); ap.add_argument('--n', type=int, default=14)
    ap.add_argument('--sky', type=float, nargs=2, default=(0.08, 0.45)); ap.add_argument('--push', type=float, default=0.05)
    ap.add_argument('--fps', type=int, default=30)
    A = ap.parse_args(); W, H = 1080, 1920
    im = cv2.imread(A.image); s = max(W / im.shape[1], H / im.shape[0]) * (1 + A.push)
    im = cv2.resize(im, None, fx=s, fy=s, interpolation=cv2.INTER_LANCZOS4).astype(np.float32)
    fl = Flock(W, H, A.n, tuple(A.sky))
    p = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{W}x{H}', '-r', str(A.fps), '-i', '-',
                          '-c:v', 'libx264', '-crf', '19', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', A.out], stdin=subprocess.PIPE)
    N = int(A.dur * A.fps)
    for i in range(N):
        t = i / A.fps
        M = np.float32([[1, 0, -(im.shape[1] - W) / 2], [0, 1, -(im.shape[0] - H) / 2]])
        fr = cv2.warpAffine(im, M, (W, H))
        k = 1 + A.push * i / N
        fr = cv2.warpAffine(fr, cv2.getRotationMatrix2D((W / 2, H / 2), 0, k), (W, H), borderMode=cv2.BORDER_REFLECT)
        p.stdin.write(np.clip(fl.draw(fr, t), 0, 255).astype(np.uint8).tobytes())
    p.stdin.close(); p.wait()

if __name__ == '__main__':
    main()
