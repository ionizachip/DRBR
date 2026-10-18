"""DRBR 1.0.2 - your report: "ERROR in action number 1 of Draw Event for object obj_fl_soul: Variable
<unknown_object>.fakecamxspeedadditional not set before reading it". The orange SOUL drew with its board's controller gone
(obj_fl_ctrl: the SOUL's Draw takes `controller = -1` when there is none and reads it). A practice match against Flowery, his
attacks forced, every frame stepped and drawn, the battle camera away from the room's corner:
  - one half of his board goes in the middle of an attack, after the SOUL's Step and before its Draw (an End Step takes it):
    the controller (destroyed, or switched off and later back on), the orange SOUL, or the battle box. No error (1.0.1: this
    is the crash), and the board ends in that game as the cut ends it: none of its pieces left, the red SOUL visible and
    moving again, Flowery back on stage; the attack runs to its own end and the next one builds a whole board again;
  - his attacks with nothing taken away never end their board early (the check is quiet when the board is whole).
Usage: python3 t_flboard102.py [kind:attack ...]   (kind: ctrl, ctrloff, soul, box)"""
import sys, os, json, time
os.environ.setdefault('KH_CAM', '1000,320')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from br_harness import *

FAILS = []
N = [0]
CASES = [('ctrl', 0), ('ctrl', 1), ('ctrl', 2), ('ctrl', 4), ('ctrl', 5), ('ctrl', 10), ('ctrloff', 0), ('soul', 0), ('soul', 2),
         ('box', 0), ('box', 2)]
NORMAL = [0, 1, 2, 4, 5, 10, 12]
PIECES = ['obj_fl_soul', 'obj_fl_ctrl', 'obj_fl_wall', 'obj_fl_bullet', 'obj_fl_thorns', 'obj_fl_pad', 'obj_fl_box', 'obj_fl_book', 'obj_fl_bloom',
          'obj_fl_beam', 'obj_fl_jarona', 'obj_fl_wordflower']
ST = ('(function(){ var _o = {}; var _l = [%s]; for (var _i = 0; _i < array_length(_l); _i++) variable_struct_set(_o, object_get_name(_l[_i]), instance_number(_l[_i]));'
      ' var _h = instance_find(obj_heart, 0);'
      ' return { n: _o, ph: global.kfo.M.R.ph, k: global.kfo.M.R.k, heart: instance_exists(_h) ? [_h.visible, variable_instance_exists(_h, "canmove") ? _h.canmove : -1] : [],'
      ' fl: instance_exists(obj_fl_flowery) ? obj_fl_flowery.visible : -1, broke: variable_global_exists("kbr_fl_broke") ? global.kbr_fl_broke : 0,'
      ' box: instance_number(obj_growtangle), mode: kbr_soul_mode() }; })()') % ', '.join(PIECES)
# the End Step that takes one half away (made after the board: an End Step runs after every Step and before every Draw)
BREAK = {
    'ctrl': 'with (obj_fl_ctrl) instance_destroy();',
    'ctrloff': 'global.T_OFF = instance_find(obj_fl_ctrl, 0); instance_deactivate_object(global.T_OFF);',
    'soul': 'with (obj_fl_soul) instance_destroy();',
    'box': 'with (obj_growtangle) instance_destroy();',
}


def ok(c, msg):
    N[0] += 1
    print(('ok   ' if c else 'FAIL ') + msg, flush=True)
    if not c:
        FAILS.append(msg)
    return c


def J(s, e):
    return s.py(s.eval(e))


def game(atk, seed):
    sim, e = br_match(open_ok=8, kn=(8,), seed=seed, bots=0, setx='_s.mhp = 999; _s.skills = 0;')
    assert not e, e
    sim.run('with (obj_battlecontroller) if (!variable_instance_exists(id, "mercytotal")) mercytotal = 0;')
    sim.run('global.BS_FORCE = %d; global.T_BRK = ""; global.T_OFF = noone;' % atk)
    sim.load_source('gml_GlobalScript_flb102force', 'function kbr_tl_pick_attack(_tl, _k, _g, _ok, _st) { return global.BS_FORCE; }\n')
    sim.run('global.kfo.M.tl.cyc = []; global.kfo.H.tl.cyc = [];')
    sim.define_event('obj_t_flbreak', 'Step', 2, 'if (global.T_BRK != "") { var _b = global.T_BRK; global.T_BRK = ""; switch (_b) {%s} }'
                     % ''.join(' case "%s": %s break;' % (k, v) for k, v in BREAK.items()))
    sim.run('instance_create(0, 0, obj_t_flbreak);')
    return sim


def frame(sim):
    sim.run('if (!global.kfo.M.out) global.hp[kbr_char()] = global.maxhp[kbr_char()];')
    return step(sim, 1)


def to_board(sim, need=60, limit=2600):
    """into the next attack's running board, `need` frames in: (error, frames)"""
    t = 0
    for f in range(limit):
        err = frame(sim)
        if err:
            return err, f
        s = J(sim, ST)
        if s['ph'] == 'run' and s['n']['obj_fl_soul'] > 0 and s['n']['obj_fl_ctrl'] > 0:
            t += 1
            if t >= need:
                return None, f
        else:
            t = 0
    return 'no board within %d frames' % limit, limit


def broken_case(kind, atk):
    print('== %s gone in attack %d' % (kind, atk), flush=True)
    sim = game(atk, 5600 + atk)
    err, _ = to_board(sim)
    if not ok(err is None, '%s %d: the board is up (%s)' % (kind, atk, err)):
        return
    k0 = J(sim, ST)['k']
    sim.run('global.T_BRK = "%s";' % kind)
    err = frame(sim)
    ok(err is None, '%s %d: no error in the frame it went - its Draw included (%s)' % (kind, atk, (err or '')[:300]))
    if err:
        return
    s = J(sim, ST)
    left = {k: v for k, v in s['n'].items() if v}
    ok(not left, '%s %d: the board ended in this game - none of its pieces left (%r)' % (kind, atk, left))
    if kind != 'box':
        ok(s['heart'] == [True, 1] and s['fl'] == True and s['mode'] == 'red', '%s %d: the red SOUL is back (visible, moving), Flowery on stage (heart %r, Flowery %r, SOUL %s)'
           % (kind, atk, s['heart'], s['fl'], s['mode']))
    ok(s['broke'] >= 1, '%s %d: it was the half-a-board check that ended it (%d)' % (kind, atk, s['broke']))
    # the attack runs to its own end; a switched-off controller that comes back goes too
    errs = None
    back = False
    for f in range(900):
        if kind == 'ctrloff' and f == 20:
            sim.run('instance_activate_object(global.T_OFF);')
            back = True
        err = frame(sim)
        if err:
            errs = err
            break
        s = J(sim, ST)
        if kind == 'ctrloff' and back and f == 22:
            ok(s['n']['obj_fl_ctrl'] == 0 and s['n']['obj_fl_soul'] == 0, 'ctrloff %d: the controller switched back on with no SOUL left goes (%r)' % (atk, s['n']))
        if s['k'] > k0:
            break
    ok(errs is None and s['k'] > k0, '%s %d: the attack ran to its end without an error (cycle %d -> %d, %s)' % (kind, atk, k0, s['k'], (errs or '')[:200]))
    err, _ = to_board(sim)
    s = J(sim, ST)
    ok(err is None and s['n']['obj_fl_soul'] == 1 and s['n']['obj_fl_ctrl'] == 1, '%s %d: the next attack builds a whole board again (%s, %r)' % (kind, atk, err, s['n']))


def normal_case(atk):
    sim = game(atk, 5700 + atk)
    err, _ = to_board(sim, need=1)
    k0 = J(sim, ST)['k']
    errs = err
    for f in range(1400):
        if errs:
            break
        errs = frame(sim)
        if J(sim, 'global.kfo.M.R.k') > k0:
            break
    s = J(sim, ST)
    ok(errs is None and s['k'] > k0 and s['broke'] == 0, 'attack %d with nothing taken away: run to its cut, its board never ended early (%d, %s)' % (atk, s['broke'], (errs or '')[:200]))


t0 = time.time()
want = [(a.split(':')[0], int(a.split(':')[1])) for a in sys.argv[1:]]
for kind, atk in (want or CASES):
    try:
        broken_case(kind, atk)
    except Exception as ex:
        ok(False, '%s %d: crashed: %s' % (kind, atk, str(ex)[:300]))
if not want:
    for atk in NORMAL:
        try:
            normal_case(atk)
        except Exception as ex:
            ok(False, 'attack %d: crashed: %s' % (atk, str(ex)[:300]))
print('flboard102: %d checks, %d failed (%.0fs)' % (N[0], len(FAILS), time.time() - t0))
for f in FAILS:
    print('  -', f)
sys.exit(1 if FAILS else 0)
