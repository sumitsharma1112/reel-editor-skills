---
name: series-thumbnails
description: Consistent 1080x1920 reel covers for Sumit's biography, sant katha and book summary reels - category tag pill, big white outlined title, coloured subtitle pill, PART badge, soft backdrop built from the reel's own colours.
---

# Series thumbnails

Use when Sumit asks for thumbnails/covers for his biography or book-summary reels, or to make his reels grid look organised.

1. Open his reels tab in the browser, read each reel's caption, pick biography / sant katha / book summary reels and work out Part 1 / Part 2 from the captions.
2. The workspace cannot download Instagram images. In the page, shrink each reel's cover to a 4x7 colour grid and return it as hex (one line per reel in `scripts/pal.txt`: `index:hex...`).
3. Edit the `T` list in `scripts/series_thumbnails.py` (index, reel id, category, title lines, subtitle, part) and run it; it writes `out/NN_Title_PARTn_<reelid>.jpg` and a contact sheet. Look at the sheet.
4. Text stays in the middle band (y 520-1300) so the 3:4 grid crop keeps it. Roman Hinglish only.
5. Instagram web cannot change a reel cover; Sumit sets each cover in the phone app (Edit > Cover > Add from camera roll). The reel id in the file name tells him which reel it belongs to.
