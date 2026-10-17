# Save-loading tests

| What | Where | How to run |
|---|---|---|
| The provided starting save: format, room 30108, story point 320, party, checksums | `scripts/validate-save.py` | `python3 scripts/validate-save.py` (also in CI) |
| The DRBR start in the real game code: the save copied and loaded, isolation of every story file, start report, template / continue modes, damaged saves, chapter switch, the rejoin note, the DRBR names | `mod/tests/t_drbr_save54.py` (GameMaker emulator) | `scripts/test-drbr.sh mod` (needs the mod build environment) |
| The launcher's side: the template and profile config before every PLAY, Restore Starting Save, the profile record and migrations, the vanilla-save check | `src/Drbr.Tests` groups `save`, `install`, `update` | `scripts/test-core.sh <payload> <vanilla data.win> <key> save install update` |
| The whole chain on Windows programs | `tests/installation/wine_e2e.sh` steps 1-3 | see `docs/DEVELOPMENT.md` |

None of these run the real game. The real-PC check is in `docs/RELEASING.md`.
