# devotional_glow_story: narration part (word-by-word golden glow captions from Whisper timings, Ken Burns, particles, light leaks, tanpura drone + temple bells) then a shabad/aarti part with big Hinglish meaning text. Made with Claude, Nov 2026.
# Paths to inputs (videos, images, fonts, audio) are set near the top: edit them for a new reel.
import os, sys
import sys, subprocess
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from multiprocessing import Pool
import gn
def job(i): return gn.frame(i/30.0).tobytes()
if __name__=='__main__':
    N=int(gn.T*30)
    enc=subprocess.Popen(['ffmpeg','-v','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s','1080x1920','-r','30','-i','-','-i','/home/claude/gn/mix.wav','-map','0:v','-map','1:a','-c:v','libx264','-preset','veryfast','-crf','18','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-shortest','/home/claude/gn/gagan_mai_thaal_1080.mp4'],stdin=subprocess.PIPE)
    with Pool(2) as p:
        for b in p.imap(job,range(N),chunksize=4): enc.stdin.write(b)
    enc.stdin.close(); enc.wait(); print('done',N)
