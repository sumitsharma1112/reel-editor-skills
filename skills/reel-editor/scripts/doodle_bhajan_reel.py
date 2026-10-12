"""Animate generated white-page doodle scenes with timed Roman serif lyrics.
JSON: duration, audio, scenes [{start,end,image,lines:[...]}]. Paths relative to spec.
Artwork breathes/bobs as a whole sprite; it does not perform skeletal animation.
"""
import argparse,json,math,subprocess
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont,ImageFilter
from doodle_page_motion import page
W,H=1080,1920
def asset(path):
    im=Image.open(path).convert('RGB');arr=np.asarray(im)
    grey=arr.mean(axis=2);yy,xx=np.where(grey<140)
    if not len(xx): raise ValueError(f'No drawing in {path}')
    im=im.crop((max(0,xx.min()-10),max(0,yy.min()-10),min(im.width,xx.max()+11),min(im.height,yy.max()+11)))
    ratio=min(810/im.width,660/im.height);im=im.resize((round(im.width*ratio),round(im.height*ratio)),Image.Resampling.LANCZOS)
    grey=np.asarray(im).mean(axis=2)
    return np.uint8(np.clip((245-grey)/220,0,1)*255)
def font(text,size=69):
    p=Path(__file__).resolve().parents[1]/'fonts'/'cormorant-garamond-700i.ttf'
    f=ImageFont.truetype(str(p),size)
    while f.getlength(text)>840:
        size-=1;f=ImageFont.truetype(str(p),size)
    return f
def render(spec,root,out,preview=None):
    scenes=spec['scenes'];sprites=[asset(root/s['image']) for s in scenes]
    def frame(t):
        idx=max(i for i,s in enumerate(scenes) if t>=s['start']);s=scenes[idx]
        age=t-s['start'];phase=age*2*math.pi
        im=Image.new('RGB',(W,H),'white')
        a=Image.fromarray(sprites[idx]);a=a.resize((round(a.width*(1+.012*math.sin(phase))),round(a.height*(1-.012*math.sin(phase)))),Image.Resampling.BICUBIC)
        palette=[(30,28,30),(48,49,113),(139,49,102),(24,115,145)]
        # Intermittent ink pulses, leaving most frames black like the reference.
        color=palette[int(age/.45)%4] if age%3<1.1 else palette[0]
        ink=Image.new('RGB',a.size,color)
        im.paste(ink,(490-a.width//2,1150-a.height//2+round(4*math.sin(phase))),a)
        draw=ImageDraw.Draw(im)
        lines=s['lines'];ys=[620] if len(lines)==1 else [580,660]
        alpha=min(1,age/.16)
        col=tuple(round(255+(v-255)*alpha) for v in (155,132,62))
        for text,y in zip(lines,ys): draw.text((490,y),text,font=font(text),fill=col,anchor='mm')
        # Actual scene changes get the 3D page swing. Caption-only changes stay flat.
        if idx and s['image']!=scenes[idx-1]['image'] and age<.68:
            u=age/.68
            angle=-82*(1-u)**2 + 8*math.sin(math.pi*u)
            arr=page(np.asarray(im),angle,.42+.58*(1-(1-u)**3))
            im=Image.fromarray(arr)
        elif age%4>.0 and age%4<.65:
            # Subtle edge vignette pulse, much lighter than the page-turn surround.
            small=Image.new('L',(108,192),255)
            d=ImageDraw.Draw(small);d.rectangle((0,0,107,191),outline=215,width=12)
            mask=small.filter(ImageFilter.GaussianBlur(14)).resize((W,H))
            arr=np.asarray(im).astype(float)*np.asarray(mask)[:,:,None]/255
            im=Image.fromarray(np.uint8(arr))
        return im
    if preview:
        sheet=Image.new('RGB',(1080,960))
        for i,s in enumerate(scenes):sheet.paste(frame(s['start']+.9).resize((270,480)),((i%4)*270,(i//4)*480))
        sheet.save(preview)
    cmd=['ffmpeg','-v','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r','30','-i','-','-i',str(root/spec['audio']),'-map','0:v','-map','1:a','-c:v','libx264','-threads','4','-preset','fast','-crf','20','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-t',str(spec['duration']),'-movflags','+faststart',str(out)]
    proc=subprocess.Popen(cmd,stdin=subprocess.PIPE)
    try:
        for n in range(math.ceil(spec['duration']*30)):proc.stdin.write(frame(n/30).tobytes())
    finally:proc.stdin.close()
    if proc.wait():raise RuntimeError('ffmpeg failed')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--spec',required=True);p.add_argument('--out',required=True);p.add_argument('--preview');a=p.parse_args()
    path=Path(a.spec).resolve();render(json.loads(path.read_text()),path.parent,a.out,a.preview)
