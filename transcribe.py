#!/usr/bin/env python3
"""Transkrip audio/video -> txt / srt / vtt / json (dengan word-level timestamps).

Contoh:
    ./transcribe.py clip.mp4
    ./transcribe.py clip.mp4 --model large-v3 --formats srt,json
    ./transcribe.py clip.mp4 --lang auto
"""
import argparse, json, os, sys, time
from pathlib import Path

MODELS = {
    "turbo":    "deepdml/faster-whisper-large-v3-turbo-ct2",
    "large-v3": "Systran/faster-whisper-large-v3",
}


def ts(sec: float, sep: str = ",") -> str:
    h, rem = divmod(max(sec, 0), 3600)
    m, s = divmod(rem, 60)
    return f"{int(h):02d}:{int(m):02d}:{int(s):02d}{sep}{int(round(s % 1 * 1000)):03d}"


def write_srt(segs, path):
    with open(path, "w", encoding="utf-8") as f:
        for i, s in enumerate(segs, 1):
            f.write(f"{i}\n{ts(s['start'])} --> {ts(s['end'])}\n{s['text'].strip()}\n\n")


def write_vtt(segs, path):
    with open(path, "w", encoding="utf-8") as f:
        f.write("WEBVTT\n\n")
        for s in segs:
            f.write(f"{ts(s['start'], '.')} --> {ts(s['end'], '.')}\n{s['text'].strip()}\n\n")


def main():
    p = argparse.ArgumentParser(description="Transkrip pakai faster-whisper (default: Bahasa Indonesia)")
    p.add_argument("input", help="file audio/video apa aja (mp4, mov, wav, mp3, ...)")
    p.add_argument("-m", "--model", default="turbo", choices=list(MODELS),
                   help="turbo = 2.5x lebih cepat, akurasi setara (default)")
    p.add_argument("-l", "--lang", default="id", help="kode bahasa, atau 'auto' (default: id)")
    p.add_argument("-f", "--formats", default="txt,srt,json", help="txt,srt,vtt,json")
    p.add_argument("-o", "--outdir", default=None, help="folder output (default: sebelah input)")
    p.add_argument("--beam", type=int, default=5)
    p.add_argument("--no-vad", action="store_true", help="matikan filter silence")
    p.add_argument("--threads", type=int, default=os.cpu_count() or 4)
    p.add_argument("--compute", default="int8", help="int8 (CPU) / float16 (GPU)")
    p.add_argument("--device", default="cpu")
    p.add_argument("--prompt", default=None, help="initial_prompt, mis. daftar nama/istilah")
    a = p.parse_args()

    src = Path(a.input)
    if not src.exists():
        sys.exit(f"error: file tidak ditemukan: {src}")

    from faster_whisper import WhisperModel

    t0 = time.time()
    model = WhisperModel(MODELS[a.model], device=a.device,
                         compute_type=a.compute, cpu_threads=a.threads)
    print(f"[{a.model}] model siap dalam {time.time()-t0:.1f}s", file=sys.stderr)

    t1 = time.time()
    seg_iter, info = model.transcribe(
        str(src),
        language=None if a.lang == "auto" else a.lang,
        beam_size=a.beam,
        vad_filter=not a.no_vad,
        word_timestamps=True,
        initial_prompt=a.prompt,
    )
    print(f"bahasa: {info.language} (conf {info.language_probability:.2f}) | "
          f"durasi {info.duration:.1f}s", file=sys.stderr)

    segs = []
    for s in seg_iter:
        segs.append({
            "start": s.start, "end": s.end, "text": s.text,
            "words": [{"start": w.start, "end": w.end,
                       "word": w.word, "prob": round(w.probability, 3)}
                      for w in (s.words or [])],
        })
        print(f"  [{s.start:7.2f} -> {s.end:7.2f}] {s.text.strip()}", file=sys.stderr)

    took = time.time() - t1
    print(f"selesai dalam {took:.1f}s (RTF {took/max(info.duration,0.01):.2f}x)", file=sys.stderr)

    outdir = Path(a.outdir) if a.outdir else src.parent
    outdir.mkdir(parents=True, exist_ok=True)
    stem = outdir / src.stem
    want = {x.strip() for x in a.formats.split(",") if x.strip()}
    made = []

    if "txt" in want:
        (stem.with_suffix(".txt")).write_text(
            "\n".join(s["text"].strip() for s in segs) + "\n", encoding="utf-8")
        made.append(stem.with_suffix(".txt"))
    if "srt" in want:
        write_srt(segs, stem.with_suffix(".srt")); made.append(stem.with_suffix(".srt"))
    if "vtt" in want:
        write_vtt(segs, stem.with_suffix(".vtt")); made.append(stem.with_suffix(".vtt"))
    if "json" in want:
        (stem.with_suffix(".json")).write_text(json.dumps({
            "source": str(src), "model": a.model, "language": info.language,
            "language_probability": info.language_probability,
            "duration": info.duration, "segments": segs,
        }, ensure_ascii=False, indent=2), encoding="utf-8")
        made.append(stem.with_suffix(".json"))

    for m in made:
        print(f"-> {m}")


if __name__ == "__main__":
    main()
