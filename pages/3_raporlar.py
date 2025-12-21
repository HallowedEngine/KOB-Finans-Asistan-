"""
Raporlar Sayfası
Gider analizleri, grafikler ve içgörüler
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta

from utils.veritabani import kategori_ozet, aylik_ozet, giderleri_getir
from utils.kategorileme import GIDER_KATEGORILERI
from utils.muhasebe_bilgi import rapor_insight_uret

# Sayfa yapılandırması
st.set_page_config(
    page_title="Raporlar - KOBİ Finans Asistanı",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Raporlar ve Analizler")
st.markdown("Giderlerinizi analiz edin, trendleri takip edin.")

# Dönem seçimi
bugun = date.today()
ay_basi = bugun.replace(day=1)

donem_secenekleri = {
    "Bu Ay": (ay_basi, bugun),
    "Geçen Ay": (
        (ay_basi - relativedelta(months=1)),
        ay_basi - timedelta(days=1)
    ),
    "Son 3 Ay": (
        (ay_basi - relativedelta(months=2)),
        bugun
    ),
    "Son 6 Ay": (
        (ay_basi - relativedelta(months=5)),
        bugun
    ),
    "Bu Yıl": (
        date(bugun.year, 1, 1),
        bugun
    ),
    "Özel Tarih": None
}

col1, col2, col3 = st.columns([2, 1, 1])

with col1:
    secili_donem = st.selectbox(
        "Dönem Seçin",
        options=list(donem_secenekleri.keys())
    )

if secili_donem == "Özel Tarih":
    with col2:
        baslangic_tarih = st.date_input("Başlangıç", value=ay_basi)
    with col3:
        bitis_tarih = st.date_input("Bitiş", value=bugun)
else:
    baslangic_tarih, bitis_tarih = donem_secenekleri[secili_donem]

# Verileri getir
kategori_df = kategori_ozet(
    baslangic_tarih.strftime('%Y-%m-%d'),
    bitis_tarih.strftime('%Y-%m-%d')
)

aylik_df = aylik_ozet(
    baslangic_tarih.strftime('%Y-%m-%d'),
    bitis_tarih.strftime('%Y-%m-%d')
)

giderler_df = giderleri_getir(
    baslangic_tarih.strftime('%Y-%m-%d'),
    bitis_tarih.strftime('%Y-%m-%d')
)

st.divider()

# Veri kontrolü
if kategori_df.empty:
    st.info("Seçilen dönemde gider kaydı bulunamadı. Gider eklemek için Belge Okuyucu veya Giderlerim sayfasını kullanın.")
else:
    # Özet kartlar
    st.subheader("Dönem Özeti")
    col_m1, col_m2, col_m3, col_m4 = st.columns(4)

    toplam_gider = kategori_df['toplam'].sum()
    kayit_sayisi = kategori_df['kayit_sayisi'].sum()
    gun_sayisi = (bitis_tarih - baslangic_tarih).days + 1
    gunluk_ortalama = toplam_gider / gun_sayisi if gun_sayisi > 0 else 0

    # En yüksek kategori
    en_yuksek = kategori_df.iloc[0] if not kategori_df.empty else None
    en_yuksek_kategori = GIDER_KATEGORILERI.get(
        en_yuksek['kategori'], en_yuksek['kategori']
    ) if en_yuksek is not None else "-"

    with col_m1:
        st.metric("Toplam Gider", f"{toplam_gider:,.2f} TL")

    with col_m2:
        st.metric("Kayıt Sayısı", int(kayit_sayisi))

    with col_m3:
        st.metric("Günlük Ortalama", f"{gunluk_ortalama:,.2f} TL")

    with col_m4:
        st.metric("En Yüksek Kategori", en_yuksek_kategori)

    # Geçen dönem karşılaştırması
    donem_uzunlugu = (bitis_tarih - baslangic_tarih).days + 1
    onceki_baslangic = baslangic_tarih - timedelta(days=donem_uzunlugu)
    onceki_bitis = baslangic_tarih - timedelta(days=1)

    onceki_kategori_df = kategori_ozet(
        onceki_baslangic.strftime('%Y-%m-%d'),
        onceki_bitis.strftime('%Y-%m-%d')
    )

    if not onceki_kategori_df.empty:
        onceki_toplam = onceki_kategori_df['toplam'].sum()
        if onceki_toplam > 0:
            degisim_yuzde = ((toplam_gider - onceki_toplam) / onceki_toplam) * 100
            degisim_text = f"Önceki döneme göre %{abs(degisim_yuzde):.1f} {'artış' if degisim_yuzde > 0 else 'azalış'}"
            st.info(f"📈 {degisim_text}")

    st.divider()

    # Grafikler
    col_graf1, col_graf2 = st.columns(2)

    with col_graf1:
        st.subheader("Kategori Dağılımı")

        # Kategori adlarını ekle
        kategori_df['kategori_adi'] = kategori_df['kategori'].apply(
            lambda x: GIDER_KATEGORILERI.get(x, x)
        )

        fig_pie = px.pie(
            kategori_df,
            values='toplam',
            names='kategori_adi',
            color_discrete_sequence=px.colors.qualitative.Set3,
            hole=0.4
        )
        fig_pie.update_traces(textposition='inside', textinfo='percent+label')
        fig_pie.update_layout(
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=-0.3),
            margin=dict(t=20, b=20, l=20, r=20)
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    with col_graf2:
        st.subheader("Kategori Bazlı Harcamalar")

        fig_bar = px.bar(
            kategori_df.sort_values('toplam', ascending=True),
            x='toplam',
            y='kategori_adi',
            orientation='h',
            color='toplam',
            color_continuous_scale='Greens'
        )
        fig_bar.update_layout(
            xaxis_title="Tutar (TL)",
            yaxis_title="",
            showlegend=False,
            margin=dict(t=20, b=20, l=20, r=20)
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    # Aylık trend
    if len(aylik_df) > 1:
        st.subheader("Aylık Trend")

        fig_line = px.line(
            aylik_df,
            x='ay',
            y='toplam',
            markers=True,
            line_shape='spline'
        )
        fig_line.update_traces(
            line_color='#2E7D32',
            marker=dict(size=10),
            fill='tozeroy',
            fillcolor='rgba(46, 125, 50, 0.1)'
        )
        fig_line.update_layout(
            xaxis_title="Ay",
            yaxis_title="Toplam Gider (TL)",
            margin=dict(t=20, b=20, l=20, r=20)
        )
        st.plotly_chart(fig_line, use_container_width=True)

    # AI İçgörüleri
    st.subheader("AI İçgörüleri")

    with st.spinner("İçgörüler oluşturuluyor..."):
        try:
            # Özet verileri hazırla
            kategori_dict = {
                GIDER_KATEGORILERI.get(row['kategori'], row['kategori']): row['toplam']
                for _, row in kategori_df.iterrows()
            }

            onceki_dict = None
            if not onceki_kategori_df.empty:
                onceki_dict = {
                    GIDER_KATEGORILERI.get(row['kategori'], row['kategori']): row['toplam']
                    for _, row in onceki_kategori_df.iterrows()
                }

            insight = rapor_insight_uret(kategori_dict, onceki_dict)
            st.info(insight)
        except Exception:
            st.info("İçgörü oluşturulamadı. API bağlantısını kontrol edin.")

    # Detaylı kategori tablosu
    st.subheader("Detaylı Kategori Tablosu")

    display_kategori = kategori_df.copy()
    display_kategori = display_kategori.rename(columns={
        'kategori_adi': 'Kategori',
        'kayit_sayisi': 'Kayıt Sayısı',
        'toplam': 'Toplam (TL)',
        'ortalama': 'Ortalama (TL)',
        'toplam_kdv': 'Toplam KDV (TL)'
    })

    display_kategori = display_kategori[[
        'Kategori', 'Kayıt Sayısı', 'Toplam (TL)', 'Ortalama (TL)', 'Toplam KDV (TL)'
    ]]

    st.dataframe(
        display_kategori,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Toplam (TL)": st.column_config.NumberColumn(format="%.2f TL"),
            "Ortalama (TL)": st.column_config.NumberColumn(format="%.2f TL"),
            "Toplam KDV (TL)": st.column_config.NumberColumn(format="%.2f TL"),
        }
    )

# Alt bilgi
st.divider()
st.markdown("""
**Rapor İpuçları:**
- Farklı dönemleri karşılaştırarak harcama trendlerinizi analiz edin
- En yüksek harcama kategorilerinize dikkat edin
- Aylık trend grafiği ile mevsimsel değişimleri takip edin
""")
