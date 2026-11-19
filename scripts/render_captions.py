#!/usr/bin/env python3
"""Render caption jadi PNG transparan, lalu tempel ke video + warm color grade.

Gaya: Inter Black putih + outline hitam, kata kunci emas #ffd23f.
Posisi tengah-bawah di dalam safe zone (atas 220, bawah 1470, sisi 35).
"""
import json, os, subprocess, sys, glob
from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1920
# Safe zone SHOPEE VIDEO (paling ketat; aman juga utk TikTok/Reels).
# Diukur dari screenshot 1206x2622, video cover-fit -> koordinat 1080x1920:
#   kartu produk mulai y=1384 | kolom ikon kanan x>=852 | sisi kepotong 52px
SAFE_T, SAFE_B, SAFE_X = 220, 1384, 70
BAND_BOT = 1355           # baris caption terbawah - DI ATAS kartu produk
ICON_X = 852              # kolom aksi kanan, teks tidak boleh melewatinya
CENTER_X = (SAFE_X + ICON_X) // 2      # 461 - digeser kiri supaya bebas ikon
GOLD, WHITE, OUTL = "#ffd23f", "#ffffff", "#000000"
FONT = "/usr/share/fonts/opentype/inter/Inter-Black.otf"
EMOJI_F = "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf"
CAP_SZ, HOOK_SZ, STROKE = 58, 86, 7
MAXW = ICON_X - SAFE_X - 20          # 762
D = "work/cap"

data = json.load(open("work/captions.json"))
os.makedirs(D, exist_ok=True)
for f in glob.glob(f"{D}/*.png"):
    os.remove(f)
fnt = ImageFont.truetype(FONT, CAP_SZ)
fnt_h = ImageFont.truetype(FONT, HOOK_SZ)
try:
    femo = ImageFont.truetype(EMOJI_F, 109)
except Exception:
    femo = None


def emoji_img(ch, px):
    if not femo:
        return None
    tmp = Image.new("RGBA", (160, 160), (0, 0, 0, 0))
    ImageDraw.Draw(tmp).text((8, 8), ch, font=femo, embedded_color=True)
    bb = tmp.getbbox()
    if not bb:
        return None
    tmp = tmp.crop(bb)
    return tmp.resize((max(1, round(tmp.width * px / tmp.height)), px), Image.LANCZOS)


def layout(tokens, font, maxw):
    """tokens: [(teks, warna)|('<emoji>', ch)] -> baris-baris terbungkus"""
    d = ImageDraw.Draw(Image.new("RGBA", (10, 10)))
    sp = d.textlength(" ", font=font)
    lines, cur, cw = [], [], 0
    for tok in tokens:
        w = (font.size * 1.15) if tok[0] == "<emoji>" else d.textlength(tok[0], font=font)
        if cur and cw + sp + w > maxw:
            lines.append((cur, cw)); cur, cw = [], 0
        cw += (sp if cur else 0) + w
        cur.append((tok, w))
    if cur:
        lines.append((cur, cw))
    return lines, sp


def draw_block(tokens, font, bottom_y, size):
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    lines, sp = layout(tokens, font, MAXW)
    lh = round(size * 1.18)
    y = bottom_y - len(lines) * lh
    for toks, cw in lines:
        x = CENTER_X - cw / 2
        for (tok, tw) in toks:
            if tok[0] == "<emoji>":
                em = emoji_img(tok[1], round(size * 0.95))
                if em:
                    im.alpha_composite(em, (round(x), round(y + size * 0.1)))
            else:
                d.text((x, y), tok[0], font=font, fill=tok[1],
                       stroke_width=STROKE, stroke_fill=OUTL)
            x += tw + sp
        y += lh
    return im


items = []
# HOOK - teks besar
hk = data["hook"]
toks = []
for ln in hk["lines"]:
    toks += [(w, GOLD if ln["key"] else WHITE) for w in ln["t"].split()]
draw_block(toks, fnt_h, 1300, HOOK_SZ).save(f"{D}/hook.png")
items.append((f"{D}/hook.png", hk["start"], hk["end"]))

for i, c in enumerate(data["captions"]):
    toks = [(w["t"], GOLD if w["key"] else WHITE) for w in c["words"]]
    if c.get("emoji"):
        toks.append(("<emoji>", c["emoji"]))
    p = f"{D}/c{i:03d}.png"
    draw_block(toks, fnt, BAND_BOT, CAP_SZ).save(p)
    items.append((p, c["start"], c["end"]))

# ---- kartu CTA penutup (3.3s terakhir) ----
OUTRO_T = 49.58
cta = Image.new("RGBA", (W, H), (0, 0, 0, 0))
dc = ImageDraw.Draw(cta)
f_cta = ImageFont.truetype(FONT, 52)
label = "CHECK OUT SEKARANG"
tw = dc.textlength(label, font=f_cta)
em = emoji_img("\U0001F6D2", 50)
gap, ew = 18, (em.width if em else 0)
total = tw + gap + ew
pad_x, pad_y, top = 40, 24, 1120
box = [CENTER_X - total / 2 - pad_x, top, CENTER_X + total / 2 + pad_x, top + 52 + 2 * pad_y]
dc.rounded_rectangle(box, radius=52, fill=(16, 16, 18, 232), outline=(255, 210, 63, 255), width=4)
x0 = CENTER_X - total / 2
dc.text((x0, top + pad_y - 4), label, font=f_cta, fill=GOLD)
if em:
    cta.alpha_composite(em, (round(x0 + tw + gap), round(top + pad_y)))
cta.save(f"{D}/outro.png")
items.append((f"{D}/outro.png", OUTRO_T, 99))

print(f"PNG caption: {len(items)} (termasuk hook + kartu CTA)")

# ---- susun perintah ffmpeg: grade + overlay ----
SRC = sys.argv[1] if len(sys.argv) > 1 else "work/zoomed.mp4"
OUT = sys.argv[2] if len(sys.argv) > 2 else "work/styled.mp4"
GRADE = ("eq=saturation=1.12:contrast=1.06:brightness=0.012,"
         "colorbalance=rs=0.055:gs=0.012:bs=-0.05:rm=0.03:bm=-0.025")
cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-stats", "-i", SRC]
for p, _, _ in items:
    cmd += ["-i", p]
fc = [f"[0:v]{GRADE}[bg]"]
prev = "bg"
for n, (p, s, e) in enumerate(items, start=1):
    lbl = f"v{n}"
    fc.append(f"[{prev}][{n}:v]overlay=0:0:enable='between(t,{s},{e})'[{lbl}]")
    prev = lbl
cmd += ["-filter_complex", ";".join(fc), "-map", f"[{prev}]", "-map", "0:a",
        "-c:v", "libx264", "-crf", "17", "-preset", "medium", "-profile:v", "high",
        "-pix_fmt", "yuv420p", "-r", "30", "-fps_mode", "cfr",
        "-c:a", "copy", "-movflags", "+faststart", OUT, "-y"]
print(f"overlay: {len(items)}  ->  {OUT}")
sys.exit(subprocess.run(cmd).returncode)
