import os
import re
import pandas as pd

def preprocess_fathul_muin(text):
    # 1. Menghilangkan Tag HTML
    text = re.sub(r'<[^>]+>', '', text)
    
    # 2. Sambungkan baris lanjutan (yang diawali ~~) ke baris sebelumnya
    text = re.sub(r'\n~~', ' ', text)
    
    # 3. Menghilangkan deretan titik beruntun (". . . . ." atau "......")
    text = re.sub(r'(\s*\.\s*){3,}', ' ', text)
    
    # 4. Menghilangkan simbol khusus
    text = text.replace('~~', ' ')
    text = text.replace('~', '')   # hapus sisa ~ tunggal
    text = text.replace('#', '')
    text = text.replace('*', '')
    
    # 5. Menghilangkan deretan 0 berulang (000000...)
    text = re.sub(r'0{2,}', '', text)
    
    # 6. Menghilangkan identifier halaman (PageV01P147, ms002, dsb)
    text = re.sub(r'PageV\d+P\d+', '', text)
    text = re.sub(r'ms\d+', '', text)
    
    # 7. Bersihkan spasi & baris kosong berlebih
    text = re.sub(r' +', ' ', text)
    text = re.sub(r'\n +', '\n', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    return text.strip()

def load_and_clean_corpus(folder_path):
    corpus_data = []
    file_list = sorted([f for f in os.listdir(folder_path) if f.endswith('.txt')])
    
    print(f"Memproses {len(file_list)} file...")
    
    for filename in file_list:
        file_path = os.path.join(folder_path, filename)
        
        with open(file_path, 'r', encoding='utf-8') as file:
            raw_content = file.read()
            clean_content = preprocess_fathul_muin(raw_content)
            doc_id = filename.replace('.txt', '')
            
            corpus_data.append({
                "doc_no": doc_id,
                "text_arabic": clean_content
            })
    
    return pd.DataFrame(corpus_data)

# Eksekusi - menggunakan path relatif ke folder pages
script_dir = os.path.dirname(os.path.abspath(__file__))
# pages_folder = os.path.join(script_dir, 'pages')
pages_folder = os.path.join(script_dir, 'fath_muin_pages')

df_korpus = load_and_clean_corpus(pages_folder)

# Menyimpan ke CSV
# output_file = 'data/raw/fathul_muin.csv'
output_file = os.path.join(script_dir, 'fathul_muin.csv')

df_korpus.to_csv(output_file, index=False, encoding='utf-8')

print(f"\nCSV berhasil dibuat: {output_file}")
print(f"Total dokumen: {len(df_korpus)}")
print("\nPreview data:")
print(df_korpus.head())
