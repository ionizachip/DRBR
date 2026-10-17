"""Build 50: no stray triangle - Flowery's moves never make Chapter 3's spr_swatchling_shockwave (one tall white spike) when he
lands: MY JARONA, LAST JARONA and his FIGHT (Jarona). Usage: python3 t_noshock50.py [key ...]"""
import sys, os, time
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
      ['spr_headflowery', 'spr_bnameflowery', 'spr_ja_bnameflowery', 'spr_swatchling_shockwave', 'spr_flowery_crescent_only']


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
    sim.run('global.knight_fl = undefined; knight_fl_register();')
    for o in ('obj_marker', 'obj_marker_animateOnce', 'obj_knight_herocc', 'obj_knight_omega', 'obj_afterimage', 'obj_knight_vignette', 'obj_battleblcon', 'obj_spellphase', 'obj_marker_animateOnce'):
        try:
            sim.define_object(o)
        except Exception:
            pass
    sim._snapauto = True
    for o in ('obj_herokris', 'obj_herosusie', 'obj_heronoelle', 'obj_knight_herocc'):
        auto(sim, lambda: sim.run('with(%s) instance_destroy();' % o))
    sim.run('global.hp=[0,140,140,140,90,0,0]; global.maxhp=[0,140,140,140,140,0,0]; global.at=[0,10,14,8,6,0,0]; global.df=[0,2,2,2,1,0,0]; global.mag=[0,0,1,10,12,0,0];'
            'global.charname=["","Kris","Susie","Ralsei","Noelle"," "," "]; global.charauto=[0,0,0,0,0,0,0]; for (var _c = 0; _c < 7; _c++) { for (var _j = 0; _j < 12; _j++) global.spell[_c][_j] = 0; }'
            'for (var _c = 0; _c < 7; _c++) { global.charweapon[_c] = 0; global.chararmor1[_c] = 0; global.chararmor2[_c] = 0; for (var _q = 0; _q < 4; _q++) { global.itemat[_c][_q] = 0; global.itemdf[_c][_q] = 0; global.itemmag[_c][_q] = 0; } } global.knight_cc_inited = [];')
    sim.run('global.monster=[1,0,0];global.monsterattackname=["","",""];global.monstername=["","",""];global.monstergold=[0,0,0,0];global.monsterexp=[0,0,0,0];global.monsterdef=[0,0,0];global.monsterinstance=[0,0,0];global.monsterhp=[7300,0,0];global.monstermaxhp=[7300,0,0];global.monsterat=[10,0,0];global.monsterdf=[0,0,0];global.monstertype=[0,0,0];global.monsterstatus=[0,0,0];global.charcantarget=[1,1,1];global.targeted=[0,0,0,0,0];global.charaction=[0,0,0];global.charspecial=[0,0,0];global.acting=[0,0,0,0,0];global.faceaction=[0,0,0];global.charmove=[0,0,0];global.mnfight=0;global.inv=-1;global.invc=1;global.turntimer=0;global.bmenuno=0;global.myfight=0;global.fighting=0;global.msc=0;global.typer=5;global.automiss=[0,0,0];global.hittarget=[0,0,0];global.chartarget=[0,0,0];global.tension=0;global.maxtension=250;global.battleat=[10,12,9];global.battlemag=[5,3,14];global.battledf=[0,0,0];global.monsterx=[300,0,0];global.monstery=[100,0,0];global.heromakex=[100,100,100];global.heromakey=[160,240,320];global.charturn=0;')
    ok_, err = auto(sim, lambda: sim.run('with(obj_battlecontroller) instance_destroy(); instance_create(0,0,obj_battlecontroller); with(obj_knight_enemy) instance_destroy(); global.K=instance_create(300,100,obj_knight_enemy); global.K.myself=0; global.monsterinstance[0]=global.K;'))
    if not ok_:
        return ('create', err)
    ok_, err = auto(sim, lambda: sim.run('global.knight_run = 1; var _c = knight_cfg_default(); _c.party = [1,2,5];'
                                         'global.krun = knight_run_new({src: _c, cfg: _c, plan: [knight_find_key("%s")], reveal: ""}); global.krun.state = "battle";'
                                         'global.char = [global.krun.party[0], global.krun.party[1], global.krun.party[2]]; knight_cc_spells_apply(); knight_cc_stats(); knight_cc_gear_default(false); knight_party_full_heal(); knight_cc_battle_begin();' % key))
    if not ok_:
        return ('run', err)
    ok_, err = auto(sim, lambda: sim.run('global.charinstance=[instance_create(100,160,obj_herokris), instance_create(100,240,obj_herosusie), noone];'
                                         'for (var _i = 0; _i < 2; _i++) with (global.charinstance[_i]) { myself = _i; myheight = 60; mywidth = 30; tu = 0; healnum = 0; state = 0; }'
                                         'with (obj_battlecontroller) { havechar = [0,0,0,0,0]; charpos = [0,0,0,0,0]; knight_cc_hero_make(2); }'
                                         'with (global.charinstance[2]) { tu = 0; healnum = 0; state = 0; }'
                                         'if (!variable_global_exists("bmenucoord") || !is_array(global.bmenucoord)) global.bmenucoord = []; for (var _m = 0; _m < 15; _m++) global.bmenucoord[_m] = [0, 0, 0];'
                                         'global.K.phase = 1; global.K.phasing = false; global.K.unleash_con = 0; global.K.holdbreathcount = 0; global.K.braveried = false;'
                                         'var _nm = ["canact","actcost","actname","actdesc","actsimul","canactsus","actcostsus","actnamesus","actdescsus","canactral","actcostral","actnameral","actdescral","canactnoe","actcostnoe","actnamenoe","actdescnoe","battlespell","battlespellcost","battlespellname","battlespelldesc","battlespelltarget","battlespellspecial"]; for (var _q = 0; _q < array_length(_nm); _q++) { var _ar = []; for (var _r = 0; _r < 3; _r++) { _ar[_r] = array_create(12, 0); } variable_global_set(_nm[_q], _ar); } global.battleactcount = [0, 0, 0];'
                                         'scr_spellmenu_setup();'))
    if not ok_:
        return ('hero', err)
    res = {}
    for sid in (17, 23):
        sim.run('global.SHK = 0; global.monster[0] = 1; global.chartarget = [0, 0, 0]; global.tension = 250;')
        ok_, err = auto(sim, lambda: sim.run('with (global.K) scr_spell(%d, 2);' % sid))
        if not ok_:
            return ('cast%d' % sid, err)
        n = 0
        while sim.eval('!is_undefined(global.knight_ks)') and n < 400:
            auto(sim, lambda: sim.run('global.mnfight = 1.5; knight_kspell_tick(); with (obj_marker_animateOnce) { if (sprite_index == spr_swatchling_shockwave) global.SHK++; }'))
            n += 1
        res[sid] = [n, sim.eval('global.SHK'), sim.eval('instance_number(obj_marker_animateOnce)')]
    res['a'] = sim.eval('knight_fl_a().shock')
    return ('ok', res)


for key in (sys.argv[1:] or ['base', 'violet']):
    r = run(key)
    print(key, r[0], str(r[1])[:400], flush=True)
    if r[0] != 'ok':
        ok(False, key + ': ' + str(r[1])[:300]); continue
    res = r[1]
    ok(res['a'] == -1, key + ': no shockwave sprite in his registry')
    ok(res[17][1] == 0 and 0 < res[17][0] < 400, key + ': MY JARONA: no spike / triangle at any frame (it ran to its end) %r' % res[17])
    ok(res[23][1] == 0 and 0 < res[23][0] < 400, key + ': LAST JARONA: no spike / triangle at any frame (landings included) %r' % res[23])
print('%d checks, %d failed' % (N[0], len(FAILS)))
for f_ in FAILS:
    print('FAILED:', f_)
sys.exit(1 if FAILS else 0)
