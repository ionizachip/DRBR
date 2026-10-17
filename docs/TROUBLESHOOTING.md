# DRBR troubleshooting

If you need to look closer, DRBR keeps a log in `%LOCALAPPDATA%\DRBR\logs\` (newest file at the bottom of the folder).
To open the folder, use DRBR Launcher > **Open Installation Folder**, then go into `logs`.

## DELTARUNE not detected

The Setup says **DELTARUNE NOT FOUND**.

- Click **Browse...** and pick the folder that contains `DELTARUNE.exe`. With Steam this is usually
  `C:\Program Files (x86)\Steam\steamapps\common\DELTARUNE`, or `<drive>:\SteamLibrary\steamapps\common\DELTARUNE` for
  another Steam library.
- Chapter 3 must be installed: the folder needs `chapter3_windows\data.win`. Start Chapter 3 once from Steam if it is
  missing.

## Unsupported game version

The Setup says **"This DELTARUNE's Chapter 3 data.win is not a version DRBR supports"**.

- Steam may have updated DELTARUNE to a version this DRBR release does not know yet. Wait for a DRBR update.
- Another mod may have changed `chapter3_windows\data.win`. In Steam, right-click DELTARUNE, then choose
  **Properties > Installed Files > Verify integrity of game files**, and run the Setup again.
- An installed DRBR keeps working after a DELTARUNE update, because it runs its own copy of the game. Only a new install
  needs the supported version.

## Missing starting save

You see "The DRBR starting save (drbr_data\start_filech3) is missing" or "is damaged".

Normally you never see this: PLAY puts the starting save back from DRBR's own copy before starting. If the game shows it
anyway, open DRBR Launcher and choose **Repair Installation**. If Repair says DRBR's package is missing, run
`DRBR-Setup.exe` again. Your settings and saves are kept.

## The game starts in the wrong room

- In **Settings**, the start mode should be **Start from the DRBR starting save every time**. In *continue* mode DRBR
  loads your last DRBR save, which can be past the Roaring Knight.
- Use **Restore Starting Save**: the next start is the provided save again.
- DRBR Launcher's status line after PLAY says which room the game reached. "not in the starting room" means the game
  reported another room. Send the log and `%LOCALAPPDATA%\DELTARUNE\drbr_profile\last_start.ini`.

## Incorrect save flags (missing hub sign, a cutscene plays again)

The hub sign exists only at the Roaring Knight's story points (310 to 329). The provided save is at 320. If the sign is
missing, the loaded save is a later one: use **Restore Starting Save**. The provided save itself is checked by its SHA-1
on every start, so DRBR never loads a changed copy of it.

## Save profile corrupted

If DRBR starts badly or not at all after a crash, use **Restore Starting Save**. Your DRBR saves are moved to
`%LOCALAPPDATA%\DRBR\backups\` and never deleted. If that does not help, use **Repair Installation**. In continue mode,
an invalid DRBR save is replaced by the starting save automatically.

## Vanilla save conflict

DRBR's saves live in `%LOCALAPPDATA%\DELTARUNE\drbr_profile\`, and your own DELTARUNE saves are never touched. After
each game, DRBR Launcher checks them and says "Your own DELTARUNE saves were not touched".

If it ever names a file that changed, the change came from vanilla DELTARUNE, Steam Cloud or another program, not from
DRBR's game, which cannot write there. Your Chapter 3 slots in vanilla DELTARUNE are the same as before.

## Installer failure

The Setup shows an error, and **nothing was changed**: a failed install is rolled back completely.

| Message | Fix |
|---|---|
| **Not enough free disk space** | DRBR needs about 1 GB. |
| **DRBR is running** | Close the game first. |
| **The DRBR package is damaged** | Download `DRBR-Setup.exe` again and compare it with `SHA256SUMS.txt` in the release. |
| **Applying the DRBR game patch failed** | Your Chapter 3 `data.win` is probably not the supported one (see above). |
| Antivirus warnings | DRBR's programs are not code-signed. Allow them, or install from a folder your antivirus trusts. |

## Update failure

| Message | What it means |
|---|---|
| **Could not reach the DRBR update server** | No internet, or GitHub is down. Play the installed version; try again later. |
| **not signed by DRBR's release key** | The update was refused on purpose. Something other than DRBR's release was served. Nothing was downloaded or changed. |
| **The download ... was damaged twice and was refused** | Try again later. Nothing was changed. |
| **The download ... stopped** | Run the update again. It continues where it stopped. |

An update that was interrupted while installing is undone the next time DRBR Launcher starts.

## Steam lobby mismatch

**"That room has a newer DRBR"**: close the game, open DRBR Launcher and update. The launcher offers the update by itself
because the game noted the room. After the update, open the sign's menu: **"DRBR IS UPDATED - Join the room you tried to
join before the update?"**.

**"That room's players have an older DRBR"**: the room's players need to update.

Steam must be running for Steam rooms.

## Missing assets or shaders

- If the music is missing in a fight, run **Repair Installation**. Every song is checked against its checksum.
- DRBR does not use shaders of its own. Graphics injectors from the Steam folder (`dxgi.dll`, ReShade) are not copied
  into DRBR, which is on purpose.

## The game crashes at startup

1. Run **Repair Installation**.
2. Make sure your own DELTARUNE (Steam) starts Chapter 3 normally.
3. Send the newest log from `%LOCALAPPDATA%\DRBR\logs\`, `%LOCALAPPDATA%\DELTARUNE\drbr_profile\last_start.ini`, and
   `%LOCALAPPDATA%\DELTARUNE\knightfights_debug.log`.
