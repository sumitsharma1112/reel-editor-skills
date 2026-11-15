---
name: story-ama
description: 10-second animated 9:16 "Ask Me Anything" Instagram story for @aitricksbysumit with an empty glowing slot for the Instagram question sticker. Use when Sumit asks for an AMA / question-box story video.
---
# Ask Me Anything story
`python3 scripts/ama.py` → Ask_Me_Anything_Story.mp4 (10 s, 1080x1920, 30 fps, silent track so Instagram music can be added).
`python3 scripts/ama.py 6.0` → preview still f_6.0.png.

Layout (story safe zones): handle pill y=300, "ASK ME / ANYTHING" slam-in y=440-690, Kaushan "kuch bhi poocho!" y=905, sticker slot 150-930 x 1060-1390 with bobbing arrows, 4 floating question chips y=1450-1645 (edit CHIPS list). Fonts: Anton, SpaceMono, Montserrat, Kaushan Script.
