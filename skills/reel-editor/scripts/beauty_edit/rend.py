# beauty_edit: beat-synced glam edit of a talking/posing clip: optical-flow slow motion, speed ramps, whip/zoom/spin/glitch/blur transitions, flashes, pink grade + bloom + bokeh, sharpening, script titles, before/after wipe, triptych, card, polaroids, voice-hook captions. Made with Claude, Nov 2026.
# Paths to inputs (videos, images, fonts, audio) are set near the top: edit them for a new reel.
import os, sys
import sys, subprocess, importlib
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from multiprocessing import Pool
mod=importlib.import_module(sys.argv[1]); out=sys.argv[2]; aud=sys.argv[3]
def job(i): return mod.frame(i/30.0).tobytes()
if __name__=='__main__':
    N=int(mod.T*30)
    enc=subprocess.Popen(['ffmpeg','-v','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s','1080x1920','-r','30','-i','-','-i',aud,'-map','0:v','-map','1:a','-c:v','libx264','-preset','medium','-crf','17','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-shortest',out],stdin=subprocess.PIPE)
    with Pool(2) as p:
        for b in p.imap(job,range(N),chunksize=6): enc.stdin.write(b)
    enc.stdin.close(); enc.wait(); print('done',N)
