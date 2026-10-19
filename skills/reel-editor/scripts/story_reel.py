#!/usr/bin/env python3
"""Render square illustrated story reels. See references/story-first-reels.md."""
import argparse
import json
import math
from pathlib import Path
import subprocess
import tempfile
import unicodedata

FPS = 30
SKILL = Path(__file__).resolve().parent.parent


def run(args):
    result = subprocess.run([str(x) for x in args], capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError(result.stderr[-6000:])
    return result.stdout


def probe(path):
    return json.loads(run(['ffprobe', '-v', 'error', '-show_streams', '-show_format', '-of', 'json', path]))


def number(value):
    result = float(value)
    if not math.isfinite(result):
        raise ValueError('Times must be finite')
    return result


def normalized(text):
    return ''.join(c for c in unicodedata.normalize('NFC', text) if unicodedata.category(c)[0] in 'LNM').casefold()


def validate(spec, base):
    duration = number(spec['duration'])
    if duration <= 0 or abs(duration * FPS - round(duration * FPS)) > 1e-6:
        raise ValueError('Duration must be positive and on the 30 fps frame grid')
    audio = (base / spec['audio']).resolve()
    media = probe(audio)
    if not any(s['codec_type'] == 'audio' for s in media['streams']):
        raise ValueError('Narration file has no audio stream')
    audio_duration = float(media['format']['duration'])
    if audio_duration > duration + 0.02:
        raise ValueError('Output would truncate narration')
    if duration - audio_duration > number(spec.get('max_end_hold', 1.0)):
        raise ValueError('Unexplained end hold: check recording completeness')
    scenes = spec['scenes']
    if not scenes:
        raise ValueError('At least one scene is required')
    previous = 0
    for scene in scenes:
        start, end = number(scene['start']), number(scene['end'])
        first, last = round(start * FPS), round(end * FPS)
        if start < 0 or first != previous or last <= first:
            raise ValueError('Scenes must cover the timeline contiguously with at least one frame each')
        if not (base / scene['image']).is_file():
            raise ValueError('Missing scene image: ' + scene['image'])
        previous = last
        if scene.get('motion', 'push') not in ('push', 'pull', 'hold'):
            raise ValueError('Motion must be push, pull or hold')
    if previous != round(duration * FPS):
        raise ValueError('Scene coverage does not match duration')
    captions = spec['captions']
    previous = 0.0
    for cue in captions:
        start, end = number(cue['start']), number(cue['end'])
        if start < previous or end <= start or end > duration or not cue['text'].strip():
            raise ValueError('Captions must be nonempty, ordered and within the timeline')
        if any(c in cue['text'] for c in '{}\\\r'):
            raise ValueError('Use plain caption text with | for a line break; ASS overrides are not allowed')
        previous = end
    approved = (base / spec['approved_script']).read_text(encoding='utf-8')
    if not normalized(approved) or normalized(approved) != normalized(' '.join(c['text'] for c in captions)):
        raise ValueError('Caption text differs from approved script; check missing or duplicated lines')
    title = spec['title']
    if not isinstance(title, list) or len(title) != 2 or any(not isinstance(t, str) or not t.strip() or any(c in t for c in '{}\\\n\r') for t in title):
        raise ValueError('Title must contain two nonempty plain-text lines')
    handle = spec.get('handle', '@aitricksbysumit')
    if not isinstance(handle, str) or any(c in handle for c in '{}\\\n\r'):
        raise ValueError('Handle must be plain text')
    font = (base / spec['font']).resolve() if 'font' in spec else SKILL / 'fonts/deva/noto-sans-devanagari-700.ttf'
    if not font.is_file():
        raise ValueError('Missing font')
    family = spec.get('font_family', 'Noto Sans Devanagari')
    if not isinstance(family, str) or not family.strip() or any(c in family for c in ',\r\n'):
        raise ValueError('Invalid font family')
    return duration, audio, font


def timestamp(t, srt=False):
    scale = 1000 if srt else 100
    n = round(t * scale)
    return f'{n // (3600*scale):02}:{n // (60*scale) % 60:02}:{n // scale % 60:02}' + (f',{n % scale:03}' if srt else f'.{n % scale:02}')


def write_captions(spec, folder):
    family = spec.get('font_family', 'Noto Sans Devanagari')
    header = f'''[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 2
[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Caption,{family},61,&H00FFFFFF,&H0062D7FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,1,0,5,85,155,0,1
Style: Title,{family},74,&H00FFFFFF,&H0062D7FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,1,0,5,85,155,0,1
Style: Brand,DejaVu Sans,29,&H25FFFFFF,&H0062D7FF,&H65000000,&H80000000,0,0,0,0,100,100,0,0,1,2,0,5,85,155,0,1
[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
'''
    end = timestamp(spec['duration'])
    title = spec['title'][0] + r'\N{\c&H62D7FF&}' + spec['title'][1]
    events = [f'Dialogue: 1,0:00:00.00,{end},Title,,0,0,0,,{{\\pos(505,304)}}{title}',
              f'Dialogue: 1,0:00:00.00,{end},Brand,,0,0,0,,{{\\pos(505,1462)}}' + spec.get('handle', '@aitricksbysumit')]
    srt = []
    for i, cue in enumerate(spec['captions'], 1):
        text = cue['text'].replace('|', r'\N{\c&H62D7FF&}', 1).replace('|', r'\N')
        events.append(f"Dialogue: 2,{timestamp(cue['start'])},{timestamp(cue['end'])},Caption,,0,0,0,,{{\\pos(505,1600)\\fad(50,70)}}{text}")
        plain = cue['text'].replace('|', '\n')
        srt.append(f"{i}\n{timestamp(cue['start'], True)} --> {timestamp(cue['end'], True)}\n{plain}\n")
    (folder / 'captions.ass').write_text(header + '\n'.join(events), encoding='utf-8')
    (folder / 'captions.srt').write_text('\n'.join(srt), encoding='utf-8')


def check_video(path, frames):
    stream = next(s for s in probe(path)['streams'] if s['codec_type'] == 'video')
    if (stream['width'], stream['height'], int(stream.get('nb_frames', 0))) != (1080, 1920, frames) or abs(float(stream['duration']) - frames / FPS) > 1 / FPS:
        raise RuntimeError('Incomplete video or wrong dimensions')


def render(spec, base, out):
    duration, audio, font = validate(spec, base)
    out.parent.mkdir(parents=True, exist_ok=True)
    # Work beside the destination so the validated result can replace it atomically.
    with tempfile.TemporaryDirectory(prefix='story-reel-', dir=out.parent) as temp:
        folder = Path(temp)
        (folder / 'fonts').mkdir()
        import shutil
        shutil.copy2(font, folder / 'fonts' / font.name)
        write_captions(spec, folder)
        clips = []
        for i, scene in enumerate(spec['scenes']):
            count = round(scene['end'] * FPS) - round(scene['start'] * FPS)
            motion = scene.get('motion', 'push')
            zoom = f'1.025+0.065*on/{count}' if motion == 'push' else (f'1.09-0.065*on/{count}' if motion == 'pull' else '1.025')
            # Use normalized local filenames inside the ASS filter (safe for spaces/quotes in output paths).
            vf = f"scale=1800:1800:force_original_aspect_ratio=increase,crop=1800:1800,zoompan=z='{zoom}':x='(iw-iw/zoom)*0.48':y='(ih-ih/zoom)*0.46':d={count}:s=1080x1080:fps=30,pad=1080:1920:0:420:black,setsar=1,format=yuv420p"
            clip = folder / f'{i:03}.mp4'
            print(f'Scene {i+1}/{len(spec["scenes"])}', flush=True)
            run(['ffmpeg', '-y', '-v', 'error', '-xerror', '-i', (base / scene['image']).resolve(), '-vf', vf, '-frames:v', count, '-an', '-c:v', 'libx264', '-preset', 'fast', '-crf', '18', '-threads', '2', '-movflags', '+faststart', clip])
            check_video(clip, count)
            clips.append(clip.name)
        (folder / 'concat.txt').write_text('\n'.join(f"file '{p}'" for p in clips))
        partial = folder / 'final.mp4'
        # Relative filters avoid escaping arbitrary external paths through libavfilter.
        command = ['ffmpeg', '-y', '-v', 'error', '-xerror', '-f', 'concat', '-safe', '0', '-i', 'concat.txt', '-i', str(audio), '-vf', 'ass=captions.ass:fontsdir=fonts', '-af', 'apad,aformat=channel_layouts=stereo,loudnorm=I=-14:TP=-1.7:LRA=9', '-map', '0:v:0', '-map', '1:a:0', '-t', str(duration), '-r', '30', '-c:v', 'libx264', '-preset', 'fast', '-crf', '18', '-threads', '2', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k', '-ar', '48000', '-ac', '2', '-movflags', '+faststart', 'final.mp4']
        result = subprocess.run(command, cwd=folder, capture_output=True, text=True)
        if result.returncode:
            raise RuntimeError(result.stderr[-6000:])
        check_video(partial, round(duration * FPS))
        final_streams = probe(partial)['streams']
        if not any(s['codec_type'] == 'audio' and s['codec_name'] == 'aac' and s.get('channels') == 2 and int(s.get('sample_rate', 0)) == 48000 for s in final_streams):
            raise RuntimeError('Missing or invalid final AAC stereo audio stream')
        run(['ffmpeg', '-v', 'error', '-xerror', '-i', partial, '-f', 'null', '-'])
        shutil.copy2(folder / 'captions.srt', out.with_suffix('.srt'))
        shutil.copy2(folder / 'captions.ass', out.with_suffix('.ass'))
        partial.replace(out)
    print(f'Verified {duration:.2f}s, {round(duration*FPS)} frames: {out}')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('spec', type=Path)
    parser.add_argument('--out', type=Path)
    parser.add_argument('--validate-only', action='store_true')
    args = parser.parse_args()
    spec = json.loads(args.spec.read_text(encoding='utf-8'))
    base = args.spec.resolve().parent
    validate(spec, base)
    if args.validate_only:
        print('Manifest, media duration and caption coverage passed; recording content still requires listening.')
    elif args.out is None:
        parser.error('--out is required for rendering')
    else:
        render(spec, base, args.out.resolve())


if __name__ == '__main__':
    try:
        main()
    except (ValueError, KeyError, OSError, RuntimeError) as exc:
        raise SystemExit(f'error: {exc}')
