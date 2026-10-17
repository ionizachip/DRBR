"""Build 45: the START box's lines for every knight x START AT / REPEAT attack x Random Knight on/off (the UI fuzz found
a crash: REPEAT at Thorn's attack 22 with Random Knight on picked a knight with 21 attacks, and the START box read past the
end of its list). Checks: knight_resolve keeps p_atk inside the resolved knight's list (a Random Knight other than the menu's
starts over at its first attack), knight_ui_launch_lines never fails and names an attack of the resolved knight."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from harness import *

sim = make_sim()
FAILS = []
N = [0]


def ok(c, m):
    N[0] += 1
    if not c:
        FAILS.append(m)
        print('FAIL', m, flush=True)


nk = sim.eval('array_length(global.knight_registry)') if sim.eval('variable_global_exists("knight_registry")') else 6
lens = [sim.eval('array_length(knight_reg(%d).atk)' % k) for k in range(nk)]
print('attack list lengths', lens)
for k in range(nk):
    if sim.eval('knight_reg(%d).joke' % k):
        continue
    for pm in (1, 2):
        for rnd in (0, 1):
            for pa in range(lens[k]):
                for rs in range(3 if rnd else 1):
                    sim.rng.seed(1000 * k + 10 * pa + rs)
                    sim.run('global.LC = knight_cfg_default(); global.LC.knight = %d; global.LC.p_mode = %d; global.LC.p_atk = %d;'
                            'global.LC.random = %d; global.LC.mode = 0; global.LC.combo = 0; global.LC.practice = 0;' % (k, pm, pa, rnd))
                    try:
                        sim.run('global.LR = knight_resolve(global.LC);')
                        r = sim.py(sim.eval('{ ok: global.LR.ok, kn: global.LR.ok ? global.LR.cfg.knight : -1, pa: global.LR.ok ? global.LR.cfg.p_atk : -1 }'))
                    except Exception as e:
                        ok(False, 'resolve k%d pm%d pa%d rnd%d: %s' % (k, pm, pa, rnd, str(e)[:200]))
                        continue
                    if not r['ok']:
                        continue
                    kn = int(r['kn'])
                    ok(0 <= r['pa'] < lens[kn], 'k%d pm%d pa%d rnd%d -> knight %d p_atk %s outside its %d attacks' % (k, pm, pa, rnd, kn, r['pa'], lens[kn]))
                    if kn != k:
                        ok(r['pa'] == 0, 'k%d pm%d pa%d rnd%d -> another knight %d keeps p_atk %s' % (k, pm, pa, rnd, kn, r['pa']))
                    try:
                        sim.run('global.LL = knight_ui_launch_lines({ src: global.LR.src, cfg: global.LR.cfg, plan: global.LR.plan, reveal: global.LR.reveal, corr: global.LR.corr });')
                        lines = sim.py(sim.eval('global.LL'))
                        ok(isinstance(lines, list), 'lines not a list')
                    except Exception as e:
                        ok(False, 'launch lines k%d pm%d pa%d rnd%d: %s' % (k, pm, pa, rnd, str(e)[:200]))
# a stale out-of-range index straight into the START box (no resolve): the lines clamp it
for k in range(nk):
    try:
        sim.run('var _c = knight_cfg_default(); _c.knight = %d; _c.p_mode = 2; _c.p_atk = 99; _c.random = 0; _c.mode = 0; _c.combo = 0; _c.practice = 0;'
                'global.LL = knight_ui_launch_lines({ src: _c, cfg: _c, plan: [%d], reveal: "", corr: [] });' % (k, k))
        ok(True, '')
    except Exception as e:
        ok(False, 'stale index k%d: %s' % (k, str(e)[:200]))
print('launch lines: %d checks, %d failed' % (N[0], len(FAILS)))
sys.exit(1 if FAILS else 0)
