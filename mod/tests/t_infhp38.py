"""INFINITE HP (build 38) in the real merged damage code of all six knights: with the option on a hit still lands (damage number,
hurt) but takes no HP, nobody goes down even from a huge hit, the party-wide hits too; with it off the hit takes HP as before.
Static checks for the drains (ThornRing, Kaizo's GLOOM and turned-back SnowGrave)."""
import sys, re, time
from harness import *
FAILS = []; N = [0]
def ok(c, msg):
    N[0] += 1
    if not c: FAILS.append(msg); print('FAIL', msg, flush=True)
def eq(a, b, msg):
    N[0] += 1
    if a != b: FAILS.append(msg); print('FAIL', msg, 'got', repr(a), 'want', repr(b), flush=True)
t0 = time.time()
sim = make_sim()
for f in ('scr_damage', 'scr_damage_calculation', 'scr_randomtarget_old', 'scr_damage_maxhp', 'scr_damage_fixed', 'kaizo_settings_init'):
    try: sim.load_file(M + 'gml_GlobalScript_%s.gml' % f, entry='gml_GlobalScript_%s' % f)
    except Exception: sim.load_file('/home/claude/work/gml/base/CodeEntries/gml_GlobalScript_%s.gml' % f, entry='gml_GlobalScript_%s' % f)
for n in ['scr_damage_cache', 'scr_damage_check', 'scr_dmgwriter_selfchar', 'scr_oflash', 'snd_play', 'scr_shakeobj', 'scr_dead', 'scr_tensionheal', 'knight_hit_event',
          'scr_gameover', 'snd_play_x', 'scr_party_hpaverage', 'snd_stop', 'snd_pitch']:
    sim.mock(n, 0)
sim.mock('scr_element_damage_reduction', lambda s, *a: 1)
sim.mock('debug_message', 0); sim.mock('camerax', 0); sim.mock('cameray', 0)
sim.mock('kaizo_sideb', lambda s, *a: 0); sim.mock('violet_sideb', lambda s, *a: 0)
sim.define_object('obj_dmgwriter'); sim.define_object('obj_b'); sim.define_object('obj_shake')
sim.define_event('obj_dmgwriter', 'Create', 0, 'delaytimer = 0; delay = 0; killactive = 0; damage = 0; type = 0; specialmessage = 0;')
_src = ''.join(open(M + 'gml_GlobalScript_%s.gml' % f).read() for f in ('scr_damage', 'scr_damage_maxhp', 'scr_damage_fixed'))
for _o in sorted(set(re.findall(r'\b(obj_\w+)', _src))):
    if _o not in sim.objects:
        try: sim.define_object(_o)
        except Exception: pass
for _v in sorted(set(re.findall(r'\b(spr_\w+|snd_\w+)', _src))):
    try: sim.define_asset(_v)
    except Exception: pass
SET = ('global.inv=-1; global.chapter=3; global.hp=[0,160,190,140,90]; global.maxhp=[0,160,190,140,90]; global.battledf=[0,0,0,0,0]; '
       'global.charcantarget=[1,1,1]; global.targeted=[0,0,0,0]; global.chardead=[0,0,0]; global.tension=0; global.invc=1; '
       'global.charinstance=[instance_create(0,0,obj_b),instance_create(0,0,obj_b),instance_create(0,0,obj_b),instance_create(0,0,obj_b)]; for(var _q=0;_q<4;_q++){global.charinstance[_q].myheight=0;} '
       'global.chararmor1=[0,0,0,0,0]; global.chararmor2=[0,0,0,0,0]; global.charweapon=[0,0,0,0,0]; global.battleat=[0,10,10,10,10]; global.mnfight=2; global.charaction=[0,0,0]; global.charspecial=[0,0,0]; '
       'global.charmove=[0,0,0]; global.faceaction=[0,0,0]; global.charauto=[0,0,0]; global.flag=array_create(10000,0); global.char=[1,2,3];'
       'with (obj_dmgwriter) instance_destroy(); with (obj_knight_enemy) instance_destroy(); global.KE = instance_create(0,0,obj_knight_enemy); '
       'global.KE.aoedamage = false; global.KE.myattackchoice = 1; global.KE.damagecounter = 0; global.KE.difficulty = 0; global.KE.practicemode = 0; global.KE.k_gloom = [0,0,0,0,0]; '
       'global.KE.damagereduction = 1; global.KE.myself = 0; global.KE.buttonsparked = [[0,0,0,0,0],[0,0,0,0,0],[0,0,0,0,0],[0,0,0,0,0]]; global.KE.phase = 1; global.KE.phasing = 0;')
def run(variant, infhp, target, dmg, fn='scr_damage'):
    sim.run(SET)
    sim.run('global.knight_variant = %d; global.knight_run = 1; global.krun = { state: "battle", cfg: knight_cfg_default(), party: [1,2,3] }; global.krun.cfg.infhp = %d;' % (variant, infhp))
    good, err = True, None
    try:
        sim.run('var _b = instance_create(0,0,obj_b); _b.target = %d; _b.damage = %d; _b.element = 0; _b.grazed = 0; with (_b) { %s(); }' % (target, dmg, fn))
    except Exception as e:
        good, err = False, str(e)[:160]
    hp = [sim.eval('global.hp[%d]' % i) for i in range(1, 4)]
    sim.run('global.DW = 0; with (obj_dmgwriter) { if (damage > global.DW) global.DW = damage; }')
    return good, err, hp, sim.eval('global.DW')
K = ['base', 'kaizo', 'elec', 'violet', 'thorn', 'cyan']
for v, key in enumerate(K):
    good, err, hp, dw = run(v, 1, 0, 90)
    ok(good, '%s: a hit runs with INFINITE HP (%s)' % (key, err))
    eq(hp, [160, 190, 140], '%s INFINITE HP: the hit takes no HP' % key)
    ok(dw > 0, '%s INFINITE HP: the damage number still shows (%s)' % (key, dw))
    good, err, hp, dw = run(v, 1, 0, 99999)
    eq(min(hp) > 0, True, '%s INFINITE HP: a huge hit downs nobody (%s)' % (key, hp))
    good, err, hp, dw = run(v, 1, 3, 90)
    ok(good, '%s: a party-wide hit runs (%s)' % (key, err))
    eq(hp, [160, 190, 140], '%s INFINITE HP: the party-wide hit takes no HP' % key)
    good, err, hp, dw = run(v, 0, 0, 90)
    ok(good and sum(hp) < 160 + 190 + 140, '%s off: the hit takes HP (%s) %s' % (key, hp, err))
    good, err, hp, dw = run(v, 1, 0, 90, 'scr_damage_maxhp')
    ok(good, '%s: a max-HP hit runs (%s)' % (key, err))
    eq(hp, [160, 190, 140], '%s INFINITE HP: the max-HP hit takes no HP' % key)
    print(key, 'ok %.0fs' % (time.time() - t0), flush=True)

# drains
rd = lambda f: open(M + f, encoding='utf8', errors='replace').read()
ST = rd('gml_Object_obj_knight_enemy_Step_0.gml'); S2 = rd('gml_Object_obj_knight_enemy_Step_2.gml')
ok('global.hp[_char] -= knight_infhp_cut(_frdmg);' in ST, "Kaizo: the turned-back SnowGrave goes through the cut")
ok('global.hp[i] -= knight_infhp_cut(1);' in S2, 'Kaizo: GLOOM drains through the cut')
ok(rd('gml_GlobalScript_scr_damage.gml').count('k_gloom[chartarget] += knight_infhp_cut(_gloomdmg)') >= 1, 'Kaizo: hits build no GLOOM')
BC = rd('gml_Object_obj_battlecontroller_Step_0.gml')
ok(BC.count('-= knight_infhp_cut(1);') >= 2, 'ThornRing drains go through the cut')
print('infhp38 tests', N[0], 'fails', len(FAILS), '%.0fs' % (time.time() - t0)); sys.exit(1 if FAILS else 0)
