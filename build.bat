@echo off
REM Build script for ProbablyTasty on Windows
REM Creates standalone executable and optionally installer

echo ===================================
echo ProbablyTasty Build Script - Windows
echo ===================================
echo.

REM Check for PyInstaller
where pyinstaller >nul 2>nul
if %errorlevel% neq 0 (
    echo PyInstaller not found. Installing...
    pip install pyinstaller
)

REM Build with PyInstaller
echo Building executable with PyInstaller...
pyinstaller probablytasty.spec

if %errorlevel% equ 0 (
    echo Build successful!
    echo Location: dist\ProbablyTasty\ProbablyTasty.exe
) else (
    echo Build failed!
    exit /b 1
)

REM Ask about installer
echo.
set /p CREATE_INSTALLER="Do you want to create an installer with Inno Setup? (Y/N): "

if /i "%CREATE_INSTALLER%"=="Y" (
    echo.
    echo Creating installer with Inno Setup...
    
    REM Check for Inno Setup
    set INNO_PATH=C:\Program Files (x86)\Inno Setup 6\ISCC.exe
    
    if exist "%INNO_PATH%" (
        "%INNO_PATH%" installer.iss
        
        if %errorlevel% equ 0 (
            echo Installer created successfully!
            echo Location: dist\installer\ProbablyTasty-Setup-1.0.0.exe
        ) else (
            echo Installer creation failed!
        )
    ) else (
        echo Inno Setup not found!
        echo Download from: https://jrsoftware.org/isdl.php
        echo Then run: "%INNO_PATH%" installer.iss
    )
)

echo.
echo Build complete!
echo.
echo Output:
dir dist\ProbablyTasty\ProbablyTasty.exe
if exist dist\installer\ProbablyTasty-Setup-1.0.0.exe dir dist\installer\ProbablyTasty-Setup-1.0.0.exe
echo.
echo To test: dist\ProbablyTasty\ProbablyTasty.exe
pause
