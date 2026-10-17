# The DRBR starting save

`start_filech3` is the save that every DRBR start loads. It is **the save file provided for DRBR, byte for byte**: it
was not generated, edited or rebuilt.

| | |
|---|---|
| Format | DELTARUNE Chapter 3, PC (3055 lines, CRLF) |
| Size | 12385 bytes |
| SHA-256 | `fa956269ee3ee98e7df04356bb575e3afd5455a538bb5568b2ac931fdb0aa082` |
| SHA-1 | `e1b7086a53f5ac9ec46ecd23c1c465ae4f6a321b` (the game's own check) |
| Where | room 30108, `room_dw_snow_zone`: the cold place, right before the Roaring Knight |
| Story point | 320 (the hub sign is there from 310 to 329) |
| Party | Kris, Susie, Ralsei, at full HP |
| File name | ENDER, as in the provided file |

To print this from the file itself, run `scripts/validate-save.py`.

## How it is used

1. `DRBR-Setup.exe` carries it in its package, installs it next to DRBR's `data.win`
   (`game\chapter3_windows\drbr_data\start_filech3`), and keeps a second copy in `save-profile\` for repairs.
2. Before every PLAY, DRBR Launcher checks both copies by SHA-256 and replaces a missing or changed one.
3. When the game starts, the DRBR build checks the file again by size and SHA-1. It copies the file to
   `%LOCALAPPDATA%\DELTARUNE\drbr_profile\filech3_0` and loads it, as the file menu's CONTINUE does.

Your own DELTARUNE saves (`%LOCALAPPDATA%\DELTARUNE\filech3_*`) are never read or written by any of this.

## Changing it

Never edit this file in place: the game and the launcher both refuse a copy whose checksum they do not know. To ship
another starting save:

1. Replace the file.
2. Raise `save_template_version` in `drbr.json` and update its sizes and checksums.
3. Add its SHA-1 and size to `kdr_template_list()` in `mod/gml/drbr_save54.gml`.
4. Rebuild the game, then run `scripts/validate-save.py`.

CI checks the exact bytes of this file on every push.
