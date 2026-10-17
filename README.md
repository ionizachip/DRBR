# DRBR - DELTARUNE BATTLE ROYALE

An online battle royale for **DELTARUNE Chapter 3**. Up to 8 players fight the same boss at the same moment, each in
their own game. You dodge its attacks, send attacks of your own at each other, and the last SOUL standing wins.

DRBR is an unofficial fan mod by ImperfectNORE, built on the **Knight Hub** (every knight fight in one game). It needs
your own copy of DELTARUNE from Steam.

## Play

1. Have **DELTARUNE (Steam)** with Chapter 3 installed.
2. Download **`DRBR-Setup.exe`** from [Releases](../../releases/latest).
3. Run it, then click **INSTALL DRBR**, then **PLAY DRBR**.
4. The game opens in the cold place, right before the Roaring Knight. Walk right to the sign and press **Z**:
   **ONLINE** is in its menu.

You do not need a save file, UndertaleModTool, or to play through any chapter. Windows may say "Windows protected your
PC" because DRBR is not code-signed: click **More info**, then **Run anyway**.

## What is in it

**Online (DRBR)**

- Host a room, or join one from the browse list, by its code, or from a friend's Steam invite. DRBR never joins a room by
  itself.
- Rooms take up to 8 players, plus bots if the host adds them. There is also **HOW TO PLAY** (a lesson against a dummy)
  and **PRACTICE** against any boss alone.
- The host's room settings choose who fights and in what order, the damage, whose attacks players can send, and which
  targeting modes are allowed. A preset sets all of it at once.
- Skins are cosmetic only.

**Bosses**

| Boss | From | SOUL |
|---|---|---|
| The knights: Normal, Kaizo, Supercharged, Violet, Thorn, the Knightmare | Chapter 3 and the Knight Hub's knight mods | red |
| Jevil | Chapter 1, secret boss | red |
| Spamton NEO | Chapter 2, secret boss | yellow (shoot) |
| Gerson, the Hammer of Justice | Chapter 4, secret boss | green (shield) |
| Flowery | Chapter 5 | orange (dash) |
| Pink | Chapter 5, secret boss | purple (lanes) |

Each boss is the game's own fight, made from your own DELTARUNE files when the mod is built. The details are in
[mod/notes/DRBR_BOSSES.txt](mod/notes/DRBR_BOSSES.txt).

**Offline**

The sign's menu also has the Knight Hub's offline fights, the Cyan Knight among them.

## Your saves and your game are safe

- DRBR installs its own copy of the game in `%LOCALAPPDATA%\DRBR`. Your DELTARUNE in Steam is only read, never changed.
- DRBR's story saves live in their own folder (`%LOCALAPPDATA%\DELTARUNE\drbr_profile`). Your own DELTARUNE saves are
  never read or written, and DRBR Launcher checks them after every game.
- Every start loads the provided starting save, in front of the Roaring Knight. That stays true after updates, repairs
  and reinstalls. Your online settings (name, skin, SOUL colour, keybinds) are kept across all of them.

Details: [docs/SAVE_SYSTEM.md](docs/SAVE_SYSTEM.md).

## Updates

DRBR Launcher checks for a new release when it opens.

- It accepts an update only if the update is signed with DRBR's release key.
- It downloads only the files that changed, checks each one, and installs the update as a single step that rolls back if
  anything fails.
- If you tried to join a room that has a newer DRBR, the launcher offers the update. The updated game then offers that
  room again.

Details: [docs/UPDATING.md](docs/UPDATING.md).

## Requirements

- Windows 10 or 11 (DRBR uses .NET Framework 4.8, which Windows already has)
- DELTARUNE (Steam), Chapter 3 v0.0.105
- About 1 GB of free disk space
- Steam running, for online play

## Documentation

| Document | What it covers |
|---|---|
| [Installation](docs/INSTALLATION.md) | install, start mode, repair, uninstall |
| [Save system](docs/SAVE_SYSTEM.md) | how the starting save works and how your saves stay safe |
| [Updating](docs/UPDATING.md) | update checks, rollback, version compatibility |
| [Troubleshooting](docs/TROUBLESHOOTING.md) | every known problem and its fix |
| [Architecture](docs/ARCHITECTURE.md) | the installer, launcher and updater, and their files |
| [Development](docs/DEVELOPMENT.md) | building and testing |
| [Releasing](docs/RELEASING.md) | publishing a version |
| [Changelog](CHANGELOG.md) | what changed in each version |

## Credits

- **DELTARUNE** is by Toby Fox. DRBR is not affiliated with or endorsed by Toby Fox or the DELTARUNE team.
- **DRBR and the Knight Hub** are by ImperfectNORE.
- **The knight fights** are by their mods' makers, credited on each knight's page in the game.
- **The fight songs** are by their artists: in the game, CONFIG > CREDITS > MUSIC. The songs belong to their artists.
