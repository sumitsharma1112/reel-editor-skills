"""Render exact-timed still scenes with transparent caption overlays.

spec: [{"start":0,"end":3,"image":"bg.jpg","overlay":"caption.png"}, ...]
Use a shaped Gurmukhi-capable font for Punjabi overlays; Berkshire Swash has
Latin glyphs only. Cream #F2E6CE with a dark stroke reads well on gold artwork.
python timed_caption_stills.py --spec scenes.json --out reel.mp4
"""
import argparse,json,subprocess,tempfile
from pathlib import Path

def main():
    p=argparse.ArgumentParser();p.add_argument('--spec',required=True);p.add_argument('--out',required=True);a=p.parse_args()
    spec=Path(a.spec).resolve();rows=json.loads(spec.read_text());base=spec.parent
    with tempfile.TemporaryDirectory() as work:
        parts=[]
        for i,r in enumerate(rows):
            dur=r['end']-r['start'];n=round(dur*30);part=Path(work)/f'{i}.mp4';parts.append(part)
            vf=f"[0:v]scale=2160:3840,zoompan=z='1+0.045*on/{n}':x='iw/2-iw/zoom/2':y='ih/2-ih/zoom/2':d={n}:s=1080x1920:fps=30[b];[1:v]format=rgba,fade=t=in:d=0.18:alpha=1[c];[b][c]overlay=0:0:shortest=1,format=yuv420p[v]"
            subprocess.run(['ffmpeg','-v','error','-y','-i',str(base/r['image']),'-loop','1','-i',str(base/r['overlay']),'-filter_complex',vf,'-map','[v]','-t',str(dur),'-c:v','libx264','-preset','fast','-crf','21','-threads','4',str(part)],check=True)
        listing=Path(work)/'concat.txt';listing.write_text(''.join(f"file '{x}'\n" for x in parts))
        subprocess.run(['ffmpeg','-v','error','-y','-f','concat','-safe','0','-i',str(listing),'-c','copy','-movflags','+faststart',a.out],check=True)

if __name__=='__main__':main()
