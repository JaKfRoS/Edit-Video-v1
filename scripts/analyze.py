#!/usr/bin/env python3
"""Analisa transkrip: jeda, blok konten, estimasi durasi tiap rencana potong."""
import json, sys

MIN_GAP = 0.30   # jeda > ini dipotong
KEEP    = 0.10   # sisa napas

d = json.load(open(sys.argv[1] if len(sys.argv) > 1 else "work/audio.json"))
words = [w for s in d["segments"] for w in s["words"]]
total = d["duration"]

# jeda antar kata
gaps = []
for a, b in zip(words, words[1:]):
    g = b["start"] - a["end"]
    if g > MIN_GAP:
        gaps.append((a["end"], b["start"], g, a["word"].strip(), b["word"].strip()))
lead = words[0]["start"]
tail = total - words[-1]["end"]

saved = sum(g[2] - KEEP for g in gaps) + max(0, lead - KEEP) + max(0, tail - KEEP)
print(f"durasi asli        : {total:.2f}s")
print(f"jeda > {MIN_GAP}s       : {len(gaps)} titik, total {sum(g[2] for g in gaps):.2f}s")
print(f"lead-in {lead:.2f}s | tail {tail:.2f}s")
print(f"hemat dari jeda    : {saved:.2f}s  ->  {total-saved:.2f}s\n")
print("JEDA:")
for s, e, g, wa, wb in gaps:
    print(f"  {s:6.2f} -> {e:6.2f}  ({g:.2f}s)   ...{wa} | {wb}...")

SECTIONS = [
    ("HOOK",      0.00,  9.80, "ajakan pemula + mau spill ukuran/kapasitas"),
    ("P1 60x45",  10.56, 20.21, "D60 T45, 50 bibit, setara 5 kolam galon + praktis"),
    ("ULANG",     20.21, 22.65, "'setara dengan 5 kolam galon' DIULANG"),
    ("P2 60x60",  23.39, 28.59, "D60 T60, isi 60 lele sampai panen tanpa sortir"),
    ("KANIBAL",   29.42, 43.72, "objection kanibalisme 0% + pakan PF1000 protein 39%"),
    ("CTA1",      43.72, 48.94, "ajakan checkout skala rumahan"),
    ("P3 100x60", 49.46, 54.90, "D1m T60, 200 bibit sampai panen, sortir"),
    ("CTA2",      55.55, 58.70, "checkout, stok tiap hari, check out sekarang"),
]
print("\nBLOK KONTEN:")
for n, s, e, desc in SECTIONS:
    print(f"  {n:<10} {s:6.2f}-{e:6.2f}  {e-s:5.2f}s  {desc}")
print(f"  {'JUMLAH':<10} {sum(e-s for _,s,e,_ in SECTIONS):22.2f}s bicara bersih")
