import json, os
S = '/home/claude/scripts/'
OUT = '/home/claude/work/build/merged/'
T = S + 'gml_templates_v6/'
K = json.load(open(S + 'knights.json'))

def q(s):
    # build 48: "//" inside a string is written as "/" + "/" (a song title has it; the build's line tools read // as a comment)
    return '"' + s.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n').replace('//', '/" + "/') + '"'

def b(v):
    return 'true' if v else 'false'

def arr(l):
    return '[' + ', '.join(q(x) for x in l) + ']'

def credits(groups):
    out = []
    for g in groups:
        names = ', '.join('[' + q(n[0]) + ', ' + q(n[1]) + ']' for n in g['n'])
        out.append('{ g: %s, n: [%s] }' % (q(g['g']), names))
    return '[' + ', '.join(out) + ']'

def color(c):
    return 'make_color_rgb(%d, %d, %d)' % tuple(c)

def pace(p):
    return '{ gate: %s, tmin: %d, gate_b: %s, tmin_b: %d }' % (repr(float(p.get('gate', 0))), p.get('tmin', 0), repr(float(p.get('gate_b', p.get('gate', 0)))), p.get('tmin_b', p.get('tmin', 0)))

# art the Twin Knight uses in each fight: the fight's own star, small bullet and sword (renamed per variant by the merge)
RENAME = json.load(open('/home/claude/work/build/assets.json'))['rename']
TWIN_SMALL = {'thorn': 'spr_smallbullet_red'}
def twin_art(key):
    r = RENAME.get(key, {})
    return (r.get('spr_knight_bullet_star', 'spr_knight_bullet_star'), TWIN_SMALL.get(key, r.get('spr_smallbullet', 'spr_smallbullet')),
            r.get('spr_roaringknight_sword_ol', 'spr_roaringknight_sword_ol'))

# each knight's attack list (build 41: Start At / Repeat practice, Attack Remix, fight stats), read from the merged fight code:
# [phase, turn, name, flags] (flags: 1 = listed as unused, 2 = Roaring finale / phase 4). Kaizo names its attacks: turn = the attack's variable.
import re, sys
sys.path.insert(0, S)
from vtext import vtext

def atk_list(key):
    if key == 'kaizo':
        t = vtext('gml_Object_obj_knight_enemy_Other_24', 'kaizo')
        names = []
        for n in re.findall(r'array_push\(kaizo_list, "(atk_\w+)"\);', t):
            if n not in names:
                names.append(n)
        out = []
        for n in names:
            blk = re.search(r'\b' + n + r' = \s*\{(.*?)\n\s*\};', t, re.S).group(1)
            ans = re.findall(r'attackName: "([^"]*)"', blk)
            ph = int(re.search(r'attackPhase: (\d+)', blk).group(1))
            out.append([ph, n, ans[-1] if ans else n])
    else:
        t = vtext('gml_Object_obj_knight_enemy_Create_0', key)
        s = re.search(r'^prac_list = (.*);$', t, re.M).group(1)
        if s.startswith('((('):
            s = s[s.rfind(' : [') + 3:].rstrip(')')   # Violet: the list without Weird Route
        out = json.loads(s.strip())
    for e in out:
        e.append((1 if '(unused)' in e[2] else 0) + (2 if e[0] == 4 else 0))
    assert len(out) >= 10, key
    return out

def atk_gml(l):
    return '[' + ', '.join('[%d, %s, %s, %d]' % (e[0], q(e[1]) if isinstance(e[1], str) else str(e[1]), q(e[2]), e[3]) for e in l) + ']'

reg = []
for v in K['variants']:
    mr = v.get('music_rename')
    mrs = '{ ' + ', '.join(f'{q(a)}: {q(c)}' for a, c in mr.items()) + ' }' if mr else 'undefined'
    reg.append(('    { id: %d, key: %s, name: %s, short: %s, title: %s, desc: %s, author: %s, skip_flag: %d, has_practice: %s, music_rename: %s, music: %s, '
                'joke: %s, rush: %s, weird: %s, needs_kris: %s, color: %s, tint: %s, portrait: %s, credits: %s, songcredit: %s, pace: %s, '
                'twin_star: %s, twin_small: %s, twin_sword: %s, twin_blend: %s, atk: %s, chapter: %d }') % (
        v['id'], q(v['key']), q(v['name']), q(v['short']), q(v['title']), q(v['desc']), q(v.get('author', '')), v.get('skip_flag', -1),
        b(v.get('has_practice')), mrs, q(v['music']), b(v['joke']), b(v['rush']), b(v['weird']), b(v['needs_kris']), color(v['color']), b(v.get('tint', False)),
        q(v.get('portrait', '')), credits(v.get('credits', [])), q(v.get('songcredit', '')), pace(v.get('pace', {})),
        *[q(a) for a in twin_art(v['key'])], color(v['color']) if v.get('tint') else 'c_white', atk_gml(atk_list(v['key'])), int(v.get('chapter', 3))))
# build 50: every song has a stable id (its file; never its place in the list) and its credit lines (CREDITS > MUSIC), wrapped to
# fit the credits page; songs_order_v49: the list's order before build 50 (an old online MUSIC setting saved as a number)
import textwrap as _tw
def _cl(s):
    t = s.get('credit_game') or s.get('credit') or ''
    return '[' + ', '.join(q(x) for x in _tw.wrap(t, 56)) + ']'
songs = [f'    {{ name: {q(s["name"])}, file: {q(s["file"])}, by: {q(s.get("by", ""))}, src: {q(s.get("src", ""))}, sid: {q(s.get("id", s["file"]))}, cl: {_cl(s)} }}' for s in K['songs']]
songs_v49 = '[' + ', '.join(q(f) for f in K.get('songs_order_v49', [])) + ']'

TEMPLATES = ['core.gml', 'store.gml', 'rules.gml', 'run.gml', 'challenges.gml', 'loadouts.gml', 'weird.gml', 'b38.gml', 'b39.gml', 'lineup.gml', 'qol.gml',
             'online_set.gml', 'online_net.gml', 'online_host.gml', 'online_play.gml', 'online_br.gml', 'online_br_run.gml', 'online_br_me.gml',
             'online_br_skill.gml', 'online_sent50.gml', 'online_hud50.gml', 'online_target.gml', 'online_bots.gml', 'online_debug49.gml', 'online_br_hud.gml', 'online_world.gml', 'online_view.gml', 'online_chat.gml', 'online_steam.gml', 'online_ui.gml', 'online_ui47.gml', 'online_ui49.gml', 'online_invite49.gml', 'online_tut51.gml', 'online_spec52.gml', 'online_skin52.gml', 'online_skin53.gml', 'online_boss53.gml', 'online_jevil52.gml', 'drbr53.gml', 'online_gerson53.gml', 'online_flowery53.gml', 'online_spamton53.gml', 'online_pink53.gml', 'drbr_save54.gml', 'ui.gml', 'ui_draw.gml', 'lyrics50.gml', 'cc50.gml', 'flowery50.gml', 'omega50.gml']
core = ''.join(open(T + f).read() for f in TEMPLATES)
# build 50: the KNIGHT tab's pages (one per DELTARUNE chapter) and the bosses planned for them (shown as COMING SOON)
pages = [f'    {{ ch: {int(pg["ch"])}, title: {q(pg["title"])} }}' for pg in K.get('pages', [{'ch': 3, 'title': 'CHAPTER 3'}])]
planned = [f'    {{ ch: {int(pl["ch"])}, key: {q(pl["key"])}, short: {q(pl["short"])}, name: {q(pl["name"])}, online: {b(pl.get("online", False))} }}' for pl in K.get('planned', [])]
core = core.replace('@@PAGES@@', ',\n'.join(pages)).replace('@@PLANNED@@', ',\n'.join(planned))
core = core.replace('@@REGISTRY@@', ',\n'.join(reg)).replace('@@SONGS@@', ',\n'.join(songs)).replace('@@SONGSV49@@', songs_v49).replace('@@HUBCREDITS@@', credits(K.get('hub_credits', [])))

# build 45: the online attack catalogue (tests/br_measure.py): per hub knight, the frames each attack runs (0: not usable online),
# and every object the online attacks make that the end of an attack has to take away (kbr_cut)
CAT = json.load(open('/home/claude/work/online/br_catalogue.json'))
cat_rows = []
atk_objs = set()
for v in K['variants']:
    n = len(atk_list(v['key']))
    row = [0] * n
    if not v['joke']:
        for a in CAT.get(str(v['id']), []):
            if a.get('err') is None and a.get('dur') and 0 <= a['ai'] < n:
                row[a['ai']] = int(a['dur'])
            atk_objs |= set(a.get('objs', []))
    cat_rows.append('[' + ', '.join(str(x) for x in row) + ']')
KEEP = {'obj_heart', 'obj_grazebox', 'obj_moveheart', 'obj_returnheart', 'obj_heartburst', 'obj_heart_follower', 'obj_heart_follower_overshoot', 'obj_growtangle',
        'obj_knight_split_growtangle', 'obj_lerpvar', 'obj_knight_enemy', 'obj_knight_twin', 'obj_knight_twin_bullet', 'obj_regularbullet', 'obj_bulletparent',
        'obj_collidebullet', 'obj_dbulletcontroller'}
# build 48: the Roaring of every knight (measured in the emulator by tests/roar_measure48.py): its length and the objects it makes
ROAR = json.load(open('/home/claude/work/online/roar48.json')) if os.path.exists('/home/claude/work/online/roar48.json') else {}
roar_rows = []
for v in K['variants']:
    # a Roaring that never ends its own turn (the Violet Knight's) is cut at 30 s; a long one (the Thorn Knight's, 60 s) at 40 s
    d = 900
    for a in ROAR.get(str(v['id']), []):
        if a.get('err') is None and a.get('dur') and a.get('why') == 'end':
            d = int(a['dur'])
        atk_objs |= set(a.get('objs', []))
    roar_rows.append(str(min(max(d, 120), 1200)))
atk_objs = sorted(o for o in atk_objs if o not in KEEP)
core = core.replace('@@ROARDUR@@', '[' + ', '.join(roar_rows) + ']')
core = core.replace('@@KBRCAT@@', '[' + ', '.join(cat_rows) + ']').replace('@@KBRATKOBJS@@', '[' + ', '.join(atk_objs) + ']')
# build 49: the build stamp's time (UTC, when this code was generated); KH_BUILDTIME pins it for a reproducible build
import datetime as _dt
core = core.replace('@@BUILDTIME@@', os.environ.get('KH_BUILDTIME') or _dt.datetime.now(_dt.timezone.utc).strftime('%Y-%m-%d %H:%M UTC'))
assert '@@' not in core, 'a template placeholder was left'
open(OUT + 'gml_GlobalScript_knight_core.gml', 'w').write(core)
objs = {'menu': 'obj_knight_menu', 'prompt': 'obj_knight_prompt', 'ctrl': 'obj_knight_ctrl', 'ghost_kris': 'obj_knight_ghost_kris', 'ghost_susie': 'obj_knight_ghost_susie',
        'ghost_ralsei': 'obj_knight_ghost_ralsei', 'firespell': 'obj_firespell', 'firehex': 'obj_firespell_hexagon', 'twin': 'obj_knight_twin', 'twinbullet': 'obj_knight_twin_bullet', 'bench': 'obj_knight_bench',
        'heart': 'obj_heart', 'herocc': 'obj_knight_herocc', 'omega': 'obj_knight_omega', 'skinart': 'obj_knight_skinart'}
n = 0
for f in sorted(os.listdir(T + 'events')):
    short, ev = f[:-4].rsplit('_', 2)[0], '_'.join(f[:-4].rsplit('_', 2)[1:])
    open(OUT + f'gml_Object_{objs[short]}_{ev}.gml', 'w').write(open(T + 'events/' + f).read())
    n += 1
# build 52: JEVIL's pieces from the player's Chapter 1 data.win (make_jevil.py writes them and their assets to the manifest)
import make_jevil
make_jevil.main()
for f in sorted(os.listdir('/home/claude/scripts/jevil_gen')):
    open(OUT + f, 'w').write(open('/home/claude/scripts/jevil_gen/' + f).read())
    n += 1
# DRBR: the other bosses' pieces, each from the player's own chapter data.win (make_<boss>.py -> <boss>_gen)
import make_gerson
make_gerson.main()
for f in sorted(os.listdir('/home/claude/scripts/gerson_gen')):
    open(OUT + f, 'w').write(open('/home/claude/scripts/gerson_gen/' + f).read())
# DRBR: Flowery (Chapter 5) - make_flowery.py: his pieces, the orange SOUL and the tower
import make_flowery
make_flowery.main()
for f in sorted(os.listdir('/home/claude/scripts/flowery_gen')):
    open(OUT + f, 'w').write(open('/home/claude/scripts/flowery_gen/' + f).read())
    n += 1
# DRBR: Spamton NEO (Chapter 2) - make_spamton.py: his pieces, his body, the yellow SOUL's shots
import make_spamton
make_spamton.main()
for f in sorted(os.listdir('/home/claude/scripts/spamton_gen')):
    open(OUT + f, 'w').write(open('/home/claude/scripts/spamton_gen/' + f).read())
    n += 1
# DRBR: Pink (Chapter 5) - make_pink.py: her pieces, the purple SOUL
import make_pink
make_pink.main()
for f in sorted(os.listdir('/home/claude/scripts/pink_gen')):
    open(OUT + f, 'w').write(open('/home/claude/scripts/pink_gen/' + f).read())
    n += 1
# build 47: base-game scripts the online battle reads differently (the same in every knight's code, so not in the merge):
# the camera's position as the attacks see it ignores a screen shake while an online match runs (kbr_cam_logical), so a
# shake (or REDUCED SHAKE, the game's own no-shake flag) never moves anybody's bullets
BASE = '/home/claude/work/gml/base/CodeEntries/'
def base_over(name, pairs):
    src = open(BASE + name + '.gml', encoding='utf8').read()
    out = src
    for a, b_ in pairs:
        assert out.count(a) == 1, (name, a)
        out = out.replace(a, b_)
    open(OUT + name + '.gml', 'w').write(out)
    return 1
n += base_over('gml_GlobalScript_camerax', [('    return camera_get_view_x(view_camera[0]);', '    if (kbr_cam_fix_on())\n        return kbr_cam_logical(0);\n    return camera_get_view_x(view_camera[0]);')])
n += base_over('gml_GlobalScript_cameray', [('    return camera_get_view_y(view_camera[0]);', '    if (kbr_cam_fix_on())\n        return kbr_cam_logical(1);\n    return camera_get_view_y(view_camera[0]);')])
n += base_over('gml_GlobalScript___view_get', [('            __res = camera_get_view_x(__cam);', '            __res = (__index == 0 && kbr_cam_fix_on()) ? kbr_cam_logical(0) : camera_get_view_x(__cam);'),
                                               ('            __res = camera_get_view_y(__cam);', '            __res = (__index == 0 && kbr_cam_fix_on()) ? kbr_cam_logical(1) : camera_get_view_y(__cam);')])
# DRBR: the projectile contract's fallback at the SOUL's contact (drbr53.gml: kbr_bullet_fix) - the root fix is in the pieces
n += base_over('gml_Object_obj_heart_Collision_obj_collidebullet', [('with (other)\n{\n    event_user(5);\n}', 'with (other)\n{\n    kbr_bullet_fix();\n    event_user(5);\n}')])
# build 47: the cold place as a room - your SKIN drawn in Kris's place (his sprite, mask and speed stay: kfo_world_self_draw)
n += base_over('gml_Object_obj_mainchara_Draw_0', [('if (swordmode == 0)\n{\n    draw_self();\n}', 'if (swordmode == 0)\n{\n    if (!kfo_world_self_draw())\n        draw_self();\n}\n// build 50: a save past the Knight Hub point in the hub\'s room: no sign there - say so\nknight_hub_hint_draw();\n// DRBR (update 10): in the DRBR install, a short line on arrival says where the hub and ONLINE are\nkdr_hint_draw();')])
# DRBR (update 10): the DRBR install's save profile (drbr_save54.gml). In DRBR mode the game starts straight in the
# provided starting save, and every story file goes to drbr_profile/ (the player's own saves are never touched); outside
# the DRBR install (no drbr_data/drbr_profile.cfg next to data.win) kdr_on() is 0 and these hooks change nothing.
n += base_over('gml_Object_obj_initializer2_Step_0', [('    room_goto(roomchoice);\n}', '    if (!kdr_boot())\n        room_goto(roomchoice);\n}')])
n += base_over('gml_GlobalScript_ossafe_ini_open', [('        ini_open(arg0);', '        ini_open(kdr_path(arg0));')])
n += base_over('gml_GlobalScript_ossafe_file_text_open_read', [('        return file_text_open_read(arg0);', '        return file_text_open_read(kdr_path(arg0));')])
n += base_over('gml_GlobalScript_ossafe_file_text_open_write', [('        return file_text_open_write(arg0);', '        return file_text_open_write(kdr_path(arg0));')])
n += base_over('gml_GlobalScript_ossafe_file_exists', [('        return file_exists(arg0);', '        return file_exists(kdr_path(arg0));')])
n += base_over('gml_GlobalScript_ossafe_file_delete', [('        return file_delete(arg0);', '        return file_delete(kdr_path(arg0));')])
n += base_over('gml_GlobalScript_scr_chapterswitch', [('function scr_chapterswitch(arg0 = 0)\n{\n', 'function scr_chapterswitch(arg0 = 0)\n{\n    if (kdr_on())\n    {\n        kdr_chapter_switch(arg0);\n        exit;\n    }\n')])


def merged_over(name, pairs):
    """an entry the merge already wrote (a knight mod's own copy of a base script), patched in place - idempotent like
    br_patch: (old, new, mark, want): the old text found + the mark of a patched one found must be want"""
    p_ = OUT + name + '.gml'
    out = open(p_, encoding='utf8').read()
    for a, b_, mark, want in pairs:
        n_old = len(a.findall(out)) if isinstance(a, re.Pattern) else out.count(a)
        n_new = out.count(mark)
        assert n_old + n_new == want, (name, getattr(a, 'pattern', a), n_old, n_new, want)
        if n_old:
            out = a.sub(lambda m: b_, out) if isinstance(a, re.Pattern) else out.replace(a, b_)
    open(p_, 'w', encoding='utf8').write(out)
    return 0


# the DELTARUNE CONFIG menu's own (non-ossafe) keyconfig write, and the DRBR start check every frame
merged_over('gml_Object_obj_darkcontroller_Step_0', [(re.compile(r'(?<!ossafe_)ini_open\("keyconfig_" \+ string\(global\.filechoice\) \+ "\.ini"\);'), 'ini_open(kdr_path("keyconfig_" + string(global.filechoice) + ".ini"));', 'ini_open(kdr_path("keyconfig_"', 2)])
_gc = OUT + 'gml_Object_obj_gamecontroller_Step_1.gml'
_t = open(_gc, encoding='utf8').read()
assert _t.count('kdr_frame();') in (0, 1), 'kdr_frame twice in obj_gamecontroller Begin Step'
if not _t.startswith('kdr_frame();\n'):
    open(_gc, 'w', encoding='utf8').write('kdr_frame();\n' + _t)
# build 50: the KF Song Pack's code (scr_kf_song, scr_kf_lyrics_fx, obj_kf_songlyrics), as the pack has it (its gml folder)
for f in sorted(os.listdir(T + 'kfsong')):
    open(OUT + f, 'w').write(open(T + 'kfsong/' + f).read())
    n += 1
print('hub entries written:', n + 1)
# build 45: the attack code draws its randomness from the shared stream (det_rewrite), and the battle hooks of the shared battle
import det_rewrite, br_patch, det_sent
det_rewrite.main()
# build 50: the players' attack skills are the Knights' real attack objects - wrapped (det_sent.py)
det_sent.main()
br_patch.main()
