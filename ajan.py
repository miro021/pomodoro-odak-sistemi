import ctypes
import time
import threading
import sys
import requests
import psycopg2
import psutil
from pynput import keyboard, mouse
from datetime import datetime

# --- NEON BULUT VERİTABANI BAĞLANTISI ---
DATABASE_URL = "postgresql://neondb_owner:npg_fekm1rsUZ5TR@ep-green-cell-ah2wf67f-pooler.c-3.us-east-1.aws.neon.tech/neondb?sslmode=require"

# --- CİHAZ (IP) TESPİTİ ---
try:
    CIHAZ_IP = requests.get('https://api.ipify.org', timeout=5).text
    print(f"🌍 İnternet Bağlantısı Aktif. Cihaz IP: {CIHAZ_IP}")
except:
    CIHAZ_IP = "Bilinmeyen_Cihaz"
    print("⚠️ IP adresi alınamadı, yerel olarak etiketlenecek.")

# --- YENİ NESİL ZAMANLAMA VE SENSÖR AYARLARI ---
BOS_KALMA_SURESI = 10       # 10 saniye işlem yapılmazsa cümleyi bitirip RAM kuyruğuna alır
TOPLU_GONDERIM_SURESI = 60  # Tam 60 saniyede bir RAM'deki her şeyi buluta fırlatır
AFK_SURESI = 180            # 3 dakika (180sn) fare/klavye oynamazsa "Boşta" moduna geçer

# --- YAPAY ZEKA DESTEKLİ KATEGORİZASYON ---
KATEGORILER = {
    "🚀 Teknofest & Ar-Ge": ["cellfire", "type-", "teknofest", "proje", "rapor", "sunum", "araştırma"],
    "🧪 Kimya & Laboratuvar": ["kimya", "deney", "reaksiyon", "periyodik", "asistan", "element", "molekül", "formül"],
    "💻 Yazılım & Geliştirme": ["python", "vscode", "pomodoro", "def ", "import ", "github", "localhost", "streamlit", "api", "sql", "veritabanı"],
    "📺 Medya & Araştırma": ["youtube", "video", "mp4", "pdf", "chatgpt", "gemini", "stackoverflow", "makale"],
    "💬 İletişim & Sosyal": ["whatsapp", "discord", "mail", "telegram", "outlook", "instagram", "twitter"]
}

# --- YENİ NESİL VERİTABANI KURULUMU (.EXE ve TIKLAMA DESTEKLİ) ---
def bulut_veritabanini_hazirla():
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS loglar (
                id SERIAL PRIMARY KEY,
                zaman TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                ip_adresi TEXT,
                uygulama_sekme TEXT,
                uygulama_exe TEXT,
                yazilan_metin TEXT,
                kategori TEXT,
                klavye_hizi INTEGER DEFAULT 0,
                tiklama_sayisi INTEGER DEFAULT 0
            );
        """)
        # Eski tabloda olmayan sütunları hata vermeden ekliyoruz (Sistem Güncellemesi)
        try: cursor.execute("ALTER TABLE loglar ADD COLUMN IF NOT EXISTS uygulama_exe TEXT;")
        except: pass
        try: cursor.execute("ALTER TABLE loglar ADD COLUMN IF NOT EXISTS klavye_hizi INTEGER DEFAULT 0;")
        except: pass
        try: cursor.execute("ALTER TABLE loglar ADD COLUMN IF NOT EXISTS tiklama_sayisi INTEGER DEFAULT 0;")
        except: pass
        
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_ip ON loglar(ip_adresi);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_zaman ON loglar(zaman DESC);")
        conn.commit()
        conn.close()
        print("✅ Neon Bulut Veritabanı ve V3 Sensör Sütunları Hazır!")
    except Exception as e:
        print(f"❌ Veritabanı Kurulum Hatası: {e}")

bulut_veritabanini_hazirla()

# --- AJANIN HAFIZASI ---
aktif_pencere, aktif_exe, canli_metin = "", "", ""
son_aktivite_zamani = time.time()
son_etkilesim_zamani = time.time() # AFK (Boşta) kontrolü için
son_bulut_gonderim = time.time()

tus_vurusu = 0
fare_tiklamasi = 0
oturum_baslangici = time.time()
afk_modu = False

veri_kilidi = threading.Lock()
genel_kuyruk = [] 

def aktif_sekmeyi_ve_exeyi_bul():
    """Windows API ve psutil ile milisaniye hızında uygulamanın .exe adını ve başlığını çeker."""
    try:
        hwnd = ctypes.windll.user32.GetForegroundWindow()
        if not hwnd: return "Masaüstü / Bilinmeyen", "bilinmiyor.exe"
        
        uzunluk = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
        buf = ctypes.create_unicode_buffer(uzunluk + 1)
        ctypes.windll.user32.GetWindowTextW(hwnd, buf, uzunluk + 1)
        baslik = buf.value if uzunluk > 0 else "Masaüstü"

        pid = ctypes.c_ulong()
        ctypes.windll.user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        try:
            exe_adi = psutil.Process(pid.value).name().lower()
        except:
            exe_adi = "bilinmiyor.exe"

        return baslik, exe_adi
    except:
        return "Bilinmeyen Pencere", "hata.exe"

def metni_kategorize_et(metin, pencere):
    analiz_metni = (metin + " " + pencere).lower()
    for kategori, kelimeler in KATEGORILER.items():
        if any(kelime in analiz_metni for kelime in kelimeler):
            return kategori
    return "📁 Genel Çalışma"

def veriyi_kuyruga_ekle(metin, pencere, exe_adi):
    global genel_kuyruk, tus_vurusu, fare_tiklamasi, oturum_baslangici
    
    gecen_sure = (time.time() - oturum_baslangici) / 60.0
    kpm = int(tus_vurusu / gecen_sure) if gecen_sure > 0 else tus_vurusu * 60

    # Yazı yazılmasa bile, tıklama varsa (Örn: YouTube'da video arama, tasarım yapma) kaydet!
    if len(metin.strip()) > 1 or fare_tiklamasi > 2:
        kategori = metni_kategorize_et(metin, pencere)
        temiz_metin = metin.strip() if metin.strip() != "" else "[SADECE FARE KULLANILDI]"
        
        # Yenilenmiş 7 Parçalı Veri Paketi
        veri_paketi = (CIHAZ_IP, pencere, exe_adi, temiz_metin, kategori, kpm, fare_tiklamasi)
        genel_kuyruk.append(veri_paketi)
        
        zaman_etiketi = datetime.now().strftime('%H:%M:%S')
        print(f"[{zaman_etiketi}] 📦 PAKETLENDİ (Kuyruk: {len(genel_kuyruk)}) | EXE: {exe_adi} | KPM: {kpm} | Tık: {fare_tiklamasi}")

    # Sayaçları sıfırla
    tus_vurusu = 0
    fare_tiklamasi = 0
    oturum_baslangici = time.time()

def buluta_toplu_firlat():
    global genel_kuyruk, son_bulut_gonderim
    
    if not genel_kuyruk:
        son_bulut_gonderim = time.time()
        return

    zaman_etiketi = datetime.now().strftime('%H:%M:%S')
    yedek_kuyruk = genel_kuyruk.copy() 
    genel_kuyruk.clear() 

    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        kuyruk_sorgusu = """
            INSERT INTO loglar (ip_adresi, uygulama_sekme, uygulama_exe, yazilan_metin, kategori, klavye_hizi, tiklama_sayisi) 
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        cursor.executemany(kuyruk_sorgusu, yedek_kuyruk)
        
        conn.commit()
        conn.close()
        
        print(f"\n[{zaman_etiketi}] 🚀🚀 TOPLU GÖNDERİM BAŞARILI! {len(yedek_kuyruk)} veri Neon'a işlendi.\n")
        son_bulut_gonderim = time.time()
        
    except Exception as e: 
        genel_kuyruk.extend(yedek_kuyruk)
        print(f"\n[{zaman_etiketi}] ⚠️ BAĞLANTI HATASI! {len(yedek_kuyruk)} veri RAM'de korunuyor.\n")

def arka_plan_takip_dongusu():
    global aktif_pencere, aktif_exe, canli_metin, son_aktivite_zamani, afk_modu
    print("\n" + "="*50)
    print("👁️‍🗨️ V3 OTONOM AJAN AKTİF | 60 SN SİSTEMİ & SENSÖRLER DEVREDE...")
    print("="*50 + "\n")
    
    while True:
        zaman_farki = time.time() - son_aktivite_zamani
        afk_farki = time.time() - son_etkilesim_zamani
        yeni_pencere, yeni_exe = aktif_sekmeyi_ve_exeyi_bul()
        
        with veri_kilidi:
            # 1. ŞART: AFK Tespiti
            if afk_farki > AFK_SURESI and not afk_modu:
                veriyi_kuyruga_ekle(canli_metin, aktif_pencere, aktif_exe)
                canli_metin = ""
                afk_modu = True
                print(f"[{datetime.now().strftime('%H:%M:%S')}] 🛑 KULLANICI BİLGİSAYAR BAŞINDAN KALKTI (AFK MODU)")
                veriyi_kuyruga_ekle("[AFK BAŞLADI - BİLGİSAYAR BOŞTA]", "Sistem Uyku Modu", "system.exe")

            # 2. ŞART: Sekme değişirse logu kuyruğa at
            if (yeni_pencere != aktif_pencere or yeni_exe != aktif_exe) and (canli_metin != "" or fare_tiklamasi > 0):
                veriyi_kuyruga_ekle(canli_metin, aktif_pencere, aktif_exe)
                canli_metin = ""
                aktif_pencere, aktif_exe = yeni_pencere, yeni_exe
                
            # 3. ŞART: 10 Saniye boyunca klavyeye basılmazsa logu kuyruğa at
            elif zaman_farki > BOS_KALMA_SURESI and (canli_metin != "" or fare_tiklamasi > 0):
                veriyi_kuyruga_ekle(canli_metin, aktif_pencere, aktif_exe)
                canli_metin = ""
                
            if aktif_pencere != yeni_pencere:
                aktif_pencere, aktif_exe = yeni_pencere, yeni_exe

        # --- YENİ NESİL 60 SANİYE KONTROLÜ ---
        if time.time() - son_bulut_gonderim >= TOPLU_GONDERIM_SURESI:
            buluta_toplu_firlat()
                
        time.sleep(0.1)

# --- SENSÖRLER (KLAVYE VE FARE) ---
def etkilesim_oldu():
    global son_aktivite_zamani, son_etkilesim_zamani, afk_modu
    son_aktivite_zamani = time.time()
    son_etkilesim_zamani = time.time()
    if afk_modu:
        afk_modu = False
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 🟢 KULLANICI GERİ DÖNDÜ")
        veriyi_kuyruga_ekle("[AFK BİTTİ - KULLANICI MASADA]", "Sistem Uyku Modu", "system.exe")

def tusa_basildiginda(tus):
    global canli_metin, tus_vurusu
    etkilesim_oldu()
    with veri_kilidi:
        tus_vurusu += 1
        try:
            if tus == keyboard.Key.space: canli_metin += " "
            elif tus == keyboard.Key.enter: canli_metin += " [ENTER] "
            elif tus == keyboard.Key.backspace: canli_metin = canli_metin[:-1] if len(canli_metin) > 0 else ""
            elif hasattr(tus, 'char') and tus.char is not None: canli_metin += tus.char
        except: pass

def fare_tiklandiginda(x, y, button, pressed):
    global fare_tiklamasi
    if pressed:
        etkilesim_oldu()
        with veri_kilidi:
            fare_tiklamasi += 1

def fare_hareket_ettiginde(x, y):
    global son_etkilesim_zamani, afk_modu
    son_etkilesim_zamani = time.time()
    if afk_modu:
        afk_modu = False
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 🟢 KULLANICI GERİ DÖNDÜ (Fare Hareket Etti)")

if __name__ == "__main__":
    try:
        # psutil kütüphanesi eksikse uyar
        import psutil
    except ImportError:
        print("❌ 'psutil' yüklü değil! Terminale şunu yazın: pip install psutil pynput")
        sys.exit()

    try:
        takip_thread = threading.Thread(target=arka_plan_takip_dongusu, daemon=True)
        takip_thread.start()

        klavye_dinleyici = keyboard.Listener(on_press=tusa_basildiginda)
        fare_dinleyici = mouse.Listener(on_click=fare_tiklandiginda, on_move=fare_hareket_ettiginde)
        
        klavye_dinleyici.start()
        fare_dinleyici.start()

        klavye_dinleyici.join()
        fare_dinleyici.join()
            
    except KeyboardInterrupt:
        print("\n[!] Sistem durduruluyor. Kalan veriler buluta aktarılıyor...")
        buluta_toplu_firlat()
        sys.exit()