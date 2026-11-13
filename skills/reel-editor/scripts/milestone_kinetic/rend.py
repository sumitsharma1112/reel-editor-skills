# milestone_kinetic: follower-milestone reel from dashboard numbers: counters, orbiting reel thumbnails, city/country bars, real views graph, Hinglish Roman captions, egg-drop hook. Made with Claude, Nov 2026.
# Paths to inputs (videos, images, fonts, audio) are set near the top: edit them for a new reel.
import os, sys
import sys, subprocess
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from multiprocessing import Pool
import sc3
def job(i): return sc3.frame(i/30.0).tobytes()
if __name__=='__main__':
    N=int(sc3.T*30)
    enc=subprocess.Popen(['ffmpeg','-v','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s','1080x1920','-r','30','-i','-','-c:v','libx264','-preset','veryfast','-crf','17','-pix_fmt','yuv420p','reel_v.mp4'],stdin=subprocess.PIPE)
    with Pool(2) as p:
        for b in p.imap(job,range(N),chunksize=4): enc.stdin.write(b)
    enc.stdin.close(); enc.wait(); print('done',N)
