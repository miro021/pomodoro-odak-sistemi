import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from sqlalchemy import create_engine
import datetime
import re
from collections import Counter

# --- SAYFA AYARLARI VE SİBER-ESTETİK CSS ---
st.set_page_config(page_title="Komuta Merkezi | TYPE-Ω", page_icon="👁️‍🗨️", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    .ana-baslik { font-size: 40px; font-weight: 900; background: -webkit-linear-gradient(45deg, #FF007A, #00FFCA); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-align: center; }
    .alt-baslik { color: #888888; font-size: 16px; margin-bottom: 20px; text-align: center; }
    .stButton>button { background-color: #2b2b2b; color: #00FFCA; font-weight: bold; border-radius: 8px; border: 1px solid #00FFCA; width: 100%; }
    .stButton>button:hover { background-color: #00FFCA; color: black; }
    .kilit-ekrani { max-width: 400px; margin: 100px auto; padding: 30px; border: 2px solid #FF007A; border-radius: 15px; background-color: #111; box-shadow: 0 0 20px rgba(255, 0, 122, 0.4); }
    </style>
""", unsafe_allow_html=True)

# --- OTURUM (SESSION) KONTROLÜ ---
if "moderatör_onayi" not in st.session_state:
    st.session_state["moderatör_onayi"] = False

# ==========================================
# 1. GÖRSEL KİLİT EKRANI (GİRİŞ KAPISI)
# ==========================================
def giris_ekranini_goster():
    st.markdown('<div class="kilit-ekrani">', unsafe_allow_html=True)
    st.markdown('<h1 style="color:#FF007A; text-align:center;">🔴 ERİŞİM REDDEDİLDİ</h1>', unsafe_allow_html=True)
    st.markdown('<p style="color:#888; text-align:center;">TYPE-Ω Komuta Merkezine erişmek için<br>moderatör yetkinizi doğrulayın.</p>', unsafe_allow_html=True)
    
    sifre_denemesi = st.text_input("🔑 Güvenlik Protokolü Şifresi", type="password", placeholder="Şifrenizi girin...")
    
    if st.button("SİSTEME GİRİŞ YAP"):
        if sifre_denemesi == "albayraklar":
            st.session_state["moderatör_onayi"] = True
            st.rerun()
        else:
            st.error("❌ Hatalı şifre! İzinsiz giriş denemesi kaydedildi.")
    st.markdown('</div>', unsafe_allow_html=True)

# Şifre girilmediyse SADECE kilit ekranını göster ve kodun geri kalanını ÇALIŞTIRMA!
if not st.session_state["moderatör_onayi"]:
    giris_ekranini_goster()
    st.stop() # Güvenlik duvarı: Kodun alt kısımlarını okumayı burada keser.

# ==========================================
# (ŞİFRE DOĞRUYSA BURADAN AŞAĞISI ÇALIŞIR)
# ==========================================

# --- NEON BULUT VERİTABANI BAĞLANTISI ---
DATABASE_URL = "postgresql://neondb_owner:npg_fekm1rsUZ5TR@ep-green-cell-ah2wf67f-pooler.c-3.us-east-1.aws.neon.tech/neondb?sslmode=require"

@st.cache_resource
def get_engine():
    return create_engine(DATABASE_URL)
engine = get_engine()

# --- VERİ ÇEKME MODÜLÜ ---
@st.cache_data(ttl=60)
def buluttan_veri_indir(limit):
    query = f"SELECT * FROM loglar ORDER BY zaman DESC LIMIT {limit}"
    df = pd.read_sql_query(query, engine)
    if not df.empty:
        df['zaman'] = pd.to_datetime(df['zaman']).dt.tz_convert('Europe/Istanbul')
        if 'uygulama_exe' not in df.columns: df['uygulama_exe'] = 'bilinmiyor.exe'
        if 'klavye_hizi' not in df.columns: df['klavye_hizi'] = 0
        if 'tiklama_sayisi' not in df.columns: df['tiklama_sayisi'] = 0
        df['uygulama_exe'] = df['uygulama_exe'].fillna('bilinmiyor.exe')
        df['klavye_hizi'] = df['klavye_hizi'].fillna(0)
        df['tiklama_sayisi'] = df['tiklama_sayisi'].fillna(0)
    return df

# --- SABİT ALAN (Yan Menü) ---
st.sidebar.title("⚙️ Sistem Kontrolü")

# Çıkış Butonu Eklendi!
if st.sidebar.button("🔒 SİSTEMİ KİLİTLE (ÇIKIŞ)", use_container_width=True):
    st.session_state["moderatör_onayi"] = False
    st.rerun()

st.sidebar.markdown("---")
if st.sidebar.button("🔄 Radarı Anında Güncelle", use_container_width=True):
    buluttan_veri_indir.clear()
    st.rerun()

otomatik_yenile = st.sidebar.toggle("Otonom Senkronizasyon (60sn)", value=True)
gosterilecek_limit = st.sidebar.slider("📡 Veri Menzili", min_value=100, max_value=5000, value=1500, step=100)
arama_kutusu = st.sidebar.text_input("🔍 Hedef Ara...", placeholder="Örn: vscode, deney, python...")

st.markdown('<div class="ana-baslik">👁️‍🗨️ Küresel Odak & İstihbarat Ağı V4.1</div>', unsafe_allow_html=True)
st.markdown('<div class="alt-baslik">Güvenlik Protokolü Aktif. Hoş geldiniz Moderatör.</div>', unsafe_allow_html=True)

VERIMLI_KATEGORILER = ["🚀 Teknofest & Ar-Ge", "🧪 Kimya & Laboratuvar", "💻 Yazılım & Geliştirme"]

# --- DİNAMİK GRAFİK VE ANALİZ ALANI ---
def ana_verileri_isle_ve_ciz():
    try:
        df = buluttan_veri_indir(gosterilecek_limit)
        
        if not df.empty:
            aktif_df = df[df['uygulama_exe'] != 'system.exe']

            if arama_kutusu:
                filtre = aktif_df['uygulama_sekme'].str.contains(arama_kutusu, case=False, na=False) | \
                         aktif_df['yazilan_metin'].str.contains(arama_kutusu, case=False, na=False) | \
                         aktif_df['uygulama_exe'].str.contains(arama_kutusu, case=False, na=False)
                aktif_df = aktif_df[filtre]

            filtre_kolonu1, filtre_kolonu2 = st.columns(2)
            with filtre_kolonu1:
                ip_listesi = ["Tüm Ağ Cihazları"] + list(aktif_df['ip_adresi'].dropna().unique())
                secilen_ip = st.selectbox("🖥️ Cihaz Seç", ip_listesi, key="ip_secim")
            with filtre_kolonu2:
                kategori_listesi = list(aktif_df['kategori'].unique())
                secilen_kategoriler = st.multiselect("📂 Sektör Filtresi", kategori_listesi, default=kategori_listesi, key="kat_secim")

            if secilen_ip != "Tüm Ağ Cihazları":
                aktif_df = aktif_df[aktif_df['ip_adresi'] == secilen_ip]
            if secilen_kategoriler:
                aktif_df = aktif_df[aktif_df['kategori'].isin(secilen_kategoriler)]

            toplam_islem = len(aktif_df)
            toplam_tiklama = int(aktif_df['tiklama_sayisi'].sum())
            
            hizli_anlar = aktif_df[aktif_df['klavye_hizi'] > 0]
            ort_kpm = int(hizli_anlar['klavye_hizi'].mean()) if not hizli_anlar.empty else 0
            
            verimli_islem = len(aktif_df[aktif_df['kategori'].isin(VERIMLI_KATEGORILER)])
            odak_skoru = int((verimli_islem / toplam_islem) * 100) if toplam_islem > 0 else 0

            st.markdown("---")
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("🖱️ Toplam Fare Tıklaması", f"{toplam_tiklama} Tık")
            col2.metric("⌨️ Ortalama Yazma Hızı", f"{ort_kpm} KPM")
            col3.metric("📡 Son Sinyal", df['zaman'].max().strftime('%H:%M:%S'))
            col4.metric("⚙️ Baskın EXE", aktif_df['uygulama_exe'].mode()[0] if not aktif_df['uygulama_exe'].mode().empty else "Yok")
            st.markdown("---")

            tab1, tab2, tab3, tab4, tab5 = st.tabs(["🔥 Odak & Enerji", "🪐 Kök (EXE) ve Fare Radarı", "⚡ Zihinsel Akış (KPM)", "⌨️ Kelime Madenciliği", "📡 İstihbarat & Dışa Aktarım"])

            with tab1:
                g1, g2 = st.columns([1, 2])
                with g1:
                    fig_gauge = go.Figure(go.Indicator(
                        mode = "gauge+number", value = odak_skoru, title = {'text': "🔥 Odak Skoru (%)"},
                        gauge = {'axis': {'range': [None, 100]}, 'bar': {'color': "#FF007A"},
                                 'steps': [{'range': [0, 40], 'color': "#333333"}, {'range': [40, 75], 'color': "#888888"}, {'range': [75, 100], 'color': "#00FFCA"}]}
                    ))
                    fig_gauge.update_layout(height=350)
                    st.plotly_chart(fig_gauge, use_container_width=True)

                with g2:
                    kat_df = aktif_df['kategori'].value_counts().reset_index()
                    kat_df.columns = ['Kategori', 'İşlem Sayısı']
                    fig_pie = px.pie(kat_df, values='İşlem Sayısı', names='Kategori', hole=0.6, color_discrete_sequence=px.colors.sequential.Plasma)
                    fig_pie.update_layout(height=350, title_text="Enerji Dağılımı")
                    st.plotly_chart(fig_pie, use_container_width=True)

            with tab2:
                g3, g4 = st.columns(2)
                with g3:
                    exe_df = aktif_df['uygulama_exe'].value_counts().head(10).reset_index()
                    exe_df.columns = ['Program (EXE)', 'Kullanım Yoğunluğu']
                    fig_exe = px.bar(exe_df, x='Kullanım Yoğunluğu', y='Program (EXE)', orientation='h', title="En Çok Çalışan Kök Programlar", color='Kullanım Yoğunluğu', color_continuous_scale='Mint')
                    fig_exe.update_layout(yaxis={'categoryorder':'total ascending'}, height=400)
                    st.plotly_chart(fig_exe, use_container_width=True)
                
                with g4:
                    if toplam_tiklama > 0:
                        tik_df = aktif_df.groupby('uygulama_exe')['tiklama_sayisi'].sum().reset_index().sort_values('tiklama_sayisi', ascending=False).head(10)
                        fig_tik = px.bar(tik_df, x='uygulama_exe', y='tiklama_sayisi', title="Fare Tıklama Radarı (Nereye Çok Tıklandı?)", color='tiklama_sayisi', color_continuous_scale='Inferno')
                        fig_tik.update_layout(height=400)
                        st.plotly_chart(fig_tik, use_container_width=True)
                    else:
                        st.info("Yeterli fare tıklama verisi yok.")

            with tab3:
                aktif_df['Saat_Dakika'] = aktif_df['zaman'].dt.strftime('%H:%M')
                hiz_df = aktif_df[aktif_df['klavye_hizi'] > 0].groupby('Saat_Dakika')['klavye_hizi'].mean().reset_index()
                if not hiz_df.empty:
                    fig_area = px.area(hiz_df, x="Saat_Dakika", y="klavye_hizi", markers=True, title="Zihinsel Akış: Saatlere Göre Yazma Hızı (KPM)")
                    fig_area.update_traces(line_color="#00FFCA")
                    fig_area.update_layout(height=450)
                    st.plotly_chart(fig_area, use_container_width=True)
                else:
                    st.info("Yeterli klavye hız verisi birikmedi.")

            with tab4:
                st.subheader("En Çok Yazılan Kelimeler (Siber Madencilik)")
                tum_metin = " ".join(aktif_df['yazilan_metin'].dropna().tolist()).lower()
                temiz_kelimeler = re.findall(r'\b[a-zçğıöşüA-ZÇĞİÖŞÜ]{4,}\b', tum_metin) 
                if temiz_kelimeler:
                    kelime_sayilari = Counter(temiz_kelimeler).most_common(15)
                    kelime_df = pd.DataFrame(kelime_sayilari, columns=['Kelime', 'Frekans'])
                    fig_kelime = px.bar(kelime_df, x='Frekans', y='Kelime', orientation='h', color='Frekans', title="Klavye İzleri (Top 15)", color_continuous_scale='Viridis')
                    fig_kelime.update_layout(yaxis={'categoryorder':'total ascending'}, height=400)
                    st.plotly_chart(fig_kelime, use_container_width=True)
                else:
                    st.info("Yeterli kelime verisi birikmedi.")

            with tab5:
                st.download_button(
                    label="📥 Süzülmüş Veriyi Excel/CSV Olarak İndir",
                    data=aktif_df.to_csv(index=False).encode('utf-8'),
                    file_name=f'komuta_merkezi_log_{datetime.datetime.now().strftime("%Y%m%d_%H%M")}.csv',
                    mime='text/csv',
                )
                gosterilecek_sutunlar = ['zaman', 'uygulama_exe', 'uygulama_sekme', 'kategori', 'klavye_hizi', 'tiklama_sayisi', 'yazilan_metin']
                st.dataframe(aktif_df[gosterilecek_sutunlar], use_container_width=True, hide_index=True, height=500)
        else:
            st.info("📡 Ağ dinleniyor, veritabanı boş veya filtreler çok dar.")

    except Exception as e:
        st.error(f"Kritik Hata: {e}")

# --- YENİ NESİL 60 SANİYELİK TİTREMEYEN DÖNGÜ ---
if otomatik_yenile:
    if hasattr(st, 'fragment'):
        ana_verileri_isle_ve_ciz = st.fragment(run_every=60)(ana_verileri_isle_ve_ciz)
        ana_verileri_isle_ve_ciz()
    else:
        ana_verileri_isle_ve_ciz()
else:
    ana_verileri_isle_ve_ciz()