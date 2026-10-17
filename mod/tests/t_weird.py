import os,sys,time
from emu_atk import *
import emu_atk
def run(key,party,kt,phase,frames=1500,sideb=1):
    sim=mk(key,party); emu_atk.LAST=sim
    sim.define_object('obj_dummy_bl'); sim.define_const('violetknight_sideb',0)
    for _m in ['scr_84_get_sprite','scr_84_get_font','scr_enemyblcon','scr_battletext','scr_battletext_default','scr_speaker','scr_mnendturn','scr_damage_enemy','scr_dark_marker_dummy','scr_spellmenu_setup']: sim.mock(_m,0)
    sim._snapauto=True
    for c in party:
        if c in (1,2,3,4):
            _o={1:'obj_herokris',2:'obj_herosusie',3:'obj_heroralsei',4:'obj_heronoelle'}[c]
            auto(sim,lambda: sim.run('instance_create(100,100,%s);'%_o))
    sim.run('global.flag[456]=%d;global.char=[%d,%d,%d];'%(sideb,*party))
    for i in (1,2,3,4): sim.run('global.hp[%d]=140;global.maxhp[%d]=140;'%(i,i))
    sim.run('global.monster=[1,0,0];global.monsterattackname=[\"\",\"\",\"\"];global.monstername=[\"\",\"\",\"\"];global.monstergold=[0,0,0,0];global.monsterexp=[0,0,0,0];global.monsterdef=[0,0,0];global.monsterinstance=[0,0,0];global.monsterhp=[99999,0,0];global.monstermaxhp=[99999,0,0];global.monsterat=[10,0,0];global.monsterdf=[0,0,0];global.monstermaxhp=[99999,0,0];global.monstertype=[0,0,0];global.monsterstatus=[0,0,0];global.charcantarget=[1,1,1];global.targeted=[0,0,0,0,0];global.charaction=[0,0,0];global.acting=[0,0,0,0,0];global.faceaction=[0,0,0];global.charmove=[0,0,0];global.mnfight=1.5;global.inv=0;global.invc=1;global.turntimer=0;global.TT_f=0;global.TT_end=-1;global.TT_active=0;global.bmenuno=0;global.myfight=0;global.fighting=0;global.msc=0;global.typer=5;')
    ok,err=auto(sim,lambda: sim.run('with(obj_battlecontroller) instance_destroy(); instance_create(0,0,obj_battlecontroller); global.K=instance_create(300,100,obj_knight_enemy); global.K.myself=0; instance_create(300,300,obj_heart);'))
    if not ok: return ('create',err)
    sim.run('global.K.phase=%d;global.K.phaseturn=0;global.K.turn=0;global.mnfight=99;global.myfight=99;global.charturn=-1;global.K.attackchosen=false;global.K.talked=1;global.K.rtimer=0;global.batmusic=[0,0];global.K.myblcon=instance_create(0,0,obj_dummy_bl); with(obj_herokris) myself=0; '%phase)
    sim.run('with(global.K){ %s }'%kt)
    traj=[];last=None
    for f in range(frames):
        ok,err=auto(sim,lambda: sim.step(1))
        if not ok: return ('err@%d'%f,err,traj)
        k=sim.eval('global.K.knightkillcon')
        if k!=last: traj.append((f,k)); last=k
        if k==0 and f>5: break
    return ('ok',sim.eval('global.spell[4]'),sim.eval('global.K.v_sideb'),traj[-12:],sim.eval('global.K.sus_dead'),sim.eval('global.K.ral_dead'),sim.eval('global.K.whatsact3'))
if __name__=='__main__':
    party=eval(sys.argv[1]); which=sys.argv[2]
    sel=lambda a,b: ('kill_target=%s;'%a)
    if which=='p1': kt='knightkillcon=2; kill_target=(scr_havechar(3) ? obj_heroralsei : (scr_havechar(4) ? obj_heronoelle : -4));'; ph=2
    else: kt='knightkillcon=2; kill_target=(scr_havechar(2) ? obj_herosusie : -4);'; ph=3
    print(party,which,run('violet',party,kt,ph))
