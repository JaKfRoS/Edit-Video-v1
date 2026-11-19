#!/usr/bin/env python3
"""Sampling frame per blok kalimat + grid koordinat, buat menentukan window zoom."""
import subprocess, sys, json
from PIL import Image, ImageDraw

SRC = "work/aroll.mp4"
BLOCKS = json.load(open("work/blocks.json"))
TH = 480                      # tinggi tile di contact sheet
SC = 1920 / TH                # faktor skala balik ke koordinat 1080x1920

tiles = []
for i, b in enumerate(BLOCKS):
    t = (b["start"] + b["end"]) / 2
    p = f"work/blk_{i:02d}.png"
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-ss", f"{t:.2f}",
                    "-i", SRC, "-frames:v", "1", "-vf", f"scale=-1:{TH}", p, "-y"], check=True)
    im = Image.open(p).convert("RGB")
    d = ImageDraw.Draw(im)
    # grid tiap 200px (koordinat frame asli)
    for y in range(200, 1920, 200):
        yy = y / SC
        d.line([(0, yy), (im.width, yy)], fill=(0, 255, 160), width=1)
        d.text((3, yy + 1), str(y), fill=(0, 255, 160))
    for x in range(200, 1080, 200):
        xx = x / SC
        d.line([(xx, 0), (xx, im.height)], fill=(0, 255, 160), width=1)
        d.text((xx + 2, 2), str(x), fill=(0, 255, 160))
    # safe zone: atas 220, bawah 1470
    d.line([(0, 220/SC), (im.width, 220/SC)], fill=(255, 60, 60), width=2)
    d.line([(0, 1470/SC), (im.width, 1470/SC)], fill=(255, 60, 60), width=2)
    d.rectangle([0, 0, im.width - 1, im.height - 1], outline=(255, 255, 0), width=2)
    d.text((6, im.height - 30), f"{i}  {b['start']:.1f}-{b['end']:.1f}s", fill=(255, 255, 0))
    tiles.append(im)

cols = 5
rows = (len(tiles) + cols - 1) // cols
W, H = tiles[0].size
sheet = Image.new("RGB", (W * cols, H * rows), (20, 20, 20))
for i, im in enumerate(tiles):
    sheet.paste(im, ((i % cols) * W, (i // cols) * H))
sheet.save(sys.argv[1] if len(sys.argv) > 1 else "work/grid_sheet.jpg", quality=86)
print("sheet:", sheet.size, "tiles:", len(tiles))
