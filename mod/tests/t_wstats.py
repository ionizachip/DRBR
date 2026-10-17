from harness import *
sim=make_sim(); sim.load_file(M+'gml_GlobalScript_knight_core.gml',entry='gml_GlobalScript_knight_core')
sim.run('global.maxhp=[0,90,90,90,90];global.hp=[0,50,90,90,90];global.at=[0,1,1,1,1];global.df=[0,1,1,1,1];global.mag=[0,1,1,1,1];global.knight_weird_stats=1;')
print(sim.eval('knight_apply_weird_stats({weird:0,c_wstats:1})'), sim.eval('global.maxhp'))
print(sim.eval('knight_apply_weird_stats({weird:1,c_wstats:1})'), sim.eval('global.maxhp'), sim.eval('global.hp'), sim.eval('global.at'), sim.eval('global.mag'))
sim.run('global.knight_weird_stats=0;global.maxhp=[0,90,90,90,90];')
print(sim.eval('knight_apply_weird_stats({weird:1,c_wstats:1})'), sim.eval('global.maxhp'))
