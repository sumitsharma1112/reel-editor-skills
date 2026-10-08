"""Place-name title effects that interact with the scene (stills + animated clips).

Effects (each a function f(p, ph) where p = reveal progress 0..1, ph = water phase):
  trevi      - word LYING ON WATER: letters laid out on a flat plane, warped with a perspective transform
               onto the water, modulated by the water's own caustics, rippled, with a teal under-shadow;
               the person (rembg u2net_human_seg) stays in front and the word is split around him (TRE  VI).
  pattaya    - word RISING FROM THE SEA: gradient caps cut at a waterline, rippled reflection under it,
               a foam line where letters meet water; animate the top edge rising out of the water.
  colosseum  - letters FLY OUT OF THE ARCHES: each letter starts tiny at an arch centre and scales/moves
               to its slot, with fading motion ghosts back to the arch; gold gradient + dark outline.
  salzburg   - HUGE word BEHIND the person (hair/head in front), copper-green gradient matching the domes,
               a signature-script country name crossing the corner.
  golden     - Hindi calligraphy (Amita) in liquid-gold gradient with an orange glow, written on left to right.
  sissu      - word SLIDES OUT FROM BEHIND A MOUNTAIN: a hand-traced ridge polygon masks the word, icy
               gradient + frost noise, script "valley" + spaced region caps.
Each recipe uses hard-coded positions for its own photo (base_<name>.png, already cover-fit to 1080x1920).
Re-use the helpers (mask_text, fill, shadow, glow, ripple, person_mask, front) and re-measure positions
on a gridded copy of the new photo before placing text.

  python travel_titles.py            # stills  -> $OUT/<name>.jpg
  python travel_titles_anim.py       # 4 s clips (2.2 s reveal) -> $OUT/<name>.mp4
"""
import os, sys, math, numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter
W, H = 1080, 1920
FD = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'fonts') + '/'
OUT = os.environ.get('OUT', './travel_titles_out/')


def font(f, s): return ImageFont.truetype(FD + f, int(s), layout_engine=ImageFont.Layout.RAQM)


def mask_text(t, f, s, spacing=0):
    ft = font(f, s)
    if spacing:
        parts = [mask_text(c, f, s) if c.strip() else Image.new('L', (int(s * 0.28), 1)) for c in t]; asc = ft.getbbox('H')
        tw = sum(p.width for p in parts) + spacing * (len(parts) - 1); th = max(p.height for p in parts)
        out = Image.new('L', (tw, th)); x = 0
        for c, p in zip(t, parts):
            out.paste(p, (x, th - p.height)); x += p.width + spacing
        return out
    b = ft.getbbox(t); pad = int(s * 0.6)
    m = Image.new('L', (b[2] - b[0] + 2 * pad, b[3] - b[1] + 2 * pad))
    ImageDraw.Draw(m).text((pad - b[0], pad - b[1]), t, font=ft, fill=255)
    return m.crop(m.getbbox())


def gradient(size, stops, axis=1):
    w, h = size; n = h if axis else w
    x = np.linspace(0, 1, n); g = np.zeros((n, 3))
    for c in range(3): g[:, c] = np.interp(x, [s[0] for s in stops], [s[1][c] for s in stops])
    g = g[:, None, :].repeat(w, 1) if axis else g[None, :, :].repeat(h, 0)
    return g.astype(np.float32)


def fill(m, stops, axis=1, shine=0.0):
    """Gradient-filled RGBA from a mask, optional diagonal glossy shine band."""
    g = gradient(m.size, stops, axis)
    if shine:
        yy, xx = np.mgrid[0:m.height, 0:m.width]
        band = np.exp(-(((xx * 0.35 + yy) / max(m.height, 1) - 0.42) / 0.07) ** 2)[..., None]
        g = g + (255 - g) * band * shine
    a = np.array(m)[..., None].astype(np.float32)
    return Image.fromarray(np.concatenate([np.clip(g, 0, 255), a], 2).astype(np.uint8), 'RGBA')


def shadow(im, off=(0, 10), blur=18, alpha=0.5, color=(0, 0, 0), spread=1):
    p = blur * 3; out = Image.new('RGBA', (im.width + 2 * p, im.height + 2 * p))
    sh = Image.new('RGBA', im.size, color + (0,)); sh.putalpha(im.split()[3].point(lambda v: min(255, int(v * alpha * spread))))
    tmp = Image.new('RGBA', out.size); tmp.alpha_composite(sh, (p + off[0], p + off[1]))
    out.alpha_composite(tmp.filter(ImageFilter.GaussianBlur(blur))); out.alpha_composite(im, (p, p))
    return out, p


def glow(im, blur, color, strength=1.0):
    p = blur * 3; out = Image.new('RGBA', (im.width + 2 * p, im.height + 2 * p))
    g = Image.new('RGBA', im.size, color + (0,)); g.putalpha(im.split()[3])
    tmp = Image.new('RGBA', out.size); tmp.alpha_composite(g, (p, p)); tmp = tmp.filter(ImageFilter.GaussianBlur(blur))
    a = np.array(tmp).astype(np.float32); a[..., 3] = np.clip(a[..., 3] * strength, 0, 255); tmp = Image.fromarray(a.astype(np.uint8))
    out.alpha_composite(tmp); out.alpha_composite(im, (p, p)); return out, p


def fit(im, w): return im.resize((w, int(im.height * w / im.width)), Image.LANCZOS) if im.width != w else im


def paste_c(canvas, im, cx, cy, pad=0):
    canvas.alpha_composite(im, (int(cx - im.width / 2), int(cy - im.height / 2)))


def ripple(arr, amp=4, wl=26, phase=0.0, axis_y=True):
    h, w = arr.shape[:2]; yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    dx = amp * np.sin(yy / wl * 2 * math.pi + phase) + amp * 0.5 * np.sin(xx / (wl * 2.3) + phase * 1.7)
    dy = amp * 0.6 * np.sin(xx / (wl * 1.7) * 2 * math.pi + phase * 1.3)
    return cv2.remap(arr, xx + dx, yy + dy, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)


_seg = {}
def person_mask(img, key):
    if key in _seg: return _seg[key]
    from rembg import remove, new_session
    m = remove(img.convert('RGB'), session=new_session('u2net_human_seg'), only_mask=True)
    m = m.filter(ImageFilter.GaussianBlur(1.2)); _seg[key] = m; return m


def front(canvas, base, m):
    fg = base.convert('RGBA').copy(); fg.putalpha(m); canvas.alpha_composite(fg)


def ease(t): t = min(max(t, 0), 1); return 1 - (1 - t) ** 3


def spaced_caps(t, f, s, color, sp):
    m = mask_text(t, f, s, sp); im = Image.new('RGBA', m.size, color + (0,)); im.putalpha(m); return im


# ---------------------------------------------------------------- 1. TREVI lying on the water
def trevi(p=1.0, ph=0.0):
    base = Image.open('base_trevi.png').convert('RGB'); can = base.convert('RGBA')
    plane = Image.new('L', (1400, 420))
    F_ = 'abril-fatface-400.ttf'; full = mask_text('TRE', F_, 380, 14); sc = 600 / full.width
    left = full.resize((600, int(full.height * sc)), Image.LANCZOS); right = mask_text('VI', F_, 380, 14); right = right.resize((int(right.width * sc), int(right.height * sc)), Image.LANCZOS)
    plane.paste(left, (40, 420 - left.height - 6)); plane.paste(right, (1400 - right.width - 90, 420 - right.height - 6))
    m = np.array(plane).astype(np.float32)
    # reveal: letters "float up" from the water (opacity + ripple fade)
    rgb = gradient(plane.size, [(0, (255, 252, 236)), (0.6, (255, 255, 255)), (1, (255, 222, 150))])
    src = np.float32([[0, 0], [1400, 0], [1400, 420], [0, 420]])
    dst = np.float32([[40, 1280], [1040, 1280], [1130, 1620], [-50, 1620]])
    M = cv2.getPerspectiveTransform(src, dst)
    rgba = np.concatenate([rgb, m[..., None]], 2)
    warp = cv2.warpPerspective(rgba, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
    warp = ripple(warp, amp=3 + 3 * (1 - p), wl=14, phase=ph)
    water = np.array(base).astype(np.float32)
    lum = cv2.cvtColor(water.astype(np.uint8), cv2.COLOR_RGB2GRAY).astype(np.float32) / 255
    caust = np.clip(0.92 + 0.35 * (lum - cv2.GaussianBlur(lum, (0, 0), 6)) * 4, 0.75, 1.15)[..., None]
    a = warp[..., 3:4] / 255 * 0.97 * ease(p)
    col = np.clip(warp[..., :3] * caust, 0, 255)
    # soft dark under-glow so the white sits on bright aqua
    sh = cv2.GaussianBlur(warp[..., 3], (0, 0), 7)[..., None] / 255 * 0.55 * ease(p)
    sh_shift = np.roll(np.roll(sh, 12, 0), 8, 1)
    out = water * (1 - sh_shift) + np.array([0, 70, 80]) * sh_shift
    out = out * (1 - a) + col * a
    can = Image.fromarray(np.clip(out, 0, 255).astype(np.uint8)).convert('RGBA')
    # kicker
    k = spaced_caps('FONTANA DI', 'cinzel-700.ttf', 40, (255, 255, 255), 14)
    k, _ = shadow(k, (0, 3), 8, 0.6)
    ka = k.copy(); ka.putalpha(ka.split()[3].point(lambda v: int(v * ease((p - 0.4) / 0.6))))
    paste_c(can, ka, W / 2, 1235)
    front(can, base, person_mask(base, 'trevi'))
    return can.convert('RGB')


# ---------------------------------------------------------------- 2. PATTAYA rising from the sea
def pattaya(p=1.0, ph=0.0):
    base = Image.open('base_pattaya.png').convert('RGB')
    WL = 652                                                     # waterline (just under the horizon)
    m = fit(mask_text('PATTAYA', 'anton-400.ttf', 400, 4), 1010)
    txt = fill(m, [(0, (255, 236, 160)), (0.45, (255, 128, 88)), (1, (222, 48, 118))], shine=0.35)
    h = txt.height
    top = WL - h * ease(p) + 18                                  # rises out of the water
    can = base.convert('RGBA')
    layer = Image.new('RGBA', (W, H)); layer.alpha_composite(txt, ((W - txt.width) // 2, int(top)))
    L = np.array(layer).astype(np.float32)
    yy = np.arange(H)[:, None]
    above = np.clip((WL - yy) / 6 + 1, 0, 1)                      # cut at the waterline
    wet = L.copy(); wet[..., 3] *= above[..., 0] if above.ndim == 3 else above
    # reflection in the sea
    vis = L[:WL].copy(); vis[..., 3] *= above[:WL]
    ref = np.zeros_like(L); fl = vis[::-1]; n = min(H - WL, fl.shape[0]); ref[WL:WL + n] = fl[:n]
    fade = np.clip(1 - (yy - WL) / 260, 0, 1) * 0.45; ref[..., 3] *= fade
    ref = ripple(ref, amp=7, wl=9, phase=ph); ref[..., 3] *= (yy >= WL)
    for lay in (ref, wet):
        a = lay[..., 3:4] / 255
        base_arr = np.array(can).astype(np.float32)
        base_arr[..., :3] = base_arr[..., :3] * (1 - a) + lay[..., :3] * a
        can = Image.fromarray(base_arr.astype(np.uint8), 'RGBA')
    # foam line where letters meet the water
    if p > 0.2:
        fm = Image.new('RGBA', (W, H)); d = ImageDraw.Draw(fm)
        d.rectangle([(W - txt.width) // 2, WL - 3, (W + txt.width) // 2, WL + 3], fill=(255, 255, 255, int(120 * min(1, p))))
        can.alpha_composite(fm.filter(ImageFilter.GaussianBlur(4)))
    k = spaced_caps('THAILAND', 'cinzel-700.ttf', 40, (255, 255, 255), 22); k, _ = shadow(k, (0, 3), 8, 0.45)
    ka = k.copy(); ka.putalpha(ka.split()[3].point(lambda v: int(v * ease((p - 0.5) / 0.5))))
    paste_c(can, ka, W / 2, top - 45)
    front(can, base, person_mask(base, 'pattaya'))
    return can.convert('RGB')


# ---------------------------------------------------------------- 3. COLOSSEUM letters out of the arches
ARCH = [(130, 560), (269, 560), (405, 560), (528, 560), (664, 560), (794, 560), (923, 560), (269, 800), (664, 800)]
def colosseum(p=1.0):
    base = Image.open('base_colo.png').convert('RGB'); can = base.convert('RGBA')
    stops = [(0, (255, 240, 190)), (0.5, (255, 196, 70)), (1, (214, 98, 18))]
    lines = [('COLOS', 330, 470), ('SEUM', 330, 720)]
    letters = []
    for word, sz, cy in lines:
        full = mask_text(word, 'cinzel-900.ttf', sz, 10); sc = 1000 / full.width
        x = (W - 1000) / 2
        for c in word:
            mm = mask_text(c, 'cinzel-900.ttf', sz); mm = mm.resize((max(1, int(mm.width * sc)), max(1, int(mm.height * sc))), Image.LANCZOS)
            letters.append((mm, x + mm.width / 2, cy + (full.height * sc - mm.height) / 2)); x += mm.width + 10 * sc
    for i, (mm, tx, ty) in enumerate(letters):
        ax, ay = ARCH[i % len(ARCH)]
        t = ease((p - i * 0.06) / 0.5)
        x = ax + (tx - ax) * t; y = ay + (ty - ay) * t; s = 0.15 + 0.85 * t
        if t <= 0: continue
        im = fill(mm, stops, shine=0.25)
        im = im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))), Image.LANCZOS)
        # motion ghosts back towards the arch
        for g in (0.35, 0.2, 0.1):
            gt = max(0, t - g * 0.6); gx = ax + (tx - ax) * gt; gy = ay + (ty - ay) * gt; gs = 0.15 + 0.85 * gt
            gim = fill(mm, stops).resize((max(1, int(mm.width * gs)), max(1, int(mm.height * gs))), Image.LANCZOS)
            gim.putalpha(gim.split()[3].point(lambda v: int(v * g * 0.9)))
            paste_c(can, gim, gx, gy)
        im2, pd = shadow(im, (6, 12), 10, 0.75, (40, 14, 0))
        im3 = Image.new('RGBA', im2.size)
        ol = Image.new('RGBA', im.size, (52, 22, 4, 0)); ol.putalpha(im.split()[3].filter(ImageFilter.MaxFilter(7)))
        im3.alpha_composite(im2); im3.alpha_composite(ol, (pd, pd)); im3.alpha_composite(im, (pd, pd))
        paste_c(can, im3, x, y)
    k = spaced_caps('ROMA', 'cinzel-700.ttf', 46, (255, 255, 255), 30); k, _ = shadow(k, (0, 3), 8, 0.8)
    ka = k.copy(); ka.putalpha(ka.split()[3].point(lambda v: int(v * ease((p - 0.75) / 0.25))))
    paste_c(can, ka, W / 2, 330)
    return can.convert('RGB')


# ---------------------------------------------------------------- 4. SALZBURG huge behind me
def salzburg(p=1.0):
    base = Image.open('base_salz.png').convert('RGB'); can = base.convert('RGBA')
    m = fit(mask_text('SALZBURG', 'big-shoulders-900.ttf', 520, 6), 1040)
    txt = fill(m, [(0, (232, 255, 250)), (0.35, (122, 226, 206)), (1, (18, 128, 128))], shine=0.3)
    t = ease(p); s = 1.25 - 0.25 * t
    im = txt.resize((int(txt.width * s), int(txt.height * s)), Image.LANCZOS)
    im.putalpha(im.split()[3].point(lambda v: int(v * min(1, p * 2))))
    im, _ = shadow(im, (0, 12), 22, 0.35, (10, 40, 50))
    paste_c(can, im, W / 2, 470 + m.height / 2 - 40)
    sc = Image.new('RGBA', (1, 1))
    k = mask_text('Austria', 'mrs-saint-delafield-400.ttf', 190); ki = Image.new('RGBA', k.size, (255, 255, 255, 0)); ki.putalpha(k)
    ki, _ = shadow(ki, (0, 4), 8, 0.5)
    ki.putalpha(ki.split()[3].point(lambda v: int(v * ease((p - 0.5) / 0.5))))
    paste_c(can, ki, 800, 420)
    front(can, base, person_mask(base, 'salz'))
    return can.convert('RGB')


# ---------------------------------------------------------------- 5. Golden Temple, Hindi calligraphy in gold
def golden(p=1.0):
    base = Image.open('base_golden.png').convert('RGB'); can = base.convert('RGBA')
    m = fit(mask_text('श्री हरिमंदिर साहिब', 'deva/amita-devanagari-700.ttf', 200), 1010)
    txt = fill(m, [(0, (255, 248, 210)), (0.4, (255, 214, 98)), (0.75, (240, 160, 40)), (1, (190, 110, 20))], shine=0.4)
    # write-on reveal left to right
    rv = np.array(txt); cut = int(rv.shape[1] * ease(p)); rv[:, cut:, 3] = 0
    edge = np.clip(1 - np.abs(np.arange(rv.shape[1]) - cut) / 60, 0, 1)
    txt = Image.fromarray(rv)
    g, pd = glow(txt, 26, (255, 170, 40), 1.1)
    paste_c(can, g, W / 2, 345)
    k = spaced_caps('GOLDEN TEMPLE  ·  AMRITSAR', 'cinzel-700.ttf', 25, (255, 226, 160), 5); k, _ = glow(k, 10, (255, 160, 40), 0.7)
    k.putalpha(k.split()[3].point(lambda v: int(v * ease((p - 0.7) / 0.3))))
    paste_c(can, k, 265, 470)
    return can.convert('RGB')


# ---------------------------------------------------------------- 6. SISSU coming out of the right mountain
RIDGE = [(0, 880), (125, 856), (250, 787), (375, 675), (450, 631), (537, 619), (625, 612), (700, 581), (812, 550), (900, 494), (1000, 456), (1080, 412)]
def sissu(p=1.0):
    base = Image.open('base_sissu.png').convert('RGB'); can = base.convert('RGBA')
    m = fit(mask_text('SISSU', 'bebas-neue-400.ttf', 520, 40), 720)
    rng = np.random.default_rng(4); frost = (rng.random((m.height, m.width)) * 30).astype(np.float32)
    txt = fill(m, [(0, (255, 255, 255)), (0.45, (214, 240, 255)), (1, (98, 176, 232))], shine=0.3)
    a = np.array(txt).astype(np.float32); a[..., :3] = np.clip(a[..., :3] - frost[..., None] * 0.6, 0, 255); txt = Image.fromarray(a.astype(np.uint8))
    txt, pd = shadow(txt, (0, 10), 16, 0.55, (16, 30, 60))
    t = ease(p)
    cx_end, cy = 410, 280 + m.height / 2
    cx = 1080 + txt.width / 2 + (cx_end - 1080 - txt.width / 2) * t   # slides out from behind the right mountain
    cy_now = cy + (520 - cy) * (1 - t) * 0.6
    lay = Image.new('RGBA', (W, H)); paste_c(lay, txt, cx, cy_now)
    mtn = Image.new('L', (W, H), 255); ImageDraw.Draw(mtn).polygon(RIDGE + [(1080, 0), (0, 0)], fill=0)
    mtn = mtn.filter(ImageFilter.GaussianBlur(1.5))
    la = np.array(lay); la[..., 3] = (la[..., 3].astype(np.float32) * (1 - np.array(mtn) / 255)).astype(np.uint8)
    can.alpha_composite(Image.fromarray(la))
    k = mask_text('valley', 'mrs-saint-delafield-400.ttf', 230); ki = Image.new('RGBA', k.size, (255, 255, 255, 0)); ki.putalpha(k)
    ki, _ = shadow(ki, (0, 4), 8, 0.6, (16, 30, 60))
    ki.putalpha(ki.split()[3].point(lambda v: int(v * ease((p - 0.65) / 0.35))))
    paste_c(can, ki, 300, 285 + m.height + 10)
    k2 = spaced_caps('LAHAUL  ·  HIMACHAL', 'cinzel-700.ttf', 34, (255, 255, 255), 10); k2, _ = shadow(k2, (0, 3), 8, 0.7, (16, 30, 60))
    k2.putalpha(k2.split()[3].point(lambda v: int(v * ease((p - 0.75) / 0.25))))
    paste_c(can, k2, 410, 262)
    return can.convert('RGB')


ALL = {'1_Trevi': trevi, '2_Pattaya': pattaya, '3_Colosseum': colosseum, '4_Salzburg': salzburg, '5_Golden_Temple': golden, '6_Sissu': sissu}
if __name__ == '__main__':
    only = sys.argv[1:] or list(ALL)
    for k in only:
        ALL[k]().save(OUT + k + '.jpg', quality=95); print('saved', k)
