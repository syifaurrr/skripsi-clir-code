import pyterrier as pt
import pandas as pd
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer

class FaissRetriever(pt.Transformer):
    """
    Custom PyTerrier Transformer untuk Dense Retrieval menggunakan FAISS.
    """
    def __init__(self, model_path, index_path, doc_df=None, batch_size=32):
        self.model = SentenceTransformer(model_path)
        self.index = None
        self.index_path = index_path
        self.doc_map = {} # Mapping dari internal ID FAISS ke docno asli
        self.batch_size = batch_size
        
        # Jika index belum ada, kita buat (Indexing)
        if doc_df is not None:
            self._index_docs(doc_df)
        else:
            self._load_index()

    def _index_docs(self, doc_df):
        print("Encoding documents for FAISS index...")
        # doc_df harus punya kolom ['docno', 'text']
        docs = doc_df['text'].tolist()
        docnos = doc_df['docno'].tolist()
        
        # Encode semua dokumen Arab ke vektor
        embeddings = self.model.encode(docs, batch_size=self.batch_size, show_progress_bar=True, convert_to_numpy=True)
        
        # Normalisasi vektor untuk Cosine Similarity (Dot Product di FAISS)
        faiss.normalize_L2(embeddings)
        
        # Buat Index FAISS (FlatInnerProduct = Cosine Similarity jika vektor ternormalisasi)
        dim = embeddings.shape[1]
        self.index = faiss.IndexFlatIP(dim)
        self.index.add(embeddings)
        
        # Simpan mapping docno
        self.doc_map = {i: docno for i, docno in enumerate(docnos)}
        
        # Simpan index ke disk (opsional, tapi disarankan)
        print(f"Saving index to {self.index_path}...")
        faiss.write_index(self.index, self.index_path + ".faiss")
        # Simpan docmap (bisa pakai pickle, di sini sederhana saja)
        pd.DataFrame(list(self.doc_map.items()), columns=['id', 'docno']).to_csv(self.index_path + "_map.csv", index=False)

    def _load_index(self):
        print(f"Loading index from {self.index_path}...")
        self.index = faiss.read_index(self.index_path + ".faiss")
        map_df = pd.read_csv(self.index_path + "_map.csv")
        self.doc_map = dict(zip(map_df['id'], map_df['docno']))

    def transform(self, queries):
        """
        Melakukan retrieval saat eksperimen dijalankan.
        Input: DataFrame queries (qid, query)
        Output: DataFrame hasil (qid, docno, score, rank)
        """
        # Encode Queries (Indo) -> Vector
        q_texts = queries['query'].tolist()
        q_embeddings = self.model.encode(q_texts, batch_size=self.batch_size, show_progress_bar=False, convert_to_numpy=True)
        faiss.normalize_L2(q_embeddings)
        
        # Search di FAISS (Top-1000)
        k = 1000
        scores, ids = self.index.search(q_embeddings, k)
        
        results = []
        for i, qid in enumerate(queries['qid']):
            for j in range(k):
                doc_idx = ids[i][j]
                if doc_idx != -1: # Valid result
                    results.append({
                        'qid': str(qid),
                        'docno': self.doc_map[doc_idx],
                        'score': scores[i][j],
                        'rank': j + 1
                    })
        
        return pd.DataFrame(results)