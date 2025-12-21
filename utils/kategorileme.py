"""
Gider Kategorileme İşlemleri
"""
from typing import Optional
from openai import OpenAI
import streamlit as st
import os

# Gider kategorileri
GIDER_KATEGORILERI = {
    "kira": "Kira ve Aidat",
    "personel": "Personel ve Maaşlar",
    "elektrik": "Elektrik",
    "su": "Su",
    "dogalgaz": "Doğalgaz",
    "internet_telefon": "İnternet ve Telefon",
    "yakit": "Yakıt ve Ulaşım",
    "ofis_malzeme": "Ofis Malzemeleri",
    "hammadde": "Hammadde ve Malzeme",
    "pazarlama": "Pazarlama ve Reklam",
    "vergi": "Vergi ve Harçlar",
    "sigorta": "Sigorta",
    "bakim_onarim": "Bakım ve Onarım",
    "yemek": "Yemek ve İkram",
    "egitim": "Eğitim ve Danışmanlık",
    "banka": "Banka Masrafları",
    "diger": "Diğer"
}

# Kategorileme prompt'u
KATEGORILEME_PROMPT = """
Aşağıdaki gider bilgisine göre en uygun kategoriyi seç.

Satıcı: {satici_adi}
Açıklama: {aciklama}

Kategoriler:
- kira: Kira ve Aidat ödemeleri
- personel: Personel ve Maaş ödemeleri
- elektrik: Elektrik faturaları (TEDAŞ, Enerjisa, vb.)
- su: Su faturaları (İSKİ, ASKİ, vb.)
- dogalgaz: Doğalgaz faturaları (İGDAŞ, BOTAŞ, vb.)
- internet_telefon: İnternet ve Telefon faturaları (Turkcell, Vodafone, Türk Telekom, vb.)
- yakit: Benzin, motorin, ulaşım, otobüs, taksi
- ofis_malzeme: Kırtasiye, ofis malzemeleri
- hammadde: Üretim malzemeleri, hammadde alımları
- pazarlama: Reklam, Google Ads, Facebook Ads, sosyal medya, afiş, broşür
- vergi: Vergi ödemeleri, harçlar, noter masrafları
- sigorta: Sigorta primleri, kasko, trafik sigortası
- bakim_onarim: Tamir, bakım, servis, tadilat
- yemek: Restoran, yemek, market alışverişi, ikram
- egitim: Kurs, eğitim, danışmanlık, seminer
- banka: Havale masrafı, EFT ücreti, kredi kartı aidatı, faiz
- diger: Yukarıdaki kategorilere uymayan diğer giderler

Sadece kategori key'ini döndür (örn: "elektrik"). Başka bir şey yazma.
"""

# Anahtar kelime bazlı hızlı eşleştirme
KEYWORD_MAPPING = {
    "elektrik": ["elektrik", "enerji", "enerjisa", "tedaş", "ayedaş", "bedaş", "gediz"],
    "su": ["su", "iski", "aski", "izsu", "muski"],
    "dogalgaz": ["doğalgaz", "gaz", "igdaş", "botaş", "gazdaş", "izmirgaz"],
    "internet_telefon": ["internet", "telefon", "turkcell", "vodafone", "türk telekom", "telia", "superonline", "ttnet"],
    "yakit": ["benzin", "akaryakıt", "shell", "bp", "opet", "petrol", "total", "motorin", "lpg"],
    "kira": ["kira", "aidat", "site", "apartman"],
    "banka": ["banka", "eft", "havale", "komisyon", "faiz", "kredi"],
    "yemek": ["restoran", "lokanta", "cafe", "yemek", "market", "migros", "bim", "a101", "şok", "carrefour"],
    "ofis_malzeme": ["kırtasiye", "ofis", "kalem", "kağıt", "toner", "kartuş"],
    "pazarlama": ["reklam", "google ads", "facebook", "instagram", "afiş", "broşür", "tanıtım"],
    "sigorta": ["sigorta", "kasko", "trafik", "sağlık sigortası"],
    "vergi": ["vergi", "kdv", "mtv", "harç", "noter", "damga"],
    "bakim_onarim": ["tamir", "bakım", "servis", "onarım", "tadilat"],
    "egitim": ["eğitim", "kurs", "seminer", "danışmanlık", "coaching"],
    "personel": ["maaş", "ücret", "personel", "sgk", "işçi", "çalışan"],
    "hammadde": ["hammadde", "malzeme", "üretim", "stok"]
}


def get_openai_client() -> Optional[OpenAI]:
    """OpenAI client oluşturur."""
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


def keyword_kategori_bul(metin: str) -> Optional[str]:
    """
    Anahtar kelime bazlı hızlı kategori eşleştirmesi yapar.

    Args:
        metin: Aranacak metin

    Returns:
        Eşleşen kategori key'i veya None
    """
    metin_lower = metin.lower()

    for kategori, keywords in KEYWORD_MAPPING.items():
        for keyword in keywords:
            if keyword.lower() in metin_lower:
                return kategori

    return None


def kategori_tahmin_et(satici_adi: str, aciklama: str = "") -> str:
    """
    Gider için uygun kategoriyi tahmin eder.

    Args:
        satici_adi: Satıcı/firma adı
        aciklama: Gider açıklaması

    Returns:
        Kategori key'i
    """
    # Önce anahtar kelime bazlı hızlı eşleştirme dene
    birlesik_metin = f"{satici_adi} {aciklama}"
    keyword_sonuc = keyword_kategori_bul(birlesik_metin)

    if keyword_sonuc:
        return keyword_sonuc

    # Eğer anahtar kelime bulunamazsa GPT ile tahmin et
    client = get_openai_client()

    if not client:
        return "diger"  # API yoksa varsayılan kategori

    try:
        prompt = KATEGORILEME_PROMPT.format(
            satici_adi=satici_adi or "Belirtilmemiş",
            aciklama=aciklama or "Belirtilmemiş"
        )

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "user", "content": prompt}
            ],
            max_tokens=50,
            temperature=0
        )

        kategori = response.choices[0].message.content.strip().lower()

        # Geçerli bir kategori mi kontrol et
        if kategori in GIDER_KATEGORILERI:
            return kategori
        else:
            return "diger"

    except Exception:
        return "diger"


def kategori_adi_getir(kategori_key: str) -> str:
    """
    Kategori key'inden okunabilir adı döndürür.

    Args:
        kategori_key: Kategori anahtarı

    Returns:
        Kategori adı
    """
    return GIDER_KATEGORILERI.get(kategori_key, "Diğer")


def tum_kategoriler() -> dict:
    """Tüm kategorileri döndürür."""
    return GIDER_KATEGORILERI.copy()
