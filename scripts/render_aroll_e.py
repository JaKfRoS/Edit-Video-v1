#!/usr/bin/env python3
"""TAHAP A - GAYA E (Utuh + Style): NOL potongan.

Rekaman asli diputar UTUH dari detik 0. Satu tambahan di depan: hook DIGANDAKAN
("setara dengan 5 kolam galon"), diberi ekor diam, lalu crossfade 0.25s ke video asli.
Audio hook tidak pernah tumpang tindih dengan audio asli (ekor diam > 0.2s).

Output: work/aroll.mp4 (resolusi asli ter-rotasi, 30fps CFR) + work/edl.json
"""
import json, subprocess, sys

SRC = "/root/raw-footage/Mentah1.MOV"
H0, H1 = 13.83, 15.93          # kalimat hook di sumber ("setara dengan 5 kolam galon.")
O = 2.30                       # detik di timeline hasil saat video asli mulai (crossfade mulai)
XF = 0.25                      # durasi crossfade
SRC_DUR = 59.2413125

hook_len = H1 - H0             # 2.10
fc = [
    # video hook: kalimat + freeze frame terakhir sampai crossfade selesai
    f"[0:v]trim=start={H0}:end={H1},setpts=PTS-STARTPTS,fps=30,"
    f"tpad=stop_mode=clone:stop_duration={O + XF - hook_len + 0.1:.3f},"
    f"trim=end={O + XF:.3f},setsar=1,format=yuv420p[hv]",
    # video asli utuh
    "[0:v]setpts=PTS-STARTPTS,fps=30,setsar=1,format=yuv420p[ov]",
    f"[hv][ov]xfade=transition=fade:duration={XF}:offset={O}[vo]",
    # audio: hook + ekor diam sepanjang O detik, lalu audio asli UTUH (tanpa fade)
    f"[0:a]atrim=start={H0}:end={H1},asetpts=PTS-STARTPTS,aformat=sample_rates=48000:channel_layouts=mono,"
    f"apad=whole_dur={O}[ha]",
    "[0:a]asetpts=PTS-STARTPTS,aformat=sample_rates=48000:channel_layouts=mono[oa]",
    "[ha][oa]concat=n=2:v=0:a=1[ao]",
]
cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-stats", "-i", SRC,
       "-filter_complex", ";".join(fc), "-map", "[vo]", "-map", "[ao]",
       "-c:v", "libx264", "-crf", "16", "-preset", "medium",
       "-profile:v", "high", "-pix_fmt", "yuv420p", "-r", "30", "-fps_mode", "cfr",
       "-c:a", "aac", "-b:a", "160k", "-ac", "1",
       "-movflags", "+faststart", "work/aroll.mp4", "-y"]

total = O + SRC_DUR
edl = {"style": "E - utuh + style (nol potongan)", "source": SRC, "source_duration": SRC_DUR,
       "result_duration": round(total, 3), "added": round(total - SRC_DUR, 3),
       "hook_copy": {"src": [H0, H1], "text": "setara dengan 5 kolam galon", "tail_silence_until": O},
       "original_starts_at": O, "crossfade": {"start": O, "dur": XF},
       "offset_src_to_out": O, "junctions": []}
json.dump(edl, open("work/edl.json", "w"), indent=2)
print(f"hasil {total:.2f}s = asli {SRC_DUR:.2f}s + {O:.2f}s (hook + ekor)")
sys.exit(subprocess.run(cmd).returncode)
