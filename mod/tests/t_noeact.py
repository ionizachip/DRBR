import sys,os
from emu_atk import *
import emu_atk
bad=0
for key in sys.argv[1:]:
    r=attack(key,[1,2,4],1,1,frames=0)
    sim=emu_atk.LAST
    for _n in ['scr_battletext_default','scr_84_get_font','scr_nextact']:
        try: sim.mock(_n,0)
        except Exception as e: print('nomock',_n,e)
    sim.run('global.K.actingnoe=1; global.K.actconnoe=1; global.K.actcon=0; global.myfight=3; global.charname=["","Kris","Susie","Ralsei","Noelle"];')
    ok,err=auto(sim,lambda: sim.step(1))
    n=sim.eval('variable_instance_exists(global.K,"nactcount") ? global.K.nactcount : -1'); ac=sim.eval('global.K.actconnoe'); a=sim.eval('global.K.actcon')
    good = (n==1 and ac==0)
    print(key,'step ok',ok,(err or '')[:100],'nactcount',n,'actconnoe',ac,'actcon',a,'PASS' if good else 'FAIL')
    if not good: bad+=1
print('NOEACT bad',bad)
