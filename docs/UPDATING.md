# Updating DRBR

## Automatic update detection

When DRBR Launcher opens, and when you click **Check for Updates**, it reads the release information
(`update-manifest.json` and its signature) from the latest DRBR release on GitHub. You can turn off the check at
opening in Settings.

A DRBR release is **one file, `DRBR.zip`**. It holds `DRBR-Setup.exe` (with the whole DRBR package inside it), a
`README.txt`, and `update/update-manifest.json` with its signature as its last entries. The launcher does not download
`DRBR.zip` to check: it reads only its end (about 64 KB: the zip's directory, the manifest and the signature) with HTTP
range requests.

- The release information is **accepted only when its signature is DRBR's**. It is signed with the DRBR release key, and
  the launcher checks it with the public key built into it. A release that is not signed by DRBR is refused, and
  nothing is downloaded or changed.
- The launcher compares:
  - the DRBR version
  - its own version, plus the oldest launcher the release can be installed by
  - the multiplayer build (protocol)
  - the save template and migration versions

When a newer version is there:

```
DRBR UPDATE AVAILABLE
Installed: 1.0.0
Available: 1.1.0
[ UPDATE NOW ]   [ PLAY CURRENT VERSION ]
```

If the multiplayer build changed, the window adds that online play needs the update. You can always keep playing the
installed version offline. Without an internet connection, the launcher says it could not reach the update server and
DRBR stays playable.

## Download and installation

**UPDATE NOW** does the following:

1. It checks that DRBR's game is not running and that there is enough disk space.
2. It downloads only what changed. Each file is listed in the signed release information with its size and SHA-256. A
   file DRBR already has with that checksum is reused, not downloaded. The others are read **from inside `DRBR.zip`**:
   the files lie uncompressed in the package appended to `DRBR-Setup.exe`, which lies uncompressed in `DRBR.zip`, so
   the launcher asks the server for just their bytes. Downloads go to `%LOCALAPPDATA%\DRBR\staging\download-<version>\`.
   - The files come from that version's own `DRBR.zip` (`releases/download/v<version>/DRBR.zip`), not from "latest",
     so a release published meanwhile cannot mix in.
   - A `DRBR.zip` that was compressed again by hand, or a server that does not answer range requests, still works: then
     `DRBR.zip` is downloaded whole and the files are taken out of it here.
3. It checks every file by SHA-256. A damaged download is deleted and downloaded once more. If it is damaged again, the
   update is refused and nothing changes.
4. It installs with the same transaction as a fresh install:
   1. the new copy is built in staging, and DRBR's `data.win` is rebuilt from the clean vanilla copy and the new patch
   2. the copies are switched with one rename
   3. everything is verified
   4. **it rolls back if anything fails**, and the previous DRBR stays as it was
5. It keeps your start mode, your DRBR saves and every DRBR setting. The provided starting save is checked again.

Updates use the **full game patch**: the binary difference from the vanilla Chapter 3 `data.win`, about 110 MB, and
only when the game build changed. This is the reliable choice for GameMaker's packed data files. The manifest schema
can also describe incremental patches (`patch_incremental`, from one DRBR build to the next), but this version of the
launcher does not use them yet.

## Interrupted downloads and failed updates

- A download that stops (connection lost, launcher closed) **resumes** from where it stopped the next time, using an
  HTTP Range request on the kept `.part` file. (GitHub hands out short-lived download addresses: an expired one is
  asked for again.)
- An update that fails or is interrupted while installing, whether it crashed, lost power or was closed, is undone the
  next time DRBR Launcher or DRBR-Setup starts. The previous DRBR is put back
  (`%LOCALAPPDATA%\DRBR\drbr-transaction.json` records the transaction).
- If something still looks wrong, use **Repair Installation**.

## Launcher updates

A running program cannot replace itself. When a release has a newer launcher:

1. Its file is downloaded and checked like any other file. Windows refuses to delete or overwrite the running
   launcher, so the new one waits in `%LOCALAPPDATA%\DRBR\staging\pending\`; the rest of the update goes in as usual.
2. The launcher starts **DRBR Updater** and closes.
3. The updater waits for the launcher to close, checks the new file's SHA-256, swaps the files (the old one is kept
   until the new one is checked), and starts the launcher again.

If anything fails, the old launcher is put back and keeps working. A new launcher still waiting (for example after
DRBR-Setup.exe ran while the launcher was open) goes in the next time the launcher starts. There is no background
service.

## Save migrations

Every release states its save profile versions. At PLAY, the launcher brings DRBR's profile record
(`%LOCALAPPDATA%\DRBR\save-profile\profile.json`) up to the release. Migrations only touch DRBR's own folder and the
DRBR saves (`drbr_profile`), never your DELTARUNE saves or your DRBR settings. A profile made by a newer DRBR is refused
with a message to update. See [SAVE_SYSTEM.md](SAVE_SYSTEM.md).

## Version compatibility

| Part | What must match |
|---|---|
| Online rooms | The same multiplayer build (`protocol`, the game's `kfo_version()`) and the same boss and attack list. A room with a different build is refused with a clear message. If the room is **newer**, DRBR notes it, DRBR Launcher offers the update, and the updated game offers that room again (JOIN / NOT NOW). |
| DELTARUNE | DRBR is built from DELTARUNE (Steam) Chapter 3 v0.0.105. A Steam update to DELTARUNE does not break an installed DRBR, because DRBR runs its own copy. Updates are built from DRBR's own clean copy. Only a **new** install needs the supported version in Steam. |
| The launcher | A release can require a minimum launcher version. The update brings the new launcher with it. |
