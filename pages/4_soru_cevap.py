"""
Soru-Cevap Sayfası
Muhasebe ve vergi konularında AI destekli chatbot
"""
import streamlit as st
from utils.muhasebe_bilgi import soru_cevapla, ornek_sorular_getir

# Sayfa yapılandırması
st.set_page_config(
    page_title="Soru-Cevap - KOBİ Finans Asistanı",
    page_icon="💬",
    layout="wide"
)

st.title("💬 Muhasebe Soru-Cevap")
st.markdown("Vergi, muhasebe ve işletme konularında sorularınızı yanıtlıyoruz.")

# Session state başlatma
if 'mesajlar' not in st.session_state:
    st.session_state.mesajlar = []

# Örnek sorular
ornek_sorular = ornek_sorular_getir()

# Sidebar'da örnek sorular
with st.sidebar:
    st.subheader("Örnek Sorular")
    st.markdown("Sık sorulan konularda hızlı başlangıç:")

    for soru in ornek_sorular[:5]:
        if st.button(soru, key=f"ornek_{soru[:20]}", use_container_width=True):
            st.session_state.mesajlar.append({
                "role": "user",
                "content": soru
            })

            with st.spinner("Yanıt hazırlanıyor..."):
                yanit = soru_cevapla(soru, st.session_state.mesajlar[:-1])

            st.session_state.mesajlar.append({
                "role": "assistant",
                "content": yanit
            })
            st.rerun()

    st.divider()

    if st.button("🗑️ Sohbeti Temizle", use_container_width=True):
        st.session_state.mesajlar = []
        st.rerun()

# Ana sohbet alanı
chat_container = st.container()

with chat_container:
    # Mesajları göster
    for mesaj in st.session_state.mesajlar:
        with st.chat_message(mesaj["role"]):
            st.markdown(mesaj["content"])

    # Boş durum mesajı
    if not st.session_state.mesajlar:
        st.info("""
        Merhaba! Ben muhasebe asistanınızım. Size şu konularda yardımcı olabilirim:

        - **Vergi oranları ve tarihleri**
        - **Gider yazma kuralları**
        - **Fatura ve belge zorunlulukları**
        - **SGK ve personel maliyetleri**
        - **Basit usul vergilendirme**
        - **E-fatura ve e-arşiv**

        Aşağıdaki alana sorunuzu yazın veya soldaki örnek sorulardan birini seçin.

        ⚠️ **Not:** Verdiğim bilgiler genel niteliktedir. Spesifik durumlarınız için mali müşavirinize danışmanızı öneririm.
        """)

# Kullanıcı girişi
user_input = st.chat_input("Sorunuzu yazın...")

if user_input:
    # Kullanıcı mesajını ekle
    st.session_state.mesajlar.append({
        "role": "user",
        "content": user_input
    })

    # Yanıt al
    with st.spinner("Yanıt hazırlanıyor..."):
        yanit = soru_cevapla(user_input, st.session_state.mesajlar[:-1])

    # Yanıtı ekle
    st.session_state.mesajlar.append({
        "role": "assistant",
        "content": yanit
    })

    st.rerun()

# Alt bilgi
st.divider()
col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    **Kapsamdaki Konular:**
    - KDV oranları ve beyannameler
    - Gelir/Kurumlar vergisi
    - SGK primleri ve işveren yükümlülükleri
    - Fatura kesme kuralları
    - Gider yazma koşulları
    """)

with col2:
    st.markdown("""
    **Önemli Uyarılar:**
    - Verilen bilgiler 2024-2025 mevzuatına göredir
    - Limitler ve oranlar her yıl değişebilir
    - Kesin bilgi için resmi kaynakları kontrol edin
    - Mali müşavirinize danışmayı unutmayın
    """)
