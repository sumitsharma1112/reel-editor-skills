"""Mera Piya Ghar Aaya – Banaras Veo clips in a 4:3 band on black, one red calligraphy (roman) word at a time
(capturewithdev_ 'Mann Ki Lagan' look)."""
import os, subprocess, numpy as np
from PIL import Image, ImageDraw, ImageFont

U = './'   # folder with song.mp4 + clip1/2/3.mp4
SONG = U + 'song.mp4'
CLIPS = [U + 'clip1.mp4',   # ghats + Ganga
         U + 'clip2.mp4',   # galli
         U + 'clip3.mp4']   # rooftops + pigeons
W, H, FPS, DUR = 1080, 1920, 24, 63.5
BW, BH = 1080, 810; BY = (H - BH) // 2                       # 4:3 picture band
FONT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'fonts', 'berkshire-swash-400.ttf')
RED = np.array([212, 36, 28], np.float32)
OUT = './'

LINES = [
    (0.0, 4.0, 'Ho padh padh ilm kitaabaan waala naam rakhaayo qaazi'),
    (4.0, 7.6, 'Padh padh ilm kitaabaan waala ho'),
    (8.0, 12.0, 'Padh padh ilm kitaabaan waala naam rakhaayo qaazi'),
    (12.0, 17.0, 'Ho Makke jaa kar hajj padh aayo naam rakhaayo haaji'),
    (17.0, 21.0, 'Makke jaa kar hajj padh aayo naam rakhaayo haaji'),
    (21.0, 25.0, 'Fad shamsheer mujaahida waali naam rakhaayo ghaazi'),
    (25.0, 29.0, 'Fad shamsheer mujaahida waali naam rakhaayo ghaazi'),
    (29.0, 32.0, 'Ho Bulle Shaah ne kujh nahi keeta'),
    (32.0, 34.0, 'Bulle Shaah ne kujh nahi keeta'),
    (34.0, 38.0, 'Bulle Shaah ne kujh nahi keeta yaar nu keeta raazi'),
    (38.0, 40.0, 'Mera piya ghar aaya'),
    (40.0, 42.0, 'Mera piya ghar aaya'),
    (42.0, 44.0, 'Ho Bulle Shaah ne kujh nahi keeta'),
    (44.0, 46.0, 'Bulle Shaah ne kujh nahi keeta'),
    (46.0, 50.0, 'Bulle Shaah ne kujh nahi keeta yaar nu keeta raazi'),
    (50.0, 52.0, 'Mera piya ghar aaya'),
    (52.0, 54.0, 'Ho mera'),
    (54.0, 56.0, 'Ho mera'),
    (56.0, 59.0, 'Ho mera piya piya piya piya'),
    (59.0, 60.0, 'Piya piya piya piya'),
    (60.0, 63.2, 'Ho piya piya piya piya'),
]

# word timings: share of the line by length, last word held longer (singers stretch the line end)
WORDS = []
for st, en, txt in LINES:
    ws = txt.split(); wt = [max(2, len(w)) for w in ws]; wt[-1] *= 1.8
    t = st
    for w, k in zip(ws, wt):
        d = (en - st) * k / sum(wt); WORDS.append((w, t, t + d)); t += d

_ft = ImageFont.truetype(FONT, 210); _gc = {}
def glyph(w):
    if w not in _gc:
        im = Image.new('L', (int(_ft.getlength(w)) + 300, 800))
        ImageDraw.Draw(im).text((150, 200), w, font=_ft, fill=255)
        im = im.crop(im.getbbox()); im = im.resize((int(im.width * 0.8), im.height), Image.LANCZOS)
        if im.width > 500: im = im.resize((500, int(im.height * 500 / im.width)), Image.LANCZOS)
        _gc[w] = np.asarray(im, np.float32) / 255
    return _gc[w]

def background():
    """3 Veo clips slowed with frame blending to fill the song, 4:3 centre crop (drops the Veo sparkle), soft film grade"""
    seg = DUR / 3; parts = []
    for i, c in enumerate(CLIPS):
        sp = seg / 10.0 + 0.04
        p = OUT + f'bg{i}.mp4'; parts.append(p)
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', c, '-vf',
            f'crop=840:630:220:45,scale={BW}:{BH},setpts={sp:.4f}*PTS,minterpolate=fps={FPS}:mi_mode=blend,'
            'eq=saturation=0.82:contrast=0.95:gamma=1.02,colorbalance=rs=0.04:bs=-0.04:rh=0.03:bh=-0.03,noise=alls=4:allf=t',
            '-an', '-c:v', 'libx264', '-crf', '16', '-pix_fmt', 'yuv420p', p], check=True)
    xf = 0.8; o = seg - xf / 2
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', parts[0], '-i', parts[1], '-i', parts[2], '-filter_complex',
        f'[0][1]xfade=transition=fade:duration={xf}:offset={o:.2f}[a];[a][2]xfade=transition=fade:duration={xf}:offset={2*seg - xf:.2f},trim=0:{DUR},setpts=PTS-STARTPTS',
        '-c:v', 'libx264', '-crf', '16', '-pix_fmt', 'yuv420p', OUT + 'bg.mp4'], check=True)

def render():
    rd = subprocess.Popen(['ffmpeg', '-v', 'error', '-i', OUT + 'bg.mp4', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], stdout=subprocess.PIPE)
    wr = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
        '-ss', '0', '-i', SONG, '-map', '0:v', '-map', '1:a', '-af', 'loudnorm=I=-14:TP=-1.5', '-shortest',
        '-c:v', 'libx264', '-crf', '19', '-maxrate', '3.4M', '-bufsize', '7M', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k',
        '-movflags', '+faststart', OUT + 'Mera_Piya_Ghar_Aaya_Banaras.mp4'], stdin=subprocess.PIPE)
    n = int(DUR * FPS); fb = BW * BH * 3
    for i in range(n):
        raw = rd.stdout.read(fb)
        if len(raw) < fb: break
        t = i / FPS
        band = np.frombuffer(raw, np.uint8).reshape(BH, BW, 3).astype(np.float32)
        w = next((w for w in WORDS if w[1] <= t < w[2]), None)
        if w:
            m = glyph(w[0]) * min(1, (t - w[1]) / 0.1)
            h_, w_ = m.shape; y0 = (BH - h_) // 2; x0 = (BW - w_) // 2
            reg = band[y0:y0 + h_, x0:x0 + w_]
            band[y0:y0 + h_, x0:x0 + w_] = reg * (1 - m[..., None]) + RED * m[..., None]
        fr = np.zeros((H, W, 3), np.uint8); fr[BY:BY + BH] = np.clip(band, 0, 255).astype(np.uint8)
        wr.stdin.write(fr.tobytes())
    wr.stdin.close(); wr.wait(); print('done')

if __name__ == '__main__':
    import sys
    if 'bg' in sys.argv: background()
    render()
