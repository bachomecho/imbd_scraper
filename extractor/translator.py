import deepl
import os

class DeeplTranslator:
    _translator = None
    @classmethod
    def get_translator(cls):
        if cls._translator is None:
            api_key = os.getenv("DEEPL_API_KEY")
            cls._translator = deepl.Translator(api_key)
        return cls._translator
    @classmethod
    def initialize_translator(cls):
        return cls.get_translator()