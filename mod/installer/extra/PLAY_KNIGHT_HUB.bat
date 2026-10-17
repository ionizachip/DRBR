@echo off
rem PLAY KNIGHT HUB - one double-click does everything:
rem   1. finds your DELTARUNE Chapter 3 folder (Steam), 2. copies the Knight Hub files into it if they are not there yet
rem      (build 45: with kf_steam.dll, steam_api64.dll and steam_appid.txt for the Steam rooms of KNIGHT FIGHTS ONLINE),
rem   3. installs the hub and replaces any older Knight Hub build, 4. starts Chapter 3.
rem You can run this from the downloaded "Knight Hub v2 (build N)" folder or from chapter3_windows. Steam should be running.
setlocal DisableDelayedExpansion
title Play Knight Hub
set "HERE=%~dp0"
set "KH_NOPAUSE=1"
set "KH_ASSUME_YES=1"

if exist "%HERE%..\DELTARUNE.exe" goto :inplace

set "GAME="
if exist "%ProgramFiles(x86)%\Steam\steamapps\common\DELTARUNE\DELTARUNE.exe" set "GAME=%ProgramFiles(x86)%\Steam\steamapps\common\DELTARUNE"
if defined GAME goto :found
if exist "%ProgramFiles%\Steam\steamapps\common\DELTARUNE\DELTARUNE.exe" set "GAME=%ProgramFiles%\Steam\steamapps\common\DELTARUNE"
if defined GAME goto :found
set "SP="
for /f "tokens=2,*" %%A in ('reg query "HKCU\Software\Valve\Steam" /v SteamPath 2^>nul') do set "SP=%%B"
if defined SP set "SP=%SP:/=\%"
if defined SP if exist "%SP%\steamapps\common\DELTARUNE\DELTARUNE.exe" set "GAME=%SP%\steamapps\common\DELTARUNE"
if defined GAME goto :found
for %%D in (C D E F G H) do if not defined GAME if exist "%%D:\SteamLibrary\steamapps\common\DELTARUNE\DELTARUNE.exe" set "GAME=%%D:\SteamLibrary\steamapps\common\DELTARUNE"
if defined GAME goto :found

echo Could not find DELTARUNE automatically.
set /p "GAME=Paste the DELTARUNE folder (the one that contains DELTARUNE.exe) and press Enter: "
set "GAME=%GAME:"=%"
if exist "%GAME%\DELTARUNE.exe" goto :found
echo That folder does not contain DELTARUNE.exe. Nothing was changed.
pause
exit /b 1

:found
set "TARGET=%GAME%\chapter3_windows"
if exist "%TARGET%\data.win" goto :copy
echo Found "%GAME%" but there is no chapter3_windows\data.win in it. Start Chapter 3 once from Steam, then run this again.
pause
exit /b 1

:copy
echo Found Deltarune: %GAME%
echo Copying the Knight Hub files into chapter3_windows ...
rem build 50: every file is checked BEFORE anything in the game folder is touched (an older copy of this .bat in a folder
rem without the package deleted the patch parts in chapter3_windows and then stopped)
for %%F in (INSTALL_KNIGHT_HUB.bat install_knight_hub.ps1 RESTORE_VANILLA.bat KNIGHT_HUB_MANIFEST.txt xdelta3.exe knight_hub_extras.zip README_INSTALL.txt SHA256SUMS.txt LAUNCH_CHAPTER_3.bat kf_steam.dll steam_api64.dll steam_appid.txt DRBR_ONLINE_GUIDE.txt) do if not exist "%HERE%%%F" goto :missing
if not exist "%HERE%knight_hub_chapter3.xdelta.part0" goto :missing
rem build 52: a NEWER Knight Hub already in the game (its installer wrote knight_hub_build.txt): this older folder copies
rem nothing and the game's own newer copy runs (an older folder's PLAY used to put its older build back over the newer one)
set "MYV=0"
for /f "tokens=2 delims==" %%V in ('findstr /b /c:"mod_version=" "%HERE%KNIGHT_HUB_MANIFEST.txt" 2^>nul') do set "MYV=%%V"
set "INV=0"
if exist "%TARGET%\knight_hub_build.txt" for /f "tokens=2 delims==" %%V in ('findstr /b /c:"mod_version=" "%TARGET%\knight_hub_build.txt" 2^>nul') do set "INV=%%V"
if %INV% GTR %MYV% goto :newer
del /q "%TARGET%\knight_hub_chapter3.xdelta.part*" >nul 2>&1
copy /y "%HERE%knight_hub_chapter3.xdelta.part*" "%TARGET%\" >nul || goto :copyfail
for %%F in (INSTALL_KNIGHT_HUB.bat install_knight_hub.ps1 RESTORE_VANILLA.bat KNIGHT_HUB_MANIFEST.txt xdelta3.exe knight_hub_extras.zip README_INSTALL.txt SHA256SUMS.txt LAUNCH_CHAPTER_3.bat kf_steam.dll steam_api64.dll steam_appid.txt DRBR_ONLINE_GUIDE.txt) do copy /y "%HERE%%%F" "%TARGET%\" >nul || goto :copyfail
rem build 47: the new fight songs (optional: the hub works without them)
if exist "%HERE%knight_hub_music.zip" copy /y "%HERE%knight_hub_music.zip" "%TARGET%\" >nul || goto :copyfail
if exist "%HERE%knight_hub_music2.zip" copy /y "%HERE%knight_hub_music2.zip" "%TARGET%\" >nul || goto :copyfail
rem build 50: the Claude Music Handoff's songs
if exist "%HERE%knight_hub_music3.zip" copy /y "%HERE%knight_hub_music3.zip" "%TARGET%\" >nul || goto :copyfail
if exist "%HERE%knight_hub_music4.zip" copy /y "%HERE%knight_hub_music4.zip" "%TARGET%\" >nul || goto :copyfail
rem build 50: the KF Song Pack's songs (optional; the installer unpacks them into kfsongs next to data.win)
if exist "%HERE%knight_hub_kfsongs.zip" copy /y "%HERE%knight_hub_kfsongs.zip" "%TARGET%\" >nul || goto :copyfail
if exist "%HERE%KF_SONG_CREDITS.txt" copy /y "%HERE%KF_SONG_CREDITS.txt" "%TARGET%\" >nul || goto :copyfail
copy /y "%~f0" "%TARGET%\PLAY_KNIGHT_HUB.bat" >nul || goto :copyfail
call "%TARGET%\PLAY_KNIGHT_HUB.bat"
exit /b %ERRORLEVEL%

:newer
echo The game already has a NEWER Knight Hub (build %INV%) than this folder (build %MYV%).
echo Nothing was copied. Starting the newer one...
if not exist "%TARGET%\PLAY_KNIGHT_HUB.bat" goto :copy_anyway
call "%TARGET%\PLAY_KNIGHT_HUB.bat"
exit /b %ERRORLEVEL%
:copy_anyway
echo The game folder has no PLAY_KNIGHT_HUB.bat; run PLAY_KNIGHT_HUB.bat from the newest Knight Hub folder instead.
pause
exit /b 1

:missing
echo A Knight Hub file is missing next to this .bat: %HERE%
echo Keep ALL files of the package together, then run this again.
pause
exit /b 1

:copyfail
net session >nul 2>&1
if not errorlevel 1 goto :copyfail2
echo Windows needs permission to write into the game folder. Asking for administrator rights...
powershell -NoProfile -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
exit /b 0
:copyfail2
echo Could not copy the files into "%TARGET%". Nothing was started.
pause
exit /b 1

:inplace
cd /d "%HERE%"
if not exist "INSTALL_KNIGHT_HUB.bat" (
  echo INSTALL_KNIGHT_HUB.bat is not next to this file. Keep all Knight Hub files together in chapter3_windows.
  pause
  exit /b 1
)
if not exist "RESTORE_VANILLA.bat" (
  echo RESTORE_VANILLA.bat is not next to this file. Keep all Knight Hub files together in chapter3_windows.
  pause
  exit /b 1
)

echo Step 1/4: installing / checking the Knight Hub...
call "INSTALL_KNIGHT_HUB.bat"
set "RC=%ERRORLEVEL%"
if "%RC%"=="0" goto :launch
rem build 52: 17 = a newer Knight Hub is installed than this package - it is kept and started
if "%RC%"=="17" goto :launch
if not "%RC%"=="6" goto :failed

echo.
echo Your data.win is an older Knight Hub build (or otherwise not this one).
echo Step 2/4: removing the old version (restoring the original data.win from the backup)...
call "RESTORE_VANILLA.bat"
if errorlevel 1 goto :restorefailed
echo.
echo Step 3/4: installing the new Knight Hub...
call "INSTALL_KNIGHT_HUB.bat"
if errorlevel 1 goto :failed

:launch
echo.
echo Step 4/4: starting Deltarune Chapter 3...
cd /d "%~dp0.."
rem The game looks for its music (the mus folder) next to the data.win it was started with,
rem but the music lives one folder up. Link it once so the music is found.
if exist "mus" if not exist "chapter3_windows\mus" mklink /J "chapter3_windows\mus" "mus" >nul
start "" "DELTARUNE.exe" -game "chapter3_windows\data.win"
exit /b 0

:restorefailed
echo.
echo Could not put the original data.win back (no valid backup?). The game was NOT started.
echo Fix: Steam ^> right-click DELTARUNE ^> Properties ^> Installed Files ^> Verify integrity of game files,
echo then run this file again. Details are in knight_hub_install.log in this folder.
pause
exit /b 1

:failed
echo.
echo The installer reported a problem, so the game was NOT started.
echo Details are in knight_hub_install.log in this folder.
pause
exit /b 1
