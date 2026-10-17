"""Build 37 fixes: THORNS rule ignores the ThornRing drain (only hits wear max HP), FireShock damage up, Shadow Mantle by party slot
(real merged scr_damage), Thorn Knight erosion for whoever is hit (Noelle included), the SOUL position without Kris, the ACT row
recount, and static checks of the merged game code (Susie's bubbles, Noelle's lines, Weird Route hooks)."""
import sys, re, glob, os
from harness import *
FAILS = []; N = [0]
def ok(c, msg):
    N[0] += 1
    if not c: FAILS.append(msg); print('FAIL', msg)
def eq(a, b, msg):
    N[0] += 1
    if a != b: FAILS.append(msg); print('FAIL', msg, 'got', repr(a), 'want', repr(b))

# ---------- THORNS + ThornRing ----------
def run_sim(party, key='base', cfg=''):
    sim = make_sim()
    sim.run('global.knight_run = 1; var _c = knight_cfg_default(); _c.c_thorns = 1; %s _c.party = [%d,%d,%d];'
            'global.krun = knight_run_new({src: _c, cfg: _c, plan: [knight_find_key("%s")], reveal: ""}); global.krun.party = [%d,%d,%d]; '
            'global.krun.state = "battle"; global.char = [%d,%d,%d];' % ((cfg,) + tuple(party) + (key,) + tuple(party) + tuple(party)))
    sim.run('global.hp = [0, 160, 190, 140, 90, 0, 0]; global.maxhp = [0, 160, 190, 140, 90, 0, 0]; global.mnfight = 0;')
    sim.run('knight_ch_begin(global.krun);')
    return sim

sim = run_sim([1, 2, 4])
# the ThornRing drains 1 HP every 6 frames while HP > max/3: 1200 frames of drain, Thorns tick every frame
for f in range(1200):
    if f % 6 == 0:
        sim.run('if (global.hp[4] > round(global.maxhp[4] / 3)) global.hp[4]--;')
    sim.run('knight_ch_tick(global.krun);')
eq(sim.eval('global.maxhp[4]'), 90, 'THORNS: the ThornRing drain never lowers max HP')
eq(sim.eval('global.hp[4]'), 30, 'THORNS: the drain stops at a third of max HP like the game says')
# a real hit (scr_damage_calculation -> knight_scale_taken marks the member) wears max HP down by 30% of the HP lost
sim.run('global.hp[4] = 90;'); sim.run('knight_ch_tick(global.krun);')
d = sim.eval('knight_scale_taken(40, 2)')
sim.run('global.hp[4] -= %d;' % d)
sim.run('knight_ch_tick(global.krun);')
eq(sim.eval('global.maxhp[4]'), 90 - (-(-d * 3 // 10)), 'THORNS: a hit on Noelle takes 30%% of the %d HP it removed off her max HP' % d)
# a hit and a drain in the same frame: only the hit's share
m0 = sim.eval('global.maxhp[4]')
d = sim.eval('knight_scale_taken(20, 2)')
sim.run('global.hp[4] -= %d + 1;' % d)
sim.run('knight_ch_tick(global.krun);')
ok(m0 - sim.eval('global.maxhp[4]') <= -(-(d + 1) * 3 // 10), 'THORNS: drain in the same frame adds at most one point')
# Kris and Susie still work
sim.run('global.hp[1] = 160;'); sim.run('knight_ch_tick(global.krun);')
d = sim.eval('knight_scale_taken(50, 0)'); sim.run('global.hp[1] -= %d;' % d); sim.run('knight_ch_tick(global.krun);')
eq(sim.eval('global.maxhp[1]'), 160 - (-(-d * 3 // 10)), 'THORNS: Kris hit')
# Thorn Knight is left alone (it erodes max HP itself)
sim = run_sim([1, 2, 4], 'thorn')
d = sim.eval('knight_scale_taken(50, 0)'); sim.run('global.hp[1] -= %d;' % d); sim.run('knight_ch_tick(global.krun);')
eq(sim.eval('global.maxhp[1]'), 160, 'THORNS rule off in Thorn Knight')

# ---------- FireShock damage ----------
sim = make_sim()
for o in ('obj_knight_enemy',):
    try: sim.define_object(o)
    except Exception: pass
sim.run('global.knight_variant = 0; global.chapter = 3; instance_create(0, 0, obj_knight_enemy); obj_knight_enemy.damagereduction = 0.2; obj_knight_enemy.kaizo_block = 0;'
        'global.char = [1, 3, 0]; global.hp = [0, 10, 10, 10, 10]; global.battlemag = [5, 13, 0, 0, 0]; global.battleat = [10, 16, 0, 0, 0]; global.monsterdf = [0, 0, 0];')
ice = sim.eval('knight_iceshock_damage(1, 0, 0)')
fs = sim.eval('knight_fireshock_damage(1, 0)')
eq(fs, -(-ice * 21 // 10), 'FireShock = 2.1 x the Ice Shock number for Ralsei (was 1.3x)')
print('FireShock (Ralsei MAG 13 AT 16, normal knight):', fs, ' was', -(-ice * 13 // 10))
sim.run('global.knight_variant = 3;'); eq(sim.eval('knight_fireshock_damage(1, 0)'), -(-ice * 28 // 10), 'Violet: 2.8x')
sim.run('global.knight_variant = 0; global.char = [1, 3, 4]; global.battlemag = [5, 13, 30, 0, 0]; global.battleat = [10, 16, 20, 0, 0];')
ni = sim.eval('knight_iceshock_damage(2, 0, 0)')
ok(sim.eval('knight_fireshock_damage(1, 0)') >= -(-ni * 15 // 10), 'with a strong Noelle: at least 1.5x her Ice Shock')

# ---------- party helpers ----------
sim = make_sim()
sim.run('global.char = [2, 4, 0]; global.chararmor1 = [0, 0, 0, 0, 0]; global.chararmor2 = [0, 0, 23, 0, 0]; global.hp = [0, 100, 100, 100, 100];')
eq([sim.eval('knight_mantle_slot(%d)' % s) for s in range(3)], [True, False, False], 'mantle on slot 1 = Susie (not Kris)')
eq(sim.eval('knight_mantle_party()'), True, 'someone in the party wears it')
sim.run('global.chararmor2 = [0, 0, 0, 23, 0];')
eq(sim.eval('knight_mantle_party()'), False, "an absent member's mantle does not count")
sim.run('global.hp[4] = -5;')
eq([sim.eval('knight_slot_down(%d)' % s) for s in range(3)], [False, True, True], 'slot down: Noelle down, empty slot counts as down')
# Thorn Knight erosion
sim.run('global.maxhp = [0, 160, 190, 140, 90]; global.chararmor2 = [0, 0, 0, 0, 0];')
sim.run('knight_thorn_erode(1, 12, 7);'); eq(sim.eval('global.maxhp[4]'), 78, 'Thorn Knight: Noelle (slot 2) loses max HP')
sim.run('global.maxhp[4] = 55; knight_thorn_erode(1, 12, 7);'); eq(sim.eval('global.maxhp[4]'), 50, "Noelle's floor is 50")
sim.run('global.maxhp[4] = 45; knight_thorn_erode(1, 12, 7);'); eq(sim.eval('global.maxhp[4]'), 45, 'a floor never raises a lower max HP')
sim.run('global.chararmor2[2] = 23; global.maxhp[2] = 190; knight_thorn_erode(0, 12, 7);'); eq(sim.eval('global.maxhp[2]'), 183, 'mantle wearer loses the smaller amount')
sim.run('knight_thorn_erode(2, 12, 7);'); eq(sim.eval('global.maxhp[0]'), 0, 'empty slot: nothing')
# ACT row recount
sim.run('global.battleactcount = [1, 2, 1]; knight_actcount_fix();'); eq(sim.py(sim.eval('global.battleactcount')), [0, 0, 0], 'ACT rows recounted for every slot')
# SOUL position without Kris
sim.define_object('obj_hx')
sim.run('global.char = [3, 4, 0]; global.charinstance = [instance_create(50, 60, obj_hx), instance_create(70, 90, obj_hx), noone];')
eq((sim.eval('knight_soul_x()'), sim.eval('knight_soul_y()')), (60, 100), 'no Kris: the heart comes out of the leader')
sim.run('global.char = [3, 1, 0];')
eq((sim.eval('knight_soul_x()'), sim.eval('knight_soul_y()')), (80, 130), 'Kris anywhere: from Kris')

# ---------- Shadow Mantle in the real merged scr_damage (Normal Knight) ----------
sim = make_sim()
sim.load_file(M + 'gml_GlobalScript_scr_damage.gml', entry='gml_GlobalScript_scr_damage')
for n in ['scr_damage_cache', 'scr_damage_check', 'scr_dmgwriter_selfchar', 'scr_oflash', 'snd_play', 'scr_shakeobj', 'scr_dead', 'scr_tensionheal', 'knight_hit_event']:
    sim.mock(n, 0)
for ent in ('scr_randomtarget_old', 'scr_damage_calculation'):
    try: sim.load_file(M + 'gml_GlobalScript_%s.gml' % ent, entry='gml_GlobalScript_%s' % ent)
    except Exception: sim.load_file('/home/claude/work/gml/base/CodeEntries/gml_GlobalScript_%s.gml' % ent, entry='gml_GlobalScript_%s' % ent)
sim.mock('scr_element_damage_reduction', lambda s, *a: 1)
sim.mock('debug_message', 0); sim.mock('camerax', 0); sim.mock('cameray', 0)
sim.define_object('obj_dmgwriter'); sim.define_object('obj_b'); sim.define_object('obj_shake')
sim.define_event('obj_dmgwriter', 'Create', 0, 'delaytimer = 0; delay = 0; killactive = 0; damage = 0; type = 0; specialmessage = 0;')
_src = open(M + 'gml_GlobalScript_scr_damage.gml').read()
for _o in sorted(set(re.findall(r'\b(obj_\w+)', _src))):
    if _o not in sim.objects:
        try: sim.define_object(_o)
        except Exception: pass
for _v in sorted(set(re.findall(r'\b(spr_\w+|snd_\w+)', _src))):
    try: sim.define_asset(_v)
    except Exception: pass
try: sim.define_object('obj_knight_enemy')
except Exception: pass
SET = ('global.inv=-1; global.chapter=3; global.hp=[0,160,190,140,90]; global.maxhp=[0,160,190,140,90]; global.battledf=[0,0,0,0,0]; '
       'global.charcantarget=[1,1,1]; global.targeted=[0,0,0,0]; global.chardead=[0,0,0]; global.tension=0; global.invc=1; global.knight_variant=0; global.knight_run=0; '
       'global.charinstance=[instance_create(0,0,obj_b),instance_create(0,0,obj_b),instance_create(0,0,obj_b)]; for(var _q=0;_q<3;_q++){global.charinstance[_q].myheight=0;} '
       'global.chararmor1=[0,0,0,0,0]; global.chararmor2=[0,0,0,0,0]; global.battleat=[0,10,10,10,10]; global.mnfight=2; global.charaction=[0,0,0]; global.charspecial=[0,0,0]; '
       'global.charmove=[0,0,0]; global.faceaction=[0,0,0]; global.charauto=[0,0,0]; global.flag=array_create(2000,0);'
       'with (obj_dmgwriter) instance_destroy(); with (obj_knight_enemy) instance_destroy(); global.KE = instance_create(0,0,obj_knight_enemy); global.KE.aoedamage = false; global.KE.myattackchoice = 1; global.KE.damagecounter = 0; global.KE.difficulty = 0;')
def hit(party, armor2, target, n=1):
    sim.run(SET)
    sim.run('global.char = [%d,%d,%d]; global.chararmor2 = %s;' % (tuple(party) + (armor2,)))
    for _ in range(n):
        sim.run('global.inv = -1; var _b = instance_create(0,0,obj_b); _b.target = %d; _b.damage = 90; _b.element = 0; with (_b) { scr_damage(); }' % target)
    return [sim.eval('global.hp[%d]' % i) for i in range(1, 5)]
h = hit([2, 4, 0], '[0,0,23,0,0]', 1)
ok(h[3] == 90 and h[1] < 190, 'mantle on Susie in slot 1: the hit aimed at Noelle goes to Susie (hp %s)' % h)
ok(190 - h[1] <= 40, 'and Susie takes a third of it (lost %d)' % (190 - h[1]))
h = hit([4, 2, 0], '[0,0,0,0,0]', 0)
eq(h[3] < 90 and h[1] == 190, True, 'no mantle anywhere: Noelle in slot 1 takes the hit herself')
h = hit([4, 2, 0], '[0,0,0,23,0]', 0)
ok(h[3] < 90 and 90 - h[3] > 40, "Ralsei's mantle (Ralsei absent) protects nobody (Noelle lost %d)" % (90 - h[3]))
h = hit([1, 2, 3], '[0,0,23,0,0]', 2)
ok(h[2] == 140 and h[1] < 190, 'story party: Susie\'s mantle still draws the hit (hp %s)' % h)

# ---------- static checks of the merged game code ----------
ST = open(M + 'gml_Object_obj_knight_enemy_Step_0.gml').read()
eq(ST.count('if (knight_taunt_begin(!practicemode))'), 4, "the taunts need Susie in the party (build 39: or Ralsei / Noelle without her) and no practice (Normal, Supercharged, Thorn, Cyan)")
ok('&* You d-don' not in ST and '&* are so angry' not in ST and '&* just talk' not in ST, "Noelle's lines are not split into extra asterisk lines")
CORE = open(M + 'gml_GlobalScript_knight_core.gml').read()
eq((ST.count('knight_noe_act_text(nactcount);'), CORE.count('scr_anyface_next("noelle", "B")')), (6, 1), "Noelle's worried face (B) in her talk ACT in every knight (build 39: one shared function)")
ok('scr_anyface_next("noelle", "2")' not in ST, "Noelle's big smile (face 2) is not used for frightened lines any more")
ok('knight_say(4, "R^2-Ralsei...?!/%", 3);' in ST, 'Violet: Noelle reacts to Ralsei in her own speech bubble')
ok('N^3-Noelle...?' in ST and 'T^3-The Angel' not in ST, 'Violet: Susie calls Noelle by her name')
eq(ST.count('knight_actcount_fix();'), 8, 'every "ACT used up" recounts the ACT rows')
ok('knight_vb_acts();' in ST and 'knight_vb_extra();' in ST and 'knightkillcon = knight_vb_route9();' in ST and 'knight_battle_won();' in ST, 'Violet Side B hooks')
ok('knight_kz_init();' in ST and 'knight_kz_acts();' in ST, 'Kaizo Side B without Kris hooks')
MH = open(M + 'gml_GlobalScript_scr_moveheart.gml').read()
ok('obj_herokris.x' not in MH.split('function scr_moveheart__g3')[1].split('function')[0] if 'function scr_moveheart__g3' in MH else 'obj_herokris.x + 10, obj_herokris.y + 40, obj_moveheart' not in MH, 'Violet scr_moveheart no longer reads obj_herokris')
RH = open(M + 'gml_Object_obj_returnheart_Create_0.gml').read()
eq(RH.count('obj_herokris.x'), 0, 'obj_returnheart never reads obj_herokris directly')
DM = open(M + 'gml_GlobalScript_scr_damage.gml').read() + open(M + 'gml_GlobalScript_scr_damage_maxhp.gml').read()
eq(len(re.findall(r'chararmor[12]\[[123]\] == 23', DM)), 0, 'no Shadow Mantle check by fixed character id is left in the damage scripts')
HL = open(M + 'gml_GlobalScript_scr_heal.gml').read()
ok(HL.count('knight_wr_noheal(arg0)') >= 1, 'scr_heal: the member the Knight took cannot be healed')
MN = open(M + 'gml_GlobalScript_scr_mnendturn.gml').read()
eq(MN.count('knight_wr_turnend();'), 2, 'end of enemy turn hook (base/elec/cyan share one copy, thorn has its own)')
HP = open(M + 'gml_Object_obj_heroparent_Create_0.gml').read()
eq(HP.count('_sideb = global.flag[456] > 0;'), 4, 'Noelle Side B look on a Weird Route save in every variant')
print('b37 tests', N[0], 'fails', len(FAILS)); sys.exit(1 if FAILS else 0)
