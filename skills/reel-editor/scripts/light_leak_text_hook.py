#!/usr/bin/env python3
"""Black screen + orange/amber light-leak flashes + serif text hook (the "Har bala se" Insta style).

White lines in Playfair Display (cream, thin dark stroke) and a last line in gold Great Vibes
script with a colour emoji; whoosh on every leak. --reveal word = word by word (like the
reference), --reveal all = whole text in one go. Renders 9:16 and 16:9.

  python3 light_leak_text_hook.py --lines "7 mein se kitni movies pehchaani?" "4+ matlab ..." \
      --gold "Comment mein bas number likho" --emoji "👇🍷" --dur 6 --reveal all --out Hook
"""
import numpy as np, cv2, subprocess, wave, sys, argparse, os
from PIL import Image, ImageDraw, ImageFont
ap=argparse.ArgumentParser(); ap.add_argument('--lines',nargs='+',required=True); ap.add_argument('--gold',default='')
ap.add_argument('--emoji',default=''); ap.add_argument('--dur',type=float,default=6.0); ap.add_argument('--reveal',choices=['word','all'],default='word')
ap.add_argument('--out',default='Hook'); A=ap.parse_args()
FONTS=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','fonts')+'/'
FPS=30; DUR=A.dur
LINES=A.lines; L2=A.gold; EMO=A.emoji
# word reveal times (like ref: ~0.4s per word), line 2 lands with a flash
T2=0.1 if A.reveal=='all' else 0.25+sum(len(l.split()) for l in LINES)*0.42+0.4
def font(sz): return ImageFont.truetype(FONTS+'playfair-display-700.ttf',int(sz*0.92))
def sfont(sz): return ImageFont.truetype(FONTS+'great-vibes-400.ttf',int(sz*1.7))
emo=ImageFont.truetype('/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf',109)
def emoji_img(h):
    im=Image.new('RGBA',(140,140),(0,0,0,0)); im=Image.new('RGBA',(300,140),(0,0,0,0)); ImageDraw.Draw(im).text((0,0),EMO,font=emo,embedded_color=True)
    im=im.crop(im.getbbox()); return im.resize((int(im.width*h/im.height),h),Image.LANCZOS)
# light-leak events: (start, dur, kind)
EV=[(0.45,0.45,'full'),(1.4,0.35,'top'),(1.75,0.4,'left'),(2.7,0.5,'leftred'),(4.15,0.55,'fullwarm'),(5.0,0.45,'left'),(5.3,0.45,'dim')]
EV=[(t*DUR/6.0,d*min(1,DUR/6.0),k) for t,d,k in EV]  # spread the leaks over any duration
def leak(W,H,t):
    w,h=96,int(96*H/W); acc=np.zeros((h,w,3),np.float32)
    yy,xx=np.mgrid[0:h,0:w]/np.array([h,w])[:,None,None]
    for t0,d,k in EV:
        p=(t-t0)/d
        if not 0<=p<=1: continue
        a=np.sin(np.pi*p)**0.8
        if k in('full','fullwarm'):
            cx=0.3+0.5*p; m=np.exp(-((xx-cx)**2/0.35+(yy-0.4)**2/0.6))
            col=np.array([40,110,235]) if k=='full' else np.array([70,190,245])
            m=np.clip(m*1.6,0,1); edge=np.exp(-((xx-cx-0.35)**2/0.01))*0.6
            acc+=a*(m[...,None]*col+edge[...,None]*np.array([30,60,220]))
        elif k=='top':
            m=(yy<0.12+0.05*np.sin(xx*6)).astype(np.float32)*(xx<0.6+0.2*p); acc+=a*m[...,None]*np.array([30,40,200])
        elif k in('left','leftred'):
            m=np.clip((0.55-xx)/0.25,0,1)*(1 if k=='leftred' else (yy<0.62)); m=np.asarray(m,np.float32)
            col=np.array([40,120,240]) if k=='left' else np.array([30,70,220])
            acc+=a*m[...,None]*col
        else:
            acc+=a*0.35*np.ones_like(xx)[...,None]*np.array([20,35,70])
    acc=cv2.GaussianBlur(acc,(0,0),3)
    return cv2.resize(acc,(W,H),interpolation=cv2.INTER_CUBIC)
def alpha(t,t0,d=0.25): return max(0,min(1,(t-t0)/d))
def frame(W,H,t):
    img=Image.fromarray(np.clip(leak(W,H,t)+3,0,255).astype(np.uint8)[...,::-1]).convert('RGBA')
    sz=int(min(W,H)*0.058)
    while max(max(font(sz).getlength(l) for l in LINES), sfont(sz).getlength(L2)+sz*2.2)>W*0.86: sz-=2
    f=font(sz)
    lay=Image.new('RGBA',(W,H),(0,0,0,0)); d=ImageDraw.Draw(lay)
    y1=(H*0.43 if H>W else H*0.40); k=0
    for li,line in enumerate(LINES):
        ws=line.split(); x=(W-f.getlength(line,features=['lnum']))/2; y=y1+li*sz*1.2
        for wd in ws:
            a=alpha(t,0.1,0.3) if A.reveal=='all' else alpha(t,0.25+k*0.42); k+=1
            if a>0: d.text((x,y),wd,font=f,fill=(255,248,236,int(255*a)),anchor='ls',features=['lnum'],stroke_width=2,stroke_fill=(0,0,0,int(180*a)))
            x+=f.getlength(wd+' ',features=['lnum'])
    y1=y1+sz*1.2
    a=alpha(t,T2,0.3)
    if a>0 and L2:
        f=sfont(sz); gold=(240,196,90,int(255*a)); w2=f.getlength(L2); e=emoji_img(int(sz*0.95)); tot=w2+sz*0.25+e.width
        x2=(W-tot)/2; y2=y1+sz*1.75
        d.text((x2,y2),L2,font=f,fill=gold,anchor='ls',stroke_width=1,stroke_fill=(120,60,10,int(200*a)))
        ea=e.copy(); ea.putalpha(Image.eval(e.getchannel('A'),lambda v:int(v*a)))
        lay.alpha_composite(ea,(int(x2+w2+sz*0.25),int(y2-sz*0.95)))
    img.alpha_composite(lay)
    return np.asarray(img.convert('RGB'))
# soft whooshes on leaks
sr=44100; au=np.zeros(int(DUR*sr)); rng=np.random.default_rng(5)
for t0,d,k in EV:
    j=int(t0*sr); n=min(int(d*1.4*sr),len(au)-j)
    if n<=0: continue
    env=np.sin(np.linspace(0,np.pi,n))**2
    nz=np.convolve(rng.standard_normal(n),np.ones(30)/30,'same'); au[j:j+n]+=nz*env*(1.0 if 'full' in k else 0.5)
au=au/np.abs(au).max()*0.5
with wave.open('/tmp/_leak.wav','wb') as w: w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes((au*32767).astype(np.int16).tobytes())
for W,H,name in [(1080,1920,A.out+'_9x16.mp4'),(1920,1080,A.out+'_16x9.mp4')]:
    p=subprocess.Popen(['ffmpeg','-v','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-','-i','/tmp/_leak.wav','-c:v','libx264','-crf','18','-pix_fmt','yuv420p','-c:a','aac','-b:a','160k','-shortest','-movflags','+faststart',name],stdin=subprocess.PIPE)
    for i in range(int(DUR*FPS)): p.stdin.write(frame(W,H,i/FPS).tobytes())
    p.stdin.close(); p.wait()
