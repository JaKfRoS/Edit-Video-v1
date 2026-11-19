# Panduan Editing Video Jualan v1

Panduan ini bukan teori. Semua angka di sini **hasil ukur dan uji** pada satu proyek nyata:
`Mentah1.MOV` → reel 9:16 untuk Shopee Video / TikTok / Reels, 19 November 2026.

Target: talking-head one-take → reel jualan yang rapi, caption aman dari UI platform,
dan setiap keputusan bisa diulang lewat script.

---

## 1. Lingkungan

| Kebutuhan | Versi teruji | Catatan |
|---|---|---|
| ffmpeg / ffprobe | 6.1.1 | wajib |
| Python | 3.13 | venv di `.venv/` |
| faster-whisper | 1.2.1 | + `ctranslate2` 4.9.0 |
| `av` | **14.2.0** | **wajib di-pin** |
| Pillow | 13.0 | render caption |
| Font | Inter Black + Noto Color Emoji | sudah ada di container |
| SFX | `~/.claude/skills/video-edit/assets/template/assets/sfx/` | pop, click, sparkle, whoosh, impact |

```bash
uv venv .venv --python 3.13
uv pip install --python .venv/bin/python -r requirements.txt
```

> **Jebakan:** `av` 15+ menghapus kwarg `metadata_errors` yang masih dipakai faster-whisper 1.2.1,
> dan `av` 14.4.0 tidak punya wheel untuk Python 3.13. Harus **14.2.0**.

---

## 2. Alur kerja (6 langkah)

Berhenti dan tunjukkan hasil ke klien di **langkah 2** dan **langkah 5**.

```
1. Cek file + lingkungan
2. Transkrip Indonesia  ──────────► TUNJUKKAN, minta keputusan
3. TAHAP A: potong + gabung (resolusi asli, tanpa zoom)
4. TAHAP B: zoom di timeline gabungan
5. Caption + style + preview 540x960 ──► TUNJUKKAN, tunggu ACC
6. Render final 1080x1920 + ekspor
```

---

## 3. Langkah 1 — Cek sumber

```bash
ffprobe -v error -select_streams v:0 \
  -show_entries stream=codec_name,width,height,r_frame_rate,bit_rate \
  -show_entries stream_side_data=rotation -of default=nw=1 input.MOV
```

**Yang wajib dicek:**

| Cek | Kenapa penting |
|---|---|
| `rotation` | Video HP sering disimpan 1920×1080 + rotasi −90°. ffmpeg auto-rotate → decoded jadi 1080×1920. Jangan tertipu angka `width/height` mentah. |
| Resolusi *setelah* rotasi | Menentukan berapa banyak ruang zoom yang ada |
| `r_frame_rate` vs `avg_frame_rate` | Kalau beda, sumbernya VFR → wajib `-fps_mode cfr` |

**Temuan kasus ini:** decoded **1080×1920** — persis sama dengan resolusi render akhir.
Artinya **tidak ada headroom 4K**. Setiap punch-in = upscale:

| Zoom | Area crop | Efek |
|---|---|---|
| 1.25× | 864×1536 | aman, masih tajam |
| 1.5× | 720×1280 | mulai terasa lembut |

Kalau sumbernya 4K, batas ini tidak berlaku — bisa sampai 2× tanpa kehilangan ketajaman.
**Sampaikan ini ke klien sebelum mulai**, jangan setelah render.

---

## 4. Langkah 2 — Transkrip Indonesia

```bash
ffmpeg -i input.MOV -vn -ac 1 -ar 16000 -c:a pcm_s16le work/audio.wav -y
./transcribe work/audio.wav --model large-v3 --lang id --formats srt,json,txt -o work
```

| Model | RTF (4 vCPU, int8) | Pakai untuk |
|---|---|---|
| `large-v3` | 1.14× | transkrip final, audio lapangan/berisik |
| `turbo` | 0.28× | cek cepat, verifikasi |

Keduanya butuh **word-level timestamps** (`word_timestamps=True`) — itu dasar caption dan titik potong.

### Yang dilaporkan ke klien

Pecah transkrip jadi blok: **hook / penjelasan produk / harga-promo / penutup**.
Lalu tandai:

- **Filler** (`eee`, `anu`) — kasus ini: nol, talent lancar
- **Kalimat ulang** — kasus ini: *"setara 5 kolam galon"* muncul 2×
- **CTA dobel** — kasus ini: ada 2 CTA yang fungsinya sama
- **Kata confidence rendah** (`prob < 0.6`) — cek ulang manual

```bash
jq -r '.segments[].words[] | select(.prob < 0.60) | "\(.start)s p=\(.prob) \"\(.word)\""' work/audio.json
```

> **Pelajaran nyata:** kata berbunyi *"Tokamire"* (prob 0.73) ternyata **"toko kami, ready stock"**.
> Transkrip ulang hasil potongan (`aroll.mp4`) mengonfirmasinya — konteks kalimat yang sudah rapat
> membuat Whisper lebih akurat. **Selalu tanya klien** untuk nama toko/merek, jangan menebak.

### Hitung durasi sebelum janji

```bash
.venv/bin/python scripts/analyze.py work/audio.json
```

Potong jeda saja biasanya **hanya hemat 10–12%**. Kasus ini: 59.24s → 55.5s, padahal target 30–45s.
**Sajikan opsi potong konten ke klien dengan angka**, jangan diputuskan sendiri.

---

## 5. Langkah 3 — TAHAP A: potong & gabung

Script: `scripts/build_edl.py` → `scripts/render_aroll.py`

### Parameter teruji

```python
MIN_SIL   = 0.30   # jeda lebih dari ini dipotong
KEEP_SIL  = 0.10   # napas yang disisakan
MARGIN    = 0.06   # jarak aman dari kata terdekat
MIN_SAVE  = 0.15   # hemat < ini? jangan potong (sambungan sia-sia)
MIN_KEEP  = 0.45   # segmen < ini digabung ke tetangga (hindari cut beruntun)
```

Dua parameter terakhir **wajib**. Tanpanya muncul potongan 0.04 detik yang tidak menghemat apa pun
tapi menambah titik sambungan, dan segmen 0.43 detik yang bikin cut terasa patah-patah.
Di kasus ini: 16 segmen → **14 segmen**, hasil lebih halus.

### Hook

Pindahkan kalimat paling menjual ke 3 detik pertama. **Pindah, bukan gandakan.**

> **Trik:** kalau ada kalimat yang diucapkan 2×, pindahkan **instance pertama** ke depan.
> Instance kedua tetap di tempatnya → **nol konten hilang**, dan kalimat aslinya tetap mengalir.
> Di kasus ini: *"setara dengan 5 kolam galon"* (13.86–15.90) ditarik ke 0.00–2.04.

### Render

Resolusi **asli**, tanpa zoom, tanpa resize turun:

```python
ffmpeg -i SRC -filter_complex "
  [0:v]split=N[sv0][sv1]...;
  [0:a]asplit=N[sa0][sa1]...;
  [sv0]trim=start=A:end=B,setpts=PTS-STARTPTS[v0]; ...
  [v0][a0][v1][a1]...concat=n=N:v=1:a=1[vo][ao]"
  -crf 16 -preset medium -r 30 -fps_mode cfr
```

### Verifikasi wajib

```bash
.venv/bin/python scripts/map_words.py          # harus 148/148 kata, 0 hilang
./transcribe work/aroll.mp4 --model turbo --lang id -o work   # transkrip ulang
```

Kalau jumlah kata berkurang, ada konsonan yang kepotong → naikkan `MARGIN`.

> **Jebakan pemetaan:** kata yang jatuh tepat di batas potongan bisa "hilang".
> Hitung akhir kata di **segmen yang sama dengan awalnya**, lalu jepit ke ujung segmen itu.
> Jangan cari segmen terpisah untuk `start` dan `end`.

---

## 6. Langkah 4 — TAHAP B: zoom

Script: `scripts/zoom_plan.json` → `scripts/render_zoom.py`

### Metode: `scale(eval=frame)` + `crop` ukuran tetap

**Jangan pakai `zoompan`** — bergetar.
**Jangan pakai `crop` dengan ukuran berubah** — `crop` hanya mengevaluasi `w`/`h` sekali di awal;
hanya `x`/`y` yang per-frame.

```
scale=w='2*round(540*(Z))':h='2*round(960*(Z))':eval=frame:flags=lanczos,
crop=1080:1920:
  x='clip((CX)*(Z)-540,0,iw-1080)':
  y='clip((CY)*(Z)-960,0,ih-1920)',
setsar=1
```

`Z`, `CX`, `CY` adalah ekspresi waktu. `CX`/`CY` dalam koordinat sumber (0–1080 / 0–1920).

### Easing: bentuk ADITIF, bukan `if` bertingkat

```
v(t) = V0 + Σ (Vi − V[i−1]) · E( clip((t − Ti)/Di, 0, 1) )

E(p) = p < 0.5 ? 4p³ : 1 − (2−2p)³/2        (ease-in-out cubic)
```

Transisi tidak tumpang tindih, jadi penjumlahan aman. Bentuk ini **5.642 karakter**
versus 7.940 untuk `if` bertingkat 10 level — lebih pendek, lebih mudah dibaca,
dan gampang diverifikasi angkanya:

```python
# replikasi ekspresi yang sama di Python, cetak z/cx/cy di beberapa t
# t=47.0 harus z=1.25 ; t=2.3 (tengah transisi) harus z=1.111
```

**Selalu jalankan verifikasi numerik ini** sebelum render panjang.

### Aturan penempatan

| Aturan | Alasan |
|---|---|
| Transisi **mulai tepat di titik sambungan** EDL | Potongan menyamarkan awal gerakan |
| Durasi **0.4–0.6 detik** | Di bawah itu terasa menyentak |
| Level dipertahankan **sepanjang satu kalimat** | Zoom berubah di tengah kalimat terasa gelisah |
| Jangan ubah zoom di tengah kata | Titik sambungan selalu di jeda, jadi aman otomatis |
| Level: wide 1.0 / medium 1.25 / close 1.5 | Sesuaikan batas atas dengan headroom sumber |

### Kuantisasi

Lebar hasil `scale` dibulatkan ke genap → langkah **2 px** di resolusi scaled
= **1.33–1.60 px di output**. Gerak nyata saat transisi ±40 px/frame,
jadi kuantisasi hanya ~4% dari gerakan → **tidak terlihat**.

Cek sendiri: cetak `2*round(540*z(t))` per frame sepanjang tiap transisi,
pastikan langkahnya monoton.

---

## 7. Menentukan window zoom — apa yang BERHASIL dan yang TIDAK

Ini bagian yang paling banyak membuang waktu. Baca sebelum mencoba.

### ❌ Background subtraction (median plate) — GAGAL

Asumsi kamera statis. **Kameranya bergerak** (handheld / pan), background plate jadi blur,
seluruh frame terdeteksi sebagai "berubah".

Cara cek cepat: simpan median plate sebagai PNG. **Kalau blur, kamera bergerak — hentikan.**

### ❌ Deteksi skin-tone (YCrCb) — GAGAL untuk footage ini

Kolam terpal oranye-coklat masuk rentang warna kulit. Setelah diperketat dengan gate
saturasi HSV dan batas area, akurasinya tetap hanya **6 dari 12 sampel** —
sering mengunci tiang, dahan, atau benda latar.

### ❌ YuNet ONNX — tidak bisa diunduh

`raw.githubusercontent.com` diblokir proxy (403).

### ❌ `headpos.py` dari skill video-edit — tidak berlaku

Butuh alpha hasil cutout (`assets/subject.webm`). Kalau briefnya **tanpa cutout**, tidak terpakai.

### ✅ Yang BERHASIL: tetapkan manual, lalu render dan lihat

1. Buat contact sheet per blok kalimat dengan **grid koordinat** + garis safe zone
   → `scripts/grid_sheet.py`
2. Tetapkan `z`, `cx`, `cy` per blok dari frame yang terbaca jelas
3. **Render crop yang diusulkan dan lihat hasilnya** — ini satu-satunya kebenaran
4. Sapu seluruh durasi tiap 2.5 detik → `scripts/check_frames.py`

> **Pelajaran mahal:** jangan menilai framing dari thumbnail kecil di contact sheet.
> Saya pernah salah baca sebuah tiang di tile kecil, menyimpulkan ekspresi zoom rusak,
> lalu menulis ulang kode yang sebenarnya **sudah benar**. Uji A/B frame ukuran penuh
> (hasil render vs crop manual yang diharapkan) menyelesaikannya dalam satu langkah.
> **Kalau ragu, perbesar frame-nya.**

### Batas yang tidak bisa ditolong crop

Di kasus ini kamera pan ke kolam besar dan **talent keluar frame dari detik 48.2 sampai 51.0**.
Tidak ada crop yang bisa memunculkan informasi yang tidak terekam.

**Yang dilakukan:** turunkan zoom ke 1.0 di bagian itu, dan laporkan ke klien apa adanya.
Jangan diam-diam membiarkan kepala terpotong.

---

## 8. Safe zone — hasil ukur, bukan tebakan

Diukur dari screenshot Shopee Video **1206×2622**. Video ditampilkan **cover-fit**,
jadi perlu dikonversi ke koordinat frame 1080×1920:

```
skala = tinggi_area_video / 1920 = 2373 / 1920 = 1.2359
video_y = screen_y / 1.2359
video_x = (screen_x + 64.4) / 1.2359
```

### Hasil (koordinat frame 1080×1920)

| Elemen | Batas | Dampak |
|---|---|---|
| **Kartu produk Shopee** | mulai **y = 1384** | caption harus berakhir di atas ini |
| **Kolom ikon** (♥ 💬 Promosikan) | **x ≥ 852** | teks tidak boleh melewatinya |
| Bar diskon + @handle + deskripsi | y ≥ 1630 | sudah di luar area aman |
| **Sisi kiri & kanan terpotong** | **52 px** masing-masing | cover-fit memotong ~5% lebar |
| UI atas (status bar + search) | y ≤ 218 | sama dengan safe zone Reels |

### Nilai yang dipakai

```python
SAFE_T   = 220     # batas atas
SAFE_X   = 70      # margin sisi (lebih besar dari 52px area terpotong)
ICON_X   = 852     # kolom aksi kanan
BAND_BOT = 1355    # baris caption terbawah
CENTER_X = 461     # (SAFE_X + ICON_X) / 2 - teks digeser kiri
MAXW     = 762     # ICON_X - SAFE_X - 20
```

> Layout ini **lebih ketat dari TikTok/Reels**, jadi satu render aman untuk ketiga platform.
> Reels hanya minta bawah 450 px bersih (y < 1470) dan kolom kanan 100 px.

### Verifikasi

`scripts/check_shopee.py` menumpuk **mockup UI Shopee** (kartu produk, kolom ikon,
area terpotong) di atas frame hasil render. Jarak amannya **kelihatan**, bukan dikira-kira.

```bash
.venv/bin/python scripts/check_shopee.py ~/ekspor/final.mp4 work/cek.jpg "1.0,19.9,31.5,51.5"
```

---

## 9. Langkah 5 — Caption & style

Script: `scripts/build_captions.py` → `scripts/render_captions.py`

### Kenapa PNG, bukan `drawtext`

Satu frasa bisa berisi kata putih + kata emas + emoji. `drawtext` butuh satu filter per kata
dengan posisi `x` dihitung manual, plus neraka escaping. Render PNG transparan dengan PIL
memberi kontrol penuh, lalu tempel dengan `overlay=...:enable='between(t,s,e)'`.

41 overlay dalam satu filtergraph berjalan lancar.

### Pengelompokan frasa

| Aturan | Nilai |
|---|---|
| Maks kata / karakter | 4 kata / 22 karakter |
| Pecah di akhir kalimat | `.` `?` `!` — jangan pernah sambung dua kalimat |
| Pecah sebelum kata berhuruf kapital | awal kalimat yang tidak bertanda baca |
| **Jangan pisah angka dari satuannya** | `45 cm`, `39 %` harus satu frasa |
| Durasi minimum | 0.45 detik |
| Token diawali `-` | gabung ke token sebelumnya → `kolam-kolam`, bukan `kolam -kolam` |

> Aturan terakhir terlewat di render pertama dan **lolos sampai preview**.
> Perbaikan di level teks tidak cukup — renderer menggambar **per token**,
> jadi perbaikan harus di daftar token.

### Tipografi

| | |
|---|---|
| Font | Inter Black |
| Caption | 58 px, stroke hitam 7 px |
| Hook | 86 px, baris terbawah y = 1300 |
| Putih | `#ffffff` |
| **Emas** | `#ffd23f` |
| Kartu CTA | 52 px, pill gelap + garis emas, y = 1120 |

### Kapan pakai emas

Hanya **angka spesifikasi**: `50`, `5`, `45 cm`, `0%`, `39%`, `200`, `PF1000`.
Kalau semua di-emas, tidak ada yang menonjol — di kasus ini 10 dari 40 caption.

> **Aturan keras:** kalau talent **tidak menyebut harga**, jangan buat caption harga.
> Jangan menambah klaim yang tidak diucapkan. Di kasus ini tidak ada harga sama sekali,
> jadi emas dialihkan ke angka spesifikasi — dan ini **dilaporkan ke klien**.

### Koreksi transkrip yang boleh

Hanya artefak transkrip, bukan mengubah ucapan:

```python
FIX = {
    "leleh": "lele",          # artefak Whisper
    "spil": "spill",
    "Tokamire": "toko kami",  # dikonfirmasi klien
}
```

Logat tetap dibiarkan (`kerawatnya`, `doang`) — itu suara talent.

### Emoji

Noto Color Emoji adalah font bitmap. Render di ukuran **109 px** dengan
`embedded_color=True`, crop ke bounding box, lalu resize. Pakai **hanya di frasa kunci** —
di kasus ini 8 dari 40.

### Color grade (warm, halus)

```
eq=saturation=1.12:contrast=1.06:brightness=0.012,
colorbalance=rs=0.055:gs=0.012:bs=-0.05:rm=0.03:bm=-0.025
```

### Sound design

10 titik saja, hanya di momen kunci — bukan tiap caption.

| Momen | SFX | Gain |
|---|---|---|
| Masuk hook | `whoosh-short` | 0.26 |
| Potong ke intro | `click-soft` | 0.20 |
| Angka spesifikasi | `pop` | 0.20–0.22 |
| Angka unggulan (0%, 39%) | `sparkle` | 0.18 |
| Kartu CTA muncul | `click` | 0.18 |
| CTA akhir | `impact-bass-1` | 0.28 |

```
amix=inputs=N:duration=first:normalize=0,alimiter=limit=0.95:level=disabled
```

`normalize=0` **wajib** — tanpa itu suara talent ikut turun. Cek hasilnya:

```bash
ffmpeg -i final.mp4 -af volumedetect -f null - 2>&1 | grep -E "mean_volume|max_volume"
# target: max_volume mendekati -0.4 dB, tidak 0.0 (clipping)
```

### Preview

540×960, CRF 23 → ~6 MB. Cukup ringan untuk dilihat di HP, cukup jelas untuk menilai timing.

---

## 10. Langkah 6 — Render final

**Render satu pass dari `aroll.mp4`** — zoom + grade + semua caption dalam satu encode.

```
sumber → aroll → final          (2 generasi)   ✅
sumber → aroll → zoom → styled → final  (4 generasi)   ❌
```

```bash
.venv/bin/python scripts/render_final.py work/final_video.mp4 18
.venv/bin/python scripts/add_sfx.py work/final_video.mp4 ~/ekspor/final.mp4
```

| Setelan | Nilai |
|---|---|
| Codec | libx264, High 4.1 |
| CRF | 18, preset `slow` |
| Framerate | 30 CFR (`-fps_mode cfr`) |
| GOP | `keyint=60:min-keyint=30` |
| Pixel format | `yuv420p` |
| Audio | AAC 192k mono |
| | `-movflags +faststart` |

Hasil kasus ini: **40 MB / 6.2 Mbps** untuk 52.9 detik. Jangan dikompres lagi sebelum
upload — platform akan re-encode sendiri, sumber berkualitas tinggi justru menguntungkan.

Script bertahap (`render_zoom.py` + `render_captions.py`) tetap berguna sebagai
**jalur cepat untuk preview dan revisi**.

---

## 11. Checklist verifikasi

Jangan lapor selesai sebelum semua ini hijau.

- [ ] `ffprobe` — resolusi, fps, rotasi sumber dicatat
- [ ] Jumlah kata setelah potong **sama persis** dengan sebelum (`map_words.py`)
- [ ] Transkrip ulang `aroll.mp4` terbaca wajar, tidak ada kata terpenggal
- [ ] Verifikasi numerik ekspresi zoom (`z`, `cx`, `cy` di beberapa `t`)
- [ ] Kuantisasi zoom < 2 px di output
- [ ] Sapuan seluruh durasi: kepala di bawah y=220, produk terlihat (`check_frames.py`)
- [ ] Mockup UI Shopee: tidak ada caption tertutup kartu produk / kolom ikon (`check_shopee.py`)
- [ ] `max_volume` tidak 0.0 dB
- [ ] Durasi final = durasi EDL (±1 frame)
- [ ] Preview dikirim, **ACC diterima**, baru render final

---

## 12. Batasan yang diketahui

| Batasan | Nilai | Solusi |
|---|---|---|
| Upload connector Google Drive | **~3.1 MB per panggilan** | Kirim file ke chat, klien upload sendiri |
| `raw.githubusercontent.com` | diblokir proxy (403) | Pakai HuggingFace atau hindari unduhan model |
| CPU container | 4 vCPU, tanpa GPU | Whisper `int8`; render ~1.5–2 menit per pass |
| Container bersifat sementara | venv & model hilang saat sesi mati | Script di-commit; model auto-download saat dipakai |

---

## 13. Catatan untuk syuting berikutnya

Kalau footage-nya lebih baik, editnya jauh lebih mudah:

1. **Rekam 4K** kalau bisa. 1080×1920 = nol headroom untuk punch-in.
2. **Jangan pan terlalu jauh dari talent.** Di kasus ini talent keluar frame 2.8 detik.
3. **Sebutkan harga/promo** kalau mau muncul di caption — editor tidak boleh mengarang.
4. **Sebutkan nama toko dengan jelas** di penutup. Ucapan cepat bikin Whisper salah dengar.
5. **Beri jeda 0.5 detik antar kalimat.** Memudahkan potong bersih tanpa memenggal konsonan.
6. **Tripod kalau memungkinkan.** Kamera statis membuka pelacakan subjek otomatis.
7. **Letakkan produk di tengah-atas frame**, bukan di sepertiga bawah — area bawah habis
   dipakai kartu produk Shopee.

---

## 14. Peta script

| File | Fungsi |
|---|---|
| `transcribe` / `transcribe.py` | CLI faster-whisper, word-level timestamps |
| `scripts/analyze.py` | laporan jeda + blok konten + estimasi durasi |
| `scripts/build_edl.py` | titik potong + pemindahan hook → `edl.json` |
| `scripts/render_aroll.py` | gabung potongan, resolusi asli |
| `scripts/map_words.py` | petakan timestamp kata ke timeline hasil |
| `scripts/grid_sheet.py` | contact sheet + grid koordinat per blok |
| `scripts/zoom_plan.json` | **keputusan zoom** — edit di sini |
| `scripts/render_zoom.py` | render zoom (jalur bertahap) |
| `scripts/build_captions.py` | frasa caption + penanda kata kunci |
| `scripts/render_captions.py` | PNG caption + overlay + grade |
| `scripts/add_sfx.py` | mix sound design |
| `scripts/render_final.py` | **render final satu pass** |
| `scripts/check_frames.py` | sapuan safe zone seluruh durasi |
| `scripts/check_shopee.py` | mockup UI Shopee di atas frame |
| `scripts/track_subject.py` | background subtraction — *gagal, disimpan sebagai diagnostik* |
| `scripts/track_head.py` | deteksi skin-tone — *6/12 akurat, jangan diandalkan* |

---

## 15. Prinsip

1. **Ukur, jangan tebak.** Safe zone berasal dari screenshot nyata, bukan ingatan.
2. **Render dan lihat.** Angka dari detektor tidak berarti sampai frame-nya dilihat.
3. **Perbesar sebelum menyimpulkan.** Thumbnail kecil menyesatkan.
4. **Jangan diam-diam ganti pendekatan.** Kalau sesuatu gagal, jelaskan kenapa, lalu lanjut.
5. **Jangan mengarang klaim.** Tidak disebut talent = tidak muncul di layar.
6. **Berhenti di titik yang disepakati.** Langkah 2 dan 5 butuh keputusan klien.
7. **Batasan sumber dilaporkan, bukan disembunyikan.**

---

*v1 — 19 November 2026. Diuji pada `Mentah1.MOV` (59.24s → 52.93s, 14 segmen, 10 titik zoom, 40 caption).*
