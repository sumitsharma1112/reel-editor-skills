"""Einstein Part 1 - premium scene engine: cutout layers on periwinkle stage + painted B-roll,
frosted word-by-word captions, beat motion graphics, varied transitions."""
import numpy as np, cv2, math, subprocess, sys, json, wave
from PIL import Image, ImageDraw, ImageFont
W, H = 1080, 1920; FPS = 30; T = 177.19
FD = '/home/claude/effects/fonts/'
ANTON = FD + 'Anton-Regular.ttf'; ARCH = FD + 'ArchivoBlack-Regular.ttf'; SERIF = FD + 'InstrumentSerif-Italic.ttf'
NAVY = (34, 38, 110); GOLD = (255, 190, 60); RED = (214, 40, 60); WHITE = (255, 255, 255)
CZ = '/home/claude/ein/cz/'; IM = '/home/claude/ein/imgs/'

# ------------------------------------------------------------------ SCENES
# e(name, x, y, h, delay, anim)  anim: pop | up | down | left | right | fade | fly
def e(n, x=540, y=1060, h=950, d=0.0, a='pop'): return (n, x, y, h, d, a)
# scene: (t, bg, elements, small, big, transition, overlay)
#   bg: 'g' gradient stage | ('i', n) painting with Ken Burns | ('g', 'dark') dim stage
SC = [
 (0.00, 'g', [e('c01_graduate', 540, 1080, 1000), e('c02_cap', 800, 640, 300, 1.2, 'fly')], 'engineering college ki', 'DEGREE', 'fade', None),
 (3.78, 'g', [e('c04_laptop', 540, 1050, 760), e('c08_question', 860, 700, 330, 1.4, 'pop')], 'acchi CGPA, phir bhi', 'PACKAGE?', 'zoom', None),
 (6.98, 'g', [e('c06_friends', 380, 1040, 900, 0, 'left'), e('c05_offer', 820, 1130, 600, 1.2, 'up')], 'dost celebrate kar rahe, aur tum?', '₹20-25 HAZAAR', 'whip', 'salary'),
 (11.52, 'g', [e('c09_phone_msg', 540, 1070, 1000)], 'itni padhai karke', 'BAS YAHI?', 'up', None),
 (14.88, ('g', 'dark'), [e('c10_books', 230, 1250, 520, 0.6, 'left'), e('c07_lonely', 600, 1080, 940), e('c08_question', 860, 640, 300, 1.4, 'pop')], 'dheere dheere', 'DOUBT', 'blur', None),
 (18.56, 'g', [e('c12_envelopes', 300, 1300, 420, 0.8, 'up'), e('c11_einstein_letters', 600, 1070, 1000)], 'Albert Einstein ne bhi jhela', 'REJECTION', 'flash', 'chapter:ALBERT EINSTEIN'),
 (23.54, 'g', [e('c13_einstein_door', 540, 1070, 1000)], 'jise duniya genius kehne wali thi', 'NO JOB', 'zoom', None),
 (26.30, 'g', [e('c12_envelopes', 540, 1060, 760), e('c08_question', 860, 680, 300, 0.8, 'pop')], 'research aur teaching ki', 'NAUKRI NAHI', 'whip', None),
 (29.54, 'g', [e('c14_patent_desk', 540, 1080, 950)], 'aakhir mila kaam', 'PATENT OFFICE', 'iris', None),
 (31.58, 'g', [e('c15_patent_stack', 540, 1060, 760)], 'subah se shaam', 'APPLICATIONS', 'up', None),
 (35.06, 'g', [e('c22_four_papers', 540, 1040, 760)], 'usi naukri ke dauraan', 'PAPERS', 'zoom', 'glow'),
 (38.26, 'g', [e('c23_pocketwatch', 540, 1040, 860, 0, 'swing')], 'samajhne ka tareeka badla', 'TIME', 'blur', None),
 (40.78, 'g', [e('c16_einstein_think', 540, 1080, 980)], 'dimaag mein ek', 'THOUGHT EXPERIMENT', 'whip', None),
 (43.02, 'g', [e('c18_einstein_run', 540, 1060, 860, 0, 'run')], 'agar main daud sakoon', 'ROSHNI KE SAATH?', 'flash', 'beam'),
 (45.16, ('g', 'dark'), [e('c17_light_beam', 540, 1040, 1100, 0, 'fade'), e('c08_question', 540, 1000, 420, 0.5, 'pop')], 'toh kya woh dikhegi', 'RUKI HUI?', 'whip', None),
 (47.56, 'g', [e('c19_couple', 540, 1080, 1000)], 'phir hui shaadi', 'MILEVA', 'zoom', None),
 (49.20, 'g', [e('c20_cradle', 540, 1080, 700)], 'ghar aur naukri ke beech', 'ZIMMEDAARI', 'blur', None),
 (51.18, 'g', [e('c21_einstein_baby', 540, 1070, 1000)], 'sawaalon ke liye', 'SAMAY?', 'up', None),
 (53.40, ('g', 'dark'), [e('c33_bulb', 540, 1040, 760)], 'din bhar kaam, phir bhi', 'SAPNA ZINDA', 'iris', 'glow'),
 (56.98, 'g', [e('c22_four_papers', 540, 1180, 560, 1.4, 'up')], 'phir aaya saal', 'UMAR SIRF 26', 'flash', 'year'),
 (60.20, ('i', 13), [], 'kuch hi mahinon mein', '4 PAPERS', 'zoom', 'glow'),
 (62.62, 'g', [e('c24_melting_clock', 540, 1060, 820)], 'aur bataya', 'RELATIVITY', 'whip', None),
 (64.58, ('i', 12), [], 'poore universe ki', 'NO MASTER CLOCK', 'blur', None),
 (67.20, 'g', [e('c25_clock_set', 540, 1060, 900)], 'motion aur gravity se', 'ALAG TIME', 'iris', 'tick'),
 (71.44, 'g', [e('c10_books', 540, 1080, 820)], 'ye sirf textbook nahi', 'REAL LIFE', 'up', None),
 (73.20, 'g', [e('c27_smartphone_map', 540, 1080, 900), e('c28_satellite', 820, 620, 260, 0.6, 'orbit')], 'tumhare phone ka', 'GPS', 'zoom', None),
 (76.64, 'g', [e('c30_india_gate', 540, 1120, 820), e('c29_pin', 540, 690, 260, 0.8, 'down')], 'imagine karo', 'INDIA GATE', 'whip', None),
 (79.38, ('i', 16), [], 'pin Connaught Place ki taraf', 'BHATAK GAYI', 'flash', 'pin'),
 (82.40, 'g', [e('c27_smartphone_map', 540, 1080, 860)], 'sirf samjhaane ke liye', 'EXAMPLE', 'blur', None),
 (84.40, 'g', [e('c28_satellite', 540, 920, 560, 0, 'orbit'), e('c29_pin', 540, 1250, 300, 0.8, 'down')], 'corrections hata do toh', '10 KM ROZ', 'zoom', 'km'),
 (90.60, 'g', [e('c26_einstein_chalk', 540, 1080, 1000)], 'aur equation ne bataya', 'E = MC²', 'flash', None),
 (93.36, 'g', [e('c31_atom', 540, 1040, 760, 0, 'spin')], 'thode se mass mein', 'VISHAAL ENERGY', 'zoom', 'energy'),
 (96.50, 'g', [e('c32_cooling_tower', 400, 1080, 820), e('c33_bulb', 820, 820, 420, 1.0, 'pop')], 'aaj New York State ki', 'BIJLI', 'whip', 'glow'),
 (100.92, ('i', 18), [], 'is bijli ke peeche', 'LOW-CARBON', 'blur', None),
 (104.24, 'g', [e('c26_einstein_chalk', 540, 1080, 1000)], 'samjhaata hai', 'YAHI EQUATION', 'up', 'energy'),
 (106.12, 'g', [e('c34_chain_atoms', 540, 1060, 860)], 'fission aur', 'CHAIN REACTION', 'flash', 'energy'),
 (109.30, 'g', [e('c16_einstein_think', 540, 1080, 980)], 'lekin Einstein ne', 'BOMB NAHI BANAYA', 'zoom', None),
 (113.10, 'g', [e('c35_sun', 540, 1040, 640, 0, 'spin')], 'ab lauto gravity par', 'STARLIGHT', 'flash', 'chapter:GRAVITY|curve'),
 (115.90, ('i', 20), [], 'suraj ke paas', 'RAASTA MUDEGA', 'blur', 'curve'),
 (120.26, 'g', [e('c36_telescope', 300, 1130, 680, 0.5, 'left'), e('c37_freundlich', 660, 1080, 960)], '1914 · astronomer', 'FREUNDLICH', 'whip', None),
 (123.40, 'g', [e('c42_steam_train', 540, 1060, 560, 0, 'run')], 'team aur telescopes lekar', 'CRIMEA', 'zoom', None),
 (126.16, ('g', 'dark'), [e('c38_eclipse', 540, 1040, 760)], 'suryagrahan ke dauraan', 'TASVEEREN', 'iris', 'corona'),
 (129.60, ('i', 22), [e('c39_glass_plate', 800, 1300, 420, 0.6, 'up')], 'prediction jaanchni thi', 'SABOOT', 'blur', None),
 (133.68, ('g', 'dark'), [e('c40_soldiers', 540, 1080, 960, 0, 'left')], 'lekin shuru ho gaya', 'WORLD WAR', 'flash', None),
 (137.00, 'g', [e('c41_astronomer_held', 540, 1080, 1000)], 'German astronomers', 'GIRAFTAAR', 'whip', 'stamp'),
 (140.62, ('g', 'dark'), [e('c37_freundlich', 540, 1080, 1000)], 'aasmaan ke khojne wale', 'KAIDI', 'blur', None),
 (144.10, 'g', [e('c43_einstein_confused', 540, 1080, 1000)], 'lekin twist ye tha', 'CALCULATION', 'flash', None),
 (146.84, 'g', [e('c43_einstein_confused', 540, 1250, 1500, 0, 'fade')], 'Einstein ki bhi', 'KAMI THI', 'zoom', None),
 (148.14, 'g', [e('c39_glass_plate', 520, 1080, 760), e('c08_question', 860, 700, 320, 0.6, 'pop')], 'agar tasveeren mil jaatin', 'SAWAAL?', 'up', None),
 (151.72, 'g', [e('c44_letter', 540, 1060, 900)], 'saalon baad, ek chitthi', '1939', 'flash', 'chapter:THE LETTER|type'),
 (155.86, 'g', [e('c46_white_house', 540, 1120, 620), e('c45_flying_envelope', 540, 760, 360, 0.2, 'fly')], 'President tak pahunchi', 'ROOSEVELT', 'whip', None),
 (158.84, 'g', [e('c47_president_desk', 540, 1080, 860)], 'aise hathiyaar ki', 'CHETAVANI', 'zoom', None),
 (161.28, ('g', 'dark'), [e('c48_harbour', 540, 1080, 760)], 'ek dhamaake mein', 'BANDARGAH', 'flash', 'blast'),
 (166.18, 'g', [e('c49_older_einstein', 540, 1080, 1000)], 'woh dar kis baat se rahe the?', 'KIS KHATRE SE?', 'blur', None),
 (168.60, ('g', 'dark'), [e('c38_eclipse', 540, 1000, 700), e('c39_glass_plate', 820, 1300, 360, 0.6, 'up')], 'kis tasveer ne naam amar kiya?', 'KAUN SI TASVEER?', 'iris', 'corona'),
 (172.10, 'g', [e('c50_einstein_back', 540, 1080, 1000, 0, 'walk')], 'aage ki kahani', 'PART 2', 'zoom', 'follow'),
]
CUTS = [s[0] for s in SC] + [T]
TD = 0.24

# ------------------------------------------------------------------ CAPTIONS
CAP = [
 (0.0, 3.48, "Kya ho agar kisi badhiya engineering college se degree lene ke baad"),
 (3.78, 6.58, "acchi CGPA hone par bhi tumhein manchaha package na mile?"),
 (6.98, 11.52, "Dost apni placement celebrate kar rahe hon aur tumhein 20-25 hazaar ki naukri karni pade"),
 (11.52, 14.36, "Sab poochhein itni padhai karke bas yahi mila?"),
 (14.88, 18.06, "Aur dheere dheere tumhein bhi apni kaabiliyat par doubt hone lage"),
 (18.56, 23.54, "Rakam aur daur alag the lekin Albert Einstein ne bhi aisa rejection jhela tha"),
 (23.54, 29.10, "Jise duniya genius kehne wali thi use shuruaat mein research aur teaching ki naukri tak nahi mili"),
 (29.54, 31.10, "Aakhir ek patent office mein kaam mila"),
 (31.58, 35.06, "Subah se shaam doosron ke inventions ki applications jaanchna"),
 (35.06, 37.88, "Phir usi naukri ke dauraan usne aise papers likhe"),
 (38.26, 40.46, "jinhone time ko samajhne ka tareeka badal diya"),
 (40.78, 42.68, "Ek thought experiment dimaag mein chalne laga"),
 (43.02, 45.16, "Agar main roshni ki kiran ke saath daud sakoon"),
 (45.16, 47.18, "toh kya woh mujhe ruki hui dikhai degi?"),
 (47.56, 48.70, "Phir Mileva se shaadi hui"),
 (49.20, 51.18, "Ghar ki zimmedaariyon aur naukri ke beech"),
 (51.18, 53.08, "apne sawaalon ke liye samay nikaalna padta tha"),
 (53.40, 56.04, "Din bhar kaam karke apna sapna zinda rakhne wale"),
 (56.04, 56.98, "ye zindagi samjhenge"),
 (56.98, 60.20, "Phir aaya 1905. Umar chhabbees saal"),
 (60.20, 62.62, "Kuch mahinon mein chaar landmark papers"),
 (62.62, 64.20, "Relativity ne bataya"),
 (64.58, 66.88, "poore universe ki ek master clock nahi hai"),
 (67.20, 68.66, "Motion aur gravity ke kaaran"),
 (68.66, 71.44, "alag clocks alag elapsed time maap sakti hain"),
 (71.44, 73.20, "Ye sirf textbook ki baat nahi"),
 (73.20, 75.30, "Tumhare phone ka GPS bhi relativity ki"),
 (75.30, 76.56, "corrections istemaal karta hai"),
 (76.64, 78.98, "Imagine karo tum India Gate par khade ho"),
 (79.38, 82.00, "lekin location pin Connaught Place ki taraf bhatak rahi ho"),
 (82.40, 84.40, "Ye jagahon wala example samjhaane ke liye hai"),
 (84.40, 87.66, "Asal mein corrections hata dein toh positioning errors"),
 (87.66, 90.18, "lagbhag das kilometre roz ki dar se badh sakte hain"),
 (90.60, 92.92, "Aur E equals MC squared ne bataya"),
 (93.36, 96.50, "thode se mass ke baraabar bhi kitni vishaal energy hoti hai"),
 (96.50, 100.50, "Aaj New York State ki bijli ka ek hissa nuclear plants se aata hai"),
 (100.92, 104.08, "Is low-carbon bijli ke peeche nuclear energy ka hisaab"),
 (104.24, 105.50, "yahi equation samjhaata hai"),
 (106.12, 109.14, "Baad mein nuclear fission aur chain reaction ki discoveries se"),
 (109.30, 113.00, "bijli bhi bani aur atomic bombs bhi. Lekin Einstein ne bomb nahi banaya"),
 (113.10, 115.90, "Ab lauto unki gravity wali khoj par"),
 (115.90, 118.88, "Einstein ne prediction ki thi ki suraj ke paas guzarti"),
 (118.88, 120.26, "starlight ka raasta mudega"),
 (120.26, 125.85, "1914 mein astronomer Erwin Freundlich apni team aur telescopes lekar Crimea pahunche"),
 (126.16, 133.35, "Suryagrahan ke dauraan tasveeren kheenchkar is prediction ko jaanchna tha"),
 (133.68, 140.40, "Lekin pehla World War shuru ho gaya aur Russian army ne German astronomers ko giraftaar kar liya"),
 (140.62, 144.10, "Aasmaan mein saboot khojne wale zameen par kaidi ban gaye"),
 (144.10, 146.84, "Lekin twist ye tha ki Einstein ki us waqt ki"),
 (146.84, 148.14, "calculation mein bhi kami thi"),
 (148.14, 149.70, "Agar tasveeren mil jaatin"),
 (149.70, 151.72, "toh kya unki prediction par sawaal uthta?"),
 (151.72, 153.14, "Aur saalon baad"),
 (153.14, 155.86, "doosre World War ki shuruaat ke aaspaas"),
 (155.86, 158.78, "President Roosevelt tak unki ek aur chitthi pahunchi"),
 (158.84, 161.28, "Usmein aise hathiyaar ki chetavani thi"),
 (161.28, 165.50, "jo ek dhamaake mein bandargah aur aaspaas ka ilaaka tabaah kar sakta tha"),
 (166.18, 171.00, "Woh kis khatre se dar rahe the? Aur kis tasveer ne duniya ko unka naam yaad kara diya?"),
 (172.10, 173.96, "Doosre aur antim part mein"),
 (173.96, 177.04, "aage ki kahani ke liye follow kar lijiye aur ye reel save kar lijiye"),
]
HOT = ('degree', 'package', 'celebrate', 'doubt', 'einstein', 'rejection', 'genius', 'patent', 'papers', 'time', 'roshni',
       'mileva', 'sapna', '1905', 'universe', 'clock', 'gps', 'india', 'pin', 'kilometre', 'energy', 'mc', 'squared',
       'bijli', 'nuclear', 'fission', 'bomb', 'gravity', 'suraj', 'starlight', 'freundlich', 'crimea', 'suryagrahan',
       'tasveer', 'war', 'giraftaar', 'kaidi', 'twist', 'calculation', 'roosevelt', 'chitthi', 'hathiyaar', 'bandargah',
       'follow', 'save', 'naukri', 'shaadi', 'relativity', '20-25', 'hazaar', 'chhabbees', 'chaar', 'das', 'khatre')


def build_words():
    try:
        wj = json.load(open('/home/claude/ein/w.json')); ww = [w for s in wj for w in s['words']]
    except Exception:
        ww = []
    out = []
    for c0, c1, line in CAP:
        toks = line.split()
        wt = [w for w in ww if c0 - 0.1 <= w[0] < c1]
        a = wt[0][0] if wt else c0; b = min(c1, wt[-1][1]) if wt else c1
        a = max(c0, min(a, c0 + 0.4)); b = max(a + 0.3 * len(toks), b) if b - a < 0.15 * len(toks) else b
        wts = np.array([len(t) + 2 for t in toks], float); cs = np.concatenate([[0], np.cumsum(wts)[:-1]]) / wts.sum()
        out.append((c0, c1, toks, list(a + cs * (b - a))))
    return out


WORDS = build_words()

# ------------------------------------------------------------------ helpers
def ease(u): u = min(max(u, 0), 1); return 1 - (1 - u) ** 3
def eio(u): u = min(max(u, 0), 1); return u * u * (3 - 2 * u)
def back(u, s=1.9):
    u = min(max(u, 0), 1); return 1 + (s + 1) * (u - 1) ** 3 + s * (u - 1) ** 2


_fc = {}
def font(p, s):
    if (p, s) not in _fc: _fc[(p, s)] = ImageFont.truetype(p, s)
    return _fc[(p, s)]


_tc = {}
def tmask(s, fp, size, shear=0.0, track=0):
    k = (s, fp, size, shear, track)
    if k in _tc: return _tc[k]
    f = font(fp, size)
    if track:
        ws = [f.getlength(c) + track for c in s]; tw = int(sum(ws)) + 40; bb = f.getbbox('Hg')
        hh = bb[3] - bb[1] + 60; m = Image.new('L', (tw, hh), 0); dr = ImageDraw.Draw(m); x = 20
        for c, w in zip(s, ws): dr.text((x, 30 - bb[1]), c, font=f, fill=255); x += w
    else:
        bb = f.getbbox(s); w, hh = bb[2] - bb[0] + 40, bb[3] - bb[1] + 40
        m = Image.new('L', (w, hh), 0); ImageDraw.Draw(m).text((20 - bb[0], 20 - bb[1]), s, font=f, fill=255)
    if shear:
        w, hh = m.size; ex = int(hh * shear)
        m = m.transform((w + ex, hh), Image.AFFINE, (1, shear, -shear * hh, 0, 1, 0), Image.BICUBIC)
    a = np.asarray(m).astype(np.float32) / 255; _tc[k] = a; return a


def blend(fr, rgb, a, x, y):
    """composite premult rgb/alpha sprite with top-left at x,y"""
    h, w = a.shape[:2]; x, y = int(round(x)), int(round(y))
    x0, y0, x1, y1 = max(x, 0), max(y, 0), min(x + w, W), min(y + h, H)
    if x1 <= x0 or y1 <= y0: return
    aa = a[y0 - y:y1 - y, x0 - x:x1 - x]
    if aa.ndim == 2: aa = aa[..., None]
    reg = fr[y0:y1, x0:x1]
    if rgb is None: return
    if isinstance(rgb, tuple): reg[:] = reg * (1 - aa) + np.array(rgb, np.float32) * aa
    else: reg[:] = reg * (1 - aa) + rgb[y0 - y:y1 - y, x0 - x:x1 - x]


def put(fr, a, col, cx, cy, alpha=1.0, scale=1.0, reveal=1.0):
    if alpha <= 0.01: return
    if scale != 1.0 and scale > 0.05: a = cv2.resize(a, None, fx=scale, fy=scale, interpolation=cv2.INTER_LINEAR)
    h, w = a.shape
    if reveal < 1: a = a * np.clip((reveal * w * 1.3 - np.arange(w)) / (w * 0.3), 0, 1)[None, :]
    blend(fr, col, a * alpha, cx - w / 2, cy - h / 2)


# ------------------------------------------------------------------ sprites
_sp = {}
def sprite(name, h):
    k = (name, h)
    if k in _sp: return _sp[k]
    im = cv2.imread(CZ + name + '.png', cv2.IMREAD_UNCHANGED)
    a = im[..., 3]; ys, xs = np.where(a > 8); im = im[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    s = h / im.shape[0]; im = cv2.resize(im, None, fx=s, fy=s, interpolation=cv2.INTER_AREA)
    rgb = cv2.cvtColor(im[..., :3], cv2.COLOR_BGR2RGB).astype(np.float32); a = im[..., 3].astype(np.float32) / 255
    # light sharpen + warm rim from the edge of the matte
    bl = cv2.GaussianBlur(rgb, (0, 0), 1.2); rgb = np.clip(rgb + 0.5 * (rgb - bl), 0, 255)
    pad = 60; P = lambda z: cv2.copyMakeBorder(z, pad, pad, pad, pad, cv2.BORDER_CONSTANT, value=0)
    rgb, a = P(rgb), P(a)
    edge = np.clip(a - cv2.erode(a, np.ones((5, 5), np.uint8)), 0, 1)
    rgb = rgb * (1 - edge[..., None] * 0.25) + edge[..., None] * 0.25 * np.array([255, 240, 220], np.float32)
    shadow = cv2.GaussianBlur(a, (0, 0), 16)
    _sp[k] = (rgb * a[..., None], a, shadow)
    if len(_sp) > 40: _sp.pop(next(iter(_sp)))
    return _sp[k]


def draw_el(fr, el, t, ts, k):
    name, x, y, h, d, an = el; u = t - ts - d
    if u < 0: return
    pre, a, sh = sprite(name, h)
    sc = 1.0; dx = dy = 0.0; rot = 0.0; al = 1.0
    i = ease(u / 0.55); ib = back(u / 0.6)
    if an == 'pop': sc = 0.4 + 0.6 * ib; al = min(1, u / 0.15)
    elif an == 'up': dy = (1 - ib) * 700; al = min(1, u / 0.2)
    elif an == 'down': dy = -(1 - ib) * 700; al = min(1, u / 0.2)
    elif an == 'left': dx = -(1 - i) * 600; al = min(1, u / 0.25)
    elif an == 'right': dx = (1 - i) * 600; al = min(1, u / 0.25)
    elif an == 'fade': al = ease(u / 0.6); sc = 0.9 + 0.1 * i
    elif an == 'fly': dx = (1 - i) * 700; dy = (1 - i) * 500; rot = (1 - i) * -25; al = min(1, u / 0.2)
    elif an == 'run': dx = -260 + 520 * eio(u / 2.2); dy = -abs(math.sin(u * 9)) * 22
    elif an == 'walk': dy = -abs(math.sin(u * 4)) * 8; sc = 1.0 - 0.18 * ease(u / 4.5)
    elif an == 'swing': rot = 9 * math.sin(u * 2.4) * math.exp(-u * 0.2); al = min(1, u / 0.2)
    elif an == 'orbit': dx = 60 * math.sin(u * 0.9); dy = 30 * math.cos(u * 0.9); rot = 6 * math.sin(u * 0.9); al = min(1, u / 0.3)
    elif an == 'spin': rot = u * 8; sc = 0.6 + 0.4 * ib; al = min(1, u / 0.2)
    # idle float + slow push
    dy += 8 * math.sin(t * 1.6 + x * 0.01); sc *= 1 + 0.035 * min(u, 4) / 4
    if al <= 0.01 or sc <= 0.05: return
    hh, ww = a.shape
    if abs(rot) > 0.2 or abs(sc - 1) > 0.005:
        M = cv2.getRotationMatrix2D((ww / 2, hh / 2), rot, sc)
        cs, sn = abs(M[0, 0]), abs(M[0, 1]); nw, nh = int(hh * sn + ww * cs) + 2, int(hh * cs + ww * sn) + 2
        M[0, 2] += nw / 2 - ww / 2; M[1, 2] += nh / 2 - hh / 2
        pre = cv2.warpAffine(pre, M, (nw, nh)); a = cv2.warpAffine(a, M, (nw, nh)); sh = cv2.warpAffine(sh, M, (nw, nh)); hh, ww = nh, nw
    X = x + dx - ww / 2; Y = y + dy - hh / 2
    blend(fr, (30, 26, 80), sh * 0.30 * al, X + 14, Y + 30)
    blend(fr, pre * al, a * al, X, Y)


# ------------------------------------------------------------------ backgrounds
yy_, xx_ = np.mgrid[0:H, 0:W].astype(np.float32)
GRAD = np.stack([np.interp(yy_[:, :1], [0, H], [c0, c1]) for c0, c1 in [(214, 132), (220, 142), (250, 222)]], -1)
GRAD = np.repeat(GRAD, W, 1).astype(np.float32)
_blob = np.exp(-((np.mgrid[-600:600, -600:600] ** 2).sum(0)) / (2 * 260 ** 2)).astype(np.float32)[..., None]
STAGE_RING = None


def stage(t, dark=False, k=0):
    fr = GRAD.copy()
    for i, (cx, cy, col) in enumerate([(0.25, 0.3, (255, 235, 245)), (0.8, 0.7, (200, 210, 255))]):
        X = int(W * cx + 160 * math.sin(t * 0.21 + i * 2)) - 600; Y = int(H * cy + 200 * math.cos(t * 0.17 + i)) - 600
        blend(fr, col, _blob[..., 0] * 0.55, X, Y)
    # floor glow under the subject
    g = np.exp(-(((xx_ - W / 2) / 420) ** 2 + ((yy_ - 1540) / 90) ** 2))[..., None] if False else None
    if dark: fr = fr * 0.62 + np.array([10, 8, 40], np.float32)
    return fr


_ic = {}
def painting(n):
    if n not in _ic:
        if len(_ic) > 4: _ic.pop(next(iter(_ic)))
        im = cv2.cvtColor(cv2.imread(IM + f'img{n:02d}.png'), cv2.COLOR_BGR2RGB).astype(np.float32)
        _ic[n] = cv2.resize(im, (W, H), interpolation=cv2.INTER_AREA)
    return _ic[n]


def kenburns(n, u, k):
    im = painting(n); z = 1.04 + 0.10 * eio(u); dx = 30 * math.sin(k * 1.7) * u; dy = -25 * u
    M = np.float32([[z, 0, W / 2 - W / 2 * z + dx], [0, z, H / 2 - H / 2 * z + dy]])
    return cv2.warpAffine(im, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)


# ------------------------------------------------------------------ titles
def fitbig(s, maxw):
    size = 190
    while size > 80:
        a = tmask(s, ANTON, size, 0, 4)
        if a.shape[1] <= maxw: return a
        size -= 10
    return tmask(s, ANTON, size, 0, 4)


_gl = {}
def glow_of(a):
    k = id(a)
    if k not in _gl: _gl[k] = np.clip(cv2.GaussianBlur(cv2.dilate(a, np.ones((9, 9), np.uint8)), (0, 0), 14) * 1.4, 0, 1)
    return _gl[k]


def titles(fr, t, k):
    ts, bg, els, sm, big = SC[k][:5]; u = t - ts; t1 = CUTS[k + 1]
    out = 1 - ease((t - (t1 - 0.2)) / 0.2)
    a = tmask(sm, SERIF, 64); put(fr, glow_of(a), WHITE, W / 2, 200, 0.55 * ease(u / 0.3) * out)
    put(fr, a, (60, 66, 150), W / 2, 200, ease((u - 0.05) / 0.3) * out, 1.0, min(1, (u - 0.05) / 0.4))
    words = big.split(' ')
    lines = [big] if (len(big) <= 11 or len(words) == 1) else [' '.join(words[:(len(words) + 1) // 2]), ' '.join(words[(len(words) + 1) // 2:])]
    for j, l in enumerate(lines):
        bm = fitbig(l, W * 0.88); tt = u - 0.15 - j * 0.12
        if tt < 0: continue
        sc = 1.0 + 0.35 * (1 - back(tt / 0.42)); cy = 335 + j * 175
        put(fr, glow_of(bm), WHITE, W / 2, cy, 0.6 * ease(tt / 0.25) * out, sc)
        put(fr, bm, NAVY, W / 2, cy, ease(tt / 0.15) * out, sc)
        if j == len(lines) - 1:
            # gold underline swipe
            uw = bm.shape[1] * 0.55 * ease((tt - 0.25) / 0.35)
            if uw > 2:
                y0 = int(cy + bm.shape[0] / 2 - 18); cv2.rectangle(fr, (int(W / 2 - uw / 2), y0), (int(W / 2 + uw / 2), y0 + 10), (*GOLD,), -1, cv2.LINE_AA) if False else None
                fr[y0:y0 + 10, int(W / 2 - uw / 2):int(W / 2 + uw / 2)] = fr[y0:y0 + 10, int(W / 2 - uw / 2):int(W / 2 + uw / 2)] * (1 - out) + np.array(GOLD, np.float32) * out


# ------------------------------------------------------------------ overlays
def mglow(fr, cx, cy, r, col, amt):
    X, Y = int(cx - 600), int(cy - 600); s = r / 260
    b = cv2.resize(_blob[..., 0], None, fx=s, fy=s); blend_add(fr, b * amt, col, cx - b.shape[1] / 2, cy - b.shape[0] / 2)


def blend_add(fr, a, col, x, y):
    h, w = a.shape; x, y = int(x), int(y)
    x0, y0, x1, y1 = max(x, 0), max(y, 0), min(x + w, W), min(y + h, H)
    if x1 <= x0 or y1 <= y0: return
    fr[y0:y1, x0:x1] += a[y0 - y:y1 - y, x0 - x:x1 - x, None] * np.array(col, np.float32)


def pill(fr, text, cx, cy, alpha, bg=NAVY, fg=WHITE, size=34):
    m = tmask(text, ARCH, size); h, w = m.shape; pw, ph = w + 40, h + 16
    p = np.zeros((ph, pw), np.float32); cv2.rectangle(p, (ph // 2, 0), (pw - ph // 2, ph - 1), 1, -1)
    cv2.circle(p, (ph // 2, ph // 2), ph // 2, 1, -1); cv2.circle(p, (pw - ph // 2 - 1, ph // 2), ph // 2, 1, -1)
    p = cv2.GaussianBlur(p, (3, 3), 0)
    put(fr, p, bg, cx, cy, alpha * 0.95); put(fr, m, fg, cx, cy, alpha)


def overlay(fr, t, k):
    ts = SC[k][0]; ov = SC[k][6]; u = t - ts
    if not ov: return
    for o in ov.split('|'):
        if o.startswith('chapter:'):
            a = ease(u / 0.3) * (1 - ease((u - 2.6) / 0.4))
            if a > 0: pill(fr, o.split(':', 1)[1], W / 2, 108, a, size=32)
        elif o == 'salary':
            v = int(25000 * ease((u - 1.4) / 1.8))
            if u > 1.3: pill(fr, f'Rs {v:,} / month', 820, 1470, ease((u - 1.3) / 0.2), RED, WHITE, 40)
        elif o == 'glow':
            mglow(fr, W / 2, 1040, 520 + 40 * math.sin(u * 3), (255, 200, 120), 0.35)
        elif o == 'beam':
            p = (u % 1.6) / 1.6; x = -400 + (W + 800) * ease(p); y = 1000
            lay = np.zeros((H // 4, W // 4), np.float32)
            cv2.line(lay, (int((x - 700) / 4), int((y + 40) / 4)), (int(x / 4), int(y / 4)), 1.0, 3, cv2.LINE_AA)
            lay = cv2.resize(cv2.GaussianBlur(lay, (0, 0), 2) * 1.6 + lay, (W, H))
            fr += lay[..., None] * np.array([255, 215, 140], np.float32)
        elif o == 'year':
            v = int(1880 + 25 * ease((u - 0.1) / 1.2)); m = tmask(str(v), ANTON, 300, 0, 8)
            a = ease(u / 0.25) * (1 - ease((u - 1.35) / 0.25))
            put(fr, glow_of(m), (255, 220, 150), W / 2, 1050, a * 0.8); put(fr, m, (200, 140, 40), W / 2, 1050, a)
        elif o == 'tick':
            cx, cy, r = W / 2, 1060, 500; sec = int(u * 4)
            lay = np.zeros((H // 2, W // 2), np.float32)
            for i in range(60):
                if i > sec % 61: break
                ang = math.radians(i * 6 - 90); L = 26 if i % 5 == 0 else 12
                p0 = (int((cx + (r - L) * math.cos(ang)) / 2), int((cy + (r - L) * math.sin(ang)) / 2)); p1 = (int((cx + r * math.cos(ang)) / 2), int((cy + r * math.sin(ang)) / 2))
                cv2.line(lay, p0, p1, 1.0, 2, cv2.LINE_AA)
            lay = cv2.resize(lay, (W, H))[..., None]; fr[:] = fr * (1 - lay * 0.7) + lay * 0.7 * 255
        elif o == 'pin':
            p = ease((u - 0.5) / 2.5); sx, sy = W * 0.45, H * 0.45; ex, ey = W * 0.78, H * 0.36
            for i in range(int(p * 26)):
                q = i / 26; cv2.circle(fr, (int(sx + (ex - sx) * q), int(sy + (ey - sy) * q)), 7, (230, 50, 70), -1, cv2.LINE_AA)
            pre, a, sh = sprite('c29_pin', 170); X = sx + (ex - sx) * p; Y = sy + (ey - sy) * p
            blend(fr, pre, a, X - a.shape[1] / 2, Y - a.shape[0] + 40)
        elif o == 'km':
            v = 10 * ease((u - 0.8) / 4.0)
            if u > 0.7: pill(fr, f'+ {v:.1f} km error / din', W / 2, 1480, ease((u - 0.7) / 0.2), RED, WHITE, 44)
        elif o == 'energy':
            for j in range(3):
                p = ((u + j * 0.5) % 1.5) / 1.5; r = int(60 + 650 * ease(p))
                lay = np.zeros((H // 2, W // 2), np.float32); cv2.circle(lay, (W // 4, 1040 // 2), r // 2, 1.0, 3, cv2.LINE_AA)
                lay = cv2.resize(cv2.GaussianBlur(lay, (0, 0), 3), (W, H)) * (1 - p) * 1.8
                fr += lay[..., None] * np.array([255, 205, 120], np.float32)
        elif o == 'curve':
            p = ease((u - 0.3) / 1.8); lay = np.zeros((H // 2, W // 2), np.float32)
            pts = []
            for i in range(int(p * 60) + 1):
                q = i / 60; x = -40 + q * (W + 80); y = 720 + 160 * math.exp(-((x - W / 2) / 300) ** 2) + q * 40
                pts.append((int(x / 2), int(y / 2)))
            if len(pts) > 1:
                cv2.polylines(lay, [np.array(pts)], False, 1.0, 3, cv2.LINE_AA)
                for x in range(0, len(pts), 6): pass
                lay = cv2.resize(cv2.GaussianBlur(lay, (0, 0), 2) * 1.5 + lay, (W, H))
                fr += lay[..., None] * np.array([255, 245, 200], np.float32)
                hx, hy = pts[-1]; mglow(fr, hx * 2, hy * 2, 60, (255, 250, 220), 1.0)
        elif o == 'corona':
            pul = 0.5 + 0.5 * math.sin(u * 3.2); mglow(fr, W / 2, 1040, 560, (230, 235, 255), 0.25 + 0.25 * pul)
        elif o == 'stamp':
            if u > 0.9:
                m = tmask('ARRESTED · 1914', ANTON, 92, 0, 4); s = 1 + 1.8 * max(0, 1 - (u - 0.9) / 0.12)
                R = cv2.getRotationMatrix2D((m.shape[1] / 2, m.shape[0] / 2), -9, 1); mr = cv2.warpAffine(m, R, (m.shape[1], m.shape[0]))
                hh, ww = mr.shape; box = np.zeros_like(mr); cv2.rectangle(box, (14, 14), (ww - 14, hh - 14), 1, 8)
                box = cv2.warpAffine(box, R, (ww, hh))
                put(fr, np.clip(mr + box, 0, 1), (200, 30, 45), W / 2, 1180, min(1, (u - 0.9) / 0.06) * 0.92, s)
        elif o == 'type':
            s = 'August 2, 1939'; n = int(max(0, u - 0.6) / 0.07)
            if n > 0: pill(fr, s[:min(n, len(s))] + ('|' if n < len(s) and int(u * 6) % 2 else ''), W / 2, 1480, 1.0, WHITE, NAVY, 46)
        elif o == 'blast':
            if u > 0.6:
                p = min(1, (u - 0.6) / 1.4); mglow(fr, W / 2, 1060, 300 + 700 * ease(p), (255, 170, 80), 0.9 * (1 - p) ** 1.5)
                fr += 255 * max(0, 1 - (u - 0.6) / 0.15) * 0.6
        elif o == 'follow':
            if u > 1.2:
                a = ease((u - 1.2) / 0.3); s = 1 + 0.06 * math.sin(u * 6)
                pill(fr, '+  FOLLOW', W / 2 - 170, 1480, a, (0, 110, 230), WHITE, 46)
                pill(fr, 'SAVE', W / 2 + 200, 1480, ease((u - 1.6) / 0.3), WHITE, NAVY, 46)


# ------------------------------------------------------------------ scene render
def scene(k, t):
    ts, bg, els = SC[k][:3]; d = CUTS[k + 1] - ts; u = (t - ts) / d
    if isinstance(bg, tuple) and bg[0] == 'i': fr = kenburns(bg[1], u, k)
    else: fr = stage(t, isinstance(bg, tuple) and bg[1] == 'dark', k)
    ov = SC[k][6] or ''
    if 'corona' in ov or 'glow' in ov: overlay(fr, t, k)
    for el in els: draw_el(fr, el, t, ts, k)
    if not ('corona' in ov or 'glow' in ov): overlay(fr, t, k)
    titles(fr, t, k)
    return fr


def zoomf(img, z, blur=0):
    M = np.float32([[z, 0, W / 2 - W / 2 * z], [0, z, H / 2 - H / 2 * z]])
    o = cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    if blur > 2: o = cv2.resize(cv2.GaussianBlur(cv2.resize(o, (W // 4, H // 4)), (0, 0), blur / 4), (W, H))
    return o


def base(t):
    k = max(i for i, c in enumerate(CUTS[:-1]) if c <= t)
    if k + 1 < len(SC) and t > CUTS[k + 1] - TD: A, B = k, k + 1
    elif k > 0 and t < CUTS[k] + TD: A, B = k - 1, k
    else: return scene(k, t)
    b = CUTS[B]; p = (t - (b - TD)) / (2 * TD); tr = SC[B][5]
    if tr == 'flash':
        img = scene(A if t < b else B, t); f = math.exp(-abs(t - b) / 0.07)
        pos = (p * 1.6 - 0.3) * (W + H); band = np.exp(-(((xx_ + yy_ * 0.6) - pos) / 160) ** 2)[..., None]
        return img + band * 80 * np.array([1, 0.9, 0.7], np.float32) + f * 60
    a = scene(A, t); bb = scene(B, t); e = eio(p)
    if tr == 'zoom':
        if p < 0.5: return zoomf(a, 1 + 0.6 * (p * 2) ** 2, 40 * p * 2) * (1 - 0.25 * p * 2) + 255 * 0.25 * p * 2
        q = (p - 0.5) * 2; return zoomf(bb, 0.82 + 0.18 * ease(q), 40 * (1 - q))
    if tr == 'whip':
        off = int(e * W); out = np.empty_like(a)
        if off < W: out[:, :W - off] = a[:, off:]
        if off > 0: out[:, W - off:] = bb[:, :off]
        kk = int(160 * math.sin(math.pi * p)) // 4 * 2 + 1
        if kk > 3: out = cv2.resize(cv2.blur(cv2.resize(out, (W // 2, H // 2)), (kk // 2 | 1, 1)), (W, H))
        return out
    if tr == 'up':
        off = int(e * H); out = np.empty_like(a)
        if off < H: out[:H - off] = a[off:]
        if off > 0: out[H - off:] = bb[:off]
        kk = int(160 * math.sin(math.pi * p)) // 4 * 2 + 1
        if kk > 3: out = cv2.resize(cv2.blur(cv2.resize(out, (W // 2, H // 2)), (1, kk // 2 | 1)), (W, H))
        return out
    if tr == 'iris':
        r = ease(p) * 1150; d = np.sqrt((xx_ - W / 2) ** 2 + (yy_ - H * 0.55) ** 2)
        m = np.clip((r - d) / 25, 0, 1)[..., None]; ring = np.exp(-((d - r) / 9) ** 2)[..., None]
        return a * (1 - m) + bb * m + ring * 200 * np.array([1, 0.92, 0.75], np.float32)
    if tr == 'blur':
        bl = 50 * math.sin(math.pi * p)
        mix = a * (1 - e) + bb * e
        return zoomf(mix, 1 + 0.04 * math.sin(math.pi * p), bl)
    return a * (1 - e) + bb * e


# ------------------------------------------------------------------ finishing
VIG = (1 - 0.32 * np.clip(np.sqrt(((xx_ - W / 2) / (W / 2)) ** 2 + ((yy_ - H / 2) / (H / 2)) ** 2) - 0.5, 0, 1) ** 1.5)[..., None]
GR = np.random.default_rng(3).normal(0, 1, (H // 2, W // 2)).astype(np.float32)
R = np.random.default_rng(8); NP = 55
PX, PY, PV, PS, PP = R.uniform(0, W, NP), R.uniform(0, H, NP), R.uniform(10, 35, NP), R.uniform(1.0, 3.2, NP), R.uniform(0, 6.3, NP)


def finish(fr, t):
    lay = np.zeros((H // 2, W // 2), np.float32)
    for i in range(NP):
        y = (PY[i] - PV[i] * t) % H; x = (PX[i] + 16 * math.sin(t * 0.5 + PP[i])) % W
        cv2.circle(lay, (int(x / 2), int(y / 2)), max(1, int(PS[i])), 0.5 + 0.5 * math.sin(t * 1.3 + PP[i]), -1, cv2.LINE_AA)
    lay = cv2.resize(cv2.GaussianBlur(lay, (0, 0), 1.3), (W, H))[..., None]
    fr = fr + lay * np.array([255, 245, 230], np.float32) * 0.32
    fr = fr * VIG
    o = int(t * 997) % 300; fr += cv2.resize(np.roll(GR, o, 0), (W, H), interpolation=cv2.INTER_NEAREST)[..., None] * 3.0
    return fr


def rrect(w, h, r):
    m = np.zeros((h, w), np.float32); cv2.rectangle(m, (r, 0), (w - r, h), 1, -1); cv2.rectangle(m, (0, r), (w, h - r), 1, -1)
    for cx, cy in [(r, r), (w - r - 1, r), (r, h - r - 1), (w - r - 1, h - r - 1)]: cv2.circle(m, (cx, cy), r, 1, -1, cv2.LINE_AA)
    return m


def captions(fr, t):
    for c0, c1, toks, ts in WORDS:
        if not (c0 <= t < c1 + 0.2): continue
        idx = max([i for i, x in enumerate(ts) if x <= t] or [0]); st = (idx // 4) * 4; chunk = toks[st:st + 4]
        size = 64; f = font(ARCH, size); sp = f.getlength(' ')
        tot = sum(f.getlength(w) for w in chunk) + sp * 1.5 * (len(chunk) - 1)
        if tot > W * 0.84: size = 52; f = font(ARCH, size); sp = f.getlength(' '); tot = sum(f.getlength(w) for w in chunk) + sp * 1.5 * (len(chunk) - 1)
        while tot > W * 0.84 and size > 36:
            size -= 6; f = font(ARCH, size); sp = f.getlength(' '); tot = sum(f.getlength(w) for w in chunk) + sp * 1.5 * (len(chunk) - 1)
        out = 1 - ease((t - c1) / 0.2); cin = ease((t - c0) / 0.2)
        y = 1665; bw, bh = int(tot + 80), int(size * 1.75); bx, by = int((W - bw) / 2), int(y - bh / 2)
        # frosted glass card
        reg = fr[by:by + bh, bx:bx + bw]
        if reg.size:
            sm = cv2.resize(cv2.GaussianBlur(cv2.resize(reg, (max(1, bw // 6), max(1, bh // 6))), (0, 0), 2), (bw, bh))
            m = rrect(bw, bh, bh // 2)[..., None] * out * cin
            glass = sm * 0.55 + np.array([255, 255, 255], np.float32) * 0.45
            reg[:] = reg * (1 - m) + glass * m
            edge = np.clip(rrect(bw, bh, bh // 2) - cv2.erode(rrect(bw, bh, bh // 2), np.ones((5, 5), np.uint8)), 0, 1)[..., None]
            reg[:] = reg * (1 - edge * 0.6 * out * cin) + 255 * edge * 0.6 * out * cin
        x = (W - tot) / 2
        for j, w in enumerate(chunk):
            gi = st + j; ww = f.getlength(w)
            if ts[gi] > t + 0.02:
                put(fr, tmask(w, ARCH, size), NAVY, x + ww / 2, y, 0.35 * out * cin)
            else:
                key = ''.join(ch for ch in w.lower() if ch.isalnum() or ch == '-')
                active = gi == idx; hot = any(key.startswith(h) for h in HOT)
                pp = back((t - ts[gi]) / 0.2)
                a = tmask(w, ARCH, size); cy = y - (1 - min(pp, 1)) * 12
                if active:
                    hw, hh = int(ww + 26), int(size * 1.25); hp = rrect(hw, hh, 18)
                    put(fr, hp, GOLD if hot else NAVY, x + ww / 2, y + 2, out * cin)
                    put(fr, a, NAVY if hot else WHITE, x + ww / 2, cy, out * cin, 1.0 + 0.1 * (1 - min(1, (t - ts[gi]) / 0.25)))
                else:
                    put(fr, a, (200, 120, 20) if hot else NAVY, x + ww / 2, cy, out * cin)
            x += ww + sp * 1.5
        break


def frame(t):
    fr = base(t); fr = finish(fr, t); captions(fr, t)
    if t < 0.35: fr = fr * (t / 0.35)
    if t > T - 0.6: fr = fr * max(0, (T - t) / 0.6)
    return np.clip(fr, 0, 255).astype(np.uint8)


# ------------------------------------------------------------------ audio
def audio(out):
    SR = 44100
    r = subprocess.run(['ffmpeg', '-v', 'error', '-i', '/home/claude/ein/vo.wav', '-ac', '1', '-ar', str(SR), '-f', 'f32le', '-'], capture_output=True).stdout
    vo = np.frombuffer(r, np.float32).copy(); N = int(T * SR); vo = np.pad(vo, (0, max(0, N - len(vo))))[:N]; vo = vo / np.abs(vo).max() * 0.9
    mix = np.zeros(N, np.float32); rng = np.random.default_rng(2)
    def add(t, s, g):
        i = int(t * SR); e = min(N, i + len(s))
        if 0 <= i < N: mix[i:e] += s[:e - i] * g
    def whoosh(d=0.45):
        n = int(SR * d); x = rng.normal(0, 1, n).astype(np.float32)
        # band-passed noise sweep via FFT shaping
        X = np.fft.rfft(x); f = np.fft.rfftfreq(n, 1 / SR); X *= np.exp(-((np.log(f + 1) - 7.2) / 0.9) ** 2); y = np.fft.irfft(X, n)
        y = y / np.abs(y).max(); return y * np.sin(np.pi * np.arange(n) / n) ** 2
    def hit():
        n = int(SR * 0.7); x = np.arange(n) / SR; return np.sin(2 * np.pi * (48 + 70 * np.exp(-x * 25)) * x) * np.exp(-x * 5)
    def pop():
        n = int(SR * 0.08); x = np.arange(n) / SR; return np.sin(2 * np.pi * (900 - 4000 * x) * x) * np.exp(-x * 60)
    def tick():
        n = int(SR * 0.03); x = np.arange(n) / SR; return np.sin(2 * np.pi * 2600 * x) * np.exp(-x * 180)
    def riser(d=1.4):
        n = int(SR * d); x = np.arange(n) / SR; f = 180 + 700 * (x / d) ** 2
        return np.sin(2 * np.pi * np.cumsum(f) / SR) * (x / d) ** 2 * 0.5
    wh = whoosh()
    for s in SC[1:]:
        tr = s[5]
        if tr in ('whip', 'up', 'zoom'): add(s[0] - 0.22, wh, 0.07)
        if tr == 'flash': add(s[0], hit(), 0.14)
        if tr == 'iris': add(s[0] - 0.22, wh, 0.05)
        for el in s[2]:
            if el[4] > 0.3: add(s[0] + el[4], pop(), 0.05)
    for tt in (18.56, 56.98, 113.10, 151.72): add(tt - 1.4, riser(), 0.05)
    for i, s in enumerate(SC):
        if s[6] == 'tick':
            x = s[0]
            while x < CUTS[i + 1]: add(x, tick(), 0.05); x += 0.25
        if s[6] == 'blast': add(s[0] + 0.6, hit(), 0.2)
        if s[6] and 'type' in s[6]:
            for j in range(14): add(s[0] + 0.6 + j * 0.07, tick(), 0.04)
    # warm pad
    tt = np.arange(N) / SR; pad = np.zeros(N, np.float32)
    chords = [(110, 164.8, 220, 277.2), (98, 146.8, 196, 246.9), (87.3, 130.8, 174.6, 220), (98, 146.8, 196, 293.7)]
    for i, t0 in enumerate(np.arange(0, T, 6.0)):
        s0 = int(t0 * SR); e = min(N, int((t0 + 7) * SR)); x = np.arange(e - s0) / SR; env = np.minimum(1, x / 2) * np.minimum(1, (7 - x) / 2)
        for f in chords[i % 4]: pad[s0:e] += np.sin(2 * np.pi * f * x) * env
    pad *= 0.009
    o = vo + mix + pad; o = o / np.abs(o).max() * 0.95
    st = (np.stack([o, o], 1) * 32767).astype(np.int16)
    w = wave.open(out, 'wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(st.tobytes()); w.close()


if __name__ == '__main__':
    if sys.argv[1] == 'stills':
        ts = [float(x) for x in sys.argv[2].split(',')]
        ims = [Image.fromarray(frame(t)).resize((270, 480)) for t in ts]
        cols = min(8, len(ims)); M = Image.new('RGB', (cols * 270, ((len(ims) + cols - 1) // cols) * 480))
        for i, im in enumerate(ims): M.paste(im, ((i % cols) * 270, (i // cols) * 480))
        M.save(sys.argv[3] if len(sys.argv) > 3 else '/home/claude/ein/prev.png')
    elif sys.argv[1] == 'one':
        Image.fromarray(frame(float(sys.argv[2]))).save('/home/claude/ein/one.png')
    else:
        from multiprocessing import Pool
        out = sys.argv[1]; audio(out + '.wav')
        enc = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', '30', '-i', '-', '-i', out + '.wav',
                                '-map', '0:v', '-map', '1:a', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '18', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k', '-shortest', out], stdin=subprocess.PIPE)
        with Pool(2) as p:
            for i, b in enumerate(p.imap(frame, [i / 30 for i in range(int(T * 30))], chunksize=8)):
                enc.stdin.write(b.tobytes())
                if i % 600 == 0: print(i, flush=True)
        enc.stdin.close(); enc.wait(); print('done')
