# Multiplayer tests

| What | Where | How to run |
|---|---|---|
| Rooms, joining, the build number rooms compare, refusals | `mod/tests/t_online.py` | from `mod/tests` in the mod build environment |
| Steam rooms: the GML, the real `kf_steam` code, a pretend Steam | `mod/tests/t_steam_gml.py`, `mod/online-steam/t_steam_dll.py` | same |
| A room with a newer DRBR: the note, the update, the rejoin offer (JOIN / NOT NOW) | `mod/tests/t_drbr_save54.py` section 13 (game), `src/Drbr.Tests` group `join` (launcher) | `scripts/test-drbr.sh mod`, `scripts/test-core.sh ... join` |
| The bosses over the simulated network (no desync) | `mod/tests/t_*53*.py` | from `mod/tests` |

The version a room needs is the game's `kfo_version()` (`mod/gml/online_net.gml`) and `protocol` in `drbr.json`. A real
Steam room between two PCs is part of the real-PC check in `docs/RELEASING.md`.
