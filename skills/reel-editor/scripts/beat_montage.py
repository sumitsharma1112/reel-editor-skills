"""Beat-synced montage: cut a folder of clips onto the beats of a song.
Cut points come from the music (librosa) or from a Premiere/FCP XML cut list (--xml).
On strong beats: zoom punch, flash, small shake. Calm sections get 2-beat shots, loud ones 1-beat.

Examples
  python beat_montage.py --clips clips/ --song song.mp3 --out reel.mp4
  python beat_montage.py --clips clips/ --song song.mp3 --xml Sequence_01.xml --out reel.mp4
  python beat_montage.py --clips clips/ --song song.mp3 --start 9.1 --dur 30 --out reel.mp4
"""
import argparse, glob, os, sys, tempfile, subprocess, math, numpy as np, cv2
import xml.etree.ElementTree as ET
sys.path.insert(0, os.path.dirname(__file__))
from common import W, H, FPS, writer, beats, zoom


def xml_cuts(path):
    """[(start_frame, end_frame)] of clips on the first video track of an xmeml (Premiere/FCP7) export."""
    r = ET.parse(path).getroot()
    tr = r.find('sequence/media/video').findall('track')[0]
    cuts = [(int(c.findtext('start')), int(c.findtext('end'))) for c in tr.findall('clipitem')]
    if len(cuts) <= 1:
        sys.exit('XML has no cuts (only one clip). Cut the reference in Premiere first, or drop --xml to use beat detection.')
    return cuts


def beat_cuts(song, dur):
    tempo, bt, on, ot = beats(song)
    bt = bt[bt < dur]
    strength = np.array([on[max(0, np.searchsorted(ot, t) - 2):np.searchsorted(ot, t) + 3].max() for t in bt])
    loud = strength > np.percentile(strength, 60)
    pts, i = [0.0], 0
    while i < len(bt):
        step = 1 if loud[i] else 2
        pts.append(bt[i]); i += step
    pts.append(dur)
    fr = sorted(set(int(round(t * FPS)) for t in pts))
    return [(a, b) for a, b in zip(fr, fr[1:]) if b - a >= 3]


def read(path, ss, n, speed=1.0):
    vf = f'setpts=PTS/{speed},fps={FPS},scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H}'
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-ss', f'{ss:.3f}', '-i', path, '-t', f'{n / FPS * speed + 0.3:.3f}', '-vf', vf,
                          '-frames:v', str(n), '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-'], capture_output=True).stdout
    m = len(raw) // (W * H * 3)
    return np.frombuffer(raw[:m * W * H * 3], np.uint8).reshape(m, H, W, 3)


def length(path):
    return float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', path],
                                capture_output=True, text=True).stdout)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--clips', required=True, help='folder of clips (played in name order, cycled)')
    p.add_argument('--song', required=True)
    p.add_argument('--start', type=float, default=0, help='song start time (s)')
    p.add_argument('--dur', type=float, default=0, help='reel length (s), default = whole song')
    p.add_argument('--xml', help='Premiere/FCP xmeml cut list to copy cut timing from')
    p.add_argument('--slowmo-last', action='store_true', help='play the final shot at 0.4x')
    p.add_argument('--out', required=True)
    a = p.parse_args()
    tmp = tempfile.mkdtemp()
    song = os.path.join(tmp, 'song.wav')
    cmd = ['ffmpeg', '-v', 'error', '-y', '-ss', str(a.start), '-i', a.song]
    if a.dur:
        cmd += ['-t', str(a.dur)]
    subprocess.run(cmd + ['-vn', '-ac', '2', '-ar', '44100', song], check=True)
    dur = length(song)
    clips = sorted(sum([glob.glob(os.path.join(a.clips, e)) for e in ('*.mp4', '*.mov', '*.MOV', '*.MP4')], []))
    if not clips:
        sys.exit('no clips found')
    cuts = xml_cuts(a.xml) if a.xml else beat_cuts(song, dur)

    _, bt, on, ot = beats(song)
    st = np.array([on[max(0, np.searchsorted(ot, s / FPS) - 2):np.searchsorted(ot, s / FPS) + 3].max() for s, _ in cuts])
    big = st >= np.percentile(st, 80)
    rng = np.random.default_rng(7)
    w = writer(a.out, song)
    NF = cuts[-1][1]
    for k, (s, e) in enumerate(cuts):
        n = e - s
        path = clips[k % len(clips)]
        spd = 0.4 if (a.slowmo_last and k == len(cuts) - 1) else 1.0
        L = length(path)
        ss = rng.uniform(0, max(0.01, L - n / FPS * spd - 0.3))
        F = read(path, ss, n, spd)
        for j in range(n):
            f = F[min(j, len(F) - 1)] if len(F) else np.zeros((H, W, 3), np.uint8)
            z = 1 + 0.03 * j / max(n, 1) + (0.14 if big[k] else 0.06) * math.exp(-j / 2.5)
            dx = dy = 0
            if big[k] and j < 4:
                dx, dy = rng.integers(-18, 19, 2) * (1 - j / 4)
            f = zoom(f, z, dx=dx, dy=dy)
            if big[k] and j < 2:
                f = cv2.convertScaleAbs(f, alpha=1.25 - 0.1 * j, beta=10)
            g = s + j
            if g < 8:
                f = (f * (g / 8)).astype(np.uint8)
            if g > NF - 20:
                f = (f * ((NF - g) / 20)).astype(np.uint8)
            w.stdin.write(f.tobytes())
    w.stdin.close(); w.wait()
    print('done', a.out, len(cuts), 'cuts')


if __name__ == '__main__':
    main()
