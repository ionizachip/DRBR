"""Generate rules/weird_route_rules.json : Weird Route for any party that contains Kris (Kaizo Side-B + Violet)."""
import json
G='/home/claude/work/gml/'
S=open(G+'violet/CodeEntries/gml_Object_obj_knight_enemy_Step_0.gml').read()
SV=open(G+'violet/CodeEntries/gml_GlobalScript_scr_complete_save_file.gml').read()
i=SV.index('    if (personwhosabouttosuperdie == "ralsei")');j=SV.index('function scr_vsideb_flavortext')
OLD_KILL=SV[i:j].rstrip()
# strip the function's closing brace (last '}' in OLD_KILL belongs to function)
assert OLD_KILL.endswith('}')
OLD_KILL=OLD_KILL[:-1].rstrip('\n')
SC=['solo','dup','noelle','nokris']
rules=[]
def R(i,var,entry,find,rep,why,regex=False,count=None):
    r={"id":i,"variants":[var],"entry":entry,"find":find,"replace":rep,"why":why,"scenarios":SC}
    if regex:
        r["regex"]=True
        if count:r["count"]=count
    rules.append(r)
ST='gml_Object_obj_knight_enemy_'
def chk(s,n=1):
    assert S.count(s)==n,(S.count(s),s[:50])
R('W01-v-sideb-needs-kris','violet',ST+'Create_0','v_sideb = global.flag[456] && scr_havechar(1) && scr_havechar(2) && scr_havechar(3);',
  'v_sideb = global.flag[456];','Weird Route (Violet) works for every party (build 37): with Kris the mod\'s own story plays; without Kris the member who stays to the end finishes the fight (knight_vb_* in the hub).')
R('W02-kill1-target','violet',ST+'Other_19','kill_target = 1411;','kill_target = knight_vb_victim(1);',
  'Phase-1 loss: with Kris Ralsei, else Noelle; without Kris the Angel (Noelle), else Ralsei; nobody -> scene skipped (knight_vb_victim).')
R('W03-kill2-target','violet',ST+'Other_19','kill_target = 1410;','kill_target = knight_vb_victim(2);',
  'Phase-2 loss: with Kris Susie; without Kris Ralsei (when the Angel went first); nobody -> scene skipped.',regex=True,count=2)
R('W04-kill-skip','violet',ST+'Step_0','if (knightkillcon == 2)\n{\n',
  'if (knightkillcon == 2 && kill_target == -4)\n{\n    kill_skipped = 1;\n    if (knight_vb_kris())\n    {\n        if (phase == 3)\n        {\n            kill_target = obj_herosusie;\n            knightkillcon = 30;\n        }\n        else\n        {\n            kill_target = obj_heroralsei;\n            snd_stop(global.batmusic[0]);\n            knightkillcon = 10;\n        }\n    }\n    else\n    {\n        if (phase < 3)\n            snd_stop(global.batmusic[0]);\n        knightkillcon = 10;\n    }\n}\nif (knightkillcon == 2)\n{\n','Nobody to lose in this phase: skip the scripted loss but still apply its consequences (stronger Knight, ACT unlock; without Kris the finisher scene).')
a='        var personwhosgonnadie = "ralsei";\n        if (kill_target == 1410)\n        {\n            personwhosgonnadie = "susie";\n        }\n'
chk(a)
R('W05-kill-name','violet',ST+'Step_0',a,a+'        if (kill_target == obj_heronoelle)\n        {\n            personwhosgonnadie = "noelle";\n        }\n','Noelle can take the phase-1 loss.')
a='        if (kill_target == 1411)\n        {\n            snd_stop(global.batmusic[0]);\n            if (global.hp[2] > 0)\n'
chk(a)
R('W06-kill-susie-shock','violet',ST+'Step_0',a,'        if (kill_target != obj_herosusie)\n        {\n            snd_stop(global.batmusic[0]);\n            if (scr_havechar(2) && global.hp[2] > 0)\n','Susie shock only if Susie is in the party; Noelle counts as the phase-1 loss too.')
a='    else if (global.hp[2] > 0)\n    {\n        knightkillcon = 11;\n    }\n    else\n    {\n        knightkillcon = 50;\n    }\n'
chk(a)
R('W07-kill9-route','violet',ST+'Step_0',a,'    else if (!scr_havechar(2))\n    {\n        knightkillcon = 10;\n    }\n    else if (global.hp[2] > 0)\n    {\n        knightkillcon = 11;\n    }\n    else\n    {\n        knightkillcon = 50;\n    }\n','No Susie: no reaction scene after the phase-1 loss.')
a='global.battlemsg[0] = stringsetsub("* ~1 was completely obliterated.&* The enemy became stronger.", ralseititle);'
chk(a)
R('W08-msg1','violet',ST+'Step_0',a,'if (variable_instance_exists(id, "kill_skipped") && kill_skipped)\n            global.battlemsg[0] = "* The enemy became stronger.";\n        else\n            global.battlemsg[0] = stringsetsub("* ~1 was completely obliterated.&* The enemy became stronger.", (kill_target == obj_heronoelle) ? "The Angel" : ralseititle);\n        kill_skipped = 0;','Message follows who was actually lost.')
a='global.battlemsg[0] = stringsetsub("* ~1 never stood a chance.&* The enemy became stronger.", susietitle);'
chk(a)
R('W09-msg2','violet',ST+'Step_0',a,'if (variable_instance_exists(id, "kill_skipped") && kill_skipped)\n            global.battlemsg[0] = "* The enemy became stronger.";\n        else\n            global.battlemsg[0] = stringsetsub("* ~1 never stood a chance.&* The enemy became stronger.", susietitle);\n        kill_skipped = 0;','Message follows who was actually lost.')
a='        global.canact[myself][2] = 1;\n        global.actactor[myself][2] = 2;\n        global.actname[myself][2] = stringset("RedBuster");\n        global.actdesc[myself][2] = stringset("Red#Damage");\n        global.actcost[myself][2] = 150;\n        whatsact3 = "redbuster";\n'
chk(a)
b=a.replace('        global.canact','            global.canact').replace('        global.actactor','            global.actactor').replace('        global.actname','            global.actname').replace('        global.actdesc','            global.actdesc').replace('        global.actcost','            global.actcost').replace('        whatsact3','            whatsact3')
R('W10-redbuster-needs-susie','violet',ST+'Step_0',a,'        if (scr_havechar(2))\n        {\n'+b+'        }\n','RED BUSTER is Susie\'s ACT: only unlocked when Susie is in the party.')
a='msgset(0, "R^3-Ralsei...?\\\\s0/%");'
chk(a)
R('W11-susie-line1','violet',ST+'Step_0',a,'if (kill_target == obj_heronoelle)\n            msgset(0, "N^3-Noelle...?\\\\s0/%");\n        else\n            msgset(0, "R^3-Ralsei...?\\\\s0/%");','Unique Susie reaction when it is Noelle.')
a='msgset(0, "I\'ll..^2. make..^2.&YOU..^2. SUFFER!/%");'
chk(a)
R('W12-susie-line2','violet',ST+'Step_0',a,'if (kill_target == obj_heronoelle)\n    {\n        msgset(0, "I\'LL..^2. TEAR..^2.&YOU..^2. APART!!!/%");\n        with (obj_herosusie)\n        {\n            scr_shakeobj();\n        }\n        snd_play(snd_noise);\n    }\n    else\n        msgset(0, "I\'ll..^2. make..^2.&YOU..^2. SUFFER!/%");','Unique Susie reaction when it is Noelle.')
a='msgnext("R..^2. Ralsei...?/");'
chk(a)
R('W13-susie-line3','violet',ST+'Step_0',a,'msgnext((kill_target == obj_heronoelle) ? "N..^2. Noelle...?/" : "R..^2. Ralsei...?/");','Unique Susie reaction when it is Noelle.')
new_kill='''    var _cid = 3;
    var _obj = obj_heroralsei;
    if (personwhosabouttosuperdie == "susie")
    {
        _cid = 2;
        _obj = obj_herosusie;
    }
    if (personwhosabouttosuperdie == "noelle")
    {
        _cid = 4;
        _obj = obj_heronoelle;
    }
    global.hp[_cid] = global.hp[_cid] - howmuchsaidpersonisgonnasuperdie;
    for (var _s = 0; _s < 3; _s++)
    {
        if (global.char[_s] == _cid)
        {
            global.char[_s] = 0;
            global.faceaction[_s] = 8;
            scr_dead(_s);
        }
    }
    with (_obj)
    {
        var _d = instance_create(x, y, obj_deathanim);
        _d.sprite_index = sprite_index;
        _d.depth = depth - 1;
        _d.image_xscale = 2;
        _d.image_yscale = 2;
        visible = 0;
        x -= 600;
    }
'''
R('W14-kill-char-any-slot','violet','gml_GlobalScript_scr_complete_save_file',OLD_KILL,new_kill.rstrip('\n'),'scr_vsideb_kill_char hard-coded char slots 1/2: now removes every slot holding that character (duplicates included) and supports Noelle.')
R('W15-kill-skipped-init','violet',ST+'Create_0','kill_target = -4;','kill_target = -4;\nkill_skipped = 0;','init')
R('W16-kaizo-sideb-end','kaizo','gml_Object_obj_ch3_PTB02_Step_0','    if (con == 49 && global.flag[456])\n    {\n        con = 49.1;\n    }\n','','Kaizo Side-B victory had no handler for con 49.1 (soft-lock on a white screen). It now uses the normal victory sequence.')

for _v in ['base','kaizo','elec','violet','thorn','cyan']:
    R('S01-setdirection-bounds-'+_v,_v,'gml_Object_obj_tracking_swords_manager_Step_0',r'if \(setdirection\[setcount\] != -1\)','if (setcount < array_length(setdirection) && setdirection[setcount] != -1)',
      'Long Tracking Swords turns advance setcount past the end of setdirection (400 in Violet, 200 in Kaizo): array read out of range = crash in GameMaker. Guarded.',regex=True)

R('S02-cyan-random-args','cyan','gml_Object_obj_roaringknight_splitslash_Step_0',r'random\(1, -1\)','random(1)',
  'random() takes one argument; the extra argument is dropped (value was never used for anything but a dummy variable).',regex=True)

R('K02-final-kill-hub','kaizo','gml_Object_obj_knight_roaring2_Other_11','                    room_goto(PLACE_FAILURE);\n',
  '                    if (variable_global_exists("knight_run") && global.knight_run == 1 && is_struct(global.krun))\n                        knight_defeat_begin();\n                    else\n                        room_goto(PLACE_FAILURE);\n',
  'Kaizo final attack jumped straight to the failure room, bypassing scr_gameover (the hub never heard about the defeat and the failure-room retry loop started inside a hub run). In a hub run it now reports a normal defeat.')
a='        with (obj_heroralsei)\n        {\n            if (global.hp[3] > 0)\n            {\n                snd_play(snd_txtral);\n                scr_shakeobj();\n                global.faceaction[2] = 5;\n            }\n            idlesprite = spr_ralsei_hurt_fixed;\n        }\n'
chk(a)
R('W17-angel-scared-sprite','violet',ST+'Step_0',a,'        if (kill_target == obj_heronoelle)\n        {\n            with (obj_heronoelle)\n            {\n                if (global.hp[4] > 0)\n                {\n                    snd_play(snd_noelle_scared);\n                    scr_shakeobj();\n                    for (var _fs = 0; _fs < 3; _fs++)\n                    {\n                        if (global.char[_fs] == 4)\n                            global.faceaction[_fs] = 5;\n                    }\n                }\n                idlesprite = variable_instance_exists(id, "hurtsprite") ? hurtsprite : spr_noelleb_hurt;\n            }\n        }\n        else\n        {\n            with (obj_heroralsei)\n            {\n                if (global.hp[3] > 0)\n                {\n                    snd_play(snd_txtral);\n                    scr_shakeobj();\n                    global.faceaction[2] = 5;\n                }\n                idlesprite = spr_ralsei_hurt_fixed;\n            }\n        }\n','The Angel (Noelle) takes the phase-1 loss: her own startled/hurt sprite, her own scared sound and her own party slot instead of Ralsei\'s.')
import make_w18; make_w18.add(R,chk,ST,S)
json.dump(rules,open('/home/claude/scripts/rules/weird_route_rules.json','w'),indent=1)
print(len(rules),'rules')
