import sys, subprocess, numpy as np, inspect
import os, travel_titles as make
FPS, DUR, REV = 30, 4.0, 2.2
OUT = make.OUT
for k in (sys.argv[1:] or list(make.ALL)):
    fn = make.ALL[k]; takes_ph = 'ph' in inspect.signature(fn).parameters
    p = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', '1080x1920', '-r', str(FPS), '-i', '-',
                          '-c:v', 'libx264', '-crf', '19', '-preset', 'medium', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', OUT + k + '.mp4'], stdin=subprocess.PIPE)
    for n in range(int(FPS * DUR)):
        t = n / FPS; pr = min(1.0, t / REV)
        im = fn(pr, t * 3.0) if takes_ph else fn(pr)
        p.stdin.write(np.asarray(im).tobytes())
    p.stdin.close(); p.wait(); print('clip', k, flush=True)
