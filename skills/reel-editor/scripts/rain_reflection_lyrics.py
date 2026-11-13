#!/usr/bin/env python3
"""Rain-reflection lyric captions ("Barsaat reflection").

Word-timed Hindi lyric captions for painted / rainy / golden-hour reels:
  * words write on one by one and build a centred block per lyric line
  * connecting words: Tiro Devanagari Hindi, cream; key words: big Amita 700, gold gradient + bloom,
    light sweep and a 4-point sparkle when sung
  * the whole block is mirrored underneath as a rippling wet-pavement reflection
  * each line washes away downward (vertical blur + drift) before the next one
  * look pass over the whole video: soft highlight bloom, warm/teal split tone, vignette, gold dust, grain

Input: a word-per-event ASS file (text + which words are "key" = any event whose colour differs from the
most common colour) and a timing JSON:
  {"lines": [9, 8, 2, ...],            # words per lyric line
   "starts": [0.0, 0.88, ...],         # one start time per word (seconds), verified against the vocal
   "hero_last": true,                  # last word alone on its own line, extra large
   "base_y": {"0": 930},               # optional: baseline per line, to keep text off the subject in that shot
   "rows": {"2": [5, 3]}}              # optional: words per row for a line (default: balanced wrap)
Usage:
  python rain_reflection_lyrics.py in.mp4 captions.ass timing.json out.mp4 [--stills 1.0,5.2 --sheet sheet.jpg]
"""
import re, json, math, subprocess, sys, argparse, os
from collections import Counter
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
FD = os.environ.get('REEL_FONTS', os.path.join(HERE, '..', 'fonts'))
W, H, FPS = 1080, 1920, 30
F_BODY = os.path.join(FD, 'deva', 'tiro-devanagari-hindi-devanagari-400.ttf')
F_KEY = os.path.join(FD, 'deva', 'amita-devanagari-700.ttf')
S_BODY, S_KEY, S_HERO = 92, 146, 216
BASE_Y = 1325                      # baseline of the last text line (inside the IG safe zone)
MAXW = 940
CREAM = np.array([226, 244, 255], np.float32)                       # BGR
GOLD_TOP, GOLD_MID, GOLD_BOT = [np.array(c, np.float32) for c in ([190, 244, 255], [104, 212, 255], [52, 158, 236])]
GLOW = np.array([60, 170, 255], np.float32)
PAD = 60


def font(path, size):
    return ImageFont.truetype(path, size, layout_engine=ImageFont.Layout.RAQM)


def parse_ass(path):
    words = []
    for ln in open(path, encoding='utf-8'):
        if not ln.startswith('Dialogue:'):
            continue
        text = ln.split(',', 9)[9].strip()
        col = re.search(r'\\c&H([0-9A-Fa-f]+)&', text)
        words.append((re.sub(r'\{[^}]*\}', '', text).strip(), col.group(1) if col else ''))
    base = Counter(c for _, c in words).most_common(1)[0][0]
    return [(w, c != base) for w, c in words]


class Word:
    def __init__(self, text, key, hero, start):
        self.text, self.key, self.start = text, key or hero, start
        f = font(F_KEY, S_HERO if hero else S_KEY) if self.key else font(F_BODY, S_BODY)
        l, t, r, b = f.getbbox(text, anchor='ls')
        self.adv = f.getlength(text)
        im = Image.new('L', (int(r - l) + 2 * PAD, int(b - t) + 2 * PAD), 0)
        ImageDraw.Draw(im).text((PAD - l, PAD - t), text, font=f, fill=255, anchor='ls')
        self.m = np.asarray(im, np.float32) / 255
        self.off = (l - PAD, t - PAD)
        self.soft = cv2.GaussianBlur(self.m, (0, 0), 9)
        self.g = cv2.GaussianBlur(self.m, (0, 0), 20 if self.key else 8)
        self.sh = np.clip(cv2.GaussianBlur(self.m, (0, 0), 7) + cv2.GaussianBlur(cv2.dilate(self.m, np.ones((7, 7), np.uint8)), (0, 0), 2.5) * .8, 0, 1)
        h = self.m.shape[0]
        if self.key:
            u = np.clip((np.arange(h) - PAD) / max(1, h - 2 * PAD), 0, 1)[:, None, None]
            self.col = np.where(u < .5, GOLD_TOP + (GOLD_MID - GOLD_TOP) * u * 2, GOLD_MID + (GOLD_BOT - GOLD_MID) * (u - .5) * 2)
        else:
            self.col = np.broadcast_to(CREAM, (h, 1, 3))
        self.col = self.col.astype(np.float32)


class Phrase:
    def __init__(self, words, hero_last, base=BASE_Y, rows=None):
        self.words, self.base = words, base
        gap = 24
        fixed = None
        if rows:                                            # explicit words-per-row override
            fixed, k = [], 0
            for n in rows:
                fixed.append(words[k:k + n]); k += n
        rows = [words[:-1], words[-1:]] if hero_last and len(words) > 1 else [words]
        out = []
        for row in ([] if fixed else rows):                                    # balanced wrap to <= MAXW
            n = 1
            while True:
                best = self._split(row, n, gap)
                if max(self._w(r, gap) for r in best) <= MAXW or n >= len(row):
                    break
                n += 1
            out += best
        out = fixed or out
        self.rows = out
        y = base
        for row in reversed(out):                           # stack upward from the base line
            lh = max((S_HERO * 1.02 if w.m.shape[0] > S_KEY * 1.9 else S_KEY * 1.0) if w.key else S_BODY * 1.42 for w in row)
            x = (W - self._w(row, gap)) / 2
            for w in row:
                w.x, w.y = int(round(x + w.off[0])), int(round(y + w.off[1]))
                x += w.adv + gap
            y -= lh
        self.top = int(min(w.y for w in words)) + PAD - 30
        self.start = words[0].start
        self.r0, self.r1 = max(0, self.top - 110), min(H, base + 360)
        plate = np.zeros((self.r1 - self.r0, W), np.float32)
        for w in words:
            put(plate, w.m, w.x, w.y - self.r0, 1)
        self.plate = np.clip(cv2.GaussianBlur(np.clip(plate, 0, 1), (0, 0), 70) * 3.2, 0, 1) * 0.40

    @staticmethod
    def _w(row, gap):
        return sum(w.adv for w in row) + gap * (len(row) - 1)

    def _split(self, row, n, gap):
        if n == 1:
            return [row]
        best, bc = None, 1e9
        import itertools
        for cuts in itertools.combinations(range(1, len(row)), n - 1):
            parts = [row[a:b] for a, b in zip((0,) + cuts, cuts + (len(row),))]
            c = max(self._w(p, gap) for p in parts) - min(self._w(p, gap) for p in parts)
            if c < bc:
                best, bc = parts, c
        return best


def put(dst, src, x, y, gain, col=None):
    """Add src*gain (optionally tinted) into dst at x,y with clipping."""
    h, w = src.shape[:2]
    x0, y0, x1, y1 = max(0, x), max(0, y), min(dst.shape[1], x + w), min(dst.shape[0], y + h)
    if x1 <= x0 or y1 <= y0:
        return
    s = src[y0 - y:y1 - y, x0 - x:x1 - x] * gain
    if col is None:
        dst[y0:y1, x0:x1] += s
    else:
        c = col[y0 - y:y1 - y] if col.shape[0] == h else col
        dst[y0:y1, x0:x1] += s[..., None] * c


def star(r):
    y, x = np.mgrid[-r:r + 1, -r:r + 1].astype(np.float32)
    s = np.exp(-(x / (r * .42)) ** 2 - (y / 2.2) ** 2) + np.exp(-(y / (r * .42)) ** 2 - (x / 2.2) ** 2) + 1.4 * np.exp(-(x * x + y * y) / 26)
    return np.clip(s, 0, 1.6)


STAR = star(46)
_rng = np.random.default_rng(7)
DUST = [dict(x=_rng.uniform(0, W), y=_rng.uniform(0, H), v=_rng.uniform(10, 38), r=int(_rng.choice([3, 4, 5, 7, 10, 15])),
             ph=_rng.uniform(0, 6.28), sw=_rng.uniform(8, 30), a=_rng.uniform(.25, .8)) for _ in range(54)]
DSPR = {r: np.exp(-(np.mgrid[-3 * r:3 * r + 1, -3 * r:3 * r + 1].astype(np.float32) ** 2).sum(0) / (2 * r * r)) for r in (3, 4, 5, 7, 10, 15)}
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
_r = np.sqrt(((xx - W / 2) / (W * .78)) ** 2 + ((yy - H / 2) / (H * .62)) ** 2)
VIG = (1 - 0.46 * np.clip((_r - .52) / .55, 0, 1) ** 2).astype(np.float32)
INV = 1 - VIG
BLACK = np.zeros((H, W, 3), np.uint8)
_x = np.arange(256) / 255.0
_s = _x - 0.035 * np.sin(2 * np.pi * _x)
LUT = np.stack([np.clip((_s + 0.03 * (1 - _x) ** 2 - 0.018 * _x) * 255, 0, 255),       # B: cool shadows
                np.clip(_s * 255, 0, 255),
                np.clip((_s + 0.03 * _x * _x) * 255, 0, 255)], 1).astype(np.uint8).reshape(256, 1, 3)   # R: warm highs
GRAIN = [np.clip(128 + cv2.resize(_rng.normal(0, 5.5, (H // 2, W // 2)).astype(np.float32), (W, H)), 0, 255).astype(np.uint8) for _ in range(6)]
GRAIN = [cv2.merge([g, g, g]) for g in GRAIN]


def look(fr, t, n):
    fr = cv2.LUT(fr, LUT)
    sm = cv2.resize(fr, (W // 8, H // 8), interpolation=cv2.INTER_AREA).astype(np.float32)
    bl = cv2.GaussianBlur(np.clip(sm - 150, 0, None) * 1.5, (0, 0), 7)
    fr = cv2.add(fr, cv2.resize(np.clip(bl * .55, 0, 255).astype(np.uint8), (W, H), interpolation=cv2.INTER_LINEAR))
    fr = cv2.blendLinear(fr, BLACK, VIG, INV)
    for d in DUST:                                           # floating gold dust / bokeh
        y = (d['y'] - d['v'] * t) % (H + 80) - 40
        x = d['x'] + d['sw'] * math.sin(t * .6 + d['ph'])
        a = d['a'] * (.55 + .45 * math.sin(t * 2.1 + d['ph'] * 3)) * (22 if d['r'] > 6 else 60)
        s = DSPR[d['r']]; r = s.shape[0] // 2
        x0, y0 = int(x) - r, int(y) - r
        if x0 < 0 or y0 < 0 or x0 + s.shape[1] > W or y0 + s.shape[0] > H:
            continue
        roi = fr[y0:y0 + s.shape[0], x0:x0 + s.shape[1]]
        roi[:] = cv2.add(roi, (s[..., None] * a * (GLOW / 255 * .6 + .4)).astype(np.uint8))
    return fr


def captions(fr, t, phrases, dur):
    for i, p in enumerate(phrases):
        nxt = phrases[i + 1].start if i + 1 < len(phrases) else dur - 0.55
        ex1 = nxt - 0.06
        ex0 = max(p.words[-1].start + 0.45, ex1 - 0.5)
        if not (p.start - 0.2 <= t < ex1):
            continue
        u = min(1, max(0, (t - ex0) / max(.01, ex1 - ex0)))
        h = p.r1 - p.r0
        fa, frgb, gl, sh = np.zeros((h, W), np.float32), np.zeros((h, W, 3), np.float32), np.zeros((h, W, 3), np.float32), np.zeros((h, W), np.float32)
        for w in p.words:
            e = (t - w.start) / 0.42
            if e <= 0:
                continue
            e = 1 - (1 - min(1, e)) ** 3
            y = w.y - p.r0 + int((1 - e) * 30)
            m = w.soft * (1 - e) + w.m * e
            put(fa, m, w.x, y, e)
            put(frgb, m, w.x, y, e, w.col)
            put(sh, w.sh, w.x, y + 6, e)
            sung = t - w.start
            if w.key:
                swell = math.exp(-max(0, sung - .25) / 1.1)
                put(gl, w.g, w.x, y, e * (.42 + .55 * swell + .06 * math.sin(t * 2.4)), np.broadcast_to(GLOW, (1, 1, 3)))
                if sung < .9:                                # light sweep across the word
                    hh, ww = w.m.shape
                    px = -90 + (ww + 180) * sung / .9
                    X, Y = np.meshgrid(np.arange(ww, dtype=np.float32), np.arange(hh, dtype=np.float32))
                    put(frgb, w.m * np.exp(-((X - px + (Y - hh / 2) * .5) / 40) ** 2), w.x, y, 150 * e, np.ones((1, 1, 3), np.float32))
                if sung < .7:                                # sparkle
                    k = math.sin(math.pi * sung / .7)
                    s = cv2.resize(STAR, None, fx=.5 + .7 * k, fy=.5 + .7 * k)
                    put(gl, s, w.x + w.m.shape[1] - PAD - s.shape[1] // 2, y + PAD - s.shape[0] // 2 + 10, 210 * k, np.array([[[200, 235, 255]]], np.float32))
            else:
                put(gl, w.g, w.x, y, e * .16, np.broadcast_to(GLOW, (1, 1, 3)))
        pin = min(1, max(0, (t - p.start + .2) / .5))
        if i == 0:
            pin = 1
        if u > 0:                                            # rain-wash exit: vertical smear, drift down, fade
            k = 1 + 2 * int(u * 38)
            M = np.float32([[1, 0, 0], [0, 1, 50 * u * u]])
            f = (1 - u) ** 1.4
            fa, frgb, gl, sh = [cv2.warpAffine(cv2.blur(a, (1, k)), M, (W, h)) * f for a in (fa, frgb, gl, sh)]
            pin *= 1 - u
        # wet-pavement reflection
        my = p.base + 66 - p.r0
        src = np.dstack([np.clip(frgb + gl * .5, 0, 255), np.clip(fa, 0, 1)])[max(0, my - 420):my][::-1]
        rh = min(h - my, int(src.shape[0] * .55))
        ref = cv2.resize(src, (W, rh), interpolation=cv2.INTER_AREA)
        ry, rx = np.mgrid[0:rh, 0:W].astype(np.float32)
        ref = cv2.remap(ref, rx + (2 + 9 * ry / rh) * np.sin(ry * .17 - t * 3.4) + 2 * np.sin(ry * .61 + t * 5.1), ry, cv2.INTER_LINEAR)
        ref = cv2.GaussianBlur(ref, (0, 0), 1.6)
        fade = ((1 - ry[:, :1] / rh) ** 1.5 * .46)
        roi = fr[p.r0:p.r1].astype(np.float32)
        roi *= (1 - p.plate * pin)[..., None]
        roi *= (1 - np.clip(sh, 0, 1) * .62)[..., None]
        roi += gl
        a = np.clip(fa, 0, 1)[..., None]
        roi = roi * (1 - a) + np.minimum(frgb, 255 * a + 150 * (frgb > 255 * a))
        rr = roi[my:my + rh]
        ra = ref[..., 3:] * fade[..., None]
        rr[:] = rr * (1 - ra * .55) + ref[..., :3] * fade[..., None]
        fr[p.r0:p.r1] = np.clip(roi, 0, 255).astype(np.uint8)
    return fr


def build(ass, timing):
    tj = json.load(open(timing))
    raw = parse_ass(ass)
    assert len(raw) == len(tj['starts']) == sum(tj['lines']), (len(raw), len(tj['starts']), sum(tj['lines']))
    phrases, k = [], 0
    for li, n in enumerate(tj['lines']):
        last = li == len(tj['lines']) - 1
        ws = [Word(raw[k + j][0], raw[k + j][1], last and tj.get('hero_last') and j == n - 1, tj['starts'][k + j]) for j in range(n)]
        phrases.append(Phrase(ws, last and tj.get('hero_last'), tj.get('base_y', {}).get(str(li), BASE_Y), tj.get('rows', {}).get(str(li))))
        k += n
    phrases[0].words[0].start = -1.0                         # hook: first word already on screen at frame 0
    return phrases


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('video'); ap.add_argument('ass'); ap.add_argument('timing'); ap.add_argument('out')
    ap.add_argument('--stills'); ap.add_argument('--sheet')
    a = ap.parse_args()
    dur = float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', a.video], capture_output=True, text=True).stdout)
    phrases = build(a.ass, a.timing)
    dec = ['ffmpeg', '-v', 'error', '-i', a.video, '-vf', f'scale={W}:{H},fps={FPS}', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-']
    if a.stills:
        tiles = []
        for ts in a.stills.split(','):
            t = float(ts)
            raw = subprocess.run(['ffmpeg', '-v', 'error', '-ss', ts, '-i', a.video, '-frames:v', '1', '-vf', f'scale={W}:{H}', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-'], capture_output=True).stdout
            fr = np.frombuffer(raw, np.uint8).reshape(H, W, 3).copy()
            fr = captions(look(fr, t, int(t * FPS)), t, phrases, dur)
            fr = cv2.addWeighted(fr, 1, GRAIN[0], 1, -128)
            cv2.imwrite(f'{a.out}_{ts}.jpg', fr, [cv2.IMWRITE_JPEG_QUALITY, 90])
            tiles.append(cv2.resize(fr, (360, 640), interpolation=cv2.INTER_AREA))
        if a.sheet:
            cols = 6
            while len(tiles) % cols:
                tiles.append(np.zeros_like(tiles[0]))
            cv2.imwrite(a.sheet, np.vstack([np.hstack(tiles[i:i + cols]) for i in range(0, len(tiles), cols)]), [cv2.IMWRITE_JPEG_QUALITY, 88])
        return
    p_in = subprocess.Popen(dec, stdout=subprocess.PIPE)
    p_out = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                              '-i', a.video, '-map', '0:v', '-map', '1:a?', '-c:v', 'libx264', '-preset', 'medium', '-crf', '17', '-pix_fmt', 'yuv420p',
                              '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709', '-c:a', 'aac', '-b:a', '256k',
                              '-movflags', '+faststart', '-shortest', a.out], stdin=subprocess.PIPE)
    n = 0
    while True:
        raw = p_in.stdout.read(W * H * 3)
        if len(raw) < W * H * 3:
            break
        t = n / FPS
        fr = np.frombuffer(raw, np.uint8).reshape(H, W, 3).copy()
        fr = captions(look(fr, t, n), t, phrases, dur)
        fr = cv2.addWeighted(fr, 1, GRAIN[n % len(GRAIN)], 1, -128)
        p_out.stdin.write(fr.tobytes())
        n += 1
        if n % 150 == 0:
            print(n, flush=True)
    p_out.stdin.close(); p_out.wait()


if __name__ == '__main__':
    main()
