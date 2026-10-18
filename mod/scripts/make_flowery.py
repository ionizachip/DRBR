"""DRBR: FLOWERY (DELTARUNE Chapter 5's boss, encounter 225) - his pieces from the player's own Chapter 5 data.win
(MODS_DIR/c5.win, decompiled to /home/claude/work/src/c5). See make_boss.py for the common rules and online/notes/src_flowery.md
for the source survey (its section numbers are quoted below).

Taken as they are (renamed obj_fl_*): the ORANGE SOUL (obj_orangeheart: hold Z to charge, let go to DASH; up / down only) and its
board (obj_debug_orangeheartcontroller: the scrolling course, its lines, the spawning), every hazard (bamboo / vases / cacti /
petals, bullets, lilypads, the thorn wall, Blue's flowers and Yellow's beam, Seth's boxes / book / words, the word flower),
Flowery's Jarona lunges and decoys (obj_orangeheart_floweryjarona), the C5 helpers they use (obj_marker_fancy / _fog /
_centerpoint, C5's obj_particle_generic) and the tower background (obj_flowery_towery, its pillars, decorations and petals,
with Chapter 5's own shaders). The attack set-ups of obj_dbulletcontroller (types 620-641) become kbr_fl_build().
Changed where Chapter 3 / the shared timeline differ (section 7.2):
  - the decompiler's raw asset numbers (6.6) -> names;
  - the course (the board's spawning) draws from the attack's own stream (kbr_fl_*random: the same course in every game, whatever
    each player's dashes did); everything else (a hit, a parry, a Jarona's wait) keeps the game's own randomness (local outcomes);
  - global.time (the save's play time in Chapter 5: different in every game) -> global.kbr_fl_t, the attack's own clock;
  - the turn-timer writes (6.7) only note where Chapter 5 would have ended the turn (kbr_fl_done); the timeline's cut ends it;
  - the dash tutorial (difficulty 7: balloons, a spotlight) is not part of an online attack;
  - Flowery's battle object (obj_flowery_enemy) -> obj_fl_flowery (the hub's, online_flowery53.gml), read through kbr_fl_gv()
    so a send can use the pieces while a knight is on stage;
  - the SOUL's clean-up no longer destroys every obj_marker / obj_afterimage in the room (only the board's);
  - a Jarona copy made at cameray() + 500 (Chapter 5's camera is at 0, 0) -> camerax() + 500.
Usage: python3 make_flowery.py"""
import os, re, sys
sys.path.insert(0, '/home/claude/scripts')
from make_boss import Boss, block_at, SRC

OUT = '/home/claude/scripts/flowery_gen/'
OBJ = {
    'obj_orangeheart': 'obj_fl_soul', 'obj_debug_orangeheartcontroller': 'obj_fl_ctrl', 'obj_orangeheart_hazard': 'obj_fl_hazard',
    'obj_orangeheart_wall': 'obj_fl_wall', 'obj_orangeheart_bullet': 'obj_fl_bullet', 'obj_orangeheart_bullet_word': 'obj_fl_word',
    'obj_orangeheart_bullet_orbit': 'obj_fl_orbit', 'obj_orangeheart_jumppad': 'obj_fl_pad', 'obj_orangeheart_chaseattack': 'obj_fl_thorns',
    'obj_orangeheart_wallflower': 'obj_fl_bloom', 'obj_orangeheart_floweryjarona': 'obj_fl_jarona', 'obj_orangeheart_square': 'obj_fl_box',
    'obj_orangeheart_word_manager': 'obj_fl_book', 'obj_orangeheart_collectible': 'obj_fl_pickup', 'obj_orangeheart_helpful_flower': 'obj_fl_wordflower',
    'obj_yellow_beam': 'obj_fl_beam', 'obj_marker_fancy': 'obj_fl_mfancy', 'obj_marker_fog': 'obj_fl_mfog', 'obj_marker_centerpoint': 'obj_fl_mcenter',
    'obj_particle_generic': 'obj_fl_particle', 'obj_flowery_enemy': 'obj_fl_flowery', 'obj_flowery_towery': 'obj_fl_towery',
    'obj_flowery_towery_pillars': 'obj_fl_pillars', 'obj_flowery_tower_decoration': 'obj_fl_towerdeco', 'obj_towery_particle': 'obj_fl_tparticle',
    'obj_flowery_marker': 'obj_fl_friend',
}
NOT_TAKEN = ('obj_flowery_enemy', 'obj_flowery_marker')
TAKE = [o for o in OBJ if o not in NOT_TAKEN]
# none of the pieces draws from the shared stream: the course (the board) has the attack's own stream (course_random), the rest
# keep the game's own randomness (local outcomes: a hit, a parry, a Jarona's wait)
LOCAL = set(OBJ)
# the attack set-ups the encounter uses (section 2.4) and the optional harder ones
TYPES = [620, 621, 622, 623, 624, 625, 626, 630, 631, 632, 633, 634, 635, 636, 638, 639, 640, 641]
KEEP_SPR = {'spr_heart', 'spr_dodgeheart', 'spr_nothing', 'spr_whitepixel', 'spr_pxwhite', 'spr_pixel_white', 'spr_thrash_slash',
            'spr_battlebg_0', 'spr_sneo_bullet_arrow', 'spr_yheart_charge', 'spr_spin_petal', 'spr_rouxls_ripple', 'spr_bellsparkle',
            'spr_cakesmoke', 'spr_sparestar_anim'}
# Chapter 5 scripts Chapter 3 lacks, copied whole (their own names)
SCRIPT_FILES = ['scr_marker_fog', 'scr_dark_marker_fancy', 'scr_marker_centered', 'draw_self_ext', 'shader_replace_simple_macros']
# Flowery's look written for the hub (online_flowery53.gml) uses these besides the ones in the taken code
EXTRA_SPR = ['spr_flowery_idle3', 'spr_flowery_hurt', 'spr_flowery_kiss', 'spr_flowery_thumbs_down', 'spr_flowery_idle3_blush',
             'spr_flowery_wind', 'spr_flowery_condescend', 'spr_flowery_shake_head', 'spr_flowery_shrug_spin', 'spr_flowery_jump_left',
             'spr_seth_idle_serious_flowery', 'spr_seth_idle_dizzy_flowery', 'spr_enemy_aqua_spin', 'spr_enemy_aqua_idle',
             'spr_enemy_orange_flowery_angry', 'spr_green_together', 'spr_enemy_green_witharmandpan_flowery', 'spr_enemy_blue_ballet',
             'spr_blue_hover', 'spr_yellow_cool_fall_armsraised', 'spr_yellow_cool_landing', 'spr_yellow_jump', 'spr_orangeheart_white',
             'spr_towery_vines', 'spr_towery_vines_depth']
SHADERS = {'shd_depthmap': 'shd_fl_depthmap', 'shd_tower': 'shd_fl_tower', 'shd_fakedepth_tower': 'shd_fl_fakedepth_tower',
           'shd_brightness_to_alpha': 'shd_fl_brightness_to_alpha', 'shd_overlay_blend': 'shd_fl_overlay_blend'}
EXTRA_SND = ['snd_whack_absurdlyloud', 'snd_forthefans', 'snd_jarona_orange1', 'snd_jarona_orange2', 'snd_parry_fast_nodelay', 'snd_splash']


def idx_tables():
    t = {'obj': [], 'spr': [], 'snd': [], 'shd': []}
    for l in open(SRC + 'c5/assets.tsv', encoding='utf8'):
        r = l.rstrip('\n').split('\t')
        if r[0] in t:
            t[r[0]].append(r[1])
    return t


def sub1(t, a, b, n=1, fname=''):
    c = t.count(a)
    assert c == n, ('expected %d x %r in %s, found %d' % (n, a, fname, c))
    return t.replace(a, b)


def course_random(t):
    """the board's own draws (its course) -> the attack's stream (kbr_fl_*: online_flowery53.gml)"""
    t = re.sub(r'(?<![\w.])irandom_range\(', 'kbr_fl_irandom_range(', t)
    t = re.sub(r'(?<![\w.])random_range\(', 'kbr_fl_random_range(', t)
    t = re.sub(r'(?<![\w.])irandom\(', 'kbr_fl_irandom(', t)
    t = re.sub(r'(?<![\w.])random\(', 'kbr_fl_random(', t)
    t = re.sub(r'(?<![\w.])choose\(', 'kbr_fl_choose(', t)
    t = re.sub(r'(?<![\w.])ds_list_shuffle\(', 'kbr_fl_list_shuffle(', t)
    return t


def rewrite_reads(t):
    """obj_fl_flowery.f reads -> kbr_fl_gv("f"); writes -> with (obj_fl_flowery)"""
    t = re.sub(r'^([ ]*)obj_fl_flowery\.(\w+)(\+\+|--);$', r'\1with (obj_fl_flowery)\n\1    \2\3;', t, flags=re.M)
    t = re.sub(r'^([ ]*)obj_fl_flowery\.(\w+) ([-+*/]?=) (.+);$', lambda m: '%svar _flw = %s;\n%swith (obj_fl_flowery)\n%s    %s %s _flw;' % (m.group(1), m.group(4), m.group(1), m.group(1), m.group(2), m.group(3)), t, flags=re.M)
    t = re.sub(r'\bobj_fl_flowery\.(\w+)\b(?!\s*(=[^=]|\+=|-=|\*=|/=|\+\+|--))', r'kbr_fl_gv("\1")', t)
    # a field of the instance one of his fields holds (his friends' markers): no accessor on a call's result for the compiler
    t = re.sub(r'kbr_fl_gv\("(\w+)"\)\.(\w+)', r'kbr_fl_gv2("\1", "\2")', t)
    return t


def main():
    IX = idx_tables()
    spr = lambda i: IX['spr'][i]
    snd = lambda i: IX['snd'][i]
    obj = lambda i: IX['obj'][i]
    shd = lambda i: IX['shd'][i]
    # the decompiler's numbers checked against their use (section 6.6)
    assert obj(745) == 'obj_debug_orangeheartcontroller' and obj(1022) == 'obj_orangeheart' and obj(921) == 'obj_flowery_towery', (obj(745), obj(1022), obj(921))
    assert snd(371) == 'snd_punchheavythunder', snd(371)
    B = Boss('flowery', 'c5', 'fl', OBJ, keep_spr=KEEP_SPR, local=LOCAL)
    for o in TAKE:
        B.take(o)
    F = B.files
    # ---- raw numbers -> names
    for n in list(F):
        t = F[n]
        t = t.replace('var controller = 745;', 'var controller = obj_fl_ctrl;')
        t = t.replace('var _towery = 921;', 'var _towery = obj_fl_towery;').replace('var _tower = 921;', 'var _tower = obj_fl_towery;')
        F[n] = t
    c = F['gml_Object_obj_fl_ctrl_Create_0.gml']
    c = sub1(c, 'heart = 1022;', 'heart = obj_fl_soul;', fname='ctrl Create')
    # (its stand-in SOUL when none was made: on the box, not the room's middle - the battle is not at the room's corner)
    c = sub1(c, 'heart = instance_create((camerax() + (room_width / 2)) - 160, cameray() + (room_height / 2), obj_fl_soul);',
             'heart = instance_create(scr_get_box(4) - 75, scr_get_box(5), obj_fl_soul);', fname='ctrl Create')
    F['gml_Object_obj_fl_ctrl_Create_0.gml'] = c
    s2 = F['gml_Object_obj_fl_ctrl_Step_2.gml']
    a = re.search(r'var tocheck = \[\];\n(\s*array_push\(tocheck, [\d, ]+\);\n)+', s2)
    assert a, 'tocheck'
    nums = [int(x) for x in re.findall(r'\d+', ', '.join(re.findall(r'array_push\(tocheck, ([\d, ]+)\)', a.group(0))))]
    names = [OBJ.get(obj(i), obj(i)) for i in nums]
    assert len(names) == 11 and 'obj_fl_wall' in names and 'obj_afterimage' in names, names
    s2 = s2[:a.start()] + 'var tocheck = [%s];\n' % ', '.join(names) + s2[a.end():]
    F['gml_Object_obj_fl_ctrl_Step_2.gml'] = s2
    bu = F['gml_Object_obj_fl_bullet_Step_0.gml']
    bu = sub1(bu, 'scr_script_delayed(snd_play, 6, 371, undefined, 1.2);', 'scr_script_delayed(snd_play, 6, snd_punchheavythunder, undefined, 1.2);', fname='bullet Step')
    F['gml_Object_obj_fl_bullet_Step_0.gml'] = bu
    j = F['gml_Object_obj_fl_jarona_Step_0.gml']
    for num in (704, 261, 150, 753, 68, 12, 40):
        j = re.sub(r'\[%d, round\(' % num, '[%s, round(' % snd(num), j)
    for num in (245, 40, 692, 124):
        j = j.replace('snd_play_flowery(%d' % num, 'snd_play_flowery(%s' % snd(num))
    # (the Final Jarona's "Hoo!" echo: Chapter 5's voice function passed to scr_script_delayed, with a raw sound number)
    j, nh = re.subn(r'scr_script_delayed\(snd_play_flowery, (\d+), (\d+)', lambda mm: 'scr_script_delayed(kbr_fl_voice, %s, %s' % (mm.group(1), snd(int(mm.group(2)))), j)
    assert nh == 3, ('hoo echo', nh)
    j = sub1(j, 'scr_var_delayed("sprite_index", 1706, 12);', 'scr_var_delayed("sprite_index", %s, 12);' % B.spr_new(spr(1706)), fname='jarona Step')
    B.sprites.add(spr(1706))
    for num in (704, 261, 150, 753, 68, 12, 40, 245, 692, 124):
        B.sounds.add(snd(num))
    F['gml_Object_obj_fl_jarona_Step_0.gml'] = j
    tw = F['gml_Object_obj_fl_towery_Create_0.gml']
    tw = sub1(tw, 'mapshader = 19;', 'mapshader = shd_fl_depthmap;', fname='towery')
    tw = sub1(tw, 'shader = 8;', 'shader = shd_fl_tower;', fname='towery')
    tw = sub1(tw, 'depth_shader = 11;', 'depth_shader = shd_fl_fakedepth_tower;', fname='towery')
    assert shd(19) == 'shd_depthmap' and shd(8) == 'shd_tower' and shd(11) == 'shd_fakedepth_tower', (shd(19), shd(8), shd(11))
    F['gml_Object_obj_fl_towery_Create_0.gml'] = tw
    dd = F['gml_Object_obj_fl_towerdeco_Draw_0.gml']
    assert shd(30) == 'shd_brightness_to_alpha' and shd(38) == 'shd_overlay_blend', (shd(30), shd(38))
    dd = sub1(dd, 'shader_replace_simple_set_hook(30);', 'shader_replace_simple_set_hook(shd_fl_brightness_to_alpha);', fname='deco Draw')
    F['gml_Object_obj_fl_towerdeco_Draw_0.gml'] = dd
    pd = F['gml_Object_obj_fl_tparticle_Draw_0.gml']
    pd = sub1(pd, 'shader_replace_simple_set_hook(38);', 'shader_replace_simple_set_hook(shd_fl_overlay_blend);', fname='particle Draw')
    F['gml_Object_obj_fl_tparticle_Draw_0.gml'] = pd
    pc = F['gml_Object_obj_fl_tparticle_Create_0.gml']
    m = re.search(r'sprites = \[([\d, ]+)\];', pc)
    assert m, 'particle sprites'
    sl = [spr(int(x)) for x in m.group(1).split(',')]
    for s in sl:
        B.sprites.add(s)
    pc = pc.replace(m.group(0), 'sprites = [%s];' % ', '.join(B.spr_new(s) for s in sl))
    F['gml_Object_obj_fl_tparticle_Create_0.gml'] = pc
    # ---- the tower's petals and decorations read the tower (obj_fl_towery.rotation ...): with no tower on (the match's end or a
    # pause switching it off first, a second tower's Create removing the first) they wait instead of failing
    n_tw = 0
    for ev in ('gml_Object_obj_fl_tparticle_Step_0.gml', 'gml_Object_obj_fl_tparticle_Draw_0.gml', 'gml_Object_obj_fl_towerdeco_Draw_0.gml',
               'gml_Object_obj_fl_towerdeco_Draw_76.gml', 'gml_Object_obj_fl_pillars_Draw_0.gml'):
        if ev in F and 'obj_fl_towery' in F[ev]:
            F[ev] = 'if (!instance_exists(obj_fl_towery))\n    exit;\n' + F[ev]
            n_tw += 1
    assert n_tw == 4, ('tower guards', n_tw)  # the petals' Step, the decorations' two Draws, the pillars' Draw
    # ---- the console borders (`if (global.console)`: Chapter 5 swaps the console version's screen border with the tower's
    # colours) - DRBR is the PC game's; the blocks name Chapter 5's border sprites (border_dw_castle_*), unknown names in Chapter 3
    pd = F['gml_Object_obj_fl_pillars_Draw_0.gml']
    nb = 0
    while '    if (global.console)\n' in pd:
        i = pd.index('    if (global.console)\n')
        s, e = block_at(pd, i + len('    if (global.console)\n'))
        while e < len(pd) and pd[e] == '\n':
            e += 1
        pd = pd[:i] + pd[e:]
        nb += 1
    assert nb == 4 and 'border_dw_' not in pd, ('console borders', nb)
    F['gml_Object_obj_fl_pillars_Draw_0.gml'] = pd
    # ---- the song's middle part's sunrise behind the pillars (Chapter 5's obj_parallax_cliffs_simple: 11 parallax layers, a sun)
    # is not ported: the pillars keep their own look through it
    pl = F['gml_Object_obj_fl_pillars_Step_0.gml']
    pl = sub1(pl, '    sunrise = instance_create_depth(x, y, depth + 2000, obj_drbr_none);\n    sunrise.visible = false;\n', '    sunrise = noone;\n', fname='pillars Step')
    F['gml_Object_obj_fl_pillars_Step_0.gml'] = pl
    # ---- the dash tutorial (difficulty 7) is not part of an online attack (section 7.2.6)
    st = F['gml_Object_obj_fl_ctrl_Step_0.gml']
    i7 = st.index('            case 7:\n')
    i8 = st.index('            case 8:\n')
    st = st[:i7] + '            case 7:\n                break;\n' + st[i8:]
    assert 'flowery_balloon' not in st and 'msgset' not in st, 'tutorial left'
    # the Jarona copy's place: Chapter 5's camera is at 0, 0 there (cameray() + 500 meant the screen's x 500)
    st = sub1(st, 'instance_create(cameray() + 500, ((boxbot + boxtop) / 2) - 59, obj_fl_jarona)', 'instance_create(camerax() + 500, ((boxbot + boxtop) / 2) - 59, obj_fl_jarona)', fname='ctrl Step')
    F['gml_Object_obj_fl_ctrl_Step_0.gml'] = st
    # ---- the SOUL's clean-up: only the board's markers and afterimages (not every one in the room: the HUD's, the sends')
    cu = F['gml_Object_obj_fl_soul_CleanUp_0.gml']
    cu = sub1(cu, 'with (obj_afterimage)\n{\n    instance_destroy();\n}', 'with (obj_afterimage)\n{\n    if (variable_instance_exists(id, "orangeheartControlled") && orangeheartControlled)\n        instance_destroy();\n}', fname='soul CleanUp')
    cu = sub1(cu, 'with (obj_marker)\n{\n    instance_destroy();\n}', 'with (obj_marker)\n{\n    if (variable_instance_exists(id, "orangeheartControlled") && orangeheartControlled)\n        instance_destroy();\n}', fname='soul CleanUp')
    F['gml_Object_obj_fl_soul_CleanUp_0.gml'] = cu
    # ---- the course's draws: the attack's own stream
    for n in list(F):
        if n.startswith('gml_Object_obj_fl_ctrl_') and '_Draw_' not in n:
            F[n] = course_random(F[n])
    # ---- a piece's own decisions (the Jarona's waits, tag-ins, fake-outs and bullet patterns; Seth's book's first word): its
    # own stream (kbr_fl_p_*: seeded by the cycle and the order it was made in; a sent one draws from its send's stream)
    n_pr = 0
    for n in ('gml_Object_obj_fl_jarona_Create_0.gml', 'gml_Object_obj_fl_jarona_Step_0.gml', 'gml_Object_obj_fl_book_Create_0.gml'):
        t0 = F[n]
        t1 = re.sub(r'(?<![\w.])irandom_range\(', 'kbr_fl_p_irandom_range(', t0)
        t1 = re.sub(r'(?<![\w.])random_range\(', 'kbr_fl_p_random_range(', t1)
        t1 = re.sub(r'(?<![\w.])irandom\(', 'kbr_fl_p_irandom(', t1)
        t1 = re.sub(r'(?<![\w.])random\(', 'kbr_fl_p_random(', t1)
        t1 = re.sub(r'(?<![\w.])choose\(', 'kbr_fl_p_choose(', t1)
        n_pr += len(re.findall(r'kbr_fl_p_', t1)) - len(re.findall(r'kbr_fl_p_', t0))
        F[n] = t1
    assert n_pr >= 30, ('piece draws', n_pr)
    # ---- the orange SOUL's keys (the game's own button1_h / up_h / down_h) through the hub: nothing while this game only
    # watches (its orange SOUL is then the followed player's puppet: kbr_fl_puppet)
    k1 = k2 = k3 = 0
    for n in list(F):
        if not n.startswith('gml_Object_obj_fl_'):
            continue
        t, a = re.subn(r'\bbutton1_h\(\)', 'kbr_fl_in_b1()', F[n])
        t, b = re.subn(r'\bup_h\(\)', 'kbr_fl_in_up()', t)
        t, c = re.subn(r'\bdown_h\(\)', 'kbr_fl_in_dn()', t)
        k1 += a
        k2 += b
        k3 += c
        F[n] = t
        assert not re.search(r'\b(button[123]_[hp]|up_[hp]|down_[hp]|left_[hp]|right_[hp])\(', t), ('another key read', n)
    assert k1 == 2 and k2 >= 3 and k3 >= 3, ('orange keys', k1, k2, k3)
    # ---- a sent Jarona (a player's JARONA / ORANGE & GREEN / LAST JARONA) lunges a set number of times, then leaves
    j = F['gml_Object_obj_fl_jarona_Step_0.gml']
    j, nl = re.subn(r'^(        )if \(timer == waittime\)\n', lambda mm: '%sif (timer == waittime && !kbr_fl_jr_more())\n%s    exit;\n%sif (timer == waittime)\n' % (mm.group(1), mm.group(1), mm.group(1)), j, flags=re.M)
    assert nl == 2, ('jarona lunge starts', nl)
    F['gml_Object_obj_fl_jarona_Step_0.gml'] = j
    # ---- the attack's own clock instead of the save's play time; the turn-timer writes only note Chapter 5's turn end
    n_tt = 0
    for n in list(F):
        F[n] = re.sub(r'\bglobal\.time\b', 'global.kbr_fl_t', F[n])
        t, k = re.subn(r'^([ ]*)global\.turntimer = ([\d.]+);\n', lambda mm: '' if float(mm.group(2)) >= 900 else '%skbr_fl_done(%s);\n' % (mm.group(1), mm.group(2)), F[n], flags=re.M)
        n_tt += k
        F[n] = t
    assert n_tt >= 6, ('turn-timer writes', n_tt)  # the controller's 70, the Jarona's four, the wall's 9999 (the tutorial's two went with it)
    # ---- Chapter 5's TP for the orange SOUL's dashes (breaks, parries, lilypads, word flowers) -> the hub's kbr_fl_tp: the
    # player's gauge and the GROUP MERCY's count (online_flowery53.gml); Chapter 3's TP bar shows the gauge online
    n_tp = 0
    for n in list(F):
        F[n], k = re.subn(r'\bscr_tensionheal\(', 'kbr_fl_tp(', F[n])
        n_tp += k
    assert n_tp == 8, ('tension heals', n_tp)
    # ---- Chapter 5 voice clips: snd_play_flowery (C5 mutes them by a C5 flag) -> the hub's kbr_fl_voice
    for n in list(F):
        F[n] = re.sub(r'\bsnd_play_flowery\(', 'kbr_fl_voice(', F[n])
        assert not re.search(r'\bsnd_play_flowery\b', re.sub(r'//[^\n]*', '', F[n])), ('snd_play_flowery left', n)
    # ---- the act menu's / enemy's C5 fields read through kbr_fl_gv (the hub's battle object, or its defaults for a send)
    for n in list(F):
        F[n] = rewrite_reads(F[n])
    # ---- rooms of Chapter 5 that are not here (the tower checks which room it is in): never this one
    for n in list(F):
        F[n] = re.sub(r'\broom_(dw_fcastle_\w+|plat_lab)\b', '-1', F[n])
    # ---- the C5 scripts Chapter 3 lacks
    for sname in SCRIPT_FILES:
        t = B.code('gml_GlobalScript_' + sname)
        assert t, sname
        F['gml_GlobalScript_%s.gml' % sname] = B.fix(t, det=False)
    # Chapter 5's shader hooks tell its renderer which shader is on (shader_replace_simple_sync: not a GML function - Chapter
    # 5's data.win brings it, Chapter 3's has no such name, and a call to it would stop the game): the hooks only set / reset
    sm = F['gml_GlobalScript_shader_replace_simple_macros.gml']
    sm, nsy = re.subn(r'^[ ]*shader_replace_simple_sync\([^;\n]*\);\n', '', sm, flags=re.M)
    assert nsy == 2 and 'shader_replace_simple_sync' not in sm, ('shader sync', nsy)
    F['gml_GlobalScript_shader_replace_simple_macros.gml'] = sm
    # Chapter 5's debug overlay lines (debug_print_persistent: a Chapter 5 name for an empty function; Chapter 3 only has
    # scr_debug_print_persistent): gone
    ndp = 0
    for n in list(F):
        F[n], k = re.subn(r'^[ ]*debug_print_persistent\([^;\n]*\);\n', '', F[n], flags=re.M)
        ndp += k
        assert not re.search(r'\bdebug_print_persistent\b', re.sub(r'//[^\n]*', '', F[n])), ('debug print left', n)
    assert ndp == 3, ('debug prints', ndp)
    # the C5 scr_script_delayed's companion (a function defined in that file; Chapter 3 has its own scr_script_delayed)
    sd = B.code('gml_GlobalScript_scr_script_delayed')
    mm = re.search(r'^function delay_function\(', sd, re.M)
    assert mm, 'delay_function'
    s0, e0 = block_at(sd, mm.end())
    F['gml_GlobalScript_kbr_fl_delay_function.gml'] = sd[mm.start():e0] + '\n'
    # ---- the attack set-ups (obj_dbulletcontroller's type blocks) as kbr_fl_build(_type)
    dbc = B.code('gml_Object_obj_dbulletcontroller_Step_0')
    body = []
    for ty in TYPES:
        mt = re.search(r'^if \(type == %d\)\s*$' % ty, dbc, re.M)
        assert mt, ty
        s1, e1 = block_at(dbc, mt.end())
        blk = dbc[s1:e1]
        mm2 = re.search(r'if \(!made\)\s*\{', blk)
        assert mm2, ('made', ty)
        s2_, e2_ = block_at(blk, mm2.start())
        inner = blk[s2_ + 1:e2_ - 1]
        inner = re.sub(r'^\s*made = true;\n', '', inner, flags=re.M)
        body.append('        case %d:\n%s\n            break;' % (ty, '\n'.join('    ' + l if l else l for l in inner.split('\n'))))
    fn = ('// DRBR (make_flowery.py): Chapter 5\'s attack set-ups (its bullet controller\'s blocks for types 620-641): the orange SOUL,\n'
          '// the board and its parameters. Run by Flowery\'s battle object (self) when an attack starts.\n'
          'function kbr_fl_build(_type)\n{\n    switch (_type)\n    {\n' + '\n'.join(body) + '\n    }\n    return 1;\n}\n')
    F['gml_GlobalScript_kbr_fl_build.gml'] = B.fix(fn, det=False)
    # ---- reads of the board / SOUL in the set-ups (Chapter 5's obj_dbulletcontroller ran them) are the same
    left = [(n, x) for n, t in F.items() for x in re.findall(r'\b(obj_orangeheart\w*|obj_debug_orangeheartcontroller|obj_flowery_enemy|obj_flowery_marker|obj_dbulletcontroller)\b', re.sub(r'"(?:\\.|[^"\\])*"', '""', t))]
    assert not left, left[:6]
    B.finish(no_vars=('obj_fl_mfancy', 'obj_fl_mfog', 'obj_fl_mcenter', 'obj_fl_particle', 'obj_fl_towery', 'obj_fl_pillars', 'obj_fl_towerdeco', 'obj_fl_tparticle'),
             no_guard=('obj_fl_towery', 'obj_fl_pillars', 'obj_fl_towerdeco', 'obj_fl_tparticle', 'obj_fl_soul'))
    for n in list(F):
        F[n] = rewrite_reads(F[n])
    sn = B.sendable(skip=('obj_fl_towery', 'obj_fl_pillars', 'obj_fl_towerdeco', 'obj_fl_tparticle'),
                    keep_soul=('obj_fl_soul', 'obj_fl_ctrl', 'obj_fl_box', 'obj_fl_jarona', 'obj_fl_wall', 'obj_fl_pad', 'obj_fl_thorns', 'obj_fl_bullet'))
    print('flowery sendable: %d Creates, %d events, %d turn-timer reads, %d guarded writes' % sn)
    # ---- Flowery's battle object and his friends: the hub's own code (online_flowery53.gml)
    F['gml_Object_obj_fl_flowery_Create_0.gml'] = 'kbr_fl_create();\n'
    F['gml_Object_obj_fl_flowery_Step_0.gml'] = 'kbr_fl_step();\n'
    F['gml_Object_obj_fl_flowery_Draw_0.gml'] = 'kbr_fl_draw();\n'
    F['gml_Object_obj_drbr_none_Create_0.gml'] = '// DRBR: the stand-in for objects of another chapter that are not imported: never kept\ninstance_destroy();\n'
    # ---- 1.0.1: his line while his Jarona copy stands in for him (he hides for those attacks)
    jd = 'gml_Object_obj_fl_jarona_Draw_0.gml'
    F[jd] = F[jd].rstrip('\n') + '\nkbr_fl_jarona_say();\n'
    for s in EXTRA_SPR:
        assert s in B.S['spr'], s
        B.sprites.add(s)
    B.write(OUT)
    sprs, snds = B.manifest(extra_snd=EXTRA_SND)
    # the tower's own shaders (build.csx copies them from the Chapter 5 game file: the same runner runs every chapter)
    import json
    from make_boss import ASSETS
    A = json.load(open(ASSETS))
    M = A['manifest']
    M['shaders'] = [m for m in M.get('shaders', []) if m.get('boss') != 'flowery']
    for a, b in SHADERS.items():
        M['shaders'].append({'name': a, 'new': b, 'src': 'c5', 'boss': 'flowery'})
    json.dump(A, open(ASSETS, 'w'), indent=1)
    print('flowery: %d code files, %d sprites, %d sounds, %d objects' % (len(F), len(sprs), len(snds), len(OBJ)))
    return B


if __name__ == '__main__':
    main()
