"""
Object Detection using Color in HSV
====================================
Mata Kuliah : Pengolahan Analisis Citra Digital
Deskripsi   : Deteksi objek real-time via webcam berdasarkan warna
              menggunakan ruang warna HSV.

Kontrol keyboard:
  1-6   → ganti warna target
  M     → tampilkan/sembunyikan mask
  S     → simpan screenshot frame sekarang
  Q     → keluar
"""

import time

import cv2
from hsv_config import COLOR_KEYS
from utils import (build_mask, clean_mask, find_objects, draw_detections,
                   draw_hud, draw_swatches, draw_status_bar, stack_with_mask)


def main():
    # ── Inisialisasi webcam ──────────────────────────────────────────────────
    cap = cv2.VideoCapture(0)      # 0 = webcam default
    if not cap.isOpened():
        print("[ERROR] Kamera tidak terdeteksi. Cek koneksi webcam.")
        return

    cap.set(cv2.CAP_PROP_FRAME_WIDTH,  640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_FPS, 30)

    # ── State awal ───────────────────────────────────────────────────────────
    current_color_idx = 0       # mulai dengan warna pertama (Merah)
    show_mask         = False   # toggle tampilan mask
    screenshot_count  = 0
    fps               = 0.0
    prev_t            = time.time()

    print("=" * 45)
    print("  Object Detection using Color in HSV")
    print("=" * 45)
    print(f"  Warna tersedia: {', '.join(COLOR_KEYS)}")
    print("  Tekan 1-{} untuk ganti warna".format(len(COLOR_KEYS)))
    print("  Tekan M untuk toggle mask")
    print("  Tekan S untuk screenshot")
    print("  Tekan Q untuk keluar")
    print("=" * 45)

    while True:
        ret, frame = cap.read()
        if not ret:
            print("[WARNING] Frame tidak terbaca, melewati...")
            continue

        color_name = COLOR_KEYS[current_color_idx]

        # ── Pipeline pemrosesan ──────────────────────────────────────────────
        # 1. Konversi BGR → HSV
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        # 2. Buat mask berdasarkan warna target
        mask = build_mask(hsv, color_name)

        # 3. Bersihkan noise dengan morfologi
        mask_clean = clean_mask(mask)

        # 4. Temukan objek (kontur + bounding box)
        objects = find_objects(mask_clean, min_area=1500)

        # ── Hitung FPS (rata-rata bergerak agar tidak berkedip) ──────────────
        now      = time.time()
        dt       = now - prev_t
        prev_t   = now
        if dt > 0:
            fps = 0.9 * fps + 0.1 * (1.0 / dt)

        # 5. Gambar outline deteksi mengikuti bentuk objek pada frame asli
        output = frame.copy()
        draw_detections(output, objects, color_name)

        # 6. Overlay tampilan: HUD, swatch warna, status bar
        draw_hud(output, color_name, COLOR_KEYS, show_mask, fps=fps)
        draw_swatches(output, color_name)
        draw_status_bar(output, len(objects))

        # ── Tampilkan window ─────────────────────────────────────────────────
        if show_mask:
            combined = stack_with_mask(output, mask_clean, color_name)
            cv2.imshow("HSV Object Detection", combined)
        else:
            cv2.imshow("HSV Object Detection", output)

        # ── Input keyboard ───────────────────────────────────────────────────
        key = cv2.waitKey(1) & 0xFF

        # Angka 1–len(COLOR_KEYS) untuk ganti warna
        for i, _ in enumerate(COLOR_KEYS):
            if key == ord(str(i + 1)):
                current_color_idx = i
                print(f"[INFO] Ganti ke warna: {COLOR_KEYS[i]}")

        if key == ord('m') or key == ord('M'):
            show_mask = not show_mask
            print(f"[INFO] Mask {'ON' if show_mask else 'OFF'}")

        elif key == ord('s') or key == ord('S'):
            filename = f"screenshot_{screenshot_count:03d}.png"
            cv2.imwrite(filename, output)
            screenshot_count += 1
            print(f"[INFO] Screenshot disimpan: {filename}")

        elif key == ord('q') or key == ord('Q'):
            print("[INFO] Program dihentikan.")
            break

    # ── Cleanup ──────────────────────────────────────────────────────────────
    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()