"""Build 47: the cold place (room_dw_snow_zone) in the emulator, for the online overworld tests (t_ow47.py).

The room is made from the game's own room data (data/ow_dump.tsv, dumped from data.win by UTMT: the room's size, its
instances with their positions and scales, the sprites' sizes / origins / collision boxes). Kris (obj_mainchara: its own
Create / Step / End Step / Draw), the dark world controller that makes the party followers (its own Create), the followers
(obj_caterpillarchara: own Create / End Step), the original Knight encounter's controller (obj_ch3_PTB02: the merged
Create / Step, every knight's version) and the collision blocks are the real objects running the real code. The emulator has
no collision masks, so place_meeting is done here: axis-aligned boxes from each sprite's collision box (origin, margins)
times the instance's scale - the same boxes the game uses for these sprites (AxisAlignedRect masks; the room's diagonal
blocks and the small precise "sul" blocks are far from the encounter and are counted as their boxes)."""
import os, re, sys, glob
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from harness import *

HERE = os.path.dirname(os.path.abspath(__file__))
SPR = {}
ROOMI = []
ROOMSZ = (640, 480)
for _ln in open(os.path.join(HERE, 'data', 'ow_dump.tsv')):
    _p = _ln.rstrip('\n').split('\t')
    if _p[0] == 'SPR' and len(_p) >= 11 and _p[2] != 'MISSING':
        SPR[_p[1]] = dict(w=int(_p[2]), h=int(_p[3]), xo=int(_p[4]), yo=int(_p[5]), ml=int(_p[6]), mr=int(_p[7]), mt=int(_p[8]), mb=int(_p[9]), n=int(_p[10]))
    elif _p[0] == 'INST':
        ROOMI.append(dict(layer=_p[1], obj=_p[2], x=float(_p[3]), y=float(_p[4]), xs=float(_p[5]), ys=float(_p[6])))
    elif _p[0] == 'ROOM':
        ROOMSZ = (int(_p[2]), int(_p[3]))

OBJIDX = obj_index_table()
PARENTS = {}
for _ln in open('/home/claude/work/idx/objparents.tsv'):
    _p = _ln.rstrip('\n').split('\t')
    if len(_p) >= 4:
        PARENTS[_p[1]] = (_p[2], _p[3])

SOLIDS = ['obj_solidblock', 'obj_solidblocksized', 'obj_solidblock_32', 'obj_sul', 'obj_solidblock_diagonal_32']
OW_OBJS = ['obj_mainchara', 'obj_caterpillarchara', 'obj_darkcontroller', 'obj_ch3_PTB02', 'obj_overworldheart', 'obj_npc_sign', 'obj_savepoint',
           'obj_markerAny', 'obj_doorAny'] + SOLIDS


def code(name):
    """the merged entry if the hub changed it, else the base game's"""
    for d in (M, B):
        p = d + name + '.gml'
        if os.path.exists(p):
            return p
    return None


def spr_name(sim, idx):
    if not hasattr(sim, '_spr_rev') or len(sim._spr_rev) != len(sim.assets):
        sim._spr_rev = {v: k for k, v in sim.assets.items()}
    return sim._spr_rev.get(idx)


def bbox(sim, inst, x=None, y=None):
    v = inst.vars
    m = v.get('mask_index', -1)
    s = m if (isinstance(m, (int, float)) and m >= 0) else v.get('sprite_index', -1)
    nm = spr_name(sim, s) if isinstance(s, (int, float)) and s >= 0 else None
    d = SPR.get(nm)
    if d is None:
        return None
    xs = float(v.get('image_xscale', 1))
    ys = float(v.get('image_yscale', 1))
    xx = float(v.get('x', 0)) if x is None else float(x)
    yy = float(v.get('y', 0)) if y is None else float(y)
    l = xx + (d['ml'] - d['xo']) * xs
    r = xx + (d['mr'] + 1 - d['xo']) * xs
    t = yy + (d['mt'] - d['yo']) * ys
    b = yy + (d['mb'] + 1 - d['yo']) * ys
    return (min(l, r), min(t, b), max(l, r), max(t, b))


def _hit(a, b):
    return a is not None and b is not None and a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]


def _targets(sim, obj):
    try:
        n = int(obj)
    except Exception:
        return []
    if n >= 100000:
        i = sim.instances.get(n)
        return [i] if i is not None and not i.dead else []
    return [i for i in sim.instances_of(n) if not i.dead]


def place_meeting(sim, f, x, y, obj):
    me = f.self
    a = bbox(sim, me, x, y)
    for i in _targets(sim, obj):
        if i is me:
            continue
        if _hit(a, bbox(sim, i)):
            return True
    return False


def instance_place(sim, f, x, y, obj):
    me = f.self
    a = bbox(sim, me, x, y)
    for i in _targets(sim, obj):
        if i is not me and _hit(a, bbox(sim, i)):
            return i.id
    return -4


def collision_rectangle(sim, f, x1, y1, x2, y2, obj, prec, notme):
    a = (min(float(x1), float(x2)), min(float(y1), float(y2)), max(float(x1), float(x2)) + 1, max(float(y1), float(y2)) + 1)
    for i in _targets(sim, obj):
        if notme and i is f.self:
            continue
        if _hit(a, bbox(sim, i)):
            return i.id
    return -4


KW = {'if', 'for', 'while', 'switch', 'return', 'with', 'repeat', 'until', 'function', 'catch', 'try', 'do', 'case', 'else', 'new',
      'not', 'div', 'mod', 'and', 'or', 'xor', 'exit', 'break', 'continue', 'var', 'static', 'globalvar', 'enum', 'default', 'throw',
      'delete', 'constructor'}
# scripts that stay mocked (sound, saving, the debug key, the game's text system): their effect is not what is tested here
KEEP_MOCKED = {'scr_debug', 'snd_play', 'snd_play_x', 'snd_stop', 'snd_volume', 'snd_free_all', 'snd_stop_all', 'snd_loop', 'snd_pitch',
               'mus_play', 'mus_loop', 'mus_volume', 'mus_stop', 'scr_84_load_ini', 'ossafe_savedata_save', 'scr_save', 'scr_load',
               'scr_84_get_lang_string', 'stringsetloc', 'stringset', 'scr_84_get_subst_string', 'scr_84_get_sprite', 'scr_84_get_font',
               'scr_84_set_draw_font', 'sunkus_kb_check_pressed', 'sunkus_kb_check', 'scr_steam_achievement', 'scr_achievement'}


def closure_load(sim, texts):
    """the game's own scripts the room's code calls (and the ones those call), loaded from the base game; what has no script
    of its own is mocked (returns 0); every object the code names is defined with the game's number"""
    from gmlsim.registry import DEFAULT_BUILTINS
    seen = set()
    todo = list(texts)
    objn = set()
    assets = set()
    loaded = 0
    mocked = 0
    while todo:
        t = todo.pop()
        objn |= set(re.findall(r'(?<![\w.])(obj_[A-Za-z0-9_]+)', t))
        t2 = re.sub(r'"(?:\\.|[^"\\])*"', '""', t)
        assets |= set(re.findall(r'(?<![\w.])((?:spr|snd|mus|bg|fnt|room|path|shd)_[A-Za-z0-9_]+)', t2))
        for n in set(re.findall(r'(?<![\w.])([A-Za-z_]\w*)\s*\(', t2)):
            if n in seen or n in KW:
                continue
            seen.add(n)
            if n in KEEP_MOCKED:
                if n not in sim.mocked:
                    sim.mock(n, 0)
                continue
            if n in DEFAULT_BUILTINS or n in sim.scripts or n in getattr(sim, 'script_entries', {}) or n in sim.mocked:
                continue
            p = B + 'gml_GlobalScript_%s.gml' % n
            if os.path.exists(p) and n not in ('scr_debug',):
                try:
                    sim.load_file(p, entry='gml_GlobalScript_%s' % n)
                    todo.append(open(p, encoding='utf8', errors='replace').read())
                    loaded += 1
                    continue
                except Exception:
                    pass
            if n.startswith('obj_'):
                continue
            sim.mock(n, 0)
            mocked += 1
    for o in sorted(objn):
        if o not in sim.objects:
            try:
                sim.define_object(o, index=OBJIDX.get(o) if OBJIDX.get(o) not in sim.obj_by_index else None)
            except Exception:
                pass
    for a in sorted(assets):
        try:
            sim.eval(a)
        except Exception:
            try:
                sim.define_asset(a)
            except Exception:
                pass
    sim.closure = (loaded, mocked)
    return loaded, mocked


def ow_sim(name='Kris', skin=1, variant=0, plot=320, facing=0):
    """a game in the cold place (offline until a room is made / joined); returns the sim (the room is entered with enter())"""
    sim = make_sim()
    sim.run('knight_store_load(); global.knight_cfg = knight_cfg_default(); knight_ensure_ctrl();')
    sim.run('kfo_get(); global.kfo.name = "%s"; global.kfo.skin = %d;' % (name, skin))
    sim.nm = name
    # the room's objects with the game's object numbers (the code compares them: obj_heart is 1463 and so on)
    for o in OW_OBJS:
        par = PARENTS.get(o, ('', ''))[0] or None
        if par and par not in sim.objects:
            sim.define_object(par, index=OBJIDX.get(par))
        if o in sim.objects:
            od = sim.objects[o]
            if o in OBJIDX and od.index != OBJIDX[o]:
                sim.obj_by_index.pop(od.index, None)
                od.index = OBJIDX[o]
                sim.obj_by_index[od.index] = o
                sim.names[o] = od.index
            if par:
                od.parent = par
        else:
            sim.define_object(o, parent=par, index=OBJIDX.get(o))
    sim.desc_cache.clear(); sim.chain_cache.clear(); sim.events_cache.clear()
    for nm in SPR:
        sim.define_asset(nm)
    for o in OW_OBJS:
        sp = PARENTS.get(o, ('', ''))[1]
        if sp:
            sim.define_asset(sp)
            sim.objects[o].sprite = sim.eval(sp)
    sim.sys_state['sprite_sizes'] = {sim.eval(n): (d['w'], d['h']) for n, d in SPR.items()}
    # the objects' own code
    texts = []
    for o, evs in [('obj_mainchara', ['Create_0', 'Step_0', 'Step_2', 'Alarm_1', 'Draw_0']),
                   ('obj_caterpillarchara', ['Create_0', 'Step_2', 'Draw_0']),
                   ('obj_darkcontroller', ['Create_0']),
                   ('obj_ch3_PTB02', ['Create_0', 'Step_0']),
                   ('obj_npc_sign', ['Create_0'])]:
        for ev in evs:
            p = code('gml_Object_%s_%s' % (o, ev))
            if p:
                sim.load_file(p, entry=os.path.basename(p)[:-4])
                texts.append(open(p, encoding='utf8', errors='replace').read())
    closure_load(sim, texts)
    for fn, impl in [('place_meeting', place_meeting), ('instance_place', instance_place), ('collision_rectangle', collision_rectangle)]:
        sim.mock(fn, impl, frame=True)
    sim.mock('scr_debug', 0)
    # the sprites' own frame counts and origins (the emulator's defaults are 0)
    sim.mock('sprite_get_number', lambda s, i: SPR.get(spr_name(s, i), {}).get('n', 1))
    sim.mock('sprite_get_xoffset', lambda s, i: SPR.get(spr_name(s, i), {}).get('xo', 0))
    sim.mock('sprite_get_yoffset', lambda s, i: SPR.get(spr_name(s, i), {}).get('yo', 0))
    # the game's rooms by name (the code adds / compares them)
    for _ln in open('/home/claude/work/idx/merged.tsv'):
        _p = _ln.rstrip('\n').split('\t')
        if len(_p) >= 3 and _p[0] == 'room' and _p[2] not in sim.rooms:
            try:
                sim.define_asset(_p[2])
            except Exception:
                pass
    # the room as data.win has it (the three other cutscene controllers of the room - GSB05, BTB04, PTB01 - and the room's
    # parallax are left out: none of them is in this test)
    inst = []
    for r in ROOMI:
        if r['obj'] in ('obj_ch3_GSB05', 'obj_ch3_BTB04', 'obj_ch3_PTB01', 'obj_dw_snow_zone_parallax', 'obj_doorAny', 'obj_markerAny'):
            continue
        inst.append((r['obj'], r['x'], r['y'], {'image_xscale': r['xs'], 'image_yscale': r['ys']}))
    sim.define_room('room_dw_snow_zone', instances=inst, width=ROOMSZ[0], height=ROOMSZ[1])
    sim.define_room('room_ow_test_other', instances=[('obj_mainchara', 200, 240, {'image_xscale': 2, 'image_yscale': 2}), ('obj_darkcontroller', 0, 0, {})], width=1280, height=480)
    sim.run('global.screen_border_id = 0; global.lang = "en"; global.darkzone = 1; global.chapter = 3; global.plot = %d; global.facing = %d; global.interact = 0; global.entrance = 0; global.char = [1, 2, 3];'
            'global.knight_variant = %d; global.knight_variant_pending = %d;' % (plot, facing, variant, variant))
    sim.run('for (var _i = array_length(global.flag); _i < 2000; _i++) global.flag[_i] = 0; global.tempflag = array_create(100, 0); global.tempflag[90] = 0;')
    sim.inp.update({'up': 0, 'down': 0, 'left': 0, 'right': 0})
    gm_room_order(sim)
    return sim


def gm_room_order(sim):
    """the runner's order for a room change: the frame that asked for it still draws the old room, the new room's instances
    are made after that frame (Create, Room Start), and their first Draw comes after a full step of the new room - the
    emulator alone would make them before this frame's Draw. After each frame's Draw, what was drawn awake is noted
    (sim.awake_at_draw: the party followers awake while the frame was drawn)"""
    orig_frame = sim._frame
    orig_change = sim._change_room
    sim.awake_at_draw = 0

    def deferred():
        sim._pend_room = sim.pending_room
        sim.pending_room = None

    def frame(draw):
        sim._pend_room = None
        sim._change_room = deferred
        try:
            orig_frame(draw)
        finally:
            sim._change_room = orig_change
        sim.awake_at_draw = len([i for i in sim.instances_of('obj_caterpillarchara') if not i.dead and i.vars.get('visible', True)])
        if sim._pend_room is not None:
            sim.pending_room = sim._pend_room
            sim._pend_room = None
            orig_change()
    sim._frame = frame


def enter(sim, room='room_dw_snow_zone'):
    if sim.room_started:
        sim.goto_room(room)
        ow_step(sim)
    else:
        sim.start(room)


def held(sim, keys):
    for k in ('up', 'down', 'left', 'right', 'ok', 'back', 'alt'):
        sim.inp[k] = 1 if k in keys else 0


def ow_step(sim, n=1):
    """frames as the game runs them: xprevious / yprevious first (the runner sets them before the step), then the events"""
    for _ in range(n):
        for i in list(sim.instances.values()):
            if not i.dead:
                i.vars['xprevious'] = i.vars.get('x', 0)
                i.vars['yprevious'] = i.vars.get('y', 0)
        sim.step(1)


def mc(sim):
    l = [i for i in sim.instances_of('obj_mainchara') if not i.dead]
    return l[0] if l else None


def followers(sim, active_only=True):
    return [i for i in sim.instances_of('obj_caterpillarchara') if not i.dead]


def deactivated_followers(sim):
    d = sim.descendants('obj_caterpillarchara')
    return [i for i in sim.deact.values() if i.obj in d and not i.dead]
