KNIGHT HUB - Chapter 3 (DELTARUNE) - installer instructions
============================================================
Knight Hub puts all the Knight mods into one data.win for DELTARUNE Chapter 3 v0.0.105.
This file explains how to install it, how to undo it, and what to do when something goes wrong.
(The installer never downloads anything and never touches Steam.)


1. WHAT IS IN THE PACKAGE (exact file names)
--------------------------------------------
  INSTALL_KNIGHT_HUB.bat            double-click this to install (it only starts the .ps1 below)
  install_knight_hub.ps1            the installer program (all the logic lives here)
  RESTORE_VANILLA.bat               double-click this to put the original data.win back
  KNIGHT_HUB_MANIFEST.txt           list of every file with its size and SHA256 checksum
  knight_hub_chapter3.xdelta.part0  } the patch, split into pieces. The number of pieces is
  knight_hub_chapter3.xdelta.part1  } decided by KNIGHT_HUB_MANIFEST.txt (the installer joins
  knight_hub_chapter3.xdelta.part2  } them itself in the order the manifest lists; there may be
  knight_hub_chapter3.xdelta.part3  } more or fewer than four)
  xdelta3.exe                       the patching tool (xdelta 3.1.0)
  knight_hub_extras.zip             OPTIONAL fight music (see section 5)
  knight_hub_music.zip              build 47: OPTIONAL - the seven new fight songs (see section 5)
  knight_hub_music2.zip             build 48: OPTIONAL - twelve more fight songs (see section 5)
  kf_steam.dll                      build 45: the online battle royale's Steam rooms (the mod's own small DLL)
  steam_api64.dll                   build 45: Valve's Steam API (from the Steamworks SDK 1.65), used by kf_steam.dll
  steam_appid.txt                   build 45: "480" - Steam rooms run as Steam's test app (Spacewar)
                                    (these three stay in chapter3_windows next to data.win; see DRBR_ONLINE_GUIDE.txt)
  DRBR_ONLINE_GUIDE.txt             DRBR - DELTARUNE BATTLE ROYALE, the online battle royale (it was KNIGHT FIGHTS ONLINE):
                                    how to play, the bosses, the keys, settings, Steam, known issues
  DRBR_BOSSES.txt                   the online bosses (Jevil, Gerson, Flowery, Spamton NEO, Pink): what is the original game's
                                    and what had to change for a shared online fight
  SKINS.txt                         the online skins, and how to add one
  knightfights_server.zip           the online battle royale's relay server (only for RELAY rooms: the player who runs the
                                    server for a group needs it; Steam rooms do not)
  README_INSTALL.txt                this file
  SHA256SUMS.txt                    checksums of the files above (for checking a download)

You do NOT need JOIN_PATCH.bat any more; the installer joins the parts itself.
Every file must be in the SAME folder: your DELTARUNE "chapter3_windows" folder.


2. INSTALL
----------
 1. Close DELTARUNE completely.
 2. Find your Chapter 3 folder. In Steam: right-click DELTARUNE > Manage > Browse local files, then
    open the "chapter3_windows" folder (the one that contains data.win).
 3. Copy ALL package files listed above into that folder. If you got a .zip, extract it first;
    do not run the installer from inside the zip.
 4. Double-click INSTALL_KNIGHT_HUB.bat.
    - For a folder under "Program Files", Windows may need "Run as administrator"
      (right-click INSTALL_KNIGHT_HUB.bat > Run as administrator). The installer tells you if the
      folder is not writable.
 5. The installer shows what it found, asks you to type Y to continue, and then:
      a) checks that data.win is the original Chapter 3 v0.0.105 file (SHA256 check),
      b) checks xdelta3.exe, the manifest and every patch part (size + SHA256 of each part),
      c) checks free disk space,
      d) joins the parts, and checks the joined patch,
      e) makes your backup data.win.vanilla (from the verified original only),
      f) builds the patched file in a temporary file and checks its SHA256,
      g) swaps it in safely (see section 6) and checks the final data.win again,
      h) copies the optional music (section 5).
    The window stays open at the end. "RESULT: SUCCESS" means it worked.
 6. Start DELTARUNE, load a save at the Roaring Knight area (cold place) and use the sign there.

Shortcuts (optional, not needed for the install; keep them in the same chapter3_windows folder):
  PLAY_KNIGHT_HUB.bat   installs the hub, replaces an older Knight Hub build if it finds one, then starts Chapter 3.
  LAUNCH_CHAPTER_3.bat  only starts Chapter 3 (links the music folder first). Neither .bat has been run by the author. PLAY_KNIGHT_HUB.bat can be double-clicked from the downloaded folder: it finds the game folder, copies the files in and installs.

Running the installer again is harmless: if Knight Hub is already installed it says so and changes
nothing in data.win. To force a clean reinstall from your backup, run from a command prompt in the folder:
    powershell -NoProfile -ExecutionPolicy Bypass -File install_knight_hub.ps1 -Force


3. UNINSTALL / GO BACK TO NORMAL DELTARUNE
------------------------------------------
Double-click RESTORE_VANILLA.bat. It checks that data.win.vanilla really is the original file
(SHA256), then puts it back as data.win using the same safe swap. data.win.vanilla is kept.
Manual way (only if you have to): close the game, delete data.win, rename data.win.vanilla to data.win.
Do this only if data.win.vanilla is the original; RESTORE_VANILLA.bat checks that for you.
The music files you copied can stay; they do nothing without the mod.
The other Knight Hub files in the folder stay too (the .bat files, the patch parts, kf_steam.dll, steam_api64.dll and
steam_appid.txt): the normal game does not use them, and installing again needs them. Delete them by hand if you
want them gone.


4. IF DATA.WIN IS NOT SUPPORTED ("exit code 6") / STEAM "VERIFY INTEGRITY"
---------------------------------------------------------------------------
The installer only patches the exact original Chapter 3 v0.0.105 data.win. If your data.win is
modded by something else, an old Knight Hub build, or a different game version, the installer
REFUSES and does not change anything.
To get a clean original data.win:
  - If you have a good backup named data.win.vanilla, use RESTORE_VANILLA.bat.
  - Otherwise use Steam's repair: Steam > Library > right-click DELTARUNE > Properties >
    Installed Files > "Verify integrity of game files". Steam then re-downloads files that differ
    from the original. Wait until Steam says it finished, then run INSTALL_KNIGHT_HUB.bat again.
  Notes: the installer does not start the Steam check for you and cannot know whether it
  finished. Steam verification also reverts other mods in the game folder, and if DELTARUNE has
  been updated beyond v0.0.105 the restored file will be a newer version that this mod does not
  match (the installer will then refuse again; you need a Knight Hub build made for that version).


5. OPTIONAL MUSIC
-----------------
The fight songs are optional. Without them the fights use their default music.
The installer looks for these files (listed in KNIGHT_HUB_MANIFEST.txt) either beside the installer,
or inside knight_hub_extras.zip / knight_hub_music.zip / knight_hub_music2.zip (entries named mus/<name>), and copies them into
the folder DELTARUNE\mus  (the "mus" folder next to chapter3_windows; created if needed):
    mus\knightmare_knight.ogg
    mus\thorn_knight.ogg
    mus\its_nothing_but_garbage_noise.ogg
    mus\superchargedknight\cleaver.ogg      (keep it inside its own folder)
  build 47 (knight_hub_music.zip), picked in FIGHT SONG (offline) and MORE OPTIONS > MUSIC (online):
    mus\kh_void_star.ogg            VOID STAR - rundown (soundcloud.com/rundownsd/void-star)
    mus\kh_lv_crusher.ogg           L.V. CRUSHER - saknol (soundcloud.com/saknol/lvcrusher)
    mus\kh_true_hero.ogg            TRUE HERO - Tory Fox [DISC 2] (soundcloud.com/toryfox2/mus_undynex_ogg)
    mus\kh_neotech_online.ogg       NEOTECH:ONLINE - antagonist (soundcloud.com/genericantagonist/neotech)
    mus\kh_storyshift_black.ogg     STORYSHIFT ~ 100. BLACK - Jay (soundcloud.com/jay_josh1212/jackblack)
    mus\kh_anywhere_you_go.ogg      ANYWHERE YOU GO [LEGACY] - lexxiemoww (soundcloud.com/lexxiemow/x_cc)
    mus\kh_ever_ascending.ogg       EVER ASCENDING - lexxiemoww (soundcloud.com/lexxiemow/trinky_finale)
  Flower Man (feat. Camellia) - Toby Fox is the game's own file, DELTARUNE\mus\Flowerman_Arrangement.ogg: it is not
  shipped or copied; the song list uses it from there (if a game does not have it, picking it plays the fight's music).
  build 48 (knight_hub_music2.zip; credits and links also in CREDITS on the KNIGHT page):
    mus\kh_lost_dream.ogg           LOST DREAM // VS NOELLE.EXE - ImperfectNORE (soundcloud.com/imperfectnore)
    mus\kh_forget_me_not.ogg        FORGET ME NOT V3 (DELTARUNE Chapter 6) - JustStereo (soundcloud.com/juststereo)
    mus\kh_hell_hammer.ogg          HELL HAMMER - Geefel (cover; original amt1179, AU Chapter Rewritten)
    mus\kh_in_my_way.ogg            In My Way - SEWNPUARD (soundcloud.com/sewnpard)
    mus\kh_till_the_end.ogg         TILL THE END (Encounter with Friends) - DanlyDaMusician
    mus\kh_megalo_vania.ogg         MEGALO VANIA - igorsantusa (original: mcswordguy)
    mus\kh_megalo_strike_back.ogg   (Unused) MEGALO STRIKE BACK - EVAERDRAD (soundcloud.com/modestbbq)
    mus\kh_red_crimson_death.ogg    RED, CRIMSON DEATH - Tory Fox, Igorsantusa (soundcloud.com/toryfox2)
    mus\kh_wrong_enemy.ogg          Wrong Enemy....? - Tory Fox (soundcloud.com/toryfox)
    mus\kh_n1ght_of_n1ghtcore.ogg   N1GHT OF N1GH+COR3 >:3 - plush (soundcloud.com/plushcat)
    mus\kh_that_feeling.ogg         That Feeling (In Your Bones) - sunhatgirl (title: d3adeyes)
    mus\kh_identity_crisis.ogg      IDENTITY CRISIS (Arrangement) - moved accounts!! (original: DIRECT-TO-DARKNESS)
  Guardian - Toby Fox is the game's own Chapter 4 file, DELTARUNE\mus\titan_battle.ogg (not shipped, like Flower Man).
  RANDOM picks one of the songs you have for every fight. Z on FIGHT SONG / MUSIC opens the song list (title and
  artist, C listens). All these tracks are the artists' own (their pages say all rights reserved): credited, not ours.
Rules: an existing kaizoknight.ogg is NEVER overwritten, whatever happens. A file that is already
there and identical is skipped. A file that is already there but different is left alone with a
warning (to replace it anyway, run the .ps1 with -OverwriteMusic). A missing or damaged optional
music file only produces a warning; it never fails the installation (exit code 0).


6. HOW IT KEEPS DATA.WIN SAFE
-----------------------------
 - data.win.vanilla (the backup) is only ever made from a data.win that passed the original-file
   SHA256 check. If data.win.vanilla already exists it is checked first: a good one is kept and
   used; a bad one (not the original) is never used, never overwritten and never deleted - the
   installer stops (exit code 7) and tells you.
 - The patch is written to a temporary file in the game folder named .knighthub_tmp_<something>
   and checked before your data.win is touched. Only files with that name prefix are ever deleted
   by the installer, on success and on failure.
 - The swap: data.win is renamed to data.win.knighthub_prev, the new file is renamed to data.win,
   the new data.win is checked by SHA256, and only then is data.win.knighthub_prev deleted. If any
   step fails, the previous data.win is put back automatically.
 - If the computer crashes or the window is killed in the middle, just run the installer again:
   if data.win is missing but data.win.knighthub_prev exists, the installer puts it back first,
   leftover .knighthub_tmp_* files are removed, and then it continues normally.
 - If DELTARUNE (or anything else) has data.win open, the installer stops before changing anything
   (exit code 9). Read-only files or folders stop it too (exit code 15).
 - Free disk space is checked first: roughly the size of the joined patch + the new data.win
   (+ the size of data.win for the first backup) + a 5% margin, computed from the manifest.


7. THE LOG
----------
knight_hub_install.log (next to the installer) is appended on every run and restarted when it
gets big. It lists what the installer checked and did, using only file names relative to the game
folder. It does not record your user name, computer name or environment variables; folder paths
in error messages are shortened to <game folder> / <DELTARUNE folder>. If you ask for help, send
this file.


8. EXIT CODES (shown in the window and returned by the .bat files)
-------------------------------------------------------------------
   0  Success (installed / already installed / restored / already original). Missing optional music
      is only a warning and still gives 0.
   1  Unexpected internal error (see the log)
   2  Wrong folder: data.win not found next to the installer (or run from inside a zip)
   3  xdelta3.exe missing, not the expected file, or cannot be started
   4  KNIGHT_HUB_MANIFEST.txt missing or invalid
   5  A patch part is missing, has the wrong size, or has the wrong checksum (the message names it)
   6  data.win is not supported (different version or different mod); nothing changed
   7  data.win.vanilla exists but is not the original file; nothing changed
   8  Not enough free disk space (or the disk filled up); nothing changed
   9  data.win is in use (close DELTARUNE); nothing changed
  10  Patching failed (xdelta3 error or the result did not match its checksum); data.win unchanged
  11  Replacing data.win failed; the previous data.win was put back
  12  The new data.win failed the final check; the previous data.win was put back
  13  No valid data.win.vanilla available (needed by RESTORE_VANILLA and by -Force reinstall)
  14  You answered anything other than Y to the question
  15  No permission (read-only file or folder); nothing changed
  16  CRITICAL: the replacement failed and the previous data.win could not be put back
      automatically. The message tells you how to do it by hand (your previous file is kept as
      data.win.knighthub_prev)
  17  A NEWER Knight Hub build is installed than this package (you ran an older folder's
      installer); nothing changed. Use the newest folder. PLAY_KNIGHT_HUB.bat starts the newer
      one. (The installer notes the installed build in knight_hub_build.txt.)
  99  Simulated failure (test hook, see section 10)


9. TROUBLESHOOTING
------------------
 - "data.win was not found": the files are not in the chapter3_windows folder (section 2, step 2-3).
 - "xdelta3.exe is missing": copy xdelta3.exe from the package next to the installer.
 - "Patch part ... missing / wrong size / checksum mismatch": the file is incomplete or damaged,
   or from a different build. Download that one file again (all parts must be from the same
   build as KNIGHT_HUB_MANIFEST.txt). Parts are joined in the manifest's order, not by file name.
 - "data.win is in use": quit DELTARUNE; check Task Manager for deltarune.exe; also pause any
   program that scans the game folder, then run again.
 - "not writable": use Run as administrator, or move the game to a normal folder.
 - Windows says the script is blocked or does nothing: right-click the downloaded .zip >
   Properties > tick Unblock BEFORE extracting. The .bat starts PowerShell with
   -ExecutionPolicy Bypass for this one script only.
 - Antivirus removed xdelta3.exe or a part: restore it from quarantine or download again.
 - The folder name has odd characters (& ^ % ! ( ) ' [ ] ; , = or non-English letters): this is
   supported. If something still fails, send knight_hub_install.log.


10. FOR TESTERS / SUPPORT (environment variables; ignored when not set)
------------------------------------------------------------------------
  KH_XDELTA=<path>            use this xdelta3 program instead of xdelta3.exe beside the installer
  KH_NOPAUSE=1                the .bat files do not wait for a key at the end
  KH_ASSUME_YES=1             do not ask the Y question
  KH_FREE_BYTES_OVERRIDE=<n>  pretend the drive has n free bytes
  KH_FAIL_AT=<stage>          simulate a failure at: after_join, after_backup, after_patch,
                              after_verify_output, after_prev_rename, after_move,
                              after_final_verify, before_music, after_restore_copy
  KH_FAIL_MODE=exit           together with KH_FAIL_AT: stop dead with exit code 99 and no cleanup
  Switches of install_knight_hub.ps1: -Restore, -Force, -OverwriteMusic.
  Build tools (not part of the download): make_manifest.py, make_package.sh, run_installer_tests.py.


11. USING THE MOD
-----------------
Walk to the sign in the cold place (Roaring Knight area) and interact with it. Use a save at
story point 310-330 there. The Knight Hub menu works like DELTARUNE's own dark-world menu.

Controls: arrows move, Z = select, X = back, C = START from any page.
Backspace during a fight asks if you want to leave it. Build 41: R restarts the fight at once and holding TAB
fast-forwards (see HOTKEYS below).

Top bar: five buttons. Left/right picks one, Z (or down) opens it, X closes the hub.
Inside a page the top bar describes whatever is highlighted.
  KNIGHT   the fights: Normal, Kaizo, Supercharged, Violet, Thorn, Cyan (joke), KNIGHT RUSH, RANDOM, and (build 41)
           TAG TEAM and ATTACK REMIX (below), and (build 43) ONLINE - KNIGHT FIGHTS ONLINE, below. The right side
           shows the knight, who made it and your best time. Z on a
           fight opens the START box (who fights, which rules, automatic corrections); START begins it.
  PARTY    3 slots. Left/right picks a slot, up/down changes who is in it (Kris, Susie, Ralsei, Noelle or
           nobody; duplicates and solo are fine). Z opens that member's equipment (weapon, two armors):
           left/right steps through what they can wear, Z opens the full list (the stats show the change).
           Equipment is saved in presets and put back when you leave the hub.
  POWER    each member's 12 spell slots. Z opens the list, left/right changes the spell in a slot,
           Z empties it. Your spell and equipment set is remembered between sessions.
  RULES    16 switches in two columns (Z toggles; "--" = not possible with the current setup):
             NO-HIT, NO ITEMS, NO HEALING, 1 HP START, SOLO, 2X DAMAGE, HALF MAX HP, NO TP,
             ONE LIFE, TWIN KNIGHT, DARKNESS, HYPER SPEED, THORNS, TIME LIMIT, RANDOM PARTY, RANDOM RULE.
           Incompatible choices are refused with a reason and a suggested fix.
  CONFIG   FIGHT SONG (left/right picks, Z previews; missing files are marked), WEIRD ROUTE, WEIRD STATS,
           PRACTICE (OFF / PICKER / START AT / REPEAT, below), INFINITE HP (below), QUICK RETRY (No-Hit restarts by
           itself), HOTKEYS (below), RUSH ORDER, RUSH HEALING (full / 75 / 50 / 25% / none), LOADOUTS (ready-made
           parties, below), PRESETS (8 slots: save, load, rename, delete), RECORDS, CREDITS.
           RECORDS: per knight and category (Normal, Rules, No-Hit, Practice) wins/attempts, best time, least
           damage, no-hit streak, fights left early; Z explains the numbers. Tag Team and Attack Remix have tables
           of their own (Normal, Rules, No-Hit). CREDITS: one page per fight with the people its GameBanana page
           credits, plus a page for the hub.

LOADOUTS (build 36): ready-made party + equipment + spells. Left/right picks the party (KSR, KSN, KRN, SRN,
the duos KS, KR, KN, SR, SN, RN, the solos, DOUBLE and TRIPLE), up/down the loadout, Z loads it after asking. It replaces
the party and those members' gear and spells; the knight, the rules and the song stay. Save it in a PRESET slot
if you want to keep a mix. The page opens on your current party with MAXED highlighted.
  BASE        the normal end-of-Chapter-3 gear and spells (as in the Kaizo Knight mod's own save file):
              Kris Saber10 / TennaTie / Jevilstail; Susie ToxicAxe / Dealmaker / ShadowMantle; Ralsei FlexScarf /
              RoyalPin / TwinRibbon; Noelle SnowRing / Silver Watch / RoyalPin. Spells: Kris ACT; Susie Rude Buster,
              UltraHeal; Ralsei Pacify, Heal Prayer; Noelle Heal Prayer, SleepMist, IceShock.
  MAXED       the best gear (Kris BlackShard, Susie and Ralsei EverybodyWeapon, Noelle ThornRing - it halves her
              IceShock / SnowGrave TP and slowly drains her HP to a third; Dealmaker plus TennaTie for Kris and
              Susie, plus RoyalPin for Ralsei and Noelle) and each member's OWN moves for that party:
              Kris ACT, X-Slash and the SOUL moves (Red Buster with Susie, Dual Heal and Heatwave with Ralsei,
              Permafrost with Noelle); Susie Rude Buster, UltraHeal; Ralsei Heal Prayer, Pacify, FireShock, plus
              Frostfire and Dual Heal with Noelle; Noelle Heal Prayer, SleepMist, IceShock, SnowGrave, plus
              Frostfire and Dual Heal with Ralsei.
  DUAL MOVES  BASE gear and spells plus every two-person move the party can do (only shown where there is one).
  DOUBLE      KRIS x2, SUSIE x2, RALSEI x2, NOELLE x2 (build 38): two of one member, MAXED, one HP bar.
  TRIPLE      KRIS x3, SUSIE x3, RALSEI x3, NOELLE x3: three of one member, MAXED. The three share one HP bar, one
              set of gear and one spell list (the game keeps those per character).
  SHADOW MANTLE: only one member can wear it in a setup. Every loadout has exactly one when someone in it can wear
              it: Susie first, else Kris, else Ralsei (Noelle cannot wear it, so solo Noelle and NOELLE x3 have
              none). In the PARTY page, stepping through armor never takes it from whoever wears it; picking it
              from the list moves it (the top bar says from whom). A preset with more than one is fixed on load.

The rules added in build 35:
  TWIN KNIGHT   a second knight stands behind the first and attacks in every knight turn with its own
                pattern (falling stars, swords from the sides, star bursts or dashing swords), in that fight's
                own bullet art. Its bullets hit like the knight's (a bit softer), can be grazed for TP and leave
                at the end of the turn. It holds back during the Roaring and the finale.
  DARKNESS      during the knight's turn everything goes dark except a small light around your SOUL.
  HYPER SPEED   the battle runs at 38 steps a second instead of 30 (25% faster). Battle times stay in real seconds.
  THORNS        every hit also takes 30% of the HP it removed off that member's max HP for the rest of the
                fight (never under a third). Only hits count: the ThornRing's own HP drain does not (build 37).
                Thorn Knight already does this itself, so the rule skips it.
  TIME LIMIT    win within the knight's attack list + 10 enemy turns (Normal 25, Kaizo 37, Supercharged 27,
                Violet 32 / Side B 37, Thorn 30, Cyan 30) or the attempt is lost (TIME UP). A Roaring that has
                started always finishes. Not with Practice. Build 41: Tag Team gets both knights' lists + 10
                (Normal + Kaizo: 25 + 37 - 10 = 52), Attack Remix 34; the START box shows the number.

Fight pacing (all fights, build 35; smoother since build 39):
  Every knight plays a fixed list of attacks and starts its Roaring once its HP is at or under a gate
  (Normal 80%, Kaizo 60%, Supercharged 80%, Violet 65% / Side B 13%, Thorn 50%). Strong setups used to pass
  the gate early and skip the end of the list, where the mods keep their new attacks. So, until the list has
  been played, the knight follows a schedule line (full HP down to the gate on the last listed turn): damage
  that keeps it above the line counts in full, and damage past the line counts 35% at first, then less the
  further ahead of the line the knight already is, down to 5%. Build 39: there is no hard stop at the gate any
  more, so a hit always does damage (no more MISS once a strong party gets ahead); a very strong party reaches
  the Roaring a few turns before the end of the list instead (the Weird Route's scenes then come right before
  the Roaring). The knight cannot fall before its Roaring (its last 5% of HP counts less and a hit always leaves
  it at least 1 HP). Slow parties get a catch-up instead (+12% per turn past the list, up to x2). Practice, Cyan
  and everything after the Roaring keep the fight's own rules. Also: nothing hurts Supercharged Knight while it is
  phasing (UNLEASH first; the hub's spells used to slip through), Violet's Side B ends only with its finisher
  after the Roaring (Kris's X-Slash, or the Kris-less finisher) - other hits still show their damage there, but
  the Knight stays at the mod's 8% (build 38 showed MISS) - and Kaizo Knight's guard divides X-Slash the way it
  divides Ice Shock and FireShock.

INFINITE HP (CONFIG, build 38): party HP never goes down. Every hit still lands (damage numbers, the hurt flash,
  No-Hit still fails on a hit) but takes no HP, so nobody goes down; drains take nothing either (ThornRing, Kaizo
  Knight's GLOOM and the SnowGrave it turns back), and Thorn Knight wears no max HP down. The story still happens:
  the Weird Route and Violet's Side B still take members. Runs with it on are not recorded (no wins, attempts or
  times). Not with 1 HP START.

Party details:
  Supercharged Knight does not need Kris: its last phase's UNLEASH (Reveal the Knight) is used by Kris when
  they are in the party, and by the top-most living party member otherwise. Noelle has an ACT in every fight.
  Without Kris (build 38) Susie, Ralsei and Noelle each get HOLDBREATH (the SOUL moves faster) on their own
  S / R / N-Action list in every fight, like Kaizo Knight already did; on Violet Knight it toggles with DEEPBREATH
  like Kris's. If the Knight takes Kris on a Weird Route, the others get it then.

WEIRD ROUTE (build 37: every fight, every party; build 38: the party ORDER decides):
  Who is taken  the member on TOP of the party is never taken (on Violet Knight they finish the fight). The
                Knight takes the BOTTOM member first, then the next one up - Kris too, when Kris is not on top.
  The talk      after a loss the others react in their own speech bubbles. Susie always speaks first, wherever
                she stands; the others pick up after her in party order (top first), then everyone says what
                they will do about it (Susie's fury, Ralsei's resolve, Noelle's courage). Kris does not speak.
  Learned moves (on the member's own S / R / N-Action list for that fight)
                RUDER BUSTER  Susie, when the Knight takes Ralsei (or after the first loss she sees when it can no
                              longer take Ralsei in that fight): two Rude Busters, the second 15 frames after the
                              first, like X-Slash's two slashes. 60% TP. (Replaces the old RED BUSTER unlock.)
                ICESTORM      Noelle finds her courage after the first loss she sees: two Ice Shocks, X-Slash
                              timing, 30% TP (she also learns SnowGrave).
                FIRESTORM     Ralsei, after the first loss he sees: two FireShocks, X-Slash timing, 30% TP.
  The last one  when the Knight comes for someone and only one member is left, it charges them and they knock
                the blade back: nobody dies and the fight goes on.
  Kaizo Knight   its own Side B. Kris has the X-Slash ACT; without Kris, Susie gets a RudeBuster S-Action
                 (25% TP, her own Rude Buster) instead.
  Violet Knight  its own Side B: a loss at the end of phase 1 and one at the end of phase 2. With Kris on top,
                 as the mod plays it (Kris ends the fight with X-Slash once Susie is gone - unlocked when the
                 Knight takes Susie, or when Kris is left alone). With anyone else on top, that member gets a
                 power-up scene after the second loss (or parry) and ends the fight after the Roaring with their
                 move: Susie RUDER BUSTER (Rude Buster if she never learned it), Ralsei FIRESTORM (FireShock),
                 Noelle SnowGrave.
  Normal, Supercharged, Thorn, Cyan  (no Side B of their own) halfway through the attack list the Knight takes
                 the bottom member at the end of its turn (never the top member or the last one standing). The
                 lost member cannot be healed back and the Knight hits 25% harder from then on. A solo party parries
                 at that point instead, and a two-member party is down to one: at about 3/4 of the list the
                 Knight charges that member, who parries. Build 39: if a strong party already has the knight at
                 its Roaring gate before that point, the scene comes at the end of that enemy turn instead (and
                 the parry one enemy turn later), so the Roaring never skips them.
  Noelle shows her Side B (Angel) sprites on a Weird Route save in every fight. Not with Practice (the
  scenes are skipped) or One life.
  WEIRD STATS (needs Weird Route): the party uses the Weird Route file's HP / ATTACK / DEFENSE / MAGIC (Kris
  186/15/2/0, Susie 222/19/2/3, Ralsei 166/13/2/12, Noelle 166/8/1/16); weapons and armor stay yours.
  Stats are rebuilt from YOUR saved values at the start of every fight, so nothing a fight does to them can
  stack into the next fight. A member who is already down takes no further damage.

WHEN SUSIE IS NOT IN THE FIGHT (build 39):
  In every knight Susie taunts the Knight in her own speech bubble during the fight (turns 6 to 14: "Heheh... Didn't think
  we'd still be standing, did you?" ... "people like you... just piss me off."). Without her nobody said anything. Now the
  first of Ralsei / Noelle in party order who is still standing says those beats in their own words, in their own voice
  and bubble (Kris never speaks):
    Ralsei   gentle even here (build 40): where Susie taunts, he hopes, cheers his friends on and pleads ("So...
             please... stop this..."); he heals them, and at the end he apologizes and still means to stop the Knight
             ("I'm sorry... But we have to stop you."). He never threatens or demands.
    Noelle   Susie's own steps in Noelle's voice - stammering where Susie smirks ("D-didn't think we'd still be
             standing, did you?"), ending in her own outburst ("People like you... LEAVE MY FRIENDS ALONE!!").
    Noelle on a Weird Route save (the Angel): Susie's steps again, melodramatic - shaking laughter, power she is afraid
             of, Kris always behind her ("Me? I have Kris. Kris is ALWAYS behind me...", "So... give up. ...Please. I
             don't want to do it again.", "People like you... make me want to FREEZE it ALL!!").
    Cyan Knight (joke fight): joke lines in their voices, like Susie's there.
  The lines follow the party: they name the friends who are really there, and change when those friends are down or when
  the member is alone. If that member is down the next one takes over; Susie down (but there) still means nobody talks, as
  in the original fight. Susie's own lines now name the real party in every knight too (the Normal, Supercharged and Thorn
  Knights had her name Kris and Ralsei whoever was there). No talk in Practice; the Kaizo Knight's frozen check and the
  Violet Knight's Side B (after a loss the survivors' own talk takes over) still apply. The narration before the Roaring
  ("* Susie grew pale.") names whoever is there. Noelle's N-Action on a Weird Route save is the Angel's own lines too
  (the Kaizo Knight keeps its own Noelle ACT). The lines were written from Ralsei's and Noelle's dialogue in the
  Chapter 2 and 3 game files; how they read in the real game has not been seen.

TAG TEAM (KNIGHT page, build 41): two knights in one battle.
  Z on TAG TEAM opens a page with the six fights: left/right picks the slot (FIRST / SECOND), Z puts the highlighted
  knight there (the same knight twice is allowed - a mirror match), START begins. The first knight starts; after every
  enemy turn the other one steps forward, so they take turns. Each keeps its own HP bar (shown top right), its own ACTs,
  attack list, pacing and Roaring, and damage only reaches the one in front; the one waiting stands at the back. When one
  is beaten after its Roaring it is knocked out ("NORMAL KNIGHT IS DOWN! THORN KNIGHT TAKES OVER!") and the other fights
  on alone to its own ending. Beat both to win. With FIGHT SONG = MOD DEFAULT the knight that takes over brings its own
  song (the old one fades out over a second, the new one fades in over two). Weird Route, Practice and Twin Knight are
  switched off for it (the START box says so); a team with the Cyan joke fight is not recorded.
ATTACK REMIX (KNIGHT page, build 41; build 42: you pick the knights, never the Cyan joke fight): Z on ATTACK REMIX opens
  a page with the five fights. Z (or left/right) switches a knight on or off (at least one stays on); START or C begins.
  Every enemy turn one of the knights that are on steps in (never the same one twice in a row when two or more are on)
  and uses one random attack from its own list (unused and finale attacks left out); the battle box says who comes next
  and with which attack. With only one knight on, it takes every turn with its attacks in random order. The knights share
  one HP bar. The Normal Knight opens the battle and returns at 30% HP for the finale (its own Roaring and ending) - also
  when it is switched off for the turns, because the finale is its own. Own records table (the record notes the knights
  when not all five were on). With Supercharged Knight on, No TP and One life are refused as in its own fight.
PRACTICE FROM ANY ATTACK (CONFIG > PRACTICE, build 41): left/right sets OFF, PICKER (the in-fight attack picker, as
  before), START AT or REPEAT; Z opens the selected knight's attack list (PHASE / FINALE marks, unused attacks in gray) and
  Z there picks the attack.
    START AT  the real fight starts at that attack: the knight's HP and the pacing are set to where that attack comes,
              then the list goes on from there to the Roaring and the ending.
    REPEAT    the knight uses only that attack, turn after turn, and cannot fall (its HP refills). Not with TIME LIMIT.
  Neither is recorded, neither works in Knight Rush, Tag Team, Attack Remix or with Weird Route (the START box says so).
HOTKEYS (CONFIG, build 41, ON by default): during a fight (walk-in, battle, after the win; not in a menu or a results
  box) R restarts the fight at once (it counts as a fight left early; in Knight Rush it restarts the Rush), and holding
  TAB fast-forwards talk, scenes, the walk-in and the walk after the fight four times as fast - never while bullets are
  flying or the FIGHT bars are up, and never in an online match (TAB is the player list there). Battle times are game
  time, so fast-forwarding does not shorten them.
FIGHT STATS (results box, build 41): "Fight stats" ("Rush stats" in Knight Rush) shows damage dealt and taken per member
  ("Other" = damage the hub could not tie to a member) and every attack the knight used, how often, and how many times it
  hit you (most hits first, yellow = never hit you; 8 per page, "Next page" for more).
Music (build 41): Violet Knight's Side B (Weird Route) no longer cuts the battle song dead and starts the Side B song at
  full volume: the song fades out in a third of a second at the blow and the Side B song fades in over two seconds (if
  the old song was still playing it fades out under the new one instead of playing on). The other knights' Weird Route
  scene brings the music back over a second and a half instead of one.

DRBR - DELTARUNE BATTLE ROYALE (it was KNIGHT FIGHTS ONLINE; KNIGHT page > ONLINE; rebuilt in build 45): a battle royale for 2 to 8 players. Everyone dodges
  the SAME Knight with the SAME attacks at the SAME moment (one shared match timeline every game works out from the
  host's seed); your own dodging, hits, HP and skills are decided in your game, so lag never touches your movement. The
  knight switches between attacks as the room says (CLASSIC, KNIGHT RUSH, RAPID, RANDOM, PROGRESSIVE, WEIGHTED,
  NIGHTMARE), the match climbs through five stages, then SUDDEN DEATH; the last SOUL standing wins. Online knights:
  NORMAL, KAIZO, ELECKNIGHT, VIOLET, THORN and KNIGHTMARE (never the Cyan joke fight, which is unchanged offline), and
  (build 51 update 9) five bosses of the other chapters with their own SOULs: JEVIL (Chapter 1), GERSON (Chapter 4, green
  SOUL), FLOWERY (Chapter 5, orange SOUL), SPAMTON NEO (Chapter 2, yellow SOUL) and PINK (Chapter 5, purple SOUL) - each
  the game's own fight taken from your own DELTARUNE files when the patch is made (DRBR_BOSSES.txt).
  Rooms: STEAM (host / 7-letter code / browse / invites - kf_steam.dll, steam_api64.dll and steam_appid.txt must be in
  chapter3_windows), the RELAY server (knightfights_server.zip, 5-letter codes), or PRACTICE against bots. While you are
  in a room the cold place is its lobby: everyone walks around it as their skin (no party following, the way to the
  original Knight encounter closed); the sign is the room's page.
  Skills (keys changeable in MORE OPTIONS > KEYBINDS): hold C to charge your gauge (the TP bar) and draw skills, tap Z to
  pick the next skill and hold Z to use the picked one, D puts it in the HOLD slot (and back), press S to hold your breath (a toggle since build 50;
  your SOUL moves faster, as in the fights), F quick settings, V the other SOULs on / off, Q / E the TARGETING mode, A or
  1-8 a target (CHECK), T or \ the chat (ENTER too in a match; ENTER or \ sends); X is the game's own slow walk. The battle's FIGHT / ACT menu and party box
  never come up online.
  Build 47: SOUL colours, the other SOULs very see-through (OPACITY slider 0-100%), SPECTATE MATCH from the room,
  watching cameras, and Kaizo Knight no longer cutting HP online.
  Build 48: the other SOULs really shown (70%, their colours, no rings), SOUL SETTINGS in five rows with a colour page,
  CHAT, TARGETING with SHARDS (Tetris 99 style), the Knight's Roaring at the final two and after 3 minutes, and a SOUL that
  breaks like Chapter 3's GAME OVER (yours followed by the GAME OVER over the battle, which goes on).
  Build 49: the other SOULs and the bots really on screen in the real arena (positions relative to the battle's camera),
  smart bots with DUMMY ... PERFECT and sliders (the room page's BOTS row), the build stamp on the sign's menu, the F3
  DEBUG OVERLAY (and knightfights_debug.log), OTHER SOUL OPACITY 15-100%, CONFIG > RESET MOD SETTINGS.
  Build 50: the attack skills are the Roaring Knights' real attacks (their own sprites, telegraphs and sounds, the
  sender's colour), five new items from Kaizo, Elecknight, Thorn and the Violet Knight, the TP bar as the skill meter,
  the SHIELD in blue on your HP bar, Hold Breath as a toggle, Shadow Crystal shards, the Twin Knight moving round the box
  and using the Knights' real attacks (bursting stars, tracking and falling swords), no HUD over a knight's Roaring, and
  bots that get through the Roaring like a player.
  Also: FLOWERY (Chapter 5) as a party member of his OWN (character 5 - his own hero, stats, gear and golden HP bar, not
  Noelle's slot; his moves built from his own Chapter 5 fight, F-Action, voice clips; every knight), song lyrics for Flower
  Man and the new Raise Up Your Bat, your SKIN kept after closing the menu, practice with no bots.
  For modders: custom party members are one registry entry each (knight_cc_register in the hub's code, cc50.gml); the game's
  battle code reaches them through it (technique ids 16-39, gear ids 30-35, one shared hero object).
  113 room settings (19 of them mutators, 11 targeting), 9 presets, 3 custom slots, settings codes.
  Everything is explained in DRBR_ONLINE_GUIDE.txt (including what to do when Steam rooms do not work).
  Online fights are not recorded. Your own spells, equipment and stats are put back after the match.

Spell notes:
  Kris starts with ACT, X-Slash and Red Buster. In the fight, Kris's command opens a magic list with an ACT
  entry plus their spells. X-Slash: two slashes 14 frames apart, 62 TP. Red Buster / Dual Heal / Permafrost /
  Heatwave are Kris's SOUL powers: Kris shines their SOUL on Susie / Ralsei / Noelle / Ralsei, who performs it
  with their own stats; the partner's command that turn is used up. FireShock (Chapter 5, Ralsei by default,
  anyone can pick it; build 37: about 60% stronger, 2.1x the Ice Shock number for the caster's stats, 2.5x on
  Kaizo, 2.8x on Violet), Frostfire (Ralsei and Noelle together). Weird Route moves: RUDER BUSTER, ICESTORM,
  FIRESTORM (above). Damage numbers are estimates.
  Shadow Mantle (build 37): it protects and draws hits for the member who actually wears it, in any slot
  (the game's knight code checked Kris's armor for slot 1, Susie's for slot 2 and Ralsei's for slot 3).
  Thorn Knight's max-HP erosion now hits whoever was hit, Noelle included (her floor is 50).

Damage:
  With fewer than three party slots the fights scale (ESTIMATE, never play-tested): duo deals x1.5 and takes
  x0.85, solo deals x3 and takes x0.7. The full trio is unchanged. Clones of one character share one HP bar,
  so each hit is split between the clone slots. Every hit on the knight goes through one filter (party scaling,
  then the pacing above); tuning lives in knight_scale_factors and knight_dmg_filter.

Knight Rush plays the five scored knights in order (or shuffled). The whole run is recorded, not each fight.
HP recovery between fights follows RUSH HEALING; TP resets; items carry. After a win the CLEARED box shows for
about a second and the next knight starts by itself (Abandon Rush is still selectable, or press Backspace).

CYAN KNIGHT IS A JOKE FIGHT. It is never part of Knight Rush or Random, has no No-Hit mode, and nothing from it
is recorded. It is labelled JOKE FIGHT on its card and during the fight.

After a fight: Rematch / Reroll (when random) / Change settings / Return to Hub / Continue story (the story
result is only written when you choose Continue story) / Fight stats (build 41). Tag Team and Attack Remix have
no Continue story. A failed No-Hit or Time limit shows Retry / Change settings / Return to Hub. A new best time,
least damage or first clear is announced in the results box.

Records are stored in knight_hub.ini in the game's save folder (with knight_hub.bak as the last good copy).
A damaged file is replaced by a fresh one and the old one is kept as knight_hub.bad.

Known limits (honest list):
  - PRACTICE exists for every fight. Kaizo Knight uses the mod's own picker; the others get a picker added by
    this hub (Left/Right choose an attack, Z starts it, MENU toggles HoldBreath and ends a running attack).
    The hub-made pickers are NOT part of the original mods and have only been run in a simulator.
  - No Healing blocks heals from the party; scripted HP changes inside a knight's own fight code are not blocked.
  - Some hit sources may not be seen by No-Hit if the fight code bypasses the game's damage routine.
  - Duplicate party members share ONE HP bar. Their status boxes animate separately.
  - Naming a preset needs a keyboard (ENTER confirms); on a controller, confirm keeps the suggested name.
  - The new rules, the pacing numbers and the new menus were checked in a simulator and by rendering the menus
    with the game's own fonts and sprites, NOT by playing the real game.
  - Build 41: TAG TEAM and ATTACK REMIX put several knight fights' code into one battle (one knight runs at a time,
    the others wait switched off). Build 41 crashed in the real game while making the second knight (Violet Knight's
    setup read a value only its own arena cutscene sets). Build 42 fixes that: those values are put in place before a
    knight is made, the arena cutscene and the other room objects always run the code of the fight that made them, and
    the simulator now has the room's real objects in every lineup test and fails on such reads instead of filling them
    in. This is still the biggest change in a long time and it has only been run in a simulator:
    every pair (36, the same knight twice included), knock-outs, the end of the battle and the Remix with every
    knight were checked there, but the real game may still show things a simulator cannot (a knight drawn in the
    wrong place for a frame, a sound or effect of one knight still running when the other steps in). If a Tag Team or
    Remix battle misbehaves, the single fights are not affected by it. Tell me which pair and what happened.
  - START AT / REPEAT, the fight stats, the hotkeys and the music fades are simulator-tested only. The fades use
    the game's own volume fade; how they sound has not been heard.
  - Build 45, KNIGHT FIGHTS ONLINE: rebuilt from scratch and tested only in the emulator that runs the mod's real code
    (several emulated games in one match over a simulated network with lag, loss and jitter; the real relay server;
    kf_steam.dll's own code against a PRETEND Steam). It has NOT run in the real game and NOT on real Steam yet - see
    TESTING_REPORT.txt for exactly what was and was not tested, and DRBR_ONLINE_GUIDE.txt for the known issues
    (Steam shows "Spacewar"; accepting an invite while the game is closed starts Spacewar; no Steam avatars; attacks that
    aim, aim at your own SOUL). Try PRACTICE first, then a room with a friend; if anything crashes, send the error text.
  - Build 46: the two build 45 crashes you sent are fixed and the keys changed (see BUILD 46 below and TESTING_REPORT.txt).
    The fixes were proven in the emulator - which now also runs Chapter 3's own battle controller under the online match
    and the code taken back out of the built data.win - not in the real game; build 46 has not been played yet.
  - Build 47: tested in the same emulator (several games in one match, the real relay server, Chapter 3's own cold place
    with Kris, the party and the Knight encounter's trigger running their own code) - not in the real game and not on
    real Steam; build 47 has not been played yet (TESTING_REPORT.txt, BUILD 47).
  - Build 48: tested the same way (three games in one targeted match over the simulated network, practice with bots, the
    Roaring of every knight run as a cycle, the pictures of the new HUD) - not in the real game, not on real Steam
    (TESTING_REPORT.txt, BUILD 48).
  - Build 49: tested the same way, and for the first time with each emulated game's camera where the real arena's is
    (the reason builds 47-48 showed no other SOULs and no moving bots in the real game: see BUILD 49 below) - not in the
    real game, not on real Steam (TESTING_REPORT.txt, BUILD 49).
  - Build 50: tested the same way (every item sent between two emulated games for every knight, the Knight's own fight
    checked unchanged in both, the bots dodging the new items, the party panel and the TP bar drawn with the game's
    fonts and sprites) - not in the real game, not on real Steam (TESTING_REPORT.txt, BUILD 50).

BUILD 26: FireShock keeps Ralsei in place and has a trail/spark effect, FireShock damage matches Ice Shock, and all Knight Hub menus use the game's own menu text size with auto-fitting panels.

BUILD 27: Ice Shock halved (x0.5), FireShock = 1.3x Ice Shock and always above Noelle's Ice Shock. Numbers are estimates - tell me how they feel.

BUILD 28: SOUL SHOCK is now PERMAFROST. New: HEATWAVE (Kris shines their SOUL on Ralsei, blue FireShock), FROSTFIRE (Ralsei or Noelle, Ice Shock + FireShock together), Dual Heal for Ralsei + Noelle without Kris, stronger FireShock on Kaizo/Violet, WEIRD STATS is saved with your settings, and a Thorn Knight leave-fight crash is fixed. Damage numbers are estimates; the blue fire has not been seen in the real game.

BUILD 29: partners no longer stay stuck in the ACT pose after Dual Heal / SOUL spells / Frostfire.
BUILD 29 also: Dual Heal / Frostfire work when the party has duplicates (e.g. Ralsei, Noelle, Ralsei).

BUILD 30: a downed duplicate party member can no longer pick a command.

BUILD 31: Frostfire costs 22% TP and has an ice+fire graphic; Heatwave costs 50%; Permafrost/Heatwave work with Kris in any slot.

BUILD 34: every attack object now uses each variant's own knight / bullet art (the cone fix of build 33 only covered the cone); variants no longer share one copy of an object when their art differs.

BUILD 35: menus rebuilt to DELTARUNE's own menu layout (KNIGHT / PARTY / POWER / RULES / CONFIG), per-fight CREDITS pages, new rules TWIN KNIGHT, DARKNESS, HYPER SPEED, THORNS and TIME LIMIT, fight pacing so no knight skips the end of its attack list, cleaner results boxes (new records announced).

BUILD 36: CONFIG > LOADOUTS - BASE / MAXED / DUAL MOVES for every party (trios, duos, solos) and TRIPLE (x3) loadouts; MAXED gives each member their own moves; one Shadow Mantle per setup (Susie first).

BUILD 37: WEIRD ROUTE on every fight and every party (Kris-less scenes in Violet Knight, a lost member in the knights without a Side B, Susie's RudeBuster in Kaizo), crash fix for Violet Knight without Kris (scr_moveheart), THORNS no longer feeds on the ThornRing drain, Thorn Knight wears down Noelle's max HP too, Shadow Mantle works in any slot, FireShock about 60% stronger, Susie no longer talks when she is not in the party (practice included), Noelle's lines fixed (her own faces and speech bubbles, no split lines), a Violet Side B clear is now recorded as a win.

BUILD 38: party speech bubbles open on the correct side (to the right of the member), Ralsei goes back to his normal stance after his lines, HOLDBREATH for Susie / Ralsei / Noelle when Kris is not in the party, INFINITE HP option, the Weird Route by party order (bottom first, top never; Kris can be taken), the survivors' talk with Susie first, RUDER BUSTER (replaces RED BUSTER), ICESTORM and FIRESTORM, the last member parries the Knight, DOUBLE (x2) loadouts.
BUILD 39: no more MISS from the fight pacing (Violet Knight and the others): hits past the schedule ease off smoothly (35% down to 5%) instead of stopping at the gate, Violet Side B shows damage after the Roaring (the Knight still stays at 8% until the finisher), the Weird Route scenes come before an early Roaring, Ralsei keeps his own (hatless) sprites in the Violet parry / power-up scene instead of switching to his Chapter 1 hat sprites, and when Susie is not in the fight Ralsei or Noelle say her lines in their own words (Noelle as the Angel on a Weird Route save; her N-Action too).
BUILD 40: Ralsei's stand-in lines rewritten in character (gentle and pleading, never demanding), Noelle's follow Susie's steps more closely, and the Angel's (Weird Route) are melodramatic, her N-Action too.
BUILD 41: TAG TEAM (two knights in one battle, taking turns, each with its own HP bar, attacks and Roaring; knock one out and the other takes over), ATTACK REMIX (a random knight and attack every turn, Normal Knight finale), PRACTICE START AT / REPEAT from any attack (CONFIG > PRACTICE, Z for the attack list), HOTKEYS (R restarts, hold TAB to fast-forward), FIGHT STATS after every fight, the Weird Route "learned" messages (FIRESTORM / ICESTORM ...) get one box each instead of running out of the box, and cleaner music in Violet Knight's Side B (fade out at the blow, the Side B song fades in).
BUILD 42: fixes the Tag Team / Attack Remix crash when the second knight was made ("obj_ch3_PTB02.nokaizo not set before reading it"), Attack Remix never includes the Cyan joke fight any more and lets you switch knights on and off (Z on ATTACK REMIX), and the arena cutscene and the other room objects keep running the code of the fight that made them while another knight is in front.
BUILD 43: KNIGHT FIGHTS ONLINE (KNIGHT page > ONLINE): a battle royale for up to 8 players with rooms and codes on a small relay server (knightfights_server.zip), or PRACTICE against bots with no server; the Attack Remix knight switches work again (they were stored as a number type the game read back as 0, so every knight always looked ON).
BUILD 44: fixes the build 43 crash as soon as you reached the Knight Hub ("Variable <unknown_object>.lq not set before reading it" in kfo_local_run): a function of the online code had the same name as the variable that holds the online state, and GameMaker treats a function as a global variable of the same name, so the game read the function instead of the state. The online code also no longer relies on how this GameMaker version hands out socket and buffer ids, and never uses the built-in name "id" for its own data. Everyone in a room needs build 44 (a build 43 game is refused).
BUILD 45: KNIGHT FIGHTS ONLINE rebuilt as one shared battle royale: every player gets the same knight, attack and attack randomness at the same moment from one match timeline (the knights' attack code draws its random numbers from a per-attack stream), seven synchronized switching modes, five stages, final two, sudden death, spectating, skills with a gauge (charge / use / hold / Hold Breath), 97 room settings (19 mutators) with presets, custom slots and settings codes, Steam rooms (app 480: host, 7-letter codes, browse, invites, version and full-room checks, host migration) through the new kf_steam.dll, the cold place as the room's lobby with every player walking around it, a battle HUD that fits 640x480, desync detection and recovery, and the host's checks on impossible numbers. The Cyan Knight is never online and unchanged offline. Also fixed: a crash in the hub's START box with START AT / REPEAT set to a late attack and RANDOM KNIGHT on (the random knight's attack list was shorter; Random Knight now starts START AT / REPEAT over at the first attack). Installer: putting the original data.win back no longer deletes the three Steam files (PLAY_KNIGHT_HUB.bat does that step on its way from an older build, which left the ONLINE page saying kf_steam.dll is missing).
BUILD 46: fixes the two KNIGHT FIGHTS ONLINE crashes of build 45. (1) "Variable Index [3] out of range [3] - global.char" in obj_battlecontroller: the battle's own command menu (FIGHT / ACT / ITEM / SPARE / DEFEND) was still running under the online match, so the match keys moved and pressed it (the menu sounds you kept hearing) and a FIGHT or ACT choice with a one-member party left it reading a fourth party slot; the menu now never opens in an online match (offline battles are unchanged). (2) "trying to index a variable which is not an array" in kbr_list_shuffle (Rotating Slash): the compiler the mod is built with turns GameMaker's ds_list accessor into a plain array read; it now uses ds_list_find_value / ds_list_set, the same fix went into the bots' hit check, and a build check refuses those accessors everywhere. New keys: S = Hold Breath (X stays the game's slow walk), tap Z = pick the next skill, hold Z = use the picked one, A = the HOLD slot (kept), and KEYBINDS (MORE OPTIONS or the room) to change every match key; no menu sounds while you play; the "+5 for five clean seconds" gauge bonus is gone; TAB never fast-forwards an online match. Everyone in a room needs build 46.

BUILD 47: KNIGHT FIGHTS ONLINE. Kaizo Knight never lowers HP online any more (its HP scene that cut max HP above 200, its arena raising Noelle to 120, and the knights' own damage cuts after the online damage table - Kaizo's half damage on Noelle, one attack's 66%, DEFEND, element resistance; Thorn Knight's max-HP erosion too): online the room's HP rules are the only ones, offline every fight is unchanged, and the same hit now takes the same HP from every skin. SOUL colours (MORE OPTIONS > SOUL APPEARANCE: presets including cyan, RGB, a colour code, outline, highlight) seen by everyone; SOUL VISIBILITY (the others' SOULs very see-through by default, an OPACITY slider 0-100% in 5% steps, V switches them off / on in a match, no names under SOULs unless switched on, colour modes, shape markers); SPECTATE MATCH from the room and watching cameras (FOLLOW, FULL ARENA, AUTO, ZOOM) with a watching card and MATCH STATS; QUICK SETTINGS (Q) in a match with SFX / music volume; MATCH VIEW (reduced shake - a shake never moves an online bullet now - reduced flashing, notices, match info, network stats); the room's page with colours, statuses, pings, COPY CODE, CONNECTION HELP, rematch votes and up to 4 watch places; the cold place without party followers, every player in their own skin, the original Knight encounter closed by a wall and its own trigger while you are in a room; Hold Breath as in the fights (a faster SOUL); seven new fight songs plus the game's own Flower Man, offline and online, with credits; the battle's party box no longer pops up online. Everyone in a room needs build 47.

BUILD 48: KNIGHT FIGHTS ONLINE. SHOW OTHER SOULS now really shows the other players' SOULs: they were drawn with the GPU's fog (a colour fill that depends on depth), which the hub's controller - drawn at depth -99000 - never got, so only the rings around them were visible; every SOUL is now a white SOUL picture tinted with its colour, 70% for the others by default, yours always solid, and every ring / halo / marker circle around SOULs is gone. SOUL SETTINGS has five rows (SHOW OTHER SOULS, SOUL COLOR with its own page - nine presets, RGB, hex, OUTLINE and its colour, a preview -, SOUL NAMES, OTHER SOUL OPACITY, HIGHLIGHT MY SOUL). CHAT in rooms, the cold place, matches and while watching (T / ENTER, ESC, TAB, the wheel, /mute). TARGETING: seven modes (CHAOS, PROCEED, BIG SHOT, DEFEND, CHECK, PACIFY, ROARING) decide where your attack skills go; sends start around their target and hurt anyone but the sender, tinted in the sender's colour; Shadow Crystal SHARDS for knockouts (1 + half the victim's) raise send strength; OUTNUMBERED BONUS; threads, the "!", TIRED, callouts; the host can turn it all off (the UNTARGETED preset). New keys: HOLD SLOT D, QUICK SETTINGS F (Q / E / A / 1-8 for targeting; controller LB / RB, right stick; Hold Breath LT, HOLD slot RT). The Roaring: the first attack of the final two and the first after 3 minutes are the Roaring of that moment's knight (any knight; the Violet Knight's forced phase-4 pick and the Supercharged Knight's phase 5 after its Roaring are fixed for this). Breaking SOULs crack and shatter as in Chapter 3's GAME OVER; yours is followed by the GAME OVER over the battle (which goes on), then you watch. KNIGHTMARE is renamed (song by Ann); twelve new songs (knight_hub_music2.zip), Guardian (the game's own titan_battle.ogg) and RANDOM; Z on FIGHT SONG / MUSIC opens a song list with every title and artist. Bots now really use their attack skills. Offline: the Normal Knight's WEIRD ROUTE no longer takes a party member. Everyone in a room needs build 48.
BUILD 51: KNIGHT FIGHTS ONLINE - A CLEANER MATCH SCREEN AND HOW TO PLAY. The TARGETING modes have plain names (RANDOM, LOW HP, CRYSTALS, REVENGE, CHOOSE, TIRED, EVERYONE - the same seven modes doing exactly what they did) on one slim strip: who you target on the left, the modes in the middle, your Shadow Crystals and how many target you (!) on the right; a mode's one-line description shows for 2 seconds when you change it; the key hints moved to the TAB box. Your skill slots are staggered diamonds floating off the top-left corner, each with a picture of what the skill does made from the game's own art (the Knight's sword bullets, red slash, stars, diamonds, teeth, the SOUL in colours, the battle menu's shield), MAX (Full Heal) a green plus; the TP bar sits a little lower to make room. Everyone (bots too) starts with exactly one MAX, and MAX now always fills to full HP. The other players are small cards (SOUL colour, name, crystals, connection, HP bar; a yellow edge = you target them, red = they target you). The feed shows 3 lines and each send once (it used to show twice). Knight changes, stages, the final two and sudden death get a big animated announcement with a new line each. NEW: HOW TO PLAY on the sign's ONLINE page - a step-by-step lesson in a practice match: the Knight waits while it shows you the screen, the TP bar, charging, using and holding skills, MAX and the seven targeting modes, then attacks only for the dodge, graze and attack lessons, and it ends with a tour of the menus (hosting, joining, settings, keys, chat). Steps you do move on by themselves. The ONLINE page is shorter (relay options and settings under MORE...). The party's HP panel sits at the very bottom online, with the targeting strip, the feed and the announcements just above it, clear of the battle box. Your SOUL keeps your colour in the Roaring. If you go out without being hit, the results now say why and knightfights_debug.log records the moment. Everyone in a room needs build 51. BUILD 51 UPDATE 3: four new skills - DARKNESS (red, mid: the target's screen goes dark but a circle around their SOUL for 5 seconds; the sender's Shadow Crystals make the circle smaller), LOCK (red, full: one of the target's skills is padlocked for 6 seconds), LIFESTEAL (green, mid: for 10 seconds a quarter of the damage your sends deal heals you) and DETERMINATION (green, full, once a match: for 15 seconds a hit that would put you out leaves you at 1 HP). Bots use and feel them too. Effects on you show as small timer chips under your skills. HOW TO PLAY is longer (22 steps in 8 lessons: moving, slow walk and Hold Breath included, plus a DARKNESS demo), types its text out, points at what it talks about, and sits under the battle box. The room settings use the menu's normal big font, on ten plain pages (BASICS, KNIGHTS, DIFFICULTY, SKILLS, SKILL LIST, TARGETING, MODIFIERS, ENDGAME, ADVANCED, PRESETS) with short names and plain descriptions; the mutators are now MODIFIERS with simpler explanations. Online song lyrics sit just above the targeting strip. Everyone in a room should have this update. BUILD 51 UPDATE 4: two online-only skins - BERDLY and AQUA (their real walking frames in the room, their real battle idles facing right in the battle, their dialogue faces on the ONLINE page - Aqua's is her knife - and their own colours; only a look: they play as Kris underneath, same HP and SOUL; never in the hub's own game). An online-only skin's name is in the HP panel in the battle-name lettering. Watching a player now shows their battle: your hidden SOUL sits on theirs and every attack skill sent at them is built in your game too, from the same seed. CHANGE NAME in the room (or /name in the chat) works mid-match. Chat messages pop up over players' heads in the room. Seven new coloured presets (THORN GARDEN, STORM FRONT, VIOLET DREAM, SKILL BRAWL, ONE HIT, PARTY, LAST STAND). The KNIGHT page is a carousel: < > the knights, the MODE strip (KNIGHT RUSH, RANDOM, TAG TEAM, ATTACK REMIX) and ONLINE under it; the chapter pages with only planned bosses are hidden for now. SKINS.txt explains how to add a skin. BUILD 51 UPDATE 9 - DRBR: the online battle royale is now DRBR - DELTARUNE BATTLE ROYALE (the ONLINE page, the window title in a room, HOW TO PLAY, these docs). Five bosses besides the knights: JEVIL (Chapter 1), GERSON (Chapter 4, GREEN SOUL: the arrows turn your shield), FLOWERY (Chapter 5, ORANGE SOUL: hold Z, let go to dash), SPAMTON NEO (Chapter 2, YELLOW SOUL: Z shoots, hold for a BIG SHOT) and PINK (Chapter 5, PURPLE SOUL: lanes) - each the game's own fight from your own chapter files, its turn order, pieces, music, background and lines; your SOUL changes only in your own game for that boss's attacks. WHO FIGHTS (the boss preset), each boss's ON / OFF row, SENDS (CURRENT BOSS / ALL ENABLED / one family) and the presets JEVIL, ALL BOSSES, GERSON, FLOWERY, SPAMTON, PINK in the room's settings. 31 new attack skills made from the bosses' own pieces (Gerson 6, Flowery 7, Spamton NEO 6, Pink 6, with Jevil's 6), built only in the target's game and kept dodgeable; an INCOMING list of what is coming at you. A new BOSSES page (ONLINE > BOSSES and the room) with each boss's look, chapter, SOUL, sends and music, and a practice match against one. Seven new online-only skins (Chapter 5's Seth, Orange, Green, Yellow, Blue; Pink; Chapter 2's small Spamton) and a SKINS page with groups and a walking preview; skins are cosmetic online. Every menu and the match screen checked at 640 x 480 (the room page, KEYBINDS, FIND ROOMS, the settings, the results, the top of the match screen, the network line and the watching lens fixed); the mouse wheel scrolls the menus' lists. Fixed: the "obj_collidebullet.destroyonhit" crash when a Jevil piece touched your SOUL. Everyone in a room needs this update.

BUILD 50: KNIGHT FIGHTS ONLINE. The attack skills players send each other are the Roaring Knights' real attacks, made only in the target's game from the Knights' own attack objects with their own animations, telegraphs and sounds (quieter when several come at once), tinted in the sender's colour: Sword and Flurry are tracking swords, Diamond Storm Kaizo's diagonal diamond rows, Streamline the Splitters' teeth, Ring and Star Burst the pointing stars bursting into starchildren, Weird Circle Kaizo's Rising Abyss, Knightmare the Spinning Slashes (three rounds of the rotating slash's markers and slashes). New items, drawn only when their knight is in the match: Crescent Slash and Sword Rain (Kaizo), Thunder Lines (Elecknight), Fountain Split (Thorn), Diamond Eruption (Violet). The charge and item system is unchanged (gauge, costs, pools, draws, slots, keys, damage per hit). The sent objects are kept apart from the Knight's own (the Knight's fight does not change), use their own random numbers, never touch the turn timer and are cleaned up completely. The TP bar is the one skill meter (the game's own TP bar art): a slanted white line at the draw cost, orange below it and gold above, white flashing and MAX at 100, the red section showing what a draw takes, YOU DREW A SKILL! beside it. SHIELD shows in blue on your HP bar (with a blue +N, a break when it breaks) and on the others' bars in the player list. Hold Breath is a toggle. Shards use the Shadow Crystal graphic. The Twin Knight flies round the box to its attacks and plays their animations, and attacks with the Knights' real objects (pointing stars that burst into starchildren, tracking swords, falling swords) with the Knight's warp, afterimages and sounds, see-through. The online HUD steps aside while a knight's Roaring is on screen. The bots keep to the screen in a Roaring, are hit by stars only on the stars' precise test and are pulled by the Roaring like a player's SOUL. Everyone in a room needs build 50.

BUILD 49: KNIGHT FIGHTS ONLINE. The other players' SOULs and the bots now show in the real game. The hub's fight is Chapter 3's own Knight encounter far into the cold place (the arena camera at x 2063 and more); build 48 kept every SOUL position inside x -200..1000, so the others' SOULs were drawn at x 1000, off screen, and its bots took the real battle box (x 2000+) for "no box", so they were never placed, never moved and never drawn. Positions now travel relative to the battle's camera and are drawn at that place plus each game's own camera; the room-x limits are gone. Earlier tests ran the battle with the camera at 0, where neither problem shows; the new test runs with the real arena's camera and fails on build 48's code. SMART BOTS: same rules as the players (SOUL, hitbox, speed, damage, gauge, skills, TARGETING), dodging from the real bullets' boxes and motion with a look-ahead (17 moves incl. half speed, edges and corners avoided), healing when low and safe, SHIELD / REFLECT, sends with a TARGETING mode for the moment (PROCEED, DEFEND, BIG SHOT, PACIFY, ROARING), a BOT tag in the player list; difficulty DUMMY / EASY / NORMAL / HARD / EXPERT / PERFECT per bot or for the room, and seven sliders (REACTION TIME, PREDICTION, MISTAKES, PRECISION, HEALING, CHARGING, AGGRESSION) on the room page's new BOTS row (host). A build stamp (KNIGHT HUB V2 - BUILD 49 - date) at the bottom right of the sign's menu; F3 turns on a DEBUG OVERLAY (room, camera, every SOUL and bot with its position, depth, drawn or not and why, alpha, a coloured square at each) that also writes knightfights_debug.log in %LOCALAPPDATA%\DELTARUNE. OTHER SOUL OPACITY 15-100% (lower saved values are raised); CONFIG > RESET MOD SETTINGS. CHAT opens with T or \ and sends with \ (a new CHAT key in KEYBINDS) - ENTER no longer opens or sends it. Everyone in a room needs build 49.
BUILD 50 (KF SONG PACK): FIGHT SONG has IT DOESN'T END HERE by DIGITAL DESCENDANT (Nullscape Vol. 3) with its timed lyrics and credit. Its files come in knight_hub_kfsongs.zip, which the installer unpacks into the kfsongs folder next to data.win (chapter3_windows\kfsongs). Without that folder the song shows NOT FOUND and the knight's own music plays. Keep KF_SONG_CREDITS.txt with the mod.
