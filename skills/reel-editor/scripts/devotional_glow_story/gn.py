# devotional_glow_story: narration part (word-by-word golden glow captions from Whisper timings, Ken Burns, particles, light leaks, tanpura drone + temple bells) then a shabad/aarti part with big Hinglish meaning text. Made with Claude, Nov 2026.
# Paths to inputs (videos, images, fonts, audio) are set near the top: edit them for a new reel.
import numpy as np, cv2, math, json, sys, random, re
from PIL import Image, ImageDraw, ImageFont, ImageFilter
W,H=1080,1920; FPS=30
P1=37.45; P2=36.82; T=P1+P2
CORM='/home/claude/gn/corm600.ttf'; CORMI='/home/claude/gn/corm500i.ttf'; CIN='/home/claude/gn/cinzel700.ttf'
A=lambda n: f'/home/claude/gn/A/{n}'
B=lambda n: f'/home/claude/gn/B/{n}'
import glob
AF=sorted(glob.glob('/home/claude/gn/A/*.jpg')); BF=sorted(glob.glob('/home/claude/gn/B/*.jpg'))
# scenes: (t0,t1,img,zoom0,zoom1,px,py)
S1=[(0.0,3.26,AF[0],1.12,1.0,0,0.3),(3.26,7.42,AF[1],1.0,1.1,0.3,0),(7.42,10.28,AF[2],1.0,1.1,0,-0.3),(10.28,15.16,AF[3],1.1,1.0,-0.3,0),
    (15.16,21.88,AF[4],1.0,1.14,0,0.5),(21.88,26.02,AF[5],1.12,1.0,0,-0.3),(26.02,28.52,AF[6],1.0,1.1,0.3,0),(28.52,33.20,AF[7],1.0,1.12,-0.3,0.2),(33.20,P1,AF[8],1.0,1.12,0,0.4)]
o=P1
S2=[(o+0.0,o+2.6,BF[0],1.0,1.08,0,0.3),(o+2.6,o+4.3,BF[1],1.0,1.08,0,0),(o+4.3,o+6.1,BF[2],1.08,1.0,0,0.2),(o+6.1,o+12.6,BF[3],1.0,1.14,0.2,0.3),
    (o+12.6,o+15.1,BF[4],1.0,1.1,0,0),(o+15.1,o+18.6,BF[5],1.1,1.0,0.3,0),(o+18.6,o+24.1,BF[6],1.0,1.12,-0.2,0),(o+24.1,o+27.1,BF[7],1.0,1.1,0,0.3),
    (o+27.1,o+31.1,BF[7],1.12,1.02,0.3,-0.3),(o+31.1,T,BF[0],1.1,1.0,0,0.5)]
SC=S1+S2; XF=0.7
_im={}
def img(p):
    if p not in _im:
        a=cv2.cvtColor(cv2.imread(p),cv2.COLOR_BGR2RGB); a=cv2.resize(a,(W,H),interpolation=cv2.INTER_AREA)
        _im[p]=a.astype(np.float32)
    return _im[p]
def kb(sc,t):
    t0,t1,p,z0,z1,px,py=sc; u=min(max((t-t0+XF)/(t1-t0+2*XF),0),1)
    u=u*u*(3-2*u); z=z0+(z1-z0)*u
    cw,ch=W/z,H/z; cx=W/2+px*(W-cw)/2*(2*u-1); cy=H/2+py*(H-ch)/2*(2*u-1)
    M=np.array([[z,0,-(cx-cw/2)*z],[0,z,-(cy-ch/2)*z]],np.float32)
    return cv2.warpAffine(img(p),M,(W,H),flags=cv2.INTER_LINEAR,borderMode=cv2.BORDER_REFLECT)
yy,xx=np.mgrid[0:H,0:W]
VIG=(1-0.42*np.clip(np.sqrt(((xx-W/2)/(W/2))**2+((yy-H*0.48)/(H/2))**2)-0.45,0,1)**1.4).astype(np.float32)[...,None]
GRAD=np.clip((yy-H*0.55)/(H*0.45),0,1).astype(np.float32)[...,None]  # bottom darkening for text
def bg(t):
    act=[s for s in SC if s[0]-XF<=t<s[1]+XF]
    out=None; wsum=0
    for s in act:
        w=min(1,max(0,(t-(s[0]-XF))/(2*XF)) if s[0]>0 else 1)*min(1,max(0,((s[1]+XF)-t)/(2*XF)) if s[1]<T-0.01 else 1)
        # smoother: cross dissolve
        f=kb(s,t)
        out=f*w if out is None else out+f*w; wsum+=w
    out=out/max(wsum,1e-3)
    # warm grade
    out=out*np.array([1.04,1.0,0.93],np.float32)
    out=out*VIG*(1-0.38*GRAD)
    return out
# particles
rng=np.random.default_rng(5)
NP=110
PX=rng.uniform(0,W,NP); PY=rng.uniform(0,H,NP); PV=rng.uniform(12,45,NP); PS=rng.uniform(1.2,3.6,NP); PH=rng.uniform(0,6.28,NP); PD=rng.uniform(-10,10,NP)
def particles(t):
    lay=np.zeros((H//2,W//2,3),np.float32)
    for i in range(NP):
        y=(PY[i]-PV[i]*t)%H; x=(PX[i]+PD[i]*t+18*math.sin(t*0.6+PH[i]))%W
        a=0.5+0.5*math.sin(t*1.7+PH[i])
        cv2.circle(lay,(int(x/2),int(y/2)),max(1,int(PS[i])),(255*a,200*a,110*a),-1,cv2.LINE_AA)
    g=cv2.GaussianBlur(lay,(0,0),2.2)*1.6+lay*0.6
    return cv2.resize(g,(W,H),interpolation=cv2.INTER_LINEAR)
def leak(t):
    cx=W*(0.5+0.45*math.sin(t*0.21)); cy=H*(0.25+0.15*math.sin(t*0.17+1))
    d=((xx-cx)/(W*0.7))**2+((yy-cy)/(H*0.45))**2
    return (np.exp(-d)[...,None]*np.array([60,30,5],np.float32)*(0.6+0.4*math.sin(t*0.5)))
# ---------- text sprites
_fc={}
def F(p,s):
    if (p,s) not in _fc: _fc[(p,s)]=ImageFont.truetype(p,s)
    return _fc[(p,s)]
def sprite(txt,font,size,col,glow=(255,190,90),gr=14,ga=0.9,track=0):
    f=F(font,size)
    if track:
        ws=[f.getlength(c) for c in txt]; tw=int(sum(ws)+track*(len(txt)-1))
    else: tw=int(f.getlength(txt))
    asc,desc=f.getmetrics(); pad=gr*3
    w=tw+pad*2; h=asc+desc+pad*2
    m=Image.new('L',(w,h),0); d=ImageDraw.Draw(m)
    if track:
        x=pad
        for c,cw in zip(txt,ws): d.text((x,pad),c,font=f,fill=255); x+=cw+track
    else: d.text((pad,pad),txt,font=f,fill=255)
    m=np.asarray(m).astype(np.float32)/255
    g=cv2.GaussianBlur(m,(0,0),gr)*ga
    g2=cv2.GaussianBlur(m,(0,0),gr/3)*0.5
    rgb=np.zeros((h,w,3),np.float32)
    gl=np.clip(g+g2,0,1)
    rgb=np.array(glow,np.float32)*gl[...,None]
    # text fill with vertical gradient
    if isinstance(col,tuple) and len(col)==2:
        c0,c1=np.array(col[0],np.float32),np.array(col[1],np.float32)
        gy=np.linspace(0,1,h)[:,None,None]; fill=c0*(1-gy)+c1*gy
    else: fill=np.array(col,np.float32)[None,None,:]*np.ones((h,1,1))
    a=np.clip(m+gl*0.85,0,1)
    out=(fill*m[...,None]+rgb*(1-m[...,None]))
    sh=cv2.GaussianBlur(m,(0,0),5)*0.75
    return out,a,pad,sh
def comp(fr,spr,x,y,alpha,blend='normal'):
    rgb,a,pad,sh=spr; h,w=a.shape; x=int(x)-pad; y=int(y)-pad
    x0,y0=max(x,0),max(y,0); x1,y1=min(x+w,W),min(y+h,H)
    if x1<=x0 or y1<=y0 or alpha<=0.003: return
    aa=a[y0-y:y1-y,x0-x:x1-x,None]*alpha; cc=rgb[y0-y:y1-y,x0-x:x1-x]
    reg=fr[y0:y1,x0:x1]
    ss=sh[y0-y:y1-y,x0-x:x1-x,None]*alpha
    reg[:]=reg*(1-ss*0.8)
    reg[:]=reg*(1-aa)+cc*aa
# ---------- part 1 lines
WJ=json.load(open('/home/claude/gn/vo_words.json'))
WW=[w for s in WJ for w in s['words']]
L1=[(0.00,1.78,"Jagannath Puri ka vishaal mandir"),(1.78,3.26,"Aarti ka samay tha"),(3.26,5.02,"Ghante ghadiyaal baj rahe the"),
(5.02,7.42,"Aur hazaaron log haath jodkar khade the"),(7.42,10.28,"Kehte hain, Guru Nanak Dev Ji bahar hi baithe rahe"),
(10.28,11.40,"Kisi ne poochha"),(11.80,14.02,"Baba ji, sab aarti mein shaamil hain"),(14.04,15.12,"Aap andar kyon nahi aaye?"),
(15.16,17.72,"Guru Nanak Dev Ji ne aasmaan ki or dekha"),(17.76,19.6,"Zara upar dekho"),(20.04,21.88,"Aarti toh poori kaaynaat kar rahi hai"),
(21.88,23.64,"Aakash hi thaal hai"),(23.64,26.02,"Suraj aur chaand uske deepak hain"),(26.02,28.52,"Taare us thaal mein saje moti hain"),
(28.52,30.14,"Hawa... paani..."),(30.14,33.20,"Saari kudrat usi Parmatma ki aarti kar rahi hai"),(33.20,37.30,"Aur phir Guru Nanak Dev Ji ne usi aarti ko shabad diye")]
GOLD={'aarti','guru','nanak','dev','ji','thaal','suraj','chaand','taare','moti','kudrat','parmatma','shabad','aasmaan','kaaynaat','deepak','aakash','upar'}
SZ=84; MAXW=960
LINES=[]
for (s,e,txt) in L1:
    ws=txt.split(' ')
    wt=[w for w in WW if s-0.05<=w[0]<e]
    ts=[]
    for i in range(len(ws)):
        if wt:
            k=min(len(wt)-1,int(i*len(wt)/len(ws))); ts.append(wt[k][0])
        else: ts.append(s+(e-s)*i/len(ws))
    ts=sorted(ts)
    f=F(CORM,SZ); sp=f.getlength(' ')
    rows=[[]]; cw=0
    for w in ws:
        lw=f.getlength(w)
        if rows[-1] and cw+sp+lw>MAXW: rows.append([]); cw=0
        rows[-1].append(w); cw+=(sp if cw else 0)+lw
    place=[]; idx=0
    nrow=len(rows); base_y=1440-(nrow-1)*52
    for r,row in enumerate(rows):
        rw=sum(f.getlength(w) for w in row)+sp*(len(row)-1); x=(W-rw)/2
        for w in row:
            key=re.sub(r'[^a-z]','',w.lower())
            col=((255,236,190),(232,180,90)) if key in GOLD else ((255,255,255),(238,232,220))
            spr=sprite(w,CORM,SZ,col,glow=(255,170,60) if key in GOLD else (255,200,140),gr=12,ga=0.75 if key in GOLD else 0.45)
            place.append((spr,x,base_y+r*104,ts[idx])); x+=f.getlength(w)+sp; idx+=1
    LINES.append((s,e,place))
def draw_p1(fr,t):
    for li,(s,e,place) in enumerate(LINES):
        nxt=LINES[li+1][0] if li+1<len(LINES) else P1
        end=min(nxt,e+0.6)
        if not (s-0.1<=t<=end+0.3): continue
        out=1-min(1,max(0,(t-end)/0.3))
        for spr,x,y,tw in place:
            if t<tw-0.02: continue
            p=min(1,(t-tw+0.02)/0.35); p=1-(1-p)**3
            comp(fr,spr,x,y+(1-p)*18,p*out)
# ---------- part 2 shabad
L2=[(0.0,2.6,"Gagan mai thaal","Poora aasmaan hi aarti ki thaali hai"),
(2.6,6.1,"Rav chand deepak bane","Suraj aur chaand uske diye hain"),
(6.1,12.6,"Taarika mandal janak moti","Taare us thaali mein jade moti hain"),
(12.6,15.1,"Dhoop malaanlo","Chandan ki khushboo hi dhoop hai"),
(15.1,18.6,"Pavan chavaro kare","Hawa chanwar jhula rahi hai"),
(18.6,24.1,"Sagal banrai phoolant joti","Saare van tujh par phool chadha rahe hain, Prabhu"),
(24.1,27.1,"Kaisi aarti hoe","Kitni anokhi aarti ho rahi hai!"),
(27.1,31.1,"Bhav khandana teri aarti","Hey bhay mitaane wale, ye teri aarti hai"),
(31.1,P2,"Anhata shabad vaajant bheri","Anhad naad ke nagaade baj rahe hain")]
SH=[]
MS=98
for s_,e,g,mn in L2:
    gs=sprite(g.upper(),CIN,46,((255,236,200),(225,175,85)),glow=(255,160,50),gr=10,ga=0.6,track=5)
    f=F(CORM,MS); words=mn.split(' '); rows=[]; cur=''
    for w in words:
        test=(cur+' '+w).strip()
        if f.getlength(test)>980 and cur: rows.append(cur); cur=w
        else: cur=test
    rows.append(cur)
    ms=[sprite(r,CORM,MS,((255,246,225),(240,200,120)),glow=(255,170,60),gr=14,ga=0.7) for r in rows]
    SH.append((o+s_,o+e,gs,ms))
HDR=sprite('A A R T I',CIN,40,((255,236,200),(230,190,110)),glow=(255,170,60),gr=10,ga=0.6)
HDR1=sprite('Jagannath Puri',CORMI,46,(250,240,225),glow=(255,190,120),gr=8,ga=0.4)
HND=sprite('@aitricksbysumit',CORMI,40,(250,240,225),glow=(255,190,120),gr=6,ga=0.3)
def draw_p2(fr,t):
    for s_,e,gs,ms in SH:
        if not (s_-0.05<=t<=e+0.05): continue
        q=1-min(1,max(0,(t-(e-0.45))/0.45)) if e<T-0.01 else 1
        n=len(ms); y0=1300-(n-1)*55
        pg=min(1,(t-s_)/0.6); pg=1-(1-pg)**3
        w=gs[1].shape[1]-2*gs[2]; comp(fr,gs,(W-w)/2,y0-105+(1-pg)*14,pg*q*0.95)
        for i,spr in enumerate(ms):
            w=spr[1].shape[1]-2*spr[2]
            pi_=min(1,max(0,(t-s_-0.15-i*0.2)/0.7)); pi_=1-(1-pi_)**3
            comp(fr,spr,(W-w)/2,y0+i*122+(1-pi_)*24,pi_*q)
def frame(t):
    fr=bg(t)
    fr=fr+particles(t)*(0.55 if t<P1 else 0.8)+leak(t)*0.6
    if t<P1:
        if t<3.4:
            a=min(1,t/0.8)*(1-min(1,max(0,(t-2.8)/0.6)))
            w=HDR1[1].shape[1]-2*HDR1[2]; comp(fr,HDR1,(W-w)/2,170,a)
        draw_p1(fr,t)
    else:
        a=min(1,(t-P1)/1.0)
        w=HDR[1].shape[1]-2*HDR[2]; comp(fr,HDR,(W-w)/2,160,a*0.9)
        draw_p2(fr,t)
        if t>T-4: 
            w=HND[1].shape[1]-2*HND[2]; comp(fr,HND,(W-w)/2,1780,min(1,(t-(T-4))/0.8)*0.8)
    if t<0.6: fr=fr*(t/0.6)
    if t>T-0.8: fr=fr*max(0,(T-t)/0.8)
    # transition glow flash at part change
    d=abs(t-P1)
    if d<0.5: fr=fr+(1-d/0.5)**2*np.array([150,115,60],np.float32)
    return np.clip(fr,0,255).astype(np.uint8)
if __name__=='__main__':
    ts=[float(x) for x in sys.argv[1:]]
    ims=[Image.fromarray(frame(t)).resize((360,640)) for t in ts]
    cols=min(6,len(ims)); rows=(len(ims)+cols-1)//cols
    M=Image.new('RGB',(cols*360,rows*640))
    for i,im in enumerate(ims): M.paste(im,((i%cols)*360,(i//cols)*640))
    M.save('/home/claude/gn/prev.png')
