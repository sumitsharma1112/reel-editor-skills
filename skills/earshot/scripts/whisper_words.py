#!/usr/bin/env python3
"""Word-level transcript with faster-whisper (Whisper small, int8).

Model: if Hugging Face is blocked, build it from npm:
  for i in 0 1 2 3; do npm pack @skillninja/shortmovie-telop-model-p$i; done
  # untar each, cat model.bin.part0..3 > model/model.bin, copy config/tokenizer/vocabulary/preprocessor json into model/
Usage: python3 -I whisper_words.py input.(wav|mp4) out.json [model_dir] [lang]
Audio is decoded with ffmpeg and passed as numpy (avoids PyAV version clashes).
"""
import json, subprocess, sys
import numpy as np
from faster_whisper import WhisperModel
src, out = sys.argv[1], sys.argv[2]
mdir = sys.argv[3] if len(sys.argv) > 3 else 'model'
lang = sys.argv[4] if len(sys.argv) > 4 else 'hi'
m = WhisperModel(mdir, device='cpu', compute_type='int8')
raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', src, '-ac', '1', '-ar', '16000', '-f', 'f32le', '-'], capture_output=True).stdout
segs, _ = m.transcribe(np.frombuffer(raw, np.float32), language=lang, word_timestamps=True, beam_size=5)
res = []
for s in segs:
    res.append({'start': s.start, 'end': s.end, 'text': s.text, 'words': [(w.start, w.end, w.word) for w in s.words]})
    print(f'{s.start:6.2f}-{s.end:6.2f} {s.text}')
json.dump(res, open(out, 'w'), ensure_ascii=False, indent=1)
