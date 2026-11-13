# devotional_glow_story: narration part (word-by-word golden glow captions from Whisper timings, Ken Burns, particles, light leaks, tanpura drone + temple bells) then a shabad/aarti part with big Hinglish meaning text. Made with Claude, Nov 2026.
# Paths to inputs (videos, images, fonts, audio) are set near the top: edit them for a new reel.
import numpy as np, subprocess, wave
SR=44100
def load(p):
    r=subprocess.run(['ffmpeg','-v','error','-i',p,'-ac','1','-ar',str(SR),'-f','f32le','-'],capture_output=True).stdout
    return np.frombuffer(r,np.float32).copy()
vo=load('/home/claude/gn/vo.wav'); ref=load('/home/claude/gn/ref.mp4')
P1=37.45; N1=int(P1*SR); vo=vo[:N1]; vo=np.pad(vo,(0,N1-len(vo)))
vo=vo/np.abs(vo).max()*0.85
x=np.arange(N1)/SR
drone=np.zeros(N1,np.float32)
for f,a in [(146.83,0.5),(220.0,0.35),(293.66,0.3),(73.42,0.4)]:
    for h,ha in [(1,1),(2,0.4),(3,0.2),(4,0.1)]:
        drone+=a*ha*np.sin(2*np.pi*f*h*x+np.sin(2*np.pi*0.13*h*x)*0.6)
drone*=(0.75+0.25*np.sin(2*np.pi*0.25*x))*np.minimum(1,x/2.0)
drone=drone/np.abs(drone).max()*0.07
def bell(dur=3.0,f0=520):
    n=int(SR*dur); t=np.arange(n)/SR
    s=sum(a*np.sin(2*np.pi*f0*r*t)*np.exp(-t*d) for r,a,d in [(1,1,1.2),(2.0,0.5,1.8),(2.76,0.35,2.4),(5.4,0.2,4),(8.9,0.1,6)])
    return s/np.abs(s).max()
bed=drone.copy()
for t0,f0,g in [(0.2,410,0.10),(3.3,520,0.12),(3.95,600,0.09),(4.6,520,0.08),(33.4,410,0.10)]:
    b=bell(3.0,f0)*g; i=int(t0*SR); e=min(N1,i+len(b)); bed[i:e]+=b[:e-i]
# fade drone out at end
bed[-int(1.0*SR):]*=np.linspace(1,0.3,int(1.0*SR))
p1=vo+bed
ref=ref/np.abs(ref).max()*0.85
fi=int(0.6*SR); ref[:fi]*=np.linspace(0,1,fi)
fo=int(1.5*SR); ref[-fo:]*=np.linspace(1,0,fo)
out=np.concatenate([p1,ref])
out=np.tanh(out*1.05); out=out/np.abs(out).max()*0.93
st=(np.stack([out,out],1)*32767).astype(np.int16)
w=wave.open('/home/claude/gn/mix.wav','wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(st.tobytes()); w.close()
print(len(out)/SR)
