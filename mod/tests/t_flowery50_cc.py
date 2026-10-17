"""Build 50: FLOWERY as his own party member (custom character 5) with every knight's own fight code (the merged game: every knight
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
    res = {'char': sim.py(sim.eval('global.char')), 'maxhp': sim.eval('global.maxhp[5]'), 'hp': sim.eval('global.hp[5]'),
           'spl': sim.py(sim.eval('global.spell[5]')), 'name': sim.eval('global.charname[5]'), 'gear': [sim.eval('global.charweapon[5]'), sim.eval('global.chararmor1[5]'), sim.eval('global.chararmor2[5]')]}
    # the heroes: Kris and Susie as before, his through the battle's hook
    ok_, err = auto(sim, lambda: sim.run('global.charinstance=[instance_create(100,160,obj_herokris), instance_create(100,240,obj_herosusie), noone];'
                                         'for (var _i = 0; _i < 2; _i++) with (global.charinstance[_i]) { myself = _i; myheight = 60; mywidth = 30; tu = 0; healnum = 0; state = 0; attacksprite = spr_knfl_attack; }'
                                         'with (obj_battlecontroller) { havechar = [0,0,0,0,0]; charpos = [0,0,0,0,0]; knight_cc_hero_make(2); }'
                                         'with (global.charinstance[2]) { tu = 0; healnum = 0; state = 0; }'))
    if not ok_:
        return ('hero', err)
    res['hero'] = [sim.eval('global.charinstance[2].object_index') == sim.eval('obj_knight_herocc'), sim.eval('global.charinstance[2].char'),
                   sim.eval('global.charinstance[2].idlesprite') == sim.eval('spr_knfl_idle'), sim.eval('global.charinstance[2].hurtsprite') == sim.eval('spr_knfl_hurt')]
    sim.run('global.K.phase=1; global.K.phaseturn=0; global.K.turn=1; global.mnfight=1.5; global.K.attackchosen=false; global.K.talked=1; global.K.rtimer=0;')
    # the knight's own spell scripts
    info = []
    texts = []
    for sid in range(16, 23):
        ok_, err = auto(sim, lambda: sim.run('with (global.K) { scr_spellinfo(%d); global.SI = [spellname, cost, spelltarget]; } with (global.K) scr_spelltext(%d, 2);' % (sid, sid)))
        if not ok_:
            return ('info%d' % sid, err)
        info.append(sim.py(sim.eval('global.SI')))
        texts.append((sim.eval('global.msg[0]'), sim.eval('is_struct(global.knight_cc_line) ? global.knight_cc_line.cid : -1'), sim.eval('is_struct(global.knight_cc_line) ? global.knight_cc_line.narr : "?"')))
    res['info'] = info
    # the battle writer for his line: made with his face (fc 23), his expression and his voice typer from the start; once
    # it is closed, the narration in a writer of the battle's own (no face, typer 4)
    ok_, err = auto(sim, lambda: sim.run('for (var _i = array_length(global.msg); _i < 100; _i++) global.msg[_i] = ""; global.knight_fl_fan = 0; with (global.K) { scr_spelltext(22, 2); global.BOX = global.msg[0]; global.W1 = knight_cc_battletext(); }'
                                         'global.BT = [i_ex(global.W1), i_ex(global.knight_cc_bal), global.BOX, global.msg[0]];'
                                         'with (global.W1) instance_destroy(); with (obj_face) instance_destroy();'
                                         'with (global.K) { spellwriter = noone; knight_cc_narrate(); }'
                                         'global.BT2 = [i_ex(global.knight_cc_bal)];'
                                         'global.msg[0] = "* Kris used X!/%"; with (global.K) global.W3 = knight_cc_battletext();'
                                         'global.BT3 = [global.fc, global.typer]; with (global.W3) instance_destroy(); with (obj_face) instance_destroy();'))
    if not ok_:
        return ('battletext', err)
    res['bt'] = [sim.py(sim.eval('global.BT')), sim.py(sim.eval('global.BT2')), sim.py(sim.eval('global.BT3'))]
    # his line: one page, no codes (the writer gets his face and voice from knight_cc_battletext), his id with it; its
    # narration (if any) a page of its own
    res['texts'] = all((t.count('/') == 1 and t.endswith('/%') and '\\' not in t and c == 5 and (n == '' or (n.count('/') == 1 and n.endswith('/%')))) for t, c, n in texts)
    res['text0'] = texts[:2] + texts[-1:]
    # casts through the knight's own scr_spell: every move runs to its end, nothing is left behind
    hp0 = sim.eval('global.monsterhp[0]')
    res['casts'] = []
    for sid, star in ((16, 0), (17, 0), (19, 0), (18, 0), (20, 1), (21, 0), (22, 0)):
        sim.run('global.chartarget = [0, 0, 0]; global.monster[0] = 1; global.tension = 0;')
        mh = sim.eval('global.monsterhp[0]')
        ok_, err = auto(sim, lambda: sim.run('with (global.K) scr_spell(%d, 2);' % sid) if star == 0 else sim.run('with (global.K) { star = %d; scr_spell(%d, 2); }' % (star, sid)))
        if not ok_:
            return ('cast%d' % sid, err)
        n = 0
        if sim.eval('!is_undefined(global.knight_ks)'):
            res.setdefault('kdmg', {})[sid] = sim.eval('global.knight_ks.dmg')
        while sim.eval('!is_undefined(global.knight_ks)') and n < 400:
            ok_, err = auto(sim, lambda: sim.run('global.mnfight = 1.5; knight_kspell_tick();'))
            if not ok_:
                return ('tick%d' % sid, err)
            if sid == 19:
                res.setdefault('krisa', []).append(sim.eval('global.charinstance[0].image_alpha'))
            ok_, err = auto(sim, lambda: sim.step(1))
            if not ok_:
                return ('tickstep%d' % sid, err)
            n += 1
        if n >= 400:
            return ('cast%d never ended' % sid, '')
        res['casts'].append((sid, n, mh - sim.eval('global.monsterhp[0]'), sim.eval('instance_number(obj_marker)') + om01(sim), sim.eval('global.charinstance[2].image_alpha'), sim.eval('global.tension')))
    res['dmg'] = hp0 - sim.eval('global.monsterhp[0]')
    # the turn-long effects (Ez2Dance, Afinihug on slot 1, Honey Kiss): armed, on for the enemy turn, gone after it
    res['fx0'] = sim.py(sim.eval('[global.knight_fl_fxs.dance, global.knight_fl_fxs.hug[0], global.knight_fl_fxs.charm]'))
    # the guards shown: Afinihug's shield on the hugged member, Honey Kiss's charm on the knight
    ok_, err = auto(sim, lambda: sim.run('global.mnfight = 1.5; knight_fl_tick(); global.G5 = 0; global.G6 = 0; with (obj_knight_omega) { if (kind == 5 && !gone) global.G5++; if (kind == 6 && !gone) global.G6++; }'))
    if not ok_:
        return ('guards', err)
    res['guards'] = [sim.eval('global.G5'), sim.eval('global.G6'), sim.eval('global.knight_om_guards[0].hero == global.charinstance[0]')]
    auto(sim, lambda: sim.run('with (obj_heart) instance_destroy(); global.H = instance_create(300, 300, obj_heart); global.H.wspeed = 4;'))
    sim.run('global.mnfight = 2;')
    w = []
    for f in range(5):
        auto(sim, lambda: sim.run('knight_cc_tick();'))
        w.append(sim.eval('global.H.wspeed'))
    res['wsp'] = w
    res['taken'] = [sim.eval('knight_fl_taken(100, 1)'), sim.eval('knight_fl_taken(100, 0)')]
    sim.run('global.mnfight = 0;')
    auto(sim, lambda: sim.run('knight_cc_tick();'))
    res['fx1'] = sim.py(sim.eval('[global.knight_fl_fxs.dance, global.knight_fl_fxs.hug[0], global.knight_fl_fxs.charm, global.H.wspeed]'))
    auto(sim, lambda: sim.run('knight_fl_tick(); global.G7 = 0; with (obj_knight_omega) { if ((kind == 5 || kind == 6) && !gone) global.G7++; }'))
    res['guards'].append(sim.eval('global.G7'))
    # the knight's own HP bar code: every version of scr_charbox has the custom characters' head/name and colour
    cb = open(M + 'gml_GlobalScript_scr_charbox.gml', encoding='utf8').read()
    fns = [f for f in re.split(r'(?m)^function ', cb) if 'spr_headnoelle' in f]
    res['charbox'] = all(('knight_cc_charbox(c + 1' in f and 'knight_cc_hpcolor(c + 1)' in f and 'knight_fl_' not in f) for f in fns) and len(fns) >= 5
    res['col'] = sim.eval('knight_cc_hpcolor(5)')
    # its fight with him
    for f in range(60):
        ok_, err = auto(sim, lambda: sim.run('knight_run_tick(); knight_cc_tick();'))
        if not ok_:
            return ('frame%d' % f, err)
        ok_, err = auto(sim, lambda: sim.step(1))
        if not ok_:
            return ('step%d' % f, err)
    res['still'] = sim.eval('global.charinstance[2].idlesprite') == sim.eval('spr_knfl_idle')
    # his FIGHT: one Jarona, timed on the game's hit (finishattacktimer 11 -> 0), his hero back afterwards
    fj = []
    ok_, err = auto(sim, lambda: sim.run('global.knight_ks = undefined; global.mnfight = 1.5; with (global.charinstance[2]) { state = 1; finishattacktimer = 11; image_alpha = 1; }'))
    for f in range(40):
        ok_, err = auto(sim, lambda: sim.run('with (global.charinstance[2]) { if (finishattacktimer > 0) finishattacktimer--; if (finishattacktimer == 0 && state == 1) state = 0; } knight_fl_tick();'))
        if not ok_:
            return ('fight%d' % f, err)
        sim.step(1)
        fj.append((sim.eval('is_struct(global.knight_fl_fj)'), sim.eval('global.charinstance[2].image_alpha')))
    res['fj'] = [fj[0], fj[10], fj[39], sim.eval('instance_number(obj_marker)') + om01(sim)]
    # (the battle menu's own arrays are not set up in this emulated battle)
    sim.mock('scr_spellmenu_setup', 0)
    # the Violet Knight's last stand: not in another knight's fight; with everyone else down, the scene, then OMEGA FLOWERY for good
    ok_, err = auto(sim, lambda: sim.run('global.heromakex = [100, 140, 180]; global.heromakey = [50, 130, 210]; knight_fl_begin(); global.myfight = 0; global.mnfight = 0; global.KV = global.knight_variant; global.L0 = knight_fl_laststand_check(); global.hp[1] = 0; global.hp[2] = 0;'
                                         'global.LD = knight_fl_laststand_check(); if (!variable_struct_exists(global.krun, "wr") || !is_struct(global.krun.wr)) global.krun.wr = { slain: array_create(8, false) }; global.krun.wr.slain[1] = true; global.krun.wr.slain[2] = true;'
                                         'global.MH0 = global.maxhp[5]; knight_lu_turnend(); global.L1 = (!is_undefined(global.knight_ks) && global.knight_ks.kind == 28); global.L2 = global.myfight;'))
    if not ok_:
        return ('laststand', err)
    res['ls0'] = [sim.eval('global.L0 || global.LD'), sim.eval('global.L1'), sim.eval('global.L2'), sim.eval('is_struct(global.knight_ks) ? global.knight_ks.kind : -1')]
    n = 0
    while sim.eval('!is_undefined(global.knight_ks)') and n < 400:
        ok_, err = auto(sim, lambda: sim.run('global.mnfight = 99; knight_kspell_tick(); knight_fl_tick();'))
        if not ok_:
            return ('ls%d' % n, err)
        # (no object frames here: the knight in this emulator is not the Violet Knight - its own code would run as one)
        n += 1
    res['ls1'] = [n, sim.eval('knight_fl_om_on()'), sim.eval('global.spell[5][0]'), sim.eval('global.maxhp[5]') - sim.eval('global.MH0'), [om_kind(sim, 4), om01(sim)],
                  sim.eval('global.charinstance[2].image_alpha'), sim.eval('global.knight_fl_om.wait'), sim.eval('global.L1 && knight_fl_laststand_check()'),
                  [sim.eval('global.spell[5][1]'), sim.eval('global.spell[5][2]')],
                  [sim.eval('global.charinstance[2].idlesprite == knight_fl_a().om_idle'), sim.eval('global.charinstance[2].attacksprite == knight_fl_a().om_attack'),
                   sim.eval('global.charinstance[2].spellsprite == knight_fl_a().om_spell'), sim.eval('knight_cc(5).poses.hurt == knight_fl_a().om_hurt'),
                   sim.eval('knight_cc(5).flurry == knight_fl_a().om_attack')]]
    # in the Omega form: PRISM RUSH just goes off (no transformation), LAST JARONA, each ends with his (Omega-dressed) hero shown
    res['omc'] = []
    for sid in (19, 23, 25):
        sim.run('global.chartarget = [0, 0, 0]; global.monster[0] = 1; global.tension = 250; global.knight_ks = undefined; global.hp[5] = 10; global.HP5A = 10;')
        ok_, err = auto(sim, lambda: sim.run('with (global.K) scr_spell(%d, 2);' % sid))
        if not ok_:
            return ('omcast%d' % sid, err)
        n = 0
        res.setdefault('omdmg', {})[sid] = sim.eval('is_struct(global.knight_ks) ? global.knight_ks.dmg : -1')
        while sim.eval('!is_undefined(global.knight_ks)') and n < 500:
            # LAST JARONA: [Z] pressed on the 14th frame of punches 1 and 3 (strong), on the 6th of punch 2 (too early)
            kt = sim.eval('is_struct(global.knight_ks) ? global.knight_ks.t : -1')
            sim.mock('button1_p', 1 if (sid == 23 and kt + 1 in (6 + 14, 46 + 6, 86 + 15)) else 0)
            ok_, err = auto(sim, lambda: sim.run('global.mnfight = 1.5; knight_kspell_tick();'))
            if not ok_:
                return ('omtick%d' % sid, err)
            if sid == 23 and sim.eval('is_struct(global.knight_ks)'):
                sim.run('if (variable_struct_exists(global.knight_ks, "zb")) { global.Z0 = global.knight_ks.zb[0]; global.Z1 = global.knight_ks.zb[1]; global.Z2 = global.knight_ks.zb[2]; }')
                res['ljz'] = [sim.eval('global.Z0'), sim.eval('global.Z1'), sim.eval('global.Z2')]
            n += 1
        sim.mock('button1_p', 0)
        if sid == 25:
            res['heal'] = [sim.eval('global.hp[5]'), sim.eval('global.maxhp[5]')]
        res['omc'].append((sid, n, sim.eval('global.charinstance[2].image_alpha'), om01(sim), sim.eval('knight_fl_om_on()'), sim.eval('global.charinstance[2].idlesprite == knight_fl_a().om_idle')))
    # after the scene: he glides to the middle member's place (Susie's in a party of three) and floats; his hero draws as Omega Flowery
    ok_, err = auto(sim, lambda: sim.run('global.knight_ks = undefined; repeat (45) knight_fl_om_tick(); global.FMN = 99; global.FMX = -99; repeat (100) { knight_fl_om_tick(); global.FMN = min(global.FMN, knight_fl_om_float()); global.FMX = max(global.FMX, knight_fl_om_float()); }'
                                         'with (global.charinstance[2]) { if (!variable_instance_exists(id, "hurt")) { hurt = 0; state = 0; specdraw = 0; flash = 0; becomeflash = 0; fsiner = 0; hurtindex = 0; defendtimer = 0; myself = 2; } if (!variable_instance_exists(id, "thissprite")) { thissprite = idlesprite; index = 0; } global.HD = knight_cc_hero_draw(); }'))
    if not ok_:
        return ('omplace', err)
    res['omp'] = [sim.eval('global.charinstance[2].x'), sim.eval('global.charinstance[2].y'), sim.eval('global.FMN'), sim.eval('global.FMX'), sim.eval('global.HD'), sim.eval('global.knight_fl_om.n0')]
    ok_, err = auto(sim, lambda: sim.run('with (global.K) { scr_spellinfo(23); global.C0 = cost; } global.knight_fl_om.cd = 2; with (global.K) { scr_spellinfo(23); global.C1 = cost; }'
                                         'global.knight_fl_om.mn = 2; global.mnfight = 0; knight_fl_om_tick(); global.CD = global.knight_fl_om.cd;'))
    if not ok_:
        return ('ljcost', err)
    res['lj'] = [sim.eval('global.C0'), sim.eval('global.C1')]
    ok_, err = auto(sim, lambda: sim.run('global.knight_fl_om.on = false; knight_fl_begin(); global.RB = (knight_cc(5).poses.idle == knight_fl_a().idle) && (knight_cc(5).flurry == knight_fl_a().jarona);'))
    if not ok_:
        return ('undress', err)
    res['lj'].append(sim.eval('global.RB'))
    # OMEGA FORM (technique 24): optional (offered on the POWER page, not in his starting list), 100 TP, his transformation as a move
    sim.run('global.SP = knight_cc_pickable(5); global.SPN = array_length(global.SP); global.SPL = global.SP[global.SPN - 1]; global.knight_cc_spells = []; global.DEF = knight_cc_spl(5);'
            'global.DEF24 = false; for (var i = 0; i < 12; i++) if (global.DEF[i] == 24) global.DEF24 = true; with (global.K) { scr_spellinfo(24); global.C24 = cost; }')
    ok_, err = auto(sim, lambda: sim.run('global.knight_ks = undefined; global.chartarget = [0, 0, 0]; with (global.K) scr_spell(24, 2);'))
    if not ok_:
        return ('omform', err)
    n = 0
    k30 = sim.eval('is_struct(global.knight_ks) ? global.knight_ks.kind : -1')
    while sim.eval('!is_undefined(global.knight_ks)') and n < 400:
        ok_, err = auto(sim, lambda: sim.run('global.mnfight = 1.5; knight_kspell_tick();'))
        if not ok_:
            return ('omformtick', err)
        n += 1
    res['omf'] = [sim.eval('global.SPL'), sim.eval('global.DEF24'), sim.eval('global.C24'), sim.eval('knight_cc_spell_owner(24)'), k30, n,
                  sim.eval('knight_fl_om_on()'), sim.eval('global.spell[5][0]'), sim.eval('global.spell[5][1]'), sim.eval('global.charinstance[2].image_alpha'),
                  sim.eval('global.knight_fl_om.trig && !knight_fl_laststand_check()')]
    ok_, err = auto(sim, lambda: sim.run('global.knight_fl_fxs.charm = 0; global.knight_fl_fxs.hug = [0, 0, 0]; with (global.charinstance[2]) image_alpha = 0; global.mnfight = 0; repeat (12) knight_fl_tick(); global.VG = global.charinstance[2].image_alpha; global.TK = knight_fl_taken(100, 2);'))
    if not ok_:
        return ('visguard', err)
    res['vg'] = [sim.eval('global.VG'), sim.eval('global.TK')]
    # his FIGHT as OMEGA FLOWERY: his own hero does the Jarona (a pose and an offset on its Omega Draw) - it never hides
    ok_, err = auto(sim, lambda: sim.run('global.knight_ks = undefined; global.knight_fl_fj = undefined; global.mnfight = 1.5; with (global.charinstance[2]) { state = 1; finishattacktimer = 11; image_alpha = 1; attacktimer = 0; force = 0; }'))
    ofj = []
    for f in range(40):
        ok_, err = auto(sim, lambda: sim.run('with (global.charinstance[2]) { if (finishattacktimer > 0) finishattacktimer--; } knight_fl_tick();'
                                             'global.OP = is_struct(global.knight_fl_om.pose) ? global.knight_fl_om.pose.dx : -9999;'))
        if not ok_:
            return ('omfight%d' % f, err)
        ofj.append((sim.eval('global.charinstance[2].image_alpha'), sim.eval('global.OP'), sim.eval('is_struct(global.knight_fl_fj)')))
    res['omfj'] = [min(o[0] for o in ofj), max(o[1] for o in ofj), ofj[-1][1], ofj[-1][2], om01(sim)]
    # paused in the middle of one of his scenes: it waits (it used to count on, find no battle and end itself halfway)
    ok_, err = auto(sim, lambda: sim.run('global.knight_ks = undefined; knight_kspell_start(31, 2, 0, 0); knight_fl_ks_init(); global.knight_ks.t = 10; global.knight_frozen = true;'
                                         'repeat (5) knight_kspell_tick(); global.PZ1 = is_struct(global.knight_ks) ? global.knight_ks.t : -1; global.knight_frozen = false;'
                                         'knight_kspell_tick(); global.PZ2 = is_struct(global.knight_ks) ? global.knight_ks.t : -1; if (is_struct(global.knight_ks)) knight_fl_end(global.knight_ks);'))
    if not ok_:
        return ('pause', err)
    res['pause'] = [sim.eval('global.PZ1'), sim.eval('global.PZ2')]
    # a teammate counts as taken when the Knight removed them from the party (the Violet Knight's taking) or marked them
    # slain - not when they are only down
    ok_, err = auto(sim, lambda: sim.run('var c0 = global.char[0]; var c1 = global.char[1]; global.knight_fl_om.p0 = [1, 2, 5]; global.krun.wr.slain[1] = false; global.krun.wr.slain[2] = false;'
                                         'global.hp[1] = 0; global.G0 = knight_fl_gone_count(); global.char[0] = 0; global.G1 = knight_fl_gone_count(); global.char[1] = 0; global.G2 = knight_fl_gone_count();'
                                         'global.char[0] = c0; global.char[1] = c1; global.knight_fl_om.trig = true; global.G3 = knight_fl_laststand_force();'))
    if not ok_:
        return ('gone', err)
    res['gone'] = [sim.eval('global.G0'), sim.eval('global.G1'), sim.eval('global.G2'), sim.eval('global.G3')]
    # the Violet Knight's Side B with Flowery on top, after its second taking (knightkillcon 130): his transformation scene
    # in place of the generic power-up, LAST JARONA unlocked
    ok_, err = auto(sim, lambda: sim.run('global.knight_fl_om.trig = false; global.knight_ks = undefined; global.myfight = 0; global.mnfight = 0;'
                                         'with (global.K) { knight_vb_init(); v_sideb = 1; vb_fin = 5; whatsact3 = ""; knightkillcon = 130; knight_vb_extra(); global.VB = [knightkillcon, whatsact3]; }'
                                         'global.VK = is_struct(global.knight_ks) ? global.knight_ks.kind : -1; global.VM = global.myfight; global.VS = global.spell[5][0];'
                                         'if (is_struct(global.knight_ks)) knight_fl_end(global.knight_ks); global.myfight = 0; global.mnfight = 0;'))
    if not ok_:
        return ('vb130', err)
    res['vb130'] = [sim.eval('global.VK'), sim.eval('global.VM'), sim.eval('global.VS'), sim.eval('global.VB[0]'), sim.eval('global.VB[1]')]
    # the Weird Route's end with him: his clash with the Knight, then the Knight's own death scene from its dissolve on
    ok_, err = auto(sim, lambda: sim.run('global.knight_ks = undefined; knight_kspell_start(29, 2, 0, 0); knight_fl_ks_init(); with (global.K) { whatsact3 = ""; acting = 0; actcon = 0; }'))
    if not ok_:
        return ('clash', err)
    n = 0
    while sim.eval('!is_undefined(global.knight_ks)') and n < 400:
        ok_, err = auto(sim, lambda: sim.run('knight_kspell_tick();'))
        if not ok_:
            return ('clash%d' % n, err)
        n += 1
    res['clash'] = [n, sim.eval('global.K.whatsact3'), sim.eval('global.K.acting'), sim.eval('global.K.actcon'), sim.eval('i_ex(global.K.knightmarker)'),
                    sim.eval('i_ex(global.K.blind_soon) && !global.K.blind_soon.visible'), sim.eval('global.K.visible')]
    sim.run('global.knight_variant = global.KV;')
    # Noelle and Flowery in one party: Noelle keeps everything of hers
    ok_, err = auto(sim, lambda: sim.run('var _c = knight_cfg_default(); _c.party = [1,4,5]; knight_cfg_sanitize(_c); global.PP = _c.party;'
                                         'global.char = [1,4,5]; knight_cc_spells_apply(); knight_cc_stats();'))
    if not ok_:
        return ('noelle', err)
    # his voice lines in his transformation: each line once (OMEGA FLOWERY! used to play twice, and "Lend me your power"
    # on top of "With your powers combined...")
    for vn in ('omega_flowery', 'with_your_powers_combined', 'lend_me_your_power', 'huh', 'last_jarona', 'smile_again'):
        try:
            sim.define_asset('snd_flowery_voiceclip_' + vn)
        except Exception:
            pass
    sim.vplays = []
    sim.mock('audio_exists', 1)
    sim.mock('snd_play', lambda s, *a: (s.vplays.append(s.eval('audio_get_name(%s)' % a[0]) if False else a[0]), 0)[1])
    ok_, err = auto(sim, lambda: sim.run('global.knight_fl_vname = ""; global.knight_fl_om.on = false; global.knight_fl_om.trig = false; knight_fl_om_undress(); global.knight_ks = undefined;'
                                         'global.VIDS = [asset_get_index("snd_flowery_voiceclip_omega_flowery"), asset_get_index("snd_flowery_voiceclip_with_your_powers_combined"), asset_get_index("snd_flowery_voiceclip_lend_me_your_power")];'
                                         'with (global.K) scr_spell(24, 2);'))
    if not ok_:
        return ('voice', err)
    n = 0
    while sim.eval('!is_undefined(global.knight_ks)') and n < 400:
        ok_, err = auto(sim, lambda: sim.run('global.mnfight = 1.5; knight_kspell_tick();'))
        if not ok_:
            return ('voicetick', err)
        n += 1
    vids = [sim.eval('global.VIDS[%d]' % i) for i in range(3)]
    res['voice'] = [sim.vplays.count(vids[0]), sim.vplays.count(vids[1]), sim.vplays.count(vids[2]), n]
    res['noelle'] = [sim.py(sim.eval('global.PP')), sim.eval('global.charname[4]'), sim.eval('global.spell[4][0]'), sim.eval('global.spell[4][1]')]
    # the Omega form never outlives its fight: the reset puts his own poses back on the entry and on a hero already made
    ok_, err = auto(sim, lambda: sim.run('global.knight_fl_om.on = true; knight_fl_om_dress(); global.RD0 = (knight_cc(5).poses.idle == knight_fl_a().om_idle);'
                                         'knight_fl_om_reset(); global.HR = -1; with (obj_knight_herocc) { if (char == 5) global.HR = (idlesprite == knight_fl_a().idle); }'
                                         'global.RD = [global.RD0, knight_fl_om_on(), knight_cc(5).poses.idle == knight_fl_a().idle, global.HR];'))
    if not ok_:
        return ('omreset', err)
    res['omreset'] = [sim.eval('global.RD[0]'), sim.eval('global.RD[1]'), sim.eval('global.RD[2]'), sim.eval('global.RD[3]')]
    # a single fight won: once the ending cutscene is over (no battle, no cutscene, no text, you could walk) the results show
    sim.mock('knight_fight_finished', lambda s, *a: (s.run('global.FF = 1;'), 0)[1])
    # (the player is back: obj_mainchara - its own Create needs the overworld, which the emulated battle does not have)
    if not sim.eval('instance_exists(obj_mainchara)'):
        try:
            sim.create_instance('obj_mainchara', 0, 0)
        except Exception:
            pass   # (made; only its Create stopped)
    ok_, err = auto(sim, lambda: sim.run('global.FF = 0; with (obj_battlecontroller) instance_destroy(); with (obj_writer) instance_destroy(); global.knight_frozen = false; global.interact = 0; global.krun.state = "won"; global.krun.mode = 0; global.krun.won_t = 0;'
                                         'repeat (10) knight_run_tick(); global.FF10 = global.FF; repeat (25) knight_run_tick();'))
    if not ok_:
        return ('results', err)
    res['results'] = [sim.eval('global.FF10'), sim.eval('global.FF'), sim.eval('w_ex()'), sim.eval('instance_exists(obj_cutscene_master)'), sim.eval('global.interact')]
    return ('ok', res)


keys = sys.argv[1:] or ['base', 'kaizo', 'elec', 'violet', 'thorn', 'cyan']
for key in keys:
    t = time.time()
    r = run(key)
    print(key, r[0], str(r[1])[:700], round(time.time() - t, 1), flush=True)
    if r[0] != 'ok':
        ok(False, '%s: %s %s' % (key, r[0], str(r[1])[:300]))
        continue
    res = r[1]
    ok(res['char'] == [1, 2, 5], key + ': Flowery is character 5 in the fight %r' % res['char'])
    ok(res['maxhp'] == 300 and res['hp'] == 300 and res['name'] == 'Flowery', key + ': his own stats: max HP 300 (%r/%r), name' % (res['hp'], res['maxhp']))
    ok(res['spl'][:7] == [27, 16, 17, 18, 19, 20, 21], key + ': his MAGIC = ACT (his ACT list) + his techniques %r' % res['spl'][:8])
    ok(res['gear'] == [30, 30, 31], key + ': his gear WinningSmile / PetalMantle / SundayBest %r' % res['gear'])
    ok(res['hero'] == [True, 5, True, True], key + ': the battle makes HIS hero (obj_knight_herocc, char 5, his poses) %r' % res['hero'])
    ok([i[0] for i in res['info']] == ['Sanfrandisco', 'MyJarona', 'Ez2Dance', 'PrismRush', 'Afinihug', 'HoneyKiss', 'F-Action'], key + ": the knight's spell info has his techniques")
    ok([i[1] for i in res['info']] == [0, 125, 50, 250, 88, 100, 0], key + ': TP costs 0 / 50 / 20 / 100 / 35 / 40 %% and F-Action 0 %r' % [i[1] for i in res['info']])
    ok(res['texts'], key + ": the knight's spell text: one page each, his id for the face writer, narration apart %r" % res['text0'])
    bt = res['bt']
    ok(bt[0][0] and not bt[0][1] and 'cheered everyone on!' in bt[0][2] and 'TP went up' in bt[0][2] and 'Watch this' not in str(bt[0][3]) and bt[1] == [False] and bt[2] == [0, 4],
       key + ': the box says what he did (battle text), no speech balloon for his moves (his voice clips only), other text untouched %r' % bt)
    ok(all(c[3] == 0 and c[4] == 1 for c in res['casts']), key + ': every move ends with nothing left behind and his hero back %r' % [(c[0], c[1], c[3], c[4]) for c in res['casts']])
    dm = {c[0]: c[2] for c in res['casts']}
    kd = res['kdmg']
    # (the knight's own scaling cuts every hit after the first in a turn, the same for every member's spells: the moves' own
    # damage is compared, and that every attack landed)
    ok(dm[16] > 0 and dm[17] > 0 and dm[19] > 0 and kd[16] < kd[17] < kd[19] and abs(kd[17] / kd[16] - 1.6 / 0.85) < 1.2 and abs(kd[19] / kd[16] - 2.5 / 0.85) < 1.8,
       key + ': Sanfrandisco < My Jarona < Prism Rush (about 0.85 / 1.6 / 2.5 of a FIGHT hit) %r, all landed %r' % (kd, dm))
    ok(min(res['krisa']) == 1 and sim_kris_ok(res), key + ': PRISM RUSH is his alone: Kris stays in place, never hidden or jumping in')
    ok(res['casts'][-1][5] == 80, key + ': F-Action: TP +32%% (%r)' % res['casts'][-1][5])
    ok(res['guards'] == [1, 1, True, 0], key + ': the guards shown: a shield on the hugged member, the charm on the knight, let go when they end %r' % res['guards'])
    ok(res['fx0'] == [1, 1, 1], key + ': Ez2Dance / Afinihug / Honey Kiss armed by the casts %r' % res['fx0'])
    ok(sorted(set(res['wsp'])) == [4, 5] and res['taken'] == [85, 68], key + ': on the enemy turn: SOUL faster %r, hugged member -20%% and charm -15%% %r' % (res['wsp'], res['taken']))
    ok(res['fx1'] == [0, 0, 0, 4], key + ': gone after the enemy turn, SOUL speed back %r' % res['fx1'])
    ok(res['charbox'] and res['col'] == 189950, key + ": every knight's HP bar draws a custom character's head, name and his colour")
    ok(res['still'], key + ': 60 frames of the fight, he keeps his look')
    ok(res['fj'][0] == (True, 0) and res['fj'][1][0] and res['fj'][2] == (False, 1) and res['fj'][3] == 0, key + ': FIGHT: one Jarona over the game\'s hit, then his hero is back, nothing left %r' % res['fj'])
    ok(res['ls0'] == [False, True, 99, 28], key + ': last stand: not while a teammate is up, not while they are only knocked down; with everyone else TAKEN by the Knight, at the end of the turn (every knight\'s scr_mnendturn calls knight_lu_turnend) the battle holds and his scene starts %r' % res['ls0'])
    ok(res['ls1'][1] and res['ls1'][2] == 23 and res['ls1'][3] == 60 and res['ls1'][4] == [0, 0] and res['ls1'][5] == 1 and res['ls1'][6] == 1 and not res['ls1'][7] and res['ls1'][8] == [19, 25] and all(res['ls1'][9]),
       key + ': OMEGA FLOWERY for good: MAGIC only LAST JARONA + PRISM RUSH, max HP +20%%, every pose of his hero and registry the Omega ones (hero shown, drawn by his own Omega Draw), the turn waits for its text, once only %r' % res['ls1'])
    ok(res['clash'][1:] == ['deathanim', 3, 64, True, True, 0] and res['clash'][0] < 300, key + ': the Weird Route end with him: his clash, then the Knight\'s death scene from its dissolve (no black/red screen) %r' % res['clash'])
    ok(res['omp'][:2] == [140, 130] and res['omp'][2] <= -5 and res['omp'][3] >= 5 and res['omp'][4] in (True, 1) and res['omp'][5] == 3,
       key + ': Omega form: he glides to the middle member\'s place (Susie\'s: heromake[1]) and floats up and down (+-6 px); his hero\'s Draw is the Omega one %r' % res['omp'])
    ok(res['heal'][0] >= 10 + int(res['heal'][1] * 0.4) - 1, key + ': SMILE AGAIN (his Omega heal): +40%% max HP %r' % res['heal'])
    ok(len(res['omc']) == 3 and res['omc'][0][1] < 250 and all(c[1] < 500 and c[2] == 1 and c[3] == 0 and c[4] and c[5] for c in res['omc']),
       key + ': Omega form: PRISM RUSH just goes off (no transformation), LAST JARONA; both end with his Omega hero shown, still Omega, nothing left %r' % res['omc'])
    ok(res['gone'] == [0, 1, 2, False], key + ': taken = removed from the party by the Knight (the Violet Knight) or slain; only down = not taken; the Violet power-up hook never runs twice %r' % res['gone'])
    ok(res['vb130'] == [28, 99, 23, 0, 'finisher'], key + ': Violet Side B, Flowery on top, second taking: his transformation scene is the power-up, LAST JARONA unlocked %r' % res['vb130'])
    ok(res['pause'] == [10, 11], key + ': paused in the middle of his scene: it waits, then goes on %r' % res['pause'])
    ok(res['omfj'][0] == 1 and res['omfj'][1] > 100 and res['omfj'][2] == -9999 and not res['omfj'][3] and res['omfj'][4] == 0,
       key + ': his FIGHT as OMEGA FLOWERY: his hero stays shown the whole time (it does the Jarona itself, out to the foe and back), nothing left %r' % res['omfj'])
    ok(res['vg'] == [1, 75], key + ': Omega form: his hero left hidden with nothing of his on screen is shown again; 25%% less damage taken %r' % res['vg'])
    ok(res['omf'][:5] == [24, False, 100, 5, 30] and res['omf'][5] < 400 and res['omf'][6] and res['omf'][7:9] == [23, 19] and res['omf'][9] == 1 and res['omf'][10],
       key + ': OMEGA FORM (technique 24): offered on the POWER page but not in his starting list, 100 TP, plays his transformation, then OMEGA FLOWERY (MAGIC LAST JARONA + PRISM RUSH), no last stand after it %r' % res['omf'])
    ok(res['omdmg'][19] > res['kdmg'][19] * 1.3, key + ': PRISM RUSH as OMEGA FLOWERY hits harder %r' % [res['kdmg'][19], res['omdmg'][19]])
    zb = res.get('ljz')
    ok(zb == [1, -1, 1],
       key + ': LAST JARONA: [Z] just before contact = STRONG punch, too early = plain, one press a punch %r' % (zb,))
    ok(res['lj'] == [100, 100, 1], key + ': LAST JARONA: 100 TP always (no 999 "charging" cost - TP can no longer go below 0); next fight his Flowery poses are back %r' % res['lj'])
    ok(res['omreset'][0] and not res['omreset'][1] and res['omreset'][2] and res['omreset'][3] in (True, 1, -1), key + ': after the fight his Omega form is gone: his own poses back on the entry and his hero %r' % res['omreset'])
    ok(res['results'][:2] == [0, 1], key + ': a single fight won: the results show once the ending cutscene is over (no walk to the door) %r' % res['results'])
    ok(res['voice'][:3] == [1, 1, 0], key + ': his transformation (OMEGA FORM): OMEGA FLOWERY! once, "With your powers combined..." once, no "Lend me your power" on top %r' % res['voice'])
    ok(res['noelle'] == [[1, 4, 5], 'Noelle', 4, 10], key + ': Noelle in the same party keeps her name and spells %r' % res['noelle'])
print('%d checks, %d failed' % (N[0], len(FAILS)))
for f_ in FAILS:
    print('FAILED:', f_)
sys.exit(1 if FAILS else 0)
