# beauty_edit: beat-synced glam edit of a talking/posing clip: optical-flow slow motion, speed ramps, whip/zoom/spin/glitch/blur transitions, flashes, pink grade + bloom + bokeh, sharpening, script titles, before/after wipe, triptych, card, polaroids, voice-hook captions. Made with Claude, Nov 2026.
# Paths to inputs (videos, images, fonts, audio) are set near the top: edit them for a new reel.
import numpy as np, cv2, math, random
from PIL import Image, ImageDraw, ImageFont, ImageFilter
W,H=1080,1920; FPS=30
NF=1380
_fc={}
def frame_i(i):
    i=int(min(max(i,0),NF-1))
    if i in _fc: return _fc[i]
    if len(_fc)>90: _fc.pop(next(iter(_fc)))
    a=cv2.imread(f'/home/claude/girl/fr/{i+1:05d}.jpg')[:,:,::-1].astype(np.float32)
    _fc[i]=a; return a
_flow=cv2.DISOpticalFlow_create(cv2.DISOPTICAL_FLOW_PRESET_MEDIUM)
_flc={}
def flowpair(i):
    if i in _flc: return _flc[i]
    a=cv2.cvtColor(frame_i(i).astype(np.uint8),cv2.COLOR_RGB2GRAY); b=cv2.cvtColor(frame_i(i+1).astype(np.uint8),cv2.COLOR_RGB2GRAY)
    s=0.5; a=cv2.resize(a,None,fx=s,fy=s); b=cv2.resize(b,None,fx=s,fy=s)
    f1=_flow.calc(a,b,None); f2=_flow.calc(b,a,None)
    f1=cv2.resize(f1,(720,1280))/s; f2=cv2.resize(f2,(720,1280))/s
    if len(_flc)>20: _flc.pop(next(iter(_flc)))
    _flc[i]=(f1,f2); return _flc[i]
gx,gy=np.meshgrid(np.arange(720,dtype=np.float32),np.arange(1280,dtype=np.float32))
def src(t,interp=True):
    x=t*FPS; i=int(math.floor(x)); f=x-i
    if not interp or f<0.06: return frame_i(i)
    if f>0.94: return frame_i(i+1)
    f1,f2=flowpair(i)
    A=cv2.remap(frame_i(i),gx-f2[...,0]*f,gy-f2[...,1]*f,cv2.INTER_LINEAR,borderMode=cv2.BORDER_REFLECT)
    B=cv2.remap(frame_i(i+1),gx-f1[...,0]*(1-f),gy-f1[...,1]*(1-f),cv2.INTER_LINEAR,borderMode=cv2.BORDER_REFLECT)
    return A*(1-f)+B*f
def src_blur(t,spd):
    # motion blur for fast segments: average several sub-frames
    n=max(1,min(5,int(spd)))
    if n==1: return src(t)
    acc=0
    for k in range(n): acc=acc+frame_i(int((t)*FPS)-k)
    return acc/n
def to_canvas(img,zoom=1.0,cx=0.5,cy=0.45,rot=0.0,dx=0,dy=0):
    s=W/720*zoom
    M=cv2.getRotationMatrix2D((360*1.0,1280*cy),rot,s)
    M[0,2]+=W/2-360+dx; M[1,2]+=H*cy-1280*cy+dy
    M[0,2]+= -(cx-0.5)*720*s
    return cv2.warpAffine(img,M,(W,H),flags=cv2.INTER_CUBIC,borderMode=cv2.BORDER_REFLECT)
yy,xx=np.mgrid[0:H,0:W].astype(np.float32)
VIG=(1-0.45*np.clip(np.sqrt(((xx-W/2)/(W/2))**2+((yy-H/2)/(H/2))**2)-0.5,0,1)**1.5)[...,None]
def grade(img,warm=1.0,sat=1.12,pink=0.6,lift=6):
    a=img/255.0
    a=a*(1-lift/255)+lift/255*np.array([0.55,0.32,0.45])  # plum lift
    a=np.clip(a,0,1); a=a*a*(3-2*a)*0.35+a*0.65  # soft S
    g=a.mean(-1,keepdims=True); a=g+(a-g)*sat
    a=a*np.array([1.02,0.985,1.0+0.03*pink])
    return np.clip(a*255,0,255)
def bloom(img,th=215,k=0.12,r=18):
    b=np.clip(img-th,0,255)*(255/(255-th))
    b=cv2.resize(b,(W//4,H//4)); b=cv2.GaussianBlur(b,(0,0),r/4); b=cv2.resize(b,(W,H))
    return img+b*k*np.array([1.0,0.82,0.9],np.float32)
_gr=np.random.default_rng(1).normal(0,1,(H//2,W//2)).astype(np.float32)
def grain(img,t,amt=5):
    o=int(t*997)%200
    g=np.roll(_gr,o,axis=0); g=cv2.resize(g,(W,H),interpolation=cv2.INTER_NEAREST)
    return img+g[...,None]*amt
def leak(t,col=(255,90,150),k=0.35,sp=0.4,seed=0):
    cx=W*(0.5+0.6*math.sin(t*sp+seed)); cy=H*(0.3+0.4*math.sin(t*sp*0.7+seed*2))
    d=((xx-cx)/(W*0.6))**2+((yy-cy)/(H*0.4))**2
    return np.exp(-d)[...,None]*np.array(col,np.float32)*k
# particles: pink bokeh + sparkles
R=np.random.default_rng(9); NB=40
BX=R.uniform(0,W,NB); BY=R.uniform(0,H,NB); BR=R.uniform(10,46,NB); BV=R.uniform(15,60,NB); BP=R.uniform(0,6.28,NB)
def bokeh(t,k=1.0):
    lay=np.zeros((H//4,W//4,3),np.float32)
    for i in range(NB):
        y=(BY[i]-BV[i]*t)%H; x=(BX[i]+20*math.sin(t*0.8+BP[i]))%W
        a=(0.5+0.5*math.sin(t*1.3+BP[i]))*0.8
        cv2.circle(lay,(int(x/4),int(y/4)),max(1,int(BR[i]/4)),(255*a,140*a,200*a),-1,cv2.LINE_AA)
    lay=cv2.GaussianBlur(lay,(0,0),1.6); return cv2.resize(lay,(W,H))*k*0.38
NS=60; SX=R.uniform(0,W,NS); SY=R.uniform(0,H,NS); SP=R.uniform(0,6.28,NS); SF=R.uniform(1.5,4,NS)
def sparkles(t,k=1.0,region=None):
    lay=np.zeros((H//2,W//2,3),np.float32)
    for i in range(NS):
        a=max(0,math.sin(t*SF[i]+SP[i]))**6
        if a<0.05: continue
        x,y=int(SX[i]/2),int((SY[i]-t*20)%H/2); L=int(4+10*a)
        c=(255*a,230*a,245*a)
        cv2.line(lay,(x-L,y),(x+L,y),c,1,cv2.LINE_AA); cv2.line(lay,(x,y-L),(x,y+L),c,1,cv2.LINE_AA)
        cv2.circle(lay,(x,y),2,c,-1,cv2.LINE_AA)
    lay=lay+cv2.GaussianBlur(lay,(0,0),2)*2
    return cv2.resize(lay,(W,H))*k
# transitions
def flash(img,p,col=(255,240,248)):
    return img*(1-p)+np.array(col,np.float32)*p
def dirblur(img,k,horiz=True):
    k=int(k)
    if k<3: return img
    small=cv2.resize(img,(W//2,H//2)); small=cv2.blur(small,(k//2,1) if horiz else (1,k//2))
    return cv2.resize(small,(W,H))
def zoomblur(img,amt):
    if amt<0.01: return img
    acc=img.copy(); n=6
    for i in range(1,n):
        s=1+amt*i/n; M=cv2.getRotationMatrix2D((W/2,H/2),0,s)
        acc+=cv2.warpAffine(img,M,(W,H),borderMode=cv2.BORDER_REFLECT)
    return acc/n
def rgbsplit(img,d):
    d=int(d)
    if d<1: return img
    o=img.copy(); o[:,:,0]=np.roll(img[:,:,0],d,1); o[:,:,2]=np.roll(img[:,:,2],-d,1); return o
def glitch(img,t,k):
    o=rgbsplit(img,18*k); rng=random.Random(int(t*60))
    for i in range(int(10*k)):
        y=rng.randrange(0,H-120); h=rng.randrange(10,120); o[y:y+h]=np.roll(o[y:y+h],rng.randrange(-90,90),1)
    return o
def gblur(img,s):
    if s<0.5: return img
    small=cv2.resize(img,(W//4,H//4)); small=cv2.GaussianBlur(small,(0,0),s/4); return cv2.resize(small,(W,H))
# text
_tc={}
def F(p,s): return ImageFont.truetype(p,s)
def text_sprite(txt,font,size,col=(255,255,255),glow=(255,120,180),gr=14,ga=0.9,stroke=0,scol=(0,0,0),shadow=0.5,outline=0):
    k=(txt,font,size,col,glow,gr,ga,stroke,shadow,outline)
    if k in _tc: return _tc[k]
    f=F(font,size); bb=f.getbbox(txt,stroke_width=stroke); pad=gr*3
    w=bb[2]-bb[0]+2*pad; h=bb[3]-bb[1]+2*pad
    m=Image.new('L',(w,h),0); ImageDraw.Draw(m).text((pad-bb[0],pad-bb[1]),txt,font=f,fill=255,stroke_width=stroke,stroke_fill=255)
    m=np.asarray(m).astype(np.float32)/255
    g=cv2.GaussianBlur(m,(0,0),gr)*ga; sh=cv2.GaussianBlur(m,(0,0),6)*shadow
    rgb=np.array(glow,np.float32)*np.clip(g,0,1)[...,None]
    rgb=rgb*(1-m[...,None])+np.array(col,np.float32)*m[...,None]
    a=np.clip(m+g,0,1)
    if outline:
        o=cv2.dilate(m,cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(2*outline+1,2*outline+1)))
        rgb=rgb*m[...,None]+np.array(scol,np.float32)*(1-m[...,None])*(o>0)[...,None]+rgb*(1-m[...,None])*(o<=0)[...,None]
        a=np.maximum(a,o)
    _tc[k]=(rgb,a,sh); return _tc[k]
def paste(fr,spr,cx,cy,alpha=1.0,scale=1.0,reveal=1.0):
    rgb,a,sh=spr
    if scale!=1.0:
        rgb=cv2.resize(rgb,None,fx=scale,fy=scale); a=cv2.resize(a,None,fx=scale,fy=scale); sh=cv2.resize(sh,None,fx=scale,fy=scale)
    h,w=a.shape
    if reveal<1.0:
        edge=reveal*(w*1.25); ramp=np.clip((edge-np.arange(w))/(w*0.25),0,1).astype(np.float32)
        a=a*ramp[None,:]; sh=sh*ramp[None,:]
    x=int(cx-w/2); y=int(cy-h/2)
    x0,y0=max(x,0),max(y,0); x1,y1=min(x+w,W),min(y+h,H)
    if x1<=x0 or y1<=y0 or alpha<=0: return
    aa=a[y0-y:y1-y,x0-x:x1-x,None]*alpha; ss=sh[y0-y:y1-y,x0-x:x1-x,None]*alpha
    reg=fr[y0:y1,x0:x1]; reg*=1-ss*0.6
    reg[:]=reg*(1-aa)+rgb[y0-y:y1-y,x0-x:x1-x]*aa
def heart_sprite(size=60,col=(255,110,170)):
    k=('heart',size,col)
    if k in _tc: return _tc[k]
    S=size*4; m=Image.new('L',(S,S),0); d=ImageDraw.Draw(m)
    r=S//4; d.ellipse([S//2-2*r,S//4,S//2,S//4+2*r],fill=255); d.ellipse([S//2,S//4,S//2+2*r,S//4+2*r],fill=255)
    d.polygon([(S//2-2*r+4,S//4+r+10),(S//2+2*r-4,S//4+r+10),(S//2,S-S//8)],fill=255)
    m=m.resize((size+40,size+40),Image.LANCZOS); m=np.asarray(m).astype(np.float32)/255
    g=cv2.GaussianBlur(m,(0,0),8)*0.8
    rgb=np.array(col,np.float32)*np.clip(m+g,0,1)[...,None]
    _tc[k]=(rgb,np.clip(m+g*0.7,0,1),m*0); return _tc[k]
def ease_out(u): u=min(max(u,0),1); return 1-(1-u)**3
def ease_io(u): u=min(max(u,0),1); return u*u*(3-2*u)
def eob(u):
    u=min(max(u,0),1); c1=1.70158; c3=c1+1; return 1+c3*(u-1)**3+c1*(u-1)**2

def sharpen(img,amt=0.7,r=1.3):
    small=cv2.GaussianBlur(img,(0,0),r)
    return img+(img-small)*amt
