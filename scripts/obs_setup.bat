@echo off
REM OBS + RetroArch Setup for T3MPLATE TV
REM Capture Lutro window for streaming

REM Start RetroArch with Lutro core + main.lua
start RetroArch.exe -L cores/lutro_libretro.dll engine/lua/main.lua --config conf.lua

REM Wait for startup
timeout /t 5

REM OBS Scene preset (JSON export)
powershell -Command "Add-Type -Path 'C:\Program Files\obs-studio\bin\64bit\obs-api.dll'; obs-create-scene-from-json 'assets/obs_scene.json'"

echo "Broadcast ready - Capture RetroArch window at 1280x720 60fps"
echo "API status: http://localhost:8080/status"
