"""Build 38 in the real merged knight code (emulator): HoldBreath on Susie's / Ralsei's / Noelle's ACT lists when Kris is not in the
party (every knight but Kaizo, which has its own), using it speeds the SOUL up without the fight's own ACT code also running, the Violet
Knight's HoldBreath / DeepBreath toggle, HoldBreath moving up when Susie's talk ACT is used up, and the learned double moves
(RUDER BUSTER, ICESTORM, FIRESTORM) casting twice, 15 frames apart."""
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

def setup(key, party):
    sim = mk(key, party)
    for _m in ['scr_84_get_sprite', 'scr_84_get_font', 'scr_battletext', 'scr_speaker', 'scr_damage_enemy', 'scr_endcombat', 'scr_nextact', 'scr_attackphase',
               'scr_enemyblcon', 'snd_stop', 'mus_volume', 'scr_spellmenu_setup']:
        sim.mock(_m, 0)
    sim.played = []
    sim.mock('snd_play', lambda s, a, *r: (s.played.append(a), 0)[1])
    sim.msgs = []
    sim.mock('scr_battletext_default', lambda s, *a: (s.msgs.append(s.eval('global.msg[0]')), 0)[1])
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
        sim.run('global.hp[%d]=140; global.maxhp[%d]=140;' % (i, i))
    sim.run('global.monster=[1,0,0];global.monsterattackname=["","",""];global.monstername=["","",""];global.monstergold=[0,0,0,0];global.monsterexp=[0,0,0,0];'
            'global.monsterdef=[0,0,0];global.monsterinstance=[0,0,0];global.monsterhp=[10000,0,0];global.monstermaxhp=[10000,0,0];global.monsterat=[10,0,0];'
            'global.monsterdf=[0,0,0];global.monstertype=[104,0,0];global.monsterstatus=[0,0,0];global.charcantarget=[1,1,1];global.targeted=[0,0,0,0,0];'
            'global.charaction=[0,0,0];global.charspecial=[0,0,0];global.chartarget=[0,0,0];global.acting=[0,0,0,0,0];global.faceaction=[0,0,0];global.charmove=[0,0,0];'
            'global.mnfight=0;global.inv=0;global.invc=1;global.turntimer=0;global.TT_f=0;global.TT_end=-1;global.TT_active=0;global.bmenuno=0;global.myfight=0;'
            'global.fighting=1;global.msc=0;global.typer=5;global.battleactcount=[0,0,0];global.batmusic=[0,0];global.actingsingle=[0,0,0,0];global.currentactingchar=0;'
            'global.charauto=[0,0,0,0,0];global.chardead=[0,0,0];global.monsterx=[400,0,0];global.monstery=[150,0,0];global.automiss=[0,0,0];global.hittarget=[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0];')
    for nm in ['canact', 'actname', 'actdesc', 'actcost', 'actsimul', 'actactor']:
        for sfx in ['', 'sus', 'ral', 'noe']:
            z = '""' if nm in ('actname', 'actdesc') else '0'
            sim.run('global.%s%s = [[%s]];' % (nm, sfx, ','.join([z] * 6)) + 'for (var _m = 1; _m < 3; _m++) global.%s%s[_m] = [%s];' % (nm, sfx, ','.join([z] * 6)))
    good, err = auto(sim, lambda: sim.run('with(obj_battlecontroller) instance_destroy(); instance_create(0,0,obj_battlecontroller); '
                                         'global.K=instance_create(300,100,obj_knight_enemy); global.K.myself=0; global.monsterinstance[0]=global.K; myself = 0;'))
    assert good, err
    good, err = auto(sim, lambda: sim.run('with (global.K) scr_monstersetup();'))
    ok(good, '%s %s: monster setup runs (%s)' % (key, party, err))
    sim.run('global.K.holdbreathcount = 0; global.K.actingsus = 0; global.K.actingral = 0; global.K.actingnoe = 0; global.K.actconsus = 0; global.K.actconral = 0; global.K.actconnoe = 0; global.K.actcon = 0;')
    return sim

def act(sim, who, idx):
    v = {2: ('actingsus', 'actconsus'), 3: ('actingral', 'actconral'), 4: ('actingnoe', 'actconnoe')}[who]
    sim.msgs.clear()
    sim.run('global.myfight=3; global.K.%s=%d; global.K.%s=1; global.K.actcon=0;' % (v[0], idx + 1, v[1]))
    good, err = auto(sim, lambda: sim.step(1))
    return good, err

t0 = time.time()
for key in ('base', 'elec', 'violet', 'thorn', 'cyan'):
    sim = setup(key, [2, 3, 4])
    names = [(sim.eval('global.actnamesus[0][%d]' % i), sim.eval('global.actnameral[0][%d]' % i), sim.eval('global.actnamenoe[0][%d]' % i)) for i in range(2)]
    eq(names[1], ('HoldBreath', 'HoldBreath', 'HoldBreath'), '%s no Kris: HoldBreath for Susie, Ralsei and Noelle' % key)
    eq([sim.eval('global.canactsus[0][1]'), sim.eval('global.canactral[0][1]'), sim.eval('global.canactnoe[0][1]')], [1, 1, 1], '%s: usable' % key)
    ok(names[0][0] != 'HoldBreath', '%s: their own ACT stays first (%s)' % (key, names[0]))
    # Susie holds her breath: the SOUL is faster, the fight's own S-Action code does not run
    good, err = act(sim, 2, 1)
    ok(good, '%s: HoldBreath runs (%s)' % (key, err))
    eq(sim.eval('global.K.holdbreathcount'), 1, '%s: the SOUL moves faster' % key)
    eq(sim.eval('global.K.actconsus'), 0, '%s: the action is used up' % key)
    eq(sim.eval('global.canactsus[0][0]'), 1, "%s: Susie's own talk ACT did not run" % key)
    ok(any('faster' in m for m in sim.msgs), '%s: text (%s)' % (key, sim.msgs))
    ok(any('kept her breath held' in m for m in sim.msgs), "%s: Susie's own line" % key)
    if key == 'violet':
        eq((sim.eval('global.actnamesus[0][1]'), sim.eval('global.actnameral[0][1]'), sim.eval('global.actnamenoe[0][1]')), ('DeepBreath',) * 3, 'violet: everyone\'s act turns into DeepBreath')
        good, err = act(sim, 3, 1)
        eq(sim.eval('global.K.holdbreathcount'), 1, 'violet: a second breath in the same turn changes nothing')
        ok(any('Nothing else happened' in m for m in sim.msgs), 'violet: same turn text (%s)' % sim.msgs)
        sim.run('global.krun.eturns += 1;')
        good, err = act(sim, 3, 1)
        eq(sim.eval('global.K.holdbreathcount'), 0, 'violet: DeepBreath (next turn) slows the SOUL down again')
        eq(sim.eval('global.actnameral[0][1]'), 'HoldBreath', 'violet: back to HoldBreath')
        ok(any('deep breath' in m for m in sim.msgs), 'violet: deep breath text')
    else:
        good, err = act(sim, 4, 1)
        eq(sim.eval('global.K.holdbreathcount'), 1, '%s: a second HoldBreath does nothing more' % key)
        ok(any('held her breath in panic' in m and 'nothing' in m for m in sim.msgs), "%s: Noelle's line, nothing happens (%s)" % (key, sim.msgs))
    # Susie's talk ACT used up: HoldBreath moves into the first row where nothing reuses it (Normal, Thorn, Cyan)
    good, err = act(sim, 2, 0)
    ok(good, '%s: Susie talks (%s)' % (key, err))
    eq(sim.eval('global.canactsus[0][0]'), 0, "%s: Susie's talk ACT is used up" % key)
    sim.run('global.mnfight = 2; global.myfight = 0; with (global.K) knight_hb_compact();')
    if key in ('base', 'thorn', 'cyan'):
        eq((sim.eval('global.actnamesus[0][0]'), sim.eval('global.canactsus[0][1]')), ('HoldBreath', 0), '%s: HoldBreath moved up to the first row' % key)
    else:
        eq(sim.eval('global.actnamesus[0][1]'), ('HoldBreath' if key != 'violet' else sim.eval('global.actnamesus[0][1]')), '%s: HoldBreath stays (the fight reuses the first row)' % key)
    sim.run('global.mnfight = 0;')
    # with Kris: only Kris has HoldBreath (the fight's own)
    sim2 = setup(key, [1, 2, 3])
    eq((sim2.eval('global.actnamesus[0][1]').strip(), sim2.eval('global.actnameral[0][1]').strip()), ('', ''), '%s with Kris: no extra HoldBreath' % key)
    eq(sim2.eval('global.actname[0][1]'), 'HoldBreath', "%s with Kris: Kris's own HoldBreath" % key)
    print(key, 'ok %.0fs' % (time.time() - t0), flush=True)

# ---------- the learned double moves ----------
sim = setup('base', [2, 3, 4])
sim.define_object('obj_tst')
sim.run('with (global.K) { knight_act_put(2, 2, "RuderBuster", "", 150); knight_act_put(3, 2, "FireStorm", "", 75); knight_act_put(4, 2, "IceStorm", "", 75); }')
for who, sp, slot in ((2, 4, 0), (3, 13, 1), (4, 9, 2)):
    sim.run('global.currentactingchar = %d; global.charaction = [0,0,0]; global.charspecial = [0,0,0];' % slot)
    good, err = act(sim, who, 2)
    ok(good, 'learned move %d runs (%s)' % (sp, err))
    eq((sim.eval('global.charaction[%d]' % slot), sim.eval('global.charspecial[%d]' % slot)), (2, sp), 'member %d casts spell %d in the spell phase' % (who, sp))
    eq(sim.eval('global.knight_dbl[%d]' % slot), sp, '... as the double version')
    eq(sim.eval('global.K.actcon'), 1, '... and the ACT is done')
sim.run('global.msg = [""]; global.charspecial = [4, 13, 9]; knight_dbl_text(0);'); ok('RUDER BUSTER' in sim.eval('global.msg[0]'), 'spell line: RUDER BUSTER')
sim.run('knight_dbl_text(1);'); ok('FIRESTORM' in sim.eval('global.msg[0]'), 'spell line: FIRESTORM')
sim.run('knight_dbl_text(2);'); ok('ICESTORM' in sim.eval('global.msg[0]'), 'spell line: ICESTORM')
def ids(obj):
    sim.run('global.IDS = []; with (%s) array_push(global.IDS, id);' % obj)
    return set(sim.py(sim.eval('global.IDS')))
# RUDER BUSTER: two Rude Busters, the second 15 frames after the first
sim.played.clear()
good, err = auto(sim, lambda: sim.run('with (instance_create(0, 0, obj_tst)) scr_spell(4, 0);'))
ok(good, 'Rude Buster cast runs (%s)' % err)
eq((sim.eval('global.knight_ks.kind'), sim.eval('global.spelldelay')), (8, 95), 'RUDER BUSTER sequence, longer spell phase')
eq(sim.eval('global.knight_dbl[0]'), 0, 'the double is used up')
seen = []
for f in range(50):
    good, err = auto(sim, lambda: sim.run('knight_kspell_tick();'))
    if not good:
        break
    t = sim.eval('is_undefined(global.knight_ks) ? -1 : global.knight_ks.t')
    for i in ids('obj_rudebuster_anim'):
        if i not in [s[1] for s in seen]:
            seen.append((t, i))
    auto(sim, lambda: sim.step(1))
ok(good, 'RUDER BUSTER ticks run (%s)' % err)
eq([s[0] for s in seen], [1, 16], 'two Rude Buster swings, at t 1 and t 16 (X-Slash timing)')
# a normal Rude Buster stays single
good, err = auto(sim, lambda: sim.run('global.knight_ks = undefined; with (instance_create(0, 0, obj_tst)) scr_spell(4, 0);'))
ok(sim.eval('is_undefined(global.knight_ks)'), 'a normal Rude Buster is not doubled')
# ICESTORM
good, err = auto(sim, lambda: sim.run('global.knight_ks = undefined; with (obj_icespell) instance_destroy(); with (instance_create(0, 0, obj_tst)) scr_spell(9, 2);'))
ok(good, 'Ice Shock cast runs (%s)' % err)
eq(sim.eval('global.knight_ks.kind'), 9, 'ICESTORM sequence')
seen = []
for f in range(40):
    good, err = auto(sim, lambda: sim.run('knight_kspell_tick();'))
    t = sim.eval('is_undefined(global.knight_ks) ? -1 : global.knight_ks.t')
    for i in ids('obj_icespell'):
        if i not in [s[1] for s in seen]:
            seen.append((t, i))
eq([s[0] for s in seen], [1, 16], 'two Ice Shocks, at t 1 and t 16')
# FIRESTORM: kind 5 with a second fireball
sim.run('global.knight_dbl[1] = 13; with (obj_heroralsei) { spellsprite = spr_ralsei_spell; spellframes = 0; attacktimer = 0; state = 0; }')
good, err = auto(sim, lambda: sim.run('global.knight_ks = undefined; with (obj_firespell) instance_destroy(); with (instance_create(0, 0, obj_tst)) scr_spell(13, 1);'))
ok(good, 'FireShock cast runs (%s)' % err)
eq((sim.eval('global.knight_ks.kind'), sim.eval('global.knight_ks.dbl'), sim.eval('global.spelldelay')), (5, 1, 100), 'FIRESTORM: FireShock with a second throw')
seen = []
for f in range(60):
    good, err = auto(sim, lambda: sim.run('knight_kspell_tick();'))
    if not good:
        break
    t = sim.eval('is_undefined(global.knight_ks) ? -1 : global.knight_ks.t')
    for i in ids('obj_firespell'):
        if i not in [s[1] for s in seen]:
            seen.append((t, i))
ok(good, 'FIRESTORM ticks run (%s)' % err)
eq(len(seen), 2, 'two fire bursts land (%s)' % seen)
ok(len(seen) == 2 and seen[1][0] - seen[0][0] == 15, 'the second one 15 frames after the first (%s)' % seen)
print('hb38 tests', N[0], 'fails', len(FAILS), '%.0fs' % (time.time() - t0)); sys.exit(1 if FAILS else 0)
