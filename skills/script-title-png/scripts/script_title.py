import math, numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
W,H=1080,1920
import os; K=os.path.join(os.path.dirname(__file__),'..','fonts','KaushanScript-Regular.ttf')
def layer(text,size,fill,rot,cx,cy,track=0):
    f=ImageFont.truetype(K,size); bb=f.getbbox(text); w,h=bb[2]-bb[0]+80,bb[3]-bb[1]+80
    t=Image.new('L',(w,h),0); ImageDraw.Draw(t).text((40-bb[0],40-bb[1]),text,font=f,fill=255)
    out=Image.new('RGBA',(w,h),(0,0,0,0))
    # soft shadow
    sh=t.filter(ImageFilter.GaussianBlur(10)); out.paste((20,10,15,170),(6,10),sh)
    # outline
    ol=t.filter(ImageFilter.MaxFilter(7)); out.paste((40,22,28,255),(0,0),ol)
    out.paste(fill+(255,),(0,0),t)
    out=out.rotate(rot,resample=Image.BICUBIC,expand=True)
    return out,(int(cx-out.width/2),int(cy-out.height/2))
def rays(d,cx,cy,r0,r1,angles,col):
    for a in angles:
        x0,y0=cx+r0*math.cos(math.radians(a)),cy+r0*math.sin(math.radians(a))
        x1,y1=cx+r1*math.cos(math.radians(a)),cy+r1*math.sin(math.radians(a))
        d.line([(x0+3,y0+4),(x1+3,y1+4)],fill=(30,15,20,150),width=6)
        d.line([(x0,y0),(x1,y1)],fill=col,width=6)
img=Image.new('RGBA',(W,H),(0,0,0,0))
a,p=layer('Amrita Pritam',150,(248,232,205),6,W/2,330); img.alpha_composite(a,p)
b,q=layer('Biography · Part 1',78,(244,166,185),6,W/2,470); img.alpha_composite(b,q)
d=ImageDraw.Draw(img)
rays(d,195,250,40,85,[200,225,250],(248,232,205,255))
rays(d,900,215,40,85,[290,315,340],(248,232,205,255))
img.save('Amrita_Pritam_Part1_Title.png')
# previews
bg=Image.open('/home/claude/ein/imgs/img13.png').convert('RGBA').resize((W,H))
pv=bg.copy(); pv.alpha_composite(img)
dk=Image.new('RGBA',(W,H),(60,60,60,255)); dk.alpha_composite(img)
S=Image.new('RGB',(1080,960)); S.paste(pv.convert('RGB').resize((540,960)),(0,0)); S.paste(dk.convert('RGB').resize((540,960)),(540,0)); S.save('title_preview.jpg')
