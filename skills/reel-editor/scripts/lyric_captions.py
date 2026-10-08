"""Word-by-word lyric captions over still images, in the "sky is the canvas" style:
one word at a time in the sky area. HUGE red calligraphy words slam in while the photo turns black &
white; small white words fade up on the colour photo. Red words get a small spaced roman transliteration.

  python lyric_captions.py --spec spec.json --audio song.mp4 --out reel.mp4

spec.json:
{
  "images": {"a": "img_back.png", "b": "img_seated.png"},
  "anchors": {"a": [540, 470], "b": [600, 420]},          # text centre in the sky, per image (1080x1920)
  "lines": [
    {"start": 0.0, "end": 8.0, "words": [
       {"w": "अयि", "style": "W", "img": "a"},
       {"w": "गिरिनन्दिनि", "style": "R", "img": "a", "font": "amita", "roman": "GIRINANDINI"},
       {"w": "शैलसुते", "style": "R", "img": "b", "font": "rozha", "roman": "SHAILASUTE", "swash": true}]}
  ]
}
Word start times are spread across each line by syllable count and snapped to the nearest vocal
onset (librosa). Add "t": 1.23 to a word to force its start time.
Fonts: amita (flowing pen calligraphy), rozha (bold calligraphy), eczar (heaviest, power words).
"""
import argparse, json, math, os, subprocess, sys
import numpy as np, cv2, librosa
from PIL import Image, ImageDraw, ImageFont, ImageFilter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from deva_kit import swash

W, H, FPS = 1080, 1920, 30
FD = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'fonts')
DV = os.path.join(FD, 'deva')
FONTS = {'amita': 'amita-devanagari-700.ttf', 'rozha': 'rozha-one-devanagari-400.ttf', 'eczar': 'eczar-devanagari-800.ttf'}
SMALL = 'tiro-devanagari-hindi-devanagari-400.ttf'
ROMAN = os.path.join(FD, 'cinzel-400.ttf')
RED, WHITE = (232, 18, 26), (255, 255, 255)


def aks(w):
    c = sum(1 for ch in w if 'क' <= ch <= 'ह' or 'ऄ' <= ch <= 'औ' or ch.isalpha() and ch.isascii())
    return max(1, c - w.count('्'))


def dtext(s, font, size, color):
    ft = ImageFont.truetype(font, int(size), layout_engine=ImageFont.Layout.RAQM)
    b = ft.getbbox(s); pad = int(size * 0.6)
    im = Image.new('RGBA', (b[2] - b[0] + 2 * pad, b[3] - b[1] + 2 * pad))
    ImageDraw.Draw(im).text((pad - b[0], pad - b[1]), s, font=ft, fill=color)
    return im.crop(im.getbbox())


def spaced(s, size, color, sp):
    ft = ImageFont.truetype(ROMAN, size)
    ws = [ft.getbbox(c)[2] for c in s]; tw = sum(ws) + sp * (len(s) - 1)
    im = Image.new('RGBA', (tw + 20, size * 2)); d = ImageDraw.Draw(im); x = 10
    for c, w in zip(s, ws):
        d.text((x, size // 2), c, font=ft, fill=color); x += w + sp
    return im.crop(im.getbbox())


def glow(im, rad, a, col=(0, 0, 0)):
    pad = rad * 3
    sh = Image.new('RGBA', im.size, col + (0,)); sh.putalpha(im.split()[3].point(lambda v: int(v * a)))
    out = Image.new('RGBA', (im.width + 2 * pad, im.height + 2 * pad)); out.alpha_composite(sh, (pad, pad + 4))
    out = out.filter(ImageFilter.GaussianBlur(rad)); out.alpha_composite(im, (pad, pad))
    return out


def fit_bg(path):
    b = cv2.imread(path)
    s = max(W / b.shape[1], H / b.shape[0])
    b = cv2.resize(b, (math.ceil(b.shape[1] * s), math.ceil(b.shape[0] * s)), interpolation=cv2.INTER_LANCZOS4)
    y, x = (b.shape[0] - H) // 2, (b.shape[1] - W) // 2
    return b[y:y + H, x:x + W]


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--spec', required=True); p.add_argument('--audio', required=True); p.add_argument('--out', required=True)
    a = p.parse_args()
    S = json.load(open(a.spec))
    base = os.path.dirname(os.path.abspath(a.spec))
    wav = os.path.join(os.path.dirname(os.path.abspath(a.out)), '_lyric_audio.wav')
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', a.audio, '-vn', '-ac', '1', '-ar', '22050', wav], check=True)
    y, sr = librosa.load(wav, sr=22050)
    dur = len(y) / sr
    ons = librosa.onset.onset_detect(y=y, sr=sr, units='time', backtrack=True, delta=0.05)

    words = []
    for L in S['lines']:
        ws = L['words']; s, e = L['start'], L['end']
        wt = np.array([aks(w['w']) + 1.5 for w in ws], float)
        st = s + 0.1 + np.concatenate([[0], np.cumsum(wt)[:-1]]) / wt.sum() * (e - s - 0.6)
        for w, t in zip(ws, st):
            if 't' not in w:
                near = ons[np.abs(ons - t) < 0.25]
                t = float(near[np.abs(near - t).argmin()]) if len(near) else float(t)
            words.append((float(w.get('t', t)), w))
    words.sort(key=lambda x: x[0]); words[0] = (0.0, words[0][1])
    for t, w in words:
        print(f"{t:6.2f}  {w['style']}  {w['img']}  {w['w']}")

    SPR = []
    for _, w in words:
        if w['style'] == 'R':
            im = dtext(w['w'], os.path.join(DV, FONTS[w.get('font', 'rozha')]), 330 if len(w['w']) <= 6 else 260, RED)
            if w.get('swash'): im = swash(im, RED, 'right', reach=0.35, drop=0.35)
            if im.width > 880: im = im.resize((880, int(im.height * 880 / im.width)), Image.LANCZOS)
            SPR.append((glow(im, 10, 0.35), glow(spaced(w['roman'], 44, WHITE, 8), 8, 0.85) if w.get('roman') else None))
        else:
            im = dtext(w['w'], os.path.join(DV, SMALL), 120, WHITE)
            if im.width > 900: im = im.resize((900, int(im.height * 900 / im.width)), Image.LANCZOS)
            SPR.append((glow(im, 12, 0.6), None))
    BG = {k: fit_bg(os.path.join(base, v)) for k, v in S['images'].items()}
    ANCH = {k: tuple(v) for k, v in S['anchors'].items()}
    starts = [t for t, _ in words]
    seg = {k: words[k][0] for k in range(len(words)) if k == 0 or words[k - 1][1]['img'] != words[k][1]['img']}

    N = int(dur * FPS)
    pr = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                           '-i', a.audio, '-map', '0:v', '-map', '1:a', '-af', f'afade=t=out:st={dur - 0.8:.2f}:d=0.8',
                           '-c:v', 'libx264', '-crf', '18', '-maxrate', '12M', '-bufsize', '24M', '-preset', 'slow', '-pix_fmt', 'yuv420p',
                           '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', a.out], stdin=subprocess.PIPE)
    for n in range(N):
        t = n / FPS
        k = max(i for i, s in enumerate(starts) if s <= t + 1e-6)
        w = words[k][1]; red = w['style'] == 'R'; last = k == len(words) - 1
        ks = max(i for i in seg if i <= k)
        z = 1.0 + 0.012 * (t - seg[ks])                       # slow push per image
        M = cv2.getRotationMatrix2D((W / 2, H * 0.6), 0, z)
        f = cv2.warpAffine(BG[w['img']], M, (W, H), borderMode=cv2.BORDER_REFLECT).astype(np.float32)
        u = t - starts[k]
        if red:                                               # black & white frame under red words
            g = cv2.cvtColor(f.astype(np.uint8), cv2.COLOR_BGR2GRAY).astype(np.float32)[..., None].repeat(3, 2)
            g = np.clip((g - 128) * 1.12 + 128, 0, 255)
            mix = 0.92
            if last and t > dur - 1.5: mix *= max(0, 1 - (t - (dur - 1.5)) / 1.0)   # colour bloom on the final word
            f = f * (1 - mix) + g * mix
            if u < 2 / FPS: f = f * 0.7 + 255 * 0.3              # 2-frame flash on the slam
        frame = Image.fromarray(cv2.cvtColor(np.clip(f, 0, 255).astype(np.uint8), cv2.COLOR_BGR2RGB)).convert('RGBA')
        im, sub = SPR[k]
        ax, ay = ANCH[w['img']]
        hw = im.width / 2 - 25; ax = min(max(ax, hw + 30), W - hw - 30)
        if red:
            e = min(1, u / 0.17); sc = 1.15 - 0.15 * (1 - (1 - e) ** 3) + 0.02 * min(u, 3) / 3; al = min(1, u / 0.07)
        else:
            e = min(1, u / 0.2); sc = 1.0; al = e; ay = ay + 24 * (1 - e) ** 2
        s2 = im.resize((max(1, int(im.width * sc)), max(1, int(im.height * sc))), Image.LANCZOS) if sc != 1 else im
        if al < 1:
            s2 = s2.copy(); s2.putalpha(s2.split()[3].point(lambda v: int(v * al)))
        frame.alpha_composite(s2, (int(ax - s2.width / 2), int(ay - s2.height / 2)))
        if sub is not None and u > 0.12:
            sa = min(1, (u - 0.12) / 0.25); s3 = sub.copy(); s3.putalpha(s3.split()[3].point(lambda v: int(v * sa)))
            frame.alpha_composite(s3, (int(ax - s3.width / 2), int(ay + im.height / 2 + 10)))
        out = np.array(frame.convert('RGB'))[..., ::-1].astype(np.float32)
        if t > dur - 0.55: out *= max(0, (dur - t) / 0.55)
        pr.stdin.write(np.clip(out, 0, 255).astype(np.uint8).tobytes())
    pr.stdin.close(); pr.wait(); os.remove(wav)
    print('done', a.out)


if __name__ == '__main__':
    main()
