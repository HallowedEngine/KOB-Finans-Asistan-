"""
GPT-4o Vision ile Belge Okuma İşlemleri
"""
import base64
import json
from typing import Dict, Any, Optional
from openai import OpenAI
import streamlit as st

# Belge okuma prompt'u
BELGE_OKUMA_PROMPT = """
Bu bir Türk ticari belgesidir (fatura, fiş, dekont veya makbuz olabilir).
Lütfen aşağıdaki bilgileri JSON formatında çıkar:

{
  "belge_tipi": "fatura|fiş|dekont|makbuz|diğer",
  "tarih": "YYYY-MM-DD formatında (örn: 2024-01-15)",
  "satici_adi": "firma veya işletme adı",
  "vergi_no": "varsa vergi numarası, yoksa null",
  "toplam_tutar": sayısal değer (sadece rakam, TL yazmadan),
  "kdv_tutari": sayısal değer veya null,
  "odeme_yontemi": "nakit|kart|havale|belirsiz",
  "aciklama": "belgede yazanların kısa özeti",
  "kalemler": [
    {"urun": "ürün adı", "adet": sayı, "birim_fiyat": sayı, "toplam": sayı}
  ]
}

Önemli kurallar:
1. Eğer bir bilgiyi okuyamıyorsan null yaz
2. Türkçe karakterleri doğru kullan (ş, ı, ğ, ü, ö, ç)
3. Tutarları nokta ile ayır (örn: 1234.56), binlik ayracı kullanma
4. Tarih formatı mutlaka YYYY-MM-DD olmalı
5. Sadece JSON döndür, başka açıklama yazma
"""


def get_openai_client() -> Optional[OpenAI]:
    """OpenAI client oluşturur."""
    import os
    api_key = None

    # Önce Streamlit secrets'tan dene
    try:
        api_key = st.secrets.get("OPENAI_API_KEY")
    except Exception:
        pass

    # Bulunamadıysa environment variable'dan dene
    if not api_key:
        api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        return None

    return OpenAI(api_key=api_key)


def encode_image_to_base64(image_bytes: bytes) -> str:
    """Görüntüyü base64 formatına çevirir."""
    return base64.b64encode(image_bytes).decode('utf-8')


def belge_oku(image_bytes: bytes) -> Dict[str, Any]:
    """
    Belge görüntüsünden bilgi çıkarır.

    Args:
        image_bytes: Görüntü dosyasının byte içeriği

    Returns:
        Çıkarılan bilgileri içeren sözlük
    """
    client = get_openai_client()

    if not client:
        return {
            "hata": True,
            "mesaj": "OpenAI API anahtarı bulunamadı. Lütfen .env dosyasını veya Streamlit secrets'ı kontrol edin."
        }

    try:
        # Görüntüyü base64'e çevir
        base64_image = encode_image_to_base64(image_bytes)

        # GPT-4o Vision API'ye gönder
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": BELGE_OKUMA_PROMPT
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}",
                                "detail": "high"
                            }
                        }
                    ]
                }
            ],
            max_tokens=1500
        )

        # Yanıtı al
        content = response.choices[0].message.content.strip()

        # JSON bloğunu temizle (eğer markdown formatında geldiyse)
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]

        content = content.strip()

        # JSON parse et
        result = json.loads(content)
        result["hata"] = False

        return result

    except json.JSONDecodeError as e:
        return {
            "hata": True,
            "mesaj": f"JSON parse hatası: {str(e)}",
            "ham_yanit": content if 'content' in locals() else None
        }
    except Exception as e:
        return {
            "hata": True,
            "mesaj": f"Belge okuma hatası: {str(e)}"
        }


def pdf_to_images(pdf_bytes: bytes) -> list:
    """
    PDF dosyasını görüntülere çevirir.
    Not: Bu basit bir implementasyon, pdf2image kütüphanesi gerektirir.

    Args:
        pdf_bytes: PDF dosyasının byte içeriği

    Returns:
        Görüntü byte listesi
    """
    try:
        # PDF'in ilk sayfasını oku
        # Bu basit implementasyonda sadece ilk sayfa destekleniyor
        # Tam destek için pdf2image veya PyMuPDF kullanılabilir
        return [pdf_bytes]  # Placeholder - gerçek implementasyonda dönüştürme yapılmalı
    except Exception as e:
        return []
