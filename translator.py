import deepl
import os
from dotenv import load_dotenv

class DeeplTranslator:
    _instance = None
    def __new__(cls):
        if not cls._instance:
            return super(DeeplTranslator, cls).__new__(cls)
        return cls._instance

    def __init__(self, api_key: str):
        self.api_key = os.getenv("DEEPL_API_KEY")

    def initialize_translator(self):
        load_dotenv('.env')
        return deepl.Translator(os.getenv("DEEPL_API_KEY"))