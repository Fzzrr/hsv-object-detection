"""
Object Detection using Color in HSV — Streamlit App
====================================================
Berdasarkan resep "Object detection using color in HSV" (OpenCV-Python).

Fitur:
- Upload gambar apa saja (jpg/png/webp/bmp).
- Pilih warna yang ingin dideteksi secara BEBAS, lewat 2 cara:
    1. Color Picker (klik warna -> rentang HSV dihitung otomatis + toleransi)
    2. Slider HSV manual (lower & upper bound, seperti cv2.inRange)
- Lihat hasil: Original, Mask, Objek Saja, Ubah Warna Objek, Objek Transparan.
- Ubah warna objek dengan: geser Hue ATAU ganti ke warna pilihan sendiri.
- Unduh tiap hasil sebagai PNG.

Cara menjalankan:
    pip install streamlit opencv-python-headless numpy pillow
    streamlit run app.py
"""

import io

import cv2
import numpy as np
import streamlit as st
from PIL import Image

# ----------------------------------------------------------------------------
# Konfigurasi halaman
# ----------------------------------------------------------------------------
st.set_page_config(
    page_title="Deteksi Objek Berdasarkan Warna (HSV)",
    page_icon="🎨",
    layout="wide",
)

st.title("🎨 Deteksi Objek Berdasarkan Warna di Ruang HSV")
st.caption(
    "Upload gambar apa saja, pilih warna yang ingin dideteksi, lalu ekstrak, "
    "ubah warnanya, atau buat objek menjadi transparan — semua di ruang warna HSV."
)


# ----------------------------------------------------------------------------
# Fungsi bantu
# ----------------------------------------------------------------------------
def load_image(uploaded_file) -> np.ndarray:
    """Baca file yang diupload menjadi array RGB (uint8)."""
    image = Image.open(uploaded_file).convert("RGB")
    return np.array(image)  # RGB, HxWx3


def hex_to_rgb(hex_color: str) -> tuple:
    """'#rrggbb' -> (r, g, b)."""
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))


def rgb_to_hsv_single(rgb: tuple) -> np.ndarray:
    """Konversi 1 warna RGB ke HSV (skala OpenCV: H 0-179, S/V 0-255)."""
    px = np.uint8([[list(rgb)]])  # 1x1x3
    hsv = cv2.cvtColor(px, cv2.COLOR_RGB2HSV)
    return hsv[0, 0]  # [H, S, V]


def build_range_from_color(rgb, h_tol, s_tol, v_tol):
    """Bangun lower & upper HSV dari sebuah warna + toleransi (mirip resep)."""
    h, s, v = [int(x) for x in rgb_to_hsv_single(rgb)]
    lower = np.array(
        [max(h - h_tol, 0), max(s - s_tol, 0), max(v - v_tol, 0)], dtype=np.uint8
    )
    upper = np.array(
        [min(h + h_tol, 179), min(s + s_tol, 255), min(v + v_tol, 255)],
        dtype=np.uint8,
    )
    return lower, upper


def make_mask(rgb_img, lower, upper):
    """cv2.inRange di ruang HSV -> mask biner."""
    hsv = cv2.cvtColor(rgb_img, cv2.COLOR_RGB2HSV)
    mask = cv2.inRange(hsv, lower, upper)
    return mask  # 0 atau 255


def slice_object(rgb_img, mask):
    """Ambil hanya objek (langkah 'Slice using the mask' di resep)."""
    imask = mask > 0
    obj = np.zeros_like(rgb_img, np.uint8)
    obj[imask] = rgb_img[imask]
    return obj


def shift_hue(rgb_img, mask, hue_delta):
    """Ubah warna objek dengan menggeser channel Hue saja (seperti resep)."""
    imask = mask > 0
    hsv = cv2.cvtColor(rgb_img, cv2.COLOR_RGB2HSV).astype(np.int16)
    hsv[..., 0] = (hsv[..., 0] + hue_delta) % 180  # wrap di 0-179
    hsv = hsv.astype(np.uint8)
    recolored = cv2.cvtColor(hsv, cv2.COLOR_HSV2RGB)
    out = rgb_img.copy()
    out[imask] = recolored[imask]
    return out


def replace_color(rgb_img, mask, target_rgb, keep_shading=True):
    """Ganti warna objek ke warna pilihan user."""
    imask = mask > 0
    out = rgb_img.copy()
    if keep_shading:
        # Pertahankan gelap-terang objek: pakai Hue & Sat target, tapi Value asli.
        hsv = cv2.cvtColor(rgb_img, cv2.COLOR_RGB2HSV)
        t_h, t_s, _ = rgb_to_hsv_single(target_rgb)
        new_hsv = hsv.copy()
        new_hsv[..., 0] = t_h
        new_hsv[..., 1] = t_s
        recolored = cv2.cvtColor(new_hsv, cv2.COLOR_HSV2RGB)
        out[imask] = recolored[imask]
    else:
        out[imask] = np.array(target_rgb, dtype=np.uint8)
    return out


def make_transparent(rgb_img, mask):
    """Jadikan objek transparan -> RGBA (alpha=0 pada area objek)."""
    imask = mask > 0
    rgba = np.dstack([rgb_img, np.full(rgb_img.shape[:2], 255, np.uint8)])
    rgba[imask, 3] = 0  # objek menjadi transparan
    return rgba


def cloak_with_background(rgb_img, mask, bg_img):
    """Versi 'cloaking' seperti di buku: ganti objek dengan latar pilihan."""
    bg = cv2.resize(bg_img, (rgb_img.shape[1], rgb_img.shape[0]))
    imask = mask > 0
    out = rgb_img.copy()
    out[imask] = bg[imask]
    return out


def to_png_bytes(arr: np.ndarray) -> bytes:
    """Array (RGB/RGBA/gray) -> bytes PNG untuk tombol unduh."""
    if arr.ndim == 2:
        img = Image.fromarray(arr, mode="L")
    elif arr.shape[2] == 4:
        img = Image.fromarray(arr, mode="RGBA")
    else:
        img = Image.fromarray(arr, mode="RGB")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def download_button(label, arr, filename):
    st.download_button(label, data=to_png_bytes(arr), file_name=filename, mime="image/png")


# ----------------------------------------------------------------------------
# Sidebar — input & kontrol
# ----------------------------------------------------------------------------
with st.sidebar:
    st.header("1. Upload Gambar")
    uploaded = st.file_uploader(
        "Pilih gambar", type=["jpg", "jpeg", "png", "webp", "bmp"]
    )

    st.divider()
    st.header("2. Pilih Warna Target")
    mode = st.radio(
        "Cara memilih warna yang dideteksi:",
        ["Color Picker (otomatis)", "Slider HSV manual"],
    )

    if mode == "Color Picker (otomatis)":
        target_hex = st.color_picker("Warna yang ingin dideteksi", "#FF7A00")
        target_rgb = hex_to_rgb(target_hex)
        st.caption("Atur toleransi seberapa lebar rentang warna di sekitar pilihanmu:")
        h_tol = st.slider("Toleransi Hue (warna)", 1, 90, 15)
        s_tol = st.slider("Toleransi Saturation", 10, 255, 100)
        v_tol = st.slider("Toleransi Value (kecerahan)", 10, 255, 120)
        lower, upper = build_range_from_color(target_rgb, h_tol, s_tol, v_tol)
        st.info(f"Rentang HSV: lower={lower.tolist()}  upper={upper.tolist()}")
    else:
        st.caption("Format OpenCV: H 0–179, S 0–255, V 0–255.")
        h_lo, h_hi = st.slider("Hue (H)", 0, 179, (5, 25))
        s_lo, s_hi = st.slider("Saturation (S)", 0, 255, (75, 255))
        v_lo, v_hi = st.slider("Value (V)", 0, 255, (25, 255))
        lower = np.array([h_lo, s_lo, v_lo], dtype=np.uint8)
        upper = np.array([h_hi, s_hi, v_hi], dtype=np.uint8)

    st.divider()
    st.header("3. Ubah Warna Objek")
    recolor_mode = st.radio(
        "Metode pewarnaan ulang:",
        ["Geser Hue", "Ganti ke warna pilihan"],
    )
    if recolor_mode == "Geser Hue":
        hue_delta = st.slider("Pergeseran Hue (+/-)", -90, 90, 20)
    else:
        new_hex = st.color_picker("Warna baru objek", "#FFE600")
        new_rgb = hex_to_rgb(new_hex)
        keep_shading = st.checkbox("Pertahankan gelap/terang objek", value=True)

    st.divider()
    st.header("4. (Opsional) Cloaking")
    st.caption(
        "Seperti di buku: ganti objek dengan gambar latar agar 'menghilang'. "
        "Upload latar dengan komposisi mirip background gambar utama."
    )
    bg_uploaded = st.file_uploader(
        "Gambar latar untuk cloaking", type=["jpg", "jpeg", "png", "webp", "bmp"],
        key="bg",
    )


# ----------------------------------------------------------------------------
# Proses utama
# ----------------------------------------------------------------------------
if uploaded is None:
    st.info("⬅️ Mulai dengan mengupload gambar di sidebar.")
    with st.expander("ℹ️ Tentang aplikasi ini & cara kerjanya"):
        st.markdown(
            """
Aplikasi ini menerapkan resep **deteksi objek berdasarkan warna di ruang HSV**:

1. **Konversi BGR/RGB → HSV.** HSV memisahkan *warna* (Hue) dari *kecerahan* (Value),
   sehingga deteksi warna lebih stabil daripada di ruang RGB.
2. **`cv2.inRange(hsv, lower, upper)`** membuat *mask* biner: piksel di dalam
   rentang warna menjadi putih, sisanya hitam.
3. **Slicing dengan mask** untuk mengambil hanya objek.
4. **Ubah warna** cukup dengan menggeser channel **Hue** saja (tanpa menyentuh
   Saturation/Value) lalu konversi balik ke RGB.
5. **Transparansi/cloaking** dengan mengganti area objek (alpha=0 atau ditimpa latar).
            """
        )
    st.stop()

rgb = load_image(uploaded)
mask = make_mask(rgb, lower, upper)
only_obj = slice_object(rgb, mask)

if recolor_mode == "Geser Hue":
    recolored = shift_hue(rgb, mask, hue_delta)
else:
    recolored = replace_color(rgb, mask, new_rgb, keep_shading)

transparent = make_transparent(rgb, mask)

# Statistik kecil
coverage = float((mask > 0).mean() * 100)
st.metric("Area terdeteksi", f"{coverage:.1f}% dari gambar")

# Tampilan hasil
col1, col2, col3 = st.columns(3)
with col1:
    st.subheader("Original")
    st.image(rgb, use_container_width=True)
    download_button("⬇️ Unduh", rgb, "original.png")
with col2:
    st.subheader("Mask")
    st.image(mask, use_container_width=True, clamp=True)
    download_button("⬇️ Unduh", mask, "mask.png")
with col3:
    st.subheader("Objek Saja")
    st.image(only_obj, use_container_width=True)
    download_button("⬇️ Unduh", only_obj, "only_object.png")

col4, col5, col6 = st.columns(3)
with col4:
    st.subheader("Warna Objek Diubah")
    st.image(recolored, use_container_width=True)
    download_button("⬇️ Unduh", recolored, "recolored.png")
with col5:
    st.subheader("Objek Transparan")
    st.image(transparent, use_container_width=True)
    download_button("⬇️ Unduh (PNG transparan)", transparent, "transparent.png")
with col6:
    st.subheader("Cloaking")
    if bg_uploaded is not None:
        bg = load_image(bg_uploaded)
        cloaked = cloak_with_background(rgb, mask, bg)
        st.image(cloaked, use_container_width=True)
        download_button("⬇️ Unduh", cloaked, "cloaked.png")
    else:
        st.caption("Upload gambar latar di sidebar (bagian 4) untuk fitur ini.")

with st.expander("🔧 Tips kalau deteksi belum pas"):
    st.markdown(
        """
- **Objek tidak tertangkap penuh?** Perbesar toleransi *Saturation* & *Value*,
  atau lebarkan rentang *Hue*.
- **Terlalu banyak area ikut tertangkap?** Persempit toleransi, terutama *Hue*.
- **Warna merah** berada di dua ujung lingkaran Hue (mendekati 0 dan 179). Untuk
  merah, gunakan mode slider manual dan coba dua rentang, atau pilih warna merah
  yang condong oranye/magenta lewat color picker.
- Mode **Color Picker** menghitung rentang otomatis di sekitar warna pilihanmu —
  paling mudah untuk eksplorasi cepat.
        """
    )