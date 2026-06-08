import streamlit as st

from components import render_sidebar, result_panel
from processing import (
    cloak_with_background,
    make_mask,
    make_transparent,
    replace_color,
    shift_hue,
    slice_object,
)
from utils import load_image

st.set_page_config(
    page_title="Deteksi Objek Warna HSV",
    page_icon="🎨",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    "<style>.block-container { padding-top: 2rem; max-width: 1280px; }</style>",
    unsafe_allow_html=True,
)

st.title("Deteksi Objek Berdasarkan Warna — HSV")

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
ctx = render_sidebar()
uploaded       = ctx["uploaded"]
lower          = ctx["lower"]
upper          = ctx["upper"]
recolor_mode   = ctx["recolor_mode"]
recolor_params = ctx["recolor_params"]
bg_uploaded    = ctx["bg_uploaded"]

# ---------------------------------------------------------------------------
# Belum ada gambar
# ---------------------------------------------------------------------------
if uploaded is None:
    st.info("Upload Gambar Memulai Deteksi Objek Warna HSV")
    st.stop()

# ---------------------------------------------------------------------------
# Proses
# ---------------------------------------------------------------------------
rgb         = load_image(uploaded)
mask        = make_mask(rgb, lower, upper)
only_obj    = slice_object(rgb, mask)
transparent = make_transparent(rgb, mask)

if recolor_mode == "Geser Hue":
    recolored = shift_hue(rgb, mask, recolor_params["hue_delta"])
else:
    recolored = replace_color(
        rgb, mask, recolor_params["new_rgb"], recolor_params["keep_shading"]
    )

# ---------------------------------------------------------------------------
# Satu baris info — tidak perlu tiga metric card
# ---------------------------------------------------------------------------
h, w = mask.shape
coverage = float((mask > 0).mean() * 100)
st.caption(f"Terdeteksi {coverage:.1f}% area · {w} × {h} px")

# ---------------------------------------------------------------------------
# Hasil
# ---------------------------------------------------------------------------
col1, col2, col3 = st.columns(3)
with col1:
    result_panel("Original", rgb, "original.png")
with col2:
    result_panel("Mask", mask, "mask.png", clamp=True)
with col3:
    result_panel("Objek Saja", only_obj, "only_object.png")

st.write("")  # sedikit jarak antar baris

col4, col5, col6 = st.columns(3)
with col4:
    result_panel("Warna Diubah", recolored, "recolored.png")
with col5:
    result_panel("Transparan", transparent, "transparent.png")
with col6:
    if bg_uploaded is not None:
        bg = load_image(bg_uploaded)
        cloaked = cloak_with_background(rgb, mask, bg)
        result_panel("Cloaking", cloaked, "cloaked.png")
    else:
        st.markdown("**Cloaking**")
        st.caption("Upload gambar latar di sidebar untuk mengaktifkan.")

# ---------------------------------------------------------------------------
# Tips
# ---------------------------------------------------------------------------
with st.expander("Tips"):
    st.markdown(
        """
- Objek belum tertangkap penuh: perbesar toleransi Saturation & Value, atau lebarkan Hue.
- Terlalu banyak area ikut tertangkap: persempit toleransi Hue.
- Warna merah ada di dua ujung Hue (0 dan 179) — gunakan slider manual dengan dua rentang terpisah.
- Color Picker cocok untuk eksplorasi cepat; slider manual untuk presisi.
        """
    )
