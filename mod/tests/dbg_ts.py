import os,sys,time
from emu_atk import *
import emu_atk
r=attack('violet',[1,2,3],3,7,frames=60)
print(r)
sim=emu_atk.LAST
for blk in range(14):
    ok,err=auto(sim,lambda: sim.step(60))
    if not ok: print('ERR',err[:150]); break
    print(blk,'tt',sim.eval('global.turntimer'),'mn',sim.eval('global.mnfight'),'TT_end',sim.eval('global.TT_end'),'mgr',sim.eval('instance_number(obj_tracking_swords_manager)'),
      'con',sim.eval('obj_tracking_swords_manager.con'),'sc',sim.eval('obj_tracking_swords_manager.swordcount'),'set',sim.eval('obj_tracking_swords_manager.setcount'),'t',sim.eval('obj_tracking_swords_manager.timer'),flush=True)
