"""DRBR 1.0.4: the checks on what the real-runner autotest wrote (rr_run.py output folders).
  dk  <out>  : the Devilsknife (3) / Devilsknife Swing (11) run with detail=1 - every frame of every one of them: four
               Devilsknives, the middle they swing round = the box's middle, every one on the screen; the Swing's red blade
               on the screen; no piece far off the screen
  old <out>  : the same run on 1.0.3's code - the Devilsknives far off the screen (the bug, in the real game)
  send <out> : the DEVILSKNIFE skill (sent at this game): its four Devilsknives round the box's middle, on the screen
  sweep <out>: every attack listed ran to its end (no error stopped the game) and no piece was far off the screen
  ran <out>  : every attack listed ran to its end (no error stopped the game); the pieces far off the screen are listed (the
               other bosses park some there by design - compare with the emulator)
Usage: python3 rr_check.py dk|old|send|sweep <out dir> [expected attacks]"""
import sys, re, os

FAILS = []
N = [0]


def ok(c, msg):
    N[0] += 1
    print(('ok   ' if c else 'FAIL ') + msg, flush=True)
    if not c:
        FAILS.append(msg)
    return c


def frames(log):
    """the detail lines: [(af, [scythes], [blades], box, cam)]"""
    out = []
    cur = None
    for l in open(log, encoding='utf8', errors='replace'):
        if l.startswith('PH ') and '-> run' in l:
            cur = []
            out.append(cur)
            continue
        m = re.match(r'^F\d+ run af (\d+) ', l)
        if not m or cur is None:
            continue
        parts = l.rstrip('\n').split(' | ')
        sc, rb, box, cam = [], [], None, None
        for p in parts[1:]:
            if p.startswith('S '):
                q = re.match(r'S (-?\d+),(-?\d+) a([\d.]+) .* kx(\d+) c (?:(-?\d+),(-?\d+)|none)', p)
                if q:
                    sc.append((int(q.group(1)), int(q.group(2)), float(q.group(3)), int(q.group(4)),
                               int(q.group(5)) if q.group(5) else None, int(q.group(6)) if q.group(6) else None))
            elif p.startswith('RB '):
                q = re.match(r'RB (-?\d+),(-?\d+) a([\d.]+) spr_jv_joker_scythebody', p)
                if q:
                    rb.append((int(q.group(1)), int(q.group(2)), float(q.group(3))))
            elif p.startswith('BOX '):
                q = re.match(r'BOX (-?\d+),(-?\d+)', p)
                box = (int(q.group(1)), int(q.group(2)))
            elif p.startswith('cam '):
                q = re.match(r'cam (-?[\d.]+),(-?[\d.]+)', p)
                cam = (float(q.group(1)), float(q.group(2)))
        cur.append((int(m.group(1)), sc, rb, box, cam))
    return out


def on(x, y, cam, m=0):
    return cam[0] - m <= x <= cam[0] + 640 + m and cam[1] - m <= y <= cam[1] + 480 + m


def summaries(log):
    return [l.rstrip('\n') for l in open(log, encoding='utf8', errors='replace') if l.startswith('ATK ')]


def main():
    what, out = sys.argv[1], sys.argv[2]
    log = os.path.join(out, 'kat_log.txt')
    if not ok(os.path.exists(log), 'the real runner wrote its log (%s)' % log):
        return
    done = any(l.startswith('KAT done') for l in open(log, encoding='utf8', errors='replace'))
    ok(done, 'the game ran its attacks to the end (no error stopped it)')
    if what in ('dk', 'old', 'send'):
        att = frames(log)
        for k, fr in enumerate(att):
            sm = summaries(log)
            name = sm[k].split(' | ')[0] if k < len(sm) else 'attack %d' % (k + 1)
            sel = [(af, [s for s in sc if (s[3] > 0) == (what == 'send')], rb, box, cam) for af, sc, rb, box, cam in fr]
            sel = [f for f in sel if f[1]]
            if what == 'send' and not sel:
                continue
            n4 = max((len(f[1]) for f in sel), default=0)
            if what == 'old':
                far = [s for f in sel for s in f[1] if not on(s[0], s[1], f[4], 1000)]
                allk = [s for f in sel for s in f[1]]
                ok(n4 == 4 and allk and len(far) == len(allk), '%s (1.0.3): four Devilsknives, every one far off the screen every frame - the bug '
                   '(%d of %d positions more than 1000 px out; e.g. %s)' % (name, len(far), len(allk), (far[0][:2] if far else None)))
                continue
            cen = [f[3] is not None and s[4] == f[3][0] and s[5] == f[3][1] for f in sel for s in f[1]]
            vis = [on(s[0], s[1], f[4]) for f in sel for s in f[1] if s[2] > 0]
            ok(n4 == 4, '%s: four Devilsknives (%d)' % (name, n4))
            ok(cen and all(cen), '%s: they swing round the box\'s middle, every frame (%d of %d)' % (name, sum(cen), len(cen)))
            ok(vis and all(vis), '%s: every one on the screen every frame it shows (%d of %d)' % (name, sum(vis), len(vis)))
            if ' ai 11 ' in name + ' ':
                bl = [b for f in fr for b in f[2] if b[2] > 0]
                ok(len(bl) > 20 and all(on(b[0], b[1], f[4], 120) for f in fr for b in f[2]), '%s: the red blade on the screen beside the box (%d frames)' % (name, len(bl)))
    if what == 'ran':
        sm = summaries(log)
        want = int(sys.argv[3]) if len(sys.argv) > 3 else len(sm)
        ok(len(sm) == want, '%d attacks ran to their end (%d expected)' % (len(sm), want))
        for s in sm:
            far = sorted(set(re.findall(r'(obj_\w+)@', s.split(' | ')[-1])))
            print('     %s: far off the screen: %s' % (s.split(' | ')[0], ' '.join(far) or 'nothing'))
    if what in ('dk', 'sweep', 'send'):
        sm = summaries(log)
        want = int(sys.argv[3]) if len(sys.argv) > 3 else len(sm)
        ok(len(sm) == want, '%d attacks ran (%d expected)' % (len(sm), want))
        for s in sm:
            m = re.search(r'far frames (\d+) max off-screen (\d+)', s)
            ok(m and int(m.group(1)) == 0, '%s: no piece more than 1000 px off the screen (furthest %s px)' % (s.split(' | ')[0], m.group(2) if m else '?'))
    print('real runner %s: %d checks, %d failed' % (what, N[0], len(FAILS)))
    for f in FAILS:
        print('  -', f)


if __name__ == '__main__':
    main()
    sys.exit(1 if FAILS else 0)
