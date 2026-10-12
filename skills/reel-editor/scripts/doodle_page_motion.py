"""Reference-inspired white-page doodle motion (not an exact app preset).

python doodle_page_motion.py --a page_a.png --b page_b.png --effect hinge --out test.mp4
Effects: hinge (3D yaw, black surround), halfturn (180-degree page turn),
dolly (large crop to settled page), inkpulse (recolour ink, preserve paper).
Inputs are complete pages; animate limbs/expressions separately before compositing.
"""
import argparse, math, subprocess
import numpy as np
from PIL import Image, ImageOps

def ease(t):
    t=np.clip(t,0,1)
    return float(t*t*(3-2*t))

def page(im,angle,scale=1,background=0):
    h,w=im.shape[:2];focal=w*1.8
    rad=math.radians(angle)
    pts=[]
    for x,y in [(-w/2,-h/2),(w/2,-h/2),(w/2,h/2),(-w/2,h/2)]:
        depth=-x*math.sin(rad)
        factor=focal/(focal+depth)
        pts.append([w/2+x*math.cos(rad)*factor*scale,h/2+y*factor*scale])
    src=[[0,0],[w,0],[w,h],[0,h]]
    rows=[];values=[]
    for (x,y),(u,v) in zip(pts,src):
        rows.extend([[x,y,1,0,0,0,-u*x,-u*y],[0,0,0,x,y,1,-v*x,-v*y]])
        values.extend([u,v])
    coeff=np.linalg.solve(np.asarray(rows),np.asarray(values))
    return np.array(Image.fromarray(im).transform((w,h),Image.Transform.PERSPECTIVE,coeff,Image.Resampling.BICUBIC,fillcolor=(background,)*3))

def zoom(im,scale):
    h,w=im.shape[:2]
    p=Image.fromarray(im).resize((round(w*scale),round(h*scale)),Image.Resampling.BICUBIC)
    return np.array(p.crop(((p.width-w)//2,(p.height-h)//2,(p.width+w)//2,(p.height+h)//2)))

def effect(a,b,t,mode):
    if mode=='hinge':
        # Reference: outgoing page narrows, incoming page starts small over black,
        # swings close to edge-on, expands and gently settles back to a flat page.
        if t<.25: return page(a,85*ease(t/.25),1-.65*ease(t/.25))
        u=(t-.25)/.75
        angle=-82*(1-ease(u)) + 15*math.sin(3*math.pi*u)*(1-u)
        scale=.3+.7*ease(min(1,u*1.5))+.12*math.sin(math.pi*u)
        return page(b,angle,scale)
    if mode=='halfturn':
        im=a if t<.5 else b
        angle=180*ease(t)
        if t>=.5: angle-=180
        h,w=im.shape[:2]
        return np.array(Image.fromarray(im).rotate(angle,Image.Resampling.BICUBIC,fillcolor=(255,)*3))
    if mode=='dolly': return zoom(b,1+1.1*(1-ease(t)))
    # Dark line art tinted while white paper remains white. Affects captions too,
    # matching the reference's occasional whole-page colour pulses.
    im=b.astype(np.float32)/255
    grey=im[:,:,0]*.299+im[:,:,1]*.587+im[:,:,2]*.114
    palette=np.float32([[.1,.08,.05],[.75,.15,.6],[.8,.45,.1],[.1,.1,.65]])
    phase=t*(len(palette)-1);idx=min(len(palette)-2,int(phase));u=phase-idx
    ink=palette[idx]*(1-u)+palette[idx+1]*u
    result=1-(1-grey[:,:,None])*(1-ink)
    h,w=grey.shape;yy,xx=np.mgrid[0:h,0:w]
    edge=((xx-w/2)/(w/2))**2+((yy-h/2)/(h/2))**2
    vignette=1-.18*(.5+.5*math.sin(t*4*math.pi))*np.clip(edge,0,1)
    return np.uint8(np.clip(result*vignette[:,:,None],0,1)*255)

def main():
    p=argparse.ArgumentParser();p.add_argument('--a',required=True);p.add_argument('--b',required=True)
    p.add_argument('--effect',choices=['hinge','halfturn','dolly','inkpulse'],default='hinge')
    p.add_argument('--duration',type=float,default=1.4);p.add_argument('--width',type=int,default=1080);p.add_argument('--out',required=True)
    args=p.parse_args();w=args.width;h=round(w*16/9)
    pages=[]
    for path in [args.a,args.b]:
        pages.append(np.array(ImageOps.fit(Image.open(path).convert('RGB'),(w,h))))
    n=round(args.duration*30)
    if n<2: raise ValueError('Duration must cover at least two frames')
    cmd=['ffmpeg','-v','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s',f'{w}x{h}','-r','30','-i','-','-an','-c:v','libx264','-preset','fast','-crf','20','-pix_fmt','yuv420p','-movflags','+faststart',args.out]
    proc=subprocess.Popen(cmd,stdin=subprocess.PIPE)
    try:
        for i in range(n): proc.stdin.write(effect(*pages,i/(n-1),args.effect).tobytes())
    finally: proc.stdin.close()
    if proc.wait(): raise RuntimeError('ffmpeg failed')

if __name__=='__main__': main()
