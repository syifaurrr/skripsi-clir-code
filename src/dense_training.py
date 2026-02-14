import pandas as pd
from sentence_transformers import SentenceTransformer, InputExample, losses, models, datasets
from torch.utils.data import DataLoader
import os

def train_dense_model(triplets_path, model_name='distilbert-base-multilingual-cased', output_path='../models/fine_tuned_mbert'):
    """
    Melatih model multilingual menggunakan Contrastive Loss (MNRL).
    Input: CSV dengan kolom [query_indo, pos_doc_arab, neg_doc_arab]
    """
    print(f"Loading base model: {model_name}...")
    # Load model pre-trained
    word_embedding_model = models.Transformer(model_name, max_seq_length=512)
    pooling_model = models.Pooling(word_embedding_model.get_word_embedding_dimension())
    model = SentenceTransformer(modules=[word_embedding_model, pooling_model])

    # Load Data Tripel (Hasil JH-POLO)
    print("Loading training data...")
    df = pd.read_csv(triplets_path)
    
    # Konversi ke format InputExample
    train_examples = []
    for i, row in df.iterrows():
        # Struktur: [Anchor (Query Indo), Positive (Arab), Negative (Arab)]
        train_examples.append(InputExample(texts=[row['query'], row['pos_doc'], row['neg_doc']]))

    # Buat DataLoader
    train_dataloader = DataLoader(train_examples, shuffle=True, batch_size=16) # Sesuaikan batch_size dengan GPU Kaggle (T4 bisa 16 atau 32)

    # Definisi Loss: MultipleNegativesRankingLoss adalah standar untuk Contrastive Learning
    train_loss = losses.MultipleNegativesRankingLoss(model=model)

    # Mulai Training
    print("Starting fine-tuning...")
    model.fit(
        train_objectives=[(train_dataloader, train_loss)],
        epochs=3, # Biasanya 3-5 epoch cukup untuk fine-tuning
        warmup_steps=100,
        output_path=output_path,
        show_progress_bar=True
    )
    print(f"Model saved to {output_path}")

if __name__ == "__main__":
    # Contoh pemanggilan (pastikan path sesuai)
    train_dense_model('../data/training/triplets.csv')