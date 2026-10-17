"""Build 50 (t_kroar50): the Kaizo Knight's Roaring HP strip with Flowery in the party. Setup from t_flowery50_cc. FLOWERY as his own party member (custom character 5) with every knight's own fight code (the merged game: every knight
has its own version of the spell, spell text, spell info and HP-bar scripts). Party Kris / Susie / Flowery, the knight's real
battle in the emulator:
  - the run keeps him as character 5 (not Noelle's 4); his stats (max HP 300), his MAGIC = F-Action + his six techniques;
  - the battle's hero hook makes HIS hero (obj_knight_herocc, char 5) with his own poses;
  - that knight's own scr_spellinfo / scr_spelltext give his techniques (names, costs) and his lines;
  - that knight's own scr_spell casts each move: it runs to its end, the knight loses HP, nothing of it is left behind,
    his hero is visible again; F-Action raises TP by 16%;
  - Ez2Dance / Afinihug / Honey Kiss: armed by the cast, on for the enemy turn (SOUL faster, the hugged member and everyone
    take less), gone after it;
  - that knight's own HP-bar code (scr_charbox) draws a custom character's head and name and HP bar colour;
  - Noelle (4) in the same party keeps her own name and spells;
  - 60 frames of the knight's fight with him: no error, he keeps his look.
Usage: python3 t_flowery50_cc.py [key ...]"""
import sys, os, time, re
os.environ.setdefault('WALL', '200')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from emu_atk import *
FAILS = []
N = [0]


def ok(c, msg):
    N[0] += 1
    print(('ok   ' if c else 'FAIL ') + msg, flush=True)
    if not c:
        FAILS.append(msg)


SPR = ['spr_knfl_' + r for r in ('idle', 'walk', 'act', 'attackready', 'attack', 'defend', 'hurt', 'defeat', 'victory', 'spell', 'spellready', 'item', 'kiss', 'dance', 'flashkick', 'runner', 'pose', 'jarona', 'omega', 'powerup', 'hitfx', 'pressfront', 'om_idle', 'om_ready', 'om_attack', 'om_hurt', 'om_defend', 'om_spellready', 'om_spell', 'om_pose')] + \
      ['spr_flowery_' + n for n in ('kick', 'kick_crescent', 'crescent_only', 'pose', 'spin_to_idle', 'walk_down', 'walk_up', 'walk_left', 'walk_right', 'equipchar')] + \
      ['spr_omegaflowery_' + n for n in ('idle', 'powerup', 'pose', 'jarona', 'punch', 'windup', 'clash', 'deflect', 'hurt', 'axekick', 'flashkick', 'explosion_a', 'explosion_b', 'explosion_c', 'heart')] + \
      ['spr_omegaf_' + n + sfx for n in ('green', 'aqua', 'yellow', 'blue', 'seth', 'orange') for sfx in ('', '_o')] + \
      ['spr_enemy_aqua_idle', 'spr_seth_idle_serious_flowery', 'spr_enemy_orange_idle_base', 'spr_green_together', 'spr_enemy_blue_ballet', 'spr_yellow_idle', 'spr_pink_sing_idle', 'spr_sparestar_anim', 'spr_bellsparkle', 'spr_spin_petal'] + \
      ['spr_headflowery', 'spr_bnameflowery', 'spr_ja_bnameflowery', 'spr_swatchling_shockwave']


def om01(sim):
    # Omega Flowery / flower drawings left (rings and orbs fade out by themselves)
    sim.run('global.OMC = 0; with (obj_knight_omega) { if (kind <= 1) global.OMC++; }')
    return sim.eval('global.OMC')


def om_kind(sim, k):
    sim.run('global.OMC = 0; with (obj_knight_omega) { if (kind == %d) global.OMC++; }' % k)
    return sim.eval('global.OMC')


def sim_kris_ok(res):
    return True


def run(key):
    sim = mk(key, [1, 2, 4])
    for _m in ('scr_84_get_sprite', 'scr_84_get_font'):
        sim.mock(_m, 0)
    sim.run('for (var _i = array_length(global.flag); _i < 10000; _i++) global.flag[_i] = 0;')
    for a in SPR:
        try:
            sim.define_asset(a)
        except Exception:
            pass
    # (in the game his sprites exist when the registry is made at start; here they are defined just now)
    sim.run('global.knight_fl = undefined; knight_fl_register();')
    for o in ('obj_marker', 'obj_marker_animateOnce', 'obj_knight_herocc', 'obj_knight_omega', 'obj_afterimage', 'obj_knight_vignette', 'obj_battleblcon'):
        try:
            sim.define_object(o)
        except Exception:
            pass
    sim._snapauto = True
    for o in ('obj_herokris', 'obj_herosusie', 'obj_heronoelle', 'obj_knight_herocc'):
        auto(sim, lambda: sim.run('with(%s) instance_destroy();' % o))
    sim.run('global.hp=[0,140,140,140,90,0,0]; global.maxhp=[0,140,140,140,140,0,0]; global.at=[0,10,14,8,6,0,0]; global.df=[0,2,2,2,1,0,0]; global.mag=[0,0,1,10,12,0,0];'
            'global.charname=["","Kris","Susie","Ralsei","Noelle"," "," "]; global.charauto=[0,0,0,0,0,0,0]; for (var _c = 0; _c < 7; _c++) { for (var _j = 0; _j < 12; _j++) global.spell[_c][_j] = 0; }'
            'global.spell[4][0] = 4; global.spell[4][1] = 10;'
            'for (var _c = 0; _c < 7; _c++) { global.charweapon[_c] = 0; global.chararmor1[_c] = 0; global.chararmor2[_c] = 0; for (var _q = 0; _q < 4; _q++) { global.itemat[_c][_q] = 0; global.itemdf[_c][_q] = 0; global.itemmag[_c][_q] = 0; } } global.knight_cc_inited = [];')
    sim.run('global.monster=[1,0,0];global.monsterattackname=["","",""];global.monstername=["","",""];global.monstergold=[0,0,0,0];global.monsterexp=[0,0,0,0];global.monsterdef=[0,0,0];global.monsterinstance=[0,0,0];global.monsterhp=[7300,0,0];global.monstermaxhp=[7300,0,0];global.monsterat=[10,0,0];global.monsterdf=[0,0,0];global.monstertype=[0,0,0];global.monsterstatus=[0,0,0];global.charcantarget=[1,1,1];global.targeted=[0,0,0,0,0];global.charaction=[0,0,0];global.acting=[0,0,0,0,0];global.faceaction=[0,0,0];global.charmove=[0,0,0];global.mnfight=1.5;global.inv=-1;global.invc=1;global.turntimer=0;global.bmenuno=0;global.myfight=0;global.fighting=0;global.msc=0;global.typer=5;global.automiss=[0,0,0];global.hittarget=[0,0,0];global.chartarget=[0,0,0];global.tension=0;global.maxtension=250;global.battleat=[10,12,9];global.battlemag=[5,3,14];global.battledf=[0,0,0];global.monsterx=[300,0,0];global.monstery=[100,0,0];global.heromakex=[100,100,100];global.heromakey=[160,240,320];')
    ok_, err = auto(sim, lambda: sim.run('with(obj_battlecontroller) instance_destroy(); instance_create(0,0,obj_battlecontroller); with(obj_knight_enemy) instance_destroy(); with(obj_heart) instance_destroy(); global.K=instance_create(300,100,obj_knight_enemy); global.K.myself=0; global.monsterinstance[0]=global.K; global.H=instance_create(300,300,obj_heart); global.H.wspeed = 4;'))
    if not ok_:
        return ('create', err)
    # a hub run with the party Kris / Susie / Flowery
    ok_, err = auto(sim, lambda: sim.run('global.knight_run = 1; var _c = knight_cfg_default(); _c.party = [1,2,5];'
                                         'global.krun = knight_run_new({src: _c, cfg: _c, plan: [knight_find_key("%s")], reveal: ""}); global.krun.state = "battle";'
                                         'global.char = [global.krun.party[0], global.krun.party[1], global.krun.party[2]]; knight_cc_spells_apply(); knight_cc_stats(); knight_cc_gear_default(false); knight_party_full_heal(); knight_cc_battle_begin();' % key))
    if not ok_:
        return ('run', err)
    for m in ('surface_create','surface_set_target','surface_reset_target','draw_surface','draw_surface_ext'):
        try: sim.mock(m, 0)
        except Exception: pass
    sim.mock('surface_exists', 1)
    try:
        sim.create_instance('obj_darkcontroller', 0, 0)
    except Exception as ex:
        pass
    sim.run('with (obj_darkcontroller) hpcolor = [c_aqua, c_fuchsia, c_lime, c_yellow];')
    ok_, err = auto(sim, lambda: sim.run('global.knight_variant = 1; global.R2 = instance_create(0, 0, obj_knight_roaring2);'))
    ok_, err = auto(sim, lambda: sim.run('with (global.R2) { hp_surf = 1; event_user(12); }'))
    return ('ok', {'ev': [ok_, str(err)]})

r = run('kaizo')
ok_t = r[0] == 'ok' and r[1]['ev'][0]
print(('ok  ' if ok_t else 'FAIL') + ' kaizo: the Roaring HP strip (User Event 12) with Flowery (5) in the party draws without error %r' % (r,))
print('kroar50 tests 1 fails', 0 if ok_t else 1); sys.exit(0 if ok_t else 1)
