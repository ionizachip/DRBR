from harness import *
def L(e): return [sim.eval('%s[%d]'%(e,i)) for i in range(5)]
sim=make_sim(); sim.load_file(M+'gml_GlobalScript_knight_core.gml',entry='gml_GlobalScript_knight_core')
sim.run('global.knight_orig={maxhp:[0,90,110,100,80],at:[0,5,6,7,8],df:[0,1,2,3,4],mag:[0,0,1,2,3]};global.knight_weird_stats=0;')
# Weird Route finale gave Kris +400 max HP, hp above max
sim.run('global.maxhp=[0,490,110,100,80];global.hp=[0,490,-20,100,80];global.at=[0,50,6,7,8];global.df=[0,9,2,3,4];global.mag=[0,0,1,2,3];')
sim.eval('knight_apply_stat_options({weird:1,c_halfhp:0,c_wstats:0})')
pass
assert L('global.maxhp')==[0,90,110,100,80] and L('global.hp')==[0,90,-20,100,80] and L('global.at')==[0,5,6,7,8]
sim.run('global.maxhp=[0,490,110,100,80];global.knight_weird_stats=1;')
sim.eval('knight_apply_stat_options({weird:1,c_halfhp:0,c_wstats:1})')
pass
assert L('global.maxhp')==[0,186,222,166,166]
sim.eval('knight_apply_stat_options({weird:1,c_halfhp:1,c_wstats:1})')
pass
assert L('global.maxhp')==[0,93,111,83,83]
sim.run('global.knight_weird_stats=1;')
sim.eval('knight_apply_stat_options({weird:0,c_halfhp:0,c_wstats:1})')
assert L('global.maxhp')==[0,90,110,100,80]   # weird stats only with Weird Route
print('STACKSTATS OK')
