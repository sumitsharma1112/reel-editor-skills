# screen_record_privacy_blur: blur names, numbers, addresses and chat lists in a phone screen recording, per time-range rectangles plus a tracked keyboard edge; verify afterwards with tesseract OCR on sampled frames. Made with Claude, Nov 2026.
# Paths to inputs (videos, images, fonts, audio) are set near the top: edit them for a new reel.
import cv2, numpy as np, subprocess
V='/mnt/user-data/uploads/RecordIt-00083B56-D7B9-450E-9C3F-09609FCE854C.mp4'
S=0.6; W,H=int(886*S),int(1920*S)
R=[(8,10.8),(16,42),(62,73),(78,89),(90,100)]
sel='+'.join(f'between(t,{a},{b})' for a,b in R)
vf=f"fps=30,select='{sel}',scale={W}:{H}:flags=area"
rd=subprocess.Popen(['ffmpeg','-v','error','-i',V,'-vf',vf,'-vsync','0','-f','rawvideo','-pix_fmt','bgr24','-'],stdout=subprocess.PIPE)
times=[]
for a,b in R:
    k=int(round(a*30))
    while k/30.0<=b+1e-6: times.append(k); k+=1
def heavy(img):
    s=cv2.resize(img,(W//4,H//4),interpolation=cv2.INTER_AREA)
    s=cv2.GaussianBlur(s,(0,0),4)
    return cv2.resize(s,(W,H),interpolation=cv2.INTER_LINEAR)
def mosaic(img):
    s=cv2.resize(img,(W//16,H//16),interpolation=cv2.INTER_AREA)
    s=cv2.resize(s,(W,H),interpolation=cv2.INTER_NEAREST)
    return cv2.GaussianBlur(s,(0,0),3)
def rect(m,x0,y0,x1,y1,v=1.0):
    x0,y0,x1,y1=[int(round(c*S)) for c in (x0,y0,x1,y1)]
    m[max(y0,0):min(y1,H),max(x0,0):min(x1,W)]=v
n=0
while True:
    b=rd.stdout.read(W*H*3)
    if len(b)<W*H*3: break
    if n>=len(times): break
    idx=times[n]; t=idx/30.0; n+=1
    img=np.frombuffer(b,np.uint8).reshape(H,W,3)
    m=np.zeros((H,W),np.float32)
    if t<6:
        rect(m,0,125,620,235); rect(m,0,235,886,1750)
    elif t<9.3:
        rect(m,0,110,886,1860); rect(m,36,320,800,430,0); rect(m,36,1075,600,1840,0)
    elif t<44:
        rect(m,0,125,620,235); rect(m,0,235,886,1745); rect(m,0,1745,886,1850)
        rect(m,330,1755,560,1830,0); rect(m,30,1755,130,1830,0); rect(m,780,1755,860,1830,0)
        rect(m,0,1850,886,1920)
    elif t<55:
        rect(m,0,100,886,1920)
    elif t<73.5:
        if t<60:
            rect(m,0,0,886,1060)
        else:
            reg=img[int(600*S):int(1700*S),int(780*S):int(880*S)].astype(int)
            mk=(reg[:,:,2]>190)&(reg[:,:,1]<140)&(reg[:,:,0]<120)
            ys=np.where(mk.any(axis=1))[0]
            if mk.sum()>150*S*S: bot=int((600*S+np.median(ys))/S)-130
            else: bot=960
            rect(m,0,0,886,max(bot,110))
    elif t<89:
        rect(m,0,0,886,1290)
    else:
        rect(m,0,0,886,110); rect(m,0,250,886,1920)
        if t<90: rect(m,0,110,886,250)
    if m.max()>0:
        m=cv2.GaussianBlur(m,(0,0),3)[:,:,None]
        eff=mosaic(img) if t>=90 else heavy(img)
        out=(img*(1-m)+eff*m).astype(np.uint8)
    else: out=img
    cv2.imwrite(f'rec/{idx:05d}.jpg',out,[cv2.IMWRITE_JPEG_QUALITY,90])
print('done',n,len(times))
