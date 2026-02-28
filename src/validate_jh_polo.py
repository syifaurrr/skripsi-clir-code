import pandas as pd
import numpy as np
from difflib import SequenceMatcher


# 1. Load Data
df_docs = pd.read_csv('../data/raw/fathul_muin.csv')

def get_longest_common_substring(s1, s2):
    match = SequenceMatcher(None, s1, s2).find_longest_match(0, len(s1), 0, len(s2))
    return match.size

def verify_jhpolo_pairs(df):
    pairs = []
    used_docs = set()

    print("Memulai proses seleksi pasangan dokumen untuk VERIFIKASI...")
    
    for idx, row in df.iterrows():
        query_id = str(row['docno'])
        query_text = str(row['text'])
        
        # Syarat 1: Panjang min 150 karakter & belum terpakai
        if len(query_text) < 150 or query_id in used_docs:
            continue
            
        tokenized_query = query_text.split()
        scores = bm25.get_scores(tokenized_query)
        top_n_indices = np.argsort(scores)[::-1][:21]
        
        query_score = scores[idx] # Skor dokumen terhadap dirinya sendiri
        
        for cand_idx in top_n_indices:
            cand_id = str(df.iloc[cand_idx]['docno'])
            cand_text = str(df.iloc[cand_idx]['text'])
            cand_score = scores[cand_idx]
            
            # Lewati jika dokumen yang sama atau sudah terpakai
            if cand_id == query_id or cand_id in used_docs: continue
            
            # Syarat 2: Rasio Skor BM25 tidak boleh > 0.65 (Terlalu mirip)
            score_ratio = cand_score / (query_score + 1e-9)
            if score_ratio > 0.65: continue
            
            # Syarat 3: Kandidat negatif minimal 150 karakter
            if len(cand_text) < 150: continue
            
            # Syarat 4: LCS Ratio tidak boleh > 60% (Menghindari duplikat parsial)
            lcs_size = get_longest_common_substring(query_text, cand_text)
            lcs_ratio = lcs_size / len(query_text)
            if lcs_ratio > 0.60: continue
            
            # Jika lolos semua filter, simpan BUKTI METRIKNYA
            pairs.append({
                'pos_id': query_id,
                'neg_id': cand_id,
                'bm25_pos_score': round(query_score, 4),
                'bm25_neg_score': round(cand_score, 4),
                'score_ratio': round(score_ratio, 4),
                'lcs_ratio': round(lcs_ratio, 4),
                # Cuplikan teks untuk dicek manual
                'pos_text_snippet': query_text[:80] + "...",
                'neg_text_snippet': cand_text[:80] + "..." 
            })
            
            used_docs.add(query_id)
            used_docs.add(cand_id)
            break 
            
    return pd.DataFrame(pairs)

# Eksekusi dan Simpan
df_verify = verify_jhpolo_pairs(df_docs)
df_verify.to_csv('jhpolo_verification_pairs.csv', index=False)

print(f"\nBerhasil membentuk {len(df_verify)} pasangan dokumen.")
print("File 'jhpolo_verification_pairs.csv' telah disimpan di direktori /kaggle/working.")
print("\n=== PREVIEW 5 PASANGAN PERTAMA ===")
display(df_verify.head())