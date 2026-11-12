# Pack 20: twenty more starter effects, written by Claude for @aitricksbysumit.
# Loaded into fx.py's globals, so every helper from fx.py (place, comp, glass, text_img, ...) is available here.
# Effect names follow the "Effects to try" list; the looks are Claude's own versions, not copies of anyone's code.

WHITE = (255, 255, 255)
NOTE_Y = (255, 204, 0)


def _lay(c):
    return Image.new('RGBA', (c.W, c.H), (0, 0, 0, 0))


def _bg_plate(c, e):
    """A rough empty-room plate: the person is painted out with inpainting (done at low res, so it is soft)."""
    s = 4; w, h = c.W // s, c.H // s
    img = (cv2.resize(c.img, (w, h)) * 255).astype(np.uint8)
    m = (cv2.resize(c.m, (w, h)) > 0.25).astype(np.uint8) * 255
    m = cv2.dilate(m, np.ones((9, 9), np.uint8))
    out = cv2.inpaint(img, m, 9, cv2.INPAINT_TELEA)
    out = cv2.GaussianBlur(out, (0, 0), 2)
    return cv2.resize(out, (c.W, c.H), interpolation=cv2.INTER_CUBIC).astype(np.float32) / 255


def _behind(c, cx, cy, w, h):
    """Sit behind the person, unless the person fills that spot (close-up framing): then just keep off the face."""
    x0, y0, x1, y1 = int(max(0, cx - w / 2)), int(max(0, cy - h / 2)), int(min(c.W, cx + w / 2)), int(min(c.H, cy + h / 2))
    if x1 <= x0 or y1 <= y0: return {'behind': True}
    occ = float(c.m[y0:y1, x0:x1].mean())
    return {'behind': True} if occ < 0.45 else {'guard': True}


def _person(c):
    return c.img.copy(), c.m[..., None].copy()


# 1 ---------------------------------------------------------------------------
@effect('fisheye', 'a bulging fisheye lens punches in on your face, then relaxes')
def fx_fisheye(c, e):
    k = float(e.o.get('strength', 0.9)) * math.sin(math.pi * clamp(c.lt / e.d)) ** 0.6
    if k <= 0.01: return
    yy, xx = np.mgrid[0:c.H, 0:c.W].astype(np.float32)
    cx, cy = c.fx, c.fy + c.fw * 0.2; R = max(c.W, c.H) * 0.62
    dx, dy = (xx - cx) / R, (yy - cy) / R; r = np.sqrt(dx * dx + dy * dy)
    f = 1 / (1 + k * (1 - np.clip(r, 0, 1)) ** 2 * 1.6)
    mx, my = (cx + dx * f * R).astype(np.float32), (cy + dy * f * R).astype(np.float32)
    c.img = cv2.remap(c.img, mx, my, cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)
    c.m = cv2.remap(c.m, mx, my, cv2.INTER_LINEAR)
    vignette(c, 0.45 * k)


# 2 ---------------------------------------------------------------------------
@effect('select-box', 'a blue design-app selection box with handles snaps around you, with a name tag')
def fx_select_box(c, e):
    al = fade(c, e) * clamp(c.lt / 0.06)
    if al <= 0: return
    ys, xs = np.where(c.m > 0.5)
    if len(xs) < 50: return
    x0, x1 = np.percentile(xs, 1), np.percentile(xs, 99); y0 = np.percentile(ys, 0.5); y1 = min(c.H - 4, np.percentile(ys, 99.5))
    p = ease_out(c.lt / 0.3); pad = c.W * 0.03 * (1 + 2 * (1 - p))
    x0, x1, y0, y1 = max(c.W * 0.05, x0 - pad), min(c.W * 0.95, x1 + pad), max(c.H * 0.08, y0 - pad), min(c.H * 0.9, y1 + pad)
    lay = _lay(c); d = ImageDraw.Draw(lay); B = BLUE + (255,); lw = max(3, c.W // 300)
    d.rectangle([x0, y0, x1, y1], outline=B, width=lw)
    hs = c.W * 0.012
    for qx in (x0, (x0 + x1) / 2, x1):
        for qy in (y0, (y0 + y1) / 2, y1):
            if qx == (x0 + x1) / 2 and qy == (y0 + y1) / 2: continue
            d.rectangle([qx - hs, qy - hs, qx + hs, qy + hs], fill=WHITE + (255,), outline=B, width=lw)
    comp(c, to_np(lay), 0, 0, al)
    tag = cached(e, 'tag', lambda: _pill(e.o.get('text', 'You'), int(c.W * 0.034), BLUE, WHITE))
    place(c, tag, x0 + tag.width / 2, y0 - tag.height * 0.75, 1, 0, al)
    size = cached(e, 'sz', lambda: _pill(e.o.get('size', '1080 x 1920'), int(c.W * 0.028), BLUE, WHITE))
    place(c, size, (x0 + x1) / 2, y1 + size.height * 0.8, 1, 0, al * ease_out((c.lt - 0.3) / 0.25))


def _pill(s, size, bg, fg, kind='uib'):
    t = text_img(s, size, kind, fg)
    w, h = t.width + size * 0.6, t.height + size * 0.1
    im = rrect(w, h, h / 2, bg + (255,)); im.alpha_composite(t, (int((w - t.width) / 2), int((h - t.height) / 2)))
    return shadowed(im, 8, 4, 90)


# 3 ---------------------------------------------------------------------------
@effect('artifact', 'a Claude artifact window builds itself behind your head: title bar, code, then a live preview')
def fx_artifact(c, e):
    al = fade(c, e) * pop(c, 0, 0.35)
    if al <= 0: return
    W_, H_ = int(c.W * 0.86), int(c.W * 0.62)
    p = clamp((c.lt - 0.3) / max(0.5, e.d - 0.8))
    def base():
        im = rrect(W_, H_, W_ * 0.04, (250, 249, 245, 255)); d = ImageDraw.Draw(im)
        d.rounded_rectangle([0, 0, W_ - 1, int(H_ * 0.13)], int(W_ * 0.04), fill=(240, 238, 230, 255)); d.rectangle([0, int(H_ * 0.08), W_, int(H_ * 0.13)], fill=(240, 238, 230, 255))
        for i, col in enumerate(((255, 95, 87), (254, 188, 46), (40, 200, 64))):
            r = H_ * 0.025; cx = W_ * 0.04 + i * r * 3; d.ellipse([cx - r, H_ * 0.065 - r, cx + r, H_ * 0.065 + r], fill=col + (255,))
        t = text_img(e.o.get('text', 'reel_editor.html'), int(H_ * 0.06), 'uim', (60, 60, 64)); im.alpha_composite(t, (int(W_ / 2 - t.width / 2), int(H_ * 0.065 - t.height / 2)))
        t = _pill('Artifact', int(H_ * 0.045), ORANGE, WHITE); im.alpha_composite(t, (int(W_ - t.width - W_ * 0.02), int(H_ * 0.065 - t.height / 2)))
        return im
    im = cached(e, 'base', base).copy(); d = ImageDraw.Draw(im)
    lines = ['<div class="reel">', '  <video src="you.mp4"/>', '  <Effect name="glow"/>', '  <Captions style="pop"/>', '</div>']
    cols = [(124, 92, 255), (40, 40, 44), (217, 119, 87), (34, 150, 94), (124, 92, 255)]
    ch = int(H_ * 0.055); n_chars = int(p * 2.2 * sum(len(l) for l in lines)); shown = 0
    split = W_ * 0.5 if p > 0.5 else W_
    for i, (l, col) in enumerate(zip(lines, cols)):
        k = max(0, min(len(l), n_chars - shown)); shown += len(l)
        if k: d.text((W_ * 0.05, H_ * 0.2 + i * ch * 1.6), l[:k], font=font('mono', ch * 0.82), fill=col + (255,))
    if p > 0.5:
        q = ease_out((p - 0.5) / 0.3)
        d.rectangle([split, H_ * 0.13, W_, H_], fill=(236, 233, 224, 255)); d.line([split, H_ * 0.13, split, H_], fill=(210, 205, 195, 255), width=3)
        pw, ph = W_ * 0.3, H_ * 0.66; px, py = split + (W_ - split - pw) / 2, H_ * 0.22
        thumb = Image.fromarray((np.clip(c.img, 0, 1) * 255).astype(np.uint8)).resize((int(pw), int(ph)))
        m = Image.new('L', thumb.size, 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, thumb.width - 1, thumb.height - 1], int(pw * 0.08), fill=int(255 * q))
        thumb = thumb.convert('RGBA'); thumb.putalpha(m); im.alpha_composite(thumb, (int(px), int(py)))
    cy_ = above_head(c, H_) + c.H * 0.02; place(c, shadowed(im, 20, 12, 120), c.W / 2, cy_, 0.9 + 0.1 * al, 0, al, **_behind(c, c.W / 2, cy_, W_, H_))


# 4 ---------------------------------------------------------------------------
@effect('flash-cut', 'a white flash with a hard punch-in and a tiny shake, cut on a word')
def fx_flash_cut(c, e):
    z = float(e.o.get('zoom', 1.35))
    u = c.lt
    if u < e.d * 0.5: face_cam(c, z - 0.06 * clamp(u / 0.4), 0.42)
    else: face_cam(c, 1 + (z - 1) * 0.55, 0.42)
    sh = math.exp(-u * 14) * c.W * 0.012
    if sh > 0.5:
        M = np.float32([[1, 0, sh * math.sin(u * 90)], [0, 1, sh * math.cos(u * 71)]])
        c.img = cv2.warpAffine(c.img, M, (c.W, c.H), borderMode=cv2.BORDER_REFLECT)
    for t0 in (0.0, e.d * 0.5):
        f = math.exp(-max(0, c.lt - t0) / 0.07) if c.lt >= t0 else 0
        if f > 0.01: c.img = c.img * (1 - f) + f


# 5 ---------------------------------------------------------------------------
@effect('wall-captions', 'your words appear painted on the wall beside you in 3D perspective, with a light trail')
def fx_wall_captions(c, e):
    words = e.o.get('text', 'Wall|captions').split('|')
    al = fade(c, e)
    side = e.o.get('side', 'left')
    per = e.d / max(1, len(words))
    for i, w in enumerate(words):
        t0 = i * per * 0.75
        if c.lt < t0: continue
        k = ease_out((c.lt - t0) / 0.35)
        S = int(c.W * 0.16)
        t = cached(e, ('w', i), lambda w=w: text_img(w, S, 'anton', (255, 252, 240), glow=((255, 220, 150), 18)))
        tw, th = t.size
        A = to_np(t)
        # perspective: the near edge (towards the centre) is taller than the far edge
        far = 0.55; x_near = c.W * 0.62 if side == 'left' else c.W * 0.38
        x_far = c.W * 0.03 if side == 'left' else c.W * 0.97
        ycen = c.H * 0.2 + i * c.H * 0.11
        hn, hf = th * 1.0, th * far
        if side == 'left':
            dst = np.float32([[x_far, ycen - hf / 2], [x_near, ycen - hn / 2], [x_near, ycen + hn / 2], [x_far, ycen + hf / 2]])
        else:
            dst = np.float32([[x_near, ycen - hn / 2], [x_far, ycen - hf / 2], [x_far, ycen + hf / 2], [x_near, ycen + hn / 2]])
        srcp = np.float32([[0, 0], [tw, 0], [tw, th], [0, th]])
        M = cv2.getPerspectiveTransform(srcp, dst)
        L = cv2.warpPerspective(A, M, (c.W, c.H))
        if k < 1:  # light trail as it slides into place
            sh = (1 - k) * c.W * 0.25 * (1 if side == 'left' else -1)
            trail = np.zeros_like(L)
            for j in range(6):
                Mj = np.float32([[1, 0, -sh * j / 6], [0, 1, 0]]); trail += cv2.warpAffine(L, Mj, (c.W, c.H)) * (0.35 * (1 - j / 6))
            L = np.clip(L * k + trail, 0, 1)
        occ = float((c.m * (L[..., 3] > 0.3)).sum() / max(1.0, (L[..., 3] > 0.3).sum()))
        comp(c, L, 0, 0, al, **({'behind': True} if occ < 0.45 else {'guard': True}))


# 6 ---------------------------------------------------------------------------
@effect('magnifier', 'a magnifying glass glides in and enlarges a spot (your face by default)')
def fx_magnifier(c, e):
    al = fade(c, e) * ease_out(c.lt / 0.3)
    if al <= 0: return
    R = int(c.W * float(e.o.get('size', 0.2))); z = float(e.o.get('zoom', 2.0))
    tx = float(e.o['x']) * c.W if 'x' in e.o else c.fx; ty = float(e.o['y']) * c.H if 'y' in e.o else c.fy
    p = ease_inout(c.lt / 0.6); sx, sy = c.W * 1.1, c.H * 0.85
    cx, cy = sx + (tx - sx) * p, sy + (ty - sy) * p
    x0, y0 = int(cx - R / z), int(cy - R / z); sz = int(2 * R / z)
    xs = np.clip(np.arange(x0, x0 + sz), 0, c.W - 1); ys = np.clip(np.arange(y0, y0 + sz), 0, c.H - 1)
    reg = cv2.resize(np.ascontiguousarray(c.img[np.ix_(ys, xs)]), (2 * R, 2 * R), interpolation=cv2.INTER_CUBIC)
    yy, xx = np.mgrid[0:2 * R, 0:2 * R].astype(np.float32); rr = np.sqrt((xx - R) ** 2 + (yy - R) ** 2) / R
    bend = 1 - 0.18 * rr ** 2
    reg = cv2.remap(reg, (R + (xx - R) * bend).astype(np.float32), (R + (yy - R) * bend).astype(np.float32), cv2.INTER_LINEAR)
    reg = reg + (np.clip(0.9 - rr, 0, 1) * 0)[..., None]
    spec = np.exp(-(((xx - R * 0.6) / (R * 0.35)) ** 2 + ((yy - R * 0.55) / (R * 0.2)) ** 2)) * 0.35
    reg = np.clip(reg + spec[..., None], 0, 1)
    a = np.clip((1 - rr) * R * 0.5, 0, 1)[..., None]
    L = np.concatenate([reg, a], -1)
    # handle and rim
    lay = _lay(c); d = ImageDraw.Draw(lay); rim = max(6, R // 9)
    ang = math.radians(40); hx0, hy0 = cx + R * math.cos(ang), cy + R * math.sin(ang)
    d.line([(hx0, hy0), (hx0 + R * 1.1 * math.cos(ang), hy0 + R * 1.1 * math.sin(ang))], fill=(30, 30, 34, 255), width=rim * 2)
    comp(c, to_np(lay), 0, 0, al)
    comp(c, L, cx - R, cy - R, al)
    d2 = _lay(c); ImageDraw.Draw(d2).ellipse([cx - R, cy - R, cx + R, cy + R], outline=(30, 30, 34, 255), width=rim)
    ImageDraw.Draw(d2).ellipse([cx - R + rim * 0.4, cy - R + rim * 0.4, cx + R - rim * 0.4, cy + R - rim * 0.4], outline=(200, 200, 205, 255), width=max(2, rim // 3))
    comp(c, to_np(d2), 0, 0, al)


# 7 ---------------------------------------------------------------------------
@effect('graph-split', 'the frame splits: a growing bar graph slides into the top half, you move to the bottom')
def fx_graph_split(c, e):
    p = ease_inout(c.lt / 0.45) * clamp((e.d - c.lt) / 0.35)
    if p <= 0: return
    hh = int(c.H * 0.46 * p)
    shift(c, hh * 0.55)
    vals = [float(v) for v in str(e.o.get('values', '12|19|27|41|66|100')).split('|')]
    labels = str(e.o.get('labels', 'Jun|Jul|Aug|Sep|Oct|Nov')).split('|')
    title = e.o.get('text', 'Views per month')
    W_, H_ = c.W, int(c.H * 0.46)
    k = ease_out((c.lt - 0.35) / 1.0)
    im = Image.new('RGBA', (W_, H_), (14, 14, 18, 255)); d = ImageDraw.Draw(im)
    t = text_img(title, int(c.W * 0.05), 'uib', WHITE); im.alpha_composite(t, (int(W_ * 0.06), int(H_ * 0.06)))
    bx0, bx1, by1, by0 = W_ * 0.08, W_ * 0.92, H_ * 0.86, H_ * 0.26
    n = len(vals); gap = (bx1 - bx0) / n; mx = max(vals)
    for i, v in enumerate(vals):
        kk = clamp(k * n - i * 0.6)
        h = (by1 - by0) * v / mx * ease_out(kk)
        col = (255, 70, 100) if i == n - 1 else (90, 90, 104)
        d.rounded_rectangle([bx0 + i * gap + gap * 0.18, by1 - h, bx0 + (i + 1) * gap - gap * 0.18, by1], int(gap * 0.12), fill=col + (255,))
        lt = text_img(labels[i % len(labels)], int(c.W * 0.028), 'uim', (160, 160, 170)); im.alpha_composite(lt, (int(bx0 + i * gap + gap / 2 - lt.width / 2), int(by1 + H_ * 0.02)))
        if i == n - 1 and kk > 0.9:
            vt = text_img(e.o.get('top', '+8x'), int(c.W * 0.05), 'uib', (255, 70, 100)); im.alpha_composite(vt, (int(bx0 + i * gap + gap / 2 - vt.width / 2), int(by1 - h - vt.height)))
    comp(c, to_np(im), 0, hh - H_)
    d2 = _lay(c); ImageDraw.Draw(d2).rectangle([0, hh - 3, c.W, hh + 3], fill=WHITE + (255,)); comp(c, to_np(d2), 0, 0, 0.9)


# 8 ---------------------------------------------------------------------------
@effect('flight-map', 'a dotted flight path arcs between two places on a map card behind you, with a plane flying it')
def fx_flight_map(c, e):
    al = fade(c, e) * pop(c, 0, 0.35)
    if al <= 0: return
    places = str(e.o.get('text', 'Jalandhar|Dubai')).split('|')
    W_, H_ = int(c.W * 0.86), int(c.W * 0.56)
    def base():
        im = rrect(W_, H_, W_ * 0.05, (16, 28, 46, 255)); d = ImageDraw.Draw(im)
        rng = np.random.default_rng(4)
        for gx in range(0, W_, int(W_ / 46)):
            for gy in range(0, H_, int(W_ / 46)):
                v = math.sin(gx / W_ * 9.0 + 1.3) * math.cos(gy / H_ * 6.0) + 0.5 * math.sin(gx / W_ * 21 + gy / H_ * 13)
                if v > 0.35: d.ellipse([gx - 3, gy - 3, gx + 3, gy + 3], fill=(70, 110, 150, 255))
        return im
    im = cached(e, 'b', base).copy(); d = ImageDraw.Draw(im)
    A = (W_ * 0.78, H_ * 0.32); B = (W_ * 0.22, H_ * 0.62)
    pts = [(A[0] + (B[0] - A[0]) * u, A[1] + (B[1] - A[1]) * u - math.sin(math.pi * u) * H_ * 0.35) for u in np.linspace(0, 1, 80)]
    p = ease_inout((c.lt - 0.3) / max(0.6, e.d - 0.9)); n = int(len(pts) * p)
    for i in range(0, n, 3): d.ellipse([pts[i][0] - 4, pts[i][1] - 4, pts[i][0] + 4, pts[i][1] + 4], fill=WHITE + (255,))
    for (x, y), name in ((A, places[0]), (B, places[-1])):
        d.ellipse([x - 12, y - 12, x + 12, y + 12], fill=(255, 70, 100, 255), outline=WHITE + (255,), width=4)
        t = text_img(name, int(W_ * 0.05), 'uib', WHITE); im.alpha_composite(t, (int(x - t.width / 2), int(y + 16)))
    if 0 < n < len(pts):
        x, y = pts[n - 1]; x2, y2 = pts[min(n, len(pts) - 1)]; ang = math.degrees(math.atan2(y2 - y, x2 - x))
        pl = Image.new('RGBA', (60, 60), (0, 0, 0, 0)); pd = ImageDraw.Draw(pl)
        pd.polygon([(58, 30), (8, 22), (8, 38)], fill=WHITE + (255,)); pd.polygon([(34, 30), (18, 4), (26, 4), (44, 30)], fill=WHITE + (255,)); pd.polygon([(34, 30), (18, 56), (26, 56), (44, 30)], fill=WHITE + (255,))
        pl = pl.rotate(-ang, Image.BICUBIC, expand=True); im.alpha_composite(pl, (int(x - pl.width / 2), int(y - pl.height / 2)))
    cy_ = above_head(c, H_) + c.H * 0.02; place(c, shadowed(im, 18, 10, 120), c.W / 2, cy_, 1, 0, al, **_behind(c, c.W / 2, cy_, W_, H_))


# 9 comment-box already exists in the base pack.

# 10 --------------------------------------------------------------------------
@effect('room-swap', 'your room wipes away and you are standing somewhere else (uses the images folder or a gradient)')
def fx_room_swap(c, e):
    def room():
        if e.cards:
            im = e.cards[0].convert('RGB'); sw, sh = im.size; s = max(c.W / sw, c.H / sh)
            im = im.resize((int(sw * s) + 1, int(sh * s) + 1), Image.LANCZOS); l, t = (im.width - c.W) // 2, (im.height - c.H) // 2
            return np.asarray(im.crop((l, t, l + c.W, t + c.H)), np.float32) / 255
        yy = np.linspace(0, 1, c.H)[:, None, None]
        return np.clip(np.float32([0.98, 0.62, 0.78]) * (1 - yy) + np.float32([0.42, 0.28, 0.72]) * yy, 0, 1) * np.ones((1, c.W, 1), np.float32)
    R = cached(e, 'room', room)
    p = ease_inout(c.lt / 0.6) * clamp((e.d - c.lt) / 0.4)
    if p <= 0: return
    x = int(c.W * p); m = c.m[..., None]
    new = R * (1 - m) + c.img * m
    out = c.img.copy(); out[:, :x] = new[:, :x]
    if 0 < x < c.W: out[:, max(0, x - 4):x + 4] = 1.0
    c.img = out


# 11 --------------------------------------------------------------------------
@effect('apple-notes', 'an Apple Notes checklist sits beside you and ticks itself off, line by line')
def fx_apple_notes(c, e):
    al = fade(c, e) * pop(c, 0, 0.3)
    if al <= 0: return
    items = str(e.o.get('text', 'Fisheye|Select box|Artifact|Flash cut|Wall captions|Magnifier')).split('|')
    title = e.o.get('title', 'Effects to try')
    W_ = int(c.W * 0.5); S = int(W_ * 0.07); rowh = int(S * 1.55); H_ = int(S * 4.2 + rowh * len(items))
    per = max(0.25, (e.d - 0.6) / len(items))
    im = rrect(W_, H_, W_ * 0.07, (252, 251, 246, 255)); d = ImageDraw.Draw(im)
    d.text((W_ * 0.06, S * 0.4), '< Notes', font=font('uim', S * 0.62), fill=NOTE_Y + (255,))
    d.text((W_ * 0.78, S * 0.4), 'Done', font=font('uib', S * 0.62), fill=NOTE_Y + (255,))
    d.text((W_ * 0.06, S * 1.5), title, font=font('uib', S * 1.05), fill=(20, 20, 22, 255))
    for i, it in enumerate(items):
        y = S * 3.4 + i * rowh; done = c.lt > 0.5 + per * (i + 1) - per * 0.3
        cx, cy, r = W_ * 0.1, y + S * 0.5, S * 0.42
        if done:
            d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=NOTE_Y + (255,)); tick(d, cx - r * 0.55, cy - r * 0.5, r * 1.1, WHITE + (255,), max(2, int(S / 6)))
        else: d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(190, 190, 196, 255), width=max(2, S // 9))
        col = (160, 160, 166) if done else (24, 24, 26)
        d.text((W_ * 0.2, y), it, font=font('uim', S * 0.82), fill=col + (255,))
        if done:
            tw = font('uim', S * 0.82).getlength(it); d.line([(W_ * 0.2, y + S * 0.55), (W_ * 0.2 + tw, y + S * 0.55)], fill=col + (255,), width=max(2, S // 10))
        cur = 0.5 + per * i < c.lt < 0.5 + per * (i + 1)
        if cur and not done: d.rounded_rectangle([W_ * 0.17, y - S * 0.15, W_ * 0.95, y + S * 1.1], S // 4, fill=(255, 236, 140, 110))
    side = 1 if c.fx < c.W / 2 else -1
    cx = c.fx + side * (c.fw * 0.9 + W_ * 0.55); cx = clamp(cx, W_ * 0.55, c.W - W_ * 0.55)
    cy_ = clamp(max(c.fy + c.fw * 1.3, c.H * 0.62), H_ * 0.55, c.H - H_ * 0.55)
    place(c, shadowed(im, 16, 8, 110), cx, cy_, 1, 0, al)


# 12 --------------------------------------------------------------------------
@effect('dolly-zoom', 'the vertigo shot: you stay the same size while the room behind you stretches away')
def fx_dolly_zoom(c, e):
    k = float(e.o.get('amount', 0.35)) * ease_inout(c.lt / e.d)
    if k <= 0.003: return
    plate = cached(e, 'plate', lambda: _bg_plate(c, e))
    z = 1 + k
    M = cv2.getRotationMatrix2D((c.fx, c.fy), 0, z)
    bg = cv2.warpAffine(plate, M, (c.W, c.H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)
    # radial blur on the room for the push
    acc = bg.copy()
    for j in range(1, 4):
        Mj = cv2.getRotationMatrix2D((c.fx, c.fy), 0, 1 + 0.012 * j * k / 0.35); acc += cv2.warpAffine(bg, Mj, (c.W, c.H), borderMode=cv2.BORDER_REFLECT)
    bg = acc / 4
    m = c.m[..., None]
    c.img = bg * (1 - m) + c.img * m


# 13 --------------------------------------------------------------------------
@effect('stop-motion', 'drops to 8 frames a second with tiny jitter, like a stop-motion clip')
def fx_stop_motion(c, e):
    fps = float(e.o.get('fps', 8)); step = int(c.lt * fps)
    if e.state.get('step') != step:
        rng = random.Random(step * 31 + 7)
        e.state['step'] = step; e.state['hold'] = c.img.copy(); e.state['holdm'] = c.m.copy()
        e.state['j'] = (rng.uniform(-1, 1) * c.W * 0.006, rng.uniform(-1, 1) * c.W * 0.006, rng.uniform(-0.7, 0.7), rng.uniform(0.96, 1.04))
    dx, dy, rot, br = e.state['j']
    M = cv2.getRotationMatrix2D((c.W / 2, c.H / 2), rot, 1.02); M[0, 2] += dx; M[1, 2] += dy
    c.img = np.clip(cv2.warpAffine(e.state['hold'], M, (c.W, c.H), borderMode=cv2.BORDER_REFLECT) * br, 0, 1)
    c.m = cv2.warpAffine(e.state['holdm'], M, (c.W, c.H))
    lum = (c.img @ np.float32([0.299, 0.587, 0.114]))[..., None]; c.img = np.clip(lum + (c.img - lum) * 0.85, 0, 1) * np.float32([1.04, 1.0, 0.92])
    vignette(c, 0.4)


# 14 --------------------------------------------------------------------------
@effect('word-funnel', 'words swirl in from the edges and get sucked into a funnel behind your head')
def fx_word_funnel(c, e):
    words = str(e.o.get('text', 'ideas|scripts|captions|edits|hooks|thumbnails|music|b-roll')).split('|')
    al = fade(c, e)
    cx, cy = c.fx, c.fy - c.fw * 0.1
    for i, w in enumerate(words):
        t0 = i * (e.d * 0.6 / len(words)); u = (c.lt - t0) / 1.2
        if u <= 0 or u >= 1: continue
        ang = i * 2.39996 + u * 4.5; r = (1 - ease_inout(u)) * c.W * 0.62 + c.fw * 0.2
        x, y = cx + r * math.cos(ang), cy + r * math.sin(ang) * 0.75
        S = int(c.W * 0.085)
        t = cached(e, ('w', i), lambda w=w: text_img(w, S, 'uib', WHITE, glow=((120, 160, 255), 12), shadow=8))
        place(c, t, x, y, 0.2 + 0.8 * (1 - u), math.degrees(-ang) * 0.15, al * math.sin(math.pi * u) ** 0.5, guard=True)
    # the funnel glow
    g = _lay(c); d = ImageDraw.Draw(g)
    for j in range(6):
        rr = c.fw * (0.5 + j * 0.45) * (1 + 0.05 * math.sin(c.lt * 8 + j))
        d.ellipse([cx - rr, cy - rr * 0.42, cx + rr, cy + rr * 0.42], outline=(120, 160, 255, int(140 - j * 20)), width=max(2, c.W // 300))
    comp(c, to_np(g.filter(ImageFilter.GaussianBlur(2))), 0, 0, al * ease_out(c.lt / 0.3), behind=True)


# 15 --------------------------------------------------------------------------
@effect('glass-tunnel', 'you fly through a tunnel of frosted glass panels behind your head')
def fx_glass_tunnel(c, e):
    al = fade(c, e) * ease_out(c.lt / 0.3)
    if al <= 0: return
    n = 7; spd = float(e.o.get('speed', 0.9))
    # soft blur of the room so the panels read as glass
    bl = cv2.GaussianBlur(c.img, (0, 0), c.W / 200 * al)
    m = c.m[..., None]; c.img = bl * (1 - m) + c.img * m
    base = c.img.copy()
    for j in range(n, 0, -1):
        ph = (j - (c.lt * spd) % 1.0) / n
        s = 0.12 + ph ** 1.6 * 1.25
        w, h = int(c.W * s), int(c.H * s * 0.62)
        if w < 30 or w > c.W * 1.3: continue
        cx, cy = c.fx, c.fy + c.fw * 0.3
        x0, y0 = int(cx - w / 2), int(cy - h / 2)
        lay = Image.new('RGBA', (w + 8, h + 8), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
        a = int(255 * min(1, (1.15 - ph)) * al)
        d.rounded_rectangle([4, 4, w + 3, h + 3], int(w * 0.08), fill=(200, 220, 255, int(35 * (1 - ph) * al)))
        d.rounded_rectangle([4, 4, w + 3, h + 3], int(w * 0.08), outline=(235, 245, 255, a), width=max(4, int(c.W * 0.01 * (0.4 + ph))))
        gl = lay.filter(ImageFilter.GaussianBlur(10))
        comp(c, to_np(gl), x0 - 4, y0 - 4, 1, guard=True); comp(c, to_np(lay.filter(ImageFilter.GaussianBlur(1))), x0 - 4, y0 - 4, 1, guard=True)


# 16 --------------------------------------------------------------------------
@effect('prompt-box', 'an AI prompt box under your chin types your line and hits send')
def fx_prompt_box(c, e):
    al = fade(c, e) * pop(c, 0, 0.3)
    if al <= 0: return
    txt = e.o.get('text', 'Make my reel look professional')
    W_ = int(c.W * 0.86); S = int(c.W * 0.04); H_ = int(S * 3.6)
    n = int(len(txt) * clamp((c.lt - 0.25) / max(0.4, e.d * 0.55)))
    sent = c.lt > 0.35 + e.d * 0.62
    im = rrect(W_, H_, H_ * 0.3, (255, 255, 255, 250)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, W_ - 1, H_ - 1], int(H_ * 0.3), outline=(220, 218, 210, 255), width=3)
    shown = txt[:n] + ('|' if not sent and int(c.lt * 2.5) % 2 == 0 else '')
    if not n: shown = 'Ask anything...' ; col = (160, 160, 166)
    else: col = (24, 24, 26)
    d.text((S * 0.8, H_ * 0.18), shown, font=font('uim', S), fill=col + (255,))
    d.text((S * 0.8, H_ * 0.62), '+   Tools', font=font('uim', S * 0.7), fill=(130, 130, 136, 255))
    br = H_ * 0.22; bx, by = W_ - br * 1.8, H_ * 0.68
    press = 0.85 if sent and c.lt < 0.35 + e.d * 0.62 + 0.12 else 1
    d.ellipse([bx - br * press, by - br * press, bx + br * press, by + br * press], fill=ORANGE + (255,) if n else (200, 200, 205, 255))
    d.line([(bx, by + br * 0.45), (bx, by - br * 0.45)], fill=WHITE + (255,), width=max(3, int(br / 4))); d.line([(bx - br * 0.38, by - br * 0.05), (bx, by - br * 0.45), (bx + br * 0.38, by - br * 0.05)], fill=WHITE + (255,), width=max(3, int(br / 4)))
    y = clamp(c.fy + c.fw * 1.55, c.H * 0.45, c.H * 0.8)
    if sent:
        k = ease_inout((c.lt - 0.35 - e.d * 0.62) / 0.35); y -= k * c.H * 0.05
        al *= 1 - k * 0.0
    place(c, shadowed(im, 18, 10, 110), c.W / 2, y, 1, 0, al, guard=True)


# 17 --------------------------------------------------------------------------
@effect('liquid-glass', 'a blob of liquid glass slides across, bending the picture behind it')
def fx_liquid_glass(c, e):
    al = fade(c, e)
    p = ease_inout(c.lt / e.d)
    w, h = int(c.W * 0.62), int(c.W * 0.3)
    cx = -w / 2 + (c.W + w) * p; cy = float(e.o.get('y', 0.72)) * c.H
    wob = 1 + 0.06 * math.sin(c.lt * 6)
    g = glass(c, w * wob, h / wob, h / wob / 2, cx, cy, amt=0.5, blur=c.W // 30)
    comp(c, to_np(g), cx - g.width / 2, cy - g.height / 2, al)
    t = cached(e, 't', lambda: text_img(e.o.get('text', 'liquid glass'), int(h * 0.3), 'uib', WHITE, shadow=8)); place(c, t, cx, cy, 1, 0, al)


# 18 --------------------------------------------------------------------------
@effect('disappear', 'you dissolve into drifting particles and leave the room empty')
def fx_disappear(c, e):
    plate = cached(e, 'plate', lambda: _bg_plate(c, e))
    p = ease_inout(c.lt / max(0.5, e.d * 0.8))
    m = c.m.copy()
    if 'noise' not in e.state:
        n = cv2.resize(np.random.default_rng(5).random((c.H // 12, c.W // 12)).astype(np.float32), (c.W, c.H), interpolation=cv2.INTER_NEAREST)
        yy = np.linspace(0, 1, c.H, dtype=np.float32)[:, None]; e.state['noise'] = n * 0.55 + (1 - yy) * 0.45
    thr = e.state['noise']
    keep = np.clip((thr - p * 1.15) * 12 + 0.5, 0, 1) if p < 1 else np.zeros_like(thr)
    mm = (m * keep)[..., None]
    c.img = plate * (1 - mm) + c.img * mm
    # particles flying off the edge of the dissolve
    ys, xs = np.where((m > 0.5) & (np.abs(thr - p * 1.15) < 0.03))
    if len(xs):
        rng = np.random.default_rng(int(c.lt * 30)); idx = rng.choice(len(xs), min(400, len(xs)), replace=False)
        lay = np.zeros((c.H, c.W, 4), np.float32)
        for i in idx:
            x = int(xs[i] + rng.uniform(10, 80) * c.W / 1080); y = int(ys[i] - rng.uniform(5, 60) * c.W / 1080)
            if 0 <= x < c.W - 4 and 0 <= y < c.H - 4:
                lay[y:y + 4, x:x + 4, :3] = c.img[ys[i], xs[i]]; lay[y:y + 4, x:x + 4, 3] = rng.uniform(0.4, 1)
        comp(c, lay, 0, 0, 1)
    c.m = c.m * keep


# 19 --------------------------------------------------------------------------
@effect('thrown-in', 'cards are thrown into the frame from off screen, spin, and land behind you')
def fx_thrown_in(c, e):
    al = fade(c, e)
    n = int(e.o.get('count', 5)); cw = int(c.W * 0.22)
    cards = cached(e, 'cards', lambda: [card(vary(e.cards[i % len(e.cards)], i) if e.cards else Image.new('RGB', (90, 160), (200, 80, 120)), cw, 0.06) for i in range(n)])
    rng = random.Random(11)
    for i in range(n):
        t0 = i * 0.18; u = (c.lt - t0) / 0.55
        if u <= 0: continue
        side = -1 if i % 2 == 0 else 1
        tx = c.W / 2 + side * c.W * (0.18 + 0.14 * (i // 2)); ty = c.fy - c.fw * (0.2 + 0.5 * rng.random())
        sx, sy = c.W / 2 + side * c.W * 0.9, c.H * 1.1
        k = ease_out(u); x = sx + (tx - sx) * k; y = sy + (ty - sy) * k - math.sin(math.pi * clamp(u)) * c.H * 0.15
        rot = (1 - k) * 540 * side + side * (8 + 6 * i)
        bounce = 1 + 0.08 * math.sin(clamp(u - 1, 0, 1) * 20) * math.exp(-clamp(u - 1, 0, 9) * 6) if u > 1 else 1
        place(c, cards[i], x, y, bounce, rot, al, **_behind(c, x, y, cw, cw * 1.7))


# 20 --------------------------------------------------------------------------
def _bell(size, col=WHITE):
    S = int(size); im = Image.new('RGBA', (S, S), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.pieslice([S * 0.18, S * 0.12, S * 0.82, S * 0.85], 180, 360, fill=col + (255,))
    d.rectangle([S * 0.18, S * 0.48, S * 0.82, S * 0.7], fill=col + (255,))
    d.polygon([(S * 0.1, S * 0.78), (S * 0.9, S * 0.78), (S * 0.82, S * 0.66), (S * 0.18, S * 0.66)], fill=col + (255,))
    d.ellipse([S * 0.4, S * 0.78, S * 0.6, S * 0.95], fill=col + (255,)); d.ellipse([S * 0.45, S * 0.04, S * 0.55, S * 0.16], fill=col + (255,))
    return im


@effect('follow-bell', 'a Follow button flips to Following, then a bell rings and turns on notifications')
def fx_follow_bell(c, e):
    al = fade(c, e) * pop(c, 0, 0.3)
    if al <= 0: return
    at = float(e.o.get('at', 0.6)); bt = at + 0.45
    S = int(c.W * 0.045); bw, bh = int(c.W * 0.42), int(S * 2.4)
    fol = c.lt >= at
    btn = rrect(bw, bh, bh / 2, (60, 60, 66, 255) if fol else (0, 149, 246, 255))
    t = text_img('Following' if fol else 'Follow', S, 'uib', WHITE); btn.alpha_composite(t, ((bw - t.width) // 2, (bh - t.height) // 2))
    press = 0.9 if at - 0.06 < c.lt < at + 0.08 else 1
    cx, cy = c.W / 2 - bh * 0.7, clamp(c.fy + c.fw * 1.7, c.H * 0.62, c.H * 0.82)
    place(c, shadowed(btn, 12, 6, 110), cx, cy, press, 0, al)
    on = c.lt >= bt
    bb = rrect(bh, bh, bh / 2, (255, 214, 10, 255) if on else (60, 60, 66, 255))
    bell = _bell(bh * 0.62, (30, 30, 34) if on else WHITE); bb.alpha_composite(bell, ((bh - bell.width) // 2, (bh - bell.height) // 2))
    ring = math.sin((c.lt - bt) * 40) * 22 * math.exp(-(c.lt - bt) * 5) if on else 0
    place(c, shadowed(bb, 12, 6, 110), cx + bw / 2 + bh * 0.75, cy, 1, ring, al)
    if on:
        k = ease_out((c.lt - bt - 0.15) / 0.3)
        toast = cached(e, 'toast', lambda: _pill('Notifications on for ' + e.o.get('text', '@aitricksbysumit'), int(c.W * 0.03), (30, 30, 34), WHITE, 'uim'))
        place(c, toast, c.W / 2, cy + bh * 1.4, 0.9 + 0.1 * k, 0, al * k)
    cu = cached(e, 'cu', lambda: cursor(c.W * 0.05))
    tgt = (cx, cy) if c.lt < at + 0.2 else (cx + bw / 2 + bh * 0.75, cy)
    pr = ease_inout(c.lt / at) if c.lt < at else 1
    place(c, cu, c.W * 0.9 + (tgt[0] - c.W * 0.9) * pr + cu.width * 0.3, c.H * 0.95 + (tgt[1] - c.H * 0.95) * pr + cu.height * 0.4, 1, 0, al)


@effect('fx-label', 'a small counter pill and effect-name tag in the top-left corner (for demo reels)')
def fx_label(c, e):
    al = fade(c, e, 0.1) * clamp(c.lt / 0.1)
    parts = str(e.o.get('text', '01/20|/effect')).split('|')
    S = int(c.W * 0.034)
    a = cached(e, 'a', lambda: _pill(parts[0], S, (233, 30, 99), WHITE))
    b = cached(e, 'b', lambda: _pill(parts[-1], S, (250, 250, 250), (20, 20, 22)))
    y = c.H * 0.075
    place(c, a, c.W * 0.06 + a.width / 2, y, 1, 0, al); place(c, b, c.W * 0.06 + a.width + b.width / 2 - S * 0.2, y, 1, 0, al)
