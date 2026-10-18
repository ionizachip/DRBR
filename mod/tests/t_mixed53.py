"""DRBR: every encounter in one KNIGHT RUSH (a new one every attack): the Normal Knight, Jevil, Gerson, Flowery, Spamton NEO and
Pink in a practice match (the emulator: the real merged code, a mocked engine, SOUL / bullet collisions on), the SOUL standing.
At the start of every attack, checked:
  - the stage: the lineup's active entry is the cycle's encounter (a knight: its index; a boss: its lineup id 1000 + n), its
    battle object on stage and NO other boss's battle object;
  - nothing of another encounter left: no piece of another boss (obj_jv_ / obj_hj_ / obj_fl_ / obj_sn_ / obj_pk_, their
    backgrounds aside), no knight while a boss is out;
  - the battle names the boss while it is out;
and over each attack: the SOUL in the boss's own mode at some point (Gerson green, Flowery orange, Spamton yellow, Pink purple or
her concert's red) and red again after the cut; no error, no frame run twice.
1.0.1: the music (every boss's song file made in the game's mus folder): one song change at a time (two handlers once queued two
songs when a boss came on after another), the boss's own song while it is out, none of a boss's while a knight is; the stage
banners on a boss's attack name no Knight stage and use the boss's own battle text. Usage: python3 t_mixed53.py [frames]"""
import sys, os, json, time
os.environ.setdefault('KH_CAM', '1000,320')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import br_harness
br_harness.COLLIDE = True
from br_harness import *

FAILS = []
N = [0]
FR = int(sys.argv[1]) if len(sys.argv) > 1 else 5000
OKS = (0, 6, 7, 8, 9, 10)
BOSS = {6: ('obj_jv_joker', 'obj_jv_', 1000, 'Jevil', None), 7: ('obj_hj_gerson', 'obj_hj_', 1001, 'Gerson', 'green'),
        8: ('obj_fl_flowery', 'obj_fl_', 1002, 'Flowery', 'orange'), 9: ('obj_sn_neo', 'obj_sn_', 1003, 'Spamton NEO', 'yellow'),
        10: ('obj_pk_pink', 'obj_pk_', 1004, 'Pink', 'purple')}


def ok(c, m):
    N[0] += 1
    print(('ok   ' if c else 'FAIL ') + m, flush=True)
    if not c:
        FAILS.append(m)
    return c


def J(sim, e):
    return sim.py(sim.eval(e))


t0 = time.time()
sim, e = br_match(open_ok=0, kn=OKS, seed=6300, bots=0, setx='_s.mhp = 999; _s.rush = 1; _s.ramp = 3; _s.hard = 1;')
ok(e is None, 'mixed: practice with the Knight and the five bosses, a new one every attack (%s)' % (e,))
sim.run('global.knight_mus_ok_force = true;')
# the songs are there (empty files: the emulator only asks whether they exist)
MUS = {6: 'joker.ogg', 7: 'ch4_extra_boss.ogg', 8: 'Flowerman_Arrangement.ogg', 9: 'spamton_neo_mix_ex_wip.ogg', 10: 'pink.ogg'}
os.makedirs(os.path.join(sim.fs.root, 'mus'), exist_ok=True)
for fn in list(MUS.values()) + ['knight.ogg', 'kh_forget_me_not.ogg', 'kh_close_to_inevitability.ogg']:
    open(os.path.join(sim.fs.root, 'mus', fn), 'w').close()
sim.run('knight_music_cache_clear();')
FLAV = {o: J(sim, 'kbr_enc_of_lu(%d).flavor' % BOSS[o][2]) for o in BOSS}
songs = []          # every song change queued: [frame, file]
maxq = 0
banners = []        # every big announcement: [cycle, title, line]
seen_q = set()
last_bn = None
# every instance's object name, grouped by prefix (the bosses' backgrounds aside: they fade out after their boss)
STAGE = ('(function(){ var _M = global.kfo.M; var _c = kbr_tl_get(_M.tl, _M.R.k); var _lu = global.knight_lu; var _o = {};'
         'var _p = ["obj_jv_", "obj_hj_", "obj_fl_", "obj_sn_", "obj_pk_"];'
         'with (all) { var _n = object_get_name(object_index); for (var _i = 0; _i < 5; _i++) { if (string_pos(_p[_i], _n) == 1 && string_pos("_bg", _n) == 0) { variable_struct_set(_o, _n, (variable_struct_exists(_o, _n) ? variable_struct_get(_o, _n) : 0) + 1); } } }'
         'var _kn = 0; with (obj_knight_enemy) _kn++;'
         'return { k: _c.k, ok: _c.ok, ai: _c.ai, act: _lu.ks[_lu.act], kn: _kn, pre: _o, name: global.monstername[0],'
         ' objs: [instance_number(obj_jv_joker), instance_number(obj_hj_gerson), instance_number(obj_fl_flowery), instance_number(obj_sn_neo), instance_number(obj_pk_pink)] }; })()')
rows = []
modes = {}
last_k = -1
err = None
for f in range(FR):
    sim.run('if (!global.kfo.M.out) global.hp[kbr_char()] = global.maxhp[kbr_char()];')
    err = step(sim, 1)
    if err:
        break
    if f % 30 == 0:
        sim.log.clear()
    sim.run(BR_CHK)
    b = J(sim, 'global.BRS')
    if b['ph'] == 'run' and b['k'] != last_k:
        last_k = b['k']
        rows.append(J(sim, STAGE))
    if b['ph'] == 'run' and rows:
        modes.setdefault(rows[-1]['k'], set()).add(J(sim, 'kbr_soul_mode()'))
    # the music queue: how many song changes wait at once, and each new one
    q = J(sim, '(function(){ var _o = []; for (var _i = 0; _i < array_length(global.knight_mus_q); _i++) { var _e = global.knight_mus_q[_i]; if (_e.k == "song") array_push(_o, [_e.file, _e.t]); } return _o; })()')
    maxq = max(maxq, len(q))
    for fn, t in q:
        key = (fn, f + t)
        if key not in seen_q:
            seen_q.add(key)
            songs.append([f, fn, b['k']])
    bn = J(sim, 'is_struct(global.kfo.M) && variable_struct_exists(global.kfo.M, "bn") && is_struct(global.kfo.M.bn) ? [global.kfo.M.bn.title, global.kfo.M.bn.sub, global.kfo.M.R.k] : 0')
    if bn and bn != last_bn:
        banners.append(bn)
    last_bn = bn
ok(err is None, 'mixed: no error in %d frames %s' % (FR, (err or '')[:300]))
ok(not getattr(sim, 'retrylog', []), 'mixed: no frame run twice %r' % (getattr(sim, 'retrylog', [])[:2],))
print('cycles', json.dumps(rows), flush=True)
print('modes', {k: sorted(v) for k, v in modes.items()}, flush=True)
print('songs', songs, flush=True)
print('banners', banners, flush=True)
ok(maxq <= 1, 'mixed: never two song changes waiting at once (most at once: %d)' % maxq)
# the song while each cycle runs: the last change queued before its attack started
okk = {r['k']: r['ok'] for r in rows}
for r in rows:
    before = [x for x in songs if x[2] <= r['k']]
    cur = before[-1][1] if before else ''
    if r['ok'] in MUS:
        ok(cur == MUS[r['ok']], "cycle %d (%s): the boss's own song is on (%r)" % (r['k'], BOSS[r['ok']][3], cur))
    else:
        ok(cur not in MUS.values(), 'cycle %d (knight %d): no boss song (%r)' % (r['k'], r['ok'], cur))
st_b = [x for x in banners if str(x[0]).startswith('STAGE ')]
for x in st_b:
    o = okk.get(x[2])
    if o in BOSS:
        ok(not any(w in x[0] for w in ('GUESTS', 'SHUFFLE', 'KNIGHTMARE')) and x[1] in FLAV[o],
           "stage banner on %s's attack (cycle %d): no Knight stage, the boss's own battle text %r" % (BOSS[o][3], x[2], x[:2]))
# each boss's stage banner and the FINAL TWO line, called directly (this run's ramp starts at stage 3: no stage changes)
for o in sorted(BOSS) + [0]:
    for st in (1, 3, 4):
        sim.run('global.kfo.M.stage = %d; global.kfo.M.bn = undefined; global.kfo.M.ft_on = true; global.kfo.M.sd_on = true;'
                'kbr_stage_fx({ st: %d, ok: %d, k: 5, sd: false, ft: false });' % (st - 1, st, o))
        x = J(sim, 'is_struct(global.kfo.M.bn) ? [global.kfo.M.bn.title, global.kfo.M.bn.sub] : 0')
        if o in BOSS:
            ok(x and not any(w in x[0] for w in ('GUESTS', 'SHUFFLE', 'KNIGHTMARE')) and x[1] in FLAV[o] and x[0].startswith('STAGE %d' % st),
               "stage %d banner on %s's attack: its number%s and the boss's own battle text %r" % (st, BOSS[o][3], ' and OVERDRIVE' if st == 4 else '', x))
        else:
            ok(x and x[0] == 'STAGE %d: %s' % (st, J(sim, 'kfo_stage_name(%d)' % st)), 'stage %d banner on the Knight: as before %r' % (st, x))
    sim.run('global.kfo.M.bn = undefined; kbr_final_two_fx({ ok: %d });' % o)
    x = J(sim, 'is_struct(global.kfo.M.bn) ? [global.kfo.M.bn.title, global.kfo.M.bn.sub] : 0')
    ok(x and x[0] == 'FINAL TWO' and (('Roaring' in x[1]) == (o not in BOSS)), 'FINAL TWO line for %s: %r' % (BOSS[o][3] if o in BOSS else 'the Knight', x))
seen = sorted(set(r['ok'] for r in rows))
ok(len(seen) >= 4, 'mixed: at least four encounters took turns %r (%d cycles)' % (seen, len(rows)))
for r in rows:
    o = r['ok']
    if o in BOSS:
        obj, pre, lu, name, mode = BOSS[o]
        oi = sorted(BOSS).index(o)
        ok(r['act'] == lu and r['kn'] == 0 and r['objs'][oi] == 1 and sum(r['objs']) == 1,
           'cycle %d (%s, attack %d): %s on stage alone, no knight %r' % (r['k'], name, r['ai'], name, [r['act'], r['kn'], r['objs']]))
        ok(all(n.startswith(pre) for n in r['pre']), 'cycle %d (%s): nothing of another boss left %r' % (r['k'], name, {n: v for n, v in r['pre'].items() if not n.startswith(pre)}))
        ok(r['name'] == name, 'cycle %d: the battle names %s (%r)' % (r['k'], name, r['name']))
        if mode is not None:
            ms = modes.get(r['k'], set())
            ok(mode in ms or (o == 10 and 'red' in ms), 'cycle %d (%s, attack %d): the SOUL in his / her mode (%s) %r' % (r['k'], name, r['ai'], mode, sorted(ms)))
    else:
        ok(r['act'] == o and r['kn'] == 1 and sum(r['objs']) == 0 and r['pre'] == {}, 'cycle %d (knight %d): the knight on stage, no boss and nothing of one left %r' % (r['k'], o, [r['act'], r['kn'], r['objs'], r['pre']]))
        ok(modes.get(r['k'], {'red'}) == {'red'}, 'cycle %d (knight %d): the SOUL red all the attack %r' % (r['k'], o, sorted(modes.get(r['k'], []))))
print('mixed53: %d checks, %d failed (%.0fs)' % (N[0], len(FAILS), time.time() - t0))
for f in FAILS:
    print('  -', f)
sys.exit(1 if FAILS else 0)
