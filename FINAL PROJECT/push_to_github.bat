@echo off
title Push to GitHub
cd /d "%~dp0"
echo ===================================================================
echo   Pushing Data-Structures project to GitHub...
echo   Repository: https://github.com/anishkannan104-pixel/Data-Structures.git
echo ===================================================================
echo.
git push -u origin main
echo.
if %errorlevel% equ 0 (
    echo [SUCCESS] Project successfully pushed to GitHub!
) else (
    echo [!] Push failed or was canceled. Please check your GitHub credentials.
)
echo.
pause
