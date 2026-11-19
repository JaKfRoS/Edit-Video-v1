#!/usr/bin/env python3
"""Render FINAL satu pass dari aroll: zoom + warm grade + caption sekaligus.

Menggabungkan render_zoom.py dan render_captions.py jadi satu encode, supaya
hanya ada 2 generasi encoding (sumber -> aroll -> final), bukan 4.
"""
import json, subprocess, sys, glob, os

SRC = "work/aroll.mp4"
OUT = sys.argv[1] if len(sys.argv) > 1 else "work/final_video.mp4"
CRF = sys.argv[2] if len(sys.argv) > 2 else "18"

K = json.load(open("work/zoom_plan.json"))["keys"]


def ramp(field):
    terms = [f"{K[0][field]}"]
    for prev, cur in zip(K, K[1:]):
        a, b = prev[field], cur[field]
        if a == b:
            continue
        t0, d = cur["t"], max(cur["dur"], 1e-6)
        P = f"clip((t-{t0})/{d},0,1)"
        E = f"if(lt({P},0.5),4*pow({P},3),1-pow(2-2*({P}),3)/2)"
        terms.append(f"({b - a})*({E})")
    return "(" + "+".join(terms) + ")"


Z, CX, CY = ramp("z"), ramp("cx"), ramp("cy")
ZOOM = (f"scale=w='2*round(540*({Z}))':h='2*round(960*({Z}))':eval=frame:flags=lanczos,"
        f"crop=1080:1920:x='clip(({CX})*({Z})-540,0,iw-1080)':"
        f"y='clip(({CY})*({Z})-960,0,ih-1920)',setsar=1")
GRADE = ("eq=saturation=1.12:contrast=1.06:brightness=0.012,"
         "colorbalance=rs=0.055:gs=0.012:bs=-0.05:rm=0.03:bm=-0.025")

data = json.load(open("work/captions.json"))
items = [("work/cap/hook.png", data["hook"]["start"], data["hook"]["end"])]
for i, c in enumerate(data["captions"]):
    items.append((f"work/cap/c{i:03d}.png", c["start"], c["end"]))
items.append(("work/cap/outro.png", 49.58, 99))
for p, _, _ in items:
    if not os.path.exists(p):
        sys.exit(f"PNG caption hilang: {p} - jalankan render_captions.py dulu")

cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-stats", "-i", SRC]
for p, _, _ in items:
    cmd += ["-i", p]
fc = [f"[0:v]{ZOOM},{GRADE}[bg]"]
prev = "bg"
for n, (p, s, e) in enumerate(items, start=1):
    fc.append(f"[{prev}][{n}:v]overlay=0:0:enable='between(t,{s},{e})'[v{n}]")
    prev = f"v{n}"
cmd += ["-filter_complex", ";".join(fc), "-map", f"[{prev}]", "-map", "0:a",
        "-c:v", "libx264", "-crf", CRF, "-preset", "slow", "-profile:v", "high",
        "-level", "4.1", "-pix_fmt", "yuv420p", "-r", "30", "-fps_mode", "cfr",
        "-x264-params", "keyint=60:min-keyint=30",
        "-c:a", "copy", "-movflags", "+faststart", OUT, "-y"]
print(f"satu pass: zoom + grade + {len(items)} caption -> {OUT} (crf {CRF}, preset slow)")
sys.exit(subprocess.run(cmd).returncode)
