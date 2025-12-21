"""
KOBİ Finans Asistanı - Ana Sayfa (Dashboard)
Türkiye'deki küçük işletmeler için AI destekli finans asistanı
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta

from utils.veritabani import (
    toplam_istatistikler, init_database, kategori_ozet, aylik_ozet,
    butce_durum_getir, tekrar_giderleri_getir, tekrar_giderleri_isle
)
from utils.kategorileme import GIDER_KATEGORILERI
from config import APP_NAME, APP_VERSION

# Sayfa yapılandırması
st.set_page_config(
    page_title=APP_NAME,
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Veritabanını başlat
init_database()

# Tekrarlayan giderleri otomatik işle
try:
    tekrar_giderleri_isle()
except Exception:
    pass

# Tarih hesaplamaları
bugun = date.today()
ay_basi = bugun.replace(day=1)
gecen_ay_basi = (ay_basi - relativedelta(months=1))
gecen_ay_sonu = ay_basi - timedelta(days=1)

# Sidebar
with st.sidebar:
    st.title(f"💼 {APP_NAME}")
    st.caption(f"v{APP_VERSION}")

    st.divider()

    st.markdown("""
    **Sayfalar:**
    - 📄 Belge Okuyucu
    - 💰 Giderlerim
    - 📊 Raporlar
    - 💬 Soru-Cevap
    - 🎯 Bütçe Planlama
    - 🔄 Tekrarlayan Giderler
    """)

    st.divider()

    # Hızlı işlemler
    st.markdown("**Hızlı İşlemler**")
    st.page_link("pages/1_belge_okuyucu.py", label="📄 Belge Yükle", use_container_width=True)
    st.page_link("pages/2_giderlerim.py", label="➕ Gider Ekle", use_container_width=True)

    st.divider()
    st.caption(f"© 2024 {APP_NAME}")

# Ana içerik
st.title(f"💼 {APP_NAME}")
st.markdown("Küçük işletmeniz için akıllı finans yönetimi")

# İstatistikleri al
try:
    istatistikler = toplam_istatistikler()
    bu_ay_toplam = istatistikler['bu_ay_toplam']
    toplam_kayit = istatistikler['toplam_kayit']

    # Geçen ay verileri
    gecen_ay_ozet = kategori_ozet(
        gecen_ay_basi.strftime('%Y-%m-%d'),
        gecen_ay_sonu.strftime('%Y-%m-%d')
    )
    gecen_ay_toplam = gecen_ay_ozet['toplam'].sum() if not gecen_ay_ozet.empty else 0

    # Bu ay kategori özeti
    bu_ay_kategori = kategori_ozet(
        ay_basi.strftime('%Y-%m-%d'),
        bugun.strftime('%Y-%m-%d')
    )

    # Değişim yüzdesi
    if gecen_ay_toplam > 0:
        degisim = ((bu_ay_toplam - gecen_ay_toplam) / gecen_ay_toplam) * 100
    else:
        degisim = 0

except Exception as e:
    bu_ay_toplam = 0
    toplam_kayit = 0
    gecen_ay_toplam = 0
    degisim = 0
    bu_ay_kategori = pd.DataFrame()
    istatistikler = {'son_kayitlar': []}

# Metrik kartları
st.subheader("📈 Bu Ay Özeti")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "Bu Ay Toplam",
        f"{bu_ay_toplam:,.2f} TL",
        delta=f"{degisim:+.1f}%" if gecen_ay_toplam > 0 else None,
        delta_color="inverse"
    )

with col2:
    st.metric(
        "Geçen Ay",
        f"{gecen_ay_toplam:,.2f} TL"
    )

with col3:
    gun_sayisi = (bugun - ay_basi).days + 1
    gunluk_ort = bu_ay_toplam / gun_sayisi if gun_sayisi > 0 else 0
    st.metric(
        "Günlük Ortalama",
        f"{gunluk_ort:,.2f} TL"
    )

with col4:
    st.metric(
        "Toplam Kayıt",
        toplam_kayit
    )

st.divider()

# Grafikler ve son kayıtlar
col_chart, col_recent = st.columns([2, 1])

with col_chart:
    st.subheader("📊 Kategori Dağılımı")

    if not bu_ay_kategori.empty:
        bu_ay_kategori['kategori_adi'] = bu_ay_kategori['kategori'].apply(
            lambda x: GIDER_KATEGORILERI.get(x, x)
        )

        fig = px.pie(
            bu_ay_kategori,
            values='toplam',
            names='kategori_adi',
            color_discrete_sequence=px.colors.qualitative.Set3,
            hole=0.4
        )
        fig.update_traces(textposition='inside', textinfo='percent+label')
        fig.update_layout(
            showlegend=False,
            margin=dict(t=20, b=20, l=20, r=20),
            height=300
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Bu ay henüz gider kaydı yok.")

with col_recent:
    st.subheader("🕐 Son İşlemler")

    son_kayitlar = istatistikler.get('son_kayitlar', [])

    if son_kayitlar:
        for kayit in son_kayitlar[:5]:
            kategori_adi = GIDER_KATEGORILERI.get(kayit.get('kategori', ''), kayit.get('kategori', ''))
            satici = kayit.get('satici_adi', 'Belirtilmemiş')
            tutar = kayit.get('toplam_tutar', 0)

            with st.container(border=True):
                st.markdown(f"**{satici}**")
                col_a, col_b = st.columns([2, 1])
                with col_a:
                    st.caption(kategori_adi)
                with col_b:
                    st.markdown(f"**{tutar:,.2f} TL**")
    else:
        st.info("Henüz gider kaydı yok.")

st.divider()

# Bütçe durumu ve tekrarlayan giderler
col_budget, col_recurring = st.columns(2)

with col_budget:
    st.subheader("🎯 Bütçe Durumu")

    bu_ay_str = bugun.strftime('%Y-%m')
    butce_durum = butce_durum_getir(bu_ay_str)

    if not butce_durum.empty:
        for _, row in butce_durum.head(4).iterrows():
            kategori_adi = GIDER_KATEGORILERI.get(row['kategori'], row['kategori'])
            limit = row['limit_tutar']
            harcanan = row['harcanan']
            oran = (harcanan / limit * 100) if limit > 0 else 0

            # Renk belirleme
            if oran >= 100:
                renk = "🔴"
            elif oran >= 80:
                renk = "🟡"
            else:
                renk = "🟢"

            st.markdown(f"{renk} **{kategori_adi}**: {harcanan:,.0f} / {limit:,.0f} TL")
            st.progress(min(oran / 100, 1.0))

        st.page_link("pages/5_butce.py", label="Tüm Bütçeleri Gör →", icon="🎯")
    else:
        st.info("Henüz bütçe tanımlanmamış.")
        st.page_link("pages/5_butce.py", label="Bütçe Oluştur →", icon="🎯")

with col_recurring:
    st.subheader("🔄 Aylık Sabit Giderler")

    tekrar_giderler = tekrar_giderleri_getir(sadece_aktif=True)

    if not tekrar_giderler.empty:
        aylik_sabit = tekrar_giderler['tutar'].sum()
        st.metric("Aylık Sabit Toplam", f"{aylik_sabit:,.2f} TL")

        for _, row in tekrar_giderler.head(4).iterrows():
            kategori_adi = GIDER_KATEGORILERI.get(row['kategori'], row['kategori'])
            st.markdown(f"• **{row['satici_adi']}**: {row['tutar']:,.0f} TL ({kategori_adi})")

        st.page_link("pages/6_tekrar_giderler.py", label="Tümünü Gör →", icon="🔄")
    else:
        st.info("Henüz tekrarlayan gider tanımlanmamış.")
        st.page_link("pages/6_tekrar_giderler.py", label="Tanımla →", icon="🔄")

st.divider()

# Hızlı erişim kartları
st.subheader("🚀 Hızlı Erişim")

col1, col2, col3 = st.columns(3)

with col1:
    with st.container(border=True):
        st.markdown("### 📄 Belge Okuyucu")
        st.markdown("Fatura, fiş yükleyerek otomatik veri çıkarın.")
        st.page_link("pages/1_belge_okuyucu.py", label="Belge Yükle →", icon="📄")

with col2:
    with st.container(border=True):
        st.markdown("### 📊 Raporlar")
        st.markdown("Detaylı analiz ve trend raporları.")
        st.page_link("pages/3_raporlar.py", label="Raporlara Git →", icon="📊")

with col3:
    with st.container(border=True):
        st.markdown("### 💬 Soru-Cevap")
        st.markdown("Vergi ve muhasebe sorularınızı sorun.")
        st.page_link("pages/4_soru_cevap.py", label="Soru Sor →", icon="💬")

# Alt bilgi
st.divider()
st.markdown("""
<div style="text-align: center; color: #666; font-size: 0.9em;">
    <p>KOBİ Finans Asistanı - Türk KOBİ'leri için geliştirilmiştir</p>
    <p>⚠️ Bu uygulama genel bilgi amaçlıdır. Mali kararlarınız için profesyonel danışmanlık alınız.</p>
</div>
""", unsafe_allow_html=True)
