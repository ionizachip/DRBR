@echo off
rem Knight Fights Online relay server - needs Node.js 18 or newer (https://nodejs.org)
cd /d "%~dp0"
where node >NUL 2>NUL
if errorlevel 1 (
  echo Node.js was not found. Install it from https://nodejs.org ^(the LTS version^), then run this again.
  pause
  exit /b 1
)
echo Starting the Knight Fights relay on port 7777. Players type this PC's address as SERVER in the game.
echo Close this window to stop it.
node relay.js %*
pause
