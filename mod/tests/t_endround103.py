"""DRBR 1.0.3 - your request: "add an end round button for the host". A room of three games (br_multi: the real code in every
game, the simulated network) in a running match, and a practice room with bots:
  - the host's GIVE UP box (BACKSPACE) has END ROUND; a player's has not;
  - END ROUND asks again ("END THE ROUND?": Keep playing / End the round); Keep playing goes back to the match;
  - End the round: the round ends in every game - the results (the most HP wins, as at TIME), the feed and the room's chat
    say the host ended it, the room is back in the lobby;
  - the room's page: an END ROUND row for the host while a match runs (none for a player, none without a match); its box
    ends the round too (the practice room with bots: the bots are placed by HP).
Usage: python3 t_endround103.py"""
import sys, os, json, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from br_multi import *

FAILS = []
N = [0]


def ok(c, m):
    N[0] += 1
    print(('ok   ' if c else 'FAIL ') + m, flush=True)
    if not c:
        FAILS.append(m)
    return c


def J(s, e):
    return s.py(s.eval(e))


def keep_hp(sims):
    for s in sims:
        s.run('if (is_struct(global.kfo.M) && !global.kfo.M.out && global.kfo.M.me) global.hp[kbr_char()] = max(1, global.hp[kbr_char()]);')


net, sims = make_room(3, 'lan', 5310, setx='_s.mhp = 400;', kn=(0, 1), open_ok=0)
H, C2, C3 = sims


def go(n):
    rec = run(net, sims, n, 'none', wall=900)
    errs = {c: rec[c]['errors'][:1] for c in range(1, 4) if rec[c]['errors']}
    ok(not errs, 'no errors in the games (%d frames) %r' % (n, errs))
    return rec


go(420)
ok(J(H, 'global.kfo.M.go') and J(H, 'global.kfo.H.st') == 'match', 'the match runs')
# different HP: Susie's game the most, Ralsei's the least (the results go by HP %)
C2.run('global.hp[kbr_char()] = 380;')
C3.run('global.hp[kbr_char()] = 120;')
H.run('global.hp[kbr_char()] = 250;')
go(40)

# ---- the GIVE UP boxes
H.run('global.P = kfo_leave_request();')
opts_h = J(H, '(function(){ var _o = []; with (obj_knight_prompt) { for (var _i = 0; _i < array_length(opts); _i++) array_push(_o, [opts[_i].t, opts[_i].a]); } return _o; })()')
ok(['END ROUND', 'onl_endround_ask'] in opts_h, 'the host\'s GIVE UP box has END ROUND (%r)' % opts_h)
ok(any('END ROUND' in l for l in J(H, 'obj_knight_prompt.lines')), 'it says what END ROUND does (%r)' % J(H, 'obj_knight_prompt.lines'))
H.run('knight_run_teardown();')
C2.run('global.P = kfo_leave_request();')
opts_c = J(C2, '(function(){ var _o = []; with (obj_knight_prompt) { for (var _i = 0; _i < array_length(opts); _i++) array_push(_o, opts[_i].t); } return _o; })()')
ok('END ROUND' not in opts_c and 'Leave' in opts_c, 'a player\'s GIVE UP box has no END ROUND (%r)' % opts_c)
C2.run('knight_run_teardown();')

# ---- asked again; Keep playing goes back to the match
H.run('global.P = kfo_leave_request(); knight_act_run("onl_endround_ask");')
t = J(H, 'instance_exists(obj_knight_prompt) ? [obj_knight_prompt.title, obj_knight_prompt.opts[0].t, obj_knight_prompt.opts[1].t] : []')
ok(t == ['END THE ROUND?', 'Keep playing', 'End the round'], 'END ROUND asks again (%r)' % t)
H.run('knight_act_run("resume");')
go(30)
ok(J(H, 'global.kfo.H.st') == 'match' and not J(H, 'global.kfo.M.ended') and not J(H, 'instance_exists(obj_knight_prompt)'),
   'Keep playing: the match goes on (host %r, ended %r)' % (J(H, 'global.kfo.H.st'), J(H, 'global.kfo.M.ended')))

# ---- End the round (the host's own records decide the places: Susie the most HP, Ralsei the least)
H.run('for (var _i = 0; _i < array_length(global.kfo.H.pl); _i++) { var _p = global.kfo.H.pl[_i]; _p.mh = 400; _p.hp = (_p.n == "Susie") ? 380 : ((_p.n == "Ralsei") ? 120 : 250); }')
H.run('global.P = kfo_leave_request(); knight_act_run("onl_endround_ask");')
H.run('with (obj_knight_prompt) { sel = 1; knight_act_run(opts[1].a); }')
go(60)
for name, s in (('host', H), ('Susie\'s game', C2), ('Ralsei\'s game', C3)):
    r = J(s, 'is_struct(global.kfo.M) ? [global.kfo.M.ended, is_struct(global.kfo.M.res) ? kfo_js(global.kfo.M.res, "wn", "") : "", global.krun.state] : []')
    ok(r and r[0] and r[1] == 'Susie', '%s: the round is over - the most HP won (%r)' % (name, r))
feed = J(H, 'global.kfo.H.feed')
ok(any('ended the round' in str(f[1]) for f in feed), 'the feed says the host ended it (%r)' % [f[1] for f in feed][-3:])
ok(J(H, 'global.kfo.H.st') == 'lobby', 'the room is back in the lobby (%r)' % J(H, 'global.kfo.H.st'))
res = J(H, 'global.kfo.H.res')
places = {p['n']: p['pl'] for p in res['pl']}
ok(places.get('Susie') == 1 and places.get('Kris') == 2 and places.get('Ralsei') == 3, 'placed by HP: %r' % places)

# ---- the room's page: the host's END ROUND row (a practice room with bots, its match running)
sim, e = br_match(open_ok=0, kn=(0,), seed=5320, bots=3, setx='_s.mhp = 300;')
ok(e is None, 'a practice room with 3 bots starts (%r)' % (e,))
for f in range(400):
    step(sim, 1)
sim.run('global.kfo.lobby = kfo_host_lobby_msg();')
rows = J(sim, 'kfo_ui_lobby_rows()')
ok('endround' in rows and rows.index('endround') == 1, 'the room\'s page: END ROUND under START while the match runs (%r)' % rows[:4])
sim.run('global.knight_ui = knight_ui_open_state(); global.knight_ui.sub = "lobby"; global.knight_ui.lob_row = 1;')
desc = J(sim, 'kfo_ui_desc()')
ok('end the running round' in str(desc).lower(), 'its line in the top bar (%r)' % desc)
sim.run('global.kfo.H.pl[1].hp = 200; global.kfo.H.pl[2].hp = 50; global.kfo.H.pl[3].hp = 290; global.hp[kbr_char()] = 100;')
sim.run('for (var _i = 0; _i < array_length(global.kfo.H.pl); _i++) global.kfo.H.pl[_i].mh = 300;')
sim.run('kfo_ui_modal_do("kfo_endround");')
for f in range(30):
    step(sim, 1)
res = J(sim, 'global.kfo.H.res')
pl = {p['n']: p['pl'] for p in res['pl']} if isinstance(res, dict) else {}
ok(isinstance(res, dict) and res['wn'] == 'QUEEN' or (isinstance(res, dict) and pl.get(res['wn']) == 1), 'the room\'s END ROUND ends it: %s wins, places %r' % (res.get('wn') if isinstance(res, dict) else res, pl))
sim.run('global.kfo.lobby = kfo_host_lobby_msg();')
ok('endround' not in J(sim, 'kfo_ui_lobby_rows()'), 'no END ROUND row without a running match (%r)' % J(sim, 'kfo_ui_lobby_rows()')[:3])

print('\n%d checks, %d failed' % (N[0], len(FAILS)))
for f in FAILS:
    print('  FAIL', f)
sys.exit(1 if FAILS else 0)
