from harness import *
sim=make_sim()
sim.mock('scr_dead',lambda s,i:(sim.run('global.charmove[%d]=0;global.charcantarget[%d]=0;global.chardead[%d]=1;global.charaction[%d]=0;global.charspecial[%d]=0;'%((int(i),)*5)),0)[1])
sim.run('global.char=[3,4,3]; global.hp=[0,10,10,-999,10]; global.chardead=[1,0,0]; global.charmove=[0,1,1]; global.charcantarget=[0,1,1];')
sim.run('knight_sync_downed();')
assert sim.eval('global.chardead[2]')==1 and sim.eval('global.charmove[2]')==0 and sim.eval('global.charcantarget[2]')==0,'clone marked down'
assert sim.eval('global.chardead[1]')==0 and sim.eval('global.charmove[1]')==1,'Noelle untouched'
# revive: slot 0 healed up (chardead 0), clone follows
sim.run('global.hp[3]=40; global.chardead[0]=0; global.charmove[0]=1; knight_sync_downed();')
assert sim.eval('global.chardead[2]')==0 and sim.eval('global.charmove[2]')==1,'clone revived with sibling'
# a lone member scripted dead (hp>0, chardead 1) stays dead
sim.run('global.char=[1,2,3]; global.hp=[0,50,50,50,50]; global.chardead=[0,1,1]; global.charmove=[1,0,0]; knight_sync_downed();')
assert sim.eval('global.chardead[1]')==1 and sim.eval('global.chardead[2]')==1,'scripted down kept'
print('DUPDOWN OK')
