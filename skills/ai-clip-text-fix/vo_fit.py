import numpy as np, soundfile as sf, json
x,sr=sf.read('vo.wav'); x=x if x.ndim==1 else x.mean(1)
segs=[(0.13,2.59),(3.15,3.85),(4.71,6.12),(6.55,7.82),(8.12,8.98),(9.64,10.77),(11.43,11.82),(12.04,12.86),(13.21,16.10),(16.73,17.62),(18.01,19.01),(19.36,19.94),(20.22,20.67),(20.97,21.97),(22.50,24.48),(24.67,25.47),(25.85,27.02),(27.36,27.84),(28.20,28.84),(29.08,29.68),(29.96,30.57),(31.10,32.96),(33.34,34.59),(35.23,36.58),(36.85,37.49),(38.02,38.80),(39.08,39.61),(39.89,40.44),(40.90,43.40)]
lines=[[0,1],[2,3,4],[5,6,7],[8,9,10],[11,12,13],[14,15,16],[17,18,19,20,21],[22,23],[24,25,26,27,28]]
PAD=0.06; CAP=0.38
def chunk(i):
    a,b=segs[i]; return x[int((a-PAD)*sr):int((b+PAD)*sr)]
# scenes: list of (line ids, lead, tail, min_dur, gap_between_lines)
scenes=[('hook',[0],0.05,0.25,0),('family',[1,2],0.2,0.35,0),('building',[3],0.2,0.3,0),('pack',[4],0.15,0.3,0),
        ('counter',[5],0.15,0.3,0),('globe',[6],0.15,0.3,0),('receive',[7],0.25,0.6,4.2),('cta',[8],0.15,1.4,0)]
buf=np.zeros(int(70*sr)); T=0.0; info=[]
for name,lids,lead,tail,mind in scenes:
    s0=T; t=T+lead; anchors=[]
    for li,l in enumerate(lids):
        if li>0: t+=0.45
        for k,i in enumerate(lines[l]):
            if k>0:
                g=segs[i][0]-segs[lines[l][k-1]][1]; t+=min(g,CAP)
            c=chunk(i); anchors.append(round(t-s0,3))
            pos=int((t-PAD)*sr)
            if pos<0: c=c[-pos:]; pos=0
            buf[pos:pos+len(c)]+=c
            t+=segs[i][1]-segs[i][0]
    dur=max(t+tail-s0,mind); T=s0+dur
    info.append({'name':name,'start':round(s0,3),'dur':round(dur,3),'anchors':anchors})
total=T; out=buf[:int(total*sr)]
sf.write('vo_fit.wav',out,sr)
json.dump(info,open('timing.json','w'),indent=1)
for d in info: print(d)
print('total',round(total,2))
