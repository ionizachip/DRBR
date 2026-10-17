"""Build 41 lineup harness: a real knight battle in the emulator (merged fight code, the stub battle controller from emu_atk,
heroes as in t_hb38) with the hub's lineup (Tag Team / Attack Remix) driving it. Used by t_lineup.py."""
import sys, os, re, time, glob
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from emu_atk import *

KEYI = {'base': 0, 'kaizo': 1, 'elec': 2, 'violet': 3, 'thorn': 4, 'cyan': 5}
OBJ = {1: 'obj_herokris', 2: 'obj_herosusie', 3: 'obj_heroralsei', 4: 'obj_heronoelle'}


def lu_battle(host, party=(1, 2, 3), combo=1, partner='thorn', hp=140, extra_cfg='', world=False, pre=None):
    """world=True: the battle room's own objects are there too, made under the host's variant as in the real game (the arena
    cutscene obj_ch3_PTB02 waiting for the battle to end, the sign, the dark world controller, the tension bar), so a partner's
    code that reads them meets the host's instances (build 41 crash: obj_ch3_PTB02.nokaizo)."""
    sim = mk(host, list(party))
    sim.autolog = []
    if pre is not None:
        pre(sim)
    if world:
        sim.run('global.knight_variant=%d;' % KEYI[host])
    for _m in ['scr_84_get_sprite', 'scr_84_get_font', 'scr_battletext', 'scr_speaker', 'scr_endcombat', 'scr_nextact', 'scr_attackphase',
               'scr_enemyblcon', 'snd_stop', 'mus_volume', 'scr_spellmenu_setup']:
        sim.mock(_m, 0)
    sim.played = []
    sim.mock('snd_play', lambda s, a, *r: (s.played.append(a), 0)[1])
    for ev in ('Draw_0',):
        sim.load_file(M + 'gml_Object_obj_knight_enemy_%s.gml' % ev, entry='gml_Object_obj_knight_enemy_%s' % ev)
    for ev in ('Create_0', 'Draw_0'):
        sim.load_file(M + 'gml_Object_obj_knight_bench_%s.gml' % ev, entry='gml_Object_obj_knight_bench_%s' % ev)
    sim._snapauto = True
    sim.run('global.charinstance = [noone, noone, noone]; for (var _i = array_length(global.flag); _i < 10000; _i++) global.flag[_i] = 0;')
    sim.run('global.battlemag = [6, 6, 6]; global.battleat = [12, 12, 12]; global.battledf = [2, 2, 2]; global.chapter = 3;')
    made = {}
    for i, c in enumerate(party):
        if c in OBJ:
            if c not in made:
                auto(sim, lambda: sim.run('global.HI = instance_create(100, 100 + %d * 40, %s);' % (i, OBJ[c])))
                made[c] = sim.eval('global.HI')
            sim.run('global.charinstance[%d] = %d; with (%d) { if (!variable_instance_exists(id, "myself")) myself = %d; myheight = 60; }' % (i, made[c], made[c], i))
    sim.run('global.flag[456]=0; global.char=[%d,%d,%d];' % tuple((list(party) + [0, 0, 0])[:3]))
    for i in (1, 2, 3, 4):
        sim.run('global.hp[%d]=%d; global.maxhp[%d]=%d;' % (i, hp, i, hp))
    sim.run('global.monster=[1,0,0];global.monsterattackname=["","",""];global.monstername=["","",""];global.monstergold=[0,0,0,0];global.monsterexp=[0,0,0,0];'
            'global.monsterdef=[0,0,0];global.monsterinstance=[0,0,0];global.monsterhp=[10000,0,0];global.monstermaxhp=[10000,0,0];global.monsterat=[10,0,0];'
            'global.monsterdf=[0,0,0];global.monstertype=[104,0,0];global.monsterstatus=[0,0,0];global.charcantarget=[(global.char[0]!=0)?1:0,(global.char[1]!=0)?1:0,(global.char[2]!=0)?1:0];global.targeted=[0,0,0,0,0];'
            'global.charaction=[0,0,0];global.charspecial=[0,0,0];global.chartarget=[0,0,0];global.acting=[0,0,0,0,0];global.faceaction=[0,0,0];global.charmove=[0,0,0];'
            'global.mnfight=0;global.inv=0;global.invc=1;global.turntimer=0;global.TT_f=0;global.TT_end=-1;global.TT_active=0;global.bmenuno=0;global.myfight=0;'
            'global.fighting=1;global.msc=0;global.typer=5;global.battleactcount=[0,0,0];global.batmusic=[0,0];global.actingsingle=[0,0,0,0];global.currentactingchar=0;'
            'global.charauto=[0,0,0,0,0];global.chardead=[0,0,0];global.monsterx=[400,0,0];global.monstery=[150,0,0];global.automiss=[0,0,0];'
            'global.hittarget=[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0];global.monstermakex=[300,0,0];global.monstermakey=[100,0,0];global.sparepoint=[0,0,0];'
            'global.mercymod=[0,0,0];global.mercymax=[100,100,100];global.battlemsg=["* start"];global.charname=["", "Kris", "Susie", "Ralsei", "Noelle"];')
    for nm in ['canact', 'actname', 'actdesc', 'actcost', 'actsimul', 'actactor']:
        for sfx in ['', 'sus', 'ral', 'noe']:
            z = '""' if nm in ('actname', 'actdesc') else '0'
            sim.run('global.%s%s = [[%s]];' % (nm, sfx, ','.join([z] * 6)) + 'for (var _m = 1; _m < 3; _m++) global.%s%s[_m] = [%s];' % (nm, sfx, ','.join([z] * 6)))
    sim.run('global.knight_variant=%d; global.knight_variant_pending=%d;' % (KEYI[host], KEYI[host]))
    sim.run('var _c = knight_cfg_default(); _c.party = [%d, %d, %d]; _c.knight = %d; _c.knight2 = %d; _c.combo = %d; %s'
            'global.knight_cfg = _c; global.knight_run = 1; global.krun = knight_run_new({ src: _c, cfg: _c, plan: [%d], reveal: "", corr: [] });'
            'global.krun.state = "battle"; knight_lu_new(global.krun);'
            % (party[0], party[1] if len(party) > 1 else 0, party[2] if len(party) > 2 else 0, KEYI[host], KEYI.get(partner, 0), combo, extra_cfg, KEYI[host]))
    if world:
        # the arena cutscene made the battle and waits in con 6 for its end; the sign, the dark world controller and the tension
        # bar of the room - all made under the host's variant
        good, err = auto(sim, lambda: sim.run('global.CM = instance_create(0, 0, obj_cutscene_master); global.CM.actor_id = []; global.CM.actor_name = [];'))
        if not good:
            return sim, ('world obj_cutscene_master', err)
        # the overworld party (base-game objects, the same for every fight): made with their own Create as in the room
        for _ln in open('/home/claude/work/idx/merged.tsv'):
            _p = _ln.rstrip('\n').split('\t')
            if len(_p) >= 3 and _p[0] == 'room':
                sim.define_asset(_p[2])
        sim.run('global.facing = 0;')
        good, err = auto(sim, lambda: sim.run('global.MC = instance_create(300, 200, obj_mainchara); global.cinstance = [];'))
        if not good:
            return sim, ('world obj_mainchara', err)
        _k = 0
        for _c in party:
            if _c in (2, 3, 4):
                good, err = auto(sim, lambda: sim.run('var _cc = instance_create(280, 200, obj_caterpillarchara); _cc.name = "%s"; global.cinstance[%d] = _cc;' % ({2: 'susie', 3: 'ralsei', 4: 'noelle'}[_c], _k)))
                if not good:
                    return sim, ('world caterpillar', err)
                _k += 1
        good, err = auto(sim, lambda: sim.run('global.P = instance_create(0, 0, obj_ch3_PTB02);'))
        if not good:
            return sim, ('world obj_ch3_PTB02', err)
        sim.run('global.P.con = 6;')
        for o in ('obj_npc_sign', 'obj_darkcontroller', 'obj_tensionbar'):
            good, err = auto(sim, lambda: sim.run('instance_create(0, 0, %s);' % o))
            if not good:
                return sim, ('world ' + o, err)
    good, err = auto(sim, lambda: sim.run('with(obj_battlecontroller) instance_destroy(); instance_create(0,0,obj_battlecontroller); obj_battlecontroller.intro = 1;'
                                         'if (!instance_exists(obj_knight_ctrl)) instance_create_depth(0,0,-99000,obj_knight_ctrl);'
                                         'global.K=instance_create(300,100,obj_knight_enemy); global.K.myself=0; global.monsterinstance[0]=global.K; myself = 0;'))
    if not good:
        return sim, ('create', err)
    good, err = auto(sim, lambda: sim.run('with (global.K) event_user(12);'))
    if not good:
        return sim, ('setup', err)
    return sim, None


def frames(sim, n, stop=None):
    for f in range(n):
        good, err = auto(sim, lambda: sim.step(1))
        if not good:
            return ('step', err)
        if stop and stop():
            return ('stop', f)
    return None


def end_turn_now(sim):
    """what the battle controller does when the bullets are over (bullets, box and SOUL gone) - used to cut long attacks short"""
    sim.run('with (obj_bulletparent) instance_destroy(); with (obj_bulletgenparent) instance_destroy(); with (obj_dbulletcontroller) instance_destroy();'
            'with (obj_growtangle) instance_destroy(); with (obj_heart) instance_destroy(); global.TT_end = 1; global.mnfight = 0;')


def enemy_turn(sim, maxf=1500, keep_hp=True, bullet_frames=45):
    """one enemy turn of the knight that is fighting: talk skipped, the attack chosen by the knight's own Step at mnfight 1.5
    (Other_10), bullets until the stub battle controller ends the turn; then what the real battle controller does at the end of a
    turn (alarm 2 -> scr_mnendturn: monster reset + the lineup hook). Returns None or (where, error)."""
    sim.run('global.TT_end=-1; global.mnfight=1.5; global.myfight=0; with (obj_knight_enemy) { talked = 1; attackchosen = false; rtimer = 0; attacked = 0; }')
    t0 = time.time()
    for f in range(maxf):
        good, err = auto(sim, lambda: sim.step(1))
        if not good:
            if sim.eval('global.TT_end') >= 0 and 'object index 1463' in err:
                break
            return ('step%d' % f, err)
        if sim.eval('global.TT_end') >= 0:
            break
        if bullet_frames and f >= bullet_frames:
            good, err = auto(sim, lambda: end_turn_now(sim))
            if not good:
                return ('cut', err)
            break
        if keep_hp and f % 3 == 0:
            sim.run('for (var _i = 1; _i <= 4; _i++) global.hp[_i] = max(global.hp[_i], 60);')
        if time.time() - t0 > float(os.environ.get('WALL', '240')):
            return ('wall', f)
    good, err = auto(sim, lambda: sim.run('with (obj_growtangle) instance_destroy(); with (obj_heart) instance_destroy(); global.mnfight = 0; global.myfight = 0;'
                                         'with (obj_monsterparent) { attacked = 0; talked = 0; acting = 0; } knight_lu_turnend();'))
    if not good:
        return ('turnend', err)
    return None
