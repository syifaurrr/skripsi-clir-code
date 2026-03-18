# Dashboard Analisis CLIR - Panduan Penggunaan

## 🚀 Cara Menjalankan

```bash
# Pastikan berada di root project
cd /path/to/skripsi-clir-code

# Jalankan dashboard
streamlit run src/dashboard.py
```

Dashboard akan terbuka di browser: `http://localhost:8501`

---

## 🎨 Fitur Light Mode untuk Laporan Skripsi

### Mengaktifkan Light Mode
1. Buka **sidebar** (panel kiri)
2. Di bagian "🎨 Pengaturan Tampilan", pilih **"☀️ Light Mode"**
3. Tampilan akan otomatis berubah menjadi tema terang yang cocok untuk laporan

### Mengapa Light Mode?
- ✅ Lebih profesional untuk laporan akademik
- ✅ Cetakan lebih jelas (jika perlu print)
- ✅ Warna chart lebih kontras dan mudah dibaca
- ✅ Standar untuk publikasi ilmiah

---

## 📋 Fitur Copy to Clipboard

Setiap teks yang ditampilkan di dashboard memiliki tombol **📋 Copy** di sebelahnya:

### Di Halaman "🌍 Query Bahasa Arab":
- **Query Indonesia** - Copy teks query asli
- **Arab (Google NMT)** - Copy terjemahan NMT
- **Arab (Gemini LLM)** - Copy terjemahan LLM
- **ID Dokumen** - Copy ID dokumen korpus
- **Isi Dokumen** - Copy seluruh teks dokumen Fathul Muin
- **Query + Doc** - Copy kombinasi query dan dokumen

### Cara Menggunakan:
1. Klik tombol **📋** di sebelah teks yang ingin dicopy
2. Teks akan tersimpan di clipboard
3. Paste ke dokumen Anda (Ctrl+V)

---

## 📥 Export Visualisasi untuk Laporan

### Cara Export Grafik

Setiap halaman memiliki tombol **"💾 Simpan Grafik untuk Laporan"** yang akan menyimpan grafik dalam format PNG beresolusi tinggi (1200x800px, 2x scale).

File yang tersimpan:
- `hit_rate_overview.png` - Grafik performa model
- `heatmap_query_type.png` - Heatmap per tipe query
- `correlation_matrix.png` - Matriks korelasi antar model
- `model_comparison_pie.png` - Grafik perbandingan model
- `success_curve.png` - Success@k curve

### Tips Export untuk Skripsi

1. **Gunakan Light Mode** sebelum export
2. **Resolusi tinggi** sudah otomatis (2400x1600px efektif)
3. Format PNG cocok untuk dimasukkan ke Word/LaTeX
4. Gunakan **SVG** jika membutuhkan vektor (bisa diskalakan tanpa pecah)

---

## 📊 Halaman Dashboard

### 1. 📈 Overview
- Ringkasan statistik (total query, model, dll)
- Ranking model berdasarkan Hit Rate
- Visualisasi bar chart performa

### 2. 🏆 Perbandingan Model
**4 Jenis Perbandingan dengan Tab:**
- **Tab 1 - A Berhasil, B Gagal**: Query yang hanya berhasil di Model A
- **Tab 2 - A Gagal, B Berhasil**: Query yang hanya berhasil di Model B
- **Tab 3 - Keduanya Berhasil**: Query yang berhasil di kedua model (overlap)
- **Tab 4 - Keduanya Gagal**: Query yang gagal di kedua model (hard queries)
- **Metrics**: Hit rate, keunggulan, overlap rate, dll
- **Analisis "Unique Hits"**: Query yang hanya ditemukan oleh satu model
- Breakdown per tipe query untuk setiap kategori

### 3. 🔍 Analisis Query
- **Query Sulit (≤2 model)** vs **Query Mudah (≥10 model)**
- **By Query Type**: Heatmap performa per tipe (1, 2, 3)
- **All Hit/Miss**: Query yang sukses/gagal di semua model

### 4. 📊 Metrik Lengkap (MRR & Success@k)
**Metrik Evaluasi Lengkap:**
- **MRR Ranking**: Tabel ranking model berdasarkan Mean Reciprocal Rank
- **Success@k Curve**: Kurva peningkatan success rate (k=10,20,50,100)
- **Per Skenario**: Perbandingan metrik untuk setiap skenario
- **MRR vs Success@10 Scatter**: Hubungan antara MRR dan Success@10
- **Statistik**: MRR tertinggi, terendah, dan rata-rata

### 5. 🌍 Query Bahasa Arab
**Perbandingan Terjemahan Query & Performa:**
- **Tabel Query**: Semua query dalam bahasa Indonesia, Arab (NMT), dan Arab (LLM)
- **Filter**: Filter berdasarkan tipe query, pencarian teks
- **Detail Perbandingan**: Lihat perbandingan lengkap per query
- **📋 Copy to Clipboard**: Tombol copy untuk setiap teks (Query Indo, Arab NMT, Arab LLM)
- **Analisis Panjang**: Perbandingan panjang karakter NMT vs LLM
- **📚 Dokumen Korpus**: Lihat dokumen Fathul Muin yang relevan dengan query yang dipilih
  - Tampilkan dokumen relevan dari korpus
  - Panjang dokumen, jumlah kata, jumlah baris
  - **📋 Copy ID Dokumen, Copy Isi Dokumen, Copy Query+Doc**
- **🎯 Performa Query**: Lihat ranking dan keberhasilan query yang dipilih untuk SEMUA model
  - Rank (posisi dokumen relevan pertama)
  - Hit@10, @20, @50, @100 untuk setiap model
  - Visualisasi ranking per model
  - Success rate per skenario
- **Export**: Export data query Arab ke CSV

### 6. 📈 Visualisasi Lanjutan
- **Fine-Tuned vs Baseline**: Efek fine-tuning JH-POLO
- **LLM vs NMT**: Perbandingan Google NMT vs Gemini LLM
- **Correlation Matrix**: Korelasi antar model

---

## 💡 Tips untuk Bab Analisis Skripsi

### Analisis yang Bisa Ditulis:

1. **Bandingkan BM25+RM3 vs Baseline Dense**
   - Pergi ke halaman "🏆 Perbandingan Model"
   - Pilih BM25+RM3 (Gemini LLM) sebagai Model A
   - Pilih Baseline (mmBERT-base) sebagai Model B
   - **Gunakan 4 Tab untuk analisis lengkap:**
     - Tab 1: Query yang hanya berhasil di BM25+RM3
     - Tab 2: Query yang hanya berhasil di Baseline
     - Tab 3: Query yang berhasil di keduanya (overlap)
     - Tab 4: Query yang gagal di keduanya (hard queries)

2. **Analisis Efek Fine-Tuning**
   - Di halaman "📈 Visualisasi Lanjutan"
   - Lihat grafik "Fine-Tuned vs Baseline"
   - Hitung berapa query yang membaik setelah fine-tuning

3. **Analisis Per Tipe Query**
   - Di halaman "🔍 Analisis Query" → tab "By Query Type"
   - Lihat heatmap performa model per tipe query
   - Identifikasi tipe query mana yang paling sulit

4. **Temukan Query Sulit**
   - Di halaman "🔍 Analisis Query" → tab "Query Sulit & Mudah"
   - Lihat query yang gagal ditemukan oleh semua model
   - Analisis karakteristik query tersebut

5. **Analisis Korpus dengan Query**
   - Di halaman "🌍 Query Bahasa Arab"
   - Pilih query yang ingin dianalisis
   - Scroll ke bawah ke bagian "📚 Dokumen Korpus yang Relevan"
   - Baca dokumen relevan untuk memahami konteks
   - Copy query dan dokumen untuk analisis lebih lanjut

---

## 📸 Contoh Screenshot untuk Laporan

**Rekomendasi screenshot yang perlu diambil:**

1. **Gambar 4.1**: Overview performa semua model (bar chart)
2. **Gambar 4.2**: Heatmap performa per tipe query
3. **Gambar 4.3**: Success@k Curve (metrik lengkap)
4. **Gambar 4.4**: MRR Ranking (tabel)
5. **Gambar 4.5**: Perbandingan Fine-Tuned vs Baseline
6. **Gambar 4.6**: Perbandingan LLM vs NMT
7. **Gambar 4.7**: Correlation matrix antar model
8. **Gambar 4.8**: MRR vs Success@10 Scatter plot

---

## 🔧 Troubleshooting

### Dashboard tidak bisa dibuka?
- Pastikan port 8501 tidak digunakan aplikasi lain
- Coba jalankan dengan port berbeda: `streamlit run src/dashboard.py --server.port 8502`

### Grafik tidak muncul?
- Refresh halaman (F5)
- Pastikan koneksi internet aktif (untuk load Plotly)

### Export PNG gagal?
- Install kaleido: `pip install kaleido`
- Atau gunakan screenshot manual dari browser

### Copy to clipboard tidak berfungsi?
- Beberapa browser memerlukan HTTPS untuk clipboard API
- Alternatif: Gunakan tombol copy, lalu pilih dan copy manual dari text area

---

## 📝 Catatan Penting

- Data yang ditampilkan bersumber dari file CSV di `data/results/`
- Query list diambil dari `data/queries/queries_indo.csv` (153 query)
- Korpus dokumen dari `data/raw/fathul_muin.csv` (5139 dokumen)
- Mapping relevansi dari `data/queries/qrels.csv`
- Hasil analisis bersifat dinamis sesuai data yang tersedia

---

## 📁 Struktur File Data

```
data/
├── queries/
│   ├── queries_indo.csv      # Query Indonesia (153)
│   ├── queries_arab.csv      # Query Arab NMT & LLM
│   └── qrels.csv             # Mapping query-doc relevan
├── raw/
│   └── fathul_muin.csv       # Korpus dokumen
└── results/
    └── *.csv                 # Hasil evaluasi model
```

---

Selamat menganalisis! 🎓
