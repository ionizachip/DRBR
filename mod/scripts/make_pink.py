"""DRBR: PINK (DELTARUNE Chapter 5's secret boss, encounter 224) - her pieces from the player's own Chapter 5 data.win
(MODS_DIR/c5.win, decompiled to /home/claude/work/src/c5). See make_boss.py for the common rules and online/notes/src_pink.md for
the source survey (section 7: the port plan).

Taken as they are (renamed obj_pk_*, spr_pk_*): the PURPLE SOUL's engine (obj_purplecontrols: the lanes, the bomb grid, the
rolling box, the 3D tunnel, the node maze), Pink inside the battle (obj_pink_battlemovement: the ball jump onto the box, the bomb
throws, the stage), her cats, hearts, fuse bombs and their explosions, the rolling box's lane bullets and the ghost's huge face,
the tunnel's zaps, the concert (curtains, fans, haters), the effects; obj_dbulletcontroller's types 199-210 as obj_pk_dbc.
Changed where Chapter 3 / the shared timeline differ (see main() for each, with its reason):
  - her battle object (obj_pink_enemy: talk, ACTs, DOKI, dates) is the hub's (online_pink53.gml: obj_pk_pink);
  - team damage (her bombs: a share of every member's HP) -> one hit through the room's table;
  - the HEARTS (Chapter 5: TP and the TP cap) -> the online gauge;
  - the tunnel's tutorial pause (waits for the player's UP) is off; the bomb dial is the room's HARD ATTACKS;
  - randomness: each piece's own stream (kbr_p_*), as Spamton's (a kicked bomb in one game never moves another game's cats)."""
import os, re, sys
sys.path.insert(0, '/home/claude/scripts')
from make_boss import Boss, block_at

OUT = '/home/claude/scripts/pink_gen/'
OBJ = {
    'obj_pink_enemy': 'obj_pk_pink', 'obj_dbulletcontroller': 'obj_pk_dbc',
    'obj_purplecontrols': 'obj_pk_purple', 'obj_pink_battlemovement': 'obj_pk_move', 'obj_pinkcatbullet': 'obj_pk_cat',
    'obj_dokiheart': 'obj_pk_doki', 'obj_fusebomb': 'obj_pk_bomb', 'obj_fusebomb_big': 'obj_pk_bigbomb',
    'obj_pinkbombexplosion': 'obj_pk_boom', 'obj_pinkmeteorfire': 'obj_pk_smoke', 'obj_pinkchargeball': 'obj_pk_chargeball',
    'obj_fx_pinkchargestar': 'obj_pk_chargestar', 'obj_pinklanebullet': 'obj_pk_lanebullet', 'obj_huge_anime_face': 'obj_pk_face',
    'obj_pinkmeteor': 'obj_pk_meteor', 'obj_explosion_flamingbit': 'obj_pk_flamebit', 'obj_purplebg': 'obj_pk_rollbg',
    'obj_pinkzap': 'obj_pk_zap', 'obj_pink3durgenter': 'obj_pk_rim', 'obj_pinktimeoutzap': 'obj_pk_zapring',
    'obj_pink_curtains': 'obj_pk_curtains', 'obj_audience_hitbox': 'obj_pk_fan', 'obj_audienceheart': 'obj_pk_fanheart',
    'obj_audiencehater': 'obj_pk_hater', 'obj_pinkdust': 'obj_pk_dust', 'obj_pinktrail': 'obj_pk_trail',
    'obj_fx_purpleripple': 'obj_pk_ripple', 'obj_sweatdrop': 'obj_pk_sweat', 'obj_purple_tea': 'obj_pk_tea',
    'obj_pinknode': 'obj_pk_node', 'obj_pinknodeact': 'obj_pk_nodeact', 'obj_roundbellbullet': 'obj_pk_bell',
    'obj_fx_pinksparkle': 'obj_pk_sparkle', 'obj_buzzsaw': 'obj_pk_saw', 'obj_pinkhealheart': 'obj_pk_healheart',
    # the hub's own (online_pink53.gml): the stage behind her
    '@bg': 'obj_pk_bg',
}
TAKE = [o for o in OBJ if not o.startswith('@') and o not in ('obj_pink_enemy', 'obj_dbulletcontroller')]
# her attack types in obj_dbulletcontroller (the ones her fight uses, and the unused ones the sends take pieces from)
TYPES = [199, 200, 201, 202, 203, 204, 205, 206, 207, 208, 209, 210]
KEEP_SPR = {'spr_heart', 'spr_dodgeheart', 'spr_dodgeheartmask', 'spr_nothing', 'spr_whitepixel', 'spr_pxwhite', 'spr_pixel_white',
            'spr_grazemask', 'spr_heartbullet', 'spr_heartoutline', 'spr_dust1', 'spr_explosion_round', 'spr_bhero_flame'}


def sub(t, a, b, n=1, what=''):
    c = t.count(a)
    assert c == n, ('%s: %r found %d times (want %d)' % (what, a[:70], c, n))
    return t.replace(a, b)


def piece_random(t):
    """a piece's own draws -> its own stream (kbr_p_*: drbr53.gml)"""
    t = re.sub(r'(?<![\w.])irandom_range\(', 'kbr_p_irandom_range(', t)
    t = re.sub(r'(?<![\w.])random_range\(', 'kbr_p_random_range(', t)
    t = re.sub(r'(?<![\w.])irandom\(', 'kbr_p_irandom(', t)
    t = re.sub(r'(?<![\w.])random\(', 'kbr_p_random(', t)
    t = re.sub(r'(?<![\w.])choose\(', 'kbr_p_choose(', t)
    t = re.sub(r'(?<![\w.])ds_list_shuffle\(', 'kbr_p_list_shuffle(', t)
    t = re.sub(r'(?<![\w.])scr_array_shuffle\(', 'kbr_p_array_shuffle(', t)
    return t


def rewrite_reads(t):
    """obj_pk_pink.f reads -> kbr_pk_gv("f"); her writes -> with (obj_pk_pink)"""
    t = re.sub(r'^([ ]*)obj_pk_pink\.(\w+)(\+\+|--);$', r'\1with (obj_pk_pink)\n\1    \2\3;', t, flags=re.M)
    t = re.sub(r'^([ ]*)obj_pk_pink\.(\w+) ([-+*/]?=) (.+);$', lambda m: '%svar _pkw = %s;\n%swith (obj_pk_pink)\n%s    %s %s _pkw;' % (m.group(1), m.group(4), m.group(1), m.group(1), m.group(2), m.group(3)), t, flags=re.M)
    t = re.sub(r'\bobj_pk_pink\.(\w+)\b(?!\s*(=[^=]|\+=|-=|\*=|/=|\+\+|--|\[))', r'kbr_pk_gv("\1")', t)
    return t


def dbc_step(B):
    t = B.code('gml_Object_obj_dbulletcontroller_Step_0')
    head = t[:t.index('btimer += 1;')]
    parts = []
    got = set()
    for m in re.finditer(r'^if \(type == (\d+)\)\s*$', t, re.M):
        a = int(m.group(1))
        if a in TYPES:
            s, e = block_at(t, m.end())
            parts.append(m.group(0) + '\n' + t[s:e])
            got.add(a)
    missing = [x for x in TYPES if x not in got]
    assert not missing, ('Pink types not in obj_dbulletcontroller', missing)
    return head + 'btimer += 1;\n' + '\n'.join(parts) + '\n'


# sprites the hub's own code names (online_pink53.gml: her body, the stage) and the fuse sprites Chapter 5 names by NUMBER
EXTRA_SPR = ['spr_pink_idle', 'spr_pink_laugh', 'spr_pink_front_ohoho', 'spr_pink_front_surprised', 'spr_pink_shocked', 'spr_pink_yelling',
             'spr_pink_peace_sign', 'spr_pink_ball', 'spr_fusebomb_burning', 'spr_fusebomb_burning_fast', 'spr_pink_spotlight_pink',
             'spr_pink_bg_dummy', 'spr_pink_bg_dummy_glowstick', 'spr_pink_fg_dummy', 'spr_purpleheart', 'spr_dokiheart', 'spr_bullet_catface',
             'spr_fusebomb', 'spr_fusebomb_big', 'spr_pinklanebullet_animation', 'spr_pinkzap', 'spr_spin_petal']
EXTRA_SND = ['snd_pink_laugh_short', 'snd_pink_laugh_long', 'snd_pink_gasp']

DOKI_GLOW = """        if (i_ex(obj_drbr_none))
        {
            with (obj_drbr_none)
            {
                alphamod = 1;
            }
        }
        else
        {
            instance_create_depth(0, 0, 0, obj_drbr_none);
        }
"""


def main():
    B = Boss('pink', 'c5', 'pk', OBJ, keep_spr=KEEP_SPR, local=set(OBJ))
    for o in TAKE:
        B.take(o)
    F = B.files
    B.shell('obj_dbulletcontroller')
    F['gml_Object_obj_pk_dbc_Step_0.gml'] = B.fix(dbc_step(B), det=False)
    F['gml_Object_obj_pk_dbc_Create_0.gml'] = B.fix(B.code('gml_Object_obj_dbulletcontroller_Create_0'), det=False)
    B.shell('obj_pink_enemy')
    dc = 'gml_Object_obj_pk_dbc_Create_0.gml'
    # (Chapter 5's other fights' notes in the shared controller: never hers)
    F[dc] = re.sub(r'\nif \(save_kris_hp == global\.hp\[1\].*\Z', '\n', F[dc], flags=re.S)
    F[dc] = sub(F[dc], 'if (i_ex(obj_drbr_none))\n{\n    timepoints = 1;\n}\n', '', 1, 'dbc aqua')
    F[dc] = re.sub(r'if \(scr_monsterpop\(\) == 2\)\n\{\n    ratio = 1\.6;\n\}\nif \(scr_monsterpop\(\) == 3\)\n\{\n    ratio = 2\.3;\n\}\n', '', F[dc])
    F[dc] = re.sub(r'if \(!variable_global_exists\("__debugHide"\)\)\n\{\n    global\.__debugHide = 0;\n\}\nhide = 1;\nhideamt = global\.__debugHide;\n', 'hide = 1;\nhideamt = 0;\n', F[dc])
    assert '__debug' not in F[dc] and 'obj_drbr_none' not in F[dc] and 'scr_monsterpop' not in F[dc], F[dc]
    # ---- team damage (her bombs and their blasts: a share of every member's HP, through her user event 2) -> one hit through
    # the room's table, like every bullet (obj_regularbullet's own hit event)
    for n in ('gml_Object_obj_pk_bomb_Other_15.gml', 'gml_Object_obj_pk_boom_Other_15.gml'):
        assert 'teamdamage' in F[n], n
        F[n] = 'if (active == 1)\n{\n    event_inherited();\n}\n'
    # ---- the HEARTS: Chapter 5 heals 1 HP and raises the TP cap / TP (her fight's own economy, ACTs and dates); online they
    # charge your gauge and heal a little (kbr_pk_heart: the room's GRAZE CHARGE / HEAL POWER)
    dk = 'gml_Object_obj_pk_doki_Step_0.gml'
    F[dk] = sub(F[dk], '        snd_play(snd_power);\n        scr_healall(1);\n', '        snd_play(snd_power);\n        kbr_pk_heart(tension_value);\n', 1, 'doki heal')
    i0 = F[dk].index('        with (obj_tensionbar)\n')
    i1 = F[dk].index('        snd_stop(snd_swallow);\n')
    F[dk] = F[dk][:i0] + F[dk][i1:]
    F[dk] = sub(F[dk], DOKI_GLOW, '', 1, 'doki glow')
    assert 'tension' not in F[dk].replace('tension_value', '') and 'scr_healall' not in F[dk], 'doki TP left'
    # ---- the bomb dial (a Chapter 5 NPC, a save flag: Default / Nicer / Meaner): the room's own (kbr_pk_dial) - every game the same
    nd = 0
    for n in list(F):
        F[n], k = re.subn(r'global\.flag\[1914\]', 'kbr_pk_dial()', F[n])
        nd += k
    assert nd >= 20, ('bomb dial', nd)
    # ---- DRBR 1.0.3: a SENT mega bomb's warning cross and its explosions stop at the box it lands in (kbr_pk_lim: the screen for
    # her own) - the MEGA BOMB skill's cross ran across the whole screen
    bd = 'gml_Object_obj_pk_bigbomb_Draw_0.gml'
    F[bd] = sub(F[bd], 'd_rectangle(camera_get_view_x(view_camera[0]), y - _thick, camera_get_view_x(view_camera[0]) + 640, y + _thick, 0);', 'd_rectangle(kbr_pk_lim(0), y - _thick, kbr_pk_lim(2), y + _thick, 0);', 1, 'bomb cross h')
    F[bd] = sub(F[bd], 'd_rectangle(x - _thick, camera_get_view_y(view_camera[0]), x + _thick, camera_get_view_y(view_camera[0]) + 480, 0);', 'd_rectangle(x - _thick, kbr_pk_lim(1), x + _thick, kbr_pk_lim(3), 0);', 1, 'bomb cross v')
    bs = 'gml_Object_obj_pk_bigbomb_Step_0.gml'
    F[bs] = sub(F[bs], 'until (_xx < camera_get_view_x(view_camera[0]) || _xx > (camera_get_view_x(view_camera[0]) + 640) || _yy < camera_get_view_y(view_camera[0]) || _yy > (camera_get_view_y(view_camera[0]) + 480));', 'until (_xx < kbr_pk_lim(0) || _xx > kbr_pk_lim(2) || _yy < kbr_pk_lim(1) || _yy > kbr_pk_lim(3));', 1, 'bomb chain')
    # (the fuse bombs' the same: their warning lines and explosion rows)
    fd = 'gml_Object_obj_pk_bomb_Draw_0.gml'
    F[fd] = sub(F[fd], 'd_rectangle(camera_get_view_x(view_camera[0]), y - _thick, camera_get_view_x(view_camera[0]) + 640, y + _thick, 0);', 'd_rectangle(kbr_pk_lim(0), y - _thick, kbr_pk_lim(2), y + _thick, 0);', 1, 'fuse cross h')
    F[fd] = sub(F[fd], 'd_rectangle(x - _thick, camera_get_view_y(view_camera[0]), x + _thick, camera_get_view_y(view_camera[0]) + 480, 0);', 'd_rectangle(x - _thick, kbr_pk_lim(1), x + _thick, kbr_pk_lim(3), 0);', 1, 'fuse cross v')
    fs = 'gml_Object_obj_pk_bomb_Step_0.gml'
    F[fs] = sub(F[fs], 'until (_xx < camera_get_view_x(view_camera[0]) || _xx > (camera_get_view_x(view_camera[0]) + 640) || _yy < camera_get_view_y(view_camera[0]) || _yy > (camera_get_view_y(view_camera[0]) + 480));', 'until (_xx < kbr_pk_lim(0) || _xx > kbr_pk_lim(2) || _yy < kbr_pk_lim(1) || _yy > kbr_pk_lim(3));', 1, 'fuse chain')
    # ---- the fuse sprites Chapter 5 names by their NUMBER (5129, 7112): by name
    for n in ('gml_Object_obj_pk_bomb_Draw_0.gml', 'gml_Object_obj_pk_bigbomb_Draw_0.gml'):
        F[n] = sub(F[n], '_burnsprite = 7112;', '_burnsprite = spr_pk_fusebomb_burning_fast;', 1, n)
        F[n] = sub(F[n], '_burnsprite = 5129;', '_burnsprite = spr_pk_fusebomb_burning;', 1, n)
    # ---- Chapter 5's scr_wrap (an inclusive range; called with ONE argument in the rolling box - then it changes nothing) and
    # scr_shakescreen(strength) (Chapter 3's takes none)
    # (the arguments are split at their top-level commas: `scr_wrap(_dir + (_diradd * choose(1, 2)))` is ONE argument)
    nw = n1 = 0
    for n in list(F):
        t = F[n]
        while True:
            m = re.search(r'\bscr_wrap\(', t)
            if not m:
                break
            i = m.end()
            d = 1
            j = i
            cut = []
            while d:
                c = t[j]
                if c == '"':
                    j = t.index('"', j + 1)
                elif c in '([{':
                    d += 1
                elif c in ')]}':
                    d -= 1
                elif c == ',' and d == 1:
                    cut.append(j)
                j += 1
            inner = t[i:j - 1]
            if not cut:
                t = t[:m.start()] + '(' + inner + ')' + t[j:]
                n1 += 1
            else:
                t = t[:m.start()] + 'kbr_pk_wrap(' + inner + ')' + t[j:]
            nw += 1
        F[n] = re.sub(r'\bscr_shakescreen\((\d+)\)', r'kbr_pk_shake(\1)', t)
    assert nw >= 10 and n1 >= 2, ('scr_wrap', nw, n1)
    assert not [n for n in F if 'scr_wrap(' in F[n]]
    # ---- the purple SOUL's keys: never while you watch, type in the chat or have the quick settings open
    pp = 'gml_Object_obj_pk_purple_Step_0.gml'
    for k, v in (('left', 'l'), ('right', 'r'), ('up', 'u'), ('down', 'd')):
        F[pp] = sub(F[pp], '%s_h()' % k, 'kbr_pk_in_h("%s")' % v, 1, 'purple key ' + k)
        F[pp] = sub(F[pp], '%s_p()' % k, 'kbr_pk_in_p("%s")' % v, 1, 'purple key ' + k)
    # ---- the tunnel's tutorial pause (it freezes the tunnel until the player presses UP, stretching the turn): off - every game's
    # tunnel moves on the same frames
    F[pp] = sub(F[pp], 'tutorial_time = 300;', 'tutorial_time = 0;', 1, 'tunnel tutorial')
    # ---- her date's maze reads the date count (always the last date here)
    na = 'gml_Object_obj_pk_nodeact_Step_0.gml'
    F[na] = sub(F[na], 'if (obj_pk_pink.datecount > 1)', 'if (true)', 1, 'maze datecount')
    # ---- every piece's draws: its own stream (Draw events are looks only here: GameMaker's own generator)
    for n in list(F):
        if '_Draw_' in n:
            continue
        F[n] = piece_random(F[n])
    # ---- reads of her battle object (a send may run a piece with her off stage)
    for n in list(F):
        F[n] = rewrite_reads(F[n])
    B.finish(no_vars=('obj_pk_purple', 'obj_pk_move', 'obj_pk_dbc'), no_guard=('obj_pk_purple', 'obj_pk_move', 'obj_pk_dbc'))
    for n in list(F):
        F[n] = rewrite_reads(F[n])
    # ---- the pieces her SENDS use: adopted by the send that makes them; their own stream right after
    sn = B.sendable(skip=('obj_pk_pink', 'obj_pk_dbc', 'obj_pk_purple', 'obj_pk_move', 'obj_pk_rollbg', 'obj_pk_face', 'obj_pk_meteor', 'obj_pk_node',
                          'obj_pk_nodeact', 'obj_pk_tea', 'obj_pk_curtains'),
                    guard=('obj_pk_pink', 'obj_pk_purple', 'obj_pk_move', 'obj_pk_dbc'))
    print('pink sendable: %d Creates, %d events, %d turn-timer reads, %d guarded writes' % sn)
    nb = 0
    for n in list(F):
        if re.match(r'gml_Object_obj_pk_\w+_Create_0\.gml$', n) and not n.startswith('gml_Object_obj_pk_pink_'):
            tt = F[n]
            if tt.startswith('kbr_ev_cr();\n'):
                F[n] = 'kbr_ev_cr();\nkbr_p_born();\n' + tt[len('kbr_ev_cr();\n'):]
            else:
                F[n] = 'kbr_p_born();\n' + tt
            nb += 1
    # ---- her battle object and the stage: the hub's own code (online_pink53.gml)
    # ---- a SENT bomb (online_pink53.gml's FUSE BOMBS / MEGA BOMB, in the target's own box) is not on her 4x4 bomb grid: a kick
    # never wraps it round the grid (200 px across the box), and another blast never sets it off early (its fuse is what the
    # target was shown) - her own bombs (kbr_mine()) keep Chapter 5's rules
    bs = 'gml_Object_obj_pk_bomb_Step_0.gml'
    for c in ('if (grid_x < 0)', 'else if (grid_x > 3)', 'if (grid_y < 0)', 'else if (grid_y > 3)'):
        F[bs] = sub(F[bs], '                %s\n' % c, '                %s\n' % c.replace(')', ' && kbr_mine())'), 1, 'bomb wrap ' + c)
    for n in (bs, 'gml_Object_obj_pk_bigbomb_Step_0.gml'):
        F[n] = sub(F[n], '        if (inside_the_grid)\n        {\n            fuse_time = min(fuse_time, 3);', '        if (inside_the_grid && kbr_mine())\n        {\n            fuse_time = min(fuse_time, 3);', 1, 'bomb chain ' + n)
    F['gml_Object_obj_pk_pink_Create_0.gml'] = 'kbr_pk_create();\n'
    F['gml_Object_obj_pk_pink_Step_0.gml'] = 'kbr_pk_step();\n'
    F['gml_Object_obj_pk_pink_Draw_0.gml'] = 'kbr_pk_draw();\n'
    F['gml_Object_obj_pk_bg_Create_0.gml'] = 'kbr_pk_bg_create();\n'
    F['gml_Object_obj_pk_bg_Step_0.gml'] = 'kbr_pk_bg_step();\n'
    F['gml_Object_obj_pk_bg_Draw_0.gml'] = 'kbr_pk_bg_draw();\n'
    F['gml_Object_obj_drbr_none_Create_0.gml'] = '// DRBR: the stand-in for objects of another chapter that are not imported: never kept\ninstance_destroy();\n'
    left = [(n, x) for n, tt in F.items() for x in re.findall(r'\b(obj_pink_enemy|obj_dbulletcontroller|obj_purplecontrols|obj_fusebomb\w*|obj_pink\w+|e__VW|obj_date_\w+)',
                                                              re.sub(r'"[^"\n]*"', '""', tt))]
    assert not left, left[:6]
    # ---- 1.0.1: her line while she is in the battle herself (her own object is hidden then; obj_pk_move shows her)
    mv = 'gml_Object_obj_pk_move_Draw_0.gml'
    F[mv] = F[mv].rstrip('\n') + '\nkbr_pk_move_say();\n'
    for s in EXTRA_SPR:
        assert s in B.S['spr'], s
        B.sprites.add(s)
    print('pink: %d files, %d piece streams' % (len(F), nb))
    B.write(OUT)
    sprs, snds = B.manifest(extra_snd=EXTRA_SND)
    print('pink: %d code files, %d sprites, %d sounds %s, %d objects' % (len(F), len(sprs), len(snds), snds, len(OBJ)))
    return B


if __name__ == '__main__':
    main()
