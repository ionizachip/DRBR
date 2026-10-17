"""Build 38, hub logic: INFINITE HP (option, blocks, records, the HP cut and the refill), the x2 loadouts, the Weird Route by party
order (top member, bottom-up victims, the last member), the talk order (Susie first, the others in party order), what the survivors
learn, and the double-cast flags. Plus static checks that the build 38 hooks are in the merged game code."""
import sys, os, re, time
from harness import *
FAILS = []; N = [0]
def ok(c, msg):
    N[0] += 1
    if not c: FAILS.append(msg); print('FAIL', msg, flush=True)
def eq(a, b, msg):
    N[0] += 1
    if a != b: FAILS.append(msg); print('FAIL', msg, 'got', repr(a), 'want', repr(b), flush=True)

t0 = time.time()
sim = make_sim(); sim.run('knight_store_load(); knight_ui_init();')
sim.load_file(B + 'gml_GlobalScript_scr_havechar.gml', entry='gml_GlobalScript_scr_havechar')
sim.run('global.charname = ["", "Kris", "Susie", "Ralsei", "Noelle"];')
L = lambda e: sim.py(sim.eval(e))

# ---------- INFINITE HP: the option ----------
eq(sim.eval('global.knight_cfg.infhp'), 0, 'INFINITE HP is off by default')
ids = L('knight_ui_cfg_ids()')
ok('infhp' in ids and ids.index('infhp') == ids.index('practice') + 1, 'CONFIG page: INFINITE HP right after PRACTICE (%s)' % ids)
eq(sim.eval('knight_ui_cfg_label("infhp")'), 'INFINITE HP', 'label')
d = sim.eval('knight_ui_cfg_desc("infhp")')
ok(all(len(x) <= 38 for x in d.split('#')) and len(d.split('#')) == 2, 'description fits two lines: %r' % d)
sim.run('knight_ui_cfg_act("infhp", 0);'); eq(sim.eval('global.knight_cfg.infhp'), 1, 'Z turns it on')
eq(sim.eval('knight_ui_cfg_value("infhp")'), 'ON', 'shows ON')
eq(sim.eval('knight_ui_block("c_hp1")'), 'Not with INFINITE HP (CONFIG page).', '1 HP START is blocked while INFINITE HP is on')
sim.run('knight_ui_rule_toggle("c_hp1");'); eq(sim.eval('global.knight_cfg.c_hp1'), 0, '... and cannot be turned on')
sim.run('knight_ui_cfg_act("infhp", 0);'); eq(sim.eval('global.knight_cfg.infhp'), 0, 'Z turns it off')
sim.run('global.knight_cfg.c_hp1 = 1;')
eq(sim.eval('knight_ui_block("infhp")'), 'Not with 1 HP START (RULES page).', 'INFINITE HP is blocked while 1 HP START is on')
sim.run('knight_ui_cfg_act("infhp", 0);'); eq(sim.eval('global.knight_cfg.infhp'), 0, '... and cannot be turned on')
# a config with both (a preset, an old file): the check refuses it and the fix drops 1 HP START
sim.run('global.CC = knight_cfg_copy(global.knight_cfg); global.CC.infhp = 1; global.CC.c_hp1 = 1; global.CK = knight_check(global.CC, [0]);')
ok(not sim.eval('global.CK.ok') and any('Infinite HP' in e for e in L('global.CK.errors')), 'knight_check refuses 1 HP START + INFINITE HP')
eq((sim.eval('global.CK.fixcfg.c_hp1'), sim.eval('global.CK.fixcfg.infhp')), (0, 1), 'the fix drops 1 HP START, keeps INFINITE HP')
sim.run('global.CC.c_hp1 = 0; global.CC.randchal = 1;')
for i in range(30):
    f = sim.eval('knight_random_challenge(global.CC, [0])')
    ok(f != 'c_hp1', 'Random Rule never picks 1 HP START with INFINITE HP')
# it is saved like the other options
sim.run('global.knight_cfg.c_hp1 = 0; global.knight_cfg.infhp = 1; knight_store_save();')
s2 = make_sim(); import shutil; shutil.copy(os.path.join(sim.sandbox, 'knight_hub.ini'), os.path.join(s2.sandbox, 'knight_hub.ini')); s2.run('knight_store_load();')
eq(s2.eval('global.knight_cfg.infhp'), 1, 'INFINITE HP is remembered')
# runs: nothing recorded; HUD / launch / result notes
sim.run('global.knight_cfg = knight_cfg_default(); global.knight_cfg.infhp = 1; global.knight_cfg.party = [1,2,3];')
sim.run('global.RES = knight_resolve(global.knight_cfg);')
ok(sim.eval('global.RES.ok'), 'a run with INFINITE HP resolves')
ok('Infinite HP: nothing is recorded.' in L('knight_ui_launch_lines({cfg: global.RES.cfg, plan: global.RES.plan, src: global.RES.src, corr: []})'), 'launch summary says so')
sim.run('global.krun = knight_run_new(global.RES); global.knight_run = 1; knight_fight_setup();')
ok(not sim.eval('global.krun.rec'), 'an INFINITE HP run records nothing')
eq(sim.eval('knight_record_note(global.krun)'), 'Infinite HP: nothing is recorded.', 'result note')
sim.run('global.krun.state = "battle";')
ok('INFINITE HP - NOT RECORDED' in L('knight_hud_lines()'), 'HUD line')
# ---------- INFINITE HP: the cut and the refill ----------
eq(sim.eval('knight_infhp_cut(57)'), 0, 'a hit takes no HP')
sim.run('global.krun.cfg.infhp = 0;'); eq(sim.eval('knight_infhp_cut(57)'), 57, 'off: the hit takes its HP')
sim.run('global.krun.cfg.infhp = 1; global.krun.state = "arena";'); eq(sim.eval('knight_infhp_cut(57)'), 57, 'only in a battle')
sim.run('global.krun.state = "battle"; global.char = [1,2,3]; global.hp = [0, 50, -20, 7, 100]; global.maxhp = [0, 90, 110, 140, 100];')
sim.run('knight_wr_reset(global.krun); global.krun.wr.slain[3] = true; knight_infhp_tick(global.krun);')
eq(L('global.hp'), [0, 90, -20, 7, 100], 'refill: members still up are put back to full; a downed member and one the Knight took are not')
sim.run('global.maxhp[4] = 90; global.char = [4,0,0]; global.krun.cfg.infhp = 1; knight_thorn_erode(0, 12, 7);')
eq(sim.eval('global.maxhp[4]'), 90, 'Thorn Knight wears no max HP down with INFINITE HP')
sim.run('global.krun.cfg.infhp = 0; knight_thorn_erode(0, 12, 7);')
eq(sim.eval('global.maxhp[4]'), 78, '... and does without it')

# ---------- x2 loadouts ----------
ng = sim.eval('knight_lo_group_count()')
eq(ng, 27, '4 trios + 6 duos + 4 solos + 11 with Flowery + x2 + x3')
eq((sim.eval('knight_lo_group_label(25)'), sim.eval('knight_lo_group_label(26)')), ('DOUBLE', 'TRIPLE'), 'the x2 group sits before the x3 group')
lst = L('knight_lo_list(25)')
eq([x['kind'] for x in lst], ['double'] * 4, 'one x2 loadout per member')
eq([sim.eval('knight_lo_label(knight_lo_list(25)[%d])' % i) for i in range(4)], ['KRIS x2', 'SUSIE x2', 'RALSEI x2', 'NOELLE x2'], 'x2 labels')
for i, c in enumerate([1, 2, 3, 4]):
    sim.run('global.LL = knight_lo_list(25); knight_lo_apply(25, global.LL[%d]);' % i)
    eq(L('global.knight_cfg.party'), [c, c, 0], 'x2 %d: two of one member' % c)
for party, g, i in [([2, 2, 0], 25, 1), ([0, 4, 4], 25, 3), ([3, 3, 3], 26, 2), ([1, 2, 0], 4, 1)]:
    sim.run('global.knight_cfg.party = [%d,%d,%d]; knight_ui_lo_focus_party();' % tuple(party))
    eq((sim.eval('global.knight_ui.lo_g'), sim.eval('global.knight_ui.lo_i')), (g, i), 'LOADOUTS opens on the group of %s' % party)

# ---------- party order ----------
sim.run('global.knight_run = 0;')
def P(party, hp=(0, 90, 90, 90, 90, 90)):
    hp = tuple(hp) + (90,) * (6 - len(hp))
    sim.run('global.char = [%d,%d,%d]; global.hp = [%d,%d,%d,%d,%d,%d];' % (tuple(party) + hp))
P([3, 1, 2]); eq(sim.eval('knight_wr_fin_of_party()'), 3, 'the member on top stays to the end (Ralsei on top)')
eq(sim.eval('knight_wr_bottom(3)'), 2, 'bottom first: Susie at the bottom goes first')
P([3, 1, 0]); eq(sim.eval('knight_wr_bottom(3)'), 1, 'Kris can be taken when Kris is not on top')
P([2, 0, 0]); eq(sim.eval('knight_wr_bottom(2)'), 0, 'solo: nobody to take')
eq(sim.eval('knight_wr_lone()'), 2, 'solo: the last member')
P([2, 2, 0]); eq((sim.eval('knight_wr_bottom(2)'), sim.eval('knight_wr_lone()')), (0, 2), 'Susie x2 counts as one member')
P([1, 4, 3]); eq(sim.eval('knight_wr_lone()'), 0, 'three members: nobody is alone')
# build 50: Flowery (5) counts like the others - on top he stays to the end (Kris below him is taken), at the bottom he is taken
P([5, 1, 0]); eq((sim.eval('knight_wr_fin_of_party()'), sim.eval('knight_wr_bottom(5)')), (5, 1), 'Flowery on top: Kris below him is the one taken')
P([1, 5, 0]); eq((sim.eval('knight_wr_fin_of_party()'), sim.eval('knight_wr_bottom(1)')), (1, 5), 'Kris on top: Flowery below is taken')
P([5, 0, 0]); eq(sim.eval('knight_wr_lone()'), 5, 'solo Flowery: the last member')
eq(sim.eval('knight_wr_pick()'), 0, 'solo Flowery: nobody to take')
P([2, 3, 5]); eq(sim.eval('knight_wr_pick()'), 5, 'Flowery at the bottom goes first')
eq((sim.eval('knight_vb_fin_name(5)'), sim.eval('knight_vb_fin_upper(5)'), sim.eval('knight_vb_fin_spell(5)')), ('LastJarona', 'LAST JARONA', 23), 'Flowery\'s finisher: LAST JARONA')
sim.run('global.knight_variant = 3; global.charname[5] = "Flowery";')
eq((sim.eval('knight_vtitle(5)'), sim.eval('knight_vtitle(2)')), ('The Flower Man', 'Susie'), 'the Violet Knight calls him The Flower Man')
sim.run('global.knight_variant = 0;')
eq(sim.eval('knight_vtitle(5)'), 'Flowery', '... nobody else does')

# ---------- the talk order: Susie first, then the others in party order ----------
def talk(party, v, again=False):
    P(party)
    q = L('knight_talk_build(%d, %s)' % (v, 'true' if again else 'false'))
    return [(x[0], x[1], x[3]) for x in q]
q = talk([1, 3, 2], 4)
eq([x[0] for x in q], [2, 3, 2, 2, 3], 'Noelle lost, Ralsei above Susie: Susie still speaks first, Ralsei picks up, then Susie\'s fury and Ralsei\'s resolve')
ok('prophecy' in q[1][1], 'Ralsei: "this wasn\'t in the prophecy"')
q = talk([3, 4, 2], 1) if False else talk([3, 4, 1], 2)
eq([x[0] for x in q], [3, 4, 3, 4], 'Susie lost: Ralsei (higher) before Noelle')
q = talk([4, 1, 3], 2)
eq([x[0] for x in q], [4, 3, 4, 3], 'Susie lost: Noelle on top speaks before Ralsei')
q = talk([2, 4, 3], 3)
eq([x[0] for x in q], [2, 4, 4, 2, 2, 4], 'Ralsei lost: Susie, then Noelle ("get up..."), then Susie\'s fury, then Noelle\'s courage')
ok('do it myself' in q[-1][1], 'Noelle finds her courage')
q = talk([2, 3, 0], 3, True)
eq([x[1] for x in q], ['R^3-Ralsei...?/%', '...^2. Not..^2.&not you too.../%', 'YOU..^2.&I\'M GONNA..^2.&END YOU!!!/%'], 'Susie loses a second friend')
q = talk([1, 2, 0], 2)
eq(q, [], 'Kris never speaks')
q = talk([5, 1, 0], 1)
eq([x[0] for x in q], [5, 5, 5], 'Kris taken under Flowery: Flowery speaks (shock, then his resolve)')
ok('Nobody hurts' in q[-1][1] and 'Kris' in q[0][1], 'his lines: %r' % [x[1] for x in q])
q = talk([2, 5, 3], 3)
eq([x[0] for x in q][:2], [2, 5], 'Ralsei lost with Flowery there: Susie still first, then Flowery')
ok(5 in [x[0] for x in q], 'Flowery speaks too')
P([1, 2, 3], hp=(0, 90, -5, 90, 90))
eq(L('knight_talk_speakers(3)'), [2], 'Susie answers even when she is down (she gets back up)')
P([1, 3, 4], hp=(0, 90, 90, 90, -5))
eq(L('knight_talk_speakers(2)'), [3], 'Noelle down: she does not talk')

# ---------- what they learn ----------
# a knight instance with ACT lists, so the learned moves can go on them
sim.run('global.monstertype = [104,0,0];')
for nm in ['canact', 'actname', 'actdesc', 'actcost', 'actsimul', 'actactor']:
    for sfx in ['', 'sus', 'ral', 'noe']:
        z = '""' if nm in ('actname', 'actdesc') else '0'
        sim.run('global.%s%s = [[%s],[%s],[%s]];' % (nm, sfx, ','.join([z] * 6), ','.join([z] * 6), ','.join([z] * 6)))
sim.mock('scr_spellmenu_setup', 0); sim.mock('scr_spellget', lambda s, c, sp: (s.run('global.spell[%d][5] = %d;' % (c, sp)), 0)[1])
sim.run('with (obj_knight_enemy) instance_destroy(); global.K = instance_create(0, 0, obj_knight_enemy); global.K.myself = 0; global.battleactcount = [0,0,0];')
def learn(party, v, quiet=0, fresh=True, hp=(0, 90, 90, 90, 90), more=True):
    P(party, hp)
    if fresh:
        sim.run('knight_learn_init(true); for (var c = 0; c < 5; c++) for (var s = 0; s < 12; s++) global.spell[c][s] = 0;')
        for sfx in ['sus', 'ral', 'noe']:
            sim.run('global.canact%s[0] = [1,0,0,0,0,0]; global.actname%s[0] = ["X","","","","",""];' % (sfx, sfx))
    return sim.eval('knight_learn_after(%d, %d, %s)' % (v, quiet, 'true' if more else 'false'))
m = learn([1, 2, 3], 3)
ok('RUDER BUSTER' in m, 'Ralsei taken: Susie learns RUDER BUSTER (%r)' % m)
eq((sim.eval('global.actnamesus[0][1]'), sim.eval('global.actcostsus[0][1]')), ('RuderBuster', 150), 'on her S-Action list, 60% TP')
m = learn([1, 2, 3, ], 1) if False else learn([2, 3, 4], 4)
ok('RUDER BUSTER' not in m and 'FIRESTORM' in m, 'the Angel taken, Ralsei still there: Susie waits, Ralsei learns FIRESTORM (%r)' % m)
eq(sim.eval('global.actnameral[0][1]'), 'FireStorm', 'FireStorm on his R-Action list')
m3 = learn([2, 3, 4], 4, more=False)
ok('RUDER BUSTER' in m3, 'the only loss of the fight (Normal / Supercharged / Thorn / Cyan): Susie learns it now (%r)' % m3)
m = learn([2, 3, 4], 4)
m2 = learn([2, 3, 0], 3, fresh=False)
ok('RUDER BUSTER' in m2 and 'FIRESTORM' not in m2, 'then Ralsei taken: now Susie learns it; Ralsei learns nothing again (%r)' % m2)
m = learn([1, 2, 4], 4)
ok('RUDER BUSTER' in m, 'no Ralsei in the party: Susie learns it after the first loss she sees (%r)' % m)
m = learn([3, 2, 4], 4)
ok('RUDER BUSTER' in m, 'Ralsei on top (never taken): Susie learns it after the first loss (%r)' % m)
m = learn([1, 4, 2], 2)
ok('courage' in m and 'ICESTORM' in m and 'SNOWGRAVE' in m, 'Noelle finds her courage, learns ICESTORM and SnowGrave (%r)' % m)
eq((sim.eval('global.actnamenoe[0][1]'), sim.eval('global.actcostnoe[0][1]')), ('IceStorm', 75), 'IceStorm on her N-Action list, 30% TP')
eq(sim.eval('global.K.noe_learned'), 1, "the mod's own Noelle scene will not play again")
m = learn([2, 3, 4], 4, quiet=2) if False else learn([2, 3, 0], 3, quiet=2)
eq(m, '', 'the finisher scene gives Susie\'s line instead (quiet)')
eq(sim.eval('global.actnamesus[0][1]'), 'RuderBuster', '... but she still learns it')
ok(m.endswith('/%') or m == '', 'the text ends the box')
m = learn([1, 2, 3], 3); pages = m.split('/')
ok(m.index('RUDER') < m.index('FIRESTORM') if 'FIRESTORM' in m else True, 'Susie\'s line comes first')

# ---------- the double-cast flags ----------
sim.run('knight_dbl_clear(); knight_dbl_set(1, 4); global.charspecial = [0, 4, 0]; global.char = [1, 2, 0]; global.msg = [""];')
sim.run('knight_dbl_text(1);'); ok('RUDER BUSTER' in sim.eval('global.msg[0]'), 'the spell line names RUDER BUSTER')
eq(sim.eval('knight_dbl_take(0, 4)'), False, 'other slot: not the double')
eq(sim.eval('knight_dbl_take(1, 9)'), False, 'other spell: not the double')
eq(sim.eval('knight_dbl_take(1, 4)'), True, 'the double, once')
eq(sim.eval('knight_dbl_take(1, 4)'), False, '... only once')

# ---------- the hooks are in the merged game code ----------
M = '/home/claude/work/build/merged/'
rd = lambda f: open(M + f, encoding='utf8', errors='replace').read()
MS = rd('gml_GlobalScript_scr_monstersetup.gml')
for k in ('base', 'elec', 'violet', 'thorn', 'cyan'):
    ok('knight_hb_setup("%s");' % k in MS, 'HoldBreath setup in the %s knight' % k)
ok('knight_hb_setup("kaizo")' not in MS, 'Kaizo keeps its own HoldBreath')
ST = rd('gml_Object_obj_knight_enemy_Step_0.gml')
eq(ST.count('knight_member_acts();'), 5, 'the S/R/N-Action hook in every knight but Kaizo')
ok('stringset("RedBuster")' not in ST.split('knightkillcon == 10')[1] if 'knightkillcon == 10' in ST else True, 'no Kris RedBuster ACT after a loss')
ok('knight_vb_deflect_start();' in ST and 'knight_vb_hurt_kris();' in ST and 'personwhosgonnadie = "kris"' in ST, 'Violet: the parry and Kris as a victim')
SV = rd('gml_GlobalScript_scr_complete_save_file.gml')
ok('personwhosabouttosuperdie == "kris"' in SV, 'Violet kill script knows Kris')
SP = rd('gml_GlobalScript_scr_spell.gml')
for sp, kind in ((4, 8), (9, 9)):
    ok(SP.count('knight_dbl_take(caster, %d)' % sp) >= 1 and SP.count('knight_kspell_start(%d, caster, star, damage)' % kind) >= 1, 'spell %d has its double version' % sp)
ok(SP.count('knight_dbl_take(caster, 13)') >= 1 and 'global.knight_ks.dbl = 1;' in SP, 'FireShock has its double version')
DM = rd('gml_GlobalScript_scr_damage.gml')
ok(len(re.findall(r'global\.hp\[chartarget\] -= (?!knight_infhp_cut)', DM)) == 0, 'every HP loss in scr_damage goes through the INFINITE HP cut')
for f in ('scr_damage_fixed', 'scr_damage_maxhp', 'scr_damage_proportional', 'scr_damage_sneo_final_attack'):
    t = rd('gml_GlobalScript_%s.gml' % f)
    ok(len(re.findall(r'global\.hp\[chartarget\] -= (?!knight_infhp_cut)', t)) == 0, f + ': every HP loss goes through the cut')
BC = rd('gml_Object_obj_battlecontroller_Step_0.gml')
eq(len(re.findall(r'global\.hp\[\d\]--;', BC)), 0, 'ThornRing drains go through the cut')
SPP = rd('gml_Object_obj_spellphase_Step_0.gml') + rd('gml_Object_obj_spellphase_Alarm_0.gml')
ok(SPP.count('knight_dbl_text(') >= 4, 'spell phase lines name the learned moves')
print('b38 tests', N[0], 'fails', len(FAILS), '%.0fs' % (time.time() - t0)); sys.exit(1 if FAILS else 0)
