#!/usr/bin/env python3
"""Petakan timestamp kata dari sumber -> timeline aroll (pakai edl.json)."""
import json

edl = json.load(open("work/edl.json"))
segs = edl["segments"]
src = json.load(open("work/audio.json"))
words = [w for s in src["segments"] for w in s["words"]]

def to_out(t):
    """waktu sumber -> waktu hasil. Kalau jatuh di jeda yang dibuang, dijepit
    ke batas segmen terdekat (kata di tepi potongan tetap ikut)."""
    for s in segs:
        if s["src_start"] - 1e-6 <= t <= s["src_end"] + 1e-6:
            return s["out_start"] + (t - s["src_start"])
    best, bd = None, 1e9
    for s in segs:
        for sv, ov in ((s["src_start"], s["out_start"]), (s["src_end"], s["out_end"])):
            if abs(t - sv) < bd:
                best, bd = ov, abs(t - sv)
    return best

def seg_of(t):
    for s in segs:
        if s["src_start"] - 1e-6 <= t < s["src_end"] + 1e-6:
            return s
    return None

out, lost = [], []
for w in words:
    a = to_out(w["start"])
    sg = seg_of(w["start"])
    # akhir kata dihitung di segmen yang sama dgn awalnya, dijepit ke ujung segmen
    b = (sg["out_start"] + (min(w["end"], sg["src_end"]) - sg["src_start"])) if sg else to_out(w["end"])
    if a is None or b is None or b <= a:
        lost.append(w); continue
    out.append({"start": round(a, 3), "end": round(b, 3),
                "word": w["word"], "prob": w["prob"]})
out.sort(key=lambda w: w["start"])

json.dump({"duration": edl["result_duration"], "words": out},
          open("work/words_aroll.json", "w"), ensure_ascii=False, indent=1)

print(f"kata sumber : {len(words)}")
print(f"kata hasil  : {len(out)}")
print(f"hilang      : {len(lost)}  {[w['word'] for w in lost]}")
print(f"durasi      : {edl['result_duration']}s")
print("\n12 kata pertama di timeline baru:")
for w in out[:12]:
    print(f"  {w['start']:6.2f}-{w['end']:6.2f}  \"{w['word']}\"")
