import numpy as np, wave, random
SR=44100; T=55.5; N=int(SR*T)
rng=np.random.default_rng(7); random.seed(7)
def load(p):
    w=wave.open(p); a=np.frombuffer(w.readframes(w.getnframes()),np.int16).astype(np.float32)/32768
    if w.getnchannels()==2: a=a.reshape(-1,2).mean(1)
    return a
vo=load('/home/claude/ex/vo.wav'); vo=vo/np.abs(vo).max()*0.8
mix=np.zeros(N,np.float32)
def add(t,s,g=1.0):
    i=int(t*SR); 
    if i<0: s=s[-i:]; i=0
    e=min(N,i+len(s))
    if e>i: mix[i:e]+=s[:e-i]*g
def env(n,a=0.005,d=None):
    x=np.arange(n)/SR; d=d or n/SR
    return np.minimum(1,x/a)*np.exp(-x/(d/4))
def whoosh(dur=0.45):
    n=int(SR*dur); x=rng.standard_normal(n).astype(np.float32)
    # sweeping lowpass via cumulative smoothing
    out=np.zeros(n,np.float32); y=0
    for i in range(n):
        a=0.02+0.5*np.sin(np.pi*i/n)**2
        y+=a*(x[i]-y); out[i]=y
    return out*np.sin(np.pi*np.arange(n)/n)**1.5*2.2
def pop():
    n=int(SR*0.18); x=np.arange(n)/SR; f=520+900*np.exp(-x*30)
    return np.sin(2*np.pi*np.cumsum(f)/SR)*np.exp(-x*22)*0.8
def ding():
    n=int(SR*0.5); x=np.arange(n)/SR
    return (np.sin(2*np.pi*1318*x)+0.5*np.sin(2*np.pi*1975*x))*np.exp(-x*9)*0.45
def thud():
    n=int(SR*0.5); x=np.arange(n)/SR
    return (np.sin(2*np.pi*(70+90*np.exp(-x*25))*x)*np.exp(-x*9)+rng.standard_normal(n)*np.exp(-x*60)*0.5)*1.1
def tick():
    n=int(SR*0.09); x=np.arange(n)/SR
    return (np.sin(2*np.pi*1900*x)*np.exp(-x*70)+np.sin(2*np.pi*2850*x)*np.exp(-x*90)*0.5)*0.55
def key():
    n=int(SR*0.04); x=np.arange(n)/SR
    return rng.standard_normal(n).astype(np.float32)*np.exp(-x*140)*0.35
def clock():
    n=int(SR*0.05); x=np.arange(n)/SR
    return np.sin(2*np.pi*1100*x)*np.exp(-x*100)*0.35
def buzz(dur):
    n=int(SR*dur); x=np.arange(n)/SR
    bursts=(np.sin(2*np.pi*38*x)>0.2)
    return rng.standard_normal(n).astype(np.float32)*bursts*0.25*np.minimum(1,x*20)*np.minimum(1,(dur-x)*20)
BND=[5.4,11.4,16.0,22.0,36.6,38.7,42.5,47.4,51.3]
wsh=whoosh()
for b in BND: add(b-0.28,wsh,0.55)
for t in [3.0,42.7,47.5,22.0]: add(t-0.05,whoosh(0.5),0.5)
pops=[2.4,4.6,5.9,9.0,9.1,10.4,10.6,13.4,18.5,20.7,37.2,38.9,39.95,42.8,43.0,43.4,43.8,44.5,47.6,48.3,48.9,51.5,52.5,36.9,17.4,44.6,37.0,11.6]
p=pop()
for t in pops: add(t,p,0.55)
d=ding()
for i in range(5): add(11.7+0.7*i,d,0.5)
th=thud()
for t in [4.1,16.9,41.2]: add(t,th,0.9)
tk=tick()
for t in [24.3,26.9,28.4,31.0,34.0,35.6,44.9,45.6,46.3,52.4]: add(t,tk,0.9)
k=key(); t=27.3
while t<32.7:
    add(t,k,random.uniform(0.5,1.0)); t+=random.uniform(0.07,0.17)
c=clock()
for i in range(5): add(0.3+i,c,0.8)
for i in range(5): add(53.9+i*0.3,c,0.8)
add(29.2,buzz(0.9),0.7)
# pad
x=np.arange(N)/SR; pad=np.zeros(N,np.float32)
chords=[(220,261.6,329.6),(174.6,220,261.6),(261.6,329.6,392),(196,246.9,293.7)]
for i,t0 in enumerate(np.arange(0,T,3.5)):
    ch=chords[i%4]; s=int(t0*SR); e=min(N,int((t0+4.2)*SR)); n=e-s; xx=np.arange(n)/SR
    env_=np.minimum(1,xx/1.2)*np.minimum(1,(4.2-xx)/1.5)
    for f in ch: pad[s:e]+=np.sin(2*np.pi*f*xx)*env_*0.33
pad*=np.minimum(1,x/1.5)*np.minimum(1,(T-x)/1.2)
final=vo[:N] if len(vo)>=N else np.pad(vo,(0,N-len(vo)))
final=final+mix*0.34+pad*0.055
final=np.tanh(final*1.05)
final=final/np.abs(final).max()*0.92
st=np.stack([final,final],1)
w=wave.open('/home/claude/ex/build/audio_mix.wav','wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
w.writeframes((st*32767).astype(np.int16).tobytes()); w.close(); print('audio ok',len(final)/SR)
