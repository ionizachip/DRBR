"""Build 50: an online match with Flowery as your SKIN starts (the kit of every player, not his hub stats) and puts his gear back
afterwards; online at all, the party does not follow you in the overworld."""
from harness import *
FAILS = []; N = [0]
def ok(c, msg):
    N[0] += 1
    print(('ok   ' if c else 'FAIL ') + msg, flush=True)
    if not c: FAILS.append(msg)
sim = make_sim(); sim.run('knight_store_load(); knight_cc_stats();')
sim.run('global.charweapon[5] = 30; global.chararmor1[5] = 30; global.chararmor2[5] = 31;')
sim.run('kfo_get(); global.kfo.M = undefined; var _c = knight_cfg_default(); _c.mode = 0; _c.combo = 3; _c.knight = knight_find_key("base"); _c.knight2 = _c.knight; _c.party = [5, 0, 0];'
        'global.knight_launch = { src: _c, cfg: _c, plan: [_c.knight], reveal: "", corr: [] }; knight_launch_go();')
ok(sim.py(sim.eval('global.char')) == [5, 0, 0], 'the online fight: you as your SKIN (Flowery), nobody else %r' % sim.py(sim.eval('global.char')))
ok(sim.eval('global.maxhp[5]') == 150 and sim.eval('global.at[5]') == 14 and sim.eval('global.spell[5][0]') == 0 and sim.eval('global.charweapon[5]') == 0,
   'the online kit, not his hub stats / techniques (max HP %r, AT %r, spell %r)' % (sim.eval('global.maxhp[5]'), sim.eval('global.at[5]'), sim.eval('global.spell[5][0]')))
sim.run('kfo_kit_restore();')
ok([sim.eval('global.charweapon[5]'), sim.eval('global.chararmor1[5]'), sim.eval('global.chararmor2[5]')] == [30, 30, 31], 'after the match his gear is back')
sim.run('global.knight_run = 0; global.krun = undefined; with (obj_battlecontroller) instance_destroy(); instance_create(0, 0, obj_mainchara); global.kfo.st = "lobby"; global.kfo.mode = "steam";')
ok(sim.eval('kfo_ow_party_off()'), 'online (a lobby): the party does not follow')
sim.run('global.kfo.st = "idle"; global.kfo.mode = "off"; global.kfo.prac = false;')
ok(not sim.eval('kfo_ow_party_off()'), 'off-line: the party is back')
# switching knights in a lineup (online, Tag Team, Remix): his hero is not one of the knight's own objects (they are put away)
ok(not sim.eval('knight_lu_owned(obj_knight_herocc)') and sim.eval('knight_lu_owned(obj_knight_twin_bullet)') == 0, 'switching knights never puts his hero away')
# the overworld around a hub fight: he follows as himself (not Berdly, not nobody)
for o in ('obj_caterpillarchara',):
    try: sim.define_object(o)
    except Exception: pass
sim.run('global.knight_run = 1; global.krun = { state: "battle", cfg: knight_cfg_default(), party: [1, 5, 0] }; global.char = [1, 5, 0]; global.cinstance = [noone, noone];'
        'with (obj_mainchara) instance_destroy(); instance_create(100, 100, obj_mainchara); global.DC = instance_create(0, 0, obj_knight_prompt); with (global.DC) { havechar = [0,0,0,0,0]; charpos = [0,0,0,0,0]; knight_cc_follower(1); }')
ok(sim.eval('instance_exists(global.cinstance[0])') and sim.eval('global.cinstance[0].name') == 'flowery' and sim.eval('global.cinstance[0].dsprite') == sim.eval('knight_cc(5).walk[0]'),
   'a fight with him: his follower is Flowery (%r)' % sim.eval('instance_exists(global.cinstance[0]) ? global.cinstance[0].name : "none"'))
sim.load_file(M + 'gml_GlobalScript_scr_makecaterpillar.gml', entry='gml_GlobalScript_scr_makecaterpillar')
sim.run('var _c = scr_makecaterpillar(50, 50, 5, 1); global.CC = _c;')
ok(sim.eval('global.CC.name') == 'flowery' and sim.eval('global.CC.rsprite') == sim.eval('knight_cc(5).walk[1]'), "the game's follower maker: number 5 in a hub fight is Flowery, not Berdly")
sim.run('global.char = [5, 2, 0];')
ok(sim.eval('knight_cc_lead_ow()') == 5, 'leading the fight: you walk the cold place as him')
print('%d checks, %d failed' % (N[0], len(FAILS)))
sys.exit(1 if FAILS else 0)
