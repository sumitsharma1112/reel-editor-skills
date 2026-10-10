"""Sansoon Ki Mala – white page, giant red calligraphy (roman phonetic lyrics), words stack one by one like the
Barsaat/Banjaare reel. Held notes stretch live: raang → raaaaaaang, letter by letter on the ASS timings."""
import subprocess, math, re, numpy as np
from PIL import Image, ImageDraw, ImageFont

W, H, FPS, DUR = 1080, 1920, 30, 47.0
FONT = '/home/claude/reel-editor-skills/skills/reel-editor/fonts/berkshire-swash-400.ttf'
RED = np.array([234, 0, 0], np.float32)
CONDENSE = 0.80
MAXW, MAXH, CY = 960, 1150, 980          # block stays in y≈405-1555: below IG header, inside the 4:5 crop

# (final text, start, stretch_end, base run length)  – stretch grows the repeated letter from base → final
G = [
    [('Prem', 3.00), ('ka', 3.35)],
    [('raaaaaaaaaaaaang', 3.78, 5.30, 1)],
    [('main', 5.35)],
    [('Aisi', 5.90), ('doobi', 6.60)],
    [('ban', 7.60), ('gaya', 8.05)],
    [('ek', 8.60), ('hi', 8.85), ('roop', 9.10)],
    [('Preeeeeeeeem', 10.20, 11.45, 1)],
    [('ka', 11.48)],
    [('raaaaaaaaaang', 11.88, 14.85, 1)],
    [('main', 15.00)],
    [('Aisi', 15.70), ('doobi', 16.40)],
    [('ban', 17.20), ('gaya', 17.85)],
    [('ek', 18.30), ('hi', 18.50)],
    [('roooooooop', 18.70, 19.70, 2)],
    [('Prem', 20.10), ('ki', 20.40), ('maala', 20.90)],
    [('japte', 21.60), ('japte', 22.30)],
    [('Aaaaaap', 23.40, 25.10, 2)],
    [('bani', 25.20)],
    [('maaaaain', 26.00, 26.95, 1)],
    [('shyaaaaaam', 27.05, 28.95, 2)],
    [('Sansooooooooon', 29.60, 30.35, 2)],
    [('ki', 30.40)],
    [('maaaaaaaaaala', 30.90, 31.95, 2)],
    [('pe', 32.05)],
    [('Simroon', 33.05), ('main', 33.60)],
    [('pee', 34.05), ('ka', 34.25)],
    [('naaaaaaaaaaam', 34.50, 35.85, 2)],
    [('Sansoooooooooon', 36.40, 37.20, 2)],
    [('ki', 37.60), ('maala', 38.10)],
    [('peeeeeeeee', 38.85, 39.60, 1)],
    [('Sansoon', 40.15), ('ki', 40.90), ('maala', 41.25)],
    [('peeeeeee', 41.95, 42.60, 1)],
    [('Simroon', 42.85), ('main', 43.45)],
    [('peeeeeee', 43.90, 45.05, 2)],
    [('ka', 45.05), ('naaaaaaam', 45.20, 45.95, 2)],
]
END = 46.6

def current(w, t):
    """text of a word at time t (stretched run grows with the held note)"""
    if len(w) == 2: return w[0]
    txt, st, se, base = w
    low = txt.lower(); best = (0, 0)
    i = 0
    while i < len(low):
        j = i
        while j < len(low) and low[j] == low[i]: j += 1
        if j - i > best[1] - best[0]: best = (i, j)
        i = j
    a, b = best; L = b - a
    n = base + int(round((L - base) * min(1, max(0, (t - st) / (se - st)))))
    return txt[:a] + txt[a] + low[a] * (n - 1) + txt[b:]

_ft = ImageFont.truetype(FONT, 400); _cache = {}
def glyph(word):
    if word not in _cache:
        im = Image.new('L', (int(_ft.getlength(word)) + 400, 900))
        ImageDraw.Draw(im).text((150, 200), word, font=_ft, fill=255)
        bb = im.getbbox(); asc = _ft.getbbox('Ab')            # consistent line box so baselines don't jump
        im = im.crop((bb[0], 200 + asc[1] - 20, bb[2], 200 + _ft.getbbox('gyp')[3] + 20))
        _cache[word] = im.resize((max(1, int(im.width * CONDENSE)), im.height), Image.LANCZOS)
    return _cache[word]

def frame(t):
    img = np.full((H, W, 3), 255, np.float32)
    gi = max((i for i, g in enumerate(G) if g[0][1] <= t), default=None)
    if gi is None or t >= END: return img.astype(np.uint8)
    full = G[gi]
    # long held words break into stacked chunks (raaaaa / aaaang) so letters stay huge like the reference
    def chunks(txt, final=None, k=5):
        f = final or txt; n = max(1, math.ceil(len(f) / k)); L = math.ceil(len(f) / n)
        cs = [txt[i:i + L] for i in range(0, len(txt), L)]
        if len(cs) > 1 and len(cs[-1]) < 3:                     # no orphan "ng" — pull letters down
            k2 = 3 - len(cs[-1]); cs[-1] = cs[-2][-k2:] + cs[-1]; cs[-2] = cs[-2][:-k2]
        return cs
    fin = [glyph(c) for w in full for c in (chunks(w[0]) if len(w) > 2 else [w[0]])]
    gap = -0.12
    s = min(MAXW / max(g.width for g in fin), MAXH / (fin[0].height * (len(fin) + gap * (len(fin) - 1))), 1.25)
    h = int(fin[0].height * s); step = h + int(gap * h)
    lines = []
    for w in full:
        if w[1] > t: break
        for c in (chunks(current(w, t), w[0]) if len(w) > 2 else [w[0]]): lines.append((c, t - w[1]))
    y = int(CY - (h + step * (len(lines) - 1)) / 2)
    A = np.zeros((H, W), np.float32)
    for c, age in lines:
        g = glyph(c)
        pop = 1 + 0.08 * math.exp(-age * 14) if age < 0.4 else 1.0
        ww, hh = max(2, int(g.width * s * pop)), max(2, int(h * pop))
        m = np.asarray(g.resize((ww, hh), Image.LANCZOS), np.float32) / 255
        x0 = (W - ww) // 2; y0 = y + (h - hh) // 2
        xa, xb = max(0, x0), min(W, x0 + ww); ya, yb = max(0, y0), min(H, y0 + hh)
        A[ya:yb, xa:xb] = np.maximum(A[ya:yb, xa:xb], m[ya - y0:yb - y0, xa - x0:xb - x0])
        y += step
    img = img * (1 - A[..., None]) + RED * A[..., None]
    return np.clip(img, 0, 255).astype(np.uint8)

if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        for t in map(float, sys.argv[1:]): Image.fromarray(frame(t)).save(f'/home/claude/raft/sufi/rr_{t}.png')
        sys.exit()
    out = '/home/claude/raft/sufi/Sansoon_Ki_Mala_Red_Lyrics.mp4'
    pr = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                           '-f', 'lavfi', '-i', 'anullsrc=r=44100:cl=stereo', '-shortest', '-c:v', 'libx264', '-crf', '18', '-maxrate', '3M',
                           '-bufsize', '6M', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-movflags', '+faststart', out], stdin=subprocess.PIPE)
    for i in range(int(DUR * FPS)):
        pr.stdin.write(frame(i / FPS).tobytes())
    pr.stdin.close(); pr.wait(); print('done', out)
