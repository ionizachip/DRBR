"""DRBR 1.0.4 - your report: "DEVILSKNIFE ATTACK IS STILL BUGGED" (on 1.0.3; on 1.0.2: "the attack where the scythes come in at
you, it's still bugged and broken").

What it was: Chapter 3 has global helper functions centerx() / centery(); Chapter 1's Devilsknives (obj_centerscythe ->
obj_jv_cscythe) keep the middle they swing round in instance variables of those names. In Chapter 3's compiled code every READ
of such a name is the FUNCTION (a reference - about 100000 as a number), only the writes reach the variable: in the real game
the four Devilsknives swung round a point about 100000 pixels away, never on the screen - Jevil turned into the Devilsknife
and nothing came (the same for the Devilsknife Swing's red blade and the DEVILSKNIFE skill). The emulator looked names up at run
time, variable first, and saw them swing round the box. Now the variables are jv_centerx / jv_centery (make_jevil.py through
fnclash.py), and the emulator reads such a name the way the game does: as an error (harness: sim.fn_shadow_check).

A practice match against Jevil at the real arena camera (x 2063) with collisions, every frame stepped:
  - Devilsknife (3) and Devilsknife Swing (11), twice each: four Devilsknives, the middle they swing round is the box's, every
    one of them on the screen every frame, swinging in through the box and out again (from the middle to 150 px out); the
    Swing's red blade on the screen beside the box;
  - the DEVILSKNIFE skill sent at you: its four Devilsknives round your box's middle, on the screen;
  - on 1.0.3's code (KH_MERGED): the read of centerx stops it with the emulator's new error - the bug reproduced.
Usage: python3 t_jevil104.py [old merged dir for the reproduction]"""
import sys, os, json, time, math, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('KH_CAM', '2063,0')
import br_harness
br_harness.COLLIDE = True
from br_harness import *

FAILS = []
N = [0]
CX, CY = br_harness.CAM
OLD = sys.argv[1] if len(sys.argv) > 1 else '/tmp/claude-0/-home-claude/86dc8034-1d0e-5f2c-a65f-e537350090b1/scratchpad/merged_rel103/'


def ok(c, msg):
    N[0] += 1
    print(('ok   ' if c else 'FAIL ') + msg, flush=True)
    if not c:
        FAILS.append(msg)
    return c


def game(force, seed=5406, skills=0):
    sim, e = br_match(open_ok=6, kn=(6,), seed=seed, bots=0, setx='_s.mhp = 999; _s.skills = %d;' % skills)
    assert not e, e
    sim.mock('camera_get_view_x', lambda s, *a: CX)
    sim.mock('camera_get_view_y', lambda s, *a: CY)
    sim.run('with (obj_battlecontroller) if (!variable_instance_exists(id, "mercytotal")) mercytotal = 0;')
    sim.run('global.BS_FORCE = %d;' % force)
    sim.load_source('gml_GlobalScript_jv104force', 'function kbr_tl_pick_attack(_tl, _k, _g, _ok, _st) { return global.BS_FORCE; }\n')
    sim.run('global.kfo.M.tl.cyc = []; global.kfo.H.tl.cyc = [];')
    sim.objects['obj_jv_cscythe'].sprite = sim.asset_index('spr_jv_joker_scythebody')
    return sim


SC = ('(function(){ var _o = []; with (obj_jv_cscythe) array_push(_o, [x, y, (variable_instance_exists(id, "jv_centerx") ? jv_centerx : -1),'
      ' (variable_instance_exists(id, "jv_centery") ? jv_centery : -1), image_alpha, (variable_instance_exists(id, "kbrx") ? kbrx : 0)]); return _o; })()')
RB = ('(function(){ var _o = []; with (obj_collidebullet) if (object_index == obj_collidebullet && sprite_index == spr_jv_joker_scythebody) array_push(_o, [x, y,'
      ' image_alpha]); return _o; })()')
BOX = 'instance_exists(obj_growtangle) ? [obj_growtangle.x, obj_growtangle.y] : []'


def run(sim, n_attacks, frames=1400, on=None):
    out = []
    cur = None
    last = ''
    for f in range(frames):
        sim.run('if (!global.kfo.M.out) global.hp[kbr_char()] = global.maxhp[kbr_char()];')
        err = step(sim, 1)
        if err:
            return out, err
        ph = sim.eval('global.kfo.M.R.ph')
        if ph == 'run' and last != 'run':
            cur = {'ai': sim.eval('obj_jv_joker.jattack'), 'fr': []}
            out.append(cur)
        if ph != 'run' and last == 'run' and len(out) >= n_attacks:
            break
        last = ph
        if cur is not None and ph == 'run':
            cur['fr'].append((sim.py(sim.eval(SC)), sim.py(sim.eval(RB)), sim.py(sim.eval(BOX))))
            if on:
                on(sim, cur)
    return out, None


def on_screen(x, y, m=0):
    return CX - m <= x <= CX + 640 + m and CY - m <= y <= CY + 480 + m


def check_knives(name, fr, sent=None):
    """the Devilsknives of the frames fr (sent: only those of a send / only Jevil's own)"""
    sc = [[s for s in f[0] if (sent is None or (s[5] > 0) == sent)] for f in fr]
    live = [(s, f[2]) for s, f in zip(sc, fr) if s]
    n4 = max((len(s) for s, b in live), default=0)
    centre = [abs(k[2] - b[0]) <= 0.5 and abs(k[3] - b[1]) <= 0.5 for s, b in live if b for k in s]
    vis = [on_screen(k[0], k[1]) for s, b in live for k in s if k[4] > 0]
    dist = [math.hypot(k[0] - k[2], k[1] - k[3]) for s, b in live for k in s if k[4] >= 1]
    ok(n4 == 4, '%s: four Devilsknives (%d)' % (name, n4))
    ok(centre and all(centre), '%s: the middle they swing round is the box\'s middle, every frame (%d of %d)' % (name, sum(centre), len(centre)))
    ok(vis and all(vis), '%s: every Devilsknife on the screen every frame it shows (%d of %d)' % (name, sum(vis), len(vis)))
    ok(dist and min(dist) <= 20 and max(dist) >= 140, '%s: they swing in through the box and out again (%.0f to %.0f px from the middle)'
       % (name, min(dist) if dist else -1, max(dist) if dist else -1))
    if live:
        k = live[len(live) // 2][0][0]
        print('     (mid-attack: one at %d, %d; the camera at %d, %d)' % (k[0], k[1], CX, CY))


t0 = time.time()
for ai, name in ((3, 'Devilsknife'), (11, 'Devilsknife Swing')):
    sim = game(ai)
    res, err = run(sim, 2)
    ok(not err and len(res) >= 2, '%s: two of it ran, no error (%s)' % (name, err))
    for k, a in enumerate(res[:2]):
        nm = '%s (%s time)' % (name, 'first' if k == 0 else 'second')
        check_knives(nm, a['fr'])
        if ai == 11:
            bl = [b for f in a['fr'] for b in f[1] if b[2] > 0]
            ok(len(bl) > 20 and all(on_screen(b[0], b[1], 120) for b in bl), '%s: the red blade comes, on the screen beside the box (%d frames)' % (nm, len(bl)))
# the DEVILSKNIFE skill sent at you during his Ring-Around
sim = game(1, seed=5407, skills=1)
landed = {}


def send_once(sim, cur):
    if 'sent' not in landed and len(cur['fr']) == 30:
        landed['sent'] = sim.frame_no
        sim.run('var _M = global.kfo.M; array_push(_M.sk.pend, { sid: 30, from: 2, fn: "LANCER", sd: 777, t: 0, rf: 0, sh: 0 });')


res, err = run(sim, 1, on=send_once)
ok(not err and 'sent' in landed, 'DEVILSKNIFE skill: sent at you during his attack, no error (%s)' % err)
if res:
    check_knives('DEVILSKNIFE skill', res[0]['fr'], sent=True)
# 1.0.3's code: the read of centerx stops it (the emulator now reads the name the way the game does)
if os.path.isdir(OLD):
    code = ('import sys, os\nsys.path.insert(0, %r)\nos.environ["KH_CAM"] = "2063,0"\nimport br_harness\nbr_harness.COLLIDE = True\n'
            'from br_harness import *\nsim, e = br_match(open_ok=6, kn=(6,), seed=5406, bots=0, setx="_s.mhp = 999; _s.skills = 0;")\n'
            'sim.run("with (obj_battlecontroller) if (!variable_instance_exists(id, \\"mercytotal\\")) mercytotal = 0;")\n'
            'sim.load_source("gml_GlobalScript_f", "function kbr_tl_pick_attack(_tl, _k, _g, _ok, _st) { return 3; }\\n")\n'
            'sim.run("global.kfo.M.tl.cyc = []; global.kfo.H.tl.cyc = [];")\n'
            'for f in range(700):\n    err = step(sim, 1)\n    if err:\n        print("ERR", err[:300]); break\n') % os.path.dirname(os.path.abspath(__file__))
    r = subprocess.run([sys.executable, '-c', code], env=dict(os.environ, KH_MERGED=OLD), capture_output=True, text=True, timeout=1200)
    msg = [l for l in r.stdout.splitlines() if l.startswith('ERR')]
    ok(msg and 'centerx is also a global function' in msg[0], '1.0.3\'s code: the Devilsknife\'s read of centerx is the function in the game - reproduced (%s)'
       % (msg[0][:160] if msg else 'no error'))
else:
    print('     (1.0.3\'s code not found at %s: the reproduction NOT RUN)' % OLD)
print('jevil104: %d checks, %d failed (%.0fs)' % (N[0], len(FAILS), time.time() - t0))
for f in FAILS:
    print('  -', f)
sys.exit(1 if FAILS else 0)
