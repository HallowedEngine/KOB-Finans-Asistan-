"""
Giderlerim Sayfası
Gider listesi, gelişmiş filtreleme, dışa aktarım ve manuel gider ekleme
"""
import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta

from utils.veritabani import giderleri_getir_gelismis, gider_ekle, gider_sil, gider_guncelle
from utils.kategorileme import GIDER_KATEGORILERI
from utils.export import export_to_excel, export_to_csv

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

# Tarih presetleri
tarih_presetleri = {
    "Bu Ay": (ay_basi, bugun),
    "Geçen Ay": ((ay_basi - timedelta(days=1)).replace(day=1), ay_basi - timedelta(days=1)),
    "Son 7 Gün": (bugun - timedelta(days=7), bugun),
    "Son 30 Gün": (bugun - timedelta(days=30), bugun),
    "Son 90 Gün": (bugun - timedelta(days=90), bugun),
    "Bu Yıl": (date(bugun.year, 1, 1), bugun),
    "Özel": None
}

# Filtreler
with st.expander("🔍 Filtreler", expanded=True):
    # İlk satır: Tarih presetleri ve tarih seçiciler
    col_preset, col_start, col_end = st.columns([1, 1, 1])

    with col_preset:
        preset = st.selectbox("Dönem", options=list(tarih_presetleri.keys()), index=0)

    if preset != "Özel" and tarih_presetleri[preset]:
        baslangic_tarih, bitis_tarih = tarih_presetleri[preset]
    else:
        with col_start:
            baslangic_tarih = st.date_input("Başlangıç", value=ay_basi, max_value=bugun)
        with col_end:
            bitis_tarih = st.date_input("Bitiş", value=bugun, min_value=baslangic_tarih)

    if preset != "Özel":
        with col_start:
            st.date_input("Başlangıç", value=baslangic_tarih, disabled=True, key="start_disabled")
        with col_end:
            st.date_input("Bitiş", value=bitis_tarih, disabled=True, key="end_disabled")

    # İkinci satır: Kategori, ödeme yöntemi, arama
    col_kat, col_odeme, col_arama = st.columns([2, 1, 2])

    with col_kat:
        secili_kategoriler = st.multiselect(
            "Kategoriler",
            options=list(GIDER_KATEGORILERI.keys()),
            format_func=lambda x: GIDER_KATEGORILERI[x],
            placeholder="Tüm kategoriler"
        )

    with col_odeme:
        odeme_filtre = st.multiselect(
            "Ödeme Yöntemi",
            options=["nakit", "kart", "havale", "belirsiz"],
            format_func=lambda x: {"nakit": "Nakit", "kart": "Kart", "havale": "Havale", "belirsiz": "Belirsiz"}.get(x, x),
            placeholder="Tümü"
        )

    with col_arama:
        arama_metni = st.text_input("Ara (Satıcı/Açıklama)", placeholder="Arama metni...")

    # Üçüncü satır: Tutar aralığı
    col_min, col_max = st.columns(2)

    with col_min:
        min_tutar = st.number_input("Min Tutar (TL)", min_value=0.0, value=0.0, step=100.0)

    with col_max:
        max_tutar = st.number_input("Max Tutar (TL)", min_value=0.0, value=0.0, step=100.0,
                                    help="0 = limit yok")

# Giderleri getir (gelişmiş filtreleme)
giderler_df = giderleri_getir_gelismis(
    baslangic_tarih=baslangic_tarih.strftime('%Y-%m-%d'),
    bitis_tarih=bitis_tarih.strftime('%Y-%m-%d'),
    kategori=secili_kategoriler if secili_kategoriler else None,
    min_tutar=min_tutar if min_tutar > 0 else None,
    max_tutar=max_tutar if max_tutar > 0 else None,
    odeme_yontemi=odeme_filtre if odeme_filtre else None,
    arama=arama_metni if arama_metni else None
)

# Özet bilgiler ve dışa aktarım
st.divider()
col_ozet1, col_ozet2, col_ozet3, col_export = st.columns([1, 1, 1, 1])

with col_ozet1:
    toplam = giderler_df['toplam_tutar'].sum() if not giderler_df.empty else 0
    st.metric("Toplam Gider", f"{toplam:,.2f} TL")

with col_ozet2:
    kayit_sayisi = len(giderler_df)
    st.metric("Kayıt Sayısı", kayit_sayisi)

with col_ozet3:
    ortalama = toplam / kayit_sayisi if kayit_sayisi > 0 else 0
    st.metric("Ortalama", f"{ortalama:,.2f} TL")

with col_export:
    st.markdown("**Dışa Aktar**")
    col_xl, col_csv = st.columns(2)

    with col_xl:
        if not giderler_df.empty:
            excel_data = export_to_excel(giderler_df)
            st.download_button(
                "📊 Excel",
                data=excel_data,
                file_name=f"giderler_{baslangic_tarih}_{bitis_tarih}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
        else:
            st.button("📊 Excel", disabled=True, use_container_width=True)

    with col_csv:
        if not giderler_df.empty:
            csv_data = export_to_csv(giderler_df)
            st.download_button(
                "📄 CSV",
                data=csv_data,
                file_name=f"giderler_{baslangic_tarih}_{bitis_tarih}.csv",
                mime="text/csv",
                use_container_width=True
            )
        else:
            st.button("📄 CSV", disabled=True, use_container_width=True)

st.divider()

# Gider tablosu ve Manuel ekleme
tab1, tab2 = st.tabs(["📋 Gider Listesi", "➕ Manuel Gider Ekle"])

with tab1:
    if giderler_df.empty:
        st.info("Bu filtrelerle eşleşen gider kaydı bulunamadı.")
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
            st.write("")
            st.write("")
            if st.button("🗑️ Sil", type="secondary"):
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
        col1, col2 = st.columns(2)

        with col1:
            tarih = st.date_input("Tarih", value=date.today(), max_value=date.today())

            satici_adi = st.text_input(
                "Satıcı/Firma Adı",
                placeholder="Örn: Migros, Shell, Türk Telekom"
            )

            toplam_tutar = st.number_input(
                "Toplam Tutar (TL)",
                min_value=0.01,
                step=0.01,
                format="%.2f"
            )

            kdv_tutari = st.number_input(
                "KDV Tutarı (TL) - Opsiyonel",
                min_value=0.0,
                step=0.01,
                format="%.2f",
                value=0.0
            )

        with col2:
            kategori = st.selectbox(
                "Kategori",
                options=list(GIDER_KATEGORILERI.keys()),
                format_func=lambda x: GIDER_KATEGORILERI[x]
            )

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

            aciklama = st.text_area(
                "Açıklama (Opsiyonel)",
                placeholder="Giderle ilgili not ekleyin...",
                height=100
            )

        submitted = st.form_submit_button("💾 Gider Kaydet", type="primary", use_container_width=True)

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
- Tarih presetlerini kullanarak hızlıca dönem seçebilirsiniz
- Gelişmiş filtrelerle istediğiniz kayıtları bulabilirsiniz
- Excel/CSV butonlarıyla verileri dışa aktarabilirsiniz
""")
