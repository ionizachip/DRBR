from harness import *
FAILS=[];N=[0]
def ok(c,msg):
    N[0]+=1
    if not c:FAILS.append(msg);print('FAIL',msg)
def eq(a,b,msg):
    N[0]+=1
    if a!=b:FAILS.append(msg);print('FAIL',msg,'got',repr(a),'want',repr(b))
sim=make_sim()
def E(x):return sim.eval(x)
def R(x):sim.run(x)
R('global.t=knight_cfg_default();')
# defaults valid
eq(E('knight_resolve(global.t).ok'),True,'default resolves')
# random knight never cyan
R('global.cy=knight_find_key("cyan"); global.tc=0; for(var i=0;i<400;i++){var c=knight_cfg_default(); var k=knight_random_knight(c); if(k==global.cy) global.tc++; if(k<0) global.tc+=1000;}')
eq(E('global.tc'),0,'random knight never cyan, never -1')
# rush list excludes cyan
R('global.rl=knight_rush_list(); global.hascy=0; for(var i=0;i<array_length(global.rl);i++) if(global.rl[i]==global.cy) global.hascy=1;')
eq(E('global.hascy'),0,'rush list excludes cyan')
eq(E('array_length(global.rl)'),5,'rush has 5')
# shuffled never includes cyan, permutation
R('global.bad=0; for(var i=0;i<100;i++){var l=knight_rush_order_shuffled(); if(array_length(l)!=5) global.bad++; for(var j=0;j<array_length(l);j++) if(l[j]==global.cy) global.bad++;}')
eq(E('global.bad'),0,'shuffle ok')
# elec with No TP is blocked (UNLEASH needs TP); elec no longer needs Kris
R('var c=knight_cfg_default(); c.knight=knight_find_key("elec"); c.party=[2,3,0]; global.r0=knight_resolve(c);')
eq(E('global.r0.ok'),True,'elec without kris now allowed')
R('var c=knight_cfg_default(); c.knight=knight_find_key("elec"); c.party=[1,2,3]; c.c_notp=1; global.r=knight_resolve(c);')
eq(E('global.r.ok'),False,'elec with no-tp blocked')
ok(E('is_struct(global.r.fixcfg)'),'elec fix suggested')
R('global.f=global.r.fixcfg; global.r2=knight_resolve(global.f);')
eq(E('global.r2.ok'),True,'suggested fix launches')
# solo kris elec ok
R('var c=knight_cfg_default(); c.knight=knight_find_key("elec"); c.party=[1,0,0]; c.c_solo=1; global.r=knight_resolve(c);')
eq(E('global.r.ok'),True,'solo kris elec ok')
# solo with 3 members errors
R('var c=knight_cfg_default(); c.c_solo=1; global.r=knight_resolve(c);')
eq(E('global.r.ok'),False,'solo w/3 blocked')
# solo susie, base ok; noelle slot
R('var c=knight_cfg_default(); c.c_solo=1; c.party=[2,0,0]; global.r=knight_resolve(c);')
eq(E('global.r.ok'),True,'solo susie ok')
R('var c=knight_cfg_default(); c.party=[1,2,4]; global.r=knight_resolve(c);')
eq(E('global.r.ok'),True,'kris susie noelle ok')
# duplicates
R('var c=knight_cfg_default(); c.party=[1,1,1]; global.r=knight_resolve(c);')
eq(E('global.r.ok'),True,'dupes ok')
# empty
R('var c=knight_cfg_default(); c.party=[0,0,0]; global.r=knight_resolve(c);')
eq(E('global.r.ok'),False,'empty blocked')
# gap closes with visible correction
R('var c=knight_cfg_default(); c.party=[0,2,0]; global.r=knight_resolve(c);')
eq(E('global.r.ok'),True,'gap ok'); eq(E('array_length(global.r.corr)>0'),True,'gap correction visible')
eq(E('global.r.cfg.party[0]'),2,'gap compacted')
# weird auto-off
R('var c=knight_cfg_default(); c.weird=1; c.party=[2,3,4]; global.r=knight_resolve(c);')
eq(E('global.r.cfg.weird'),1,'weird stays on without Kris (build 37: any party)')
R('var c=knight_cfg_default(); c.weird=1; c.party=[1,2,4]; global.r=knight_resolve(c);')
eq(E('global.r.cfg.weird'),1,'weird kept with Kris+Noelle')
R('var c=knight_cfg_default(); c.weird=1; c.party=[1,1,1]; global.r=knight_resolve(c);')
eq(E('global.r.cfg.weird'),1,'weird kept with Kris clones')
R('var c=knight_cfg_default(); c.weird=1; global.r=knight_resolve(c);')
eq(E('global.r.cfg.weird'),1,'weird kept with trio')
# practice
R('var c=knight_cfg_default(); c.practice=1; global.r=knight_resolve(c);')
eq(E('global.r.cfg.practice'),1,'practice kept on base (every knight has practice now)')
R('var c=knight_cfg_default(); c.practice=1; c.knight=5; global.r=knight_resolve(c);')
eq(E('global.r.cfg.practice'),1,'practice kept on cyan')
R('var c=knight_cfg_default(); c.practice=1; c.mode=1; global.r=knight_resolve(c);')
eq(E('global.r.cfg.practice'),0,'practice off in rush')
R('var c=knight_cfg_default(); c.practice=1; c.knight=knight_find_key("kaizo"); global.r=knight_resolve(c);')
eq(E('global.r.cfg.practice'),1,'practice kept kaizo')
R('var c=knight_cfg_default(); c.practice=1; c.mode=1; global.r=knight_resolve(c);')
eq(E('global.r.cfg.practice'),0,'practice off in rush'); eq(E('array_length(global.r.plan)'),5,'rush plan')
# nohit
R('var c=knight_cfg_default(); c.c_nohit=1; c.knight=knight_find_key("cyan"); global.r=knight_resolve(c);')
eq(E('global.r.ok'),False,'nohit cyan blocked')
R('var c=knight_cfg_default(); c.c_nohit=1; c.practice=1; c.knight=knight_find_key("kaizo"); global.r=knight_resolve(c);')
eq(E('global.r.ok'),False,'nohit+practice blocked'); ok(E('is_struct(global.r.fixcfg)'),'fix offered')
# random challenge never solo with 3, never nohit on cyan
R('global.bad=0; for(var i=0;i<300;i++){var c=knight_cfg_default(); c.knight=global.cy; var f=knight_random_challenge(c,[global.cy]); if(f=="c_solo"||f=="c_nohit"||f=="") global.bad++;}')
eq(E('global.bad'),0,'random challenge compat on cyan trio')
R('var c=knight_cfg_default(); c.mode=0; c.random=1; c.randchal=1; global.ok_r=0; global.nb=0; for(var i=0;i<200;i++){var r=knight_resolve(c); if(r.ok){global.ok_r++; if(r.plan[0]==global.cy) global.nb++;} else global.nb+=1000;}')
eq(E('global.nb'),0,'random resolve valid, never cyan')
# random knight with party w/o kris never elec
R('var c=knight_cfg_default(); c.party=[2,3,0]; c.c_notp=1; global.bad=0; for(var i=0;i<200;i++){var k=knight_random_knight(c); if(k==knight_find_key("elec")||k<0) global.bad++;}')
eq(E('global.bad'),0,'random respects no-tp')
# sanitize garbage
R('var c=knight_cfg_default(); c.knight=99; c.song=-4; c.party=[7,2.5,"a"]; c.rush_pct=33; c.rush_heal=9; c.mode=5; var cr=knight_cfg_sanitize(c); global.c=c; global.cr=cr;')
eq(E('global.c.knight'),0,'bad knight');eq(E('global.c.song'),0,'bad song');eq(E('global.c.mode'),0,'bad mode')
eq(E('global.c.rush_pct'),30,'pct rounded');eq(E('global.c.rush_heal'),0,'heal range')
eq(E('global.c.party[0]+global.c.party[1]+global.c.party[2]'),0,'garbage party emptied')
# challenge combos: all valid combos on every non-joke knight with trio
R('global.bad=0; for(var k=0;k<knight_count();k++){ for(var m=0;m<8;m++){var c=knight_cfg_default(); c.knight=k; c.c_items=m&1; c.c_heal=(m>>1)&1; c.c_hp1=(m>>2)&1; var r=knight_resolve(c); if(!r.ok) global.bad++;}}')
eq(E('global.bad'),0,'all item/heal/hp1 combos valid')
# music: missing file indicator
eq(E('knight_music_exists("definitely_missing.ogg")'),False,'missing music false')
# brief text
ok(len(str(E('knight_cfg_brief(knight_cfg_default())')))>5,'brief text')
# party compact etc
eq(E('knight_party_is_trio([1,2,3])'),True,'trio');eq(E('knight_party_is_trio([3,2,1])'),True,'trio any order');eq(E('knight_party_is_trio([1,1,2])'),False,'not trio')
print('rules tests: %d checks, %d failures'%(N[0],len(FAILS)))
