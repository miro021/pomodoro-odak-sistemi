@echo off
chcp 65001 >nul 
title TYPE-OMEGA MOTOR TETIKLEYICI
color 0A

cd /d "%~dp0"
pip install -r requirements.txt >nul 2>&1

:: pythonw arkaplanda GÖRÜNMEZ ve ŞİFRESİZ çalıştırır
start pythonw motor.py
exit