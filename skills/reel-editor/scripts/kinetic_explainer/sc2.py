# kinetic_explainer: faceless AI explainer in the 'red 3D kinetic words' style (cartoon presenter, phone screen-recording, pixel glitch, light streak, halftone transitions, soft SFX). Made with Claude, Nov 2026.
# Paths to inputs (videos, images, fonts, audio) are set near the top: edit them for a new reel.
import os, sys
import sys; sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from fx import *
from comp import P
T=55.5
def pi(n): return P+f'img0{n}.png'
# kind,text,t0,t1,cx,cy,size,rot,mode
I=[]
def big(tx,t0,t1,cx=540,cy=430,size=230,rot=-3,mode='wipe'): I.append(('big',tx,t0,t1,cx,cy,size,rot,mode))
def sm(tx,t0,t1,cx=540,cy=260,size=72,rot=-3): I.append(('small',tx,t0,t1,cx,cy,size,rot,'wipe'))
def pl(tx,t0,t1,cx,cy,size=50,rot=0): I.append(('pill',tx,t0,t1,cx,cy,size,rot,'pop'))
# HOOK
sm('ये वीडियो',0.25,2.3,330,360,76,-4); big('DELETE',0.55,2.3,540,520,250); pl('24 घंटे बाद',1.25,2.3,760,690,56,4)
sm('क्योंकि ये स्किल',2.45,5.25,360,330,72,-4); sm('कई लोगों का',3.35,5.25,740,430,72,3)
big('धंधा',4.05,5.25,540,610,300,-3,'slam'); sm('खा जाएगी',4.6,5.25,650,800,84,-2)
# S1
sm('मान लीजिए',5.6,8.9,330,230,72,-4); big('Instagram',6.0,8.9,540,370,190); sm('store',6.6,8.9,820,500,84,0)
pl('आपका',7.35,8.9,330,620,48,-6); pl('छोटा सा स्टोर',7.55,8.9,770,1010,48,5)
sm('लोग पसंद करने लगे',9.05,11.25,540,280,72,-3); big('Likes',9.25,10.3,540,450,240)
big('Orders',10.4,11.25,540,450,240); sm('आने लगे',10.7,11.25,790,600,80,2)
# S2
sm('रोज़ नए मैसेज',11.55,13.3,540,240,72,-3); big('WhatsApp',11.7,15.9,540,400,200)
sm('हर मैसेज में नया एड्रेस',13.4,15.9,540,240,66,-3)
# S3
sm('अब एक-एक एड्रेस',16.1,18.3,360,240,70,-4); big('हाथ से',16.5,18.3,540,410,220); sm('टाइप करना हो',17.0,18.3,770,570,74,3)
pl('घंटों का काम',17.4,21.9,840,1200,46,6)
sm('तो पूरी',18.5,20.6,330,240,72,-4); big('शाम',18.7,20.6,540,410,250); sm('निकल जाती है',19.2,20.6,770,580,74,3)
big('गलती',20.75,21.9,540,410,250,-3,'slam'); sm('भी हो जाती है',21.0,21.9,770,580,74,3)
# S4 phone
Y0,Y1=150,320
sm('अब देखिए',22.15,24.1,540,Y0,64); big('मैं क्या करता हूँ',22.35,24.1,540,Y1,130)
sm('सारे मैसेज',24.15,26.0,540,Y0,64); big('Select',24.3,26.0,540,Y1,170)
big('Copy',26.15,27.05,540,Y1,170)
sm('Claude में',27.15,28.95,540,Y0,64); big('Paste',27.3,28.95,540,Y1,170)
sm('फिर सिर्फ़',29.05,30.7,540,Y0,64); big('एक लाइन',29.2,30.7,540,Y1,170)
sm('इन एड्रेस की',30.8,32.9,540,Y0,64); big('A4 शीट',30.95,32.9,540,Y1,170)
sm('कुछ पल',33.05,34.35,540,Y0,64); big('Wait...',33.2,34.35,540,Y1,170)
sm('दो मिनट में',34.45,36.5,540,Y0,64); big('PDF ready',34.6,36.5,540,Y1,170)
# S5
sm('सिर्फ़',36.7,38.6,300,190,74,-4); big('2 मिनट',36.75,38.6,540,330,230)
pl('A4 लेबल',37.0,38.6,300,560,50,-6); pl('तैयार',37.2,38.6,810,1080,50,5)
# S6
big('प्रिंट',38.86,39.85,540,330,240); sm('निकालिए',39.1,39.85,790,490,78,3)
sm('पार्सल पर',39.95,41.1,330,190,74,-4); big('चिपकाइए',40.05,41.1,540,330,220)
sm('बस, काम ख़त्म',41.2,42.4,540,190,74,-3); big('Done',41.25,42.4,540,340,260,-3,'slam')
# S7
sm('ये तो सिर्फ़ एक',42.65,44.4,540,250,72,-3); big('Example',42.85,44.4,540,410,220)
sm('रोज़ के कितने ही काम',44.5,47.3,540,220,66,-3); big('AI',44.7,47.3,540,450,380); sm('से आसान',45.2,47.3,800,640,84,2)
# S8
sm('आप भी',47.5,48.6,330,240,72,-4); big('Try करो',47.65,48.6,540,400,210)
sm('और बताइए',48.7,51.2,330,240,72,-4); big('Comment',48.85,51.2,540,400,210)
sm('अगला कौन सा काम दिखाऊँ?',49.6,51.2,540,560,58,-2)
# S9
big('Follow',51.45,53.85,540,380,250); sm('@aitricksbysumit',52.5,55.4,540,760,70,0)
sm('इससे पहले कि ये वीडियो',53.96,55.4,540,230,60,-3); big('DELETE',54.2,55.4,540,400,250,-3,'slam')
TR=[(5.4,'streak'),(11.4,'halftone'),(16.0,'glitch'),(22.0,'streak'),(36.6,'halftone'),(38.7,'glitch'),(42.5,'streak'),(47.4,'halftone'),(51.3,'streak')]
SEGS=[(22.0,26.0,16.0,42.0),(26.0,27.1,8.2,9.2),(27.1,32.8,62.0,73.0),(32.8,34.4,80.0,86.5),(34.4,36.7,86.8,99.8)]
def draw_items(base,t,kinds):
    for (k,tx,t0,t1,cx,cy,size,rot,mode) in I:
        if k not in kinds: continue
        if t<t0-0.01 or t>t1+0.25: continue
        if k=='big':
            im=word3d(tx,size); anim(base,im,cx,cy,t,t0,t1,0.42,rot,mode); pixels(base,t,t0,cx,cy,sx=min(460,im.width/2+40),sy=im.height/2,seed=hash(tx)%97)
        elif k=='small': anim(base,small_text(tx,size),cx,cy,t,t0,t1,0.35,rot,'wipe')
        else: anim(base,pill_label(tx,size),cx,cy,t,t0,t1,0.4,rot,'pop')
def floatc(base,path,w,h,cx,cy,t,t0,t1,rot):
    if t<t0 or t>t1+0.25: return
    c=card(path,w,h); p=pop(t,t0,0.5); a=1.0; s=p
    if t>t1: q=clamp((t-t1)/0.22); a=1-q; s*=1+0.1*q
    place(base,c,cx,cy+8*math.sin(t*2+cx),s,rot+1.5*math.sin(t*1.3+cy),a)
def frame(t):
    sk=None
    if t<22.0 or t>=36.6:
        base=studio()
    else:
        base=phone_backdrop()
    # scene content (cards behind avatar, avatar, front items)
    if t<5.4:
        avatar(base,'02_avatar_arms_crossed',t,0.2)
        if t>=4.05: sk=4.05
    elif t<11.4:
        floatc(base,pi(2),400,520,540,800,t,7.0,8.9,-3)
        if t<9.0: avatar(base,'01_avatar_wave',t,5.4)
        else: avatar(base,'03_avatar_point_up',t,9.0-0.5)
        if 9.3<=t<10.5:
            place(base,asset(A+'20_prop_heart.png',0.26),860,640,pop(t,9.3)*(1+0.06*math.sin(t*9)),10)
        if t>=10.45:
            floatc(base,pi(6),300,380,230,880,t,10.5,11.25,-7)
    elif t<16.0:
        avatar(base,'05_avatar_phone',t,11.4)
        pos=[(290,690,-5),(800,860,4),(280,1040,-4),(800,1220,5),(300,1400,-4)]
        bodies=['1 घड़ी  •  दिल्ली','1 घड़ी  •  पंजाब','2 घड़ी  •  मुंबई','1 घड़ी  •  हरियाणा','1 कड़ा  •  नाशिक']
        for i,(x,y,r) in enumerate(pos):
            t0=11.9+i*0.62
            if t>=t0:
                p=pop(t,t0,0.42); place(base,notif_card('नया ऑर्डर • WhatsApp',bodies[i]),x+(1-clamp(p,0,1))*(300 if x>540 else -300),y,0.82*p,r,clamp(p*3))
    elif t<22.0:
        floatc(base,pi(4),330,440,840,930,t,16.8,21.9,6)
        avatar(base,'04_avatar_shrug',t,16.0)
        if 20.75<=t: sk=20.75
    elif t<36.6:
        phone_rec(base,t,SEGS,22.0)
        if 29.2<=t<32.9: receipt(base,860,760,t,29.2,['इन एड्रेस की','A4 शीट बना दो'],dur=0.8,rot=6)
    elif t<38.7:
        floatc(base,pi(5),480,640,540,820,t,36.7,38.6,-3)
        avatar(base,'03_avatar_point_up',t,36.6)
    elif t<42.5:
        floatc(base,pi(6),420,560,540,800,t,38.75,42.4,3)
        if t<41.2: avatar(base,'01_avatar_wave',t,38.7)
        else: avatar(base,'06_avatar_thumbs_up',t,41.2-0.5)
        if t>=41.25: sk=41.25
    elif t<47.4:
        avatar(base,'06_avatar_thumbs_up',t,42.5)
        floatc(base,pi(5),230,300,210,960,t,45.0,47.3,-8)
        floatc(base,pi(6),230,300,870,1000,t,45.4,47.3,7)
        floatc(base,pi(2),230,300,230,1390,t,45.8,47.3,5)
        floatc(base,pi(3),230,300,860,1430,t,46.2,47.3,-6)
    elif t<51.3:
        avatar(base,'03_avatar_point_up',t,47.4)
        if t>=49.0: place(base,asset(A+'19_prop_dm_bubble.png',0.36),850,850,pop(t,49.0)*(1+0.04*math.sin(t*6)),8)
    else:
        avatar(base,'01_avatar_wave',t,51.3)
        if 51.6<=t<53.85:
            following=t>=52.4; bw,bh=440,120
            btn=rrect((bw,bh),60,(50,50,56,255) if following else RED+(255,))
            ti=small_text('Following' if following else 'Follow',58,(255,255,255)); btn.alpha_composite(ti,((bw-ti.width)//2,(bh-ti.height)//2))
            a=1-clamp((t-53.6)/0.25)
            place(base,btn,540,600,pop(t,51.6)*(0.92 if 52.35<t<52.5 else 1),0,a)
            cursor(base,t,52.4,(570,610),start=(900,900),lead=0.8)
        if t>=54.2: sk=54.2
    draw_items(base,t,('big','small','pill'))
    if sk is not None:
        from comp import shake
        base=shake(base,t,sk,14)
    for tc,typ in TR:
        if abs(t-tc)<0.4:
            if typ=='streak': base=streak(base,t,tc)
            elif typ=='halftone': base=halftone(base,t,tc)
            else: base=glitch(base,t,tc,seed=int(tc))
    if t<0.3: base=Image.blend(Image.new('RGBA',(W,H),(255,255,255,255)),base,t/0.3)
    if t>T-0.45: base=Image.blend(base,Image.new('RGBA',(W,H),(0,0,0,255)),clamp((t-(T-0.45))/0.45))
    return base.convert('RGB')
if __name__=='__main__':
    ts=[float(x) for x in sys.argv[1:]]
    ims=[frame(t).resize((360,640)) for t in ts]
    cols=min(8,len(ims)); rows=(len(ims)+cols-1)//cols
    M=Image.new('RGB',(cols*360,rows*640))
    for i,im in enumerate(ims): M.paste(im,((i%cols)*360,(i//cols)*640))
    M.save('/home/claude/ex/v2/prev.png')
