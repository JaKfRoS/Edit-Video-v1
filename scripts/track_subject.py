#!/usr/bin/env python3
"""Lacak posisi talent di aroll.mp4 tanpa model ML.

Kamera statis -> background = median semua frame. Yang beda dari background = talent.
Output work/track.json: per waktu -> head_top, center_x, bbox (koordinat frame 1080x1920).
"""
import json, os, subprocess, glob
import numpy as np
from PIL import Image

SRC, FPS, SC = "work/aroll.mp4", 5, 5          # sample 5 fps, skala 1/5 -> 216x384
D = "work/track_frames"
THRESH, MINROW = 26, 6

os.makedirs(D, exist_ok=True)
for f in glob.glob(f"{D}/*.png"):
    os.remove(f)
subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-i", SRC,
                "-vf", f"fps={FPS},scale={1080//SC}:{1920//SC}", f"{D}/f%04d.png", "-y"], check=True)

files = sorted(glob.glob(f"{D}/f*.png"))
arr = np.stack([np.asarray(Image.open(f).convert("RGB"), dtype=np.uint8) for f in files])
print(f"frame sample : {len(files)}  ({arr.shape[2]}x{arr.shape[1]})")

bg = np.median(arr, axis=0).astype(np.int16)
Image.fromarray(bg.astype(np.uint8)).save("work/background_plate.png")

out = []
for i, fr in enumerate(arr):
    diff = np.abs(fr.astype(np.int16) - bg).sum(axis=2)
    m = diff > THRESH * 3
    rows = m.sum(axis=1)
    cols = m.sum(axis=0)
    if m.sum() < 150:
        out.append(None); continue
    ys = np.where(rows > MINROW)[0]
    xs = np.where(cols > MINROW)[0]
    if not len(ys) or not len(xs):
        out.append(None); continue
    cx = float((np.arange(len(cols)) * cols).sum() / max(cols.sum(), 1))
    out.append({"t": round(i / FPS, 3),
                "head_top": int(ys[0] * SC), "bottom": int(ys[-1] * SC),
                "x0": int(xs[0] * SC), "x1": int(xs[-1] * SC),
                "cx": round(cx * SC, 1), "area": int(m.sum())})

# isi lubang + haluskan
val = [o for o in out if o]
for i, o in enumerate(out):
    if o is None:
        near = min(val, key=lambda v: abs(v["t"] - i / FPS))
        out[i] = dict(near, t=round(i / FPS, 3), filled=True)

def smooth(key, w=5):
    v = np.array([o[key] for o in out], dtype=float)
    k = np.ones(w) / w
    return np.convolve(np.pad(v, (w//2, w//2), mode="edge"), k, mode="valid")[:len(v)]

for key in ("head_top", "cx", "x0", "x1", "bottom"):
    sm = smooth(key)
    for o, s in zip(out, sm):
        o[key + "_s"] = round(float(s), 1)

json.dump(out, open("work/track.json", "w"), indent=1)
ht = [o["head_top_s"] for o in out]
cx = [o["cx_s"] for o in out]
print(f"head_top     : {min(ht):.0f} - {max(ht):.0f} px   (rata {np.mean(ht):.0f})")
print(f"center_x     : {min(cx):.0f} - {max(cx):.0f} px   (rata {np.mean(cx):.0f})")
print("\nposisi tiap 4 detik:")
for o in out[::FPS * 4]:
    print(f"  t={o['t']:5.1f}s  head_top={o['head_top_s']:6.0f}  cx={o['cx_s']:6.0f}  x={o['x0']:4d}-{o['x1']:4d}")
