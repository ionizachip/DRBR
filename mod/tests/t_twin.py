"""Battle rules in the emulated knight battle (real merged GML): Twin Knight appears, picks a pattern each knight turn, fires
bullets that wait harmless then go live, hit through the game's own scr_damage, and leave at the end of the turn; the
Darkness overlay draws with the SOUL inside it; Hyper speed asks for 38 fps only in battle. Usage: t_twin.py [key ...]"""
import sys, os, time
os.environ.setdefault('WALL', '200')
from emu_atk import *
import emu_atk
FAILS = []; N = [0]
def ok(c, msg):
    N[0] += 1
    if not c: FAILS.append(msg); print('FAIL', msg, flush=True)

def run(key, party=(1, 2, 3), frames=160, phase=1, turn=1):
    sim = mk(key, list(party))
    sim.define_object('obj_knight_twin_bullet', parent='obj_regularbullet')
    for _m in ('scr_84_get_sprite', 'scr_84_get_font'):
        sim.mock(_m, 0)
    sim.run('for (var _i = array_length(global.flag); _i < 10000; _i++) global.flag[_i] = 0;')
    for c in party:
        if c in (1, 2, 3):
            o = ('obj_herokris', 'obj_herosusie', 'obj_heroralsei')[c - 1]
            sim._snapauto = True
            auto(sim, lambda: sim.run('with(%s) instance_destroy(); instance_create(100,100,%s);' % (o, o)))
    sim.run('global.hp[1]=140;global.hp[2]=140;global.hp[3]=140;global.hp[4]=140;global.maxhp[1]=140;global.maxhp[2]=140;global.maxhp[3]=140;global.maxhp[4]=140;')
    sim.run('global.monster=[1,0,0];global.monsterattackname=["","",""];global.monstername=["","",""];global.monstergold=[0,0,0,0];global.monsterexp=[0,0,0,0];global.monsterdef=[0,0,0];global.monsterinstance=[0,0,0];global.monsterhp=[7300,0,0];global.monstermaxhp=[7300,0,0];global.monsterat=[10,0,0];global.monsterdf=[0,0,0];global.monstertype=[0,0,0];global.monsterstatus=[0,0,0];global.charcantarget=[1,1,1];global.targeted=[0,0,0,0,0];global.charaction=[0,0,0];global.acting=[0,0,0,0,0];global.faceaction=[0,0,0];global.charmove=[0,0,0];global.mnfight=1.5;global.inv=-1;global.invc=1;global.turntimer=0;global.TT_f=0;global.TT_end=-1;global.TT_active=0;global.bmenuno=0;global.myfight=0;global.fighting=0;global.msc=0;global.typer=5;')
    sim._snapauto = True
    ok_, err = auto(sim, lambda: sim.run('with(obj_battlecontroller) instance_destroy(); instance_create(0,0,obj_battlecontroller); with(obj_knight_enemy) instance_destroy(); with(obj_heart) instance_destroy(); global.K=instance_create(300,100,obj_knight_enemy); global.K.myself=0; global.monsterinstance[0]=global.K; instance_create(300,300,obj_heart);'))
    if not ok_:
        return ('create', err)
    # a hub run with the battle rules on
    sim.run('global.knight_run = 1; var _c = knight_cfg_default(); _c.c_twin = 1; _c.c_dark = 1; _c.c_speed = 1; _c.c_thorns = 1; _c.c_time = 1; _c.party = [%d,%d,%d];'
            'global.krun = knight_run_new({src: _c, cfg: _c, plan: [knight_find_key("%s")], reveal: ""}); global.krun.party = [%d,%d,%d]; global.krun.state = "battle"; knight_ch_begin(global.krun);'
            % (tuple((list(party) + [0, 0, 0])[:3]) + (key,) + tuple((list(party) + [0, 0, 0])[:3])))
    sim.run('global.K.phase=%d; global.K.phaseturn=%d; global.K.turn=%d; global.mnfight=1.5; global.K.attackchosen=false; global.K.talked=1; global.K.rtimer=0;' % (phase, turn - 1, turn))
    seen = {'objs': set(), 'tb': 0, 'twin': 0, 'bul': 0, 'live': 0, 'hit': 0, 'pats': set(), 'maxb': 0, 'after_end': -1, 'speed': set(), 'dark': 0}
    t0 = time.time()
    for f in range(frames):
        if f % 3 == 0:
            sim.run('global.hp[1]=max(global.hp[1],60);global.hp[2]=max(global.hp[2],60);global.hp[3]=max(global.hp[3],60);')
        ok_, err = auto(sim, lambda: sim.run('knight_run_tick();'))
        if not ok_:
            return ('tick%d' % f, err)
        ok_, err = auto(sim, lambda: sim.step(1))
        if not ok_:
            if sim.eval('global.TT_end') >= 0 and 'object index 1463' in err:
                break
            return ('step%d' % f, err)
        ok_, err = auto(sim, lambda: sim.run('knight_hud_draw();'))
        if not ok_:
            return ('draw%d' % f, err)
        nt = sim.eval('instance_number(obj_knight_twin)')
        nb = sim.eval('(function(){ var _n = 0; with (obj_bulletparent) if (variable_instance_exists(id, "kbrx") && kbrx > 0) _n++; return _n; })()')
        seen['tb'] += sim.eval('instance_number(obj_knight_twin_bullet)')
        if nb:
            for _nm in sim.py(sim.eval('(function(){ var _r = []; with (obj_bulletparent) if (variable_instance_exists(id, "kbrx") && kbrx > 0) array_push(_r, object_get_name(object_index)); return _r; })()')):
                seen['objs'].add(_nm)
        seen['twin'] = max(seen['twin'], nt)
        seen['bul'] += nb
        seen['maxb'] = max(seen['maxb'], nb)
        if nt:
            seen['pats'].add(sim.eval('instance_find(obj_knight_twin, 0).pat'))
        live = sim.eval('(function(){ var _n = 0; with (obj_collidebullet) if (variable_instance_exists(id, "kbrx") && kbrx > 0 && active == 1) _n++; return _n; })()')
        seen['live'] = max(seen['live'], live)
        if live and seen['hit'] == 0:
            hp0 = sim.eval('global.hp[1] + global.hp[2] + global.hp[3]')
            sim.run('with (obj_herokris) myheight = 60; with (obj_herosusie) myheight = 60; with (obj_heroralsei) myheight = 60;')
            sim.run('global.charinstance = [instance_find(obj_herokris, 0), instance_find(obj_herosusie, 0), instance_find(obj_heroralsei, 0)]; global.battledf = [0, 0, 0]; global.chardead = [0, 0, 0]; global.charcantarget = [1, 1, 1]; global.itemelement = []; global.itemelementamount = []; for (var _q = 0; _q < 5; _q++) { global.itemelement[_q] = [0, 0, 0]; global.itemelementamount[_q] = [0, 0, 0]; }')
            okh, errh = auto(sim, lambda: sim.run('global.inv = -1; with (obj_collidebullet) { if (variable_instance_exists(id, "kbrx") && kbrx > 0 && active == 1) { event_user(5); break; } }'))
            if not okh:
                return ('hit', errh)
            hp1 = sim.eval('global.hp[1] + global.hp[2] + global.hp[3]')
            seen['hit'] = hp0 - hp1
        seen['speed'].add(sim.eval('knight_speed_want(global.krun)'))
        if sim.eval('global.krun.dark_a') > 0.5:
            seen['dark'] += 1
        if sim.eval('global.TT_end') >= 0 and seen['after_end'] < 0:
            seen['after_end'] = f
        if seen['after_end'] >= 0 and f > seen['after_end'] + 3:
            break
        if time.time() - t0 > float(os.environ.get('WALL', '200')):
            break
    # end the knight turn: the twin's bullets must leave on their own (turntimer < 1)
    sim.run('global.turntimer = 0;')
    ok_, err = auto(sim, lambda: sim.run('global.mnfight = 1.5; with (obj_knight_twin) knight_twin_step();'))
    if not ok_:
        return ('end', err)
    nb_end = sim.eval('(function(){ var _n = 0; with (obj_bulletparent) if (variable_instance_exists(id, "kbrx") && kbrx > 0) _n++; return _n; })()')
    # every pattern fires from a fresh twin (no knight attack needed)
    sim.run('global.turntimer = 300; global.mnfight = 2;')
    for p in range(4):
        okp, errp = auto(sim, lambda: sim.run('with (obj_bulletparent) if (variable_instance_exists(id, "kbrx")) instance_destroy(); with (obj_knight_twin) { pat = %d; turnno = 6; active = true; for (t = 31; t < 140; t++) { knight_twin_fire(); knight_twin_tel_step(); } }' % p))
        if not okp:
            return ('pattern%d' % p, errp)
        seen['pats'].add((p, sim.eval('(function(){ var _n = 0; with (obj_bulletparent) if (variable_instance_exists(id, "kbrx") && kbrx > 0) _n++; return _n; })()')))
    # stars must burst into starchildren, swords must fly: one pattern's objects followed for 200 frames
    seen['life'] = {}
    for p in range(4):
        okp, errp = auto(sim, lambda: sim.run('with (obj_bulletparent) if (variable_instance_exists(id, "kbrx")) instance_destroy(); with (obj_knight_twin) { pat = %d; turnno = 6; active = true; t = 31; knight_twin_fire(); t = -100000; }' % p))
        if not okp:
            return ('life%d' % p, errp)
        names = set()
        for f in range(200):
            sim.run('global.turntimer = 300; global.mnfight = 2;')
            okp, errp = auto(sim, lambda: sim.step(1))
            if not okp:
                return ('life%d step%d' % (p, f), errp)
            for _nm in sim.py(sim.eval('(function(){ var _r = []; with (obj_bulletparent) if (variable_instance_exists(id, "kbrx") && kbrx > 0) array_push(_r, object_get_name(object_index)); return _r; })()')):
                names.add(_nm)
        seen['life'][p] = sorted(names)
    return ('ok', seen, nb_end, sim.eval('global.krun.eturns'), sim.eval('global.krun.tlimit'))

keys = sys.argv[1:] or ['base', 'kaizo', 'thorn']
for key in keys:
    t = time.time()
    r = run(key)
    print(key, r[0], r[1:] if r[0] == 'ok' else str(r[1])[:400], round(time.time() - t, 1), flush=True)
    if r[0] != 'ok':
        ok(False, '%s: %s' % (key, r[0])); continue
    seen, nb_end, et, tl = r[1], r[2], r[3], r[4]
    ok(seen['twin'] == 1, key + ': exactly one twin')
    ok(seen['bul'] > 0, key + ': the twin attacks with the Knight\'s real objects ' + repr(sorted(seen['objs'])))
    ok(seen['tb'] == 0, key + ': no old twin bullets (%d)' % seen['tb'])
    ok(seen['live'] > 0, key + ': its objects go live')
    ok(seen['hit'] > 0, key + ': a live twin object damages the party through scr_damage')
    ok(seen['maxb'] <= 40, key + ': bullet count stays sane (%d)' % seen['maxb'])
    ok(nb_end == 0, key + ': no twin bullets left after the turn (%d)' % nb_end)
    for p in range(4):
        cnt = [c for (q, c) in [x for x in seen['pats'] if isinstance(x, tuple)] if q == p]
        ok(cnt and 2 <= cnt[0] <= 40, key + ': pattern %d fires a sane number of bullets %s' % (p, cnt))
    L = seen['life']
    ok('obj_knight_pointing_starchild' in L.get(0, []), key + ': star rain bursts into starchildren %r' % L.get(0))
    ok('obj_knight_pointing_starchild' in L.get(2, []), key + ': star burst bursts into starchildren %r' % L.get(2))
    ok('obj_tracking_sword1' in L.get(1, []), key + ': side swords are the tracking sword %r' % L.get(1))
    ok('obj_fallingsword__v1' in L.get(3, []), key + ': falling swords %r' % L.get(3))
    ok(et >= 1, key + ': the knight turn was counted')
    ok(tl > 0, key + ': a turn limit is set')
    ok(38 in seen['speed'], key + ': hyper speed asks for 38 fps in battle')
    ok(seen['dark'] > 0, key + ': darkness shows during the knight turn')
print('twin tests', N[0], 'fails', len(FAILS)); sys.exit(1 if FAILS else 0)
