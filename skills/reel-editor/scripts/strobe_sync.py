"""Strobe beat-sync: rapidly alternate two shots (A/B) every few frames, like the viral
"aarti x deity" reels. The A/B cut pattern and the song can be copied frame-exactly from a
reference reel, and the song can be extended on-beat to any length.

Examples
  # copy pattern + song from a reference reel, deity image as A, aarti video as B in black & white
  python strobe_sync.py --ref ref.mp4 --a durga.png --b aarti.mp4 --bw b --min-dur 15 --out reel.mp4
  # no reference: own song, fixed 3-4 frame pattern
  python strobe_sync.py --audio song.mp3 --pattern 3,4 --a a.mp4 --b b.mp4 --out reel.mp4
"""
import argparse, os, sys, tempfile, numpy as np, cv2
sys.path.insert(0, os.path.dirname(__file__))
from common import W, H, FPS, load_frames, fit, writer, extract_audio, loop_audio, src_time, to_bw, zoom


def ref_labels(ref, first='b'):
    """Per-frame A/B label of a 2-shot strobe reference via k-means on tiny thumbnails.
    Returns list of bools (True = A). The first frame's cluster is `first`."""
    fr = load_frames(ref, max_side=160)
    X = np.float32([cv2.resize(f, (9, 16)).ravel() for f in fr])
    _, lab, _ = cv2.kmeans(X, 2, None, (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 50, 0.5), 5, cv2.KMEANS_PP_CENTERS)
    lab = lab.ravel()
    a_cluster = 1 - lab[0] if first == 'b' else lab[0]
    return [bool(l == a_cluster) for l in lab]


def pingpong(i, n):
    if n <= 1:
        return 0
    i %= 2 * (n - 1)
    return i if i < n else 2 * (n - 1) - i


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--a', required=True, help='shot A: video or image (e.g. deity)')
    p.add_argument('--b', required=True, help='shot B: video or image (e.g. aarti)')
    p.add_argument('--ref', help='reference reel: copy its A/B cut pattern and audio')
    p.add_argument('--first', default='b', choices=['a', 'b'], help='which shot the reference opens on')
    p.add_argument('--audio', help='song (if no --ref)')
    p.add_argument('--pattern', default='3,4', help='frames per shot, cycled (if no --ref)')
    p.add_argument('--min-dur', type=float, default=0, help='extend song on-beat to at least this many seconds')
    p.add_argument('--bw', default='', help="'a', 'b' or 'ab' to make those shots black & white")
    p.add_argument('--wm', default='', help='inpaint a watermark on B: x,y,r in source pixels (e.g. Veo/Gemini sparkle)')
    p.add_argument('--push', type=float, default=0.08, help='slow zoom-in over the whole reel')
    p.add_argument('--flash', type=float, default=1.12, help='brightness multiplier on each cut (1 = off)')
    p.add_argument('--out', required=True)
    a = p.parse_args()
    tmp = tempfile.mkdtemp()

    song = extract_audio(a.ref or a.audio, os.path.join(tmp, 'song.wav'))
    if a.min_dur:
        segs, dur = loop_audio(song, os.path.join(tmp, 'loop.wav'), a.min_dur)
        song = os.path.join(tmp, 'loop.wav')
    else:
        import soundfile as sf
        info = sf.info(song); segs, dur = [(0.0, 0.0)], info.frames / info.samplerate
    N = int(dur * FPS)

    if a.ref:
        lab = ref_labels(a.ref, a.first)
    else:
        pat = [int(x) for x in a.pattern.split(',')]
        lab, cur, k = [], False, 0
        while len(lab) < N + 1000:
            lab += [cur] * pat[k % len(pat)]; cur = not cur; k += 1

    A, B = load_frames(a.a), load_frames(a.b).copy()
    if a.wm:
        x, y, r = map(int, a.wm.split(','))
        m = np.zeros(B.shape[1:3], np.uint8); cv2.circle(m, (x, y), r, 255, -1)
        for i in range(len(B)):
            B[i] = cv2.inpaint(B[i], m, 5, cv2.INPAINT_TELEA)
    A = [fit(f) for f in A] if len(A) == 1 else A

    w = writer(a.out, song)
    prev = None
    for n in range(N):
        m = int(round(src_time(n / FPS, segs) * FPS))      # cut pattern follows the (looped) music
        isA = lab[min(m, len(lab) - 1)]
        src = A if isA else B
        f = src[pingpong(n, len(src))]                     # footage keeps moving, ping-pong past its end
        if f.shape[:2] != (H, W):
            f = fit(f)
        if ('a' in a.bw and isA) or ('b' in a.bw and not isA):
            f = to_bw(f)
        f = zoom(f, 1 + a.push * n / N)
        if prev is not None and isA != prev and a.flash != 1:
            f = cv2.convertScaleAbs(f, alpha=a.flash, beta=6)
        if n > N - 30:
            f = (f * ((N - n) / 30)).astype(np.uint8)
        prev = isA
        w.stdin.write(f.tobytes())
    w.stdin.close(); w.wait()
    print('done', a.out, f'{N / FPS:.1f}s')


if __name__ == '__main__':
    main()
