"""Build 50: the KNIGHT tab's chapter pages (LEFT / RIGHT) and the planned bosses (COMING SOON), with real menu input;
the online roster table (kbr_roster) and its join signature."""
import sys
sys.path.insert(0, '/home/claude/work/uiref')
from harness import *
from uiharness import menu_sim
FAILS = []; N = [0]
def ok(c, msg):
    N[0] += 1
    if not c: FAILS.append(msg); print('FAIL', msg)
def eq(a, b, msg):
    N[0] += 1
    if a != b: FAILS.append(msg); print('FAIL', msg, 'got', repr(a), 'want', repr(b))

sim, rec = menu_sim()
sim.run('knight_store_load(); knight_menu_open();')
U = lambda f: sim.eval('global.knight_ui.' + f)
def frame():
    sim.run('knight_ui_step();'); rec.ops.clear(); sim.run('knight_ui_draw();')
def press(k, n=1):
    for _ in range(n):
        for kk in sim.inp: sim.inp[kk] = 0
        sim.inp[k] = 1; frame(); sim.inp[k] = 0; frame()
        if sim.eval('is_struct(global.knight_ui) && is_struct(global.knight_ui.modal)'):
            frame(); frame()
def labels():
    sim.run('global.LB = []; var _f = knight_ui_fights(); for (var _i = 0; _i < array_length(_f); _i++) array_push(global.LB, knight_ui_fight_label(_f[_i]));')
    n = sim.eval('array_length(global.LB)')
    return [sim.eval('global.LB[%d]' % i) for i in range(int(n))]

for _ in range(12): frame()
# build 52: the chapters whose bosses are only planned are hidden (KNIGHT_SHOW_PLANNED false): one page, the knights
eq(sim.eval('knight_page_count()'), 1, 'one chapter page shown (the planned chapters are hidden behind KNIGHT_SHOW_PLANNED)')
eq(sim.eval('array_length(global.knight_pages)'), 4, 'their pages are still in the registry (nothing deleted)')
eq(sim.eval('array_length(global.knight_planned)'), 6, 'and their planned bosses too')
eq(sim.eval('knight_page_title(global.knight_ui.kpage)'), 'CHAPTER 3', 'it is the Chapter 3 page (the knights)')
k3 = labels()
# (DRBR 1.0.1: ONLINE is the menu's own first page - not a row here)
ok(k3[-4:] == ['KNIGHT RUSH', 'RANDOM', 'TAG TEAM', 'ATTACK REMIX'] and len(k3) == 10 and 'ONLINE' not in k3, 'Chapter 3 page: 6 knights + 4 modes %r' % k3)
ok(not any(l in k3 for l in ('JEVIL', 'KING', 'SPAMTON NEO', 'QUEEN', 'TITAN', 'GERSON')), 'no COMING SOON rows')
eq(sim.eval('knight_page_of_ch(4)'), 0, 'a hidden chapter has no page of its own (the first page)')
# (DRBR 1.0.1: the menu opens on ONLINE, its first page; RIGHT on the top bar goes to KNIGHT)
eq([U('tab'), U('focus')], [5, 0], 'the menu opens on ONLINE (its first page), on the top bar')
press('right')
eq(U('tab'), 0, 'RIGHT on the top bar: KNIGHT')
press('ok')
eq(U('focus'), 1, 'into the KNIGHT page')
press('right')
eq(sim.eval('knight_page_title(global.knight_ui.kpage)'), 'CHAPTER 3', 'RIGHT turns the carousel, not the page')
eq(U('krow'), 1, 'RIGHT: the next knight (KAIZO)')
press('ok')
eq(sim.eval('global.knight_cfg.knight'), 1, 'Chapter 3 still picks its knights (Kaizo)')
# every registry knight has a chapter
eq([sim.eval('knight_chapter_of(%d)' % k) for k in range(int(sim.eval('knight_count()')))], [3] * int(sim.eval('knight_count()')), 'every knight is on the Chapter 3 page')
# online roster table
# (DRBR: the five bosses follow the six knights - rows 6-10)
eq(sim.eval('kbr_ok_count()'), 11, 'online roster: 6 knights + 5 bosses')
eq([sim.eval('kbr_ok_short(%d)' % k) for k in range(6)], ['NORMAL', 'KAIZO', 'ELECKNIGHT', 'VIOLET', 'THORN', 'KNIGHTMARE'], 'online names as before')
eq([sim.eval('kbr_reg_of(%d)' % k) for k in range(6)], [0, 1, 2, 3, 4, 0], 'online ids run the same registry knights as before')
eq([sim.eval('kbr_ok_valid(%d)' % k) for k in range(12)], [True] * 11 + [False], 'all eleven valid, nothing past the table')
eq([sim.eval('kbr_nightmare(%d)' % k) for k in range(6)], [False] * 5 + [True], 'Knightmare is the nightmare row')
sim.run('global.KD = kfo_set_default();')
eq([sim.eval('global.KD.kn[%d]' % i) for i in range(6)], [0, 1, 2, 3, 4, 5], 'default: every online knight in the match')
eq([sim.eval('global.KD.kw[%d]' % i) for i in range(6)], [3, 3, 3, 3, 3, 2], 'default weights as before')
sim.run('global.KP = kbr_kw_with([2, 9, 3]);')
eq([sim.eval('global.KP[%d]' % i) for i in range(6)], [2, 9, 3, 3, 3, 2], 'a preset shorter than the roster: the rest from the defaults')
ok(sim.eval('string_length(kbr_roster_sig())') > 10, 'roster signature for joining a room: %s' % sim.eval('kbr_roster_sig()'))
print('pages50 tests', N[0], 'fails', len(FAILS)); sys.exit(1 if FAILS else 0)
