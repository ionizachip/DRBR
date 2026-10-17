"""Build 45: Knight Fights Online over STEAM, as far as it can be tested here: the emulated games run the real GML Steam
transport (online_steam.gml), which calls the real kf_steam code (its Linux build, one copy per game, through
external_define / external_call) - and kf_steam talks to a PRETEND Steam (mock_steam_backend.py). The same room / match
scenario as the relay test, plus Steam's own parts: 7-letter codes, the version check before joining, browse, invites, a full
room, the owner (host) changing. NOT a test of real Steam (accounts, servers, NAT, overlay)."""
import sys, os, json, time, shutil, ctypes, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from t_net_common import *

SB = '/home/claude/work/online/steam/build'
MOCKBE = '/home/claude/work/online/steam/mock/mock_steam_backend.py'
TMP = '/tmp/claude-0/kfsteam'
SOCK = TMP + '/s.sock'
os.makedirs(TMP, exist_ok=True)
T = {0: ctypes.c_double, 1: ctypes.c_char_p}


def steam_game(name, skin, acct, idx):
    """an emulated game with its own copy of kf_steam (and of the pretend steam_api)"""
    kf = '%s/kf_%d.so' % (TMP, idx)
    ms = '%s/ms_%d.so' % (TMP, idx)
    shutil.copy(SB + '/libkf_steam.so', kf)
    shutil.copy(SB + '/libmock_steam_api.so', ms)
    lib = ctypes.CDLL(kf)
    env = {'KF_STEAM_API': ms, 'KF_MOCK_SOCK': SOCK, 'KF_MOCK_ACCT': str(acct), 'KF_MOCK_NAME': name}
    sim = game(name, skin)
    table = {}

    def ext_define(s, path, fname, calltype, restype, argc, *types):
        f = getattr(lib, str(fname))
        f.restype = T[int(restype)]
        f.argtypes = [T[int(t)] for t in types]
        fid = len(table) + 1
        table[fid] = (f, str(fname))
        return fid

    def ext_call(s, fid, *args):
        f, nm = table[int(fid)]
        if nm == 'kf_init':
            os.environ.update(env)
        a = [x.encode() if isinstance(x, str) else float(x) for x in args]
        r = f(*a)
        return r.decode() if isinstance(r, bytes) else float(r)
    sim.mock('external_define', ext_define)
    sim.mock('external_call', ext_call)
    orig = sim.builtins.get('file_exists')
    sim.mock('file_exists', lambda s, p: True if 'kf_steam' in str(p) else (orig[0](s, p) if orig else False))
    for c, v in (('dll_cdecl', 0), ('dll_stdcall', 1), ('ty_real', 0), ('ty_string', 1)):
        sim.mock_value(c, v)
    sim.run('global.kfo.vis = 2;')
    sim.lib = lib
    sim.acct = acct
    return sim


def ctl(cmd):
    import socket
    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    s.connect(SOCK)
    s.sendall((cmd + '\n').encode())
    r = s.makefile().readline().strip()
    s.close()
    return r


be = subprocess.Popen([sys.executable, MOCKBE, SOCK], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
be.stdout.readline()
try:
    A, B, C = steam_game('Kris', 1, 2001, 1), steam_game('Susie', 2, 2002, 2), steam_game('Ralsei', 3, 2003, 3)
    ALL = [A, B, C]
    for s in ALL:
        ok(J(s, 'kfo_steam_ready()'), '%s: Steam ready (%s)' % (s.nm, J(s, 'kfo_steam_why()')))
    eq(J(A, 'kfo_steam_name()'), 'KRIS', 'the Steam name shows')
    # a code no room has
    C.run('kfo_steam_join_code("AAAAAAB");')
    pump([C], lambda: J(C, 'global.kfo.st') in ('failed', 'room'), 5)
    ok('No DRBR room' in J(C, 'global.kfo.err'), 'unknown code refused clearly (%s)' % J(C, 'global.kfo.err'))
    code = scenario(A, B, C, lambda s: s.run('kfo_steam_host();'), lambda s, c: s.run('kfo_steam_join_code("%s");' % c), 7)
    # ---- browse: the public room shows with its code, host, players and build
    D = steam_game('Noelle', 4, 2004, 4)
    D.run('kfo_steam_browse();')
    pump([D] + ALL, lambda: len(J(D, 'global.kfo.browse')) >= 1, 3)
    br = J(D, 'global.kfo.browse')
    ok(len(br) == 1 and br[0]['code'] == code and br[0]['ver'] == J(D, 'kfo_version()'), 'browse shows the room (%r)' % br)
    # ---- a full room (B hosts now: limit 2)
    B.run('var _s = kfo_set_clean(global.kfo.H.set); _s.maxp = 2; _s.minp = 2; _s.sps = 0; kfo_host_set(_s);')
    pump(ALL, None, 0.3)
    D.run('kfo_steam_join_code("%s");' % code)
    pump([D] + ALL, lambda: J(D, 'global.kfo.st') in ('failed', 'room'), 5)
    eq(J(D, 'global.kfo.err'), 'That room is full.', 'a full room is refused before joining')
    # ---- an older build: the lobby says version 44 -> refused before joining
    B.run('var _s = kfo_set_clean(global.kfo.H.set); _s.maxp = 8; kfo_host_set(_s);')
    pump(ALL, None, 0.3)
    B.run('kfo_sx("kf_lobby_set", "ver", "44");')
    D.run('kfo_steam_join_code("%s");' % code)
    pump([D] + ALL, lambda: J(D, 'global.kfo.st') in ('failed', 'room'), 5)
    ok('older Knight Hub build' in J(D, 'global.kfo.err'), 'a different build is refused (%s)' % J(D, 'global.kfo.err'))
    B.run('kfo_steam_lobby_meta();')
    # ---- an invite: D accepts a friend's invite (Steam's join request) and lands in the room
    lid = J(B, 'kfo_sx("kf_lobby_id")')
    ctl('ctl_joinreq\t2004\t%s' % lid)
    pump([D] + ALL, lambda: J(D, 'global.kfo.st') == 'room', 5)
    eq(J(D, 'global.kfo.st'), 'room', 'D joined through the invite')
    pump([D] + ALL, lambda: len(J(B, 'kfo_lobby_players()')) == 3, 3)
    eq(sorted(p['n'] for p in J(B, 'kfo_lobby_players()')), ['Noelle', 'Ralsei', 'Susie'], 'the host sees D come in')
    # ---- the host's game drops off Steam: Steam names the next owner, who takes the room
    ctl('ctl_drop\t2002')
    pump([C, D], lambda: J(C, 'kfo_is_host()') or J(D, 'kfo_is_host()'), 5)
    nh = C if J(C, 'kfo_is_host()') else D
    other = D if nh is C else C
    ok(J(nh, 'kfo_is_host()') and not J(other, 'kfo_is_host()'), 'exactly one new host (%s)' % nh.nm)
    pump([C, D], lambda: len(J(other, 'kfo_lobby_players()')) == 2, 3)
    eq(J(other, 'global.kfo.hostid'), J(nh, 'global.kfo.my'), 'the other player follows the new host')
finally:
    be.kill()
print('steam (GML + kf_steam + pretend Steam) tests: %d checks, %d failed' % (N[0], len(FAILS)))
for f in FAILS:
    print('  -', f)
