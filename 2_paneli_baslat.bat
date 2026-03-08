@echo off
chcp 65001 >nul 
title TYPE-OMEGA KOMUTA MERKEZİ
color 0B

cd /d "%~dp0"
echo ===================================================
echo [!] TYPE-OMEGA PANELİ ATESLENIYOR...
echo [!] Tarayicida acilacaktir, lutfen bekleyin.
echo ===================================================

pip install -r requirements.txt >nul 2>&1

:: Streamlit'i çalıştırıp analiz paneline götürür
streamlit run panel.py
pause