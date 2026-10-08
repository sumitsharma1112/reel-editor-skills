"""Depth cover: big title BEHIND the subject (crown / trident / head overlaps the letters), small spaced
kicker above. Uses rembg (u2net) to cut the subject out of the photo and paste it back over the title.

  python depth_cover.py --img photo.png --title "अयि गिरि|नन्दिनि" --kicker "JAI MATA DI" --out cover.jpg
  python depth_cover.py --img photo.png --title "LADAKH" --font ../fonts/cinzel-900.ttf --color 255,255,255 --out cover.jpg

Pick a photo with open sky above the subject and let only the TOP of the subject (head, crown,
weapon tip) overlap the last line. Text must stay readable in the 3:4 grid crop (y 240-1680).
"""
import argparse, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from deva_kit import swash

W, H = 1080, 1920
FD = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'fonts')


def text(t, font, size, color):
    ft = ImageFont.truetype(font, size, layout_engine=ImageFont.Layout.RAQM); b = ft.getbbox(t); p = size
    im = Image.new('RGBA', (b[2] - b[0] + 2 * p, b[3] - b[1] + 2 * p)); ImageDraw.Draw(im).text((p - b[0], p - b[1]), t, font=ft, fill=color)
    return im.crop(im.getbbox())


def glow(im, r, a, col=(0, 0, 0)):
    p = r * 3; o = Image.new('RGBA', (im.width + 2 * p, im.height + 2 * p))
    sh = Image.new('RGBA', im.size, col + (0,)); sh.putalpha(im.split()[3].point(lambda v: int(v * a)))
    o.alpha_composite(sh, (p, p + 6)); o = o.filter(ImageFilter.GaussianBlur(r)); o.alpha_composite(im, (p, p)); return o


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--img', required=True); ap.add_argument('--title', required=True, help="lines split by |")
    ap.add_argument('--kicker', default=''); ap.add_argument('--font', default=os.path.join(FD, 'deva', 'rozha-one-devanagari-400.ttf'))
    ap.add_argument('--color', default='232,18,26'); ap.add_argument('--size', type=int, default=330)
    ap.add_argument('--y', type=int, default=400, help='top of the title'); ap.add_argument('--cut', type=int, default=1100,
                    help='only subject pixels above this y go in front of the text')
    ap.add_argument('--no-swash', action='store_true'); ap.add_argument('--out', required=True)
    a = ap.parse_args()
    from rembg import remove, new_session
    col = tuple(int(c) for c in a.color.split(','))
    bg = Image.open(a.img).convert('RGB'); s = max(W / bg.width, H / bg.height)
    bg = bg.resize((round(bg.width * s), round(bg.height * s)), Image.LANCZOS)
    bg = bg.crop(((bg.width - W) // 2, (bg.height - H) // 2, (bg.width - W) // 2 + W, (bg.height - H) // 2 + H))
    m = np.array(remove(bg, session=new_session('u2net'), only_mask=True).filter(ImageFilter.GaussianBlur(1)))
    m[a.cut:] = 0
    fg = bg.copy(); fg.putalpha(Image.fromarray(m))
    canvas = bg.convert('RGBA')
    lines = a.title.split('|'); y = a.y
    for i, L in enumerate(lines):
        im = text(L, a.font, a.size, col)
        if i == len(lines) - 1 and not a.no_swash:
            im = swash(im, col, 'right', reach=0.3, drop=0.3)
        mw = 960 if i == len(lines) - 1 else 900
        if im.width > mw: im = im.resize((mw, int(im.height * mw / im.width)), Image.LANCZOS)
        im = glow(im, 12, 0.45, (255, 255, 255))
        canvas.alpha_composite(im, (W // 2 - im.width // 2 + 30 * i, y)); y += im.height - 110
    canvas.alpha_composite(fg)                                   # subject in front of the title
    if a.kicker:
        ft = ImageFont.truetype(os.path.join(FD, 'cinzel-700.ttf'), 46); sp = 16
        ws = [ft.getbbox(c)[2] for c in a.kicker]; tw = sum(ws) + sp * (len(a.kicker) - 1)
        k = Image.new('RGBA', (tw + 20, 80)); d = ImageDraw.Draw(k); x = 10
        for c, w in zip(a.kicker, ws): d.text((x, 10), c, font=ft, fill=(255, 255, 255)); x += w + sp
        k = glow(k.crop(k.getbbox()), 10, 0.8)
        canvas.alpha_composite(k, (W // 2 - k.width // 2, a.y - 70))
    canvas.convert('RGB').save(a.out, quality=95)
    print('saved', a.out)


if __name__ == '__main__':
    main()
