from harness import *
import os,shutil
FAILS=[];N=[0]
def ok(c,msg):
    N[0]+=1
    if not c:FAILS.append(msg);print('FAIL',msg)
def eq(a,b,msg):
    N[0]+=1
    if a!=b:FAILS.append(msg);print('FAIL',msg,'got',repr(a),'want',repr(b))
def rec(sim,key,cat):
    return sim.py(sim.eval('knight_rec_get("%s","%s")'%(key,cat)))
def fresh():
    sim=make_sim()
    sim.run('knight_store_load();')
    return sim
def sb(sim,name):return os.path.join(sim.sandbox,name)

# ---- 1. fresh start, save, reload ----
sim=fresh()
eq(sim.eval('global.knight_store_status'),'new','fresh store status new')
eq(rec(sim,'base','st')['att'],0,'blank record')
sim.run('var r = knight_rec_get("base","st"); r.att = 7; r.win = 3; r.best = 1234; r.lowdmg = 55; r.streak = 2; r.cur = 1; r.cfg = "K S R";')
ok(sim.eval('knight_store_save()'),'save ok')
ok(os.path.exists(sb(sim,'knight_hub.ini')),'file exists')
sim2=make_sim(); 
# copy file into the new sim's sandbox
shutil.copy(sb(sim,'knight_hub.ini'),sb(sim2,'knight_hub.ini'))
sim2.run('knight_store_load();')
eq(sim2.eval('global.knight_store_status'),'ok','reload status ok')
r=rec(sim2,'base','st')
eq((r['att'],r['win'],r['best'],r['lowdmg'],r['streak'],r['cur'],r['cfg']),(7,3,1234,55,2,1,'K S R'),'record round trip')

# ---- 2. backup on second save ----
sim.run('knight_rec_get("base","st").att = 8;')
ok(sim.eval('knight_store_save()'),'second save')
ok(os.path.exists(sb(sim,'knight_hub.bak')),'backup created')

# ---- 3. corrupt main -> recover from backup ----
data=open(sb(sim,'knight_hub.ini'),'rb').read()
sim3=make_sim()
shutil.copy(sb(sim,'knight_hub.bak'),sb(sim3,'knight_hub.bak'))
open(sb(sim3,'knight_hub.ini'),'wb').write(data[:len(data)//2])
sim3.run('knight_store_load();')
ok('backup' in sim3.eval('global.knight_store_status'),'recovered from backup: '+str(sim3.eval('global.knight_store_status')))
eq(rec(sim3,'base','st')['att'],7,'backup value (7) restored')
ok(os.path.exists(sb(sim3,'knight_hub.ini')),'main rewritten after recovery')
sim3b=make_sim(); shutil.copy(sb(sim3,'knight_hub.ini'),sb(sim3b,'knight_hub.ini')); sim3b.run('knight_store_load();')
eq(sim3b.eval('global.knight_store_status'),'ok','main valid again after recovery')

# ---- 4. both corrupt -> reset, bad copy kept ----
sim4=make_sim()
open(sb(sim4,'knight_hub.ini'),'wb').write(data[:50]); open(sb(sim4,'knight_hub.bak'),'wb').write(b'garbage')
sim4.run('knight_store_load();')
ok('damaged' in sim4.eval('global.knight_store_status'),'both corrupt -> reset message')
eq(rec(sim4,'base','st')['att'],0,'reset to blank')
ok(os.path.exists(sb(sim4,'knight_hub.bad')),'bad copy kept')
ok(sim4.eval('knight_store_save()'),'can save after reset')

# ---- 5. old schema ----
sim5=make_sim()
txt=data.decode().replace('schema=1.000000','schema=9.000000')
open(sb(sim5,'knight_hub.ini'),'w').write(txt)
sim5.run('knight_store_load();')
ok('unsupported version' in sim5.eval('global.knight_store_status'),'schema mismatch handled: '+sim5.eval('global.knight_store_status'))
ok(os.path.exists(sb(sim5,'knight_hub.old')),'old-schema file preserved')
eq(rec(sim5,'base','st')['att'],0,'old schema -> fresh')

# ---- 6. missing key / incomplete ----
sim6=make_sim()
txt=data.decode()
import re
txt2=re.sub(r'(?m)^done=.*\n','',txt)
open(sb(sim6,'knight_hub.ini'),'w').write(txt2)
sim6.run('knight_store_load();')
ok('damaged' in sim6.eval('global.knight_store_status'),'missing done flag -> treated as interrupted/damaged')

# ---- 7. tampered value caught by checksum ----
sim7=make_sim()
txt=data.decode().replace('att=8.000000','att=9.000000') if 'att=8.000000' in data.decode() else data.decode().replace('att=7.000000','att=9.000000')
open(sb(sim7,'knight_hub.ini'),'w').write(txt)
sim7.run('knight_store_load();')
ok('damaged' in sim7.eval('global.knight_store_status'),'checksum catches edits')

# ---- 8. interrupted write: file left truncated; next launch recovers from .bak ----
sim8=fresh()
sim8.run('knight_rec_get("kaizo","st").att = 4;'); ok(sim8.eval('knight_store_save()'),'save A')
sim8.run('knight_rec_get("kaizo","st").att = 5;')
sim8.inject_write_fault(Fault.interrupt(40),'knight_hub.ini')
try:
    sim8.run('knight_store_save();'); ok(False,'expected crash')
except BaseException as e:
    ok(type(e).__name__=='SimCrash','interrupted write raised SimCrash')
sim9=make_sim()
for f in ('knight_hub.ini','knight_hub.bak'):
    if os.path.exists(sb(sim8,f)): shutil.copy(sb(sim8,f),sb(sim9,f))
sim9.run('knight_store_load();')
ok(rec(sim9,'kaizo','st')['att'] in (4,5),'interrupted write: older or newer value, never garbage')
eq(rec(sim9,'kaizo','st')['att'],4,'interrupted write -> last good (4)')

# ---- 9. failed write (IOError) leaves memory but reports failure, restores file ----
sim10=fresh(); sim10.run('knight_rec_get("base","st").att = 1;'); ok(sim10.eval('knight_store_save()'),'save before fail')
sim10.run('knight_rec_get("base","st").att = 2;')
sim10.inject_write_fault(Fault.garbage(b'xxxx'),'knight_hub.ini')
res=sim10.eval('knight_store_save()')
ok(not res,'garbage write detected as failure')
ok(sim10.eval('global.knight_save_fail'),'save_fail flag raised')
sim11=make_sim(); shutil.copy(sb(sim10,'knight_hub.ini'),sb(sim11,'knight_hub.ini')); sim11.run('knight_store_load();')
eq(rec(sim11,'base','st')['att'],1,'file restored to last good after failed write')
ok(sim10.eval('knight_store_save()'),'next save succeeds again')

# ---- spell + equipment set persists across game restarts ('last' section) ----
sim=fresh()
sim.run('global.knight_orig = {}; global.charweapon=[0,0,0,0,0]; global.chararmor1=[0,0,0,0,0]; global.chararmor2=[0,0,0,0,0];'
        'for (var _c=0;_c<=4;_c++){ for (var _i=0;_i<12;_i++) global.spell[_c][_i]=0; } global.spell[1][0]=7; global.spell[1][1]=5; global.spell[1][2]=6; global.spell[3][0]=9; global.spell[4][5]=11;'
        'global.charweapon[1]=3; global.chararmor1[2]=4;')
ok(sim.eval('knight_store_save()'),'save with loadout')
sim2=make_sim(); shutil.copy(sb(sim,'knight_hub.ini'),sb(sim2,'knight_hub.ini'))
sim2.run('knight_store_load();')
eq(sim2.eval('string_length(global.knight_last_spells)'),48,'spell set stored (48 chars)')
eq(sim2.eval('string_copy(global.knight_last_spells,1,3)'),'756','Kris row 7,5,6 round trips')
eq(sim2.eval('string_char_at(global.knight_last_equip,1)'),'3','equip string loaded (Kris weapon 3)'); eq(sim2.eval('string_length(global.knight_last_equip)'),12,'equip 12 chars')
# apply as the menu does on open
sim2.run('for (var _c=0;_c<=4;_c++){ for (var _i=0;_i<12;_i++) global.spell[_c][_i]=0; }')
sim2.run('knight_spells_from_string(global.knight_last_spells);')
eq((sim2.eval('global.spell[1][0]'),sim2.eval('global.spell[1][1]'),sim2.eval('global.spell[1][2]'),sim2.eval('global.spell[3][0]'),sim2.eval('global.spell[4][5]')),(7,5,6,9,11),'spells restored exactly (incl. Ralsei + Noelle)')
# damaged values are ignored, not trusted
txt=open(sb(sim,'knight_hub.ini')).read().replace('spells=','spells=XX')
open(sb(sim2,'knight_hub.ini'),'w').write(txt)
sim3=make_sim(); open(sb(sim3,'knight_hub.ini'),'w').write(txt); sim3.run('knight_store_load();')
eq(sim3.eval('global.knight_last_spells'),'','wrong-length spell string ignored')
print('store tests:',N[0],'checks,',len(FAILS),'failures')
