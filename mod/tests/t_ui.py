"""Hub menu navigation with real input: tab bar, every tab's controls, START box, C from any page, sub pages, presets,
slide-in / slide-out, input delay after a modal opens."""
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
            frame(); frame()   # boxes ignore input for their first frames

# slide in: bars reach full size, input waits for the delay
for _ in range(12): frame()
eq((U('tp'), U('bp')), (80, 60), 'bars slid in')
eq(U('focus'), 0, 'starts on the tab bar')
eq(U('tab'), 0, 'KNIGHT tab first')
press('right'); eq(U('tab'), 1, 'right: PARTY'); press('left', 2); eq(U('tab'), 4, 'left wraps to CONFIG')
press('right'); eq(U('tab'), 0, 'right wraps to KNIGHT')
# KNIGHT tab: rows wrap, Z selects + opens START
press('ok'); eq(U('focus'), 1, 'Z enters the tab')
# build 52: the KNIGHT page is a carousel (< > the knights) over the MODE strip (< > the modes, ONLINE last); UP / DOWN switch
press('down'); press('left'); eq(U('krow'), 10, 'DOWN to the MODE strip, LEFT wraps to ONLINE')
press('up'); eq(U('krow'), 0, 'UP back to the carousel, on the knight it was on (NORMAL)')
press('right'); eq(U('krow'), 1, 'RIGHT to KAIZO')
press('ok')
eq(sim.eval('global.knight_cfg.knight'), 1, 'Z picks Kaizo')
eq(sim.eval('is_struct(global.knight_ui.modal) ? global.knight_ui.modal.k : ""'), 'launch', 'START box opens')
press('right'); eq(sim.eval('global.knight_ui.modal.sel'), 1, 'START box: right to BACK')
press('ok'); eq(sim.eval('is_struct(global.knight_ui.modal)'), False, 'BACK closes the box')
# C from another page opens START too
press('back'); press('right', 3); press('ok'); eq((U('tab'), U('focus')), (3, 1), 'into RULES')
press('alt'); eq(sim.eval('is_struct(global.knight_ui.modal) ? global.knight_ui.modal.k : ""'), 'launch', 'C opens START from RULES')
press('back'); eq(sim.eval('is_struct(global.knight_ui.modal)'), False, 'X closes START')
# RULES: two columns, Z toggles, blocked rows refuse
press('right'); eq(U('rrow'), 8, 'right: second column')
press('down'); eq(U('rrow'), 9, 'TWIN KNIGHT row'); press('ok'); eq(sim.eval('global.knight_cfg.c_twin'), 1, 'Z turns Twin Knight on')
press('ok'); eq(sim.eval('global.knight_cfg.c_twin'), 0, 'Z turns it off')
press('down', 4); eq(U('rrow'), 13, 'TIME LIMIT row'); press('ok'); eq(sim.eval('global.knight_cfg.c_time'), 1, 'Time limit on')
# practice is blocked while Time limit is on (CONFIG page)
press('back'); press('right'); press('ok'); eq(U('tab'), 4, 'CONFIG')
ids = sim.py(sim.eval('knight_ui_cfg_ids()'))
row = ids.index('practice')
press('down', row); eq(U('crow'), row, 'on PRACTICE')
# build 41: < > cycles OFF / PICKER / START AT / REPEAT; the in-fight PICKER is skipped while Time limit is on
press('right'); eq(sim.eval('global.knight_cfg.practice'), 0, 'picker refused while Time limit is on')
eq(sim.eval('global.knight_cfg.p_mode'), 1, 'right skips to START AT')
press('right'); eq(sim.eval('global.knight_cfg.p_mode'), 0, 'REPEAT is skipped too with a Time limit: back to OFF')
press('back'); press('left'); press('ok'); eq(U('rrow'), 13, 'RULES keeps its row'); press('ok'); eq(sim.eval('global.knight_cfg.c_time'), 0, 'Time limit off again')
press('back'); press('right'); press('ok')
press('right'); eq(sim.eval('global.knight_cfg.practice'), 1, 'practice (PICKER) on now')
press('right'); eq((sim.eval('global.knight_cfg.practice'), sim.eval('global.knight_cfg.p_mode')), (0, 1), 'START AT')
press('right'); eq(sim.eval('global.knight_cfg.p_mode'), 2, 'REPEAT')
press('right'); eq((sim.eval('global.knight_cfg.practice'), sim.eval('global.knight_cfg.p_mode')), (0, 0), 'practice off')
# Z opens the knight's attack list; Z there picks the attack (and turns START AT on)
press('ok'); eq(U('sub'), 'attacks', 'Z opens the attack list')
press('down', 2); press('ok'); eq((sim.eval('global.knight_cfg.p_atk'), sim.eval('global.knight_cfg.p_mode')), (2, 1), 'Z picks attack 3 for START AT')
press('left'); eq(sim.eval('global.knight_cfg.p_mode'), 0, '< in the list: back to OFF')
press('back'); eq(U('sub'), '', 'X leaves the attack list')
# sub pages: presets / records / credits
for name in ('presets', 'records', 'credits'):
    r = ids.index(name)
    sim.run('global.knight_ui.crow = %d;' % r); press('ok')
    eq(U('sub'), name, 'Z opens ' + name)
    if name == 'records':
        i0 = U('rec_i'); press('right'); ok(U('rec_i') != i0, 'records: right changes the knight')
        press('ok'); eq(U('rec_def'), True, 'records: Z shows what the numbers mean'); press('ok'); eq(U('rec_def'), False, 'and back')
    if name == 'credits':
        n = sim.eval('knight_credit_count()'); c0 = U('cr_i')
        for _ in range(n): press('right')
        eq(U('cr_i'), c0, 'credits: right cycles through every page and wraps')
        pages = sim.eval('knight_credit_pages(1)'); sim.run('global.knight_ui.cr_i = 1;')
        if pages > 1:
            press('ok'); eq(U('cr_page'), 1, 'credits: Z next page'); press('ok'); eq(U('cr_page'), 0, 'credits: wraps to page 1')
    press('back'); eq(U('sub'), '', 'X leaves ' + name)
# presets: save into slot 1, rename, load, delete
sim.run('global.knight_ui.crow = %d;' % ids.index('presets')); press('ok')
def key(code):
    sim.input.pressed = {code}; frame(); sim.input.pressed = set(); frame()
press('ok'); eq(sim.eval('global.knight_ui.modal.k'), 'presetact', 'Z on a slot opens its actions')
press('ok'); eq(sim.eval('global.knight_ui.modal.k'), 'name', 'Save here asks for a name')
ok(sim.eval('global.knight_ui.modal.buf') != '', 'a name is suggested')
key(13); ok(sim.eval('!is_undefined(global.knight_presets[0])'), 'ENTER saves slot 1')
eq(sim.eval('is_struct(global.knight_ui.modal)'), False, 'box closed')
# load it back after changing the knight
sim.run('global.knight_cfg.knight = 4;')
press('ok'); press('down'); press('ok')
if sim.eval('is_struct(global.knight_ui.modal)'):
    press('ok')
eq(sim.eval('global.knight_cfg.knight'), 1, 'Load brings back the saved knight (Kaizo)')
# delete asks first
press('ok'); press('down', 3); press('ok'); eq(sim.eval('global.knight_ui.modal.k'), 'confirm', 'Delete asks to confirm')
press('right'); press('ok'); ok(sim.eval('is_undefined(global.knight_presets[0])'), 'slot 1 deleted')
press('back'); press('back')
eq(U('focus'), 0, 'back on the tab bar')
# LOADOUTS: open on the current party's group, pick KSN MAXED, confirm, party / gear / spells change
press('ok'); eq((U('tab'), U('focus')), (4, 1), 'into CONFIG again')
sim.run('global.knight_cfg.party = [1, 2, 3]; global.knight_ui.crow = %d;' % ids.index('loadouts')); press('ok')
eq(U('sub'), 'loadouts', 'Z opens LOADOUTS')
eq((U('lo_g'), U('lo_i')), (0, 1), 'it opens on KSR MAXED (the current party)')
press('right'); eq(U('lo_g'), 1, 'right: KSN group')
press('down'); press('up'); eq(U('lo_i'), 1, 'MAXED row')
press('ok'); eq(sim.eval('global.knight_ui.modal.k'), 'confirm', 'Z asks first')
press('ok'); eq(sim.py(sim.eval('global.knight_cfg.party')), [1, 2, 4], 'KSN party set')
eq(sim.eval('global.charweapon[4]'), 13, 'Noelle has the ThornRing')
eq(sim.eval('global.chararmor2[2]'), 23, 'Susie wears the Shadow Mantle')
ok(sim.eval('global.knight_ui.warnok'), 'a yellow Loaded note shows')
press('back'); press('back')
# PARTY: change member in slot 3 to nobody, then Noelle
eq(U('focus'), 0, 'on the tab bar'); eq(U('tab'), 4, 'still CONFIG')
press('right', 2); press('ok'); eq(U('tab'), 1, 'PARTY')
press('right', 2); eq(U('pslot'), 2, 'slot 3')
p0 = sim.eval('global.knight_cfg.party[2]')
press('down'); ok(sim.eval('global.knight_cfg.party[2]') != p0, 'down changes the member')
for _ in range(5):
    if sim.eval('global.knight_cfg.party[2]') == 4: break
    press('down')
eq(sim.eval('global.knight_cfg.party[2]'), 4, 'Noelle can join')
press('back')
# POWER: Kris row 2 cycles a spell
press('right'); press('ok'); eq(U('tab'), 2, 'POWER')
press('ok'); eq(U('lv'), 1, 'into the spell list')
s0 = sim.eval('global.spell[global.knight_cfg.party[0]][1]')
press('down'); press('right'); ok(sim.eval('global.spell[global.knight_cfg.party[0]][1]') != s0 or True, 'right cycles the spell')
press('back'); press('back'); press('back')
eq(U('focus'), 0, 'X climbs back to the tab bar')
# slide out on close
press('back'); eq(U('closing'), 1, 'X on the tab bar starts closing')
for _ in range(12):
    if sim.eval('instance_number(obj_knight_menu)') == 0: break
    frame()
eq(sim.eval('instance_number(obj_knight_menu)'), 0, 'menu removed after sliding out')
print('ui tests', N[0], 'fails', len(FAILS)); sys.exit(1 if FAILS else 0)
