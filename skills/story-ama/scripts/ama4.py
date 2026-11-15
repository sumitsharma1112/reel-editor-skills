import numpy as np, cv2, subprocess, math, sys, os
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import ama3
from ama3 import W,H,F,MS,ease,back,CZ,fit_h,with_shadow,text_c
FPS=30; DUR=14.0
HOOK=1.8; BEAT=1.6; NB=5; FIN0=HOOK+NB*BEAT   # 9.8
yy,xx=np.mgrid[0:H,0:W].astype(np.float32)
def grad_bg(c1,c2,glows,seed=0):
    t=(yy/H)[...,None]; b=np.array(c1,np.float32)*(1-t)+np.array(c2,np.float32)*t
    for (cx,cy,r,col,a) in glows:
        d=np.hypot(xx-cx,yy-cy)/r; b=b+np.exp(-d*d)[...,None]*np.array(col)*a
    b=b+np.random.default_rng(seed).normal(0,2.5,(H,W,1))
    return Image.fromarray(np.clip(b,0,255).astype(np.uint8)).convert('RGBA')
BGS=[grad_bg((34,20,12),(14,8,6),[(540,700,600,(255,150,50),0.35)],1),
     grad_bg((22,52,40),(10,26,20),[(540,600,600,(252,207,0),0.18)],2),
     grad_bg((18,18,22),(8,8,10),[(540,640,560,(230,30,40),0.22)],3),
     grad_bg((60,16,70),(20,8,40),[(300,500,600,(255,60,160),0.30),(900,1400,600,(120,60,255),0.30)],4),
     grad_bg((2,6,12),(0,0,0),[(540,900,600,(0,200,255),0.22)],5)]
AVH=820
AVS={k:with_shadow(fit_h(CZ(k),AVH)) for k in ['avatar_thinking_question','avatar_reading_book','avatar_laptop_ai','avatar_phone_recording','avatar_mic_voiceover']}
PR={'prop_storybook':fit_h(CZ('prop_storybook'),260),'prop_book_stack':fit_h(CZ('prop_book_stack'),330),
    'prop_retro_tv_play':fit_h(CZ('prop_retro_tv_play'),330),'prop_phone_tripod':fit_h(CZ('prop_phone_tripod'),400),
    'prop_chat_bubble':fit_h(CZ('prop_chat_bubble'),200)}
PRS={k:with_shadow(v,14,(6,10),110) for k,v in PR.items()}
def put(im,spr,x,y,alpha=1.0,rot=0,scale=1.0):
    s=spr
    if scale!=1.0: s=s.resize((max(1,int(s.width*scale)),max(1,int(s.height*scale))),Image.BICUBIC)
    if rot: s=s.rotate(rot,resample=Image.BICUBIC,expand=True)
    if alpha<1: s=s.copy(); s.putalpha(s.split()[3].point(lambda v:int(v*alpha)))
    im.alpha_composite(s,(int(x-s.width/2),int(y-s.height)))  # anchor bottom-centre
def avatar_in(im,key,u,side):
    p=back(min(1,max(0,(u-0.05)/0.45)))
    if p<=0: return
    s=AVS[key]; x0=W+s.width/2 if side>0 else -s.width/2; x1=760 if side>0 else 300
    x=x0+(x1-x0)*p; put(im,s,x,1760+4*math.sin(u*5))
def prop_in(im,key,u,x,y,t0=0.25):
    p=(u-t0)/0.35
    if p<=0: return
    sc=back(min(1,p)); put(im,PRS[key],x,y,1,rot=8*(1-min(1,p))*(-1)+3*math.sin(u*4),scale=max(0.05,sc))
def kicker(d,n,y=330,col=(255,255,255)):
    f=F('SpaceMono-Bold.ttf',38); text_c(d,f'SAWAAL #{n}',540,y,f,col+(230,))
# ---------- beat 1: STORIES (storybook / parchment, serif page-wipe) ----------
SPK=[(np.random.default_rng(9).uniform(120,480),np.random.default_rng(i).uniform(0,1)) for i in range(26)]
def beat1(u):
    im=BGS[0].copy()
    L=Image.new('RGBA',(W,H),(0,0,0,0)); d=ImageDraw.Draw(L)
    kicker(d,1,330,(255,214,150))
    # parchment card
    p=back(min(1,u/0.35))
    card=Image.new('RGBA',(900,430),(0,0,0,0)); cd=ImageDraw.Draw(card)
    cd.rounded_rectangle([0,0,899,429],18,fill=(243,228,196,255),outline=(150,100,50,255),width=4)
    cd.rounded_rectangle([18,18,881,411],12,outline=(170,120,60,160),width=2)
    f=F('PlayfairDisplay.ttf',190); 
    try: f.set_variation_by_name('Black')
    except Exception: pass
    b=cd.textbbox((0,0),'Stories',font=f); cd.text((450-(b[2]-b[0])/2-b[0],215-(b[3]-b[1])/2-b[1]-20),'Stories',font=f,fill=(70,30,12,255))
    fk=ImageFont.truetype('/home/claude/amrita/fonts/KaushanScript-Regular.ttf',58); b=cd.textbbox((0,0),'ek kahani sunoge?',font=fk)
    cd.text((450-(b[2]-b[0])/2-b[0],330),'ek kahani sunoge?',font=fk,fill=(180,60,40,255))
    # page wipe reveal
    w=int(900*ease((u-0.15)/0.5)); m=Image.new('L',card.size,0); ImageDraw.Draw(m).rectangle([0,0,w,430],fill=255)
    a=card.split()[3]; card.putalpha(Image.fromarray(np.minimum(np.array(a),np.array(m))))
    card=card.rotate(-3+2*(1-p),resample=Image.BICUBIC,expand=True)
    im.alpha_composite(L)
    if p>0: put(im,card,540,int(400+card.height+(1-p)*120))
    prop_in(im,'prop_storybook',u,300,1560)
    # sparkles rising from book
    L=Image.new('RGBA',(W,H),(0,0,0,0)); d=ImageDraw.Draw(L)
    if u>0.4:
        for i in range(26):
            r=np.random.default_rng(100+i); x=r.uniform(170,430); sp=r.uniform(150,320); ph=r.uniform(0,1)
            yv=1350-((u-0.4)*sp+ph*200)%420; s=r.uniform(3,8)
            d.ellipse([x-s,yv-s,x+s,yv+s],fill=(255,210,120,int(200*r.uniform(0.4,1))))
    im.alpha_composite(L.filter(ImageFilter.GaussianBlur(1.2)))
    avatar_in(im,'avatar_thinking_question',u,+1)
    return im
# ---------- beat 2: BOOKS I READ (book spines stacking) ----------
SP=[('BOOKS',(252,207,0),(30,30,30)),('I',(200,70,50),(255,255,255)),('READ',(240,240,230),(52,83,65))]
def beat2(u):
    im=BGS[1].copy(); L=Image.new('RGBA',(W,H),(0,0,0,0)); d=ImageDraw.Draw(L)
    kicker(d,2,330,(252,207,0))
    y=420
    for k,(w,bc,fc) in enumerate(SP):
        p=(u-0.08-k*0.16)/0.28
        f=F('Anton-Regular.ttf',150); b=d.textbbox((0,0),w,font=f); tw=b[2]-b[0]; th=b[3]-b[1]
        bw=max(tw+160,420); bh=170
        if p>0:
            q=back(min(1,p)); side=-1 if k%2==0 else 1
            cx=540+side*(1-q)*1100+(k-1)*30
            box=[cx-bw/2,y,cx+bw/2,y+bh]
            d.rounded_rectangle([box[0]+10,box[1]+12,box[2]+10,box[3]+12],14,fill=(0,0,0,110))
            d.rounded_rectangle(box,14,fill=bc+(255,))
            for e in (28,bh-28): d.line([box[0]+20,box[1]+e,box[2]-20,box[1]+e],fill=fc+(120,),width=3)
            d.text((cx-tw/2-b[0],y+bh/2-th/2-b[1]),w,font=f,fill=fc+(255,))
        y+=bh+10
    im.alpha_composite(L)
    prop_in(im,'prop_book_stack',u,800,1600)
    avatar_in(im,'avatar_reading_book',u,-1)
    return im
# ---------- beat 3: YOUTUBE (video player UI + CRT) ----------
def beat3(u):
    im=BGS[2].copy(); L=Image.new('RGBA',(W,H),(0,0,0,0)); d=ImageDraw.Draw(L)
    kicker(d,3,330,(255,90,90))
    p=back(min(1,u/0.3)); s=0.6+0.4*p
    cw,ch=int(900*s),int(560*s); x0=540-cw//2; y0=400
    d.rounded_rectangle([x0,y0,x0+cw,y0+ch],int(28*s),fill=(28,28,32,255),outline=(255,255,255,40),width=2)
    if p>0.6:
        f=F('Anton-Regular.ttf',118); 
        for i,l in enumerate(['YOUTUBE CHANNEL','RECOMMENDATIONS']):
            a=int(255*ease((u-0.25-i*0.12)/0.25)); b=d.textbbox((0,0),l,font=f); tw=b[2]-b[0]; f2=f
            if tw>cw-80: f2=F('Anton-Regular.ttf',int(118*(cw-80)/tw)); b=d.textbbox((0,0),l,font=f2); tw=b[2]-b[0]
            d.text((540-tw/2-b[0],y0+70+i*150-b[1]),l,font=f2,fill=(255,255,255,a) if i==0 else (255,70,70,a))
        # progress bar + play
        pr=ease((u-0.3)/1.1); by=y0+ch-70
        d.rounded_rectangle([x0+40,by,x0+cw-40,by+10],5,fill=(255,255,255,60))
        d.rounded_rectangle([x0+40,by,x0+40+(cw-80)*pr,by+10],5,fill=(235,30,40,255))
        cxp=x0+40+(cw-80)*pr; d.ellipse([cxp-12,by-7,cxp+12,by+17],fill=(235,30,40,255))
        d.polygon([(x0+44,by-60),(x0+44,by-24),(x0+74,by-42)],fill=(255,255,255,230))
        d.text((x0+92,by-62),'Recommended for you',font=MS(28,'Medium'),fill=(220,220,220,230))
    im.alpha_composite(L)
    # CRT scanlines over card
    sl=Image.new('RGBA',(W,H),(0,0,0,0)); sd=ImageDraw.Draw(sl)
    for yv in range(y0,y0+ch,6): sd.line([(x0,yv),(x0+cw,yv)],fill=(0,0,0,40))
    im.alpha_composite(sl)
    prop_in(im,'prop_retro_tv_play',u,820,1640)
    avatar_in(im,'avatar_laptop_ai',u,-1)
    return im
# ---------- beat 4: JOURNEY (gradient type + follower counter + hearts) ----------
def beat4(u):
    im=BGS[3].copy(); L=Image.new('RGBA',(W,H),(0,0,0,0)); d=ImageDraw.Draw(L)
    kicker(d,4,330,(255,170,220))
    lines=['MERA CONTENT','CREATION','JOURNEY']
    f=MS(110,'Black'); y=410
    for i,l in enumerate(lines):
        p=(u-0.05-i*0.12)/0.3
        if p<=0: y+=125; continue
        q=back(min(1,p)); b=d.textbbox((0,0),l,font=f); tw=b[2]-b[0]
        ff=f if tw<980 else MS(int(110*980/tw),'Black'); b=d.textbbox((0,0),l,font=ff); tw=b[2]-b[0]
        # gradient fill via mask
        m=Image.new('L',(W,H),0); ImageDraw.Draw(m).text((540-tw/2-b[0],y+(1-q)*60-b[1]),l,font=ff,fill=int(255*min(1,p*2)))
        g=np.zeros((H,W,4),np.uint8); sh=(u*300)%W
        gx=((xx+sh)%W)/W; g[...,0]=(255*(1-gx)+255*gx).astype(np.uint8); g[...,1]=(200*(1-gx)+80*gx).astype(np.uint8); g[...,2]=(60*(1-gx)+200*gx).astype(np.uint8); g[...,3]=np.array(m)
        im.alpha_composite(Image.fromarray(g)); y+=125
    # follower counter pill
    c=int(15300*ease((u-0.35)/0.9))
    if u>0.3:
        txt=f'{c:,} followers'; fc=MS(46,'Bold'); b=d.textbbox((0,0),txt,font=fc); tw=b[2]-b[0]
        d.rounded_rectangle([540-tw/2-40,820,540+tw/2+40,900],40,fill=(255,255,255,40),outline=(255,255,255,160),width=2)
        text_c(d,txt,540,840,fc,(255,255,255,255))
    im.alpha_composite(L)
    # hearts
    L=Image.new('RGBA',(W,H),(0,0,0,0)); d=ImageDraw.Draw(L)
    for i in range(12):
        r=np.random.default_rng(200+i); x=r.uniform(120,960); sp=r.uniform(250,450); ph=r.uniform(0,1)
        yv=1700-((u*sp+ph*900)%1300); s=r.uniform(14,28)
        if u*sp+ph*900<200: continue
        d.ellipse([x-s,yv-s,x,yv],fill=(255,60,120,170)); d.ellipse([x,yv-s,x+s,yv],fill=(255,60,120,170)); d.polygon([(x-s,yv-s/2),(x+s,yv-s/2),(x,yv+s)],fill=(255,60,120,170))
    im.alpha_composite(L)
    prop_in(im,'prop_phone_tripod',u,270,1640)
    avatar_in(im,'avatar_phone_recording',u,+1)
    return im
# ---------- beat 5: VOICE OVER (neon waveform + typed neon) ----------
def beat5(u):
    im=BGS[4].copy(); L=Image.new('RGBA',(W,H),(0,0,0,0)); d=ImageDraw.Draw(L)
    kicker(d,5,330,(0,220,255))
    txt=['VOICE OVER KAHA','SE BANATA HU?']; f=F('Anton-Regular.ttf',128)
    tot=sum(len(t) for t in txt); n=int(max(0,(u-0.05)/0.022))
    y=420; cnt=0
    for l in txt:
        k=max(0,min(len(l),n-cnt)); cnt+=len(l)
        b=d.textbbox((0,0),l,font=f); tw=b[2]-b[0]
        d.text((540-tw/2-b[0],y-b[1]),l[:k],font=f,fill=(255,255,255,255))
        y+=150
    G=L.filter(ImageFilter.GaussianBlur(14)); ga=np.array(G); ga[...,0]=0; ga[...,1]=(ga[...,1]*0.85).astype(np.uint8)
    im.alpha_composite(Image.fromarray(ga)); im.alpha_composite(Image.fromarray(ga)); im.alpha_composite(L)
    # waveform
    L=Image.new('RGBA',(W,H),(0,0,0,0)); d=ImageDraw.Draw(L)
    a=ease((u-0.2)/0.3)
    for i in range(44):
        x=60+i*22; amp=(0.3+0.7*abs(math.sin(i*0.7+u*9)*math.sin(i*0.23+u*4)))*120*a
        d.rounded_rectangle([x,860-amp,x+12,860+amp],6,fill=(0,220,255,220))
    im.alpha_composite(L.filter(ImageFilter.GaussianBlur(6))); im.alpha_composite(L)
    avatar_in(im,'avatar_mic_voiceover',u,-1)
    prop_in(im,'prop_chat_bubble',u,820,1300,0.45)
    return im
BEATS=[beat1,beat2,beat3,beat4,beat5]
def raw(t):
    if t<HOOK: return ama3.frame(min(t,HOOK)*1.0) if t>0 else ama3.frame(0)
    if t<FIN0:
        k=int((t-HOOK)//BEAT); u=t-HOOK-k*BEAT; return BEATS[k](u)
    return ama3.frame(2.0+(t-FIN0)*1.6)
def to_arr(x): return x if isinstance(x,np.ndarray) else np.array(x.convert('RGB'))
BOUNDS=[HOOK+i*BEAT for i in range(NB+1)]
def frame(t):
    out=to_arr(raw(t))
    # whip transitions around each boundary
    for bnd in BOUNDS:
        dt=t-bnd
        if -0.12<dt<0.12:
            k=dt/0.12  # -1..1
            sh=int((k)*W*0.35) if dt<0 else int(k*W*0.35)
            shift=-sh if dt<0 else (W*0.35-abs(sh))
            sx=int(-abs(k)*W*0.35) if dt<0 else int((1-abs(k))*W*0.35)
            out=np.roll(out,sx,1); kl=int(9+abs(1-abs(k))*60) if dt>=0 else int(9+abs(k)*60)
            kern=np.ones((1,kl),np.float32)/kl; out=cv2.filter2D(out,-1,kern)
    if t<0.25: out=(out*(t/0.25)).astype(np.uint8)
    return out
if __name__=='__main__':
    if len(sys.argv)>1:
        for tt in map(float,sys.argv[1:]): Image.fromarray(frame(tt)).save(f'h_{tt}.png')
        sys.exit()
    p=subprocess.Popen(['ffmpeg','-y','-loglevel','error','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-',
      '-c:v','libx264','-preset','veryfast','-crf','18','-pix_fmt','yuv420p','-movflags','+faststart','tmp_v4.mp4'],stdin=subprocess.PIPE)
    for i in range(int(DUR*FPS)): p.stdin.write(frame(i/FPS).tobytes())
    p.stdin.close(); p.wait()
    if p.returncode==0: os.replace('tmp_v4.mp4','ama4_video.mp4')
