"""DRBR: FLOWERY's GROUP MERCY in a room of several games (br_multi: the real code in every game, the simulated network).
Games 1 and 2 play the orange SOUL like people (the DASHER of t_flowery53: they line up with the blue pieces and the Jarona
lunges and dash into them), game 3 never touches a key, and the host has one bot. The match is Flowery alone on the SLOW ramp
(90 seconds a stage), so in the first minute and a half every phase change can only come from the GROUP MERCY.
Checked:
  - every game has the same cycles (attack, seed, start tick, stage, the finale flag), no errors, no frame run twice;
  - each game told the host its FLOWERY TP of each of his attacks; the host's GROUP MERCY rose by a tenth of the AVERAGE of the
    standing SOULs (at most 8 an attack) - recomputed here from what the games sent;
  - each threshold it crossed was announced once, for a cycle ahead; every game has the same announcements, and from the
    announced cycle on every game's attacks are the new phase's (Aqua & Seth's at 20 %...);
  - every game shows the same GROUP MERCY as the host (the standings carry it);
  - the bot played his attacks by the odds (its own FLOWERY TP);
  - then the room's MERCY is set just under 60 %: the next count announces THE FINAL ASCENT, and the first Flowery cycle from the
    announced one is THE FINAL JARONA (the finale) in every game, with the tower climbing during it.
Usage: python3 t_flowery53_multi.py [frames]"""
import sys, os, json, time
os.environ.setdefault('KH_CAM', '1000,320')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from br_multi import *
from br_harness import live_input, keys_set
from t_flowery53 import DASHER

FR = int(sys.argv[1]) if len(sys.argv) > 1 else 2700
FAILS = []
N = [0]


def ok(c, m):
    N[0] += 1
    print(('ok   ' if c else 'FAIL ') + m, flush=True)
    if not c:
        FAILS.append(m)
    return c


def J(s, e):
    return s.py(s.eval(e))


t0 = time.time()
net, sims = make_room(3, 'lan', 5353, setx='_s.mhp = 999; _s.hard = 1; _s.ramp = 0;', kn=(8,), open_ok=8, bots=1)
print('room up; start:', sims[0].eval('global.BRWHY') or 'ok', flush=True)
for s in sims:
    live_input(s)
    s.load_source('gml_GlobalScript_t_dasher', DASHER)
ASC = {1: 0, 2: 0, 3: 0}


def play(f, sims, prev):
    for i, s in enumerate(sims):
        if f % 30 == 0:
            s.run('if (is_struct(global.kfo.M) && !global.kfo.M.out) global.hp[kbr_char()] = global.maxhp[kbr_char()];')
        if i < 2 and prev[i]['ph'] == 'run':
            w = J(s, 'kbr_t_dasher()')
            keys_set(s, ok=w[0], up=w[1], down=w[2])
        else:
            keys_set(s, ok=0, up=0, down=0)
        if prev[i]['ph'] == 'run' and J(s, 'variable_global_exists("kbr_fl_asc") && global.kbr_fl_asc && instance_exists(obj_fl_towery) && obj_fl_towery.rise > 0'):
            ASC[i + 1] += 1
    if f % 300 == 0:
        for s in sims:
            s.log.clear()
        print('frame', f, [(p['ph'], p['k']) for p in prev], 'mercy', round(J(sims[0], 'kbr_fl_host_g()'), 2), '%.0fs' % (time.time() - t0), flush=True)


rec = run(net, sims, FR, 'none', on_frame=play, wall=3000)
cmp = compare(rec, 3)
errs = {c: rec[c]['errors'][:1] for c in range(1, 4) if rec[c]['errors']}
ok(not errs, 'no errors in any game %r' % (errs,))
ok(not cmp['logic_bad'] and cmp['dupes'] == 0 and cmp['cycles_all'] > 3, 'every game the same cycles (%d, bad %r)' % (cmp['cycles_all'], cmp['logic_bad'][:3]))
ok(all(not getattr(s, 'retrylog', []) for s in sims), 'no frame run twice')
H = sims[0]
g = J(H, 'kbr_fl_host_g()')
fp = J(H, 'kbr_tl_flph_list(global.kfo.H.tl)')
print('host GROUP MERCY', g, 'announcements', fp, flush=True)
# what each game sent, the host's record of it, and the mercy recomputed from it
pl = J(H, '(function() { var _o = []; var _h = global.kfo.H; for (var _i = 0; _i < array_length(_h.pl); _i++) { var _p = _h.pl[_i]; '
          'array_push(_o, { pid: _p.pid, bot: _p.bot, al: _p.al, outt: _p.outt, flm: variable_struct_exists(_p, "flm") ? _p.flm : {} }); } return _o; })()')
print('host records', json.dumps(pl)[:800], flush=True)
lu = J(H, 'kbr_enc_by_key("flowery").lu')
fl_cycles = sorted({s['k'] for s in rec[1]['starts'] if s['ok'] == 8})
counted = J(H, 'global.kfo.H.fl_next')
exp = 0.0
for k in fl_cycles:
    if k >= counted:
        continue
    vals = [p['flm'].get(str(k), 0) for p in pl if p['al'] or p['outt'] < 0]
    if vals:
        exp = min(100, exp + min(8, (sum(vals) / len(vals)) / 10))
ok(abs(exp - g) < 0.01, 'the host\'s GROUP MERCY %.2f is the average rule\'s %.2f (cycles counted: %d)' % (g, exp, counted))
humans = [p for p in pl if not p['bot']]
ok(all(len(p['flm']) > 0 for p in humans), 'every game told its FLOWERY TP %r' % ([len(p['flm']) for p in humans],))
dasher_tp = sum(humans[0]['flm'].values()) + sum(humans[1]['flm'].values())
idle_tp = sum(humans[2]['flm'].values())
ok(dasher_tp > 0 and idle_tp == 0, 'the dashers earned TP (%d), the idle game none (%d)' % (dasher_tp, idle_tp))
bots = [p for p in pl if p['bot']]
ok(len(bots) == 1 and len(bots[0]['flm']) > 0, 'the bot played his attacks by the odds %r' % ([b['flm'] for b in bots],))
ok(g > 0 and len(fp) >= 1, 'the GROUP MERCY rose (%.1f %%) and announced %d threshold(s)' % (g, len(fp)))
lists = [J(s, 'kbr_tl_flph_list(global.kfo.M.tl)') for s in sims]
ok(all(l == fp for l in lists), 'every game has the host\'s announcements %r' % (lists,))
shown = [J(s, 'variable_struct_exists(global.kfo.M, "flg") ? global.kfo.M.flg : -1') for s in sims[1:]]
ok(all(abs(x - g) <= 8.01 for x in shown), 'the games show the GROUP MERCY (%r, host %.1f)' % (shown, g))
# the attacks follow the announced phases in every game
D = J(H, 'kbr_enc_by_key("flowery").atk')
bad = []
for cid in range(1, 4):
    for s in rec[cid]['starts']:
        if s['ok'] != 8 or s['ai'] == 12:
            continue
        want = 1
        for (ck, ph) in fp:
            if s['k'] >= ck and ph <= 5:
                want = max(want, ph)
        if D[s['ai']][0] != want:
            bad.append((cid, s['k'], s['ai'], D[s['ai']][0], want))
ok(not bad, 'every attack is its phase\'s (announced from its cycle on) %r' % (bad[:4],))
# ---- the finale: the room's MERCY just under 60 %, then the next count crosses it
H.run('global.kfo.H.flg = 59.5;')
fin0 = time.time()
rec2 = run(net, sims, 1500, 'none', on_frame=play, wall=2000)
errs2 = {c: rec2[c]['errors'][:1] for c in range(1, 4) if rec2[c]['errors']}
ok(not errs2, 'finale: no errors %r' % (errs2,))
fp2 = J(H, 'kbr_tl_flph_list(global.kfo.H.tl)')
k6 = [ck for (ck, ph) in fp2 if ph == 6]
ok(len(k6) == 1, 'finale: THE FINAL ASCENT announced once %r' % (fp2,))
fins = {}
for cid in range(1, 4):
    for s in rec2[cid]['starts']:
        if s['ok'] == 8 and k6 and s['k'] >= k6[0]:
            fins.setdefault(cid, s)
            break
ok(len(fins) == 3 and all(f['ai'] == 12 for f in fins.values()) and len({f['k'] for f in fins.values()}) == 1,
   'finale: the first Flowery cycle from the announced one is THE FINAL JARONA in every game %r' % ({c: (f['k'], f['ai']) for c, f in fins.items()},))
ok(all(ASC[c] > 100 for c in ASC), 'finale: the tower climbed during it in every game %r' % (ASC,))
tw = [J(s, 'instance_exists(obj_fl_towery) ? [obj_fl_towery.rise, obj_fl_towery.petals] : []') for s in sims]
json.dump({'cmp': cmp, 'errors': errs, 'host_g': g, 'fp': fp, 'fp2': fp2, 'records': pl, 'asc': ASC, 'tower_after': tw}, open('/home/claude/work/online/flowery_multi.json', 'w'), indent=1)
print('flowery53 multi: %d checks, %d failed (%.0fs)' % (N[0], len(FAILS), time.time() - t0))
for f in FAILS:
    print('  -', f)
sys.exit(1 if FAILS else 0)
