#!/usr/bin/env python3
"""TAHAP A - render aroll.mp4: potongan disambung jadi satu, RESOLUSI ASLI, tanpa zoom."""
import json, subprocess, sys

e = json.load(open("work/edl.json"))
segs = e["segments"]
n = len(segs)

f = [f"[0:v]split={n}" + "".join(f"[sv{i}]" for i in range(n)),
     f"[0:a]asplit={n}" + "".join(f"[sa{i}]" for i in range(n))]
for i, s in enumerate(segs):
    a, b = s["src_start"], s["src_end"]
    f.append(f"[sv{i}]trim=start={a}:end={b},setpts=PTS-STARTPTS[v{i}]")
    f.append(f"[sa{i}]atrim=start={a}:end={b},asetpts=PTS-STARTPTS[a{i}]")
f.append("".join(f"[v{i}][a{i}]" for i in range(n)) + f"concat=n={n}:v=1:a=1[vo][ao]")

cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-stats",
       "-i", e["source"], "-filter_complex", ";".join(f),
       "-map", "[vo]", "-map", "[ao]",
       "-c:v", "libx264", "-crf", "16", "-preset", "medium",
       "-profile:v", "high", "-pix_fmt", "yuv420p", "-r", "30", "-fps_mode", "cfr",
       "-c:a", "aac", "-b:a", "160k", "-ac", "1",
       "-movflags", "+faststart", "work/aroll.mp4", "-y"]
print("segmen:", n)
sys.exit(subprocess.run(cmd).returncode)
