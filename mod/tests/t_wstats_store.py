from harness import *
sim=make_sim(); sim.run('knight_store_load();')
sim.run('global.knight_cfg.c_wstats=1; global.knight_cfg.weird=1; knight_store_save();')
sim.run('global.knight_loaded=false; global.knight_cfg=knight_cfg_default(); knight_store_load();')
print('wstats after reload',sim.eval('global.knight_cfg.c_wstats'),sim.eval('global.knight_cfg.weird'))
assert sim.eval('global.knight_cfg.c_wstats')==1
sim.run('global.spell[3][0]=14; global.spell[4][1]=15; global.spell[1][2]=12; global.knight_last_spells=knight_spells_to_string();')
s=sim.eval('knight_spells_to_string()'); print(s)
print('WSTATS STORE OK')
