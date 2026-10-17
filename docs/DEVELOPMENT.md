# Developing DRBR

## Layout

```
drbr.json                 versions, the GitHub repository, the public signing key, supported DELTARUNE builds, save profile
src/                      the Windows programs (C#, .NET Framework 4.8) and their core tests (.NET 10)
  Drbr.Core/              shared logic (compiled into every program)    Drbr.Setup/ Drbr.Launcher/ Drbr.Updater/ Drbr.Tests/
  assets/drbr.ico         the programs' icon        app.manifest   Directory.Build.props   VERSION (generated)
save-profile/
  starting-save/          start_filech3: the provided starting save (exact bytes)
  profile-config/         profile.json: the profile schema and defaults
  migration/              migrations.json: the profile migrations (none yet)
packaging/                gen_buildinfo.py, make_payload.py, release_tools.py (sign / setup / release / check), split_payload.py
scripts/                  build-drbr.sh, test-drbr.sh, test-core.sh, package-drbr.sh, release-drbr.sh, build-installer.sh,
                          validate-save.py, sync-mod-sources.sh
tests/                    installation/ (Wine end to end, window screenshots, the game stand-in), updates/ (release
                          server, test releases), save-loading/, multiplayer/
mod/                      the game mod's own sources: gml/ (the GML templates), scripts/ (the generators and the build
                          scripts), tests/ (emulator tests), build/ (data.win build and checks), installer/ (the older in-place
                          Knight Hub package), online-server/, online-steam/ (kf_steam.dll's source), notes/
tools/gmlsim/             the GameMaker emulator the mod's tests run on
docs/                     these documents
.github/workflows/        ci.yml (every push), release.yml (check and publish a draft release)
```

`mod/` holds only the mod's own code. Decompiled DELTARUNE code (the bosses' generated `*_gen` folders, base-game code
dumps), DELTARUNE's data files, and anyone's saves are not in the repository (`.gitignore`, and CI refuses them). They
are made on the build machine from the player-owned game files. Before you make the repository public, decide whether
`mod/` should be in it. It includes the knight mods' patch rules (`mod/scripts/rules`).

## Dependencies

| For | Needs |
|---|---|
| The Windows programs | The .NET SDK (8 or later; 10 is used here), on Windows or Linux. The `Microsoft.NETFramework.ReferenceAssemblies` package comes from NuGet, so no Visual Studio is needed. |
| Packaging and signing | Python 3 with `cryptography` (`pip install cryptography`), and `openssl` |
| The core tests | the .NET SDK, `xdelta3` (Linux) or `tools\xdelta3.exe` (Windows), the vanilla Chapter 3 `data.win`, the private key |
| Windows end to end on Linux | Wine (wine64), wine-mono, Xvfb, xdotool, ImageMagick |
| The game mod | Python 3, the UndertaleModTool CLI, and the DELTARUNE data files of the build machine (see `mod/scripts/gen_hub.py` and `mod/build/runbuild51.sh`) |

## Build

```
scripts/build-installer.sh                         # DRBR Launcher.exe, DRBR Updater.exe, DRBR-Setup.exe -> build/bin
scripts/build-installer.sh <payload dir> build     # + build/DRBR-Setup.exe with that payload appended
python3 packaging/make_payload.py --pkg <game package> --apps build/bin --out build/payload --version 1.0.0
```

For development, `DRBR-Setup.exe` also accepts a `payload\` folder next to it, whose big files may be split:
`packaging/split_payload.py build/payload <folder>\payload`.

## Tests

```
scripts/test-core.sh build/payload <vanilla data.win> <private key> [groups]
    groups: basics signature manifest save game install repair failures interrupt update join uninstall
tests/installation/wine_e2e.sh build/DRBR-Setup.exe build/payload <vanilla data.win> <private key> build/stub
tests/installation/wine_gui.sh build/DRBR-Setup.exe build/gui-shots build/payload <private key>   # screenshots to look at
scripts/test-drbr.sh mod                           # the save profile in the game code (emulator; needs the mod build environment)
cd tools/gmlsim && python3 -m gmlsim.selftest      # the emulator itself (runs anywhere, also in CI)
```

The mod's emulator tests (`mod/tests/`) run the real merged GML, which `gen_hub.py` makes from the decompiled game on
the build machine. So they run only where the mod is built (`DRBR_MOD_WORK`), never in CI.

`build/stub` is built from `tests/installation/GameStub`. It is **a test stand-in for DELTARUNE.exe**: it does with the
files what the DRBR build's start does (checks the template, copies it, writes `last_start.ini`), so the launcher's PLAY
can be tested under Wine. It is never shipped. Results from it say nothing about the real game. The real game code's
start is tested in the emulator (`t_drbr_save54.py`).

## Debugging

| Where to look | What it holds |
|---|---|
| `%LOCALAPPDATA%\DRBR\logs\drbr-YYYY-MM-DD.log` | every step of Setup, the launcher and the updater, with the reason for any failure |
| `%LOCALAPPDATA%\DELTARUNE\drbr_profile\last_start.ini` | the game's own report of its last DRBR start |
| `%LOCALAPPDATA%\DRBR\drbr-install.json` | what is installed: versions, the source game, checksums |
| `%LOCALAPPDATA%\DRBR\drbr-transaction.json` | present only while a transaction runs, or after one was interrupted |
| `DRBR Launcher.exe --verify --result r.json` | what is wrong with an install, without a window |
| `DRBR_TEST_FAIL_AT=copy\|patch\|music\|profile\|commit\|verify` | forces an install to fail at that stage (rollback tests) |
| `DRBR_UPDATE_URL` or `update_url_override` in `drbr-settings.json` | another release server, for tests. The signature key never changes. |

## Conventions

- Every file DRBR writes is under its own folder, except the game's DRBR saves (`drbr_profile\`).
- Install, repair and update are one transaction (`InstallEngine.Install`). Do not add a second way to change files.
- Every file in a release is listed with its size and SHA-256, and is checked after every copy, download and patch.
- Player-facing messages say what happened and what to do, and never blame the player.
