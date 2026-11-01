@echo off
REM Fixed Mod Packaging Script for CoH1 AI Mod
REM This fixes the issue where files were being packaged inside temp_package/

setlocal

set MOD_NAME=coh1_mistral_ai
set SGA_FILE=%MOD_NAME%.sga
set TEMP_DIR=temp_package_fixed

REM Clean up previous temp directory
if exist "%TEMP_DIR%" rmdir /s /q "%TEMP_DIR%"

REM Create temp directory
mkdir "%TEMP_DIR%"

REM Copy SCAR files directly to temp directory root (not in a subfolder)
copy scar\config.scar "%TEMP_DIR%\config.scar" >nul
copy scar\ipc.scar "%TEMP_DIR%\ipc.scar" >nul
copy scar\main.scar "%TEMP_DIR%\main.scar" >nul
copy scar\serializer.scar "%TEMP_DIR%\serializer.scar" >nul
copy scar\state_collector.scar "%TEMP_DIR%\state_collector.scar" >nul

REM Check if reflex_layer.scar exists
if exist scar\reflex_layer.scar (
    copy scar\reflex_layer.scar "%TEMP_DIR%\reflex_layer.scar" >nul
)

REM Check if command_executor.scar exists
if exist scar\command_executor.scar (
    copy scar\command_executor.scar "%TEMP_DIR%\command_executor.scar" >nul
)

REM Create mod.ini file
(
    echo [General]
    echo ModName=%MOD_NAME%
    echo ModVersion=0.2.0
    echo Description=CoH1 AI Mod powered by Mistral
    echo Author=CoH1 AI Mod Team
    echo CompatibleVersion=1.0
    echo Type=AI
) > "%TEMP_DIR%\mod.ini"

REM Package using 7-Zip
if exist "C:\Program Files\7-Zip\7z.exe" (
    cd "%TEMP_DIR%"
    "C:\Program Files\7-Zip\7z.exe" a -tzip "..\%SGA_FILE%" * -mx=1 >nul
    cd ..
) else if exist "C:\Program Files (x86)\7-Zip\7z.exe" (
    cd "%TEMP_DIR%"
    "C:\Program Files (x86)\7-Zip\7z.exe" a -tzip "..\%SGA_FILE%" * -mx=1 >nul
    cd ..
) else (
    REM Use PowerShell
    powershell -command "& {Set-Location '%TEMP_DIR%'; Compress-Archive -Path * -DestinationPath '..\%SGA_FILE%' -CompressionLevel Optimal}" >nul 2>&1
    
    if not exist "%SGA_FILE%" (
        REM Fallback: Use tar from parent directory
        cd ..
        tar -czf "%SGA_FILE%" -C "%TEMP_DIR%" . >nul 2>&1
        cd "%TEMP_DIR%"
    )
)

cd ..

REM Clean up temp directory
if exist "%TEMP_DIR%" rmdir /s /q "%TEMP_DIR%"

if exist "%SGA_FILE%" (
    echo ==============================================================
    echo Mod packaged successfully: %SGA_FILE%
    echo ==============================================================
    echo.
    echo Archive contents:
    
    REM Show contents to verify
    if exist "C:\Program Files\7-Zip\7z.exe" (
        "C:\Program Files\7-Zip\7z.exe" l "%SGA_FILE%"
    ) else if exist "C:\Program Files (x86)\7-Zip\7z.exe" (
        "C:\Program Files (x86)\7-Zip\7z.exe" l "%SGA_FILE%"
    ) else (
        unzip -l "%SGA_FILE%"
    )
    
    echo.
    echo To install the mod:
    echo   1. Copy %SGA_FILE% to:
    echo      D:\SteamLibrary\steamapps\common\Company of Heroes Relaunch\Mods\ 
    echo   2. Start the Python orchestrator:
    echo      run_mod.bat
    echo   3. Launch CoH1 with command line:
    echo      RelicCOH.exe -mod coh1_mistral_ai
    echo.
    echo ==============================================================
) else (
    echo ERROR: Failed to create %SGA_FILE%
    echo Please install 7-Zip or ensure PowerShell Compress-Archive is available
)

endlocal
