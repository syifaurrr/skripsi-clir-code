import pandas as pd
import numpy as np
import os
from difflib import SequenceMatcher
from rank_bm25 import BM25Okapi 

# ============================================
# 1. LOAD DATA & INIT BM25
# ============================================
print("Memuat data dan inisialisasi BM25...")
# Pastikan path ini sesuai dengan struktur direktori Kaggle Anda
df_docs = pd.read_csv('../data/raw/fathul_muin.csv')

# Tokenisasi sederhana untuk BM25
tokenized_corpus = [str(doc).split() for doc in df_docs['text']]
bm25 = BM25Okapi(tokenized_corpus)
print(f"Index BM25 siap untuk {len(df_docs)} dokumen.\n")

# ============================================
# 2. FUNGSI SELEKSI PASANGAN (RANDOMIZED & REPRODUCIBLE)
# ============================================
def get_longest_common_substring(s1, s2):
    match = SequenceMatcher(None, s1, s2).find_longest_match(0, len(s1), 0, len(s2))
    return match.size

def select_randomized_jhpolo_pairs(df):
    pairs = []
    used_docs = set()

    print("Memulai proses seleksi pasangan dokumen (RANDOMIZED)...")
    
    # Mengacak urutan baris dengan seed 42 untuk menjamin Reproducibility
    df_shuffled = df.sample(frac=1, random_state=42).reset_index(drop=True)
    
    for idx, row in df_shuffled.iterrows():
        query_id = str(row['docno'])
        query_text = str(row['text'])
        
        if len(query_text) < 150 or query_id in used_docs:
            continue
            
        tokenized_query = query_text.split()
        scores = bm25.get_scores(tokenized_query)
        
        # Cari skor BM25 dari dokumen asli
        original_idx = df[df['docno'].astype(str) == query_id].index[0]
        query_score = scores[original_idx] 
        
        top_n_indices = np.argsort(scores)[::-1][:21]
        
        for cand_idx in top_n_indices:
            cand_id = str(df.iloc[cand_idx]['docno'])
            cand_text = str(df.iloc[cand_idx]['text'])
            cand_score = scores[cand_idx]
            
            if cand_id == query_id or cand_id in used_docs: continue
            
            # Filter Rasio Skor
            score_ratio = cand_score / (query_score + 1e-9)
            if score_ratio > 0.65: continue
            
            # Filter Panjang Teks
            if len(cand_text) < 150: continue
            
            # Filter LCS (Tumpang tindih teks)
            lcs_size = get_longest_common_substring(query_text, cand_text)
            lcs_ratio = lcs_size / len(query_text)
            if lcs_ratio > 0.60: continue
            
            # Simpan SEMUA data (Teks dan Skor)
            pairs.append({
                'pos_id': query_id,
                'pos_text': query_text,
                'neg_id': cand_id,
                'neg_text': cand_text,
                'bm25_pos_score': round(query_score, 4),
                'bm25_neg_score': round(cand_score, 4),
                'score_ratio': round(score_ratio, 4),
                'lcs_ratio': round(lcs_ratio, 4)
            })
            
            used_docs.add(query_id)
            used_docs.add(cand_id)
            break 
            
    return pd.DataFrame(pairs)

# Eksekusi seleksi
df_pairs = select_randomized_jhpolo_pairs(df_docs)
print(f"Berhasil membentuk {len(df_pairs)} pasangan dokumen unik.\n")

# ============================================
# 3. PENYIMPANAN DAN PEMBAGIAN FILE (CHUNKING)
# ============================================

# A. Simpan File Verifikasi Utama (Berisi daftar lengkap + skor metriknya)
verification_file = 'jhpolo_verification_full.csv'
df_pairs.to_csv(verification_file, index=False)
print(f"✅ File verifikasi metrik disimpan: {verification_file}")

# B. Siapkan kolom yang hanya dibutuhkan oleh Gemini Gem
# Kita buang skor BM25/LCS agar file lebih ringan dan prompt LLM tidak bingung
df_gemini_input = df_pairs[['pos_id', 'pos_text', 'neg_id', 'neg_text']]

# C. Pecah menjadi beberapa file dengan isi maksimal 40 baris
chunk_size = 40
num_chunks = len(df_gemini_input) // chunk_size + (1 if len(df_gemini_input) % chunk_size != 0 else 0)

print(f"\nMemecah file input Gemini menjadi {num_chunks} bagian (Maks {chunk_size} pasang/file):")

for i in range(num_chunks):
    start_idx = i * chunk_size
    end_idx = start_idx + chunk_size
    
    # Ambil potongan 40 baris
    chunk = df_gemini_input.iloc[start_idx:end_idx]
    
    # Simpan ke CSV baru
    filename = f'gemini_input_batch_{i+1}.csv'
    chunk.to_csv(filename, index=False)
    print(f"  -> Disimpan: {filename} (berisi {len(chunk)} pasangan)")

print("\n🎉 SELESAI! Silakan download file gemini_input_batch_*.csv dari folder /kaggle/working/ untuk diunggah ke Gemini Gems Anda.")