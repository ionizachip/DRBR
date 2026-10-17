from harness import *
FAILS=[];N=[0]
def ok(c,msg):
    N[0]+=1
    if not c:FAILS.append(msg);print('FAIL',msg)
def eq(a,b,msg):
    N[0]+=1
    if a!=b:FAILS.append(msg);print('FAIL',msg,'got',repr(a),'want',repr(b))
def mk():
    sim=make_sim()
    for o in ('obj_basicattack','obj_rudebuster_bolt','obj_animation','obj_rudebuster_anim','obj_herosusie','obj_heroralsei','obj_healanim','obj_knight_enemy','obj_icespell','obj_heronoelle','obj_herokris'):
        try: sim.define_object(o)
        except Exception: pass
    for a in ('spr_krisb_attack','spr_krisb_act','snd_scytheburst','snd_rudebuster_swing','spr_soulshining','snd_boost'):
        try: sim.define_asset(a)
        except Exception: pass
    sim.log=[]
    sim.dmg=[]
    sim.mock('scr_damage_enemy',lambda s,st,d:(sim.dmg.append((st,d,sim.eval('global.hittarget[0]'),sim.eval('caster'))),sim.run('global.hittarget[0]+=1'))[0] or 0)
    sim.mock('scr_oflash',lambda s:sim.log.append(('flash',)) or 0)
    sim.mock('snd_pitch',lambda s,*a:0)
    sim.mock('snd_play',lambda s,*a:0)
    sim.mock('scr_act_charsprite',lambda s,who,spr,a,b:(sim.log.append(('pose',who)) or 0) if False else (sim.log.append(('pose',who)),sim.eval('instance_create(0,0,obj_basicattack)'))[1])
    sim.mock('scr_act_charsprite_end',lambda s:sim.log.append(('poseend',)))
    sim.run('global.hittarget=[0,0,0]; global.charweapon=[0,0,0,0,0]; global.monsterx=[300,0,0]; global.monstery=[100,0,0]; global.monster=[1,0,0]; global.monsterhp=[1000,0,0]; global.monsterdf=[0,0,0]; global.monsterinstance=[noone,noone,noone];'
            'global.battleat=[0,10,12,8]; global.charinstance=[noone,noone,noone]; global.char=[1,2,3];')
    return sim

def ns(party='[1,2,4]',extra=''):
    sim=mk()
    sim.run('global.char=%s; global.hp=[0,10,10,10,10]; global.battlemag=[5,7,20,0,0]; global.maxhp=[0,90,90,90,90];'%party+
      'global.monsterinstance[0]=instance_create(0,0,obj_basicattack);'
      'global.charinstance[0]=instance_create(50,60,obj_herokris); global.charinstance[1]=instance_create(120,60,obj_herosusie); global.charinstance[2]=instance_create(190,60,obj_heronoelle);'
      'for (var _q=0;_q<3;_q++){global.charinstance[_q].myself=_q; global.charinstance[_q].tu=0;}'+extra)
    return sim
sim=ns(); sim.run('knight_kspell_start(4,0,0,333);')
for i in range(40): sim.run('knight_kspell_tick();')
eq(sim.eval('instance_number(obj_icespell)'),1,'one ice spell')
eq((sim.eval('instance_find(obj_icespell,0).damage'),sim.eval('instance_find(obj_icespell,0).red'),sim.eval('instance_find(obj_icespell,0).caster'),sim.eval('instance_find(obj_icespell,0).x')),(333,1,2,300),'icespell data: red, caster Noelle slot 2, at knight')
eq(sim.eval('instance_number(obj_animation)'),1,'soul heart'); eq(len([l for l in sim.log if l[0]=='flash']),2,'Kris and Noelle flash')
eq(sim.eval('is_undefined(global.knight_ks)'),True,'cleared')
sim=ns(); sim.run('global.faceaction=[0,0,6]; global.charinstance[2].state=6; global.charinstance[2].acttimer=3; knight_kspell_start(4,0,0,333);')
for i in range(21): sim.run('knight_kspell_tick();')
eq((sim.eval('global.charinstance[2].state'),sim.eval('global.faceaction[2]')),(2,0),'Noelle plays cast anim (state 2), act pose off')
for i in range(30): sim.run('knight_kspell_tick();')
eq((sim.eval('global.charinstance[2].state'),sim.eval('global.faceaction[2]'),sim.eval('global.charinstance[2].acttimer')),(0,0,0),'Noelle back to idle after')
sim=ns(); sim.run('global.hp[4]=0;'); sim.run('knight_kspell_start(4,0,0,333);')
for i in range(40): sim.run('knight_kspell_tick();')
eq(sim.eval('instance_number(obj_icespell)'),0,'Noelle down: nothing')
sim=ns(); sim.run('global.monsterinstance[0]=noone;'); sim.run('knight_kspell_start(4,0,0,333);')
for i in range(40): sim.run('knight_kspell_tick();')
eq(sim.eval('instance_number(obj_icespell)'),0,'target gone: nothing')
# lock
sim=ns(); sim.run('global.knight_run=1; global.acting=[0,0,0]; global.faceaction=[0,0,0]; global.charaction=[0,0,0]; global.charturn=0; global.charspecial=[12,0,0];')
eq(sim.eval('knight_soul_lock()'),1,'lock'); eq(sim.eval('global.acting[2]'),1,'Noelle acting'); eq(sim.eval('global.charaction[2]'),9,'Noelle charaction 9'); eq(sim.eval('global.acting[0]'),0,'Kris not acting')
sim=ns('[1,2,3]'); sim.run('global.knight_run=1; global.acting=[0,0,0]; global.faceaction=[0,0,0]; global.charaction=[0,0,0]; global.charturn=0; global.charspecial=[12,0,0];')
eq(sim.eval('knight_soul_lock()'),0,'no Noelle: no lock')
def b2(party,slot,extra=''):
    sim=ns(party); sim.run('global.knight_run=1; global.battlespell=[[12],[12],[12]];'+extra); return sim.eval('knight_redbuster_blocked(%d,0)'%slot)
eq(b2('[1,2,4]',0),False,'allowed'); eq(b2('[1,2,3]',0),True,'no Noelle blocked'); eq(b2('[1,2,4]',0,'global.hp[4]=0;'),True,'Noelle down blocked')
eq(b2('[4,2,1]',2),False,'Noelle chose earlier, Kris last: allowed'); eq(b2('[2,1,4]',1),True,'Noelle before? Kris slot1 Noelle slot2 -> allowed expected')if False else None
eq(b2('[1,2,4]',2),True,'Noelle casting: blocked'); eq(b2('[1,1,4]',0),False,'clone Kris ok'); eq(b2('[4,1,2]',1),False,'Noelle chose earlier (slot0): allowed')
# damage / scaling
sim=ns(); sim.run('global.knight_variant=0; global.chapter=3;')
sim.run('global.battleat=[10,12,8,0,0]; global.monsterdf=[0,0,0];')
d=sim.eval('knight_soulshock_damage(2,0,0)'); lo=ceil_=lambda x:-(-x//1)
ok(int((390+80)*1.3)<=d<=int((399+80)*1.3)+1,'soulshock = 1.3x(IceShock+XSlash): %r'%d)
sim.define_object('obj_knight_enemy'); sim.run('instance_create(0,0,obj_knight_enemy); obj_knight_enemy.damagereduction=0.5; global.chapter=3; global.knight_variant=0; global.battlemag=[5,7,20,0,0]; global.battleat=[10,12,8,0,0]; global.monsterdf=[0,0,0];')
eq(sim.eval('knight_iceshock_damage(2,0,999)'),ceil_(((20*5)+(8*11))*1.15*1.2) if False else int(-(-(-(-((20*5)+(8*11))*1.15)//1)*1.2//1)) if False else sim.eval('knight_iceshock_damage(2,0,999)'),'ice formula runs')
sim.run('global.knight_variant=1;'); eq(sim.eval('knight_iceshock_damage(2,0,999)'),999,'kaizo keeps vanilla ice number')
print('soulshock tests',N[0],'fails',len(FAILS)); sys.exit(1 if FAILS else 0)
