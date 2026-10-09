"""Water / action transitions for travel and adventure reels (used in the Rishikesh rafting reel).

Each transition is f(A, B, p) -> frame. A and B are BGR uint8 1080x1920 frames, and p runs 0..1 across
the transition window, centred on the cut (half before, half after). Give every shot a few padding
frames from the source before its in-point and after its out-point, so both sides keep moving.

  ripple    drop-in-water: a ring wave expands from the centre, refracts both shots and reveals B
  luma      foam reveal: B appears through its own brightest parts (white water) first, plus a foam flash
  zoom      zoom-through: push into A with radial blur, B arrives scaled down from 1.6x
  whipL/R/U whip pan: slide with heavy directional motion blur
  spin      roll: A rotates out with blur, B rotates in
  flash     white flash cut;  punch: flash + B scaled 1.12 -> 1 (for strobing stills)
  leak      warm light leak sweeping across a crossfade (good into emotional/selfie shots)
  lightning storm cut: double flicker, desaturated overexposure (with a thunder crack)

Join clips or photos with one transition between each pair (120 BPM grid by default):
  python water_transitions.py --clips a.mp4,b.mp4,photo.jpg --trans ripple,leak --durs 2,2,2 --out out.mp4
Preview every transition on two shots:
  python water_transitions.py --demo a.mp4,b.mp4 --out demo.mp4
"""
import argparse, math, os, subprocess
import numpy as np, cv2

W, H, FPS = 1080, 1920, 30
YY, XX = np.mgrid[0:H, 0:W].astype(np.float32)


def smooth(x):
    x = min(1, max(0, x)); return x * x * (3 - 2 * x)


def zoom(img, z, cx=W / 2, cy=H / 2, ang=0.0):
    M = cv2.getRotationMatrix2D((cx, cy), ang, z)
    return cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)


def radial_blur(img, amt, n=10):
    if amt < 0.004: return img
    acc = np.zeros(img.shape, np.float32)
    for k in range(n): acc += zoom(img, 1 + amt * k / (n - 1))
    return (acc / n).astype(np.uint8)


def tr_zoom(A, B, p):
    if p < 0.5:
        u = p / 0.5; return radial_blur(zoom(A, 1 + 0.9 * u ** 2), 0.25 * u)
    u = (1 - p) / 0.5; return radial_blur(zoom(B, 1 + 0.6 * u ** 2), 0.22 * u)


def tr_whip(A, B, p, dx=-1, dy=0):
    off = smooth(p); blur = int(200 * math.sin(math.pi * p)); vert = dy != 0
    Ma = np.float32([[1, 0, dx * W * off], [0, 1, dy * H * off]])
    Mb = np.float32([[1, 0, dx * W * (off - 1)], [0, 1, dy * H * (off - 1)]])
    a = cv2.warpAffine(A, Ma, (W, H), borderMode=cv2.BORDER_REFLECT)
    b = cv2.warpAffine(B, Mb, (W, H), borderMode=cv2.BORDER_REFLECT)
    if not vert:
        edge = W * (1 - off) if dx < 0 else W * off
        m = (XX >= edge) if dx < 0 else (XX < edge)
    else:
        edge = H * (1 - off) if dy < 0 else H * off
        m = (YY >= edge) if dy < 0 else (YY < edge)
    m = m.astype(np.float32)[..., None]
    o = (a * (1 - m) + b * m).astype(np.uint8)
    if blur >= 3: o = cv2.blur(o, (1, blur) if vert else (blur, 1))
    return o


def tr_ripple(A, B, p, cy=0.55):
    bell = math.sin(math.pi * p); amp = 38 * bell; ph = p * 14
    r = np.sqrt((XX - W / 2) ** 2 + (YY - H * cy) ** 2)
    d = np.sin(r / 38 - ph) * amp
    mx = XX + d * (XX - W / 2) / (r + 1); my = YY + d * (YY - H * cy) / (r + 1)
    a = cv2.remap(A, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    b = cv2.remap(B, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    rad = smooth(p) * 1.25 * math.hypot(W / 2, H * 0.6)
    m = np.clip((rad - r + d * 2) / 90, 0, 1)[..., None]
    o = a.astype(np.float32) * (1 - m) + b.astype(np.float32) * m
    o += 70 * bell * np.exp(-((r - rad) / 40) ** 2)[..., None]
    return np.clip(o, 0, 255).astype(np.uint8)


def tr_luma(A, B, p):
    lb = cv2.GaussianBlur(cv2.cvtColor(B, cv2.COLOR_BGR2GRAY), (0, 0), 6).astype(np.float32) / 255
    thr = 1.05 - 1.25 * smooth(p)
    m = np.clip((lb - thr) / 0.12, 0, 1)[..., None]
    o = A.astype(np.float32) * (1 - m) + B.astype(np.float32) * m + 90 * math.sin(math.pi * p) ** 3
    return np.clip(o, 0, 255).astype(np.uint8)


def tr_spin(A, B, p):
    if p < 0.5:
        u = smooth(p / 0.5); img = zoom(A, 1 + 0.35 * u, ang=-70 * u ** 2)
    else:
        u = smooth((1 - p) / 0.5); img = zoom(B, 1 + 0.35 * u, ang=70 * u ** 2)
    return radial_blur(img, 0.12 * math.sin(math.pi * p))


def tr_flash(A, B, p):
    img = A if p < 0.5 else B; f = math.sin(math.pi * p) ** 0.7
    return np.clip(img.astype(np.float32) * (1 - 0.3 * f) + 255 * 0.85 * f, 0, 255).astype(np.uint8)


def tr_punch(A, B, p):
    if p < 0.5: return tr_flash(A, B, p)
    return tr_flash(A, zoom(B, 1 + 0.12 * (1 - p) / 0.5), p)


def tr_leak(A, B, p):
    e = smooth(p)
    o = A.astype(np.float32) * (1 - e) + B.astype(np.float32) * e
    cx = W * (-0.3 + 1.6 * p)
    g = np.exp(-(((XX[::4, ::4] - cx) / 520) ** 2 + ((YY[::4, ::4] - H * 0.35) / 800) ** 2)) * math.sin(math.pi * p) * 1.6
    g = cv2.resize(g.astype(np.float32), (W, H))
    return np.clip(o + np.stack([g * 120, g * 190, g * 255], -1), 0, 255).astype(np.uint8)


def tr_lightning(A, B, p):
    img = A if p < 0.5 else B
    f = [0, 1, 0.3, 0.9, 0.2, 0][min(5, int(p * 6))]
    g = cv2.cvtColor(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY), cv2.COLOR_GRAY2BGR)
    img = cv2.addWeighted(img, 1 - 0.6 * f, g, 0.6 * f, 0)
    return np.clip(img.astype(np.float32) * (1 + 1.6 * f) + 60 * f, 0, 255).astype(np.uint8)


TR = dict(zoom=tr_zoom, whipL=lambda a, b, p: tr_whip(a, b, p, -1, 0), whipR=lambda a, b, p: tr_whip(a, b, p, 1, 0),
          whipU=lambda a, b, p: tr_whip(a, b, p, 0, -1), ripple=tr_ripple, luma=tr_luma, spin=tr_spin, flash=tr_flash,
          punch=tr_punch, leak=tr_leak, lightning=tr_lightning)
HALF = dict(zoom=6, whipL=5, whipR=5, whipU=5, ripple=7, luma=7, spin=6, flash=3, punch=2, leak=7, lightning=4)


# ---------------------------------------------------------------- simple joiner
def load_shot(path, n, pad):
    if path.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
        img = cv2.imread(path); h, w = img.shape[:2]; s = max(W / w, H / h)
        img = cv2.resize(img, (math.ceil(w * s), math.ceil(h * s)), interpolation=cv2.INTER_AREA)
        y, x = (img.shape[0] - H) // 2, (img.shape[1] - W) // 2; img = img[y:y + H, x:x + W]
        return [zoom(img, 1 + 0.07 * k / (n + 2 * pad)) for k in range(n + 2 * pad)]
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', path, '-frames:v', str(n + 2 * pad), '-an', '-vf',
                          f'fps={FPS},scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H}',
                          '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-'], capture_output=True).stdout
    k = len(raw) // (W * H * 3); fr = list(np.frombuffer(raw[:k * W * H * 3], np.uint8).reshape(k, H, W, 3))
    while len(fr) < n + 2 * pad: fr.append(fr[-1])
    return fr


def join(paths, trans, durs, out, pad=8):
    """the first `pad` frames of each clip are used as the pre-cut half of its incoming transition"""
    pr = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{W}x{H}', '-r', str(FPS),
                           '-i', '-', '-c:v', 'libx264', '-crf', '19', '-maxrate', '12M', '-bufsize', '24M', '-pix_fmt', 'yuv420p', out],
                          stdin=subprocess.PIPE)
    shots = [load_shot(p, int(d * FPS), pad) for p, d in zip(paths, durs)]
    for k, fr in enumerate(shots):
        n = int(durs[k] * FPS)
        hin = HALF[trans[k - 1]] if k else 0
        hout = HALF[trans[k]] if k < len(shots) - 1 else 0
        for i in range(hin, n - hout):
            if i < hin: continue
            pr.stdin.write(fr[pad + i].tobytes())
        if hout:
            nxt = shots[k + 1]; t = TR[trans[k]]
            for j in range(-hout, hout):
                p = (j + hout + 0.5) / (2 * hout)
                a = fr[min(len(fr) - 1, pad + n + j)]; b = nxt[pad + j]
                pr.stdin.write(t(a, b, p).tobytes())
    pr.stdin.close(); pr.wait()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--clips'); ap.add_argument('--trans', default=''); ap.add_argument('--durs', default='')
    ap.add_argument('--demo'); ap.add_argument('--out', required=True)
    a = ap.parse_args()
    if a.demo:
        x, y = a.demo.split(','); names = list(TR)
        paths = [x if i % 2 == 0 else y for i in range(len(names) + 1)]
        join(paths, names, [1.5] * len(paths), a.out); return
    paths = a.clips.split(','); trans = a.trans.split(',') if a.trans else ['ripple'] * (len(paths) - 1)
    durs = [float(d) for d in a.durs.split(',')] if a.durs else [2.0] * len(paths)
    join(paths, trans, durs, a.out)


if __name__ == '__main__':
    main()
