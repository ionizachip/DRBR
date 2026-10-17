"""Fight pacing (knight_dmg_filter) and the battle rules' bookkeeping: schedule line, the smooth slowdown ahead of the line (build 39:
no hard stop at the gate, so no MISS), no fall before the Roaring, catch-up, practice/joke/after-Roaring pass-through, Supercharged
phasing, Violet Side B after the Roaring (damage shows, the Knight stays at 8%), Kaizo guard divisor, turn counter, Time limit,
Thorns, Hyper speed, HUD lines, and whole fights for weak..absurd parties on every knight (never a 0-damage hit)."""
from harness import *
FAILS = []; N = [0]
def eq(a, b, msg):
    N[0] += 1
    if a != b:
        FAILS.append(msg); print('FAIL', msg, 'got', repr(a), 'want', repr(b))
def ok(c, msg):
    eq(bool(c), True, msg)

sim = make_sim()
for o in ('obj_heart', 'obj_knight_twin', 'obj_knight_twin_bullet', 'obj_knight_roaring2', 'obj_growtangle'):
    try: sim.define_object(o)
    except Exception: pass
sim.define_globals(monsterhp=[7300, 0, 0], monstermaxhp=[7300, 0, 0], mnfight=0, turntimer=0, knight_variant=0, monsterdf=[0, 0, 0])
sim.run("global.hp[6] = 0; global.maxhp[6] = 0;")  # (build 50: character 5, Flowery, has HP too)
sim.mock('scr_havechar', lambda s, c: 1 if c in (1, 2, 3) else 0)
sim.run('global.room_speed_v = 30;')

def setup(k, cfg='', hp=None, sideb=None):
    mx = {0: 7300, 1: 10000, 2: 7300, 3: 7300, 4: 7305, 5: 7600}[k]
    sim.run('with (obj_knight_enemy) instance_destroy();')
    sim.run('global.knight_variant = %d; global.knight_run = 1; global.char = [1,2,3];'
            'global.krun = knight_run_new({src: knight_cfg_default(), cfg: knight_cfg_default(), plan: [%d], reveal: ""});'
            'global.krun.state = "battle"; global.monstermaxhp[0] = %d; global.monsterhp[0] = %d; %s' % (k, k, mx, hp if hp is not None else mx, cfg))
    sim.run('var _e = instance_create(0, 0, obj_knight_enemy); _e.haveusedroaring = false; _e.damagereduction = 0.2; _e.phase = 1;')
    if sideb is not None:
        sim.run('obj_knight_enemy.%s = %s;' % sideb)
    return mx

def f(d):
    return sim.eval('knight_dmg_filter(0, %d)' % d)

# --- Normal Knight: gate 80%, list 15 turns. Turn 0 schedule line = 7300 * (1 - 0.2/15) = 7202
mx = setup(0)
eq(f(50), 50, 'under the line: full damage')
eq(f(98), 98, 'exactly to the line: full damage')
eq(f(300), 98 + 65, 'over the line: the part below starts at 35% and eases off (98 + ceil(340.5 * ln(1 + 0.35 * 202 / 340.5)) = 163)')
# deep into the list, far ahead of the line: 5% of the hit, never 0 (build 38 stopped the knight at gate + 1 -> MISS)
sim.run('global.krun.eturns = 10; global.monsterhp[0] = 5845;')
eq(f(1000), 50, 'far ahead of the line: 5% (no stop at gate + 1 any more)')
eq(f(3), 1, 'far ahead of the line: a tiny hit still deals 1, never MISS')
sim.run('global.monsterhp[0] = 5841;')
eq(f(450), 23, 'at gate + 1 before the end of the list: still 5% (build 38: 0 = MISS)')
sim.run('global.krun.eturns = 14; global.monsterhp[0] = 5845;')
eq(f(4), 4, 'last listed turn: HP may reach the gate exactly')
eq(f(6000), 5 + 301, 'last listed turn: past the line the slowdown is at its strongest (5 + ceil(1.95 + 0.05 * 5978))')
sim.run('global.krun.eturns = 20; global.monsterhp[0] = 3000;')
eq(f(5000), 2853, 'past the list, before the Roaring: the last 5% (365) counts less (2635 + ceil(218))')
sim.run('global.monsterhp[0] = 400;')
eq(f(5000), 383, 'before the Roaring: deep in the last 5% the hit still lands and leaves HP')
sim.run('global.monsterhp[0] = 2;')
eq(f(50), 1, 'before the Roaring: a hit always leaves the knight 1 HP')
sim.run('obj_knight_enemy.haveusedroaring = true; global.monsterhp[0] = 3000;')
eq(f(5000), 5000, 'after the Roaring the fight decides (first damaging hit ends it)')
# catch-up for slow parties: past the list and still above the gate
setup(0)
sim.run('global.krun.eturns = 20; global.monsterhp[0] = 6500;')
eq(f(100), 160, 'catch-up: 5 turns past the list -> x1.6')
sim.run('global.krun.eturns = 40;')
eq(f(100), 200, 'catch-up capped at x2')
sim.run('global.monsterhp[0] = 5000;')
eq(f(100), 100, 'no catch-up once under the gate')
# practice / joke / not a hub run
setup(0, 'global.krun.practice = true;')
eq(f(3000), 3000, 'practice: untouched')
setup(5)
eq(f(3000), 3000, 'Cyan (joke, no list): untouched')
sim.run('global.knight_run = 0;')
eq(f(3000), 3000, 'outside a hub run: untouched')
setup(0, 'global.krun.state = "won";')
eq(f(3000), 3000, 'after the battle: untouched')

# --- Kaizo: gate 60% of 10000 over 27 turns; X-Slash / FireShock share the guard divisor
setup(1)
eq(f(100), 100, 'Kaizo turn 0: 10000*(1-0.4/27)=9851 -> 100 is fine')
sim.run('obj_knight_enemy.kaizo_block = 1; obj_knight_enemy.damagereduction = 0.2;')
eq(round(sim.eval('knight_kaizo_div()'), 3), 4.5, 'Kaizo guard divisor with Susie up: 6 - 0.2*7.5 = 4.5')
sim.run('obj_knight_enemy.kaizo_block = 0;')
eq(sim.eval('knight_kaizo_div()'), 1, 'guard down: divisor 1')
setup(0)
eq(sim.eval('knight_kaizo_div()'), 1, 'other knights: divisor 1')

# --- Supercharged phasing: nothing gets through
setup(2, '', None, ('phasing', 'true'))
eq(f(500), 0, 'phasing: 0')
sim.run('obj_knight_enemy.phasing = false;')
eq(f(50), 50, 'not phasing: normal')

# --- Violet: Side A gate 65% / 22 turns, Side B 13% / 27 turns; Side B after the Roaring only the finisher
setup(3, '', None, ('v_sideb', 'true'))
eq(sim.eval('knight_side_b()'), True, 'side B detected')
eq((sim.eval('knight_pace_now(3).gate'), sim.eval('knight_pace_now(3).tmin')), (0.13, 27), 'Side B pace')
sim.run('obj_knight_enemy.haveusedroaring = true;')
eq(f(500), 500, 'Violet Side B after the Roaring: the hit shows its damage (build 38: 0 = MISS)')
sim.run('global.monsterhp[0] = 584;')
eq(f(5000), 583, 'Violet Side B after the Roaring: never the last HP (the finisher ends the fight, not a plain win)')
sim.run('global.monsterhp[0] = 100;')
eq(f(500), 500, "Violet Side B after the Roaring: the mod's 8% floor comes back first (as it does every frame)")
eq(sim.eval('global.monsterhp[0]'), 584, "Violet Side B after the Roaring: HP put back to 8% (7300 * 0.08) before the hit")
setup(3, '', None, ('v_sideb', 'false'))
eq((sim.eval('knight_pace_now(3).gate'), sim.eval('knight_pace_now(3).tmin')), (0.65, 22), 'Side A pace')
sim.run('obj_knight_enemy.haveusedroaring = true;')
eq(f(500), 500, 'Violet Side A after the Roaring: normal')

# --- Thorn: 7305 * 0.5 = 3652.5 -> the gate must be reachable (floor, not ceil)
setup(4)
sim.run('global.krun.eturns = 19; global.monsterhp[0] = 3700;')
eq(f(48), 48, 'Thorn: HP can reach 3652 <= 3652.5 on the last listed turn (floor, not ceil)')
sim.run('global.krun.eturns = 18; global.monsterhp[0] = 3700;')
eq(f(100), 5, 'Thorn turn 18: 135 under the line (3835), past its 89-HP ease-off: a 100 hit counts 5%')
sim.run('global.monsterhp[0] = 3660;')
eq(f(100), 5, 'Thorn turn 18: 8 HP over the gate: still 5 (no stop at gate + 1)')

# --- turn counter, Time limit, Thorns, speed
setup(0, 'global.krun.cfg.c_time = 1; global.krun.cfg.c_thorns = 1; global.krun.party = [1,2,3];')
sim.run('global.hp[1] = 90; global.maxhp[1] = 90; global.hp[2] = 110; global.maxhp[2] = 110; global.hp[3] = 140; global.maxhp[3] = 140; global.mnfight = 0;')
sim.run('knight_ch_begin(global.krun);')
sim.run('knight_ch_tick(global.krun);')
eq(sim.eval('global.krun.tlimit'), 25, 'Time limit for Normal: 15 + 10')
ok('WIN WITHIN 25 TURNS' in sim.eval('global.krun.reveal'), 'banner names the limit')
for t in range(3):
    sim.run('global.mnfight = 2; knight_ch_tick(global.krun); global.mnfight = 0; knight_ch_tick(global.krun);')
eq(sim.eval('global.krun.eturns'), 3, 'three enemy turns counted')
sim.run('global.hp[1] = 75; knight_ch_tick(global.krun);')
eq(sim.eval('global.maxhp[1]'), 90, 'Thorns: HP lost without a hit (ThornRing drain, ...) does not count')
sim.run('global.hp[1] = 90; knight_ch_tick(global.krun);')
sim.run('global.hp[1] = 60; global.krun.thhit[1] = true; knight_ch_tick(global.krun);')
eq(sim.eval('global.maxhp[1]'), 81, 'Thorns: 30 lost -> max HP 90 - 9 = 81')
sim.run('global.hp[1] = 1; global.krun.thhit[1] = true; knight_ch_tick(global.krun);')
eq(sim.eval('global.maxhp[1]'), 63, 'Thorns: 59 lost -> -18 = 63')
sim.run('global.hp[1] = 0; global.maxhp[1] = 31; global.krun.thprev[1] = 31; global.hp[1] = 0; global.krun.thhit[1] = true; knight_ch_tick(global.krun);')
eq(sim.eval('global.maxhp[1]'), 30, 'Thorns: never under a third of the max HP at the start (90 / 3 = 30)')
lines = sim.eval('knight_hud_lines()').data
ok(any(l.startswith('TURN 3 OF 25') for l in lines), 'HUD turn line')
ok(any('THORNS' in l for l in lines), 'HUD rule tag')
sim.run('global.krun.eturns = 25; global.mnfight = 0; knight_ch_tick(global.krun);')
sim.mock('knight_fight_commit', lambda s, *a: 0)
sim.mock('knight_rush_finish', lambda s, *a: 0)
sim.run('global.mnfight = 2; knight_ch_tick(global.krun);')
eq(sim.eval('global.krun.state'), 'failed', 'turn 26 starts: Time limit lost')
eq(sim.eval('global.krun.result'), 'time', 'result "time"')
ok(any('TIME UP' in l for l in sim.eval('knight_hud_lines()').data), 'HUD shows TIME UP')
# a Roaring in progress is never cut short
setup(0, 'global.krun.cfg.c_time = 1;')
sim.run('knight_ch_begin(global.krun); knight_ch_tick(global.krun); global.krun.eturns = 25; obj_knight_enemy.haveusedroaring = true; global.mnfight = 0; knight_ch_tick(global.krun); global.mnfight = 2; knight_ch_tick(global.krun);')
eq(sim.eval('global.krun.state'), 'battle', 'no Time limit loss once the Roaring has started')
eq(sim.eval('knight_turn_limit(1, false)'), 37, 'Kaizo limit 27 + 10')
eq(sim.eval('knight_turn_limit(3, true)'), 37, 'Violet Side B limit 27 + 10')
eq(sim.eval('knight_turn_limit(5, false)'), 30, 'Cyan (no list): 20 + 10')

# --- whole fights: every knight (and Violet Side B), parties from FIGHT-only to absurd; the Roaring starts at the end of the
# first enemy turn at or under the gate. Never a 0-damage hit (MISS) before it, the knight never falls before it.
PARTIES = {'fightonly': [15, 20, 10], 'medium': [250, 250, 20, 10], 'strong': [450, 450, 330, 300], 'huge': [900, 900, 700, 600, 600],
           'absurd': [3000, 3000, 3000]}
KN = [(0, 'normal', None), (1, 'kaizo', None), (2, 'super', ('phasing', 'false')), (3, 'violetA', ('v_sideb', 'false')), (3, 'violetB', ('v_sideb', 'true')), (4, 'thorn', None)]
ROAR = {}
for k, nm, sb in KN:
    for pn, hits in PARTIES.items():
        mx = setup(k, '', None, sb)
        tm = sim.eval('knight_pace_now(%d).tmin' % k); gate = sim.eval('floor(%d * knight_pace_now(%d).gate)' % (mx, k))
        zero = 0; low = 99999; roar = None; hp = mx
        for turn in range(tm + 12):
            sim.run('global.krun.eturns = %d;' % turn)
            for h in hits:
                d = f(h)
                if d <= 0: zero += 1
                low = min(low, d)
                sim.run('global.monsterhp[0] -= %d;' % d)
            hp = sim.eval('global.monsterhp[0]')
            if hp <= mx * sim.eval('knight_pace_now(%d).gate' % k):
                roar = turn; break
        ROAR[(nm, pn)] = roar
        eq(zero, 0, '%s %s: no 0-damage hit before the Roaring' % (nm, pn))
        ok(hp >= 1, '%s %s: the knight is still up at its Roaring (%s)' % (nm, pn, hp))
        if pn == 'medium':
            eq(roar, tm - 1, '%s medium party: the Roaring comes right after the last listed turn' % nm)
        if pn == 'strong':
            ok(roar is not None and roar >= tm - 6, '%s strong party: at most 5 turns early (gate at turn %s, list %d)' % (nm, roar, tm))
        if pn == 'fightonly':
            ok(roar is None or roar >= tm, '%s FIGHT-only party: never early (%s)' % (nm, roar))
print('roaring turns:', ROAR)

print('pacing tests', N[0], 'fails', len(FAILS)); sys.exit(1 if FAILS else 0)
