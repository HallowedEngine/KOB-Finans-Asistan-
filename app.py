"""
KOBİ Finans Asistanı - Ana Sayfa
Türkiye'deki küçük işletmeler için AI destekli finans asistanı
"""
import streamlit as st
from datetime import datetime

from utils.veritabani import toplam_istatistikler, init_database
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

# Sidebar
with st.sidebar:
    st.image("https://img.icons8.com/color/96/money-bag.png", width=80)
    st.title(APP_NAME)
    st.caption(f"v{APP_VERSION}")

    st.divider()

    st.markdown("""
    **Sayfalar:**
    - 📄 Belge Okuyucu
    - 💰 Giderlerim
    - 📊 Raporlar
    - 💬 Soru-Cevap
    """)

    st.divider()

    st.markdown(f"© 2024 {APP_NAME}")

# Ana içerik
st.title(f"💼 {APP_NAME}")
st.markdown("Küçük işletmeniz için akıllı finans yönetimi")

# Hoşgeldin mesajı
st.info("""
Hoş geldiniz! Bu uygulama ile:
- **Fatura ve fişlerinizi** fotoğraftan otomatik okuyabilir
- **Giderlerinizi** kategorize edip takip edebilir
- **Raporlar** ile harcamalarınızı analiz edebilir
- **Vergi ve muhasebe** sorularınıza yanıt alabilirsiniz
""")

# İstatistikler
st.subheader("Özet Bilgiler")

try:
    istatistikler = toplam_istatistikler()

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Bu Ay Toplam Gider",
            f"{istatistikler['bu_ay_toplam']:,.2f} TL",
            help="Bu ay içindeki toplam gider tutarı"
        )

    with col2:
        st.metric(
            "Toplam Kayıt",
            istatistikler['toplam_kayit'],
            help="Sistemdeki toplam gider kaydı sayısı"
        )

    with col3:
        ay_adi = datetime.now().strftime("%B %Y")
        st.metric(
            "Dönem",
            ay_adi,
            help="Mevcut dönem"
        )

except Exception as e:
    st.warning("İstatistikler yüklenirken bir hata oluştu.")

st.divider()

# Hızlı erişim kartları
st.subheader("Hızlı Erişim")

col1, col2 = st.columns(2)

with col1:
    with st.container(border=True):
        st.markdown("### 📄 Belge Okuyucu")
        st.markdown("Fatura, fiş veya dekont fotoğrafı yükleyerek otomatik veri çıkarın.")
        st.page_link("pages/1_belge_okuyucu.py", label="Belge Yükle →", icon="📄")

    with st.container(border=True):
        st.markdown("### 📊 Raporlar")
        st.markdown("Giderlerinizi analiz edin, trendleri ve içgörüleri görün.")
        st.page_link("pages/3_raporlar.py", label="Raporlara Git →", icon="📊")

with col2:
    with st.container(border=True):
        st.markdown("### 💰 Giderlerim")
        st.markdown("Tüm gider kayıtlarınızı görüntüleyin ve yönetin.")
        st.page_link("pages/2_giderlerim.py", label="Giderleri Gör →", icon="💰")

    with st.container(border=True):
        st.markdown("### 💬 Soru-Cevap")
        st.markdown("Vergi ve muhasebe sorularınıza AI destekli yanıtlar alın.")
        st.page_link("pages/4_soru_cevap.py", label="Soru Sor →", icon="💬")

# Son kayıtlar
st.divider()
st.subheader("Son Gider Kayıtları")

try:
    son_kayitlar = istatistikler.get('son_kayitlar', [])

    if son_kayitlar:
        for kayit in son_kayitlar[:5]:
            kategori_adi = GIDER_KATEGORILERI.get(kayit.get('kategori', ''), kayit.get('kategori', ''))
            tarih = kayit.get('tarih', '')
            satici = kayit.get('satici_adi', 'Belirtilmemiş')
            tutar = kayit.get('toplam_tutar', 0)

            col1, col2, col3 = st.columns([2, 3, 2])

            with col1:
                st.text(tarih)
            with col2:
                st.text(f"{satici} - {kategori_adi}")
            with col3:
                st.text(f"{tutar:,.2f} TL")
    else:
        st.info("Henüz gider kaydı bulunmuyor. Belge yükleyerek veya manuel olarak gider ekleyebilirsiniz.")

except Exception:
    st.info("Son kayıtlar yüklenemedi.")

# Desteklenen kategoriler
st.divider()
with st.expander("Desteklenen Gider Kategorileri"):
    col1, col2, col3 = st.columns(3)

    kategoriler = list(GIDER_KATEGORILERI.items())
    ucte_bir = len(kategoriler) // 3

    with col1:
        for key, value in kategoriler[:ucte_bir + 1]:
            st.markdown(f"- {value}")

    with col2:
        for key, value in kategoriler[ucte_bir + 1:2 * ucte_bir + 1]:
            st.markdown(f"- {value}")

    with col3:
        for key, value in kategoriler[2 * ucte_bir + 1:]:
            st.markdown(f"- {value}")

# Alt bilgi
st.divider()
st.markdown("""
<div style="text-align: center; color: #666; font-size: 0.9em;">
    <p>KOBİ Finans Asistanı - Türk KOBİ'leri için geliştirilmiştir</p>
    <p>⚠️ Bu uygulama genel bilgi amaçlıdır. Mali kararlarınız için profesyonel danışmanlık alınız.</p>
</div>
""", unsafe_allow_html=True)
