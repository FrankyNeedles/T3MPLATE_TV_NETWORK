@echo off
REM OBS Capture Script: Pygame/Lutro window + VB-Cable audio mix, export RTMP
REM Assume OBS installed, VB-Cable for virtual audio

REM Start Pygame renderer (window capture source)
start python app/renderer.py

REM Start Lutro emu (another source)
start lua app/main.lua

REM Start audio mix to VB-Cable
start python app/audio.py  # Routes to VB-Cable

REM OBS batch (mock): Add sources window/Pygame.exe, Lutro, audio VB-Cable, scene SNES TV
REM Start OBS, set stream rtmp://localhost/live/key (mock)

REM Export RTMP
obs64.exe --startstreaming --profile Default --scene "SNES Broadcast" --url rtmp://localhost/live --key dummy_key

REM Stop after 1hr
timeout /t 3600
taskkill /f /im python.exe /im lua.exe /im obs64.exe