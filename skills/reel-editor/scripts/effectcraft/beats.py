"""beats.py — onset detection -> plan.json (cut times snapped to beats, one image + caption word per cut).
usage: python3 beats.py song.wav plan_in.json plan.json
plan_in.json: {"images": [...], "words": [...], "fps": 30}  (len(words) == len(images) or words empty)"""
import sys, json, numpy as np, soundfile as sf


def onsets(path, hop_hz=100, win=4, thr=0.30):
    x, sr = sf.read(path)
    if x.ndim > 1: x = x.mean(1)
    h = sr // hop_hz
    e = np.array([np.sqrt(np.mean(x[i:i + h] ** 2)) for i in range(0, len(x) - h, h)])
    d = np.maximum(0, np.diff(e, prepend=e[0]))
    d /= d.max() + 1e-9
    on = [i / hop_hz for i in range(win, len(d) - win) if d[i] == d[i - win:i + win + 1].max() and d[i] > thr]
    return on, len(x) / sr, [float(d[int(o * hop_hz)]) for o in on]


def plan_cuts(on, dur, n):
    """n cuts: the first at 0, the rest snapped to the onset nearest to an even grid (never reusing one)."""
    cuts, used = [0.0], set()
    for k in range(1, n):
        target = dur * k / n
        cand = [o for o in on if o not in used and o > cuts[-1] + 0.25]
        if not cand: cuts.append(target); continue
        o = min(cand, key=lambda c: abs(c - target))
        if abs(o - target) > 0.45: o = target          # no beat close enough: keep the grid
        used.add(o); cuts.append(round(o, 3))
    return cuts


if __name__ == '__main__':
    song, pin, pout = sys.argv[1:4]
    cfg = json.load(open(pin))
    on, dur, strength = onsets(song)
    imgs = cfg['images']; words = cfg.get('words') or [''] * len(imgs)
    cuts = plan_cuts(on, dur, len(imgs))
    fps = cfg.get('fps', 30)
    cuts = [round(round(c * fps) / fps, 4) for c in cuts]        # frame-align
    shots = [dict(image=i, word=w, start=s, end=(cuts[k + 1] if k + 1 < len(cuts) else round(dur, 4)))
             for k, (i, w, s) in enumerate(zip(imgs, words, cuts))]
    json.dump(dict(song=song, duration=round(dur, 4), fps=fps, onsets=on, shots=shots), open(pout, 'w'), indent=1)
    print(f'{len(on)} onsets, {len(shots)} shots, cuts={[s["start"] for s in shots]}')
