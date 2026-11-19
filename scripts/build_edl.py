#!/usr/bin/env python3
"""TAHAP A - bangun EDL: potong jeda > MIN_SIL, sisakan KEEP_SIL, pindahkan hook ke depan.

Output: work/edl.json  (segmen sumber -> posisi di timeline hasil + titik sambungan)
"""
import json, subprocess, sys, os

SRC       = "/root/raw-footage/Mentah1.MOV"
WORDS     = "work/audio.json"
MIN_SIL   = 0.30    # jeda lebih dari ini dipotong
KEEP_SIL  = 0.10    # napas yang disisakan
MARGIN    = 0.06    # jarak aman dari kata terdekat, biar konsonan nggak kepotong
MIN_SAVE  = 0.15    # kalau hematnya kurang dari ini, nggak usah dipotong (sambungan sia-sia)
MIN_KEEP  = 0.45    # segmen lebih pendek dari ini digabung ke tetangga
HOOK      = (13.86, 15.90)   # "setara dengan 5 kolam galon."


def silences(wav):
    out = subprocess.run(
        ["ffmpeg", "-hide_banner", "-i", wav, "-af",
         f"silencedetect=noise=-32dB:d={MIN_SIL}", "-f", "null", "-"],
        capture_output=True, text=True).stderr
    res, start = [], None
    for line in out.splitlines():
        if "silence_start:" in line:
            start = float(line.split("silence_start:")[1].strip())
        elif "silence_end:" in line and start is not None:
            end = float(line.split("silence_end:")[1].split("|")[0].strip())
            res.append((start, end)); start = None
    return res


def main():
    d = json.load(open(WORDS))
    dur = d["duration"]
    words = [w for s in d["segments"] for w in s["words"]]

    # daerah yang DIBUANG: bagian tengah tiap jeda panjang
    drops = []
    for s, e in silences("work/audio.wav"):
        if e - s <= MIN_SIL:
            continue
        # jangan sampai makan kata: jepit ke jeda antar-kata terdekat
        lo = max((w["end"] for w in words if w["end"] <= s + 0.15), default=s)
        hi = min((w["start"] for w in words if w["start"] >= e - 0.15), default=e)
        a, b = max(s, lo + MARGIN), min(e, hi - MARGIN)
        if b - a - KEEP_SIL >= MIN_SAVE:
            mid = (a + b) / 2
            drops.append((mid - (b - a - KEEP_SIL) / 2, mid + (b - a - KEEP_SIL) / 2))
    # ekor diam di akhir
    last = words[-1]["end"]
    if dur - last > KEEP_SIL:
        drops.append((last + KEEP_SIL, dur))

    drops.sort()
    # keep = komplemen dari drops
    keeps, cur = [], 0.0
    for a, b in drops:
        if a > cur:
            keeps.append((cur, a))
        cur = max(cur, b)
    if cur < dur:
        keeps.append((cur, dur))

    # gabung segmen super pendek ke tetangga (hindari cut beruntun yang choppy)
    merged = []
    for a, b in keeps:
        if merged and (b - a < MIN_KEEP or merged[-1][1] - merged[-1][0] < MIN_KEEP):
            merged[-1] = (merged[-1][0], b)
        else:
            merged.append((a, b))
    keeps = merged

    # buang rentang HOOK dari badan, lalu taruh di paling depan
    body = []
    for a, b in keeps:
        if b <= HOOK[0] or a >= HOOK[1]:
            body.append((a, b)); continue
        if a < HOOK[0]:
            body.append((a, HOOK[0]))
        if b > HOOK[1]:
            body.append((HOOK[1], b))
    segs = [HOOK] + [s for s in body if s[1] - s[0] > 0.04]

    # susun timeline hasil
    edl, t = [], 0.0
    for i, (a, b) in enumerate(segs):
        ln = b - a
        edl.append({"i": i, "src_start": round(a, 3), "src_end": round(b, 3),
                    "out_start": round(t, 3), "out_end": round(t + ln, 3),
                    "dur": round(ln, 3),
                    "label": "HOOK (dipindah ke depan)" if i == 0 else ""})
        t += ln

    out = {"source": SRC, "source_duration": dur, "result_duration": round(t, 3),
           "saved": round(dur - t, 3),
           "min_silence": MIN_SIL, "keep_silence": KEEP_SIL,
           "hook_moved": {"src": list(HOOK), "text": "setara dengan 5 kolam galon"},
           "segments": edl,
           "junctions": [round(s["out_end"], 3) for s in edl[:-1]]}
    os.makedirs("work", exist_ok=True)
    json.dump(out, open("work/edl.json", "w"), indent=2)

    print(f"segmen    : {len(edl)}")
    print(f"asli      : {dur:.2f}s")
    print(f"hasil     : {t:.2f}s   (hemat {dur-t:.2f}s)")
    print(f"sambungan : {len(out['junctions'])} titik\n")
    for s in edl:
        print(f"  {s['i']:2d}  src {s['src_start']:6.2f}-{s['src_end']:6.2f}"
              f"  -> out {s['out_start']:6.2f}-{s['out_end']:6.2f}  ({s['dur']:5.2f}s) {s['label']}")


if __name__ == "__main__":
    main()
