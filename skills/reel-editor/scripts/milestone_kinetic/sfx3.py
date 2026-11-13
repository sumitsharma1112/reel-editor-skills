# milestone_kinetic: follower-milestone reel from dashboard numbers: counters, orbiting reel thumbnails, city/country bars, real views graph, Hinglish Roman captions, egg-drop hook. Made with Claude, Nov 2026.
# Paths to inputs (videos, images, fonts, audio) are set near the top: edit them for a new reel.
import os, sys
import sys; sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import numpy as np, wave, random
src=open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'sfx_base.py')).read().split('BND=')[0]
src=src.replace("T=55.5","T=49.52").replace("/home/claude/ex/vo.wav","/home/claude/m50/vo.wav")
exec(src)
for t in [9.08,13.51,31.79,34.65,45.27,5.5]: add(t,thud(),0.35)
for t in [16.94,17.83,18.53,20.10,22.63,22.88,23.55,24.44,25.0,20.3,37.1,45.4,30.6,26.3]: add(t,pop(),0.18)
for t0,t1 in [(1.34,2.24),(4.4,5.5)]:
    t=t0
    while t<t1: add(t,tick(),0.18); t+=0.06
for tc in [9.69,16.94,22.63,26.01,30.43,36.27,40.41]: add(tc-0.25,whoosh(0.5),0.06)
x=np.arange(N)/SR; pad=np.zeros(N,np.float32)
chords=[(220,261.6,329.6),(174.6,220,261.6),(261.6,329.6,392),(196,246.9,293.7)]
for i,t0 in enumerate(np.arange(0,T,3.5)):
    ch=chords[i%4]; s=int(t0*SR); e=min(N,int((t0+4.2)*SR)); n=e-s; xx=np.arange(n)/SR
    en=np.minimum(1,xx/1.2)*np.minimum(1,(4.2-xx)/1.5)
    for f in ch: pad[s:e]+=np.sin(2*np.pi*f*xx)*en*0.33
for b in np.arange(0.0,T-0.5,60/100):
    n=int(SR*0.12); xx=np.arange(n)/SR; add(b,np.sin(2*np.pi*(55+40*np.exp(-xx*30))*xx)*np.exp(-xx*18)*0.5,0.35)
pad*=np.minimum(1,x/1.5)*np.minimum(1,(T-x)/1.2)
final=(vo[:N] if len(vo)>=N else np.pad(vo,(0,N-len(vo))))+mix*0.3+pad*0.05
final=np.tanh(final*1.05); final=final/np.abs(final).max()*0.92
st=np.stack([final,final],1)
w=wave.open('/home/claude/m50/audio.wav','wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((st*32767).astype(np.int16).tobytes()); w.close(); print('ok')
