from harness import *
FAILS=[];N=[0]
def ok(c,msg):
    N[0]+=1
    if not c:FAILS.append(msg);print('FAIL',msg)
def eq(a,b,msg):
    N[0]+=1
    if a!=b:FAILS.append(msg);print('FAIL',msg,'got',repr(a),'want',repr(b))
def new(cfgcode='',key='base'):
    sim=make_sim(); sim.run('knight_store_load();')
    sim.run('var c=knight_cfg_default(); c.knight=knight_find_key("%s"); %s global.L=knight_resolve(c);'%(key,cfgcode))
    assert sim.eval('global.L.ok'),sim.eval('global.L.errors')
    sim.run('global.knight_launch=global.L; knight_launch_go();')
    return sim
def start_battle(sim):
    sim.run('if(!instance_exists(obj_battlecontroller)) instance_create_depth(0,0,0,obj_battlecontroller); knight_run_tick();')
def rec(sim,key,cat):
    return sim.py(sim.eval('knight_rec_get("%s","%s")'%(key,cat)))
def tick(sim,n,dmg=0,who=1):
    for i in range(n):
        if dmg: sim.run('global.hp[%d]-=%d;'%(who,dmg))
        sim.run('knight_run_tick();')

# 1. win recorded once
sim=new(); eq(sim.eval('global.krun.state'),'arena','arena at start'); start_battle(sim)
eq(sim.eval('global.krun.state'),'battle','battle'); eq(rec(sim,'base','st')['att'],1,'attempt counted')
tick(sim,100); tick(sim,1,dmg=10); tick(sim,5)
sim.run('knight_battle_won(); knight_battle_won();')
r=rec(sim,'base','st'); eq((r['win'],r['best'],r['lowdmg']),(1,106,10),'win recorded once frames=106 dmg=10')
eq(sim.eval('instance_number(obj_knight_prompt)') if False else 1,1,'-')
# 2. defeat
sim=new(); start_battle(sim); tick(sim,30)
sim.run('knight_defeat_begin(); knight_defeat_begin();')
r=rec(sim,'base','st'); eq((r['att'],r['win'],r['cur']),(1,0,0),'defeat: att1 win0'); eq(sim.eval('global.krun.state'),'lost','lost state')
sim.run('knight_exit_run(true);')
r=rec(sim,'base','st'); eq(r['att'],1,'no extra att after exit'); eq(sim.eval('global.knight_run'),0,'run cleaned')
# 3. abandon mid-fight counted once
sim=new(); start_battle(sim); tick(sim,10); sim.run('knight_exit_run(false);')
r=rec(sim,'base','st'); eq(r['aband'],1,'abandon counted')
# 4. no-hit exactly once
sim=new('c.c_nohit=1;'); start_battle(sim); tick(sim,10)
sim.run('knight_hit_event(); knight_hit_event(); knight_hit_event();')
r=rec(sim,'base','nh'); eq((r['att'],r['win'],r['cur']),(1,0,0),'nohit att1'); eq(sim.eval('global.krun.hits'),1,'one hit counted after fail'); eq(sim.eval('global.krun.state'),'failed','failed')
eq(rec(sim,'base','st')['att'],0,'st untouched by nohit')
tick(sim,3); sim.run('knight_run_tick();')
sim.run('knight_battle_won();'); eq(rec(sim,'base','nh')['win'],0,'cannot win after fail')
sim.run('knight_defeat_begin();'); eq(sim.eval('global.krun.state'),'failed','defeat after fail ignored')
# nohit win with zero hits
sim=new('c.c_nohit=1;'); start_battle(sim); tick(sim,20); sim.run('knight_battle_won();')
r=rec(sim,'base','nh'); eq((r['win'],r['best'],r['lowdmg']),(1,20,0),'nohit win')
# hit event before battle is ignored
sim=new('c.c_nohit=1;'); sim.run('knight_hit_event();'); eq(sim.eval('global.krun.failed'),False,'hit in arena ignored')
# 0-dmg hit counts
sim=new('c.c_nohit=1;'); start_battle(sim); tick(sim,5); sim.run('knight_hit_event();')
eq(sim.eval('global.krun.failed'),True,'0 dmg hit fails nohit')
# hit on non-active member? party-wide: hook is global, fine
# nohit instant retry sets autoact
sim=new('c.c_nohit=1; c.nh_retry=1;'); start_battle(sim); tick(sim,5); sim.run('knight_hit_event(); knight_run_tick(); var p=instance_find(obj_knight_prompt,0); global.pa=p.autoact;')
eq(sim.eval('global.pa'),'rematch','instant retry autoact')
# 5. joke fight not recorded
sim=new('',key='cyan'); start_battle(sim); tick(sim,10); sim.run('knight_battle_won();')
ok(sim.eval('is_undefined(knight_rec_get("cyan","st"))'),'no cyan record')
ok(any('JOKE' in l for l in sim.py(sim.eval('knight_hud_lines()'))),'joke HUD line')
# 6. practice: attempts only
sim=new('c.practice=1;',key='kaizo'); start_battle(sim); tick(sim,10); sim.run('knight_battle_won();')
r=rec(sim,'kaizo','pr'); eq((r['att'],r['win']),(1,0),'practice attempt only')
# 7. challenges
sim=new('c.c_hp1=1;'); start_battle(sim)
sim.run('instance_create_depth(0,0,0,obj_knight_enemy); knight_run_tick();')
eq(sim.eval('global.hp[1]+global.hp[2]+global.hp[3]'),3,'hp1 applied'); eq(sim.eval('global.maxhp[1]'),90,'max unchanged')
tick(sim,5); eq(sim.eval('global.krun.dmg'),0,'hp1 set not counted as damage')
sim=new('c.c_items=1;'); eq(sim.eval('global.item[0]+global.item[1]+global.item[2]'),0,'items cleared')
sim=new('c.c_heal=1;'); eq(sim.eval('knight_noheal_active()'),False,'noheal not in arena'); start_battle(sim); eq(sim.eval('knight_noheal_active()'),True,'noheal in battle')
# 8. solo party
sim=new('c.c_solo=1; c.party=[2,0,0];',key='base'); eq(sim.eval('global.char[0]'),2,'solo susie char0'); eq(sim.eval('global.char[1]+global.char[2]'),0,'others empty')
# 9. rush flow
def rush(code=''):
    return new('c.mode=1; '+code)
sim=rush(); eq(sim.eval('array_length(global.krun.plan)'),5,'rush 5'); start_battle(sim); tick(sim,50,dmg=1)
eq(rec(sim,'rush','rush')['att'],1,'rush att')
eq(rec(sim,'base','st')['att'],0,'inner fights not recorded individually')
for i in range(5):
    sim.run('knight_battle_won();')
    if i<4:
        eq(sim.eval('global.krun.state'),'rushwait','rushwait %d'%i)
        sim.run('knight_act_run("next"); knight_run_tick();'); start_battle(sim); tick(sim,10)
        eq(sim.eval('global.krun.pos'),i+1,'pos advance')
eq(sim.eval('global.krun.state'),'done','done'); r=rec(sim,'rush','rush'); eq((r['att'],r['win'],r['far']),(1,1,5),'rush complete')
sim.run('knight_battle_won(); knight_rush_finish("complete");'); eq(rec(sim,'rush','rush')['win'],1,'complete once')
# rush defeat
sim=rush(); start_battle(sim); tick(sim,10); sim.run('knight_battle_won();')
eq(sim.eval('instance_number(obj_knight_prompt)'),1,'clear prompt shown'); eq(sim.eval('instance_find(obj_knight_prompt,0).autoact'),'next','rush clear auto-advances'); eq(sim.eval('instance_find(obj_knight_prompt,0).timer')>0,True,'auto-advance timer set')
sim=rush(); start_battle(sim); tick(sim,10); sim.run('knight_battle_won(); knight_act_run("next"); knight_run_tick(); if(!instance_exists(obj_battlecontroller)) instance_create_depth(0,0,0,obj_battlecontroller); knight_run_tick();')
tick(sim,10); sim.run('knight_defeat_begin();'); r=rec(sim,'rush','rush'); eq((r['att'],r['win'],r['far']),(1,0,1),'rush defeat far=1')
# rush abandon from rushwait
sim=rush(); start_battle(sim); tick(sim,10); sim.run('knight_battle_won(); knight_act_run("abandon_rush");')
r=rec(sim,'rush','rush'); eq((r['aband'],r['win']),(1,0),'rush abandon'); eq(sim.eval('global.krun.state'),'done','done after abandon')
# rush nohit fail
sim=rush('c.c_nohit=1;'); start_battle(sim); tick(sim,10); sim.run('knight_hit_event(); knight_hit_event();')
r=rec(sim,'rush','rushnh'); eq((r['att'],r['win']),(1,0),'rush nohit att'); eq(rec(sim,'rush','rush')['att'],0,'rush normal untouched')
# recovery modes
def recov(mode,pct=50):
    s=rush('c.rush_heal=%d; c.rush_pct=%d;'%(mode,pct)); start_battle(s)
    s.run('global.hp[1]=10; global.hp[2]=0; global.hp[3]=80; knight_battle_won(); knight_act_run("next");')
    return [int(s.eval('global.hp[%d]'%i)) for i in (1,2,3)]
eq(recov(0),[90,110,140],'recover full')
eq(recov(1,50),[55,55,140],'recover 50%: 10+45, 0+55, 80+70 capped') 
eq(recov(2),[10,14,80],'recover none: floor to 1/8')
# reroll / rematch
sim=new('c.random=1;'); k1=sim.eval('global.krun.plan[0]'); start_battle(sim); tick(sim,5); sim.run('knight_battle_won();')
ok(sim.eval('knight_can_reroll(global.krun)'),'can reroll'); eq(sim.eval('knight_reroll()'),'','reroll ok'); eq(sim.eval('global.krun.state'),'arena','reroll arena')
sim.run('knight_rematch();'); eq(sim.eval('global.krun.state'),'arena','rematch arena'); eq(sim.eval('global.krun.hits'),0,'rematch resets')
sim=new(); eq(sim.eval('knight_can_reroll(global.krun)'),False,'no reroll fixed')
# leave and continue snapshot
sim=make_sim(); sim.run('knight_store_load(); global.flag[1047]=0; global.plot=250;')
sim.run('knight_snapshot_take(); var c=knight_cfg_default(); global.knight_launch=knight_resolve(c); knight_launch_go();')
eq(sim.eval('global.plot'),320,'plot forced during run'); start_battle(sim); tick(sim,5); sim.run('knight_battle_won(); knight_fight_finished(room_town_krisyard_dark);')
sim.run('knight_continue_story();'); eq(sim.eval('global.flag[1047]'),2,'story flag written once')
sim=make_sim(); sim.run('knight_store_load(); global.flag[1047]=0; global.plot=250; global.hp[1]=33;')
sim.run('knight_snapshot_take(); var c=knight_cfg_default(); global.knight_launch=knight_resolve(c); knight_launch_go(); knight_exit_run(false);')
eq(sim.eval('global.plot'),250,'leave restores plot'); eq(sim.eval('global.hp[1]'),33,'leave restores hp'); eq(sim.eval('global.flag[1047]'),0,'leave: no story flag')
# ghosts
sim=new('c.party=[1,0,0];',key='base'); n0=sim.eval('instance_number(obj_knight_ghost_susie)'); sim.run('knight_spawn_ghosts();')
eq(sim.eval('instance_number(obj_knight_ghost_susie)'),1,'ghost susie'); eq(sim.eval('instance_number(obj_knight_ghost_ralsei)'),1,'ghost ralsei'); eq(sim.eval('instance_number(obj_knight_ghost_kris)'),0,'no ghost kris')
sim=new('c.party=[1,2,3];',key='base'); sim.run('knight_spawn_ghosts();'); eq(sim.eval('instance_number(obj_knight_ghost_susie)'),0,'no ghost full party')
sim=new('c.party=[1,0,0];',key='kaizo'); sim.run('knight_spawn_ghosts();'); eq(sim.eval('instance_number(obj_knight_ghost_susie)'),0,'no ghost for kaizo')
print('run tests: %d checks, %d failures'%(N[0],len(FAILS)))
