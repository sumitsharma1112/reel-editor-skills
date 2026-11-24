import json, sys, os, subprocess, numpy as np, cv2
from PIL import Image
sys.path.insert(0,'.')
import reel as R
from reel import *
TM={d['name']:d for d in json.load(open('../vo/timing.json'))}
def A(n,i): return TM[n]['anchors'][i]
def D(n): return TM[n]['dur']
def pw(t,pts):  # piecewise-linear map scene t -> src t
    xs,ys=zip(*pts); return float(np.interp(t,xs,ys))
def img(f): return Image.fromarray(cv2.cvtColor(f,cv2.COLOR_BGR2RGB)).convert('RGBA')

def hook(t,dur):
    f=SRC['c_gemini'].frame(pw(t,[(0,0),(dur,3.30)]))
    box=B(138,582,706,802); f=glass(f,box,r=44,dark=0.55)
    z=kb(t,dur,1.02,1.07); f=zoom(f,z); c=img(f)
    cx,cy=zp(((box[0]+box[2])/2,(box[1]+box[3])/2),z)
    paste(c,T('ਵਿਦੇਸ਼ ਪਾਰਸਲ ਭੇਜਣਾ…',76),cx,cy-62*z,0.92+0.08*ease_out(t/0.25))
    pop(c,T('ਇੰਨਾ ਮਹਿੰਗਾ?? 😳',98,GOLD),cx,cy+58*z,t,max(0.35,A('hook',1)-0.05),0.3)
    return c
def family(t,dur):
    ts_stamp=A('family',5)
    ts=pw(t,[(0,3.40),(ts_stamp-0.06,8.42),(dur,10.0)])
    f=SRC['c_gemini'].frame(ts); band=B(0,765,720,1045); on=ts>=8.44
    if on: f=glass(f,(band[0]-10,band[1],band[2]+10,band[3]),r=0,dark=0.45,border=False,feather=6)
    z=kb(t,dur,1.0,1.06); f=zoom(f,z); c=img(f)
    pop(c,T('ਕੋਰੀਅਰ ਦੇ ਭਾਰੀ ਖ਼ਰਚੇ 😟',80),W/2,300,t,A('family',0),t_out=A('family',3)-0.3)
    pop(c,T('ਫਿਰ ਪੁੱਤ ਬੋਲਿਆ…',84,GOLD),W/2,300,t,A('family',3),t_out=dur-0.25)
    if t>=ts_stamp:
        cx,cy=zp(((band[0]+band[2])/2,(band[1]+band[3])/2),z)
        p=clamp((t-ts_stamp)/0.14); paste(c,stamp('ਡਾਕਘਰ ਹੈ ਨਾ! ✈️',92),cx,cy,2.0-ease_out(p),clamp(p*2))
    return c
def building(t,dur):
    ts=pw(t,[(0,0),(dur,4.95)]); i=min(119,int(round(ts*24))); f=SRC['c_postal'].frame(ts)
    rect=np.float32([[[212,429]],[[560,429]],[[560,505]],[[212,505]]])
    p=cv2.perspectiveTransform(rect,Hs[i]).reshape(-1,2)*S
    x0,y0=p[:,0].min(),p[:,1].min(); x1,y1=p[:,0].max(),p[:,1].max(); x1=min(x1,x0+(x1-x0)*0.95)
    lt=B(80,950,640,1135); f=glass(f,lt,r=36,dark=0.62)
    z=kb(t,dur,1.0,1.04); f=zoom(f,z); c=img(f)
    a0=zp((x0,y0),z); a1=zp((x1,y1),z); w,h=int(a1[0]-a0[0]),int(a1[1]-a0[1])
    if w>20 and h>10:
        pl=sign_plate(max(40,w//8*8),max(20,h//4*4)).resize((w,h),Image.LANCZOS)
        pl=R.shine(pl,(t-1.0)/1.1) if t<2.5 else R.shine(pl,(t-4.2)/1.1)
        c.alpha_composite(pl,(int(a0[0]),int(a0[1])))
    cx,cy=zp(((lt[0]+lt[2])/2,(lt[1]+lt[3])/2),z)
    pop(c,T('ਇੰਟਰਨੈਸ਼ਨਲ ਸਪੀਡ ਪੋਸਟ ✈️',70,GOLD),cx,cy-50,t,A('building',0))
    pop(c,T('📍 ਫ਼ਰੀਦਕੋਟ ਡਾਕ ਮੰਡਲ',66),cx,cy+52,t,A('building',0)+0.35)
    pop(c,pill('ਘੱਟ ਖ਼ਰਚਾ · ਪੂਰਾ ਭਰੋਸਾ',50,bg=GOLD,fg=DARK),cx,cy-190,t,A('building',1))
    return c
def pack(t,dur):
    cut=dur*0.62
    if t<cut:
        ts=pw(t,[(0,7.40),(cut,9.10)]); f=SRC['c_postal'].frame(ts); band=B(0,755,720,1010)
        f=glass(f,(band[0]-10,band[1],band[2]+10,band[3]),r=0,dark=0.6,blur=40,border=False,feather=6); z=kb(t,cut,1.0,1.05)
    else:
        ts=pw(t,[(cut,9.20),(dur,10.0)]); f=SRC['c_postal'].frame(ts); z=kb(t-cut,dur-cut,1.04,1.08)
    f=zoom(f,z); c=img(f); cy=(755+1010)/2*S
    for (s,i),x in zip([('✅ ਸੂਟ',0),('✅ ਤੋਹਫ਼ੇ',1),('✅ ਪਿਆਰ ❤️',2)],[W*0.22,W*0.5,W*0.78]):
        pop(c,pill(s,54,bg=(255,253,247,240),fg=DARK),x,cy if t<cut else 1500,t,A('pack',i))
    return c
def counter(t,dur):
    ts=pw(t,[(0,10.0),(dur,14.9)]); f=SRC['c_postal'].frame(ts); band=B(0,745,720,1150)
    f=glass(f,(band[0]-10,band[1],band[2]+10,band[3]),r=0,dark=0.35,border=False,feather=8)
    z=kb(t,dur,1.0,1.04); f=zoom(f,z); c=img(f)
    cx,cy=zp(((band[0]+band[2])/2,(band[1]+band[3])/2),z)
    a0=A('counter',0); ticks=[a0+0.85,a0+1.45,A('counter',1),A('counter',2)+0.45]
    n=sum(t>=x for x in ticks); p=clamp(t/0.3)
    paste(c,checklist_card(n),cx,cy+(1-ease_out(p))*120,1.0,p); return c
def globe(t,dur):
    ts=pw(t,[(0,0),(dur,4.85)]); f=SRC['c_receive'].frame(ts); band=B(0,262,720,510)
    if ts>=1.05: f=glass(f,(band[0]-10,band[1],band[2]+10,band[3]),r=0,dark=0.5,border=False,feather=10)
    z=kb(t,dur,1.0,1.05); f=zoom(f,z); c=img(f); cy=zp((0,(band[1]+band[3])/2),z)[1]
    t_band=(1.05/4.85)*dur
    ps=[('🇨🇦 ਕੈਨੇਡਾ',W*0.29,cy-72),('🇺🇸 ਅਮਰੀਕਾ',W*0.71,cy-72),('🇬🇧 ਯੂ.ਕੇ.',W*0.29,cy+72),('🇦🇺 ਆਸਟ੍ਰੇਲੀਆ',W*0.71,cy+72)]
    for k,(s,x,y) in enumerate(ps): pop(c,pill(s,52),x,y,t,max(A('globe',k),t_band))
    pop(c,T('ਤੁਹਾਡਾ ਪਿਆਰ, ਹਰ ਕੋਨੇ ਤੱਕ ✈️',78,GOLD),W/2,1560,t,A('globe',4))
    return c
def receive(t,dur):
    ts=pw(t,[(0,5.0),(dur,9.7)]); f=SRC['c_receive'].frame(ts); z=kb(t,dur,1.0,1.06); f=zoom(f,z); c=img(f)
    pop(c,T('ਸੱਤ ਸਮੁੰਦਰ ਪਾਰ…',90),W/2,250,t,A('receive',0),t_out=A('receive',1)-0.2)
    pop(c,T('ਮਾਂ ਦਾ ਪਿਆਰ ਪਹੁੰਚ ਗਿਆ ❤️',84,GOLD),W/2,250,t,A('receive',1))
    return c
def cta(t,dur):
    ts=pw(t,[(0,10.0),(dur,15.0)]); f=SRC['c_receive'].frame(ts); box=B(14,880,706,1262)
    f=glass(f,box,r=48,dark=0.6); z=kb(t,dur,1.0,1.03); f=zoom(f,z); c=img(f)
    bx0,by0=zp((box[0],box[1]),z); bx1,by1=zp((box[2],box[3]),z); cx=(bx0+bx1)/2; y=by0
    pop(c,T('ਅੱਜ ਹੀ ਆਓ 👇',86,GOLD),cx,y+85,t,A('cta',0))
    for k,(s,x) in enumerate([('ਫ਼ਰੀਦਕੋਟ',cx-300),('ਮੋਗਾ',cx-25),('ਮੁਕਤਸਰ',cx+250)]): pop(c,pill(s,58),x,y+215,t,A('cta',k+1))
    pop(c,T('ਜਾਂ ਫ਼ਰੀਦਕੋਟ ਡਾਕ ਮੰਡਲ ਦੇ ਕਿਸੇ ਵੀ ਡਾਕਘਰ',46),cx,y+335,t,A('cta',4))
    pop(c,T('📍 India Post · Faridkot Postal Division',38,(235,235,235,255),font='latin'),cx,y+420,t,A('cta',4)+1.2)
    return c
SC=[('hook',hook),('family',family),('building',building),('pack',pack),('counter',counter),('globe',globe),('receive',receive),('cta',cta)]
def render_scene(k):
    name,fn=SC[k]; dur=D(name); n=int(round(dur*FPS)); out=f'seg2/s{k:02d}_{name}.mp4'
    p=subprocess.Popen(['ffmpeg','-v','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-',
        '-c:v','libx264','-preset','medium','-crf','18','-pix_fmt','yuv420p',out+'.tmp.mp4'],stdin=subprocess.PIPE)
    for i in range(n):
        t=i/FPS; c=fn(t,dur)
        if k>0 and t<0.2:
            pz=1+0.06*(1-ease_out(t/0.2)); c=Image.fromarray(zoom(np.asarray(c.convert('RGB')),pz)).convert('RGBA')
        if k>0: c=R.flash(c,t,False)
        p.stdin.write(np.asarray(c.convert('RGB')).tobytes())
    p.stdin.close(); p.wait(); os.replace(out+'.tmp.mp4',out); print('seg',k,name,n,flush=True)
if __name__=='__main__':
    os.makedirs('seg2',exist_ok=True)
    ks=[int(a) for a in sys.argv[1:]] or range(len(SC))
    if 'still' in os.environ:
        name,fn=SC[ks[0]]
        for tt in [float(x) for x in os.environ['still'].split(',')]: fn(tt,D(name)).convert('RGB').resize((540,960)).save(f'seg2/still_{ks[0]}_{tt:.2f}.jpg')
    else:
        for k in ks: render_scene(k)
