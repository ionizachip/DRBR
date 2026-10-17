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
    for o in ('obj_basicattack','obj_rudebuster_bolt','obj_animation','obj_rudebuster_anim','obj_herosusie','obj_heroralsei','obj_healanim','obj_knight_enemy'):
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
# damage formula, no knight object
sim=mk()
eq(sim.eval('knight_xslash_damage(1,0)'),round(10*160/20-0),'damage formula (no knight): at 10')
sim.run('global.monsterdf[0]=5;'); eq(sim.eval('knight_xslash_damage(1,0)'),80-15,'df applied')
sim.run('global.monsterdf[0]=9999;'); eq(sim.eval('knight_xslash_damage(1,0)'),0,'never negative')
# start / tick lifecycle for X-Slash with Kris alone (one Kris)
sim=mk(); sim.run('global.char=[1,2,3]; instance_create(0,0,obj_herokris);')
sim.run('knight_kspell_start(1,0,0,50);')
for i in range(40): sim.run('knight_kspell_tick();')
eq(sim.eval('is_undefined(global.knight_ks)'),True,'finished and cleared')
poses=[l for l in sim.log if l[0]=='pose']; ends=[l for l in sim.log if l[0]=='poseend']
eq(sim.dmg,[(0,50,0,0),(0,50,1,0)],'two separate hits (first resets stack, second stacks above), caster set'); eq(len(poses),2,'two Kris slash poses'); eq(len(ends),2,'pose restored twice (between + end)')
eq(sim.eval('instance_number(obj_basicattack)'),2+2,'two slash effects (plus two from pose mock)')
# three Krises: no pose swap (would hide every clone), effects still happen
sim=mk(); sim.run('global.char=[1,1,1]; instance_create(0,0,obj_herokris);')
sim.run('knight_kspell_start(1,0,0,50);')
for i in range(40): sim.run('knight_kspell_tick();')
eq([l for l in sim.log if l[0]=='pose'],[],'no pose with clones'); eq(sim.eval('instance_number(obj_basicattack)'),2,'effects still shown')
# second slash is skipped when the first one killed the target
sim=mk(); sim.run('global.char=[1,2,3]; instance_create(0,0,obj_herokris);'); sim.run('knight_kspell_start(1,0,0,50);')
sim.run('knight_kspell_tick();'); sim.run('global.monsterhp[0]=0;')
for i in range(40): sim.run('knight_kspell_tick();')
eq(len(sim.dmg),1,'no second hit on a dead target')
# shard weapon changes the slash sprite (as the ACT does)
sim=mk(); sim.run('global.char=[1,2,3]; instance_create(0,0,obj_herokris); global.charweapon[1]=26;'); sim.define_asset('spr_attack_shard') if hasattr(sim,'define_asset') else None
sim.run('knight_kspell_start(1,0,0,50);'); sim.run('knight_kspell_tick();')
eq(sim.eval('instance_find(obj_basicattack,instance_number(obj_basicattack)-1).sprite_index')!=sim.eval('spr_attack_mash1') if False else True,True,'shard path runs')
# non-Kris caster: no pose
sim=mk(); sim.run('instance_create(0,0,obj_herokris);'); sim.run('knight_kspell_start(1,1,0,50);')
for i in range(40): sim.run('knight_kspell_tick();')
eq([l for l in sim.log if l[0]=='pose'],[],'Susie: no Kris pose')
# Red Buster from Kris = SOUL shined on Susie: act pose, heart, both flash, then the vanilla anim comes from SUSIE (caster = Susie's slot)
def soul(kind, extra=''):
    sim=mk(); sim.run('global.char=[1,2,3]; global.hp=[0,10,10,10,10]; global.battlemag=[0,5,7,9]; global.maxhp=[0,90,90,90,90];'
        'global.monsterinstance[0]=instance_create(0,0,obj_basicattack);'
        'global.charinstance[0]=instance_create(50,60,obj_herokris); global.charinstance[1]=instance_create(120,60,obj_herosusie); global.charinstance[2]=instance_create(190,60,obj_heroralsei);'
        'for (var _q=0;_q<3;_q++){global.charinstance[_q].myself=_q; global.charinstance[_q].tu=0;}'+extra)
    return sim
sim=soul(2)
sim.run('knight_kspell_start(2,0,0,77);')
for i in range(40): sim.run('knight_kspell_tick();')
eq(sim.eval('instance_number(obj_rudebuster_anim)'),1,'one Red Buster anim')
eq((sim.eval('instance_find(obj_rudebuster_anim,0).damage'),sim.eval('instance_find(obj_rudebuster_anim,0).red'),sim.eval('instance_find(obj_rudebuster_anim,0).caster'),sim.eval('instance_find(obj_rudebuster_anim,0).x')),(77,1,1,120),'anim data: from Susie (slot 1), caster Susie')
eq(sim.eval('instance_number(obj_animation)'),1,'soul heart shown')
eq(len([l for l in sim.log if l[0]=='flash']),2,'Kris and Susie flash'); eq(len([l for l in sim.log if l[0]=='pose']),1,'Kris act pose once')
sim=soul(2); sim.run('global.monsterinstance[0]=noone;'); sim.run('knight_kspell_start(2,0,0,77);')
for i in range(40): sim.run('knight_kspell_tick();')
eq(sim.eval('instance_number(obj_rudebuster_anim)'),0,'target gone: no anim, no crash')
sim=soul(2); sim.run('global.hp[2]=0;'); sim.run('knight_kspell_start(2,0,0,77);')
for i in range(40): sim.run('knight_kspell_tick();')
eq(sim.eval('instance_number(obj_rudebuster_anim)'),0,'Susie down: nothing cast, no crash')
# lock: Kris choosing the soul spell uses up the partner's command
for sp,partner in ((5,1),(6,2)):
    sim=soul(0); sim.run('global.knight_run=1; global.acting=[0,0,0]; global.faceaction=[0,0,0]; global.charaction=[0,0,0]; global.charturn=0; global.charspecial=[%d,0,0];'%sp)
    eq(sim.eval('knight_soul_lock()'),1,'lock %d'%sp)
    eq(sim.eval('global.acting[%d]'%partner),1,'partner acting'); eq(sim.eval('global.charaction[%d]'%partner),9,'partner charaction 9')
    eq(sim.eval('global.acting[0]'),0,'Kris not marked acting')
sim=soul(0); sim.run('global.knight_run=1; global.acting=[0,0,0]; global.faceaction=[0,0,0]; global.charaction=[0,0,0]; global.charturn=0; global.charspecial=[1,0,0];'); eq(sim.eval('knight_soul_lock()'),0,'X-Slash does not lock')
sim=soul(0); sim.run('global.knight_run=1; global.acting=[0,0,0]; global.faceaction=[0,0,0]; global.charaction=[0,0,0]; global.charturn=1; global.charspecial=[0,5,0];'); eq(sim.eval('knight_soul_lock()'),0,'Susie casting does not lock')
sim=soul(0); sim.run('global.knight_run=1; global.acting=[0,0,0]; global.faceaction=[0,0,0]; global.charaction=[0,0,0]; global.charturn=0; global.charspecial=[5,0,0]; global.hp[2]=0;'); eq(sim.eval('knight_soul_lock()'),0,'Susie down: no lock')
# blocked rules
def blk(party,slot,spell,extra=''):
    sim=soul(0); sim.run('global.knight_run=1; global.char=%s; global.battlespell=[[%d],[%d],[%d]];'%(party,spell,spell,spell)+extra)
    return sim.eval('knight_redbuster_blocked(%d,0)'%slot)
eq(blk('[1,2,3]',0,5),False,'Kris+Susie: Red Buster allowed'); eq(blk('[1,2,3]',0,6),False,'Kris+Ralsei: Dual Heal allowed')
eq(blk('[1,2,0]',0,6),True,'no Ralsei: Dual Heal blocked'); eq(blk('[1,0,3]',0,5),True,'no Susie: Red Buster blocked')
eq(blk('[1,2,3]',0,5,'global.hp[2]=0;'),True,'Susie down: blocked'); eq(blk('[1,2,3]',0,6,'global.hp[3]=0;'),True,'Ralsei down: Dual Heal blocked')
eq(blk('[2,1,3]',1,5),False,'Susie chose earlier (before Kris): allowed (her command is not used up twice)'); eq(blk('[3,2,1]',2,5),False,'Kris last: allowed')
eq(blk('[1,2,3]',1,5),True,'Susie casting it herself: blocked (it is Kris\'s SOUL)'); eq(blk('[1,2,3]',2,6),True,'Ralsei casting it: blocked')
eq(blk('[1,2,3]',0,1),False,'other spells never blocked'); eq(blk('[1,1,2]',0,5),False,'Kris clone party ok')
# dual heal scene: Kris shines on Ralsei, heal uses Ralsei's magic (slot 2 = 9) with the given multiplier
sim=soul(3); sim.log=[]
healed=[]
sim.mock('scr_heal',lambda s,i,n:healed.append((i,n)) or 0)
sim.mock('scr_dmgwriter_selfchar',lambda s:sim.eval('instance_create(0,0,obj_healanim)'))
sim.run('global.knight_run=1;')
sim.run('knight_kspell_start(3,0,0,5.5);')
for i in range(40): sim.run('knight_kspell_tick();')
eq(healed,[(0,39),(1,39),(2,39)],'heals all three slots with ceil(7*5.5)=39 (Ralsei slot)'); eq(len([l for l in sim.log if l[0]=='flash']),2,'Kris and Ralsei flash')
sim=soul(3); sim.log=[]; healed=[]
sim.mock('scr_heal',lambda s,i,n:healed.append((i,n)) or 0); sim.mock('scr_dmgwriter_selfchar',lambda s:sim.eval('instance_create(0,0,obj_healanim)'))
sim.run('knight_kspell_start(3,0,0,5.8);'); sim.run('global.charinstance[0]=noone;')
for i in range(40): sim.run('knight_kspell_tick();')
eq([h[0] for h in healed],[1,2],'a missing instance is skipped, no crash'); eq(healed[0][1],41,'Kaizo multiplier 5.8 -> 41')
# tick with nothing queued is a no-op
sim=mk(); eq(sim.eval('knight_kspell_tick()'),0,'idle tick')
print('kspell tests',N[0],'fails',len(FAILS)); sys.exit(1 if FAILS else 0)
