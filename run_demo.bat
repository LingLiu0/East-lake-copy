@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ============================================
echo   East-lake 知识库 · 录屏演示（主线）
echo ============================================
echo.

set PY=C:\Users\l\.workbuddy\binaries\python\versions\3.13.12\python.exe

"%PY%" demo_show.py

echo.
echo 演示结束。按任意键关闭窗口...
pause >nul
