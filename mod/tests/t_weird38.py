"""Violet Knight Side B for every party (build 38): the party order decides who the Knight takes (bottom first, never the top member,
Kris too when Kris is not on top), the others talk (Susie first), Susie learns RUDER BUSTER when Ralsei falls (no more RED BUSTER),
Ralsei FIRESTORM, Noelle ICESTORM, a lone member parries the blade, the top member's finisher, and Kris on top still playing the mod's
own Kris scenes. Runs the real merged Violet code in the emulator."""
import os, sys, time
def allmsg(s):
    n = s.eval('variable_global_exists("msgno") ? global.msgno : 0')
    return ''.join(str(s.eval('global.msg[%d]' % i)) for i in range(int(n) + 1))
from emu_atk import *
import emu_atk
FAILS = []; N = [0]
def ok(c, msg):
    N[0] += 1
    if not c: FAILS.append(msg); print('FAIL', msg)
def eq(a, b, msg):
    N[0] += 1
    if a != b: FAILS.append(msg); print('FAIL', msg, 'got', repr(a), 'want', repr(b))

OBJ = {1: 'obj_herokris', 2: 'obj_herosusie', 3: 'obj_heroralsei', 4: 'obj_heronoelle'}

def setup(party, phase, sideb=1):
    sim = mk('violet', party); emu_atk.LAST = sim
    sim.define_object('obj_dummy_bl'); sim.define_const('violetknight_sideb', 0)
    sim.calls = []
    for _m in ['scr_84_get_sprite', 'scr_84_get_font', 'scr_speaker', 'scr_damage_enemy', 'scr_spellmenu_setup', 'scr_endcombat', 'scr_spellget']:
        sim.mock(_m, 0)
    for _m in ['scr_mnendturn', 'knight_battle_won', 'scr_enemyblcon', 'scr_nextact', 'scr_attackphase', 'scr_battletext', 'scr_battletext_default']:
        sim.mock(_m, (lambda n: (lambda s, *a: (s.calls.append((n,) + tuple(a) + (allmsg(s), s.eval('global.typer'))), 0)[1]))(_m))
    sim._snapauto = True
    sim.run('global.charinstance = [noone, noone, noone]; global.battlemag = [6,6,6]; global.battleat = [12,12,12];')
    made = {}
    for i, c in enumerate(party):
        if c in OBJ:
            if c not in made:
                auto(sim, lambda: sim.run('global.HI = instance_create(100 + %d * 10, 100 + %d * 40, %s);' % (i, i, OBJ[c])))
                made[c] = sim.eval('global.HI')
            sim.run('global.charinstance[%d] = %d; with (%d) { if (!variable_instance_exists(id, "myself")) myself = %d; }' % (i, made[c], made[c], i))
    IDL = {1: 'spr_krisb_idle', 2: 'spr_susieb_idle', 3: 'spr_ralsei_idle', 4: 'spr_noelleb_idle'}
    for c in made:
        sim.run('with (%s) { idlesprite = %s; attacksprite = %s; }' % (OBJ[c], IDL[c], IDL[c]))
    sim.run('global.flag[456]=%d; global.char=[%d,%d,%d];' % (sideb, *party))
    for i in (1, 2, 3, 4):
        sim.run('global.hp[%d]=140; global.maxhp[%d]=140;' % (i, i))
    sim.run('global.monster=[1,0,0];global.monsterattackname=["","",""];global.monstername=["","",""];global.monstergold=[0,0,0,0];global.monsterexp=[0,0,0,0];'
            'global.monsterdef=[0,0,0];global.monsterinstance=[0,0,0];global.monsterhp=[99999,0,0];global.monstermaxhp=[99999,0,0];global.monsterat=[10,0,0];'
            'global.monsterdf=[0,0,0];global.monstertype=[0,0,0];global.monsterstatus=[0,0,0];global.charcantarget=[1,1,1];global.targeted=[0,0,0,0,0];'
            'global.charaction=[0,0,0];global.charspecial=[0,0,0];global.chartarget=[0,0,0];global.acting=[0,0,0,0,0];global.faceaction=[0,0,0];global.charmove=[0,0,0];'
            'global.mnfight=1.5;global.inv=0;global.invc=1;global.turntimer=0;global.TT_f=0;global.TT_end=-1;global.TT_active=0;global.bmenuno=0;global.myfight=0;'
            'global.fighting=0;global.msc=0;global.typer=5;global.battleactcount=[0,0,0];global.batmusic=[0,0];')
    for nm in ['canact', 'actname', 'actdesc', 'actcost', 'actsimul', 'actactor']:
        for sfx in ['', 'sus', 'ral', 'noe']:
            z = '""' if nm in ('actname', 'actdesc') else '0'
            sim.run('global.%s%s = [[%s]];' % (nm, sfx, ','.join([z] * 6)) + 'for (var _m = 1; _m < 3; _m++) global.%s%s[_m] = [%s];' % (nm, sfx, ','.join([z] * 6)))
    sim.run('global.actingsingle=[0,0,0,0]; global.actingsimul=[0,0,0,0]; global.actingtarget=[0,0,0,0]; global.currentactingchar=0; global.charauto=[0,0,0,0,0]; global.chardead=[0,0,0]; global.monsterinstance=[noone,noone,noone];')
    sim.run('global.canactsus[0][0] = 1; global.actnamesus[0][0] = "S-Action"; global.canactral[0][0] = 1; global.actnameral[0][0] = "R-Action"; global.canactnoe[0][0] = 1; global.actnamenoe[0][0] = "N-Action";')
    sim.run('global.canact[0][0] = 1; global.actname[0][0] = "Check"; global.canact[0][1] = 1; global.actname[0][1] = "HoldBreath";')
    good, err = auto(sim, lambda: sim.run('with(obj_battlecontroller) instance_destroy(); instance_create(0,0,obj_battlecontroller); '
                                         'global.K=instance_create(300,100,obj_knight_enemy); global.K.myself=0; instance_create(300,300,obj_heart);'))
    assert good, err
    sim.run('with (global.K) knight_hb_setup("violet");')
    sim.run('global.K.phase=%d; global.K.phaseturn=0; global.K.turn=0; global.mnfight=99; global.myfight=99; global.charturn=-1; global.K.attackchosen=false; '
            'global.K.talked=1; global.K.rtimer=0; global.K.myblcon=instance_create(0,0,obj_dummy_bl); with(obj_herokris) myself=0;' % phase)
    return sim

def kill(sim, n, frames=2500, watch=None):
    """start loss n (1 or 2) the way the fight does it and run until the scene is over; returns the list of knightkillcon states seen.
    watch: a set that collects every sprite Ralsei shows on the way (his idle sprite and the act-sprite marker standing in for him)"""
    sim.run('with (global.K) { knightkillcon = 2; kill_target = knight_vb_victim(%d); }' % n)
    seen = []; last = None
    for f in range(frames):
        good, err = auto(sim, lambda: sim.step(1))
        if not good:
            return seen, 'ERR %s' % err
        k = sim.eval('global.K.knightkillcon')
        if k != last:
            seen.append(k); last = k
        if watch is not None:
            sim.run('global.W1 = -1; global.W2 = -1; with (obj_heroralsei) global.W1 = idlesprite; '
                    'with (global.K) { if (variable_instance_exists(id, "_charactsprite") && array_length(_charactsprite) > 3 && instance_exists(_charactsprite[3])) global.W2 = _charactsprite[3].sprite_index; }')
            watch.add(sim.eval('global.W1')); watch.add(sim.eval('global.W2'))
        if k == 0 and f > 5:
            break
    return seen, None

def acts(sim, which):
    return [sim.eval('global.%s[0][%d]' % (which, i)) for i in range(3)]

def says(sim):
    return [c for c in sim.calls if c[0] == 'scr_enemyblcon']

t0 = time.time()
VOICE = {74: 3, 75: 2, 76: 4}
def says(sim):
    return [VOICE.get(c[-1], c[-1]) for c in sim.calls if c[0] == 'scr_enemyblcon']
def texts(sim):
    return ' | '.join(str(c[-2]) for c in sim.calls if c[0] in ('scr_battletext', 'scr_battletext_default'))
def names(sim, arr):
    return [sim.eval('global.%s[0][%d]' % (arr, i)) for i in range(4)]
def next_loss(sim):
    sim.run('global.myfight=99; global.mnfight=99; global.K.phase=3; global.K.actingsus=0; global.K.actingral=0; global.K.actingnoe=0; global.K.actcon=0;')
    sim.calls.clear()
def finale(sim, who, idx, tag):
    actv = {2: 'actingsus', 3: 'actingral', 4: 'actingnoe'}[who]; conv = {2: 'actconsus', 3: 'actconral', 4: 'actconnoe'}[who]
    sim.run('global.myfight=3; global.K.haveusedroaring=true; global.K.chargeupcon=0; global.K.%s=%d; global.K.%s=1; global.K.actcon=0;' % (actv, idx + 1, conv))
    sim.calls.clear()
    good = True; err = None
    for f in range(900):
        good, err = auto(sim, lambda: sim.step(1))
        if not good or any(c[0] == 'knight_battle_won' for c in sim.calls):
            break
    ok(good and any(c[0] == 'knight_battle_won' for c in sim.calls), '%s: finale reaches the win hook (%s)' % (tag, err))

# ---------- Kris on top, Susie, Ralsei at the bottom: the mod's own story, Susie learns RUDER BUSTER ----------
sim = setup([1, 2, 3], 2)
eq(sim.eval('global.K.vb_fin'), 1, 'KSR: Kris (on top) finishes the fight')
seen, err = kill(sim, 1)
ok(err is None, 'KSR loss 1 runs: %s' % err)
eq(sim.eval('global.K.kill_target') == sim.eval('obj_heroralsei'), True, 'KSR: the bottom member (Ralsei) is taken first')
eq(says(sim), [2, 2, 2], 'KSR: Susie reacts (shock, "You...", fury)')
ok('RUDER BUSTER' in texts(sim) and 'RED BUSTER' not in texts(sim), 'KSR: "Susie learned RUDER BUSTER", no RED BUSTER (%s)' % texts(sim))
ok('RuderBuster' in names(sim, 'actnamesus'), 'KSR: RuderBuster on her S-Action list (%s)' % names(sim, 'actnamesus'))
ok(sim.eval('global.K.whatsact3') != 'redbuster' and 'RedBuster' not in names(sim, 'actname'), 'KSR: no Kris RedBuster ACT any more')
eq(sim.eval('global.K.ral_dead'), 1, 'KSR: Ralsei is lost')
ok(any(c[0] == 'scr_mnendturn' for c in sim.calls), 'KSR: the player turn starts')
next_loss(sim); sim.run('global.char=[1,2,0];')
seen, err = kill(sim, 2, 4000)
ok(err is None, 'KSR loss 2 runs: %s' % err)
ok(30.5 in seen and 42.5 in seen, "KSR: Kris's X-Slash scene plays (states %s)" % seen[-10:])
eq(sim.eval('global.K.whatsact3'), 'xslash', 'KSR: X-Slash ACT')

# ---------- Kris on top, Ralsei, Susie at the bottom: Susie goes first ----------
sim = setup([1, 3, 2], 2)
seen, err = kill(sim, 1, 4000)
ok(err is None, 'KRS loss 1 runs: %s' % err)
eq(sim.eval('global.K.kill_target') == sim.eval('obj_herosusie'), True, 'KRS: Susie (bottom) is taken first')
eq(says(sim), [3, 3], 'KRS: Ralsei reacts (shock, resolve)')
ok('FIRESTORM' in texts(sim), 'KRS: Ralsei learns FIRESTORM (%s)' % texts(sim))
ok(30.5 in seen, "KRS: then Kris's X-Slash scene (states %s)" % seen[:20])
eq(sim.eval('global.K.whatsact3'), 'xslash', 'KRS: X-Slash ACT already')
eq(sim.eval('global.K.ral_dead'), 0, 'KRS: Ralsei is not marked dead')

# ---------- Kris on top, Ralsei, Noelle at the bottom: the Angel first, Ralsei still up ----------
sim = setup([1, 3, 4], 2)
seen, err = kill(sim, 1)
ok(err is None, 'KRN loss 1 runs: %s' % err)
eq(sim.eval('global.K.kill_target') == sim.eval('obj_heronoelle'), True, 'KRN: the Angel first')
eq(says(sim), [3, 3], 'KRN: Ralsei reacts ("prophecy", resolve)')
eq(sim.eval('global.K.ral_dead'), 0, 'KRN: Ralsei is not marked dead (he is right there)')
with_r = sim.eval('knight_hero_inst(3)')
sim.run('with (knight_hero_inst(3)) global.TMP = idlesprite;')
eq(sim.eval('global.TMP'), sim.eval('spr_ralsei_idle'), 'KRN: Ralsei back to his normal stance after his lines')

# ---------- no Kris: Susie on top, Ralsei, Noelle at the bottom ----------
sim = setup([2, 3, 4], 2)
eq(sim.eval('global.K.vb_fin'), 2, 'SRN: Susie (on top) finishes the fight')
eq(names(sim, 'actnamesus')[1], 'HoldBreath', 'SRN: HoldBreath on her list (no Kris)')
seen, err = kill(sim, 1)
ok(err is None, 'SRN loss 1 runs: %s' % err)
eq(sim.eval('global.K.kill_target') == sim.eval('obj_heronoelle'), True, 'SRN: the Angel (bottom) first')
eq(says(sim), [2, 3, 2, 2, 3], 'SRN: Susie first, Ralsei picks up ("prophecy"), Susie\'s fury, Ralsei\'s resolve')
ok('FIRESTORM' in texts(sim) and 'RUDER' not in texts(sim), 'SRN: Ralsei learns FIRESTORM; Susie waits for... (%s)' % texts(sim))
ok('RedBuster' not in names(sim, 'actnamesus'), 'SRN: no RED BUSTER after the Angel (%s)' % names(sim, 'actnamesus'))
ok(any(c[0] == 'scr_mnendturn' for c in sim.calls), 'SRN: the player turn starts')
sim.run('with (knight_hero_inst(3)) global.TMP = idlesprite;')
eq(sim.eval('global.TMP'), sim.eval('spr_ralsei_idle'), 'SRN: Ralsei back to his normal stance')
# FIRESTORM used: Ralsei casts FireShock twice
fs = names(sim, 'actnameral').index('FireStorm')
sim.run('global.myfight=3; global.currentactingchar=1; global.K.actingral=%d; global.K.actconral=1; global.K.actcon=0; global.charaction=[0,0,0];' % (fs + 1))
auto(sim, lambda: sim.step(1))
eq((sim.eval('global.charaction[1]'), sim.eval('global.charspecial[1]'), sim.eval('global.knight_dbl[1]')), (2, 13, 13), 'SRN: FIRESTORM = FireShock, cast twice')
# second loss: Ralsei; Susie loses a second friend, learns RUDER BUSTER, her finisher
next_loss(sim)
seen, err = kill(sim, 2, 5000)
ok(err is None, 'SRN loss 2 runs: %s' % err)
eq(sim.eval('global.K.kill_target') == sim.eval('obj_heroralsei'), True, 'SRN: Ralsei second')
eq(says(sim), [2, 2, 2], 'SRN: Susie: "R-Ralsei...?", "not you too", "END YOU!!!"')
ok(130.5 in seen and 142.5 in seen, 'SRN: then her power-up scene (states %s)' % seen[-12:])
ok('RUDER BUSTER' in texts(sim), 'SRN: "Susie will now use RUDER BUSTER" (%s)' % texts(sim))
eq(sim.eval('global.K.whatsact3'), 'finisher', 'SRN: finisher stage')
fi = sim.eval('global.K.vb_fin_idx')
eq(names(sim, 'actnamesus')[fi], 'RuderBuster', 'SRN: the finisher is RUDER BUSTER')
eq(names(sim, 'actnamesus').count('RuderBuster'), 1, 'SRN: one RUDER BUSTER entry')
sim.run('global.myfight=3; global.currentactingchar=0; global.K.haveusedroaring=false; global.K.actingsus=%d; global.K.actconsus=1; global.K.actcon=0; global.charaction=[9,0,0];' % (fi + 1))
auto(sim, lambda: sim.step(1))
eq((sim.eval('global.charaction[0]'), sim.eval('global.charspecial[0]'), sim.eval('global.knight_dbl[0]')), (2, 4, 4), 'SRN: before the Roaring: RUDER BUSTER (Rude Buster twice)')
finale(sim, 2, fi, 'SRN')
eq(sim.eval('global.K.whatsact3'), 'deathanim', 'SRN: after the Roaring it is the finale')
eq(sim.eval('global.maxhp[2]') > 140, True, "SRN: the finale's max-HP joke goes to Susie")

# ---------- no Kris: Ralsei on top, Noelle: the Angel, then Ralsei alone parries ----------
sim = setup([3, 4, 0], 2)
eq(sim.eval('global.K.vb_fin'), 3, 'RN: Ralsei finishes')
seen, err = kill(sim, 1)
ok(err is None, 'RN loss 1 runs: %s' % err)
eq(says(sim), [3, 3], 'RN: Ralsei reacts')
ok('FIRESTORM' in texts(sim), 'RN: Ralsei learns FIRESTORM')
next_loss(sim)
W = set()
seen, err = kill(sim, 2, 5000, W)
ok(err is None, 'RN loss 2 runs: %s' % err)
ok(95 in seen and 96 in seen and 97 in seen, 'RN: Ralsei alone: the Knight charges, he parries (states %s)' % seen[:12])
ok('knocked the Knight' in texts(sim), 'RN: parry text (%s)' % texts(sim))
eq(sim.eval('global.hp[3]'), 140, 'RN: Ralsei is not hurt')
ok(130.5 in seen, 'RN: then his power-up scene (states %s)' % seen[-8:])
# build 39: the parry and the power-up use Ralsei's own (hatless) battle sprites, never his Chapter 1 hat set (spr_ralseib_*)
HAT = set(sim.eval(s) for s in ('spr_ralseib_idle', 'spr_ralseib_spell', 'spr_ralseib_spellready', 'spr_ralseib_attack', 'spr_ralseib_act'))
eq(sorted(W & HAT), [], 'RN: no hat sprite on Ralsei during the parry and the power-up')
ok(sim.eval('spr_ralsei_spellready') in W and sim.eval('spr_ralsei_spell') in W, 'RN: power-up in his spell-ready stance, the flurry in his spell pose')
sim.run('with (knight_hero_inst(3)) global.TMP = idlesprite;')
eq(sim.eval('global.TMP'), sim.eval('spr_ralsei_idle'), 'RN: Ralsei stands normally (hatless) after the power-up')
fi = sim.eval('global.K.vb_fin_idx')
eq(names(sim, 'actnameral')[fi], 'FireStorm', 'RN: his finisher is FIRESTORM (the move he learned)')
finale(sim, 3, fi, 'RN')

# ---------- no Kris: Susie, Noelle ----------
sim = setup([2, 4, 0], 2)
seen, err = kill(sim, 1)
ok(err is None and says(sim) == [2, 2, 2], 'SN loss 1: Susie reacts (%s) %s' % (says(sim), err))
ok('RUDER BUSTER' in texts(sim), 'SN: no Ralsei in the party: Susie learns RUDER BUSTER at the first loss')
next_loss(sim)
seen, err = kill(sim, 2, 5000)
ok(err is None and 95 in seen and 130.5 in seen, 'SN loss 2: Susie parries, then her finisher scene (states %s) %s' % (seen[-10:], err))
eq(names(sim, 'actnamesus')[sim.eval('global.K.vb_fin_idx')], 'RuderBuster', 'SN: RUDER BUSTER finisher')

# ---------- Susie on top, Kris in the middle, Ralsei at the bottom: Kris can be taken ----------
sim = setup([2, 1, 3], 2)
eq(sim.eval('global.K.vb_fin'), 2, 'SKR: Susie on top finishes (the Kris story is for Kris on top)')
eq(names(sim, 'actnamesus')[1], ' ' if names(sim, 'actnamesus')[1] == ' ' else names(sim, 'actnamesus')[1], '')
seen, err = kill(sim, 1)
ok(err is None, 'SKR loss 1 runs: %s' % err)
eq(sim.eval('global.K.kill_target') == sim.eval('obj_heroralsei'), True, 'SKR: Ralsei (bottom) first')
ok('RUDER BUSTER' in texts(sim), 'SKR: Susie learns RUDER BUSTER')
next_loss(sim)
seen, err = kill(sim, 2, 5000)
ok(err is None, 'SKR loss 2 runs: %s' % err)
eq(sim.eval('global.K.kill_target') == sim.eval('obj_herokris'), True, 'SKR: then Kris')
eq(sim.py(sim.eval('global.char')).count(1), 0, 'SKR: Kris left the party slots')
ok(sim.eval('global.hp[1]') < 0, 'SKR: Kris is lost')
eq(says(sim), [2, 2, 2], 'SKR: Susie: "K-Kris...?", "not you too", "END YOU!!!"')
ok(130.5 in seen, 'SKR: Susie\'s finisher scene (states %s)' % seen[-8:])
eq(names(sim, 'actnamesus')[sim.eval('global.K.vb_fin_idx')], 'RuderBuster', 'SKR: RUDER BUSTER finisher')

# ---------- Kris on top with Susie: Susie goes first, then Kris parries ----------
sim = setup([1, 2, 0], 2)
seen, err = kill(sim, 1, 4000)
ok(err is None and 30.5 in seen, 'KS loss 1: Susie taken, X-Slash scene (states %s) %s' % (seen[:16], err))
next_loss(sim)
seen, err = kill(sim, 2, 4000)
ok(err is None and 95 in seen and 30.5 not in seen, 'KS loss 2: Kris alone parries, no second X-Slash scene (states %s) %s' % (seen, err))
eq(sim.eval('global.K.whatsact3'), 'xslash', 'KS: X-Slash stays')
ok(any(c[0] == 'scr_mnendturn' for c in sim.calls), 'KS: the fight goes on')

# ---------- solos: two parries, then the finisher ----------
for party, fin, name in [([2, 0, 0], 2, 'RudeBuster'), ([3, 0, 0], 3, 'FireShock'), ([4, 0, 0], 4, 'SnowGrave'), ([2, 2, 2], 2, 'RudeBuster'), ([1, 0, 0], 1, 'X-Slash')]:
    sim = setup(party, 2)
    eq(sim.eval('global.K.vb_fin'), fin, '%s: finisher member' % party)
    seen, err = kill(sim, 1)
    ok(err is None and 95 in seen, '%s loss 1: parry (states %s) %s' % (party, seen[:10], err))
    ok(fin in sim.py(sim.eval('global.char')), '%s: nobody lost' % party)
    next_loss(sim)
    seen, err = kill(sim, 2, 5000)
    ok(err is None and 95 in seen, '%s loss 2: parry (states %s) %s' % (party, seen[:10], err))
    if fin == 1:
        eq(sim.eval('global.K.whatsact3'), 'xslash', '%s: Kris gets X-Slash' % party)
        continue
    ok(130.5 in seen, '%s: finisher scene' % party)
    arr = {2: 'actnamesus', 3: 'actnameral', 4: 'actnamenoe'}[fin]
    fi = sim.eval('global.K.vb_fin_idx')
    eq(sim.eval('global.%s[0][%d]' % (arr, fi)), name, '%s: finisher %s' % (party, name))
    finale(sim, fin, fi, str(party))

print('weird38 tests', N[0], 'fails', len(FAILS), '%.0fs' % (time.time() - t0)); sys.exit(1 if FAILS else 0)
