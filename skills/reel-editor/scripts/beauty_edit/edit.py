# beauty_edit: beat-synced glam edit of a talking/posing clip: optical-flow slow motion, speed ramps, whip/zoom/spin/glitch/blur transitions, flashes, pink grade + bloom + bokeh, sharpening, script titles, before/after wipe, triptych, card, polaroids, voice-hook captions. Made with Claude, Nov 2026.
# Paths to inputs (videos, images, fonts, audio) are set near the top: edit them for a new reel.
import os, sys
import sys; sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from lib import *
GV='/home/claude/girl/greatvibes.ttf'; M6='/home/claude/girl/mont600.ttf'; M8='/home/claude/girl/mont800.ttf'; PF='/home/claude/girl/playfair700i.ttf'
def lin(u): return u
def ramp_fs(u): return 1-(1-u)**2.2   # fast then slow
def ramp_sf(u): return u**2.2
class Seg:
    def __init__(s,o0,o1,s0,s1,ease=lin,z0=1.0,z1=1.06,tr='flash',cy=0.45,rot0=0,rot1=0,dx0=0,dx1=0,bw=False,mb=False,fx=None):
        s.__dict__.update(locals()); del s.__dict__['s']
def seg_img(sg,t,beats):
    u=(t-sg.o0)/(sg.o1-sg.o0)
    if getattr(sg,'draw',None): return sg.draw(t,u)
    u=(t-sg.o0)/(sg.o1-sg.o0); uc=min(max(u,-0.3),1.3)
    st=sg.s0+(sg.s1-sg.s0)*sg.ease(min(max(uc,0),1)) + (sg.s1-sg.s0)/(sg.o1-sg.o0)*(min(uc,0)+max(uc-1,0))*0.0
    st=min(max(st,0),45.9)
    if sg.mb:
        spd=abs(sg.s1-sg.s0)/(sg.o1-sg.o0); img=src_blur(st,spd)
    else: img=src(st)
    z=sg.z0+(sg.z1-sg.z0)*ease_io(u)
    for b in beats:
        if 0<=t-b<0.4: z+=0.035*math.exp(-(t-b)*9)
    rot=sg.rot0+(sg.rot1-sg.rot0)*ease_io(u); dx=sg.dx0+(sg.dx1-sg.dx0)*ease_io(u)
    c=to_canvas(img,z,0.5,sg.cy,rot,dx)
    if sg.bw:
        g=c.mean(-1,keepdims=True); c=g*0.85+c*0.15
    if sg.fx: c=sg.fx(c,t,u)
    return c
def render_segments(segs,t,beats,D=0.17):
    # find current seg
    k=0
    for i,sg in enumerate(segs):
        if sg.o0<=t: k=i
    sg=segs[k]
    # transition into next?
    nxt=segs[k+1] if k+1<len(segs) else None
    if nxt and t>nxt.o0-D: A,B,b=sg,nxt,nxt.o0
    elif k>0 and t<sg.o0+D: A,B,b=segs[k-1],sg,sg.o0
    else: return seg_img(sg,t,beats)
    p=(t-(b-D))/(2*D); tr=B.tr
    if tr=='whip':
        e=ease_io(p); off=int(e*W)
        a=seg_img(A,t,beats); bb=seg_img(B,t,beats)
        out=np.empty_like(a)
        if off<W: out[:,:W-off]=a[:,off:]
        if off>0: out[:,W-off:]=bb[:,:off]
        return dirblur(out,90*math.sin(math.pi*p)+1)
    if tr=='zoom':
        if t<b:
            a=seg_img(A,t,beats); q=p*2; M=cv2.getRotationMatrix2D((W/2,H/2),0,1+0.5*q*q)
            return zoomblur(cv2.warpAffine(a,M,(W,H),borderMode=cv2.BORDER_REFLECT),0.25*q)
        bb=seg_img(B,t,beats); q=1-(p-0.5)*2; M=cv2.getRotationMatrix2D((W/2,H/2),0,1+0.35*q*q)
        return zoomblur(cv2.warpAffine(bb,M,(W,H),borderMode=cv2.BORDER_REFLECT),0.2*q)
    if tr=='glitch':
        img=seg_img(A,t,beats) if t<b else seg_img(B,t,beats)
        return glitch(img,t,math.sin(math.pi*p))
    if tr=='blur':
        a=seg_img(A,t,beats); bb=seg_img(B,t,beats); e=ease_io(p)
        return gblur(a*(1-e)+bb*e,40*math.sin(math.pi*p))
    if tr=='spin':
        a=seg_img(A,t,beats) if t<b else seg_img(B,t,beats)
        ang=(p-0.5)*2*25; s=1+0.25*math.sin(math.pi*p)
        M=cv2.getRotationMatrix2D((W/2,H/2),ang,s)
        return zoomblur(cv2.warpAffine(a,M,(W,H),borderMode=cv2.BORDER_REFLECT),0.15*math.sin(math.pi*p))
    # flash (default)
    img=seg_img(A,t,beats) if t<b else seg_img(B,t,beats)
    return img
def flashes(img,t,pts,w=0.09,amt=0.85):
    f=0
    for b in pts:
        d=t-b
        if -0.04<d<0.35: f=max(f,amt*math.exp(-max(d,0)/w)*(1 if d>=0 else (1+d/0.04)))
    return flash(img,min(f,1)) if f>0.01 else img
def finish(img,t,leakk=0.3,bok=1.0,spk=1.0):
    img=grade(img); img=bloom(img)
    img=img+leak(t,(255,80,150),leakk,0.35)+leak(t,(255,170,120),leakk*0.6,0.5,2.0)
    img=sharpen(img)
    img=img+bokeh(t,bok*0.45)
    img=img*VIG
    img=grain(img,t,2)
    return img
