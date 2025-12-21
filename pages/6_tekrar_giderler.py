"""
Tekrarlayan Giderler Sayfası
Aylık sabit giderlerin otomatik takibi
"""
import streamlit as st
import pandas as pd
from datetime import datetime, date

from utils.veritabani import (
    tekrar_gider_ekle, tekrar_giderleri_getir,
    tekrar_gider_sil, tekrar_gider_toggle, tekrar_giderleri_isle
)
from utils.kategorileme import GIDER_KATEGORILERI

# Sayfa yapılandırması
st.set_page_config(
    page_title="Tekrarlayan Giderler - KOBİ Finans Asistanı",
    page_icon="🔄",
    layout="wide"
)

st.title("🔄 Tekrarlayan Giderler")
st.markdown("Aylık sabit giderlerinizi tanımlayın, otomatik olarak takip edin.")

# Bilgi kutusu
st.info("""
**Nasıl Çalışır?**
- Kira, elektrik, internet gibi her ay tekrarlayan giderleri bir kez tanımlayın
- Her ayın belirlediğiniz gününde otomatik olarak gider kaydı oluşturulur
- Giderleri istediğiniz zaman aktif/pasif yapabilirsiniz
""")

# Sekmeler
tab1, tab2 = st.tabs(["📋 Tekrarlayan Giderler", "➕ Yeni Ekle"])

with tab1:
    # Otomatik işleme butonu
    col1, col2 = st.columns([3, 1])

    with col2:
        if st.button("▶️ Giderleri İşle", type="primary", help="Bugün için bekleyen tekrarlayan giderleri gider olarak ekler"):
            tekrar_giderleri_isle()
            st.success("Tekrarlayan giderler işlendi!")
            st.rerun()

    st.divider()

    # Tekrarlayan giderleri listele
    tum_gosterilsin = st.checkbox("Pasif giderleri de göster", value=False)
    tekrar_giderler = tekrar_giderleri_getir(sadece_aktif=not tum_gosterilsin)

    if tekrar_giderler.empty:
        st.info("Henüz tekrarlayan gider tanımlanmamış. 'Yeni Ekle' sekmesinden ekleyebilirsiniz.")
    else:
        # Aylık toplam
        aktif_giderler = tekrar_giderler[tekrar_giderler['aktif'] == 1]
        aylik_toplam = aktif_giderler['tutar'].sum() if not aktif_giderler.empty else 0

        st.metric("Aylık Toplam Sabit Gider", f"{aylik_toplam:,.2f} TL")

        st.divider()

        # Gider listesi
        for _, row in tekrar_giderler.iterrows():
            kategori_adi = GIDER_KATEGORILERI.get(row['kategori'], row['kategori'])
            aktif = row['aktif'] == 1

            with st.container(border=True):
                col1, col2, col3, col4 = st.columns([3, 2, 2, 1])

                with col1:
                    durum = "✅" if aktif else "⏸️"
                    st.markdown(f"**{durum} {row['satici_adi']}**")
                    st.caption(f"{kategori_adi}")

                with col2:
                    st.markdown(f"**{row['tutar']:,.2f} TL**")
                    tekrar_text = "Her ay" if row['tekrar_tipi'] == 'aylik' else row['tekrar_tipi']
                    gun_text = f" ({row['gun']}. gün)" if row['gun'] else ""
                    st.caption(f"{tekrar_text}{gun_text}")

                with col3:
                    if row['aciklama']:
                        st.caption(row['aciklama'])
                    if row['son_islem_tarihi']:
                        st.caption(f"Son işlem: {row['son_islem_tarihi']}")

                with col4:
                    col_btn1, col_btn2 = st.columns(2)

                    with col_btn1:
                        toggle_label = "⏸️" if aktif else "▶️"
                        if st.button(toggle_label, key=f"toggle_{row['id']}", help="Aktif/Pasif"):
                            tekrar_gider_toggle(row['id'])
                            st.rerun()

                    with col_btn2:
                        if st.button("🗑️", key=f"sil_{row['id']}", help="Sil"):
                            tekrar_gider_sil(row['id'])
                            st.rerun()

with tab2:
    st.subheader("Yeni Tekrarlayan Gider Ekle")

    with st.form("tekrar_gider_formu"):
        col1, col2 = st.columns(2)

        with col1:
            satici_adi = st.text_input(
                "Gider Adı / Satıcı",
                placeholder="Örn: Ofis Kirası, Türk Telekom, IGDAŞ"
            )

            kategori = st.selectbox(
                "Kategori",
                options=list(GIDER_KATEGORILERI.keys()),
                format_func=lambda x: GIDER_KATEGORILERI[x]
            )

            tutar = st.number_input(
                "Aylık Tutar (TL)",
                min_value=0.01,
                step=100.0,
                format="%.2f"
            )

        with col2:
            tekrar_tipi = st.selectbox(
                "Tekrar Sıklığı",
                options=["aylik"],
                format_func=lambda x: "Her Ay" if x == "aylik" else x
            )

            gun = st.number_input(
                "Ayın Hangi Günü",
                min_value=1,
                max_value=28,
                value=1,
                help="Her ayın bu gününde gider kaydedilir (1-28 arası)"
            )

            aciklama = st.text_area(
                "Açıklama (Opsiyonel)",
                placeholder="Ek notlar...",
                height=100
            )

        submitted = st.form_submit_button("💾 Kaydet", type="primary", use_container_width=True)

        if submitted:
            if not satici_adi:
                st.error("Gider adı zorunludur.")
            elif tutar <= 0:
                st.error("Tutar 0'dan büyük olmalıdır.")
            else:
                data = {
                    'satici_adi': satici_adi,
                    'kategori': kategori,
                    'tutar': tutar,
                    'tekrar_tipi': tekrar_tipi,
                    'gun': gun,
                    'aciklama': aciklama
                }
                tekrar_gider_ekle(data)
                st.success(f"'{satici_adi}' tekrarlayan gider olarak eklendi!")
                st.balloons()

    # Hızlı şablonlar
    st.divider()
    st.subheader("Hızlı Şablonlar")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("🏠 Kira Ekle", use_container_width=True):
            tekrar_gider_ekle({
                'satici_adi': 'Ofis Kirası',
                'kategori': 'kira',
                'tutar': 10000,
                'tekrar_tipi': 'aylik',
                'gun': 1,
                'aciklama': 'Aylık kira ödemesi'
            })
            st.success("Kira eklendi!")
            st.rerun()

    with col2:
        if st.button("📞 İnternet Ekle", use_container_width=True):
            tekrar_gider_ekle({
                'satici_adi': 'İnternet Faturası',
                'kategori': 'internet_telefon',
                'tutar': 500,
                'tekrar_tipi': 'aylik',
                'gun': 15,
                'aciklama': 'Aylık internet faturası'
            })
            st.success("İnternet eklendi!")
            st.rerun()

    with col3:
        if st.button("💡 Elektrik Ekle", use_container_width=True):
            tekrar_gider_ekle({
                'satici_adi': 'Elektrik Faturası',
                'kategori': 'elektrik',
                'tutar': 1500,
                'tekrar_tipi': 'aylik',
                'gun': 20,
                'aciklama': 'Aylık elektrik faturası'
            })
            st.success("Elektrik eklendi!")
            st.rerun()

# İpuçları
st.divider()
st.markdown("""
**İpuçları:**
- Tekrarlayan giderleri ayın 1-28 arası günlere ayarlayabilirsiniz (28 seçilirse her ay çalışır)
- Pasif hale getirilen giderler otomatik olarak eklenmez
- "Giderleri İşle" butonuna tıklayarak bekleyen giderleri hemen ekleyebilirsiniz
""")
