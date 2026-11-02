#!/usr/bin/env python3
"""Change the image on every clap / hand-percussion hit of a song.

Clap detection: STFT (nperseg 1024, hop 220) -> 2-8 kHz band energy -> positive log flux ->
peaks above --thresh at least 0.18 s apart. 0.35 gave ~66 cuts in 34 s (every clap),
0.45 ~48 (only the strong ones). Each cut: small punch-in (+10 %, 90 ms) and a white flash
(35 %, 60 ms), then a slow 3 % push until the next clap. Images alternate between the
folders given (A, B, A, B ...) and are reused when there are fewer images than claps,
never twice in a row.

  python3 clap_cut_sync.py song.mp3 out.mp4 --dirs imgsA imgsB --thresh 0.35 [--exclude bhangra couple]
"""
import argparse, glob, os, random, subprocess
import numpy as np, cv2, soundfile as sf
from scipy.signal import stft, find_peaks

W, H, FPS = 1080, 1920, 30


def claps(audio, thresh):
    wav = '/tmp/_clap.wav'
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', audio, '-ac', '1', '-ar', '22050', wav], check=True)
    y, sr = sf.read(wav)
    f, t, Z = stft(y, sr, nperseg=1024, noverlap=1024 - 220)
    hi = np.abs(Z)[(f > 2000) & (f < 8000)].sum(0)
    flux = np.maximum(0, np.diff(np.log1p(hi * 10), prepend=np.log1p(hi[0] * 10)))
    flux /= flux.max() or 1
    pk, _ = find_peaks(flux, height=thresh, distance=int(0.18 / (t[1] - t[0])))
    return [0.0] + [float(x) for x in t[pk] if x > 0.25], len(y) / sr


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('audio'); ap.add_argument('out')
    ap.add_argument('--dirs', nargs='+', required=True)
    ap.add_argument('--thresh', type=float, default=0.35)
    ap.add_argument('--exclude', nargs='*', default=[], help='skip files whose name contains any of these words')
    a = ap.parse_args()
    cuts, dur = claps(a.audio, a.thresh)
    pools = []
    for d in a.dirs:
        fs = [f for f in sorted(glob.glob(os.path.join(d, '**', '*.*'), recursive=True))
              if f.lower().endswith(('png', 'jpg', 'jpeg', 'webp')) and not any(x.lower() in f.lower() for x in a.exclude)]
        random.Random(7).shuffle(fs); pools.append(fs)
    seq = [pools[k % len(pools)][(k // len(pools)) % len(pools[k % len(pools)])] for k in range(len(cuts))]
    cache = {}

    def load(p):
        if p not in cache:
            im = cv2.imread(p); h, w = im.shape[:2]; s = max(W / w, H / h) * 1.12
            cache[p] = cv2.resize(im, (int(w * s), int(h * s)), interpolation=cv2.INTER_AREA)
        return cache[p]

    def frame(tt):
        k = max(i for i, c in enumerate(cuts) if c <= tt); c0 = cuts[k]; c1 = cuts[k + 1] if k + 1 < len(cuts) else dur
        im = load(seq[k]); dt = tt - c0; p = min(1, dt / max(0.2, c1 - c0))
        z = 1.0 + 0.10 * np.exp(-dt / 0.09) + 0.03 * p
        ih, iw = im.shape[:2]; cw, ch = int(iw / 1.12 / z), int(ih / 1.12 / z)
        x0 = (iw - cw) // 2 + int(np.sin(k) * 20 * p); y0 = (ih - ch) // 2
        f = cv2.resize(im[y0:y0 + ch, x0:x0 + cw], (W, H)).astype(np.float32)
        fl = np.exp(-dt / 0.06) * 0.35
        return np.clip(f * (1 - fl) + 255 * fl, 0, 255).astype(np.uint8)

    p = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                          '-i', a.audio, '-map', '0:v', '-map', '1:a', '-shortest', '-c:v', 'libx264', '-crf', '24', '-maxrate', '5M',
                          '-bufsize', '10M', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart', a.out], stdin=subprocess.PIPE)
    for i in range(int(dur * FPS)):
        p.stdin.write(frame(i / FPS).tobytes())
    p.stdin.close(); p.wait()
    print(f'{len(cuts)} cuts, {len(set(seq))} images')


if __name__ == '__main__':
    main()
