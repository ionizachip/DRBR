# Installing DRBR

## What you need

- **DELTARUNE from Steam**, with Chapter 3 installed. DRBR supports DELTARUNE (Steam) Chapter 3 v0.0.105 and checks
  this itself.
- Windows 10 or 11. Nothing else is needed: DRBR uses .NET Framework 4.8, which Windows already has.
- About 1 GB of free disk space.
- Steam running when you play online (DRBR rooms use Steam lobbies).

You do not need UndertaleModTool, a save file, or to play through any chapter. DRBR does not change your DELTARUNE or
your saves.

## Download

Get `DRBR-Setup.exe` from the latest release on the DRBR GitHub page (**Releases**, then **Latest**, then
**DRBR-Setup.exe**). `SHA256SUMS.txt` in the same release lists its checksum.

Windows may say "Windows protected your PC" because the program is not code-signed. Click **More info**, then
**Run anyway**.

## Install

1. Open `DRBR-Setup.exe`.
2. DRBR finds DELTARUNE by itself. It looks at Steam's registry entry, every Steam library listed in
   `steamapps\libraryfolders.vdf` (including custom library folders on other drives), DELTARUNE's Steam app manifest,
   and the usual folders. If it does not find DELTARUNE, click **Browse...** and pick the folder that contains
   `DELTARUNE.exe`.
3. The window shows:
   ```
   DELTARUNE FOUND
   Installation: Compatible
   DRBR Starting Save: Pre-Roaring Knight Room
   [ INSTALL DRBR ]
   ```
4. Click **INSTALL DRBR**. It takes about a minute. DRBR then:
   1. copies the game files it needs from your DELTARUNE into its own folder. Your DELTARUNE is only read, never
      changed.
   2. keeps a clean copy of Chapter 3's `data.win` for repairs and updates.
   3. builds DRBR's `data.win` from that copy with the DRBR patch, and checks it by checksum.
   4. adds the multiplayer files, the songs and the provided starting save.
   5. installs **DRBR Launcher** and adds shortcuts on the desktop and in the Start menu, plus an entry in
      **Settings > Apps**.
   6. checks every installed file.
5. Click **PLAY DRBR**.

**Advanced Options** (the link under the button):

- the install folder (default `%LOCALAPPDATA%\DRBR`; a folder you pick gets its own `DRBR` folder inside it)
- the start mode (below)
- whether to make shortcuts

### If the older Knight Hub is installed in Steam's folder

DRBR notices it and uses the clean backup that the Knight Hub installer kept (`chapter3_windows\data.win.vanilla`). It
leaves Steam's copy as it is. To put the original Chapter 3 back in Steam, run `RESTORE_VANILLA.bat` in Steam's
`chapter3_windows`. You can also let Steam do it: right-click DELTARUNE in Steam, then **Properties > Installed Files >
Verify integrity of game files**. DRBR does not need the Knight Hub any more.

### Other mods

DRBR mentions other mods it sees in the game folder (graphics injectors such as `dxgi.dll`, ReShade) and does not copy
them into DRBR. If Chapter 3's `data.win` is changed by another mod and there is no clean backup, DRBR asks you to
verify the game files in Steam first.

## How you start in front of the Roaring Knight

Every launch loads the provided starting save: Chapter 3, the cold place, story point 320, with Kris, Susie and Ralsei.
You do not pick a save. The start report in DRBR Launcher says "DRBR started in room_dw_snow_zone - the room before the
Roaring Knight". Walk right to the sign just ahead and press **Z**; **ONLINE** is in its menu. DRBR never joins a room
by itself.

The start mode is set in DRBR Launcher > **Settings**:

- **Start from the DRBR starting save every time** (recommended)
- **Continue from my last DRBR save**, which falls back to the starting save

Offline, the Roaring Knight encounter works as in the game. Online, it is blocked; use the sign's ONLINE menu.

See [SAVE_SYSTEM.md](SAVE_SYSTEM.md) for how this works and how your own saves are kept safe.

## Multiplayer

From the hub sign's menu, open **ONLINE**. From there you can:

- host a room
- join one by its code, from the browse list, or from a friend's Steam invite
- practice against a boss

2 to 8 players, plus bots if the host adds them. Every player in a room needs the same DRBR build. A room with a newer
build tells you to update; DRBR Launcher then offers that room again.

## Repair

DRBR Launcher > **Repair Installation** checks every file and rebuilds anything missing or damaged from DRBR's kept
package and your DELTARUNE. Your saves and settings are kept. PLAY also offers a repair when it finds a damaged file.

## Uninstall

Use **Settings > Apps > DRBR > Uninstall**, or DRBR Launcher > Settings > **Uninstall DRBR...**. This removes DRBR's
folder, shortcuts and Apps entry. Your DELTARUNE and all your own DELTARUNE saves are not touched.

You are asked whether to also delete the DRBR story saves (`%LOCALAPPDATA%\DELTARUNE\drbr_profile`). Your DRBR online
settings (skin, SOUL colour, keybinds) always stay, so a reinstall gets them back.

## Silent install (for testers)

```
DRBR-Setup.exe /S [--game "<DELTARUNE folder>"] [--dir "<install folder>"] [--start-mode template|continue] [--no-shortcuts] [--result result.json]
```
