# W18: after the Knight kills Ralsei, Noelle (if in the party) learns SnowGrave, with dialogue
def add(R, chk, ST, S):
    old = 'if (knightkillcon == 10)\n{\n    knightkillcon = 0;\n    kristitle = "Kris";'
    chk(old)
    new = ('if (knightkillcon == 10 && kill_target == obj_heroralsei && !kill_skipped && scr_havechar(4) && global.hp[4] > 0 '
           '&& !(variable_instance_exists(id, "noe_learned") && noe_learned))\n{\n    noe_learned = 1;\n    noe_t = 0;\n    knightkillcon = 60;\n}\n')
    # build 37: Noelle reacts in her own speech bubbles (battle bubble voice 76, like Susie's 75), then the SnowGrave line in the box
    new += ('if (knightkillcon == 60)\n{\n    with (obj_heronoelle)\n    {\n        w_idle = variable_instance_exists(id, "idlesprite") ? idlesprite : -1;\n'
            '        idlesprite = variable_instance_exists(id, "hurtsprite") ? hurtsprite : spr_noelleb_hurt;\n        scr_shakeobj();\n    }\n'
            '    snd_play(snd_noelle_scared);\n    noe_t = 0;\n    knightkillcon = 61;\n}\n'
            'if (knightkillcon == 61)\n{\n    noe_t++;\n    if (noe_t >= 25 && !w_ex())\n    {\n'
            '        knight_say(4, "R^2-Ralsei...?!/%", 3);\n'
            '        noe_t = 0;\n        knightkillcon = 61.2;\n    }\n}\n'
            'if (knightkillcon == 61.2 && !w_ex())\n{\n    knight_say(4, "N-no..^2. get up..^2.&please get up...!/%", 2);\n    knightkillcon = 61.4;\n}\n'
            'if (knightkillcon == 61.4 && !w_ex())\n{\n    with (obj_heronoelle)\n    {\n'
            '        idlesprite = variable_instance_exists(id, "spellreadysprite") ? spellreadysprite : spr_noelleb_spellready;\n        scr_shakeobj();\n    }\n'
            '    knight_say(4, "...^2.&Then I..^2. I have to&do it myself./%", 3);\n    knightkillcon = 61.6;\n}\n'
            'if (knightkillcon == 61.6 && !w_ex())\n{\n'
            '    scr_speaker("noone");\n'
            '    msgset(0, "* (" + global.charname[4] + " can now use \\\\cYSNOWGRAVE\\\\cW.)/%");\n'
            '    scr_battletext();\n'
            '    noe_t = 0;\n    knightkillcon = 62;\n}\n'
            'if (knightkillcon == 62 && !w_ex())\n{\n'
            '    scr_spellget(4, 10);\n    scr_spellmenu_setup();\n    snd_play(snd_power);\n    noe_t = 0;\n    knightkillcon = 63;\n}\n'
            'if (knightkillcon == 63)\n{\n    noe_t++;\n    if (noe_t >= 40)\n    {\n        with (obj_heronoelle)\n        {\n'
            '            if (variable_instance_exists(id, "w_idle") && w_idle >= 0)\n                idlesprite = w_idle;\n        }\n        knightkillcon = 10;\n    }\n}\n')
    new += old
    R('W18-noelle-snowgrave', 'violet', ST + 'Step_0', old, new,
      'After the Knight kills Ralsei, Noelle (if she is in the party) learns SnowGrave (spell 10) in her first free spell slot, with dialogue.')

    # Noelle's display name: the mod renames the party (The Cage / The Girl / The Prince); Noelle becomes The Angel everywhere the game prints charname
    R('W19-angel-name-create', 'violet', ST + 'Create_0', 'global.charname[3] = "The Prince";\n',
      'global.charname[3] = "The Prince";\nglobal.charname[4] = "The Angel";\n',
      'Noelle is called The Angel in Violet Knight (name boxes, ACT menu, battle text) like the other party members get their titles.')
    R('W19-angel-name-cleanup', 'violet', ST + 'CleanUp_0', 'global.charname[3] = "Ralsei";\n',
      'global.charname[3] = "Ralsei";\nglobal.charname[4] = "Noelle";\n', 'Put Noelle\'s name back when the Knight is gone.')
    chk('global.charname[3] = "Ralsei";\n')
    R('W19-angel-name-restore', 'violet', ST + 'Step_0', 'global.charname[3] = "Ralsei";\n',
      'global.charname[3] = "Ralsei";\n    global.charname[4] = "Noelle";\n', 'Put Noelle\'s name back with the others when the mod restores them.')

    for _a,_b,_id in (('if (global.hp[1] < 1 && global.hp[3] < 1)\n        {\n            gameover_delay(1);','if (!knight_party_alive_any())\n        {\n            gameover_delay(1);','W20-kill-gameover-susie'),
                      ('else if (global.hp[1] < 1 && global.hp[2] < 1)\n    {\n        gameover_delay(0);','else if (!knight_party_alive_any())\n    {\n        gameover_delay(0);','W20-kill-gameover-ralsei')):
        chk(_a)
        R(_id, 'violet', ST + 'Step_0', _a, _b, 'Loss-scene game-over check looked at Kris/Susie/Ralsei only (not Noelle, and counted absent members): now uses the party-aware check.')
