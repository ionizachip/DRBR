# Changelog

## 1.0.0

The first DRBR release: DRBR becomes its own installation with a launcher, instead of a patch in Steam's DELTARUNE folder.

### Installing and playing

- **DRBR-Setup.exe** finds DELTARUNE by itself, checks that it is a supported version, and installs DRBR in its own
  folder (`%LOCALAPPDATA%\DRBR`). Steam's DELTARUNE is never changed.
- **DRBR Launcher** provides Play, Check for Updates, Repair, Restore Starting Save, Settings, Release Notes, and Open
  Installation Folder.
- **Every start is right before the Roaring Knight.** DRBR uses the provided starting save, after updates, repairs and
  reinstalls too. DRBR's story saves are kept apart from your own DELTARUNE saves, which are never touched.
- **Settings > start mode**: start from the starting save every time (default), or continue from your last DRBR save.
- **Updates** are checked when the launcher opens. They are signed, only changed files are downloaded, interrupted
  downloads resume, and a failed update rolls back.
- **Multiplayer and updates**: a room with a newer DRBR is noted. The launcher offers the update, and the updated game
  offers that room again (JOIN / NOT NOW).
- **Uninstall** from Settings > Apps or from the launcher. Your DELTARUNE and your saves stay.

### In the game (build 51.10)

- The DRBR start: the starting save is loaded at once (no intro, no file menu). A note in the cold place shows where
  the hub sign is.
- Leaving Chapter 3 (the chapter select, a chapter switch) restarts DRBR at its start instead of opening a chapter DRBR
  does not include.
- The game names itself DRBR in the DRBR install: the build stamp, the credits, and the messages about rooms with
  another build or a missing Steam file.
- Everything in DRBR (Knight Hub build 51, update 9) is included: the five bosses besides the knights (Jevil, Spamton
  NEO, Gerson, Flowery and Pink), their SOULs and sends, the skins, and the polished menus.
