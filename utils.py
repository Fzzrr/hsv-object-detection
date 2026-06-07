import cv2
import numpy as np
from hsv_config import COLOR_RANGES, COLOR_KEYS

# ─────────────────────────────────────────────────────────────────────────────
# Palet & font global untuk tampilan
# ─────────────────────────────────────────────────────────────────────────────
FONT      = cv2.FONT_HERSHEY_SIMPLEX
FONT_BOLD = cv2.FONT_HERSHEY_DUPLEX

CLR_PANEL  = (28, 28, 32)     # latar panel (gelap)
CLR_ACCENT = (255, 196, 0)    # aksen
CLR_TEXT   = (235, 235, 235)  # teks utama
CLR_SUBTLE = (150, 150, 150)  # teks sekunder
CLR_OK     = (90, 230, 120)   # hijau status


# ─────────────────────────────────────────────────────────────────────────────
# Helper menggambar
# ─────────────────────────────────────────────────────────────────────────────
def rounded_rect(img, p1, p2, color, radius=12, thickness=-1):
    """Persegi panjang dengan sudut membulat (fill bila thickness < 0)."""
    x1, y1 = p1
    x2, y2 = p2
    radius = max(0, min(radius, abs(x2 - x1) // 2, abs(y2 - y1) // 2))

    if thickness < 0:
        cv2.rectangle(img, (x1 + radius, y1), (x2 - radius, y2), color, -1)
        cv2.rectangle(img, (x1, y1 + radius), (x2, y2 - radius), color, -1)
    else:
        cv2.line(img, (x1 + radius, y1), (x2 - radius, y1), color, thickness, cv2.LINE_AA)
        cv2.line(img, (x1 + radius, y2), (x2 - radius, y2), color, thickness, cv2.LINE_AA)
        cv2.line(img, (x1, y1 + radius), (x1, y2 - radius), color, thickness, cv2.LINE_AA)
        cv2.line(img, (x2, y1 + radius), (x2, y2 - radius), color, thickness, cv2.LINE_AA)

    for cx, cy, a in [(x1 + radius, y1 + radius, 180),
                      (x2 - radius, y1 + radius, 270),
                      (x1 + radius, y2 - radius, 90),
                      (x2 - radius, y2 - radius, 0)]:
        cv2.ellipse(img, (cx, cy), (radius, radius), a, 0, 90, color,
                    thickness, cv2.LINE_AA)


def panel(img, p1, p2, alpha=0.55, color=CLR_PANEL, radius=12):
    """Panel semi-transparan dengan sudut membulat di atas frame."""
    overlay = img.copy()
    rounded_rect(overlay, p1, p2, color, radius=radius, thickness=-1)
    cv2.addWeighted(overlay, alpha, img, 1 - alpha, 0, img)


# ─────────────────────────────────────────────────────────────────────────────
# Pemrosesan citra
# ─────────────────────────────────────────────────────────────────────────────
def build_mask(hsv_frame, color_name):
    """
    Buat binary mask berdasarkan nama warna dari COLOR_RANGES.
    Merah butuh 2 range (melingkar di spektrum Hue), warna lain cukup 1.
    """
    cfg = COLOR_RANGES[color_name]

    if cfg["multi"]:
        mask1 = cv2.inRange(hsv_frame, cfg["lower"][0], cfg["upper"][0])
        mask2 = cv2.inRange(hsv_frame, cfg["lower"][1], cfg["upper"][1])
        mask  = cv2.bitwise_or(mask1, mask2)
    else:
        mask = cv2.inRange(hsv_frame, cfg["lower"], cfg["upper"])

    return mask


def clean_mask(mask):
    """
    Bersihkan noise kecil dari mask menggunakan morfologi:
    - Opening : hapus noise putih kecil (erosi → dilasi)
    - Closing : tutup lubang kecil di objek (dilasi → erosi)
    """
    kernel  = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
    opened  = cv2.morphologyEx(mask,   cv2.MORPH_OPEN,  kernel, iterations=2)
    cleaned = cv2.morphologyEx(opened, cv2.MORPH_CLOSE, kernel, iterations=2)
    return cleaned


def find_objects(mask, min_area=1500):
    """
    Temukan kontur objek dari mask dan filter berdasarkan luas minimum.
    Kembalikan list of dict berisi kontur + bounding box + area.
    """
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    objects = []
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area >= min_area:
            x, y, w, h = cv2.boundingRect(cnt)
            objects.append({"contour": cnt, "x": x, "y": y,
                            "w": w, "h": h, "area": area})
    # objek terbesar digambar terakhir (paling depan)
    return sorted(objects, key=lambda o: o["area"])


# ─────────────────────────────────────────────────────────────────────────────
# Overlay / tampilan
# ─────────────────────────────────────────────────────────────────────────────
def draw_detections(frame, objects, color_name):
    """
    Gambar KOTAK (bounding box) di sekeliling objek, titik tengah,
    dan label nama warna + luas area.
    """
    cfg       = COLOR_RANGES[color_name]
    bgr_color = cfg["color_bgr"]

    for obj in objects:
        x, y, w, h, area = obj["x"], obj["y"], obj["w"], obj["h"], obj["area"]
        p1, p2 = (x, y), (x + w, y + h)

        # isi transparan di dalam kotak
        overlay = frame.copy()
        cv2.rectangle(overlay, p1, p2, bgr_color, -1)
        cv2.addWeighted(overlay, 0.18, frame, 0.82, 0, frame)

        # garis kotak (efek glow tipis + garis tegas)
        cv2.rectangle(frame, p1, p2, bgr_color, 4, cv2.LINE_AA)
        cv2.rectangle(frame, p1, p2, (255, 255, 255), 1, cv2.LINE_AA)

        # titik tengah kotak
        cx, cy = x + w // 2, y + h // 2
        cv2.circle(frame, (cx, cy), 3, (255, 255, 255), -1, cv2.LINE_AA)
        cv2.circle(frame, (cx, cy), 7, bgr_color, 2, cv2.LINE_AA)

        # label dengan latar membulat di atas objek
        label = f"{color_name}  {int(area):,}px"
        (tw, th), _ = cv2.getTextSize(label, FONT, 0.5, 1)
        ly = max(y, th + 14)
        rounded_rect(frame, (x, ly - th - 12), (x + tw + 16, ly), bgr_color,
                     radius=6, thickness=-1)
        cv2.putText(frame, label, (x + 8, ly - 5),
                    FONT, 0.5, (255, 255, 255), 1, cv2.LINE_AA)

    return frame


def draw_hud(frame, color_name, color_keys, show_mask, fps=None):
    """
    Panel kontrol di pojok kiri atas: judul, swatch warna aktif, dan tombol.
    """
    pad    = 14
    px, py = pad, pad
    pw, ph = 248, 150
    panel(frame, (px, py), (px + pw, py + ph), alpha=0.6)

    # garis aksen di kiri panel
    cv2.rectangle(frame, (px, py + 10), (px + 4, py + ph - 10), CLR_ACCENT, -1)

    tx = px + 16
    cv2.putText(frame, "HSV DETECTION", (tx, py + 26),
                FONT_BOLD, 0.6, CLR_TEXT, 1, cv2.LINE_AA)

    # swatch warna aktif
    sw_y = py + 40
    cfg  = COLOR_RANGES[color_name]
    rounded_rect(frame, (tx, sw_y), (tx + 18, sw_y + 18), cfg["color_bgr"],
                 radius=4, thickness=-1)
    cv2.putText(frame, color_name, (tx + 26, sw_y + 14),
                FONT, 0.55, CLR_TEXT, 1, cv2.LINE_AA)

    # status mask
    st_clr = CLR_OK if show_mask else CLR_SUBTLE
    cv2.putText(frame, f"Mask: {'ON' if show_mask else 'OFF'}",
                (tx + 130, sw_y + 14), FONT, 0.5, st_clr, 1, cv2.LINE_AA)

    # hint tombol
    hints = ["1-6  ganti warna", "M  mask     S  simpan", "Q  keluar"]
    for i, line in enumerate(hints):
        cv2.putText(frame, line, (tx, py + 86 + i * 20),
                    FONT, 0.45, CLR_SUBTLE, 1, cv2.LINE_AA)

    # FPS di pojok kanan atas
    if fps is not None:
        ftxt = f"{fps:4.1f} FPS"
        (fw, _), _ = cv2.getTextSize(ftxt, FONT, 0.5, 1)
        fx = frame.shape[1] - fw - 24
        panel(frame, (fx - 10, pad), (fx + fw + 10, pad + 26), alpha=0.6)
        cv2.putText(frame, ftxt, (fx, pad + 18), FONT, 0.5, CLR_OK, 1, cv2.LINE_AA)

    return frame


def draw_swatches(frame, color_name):
    """Deretan swatch semua warna di bawah, dengan highlight warna aktif."""
    h, w  = frame.shape[:2]
    n     = len(COLOR_KEYS)
    box   = 26
    gap   = 8
    total = n * box + (n - 1) * gap
    sx    = (w - total) // 2
    sy    = h - box - 14

    panel(frame, (sx - 12, sy - 10), (sx + total + 12, sy + box + 10), alpha=0.55)

    for i, name in enumerate(COLOR_KEYS):
        bx     = sx + i * (box + gap)
        active = name == color_name
        clr    = COLOR_RANGES[name]["color_bgr"]
        rounded_rect(frame, (bx, sy), (bx + box, sy + box), clr,
                     radius=6, thickness=-1)
        if active:
            rounded_rect(frame, (bx - 2, sy - 2), (bx + box + 2, sy + box + 2),
                         CLR_ACCENT, radius=7, thickness=2)
        cv2.putText(frame, str(i + 1), (bx + 8, sy + box - 8),
                    FONT, 0.45, (255, 255, 255), 1, cv2.LINE_AA)

    return frame


def draw_status_bar(frame, count):
    """Indikator jumlah objek terdeteksi."""
    h, w  = frame.shape[:2]
    bar_h = 30
    panel(frame, (14, h - bar_h - 50), (210, h - 50), alpha=0.6)
    dot = CLR_OK if count else (90, 90, 90)
    cv2.circle(frame, (32, h - 65), 6, dot, -1, cv2.LINE_AA)
    cv2.putText(frame, f"Objek: {count}", (48, h - 60),
                FONT, 0.55, CLR_TEXT, 1, cv2.LINE_AA)
    return frame


def stack_with_mask(output, mask_clean, color_name):
    """Gabungkan frame deteksi + mask berwarna berdampingan dengan label."""
    cfg = COLOR_RANGES[color_name]
    # warnai mask sesuai warna target (bukan grayscale polos)
    colored = np.zeros_like(output)
    colored[mask_clean > 0] = cfg["color_bgr"]
    gray      = cv2.cvtColor(mask_clean, cv2.COLOR_GRAY2BGR)
    mask_view = cv2.addWeighted(colored, 0.8, gray, 0.2, 0)

    cv2.putText(mask_view, "MASK", (16, 28), FONT, 0.6, CLR_ACCENT, 1, cv2.LINE_AA)

    combined = np.hstack([output, mask_view])
    x = output.shape[1]
    cv2.line(combined, (x, 0), (x, combined.shape[0]), CLR_ACCENT, 2)
    return combined
