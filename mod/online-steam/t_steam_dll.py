"""Build 45: kf_steam's own logic, tested on Linux against a PRETEND Steam (mock/mock_steam_backend.py + libmock_steam_api.so).
Each player is its own process with its own copy of libkf_steam.so (the same source as kf_steam.dll), as each game is.
What this shows: kf_steam's init and failure reporting, lobby create / code lookup / join, the version and fullness data,
browse, members in and out, the owner (host) changing, invites (join requests), private rooms refusing codes, and P2P text
packets both ways (reliable and unreliable). What it does NOT show: anything about real Steam (its servers, NAT traversal,
the overlay, Spacewar app 480 behaviour) - that needs real Steam clients and accounts."""
import os, sys, time, ctypes, subprocess, multiprocessing as mp, json

HERE = os.path.dirname(os.path.abspath(__file__))
B = os.path.join(HERE, 'build')
SOCK = '/tmp/claude-0/kfmock.sock'
FAILS = []
N = [0]


def ok(c, m):
    N[0] += 1
    if not c:
        FAILS.append(m)
        print('FAIL', m, flush=True)


SIG = {'kf_init': ('d', ''), 'kf_status': ('s', ''), 'kf_my_acct': ('d', ''), 'kf_my_name': ('s', ''), 'kf_name': ('s', 'd'),
       'kf_lobby_create': ('d', 'dd'), 'kf_lobby_find': ('d', 's'), 'kf_lobby_find_id': ('d', 's'), 'kf_lobby_join_id': ('d', 's'),
       'kf_lobby_leave': ('d', ''), 'kf_lobby_id': ('s', ''), 'kf_lobby_code': ('s', ''), 'kf_lobby_owner': ('d', ''), 'kf_lobby_count': ('d', ''),
       'kf_lobby_member': ('d', 'd'), 'kf_lobby_set': ('d', 'ss'), 'kf_lobby_get': ('s', 's'), 'kf_lobby_joinable': ('d', 'd'), 'kf_lobby_limit': ('d', 'd'),
       'kf_browse': ('d', ''), 'kf_browse_count': ('d', ''), 'kf_browse_info': ('s', 'd'), 'kf_found_info': ('s', ''), 'kf_invite_overlay': ('d', ''),
       'kf_overlay_on': ('d', ''), 'kf_send': ('d', 'dsd'), 'kf_recv': ('s', ''), 'kf_recv_from': ('d', ''), 'kf_poll': ('s', ''),
       'kf_launch_lobby': ('s', ''), 'kf_shutdown': ('d', ''),
       'kf_friends_refresh': ('d', ''), 'kf_friend_info': ('s', 'd'), 'kf_invite_user': ('d', 'd')}


def worker(conn, env):
    os.environ.update(env)
    lib = ctypes.CDLL(os.path.join(B, 'libkf_steam.so'))
    T = {'d': ctypes.c_double, 's': ctypes.c_char_p}
    for n, (r, a) in SIG.items():
        f = getattr(lib, n)
        f.restype = T[r]
        f.argtypes = [T[x] for x in a]
    while True:
        cmd = conn.recv()
        if cmd[0] == 'quit':
            break
        if cmd[0] == 'call':
            f = getattr(lib, cmd[1])
            args = [a.encode() if isinstance(a, str) else float(a) for a in cmd[2:]]
            r = f(*args)
            conn.send(r.decode() if isinstance(r, bytes) else r)
        elif cmd[0] == 'events':
            # poll for a while, collecting events and packets
            evs, pk = [], []
            t_end = time.time() + cmd[1]
            while time.time() < t_end:
                e = lib.kf_poll().decode()
                while e:
                    evs.append(e)
                    e = lib.kf_poll().decode()
                p = lib.kf_recv().decode()
                while p:
                    pk.append((int(lib.kf_recv_from()), p))
                    p = lib.kf_recv().decode()
                time.sleep(0.01)
            conn.send((evs, pk))


class P:
    def __init__(self, acct, name, extra=None):
        env = {'KF_STEAM_API': os.path.join(B, 'libmock_steam_api.so'), 'KF_MOCK_SOCK': SOCK, 'KF_MOCK_ACCT': str(acct), 'KF_MOCK_NAME': name}
        env.update(extra or {})
        self.c, c2 = mp.Pipe()
        self.p = mp.Process(target=worker, args=(c2, env), daemon=True)
        self.p.start()
        self.acct = acct

    def call(self, *a):
        self.c.send(('call',) + a)
        return self.c.recv()

    def events(self, secs=0.3):
        self.c.send(('events', secs))
        return self.c.recv()

    def stop(self):
        self.c.send(('quit',))
        self.p.join(2)


def ctl(cmd):
    import socket
    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    s.connect(SOCK)
    s.sendall((cmd + '\n').encode())
    r = s.makefile().readline().strip()
    s.close()
    return r


def main():
    os.makedirs('/tmp/claude-0', exist_ok=True)
    be = subprocess.Popen([sys.executable, os.path.join(HERE, 'mock', 'mock_steam_backend.py'), SOCK], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    be.stdout.readline()
    try:
        # ---- no Steam API at all / Steam not running
        X = P(9, 'NoApi', {'KF_STEAM_API': '/nonexistent/libsteam_api.so'})
        ok(X.call('kf_init') == 0, 'no steam_api: kf_init 0')
        ok('not found' in X.call('kf_status'), 'no steam_api: status says so')
        X.stop()
        Y = P(8, 'Offline', {'KF_MOCK_OFFLINE': '1'})
        ok(Y.call('kf_init') == -1, 'Steam not running: kf_init -1')
        ok('No Steam client' in Y.call('kf_status'), 'Steam not running: the reason comes through (%s)' % Y.call('kf_status'))
        Y.stop()
        # ---- three players
        A, Bp, C = P(1001, 'Kris'), P(1002, 'Susie'), P(1003, 'Ralsei')
        for p in (A, Bp, C):
            ok(p.call('kf_init') == 1, 'init %d' % p.acct)
            ok(p.call('kf_my_acct') == p.acct, 'account id %d' % p.acct)
        ok(A.call('kf_my_name') == 'Kris', 'own name')
        # host: a public room of 3
        ok(A.call('kf_lobby_create', 2, 3) == 1, 'create call')
        ev, _ = A.events(0.4)
        ok('joined' in ev, 'creator joined its lobby (%r)' % ev)
        code = A.call('kf_lobby_code')
        ok(len(code) == 7 and code.isalpha() and code.isupper(), 'a 7-letter code: %s' % code)
        ok(A.call('kf_lobby_owner') == 1001, 'creator owns the lobby')
        ok(A.call('kf_lobby_get', 'kfgame') == 'kfo' and A.call('kf_lobby_get', 'kfcode') == code, 'the room is tagged (kfgame, kfcode)')
        for k, v in (('ver', '45'), ('name', 'Kris'), ('st', 'lobby'), ('np', '1'), ('mx', '3')):
            A.call('kf_lobby_set', k, v)
        # a wrong code
        ok(C.call('kf_lobby_find', 'AAAAAAB') == 1, 'find call (a code no room has)')
        ok(C.call('kf_lobby_find', 'ZZZZZZZ') == 0, 'a code past 32 bits is no code')
        ev, _ = C.events(0.4)
        ok('notfound' in ev, 'a wrong code: notfound (%r)' % ev)
        ok(C.call('kf_lobby_find', 'AB1') == 0, 'not a code: refused at once')
        # the right code
        ok(Bp.call('kf_lobby_find', code.lower()) == 1, 'find call (lower case code)')
        ev, _ = Bp.events(0.4)
        found = [e for e in ev if e.startswith('found:')]
        ok(len(found) == 1, 'the code is found once (%r)' % ev)
        f = found[0][6:].split('|') if found else ['0', '', '', '', '', '']
        ok(f[1] == '45' and f[3] == '3' and f[4] == 'lobby' and f[5] == 'Kris', 'found: version, max, state, host name (%r)' % f)
        lid = f[0]
        ok(Bp.call('kf_lobby_join_id', lid) == 1, 'join call')
        ev, _ = Bp.events(0.4)
        ok('joined' in ev, 'B joined (%r)' % ev)
        ok(Bp.call('kf_lobby_code') == code and Bp.call('kf_lobby_owner') == 1001, 'B sees the same code and owner')
        ev, _ = A.events(0.4)
        ok('member_in:1002' in ev, 'host hears B come in (%r)' % ev)
        # browse
        ok(C.call('kf_browse') == 1, 'browse call')
        ev, _ = C.events(0.4)
        ok('browse:1' in ev, 'browse finds the public room (%r)' % ev)
        info = C.call('kf_browse_info', 0).split('|')
        ok(info[1] == code and info[2] == 'Kris' and info[3] == '2' and info[4] == '3' and info[5] == '45', 'browse line: code, host, players, max, version (%r)' % info)
        # packets: B -> A (reliable), A -> B (reliable + unreliable)
        msg = json.dumps({'t': 'up', 'm': {'k': 'hi', 'name': 'Susie', 'skin': 2, 'ver': 45}})
        ok(Bp.call('kf_send', 1001, msg, 1) == 1, 'B sends to the host')
        ev, pk = A.events(0.4)
        ok((1002, msg) in pk, 'the host gets it, from B, intact (%r)' % pk[:2])
        big = json.dumps({'t': 'down', 'm': {'k': 'st', 'pl': [{'n': 'x' * 40, 'hp': i} for i in range(60)]}})
        ok(len(big) > 1200, 'a big state message')
        ok(A.call('kf_send', 1002, big, 0) == 1 and A.call('kf_send', 1002, '{"t":"down","m":{"k":"ps"}}', 0) == 1, 'host sends big (goes reliable) and small unreliable')
        ev, pk = Bp.events(0.4)
        ok((1001, big) in pk and (1001, '{"t":"down","m":{"k":"ps"}}') in pk, 'B gets both (%d packets)' % len(pk))
        # C joins by code too: the room is now full (3)
        C.call('kf_lobby_find', code)
        ev, _ = C.events(0.4)
        cf = [e for e in ev if e.startswith('found:')]
        ok(len(cf) == 1, 'C finds it')
        C.call('kf_lobby_join_id', cf[0][6:].split('|')[0] if cf else '0')
        ev, _ = C.events(0.4)
        ok('joined' in ev, 'C joined')
        ok(A.call('kf_lobby_count') == 3, '3 members')
        members = sorted(int(A.call('kf_lobby_member', i)) for i in range(3))
        ok(members == [1001, 1002, 1003], 'the members (%r)' % members)
        D = P(1004, 'Noelle')
        ok(D.call('kf_init') == 1, 'D init')
        D.call('kf_lobby_join_id', lid)
        ev, _ = D.events(0.4)
        ok('join_failed:4' in ev, 'a full room refuses D with "full" (%r)' % ev)
        # an invite (the friend clicks Join Game): a join request with the lobby
        ctl('ctl_joinreq\t1004\t%s' % lid)
        ev, _ = D.events(0.4)
        ok(('join_request:%s' % lid) in ev, 'D gets the join request (%r)' % ev)
        # the host leaves: everybody hears it, and the new owner
        A.events(0.2)
        Bp.events(0.2)
        C.events(0.2)
        ok(A.call('kf_lobby_leave') == 1, 'host leaves')
        evb, _ = Bp.events(0.4)
        evc, _ = C.events(0.4)
        ok('member_out:1001' in evb and 'member_out:1001' in evc, 'B and C hear the host leave')
        own_b = [e for e in evb if e.startswith('owner:')]
        own_c = [e for e in evc if e.startswith('owner:')]
        ok(own_b == own_c and len(own_b) == 1, 'B and C hear the same new owner once (%r %r)' % (own_b, own_c))
        ok(Bp.call('kf_lobby_owner') == C.call('kf_lobby_owner') != 1001, 'both see the same new owner')
        # a private room: its code finds nothing for a stranger
        ok(D.call('kf_lobby_create', 0, 4) == 1, 'D makes a private room')
        D.events(0.4)
        pcode = D.call('kf_lobby_code')
        X2 = P(1005, 'Berdly')
        X2.call('kf_init')
        X2.call('kf_lobby_find', pcode)
        ev, _ = X2.events(0.5)
        ok('notfound' in ev, 'a private room is not found by its code (%r)' % ev)
        # build 49: the friends list and a direct invite into D's PRIVATE room
        nf = D.call('kf_friends_refresh')
        ok(nf >= 3, 'friends list: %d friends' % nf)
        fl = [D.call('kf_friend_info', i).split('|') for i in range(int(nf))]
        ok(all(len(f) == 4 for f in fl) and any(f[0] == '1005' and f[3] == 'Berdly' and f[2] == '1' for f in fl), 'friend lines acct|state|in480|name (%r)' % fl[:3])
        ok(D.call('kf_friend_info', 999) == '', 'past the end: empty')
        X2.events(0.2)
        ok(D.call('kf_invite_user', 1005) == 1, 'D invites Berdly to the private room')
        ev, _ = X2.events(0.5)
        inv = [e for e in ev if e.startswith('invited:')]
        ok(len(inv) == 1 and inv[0].endswith('|%d' % D.acct), 'Berdly gets the invite with the room and who sent it (%r)' % ev)
        plid = inv[0][8:].split('|')[0] if inv else '0'
        ok(X2.call('kf_lobby_join_id', plid) == 1, 'Berdly joins from the invite')
        ev, _ = X2.events(0.5)
        ok('joined' in ev, 'the invited friend gets into the private room (%r)' % ev)
        ok(X2.call('kf_lobby_code') == pcode, 'the same room')
        # the overlay: off unless Steam says it is on
        ok(D.call('kf_overlay_on') == 0, 'overlay off (not launched through Steam)')
        ctl('ctl_overlay\t1')
        ok(D.call('kf_overlay_on') == 1 and D.call('kf_invite_overlay') == 1, 'overlay on: the invite dialog opens')
        for p in (A, Bp, C, D, X2):
            p.call('kf_shutdown')
            p.stop()
    finally:
        be.kill()
    print('steam dll tests: %d checks, %d failed' % (N[0], len(FAILS)))
    for f in FAILS:
        print('  -', f)
    return 0 if not FAILS else 1


if __name__ == '__main__':
    sys.exit(main())
