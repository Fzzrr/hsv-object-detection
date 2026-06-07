"""
Aplikasi Web (Streamlit) - Deteksi & Manipulasi Objek berbasis Warna HSV
========================================================================
Mata Kuliah : Pengolahan Analisis Citra Digital (PACD)

Antarmuka web untuk recipe HSV pada `main.py`. Dosen/penguji cukup membuka
URL aplikasi (mis. di Streamlit Community Cloud) tanpa perlu meng-clone project
atau memasang dependensi secara lokal.

Logika inti TIDAK diduplikasi - app ini meng-import fungsi langsung dari
`main.py` (build_mask, detect_color, slice_object, recolor_object, dll).

Menjalankan secara lokal:
    streamlit run app.py
"""

import os

import cv2
import numpy as np
import streamlit as st

# Pakai ulang seluruh logika pemrosesan dari main.py (single source of truth)
import main as core

# ─────────────────────────────────────────────────────────────────────────────
# Util tampilan
# ─────────────────────────────────────────────────────────────────────────────
def to_rgb(img):
    """BGR/abu-abu -> RGB untuk st.image (Matplotlib/Streamlit pakai RGB)."""
    if img.ndim == 2:
        return cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)
    return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)


def png_bytes(img):
    """Encode citra BGR/abu-abu menjadi byte PNG untuk tombol download."""
    ok, buf = cv2.imencode(".png", img)
    return buf.tobytes() if ok else b""


def read_upload(uploaded):
    """Baca file yang di-upload Streamlit menjadi citra BGR (OpenCV)."""
    data = np.frombuffer(uploaded.getvalue(), np.uint8)
    return cv2.imdecode(data, cv2.IMREAD_COLOR)


def hex_to_bgr(hex_color):
    """'#rrggbb' -> tuple BGR untuk OpenCV."""
    h = hex_color.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return (b, g, r)


# ─────────────────────────────────────────────────────────────────────────────
# Halaman
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(page_title="Deteksi Objek HSV", page_icon="🎨", layout="wide")

st.title("🎨 Deteksi & Manipulasi Objek berbasis Warna HSV")
st.caption(
    "Pengolahan Analisis Citra Digital (PACD) — deteksi objek di ruang warna "
    "HSV, lalu iris, ubah warna, dan buat transparan. Mendukung objek berwarna "
    "maupun siluet/objek gelap."
)

# ── Sidebar: input & parameter ───────────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ Pengaturan")

    uploaded = st.file_uploader(
        "Unggah gambar", type=["png", "jpg", "jpeg", "bmp", "webp"]
    )
    use_example = st.checkbox(
        "Pakai contoh bawaan (image.png)", value=uploaded is None
    )

    st.divider()

    mode_label = st.radio(
        "Mode target objek",
        ["Warna dominan", "Siluet / objek gelap"],
        help="'Warna dominan' mendeteksi via Hue (objek berwarna). "
             "'Siluet' mendeteksi via kecerahan rendah (objek hitam/backlit).",
    )
    is_dark = mode_label.startswith("Siluet")

    if is_dark:
        dark_thresh = st.slider(
            "Ambang gelap (V <)", 10, 120, 35,
            help="Piksel dengan Value di bawah nilai ini dianggap objek. "
                 "Naikkan bila bagian objek terlewat; turunkan bila bintik "
                 "latar ikut tertangkap.",
        )
        fill_hex = st.color_picker(
            "Warna isi siluet (recolor)", "#0082FF",
            help="Untuk objek hitam, recolor dilakukan dengan mengisi warna "
                 "solid (menggeser Hue tak terlihat pada piksel gelap).",
        )
    else:
        hue_shift = st.slider(
            "Pergeseran Hue (recolor)", 0, 179, core.HUE_SHIFT,
            help="Besar pergeseran channel Hue saat mengubah warna objek.",
        )

    st.divider()
    st.subheader("Efek transparan")
    bg_upload = st.file_uploader(
        "Citra latar (opsional, mode --bg)",
        type=["png", "jpg", "jpeg", "bmp", "webp"],
        help="Bila diisi, area objek ditukar dengan latar ini (cara recipe "
             "asli). Bila kosong, objek dihapus dengan inpainting.",
    )

# ── Ambil citra input ────────────────────────────────────────────────────────
img = None
if uploaded is not None:
    img = read_upload(uploaded)
elif use_example and os.path.exists("image.png"):
    img = cv2.imread("image.png")

if img is None:
    st.info(
        "⬅️ Unggah gambar di panel kiri, atau centang **Pakai contoh bawaan** "
        "untuk memakai `image.png`."
    )
    st.stop()

# ── Pipeline (mengikuti main.main) ───────────────────────────────────────────
hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

if is_dark:
    target_label = f"Siluet (V < {dark_thresh})"
    mask = core.clean_mask(core.build_dark_mask(hsv, dark_thresh))
    info = f"Mode siluet (gelap), ambang V < {dark_thresh} — " \
           f"{int(cv2.countNonZero(mask)):,} px objek"
else:
    color_name, area = core.detect_color(hsv)
    target_label = f"Warna {color_name}"
    mask = core.clean_mask(core.build_mask(hsv, color_name))
    info = f"Warna dominan terdeteksi: **{color_name}** — {area:,} px"
    # Area sangat kecil -> kemungkinan objeknya siluet/gelap, bukan berwarna.
    if area < 0.01 * img.shape[0] * img.shape[1]:
        st.warning(
            "Objek berwarna nyaris tak terdeteksi. Jika gambarmu berupa "
            "**siluet/objek gelap** (mis. contoh `image.png`), ganti mode ke "
            "**Siluet / objek gelap** di panel kiri."
        )

imask = mask > 0

bg = None
if bg_upload is not None:
    bg = read_upload(bg_upload)
    if bg.shape != img.shape:
        bg = cv2.resize(bg, (img.shape[1], img.shape[0]))

sliced = core.slice_object(img, imask)
removed = core.remove_object(img, imask, bg)

if is_dark:
    recolored = core.fill_object(img, imask, hex_to_bgr(fill_hex))
    recolor_title = "Recolor (isi warna solid)"
else:
    recolored = core.recolor_object(img, hsv, imask, hue_shift)
    recolor_title = f"Recolor (+{hue_shift} Hue)"

mode_transp = "tukar latar" if bg is not None else "inpaint"

# ── Tampilan hasil ───────────────────────────────────────────────────────────
st.success(f"🎯 {info}")

panels = [
    ("Input", img),
    (f"Mask — {target_label}", mask),
    ("Objek diiris", sliced),
    (recolor_title, recolored),
    (f"Objek transparan ({mode_transp})", removed),
]

cols = st.columns(3)
for i, (title, im) in enumerate(panels):
    with cols[i % 3]:
        st.image(to_rgb(im), caption=title, width="stretch")
        st.download_button(
            f"⬇️ Unduh: {title}",
            data=png_bytes(im),
            file_name=title.lower().replace(" ", "_").replace("/", "-")
            .replace("—", "-") + ".png",
            mime="image/png",
            key=f"dl_{i}",
        )

with st.expander("ℹ️ Cara kerja singkat"):
    st.markdown(
        """
1. **BGR → HSV** — citra dikonversi ke ruang warna HSV.
2. **Deteksi objek** — mode *warna* memilih warna dominan via Hue
   (`detect_color`); mode *siluet* menandai piksel ber-Value rendah
   (`build_dark_mask`).
3. **Masking + pembersihan** — `cv2.inRange` lalu morfologi *opening/closing*
   (`clean_mask`).
4. **Iris** objek dari latar (`slice_object`).
5. **Recolor** — geser Hue (`recolor_object`) untuk objek berwarna, atau isi
   warna solid (`fill_object`) untuk siluet.
6. **Transparan** — tukar dengan latar bila diberikan, selain itu `cv2.inpaint`
   (`remove_object`).

> Seluruh logika di atas diambil langsung dari `main.py`.
        """
    )
