"""DRBR 1.0.3 - your report: "weird bug kicked me out the room, round is still ongoing but it said out". Reproduced: after a hit
put you OUT (your SOUL hidden, 1 HP kept so the battle never sees the party fall), a piece that sets the invincibility itself
(Spamton NEO's final forme grabbing the SOUL, his heart attack) still touched the hidden SOUL; the room's rules took nothing
from that hit (0) but Chapter 3's damage scripts make every hit at least 1 - the last HP went, the game's party-down check
ended the run and the OUT box sent you back to the room while the round went on. Practice matches against Spamton NEO, the
real collisions (collide.py), HP set low:
  - OUT by a hit, then 900 frames of his attacks touching the hidden SOUL: still in the battle (watching), HP 1, no OUT box,
    the knightfights_debug.log note names the piece that hit;
  - the same while typing in the chat (the watcher's invincibility used to stop there);
  - a hit a SHIELD takes costs no HP (it cost 1), HOW TO PLAY's last HP stays;
  - his finale's proportional hits (scr_damage_proportional, obj_sn_bulletfin) are online hits now: at 1 HP one puts you OUT
    and you watch (it took the party down and ended the run);
  - the party falling any other way (knight_defeat_begin) in a running match: OUT and watching, not the OUT box.
Usage: python3 t_out103.py"""
import sys, os, json, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('KH_CAM', '2063,0')
import br_harness
br_harness.COLLIDE = True
from br_harness import *

FAILS = []
N = [0]


def ok(c, msg):
    N[0] += 1
    print(('ok   ' if c else 'FAIL ') + msg, flush=True)
    if not c:
        FAILS.append(msg)
    return c


def J(s, e):
    return s.py(s.eval(e))


INFO = '[global.kfo.M.R.ph, global.hp[kbr_char()], global.kfo.M.out, global.krun.state, instance_number(obj_knight_prompt), global.kfo.M.ended]'


def match(atk, seed, row=9):
    sim, e = br_match(open_ok=row, kn=(row,), seed=seed, bots=2, setx='_s.mhp = 150; _s.skills = 1;')
    if e:
        return None
    sim.run('global.BS_FORCE = %d;' % atk)
    sim.run('with (obj_battlecontroller) if (!variable_instance_exists(id, "mercytotal")) mercytotal = 0;')
    sim.load_source('gml_GlobalScript_bsforce', 'function kbr_tl_pick_attack(_tl, _k, _g, _ok, _st) { return global.BS_FORCE; }\n')
    sim.run('global.kfo.M.tl.cyc = []; global.kfo.H.tl.cyc = [];')
    notes = []
    sim.mock('kh_dbg_write', lambda s, l, *a: (notes.append(s.py(l)), 0)[1])
    sim.notes = notes
    return sim


def until_out(sim, hp=14, frames=3000):
    for f in range(frames):
        if sim.eval('global.kfo.M.R.ph') == 'run' and not sim.eval('global.kfo.M.out'):
            sim.run('if (global.hp[kbr_char()] > %d) global.hp[kbr_char()] = %d;' % (hp, hp))
        err = step(sim, 1)
        if err:
            return err
        if sim.eval('global.kfo.M.out'):
            return None
    return 'never OUT'


def watch(sim, frames, typing=False):
    worst = None
    for f in range(frames):
        if typing:
            sim.mock('kfo_chat_typing', lambda s, *a: True)
        err = step(sim, 1)
        if err:
            return err, worst
        st = J(sim, INFO)
        if st[3] != 'battle' or st[4] > 0 or st[1] < 1:
            worst = st
            break
    return None, worst


# ---- 1. OUT by a hit, then his attacks go on touching the hidden SOUL (the reported case: Spamton NEO, stage-2 attacks)
for atk, seed in ((3, 5933), (10, 5934), (7, 5935)):
    sim = match(atk, seed)
    ok(sim is not None, 'Spamton NEO attack %d: the practice match starts' % atk)
    if sim is None:
        continue
    err = until_out(sim)
    ok(err is None, 'attack %d: a hit at 14 HP puts you OUT (%s)' % (atk, err or 'ok'))
    if err:
        continue
    note = [l for n in sim.notes for l in n if 'OUT:' in l]
    ok(len(note) == 1 and 'a hit emptied your HP (obj_sn_' in note[0], 'attack %d: the debug log names the piece that hit (%r)' % (atk, note[:1]))
    hits0 = J(sim, 'global.kfo.M.hits')
    err, worst = watch(sim, 900)
    st = J(sim, INFO)
    ok(err is None and worst is None and st[3] == 'battle' and st[4] == 0 and st[1] >= 1,
       'attack %d: 900 frames on, still watching the battle - HP %r, run %r, OUT box %r (worst %r) %s' % (atk, st[1], st[3], st[4], worst, (err or '')[:120]))

# ---- 2. the same while typing in the chat (watching)
sim = match(3, 5936)
err = until_out(sim)
if not err:
    err, worst = watch(sim, 900, typing=True)
    st = J(sim, INFO)
    ok(err is None and worst is None and st[3] == 'battle' and st[1] >= 1 and J(sim, 'global.inv') > 1000,
       'typing in the chat while watching: untouchable (inv %r), still watching (HP %r, run %r)' % (J(sim, 'global.inv'), st[1], st[3]))
else:
    ok(False, 'typing case: OUT first (%s)' % err)

# ---- 3. a SHIELD's hit costs nothing; HOW TO PLAY's last HP stays
sim = match(0, 5937)
for f in range(600):
    step(sim, 1)
    if sim.eval('global.kfo.M.R.ph') == 'run':
        break
sim.run('global.hp[kbr_char()] = 60; global.kfo.M.sk.shield = 3; global.kfo.M.sk.shield_t = 300;')
h0 = J(sim, 'global.hp[kbr_char()]')
sim.run('global.inv = -1; with (obj_heart) { with (instance_create(x, y, obj_regularbullet)) { kbr_bullet_contract(1); damage = 30; target = 0; scr_damage(); instance_destroy(); } }')
h1 = J(sim, 'global.hp[kbr_char()]')
ok(h1 == h0 and J(sim, 'global.kfo.M.sk.shield') == 2, 'a SHIELD takes a hit and it costs no HP (HP %r -> %r, shield %r)' % (h0, h1, J(sim, 'global.kfo.M.sk.shield')))
sim.run('global.kfo.M.sk.shield = 0; global.kfo.M.sk.shield_t = 0;')
sim.run('global.hp[kbr_char()] = 1;')
sim.mock('kfo_tut_on', lambda s, *a: True)
sim.run('global.inv = -1; with (obj_heart) { with (instance_create(x, y, obj_regularbullet)) { kbr_bullet_contract(1); damage = 30; target = 0; scr_damage(); instance_destroy(); } }')
ok(J(sim, 'global.hp[kbr_char()]') == 1 and not J(sim, 'global.kfo.M.out') and J(sim, 'global.krun.state') == 'battle',
   'HOW TO PLAY at 1 HP: a hit leaves the 1 HP (HP %r, OUT %r, run %r)' % (J(sim, 'global.hp[kbr_char()]'), J(sim, 'global.kfo.M.out'), J(sim, 'global.krun.state')))

# ---- 4. his finale's proportional hit (obj_sn_bulletfin -> scr_damage_proportional) at 1 HP: OUT and watching
sim = match(0, 5938)
for f in range(600):
    step(sim, 1)
    if sim.eval('global.kfo.M.R.ph') == 'run':
        break
sim.run('global.hp[kbr_char()] = 40;')
sim.run('global.inv = -1; with (obj_heart) { with (instance_create(x, y, obj_sn_bulletfin)) { kbr_bullet_contract(1); target = 0; active = 1; scr_damage_proportional(); instance_destroy(); } }')
hp1 = J(sim, 'global.hp[kbr_char()]')
want = J(sim, '(function(){ var _t = kbr_hit_dmg(kbr_hit_kind(obj_sn_bulletfin), false); return 40 - round(_t[0] * (global.kfo.M.eff.dmul / 100)); })()')
ok(hp1 == want, 'a proportional hit at 40 HP takes the room\'s damage (HP 40 -> %r, the table says %r)' % (hp1, want))
sim.run('global.hp[kbr_char()] = 1;')
sim.run('global.inv = -1; with (obj_heart) { with (instance_create(x, y, obj_sn_bulletfin)) { kbr_bullet_contract(1); target = 0; active = 1; scr_damage_proportional(); instance_destroy(); } }')
st = J(sim, INFO)
ok(st[2] and st[3] == 'battle' and st[4] == 0 and st[1] >= 1, 'a proportional hit at 1 HP: OUT, watching (OUT %r, run %r, OUT box %r, HP %r)' % (st[2], st[3], st[4], st[1]))
note = [l for n in sim.notes for l in n if 'OUT:' in l]
ok(any('obj_sn_bulletfin' in l for l in note), 'the note names Spamton\'s finale bullet (%r)' % note[-1:])

# ---- 5. the party falls some other way in a running match (the game's own party-down check): OUT and watching
sim = match(0, 5939)
for f in range(600):
    step(sim, 1)
    if sim.eval('global.kfo.M.R.ph') == 'run':
        break
sim.run('global.hp[kbr_char()] = -5; scr_dead(0); knight_defeat_begin();')
st = J(sim, INFO)
ok(st[2] and st[3] == 'battle' and st[4] == 0 and st[1] == 1 and J(sim, 'global.chardead[0]') == 0,
   'the party-down check in a running match: OUT and watching (OUT %r, run %r, OUT box %r, HP %r, dead %r)' % (st[2], st[3], st[4], st[1], J(sim, 'global.chardead[0]')))
note = [l for n in sim.notes for l in n if 'OUT:' in l]
ok(any('party-down check' in l for l in note), 'the note says how (%r)' % note[-1:])
err, worst = watch(sim, 300)
ok(err is None and worst is None, '300 frames on: still watching (%r) %s' % (worst, (err or '')[:100]))
sim.run('global.hp[kbr_char()] = -5; scr_dead(0); knight_defeat_begin();')
st = J(sim, INFO)
ok(st[3] == 'battle' and st[4] == 0 and st[1] == 1, 'again while watching: still watching (run %r, OUT box %r, HP %r)' % (st[3], st[4], st[1]))

print('\n%d checks, %d failed' % (N[0], len(FAILS)))
for f in FAILS:
    print('  FAIL', f)
sys.exit(1 if FAILS else 0)
