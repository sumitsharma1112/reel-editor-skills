# kinetic_explainer: faceless AI explainer in the 'red 3D kinetic words' style (cartoon presenter, phone screen-recording, pixel glitch, light streak, halftone transitions, soft SFX). Made with Claude, Nov 2026.
# Paths to inputs (videos, images, fonts, audio) are set near the top: edit them for a new reel.
import os, sys
import sys, subprocess
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from multiprocessing import Pool
import sc2
def job(i): return sc2.frame(i/30.0).tobytes()
if __name__=='__main__':
    a,b,out=int(sys.argv[1]),int(sys.argv[2]),sys.argv[3]
    enc=subprocess.Popen(['ffmpeg','-v','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s','1080x1920','-r','30','-i','-','-c:v','libx264','-preset','veryfast','-crf','17','-pix_fmt','yuv420p',out],stdin=subprocess.PIPE)
    with Pool(2) as p:
        for buf in p.imap(job,range(a,b),chunksize=4): enc.stdin.write(buf)
    enc.stdin.close(); enc.wait(); print('done',a,b)
