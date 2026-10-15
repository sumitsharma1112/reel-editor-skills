#!/usr/bin/env python3
"""Create timestamped reference contact sheets without modifying source media.
Requires ffmpeg/ffprobe and Pillow. Broad pass first, then --start/--end --step .1.
Outputs are inspection aids, not verified audio alignments or automatic cut detection.
"""
import argparse, io, json, math, subprocess
from pathlib import Path
from PIL import Image, ImageDraw

def run(args):
    return subprocess.check_output(args)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('video',type=Path);p.add_argument('--out',type=Path,required=True)
    p.add_argument('--start',type=float,default=0);p.add_argument('--end',type=float)
    p.add_argument('--step',type=float);p.add_argument('--samples',type=int,default=16)
    a=p.parse_args()
    d=json.loads(run(['ffprobe','-v','error','-show_format','-show_streams','-of','json',str(a.video)]))
    v=next(s for s in d['streams'] if s['codec_type']=='video')
    duration=float(d['format']['duration']);end=min(a.end if a.end is not None else duration,duration)
    if not (0<=a.start<end) or a.samples<1 or (a.step is not None and a.step<=0):
        p.error('Require 0 <= start < end, samples >= 1, step > 0')
    step=a.step if a.step is not None else (end-a.start)/a.samples
    count=math.ceil((end-a.start)/step)
    if count>600:p.error('Limit each inspection to 600 frames; split long intervals')
    a.out.mkdir(parents=True,exist_ok=True)
    times=[min(a.start+i*step,duration-.001) for i in range(count)]
    for page in range(math.ceil(count/16)):
        batch=times[page*16:(page+1)*16]
        sheet=Image.new('RGB',(1280,math.ceil(len(batch)/4)*400),'#e6e3df');draw=ImageDraw.Draw(sheet)
        for j,t in enumerate(batch):
            data=run(['ffmpeg','-v','error','-ss',str(t),'-i',str(a.video),'-frames:v','1','-vf','scale=310:365:force_original_aspect_ratio=decrease','-f','image2pipe','-vcodec','png','-'])
            im=Image.open(io.BytesIO(data)).convert('RGB');x=j%4*320;y=j//4*400
            sheet.paste(im,(x+(320-im.width)//2,y+30));draw.text((x+8,y+8),f'{t:.3f}s',fill='black')
        sheet.save(a.out/f'sheet_{page:03}.jpg',quality=92)
    metadata={'source_name':a.video.name,'duration':duration,'width':v['width'],'height':v['height'],'fps':v['r_frame_rate'],'sample_times':times,'note':'Visual samples only; inspect actual audio separately.'}
    (a.out/'inspection.json').write_text(json.dumps(metadata,indent=2))
    print(f'{count} samples in {math.ceil(count/16)} sheets: {a.out}')
if __name__=='__main__':main()
