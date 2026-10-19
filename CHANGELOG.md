# Changelog

## 1.0.4

### In the game

- **Jevil's Devilsknife works.** When Jevil turned into the Devilsknife, his four Devilsknives never came onto the screen:
  they were swinging round a point about 100,000 pixels away. The cause: Chapter 3 has built-in helpers called `centerx`
  and `centery`, and the Devilsknives (taken from Chapter 1) kept the middle of their swing in variables with those same
  names, so in the built game every read of them got Chapter 3's helper instead of the number. The variables have names of
  their own now. Fixed for all three uses: **Devilsknife**, **Devilsknife Swing** (its red blade too) and the
  **DEVILSKNIFE** skill sent at you. They swing round your box again, in and out through it, as in Chapter 1.
- **Fixed a crash in Spamton NEO's NEO Finale** ("ERROR in action number 1 of Draw Event for object
  obj_sn_playback: draw_sprite argument 1 incorrect type (undefined)"). His playback bar looked its picture up the way
  Chapter 2 does, and Chapter 3 does not know Chapter 2's pictures that way, so the game stopped when it tried to draw it.
  It uses the picture directly now. Found by the new real-game run below, before anyone reported it.
- Checked in the real game this time: the DELTARUNE game program itself ran DRBR (under Wine, see the testing report) through
  all 16 of Jevil's attacks, the DEVILSKNIFE skill and every other boss's attacks.

### For the next ports

- The build is now checked for this whole kind of mistake: every piece of the built game's code is disassembled, and the
  build is refused if any variable is read as a function or an asset of the same name. The test emulator also treats such a
  read as an error now (it used to read the variable, which is why the tests never saw the bug), and it stops on a picture
  draw with a missing picture, as the real game does.

### Compatibility

- 1.0.2, 1.0.3 and 1.0.4 can play in the same room (multiplayer build 51). Each game builds the attacks sent at it with
  its own code: on 1.0.4 every DEVILSKNIFE works, whoever sent it; a player still on 1.0.2 or 1.0.3 keeps the old bug until
  they update.

## 1.0.3

### In the game

- **Going OUT is always the GAME OVER, then watching.** Whatever takes your last HP while the round runs (a hit, a piece
  that takes HP by itself, the party falling another way), your SOUL breaks, the GAME OVER shows over the battle, and you
  watch the rest of the round. 1.0.2 could show the OUT box ("Back to the room") in the middle of a round: a hit on your
  hidden SOUL after you were already OUT still took your last HP, also while you were typing in the chat.
- **Watching shows the player you watch.** Their character stands where your hero was (their skin), the HP panel is theirs
  (head, character name, HP, colour and shield), the TP bar is their gauge, and the watching card shows their skill slots
  with the skills' pictures. Their character blinks when they are hit. **<** / **>** switches all of it to another player.
- **END ROUND for the host.** BACKSPACE in a match has END ROUND (it asks again): the round ends for everyone and the most
  HP wins, as when the time runs out. The room's page has an END ROUND row while a match runs too.
- **The bosses' sends are in the sender's SOUL colour.** Every piece of a Jevil, Gerson, Spamton NEO, Pink or Flowery
  send, and the boss's phantom beside your box, is drawn in the sender's colour over its own art, keeping its lines and
  shading. The boss's own pieces never are, so a send is always told apart.
- **A boss's send fits your box.** Pieces that were made for the boss's own battle are scaled to the box (Gerson's bells
  stand at its sides, the BIG SHOT beam is half as wide, Pink's warning crosses stay inside).
- **Bots shoot and show their skills.** On Spamton NEO's yellow SOUL every bot fires its shots and BIG SHOTs, and everyone
  sees them. A skill a bot (or a player) uses is shown over their SOUL: its name, a ring, and for an attack a diamond
  flying to its target. Bots wear their own skins, also in the cold place.
- **Flowery's tower is back** behind his battle (it was drawn far off the left of the screen).
- **Jevil's Devilsknife plays Chapter 1's own "METAMORPHOSIS!"** (the build's sound of that name was another, longer
  clip) and his own laugh. All 16 of his attacks were checked at the real arena camera.

### Compatibility

- 1.0.2 and 1.0.3 can play in the same room (multiplayer build 51). A 1.0.2 game does not show the new things (bots'
  shots, skill marks, the watched player's side); it ignores those messages.

## 1.0.2

### In the game

- **Fixed a crash on Flowery's board** ("ERROR in action number 1 of Draw Event for object obj_fl_soul ...
  fakecamxspeedadditional not set before reading it"): the orange SOUL was drawn after the board's controller was gone. Now,
  if a part of Flowery's board (its controller, the orange SOUL or the battle box) is gone in the middle of an attack, the
  board ends in that game the way an attack's end ends it - its pieces go and your red SOUL is back in the box - and the
  game goes on. His next attack builds the board again as usual.
- **Skills on the yellow and orange SOULs.** On Spamton NEO's yellow SOUL and Flowery's orange board, Z belongs to the
  SOUL (it shoots or dashes), so USE SKILL is on **S** (HOLD BREATH's key, LT on a controller) while they are up. The game
  now says so all the while: **SKILLS: HOLD S** beside your skill slots, in the SOUL hint under the box, and on the
  KEYBINDS page. The label blinks when you hold Z with a skill ready. Before, only Flowery's first attacks said it, so it
  looked as if skills did not work there.
- **Jevil's Devilsknife has his own voice again.** When he turns into the Devilsknife you hear Chapter 1's "METAMORPHOSIS!"
  alone (DRBR used to play a laugh or "CHAOS, CHAOS!" over it). BYE-BYE says "BYE-BYE!" once instead of twice. The
  DEVILSKNIFE skill lands with "METAMORPHOSIS!" too (it came in silently).
- The SOUL hint stays under the battle box and on screen.

### Installing and updating

- **A release under the wrong tag still updates** (from this launcher on). If a release is put up under another tag than
  its version (1.0.1 went up as `v1.01`), the 1.0.2 launcher downloads the changed files from the DRBR.zip it just checked
  (it is still checked against the signed manifest). Before, the update stopped with "There is no DRBR release to update
  from yet". Launchers 1.0.0 and 1.0.1 still need the exact tag (`v1.0.2` for this release).

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
