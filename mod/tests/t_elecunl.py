import os,sys
from emu_atk import *
import emu_atk
def run(party, who, kris):
    sim=mk('elec',party); emu_atk.LAST=sim
    for _m in ['scr_84_get_sprite','scr_84_get_font','scr_enemyblcon','scr_battletext','scr_battletext_default','scr_speaker','scr_mnendturn','scr_damage_enemy','scr_oflash','scr_spellmenu_setup','scr_nextact','scr_battle_sprite_set','scr_revive']: sim.mock(_m,0)
    sim.define_object('obj_purify_event'); sim.define_object('obj_tensionbar'); sim.define_object('obj_elecknight_phase5effects'); sim.define_object('obj_glitchyknight'); sim.define_object('obj_knight_warp')
    sim._snapauto=True
    for c in party:
        if c in (1,2,3,4):
            _o={1:'obj_herokris',2:'obj_herosusie',3:'obj_heroralsei',4:'obj_heronoelle'}[c]
            auto(sim,lambda: sim.run('instance_create(100,100,%s);'%_o))
    sim.run('global.char=[%d,%d,%d];'%tuple(party))
    for i in (1,2,3,4): sim.run('global.hp[%d]=140;global.maxhp[%d]=140;'%(i,i))
    sim.run('global.monster=[1,0,0];global.monsterattackname=["","",""];global.monstername=["","",""];global.monsterhp=[99999,0,0];global.monstermaxhp=[99999,0,0];global.mnfight=1.5;global.turntimer=0;global.TT_end=-1;global.myfight=0;global.fighting=0;global.charaction=[0,0,0];global.acting=[0,0,0,0,0];global.faceaction=[0,0,0];global.canact=[[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0]];global.actcost=[[0,0,0,0,0,0],[0,0,0,0,0,0],[0,0,0,0,0,0]];global.tension=250;')
    ok,err=auto(sim,lambda: sim.run('with(obj_battlecontroller) instance_destroy(); instance_create(0,0,obj_battlecontroller); global.K=instance_create(300,100,obj_knight_enemy); global.K.myself=0; instance_create(300,300,obj_heart);'))
    if not ok: return ('create',err)
    sim.run('instance_create(0,0,obj_tensionbar);')
    ok,err=auto(sim,lambda: sim.run('with(global.K){ start_phase5(); }'))
    if not ok: return ('start5',err)
    sel={'sus':('actingsus','actconsus'),'ral':('actingral','actconral'),'noe':('actingnoe','actconnoe')}[who]
    idx = 1 if (kris and who!='noe') else 0
    sim.run('global.K.rtimer=0; global.K.talked=1; global.batmusic=[0,0]; global.charturn=-1; global.K.attackchosen=false; global.K.global_dummy=0; global.myfight=3; with(global.K){ %s=%d; %s=1; phase=5; }'%(sel[0],idx+1,sel[1]))
    traj=[]
    for f in range(300):
        ok,err=auto(sim,lambda: sim.step(1))
        if not ok: return ('err@%d'%f,err,traj)
        u=sim.eval('global.K.unleash_con')
        if not traj or traj[-1][1]!=u: traj.append((f,u))
        if f==5: sim.run('with(obj_purify_event) instance_destroy();')
        if u==0 and f>10: break
    return ('ok','actor',sim.eval('global.K.unleash_actor'),traj,sim.eval('global.K.phase'),sim.eval('global.K.actcon'))
if __name__=='__main__':
    party=eval(sys.argv[1]); who=sys.argv[2]; kris=int(sys.argv[3])
    print(party,who,kris,run(party,who,kris))
