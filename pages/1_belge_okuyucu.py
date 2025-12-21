"""
Belge Okuyucu Sayfası
Fatura, fiş, dekont ve makbuz fotoğraflarından veri çıkarma
"""
import streamlit as st
from datetime import datetime, date
from PIL import Image
import io

from utils.ocr_parser import belge_oku
from utils.kategorileme import kategori_tahmin_et, GIDER_KATEGORILERI
from utils.veritabani import gider_ekle

# Sayfa yapılandırması
st.set_page_config(
    page_title="Belge Okuyucu - KOBİ Finans Asistanı",
    page_icon="📄",
    layout="wide"
)

st.title("📄 Belge Okuyucu")
st.markdown("Fatura, fiş, dekont veya makbuz fotoğrafı yükleyerek otomatik veri çıkarma yapın.")

# Session state başlatma
if 'belge_verisi' not in st.session_state:
    st.session_state.belge_verisi = None
if 'belge_kaydedildi' not in st.session_state:
    st.session_state.belge_kaydedildi = False


def parse_tarih(tarih_str: str) -> date:
    """Tarih string'ini date objesine çevirir."""
    if not tarih_str:
        return date.today()

    formatlar = [
        "%Y-%m-%d",
        "%d.%m.%Y",
        "%d/%m/%Y",
        "%Y/%m/%d"
    ]

    for fmt in formatlar:
        try:
            return datetime.strptime(tarih_str, fmt).date()
        except ValueError:
            continue

    return date.today()


# Ana içerik
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("Belge Yükle")

    uploaded_file = st.file_uploader(
        "Fatura, fiş veya dekont fotoğrafı seçin",
        type=["jpg", "jpeg", "png", "pdf"],
        help="Desteklenen formatlar: JPG, JPEG, PNG, PDF"
    )

    if uploaded_file is not None:
        # Görüntüyü göster
        if uploaded_file.type != "application/pdf":
            image = Image.open(uploaded_file)
            st.image(image, caption="Yüklenen Belge", use_container_width=True)
        else:
            st.info("PDF dosyası yüklendi. Okuma için butona tıklayın.")

        # Belge okuma butonu
        if st.button("🔍 Belgeyi Oku", type="primary", use_container_width=True):
            with st.spinner("Belge okunuyor..."):
                # Dosyayı byte olarak oku
                file_bytes = uploaded_file.getvalue()

                # OCR işlemi
                sonuc = belge_oku(file_bytes)

                if sonuc.get("hata"):
                    st.error(f"Belge okunamadı: {sonuc.get('mesaj', 'Bilinmeyen hata')}")
                else:
                    st.session_state.belge_verisi = sonuc
                    st.session_state.belge_kaydedildi = False
                    st.success("Belge başarıyla okundu!")
                    st.rerun()

with col2:
    st.subheader("Çıkarılan Bilgiler")

    if st.session_state.belge_verisi and not st.session_state.belge_verisi.get("hata"):
        veri = st.session_state.belge_verisi

        # Düzenlenebilir form
        with st.form("belge_formu"):
            # Belge tipi
            belge_tipi = st.selectbox(
                "Belge Tipi",
                options=["fatura", "fiş", "dekont", "makbuz", "diğer"],
                index=["fatura", "fiş", "dekont", "makbuz", "diğer"].index(
                    veri.get("belge_tipi", "diğer") if veri.get("belge_tipi") in ["fatura", "fiş", "dekont", "makbuz", "diğer"] else "diğer"
                )
            )

            # Tarih
            tarih_val = parse_tarih(veri.get("tarih"))
            tarih = st.date_input("Tarih", value=tarih_val)

            # Satıcı adı
            satici_adi = st.text_input(
                "Satıcı/Firma Adı",
                value=veri.get("satici_adi", "") or ""
            )

            # Vergi numarası
            vergi_no = st.text_input(
                "Vergi Numarası",
                value=veri.get("vergi_no", "") or ""
            )

            # Tutarlar yan yana
            col_tutar1, col_tutar2 = st.columns(2)

            with col_tutar1:
                toplam_tutar = st.number_input(
                    "Toplam Tutar (TL)",
                    min_value=0.0,
                    value=float(veri.get("toplam_tutar") or 0),
                    step=0.01,
                    format="%.2f"
                )

            with col_tutar2:
                kdv_tutari = st.number_input(
                    "KDV Tutarı (TL)",
                    min_value=0.0,
                    value=float(veri.get("kdv_tutari") or 0),
                    step=0.01,
                    format="%.2f"
                )

            # Kategori tahmini
            tahmin_edilen_kategori = kategori_tahmin_et(
                satici_adi,
                veri.get("aciklama", "")
            )

            kategori = st.selectbox(
                "Kategori",
                options=list(GIDER_KATEGORILERI.keys()),
                format_func=lambda x: GIDER_KATEGORILERI[x],
                index=list(GIDER_KATEGORILERI.keys()).index(tahmin_edilen_kategori)
            )

            # Ödeme yöntemi
            odeme_yontemi = st.selectbox(
                "Ödeme Yöntemi",
                options=["belirsiz", "nakit", "kart", "havale"],
                index=["belirsiz", "nakit", "kart", "havale"].index(
                    veri.get("odeme_yontemi", "belirsiz") if veri.get("odeme_yontemi") in ["belirsiz", "nakit", "kart", "havale"] else "belirsiz"
                )
            )

            # Açıklama
            aciklama = st.text_area(
                "Açıklama",
                value=veri.get("aciklama", "") or "",
                height=100
            )

            # Kalemler (varsa)
            if veri.get("kalemler") and len(veri.get("kalemler")) > 0:
                st.markdown("**Belge Kalemleri:**")
                for kalem in veri.get("kalemler", []):
                    if isinstance(kalem, dict):
                        st.markdown(f"- {kalem.get('urun', 'Ürün')}: {kalem.get('adet', 1)} x {kalem.get('birim_fiyat', 0):.2f} TL = {kalem.get('toplam', 0):.2f} TL")

            # Kaydet butonu
            submitted = st.form_submit_button(
                "💾 Gider Olarak Kaydet",
                type="primary",
                use_container_width=True
            )

            if submitted:
                if toplam_tutar <= 0:
                    st.error("Toplam tutar 0'dan büyük olmalıdır.")
                else:
                    gider_data = {
                        'tarih': tarih.strftime('%Y-%m-%d'),
                        'satici_adi': satici_adi,
                        'vergi_no': vergi_no if vergi_no else None,
                        'toplam_tutar': toplam_tutar,
                        'kdv_tutari': kdv_tutari if kdv_tutari > 0 else None,
                        'kategori': kategori,
                        'odeme_yontemi': odeme_yontemi,
                        'aciklama': aciklama,
                        'belge_tipi': belge_tipi
                    }

                    try:
                        gider_id = gider_ekle(gider_data)
                        st.session_state.belge_kaydedildi = True
                        st.success(f"Gider başarıyla kaydedildi! (ID: {gider_id})")
                        st.balloons()
                    except Exception as e:
                        st.error(f"Kaydetme hatası: {str(e)}")

    elif st.session_state.belge_kaydedildi:
        st.success("Gider kaydedildi! Yeni belge yükleyebilirsiniz.")

        if st.button("Yeni Belge Yükle"):
            st.session_state.belge_verisi = None
            st.session_state.belge_kaydedildi = False
            st.rerun()
    else:
        st.info("Belge yükleyip 'Belgeyi Oku' butonuna tıklayın.")

# Alt bilgi
st.divider()
st.markdown("""
**İpuçları:**
- Net ve okunaklı fotoğraflar daha iyi sonuç verir
- Belgenin tamamı görüntüde olmalı
- Mümkünse düz bir yüzeyde fotoğraf çekin
- Çıkarılan bilgileri kaydetmeden önce kontrol edin
""")
