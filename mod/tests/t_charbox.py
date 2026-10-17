import re
from harness import *
sim=make_sim()
txt=open(M+'gml_GlobalScript_scr_charbox.gml').read()
assert txt.count('if (rouxlsgridenabled && mmy[_sl] != 0)')>=1
txt=txt.replace('if (rouxlsgridenabled && mmy[_sl] != 0)','continue;\n            if (rouxlsgridenabled && mmy[_sl] != 0)')
sim.load_source('gml_GlobalScript_scr_charbox',txt)
sim.define_object('obj_tb'); sim.define_object('obj_rouxls_ch3_enemy'); sim.define_object('obj_tenna_board4_enemy'); sim.define_object('obj_battlecontroller')
sim.mock('i_ex',lambda s,o:0)
try:
    sim.run('''
    global.knight_variant=0; global.char=[1,1,1]; global.charturn=1; global.myfight=0; global.fighting=0;
    var o=instance_create_depth(0,0,0,obj_tb);
    with(o){ chartotal=3; mmy=[0,0,0,0]; charpos=[-1,-1,-1,-1]; havechar=[1,0,0,0]; hpcolor=[c_aqua,c_red,c_green,c_yellow]; rouxlsgridenabled=false; xx=0; yy=0; bp=0; bpoff=0; b_offset=0; global.myfight=0; }
    global.o=o;''')
    for i in range(14):
        for _ in range(60):
            try: sim.run('with(global.o){ scr_charbox(); }'); break
            except Exception as e:
                m=re.search(r'obj_tb\.(\w+) not set',str(e))
                if not m:
                    g=re.search(r"global variable name '(\w+)'",str(e))
                    if g: sim.run('global.%s=0;'%g.group(1)); continue
                    print('ERR',str(e)[:200]); break
                sim.run('global.o.%s=0;'%m.group(1))
    print(sim.eval('global.o.mmy[0]'),sim.eval('global.o.mmy[1]'),sim.eval('global.o.mmy[2]'))
except Exception as e: print('ERR',str(e)[:300])
assert sim.eval('global.o.mmy[1]')==-32 and sim.eval('global.o.mmy[0]')==0 and sim.eval('global.o.mmy[2]')==0
print('charbox duplicate animation: ok (active slot raised, others stay down)')
