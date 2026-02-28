import pandas as pd
import numpy as np
import os
import time
import json
import random
from difflib import SequenceMatcher
from openai import OpenAI  
from rank_bm25 import BM25Okapi 
from dotenv import load_dotenv

load_dotenv()

# ============================================
# 1. LOAD DATA & INIT BM25
# ============================================
print("Memuat data dan inisialisasi BM25...")
df_docs = pd.read_csv('../data/raw/fathul_muin.csv')

# Tokenisasi sederhana untuk BM25
tokenized_corpus = [str(doc).split() for doc in df_docs['text']]
bm25 = BM25Okapi(tokenized_corpus)
print(f"Index BM25 siap untuk {len(df_docs)} dokumen.\n")

# ============================================
# 2. FUNGSI SELEKSI PASANGAN (RANDOMIZED)
# ============================================
def get_longest_common_substring(s1, s2):
    match = SequenceMatcher(None, s1, s2).find_longest_match(0, len(s1), 0, len(s2))
    return match.size

def select_randomized_jhpolo_pairs(df):
    pairs = []
    used_docs = set()

    print("Memulai proses seleksi pasangan dokumen (RANDOMIZED)...")
    
    # Mengacak urutan baris agar topik terdistribusi merata
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
            
            score_ratio = cand_score / (query_score + 1e-9)
            if score_ratio > 0.65: continue
            if len(cand_text) < 150: continue
            
            lcs_size = get_longest_common_substring(query_text, cand_text)
            lcs_ratio = lcs_size / len(query_text)
            if lcs_ratio > 0.60: continue
            
            # Simpan SEMUA data (Teks untuk LLM, Skor untuk Verifikasi)
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
print(f"Berhasil membentuk {len(df_pairs)} pasangan dokumen unik.")

# (Opsional) Simpan daftar pasangan untuk keperluan verifikasi/arsip
df_pairs.to_csv('jhpolo_randomized_pairs_with_scores.csv', index=False)
print("File verifikasi 'jhpolo_randomized_pairs_with_scores.csv' telah disimpan.\n")


# ============================================
# 3. LLM GENERATION MENGGUNAKAN KIMI AI
# ============================================
client = OpenAI(
    api_key=os.environ.get("MOONSHOT_API_KEY"), 
    base_url="https://api.moonshot.ai/v1"  
)

MODEL_NAME = "kimi-k2.5" 

def generate_jhpolo_queries(df_pairs):
    training_triplets = []
    
    system_prompt = """
    Tugas: Buat 5 kueri faktual Bahasa Indonesia berdasarkan dua teks Arab Fiqih (Teks A dan Teks B).
    
    Aturan Keketatan (JH-POLO):
    1. Kueri HARUS bisa dijawab secara spesifik oleh Teks A.
    2. Kueri HARUS TIDAK bisa dijawab (atau akan menyesatkan) jika menggunakan Teks B.
    3. Teks A dan B memiliki topik yang mirip, fokuslah pada perbedaan detail (syarat khusus, hukum, atau pengecualian) di Teks A.
    
    Komposisi Kueri:
    - Buat tepat 2 buah Kueri Tipe 1 (Santri): Berupa frasa pendek/kata kunci, teknis, menggunakan istilah Fiqih, TANPA kata tanya.
    - Buat tepat 3 buah Kueri Tipe 2 (Awam): Berupa kalimat tanya lengkap, menggunakan bahasa sehari-hari, hindari istilah teknis Arab yang tidak natural.
    
    Output HARUS berupa format JSON murni seperti struktur di bawah ini, tanpa awalan/akhiran apapun:
    {
      "tipe_1": [
        "kueri tipe 1 pertama",
        "kueri tipe 1 kedua"
      ],
      "tipe_2": [
        "kueri tipe 2 pertama",
        "kueri tipe 2 kedua",
        "kueri tipe 2 ketiga"
      ]
    }
    """

    for i, row in df_pairs.iterrows():
        user_content = f"{system_prompt}\n\nTEKS A (Relevan):\n{row['pos_text']}\n\nTEKS B (Non-Relevan):\n{row['neg_text']}"
        
        try:
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {"role": "system", "content": "Anda adalah ahli Fiqih yang ahli dalam membuat kueri pencarian."},
                    {"role": "user", "content": user_content}
                ],
                temperature=0.6, 
                max_tokens=4096,
            )
            
            response_text = response.choices[0].message.content
            clean_json = response_text.replace('```json', '').replace('```', '').strip()
            
            # Memastikan parsing JSON aman
            try:
                queries = json.loads(clean_json)
            except json.JSONDecodeError:
                print(f"❌ Gagal mem-parsing JSON pada baris {i}. Melewati baris ini.")
                continue

            t1_list = queries.get('tipe_1', [])
            t2_list = queries.get('tipe_2', [])
            
            training_triplets.append({
                'pos_docno': row['pos_id'],
                'neg_docno': row['neg_id'],
                'query_t1_1': t1_list[0] if len(t1_list) > 0 else '',
                'query_t1_2': t1_list[1] if len(t1_list) > 1 else '',
                'query_t2_1': t2_list[0] if len(t2_list) > 0 else '',
                'query_t2_2': t2_list[1] if len(t2_list) > 1 else '',
                'query_t2_3': t2_list[2] if len(t2_list) > 2 else ''
            })
            
            print(f"✅ Generated triplet {i+1}/{len(df_pairs)} (pos: {row['pos_id']}, neg: {row['neg_id']})")
            time.sleep(1) # Jeda aman Kimi API
            
        except Exception as e:
            print(f"❌ Error API pada baris {i} (pos_id: {row['pos_id']}): {e}")
            
    return pd.DataFrame(training_triplets)

# ============================================
# 4. EKSEKUSI UTAMA
# ============================================
print("Memulai proses generasi kueri...")
# [!] UBAH INI: .head(3) digunakan untuk testing awal. 
# Jika sudah yakin, hapus .head(3) untuk mengenerate seluruh data.
df_final_training = generate_jhpolo_queries(df_pairs.head(3)) 

# Menyimpan hasil akhir (Kueri Sintetis)
df_final_training.to_csv('jh_polo_queries_final.csv', index=False)
print("\n🎉 SELESAI! Data latih berhasil disimpan ke 'jh_polo_queries_final.csv'")