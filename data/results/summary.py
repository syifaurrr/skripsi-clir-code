import pandas as pd
import os

# 1. Mengelompokkan nama file berdasarkan gambar yang Anda unggah
file_overall = [
    'skenario1_overall_nmt_vs_llm(1).csv',
    'skenario2_distilbert_evaluasi_overall.csv',
    'skenario2_mmbert-small_evaluasi_overall.csv',
    'skenario2_mmbert-base_evaluasi_overall.csv',
    'evaluasi_overall_nmt_vs_gemini(1).csv' # Ini Skenario 3
]

file_tipe = [
    'skenario1_tipe_kueri_nmt_vs_llm(1).csv',
    'skenario2_distilbert_evaluasi_tipe_kueri.csv',
    'skenario2_mmbert-small_evaluasi_tipe_kueri.csv',
    'skenario2_mmbert-base_evaluasi_tipe_kueri.csv',
    'evaluasi_tipe_kueri_nmt_vs_gemini(1).csv' # Ini Skenario 3
]

file_detail = [
    'skenario1_detail_per_kueri_nmt_vs_llm(1).csv',
    'skenario2_distilbert_detail_per_kueri.csv',
    'skenario2_mmbert-small_detail_per_kueri.csv',
    'skenario2_mmbert-base_detail_per_kueri.csv',
    'detail_per_kueri_nmt_vs_gemini(1).csv' # Ini Skenario 3
]

# 2. Fungsi untuk membaca dan menggabungkan list CSV
def gabung_csv(list_file):
    df_list = []
    for file in list_file:
        if os.path.exists(file):
            df = pd.read_csv(file)
            
            # Tambahkan kolom penanda 'Skenario' di paling kiri agar dosen mudah membaca
            if 'skenario1' in file:
                df.insert(0, 'Skenario', 'Skenario 1 (BM25)')
            elif 'skenario2' in file:
                df.insert(0, 'Skenario', 'Skenario 2 (Cross-Lingual)')
            elif 'nmt_vs_gemini' in file:
                df.insert(0, 'Skenario', 'Skenario 3 (AraDPR)')
                
            df_list.append(df)
        else:
            print(f"⚠️ File tidak ditemukan, dilewati: {file}")
            
    if df_list:
        return pd.concat(df_list, ignore_index=True)
    return pd.DataFrame()

print("Membaca dan menggabungkan data...")
df_overall = gabung_csv(file_overall)
df_tipe = gabung_csv(file_tipe)
df_detail = gabung_csv(file_detail)

# 3. Mengekspor ke format CSV (3 File Terpisah)
print("\nMenyimpan ke format CSV...")

if not df_overall.empty:
    df_overall.to_csv('Laporan_1_Master_Tabel_Overall.csv', index=False)
    print("✅ Tersimpan: Laporan_1_Master_Tabel_Overall.csv")
    
if not df_tipe.empty:
    df_tipe.to_csv('Laporan_2_Analisis_Tipe_Kueri.csv', index=False)
    print("✅ Tersimpan: Laporan_2_Analisis_Tipe_Kueri.csv")
    
if not df_detail.empty:
    df_detail.to_csv('Laporan_3_Detail_Hit_Miss.csv', index=False)
    print("✅ Tersimpan: Laporan_3_Detail_Hit_Miss.csv")

print("\n🎉 Selesai! Seluruh data Anda berhasil disatukan.")