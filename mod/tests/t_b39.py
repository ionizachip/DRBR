"""Build 39: (1) the Weird Route's scenes on the knights without a Side B also start when a strong party already has the knight at its
Roaring gate before halfway / 3/4 of the list (the smoother pacing lets a very strong party reach the Roaring a little early; the
scenes come before it instead of never); (2) Ralsei keeps his own hatless battle sprites in the Violet finisher scenes (the Chapter 1
hat set spr_ralseib_* is never used); (3) the pacing has no hard stop at the gate (no 0-damage hits). Real merged GML in the emulator."""
import sys, os, time
SRC = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'retired', 't_wr38_build38_takings.py')).read()
exec(SRC[:SRC.index('t0 = time.time()')])   # setup(), scene(), end_turn(), ok(), eq() from the build 38 Weird Route test
t0 = time.time()

def turn_end(sim, eturns, hp):
    sim.run('global.krun.eturns = %d; global.monsterhp[0] = %d; global.mnfight = 2; global.myfight = 0;' % (eturns, hp))
    return auto(sim, lambda: sim.run('with (global.K) scr_mnendturn();'))

# --- (build 48: the Normal Knight never takes anyone - these run on the Supercharged Knight, the same pacing gate)
# --- elec trio: early turn, above the gate: nothing; at the gate: the Knight takes the bottom member now
sim = setup('elec', [1, 2, 3])
eq((sim.eval('global.krun.wr.at'), sim.eval('global.krun.wr.at2')), (9, 13), 'elec: halfway 9, 3/4 at 13')
turn_end(sim, 2, 6000)
eq(sim.eval('global.krun.wr.st'), 0, 'elec turn 2, knight above its gate (80% = 5840): no scene yet')
eq(sim.eval('knight_wr_gate_now()'), False, 'gate check: 6000 > 5840')
good, err = turn_end(sim, 3, 5840)
ok(good, 'end of turn at the gate runs (%s)' % err)
eq(sim.eval('knight_wr_gate_now()'), True, 'gate check: 5840 <= 5840')
eq(sim.eval('global.krun.wr.st'), 1, 'elec turn 3 at the gate: the scene starts before the Roaring')
eq(sim.eval('global.krun.wr.vic'), 3, 'elec KSR: the bottom member (Ralsei)')
err = scene(sim)
ok(err is None, 'scene runs (%s)' % err)
ok(sim.eval('global.hp[3]') < 0 and sim.eval('global.krun.wr.done'), 'Ralsei is lost, once')
turn_end(sim, 4, 5700)
eq(sim.eval('global.krun.wr.st'), 9, 'three members: no second scene at the gate either')

# --- base duo: first loss at the gate, then the lone member's parry at the next turn end (still before the Roaring)
sim = setup('elec', [1, 2, 0])
turn_end(sim, 3, 5800)
eq((sim.eval('global.krun.wr.st'), sim.eval('global.krun.wr.vic')), (1, 2), 'elec KS at the gate: Susie (bottom) is taken')
err = scene(sim)
ok(err is None, 'KS scene runs (%s)' % err)
eq((sim.eval('global.krun.wr.st'), sim.eval('global.krun.wr.dfl')), (9, False), 'the parry does not chain onto the loss (it waits for the next enemy turn)')
sim.texts.clear()
turn_end(sim, 4, 5700)
eq(sim.eval('global.krun.wr.st'), 21, 'elec KS, next turn end still at the gate (before 3/4): the Knight charges Kris')
err = scene(sim)
ok(err is None, 'parry scene runs (%s)' % err)
ok(sim.eval('global.hp[1]') > 0 and any('knocked the Knight' in x for x in sim.texts), 'Kris parries and stays up (%s)' % sim.texts)
eq((sim.eval('global.krun.wr.dfl'), sim.eval('global.krun.wr.st')), (True, 9), 'parried once')

# --- the other knights without a Side B
# build 48: the Normal Knight (Chapter 3's own fight) never takes a party member, at the gate or past halfway
sim = setup('base', [1, 2, 3])
eq(sim.eval('global.krun.wr.on'), False, 'base: the Weird Route scenes are off for the Normal Knight')
turn_end(sim, 3, 5840)
turn_end(sim, 9, 3000)
eq(sim.eval('global.krun.wr.st'), 0, 'base: no scene at the gate or past halfway')
ok(sim.eval('global.hp[3]') > 0 and sim.eval('global.hp[2]') > 0, 'base: nobody is lost')
for key, hp in (('elec', 5840), ('thorn', 3650), ('cyan', 7300)):
    sim = setup(key, [1, 2, 3])
    turn_end(sim, 1, hp)
    want = 0 if key == 'cyan' else 1
    eq(sim.eval('global.krun.wr.st'), want, '%s turn 1 at HP %d: %s' % (key, hp, 'no pacing list (joke fight): halfway only' if key == 'cyan' else 'the scene starts at the gate'))

# --- never: after the Roaring, in practice, on Kaizo / Violet (their own Side B), with the Weird Route off
sim = setup('elec', [1, 2, 3])
sim.run('global.K.haveusedroaring = true;')
turn_end(sim, 3, 5000)
eq(sim.eval('global.krun.wr.st'), 0, 'after the Roaring: no scene')
for key, kw, why in (('base', {'practice': 1}, 'practice'), ('base', {'weird': 0}, 'weird off'), ('kaizo', {}, 'kaizo'), ('violet', {}, 'violet')):
    sim = setup(key, [1, 2, 3], **kw)
    turn_end(sim, 2, 1000)
    eq(sim.eval('global.krun.wr.st'), 0, '%s: no Weird Route scene even under the gate' % why)

# --- Ralsei's sprites in the Violet finisher scenes (the scene itself runs in t_weird38)
eq(sim.eval('knight_vb_ready_sprite(3)'), sim.eval('spr_ralsei_spellready'), "Ralsei's power-up stance: his own spell-ready sprite (no hat)")
eq(sim.eval('knight_vb_idle_sprite(3)'), sim.eval('spr_ralsei_idle'), "Ralsei's stance after it: his own idle sprite (no hat)")
CORE = open(M + 'gml_GlobalScript_knight_core.gml', encoding='utf8').read()
CODE = '\n'.join(l.split('//')[0] for l in CORE.split('\n'))
eq(CODE.count('spr_ralseib'), 0, 'the hub never uses the Chapter 1 hat sprites (spr_ralseib_*)')

# --- pacing: no hard stop at the gate any more
F = CORE[CORE.index('function knight_dmg_filter_raw('):]  # build 41: the filter is a wrapper (lineup cap + stats) around the raw pacing filter
F = F[:F.index('\n}\n')]
ok('_gate + 1' not in F and 'knight_pace_soft' in F, 'the filter has no gate + 1 stop, it uses the smooth slowdown')
print('b39 tests', N[0], 'fails', len(FAILS), '%.0fs' % (time.time() - t0)); sys.exit(1 if FAILS else 0)
