"""DRBR: GERSON, the HAMMER OF JUSTICE (DELTARUNE Chapter 4's secret boss, encounter 160) - his pieces from the player's own
Chapter 4 data.win (MODS_DIR/c4.win, decompiled to /home/claude/work/src/c4). See make_boss.py for the common rules and
online/notes/src_gerson.md for the source survey.

Taken as they are (renamed obj_hj_*, spr_hj_*): the green SOUL's shield and spears (obj_spearblocker / obj_spearshot), the hammer
swings, the box squish / shrink / throw, the shell kick, the green switch, the fake heart, the teleports; the bell attack (cut
content of Chapter 4: real objects, never used by the shipped fight - a SEND only); his pattern builder (obj_hammer_of_justice_enemy's
user event 0) for the shipped patterns as kbr_hj_build(); scr_spearpattern / scr_spearshot / scr_sonic_boom / scr_jump_arc as kbr_hj_*.
Changed where Chapter 3 / the shared timeline differ:
  - the turn-timer writes of the pieces (they ended Chapter 4's turn) are gone: the timeline's cut ends an attack;
  - reads of Gerson's battle object (obj_hj_gerson.x ...) -> kbr_hj_gv("x"): a send can use the pieces while a knight is on stage
    (his battle object switched off); writes -> with (obj_hj_gerson);
  - the spear / shield / fake heart / pinball randomness stays the game's own (local outcomes: a block or a hit must never move
    the shared stream); the pattern builder and the box throw draw from the attack stream;
  - the Sound of Justice (another fight that shares these objects) and the intro conversation are never reached;
  - Chapter 4's event-manager call and its unused enum, the giant shell kick's room coordinates (on the camera now)."""
import os, re, sys
sys.path.insert(0, '/home/claude/scripts')
from make_boss import Boss, block_at

OUT = '/home/claude/scripts/gerson_gen/'
OBJ = {
    'obj_hammer_of_justice_enemy': 'obj_hj_gerson', 'obj_spearblocker': 'obj_hj_shield', 'obj_spearblocker_piece': 'obj_hj_shieldpiece',
    'obj_shield_just_particle': 'obj_hj_justpart', 'obj_spearshot': 'obj_hj_spear', 'obj_gerson_animation': 'obj_hj_shellpop',
    'obj_arrow_long_particle': 'obj_hj_notepart', 'obj_gerson_green_switch': 'obj_hj_switch', 'obj_gerson_green_chevron': 'obj_hj_chevron',
    'obj_gerson_fakeheart': 'obj_hj_fakeheart', 'obj_gerson_teleport': 'obj_hj_teleport', 'obj_gerson_teleport_generic': 'obj_hj_tpfx',
    'obj_gerson_swing_down': 'obj_hj_swing', 'obj_afterimage_gerson': 'obj_hj_afterimage', 'obj_gerson_growtangle_telegraph': 'obj_hj_column',
    'obj_gerson_swing_down_new': 'obj_hj_swing2', 'obj_gerson_growtangle_telegraph_new': 'obj_hj_swinghit', 'obj_gerson_squishes_box': 'obj_hj_squish',
    'obj_box_throw_controller': 'obj_hj_boxthrow', 'obj_gerson_hammer_bro_hammer': 'obj_hj_hammer', 'obj_gerson_shell_kick_controller': 'obj_hj_shellkick',
    'obj_gerson_shell_pinball': 'obj_hj_pinball', 'obj_gerson_growtangle_transform': 'obj_hj_boxshrink', 'obj_jump_arc': 'obj_hj_jumparc',
    'obj_shakeobj_y': 'obj_hj_shakey', 'obj_gerson_bell': 'obj_hj_bell', 'obj_gerson_bell_hit': 'obj_hj_bellhit',
    'obj_gerson_bell_bullet_radial': 'obj_hj_note', 'obj_shakedirectional': 'obj_hj_shakedir', 'obj_gerson_bell_attack_controller': 'obj_hj_bellctrl',
    'obj_dw_church_arena_bg': 'obj_hj_bg', 'obj_marker_fancy': 'obj_hj_mfancy',
}
TAKE = [o for o in OBJ if o not in ('obj_hammer_of_justice_enemy', 'obj_dw_church_arena_bg')]
SKIP_EV = {'obj_gerson_bell_hit': ('Other_24', 'Other_25')}
# the pieces whose randomness is a local outcome (a block, a hit, a SOUL-aimed shot): never the shared stream
LOCAL = {'obj_spearshot', 'obj_spearblocker', 'obj_spearblocker_piece', 'obj_shield_just_particle', 'obj_gerson_fakeheart', 'obj_gerson_shell_pinball',
         'obj_gerson_shell_kick_controller', 'obj_gerson_animation', 'obj_arrow_long_particle'}
SCRIPTS = {'scr_spearpattern': 'kbr_hj_pat', 'scr_spearpattern_reset': 'kbr_hj_pat_reset', 'scr_spearshot': 'kbr_hj_shot',
           'scr_sonic_boom': 'kbr_hj_sonic_boom', 'scr_jump_arc': 'kbr_hj_jump_arc'}
# the shipped turn order's patterns (src_gerson.md section 2): the pattern builder keeps these
PATTERNS = [0, 1, 2, 3, 4, 72, 70, 6, 7, 12, 9, 47, 13, 14, 53, 55, 56, 220, 19]
KEEP_SPR = {'spr_heart', 'spr_dodgeheart', 'spr_nothing', 'spr_dust2', 'spr_launchsmoke', 'spr_thrash_star', 'spr_whitepixel', 'spr_pxwhite',
            'spr_diamondbullet', 'spr_battlebg_0'}
# Chapter 3 has a spr_spearblocker of its own (an empty stub object's sprite): Gerson's is imported
IMPORT_SPR = {'spr_spearblocker'}
# the look written for the hub (online_gerson53.gml) uses these besides the ones in the taken code
EXTRA_SPR = ['spr_gerson_idle', 'spr_gerson_hair', 'spr_gerson_laugh', 'spr_greenheart', 'spr_gerson_teleport', 'spr_gerson_dodge',
             'spr_gerson_swing_side', 'spr_gerson_bell', 'spr_gerson_musical_note2', 'spr_gerson_swing', 'spr_spearblocker',
             # the background (online_gerson53.gml: kbr_hj_bg_draw)
             'spr_dw_church_bell_Large_topcenter', 'spr_gersonwindow_water', 'bg_dw_gerson_arena_stained_glass', 'spr_20px_white_gradient',
             'spr_dw_gerson_arena_palette', 'bg_dw_gerson_arena_battle', 'spr_dw_gerson_arena_shadow']
EXTRA_SND = ['snd_gerlaugh', 'snd_gerlaugh_clear', 'snd_eye_telegraph', 'motor_swing_down', 'motor_upper_quick_mid', 'snd_parry_fast_nodelay']


def rewrite_reads(t):
    """obj_hj_gerson.f reads -> kbr_hj_gv("f"); increments / compound writes -> with (obj_hj_gerson)"""
    t = re.sub(r'^([ ]*)obj_hj_gerson\.(\w+)(\+\+|--);$', r'\1with (obj_hj_gerson)\n\1    \2\3;', t, flags=re.M)
    t = re.sub(r'^([ ]*)obj_hj_gerson\.(\w+) ([-+*/]=) (.+);$', lambda m: '%svar _hjw = %s;\n%swith (obj_hj_gerson)\n%s    %s %s _hjw;' % (m.group(1), m.group(4), m.group(1), m.group(1), m.group(2), m.group(3)), t, flags=re.M)
    t = re.sub(r'\bobj_hj_gerson\.(\w+)\b(?!\s*(=[^=]|\+=|-=|\*=|/=|\+\+|--))', r'kbr_hj_gv("\1")', t)
    return t


def main():
    B = Boss('gerson', 'c4', 'hj', OBJ, keep_spr=KEEP_SPR, import_spr=IMPORT_SPR, local=LOCAL)
    for o in TAKE:
        B.take(o, skip=SKIP_EV.get(o, ()))
    # ---- the scripts (as hub functions)
    for a, b in SCRIPTS.items():
        t = B.code('gml_GlobalScript_' + a)
        assert t, a
        B.files['gml_GlobalScript_%s.gml' % b] = B.fix(t, det=(a not in ('scr_spearshot',)))
    # ---- the pattern builder: Other_10's blocks of the shipped patterns, in a function run by Gerson's battle object
    src = B.code('gml_Object_obj_hammer_of_justice_enemy_Other_10')
    blocks = []
    got = set()
    for m in re.finditer(r'^if \(attackpattern == ([\d.]+)( \|\| attackpattern == ([\d.]+))?\)\s*$', src, re.M):
        nums = [float(m.group(1))] + ([float(m.group(3))] if m.group(3) else [])
        if any(n in PATTERNS for n in nums):
            s, e = block_at(src, m.end())
            blocks.append(m.group(0) + '\n' + src[s:e])
            got |= set(n for n in nums if n in PATTERNS)
    missing = [p for p in PATTERNS if p not in got]
    assert not missing, ('patterns not found', missing)
    body = '\n'.join(blocks)
    fn = ('// DRBR (make_gerson.py): Chapter 4\'s pattern builder (obj_hammer_of_justice_enemy, user event 0) for the shipped patterns.\n'
          '// Run by Gerson\'s battle object (self) when an attack starts: the list of shots for pattern _p.\n'
          'function kbr_hj_build(_p)\n{\n    attackpattern = _p;\n    kbr_hj_pat_reset();\n    attackcount = 0;\n    attackcountmax = 0;\n    attacktimer = 0;\n    swingdown_ex = 0;\n'
          + '\n'.join('    ' + l if l else l for l in body.split('\n')) + '\n    return attackcountmax;\n}\n')
    B.files['gml_GlobalScript_kbr_hj_build.gml'] = B.fix(fn, det=True)
    # ---- script names everywhere
    for n in list(B.files):
        t = B.files[n]
        for a, b in SCRIPTS.items():
            t = re.sub(r'\b%s\b' % a, b, t)
        B.files[n] = t
    # ---- the turn-timer writes of the pieces (Chapter 4's turn ends): the timeline's cut ends an attack, so they no longer end
    # anything - an end write (global.turntimer = 1 / 2 / 10 / 12) only notes where Chapter 4 would have ended the turn
    # (kbr_hj_done: the emulator measures the attacks' lengths by it); the "keep going" writes (9999) are gone
    n_tt = 0
    for n in list(B.files):
        if 'kbr_hj_build' in n:
            continue
        t, k = re.subn(r'^([ ]*)global\.turntimer = ([\d.]+);\n', lambda m: '' if float(m.group(2)) >= 900 else '%skbr_hj_done(%s);\n' % (m.group(1), m.group(2)), B.files[n], flags=re.M)
        t, k2 = re.subn(r'global\.turntimer = min\(global\.turntimer, ([\d.]+)\);', r'kbr_hj_done(\1);', t)
        n_tt += k + k2
        B.files[n] = t
    assert n_tt >= 5, ('turn-timer writes', n_tt)
    # ---- Chapter 4's event manager call (the shield break) and its enum: not in this battle
    sp = B.files['gml_Object_obj_hj_spear_Other_10.gml']
    sp2 = re.sub(r'\n\s*with \(obj_event_manager\)\s*\{[^{}]*trigger_event[^{}]*\}', '\n', sp)
    sp2 = re.sub(r'\n[ ]*obj_event_manager\.trigger_event\([^;]*\);', '\n', sp2)
    sp2 = re.sub(r'\nenum UnknownEnum\s*\{[^}]*\}\s*', '\n', sp2)
    assert 'trigger_event' not in sp2, 'trigger_event left'
    # ---- the shield break reads the spear's angle through `other` inside with-blocks, after the spear destroyed itself in the
    # same event (the runner still has it then; kept in a local instead, the same value whatever the runner does)
    i0 = sp2.index('if (breakshield == true)\n{\n')
    s0, e0 = block_at(sp2, i0 + len('if (breakshield == true)\n'))
    blk = sp2[s0:e0]
    nb = blk.count('other.image_angle')
    assert nb >= 8, ('breakshield other.image_angle', nb)
    blk = blk.replace('other.image_angle', '_hjang')
    blk = blk.replace('{\n', '{\n    var _hjang = image_angle;\n', 1)
    sp2 = sp2[:s0] + blk + sp2[e0:]
    B.files['gml_Object_obj_hj_spear_Other_10.gml'] = sp2
    # ---- the pinball's room coordinates -> the battle's camera (Chapter 4's arena camera starts at 0)
    pb = B.files['gml_Object_obj_hj_pinball_Step_0.gml']
    for a, b in (('if (y < 250)', 'if (y < (cameray() + 250))'), ('if (y > 220)', 'if (y > (cameray() + 220))')):
        assert pb.count(a) >= 1, ('pinball', a)
        pb = pb.replace(a, b)
    B.files['gml_Object_obj_hj_pinball_Step_0.gml'] = pb
    # ---- the fake heart's 300 frames of invincibility: Chapter 4 cut it to 19 every frame (Gerson's Step); the same here
    fh = B.files['gml_Object_obj_hj_fakeheart_Create_0.gml']
    assert 'global.inv = 300;' in fh
    B.files['gml_Object_obj_hj_fakeheart_Create_0.gml'] = fh.replace('global.inv = 300;', 'global.inv = 19;')
    # ---- reads of Gerson's battle object through kbr_hj_gv (a send may run them with him switched off)
    for n in list(B.files):
        B.files[n] = rewrite_reads(B.files[n])
    B.finish(no_vars=('obj_hj_mfancy',))
    for n in list(B.files):
        B.files[n] = rewrite_reads(B.files[n])
    # ---- the pieces his SENDS use (online_gerson53.gml: HAMMER TOSS, SHELL PINBALL, SWING DOWN, BELL OF JUSTICE, SPEAR VOLLEY):
    # adopted by the send that makes them, the send's own end, never his object / the box / the SOUL - except the green-SOUL
    # pieces, whose SOUL lock IS the Spear Volley
    # ---- the host's bots in his green attacks: a spear reaching the SOULs (kbr_hj_bots_spear: each bot blocks it as well as it
    # plays) - once per spear, where Chapter 4 decides a block
    sp = B.files['gml_Object_obj_hj_spear_Other_10.gml']
    a = 'if (len < shieldradius && dontblockshell == false && '
    assert sp.count(a) == 1, 'spear block test'
    sp = sp.replace(a, 'if (len < shieldradius && !variable_instance_exists(id, "kbr_hjb"))\n{\n    kbr_hjb = 1;\n    kbr_hj_bots_spear(redhammer);\n}\n' + a, 1)
    B.files['gml_Object_obj_hj_spear_Other_10.gml'] = sp
    # ---- a sent bell attack's end brings no Gerson back (his teleport-back is his own fight's)
    bc = B.files['gml_Object_obj_hj_bellctrl_CleanUp_0.gml']
    a = 'gers = instance_create(kbr_hj_gv("x") + 45, kbr_hj_gv("y") + 45, obj_hj_teleport);\ngers.type = 10;'
    assert a in bc, 'bellctrl cleanup'
    bc = bc.replace(a, 'if (!(variable_instance_exists(id, "kbrx") && kbrx > 0))\n{\n    gers = instance_create(kbr_hj_gv("x") + 45, kbr_hj_gv("y") + 45, obj_hj_teleport);\n    gers.type = 10;\n}')
    B.files['gml_Object_obj_hj_bellctrl_CleanUp_0.gml'] = bc
    sn = B.sendable(guard=('obj_hj_shellkick', 'obj_hj_boxthrow'), keep_soul=('obj_hj_shield', 'obj_hj_spear', 'obj_hj_shieldpiece', 'obj_hj_justpart', 'obj_hj_fakeheart', 'obj_hj_chevron', 'obj_hj_switch'))
    print('gerson sendable: %d Creates, %d events, %d turn-timer reads, %d guarded writes' % sn)
    # ---- the box throw's landing pulls the SOUL into the box one pixel at a time, straight at the box's middle (Chapter 4: a
    # while loop in one frame): at most as many steps as the SOUL is from that middle (it is inside the box by then), so a SOUL
    # that never meets the box mask can never hang the game - and only in the game whose SOUL it is
    bt = 'gml_Object_obj_hj_boxthrow_Step_2.gml'
    a0 = '                while (!position_meeting(obj_heart.x + 10, obj_heart.y + 10, id))\n                {\n'
    assert B.files[bt].count(a0) == 1, 'box throw loop'
    B.files[bt] = B.files[bt].replace(a0, '                var _hjn = ceil(point_distance(obj_heart.x + 10, obj_heart.y + 10, x, y)) + 2;\n                while (kbr_mine() && _hjn > 0 && !position_meeting(obj_heart.x + 10, obj_heart.y + 10, id))\n                {\n                    _hjn--;\n')
    # ---- Gerson's battle object and the background: the hub's own code (online_gerson53.gml)
    B.files['gml_Object_obj_hj_gerson_Create_0.gml'] = 'kbr_hj_create();\n'
    B.files['gml_Object_obj_hj_gerson_Step_0.gml'] = 'kbr_hj_step();\n'
    B.files['gml_Object_obj_hj_gerson_Draw_0.gml'] = 'kbr_hj_draw();\n'
    B.files['gml_Object_obj_hj_bg_Create_0.gml'] = 'kbr_hj_bg_create();\n'
    B.files['gml_Object_obj_hj_bg_Step_0.gml'] = 'kbr_hj_bg_step();\n'
    B.files['gml_Object_obj_hj_bg_Draw_0.gml'] = 'kbr_hj_bg_draw();\n'
    B.files['gml_Object_obj_drbr_none_Create_0.gml'] = '// DRBR: the stand-in for objects of another chapter that are not imported: never kept\ninstance_destroy();\n'
    # sprites named by the hub's own code
    for s in EXTRA_SPR:
        assert s in B.S['spr'], s
        B.sprites.add(s)
    left = [(n, x) for n, t in B.files.items() for x in re.findall(r'\b(obj_hammer_of_justice_enemy|obj_spearshot|obj_spearblocker\b|obj_gerson_\w+|scr_spear\w+)', t)]
    assert not left, left[:5]
    B.write(OUT)
    sprs, snds = B.manifest(extra_snd=EXTRA_SND)
    print('gerson: %d code files, %d sprites, %d sounds, %d objects' % (len(B.files), len(sprs), len(snds), len(OBJ)))
    return B


if __name__ == '__main__':
    main()
