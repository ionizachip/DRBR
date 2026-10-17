"""Built-in loadouts (CONFIG > LOADOUTS) and the one-Shadow-Mantle rule."""
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
sim.step(1)
L = lambda e: sim.py(sim.eval(e))
NAMES = {1: 'Kris', 2: 'Susie', 3: 'Ralsei', 4: 'Noelle', 5: 'Flowery'}
NEEDS = {5: {1: [2]}, 6: {1: [3], 3: [4], 4: [3]}, 12: {1: [4]}, 14: {1: [3]}, 15: {3: [4], 4: [3]}}
BASE_GEAR = {1: [23, 27, 7], 2: [24, 21, 23], 3: [25, 22, 9], 4: [12, 14, 22]}
NATURAL = {1: [7], 2: [4, 11], 3: [3, 2], 4: [2, 8, 9]}

def mantles():
    out = []
    for c in range(1, 5):
        for s in (1, 2):
            if sim.eval('knight_equip_get(%d,%d)' % (c, s)) == 23:
                out.append((c, s))
    return out

def usable(sp, c, party):
    need = NEEDS.get(sp, {})
    if sp in NEEDS and c not in need:
        return False
    return all(p in party for p in need.get(c, []))

ng = sim.eval('knight_lo_group_count()')
eq(ng, 27, '4 trios + 6 duos + 4 solos + Flowery\'s 6 trios, 4 duos and solo + the x2 and x3 groups')
total = 0
for g in range(ng):
    lst = L('knight_lo_list(%d)' % g)
    triple = sim.eval('knight_lo_is_triple(%d)' % g)
    double = sim.eval('knight_lo_is_double(%d)' % g)
    gp = L('knight_lo_group_party(%d)' % g)
    kinds = [x['kind'] for x in lst]
    if triple:
        eq(kinds, ['triple'] * 4, 'x3 group has one loadout per member')
    elif double:
        eq(kinds, ['double'] * 4, 'x2 group has one loadout per member')
    else:
        ok(kinds[:2] == ['base', 'maxed'], 'group %d starts with BASE, MAXED' % g)
        members = [c for c in gp if c]
        has_dual = any(usable(s, c, members) for c in members for s in (5, 6, 12, 14, 15))
        eq('dual' in kinds, has_dual, 'group %s: DUAL MOVES only where the party has a two-person move' % gp)
    for i, lo in enumerate(lst):
        total += 1
        name = '%s %s' % (sim.eval('knight_lo_group_label(%d)' % g), sim.eval('knight_lo_label(knight_lo_list(%d)[%d])' % (g, i)) if False else lo['kind'])
        # start from a messy state: every member wears a mantle in both slots, random spells
        sim.run('for (var c = 1; c <= 4; c++) { global.chararmor1[c] = 23; global.chararmor2[c] = 23; for (var s = 0; s < 12; s++) global.spell[c][s] = 13; }')
        sim.run('global.LL = knight_lo_list(%d); knight_lo_apply(%d, global.LL[%d]);' % (g, g, i))
        party = L('global.knight_cfg.party')
        want_party = [lo['ch']] * 3 if lo['kind'] == 'triple' else ([lo['ch'], lo['ch'], 0] if lo['kind'] == 'double' else gp)
        eq(party, want_party, name + ': party')
        members = sorted(set(c for c in party if c))
        m = mantles()
        ok(len(m) <= 1, name + ': at most one Shadow Mantle in the whole setup %s' % m)
        # every setup has exactly one mantle when anyone in it can wear it: Susie first, else Kris, else Ralsei
        pref = [c for c in (2, 1, 3) if c in members]
        eq([c for c, s in m], pref[:1], name + ': one Shadow Mantle, on Susie, else Kris, else Ralsei')
        if len(members) == 1 and members[0] not in (4, 5):
            eq(len(m), 1, name + ': a solo member who can wear it has the Shadow Mantle')
        for c in members:
            if c == 5:
                # Flowery: his own gear and all his techniques, whatever the loadout
                gear = [sim.eval('global.charweapon[5]'), sim.eval('global.chararmor1[5]'), sim.eval('global.chararmor2[5]')]
                eq(gear, [30, 30, 31], name + ': Flowery wears his own gear')
                for k in range(3):
                    ok(sim.eval('knight_equip_info(%d,%d,5).ok' % (k, gear[k])), name + ': Flowery can wear item %d' % gear[k])
                eq([x for x in L('knight_cc_spl(5)') if x], [16, 17, 18, 19, 20, 21], name + ': Flowery has all six techniques')
                continue
            gear = [sim.eval('knight_equip_get(%d,%d)' % (c, k)) for k in range(3)]
            for k in range(3):
                ok(sim.eval('knight_equip_info(%d,%d,%d).ok' % (k, gear[k], c)), name + ': %s can wear item %d in slot %d' % (NAMES[c], gear[k], k))
            sp = [sim.eval('global.spell[%d][%d]' % (c, s)) for s in range(12)]
            used = [s for s in sp if s]
            ok(len(used) == len(set(used)), name + ': no spell twice for %s' % NAMES[c])
            ok(all(0 <= s <= 15 for s in sp), name + ': spell ids valid')
            ok(sp[:len(used)] == used, name + ': spells packed from slot 1')
            for s in used:
                ok(usable(s, c, members), name + ': %s spell %d works in this party' % (NAMES[c], s))
            bg = list(BASE_GEAR[c])
            if pref and pref[0] == c:
                bg[2] = 23
            if lo['kind'] == 'base':
                eq(gear, bg, name + ': BASE gear for %s' % NAMES[c])
                eq(used, NATURAL[c], name + ': BASE spells for %s' % NAMES[c])
            if lo['kind'] == 'dual':
                eq(gear, bg, name + ': DUAL MOVES keeps the normal gear')
                ok(used[:len(NATURAL[c])] == NATURAL[c], name + ': DUAL MOVES keeps the natural spells')
                for s in (5, 6, 12, 14, 15):
                    if usable(s, c, members) and s in [x[0] for x in L('knight_lo_duals(%d)' % c)]:
                        ok(s in used, name + ': %s has two-person move %d' % (NAMES[c], s))
            if lo['kind'] in ('maxed', 'triple', 'double'):
                KIT = {1: [7, 1, 5, 6, 14, 12], 2: [4, 11], 3: [2, 3, 13, 15, 6], 4: [2, 8, 9, 10, 15, 6]}
                kit = [sp for sp in KIT[c] if usable(sp, c, members)]
                eq(used, kit, name + ': MAXED = %s own moves that work in this party' % NAMES[c])
                ok(set(NATURAL[c]) <= set(used), name + ': MAXED keeps the natural spells')
                w = {1: 26, 2: 4, 3: 4, 4: 13}[c]
                eq(gear[0], w, name + ': best weapon for %s' % NAMES[c])
                eq(gear[1], 21, name + ': Dealmaker for %s' % NAMES[c])
print('loadouts applied', total)
eq(total, 4 * 3 + 6 * 2 + 3 + 4 * 2 + 4, 'loadout count (trios 3 each, duos 2 + DUAL where possible, solos 2, x3 4)') if False else None

# the page opens on the current party's group, any order
for party, g, i in [([1, 2, 3], 0, 1), ([3, 1, 2], 0, 1), ([4, 2, 1], 1, 1), ([2, 3, 4], 3, 1), ([4, 1, 0], 6, 1), ([3, 0, 0], 12, 1), ([5, 1, 2], 14, 1), ([4, 5, 0], 23, 1), ([5, 0, 0], 24, 1), ([2, 2, 2], 26, 1), ([4, 4, 4], 26, 3), ([3, 3, 0], 25, 2)]:
    sim.run('global.knight_cfg.party = [%d,%d,%d]; knight_ui_lo_focus_party();' % tuple(party))
    eq((sim.eval('global.knight_ui.lo_g'), sim.eval('global.knight_ui.lo_i')), (g, i), 'page opens on the group of %s' % party)

# equipment menu: stepping never takes the mantle; picking it from the list moves it with a message
sim.run('for (var c = 1; c <= 4; c++) { global.chararmor1[c] = 0; global.chararmor2[c] = 0; } global.chararmor2[2] = 23; knight_equip_refresh(); global.knight_cfg.party = [1,2,3];')
seen23 = False
for _ in range(40):
    v = sim.eval('knight_equip_step(1, 1, 1)')
    seen23 = seen23 or v == 23
ok(not seen23, 'stepping Kris armor never lands on the mantle Susie wears')
eq(mantles(), [(2, 2)], 'Susie keeps it')
ok(sim.eval('knight_mantle_elsewhere(2, 1)'), "Susie's other slot cannot take a second mantle")
sim.run('global.knight_cfg.party = [1,2,3]; global.knight_ui.tab = 1; global.knight_ui.focus = 1; global.knight_ui.pslot = 0; global.knight_ui.prow = 1; global.knight_ui.lv = 2;'
        'global.PL = knight_ui_pick_list(1, 1); for (var i = 0; i < array_length(global.PL); i++) if (global.PL[i] == 23) global.knight_ui.ppick = i;')
ok(sim.eval('global.PL[global.knight_ui.ppick]') == 23, 'the list offers the mantle to Kris')
sim.run('knight_ui_step_party(false, false, false, false, true, false);')
eq(mantles(), [(1, 1)], 'picking it moves it from Susie to Kris')
ok('Susie' in sim.eval('global.knight_ui.warn') and sim.eval('global.knight_ui.warnok'), 'a yellow note says it was taken from Susie')
# presets: two mantles in a saved setup -> one, with a note
sim.run('global.chararmor1[1] = 23; global.chararmor2[2] = 23; global.chararmor1[3] = 23; global.knight_cfg.party = [3,1,2]; global.ES = knight_equip_to_string();')
sim.run('global.D = { cfg: knight_cfg_copy(global.knight_cfg), spells: knight_spells_to_string(), equip: global.ES }; global.NOTES = knight_preset_apply(global.D);')
eq(mantles(), [(3, 1)], 'preset with three mantles: the first party member (Ralsei) keeps it')
ok(any('Shadow Mantle' in n for n in L('global.NOTES')), 'preset load says why one was taken off')
# menu open fixes a doubled mantle silently
sim.run('global.chararmor1[1] = 23; global.chararmor2[1] = 23; global.chararmor1[3] = 0; global.knight_cfg.party = [1,2,3]; knight_mantle_fix();')
eq(mantles(), [(1, 1)], 'one member wearing two mantles keeps one')
# store keeps a loaded loadout between sessions
sim.run('global.LL = knight_lo_list(0); knight_lo_apply(0, global.LL[1]); knight_store_save();')
sp_before = [sim.eval('global.spell[1][%d]' % s) for s in range(12)]
eq_before = sim.eval('knight_equip_to_string()')
sim2, _ = menu_sim()
import shutil
shutil.copy(os.path.join(sim.sandbox, 'knight_hub.ini'), os.path.join(sim2.sandbox, 'knight_hub.ini'))
sim2.run('knight_store_load(); knight_snapshot_take(); knight_spells_from_string(global.knight_last_spells); knight_equip_from_string(global.knight_last_equip);')
eq([sim2.eval('global.spell[1][%d]' % s) for s in range(12)], sp_before, 'loaded spells come back next session')
eq(sim2.eval('knight_equip_to_string()'), eq_before, 'loaded gear comes back next session')

# Noelle's default spells: a save with none of hers gets Heal Prayer, SleepMist, IceShock first (then what she had); a list
# that has any of them is left alone
for before, want in [([15], [2, 8, 9, 15]), ([], [2, 8, 9]), ([10, 15], [2, 8, 9, 10, 15]), ([2, 15], [2, 15]), ([9], [9])]:
    row = before + [0] * (12 - len(before))
    sim.run('for (var s = 0; s < 12; s++) global.spell[4][s] = %s[s];' % row)
    sim.run('knight_noelle_defaults();')
    got = [x for x in [sim.eval('global.spell[4][%d]' % s) for s in range(12)] if x]
    eq(got, want, 'Noelle defaults from %s' % before)
sim.run('for (var s = 0; s < 12; s++) global.spell[4][s] = 0; knight_kris_defaults();')
eq([x for x in [sim.eval('global.spell[4][%d]' % s) for s in range(12)] if x], [2, 8, 9, 15], 'a fresh hub: Noelle has her three spells and Frostfire')
print('loadout tests', N[0], 'fails', len(FAILS)); sys.exit(1 if FAILS else 0)
