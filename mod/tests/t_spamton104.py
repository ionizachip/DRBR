"""DRBR 1.0.4 - found by running every boss's attacks in the real game program (tests/realrunner): Spamton NEO's NEO Finale
stopped the real game - "ERROR in action number 1 of Draw Event for object obj_sn_playback: draw_sprite argument 1 incorrect
type (undefined) expecting a Number" - in his NEO Finale (his final forme's playback bar). Chapter 2's code looks its playback bar's picture up by name, scr_84_get_sprite
("spr_sneo_playback"); Chapter 3's scr_84_get_sprite only knows Chapter 3's own localized pictures (global.chemg_sprite_map),
so it gave undefined, and the real runner refuses to draw that. The emulator drew anything (its draw functions only record),
so no test saw it. Now the imports use the picture itself (make_boss.py: scr_84_get_sprite("spr_x") -> spr_x, and no lookup
may be left), and the emulator's sprite draws check their arguments as the runner does (sim.strict_draw, on in the harness).
A practice match against Spamton NEO, his attacks forced, every frame stepped AND drawn the game's way (Draw / Draw End by
depth, draw_self, an instance with no Draw event drawing its sprite) with the runner's argument check:
  - Heart Attack III (12), Pipis Call III (13) and the NEO Finale (14): no error, the playback bar and his final forme hold a
    real picture (spr_sneo_playback);
  - on 1.0.3's code (KH_MERGED): the NEO Finale stops on the playback bar's draw - the real game's error, reproduced.
Usage: python3 t_spamton104.py [old merged dir]"""
import sys, os, time, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('KH_CAM', '2063,0')
import br_harness
br_harness.COLLIDE = True
from br_harness import *
from uiharness import Recorder

FAILS = []
N = [0]
CX, CY = br_harness.CAM
OLD = sys.argv[1] if len(sys.argv) > 1 else '/tmp/claude-0/-home-claude/86dc8034-1d0e-5f2c-a65f-e537350090b1/scratchpad/merged_rel103/'
SN = 9
OBJSPR = {}
for l in open('/home/claude/work/src/built103/assets.tsv'):
    r = l.rstrip('\n').split('\t')
    if r[0] == 'obj' and r[3]:
        OBJSPR[r[1]] = r[3]


def ok(c, msg):
    N[0] += 1
    print(('ok   ' if c else 'FAIL ') + msg, flush=True)
    if not c:
        FAILS.append(msg)
    return c


def setup(seq):
    sim, e = br_match(open_ok=SN, kn=(SN,), seed=5406, bots=0, setx='_s.mhp = 999; _s.skills = 0;')
    assert not e, e
    for o, od in sim.objects.items():
        if o in OBJSPR and getattr(od, 'sprite', None) in (None, -1):
            try:
                od.sprite = sim.asset_index(OBJSPR[o])
            except Exception:
                pass
    sim.mock('camera_get_view_x', lambda s, *a: CX)
    sim.mock('camera_get_view_y', lambda s, *a: CY)
    sim.run('with (obj_battlecontroller) if (!variable_instance_exists(id, "mercytotal")) mercytotal = 0;')
    sim.run('global.KSEQ = [%s];' % ','.join(str(x) for x in seq))
    sim.load_source('gml_GlobalScript_sn104force', 'function kbr_tl_pick_attack(_tl, _k, _g, _ok, _st) { return global.KSEQ[_k mod array_length(global.KSEQ)]; }\n')
    sim.run('global.kfo.M.tl.cyc = []; global.kfo.H.tl.cyc = [];')
    rec = Recorder(sim)
    try:
        sim.define_asset('hpfont')
    except Exception:
        pass
    sim.run('if (!variable_global_exists("hpfont")) global.hpfont = hpfont;')

    def dself(s, f):
        v = f.self.vars
        sp = v.get('sprite_index', -1)
        if isinstance(sp, (int, float)) and sp >= 0:
            rec.ops.append(('spr', rec.name_of(sp), v.get('image_index', 0), v.get('x', 0), v.get('y', 0), v.get('image_xscale', 1), v.get('image_yscale', 1),
                            v.get('image_angle', 0), rec.fogc(v.get('image_blend', 16777215)), v.get('image_alpha', 1), None, None))
        return 0
    sim.mock('draw_self', dself, frame=True)
    return sim, rec


def draw_all(sim, rec):
    """one frame drawn the game's way; the first error (as the runner would stop on it)"""
    rec.ops.clear()
    insts = sorted([i for i in sim.instances.values() if not i.dead], key=lambda i: -i.vars.get('depth', 0))
    for num in (72, 0, 73):
        for inst in insts:
            if inst.dead or inst.id not in sim.instances or not inst.vars.get('visible', True):
                continue
            found = sim.find_event(inst.obj, ('Draw', num))
            if found is not None:
                try:
                    sim._run_entry(inst, found[0], ('Draw', num), found[1], None)
                except Exception as ex:
                    return '%s Draw %d: %s' % (inst.obj, num, str(ex)[:220])
    return None


def run(seq, frames):
    sim, rec = setup(seq)
    last = ''
    out = []
    cur = None
    for f in range(frames):
        sim.run('if (!global.kfo.M.out) global.hp[kbr_char()] = global.maxhp[kbr_char()];')
        err = step(sim, 1)
        if err:
            return out, 'step: ' + err[:300], sim
        ph = sim.eval('global.kfo.M.R.ph')
        if ph == 'run' and last != 'run':
            cur = {'ai': seq[len(out) % len(seq)], 'frames': 0, 'pb': set()}
            out.append(cur)
        if ph != 'run' and last == 'run' and len(out) >= len(seq):
            break
        last = ph
        if ph == 'run':
            cur['frames'] += 1
            e = draw_all(sim, rec)
            if e:
                return out, e, sim
            for v in sim.py(sim.eval('(function(){ var _o = []; with (obj_sn_playback) array_push(_o, playback_sprite); with (obj_sn_forme) array_push(_o, playback_sprite); return _o; })()')):
                cur['pb'].add(v)
    return out, None, sim


t0 = time.time()
if '--old-only' in sys.argv:
    # (the reproduction's own process: the code under KH_MERGED is 1.0.3's)
    res, err, sim = run([14], 1800)
    print('OLD playbacks %d | %s' % (sim.eval('instance_number(obj_sn_playback)'), err))
    sys.exit(0)
res, err, sim = run([12, 13, 14], 3600)
ok(err is None, 'Heart Attack III, Pipis Call III, the NEO Finale: every frame drawn with the runner\'s argument check, no error (%s)' % err)
names = {12: 'Heart Attack III', 13: 'Pipis Call III', 14: 'the NEO Finale'}
spr = sim.asset_index('spr_sneo_playback')
for a in res:
    ok(a['frames'] > 30, '%s ran (%d frames)' % (names.get(a['ai'], a['ai']), a['frames']))
pb = set().union(*[a['pb'] for a in res]) if res else set()
ok(pb and pb <= {spr}, 'the playback bar and his final forme hold the picture itself, spr_sneo_playback (%r, the sprite %d)' % (sorted(pb, key=str), spr))
# 1.0.3's code: the NEO Finale stops on the playback bar's draw
if os.path.isdir(OLD):
    r = subprocess.run([sys.executable, os.path.abspath(__file__), '--old-only'], env=dict(os.environ, KH_MERGED=OLD), capture_output=True, text=True,
                       timeout=3000, cwd=os.path.dirname(os.path.abspath(__file__)))
    line = [l for l in r.stdout.splitlines() if l.startswith('OLD ')]
    ok(line and 'playbacks 0 ' not in line[0] and 'draw_sprite argument 1 incorrect type (undefined)' in line[0],
       '1.0.3\'s code: the NEO Finale stops on the playback bar\'s draw - the real game\'s error, reproduced (%s)' % (line[0][:200] if line else r.stdout[-300:]))
else:
    print('     (1.0.3\'s code not found at %s: the reproduction NOT RUN)' % OLD)
print('spamton104: %d checks, %d failed (%.0fs)' % (N[0], len(FAILS), time.time() - t0))
for f in FAILS:
    print('  -', f)
sys.exit(1 if FAILS else 0)
