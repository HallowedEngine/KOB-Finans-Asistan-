# KOBİ Finans Asistanı

Türkiye'deki küçük işletme sahipleri için AI destekli finans asistanı uygulaması.

## Özellikler

### 1. Belge Okuyucu
- Fatura, fiş, dekont ve makbuz fotoğraflarından otomatik veri çıkarma
- GPT-4o Vision ile akıllı OCR
- Çıkarılan verileri düzenleme ve kaydetme

### 2. Gider Takibi
- Otomatik kategori tahmini
- 17 farklı gider kategorisi
- Manuel gider ekleme
- Filtreleme ve arama

### 3. Raporlar
- Kategori bazlı pasta ve çubuk grafikler
- Aylık trend analizi
- Dönem karşılaştırması
- AI destekli içgörüler

### 4. Soru-Cevap
- Türk vergi mevzuatı bilgi bankası
- Muhasebe sorularına AI destekli yanıtlar
- Örnek sorular ile hızlı başlangıç

## Kurulum

### Gereksinimler
- Python 3.11+
- OpenAI API anahtarı

### Adımlar

1. **Repoyu klonlayın:**
```bash
git clone https://github.com/kullanici/kobi-finans-asistani.git
cd kobi-finans-asistani
```

2. **Sanal ortam oluşturun (önerilen):**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# veya
venv\Scripts\activate  # Windows
```

3. **Bağımlılıkları yükleyin:**
```bash
pip install -r requirements.txt
```

4. **API anahtarını ayarlayın:**
```bash
cp .env.example .env
# .env dosyasını düzenleyip OPENAI_API_KEY değerini girin
```

5. **Uygulamayı başlatın:**
```bash
streamlit run app.py
```

## Streamlit Cloud Deployment

Streamlit Cloud'a deploy ederken:

1. GitHub reposunu Streamlit Cloud'a bağlayın
2. **Secrets** bölümünde API anahtarını ekleyin:
```toml
OPENAI_API_KEY = "sk-..."
```

## Gider Kategorileri

| Kategori | Açıklama |
|----------|----------|
| kira | Kira ve Aidat |
| personel | Personel ve Maaşlar |
| elektrik | Elektrik Faturaları |
| su | Su Faturaları |
| dogalgaz | Doğalgaz Faturaları |
| internet_telefon | İnternet ve Telefon |
| yakit | Yakıt ve Ulaşım |
| ofis_malzeme | Ofis Malzemeleri |
| hammadde | Hammadde ve Malzeme |
| pazarlama | Pazarlama ve Reklam |
| vergi | Vergi ve Harçlar |
| sigorta | Sigorta |
| bakim_onarim | Bakım ve Onarım |
| yemek | Yemek ve İkram |
| egitim | Eğitim ve Danışmanlık |
| banka | Banka Masrafları |
| diger | Diğer |

## Proje Yapısı

```
kobi-finans-asistani/
├── app.py                    # Ana Streamlit uygulaması
├── pages/
│   ├── 1_belge_okuyucu.py   # Belge okuma sayfası
│   ├── 2_giderlerim.py      # Gider listesi sayfası
│   ├── 3_raporlar.py        # Raporlar sayfası
│   └── 4_soru_cevap.py      # Chatbot sayfası
├── utils/
│   ├── ocr_parser.py        # GPT-4o Vision OCR
│   ├── kategorileme.py      # Kategori tahmini
│   ├── veritabani.py        # SQLite işlemleri
│   └── muhasebe_bilgi.py    # Bilgi bankası
├── data/
│   └── giderler.db          # SQLite veritabanı
├── .streamlit/
│   └── config.toml          # Tema ayarları
├── config.py                 # Uygulama ayarları
├── requirements.txt          # Bağımlılıklar
└── README.md
```

## Teknolojiler

- **Streamlit** - Web arayüzü
- **OpenAI GPT-4o** - OCR ve AI asistan
- **SQLite** - Yerel veritabanı
- **Pandas** - Veri işleme
- **Plotly** - Grafikler

## Lisans

MIT License

## Katkıda Bulunma

Pull request'ler memnuniyetle karşılanır. Büyük değişiklikler için önce bir issue açınız.

## Uyarı

Bu uygulama genel bilgi amaçlıdır ve profesyonel mali danışmanlık yerine geçmez. Önemli mali kararlarınız için mutlaka bir mali müşavire danışınız.
