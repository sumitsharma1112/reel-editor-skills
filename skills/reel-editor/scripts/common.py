"""Shared helpers for the reel-editor scripts (ffmpeg in/out, fitting, beats, audio loop)."""
import subprocess, numpy as np, cv2

W, H, FPS = 1080, 1920, 30


def probe_size(path):
    out = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=width,height',
                          '-of', 'csv=p=0', path], capture_output=True, text=True).stdout.strip().split(',')
    return int(out[0]), int(out[1])


def fit(img, w=W, h=H):
    """Cover-fit an image to w x h (scale up/down, centre crop)."""
    ih, iw = img.shape[:2]
    s = max(w / iw, h / ih)
    img = cv2.resize(img, (round(iw * s), round(ih * s)), interpolation=cv2.INTER_LANCZOS4)
    y, x = (img.shape[0] - h) // 2, (img.shape[1] - w) // 2
    return img[y:y + h, x:x + w]


def load_frames(path, fps=FPS, max_side=1280):
    """Decode a video (or still image) into a BGR uint8 array [n,h,w,3] at the given fps."""
    if path.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
        return cv2.imread(path)[None]
    w, h = probe_size(path)
    s = min(1.0, max_side / max(w, h))
    w, h = int(w * s) // 2 * 2, int(h * s) // 2 * 2
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', path, '-vf', f'fps={fps},scale={w}:{h}', '-f', 'rawvideo',
                          '-pix_fmt', 'bgr24', '-'], capture_output=True).stdout
    n = len(raw) // (w * h * 3)
    return np.frombuffer(raw[:n * w * h * 3], np.uint8).reshape(n, h, w, 3)


def writer(out, audio=None, crf=18, maxrate='12M', w=W, h=H, fps=FPS):
    """Return an ffmpeg Popen that takes raw BGR frames on stdin. maxrate keeps a 15-20s reel under ~30MB."""
    cmd = ['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{w}x{h}', '-r', str(fps), '-i', '-']
    if audio:
        cmd += ['-i', audio, '-map', '0:v', '-map', '1:a', '-c:a', 'aac', '-b:a', '192k', '-shortest']
    cmd += ['-c:v', 'libx264', '-crf', str(crf), '-maxrate', maxrate, '-bufsize', '24M', '-preset', 'slow',
            '-pix_fmt', 'yuv420p', '-movflags', '+faststart', out]
    return subprocess.Popen(cmd, stdin=subprocess.PIPE)


def extract_audio(src, dst, sr=44100):
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', src, '-vn', '-ac', '2', '-ar', str(sr), dst], check=True)
    return dst


def beats(path):
    import librosa
    y, sr = librosa.load(path, sr=22050, mono=True)
    tempo, b = librosa.beat.beat_track(y=y, sr=sr)
    onset = librosa.onset.onset_strength(y=y, sr=sr)
    return float(np.atleast_1d(tempo)[0]), librosa.frames_to_time(b, sr=sr), onset, librosa.times_like(onset, sr=sr)


def loop_audio(wav_in, wav_out, min_dur, fade_out=1.2):
    """Extend a song to >= min_dur seconds by jumping from a late beat back to the first beat (same phase,
    30ms crossfade), so the rhythm never breaks. Returns list of (out_start_s, src_start_s) segments."""
    import soundfile as sf
    y, sr = sf.read(wav_in, always_2d=True)
    dur = len(y) / sr
    _, bt, _, _ = beats(wav_in)
    J = bt[-1] if bt[-1] < dur - 0.3 else bt[-2]
    S = bt[0]
    xf = int(0.03 * sr)
    out, segs, t = y[:int(J * sr)].copy(), [(0.0, 0.0)], J
    while len(out) / sr < min_dur:
        nxt = y[int(S * sr) - xf:].copy()
        r = np.linspace(0, 1, xf)[:, None]
        out[-xf:] = out[-xf:] * (1 - r) + nxt[:xf] * r
        segs.append((t, S))
        body = nxt[xf:int((J - S) * sr) + xf] if len(out) / sr + (J - S) < min_dur else nxt[xf:]
        out = np.concatenate([out, body])
        t += (J - S)
    fo = int(fade_out * sr)
    out[-fo:] *= np.linspace(1, 0, fo)[:, None]
    sf.write(wav_out, out, sr)
    return segs, len(out) / sr


def src_time(t, segs):
    """Map an output time back to the source-song time using loop_audio's segments."""
    start, src = segs[0]
    for s in segs:
        if t >= s[0]:
            start, src = s
    return src + (t - start)


def to_bw(f, contrast=1.15, lift=-8):
    g = cv2.convertScaleAbs(cv2.cvtColor(f, cv2.COLOR_BGR2GRAY), alpha=contrast, beta=lift)
    return cv2.cvtColor(g, cv2.COLOR_GRAY2BGR)


def zoom(f, z, cx=0.5, cy=0.5, dx=0, dy=0):
    h, w = f.shape[:2]
    M = cv2.getRotationMatrix2D((cx * w, cy * h), 0, z)
    M[0, 2] += dx
    M[1, 2] += dy
    return cv2.warpAffine(f, M, (w, h), borderMode=cv2.BORDER_REFLECT)
