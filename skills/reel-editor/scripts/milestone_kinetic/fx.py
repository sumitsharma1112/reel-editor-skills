# milestone_kinetic: follower-milestone reel from dashboard numbers: counters, orbiting reel thumbnails, city/country bars, real views graph, Hinglish Roman captions, egg-drop hook. Made with Claude, Nov 2026.
# Paths to inputs (videos, images, fonts, audio) are set near the top: edit them for a new reel.
import os, sys
import sys; sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from comp import place, pop, eob, clamp, asset, rrect, recimg, kb, A, P, W, H, LAT, font
from comp2 import notif, receipt, cursor, shadow_of
import numpy as np, cv2, math, re, random
from PIL import Image, ImageDraw, ImageFont, ImageFilter
GF='/usr/share/fonts/truetype/google-fonts/'
LBI=GF+'Poppins-BoldItalic.ttf'; LB=GF+'Poppins-Bold.ttf'; LMI=GF+'Poppins-MediumItalic.ttf'; LSBI=GF+'Poppins-MediumItalic.ttf'
DB='/home/claude/ex/fnt/baloo-2-devanagari-800-normal.ttf'; DM='/home/claude/ex/fnt/baloo-2-devanagari-700-normal.ttf'
RED=(222,26,42)
DEVRE=re.compile(r'[ऀ-ॿ]')
def _f(p,s): return font(p,s)
def mask_text(txt,size,lat,dev,shear=0.0):
    fd=_f(dev,size); fl=_f(lat,int(size*0.9))
    runs=[(m.group(0), fd if DEVRE.match(m.group(0)) else fl) for m in re.finditer(r'[ऀ-ॿ]+|[^ऀ-ॿ]+',txt)]
    wd=sum(f.getlength(r) for r,f in runs)
    pad=int(size*0.35); w=int(wd)+pad*2; h=int(size*1.9)
    m=Image.new('L',(w,h),0); d=ImageDraw.Draw(m); x=pad; base=int(size*1.25)
    for r,f in runs:
        d.text((x,base),r,font=f,fill=255,anchor='ls'); x+=f.getlength(r)
    bb=m.getbbox(); m=m.crop((max(bb[0]-8,0),max(bb[1]-8,0),min(bb[2]+8,w),min(bb[3]+8,h)))
    if shear:
        w,h=m.size; ext=int(shear*h)+4
        m=m.transform((w+ext,h),Image.AFFINE,(1,shear,-shear*h,0,1,0),resample=Image.BICUBIC)
    return m
_wc={}
def grad(w,h,c0,c1):
    a=np.linspace(0,1,h)[:,None,None]
    g=(np.array(c0)[None,None,:]*(1-a)+np.array(c1)[None,None,:]*a)
    return Image.fromarray(np.repeat(g,w,axis=1).astype(np.uint8),'RGB')
def word3d(txt,size,maxw=980):
    k=(txt,size,maxw)
    if k in _wc: return _wc[k]
    dev=bool(DEVRE.search(txt))
    m=mask_text(txt,size,LB if dev else LBI,DB,shear=0.2 if dev else 0.0)
    if m.width>maxw:
        r=maxw/m.width; m=m.resize((int(m.width*r),int(m.height*r)),Image.LANCZOS)
    w,h=m.size; D=max(6,int(h*0.06)); P_=60
    out=Image.new('RGBA',(w+P_*2,h+P_*2),(0,0,0,0))
    # soft shadow
    sh=Image.new('L',out.size,0); sh.paste(m,(P_+int(D*1.4),P_+int(D*2.6)))
    sh=sh.filter(ImageFilter.GaussianBlur(int(size*0.07)+4)).point(lambda v:int(v*0.30))
    out.paste((60,0,10,255),(0,0),sh)
    for k2 in range(D,0,-1):
        c=(120-int(40*k2/D),0,12)
        lay=Image.new('RGBA',out.size,(0,0,0,0)); lay.paste(c+(255,),(int(P_+k2*0.45),int(P_+k2*0.9)),m)
        out.alpha_composite(lay)
    face=grad(w,h,(255,78,66),(188,0,24)).convert('RGBA'); face.putalpha(m)
    # top highlight
    hl=grad(w,h,(255,255,255),(255,255,255)).convert('RGBA'); hm=np.asarray(m).astype(np.float32)*np.linspace(0.32,0,h)[:,None]
    hl.putalpha(Image.fromarray(np.clip(hm*np.concatenate([np.ones(int(h*0.45)),np.zeros(h-int(h*0.45))])[:,None],0,255).astype(np.uint8)))
    out.alpha_composite(face,(P_,P_)); out.alpha_composite(hl,(P_,P_))
    _wc[k]=out; return out
def small_text(txt,size,col=RED,maxw=1000):
    k=('s',txt,size,col)
    if k in _wc: return _wc[k]
    dev=bool(DEVRE.search(txt))
    m=mask_text(txt,size,LSBI if not dev else LB,DM,shear=0.18 if dev else 0.0)
    if m.width>maxw:
        r=maxw/m.width; m=m.resize((int(m.width*r),int(m.height*r)),Image.LANCZOS)
    out=Image.new('RGBA',(m.width+20,m.height+20),(0,0,0,0))
    glow=Image.new('L',out.size,0); glow.paste(m,(10,10)); glow=glow.filter(ImageFilter.GaussianBlur(6)).point(lambda v:int(v*0.55))
    out.paste((255,255,255,255),(0,0),glow)
    out.paste(col+(255,),(10,10),m)
    _wc[k]=out; return out
def pill_label(txt,size=50,col=RED):
    k=('p',txt,size,col)
    if k in _wc: return _wc[k]
    t=small_text(txt,size,(255,255,255))
    w,h=t.width+40,int(size*1.55)
    im=Image.new('RGBA',(w+30,h+30),(0,0,0,0))
    sh=Image.new('L',im.size,0); ImageDraw.Draw(sh).rounded_rectangle([15,22,15+w,22+h],h//2,fill=110); sh=sh.filter(ImageFilter.GaussianBlur(8))
    im.paste((90,0,10,255),(0,0),sh)
    ImageDraw.Draw(im).rounded_rectangle([15,15,15+w,15+h],h//2,fill=col+(255,))
    im.alpha_composite(t,(15+(w-t.width)//2,15+(h-t.height)//2-2))
    _wc[k]=im; return im
def hblur(im,k):
    k=int(k)
    if k<2: return im
    a=np.asarray(im); a=cv2.blur(a,(k,1)); return Image.fromarray(a,'RGBA')
def vblur(im,k):
    k=int(k)
    if k<2: return im
    a=np.asarray(im); a=cv2.blur(a,(1,k)); return Image.fromarray(a,'RGBA')
def anim(base,im,cx,cy,t,t0,t1=None,dur=0.45,rot=0,mode='wipe'):
    if t<t0 or (t1 is not None and t>t1+0.24): return
    p=clamp((t-t0)/dur); e=1-(1-p)**3
    img=im; s=1.0; dx=0; dy=0; a=1.0
    if mode=='wipe' and p<1:
        w=img.width; F=w*0.45; edge=e*(w+F)
        ramp=np.clip((edge-np.arange(w))/F,0,1).astype(np.float32)
        arr=np.asarray(img).copy(); arr[:,:,3]=(arr[:,:,3]*ramp[None,:]).astype(np.uint8)
        img=hblur(Image.fromarray(arr,'RGBA'),(1-e)*60)
        s=1.22-0.22*e; dx=(1-e)*70
    elif mode=='slam':
        s=1+max(0,1-p*2.6)*1.4; a=clamp(p*5)
    elif mode=='pop':
        s=eob(p); a=clamp(p*3)
    if t1 is not None and t>t1:
        q=clamp((t-t1)/0.22); img=vblur(img,q*40); a*=1-q; s*=1+0.18*q; dy-=60*q
    place(base,img,cx+dx,cy+dy,s,rot,a)
def pixels(base,t,t0,cx,cy,sx=430,sy=200,n=13,seed=0):
    if not (t0-0.15<t<t0+0.7): return
    rng=random.Random(seed*7919+int(t0*100))
    ov=Image.new('RGBA',(W,H),(0,0,0,0)); d=ImageDraw.Draw(ov); any_=False
    for i in range(n):
        g=30
        x=int((cx+rng.uniform(-sx,sx))//g*g); y=int((cy+rng.uniform(-sy,sy))//g*g)
        ts=t0+rng.uniform(-0.12,0.45); te=ts+rng.uniform(0.07,0.28)
        sz=g*rng.choice([1,1,1,2])
        al=int(255*rng.uniform(0.35,0.95)); col=rng.choice([RED,RED,(240,120,130),(255,190,195)])
        if ts<=t<te:
            d.rectangle([x,y,x+sz,y+sz],fill=col+(al,)); any_=True
            if rng.random()<0.5: d.rectangle([x+sz,y,x+sz+g//2,y+g//2],fill=col+(al//2,))
    if any_: base.alpha_composite(ov)
_bgc={}
def studio():
    if 's' in _bgc: return _bgc['s'].copy()
    y=np.linspace(0,1,H)[:,None]; x=np.linspace(-1,1,W)[None,:]
    top=np.array([241,239,244]); mid=np.array([231,228,235]); flo=np.array([238,236,241])
    a=np.clip(y/0.66,0,1)
    col=top[None,None,:]*(1-a[...,None])+mid[None,None,:]*a[...,None]
    fl=np.clip((y-0.66)/0.12,0,1)[...,None]
    col=col*(1-fl)+flo[None,None,:]*fl
    rad=np.exp(-((x/0.9)**2+((y-0.35)/0.55)**2))[...,None]
    col=col+rad*8
    im=Image.fromarray(np.clip(col,0,255).astype(np.uint8),'RGB').convert('RGBA')
    _bgc['s']=im; return im.copy()
def floor_shadow(base,cx,y,w=460):
    k=('fs',w)
    if k not in _bgc:
        im=Image.new('RGBA',(w+120,200),(0,0,0,0)); ImageDraw.Draw(im).ellipse([60,70,60+w,130],fill=(40,30,40,120)); _bgc[k]=im.filter(ImageFilter.GaussianBlur(18))
    place(base,_bgc[k],cx,y)
def avatar(base,name,t,t_in,sc=0.56,cx=540,bottom=1845):
    a=asset(A+name+'.png'); h=a.height*sc
    p=pop(t,t_in,0.5)
    if p<=0: return
    bob=1+0.006*math.sin(t*2.4)
    yy=bottom-h/2+(1-clamp(p,0,1))*500
    floor_shadow(base,cx,bottom-4)
    place(base,a,cx,yy,sc*bob*(0.96+0.04*clamp(p,0,1)))
_cc={}
def card(path,w,h):
    k=(path,w,h)
    if k in _cc: return _cc[k]
    img=Image.open(path).convert('RGB'); iw,ih=img.size; r=w/h
    if iw/ih>r: nw=int(ih*r); img=img.crop(((iw-nw)//2,0,(iw-nw)//2+nw,ih))
    else: nh=int(iw/r); img=img.crop((0,(ih-nh)//2,iw,(ih-nh)//2+nh))
    img=img.resize((w,h),Image.LANCZOS).convert('RGBA')
    m=Image.new('L',(w,h),0); ImageDraw.Draw(m).rounded_rectangle([0,0,w-1,h-1],30,fill=255); img.putalpha(m)
    gl=grad(w,h,(255,255,255),(255,255,255)).convert('RGBA'); gm=(np.linspace(70,0,h)[:,None]*np.ones((1,w))); gm[int(h*0.4):]=0
    gl.putalpha(Image.fromarray((gm*np.asarray(m)/255).astype(np.uint8))); img.alpha_composite(gl)
    B=12; out=Image.new('RGBA',(w+2*B+80,h+2*B+80),(0,0,0,0))
    sh=Image.new('L',out.size,0); ImageDraw.Draw(sh).rounded_rectangle([40,58,40+w+2*B,58+h+2*B],40,fill=120); sh=sh.filter(ImageFilter.GaussianBlur(20))
    out.paste((60,10,20,255),(0,0),sh)
    gw=Image.new('L',out.size,0); ImageDraw.Draw(gw).rounded_rectangle([40,40,40+w+2*B,40+h+2*B],40,outline=255,width=10); gw=gw.filter(ImageFilter.GaussianBlur(10)).point(lambda v:int(v*0.6))
    out.paste(RED+(255,),(0,0),gw)
    ImageDraw.Draw(out).rounded_rectangle([40,40,40+w+2*B,40+h+2*B],40,fill=RED+(255,))
    ImageDraw.Draw(out).rounded_rectangle([40+5,40+5,40+w+2*B-5,40+h+2*B-5],36,fill=(255,255,255,255))
    out.alpha_composite(img,(40+B,40+B))
    _cc[k]=out; return out
def streak(base,t,tc,dur=0.55):
    u=(t-(tc-dur/2))/dur
    if not (0<=u<=1): return base
    head=-300+(H+1000)*u
    ys=np.arange(max(-300,head-1000),min(H+300,head),6)
    if len(ys)<2: return base
    xs=540+250*np.sin(ys/190+1.4)+60*np.sin(ys/70)
    pts=np.stack([xs/2,ys/2],1).astype(np.int32).reshape(-1,1,2)
    g=np.zeros((H//2,W//2,3),np.float32)
    cv2.polylines(g,[pts],False,(255,40,50),26,cv2.LINE_AA); g=cv2.GaussianBlur(g,(0,0),11)
    c=np.zeros_like(g); cv2.polylines(c,[pts],False,(255,255,255),4,cv2.LINE_AA); c=cv2.GaussianBlur(c,(0,0),1.2)
    g=cv2.resize(g*0.9+c,(W,H))
    arr=np.asarray(base.convert('RGB')).astype(np.float32)
    arr=np.clip(arr*(1-0.0)+g,0,255)
    return Image.fromarray(arr.astype(np.uint8)).convert('RGBA')
_dots=None
def halftone(base,t,tc,dur=0.7):
    global _dots
    u=(t-(tc-dur/2))/dur
    if not (0<=u<=1): return base
    if _dots is None:
        gx,gy=np.meshgrid(np.arange(12,W,26),np.arange(12,H,26)); _dots=(gx.ravel(),gy.ravel(),np.sqrt(((gx.ravel()-540)/540)**2+((gy.ravel()-960)/960)**2))
    gx,gy,d=_dots; ring=u*1.9-0.2
    r=11*np.clip(1-np.abs(d-ring)/0.45,0,1)
    if u>0.5: r=np.maximum(r,11*np.clip((ring-d)/0.4,0,1)*(1-u)*2)
    ov=np.zeros((H,W,4),np.uint8)
    for x,y,rr in zip(gx,gy,r):
        if rr>0.6: cv2.circle(ov,(int(x),int(y)),int(rr),(225,30,45,235),-1,cv2.LINE_AA)
    k=1-abs(u-0.5)*2
    b=base
    if k>0.05:
        a=np.asarray(base); s=cv2.resize(a,(W//4,H//4)); s=cv2.GaussianBlur(s,(0,0),3+6*k); b=Image.fromarray(cv2.resize(s,(W,H)),'RGBA')
        b=Image.blend(base,b,clamp(k*1.3))
    b=b.copy(); b.alpha_composite(Image.fromarray(ov,'RGBA')); return b
def glitch(base,t,tc,dur=0.36,seed=1):
    u=(t-(tc-dur/2))/dur
    if not (0<=u<=1): return base
    k=1-abs(u-0.5)*2
    a=np.asarray(base.convert('RGB')).copy()
    sh=int(18*k)
    if sh>0:
        a[:,:,0]=np.roll(a[:,:,0],sh,1); a[:,:,2]=np.roll(a[:,:,2],-sh,1)
    rng=random.Random(int(t*60)+seed)
    for i in range(int(8*k)):
        y=rng.randrange(0,H-80); hh=rng.randrange(20,90); dx=rng.randrange(-80,80)
        a[y:y+hh]=np.roll(a[y:y+hh],dx,1)
    im=Image.fromarray(a).convert('RGBA')
    pixels(im,t,tc-0.1,540,960,500,800,n=30,seed=seed)
    if k>0.6: im=Image.blend(im,Image.new('RGBA',(W,H),(255,255,255,255)),(k-0.6)*1.2)
    return im
_pf={}
def phone_frame(w,h):
    k=(w,h)
    if k in _pf: return _pf[k]
    B=14; out=Image.new('RGBA',(w+2*B+100,h+2*B+100),(0,0,0,0)); o=50
    sh=Image.new('L',out.size,0); ImageDraw.Draw(sh).rounded_rectangle([o,o+22,o+w+2*B,o+22+h+2*B],90,fill=130); sh=sh.filter(ImageFilter.GaussianBlur(24)); out.paste((60,10,20,255),(0,0),sh)
    gw=Image.new('L',out.size,0); ImageDraw.Draw(gw).rounded_rectangle([o,o,o+w+2*B,o+h+2*B],90,outline=255,width=16); gw=gw.filter(ImageFilter.GaussianBlur(14)).point(lambda v:int(v*0.8)); out.paste(RED+(255,),(0,0),gw)
    ImageDraw.Draw(out).rounded_rectangle([o,o,o+w+2*B,o+h+2*B],90,fill=RED+(255,))
    ImageDraw.Draw(out).rounded_rectangle([o+4,o+4,o+w+2*B-4,o+h+2*B-4],86,outline=(255,150,155,255),width=3)
    m=Image.new('L',(w,h),0); ImageDraw.Draw(m).rounded_rectangle([0,0,w-1,h-1],76,fill=255)
    _pf[k]=(out,m,o+B); return _pf[k]
def phone_rec(base,t,segs,t_in,cx=540,cy=1150,w=600):
    p=pop(t,t_in,0.5)
    if p<=0: return
    h=int(w*1920/886)
    fr_,m,off=phone_frame(w,h)
    src=None
    for (a,b,sa,sb) in segs:
        if a<=t<b: src=sa+(sb-sa)*(t-a)/(b-a); break
    if src is None: src=segs[-1][3] if t>=segs[-1][1] else segs[0][2]
    rec=cv2.resize(recimg(src),(w,h),interpolation=cv2.INTER_AREA)
    sc=Image.fromarray(rec).convert('RGBA'); sc.putalpha(m)
    out=fr_.copy(); out.alpha_composite(sc,(off,off))
    place(base,out,cx,cy+(1-clamp(p,0,1))*300,0.85+0.15*clamp(p,0,1.2))
_bd=None
def phone_backdrop():
    global _bd
    if _bd is None:
        b=studio()
        arr=np.asarray(b).copy()
        gx,gy=np.meshgrid(np.arange(13,W,26),np.arange(13,H,26))
        d=np.sqrt(((gx-540)/540)**2+((gy-1000)/1000)**2)
        r=np.clip((d-0.78)*20,0,8)
        for x,y,rr in zip(gx.ravel(),gy.ravel(),r.ravel()):
            if rr>0.8: cv2.circle(arr,(int(x),int(y)),int(rr),(240,150,156,255),-1,cv2.LINE_AA)
        _bd=Image.fromarray(arr,'RGBA')
    return _bd.copy()

_nc={}
def notif_card(title,body):
    k=(title,body)
    if k in _nc: return _nc[k]
    w,h=640,140
    out=Image.new('RGBA',(w+60,h+60),(0,0,0,0))
    sh=Image.new('L',out.size,0); ImageDraw.Draw(sh).rounded_rectangle([30,44,30+w,44+h],34,fill=120); sh=sh.filter(ImageFilter.GaussianBlur(14)); out.paste((60,10,20,255),(0,0),sh)
    d=ImageDraw.Draw(out)
    d.rounded_rectangle([30,30,30+w,30+h],34,fill=(255,255,255,255),outline=RED+(255,),width=5)
    d.rounded_rectangle([52,52,52+96,52+96],24,fill=(37,211,102,255))
    d.ellipse([72,70,128,124],fill=(255,255,255,255)); d.polygon([(78,114),(70,136),(98,120)],fill=(255,255,255,255))
    out.alpha_composite(small_text(title,34,(30,30,34)),(160,32))
    out.alpha_composite(small_text(body,40,RED),(160,84))
    _nc[k]=out; return out
