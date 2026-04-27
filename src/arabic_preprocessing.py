import re
import pyarabic.araby as araby
from tashaphyne.stemming import ArabicLightStemmer

# Inisialisasi objek stemmer Tashaphyne satu kali di luar fungsi agar lebih cepat
ArListem = ArabicLightStemmer()

# def normalize_arabic(text):
#     """
#     Melakukan normalisasi teks Arab secara komprehensif untuk Information Retrieval.
#     """
#     if not isinstance(text, str):
#         return ""

#     # 1. Hapus Harakat (Tashkeel) dan Kasyida (Tatweel) - WAJIB UNTUK IR
#     text = araby.strip_tashkeel(text)
#     text = araby.strip_tatweel(text)

#     # 2. Unifikasi Alif dan Alif Wasla
#     text = re.sub("[إأآاٱ]", "ا", text)
    
#     # 3. Unifikasi Alif Maqsura ke Ya
#     text = re.sub("ى", "ي", text)
    
#     # 4. Unifikasi seluruh wadah Hamzah menjadi Hamzah Mandiri
#     text = re.sub("ؤ", "ء", text)
#     text = re.sub("ئ", "ء", text)
    
#     # 5. Unifikasi Ta' Marbutah menjadi Ha'
#     text = re.sub("ة", "ه", text)
    
#     # 6. Normalisasi Karakter Persia/Pegon/Noise OCR ke Arab Standar
#     text = re.sub("گ", "ك", text)
#     text = re.sub("ڤ", "ف", text)
#     text = re.sub("چ", "ج", text)
#     text = re.sub("پ", "ب", text)
#     text = re.sub("ڜ", "ش", text)
#     text = re.sub("ڪ", "ك", text)
#     text = re.sub("ڧ", "ق", text)

#     return text
import re
import pyarabic.araby as araby
# Asumsi Anda mengimpor modul normalize dari pyarabic
# from pyarabic import normalize as arabnorm 

def normalize_bm25(text):
    """
    Normalisasi agresif khusus untuk jalur Sparse Retrieval (BM25).
    """
    if not isinstance(text, str):
        return ""

    # 1. Gunakan fungsi standar IR PyArabic (Hamza, Alif, Ta' Marbutah, Harakat)
    # Teks akan menjadi seragam secara bentuk dasar
    text = araby.normalize_searchtext(text) 
    
    # 2. Injeksi pembersih noise khusus korpus turats / OCR
    text = re.sub(r'[گڪ]', 'ك', text)
    text = re.sub(r'ڤ', 'ف', text)
    text = re.sub(r'چ', 'ج', text)
    text = re.sub(r'پ', 'ب', text)
    text = re.sub(r'ڜ', 'ش', text)
    text = re.sub(r'ڧ', 'ق', text)
    text = re.sub(r'ٱ', 'ا', text) # Tambahan Alif Wasla jika terlewat PyArabic

    return text

def normalize_dense(text):
    """
    Normalisasi minimalis khusus untuk jalur Dense Retrieval.
    Menjaga integritas subword tokenizer.
    """
    if not isinstance(text, str):
        return ""

    # Hanya hapus harakat dan kasyida
    text = araby.strip_tashkeel(text)
    text = araby.strip_tatweel(text)
    
    return text

def light_stemming(text):
    """
    Light Stemming menggunakan pustaka Tashaphyne sesuai proposal skripsi.
    Membuka imbuhan (prefixes/suffixes) tanpa merusak struktur akar kata.
    """
    if not isinstance(text, str):
        return ""
        
    words = text.split()
    cleaned_words = []
    
    for word in words:
        # Gunakan fungsi light_stem dari Tashaphyne
        stemmed_word = ArListem.light_stem(word)
        cleaned_words.append(stemmed_word)
        
    return " ".join(cleaned_words)

def preprocess_pipeline(text):
    """Fungsi utama yang dipanggil oleh PyTerrier"""
    # Langkah 1: Normalisasi karakter dasar
    text = normalize_arabic(text)
    # Langkah 2: Light Stemming dengan Tashaphyne
    text = light_stemming(text)
    return text
