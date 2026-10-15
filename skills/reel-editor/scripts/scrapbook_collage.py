"""Scrapbook / paper-collage lyric animation (Procreate/VN 'song animation' look).

Cream paper canvas with grain + torn-paper corner strips, cut-out stickers (auto background removal,
white die-cut border, soft drop shadow) that pop / slide / drop / spin in on each lyric, idle float +
sway, and a tiny serif caption at the bottom. Optional full-bleed 'photo' shots (e.g. eye close-up)
with a slow push-in.

Usage:
    python scrapbook_collage.py scenes.json out.mp4 [--audio song.mp3] [--preview 3.5]

scenes.json:
{
  "size": [1080, 1920], "fps": 30, "theme": "cream", "card_y": 560, "card_h": 800,
  "scenes": [
    {"t": 0, "dur": 3, "caption": "Zakhm pe marham",
     "stickers": [{"src": "heart.png", "x": 0.5, "y": 0.5, "w": 0.45, "rot": -6, "in": "pop", "at": 0.1},
                  {"src": "bandaid.png", "x": 0.5, "y": 0.48, "w": 0.55, "rot": 20, "in": "drop", "at": 1.2}]},
    {"t": 3, "dur": 2, "photo": "eyes.jpg", "caption": "Tere naina"}
  ],
  "handle": "@yourhandle"
}
x/y are fractions of the card (paper area), w is sticker width as a fraction of card width.
Entrances: pop | slide_l | slide_r | drop | spin | fade.  Stickers persist inside their scene.
"""
import json, sys, os, math, subprocess, argparse
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
FONT = os.path.join(HERE, '..', 'fonts', 'cormorant-600i.ttf')

def paper(w, h, seed=3, base_col=(196, 226, 240), strips=((120, 160, 130), (150, 175, 190))):
    rng = np.random.default_rng(seed)
    base = np.full((h, w, 3), base_col, np.float32)                     # BGR cream
    n = cv2.GaussianBlur(rng.normal(0, 1, (h, w)).astype(np.float32), (0, 0), 1.2) * 6
    n += cv2.GaussianBlur(rng.normal(0, 1, (h, w)).astype(np.float32), (0, 0), 18) * 10
    base += n[..., None]
    fib = cv2.GaussianBlur(rng.normal(0, 1, (h, w)).astype(np.float32), (0, 0), sigmaX=0.6, sigmaY=9) * 5
    base += fib[..., None]
    # torn strips: green top-right, kraft left
    def torn(mask_poly, col):
        m = Image.new('L', (w, h)); ImageDraw.Draw(m).polygon(mask_poly, fill=255)
        m = np.asarray(m.filter(ImageFilter.GaussianBlur(1.2)), np.float32)[..., None] / 255
        tex = np.array(col, np.float32) + n[..., None] * 1.6
        sh = cv2.GaussianBlur(m[..., 0], (0, 0), 6)[..., None]
        return m, tex, sh
    def jag(p0, p1, k, amp):
        pts = []
        for i in range(k + 1):
            u = i / k; x = p0[0] + (p1[0] - p0[0]) * u; y = p0[1] + (p1[1] - p0[1]) * u
            pts.append((x + rng.uniform(-amp, amp), y + rng.uniform(-amp, amp)))
        return pts
    out = base
    for poly, col in ((jag((w * 0.62, 0), (w, h * 0.42), 40, 7) + [(w, 0)], strips[0]),
                      ([(0, h * 0.05)] + jag((w * 0.07, h * 0.05), (w * 0.03, h), 50, 5) + [(0, h)], strips[1])):
        m, tex, sh = torn(poly, col)
        out = out * (1 - sh * 0.25) ; out = out * (1 - m) + tex * m
    return np.clip(out, 0, 255)

_cut = {}
def sticker(path, width):
    key = (path, width)
    if key in _cut: return _cut[key]
    im = Image.open(path).convert('RGBA')
    if im.getextrema()[3][0] == 255:                                          # opaque -> remove background
        try:
            from rembg import remove, new_session
            im = remove(im, session=new_session('u2net'))
        except Exception:
            pass
    a0 = np.asarray(im.getchannel('A'), np.uint8)                              # keep the main piece only
    n, lab, st, _ = cv2.connectedComponentsWithStats((a0 > 40).astype(np.uint8))
    if n > 2:
        big = 1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA]))
        keep = cv2.dilate((lab == big).astype(np.uint8), np.ones((15, 15), np.uint8))
        arr = np.asarray(im).copy(); arr[..., 3] = arr[..., 3] * keep; im = Image.fromarray(arr)
    bb = im.getbbox(); im = im.crop(bb)
    s = width / im.width; im = im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))), Image.LANCZOS)
    pad = int(width * 0.06) + 10
    a = np.pad(np.asarray(im.getchannel('A'), np.uint8), pad)
    rgb = np.pad(np.asarray(im.convert('RGB'), np.uint8), ((pad, pad), (pad, pad), (0, 0)))
    border = cv2.dilate((a > 40).astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (13, 13)))
    border = cv2.GaussianBlur(border.astype(np.float32), (0, 0), 0.8)
    al = a.astype(np.float32) / 255
    col = rgb[..., ::-1].astype(np.float32) * al[..., None] + 252 * (1 - al[..., None])
    alpha = np.maximum(border, al)
    _cut[key] = (col, alpha)
    return _cut[key]

def ease_back(u):
    u = min(1, max(0, u)); c = 1.7
    return 1 + (c + 1) * (u - 1) ** 3 + c * (u - 1) ** 2

def place(canvas, col, alpha, cx, cy, scale, rot, opacity):
    h, w = alpha.shape
    M = cv2.getRotationMatrix2D((w / 2, h / 2), rot, scale)
    M[0, 2] += cx - w / 2; M[1, 2] += cy - h / 2
    H_, W_ = canvas.shape[:2]
    a = cv2.warpAffine(alpha, M, (W_, H_)) * opacity
    if a.max() <= 0: return canvas
    c = cv2.warpAffine(col, M, (W_, H_))
    sh = cv2.GaussianBlur(cv2.warpAffine(alpha, M + np.float32([[0, 0, 8], [0, 0, 14]]), (W_, H_)), (0, 0), 9) * 0.35 * opacity
    canvas = canvas * (1 - sh[..., None])
    return canvas * (1 - a[..., None]) + c * a[..., None]

def caption(text, width, size, col=(70, 50, 40)):
    f = ImageFont.truetype(FONT, size); im = Image.new('RGBA', (width, size * 2)); d = ImageDraw.Draw(im)
    tw = d.textlength(text, font=f); d.text(((width - tw) / 2, size * 0.3), text, font=f, fill=tuple(col) + (255,))
    a = np.asarray(im, np.float32); return a[..., 2::-1], a[..., 3:] / 255

FD = os.path.join(HERE, '..', 'fonts')
LYR_FONTS = ['caveat-brush-400.ttf', 'kaushan-script-400.ttf']
_lg = {}
def lyr_glyph(word, font, size):
    k = (word, font, size)
    if k not in _lg:
        f = ImageFont.truetype(os.path.join(FD, font), size); bb = f.getbbox(word)
        im = Image.new('L', (bb[2] - bb[0] + 40, bb[3] - bb[1] + 40)); ImageDraw.Draw(im).text((20 - bb[0], 20 - bb[1]), word, font=f, fill=255)
        _lg[k] = np.asarray(im, np.float32) / 255
    return _lg[k]

def layout_lyrics(lyrics, W, top):
    """Hand-lettered word-by-word lyrics (Bade Achhe Lagte Hain style). Each item: {t0, t1, text, big: [words]}.
    Words share the line time by length; 'big' words use Permanent Marker in caps and the accent colour."""
    out = []
    for n, L in enumerate(lyrics):
        words = L['text'].split(); big = {b.lower() for b in L.get('big', [])}
        wt = [max(2, len(w)) for w in words]; wt[-1] *= 1.5; span = (L['t1'] - L['t0']) * 0.8
        t = L['t0']; gl = []
        for w, k in zip(words, wt):
            isbig = w.lower().strip('.,!?…') in big
            g = lyr_glyph(w.upper() if isbig else w, 'permanent-marker-400.ttf' if isbig else LYR_FONTS[n % 2], 118 if isbig else 84)
            gl.append((t, g, isbig)); t += span * k / sum(wt)
        rows, row, rw = [], [], 0
        for item in gl:                                                      # wrap to 960 px
            w_ = item[1].shape[1]
            if row and rw + w_ + 22 > W - 120: rows.append(row); row, rw = [], 0
            row.append(item); rw += w_ + 22
        rows.append(row)
        placed, y = [], top
        for r in rows:
            tw = sum(i[1].shape[1] for i in r) + 22 * (len(r) - 1); x = (W - tw) / 2; lh = max(i[1].shape[0] for i in r)
            for ti, g, isbig in r:
                placed.append((ti, g, isbig, int(x), int(y + (lh - g.shape[0]) / 2))); x += g.shape[1] + 22
            y += lh - 14
        out.append((L['t0'], L['t1'], placed))
    return out

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('spec'); ap.add_argument('out'); ap.add_argument('--audio'); ap.add_argument('--preview', type=float)
    A = ap.parse_args()
    S = json.load(open(A.spec)); base = os.path.dirname(os.path.abspath(A.spec))
    W, H = S.get('size', [1080, 1920]); FPS = S.get('fps', 30)
    CY, CH = S.get('card_y', 560), S.get('card_h', 800)
    THEMES = {'cream': dict(paper=(196, 226, 240), strips=((120, 160, 130), (150, 175, 190)), cap=(70, 50, 40), bg=(14, 14, 14), stars=False),
              'midnight': dict(paper=(92, 44, 30), strips=((60, 175, 230), (120, 110, 200)), cap=(225, 240, 250), bg=(48, 22, 16), stars=True)}
    TH = THEMES[S.get('theme', 'cream')]
    PAPER = paper(W, CH, base_col=TH['paper'], strips=TH['strips'])
    rs = np.random.default_rng(9); STARS = np.c_[rs.uniform(0, W, 140), rs.uniform(0, H, 140), rs.uniform(1, 3, 140), rs.uniform(0, 6.3, 140)]
    yy_ = np.linspace(0, 1, H)[:, None, None]
    BG = (np.array(TH['bg'], np.float32) * (1.25 - 0.5 * yy_) * np.ones((1, W, 1))).astype(np.float32)
    scenes = S['scenes']; DUR = max(s['t'] + s['dur'] for s in scenes)
    photos = {}
    def frame(i):
        t = i / FPS
        sc = next((s for s in scenes if s['t'] <= t < s['t'] + s['dur']), scenes[-1]); lt = t - sc['t']
        if 'photo' in sc:
            p = sc['photo']
            if p not in photos:
                im = cv2.imread(os.path.join(base, p)); s = max(W / im.shape[1], CH / im.shape[0]) * 1.08
                photos[p] = cv2.resize(im, None, fx=s, fy=s, interpolation=cv2.INTER_LANCZOS4).astype(np.float32)
            im = photos[p]; z = 1 + 0.06 * lt / sc['dur']
            M = np.float32([[z, 0, W / 2 - im.shape[1] / 2 * z], [0, z, CH / 2 - im.shape[0] / 2 * z]])
            card = cv2.warpAffine(im, M, (W, CH), borderMode=cv2.BORDER_REFLECT)
        else:
            card = PAPER.copy()
            for k, st in enumerate(sc.get('stickers', [])):
                u = (lt - st.get('at', 0)) / 0.45
                if u <= 0: continue
                col, al = sticker(os.path.join(base, st['src']), int(st.get('w', 0.4) * W))
                cx, cy = st['x'] * W, st['y'] * CH; sc_ = 1.0; rot = st.get('rot', 0); op = 1.0; e = ease_back(u)
                kind = st.get('in', 'pop')
                if kind == 'pop': sc_ = max(0.01, e)
                elif kind == 'slide_l': cx = -W * 0.4 + (cx + W * 0.4) * e
                elif kind == 'slide_r': cx = W * 1.4 + (cx - W * 1.4) * e
                elif kind == 'drop': cy = -CH * 0.6 + (cy + CH * 0.6) * e; rot += (1 - min(1, u)) * 25
                elif kind == 'spin': sc_ = max(0.01, e); rot += (1 - min(1, u)) * 180
                elif kind == 'fade': op = min(1, u)
                ft = lt + k * 0.7                                                   # idle float
                cy += 5 * math.sin(ft * 2.1); rot += 1.5 * math.sin(ft * 1.6)
                card = place(card, col, al, cx, cy, sc_, rot, op)
        if sc.get('caption') and not S.get('lyrics'):
            L, Aa = caption(sc['caption'], W, S.get('caption_size', 34), TH['cap'][::-1])
            y = CH - L.shape[0] - 16; a = Aa * min(1, lt / 0.25)
            card[y:y + L.shape[0]] = card[y:y + L.shape[0]] * (1 - a) + L * a
        if S.get('handle'):
            if 'h' not in photos:
                f = ImageFont.truetype(FONT, 24); im = Image.new('RGBA', (W, 50)); d = ImageDraw.Draw(im)
                tw = d.textlength(S['handle'], font=f); d.text((W - tw - 40, 8), S['handle'], font=f, fill=tuple(TH['cap'][::-1]) + (200,))
                a = np.asarray(im, np.float32); photos['h'] = (a[..., 2::-1], a[..., 3:] / 255)
            L, Aa = photos["h"]; card[CH - 62:CH - 12] = card[CH - 62:CH - 12] * (1 - Aa * 0.8) + L * Aa * 0.8
        out = BG.copy()
        if TH['stars']:
            for x, y, r, ph in STARS:
                a = 0.35 + 0.65 * (0.5 + 0.5 * math.sin(t * 2.2 + ph))
                cv2.circle(out, (int(x), int(y)), int(r), (200 * a + 40, 230 * a + 20, 255 * a), -1, cv2.LINE_AA)
        sh = SHADOW
        out = out * (1 - 0.5 * sh[..., None]); out[CY:CY + CH] = card
        if LYR:
            tx = np.zeros((H, W), np.float32); acc = np.zeros((H, W), np.float32)
            for t0, t1, placed in LYR:
                if not (t0 - 0.05 <= t < t1): continue
                ga = min(1, (t1 - t) / 0.3)
                for ti, g, isbig, x, y in placed:
                    if t < ti: continue
                    u = min(1, (t - ti) / 0.3); dy = int((1 - u) * 22)
                    h_, w_ = g.shape; L_ = acc if isbig else tx
                    if isbig and t < ti + 0.25: dy -= int(8 * math.sin((t - ti) * 40))
                    y0 = max(0, y + dy); y1 = min(H, y + dy + h_)
                    if y1 > y0: L_[y0:y1, x:x + w_] = np.maximum(L_[y0:y1, x:x + w_], g[y0 - y - dy:y1 - y - dy] * u * ga)
            for L_, col in ((tx, LCOL), (acc, ACOL)):
                if L_.max() <= 0: continue
                sm = cv2.resize(L_, (W // 4, H // 4), interpolation=cv2.INTER_AREA)
                sh_ = cv2.resize(cv2.GaussianBlur(sm, (0, 0), 1.3), (W, H)); glow = cv2.resize(cv2.GaussianBlur(sm, (0, 0), 3.5), (W, H))
                out = out * (1 - np.clip(sh_ * 1.2, 0, 0.7)[..., None])
                out = out * (1 - L_[..., None]) + col * L_[..., None] + col * glow[..., None] * 0.45
        return np.clip(out, 0, 255).astype(np.uint8)
    SHADOW = np.zeros((H, W), np.float32); SHADOW[CY + 10:CY + CH + 24, 12:W - 12] = 1; SHADOW = cv2.GaussianBlur(SHADOW, (0, 0), 18)
    LYR = layout_lyrics(S['lyrics'], W, S.get('lyrics_y', CY + CH + 40)) if S.get('lyrics') else None
    LCOL = np.array(S.get('lyrics_colour', [215, 238, 250]), np.float32); ACOL = np.array(S.get('accent_colour', [60, 190, 245]), np.float32)
    if A.preview is not None:
        cv2.imwrite(A.out, frame(int(A.preview * FPS))); return
    cmd = ['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-']
    cmd += (['-i', A.audio, '-map', '0:v', '-map', '1:a', '-shortest', '-c:a', 'aac', '-b:a', '192k'] if A.audio else [])
    cmd += ['-c:v', 'libx264', '-crf', '19', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', A.out]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for i in range(int(DUR * FPS)): p.stdin.write(frame(i).tobytes())
    p.stdin.close(); p.wait()

if __name__ == '__main__':
    main()
