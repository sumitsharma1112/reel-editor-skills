"""Masked poster typography for Instagram carousels (Rakesh Nagrikar 'Pandal Hopping' look).
Giant distressed yellow Anton headline across the photo, the person cut out (rembg u2net_human_seg) and
placed IN FRONT of the letters, warm punchy grade + grain, small caps label, handwritten note with arrow.
Usage: python3 poster_mask_type.py photo.jpg "RISHI,KESH" "bas chal,pada…" out.jpg [--label "RISHIKESH DIARIES · MONSOON EDITION"]
pip install rembg onnxruntime   (model downloads from GitHub on first run)"""
import sys, os, argparse, numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter
FD = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'fonts') + '/'
W, H = 1080, 1440                                   # 3:4 carousel
YELLOW = np.array([245, 197, 24], np.float32)

def person_mask(img):
    from rembg import remove, new_session
    m = np.array(remove(img.resize((img.width // 2, img.height // 2)), session=new_session('u2net_human_seg'), only_mask=True))
    m = cv2.resize(m, (W, H))
    n, lab, st, _ = cv2.connectedComponentsWithStats((m > 128).astype(np.uint8))
    if n < 2: return np.zeros((H, W), np.float32)
    k = 1 + np.argmax(st[1:, cv2.CC_STAT_AREA])                     # main subject only, bystanders stay behind
    me = ((lab == k) * 255).astype(np.uint8)
    return cv2.GaussianBlur(cv2.erode(me, np.ones((3, 3))), (0, 0), 1.2).astype(np.float32) / 255

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('photo'); ap.add_argument('lines'); ap.add_argument('note'); ap.add_argument('out')
    ap.add_argument('--label', default=''); ap.add_argument('--top', type=int, default=140); ap.add_argument('--line_h', type=int, default=420)
    ap.add_argument('--note_xy', default='800,1300'); ap.add_argument('--arrow', default='left')
    a = ap.parse_args()
    src = Image.open(a.photo).convert('RGB')
    sw, sh = src.size; tw = int(sh * 3 / 4)                            # centre-crop to 3:4
    if tw <= sw: src = src.crop(((sw - tw) // 2, 0, (sw - tw) // 2 + tw, sh))
    else: th = int(sw * 4 / 3); src = src.crop((0, (sh - th) // 2, sw, (sh - th) // 2 + th))
    src = src.resize((W, H), Image.LANCZOS); me = person_mask(src)
    x = np.asarray(src).astype(np.float32) / 255
    x = np.clip((x - 0.5) * 1.12 + 0.5, 0, 1); x[..., 0] *= 1.04; x[..., 2] *= 0.94; img = (x ** 1.05) * 255
    txt = Image.new('L', (W, H)); f = ImageFont.truetype(FD + 'anton-400.ttf', 400)
    for i, t in enumerate(a.lines.split(',')):
        tmp = Image.new('L', (3000, 900)); ImageDraw.Draw(tmp).text((50, 50), t, font=f, fill=255)
        tmp = tmp.crop(tmp.getbbox()).resize((W - 60, a.line_h), Image.LANCZOS)
        txt.paste(tmp, (30, a.top + i * (a.line_h + 25)), tmp)
    t = np.asarray(txt).astype(np.float32) / 255
    rng = np.random.default_rng(4); sp = cv2.GaussianBlur(rng.random((H, W)).astype(np.float32), (0, 0), 1.3)
    t = t * np.clip((sp - 0.25) * 6, 0.55, 1) * (1 - me)                # ink speckle, subject in front
    img = img * (1 - t[..., None]) + YELLOW * t[..., None] + rng.normal(0, 7, (H, W, 1))
    out = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)); d = ImageDraw.Draw(out)
    if a.label: d.text((34, a.top - 44), a.label, font=ImageFont.truetype(FD + 'montserrat-700.ttf', 26), fill='white')
    hf = ImageFont.truetype(FD + 'caveat-brush-400.ttf', 66); nx, ny = map(int, a.note_xy.split(','))
    def note(dr, fill):
        for j, l in enumerate(a.note.split(',')): dr.text((nx + 20 * j, ny + 62 * j), l, font=hf, fill=fill)
        if a.arrow == 'left':
            dr.line([(nx, ny + 30), (nx - 30, ny + 18), (nx - 55, ny + 22)], fill=fill, width=6, joint='curve')
            dr.polygon([(nx - 62, ny + 23), (nx - 40, ny + 6), (nx - 38, ny + 36)], fill=fill)
    sh_ = Image.new('L', (W, H)); note(ImageDraw.Draw(sh_), 200)
    out.paste((0, 0, 0), (0, 0), sh_.filter(ImageFilter.GaussianBlur(6))); note(ImageDraw.Draw(out), (255, 255, 255))
    out.save(a.out, quality=95); print('saved', a.out)

if __name__ == '__main__': main()
