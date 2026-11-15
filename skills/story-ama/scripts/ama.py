import numpy as np, cv2, subprocess, math, sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter
W,H,FPS,DUR=1080,1920,30,10.0
FD='/home/claude/effects/fonts/'
F=lambda n,s: ImageFont.truetype(FD+n,s)
KS=ImageFont.truetype('/home/claude/amrita/fonts/KaushanScript-Regular.ttf',96)
# background: deep navy -> warm gold glow
yy,xx=np.mgrid[0:H,0:W].astype(np.float32)
base=np.zeros((H,W,3),np.float32)
top=np.array([14,18,38]);bot=np.array([30,18,12])
t=(yy/H)[...,None]; base=top*(1-t)+bot*t
def glow(cx,cy,r,col,a): 
    d=np.hypot(xx-cx,yy-cy)/r; return (np.exp(-d*d)[...,None]*np.array(col)*a)
BG=np.clip(base+glow(880,420,520,(255,170,60),0.35)+glow(150,1500,600,(60,90,255),0.30),0,255)
rng=np.random.default_rng(3); BG=np.clip(BG+rng.normal(0,3,(H,W,1)),0,255).astype(np.uint8)
BGI=Image.fromarray(BG).convert('RGBA')
ease=lambda x: 1-(1-max(0,min(1,x)))**3
def back(x):
    x=max(0,min(1,x)); c=1.70158; return 1+(c+1)*(x-1)**3+c*(x-1)**2
# floating question marks
QM=[(rng.uniform(60,1020),rng.uniform(250,1750),rng.uniform(60,160),rng.uniform(0,6.28),rng.uniform(0.2,0.5)) for _ in range(14)]
CHIPS=["Einstein ki kahani?","Kaunsa AI tool use karte ho?","Reel kaise edit karte ho?","Agli biography kiski?"]
CHIP_POS=[(300,1450),(760,1515),(330,1580),(740,1645)]
def text_c(d,txt,cx,y,f,fill,stroke=0,sf=None):
    b=d.textbbox((0,0),txt,font=f,stroke_width=stroke); w=b[2]-b[0]
    d.text((cx-w/2-b[0],y-b[1]),txt,font=f,fill=fill,stroke_width=stroke,stroke_fill=sf)
def frame(t):
    im=BGI.copy(); L=Image.new('RGBA',(W,H),(0,0,0,0)); d=ImageDraw.Draw(L)
    fq=F('ArchivoBlack-Regular.ttf',100)
    for (x,y,s,ph,sp) in QM:
        yy_=y-((t*sp*60)%1700); yy_=yy_ if yy_>200 else yy_+1550
        a=int(28+18*math.sin(t*1.3+ph))
        d.text((x+18*math.sin(t*0.8+ph),yy_),'?',font=F('ArchivoBlack-Regular.ttf',int(s)),fill=(255,255,255,a))
    im.alpha_composite(L.filter(ImageFilter.GaussianBlur(2)))
    L=Image.new('RGBA',(W,H),(0,0,0,0)); d=ImageDraw.Draw(L)
    # handle pill y=300
    a=ease((t-0.1)/0.5)
    if a>0:
        f=F('SpaceMono-Bold.ttf',36); txt='@aitricksbysumit'; b=d.textbbox((0,0),txt,font=f); w=b[2]-b[0]
        yo=300+20*(1-a)
        d.rounded_rectangle([540-w/2-28,yo-30,540+w/2+28,yo+30],30,fill=(255,255,255,int(40*a)),outline=(255,255,255,int(110*a)),width=2)
        text_c(d,txt,540,yo-(b[3]-b[1])/2,f,(255,255,255,int(255*a)))
    # ASK ME / ANYTHING slam
    for i,(word,t0,col) in enumerate([('ASK ME',0.35,(255,255,255)),('ANYTHING',0.6,(255,200,70))]):
        p=(t-t0)/0.45
        if p<=0: continue
        s=1+0.6*(1-back(p)) if p<1 else 1+0.015*math.sin((t-t0)*3+i)
        al=int(255*min(1,p*2))
        f=F('Anton-Regular.ttf',int(230*s) if i==0 else int(200*s))
        y=440+i*250
        b=d.textbbox((0,0),word,font=f); w=b[2]-b[0]; h=b[3]-b[1]
        if w>960: f=F('Anton-Regular.ttf',int(f.size*960/w)); b=d.textbbox((0,0),word,font=f); w=b[2]-b[0]; h=b[3]-b[1]
        d.text((540-w/2-b[0]+8,y+120-h/2-b[1]+10),word,font=f,fill=(0,0,0,int(al*0.5)))
        d.text((540-w/2-b[0],y+120-h/2-b[1]),word,font=f,fill=col+(al,),stroke_width=6,stroke_fill=(15,15,25,al))
    # script subtitle
    p=ease((t-1.2)/0.6)
    if p>0:
        text_c(d,'kuch bhi poocho!',540+40*(1-p),905,KS,(244,166,185,int(255*p)),stroke=5,sf=(30,15,30,int(255*p)))
    # sticker zone 1060-1390: glass frame + arrows
    p=ease((t-1.6)/0.6)
    if p>0:
        x0,y0,x1,y1=150,1060,930,1390
        pulse=0.5+0.5*math.sin(t*4)
        d.rounded_rectangle([x0,y0,x1,y1],46,fill=(255,255,255,int(26*p)),outline=(255,200,70,int((120+100*pulse)*p)),width=4)
        for k,ax in enumerate([95,985]):
            bob=12*math.sin(t*5+k)
            dirn=1 if k==0 else -1
            cx=ax+bob*dirn; cy=1225
            d.polygon([(cx+dirn*30,cy),(cx-dirn*20,cy-34),(cx-dirn*20,cy+34)],fill=(255,200,70,int(255*p)))
    # chips
    fc=F('Montserrat.ttf',36)
    for k,(txt,(cx,cy)) in enumerate(zip(CHIPS,CHIP_POS)):
        p=(t-(2.4+k*0.55))/0.5
        if p<=0: continue
        s=back(min(p,1)); al=int(255*min(1,p*2))
        cy2=cy+6*math.sin(t*2+k)
        b=d.textbbox((0,0),txt,font=fc); w=(b[2]-b[0]); h=b[3]-b[1]
        ww=(w/2+30)*s; hh=(h/2+22)*s
        d.rounded_rectangle([cx-ww,cy2-hh,cx+ww,cy2+hh],int(hh),fill=(20,24,40,int(200*al/255)),outline=(255,255,255,int(90*al/255)),width=2)
        if s>0.8: text_c(d,txt,cx,cy2-h/2,fc,(255,255,255,al))
    im.alpha_composite(L)
    # fade in / out
    out=np.array(im.convert('RGB'))
    if t<0.25: out=(out*(t/0.25)).astype(np.uint8)
    return out
if __name__=='__main__':
    if len(sys.argv)>1:
        for tt in map(float,sys.argv[1:]): Image.fromarray(frame(tt)).save(f'f_{tt}.png')
        sys.exit()
    p=subprocess.Popen(['ffmpeg','-y','-loglevel','error','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-',
      '-f','lavfi','-i','anullsrc=r=44100:cl=stereo','-shortest','-c:v','libx264','-preset','veryfast','-crf','18','-pix_fmt','yuv420p','-c:a','aac','-movflags','+faststart','tmp_ama.mp4'],stdin=subprocess.PIPE)
    for i in range(int(DUR*FPS)): p.stdin.write(frame(i/FPS).tobytes())
    p.stdin.close(); p.wait()
    import os; os.replace('tmp_ama.mp4','Ask_Me_Anything_Story.mp4') if p.returncode==0 else None
