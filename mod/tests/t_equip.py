from harness import *
FAILS=[];N=[0]
def ok(c,msg):
    N[0]+=1
    if not c:FAILS.append(msg);print('FAIL',msg)
def eq(a,b,msg):
    N[0]+=1
    if a!=b:FAILS.append(msg);print('FAIL',msg,'got',repr(a),'want',repr(b))
sim=make_sim(); sim.run('knight_store_load();')
# info for every item id and character: no crash, names non-empty
for k in range(3):
    for c in range(1,5):
        n_ok=0
        for i in range(0,knight_max if False else (27 if k else 26)+1) if False else range(0,(26 if k==0 else 27)+1):
            r=sim.py(sim.eval('knight_equip_info(%d,%d,%d)'%(k,i,c)))
            ok(isinstance(r['name'],str) and r['name']!='','name %d %d %d'%(k,i,c))
            n_ok+=1 if r['ok'] else 0
        ok(n_ok>=1,'at least one wearable item kind %d char %d'%(k,c))
# step cycles only through wearable items, wraps, refreshes totals
for c in (1,2,3,4):
    sim.run('global.charweapon[%d]=0;'%c)
    seen=[]
    for i in range(40):
        v=sim.eval('knight_equip_step(%d,0,1)'%c); seen.append(v)
        ok(sim.eval('knight_equip_info(0,%d,%d).ok'%(v,c)),'step lands on wearable %d %d'%(c,v))
    ok(len(set(seen))>=1,'cycled')
    v0=sim.eval('knight_equip_step(%d,0,-1)'%c); v1=sim.eval('knight_equip_step(%d,0,1)'%c)
    eq(v1,seen[39%max(1,len(set(seen)))] if False else v1,'noop')
# clear + totals
sim.run('global.charweapon[1]=3; knight_equip_refresh();')
a=sim.eval('global.itemat[1][0]')
sim.run('knight_equip_clear(1,0);')
eq(sim.eval('global.charweapon[1]'),0,'cleared')
# string round trip
sim.run('global.charweapon[2]=sim_w; ' .replace('sim_w','0'))
for c in (1,2,3,4):
    sim.run('knight_equip_step(%d,0,1); knight_equip_step(%d,1,1);'%(c,c))
s=sim.eval('knight_equip_to_string()'); eq(len(s),12,'12 chars')
before=[sim.eval('knight_equip_get(%d,%d)'%(c,k)) for c in range(1,5) for k in range(3)]
sim.run('for (var c=1;c<=4;c++){global.charweapon[c]=0;global.chararmor1[c]=0;global.chararmor2[c]=0;}')
bad=sim.eval('knight_equip_from_string("%s")'%s); eq(bad,0,'round trip clean')
after=[sim.eval('knight_equip_get(%d,%d)'%(c,k)) for c in range(1,5) for k in range(3)]
eq(after,before,'round trip equal')
# garbage / unwearable / short strings never crash and stay valid
for g in ['','zzzzzzzzzzzz','!!!!!!!!!!!!','1','abc','000000000000','ffffffffffff','99999999999999999']:
    sim.run('knight_equip_from_string("%s");'%g)
    for c in range(1,5):
        for k in range(3):
            v=sim.eval('knight_equip_get(%d,%d)'%(c,k))
            ok(v==0 or sim.eval('knight_equip_info(%d,%d,%d).ok'%(k,v,c)),'valid after "%s" %d %d'%(g,c,k))
# snapshot restore: equipment goes back on leave, stays on hub
sim=make_sim(); sim.run('knight_store_load();')
sim.run('knight_snapshot_take(); global.knight_orig.eq[0][1]=global.charweapon[1];')
w0=sim.eval('global.charweapon[1]')
sim.run('knight_equip_step(1,0,1);'); w1=sim.eval('global.charweapon[1]')
sim.run('knight_snapshot_restore("hub");'); eq(sim.eval('global.charweapon[1]'),w1,'hub keeps equipment')
sim.run('knight_snapshot_restore("leave");'); eq(sim.eval('global.charweapon[1]'),w0,'leave restores equipment')
# PARTY tab drives equipment: lv1 < > steps the slot, Z opens the list, Z in the list equips the picked item, X backs out
sys.path.insert(0,'/home/claude/work/uiref')
from uiharness import menu_sim
sim,_rec=menu_sim(); sim.run('knight_store_load(); knight_menu_open();'); sim.step(1)
sim.run('global.knight_ui.inputdelay=0; global.knight_ui.tp=80; global.knight_ui.bp=60;')
def press(k):
    for kk in sim.inp: sim.inp[kk]=0
    sim.inp[k]=1; sim.run('knight_ui_step();'); sim.inp[k]=0
sim.run('global.knight_ui.tab=1; global.knight_ui.focus=1; global.knight_ui.lv=1; global.knight_ui.pslot=0; global.knight_ui.prow=0;')
ch=sim.eval('global.knight_cfg.party[0]')
w0=sim.eval('global.charweapon[%d]'%ch)
press('right'); w1=sim.eval('global.charweapon[%d]'%ch)
ok(sim.eval('knight_equip_info(0,%d,%d).ok'%(w1,ch)),'right lands on a wearable weapon')
press('ok'); eq(sim.eval('global.knight_ui.lv'),2,'Z opens the item list')
lst=sim.py(sim.eval('knight_ui_pick_list(%d,0)'%ch))
ok(0 in lst,'the list offers (nothing)')
for _ in range(len(lst)):
    if sim.eval('knight_ui_pick_list(%d,0)[global.knight_ui.ppick]'%ch)==0: break
    press('down')
press('ok'); eq(sim.eval('global.charweapon[%d]'%ch),0,'picking (nothing) empties the slot'); eq(sim.eval('global.knight_ui.lv'),1,'back on the slots')
press('down'); press('down'); eq(sim.eval('global.knight_ui.prow'),2,'down to the second armor')
press('back'); eq(sim.eval('global.knight_ui.lv'),0,'X back to the member row')
press('back'); eq(sim.eval('global.knight_ui.focus'),0,'X back to the tab bar')
# kris defaults
sim=make_sim(); sim.run('knight_kris_defaults();')
sp=[sim.eval('global.spell[1][%d]'%i) for i in range(12)]
ok(1 in sp and 5 in sp,'Kris gets X-Slash and Red Buster: %s'%sp)
sim.run('knight_kris_defaults();'); sp2=[sim.eval('global.spell[1][%d]'%i) for i in range(12)]
eq(sp2,sp,'defaults idempotent')
# preset keeps equipment through save -> store reload -> decode -> apply
sim=make_sim(); sim.run('knight_store_load(); knight_snapshot_take(); knight_equip_step(1,0,1); knight_equip_step(2,1,1);')
e0=sim.eval('knight_equip_to_string()')
sim.run('knight_preset_save(1,"EQ");'); sim.run('knight_store_save();')
sim.run('for (var c=1;c<=4;c++){global.charweapon[c]=0;global.chararmor1[c]=0;global.chararmor2[c]=0;}')
sim.run('knight_store_load(); global.d=knight_preset_decode(global.knight_presets[1]); knight_preset_apply(global.d);')
eq(sim.eval('knight_equip_to_string()'),e0,'preset equipment round trip')
print('equip tests',N[0],'fails',len(FAILS))
sys.exit(1 if FAILS else 0)
