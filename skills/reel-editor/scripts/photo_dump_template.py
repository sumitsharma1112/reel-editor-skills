"""Recreate an Instagram Edits "photo dump" template from a cut list (templates/*.json).

A template = exact cut times learned from the original (playhead/handle tracking of a screen recording),
the long "hero" slots, and timed text items. Short slots strobe through your photos/clips; hero slots
get the photo/clip you choose, with a slow push.

  python photo_dump_template.py --template ../templates/take_me_to_the_beach.json \
      --media photos/ --hero me.jpg,beach.jpg,mountain.jpg --audio song.wav --out reel.mp4
  # change the words:  --texts "take me to|the mountains"

Learning a new template from a screen recording of the Edits timeline:
  1. Play the template once and screen-record it. The playhead is fixed; clip handles (white "I" boxes)
     pass it in real time. Sample the clip track a few px left/right of the playhead line every frame;
     each time it turns white = a cut. t0 = first hit (playback start).
  2. Text track (purple) under the playhead gives the text item spans; read the item labels from frames.
  3. Merge hits closer than 0.055 s. Slots longer than ~0.5 s are hero slots.
  4. Save {cuts, texts, hero_slots, duration} as templates/<name>.json; the song can be taken from the
     recording audio starting at t0 (user's own reel only).
"""
import argparse, glob, json, math, os, subprocess, sys
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 1080, 1920, 30
FD = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'fonts')
EXT_IMG = ('.jpg', '.jpeg', '.png', '.webp')


def cover(img):
    h, w = img.shape[:2]; s = max(W / w, H / h)
    img = cv2.resize(img, (math.ceil(w * s), math.ceil(h * s)), interpolation=cv2.INTER_LANCZOS4 if s > 1 else cv2.INTER_AREA)
    y, x = (img.shape[0] - H) // 2, (img.shape[1] - W) // 2
    return img[y:y + H, x:x + W]


class Media:
    def __init__(self, path):
        self.path = path; self.is_img = path.lower().endswith(EXT_IMG)
        if self.is_img:
            self.img = cover(cv2.imread(path))
        else:
            self.dur = float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', path],
                                            capture_output=True, text=True).stdout)

    def frames(self, n, start=None, push=0.0):
        if self.is_img:
            out = []
            for j in range(n):
                z = 1 + push * j / max(1, n)
                M = cv2.getRotationMatrix2D((W / 2, H / 2), 0, z); out.append(cv2.warpAffine(self.img, M, (W, H), borderMode=cv2.BORDER_REFLECT))
            return out
        ss = start if start is not None else max(0, (self.dur - n / FPS) / 2)
        raw = subprocess.run(['ffmpeg', '-v', 'error', '-ss', f'{ss:.3f}', '-i', self.path, '-frames:v', str(n), '-vf',
                              f'fps={FPS},scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H}', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-'],
                             capture_output=True).stdout
        k = len(raw) // (W * H * 3); fr = list(np.frombuffer(raw[:k * W * H * 3], np.uint8).reshape(k, H, W, 3))
        while len(fr) < n: fr.append(fr[-1] if fr else np.zeros((H, W, 3), np.uint8))
        return fr


def text_layer(s, size=92):
    ft = ImageFont.truetype(os.path.join(FD, 'montserrat-500.ttf'), size)
    b = ft.getbbox(s); im = Image.new('RGBA', (b[2] - b[0] + 80, b[3] - b[1] + 80))
    ImageDraw.Draw(im).text((40 - b[0], 40 - b[1]), s, font=ft, fill=(255, 255, 255))
    sh = Image.new('RGBA', im.size, (0, 0, 0, 0)); sh.putalpha(im.split()[3].point(lambda v: int(v * 0.55)))
    out = Image.new('RGBA', im.size); out.alpha_composite(sh.filter(ImageFilter.GaussianBlur(10)), (0, 4)); out.alpha_composite(im)
    return np.array(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--template', required=True); ap.add_argument('--media', required=True, help='folder or comma list')
    ap.add_argument('--hero', default='', help='comma list, one per hero slot (in order)')
    ap.add_argument('--audio', default=''); ap.add_argument('--texts', default='', help="override text items, '|' separated")
    ap.add_argument('--out', required=True)
    a = ap.parse_args()
    T = json.load(open(a.template))
    cuts = T['cuts']; slots = [(cuts[i], cuts[i + 1]) for i in range(len(cuts) - 1)]
    paths = sorted(sum([glob.glob(os.path.join(a.media, '*' + e)) for e in EXT_IMG + ('.mp4', '.mov', '.MOV')], [])) \
        if os.path.isdir(a.media) else a.media.split(',')
    pool = [Media(p) for p in paths]
    heroes = [Media(p) for p in a.hero.split(',')] if a.hero else []
    texts = T['texts']
    if a.texts:
        for t, s in zip(texts, a.texts.split('|')): t['text'] = s
    tl = [(t['t0'], t['t1'], text_layer(t['text'])) for t in texts]
    cmd = ['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-']
    if a.audio: cmd += ['-i', a.audio, '-map', '0:v', '-map', '1:a', '-c:a', 'aac', '-b:a', '192k', '-shortest']
    cmd += ['-c:v', 'libx264', '-crf', '19', '-maxrate', '12M', '-bufsize', '24M', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', a.out]
    pr = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    k = 0; hi = 0; written = 0
    for si, (s0, s1) in enumerate(slots):
        n = int(round(s1 * FPS)) - written
        if n <= 0: continue
        if si in T['hero_slots'] and hi < len(heroes):
            fr = heroes[hi].frames(n, push=0.08); hi += 1
        else:
            fr = pool[k % len(pool)].frames(n, push=0.02); k += 1
        for j, f in enumerate(fr):
            t = (written + j) / FPS
            for t0, t1, L in tl:
                if t0 <= t < t1:
                    f = f.copy(); y0 = H // 2 - L.shape[0] // 2; x0 = W // 2 - L.shape[1] // 2
                    roi = f[y0:y0 + L.shape[0], x0:x0 + L.shape[1]].astype(np.float32); al = L[..., 3:4] / 255
                    f[y0:y0 + L.shape[0], x0:x0 + L.shape[1]] = (roi * (1 - al) + L[..., 2::-1][..., :3] * al).astype(np.uint8)
            pr.stdin.write(f.tobytes())
        written += n
    pr.stdin.close(); pr.wait(); print('done', a.out, f'{written / FPS:.2f}s', len(slots), 'slots')


if __name__ == '__main__':
    main()
