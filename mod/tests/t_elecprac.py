import os,sys
os.environ['PRAC']='1'
from emu_atk import *
import emu_atk
# build battle, then drive Draw_64 picker
sim=mk('elec',[1,2,3]); 
for c in [1,2,3]:
    _o=('obj_herokris','obj_herosusie','obj_heroralsei')[c-1]; sim._snapauto=True
    auto(sim,lambda: sim.run('with(%s) instance_destroy(); instance_create(100,100,%s);'%(_o,_o)))
sim.run('global.hp[1]=140;global.hp[2]=140;global.hp[3]=140;global.maxhp[1]=140;global.maxhp[2]=140;global.maxhp[3]=140;')
sim.run('global.kaizo_practice=1;')
ok,err=auto(sim,lambda: sim.run('instance_create(0,0,obj_battlecontroller); global.K=instance_create(0,0,obj_knight_enemy);'))
print('create',ok,err)
for n in ['draw_rectangle','draw_set_alpha','draw_set_color','draw_set_font','draw_set_halign','draw_set_valign','draw_get_font','draw_get_halign','draw_get_valign','draw_get_color','draw_get_alpha','draw_text_outline','snd_play','mean','scr_kaizo_killobjs_prac']:
    try: sim.mock(n,0)
    except Exception as e: pass
sim.mock('draw_get_font',0)
sim.run('global.myfight=0; global.turntimer=0;')
def pa(): return sim.eval('variable_instance_exists(global.K,"practiceatk") ? global.K.practiceatk : -99')
for nm in ['right_p','right_p','left_p','left_p','left_p']:
    sim.mock('right_p',1 if nm=='right_p' else 0); sim.mock('left_p',1 if nm=='left_p' else 0)
    sim.run('global.myfight=0; global.turntimer=0;')
    ok,err=auto(sim,lambda: sim.step(1)); print(nm,ok,(err or '')[:150],'practiceatk',pa())
sim.mock('right_p',0); sim.mock('left_p',0); sim.mock('button1_p',1)
sim.run('global.myfight=0; global.turntimer=0;')
ok,err=auto(sim,lambda: sim.step(1)); print('confirm',ok,(err or '')[:200],'sel',sim.eval('global.K.prac_sel'),'practiceatk',pa())
