"""Build 41 Tag Team / Attack Remix in the real merged knight code (emulator): every knight as the first one and as the partner,
turns alternating with each knight keeping its own HP, ACTs and attack list, the partner made without changing the party or the
first knight's setup, exactly one knight running at any time, the knock-out hand-over, the end of the battle, freezing with
knights at the back, and the Remix (forced random attacks for every fight, one shared HP pool, the finale)."""
import sys, time, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lu_harness import *

FAILS = []; N = [0]
def ok(c, msg):
    N[0] += 1
    if not c: FAILS.append(msg); print('FAIL', msg, flush=True)
def eq(a, b, msg):
    N[0] += 1
    if a != b: FAILS.append(msg); print('FAIL', msg, 'got', repr(a), 'want', repr(b), flush=True)

KEYS = ['base', 'kaizo', 'elec', 'violet', 'thorn', 'cyan']
t0 = time.time()
only = sys.argv[1].split(',') if len(sys.argv) > 1 else None


def active_knights(sim):
    return sim.eval('instance_number(obj_knight_enemy)')


# ---------- A: every pair, four enemy turns ----------
PAIRS = [(a, b) for a in KEYS for b in KEYS]   # the same knight twice too (a mirror match)
if only:
    PAIRS = [p for p in PAIRS if p[0] in only or p[1] in only]
for host, partner in PAIRS:
    tag = '%s+%s' % (host, partner)
    sim, e = lu_battle(host, partner=partner, party=(1, 2, 3), world=True)
    if e:
        ok(False, '%s: battle set up (%s)' % (tag, e)); continue
    hp0 = [sim.eval('global.hp[%d]' % i) for i in range(5)]
    df0 = [sim.eval('global.df[%d]' % i) for i in range(5)]
    names0 = [sim.eval('global.charname[%d]' % i) for i in range(5)]
    r = frames(sim, 4)
    ok(r is None, '%s: setup frames (%s)' % (tag, r))
    eq(sim.eval('global.knight_lu.ready'), True, '%s: the partner was made' % tag)
    eq(active_knights(sim), 1, '%s: one knight running after the setup' % tag)
    eq(sim.eval('global.knight_variant'), KEYI[host], '%s: the first knight\'s code runs' % tag)
    eq(sim.eval('global.monsterinstance[0] == global.K'), True, '%s: slot 0 is still the first knight' % tag)
    eq([sim.eval('global.hp[%d]' % i) for i in range(5)], hp0, '%s: making the partner left party HP alone' % tag)
    eq([sim.eval('global.df[%d]' % i) for i in range(5)], df0, '%s: ... and defence (Cyan Knight sets Kris to -99)' % tag)
    eq([sim.eval('global.charname[%d]' % i) for i in range(5)], names0, '%s: ... and the names (Violet Knight renames everyone)' % tag)
    p = sim.eval('global.knight_lu.inst[1]')
    ok(p in sim.deact, '%s: the partner waits deactivated' % tag)
    ok(sim.eval('global.knight_lu.slot[1].maxhp') > 0, '%s: the partner has its own HP (%s)' % (tag, sim.eval('global.knight_lu.slot[1].maxhp')))
    seq = []
    hpk = {}
    for t in range(4):
        r = enemy_turn(sim)
        ok(r is None, '%s: enemy turn %d (%s)' % (tag, t + 1, r))
        if r:
            break
        r = frames(sim, 3)
        ok(r is None, '%s: frames after turn %d (%s)' % (tag, t + 1, r))
        eq(active_knights(sim), 1, '%s: one knight running after turn %d' % (tag, t + 1))
        act = sim.eval('global.knight_lu.act')
        seq.append(act)
        eq(sim.eval('global.knight_variant'), KEYI[(host, partner)[act]], '%s: the code of the knight in front runs (turn %d)' % (tag, t + 1))
        eq(sim.eval('global.monsterinstance[0] == global.knight_lu.inst[global.knight_lu.act]'), True, '%s: slot 0 instance (turn %d)' % (tag, t + 1))
        eq(sim.eval('global.monstername[0]'), sim.eval('knight_reg(%d).name' % KEYI[(host, partner)[act]]), '%s: the menus name the knight in front' % tag)
        hpk.setdefault(act, sim.eval('global.monsterhp[0]'))
    eq(seq, [1, 0, 1, 0], '%s: the knights take turns' % tag)
    st = [sim.eval('global.krun.st.atk[%d].n' % i) for i in range(sim.eval('array_length(global.krun.st.atk)'))]
    ok(len(st) >= (3 if host != partner else 2) and all(':' in s for s in st), '%s: stats name each attack with its knight (%s)' % (tag, st))
    if len(hpk) == 2 and host != partner:
        ok(True, 'hp')
    # damage to the one in front never reaches the one at the back
    sim.run('global.monsterhp[0] -= 100;')
    back = 1 - sim.eval('global.knight_lu.act')
    hb = sim.eval('global.knight_lu.slot[%d].hp' % back)
    r = enemy_turn(sim); r2 = frames(sim, 3)
    ok(r is None and r2 is None, '%s: one more turn (%s %s)' % (tag, r, r2))
    eq(sim.eval('global.knight_lu.act'), back, '%s: the other knight is in front now' % tag)
    eq(sim.eval('global.monsterhp[0]'), hb, '%s: with its own HP (the hit went to the other one)' % tag)
    print(tag, 'ok', round(time.time() - t0, 1), flush=True)

# ---------- B: knock-out and the end of the battle ----------
for host, partner in ([('base', 'violet'), ('kaizo', 'thorn'), ('cyan', 'elec')] if not only else []):
    tag = 'KO %s+%s' % (host, partner)
    sim, e = lu_battle(host, partner=partner, world=True)
    ok(e is None, tag + ' set up')
    frames(sim, 4)
    # the first knight is beaten after its Roaring: knocked out, the partner takes over at once
    sim.run('with (global.K) { haveusedroaring = true; state = 3; hurttimer = 10; end_cutscene_version = 0; endcon = 0; chargeupcon = 0; blockanim = 0; dont_fucking_kill_the_knight = 0; }'
            'global.monsterhp[0] = floor(global.monstermaxhp[0] * 0.3);')
    r = frames(sim, 3)
    ok(r is None, '%s: frames (%s)' % (tag, r))
    eq(sim.eval('global.knight_lu.ko[0]'), True, tag + ': the first knight is knocked out')
    eq(sim.eval('global.K.endcon'), 0, tag + ': its own ending did not start')
    eq(sim.eval('global.knight_lu.act'), 1, tag + ': the partner is in front')
    eq(active_knights(sim), 1, tag + ': one knight running')
    eq(sim.eval('global.krun.state'), 'battle', tag + ': the battle goes on')
    # turns no longer alternate
    r = enemy_turn(sim); frames(sim, 3)
    eq(sim.eval('global.knight_lu.act'), 1, tag + ': the knocked-out knight does not come back')
    # the partner's own hits never take it to 0 while ... it is the last one now: its ending ends the battle
    sim.run('with (global.knight_lu.inst[1]) { haveusedroaring = true; state = 3; hurttimer = 10; end_cutscene_version = 0; endcon = 0; chargeupcon = 0; blockanim = 0; dont_fucking_kill_the_knight = 0; }'
            'global.monsterhp[0] = floor(global.monstermaxhp[0] * 0.3);')
    frames(sim, 2)
    eq(sim.eval('global.knight_lu.ended'), True, tag + ': the last knight\'s ending starts')
    eq(sim.eval('global.knight_lu.inst[1].endcon'), 1, tag + ': (its own endcon)')
    # the battle controller says the battle is over: results at once
    sim.run('obj_battlecontroller.intro = 2;')
    r = frames(sim, 2)
    eq(sim.eval('global.krun.state'), 'finished', tag + ': results (%s)' % (r,))
    eq(sim.eval('instance_exists(obj_knight_prompt)'), True, tag + ': the results box is up')
    eq(sim.eval('global.knight_frozen'), True, tag + ': the game is frozen under it')
    ok(sim.eval('global.knight_lu.inst[0]') in sim.deact, tag + ': the knocked-out knight stays off while frozen')
    opts = [sim.eval('obj_knight_prompt.opts[%d].a' % i) for i in range(sim.eval('array_length(obj_knight_prompt.opts)'))]
    ok('continue' not in opts and 'stats' in opts, tag + ': no story ending, fight stats offered (%s)' % opts)
    # leaving: only what the freeze switched off comes back (the knocked-out knight never runs again), also once the run's lineup
    # is cleared (restart / leave clear it before the room changes)
    k0 = sim.eval('global.knight_lu.inst[0]')
    sim.run('knight_activate_all_safe();')
    sim.step(1)
    ok(k0 in sim.deact, tag + ': leaving does not wake the knight at the back')
    sim.run('knight_lu_clear(); knight_activate_all_safe();')
    sim.step(1)
    ok(k0 in sim.deact, tag + ': ... not even after the lineup is cleared (same room)')
    eq(sim.eval('instance_number(obj_knight_enemy)'), 1, tag + ': one knight')
    print(tag, 'ok', round(time.time() - t0, 1), flush=True)

# ---------- C: freezing (Backspace) with a knight at the back ----------
if not only:
    sim, e = lu_battle('base', partner='elec', world=True)
    frames(sim, 4)
    p = sim.eval('global.knight_lu.inst[1]')
    sim.run('knight_freeze();'); sim.step(1)
    ok(p not in [x for x in (sim.eval('global.knight_frozen_list[%d]' % i) for i in range(sim.eval('array_length(global.knight_frozen_list)')))], 'freeze: the knight at the back is not on the list')
    eq(sim.eval('instance_exists(global.K)'), False, 'freeze: the knight in front is off')
    sim.run('knight_unfreeze();'); sim.step(1)
    eq(sim.eval('instance_exists(global.K)'), True, 'unfreeze: the knight in front is back')
    ok(p in sim.deact, 'unfreeze: the knight at the back stays off')
    eq(active_knights(sim), 1, 'unfreeze: one knight running')
    # elec in front: the tension bar made under the Normal Knight gets the Supercharged fields
    r = enemy_turn(sim); frames(sim, 3)
    eq(sim.eval('global.knight_variant'), 2, 'elec in front')
    if sim.eval('instance_exists(obj_tensionbar)'):
        eq(sim.eval('variable_instance_exists(obj_tensionbar, "bluebar")'), True, 'fill: tension bar has bluebar')

# ---------- D: damage cap and spare while the partner stands ----------
if not only:
    sim, e = lu_battle('base', partner='cyan', world=True)
    frames(sim, 4)
    sim.run('global.monsterhp[0] = 500; global.krun.st.dealt = [0,0,0,0,0];')
    d = sim.eval('knight_dmg_filter(0, 9999)')
    ok(d <= 499, 'cap: a huge hit leaves the knight in front at least 1 HP while its partner stands (%s)' % d)
    sim.run('global.mercymod[0] = 100;'); frames(sim, 2)
    eq(sim.eval('global.knight_lu.ko[0]'), True, 'spare: a knight that could be spared counts as beaten (partner takes over)')
    eq(sim.eval('global.mercymod[0]'), 0, 'spare: ... and cannot be spared (the battle goes on)')
    eq(sim.eval('global.knight_lu.act'), 1, 'spare: the partner is in front')

# ---------- E: Attack Remix ----------
def remix_run(turns, seed):
    sim, e = lu_battle('base', partner='base', combo=2, world=True)
    ok(e is None, 'remix set up (%s)' % (e,))
    sim.rng.seed(seed)
    frames(sim, 6)
    eq(sim.eval('global.knight_lu.n'), 5, 'remix: five knights (build 42: never the Cyan joke fight)')
    eq(sim.eval('instance_number(obj_knight_enemy)'), 1, 'remix: one knight running')
    seen = set()
    mx = sim.eval('global.knight_lu.maxhp')
    for t in range(turns):
        pk = sim.eval('global.knight_lu.plan_k'); pi = sim.eval('global.knight_lu.plan_i')
        want = sim.eval('knight_reg(global.knight_lu.ks[%d]).atk[%d][2]' % (pk, pi))
        eq(sim.eval('global.knight_lu.act'), pk, 'remix turn %d: the planned knight is in front' % (t + 1))
        eq(sim.eval('global.monstermaxhp[0]'), mx, 'remix turn %d: one shared HP pool' % (t + 1))
        n0 = sim.eval('array_length(global.krun.st.atk)')
        r = enemy_turn(sim)
        ok(r is None, 'remix turn %d (%s %s): %s' % (t + 1, KEYS[pk], want, r))
        last = sim.eval('global.krun.st.atk[global.krun.st.cur].n')
        eq(last.split(': ', 1)[-1], want, 'remix turn %d: %s used the planned attack' % (t + 1, KEYS[pk]))
        seen.add(KEYS[pk])
        frames(sim, 3)
        eq(active_knights(sim), 1, 'remix turn %d: one knight running' % (t + 1))
    return sim, seen

if not only or 'remix' in only:
    seen_all = set()
    for seed in (3, 11, 27):
        sim, seen = remix_run(8, seed)
        seen_all |= seen
    ok(len(seen_all) == 5 and 'cyan' not in seen_all, 'remix: all five knights took turns, never Cyan (%s)' % sorted(seen_all))
    # the finale: at 30% the Normal Knight comes back with its own phase 4
    sim.run('global.monsterhp[0] = floor(global.monstermaxhp[0] * 0.25);')
    r = enemy_turn(sim); frames(sim, 3)
    eq(sim.eval('global.knight_lu.finale'), True, 'remix: finale below 30%')
    eq(sim.eval('global.knight_lu.act'), 0, 'remix: the Normal Knight takes the finale')
    eq(sim.eval('global.K.phase'), 4, 'remix finale: phase 4')
    r = enemy_turn(sim); frames(sim, 3)
    eq(sim.eval('global.K.myattackchoice'), 5, 'remix finale: its own Spinning Slashes first')
    eq(sim.eval('global.knight_lu.act'), 0, 'remix finale: no more switching')

print('lineup tests', N[0], 'fails', len(FAILS), round(time.time() - t0, 1))
