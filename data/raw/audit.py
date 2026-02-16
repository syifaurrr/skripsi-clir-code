# import re
# import pandas as pd

# # Contoh simulasi data (Ganti variabel ini dengan load file asli Anda)
# f = open('0987ZaynDinMalibari.FathMucin.Shamela0011327-ara1.txt', 'r', encoding='utf-8')
# raw_text = f.read()

# # raw_text = """
# # Teks awal...
# # # PageV01P520
# # Isi halaman 520...
# # # PageV01P521
# # Isi halaman 521...
# # # PageV01P534
# # Isi halaman 534 yang pertama (mungkin error)...
# # # PageV01P523
# # Isi halaman 523 yang nyempil...
# # # PageV01P534
# # Isi halaman 534 yang kedua (mungkin yang benar)...
# # # PageV01P536
# # Isi halaman 536 (Loh, 535 mana?)...
# # """

# def audit_corpus(text):
#     # Regex untuk menangkap pola # PageVxxPxxx
#     # Group 1 = Volume, Group 2 = Page
#     pattern = re.compile(r'# PageV(\d+)P(\d+)')
    
#     matches = []
#     for match in pattern.finditer(text):
#         matches.append({
#             'full_tag': match.group(0),
#             'vol': int(match.group(1)),
#             'page': int(match.group(2)),
#             'start_index': match.start()
#         })
    
#     errors = []
    
#     for i in range(1, len(matches)):
#         curr = matches[i]
#         prev = matches[i-1]
        
#         # Cek hanya jika Volume sama (jika ganti volume, reset urutan biasanya)
#         if curr['vol'] == prev['vol']:
#             diff = curr['page'] - prev['page']
            
#             # KASUS 1: DUPLIKAT
#             if diff == 0:
#                 errors.append({
#                     'type': 'DUPLICATE',
#                     'msg': f"Halaman {curr['page']} muncul ganda.",
#                     'pos': f"Tag 1 di index {prev['start_index']}, Tag 2 di index {curr['start_index']}"
#                 })
            
#             # KASUS 2: MUNDUR (NYEMPIL)
#             elif diff < 0:
#                 errors.append({
#                     'type': 'BACKWARD_JUMP',
#                     'msg': f"Urutan mundur! Dari {prev['page']} ke {curr['page']}.",
#                     'pos': f"Index {curr['start_index']}"
#                 })
                
#             # KASUS 3: GAP (LOMPAT JAUH)
#             elif diff > 1:
#                 errors.append({
#                     'type': 'MISSING_GAP',
#                     'msg': f"Halaman lompat. Dari {prev['page']} langsung ke {curr['page']}. (Hilang {diff-1} halaman)",
#                     'pos': f"Index {curr['start_index']}"
#                 })

#     return pd.DataFrame(errors)

# # Jalankan Audit
# df_errors = audit_corpus(raw_text)

# # Tampilkan Hasil
# if not df_errors.empty:
#     print("Ditemukan Error dalam Struktur Halaman:")
#     print(df_errors)
#     # df_errors.to_csv('laporan_error_corpus.csv') # Simpan ke excel/csv untuk diperbaiki
# else:
#     print("Struktur halaman terlihat rapi (sequential).")

# import re
# import pandas as pd

# # Load the file
# f = open('0987ZaynDinMalibari.FathMucin.Shamela0011327-ara1.txt', 'r', encoding='utf-8')
# raw_text = f.read()
# f.close()

# def audit_corpus(text):
#     # Regex untuk menangkap pola # PageVxxPxxx
#     # Group 1 = Volume, Group 2 = Page
#     pattern = re.compile(r'# PageV(\d+)P(\d+)')
#     matches = []
    
#     for match in pattern.finditer(text):
#         matches.append({
#             'full_tag': match.group(0),
#             'vol': int(match.group(1)),
#             'page': int(match.group(2)),
#             'start_index': match.start()
#         })
    
#     errors = []
    
#     for i in range(1, len(matches)):
#         curr = matches[i]
#         prev = matches[i-1]
        
#         # Cek hanya jika Volume sama (jika ganti volume, reset urutan biasanya)
#         if curr['vol'] == prev['vol']:
#             diff = curr['page'] - prev['page']
            
#             # KASUS 1: DUPLIKAT
#             if diff == 0:
#                 errors.append({
#                     'type': 'DUPLICATE',
#                     'msg': f"Halaman {curr['page']} muncul ganda.",
#                     'pos': f"Tag 1 di index {prev['start_index']}, Tag 2 di index {curr['start_index']}"
#                 })
            
#             # KASUS 2: MUNDUR (NYEMPIL)
#             elif diff < 0:
#                 errors.append({
#                     'type': 'BACKWARD_JUMP',
#                     'msg': f"Urutan mundur! Dari {prev['page']} ke {curr['page']}.",
#                     'pos': f"Index {curr['start_index']}"
#                 })
            
#             # KASUS 3: GAP (LOMPAT JAUH)
#             elif diff > 1:
#                 errors.append({
#                     'type': 'MISSING_GAP',
#                     'msg': f"Halaman lompat. Dari {prev['page']} langsung ke {curr['page']}. (Hilang {diff-1} halaman)",
#                     'pos': f"Index {curr['start_index']}"
#                 })
    
#     return pd.DataFrame(errors)

# # Jalankan Audit
# df_errors = audit_corpus(raw_text)

# # Simpan hasil ke file
# output_file = 'audit_output.txt'

# with open(output_file, 'w', encoding='utf-8') as f:
#     if not df_errors.empty:
#         f.write("Ditemukan Error dalam Struktur Halaman:\n")
#         f.write("=" * 80 + "\n\n")
#         f.write(df_errors.to_string(index=False))
#         f.write("\n\n" + "=" * 80 + "\n")
#         f.write(f"Total errors ditemukan: {len(df_errors)}\n")
        
#         # Juga print ke console
#         print("Ditemukan Error dalam Struktur Halaman:")
#         print(df_errors)
#         print(f"\nHasil telah disimpan ke '{output_file}'")
        
#         # Simpan juga ke CSV untuk analisis lebih lanjut
#         df_errors.to_csv('laporan_error_corpus.csv', index=False, encoding='utf-8')
#         print("Laporan CSV disimpan ke 'laporan_error_corpus.csv'")
#     else:
#         f.write("Struktur halaman terlihat rapi (sequential).\n")
#         f.write("Tidak ada error yang ditemukan.\n")
        
#         # Juga print ke console
#         print("Struktur halaman terlihat rapi (sequential).")
#         print(f"Hasil telah disimpan ke '{output_file}'")

# print("\nSelesai!")

import re
import pandas as pd

# Load the file
f = open('fath_muin_no_dupe.txt', 'r', encoding='utf-8')
raw_text = f.read()
f.close()

def audit_corpus(text):
    # Regex untuk menangkap pola # PageVxxPxxx
    # Group 1 = Volume, Group 2 = Page
    pattern = re.compile(r'# PageV(\d+)P(\d+)')
    matches = []
    
    for match in pattern.finditer(text):
        matches.append({
            'full_tag': match.group(0),
            'vol': int(match.group(1)),
            'page': int(match.group(2)),
            'start_index': match.start()
        })
    
    errors = []
    
    for i in range(1, len(matches)):
        curr = matches[i]
        prev = matches[i-1]
        
        # Cek hanya jika Volume sama (jika ganti volume, reset urutan biasanya)
        if curr['vol'] == prev['vol']:
            diff = curr['page'] - prev['page']
            
            # KASUS 1: DUPLIKAT
            if diff == 0:
                errors.append({
                    'type': 'DUPLICATE',
                    'msg': f"Halaman {curr['page']} muncul ganda.",
                    'pos': f"Tag 1 di index {prev['start_index']}, Tag 2 di index {curr['start_index']}"
                })
            
            # KASUS 2: MUNDUR (NYEMPIL)
            elif diff < 0:
                errors.append({
                    'type': 'BACKWARD_JUMP',
                    'msg': f"Urutan mundur! Dari {prev['page']} ke {curr['page']}.",
                    'pos': f"Index {curr['start_index']}"
                })
            
            # KASUS 3: GAP (LOMPAT JAUH)
            elif diff > 1:
                errors.append({
                    'type': 'MISSING_GAP',
                    'msg': f"Halaman lompat. Dari {prev['page']} langsung ke {curr['page']}. (Hilang {diff-1} halaman)",
                    'pos': f"Index {curr['start_index']}"
                })
    
    return pd.DataFrame(errors)

# Jalankan Audit
df_errors = audit_corpus(raw_text)

# Simpan hasil ke CSV
output_csv = 'laporan_error_corpus2.csv'

if not df_errors.empty:
    # Simpan ke CSV
    df_errors.to_csv(output_csv, index=False, encoding='utf-8')
    
    # Print ke console
    print("Ditemukan Error dalam Struktur Halaman:")
    print(df_errors)
    print(f"\nTotal errors ditemukan: {len(df_errors)}")
    print(f"Hasil telah disimpan ke '{output_csv}'")
else:
    # Jika tidak ada error, buat CSV kosong dengan header
    pd.DataFrame(columns=['type', 'msg', 'pos']).to_csv(output_csv, index=False, encoding='utf-8')
    print("Struktur halaman terlihat rapi (sequential).")
    print(f"File CSV kosong telah dibuat: '{output_csv}'")

print("\nSelesai!")