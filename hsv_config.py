import numpy as np

# ─────────────────────────────────────────────────────────────────────────────
# HSV Color Configuration
# Format: "nama_warna": {
#     "lower": [H, S, V],   ← batas bawah
#     "upper": [H, S, V],   ← batas atas
#     "color_bgr": (B, G, R) ← warna bounding box di layar
# }
#
# Referensi rentang Hue di OpenCV (0–179):
#   Merah   :   0–10  dan 160–179  (perlu dua range)
#   Oranye  :  10–25
#   Kuning  :  25–35
#   Hijau   :  35–85
#   Cyan    :  85–100
#   Biru    : 100–130
#   Ungu    : 130–160
# ─────────────────────────────────────────────────────────────────────────────

COLOR_RANGES = {
    "Merah": {
        "lower":  [np.array([0,   100, 100]), np.array([160, 100, 100])],
        "upper":  [np.array([10,  255, 255]), np.array([179, 255, 255])],
        "multi":  True,   # merah butuh 2 range karena melingkar di Hue
        "color_bgr": (0, 0, 220),
    },
    "Oranye": {
        "lower":  np.array([10,  150, 100]),
        "upper":  np.array([25,  255, 255]),
        "multi":  False,
        "color_bgr": (0, 140, 255),
    },
    "Kuning": {
        "lower":  np.array([25,  100, 100]),
        "upper":  np.array([35,  255, 255]),
        "multi":  False,
        "color_bgr": (0, 220, 220),
    },
    "Hijau": {
        "lower":  np.array([35,  80,  60]),
        "upper":  np.array([85,  255, 255]),
        "multi":  False,
        "color_bgr": (0, 200, 0),
    },
    "Biru": {
        "lower":  np.array([100, 100, 60]),
        "upper":  np.array([130, 255, 255]),
        "multi":  False,
        "color_bgr": (220, 50, 0),
    },
    "Ungu": {
        "lower":  np.array([130, 80,  60]),
        "upper":  np.array([160, 255, 255]),
        "multi":  False,
        "color_bgr": (200, 0, 200),
    },
}

# Urutan warna untuk tombol keyboard (tekan 1–6 untuk ganti warna)
COLOR_KEYS = list(COLOR_RANGES.keys())