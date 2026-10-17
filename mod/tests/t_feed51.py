"""Build 51: the combat feed and MAX (FULL HEAL) in three emulated games over the simulated network (br_multi: the real
merged fight code, the real host, relay and players).
FEED: one send = exactly one line in every game (build 50 wrote it twice: the sender's own "You used X!" / the target's
"X -> you" plus the host's "X used Y on Z!"); the same standings arriving twice add nothing; the same line again within a
second is one line with x2; at most 3 lines drawn; the short wording.
MAX: every player and bot starts with exactly one MAX; a second MAX is refused by the host (the _p.fh count) - after a
resync too, and a rematch gives one again; MAX fills to the room's real max HP even at 50% HEAL POWER; MAX is green, so
it is never sent.
Usage: python3 t_feed51.py"""
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


def keep(f, sims, prev):
    if f % 15 == 0:
        for s in sims:
            s.run('if (is_struct(global.kfo.M) && !global.kfo.M.out && !variable_global_exists("NOHEAL")) global.hp[kbr_char()] = global.maxhp[kbr_char()];')
            s.log.clear()


def go(net, sims, n):
    rec = run(net, sims, n, 'none', on_frame=keep, wall=900)
    errs = {c: rec[c]['errors'][:1] for c in range(1, len(sims) + 1) if rec[c]['errors']}
    if errs:
        ok(False, 'no errors in the games: %r' % errs)
        raise SystemExit(1)


def J(s, e):
    return s.py(s.eval(e))


def logs(s):
    return [x['base'] if isinstance(x, dict) and 'base' in x else x['t'] for x in J(s, 'global.kfo.M.log')]


t0 = time.time()
net, sims = make_room(3, 'lan', 5151, setx='_s.mhp = 250; _s.cdm = 25; _s.g0 = 50; _s.hmul = 50;', bots=1)
H, C2, C3 = sims
go(net, sims, 330)
ok(J(H, 'global.kfo.M.go'), 'the match runs')

# ---- MAX at the start: everyone, bots too
for i, s in enumerate(sims):
    sl = J(s, 'global.kfo.M.sk.slots')
    ok(sum(1 for x in sl if x['sid'] == 16) == 1, 'player %d starts with exactly one MAX (%r)' % (i + 1, [x['sid'] for x in sl]))
bots = J(H, '(function(){ var _o = []; for (var _i = 0; _i < array_length(global.kfo.H.pl); _i++) { var _p = global.kfo.H.pl[_i]; if (_p.bot && is_struct(_p.bt)) array_push(_o, _p.bt.sk.slots); } return _o; })()')
ok(len(bots) == 1 and bots[0].count(16) == 1, 'the bot starts with exactly one MAX (%r)' % bots)

# ---- the feed: one send, one line, in every game
for _ in range(40):
    if all(J(s, 'global.kfo.M.R.ph') == 'run' for s in sims):
        break
    go(net, sims, 10)
for s in sims:
    s.run('global.kfo.M.log = [];')
H.run('global.kfo.M.tg.mode = 4; global.kfo.M.tg.pick = 2; kbr_tg_send(global.kfo.M, true);')
go(net, sims, 10)
H.run('var _S = global.kfo.M.sk; array_push(_S.slots, { sid: 10, rev: 0 }); _S.sel = array_length(_S.slots) - 1; _S.cd = 0; global.USED = kbr_skill_use();')
go(net, sims, 30)
for i, s in enumerate(sims):
    L = [l for l in logs(s) if 'Knightmare' in l]
    ok(len(L) == 1, 'game %d: the send is one line, not two (%r)' % (i + 1, L))
ok(any(l == '* %s sent Knightmare to %s.' % (J(H, 'global.kfo.name'), J(C2, 'global.kfo.name')) for l in logs(C2)), 'the short wording: %r' % logs(C2)[-2:])
# the same standings twice: nothing new
n0 = len(J(C2, 'global.kfo.M.log'))
C2.run('kfo_on_state(global.kfo.M.st);')
ok(len(J(C2, 'global.kfo.M.log')) == n0, 'the same standings again add no line')
# the same line again within a second: x2
C3.run('global.kfo.M.log = []; kbr_log("* Noelle is OUT (#3)", c_red); kbr_log("* Noelle is OUT (#3)", c_red);')
L = J(C3, 'global.kfo.M.log')
ok(len(L) == 1 and L[0]['t'].endswith('x2'), 'two identical lines within a second are one with x2 (%r)' % [x['t'] for x in L])

# ---- MAX: the host refuses a second one
n_bad = J(H, 'global.kfo.H.skills_bad')
C2.run('var _S = global.kfo.M.sk; _S.sel = 0; _S.cd = 0; global.hp[kbr_char()] = 40; global.NOHEAL = 1; global.USED = kbr_skill_use();')
go(net, sims, 30)
hp = J(C2, 'global.hp[kbr_char()]')
mh = J(C2, 'global.maxhp[kbr_char()]')
ok(hp == mh and mh > 80, 'MAX fills to max HP at 50%% HEAL POWER from 40 HP (build 50 stopped at 40 + half of max) (%r / %r)' % (hp, mh))
ok(J(H, 'kfo_host_player(2).fh') == 1, 'the host counts it (fh 1)')
ok(not any(x['sid'] == 16 for x in J(C2, 'global.kfo.M.sk.slots')), 'it is gone from the slots')
ok(any(l.endswith('used MAX.') for l in logs(H)), 'the feed says "used MAX." (%r)' % [l for l in logs(H) if 'MAX' in l])
# a resync does not give one back, and a second MAX is refused
C2.run('kfo_resync_local("test");')
go(net, sims, 10)
ok(not any(x['sid'] == 16 for x in J(C2, 'global.kfo.M.sk.slots')), 'a resync gives no new MAX')
C2.run('var _S = global.kfo.M.sk; array_push(_S.slots, { sid: 16, rev: 0 }); _S.sel = array_length(_S.slots) - 1; _S.cd = 0; global.USED = kbr_skill_use();')
go(net, sims, 30)
ok(J(H, 'global.kfo.H.skills_bad') > n_bad and J(H, 'kfo_host_player(2).fh') == 2, 'a second MAX is refused by the host (fh %r)' % J(H, 'kfo_host_player(2).fh'))
ok(not J(C2, 'kbr_skill_red(16)'), 'MAX is green (targeting never sends it)')

# ---- a rematch: the host's match start resets every count, and a new match's skills start with one MAX
ok('_p.fh = 0;' in open('/home/claude/scripts/gml_templates_v6/online_host.gml').read(), "the host's match start resets fh (online_host.gml)")
sl = J(C2, 'kbr_skills_new(global.kfo.M.eff).slots')
ok([x['sid'] for x in sl] == [16], 'a new match starts with one MAX (%r)' % sl)
sl = J(H, 'kfo_bot_skill_new().slots')
ok(sl == [16], 'a new bot starts with one MAX (%r)' % sl)

print('feed / MAX: %d checks, %d failed (%.0fs)' % (N[0], len(FAILS), time.time() - t0))
for f in FAILS:
    print('  -', f)
sys.exit(1 if FAILS else 0)
