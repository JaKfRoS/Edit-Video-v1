#!/usr/bin/env python3
"""Tambah SFX halus di kata kunci saja - tidak pernah lebih keras dari suara talent."""
import subprocess, sys, os

SFX = "/root/.claude/skills/video-edit/assets/template/assets/sfx"
# (waktu, berkas, gain)  -- hanya di momen kunci, bukan tiap caption
EV = [   # gaya E: waktu hasil = waktu sumber + 2.30
    (0.90,  "pop",           0.22),   # hook: "5 kolam galon"
    (2.30,  "whoosh-short",  0.26),   # crossfade hook -> video asli
    (14.12, "pop",           0.22),   # 45 cm
    (23.88, "pop",           0.22),   # 5 kolam galon (ucapan asli)
    (27.94, "pop",           0.20),   # isi 60
    (38.56, "sparkle",       0.18),   # 0%
    (45.24, "sparkle",       0.18),   # protein 39%
    (55.18, "pop",           0.22),   # 200 bibit
    (58.00, "click",         0.18),   # kartu CTA muncul
    (60.34, "impact-bass-1", 0.28),   # "Check out sekarang"
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
