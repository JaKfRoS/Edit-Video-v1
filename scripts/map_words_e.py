#!/usr/bin/env python3
"""GAYA E - petakan kata ke timeline aroll: kata asli digeser +O (tanpa potongan),
kata hook-salinan dipetakan terpisah. Verifikasi: semua kata sumber harus ada (X/X)."""
import json
edl = json.load(open("work/edl.json"))
O = edl["offset_src_to_out"]
H0, H1 = edl["hook_copy"]["src"]
src = json.load(open("work/audio.json"))
words = [w for s in src["segments"] for w in s["words"]]
out = [{"start": round(w["start"] + O, 3), "end": round(w["end"] + O, 3),
        "word": w["word"], "prob": w["prob"]} for w in words]
hook = [{"start": round(w["start"] - H0, 3), "end": round(w["end"] - H0, 3), "word": w["word"]}
        for w in words if H0 - 0.05 <= w["start"] and w["end"] <= H1 + 0.05]
json.dump({"duration": edl["result_duration"], "words": out, "hook_words": hook},
          open("work/words_aroll.json", "w"), ensure_ascii=False, indent=1)
print(f"kata sumber: {len(words)} | kata hasil (asli): {len(out)} | hilang: {len(words)-len(out)}")
print(f"kata hook-salinan: {len(hook)} -> {[h['word'].strip() for h in hook]}")
print(f"total kata terdengar di hasil: {len(out)+len(hook)} (= asli + {len(hook)})")
