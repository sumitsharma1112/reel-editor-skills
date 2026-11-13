# kinetic_explainer: faceless AI explainer in the 'red 3D kinetic words' style (cartoon presenter, phone screen-recording, pixel glitch, light streak, halftone transitions, soft SFX). Made with Claude, Nov 2026.
# Paths to inputs (videos, images, fonts, audio) are set near the top: edit them for a new reel.
import numpy as np, cv2, math, re, os, glob, subprocess, sys
from PIL import Image, ImageDraw, ImageFont, ImageChops, ImageFilter
W,H=1080,1920; FPS=30; T=55.5
A='/home/claude/intro/assets/'; P='/home/claude/ex/seller/imgs/'; R='/home/claude/ex/rec/'; F='/home/claude/ex/fnt/'
LAT='/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf'
_fc={}
def font(p,s):
    k=(p,s)
    if k not in _fc: _fc[k]=ImageFont.truetype(p,s)
    return _fc[k]
DEVF={'baloo':F+'baloo-2-devanagari-800-normal.ttf','kalam':F+'kalam-devanagari-700-normal.ttf'}
_tc={}
def text_img(txt,size,fill=(255,255,255),dev='baloo',stroke=0,sfill=(0,0,0),lh=1.12,align='center'):
    key=(txt,size,fill,dev,stroke,sfill,lh,align)
    if key in _tc: return _tc[key]
    lines=txt.split('\n'); fd=font(DEVF[dev],size); fl=font(LAT,int(size*0.92))
    def runs(s):
        out=[]
        for m in re.finditer(r'[ऀ-ॿ]+|[^ऀ-ॿ]+',s):
            r=m.group(0); out.append((r, fd if re.match(r'[ऀ-ॿ]',r) else fl))
        return out
    widths=[sum(f.getlength(r) for r,f in runs(l)) for l in lines]
    pad=stroke+8; cw=int(max(widths))+2*pad; step=int(size*1.55*lh/1.12)
    ch=step*len(lines)+pad*2
    im=Image.new('RGBA',(cw,ch),(0,0,0,0)); d=ImageDraw.Draw(im)
    for i,l in enumerate(lines):
        x=pad+(cw-2*pad-widths[i])/2 if align=='center' else pad
        base=pad+int(size*1.2)+i*step
        for r,f in runs(l):
            d.text((x,base),r,font=f,fill=fill,anchor='ls',stroke_width=stroke,stroke_fill=sfill)
            x+=f.getlength(r)
    _tc[key]=im; return im
_ac={}
def asset(name,scale=1.0,crop=True):
    k=(name,round(scale,3))
    if k in _ac: return _ac[k]
    im=Image.open(name).convert('RGBA')
    if crop:
        bb=im.getchannel('A').point(lambda v:255 if v>20 else 0).getbbox()
        if bb: im=im.crop(bb)
    if scale!=1.0: im=im.resize((max(1,int(im.width*scale)),max(1,int(im.height*scale))),Image.LANCZOS)
    _ac[k]=im; return im
def place(base,im,cx,cy,s=1.0,rot=0,a=1.0):
    if s<=0.01 or a<=0: return
    if s!=1.0: im=im.resize((max(1,int(im.width*s)),max(1,int(im.height*s))),Image.BILINEAR)
    if rot: im=im.rotate(rot,resample=Image.BICUBIC,expand=True)
    if a<1.0:
        al=im.getchannel('A').point(lambda v:int(v*a)); im=im.copy(); im.putalpha(al)
    x=int(cx-im.width/2); y=int(cy-im.height/2)
    x0=max(x,0);y0=max(y,0);x1=min(x+im.width,W);y1=min(y+im.height,H)
    if x1<=x0 or y1<=y0: return
    base.alpha_composite(im.crop((x0-x,y0-y,x1-x,y1-y)),(x0,y0))
def eob(x):
    x=min(max(x,0),1); c1=1.70158;c3=c1+1
    return 1+c3*(x-1)**3+c1*(x-1)**2
def pop(t,t0,dur=0.38): return eob((t-t0)/dur) if t>=t0 else 0.0
def clamp(x,a=0,b=1): return min(max(x,a),b)
_bg={}
def photo(name):
    if name not in _bg: _bg[name]=cv2.cvtColor(cv2.imread(name),cv2.COLOR_BGR2RGB)
    return _bg[name]
def kb(name,u,z0=1.0,z1=1.1,px=0.0,py=0.0):
    img=photo(name); z=z0+(z1-z0)*u
    cw,ch=W/z,H/z
    cx=W/2+px*(W-cw)/2*(2*u-1); cy=H/2+py*(H-ch)/2*(2*u-1)
    x0=cx-cw/2;y0=cy-ch/2
    M=np.array([[z,0,-x0*z],[0,z,-y0*z]],np.float32)
    out=cv2.warpAffine(img,M,(W,H),flags=cv2.INTER_LINEAR)
    return Image.fromarray(out).convert('RGBA')
def flat(name):
    return Image.open(name).convert('RGB').convert('RGBA')
def darken(im,a):
    return Image.blend(im,Image.new('RGBA',im.size,(0,0,0,255)),a)
def rrect(size,r,fill,outline=None,width=0):
    im=Image.new('RGBA',size,(0,0,0,0)); d=ImageDraw.Draw(im)
    d.rounded_rectangle([0,0,size[0]-1,size[1]-1],r,fill=fill,outline=outline,width=width); return im
def sticky(base,color,txt,cx,cy,t,t0,scale=0.34,rot=-5,size=46,tcol=(40,30,20)):
    s=pop(t,t0)
    if s<=0: return
    nm=A+('13_prop_sticky_yellow.png' if color=='y' else '14_prop_sticky_pink.png')
    im=asset(nm,scale).copy()
    ti=text_img(txt,size,tcol,dev='kalam')
    im.alpha_composite(ti,(int((im.width-ti.width)/2),int((im.height-ti.height)/2)-10))
    place(base,im,cx,cy,s,rot)
def flipclock(base,cx,cy,secs,t,t0,sc=1.0,label=None):
    s=pop(t,t0)
    if s<=0: return
    h=secs//3600;m=(secs%3600)//60;sec=secs%60
    tw,th,g,cg=112,160,10,46
    width=6*tw+3*g+2*cg
    cv=Image.new('RGBA',(width,th+4),(0,0,0,0)); d=ImageDraw.Draw(cv)
    digs=f'{h:02d}{m:02d}{sec:02d}'; x=0
    for gi in range(3):
        for k in range(2):
            ch=digs[gi*2+k]
            d.rounded_rectangle([x,0,x+tw,th],20,fill=(28,28,32,255),outline=(80,80,90,255),width=3)
            d.text((x+tw/2,th/2+6),ch,font=font(LAT,116),fill=(255,255,255,255),anchor='mm')
            d.line([(x+3,th/2),(x+tw-3,th/2)],fill=(0,0,0,255),width=4)
            x+=tw+(g if k==0 else 0)
        if gi<2:
            d.ellipse([x+cg/2-8,th/2-36,x+cg/2+8,th/2-20],fill=(255,70,70,255))
            d.ellipse([x+cg/2-8,th/2+20,x+cg/2+8,th/2+36],fill=(255,70,70,255))
            x+=cg
    place(base,cv,cx,cy,s*sc)
    if label:
        place(base,text_img(label,62,(255,255,255),stroke=6,sfill=(0,0,0)),cx,cy-th*sc/2-70*sc,s*sc)
def shake(im,t,t0,amp=16):
    if t<t0 or t>t0+0.45: return im
    k=math.exp(-(t-t0)*9)*amp
    return ImageChops.offset(im,int(k*math.cos((t-t0)*60)),int(k*math.sin((t-t0)*47)))
def stamp(base,txt,cx,cy,t,t0,col=(220,30,40),size=96,rot=-8):
    if t<t0: return
    s=1+max(0,1-(t-t0)/0.16)*1.6
    ti=text_img(txt,size,col)
    w,h=ti.width+90,ti.height+30
    im=rrect((w,h),24,(255,255,255,0),outline=col+(255,),width=12)
    im.alpha_composite(ti,(45,12))
    place(base,im,cx,cy,s,rot,a=min(1,(t-t0)/0.06))
def pill(base,txt,cx,cy,t,t0,col=(30,100,255),size=70,done=None,rot=0):
    s=pop(t,t0)
    if s<=0: return
    c=(40,190,90) if (done is not None and t>=done) else col
    ti=text_img(txt,size,(255,255,255))
    w=ti.width+ (110 if (done is not None and t>=done) else 70); h=int(size*1.75)
    im=rrect((w,h),h//2,c+(255,))
    off=70 if (done is not None and t>=done) else 35
    im.alpha_composite(ti,(off,(h-ti.height)//2-2))
    if done is not None and t>=done:
        d=ImageDraw.Draw(im); y=h//2
        d.line([(30,y),(48,y+16),(78-20,y-18)],fill=(255,255,255,255),width=9,joint='curve')
    sh=Image.new('RGBA',(w+40,h+40),(0,0,0,0)); sh.paste((0,0,0,90),(20,26,20+w,26+h)); sh=sh.filter(ImageFilter.GaussianBlur(10))
    place(base,sh,cx,cy,s,rot); place(base,im,cx,cy,s,rot)
# ---- recording
def recfile(src_t):
    i=int(round(src_t*30))
    for d in range(0,40):
        for j in (i-d,i+d):
            p=f'{R}{j:05d}.jpg'
            if os.path.exists(p): return p
_rc={}
def recimg(src_t):
    p=recfile(src_t)
    if p not in _rc:
        if len(_rc)>60: _rc.clear()
        _rc[p]=cv2.cvtColor(cv2.imread(p),cv2.COLOR_BGR2RGB)
    return _rc[p]
PS=0.88
def phone(base,t,segs,t0,cy=1040):
    s=pop(t,t0,0.5)
    if s<=0: return
    ph=asset(A+'11_prop_phone_grid.png',PS)
    out=ph.copy()
    sx0,sy0,sx1,sy1=[int(v*PS) for v in (54,54,914,1773)]
    sw,sh=sx1-sx0,sy1-sy0
    # pick segment
    src=None
    for (a,b,sa,sb) in segs:
        if a<=t<b: src=sa+(sb-sa)*(t-a)/(b-a); break
    if src is None: src=segs[-1][3] if t>=segs[-1][1] else segs[0][2]
    fr=recimg(src); fh=sh; fw=int(fr.shape[1]*fh/fr.shape[0])
    fr=cv2.resize(fr,(fw,fh),interpolation=cv2.INTER_AREA)
    canvas=np.full((sh,sw,3),246,np.uint8)
    x=(sw-fw)//2
    if fw>sw: fr=fr[:,(fw-sw)//2:(fw-sw)//2+sw]; fw=sw; x=0
    canvas[:,x:x+fw]=fr
    mask=Image.new('L',(sw,sh),0); ImageDraw.Draw(mask).rounded_rectangle([0,0,sw-1,sh-1],int(62*PS),fill=255)
    sc=Image.fromarray(canvas).convert('RGBA'); sc.putalpha(mask)
    out.alpha_composite(sc,(sx0,sy0))
    sh_=Image.new('RGBA',(out.width+80,out.height+80),(0,0,0,0)); sh_.paste((0,0,0,110),(40,60,40+out.width,60+out.height)); sh_=sh_.filter(ImageFilter.GaussianBlur(22))
    yoff=(1-clamp(s,0,1.2))*1400 if s<1 else 0
    place(base,sh_,540,cy+yoff); place(base,out,540,cy+yoff)
