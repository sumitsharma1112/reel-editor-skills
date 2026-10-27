"""qawwali_phrase_lyrics.py — Sufi / qawwali lyric reel that went 267 -> 1.15 lakh views (NFAK "Yeh Jo Halka Halka Saroor Hai").
Full 9:16 AI painting, red Playfair Display 700 phrases of 2-3 words (hand-split natural "X mast" pairs, timed by length inside each
transcript line so sync never drifts), soft dark shadow, bottom of text at y=1470 (just above Instagram's bottom UI).
Companion steps (see SKILL.md): shot-shuffle hook (swap slow opening shots with equal-length dynamic ones -> beat sync kept) and a tiny
corner keyword block (NFAK + artist/song keywords) so Instagram's AI classifies the reel for the right audience.
usage: edit SRC/OUT/LINES/CH, then python3 qawwali_phrase_lyrics.py [preview_t ...]"""
import subprocess, numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont

SRC, OUT = '/home/claude/raft/mast/shuf.mov', '/home/claude/raft/mast/hm_words.mp4'
W, H, FPS = 1080, 1920, 30
BW, BH = 1080, 810; BY = (H - BH) // 2
CY = 230                                     # crop the source from here: keeps faces + embrace in the band
FONT = '/home/claude/reel-editor-skills/skills/reel-editor/fonts/playfair-display-700.ttf'
RED = np.array([212, 36, 28], np.float32)

LINES = [
    (0.0, 2.9, 'Hum mast sara jahan mast jahan ka le-daram mast'),
    (3.0, 4.9, 'Ye din mast raat mast sahar mast sham mast'),
    (5.0, 6.9, 'Ye din mast raat mast sahar mast sham mast'),
    (7.0, 8.9, 'Ye din mast raat mast sahar mast sham mast'),
    (9.0, 10.9, 'Ye din mast raat mast sahar mast sham mast'),
    (11.0, 12.9, 'Hum mast sheesha mast sab mast jam mast'),
    (13.0, 14.9, 'Hum mast sheesha mast sab mast jam mast'),
    (15.0, 17.9, 'Hum mast sheesha mast sab mast jam mast'),
    (18.0, 19.9, 'Hum mast sheesha mast sab mast jam mast'),
    (20.0, 23.0, 'Hai teri chashm-e-mast se har khaas-o-aam mast'),
]
# hand-split ~3-word phrases (natural "X mast" pairs), time shared by length
CH = {
 'Hum mast sara jahan mast jahan ka le-daram mast': ['Hum mast', 'sara jahan mast', 'jahan ka le-daram mast'],
 'Ye din mast raat mast sahar mast sham mast': ['Ye din mast', 'raat mast', 'sahar mast sham mast'],
 'Hum mast sheesha mast sab mast jam mast': ['Hum mast', 'sheesha mast', 'sab mast jam mast'],
 'Hai teri chashm-e-mast se har khaas-o-aam mast': ['Hai teri chashm-e-mast', 'se har khaas-o-aam mast'],
}
WORDS = []
for st, en, txt in LINES:
    ch = CH[txt]; wt = [len(c) + 4 for c in ch]; t = st
    for c, k in zip(ch, wt):
        d = (en - st) * k / sum(wt); WORDS.append((c, t, t + d)); t += d

_ft = ImageFont.truetype(FONT, 120); _gc = {}
def glyph(w):
    if w not in _gc:
        im = Image.new('L', (int(_ft.getlength(w)) + 300, 800))
        ImageDraw.Draw(im).text((150, 200), w, font=_ft, fill=255)
        im = im.crop(im.getbbox())
        if im.width > 960: im = im.resize((960, int(im.height * 960 / im.width)), Image.LANCZOS)
        _gc[w] = np.asarray(im, np.float32) / 255
    return _gc[w]


def grade(band, i):
    b = band.astype(np.float32)
    b = (b - 128) * 0.95 + 128 + 2                                       # soft contrast
    g = b.mean(2, keepdims=True); b = g + (b - g) * 0.85                  # gentle desaturation (film)
    b[..., 0] += 4; b[..., 2] -= 4                                        # warm
    b += np.random.default_rng(i).normal(0, 4, (H, W, 1)).astype(np.float32)   # grain
    return b


def frame(img, t, i):
    band = grade(img, i)                                      # full 9:16 frame, no black band
    w = next((w for w in WORDS if w[1] <= t < w[2]), None)
    if w:
        m = glyph(w[0]) * min(1, (t - w[1]) / 0.1)
        h_, w_ = m.shape; y0 = 1470 - h_; x0 = (W - w_) // 2       # word bottom sits just above Insta's bottom UI zone (~y 1500+)
        reg = band[y0:y0 + h_, x0:x0 + w_]
        sh = cv2.GaussianBlur(np.pad(m, 40), (0, 0), 14)[40:-40, 40:-40] * 0.55
        reg = reg * (1 - sh[..., None])
        band[y0:y0 + h_, x0:x0 + w_] = reg * (1 - m[..., None]) + RED * m[..., None]
    return np.clip(band, 0, 255).astype(np.uint8)


if __name__ == '__main__':
    import sys
    cap = cv2.VideoCapture(SRC)
    if len(sys.argv) > 1:
        for s in sys.argv[1:]:
            t = float(s); cap.set(cv2.CAP_PROP_POS_FRAMES, int(t * FPS)); ok, f = cap.read()
            Image.fromarray(frame(cv2.cvtColor(f, cv2.COLOR_BGR2RGB), t, 0)).resize((360, 640)).save(f'/home/claude/raft/mast/p3_{s}.jpg')
        sys.exit()
    wr = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                           '-i', SRC, '-map', '0:v', '-map', '1:a', '-af', 'apad,loudnorm=I=-14:TP=-1.5', '-shortest',
                           '-c:v', 'libx264', '-crf', '21', '-maxrate', '6M', '-bufsize', '12M', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart', OUT],
                          stdin=subprocess.PIPE)
    i = 0
    while True:
        ok, f = cap.read()
        if not ok: break
        wr.stdin.write(frame(cv2.cvtColor(f, cv2.COLOR_BGR2RGB), i / FPS, i).tobytes()); i += 1
    wr.stdin.close(); wr.wait(); print('done', i)
