from harness import *
FAILS=[];N=[0]
def ok(c,msg):
    N[0]+=1
    if not c:FAILS.append(msg);print('FAIL',msg)
def eq(a,b,msg):
    N[0]+=1
    if a!=b:FAILS.append(msg);print('FAIL',msg,'got',repr(a),'want',repr(b))
def new(cfg=''):
    sim=make_sim(); sim.run('knight_store_load();')
    for n in ('scr_damage_cache','scr_gameover','scr_heal'):
        sim.load_file(M+'gml_GlobalScript_%s.gml'%n,entry='gml_GlobalScript_%s'%n)
    sim.mock('i_ex',lambda s,o:s.eval('instance_exists(%s)'%'obj_knight_enemy'))
    sim.run('var c=knight_cfg_default(); c.c_nohit=1; %s global.L=knight_resolve(c); global.knight_launch=global.L; knight_launch_go();'%cfg)
    sim.run('instance_create_depth(0,0,0,obj_battlecontroller); instance_create_depth(0,0,0,obj_knight_enemy); knight_run_tick();')
    return sim
sim=new()
sim.run('global.chapter=3; global.damage_cache=[]; scr_damage_cache();')
eq(sim.eval('global.krun.failed'),True,'scr_damage_cache -> no-hit fail')
eq(sim.eval('global.krun.hits'),1,'one hit')
sim.run('scr_damage_cache();'); eq(sim.eval('global.krun.hits'),1,'fail fires exactly once')
sim.run('knight_defeat_begin();')
# gameover intercept: flag35==0
sim=new('c.c_nohit=0;'); sim.run('global.flag[35]=0; scr_gameover();')
eq(sim.eval('global.krun.state'),'lost','scr_gameover -> hub defeat')
# noheal
sim=new('c.c_nohit=0; c.c_heal=1;'); sim.run('global.hp[1]=10; scr_heal(0,50);')
eq(sim.eval('global.hp[1]'),10,'heal blocked'); 
sim=new('c.c_nohit=0;'); 
try:
    sim.run('global.hp[1]=10; scr_heal(0,50);'); print('heal normal ->',sim.eval('global.hp[1]'))
except Exception as e: print('normal heal not simulable:',str(e)[:100])
print('hook tests: %d checks, %d failures'%(N[0],len(FAILS)))
