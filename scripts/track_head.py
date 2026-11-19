#!/usr/bin/env python3
"""Lacak kepala talent via deteksi warna kulit (YCrCb) + connected components.

Tidak butuh model ML. Output work/head.json: per waktu -> head_top, head_cx, face box.
"""
import json, subprocess, glob, os
import numpy as np
import cv2

SRC, FPS = "work/aroll.mp4", 5
D = "work/hf"
os.makedirs(D, exist_ok=True)
for f in glob.glob(f"{D}/*.png"):
    os.remove(f)
subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-i", SRC,
                "-vf", f"fps={FPS},scale=270:480", f"{D}/f%04d.png", "-y"], check=True)
files = sorted(glob.glob(f"{D}/f*.png"))
SC = 1080 / 270      # 4.0

rows = []
for i, fp in enumerate(files):
    bgr = cv2.imread(fp)
    ycc = cv2.cvtColor(bgr, cv2.COLOR_BGR2YCrCb)
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    Y, Cr, Cb = ycc[:, :, 0], ycc[:, :, 1], ycc[:, :, 2]
    S, V = hsv[:, :, 1], hsv[:, :, 2]
    # kulit: Cr/Cb khas TAPI saturasi sedang - kolam oranye sangat jenuh, dibuang
    skin = ((Cr > 136) & (Cr < 173) & (Cb > 77) & (Cb < 127)
            & (Y > 80) & (S > 28) & (S < 150) & (V > 90)).astype(np.uint8)
    skin[int(skin.shape[0] * 0.68):, :] = 0      # kepala tak pernah di 32% terbawah
    skin = cv2.morphologyEx(skin, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    skin = cv2.morphologyEx(skin, cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8))
    n, lab, stats, cent = cv2.connectedComponentsWithStats(skin, 8)
    best, bs = None, 0
    for k in range(1, n):
        x, y, w, h, a = stats[k]
        if a < 55:
            continue
        ar = h / max(w, 1)
        score = a * (1.35 if 0.8 < ar < 2.4 else 0.5)   # wajah cenderung agak lonjong
        if score > bs:
            best, bs = (x, y, w, h, a), score
    if best is None:
        rows.append(None); continue
    x, y, w, h, a = best
    rows.append({"t": round(i / FPS, 3),
                 "top": round(y * SC), "cx": round((x + w / 2) * SC),
                 "w": round(w * SC), "h": round(h * SC), "area": int(a)})

ok = [r for r in rows if r]
for i, r in enumerate(rows):
    if r is None:
        near = min(ok, key=lambda v: abs(v["t"] - i / FPS))
        rows[i] = dict(near, t=round(i / FPS, 3), filled=True)

def smooth(key, w=7):
    v = np.array([r[key] for r in rows], float)
    k = np.ones(w) / w
    return np.convolve(np.pad(v, (w // 2, w // 2), mode="edge"), k, mode="valid")[:len(v)]

for key in ("top", "cx"):
    for r, s in zip(rows, smooth(key)):
        r[key + "_s"] = round(float(s))

json.dump(rows, open("work/head.json", "w"), indent=1)
det = sum(1 for r in rows if not r.get("filled"))
print(f"sample {len(rows)}  terdeteksi {det} ({det/len(rows)*100:.0f}%)")
print(f"head_top : {min(r['top_s'] for r in rows)} - {max(r['top_s'] for r in rows)}")
print(f"head_cx  : {min(r['cx_s'] for r in rows)} - {max(r['cx_s'] for r in rows)}")
B = json.load(open("work/blocks.json"))
print("\nper blok (median):")
for b in B:
    sel = [r for r in rows if b["start"] <= r["t"] < b["end"]]
    if not sel: continue
    print(f"  {b['id']:8s} {b['start']:5.1f}-{b['end']:5.1f}s  "
          f"head_top={int(np.median([r['top_s'] for r in sel])):4d}  "
          f"cx={int(np.median([r['cx_s'] for r in sel])):4d}")
