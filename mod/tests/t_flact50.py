"""Build 50: Flowery's ACT - the first entry of his MAGIC ("ACT", 27) opens his own ACT list in the MAGIC menu (like Kris's
ACT entry): Check / HoldBreath / F-Action, and in the Elec Knight's phase 5 Unleash and Bravery. X goes back to his MAGIC,
a pick (or his turn over) gives him his MAGIC back. Unleash: the SOUL's light (obj_purify_event) from him; the spell phase
waits for it; it does nothing when another Unleash is under way. Usage: python3 t_flact50.py [key ...]"""
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
      ['spr_headflowery', 'spr_bnameflowery', 'spr_ja_bnameflowery']


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
    for o in ('obj_marker', 'obj_marker_animateOnce', 'obj_knight_herocc', 'obj_knight_omega', 'obj_afterimage', 'obj_knight_vignette', 'obj_battleblcon', 'obj_spellphase'):
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
    res['spl0'] = sim.py(sim.eval('global.spell[5]'))[:3]
    sim.run('with (global.K) { scr_spellinfo(27); global.SI = [spellname, cost, spelltarget]; }')
    res['info27'] = sim.py(sim.eval('global.SI'))
    res['sp0'] = [sim.eval('global.battlespell[2][0]'), sim.eval('global.battlespellspecial[2][0]'), sim.eval('global.battlespellspecial[2][1]')]
    # his turn, MAGIC open, cursor on ACT: the battle's ACT hook
    ok_, err = auto(sim, lambda: sim.run('global.charturn = 2; global.bmenuno = 2; global.bmenucoord[2][2] = 0;'
                                         'global.AP = knight_kris_actpick(2); global.AM = knight_actpick_menu(2); global.charturn = 0; global.AK = [knight_actpick_menu(0)]; global.charturn = 2;'
                                         'global.bmenuno = global.AM;'))
    if not ok_:
        return ('open', err)
    res['open'] = [sim.eval('global.AP'), sim.eval('global.AM'), sim.eval('global.AK[0]'), sim.py(sim.eval('global.spell[5]'))[:5],
                   [sim.eval('global.battlespellspecial[2][%d]' % i) for i in range(3)], sim.eval('global.battlespellname[2][0]')]
    # still open while his MAGIC is up
    ok_, err = auto(sim, lambda: sim.run('knight_fl_act_tick();'))
    res['stay'] = [sim.eval('global.spell[5][0]'), sim.eval('global.bmenuno')]
    # X: the battle went back to the main menu (twobuffer just set) - back to his MAGIC, on ACT
    ok_, err = auto(sim, lambda: sim.run('global.bmenuno = 0; global.charaction[2] = 0; obj_battlecontroller.twobuffer = 0; knight_fl_act_tick();'))
    if not ok_:
        return ('back', err)
    res['back'] = [sim.eval('global.bmenuno'), sim.eval('global.spell[5][0]'), sim.eval('global.bmenucoord[2][2]'), sim.eval('knight_fl_act_on()')]
    # pick HoldBreath: confirmed (charaction 2, his turn over) - MAGIC back, no menu change
    ok_, err = auto(sim, lambda: sim.run('obj_battlecontroller.twobuffer = -20; global.bmenuno = 2; knight_kris_actpick(2); global.charaction[2] = 2; global.charspecial[2] = 29; global.charturn = 3; global.bmenuno = 0; knight_fl_act_tick();'
                                         'global.BR = knight_fl_breath(); with (global.K) scr_spelltext(29, 2); global.T29 = global.msg[0]; with (global.K) scr_spell(29, 2);'))
    if not ok_:
        return ('pick', err)
    res['pick'] = [sim.eval('global.bmenuno'), sim.eval('global.spell[5][0]'), sim.eval('global.knight_fl_actmenu'), sim.eval('global.BR'), sim.eval('global.K.holdbreathcount'), sim.eval('global.T29')]
    n = 0
    while sim.eval('!is_undefined(global.knight_ks)') and n < 100:
        auto(sim, lambda: sim.run('knight_kspell_tick();'))
        n += 1
    res['pickend'] = n
    # the Elec Knight's phase 5: Unleash and Bravery in his ACT list
    sim.run('global.K.phase = 5; global.K.phasing = true; global.K.unleash_con = 0; global.charturn = 2; global.bmenuno = 2; global.charaction[2] = 0; global.bmenucoord[2][2] = 0;')
    ok_, err = auto(sim, lambda: sim.run('global.AP = knight_kris_actpick(2); with (global.K) { scr_spellinfo(26); global.SI = [spellname, cost, spelltarget]; scr_spellinfo(30); global.SI2 = [spellname, cost]; }'))
    if not ok_:
        return ('open5', err)
    res['p5'] = [sim.eval('global.AP'), sim.py(sim.eval('global.spell[5]'))[:6], sim.py(sim.eval('global.SI')), sim.py(sim.eval('global.SI2')), sim.eval('knight_fl_elec5()')]
    # cast Unleash: the text, then the light from him; the spell phase is held while it lasts
    ok_, err = auto(sim, lambda: sim.run('global.charaction[2] = 2; global.charturn = 3; global.bmenuno = 0; knight_fl_act_tick();'
                                         'with (obj_spellphase) instance_destroy(); global.SP = instance_create(0, 0, obj_spellphase); global.SP.spelltimer = 50; global.SP.active = 1;'
                                         'with (obj_writer) instance_destroy(); with (global.K) scr_spelltext(26, 2); global.T26 = global.msg[0]; with (global.K) scr_spell(26, 2);'))
    if not ok_:
        return ('unleash', err)
    t0 = []
    for i in range(12):
        auto(sim, lambda: sim.run('knight_kspell_tick();'))
    t0 = [sim.eval('instance_number(obj_purify_event)'), sim.eval('!is_undefined(global.knight_ks)'), sim.eval('global.SP.spelltimer'),
          sim.eval('instance_exists(obj_purify_event) ? round(instance_find(obj_purify_event, 0).x) : -1'), sim.eval('round(global.charinstance[2].x)')]
    # the light is over
    auto(sim, lambda: sim.run('with (obj_purify_event) instance_destroy();'))
    for i in range(3):
        auto(sim, lambda: sim.run('knight_kspell_tick();'))
    res['un'] = [sim.eval('global.T26'), sim.eval('global.spell[5][0]')] + t0 + [sim.eval('is_undefined(global.knight_ks)'), sim.eval('global.charinstance[2].image_alpha')]
    # another Unleash under way (Susie's): his does nothing
    sim.run('global.K.unleash_con = 2;')
    ok_, err = auto(sim, lambda: sim.run('with (global.K) scr_spelltext(26, 2); global.T26b = global.msg[0]; with (global.K) scr_spell(26, 2);'))
    for i in range(40):
        auto(sim, lambda: sim.run('knight_kspell_tick();'))
    res['fz'] = [sim.eval('global.T26b'), sim.eval('instance_number(obj_purify_event)'), sim.eval('is_undefined(global.knight_ks)')]
    # out of phase 5: no Unleash in the list
    sim.run('global.K.phase = 3; global.K.phasing = false; global.K.unleash_con = 0; global.charturn = 2; global.bmenuno = 2; global.charaction[2] = 0;')
    auto(sim, lambda: sim.run('knight_kris_actpick(2);'))
    res['p3'] = sim.py(sim.eval('global.spell[5]'))[:4]
    auto(sim, lambda: sim.run('global.bmenuno = 3; knight_fl_act_tick();'))
    # OMEGA FLOWERY in phase 5: his ACT entry first (for Unleash), out of it only LAST JARONA / PRISM RUSH / SMILE AGAIN
    ok_, err = auto(sim, lambda: sim.run('global.knight_fl_om.on = true; global.K.phase = 5; global.K.phasing = true; knight_fl_act_tick(); global.OM5 = [global.spell[5][0], global.spell[5][1]];'
                                         'global.K.phase = 3; global.K.phasing = false; knight_fl_act_tick(); global.OM3 = [global.spell[5][0], global.spell[5][1], global.spell[5][2], global.spell[5][3]]; global.knight_fl_om.on = false;'))
    res['om'] = [sim.py(sim.eval('global.OM5')), sim.py(sim.eval('global.OM3'))] if ok_ else ('err', err)
    return ('ok', res)


keys = sys.argv[1:] or ['base', 'elec', 'kaizo']
for key in keys:
    t = time.time()
    r = run(key)
    print(key, r[0], str(r[1])[:900], round(time.time() - t, 1), flush=True)
    if r[0] != 'ok':
        ok(False, '%s: %s %s' % (key, r[0], str(r[1])[:300]))
        continue
    res = r[1]
    ok(res['spl0'][0] == 27 and res['info27'] == ['ACT', 0, 0] and res['sp0'] == [27, 1, 0], key + ': his MAGIC starts with ACT (27, ACT colour) %r' % [res['spl0'], res['info27'], res['sp0']])
    o = res['open']
    ok(o[0] in (True, 1) and o[1] == 2 and o[2] == 11 and o[3][:3] == [28, 29, 22] and o[3][3] == 0 and o[4] == [1, 1, 1] and o[5] == 'Check',
       key + ': ACT picked: the MAGIC menu stays (Kris\'s ACT entry still opens 11), now his ACT list Check / HoldBreath / F-Action %r' % o)
    ok(res['stay'] == [28, 2], key + ': the list stays while his MAGIC is open %r' % res['stay'])
    ok(res['back'] == [2, 27, 0, False] or res['back'] == [2, 27, 0, 0], key + ': X in his ACT list: back to his MAGIC, on ACT %r' % res['back'])
    p = res['pick']
    ok(p[0] == 0 and p[1] == 27 and p[2] == 0 and p[3] == 0 and p[4] == 1 and 'SOUL now moves faster' in p[5] and res['pickend'] < 60,
       key + ': HoldBreath picked: MAGIC back, the knight\'s hold-breath on (SOUL faster), his pose ends %r' % [p, res['pickend']])
    p5 = res['p5']
    if key == 'elec':
        ok(p5[0] in (True, 1) and p5[1][:5] == [28, 29, 26, 30, 22] and p5[2] == ['Unleash', 200, 0] and p5[3][0] == 'Bravery' and p5[4] in (True, 1),
           key + ': phase 5: Unleash (200 TP) and Bravery in his ACT list %r' % p5)
        u = res['un']
        ok(u[0] == '* Your SOUL emitted a brilliant light!/%' and u[1] == 27 and u[2] == 1 and u[3] in (True, 1) and u[4] < 5 and abs(u[5] - (u[6] + 30)) <= 2 and u[7] in (True, 1) and u[8] == 1,
           key + ': Unleash: the SOUL\'s light (obj_purify_event) from him, the spell phase held while it lasts, then over with his hero back %r' % u)
        ok('nothing happened' in res['fz'][0] and res['fz'][1] == 0 and res['fz'][2] in (True, 1), key + ': another Unleash under way: his does nothing (no second light) %r' % res['fz'])
        ok(res['om'][0] == [27, 23] and res['om'][1] == [23, 19, 25, 0], key + ': OMEGA FLOWERY: ACT first only in phase 5 (for Unleash), otherwise LAST JARONA / PRISM RUSH / SMILE AGAIN %r' % (res['om'],))
    else:
        ok(p5[1][:3] == [28, 29, 22] and p5[4] in (False, 0), key + ': not the Elec Knight: no Unleash / Bravery %r' % p5)
    ok(res['p3'][:3] == [28, 29, 22] and res['p3'][3] == 0, key + ': out of phase 5: no Unleash %r' % res['p3'])
print('%d checks, %d failed' % (N[0], len(FAILS)))
for f_ in FAILS:
    print('FAILED:', f_)
sys.exit(1 if FAILS else 0)
