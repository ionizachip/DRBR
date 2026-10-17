import sys,re,glob,os
from emu_end2 import *
def smoke(objname,frames=25,key='thorn'):
    sim=scenario(key,[1,2,3]); load_real(sim,['d_ex']); sim.mock('scr_debug',0)
    sim.define_object('obj_cutscene_master')
    for o in ('obj_heart','obj_growtangle','obj_knight_enemy','obj_dbulletcontroller','obj_dmgwriter','obj_battleback'):
        try: sim.define_object(o)
        except Exception: pass
    sim.run('var _k=instance_create(300,100,obj_knight_enemy); _k.myself=0; instance_create(300,300,obj_heart); instance_create(300,300,obj_growtangle); instance_create(0,0,obj_dbulletcontroller);')
    try: sim.define_object(objname)
    except Exception: pass
    n=0
    for p in glob.glob(M+'gml_Object_%s_*.gml'%objname):
        ev=os.path.basename(p)[len('gml_Object_%s_'%objname):-4]
        if re.match(r'(Create_0|Step_0|Alarm_\d+|Other_\d+|Step_1|Step_2)$',ev):
            try: sim.load_file(p,entry=os.path.basename(p)[:-4]); n+=1
            except Exception as e: return ('load',str(e)[:100])
    ok,err=auto(sim,lambda: sim.run('with (%s) instance_destroy(); global.O=instance_create(300,200,%s);'%(objname,objname)))
    if not ok: return ('create',err)
    for f in range(frames):
        ok,err=auto(sim,lambda: sim.step(1))
        if not ok: return ('step%d'%f,err)
    return ('ok',None)
if __name__=='__main__':
    names=sys.argv[1:]
    for n in names:
        r=smoke(n); print(n,r[0],(r[1] or '')[:170],flush=True)
