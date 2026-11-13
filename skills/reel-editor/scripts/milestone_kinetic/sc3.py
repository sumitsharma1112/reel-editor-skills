# milestone_kinetic: follower-milestone reel from dashboard numbers: counters, orbiting reel thumbnails, city/country bars, real views graph, Hinglish Roman captions, egg-drop hook. Made with Claude, Nov 2026.
# Paths to inputs (videos, images, fonts, audio) are set near the top: edit them for a new reel.
import os, sys
import sys; sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from fx import *
from comp import shake
T=49.52
GF='/usr/share/fonts/truetype/google-fonts/'
TH=[f'/home/claude/m50/th{i}.png' for i in range(9)]
CURVE=np.load('/home/claude/m50/curve.npy')
_g={}
def greybg():
    if 'g' in _g: return _g['g'].copy()
    y=np.linspace(-1,1,H)[:,None]; x=np.linspace(-1,1,W)[None,:]
    r=np.sqrt((x/1.1)**2+((y+0.15)/1.0)**2)
    v=np.clip(214-62*r**1.6,120,220)
    rng=np.random.default_rng(3); v=v+rng.normal(0,2.2,v.shape)
    im=Image.fromarray(np.repeat(v[...,None],3,2).astype(np.uint8),'RGB').convert('RGBA'); _g['g']=im; return im.copy()
def redbg():
    if 'r' in _g: return _g['r'].copy()
    y=np.linspace(-1,1,H)[:,None]; x=np.linspace(-1,1,W)[None,:]
    r=np.sqrt(x**2+y**2)
    c=np.stack([210-70*r,24-14*r,36-20*r],-1)
    im=Image.fromarray(np.clip(c,0,255).astype(np.uint8),'RGB').convert('RGBA'); _g['r']=im; return im.copy()
_wt={}
def wtext(txt,size,col=(255,255,255),font='Poppins-Bold.ttf',shadow=True):
    k=(txt,size,col,font)
    if k in _wt: return _wt[k]
    f=ImageFont.truetype(GF+font,size)
    bb=f.getbbox(txt); w=bb[2]-bb[0]+40; h=bb[3]-bb[1]+50
    m=Image.new('L',(w,h),0); ImageDraw.Draw(m).text((20-bb[0],20-bb[1]),txt,font=f,fill=255)
    out=Image.new('RGBA',(w+30,h+30),(0,0,0,0))
    if shadow:
        s=Image.new('L',out.size,0); s.paste(m,(18,24)); s=s.filter(ImageFilter.GaussianBlur(9)).point(lambda v:int(v*0.45))
        out.paste((20,0,5,255),(0,0),s)
    out.paste(col+(255,),(10,10),m)
    _wt[k]=out; return out
def W_(tx,t,t0,t1,cx,cy,size=110,col=(255,255,255),rot=-3,mode='wipe',font='Poppins-Bold.ttf'):
    if t0-0.01<=t<=t1+0.25: anim(BASE[0],wtext(tx,size,col,font),cx,cy,t,t0,t1,0.32,rot,mode)
def R_(tx,t,t0,t1,cx,cy,size=200,rot=-3,mode='wipe'):
    if t0-0.01<=t<=t1+0.25:
        im=word3d(tx,size); anim(BASE[0],im,cx,cy,t,t0,t1,0.38,rot,mode); pixels(BASE[0],t,t0,cx,cy,sx=min(460,im.width/2),sy=im.height/2,seed=len(tx))
BASE=[None]
def counter(t,t0,t1,v0,v1,cx,cy,size=230,dur=1.0):
    if not (t0<=t<=t1+0.25): return
    u=clamp((t-t0)/dur); u=1-(1-u)**3; v=int(v0+(v1-v0)*u)
    R_(f'{v:,}',t,t0,t1,cx,cy,size,-3,'pop') if False else None
    im=word3d(f'{v:,}',size)
    a=1.0
    if t>t1: a=1-clamp((t-t1)/0.22)
    place(BASE[0],im,cx,cy,eob(clamp((t-t0)/0.35)),-3,a)
def orbit(base,t,t0,t1,cx=540,cy=1200,rx=400,ry=300,front=True,sz=340):
    if not (t0<=t<=t1+0.3): return
    p=clamp((t-t0)/0.6); a=1-clamp((t-t1)/0.3) if t>t1 else 1
    for i,pth in enumerate(TH):
        ang=2*math.pi*i/len(TH)+ (t-t0)*1.1
        z=math.sin(ang)
        if (z>=0)!=front: continue
        s=(0.62+0.38*(z+1)/2)*p
        x=cx+rx*math.cos(ang)*p; y=cy+ry*z*p - 40
        c=card(pth,sz,int(sz*342/366))
        if z<0:
            c=c.copy(); arr=np.asarray(c).astype(np.float32); arr[...,:3]*=0.55+0.45*(z+1); c=Image.fromarray(arr.astype(np.uint8),'RGBA')
        place(base,c,x,y,s*0.8,8*math.cos(ang),a)
def bars(base,t,t0,t1,items,cy0=700,step=190,maxv=10.0):
    if not (t0<=t<=t1+0.25): return
    a=1-clamp((t-t1)/0.22) if t>t1 else 1
    for i,(name,val,ti) in enumerate(items):
        if t<ti: continue
        p=eob(clamp((t-ti)/0.4)); k=1-(1-clamp((t-ti-0.1)/0.6))**3
        w,h=900,150
        im=Image.new('RGBA',(w+40,h+40),(0,0,0,0)); d=ImageDraw.Draw(im)
        sh=Image.new('L',im.size,0); ImageDraw.Draw(sh).rounded_rectangle([20,30,20+w,30+h],40,fill=110); sh=sh.filter(ImageFilter.GaussianBlur(12)); im.paste((40,0,10,255),(0,0),sh)
        d.rounded_rectangle([20,20,20+w,20+h],40,fill=(255,255,255,255))
        # pin
        d.ellipse([50,50,100,100],fill=RED+(255,)); d.polygon([(55,88),(95,88),(75,125)],fill=RED+(255,)); d.ellipse([66,64,84,82],fill=(255,255,255,255))
        im.alpha_composite(wtext(name,54,(30,30,34),shadow=False),(118,24))
        bw=int(560*min(1,val/maxv)*k)
        d.rounded_rectangle([130,118,690,140],11,fill=(235,226,228,255)); d.rounded_rectangle([130,118,130+max(22,bw),140],11,fill=RED+(255,))
        vt=wtext(f'{val*k:.1f}%',70,RED,shadow=False); im.alpha_composite(vt,(w+10-vt.width,40))
        place(base,im,540+(1-clamp(p,0,1))*400*(1 if i%2 else -1),cy0+i*step,min(p,1.05),(-2 if i%2 else 2),a*clamp(p*3))
def graph(base,t,t0,t1):
    if not (t0<=t<=t1+0.25): return
    a=1-clamp((t-t1)/0.22) if t>t1 else 1
    w,h=940,560
    im=Image.new('RGBA',(w+60,h+60),(0,0,0,0)); d=ImageDraw.Draw(im)
    sh=Image.new('L',im.size,0); ImageDraw.Draw(sh).rounded_rectangle([30,44,30+w,44+h],46,fill=120); sh=sh.filter(ImageFilter.GaussianBlur(16)); im.paste((40,0,10,255),(0,0),sh)
    d.rounded_rectangle([30,30,30+w,30+h],46,fill=(255,255,255,255))
    im.alpha_composite(wtext('Daily views',46,(40,40,46),shadow=False),(60,40))
    for gy,lab in [(0,'0'),(2.1,'2.1L'),(4.3,'4.3L')]:
        y=30+h-60-(gy/4.3)*(h-170)
        d.line([(150,y),(w-10,y)],fill=(225,225,230,255),width=2)
        im.alpha_composite(wtext(lab,30,(130,130,138),shadow=False),(55,int(y-30)))
    k=clamp((t-t0-0.2)/1.6); n=max(2,int(len(CURVE)*k))
    xs=np.linspace(150,w-10,len(CURVE))[:n]; ys=30+h-60-(CURVE[:n]/4.3)*(h-170)
    pts=list(zip(xs,ys))
    d.line(pts,fill=RED+(255,),width=10,joint='curve')
    d.ellipse([xs[-1]-14,ys[-1]-14,xs[-1]+14,ys[-1]+14],fill=RED+(255,),outline=(255,255,255,255),width=5)
    for lab,fx_ in [('Oct 11',0.05),('Oct 25',0.48),('Nov 9',0.92)]:
        im.alpha_composite(wtext(lab,30,(130,130,138),shadow=False),(int(150+(w-160)*fx_-50),h-10))
    place(base,im,540,1060,eob(clamp((t-t0)/0.45)),0,a)
def topreel(base,t,t0,t1):
    if not (t0<=t<=t1+0.25): return
    a=1-clamp((t-t1)/0.22) if t>t1 else 1
    c=card(TH[0],560,523); p=eob(clamp((t-t0)/0.5)); z=1+0.04*(t-t0)
    place(base,c,540,1060,p*z,-3+1.5*math.sin(t*2),a)
    pl=pill_label('Hazri kam... bahane zyada',44); place(base,pl,540,1400,pop(t,t0+0.4),3,a)
def avatar_(base,name,t,tin,sc=0.5,bottom=1880): avatar(base,name,t,tin,sc,540,bottom)
SC=[(0,9.08,'grey'),(9.08,9.69,'red'),(9.69,16.94,'grey'),(16.94,22.63,'grey2'),(22.63,26.01,'grey3'),(26.01,30.43,'grey4'),(30.43,33.71,'grey5'),(33.71,36.27,'red2'),(36.27,40.41,'grey6'),(40.41,T,'grey7')]
TR=[9.08,9.69,16.94,22.63,26.01,30.43,33.71,36.27,40.41]
def frame(t):
    sk=None
    red=(9.08<=t<9.69) or (34.65<=t<36.27)
    base=redbg() if red else greybg(); BASE[0]=base
    # ---- scene content
    if t<9.08:
        if t<6.09: avatar_(base,'02_avatar_arms_crossed' if t<3.63 else '06_avatar_thumbs_up',t,0.1 if t<3.63 else 3.5)
        else: avatar_(base,'04_avatar_shrug',t,6.0)
        W_('30 din pehle',t,0.05,3.55,540,300,120)
        if t<3.63: counter(t,1.34,3.55,0,1427,540,560,250,0.9); W_('followers',t,1.6,3.55,700,760,96,RED,2)
        W_('Aaj',t,3.63,6.0,320,300,140,RED,-4)
        if 3.63<=t<6.05:
            counter(t,4.4,6.0,1427,12586,540,560,250,1.1); pl='+11,159'
            if t>=5.0: anim(base,pill_label('+11,159 in 30 din',52),540,800,t,5.0,6.0,0.35,3,'pop')
            if t>=5.5: sk=5.5
        W_('In 30 dinon mein',t,6.09,9.0,540,330,100)
        R_('asal mein',t,6.8,9.0,540,520,190); W_('kya hua?',t,7.86,9.0,700,700,120,(255,255,255),3)
    elif t<9.69:
        im=wtext('DEKHIYE',210,(255,255,255),'Poppins-Bold.ttf'); place(base,im,540,960,1+max(0,1-(t-9.08)/0.15)*1.2,-4); sk=9.08
    elif t<16.94:
        orbit(base,t,9.69,16.8,front=False)
        avatar_(base,'03_avatar_point_up' if t<13.51 else '04_avatar_shrug',t,9.69 if t<13.51 else 13.4)
        orbit(base,t,9.69,16.8,front=True)
        if t<11.08: R_('62 LAKH',t,9.69,11.0,540,300,230); W_('views',t,10.0,11.0,760,460,100,(255,255,255),3)
        elif t<13.51: R_('39 LAKH',t,11.08,13.4,540,300,230); W_('logon ne dekhi',t,11.5,13.4,560,460,92,(255,255,255),3)
        else:
            R_('90%',t,13.51,16.85,540,300,300,-3,'slam')
            if t<13.6: sk=13.51
            W_('follow bhi',t,15.39,16.85,400,500,92,(255,255,255),-3); W_('nahi karte the',t,15.7,16.85,640,640,92,RED,3)
    elif t<22.63:
        W_('Delhi se Jalandhar tak',t,16.94,22.55,540,260,80,(255,255,255),-2)
        bars(base,t,16.94,22.55,[('Delhi',8.0,16.94),('Mumbai',2.6,17.83),('Ludhiana',2.2,18.53),('Jalandhar',2.0,20.10)],cy0=700,step=200,maxv=8.0)
        if t>=20.3: anim(base,pill_label('mera apna',48),760,1390,t,20.3,22.55,0.35,4,'pop')
        if t>=21.41: R_('sirf India nahi',t,21.41,22.55,540,1600,150)
        if 20.10<=t<20.2: sk=20.10
    elif t<26.01:
        W_('Duniya bhar se',t,22.63,25.95,540,260,90,(255,255,255),-2)
        bars(base,t,22.63,25.95,[('India',81.4,22.63),('Pakistan',10.8,22.63+0.25),('UAE',1.4,23.55),('Canada',1.2,24.44),('UK',1.0,25.0)],cy0=640,step=190,maxv=81.4)
    elif t<30.43:
        W_('Har din',t,26.01,30.35,330,280,130,(255,255,255),-4)
        R_('~2 LAKH views',t,27.25,30.35,540,470,170)
        graph(base,t,26.3,30.35)
        W_('bina ruke',t,29.47,30.35,540,1460,110,RED,2)
    elif t<33.71:
        W_('ek akeli reel',t,30.43,33.6,540,280,104,(255,255,255),-3)
        R_('12 LAKH',t,31.79,33.6,540,480,240,-3,'slam')
        if 31.79<=t<31.9: sk=31.79
        topreel(base,t,30.6,33.6)
    elif t<36.27:
        if t<34.65:
            avatar_(base,'04_avatar_shrug',t,33.6); W_('Sochiye...',t,33.71,34.6,540,420,140)
        else:
            im=wtext('PAGALPAN',190,(255,255,255)); place(base,im,540,900,1+max(0,1-(t-34.65)/0.15)*1.2,-4)
            W_('hai ye',t,34.9,36.2,540,1130,100,(255,190,195),3); sk=34.65
    elif t<40.41:
        avatar_(base,'06_avatar_thumbs_up',t,36.2)
        place(base,asset(A+'20_prop_heart.png',0.3),830,820,pop(t,37.1)*(1+0.06*math.sin(t*8)),10) if t>=37.1 else None
        W_('Toh sach mein',t,36.27,40.3,540,250,96)
        R_('SHUKRIYA',t,37.02,40.3,540,430,220)
        W_('ye sab aapki wajah se',t,38.39,40.3,540,620,78,(255,255,255),2)
    else:
        if t<45.27:
            avatar_(base,'05_avatar_phone',t,40.3)
            W_('AI se editing',t,40.41,45.2,540,250,100,(255,255,255),-3)
            R_('seekhni hai?',t,40.9,42.7,540,430,170)
            W_('ya raw video',t,42.75,45.2,540,630,96,(255,255,255),3)
            R_('edit karwani hai?',t,43.1,45.2,540,800,140)
        elif t<46.47:
            avatar_(base,'03_avatar_point_up',t,45.2)
            R_('DM karo',t,45.27,46.4,540,450,260,-3,'slam'); sk=45.27
            if t>=45.4: place(base,asset(A+'19_prop_dm_bubble.png',0.42),830,800,pop(t,45.4),8)
        else:
            avatar_(base,'01_avatar_wave',t,46.4)
            R_('Follow karo',t,46.47,49.5,540,380,190)
            W_('@aitricksbysumit',t,47.35,49.5,540,600,84,RED,0)
    if sk is not None: base=shake(base,t,sk,14)
    for tc in TR:
        if abs(t-tc)<0.35: base=streak(base,t,tc,0.5) if tc not in (9.08,33.71) else glitch(base,t,tc,0.3,seed=int(tc))
    if t>T-0.4: base=Image.blend(base,Image.new('RGBA',(W,H),(0,0,0,255)),clamp((t-(T-0.4))/0.4))
    return base.convert('RGB')
if __name__=='__main__':
    ts=[float(x) for x in sys.argv[1:]]
    ims=[frame(t).resize((360,640)) for t in ts]
    cols=min(8,len(ims)); rows=(len(ims)+cols-1)//cols
    M=Image.new('RGB',(cols*360,rows*640))
    for i,im in enumerate(ims): M.paste(im,((i%cols)*360,(i//cols)*640))
    M.save('/home/claude/m50/prev.png')
