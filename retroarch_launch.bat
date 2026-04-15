@echo off
rem T3MPLATE TV WORLD - RetroArch Manual/Visual Mode (FULL_VISION Windows Integration)

set RETROARCH_PATH=%RETROARCH_PATH%
if "%RETROARCH_PATH%"=="" set RETROARCH_PATH=C:\RetroArch-Win64\retroarch.exe

set CORE_PATH=cores\lutro_libretro.dll
set ROM_PATH=%CD%\assets\ASSETS\t3mplate_tv.sfc
set CFG_PATH=%CD%\engine\retroarch.cfg

echo RETROARCH: %RETROARCH_PATH%
echo ROM: %ROM_PATH%
echo CFG: %CFG_PATH%

if not exist "%RETROARCH_PATH%" (
    echo ERROR: RetroArch not found at %RETROARCH_PATH%
    echo Install from https://retroarch.com or update RETROARCH_PATH in .env
    pause
    exit /b 1
)

if not exist "%ROM_PATH%" (
    echo ERROR: SFC ROM not found at %ROM_PATH%
    pause
    exit /b 1
)

echo Launching RetroArch Lutro...
"%RETROARCH_PATH%" -L "%CORE_PATH%" "%ROM_PATH%" --verbose --config="%CFG_PATH%" --fullscreen

echo Launched - Capture in OBS!
pause

