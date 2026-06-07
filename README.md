# HSV Object Detection

Deteksi objek **real-time via webcam berdasarkan warna** menggunakan ruang warna
HSV dengan OpenCV. Setiap objek yang cocok dengan warna target ditandai dengan
**kotak (bounding box)**, titik tengah, dan label nama warna + luas area.

> Mata Kuliah: Pengolahan Analisis Citra Digital (PACD)

---

## ✨ Fitur

- Deteksi warna real-time dari webcam dalam ruang warna **HSV**.
- 6 warna target siap pakai: Merah, Oranye, Kuning, Hijau, Biru, Ungu.
- Penanda objek berupa **bounding box** dengan isi semi-transparan + titik tengah.
- Pembersihan noise mask dengan **morfologi** (opening + closing).
- Filter objek berdasarkan **luas minimum** untuk membuang noise kecil.
- Tampilan HUD: warna aktif, status mask, jumlah objek, dan **FPS**.
- Mode **side-by-side mask** untuk melihat hasil segmentasi.
- Simpan **screenshot** kapan saja.

---

## 📦 Persyaratan

- Python 3.8+
- Webcam
- Dependensi (lihat `requirements.txt`):
  - `opencv-python`
  - `numpy`

---

## 🚀 Instalasi & Menjalankan

```bash
# (opsional) buat virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux / macOS

# install dependensi
pip install -r requirements.txt

# jalankan
python main.py
```

---

## 🎮 Kontrol Keyboard

| Tombol | Fungsi                                |
| :----: | ------------------------------------- |
| `1`–`6`| Ganti warna target                    |
| `M`    | Tampilkan / sembunyikan mask          |
| `S`    | Simpan screenshot frame saat ini      |
| `Q`    | Keluar dari program                   |

---

## 🗂️ Struktur Proyek

```
hsv-object-detection/
├── main.py            # Loop utama: ambil frame, proses, tampilkan
├── utils.py           # Pemrosesan citra + fungsi menggambar/overlay
├── hsv_config.py      # Definisi rentang warna HSV & palet bounding box
├── requirements.txt   # Daftar dependensi
└── README.md
```

---

## ⚙️ Cara Kerja

Pipeline pemrosesan tiap frame (`main.py`):

1. **BGR → HSV** — konversi frame webcam ke ruang warna HSV.
2. **Masking** (`build_mask`) — buat binary mask sesuai rentang warna target.
   Warna **Merah** memakai 2 range karena melingkar di spektrum Hue.
3. **Pembersihan** (`clean_mask`) — morfologi *opening* (buang noise) lalu
   *closing* (tutup lubang) untuk merapikan mask.
4. **Pencarian objek** (`find_objects`) — cari kontur, filter berdasarkan
   `min_area`, dan hitung bounding box tiap objek.
5. **Visualisasi** (`draw_detections`) — gambar kotak + titik tengah + label.
6. **Overlay UI** — HUD, swatch warna, dan status bar.

---

## 🎨 Menyesuaikan Warna

Rentang warna diatur di `hsv_config.py`. Setiap entri pada `COLOR_RANGES`
berisi:

```python
"NamaWarna": {
    "lower": np.array([H, S, V]),   # batas bawah HSV
    "upper": np.array([H, S, V]),   # batas atas HSV
    "multi": False,                  # True jika butuh 2 range (mis. Merah)
    "color_bgr": (B, G, R),          # warna kotak di layar
}
```

Catatan rentang Hue di OpenCV (0–179):

| Warna  | Hue            |
| ------ | -------------- |
| Merah  | 0–10 & 160–179 |
| Oranye | 10–25          |
| Kuning | 25–35          |
| Hijau  | 35–85          |
| Cyan   | 85–100         |
| Biru   | 100–130        |
| Ungu   | 130–160        |

Untuk menambah warna baru, tambahkan entri pada `COLOR_RANGES`; tombol keyboard
mengikuti urutan otomatis dari `COLOR_KEYS`.

---

## 🛠️ Tips & Troubleshooting

- **Kamera tidak terdeteksi** → ubah indeks `cv2.VideoCapture(0)` di `main.py`
  (coba `1`, `2`, dst) bila punya lebih dari satu kamera.
- **Objek tidak terdeteksi** → sesuaikan `lower`/`upper` HSV, atau turunkan
  `min_area` pada `find_objects(mask_clean, min_area=1500)` di `main.py`.
- **Banyak noise** → naikkan `min_area` atau perbesar kernel morfologi di
  `clean_mask` (`utils.py`).
- **Pencahayaan** sangat memengaruhi nilai S/V — uji di kondisi cahaya yang mirip
  dengan pemakaian sebenarnya.
