import cv2, numpy as np, subprocess, sys, math, functools
from PIL import Image, ImageDraw, ImageFilter
sys.path.insert(0,'.')
from txt import render
W,H,FPS=1080,1920,30
S=1.5  # 720 -> 1080
RED=(227,30,36,255); GOLD=(255,200,61,255); WHITE=(255,255,255,255); CREAM=(255,246,224,255); DARK=(30,22,18,255)
Hs=np.load('sign_H.npy')

def ease_back(t,s=1.7):
    t=min(max(t,0),1); t-=1; return t*t*((s+1)*t+s)+1
def ease_out(t): t=min(max(t,0),1); return 1-(1-t)**3
def clamp(v,a=0,b=1): return max(a,min(b,v))

class Src:
    def __init__(s,path): s.cap=cv2.VideoCapture(path); s.cache={}
    def frame(s,t):
        i=int(round(t*24))
        if i not in s.cache:
            s.cap.set(cv2.CAP_PROP_POS_FRAMES,i); ok,f=s.cap.read()
            if not ok: return s.cache[max(s.cache)]
            f=cv2.resize(f,(W,H),interpolation=cv2.INTER_LANCZOS4)
            bl=cv2.GaussianBlur(f,(0,0),1.2); f=cv2.addWeighted(f,1.35,bl,-0.35,0)
            s.cache={i:f}
        return s.cache[i].copy()
SRC={k:Src(f'../src/{k}.mp4') for k in ['c_gemini','c_postal','c_receive']}

def rounded_mask(w,h,r,feather=0):
    m=Image.new('L',(w,h),0); ImageDraw.Draw(m).rounded_rectangle([0,0,w-1,h-1],r,fill=255)
    if feather: m=m.filter(ImageFilter.GaussianBlur(feather))
    return np.asarray(m,np.float32)/255
def glass(img,box,r=40,dark=0.5,blur=22,border=True,feather=0):
    """frosted glass over box (x0,y0,x1,y1) in 1080 coords, img = BGR np"""
    x0,y0,x1,y1=[int(v) for v in box]; x0=max(0,x0);y0=max(0,y0);x1=min(W,x1);y1=min(H,y1)
    reg=img[y0:y1,x0:x1].astype(np.float32)
    small=cv2.resize(reg,None,fx=0.25,fy=0.25); small=cv2.GaussianBlur(small,(0,0),blur/4)
    b=cv2.resize(small,(x1-x0,y1-y0)); b=b*(1-dark)
    m=rounded_mask(x1-x0,y1-y0,r,feather)[...,None]
    img[y0:y1,x0:x1]=(reg*(1-m)+b*m).astype(np.uint8)
    if border:
        o=np.zeros((y1-y0,x1-x0),np.uint8)
        cv2.rectangle(o,(0,0),(x1-x0-1,y1-y0-1),0)
        bm=Image.new('L',(x1-x0,y1-y0),0); ImageDraw.Draw(bm).rounded_rectangle([1,1,x1-x0-2,y1-y0-2],r,outline=255,width=3)
        a=np.asarray(bm,np.float32)[...,None]/255*0.28
        img[y0:y1,x0:x1]=(img[y0:y1,x0:x1]*(1-a)+255*a).astype(np.uint8)
    return img

# ---------- graphic builders (cached RGBA) ----------
@functools.lru_cache(None)
def T(text,size,color=WHITE,font='head',stroke=0,shadow=True):
    return render(text.replace(' ','  ') if font=='head' else text,font,size,fill=color,stroke=stroke,shadow=(4,8,170) if shadow else None)
@functools.lru_cache(None)
def pill(text,size,bg=RED,fg=WHITE,pad=(34,14)):
    t=render(text.replace(' ','  '),'head',size,fill=fg)
    w,h=t.width+2*pad[0],t.height+2*pad[1]
    im=Image.new('RGBA',(w+30,h+30)); d=ImageDraw.Draw(im)
    sh=Image.new('RGBA',im.size); ImageDraw.Draw(sh).rounded_rectangle([15,22,15+w,22+h],h//2,fill=(0,0,0,140)); sh=sh.filter(ImageFilter.GaussianBlur(7))
    im.alpha_composite(sh); ImageDraw.Draw(im).rounded_rectangle([15,15,15+w,15+h],h//2,fill=bg)
    im.alpha_composite(t,(15+pad[0],15+pad[1])); return im
@functools.lru_cache(None)
def stamp(text,size):
    t=render(text.replace(' ','  '),'head',size,fill=RED)
    w,h=t.width+110,t.height+80
    im=Image.new('RGBA',(w+60,h+60)); d=ImageDraw.Draw(im)
    ox,oy=30,30
    d.rectangle([ox,oy,ox+w,oy+h],fill=CREAM)
    r=11
    for x in range(ox,ox+w+1,2*r+6):
        d.ellipse([x-r,oy-r,x+r,oy+r],fill=(0,0,0,0)); d.ellipse([x-r,oy+h-r,x+r,oy+h+r],fill=(0,0,0,0))
    for y in range(oy,oy+h+1,2*r+6):
        d.ellipse([ox-r,y-r,ox+r,y+r],fill=(0,0,0,0)); d.ellipse([ox+w-r,y-r,ox+w+r,y+r],fill=(0,0,0,0))
    d.rectangle([ox+26,oy+26,ox+w-26,oy+h-26],outline=RED,width=5)
    im.alpha_composite(t,(ox+55,oy+40))
    sh=Image.new('RGBA',im.size); a=im.split()[3].filter(ImageFilter.GaussianBlur(10)).point(lambda v:v*0.6)
    sh.putalpha(a); out=Image.new('RGBA',im.size); out.alpha_composite(sh,(0,0)); out.alpha_composite(im)
    return out.rotate(-4,resample=Image.BICUBIC,expand=True)
@functools.lru_cache(None)
def sign_plate(w,h):
    im=Image.new('RGBA',(w,h)); d=ImageDraw.Draw(im)
    d.rectangle([0,0,w,h],fill=(206,32,39,255))
    l1=render('ਭਾਰਤੀ  ਡਾਕ  ·  INDIA POST','head',100,fill=WHITE)
    l2=render('FARIDKOT POSTAL DIVISION','head',100,fill=WHITE)
    gap=int(l1.height*0.22)
    s=min((w*0.9)/max(l1.width,l2.width),(h*0.84)/(l1.height+l2.height+gap))
    l1=l1.resize((int(l1.width*s),int(l1.height*s)),Image.LANCZOS); l2=l2.resize((int(l2.width*s),int(l2.height*s)),Image.LANCZOS)
    g=int(gap*s); y=(h-l1.height-l2.height-g)//2
    im.alpha_composite(l1,((w-l1.width)//2,y)); im.alpha_composite(l2,((w-l2.width)//2,y+l1.height+g))
    return im
@functools.lru_cache(None)
def checklist_card(n_checked):
    w,h=860,470
    im=Image.new('RGBA',(w+40,h+40)); d=ImageDraw.Draw(im)
    sh=Image.new('RGBA',im.size); ImageDraw.Draw(sh).rounded_rectangle([20,30,20+w,30+h],44,fill=(0,0,0,150)); sh=sh.filter(ImageFilter.GaussianBlur(12)); im.alpha_composite(sh)
    d.rounded_rectangle([20,20,20+w,20+h],44,fill=(255,253,247,245))
    tt=render("ਡਾਕਘਰ  ਕਾਊਂਟਰ  'ਤੇ","head",58,fill=RED); im.alpha_composite(tt,(70,48))
    d.line([(70,48+tt.height+14),(20+w-50,48+tt.height+14)],fill=(230,220,205,255),width=3)
    rows=['ਵਜ਼ਨ','ਰਸੀਦ','ਟ੍ਰੈਕਿੰਗ  ਨੰਬਰ']
    y=48+tt.height+40
    for i,r in enumerate(rows):
        on=i<n_checked
        cx,cy=110,y+42
        if on:
            d.rounded_rectangle([60,y-4,20+w-40,y+88],22,fill=(255,236,170,255))
            d.ellipse([cx-30,cy-30,cx+30,cy+30],fill=(40,170,90,255))
            d.line([(cx-15,cy+1),(cx-4,cy+13),(cx+17,cy-12)],fill=WHITE,width=8)
        else:
            d.ellipse([cx-30,cy-30,cx+30,cy+30],outline=(190,180,170,255),width=5)
        t=render(r,'head',62,fill=DARK if on else (120,110,100,255)); im.alpha_composite(t,(165,y+42-t.height//2-4))
        y+=104
    return im

def paste(canvas,img,cx,cy,scale=1.0,alpha=1.0,rot=0):
    if scale<=0.01 or alpha<=0.01: return
    im=img
    if abs(scale-1)>0.005: im=im.resize((max(1,int(im.width*scale)),max(1,int(im.height*scale))),Image.BICUBIC)
    if rot: im=im.rotate(rot,resample=Image.BICUBIC,expand=True)
    if alpha<1: a=im.split()[3].point(lambda v:int(v*alpha)); im=im.copy(); im.putalpha(a)
    canvas.alpha_composite(im,(int(cx-im.width/2),int(cy-im.height/2)))
def pop(canvas,img,cx,cy,t,t0,dur=0.32,t_out=None):
    if t<t0: return
    p=(t-t0)/dur; sc=0.55+0.45*ease_back(p); al=clamp(p*3)
    if t_out is not None and t>t_out:
        q=clamp((t-t_out)/0.18); al*=1-q; sc*=1-0.15*q
    paste(canvas,img,cx,cy,sc,al)

def zoom(img,z,cx=W/2,cy=H/2):
    M=np.float32([[z,0,cx-cx*z],[0,z,cy-cy*z]])
    return cv2.warpAffine(img,M,(W,H),flags=cv2.INTER_LINEAR,borderMode=cv2.BORDER_REFLECT)
def zp(p,z,cx=W/2,cy=H/2): return (cx+(p[0]-cx)*z, cy+(p[1]-cy)*z)
def B(x0,y0,x1,y1): return (x0*S,y0*S,x1*S,y1*S)

# ---------- scenes: each returns list of (src,t_src) and draw fn ----------
def kb(t,dur,a=1.0,b=1.05): return a+(b-a)*(t/dur)

def scene_hook(t,dur):
    f=SRC['c_gemini'].frame(0.0+t)
    box=B(138,582,706,802); f=glass(f,box,r=44,dark=0.55)
    z=kb(t,dur,1.02,1.07); f=zoom(f,z)
    c=Image.fromarray(cv2.cvtColor(f,cv2.COLOR_BGR2RGB)).convert('RGBA')
    cx,cy=zp(((box[0]+box[2])/2,(box[1]+box[3])/2),z)
    l1=T('ਵਿਦੇਸ਼ ਪਾਰਸਲ ਭੇਜਣਾ…',76); l2=T('ਇੰਨਾ ਮਹਿੰਗਾ?? 😳',98,GOLD)
    sc=0.92+0.08*ease_out(t/0.25)
    paste(c,l1,cx,cy-62*z,sc); 
    if t>=0.35: pop(c,l2,cx,cy+58*z,t,0.35,0.3)
    else: pass
    return c
def scene_family(t,dur):
    ts=3.40+t; f=SRC['c_gemini'].frame(ts)
    band=B(0,765,720,1045); on_stamp=ts>=8.44
    if on_stamp: f=glass(f,(band[0]-10,band[1],band[2]+10,band[3]),r=0,dark=0.45,border=False,feather=6)
    z=kb(t,dur,1.0,1.06); f=zoom(f,z)
    c=Image.fromarray(cv2.cvtColor(f,cv2.COLOR_BGR2RGB)).convert('RGBA')
    pop(c,T('ਕੋਰੀਅਰ ਦੇ ਭਾਰੀ ਖ਼ਰਚੇ 😟',80),W/2,300,t,0.1,t_out=2.35)
    pop(c,T('ਪਰ ਪੁੱਤ ਬੋਲਿਆ…',84,GOLD),W/2,300,t,2.6,t_out=5.0)
    if on_stamp:
        cx,cy=zp(((band[0]+band[2])/2,(band[1]+band[3])/2),z)
        p=clamp((ts-8.44)/0.14); sc=2.0-1.0*ease_out(p)
        paste(c,stamp('ਡਾਕਘਰ ਹੈ ਨਾ! ✈️',92),cx,cy,sc,clamp(p*2))
    return c
def scene_building(t,dur):
    i=min(119,int(round(t*24))); f=SRC['c_postal'].frame(t)
    Hm=Hs[i]; rect=np.float32([[[216,426]],[[566,426]],[[566,508]],[[216,508]]])
    p=cv2.perspectiveTransform(rect,Hm).reshape(-1,2)*S
    x0,y0=p[:,0].min(),p[:,1].min(); x1,y1=p[:,0].max(),p[:,1].max(); x1=min(x1,x0+(x1-x0)*0.93)
    lt=B(80,950,640,1135)
    f=glass(f,lt,r=36,dark=0.62)
    z=kb(t,dur,1.0,1.04); f=zoom(f,z)
    c=Image.fromarray(cv2.cvtColor(f,cv2.COLOR_BGR2RGB)).convert('RGBA')
    # sign plate (left 22% keeps the AI logo region? cover whole text area)
    a0=zp((x0+(x1-x0)*0.25,y0),z); a1=zp((x1,y1),z)
    w,h=int(a1[0]-a0[0]),int(a1[1]-a0[1])
    if w>20 and h>10:
        pl=sign_plate(max(40,w//4*4),max(20,h//2*2)).resize((w,h),Image.LANCZOS)
        c.alpha_composite(pl,(int(a0[0]),int(a0[1])))
    cx,cy=zp(((lt[0]+lt[2])/2,(lt[1]+lt[3])/2),z)
    pop(c,T('ਇੰਟਰਨੈਸ਼ਨਲ ਸਪੀਡ ਪੋਸਟ ✈️',70,GOLD),cx,cy-50,t,0.15)
    pop(c,T('📍 ਫ਼ਰੀਦਕੋਟ ਡਾਕ ਮੰਡਲ',66),cx,cy+52,t,0.45)
    return c
def scene_pack(t,dur):
    if t<1.70:
        ts=7.40+t; f=SRC['c_postal'].frame(ts); band=B(0,755,720,1010)
        f=glass(f,(band[0]-10,band[1],band[2]+10,band[3]),r=0,dark=0.6,blur=40,border=False,feather=6)
        z=kb(t,1.7,1.0,1.05)
    else:
        ts=9.20+(t-1.70); f=SRC['c_postal'].frame(ts); z=kb(t-1.7,dur-1.7,1.04,1.08)
    f=zoom(f,z); c=Image.fromarray(cv2.cvtColor(f,cv2.COLOR_BGR2RGB)).convert('RGBA')
    cy=(755+1010)/2*S
    items=[('✅ ਸੂਟ',0.05),('✅ ਤੋਹਫ਼ੇ',0.45),('✅ ਪਿਆਰ ❤️',0.85)]
    xs=[W*0.22,W*0.5,W*0.78]
    for (s,t0),x in zip(items,xs): pop(c,pill(s,54,bg=(255,253,247,240),fg=DARK),x,cy if t<1.7 else 1500,t,t0)
    return c
def scene_counter(t,dur):
    ts=10.0+t; f=SRC['c_postal'].frame(ts); band=B(0,745,720,1150)
    f=glass(f,(band[0]-10,band[1],band[2]+10,band[3]),r=0,dark=0.35,border=False,feather=8)
    z=kb(t,dur,1.0,1.04); f=zoom(f,z); c=Image.fromarray(cv2.cvtColor(f,cv2.COLOR_BGR2RGB)).convert('RGBA')
    cx,cy=zp(((band[0]+band[2])/2,(band[1]+band[3])/2),z)
    n=0 if t<0.7 else 1 if t<1.6 else 2 if t<2.5 else 3
    p=clamp(t/0.3); paste(c,checklist_card(n),cx,cy+(1-ease_out(p))*120,1.0,p)
    return c
def scene_globe(t,dur):
    f=SRC['c_receive'].frame(t); band=B(0,262,720,510)
    if t>=1.05: f=glass(f,(band[0]-10,band[1],band[2]+10,band[3]),r=0,dark=0.5,border=False,feather=10)
    z=kb(t,dur,1.0,1.05); f=zoom(f,z); c=Image.fromarray(cv2.cvtColor(f,cv2.COLOR_BGR2RGB)).convert('RGBA')
    cy=zp((0,(band[1]+band[3])/2),z)[1]
    ps=[('🇨🇦 ਕੈਨੇਡਾ',1.1,W*0.29,cy-72),('🇺🇸 ਅਮਰੀਕਾ',1.45,W*0.71,cy-72),('🇬🇧 ਯੂ.ਕੇ.',1.8,W*0.29,cy+72),('🇦🇺 ਆਸਟ੍ਰੇਲੀਆ',2.15,W*0.71,cy+72)]
    for s,t0,x,y in ps: pop(c,pill(s,52),x,y,t,t0)
    pop(c,T('ਘੱਟ ਖ਼ਰਚਾ, ਪੂਰਾ ਭਰੋਸਾ',84,GOLD),W/2,1560,t,2.7)
    return c
def scene_receive(t,dur):
    ts=5.0+t; f=SRC['c_receive'].frame(ts); z=kb(t,dur,1.0,1.06); f=zoom(f,z)
    c=Image.fromarray(cv2.cvtColor(f,cv2.COLOR_BGR2RGB)).convert('RGBA')
    pop(c,T('ਮਾਂ ਦਾ ਭੇਜਿਆ ਪਿਆਰ…',86),W/2,250,t,0.3,t_out=2.3)
    pop(c,T('ਸੱਤ ਸਮੁੰਦਰ ਪਾਰ ❤️',96,GOLD),W/2,250,t,2.5)
    return c
def scene_cta(t,dur):
    ts=10.0+t; f=SRC['c_receive'].frame(ts); box=B(14,880,706,1262)
    f=glass(f,box,r=48,dark=0.6)
    z=kb(t,dur,1.0,1.03); f=zoom(f,z); c=Image.fromarray(cv2.cvtColor(f,cv2.COLOR_BGR2RGB)).convert('RGBA')
    bx0,by0=zp((box[0],box[1]),z); bx1,by1=zp((box[2],box[3]),z)
    cx=(bx0+bx1)/2; y=by0
    pop(c,T('ਅੱਜ ਹੀ ਆਓ 👇',86,GOLD),cx,y+85,t,0.15)
    for (s,t0,x) in [('ਫ਼ਰੀਦਕੋਟ',0.6,cx-300),('ਮੋਗਾ',0.85,cx-25),('ਮੁਕਤਸਰ',1.1,cx+250)]:
        pop(c,pill(s,58),x,y+215,t,t0)
    pop(c,T('ਜਾਂ ਫ਼ਰੀਦਕੋਟ ਡਾਕ ਮੰਡਲ ਦੇ ਕਿਸੇ ਵੀ ਡਾਕਘਰ',46),cx,y+335,t,1.6)
    pop(c,T('📍 India Post · Faridkot Postal Division',38,(235,235,235,255),font='latin'),cx,y+420,t,2.0)
    return c

SCENES=[('hook',scene_hook,3.30),('family',scene_family,6.60),('building',scene_building,4.95),('pack',scene_pack,2.50),
        ('counter',scene_counter,4.50),('globe',scene_globe,4.80),('receive',scene_receive,4.60),('cta',scene_cta,5.0)]

def flash(c,t,first):
    if first: return c
    a=clamp(1-t/0.12)*0.7
    if a>0: c.alpha_composite(Image.new('RGBA',c.size,(255,255,255,int(255*a))))
    return c
def render_scene(k):
    name,fn,dur=SCENES[k]; n=int(round(dur*FPS)); out=f'seg/s{k:02d}_{name}.mp4'
    p=subprocess.Popen(['ffmpeg','-v','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-',
        '-c:v','libx264','-preset','medium','-crf','18','-pix_fmt','yuv420p',out+'.tmp.mp4'],stdin=subprocess.PIPE)
    for i in range(n):
        t=i/FPS; c=fn(t,dur)
        if k>0 and t<0.2:  # punch-in on cut
            pz=1+0.06*(1-ease_out(t/0.2)); arr=np.asarray(c.convert('RGB')); arr=zoom(arr,pz); c=Image.fromarray(arr).convert('RGBA')
        c=flash(c,t,k==0)
        p.stdin.write(np.asarray(c.convert('RGB')).tobytes())
    p.stdin.close(); p.wait()
    import os; os.replace(out+'.tmp.mp4',out); print('seg',k,name,n)
if __name__=='__main__':
    import os; os.makedirs('seg',exist_ok=True)
    ks=[int(a) for a in sys.argv[1:]] or range(len(SCENES))
    if 'still' in os.environ:
        k=ks[0]; name,fn,dur=SCENES[k]
        for tt in [float(x) for x in os.environ['still'].split(',')]:
            fn(tt,dur).convert('RGB').save(f'seg/still_{k}_{tt:.2f}.jpg',quality=88)
    else:
        for k in ks: render_scene(k)
