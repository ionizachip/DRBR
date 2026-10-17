"""Build 45 (P0 / P1): the shared timeline on its own - the part every game works out by itself from the host's seed and
settings. Checks:
  P0  the Cyan Knight can never be picked online: by construction (no online id runs it), by the scheduler's own check
      (global.kbr_assert_n never counts), and over 1,000 generated room configurations x 10 cycles (presets, random settings,
      bad values, tampered imported codes) - 0 Cyan, disabled knights never come;
  P1  1,000+ knight transitions over the seven switching modes, every one checked against the mode's rule (who comes next,
      the entrance and breath ticks, the attack pool, no repeats where the room forbids them), weights and Knightmare's
      growth measured; 10,000 consecutive cycles worked out twice (and jumping ahead) give the same cycles; the final-two
      event gives the same cycles whenever a game hears of it.
Usage: python3 t_br_timeline.py [configs (1000)]"""
import sys, os, json, random, time, math, base64
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from harness import *

NCFG = int(sys.argv[1]) if len(sys.argv) > 1 else 1000
FAILS = []
N = [0]
INFO = {}


def ok(c, msg):
    N[0] += 1
    if not c:
        FAILS.append(msg)
        print('FAIL', msg, flush=True)


def J(sim, e):
    return sim.py(sim.eval(e))


sim = make_sim()
sim.run('knight_store_load(); global.knight_cfg = knight_cfg_default(); knight_ensure_ctrl();')
t_start = time.time()

# ---------------------------------------------------------------- P0: by construction
regs = [(i, J(sim, 'knight_reg(%d).name' % i), J(sim, 'knight_reg(%d).joke' % i)) for i in range(int(sim.eval('knight_count()')))]
cyan = [i for i, n, j in regs if j]
ok(len(cyan) == 1 and regs[cyan[0]][1] == 'Cyan Knight', 'the hub has exactly one joke fight, the Cyan Knight (%r)' % regs)
CY = cyan[0]
for k in range(6):
    ok(J(sim, 'kbr_ok_valid(%d)' % k), 'online knight %d is valid' % k)
    ok(J(sim, 'kbr_reg_of(%d)' % k) != CY, 'online knight %d does not run the Cyan Knight' % k)
for bad in ('-1', '6', '7', '99', '2.5', '"5"', 'undefined', '-0.5'):
    ok(not J(sim, 'kbr_ok_valid(%s)' % bad), 'kbr_ok_valid(%s) is false' % bad)
ok(J(sim, 'kbr_ok_count()') == 6, 'six online knights')
names = [J(sim, 'kbr_ok_name(%d)' % k) for k in range(6)]
ok(names == ['Normal Knight', 'Kaizo Knight', 'Elecknight', 'Violet Knight', 'Thorn Knight', 'Knightmare'], 'online roster names %r' % names)

# ---------------------------------------------------------------- P0: 1,000 generated configurations
R = random.Random(45045)
MUTS = J(sim, 'kfo_mut_ids()')


def gen_cfg(i):
    """a room configuration as it could reach a game: a preset, random settings, bad values, or a tampered code"""
    kind = i % 5
    d = {}
    if kind == 0:
        return {'preset': R.randrange(8)}
    pool = [0, 1, 2, 3, 4, 5]
    if kind == 1:
        d['kn'] = R.sample(pool, R.randint(1, 6))
    elif kind == 2:
        # bad knight lists: out of range, the Cyan Knight's hub number, fractions, strings, booleans, nothing
        junk = [CY, CY, 6, 7, -1, 99, 2.5, '5', 'cyan', True, None, 1e9]
        d['kn'] = R.sample(pool, R.randint(0, 3)) + R.sample(junk, R.randint(1, 4))
    elif kind == 3:
        d['kn'] = [CY] * R.randint(1, 3)
    else:
        d['kn'] = R.sample(pool, R.randint(1, 6)) + ([CY] if R.random() < 0.5 else [])
    d['open'] = R.choice([0, 1, 2, 3, 4, 5, CY, 6, -1])
    d['rush'] = R.randrange(7)
    d['kw'] = [R.randint(0, 9) for _ in range(6)]
    for k, lo, hi in (('stay', 1, 8), ('trans', 0, 90), ('gap', 0, 30), ('arep', 0, 5), ('recent', 0, 3), ('ramp', 0, 3), ('maxst', 0, 4),
                      ('twin', 0, 2), ('hyper', 0, 2), ('cdn', 3, 10), ('fin', 1, 5)):
        if R.random() < 0.6:
            d[k] = R.randint(lo, hi)
    for k in ('rep', 'speedup', 'hard', 'sd', 'sdfast', 'ft', 'fthyper'):
        if R.random() < 0.5:
            d[k] = R.randint(0, 1)
    for m in MUTS:
        if R.random() < 0.12:
            d[m] = 1
    if R.random() < 0.15:
        d['rush'] = R.choice([-5, 9, 3.7, 'x'])
    return d


t = time.time()
cyan_hits = 0
off_roster = 0
sel = 0
bad_cfgs = []
imports = 0
for i in range(NCFG):
    d = gen_cfg(i)
    seed = R.randrange(1, 2 ** 31)
    if 'preset' in d:
        mk = 'var _s = kfo_preset_apply(%d);' % d['preset']
    elif i % 4 == 1:
        # the config goes through an export code, tampered: the knight list swapped for the raw one (Cyan's number and all)
        js = json.dumps(d)
        mk = ('var _s0 = kfo_set_clean(json_parse(%s)); var _txt = kfo_set_to_text(_s0); var _raw = json_parse(base64_decode(string_delete(_txt, 1, 5)));'
              '_raw.kn = json_parse(%s).kn; var _s = kfo_set_from_text("KF45:" + base64_encode(json_stringify(_raw)));') % (json.dumps(js), json.dumps(js))
        imports += 1
    else:
        mk = 'var _s = kfo_set_clean(json_parse(%s));' % json.dumps(json.dumps(d))
    sim.run(mk + 'global.TE = kbr_eff(_s); global.TL = kbr_tl_new(%d, _s); global.TR = [];'
            'for (var _k = 0; _k < 10; _k++) { var _c = kbr_tl_get(global.TL, _k); array_push(global.TR, [_c.ok, _c.reg, knight_reg(_c.reg).joke]); }'
            'global.TROS = kbr_set_roster(global.TE);' % seed)
    rows = J(sim, 'global.TR')
    ros = J(sim, 'global.TROS')
    for okk, reg, joke in rows:
        sel += 1
        if joke or reg == CY:
            cyan_hits += 1
            bad_cfgs.append(d)
        if okk not in ros:
            off_roster += 1
            bad_cfgs.append(('off', d, okk, ros))
ok(sel == NCFG * 10, '%d knight selections made' % sel)
ok(cyan_hits == 0, 'the Cyan Knight came 0 times in %d online selections (got %d)' % (sel, cyan_hits))
ok(off_roster == 0, 'a knight the room turned off never came (%d did: %r)' % (off_roster, bad_cfgs[:2]))
ok(J(sim, 'global.kbr_assert_n') == 0, 'the scheduler\'s own Cyan / roster check never had to step in (%d)' % J(sim, 'global.kbr_assert_n'))
INFO['p0'] = {'configs': NCFG, 'selections': sel, 'cyan': cyan_hits, 'off_roster': off_roster, 'tampered_imports': imports, 'secs': round(time.time() - t, 1)}
print('P0 configs', INFO['p0'], flush=True)

# ---------------------------------------------------------------- P1: 1,000+ transitions over the seven modes
# every mode with all six knights; per mode as many cycles as it takes to get 160 knight changes
MODES = {0: 'CLASSIC', 1: 'KNIGHT RUSH', 2: 'RAPID', 3: 'RANDOM', 4: 'PROGRESSIVE', 5: 'WEIGHTED', 6: 'NIGHTMARE'}
total_tr = 0
mode_info = {}
for mode, mname in MODES.items():
    setx = {'kn': [0, 1, 2, 3, 4, 5], 'rush': mode, 'stay': 3, 'trans': 36, 'gap': 18, 'arep': 3, 'recent': 0, 'rep': 0, 'kw': [3, 3, 3, 3, 3, 2],
            'sd': 0, 'ramp': 1, 'maxst': 4}
    if mode == 5:
        setx['kw'] = [1, 6, 0, 3, 9, 2]
    sim.run('var _s = kfo_set_clean(json_parse(%s)); global.TL = kbr_tl_new(%d, _s); global.TC = [];'
            'var _sw = 0; var _k = 0; while (_sw < 160 && _k < 5000) { var _c = kbr_tl_get(global.TL, _k);'
            ' array_push(global.TC, { ok: _c.ok, ai: _c.ai, t0: _c.t0, t1: _c.t1, dur: _c.dur, tr: _c.tr, sw: _c.sw, st: _c.st, seed: _c.seed, sd: _c.sd, ft: _c.ft, roar: _c.roar });'
            ' if (_c.sw) _sw++; _k++; }' % (json.dumps(json.dumps(setx)), 777 + mode))
    cy = J(sim, 'global.TC')
    eff = J(sim, 'global.TL.set')
    bad = []
    runs = []
    run = 1
    for k in range(1, len(cy)):
        p, c = cy[k - 1], cy[k]
        sw = c['ok'] != p['ok']
        if sw != bool(c['sw']):
            bad.append((k, 'sw flag'))
        tr = (min(eff['trans'], 14) if (mode == 2 or c['ft'] or c['sd']) else eff['trans']) if sw else 0
        if c['tr'] != tr:
            bad.append((k, 'tr', c['tr'], tr))
        if c['t0'] != p['t1'] + eff['gap'] + tr:
            bad.append((k, 't0', c['t0'], p['t1'] + eff['gap'] + tr))
        if c['t1'] != c['t0'] + c['dur'] or c['dur'] <= 0:
            bad.append((k, 't1'))
        nxt = (p['ok'] + 1) % 6
        if mode in (1, 2) and c['ok'] != nxt:
            bad.append((k, 'order', p['ok'], c['ok']))
        if mode == 0:
            if sw and (run != 3 or c['ok'] != nxt):
                bad.append((k, 'classic run', run, p['ok'], c['ok']))
            if not sw and run >= 3:
                bad.append((k, 'classic stayed too long', run))
        if mode in (3, 5, 6) and not sw:
            bad.append((k, 'same knight twice (SAME KNIGHT TWICE is off)'))
        if mode == 5 and c['ok'] == 2:
            bad.append((k, 'weight 0 knight came'))
        if sw:
            runs.append(run)
            run = 1
        else:
            run += 1
    # the attack: from the knight's pool for the stage, never one of its last arep attacks (when it has enough)
    sim.run('global.TP = []; for (var _k = 0; _k < array_length(global.TL.cyc); _k++) { var _c = global.TL.cyc[_k];'
            ' var _pst = (_c.sd || global.TL.set.overlap) ? 3 : _c.st; array_push(global.TP, kbr_atk_pool(_c.reg, _pst, global.TL.set.hard)); }')
    pools = J(sim, 'global.TP')
    last = {}
    for k, c in enumerate(cy):
        reg = [0, 1, 2, 3, 4, 0][c['ok']]
        # build 48: the Roaring cycle (final two / 3 minutes in) uses the knight's own Roaring, outside the pool
        if c.get('roar'):
            if c['ai'] != J(sim, 'kbr_roar_ai(%d)' % reg):
                bad.append((k, 'roar cycle without the Roaring', c['ai']))
        elif c['ai'] not in pools[k]:
            bad.append((k, 'attack not in pool', c['ai']))
        h = last.setdefault(reg, [])
        first_classic = (mode == 0 and c['st'] == 0 and c['ok'] == 0)
        if not first_classic and len(pools[k]) > 3 and c['ai'] in h[-3:]:
            bad.append((k, 'attack repeated within 3', c['ai'], h[-3:]))
        h.append(c['ai'])
    ntr = sum(1 for c in cy if c['sw'])
    total_tr += ntr
    cnt = [sum(1 for c in cy if c['ok'] == x) for x in range(6)]
    mi = {'cycles': len(cy), 'transitions': ntr, 'bad': len(bad), 'per_knight': cnt}
    if mode == 3:
        # uniform over 6 with no repeats: chi-square against equal shares (5 degrees of freedom; 20.5 = p 0.001)
        e = len(cy) / 6.0
        chi = sum((x - e) ** 2 / e for x in cnt)
        mi['chi2'] = round(chi, 1)
        ok(chi < 20.5, 'RANDOM RUSH: every knight about as often (chi2 %.1f, %r)' % (chi, cnt))
    if mode == 5:
        # WEIGHTED with SAME KNIGHT TWICE off: compare with a simulation of the same rule (weights, the last one blocked)
        w = [1, 6, 0, 3, 9, 2]
        rr = random.Random(5)
        sim_cnt = [0] * 6
        prev = cy[0]['ok']
        for _ in range(200000):
            ww = [w[i] if i != prev else 0 for i in range(6)]
            x = rr.choices(range(6), ww)[0]
            sim_cnt[x] += 1
            prev = x
        exp = [s / 200000.0 * (len(cy) - 1) for s in sim_cnt]
        cnt1 = [sum(1 for c in cy[1:] if c['ok'] == x) for x in range(6)]
        chi = sum((cnt1[i] - exp[i]) ** 2 / exp[i] for i in range(6) if exp[i] > 0)
        mi['chi2'] = round(chi, 1)
        mi['expected'] = [round(x, 1) for x in exp]
        ok(chi < 18.5, 'WEIGHTED RUSH follows the weights (chi2 %.1f; got %r, expected %r)' % (chi, cnt1, mi['expected']))
        ok(cnt1[2] == 0, 'WEIGHTED RUSH: a knight with weight 0 never comes')
    if mode == 6:
        half = len(cy) // 2
        a = sum(1 for c in cy[:half] if c['ok'] == 5) / float(half)
        b = sum(1 for c in cy[half:] if c['ok'] == 5) / float(len(cy) - half)
        mi['knightmare_share'] = [round(a, 2), round(b, 2)]
        ok(b > a, 'NIGHTMARE RUSH: Knightmare comes more often later (%.2f -> %.2f)' % (a, b))
    if mode == 4:
        mi['runs'] = runs[:40]
        ok(all(runs[i] >= runs[i + 1] for i in range(len(runs) - 1)) and runs[-1] < runs[0], 'PROGRESSIVE: the knights stay for fewer attacks as the match goes on (%r)' % runs[:30])
    ok(not bad, '%s: every transition follows the mode (%d bad: %r)' % (mname, len(bad), bad[:4]))
    mode_info[mname] = mi
    print('mode', mname, mi, flush=True)
ok(total_tr >= 1000, '1,000+ knight transitions checked (%d)' % total_tr)
INFO['p1_transitions'] = {'total': total_tr, 'modes': mode_info}

# ---------------------------------------------------------------- P1: 10,000 consecutive cycles, the same every time
t = time.time()
SIG = ('global.TS = []; for (var _k = 0; _k < %d; _k++) array_push(global.TS, kbr_tl_sig(kbr_tl_get(global.TL, _k)));')
setc = {'kn': [0, 1, 2, 3, 4, 5], 'rush': 3, 'sd': 1, 'ramp': 2, 'm_storm': 1}
sim.run('global.TL = kbr_tl_new(424242, kfo_set_clean(json_parse(%s)));' % json.dumps(json.dumps(setc)) + SIG % 10000)
a = J(sim, 'global.TS')
sim2 = make_sim()
sim2.run('knight_store_load(); global.knight_cfg = knight_cfg_default(); knight_ensure_ctrl();')
# the other game: jumps to a late tick first (a game that joins late), then works the rest out
sim2.run('global.TL = kbr_tl_new(424242, kfo_set_clean(json_parse(%s))); var _late = kbr_tl_at(global.TL, 2000000);' % json.dumps(json.dumps(setc)) + SIG % 10000)
b = J(sim2, 'global.TS')
ok(len(a) == 10000 and a == b, '10,000 cycles: two games (one jumping ahead) work out the very same cycles')
ok(len(set(x.split(':')[3] for x in a)) == 10000, 'every one of the 10,000 cycles has its own attack seed')
t0s = [int(x.split(':')[4]) for x in a]
ok(all(t0s[i] < t0s[i + 1] for i in range(len(t0s) - 1)), 'the 10,000 start ticks only go up')
ok(J(sim, 'global.kbr_assert_n') == 0 and J(sim2, 'global.kbr_assert_n') == 0, 'no Cyan / roster correction in 20,000 cycles')
INFO['p1_cycles'] = {'cycles': len(a), 'secs': round(time.time() - t, 1), 'last_tick': t0s[-1], 'hours': round(t0s[-1] / 30.0 / 3600, 1)}
# every mode for 10,000 cycles: no Cyan, no step outside the roster
for mode in range(7):
    sim.run('global.TL = kbr_tl_new(%d, kfo_set_clean({ kn: [0, 1, 2, 3, 4, 5], rush: %d })); global.TB = 0; '
            'for (var _k = 0; _k < 10000; _k++) { var _c = kbr_tl_get(global.TL, _k); if (knight_reg(_c.reg).joke || !kbr_ok_valid(_c.ok)) global.TB++; }' % (99 + mode, mode))
    ok(J(sim, 'global.TB') == 0, 'mode %d: 10,000 cycles, never the Cyan Knight' % mode)
ok(J(sim, 'global.kbr_assert_n') == 0, 'no scheduler correction over 70,000 more cycles')

# ---------------------------------------------------------------- the final two: the same cycles whenever a game hears of it
sim.run('global.TA = kbr_tl_new(5150, kfo_set_clean({ rush: 1 })); kbr_tl_get(global.TA, 60); kbr_tl_set_ft(global.TA, 20);'
        'global.TB2 = kbr_tl_new(5150, kfo_set_clean({ rush: 1 })); kbr_tl_get(global.TB2, 5); kbr_tl_set_ft(global.TB2, 20);'
        'global.TC2 = kbr_tl_new(5150, kfo_set_clean({ rush: 1 })); kbr_tl_set_ft(global.TC2, 20);'
        'global.FA = []; global.FB = []; global.FC = []; for (var _k = 0; _k < 80; _k++) { array_push(global.FA, kbr_tl_sig(kbr_tl_get(global.TA, _k)));'
        ' array_push(global.FB, kbr_tl_sig(kbr_tl_get(global.TB2, _k))); array_push(global.FC, kbr_tl_sig(kbr_tl_get(global.TC2, _k))); }')
fa, fb, fc = J(sim, 'global.FA'), J(sim, 'global.FB'), J(sim, 'global.FC')
ok(fa == fb == fc, 'final two from cycle 20: the same cycles whether a game had made 61, 6 or 0 cycles before')
ok(all('F' in x for x in fa[20:]) and not any('F' in x for x in fa[:20]), 'final-two flag exactly from cycle 20')
sim.run('kbr_tl_set_ft(global.TA, 30); global.FA2 = kbr_tl_sig(kbr_tl_get(global.TA, 25));')
ok(J(sim, 'global.FA2') == fa[25], 'a later final-two message changes nothing (the first one counts)')

INFO['secs'] = round(time.time() - t_start, 1)
os.makedirs('/tmp/claude-0/br45', exist_ok=True)
json.dump({'checks': N[0], 'fails': FAILS, 'info': INFO}, open('/tmp/claude-0/br45/timeline.json', 'w'), indent=1)
print('timeline tests: %d checks, %d failed (%ss)' % (N[0], len(FAILS), INFO['secs']))
for f in FAILS:
    print('  -', f)
