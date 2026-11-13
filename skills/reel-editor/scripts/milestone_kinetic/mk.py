# milestone_kinetic: follower-milestone reel from dashboard numbers: counters, orbiting reel thumbnails, city/country bars, real views graph, Hinglish Roman captions, egg-drop hook. Made with Claude, Nov 2026.
# Paths to inputs (videos, images, fonts, audio) are set near the top: edit them for a new reel.
import numpy as np, subprocess, re
from PIL import Image, ImageDraw, ImageFont
W,H=1080,1920
FD='/home/claude/ex/fnt/baloo-2-devanagari-700-normal.ttf'; FL='/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf'
cards=[(2.133,3.133,'w','Reel edit karwani hai?'),(3.133,4.067,'b','Jo viral ho.'),(4.067,4.833,'w','Professional.'),(4.833,5.533,'b','AI se fast.'),(5.533,6.69,'w','DM karo.')]
def card(bg,txt):
    im=Image.new('RGB',(W,H),(255,255,255) if bg=='w' else (0,0,0)); d=ImageDraw.Draw(im)
    col=(0,0,0) if bg=='w' else (255,255,255)
    size=96
    runs=[(m.group(0),re.match(r'[ऀ-ॿ]',m.group(0)) is not None) for m in re.finditer(r'[ऀ-ॿ।]+|[^ऀ-ॿ।]+',txt)]
    def fnt(dev,s): return ImageFont.truetype(FD if dev else FL,int(s if dev else s*0.8))
    while True:
        w=sum(fnt(dv,size).getlength(r) for r,dv in runs)
        if w<=W*0.86: break
        size-=4
    x=(W-w)/2; y=H/2+size*0.35
    for r,dv in runs:
        f=fnt(dv,size); d.text((x,y),r,font=f,fill=col,anchor='ls'); x+=f.getlength(r)
    return im
for i,(a,b,bg,tx) in enumerate(cards): card(bg,tx).save(f'c{i}.png')
