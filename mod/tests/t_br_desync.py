"""Build 45 (P1): desyncs put into running games on purpose, and how fast the room puts them right. Three emulated games in one
battle royale over the simulated network; every 150 frames one of the two players' games gets one incident:
  seed   its timeline is made from a wrong seed (a corrupted state)  -> the host sees the wrong cycle signature -> resync
  ft     it believes the final two started (a stray message)          -> wrong signatures -> resync
  hp     its HP above its max HP                                      -> the host's check -> fix
  mhp    its max HP above the room's                                  -> fix
  gauge  its skill gauge at 250                                       -> fix (or its own clamp)
  stall  it freezes for 40 frames (a lag spike: no frames, time runs) -> it skips what it cannot arm in time, then plays on
Recovered = the game's numbers are right again (its timeline's next cycles equal the host's; HP / max HP / gauge in range);
for a stall, the time until it runs the same cycle as the host again. Also: no cycle twice, the same knight / attack / seed /
tick for every cycle all games ran. Usage: python3 t_br_desync.py [frames (4500)] [profile (normal)] [seed (5150)]"""
import sys, os, json, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from br_multi import *

FR = int(sys.argv[1]) if len(sys.argv) > 1 else 4500
PROF = sys.argv[2] if len(sys.argv) > 2 else 'normal'
SEED = int(sys.argv[3]) if len(sys.argv) > 3 else 5150
KINDS = ['seed', 'hp', 'ft', 'gauge', 'stall', 'mhp']
t0 = time.time()
net, sims = make_room(3, PROF, SEED, setx='_s.rush = 1; _s.mhp = 300; _s.sd = 0; _s.dmul = 25;')
H = sims[0]
print('room up', round(time.time() - t0, 1), 's', flush=True)

INJ = {'seed': 'var _M = global.kfo.M; _M.tl = kbr_tl_new(_M.seed + 77, _M.set);',
       'ft': 'var _M = global.kfo.M; kbr_tl_set_ft(_M.tl, max(_M.R.k, _M.R.arm_k) + 1);',
       'hp': 'global.hp[kbr_char()] = global.maxhp[kbr_char()] + 500;',
       'mhp': 'global.maxhp[kbr_char()] = 999; global.hp[kbr_char()] = 999;',
       'gauge': 'global.kfo.M.g = 250;'}
SIGS = ('var _M = global.kfo.M; var _k = max(_M.R.k, _M.R.arm_k); global.SG = [];'
        'for (var _j = 0; _j < 3; _j++) array_push(global.SG, kbr_tl_sig(kbr_tl_get(_M.tl, global.TK + _j)));')
incidents = []
open_inc = []
stalls = []


def host_k():
    return int(H.eval('max(global.kfo.M.R.k, global.kfo.M.R.arm_k)'))


def recovered(inc, s):
    k = inc['kind']
    if k in ('seed', 'ft'):
        hk = host_k() + 1
        H.run('global.TK = %d;' % hk)
        s.run('global.TK = %d;' % hk)
        H.run(SIGS)
        s.run(SIGS)
        return H.py(H.eval('global.SG')) == s.py(s.eval('global.SG'))
    if k == 'hp':
        return s.eval('global.hp[kbr_char()] <= global.maxhp[kbr_char()]')
    if k == 'mhp':
        return s.eval('global.maxhp[kbr_char()] <= kbr_match().eff.mhp && global.hp[kbr_char()] <= global.maxhp[kbr_char()]')
    if k == 'gauge':
        return s.eval('global.kfo.M.g <= 100')
    if k == 'stall':
        if inc['f_end'] is None:
            return False
        a = s.py(s.eval('[global.kfo.M.R.ph, global.kfo.M.R.k, global.kfo.M.R.arm_k]'))
        b = H.py(H.eval('[global.kfo.M.R.ph, global.kfo.M.R.k, global.kfo.M.R.arm_k]'))
        return a[0] == 'run' and b[0] == 'run' and a[1] == b[1]
    return False


def stall_fn(cid, f):
    for inc in stalls:
        if inc['cid'] == cid and inc['f'] <= f < inc['f'] + 40:
            return True
    return False


def on_frame(f, sims, prev):
    # HP back up every second (nobody falls in this test) - not for a game with an open HP incident
    if f % 30 == 0:
        busy = set(i['cid'] for i in open_inc if i['kind'] in ('hp', 'mhp'))
        for i, s in enumerate(sims):
            if (i + 1) not in busy:
                s.run('if (is_struct(global.kfo.M) && !global.kfo.M.out) global.hp[kbr_char()] = global.maxhp[kbr_char()];')
    # a new incident every 150 frames from frame 300 (the match runs from about frame 120)
    if f >= 300 and (f - 300) % 150 == 0 and f < FR - 300:
        n = (f - 300) // 150
        kind = KINDS[n % len(KINDS)]
        cid = 2 + (n // len(KINDS) + n) % 2
        s = sims[cid - 1]
        inc = {'n': n, 'kind': kind, 'cid': cid, 'f': f, 'ms': net.t, 'fix_f': None, 'fix_ms': None, 'f_end': None, 'rs0': s.eval('global.kfo.M.resyncs')}
        if kind == 'stall':
            stalls.append(inc)
        else:
            s.run(INJ[kind])
        incidents.append(inc)
        open_inc.append(inc)
    for inc in list(open_inc):
        s = sims[inc['cid'] - 1]
        if inc['kind'] == 'stall':
            if inc['f_end'] is None and f >= inc['f'] + 40:
                inc['f_end'] = f
                inc['ms_end'] = net.t
            if inc['f_end'] is None:
                continue
        if recovered(inc, s):
            inc['fix_f'] = f
            inc['fix_ms'] = net.t
            inc['secs'] = round((net.t - (inc['ms_end'] if inc['kind'] == 'stall' else inc['ms'])) / 1000.0, 2)
            open_inc.remove(inc)
    if f % 600 == 0:
        print('frame', f, 'incidents', len(incidents), 'open', [(i['kind'], i['cid']) for i in open_inc], '%.0fs' % (time.time() - t0), flush=True)


rec = run(net, sims, FR, 'diff', on_frame=on_frame, wall=float(os.environ.get('WALL', '1500')), stall=stall_fn)
cmp = compare(rec, 3)
errs = {c: rec[c]['errors'] for c in (1, 2, 3) if rec[c]['errors']}
state_inc = [i for i in incidents if i['kind'] != 'stall']
fixed2 = [i for i in state_inc if i['fix_f'] is not None and i['secs'] <= 2.0]
unfixed = [i for i in incidents if i['fix_f'] is None]
st_inc = [i for i in incidents if i['kind'] == 'stall']
by = {}
for i in incidents:
    b = by.setdefault(i['kind'], {'n': 0, 'fixed': 0, 'max_s': 0.0})
    b['n'] += 1
    if i['fix_f'] is not None:
        b['fixed'] += 1
        b['max_s'] = max(b['max_s'], i['secs'])
res = {'args': sys.argv[1:], 'incidents': len(incidents), 'state_incidents': len(state_inc), 'state_fixed_2s': len(fixed2),
       'pct_2s': round(100.0 * len(fixed2) / max(1, len(state_inc)), 1), 'unfixed': [(i['kind'], i['cid'], i['f']) for i in unfixed], 'by_kind': by,
       'stall_rejoin_s': [i.get('secs') for i in st_inc], 'logic_bad': cmp['logic_bad'][:5], 'dupes': cmp['dupes'], 'cycles_all': cmp['cycles_all'],
       'errors': {c: e[:1] for c, e in errs.items()}, 'host': {'desyncs': H.eval('global.kfo.H.desyncs'), 'fixes': H.eval('global.kfo.H.fixes'),
       'clockfix': H.eval('global.kfo.H.clockfix')}, 'resyncs': [s.eval('global.kfo.M.resyncs') for s in sims], 'skipped': [s.eval('global.kfo.M.R.skipped') for s in sims],
       'wall': round(time.time() - t0, 1)}
ok = (not errs and not cmp['logic_bad'] and cmp['dupes'] == 0 and not unfixed and res['pct_2s'] >= 99.0)
res['pass'] = ok
os.makedirs('/tmp/claude-0/br45', exist_ok=True)
json.dump({'res': res, 'incidents': incidents}, open('/tmp/claude-0/br45/desync_%s_%d.json' % (PROF, SEED), 'w'), indent=1)
print('RESULT', 'PASS' if ok else 'FAIL', json.dumps(res), flush=True)
sys.exit(0 if ok else 1)  # build 46: a FAIL is a failing exit code too (runall)
