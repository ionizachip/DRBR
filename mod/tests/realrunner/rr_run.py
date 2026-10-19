"""DRBR real-runner tests (1.0.4): run a test build (rr_build.py) in the REAL game runner - the player's own DELTARUNE.exe -
under Wine with software rendering (Xvfb + llvmpipe), in DRBR mode (the provided starting save, drbr_data), with an
autotest.cfg; collect what the hook wrote (kat_log.txt, the screenshots) into an output folder.
The runner is the player's own copy (never part of DRBR or this repository): RR_RUNNER = its folder (DELTARUNE.exe,
chapter3_windows/audiogroup1.dat).
Usage: python3 rr_run.py <test.win> <cfg text file> <out dir> [timeout s]"""
import os, sys, shutil, subprocess, time, glob

RUNNER = os.environ.get('RR_RUNNER', '/home/claude/rr/game')
PFX = os.environ.get('RR_PREFIX', '/home/claude/rr/pfx')
# the release payload: the provided starting save, the multiplayer DLLs (RR_PAYLOAD; the newest built release by default)
PAYLOAD = os.environ.get('RR_PAYLOAD') or sorted(glob.glob('/home/claude/drbr/dist/1.0.*/payload'), key=lambda p: [int(x) for x in p.split('/')[-2].split('.')])[-1]
SAVE = os.path.join(PFX, 'drive_c/users/root/AppData/Local/DELTARUNE')
# seconds without a new log line before the run counts as stopped (an error box in the game; the log grows at every phase)
STALL = int(os.environ.get('RR_STALL', '600'))
CFG = ('# DRBR save profile - written by DRBR Launcher, read by the game when it starts. Do not edit by hand.\r\nschema_version=1\r\n'
       'profile=drbr_default\r\nstarting_location=room_dw_snow_zone\r\nstarting_room_id=30108\r\nstarting_plot=320\r\nsave_template_version=1\r\n'
       'save_template_sha256=fa956269ee3ee98e7df04356bb575e3afd5455a538bb5568b2ac931fdb0aa082\r\nstart_mode=template\r\nmigration_version=1\r\n')


def main():
    win, cfg, out = sys.argv[1], sys.argv[2], sys.argv[3]
    tmo = int(sys.argv[4]) if len(sys.argv) > 4 else 900
    g = os.path.join(out, 'game')
    if os.path.exists(out):
        shutil.rmtree(out)
    os.makedirs(os.path.join(g, 'chapter3_windows', 'drbr_data'))
    shutil.copy(os.path.join(RUNNER, 'DELTARUNE.exe'), g)
    shutil.copy(os.path.join(RUNNER, 'options.ini'), g)
    c3 = os.path.join(g, 'chapter3_windows')
    shutil.copy(os.path.join(RUNNER, 'chapter3_windows', 'audiogroup1.dat'), c3)
    shutil.copy(os.path.join(RUNNER, 'chapter3_windows', 'options.ini'), c3)
    for f in ('kf_steam.dll', 'steam_api64.dll', 'steam_appid.txt'):
        shutil.copy(os.path.join(PAYLOAD, f), c3)
    shutil.copy(win, os.path.join(c3, 'data.win'))
    shutil.copy(os.path.join(PAYLOAD, 'start_filech3'), os.path.join(c3, 'drbr_data'))
    open(os.path.join(c3, 'drbr_data', 'drbr_profile.cfg'), 'w', newline='').write(CFG)
    shutil.copy(cfg, os.path.join(c3, 'drbr_data', 'autotest.cfg'))
    for p in glob.glob(os.path.join(g, '**'), recursive=True):
        os.chmod(p, 0o755 if os.path.isdir(p) else 0o644)
    # a clean save area: the hook's log and pictures, and DRBR's own files from an earlier run
    if os.path.isdir(SAVE):
        shutil.rmtree(SAVE)
    env = dict(os.environ, WINEPREFIX=PFX, WINEDEBUG='err+all,fixme-all', LIBGL_ALWAYS_SOFTWARE='1', GALLIUM_DRIVER='llvmpipe', DISPLAY=':79')
    xv = subprocess.Popen(['Xvfb', ':79', '-screen', '0', '1024x768x24'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(2)
    lg = open(os.path.join(out, 'runner.log'), 'w')
    gp = subprocess.Popen(['wine', 'DELTARUNE.exe', '-game', 'chapter3_windows\\data.win'], cwd=g, env=env, stdout=lg, stderr=subprocess.STDOUT)
    t0 = time.time()
    last_n = -1
    last_t = time.time()
    why = 'timeout'
    log = os.path.join(SAVE, 'kat_log.txt')
    while time.time() - t0 < tmo:
        time.sleep(3)
        if gp.poll() is not None:
            why = 'game ended'
            break
        n = os.path.getsize(log) if os.path.exists(log) else 0
        if n != last_n:
            last_n = n
            last_t = time.time()
        elif time.time() - last_t > STALL:
            why = 'no progress for %d s' % STALL
            subprocess.run(['import', '-window', 'root', os.path.join(out, 'stalled.png')], env=env)
            break
    subprocess.run(['import', '-window', 'root', os.path.join(out, 'last_screen.png')], env=env, stderr=subprocess.DEVNULL)
    if gp.poll() is None:
        gp.kill()
    subprocess.run(['wineserver', '-k'], env=env)
    xv.kill()
    lg.close()
    for p in glob.glob(os.path.join(SAVE, 'kat_*')):
        shutil.copy(p, out)
    shutil.rmtree(g, ignore_errors=True)
    print('real runner: %s after %ds; log %s' % (why, time.time() - t0, 'yes' if os.path.exists(os.path.join(out, 'kat_log.txt')) else 'NO'))


if __name__ == '__main__':
    main()
