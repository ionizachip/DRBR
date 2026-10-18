"""DRBR update 9: the full regression queue - every job in its own process, two at a time, each with its time cap.
Each job's output goes to logs53/reg/<name>.log; a line per finished job (exit code, seconds, its last summary line) to
logs53/reg/status.txt. Usage: python3 regq.py jobs.txt [workers]"""
import sys, os, subprocess, time, threading, shlex

JOBS = [l.strip() for l in open(sys.argv[1]) if l.strip() and not l.startswith('#')]
W = int(sys.argv[2]) if len(sys.argv) > 2 else 2
OUT = '/home/claude/work/tests/logs101b/'
lock = threading.Lock()
q = list(JOBS)


def last_line(p):
    try:
        ls = [l for l in open(p, errors='replace').read().splitlines() if l.strip()]
    except Exception:
        return ''
    for l in reversed(ls):
        if any(k in l for k in ('checks', 'tests', 'fails', 'PASS', 'FAIL', 'passed', 'failed', 'ok', 'Error', 'Traceback')):
            return l[:220]
    return ls[-1][:220] if ls else ''


def worker():
    while True:
        with lock:
            if not q:
                return
            job = q.pop(0)
        # "<name> <cap seconds> <command ...>"
        name, cap, cmd = job.split(' ', 2)
        log = OUT + name + '.log'
        t0 = time.time()
        with open(log, 'w') as f:
            try:
                rc = subprocess.call(['timeout', cap, 'bash', '-c', 'cd /home/claude/work/tests && ' + cmd], stdout=f, stderr=subprocess.STDOUT)
            except Exception as e:
                rc = -1
        with lock:
            with open(OUT + 'status.txt', 'a') as s:
                s.write('%s rc=%d %ds | %s\n' % (name, rc, time.time() - t0, last_line(log)))


ts = [threading.Thread(target=worker) for _ in range(W)]
for t in ts:
    t.start()
for t in ts:
    t.join()
with open(OUT + 'status.txt', 'a') as s:
    s.write('ALLDONE\n')
