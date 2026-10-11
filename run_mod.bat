@echo off
REM CoH1 × Mistral AI Mod - Run Script
REM
REM This script runs the Python orchestrator service for the mod.
REM
REM Usage:
REM   run_mod.bat              - Run with default config
REM   run_mod.bat --test      - Run in test mode with mock data
REM   run_mod.bat --debug     - Run with debug logging
REM   run_mod.bat --test --debug  - Run in test mode with debug logging

setlocal

set PYTHON=python
set SCRIPT_DIR=%~dp0

REM Check if Python is in PATH
%PYTHON% --version >nul 2>&1
if errorlevel 1 (
    echo Checking for Python...
    where python >nul 2>&1
    if errorlevel 1 (
        echo ERROR: Python not found in PATH
        echo Please install Python 3.10+ and add it to your PATH
        goto :EOF
    )
)

REM Navigate to the mod directory
cd /d "%SCRIPT_DIR%"

echo ==============================================================
echo CoH1 × Mistral AI Mod Orchestrator
echo ==============================================================
echo.
echo Starting the orchestrator service...
echo.
echo The orchestrator will:
echo   - Read game state from SCAR mod
echo   - Make AI decisions using Mistral
echo   - Send commands back to SCAR mod
echo   - Log all game state for analysis
echo.
echo Press Ctrl+C to stop the service
echo.

REM Run the orchestrator with all passed arguments
%PYTHON% python\main.py %*

echo.
echo Orchestrator stopped
echo.

endlocal
