"""Text Rise effect (CapCut "text rising from behind the mountain" clone), done automatically.

The word starts hidden below the skyline and rises (ease-out + vertical motion blur) into the sky. It is drawn
ONLY where the sky is, so mountains, trees and the person's head stay in front of it, as in the CapCut
recipe (keyframed text + a duplicate layer with the sky removed on top). The sky mask is computed per
frame (bright + low saturation + connected to the top edge, soft edges, temporal smoothing), so handheld
pans work. The sky is graded darker/cooler so white text pops on a hazy white sky.

  python text_rise.py --video clip.mov --word "ऋषिकेश" --out rise.mp4
  python text_rise.py --video clip.mov --word "CHANDRASHILA" --font ../fonts/anton-400.ttf --speed 1 --out rise.mp4

Tips: pick a shot with open sky above a ridge and the person below it (back to camera, arms opening is
perfect). 60 fps sources at --speed 0.5 give smooth slow motion. Bold Devanagari: Baloo 2 800 reads best;
Sarpanch is very square and hard to read at a glance.
"""
import argparse, os, subprocess
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont

W, H, FPS = 1080, 1920, 30
FD = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'fonts')


def skymask(f, vmin=175, smax=40, maxy=0.55):
    hsv = cv2.cvtColor(f, cv2.COLOR_BGR2HSV); s = hsv[..., 1].astype(np.float32); v = hsv[..., 2].astype(np.float32)
    raw = ((v > vmin) & (s < smax)).astype(np.uint8); raw[int(H * maxy):] = 0
    n, lab = cv2.connectedComponents(raw); top = set(np.unique(lab[:5])) - {0}
    m = np.isin(lab, list(top)).astype(np.uint8)
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8))
    soft = np.clip((v - (vmin - 15)) / 30, 0, 1) * np.clip((smax + 8 - s) / 20, 0, 1)
    m = cv2.dilate(m, np.ones((5, 5), np.uint8)).astype(np.float32) * soft
    return cv2.GaussianBlur(m, (0, 0), 1.2)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--video', required=True); ap.add_argument('--word', required=True); ap.add_argument('--out', required=True)
    ap.add_argument('--font', default=os.path.join(FD, 'deva', 'baloo-2-devanagari-800.ttf'))
    ap.add_argument('--speed', type=float, default=0.5, help='0.5 = every source frame of a 60 fps clip -> 2x slow-mo')
    ap.add_argument('--y-end', type=int, default=105, help='final top of the word'); ap.add_argument('--y-start', type=int, default=860)
    ap.add_argument('--t0', type=float, default=0.55); ap.add_argument('--t1', type=float, default=2.6)
    ap.add_argument('--maxw', type=int, default=1000); ap.add_argument('--no-grade', action='store_true')
    a = ap.parse_args()
    rf = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=r_frame_rate',
                         '-of', 'csv=p=0', a.video], capture_output=True, text=True).stdout.strip().split(',')[0].split('/')
    fps_src = float(rf[0]) / float(rf[1] if len(rf) > 1 else 1)
    vf = f'fps={FPS / a.speed},crop=ih*9/16:ih:(iw-ih*9/16)/2:0,scale={W}:{H}:flags=lanczos' if abs(fps_src - FPS / a.speed) > 0.5 else \
        f'crop=ih*9/16:ih:(iw-ih*9/16)/2:0,scale={W}:{H}:flags=lanczos'
    rd = subprocess.Popen(['ffmpeg', '-v', 'error', '-i', a.video, '-an', '-vf', vf, '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-'], stdout=subprocess.PIPE)
    size = 300; ft = ImageFont.truetype(a.font, size, layout_engine=ImageFont.Layout.RAQM)
    while ft.getlength(a.word) > a.maxw: size -= 4; ft = ImageFont.truetype(a.font, size, layout_engine=ImageFont.Layout.RAQM)
    b = ft.getbbox(a.word); im = Image.new('RGBA', (W, b[3] - b[1] + 60))
    ImageDraw.Draw(im).text(((W - (b[2] - b[0])) // 2 - b[0], 30 - b[1]), a.word, font=ft, fill=(255, 255, 255))
    T = np.array(im).astype(np.float32) / 255.; th = T.shape[0]
    tmp = a.out + '.v.mp4'
    wr = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                           '-c:v', 'libx264', '-crf', '18', '-pix_fmt', 'yuv420p', tmp], stdin=subprocess.PIPE)
    prev = None; prevy = a.y_start; i = 0
    grad = (1 - 0.30 * np.clip(1 - np.arange(H) / 900, 0, 1))[:, None, None]
    while True:
        buf = rd.stdout.read(W * H * 3)
        if len(buf) < W * H * 3: break
        f = np.frombuffer(buf, np.uint8).reshape(H, W, 3); t = i / FPS; i += 1
        m = skymask(f); m = m if prev is None else 0.6 * m + 0.4 * prev; prev = m
        u = min(1, max(0, (t - a.t0) / (a.t1 - a.t0))); e = 1 - (1 - u) ** 4
        y = a.y_start + (a.y_end - a.y_start) * e; vel = abs(y - prevy); prevy = y
        L = cv2.blur(T, (1, int(min(40, vel * 0.9)) | 1)) if vel > 2 else T
        canvas = np.zeros((H, W, 4), np.float32); yi = int(round(y)); ya, yb = max(0, yi), min(H, yi + th)
        if yb > ya: canvas[ya:yb] = L[ya - yi:yb - yi]
        al = canvas[..., 3] * m * (min(1, u * 3) if u > 0 else 0)
        fo = f.astype(np.float32)
        if not a.no_grade:
            sk = cv2.GaussianBlur(m, (0, 0), 7)[..., None]
            fo = fo * (1 - sk) + fo * sk * grad * np.array([0.80, 0.72, 0.66])
            fo = np.clip((fo - 128) * 1.08 + 128, 0, 255)
        sh = cv2.GaussianBlur(al, (0, 0), 9) * 0.35 * m
        fo = fo * (1 - sh[..., None])
        fo = fo * (1 - al[..., None]) + 255 * al[..., None]
        fo = fo + (255 - fo) * (cv2.GaussianBlur(al, (0, 0), 10) * 0.125)[..., None]
        wr.stdin.write(np.clip(fo, 0, 255).astype(np.uint8).tobytes())
    wr.stdin.close(); wr.wait()
    at = f'atempo={a.speed}' if a.speed >= 0.5 else 'atempo=0.5'
    r = subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', tmp, '-i', a.video, '-map', '0:v', '-map', '1:a?', '-c:v', 'copy',
                        '-af', at, '-c:a', 'aac', '-shortest', a.out])
    if r.returncode != 0: os.replace(tmp, a.out)
    elif os.path.exists(tmp): os.remove(tmp)
    print('done', a.out)


if __name__ == '__main__':
    main()
