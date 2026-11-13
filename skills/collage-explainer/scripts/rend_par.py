import sys, json, subprocess, numpy as np
import os; sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import collage_explainer as C
from multiprocessing import Pool
plan=json.load(open(sys.argv[1])); C.build_chunks(plan)
def job(i): return np.asarray(C.frame(plan,i/30)).tobytes()
if __name__=='__main__':
    out=sys.argv[2]; wav=out+'.mix.wav'; C.sfx_mix(plan,wav)
    enc=subprocess.Popen(['ffmpeg','-v','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s','1080x1920','-r','30','-i','-','-i',wav,'-map','0:v','-map','1:a','-c:v','libx264','-preset','veryfast','-crf','18','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-shortest',out],stdin=subprocess.PIPE)
    with Pool(2) as p:
        for b in p.imap(job,range(int(plan['duration']*30)),chunksize=8): enc.stdin.write(b)
    enc.stdin.close(); enc.wait(); print('done')
