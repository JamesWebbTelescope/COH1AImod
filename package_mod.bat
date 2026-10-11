@echo off
REM CoH1 × Mistral AI Mod - Mod Packaging Script
REM
REM This script packages the mod files into a .sga archive for CoH1.
REM In CoH1, .sga files are essentially .zip archives.
REM
REM Usage:
REM   package_mod.bat             - Creates coh1_mistral_ai.sga
REM   package_mod.bat MyModName   - Creates MyModName.sga

setlocal

set MOD_NAME=coh1_mistral_ai
set MOD_VERSION=0.1.0

if not "%~1"=="" (
    set MOD_NAME=%~1
)

set SGA_FILE=%MOD_NAME%.sga
set TEMP_DIR=temp_package

REM Clean up previous temp directory
if exist "%TEMP_DIR%" rmdir /s /q "%TEMP_DIR%"

REM Create temp directory
mkdir "%TEMP_DIR%"

REM Copy SCAR files to temp directory (they should be at the root of the .sga)
copy scar\config.scar "%TEMP_DIR%\" >nul
copy scar\ipc.scar "%TEMP_DIR%\" >nul
copy scar\main.scar "%TEMP_DIR%\" >nul
copy scar\state_collector.scar "%TEMP_DIR%\" >nul

REM Create mod.ini file (optional)
(
    echo [General]
    echo ModName=%MOD_NAME%
    echo ModVersion=%MOD_VERSION%
    echo Description=CoH1 AI Mod powered by Mistral
    echo Author=CoH1 AI Mod Team
    echo CompatibleVersion=1.0
) > "%TEMP_DIR%\mod.ini"

REM Package using 7-Zip if available
if exist "C:\Program Files\7-Zip\7z.exe" (
    "C:\Program Files\7-Zip\7z.exe" a -tzip "%SGA_FILE%" "%TEMP_DIR%\*" -mx=1 >nul
) else if exist "C:\Program Files (x86)\.7-Zip\7z.exe" (
    "C:\Program Files (x86)\.7-Zip\7z.exe" a -tzip "%SGA_FILE%" "%TEMP_DIR%\*" -mx=1 >nul
) else (
    REM Use PowerShell
    powershell -command "& {Compress-Archive -Path '%TEMP_DIR%\*' -DestinationPath '%SGA_FILE%' -CompressionLevel Optimal}" >nul 2>&1
    
    if not exist "%SGA_FILE%" (
        REM Fallback: Use tar
        tar -czf "%SGA_FILE%" -C "%TEMP_DIR%" . >nul 2>&1
    )
)

REM Clean up temp directory
if exist "%TEMP_DIR%" rmdir /s /q "%TEMP_DIR%"

if exist "%SGA_FILE%" (
    echo ==============================================================
    echo Mod packaged successfully: %SGA_FILE%
    echo ==============================================================
    echo.
    echo To install the mod:
    echo   1. Copy %SGA_FILE% to:
    echo      D:\SteamLibrary\steamapps\common\Company of Heroes Relaunch\Mods\ 
    echo   2. Start the Python orchestrator:
    echo      run_mod.bat
    echo   3. Launch CoH1 with command line:
    echo      RelicCOH.exe -modname %MOD_NAME%
    echo.
    echo IMPORTANT: The -modname parameter must match the .sga filename
    echo          (without the .sga extension)
    echo.
    echo Example: %SGA_FILE% -> -modname %MOD_NAME%
    echo.
    echo ==============================================================
) else (
    echo ERROR: Failed to create %SGA_FILE%
    echo Please install 7-Zip or ensure PowerShell Compress-Archive is available
)

endlocal
