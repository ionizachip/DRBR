@echo off
rem Launches Deltarune Chapter 3 directly (skips the chapter select).
rem Keep this file in the chapter3_windows folder. Steam should be running.
cd /d "%~dp0.."
if not exist "DELTARUNE.exe" (
  echo Could not find DELTARUNE.exe one folder above this file.
  echo Keep LAUNCH_CHAPTER_3.bat inside the chapter3_windows folder.
  pause
  exit /b 1
)
rem The game looks for its music (the mus folder) next to the data.win it was started with,
rem but the music lives one folder up. Link it once so the music is found.
if exist "mus" if not exist "chapter3_windows\mus" mklink /J "chapter3_windows\mus" "mus" >nul
start "" "DELTARUNE.exe" -game "chapter3_windows\data.win"
