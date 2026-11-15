import numpy as np, wave
SR=48000; DUR=12.0; out=np.zeros(int(SR*DUR))
rng=np.random.default_rng(7)
def add(sig,t,g):
    i=int(t*SR); n=min(len(sig),len(out)-i); out[i:i+n]+=sig[:n]*g
def env(n,a=0.005,r=0.2):
    t=np.arange(n)/SR; e=np.minimum(1,t/a)*np.exp(-t/r); return e
def lp(x,k): 
    y=np.convolve(x,np.ones(k)/k,'same'); return y
def whoosh(d=0.5,up=True):
    n=int(SR*d); x=rng.normal(0,1,n); t=np.arange(n)/n
    sh=np.sin(np.pi*t)**2; y=lp(x,int(40 if up else 60))*sh; return y/np.abs(y).max()
def thud(f=70,d=0.35):
    n=int(SR*d); t=np.arange(n)/SR; return np.sin(2*np.pi*f*t*(1-0.3*t/d))*env(n,0.003,0.09)
def pop(f0=900,f1=420,d=0.09):
    n=int(SR*d); t=np.arange(n)/SR; f=np.linspace(f0,f1,n); return np.sin(2*np.pi*np.cumsum(f)/SR)*env(n,0.002,0.03)
def tick():
    n=int(SR*0.02); x=rng.normal(0,1,n)*env(n,0.0005,0.004); return lp(x,3)
def blip():
    n=int(SR*0.12); t=np.arange(n)/SR; sq=np.sign(np.sin(2*np.pi*1200*t))*(np.sin(2*np.pi*30*t)>0); return lp(sq,8)*env(n,0.002,0.04)
def shimmer():
    n=int(SR*0.6); t=np.arange(n)/SR; y=sum(np.sin(2*np.pi*f*t) for f in (1320,1760,2640))*env(n,0.08,0.25); return y/3
add(whoosh(0.55),0.35,0.10)
for tt in (0.9,1.25): add(thud(80,0.3),tt,0.30)
add(thud(60,0.4),1.6,0.38); add(blip(),1.62,0.05)
for i in range(15): add(tick(),2.0+i*0.06,0.06)
add(blip(),2.45,0.04); add(whoosh(0.45),2.55,0.08)
add(shimmer(),3.0,0.05)
for k in range(5): add(pop(),3.6+k*0.32+0.05,0.12)
pk=np.abs(out).max(); print('peak',pk)
st=np.stack([out,out],1); st=np.clip(st,-1,1)
with wave.open('sfx.wav','wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((st*32767).astype(np.int16).tobytes())
