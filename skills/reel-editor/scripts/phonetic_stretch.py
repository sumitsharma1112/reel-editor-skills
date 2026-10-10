#!/usr/bin/env python3
"""Phonetic stretching lyric captions.

While a singer holds a note, the held vowel of the active word is repeated
letter by letter ("naam" -> "naaaaaaam"), and every new vowel letter sits
higher or lower according to the singer's pitch at the moment it appeared,
so the stretched word draws the melody (meend, vibrato, taan) on screen.

Usage:
  python3 phonetic_stretch.py IN.mp4 lyrics.json OUT.mp4 [--y 1050] [--font F.ttf]
         [--accent "#F2C46D"] [--maxw 640] [--size 66]

lyrics.json: {"lines":[{"words":[[text,t0,t1(,stretch_index)],...]},...]}
stretch_index = index of the vowel letter in `text` to repeat while held.
Example: {"lines":[{"words":[["Mera",3.0,3.4],["naam",3.4,5.2,2]]}]}
  -> "naam" grows to "naaaaaaaaam" between 3.4 s and 5.2 s, letters riding the pitch.
Pitch: vocals are pulled out of the mix with a REPET-style nn_filter mask,
then tracked with librosa.pyin (fmin 140, fmax 900 — suits male/female
classical singers; lower fmin for very deep voices).
"""
import argparse, json, subprocess, sys, os
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ap = argparse.ArgumentParser()
ap.add_argument('inp'); ap.add_argument('lyrics'); ap.add_argument('out')
ap.add_argument('--y', type=int, default=1050, help='centre Y of the current line')
ap.add_argument('--font', default=os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'fonts', 'cormorant-garamond-700i.ttf'))
ap.add_argument('--accent', default='#F2C46D')
ap.add_argument('--maxw', type=int, default=640)
ap.add_argument('--size', type=int, default=66)
ap.add_argument('--letter-rate', type=float, default=0.10, help='seconds per added vowel letter')
ap.add_argument('--max-extra', type=int, default=12)
ap.add_argument('--no-preview', action='store_true', help='hide the dim next-line preview')
A = ap.parse_args()

def probe(p):
    o = subprocess.check_output(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries',
                                 'stream=width,height,r_frame_rate', '-of', 'csv=p=0', p]).decode().strip().split(',')
    n, d = o[2].split('/')
    return int(o[0]), int(o[1]), float(n) / float(d)

W, H, FPS = probe(A.inp)
ACC = tuple(int(A.accent[i:i + 2], 16) for i in (1, 3, 5))

# ---------- pitch track of the vocal ----------
import librosa
wav = A.out + '.tmp.wav'
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', A.inp, '-ac', '1', '-ar', '22050', wav], check=True)
y, sr = librosa.load(wav, sr=22050); os.remove(wav)
HOP = 256
S, ph = librosa.magphase(librosa.stft(y, n_fft=2048, hop_length=HOP))
Sf = np.minimum(S, librosa.decompose.nn_filter(S, aggregate=np.median, metric='cosine',
                width=int(librosa.time_to_frames(1.5, sr=sr, hop_length=HOP))))
yv = librosa.istft(librosa.util.softmask(S - Sf, 10 * Sf, power=2) * S * ph, hop_length=HOP, length=len(y))
f0, vflag, _ = librosa.pyin(yv, fmin=140, fmax=900, sr=sr, frame_length=2048, hop_length=HOP)
ft = librosa.times_like(f0, sr=sr, hop_length=HOP)

def pitch_at(t, lo, hi):
    """median f0 in a 80 ms window around t; falls back to nearest voiced frame inside [lo,hi]."""
    m = (ft > t - 0.04) & (ft < t + 0.04) & ~np.isnan(f0)
    if m.any(): return float(np.median(f0[m]))
    m = (ft >= lo) & (ft <= hi) & ~np.isnan(f0)
    if not m.any(): return np.nan
    idx = np.where(m)[0]; return float(f0[idx[np.argmin(np.abs(ft[idx] - t))]])

# ---------- lyric model ----------
L = json.load(open(A.lyrics))['lines']
fonts = {}
def F(sz):
    sz = max(8, int(round(sz)))
    if sz not in fonts: fonts[sz] = ImageFont.truetype(A.font, sz)
    return fonts[sz]

for li, line in enumerate(L):
    words = []
    for w in line['words']:
        text, t0, t1 = w[0], float(w[1]), float(w[2])
        si = w[3] if len(w) > 3 else None
        d = {'text': text, 't0': t0, 't1': t1, 'si': si, 'n': 0, 'off': []}
        if si is not None:
            dur = t1 - t0
            n = int(np.clip(round(dur / A.letter_rate), 2, A.max_extra))
            d['n'] = n
            base = np.nanmedian([pitch_at(t0 + dur * k / 20, t0, t1) for k in range(21)])
            ts = [t0 + dur * k / (n + 1) for k in range(n + 1)]   # k=0 is the original vowel
            cents = []
            for tk in ts:
                p = pitch_at(tk, t0, t1)
                cents.append(0.0 if (np.isnan(p) or np.isnan(base)) else 1200 * np.log2(p / base))
            c = np.array(cents)
            if len(c) >= 3: c = np.convolve(np.pad(c, 1, mode='edge'), [.25, .5, .25], 'valid')
            d['cents'] = c; d['ts'] = ts
        words.append(d)
    line['W'] = words
    line['start'] = words[0]['t0'] - 0.25
for li, line in enumerate(L):
    line['end'] = L[li + 1]['start'] if li + 1 < len(L) else line['W'][-1]['t1'] + 1.5

def full_text(w, extra):
    if w['si'] is None: return w['text']
    s = w['si']; return w['text'][:s + 1] + w['text'][s] * extra + w['text'][s + 1:]

# fixed layout per line, sized for the fully stretched line.
# If the line is still too wide at MIN_SIZE, trim the extra-letter budget of its stretched words.
MIN_SIZE = 46
def layout(line, size):
    f = F(size); sp = f.getlength(' ')
    widths = [f.getlength(full_text(w, w['n'])) for w in line['W']]
    return widths, sum(widths) + sp * (len(widths) - 1), sp
for line in L:
    size = A.size
    widths, tot, sp = layout(line, size)
    while tot > A.maxw and size > MIN_SIZE:
        size -= 2; widths, tot, sp = layout(line, size)
    while tot > A.maxw and any(w['n'] > 2 for w in line['W']):
        w = max(line['W'], key=lambda w: w['n']); w['n'] -= 1
        dur = w['t1'] - w['t0']; n = w['n']
        base = np.nanmedian([pitch_at(w['t0'] + dur * k / 20, w['t0'], w['t1']) for k in range(21)])
        w['ts'] = [w['t0'] + dur * k / (n + 1) for k in range(n + 1)]
        c = np.array([0.0 if np.isnan(pitch_at(tk, w['t0'], w['t1'])) else 1200 * np.log2(pitch_at(tk, w['t0'], w['t1']) / base) for tk in w['ts']])
        if len(c) >= 3: c = np.convolve(np.pad(c, 1, mode='edge'), [.25, .5, .25], 'valid')
        w['cents'] = c
        widths, tot, sp = layout(line, size)
    line['size'] = size
    x = (W - tot) / 2; xs = []
    for wd in widths: xs.append(x); x += wd + sp
    line['xs'] = xs

def ease_out(u): u = min(max(u, 0), 1); return 1 - (1 - u) ** 3

STRIP_Y0 = A.y - 140; STRIP_H = 300

def draw_line(layer, glow, line, t, cy, scale=1.0, alpha=1.0, preview=False):
    d = ImageDraw.Draw(layer); g = ImageDraw.Draw(glow)
    size = line['size'] * scale; f = F(size)
    asc = f.getmetrics()[0]
    if preview:
        txt = ' '.join(w['text'] for w in line['W'])
        d.text(((W - f.getlength(txt)) / 2, cy - asc * 0.6), txt, font=f, fill=(255, 255, 255, int(70 * alpha)))
        return
    for w, x0 in zip(line['W'], line['xs']):
        active = w['t0'] <= t < w['t1']
        done = t >= w['t1']
        if done: col = (255, 255, 255, int(255 * alpha))
        elif active: col = ACC + (int(255 * alpha),)
        else: col = (255, 255, 255, int(95 * alpha))
        if w['si'] is None:
            d.text((x0, cy - asc * 0.6), w['text'], font=f, fill=col)
            if active: g.text((x0, cy - asc * 0.6), w['text'], font=f, fill=ACC + (int(200 * alpha),))
            continue
        # stretched word, letter by letter
        dur = w['t1'] - w['t0']
        if t < w['t0']: extra = 0
        elif done: extra = w['n']
        else: extra = min(w['n'], int((t - w['t0']) / dur * (w['n'] + 1)))
        s = w['si']; txt = w['text']
        letters = [(ch, 0.0, None) for ch in txt[:s]]
        amp = size * 0.36 / 300.0   # px per cent: 300 cents -> 0.36 x font size
        for k in range(extra + 1):
            off = -float(np.clip(w['cents'][k] * amp, -0.42 * size, 0.42 * size))
            letters.append((txt[s], off, w['ts'][k]))
        tail_off = letters[-1][1] * 0.5
        letters += [(ch, tail_off, None) for ch in txt[s + 1:]]
        x = x0
        for ch, off, born in letters:
            sc = 1.0; a = 1.0
            if active and born is not None and t - born < 0.14 and born > w['t0']:
                u = (t - born) / 0.14; sc = 1.45 - 0.45 * ease_out(u); a = min(1, u * 2.5)
            fl = F(size * sc)
            adv = f.getlength(ch)
            cx = x + adv / 2; wl = fl.getlength(ch)
            ascl = fl.getmetrics()[0]
            pos = (cx - wl / 2, cy + off - ascl * 0.6)
            c = col[:3] + (int(col[3] * a),)
            d.text(pos, ch, font=fl, fill=c)
            if active: g.text(pos, ch, font=fl, fill=ACC + (int(220 * alpha * a),))
            x += adv

def render_strip(t):
    layer = Image.new('RGBA', (W, STRIP_H), (0, 0, 0, 0))
    glow = Image.new('RGBA', (W, STRIP_H), (0, 0, 0, 0))
    cy = A.y - STRIP_Y0
    for li, line in enumerate(L):
        if not (line['start'] <= t < line['end']): continue
        u_in = (t - line['start']) / 0.22
        u_out = (line['end'] - t) / 0.18
        al = min(1, ease_out(u_in), max(0, u_out))
        rise = (1 - ease_out(u_in)) * 14
        draw_line(layer, glow, line, t, cy + rise, alpha=al)
        if li + 1 < len(L) and not A.no_preview:
            draw_line(layer, glow, L[li + 1], t, cy + line['size'] * 1.25, scale=0.55, alpha=al, preview=True)
    glow = glow.filter(ImageFilter.GaussianBlur(9))
    shadow = Image.new('RGBA', (W, STRIP_H), (0, 0, 0, 0))
    a = layer.split()[3].filter(ImageFilter.GaussianBlur(3)).point(lambda v: v * 0.8)
    shadow.putalpha(a)
    out = Image.alpha_composite(shadow, glow)
    return Image.alpha_composite(out, layer)

# ---------- video pipe ----------
dec = subprocess.Popen(['ffmpeg', '-v', 'error', '-i', A.inp, '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], stdout=subprocess.PIPE)
enc = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS),
                        '-i', '-', '-i', A.inp, '-map', '0:v', '-map', '1:a?', '-c:v', 'libx264', '-preset', 'medium',
                        '-crf', '17', '-pix_fmt', 'yuv420p', '-c:a', 'copy', '-movflags', '+faststart', A.out], stdin=subprocess.PIPE)
fs = W * H * 3; i = 0
while True:
    buf = dec.stdout.read(fs)
    if len(buf) < fs: break
    t = i / FPS
    fr = Image.frombuffer('RGB', (W, H), buf).convert('RGBA')
    fr.alpha_composite(render_strip(t), (0, STRIP_Y0))
    enc.stdin.write(fr.convert('RGB').tobytes()); i += 1
enc.stdin.close(); enc.wait(); dec.wait()
print(f'done: {i} frames -> {A.out}')
