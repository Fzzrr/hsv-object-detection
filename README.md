# HSV Object Manipulation

Mendeteksi dan memanipulasi objek **berdasarkan warnanya di ruang warna HSV**
menggunakan OpenCV. Program **otomatis mendeteksi warna dominan** pada gambar
(bukan hanya ikan oranye seperti contoh recipe), lalu:

1. **mengiris** (slice) objek dari latar,
2. **mengubah warnanya** (menggeser channel Hue),
3. **membuatnya transparan/hilang** — menukar area objek dengan citra latar
   bila tersedia, atau menghapusnya dengan *inpainting* bila tidak.

> Mata Kuliah: Pengolahan Analisis Citra Digital (PACD)

---

## 📦 Persyaratan

- Python 3.8+
- Dependensi (lihat `requirements.txt`):
  - `opencv-python`
  - `numpy`
  - `matplotlib`

---

## 🚀 Cara Menjalankan

```bash
# 1. (opsional) buat & aktifkan virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux / macOS

# 2. install dependensi
pip install -r requirements.txt

# 3. siapkan gambar, lalu jalankan
python main.py --image images/foto.jpg
```

Program akan mencetak warna dominan yang terdeteksi, lalu menampilkan jendela
**matplotlib** berisi 5 panel: input, mask, objek diiris, objek di-recolor,
dan objek transparan.

### Opsi argumen

| Argumen         | Default        | Fungsi                                                       |
| --------------- | -------------- | ------------------------------------------------------------ |
| `--image`       | `image.png`    | berkas citra input                                           |
| `--target`      | `color`        | `color` = deteksi warna dominan, `dark` = siluet/objek gelap |
| `--dark-thresh` | `50`           | (mode dark) ambang Value; piksel `V<nilai` dianggap objek    |
| `--fill`        | `255,130,0`    | (mode dark) warna isi `B,G,R` saat recolor (default biru)    |
| `--bg`          | *(tidak ada)*  | citra latar untuk efek transparan ala recipe asli            |
| `--hue-shift`   | `20`           | (mode color) besar pergeseran Hue saat me-recolor objek      |
| `--save`        | *(off)*        | simpan tiap panel hasil ke folder `out/`                     |

### Dua mode target

- **`color`** (default) — untuk objek berwarna. Program memilih warna dominan,
  lalu me-recolor dengan menggeser Hue. Cocok mis. kemeja merah, ikan oranye.
- **`dark`** — untuk objek **gelap/siluet** yang tidak punya warna (mis. siluet
  orang membelakangi cahaya). Dideteksi via Value rendah, dan di-recolor dengan
  **mengisi warna solid** (geser Hue tidak terlihat pada piksel hitam).

### Contoh

```bash
# deteksi warna dominan otomatis, transparan via inpaint
python main.py --image images/foto.jpg

# kasus ikan oranye + foto latar (persis cara recipe asli)
python main.py --image images/fish.png --bg images/fish_bg.png

# objek siluet/gelap (mis. fotografer membelakangi langit)
python main.py --image silhouette.png --target dark

# siluet diisi warna merah, ambang lebih ketat, simpan hasil
python main.py --image silhouette.png --target dark --fill 0,0,255 --dark-thresh 45 --save
```

---

## 🖼️ Menyiapkan Gambar

Buat folder `images/` dan letakkan gambar di dalamnya. Untuk efek transparan
ala recipe (mode `--bg`), sediakan dua foto berukuran sama: satu dengan objek
(`fish.png`) dan satu hanya latar tanpa objek (`fish_bg.png`).

```
images/
├── fish.png      # gambar berisi objek
└── fish_bg.png   # (opsional) latar tanpa objek, untuk --bg
```

---

## ⚙️ Cara Kerja

Pipeline pada `main.py` (mengembangkan recipe HSV):

1. **BGR → HSV** — konversi citra input ke ruang warna HSV.
2. **Deteksi warna dominan** (`detect_color`) — hitung luas mask untuk tiap
   warna di `COLOR_RANGES`, pilih yang terbesar. Merah memakai 2 range karena
   melingkar di spektrum Hue.
3. **Masking** (`build_mask`) + **pembersihan** (`clean_mask`, morfologi
   *opening* lalu *closing*) untuk merapikan mask.
4. **Slice** (`slice_object`) — ambil piksel objek saja memakai mask.
5. **Recolor** (`recolor_object`) — geser channel Hue (mod 180) lalu konversi
   kembali ke BGR.
6. **Transparan** (`remove_object`) — tukar latar bila `--bg` ada, selain itu
   `cv2.inpaint` untuk menghapus objek.

Rentang warna diatur di `COLOR_RANGES` (dalam `main.py`): Merah, Oranye,
Kuning, Hijau, Cyan, Biru, Ungu. Tambahkan entri baru di sana bila perlu.

---

## 🛠️ Tips & Troubleshooting

- **Warna terdeteksi salah** → objek dominan mungkin bukan yang kamu maksud;
  sesuaikan rentang di `COLOR_RANGES` atau crop gambar lebih dulu.
- **Mask kurang rapi** → ubah ukuran kernel/iterasi di `clean_mask`.
- **Hasil transparan belang (mode `--bg`)** → pastikan `--bg` diambil dari
  sudut & ukuran yang sama, hanya beda ada/tidaknya objek.
- **Pencahayaan** sangat memengaruhi nilai S/V; uji di kondisi cahaya serupa.
