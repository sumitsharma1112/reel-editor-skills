# beauty_edit: beat-synced glam edit of a talking/posing clip: optical-flow slow motion, speed ramps, whip/zoom/spin/glitch/blur transitions, flashes, pink grade + bloom + bokeh, sharpening, script titles, before/after wipe, triptych, card, polaroids, voice-hook captions. Made with Claude, Nov 2026.
# Paths to inputs (videos, images, fonts, audio) are set near the top: edit them for a new reel.
import os, sys
import sys; sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from edit import *
T=15.69
B0=0.14; P=0.3455
BEATS=[B0+P*i for i in range(46)]
C=[0.0]+[B0+P*4*k for k in range(1,12)]+[T]
def rgbpulse(c,t,u):
    for b in BEATS:
        if 0<=t-b<0.15: return rgbsplit(c,14*(1-(t-b)/0.15))
    return c
S=[Seg(C[0],C[1],16.2,17.6,lin,1.12,1.0,bw=False),
   Seg(C[1],C[2],22.0,25.05,ramp_sf,1.0,1.08,'zoom',mb=True),
   Seg(C[2],C[3],25.3,26.15,ramp_fs,1.12,1.0,'flash'),
   Seg(C[3],C[4],26.9,28.1,lin,1.0,1.08,'whip'),
   Seg(C[4],C[5],28.35,29.55,lin,1.06,1.0,'spin'),
   Seg(C[5],C[6],29.9,30.9,ramp_fs,1.0,1.1,'blur'),
   Seg(C[6],C[7],31.0,32.2,lin,1.08,1.0,'whip',fx=rgbpulse),
   Seg(C[7],C[8],32.4,33.7,lin,1.0,1.1,'flash'),
   Seg(C[8],C[9],34.2,35.45,ramp_fs,1.0,1.05,'glitch',mb=False),
   Seg(C[9],C[10],35.9,37.25,ramp_fs,1.1,1.0,'zoom'),
   Seg(C[10],C[11],38.6,39.9,lin,1.0,1.08,'whip'),
   Seg(C[11],C[12],39.95,41.2,ramp_fs,1.0,1.12,'flash')]
FL=[C[2],C[7],C[11]]+[C[1]+0.0]
TITLE=text_sprite('Gulabi Rang',GV,210,(255,248,252),(255,90,160),18,1.0)
SUB=text_sprite('P I N K   S U I T   E R A',M6,40,(255,235,245),(255,110,170),8,0.6)
WAIT=text_sprite('wait for it...',PF,92,(255,255,255),(255,120,180),10,0.7)
HAND=text_sprite('edit by @aitricksbysumit',M6,38,(255,240,248),(255,110,170),8,0.6)
HEART=heart_sprite(70)
def frame(t):
    img=render_segments(S,t,BEATS)
    img=flashes(img,t,FL)
    img=finish(img,t,0.28 if t>C[1] else 0.12, 0.6 if t<C[1] else 1.0, 0.4 if t<C[1] else 1.0)
    # motion graphics
    if t<C[1]:
        a=ease_out((t-0.2)/0.4)*(1-ease_io((t-1.3)/0.22))
        paste(img,WAIT,540,1560,a,1.0,reveal=min(1,(t-0.2)/0.6))
    if C[2]<=t<C[4]+0.2:
        r=min(1,(t-C[2]-0.05)/0.9); a=1-ease_io((t-C[4]+0.1)/0.3)
        paste(img,TITLE,540,1430,a,1.0+0.03*math.sin(t*3),reveal=r)
        paste(img,SUB,540,1590,a*ease_out((t-C[2]-0.6)/0.5))
    if C[5]<=t<C[7]:
        for i in range(5):
            t0=C[5]+i*0.35; u=(t-t0)/1.6
            if 0<=u<=1:
                paste(img,HEART,200+i*170+40*math.sin(u*6+i),1700-u*900,math.sin(math.pi*u),0.6+0.5*u)
    if t>=C[10]+0.3:
        u=t-C[10]-0.3; r=min(1,u/0.9)
        paste(img,TITLE,540,1430,ease_out(u/0.3),0.9,reveal=r)
        paste(img,HAND,540,1600,ease_out((u-0.6)/0.5)*0.95)
    if t>T-0.35: img=flash(img,(t-(T-0.35))/0.35,(255,240,248))
    if t<0.12: img=img*(t/0.12)
    return np.clip(img,0,255).astype(np.uint8)
if __name__=='__main__':
    ts=[float(x) for x in sys.argv[1:]]
    ims=[Image.fromarray(frame(t)).resize((270,480)) for t in ts]
    cols=min(8,len(ims)); rows=(len(ims)+cols-1)//cols
    M=Image.new('RGB',(cols*270,rows*480))
    for i,im in enumerate(ims): M.paste(im,((i%cols)*270,(i//cols)*480))
    M.save('/home/claude/girl/prev.png')
