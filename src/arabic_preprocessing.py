import re
import pyarabic.araby as araby
from tashaphyne.stemming import ArabicLightStemmer

# Inisialisasi objek stemmer Tashaphyne satu kali di luar fungsi agar lebih cepat
ArListem = ArabicLightStemmer()

def normalize_arabic(text):
    """
    Melakukan normalisasi teks Arab sesuai Skenario 1.
    """
    if not isinstance(text, str):
        return ""

    # 1. Hapus Harakat (Tashkeel)
    text = araby.strip_tashkeel(text)

    # 2. Hapus Tatweel (Kasyida)
    text = araby.strip_tatweel(text)

    # 3. Unifikasi Alif (mengubah أ, إ, آ menjadi ا)
    text = araby.normalize_alef(text)

    # 4. Unifikasi Ya / Hamzah
    text = re.sub(r'[ى]', 'ي', text) 
    text = re.sub(r'ؤ', 'و', text) 
    text = re.sub(r'ئ', 'ي', text)

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
