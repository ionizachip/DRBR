from emu_atk import *
import emu_atk
for key,expect in (('violet','The Angel'),('base','Noelle')):
    sim=mk(key,[1,2,4]); sim.run('global.charname=[0,"Kris","Susie","Ralsei","Noelle"];')
    attack(key,[1,2,4],1,1,frames=0); sim=emu_atk.LAST
    sim.run('global.charname=[0,"Kris","Susie","Ralsei","Noelle"];')
    sim.run('with(obj_knight_enemy) instance_destroy(); global.K=instance_create(300,100,obj_knight_enemy);')
    n=sim.eval('global.charname[4]'); print(key,n,'PASS' if n==expect else 'FAIL')
    sim.run('with(obj_knight_enemy) instance_destroy();')
    print(' after cleanup:',sim.eval('global.charname[4]'))
