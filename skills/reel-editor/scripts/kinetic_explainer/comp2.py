# kinetic_explainer: faceless AI explainer in the 'red 3D kinetic words' style (cartoon presenter, phone screen-recording, pixel glitch, light streak, halftone transitions, soft SFX). Made with Claude, Nov 2026.
# Paths to inputs (videos, images, fonts, audio) are set near the top: edit them for a new reel.
from comp import *
def shadow_of(im,off=(8,16),blur=14,alpha=0.38):
    a=im.getchannel('A').point(lambda v:int(v*alpha))
    pad=blur*3
    sh=Image.new('RGBA',(im.width+pad*2,im.height+pad*2),(0,0,0,0))
    blk=Image.new('RGBA',im.size,(0,0,0,255)); blk.putalpha(a)
    sh.alpha_composite(blk,(pad,pad)); sh=sh.filter(ImageFilter.GaussianBlur(blur))
    return sh,pad
def place_sh(base,im,cx,cy,s=1.0,rot=0,a=1.0,off=(8,16)):
    if s<=0.01: return
    sh,pad=shadow_of(im)
    place(base,sh,cx+off[0]*s,cy+off[1]*s,s,rot,a)
    place(base,im,cx,cy,s,rot,a)
def glass(base,cx,cy,w,h,r=38,tint=(255,255,255,60),border=(255,255,255,120)):
    x0=int(cx-w/2);y0=int(cy-h/2)
    x0c=max(x0,0);y0c=max(y0,0);x1c=min(x0+w,W);y1c=min(y0+h,H)
    card=Image.new('RGBA',(w,h),(0,0,0,0))
    if x1c>x0c and y1c>y0c:
        bk=base.crop((x0c,y0c,x1c,y1c)).filter(ImageFilter.GaussianBlur(18))
        full=Image.new('RGBA',(w,h),(0,0,0,0)); full.paste(bk,(x0c-x0,y0c-y0)); card=full
    m=Image.new('L',(w,h),0); ImageDraw.Draw(m).rounded_rectangle([0,0,w-1,h-1],r,fill=255)
    card.putalpha(m)
    card.alpha_composite(Image.new('RGBA',(w,h),tint))
    card.putalpha(m)
    d=ImageDraw.Draw(card); d.rounded_rectangle([0,0,w-1,h-1],r,outline=border,width=2)
    return card
def glass_out(base,card,cx,cy,s=1.0,rot=0,a=1.0):
    place_sh(base,card,cx,cy,s,rot,a,off=(0,18))
def vignette(im,k=0.28):
    arr=np.asarray(im.convert('RGB')).astype(np.float32)
    yy,xx=np.mgrid[0:H,0:W]; d=np.sqrt(((xx-W/2)/(W/2))**2+((yy-H/2)/(H/2))**2)
    m=1-k*np.clip(d-0.55,0,1)**1.5
    return Image.fromarray((arr*m[:,:,None]).astype(np.uint8)).convert('RGBA')
_vg=None
def vig(im):
    global _vg
    if _vg is None:
        yy,xx=np.mgrid[0:H,0:W]; d=np.sqrt(((xx-W/2)/(W/2))**2+((yy-H/2)/(H/2))**2)
        _vg=(1-0.30*np.clip(d-0.55,0,1)**1.5).astype(np.float32)
    arr=np.asarray(im.convert('RGB')).astype(np.float32)*_vg[:,:,None]
    return Image.fromarray(arr.astype(np.uint8)).convert('RGBA')
def notif(base,cx,cy,t,t0,title,body,sub='अभी',scale=1.0):
    x=pop(t,t0,0.42)
    if x<=0: return
    w,h=900,150
    card=glass(base,cx,cy,w,h,r=40,tint=(255,255,255,175),border=(255,255,255,200))
    d=ImageDraw.Draw(card)
    d.rounded_rectangle([24,24,24+102,24+102],26,fill=(37,211,102,255))
    d.ellipse([46,44,104,96],fill=(255,255,255,255)); d.polygon([(52,86),(46,108),(72,92)],fill=(255,255,255,255)); d.ellipse([62,60,88,80],fill=(37,211,102,255))
    card.alpha_composite(text_img(title,36,(30,30,34),dev='baloo'),(146,10))
    card.alpha_composite(text_img(body,40,(55,55,60),dev='baloo'),(146,58))
    card.alpha_composite(text_img(sub,30,(120,120,128),dev='baloo'),(w-text_img(sub,30,(120,120,128)).width-26,8))
    off=(1-clamp(x,0,1))*500
    glass_out(base,card,cx+off,cy,min(x,1.05),0,a=clamp(x*2))
def check_mark(d,x,y,sz,col=(40,190,90,255),w=8):
    d.line([(x,y+sz*0.5),(x+sz*0.35,y+sz*0.85),(x+sz,y+sz*0.1)],fill=col,width=w,joint='curve')
def todo(base,cx,cy,t,t0,title,items,ticks,done_all_col=(40,190,90),w=820,rowh=92):
    x=pop(t,t0,0.45)
    if x<=0: return
    h=100+rowh*len(items)+24
    card=glass(base,cx,cy,w,h,r=44,tint=(255,255,255,205),border=(255,255,255,230))
    card.alpha_composite(text_img(title,50,(25,25,30),dev='baloo'),(40,6))
    d=ImageDraw.Draw(card)
    for i,it in enumerate(items):
        y=96+i*rowh
        ticked=ticks[i] is not None and t>=ticks[i]
        d.rounded_rectangle([40,y+14,40+56,y+14+56],16,fill=(done_all_col+(255,)) if ticked else (255,255,255,255),outline=(150,150,160,255),width=4)
        if ticked:
            k=clamp((t-ticks[i])/0.2); check_mark(d,52,y+24,34*k if k>0 else 1,col=(255,255,255,255),w=8)
        ti=text_img(it,46,(120,120,128) if ticked else (30,30,36),dev='baloo')
        card.alpha_composite(ti,(120,y+2))
        if ticked: d.line([(120,y+44),(120+ti.width-16,y+44)],fill=(120,120,128,255),width=4)
    glass_out(base,card,cx,cy,min(x,1.04),0,a=clamp(x*2))
def receipt(base,cx,cy,t,t0,lines,dur=1.0,rot=4):
    if t<t0: return
    w=440; lh=62; h=120+lh*len(lines)+50
    im=Image.new('RGBA',(w,h),(0,0,0,0)); d=ImageDraw.Draw(im)
    pts=[(0,0),(w,0)]; zz=h-24
    pts+= [(w,zz)]
    n=14
    for i in range(n): pts+= [(w-(i*2+1)*w/(2*n),h),(w-(i*2+2)*w/(2*n),zz)]
    d.polygon(pts,fill=(253,253,250,255))
    im.alpha_composite(text_img('AI  ORDER SLIP',40,(30,30,34)),(40,2))
    d.line([(30,76),(w-30,76)],fill=(60,60,66,255),width=3)
    for i,l in enumerate(lines):
        im.alpha_composite(text_img(l,46,(25,25,30),align='left'),(34,86+i*lh))
    k=clamp((t-t0)/dur); k=1-(1-k)**2
    vis=int(h*k)
    clip=im.crop((0,0,w,max(vis,1)))
    full=Image.new('RGBA',(w,h),(0,0,0,0)); full.alpha_composite(clip,(0,h-vis))
    full=full.crop((0,h-vis,w,h)) if False else full
    # slide down: top fixed, bottom revealed
    full=Image.new('RGBA',(w,h),(0,0,0,0)); full.alpha_composite(clip,(0,0))
    place_sh(base,full,cx,cy-(h-vis)/2+0,1.0,rot)
def cursor_img():
    im=Image.new('RGBA',(90,110),(0,0,0,0)); d=ImageDraw.Draw(im)
    pts=[(10,6),(10,80),(30,62),(44,96),(58,90),(44,58),(72,58)]
    d.polygon(pts,fill=(255,255,255,255),outline=(0,0,0,255)); d.line(pts+[pts[0]],fill=(0,0,0,255),width=5)
    return im
def cursor(base,t,t_click,tgt,start=(930,420),lead=0.9):
    if not (t_click-lead<=t<=t_click+0.55): return
    u=clamp((t-(t_click-lead))/(lead-0.12)); u=1-(1-u)**3
    x=start[0]+(tgt[0]-start[0])*u; y=start[1]+(tgt[1]-start[1])*u
    press=(t>=t_click-0.08 and t<t_click+0.12)
    place(base,cursor_img(),x+22,y+34,0.9 if press else 1.0)
    if t>=t_click:
        k=clamp((t-t_click)/0.45)
        ring=Image.new('RGBA',(300,300),(0,0,0,0)); ImageDraw.Draw(ring).ellipse([150-int(120*k),150-int(120*k),150+int(120*k),150+int(120*k)],outline=(255,255,255,int(220*(1-k))),width=8)
        place(base,ring,tgt[0],tgt[1],1.0)
def bars(base,cx,cy,t,t0):
    x=pop(t,t0,0.45)
    if x<=0: return
    w,h=900,330
    card=glass(base,cx,cy,w,h,r=46,tint=(255,255,255,200),border=(255,255,255,230))
    card.alpha_composite(text_img('समय की तुलना',46,(25,25,30)),(40,0))
    d=ImageDraw.Draw(card)
    k=clamp((t-t0-0.3)/0.9); k=1-(1-k)**3
    def row(y,label,frac,col,val):
        card.alpha_composite(text_img(label,40,(60,60,66),align='left'),(40,y))
        d.rounded_rectangle([40,y+78,w-40,y+78+34],17,fill=(225,225,230,255))
        bw=max(34,int((w-80)*frac*k)); d.rounded_rectangle([40,y+78,40+bw,y+78+34],17,fill=col+(255,))
        vi=text_img(val,40,col,dev='baloo')
        card.alpha_composite(vi,(w-40-vi.width,y))
    row(76,'हाथ से टाइप करना',1.0,(230,50,60),'घंटों')
    row(200,'AI से',0.05,(40,190,90),'2 मिनट')
    glass_out(base,card,cx,cy,min(x,1.04),0,a=clamp(x*2))
