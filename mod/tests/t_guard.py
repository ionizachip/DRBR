from harness import *
sim=make_sim(); sim.load_file(M+'gml_GlobalScript_knight_core.gml',entry='gml_GlobalScript_knight_core')
sim.run('global.hp=[0,10,-5,50,-30];global.r={gprev:undefined};')
sim.eval('knight_guard_downed(global.r)')            # primes
sim.run('global.hp[2]=-40; global.hp[4]=-80; global.hp[1]=3;')   # downed members hit again, Kris (alive) hit
sim.eval('knight_guard_downed(global.r)')
h=[sim.eval('global.hp[%d]'%i) for i in range(5)]
print(h); assert h[1]==3 and h[2]==-5 and h[3]==50 and h[4]==-30
sim.run('global.hp[2]=20;')  # revived: allowed to rise
sim.eval('knight_guard_downed(global.r)'); assert sim.eval('global.hp[2]')==20
sim.run('global.hp[2]=-1;')  # then dropped: alive->down normally
sim.eval('knight_guard_downed(global.r)'); assert sim.eval('global.hp[2]')==-1
print('GUARD OK')
