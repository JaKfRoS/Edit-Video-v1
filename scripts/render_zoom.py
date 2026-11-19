#!/usr/bin/env python3
"""TAHAP B - zoom halus di timeline gabungan.

Metode: scale(eval=frame) lalu crop ukuran tetap 1080x1920. BUKAN zoompan (bergetar).
Easing ease-in-out cubic, transisi mulai tepat di titik sambungan EDL.
"""
import json, subprocess, sys

P = json.load(open("work/zoom_plan.json"))
K = P["keys"]
OUT = sys.argv[1] if len(sys.argv) > 1 else "work/zoomed.mp4"
SRC = sys.argv[2] if len(sys.argv) > 2 else "work/aroll.mp4"


def ramp(field):
    """Bentuk ADITIF (tanpa if bertingkat): nilai awal + jumlah tiap transisi.

        v(t) = V0 + SUM (Vi - V[i-1]) * E(clip((t - Ti)/Di, 0, 1))

    E = ease-in-out cubic. Transisi tidak tumpang tindih, jadi penjumlahan aman.
    Jauh lebih pendek dari if bertingkat -> ffmpeg mengevaluasinya dengan benar.
    """
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


def check():
    """verifikasi numerik ekspresi yang sama di Python"""
    import math
    def val(field, t):
        v = K[0][field]
        for prev, cur in zip(K, K[1:]):
            a, b = prev[field], cur[field]
            if a == b: continue
            p = min(max((t - cur["t"]) / max(cur["dur"], 1e-6), 0), 1)
            e = 4*p**3 if p < 0.5 else 1 - (2-2*p)**3/2
            v += (b - a) * e
        return v
    print("  t      z     cx    cy")
    for t in (1.0, 2.3, 2.55, 6.0, 12.2, 12.45, 18.0, 25.1, 30.8, 33.45, 38.0, 43.9, 47.0, 51.1, 58.0):
        print(f"  {t:5.1f}  {val('z',t):.3f}  {val('cx',t):5.0f} {val('cy',t):5.0f}")


check()
Z, CX, CY = ramp("z"), ramp("cx"), ramp("cy")
# scale: ukuran berubah tiap frame (dibulatkan genap). crop: ukuran TETAP, posisi bergerak.
vf = (f"scale=w='2*round(540*({Z}))':h='2*round(960*({Z}))':eval=frame:flags=lanczos,"
      f"crop=1080:1920:"
      f"x='clip(({CX})*({Z})-540,0,iw-1080)':"
      f"y='clip(({CY})*({Z})-960,0,ih-1920)',"
      f"setsar=1")

open("work/zoom_vf.txt", "w").write(vf)
cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-stats", "-i", SRC,
       "-vf", vf, "-c:v", "libx264", "-crf", "16", "-preset", "medium",
       "-profile:v", "high", "-pix_fmt", "yuv420p", "-r", "30", "-fps_mode", "cfr",
       "-c:a", "copy", "-movflags", "+faststart", OUT, "-y"]
print(f"keys: {len(K)}  panjang ekspresi: {len(vf)} char")
sys.exit(subprocess.run(cmd).returncode)
