@echo off
chcp 936 >nul
cd /d "%~dp0"
set PYTHONUTF8=1
"C:\Users\l\.workbuddy\binaries\python\versions\3.13.12\python.exe" ask_here.py
pause >nul