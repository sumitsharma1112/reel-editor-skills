#!/bin/bash
# EffectCraft reel prototype: beats -> JSX -> .ecproj -> H.264 MP4 (1080x1920)
set -e
B=${EFFECTCRAFT_CLI:-/home/claude/ext/target/release/effectcraft-cli}
python3 beats.py assets/song.wav plan_in.json plan.json
python3 make_reel.py plan.json assets reel.jsx
$B script reel.jsx --empty --save-as "$PWD/reel.ecproj"
$B render --project reel.ecproj --comp Reel --out "$PWD/Craft_Reel_Prototype.mp4" --format h264 --audio on
