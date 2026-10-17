from harness import *
FAILS=[];N=[0]
def ok(c,msg):
    N[0]+=1
    if not c:FAILS.append(msg);print('FAIL',msg)
def eq(a,b,msg):
    N[0]+=1
    if a!=b:FAILS.append(msg);print('FAIL',msg,'got',repr(a),'want',repr(b))
def new(cfgcode='',key='base'):
    sim=make_sim(); sim.run('knight_store_load();')
    sim.run('var c=knight_cfg_default(); c.knight=knight_find_key("%s"); %s global.L=knight_resolve(c);'%(key,cfgcode))
    assert sim.eval('global.L.ok'),sim.eval('global.L.errors')
    sim.run('global.knight_launch=global.L; knight_launch_go();')
    return sim
def start_battle(sim):
    sim.run('if(!instance_exists(obj_battlecontroller)) instance_create_depth(0,0,0,obj_battlecontroller); knight_run_tick();')
def rec(sim,key,cat):
    return sim.py(sim.eval('knight_rec_get("%s","%s")'%(key,cat)))
def tick(sim,n,dmg=0,who=1):
    for i in range(n):
        if dmg: sim.run('global.hp[%d]-=%d;'%(who,dmg))
        sim.run('knight_run_tick();')

