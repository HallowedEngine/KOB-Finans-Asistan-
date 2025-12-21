"""
Giderlerim Sayfası
Gider listesi, filtreleme ve manuel gider ekleme
"""
import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta

from utils.veritabani import giderleri_getir, gider_ekle, gider_sil, gider_guncelle
from utils.kategorileme import GIDER_KATEGORILERI, kategori_tahmin_et

# Sayfa yapılandırması
st.set_page_config(
    page_title="Giderlerim - KOBİ Finans Asistanı",
    page_icon="💰",
    layout="wide"
)

st.title("💰 Giderlerim")
st.markdown("Tüm gider kayıtlarınızı görüntüleyin, düzenleyin ve yönetin.")

# Tarih aralığı için varsayılanlar
bugun = date.today()
ay_basi = bugun.replace(day=1)

# Filtreler
st.subheader("Filtreler")
col1, col2, col3 = st.columns([1, 1, 2])

with col1:
    baslangic_tarih = st.date_input(
        "Başlangıç Tarihi",
        value=ay_basi,
        max_value=bugun
    )

with col2:
    bitis_tarih = st.date_input(
        "Bitiş Tarihi",
        value=bugun,
        min_value=baslangic_tarih,
        max_value=bugun
    )

with col3:
    secili_kategoriler = st.multiselect(
        "Kategoriler",
        options=list(GIDER_KATEGORILERI.keys()),
        format_func=lambda x: GIDER_KATEGORILERI[x],
        default=None,
        placeholder="Tüm kategoriler"
    )

# Giderleri getir
giderler_df = giderleri_getir(
    baslangic_tarih=baslangic_tarih.strftime('%Y-%m-%d'),
    bitis_tarih=bitis_tarih.strftime('%Y-%m-%d'),
    kategori=secili_kategoriler if secili_kategoriler else None
)

# Özet bilgiler
st.divider()
col_ozet1, col_ozet2, col_ozet3 = st.columns(3)

with col_ozet1:
    toplam = giderler_df['toplam_tutar'].sum() if not giderler_df.empty else 0
    st.metric("Toplam Gider", f"{toplam:,.2f} TL")

with col_ozet2:
    kayit_sayisi = len(giderler_df)
    st.metric("Kayıt Sayısı", kayit_sayisi)

with col_ozet3:
    ortalama = toplam / kayit_sayisi if kayit_sayisi > 0 else 0
    st.metric("Ortalama Gider", f"{ortalama:,.2f} TL")

st.divider()

# Gider tablosu ve Manuel ekleme
tab1, tab2 = st.tabs(["📋 Gider Listesi", "➕ Manuel Gider Ekle"])

with tab1:
    if giderler_df.empty:
        st.info("Bu tarih aralığında gider kaydı bulunamadı. Manuel gider ekleyebilir veya belge yükleyerek kayıt oluşturabilirsiniz.")
    else:
        # Görüntülenecek sütunları düzenle
        display_df = giderler_df.copy()

        # Kategori adlarını ekle
        display_df['kategori_adi'] = display_df['kategori'].apply(
            lambda x: GIDER_KATEGORILERI.get(x, x)
        )

        # Tarih formatını düzenle
        display_df['tarih'] = pd.to_datetime(display_df['tarih']).dt.strftime('%d.%m.%Y')

        # Görüntülenecek sütunlar
        columns_to_show = ['id', 'tarih', 'satici_adi', 'kategori_adi', 'toplam_tutar', 'odeme_yontemi', 'aciklama']
        columns_rename = {
            'id': 'ID',
            'tarih': 'Tarih',
            'satici_adi': 'Satıcı',
            'kategori_adi': 'Kategori',
            'toplam_tutar': 'Tutar (TL)',
            'odeme_yontemi': 'Ödeme',
            'aciklama': 'Açıklama'
        }

        st.dataframe(
            display_df[columns_to_show].rename(columns=columns_rename),
            use_container_width=True,
            hide_index=True,
            column_config={
                "ID": st.column_config.NumberColumn(width="small"),
                "Tarih": st.column_config.TextColumn(width="small"),
                "Tutar (TL)": st.column_config.NumberColumn(format="%.2f TL"),
            }
        )

        # Silme işlemi
        st.subheader("Gider Sil")
        col_sil1, col_sil2 = st.columns([2, 1])

        with col_sil1:
            silinecek_id = st.number_input(
                "Silinecek Gider ID",
                min_value=1,
                step=1,
                help="Silmek istediğiniz giderin ID numarasını girin"
            )

        with col_sil2:
            st.write("")  # Boşluk için
            st.write("")
            if st.button("🗑️ Sil", type="secondary"):
                # ID'nin var olup olmadığını kontrol et
                if silinecek_id in giderler_df['id'].values:
                    if gider_sil(silinecek_id):
                        st.success(f"Gider #{silinecek_id} silindi.")
                        st.rerun()
                    else:
                        st.error("Silme işlemi başarısız oldu.")
                else:
                    st.warning("Bu ID'ye sahip gider bulunamadı.")

with tab2:
    st.subheader("Manuel Gider Ekle")
    st.markdown("Belge olmadan da gider kaydı oluşturabilirsiniz.")

    with st.form("manuel_gider_formu"):
        # Tarih
        tarih = st.date_input(
            "Tarih",
            value=date.today(),
            max_value=date.today()
        )

        # Satıcı adı
        satici_adi = st.text_input(
            "Satıcı/Firma Adı",
            placeholder="Örn: Migros, Shell, Türk Telekom"
        )

        # Tutarlar
        col_t1, col_t2 = st.columns(2)

        with col_t1:
            toplam_tutar = st.number_input(
                "Toplam Tutar (TL)",
                min_value=0.01,
                step=0.01,
                format="%.2f"
            )

        with col_t2:
            kdv_tutari = st.number_input(
                "KDV Tutarı (TL) - Opsiyonel",
                min_value=0.0,
                step=0.01,
                format="%.2f",
                value=0.0
            )

        # Kategori
        kategori = st.selectbox(
            "Kategori",
            options=list(GIDER_KATEGORILERI.keys()),
            format_func=lambda x: GIDER_KATEGORILERI[x]
        )

        # Ödeme yöntemi
        odeme_yontemi = st.selectbox(
            "Ödeme Yöntemi",
            options=["belirsiz", "nakit", "kart", "havale"],
            format_func=lambda x: {
                "belirsiz": "Belirsiz",
                "nakit": "Nakit",
                "kart": "Kredi/Banka Kartı",
                "havale": "Havale/EFT"
            }.get(x, x)
        )

        # Belge tipi
        belge_tipi = st.selectbox(
            "Belge Tipi",
            options=["yok", "fatura", "fiş", "dekont", "makbuz", "diğer"],
            format_func=lambda x: {
                "yok": "Belge Yok",
                "fatura": "Fatura",
                "fiş": "Fiş",
                "dekont": "Dekont",
                "makbuz": "Makbuz",
                "diğer": "Diğer"
            }.get(x, x)
        )

        # Açıklama
        aciklama = st.text_area(
            "Açıklama (Opsiyonel)",
            placeholder="Giderle ilgili not ekleyin...",
            height=100
        )

        # Kaydet butonu
        submitted = st.form_submit_button(
            "💾 Gider Kaydet",
            type="primary",
            use_container_width=True
        )

        if submitted:
            if not satici_adi:
                st.error("Satıcı adı zorunludur.")
            elif toplam_tutar <= 0:
                st.error("Tutar 0'dan büyük olmalıdır.")
            else:
                gider_data = {
                    'tarih': tarih.strftime('%Y-%m-%d'),
                    'satici_adi': satici_adi,
                    'vergi_no': None,
                    'toplam_tutar': toplam_tutar,
                    'kdv_tutari': kdv_tutari if kdv_tutari > 0 else None,
                    'kategori': kategori,
                    'odeme_yontemi': odeme_yontemi,
                    'aciklama': aciklama if aciklama else None,
                    'belge_tipi': belge_tipi if belge_tipi != "yok" else None
                }

                try:
                    gider_id = gider_ekle(gider_data)
                    st.success(f"Gider başarıyla kaydedildi! (ID: {gider_id})")
                    st.balloons()
                except Exception as e:
                    st.error(f"Kaydetme hatası: {str(e)}")

# İpuçları
st.divider()
st.markdown("""
**İpuçları:**
- Tarihe ve kategoriye göre filtreleme yaparak giderlerinizi analiz edin
- Manuel gider eklerken kategori seçimini dikkatli yapın
- Raporlar sayfasından detaylı analizlere ulaşabilirsiniz
""")
