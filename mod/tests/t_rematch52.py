"""Build 52: the next match takes everyone who played the last one (emulated, three games over the simulated network).
  - READY stays on after a match (it was cleared for everyone, so a START left them out: they watched);
  - the host STARTs while the others still show the results (their game still in the last fight): they close the results,
    go back to the room and join the new match as players (they used to stay out and watch), the host's GO following.
Usage: python3 t_rematch52.py"""
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from br_multi import *

FAILS = []
N = [0]


def ok(c, msg):
    N[0] += 1
    print(('ok   ' if c else 'FAIL ') + msg, flush=True)
    if not c:
        FAILS.append(msg)


def J(s, e):
    return s.py(s.eval(e))


t0 = time.time()
net, sims = make_room(3, 'lan', 5253, setx='_s.mhp = 250;')
H, C2, C3 = sims
run(net, sims, 200, 'none', wall=600)
ok(J(H, 'global.kfo.M.go'), 'the first match runs')
mid1 = J(H, 'global.kfo.H.mid')
H.run('kfo_host_end();')
run(net, sims, 40, 'none', wall=300)
ok(all(J(s, 'global.kfo.M.ended') for s in sims), 'the match ended in every game')
ok(all(J(s, 'knight_active()') for s in (C2, C3)), "players 2 and 3 still show the results (their game is in the last fight)")
rd = J(H, '(function(){ var _o = []; for (var _i = 0; _i < array_length(global.kfo.H.pl); _i++) if (global.kfo.H.pl[_i].pid != global.kfo.my) array_push(_o, global.kfo.H.pl[_i].rd); return _o; })()')
ok(rd == [1, 1], 'READY stays on for the players after the match %r' % rd)
why = J(H, 'kfo_host_start()')
ok(why == '', 'the host starts the next match at once (%r)' % why)
mid2 = J(H, 'global.kfo.H.mid')
pl = J(H, '(function(){ var _o = []; for (var _i = 0; _i < array_length(global.kfo.H.pl); _i++) array_push(_o, global.kfo.H.pl[_i].inm); return _o; })()')
ok(pl == [1, 1, 1], 'all three are in the new match on the host %r' % pl)
seen = {2: [], 3: []}
def keep(f, ss, prev):
    for i, s in ((2, C2), (3, C3)):
        seen[i].append(J(s, '[is_struct(global.kfo.M) ? global.kfo.M.mid : -1, is_struct(global.kfo.M) ? global.kfo.M.me : -1, variable_struct_exists(global.kfo, "start_wait") && is_struct(global.kfo.start_wait), knight_active()]'))
run(net, sims, 3, 'none', wall=300)
# (the emulator cannot load a new fight after leaving one, so the host's GO - sent once every fight is up - is handed to
# player 2 here, as it would arrive while its results close)
ok(J(C2, 'is_struct(global.kfo.start_wait)'), 'player 2 is waiting to join (its results closing)')
TG = J(C2, 'current_time')
C2.run('kfo_on_go({ k: "go", mid: %d, h: -1500 });' % mid2)
ok(J(C2, 'is_struct(global.kfo.start_wait.go)'), "the GO that came meanwhile is kept for the new match")
rec = run(net, sims, 117, 'none', on_frame=keep, wall=600)
errs = {c: rec[c]['errors'][:1] for c in range(1, 4) if rec[c]['errors']}
ok(not errs, 'no errors %r' % errs)
for i in (2, 3):
    w = [x for x in seen[i] if x[2]]
    ok(len(w) > 0, 'player %d: the START waited while its results closed (%d frames)' % (i, len(w)))
    last = seen[i][-1]
    ok(last[0] == mid2 and last[1] is True, 'player %d is a PLAYER of the new match %d (not watching) %r' % (i, mid2, last))
    ok(J(sims[i - 1], 'global.kfo.M.launched'), 'player %d: its fight was launched' % i)
t0g = J(C2, 'global.kfo.M.t0ms')
ok(J(C2, 'global.kfo.M.go') and J(C2, 'global.kfo.M.mid') == mid2, "player 2: the kept GO was used once its match started")
ok(abs(t0g - (TG + 1500)) <= 2, "player 2: tick 0 where the GO put it when it came, not later (%r vs %r)" % (t0g, TG + 1500))
print('rematch52: %d checks, %d failed (%.0fs)' % (N[0], len(FAILS), time.time() - t0))
for f in FAILS:
    print('  -', f)
sys.exit(1 if FAILS else 0)
