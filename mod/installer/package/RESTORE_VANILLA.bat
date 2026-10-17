@echo off
rem Knight Hub restore launcher (puts data.win.vanilla back). All logic lives in install_knight_hub.ps1.
rem Delayed expansion is deliberately NOT enabled (folder names may contain !).
setlocal DisableDelayedExpansion
title Knight Hub - restore vanilla
set "KH_PS=powershell.exe"
if exist "%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe" set "KH_PS=%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe"
if not exist "%~dp0install_knight_hub.ps1" goto :noscript
"%KH_PS%" -NoProfile -ExecutionPolicy Bypass -File "%~dp0install_knight_hub.ps1" -Restore %*
set "KH_RC=%ERRORLEVEL%"
echo.
echo Knight Hub restore finished with exit code %KH_RC%.
if not defined KH_NOPAUSE pause
exit /b %KH_RC%

:noscript
echo ERROR: install_knight_hub.ps1 is not next to this file. Keep ALL files of the Knight Hub package together.
if not defined KH_NOPAUSE pause
exit /b 2
