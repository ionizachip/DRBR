"""Build 52: JEVIL (DELTARUNE Chapter 1) for KNIGHT FIGHTS ONLINE - his attack objects, his look and his background, taken from
the player's own Chapter 1 data.win (MODS_DIR/c1.win; decompiled to /home/claude/work/jevil/c1dump by dumpall.csx).

What it writes (idempotent, every build):
  - /home/claude/scripts/jevil_gen/*.gml: the Chapter 1 code of Jevil's pieces as obj_jv_* objects (gen_hub copies them into
    build/merged), changed only where Chapter 3 differs:
      * every Chapter 1 object / sprite name -> its obj_jv_ / spr_jv_ copy (Chapter 3 has some of these names for other things);
      * the SOUL's middle: Chapter 1's obj_heart is 16 px (x + 8), Chapter 3's 20 px (x + 10);
      * randomness of the attacks through the attack stream (det_rewrite: kbr_random & co.) - every game makes the same pattern;
        Jevil's body (a drawing only) keeps the plain generator;
      * scr_84_get_sound("snd_x") -> snd_x;
      * the laser scythe's own hit ("everyone loses 30% HP") -> a normal hit (the room's damage table, like every bullet);
      * Jevil's body no longer fades the party out (the online look hides / draws the hero itself);
      * obj_jv_dbc: Chapter 1's obj_dbulletcontroller with only Jevil's 17 types (Chapter 3 has its own obj_dbulletcontroller).
  - build/assets.json: the sprites (renamed spr_jv_*), the sounds Chapter 3 lacks (Jevil's voice), the object shells (their
    sprite / mask / parent / depth from Chapter 1), all from the source "c1".
Usage: python3 make_jevil.py"""
import os, re, json, sys, glob
sys.path.insert(0, '/home/claude/scripts')
import det_rewrite

C1 = '/home/claude/work/jevil/c1dump/'
OUT = '/home/claude/scripts/jevil_gen/'
ASSETS = '/home/claude/work/build/assets.json'

OBJ = {
    'obj_joker_body': 'obj_jv_body', 'obj_joker_teleport': 'obj_jv_teleport', 'obj_spadering': 'obj_jv_spadering',
    'obj_suitbomb': 'obj_jv_suitbomb', 'obj_heartbomb_blast': 'obj_jv_heartblast', 'obj_carouselbullet': 'obj_jv_carousel',
    'obj_centerscythe': 'obj_jv_cscythe', 'obj_laserscythe': 'obj_jv_lscythe', 'obj_bigscythe': 'obj_jv_bscythe',
    'obj_clubsbullet_dark': 'obj_jv_clubs', 'obj_dbullet_vert': 'obj_jv_dvert', 'obj_regularbullet_permanent': 'obj_jv_regbp',
    'obj_jokerbg_triangle_real': 'obj_jv_bg', 'obj_joker': 'obj_jv_joker', 'obj_dbulletcontroller': 'obj_jv_dbc'}
# objects whose Chapter 1 code is taken (obj_joker's and obj_dbulletcontroller's own code is written for the hub instead)
TAKE = [o for o in OBJ if o not in ('obj_joker', 'obj_dbulletcontroller')]
# Jevil's 17 attack types in obj_dbulletcontroller (obj_joker's user event 5)
TYPES = [46, 47, 48, 49, 50, 61, 62, 65, 68, 70, 71, 72, 73, 74, 75, 76, 77]
# Chapter 3 has these (the same generic art): used as they are
KEEP_SPR = {'spr_event', 'spr_grazemask'}
# sprites Jevil's own drawing (written for the hub, online_jevil52.gml) uses besides the ones in the taken code
EXTRA_SPR = ['spr_joker_main', 'spr_joker_dance', 'spr_joker_tired', 'spr_joker_teleport', 'spr_joker_teleport_r', 'spr_jokerchain',
             'spr_jokerbody', 'spr_jokerhead', 'spr_joker_scythebody', 'spr_joker_scythebody_mask', 'spr_jokerscythe_big', 'spr_carouselbg']
EXTRA_SND = ['snd_joker_chaos', 'snd_joker_anything', 'snd_joker_byebye', 'snd_joker_neochaos', 'snd_joker_oh', 'snd_joker_laugh0',
             'snd_joker_laugh1', 'snd_joker_ha0', 'snd_joker_ha1', 'snd_joker_metamorphosis']


def table(p):
    t = {}
    for l in open(p):
        r = l.rstrip('\n').split('\t')
        t.setdefault(r[0], {})[r[1]] = r[2:]
    return t


A1 = table(C1 + 'assets.tsv')
A3 = table('/home/claude/work/jevil/ch3_assets.tsv')


def events(o):
    out = {}
    for f in sorted(glob.glob(C1 + 'code/gml_Object_%s_*.gml' % o)):
        n = os.path.basename(f)[len('gml_Object_%s_' % o):-4]
        if re.match(r'^(Create|Step|Draw|Alarm|Other|Destroy|Collision)_', n):
            out[n] = open(f).read()
    return out


def block_at(t, i):
    """the {...} block starting at the first '{' at or after i: (start, end) of the braces"""
    j = t.index('{', i)
    d = 0
    for k in range(j, len(t)):
        if t[k] == '{':
            d += 1
        elif t[k] == '}':
            d -= 1
            if d == 0:
                return j, k + 1
    raise ValueError('unbalanced')


def jevil_dbc_step():
    t = open(C1 + 'code/gml_Object_obj_dbulletcontroller_Step_0.gml').read()
    t = re.sub(r'\nenum e__VW\s*\{.*?\}\s*$', '\n', t, flags=re.S)
    parts = []
    # (Chapter 1 keeps Jevil's types inside "if (joker == 1) { ... }": they are matched at any indent and re-indented)
    for m in re.finditer(r'^[ ]*if \(type == (\d+)( \|\| type == (\d+))?\)\s*$', t, re.M):
        a = int(m.group(1))
        b = int(m.group(3)) if m.group(3) else None
        if a in TYPES or (b is not None and b in TYPES):
            s, e = block_at(t, m.end())
            ind = len(m.group(0)) - len(m.group(0).lstrip(' '))
            blk = m.group(0).lstrip(' ') + '\n' + '\n'.join(l[ind:] if l.startswith(' ' * ind) else l for l in t[s:e].split('\n'))
            parts.append(blk)
    got = set()
    for p in parts:
        got |= set(int(x) for x in re.findall(r'type == (\d+)', p.split('\n', 1)[0]))
    missing = [x for x in TYPES if x not in got]
    assert not missing, 'Jevil types not found in obj_dbulletcontroller: %r' % missing
    return 'btimer += 1;\n' + '\n'.join(parts) + '\n'


def jevil_dbc_create():
    t = open(C1 + 'code/gml_Object_obj_dbulletcontroller_Create_0.gml').read()
    # (the number of enemies sets a slow-down; Jevil fights alone)
    t = re.sub(r'ratio = 1;.*\Z', 'ratio = 1;\n', t, flags=re.S)
    return t


def fix(t, obj, det):
    t = re.sub(r'\nenum e__VW\s*\{[^}]*\}\s*', '\n', t)
    t = re.sub(r'scr_84_get_sound\("(snd_\w+)"\)', r'\1', t)
    for a, b in OBJ.items():
        t = re.sub(r'\b%s\b' % re.escape(a), b, t)
    t = re.sub(r'\b(spr_\w+|jokerscythebig_mask)\b', lambda m: m.group(1) if m.group(1) in KEEP_SPR else jv_spr(m.group(1)), t)
    t = re.sub(r'obj_heart\.([xy]) \+ 8\b', r'obj_heart.\1 + 10', t)
    if det:
        t = det_rewrite.rewrite(t)[0]
    return t


def jv_spr(n):
    return 'spr_jv_' + (n[4:] if n.startswith('spr_') else n)


def main():
    os.makedirs(OUT, exist_ok=True)
    for f in glob.glob(OUT + '*.gml'):
        os.remove(f)
    files = {}
    sprites = set(EXTRA_SPR)
    for o in TAKE:
        ev = events(o)
        assert ev, 'no code for ' + o
        for n, t in ev.items():
            sprites |= set(x for x in re.findall(r'\b(spr_\w+|jokerscythebig_mask)\b', t) if x not in KEEP_SPR)
            det = (o not in ('obj_joker_body', 'obj_jokerbg_triangle_real'))
            files['gml_Object_%s_%s.gml' % (OBJ[o], n)] = fix(t, o, det)
    # the laser scythe: a normal hit (its own "everyone -30%" rule left out)
    files['gml_Object_obj_jv_lscythe_Other_15.gml'] = 'if (active == 1)\n{\n    if (target != 3)\n        scr_damage();\n    if (target == 3)\n        scr_damage_all();\n}\n'
    # Jevil's body: the party is never faded out by it online (the hub draws / hides the hero)
    b = files['gml_Object_obj_jv_body_Draw_0.gml']
    b = re.sub(r'with \(obj_heroparent\)\s*\{[^{}]*\}', '', b)
    files['gml_Object_obj_jv_body_Draw_0.gml'] = b
    # a spade of the ring may be gone already (the end of an attack): the ring's own write to it is guarded
    sp = files['gml_Object_obj_jv_spadering_Step_0.gml']
    sp2 = sp.replace('spade[startspade].gravity = grav;', 'if (instance_exists(spade[startspade]))\n            spade[startspade].gravity = grav;')
    assert sp2 != sp
    files['gml_Object_obj_jv_spadering_Step_0.gml'] = sp2
    # the controller with Jevil's types only
    st = jevil_dbc_step()
    sprites |= set(x for x in re.findall(r'\b(spr_\w+)\b', st) if x not in KEEP_SPR)
    files['gml_Object_obj_jv_dbc_Create_0.gml'] = fix(jevil_dbc_create(), 'obj_dbulletcontroller', True) + 'kbr_jv_dbc_create();\n'
    st = fix(st, 'obj_dbulletcontroller', True)
    # the SOUL's speed for Spade Spin / BYE-BYE: a bonus on the room's speed online (kbr_jv_speed_bonus), not set here
    st, n1 = re.subn(r'with \(obj_heart\)\s*\{\s*wspeed = \d+;\s*\}', '', st)
    st, n2 = re.subn(r'global\.sp = \d+;', '', st)
    assert n1 == 2 and n2 == 1, (n1, n2)
    # BYE-BYE's chasing scythe falls on the SOUL's column: Chapter 1's screen starts at x 0, the online battle's camera does not
    st, n3 = re.subn(r'which = floor\(\(obj_heart\.x \+ 10\) / 90\);', 'which = floor(((obj_heart.x + 10) - __view_get(e__VW.XView, 0)) / 90);', st)
    assert n3 == 1
    files['gml_Object_obj_jv_dbc_Step_0.gml'] = st
    files['gml_Object_obj_jv_dbc_Destroy_0.gml'] = 'kbr_jv_dbc_destroy();\n'
    # Jevil's battle object (online_jevil52.gml): the knights' handshake, his attacks, his balloon
    files['gml_Object_obj_jv_joker_Create_0.gml'] = 'kbr_jv_create();\n'
    files['gml_Object_obj_jv_joker_Step_0.gml'] = 'kbr_jv_step();\n'
    files['gml_Object_obj_jv_joker_Draw_0.gml'] = 'kbr_jv_draw();\n'
    # his body is drawn only while he is on stage (the lineup switches his battle object off when a knight steps in)
    files['gml_Object_obj_jv_body_Draw_0.gml'] = 'if (!variable_instance_exists(id, "owner") || !instance_exists(owner))\n    exit;\n' + files['gml_Object_obj_jv_body_Draw_0.gml']
    # the background: on while he is out (kbr_jv_bg_step); its middle on the battle's camera (Chapter 1's screen starts at 0, 0)
    files['gml_Object_obj_jv_bg_Step_0.gml'] = 'kbr_jv_bg_step();\n'
    bg = files['gml_Object_obj_jv_bg_Draw_0.gml']
    # (Chapter 1 draws the canopy's triangles at full strength always - his room always has it; here it fades with the rest)
    bg = bg.replace('for (i = 0; i < trimax; i += 1)', 'draw_set_alpha(bgalpha);\nfor (i = 0; i < trimax; i += 1)', 1).rstrip('\n') + '\ndraw_set_alpha(1);\n'
    files['gml_Object_obj_jv_bg_Draw_0.gml'] = 'xcen = __view_get(e__VW.XView, 0) + 320;\nycen = __view_get(e__VW.YView, 0) + 240;\nif (bgalpha <= 0 && on == 0)\n    exit;\n' + 'draw_set_alpha(bgalpha);\ndraw_set_color(c_black);\ndraw_rectangle(xcen - 330, ycen - 250, xcen + 330, ycen + 250, false);\ndraw_set_alpha(1);\n' + bg
    # object sprites / masks
    for o in OBJ:
        r = A1['obj'].get(o)
        if r:
            for s in (r[1], r[2]):
                if s and s not in KEEP_SPR:
                    sprites.add(s)
    missing = [s for s in sprites if s not in A1['spr']]
    assert not missing, 'sprites not in Chapter 1: %r' % missing
    # "obj_x.v = e;" sets v on EVERY instance of obj_x in GameMaker: written as a with() (the same in the game, and the emulator
    # - which sets only the first instance - then agrees)
    cnt = [0]
    def every(m):
        cnt[0] += 1
        v = '_jvv%d' % cnt[0]
        return '%svar %s = %s;\n%swith (%s)\n%s    %s = %s;' % (m.group(1), v, m.group(4), m.group(1), m.group(2), m.group(1), m.group(3), v)
    for n in list(files):
        files[n] = re.sub(r'^([ ]*)(obj_jv_\w+)\.(\w+) = (.+);$', every, files[n], flags=re.M)
    # Chapter 1's Jevil room is 640 x 480 with its camera at 0, 0: the few places that use room coordinates as screen ones are
    # put on the battle's camera (the online battle's camera is elsewhere in a bigger room) - the bombs falling in from the
    # top, the laser scythes (in from above, exploding 100 px over the screen's bottom - room_height - 100 there -, the laser
    # from the top), the Devilsknife's centre when there is no box
    VY = '__view_get(e__VW.YView, 0)'
    VX = '__view_get(e__VW.XView, 0)'
    fixes = [('gml_Object_obj_jv_suitbomb_Create_0.gml', 'y = -80;', 'y = %s - 80;' % VY, 1),
             ('gml_Object_obj_jv_dbc_Step_0.gml', 'instance_create(idealx, -20, obj_jv_suitbomb)', 'instance_create(idealx, %s - 20, obj_jv_suitbomb)' % VY, 5),
             ('gml_Object_obj_jv_dbc_Step_0.gml', ', -60, obj_jv_lscythe)', ', %s - 60, obj_jv_lscythe)' % VY, None),
             ('gml_Object_obj_jv_dbc_Step_0.gml', ', -320, obj_jv_lscythe)', ', %s - 320, obj_jv_lscythe)' % VY, 1),
             ('gml_Object_obj_jv_lscythe_Step_0.gml', '(room_height - 100)', '(%s + 380)' % VY, 1),
             ('gml_Object_obj_jv_lscythe_Step_0.gml', '    y = 0;', '    y = %s;' % VY, 1),
             ('gml_Object_obj_jv_cscythe_Create_0.gml', 'centerx = 320;', 'centerx = %s + 320;' % VX, 1),
             ('gml_Object_obj_jv_cscythe_Create_0.gml', 'centery = 120;', 'centery = %s + 120;' % VY, 1)]
    for fn, a, b, cnt in fixes:
        c = files[fn].count(a)
        assert c > 0 and (cnt is None or c == cnt), (fn, a, c)
        files[fn] = files[fn].replace(a, b)
    # the plain obj_collidebullet a piece makes joins the piece's send (it has no Create to adopt it - kbr_jv_adopt)
    for n in list(files):
        if not n.startswith('gml_Object_obj_jv_dbc_'):
            files[n] = re.sub(r'instance_create\(([^;]*?), obj_collidebullet\)', r'kbr_jv_adopt(instance_create(\1, obj_collidebullet))', files[n])
    # a piece that reads the box every step waits a step with no box (between two attacks the box is remade)
    for n in ('gml_Object_obj_jv_carousel_Step_0.gml', 'gml_Object_obj_jv_bscythe_Step_0.gml', 'gml_Object_obj_jv_spadering_Step_0.gml'):
        files[n] = 'if (!instance_exists(obj_battlesolid))\n    exit;\n' + files[n]
    # DRBR: the Devilsknife's blade (a plain collide bullet, destroyed by a hit as in Chapter 1) is turned for 10 frames after it
    # appears - only while it is still there (a SOUL touching it in those frames destroyed it: "Unable to find instance")
    n_ = 'gml_Object_obj_jv_cscythe_Step_0.gml'
    o_ = '            sbul.image_angle += 10 * scythesidex;\n            sbul.image_alpha += 0.1;'
    assert files[n_].count(o_) == 1, 'cscythe blade turn'
    files[n_] = files[n_].replace(o_, '            if (instance_exists(sbul))\n            {\n                sbul.image_angle += 10 * scythesidex;\n                sbul.image_alpha += 0.1;\n            }')
    # the view enum is Chapter 1's own (e__VW, removed above): Chapter 3's camera instead - the game has no e__VW
    for n in list(files):
        t = files[n]
        t = t.replace('__view_get(e__VW.XView, 0)', 'camera_get_view_x(view_camera[0])')
        t = t.replace('__view_get(e__VW.YView, 0)', 'camera_get_view_y(view_camera[0])')
        t = t.replace('__view_get(e__VW.WView, 0)', 'camera_get_view_width(view_camera[0])')
        t = t.replace('__view_get(e__VW.HView, 0)', 'camera_get_view_height(view_camera[0])')
        assert 'e__VW' not in t and '__view_get' not in t, n
        files[n] = t
    # Chapter 3's scr_bullet_inherit reads a few variables from its caller that Chapter 1's pieces do not all have
    for n in list(files):
        if re.match(r'gml_Object_obj_jv_(?!joker|body|bg)\w+_Create_0\.gml$', n):
            files[n] = files[n].rstrip('\n') + '\nkbr_jv_vars();\n'
    # build 52: a piece that reads the SOUL every step skips a step with no SOUL (see br_patch.soul_guard: a missing SOUL stops
    # the game - "Unable to find any instance for object index ... obj_heart")
    for n in list(files):
        if re.match(r'gml_Object_obj_jv_(?!joker|body|bg)\w+_(Step|Draw)_\d+\.gml$', n) and re.search(r'\bobj_heart\.', files[n]):
            files[n] = 'if (!instance_exists(obj_heart))\n    exit;\n' + files[n]
    for n, t in files.items():
        left = re.findall(r'\bobj_(?:joker|carouselbullet|spadering|suitbomb|centerscythe|laserscythe|bigscythe|heartbomb_blast|clubsbullet_dark|dbullet_vert|regularbullet_permanent|jokerbg)\w*', t)
        assert not left, (n, left)
        open(OUT + n, 'w').write(t)
    # sounds: the ones Chapter 3 lacks, from the taken code and Jevil's own lines
    snds = set(EXTRA_SND)
    for t in files.values():
        snds |= set(re.findall(r'\b(snd_\w+)\b', t))
    snds = sorted(s for s in snds if s in A1['snd'] and s not in A3['snd'])
    # the manifest
    A = json.load(open(ASSETS))
    M = A['manifest']
    ren = A['rename'].setdefault('c1', {})
    for kind in ('sprites', 'sounds', 'objects'):
        M[kind] = [m for m in M[kind] if m.get('src') != 'c1']
    for s in sorted(sprites):
        ren[s] = jv_spr(s)
        M['sprites'].append({'name': s, 'new': jv_spr(s), 'src': 'c1', 'users': ['c1'], 'keep': False, 'added': True, 'dx': 0, 'dy': 0})
    for s in snds:
        M['sounds'].append({'name': s, 'new': s, 'src': 'c1', 'users': ['c1'], 'keep': False, 'added': True})
    for a, b in OBJ.items():
        ren[a] = b
        M['objects'].append({'name': a, 'new': b, 'src': 'c1', 'users': ['c1'], 'keep': False, 'added': True})
    json.dump(A, open(ASSETS, 'w'), indent=1)
    print('jevil: %d code files, %d sprites, %d sounds, %d objects' % (len(files), len(sprites), len(snds), len(OBJ)))


if __name__ == '__main__':
    main()
