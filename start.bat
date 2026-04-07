@echo off
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
cd /d "%~dp0"

if "%~1"=="" (
    echo.
    echo DoggyOSINT - OSINT search tool
    echo.
    echo Usage:
    echo   start.bat -n username    Search by username
    echo   start.bat -e email       Search by email
    echo   start.bat -p phone       Search by phone
    echo   start.bat -i ip          Search by IP
    echo   start.bat -d domain      Search by domain
    echo   start.bat -m image.jpg   Image metadata
    echo.
    echo Examples:
    echo   start.bat -n durov
    echo   start.bat -n durov --depth deep
    echo   start.bat -n durov --export html
    echo   start.bat -e test@example.com
    echo   start.bat -p +79991234567
    echo   start.bat -i 8.8.8.8
    echo   start.bat -d google.com
    echo.
    pause
) else (
    python main.py %*
    pause
)
