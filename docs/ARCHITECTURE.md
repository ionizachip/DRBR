# DRBR architecture

This page describes how DRBR is put together: the installer, the launcher, the updater, the save profile, the release
pipeline and the security model. File paths are relative to this repository unless they start with `%LOCALAPPDATA%`.

## Overview

```
GitHub Releases (public)          the player's PC
---------------------------       ------------------------------------------------------------------------------
DRBR-Setup.exe  ---------------->  DRBR-Setup.exe ---------------+
update-manifest.json(.sig)                                       |  reads (never writes)
drbr-chapter3.xdelta                                             v
drbr-music-*.zip, drbr-kfsongs.zip   Steam\steamapps\common\DELTARUNE   (DELTARUNE.exe, chapter3_windows\data.win,
kf_steam.dll, steam_api64.dll,                                         its sounds/lang/vid, mus\)
steam_appid.txt, xdelta3.exe                                     |
start_filech3 (the provided save)                                v
DRBR-Launcher.exe, DRBR-Updater.exe   %LOCALAPPDATA%\DRBR\                      (everything DRBR owns)
                                       DRBR Launcher.exe, DRBR Updater.exe, tools\xdelta3.exe
           ^                           game\  DELTARUNE.exe + chapter3_windows\ (DRBR data.win, the game's own files,
           | signed manifest,                  mus\, kfsongs\, kf_steam.dll..., drbr_data\start_filech3 + drbr_profile.cfg)
           | HTTPS downloads           base\data.win.vanilla      payload\ (the installed release package)
           +---------------------------save-profile\ (template copy, profile.json)   logs\  backups\  staging\
                                       drbr-install.json, drbr-settings.json
                                      %LOCALAPPDATA%\DELTARUNE\drbr_profile\   (the game's DRBR saves, DRBR mode only)
```

## Why DRBR is a separate copy of the game

DRBR builds and runs its own copy of DELTARUNE:

- `DELTARUNE.exe`, the GameMaker runner, copied from the player's Steam install
- Chapter 3's own files (`*.ogg`, `*.dat`, `options.ini`, `lang\`, `vid\`) and the music (`mus\`)
- a `data.win` patched from the player's own vanilla `data.win`

The game is started the same way the Knight Hub's `PLAY_KNIGHT_HUB.bat` started it: `DELTARUNE.exe -game
"chapter3_windows\data.win"`, in the game folder. The music sits next to `data.win` because the runner looks for `mus\`
there. A junction `game\mus` points at it as well.

Why a copy:

- Steam's DELTARUNE is never modified. Vanilla Chapter 3 stays vanilla, Steam's *Verify integrity* never undoes DRBR,
  and a DELTARUNE update in Steam never breaks DRBR.
- Save isolation is reliable: a bundle file (`drbr_data\drbr_profile.cfg`) tells the DRBR build that it is DRBR.
- Uninstalling means deleting one folder.
- No administrator rights are needed: everything is per user in `%LOCALAPPDATA%`.

No DELTARUNE file is distributed as a file:

- The release holds a binary patch (xdelta3 / VCDIFF) from the player's own vanilla `data.win`. It applies only to that
  file.
- The installer copies the player's own game files on the player's own machine.
- Supported vanilla builds are listed by size and SHA-256 in `drbr.json` (currently DELTARUNE (Steam) Chapter 3
  v0.0.105, `c1a09253...`).

The patch does carry what the mod adds to Chapter 3: the knight fights, and the five bosses' code and art taken from
Chapters 1, 2, 4 and 5 when the mod is built. The fight songs are third-party works. See "What a release contains" in
[RELEASING.md](RELEASING.md) before a public release.

## Programs

All three are C# for **.NET Framework 4.8**, which is part of every Windows 10/11, so nothing extra has to be installed.
They are built with the .NET SDK on Windows or Linux (`src/Directory.Build.props`, `EnableWindowsTargeting`). The
shared logic in `src/Drbr.Core/*.cs` is compiled into each program, so each `.exe` is a single file with no DLLs. The
same sources are compiled for .NET 10 in `src/Drbr.Tests`.

| Program | Project | What it does |
|---|---|---|
| `DRBR-Setup.exe` | `src/Drbr.Setup` | The one-screen installer: DELTARUNE FOUND / Installation: Compatible / DRBR Starting Save / [INSTALL DRBR] / Advanced Options. Silent mode: `/S`. It carries the payload appended to the exe (a zip, then an 8-byte length, then `DRBRPAY1`), or a `payload\` folder next to it, whose large files may be split into `.partN` pieces. |
| `DRBR Launcher.exe` | `src/Drbr.Launcher` | Play DRBR, Check for Updates, Install Update, Repair Installation, Restore Starting Save, Settings, Release Notes, Open Installation Folder, Uninstall. Has a command-line mode with the same actions for scripts and tests (`--play --check --update --repair --restore-save --verify --uninstall --result <json>`). |
| `DRBR Updater.exe` | `src/Drbr.Updater` | Replaces `DRBR Launcher.exe` with its new version once the launcher has closed: it waits, checks the checksum, swaps the files, puts the old one back on failure, and restarts the launcher. |

### Core modules (`src/Drbr.Core`)

| File | Responsibility |
|---|---|
| `Game.cs` | `DrbrPaths` (every folder). `GameLocator`: Steam's registry entries, `libraryfolders.vdf` (every library), `appmanifest_1671210.acf`, common drive paths. `GameCheck`: vanilla / the older Knight Hub in place (its verified `data.win.vanilla`) / modified / unsupported, plus other mods' DLLs, and which Chapter 3 files are the game's own. |
| `Install.cs` | `InstallEngine`: install, reinstall, repair and update are one transaction (below). Also `VerifyInstall` and `Uninstall`, and `Settings` (`drbr-settings.json`). |
| `SaveProfile.cs` | The template (validation, the bundle, repair), the cfg the game reads, `Migrate`, `RestoreStartingSave`, `last_start.ini`, and the snapshot of the player's own saves. |
| `Manifest.cs` | `payload.json` / `update-manifest.json` (schema 1), and RSA signature verification. |
| `Update.cs` | `UpdateEngine` (check, download only what changed, resume) and HTTP downloads with SHA-256 checks. |
| `Launch.cs` | `LauncherCore`: PLAY (checks, starting-save checks, start, wait for the start report, after-game check), apply update, repair, pending room. |
| `Platform.cs` | Processes (is DRBR's game running, start it, run xdelta3), shortcuts (WScript.Shell), the per-user uninstall entry, junctions. |
| `Json.cs`, `Util.cs` | A small JSON reader/writer, the log (`%LOCALAPPDATA%\DRBR\logs`), hashes, versions, file helpers. |
| `BuildInfo.g.cs` | Generated from `drbr.json` by `packaging/gen_buildinfo.py`: versions, the GitHub update address, the **public** signing key. |

## The install transaction (`InstallEngine.Install`)

1. **Recover.** An interrupted earlier transaction (`drbr-transaction.json`) is undone: the previous copy is put back
   and the staging files are removed.
2. **Check the package.** Every file in `payload.json` is checked for size and SHA-256, and the starting save is
   validated.
3. **Check the game.** It must be compatible (a supported vanilla `data.win` or the verified older Knight Hub backup). An
   update or repair can instead build from DRBR's own copy (`base\data.win.vanilla` + `game\`). The game must not be
   running, and there must be enough free disk space.
4. **Stage.** Everything is built in `staging\<op>-<time>\`:
   1. copy the game's files
   2. keep a verified vanilla copy
   3. `xdelta3 -d -s vanilla drbr-chapter3.xdelta data.win`, then check the result's SHA-256
   4. add the mod's files, the music (checked per song) and the song pack
   5. add the starting save and the cfg
   6. keep the package
5. **Switch.** The old `game\` is renamed to `backups\game-<time>`, then the new one is renamed in (same drive, one
   rename each). The base copy, the package, the programs and `save-profile\` follow, then `drbr-install.json` is
   written. A launcher that is running cannot replace itself, so its new copy waits in `staging\pending\` for
   DRBR Updater.
6. **Verify.** `VerifyInstall(true)` hashes `data.win`, the template and every mod file.
7. **Roll back** on any failure at any step. The old `game\`, package and state are put back. A failed first install
   leaves nothing behind.

Tests force a failure at each stage (`DRBR_TEST_FAIL_AT`: copy, patch, music, profile, commit, verify) and kill the
process in the middle of a reinstall.

## Updates

1. The launcher downloads `update-manifest.json` and `update-manifest.json.sig` from
   `https://github.com/<owner>/<repo>/releases/latest/download/` (`BuildInfo.UpdateManifestUrl`).
2. **The signature must verify** with the public key built into the launcher: RSA-3072, PKCS#1 v1.5, SHA-256, over the
   manifest's exact bytes. Otherwise nothing is downloaded.
3. It compares the release's `version` with the installed one, `launcher_version` with its own, `min_launcher_version`,
   and `protocol` (the online build: `kfo_version()`). It shows *DRBR UPDATE AVAILABLE* with [UPDATE NOW] and
   [PLAY CURRENT VERSION]. If the protocol changed, it says that online play needs the update.
4. **Downloads** go to `staging\download-<version>\`. A file the installed package already has, by SHA-256, is copied
   instead of downloaded. Downloads resume with an HTTP Range from `.part` files. A file that fails its SHA-256 is
   deleted, downloaded once more, then refused.
5. The downloaded package is installed with the same transaction as an install (above).
6. A new launcher is swapped in by DRBR Updater.

There is no background service: checks happen when the launcher opens (this can be turned off in Settings) or on demand.

## The game side (`mod/gml/drbr_save54.gml`, hooks in `mod/scripts/gen_hub.py`)

- `kdr_on()`: DRBR mode is on when `drbr_data/drbr_profile.cfg` is in the bundle.
- `kdr_boot()`: called from `obj_initializer2` instead of going to the intro. It validates the template, copies it, then
  runs the file menu's CONTINUE sequence and `scr_load()`.
- `kdr_path()`: wraps the five `ossafe_*` file functions and the CONFIG menu's own `ini_open`, so story files live in
  `drbr_profile/`.
- `kdr_frame()`: called from `obj_gamecontroller`'s Begin Step. It writes the start report once the first room is
  reached, then offers a pending room (below).
- `kdr_chapter_switch()`: `scr_chapterswitch` in DRBR mode, at the end of Chapter 3 or from the chapter select, restarts
  at the DRBR start, because the DRBR install has no other chapter.

Details are in [SAVE_SYSTEM.md](SAVE_SYSTEM.md).

## Multiplayer version checks

The mod already checks, when a player joins a room, that everyone has the same build (`kfo_version()`, the
"protocol") and the same boss and attack catalogue (`kbr_roster_sig()`). This applies to Steam lobbies, relay rooms and
the browse list.

DRBR adds the following when a room has a **newer** build:

1. The game writes `drbr_profile/pending_join.ini`, holding only the lobby number and the builds, and tells the player
   to update through DRBR Launcher.
2. The launcher sees the file and offers the update.
3. After the update, the game offers that room again in the invite box (JOIN / NOT NOW).

This is offered only when the game now has that room's build and the note is less than an hour old. The game never
joins by itself, and nothing a room or host sends can choose a download. Downloads only come from the release
addresses in a manifest signed with DRBR's key.

## Security model

| Rule | How |
|---|---|
| No token in the installer or launcher | Release assets and `releases/latest/download` are public, so no authentication is needed. Publishing uses the maintainer's own `gh` login, or the workflow's `GITHUB_TOKEN` in Actions. |
| Only DRBR's releases are installed | Every manifest is RSA-signed with the release key and checked against the public key compiled into the launcher. Every file is checked by the SHA-256 the signed manifest gives. |
| The private key never ships | It is kept by the maintainer (see RELEASING.md). `.gitignore` excludes `*.pem`, and CI fails if a private key is committed. |
| No DELTARUNE files in releases | Releases contain the binary patch, the mod's files and the provided save ("What a release contains" in RELEASING.md lists what the patch and the songs carry). The repository holds none of them: CI fails on `*.win`, `*.xdelta`, saves other than the provided one, and settings files. |
| Paths cannot escape | Manifest file names may not contain `/`, `\`, `:` or `..`. Every destination goes through `Fs.Under(root, rel)`. |
| A multiplayer host cannot choose downloads | The game only records a lobby number. The launcher's only source is the signed manifest. |
| Vanilla DELTARUNE and saves are safe | Steam's folder is only read. Story saves are redirected. The launcher snapshots your saves before and after PLAY. |
| No admin rights, no service | Everything is installed per user, with `asInvoker` in the app manifest and no background process. |

Known limits:

- The programs are not code-signed, so Windows SmartScreen may warn the first time. A code-signing certificate would
  remove that warning.
- `DRBR-Setup.exe` itself is trusted through GitHub's HTTPS and `SHA256SUMS.txt`. Once installed, the launcher only
  accepts signed releases.

## Release pipeline

```
author's machine (has the DELTARUNE files)                  GitHub
scripts/build-drbr.sh     mod -> data.win -> in-place package
scripts/package-drbr.sh   programs + payload + DRBR-Setup.exe + signed manifest + checks
scripts/release-drbr.sh   tag + DRAFT release with every asset  ---->  .github/workflows/release.yml
                                                                       build from source + tests, download the draft,
                                                                       check signature + every checksum + the Setup,
                                                                       publish after approval ("release" environment)
```

The game patch has to be built where the DELTARUNE files are, so it is made locally and never on a hosted runner.
`.github/workflows/ci.yml` checks every push: it builds the programs, runs the core tests and the emulator selftest,
validates the starting save, and refuses private or proprietary files.
