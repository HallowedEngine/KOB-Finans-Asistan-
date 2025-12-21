"""
KOBİ Finans Asistanı - Konfigürasyon Dosyası
"""
import os
from dotenv import load_dotenv

load_dotenv()

# API Ayarları
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MODEL_VISION = "gpt-4o"
MODEL_CHAT = "gpt-4o"

# Veritabanı Ayarları
DATABASE_PATH = "data/giderler.db"

# Uygulama Ayarları
APP_NAME = "KOBİ Finans Asistanı"
APP_VERSION = "1.0.0"
DEFAULT_TARIH_ARALIK = 30  # gün

# Sayfa Ayarları
PAGE_ICON = "💼"
LAYOUT = "wide"
