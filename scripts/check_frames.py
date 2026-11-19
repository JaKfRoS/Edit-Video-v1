#!/usr/bin/env python3
"""Sapu seluruh video, buat contact sheet + garis safe zone. Untuk periksa frame by frame."""
import subprocess, sys
from PIL import Image, ImageDraw
SRC = sys.argv[1] if len(sys.argv) > 1 else "work/zoomed.mp4"
OUT = sys.argv[2] if len(sys.argv) > 2 else "work/sweep.jpg"
STEP = float(sys.argv[3]) if len(sys.argv) > 3 else 2.5
dur = float(subprocess.run(["ffprobe","-v","error","-show_entries","format=duration",
                            "-of","csv=p=0",SRC],capture_output=True,text=True).stdout.strip())
TH = 300
tiles = []
t = 0.4
while t < dur:
    p = f"work/sw_{t:.1f}.png"
    subprocess.run(["ffmpeg","-hide_banner","-loglevel","error","-ss",f"{max(0,t-2):.2f}","-i",SRC,
                    "-ss",f"{min(2,t):.2f}","-frames:v","1","-vf",f"scale=-1:{TH}",p,"-y"],check=True)
    im = Image.open(p).convert("RGB"); d = ImageDraw.Draw(im); SC = 1920/TH
    for y in (220,1470): d.line([(0,y/SC),(im.width,y/SC)],fill=(255,60,60),width=1)
    d.text((3,3),f"{t:.1f}s",fill=(255,255,0))
    d.rectangle([0,0,im.width-1,im.height-1],outline=(120,120,0),width=1)
    tiles.append(im); t += STEP
W,H = tiles[0].size; cols = 7; rows = (len(tiles)+cols-1)//cols
sh = Image.new("RGB",(W*cols,H*rows),(18,18,18))
for i,im in enumerate(tiles): sh.paste(im,((i%cols)*W,(i//cols)*H))
sh.save(OUT,quality=85); print(f"{OUT}  {sh.size}  {len(tiles)} frame")
