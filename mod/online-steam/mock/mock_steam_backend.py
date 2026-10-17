"""A pretend Steam for the kf_steam tests (build 45). NOT Steam: lobbies, lobby data, lobby lists, members, owners, invites
and peer-to-peer packets as the Steamworks API describes them, kept in this process; each test game (one process with
kf_steam + mock_steam_api) is one user connected over a UNIX socket. Usage: python3 mock_steam_backend.py <socket path>"""
import os, sys, socket, threading, random

LOBBY_HIGH = 0x0186000000000000
IND = 76561197960265728


class World:
    def __init__(self, seed=5):
        self.lock = threading.RLock()
        self.rng = random.Random(seed)
        self.users = {}      # sid -> user
        self.lobbies = {}    # lid -> lobby
        self.calls = 1000
        self.log = []
        self.overlay = False

    def user(self, sid):
        return self.users.get(sid)


class User:
    def __init__(self, sid, name, app):
        self.sid, self.name, self.app = sid, name, app
        self.cbs = []
        self.results = {}
        self.filters = []
        self.listres = []
        self.packets = []        # (from, hex)
        self.held = {}           # from -> [hex] (session not accepted yet)
        self.accepted = set()
        self.requested = set()
        self.online = True


class Lobby:
    def __init__(self, lid, owner, typ, mx):
        self.lid, self.owner, self.typ, self.max = lid, owner, typ, mx
        self.members = [owner]
        self.data = {}
        self.joinable = True
        self.invited = set()


W = World()


def cb(u, *f):
    u.cbs.append('\t'.join(str(x) for x in f))


def new_call(u, result):
    W.calls += 1
    c = W.calls
    u.results[c] = result
    cbid = int(result.split('\t')[0])
    cb(u, 703, c, cbid, 0)
    return c


def leave(u, lid):
    lb = W.lobbies.get(lid)
    if not lb or u.sid not in lb.members:
        return
    lb.members.remove(u.sid)
    for m in lb.members:
        cb(W.users[m], 506, lid, u.sid, 2)
    if not lb.members:
        del W.lobbies[lid]
        return
    if lb.owner == u.sid:
        lb.owner = lb.members[0]


def handle(u, parts):
    op = parts[0]
    if op == 'bye':
        return 'ok'
    if op == 'frame':
        out = u.cbs
        u.cbs = []
        return str(len(out)) + ('\n' + '\n'.join(out) if out else '')
    if op == 'result':
        r = u.results.pop(int(parts[1]), None)
        return r if r else 'none'
    if op == 'name':
        o = W.users.get(int(parts[1]))
        return o.name if o else ''
    if op == 'invite_dialog':
        W.log.append(('invite_dialog', u.sid, int(parts[1])))
        return '1'
    if op == 'fcount':
        return str(len([x for x in W.users if x != u.sid]))
    if op == 'fget':
        l = sorted(x for x in W.users if x != u.sid)
        i = int(parts[1])
        return str(l[i] if 0 <= i < len(l) else 0)
    if op == 'fstate':
        o = W.users.get(int(parts[1]))
        return str(getattr(o, 'pstate', 1) if (o and o.online) else 0)
    if op == 'fgame':
        o = W.users.get(int(parts[1]))
        return str(getattr(o, 'game', 480)) if (o and o.online) else '0'
    if op == 'invite':
        lid, who = int(parts[1]), int(parts[2])
        lb = W.lobbies.get(lid)
        o = W.users.get(who)
        if not lb or u.sid not in lb.members or not o:
            return '0'
        lb.invited.add(who)
        W.log.append(('invite', u.sid, who, lid))
        cb(o, 503, u.sid, lid)
        return '1'
    if op == 'overlay':
        return '1' if W.overlay else '0'
    if op == 'create':
        typ, mx = int(parts[1]), int(parts[2])
        lid = LOBBY_HIGH | W.rng.randrange(1, 2 ** 32)
        lb = Lobby(lid, u.sid, typ, mx)
        W.lobbies[lid] = lb
        c = new_call(u, '513\t1\t%d' % lid)
        cb(u, 504, lid, 1)
        return str(c)
    if op == 'join':
        lid = int(parts[1])
        lb = W.lobbies.get(lid)
        if not lb:
            return str(new_call(u, '504\t%d\t2' % lid))
        if len(lb.members) >= lb.max:
            return str(new_call(u, '504\t%d\t4' % lid))
        if lb.typ == 0 and u.sid not in lb.invited:
            return str(new_call(u, '504\t%d\t3' % lid))
        if not lb.joinable:
            return str(new_call(u, '504\t%d\t3' % lid))
        if u.sid not in lb.members:
            lb.members.append(u.sid)
            for m in lb.members:
                if m != u.sid:
                    cb(W.users[m], 506, lid, u.sid, 1)
        c = new_call(u, '504\t%d\t1' % lid)
        cb(u, 504, lid, 1)
        return str(c)
    if op == 'leave':
        leave(u, int(parts[1]))
        return 'ok'
    if op == 'owner':
        lb = W.lobbies.get(int(parts[1]))
        return str(lb.owner if lb else 0)
    if op == 'count':
        lb = W.lobbies.get(int(parts[1]))
        return str(len(lb.members) if lb else 0)
    if op == 'member':
        lb = W.lobbies.get(int(parts[1]))
        i = int(parts[2])
        return str(lb.members[i] if lb and 0 <= i < len(lb.members) else 0)
    if op == 'setdata':
        lb = W.lobbies.get(int(parts[1]))
        if not lb or lb.owner != u.sid:
            return '0'
        lb.data[parts[2]] = parts[3] if len(parts) > 3 else ''
        for m in lb.members:
            cb(W.users[m], 505, lb.lid, lb.lid, 1)
        return '1'
    if op == 'getdata':
        lb = W.lobbies.get(int(parts[1]))
        return lb.data.get(parts[2], '') if lb else ''
    if op == 'joinable':
        lb = W.lobbies.get(int(parts[1]))
        if lb and lb.owner == u.sid:
            lb.joinable = parts[2] == '1'
            return '1'
        return '0'
    if op == 'limit':
        lb = W.lobbies.get(int(parts[1]))
        if lb and lb.owner == u.sid:
            lb.max = int(parts[2])
            return '1'
        return '0'
    if op == 'reqdata':
        lid = int(parts[1])
        lb = W.lobbies.get(lid)
        # friends-only / private lobbies of strangers answer nothing useful; here every user counts as a friend
        cb(u, 505, lid, lid, 1 if (lb and lb.typ != 0) else 0)
        return '1'
    if op == 'filter':
        u.filters.append((parts[1], parts[2], int(parts[3])))
        return 'ok'
    if op == 'countfilter':
        return 'ok'
    if op == 'list':
        res = []
        for lb in W.lobbies.values():
            if lb.typ not in (2, 3):
                continue
            if all(lb.data.get(k, '') == v for k, v, cmpv in u.filters if cmpv == 0):
                res.append(lb.lid)
        u.filters = []
        u.listres = res
        return str(new_call(u, '510\t%d' % len(res)))
    if op == 'listget':
        i = int(parts[1])
        return str(u.listres[i] if 0 <= i < len(u.listres) else 0)
    if op == 'send':
        to, typ, hx = int(parts[1]), int(parts[2]), parts[4] if len(parts) > 4 else ''
        t = W.users.get(to)
        if not t or not t.online:
            return '0'
        if u.sid in t.accepted:
            t.packets.append((u.sid, hx))
        else:
            t.held.setdefault(u.sid, []).append(hx)
            if u.sid not in t.requested:
                t.requested.add(u.sid)
                cb(t, 1202, u.sid)
        # once a session exists both ways count as connected (the sender accepted by sending)
        u.accepted.add(to)
        return '1'
    if op == 'avail':
        return str(len(bytes.fromhex(u.packets[0][1]))) if u.packets else '-1'
    if op == 'read':
        if not u.packets:
            return 'none'
        f, hx = u.packets.pop(0)
        return '%d\t%s' % (f, hx)
    if op == 'accept':
        who = int(parts[1])
        u.accepted.add(who)
        for hx in u.held.pop(who, []):
            u.packets.append((who, hx))
        return '1'
    if op == 'closep2p':
        return '1'
    # ---- the test's own commands
    if op == 'ctl_joinreq':
        t = W.users.get(IND + int(parts[1]))
        if t:
            cb(t, 333, int(parts[2]), 0)
        return 'ok'
    if op == 'ctl_invite':
        lb = W.lobbies.get(int(parts[1]))
        if lb:
            lb.invited.add(IND + int(parts[2]))
        return 'ok'
    if op == 'ctl_drop':
        t = W.users.get(IND + int(parts[1]))
        if t:
            t.online = False
            for lid in [l.lid for l in W.lobbies.values() if t.sid in l.members]:
                leave(t, lid)
        return 'ok'
    if op == 'ctl_online':
        t = W.users.get(IND + int(parts[1]))
        if t:
            t.online = True
        return 'ok'
    if op == 'ctl_lobbies':
        return ';'.join('%d:%d:%s:%s' % (l.lid, l.owner, ','.join(str(m - IND) for m in l.members), l.data.get('kfcode', '')) for l in W.lobbies.values())
    if op == 'ctl_overlay':
        W.overlay = parts[1] == '1'
        return 'ok'
    if op == 'ctl_log':
        return repr(W.log)
    return 'unknown'


def serve(conn):
    buf = b''
    u = None
    while True:
        try:
            d = conn.recv(65536)
        except OSError:
            break
        if not d:
            break
        buf += d
        while b'\n' in buf:
            ln, buf = buf.split(b'\n', 1)
            parts = ln.decode('utf8', 'replace').split('\t')
            with W.lock:
                if parts[0] == 'hello':
                    sid = IND + int(parts[1])
                    u = User(sid, parts[2], parts[3] if len(parts) > 3 else '0')
                    W.users[sid] = u
                    r = 'ok'
                elif u is None and not parts[0].startswith('ctl_'):
                    r = 'nohello'
                else:
                    r = handle(u, parts)
            conn.sendall((r + '\n').encode('utf8'))
    if u is not None:
        with W.lock:
            u.online = False
            for lid in [l.lid for l in W.lobbies.values() if u.sid in l.members]:
                leave(u, lid)


def main(path):
    if os.path.exists(path):
        os.unlink(path)
    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    s.bind(path)
    s.listen(64)
    print('mock steam ready', flush=True)
    while True:
        c, _ = s.accept()
        threading.Thread(target=serve, args=(c,), daemon=True).start()


if __name__ == '__main__':
    main(sys.argv[1])
