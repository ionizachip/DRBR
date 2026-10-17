from harness import *
import sys
sim=make_sim()
M2=M
sim.load_file(M2+'gml_GlobalScript_scr_damage.gml',entry='gml_GlobalScript_scr_damage')
for n in ['scr_damage_cache','scr_damage_check','scr_dmgwriter_selfchar','scr_oflash','snd_play','scr_shakeobj','scr_dead','scr_tensionheal']:
    try: sim.mock(n,0)
    except Exception as e: print('nomock',n,e)
for ent in ('scr_randomtarget_old','scr_damage_calculation'):
    sim.load_file('/home/claude/work/gml/base/CodeEntries/gml_GlobalScript_%s.gml'%ent,entry='gml_GlobalScript_%s'%ent)
sim.mock('scr_element_damage_reduction',lambda s,*a:a[0])
sim.mock('debug_message',0); sim.mock('camerax',0); sim.mock('cameray',0)
try:
    sim.define_object('obj_dmgwriter'); sim.load_file('/home/claude/work/gml/base/CodeEntries/gml_Object_obj_dmgwriter_Create_0.gml',entry='gml_Object_obj_dmgwriter_Create_0')
except Exception as e: print('dw',e)
print('loaded')
sim.define_object('obj_b')
setup=('global.inv=-1; global.chapter=3; global.char=[1,0,4]; global.hp=[0,-20,90,90,19]; global.maxhp=[0,160,90,90,120]; global.battledf=[0,2,2,2,1]; '
 'global.charcantarget=[1,1,1]; global.targeted=[0,0,0,0]; global.chardead=[0,0,0]; global.tension=0; global.invc=1; global.knight_variant=0; '
 'global.charinstance=[instance_create(0,0,obj_b),instance_create(0,0,obj_b),instance_create(0,0,obj_b)]; for(var _q=0;_q<3;_q++){global.charinstance[_q].myheight=0;global.charinstance[_q].x=0;global.charinstance[_q].y=0;} global.chararmor1=[0,0,0,0,0]; global.chararmor2=[0,0,0,0,0]; global.battleat=[0,10,10,10,10]; global.mnfight=2; global.charcond=[0,0,0]; global.charaction=[0,0,0]; global.charspecial=[0,0,0]; global.charmove=[0,0,0]; global.faceaction=[0,0,0]; global.charauto=[0,0,0]; global.flag=array_create(2000,0);')
sim.run(setup)

import re
extra=[]
def attempt(tgt):
    for _ in range(40):
        sim.run(setup)
        sim.run('b=instance_create(0,0,obj_b); b.target=%d; b.damage=300; b.element=0;'%tgt+''.join(extra))
        try:
            sim.run('with(b){ scr_damage(); }'); return None
        except Exception as e:
            m=re.search(r'obj_b\.(\w+) not set',str(e))
            if m:
                nm=m.group(1); print('def',nm)
                if nm.startswith('obj_'): sim.define_object(nm)
                else: extra.append('b.%s=0;'%nm)
                continue
            return str(e)[:250]
    return 'too many'
bad=0
for tgt in (0,1,2):
    r=attempt(tgt)
    h=[sim.eval('global.hp[%d]'%i) for i in range(1,5)]
    ok_=(h[0]==-20 and h[3]<19 and h[1]==90 and h[2]==90)
    print('target',tgt,'hp',h,'PASS' if ok_ else 'FAIL', '(later harness error: %s)'%(r or '')[:60])
    bad+=0 if ok_ else 1
print('DMGSIM bad',bad); sys.exit(bad)
