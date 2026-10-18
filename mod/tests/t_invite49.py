"""Build 49: STEAM INVITES in the game. The INVITE page (the room's INVITE FRIENDS, Steam rooms) laid out with the game's real
font metrics, sending an invite (kf_invite_user called with the friend's account), an invite that comes in (the box with
JOIN / NOT NOW when the menu is open; JOIN leaves the room and looks the new one up), and an older kf_steam.dll without the
friends functions (only STEAM OVERLAY). kf_steam.dll itself is stood in for (its own test: online/steam/t_steam_dll.py)."""
import sys, json
sys.path.insert(0, '/home/claude/work/uiref')
sys.path.insert(0, '/home/claude/work/tests')
SRC = open('/home/claude/work/tests/t_online_ui47.py').read()
exec(SRC[:SRC.index('# ---------------------------------------------------------------- KNIGHT tab')])
FR = ['76561|1|1|Susie', '2002|1|0|Ralsei', '2003|3|0|WWWWWWWWWWWWWWWWWWWW', '2004|0|0|Noelle']
for i in range(20):
    FR.append('%d|0|0|Friend%d' % (3000 + i, i))
CALLS = []


def steam_mock(sim, full=True):
    def sx(s, name, *a):
        CALLS.append((name,) + tuple(a))
        if name == 'kf_friends_refresh':
            return len(FR)
        if name == 'kf_friend_info':
            i = int(a[0])
            return FR[i] if 0 <= i < len(FR) else ''
        if name == 'kf_invite_user':
            return 1
        if name == 'kf_name':
            return 'Lancer'
        if name == 'kf_lobby_id':
            return '1234'
        if name in ('kf_lobby_find_id', 'kf_overlay_on', 'kf_invite_overlay'):
            return 1
        return ''
    sim.mock('kfo_sx', sx)
    fns = '{ kf_friends_refresh: 1, kf_friend_info: 2, kf_invite_user: 3 }' if full else '{}'
    sim.run('global.kfo_stm = { ok: true, init: 1, why: "", fns: %s, dll: "kf_steam.dll" };' % fns)


sim, rec = setup()
steam_mock(sim)
room(sim, 3, mode='steam')
rows = None
sim.run('kfo_ui_inv_open("lobby");')
rows = sim.py(sim.eval('kfo_ui_inv_rows()'))
eq(len(rows), len(FR) + 3, 'one row per friend + REFRESH, STEAM OVERLAY, DONE')
eq(sim.py(sim.eval('kfo_ui_inv_label("f0")')), ['Susie', 'IN GAME'], 'the first friend, playing')
eq(sim.py(sim.eval('kfo_ui_inv_label("f3")'))[1], 'OFFLINE', 'an offline friend')
for row in list(range(0, 6)) + [len(rows) - 3, len(rows) - 2, len(rows) - 1]:
    sim2, rec2 = setup()
    steam_mock(sim2)
    room(sim2, 3, mode='steam')
    sim2.run('kfo_ui_inv_open("lobby");')
    draw(sim2, rec2, 'U.tab=0; U.focus=1; U.krow=10; U.sub="onl_inv"; U.pg_row=%d; U.pg_scroll=%d;' % (row, max(0, row - 13)))
    check('invite r%d' % row, rec2)
    desc_ok(sim2, 'invite r%d' % row)
    if row in (0, 2):
        rec2.render('/home/claude/work/uishots/invite_r%d.png' % row)
# Z on a friend: the invite goes to that account
del CALLS[:]
sim.run('kfo_ui_pg_change("onl_inv", "f1", 1, true);')
ok(('kf_invite_user', 2002.0) in [(c[0], float(c[1])) for c in CALLS if len(c) > 1], 'Z on Ralsei: kf_invite_user(2002) %r' % CALLS[-2:])
eq(sim.py(sim.eval('kfo_ui_inv_label("f1")'))[1], 'INVITED', 'shown as INVITED')
# the lobby row opens the page
sim.run('global.knight_ui.sub = "lobby";')
lr = sim.py(sim.eval('kfo_ui_lobby_rows()'))
ok('invite' in lr, 'Steam room: INVITE FRIENDS row')
# an invite comes in: the box when the menu is open, JOIN leaves this room and looks the other up
sim.run('kfo_steam_event("invited:99999|555");')
ok(sim.eval('is_struct(global.kfo.inv_in)'), 'the invite is kept')
sim.run('global.knight_ui.modal = undefined; global.knight_ui.tp = 80; kfo_inv_modal_check();')
m = sim.py(sim.eval('global.knight_ui.modal'))
ok(m is not None and m['k'] == 'kfo_invite' and 'Lancer' in m['lines'][0], 'the STEAM INVITE box: %r' % (m['lines'] if m else None))
rec.ops.clear()
sim.run('knight_ui_draw();')
check('invite box', rec, modal=True)
rec.render('/home/claude/work/uishots/invite_box.png')
del CALLS[:]
sim.run('knight_ui_modal_do("kfo_inv_join");')
ok(any(c[0] == 'kf_lobby_find_id' and c[1] == '99999' for c in CALLS), 'JOIN: the room is looked up (%r)' % CALLS)
ok(not sim.eval('kfo_in_room()') or sim.eval('global.kfo.mode') == 'steam', 'left the old room')
# an older DLL: no friends, STEAM OVERLAY still there
sim3, rec3 = setup()
steam_mock(sim3, full=False)
room(sim3, 3, mode='steam')
sim3.run('kfo_ui_inv_open("lobby");')
eq(sim3.py(sim3.eval('kfo_ui_inv_rows()')), ['refresh', 'ovl', 'done'], 'an older kf_steam.dll: only REFRESH / STEAM OVERLAY / DONE')
draw(sim3, rec3, 'U.tab=0; U.focus=1; U.krow=10; U.sub="onl_inv"; U.pg_row=1; U.pg_scroll=0;')
check('invite old dll', rec3)
print('invites: %d checks, %d failed' % (N[0], len(FAILS)))
sys.exit(1 if FAILS else 0)
