"""Build 45 (rewritten from build 43): Knight Fights Online - the GML core without a network: names / codes / servers, the
build number rooms compare, the player's options in the ini, a practice room and its bots, and the host's room with remote
players faked: joins, READY, START, a player leaving in the match (OUT "left"), REJOIN / SPECTATORS deciding who may watch,
the next match, the host leaving (takeover keeps the room's settings, bots and a running match). The settings, the timeline,
the rules, the transports and the battle have their own tests (t_online_set45, t_br_timeline, t_br_rules, t_online_net,
t_steam_gml, t_br_single / t_br_multi)."""
import sys, json, random
from harness import *

FAILS = []
N = [0]


def ok(c, msg):
    N[0] += 1
    if not c:
        FAILS.append(msg)
        print('FAIL', msg)


def eq(a, b, msg):
    N[0] += 1
    if a != b:
        FAILS.append(msg)
        print('FAIL', msg, 'got', repr(a), 'want', repr(b))


def new():
    sim = make_sim()
    sim.run('knight_store_load(); global.knight_cfg = knight_cfg_default();')
    sim.run('kfo_get();')
    sim.mock('kfo_launch', lambda s: 0)
    sim.mock('knight_launch_go', lambda s: 0)
    return sim


def J(sim, expr):
    return sim.py(sim.eval(expr))


# ---------------------------------------------------------------- text helpers
sim = new()
eq(J(sim, 'kfo_clean_name("  Kris   Dree  ")'), 'Kris Dree', 'name: spaces collapsed and trimmed')
eq(J(sim, 'kfo_clean_name("ionizachip12345")'), 'ionizachip12', 'name: 12 characters')
eq(J(sim, 'kfo_clean_name(chr(7) + "Su" + chr(200) + "sie")'), 'Susie', 'name: control / non-ASCII removed')
eq(J(sim, 'kfo_clean_name(42)'), '', 'name: not a string')
eq(J(sim, 'kfo_clean_code("vn-r tk9")'), 'VNRTK', 'code: letters only, upper case')
eq(J(sim, 'kfo_clean_code("abcdefghij")'), 'ABCDEFG', 'code: at most 7 letters (Steam codes are 7, relay codes 5)')
eq(J(sim, 'kfo_clean_code(5)'), '', 'code: not a string')
eq(J(sim, 'kfo_parse_server("203.0.113.5:7777")'), ['203.0.113.5', 7777], 'server with port')
eq(J(sim, 'kfo_parse_server(" relay.example.org ")'), ['relay.example.org', 7777], 'server: default port')
eq(J(sim, 'kfo_parse_server("localhost:25565")'), ['localhost', 25565], 'server: other port')
for bad in ('"host:0"', '"host:70000"', '"host:"', '":7777"', '"bad host:7777"', '"a/b"', '"h:12a"', '5', 'undefined'):
    ok(sim.eval('is_undefined(kfo_parse_server(%s))' % bad), 'server refused: ' + bad)
eq(J(sim, 'kfo_version()'), 51, 'the build rooms compare (build 51: a build 50 game cannot join)')
for why, want in (('No such room', 'There is no room with that code.'), ('Full Player', 'That room is full.'),
                  ('Client Is Older', 'The room\'s players have a newer Knight Hub build.'), ('Client Is Newer', 'The room\'s players have an older Knight Hub build.')):
    eq(J(sim, 'kfo_refusal_text("%s")' % why), want, 'refusal: ' + why)
eq(J(sim, 'kfo_num("abc12x3", 0)'), 123, 'outside number: digits read')
eq(J(sim, 'kfo_num("", 7)'), 7, 'outside number: none -> the default (never real(""))')
eq(J(sim, 'kfo_num(undefined, 7)'), 7, 'outside number: not text -> the default')

# ---------------------------------------------------------------- the player's options in the ini
# (build 47: the other SOULs' opacity and names live in [view] - SOUL VISIBILITY; build 46's two keys are written from them)
sim.run('var _o = kfo_get(); _o.name = "Berdly"; _o.skin = 3; _o.srv = "10.1.2.3"; _o.port = 9000; _o.view.sop = 40; _o.view.names = 1; _o.vis = 2; _o.lastcode = "QWERTYU"; kfo_ini_save();')
s2 = make_sim()
s2.fs.load(sim.fs.dump())
s2.run('knight_store_load(); global.knight_cfg = knight_cfg_default(); kfo_get();')
eq(J(s2, '[kfo_get().name, kfo_get().skin, kfo_get().srv, kfo_get().port, kfo_get().view.sop, kfo_get().view.names, kfo_get().vis, kfo_get().lastcode]'),
   ['Berdly', 3, '10.1.2.3', 9000, 40, 1, 2, 'QWERTYU'], 'the options come back in the next game')
eq(J(s2, '[kfo_get().sop, kfo_get().names]'), [40, 1], 'build 46\'s two keys follow SOUL VISIBILITY')
# a broken ini: everything falls back to sane values
s3 = make_sim()
s3.run('ossafe_ini_open(kfo_ini_file()); ini_write_string("player", "name", "' + 'x' * 300 + '"); ini_write_real("player", "skin", 77); ini_write_string("server", "host", "bad host!!");'
       'ini_write_real("server", "port", -5); ini_write_real("player", "soul_opacity", 9999); ini_write_real("player", "lobby_type", 9); ini_write_string("room", "settings", "{{{{");'
       'ossafe_ini_close(); knight_store_load(); global.knight_cfg = knight_cfg_default(); kfo_get();')
o3 = J(s3, '[string_length(kfo_get().name), kfo_get().skin, kfo_get().view.sop, kfo_get().vis, kfo_get().set.pre]')
eq(o3, [12, 1, 70, 2, 'CLASSIC'], 'a broken ini gives sane options (build 48: a file without [view] starts the other SOULs at 70%)')
# build 48: a file saved by build 47 (the others at 20%, no v48 mark) starts at 70% once; then the player's own value stays
s5 = make_sim()
s5.run('ossafe_ini_open(kfo_ini_file()); ini_write_real("view", "sop", 20); ossafe_ini_close(); knight_store_load(); global.knight_cfg = knight_cfg_default(); kfo_get();')
eq(J(s5, 'kfo_get().view.sop'), 70, 'build 48: a build 47 file\'s 20% becomes 70% once')
s5.run('kfo_get().view.sop = 35; kfo_ini_save(); global.kfo = undefined; kfo_get();')
eq(J(s5, 'kfo_get().view.sop'), 35, 'build 48: after that the player\'s own opacity is kept')
s4 = make_sim()
s4.run('ossafe_ini_open(kfo_ini_file()); ini_write_real("view", "sop", 9999); ini_write_real("view", "names", 7); ini_write_string("look", "color", "#GG0000");'
       'ini_write_real("look", "hli", -4); ossafe_ini_close(); knight_store_load(); global.knight_cfg = knight_cfg_default(); kfo_get();')
eq(J(s4, '[kfo_get().view.sop, kfo_get().view.names, kfo_get().look.col, kfo_get().look.hli]'), [70, 0, 255, 2], 'a broken [view] / [look]: the defaults (build 48: 70%, no names, red, medium)')

# ---------------------------------------------------------------- practice and its bots
sim = new()
sim.run('global.kfo.name = "Kris"; kfo_practice_start();')
eq(J(sim, '[global.kfo.st, global.kfo.mode, global.kfo.code, kfo_is_host()]'), ['room', 'local', 'PRACTICE', True], 'practice: a local room you host')
sim.run('var _s = kfo_set_clean(global.kfo.H.set); _s.bots = 5; kfo_host_set(_s); kfo_tick(); kfo_tick();')
pl = J(sim, 'kfo_lobby_players()')
eq(len(pl), 6, 'practice: you and 5 bots')
ok(len(set(p['n'] for p in pl)) == 6 and all(p['bot'] == 1 for p in pl[1:]), 'the bots have their own names')
sim.run('var _s = kfo_set_clean(global.kfo.H.set); _s.bots = 0; kfo_host_set(_s); kfo_tick(); kfo_tick();')
eq(len(J(sim, 'kfo_lobby_players()')), 1, 'practice: bots back to 0')

# ---------------------------------------------------------------- the host's room with remote players faked
sent = []
sim = new()
sim.mock('kfo_raw', lambda s, m: sent.append(s.py(m)) or True)
sim.run('var _o = global.kfo; _o.name = "Kris"; _o.st = "room"; _o.mode = "direct"; _o.my = 1; _o.hostid = 1; _o.code = "ABCDE";'
        '_o.members = [{ pid: 1, name: "Kris" }]; kfo_host_begin("ABCDE", false);')
for pid, nm in ((2, 'Susie'), (3, 'Ralsei'), (4, 'Kris')):
    sim.run('kfo_on_member("join", %d, "%s"); kfo_host_on(%d, { k: "hi", name: "%s", skin: 2, ver: kfo_version() });' % (pid, nm, pid, nm))
names = [p['n'] for p in J(sim, 'kfo_lobby_players()')] if J(sim, 'is_struct(global.kfo.lobby)') else [p['n'] for p in J(sim, 'global.kfo.H.pl')]
hpl = [p['n'] for p in J(sim, 'global.kfo.H.pl')]
eq(len(hpl), 4, 'three players joined')
ok(len(set(hpl)) == 4, 'a second "Kris" gets a name of its own (%r)' % hpl)
# an old build is refused
sim.run('kfo_on_member("join", 5, "Noelle"); kfo_host_on(5, { k: "hi", name: "Noelle", skin: 4, ver: 44 });')
ok(not any(p['pid'] == 5 for p in J(sim, 'global.kfo.H.pl')), 'a player with build 44 is not let in')
ok(any(m.get('t') == 'down' and m.get('to') == 5 and m.get('m', {}).get('k') == 'kick' for m in sent), 'and is told why')
sim.run('kfo_on_member("leave", 5, "");')
# READY and START
sim.run('var _s = kfo_set_clean(global.kfo.H.set); _s.ready = 1; kfo_host_set(_s);')
eq(J(sim, 'kfo_host_start()'), 'Everyone has to be READY (3 not yet).', 'READY CHECK: EVERYONE')
for pid in (2, 3):
    sim.run('kfo_host_on(%d, { k: "ready", on: 1 });' % pid)
eq(J(sim, 'kfo_host_start()'), 'Everyone has to be READY (1 not yet).', 'one still not ready')
sim.run('var _s = kfo_set_clean(global.kfo.H.set); _s.ready = 0; _s.spec = 0; _s.rejoin = 1; kfo_host_set(_s);')
eq(J(sim, 'kfo_host_start()'), '', 'READY ONES: starts with the ready players')
inm = {p['n']: p['inm'] for p in J(sim, 'global.kfo.H.pl')}
eq(sorted(n for n, v in inm.items() if v), sorted(['Kris', 'Susie', 'Ralsei']), 'the ready ones are in the match')
sim.run('kfo_local_run(); var _h = global.kfo.H; _h.go = true; _h.t0ms = current_time - 3000;')
# player 3 leaves in the match: OUT ("left"), placed
sim.run('kfo_on_member("leave", 3, ""); kfo_host_member("leave", 3, ""); kfo_host_outs_settle(true);')
eq(J(sim, 'kfo_host_alive()'), 2, 'a player who left is out of the match')
ok(any('left the match' in f[1] for f in J(sim, 'global.kfo.H.feed')), 'the feed says who left')
# REJOIN on, SPECTATORS off: the one who left may watch when they come back; a newcomer may not
sim.run('kfo_on_member("join", 6, "Ralsei"); kfo_host_on(6, { k: "hi", name: "Ralsei", skin: 3, ver: kfo_version() });'
        'kfo_on_member("join", 7, "Lancer"); kfo_host_on(7, { k: "hi", name: "Lancer", skin: 1, ver: kfo_version() });')
eq(J(sim, 'kfo_host_may_watch(kfo_host_player(6))'), True, 'REJOIN: the player who lost the connection may watch')
eq(J(sim, 'kfo_host_may_watch(kfo_host_player(7))'), False, 'SPECTATORS off: a newcomer may not')
lob = J(sim, 'kfo_host_lobby_msg()')
eq({p['n']: p['rj'] for p in lob['players'] if p['pid'] in (6, 7)}, {'Ralsei': 1, 'Lancer': 0}, 'the lobby tells each player whether they may watch')
sent.clear()
sim.run('kfo_host_on(6, { k: "watch" }); kfo_host_on(7, { k: "watch" });')
starts = [m for m in sent if m.get('t') == 'down' and m.get('m', {}).get('k') == 'start']
eq([m['to'] for m in starts], [6], 'only the returning player is sent the match to watch')
sim.run('var _s = kfo_set_clean(global.kfo.H.set); _s.spec = 1; global.kfo.H.eff.spec = 1;')
eq(J(sim, 'kfo_host_may_watch(kfo_host_player(7))'), True, 'SPECTATORS on: anyone in the room may watch')
# the match ends: the next one counts on
sim.run('kfo_host_out_report(2, 900, "out"); kfo_host_outs_settle(true);')
eq(J(sim, '[global.kfo.H.st, global.kfo.H.res.wn]'), ['lobby', 'Kris'], 'the last one standing wins; the room is back')
eq(J(sim, 'kfo_host_may_watch(kfo_host_player(6))'), False, 'no match: nobody watches')
# ---------------------------------------------------------------- the host removes a player
sent.clear()
eq(J(sim, 'kfo_host_kick(6)'), True, 'KICK: the host removes Ralsei')
ok(not any(p['pid'] == 6 for p in J(sim, 'global.kfo.H.pl')), 'Ralsei is out of the room')
ok(any(m.get('t') == 'down' and m.get('to') == 6 and m.get('m', {}).get('k') == 'kick' for m in sent), 'Ralsei is told why')
ok(any(m.get('t') == 'kick' and m.get('id') == 6 for m in sent), 'the relay drops the connection from the room')
eq(J(sim, 'kfo_host_kick(1)'), False, 'the host cannot remove itself')
sent.clear()
sim.run('kfo_host_member("join", 6, "Ralsei"); kfo_host_on(6, { k: "hi", name: "Ralsei", skin: 3, ver: kfo_version() });')
ok(not any(p['pid'] == 6 for p in J(sim, 'global.kfo.H.pl')), 'a removed player cannot come back into the room')
eq(J(sim, 'array_length(kfo_ui_kickable())') >= 1, True, 'REMOVE A PLAYER lists the others')

# ---------------------------------------------------------------- takeover: the next host keeps the room as it was
sim2 = new()
lobby = J(sim, 'kfo_host_lobby_msg()')
lobby['set']['mhp'] = 220
lobby['set']['bots'] = 2
sim2.run('var _o = global.kfo; _o.name = "Susie"; _o.st = "room"; _o.mode = "direct"; _o.my = 2; _o.hostid = 1; _o.code = "ABCDE";'
         '_o.lobby = json_parse(%s); _o.members = [{ pid: 1, name: "Kris" }, { pid: 2, name: "Susie" }, { pid: 6, name: "Ralsei" }];' % json.dumps(json.dumps(lobby)))
sim2.run('kfo_on_promote(2, [{ id: 2, name: "Susie" }, { id: 6, name: "Ralsei" }]);')
eq(J(sim2, 'kfo_is_host()'), True, 'Susie hosts now')
eq(J(sim2, 'global.kfo.H.set.mhp'), 220, 'the new host keeps the room\'s settings')
hp = [p['n'] for p in J(sim2, 'global.kfo.H.pl')]
ok('Ralsei' in hp and 'Kris' not in hp, 'the room\'s players without the old host (%r)' % hp)
eq(J(sim2, 'global.kfo.hostid'), 2, 'the host id moved')

print('online core: %d checks, %d failed' % (N[0], len(FAILS)))
sys.exit(1 if FAILS else 0)
