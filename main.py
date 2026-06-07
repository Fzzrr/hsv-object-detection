"""
Object Detection & Manipulation using HSV Color Range  (versi general)
======================================================================
Mata Kuliah : Pengolahan Analisis Citra Digital (PACD)

Generalisasi dari recipe "ikan oranye": bekerja untuk objek warna APA PUN,
bukan hanya ikan. Program otomatis mendeteksi WARNA DOMINAN pada gambar
(dari beberapa rentang warna HSV yang umum), lalu:

  1. membuat mask objek berwarna tsb (cv2.inRange),
  2. mengiris (slice) objek dari latar,
  3. mengubah warna objek (geser channel Hue),
  4. membuat objek "transparan"/hilang:
       - jika --bg diberikan : tukar area objek dengan citra latar (cara recipe),
       - jika tidak          : pakai cv2.inpaint (objek dihapus dari piksel sekitar).

Cara menjalankan:
    python main.py                                  # default images/fish.png
    python main.py --image images/foto.jpg
    python main.py --image images/fish.png --bg images/fish_bg.png
    python main.py --image images/foto.jpg --save   # simpan hasil ke folder out/
"""

import os
import argparse

import cv2
import numpy as np
import matplotlib.pylab as plt


# ─────────────────────────────────────────────────────────────────────────────
# Rentang warna HSV (OpenCV: H 0-179, S/V 0-255)
# Merah melingkar di spektrum Hue -> butuh 2 range.
# ─────────────────────────────────────────────────────────────────────────────
# Catatan: ambang Saturation/Value sengaja dibuat moderat (S>=80, V>=50) agar
# objek pada FOTO NYATA (yang warnanya tidak setajam ilustrasi) tetap terdeteksi.
# Naikkan batas bawah S bila latar/kulit ikut tertangkap; turunkan bila objek
# berwarna pudar tidak terdeteksi.
COLOR_RANGES = {
    "Merah":  {"multi": True,
               "lower": [(0, 90, 50), (160, 90, 50)],
               "upper": [(10, 255, 255), (179, 255, 255)]},
    "Oranye": {"multi": False, "lower": (10, 90, 50),  "upper": (22, 255, 255)},
    "Kuning": {"multi": False, "lower": (22, 80, 50),  "upper": (33, 255, 255)},
    "Hijau":  {"multi": False, "lower": (33, 60, 40),  "upper": (85, 255, 255)},
    "Cyan":   {"multi": False, "lower": (85, 60, 40),  "upper": (100, 255, 255)},
    "Biru":   {"multi": False, "lower": (100, 70, 40), "upper": (130, 255, 255)},
    "Ungu":   {"multi": False, "lower": (130, 60, 40), "upper": (160, 255, 255)},
}

HUE_SHIFT = 20  # pergeseran Hue saat me-recolor objek


# ─────────────────────────────────────────────────────────────────────────────
# Pemrosesan inti
# ─────────────────────────────────────────────────────────────────────────────
def build_mask(hsv, color_name):
    """Buat binary mask untuk satu warna (gabung 2 range bila perlu)."""
    cfg = COLOR_RANGES[color_name]
    if cfg["multi"]:
        m1 = cv2.inRange(hsv, cfg["lower"][0], cfg["upper"][0])
        m2 = cv2.inRange(hsv, cfg["lower"][1], cfg["upper"][1])
        return cv2.bitwise_or(m1, m2)
    return cv2.inRange(hsv, cfg["lower"], cfg["upper"])


def clean_mask(mask):
    """
    Bersihkan noise: opening ringan (buang bintik) lalu closing lebih kuat
    (tutup lubang/sambung pola tipis seperti kotak-kotak kemeja).
    """
    kernel  = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    opened  = cv2.morphologyEx(mask,   cv2.MORPH_OPEN,  kernel, iterations=1)
    return cv2.morphologyEx(opened, cv2.MORPH_CLOSE, kernel, iterations=3)


def detect_color(hsv):
    """Pilih warna dengan luas mask terbesar -> 'warna dominan' gambar."""
    best, best_area = None, -1
    for name in COLOR_RANGES:
        area = int(cv2.countNonZero(clean_mask(build_mask(hsv, name))))
        if area > best_area:
            best, best_area = name, area
    return best, best_area


def build_dark_mask(hsv, vthresh):
    """
    Mask objek GELAP (siluet): piksel dengan Value < ambang.
    Berguna untuk objek hitam/backlit yang tidak punya warna (hue) untuk
    dideteksi, mis. siluet orang di depan langit terang.
    """
    return (hsv[..., 2] < vthresh).astype(np.uint8) * 255


def slice_object(img, imask):
    """Iris objek memakai mask (latar jadi hitam)."""
    out = np.zeros_like(img, np.uint8)
    out[imask] = img[imask]
    return out


def recolor_object(img, hsv, imask, hue_shift=HUE_SHIFT):
    """Geser Hue objek (mod 180 agar tidak overflow), warna lain tetap."""
    hsv = hsv.copy()
    hsv[..., 0] = (hsv[..., 0].astype(np.int16) + hue_shift) % 180
    recolored = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)
    out = img.copy()
    out[imask] = recolored[imask]
    return out


def fill_object(img, imask, color_bgr):
    """
    Isi area objek dengan warna solid. Dipakai untuk objek GELAP/siluet:
    menggeser Hue tidak terlihat pada piksel hitam (saturasi ~0), jadi cara
    yang benar untuk 'mengubah warna' siluet adalah menimpa dengan warna solid.
    """
    out = img.copy()
    out[imask] = color_bgr
    return out


def remove_object(img, imask, bg=None):
    """
    Hilangkan objek:
      - bg ada  : tukar area objek dengan latar (cara recipe asli),
      - bg None : cv2.inpaint (rekonstruksi dari piksel sekitar).
    """
    m = imask.astype(np.uint8)
    if bg is not None:
        notm   = np.bitwise_not(imask).astype(np.uint8)
        bckobj = cv2.bitwise_and(bg,  bg,  mask=m)
        noobj  = cv2.bitwise_and(img, img, mask=notm)
        return noobj + bckobj
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    m_dil  = cv2.dilate(m * 255, kernel, iterations=2)
    return cv2.inpaint(img, m_dil, 3, cv2.INPAINT_TELEA)


# ─────────────────────────────────────────────────────────────────────────────
# I/O & tampilan
# ─────────────────────────────────────────────────────────────────────────────
def load_image(path):
    if not os.path.exists(path):
        raise FileNotFoundError(f"Berkas tidak ditemukan: {path}")
    img = cv2.imread(path)
    if img is None:
        raise ValueError(f"Gagal membaca citra: {path}")
    return img


def show_results(panels, suptitle, save_dir=None):
    """Tampilkan (dan opsional simpan) panel hasil. panels = [(judul, bgr_or_gray)]."""
    plt.figure(figsize=(14, 8))
    plt.suptitle(suptitle, fontsize=14)
    for i, (title, im) in enumerate(panels, start=1):
        plt.subplot(2, 3, i)
        if im.ndim == 2:
            plt.imshow(im, cmap="gray")
        else:
            plt.imshow(cv2.cvtColor(im, cv2.COLOR_BGR2RGB))
        plt.title(title)
        plt.axis("off")
    plt.tight_layout()

    if save_dir:
        os.makedirs(save_dir, exist_ok=True)
        for title, im in panels:
            fname = title.lower().replace(" ", "_").replace("/", "-") + ".png"
            cv2.imwrite(os.path.join(save_dir, fname), im)
        print(f"[INFO] Hasil disimpan ke folder: {save_dir}/")
    plt.show()


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────
def parse_args():
    ap = argparse.ArgumentParser(
        description="Deteksi & manipulasi objek berdasarkan warna dominan (HSV).")
    ap.add_argument("--image", default="image.png",
                    help="berkas citra input (default: image.png)")
    ap.add_argument("--target", choices=["color", "dark"], default="color",
                    help="objek target: 'color' = warna dominan (default), "
                         "'dark' = siluet/objek gelap (deteksi via Value rendah)")
    ap.add_argument("--dark-thresh", type=int, default=50,
                    help="ambang Value untuk mode dark; piksel V<nilai ini "
                         "dianggap objek (default 50)")
    ap.add_argument("--fill", default="255,130,0",
                    help="warna isi 'B,G,R' untuk recolor mode dark "
                         "(default '255,130,0' = biru)")
    ap.add_argument("--bg", default=None,
                    help="citra latar untuk efek transparan (opsional; "
                         "tanpa ini dipakai inpainting)")
    ap.add_argument("--hue-shift", type=int, default=HUE_SHIFT,
                    help=f"besar pergeseran Hue saat recolor mode color "
                         f"(default {HUE_SHIFT})")
    ap.add_argument("--save", action="store_true",
                    help="simpan tiap panel hasil ke folder out/")
    return ap.parse_args()


def main():
    args = parse_args()

    img = load_image(args.image)
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    # ── Tentukan mask objek sesuai mode target ───────────────────────────────
    if args.target == "dark":
        target_label = f"Siluet (V<{args.dark_thresh})"
        mask = clean_mask(build_dark_mask(hsv, args.dark_thresh))
        print(f"[INFO] Mode siluet (gelap), ambang V<{args.dark_thresh}  "
              f"({int(cv2.countNonZero(mask)):,} px)")
    else:
        color_name, area = detect_color(hsv)
        target_label = f"Warna {color_name}"
        mask = clean_mask(build_mask(hsv, color_name))
        print(f"[INFO] Warna dominan terdeteksi: {color_name}  ({area:,} px)")

    imask = mask > 0

    # ── Latar untuk efek transparan (opsional) ───────────────────────────────
    bg = None
    if args.bg:
        bg = load_image(args.bg)
        if bg.shape != img.shape:
            bg = cv2.resize(bg, (img.shape[1], img.shape[0]))

    # ── Pipeline ─────────────────────────────────────────────────────────────
    sliced  = slice_object(img, imask)
    removed = remove_object(img, imask, bg)

    if args.target == "dark":
        fill = tuple(int(v) for v in args.fill.split(","))
        recolored      = fill_object(img, imask, fill)
        recolor_title  = f"Recolor (isi solid {args.fill})"
    else:
        recolored      = recolor_object(img, hsv, imask, args.hue_shift)
        recolor_title  = f"Recolor (+{args.hue_shift} Hue)"

    mode = "tukar latar" if bg is not None else "inpaint"
    panels = [
        ("Input",                      img),
        (f"Mask - {target_label}",     mask),
        ("Objek diiris",               sliced),
        (recolor_title,                recolored),
        (f"Objek transparan ({mode})", removed),
    ]
    show_results(panels, f"Manipulasi HSV - target: {target_label}",
                 save_dir="out" if args.save else None)


if __name__ == "__main__":
    main()
