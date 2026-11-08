#!/bin/bash
# Tilt-view reel: landscape clips -> 4K -> crossfade -> rotate 90 deg CW (2160x3840) with a "TILT YOUR PHONE" intro.
# Usage: tilt_view_reel.sh <scene.png for the phone icon> <out.mp4> <clip1.mp4:start:dur> <clip2.mp4:start:dur> ...
# Rendered in stages (one 4K ffmpeg at a time): a single filter graph with all inputs gets OOM-killed on 8 GB.
set -e
HERE="$(cd "$(dirname "$0")" && pwd)"; SCENE="$1"; OUT="$2"; shift 2
W=$(mktemp -d); X=0.6
python3 -I "$HERE/tilt_intro.py" 2 "$W/intro" "$SCENE"
ENC="-c:v libx264 -preset veryfast -crf 14 -pix_fmt yuv420p -r 24 -an"
UP="scale=3840:2160:flags=lanczos,unsharp=7:7:0.8:5:5:0.0"
ffmpeg -v error -y -framerate 24 -i "$W/intro/f_%04d.png" -vf format=yuv420p $ENC "$W/si.mp4"
i=0; AIN=(); AF=""; 
for spec in "$@"; do
  IFS=: read f st du <<<"$spec"
  ffmpeg -v error -y -ss "$st" -t "$du" -i "$f" -vf "setpts=PTS-STARTPTS,fps=24,$UP,transpose=1,format=yuv420p" $ENC "$W/s$i.mp4"
  ffmpeg -v error -y -ss "$st" -t "$du" -i "$f" -vn -af "loudnorm=I=-17:TP=-2:LRA=9,aresample=48000,aformat=channel_layouts=stereo" "$W/a$i.wav"
  i=$((i+1))
done
# join pairwise
cp "$W/s0.mp4" "$W/acc.mp4"; acc=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$W/acc.mp4")
for ((k=1;k<i;k++)); do
  off=$(python3 -c "print(round($acc-$X,3))")
  ffmpeg -v error -y -i "$W/acc.mp4" -i "$W/s$k.mp4" -filter_complex "[0][1]xfade=transition=fade:duration=$X:offset=$off,format=yuv420p" $ENC "$W/n.mp4"
  mv "$W/n.mp4" "$W/acc.mp4"; acc=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$W/acc.mp4")
done
ioff=2.4; tot=$(python3 -c "print(round(2.8+$acc-0.4,3))")
ffmpeg -v error -y -i "$W/si.mp4" -i "$W/acc.mp4" -filter_complex "[0][1]xfade=transition=fade:duration=0.4:offset=$ioff,fade=t=out:st=$(python3 -c "print(round($tot-0.8,3))"):d=0.8,format=yuv420p" -c:v libx264 -preset medium -crf 18 -pix_fmt yuv420p -r 24 -an "$W/v.mp4"
# audio: intro sfx, then clip audios crossfaded
cp "$W/a0.wav" "$W/aacc.wav"
for ((k=1;k<i;k++)); do ffmpeg -v error -y -i "$W/aacc.wav" -i "$W/a$k.wav" -filter_complex "[0][1]acrossfade=d=$X" "$W/an.wav"; mv "$W/an.wav" "$W/aacc.wav"; done
ffmpeg -v error -y -i "$W/intro/intro.wav" -i "$W/aacc.wav" -filter_complex "[0]aresample=48000,aformat=channel_layouts=stereo[a];[1]aformat=channel_layouts=stereo[b];[a][b]acrossfade=d=0.4,afade=t=out:st=$(python3 -c "print(round($tot-0.8,3))"):d=0.8" -c:a aac -b:a 192k "$W/a.m4a"
ffmpeg -v error -y -i "$W/v.mp4" -i "$W/a.m4a" -map 0:v -map 1:a -c copy -shortest -movflags +faststart "$OUT"
echo "done: $OUT"; rm -rf "$W"
