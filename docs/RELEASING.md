# Releasing DRBR

This page walks the maintainer through publishing a version, from the finished game build to a GitHub release that
every installed DRBR Launcher picks up.

## Once: set up

1. **The GitHub repository.** Create it on GitHub, for example `<you>/DRBR`. It must be **public** so the launcher can
   download releases without a token. Then point this repository at it:
   ```
   git remote add origin https://github.com/<you>/DRBR.git
   git push -u origin main
   ```
2. **drbr.json.** Set `"github": {"owner": "<you>", "repo": "DRBR"}`. The launcher's update address is built from it
   (`packaging/gen_buildinfo.py`). Until it is set, the launcher says updates are not set up.
3. **The signing key.**
   - The private key (`drbr-signing-key.pem`, RSA-3072) signs every release. Its public half is in `drbr.json` and is
     built into every launcher. **Keep the private key private**: not in the repository (`.gitignore` excludes `*.pem`,
     and CI fails on a committed key), not in a release, not in a chat.
   - Keep a backup of it. If it is lost, installed launchers cannot accept new releases until players install
     `DRBR-Setup.exe` again.
   - Making a new key: `openssl genpkey -algorithm RSA -pkeyopt rsa_keygen_bits:3072 -out drbr-signing-key.pem`. Then put
     the base64 modulus in `drbr.json` (see `packaging/gen_buildinfo.py`).
4. **The GitHub CLI.** Run `gh auth login` on the release machine. DRBR itself never stores a token.
5. **GitHub, approval to publish.** Go to Settings > Environments, create `release`, and add yourself under
   **Required reviewers**. The release workflow then publishes only after you approve it.

## What a release contains (decide before the first public release)

| File | What it is |
|---|---|
| `drbr-chapter3.xdelta` | The game patch: the binary difference from the player's own vanilla Chapter 3 `data.win`. It applies only to that file. It carries DRBR's code and art. That includes the knight fights from the Knight Hub's knight mods, and the five bosses' code and art, which are taken from DELTARUNE Chapters 1, 2, 4 and 5 when the mod is built. |
| `drbr-music-0..4.zip`, `drbr-kfsongs.zip` | The mod's fight songs. These are **third-party fan works**. `KF_MUSIC_CREDITS.txt` notes that their pages say "all rights reserved" and give no usage terms. |
| `kf_steam.dll`, `steam_api64.dll`, `steam_appid.txt` | The multiplayer files: DRBR's own DLL, Valve's Steam API redistributable, and app ID 480. |
| `xdelta3.exe` | The open-source patch tool. |
| `start_filech3` | The provided starting save. |
| The programs and docs | DRBR's programs and documentation. |

A release does **not** contain any DELTARUNE file (`data.win`, `DELTARUNE.exe`, music). Those are copied from the
player's own install when DRBR installs. It contains no save other than the provided one, and no keys.

Before a **public** release, make sure:

- **The fight songs may be shared publicly**, with their artists' permission. If not, build without them:
  `DRBR_NO_MUSIC=1 scripts/package-drbr.sh <version>`. Those fights then play the game's own music.
- **The knight mods' makers agree** to their fights being in a public release, as they were in the Knight Hub tester
  pack.
- **You are fine with the patch carrying other chapters' assets.** It includes DELTARUNE content from other chapters
  (needed for the bosses), in patch form, which only applies to an owned Chapter 3.

## Every release

All commands run from the repository root, on the machine that has DELTARUNE (the patch needs its `data.win` files).
Set the key for the session:

```
export DRBR_SIGNING_KEY_FILE=/path/to/drbr-signing-key.pem
```

### 1. Build the game mod

```
scripts/build-drbr.sh
```

This generates the merged GML, lints it (unresolved names 0, raw asset numbers 0), and builds `data.win` with the
UndertaleModTool CLI. It then runs the static checks (every function and variable is in the runner, and the round trip
of every code entry), and makes the in-place package: the xdelta patch, checked by applying it to the vanilla
`data.win`.

**This step is local on purpose.** It needs DELTARUNE's Chapter 3 `data.win`, plus Chapters 1, 2, 4 and 5 for the
bosses' art. Those files must never go to GitHub or a hosted runner. The release contains only the binary patch.

### 2. Test

```
scripts/test-drbr.sh                # save mod core wine
```

| Suite | What it runs |
|---|---|
| `save` | the provided starting save is valid (`scripts/validate-save.py`) |
| `mod` | the DRBR save profile in the game code (GameMaker emulator, the real merged GML) |
| `core` | the installer, launcher and updater logic with the real vanilla `data.win`, the real patch, your key, and a local release server (update, resume, refusals) |
| `wine` | the real `DRBR-Setup.exe`, `DRBR Launcher.exe` and `DRBR Updater.exe` under Wine (emulated Windows), end to end |

A suite whose inputs are missing reports BLOCKED, never PASS. Before a release, also try a real Windows PC (see
"Real-PC check" below), because nothing here runs the real game on real Windows.

The mod's own regression suites (the bosses, the online UI and so on) are in `mod/tests/`. Their results go into
`mod/notes/TESTING_REPORT.txt`.

### 3. Write the release notes

Add a section to `CHANGELOG.md`. It becomes the release notes and the launcher's **Release Notes**. If the multiplayer
build changed (`kfo_version()` in `mod/gml/online_net.gml`), also set `"protocol"` in `drbr.json`. If the launcher
changed, raise `"launcher_version"`.

### 4. Package and sign

```
scripts/package-drbr.sh 1.1.0
```

This makes `dist/1.1.0/`:

| Path | What it is |
|---|---|
| `payload/` | everything a DRBR install is made of, plus `payload.json` with every size and SHA-256 |
| `DRBR-Setup.exe` | the installer with the payload appended |
| `release/DRBR.zip` | **the release: its one file** |
| `release/RELEASE_NOTES.md` | the text for the release's description |

`DRBR.zip` is a zip **without compression** ("stored"), in this order:

1. `DRBR-Setup.exe` (the whole package appended to it)
2. `README.txt` (how to install)
3. `update/update-manifest.json` and `update/update-manifest.json.sig` (signed with your key) - **last**, so the
   launcher finds them by reading only the end of the file

Players download `DRBR.zip`, open it and run `DRBR-Setup.exe`. Launchers read the manifest from its end and then only
the bytes of the files that changed (see [UPDATING.md](UPDATING.md)).

At the end the script runs `release_tools.py check release/DRBR.zip`: it reads the zip the way the launcher does
(its end, then each file at its place), checks the signature against `drbr.json`'s public key and every file's SHA-256,
and that nothing in it is compressed.

### 5. Publish

Upload **`DRBR.zip` exactly as it was made**: do not unpack it and zip it again. (A re-zipped `DRBR.zip` still works,
but every launcher then has to download all of it for an update.)

By hand on GitHub: Releases > Draft a new release > tag `v1.1.0` (exactly the version, every dot included - `v1.1.0`,
not `v1.10`: the signed manifest points at `releases/download/v1.1.0/DRBR.zip`) > title `DRBR 1.1.0` > the text of
`RELEASE_NOTES.md` > attach `DRBR.zip` > "Set as the latest release" > Publish.

A release under another tag still updates from launcher 1.0.2 on (it falls back to the `DRBR.zip` it checked, still
verified against the signed manifest), but launchers 1.0.0 and 1.0.1 can only download from the exact tag. 1.0.1 went
up as `v1.01`: renaming that tag to `v1.0.1` (Edit release > tag) fixes it for them; once a later release is the latest,
they update to that one instead. After publishing, check it the launcher's way: `drbr-tests.dll live`.

Or with the GitHub CLI:

```
scripts/release-drbr.sh 1.1.0
```

This tags `v1.1.0`, pushes the tag, and creates a **draft** GitHub release with `DRBR.zip`. It uses your `gh` login.
Then run the **release** workflow on GitHub (Actions > release > Run workflow, version `1.1.0`): it builds the programs,
runs the tests that need no game files, downloads the draft's `DRBR.zip` and checks it completely, and publishes after
your approval (the `release` environment). Without the workflow: `gh release edit v1.1.0 --draft=false`.

Once published, every DRBR Launcher finds the release at
`https://github.com/<you>/DRBR/releases/latest/download/DRBR.zip`.

(`release_tools.py release` still makes DRBR 1.0.0's layout - every file as its own asset with `update-manifest.json`
- and launchers still read it, but releases are `DRBR.zip` from 1.0.1 on.)

## Real-PC check (recommended before publishing)

On a Windows PC with DELTARUNE from Steam:

1. Run `DRBR-Setup.exe` and click **INSTALL DRBR**, then **PLAY DRBR**. The game should open in the cold place with the
   hub sign. The launcher should say "DRBR started in room_dw_snow_zone".
2. Open the sign, then ONLINE, and host or join a room with a second PC or a friend.
3. Close the game. The launcher should say "Your own DELTARUNE saves were not touched".
4. Check that Steam's DELTARUNE still plays normally.

## Fixing a bad release

- **Never** re-use a version number. Publish a new version with the fix.
- Before any launcher installs a release, you can turn it back into a draft (`gh release edit vX --draft=true`). The
  `latest` address then points at the previous release again.
- A release must not be published while installation, save-loading or update-integrity problems are open (failing
  `core` or `wine` tests, or the real-PC check).
