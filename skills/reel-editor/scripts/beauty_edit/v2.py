# beauty_edit: beat-synced glam edit of a talking/posing clip: optical-flow slow motion, speed ramps, whip/zoom/spin/glitch/blur transitions, flashes, pink grade + bloom + bokeh, sharpening, script titles, before/after wipe, triptych, card, polaroids, voice-hook captions. Made with Claude, Nov 2026.
# Paths to inputs (videos, images, fonts, audio) are set near the top: edit them for a new reel.
import os, sys
import sys; sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from edit import *
O=5.6; T=O+15.69
B0=0.14; P=0.3455
BEATS=[O+B0+P*i for i in range(46)]
C=[O]+[O+B0+P*4*k for k in range(1,12)]+[T]
def srcc(st,z=1.0,cy=0.45,rot=0,dx=0): return to_canvas(src(st),z,0.5,cy,rot,dx)
def lerp(a,b,u): return a+(b-a)*min(max(u,0),1)
# ---------- hook
REC=text_sprite('REC',M8,40,(255,255,255),(255,60,60),4,0.3,shadow=0.4)
def hook(t,u):
    st=0.2+t; z=1.0
    if t>=1.8: z=1.12
    if t>=3.9: z=1.24
    c=to_canvas(src(st,False),z,0.5,0.4)
    g=c.mean(-1,keepdims=True); c=g*0.35+c*0.65
    return c
CAPS=[(0.3,1.75,['Guys','meri','baat','suno!']),(1.8,3.85,['Pink','suit','pehen','ke','aayi','hoon']),(3.9,5.5,['Par','mujhe','edit','banana','nahi','aata'])]
def caps(img,t):
    for t0,t1,ws in CAPS:
        if not (t0<=t<t1): continue
        f=F(M8,78); sp=f.getlength(' ')
        lines=[ws[:3],ws[3:]] if len(ws)>3 else [ws]
        for li,line in enumerate(lines):
            tot=sum(f.getlength(w) for w in line)+sp*(len(line)-1); x=(W-tot)/2; y=1340+li*110
            for wi,w in enumerate(line):
                idx=(0 if li==0 else 3)+wi; tw=t0+idx*(t1-t0-0.3)/len(ws)
                if t>=tw:
                    key=w.lower().strip('!')
                    hot=key in ('suno','pink','suit','edit','nahi')
                    spr=text_sprite(w,M8,78,(255,95,160) if hot else (255,255,255),(0,0,0),6,0.0,scol=(25,10,20),shadow=0.9,outline=5)
                    s=eob((t-tw)/0.22)
                    ww=f.getlength(w); paste(img,spr,x+ww/2,y,1.0,0.7+0.3*s)
                x+=f.getlength(w)+sp
# ---------- song scenes
LB=text_sprite('before',PF,70,(255,255,255),(0,0,0),6,0,shadow=0.9)
LA=text_sprite('after',GV,110,(255,240,248),(255,90,160),12,0.9)
def s_before_after(t,u):
    a=srcc(9.6+(t-C[0])*0.9,1.0); b=srcc(30.0+(t-C[0])*0.75,1.05)
    a=a.mean(-1,keepdims=True)*0.5+a*0.5
    x=int(W*(1-ease_io(max(0,(u-0.25)/0.7)))) if u>0.25 else W
    x=min(W,max(0,x)); c=a.copy(); c[:,x:]=b[:,x:]
    if 0<x<W: c[:,max(0,x-3):x+3]=255
    paste(c,LB,250,300,1.0 if x>320 else 0.0)
    paste(c,LA,min(W-200,x+220) if x<W else W+300,300,1.0)
    return c
def s_trip(t,u):
    bg=gblur(srcc(25.6+(t-C[2])*0.4,1.3),60)*0.55
    starts=[25.3,27.0,28.4]
    for i,s0 in enumerate(starts):
        tb=C[2]+i*P
        if t<tb: continue
        e=ease_out((t-tb)/0.3)
        p=src(s0+(t-tb)*0.6); pw=340; ph=1820
        z=ph/1280; img=cv2.resize(p,(int(720*z),ph)); x0=(img.shape[1]-pw)//2; img=img[:, x0:x0+pw]
        X=20+i*(pw+10); Y=50+int((1-e)*(300 if i%2==0 else -300))
        y0,y1=max(Y,0),min(Y+ph,H)
        bg[y0:y1,X:X+pw]=bg[y0:y1,X:X+pw]*(1-e)+img[y0-Y:y1-Y]*e
    return bg
def rounded_mask(w,h,r):
    m=np.zeros((h,w),np.float32); cv2.rectangle(m,(r,0),(w-r,h),1,-1); cv2.rectangle(m,(0,r),(w,h-r),1,-1)
    for cx,cy in [(r,r),(w-r,r),(r,h-r),(w-r,h-r)]: cv2.circle(m,(cx,cy),r,1,-1,cv2.LINE_AA)
    return m
CM=rounded_mask(860,1530,60)
def s_card(t,u):
    st=29.9+1.0*ramp_fs(u)
    bg=gblur(srcc(st,1.35),70)*0.7
    p=src(st); card=cv2.resize(p,(860,1530)) if False else cv2.resize(p,(int(720*1530/1280),1530))
    x0=(card.shape[1]-860)//2; card=card[:,x0:x0+860]
    e=eob(min(1,u*3)); s=0.85+0.15*e; ang=(1-ease_out(u*2))*-6
    c=np.zeros((H,W,3),np.float32); y=(H-1530)//2; xx0=(W-860)//2
    c[y:y+1530,xx0:xx0+860]=card
    m=np.zeros((H,W),np.float32); m[y:y+1530,xx0:xx0+860]=CM
    # border
    b=cv2.dilate(m,np.ones((15,15),np.uint8))
    M=cv2.getRotationMatrix2D((W/2,H/2),ang,s)
    c=cv2.warpAffine(c,M,(W,H)); m=cv2.warpAffine(m,M,(W,H))[...,None]; b=cv2.warpAffine(b,M,(W,H))[...,None]
    sh=cv2.GaussianBlur(b,(0,0),30)[...,None] if b.ndim==2 else cv2.GaussianBlur(b[...,0],(0,0),30)[...,None]
    out=bg*(1-sh*0.6)
    out=out*(1-b)+np.array([255,236,244],np.float32)*b
    out=out*(1-m)+c*m
    return out
def s_lips(t,u):
    c=srcc(32.4+1.3*u,1.0+0.08*u)
    for b in BEATS:
        if 0<=t-b<0.18: c=rgbsplit(c,16*(1-(t-b)/0.18))
    return c
POL=[(25.6,'pink',-9,290,620),(36.95,'suit',7,790,900),(40.5,'era',-4,460,1340)]
_pc={}
def polaroid(st,word):
    if st in _pc: return _pc[st]
    p=src(st,False); ph=cv2.resize(p,(420,int(420*1280/720)))[110:110+560]
    w,h=480,700; card=np.full((h,w,3),250,np.float32); card[30:30+560,30:30+420]=ph
    spr=text_sprite(word,GV,80,(200,60,110),(255,255,255),2,0.0,shadow=0.0)
    tmp=card.copy(); 
    rgb,a,sh=spr; hh,ww=a.shape; x=(w-ww)//2; y=600-hh//2+20
    y0=max(y,0); aa=a[y0-y:min(h-y,hh),:min(ww,w-x)][...,None]
    tmp[y0:y0+aa.shape[0],x:x+aa.shape[1]]=tmp[y0:y0+aa.shape[0],x:x+aa.shape[1]]*(1-aa)+rgb[y0-y:y0-y+aa.shape[0],:aa.shape[1]]*aa
    _pc[st]=tmp; return tmp
def s_pol(t,u):
    bg=gblur(srcc(31.0+(t-C[5])*0.8,1.2),45)*0.75
    for i,(st,wd,rot,cx,cy) in enumerate(POL):
        tb=C[5]+i*P*1.0
        if t<tb: continue
        e=eob((t-tb)/0.35); card=polaroid(st,wd)
        h,w=card.shape[:2]; pad=60
        big=np.zeros((h+2*pad,w+2*pad,3),np.float32); big[pad:pad+h,pad:pad+w]=card
        m=np.zeros((h+2*pad,w+2*pad),np.float32); m[pad:pad+h,pad:pad+w]=1
        s=1.6-0.6*e if e<1 else 1.0
        M=cv2.getRotationMatrix2D(((w+2*pad)/2,(h+2*pad)/2),rot+(1-min(e,1))*20,0.95*max(s,0.6))
        M[0,2]+=cx-(w+2*pad)/2; M[1,2]+=cy-(h+2*pad)/2
        cimg=cv2.warpAffine(big,M,(W,H)); mm=cv2.warpAffine(m,M,(W,H))
        sh=cv2.GaussianBlur(np.roll(mm,25,0),(0,0),18)[...,None]
        a=min(1,(t-tb)/0.12)
        bg=bg*(1-sh*0.5*a); bg=bg*(1-mm[...,None]*a)+cimg*mm[...,None]*a
    return bg
def s_mirror(t,u):
    st=37.4+1.2*u
    c=srcc(st,1.05)
    for k,(dt,al,z) in enumerate([(0.25,0.35,1.08),(0.5,0.2,1.16)]):
        g=srcc(max(37.4,st-dt),z); c=c*(1-al)+np.maximum(c,g)*al
    return c
TI1=text_sprite('Pink Suit',PF,120,(255,250,252),(255,90,160),14,0.8)
TI2=text_sprite('glow up',GV,190,(255,200,225),(255,80,150),18,1.0)
HAND=text_sprite('edit by @aitricksbysumit',M6,38,(255,240,248),(255,110,170),8,0.6)
segs=[Seg(0,O,0,0,tr='flash')]; segs[0].draw=hook
def mk(i,draw=None,**kw):
    s=Seg(C[i],C[i+1],kw.pop('s0',0),kw.pop('s1',0),**kw)
    if draw: s.draw=draw
    segs.append(s)
mk(0,s_before_after,tr='glitch')
mk(1,s0=22.0,s1=25.05,ease=ramp_sf,z0=1.0,z1=1.1,tr='zoom',mb=True)
mk(2,s_trip,tr='whip')
mk(3,s_card,tr='zoom')
mk(4,s_lips,tr='flash')
mk(5,s_pol,tr='whip')
mk(6,s0=34.2,s1=35.45,ease=ramp_fs,z0=1.0,z1=1.12,tr='glitch')
mk(7,s0=35.9,s1=37.25,ease=ramp_fs,z0=1.12,z1=1.0,tr='flash')
mk(8,s_mirror,tr='spin')
mk(9,s0=38.6,s1=39.9,z0=1.0,z1=1.08,tr='whip')
mk(10,s0=39.95,s1=41.2,ease=ramp_fs,z0=1.0,z1=1.1,tr='blur')
mk(11,s0=41.5,s1=43.0,z0=1.1,z1=1.0,tr='flash')
FL=[C[4],C[7],C[11]]
def frame(t):
    img=render_segments(segs,t,BEATS if t>=O else [])
    if t<O:
        img=sharpen(img)*VIG; img=grain(img,t,3)
        caps(img,t)
        if int(t*2)%2==0: cv2.circle(img,(80,140),14,(255,40,40),-1,cv2.LINE_AA)
        paste(img,REC,150,140,1.0)
        if t>O-0.4: img=glitch(img,t,(t-(O-0.4))/0.4)
    else:
        img=flashes(img,t,FL+[O])
        img=finish(img,t,0.28,1.0,1.0)
        if t>=C[10]+0.2:
            v=t-C[10]-0.2
            paste(img,TI1,540,1330,ease_out(v/0.35),1.0,reveal=min(1,v/0.6))
            paste(img,TI2,560,1480,ease_out((v-0.3)/0.4),1.0+0.02*math.sin(t*4),reveal=min(1,(v-0.3)/0.8))
            paste(img,HAND,540,1650,ease_out((v-0.8)/0.4)*0.95)
    if t>T-0.35: img=flash(img,(t-(T-0.35))/0.35,(255,240,248))
    if t<0.1: img=img*(t/0.1)
    return np.clip(img,0,255).astype(np.uint8)
if __name__=='__main__':
    ts=[float(x) for x in sys.argv[1:]]
    ims=[Image.fromarray(frame(t)).resize((270,480)) for t in ts]
    cols=min(8,len(ims)); rows=(len(ims)+cols-1)//cols
    M=Image.new('RGB',(cols*270,rows*480))
    for i,im in enumerate(ims): M.paste(im,((i%cols)*270,(i//cols)*480))
    M.save('/home/claude/girl/prev2.png')
