from harness import *
import random,traceback,sys
sys.path.insert(0,'/home/claude/work/uiref')
from uiharness import menu_sim
seeds=int(sys.argv[1]) if len(sys.argv)>1 else 6
steps=int(sys.argv[2]) if len(sys.argv)>2 else 1500
bad=0
from collections import Counter
COV=Counter()
import re as _re
_kc=open(M+'gml_GlobalScript_knight_core.gml',encoding='utf8').read()
# build 45: the online match end (kbr_end_clean) clears the battle's objects; the menu harness has no battle, so the objects
# it names are made here (empty) - in the game they always exist
_BATTLE_OBJS=['obj_bulletparent','obj_bulletgenparent','obj_dbulletcontroller','obj_knight_twin','obj_attackpress']  # obj_attackpress: the FIGHT bars (TAB fast-forward checks it; build 46's fuzz presses TAB)
for _fn in ('kbr_atk_objs','kbr_split_objs'):
    _m=_re.search(r'function %s\(\)\s*\{\s*return \[([^\]]*)\]'%_fn,_kc)
    if _m: _BATTLE_OBJS+=[x.strip() for x in _m.group(1).split(',') if x.strip()]
for seed in range(seeds):
    sim,rec=menu_sim(seed=seed)
    for _i,_o in enumerate(_BATTLE_OBJS):
        if _o not in sim.objects: sim.define_object(_o,index=95000+_i)
    sim.run('knight_menu_open();')
    # build 46: every fourth seed starts on the KEYBINDS page (the random walk seldom reaches MORE OPTIONS)
    if seed%4==3:
        sim.run('global.knight_ui.tab=0; global.knight_ui.focus=1; global.knight_ui.krow=10; kfo_ui_open(); kfo_ui_keys_open("onl_opt");')
    rnd=random.Random(seed)
    keys=['up','down','left','right','ok','back','alt']
    last=None
    try:
        for i in range(steps):
            k=rnd.choice(keys+['ok','ok','down','right','right','right','down']) if rnd.random()<0.9 else None
            for kk in keys: sim.inp[kk]=0
            if k: sim.inp[k]=1
            # build 46: real keyboard keys too, now and then (a typing box's ENTER / ESC, the KEYBINDS box waiting for a key -
            # refused keys included -, letters, arrows, SHIFT, F4, TAB, BACKSPACE)
            if rnd.random()<0.12:
                sim.press(rnd.choice([27,13,27,13,ord('Q'),ord('S'),ord('Z'),ord('X'),ord('A'),ord('C'),ord('J'),37,38,39,40,16,160,115,9,8,32,112,188,96,48]),hold=rnd.choice([1,1,2,6]))
            last=(i,k)
            # menu may have been closed or a run launched; keep sim alive
            if sim.eval('instance_number(obj_knight_menu)')==0 and sim.eval('instance_number(obj_knight_prompt)')==0:
                if sim.eval('global.knight_run')==1 and sim.eval('knight_active()'):
                    # simulate a fight outcome so the fuzz explores result prompts
                    r=rnd.random()
                    sim.run('if(!instance_exists(obj_battlecontroller)) instance_create_depth(0,0,0,obj_battlecontroller); knight_run_tick();')
                    if r<0.3: sim.run('knight_hit_event();')
                    elif r<0.5: sim.run('knight_battle_won(); if(rnd_dummy()) {}') if False else sim.run('knight_battle_won(); if(global.krun.mode==0) knight_fight_finished(room_town_krisyard_dark);')
                    elif r<0.7: sim.run('knight_defeat_begin();')
                    sim.run('knight_run_tick();')
                    if sim.eval('instance_number(obj_knight_prompt)')==0 and rnd.random()<0.3:
                        sim.run('knight_continue_story();') if False else None
                        sim.run('knight_exit_run(true);')
                else:
                    sim.run('knight_menu_open();')
            sim.step(1)
            rec.ops.clear()
            if sim.eval('instance_number(obj_knight_menu)')>0:
                sim.run('knight_ui_draw();')
                rec.ops.clear()
                u=sim.eval('global.knight_ui')
                COV['tab%d'%sim.eval('global.knight_ui.tab')]+=1
                COV['sub:'+str(sim.eval('global.knight_ui.sub'))]+=1
                m=sim.eval('is_struct(global.knight_ui.modal)')
                if m: COV['modal:'+str(sim.eval('global.knight_ui.modal.k'))]+=1
            if sim.eval('instance_number(obj_knight_prompt)')>0: COV['prompt:'+str(sim.eval('instance_find(obj_knight_prompt,0).title'))]+=1
            if sim.eval('global.knight_run')==1: COV['run_active']+=1
        sim.run('knight_store_save();')
        inv=sim.eval('''(function(){var bad=0; var ks=knight_rec_keys(); for(var i=0;i<array_length(ks);i++){ var cats=(ks[i]=="rush")?["rush","rushnh"]:((ks[i]=="tag"||ks[i]=="remix")?["st","ch","nh"]:["st","ch","nh","pr"]); for(var j=0;j<array_length(cats);j++){ var r=knight_rec_get(ks[i],cats[j]); if(is_undefined(r)){bad+=1000;continue;} if(r.win>r.att) bad++; if(r.cur>r.streak) bad++; if(r.att<0||r.win<0||r.aband<0) bad++; if(cats[j]=="pr" && r.win>0) bad++; } } if(!is_undefined(knight_rec_get("cyan","st"))) bad+=100; var cc=knight_cfg_copy(global.knight_cfg); var cr=knight_cfg_sanitize(cc); return bad;})()''')
        if inv: print('seed',seed,'INVARIANT',inv); bad+=1
        import os,shutil
        s2=make_sim(); shutil.copy(os.path.join(sim.sandbox,'knight_hub.ini'),os.path.join(s2.sandbox,'knight_hub.ini')); s2.run('knight_store_load();')
        st=s2.eval('global.knight_store_status')
        if st!='ok': print('seed',seed,'reload status',st); bad+=1
    except Exception as e:
        bad+=1
        print('seed',seed,'failed at',last); traceback.print_exc(limit=1); print(str(e)[:300])
print(dict(COV));print('fuzz done, failures',bad)
sys.exit(1 if bad else 0)
