---
name: script-title-png
description: Transparent 1080x1920 PNG title overlay in the hand-lettered creator style (Jaspreet Dyora type covers) - tilted cream brush-script name, smaller pink subtitle, dark outline, soft drop shadow, little sparkle rays.
---

# Script title PNG

Use when Sumit wants a reel title / cover text "in the same caption style" as hand-lettered creator covers.

- Font: Kaushan Script (OFL, in `fonts/`).
- Main line: cream (248,232,205), size ~150, rotated ~6 degrees, 7px dark outline + blurred shadow.
- Second line: pink (244,166,185), size ~78, same tilt.
- Sparkle rays (3 short strokes) at the top-left and top-right corners of the title.
- Keep it at y 250-550 so the Instagram top bar and the 3:4 grid crop don't cut it.
- Edit the two `layer(...)` calls in `scripts/script_title.py` (text, size, colour, y) and run it; it writes the PNG and a preview on an image and on dark grey.
