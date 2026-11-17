---
name: style-demo-site
description: Render trending reel-style demo clips with the AI avatar and rebuild the AI Tricks Studio service website.
---

# Style demo site (AI Tricks Studio)

`demos.py` renders 10 trending reel-style demos (540x960, 8s) with the AI avatar:
text behind head, liquid glass cards, wall text, karaoke captions, glitch cuts,
editorial font mix, neon glow, punch-in + stickers, counter/split-flap, comment pop-ups.

```
python3 demos.py --sample 3.5          # stills to /tmp/sample_*.jpg
python3 demos.py text_behind glass     # renders site/media/<style>.mp4 + poster
```

The website lives in `/studio-site` (static HTML, deployed on Vercel with root directory `studio-site`).
