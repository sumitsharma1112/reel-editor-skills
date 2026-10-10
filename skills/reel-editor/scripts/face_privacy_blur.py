"""Blur ONE person's face in a finished reel (privacy), leave everyone else sharp.

Uses OpenCV YuNet (detect) + SFace (recognise). Models (download once from opencv_zoo via Git LFS):
  https://media.githubusercontent.com/media/opencv/opencv_zoo/main/models/face_detection_yunet/face_detection_yunet_2023mar.onnx
  https://media.githubusercontent.com/media/opencv/opencv_zoo/main/models/face_recognition_sface/face_recognition_sface_2021dec.onnx

  python face_privacy_blur.py --video in.mp4 --hide hide1.jpg,hide2.jpg --keep me1.jpg,me2.jpg --models models/ --out out.mp4

--hide / --keep: clear photos where the person is the ONLY (or largest) face. Detections are linked into tracks
and a whole track is blurred when it looks more like --hide than --keep (mean cosine >= 0.25), padded 4 frames
each side; blur = pixelate + gaussian inside a feathered ellipse. Mux the original audio back afterwards.
"""
import argparse, json, subprocess, numpy as np, cv2

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--video', required=True); ap.add_argument('--hide', required=True)
    ap.add_argument('--keep', default=''); ap.add_argument('--models', required=True); ap.add_argument('--out', required=True)
    a = ap.parse_args()
    det = cv2.FaceDetectorYN.create(a.models + '/face_detection_yunet_2023mar.onnx', '', (320, 320), 0.6, 0.3, 5000)
    rec = cv2.FaceRecognizerSF.create(a.models + '/face_recognition_sface_2021dec.onnx', '')
    def faces(img):
        det.setInputSize((img.shape[1], img.shape[0])); _, f = det.detect(img); return [] if f is None else list(f)
    def ref(paths):
        out = []
        for p in [p for p in paths.split(',') if p]:
            im = cv2.imread(p); fs = faces(im)
            if fs: f = max(fs, key=lambda f: f[2] * f[3]); out.append(rec.feature(rec.alignCrop(im, f)))
        return out
    D, S = ref(a.hide), ref(a.keep)
    sim = lambda e, R: max([rec.match(e, r, cv2.FaceRecognizerSF_FR_COSINE) for r in R] or [0])
    W, H = [int(v) for v in subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=width,height',
                                           '-of', 'csv=p=0', a.video], capture_output=True, text=True).stdout.strip().split(',')[:2]]
    rd = subprocess.Popen(['ffmpeg', '-v', 'error', '-i', a.video, '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-'], stdout=subprocess.PIPE)
    R = []
    while True:
        b = rd.stdout.read(W * H * 3)
        if len(b) < W * H * 3: break
        f = np.frombuffer(b, np.uint8).reshape(H, W, 3); out = []
        for d in faces(cv2.resize(f, (W // 2, H // 2))):
            d2 = d.copy(); d2[:14] *= 2; e = rec.feature(rec.alignCrop(f, d2))
            out.append([float(v) for v in d2[:4]] + [sim(e, D), sim(e, S)])
        R.append(out)
    tracks, active = [], []
    for i, dets in enumerate(R):
        for x, y, w, h, sd, ss in dets:
            cx, cy = x + w / 2, y + h / 2; best = None
            for t in active:
                lx, ly, lw = t['last']
                if i - t['end'] <= 6 and abs(cx - lx) < max(lw, w) * 0.8 and abs(cy - ly) < max(lw, w) * 0.8: best = t; break
            if best is None: best = {'dets': {}, 'sd': [], 'ss': []}; tracks.append(best)
            best['dets'][i] = (x, y, w, h); best['sd'].append(sd); best['ss'].append(ss); best['last'] = (cx, cy, w); best['end'] = i
        active = [t for t in tracks if i - t['end'] <= 6]
    blur = {}
    for t in tracks:
        sd, ss = np.array(t['sd']), np.array(t['ss'])
        if (sd.mean() >= 0.25 and sd.mean() > ss.mean()) or (np.max(sd - ss) >= 0.15 and sd.max() >= 0.35):
            fr = sorted(t['dets'])
            for k in range(fr[0] - 4, fr[-1] + 5): blur.setdefault(k, []).append(t['dets'][min(fr, key=lambda q: abs(q - k))])
    rd = subprocess.Popen(['ffmpeg', '-v', 'error', '-i', a.video, '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-'], stdout=subprocess.PIPE)
    fps = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=r_frame_rate', '-of', 'csv=p=0', a.video],
                         capture_output=True, text=True).stdout.strip()
    wr = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{W}x{H}', '-r', fps, '-i', '-',
                           '-i', a.video, '-map', '0:v', '-map', '1:a?', '-c:a', 'copy', '-c:v', 'libx264', '-crf', '18', '-pix_fmt', 'yuv420p', a.out],
                          stdin=subprocess.PIPE)
    i = 0
    while True:
        b = rd.stdout.read(W * H * 3)
        if len(b) < W * H * 3: break
        f = np.frombuffer(b, np.uint8).reshape(H, W, 3).copy()
        for x, y, w, h in blur.get(i, []):
            cx, cy = x + w / 2, y + h / 2; r = max(w, h) * 0.85
            x0, y0, x1, y1 = int(max(0, cx - r)), int(max(0, cy - r * 1.15)), int(min(W, cx + r)), int(min(H, cy + r * 1.15))
            roi = f[y0:y1, x0:x1]
            if roi.size == 0: continue
            sm = cv2.resize(roi, (max(1, (x1 - x0) // 14), max(1, (y1 - y0) // 14)))
            pix = cv2.GaussianBlur(cv2.resize(sm, (x1 - x0, y1 - y0)), (0, 0), 6)
            m = np.zeros((y1 - y0, x1 - x0), np.float32)
            cv2.ellipse(m, ((x1 - x0) // 2, (y1 - y0) // 2), ((x1 - x0) // 2, (y1 - y0) // 2), 0, 0, 360, 1, -1)
            m = cv2.GaussianBlur(m, (0, 0), 6)[..., None]; f[y0:y1, x0:x1] = (roi * (1 - m) + pix * m).astype(np.uint8)
        wr.stdin.write(f.tobytes()); i += 1
    wr.stdin.close(); wr.wait(); print('blurred tracks:', len(set(map(id, [t for t in tracks]))), 'frames with blur:', len(blur))

if __name__ == '__main__':
    main()
