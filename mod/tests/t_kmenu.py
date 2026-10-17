from harness import *
FAILS=[];N=[0]
def eq(a,b,msg):
    N[0]+=1
    if a!=b:FAILS.append(msg);print('FAIL',msg,'got',repr(a),'want',repr(b))
sim=make_sim()
eq(sim.eval('knight_kris_menu()'),False,'not in a hub run: vanilla Kris ACT list')
sim.run('global.knight_run=1; global.spell[1][0]=7;')
eq(sim.eval('knight_kris_menu()'),False,'ACT only: vanilla route')
sim.run('knight_kris_defaults();')
eq(sim.eval('knight_kris_menu()'),True,'ACT + X-Slash + Red Buster: magic list')
sim.run('global.spell[1][0]=0; global.spell[1][1]=0; global.spell[1][2]=0; global.spell[1][3]=0;')
eq(sim.eval('knight_kris_menu()'),False,'ACT entry removed: keep vanilla ACT list (ACT never lost)')
sim.run('global.spell[1][0]=0; knight_kris_defaults();')
eq(sim.eval('knight_kris_menu()'),True,'defaults restore ACT entry')
# actpick: only the ACT entry of a Kris slot
sim.run('global.charturn=0; global.char=[1,2,3]; global.bmenucoord=[[0,0,0],[0,0,0],[0,0,0]]; global.battlespell=[[7,1,5],[0,0,0],[0,0,0]];')
eq(sim.eval('knight_kris_actpick(0)'),True,'ACT entry picked')
sim.run('global.bmenucoord[2][0]=1;'); eq(sim.eval('knight_kris_actpick(0)'),False,'X-Slash is a spell')
sim.run('global.bmenucoord[2][0]=0; global.char=[2,1,3];'); eq(sim.eval('knight_kris_actpick(0)'),False,'only for Kris')
sim.run('global.knight_run=0; global.char=[1,2,3];'); eq(sim.eval('knight_kris_actpick(0)'),False,'only in hub runs')
# actor stand-ins
sim=make_sim(); sim.define_object('obj_actor')
sim.run('global.knight_run=1;')
sim.run('global.h=instance_create(0,0,obj_knight_prompt); with (global.h) knight_actor_stubs();')
eq(sim.eval('instance_number(obj_actor)'),3,'three stand-ins created'); sim.run('with (global.h) knight_actor_stubs();')
eq(sim.eval('instance_number(obj_actor)'),3,'idempotent')
eq(sim.eval('global.h.su_actor.visible') in (0,False),True,'invisible'); eq(sim.eval('global.h.ra'),2,'indices set')
sim.run('global.knight_run=0;'); sim2=make_sim(); sim2.define_object('obj_actor'); sim2.run('global.h=instance_create(0,0,obj_knight_prompt); with (global.h) knight_actor_stubs();')
eq(sim2.eval('instance_number(obj_actor)'),0,'no stubs outside hub runs')
sim.run('global.knight_run=1; instance_destroy(global.h.su_actor); with (global.h) knight_actors_ensure();')
eq(sim.eval('instance_number(obj_actor)'),3,'destroyed actor is replaced'); eq(sim.eval('i_ex(global.h.su_actor)'),True,'replacement is live')
sim.run('global.h.ra_actor=-4; with (global.h) knight_actors_ensure();'); eq(sim.eval('i_ex(global.h.ra_actor)'),True,'invalid ref replaced')
print('kmenu tests',N[0],'fails',len(FAILS)); sys.exit(1 if FAILS else 0)
