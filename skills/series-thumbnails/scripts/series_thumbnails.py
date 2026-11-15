import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
W,H=1080,1920; FD='/home/claude/effects/fonts/'
F=lambda n,s: ImageFont.truetype(FD+n,s)
PAL={int(l.split(':')[0]):l.strip().split(':')[1] for l in open('pal.txt')}
CAT={'bio':('BIOGRAPHY',(255,205,60),(20,20,20)),'sant':('SANT KATHA',(255,140,60),(20,20,20)),'book':('BOOK SUMMARY',(90,220,150),(20,20,20))}
# idx, reel id, cat, title lines, pill subtitle, part
T=[(3,'DfvnUOGhDsp','bio',['ALBERT','EINSTEIN'],'jise naukri nahi mili','PART 1'),
(9,'Dfr2UxTB5U_','bio',['MAX','PLANCK'],'Nobel mila, beta nahi bacha','PART 1'),
(10,'Dfrksz1BJ-K','bio',['MAX','PLANCK'],'discovery ke peeche ka dard','PART 2'),
(20,'Dfeu7X2BfkD','bio',['OSHO'],'bailgaadi se Rolls-Royce tak','PART 1'),
(19,'DfhZpCkBzEP','bio',['OSHO'],'Rolls-Royce par hungama kyun?','PART 2'),
(38,'DfOrW8VhXwv','bio',['RAMANUJAN'],'exam me fail, Maths ka genius',None),
(46,'DfJMgsjx-lo','bio',['LEONARDO','DA VINCI'],'ek muskaan ka raaz',None),
(55,'DfDxI0_SF99','bio',['ISAAC','NEWTON'],'genius ka uljha bachpan',None),
(60,'De_63lihwEW','bio',['MARIE','CURIE'],'2 Nobel, phir bhi admission nahi',None),
(95,'DeuPVHLBnJ2','bio',['GALILEO'],'awaaz dab sakti hai, sach nahi','PART 1'),
(94,'DevfjWtR_Iu','bio',['GALILEO'],'Eppur si muove','PART 2'),
(27,'DfbHEC9hk3i','sant',['BULLEH','SHAH'],'ek maali bana murshid','PART 1'),
(26,'DfcWyKrBKq2','sant',['BULLEH','SHAH'],'murshid ko manane ka naach','PART 2'),
(15,'Dfj4il2hIUo','sant',['SANT','RAVIDAS'],'ek joota, ek tedha taanka','PART 1'),
(11,'DfliY7ch_Ko','sant',['SANT','RAVIDAS'],'aaj aapka din kaisa raha?','PART 2'),
(50,'DfHo9Goha7A','sant',['KABIR'],'insaan ko insaan se joda',None),
(82,'De1ghqwBk2P','book',['THE','ALCHEMIST'],'Paulo Coelho',None),
(84,'Dezlv-AOXph','book',['THE','METAMORPHOSIS'],'Franz Kafka',None),
(93,'DewTdskhVzA','book',['THE','FOUNTAINHEAD'],'Ayn Rand',None)]
def bg(i):
    h=PAL[i]; a=np.array([int(h[k:k+2],16) for k in range(0,len(h),2)],np.float32).reshape(7,4,3)
    b=cv2.resize(a,(W,H),interpolation=cv2.INTER_CUBIC); b=cv2.GaussianBlur(b,(0,0),60)
    b=np.clip((b-b.mean())*1.25+b.mean(),0,255)*0.62
    yy,xx=np.mgrid[0:H,0:W]; v=1-0.55*np.clip(np.hypot((xx-W/2)/(W/2),(yy-H/2)/(H/2))-0.35,0,1)
    n=np.random.default_rng(i).normal(0,5,(H,W,1))
    return Image.fromarray(np.clip(b*v[...,None]+n,0,255).astype(np.uint8)).convert('RGBA')
def pill(d,t,cx,cy,f,bgc,fg,pad=(30,16),r=12,rot=0):
    b=d.textbbox((0,0),t,font=f); w,h=b[2]-b[0],b[3]-b[1]
    d.rounded_rectangle([cx-w/2-pad[0],cy-h/2-pad[1],cx+w/2+pad[0],cy+h/2+pad[1]],r,fill=bgc)
    d.text((cx-w/2-b[0],cy-h/2-b[1]),t,font=f,fill=fg)
def fit(d,t,maxw,size):
    while size>70:
        f=F('ArchivoBlack-Regular.ttf',size)
        if d.textlength(t,font=f)<=maxw: return f
        size-=6
    return f
for n,(i,rid,cat,lines,sub,part) in enumerate(T,1):
    im=bg(i); d=ImageDraw.Draw(im)
    if i==3:
        c=Image.open('/home/claude/ein/cz/c16_einstein_think.png').convert('RGBA'); c=c.crop(c.getbbox()); s=900/c.height; c=c.resize((int(c.width*s),900)); im.alpha_composite(c,((W-c.width)//2,1090)); d=ImageDraw.Draw(im)
    lab,bc,fc=CAT[cat]; pill(d,lab,W/2,560,F('SpaceMono-Bold.ttf',40),bc,fc,(26,14),8)
    y=650
    for l in lines:
        f=fit(d,l,880,190); b=d.textbbox((0,0),l,font=f); w=b[2]-b[0]
        d.text(((W-w)/2-b[0],y-b[1]),l,font=f,fill=(255,255,255),stroke_width=10,stroke_fill=(15,15,15)); y+=b[3]-b[1]+34
    fs=F('ArchivoBlack-Regular.ttf',50)
    while d.textlength(sub,font=fs)>820: fs=F('ArchivoBlack-Regular.ttf',fs.size-3)
    pill(d,sub,W/2,y+50,fs,(240,60,120) if cat!='book' else (70,110,240),(255,255,255),(28,16),10)
    if part: pill(d,part,W/2,y+170,F('SpaceMono-Bold.ttf',40),(250,248,240),(20,20,20),(22,12),6)
    name=f"out/{n:02d}_{'_'.join(lines).replace(' ','').replace('-','').title()}{'_'+part.replace(' ','') if part else ''}_{rid}.jpg"
    im.convert('RGB').save(name,quality=93)
import glob
fs=sorted(glob.glob('out/*.jpg')); S=Image.new('RGB',(7*216,3*384))
for k,f in enumerate(fs): S.paste(Image.open(f).resize((216,384)),((k%7)*216,(k//7)*384))
S.save('sheet.jpg',quality=85)
