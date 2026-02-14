from deep_translator import GoogleTranslator
import time

class QueryTranslator:
    def __init__(self, source='id', target='ar'):
        self.translator = GoogleTranslator(source=source, target=target)

    def translate(self, text):
        try:
            # Sleep sebentar agar tidak terkena rate limit jika pakai free API
            time.sleep(0.5) 
            return self.translator.translate(text)
        except Exception as e:
            print(f"Error translating '{text}': {e}")
            return text