import numpy as np, wave
exec(open('sfx.py').read().split("add(whoosh(0.55)")[0].replace('DUR=12.0','DUR=14.0'))
HOOK=1.8; BEAT=1.6; FIN0=9.8
# hook (same as before, first 1.8 s)
add(whoosh(0.55),0.35,0.10)
for tt in (0.9,1.25): add(thud(80,0.3),tt,0.28)
add(thud(60,0.4),1.6,0.32); add(blip(),1.62,0.05)
# whoosh on every scene change (soft)
for i in range(6): add(whoosh(0.28),HOOK+i*BEAT-0.14,0.07)
b=[HOOK+i*BEAT for i in range(5)]
# 1 stories: page flutter + sparkle
fl=lp(rng.normal(0,1,int(SR*0.35)),25)*np.sin(np.linspace(0,np.pi,int(SR*0.35)))*(0.6+0.4*np.sign(np.sin(np.linspace(0,60,int(SR*0.35)))))
add(fl/np.abs(fl).max(),b[0]+0.15,0.06); add(shimmer(),b[0]+0.45,0.035)
# 2 books: three soft thuds
for k in range(3): add(thud(95,0.22),b[1]+0.22+k*0.16,0.22)
# 3 youtube: click
add(pop(1400,1000,0.04),b[2]+0.3,0.08)
# 4 journey: tiny counter ticks then pop
for k in range(10): add(tick(),b[3]+0.4+k*0.08,0.05)
add(pop(700,1100,0.1),b[3]+1.25,0.10)
# 5 voice: soft swell
n=int(SR*0.9); t=np.arange(n)/SR; sw=np.sin(2*np.pi*110*t)*np.sin(np.pi*t/0.9)**2
add(sw,b[4]+0.15,0.10)
for i in range(16): add(tick(),b[4]+0.05+i*0.044,0.04)
# final AMA (ama3 sped 1.6x from t'=2.0)
f=lambda tp: FIN0+(tp-2.0)/1.6
for i in range(15): add(tick(),f(2.0+i*0.06),0.05)
add(blip(),f(2.45),0.035); add(whoosh(0.35),f(2.55),0.06); add(shimmer(),f(3.0),0.04)
for k in range(5): add(pop(),f(3.6+k*0.32+0.05),0.10)
st=np.clip(np.stack([out,out],1),-1,1)
with wave.open('sfx4.wav','wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((st*32767).astype(np.int16).tobytes())
print('peak',np.abs(out).max())
