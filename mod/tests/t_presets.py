from harness import *
import os,shutil
FAILS=[];N=[0]
def ok(c,msg):
    N[0]+=1
    if not c:FAILS.append(msg);print('FAIL',msg)
def eq(a,b,msg):
    N[0]+=1
    if a!=b:FAILS.append(msg);print('FAIL',msg,'got',repr(a),'want',repr(b))
sim=make_sim(); sim.run('knight_store_load();')
sim.run('global.knight_cfg.knight=knight_find_key("violet"); global.knight_cfg.party=[1,3,0]; global.knight_cfg.c_hp1=1; global.knight_cfg.rush_pct=70; global.spell[2][1]=5; global.spell[3][3]=11;')
sim.run('knight_preset_save(2,"My Preset=;[x]");')
eq(sim.eval('global.knight_presets[2].name'),'My Presetx','name cleaned')
sim.run('knight_store_save();')
s2=make_sim(); shutil.copy(os.path.join(sim.sandbox,'knight_hub.ini'),os.path.join(s2.sandbox,'knight_hub.ini')); s2.run('knight_store_load();')
eq(s2.eval('global.knight_store_status'),'ok','reload ok')
s2.run('global.d=knight_preset_decode(global.knight_presets[2]);')
eq(s2.eval('global.d.ok'),True,'decode ok'); eq(s2.eval('global.d.cfg.knight==knight_find_key("violet")'),True,'knight by key')
eq(s2.eval('global.d.cfg.party[1]'),3,'party kept'); eq(s2.eval('global.d.cfg.c_hp1'),1,'chal kept'); eq(s2.eval('global.d.cfg.rush_pct'),70,'pct kept')
eq(s2.eval('string_char_at(global.d.spells,13+1)'),'5','spell string'); 
s2.run('knight_preset_apply(global.d); ')
eq(s2.eval('global.spell[3][3]'),11,'spell applied'); eq(s2.eval('global.knight_cfg.c_hp1'),1,'cfg applied')
# rename, delete
s2.run('knight_preset_rename(2,"Renamed");'); eq(s2.eval('global.knight_presets[2].name'),'Renamed','rename')
s2.run('knight_preset_delete(2);'); ok(s2.eval('is_undefined(global.knight_presets[2])'),'deleted')
# empty name -> default
s2.run('knight_preset_save(0,"   ");'); eq(s2.eval('global.knight_presets[0].name'),'PRESET 1','default name')
# corrupted preset content decode
s2.run('var p=global.knight_presets[0]; p.knight="ghostknight"; p.song="nope.ogg"; p.party=[9,2,2]; p.spells="zz"; global.d=knight_preset_decode(p);')
eq(s2.eval('global.d.ok'),True,'bad preset decodes'); ok(s2.eval('array_length(global.d.corr)')>=4,'corrections listed: %s'%s2.eval('array_length(global.d.corr)'))
eq(s2.eval('global.d.cfg.knight'),0,'unknown knight->normal'); eq(len(s2.eval('global.d.spells')),48,'spell string 48')
# preset with elec with no-tp is loadable but launch blocked (validation after load)
s2.run('var c=knight_cfg_default(); c.knight=knight_find_key("elec"); c.party=[1,2,3]; c.c_notp=1; global.knight_cfg=c; knight_preset_save(1,"E"); var d=knight_preset_decode(global.knight_presets[1]); knight_preset_apply(d); global.r=knight_resolve(global.knight_cfg);')
eq(s2.eval('global.r.ok'),False,'invalid preset blocked at launch'); ok(s2.eval('is_struct(global.r.fixcfg)'),'suggestion')
# future slot
ini=open(os.path.join(sim.sandbox,'knight_hub.ini')).read()
print([l for l in ini.splitlines() if l.startswith('[preset2')or l.startswith('ver')][:4])
print('preset tests: %d checks, %d failures'%(N[0],len(FAILS)))
# future-version slot (written by 'newer' hub with a valid checksum)
sim.run('global.knight_presets[2].ver=2; global.knight_presets[2].future=true; knight_store_save();')
s3=make_sim(); shutil.copy(os.path.join(sim.sandbox,'knight_hub.ini'),os.path.join(s3.sandbox,'knight_hub.ini')); s3.run('knight_store_load();')
eq(s3.eval('global.knight_store_status'),'ok','future slot file loads ok')
ok(s3.eval('is_struct(global.knight_presets[2])'),'future slot present')
s3.run('global.d=knight_preset_decode(global.knight_presets[2]);')
eq(s3.eval('global.d.ok'),False,'future slot unloadable')
s3.run('knight_preset_delete(2);')
ok(s3.eval('is_undefined(global.knight_presets[2])'),'future slot deletable')
print('preset tests: %d checks, %d failures'%(N[0],len(FAILS)))
