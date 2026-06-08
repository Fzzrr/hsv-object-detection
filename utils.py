import io

import numpy as np
from PIL import Image


def load_image(uploaded_file) -> np.ndarray:
    return np.array(Image.open(uploaded_file).convert("RGB"))


def to_png_bytes(arr: np.ndarray) -> bytes:
    if arr.ndim == 2:
        img = Image.fromarray(arr, mode="L")
    elif arr.shape[2] == 4:
        img = Image.fromarray(arr, mode="RGBA")
    else:
        img = Image.fromarray(arr, mode="RGB")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()
