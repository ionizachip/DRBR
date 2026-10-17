# Noelle gets an ACT ("N-Action", she tries talking) in every knight; Elecknight's Unleash works without Kris
import json,re
G='/home/claude/work/gml/'
K=['base','kaizo','elec','violet','thorn','cyan']
rules=[]
def R(i,var,entry,find,rep,why):
    t=open(G+var+'/CodeEntries/'+entry+'.gml',encoding='utf8').read()
    assert t.count(find)==1,(i,var,t.count(find),find[:60])
    rules.append({"id":i,"variants":[var],"entry":entry,"find":find,"replace":rep,"why":why,"scenarios":['solo','dup','noelle','nokris']})
MS='gml_GlobalScript_scr_monstersetup'
ST='gml_Object_obj_knight_enemy_'
f1='        global.actnameral[myself][0] = stringsetloc("R-Action", "scr_monstersetup_slash_scr_monstersetup_gml_2187_0");\n        global.actsimulral[myself][0] = 0;\n'
r1=f1+'        global.canactnoe[myself][0] = 1;\n        global.actnamenoe[myself][0] = "N-Action";\n        global.actsimulnoe[myself][0] = 0;\n        global.actcostnoe[myself][0] = 0;\n'
talk=('    if (actingnoe == 1 && actconnoe == 1%s)\n    {\n        if (!variable_instance_exists(id, "nactcount"))\n            nactcount = 0;\n        nactcount++;\n'
 '        scr_speaker("noone");\n        if (nactcount == 1)\n        {\n            msgset(0, "* " + global.charname[4] + " tried talking.../");\n'
 '            scr_anyface_next("noelle", "B");\n            msgnext("\\\\EB* U-um... h-hello? You d-don\'t have to do this...!/");\n            scr_anyface_next("noelle", "Y");\n            msgnext("\\\\EY* I don\'t know why you\'re so angry, but... p-please stop!/");\n            scr_anyface_next("none", 0);\n            msgnext("* (... but nothing happened.)/%%");\n        }\n'
 '        else\n        {\n            msgset(0, "* " + global.charname[4] + " tried talking.../");\n            scr_anyface_next("noelle", "A");\n            msgnext("\\\\EA* U-umm... c-can we just talk about it...?/");\n            scr_anyface_next("none", 0);\n            msgnext("* (... but nothing happened.)/%%");\n        }\n'
 '        scr_battletext_default();\n        actcon = 1;\n        actconnoe = 0;\n    }\n')
f2='    if (actcon == 20 || actconsus == 20 || actconral == 20)\n'
for v in K:
    R('N01-noelle-act-setup-'+v,v,MS,f1,r1,'Noelle had no ACT list for the Knight (monster type 104); the engine already supports a Noelle list.')
    g=' && !(phase == 5 && unleash_actor == 4)' if v=='elec' else ''
    R('N02-noelle-act-'+v,v,ST+'Step_0',f2,talk%g+f2,'Noelle ACT handler (she tries talking, like Ralsei).')
# ---- Elecknight: Unleash for the topmost living non-Kris party member and no Kris requirement
E='elec'
setm=('unleash_con = 0;\nunleash_who = -4;\nunleash_actor = 0;\n'
 'set_unleash_actor = function(_na)\n{\n    var _kr = scr_havechar(1);\n    var _ix = _kr ? 1 : 0;\n'
 '    if (unleash_actor == 2)\n    {\n        if (_kr)\n        {\n            global.canactsus[myself][1] = false;\n            global.actnamesus[myself][1] = " ";\n            global.actcostsus[myself][1] = 0;\n        }\n        else\n        {\n            global.actnamesus[myself][0] = "S-Action";\n            global.actdescsus[myself][0] = "";\n            global.actcostsus[myself][0] = 0;\n        }\n    }\n'
 '    if (unleash_actor == 3)\n    {\n        if (_kr)\n        {\n            global.canactral[myself][1] = false;\n            global.actnameral[myself][1] = " ";\n            global.actcostral[myself][1] = 0;\n        }\n        else\n        {\n            global.actnameral[myself][0] = "R-Action";\n            global.actdescral[myself][0] = "";\n            global.actcostral[myself][0] = 0;\n        }\n    }\n'
 '    if (unleash_actor == 4)\n    {\n        global.actnamenoe[myself][0] = "N-Action";\n        global.actdescnoe[myself][0] = "";\n        global.actcostnoe[myself][0] = 0;\n    }\n'
 '    unleash_actor = _na;\n'
 '    if (_na == 2)\n    {\n        global.canactsus[myself][_ix] = true;\n        global.actnamesus[myself][_ix] = "Unleash";\n        global.actdescsus[myself][_ix] = "Reveal#Enemy";\n        global.actcostsus[myself][_ix] = 200;\n        global.actsimulsus[myself][_ix] = 0;\n    }\n'
 '    if (_na == 3)\n    {\n        global.canactral[myself][_ix] = true;\n        global.actnameral[myself][_ix] = "Unleash";\n        global.actdescral[myself][_ix] = "Reveal#Enemy";\n        global.actcostral[myself][_ix] = 200;\n        global.actsimulral[myself][_ix] = 0;\n    }\n'
 '    if (_na == 4)\n    {\n        global.canactnoe[myself][0] = true;\n        global.actnamenoe[myself][0] = "Unleash";\n        global.actdescnoe[myself][0] = "Reveal#Enemy";\n        global.actcostnoe[myself][0] = 200;\n        global.actsimulnoe[myself][0] = 0;\n    }\n};\n')
setm=setm.replace('\\n','\n')
R('N10-elec-init',E,ST+'Create_0','toldaboutunleash = 0;\n','toldaboutunleash = 0;\n'+setm.replace('\\n','\n'),'state and helper for the Unleash actor.')
add=('    if (!scr_havechar(1))\n    {\n        global.actnamesus[myself][0] = "S-Action";\n        global.actdescsus[myself][0] = "";\n        global.actcostsus[myself][0] = 0;\n'
 '        global.actnameral[myself][0] = "R-Action";\n        global.actdescral[myself][0] = "";\n        global.actcostral[myself][0] = 0;\n    }\n'
 '    unleash_actor = 0;\n    var _na5 = 0;\n    for (var _s5 = 0; _s5 < 3; _s5++)\n    {\n        var _c5 = global.char[_s5];\n        if (_c5 >= 2 && _c5 <= 4 && global.hp[_c5] > 0)\n        {\n            _na5 = _c5;\n            break;\n        }\n    }\n    set_unleash_actor(_na5);\n')
R('N11-elec-start5',E,ST+'Create_0','    global.actcostral[myself][0] = 12.5;\n    scr_spellmenu_setup();\n','    global.actcostral[myself][0] = 12.5;\n'+add+'    scr_spellmenu_setup();\n','Phase 5 (Unleash): the topmost living non-Kris member gets Unleash too; Kris-revive acts only exist with Kris.')
R('N12-elec-end5',E,ST+'Create_0','    global.actcostral[myself][0] = 0;\n    scr_spellmenu_setup();\n','    global.actcostral[myself][0] = 0;\n    set_unleash_actor(0);\n    global.canactnoe[myself][0] = true;\n    scr_spellmenu_setup();\n','Remove the extra Unleash entries when phase 5 ends.')
R('N13-elec-hint',E,ST+'Step_0','else if (phase == 5 && global.tension > global.actcost[myself][2] && global.hp[1] > 0)','else if (phase == 5 && global.tension > global.actcost[myself][2] && (global.hp[1] > 0 || !scr_havechar(1)))','UNLEASH hint without Kris.')
R('N14-elec-raisekris-sus',E,ST+'Step_0','    if (actingsus == 1 && actconsus == 1 && phase == 5)\n','    if (actingsus == 1 && actconsus == 1 && phase == 5 && scr_havechar(1))\n','Revive-Kris act only with Kris.')
R('N15-elec-raisekris-ral',E,ST+'Step_0','    if (actingral == 1 && actconral == 1 && phase == 5)\n','    if (actingral == 1 && actconral == 1 && phase == 5 && scr_havechar(1))\n','Revive-Kris act only with Kris.')
R('N16-elec-ral-talk',E,ST+'Step_0','    if (actingral == 1 && actconral == 1 && phase != 5)\n','    if (actingral == 1 && actconral == 1 && (phase != 5 || (!scr_havechar(1) && unleash_actor != 3)))\n','Ralsei talk act also in phase 5 when there is no Kris (and he is not the Unleash actor).')
upd=('if (phase == 5 && unleash_con == 0)\n{\n    var _nu = 0;\n    for (var _su = 0; _su < 3; _su++)\n    {\n        var _cu = global.char[_su];\n        if (_cu >= 2 && _cu <= 4 && global.hp[_cu] > 0)\n        {\n            _nu = _cu;\n            break;\n        }\n    }\n    if (_nu != unleash_actor)\n        set_unleash_actor(_nu);\n}\n')
R('N18-elec-unleash-actor-update',E,ST+'Step_0','if (global.myfight == 3)\n{\n    xx = __view_get(e__VW.XView, 0);\n',upd+'if (global.myfight == 3)\n{\n    xx = __view_get(e__VW.XView, 0);\n','If the Unleash actor is knocked down, the next living member takes over.')
unl=('    var _unl = false;\n    var _who = -4;\n    var _kru = scr_havechar(1);\n'
 '    if (phase == 5 && unleash_actor == 2 && actingsus == (_kru ? 2 : 1) && actconsus == 1)\n    {\n        _unl = true;\n        _who = obj_herosusie;\n        actconsus = 0;\n    }\n'
 '    if (phase == 5 && unleash_actor == 3 && actingral == (_kru ? 2 : 1) && actconral == 1)\n    {\n        _unl = true;\n        _who = obj_heroralsei;\n        actconral = 0;\n    }\n'
 '    if (phase == 5 && unleash_actor == 4 && actingnoe == 1 && actconnoe == 1)\n    {\n        _unl = true;\n        _who = obj_heronoelle;\n        actconnoe = 0;\n    }\n'
 '    if (_unl)\n    {\n        unleash_who = _who;\n        msgset(0, "* Your SOUL emitted a brilliant light!/%");\n        scr_battletext_default();\n        unleash_con = 1;\n    }\n'
 '    if (unleash_con == 1 && actcon == 0 && !i_ex(obj_writer))\n    {\n        unleash_con = 2;\n        with (unleash_who)\n        {\n            scr_oflash();\n        }\n        instance_create(unleash_who.x + 30, unleash_who.y + 50, obj_purify_event);\n    }\n'
 '    if (unleash_con == 2 && !i_ex(obj_purify_event))\n    {\n        unleash_con = 0;\n        actcon = 1;\n    }\n')
R('N17-elec-unleash-actor',E,ST+'Step_0','    if (actingsus == 1 && actconsus == 1 && phase != 5)\n',unl+'    if (actingsus == 1 && actconsus == 1 && (phase != 5 || (!scr_havechar(1) && unleash_actor != 2)))\n','UNLEASH for the topmost living non-Kris member and S-Action in phase 5 without Kris.')
json.dump(rules,open('/home/claude/scripts/rules/noelle_act_rules.json','w'),indent=1)
print(len(rules),'rules')
