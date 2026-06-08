# HSV Object Detection

Aplikasi Streamlit untuk mendeteksi dan memanipulasi objek pada gambar berdasarkan rentang warna di ruang HSV. Dibuat untuk mata kuliah Pengolahan Citra Digital (PACD).

## Menjalankan

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Fitur

- Deteksi warna via **color picker** (rentang HSV dihitung otomatis + slider toleransi) atau **slider HSV manual**
- Output per gambar: mask, objek hasil slicing, recolor (geser hue / ganti warna), transparansi PNG, cloaking dengan gambar latar
- Setiap output bisa diunduh sebagai PNG

## Cara Kerja

Gambar dikonversi ke HSV, lalu `cv2.inRange(hsv, lower, upper)` membuat mask biner. Dari mask itu piksel objek diisolasi, diubah warnanya dengan menggeser channel Hue, atau dijadikan transparan (alpha = 0).

Format OpenCV: H 0–179, S 0–255, V 0–255. Warna merah terbagi di dua ujung Hue (0 dan 179) — gunakan slider manual untuk kasus ini.

## Struktur

```
app.py          # entry point Streamlit
processing.py   # fungsi OpenCV/numpy (mask, recolor, transparansi, cloaking)
utils.py        # load gambar & ekspor PNG
components.py   # komponen UI (sidebar, result panel)
```
