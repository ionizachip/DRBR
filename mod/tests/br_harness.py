"""Build 45 battle royale harness: a real knight battle in the emulator (merged fight code, the online lineup) run the way
the online battle runs it - no player turns, the SOUL stays, one attack after another.
The base game's code for every object the Knights' attacks can make is loaded up front, so the frames can run without the
whole-state snapshot auto() takes before each one (that snapshot costs more than the frame with 100+ bullets)."""
import sys, os, re, glob, json, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from harness import *
from lu_harness import *

KN = ['base', 'kaizo', 'elec', 'violet', 'thorn', 'cyan']
BDIR = '/home/claude/work/gml/base/CodeEntries/'
MDIR = M  # harness.M: the build's merged code, or KH_MERGED (the round trip runs the tests on code decompiled from the built data.win)
EVRE = re.compile(r'(Create_0|Step_0|Step_1|Step_2|Alarm_\d+|Other_\d+|Destroy_0|CleanUp_0|Collision_\w+|PreCreate_0)$')

BR_STUB = '''reset = (variable_instance_exists(id,"reset")) ? reset : 0;
if (global.mnfight == 2) { global.turntimer -= 1; global.TT_active = 1;
 if (global.turntimer <= 0 && reset == 0 && !kbr_hold_end()) { with (obj_bulletparent) instance_destroy(); with (obj_bulletgenparent) instance_destroy(); with (obj_heart) instance_destroy(); reset = 1; global.TT_end = global.TT_f; global.mnfight = 0; }
 if (global.turntimer <= 0 && reset == 0 && kbr_hold_end()) { global.TT_end = global.TT_f; } }
global.TT_f += 1;'''


def _static_closure():
    """every object the knight and the bullet controller can make (by name in their code), transitively"""
    files = {}
    for d in (BDIR, MDIR):
        for f in os.listdir(d):
            files[f] = d + f
    objcode = {}
    for f in files:
        m = re.match(r'gml_Object_(.+?)_(Create|Step|Draw|Alarm|Other|Collision|Destroy|CleanUp|PreCreate)_', f)
        if m:
            objcode.setdefault(m.group(1), []).append(f)
    seen = set()
    stack = ['obj_knight_enemy', 'obj_dbulletcontroller', 'obj_moveheart', 'obj_returnheart', 'obj_heart', 'obj_grazebox']
    # DRBR: the base parents of the bosses' pieces (their events run through event_inherited: Pink's hearts are obj_bullet_healing)
    try:
        stack += sorted(set(p for o, p in boss_parents() if p and not re.match(r'obj_(jv|hj|fl|sn|pk)_', p)))
    except Exception:
        pass
    while stack:
        o = stack.pop()
        if o in seen:
            continue
        seen.add(o)
        for f in objcode.get(o, []):
            t = open(files[f], encoding='utf8', errors='replace').read()
            for c in re.findall(r'(?:instance_create(?:_depth|_layer)?|scr_bulletspawner|scr_fire_bullet)\s*\([^;]*?\b(obj_[A-Za-z0-9_]+)', t):
                if c not in seen:
                    stack.append(c)
    return seen


def preload_base(sim):
    n = 0
    for o in sorted(_static_closure()):
        for p in glob.glob(BDIR + 'gml_Object_%s_*.gml' % o):
            bn = os.path.basename(p)
            ev = bn[len('gml_Object_%s_' % o):-4]
            if os.path.exists(MDIR + bn) or not EVRE.match(ev):
                continue
            try:
                sim.define_object(o)
            except Exception:
                pass
            try:
                sim.load_file(p, entry=bn[:-4])
                n += 1
            except Exception:
                pass
    # (DRBR: the game's language, set at its start: Chapter 2's pipis sign reads it)
    try:
        sim.run('if (!variable_global_exists("lang")) global.lang = "en";')
        # (Chapter 3's scr_gamestart sets the frame clock the knights' afterimages read - obj_knight_rotating_slash: global.time)
        sim.run('if (!variable_global_exists("time")) global.time = 0;')
    except Exception:
        pass
    return n


KW = {'if', 'for', 'while', 'switch', 'return', 'with', 'repeat', 'until', 'function', 'catch', 'try', 'do', 'case', 'else', 'new',
      'not', 'div', 'mod', 'and', 'or', 'xor', 'exit', 'break', 'continue', 'var', 'static', 'globalvar', 'enum', 'default', 'throw',
      'delete', 'constructor'}


def collide_list_mock(sim, x1, y1, x2, y2, obj, prec, notme, lst, ordered=False):
    """collision_rectangle_list as the bots use it: the emulator has no sprite masks, so a bullet counts when its origin is
    within 8 px of the rectangle's middle (the box's split halves are outlines in the game: never)"""
    cx, cy = (float(x1) + float(x2)) / 2.0, (float(y1) + float(y2)) / 2.0
    n = 0
    out = sim.ds_list(lst)
    for inst in sim.instances_of(obj):
        if inst.dead or 'growtangle' in inst.obj:
            continue
        try:
            ix, iy = float(inst.vars.get('x', -99999)), float(inst.vars.get('y', -99999))
        except Exception:
            continue
        if abs(ix - cx) < 8 and abs(iy - cy) < 8:
            out.append(inst.id)
            n += 1
    return n


def real_soul_sprites(sim):
    """build 47: the SOUL objects' own sprite as in data.win (obj_moveheart / obj_returnheart / obj_heart: spr_dodgeheart,
    Chapter 3's SOUL with its black edge; obj_moveheart hands its sprite to the SOUL it makes)"""
    if 'spr_dodgeheart' not in sim.assets:
        sim.define_asset('spr_dodgeheart')
    for o in ('obj_heart', 'obj_moveheart', 'obj_returnheart'):
        if o in sim.objects:
            sim.objects[o].sprite = sim.assets['spr_dodgeheart']
    for i in sim.instances_of('obj_heart'):
        if i.vars.get('sprite_index', -1) in (-1, None):
            i.vars['sprite_index'] = sim.assets['spr_dodgeheart']


def premock(sim):
    """mock every function the attack code (and the scripts it calls) can reach that the emulator does not know, and
    define every asset name it mentions - up front, so frames never need auto()'s snapshot-and-retry"""
    sim.mock('collision_rectangle_list', collide_list_mock)
    from gmlsim.registry import DEFAULT_BUILTINS
    from emu_end import DUM
    files = {}
    for d in (BDIR, MDIR):
        for f in os.listdir(d):
            files[f] = d + f
    objs = _static_closure()
    texts = []
    # DRBR: the bosses' objects too, their Draw events included (boss_draws loads them)
    brx = re.compile(r'gml_Object_(obj_(?:%s)_\w+?)_(Create|Step|Alarm|Other|Collision|Destroy|CleanUp|PreCreate|Draw)_' % '|'.join(BOSS_PREFIX))
    for f, p in files.items():
        m = re.match(r'gml_Object_(.+?)_(Create|Step|Alarm|Other|Collision|Destroy|CleanUp|PreCreate)_', f)
        if (m and m.group(1) in objs) or brx.match(f):
            texts.append(open(p, encoding='utf8', errors='replace').read())
        elif f.startswith('gml_GlobalScript_'):
            texts.append(open(p, encoding='utf8', errors='replace').read())
    names = set()
    assets = set()
    objn = set()
    for t in texts:
        objn |= set(re.findall(r'(?<![\\w.])(obj_[A-Za-z0-9_]+)', t))
        t = re.sub(r'"(?:\\.|[^"\\])*"', '""', t)
        names |= set(re.findall(r'(?<![\w.])([A-Za-z_]\w*)\s*\(', t))
        assets |= set(re.findall(r'(?<![\w.])((?:spr|snd|mus|bg|fnt|font|room|path|tile|shd|pal)_[A-Za-z0-9_]+)', t))
    nm = 0
    for n in sorted(names):
        if n in KW or n in DEFAULT_BUILTINS or n in sim.scripts or n in getattr(sim, 'script_entries', {}) or n in getattr(sim, 'mocked', {}):
            continue
        if n.startswith('obj_'):
            continue
        try:
            sim.mock(n, (lambda nn: (lambda sm, *a: DUM(sm)))(n))
            nm += 1
        except Exception:
            pass
    no = 0
    for o in sorted(objn):
        if o not in sim.objects:
            try:
                sim.define_object(o)
                no += 1
            except Exception:
                pass
    na = 0
    for a in sorted(assets):
        try:
            sim.eval(a)
        except Exception:
            try:
                sim.define_asset(a)
                na += 1
            except Exception:
                pass
    real_soul_sprites(sim)
    return nm, na, no


def br_battle(open_k=0, kn=(0, 1, 2, 3, 4), skin=1, seed=777, rng_seed=1, extra='', stub=None):
    """a practice room of one, its match started, the battle made under the opening knight's variant"""
    setc = '{ kn: %s, open: %d, ramp: 1, maxst: 4, sends: 0, maxp: 8, bots: 0 }' % (json.dumps(list(kn)), open_k)
    ex = ('global.is_console = 0; kfo_get(); global.kfo.name = "Kris"; global.kfo.skin = %d; global.kfo.set = kfo_set_clean(%s); global.kfo.set.bots = 0;'
          'kfo_practice_start(); kfo_tick();'
          'var _H = global.kfo.H; _H.st = "match"; _H.mid = 1; _H.seed = %d; _H.mset = kfo_set_clean(global.kfo.set); _H.startn = 1;'
          '_H.pl[0].inm = 1; _H.pl[0].al = 1;'
          'global.kfo.M = kfo_match_new({ mid: 1, seed: %d, set: global.kfo.set, players: [{ pid: 1, n: "Kris", s: %d, bot: 0 }], prac: 1 });'
          'global.kfo.M.launched = true;' + extra) % (skin, setc, seed, seed, skin)
    sim, e = lu_battle(KN[open_k], party=(skin,), combo=3, extra_cfg=ex, world=False)
    if e is not None:
        return None, e
    sim.rng.seed(rng_seed)
    preload_base(sim)
    sim.premocked = premock(sim)
    sim.define_event('obj_battlecontroller', 'Step', 0, stub or BR_STUB)
    r = frames(sim, 6)
    if r is not None:
        return None, r
    sim._snapauto = False
    return sim, None


# DRBR: SOUL / bullet collisions (collide.py) - on for the tests that ask for them (COLLIDE = True or KH_COLLIDE=1)
COLLIDE = bool(os.environ.get('KH_COLLIDE'))


# DRBR: real division by zero as the game's runner does it (IEEE: inf / nan - Chapter 4's shipped Gerson fight relies on it);
# div / mod by zero still fail. KH_DIV0=error for the old strict mode.
DIV0 = os.environ.get('KH_DIV0', 'real')


def _step1(sim):
    if getattr(sim, 'div_zero', None) != DIV0:
        sim.set_div_zero(DIV0)
    sim.step(1)
    if COLLIDE:
        import collide
        collide.pump(sim)


def step(sim, n=1):
    for _ in range(n):
        good, err = auto(sim, lambda: _step1(sim))
        if not good:
            return err
    return None


OKREG = [0, 1, 2, 3, 4, 0, 0, 0, 0, 0, 0, 0, 0, 0]   # build 52: 6 = Jevil (the battle is the Normal Knight's); DRBR: 7+ the other bosses (the same)


# build 52: the emulator makes an asset known when code first names it; the game has them all from the start - Jevil's battle
# object and look are asked for (kbr_enc_ready) before any of his code runs
JV_ASSETS = ['obj_jv_joker', 'obj_jv_body', 'obj_jv_bg', 'obj_jv_dbc', 'spr_jv_joker_main', 'obj_hj_gerson', 'obj_hj_bg', 'spr_hj_gerson_idle',
             'obj_fl_flowery', 'spr_fl_flowery_idle3', 'obj_sn_neo', 'spr_sneo_example', 'obj_sn_ysoul', 'obj_sn_bg']


# their parents as the built data.win has them (jevil/built_assets.tsv) - the emulator's with() over a parent reaches them then
JV_PARENTS = [('obj_jv_teleport', 'obj_bulletparent'), ('obj_jv_spadering', 'obj_bulletparent'), ('obj_jv_suitbomb', 'obj_bulletparent'),
              ('obj_jv_heartblast', 'obj_bulletparent'), ('obj_jv_regbp', 'obj_regularbullet'), ('obj_jv_carousel', 'obj_jv_regbp'),
              ('obj_jv_cscythe', 'obj_jv_regbp'), ('obj_jv_lscythe', 'obj_jv_regbp'), ('obj_jv_bscythe', 'obj_jv_regbp'),
              ('obj_jv_clubs', 'obj_bulletparent'), ('obj_jv_dvert', 'obj_collidebullet'), ('obj_jv_joker', 'obj_monsterparent'),
              ('obj_jv_dbc', 'obj_bulletgenparent')]


_BOSS_PARENTS = []


def boss_parents():
    """DRBR: every imported boss object (build/assets.json, the ones with a "boss" key) and its parent as the build makes it (the
    source's parent, renamed when it is imported too)"""
    if not _BOSS_PARENTS:
        A = json.load(open('/home/claude/work/build/assets.json'))
        ren = A['rename']
        tabs = {}
        for m in A['manifest']['objects']:
            if 'boss' not in m:
                continue
            src = m['src']
            if src not in tabs:
                t = {}
                for l in open('/home/claude/work/src/%s/assets.tsv' % src, encoding='utf8'):
                    r = l.rstrip('\n').split('\t')
                    if r[0] == 'obj':
                        t[r[1]] = r[2]
                tabs[src] = t
            par = tabs[src].get(m['name'], '')
            par = ren.get(src, {}).get(par, par) if par else None
            _BOSS_PARENTS.append((m['new'], par or None))
        _BOSS_PARENTS.append(('obj_drbr_none', None))
    return _BOSS_PARENTS


_BOSS_ASSETS = []


def boss_assets():
    """DRBR: every sprite and sound the build imports for a boss (build/assets.json) - the game has them from the start (the
    emulator would take a name it has not met for an instance variable: Gerson's motor_swing_down sound)"""
    if not _BOSS_ASSETS:
        A = json.load(open('/home/claude/work/build/assets.json'))
        for kind in ('sprites', 'sounds'):
            for m in A['manifest'][kind]:
                if 'boss' in m:
                    _BOSS_ASSETS.append(m['new'])
    return _BOSS_ASSETS


def jv_assets(sim):
    for o, p in JV_PARENTS:
        sim.define_object(o, parent=p)
    # DRBR: the other bosses' objects (their parents first: a child's parent must be known)
    todo = list(boss_parents())
    done = set(sim.objects)
    for _ in range(4):
        rest = []
        for o, p in todo:
            if p is None or p in done or p in sim.objects:
                sim.define_object(o, parent=p)
                done.add(o)
            else:
                rest.append((o, p))
        todo = rest
    for o, p in todo:
        sim.define_object(o, parent=p)
    for a in JV_ASSETS + boss_assets():
        try:
            sim.define_asset(a)
        except Exception:
            pass
    if BOSS_DRAW:
        boss_draws(sim)


# DRBR: the bosses' own Draw events run too. The fight harnesses load no Draw code for the knights' attacks (speed: their
# Draws only draw), but the ported bosses keep game logic in theirs (Gerson's chevron makes the shield in its Draw, Jevil's
# background reads the camera there - the build 51 e__VW crash was a Draw's), so a boss test without them misses real errors
BOSS_DRAW = True
BOSS_PREFIX = ('jv', 'hj', 'fl', 'sn', 'pk')


# DRBR: the battle camera as the game has it - 640 x 480 (the emulator's camera answers 0 for everything), and where it is in
# the room: CAM (the knights' tests: (0, 0); a boss test can move it to catch code that takes the camera for the room's corner)
CAM = tuple(int(v) for v in os.environ.get('KH_CAM', '0,0').split(','))


def boss_draws(sim):
    sim.mock('camera_get_view_x', lambda s, *a: CAM[0])
    sim.mock('camera_get_view_y', lambda s, *a: CAM[1])
    sim.mock('camera_get_view_width', lambda s, *a: 640)
    sim.mock('camera_get_view_height', lambda s, *a: 480)
    # what the game's start has made by then: the palette swapper (obj_initializer2: pal_swap_init_system) and a sprite's UVs
    sim.mock('sprite_get_uvs', lambda s, *a: s.eval('[0, 0, 1, 1, 0, 0, 1, 1]'))
    # (the dark world's flag the game sets long before: Chapter 4's shakes read it)
    sim.run('if (!variable_global_exists("darkzone")) global.darkzone = 1;')
    try:
        sim.run('if (!variable_global_exists("retro_pal_swapper")) pal_swap_init_system(18);')
    except Exception as e:
        print('boss_draws: no palette swapper (%s)' % str(e)[:120])
    n = 0
    rx = re.compile(r'gml_Object_(obj_(?:%s)_\w+?)_Draw_\d+$' % '|'.join(BOSS_PREFIX))
    for p in sorted(glob.glob(MDIR + 'gml_Object_obj_*_Draw_*.gml')):
        bn = os.path.basename(p)[:-4]
        m = rx.match(bn)
        if not m:
            continue
        try:
            if m.group(1) not in sim.objects:
                sim.define_object(m.group(1))
            sim.load_file(p, entry=bn)
            n += 1
        except Exception as e:
            print('boss_draws: %s not loaded (%s)' % (bn, str(e)[:120]))
    return n


def br_match(open_ok=0, kn=(0, 1, 2, 3, 4, 5), skin=1, seed=4242, setx='', bots=0, rng_seed=1, stub=None, me_name='Kris', world=False):
    """a practice room of one (and bots): the host's START as in the game, the battle made under the first cycle's knight.
    setx: GML that changes _s (the settings) before the start."""
    ex = ('global.is_console = 0; kfo_get(); global.kfo.name = "%s"; global.kfo.skin = %d;'
          'var _s = kfo_set_clean({ kn: %s, open: %d, bots: %d }); %s global.kfo.set = kfo_set_clean(_s);'
          'kfo_practice_start(); kfo_host_set(global.kfo.set);'
          'var _why = kfo_host_start(); global.BRWHY = _why;'
          'var _q = global.kfo.lq; var _st = undefined;'
          'for (var _i = 0; _i < array_length(_q); _i++) { if (!_q[_i].up && kfo_js(_q[_i].m, "k", "") == "start") _st = _q[_i].m; }'
          'global.kfo.lq = [];'
          '_st.seed = %d; global.kfo.H.seed = %d; global.kfo.H.tl = kbr_tl_new(%d, global.kfo.H.mset);'
          'global.kfo.M = kfo_match_new(_st); global.kfo.M.launched = true;') % (me_name, skin, json.dumps(list(kn)), open_ok, bots, setx, seed, seed, seed)
    host = KN[OKREG[open_ok if open_ok in kn else kn[0]]]
    sim, e = lu_battle(host, party=(skin,), combo=3, extra_cfg=ex, world=world, pre=jv_assets)
    if e is not None:
        return None, e
    sim.rng.seed(rng_seed)
    preload_base(sim)
    sim.premocked = premock(sim)
    sim.define_event('obj_battlecontroller', 'Step', 0, stub or BR_STUB)
    sim._snapauto = False
    sim.retrylog = []
    return sim, None


def live_input(sim):
    """DRBR: the game's own input scripts (button1_h, up_h, ... - the battle harness has them all at 0) read the test's keys:
    sim.inp (held this frame) and sim.inp_p (went down this frame; the test sets it on a hold's first frame)"""
    keys = [('up', 'up'), ('down', 'down'), ('left', 'left'), ('right', 'right'), ('button1', 'ok'), ('button2', 'back'), ('button3', 'alt')]
    sim.inp = {'up': 0, 'down': 0, 'left': 0, 'right': 0, 'ok': 0, 'back': 0, 'alt': 0}
    sim.inp_p = dict(sim.inp)
    sim.inp_r = dict(sim.inp)
    for n, k in keys:
        sim.mock(n + '_h', (lambda kk: (lambda s, *a: s.inp[kk]))(k))
        sim.mock(n + '_p', (lambda kk: (lambda s, *a: s.inp_p[kk]))(k))
        # (DRBR: released this frame - the yellow SOUL's BIG SHOT fires on the confirm key's release)
        sim.mock(n + '_r', (lambda kk: (lambda s, *a: s.inp_r[kk]))(k))
    return sim


def keys_set(sim, **kw):
    """hold / let go keys for the next frame: keys_set(sim, ok=1, up=0); a key that was up and is now down is also pressed"""
    for k, v in kw.items():
        sim.inp_p[k] = 1 if (v and not sim.inp.get(k)) else 0
        if hasattr(sim, 'inp_r'):
            sim.inp_r[k] = 1 if (not v and sim.inp.get(k)) else 0
        sim.inp[k] = 1 if v else 0


BR_CHK = """var _M = global.kfo.M; var _R = _M.R; var _lu = global.knight_lu;
global.BRS = { ph: _R.ph, k: _R.k, arm: _R.arm_k, af: _R.af, now: kbr_now(), act: (is_struct(_lu) && _lu.ready) ? _lu.ks[_lu.act] : -1,
  mn: global.mnfight, tt: global.turntimer, bul: instance_number(obj_bulletparent), box: instance_number(obj_growtangle), heart: instance_number(obj_heart),
  skipped: _R.skipped, cycles: _R.cycles, go: _M.go, out: _M.out, hp: global.hp[kbr_char()], g: _M.g, det: global.kbr_det.on, cut: _R.cut_why,
  plan: (is_struct(_lu) ? _lu.plan_i : -1), ended: _M.ended };"""


def br_state(sim):
    sim.run(BR_CHK)
    return sim.py(sim.eval('global.BRS'))
