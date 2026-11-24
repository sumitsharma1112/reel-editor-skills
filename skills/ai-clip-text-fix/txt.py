from PIL import Image, ImageDraw, ImageFont, ImageFilter
import functools, re
F='/home/claude/faridkot/fonts/'
FONTS={'head':F+'baloo-paaji-2-800-full.ttf','semi':F+'baloo-paaji-2-600-full.ttf','body':F+'mukta-mahee-700-full.ttf','anek':F+'anek-gurmukhi-800-full.ttf',
       'latin':'/home/claude/faridkot/fonts/baloo-paaji-2-800-full.ttf'}
EMOJI='/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf'
@functools.lru_cache(None)
def font(name,size): return ImageFont.truetype(FONTS[name],size,layout_engine=ImageFont.Layout.RAQM)
@functools.lru_cache(None)
def efont(): return ImageFont.truetype(EMOJI,109)
EMO=re.compile('([\U0001F000-\U0001FAFF☀-➿⭐❤][️\U0001F1E6-\U0001F1FF]*)')
@functools.lru_cache(None)
def emoji_img(ch,size):
    im=Image.new('RGBA',(160,160)); d=ImageDraw.Draw(im); d.text((10,10),ch,font=efont(),embedded_color=True)
    im=im.crop(im.getbbox()); s=size/im.height*0.95
    return im.resize((max(1,int(im.width*s)),max(1,int(im.height*s))),Image.LANCZOS)
def render(text,name,size,fill=(255,255,255,255),stroke=0,stroke_fill=(0,0,0,255),shadow=None):
    """returns RGBA image of a single line incl. emoji"""
    f=font(name,size); parts=[p for p in EMO.split(text) if p]
    asc,desc=f.getmetrics(); H=int((asc+desc)*1.15)+2*stroke
    pieces=[]
    for p in parts:
        if EMO.fullmatch(p): pieces.append(('e',emoji_img(p,int(size*0.9))))
        else:
            bb=f.getbbox(p,stroke_width=stroke); w=bb[2]-min(0,bb[0])+stroke
            pieces.append(('t',p,w))
    W=sum((x[2] if x[0]=='t' else x[1].width+int(size*0.1)) for x in pieces)+4
    im=Image.new('RGBA',(W+20,H+int(size*0.3))); d=ImageDraw.Draw(im); x=10; y=int(size*0.1)
    for pc in pieces:
        if pc[0]=='t':
            d.text((x,y),pc[1],font=f,fill=fill,stroke_width=stroke,stroke_fill=stroke_fill); x+=pc[2]
        else:
            e=pc[1]; im.alpha_composite(e,(x+int(size*0.05),y+int(asc*0.98)-e.height+int(size*0.08))); x+=e.width+int(size*0.1)
    im=im.crop(im.getbbox())
    if shadow:
        off,blur,alpha=shadow
        sh=Image.new('RGBA',(im.width+4*blur+off,im.height+4*blur+off))
        a=im.split()[3].point(lambda v:v*alpha//255)
        blk=Image.new('RGBA',im.size,(0,0,0,255)); blk.putalpha(a)
        sh.alpha_composite(blk,(2*blur+off,2*blur+off)); sh=sh.filter(ImageFilter.GaussianBlur(blur))
        sh.alpha_composite(im,(2*blur,2*blur)); im=sh
    return im
