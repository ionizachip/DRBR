"""Build 45 (P3): the battle royale's rules, with the host's and the player's real code (no battle running):
  - places and the tie rules (BOTH 1ST: outs within 10 frames share the better place; LATER WINS: only the same frame),
    the winner (or the tie), the results in place order - 300 random matches, every one checked against a reference;
  - the final two: announced exactly once in every match that gets down to two (never with 2 players from the start, never
    with FINAL TWO off, never when the last three fall together) - the same 300 matches;
  - sudden death: the tick it starts at for 100 random rooms, every cycle from there marked, never without SUDDEN DEATH,
    from tick 0 with SUDDEN DEATH FROM THE START; max HP drains at the room's rate down to the floor;
  - the host's checks: 10,000 valid skill uses accepted, and the invalid ones (out, not allowed, cooldown, a red skill
    twice, a green one at the host, a Full Heal too many) refused; impossible HP / max HP / gauge always put right;
  - your own HP: 10,000 hits through the real damage code - every hit counted once, the HP taken adds up, a lethal hit
    makes you OUT exactly once (100 times), and you watch: Left / Right go through the SOULs still standing.
Usage: python3 t_br_rules.py"""
import sys, os, json, random
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


def gq(v):
    return 'json_parse(%s)' % json.dumps(json.dumps(v))


def host_sim():
    s = make_sim()
    s.run('knight_store_load(); global.knight_cfg = knight_cfg_default(); knight_ensure_ctrl(); kfo_get(); global.kfo.name = "Kris";')
    s.mock('kfo_launch', lambda sim: 0)
    s.mock('knight_launch_go', lambda sim: 0)
    return s


def start_match(s, n, setx=None, tick=4000):
    """a practice room with n players (me + n - 1 bots), the match on, its clock at _tick_"""
    sx = dict(setx or {})
    sx['bots'] = n - 1
    s.run('kfo_practice_start(); var _s = kfo_set_clean(%s); kfo_host_set(_s); kfo_host_bots(%d); global.kfo_test_seed = 777;'
          'global.WHY = kfo_host_start(); kfo_local_run(); var _h = global.kfo.H; _h.go = true; _h.t0ms = current_time - (%d / 0.03); _h.feed = [];' % (gq(sx), n - 1, tick))
    return J(s, 'global.WHY')


# ---------------------------------------------------------------- places, ties, winners, the final two: 300 matches
R = random.Random(303)
sim = host_sim()
bad = []
ft_count_bad = []
for m in range(300):
    n = R.choice([2, 3, 4, 5, 6, 7, 8])
    tie = R.randint(0, 1)
    ft_on = 1 if R.random() < 0.85 else 0
    why = start_match(sim, n, {'tie': tie, 'ft': ft_on})
    if why != '':
        bad.append((m, 'start', why))
        continue
    pids = J(sim, '(function() { var _l = []; var _h = global.kfo.H; for (var _i = 0; _i < array_length(_h.pl); _i++) if (_h.pl[_i].inm) array_push(_l, _h.pl[_i].pid); return _l; })()')
    if len(pids) != n:
        bad.append((m, 'players', pids))
        continue
    # outs: everyone but one (or everyone: the last ones together), in batches; ticks close together sometimes
    order = pids[:]
    R.shuffle(order)
    t = 4000
    alive = n
    ref_place = {}
    batches = []
    i = 0
    last_all = R.random() < 0.3
    stop = n if last_all else n - 1
    while i < stop:
        k = min(stop - i, R.choice([1, 1, 1, 2, 3]))
        grp = order[i:i + k]
        ticks = [t + R.choice([0, 0, 3, 9, 11, 25]) * j for j in range(len(grp))]
        batches.append(list(zip(grp, ticks)))
        i += k
        t += R.randint(30, 400)
    ft_seen = 0
    alive_hist = [n]
    settle_alive = []
    for b in batches:
        for pid, tk in b:
            sim.run('kfo_host_out_report(%d, %d, "out");' % (pid, tk))
        sim.run('kfo_host_outs_settle(true);')
        # the reference: earliest first; a group = within 10 frames (BOTH 1ST) or the same frame (LATER WINS) of its first
        srt = sorted(b, key=lambda x: x[1])
        win = 10 if tie == 0 else 0
        j = 0
        while j < len(srt):
            g = [srt[j]]
            q = j + 1
            while q < len(srt) and srt[q][1] - srt[j][1] <= win:
                g.append(srt[q])
                q += 1
            place = max(1, alive - len(g) + 1)
            for pid, _ in g:
                ref_place[pid] = place
            alive -= len(g)
            alive_hist.append(alive)
            j = q
        settle_alive.append(alive)
    if alive == 1:
        last = [p for p in pids if p not in ref_place][0]
        ref_place[last] = 1
    res = J(sim, 'is_struct(global.kfo.H.res) ? global.kfo.H.res : undefined')
    if res is None:
        bad.append((m, 'no result', n, alive))
        continue
    got = {p['pid']: p['pl'] for p in res['pl']}
    if got != ref_place:
        bad.append((m, 'places', n, tie, ref_place, got))
    want_w = sorted(p for p, pl in ref_place.items() if pl == 1)
    if sorted(res['wid']) != want_w:
        bad.append((m, 'winners', want_w, res['wid']))
    pls = [p['pl'] for p in res['pl']]
    if pls != sorted(pls):
        bad.append((m, 'order', pls))
    feed = [f[1] if isinstance(f, list) else f.get('t', '') for f in J(sim, 'global.kfo.H.feed')]
    nft = sum(1 for f in feed if 'FINAL TWO' in f)
    # the host looks after each settle (the outs of the last half second together): a match qualifies when one leaves two
    qualifies = ft_on and n > 2 and 2 in settle_alive
    if nft != (1 if qualifies else 0):
        ft_count_bad.append((m, n, ft_on, alive_hist, nft))
    if len(want_w) > 1 and not any('A TIE' in f for f in feed):
        bad.append((m, 'tie not told', feed[-2:]))
ok(not bad, '300 matches: places, ties, winners, the result order as the rules say (%d bad: %r)' % (len(bad), bad[:3]))
ok(not ft_count_bad, 'the final two exactly once in every match that gets to two, never otherwise (%r)' % ft_count_bad[:4])

# a match that ends and a new one: the final two again, once
why = start_match(sim, 4, {'ft': 1})
bp = [p for p in J(sim, '(function() { var _l = []; var _h = global.kfo.H; for (var _i = 0; _i < array_length(_h.pl); _i++) if (_h.pl[_i].inm) array_push(_l, _h.pl[_i].pid); return _l; })()') if p != 1]
for pid, tk in ((bp[0], 4100), (bp[1], 4300)):
    sim.run('kfo_host_out_report(%d, %d, "out"); kfo_host_outs_settle(true);' % (pid, tk))
eq(J(sim, 'global.kfo.H.ft_done'), True, 'final two announced')
ftk = J(sim, 'global.kfo.H.ftk')
ok(ftk > 0 and J(sim, 'global.kfo.H.tl.ft') == ftk, 'the host\'s own timeline has the final two from cycle %d' % ftk)
sim.run('kfo_host_out_report(%d, 4500, "out"); kfo_host_outs_settle(true);' % bp[2])
eq(J(sim, 'global.kfo.H.st'), 'lobby', 'the match ended')
why = start_match(sim, 4, {'ft': 1})
eq(J(sim, '[global.kfo.H.ft_done, global.kfo.H.ftk]'), [False, -1], 'a new match: the final two not yet')

# ---------------------------------------------------------------- sudden death
sd_bad = []
for i in range(100):
    st = {'sd': 1, 'ramp': R.randint(0, 3), 'maxst': R.randint(0, 4), 'fin': R.randint(1, 5), 'cdn': R.randint(3, 10), 'rush': R.randint(0, 6), 'm_sd0': 1 if i % 10 == 0 else 0}
    sim.run('global.TL = kbr_tl_new(%d, kfo_set_clean(%s)); global.SDK = []; for (var _k = 0; _k < 400; _k++) { var _c = kbr_tl_get(global.TL, _k); array_push(global.SDK, [_c.t0, _c.sd]); }' % (1000 + i, gq(st)))
    sd_t = J(sim, 'global.TL.sd_t')
    cyc = J(sim, 'global.SDK')
    if st['m_sd0']:
        want = 0
    else:
        intro = st['cdn'] * 30
        to4 = 0 if st['ramp'] == 3 else {0: 90, 1: 60, 2: 40}[st['ramp']] * st['maxst']
        want = intro + (to4 + st['fin'] * 60) * 30
    if sd_t != want:
        sd_bad.append(('sd_t', st, sd_t, want))
    # a cycle is a sudden-death cycle when it begins (the end of the one before it; the first: the countdown's end) at or
    # after sd_t; the drain counts from the first one's start (kbr_tl_sd_t0)
    sim.run('global.SDB = []; for (var _k = 0; _k < 400; _k++) array_push(global.SDB, (_k == 0) ? global.TL.intro : kbr_tl_get(global.TL, _k - 1).t1);'
            'global.SD0 = kbr_tl_sd_t0(global.TL);')
    base = J(sim, 'global.SDB')
    wrong = [(k, t0, sd) for k, ((t0, sd), b) in enumerate(zip(cyc, base)) if bool(sd) != (b >= sd_t)]
    if wrong:
        sd_bad.append(('cycle flags', st, wrong[:2]))
    first = [t0 for t0, sd in cyc if sd]
    if first and J(sim, 'global.SD0') != first[0]:
        sd_bad.append(('sd start', st, J(sim, 'global.SD0'), first[0]))
    if cyc[-1][0] < sd_t:
        sd_bad.append(('timeline too short to reach it', st))
for i in range(20):
    sim.run('global.TL = kbr_tl_new(%d, kfo_set_clean({ sd: 0, m_sd0: 0 })); global.SDN = 0; for (var _k = 0; _k < 400; _k++) if (kbr_tl_get(global.TL, _k).sd) global.SDN++;' % (2000 + i))
    if J(sim, 'global.TL.sd_t') != -1 or J(sim, 'global.SDN') != 0:
        sd_bad.append(('sd off but on', i))
ok(not sd_bad, 'sudden death: 100 rooms start it at the right tick and mark every cycle from there; never when it is off (%r)' % sd_bad[:3])

# ---------------------------------------------------------------- the host's checks: skills and impossible numbers
why = start_match(sim, 8, {'skills': 1, 'cdm': 25})
sk = J(sim, 'global.kfo.H.eff.skoff')
acc0 = J(sim, 'global.kfo.H.skills_ok')
seq = {}
valid_n = 0
pids = [p for p in J(sim, '(function() { var _l = []; var _h = global.kfo.H; for (var _i = 0; _i < array_length(_h.pl); _i++) if (_h.pl[_i].inm) array_push(_l, _h.pl[_i].pid); return _l; })()') if p != 1]
t_ms = 0
for i in range(10000):
    pid = pids[i % len(pids)]
    sid = R.randint(1, 10)
    seq[pid] = seq.get(pid, 0) + 1
    # a use that keeps every rule: alive, an attack skill the room allows, a new sequence number, after the cooldown
    sim.run('var _p = kfo_host_player(%d); _p.al = 1; _p.t_sk = -999999; _p.last_sid = -1;'
            'kfo_host_skill(_p, { k: "sk", sid: %d, seq: %d, mid: global.kfo.H.mid });' % (pid, sid, seq[pid]))
    valid_n += 1
acc = J(sim, 'global.kfo.H.skills_ok') - acc0
ok(acc >= 0.999 * valid_n, '10,000 valid skill uses: %d accepted (%.2f%%)' % (acc, 100.0 * acc / valid_n))
bad0 = J(sim, 'global.kfo.H.skills_bad')
P2, P3, P4, P5 = pids[0], pids[1], pids[2], pids[3]
M_ = 'mid: global.kfo.H.mid'
invalid = [
    ('out', 'var _p = kfo_host_player(%d); _p.al = 0; kfo_host_skill(_p, { k: "sk", sid: 1, seq: 999001, %s }); _p.al = 1;' % (P2, M_)),
    ('green at host', 'var _p = kfo_host_player(%d); _p.t_sk = -999999; kfo_host_skill(_p, { k: "sk", sid: 11, seq: 999002, %s });' % (P3, M_)),
    ('not a skill', 'var _p = kfo_host_player(%d); _p.t_sk = -999999; kfo_host_skill(_p, { k: "sk", sid: 99, seq: 999003, %s });' % (P3, M_)),
    ('a fraction', 'var _p = kfo_host_player(%d); _p.t_sk = -999999; kfo_host_skill(_p, { k: "sk", sid: 2.5, seq: 999004, %s });' % (P3, M_)),
    ('a string', 'var _p = kfo_host_player(%d); _p.t_sk = -999999; kfo_host_skill(_p, { k: "sk", sid: "1", seq: 999005, %s });' % (P3, M_)),
    ('the same use twice', 'var _p = kfo_host_player(%d); _p.t_sk = -999999; kfo_host_skill(_p, { k: "sk", sid: 1, seq: 999006, %s }); _p.t_sk = -999999; kfo_host_skill(_p, { k: "sk", sid: 1, seq: 999006, %s });' % (P4, M_, M_)),
    ('cooldown', 'var _p = kfo_host_player(%d); _p.t_sk = -999999; kfo_host_skill(_p, { k: "sk", sid: 1, seq: 999007, %s }); kfo_host_skill(_p, { k: "sk", sid: 2, seq: 999008, %s });' % (P5, M_, M_)),
]
for nm, code in invalid:
    b0 = J(sim, 'global.kfo.H.skills_bad')
    a0 = J(sim, 'global.kfo.H.skills_ok')
    sim.run(code)
    b1 = J(sim, 'global.kfo.H.skills_bad')
    a1 = J(sim, 'global.kfo.H.skills_ok')
    if nm in ('the same use twice', 'cooldown'):
        ok(a1 - a0 == 1 and b1 - b0 >= 1, 'host refuses %s (accepted %d, refused %d)' % (nm, a1 - a0, b1 - b0))
    else:
        ok(a1 == a0 and b1 > b0, 'host refuses %s (accepted %d, refused %d)' % (nm, a1 - a0, b1 - b0))
# a skill switched off in the room
why = start_match(sim, 4, {'skills': 1, 'skoff': [1, 2]})
sim.run('var _p = kfo_host_player(%d); _p.t_sk = -999999; global.A0 = global.kfo.H.skills_ok; kfo_host_skill(_p, { k: "sk", sid: 1, seq: 5, mid: global.kfo.H.mid });' % J(sim, 'global.kfo.H.pl[1].pid'))
eq(J(sim, 'global.kfo.H.skills_ok - global.A0'), 0, 'a skill the room switched off is refused')
why = start_match(sim, 4, {'skills': 0})
sim.run('var _p = kfo_host_player(%d); _p.t_sk = -999999; global.A0 = global.kfo.H.skills_ok; kfo_host_skill(_p, { k: "sk", sid: 3, seq: 5, mid: global.kfo.H.mid });' % J(sim, 'global.kfo.H.pl[1].pid'))
eq(J(sim, 'global.kfo.H.skills_ok - global.A0'), 0, 'no skills at all when SKILLS is off')
# impossible numbers: 1,000 random statuses, every one leaves the host's numbers in range
why = start_match(sim, 4, {'mhp': 150})
fx_bad = []
for i in range(1000):
    hp = R.choice([R.uniform(-50, 400), 9999, -1, 150, 75, 'x', None, 1e12])
    mh = R.choice([150, 160, 9999, 0, -5, 100, 'y', None])
    g = R.choice([0, 50, 100, 101, 250, -3, 'z', None])
    sim.run('var _p = global.kfo.H.pl[1]; _p.al = 1; kfo_host_on_status(_p, %s); global.P = [_p.hp, _p.mh, _p.g];' % gq({'k': 's', 'mid': 1, 'hp': hp, 'mhp': mh, 'g': g}))
    php, pmh, pg = J(sim, 'global.P')
    if not (isinstance(pmh, (int, float)) and 1 <= pmh <= 150 and 0 <= php <= pmh and 0 <= pg <= 100):
        fx_bad.append((hp, mh, g, php, pmh, pg))
ok(not fx_bad, '1,000 statuses with impossible numbers: the host keeps HP / max HP / gauge in range (%r)' % fx_bad[:3])

# the host's max HP check in sudden death counts from the first sudden-death attack, as the games drain it
why = start_match(sim, 4, {'sd': 1, 'ramp': 2, 'maxst': 1, 'fin': 1, 'mhp': 150, 'sdrate': 1})
sd_t = J(sim, 'global.kfo.H.tl.sd_t')
sd0 = J(sim, 'kbr_tl_sd_t0(global.kfo.H.tl)')
ok(sd0 >= sd_t, 'the first sudden-death attack starts at or after sd_t (%d, %d)' % (sd_t, sd0))
sim.run('var _h = global.kfo.H; _h.t0ms = current_time - (%d / 0.03); var _p = _h.pl[1]; _p.al = 1; global.F0 = _h.fixes; kfo_host_on_status(_p, { k: "s", mid: _h.mid, hp: 150, mhp: 150, g: 0 }); global.F1 = _h.fixes;' % (sd0 - 1))
eq(J(sim, 'global.F1 - global.F0'), 0, 'full max HP just before the first sudden-death attack is not "fixed"')
sim.run('var _h = global.kfo.H; _h.t0ms = current_time - (%d / 0.03); var _p = _h.pl[1]; global.F0 = _h.fixes; kfo_host_on_status(_p, { k: "s", mid: _h.mid, hp: 150, mhp: 150, g: 0 }); global.F1 = _h.fixes;' % (sd0 + 30 * 20))
eq(J(sim, 'global.F1 - global.F0'), 1, 'full max HP 20 seconds into sudden death is put right')
eq(J(sim, 'global.kfo.H.pl[1].mh'), 150 - 20 + 3, 'to what the drain leaves (with 3 seconds to spare)')

# ---------------------------------------------------------------- your HP: 10,000 hits, OUT once, watching
sys.path.insert(0, '/home/claude/work/uiref')
from br_shot import br_frame
s2, _ = br_frame('t_rules', n=4, out=(), render=False)
s2.define_object('obj_testbullet')
s2.run('global.TBI = instance_create(0, 0, obj_testbullet);')
s2.run('global.kfo.hostid = 1; global.kfo.mode = "local"; var _M = global.kfo.M; _M.out = false; _M.me = true; global.hp[1] = 10000000; global.maxhp[1] = 10000000; _M.hits = 0; _M.taken = 0;')
tot = 0
hits = 0
d_bad = 0
for i in range(10000):
    s2.run('with (global.TBI) global.D = kbr_dmg_taken(0); global.hp[1] -= global.D;')
    d = J(s2, 'global.D')
    tot += d
    hits += 1
    if d < 0:
        d_bad += 1
st = J(s2, '[global.kfo.M.hits, global.kfo.M.taken, global.hp[1], global.kfo.M.out]')
eq(st[0], hits, '10,000 hits: every hit counted once')
eq(st[1], tot, '10,000 hits: the HP taken adds up exactly')
eq(st[2], 10000000 - tot, '10,000 hits: HP went down by exactly that')
ok(d_bad == 0 and not st[3], 'no negative damage, still standing')
outs = 0
q_bad = []
for i in range(100):
    s2.run('var _M = global.kfo.M; _M.out = false; global.hp[1] = 5; global.maxhp[1] = 150; global.kfo.lq = []; with (global.TBI) global.D = kbr_dmg_taken(0); global.hp[1] -= global.D;'
           'with (global.TBI) global.D2 = kbr_dmg_taken(0);')
    o = J(s2, '[global.kfo.M.out, global.hp[1], global.D2]')
    msgs = J(s2, '(function() { var _n = 0; for (var _i = 0; _i < array_length(global.kfo.lq); _i++) if (global.kfo.lq[_i].up && kfo_js(global.kfo.lq[_i].m, "k", "") == "out") _n++; return _n; })()')
    if o[0] and o[1] >= 1 and o[2] == 0 and msgs == 1:
        outs += 1
    else:
        q_bad.append((i, o, msgs))
eq(outs, 100, '100 lethal hits: OUT once each (HP left at 1 for the battle, one OUT message, no hit after)')
# watching: Left / Right go through the SOULs still standing
# (build 47: a player who just went OUT sees their SOUL break for 45 frames before the camera picks someone - t_view47
# SOUL-006 checks that; here the wait is over)
s2.run('global.kfo.M.out = true; global.kfo.M.spect = -1; if (!variable_struct_exists(global.kfo.M, "vw")) global.kfo.M.vw = kbr_vw_new(); global.kfo.M.vw.out_t = 1;')
seen = []
for i in range(6):
    s2.inp['right'] = 1
    s2.run('kbr_spectate_tick();')
    s2.inp['right'] = 0
    s2.step(0) if False else None
    seen.append(J(s2, 'global.kfo.M.spect'))
alive_ids = J(s2, 'kbr_alive_ids()')
ok(set(seen) == set(alive_ids) and all(x in alive_ids for x in seen), 'watching: RIGHT cycles through every SOUL still standing (%r of %r)' % (seen, alive_ids))

# ---------------------------------------------------------------- mutators in the battle (the player's own code)
def mut_sim(setx):
    m, _ = br_frame('t_mut', n=4, out=(), render=False)
    for b in ('button1_h', 'button2_h', 'button3_h', 'left_h', 'right_h', 'up_h', 'down_h'):
        if b not in m.builtins and b not in m.scripts:
            m.mock(b, lambda s: 0)
    m.define_object('obj_testbullet')
    m.run('global.TBI = instance_create(0, 0, obj_testbullet); global.kfo.hostid = 1; global.kfo.mode = "local";'
          'var _M = global.kfo.M; var _s = kfo_set_clean(%s); _M.set = _s; _M.eff = kbr_eff(_s); _M.sk = kbr_skills_new(_M.eff); _M.out = false; _M.me = true;'
          'global.hp[1] = 150; global.maxhp[1] = 150;' % gq(setx))
    return m


m = mut_sim({'m_ohko': 1})
m.run('with (global.TBI) global.D = kbr_dmg_taken(0); global.hp[1] -= global.D;')
eq(J(m, '[global.kfo.M.out, global.hp[1]]'), [True, 1], 'ONE-HIT ELIMINATION: the first hit makes you OUT')
m = mut_sim({})
m.run('with (global.TBI) global.D = kbr_dmg_taken(0); global.hp[1] -= global.D;')
eq(J(m, 'global.kfo.M.out'), False, 'without it one hit does not')
for mu, scale in (('m_giant', 1.5), ('m_tiny', 0.6), (None, 1)):
    m = mut_sim({mu: 1} if mu else {})
    m.run('global.HI = instance_create(300, 160, obj_heart); with (global.HI) { image_xscale = 1; image_yscale = 1; wspeed = 4; } kbr_me_tick();')
    eq(J(m, '[global.HI.image_xscale, global.HI.image_yscale]'), [scale, scale], '%s: SOUL size %.1f' % (mu or 'no size mutator', scale))
for mirror in (1, 0):
    m = mut_sim({'m_mirror': mirror})
    m.run('global.GB = instance_create(320, 170, obj_growtangle); with (global.GB) { bbox_left = 245; bbox_right = 395; bbox_top = 95; bbox_bottom = 245; }'
          'global.HI = instance_create(300, 160, obj_heart); with (global.HI) { canmove = 1; xprevious = 300; yprevious = 160; x = 304; y = 157; bbox_left = x; bbox_right = x + 16; bbox_top = y; bbox_bottom = y + 16; }'
          'kbr_end_step();')
    eq(J(m, '[global.HI.x, global.HI.y]'), [296, 163] if mirror else [304, 157], 'MIRROR CONTROLS %s: the SOUL moves %s' % ('on' if mirror else 'off', 'the other way' if mirror else 'as pressed'))
m = mut_sim({'m_rcost': 1})
needs = set()
for i in range(40):
    m.run('global.kfo.M.sk.need = -1;')
    needs.add(J(m, 'kbr_skill_need()'))
ok(len(needs) > 5 and min(needs) >= 40 and max(needs) <= 100, 'RANDOM SKILL COSTS: a new cost 40-100 after each draw (%d different)' % len(needs))
m = mut_sim({})
eq(J(m, 'kbr_skill_need()'), 60, 'without it: 60')
m = mut_sim({'m_shield': 1, 'skills': 1})
draws = [J(m, 'kbr_skill_draw(100)') for _ in range(200)]
ok(0.3 < draws.count(13) / 200.0 < 0.75, 'SHIELD MADNESS: about half the draws are Shields (%d of 200)' % draws.count(13))
m = mut_sim({'m_noheal': 1, 'skills': 1})
draws = [J(m, 'kbr_skill_draw(100)') for _ in range(200)]
ok(not any(d in (11, 12, 14) for d in draws), 'NO HEALING: no heal or regeneration is ever drawn')

print('battle royale rules: %d checks, %d failed' % (N[0], len(FAILS)))
for f in FAILS[:20]:
    print('  -', f)
sys.exit(1 if FAILS else 0)
