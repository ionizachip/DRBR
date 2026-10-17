"""BUILD 50: the hub's own Weird Route takings are OFF for every knight (only the Violet Knight's own Side B takes members).
Was: Weird Route on the knights without a Side B (Normal, Supercharged, Thorn, Cyan), build 38: halfway through the attack list the
Knight takes the BOTTOM member at the end of an enemy turn (real merged scr_mnendturn hook; the member on top is never taken), the
others talk in their own speech bubbles (Susie first, then party order), learn their moves, the lost member stays down (no healing),
the Knight hits 25% harder, and the battle resumes. With one member left (solo at halfway, two-member parties at about 3/4) the Knight
charges and the member knocks the blade back. INFINITE HP does not stop the story. Real merged GML in the emulator."""
import sys, os, time
def allmsg(s):
    n = s.eval('variable_global_exists("msgno") ? global.msgno : 0')
    return ''.join(str(s.eval('global.msg[%d]' % i)) for i in range(int(n) + 1))
from emu_atk import *
import emu_atk
FAILS = []; N = [0]
def ok(c, msg):
    N[0] += 1
    if not c: FAILS.append(msg); print('FAIL', msg, flush=True)
def eq(a, b, msg):
    N[0] += 1
    if a != b: FAILS.append(msg); print('FAIL', msg, 'got', repr(a), 'want', repr(b), flush=True)

OBJ = {1: 'obj_herokris', 2: 'obj_herosusie', 3: 'obj_heroralsei', 4: 'obj_heronoelle'}

def setup(key, party, weird=1, practice=0, infhp=0):
    sim = mk(key, list(party))
    for _m in ('scr_84_get_sprite', 'scr_84_get_font', 'scr_battletext_default', 'scr_speaker', 'scr_spellmenu_setup', 'snd_play_x', 'mus_volume', 'scr_spellget'):
        sim.mock(_m, 0)
    sim.texts = []
    sim.mock('scr_battletext', lambda s, *a: (s.texts.append(allmsg(s)), 0)[1])
    sim.calls = []
    for _m in ('scr_enemyblcon',):
        sim.mock(_m, (lambda n: (lambda s, *a: (s.calls.append((n,) + tuple(a) + (s.eval('global.msg[0]'), s.eval('global.typer'))), 0)[1]))(_m))
    sim.run('for (var _i = array_length(global.flag); _i < 10000; _i++) global.flag[_i] = 0;')
    sim._snapauto = True
    sim.run('global.charinstance = [noone, noone, noone];')
    made = {}
    for i, c in enumerate(party):
        if c in OBJ:
            if c not in made:
                auto(sim, lambda: sim.run('global.HI = instance_create(100 + %d * 10, 100 + %d * 40, %s);' % (i, i, OBJ[c])))
                made[c] = sim.eval('global.HI')
            sim.run('global.charinstance[%d] = %d; with (%d) { myself = %d; myheight = 60; }' % (i, made[c], made[c], i))
    IDL = {1: 'spr_krisb_idle', 2: 'spr_susieb_idle', 3: 'spr_ralsei_idle', 4: 'spr_noelleb_idle'}
    for c in made:
        sim.run('with (%s) idlesprite = %s;' % (OBJ[c], IDL[c]))
    for i in (1, 2, 3, 4):
        sim.run('global.hp[%d]=140; global.maxhp[%d]=140;' % (i, i))
    sim.run('global.char=[%d,%d,%d];' % tuple((list(party) + [0, 0, 0])[:3]))
    sim.run('global.monster=[1,0,0];global.monsterattackname=["","",""];global.monstername=["","",""];global.monstergold=[0,0,0,0];global.monsterexp=[0,0,0,0];'
            'global.monsterdef=[0,0,0];global.monsterinstance=[0,0,0];global.monsterhp=[7300,0,0];global.monstermaxhp=[7300,0,0];global.monsterat=[10,0,0];'
            'global.monsterdf=[0,0,0];global.monstertype=[0,0,0];global.monsterstatus=[0,0,0];global.charcantarget=[1,1,1];global.targeted=[0,0,0,0,0];'
            'global.charaction=[0,0,0];global.acting=[0,0,0,0,0];global.faceaction=[0,0,0];global.charmove=[1,1,1];global.chardead=[0,0,0];global.charauto=[0,0,0,0,0];'
            'global.mnfight=0;global.inv=-1;global.invc=1;global.turntimer=0;global.TT_f=0;global.TT_end=-1;global.TT_active=0;global.bmenuno=0;global.myfight=0;'
            'global.fighting=1;global.msc=0;global.typer=5;global.batmusic=[0,0];global.battlemsg=[""];global.hittarget=[0,0,0];global.actingsingle=[0,0,0,0];'
            'global.actingsimul=[0,0,0,0];global.actingtarget=[0,0,0,0];global.temptension=[0,0,0];global.charspecial=[0,0,0];global.tension=0;')
    for nm in ['canact', 'actname', 'actdesc', 'actcost', 'actsimul', 'actactor']:
        for sfx in ['', 'sus', 'ral', 'noe']:
            z = '""' if nm in ('actname', 'actdesc') else '0'
            sim.run('global.%s%s = [[%s],[%s],[%s]];' % (nm, sfx, ','.join([z] * 6), ','.join([z] * 6), ','.join([z] * 6)))
    sim.run('global.canactsus[0][0] = 1; global.canactral[0][0] = 1; global.canactnoe[0][0] = 1; global.battleactcount = [0,0,0];')
    good, err = auto(sim, lambda: sim.run('with(obj_battlecontroller) instance_destroy(); instance_create(0,0,obj_battlecontroller); global.K=instance_create(300,100,obj_knight_enemy); '
                                         'global.K.myself=0; global.monsterinstance[0]=global.K; global.K.hb_key = "%s";' % key))
    assert good, err
    sim.run('global.knight_run = 1; var _c = knight_cfg_default(); _c.weird = %d; _c.practice = %d; _c.infhp = %d; _c.party = [%d,%d,%d];'
            'global.krun = knight_run_new({src: _c, cfg: _c, plan: [knight_find_key("%s")], reveal: ""}); global.krun.party = [%d,%d,%d]; global.krun.practice = %s; '
            'global.krun.state = "battle"; knight_ch_begin(global.krun); global.flag[456] = %d;'
            % ((weird, practice, infhp) + tuple((list(party) + [0, 0, 0])[:3]) + (key,) + tuple((list(party) + [0, 0, 0])[:3]) + ('true' if practice else 'false', weird)))
    return sim

def scene(sim, frames=900):
    """run the hub tick + battle step until the weird-route scene is over"""
    for f in range(frames):
        good, err = auto(sim, lambda: sim.run('if (!instance_exists(obj_knight_ctrl)) instance_create(0, 0, obj_knight_ctrl); with (obj_knight_ctrl) knight_run_tick();'))
        if not good:
            return 'tick%d %s' % (f, err)
        good, err = auto(sim, lambda: sim.step(1))
        if not good:
            return 'step%d %s' % (f, err)
        if sim.eval('global.krun.wr.st') == 9:
            return None
    return 'timeout st=%s' % sim.eval('global.krun.wr.st')

def end_turn(sim):
    """the real end of an enemy turn (scr_mnendturn) once the fight is halfway"""
    sim.run('global.krun.eturns = global.krun.wr.at; global.mnfight = 2; global.myfight = 0;')
    good, err = auto(sim, lambda: sim.run('with (global.K) scr_mnendturn();'))
    return good, err

t0 = time.time()
# build 50: with WEIRD ROUTE on, at halfway (and at 3/4) through the attack list, no knight takes anyone: no scene, nobody lost
for key, party in [('thorn', [1, 2, 3]), ('thorn', [2, 3, 4]), ('elec', [1, 2, 3]), ('cyan', [1, 2, 3]), ('base', [1, 2, 3]),
                   ('thorn', [1, 2, 0]), ('thorn', [2, 0, 0]), ('kaizo', [1, 2, 3]), ('violet', [1, 2, 3])]:
    sim = setup(key, party)
    eq(sim.eval('global.krun.wr.on'), False, '%s %s: the hub Weird Route takings are off' % (key, party))
    good, err = end_turn(sim)
    ok(good, '%s %s: the end of the turn runs (%s)' % (key, party, err))
    eq(sim.eval('global.krun.wr.st'), 0, '%s %s: no taking scene at halfway' % (key, party))
    sim.run('global.krun.eturns = global.krun.wr.at2; global.mnfight = 2; global.myfight = 0;')
    auto(sim, lambda: sim.run('with (global.K) scr_mnendturn();'))
    eq(sim.eval('global.krun.wr.st'), 0, '%s %s: none at 3/4 either' % (key, party))
    eq([sim.eval('global.myfight'), sim.eval('global.mnfight')], [0, 0], '%s %s: the battle is not held' % (key, party))
    hp = [sim.eval('global.hp[%d]' % c) for c in party if c]
    ok(min(hp) > 0, '%s %s: nobody is lost %r' % (key, party, hp))
print('wr50 tests', N[0], 'fails', len(FAILS), '%.0fs' % (time.time() - t0)); sys.exit(1 if FAILS else 0)
