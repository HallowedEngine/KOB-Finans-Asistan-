"""
Bütçe Planlama Sayfası
Kategori bazlı aylık bütçe belirleme ve takip
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date
from dateutil.relativedelta import relativedelta

from utils.veritabani import (
    butce_ekle_guncelle, butceleri_getir, butce_sil, butce_durum_getir
)
from utils.kategorileme import GIDER_KATEGORILERI

# Sayfa yapılandırması
st.set_page_config(
    page_title="Bütçe Planlama - KOBİ Finans Asistanı",
    page_icon="🎯",
    layout="wide"
)

st.title("🎯 Bütçe Planlama")
st.markdown("Kategori bazlı aylık bütçe belirleyin ve harcamalarınızı takip edin.")

# Ay seçimi
bugun = date.today()
bu_ay = bugun.strftime('%Y-%m')

ay_secenekleri = {}
for i in range(-3, 4):
    ay = (bugun + relativedelta(months=i)).strftime('%Y-%m')
    ay_label = (bugun + relativedelta(months=i)).strftime('%B %Y')
    ay_secenekleri[ay] = ay_label

col1, col2 = st.columns([1, 3])
with col1:
    secili_ay = st.selectbox(
        "Dönem Seçin",
        options=list(ay_secenekleri.keys()),
        format_func=lambda x: ay_secenekleri[x],
        index=3  # Bu ay
    )

# Sekmeler
tab1, tab2 = st.tabs(["📊 Bütçe Durumu", "➕ Bütçe Ayarla"])

with tab1:
    st.subheader("Bütçe Durumu")

    butce_durum = butce_durum_getir(secili_ay)

    if butce_durum.empty:
        st.info(f"{ay_secenekleri[secili_ay]} için henüz bütçe tanımlanmamış. 'Bütçe Ayarla' sekmesinden bütçe ekleyebilirsiniz.")
    else:
        # Özet metrikler
        toplam_butce = butce_durum['limit_tutar'].sum()
        toplam_harcanan = butce_durum['harcanan'].sum()
        toplam_kalan = butce_durum['kalan'].sum()

        col_m1, col_m2, col_m3, col_m4 = st.columns(4)

        with col_m1:
            st.metric("Toplam Bütçe", f"{toplam_butce:,.2f} TL")

        with col_m2:
            st.metric("Harcanan", f"{toplam_harcanan:,.2f} TL")

        with col_m3:
            st.metric("Kalan", f"{toplam_kalan:,.2f} TL",
                     delta=f"{(toplam_kalan/toplam_butce*100):.1f}%" if toplam_butce > 0 else "0%")

        with col_m4:
            kullanim_orani = (toplam_harcanan / toplam_butce * 100) if toplam_butce > 0 else 0
            st.metric("Kullanım Oranı", f"%{kullanim_orani:.1f}")

        st.divider()

        # Kategori bazlı bütçe durumu
        for _, row in butce_durum.iterrows():
            kategori_adi = GIDER_KATEGORILERI.get(row['kategori'], row['kategori'])
            limit = row['limit_tutar']
            harcanan = row['harcanan']
            kalan = row['kalan']
            oran = (harcanan / limit * 100) if limit > 0 else 0

            # Renk belirleme
            if oran >= 100:
                renk = "🔴"
                bar_renk = "#D32F2F"
            elif oran >= 80:
                renk = "🟡"
                bar_renk = "#FFA000"
            else:
                renk = "🟢"
                bar_renk = "#2E7D32"

            col1, col2 = st.columns([3, 1])

            with col1:
                st.markdown(f"**{renk} {kategori_adi}**")
                st.progress(min(oran / 100, 1.0))

            with col2:
                st.markdown(f"**{harcanan:,.2f}** / {limit:,.2f} TL")
                if kalan < 0:
                    st.markdown(f"<span style='color: red;'>⚠️ {abs(kalan):,.2f} TL aşım!</span>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<span style='color: green;'>✓ {kalan:,.2f} TL kaldı</span>", unsafe_allow_html=True)

            st.divider()

        # Grafik
        st.subheader("Bütçe vs Harcama Grafiği")

        butce_durum['kategori_adi'] = butce_durum['kategori'].apply(
            lambda x: GIDER_KATEGORILERI.get(x, x)
        )

        fig = go.Figure()

        fig.add_trace(go.Bar(
            name='Bütçe',
            x=butce_durum['kategori_adi'],
            y=butce_durum['limit_tutar'],
            marker_color='#90CAF9'
        ))

        fig.add_trace(go.Bar(
            name='Harcanan',
            x=butce_durum['kategori_adi'],
            y=butce_durum['harcanan'],
            marker_color='#2E7D32'
        ))

        fig.update_layout(
            barmode='group',
            xaxis_title="Kategori",
            yaxis_title="Tutar (TL)",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )

        st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.subheader("Bütçe Ayarla")

    # Mevcut bütçeler
    mevcut_butceler = butceleri_getir(secili_ay)

    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown("### Yeni Bütçe Ekle")

        with st.form("butce_formu"):
            kategori = st.selectbox(
                "Kategori",
                options=list(GIDER_KATEGORILERI.keys()),
                format_func=lambda x: GIDER_KATEGORILERI[x]
            )

            limit_tutar = st.number_input(
                "Bütçe Limiti (TL)",
                min_value=0.0,
                step=100.0,
                format="%.2f"
            )

            submitted = st.form_submit_button("💾 Bütçe Kaydet", type="primary", use_container_width=True)

            if submitted:
                if limit_tutar <= 0:
                    st.error("Bütçe limiti 0'dan büyük olmalıdır.")
                else:
                    butce_ekle_guncelle(kategori, secili_ay, limit_tutar)
                    st.success(f"{GIDER_KATEGORILERI[kategori]} için bütçe kaydedildi!")
                    st.rerun()

        # Hızlı bütçe şablonları
        st.markdown("### Hızlı Şablonlar")

        if st.button("📋 Temel İşletme Bütçesi", use_container_width=True):
            sablonlar = {
                'kira': 15000,
                'elektrik': 2000,
                'su': 500,
                'internet_telefon': 1000,
                'ofis_malzeme': 1000,
                'yemek': 3000
            }
            for kat, limit in sablonlar.items():
                butce_ekle_guncelle(kat, secili_ay, limit)
            st.success("Temel işletme bütçesi eklendi!")
            st.rerun()

    with col2:
        st.markdown("### Mevcut Bütçeler")

        if mevcut_butceler.empty:
            st.info("Bu dönem için bütçe tanımlanmamış.")
        else:
            for _, row in mevcut_butceler.iterrows():
                kategori_adi = GIDER_KATEGORILERI.get(row['kategori'], row['kategori'])

                col_a, col_b, col_c = st.columns([3, 2, 1])

                with col_a:
                    st.markdown(f"**{kategori_adi}**")

                with col_b:
                    st.markdown(f"{row['limit_tutar']:,.2f} TL")

                with col_c:
                    if st.button("🗑️", key=f"sil_{row['id']}"):
                        butce_sil(row['id'])
                        st.rerun()

# İpuçları
st.divider()
st.markdown("""
**İpuçları:**
- 🟢 Yeşil: Bütçenin %80'inden azı kullanıldı
- 🟡 Sarı: Bütçenin %80-100'ü kullanıldı
- 🔴 Kırmızı: Bütçe aşıldı
- Hızlı şablonları kullanarak temel bütçeleri hızlıca ekleyebilirsiniz
""")
