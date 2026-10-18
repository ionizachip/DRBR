"""DRBR: SPAMTON NEO (DELTARUNE Chapter 2's boss, encounter 61) - his pieces from the player's own Chapter 2 data.win
(MODS_DIR/c2.win, decompiled to /home/claude/work/src/c2). See make_boss.py for the common rules and online/notes/src_spamton.md
for the source survey (section 7: the port plan).

Taken as they are (renamed obj_sn_*): his attack controller (obj_sneo_bulletcontroller: the types his fight uses - 0 FLYING
HEADS / BIG SHOT dance, 1 PIPIS, 1.5 HEART ATTACK, 6 RECREW columns, 8.5 PHONEHANDS, 9 the FINALE, 12 the FACE), every piece they
make (heads, head bullets, mail walls and their bombs, wire hearts, the phone and its pipis thrower, eggs and their heads, the
phone hands, the face and its lasers, the final forme, its dollars, the fake heart, the last attack and its BIG SHOTs), his
body's own drawing (obj_spamton_neo_enemy's Create and Draw: the wings, arms, legs, wires and his partmode dances, the hearts he
pulls from his chest and the shooting dance) and the YELLOW SOUL's shot (obj_yheart_shot and its effects, renamed: the hub's own
obj_yheart_shot is the Thorn Knight's).
Changed where Chapter 3 / the shared timeline differ:
  - his Step (talk, ACTs, mercy, endings) is the hub's (online_spamton53.gml: the knights' handshake, his box, his attack, his
    lines); his own HP / MERCY writes in the pieces (a big shot on his heart, a BIG SHOT ending the finale) are gone: online he
    has no HP - the shared timeline ends his attacks;
  - the turn-timer writes of the pieces (a good shot ends Chapter 2's turn early: the big heart, the face, the pipis) are kept
    and end the attack in THAT game only (it then waits for the next shared attack, which starts on the same tick everywhere);
    a SENT piece never ends anyone's attack (kbr_sn_tt / kbr_sn_tt_sub);
  - his pieces' randomness: each piece's own stream (kbr_p_*: seeded by the cycle and by the piece that made it) - a shot that
    breaks an egg in one game never moves another game's hearts;
  - reads of his battle object (obj_spamton_neo_enemy.x ...) -> kbr_sn_gv("x") (a send may run them with him off stage);
  - Chapter 2's view enum -> Chapter 3's camera; the phone's skip keys -> none (fixed lengths keep the games in step)."""
import os, re, sys
sys.path.insert(0, '/home/claude/scripts')
from make_boss import Boss, block_at

OUT = '/home/claude/scripts/spamton_gen/'
OBJ = {
    'obj_spamton_neo_enemy': 'obj_sn_neo', 'obj_sneo_bulletcontroller': 'obj_sn_bc', 'obj_sneo_hitdetector': 'obj_sn_head',
    # FLYING HEADS / the BIG SHOT dance
    'obj_sneo_guymaker': 'obj_sn_guymaker', 'obj_sneo_lilguy': 'obj_sn_lilguy', 'obj_sneo_lilguy_bullet': 'obj_sn_lilbullet',
    'obj_sneo_biglaser': 'obj_sn_biglaser', 'obj_sneo_biglaser_friendlyhitbox': 'obj_sn_laserfhb', 'obj_sneo_arm_laser_telegraph': 'obj_sn_armtel',
    'obj_spamtonshot': 'obj_sn_cannonshot', 'obj_sneo_crew_dissolve': 'obj_sn_dissolve',
    # the base bullets
    'obj_basicbullet_sneo': 'obj_sn_bullet', 'obj_basicbullet_sneo_finale': 'obj_sn_bulletfin',
    # RECREW columns
    'obj_sneo_wall_controller_new': 'obj_sn_wallctrl', 'obj_sneo_wallbullet_new': 'obj_sn_wallcell', 'obj_sneo_rotatingwall_bomb': 'obj_sn_wallbomb',
    'obj_mettaton_bomb_hitbox': 'obj_sn_bombhit',
    # HEART ATTACK
    'obj_sneo_wireheart': 'obj_sn_wireheart', 'obj_sneo_heart_laser': 'obj_sn_heartlaser', 'obj_queen_laser': 'obj_sn_laser',
    'obj_sneo_heart_bomb_explode': 'obj_sn_heartbomb', 'obj_sneo_heatattack_bullet': 'obj_sn_heatbullet',
    # the PHONE and the PIPIS
    'obj_sneo_phonecall': 'obj_sn_phonecall', 'obj_sneo_phonecall_pipis_stream': 'obj_sn_headstream', 'obj_sneo_phonecall_sneohead': 'obj_sn_headpuff',
    'obj_pipis_controller': 'obj_sn_pipthrow', 'obj_pipis_egg_bullet': 'obj_sn_pipegg', 'obj_pipis_bullet_cone': 'obj_sn_pipcone',
    'obj_pipis_destroy_fx': 'obj_sn_pipfx', 'obj_pipis_egg_bullet_piece': 'obj_sn_pippiece', 'obj_pipis_wall': 'obj_sn_pipwall',
    'obj_sneo_armcannon_smoke': 'obj_sn_armsmoke',
    # PHONEHANDS
    'obj_sneo_phonehand_master': 'obj_sn_handhead', 'obj_sneo_phonehand': 'obj_sn_phonehand', 'obj_sneo_mmx_spreadshot': 'obj_sn_spreadshot',
    # the FACE
    'obj_sneo_faceattack': 'obj_sn_face', 'obj_sneo_faceattack_target': 'obj_sn_facetarget', 'obj_werewire_bullet_lasercircle': 'obj_sn_eyelaser',
    'obj_werewire_bullet_lasersquare': 'obj_sn_eyelaserseg', 'obj_boxing_crescent': 'obj_sn_crescent',
    # the FINALE
    'obj_finale_growtangle': 'obj_sn_finalebox', 'obj_sneo_warped_box': 'obj_sn_warpbox', 'obj_sneo_final_forme': 'obj_sn_forme',
    'obj_sneo_final_forme_hitbox': 'obj_sn_formehit', 'obj_sneo_final_forme_mouth_back': 'obj_sn_formemouth', 'obj_sneo_dollar': 'obj_sn_dollar',
    'obj_sneo_fakeheart': 'obj_sn_fakeheart', 'obj_wreckpausespew': 'obj_sn_playback', 'obj_sneo_lastattack': 'obj_sn_lastattack',
    'obj_sneo_lastattack_hitbox': 'obj_sn_lasthit', 'obj_sneo_bigshot': 'obj_sn_bigshot', 'obj_sneo_smoke': 'obj_sn_smoke',
    'obj_sneo_final_orb': 'obj_sn_finalorb',
    # PIPIS FIREWORKS (Chapter 2's weird-route pipis - a SEND here)
    'obj_sneo_weird_end_pipis': 'obj_sn_wpipis', 'obj_sneo_weird_end_pipis_bullet': 'obj_sn_wpipishead',
    # the YELLOW SOUL's shot (the hub's own obj_yheart_shot is the Thorn Knight's: Spamton's are his)
    'obj_yheart_shot': 'obj_sn_yshot', 'obj_yshot_anim': 'obj_sn_yshotanim', 'obj_yheart_shot_afterimage': 'obj_sn_ytrail',
    'obj_yheart_sneo_particle': 'obj_sn_yspark', 'obj_supercharge_end': 'obj_sn_superend',
    # the hub's own (online_spamton53.gml): the yellow SOUL's driver, the background
    '@ysoul': 'obj_sn_ysoul', '@bg': 'obj_sn_bg',
}
TAKE = [o for o in OBJ if not o.startswith('@') and o != 'obj_spamton_neo_enemy']
# his own object: the look (Create's fields, the Draw) - his Step is the hub's
NEO_EVENTS = ('Create_0', 'Draw_0')
# events never reached online (the ACT pieces Tiny Ralsei / Susie's axe, Chapter 2's debug keys, the head box's disabled hits)
SKIP_EV = {
    'obj_sneo_wireheart': ('Collision_obj_sneo_tiny_ralsei', 'Collision_obj_sneo_tiny_susie_axe'),
    'obj_sneo_hitdetector': ('Collision_obj_yheart_shot', 'Collision_obj_sneo_phonebullet'),
}
# the controller's types the fight (and the sends) use; the rest are Chapter 2's dead / debug ones
BC_TYPES = {'0', '1', '1.5', '6', '8.5', '9', '12'}
KEEP_SPR = {'spr_heart', 'spr_dodgeheart', 'spr_nothing', 'spr_whitepixel', 'spr_pxwhite', 'spr_yellowheart', 'spr_diamondbullet'}


def piece_random(t):
    """a piece's own draws -> its own stream (kbr_p_*: drbr53.gml)"""
    t = re.sub(r'(?<![\w.])irandom_range\(', 'kbr_p_irandom_range(', t)
    t = re.sub(r'(?<![\w.])random_range\(', 'kbr_p_random_range(', t)
    t = re.sub(r'(?<![\w.])irandom\(', 'kbr_p_irandom(', t)
    t = re.sub(r'(?<![\w.])random\(', 'kbr_p_random(', t)
    t = re.sub(r'(?<![\w.])choose\(', 'kbr_p_choose(', t)
    t = re.sub(r'(?<![\w.])ds_list_shuffle\(', 'kbr_p_list_shuffle(', t)
    return t


def rewrite_reads(t):
    """obj_sn_neo.f reads -> kbr_sn_gv("f"); increments / compound writes -> with (obj_sn_neo)"""
    t = re.sub(r'^([ ]*)obj_sn_neo\.(\w+)(\+\+|--);$', r'\1with (obj_sn_neo)\n\1    \2\3;', t, flags=re.M)
    t = re.sub(r'^([ ]*)obj_sn_neo\.(\w+) ([-+*/]=) (.+);$', lambda m: '%svar _snw = %s;\n%swith (obj_sn_neo)\n%s    %s %s _snw;' % (m.group(1), m.group(4), m.group(1), m.group(1), m.group(2), m.group(3)), t, flags=re.M)
    t = re.sub(r'\bobj_sn_neo\.(\w+)\b(?!\s*(=[^=]|\+=|-=|\*=|/=|\+\+|--|\[))', r'kbr_sn_gv("\1")', t)
    return t


def strip_if_blocks(t, cond_re, keep):
    """remove top-level `if (cond)` blocks whose matched value is not in keep (the controller's dead types)"""
    out = t
    while True:
        changed = False
        for m in re.finditer(r'^if \(type == ([\d.]+)\)\s*$', out, re.M):
            if m.group(1) in keep:
                continue
            s, e = block_at(out, m.end())
            out = out[:m.start()] + out[e:].lstrip('\n')
            changed = True
            break
        if not changed:
            return out


def sub(t, a, b, n=1, what=''):
    c = t.count(a)
    assert c == n, ('%s: %r found %d times (want %d)' % (what, a[:70], c, n))
    return t.replace(a, b)


def drop_block(t, head, what='', n=1):
    """remove `head` (a line ending the statement before a {...} block) and its block, n times"""
    for _ in range(n):
        i = t.index(head)
        s, e = block_at(t, i + len(head))
        while e < len(t) and t[e] == '\n':
            e += 1
        t = t[:i] + t[e:]
    assert head not in t, ('drop_block left', what, head[:60])
    return t


def drop_with_containing(t, key, what=''):
    """remove every `with (obj_sn_neo) {...}` block whose body contains key (NEO's HP / mercy writes)"""
    k = 0
    while key in t:
        j = t.index(key)
        i = t.rfind('with (obj_sn_neo)', 0, j)
        assert i >= 0, what
        s, e = block_at(t, i + len('with (obj_sn_neo)'))
        assert s < j < e, (what, 'key not in the with block')
        ls = t.rfind('\n', 0, i) + 1
        while e < len(t) and t[e] == '\n':
            e += 1
        t = t[:ls] + t[e:]
        k += 1
    return t, k


# Draw events whose randomness is the piece's play (the pipis thrower throws from its Draw); every other Draw's draws are looks
# only (shakes, jitter, smoke) and stay on GameMaker's own generator - a look (or a player's SIMPLIFY VFX setting) never moves
# a piece's stream
DRAW_PLAY = {'gml_Object_obj_sn_pipthrow_Draw_0.gml'}
NEO_DRAW_PLAY = 'makehearttype = choose(3, 4);'
# the hub's own (online_spamton53.gml)
EXTRA_SPR = ['bg_dw_mansion_basement_cityscape_background', 'bg_dw_mansion_basement_cityscape_midground', 'bg_dw_mansion_basement_cityscape_foreground',
             'spr_sneo_track', 'spr_yellowheart', 'spr_yheart_charge', 'spr_grazeappear_yellow', 'spr_yheart_bigshot', 'spr_sneo_example']
EXTRA_SND = ['snd_sneo_laugh_long', 'snd_spamton_laugh', 'snd_chargeshot_charge', 'snd_chargeshot_fire', 'snd_heartshot_dr_b']


def main():
    B = Boss('spamton', 'c2', 'sn', OBJ, keep_spr=KEEP_SPR, local=set(OBJ))
    for o in TAKE:
        B.take(o, skip=SKIP_EV.get(o, ()))
    ev = B.events('obj_spamton_neo_enemy')
    B.shell('obj_spamton_neo_enemy')
    for n in NEO_EVENTS:
        B.files['gml_Object_obj_sn_neo_%s.gml' % n] = B.fix(ev[n], det=False)
    F = B.files
    # ---- collision events named after a renamed object (Collision_obj_yheart_shot -> Collision_obj_sn_yshot)
    for n in list(F):
        m = re.match(r'(gml_Object_\w+?_Collision_)(obj_\w+)\.gml$', n)
        if m and m.group(2) in OBJ:
            F[m.group(1) + OBJ[m.group(2)] + '.gml'] = F.pop(n)
    left_ev = [n for n in F if re.search(r'_Collision_(obj_sneo_|obj_pipis_|obj_yheart_shot|obj_spamton_neo)', n)]
    assert not left_ev, left_ev
    # ---- the controller: only the types used; the pipis thrower: only its variant 2 (its Create sets 2, nothing changes it)
    bcs = 'gml_Object_obj_sn_bc_Step_0.gml'
    F[bcs] = strip_if_blocks(F[bcs], None, BC_TYPES)
    pt = 'gml_Object_obj_sn_pipthrow_Draw_0.gml'
    for v in ('0', '1', '3'):
        for head in ('if (variant == %s && movecon == 1)\n' % v, 'if (variant == %s)\n' % v):
            if head in F[pt]:
                F[pt] = drop_block(F[pt], head, 'pipthrow variant ' + v)
    assert 'variant == 2' in F[pt] and 'obj_sneo_pipis_bomb' not in F[pt] and 'variant == 3' not in F[pt]
    # ---- NEO's HP and MERCY (online he has neither: the shared timeline ends his attacks)
    F[bcs] = drop_block(F[bcs], 'if (global.mercymod[obj_sn_neo.myself] > 99 && global.turntimer > 1)\n', 'bc mercy end')
    bd = 'gml_Object_obj_sn_bc_Destroy_0.gml'
    F[bd] = drop_block(F[bd], 'if (mercyaccumulated > 0)\n', 'bc Destroy mercy')
    for n in ('gml_Object_obj_sn_wireheart_Draw_0.gml', 'gml_Object_obj_sn_bigshot_Destroy_0.gml'):
        F[n], k = drop_with_containing(F[n], 'global.monsterhp[myself] == global.monstermaxhp[myself]', n)
        assert k == 1, (n, k)
    nd = 'gml_Object_obj_sn_neo_Draw_0.gml'
    F[nd] = sub(F[nd], 'global.mercymod[myself] > 89', 'false', 2, 'NEO Draw mercy vines')
    F[nd], k = re.subn(r'if \(\(didwejustdie == 0 && i_ex\(obj_battlecontroller\) && global\.monsterhp\[global\.chartarget\[myself\]\] <= 0\)[^\n]*\)\n', 'if (false)\n', F[nd])
    assert k == 1, 'NEO Draw defeat'
    nc = 'gml_Object_obj_sn_neo_Create_0.gml'
    F[nc] = sub(F[nc], 'if (global.fighting == 0)\n{\n    myself = 0;\n    global.mercymod[myself] = 0;\n}\n', 'myself = 0;\n', 1, 'NEO Create mercy')
    # ---- the weird route, Chapter 2's debug keys, its room: never online (every game the same - a save's route never shows)
    for n in list(F):
        F[n] = F[n].replace('scr_sideb_get_phase()', '0').replace('scr_debug()', 'false')
    F[nd] = sub(F[nd], 'room != room_dw_mansion_b_east_a', 'true', 1, 'NEO Draw room')
    # bullets leave at the battle's view, not Chapter 2's room (2720 wide: they flew 1700 px off screen first)
    bb = 'if (x >= (room_width + 100) || x <= -100 || y >= (room_height + 100) || y <= -100)'
    nb = 0
    for n in list(F):
        if bb in F[n]:
            F[n] = F[n].replace(bb, 'if (x >= (camerax() + 740) || x <= (camerax() - 100) || y >= (cameray() + 580) || y <= (cameray() - 100))')
            nb += 1
    assert nb == 4, ('bullet bounds', nb)
    assert not [n for n in F if 'room_' in F[n]], [n for n in F if 'room_' in F[n]]
    # ---- the decompiler's raw object number in the final forme's shakes: Chapter 2's obj_shake was object 196 ("d =
    # instance_exists(obj_shake) ? 196 : instance_create(...)"); in the built game 196 is another object - "Unable to find
    # instance for object index 196" in the NEO Finale (found by the shooting sweep). The object itself, as Chapter 2 wrote it.
    nsh = 0
    for n in list(F):
        a = 'instance_exists(obj_shake) ? 196 : instance_create(0, 0, obj_shake)'
        nsh += F[n].count(a)
        F[n] = F[n].replace(a, 'instance_exists(obj_shake) ? obj_shake : instance_create(0, 0, obj_shake)')
    assert nsh == 3, ('forme shakes', nsh)
    # Chapter 2's chapter check (a BIG SHOT marks NEO's bigshotused): Chapter 3 is 3
    ys = 'gml_Object_obj_sn_yshot_Create_0.gml'
    F[ys] = sub(F[ys], 'global.chapter == 2 && ', '', 1, 'yshot chapter')
    # ---- room coordinates -> the battle's camera: the wires up to y -400, the phone dropping from y -30
    nw = 0
    for a in (', -400, 1);', ', -400, 2);', ', -400, 1 + (lastwiretimer / 30));'):
        nw += F[nd].count(a)
        F[nd] = F[nd].replace(a, a.replace('-400', 'cameray() - 400'))
    assert nw == 8, ('wires', nw)
    pcs = 'gml_Object_obj_sn_phonecall_Step_0.gml'
    pcd = 'gml_Object_obj_sn_phonecall_Draw_0.gml'
    F[pcs] = sub(F[pcs], '    y = -30;\n', '    y = cameray() - 30;\n', 1, 'phone y')
    F[pcd] = sub(F[pcd], 'y = lerp(-30, ystart', 'y = lerp(cameray() - 30, ystart', 1, 'phone drop')
    # ---- the phone's lines: no skipping (Z fires the yellow SOUL; fixed lengths keep every game in step), NEO's own balloon
    F[pcs] = sub(F[pcs], 'if (button1_p() && talktimer > 5 && aa == 0)', 'if (false)', 1, 'phone skip Z')
    F[pcs] = sub(F[pcs], 'if (button3_h() && talktimer > 1 && aa == 0)', 'if (false)', 1, 'phone skip C')
    F[pcs] = sub(F[pcs], '        with (obj_writer)\n        {\n            instance_destroy();\n        }\n', '        with (obj_sn_neo)\n            say_t = 0;\n', 1, 'phone writer end')
    a = ('    with (obj_sn_neo)\n    {\n        global.typer = 72;\n        scr_enemyblcon(((x - obj_sn_phonecall.textboxdistance) + 22) - obj_sn_phonecall.textboxoffsetx, '
         'y + 60 + obj_sn_phonecall.textboxoffsety, 10);\n    }\n')
    F[pcs] = sub(F[pcs], a, '    with (obj_sn_neo)\n        kbr_sn_line(global.msg[0], other.talkmax + 15);\n', 1, 'phone balloon')
    # ---- the yellow SOUL is the driver's (obj_sn_ysoul), never obj_heart.color (Chapter 3's colour code fires the hub's own shots)
    nh = 0
    for n in list(F):
        for a, b in (('obj_heart.color = 1;', 'kbr_sn_heart_yellow(1);'), ('obj_heart.color = 0;', 'kbr_sn_heart_yellow(0);')):
            nh += F[n].count(a)
            F[n] = F[n].replace(a, b)
    assert nh == 4, ('heart colour', nh)
    assert not [n for n in F if 'obj_heart.color' in F[n]]
    # ---- the swallowed SOUL's damage number goes to the hero (Chapter 2's party is always there; the hub's may be a stand-in)
    fh = 'gml_Object_obj_sn_fakeheart_Step_2.gml'
    F[fh] = sub(F[fh], '            x = obj_heroparent.x;\n            y = obj_heroparent.y;\n',
                '            if (instance_exists(obj_heroparent))\n            {\n                x = obj_heroparent.x;\n                y = obj_heroparent.y;\n            }\n', 1, 'fakeheart hero')
    # ---- NEO's user event 2 (a share of every member's HP) -> one hit through the room's table, from the piece that hits
    nu = 0
    for n in list(F):
        F[n], k = re.subn(r'^([ ]*)with \(obj_sn_neo\)\n\1\{\n\1    event_user\(2\);\n\1\}\n', r'\1kbr_sn_hurt();\n', F[n], flags=re.M)
        nu += k
    assert nu == 6, ('NEO user event 2', nu)
    # ---- the turn timer: Chapter 2's own writes stay (a shot heart, a broken face, a pipis crowd shot down end YOUR attack early
    # - that game only: it waits for the next shared attack), through kbr_sn_tt (a SENT piece never ends anyone's attack)
    ntt = 0
    for n in list(F):
        F[n], k1 = re.subn(r'\bglobal\.turntimer -= (.+);$', r'kbr_sn_tt_sub(\1);', F[n], flags=re.M)
        F[n], k2 = re.subn(r'\bglobal\.turntimer = (.+);$', r'kbr_sn_tt(\1);', F[n], flags=re.M)
        ntt += k1 + k2
    assert ntt == 18, ('turn-timer writes', ntt)
    assert not [n for n in F if re.search(r'global\.turntimer\s*([-+*/]?=[^=]|\+\+|--)', F[n])]
    # ---- every piece's draws: its own stream (looks in Draw events stay on GameMaker's generator)
    F[nd] = sub(F[nd], NEO_DRAW_PLAY, 'makehearttype = kbr_p_choose(3, 4);', 1, 'NEO heart type')
    # his body's look (the parts' jitter - it also turns his arm, where his cannon shots start): a look stream of its own, the same
    # in every game for the same cycle (kbr_sn_l*: online_spamton53.gml), never GameMaker's generator (different in every game)
    F[nd] = re.sub(r'(?<![\w.])random_range\(', 'kbr_sn_lrandom_range(', F[nd])
    F[nd] = re.sub(r'(?<![\w.])random\(', 'kbr_sn_lrandom(', F[nd])
    F[nd] = re.sub(r'(?<![\w.])irandom\(', 'kbr_sn_lirandom(', F[nd])
    assert not re.search(r'(?<![\w.])(choose|irandom_range)\(', F[nd]), 'NEO Draw: another random call'
    for n in list(F):
        if '_Draw_' in n and n not in DRAW_PLAY:
            continue
        F[n] = piece_random(F[n])
    # ---- reads of NEO's battle object (a send may run a piece with him off stage)
    for n in list(F):
        if not n.startswith('gml_Object_obj_sn_neo_'):
            F[n] = rewrite_reads(F[n])
    # ---- reads of his attack's controller by its pieces (a sent piece has none): kbr_sn_bcv (its value, or the default)
    nbc = 0
    for n in list(F):
        if n.startswith('gml_Object_obj_sn_neo_') or n.startswith('gml_Object_obj_sn_bc_'):
            continue
        F[n], k = re.subn(r'\bobj_sn_bc\.(\w+)\b(?!\s*(=[^=]|\+=|-=|\*=|/=|\+\+|--|\[))', r'kbr_sn_bcv("\1")', F[n])
        nbc += k
    assert nbc >= 14, ('controller reads', nbc)
    # ---- the mail walls' cells and pipis bombs follow THEIR OWN wall controller (Chapter 2 runs one at a time, so its cells read
    # and write obj_sneo_wall_controller_new - the first one; online a sent MAIL WALL and his own RECREW columns can run together:
    # each cell would move by, and set the speed of, the other's walls). The controller hands each cell itself (ctrl).
    wc = 'gml_Object_obj_sn_wallctrl_Step_0.gml'
    F[wc], k = re.subn(r'^([ ]*)(bullet\[i\] = instance_create\(.*\);)$', r'\1\2\n\1bullet[i].ctrl = id;', F[wc], flags=re.M)
    assert k == 4, ('wall cells made', k)
    nwc = 0
    for n in ('gml_Object_obj_sn_wallcell_Step_0.gml', 'gml_Object_obj_sn_wallbomb_Step_0.gml'):
        F[n], k1 = re.subn(r'\bi_ex\(obj_sn_wallctrl\)', 'kbr_sn_wc_ok()', F[n])
        F[n], k2 = re.subn(r'\bobj_sn_wallctrl\.', 'ctrl.', F[n])
        nwc += k1 + k2
    F['gml_Object_obj_sn_wallcell_Step_0.gml'] = sub(F['gml_Object_obj_sn_wallcell_Step_0.gml'], 'if (wallcontroller > -1)\n', 'if (wallcontroller > -1 && kbr_sn_wc_ok())\n', 1, 'wall lead cell')
    # DRBR 1.0.3: the arm laser sizes itself in its Draw (its orb, its beam's thickness): a SENT one is made to fit the box it
    # lands in by its kbrsz (kbr_fitv(): 1 for his own) - the BIG SHOT skill's white orb and beam were twice the box's height
    bl = 'gml_Object_obj_sn_biglaser_Draw_0.gml'
    F[bl] = sub(F[bl], 'draw_circle(x, y, max(2, (orbsize / 2) + (sin(siner / 2) * 2)), 0);', 'draw_circle(x, y, max(2, ((orbsize / 2) + (sin(siner / 2) * 2)) * kbr_fitv()), 0);', 1, 'laser orb')
    F[bl] = sub(F[bl], '    if (image_yscale < 0.5)\n    {\n        image_yscale = scr_movetowards(image_yscale, 0.5, 0.1);', '    if (image_yscale < (0.5 * kbr_fitv()))\n    {\n        image_yscale = scr_movetowards(image_yscale, 0.5 * kbr_fitv(), 0.1);', 1, 'laser beam')
    # (a red crew member shot takes its wall with it: its own wall - the same number AND the same controller)
    w10 = 'gml_Object_obj_sn_wallcell_Other_10.gml'
    F[w10] = sub(F[w10], '        with (obj_sn_wallcell)\n        {\n            if (wallnumber == other.wallnumber)\n', '        with (obj_sn_wallcell)\n        {\n            if (wallnumber == other.wallnumber && kbr_sn_same_ctrl(other.id))\n', 1, 'red crew wall')
    assert nwc == 10, ('wall controller refs', nwc)
    B.finish(no_vars=('obj_sn_neo',), no_guard=('obj_sn_neo',))
    for n in list(F):
        if not n.startswith('gml_Object_obj_sn_neo_'):
            F[n] = rewrite_reads(F[n])
    # ---- sendable pieces: adopted by the send that makes them; their own stream right after (kbr_p_born)
    sn = B.sendable(skip=('obj_sn_neo', 'obj_sn_bc', 'obj_sn_phonecall', 'obj_sn_finalebox', 'obj_sn_warpbox', 'obj_sn_forme', 'obj_sn_formehit',
                          'obj_sn_formemouth', 'obj_sn_fakeheart', 'obj_sn_lastattack', 'obj_sn_lasthit', 'obj_sn_finalorb', 'obj_sn_playback',
                          'obj_sn_yshot', 'obj_sn_yshotanim', 'obj_sn_ytrail', 'obj_sn_yspark', 'obj_sn_superend', 'obj_sn_head'),
                    guard=('obj_sn_neo', 'obj_sn_bc'))
    print('spamton sendable: %d Creates, %d events, %d turn-timer reads, %d guarded writes' % sn)
    nb = 0
    for n in list(F):
        if re.match(r'gml_Object_obj_sn_\w+_Create_0\.gml$', n) and not n.startswith('gml_Object_obj_sn_neo_'):
            t = F[n]
            if t.startswith('kbr_ev_cr();\n'):
                F[n] = 'kbr_ev_cr();\nkbr_p_born();\n' + t[len('kbr_ev_cr();\n'):]
            else:
                F[n] = 'kbr_p_born();\n' + t
            nb += 1
    # ---- NEO's battle object: Chapter 2's Create and Draw (his look), the hub's Step (online_spamton53.gml); his user event 2
    F[nc] = F[nc].rstrip('\n') + '\nkbr_sn_create();\n'
    F[nd] = F[nd].rstrip('\n') + '\nkbr_sn_draw_extra();\n'
    F['gml_Object_obj_sn_neo_Step_0.gml'] = 'kbr_sn_step();\n'
    F['gml_Object_obj_sn_neo_Other_12.gml'] = 'kbr_sn_hurt();\n'
    # the yellow SOUL's driver and the background (the hub's own objects)
    F['gml_Object_obj_sn_ysoul_Create_0.gml'] = 'kbr_sn_ys_create();\n'
    F['gml_Object_obj_sn_ysoul_Step_0.gml'] = 'kbr_sn_ys_step();\n'
    F['gml_Object_obj_sn_ysoul_Step_2.gml'] = 'kbr_sn_ys_end();\n'
    F['gml_Object_obj_sn_ysoul_Draw_0.gml'] = 'kbr_sn_ys_draw();\n'
    F['gml_Object_obj_sn_bg_Create_0.gml'] = 'kbr_sn_bg_create();\n'
    F['gml_Object_obj_sn_bg_Step_0.gml'] = 'kbr_sn_bg_step();\n'
    F['gml_Object_obj_sn_bg_Draw_0.gml'] = 'kbr_sn_bg_draw();\n'
    F['gml_Object_obj_drbr_none_Create_0.gml'] = '// DRBR: the stand-in for objects of another chapter that are not imported: never kept\ninstance_destroy();\n'
    left = [(n, x) for n, t in F.items() for x in re.findall(r'\b(obj_spamton_neo_enemy|obj_sneo_\w+|obj_pipis_\w+|obj_yheart_shot\b|e__VW)', re.sub(r'"[^"\n]*"', '""', t))]
    assert not left, left[:5]
    for s in EXTRA_SPR:
        assert s in B.S['spr'], s
        B.sprites.add(s)
    print('spamton: %d files, %d piece streams' % (len(F), nb))
    B.write(OUT)
    sprs, snds = B.manifest(extra_snd=EXTRA_SND)
    print('spamton: %d code files, %d sprites imported %s, %d sounds %s, %d objects' % (len(F), len(sprs), sprs, len(snds), snds, len(OBJ)))
    return B


if __name__ == '__main__':
    main()
