"""Black-page kinetic lyric cards. JSON: duration, cards(start,end,lines).
Each line has text, font (bold/script/outline), size, y, delay, color.
Render with --spec JSON --out MP4; optional --audio matching soundtrack.
"""
import argparse,json,subprocess
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont,ImageFilter

W,H,FPS=1080,1920,30
FONTS=Path(__file__).resolve().parents[1]/'fonts'
def ease(v):
    return 1-(1-max(0,min(1,v)))**3
def layer(line):
    style=line.get('font','bold')
    fontfile={'bold':'montserrat-900.ttf','script':'great-vibes-400.ttf','outline':'montserrat-900.ttf'}[style]
    font=ImageFont.truetype(str(FONTS/fontfile),line.get('size',100))
    text=line['text']; box=font.getbbox(text,stroke_width=2)
    im=Image.new('RGBA',(box[2]-box[0]+40,box[3]-box[1]+40))
    draw=ImageDraw.Draw(im); color=line.get('color','#EDB84F' if style!='bold' else '#FFFFFF')
    draw.text((20-box[0],20-box[1]),text,font=font,fill=(0,0,0,0) if style=='outline' else color,stroke_width=2 if style=='outline' else 0,stroke_fill=color)
    if style=='outline': im=im.resize((round(im.width*.72),im.height),Image.Resampling.LANCZOS)
    if im.width>820: im=im.resize((820,round(im.height*820/im.width)),Image.Resampling.LANCZOS)
    glow=im.filter(ImageFilter.GaussianBlur(7)); glow.putalpha(glow.getchannel('A').point(lambda v:int(v*.25)))
    glow.alpha_composite(im)
    return glow
def render(spec,out,audio=None):
    cards=spec['cards']; cached=[[layer(l) for l in c['lines']] for c in cards]
    cmd=['ffmpeg','-v','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-']
    if audio: cmd+=['-i',audio,'-map','0:v','-map','1:a:0','-c:a','aac','-b:a','192k']
    cmd+=['-t',str(spec['duration']),'-c:v','libx264','-preset','fast','-crf','19','-pix_fmt','yuv420p','-movflags','+faststart',out]
    proc=subprocess.Popen(cmd,stdin=subprocess.PIPE)
    for n in range(round(spec['duration']*FPS)):
        t=n/FPS; frame=Image.new('RGBA',(W,H),(0,0,0,255))
        for c,images in zip(cards,cached):
            if not c['start']<=t<c['end']: continue
            local=t-c['start']; remaining=c['end']-t
            for i,(l,base) in enumerate(zip(c['lines'],images)):
                age=local-l.get('delay',0)
                if age<0: continue
                p=ease(age/.18); scale=1+1.8*(1-p) if i==0 else 1+.13*(1-p)
                alpha=min(1,age/.09)*min(1,remaining/.10)
                im=base.resize((max(1,int(base.width*scale)),max(1,int(base.height*scale))),Image.Resampling.BICUBIC)
                blur=12*(1-p)
                if blur>.3: im=im.filter(ImageFilter.GaussianBlur(blur))
                im.putalpha(im.getchannel('A').point(lambda v:int(v*alpha)))
                x=int(490-im.width/2+(0 if i==0 else 150*(1-p)))
                y=int(l.get('y',960)-im.height/2)
                frame.alpha_composite(im,(x,y))
        proc.stdin.write(np.asarray(frame.convert('RGB')).tobytes())
    proc.stdin.close()
    if proc.wait(): raise RuntimeError('ffmpeg render failed')
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--spec',required=True);ap.add_argument('--out',required=True);ap.add_argument('--audio');args=ap.parse_args()
    render(json.loads(Path(args.spec).read_text()),args.out,args.audio)
