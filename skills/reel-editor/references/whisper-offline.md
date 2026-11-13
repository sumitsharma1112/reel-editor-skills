# Whisper when Hugging Face is blocked

The cloud workspace blocks huggingface.co, so faster-whisper cannot download models. A Whisper small CTranslate2 int8 model is published on npm in four parts:

```
for i in 0 1 2 3; do npm pack @skillninja/shortmovie-telop-model-p$i; done
for i in 0 1 2 3; do mkdir x$i; tar -xzf skillninja-shortmovie-telop-model-p$i-*.tgz -C x$i; done
mkdir model; cp x0/package/*.json model/
cat x0/package/model.bin.part0 x1/package/model.bin.part1 x2/package/model.bin.part2 x3/package/model.bin.part3 > model/model.bin
pip install --break-system-packages faster-whisper
```

Pass audio as a float32 numpy array decoded by ffmpeg (16 kHz mono) instead of a file path: the bundled PyAV can clash with the installed one.
Hindi text from Whisper small is rough (spellings), but word timings are good: keep the times, rewrite the words.
Script: `skills/earshot/scripts/whisper_words.py`.
