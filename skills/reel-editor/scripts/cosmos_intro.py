"""5 s black & white cosmos intro: warp stars, spiral galaxy, black hole, nebula, planet; cuts accelerate
in sync with synthesized camera-shutter clicks; ends by diving into the black hole into a white flash."""
import math, subprocess, numpy as np, cv2, soundfile as sf
W, H, FPS, DUR = 720, 1280, 30, 5.0
N = int(FPS * DUR)
rng = np.random.default_rng(11)
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
CX, CY = W / 2, H / 2

# ---------- scenes (each returns float32 HxW in 0..1)
STARS = np.stack([rng.uniform(-1, 1, 2500), rng.uniform(-1.6, 1.6, 2500), rng.uniform(0.05, 1, 2500)], 1)
def warp(u, speed=1.0, seed=0):
    img = np.zeros((H, W), np.float32)
    z0 = (STARS[:, 2] - (u * 0.5 * min(speed, 2.5) + seed * 0.13)) % 1 + 0.04; z1 = z0 + 0.014 * min(speed, 2.5)
    f = 300
    for (x, y), a, b in zip(STARS[:, :2], z0, z1):
        p0 = (int(CX + x * f / a), int(CY + y * f / a)); p1 = (int(CX + x * f / b), int(CY + y * f / b))
        c = min(1.0, 0.12 / a)
        if -50 < p0[0] < W + 50 and -50 < p0[1] < H + 50:
            cv2.line(img, p1, p0, c, 1 if a > 0.15 else 2, cv2.LINE_AA)
    return np.clip(img + cv2.GaussianBlur(img, (0, 0), 3) * 0.5, 0, 1)

NG = 60000
arm = rng.integers(0, 2, NG); rr = rng.power(0.6, NG) * 1.0
th = np.log(rr + 0.02) * 2.6 + arm * math.pi + rng.normal(0, 0.28 + 0.15 * (1 - rr), NG)
GX, GY = rr * np.cos(th), rr * np.sin(th); GB = rng.uniform(0.3, 1, NG) * (1.2 - rr)
def galaxy(u, rot0=0.0, tilt=0.5, zoom=1.0):
    a = rot0 + u * 2.2; s = 420 * zoom * (1 + 0.6 * u)
    x = CX + s * (GX * math.cos(a) - GY * math.sin(a)); y = CY + s * tilt * (GX * math.sin(a) + GY * math.cos(a))
    img = np.zeros((H, W), np.float32); ok = (x > 0) & (x < W - 1) & (y > 0) & (y < H - 1)
    np.add.at(img, (y[ok].astype(int), x[ok].astype(int)), GB[ok] * 0.35)
    core = np.exp(-(((xx - CX) / (60 * zoom)) ** 2 + ((yy - CY) / (60 * zoom * tilt)) ** 2) * 1.0)
    img = img + cv2.GaussianBlur(img, (0, 0), 3) * 1.5 + cv2.GaussianBlur(img, (0, 0), 14) * 2 + core * 0.9
    return np.clip(img, 0, 1)

NOISE = [cv2.resize(rng.random((8 * 2 ** k, 5 * 2 ** k)).astype(np.float32), (W * 2, H * 2), interpolation=cv2.INTER_CUBIC) for k in range(6)]
FBM = sum(n / 2 ** k for k, n in enumerate(NOISE)); FBM = (FBM - FBM.min()) / (FBM.max() - FBM.min())
def nebula(u, zoom0=1.0):
    z = zoom0 * (1 + 1.2 * u); Mx = cv2.getRotationMatrix2D((W, H), u * 25, z)
    n = cv2.warpAffine(FBM, Mx, (W * 2, H * 2), borderMode=cv2.BORDER_REFLECT)[H // 2:H // 2 + H, W // 2:W // 2 + W]
    n = np.clip((n - 0.56) * 3.2, 0, 1) ** 2.0 * 0.85
    st = (rng.random((H, W)) > 0.9985).astype(np.float32)
    return np.clip(n + cv2.GaussianBlur(st, (0, 0), 1.2) * 3, 0, 1)

def blackhole(u, zoom=1.0, spin0=0.0):
    s = 1 + 2.5 * u ** 2 * zoom if zoom > 1 else 1 + 0.35 * u
    X = (xx - CX) / (s * 1.0); Y = (yy - CY) / s
    rs = 95.0                                                 # shadow radius
    tilt = 0.22
    rd = np.sqrt(X ** 2 + (Y / tilt) ** 2); ang = np.arctan2(Y / tilt, X)
    streak = 0.6 + 0.4 * np.sin(ang * 9 + rd * 0.07 - (spin0 + u * 18)) * np.sin(ang * 23 - u * 31 + rd * 0.03)
    disk = np.exp(-((rd - 250) / 75) ** 2) * (rd > rs * 1.5) * streak * (1.0 - 0.35 * np.tanh(X / 200)) * 0.75
    rr2 = np.sqrt(X ** 2 + Y ** 2)
    front_mask = (Y > 0) | (rr2 > rs)                          # disk in front of the shadow on the lower half
    arc_r = np.sqrt(X ** 2 + ((Y + 20) / 0.92) ** 2)
    lensed = np.exp(-((arc_r - 150) / 16) ** 2) * (Y < 10) * (0.55 + 0.3 * np.sin(np.arctan2(Y, X) * 7 - u * 20))
    ring = np.exp(-((rr2 - rs * 1.08) / 5) ** 2) * 1.2
    img = disk * front_mask + lensed * 0.9 + ring
    img = img * (rr2 > rs) + 0                                 # pure black shadow
    st = (rng.random((H, W)) > 0.999).astype(np.float32) * (rr2 > 300)
    img = img + cv2.GaussianBlur(img.astype(np.float32), (0, 0), 12) * 0.45 + st
    return np.clip(img, 0, 1).astype(np.float32)

def planet(u, side=1):
    R = 900 * (1 + 0.5 * u); px, py = CX + side * 380, CY + 820 - 260 * u
    d = np.sqrt((xx - px) ** 2 + (yy - py) ** 2)
    lx, ly = -side * 0.75, -0.66
    nz = np.sqrt(np.clip(1 - (d / R) ** 2, 0, 1))
    shade = np.clip(((xx - px) / R * lx + (yy - py) / R * ly) * 0.9 + nz * 0.15, 0, 1) ** 1.3
    tex = FBM[:H, :W] * 0.35 + 0.65
    body = (d < R) * shade * tex * 0.55
    rim = np.exp(-((d - R) / 10) ** 2) * np.clip(((xx - px) * lx + (yy - py) * ly) / R + 0.3, 0, 1) * 1.4
    st = (rng.random((H, W)) > 0.9988).astype(np.float32) * (d > R)
    return np.clip(body + rim + cv2.GaussianBlur(rim.astype(np.float32), (0, 0), 14) + st, 0, 1).astype(np.float32)

# ---------- edit plan: accelerating cuts
gaps = [16, 9, 8, 7, 7, 6, 6, 5, 5, 4, 4, 4, 3, 3, 3, 3, 3] + [2] * 20
cuts = [0]
for g in gaps:
    if cuts[-1] + g >= 126: break
    cuts.append(cuts[-1] + g)
FINAL = 126
seq = ['warp', 'galaxy', 'blackhole', 'nebula', 'warp', 'planet', 'galaxy', 'blackhole', 'nebula', 'warp']
plan = [(c, seq[i % len(seq)], i) for i, c in enumerate(cuts)] + [(FINAL, 'dive', 99)]
print('cuts', len(plan), plan[-3:])

def scene(name, u, i):
    if name == 'warp': return warp(u * (1 + i * 0.1), 1 + 0.15 * i, i)
    if name == 'galaxy': return galaxy(u, rot0=i * 1.3, tilt=[0.5, 0.3, 0.8][i % 3], zoom=[1.0, 1.6, 0.8][i % 3])
    if name == 'blackhole': return blackhole(u, 1.0, i * 2.0)
    if name == 'nebula': return nebula(u, 1 + 0.3 * (i % 3))
    if name == 'planet': return planet(u, 1 if i % 2 else -1)

grain = [rng.normal(0, 0.05, (H // 2, W // 2)).astype(np.float32) for _ in range(6)]
VIG = np.clip(1 - 0.55 * (((xx - CX) / CX) ** 2 + ((yy - CY) / CY) ** 2), 0.25, 1)
out = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'gray', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                        '-vf', 'scale=1080:1920:flags=lanczos', '-c:v', 'libx264', '-crf', '17', '-pix_fmt', 'yuv420p', 'cosmos_v.mp4'], stdin=subprocess.PIPE)
for n in range(N):
    k = max(i for i, (c, _, _) in enumerate(plan) if c <= n)
    c0, name, idx = plan[k]; c1 = plan[k + 1][0] if k + 1 < len(plan) else N
    u = (n - c0) / max(1, c1 - c0)
    if name == 'dive':                                         # dive into the black hole -> white
        f = blackhole(u, 3.0, 5.0)
        f = f + np.clip((u - 0.72) / 0.28, 0, 1) ** 2
    else:
        f = scene(name, u, idx)
        z = 1 + 0.12 * math.exp(-(n - c0) / 2.0)                # punch on every cut
        if z > 1.01:
            M = cv2.getRotationMatrix2D((CX, CY), 0, z); f = cv2.warpAffine(f, M, (W, H))
        if n == c0 and n > 0 and (c1 - c0 > 3 or idx % 3 == 0): f = f * 0.55 + 0.35   # shutter flash (not every fast cut)
    g = cv2.resize(grain[n % 6], (W, H))
    f = 1 - np.exp(-np.clip(f, 0, 4) * 1.6); f = np.clip(f * VIG + g, 0, 1)
    out.stdin.write((f * 255).astype(np.uint8).tobytes())
out.stdin.close(); out.wait()

# ---------- audio: camera shutter clicks on every cut + rising rumble + final boom
SR = 48000; A = np.zeros(int(SR * DUR) + SR, np.float32)
def click(t0, gain=1.0):
    i = int(t0 * SR)
    for dt, g, ln in [(0.0, 1.0, 0.006), (0.032, 0.7, 0.012), (0.045, 0.35, 0.02)]:
        n = int(ln * SR); b = rng.normal(0, 1, n) * np.exp(-np.arange(n) / (n * 0.25))
        b = np.diff(np.concatenate([[0], b]))                    # high-passed snap
        j = i + int(dt * SR); A[j:j + n] += b * g * gain * 0.5
    th_ = np.sin(2 * math.pi * 90 * np.arange(int(0.05 * SR)) / SR) * np.exp(-np.arange(int(0.05 * SR)) / (0.012 * SR))
    A[i:i + len(th_)] += th_ * 0.25 * gain
for c, name, _ in plan[:-1]:
    click(c / FPS, 0.8 + 0.2 * rng.random())
# extra off-beat clicks for a continuous motor-drive feel in the fast part
for c in range(60, FINAL, 2):
    click(c / FPS + 1 / 60, 0.45)
t = np.arange(int(SR * DUR)) / SR
rumble = rng.normal(0, 1, len(t)).astype(np.float32); rumble = np.convolve(rumble, np.ones(400) / 400, 'same') * 6
A[:len(t)] += rumble * np.clip(t / DUR, 0, 1) ** 2 * 0.35
i = int(FINAL / FPS * SR) + int(0.55 * SR); n = int(1.2 * SR)
boom = np.sin(2 * math.pi * (55 - 20 * np.arange(n) / n) * np.arange(n) / SR) * np.exp(-np.arange(n) / (0.35 * SR))
A[i:i + n] += boom * 0.9
A = A[:int(SR * DUR)]; A = A / np.abs(A).max() * 0.9
sf.write('cosmos_a.wav', np.stack([A, A], 1), SR)
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', 'cosmos_v.mp4', '-i', 'cosmos_a.wav', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k',
                '-af', 'loudnorm=I=-14:TP=-1', '-shortest', 'cosmos.mp4'], check=True)
print('done')
