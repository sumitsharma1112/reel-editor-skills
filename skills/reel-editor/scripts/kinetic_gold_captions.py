from pathlib import Path
from PIL import Image,ImageOps,ImageDraw,ImageFont,ImageFilter
import numpy as np, cv2,subprocess
import argparse,json,math
parser=argparse.ArgumentParser(description='White/gold kinetic lyric captions over full-frame photos.')
parser.add_argument('--spec',required=True,help='JSON: duration, scenes [{start,image}], captions [{start,end,before,accent,after}]')
parser.add_argument('--out',required=True)
parser.add_argument('--audio',help='Matching audio only; omit for a silent visual edit')
parser.add_argument('--preview',action='store_true')
a=parser.parse_args()
spec_path=Path(a.spec).resolve();spec=json.loads(spec_path.read_text());R=spec_path.parent
F=Path(__file__).resolve().parents[1]/'fonts';W,H=1080,1920
DUR=float(spec['duration'])
assert DUR>0
scenes=spec['scenes'];starts=[float(s['start']) for s in scenes]
assert starts[0]==0 and starts==sorted(set(starts))
bgs=[]
for scene in scenes:
 im=ImageOps.fit(Image.open(R/scene['image']).convert('RGB'),(W,H),centering=(.5,.42));bgs.append(np.array(im))
lines=[(float(c['start']),float(c['end']),c['before'],c['accent'],c['after']) for c in spec['captions']]
assert all(0<=s<e<=DUR for s,e,*_ in lines)
cache={}
def word(text,script=False):
 key=(text,script)
 if key in cache:return cache[key]
 size=145 if script else 100
 while True:
  f=ImageFont.truetype(str(F/('great-vibes-400.ttf' if script else 'montserrat-700.ttf')),size);bb=f.getbbox(text)
  if bb[2]-bb[0]<780:break
  size-=2
 im=Image.new('RGBA',(bb[2]-bb[0]+70,bb[3]-bb[1]+60));d=ImageDraw.Draw(im)
 d.text((35-bb[0],30-bb[1]),text,font=f,fill='#FFD64A' if script else '#FFFFFF')
 if script:im=Image.alpha_composite(im.filter(ImageFilter.GaussianBlur(9)),im)
 cache[key]=im
 return im
def layer(text,script,x,y,alpha=1,scale=1,angle=0,blur=0):
 w=word(text,script)
 if scale!=1:w=w.resize((max(1,round(w.width*scale)),max(1,round(w.height*scale))),Image.Resampling.BICUBIC)
 if angle:w=w.rotate(angle,Image.Resampling.BICUBIC,expand=True)
 if blur:w=w.filter(ImageFilter.GaussianBlur(blur))
 if alpha<1:w=w.copy();w.putalpha(w.getchannel('A').point(lambda v:round(v*max(0,alpha))))
 full=Image.new('RGBA',(W,H));full.alpha_composite(w,(round(x-w.width/2),round(y-w.height/2)))
 return full
def ease(u):return 1-(1-max(0,min(1,u)))**3
def text_scene(j,t):
 start,end,a,b,c=lines[j];dur=end-start;p=(t-start)/dur
 im=Image.new('RGBA',(W,H))
 # Opening build: words slide independently, then settle into a single line.
 first=a.split();stage_end=dur*.27
 widths=[word(w).width-50 for w in first];total=sum(widths)+24*(len(first)-1);left=480-total/2
 age=t-start
 for k,w in enumerate(first):
  u=(age-k*stage_end/max(1,len(first)))/.22;v=ease(u)
  if u<0:continue
  x=left+widths[k]/2+120*(1-v)
  im=Image.alpha_composite(im,layer(w,False,x,950,min(1,max(0,u)),1,0,8*(1-v)))
  left+=widths[k]+24
 # Gold script writes in above the white anchor.
 if p>.28:
  u=(p-.28)*dur/.25;v=ease(u)
  im=Image.alpha_composite(im,layer(b,True,480,840+50*(1-v),min(1,max(0,u)),.7+.3*v,-18*(1-v),3*(1-v)))
 # Reference camera flip: rotate the outgoing two-line stack through 180 degrees.
 if p>.57:
  u=(p-.57)*dur/.42;v=ease(u)
  crop=im.crop((40,650,920,1160));im=Image.new('RGBA',(W,H))
  if v<1:
   crop=crop.rotate(180*v,Image.Resampling.BICUBIC,expand=True)
   crop=crop.resize((round(crop.width*(1-.26*v)),round(crop.height*(1-.26*v))),Image.Resampling.BICUBIC)
   crop.putalpha(crop.getchannel('A').point(lambda value:round(value*(1-v))))
   im.alpha_composite(crop,(480-crop.width//2,round(980+85*v)-crop.height//2))
  im=Image.alpha_composite(im,layer(c,False,480,870-100*(1-v),v,.6+.4*v,0,5*(1-v)))
 return im
def frame(t):
 idx=max(i for i,s in enumerate(starts) if s<=t);age=t-starts[idx];end=starts[idx+1] if idx<len(starts)-1 else DUR
 z=1+.025*age/(end-starts[idx]);nw=round(W*z);nh=round(H*z)
 def move(bg):
  a=cv2.resize(bg,(nw,nh));return a[(nh-H)//2:(nh-H)//2+H,(nw-W)//2:(nw-W)//2+W]
 bg=move(bgs[idx]).copy()
 if idx and age<.4:bg=cv2.addWeighted(move(bgs[idx-1]),1-age/.4,bg,age/.4,0)
 # Keep the reference's luminous lettering readable against the real sky.
 bg=(bg.astype(np.float32)*.61).astype(np.uint8)
 im=Image.fromarray(bg).convert('RGBA')
 for j,e in enumerate(lines):
  if e[0]<=t<e[1]:
   ov=text_scene(j,t)
   dt=t-e[0]
   if j and dt<.2:
    # Incoming zoom-through with directional smear, like the reference's hard word cuts.
    v=ease(dt/.2);z=3.6-2.6*v
    ov=ov.crop((40,570,920,1350));ov=ov.resize((round(ov.width*z),round(ov.height*z)),Image.Resampling.BICUBIC)
    canvas=Image.new('RGBA',(W,H));canvas.alpha_composite(ov,(480-ov.width//2,960-ov.height//2));ov=canvas
    if v<.96:
     arr=np.array(ov);kernel=np.zeros((1,41),np.float32);kernel[0]=1/41;arr=cv2.filter2D(arr,-1,kernel);ov=Image.fromarray(arr)
   im=Image.alpha_composite(im,ov);break
 return im.convert('RGB')
if __name__=='__main__':
 out=Path(a.out).resolve();out.parent.mkdir(parents=True,exist_ok=True)
 if a.preview:
  sheet=Image.new('RGB',(1080,960))
  sample_start,sample_end,*_=lines[0]
  for i in range(8):
   t=sample_start+(sample_end-sample_start)*(i+.5)/8
   sheet.paste(frame(t).resize((270,480)),((i%4)*270,(i//4)*480))
  sheet.save(out);raise SystemExit()
 cmd=['ffmpeg','-v','warning','-y','-f','rawvideo','-pixel_format','rgb24','-video_size','1080x1920','-framerate','30','-i','pipe:0']
 if a.audio:cmd+=['-i',str(Path(a.audio).resolve()),'-map','0:v:0','-map','1:a:0','-c:a','aac','-b:a','192k']
 else:cmd+=['-an']
 cmd+=['-c:v','libx264','-threads','4','-preset','fast','-crf','21','-maxrate','3M','-bufsize','6M','-pix_fmt','yuv420p','-t',str(DUR),'-movflags','+faststart',str(out)]
 p=subprocess.Popen(cmd,stdin=subprocess.PIPE)
 try:
  for n in range(math.ceil(DUR*30)):p.stdin.write(frame(n/30).tobytes())
 finally:p.stdin.close()
 if p.wait():raise RuntimeError('ffmpeg render failed')
 print(out)
