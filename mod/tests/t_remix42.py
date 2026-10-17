"""Build 42 Attack Remix knights: Cyan Knight (the joke fight) is never in it, and the player switches knights on and off.
Menu (real input): the REMIX page from the KNIGHT tab, Z / left / right switch a knight, the last one cannot be switched off,
START and C begin, X goes back, the page and the KNIGHT card draw. Settings: sanitizing, saving / loading, the checks for the
knights that are on, the record and START box texts. Battles (emulator, the room's own objects made under the host): the
default five, a joke bit ignored, two knights (never the Normal Knight in the turns, never the same one twice in a row), one
knight, the Normal Knight alone; the Normal Knight always opens and takes the finale."""
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, '/home/claude/work/uiref')
from harness import *
from uiharness import menu_sim
from lu_harness import *
FAILS = []; N = [0]
def ok(c, msg):
    N[0] += 1
    if not c: FAILS.append(msg); print('FAIL', msg, flush=True)
def eq(a, b, msg):
    N[0] += 1
    if a != b: FAILS.append(msg); print('FAIL', msg, 'got', repr(a), 'want', repr(b), flush=True)

t0 = time.time()

# ======================= the menu =======================
sim, rec = menu_sim()
sim.run('knight_store_load(); knight_menu_open();')
U = lambda f: sim.eval('global.knight_ui.' + f)
C = lambda f: sim.eval('global.knight_cfg.' + f)
def frame():
    sim.run('knight_ui_step();'); rec.ops.clear(); sim.run('knight_ui_draw();')
def press(k, n=1):
    for _ in range(n):
        for kk in sim.inp: sim.inp[kk] = 0
        sim.inp[k] = 1; frame(); sim.inp[k] = 0; frame()
        if sim.eval('is_struct(global.knight_ui) && is_struct(global.knight_ui.modal)'):
            frame(); frame()
for _ in range(12): frame()
eq(C('rmask'), 31, 'default: the five knights that are not a joke fight (bits 0-4)')
press('ok'); press('up', 2); eq(U('krow'), 9, 'ATTACK REMIX row (build 43: ONLINE is the last row)')
desc = sim.eval('knight_ui_desc()')
ok('pick' in desc.lower(), 'the KNIGHT page says Z picks the knights (%s)' % desc)
press('ok')
eq(U('sub'), 'remix', 'Z opens the REMIX page')
eq(C('combo'), 2, '... with Attack Remix selected')
rows = sim.py(sim.eval('knight_ui_remix_rows()'))
eq(rows, [0, 1, 2, 3, 4], 'the page lists Normal, Kaizo, Supercharged, Violet, Thorn - no Cyan')
eq(U('rmx_row'), 0, 'cursor on the first knight')
press('ok'); eq(C('rmask'), 30, 'Z switches the Normal Knight off')
ok('normal' in sim.eval('knight_ui_desc()').lower(), 'the description names the knight under the cursor')
press('ok'); eq(C('rmask'), 31, 'Z again: on')
press('right'); eq(C('rmask'), 30, 'right switches too')
press('left'); eq(C('rmask'), 31, 'left switches too')
# switch everything off but Thorn
for r in range(4):
    press('ok'); press('down')
eq(C('rmask'), 16, 'only Thorn left on')
eq(sim.eval('is_real(global.knight_cfg.rmask)'), True, 'the switches are stored as plain numbers (build 43: a bitwise result is an int64, which reads back as 0)')
eq(U('rmx_row'), 4, 'cursor on Thorn')
press('ok'); eq(C('rmask'), 16, 'the last knight cannot be switched off')
ok('least one' in str(sim.eval('global.knight_ui.warn')).lower(), 'a warning says why (%s)' % sim.eval('global.knight_ui.warn'))
press('up'); press('ok'); eq(C('rmask'), 24, 'Violet back on (Violet + Thorn)')
press('down', 2); eq(U('rmx_row'), 5, 'START row')
press('ok')
eq(sim.eval('is_struct(global.knight_ui.modal) ? global.knight_ui.modal.k : ""'), 'launch', 'START opens the START box')
lines = sim.py(sim.eval('global.knight_ui.modal.lines'))
ok(any(l.startswith('Knights: VIOLET, THORN') for l in lines), 'the START box lists the knights (%s)' % lines)
ok(any('Normal Knight takes the finale' in l for l in lines), 'and says who takes the finale (%s)' % lines)
eq(sim.py(sim.eval('global.knight_launch.plan')), [0], 'the Normal Knight hosts the battle')
press('back'); eq(sim.eval('is_struct(global.knight_ui.modal)'), False, 'X closes the box')
eq(U('sub'), 'remix', '... back on the REMIX page')
press('alt'); eq(sim.eval('is_struct(global.knight_ui.modal) ? global.knight_ui.modal.k : ""'), 'launch', 'C starts from the REMIX page too')
press('back'); press('back'); eq(U('sub'), '', 'X leaves the REMIX page')
# drawing: the page in every state, the KNIGHT card with knights off, the caption
for r in range(6):
    sim.run('global.knight_ui.sub = "remix"; global.knight_ui.rmx_row = %d;' % r)
    rec.ops.clear(); sim.run('knight_ui_draw();')
    ok(len(rec.ops) > 10, 'REMIX page row %d draws' % r)
eq(sim.eval('knight_capf("REMIX")'), 17, 'its caption is frame 17 of the hub captions')
sim.run('global.knight_ui.sub = "";')

# ======================= settings =======================
s3 = make_sim()
s3.run('knight_store_load(); var _c = knight_cfg_default(); _c.rmask = 63; knight_cfg_sanitize(_c); global.C = _c;')
eq(s3.eval('global.C.rmask'), 31, 'sanitize: the joke fight bit is dropped')
for m, want in ((0, 31), (32, 31), (-5, 31), (18, 18), (1, 1)):
    s3.run('var _c = knight_cfg_default(); _c.rmask = %d; knight_cfg_sanitize(_c); global.C = _c;' % m)
    eq(s3.eval('global.C.rmask'), want, 'sanitize %d -> %d' % (m, want))
eq(s3.py(s3.eval('knight_remix_list({ rmask: 18 })')), [0, 1, 4], 'Kaizo + Thorn: the Normal Knight first (opens and takes the finale)')
eq(s3.py(s3.eval('knight_remix_list({ rmask: 8 })')), [0, 3], 'Violet alone')
eq(s3.py(s3.eval('knight_remix_list({ rmask: 1 })')), [0], 'the Normal Knight alone')
eq(s3.py(s3.eval('knight_remix_list({ rmask: 31 })')), [0, 1, 2, 3, 4], 'all five')
# saved with the last-used settings and with presets
s3.run('var _c = knight_cfg_default(); _c.combo = 2; _c.rmask = 18; global.knight_cfg = _c; knight_store_save(); global.knight_cfg = knight_cfg_default(); global.knight_loaded = false; knight_store_load();')
eq(s3.eval('global.knight_cfg.rmask'), 18, 'the knights are remembered (last-used settings)')
s3.run('var _c = knight_cfg_default(); _c.combo = 2; _c.rmask = 18; global.PR = knight_cfg_to_preset(_c, "test"); global.PR.spells = ""; global.PR.equip = ""; global.PD = knight_preset_decode(global.PR);')
eq(s3.eval('global.PD.cfg.rmask'), 18, 'presets keep the knights')
# checks follow the knights that are on
s3.run('var _c = knight_cfg_default(); _c.combo = 2; _c.c_notp = 1; global.R = knight_resolve(_c);')
eq(s3.eval('global.R.ok'), False, 'No TP is refused while Supercharged Knight is in the Remix (its UNLEASH needs TP)')
s3.run('var _c = knight_cfg_default(); _c.combo = 2; _c.c_notp = 1; _c.rmask = 27; global.R = knight_resolve(_c);')
eq(s3.eval('global.R.ok'), True, '... and allowed with Supercharged switched off')
s3.run('var _c = knight_cfg_default(); _c.combo = 2; _c.c_nohit = 1; global.R = knight_resolve(_c);')
eq(s3.eval('global.R.ok'), True, 'No-Hit is fine (no joke fight in the Remix any more)')
s3.run('var _c = knight_cfg_default(); _c.combo = 2; _c.rmask = 18; global.RR = knight_run_new({ src: _c, cfg: _c, plan: [0], reveal: "", corr: [] });')
eq(s3.eval('knight_run_rec_key(global.RR)'), 'remix', 'records: the Remix table')
ok(s3.eval('knight_cfg_text(global.RR.cfg)').startswith('KAIZO+THORN '), 'records: the knights are noted when not all are on (%s)' % s3.eval('knight_cfg_text(global.RR.cfg)'))
s3.run('var _c = knight_cfg_default(); _c.combo = 2; global.RR = knight_run_new({ src: _c, cfg: _c, plan: [0], reveal: "", corr: [] });')
ok(not s3.eval('knight_cfg_text(global.RR.cfg)').startswith('NORMAL+'), 'records: nothing extra with all five on')
s3.run('var _c = knight_cfg_default(); _c.combo = 2; _c.rmask = 18; global.BR = knight_cfg_brief(_c);')
ok('(KAIZO, THORN)' in s3.eval('global.BR'), 'the short text names them (%s)' % s3.eval('global.BR'))
print('remix menu/settings', N[0], 'fails', len(FAILS), round(time.time() - t0, 1), flush=True)

# ======================= battles =======================
KN = ['base', 'kaizo', 'elec', 'violet', 'thorn', 'cyan']


def remix(mask, seed=5):
    extra = '' if mask is None else '_c.rmask = %d;' % mask
    sim, e = lu_battle('base', partner='base', combo=2, extra_cfg=extra, world=True)
    ok(e is None, 'remix %s: set up (%s)' % (mask, e))
    sim.rng.seed(seed)
    r = frames(sim, 6)
    ok(r is None, 'remix %s: first frames (%s)' % (mask, r))
    return sim


def turns(sim, n, tag):
    seq = []
    for t in range(n):
        pk = sim.eval('global.knight_lu.plan_k')
        eq(sim.eval('global.knight_lu.act'), pk, '%s turn %d: the planned knight is in front' % (tag, t + 1))
        seq.append(KN[sim.eval('global.knight_lu.ks[%d]' % pk)])
        r = enemy_turn(sim)
        ok(r is None, '%s turn %d (%s): %s' % (tag, t + 1, seq[-1], r))
        if r:
            break
        r = frames(sim, 3)
        ok(r is None, '%s after turn %d: %s' % (tag, t + 1, r))
        eq(sim.eval('instance_number(obj_knight_enemy)'), 1, '%s turn %d: one knight running' % (tag, t + 1))
    return seq


def finale(sim, tag):
    sim.run('global.monsterhp[0] = floor(global.monstermaxhp[0] * 0.25);')
    r = enemy_turn(sim); frames(sim, 3)
    eq(sim.eval('global.knight_lu.finale'), True, '%s: finale below 30%%' % tag)
    eq(sim.eval('global.knight_lu.act'), 0, '%s: the Normal Knight takes the finale' % tag)
    eq(KN[sim.eval('global.knight_variant')], 'base', '%s: its own code runs' % tag)
    eq(sim.eval('global.K.phase'), 4, '%s finale: phase 4' % tag)


# the default: five knights, never Cyan
seen = set()
for seed in (3, 11):
    sim = remix(None, seed)
    eq(sim.eval('global.knight_lu.n'), 5, 'default: five knights in the battle')
    eq(sim.py(sim.eval('global.knight_lu.ks')), [0, 1, 2, 3, 4], 'default: Normal, Kaizo, Supercharged, Violet, Thorn')
    seq = turns(sim, 8, 'default s%d' % seed)
    seen |= set(seq)
    ok(all(a != b for a, b in zip(seq, seq[1:])), 'default s%d: never the same knight twice in a row (%s)' % (seed, seq))
ok('cyan' not in seen, 'default: Cyan Knight never steps in (%s)' % sorted(seen))
ok(len(seen) >= 4, 'default: the knights take turns (%s)' % sorted(seen))
finale(sim, 'default')

# an old setting with the joke bit: still no Cyan
sim = remix(63)
eq(sim.py(sim.eval('global.knight_lu.ks')), [0, 1, 2, 3, 4], 'joke bit set: Cyan is still left out')

# two knights without the Normal Knight: it opens, steps out before the first enemy turn, and only comes back for the finale
sim = remix(18)
eq(sim.py(sim.eval('global.knight_lu.ks')), [0, 1, 4], 'Kaizo + Thorn: the Normal Knight hosts')
eq(sim.py(sim.eval('global.knight_lu.inpool')), [0, 1, 1], '... but is not in the turns')
ok(sim.eval('global.knight_lu.act') != 0, 'the Normal Knight steps out before the first enemy turn')
seq = turns(sim, 6, 'kaizo+thorn')
ok(set(seq) <= {'kaizo', 'thorn'} and len(seq) == 6, 'only Kaizo and Thorn take the turns (%s)' % seq)
ok(all(a != b for a, b in zip(seq, seq[1:])), 'they alternate (%s)' % seq)
finale(sim, 'kaizo+thorn')

# one knight: Violet every turn, random attacks, then the Normal Knight's finale
sim = remix(8)
eq(sim.py(sim.eval('global.knight_lu.ks')), [0, 3], 'Violet alone: the Normal Knight hosts')
seq = turns(sim, 4, 'violet')
eq(seq, ['violet'] * 4, 'Violet takes every turn')
names = [sim.eval('global.krun.st.atk[%d].n' % i) for i in range(sim.eval('array_length(global.krun.st.atk)'))]
ok(all(n.startswith('VIOLET: ') for n in names), 'the stats name Violet attacks (%s)' % names)
finale(sim, 'violet')

# the Normal Knight alone: no second knight is made at all
sim = remix(1)
eq(sim.eval('global.knight_lu.n'), 1, 'Normal alone: one knight')
seq = turns(sim, 3, 'normal')
eq(seq, ['base'] * 3, 'it takes every turn')
finale(sim, 'normal')

print('remix42 tests', N[0], 'fails', len(FAILS), round(time.time() - t0, 1))
sys.exit(1 if FAILS else 0)
