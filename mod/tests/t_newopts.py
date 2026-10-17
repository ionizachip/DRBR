from harness import *
import os,shutil,re
FAILS=[];N=[0]
def eq(a,b,msg):
    N[0]+=1
    if a!=b:FAILS.append(msg);print('FAIL',msg,'got',repr(a),'want',repr(b))
sim=make_sim(); sim.run('knight_store_load();')
sim.run('var c=global.knight_cfg; c.c_dmg2=1; c.c_halfhp=1; c.c_notp=1; c.c_onelife=1; c.rparty=1;')
sim.run('knight_preset_save(1,"NEW");knight_store_save();')
s2=make_sim(); shutil.copy(os.path.join(sim.sandbox,'knight_hub.ini'),os.path.join(s2.sandbox,'knight_hub.ini')); s2.run('knight_store_load();')
eq(s2.eval('global.knight_store_status'),'ok','reload ok')
for f in ['c_dmg2','c_halfhp','c_notp','c_onelife','rparty']:
    eq(s2.eval('global.knight_cfg.%s'%f),1,'last-config persisted '+f)
    eq(s2.eval('global.knight_presets[1].%s'%f),1,'preset persisted '+f)
# old file without the new keys still loads, new fields default 0
ini=open(os.path.join(sim.sandbox,'knight_hub.ini')).read()
old=re.sub(r'^(c_dmg2|c_halfhp|c_notp|c_onelife|rparty)=.*\n','',ini,flags=re.M)
s3=make_sim(); open(os.path.join(s3.sandbox,'knight_hub.ini'),'w').write(old); s3.run('knight_store_load();')
eq(s3.eval('global.knight_store_status'),'ok','old-format file loads')
eq(s3.eval('global.knight_cfg.c_dmg2'),0,'old file -> default 0')
eq(s3.eval('global.knight_presets[1].c_dmg2'),0,'old preset -> default 0')
# damage doubling + resolve keeps rparty
s4=make_sim(); s4.run('knight_store_load();')
s4.run('global.knight_run=1; global.krun={cfg:{c_dmg2:1}}; global.char=[1,2,3]; global.maxhp=[0,90,90,90,90];')
print('scale',s4.eval('knight_scale_taken(10,0)'))
s4.run('global.krun.cfg.c_dmg2=0;'); eq(s4.eval('knight_scale_taken(10,0)'),10,'no dmg2 unchanged')
print('newopts tests: %d checks, %d failures'%(N[0],len(FAILS))); sys.exit(1 if FAILS else 0)
