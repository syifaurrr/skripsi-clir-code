import re
import pyarabic.araby as araby

def normalize_arabic(text):
    """
    Melakukan normalisasi teks Arab sesuai Skenario 1.
    """
    if not isinstance(text, str):
        return ""

    # 1. Hapus Harakat (Tashkeel)
    text = araby.strip_tashkeel(text)

    # 2. Hapus Tatweel (Kasyida) - Contoh: مـــــرحـــــبــــا jadi مرحبا
    text = araby.strip_tatweel(text)

    # 3. Unifikasi Alif (mengubah أ, إ, آ menjadi ا)
    text = araby.normalize_alef(text)

    # 4. Unifikasi Ya / Alif Maqsura (mengubah ى menjadi ي atau sebaliknya sesuai kebutuhan)
    # Di pyarabic, normalize_teh_marbuta mengubah ة jadi ه
    # Kita buat custom untuk Ya
    text = re.sub(r'[ى]', 'ي', text) 
    text = re.sub(r'ؤ', 'و', text) # Normalisasi Hamzah umum
    text = re.sub(r'ئ', 'ي', text)

    return text

def light_stemming(text):
    """
    Light Stemming: Membuang imbuhan umum (prefixes/suffixes) 
    tanpa mengubah ke root word (akar kata).
    """
    # Daftar prefixes umum dalam Fiqih/Arab (wa, al, bi, lil, dll)
    # Hati-hati: Regex ini sederhana. Untuk hasil lebih akurat bisa pakai library 'Tashaphyne'
    prefixes = [
        r"^ال", r"^و", r"^ف", r"^ب", r"^ك", r"^ل", r"^لل"
    ]
    
    # Daftar suffixes umum (at, un, an, in, hum, ha, etc)
    suffixes = [
        r"ة$", r"ه$", r"ي$", r"نا$", r"كم$", r"هم$", r"هن$", r"ها$", 
        r"ون$", r"ين$", r"ان$", r"ات$"
    ]
    
    words = text.split()
    cleaned_words = []
    
    for word in words:
        original = word
        # Hapus prefix
        for p in prefixes:
            if re.match(p, word) and len(word) > 3: # Syarat panjang agar tidak merusak kata pendek
                word = re.sub(p, "", word, count=1)
        
        # Hapus suffix
        for s in suffixes:
            if re.search(s, word) and len(word) > 3:
                word = re.sub(s, "", word, count=1)
                
        cleaned_words.append(word)
        
    return " ".join(cleaned_words)

def preprocess_pipeline(text):
    """Fungsi utama yang dipanggil oleh PyTerrier"""
    text = normalize_arabic(text)
    text = light_stemming(text)
    return text