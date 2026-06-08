import cv2
import numpy as np


def hex_to_rgb(hex_color: str) -> tuple:
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))


def rgb_to_hsv_single(rgb: tuple) -> np.ndarray:
    """Satu piksel RGB -> HSV skala OpenCV (H 0-179, S/V 0-255)."""
    px = np.uint8([[list(rgb)]])
    return cv2.cvtColor(px, cv2.COLOR_RGB2HSV)[0, 0]


def build_range_from_color(
    rgb: tuple, h_tol: int, s_tol: int, v_tol: int
) -> tuple[np.ndarray, np.ndarray]:
    h, s, v = (int(x) for x in rgb_to_hsv_single(rgb))
    lower = np.array([max(h - h_tol, 0), max(s - s_tol, 0), max(v - v_tol, 0)], dtype=np.uint8)
    upper = np.array(
        [min(h + h_tol, 179), min(s + s_tol, 255), min(v + v_tol, 255)], dtype=np.uint8
    )
    return lower, upper


def make_mask(rgb_img: np.ndarray, lower: np.ndarray, upper: np.ndarray) -> np.ndarray:
    hsv = cv2.cvtColor(rgb_img, cv2.COLOR_RGB2HSV)
    return cv2.inRange(hsv, lower, upper)


def slice_object(rgb_img: np.ndarray, mask: np.ndarray) -> np.ndarray:
    out = np.zeros_like(rgb_img, dtype=np.uint8)
    out[mask > 0] = rgb_img[mask > 0]
    return out


def shift_hue(rgb_img: np.ndarray, mask: np.ndarray, hue_delta: int) -> np.ndarray:
    hsv = cv2.cvtColor(rgb_img, cv2.COLOR_RGB2HSV).astype(np.int16)
    hsv[..., 0] = (hsv[..., 0] + hue_delta) % 180
    recolored = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2RGB)
    out = rgb_img.copy()
    out[mask > 0] = recolored[mask > 0]
    return out


def replace_color(
    rgb_img: np.ndarray, mask: np.ndarray, target_rgb: tuple, keep_shading: bool = True
) -> np.ndarray:
    out = rgb_img.copy()
    if keep_shading:
        hsv = cv2.cvtColor(rgb_img, cv2.COLOR_RGB2HSV)
        t_h, t_s, _ = rgb_to_hsv_single(target_rgb)
        new_hsv = hsv.copy()
        new_hsv[..., 0] = t_h
        new_hsv[..., 1] = t_s
        recolored = cv2.cvtColor(new_hsv, cv2.COLOR_HSV2RGB)
        out[mask > 0] = recolored[mask > 0]
    else:
        out[mask > 0] = np.array(target_rgb, dtype=np.uint8)
    return out


def make_transparent(rgb_img: np.ndarray, mask: np.ndarray) -> np.ndarray:
    rgba = np.dstack([rgb_img, np.full(rgb_img.shape[:2], 255, dtype=np.uint8)])
    rgba[mask > 0, 3] = 0
    return rgba


def cloak_with_background(
    rgb_img: np.ndarray, mask: np.ndarray, bg_img: np.ndarray
) -> np.ndarray:
    bg = cv2.resize(bg_img, (rgb_img.shape[1], rgb_img.shape[0]))
    out = rgb_img.copy()
    out[mask > 0] = bg[mask > 0]
    return out
