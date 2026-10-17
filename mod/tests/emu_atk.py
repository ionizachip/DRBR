import sys,re,glob,os,time
from emu_end2 import *
def reindex(sim):
    for nm,od in list(sim.objects.items()):
        if nm in sim.OBJIDX: od.index=sim.OBJIDX[nm]
    sim.obj_by_index={od.index:nm for nm,od in sim.objects.items()}
    for nm,od in sim.objects.items(): sim.names[nm]=od.index
    sim.desc_cache.clear(); sim.chain_cache.clear(); sim.events_cache.clear()
def mk(key,party):
    sim=scenario(key,party)
    OBJIDX=obj_index_table()
    sim.OBJIDX=OBJIDX
    reindex(sim); load_real(sim,['d_ex','scr_maincharacters_actors','scr_actor_setup']); sim.mock('scr_debug',0)
    sim.define_object('obj_cutscene_master')
    for _n in ['button1_h','button2_h','button3_h','left_h','right_h','up_h','down_h','button1_p','button2_p','button3_p','left_p','right_p','up_p','down_p','menu_h','menu_p']: sim.mock(_n,0)
    for _i,_c in enumerate(['os_windows','os_macosx','os_psp','os_ios','os_android','os_symbian','os_linux','os_winphone','os_tizen','os_win8native','os_wiiu','os_3ds','os_psvita','os_bb10','os_ps4','os_xboxone','os_ps3','os_xbox360','os_uwp','os_tvos','os_switch','os_ps5','os_xboxseriesxs']):
        try: sim.define_const(_c,_i)
        except Exception: pass
    names=set()
    for p in glob.glob(M+'gml_Object_*.gml'):
        b=os.path.basename(p)[len('gml_Object_'):-4]
        m=re.match(r'(.*)_(Create_0|Step_0|Step_1|Step_2|Alarm_\d+|Other_\d+|Destroy_0|CleanUp_0|Collision_\w+|Draw_\d+|PreCreate_0)$',b)
        if not m: continue
        o=m.group(1); names.add(o)
    for o in sorted(names):
        try: sim.define_object(o)
        except Exception: pass
    names.discard('obj_battlecontroller')
    for o in sorted(names):
        for p in glob.glob(M+'gml_Object_%s_*.gml'%o):
            ev=os.path.basename(p)[len('gml_Object_%s_'%o):-4]
            if re.match(r'(Create_0|Step_0|Step_1|Step_2|Alarm_\d+|Other_\d+|Destroy_0|CleanUp_0|Collision_\w+)$',ev):
                try: sim.load_file(p,entry=os.path.basename(p)[:-4])
                except Exception as e: pass
    BASEOBJ=['obj_heart','obj_growtangle','obj_dbulletcontroller','obj_herokris','obj_herosusie','obj_heroralsei','obj_dmgwriter','obj_darkener','obj_shake','obj_chara','obj_heroparent','obj_basicattack','obj_animation','obj_afterimage','obj_afterimage_screen','obj_afterimage_grow','obj_lerpvar','obj_bullet_knight_slash','obj_regularbullet','obj_dbullet','obj_collidebullet','obj_hurtbox']
    for o in BASEOBJ:
        try: sim.define_object(o)
        except Exception: pass
        for p in glob.glob(B+'gml_Object_%s_*.gml'%o):
            ev=os.path.basename(p)[len('gml_Object_%s_'%o):-4]
            if not os.path.exists(M+os.path.basename(p)) and re.match(r'(Create_0|Step_0|Step_1|Step_2|Alarm_\d+|Other_\d+|Destroy_0|CleanUp_0|Collision_\w+)$',ev):
                try: sim.load_file(p,entry=os.path.basename(p)[:-4])
                except Exception: pass
    for p in glob.glob(M+'gml_GlobalScript_*.gml'):
        bn=os.path.basename(p); nm=bn[len('gml_GlobalScript_'):-4]
        if nm.startswith('knight_') or nm in ('button1_h','scr_debug'): continue
        try: sim.load_file(p,entry=bn[:-4])
        except Exception as e: pass
    nld=0
    for p in glob.glob(B+'gml_GlobalScript_*.gml'):
        bn=os.path.basename(p)
        if os.path.exists(M+bn): continue
        nm=bn[len('gml_GlobalScript_'):-4]
        if nm in ('button1_h','button2_h','button3_h','left_h','right_h','up_h','down_h','button1_p','button2_p','button3_p','left_p','right_p','up_p','down_p','menu_h','menu_p','scr_debug'): continue
        try: sim.load_file(p,entry=bn[:-4]); nld+=1
        except Exception as e: pass
    sim.mock('object_get_depth',0)
    try: sim.run_global_inits()
    except Exception as e: print('ginit',str(e)[:100])
    sim.define_object('obj_battlecontroller')
    sim.define_event('obj_battlecontroller','Create',0,'victory=0;intro=2;cantspare=[0,0,0];encounterno=0;')
    sim.define_event('obj_battlecontroller','Step',0,'''reset = (variable_instance_exists(id,"reset")) ? reset : 0;
if (global.mnfight == 2) { global.turntimer -= 1; global.TT_active = 1;
 if (global.turntimer <= 0 && reset == 0) { with (obj_bulletparent) instance_destroy(); with (obj_bulletgenparent) instance_destroy(); with (obj_heart) instance_destroy(); reset = 1; global.TT_end = global.TT_f; global.mnfight = 0; } }
global.TT_f += 1; global.time = (variable_global_exists("time") ? global.time : 0) + 1;''')
    PAR={}
    for _ln in open('/home/claude/work/idx/objparents.tsv'):
        _p=_ln.rstrip('\n').split('\t')
        if len(_p)>=3 and _p[2] and _p[2] not in ('obj_heroparent','obj_chara','obj_actor','obj_moveheart'): PAR[_p[1]]=_p[2]
    sim.PAR=PAR
    for ch,pa in PAR.items():
        try: sim.define_object(ch,parent=pa,index=sim.OBJIDX.get(ch))
        except Exception: pass
    parents=set(PAR.values())
    for o in sorted(parents):
        for p in glob.glob(B+'gml_Object_%s_*.gml'%o):
            ev=os.path.basename(p)[len('gml_Object_%s_'%o):-4]
            if not os.path.exists(M+os.path.basename(p)) and re.match(r'(Create_0|Step_0|Step_1|Step_2|Alarm_\d+|Other_\d+|Destroy_0|CleanUp_0|Collision_\w+)$',ev):
                try: sim.load_file(p,entry=os.path.basename(p)[:-4])
                except Exception: pass
    reindex(sim)
    done=set()
    def hook(name):
        chain=[]; o=name
        while o and o not in chain:
            chain.append(o); o=sim.PAR.get(o)
        for o in chain:
            if o in done: continue
            done.add(o)
            if o in ('obj_heroparent','obj_chara','obj_actor'): continue
            for p in glob.glob(B+'gml_Object_%s_*.gml'%o):
                ev=os.path.basename(p)[len('gml_Object_%s_'%o):-4]
                if not os.path.exists(M+os.path.basename(p)) and re.match(r'(Create_0|Step_0|Step_1|Step_2|Alarm_\d+|Other_\d+|Destroy_0|CleanUp_0|Collision_\w+)$',ev):
                    try: sim.load_file(p,entry=os.path.basename(p)[:-4])
                    except Exception: pass
    sim.create_hook=hook
    return sim
LAST=None
def attack(key,party,phase,turn,frames=900,hp=140,name=None,sideb=0):
    global LAST
    sim=mk(key,party); LAST=sim
    if os.environ.get('PRACPICK'):
        sim.load_file(M+'gml_Object_obj_knight_enemy_Draw_64.gml',entry='gml_Object_obj_knight_enemy_Draw_64')
    for c in party:
        if c in (1,2,3):
            _o=('obj_herokris','obj_herosusie','obj_heroralsei')[c-1]
            sim._snapauto=True
            auto(sim,lambda: sim.run('with(%s) instance_destroy(); instance_create(100,100,%s);'%(_o,_o)))
    ok,err=auto(sim,lambda: sim.run('global.hp[1]=%d;global.hp[2]=%d;global.hp[3]=%d;global.maxhp[1]=%d;global.maxhp[2]=%d;global.maxhp[3]=%d;'%((hp,)*6)))
    sim.run('global.monster=[1,0,0];global.monsterattackname=[\"\",\"\",\"\"];global.monstername=[\"\",\"\",\"\"];global.monstergold=[0,0,0,0];global.monsterexp=[0,0,0,0];global.monsterdef=[0,0,0];global.monsterinstance=[0,0,0];global.monsterhp=[99999,0,0];global.monstermaxhp=[99999,0,0];global.monsterat=[10,0,0];global.monsterdf=[0,0,0];global.monstermaxhp=[99999,0,0];global.monstertype=[0,0,0];global.monsterstatus=[0,0,0];global.charcantarget=[1,1,1];global.targeted=[0,0,0,0,0];global.charaction=[0,0,0];global.acting=[0,0,0,0,0];global.faceaction=[0,0,0];global.charmove=[0,0,0];global.mnfight=1.5;global.inv=0;global.invc=1;global.turntimer=0;global.TT_f=0;global.TT_end=-1;global.TT_active=0;global.bmenuno=0;global.myfight=0;global.fighting=0;global.msc=0;global.typer=5;')
    sim.run('global.flag[9998]=0;')
    if os.environ.get('PRAC'): sim.run('global.kaizo_practice=1;')
    if os.environ.get('SIDEB'): sim.run('global.flag[456]=1;')
    sim._snapauto=True
    ok,err=auto(sim,lambda: sim.run('with(obj_battlecontroller) instance_destroy(); instance_create(0,0,obj_battlecontroller); with(obj_knight_enemy) instance_destroy(); with(obj_heart) instance_destroy(); global.K=instance_create(300,100,obj_knight_enemy); global.K.myself=0; instance_create(300,300,obj_heart);'))
    if not ok: return ('create',err)

    if os.environ.get('PRAC'):
        sim.run('var _pi=0; for (var _q=0;_q<array_length(global.K.prac_list);_q++) { if (global.K.prac_list[_q][0]==%d && global.K.prac_list[_q][1]==%d) _pi=_q; } global.K.prac_sel=_pi;'%(phase,turn)); print('practicemode',sim.eval('global.K.practicemode'),'sel',sim.eval('global.K.prac_sel'))
    sim.run('global.K.phase=%d; global.K.phaseturn=%d; global.K.turn=%d;global.mnfight=1.5; global.K.attackchosen=false; global.K.talked=1; global.K.rtimer=0;'%(phase,turn-1,turn))
    if os.environ.get('PRACPICK'):
        def pa(): return sim.eval('variable_instance_exists(global.K,"practiceatk") ? global.K.practiceatk : -99')
        out=[]
        for nm in ['right_p','right_p','left_p','left_p','left_p']:
            sim.mock('right_p',1 if nm=='right_p' else 0); sim.mock('left_p',1 if nm=='left_p' else 0)
            sim.run('global.myfight=0; global.mnfight=0; global.turntimer=0;')
            ok,err=auto(sim,lambda: sim.step(1)); out.append((nm,ok,(err or '')[:120],pa()))
        sim.run('global.charauto=[0,0,0,0,0];global.charturn=0;global.actingsingle=[0,0,0,0];'); sim.mock('right_p',0); sim.mock('left_p',0); sim.mock('button1_p',1)
        sim.run('global.myfight=0; global.mnfight=0; global.turntimer=0;')
        ok,err=auto(sim,lambda: sim.step(1)); out.append(('confirm',ok,(err or '')[:160],pa(),sim.eval('global.K.prac_sel')))
        return ('pick',str(out))
    if name: sim.run('global.K.kaizo_attack="%s";'%name)
    if phase==4 and not name: sim.run('global.K.phase4turn=%d;'%(turn-1))
    last=None; _t0=time.time()
    for f in range(frames):
        if f%3==0 and not (sim.eval('global.TT_end')>=0 and f>sim.eval('global.TT_end')+40): pass
        if sim.eval('global.TT_end')>=0 and f>sim.eval('global.TT_end')+0: break
        if f%3==0: sim.run('global.hp[1]=140;global.hp[2]=140;global.hp[3]=140;global.hp[4]=140;')
        ok,err=auto(sim,lambda: sim.step(1))
        if not ok:
            if sim.eval('global.TT_end')>=0 and 'object index 1463' in err: return ('ok-end',str((f,)))
            return ('step%d'%f,err)
        if time.time()-_t0>float(os.environ.get('WALL','240')): return ('ok-wall',str((sim.eval('global.K.myattackchoice'),sim.eval('global.TT_end'),f)))
        if os.environ.get('PR') and f%int(os.environ['PR'])==0: print('  f',f,round(time.time()-_t0,1),'mn',sim.eval('global.mnfight'),'tt',sim.eval('global.turntimer'),'inst',sim.eval('instance_count'),flush=True)
        if os.environ.get('TR') and f<int(os.environ['TR']): print(f,sim.eval('global.mnfight'),sim.eval('global.turntimer'),sim.eval('global.K.rtimer'),sim.eval('instance_number(obj_dbulletcontroller)'),sim.eval('instance_number(obj_heart)'))
    info=(sim.eval('global.K.myattackchoice'),sim.eval('global.mnfight'),sim.eval('global.myfight'),sim.eval('instance_number(obj_growtangle)'),sim.eval('instance_number(obj_dbulletcontroller)'),sim.eval('global.K.attacked'),sim.eval('global.turntimer'),sim.eval('global.TT_end'))
    return ('ok',str(info))
def main3():
    key=sys.argv[2]; specs=sys.argv[3].split(','); party=eval(sys.argv[4]); fr=int(sys.argv[5])
    for sp in specs:
        ph,tn=[int(x) for x in sp.split(':')]
        t=time.time(); r=attack(key,party,ph,tn,frames=fr); print(key,sp,party,r[0],(r[1] or '')[:250],round(time.time()-t,1),flush=True)
if __name__=='__main__' and sys.argv[1]=='pts': main3(); sys.exit()
def main2():
    key=sys.argv[2]; names=sys.argv[3].split(','); party=eval(sys.argv[4]); fr=int(sys.argv[5])
    for n in names:
        t=time.time(); r=attack(key,party,1,1,frames=fr,name=n); print(key,n,party,r[0],(r[1] or '')[:250],round(time.time()-t,1),flush=True)
if __name__=='__main__' and sys.argv[1]=='names': main2(); sys.exit()
if __name__=='__main__':
    key=sys.argv[1]; party=[1,2,3]
    ph,tn=int(sys.argv[2]),int(sys.argv[3])
    t=time.time(); r=attack(key,party,ph,tn,frames=int(sys.argv[4]) if len(sys.argv)>4 else 300); print(key,ph,tn,r[0],(r[1] or '')[:300],round(time.time()-t,1))
