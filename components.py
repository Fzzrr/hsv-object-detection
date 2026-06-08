import numpy as np
import streamlit as st

from processing import build_range_from_color, hex_to_rgb
from utils import to_png_bytes


def render_sidebar() -> dict:
    with st.sidebar:
        uploaded = st.file_uploader(
            "Gambar", type=["jpg", "jpeg", "png", "webp", "bmp"]
        )

        st.divider()

        mode = st.radio("Mode deteksi:", ["Color Picker", "Slider manual"])
        if mode == "Color Picker":
            hex_val = st.color_picker("Warna target", "#FF7A00")
            target_rgb = hex_to_rgb(hex_val)
            with st.expander("Toleransi"):
                h_tol = st.slider("Hue ±", 1, 90, 15)
                s_tol = st.slider("Saturation ±", 10, 255, 100)
                v_tol = st.slider("Value ±", 10, 255, 120)
            lower, upper = build_range_from_color(target_rgb, h_tol, s_tol, v_tol)
        else:
            h_lo, h_hi = st.slider("Hue  (0–179)", 0, 179, (5, 25))
            s_lo, s_hi = st.slider("Saturation  (0–255)", 0, 255, (75, 255))
            v_lo, v_hi = st.slider("Value  (0–255)", 0, 255, (25, 255))
            lower = np.array([h_lo, s_lo, v_lo], dtype=np.uint8)
            upper = np.array([h_hi, s_hi, v_hi], dtype=np.uint8)

        with st.expander("Ubah warna objek"):
            recolor_mode = st.radio("Metode:", ["Geser Hue", "Warna pilihan"])
            recolor_params: dict = {}
            if recolor_mode == "Geser Hue":
                recolor_params["hue_delta"] = st.slider("Pergeseran Hue", -90, 90, 20)
            else:
                new_hex = st.color_picker("Warna baru", "#FFE600")
                recolor_params["new_rgb"] = hex_to_rgb(new_hex)
                recolor_params["keep_shading"] = st.checkbox(
                    "Pertahankan gelap/terang", value=True
                )

        with st.expander("Cloaking"):
            bg_uploaded = st.file_uploader(
                "Gambar latar",
                type=["jpg", "jpeg", "png", "webp", "bmp"],
                key="bg",
            )

    return {
        "uploaded": uploaded,
        "lower": lower,
        "upper": upper,
        "recolor_mode": recolor_mode,
        "recolor_params": recolor_params,
        "bg_uploaded": bg_uploaded,
    }


def _download_btn(arr: np.ndarray, filename: str):
    st.download_button(
        "Unduh PNG",
        data=to_png_bytes(arr),
        file_name=filename,
        mime="image/png",
        key=f"dl_{filename}",
        use_container_width=True,
    )


def result_panel(title: str, img, filename: str, clamp: bool = False):
    st.markdown(f"**{title}**")
    st.image(img, use_container_width=True, clamp=clamp)
    _download_btn(img, filename)
