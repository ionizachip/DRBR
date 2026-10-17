"""DRBR: sprite animation and the bosses' sprites for the emulator.

The emulator keeps image_index where code puts it, knows no sprite's frame count (sprite_get_number answers 0, image_number
stays 1) or name (sprite_get_name answers ""), and gives an object no default sprite unless a test sets one. The ported bosses
lean on all of these (Gerson's green-SOUL switch waits for its own animation to pass frame 4; the chevron it then makes draws
the shield into being), so with the collision pump on (collide.py) this adds, as the runner does:
  - after each frame every live instance with a sprite moves image_index on by image_speed (the sprites in these chapters'
    data play one frame per game frame at image_speed 1) and, going past the last frame (or before the first when it plays
    backwards), comes round and runs its Animation End event (Other 7); image_number follows the sprite;
  - sprite_get_number / sprite_get_name answer from the built data.win's tables;
  - each imported boss object gets its sprite as the build gives it (its source object's sprite, renamed when imported);
  - bbox_model learns the bosses' sprites' collision boxes and the objects' sprites / masks (the build 51 table predates them).
Tables: src/built/assets.tsv (the merged build 51 data.win: Chapter 3 + the hub + Jevil) and, for sprites build/assets.json
imports from another chapter, that chapter's own data.win dump (src/c2, src/c4, src/c5, jevil/c1dump)."""
import json, os

W = '/home/claude/work/'
FRAMES = {}       # sprite name -> frame count
SPRROW = {}       # sprite name -> (w, h, ox, oy, ml, mr, mt, mb) for bbox_model
OBJDEF = {}       # boss object (new name) -> (parent, sprite, mask) with new names
_SRC = {'c1': W + 'jevil/c1dump/assets.tsv', 'c2': W + 'src/c2/assets.tsv', 'c4': W + 'src/c4/assets.tsv', 'c5': W + 'src/c5/assets.tsv'}
_TAB = {}
STATS = {'ends': 0, 'frames': 0}


def _tab(key):
    if key in _TAB:
        return _TAB[key]
    t = {'spr': {}, 'obj': {}}
    p = _SRC.get(key) if key != 'built' else W + 'src/built/assets.tsv'
    if p and os.path.exists(p):
        for l in open(p, encoding='utf8'):
            r = l.rstrip('\n').split('\t')
            if r[0] == 'spr' and len(r) >= 11:
                try:
                    v = [int(x) for x in r[2:11]]
                except ValueError:
                    continue
                t['spr'][r[1]] = v                      # w, h, ox, oy, frames, ml, mr, mt, mb
            elif r[0] == 'obj' and len(r) >= 5:
                t['obj'][r[1]] = (r[2], r[3], r[4])     # parent, sprite, mask
    _TAB[key] = t
    return t


def load():
    if FRAMES:
        return
    b = _tab('built')
    for n, v in b['spr'].items():
        FRAMES[n] = max(1, v[4])
    A = json.load(open(W + 'build/assets.json'))
    ren = A['rename']
    for m in A['manifest']['sprites']:
        t = _tab(m['src']) if m['src'] in _SRC else None
        if t is None:
            continue
        v = t['spr'].get(m['name'])
        if v is None:
            continue
        if m['new'] not in FRAMES:
            FRAMES[m['new']] = max(1, v[4])
        if m['new'] not in b['spr']:
            SPRROW[m['new']] = (v[0], v[1], v[2], v[3], v[5], v[6], v[7], v[8])
    for m in A['manifest']['objects']:
        if 'boss' not in m or m['src'] not in _SRC:
            continue
        r = _ren = ren.get(m['src'], {})
        par, spr, msk = _tab(m['src'])['obj'].get(m['name'], ('', '', ''))
        # a sprite / mask / parent the build does not import keeps its own name (Chapter 3 has it: the build checked)
        OBJDEF[m['new']] = (_ren.get(par, par) if par else '', _ren.get(spr, spr) if spr else '', _ren.get(msk, msk) if msk else '')


def _rev(sim):
    rv = getattr(sim, '_anim_rev', None)
    if rv is None or len(rv) != len(sim.assets):
        sim._anim_rev = rv = {v: k for k, v in sim.assets.items()}
    return rv


def install(sim):
    """once per emulator: the mocks, the boss objects' sprites, bbox_model's extra rows"""
    if getattr(sim, '_anim_on', False):
        return
    sim._anim_on = True
    load()

    def _num(s, i, *a):
        try:
            return FRAMES.get(_rev(s).get(int(i)), 1)
        except Exception:
            return 1

    def _name(s, i, *a):
        try:
            return _rev(s).get(int(i), '') or ''
        except Exception:
            return ''
    sim.mock('sprite_get_number', _num)
    sim.mock('sprite_get_name', _name)
    for o, (par, spr, msk) in OBJDEF.items():
        od = sim.objects.get(o)
        if od is None:
            continue
        if spr and getattr(od, 'sprite', -1) in (-1, None):
            try:
                od.sprite = sim.define_asset(spr)
            except Exception:
                pass
    import geom
    geom.install(sim)
    try:
        import bbox_model as BM
        for n, row in SPRROW.items():
            BM.SPR.setdefault(n, row)
        for o, d in OBJDEF.items():
            BM.OBJ.setdefault(o, d)
    except Exception:
        pass


def _bbox(sim, inst, d):
    import bbox_model as BM
    b = BM.box_of(sim, inst)
    if b is None:
        return
    d['bbox_left'], d['bbox_top'], d['bbox_right'], d['bbox_bottom'] = b[0], b[1], b[2], b[3]
    nm = BM._sprite_name(sim, inst)
    if nm in BM.SPR:
        try:
            d['sprite_width'] = BM.SPR[nm][0] * float(d.get('image_xscale', 1))
            d['sprite_height'] = BM.SPR[nm][1] * float(d.get('image_yscale', 1))
        except Exception:
            pass


def tick(sim):
    """one frame of animation for every live instance"""
    install(sim)
    STATS['frames'] += 1
    rv = _rev(sim)
    for inst in list(sim.instances.values()):
        if inst.dead:
            continue
        d = inst.vars
        # the runner's read-only box and size (the emulator keeps plain variables: Chapter 5's bamboo tests its own bbox)
        _bbox(sim, inst, d)
        si = d.get('sprite_index', -1)
        try:
            si = int(si)
        except Exception:
            continue
        if si < 0:
            continue
        n = FRAMES.get(rv.get(si), 1)
        d['image_number'] = n
        sp = d.get('image_speed', 1)
        try:
            sp = float(sp)
        except Exception:
            continue
        if sp == 0:
            continue
        try:
            ii = float(d.get('image_index', 0)) + sp
        except Exception:
            continue
        ended = False
        if ii >= n:
            ii -= n
            ended = True
        elif ii < 0:
            ii += n
            ended = True
        d['image_index'] = ii
        if ended:
            STATS['ends'] += 1
            if sim.find_event(inst.obj, ('Other', 7)) is not None:
                sim.run_event(inst, 'Other', 7)
