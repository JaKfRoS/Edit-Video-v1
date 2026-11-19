#!/usr/bin/env python3
"""Tambah SFX halus di kata kunci saja - tidak pernah lebih keras dari suara talent."""
import subprocess, sys, os

SFX = "/root/.claude/skills/video-edit/assets/template/assets/sfx"
# (waktu, berkas, gain)  -- hanya di momen kunci, bukan tiap caption
EV = [
    (0.00,  "whoosh-short", 0.26),   # masuk hook
    (2.06,  "click-soft",   0.20),   # potong ke intro
    (12.10, "pop",          0.22),   # 45 cm / 50 bibit
    (19.54, "pop",          0.22),   # 5 kolam galon
    (21.96, "pop",          0.20),   # 60 cm / isi 60
    (30.82, "sparkle",      0.18),   # 0%
    (37.50, "sparkle",      0.18),   # protein 39%
    (46.60, "pop",          0.22),   # 200 bibit
    (49.60, "click",        0.18),   # kartu CTA muncul
    (52.14, "impact-bass-1", 0.28),  # CTA akhir
]
SRC = sys.argv[1] if len(sys.argv) > 1 else "work/styled.mp4"
OUT = sys.argv[2] if len(sys.argv) > 2 else "work/final_master.mp4"

miss = [e for e in EV if not os.path.exists(f"{SFX}/{e[1]}.mp3")]
if miss:
    sys.exit(f"SFX hilang: {miss}")

cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-stats", "-i", SRC]
for _, f, _ in EV:
    cmd += ["-i", f"{SFX}/{f}.mp3"]
fc = []
for n, (t, f, g) in enumerate(EV, start=1):
    fc.append(f"[{n}:a]aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=mono,"
              f"volume={g},adelay={int(t*1000)}|{int(t*1000)}[s{n}]")
mix = "[0:a]" + "".join(f"[s{n}]" for n in range(1, len(EV) + 1))
fc.append(f"{mix}amix=inputs={len(EV)+1}:duration=first:normalize=0,"
          f"alimiter=limit=0.95:level=disabled[ao]")
cmd += ["-filter_complex", ";".join(fc), "-map", "0:v", "-map", "[ao]",
        "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ac", "1",
        "-movflags", "+faststart", OUT, "-y"]
print(f"SFX: {len(EV)} titik -> {OUT}")
sys.exit(subprocess.run(cmd).returncode)
