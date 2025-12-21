"""
Türk Vergi ve Muhasebe Bilgi Bankası
"""
from typing import Optional, List
from openai import OpenAI
import streamlit as st
import os

# Muhasebe bilgi bankası
MUHASEBE_CONTEXT = """
# Türkiye Vergi ve Muhasebe Temel Bilgileri (2024-2025)

## KDV Oranları
- Genel oran: %20
- İndirimli oran: %10 (temel gıda, konaklama, sağlık hizmetleri, ulaşım)
- Özel indirimli: %1 (tarım ürünleri, gazete, dergi, kitap)

## Önemli Vergi Tarihleri
- KDV beyannamesi: Her ayın 28'ine kadar (önceki ay için)
- Muhtasar beyanname: 3 ayda bir, takip eden ayın 26'sına kadar
- Geçici vergi: 3 ayda bir (Şubat, Mayıs, Ağustos, Kasım'ın 17'si)
- Yıllık gelir vergisi: Mart ayı sonuna kadar
- Yıllık kurumlar vergisi: Nisan ayı sonuna kadar
- SGK primi: Her ayın sonuna kadar
- Ba-Bs formları: Takip eden ayın sonuna kadar

## Gelir Vergisi Dilimleri (2024)
- 0 - 110.000 TL: %15
- 110.000 - 230.000 TL: %20
- 230.000 - 580.000 TL: %27
- 580.000 - 3.000.000 TL: %35
- 3.000.000 TL üzeri: %40

## Gider Yazma Kuralları
- İşle ilgili tüm harcamalar gider yazılabilir
- Fatura veya fiş şart (5.000 TL altı için fiş yeterli)
- Araç giderleri: İşletme adına kayıtlıysa %70'i gider yazılabilir
- Binek araç KDV'si indirilemez
- Yemek giderleri: İş amaçlı ise gider yazılabilir
- Ev ofis: Kira ve faturanın iş için kullanılan oranı yazılabilir
- Temsil ve ağırlama: Hasılatın %0.5'i ile sınırlı
- Bağış ve yardımlar: Kazancın %5'i ile sınırlı

## Fatura Kesme Zorunluluğu
- 5.000 TL üzeri tüm satışlarda fatura zorunlu
- E-ticaret satışlarında her durumda fatura zorunlu
- 5.000 TL altında fiş yeterli (esnaf muaflığı yoksa)
- Perakende satışlarda yazar kasa fişi geçerli

## E-Fatura / E-Arşiv Zorunlulukları
- Brüt satış hasılatı 3 milyon TL üzeri: E-fatura zorunlu
- E-ticaret yapanlar: E-arşiv zorunlu
- Ticari araç satanlar: E-fatura zorunlu
- Akaryakıt satıcıları: E-fatura zorunlu
- Diğerleri: Gönüllü geçiş yapılabilir

## Basit Usul Vergilendirme (2024)
- Yıllık alış limiti: 960.000 TL
- Yıllık satış limiti: 480.000 TL
- KDV muafiyeti var
- Defter tutma yok, sadece belge toplama
- Stopaj muafiyeti var
- Genç girişimci istisnası ile ilk 3 yıl 75.000 TL'ye kadar muafiyet

## SGK İşveren Yükümlülükleri
- İşçi SGK primi: Brüt maaşın %14'ü işçiden kesilir
- İşveren SGK payı: Brüt maaşın %20.5'i işveren öder
- İşsizlik sigortası: %1 işçi, %2 işveren
- Ödeme: Her ayın sonuna kadar
- İşe giriş bildirimi: İşe başlamadan en geç 1 gün önce
- 5 puanlık teşvik: 5510 sayılı kanun kapsamında

## Asgari Ücret (2024)
- Brüt: 20.002,50 TL
- Net: 17.002,12 TL
- İşveren maliyeti: Yaklaşık 23.500 TL

## Önemli Limitler
- KDV iade alt sınırı: 2.600 TL
- Fatura düzenleme sınırı: 5.000 TL
- Ba-Bs bildirim sınırı: 5.000 TL (KDV hariç)
- Nakit ödeme sınırı: 7.000 TL (üzeri banka yoluyla)

## Cezalar
- Beyanname vermeme: 1. derece usulsüzlük cezası
- Geç beyanname: %50 indirimli vergi ziyaı cezası
- Defter tutmama: Özel usulsüzlük cezası
- Fatura kesmeme: Her belge için ayrı ceza

## Vergi İndirimi ve Teşvikler
- AR-GE indirimi: %100
- Sponsorluk indirimi: Amatör spor %100, profesyonel %50
- Engelli istihdamı: SGK primi desteği
- 5 puan SGK indirimi: Tüm işverenler
- İşbaşı eğitim programı: SGK desteği

## Sık Sorulan Sorular için Notlar
1. Araç yakıtı: İşletme aracıysa %70'i gider yazılır, KDV indirilemez
2. Cep telefonu: İşle ilgili kullanılıyorsa gider yazılır
3. Kişisel kredi: İşle ilgili değilse gider yazılamaz
4. Personel yemek kartı: Günlük limitler dahilinde gider yazılır
5. İş seyahati: Belgeli ise tamamı gider yazılır
"""

# Örnek sorular
ORNEK_SORULAR = [
    "Araç yakıtını gider yazabilir miyim?",
    "KDV oranları nedir?",
    "SGK primini ne zaman ödeyeceğim?",
    "Fatura kesmeden satış yapabilir miyim?",
    "Basit usul nedir, kimler yararlanabilir?",
    "E-fatura kullanmak zorunda mıyım?",
    "Vergi beyannamelerini ne zaman vereceğim?",
    "İşçi çalıştırınca ne kadar SGK öderim?",
    "Ev ofis masraflarını gider yazabilir miyim?",
    "Nakit ödeme limiti nedir?"
]

# Soru-cevap prompt'u
SORU_CEVAP_PROMPT = """
Sen Türkiye'de faaliyet gösteren küçük işletmelere yardımcı olan bir muhasebe asistanısın.

Aşağıdaki bilgi bankasını kullanarak soruları yanıtla:

{context}

Kurallar:
1. Sadece bilgi bankasındaki konularda kesin bilgi ver
2. Emin olmadığın konularda "Bu konuda bir mali müşavire danışmanızı öneririm" de
3. Rakamlar ve limitler her yıl değişebilir, güncel bilgi için resmi kaynakları kontrol etmelerini öner
4. Kısa ve net cevaplar ver, gereksiz uzatma
5. Türkçe yanıt ver
6. Yasal tavsiye vermiyorsun, sadece genel bilgi sağlıyorsun
7. Mümkünse pratik örnekler ver
8. Önemli tarihleri ve limitleri vurgula

Kullanıcı sorusu: {soru}
"""


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


def soru_cevapla(soru: str, gecmis_mesajlar: List[dict] = None) -> str:
    """
    Muhasebe sorusunu yanıtlar.

    Args:
        soru: Kullanıcının sorusu
        gecmis_mesajlar: Önceki mesajlar (bağlam için)

    Returns:
        Yanıt metni
    """
    client = get_openai_client()

    if not client:
        return "OpenAI API anahtarı bulunamadı. Lütfen ayarları kontrol edin."

    try:
        messages = []

        # Sistem mesajı
        messages.append({
            "role": "system",
            "content": SORU_CEVAP_PROMPT.format(
                context=MUHASEBE_CONTEXT,
                soru="{soru}"  # Placeholder
            )
        })

        # Geçmiş mesajları ekle (varsa)
        if gecmis_mesajlar:
            for mesaj in gecmis_mesajlar[-10:]:  # Son 10 mesaj
                messages.append(mesaj)

        # Kullanıcı sorusunu ekle
        messages.append({
            "role": "user",
            "content": soru
        })

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            max_tokens=1000,
            temperature=0.7
        )

        return response.choices[0].message.content

    except Exception as e:
        return f"Bir hata oluştu: {str(e)}"


def ornek_sorular_getir() -> List[str]:
    """Örnek soruları döndürür."""
    return ORNEK_SORULAR.copy()


def rapor_insight_uret(kategori_ozet: dict, onceki_donem: dict = None) -> str:
    """
    Harcama raporu için içgörüler üretir.

    Args:
        kategori_ozet: Mevcut dönem kategori özeti
        onceki_donem: Önceki dönem kategori özeti

    Returns:
        İçgörü metni
    """
    client = get_openai_client()

    if not client:
        return "İçgörü üretilemedi."

    try:
        prompt = f"""
        Aşağıdaki gider verilerine göre kısa ve öz içgörüler üret:

        Mevcut Dönem Harcamaları:
        {kategori_ozet}

        {"Önceki Dönem: " + str(onceki_donem) if onceki_donem else ""}

        Lütfen:
        1. En yüksek harcama kategorisini belirt
        2. Varsa önceki döneme göre önemli değişimleri vurgula
        3. Dikkat edilmesi gereken noktaları belirt
        4. Maksimum 3-4 cümle yaz
        5. Türkçe ve sade bir dil kullan
        """

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300,
            temperature=0.7
        )

        return response.choices[0].message.content

    except Exception:
        return "İçgörü üretilemedi."
