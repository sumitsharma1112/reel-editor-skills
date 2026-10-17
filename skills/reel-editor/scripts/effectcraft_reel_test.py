#!/usr/bin/env python3
"""Build a native EffectCraft portrait reel from prepared stills and frame cues.
Requires effectcraft-cli 0.10.0 and Pillow. Supply matching caption/audio timing; this script
neither detects musical beats nor transcribes lyrics. Assets must be 1080x1920.
Usage: effectcraft_reel_test.py --binary /path/effectcraft-cli --spec local.json --out-dir output [--render]
Spec: {frames:180, fps:30, assets:{eye:'eye.png'}, audio:'song.wav',
 scenes:[{asset:'eye',start:0,end:60}], captions:[{text:'Hello',start:0,end:60}],
 font:'Montserrat', style:'Medium', handle:'@handle'}.
Paths resolve relative to the spec. Keeps personal media out of this repository.
"""
import argparse,json,os,subprocess,wave
from PIL import Image
from pathlib import Path

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--binary',type=Path,required=True);p.add_argument('--spec',type=Path,required=True)
 p.add_argument('--out-dir',type=Path,required=True);p.add_argument('--render',action='store_true')
 a=p.parse_args();specpath=a.spec.resolve();s=json.loads(specpath.read_text());out=a.out_dir.resolve();out.mkdir(parents=True,exist_ok=True)
 binary=str(a.binary.resolve());fps=s.get('fps',30);frames=s['frames']
 if fps!=30 or not isinstance(frames,int) or frames<1:raise ValueError('Prototype supports positive frame count at 30 fps')
 assets={k:(specpath.parent/v).resolve() for k,v in s['assets'].items()};audio=(specpath.parent/s['audio']).resolve()
 if len({v.name for v in assets.values()}|{audio.name})!=len(assets)+1:raise ValueError('Imported asset basenames must be unique')
 for f in [*assets.values(),audio]:
  if not f.is_file():raise FileNotFoundError(f)
 for f in assets.values():
  with Image.open(f) as im:
   im.load()
   if im.size!=(1080,1920):raise ValueError(f'{f}: prepare 1080x1920 assets before import')
 with wave.open(str(audio)) as wav:
  if wav.getnframes()/wav.getframerate()+1/fps<frames/fps:raise ValueError('Audio is shorter than the composition')
 for event in s['scenes']+s['captions']:
  if not all(isinstance(event[k],int) for k in ['start','end']) or not 0<=event['start']<event['end']<=frames:raise ValueError(f'Invalid frame interval: {event}')
 cmds=[]
 def add(id,**params):cmds.append((id,params))
 def prop(name,path,value):add('prop.set',layer=name,path=path,value=value)
 def key(name,path,t,value):add('prop.addKey',layer=name,path=path,time=t,timeBase='comp',value=value)
 add('comp.new',name='ReelTest',width=1080,height=1920,frameRate=fps,duration=frames/fps)
 add('file.import',paths=[str(x) for x in [*assets.values(),audio]],sequence=False)
 add('layer.newSolid',name='Backdrop',color='#060D18')
 for i,event in enumerate(s['scenes']):
  name=f'Shot{i}';t0=event['start']/fps;t1=event['end']/fps;settle=min(t1-1/fps,t0+5/fps)
  add('layer.addItem',item=assets[event['asset']].name,time=0,duration=frames/fps);add('layer.rename',name=name)
  add('layer.timing',layers=[name],start=0,**{'in':t0,'out':t1})
  add('effect.apply',effect='ec.stylize.glow',layers=[name])
  for k,v in [('threshold',72),('radius',22),('intensity',.26)]:prop(name,'effects/#1/'+k,v)
  add('effect.apply',effect='ec.blur.radial',layers=[name]);prop(name,'effects/#2/type',1)
  key(name,'transform/scale',t0,[112 if i else 100]*2+[100]);key(name,'transform/scale',settle,[102,102,100]);key(name,'transform/scale',t1-1/fps,[104,104,100])
  key(name,'effects/#2/amount',t0,14 if i else 0);key(name,'effects/#2/amount',settle,0)
 add('layer.addItem',item=audio.name,time=0)
 for i,event in enumerate(s['captions']):
  name=f'Caption{i}';t0=event['start']/fps;t1=event['end']/fps
  if event['end']-event['start']<12:raise ValueError('Caption groups must last at least 12 frames')
  add('layer.newText',name=name,text=event['text'],size=60,fill='#F7EBD8')
  add('layer.setText',layer=name,font=s.get('font','Montserrat'),style=s.get('style','Medium'),justify='center',applyStroke=False)
  add('layer.timing',layers=[name],start=0,**{'in':t0,'out':t1})
  for t,v in [(t0,[540,1325,0]),(t0+.2,[540,1280,0])]:key(name,'transform/position',t,v)
  for t,v in [(t0,0),(t0+.14,100),(t1-.1,100),(t1-1/fps,0)]:key(name,'transform/opacity',t,v)
  for t,v in [(t0,[92,92,100]),(t0+.17,[103,103,100]),(t0+.3,[100,100,100])]:key(name,'transform/scale',t,v)
 if s.get('handle'):
  add('layer.newText',name='Brand',text=s['handle'],size=28,fill='#E5DFD2');add('layer.setText',layer='Brand',font='Montserrat',style='Medium',justify='center')
  prop('Brand','transform/position',[540,1440,0]);prop('Brand','transform/opacity',75)
 (out/'commands.json').write_text(json.dumps([{'id':id,'params':v} for id,v in cmds],indent=2))
 project=out/'ReelTest.ecproj';args=[binary,'--empty','run']
 for id,v in cmds:args.extend([id,json.dumps(v)])
 args+=['--save-as',str(project),'--json'];env={**os.environ,'RAYON_NUM_THREADS':'2'}
 result=subprocess.run(args,capture_output=True,text=True,env=env);(out/'build.log').write_text(result.stdout+result.stderr)
 if result.returncode:raise RuntimeError(result.stdout+result.stderr)
 if a.render:
  with (out/'render.log').open('w') as log:subprocess.run([binary,'--project',str(project),'render','--out',str(out/'EffectCraft_Test.mp4'),'--format','h264','--fps','30','--resolution','full','--quality','best','--bitrate','10000','--audio','on','--json'],stdout=log,stderr=subprocess.STDOUT,env=env,check=True)
 print(project)
if __name__=='__main__':main()
