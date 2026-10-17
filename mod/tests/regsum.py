"""Summarize the regression: every job's exit code, time and summary line (logs53/reg/status.txt), grouped."""
import re, sys
S = '/home/claude/work/tests/logs53/reg/status.txt'
rows = []
for l in open(S):
    l = l.rstrip('\n')
    if not l or l == 'ALLDONE':
        continue
    m = re.match(r'(\S+) rc=(-?\d+) (\d+)s \| (.*)$', l)
    if m:
        rows.append((m.group(1), int(m.group(2)), int(m.group(3)), m.group(4)))
ok = [r for r in rows if r[1] == 0]
bad = [r for r in rows if r[1] != 0]
print('jobs %d: %d exit 0, %d not' % (len(rows), len(ok), len(bad)))
for r in bad:
    print('  NOT OK %-24s rc=%d %5ds %s' % r)
if '-v' in sys.argv:
    for r in ok:
        print('  ok     %-24s rc=%d %5ds %s' % r)
