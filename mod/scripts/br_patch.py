"""Build 45: the battle hooks of the online battle royale, applied to the merged fight code (after merge.py / det_rewrite).
Idempotent: each patch looks for the unpatched text and leaves already patched code alone. Every patch must be found the
expected number of times in total (patched + unpatched), or the step fails.

  1. the knight's Step (every fight): an attack starts when rtimer reaches 12 after the enemy turn begins. Online, the start
     is held at the shared moment of the timeline: rtimer += kbr_rgate() (1 offline - unchanged).
  2. the battle controller's Step: when the turn timer runs out it ends the enemy turn (bullets, box, SOUL away, the
     menu). Online the battle never goes back to the menu: the timeline ends attacks (kbr_hold_end() is false offline).
  3. the graze box: grazing shortens the enemy turn in Chapter 3 (global.turntimer -= ...). Online every game must keep
     the same attack length, so grazing does not touch the turn timer there; a graze also fills the skill gauge
     (kbr_on_graze()).
  4. (build 46) the battle controller's Step and Draw start with kbr_menu_block(): online the command menu (FIGHT / ACT /
     ITEM / SPARE / DEFEND) never opens - its keys, its sounds and its party-slot walk (build 45's "Variable Index [3] out
     of range [3] - global.char" crash) never run. Offline kbr_menu_block() does nothing.
  5. (build 47) Kaizo Knight's own HP rules are off online (knight_enc_hp_rules() is false only in an online fight): its
     "HP scene" (max HP above Kris 200 / Susie 230 / Ralsei 180 / Noelle 180 on its first frame -> a cutscene that cuts max HP
     and HP to those numbers and holds the battle for ~100 frames) and its arena's Noelle floor (max HP and HP set to 120
     whenever her max HP is lower - again after every sudden-death step).
  6. (build 47) scr_damage_maxhp's one-member branch (split slashes, the big quick slash) takes the online damage online
     (knight_direct_taken; offline it returns the number unchanged).
  6b. (DRBR 1.0.3) scr_damage_proportional (Spamton NEO's finale bullets) the same: an online hit online.
  7. (build 47) the original Knight encounter (walking right past x 1840 in the cold place starts it, every knight's version)
     does not start while you are in an online / practice room outside a fight (kfo_ow_encounter_ok; offline always true).
"""
import os, re, sys

M = '/home/claude/work/build/merged/'

PATCHES = [
    # build 48: the Roaring runs as an online cycle. The Violet Knight's forced pick of a phase-4 attack counted its phase-4 turn
    # once more than the practice pick does (its Roaring came out as no attack); the Supercharged Knight's Roaring starts its
    # extra phase 5 (offline only: kbr_phase5_ok() is false in an online fight)
    ('gml_Object_obj_knight_enemy_Other_10.gml', r'phase4turn = phaseturn;',
     'phase4turn = phaseturn - ((practice == false && !practicemode) ? 1 : 0);',
     r'phase4turn = phaseturn - \(\(practice == false && !practicemode\) \? 1 : 0\);', 1),
    ('gml_Object_obj_knight_roaring2_Step_0.gml', r'if \(phase < 5\)(?! && kbr_phase5_ok)', 'if (phase < 5 && kbr_phase5_ok())',
     r'if \(phase < 5 && kbr_phase5_ok\(\)\)', 1),
    # (entry file, old regex, new text, patched-marker regex, expected total)
    ('gml_Object_obj_knight_enemy_Step_0.gml', r'rtimer \+= 1;', 'rtimer += kbr_rgate();', r'rtimer \+= kbr_rgate\(\);', 6),
    ('gml_Object_obj_battlecontroller_Step_0.gml', r'if \(global\.turntimer <= 0 && reset == 0\)',
     'if (global.turntimer <= 0 && reset == 0 && !kbr_hold_end())', r'if \(global\.turntimer <= 0 && reset == 0 && !kbr_hold_end\(\)\)', 5),
    ('gml_Object_obj_grazebox_Collision_obj_collidebullet.gml', r'if \(global\.turntimer >= 10\)',
     'if (global.turntimer >= 10 && !global.kbr_det.on)', r'if \(global\.turntimer >= 10 && !global\.kbr_det\.on\)', 8),
    ('gml_Object_obj_grazebox_Collision_obj_collidebullet.gml', r'grazed = 1;(?!\s*kbr_on_graze)', 'grazed = 1;\n                    kbr_on_graze();',
     r'grazed = 1;\s*kbr_on_graze\(\);', 3),
    ('gml_Object_obj_battlecontroller_Step_0.gml', r'\Aswitch \(global\.knight_variant\)', 'kbr_menu_block();\nswitch (global.knight_variant)',
     r'\Akbr_menu_block\(\);\nswitch \(global\.knight_variant\)', 1),
    ('gml_Object_obj_battlecontroller_Draw_0.gml', r'\Aswitch \(global\.knight_variant\)', 'kbr_menu_block();\nswitch (global.knight_variant)',
     r'\Akbr_menu_block\(\);\nswitch \(global\.knight_variant\)', 1),
    ('gml_Object_obj_knight_enemy_Step_0.gml', r'if \(!practicemode && !nohitmode\)(?=\s*\{\s*if \(\(global\.maxhp\[1\] > 200)',
     'if (!practicemode && !nohitmode && knight_enc_hp_rules())',
     r'if \(!practicemode && !nohitmode && knight_enc_hp_rules\(\)\)(?=\s*\{\s*if \(\(global\.maxhp\[1\] > 200)', 1),
    ('gml_Object_obj_ch3_PTB02_Step_0.gml', r'if \(global\.maxhp\[4\] < 120\)', 'if (global.maxhp[4] < 120 && knight_enc_hp_rules())',
     r'if \(global\.maxhp\[4\] < 120 && knight_enc_hp_rules\(\)\)', 1),
    ('gml_GlobalScript_scr_damage_maxhp.gml', r'(?<!hpdiff = tdamage; )global\.hp\[chartarget\] -= knight_infhp_cut\(tdamage\);',
     'tdamage = knight_direct_taken(tdamage); hpdiff = tdamage; global.hp[chartarget] -= knight_infhp_cut(tdamage);',
     r'tdamage = knight_direct_taken\(tdamage\); hpdiff = tdamage; global\.hp\[chartarget\] -= knight_infhp_cut\(tdamage\);', 2),
    # DRBR 1.0.3: scr_damage_proportional (Spamton NEO's finale bullets, obj_sn_bulletfin: a share of max HP, 25 at 1 HP) took HP
    # with no online hit at all - no damage table, no SHIELD, no OUT: the party fell and the run ended in the middle of the
    # round. Online it is an online hit (knight_direct_taken, as scr_damage_maxhp's); offline unchanged
    ('gml_GlobalScript_scr_damage_proportional.gml', r'(?<!hpdiff = tdamage; )global\.hp\[chartarget\] -= knight_infhp_cut\(tdamage\);',
     'tdamage = knight_direct_taken(tdamage); hpdiff = tdamage; global.hp[chartarget] -= knight_infhp_cut(tdamage);',
     r'tdamage = knight_direct_taken\(tdamage\); hpdiff = tdamage; global\.hp\[chartarget\] -= knight_infhp_cut\(tdamage\);', 2),
    # build 47: the Knight's own damage cut for one attack (attack 2 at difficulty 1 / 3: 66%) is the original encounter's
    # balance - online every hit is the room's damage table, nothing taken off it after (offline unchanged)
    ('gml_GlobalScript_scr_damage.gml',
     r'obj_knight_enemy\.myattackchoice == 2 && \(obj_knight_enemy\.difficulty == 1 \|\| obj_knight_enemy\.difficulty == 3\)\)(?! && knight_enc_hp_rules)',
     'obj_knight_enemy.myattackchoice == 2 && (obj_knight_enemy.difficulty == 1 || obj_knight_enemy.difficulty == 3) && knight_enc_hp_rules())',
     r'obj_knight_enemy\.myattackchoice == 2 && \(obj_knight_enemy\.difficulty == 1 \|\| obj_knight_enemy\.difficulty == 3\) && knight_enc_hp_rules\(\)\)', 4),
    # build 47: the rest of the game's own cuts after the online damage (the table's number is the hit): DEFEND (2/3) and the
    # element resistance of a member's equipment (Noelle's ring halved some knights' hits online: a SKIN must be only a look)
    ('gml_GlobalScript_scr_damage.gml', r'if \(global\.charaction\[target\] == 10\)(?! && knight_enc_hp_rules)',
     'if (global.charaction[target] == 10 && knight_enc_hp_rules())',
     r'if \(global\.charaction\[target\] == 10 && knight_enc_hp_rules\(\)\)', 5),
    ('gml_GlobalScript_scr_damage.gml', r'if \(shadowmantlereduction == false\)(?! && knight_enc_hp_rules)',
     'if (shadowmantlereduction == false && knight_enc_hp_rules())',
     r'if \(shadowmantlereduction == false && knight_enc_hp_rules\(\)\)', 10),
    # build 47: Kaizo Knight's fight halves every hit on Noelle (its own balance for her) - after the online damage table, so
    # online Noelle (SKIN 4) took half damage from Kaizo's attacks: off online (a SKIN is only a look), offline unchanged
    ('gml_GlobalScript_scr_damage.gml', r'if \(global\.char\[target\] == 4\)(?! && knight_enc_hp_rules)',
     'if (global.char[target] == 4 && knight_enc_hp_rules())',
     r'if \(global\.char\[target\] == 4 && knight_enc_hp_rules\(\)\)', 1),
    ('gml_Object_obj_ch3_PTB02_Step_0.gml', r'if \(con == 0 && obj_mainchara\.x >= 1840 && global\.interact == 0\)',
     'if (con == 0 && obj_mainchara.x >= 1840 && global.interact == 0 && kfo_ow_encounter_ok())',
     r'if \(con == 0 && obj_mainchara\.x >= 1840 && global\.interact == 0 && kfo_ow_encounter_ok\(\)\)', 6),
    # DRBR: a hit on "a random member" (target 4: the Thorn Knight's Children ...) online, with nobody left to take it (the one
    # member already down, the same frame its SOUL breaks): scr_randomtarget_old gives slot 3 and the HP check divides by that
    # slot's max HP of 0 ("Division by zero" in scr_damage). Online that hit is simply not taken (offline unchanged).
    ('gml_GlobalScript_scr_damage.gml', r'__remtarget = 4;\n(\s*)scr_randomtarget_old\(\);\n\s*target = mytarget;\n(?!\s*if \(kbr_on\(\) && \(target >= 3)',
     lambda m: '__remtarget = 4;\n' + m.group(1) + 'scr_randomtarget_old();\n' + m.group(1) + 'target = mytarget;\n' + m.group(1) + 'if (kbr_on() && (target >= 3 || global.maxhp[global.char[target]] <= 0))\n' + m.group(1) + '    exit;\n',
     r'target = mytarget;\n\s*if \(kbr_on\(\) && \(target >= 3 \|\| global\.maxhp\[global\.char\[target\]\] <= 0\)\)', 5),
    # DRBR: Gerson's green SOUL (online_gerson53.gml: kbr_hj_heart_lock) - Chapter 4's obj_heart locks the SOUL while the shield is
    # up; Chapter 3's has no such hook: it goes in after the arrows are read, in every knight's version of the Step
    ('gml_Object_obj_heart_Step_0.gml', r'(?<!kbr_hj_heart_lock\(\);)\n(        )px = 0;\n        py = 0;\n        if \(canmove\)',
     lambda m: '\n' + m.group(1) + 'kbr_hj_heart_lock();\n' + m.group(1) + 'px = 0;\n        py = 0;\n        if (canmove)',
     r'kbr_hj_heart_lock\(\);\n        px = 0;', 3),
    # DRBR: the projectile contract's fallback (drbr53.gml) - a bullet missing a field obj_collidebullet's events read is
    # completed (and counted) before user event 5 and before the graze box reads it
    ('gml_Object_obj_collidebullet_Other_15.gml', r'\A(?!kbr_bullet_fix)', 'kbr_bullet_fix();\n', r'\Akbr_bullet_fix\(\);\n', 1),
    ('gml_Object_obj_grazebox_Collision_obj_collidebullet.gml', r'\A(?!with \(other\)\s*kbr_bullet_fix)', 'with (other)\n    kbr_bullet_fix();\n',
     r'\Awith \(other\)\n    kbr_bullet_fix\(\);\n', 1),
]


def main():
    done = 0
    for fn, old, new, mark, want in PATCHES:
        p = M + fn
        t = open(p, encoding='utf8').read()
        n_old = len(re.findall(old, t))
        n_new = len(re.findall(mark, t))
        if n_old + n_new != want:
            print('BR PATCH FAILED', fn, old, 'found', n_old, '+', n_new, 'patched, want', want)
            sys.exit(1)
        if n_old:
            t = re.sub(old, new if callable(new) else (lambda m: new), t)
            open(p, 'w', encoding='utf8').write(t)
            done += n_old
    print('br patches: %d applied (%d hook kinds)' % (done, len(PATCHES)))
    soul_guard()


# build 52: the attack pieces that read the SOUL every step (obj_heart.x ...) without checking it is there. With no SOUL
# (the turn's end took it away, the match's results, a send that outlived the attack) GameMaker stops the game: "Unable to
# find any instance for object index ... obj_heart" in obj_tracking_sword1's Step (a player's report). These pieces only
# exist while a SOUL does, so a step with no SOUL is skipped (the knight, the Roarings and the box controllers - which
# also run while there is no SOUL - are not touched).
GUARD = 'if (!instance_exists(obj_heart))\n    exit;\n'
GUARD_PRE = ('obj_tracking_sword1', 'obj_tracking_swords_manager', 'obj_knight_rotating_slash', 'obj_sword_tunnel_sword',
             'obj_roaringknight_split_bullet', 'obj_roaringknight_splitslash', 'obj_roaringknight_quickslash_big',
             'obj_knight_pointing_starchild', 'obj_knight_pointing_cone', 'obj_knight_diamondswordbullet_ext', 'obj_knight_swordfall')


def soul_guard():
    import glob
    n = 0
    seen = 0
    for f in sorted(glob.glob(M + 'gml_Object_*_Step_*.gml')):
        o = re.match(r'gml_Object_(.+)_Step_\d+\.gml$', os.path.basename(f)).group(1)
        if not o.startswith(GUARD_PRE):
            continue
        t = open(f, encoding='utf8').read()
        if not re.search(r'\bobj_heart\.', t):
            continue
        seen += 1
        if t.startswith(GUARD):
            continue
        open(f, 'w', encoding='utf8').write(GUARD + t)
        n += 1
    if seen < 20:
        print('SOUL GUARD FAILED: only %d attack steps found' % seen)
        sys.exit(1)
    print('soul guard: %d attack steps (%d newly guarded)' % (seen, n))


if __name__ == '__main__':
    main()
