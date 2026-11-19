#!/usr/bin/env python3
"""Tumpuk mockup UI Shopee Video di atas frame, untuk cek caption tidak tertutup.

Koordinat diukur dari screenshot 1206x2622 (video cover-fit ke 1080x1920):
  kartu produk y 1384-1608 | kolom aksi x>=852 | sisi kepotong 52px kiri/kanan
"""
import subprocess, sys
from PIL import Image, ImageDraw
SRC = sys.argv[1] if len(sys.argv) > 1 else "work/final_master.mp4"
OUT = sys.argv[2] if len(sys.argv) > 2 else "work/shopee_check.jpg"
TIMES = [float(x) for x in (sys.argv[3].split(",") if len(sys.argv) > 3
         else "1.0,12.6,19.9,26.5,31.5,38.0,47.0,51.5".split(","))]
TH = 640
tiles = []
for t in TIMES:
    p = f"work/sc_{t}.png"
    subprocess.run(["ffmpeg","-hide_banner","-loglevel","error","-ss",f"{max(0,t-2):.2f}","-i",SRC,
                    "-ss",f"{min(2,t):.2f}","-frames:v","1","-vf",f"scale=-1:{TH}",p,"-y"],check=True)
    im = Image.open(p).convert("RGB"); SC = 1920/TH
    ov = Image.new("RGBA", im.size, (0,0,0,0)); d = ImageDraw.Draw(ov)
    # sisi kepotong cover-fit
    d.rectangle([0,0,52/SC,im.height], fill=(255,0,0,90))
    d.rectangle([(1080-52)/SC,0,im.width,im.height], fill=(255,0,0,90))
    # kartu produk
    d.rectangle([40/SC,1384/SC,1040/SC,1608/SC], fill=(255,255,255,205), outline=(255,0,0,255), width=3)
    d.text((70/SC,1420/SC), "KARTU PRODUK SHOPEE", fill=(200,0,0,255))
    # bar diskon + handle + caption toko
    d.rectangle([40/SC,1630/SC,660/SC,1700/SC], fill=(255,255,255,190))
    d.rectangle([40/SC,1730/SC,820/SC,1870/SC], fill=(0,0,0,150))
    # kolom aksi kanan
    d.rectangle([852/SC,930/SC,im.width,1760/SC], fill=(0,120,255,80), outline=(0,120,255,255), width=2)
    d.text((860/SC,950/SC), "IKON", fill=(0,90,255,255))
    # UI atas
    d.rectangle([0,0,im.width,218/SC], fill=(0,0,0,130))
    im = Image.alpha_composite(im.convert("RGBA"), ov).convert("RGB")
    ImageDraw.Draw(im).text((6,4), f"{t}s", fill=(0,255,255))
    tiles.append(im)
W,H = tiles[0].size; cols = 4; rows = (len(tiles)+cols-1)//cols
sh = Image.new("RGB",(W*cols,H*rows),(18,18,18))
for i,im in enumerate(tiles): sh.paste(im,((i%cols)*W,(i//cols)*H))
sh.save(OUT, quality=88); print(OUT, sh.size)
