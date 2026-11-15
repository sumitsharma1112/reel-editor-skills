import numpy as np, cv2, subprocess, math, sys, os
from PIL import Image, ImageDraw, ImageFont, ImageFilter
W,H,FPS,DUR=1080,1920,30,12.0
FD='/home/claude/effects/fonts/'
F=lambda n,s: ImageFont.truetype(FD+n,s)
def MS(s,w='SemiBold'):
    f=ImageFont.truetype(FD+'Montserrat.ttf',s); f.set_variation_by_name(w); return f
ease=lambda x: 1-(1-max(0,min(1,x)))**3
def back(x,c=1.70158):
    x=max(0,min(1,x)); return 1+(c+1)*(x-1)**3+c*(x-1)**2
CZ=lambda n: Image.open(f'cz/{n}.png').convert('RGBA')
def fit_h(im,h): return im.resize((max(1,int(im.width*h/im.height)),h),Image.LANCZOS)
# ---------- static background: dark room ----------
yy,xx=np.mgrid[0:H,0:W].astype(np.float32)
VP=(540,960)
top=np.array([10,12,26.]); mid=np.array([16,14,34.])
bg=top*(1-(yy/H))[...,None]+mid*(yy/H)[...,None]
def glow(cx,cy,r,col,a): d=np.hypot(xx-cx,yy-cy)/r; return np.exp(-d*d)[...,None]*np.array(col)*a
bg=bg+glow(540,960,620,(0,190,255),0.18)+glow(900,380,420,(255,170,60),0.22)+glow(160,1500,520,(140,60,255),0.20)
rng=np.random.default_rng(5); bg=np.clip(bg+rng.normal(0,2.5,(H,W,1)),0,255).astype(np.uint8)
BG=Image.fromarray(bg).convert('RGBA')
# ---------- assets ----------
AV=fit_h(CZ('avatar_point_side'),740)
ROBOT=fit_h(CZ('prop_ai_robot'),230)
CHIP=fit_h(CZ('prop_ai_chip'),120)
QM=fit_h(CZ('prop_question_marks'),300)
ICONS={'Stories':fit_h(CZ('prop_storybook'),44),'Books I read':fit_h(CZ('prop_book_stack'),52),
 'YouTube channel recommendations':fit_h(CZ('prop_retro_tv_play'),52),'Mera content creation journey':fit_h(CZ('prop_phone_tripod'),56),
 'Voice over kaha se banata hu?':fit_h(CZ('prop_studio_mic'),56)}
CHIPS=list(ICONS.keys())
FC=MS(30)
# shadows for cutouts
def with_shadow(im,blur=18,off=(10,16),a=120):
    sh=Image.new('RGBA',(im.width+80,im.height+80),(0,0,0,0))
    m=im.split()[3].point(lambda v:v*a//255); blk=Image.new('RGBA',im.size,(0,0,0,255)); blk.putalpha(m)
    sh.alpha_composite(blk,(40+off[0],40+off[1])); sh=sh.filter(ImageFilter.GaussianBlur(blur)); sh.alpha_composite(im,(40,40)); return sh
AVS=with_shadow(AV); ROBS=with_shadow(ROBOT,14,(6,10),90)
# ---------- wall panel texture ----------
PW,PH=1000,520
def panel_tex(t):
    p=Image.new('RGBA',(PW,PH),(246,236,214,255)); d=ImageDraw.Draw(p)
    n=Image.fromarray(np.clip(np.random.default_rng(1).normal(0,7,(PH,PW)),-20,20).astype(np.int16).astype(np.uint8)+0) # grain
    words=[('ASK',0.9,(110,95),215,(22,22,34)),('ME',1.25,(500,95),215,(22,22,34)),('ANYTHING',1.6,(60,295),195,(232,88,28))]
    glitch=False
    for w,t0,(x,y),s,col in words:
        p_=(t-t0)/0.22
        if p_<=0: continue
        sc=1+0.5*(1-back(p_)) if p_<1 else 1
        f=F('Anton-Regular.ttf',int(s*sc))
        b=d.textbbox((0,0),w,font=f); bw=b[2]-b[0]; bh=b[3]-b[1]
        b0=F('Anton-Regular.ttf',s); bb=d.textbbox((0,0),w,font=b0); cx=x+(bb[2]-bb[0])/2; cy=y+(bb[3]-bb[1])/2
        if w=='ANYTHING': cx=PW/2
        al=int(255*min(1,p_*1.5))
        if 0<p_<1.6: glitch=True
        d.text((cx-bw/2-b[0],cy-bh/2-b[1]),w,font=f,fill=col+(al,))
    # thin rule + kicker
    if t>2.0:
        a=int(255*ease((t-2.0)/0.4)); d.text((64,22),'AMA  ·  LIVE  ·  @aitricksbysumit',font=F('SpaceMono-Bold.ttf',26),fill=(120,110,95,a))
    return p,glitch
def quad(t):
    p=back((t-0.45)/0.6,1.2)
    final=np.float32([[80,430],[1010,330],[1010,900],[80,820]])
    flat=np.float32([[545,430],[545,330],[545,900],[545,820]])
    q=flat+(final-flat)*p
    sway=6*math.sin(t*0.9); q[:,1]+=np.array([sway,-sway,-sway,sway])*0.6
    return q, p
def grid_layer(t):
    L=Image.new('RGBA',(W,H),(0,0,0,0)); d=ImageDraw.Draw(L)
    for k in range(-9,10):
        xb=540+k*190; d.line([VP,(xb,H)],fill=(0,200,255,40),width=2)
    off=(t*0.35)%1
    for i in range(14):
        z=(i+off)/14; y=VP[1]+(H-VP[1])*(z**2.2)
        a=int(70*z); d.line([(0,y),(W,y)],fill=(0,200,255,a),width=2)
    return L
def text_c(d,txt,cx,y,f,fill,stroke=0,sf=None):
    b=d.textbbox((0,0),txt,font=f,stroke_width=stroke); w=b[2]-b[0]
    d.text((cx-w/2-b[0],y-b[1]),txt,font=f,fill=fill,stroke_width=stroke,stroke_fill=sf)
SLOT=(380,1010,1030,1290)
CHIP_Y=[1360,1432,1504,1576,1648]; CHIP_X=700
def frame(t):
    im=BG.copy()
    im.alpha_composite(grid_layer(t))
    # faint floating question marks prop
    a=ease((t-0.2)/1.0)
    if a>0:
        q=QM.copy(); q.putalpha(q.split()[3].point(lambda v:int(v*0.22*a)))
        im.alpha_composite(q,(int(820+10*math.sin(t)),int(1080+14*math.sin(t*0.8))))
    L=Image.new('RGBA',(W,H),(0,0,0,0)); d=ImageDraw.Draw(L)
    # handle pill
    a=ease((t-0.2)/0.5)
    if a>0:
        f=F('SpaceMono-Bold.ttf',34); txt='@aitricksbysumit'; b=d.textbbox((0,0),txt,font=f); w=b[2]-b[0]
        yo=290+20*(1-a)
        d.rounded_rectangle([600-w/2-28,yo-28,600+w/2+28,yo+28],28,fill=(255,255,255,int(36*a)),outline=(0,210,255,int(160*a)),width=2)
        text_c(d,txt,600,yo-(b[3]-b[1])/2-2,f,(255,255,255,int(255*a)))
    im.alpha_composite(L)
    # AI chip (top-left), gentle float + glow
    a=ease((t-0.3)/0.5)
    if a>0:
        c=CHIP.rotate(6*math.sin(t*1.5),resample=Image.BICUBIC,expand=True)
        c.putalpha(c.split()[3].point(lambda v:int(v*a)))
        im.alpha_composite(c,(70,int(250+6*math.sin(t*2))))
    # wall panel
    q,p=quad(t)
    if p>0.02:
        tex,gl=panel_tex(t)
        src=np.float32([[0,0],[PW,0],[PW,PH],[0,PH]])
        M=cv2.getPerspectiveTransform(src,q)
        arr=np.array(tex)
        if gl:
            sh=7; r=np.roll(arr[...,0],sh,1); b_=np.roll(arr[...,2],-sh,1); arr=arr.copy(); arr[...,0]=r; arr[...,2]=b_
        wp=cv2.warpPerspective(arr,M,(W,H),flags=cv2.INTER_LINEAR,borderValue=(0,0,0,0))
        # shadow
        sh_=np.zeros((H,W,4),np.uint8); cv2.fillPoly(sh_,[ (q+np.float32([18,26])).astype(np.int32)],(0,0,0,150))
        im.alpha_composite(Image.fromarray(sh_).filter(ImageFilter.GaussianBlur(22)))
        im.alpha_composite(Image.fromarray(wp))
        G=Image.new('RGBA',(W,H),(0,0,0,0)); gd=ImageDraw.Draw(G)
        gd.polygon([tuple(v) for v in q],outline=(0,220,255,int(230*min(1,p))),width=5)
        im.alpha_composite(G.filter(ImageFilter.GaussianBlur(8))); im.alpha_composite(G)
    # robot near wall corner
    a=ease((t-2.4)/0.6)
    if a>0:
        r=ROBS.copy(); r.putalpha(r.split()[3].point(lambda v:int(v*a)))
        im.alpha_composite(r,(int(850+6*math.sin(t*1.7)),int(590+(1-a)*80+12*math.sin(t*2.2))))
    L=Image.new('RGBA',(W,H),(0,0,0,0)); d=ImageDraw.Draw(L)
    # typed serif line + cursor
    txt='kuch bhi poocho'; t0=2.0; n=int(max(0,min(len(txt),(t-t0)/0.06)))
    if t>t0:
        f=F('InstrumentSerif-Italic.ttf',112); full=d.textbbox((0,0),txt,font=f); fw=full[2]-full[0]
        x0=540-fw/2; y0=880
        d.text((x0-full[0],y0),txt[:n],font=f,fill=(120,240,190,255))
        cb=d.textbbox((0,0),txt[:n] or ' ',font=f); cx=x0+(cb[2]-cb[0] if n else 0)+8
        if (int(t*2.2)%2==0) or n<len(txt): d.rectangle([cx,y0+30,cx+6,y0+128],fill=(120,240,190,255))
    im.alpha_composite(L)
    # sticker slot (frosted glass)
    a=ease((t-3.0)/0.5)
    M=Image.new('L',(W,H),0); md=ImageDraw.Draw(M)
    chip_boxes=[]
    for k,txt in enumerate(CHIPS):
        p_=(t-(3.6+k*0.32))/0.4
        if p_<=0: continue
        s_=back(min(p_,1)); al=min(1,p_*2)
        ic=ICONS[txt]; b=FC.getbbox(txt); tw=b[2]-b[0]
        w=(tw+ic.width+70)*s_; h=62*s_; cy=CHIP_Y[k]+4*math.sin(t*2+k)
        box=(CHIP_X-w/2,cy-h/2,CHIP_X+w/2,cy+h/2); chip_boxes.append((k,txt,box,al,s_))
        md.rounded_rectangle(box,int(h/2),fill=int(255*al))
    if a>0: md.rounded_rectangle(SLOT,44,fill=int(255*a))
    fro=im.filter(ImageFilter.GaussianBlur(20)); fro=Image.blend(fro,Image.new('RGBA',(W,H),(255,255,255,255)),0.12)
    im=Image.composite(fro,im,M)
    L=Image.new('RGBA',(W,H),(0,0,0,0)); d=ImageDraw.Draw(L)
    if a>0:
        pulse=0.5+0.5*math.sin(t*4)
        d.rounded_rectangle(SLOT,44,outline=(0,220,255,int((120+110*pulse)*a)),width=4)
    for k,txt,box,al,s_ in chip_boxes:
        d.rounded_rectangle(box,int((box[3]-box[1])/2),outline=(255,255,255,int(150*al)),width=2)
    im.alpha_composite(L)
    for k,txt,box,al,s_ in chip_boxes:
        if s_<0.85: continue
        ic=ICONS[txt]; cy=(box[1]+box[3])/2
        im.alpha_composite(ic,(int(box[0]+22),int(cy-ic.height/2)))
        L=Image.new('RGBA',(W,H),(0,0,0,0)); d=ImageDraw.Draw(L)
        b=FC.getbbox(txt); d.text((box[0]+22+ic.width+14-b[0],cy-(b[3]-b[1])/2-b[1]),txt,font=FC,fill=(255,255,255,int(255*al)))
        im.alpha_composite(L)
    # avatar slides up from bottom-left, points at slot
    a=(t-2.6)/0.6
    if a>0:
        y=int(940+ (1-back(min(a,1)))*900 + 6*math.sin(t*1.6))
        im.alpha_composite(AVS,(-60,y))
    out=np.array(im.convert('RGB'))
    if t<0.25: out=(out*(t/0.25)).astype(np.uint8)
    return out
if __name__=='__main__':
    if len(sys.argv)>1:
        for tt in map(float,sys.argv[1:]): Image.fromarray(frame(tt)).save(f'g_{tt}.png')
        sys.exit()
    p=subprocess.Popen(['ffmpeg','-y','-loglevel','error','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-',
      '-c:v','libx264','-preset','veryfast','-crf','18','-pix_fmt','yuv420p','-movflags','+faststart','tmp_v.mp4'],stdin=subprocess.PIPE)
    for i in range(int(DUR*FPS)): p.stdin.write(frame(i/FPS).tobytes())
    p.stdin.close(); p.wait()
    if p.returncode==0: os.replace('tmp_v.mp4','ama3_video.mp4')
