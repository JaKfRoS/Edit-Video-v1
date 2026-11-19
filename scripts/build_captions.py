#!/usr/bin/env python3
"""Kelompokkan kata jadi frasa caption pendek + tandai kata kunci (emas).

Aturan:
  - pecah di akhir kalimat (. ? !), tidak pernah menyambung dua kalimat
  - 2-4 kata / maks ~22 karakter
  - angka dan satuannya TIDAK dipisah ("45 cm", "39 %")
  - rentang HOOK ditangani terpisah (teks besar), tidak jadi caption biasa
Koreksi hanya untuk artefak transkrip, bukan mengubah ucapan talent.
"""
import json, re

HOOK_END = 2.30      # gaya E: video asli mulai di 2.30 (crossfade)
FIX = {          # koreksi artefak transkrip saja - ucapan talent tidak diubah
    "leleh": "lele", "Leleh": "Lele",
    "spil": "spill",
    "Tokamire": "toko kami",      # dikonfirmasi klien: "toko kami"
}
BYTIME = {        # koreksi per kata (waktu hasil = sumber + 2.30), dikonfirmasi klien / pengenalan ke-2
    56.80 + 2.30: "ready",       # "di stok" -> "ready stok" (transkrip ke-2: "ready")
    51.20 + 2.30: "1 meter",     # "diameter 1" = 1 meter (dikonfirmasi klien)
}
NOBREAK = {"diameter", "tinggi", "kapasitas", "isi", "yang", "di", "dengan", "atau", "dari", "untuk", "mau", "dan", "setara", "ready"}
UNITS = {"cm", "%", "meter", "m"}

W = [w for w in json.load(open("work/words_aroll.json"))["words"] if w["start"] >= HOOK_END - 1e-6]
toks = []
for w in W:
    t = w["word"].strip()
    for tt, rep in BYTIME.items():
        if abs(w["start"] - tt) < 0.02:
            t = rep + "".join(c for c in t if c in ".,?!")
    t = FIX.get(t.strip(".,?!"), t.strip(".,?!")) + "".join(c for c in t if c in ".,?!")
    # token yang diawali "-" (mis. "-kolam") disatukan ke token sebelumnya
    if t.startswith("-") and toks:
        toks[-1]["t"] += t
        toks[-1]["end"] = w["end"]
        continue
    toks.append({"t": t, "start": w["start"], "end": w["end"]})

def is_key(t):
    s = re.sub(r"[^\w%]", "", t).upper()
    return bool(re.fullmatch(r"\d+%?", s) or s in {"PF1000", "1METER"})

EMOJI = {"galon": "🪣", "0%": "✅", "39%": "💪", "200": "🐟",
         "praktis": "⚡", "sortir": "🎯", "check out": "🛒"}

MAXW, MAXC = 4, 22
caps, cur = [], []
for i, tk in enumerate(toks):
    cur.append(tk)
    nxt = toks[i + 1] if i + 1 < len(toks) else None
    txt = " ".join(x["t"] for x in cur)
    end_sent = bool(re.search(r"[.?!]$", tk["t"]))
    # kata berikutnya berhuruf kapital = awal kalimat baru -> pecah di sini
    new_sent = bool(nxt and len(cur) >= 2 and re.match(r"[A-Z][a-z]", nxt["t"])
                    and not re.search(r"[.?!,]$", tk["t"]))
    # jangan pisahkan angka dari satuannya
    glue = bool(nxt and re.fullmatch(r"\d+", tk["t"].strip(".,")) and nxt["t"].strip(".,").lower() in UNITS)
    # jangan putus setelah kata sambung/pembuka spesifikasi, dan "ya." menempel ke frasa sebelumnya
    orphan = bool(nxt and re.search(r"[.?!]$", nxt["t"]) and len(cur) >= 3)   # satu kata sendirian di ujung kalimat
    hang = (tk["t"].strip(".,?!").lower() in NOBREAK or orphan or (nxt and nxt["t"].strip(".,?!").lower() == "ya")) \
        and not end_sent and len(cur) < MAXW + 2
    brk = end_sent or nxt is None or (not glue and not hang and (new_sent or len(cur) >= MAXW or len(txt) >= MAXC))
    if not brk:
        continue
    caps.append({"start": round(cur[0]["start"], 3), "end": round(cur[-1]["end"] + 0.06, 3),
                 "words": [{"t": x["t"], "key": is_key(x["t"])} for x in cur]})
    cur = []

for i, c in enumerate(caps):
    if c["end"] - c["start"] < 0.45:
        c["end"] = c["start"] + 0.45
    if i + 1 < len(caps):
        c["end"] = min(c["end"], caps[i + 1]["start"] - 0.01)
    c["text"] = re.sub(r"\s+-", "-", " ".join(w["t"] for w in c["words"]))
    low = c["text"].lower()
    c["emoji"] = next((e for k, e in EMOJI.items() if k in low), None)

hook = {"start": 0.0, "end": HOOK_END - 0.05,
        "lines": [{"t": "SETARA", "key": False}, {"t": "5 KOLAM GALON", "key": True}]}
json.dump({"hook": hook, "captions": caps}, open("work/captions.json", "w"),
          ensure_ascii=False, indent=1)

print(f"caption {len(caps)} | emas {sum(1 for c in caps if any(w['key'] for w in c['words']))}"
      f" | emoji {sum(1 for c in caps if c['emoji'])}"
      f" | rata {sum(c['end']-c['start'] for c in caps)/len(caps):.2f}s\n")
for c in caps:
    g = "".join("*" if w["key"] else "" for w in c["words"])
    print(f"  {c['start']:6.2f}-{c['end']:6.2f}  {c['text']:<26} {c['emoji'] or ' '} {g}")
