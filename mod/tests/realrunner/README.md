# Real-runner tests (DRBR 1.0.4)

These run DRBR's built game code in **the real DELTARUNE game program** (`DELTARUNE.exe`, GameMaker's own runner) instead of
the GML emulator - under Wine with software rendering (Xvfb + Mesa llvmpipe), in DRBR mode (the provided starting save).

They exist because the emulator once missed a bug the real game had: Jevil's Devilsknives read `centerx` / `centery`,
which Chapter 3's compiled code turns into its own `centerx()` / `centery()` functions; the emulator read the variables.

- `kat_hook.gml` - the autotest hook. `rr_build.py` adds it to a **copy** of the merged code in a sandbox and builds a
  private test `data.win` with the release's own `build.csx`. The hook is never in a release build.
  It starts a practice match, forces the attacks listed in `drbr_data/autotest.cfg`, logs every attack's pieces
  (`kat_log.txt`) and saves screenshots (`screen_save`).
- `rr_run.py` - copies the runner and the test build into a fresh game folder and runs it until the hook ends the game.
- `rr_check.py` - the checks on the log (`dk`, `old`, `send`, `sweep`).

The game program is **the player's own copy** (point `RR_RUNNER` at a folder with `DELTARUNE.exe` and
`chapter3_windows/audiogroup1.dat`); it is never part of DRBR or this repository. Results are labelled REAL RUNNER (Wine):
the real runner and the real build, but Wine instead of Windows and a test hook in the build.

    python3 rr_build.py /path/to/build/merged /tmp/t.win
    printf 'kn=6\nseq=3,11\nshots=30,90\ndetail=1\n' > dk.cfg
    RR_RUNNER=/path/to/DELTARUNE python3 rr_run.py /tmp/t.win dk.cfg /tmp/out_dk
    python3 rr_check.py dk /tmp/out_dk 2
