"""Build 50: SONG: RANDOM in KNIGHT RUSH draws a new song for every fight (never the same twice in a row when there is a
choice); a single fight keeps its song."""
import sys
sys.path.insert(0, '/home/claude/work/uiref')
from harness import *
from uiharness import menu_sim
FAILS = []; N = [0]
def ok(c, msg):
    N[0] += 1
    if not c: FAILS.append(msg); print('FAIL', msg)
sim, rec = menu_sim()
sim.mock('knight_music_exists', lambda s, *a: 1)
sim.run('knight_store_load(); var _c = knight_cfg_default(); _c.song = knight_song_find("@random"); _c.mode = 1;'
        'global.krun = { mode: 1, pos: 0, cfg: _c };')
ok(sim.eval('global.knight_songs[global.krun.cfg.song].file') == '@random', 'SONG: RANDOM is picked')
seq = []
for pos in range(6):
    sim.run('global.krun.pos = %d;' % pos)
    a = sim.eval('knight_song_eff()'); b = sim.eval('knight_song_eff()')
    ok(a == b, 'fight %d keeps its song while it lasts' % pos)
    seq.append(a)
ok(all(seq[i] != seq[i + 1] for i in range(len(seq) - 1)), 'RUSH: a new song every fight, never the same twice in a row %r' % seq)
ok(all(sim.eval('global.knight_songs[%d].file' % i) not in ('', '@random') for i in seq), 'only real songs are drawn')
sim.run('global.krun = { mode: 0, pos: 0, cfg: global.krun.cfg }; global.S1 = knight_song_eff(); global.krun.pos = 3; global.S2 = knight_song_eff();')
ok(sim.eval('global.S1') == sim.eval('global.S2'), 'a single fight keeps the song it drew')
print('rushsong50 tests', N[0], 'fails', len(FAILS)); sys.exit(1 if FAILS else 0)
