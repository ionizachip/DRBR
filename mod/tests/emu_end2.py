import sys,re
from emu_end import *
from t_run_helpers import *
KEYS={'base':0,'kaizo':1,'elec':2,'violet':3,'thorn':4,'cyan':5}
def scenario(key,party,steps=600,verbose=False):
    sim=new('c.party=%s;'%party if False else '',key)
    start_battle(sim)
    sim.run('global.knight_variant=%d;'%KEYS[key])
    sim.run('global.char=%s;'%party)
    for o in ['obj_ch3_PTB02','obj_actor','obj_caterpillarchara','obj_battleback','obj_fadeout','obj_dialoguer','obj_writer','obj_face']:
        try: sim.define_object(o)
        except Exception: pass
    for ev in ('Create_0','Step_0','Alarm_8','Other_17','CleanUp_0'):
        try: sim.load_file(M+'gml_Object_obj_ch3_PTB02_%s.gml'%ev,entry='gml_Object_obj_ch3_PTB02_%s'%ev)
        except Exception as e: pass
    return sim

def load_real(sim,names):
    for n in names:
        try: sim.load_file((M if os.path.exists(M+'gml_GlobalScript_%s.gml'%n) else B)+'gml_GlobalScript_%s.gml'%n,entry='gml_GlobalScript_%s'%n)
        except Exception as e: print('noload',n,e)
def play(key,party,frames=900,verbose=False,hero_objs=None):
    sim=scenario(key,party)
    load_real(sim,['scr_maincharacters_actors','scr_actor_setup','d_ex']); sim.mock('scr_debug',0)
    sim.run('global.tempflag[90]=%d;'%sim.eval('knight_reg(knight_find_key("%s")).skip_flag'%key) if False else 'var _x=0;')
    names={1:'kris',2:'susie',3:'ralsei',4:'noelle'}
    if os.environ.get('MUT'): sim.mock('knight_actors_ensure',0); sim.mock('knight_actor_stubs',0)
    sim.define_object('obj_cutscene_master'); sim.run('var _m=instance_create(0,0,obj_cutscene_master); _m.actor_id=[]; _m.actor_name=[];')
    # overworld
    sim.run('instance_create(300,200,obj_mainchara);')
    sim.run('global.cinstance=[];')
    k=0
    for c in party:
        if c in (2,3,4):
            sim.run('var _c=instance_create(280,200,obj_caterpillarchara); _c.name="%s"; global.cinstance[%d]=_c;'%(names[c],k)); k+=1
    # battle heroes
    present=set(party)
    sim.run('global.flag[456]=%d;global.flag[50]=%d;'%(1 if os.environ.get('W456') else 0,1 if os.environ.get('WIN') else 0)); sim.run('global.knight_mode=0; global.flag[50]=%d;'%(1 if os.environ.get('WIN') else 0)+' with (obj_battlecontroller) intro=0; global.batmusic=[0,0,0]; global.currentsong=[0,0,0];')
    for c,o in ((1,'obj_herokris'),(2,'obj_herosusie'),(3,'obj_heroralsei')):
        if c in present: sim.run('instance_create(100,100,%s);'%o)
    ok,err=auto(sim,lambda: sim.run('with (obj_ch3_PTB02) instance_destroy(); global.P=instance_create(0,0,obj_ch3_PTB02);'))
    log=[]
    if not ok: return ('create',err,log)
    last=None
    stall=0
    seq=[0,2,3,3.1,4,5,6,7,8,9,10,11,12]
    for f in range(frames):
        con=sim.eval('global.P.con')
        if con!=last: log.append((f,con)); last=con; stall=0
        else: stall+=1
        if con==4: sim.run('global.P.customcon=1; global.P.sword_draw_ready=true;')
        if con==6 and not sim.eval('instance_exists(obj_battlecontroller)'): sim.run('instance_create(0,0,obj_battlecontroller);')
        if con==6: sim.run('with (obj_battlecontroller) intro=2;')
        if stall>80 and con in seq and con!=12:
            nxt=seq[seq.index(con)+1]; sim.run('global.P.con=%s;'%nxt); stall=0; log.append((f,'forced',nxt))
        ok,err=auto(sim,lambda: sim.step(1) if hasattr(sim,'step') else None)
        if not ok: return ('step f=%d con=%s'%(f,sim.eval('global.P.con')),err,log)
    return ('done',None,log)
if __name__=='__main__':
    r=play('base',[1,2,3]); print(r[0],r[1]); print(r[2][:40])
