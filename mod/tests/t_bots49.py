"""Build 49: the smart bots.

  presets  the numbers (one place: kfo_bot_presets), PERFECT = no delay, full look-ahead, no mistakes, exact moves; a bot's
           own settings, CUSTOM after a slider, back to the room's BOT SKILL; the settings cleaned (bad values)
  dodge    one practice match per knight with six bots, one per preset (DUMMY ... PERFECT), the same bullets for all: hits taken
           by each over the run. The emulator's stand-in for GameMaker's motion and collision boxes (bbox_model.py: the real
           sprites' boxes from data.win, motion by speed, rectangle collision) - the bots' code itself is the mod's
  skills   the bots charge, heal when low and safe, shield / reflect, send attack skills with a TARGETING mode for the moment
           (PROCEED when someone is nearly out, DEFEND when two or more target it)
  ui       the room's BOTS page: add / remove bots, the room's BOT SKILL, a bot's page (preset, sliders, ROOM'S SKILL); BOT tag
           in the match's player list; the lobby row only for the host
Usage: python3 t_bots49.py [part ...]"""
import sys, os, json, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from br_harness import *
import bbox_model
import t_view47

FAILS = []
N = [0]
STATS = {}


def ok(c, m):
    N[0] += 1
    print(('ok   ' if c else 'FAIL ') + m, flush=True)
    if not c:
        FAILS.append(m)
    return c


def J(sim, e):
    return sim.py(sim.eval(e))


PRE = ['DUMMY', 'EASY', 'NORMAL', 'HARD', 'EXPERT', 'PERFECT']


def part_presets():
    sim, e = br_match(open_ok=0, kn=(0,), seed=11, bots=2, setx='_s.mhp = 300;')
    ok(e is None, 'presets: practice room (%s)' % (e,))
    P = J(sim, 'kfo_bot_presets()')
    ok([p[0] for p in P] == PRE, 'six presets in order %r' % [p[0] for p in P])
    pf = J(sim, 'kfo_bot_cfg(5)')
    ok(pf['react'] == 0 and pf['pred'] == 40 and pf['miss'] == 0 and pf['prec'] == 100 and pf['every'] == 1, 'PERFECT: no delay, the full look-ahead (40 frames = the slider\'s top), no mistakes, exact moves, thinks every frame %r' % pf)
    sl = J(sim, 'kfo_bot_sliders()')
    ok([s[0] for s in sl] == ['react', 'pred', 'miss', 'prec', 'heal', 'chg', 'aggr'], 'seven sliders %r' % [s[1] for s in sl])
    # each one is easier than the next
    for k, better in (('react', -1), ('pred', 1), ('miss', -1), ('prec', 1), ('heal', 1), ('chg', 1)):
        v = [p[1 + ['react', 'pred', 'miss', 'prec', 'heal', 'chg'].index(k)] for p in P]
        ok(all((b - a) * better >= 0 for a, b in zip(v, v[1:])), '%s goes the right way from DUMMY to PERFECT %r' % (k, v))
    c = J(sim, 'kfo_bot_cfg_clean({ pre: 9, react: -5, pred: 999, miss: "x", prec: 50, own: 1 }, 2)')
    ok(c['pre'] == 5 and c['react'] == 0 and c['pred'] == 40 and c['miss'] == 0 and c['prec'] == 50 and c['own'], 'cleaned: out-of-range values pulled in %r' % c)
    # the room's BOT SKILL for bots not set one by one; a bot's own stays
    sim.run('global.kfo.H.set.botp = 4;')
    ok(J(sim, 'kfo_host_botcfg(0).pre') == 4 and J(sim, 'kfo_host_botcfg(1).pre') == 4, 'the room BOT SKILL EXPERT reaches both bots')
    sim.run('var _c = kfo_bot_cfg(0); _c.own = true; global.kfo.H.botcfg[1] = _c; global.kfo.H.set.botp = 1;')
    ok(J(sim, 'kfo_host_botcfg(0).pre') == 1 and J(sim, 'kfo_host_botcfg(1).pre') == 0, 'bot 2 keeps its own DUMMY while the room goes EASY')


def wrap_tick(sim):
    src = t_view47.func_src('kfo_host_bots_tick').replace('function kfo_host_bots_tick(', 'function kfo_host_bots_tick__orig(', 1)
    sim.load_source('gml_GlobalScript_bots49_wrap', src + '\nfunction kfo_host_bots_tick() { test_bbox_sync(); return kfo_host_bots_tick__orig(); }\n')


def dodge_run(kn, frames, seed):
    sim, e = br_match(open_ok=0, kn=(kn,), seed=seed, bots=6, setx='_s.mhp = 999; _s.skills = 0;')
    ok(e is None, 'dodge kn %d: practice with 6 bots (%s)' % (kn, e))
    if e is not None:
        return None
    bbox_model.install(sim)
    wrap_tick(sim)
    sim.run('for (var _i = 0; _i < 6; _i++) { var _c = kfo_bot_cfg(_i); _c.own = true; global.kfo.H.botcfg[_i] = _c; }')
    hits = {}
    run = 0
    t0 = time.time()
    names = None
    for f in range(frames):
        sim.run('if (!global.kfo.M.out) global.hp[kbr_char()] = global.maxhp[kbr_char()];'
                'for (var _i = 0; _i < array_length(global.kfo.H.pl); _i++) { var _b = global.kfo.H.pl[_i]; if (_b.bot) _b.hp = _b.mh; }')
        err = step(sim, 1)
        if err:
            ok(False, 'dodge kn %d: error %s' % (kn, err[:300]))
            return None
        bbox_model.move(sim)
        if f % 30 == 0:
            sim.log.clear()
        if J(sim, 'global.kfo.M.R.ph') == 'run':
            run += 1
    sim.run('global.BH = []; var _j = 0; for (var _i = 0; _i < array_length(global.kfo.H.pl); _i++) { var _b = global.kfo.H.pl[_i]; if (_b.bot) { array_push(global.BH, [kfo_bot_pre_name(kfo_host_botcfg(_j).pre), _b.hits, _b.al]); _j++; } }')
    res = J(sim, 'global.BH')
    return {'kn': kn, 'run_frames': run, 'hits': {r[0]: r[1] for r in res}, 'alive': all(r[2] for r in res), 'wall': round(time.time() - t0)}


def part_dodge():
    tot = {p: 0 for p in PRE}
    runs = []
    for kn, seed in ((0, 4950), (1, 777), (2, 31337), (3, 2024)):
        r = dodge_run(kn, int(os.environ.get('BOT_FRAMES', '2400')), seed)
        if r is None:
            continue
        runs.append(r)
        print('dodge', json.dumps(r), flush=True)
        for p in PRE:
            tot[p] += r['hits'].get(p, 0)
    STATS['dodge'] = {'runs': runs, 'total_hits': tot}
    print('dodge totals', tot, flush=True)
    ok(tot['DUMMY'] > tot['NORMAL'] > tot['PERFECT'], 'more skill, fewer hits: DUMMY %d > NORMAL %d > PERFECT %d' % (tot['DUMMY'], tot['NORMAL'], tot['PERFECT']))
    ok(tot['EASY'] >= tot['HARD'] and tot['HARD'] >= tot['PERFECT'] and tot['EXPERT'] >= tot['PERFECT'], 'EASY %d >= HARD %d >= PERFECT %d, EXPERT %d >= PERFECT' % (tot['EASY'], tot['HARD'], tot['PERFECT'], tot['EXPERT']))
    ok(tot['PERFECT'] <= max(2, tot['DUMMY'] // 10), 'PERFECT takes few hits (%d, DUMMY %d)' % (tot['PERFECT'], tot['DUMMY']))


def part_skills():
    sim, e = br_match(open_ok=0, kn=(0,), seed=4950, bots=3, setx='_s.mhp = 300;')
    ok(e is None, 'skills: practice with 3 bots (%s)' % (e,))
    for f in range(300):
        sim.run('if (!global.kfo.M.out) global.hp[kbr_char()] = global.maxhp[kbr_char()];')
        step(sim, 1)
        if f % 30 == 0:
            sim.log.clear()
    ok(J(sim, 'global.kfo.H.eff.skills') == 1 or J(sim, 'global.kfo.H.eff.skills') is True, 'skills on in the room')
    bots = [p['pid'] for p in J(sim, 'global.kfo.H.pl') if p['bot']]
    b0 = bots[0]
    B = 'kfo_host_player(%d)' % b0
    red = [i for i in range(1, 17) if J(sim, 'kbr_skill_ok(%d) && kbr_skill_red(%d)' % (i, i))]
    ok(len(red) >= 3, 'attack skills exist %r' % red)
    def setup(slots, hp, danger, cfg):
        sim.run('var _b = %s; _b.hp = %d; _b.bt.danger = %d; _b.bt.sk.slots = %s; _b.bt.sk.cd = 0; _b.g = 0; global.CF = kfo_bot_cfg(%d); %s' % (B, hp, danger, json.dumps(slots), cfg[0], cfg[1]))
    def go():
        sim.run('global.R = kfo_bot_skills(global.kfo.H, %s, global.CF);' % B)
        return J(sim, 'global.R')
    mh = J(sim, B + '.mh')
    # heal: low and safe
    setup([12], int(mh * 0.2), 0, (5, ''))
    ok(go() == 1 and J(sim, B + '.hp') > int(mh * 0.2), 'PERFECT bot at 20%% HP, nothing near: heals (%d -> %d)' % (int(mh * 0.2), J(sim, B + '.hp')))
    # not while a bullet is about to hit (a smart healer waits for a quiet moment)
    setup([12], int(mh * 0.2), 5000, (5, ''))
    ok(go() == 1, 'build 49: low HP: a held heal is used even in danger')
    setup([12], mh - 30, 5000, (5, ''))
    ok(go() == 0, 'a little hurt and in danger: keeps it for a quiet moment')
    setup([12], mh - 90, 0, (1, ''))
    ok(go() == 1, 'hurt by more than the heal gives, nothing near: heals (any skill level)')
    # not when healthy
    setup([12], mh, 0, (5, ''))
    ok(go() == 0, 'full HP: keeps the heal')
    # shield in trouble
    setup([13], mh, 5000, (5, ''))
    ok(go() == 1 and J(sim, B + '.bt.shield') > 0, 'in danger: SHIELD up (%r)' % J(sim, B + '.bt.shield'))
    # charging: PERFECT waits for two draws, draws two
    setup([], mh, 0, (5, ''))
    sim.run('%s.g = 70;' % B)
    go()
    n70 = len(J(sim, B + '.bt.sk.slots'))
    # (a cooldown running: what it drew stays in its hand to be counted - a PERFECT bot plays one at once otherwise)
    sim.run('%s.g = 100; %s.bt.sk.slots = []; %s.bt.sk.cd = 999;' % (B, B, B))
    go()
    n100 = len(J(sim, B + '.bt.sk.slots'))
    ok(n70 == 0 and n100 == 2, 'PERFECT charging: waits at 70 (%d drawn), draws two at 100 (%d)' % (n70, n100))
    setup([], mh, 0, (1, ''))
    sim.run('%s.g = 70;' % B)
    go()
    ok(len(J(sim, B + '.bt.sk.slots')) == 0, 'build 49: EASY charges to the top too (nothing drawn at 70)')
    sim.run('%s.g = 100;' % B)
    go()
    ok(len(J(sim, B + '.bt.sk.slots')) == 2, 'EASY at 100: two skills')
    # targeting mode for a send
    mode = lambda: J(sim, 'kfo_bot_pick_mode(global.kfo.H, %s)' % B)
    sim.run('for (var _i = 0; _i < array_length(global.kfo.H.pl); _i++) { var _p = global.kfo.H.pl[_i]; _p.hp = _p.mh; _p.tg = []; _p.sh = 0; }')
    m0 = mode()
    ok(m0 in (J(sim, 'KBR_TG_CHAOS'), J(sim, 'KBR_TG_ROAR')), 'nothing special: CHAOS (or now and then ROARING) %r' % m0)
    sim.run('var _o = kfo_host_player(%d); _o.hp = round(_o.mh * 0.2);' % bots[1])
    ok(mode() == J(sim, 'KBR_TG_PROCEED'), 'someone at 20% HP: PROCEED (finish them)')
    sim.run('var _o = kfo_host_player(%d); _o.hp = _o.mh;' % bots[1])
    sim.run('kfo_host_player(%d).tg = [%d]; kfo_host_player(%d).tg = [%d];' % (bots[1], b0, J(sim, 'global.kfo.my'), b0))
    ok(mode() == J(sim, 'KBR_TG_DEFEND'), 'two target it: DEFEND (hit back)')
    # an attack: aggression 100 sends the red skill, with the mode set
    sim.run('kfo_host_player(%d).tg = []; kfo_host_player(%d).tg = [];' % (bots[1], J(sim, 'global.kfo.my')))
    setup([red[0]], mh, 0, (5, 'global.CF.aggr = 100;'))
    sent = False
    for _ in range(40):
        sim.run('%s.bt.sk.cd = 0; %s.bt.sk.slots = [%d];' % (B, B, red[0]))
        if go() == 1:
            sent = True
            break
    feed = [x[1] for x in J(sim, 'global.kfo.H.feed')]
    bn = J(sim, B + '.n')
    ok(sent and any(l.startswith('* ' + bn + ' used') for l in feed), 'aggression 100: sends %s (%r)' % (J(sim, 'kbr_skill_name(%d)' % red[0]), feed[-1:]))
    setup([red[0]], mh, 0, (0, ''))
    # (build 50: even a DUMMY sends now and then - about 6% of its looks; build 49 said never)
    na = sum(1 for _ in range(60) if go() == 1)
    ok(na <= 12, 'DUMMY attacks only now and then (%d of 60 looks)' % na)


def part_perf():
    # the bots' thinking in a busy frame: 7 PERFECT bots, time per frame in the emulator, and the 6 ms budget's effect
    sim, e = br_match(open_ok=0, kn=(0,), seed=4950, bots=7, setx='_s.mhp = 999; _s.skills = 0;')
    ok(e is None, 'perf: 7 bots (%s)' % (e,))
    bbox_model.install(sim)
    wrap_tick(sim)
    sim.run('for (var _i = 0; _i < 7; _i++) { var _c = kfo_bot_cfg(5); _c.own = true; global.kfo.H.botcfg[_i] = _c; }')
    sim.run('global.OWE = 0;')
    owe = 0
    for f in range(600):
        sim.run('for (var _i = 0; _i < array_length(global.kfo.H.pl); _i++) { var _b = global.kfo.H.pl[_i]; if (_b.bot) _b.hp = _b.mh; } if (!global.kfo.M.out) global.hp[kbr_char()] = global.maxhp[kbr_char()];')
        step(sim, 1)
        bbox_model.move(sim)
        if f % 30 == 0:
            sim.log.clear()
        sim.run('global.OW = 0; for (var _i = 0; _i < array_length(global.kfo.H.pl); _i++) { var _b = global.kfo.H.pl[_i]; if (_b.bot && is_struct(_b.bt) && _b.bt.owe) global.OW++; }')
        owe += J(sim, 'global.OW')
    STATS['perf'] = {'bot_frames_deferred': owe}
    ok(True, 'perf: %d bot-frames deferred by the 6 ms budget in the emulator (slower than the game)' % owe)


if __name__ == '__main__':
    parts = sys.argv[1:] or ['presets', 'skills', 'dodge']
    t0 = time.time()
    for p in parts:
        globals()['part_' + p]()
    print('STATS', json.dumps(STATS))
    print('PASS' if not FAILS else 'FAIL', N[0] - len(FAILS), '/', N[0], round(time.time() - t0), 's')
    sys.exit(1 if FAILS else 0)
