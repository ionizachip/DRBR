# Changelog

## 1.0.1

### In the game

- **Menus in DELTARUNE's own text size.** The menus' small print is gone, and overlapping text is fixed. A text too long
  for its place scrolls by itself instead of being cut off. A box with a lot in it (a results box with every option,
  FIGHT STATS) packs its rows a little closer instead of running into its buttons.
- **ONLINE is the menu's first page**, with its own icon.
- **Boss speech balloons are off by default** (they covered the battle). Turn them on in VIEW > BOSS LINES: then they are
  DELTARUNE's own rounded balloons, beside the boss and away from the battle box. The bosses' lines are exactly their
  chapters' lines.
- **Your own music plays over the bosses.** MUSIC > DEFAULT gives each boss its own music. A song you pick keeps playing
  through every boss.
- **Pink's stage is Chapter 5's**: black, her spotlight and the audience between her attacks.
- **Bosses together**: one boss after another changes the music once, the stage announcements fit the boss on stage,
  and the Knight's songs and lines are not used over a boss.
- Smaller boss icons in the skill slots. The send telegraph (the knight's outline beside your box) is in the sender's
  colour.
- **Less slowdown**: the bots plan their moves faster, and the menus no longer measure and wrap their text every frame.
- **The bots play the bosses' SOUL modes** (they used to sit still or wander there, with dice for every hit):
  - Gerson's green SOUL: each bot turns its own shield toward the spears (and away from a red hammer); whether it blocks
    depends on where it is facing.
  - Pink's lanes, grid and "+": bots change lane / spot as a player does, and plan for it.
  - Pink's 3D tunnel and maze: bots go from ring to ring and walk the maze's paths.
  - Flowery's board: bots move up and down out of the way and dash when they get past a lunge.
  - Harder bots do all of this better.
- **Watching a bot (or a player) shows what they do in those modes**: their green shield's direction, their dashes on
  Flowery's board, their ring in Pink's tunnel and their spot in her maze.
- The credits name ionizachip.

### Installing and updating

- **A release is one file: `DRBR.zip`.** Open it and run `DRBR-Setup.exe`.
- The launcher checks for updates by reading only the end of `DRBR.zip` (about 64 KB), then downloads just the bytes of
  the files that changed. Everything is still signed and checked.
- **An update that brings a new launcher works.** Windows does not let a running program be replaced, so the new
  launcher waits until the launcher closes; DRBR Updater then puts it in and opens it again. (Before, such an update
  stopped with "access denied" and was rolled back.) A new launcher left waiting goes in at the next start.
- A server that ignores download ranges, or a redirect that drops them, no longer makes the update check download the
  whole release.

## 1.0.0

(Re-issued as one `DRBR.zip`: the same game; its launcher reads releases that are one file.)

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
