#!/usr/bin/env python3
"""Build an EDITABLE FilmCraft project (.fcproj) for a reel instead of a flat MP4.

FilmCraft (github.com/storytold/filmcraft, MIT/Apache, Rust, Premiere-like NLE) is driven
headlessly through `filmcraft-cli` (every UI action is a command; same commands over MCP).
This script: new project + 1080x1920 30 fps sequence -> imports the shots + audio ->
places each shot on V1 at its cut time -> Motion.scale keyframes (103 % punch on the cut,
100 % after 0.12 s, slow push to 105 % at the end) -> caption track C1 with one caption per
line (uppercase, cream background, dark Poppins Bold, bottom margin 27 %) -> saves -> optional
export. The person can then open the .fcproj in FilmCraft and change any caption/cut by hand.

Build the CLI (release downloads may be blocked; source build ~10 min):
  git clone --depth 1 https://github.com/storytold/filmcraft && cd filmcraft && cargo build --release -p filmcraft-cli

plan.json:
  {"width":1080,"height":1920,"fps":30,"duration":78.9,"audio":"/abs/audio.wav",
   "shots":[{"t":0,"image":"/abs/shot_01.png"}, ...],
   "captions":[{"t":0,"text":"Line one|line two"}, ...]}
Images should already be 9:16 (cover-crop them first). Media paths are stored absolute:
on another computer use File > Link Media (or `media.autoRelink`).

  python3 filmcraft_project.py plan.json out.fcproj --cli /path/filmcraft-cli [--export out.mp4]
Caption size note: FilmCraft wraps captions at a fixed width, size 25 fits ~35 characters per line.
"""
import argparse, json, subprocess, sys, tempfile

T = 254016000000  # FilmCraft ticks per second


def run(cli, proj, steps, save=True):
    with tempfile.NamedTemporaryFile('w', suffix='.jsonl', delete=False) as f:
        f.write('\n'.join(json.dumps(s, ensure_ascii=False) for s in steps) + '\n')
    args = [cli] + (['--project', proj] if proj else []) + (['--save'] if save and proj else []) + ['run', f.name]
    out = subprocess.run(args, capture_output=True, text=True).stdout.splitlines()
    res = []
    for line in out:
        try:
            d = json.loads(line)
        except ValueError:
            continue
        if not d.get('ok'):
            sys.exit(f'FilmCraft command failed: {line[:300]}')
        res.append(d)
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('plan'); ap.add_argument('out')
    ap.add_argument('--cli', default='filmcraft-cli'); ap.add_argument('--export')
    ap.add_argument('--caption-size', type=float, default=25)
    a = ap.parse_args()
    P = json.load(open(a.plan)); D = P['duration']; shots = P['shots']; caps = P.get('captions', [])
    # 1. project + sequence, saved to out
    with tempfile.NamedTemporaryFile('w', suffix='.jsonl', delete=False) as f:
        f.write(json.dumps({"id": "file.newProject", "params": {"name": P.get('name', 'Reel')}}) + '\n')
        f.write(json.dumps({"id": "file.newSequence", "params": {"name": "Reel", "width": P.get('width', 1080),
                            "height": P.get('height', 1920), "fps": P.get('fps', 30), "video": 3, "audio": 2}}) + '\n')
    subprocess.run([a.cli, 'run', f.name, '--save-as', a.out], check=True, capture_output=True)
    # 2. import, then read item ids by file name
    files = [s['image'] for s in shots] + [P['audio']]
    subprocess.run([a.cli, '--project', a.out, '--save', 'import'] + list(dict.fromkeys(files)), check=True, capture_output=True)
    tree = json.loads(subprocess.run([a.cli, '--project', a.out, 'inspect', 'project'], capture_output=True, text=True, check=True).stdout)
    ids = {c['name']: c['item'] for c in tree['root']['children']}
    base = lambda p: p.rsplit('/', 1)[-1]
    # 3. place shots + audio
    steps = []
    for k, s in enumerate(shots):
        t1 = shots[k + 1]['t'] if k + 1 < len(shots) else D
        steps.append({"id": "timeline.place", "params": {"item": ids[base(s['image'])], "track": "V1", "seconds": s['t'],
                      "duration": {"seconds": round(t1 - s['t'], 4)}, "audio": False}})
    steps.append({"id": "timeline.place", "params": {"item": ids[base(P['audio'])], "track": "A1", "seconds": 0, "video": False}})
    res = run(a.cli, a.out, steps)
    clips = [r['result']['clips'][0] for r in res[:len(shots)]]
    # 4. zoom keyframes + captions
    steps = []
    for k, (s, c) in enumerate(zip(shots, clips)):
        t0 = s['t']; t1 = shots[k + 1]['t'] if k + 1 < len(shots) else D
        for tt, v in ((t0, 103), (t0 + 0.12, 100), (t1 - 0.04, 105)):
            steps.append({"id": "effects.setParam", "params": {"clip": c, "effect": "motion", "param": "scale", "value": v,
                          "time": int(tt * T), "keyframe": True}})
    if caps:
        steps.append({"id": "captions.newTrack", "params": {"format": "Subtitle", "name": "Captions"}})
        for k, c in enumerate(caps):
            t1 = caps[k + 1]['t'] if k + 1 < len(caps) else D
            steps.append({"id": "captions.add", "params": {"track": "C1", "text": c['text'].upper().replace('|', '\n'),
                          "seconds": c['t'], "durationSeconds": round(t1 - c['t'] - 0.02, 3)}})
        steps.append({"id": "captions.setStyle", "params": {"track": "C1", "font": "Poppins", "fontStyle": "Bold", "size": a.caption_size,
                      "color": "#231e1e", "background": True, "backgroundColor": "#faf4e6f5", "align": "center", "anchor": "bottom",
                      "margin": 0.27, "lineSpacing": 1.15}})
    run(a.cli, a.out, steps)
    print('saved', a.out)
    if a.export:  # FilmCraft's export is high-bitrate: recompress with ffmpeg (crf 26, maxrate 2.6M) before Instagram
        subprocess.run([a.cli, '--project', a.out, 'export', a.export, '--range', 'entire'], check=True)


if __name__ == '__main__':
    main()
