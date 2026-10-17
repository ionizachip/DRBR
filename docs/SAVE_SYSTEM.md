# DRBR save system

DRBR always starts in the same place: Chapter 3's cold place (`room_dw_snow_zone`), just before the Roaring Knight
encounter, from a save file the mod's author provided. This page explains that file, how DRBR loads it, and how your own
DELTARUNE saves stay safe.

Two things are kept apart:

- **The forced starting profile.** This is the story state DRBR starts from: the provided save, which never changes.
- **Your persistent player settings.** These are your DRBR settings, skin, SOUL colour, keybinds, chat and accessibility
  options. They live in the mod's own settings files and nothing in the save system resets them.

## 1. The provided save

| | |
|---|---|
| File in this repository | `save-profile/starting-save/start_filech3` (exact bytes, CRLF lines) |
| Where it came from | the author's own Chapter 3 save, slot 1: `%LOCALAPPDATA%\DELTARUNE\filech3_0`. The Knight Hub tester packs shipped the same file as `Save file\filech3_2`. |
| Size | 12,385 bytes |
| SHA-256 | `fa956269ee3ee98e7df04356bb575e3afd5455a538bb5568b2ac931fdb0aa082` |
| SHA-1 (what the game checks) | `e1b7086a53f5ac9ec46ecd23c1c465ae4f6a321b` |
| MD5 | `3f049272986e464881f3bfd26f9819cd` |
| Save template version | 1 |

`scripts/validate-save.py` checks the file and prints what it contains:

| Field | Value |
|---|---|
| Name (`global.truename`, `othername[0]`) | `ENDER`, the vessel's name. **This is public in every DRBR release.** |
| Party (`global.char`) | 1, 2, 3: Kris, Susie, Ralsei |
| Gold / LV / dark world | 8896 / 1 / yes |
| HP (Kris, Susie, Ralsei, Noelle) | 160/160, 190/190, 140/140, 120/120 |
| TP | 180.993 of 250 |
| Story point (`global.plot`) | **320** |
| Room (`global.currentroom`) | **30108** = `room_dw_snow_zone` (Chapter 3's room id table, `scr_get_room_by_id`) |
| Play time | 1,181,310 frames (about 10.9 hours at 30 fps) |
| Story flags set | 452 of 2500 |

The file holds no other personal data. It records only the game state above, with no paths, account names or dates.

### Its format

A DELTARUNE Chapter 3 PC save is text, written by `scr_saveprocess` and read by `scr_load`:

- It has 3055 lines, each ending in CR LF, except the last.
- Strings are written as they are. Numbers are written in C's `%g` format followed by a space, for example `8896 `,
  `180.993 ` or `1.18131e+06 `.
- The fields come in this order:
  1. the name
  2. 6 other names
  3. 3 party slots
  4. gold, xp, lv, inv, invc, darkzone
  5. for each of 5 characters: 10 stats, 4×10 item stats and 12 spells
  6. bolt speed, graze amount, graze size
  7. 13 items + 13 key items
  8. 48 weapons + 48 armours
  9. 72 pocket items
  10. tension, max tension
  11. 11 light world values
  12. 8 light items + 8 phone numbers
  13. **2500 flags**
  14. **story point, room id, play time**

DRBR accepts a save only when it has exactly 3055 lines and its last three values are numbers with a Chapter 3 room id
(30000 to 39999). Any other file gets a clear error (see section 7).

## 2. The starting room, as the game has it

These values were read from Chapter 3's own data (`room_dw_snow_zone`, room index 109) and from the decompiled code:

| | |
|---|---|
| Room size / view | 2960 × 480, a 640 × 480 view |
| Player | `obj_mainchara` is placed at (120, 240) at scale 2. A load puts the player where the room places them (`global.entrance` is 0 after `scr_load`). The emulated start reports x 120, y 240. |
| Save point | `obj_savepoint` at (200, 200) |
| The Roaring Knight scene | `obj_ch3_PTB02` is active at story points 310 to 329 (`con = 0` at 320). Walking right starts the encounter. Winning sets story point 340. |
| Other scene objects | `obj_ch3_PTB01` (310 to 319: inactive at 320), `obj_ch3_GSB05` (160 to 169: inactive), `obj_ch3_BTB04` |
| Collision | `obj_solidblocksized` / `obj_solidblock_diagonal_32` on the `COLLISION_DOOR` layer, and the left exit `obj_doorAny` at (18, 217) |
| Background | `obj_dw_snow_zone_parallax` (layer `BG_Parallax`) |
| The hub sign (the mod) | `obj_ch3_PTB02`'s Create adds an `obj_npc_sign` (`extflag "kaizo settings"`) at (352, 200) and the hub controller, for story points 310 to 329. The sign opens the Knight Hub menu, and ONLINE is in that menu. |

Because the save is loaded the same way the file menu's **CONTINUE** loads it, the result is the same as a normal
continue:

- `scr_load` runs `scr_gamestart`, the game's full initialisation.
- It reads every value, including all 2500 flags.
- It goes to `room_dw_snow_zone`.

No story flag is changed, and no cutscene that already happened plays again.

**Offline vs online.** These are unchanged from the Knight Hub.

- Offline, the original Roaring Knight encounter works as in the game.
- Online, the mod blocks the encounter trigger (`mod/scripts/br_patch.py`, hook 7), and players use the hub sign's
  ONLINE menu instead.

## 3. How DRBR selects it

**DRBR mode.** The DRBR install's own copy of the game, `%LOCALAPPDATA%\DRBR\game\chapter3_windows`, contains
`drbr_data\drbr_profile.cfg`. The DRBR build of `data.win` turns DRBR mode on only when it finds that file next to
itself. The same `data.win` patched into Steam's folder by the older Knight Hub installer has no such file, and there it
behaves exactly as before.

The game code is in `mod/gml/drbr_save54.gml`, and its hooks are in `mod/scripts/gen_hub.py`.

1. **Start.** `obj_initializer2` would normally go to the intro and the file menu. Instead it calls `kdr_boot()`:
   1. It checks `drbr_data/start_filech3` (read-only, next to `data.win`). The size must be 12,385 bytes and the SHA-1
      must be one in `kdr_template_list()`.
   2. It copies the file byte for byte (`buffer_load` / `buffer_save`) to `drbr_profile/filech3_0` in the save folder.
      In continue mode it keeps an existing valid DRBR save instead.
   3. It does what the file menu's CONTINUE does: slot 0, `snd_free_all`, the fade, the DRBR slot's controls, then
      `scr_load()`.
2. **Report.** `drbr_profile/last_start.ini` records how the start went:
   - `result=loading`, then `result=ok` once the first room is reached (`kdr_frame`)
   - `room=room_dw_snow_zone`, `room_id=30108`, `plot=320`
   - the player's x and y, and the party

   DRBR Launcher waits for this file, so PLAY reports **"DRBR started in room_dw_snow_zone - the room before the
   Roaring Knight"**.
3. **A hint.** For the first 8 seconds, a line says where the hub sign is and that ONLINE is in its menu.

DRBR never connects to a lobby by itself.

### The profile config (`chapter3_windows\drbr_data\drbr_profile.cfg`)

DRBR Launcher writes this file and the game reads it as plain text, line by line.

```
schema_version=1
profile=drbr_default
starting_location=room_dw_snow_zone
starting_room_id=30108
starting_plot=320
save_template_version=1
save_template_sha256=fa956269...
start_mode=template
migration_version=1
```

`start_mode` is set in DRBR Launcher > Settings:

- **`template` (default)** starts every launch from the provided save, so every launch is in front of the Roaring
  Knight.
- **`continue`** starts from your last DRBR save if it is a valid Chapter 3 save. Otherwise it uses the provided save.

## 4. Profile isolation: where every file is

| What | Where | Written by |
|---|---|---|
| The provided save (immutable template) | `%LOCALAPPDATA%\DRBR\game\chapter3_windows\drbr_data\start_filech3` | the installer and launcher (checked before every PLAY) |
| The launcher's own copy of it (for repairs) | `%LOCALAPPDATA%\DRBR\save-profile\start_filech3` | the installer |
| Profile record (versions) | `%LOCALAPPDATA%\DRBR\save-profile\profile.json` | the launcher |
| **DRBR's live story saves** | `%LOCALAPPDATA%\DELTARUNE\drbr_profile\` (`filech3_0`, `filech3_9`, `dr.ini`, `keyconfig_0.ini`) | the game, in DRBR mode only |
| DRBR start report / pending room | `%LOCALAPPDATA%\DELTARUNE\drbr_profile\last_start.ini`, `pending_join.ini` | the game |
| **Your persistent DRBR settings** | `%LOCALAPPDATA%\DELTARUNE\knight_hub.ini` (+ `.bak`), `knightfights_online.ini`, `knighthub_songs.ini` | the mod (unchanged since the Knight Hub) |
| The game's window and language settings | `%LOCALAPPDATA%\DELTARUNE\true_config.ini` | the game (shared on purpose) |
| **Your own DELTARUNE saves** | `%LOCALAPPDATA%\DELTARUNE\filechN_M`, `dr.ini`, `keyconfig_N.ini`, `config_N.ini` | vanilla DELTARUNE only: **never touched by DRBR** |

The DRBR live saves have to be inside `%LOCALAPPDATA%\DELTARUNE`. GameMaker only lets a game write inside its own save
folder, and DELTARUNE's save folder is named after the game.

In DRBR mode, every story file name goes through `kdr_path()`. This covers Chapter 3's `ossafe_ini_open`,
`ossafe_file_text_open_read/write`, `ossafe_file_exists` and `ossafe_file_delete`, plus the CONFIG menu's own direct
`ini_open("keyconfig_N.ini")`. Each name is matched against `filech*`, `dr.ini`, `keyconfig_<n>.ini` and
`config_<n>.ini` and then lives in `drbr_profile\`.

Nothing else is redirected: not the mod's settings, not `true_config.ini`, and not another mod's `keyconfig_mod.ini`.
The game's own SAVE, the Chapter 3 completion save, `dr.ini`'s slot list, the ura-boss result and the controls therefore
all stay inside `drbr_profile\`.

## 5. Save migration and future releases

- Every release lists its starting save in `payload.json` / `update-manifest.json` (`save_profile`). That entry gives
  the schema, template version, migration version, starting room id and story point, and the template's size, SHA-256
  and SHA-1. These come from `drbr.json`.
- At every PLAY, the launcher does two things:
  1. `SaveProfile.EnsureBundle` checks the bundled template and the cfg, and repairs them from its own copy.
  2. `SaveProfile.Migrate` compares `save-profile\profile.json` with the release.
     - A newer profile schema than the launcher knows is refused, with a message to update.
     - Migration 1 is the first profile and has nothing to do.
     - A later release adds its steps there. Steps may only touch `drbr_profile\` and DRBR's own folder, never your
       DELTARUNE saves or the mod's settings files.
- **Changing the starting save in a future release:**
  1. Put the new file in `save-profile/starting-save/`.
  2. Raise `save_template_version`.
  3. Add its SHA-1 to `kdr_template_list()` in `drbr_save54.gml`. Keep the old SHA-1 there while players may still
     have the old template.
  4. Run `scripts/validate-save.py`.
- Game updates by Steam do not break DRBR. DRBR runs its own copy of the game, made when it was installed, and keeps a
  clean copy of the vanilla `data.win` (`%LOCALAPPDATA%\DRBR\base\data.win.vanilla`) to rebuild from.

## 6. Recovery

- **Restore Starting Save** (DRBR Launcher) moves DRBR's story saves (`drbr_profile\filech*`, `dr.ini`) to
  `%LOCALAPPDATA%\DRBR\backups\profile-<date>\`. They are moved, not deleted. The next start is the provided save in
  either start mode. The DRBR controls, the mod's settings and your own saves are kept.
- **Repair** rebuilds the install from DRBR's kept package and your game:
  - `data.win` from the vanilla copy and the patch
  - the bundled template from the launcher's copy, or from the package
  - every mod file
- **If the bundled template is missing or damaged**, PLAY replaces it before starting. If the game itself finds the
  template unusable, for example because the files were changed while the launcher was closed, it shows "DRBR could not
  start ... open DRBR Launcher and choose REPAIR" and closes. It loads nothing and writes nothing.

## 7. How your DELTARUNE saves are protected

1. The installer and launcher never write to `%LOCALAPPDATA%\DELTARUNE` except two things:
   - Restore Starting Save, which moves files out of `drbr_profile\`
   - uninstall, which removes `drbr_profile\` only when you ask
2. The game in DRBR mode reads and writes story files only inside `drbr_profile\` (section 4).
3. Steam's DELTARUNE folder is only read: the vanilla `data.win`, or the older Knight Hub's verified backup of it, plus
   `DELTARUNE.exe` and Chapter 3's sounds, language, videos and music.
4. Before each PLAY, the launcher hashes your own save files (`filechN_M`, `dr.ini`, `keyconfig_N.ini`,
   `config_N.ini`) and checks them again after the game closes. It says "Your own DELTARUNE saves were not touched", or
   names any file that changed. Vanilla DELTARUNE or Steam Cloud can change them.
5. Tested:
   - In the emulator with the real game code: the player's files are compared byte for byte after every step
     (`mod/tests/t_drbr_save54.py`).
   - The core tests (`src/Drbr.Tests`).
   - The Windows programs under Wine (`tests/installation/wine_e2e.sh`).

Errors you can see:

| Situation | What happens |
|---|---|
| The template is missing, damaged or not a known starting save (one changed byte is enough) | PLAY repairs it from DRBR's copy. If the game finds it bad anyway: a message, and the game closes. |
| The live DRBR save is invalid (continue mode) | The provided save is used instead. Nothing crashes. |
| Not a Chapter 3 save (wrong line count, a non-Chapter 3 room) | "it is not a DELTARUNE Chapter 3 save (N lines, 3055 expected)" or "its room ... is not a Chapter 3 room" |
| A profile made by a newer DRBR | "This DRBR profile was made by a newer DRBR version ... Update DRBR." |

**Steam Cloud.** DELTARUNE's save folder is synced by Steam Auto-Cloud (it contains `steam_autocloud.vdf`), so
`drbr_profile\` may be synced too. This is harmless.
