# kinetic_explainer: faceless AI explainer in the 'red 3D kinetic words' style (cartoon presenter, phone screen-recording, pixel glitch, light streak, halftone transitions, soft SFX). Made with Claude, Nov 2026.
# Paths to inputs (videos, images, fonts, audio) are set near the top: edit them for a new reel.
import os, sys
import sys; sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import numpy as np, wave, random
import sc2
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'sfx_base.py')).read().split('BND=')[0])  # reuse generators + vo load + mix
def glitchnoise(dur=0.18):
    n=int(SR*dur); x=np.arange(n)/SR
    sq=np.sign(np.sin(2*np.pi*rng.uniform(300,900)*x))*0.3
    return (rng.standard_normal(n)*0.4+sq)*(np.sin(np.pi*x/dur)**2)*((np.arange(n)//400)%2)
def blip():
    n=int(SR*0.12); x=np.arange(n)/SR; f=1600-900*x/0.12
    return np.sin(2*np.pi*np.cumsum(f)/SR)*np.exp(-x*25)*0.4
sw=whoosh(0.35)
for (k,tx,t0,t1,cx,cy,size,rot,mode) in sc2.I:
    if k=='big':
        if mode=='slam': add(t0,thud(),0.9)
        else: add(t0-0.08,sw,0.12); add(t0,blip(),0.2)
    elif k=='small': add(t0,tick(),0.35)
    else: add(t0,pop(),0.45)
for tc,typ in sc2.TR:
    add(tc-0.3,whoosh(0.6),0.12)
for i in range(5): add(11.9+i*0.62,ding(),0.45)
for t in [7.0,10.5,16.8,36.7,38.75,45.0,45.4,45.8,46.2,49.0,51.6,9.3]: add(t,pop(),0.5)

k=key(); t=27.3
while t<32.7: add(t,k,random.uniform(0.5,1.0)); t+=random.uniform(0.07,0.17)
add(29.2,buzz(0.8),0.6); add(52.4,tick(),1.0)
x=np.arange(N)/SR; pad=np.zeros(N,np.float32)
chords=[(220,261.6,329.6),(174.6,220,261.6),(261.6,329.6,392),(196,246.9,293.7)]
for i,t0 in enumerate(np.arange(0,T,3.5)):
    ch=chords[i%4]; s=int(t0*SR); e=min(N,int((t0+4.2)*SR)); n=e-s; xx=np.arange(n)/SR
    en=np.minimum(1,xx/1.2)*np.minimum(1,(4.2-xx)/1.5)
    for f in ch: pad[s:e]+=np.sin(2*np.pi*f*xx)*en*0.33
# soft beat
for b in np.arange(0.0,T-0.5,60/100):
    n=int(SR*0.12); xx=np.arange(n)/SR; add(b,np.sin(2*np.pi*(55+40*np.exp(-xx*30))*xx)*np.exp(-xx*18)*0.5,0.5)
pad*=np.minimum(1,x/1.5)*np.minimum(1,(T-x)/1.2)
final=(vo[:N] if len(vo)>=N else np.pad(vo,(0,N-len(vo))))+mix*0.30+pad*0.05
final=np.tanh(final*1.05); final=final/np.abs(final).max()*0.92
st=np.stack([final,final],1)
w=wave.open('/home/claude/ex/v2/audio2.wav','wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((st*32767).astype(np.int16).tobytes()); w.close()
print('audio ok')
