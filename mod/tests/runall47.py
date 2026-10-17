"""Run every t_*.py (2 at a time), log each to logs/<name>.log, summarise exit code / tracebacks / FAIL lines."""
import subprocess, sys, os, glob, time
from concurrent.futures import ThreadPoolExecutor
os.chdir('/home/claude/work/tests')
LOGD = os.environ.get('RA_LOGS', 'logs47')
os.makedirs(LOGD, exist_ok=True)
only = sys.argv[1:]
tests = sorted(glob.glob('t_*.py'))
if only:
    tests = [t for t in tests if any(o in t for o in only)]
skip = {'t_lineup.py', 't_sprmon.py', 't_defspr.py', 't_twin.py', 't_weird.py', 't_elecunl.py',
        # build 45: the long multi-game / network runs (with their own arguments, see TESTING_REPORT): run separately
        't_br_multi.py', 't_br_desync.py', 't_br_practice.py', 't_net_repeat45.py',
        # build 47: the multi-game fixture runs (several games for minutes each, the long Kaizo ledger, the overworld soak):
        # run separately with their own arguments (TESTING_REPORT build 47)
        't_view47.py', 't_ow47.py', 't_kaizo47.py',
        # build 49: the bots' dodging runs (four knights, minutes each): run separately (t_bots49.py; presets / skills too)
        't_bots49.py',
        # build 50: the real-attack sends for every knight (two games, minutes each) and the bots with them: run separately
        't_sent50.py', 't_sent50_bots.py'}  # long sweeps / scenario tests with arguments: run separately


def run(t):
    if t in skip and not only:
        return t, 'SKIP', 0, ''
    t0 = time.time()
    log = LOGD + '/' + t[:-3] + '.log'
    with open(log, 'w') as f:
        try:
            p = subprocess.run(['python3', t], stdout=f, stderr=subprocess.STDOUT, timeout=5400)
            rc = p.returncode
        except subprocess.TimeoutExpired:
            rc = 'TIMEOUT'
    txt = open(log, errors='replace').read()
    bad = [l for l in txt.splitlines() if ('FAIL' in l and 'FAILED' not in l.upper().replace('FAIL', '', 0)) or l.startswith('Traceback') or 'Error' in l[:40]]
    return t, rc, round(time.time() - t0), '\n    '.join(bad[:6])


with ThreadPoolExecutor(int(os.environ.get('RA_WORKERS', '2'))) as ex:
    for t, rc, dt, bad in ex.map(run, tests):
        print('%-24s rc=%s %ss %s' % (t, rc, dt, ('\n    ' + bad) if bad else ''), flush=True)
print('ALL DONE')
