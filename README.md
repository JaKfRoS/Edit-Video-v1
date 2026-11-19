# Edit-Video-v1

## Transkrip (faster-whisper)

Transkrip audio/video ke `txt` / `srt` / `vtt` / `json` dengan **word-level timestamps**.
Default bahasa Indonesia.

### Setup

```bash
uv venv .venv --python 3.13
uv pip install --python .venv/bin/python -r requirements.txt
```

Model ke-download otomatis saat pertama dipakai (cache di `~/.cache/huggingface`).

### Pakai

```bash
./transcribe clip.mp4                          # turbo, bahasa Indonesia
./transcribe clip.mp4 --model large-v3         # akurasi maksimal
./transcribe clip.mp4 --lang auto              # deteksi bahasa otomatis
./transcribe clip.mp4 --formats srt,json
./transcribe clip.mp4 -o out/
./transcribe clip.mp4 --prompt "Shoken, Shopee, reels"   # bantu ejaan nama/istilah
```

### Model

| Model | Ukuran | Kecepatan (4 vCPU, int8) | Catatan |
|---|---|---|---|
| `turbo` *(default)* | ~1.6 GB | **RTF 0.25x** (~4x realtime) | akurasi Indonesia setara large-v3 |
| `large-v3` | ~3.1 GB | RTF 0.59x (~1.7x realtime) | paling teliti buat audio berat/noise |

### Output JSON

```json
{
  "language": "id",
  "segments": [
    {
      "start": 0.98, "end": 6.70,
      "text": " Ini adalah CEP ke-5 Marteli dalam 4 tahun.",
      "words": [{ "start": 0.98, "end": 1.58, "word": " Ini", "prob": 0.92 }]
    }
  ]
}
```

`prob` = confidence per kata. Berguna buat nandain kata yang perlu dicek manual,
dan buat animasi caption per-kata.

### Catatan

- `av` dipin ke `14.2.0` — versi 15+ ngehapus kwarg yang masih dipakai `faster-whisper 1.2.1`.
- Container ini CPU-only, jadi `compute_type` default `int8`. Kalau ada GPU: `--device cuda --compute float16`.
