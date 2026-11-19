---
name: edit-jualan
description: "Edit video jualan one-take jadi reel 9:16 siap posting untuk Shopee Video, TikTok, dan Reels. Selalu tanya gaya edit yang tersedia dulu sebelum mulai. Transkrip Indonesia dengan timestamp per kata, potong jeda dan take salah, pindahkan kalimat paling menjual jadi hook, punch-in halus di timeline gabungan, caption per frasa dengan kata kunci emas, sound design halus, dan cek tiap frame di dalam safe zone Shopee. Pakai saat diminta 'edit video ini', 'edit video jualan', 'jadiin reel', 'potong videonya', 'bikin konten dari footage ini', atau /edit-jualan."
---

# /edit-jualan

Footage mentah masuk, reel jualan siap posting keluar. Klien tidak pernah membuka editor:
mereka menilai preview di HP lalu memberi catatan; tiap revisi cuma render ulang ~4 menit.

**Panduan teknis lengkap ada di `panduan-editing-v1.md` di root project.** Baca itu sebelum
langkah 3 — semua angka di sana hasil uji, bukan tebakan. Skill ini mengatur alurnya;
panduan mengatur caranya.

---

## LANGKAH 0 — WAJIB: tanya gaya edit dulu

**Jangan unduh apa pun. Jangan jalankan ffprobe. Jangan buka file. Tanya dulu.**

Begitu user minta edit, langsung panggil `AskUserQuestion` dengan 3 pertanyaan ini
dalam satu kali panggil. Baru setelah dijawab, mulai kerja.

### Pertanyaan 1 — Gaya edit

| Gaya | Untuk | Caption | Zoom | SFX | Tempo |
|---|---|---|---|---|---|
| **A. Spek & Angka** *(default)* | Produk teknis, jelasin ukuran/kapasitas, edukasi | Inter Black 58px, putih + outline, **angka spek emas** | 1.0 / 1.25 / 1.5, punch saat sebut angka | 10 titik halus | Sedang, potong jeda > 0.30s |
| **B. Hard Sell** | Diskon, flash sale, urgency | 68px, ALL CAPS di kata kunci, emas lebih banyak | Lebih sering (tiap 3–4 detik), maks 1.5 | 15–18 titik, impact tiap angka | Cepat, potong jeda > 0.20s |
| **C. Soft / Cerita** | Brand story, testimoni, edukasi pelan | 52px, putih saja, emas jarang | 1.0 / 1.15 saja, transisi 0.8s | 3–4 titik | Santai, potong jeda > 0.45s |
| **D. Potong Bersih** | Upload cepat, atau klien mau lanjut edit sendiri | Polos putih + outline | Tidak ada | Tidak ada | Potong jeda > 0.30s, tanpa grade |
| **E. Utuh + Style** | Rekaman mau dipertahankan apa adanya, cuma dipercantik | Sama seperti A | Sama seperti A | Sama seperti A | **Nol potongan** — tidak ada frame yang dibuang |

### Pertanyaan 2 — Platform

- **Shopee Video** → safe zone paling ketat (kartu produk y=1384, kolom ikon x≥852, sisi kepotong 52px)
- **TikTok / Reels** → bawah 450px bersih (y < 1470), kolom kanan 100px
- **Semua platform** *(rekomendasi)* → pakai safe zone Shopee, aman di ketiganya

### Pertanyaan 3 — Durasi & potong konten

- **30–45 detik, boleh potong konten** — kalau terlalu panjang, buang bagian paling lemah
- **Pertahankan semua konten** — cuma potong jeda, durasi mengikuti
- **Durasi lain** — user sebutkan sendiri

Kalau user memilih **gaya E**, lewati pertanyaan ini — gaya E sudah berarti nol potongan.
Ganti dengan satu konfirmasi: durasi hasil akan **lebih panjang** dari aslinya
(asli + panjang hook yang digandakan, biasanya 2–3 detik).

Kalau user sudah menyebut jawabannya di pesan awal ("gaya hard sell dong, buat TikTok"),
jangan tanya ulang yang itu — tanya sisanya saja. Kalau semua sudah disebut, langsung jalan.

---

## LANGKAH 1 — Ambil & cek footage

Sumber bisa berupa folder Google Drive, path lokal, atau file yang di-drop user.

**Drive:** pakai `mcp__Google_Drive__search_files` dengan `'<folderId>' in ancestors` untuk
melihat isinya dulu (murah, metadata saja). Unduh dengan `gdown`, **jangan**
`download_file_content` — itu mengembalikan base64 dan membanjiri context.

```bash
gdown --folder "https://drive.google.com/drive/folders/<id>" -O ~/raw-footage
```

Kalau gagal karena akses: **jangan ulang-ulang**. Bilang ke user folder perlu diatur
"Siapa saja yang memiliki link", lalu berhenti.

**Cek tiap file:**

```bash
ffprobe -v error -select_streams v:0 \
  -show_entries stream=codec_name,width,height,r_frame_rate,bit_rate \
  -show_entries stream_side_data=rotation -of default=nw=1 <file>
```

Laporkan ringkasannya, dan **wajib sebut headroom zoom**:

- Video HP sering 1920×1080 + rotasi −90° → decoded 1080×1920
- Kalau decoded = 1080×1920, **tidak ada headroom** — tiap punch-in itu upscale.
  1.25× masih tajam, 1.5× mulai lembut. Sampaikan sebelum mulai, bukan setelah render.
- Kalau sumbernya 4K, batas ini tidak berlaku

**File asli hanya dibaca. Jangan diubah, jangan dihapus.**

---

## LANGKAH 2 — Transkrip Indonesia → BERHENTI, tunjukkan

```bash
ffmpeg -i <file> -vn -ac 1 -ar 16000 -c:a pcm_s16le work/audio.wav -y
./transcribe work/audio.wav --model large-v3 --lang id --formats srt,json,txt -o work
.venv/bin/python scripts/analyze.py work/audio.json
```

Laporkan ke user, dipecah per blok: **hook / penjelasan produk / harga-promo / penutup**.
Tandai juga:

- Filler (`eee`, `anu`)
- Kalimat yang diulang
- CTA dobel
- Kata dengan `prob < 0.6` — cek ulang, dan **tanya user** untuk nama toko/merek, jangan menebak
- **Kalau tidak ada harga di audio, bilang terus terang.** Tidak boleh bikin caption harga
  yang tidak diucapkan talent.

Lalu hitung durasi: potong jeda saja biasanya hanya hemat 10–12%. Kalau masih di atas target,
**sajikan opsi potong konten dengan angka** dan minta user memilih.

**BERHENTI DI SINI. Tunggu jawaban user sebelum lanjut.**

---

## LANGKAH 3 — TAHAP A: potong & gabung

### Gaya A / B / C / D — potong jeda

`scripts/build_edl.py` → `scripts/render_aroll.py`

Ambang sesuai gaya yang dipilih di Langkah 0 (`MIN_SIL`: A/D 0.30 · B 0.20 · C 0.45).
Parameter lain tetap: `KEEP_SIL` 0.10, `MARGIN` 0.06, `MIN_SAVE` 0.15, `MIN_KEEP` 0.45.

Gabungkan jadi **satu video utuh di resolusi asli** — tanpa zoom, tanpa resize turun.
Catat tiap titik sambungan di `edl.json`.

**Hook:** pindahkan kalimat paling menjual ke 3 detik pertama. *Pindah, bukan gandakan.*
Kalau ada kalimat yang diucapkan 2×, pindahkan instance pertama — yang kedua tetap di
tempatnya, jadi nol konten hilang.

### Gaya E — Utuh + Style (nol potongan)

**Lewati `build_edl.py` sepenuhnya.** Rekaman asli tidak disentuh: tidak ada jeda yang
dipangkas, tidak ada frame yang dibuang, urutan ucapan tidak diubah.

Yang dibuat cuma satu tambahan di depan — **hook digandakan, bukan dipindah:**

1. Pilih kalimat paling menjual dari transkrip (lihat Langkah 2)
2. **Salin** klip kalimat itu, beri ekor diam ~0.2 detik di belakangnya
3. Taruh salinannya di paling depan sebagai teaser
4. Sambungkan ke video asli dengan **crossfade 0.25 detik** + SFX `whoosh-short`
5. Video asli tetap diputar **utuh dari detik 0**, termasuk kalimat itu di tempat aslinya

Ekor diam di langkah 2 itu penting: crossfade harus jatuh di bagian senyap,
jangan sampai dua ucapan saling tumpang tindih.

```
[hook salinan + ekor] ──crossfade 0.25s── [VIDEO ASLI UTUH]
```

Durasi hasil = **durasi asli + panjang hook** (biasanya +2–3 detik). Sebutkan ini ke user.

Kalimat hook jadi terdengar 2×, dan itu memang disengaja — polanya sama seperti
teaser di awal reel. Normalisasi tetap jalan: 30fps CFR, resolusi asli.

### Verifikasi wajib (semua gaya)

```bash
.venv/bin/python scripts/map_words.py    # harus X/X kata, 0 hilang
./transcribe work/aroll.mp4 --model turbo --lang id -o work
```

Kalau ada kata hilang, konsonan kepotong → naikkan `MARGIN`.
Untuk gaya E, jumlah kata harus **lebih banyak** dari aslinya (karena hook digandakan) —
selisihnya persis sejumlah kata di kalimat hook.

---

## LANGKAH 4 — TAHAP B: zoom di timeline gabungan

`scripts/zoom_plan.json` → `scripts/render_zoom.py`

Animasikan di **timeline gabungan**, bukan per potongan.

- Metode: `scale(eval=frame)` lalu `crop` ukuran tetap. **Jangan `zoompan`** (bergetar).
  **Jangan `crop` dengan ukuran berubah** — `w`/`h` hanya dievaluasi sekali.
- Easing: ease-in-out cubic, bentuk **aditif** (bukan `if` bertingkat). Rumus di panduan §6.
- **Verifikasi numerik ekspresi di Python sebelum render panjang.**
- Transisi **mulai tepat di titik sambungan**, durasi sesuai gaya (A/B 0.5s · C 0.8s).
- Level dipertahankan sepanjang satu kalimat. Jangan ubah zoom di tengah kata.

> **Gaya E tidak punya titik sambungan** (selain crossfade hook di awal). Potongan biasanya
> menyembunyikan awal gerakan zoom; tanpa itu perpindahan lebih terasa. Taruh tiap
> perpindahan di **jeda napas antar kalimat** — ambil dari `silencedetect` atau dari
> celah antar kata di `words_aroll.json`, pilih jeda terpanjang di sekitar batas blok.
> Jangan pernah mulai gerakan saat talent sedang bicara.
- Saat talent menyebut detail (ukuran, bahan, motif), zoom ke bagian itu.
- **Kepala dan produk tetap di frame.**

### Menentukan window zoom

Jangan buang waktu di pelacakan otomatis. Panduan §7 mendokumentasikan 4 pendekatan
yang sudah gagal: background subtraction (gagal kalau kamera bergerak), deteksi skin-tone
(kolam/kayu oranye kebaca kulit), YuNet (proxy blokir), `headpos.py` (butuh cutout).

**Yang berhasil:** contact sheet bergrid (`scripts/grid_sheet.py`) → tetapkan `z`/`cx`/`cy`
per blok → **render crop-nya dan lihat hasilnya** → sapu seluruh durasi
(`scripts/check_frames.py`).

Kalau ragu soal framing, **perbesar frame-nya**. Thumbnail kecil menyesatkan.

Kalau talent keluar frame di sumber, tidak ada crop yang bisa menolong.
Turunkan zoom ke 1.0 di bagian itu dan **laporkan apa adanya**.

Resize ke 1080×1920 baru di tahap akhir, setelah zoom selesai.

---

## LANGKAH 5 — Caption, style, preview → BERHENTI, tunggu ACC

`scripts/build_captions.py` → `scripts/render_captions.py` → `scripts/add_sfx.py`

Nilai layout menyesuaikan platform dari Langkah 0. Untuk Shopee (dan "semua platform"):

```python
SAFE_T = 220 ; SAFE_X = 70 ; ICON_X = 852
BAND_BOT = 1355 ; CENTER_X = 461 ; MAXW = 762
```

Caption per frasa pendek: maks 4 kata / 22 karakter, pecah di akhir kalimat,
**jangan pisahkan angka dari satuannya** (`45 cm`), token diawali `-` digabung ke
token sebelumnya (`kolam-kolam`).

Putih + outline hitam; **kata kunci emas `#ffd23f`** — angka spesifikasi dan harga saja,
jangan semua. Emoji & SFX pop hanya di kata kunci, bukan tiap caption.
Warm color grade. Tanpa cutout kecuali user minta.

**Penutup 3–5 detik: CTA singkat + nama toko.** Kalau nama toko tidak jelas di audio,
tanya user — jangan karang.

Koreksi transkrip hanya untuk artefak jelas (`leleh`→`lele`). Logat dibiarkan.
**Jangan ubah makna ucapan, jangan tambah klaim yang tidak diucapkan talent.**

**Verifikasi sebelum lapor:**

```bash
.venv/bin/python scripts/check_shopee.py <video> work/cek.jpg "1.0,19.9,31.5,51.5"
.venv/bin/python scripts/check_frames.py <video> work/sweep.jpg 2.5
ffmpeg -i <video> -af volumedetect -f null - 2>&1 | grep max_volume   # jangan 0.0 dB
```

Render preview 540×960 ke `~/ekspor/preview.mp4`, salin juga ke `ekspor/` di project
supaya user bisa membukanya dari app. Kirim dengan `SendUserFile`.

Laporkan: **durasi sebelum/sesudah, apa yang dipotong, daftar waktu zoom.**

**BERHENTI DI SINI. Tunggu ACC user sebelum render final.**

---

## LANGKAH 6 — Render final

Setelah disetujui, render **satu pass dari `aroll.mp4`** (zoom + grade + caption sekaligus) —
2 generasi encoding, bukan 4.

```bash
.venv/bin/python scripts/render_final.py work/final_video.mp4 18
.venv/bin/python scripts/add_sfx.py work/final_video.mp4 ~/ekspor/final.mp4
```

1080×1920 · 30fps CFR · H.264 High 4.1 · CRF 18 preset slow · `+faststart` · AAC 192k.

**Cara user mengambil hasil** (tidak bisa dibuka langsung dari HP):

1. Kirim dengan `SendUserFile` — ini jalur utama
2. Connector Google Drive **batas ~3.1 MB per panggilan**, jadi file final 1080p
   hampir pasti tidak muat. Jangan janjikan upload Drive sebelum ukurannya dicek.
3. Simpan di `ekspor/` (sudah di-gitignore) dan sebutkan path lengkapnya

---

## Aturan

- **File asli hanya dibaca.** Jangan diubah, jangan dihapus.
- **Jangan ubah makna ucapan.** Jangan tambah klaim, harga, atau promo yang tidak disebut talent.
- **Semua script ditulis di `scripts/`** supaya revisi bisa diulang.
- **Kalau ada error, jelaskan singkat lalu cari solusi.** Jangan diam-diam ganti pendekatan.
- **Berhenti di Langkah 0, 2, dan 5.** Ketiganya butuh keputusan user.
- **Ukur, jangan tebak.** Safe zone dari screenshot nyata. Framing dari frame yang dirender.
- **Batasan sumber dilaporkan, bukan disembunyikan.**

## Revisi

Semua keputusan ada di file, jadi revisi tinggal ubah satu file lalu render ulang:

| Mau ubah | File |
|---|---|
| Timing / level zoom | `scripts/zoom_plan.json` |
| Teks, kata emas, emoji | `scripts/build_captions.py` |
| Titik potong | `scripts/build_edl.py` |
| SFX | `scripts/add_sfx.py` |
| Posisi caption vs UI platform | `scripts/render_captions.py` |
