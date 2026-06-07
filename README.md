# 🎨 Deteksi Objek Berdasarkan Warna di Ruang HSV

Aplikasi web **Streamlit** untuk mendeteksi dan memanipulasi objek pada gambar
berdasarkan **warna**, menggunakan ruang warna **HSV** dengan OpenCV.

Aplikasi ini menerapkan resep klasik _"Object detection using color in HSV"_:
gambar dikonversi ke HSV, lalu `cv2.inRange()` membuat **mask** biner untuk
memisahkan objek berwarna tertentu dari latarnya. Dari mask itu objek bisa
diekstrak, diubah warnanya, dibuat transparan, atau "disembunyikan" (_cloaking_).

> Dibuat untuk mata kuliah **Pengolahan Citra Digital (PACD)**.

---

## ✨ Fitur

- **Upload gambar apa saja** (JPG, JPEG, PNG, WEBP, BMP).
- **Dua cara memilih warna target:**
  1. **Color Picker** — klik warna, rentang HSV dihitung otomatis lengkap dengan
     slider toleransi (Hue / Saturation / Value).
  2. **Slider HSV manual** — atur sendiri batas bawah & atas (`lower`/`upper`),
     persis seperti parameter `cv2.inRange`.
- **5+ hasil sekaligus**, masing-masing bisa diunduh sebagai PNG:
  - 🖼️ **Original** — gambar asli.
  - ⚫ **Mask** — peta biner area yang terdeteksi.
  - ✂️ **Objek Saja** — hanya objek hasil _slicing_ mask.
  - 🌈 **Warna Objek Diubah** — geser **Hue** atau ganti ke warna pilihan
    (opsi mempertahankan gelap/terang asli objek).
  - 👻 **Objek Transparan** — area objek dijadikan transparan (PNG dengan alpha).
  - 🫥 **Cloaking** — objek "menghilang" diganti gambar latar pilihan.
- **Statistik cepat:** persentase area gambar yang terdeteksi.
- **Tips bawaan** untuk menyempurnakan hasil deteksi.

---

## 🚀 Cara Menjalankan

### 1. Instal dependensi

```bash
pip install -r requirements.txt
```

Atau secara manual:

```bash
pip install streamlit opencv-python-headless numpy pillow
```

### 2. Jalankan aplikasi

```bash
streamlit run app.py
```

Browser akan terbuka otomatis (biasanya di `http://localhost:8501`).

---

## 🧠 Cara Kerja

1. **Konversi RGB → HSV.** HSV memisahkan _warna_ (Hue) dari _kecerahan_ (Value),
   sehingga deteksi warna jauh lebih stabil dibanding di ruang RGB.
2. **`cv2.inRange(hsv, lower, upper)`** membuat **mask** biner: piksel di dalam
   rentang warna menjadi putih (255), sisanya hitam (0).
3. **Slicing dengan mask** untuk mengambil hanya piksel objek.
4. **Ubah warna** cukup dengan menggeser channel **Hue** (tanpa menyentuh
   Saturation/Value), lalu konversi balik ke RGB.
5. **Transparansi / cloaking** dengan mengganti area objek (alpha = 0 atau
   ditimpa gambar latar).

> Catatan format OpenCV: **H ∈ [0, 179]**, **S ∈ [0, 255]**, **V ∈ [0, 255]**.

---

## 📦 Dependensi

| Paket                     | Fungsi                                  |
| ------------------------- | --------------------------------------- |
| `streamlit`               | Antarmuka web interaktif                |
| `opencv-python-headless`  | Pemrosesan citra & konversi ruang warna |
| `numpy`                   | Operasi array piksel                    |
| `pillow`                  | Baca/tulis gambar & ekspor PNG          |

---

## 💡 Tips Deteksi

- **Objek tidak tertangkap penuh?** Perbesar toleransi _Saturation_ & _Value_,
  atau lebarkan rentang _Hue_.
- **Terlalu banyak area ikut tertangkap?** Persempit toleransi, terutama _Hue_.
- **Warna merah** berada di dua ujung lingkaran Hue (dekat 0 dan 179). Gunakan
  mode slider manual (coba dua rentang) atau pilih merah yang condong
  oranye/magenta lewat color picker.
- Mode **Color Picker** menghitung rentang otomatis di sekitar warna pilihan —
  paling mudah untuk eksplorasi cepat.

---

## 📁 Struktur Proyek

```
hsv-object-detection/
├── app.py            # Aplikasi Streamlit (seluruh logika & UI)
├── requirements.txt  # Daftar dependensi
└── README.md
```
