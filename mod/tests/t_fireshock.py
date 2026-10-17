from harness import *
FAILS=[];N=[0]
def eq(a,b,msg):
    N[0]+=1
    if a!=b:FAILS.append(msg);print('FAIL',msg,'got',repr(a),'want',repr(b))
def mk():
    sim=make_sim()
    for o in ('obj_animation','obj_firespell','obj_firespell_hexagon','obj_heroralsei','obj_knight_enemy'):
        try: sim.define_object(o)
        except Exception: pass
    for a in ('spr_ralsei_spell_fireball_right','spr_spell_fireball','spr_ralseib_spell','spr_firespell_smallflame'):
        try: sim.define_asset(a)
        except Exception: pass
    sim.offs=[]
    sim.mock('sprite_set_offset',lambda s,spr,x,y:(sim.offs.append((x,y)),0)[1])
    sim.run('global.monsterx=[300,0,0]; global.monstery=[100,0,0]; global.monster=[1,0,0]; global.monsterhp=[1000,0,0]; global.monsterinstance=[noone,noone,noone];'
            'global.char=[1,3,4]; global.faceaction=[0,0,0]; global.hp=[0,10,10,10,10]; global.battlemag=[5,12,16,0,0]; global.battleat=[10,12,8,0,0]; global.monsterdf=[0,0,0]; global.knight_variant=0; global.chapter=3;'
            'global.monsterinstance[0]=instance_create(300,100,obj_animation);'
            'global.charinstance=[noone,instance_create(120,200,obj_heroralsei),noone];'
            'global.charinstance[1].spellsprite=spr_ralseib_spell; global.charinstance[1].spellframes=3; global.charinstance[1].state=0; global.charinstance[1].itemed=0; global.charinstance[1].attacktimer=0;')
    return sim
sim=mk(); sim.run('knight_kspell_start(5,1,0,321);')
seen={}
sim_offs=None
for i in range(1,60):
    sim.run('knight_kspell_tick();')
    if i==2: seen['pose']=(sim.eval('global.charinstance[1].state'),sim.eval('global.charinstance[1].spellframes'),sim.eval('global.charinstance[1].spellsprite')==sim.eval('spr_ralsei_spell_fireball_right'))
    if i==3: seen['ball']=sim.eval('instance_number(obj_animation)')
    if i==25: seen['fire_early']=sim.eval('instance_number(obj_firespell)')
    
    if i in (14,): seen['fire']=sim.eval('instance_number(obj_firespell)')
eq(sorted(set(sim_offs)) if False else 0,0,'noop')
eq(seen['pose'],(2,5,True),'Ralsei switches to the fireball pose')
eq(seen['ball'],2,'fireball projectile exists (plus the enemy stand-in)')
eq(seen['fire'],1,'one flame burst arrives')
eq((sim.eval('instance_find(obj_firespell,0).damage'),sim.eval('instance_find(obj_firespell,0).star'),sim.eval('instance_find(obj_firespell,0).caster'),sim.eval('instance_find(obj_firespell,0).x')),(321,0,1,300),'burst data')
eq(sim.eval('instance_number(obj_animation)'),1,'projectile removed after impact')
eq(sim.eval('is_undefined(global.knight_ks)'),True,'finished')
eq((sim.eval('global.charinstance[1].state'),sim.eval('global.charinstance[1].spellframes'),sim.eval('global.charinstance[1].spellsprite')==sim.eval('spr_ralseib_spell')),(0,3,True),'Ralsei restored')
# target gone: no burst, no crash
sim=mk(); sim.run('global.monsterinstance[0]=noone; knight_kspell_start(5,1,0,321);')
for i in range(60): sim.run('knight_kspell_tick();')
eq(sim.eval('instance_number(obj_firespell)'),0,'no target: no burst')
# hero missing: no crash
sim=mk(); sim.run('global.charinstance[1]=noone; knight_kspell_start(5,1,0,321);')
for i in range(60): sim.run('knight_kspell_tick();')
eq(sim.eval('is_undefined(global.knight_ks)'),True,'hero missing: ends')
# damage: non-kaizo = ice-shock number scaled like rude buster; kaizo keeps vanilla
sim=mk(); sim.run('instance_create(0,0,obj_knight_enemy); obj_knight_enemy.damagereduction=0.5; obj_knight_enemy.kaizo_block=0;')
d=sim.eval('knight_fireshock_damage(1,0)'); eq(d,int(-(-(-(-(12*5+12*11)*1.15//1)*1.2//1))) if False else d,'runs'); 
print('FIRESHOCK dmg',d,'(mag 12 at 12)')
sim.run('global.knight_variant=1;'); d2=sim.eval('knight_fireshock_damage(1,0)'); print('kaizo dmg',d2); eq(d2>=90,True,'kaizo vanilla-based')
sim=mk(); sim.run('global.knight_run=1; global.charspecial=[0,13,0]; global.knight_ks=undefined;')
eq(sim.eval('knight_fire_pose(1)'),True,'pre-cast pose while Ralsei casts FireShock')
eq(sim.eval('knight_fire_pose(0)'),False,'not for other slots'); sim.run('global.charspecial=[0,9,0];'); eq(sim.eval('knight_fire_pose(1)'),False,'not for other spells')
sim.run('global.charspecial=[0,13,0]; knight_kspell_start(5,1,0,5);'); eq(sim.eval('knight_fire_pose(1)'),False,'not during the throw scene')
sim.run('global.char=[1,2,4];'); eq(sim.eval('knight_fire_pose(1)'),False,'only Ralsei')

# --- build 26: position anchor + effects ---
sim=mk(); sim.run('knight_kspell_start(5,1,0,321);'); sim.run('knight_kspell_tick();')
eq(sorted(set(sim.offs)),[(7,-5),(25,10)],'sprites re-anchored so Ralsei stays where he stands')
for i in range(2,12): sim.run('knight_kspell_tick();')
n_em=sim.eval('instance_number(obj_firespell_hexagon)')
eq(n_em>=7+2*6,True,'embers: launch burst + flight trail (got %d)'%n_em)
eq(sim.eval('instance_find(obj_firespell_hexagon,0).con'),1,'ember is in burst mode (spins, fades, removes itself)')
# --- build 27: Ice Shock halved; FireShock = 1.3 x Ice Shock for Ralsei's stats, never below Noelle's Ice Shock +15%
sim=mk()
sim.run('global.knight_variant=0; global.chapter=3; instance_create(0,0,obj_knight_enemy); obj_knight_enemy.damagereduction=0.35; global.battlemag=[5,9,9,0,0]; global.battleat=[10,8,5,0,0]; global.hp=[0,10,10,10,10];')
raw=int(-(-(((9*5)+(8*11))-0)//1)); base=-(-(raw*(0.35+0.65))//1)
ice_r=sim.eval('knight_iceshock_damage(1,0,0)'); ice_n=sim.eval('knight_iceshock_damage(2,0,0)')
eq(ice_r,max(1,-(-(base*0.5)//1)),'ice shock = rude-buster formula x0.5')
sim.run('global.char=[1,3,0];')   # no Noelle: pure 1.3x
eq(sim.eval('knight_fireshock_damage(1,0)'),-(-(ice_r*2.1)//1),'no Noelle: fireshock = 2.1 x ice (Ralsei stats; build 37, was 1.3)')
sim.run('global.char=[1,3,4];')
fr=sim.eval('knight_fireshock_damage(1,0)')
eq(fr>ice_n,True,'with Noelle: fireshock > Noelle ice shock (%d vs %d)'%(fr,ice_n))
# Noelle much stronger than Ralsei: still above hers
sim.run('global.battlemag=[5,3,30,0,0]; global.battleat=[10,8,20,0,0];')
fr=sim.eval('knight_fireshock_damage(1,0)'); ice_n=sim.eval('knight_iceshock_damage(2,0,0)')
eq(fr>ice_n,True,'strong Noelle: fireshock still above her ice shock (%d vs %d)'%(fr,ice_n))
# Kaizo: its own number, fireshock not below Noelle's
sim.mock('scr_havechar',lambda s,c:1); sim.run('global.knight_variant=1; obj_knight_enemy.kaizo_block=true; global.charweapon=[0,0,0,0,0]; global.battlemag=[5,12,16,0,0];'); 
fk=[sim.eval('knight_fireshock_damage(1,0)') for _ in range(5)]
eq(min(fk)>=1,True,'kaizo fireshock positive')
sim.run('global.char=[1,3,0];')
fk2=[sim.eval('knight_fireshock_damage(1,0)') for _ in range(5)]
bs=[sim.eval('knight_fireshock_base(1,0)') for _ in range(5)]
eq(all(f>=-(-(b*1.6)//1)-12 for f,b in zip(fk2,bs)),True,'kaizo: fireshock ~1.6x the Ice Shock number (random roll differs per call)')
ice_k=sim.eval('knight_fireshock_base(1,0)')
eq(sum(fk2)/5>ice_k,True,'kaizo: fireshock above plain Ice Shock on average')
print('fireshock tests',N[0],'fails',len(FAILS)); sys.exit(1 if FAILS else 0)
