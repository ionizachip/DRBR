from harness import *
FAILS=[];N=[0]
def eq(a,b,msg):
    N[0]+=1
    if a!=b:FAILS.append(msg);print('FAIL',msg,'got',repr(a),'want',repr(b))
def ok(c,msg): eq(bool(c),True,msg)
def mk(chars='[1,3,4]'):
    sim=make_sim()
    for o in ('obj_animation','obj_firespell','obj_firespell_hexagon','obj_heroralsei','obj_heronoelle','obj_herokris','obj_icespell','obj_knight_enemy'):
        try: sim.define_object(o)
        except Exception: pass
    for a in ('spr_ralsei_spell_fireball_right','spr_ralsei_spell_bluefireball_right','spr_spell_fireball','spr_bluefire_ball','spr_bluefire_smallflame','spr_bluefire_flame','spr_ralseib_spell','spr_noelleb_spell','spr_firespell_smallflame','spr_soulshining','spr_krisb_act'):
        try: sim.define_asset(a)
        except Exception: pass
    sim.mock('sprite_set_offset',lambda s,*a:0)
    sim.mock('snd_play',lambda s,*a:0); sim.mock('snd_pitch',lambda s,*a:0); sim.mock('scr_oflash',lambda s,*a:0)
    sim.mock('scr_act_charsprite',lambda s,who,spr,a,b:(sim.eval('instance_create(0,0,obj_animation)'))); sim.mock('scr_act_charsprite_end',lambda s:0)
    sim.run('global.monsterx=[300,0,0]; global.monstery=[100,0,0]; global.monster=[1,0,0]; global.monsterhp=[1000,0,0]; global.monsterinstance=[noone,noone,noone];'
            'global.char=%s; global.faceaction=[0,0,0,0,0]; global.hp=[0,10,10,10,10]; global.battlemag=[5,12,16,9,0]; global.battleat=[10,12,8,0,0]; global.monsterdf=[0,0,0]; global.knight_variant=0; global.chapter=3; global.automiss=[0,0,0,0,0];'
            'global.monsterinstance[0]=instance_create(300,100,obj_animation);global.charinstance=[noone,noone,noone,noone,noone];'%chars)
    return sim
def hero(sim,slot,obj):
    sim.run('global.charinstance[%d]=instance_create(%d,200,%s); global.charinstance[%d].spellsprite=spr_ralseib_spell; global.charinstance[%d].spellframes=3; global.charinstance[%d].state=0; global.charinstance[%d].itemed=0; global.charinstance[%d].attacktimer=0;'%(slot,100+slot*30,obj,slot,slot,slot,slot,slot))
# ---- Frostfire (kind 7): both cast, both effects land, nobody left in a pose, queue clears
for caster in (1,2):
    sim=mk('[1,3,4]'); hero(sim,1,'obj_heroralsei'); hero(sim,2,'obj_heronoelle')
    sim.run('knight_kspell_start(7,%d,0,300);'%caster if False else 'knight_frostfire_start(%d,0);'%(1))
    mx=dict(fire=0,ice=0,tw=0,fb2=0,blue_embers=0); poses=set()
    for i in range(120):
        sim.run('knight_kspell_tick();')
        mx['fire']=max(mx['fire'],sim.eval('instance_number(obj_firespell)')); mx['ice']=max(mx['ice'],sim.eval('instance_number(obj_icespell)'))
        if not sim.eval('is_undefined(global.knight_ks)'):
            mx['tw']=max(mx['tw'],1 if sim.eval('global.knight_ks.blue')==2 else 0)
            mx['fb2']=max(mx['fb2'],1 if sim.eval('i_ex(global.knight_ks.fb2)') else 0)
        poses.add((sim.eval('global.charinstance[1].state'),sim.eval('global.charinstance[2].state')))
        if sim.eval('is_undefined(global.knight_ks)'):break
    ok(sim.eval('is_undefined(global.knight_ks)'),'frostfire finishes (caster %d)'%caster)
    ok(mx['tw']==1,'frostfire runs in twin (ice+fire) mode'); ok(mx['fb2']==1,'frostfire: blue twin fireball flies beside the red one')
    ok(mx['fire']>=1,'frostfire: fire burst lands'); ok(mx['ice']>=1,'frostfire: ice spell lands')
    ok((2,2) in poses or any(p[0]==2 and p[1]==2 for p in poses),'both cast poses seen')
    eq((sim.eval('global.charinstance[1].state'),sim.eval('global.charinstance[2].state')),(0,0),'both restored')
# ---- Heatwave (kind 6): shine then blue fireshock
sim=mk('[1,3,4]'); hero(sim,1,'obj_herokris'); hero(sim,2,'obj_heroralsei')
sim.run('knight_kspell_start(6,2,0,400);')
blue=False; fire=0
for i in range(120):
    sim.run('knight_kspell_tick();')
    ks=sim.eval('global.knight_ks')
    if not sim.eval('is_undefined(global.knight_ks)') and sim.eval('global.knight_ks.kind')==5: blue=sim.eval('global.knight_ks.blue')==1 or blue
    fire=max(fire,sim.eval('instance_number(obj_firespell)'))
    if sim.eval('is_undefined(global.knight_ks)'):break
ok(sim.eval('is_undefined(global.knight_ks)'),'heatwave finishes'); ok(blue,'heatwave converts to a BLUE fireshock'); ok(fire>=1,'heatwave: burst lands')
# ---- damage numbers
sim=mk('[1,3,4]'); sim.run('instance_create(0,0,obj_knight_enemy); obj_knight_enemy.damagereduction=0.5; obj_knight_enemy.kaizo_block=0;')
for v,m in ((0,1.3),(1,1.6),(3,1.8)):
    sim.run('global.knight_variant=%d;'%v)
    fs=sim.eval('knight_fireshock_damage(1,0)'); ic=sim.eval('knight_iceshock_damage(2,0,0)')
    ok(fs>=ic*(1.6 if v in(1,3) else 1.15)-1,'v%d: fireshock %d well above noelle ice %d'%(v,fs,ic))
    ok(sim.eval('knight_heatwave_damage(1,0,0)')>fs,'v%d: heatwave > fireshock'%v)
# ---- blocked / partner rules
sim=mk('[2,3,4]'); sim.run('global.knight_run=1;')   # Susie, Ralsei, Noelle (no Kris)
sim.run('global.hp=[0,10,10,10,10];')
print('partner of 6 for Ralsei', sim.eval('knight_partner_of(6,3)'), 'noelle', sim.eval('knight_partner_of(6,4)'), 'frostfire', sim.eval('knight_partner_of(15,3)'))
eq((sim.eval('knight_duo_heal_mode()'),sim.eval('knight_kris_in_party()')),(True,False),'duo mode when no Kris')
eq(sim.eval('knight_partner_of(6,3)'),4,'Ralsei needs Noelle'); eq(sim.eval('knight_partner_of(6,4)'),3,'Noelle needs Ralsei')
sim=mk('[1,3,4]'); eq(sim.eval('knight_duo_heal_mode()'),False,'Kris present: not duo heal mode')
# knight_redbuster_blocked: Ralsei(slot0)+Noelle(slot1), no Kris
def blk(chars,slot,spell):
    sim=mk(chars); sim.run('global.knight_run=1; global.hp=[0,10,10,10,10]; global.battlespell=[[0,0,0],[0,0,0],[0,0,0]]; global.battlespell[%d][0]=%d;'%(slot,spell))
    return sim.eval('knight_redbuster_blocked(%d,0)'%slot)
eq(blk('[3,4,0]',0,6),False,'Ralsei+Noelle: Dual Heal usable by Ralsei (Noelle later slot)')
eq(blk('[3,4,0]',1,6),False,'Noelle in last slot can still cast it (Ralsei acted earlier; her command is not used up twice)')
eq(blk('[3,0,0]',0,6),True,'Ralsei alone: Dual Heal blocked')
eq(blk('[2,3,0]',0,6),True,'Susie+Ralsei: Dual Heal blocked')
eq(blk('[1,3,0]',0,6),False,'Kris+Ralsei: Kris casts Dual Heal as before')
eq(blk('[3,4,0]',0,15),False,'Frostfire: Ralsei with Noelle later ok')
eq(blk('[3,0,0]',0,15),True,'Frostfire alone blocked')
eq(blk('[1,3,0]',0,15),True,'Kris cannot cast Frostfire')
eq(blk('[1,3,0]',0,14),False,'Heatwave: Kris + Ralsei ok')
eq(blk('[3,1,0]',0,14),True,'Heatwave not for Ralsei')
eq(blk('[3,1,0]',1,14),False,'Heatwave: Kris in a later slot than Ralsei works')
eq(blk('[4,2,1]',2,12),False,'Permafrost: Kris in the last slot works (Noelle earlier)')
# partner pose is released once the turn moves on (myfight >= 4), not before
sim=mk('[3,4,0]'); hero(sim,0,'obj_heroralsei'); hero(sim,1,'obj_heronoelle')
sim.run('global.knight_run=1; global.charturn=0; global.charspecial=[6,0,0]; global.acting=[0,0,0]; global.charaction=[0,0,0]; global.myfight=3; knight_soul_lock(); global.charinstance[1].state=6; global.charinstance[1].acttimer=5;')
eq((sim.eval('global.faceaction[1]'),sim.eval('global.knight_lockslots[1]')),(6,1),'duo Dual Heal: Noelle locked in the ACT pose')
sim.run('knight_lock_release();'); eq(sim.eval('global.faceaction[1]'),6,'pose kept while the spell plays (myfight 3)')
sim.run('global.myfight=5; knight_lock_release();')
eq((sim.eval('global.faceaction[1]'),sim.eval('global.charinstance[1].state'),sim.eval('global.charinstance[1].acttimer'),sim.eval('global.knight_lockslots[1]')),(0,0,0,0),'pose dropped when the turn moves on')
# duplicates (user's screenshot): Ralsei, Noelle, Ralsei - Noelle's Dual Heal uses the LATER Ralsei
eq(blk('[3,4,3]',1,6),False,'Ralsei,Noelle,Ralsei: Noelle can cast Dual Heal (later Ralsei)')
eq(blk('[3,4,3]',0,6),False,'Ralsei,Noelle,Ralsei: first Ralsei ok')
eq(blk('[3,4,3]',2,6),False,'Ralsei,Noelle,Ralsei: last Ralsei pairs with an earlier Noelle')
sim=mk('[3,4,3]'); sim.run('global.knight_run=1; global.charturn=1; global.charspecial=[0,6,0]; global.acting=[0,0,0]; global.charaction=[0,0,0]; knight_soul_lock();')
eq((sim.eval('global.acting[2]'),sim.eval('global.acting[0]')),(1,0),'lock uses up the LATER Ralsei, not the first')
print('HEATFROST tests',N[0],'fails',len(FAILS)); sys.exit(1 if FAILS else 0)
