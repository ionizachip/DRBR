"""Build 45 (P4): the room settings, presets and mutators on their own.
  - 1,000 generated valid configurations: cleaning keeps them as they are, JSON (the network) and the KF45 settings code
    (export / import) give them back exactly;
  - invalid values (out of range, off the step, wrong types, NaN, huge, arrays, structs) for every setting: always made valid;
  - every built-in preset 100 times: the same every time, valid as it is, its name kept, its own values in it;
  - the 3 custom slots: 100 save / load cycles exact; 100 restarts (the ini file carried into a new game) keep the player's
    options and the last room settings;
  - every mutator on its own does what it says in the settings a match plays with (kbr_eff), off does nothing; every pair
    of mutators gives valid settings and a timeline; the one-switching-mutator and GIANT/TINY rules hold;
  - every option can be stepped through its whole range with < > (always valid, the preset turns CUSTOM), the last knight
    and the last skill cannot be switched off, the opening knight follows the knights that are in;
  - every option the settings page shows is read by the game code somewhere (none is only for show).
Usage: python3 t_online_set45.py"""
import sys, os, json, random, math, re, glob
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from harness import *

FAILS = []
N = [0]


def ok(c, msg):
    N[0] += 1
    if not c:
        FAILS.append(msg)
        print('FAIL', msg, flush=True)


def eq(a, b, msg):
    ok(a == b, '%s (got %r want %r)' % (msg, a, b))


def J(sim, e):
    return sim.py(sim.eval(e))


def new_sim():
    s = make_sim()
    s.run('knight_store_load(); global.knight_cfg = knight_cfg_default(); knight_ensure_ctrl(); kfo_get();')
    return s


def gq(v):
    """a Python value as GML source"""
    return 'json_parse(%s)' % json.dumps(json.dumps(v))


sim = new_sim()
OPTS = J(sim, 'kfo_opts()')
NUMS = [o for o in OPTS if o['kind'] in ('num', 'enum', 'bool', 'mut')]
MUTS = J(sim, 'kfo_mut_ids()')
DEF = J(sim, 'kfo_set_default()')
R = random.Random(4545)


def valid_check(s, where):
    """every field of a cleaned settings struct inside the schema"""
    bad = []
    for o in NUMS:
        v = s.get(o['oid'])
        if not isinstance(v, (int, float)) or isinstance(v, bool) or not (o['lo'] <= v <= o['hi']):
            bad.append((o['oid'], v))
        elif o['st'] > 0 and abs(((v - o['lo']) / o['st']) - round((v - o['lo']) / o['st'])) > 1e-9:
            bad.append((o['oid'], v, 'step'))
    kn = s.get('kn')
    if not isinstance(kn, list) or not kn or any(k not in range(7) for k in kn) or kn != sorted(set(kn)):
        bad.append(('kn', kn))
    elif s.get('open') not in kn:
        bad.append(('open', s.get('open'), kn))
    kw = s.get('kw')
    if not isinstance(kw, list) or len(kw) != 7 or any(not (0 <= w <= 9) for w in kw):
        bad.append(('kw', kw))
    sk = s.get('skoff')
    # build 52: skills 1-31 (16 FULL HEAL has no switch; 26-31 Jevil's), 30 switches
    if not isinstance(sk, list) or any(not (1 <= x <= 31) or x == 16 for x in sk) or len(sk) >= 30:
        bad.append(('skoff', sk))
    if s.get('minp', 2) > s.get('maxp', 8):
        bad.append(('minp>maxp', s.get('minp'), s.get('maxp')))
    if s.get('m_giant') and s.get('m_tiny'):
        bad.append(('giant+tiny',))
    if sum(1 for m in ('m_rapid', 'm_roul', 'm_nmesc') if s.get(m)) > 1:
        bad.append(('two switching mutators',))
    if not any(s.get('tgm%d' % t, 1) for t in range(7)):
        bad.append(('every targeting mode off',))
    if not isinstance(s.get('pre'), str) or not (1 <= len(s['pre']) <= 16):
        bad.append(('pre', s.get('pre')))
    ok(not bad, '%s: valid settings (%r)' % (where, bad[:4]))
    return not bad


def rand_valid():
    s = {}
    for o in NUMS:
        steps = int(round((o['hi'] - o['lo']) / max(o['st'], 1e-9))) if o['st'] > 0 else 0
        s[o['oid']] = o['lo'] + R.randint(0, steps) * o['st'] if o['st'] > 0 else R.uniform(o['lo'], o['hi'])
    s['kn'] = sorted(R.sample(range(6), R.randint(1, 6)))
    s['open'] = R.choice(s['kn'])
    s['kw'] = [R.randint(0, 9) for _ in range(7)]
    s['skoff'] = sorted(R.sample(range(1, 16), R.randint(0, 8)))
    s['pre'] = R.choice(['CUSTOM', 'CLASSIC', 'MY ROOM', 'NIGHTMARE'])
    if s['minp'] > s['maxp']:
        s['minp'] = s['maxp']
    if s['m_giant'] and s['m_tiny']:
        s['m_tiny'] = 0
    sw = [m for m in ('m_rapid', 'm_roul', 'm_nmesc') if s[m]]
    for m in sw[1:]:
        s[m] = 0
    # build 48: at least one targeting mode stays on
    if not any(s.get('tgm%d' % t) for t in range(7)):
        s['tgm0'] = 1
    return s


# ---------------------------------------------------------------- defaults
valid_check(DEF, 'defaults')
eq(DEF['pre'], 'CLASSIC', 'the default settings are CLASSIC')
d0 = J(sim, 'kfo_preset_apply(0)')
eq(d0, DEF, 'CLASSIC preset = the defaults')

# ---------------------------------------------------------------- 1,000 round trips
rt_bad = []
for i in range(1000):
    s = rand_valid()
    sim.run('global.S0 = %s; global.S1 = kfo_set_clean(global.S0); global.S2 = kfo_set_clean(json_parse(json_stringify(global.S1)));'
            'global.T = kfo_set_to_text(global.S1); global.S3 = kfo_set_from_text(global.T); global.T2 = kfo_set_to_text(global.S3);' % gq(s))
    s1, s2, s3 = J(sim, 'global.S1'), J(sim, 'global.S2'), J(sim, 'global.S3')
    want = dict(s)
    want['pre'] = s['pre']
    if s1 != want:
        rt_bad.append(('clean changed a valid config', i, {k: (want.get(k), s1.get(k)) for k in set(want) | set(s1) if want.get(k) != s1.get(k)}))
    if s2 != s1:
        rt_bad.append(('json', i))
    w3 = dict(s1)
    w3['pre'] = 'CUSTOM'
    if s3 != w3:
        rt_bad.append(('code', i, {k: (w3.get(k), s3.get(k)) for k in set(w3) | set(s3) if w3.get(k) != s3.get(k)}))
    if not J(sim, 'string_pos("KF45:", global.T) == 1'):
        rt_bad.append(('code prefix', i))
ok(not rt_bad, '1,000 valid configurations: clean / JSON / settings code give them back exactly (%d bad: %r)' % (len(rt_bad), rt_bad[:3]))

# ---------------------------------------------------------------- invalid values
JUNK = [-1e9, 1e9, -1, 0.5, 2.5, 7.77, 'abc', '50', True, False, [1, 2], {'a': 1}, None]
inv_n = 0
for o in NUMS:
    for v in JUNK + [o['lo'] - 1, o['hi'] + 1, o['lo'] + o['st'] / 2.0 if o['st'] > 0 else o['lo']]:
        sim.run('global.S1 = kfo_set_clean(%s);' % gq({o['oid']: v}))
        s1 = J(sim, 'global.S1')
        inv_n += 1
        if not valid_check(s1, 'invalid %s = %r' % (o['oid'], v)):
            break
# NaN / infinity straight from GML
for o in NUMS[:12]:
    sim.run('var _s = {}; variable_struct_set(_s, "%s", NaN); global.S1 = kfo_set_clean(_s); var _t = {}; variable_struct_set(_t, "%s", infinity); global.S2 = kfo_set_clean(_t);' % (o['oid'], o['oid']))
    valid_check(J(sim, 'global.S1'), 'NaN %s' % o['oid'])
    valid_check(J(sim, 'global.S2'), 'infinity %s' % o['oid'])
    inv_n += 2
for kn in ([], [9], [-1, 6, 7], ['1', '2'], [2.5], [True], [None], 'all', 5, [5, 5, 5], [3, 1, 3, 0]):
    sim.run('global.S1 = kfo_set_clean(%s);' % gq({'kn': kn, 'open': 4}))
    s1 = J(sim, 'global.S1')
    valid_check(s1, 'kn %r' % (kn,))
    inv_n += 1
for kw in ([99, -5, 'x', None, 3.5, 2], [1], 'w', [None] * 9):
    sim.run('global.S1 = kfo_set_clean(%s);' % gq({'kw': kw}))
    valid_check(J(sim, 'global.S1'), 'kw %r' % (kw,))
    inv_n += 1
for sk in ([x for x in range(1, 32) if x != 16], [0, 16, -2, 3.5, 'x', 32], 'x', [1] * 30):
    sim.run('global.S1 = kfo_set_clean(%s);' % gq({'skoff': sk}))
    s1 = J(sim, 'global.S1')
    valid_check(s1, 'skoff %r' % (sk,))
    inv_n += 1
sim.run('global.S1 = kfo_set_clean(%s);' % gq({'skoff': [x for x in range(1, 32) if x != 16]}))
eq(J(sim, '[global.S1.skills, array_length(global.S1.skoff)]'), [0, 0], 'every skill off = SKILLS off')
for pre in ('', 'X' * 40, 'ééé', 'a"b', None, 5):
    sim.run('global.S1 = kfo_set_clean(%s);' % gq({'pre': pre}))
    valid_check(J(sim, 'global.S1'), 'pre %r' % (pre,))
    inv_n += 1
for bad in ('undefined', '5', '"text"', '[1,2,3]', 'noone'):
    sim.run('global.S1 = kfo_set_clean(%s);' % bad)
    eq(J(sim, 'global.S1'), DEF, 'kfo_set_clean(%s) = the defaults' % bad)
    inv_n += 1
for t in ('', 'KF45:', 'KF45:!!!!', 'KF44:' + 'e30=', 'hello', 'KF45:' + 'A' * 9000, 'KF45:WzEsMiwzXQ==', None):
    sim.run('global.S1 = kfo_set_from_text(%s);' % (gq(t) if t is not None else 'undefined'))
    ok(J(sim, 'is_undefined(global.S1)'), 'not a settings code: %r -> refused' % (t if t is None else t[:20]))
    inv_n += 1
print('invalid values tried:', inv_n, flush=True)

# ---------------------------------------------------------------- presets x 100
PRE = J(sim, 'kfo_presets()')
eq(PRE, ['CLASSIC', 'CASUAL', 'COMPETITIVE', 'HARDCORE', 'KNIGHT RUSH', 'KAIZO', 'CHAOS', 'NIGHTMARE', 'UNTARGETED', 'THORN GARDEN', 'STORM FRONT', 'VIOLET DREAM', 'SKILL BRAWL', 'ONE HIT', 'PARTY', 'LAST STAND', 'JEVIL', 'ALL BOSSES'], 'the built-in presets (build 52: 18)')
WANT = {1: {'mhp': 220, 'ramp': 0, 'hard': 0, 'bots': 3}, 2: {'ready': 1, 'cdn': 5}, 3: {'mhp': 100, 'dmul': 125, 'fullheal': 0},
        4: {'rush': 1, 'trans': 24}, 5: {'rush': 5, 'open': 1, 'mhp': 120}, 6: {'rush': 2, 'm_storm': 1, 'm_hyper': 1, 'm_rcost': 1},
        7: {'rush': 6, 'twin': 1, 'open': 5}, 9: {'rush': 5, 'open': 4}, 10: {'rush': 5, 'open': 2, 'hyper': 1},
        11: {'rush': 5, 'open': 3, 'ramp': 0}, 12: {'scost': 50, 'cdm': 50, 'g0': 50}, 13: {'m_ohko': 1, 'fullheal': 0, 'shp': 1},
        14: {'bots': 3, 'm_giant': 1, 'mhp': 220}, 15: {'m_lowhp': 1, 'm_sd0': 1}}
for i, name in enumerate(PRE):
    first = None
    same = True
    for rep in range(100):
        p = J(sim, 'kfo_preset_apply(%d)' % i)
        if first is None:
            first = p
        elif p != first:
            same = False
    ok(same, '%s: 100 loads give the same settings' % name)
    valid_check(first, 'preset %s' % name)
    eq(first['pre'], name, '%s: named' % name)
    eq(J(sim, 'kfo_set_clean(kfo_preset_apply(%d))' % i), first, '%s: valid as it is' % name)
    eq(J(sim, 'kfo_set_named(kfo_preset_apply(%d)).pre' % i), name, '%s: keeps its name while unchanged' % name)
    for k, v in WANT.get(i, {}).items():
        eq(first[k], v, '%s: %s' % (name, k))
    if i:
        sim.run('var _s = kfo_preset_apply(%d); _s.mhp = (_s.mhp == 150) ? 160 : 150; global.S1 = kfo_set_named(_s);' % i)
        eq(J(sim, 'global.S1.pre'), 'CUSTOM', '%s changed: CUSTOM' % name)

# ---------------------------------------------------------------- custom slots x 100, restarts x 100
cs_bad = 0
saved = {}
for i in range(100):
    s = rand_valid()
    slot = 1 + i % 3
    sim.run('kfo_custom_save(%d, kfo_set_clean(%s)); global.S1 = kfo_custom_load(%d);' % (slot, gq(s), slot))
    got = J(sim, 'global.S1')
    want = J(sim, 'kfo_set_clean(%s)' % gq(s))
    want['pre'] = 'CUSTOM %d' % slot
    saved[slot] = want
    if got != want:
        cs_bad += 1
ok(cs_bad == 0, '100 custom preset save / load cycles exact (%d bad)' % cs_bad)
eq(J(sim, '[kfo_custom_exists(1), kfo_custom_exists(2), kfo_custom_exists(3)]'), [True, True, True], 'the three slots are in use')
eq(J(sim, 'is_undefined(kfo_custom_load(4))'), True, 'slot 4 does not exist')
# restarts: the ini carried into a fresh game
rs_bad = []
for i in range(100):
    s = rand_valid()
    nm = ''.join(R.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz ') for _ in range(R.randint(1, 12))).strip() or 'X'
    sk, sop, nms, vis = R.randint(1, 4), 20 + 5 * R.randint(0, 16), R.randint(0, 1), R.randint(0, 2)
    sim.run('var _o = kfo_get(); _o.name = kfo_clean_name(%s); _o.skin = %d; _o.sop = %d; _o.names = %d; _o.vis = %d; _o.set = kfo_set_clean(%s); _o.srv = "10.0.0.%d"; _o.port = %d; _o.lastcode = "ABCDEFG"; kfo_ini_save();'
            % (gq(nm), sk, sop, nms, vis, gq(s), i % 250, 7000 + i))
    before = J(sim, '[kfo_get().name, kfo_get().skin, kfo_get().sop, kfo_get().names, kfo_get().vis, kfo_get().set, kfo_get().srv, kfo_get().port, kfo_get().lastcode]')
    s2 = make_sim()
    s2.fs.load(sim.fs.dump())
    s2.run('knight_store_load(); global.knight_cfg = knight_cfg_default(); knight_ensure_ctrl(); kfo_get();')
    after = J(s2, '[kfo_get().name, kfo_get().skin, kfo_get().sop, kfo_get().names, kfo_get().vis, kfo_get().set, kfo_get().srv, kfo_get().port, kfo_get().lastcode]')
    if after != before:
        rs_bad.append((i, [(a, b) for a, b in zip(before, after) if a != b][:2]))
    if i % 10 == 0:
        # the custom slots survive the restart too
        if J(s2, 'kfo_custom_load(1)') != saved[1]:
            rs_bad.append((i, 'custom 1'))
ok(not rs_bad, '100 restarts keep the name, skin, SOUL options, server, last code and the room settings (%r)' % rs_bad[:3])

# ---------------------------------------------------------------- mutators
EFFECT = {
    'm_storm': lambda e, b: e['twin'] == 1,
    'm_hyper': lambda e, b: e['hyper'] == 1,
    'm_dbl': lambda e, b: e['dmul'] == b['dmul'] * 2,
    'm_ohko': lambda e, b: e['ohko'] == 1,
    'm_giant': lambda e, b: e['soul'] == 1.5,
    'm_tiny': lambda e, b: e['soul'] == 0.6,
    'm_mirror': lambda e, b: e['mirror'] == 1,
    'm_rcost': lambda e, b: e['rcost'] == 1,
    'm_fast': lambda e, b: e['gmul'] == b['gmul'] * 2,
    'm_noheal': lambda e, b: e['fullheal'] == 0 and e['hmul'] == 0 and all(x in e['skoff'] for x in (11, 12, 14)),
    'm_shield': lambda e, b: e['shieldmad'] == 1,
    'm_rapid': lambda e, b: e['rush'] == 2,
    'm_roul': lambda e, b: e['rush'] == 3,
    'm_nmesc': lambda e, b: e['rush'] == 6 and 5 in e['kn'],
    'm_overlap': lambda e, b: e['overlap'] == 1 and e['twin'] == 1,
    'm_sd0': lambda e, b: e['sd0'] == 1,
    'm_dgraze': lambda e, b: e['grz'] == b['grz'] * 2,
    'm_lowhp': lambda e, b: e['mhp'] <= 60,
    'm_chaos': lambda e, b: e['twin'] == 1 and e['hyper'] == 1 and e['rush'] == 2 and e['gmul'] == b['gmul'] * 2 and e['rcost'] == 1 and e['grz'] == b['grz'] * 2,
}
ok(sorted(EFFECT) == sorted(MUTS), 'every mutator has a test (%r)' % sorted(set(MUTS) ^ set(EFFECT)))
base = J(sim, 'kbr_eff(kfo_set_default())')
for m in ('ohko', 'mirror', 'rcost', 'shieldmad', 'overlap', 'sd0'):
    eq(base[m], 0, 'no mutator: %s off' % m)
eq(base['soul'], 1, 'no mutator: SOULs normal size')
for m in MUTS:
    s = dict(DEF)
    s[m] = 1
    if m == 'm_lowhp':
        s['mhp'] = 200
    e = J(sim, 'kbr_eff(%s)' % gq(s))
    ok(EFFECT[m](e, DEF), '%s does what it says (%r)' % (m, {k: e[k] for k in ('twin', 'hyper', 'dmul', 'ohko', 'soul', 'mirror', 'rcost', 'gmul', 'rush', 'overlap', 'sd0', 'grz', 'mhp')}))
    # and the sudden-death-from-the-start mutator really starts it at tick 0
    if m == 'm_sd0':
        eq(J(sim, 'kbr_tl_new(5, %s).sd_t' % gq(s)), 0, 'SUDDEN DEATH FROM THE START: sudden death at tick 0')
pairs = 0
pair_bad = []
for a in range(len(MUTS)):
    for b in range(a + 1, len(MUTS)):
        s = dict(DEF)
        s[MUTS[a]] = 1
        s[MUTS[b]] = 1
        sim.run('global.S1 = kfo_set_clean(%s); global.E = kbr_eff(global.S1); global.TL = kbr_tl_new(77, global.S1); global.TB = 0;'
                'for (var _k = 0; _k < 20; _k++) { var _c = kbr_tl_get(global.TL, _k); if (!kbr_ok_valid(_c.ok) || knight_reg(_c.reg).joke || _c.dur <= 0) global.TB++; }' % gq(s))
        s1 = J(sim, 'global.S1')
        pairs += 1
        if not valid_check(s1, 'pair %s + %s' % (MUTS[a], MUTS[b])) or J(sim, 'global.TB') != 0:
            pair_bad.append((MUTS[a], MUTS[b]))
        # both on, unless the rules say one wins
        excl = {('m_giant', 'm_tiny'), ('m_rapid', 'm_roul'), ('m_rapid', 'm_nmesc'), ('m_roul', 'm_nmesc')}
        if (MUTS[a], MUTS[b]) not in excl and not (s1[MUTS[a]] == 1 and s1[MUTS[b]] == 1):
            pair_bad.append(('dropped', MUTS[a], MUTS[b]))
ok(not pair_bad, '%d mutator pairs: valid settings, a clean timeline, both on (%r)' % (pairs, pair_bad[:4]))
sim.run('global.S1 = kfo_set_clean({ m_giant: 1, m_tiny: 1, m_rapid: 1, m_roul: 1, m_nmesc: 1 });')
eq(J(sim, '[global.S1.m_giant, global.S1.m_tiny, global.S1.m_rapid, global.S1.m_roul, global.S1.m_nmesc]'), [1, 0, 1, 0, 0], 'GIANT beats TINY, the first switching mutator stays')
ok(J(sim, 'global.kbr_assert_n') == 0, 'no Cyan / roster correction in the mutator timelines')

# ---------------------------------------------------------------- < > through every option
step_bad = []
for o in OPTS:
    if o['kind'] in ('num', 'enum', 'bool', 'mut', 'kw', 'open', 'kn', 'sk'):
        sim.run('global.S1 = kfo_set_default();')
        n = 30 if o['kind'] in ('num', 'kw', 'enum', 'open') else 3
        for d in (1, -1):
            for _ in range(n):
                sim.run('var _r = kfo_opt_change(global.S1, "%s", %d); if (is_struct(_r)) global.S1 = _r;' % (o['oid'], d))
                s1 = J(sim, 'global.S1')
                if not valid_check(s1, 'stepping %s' % o['oid']):
                    step_bad.append(o['oid'])
                    break
        if J(sim, 'global.S1.pre') != 'CUSTOM' and o['kind'] not in ('kn', 'sk', 'open'):
            step_bad.append((o['oid'], 'not CUSTOM'))
ok(not step_bad, 'every option steps through its range and stays valid (%r)' % step_bad[:4])
# knights: the last one stays; the opening knight follows
sim.run('global.S1 = kfo_set_clean({ kn: [3], open: 3 }); global.R1 = kfo_opt_change(global.S1, "kn3", 1);')
ok(J(sim, 'is_string(global.R1)'), 'the last knight cannot be switched off (%s)' % J(sim, 'global.R1'))
sim.run('global.S1 = kfo_set_clean({ kn: [1, 3], open: 3 }); global.R1 = kfo_opt_change(global.S1, "kn3", 1);')
eq(J(sim, '[global.R1.kn, global.R1.open]'), [[1], 1], 'switching off the opening knight moves OPENS to one that is in')
sim.run('global.S1 = kfo_set_clean({ skoff: [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,17,18,19,20,21,22,23,24,25,26,27,28,29,30] }); global.R1 = kfo_opt_change(global.S1, "sk31", 1);')
ok(J(sim, 'is_string(global.R1)'), 'the last skill cannot be switched off (%s)' % J(sim, 'global.R1'))
for k in range(6):
    sim.run('global.S1 = kfo_set_default(); global.R1 = kfo_opt_change(global.S1, "kn%d", 1);' % k)
    ok(k not in J(sim, 'global.R1.kn'), 'Z on %s switches it out' % J(sim, 'kbr_ok_short(%d)' % k))

# ---------------------------------------------------------------- every option is read by the game
src = ''
for f in glob.glob('/home/claude/scripts/gml_templates_v6/*.gml'):
    if os.path.basename(f) not in ('online_set.gml',):
        src += open(f).read()
unused = []
for o in OPTS:
    oid = o['oid']
    if o['kind'] in ('kn', 'kw', 'sk', 'mut', 'encp') or oid.startswith('tgm'):
        # (build 52: ENCOUNTERS is a view of kn - it is never stored, kfo_encp_of)
        # (build 48: the targeting modes are read as "tgm" + string(m): kbr_tg_mode_ok, t_target48)
        # the knight / weight / skill switches are arrays; the mutators work through kbr_eff (checked above)
        continue
    if not re.search(r'\.' + re.escape(oid) + r'\b', src):
        unused.append(oid)
ok(not unused, 'every setting is used by the game code (%r)' % unused)

print('settings tests: %d checks, %d failed' % (N[0], len(FAILS)))
for f in FAILS[:30]:
    print('  -', f)
sys.exit(1 if FAILS else 0)
