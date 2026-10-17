"""Kaizo Knight Side B without Kris (build 37): Susie gets a RudeBuster S-Action (25% TP) in place of Kris's X-Slash ACT, it makes
her cast her Rude Buster, and the mod's own HoldBreath S-Action still works. Real merged Kaizo code in the emulator."""
import sys, time
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

def setup(party, sideb=1):
    sim = mk('kaizo', party)
    for _m in ['scr_84_get_sprite', 'scr_84_get_font', 'scr_battletext', 'scr_battletext_default', 'scr_speaker', 'scr_damage_enemy', 'scr_endcombat', 'scr_nextact', 'scr_attackphase', 'scr_enemyblcon', 'scr_spellmenu_setup']:
        sim.mock(_m, 0)
    sim._snapauto = True
    sim.run('global.charinstance = [noone, noone, noone];')
    for i, c in enumerate(party):
        if c in OBJ:
            auto(sim, lambda: sim.run('global.HI = instance_create(100, 100 + %d * 40, %s); global.HI.myself = %d; global.charinstance[%d] = global.HI;' % (i, OBJ[c], i, i)))
    sim.run('global.flag[456]=%d; global.char=[%d,%d,%d];' % (sideb, *party))
    for i in (1, 2, 3, 4):
        sim.run('global.hp[%d]=140; global.maxhp[%d]=140;' % (i, i))
    sim.run('global.monster=[1,0,0];global.monsterattackname=["","",""];global.monstername=["","",""];global.monstergold=[0,0,0,0];global.monsterexp=[0,0,0,0];'
            'global.monsterdef=[0,0,0];global.monsterinstance=[0,0,0];global.monsterhp=[10000,0,0];global.monstermaxhp=[10000,0,0];global.monsterat=[10,0,0];'
            'global.monsterdf=[0,0,0];global.monstertype=[104,0,0];global.monsterstatus=[0,0,0];global.charcantarget=[1,1,1];global.targeted=[0,0,0,0,0];'
            'global.charaction=[0,0,0];global.charspecial=[0,0,0];global.chartarget=[0,0,0];global.acting=[0,0,0,0,0];global.faceaction=[0,0,0];global.charmove=[0,0,0];'
            'global.mnfight=0;global.inv=0;global.invc=1;global.turntimer=0;global.TT_f=0;global.TT_end=-1;global.TT_active=0;global.bmenuno=0;global.myfight=0;'
            'global.fighting=1;global.msc=0;global.typer=5;global.battleactcount=[0,0,0];global.batmusic=[0,0];global.actingsingle=[0,0,0,0];global.currentactingchar=0;'
            'global.charauto=[0,0,0,0,0];global.chardead=[0,0,0];')
    for nm in ['canact', 'actname', 'actdesc', 'actcost', 'actsimul', 'actactor']:
        for sfx in ['', 'sus', 'ral', 'noe']:
            z = '""' if nm in ('actname', 'actdesc') else '0'
            sim.run('global.%s%s = [[%s]];' % (nm, sfx, ','.join([z] * 6)) + 'for (var _m = 1; _m < 3; _m++) global.%s%s[_m] = [%s];' % (nm, sfx, ','.join([z] * 6)))
    good, err = auto(sim, lambda: sim.run('with(obj_battlecontroller) instance_destroy(); instance_create(0,0,obj_battlecontroller); '
                                         'global.K=instance_create(300,100,obj_knight_enemy); global.K.myself=0; global.monsterinstance[0]=global.K; myself = 0;'))
    assert good, err
    good, err = auto(sim, lambda: sim.run('with (global.K) scr_monstersetup();'))
    ok(good, 'monster setup runs (%s)' % err)
    return sim

t0 = time.time()
sim = setup([2, 3, 4])
eq(sim.eval('global.K.k_sideb'), 1, 'Kaizo Side B on without Kris')
for f in range(3):
    good, err = auto(sim, lambda: sim.step(1))
    ok(good, 'step %d runs (%s)' % (f, err))
eq(sim.eval('global.K.kz_rb'), 1, 'Susie gets a RudeBuster S-Action (index 2)')
eq((sim.eval('global.actnamesus[0][1]'), sim.eval('global.actcostsus[0][1]')), ('RudeBuster', 62.5), 'RudeBuster at 25% TP, like X-Slash')
eq(sim.eval('global.actnamesus[0][0]'), 'HoldBreath', "the mod's own HoldBreath S-Action stays first")
sim.run('global.myfight=3; global.K.actingsus=2; global.K.actconsus=1; global.K.actcon=0; global.charaction=[9,0,0];')
good, err = auto(sim, lambda: sim.step(1))
ok(good, 'RudeBuster runs (%s)' % err)
eq((sim.eval('global.charaction[0]'), sim.eval('global.charspecial[0]')), (2, 4), 'RudeBuster makes Susie cast her Rude Buster (spell 4)')
eq(sim.eval('global.K.holdbreathcount'), 0, "the mod's HoldBreath handler did not also run")
# with Kris: no RudeBuster, the X-Slash ACT as the mod has it
sim = setup([1, 2, 3])
for f in range(3):
    auto(sim, lambda: sim.step(1))
eq(sim.eval('global.K.kz_rb'), -1, 'with Kris: no extra S-Action')
eq(sim.eval('global.actname[0][2]'), 'X-Slash', 'with Kris: the X-Slash ACT')
# no Susie: nothing extra
sim = setup([3, 4, 0])
for f in range(3):
    auto(sim, lambda: sim.step(1))
eq(sim.eval('global.K.kz_rb'), -1, 'no Susie: no RudeBuster')
print('kz37 tests', N[0], 'fails', len(FAILS), '%.0fs' % (time.time() - t0)); sys.exit(1 if FAILS else 0)
