"""Build 45 (rewritten from build 43): Knight Fights Online over the RELAY (real sockets, the real relay.js, the real GML: the
Async Networking event, line splitting, JSON). Three emulated games: create / join by code, a wrong code, the lobby, the
settings, the start and the shared timeline, outs, places, results, the next match, the host leaving (takeover), a full room,
the server going away. (The battle royale itself is tested by t_br_single / t_br_multi.)"""
import sys, os, json, time, socket, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from t_net_common import *

RELAY = '/home/claude/work/online/server/relay.js'
NODE = '/opt/node22/bin/node'


def free_port():
    s = socket.socket(); s.bind(('127.0.0.1', 0)); p = s.getsockname()[1]; s.close(); return p


def start_relay(port):
    p = subprocess.Popen([NODE, RELAY, '--port', str(port), '--host', '127.0.0.1', '--quiet'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    for _ in range(100):
        try:
            socket.create_connection(('127.0.0.1', port), timeout=0.2).close()
            return p
        except OSError:
            time.sleep(0.05)
    raise RuntimeError('relay did not start')


port = free_port()
relay = start_relay(port)
try:
    def mk(name, skin):
        s = game(name, skin)
        s.run('global.kfo.srv = "127.0.0.1"; global.kfo.port = %d;' % port)
        return s
    A, B, C = mk('Kris', 1), mk('Susie', 2), mk('Ralsei', 3)
    ALL = [A, B, C]
    # ---- a wrong server address fails cleanly
    X = mk('Nobody', 1)
    X.run('global.kfo.port = %d; kfo_create();' % free_port())
    eq(J(X, 'global.kfo.st'), 'connecting', 'connecting state')
    pump([X], lambda: J(X, 'global.kfo.st') != 'connecting', 5)
    eq(J(X, 'global.kfo.st'), 'failed', 'no server: failed')
    ok('Could not connect' in J(X, 'global.kfo.err'), 'no server: says so (%s)' % J(X, 'global.kfo.err'))
    # ---- a wrong code
    C.run('kfo_join("ZZZZZ");')
    pump([C], lambda: J(C, 'global.kfo.st') in ('failed', 'room'), 5)
    eq(J(C, 'global.kfo.err'), 'There is no room with that code.', 'wrong code refused with a clear text')
    code = scenario(A, B, C, lambda s: s.run('kfo_create();'), lambda s, c: s.run('kfo_join("%s");' % c), 5)
    # ---- a full room
    B.run('var _s = kfo_set_clean(global.kfo.H.set); _s.maxp = 2; _s.minp = 2; _s.sps = 0; kfo_host_set(_s);')
    pump(ALL, None, 0.2)
    A.run('kfo_join("%s");' % code)
    pump(ALL, lambda: J(A, 'global.kfo.st') in ('failed', 'room'), 5)
    eq(J(A, 'global.kfo.err'), 'That room is full.', 'full room refused')
    # ---- the server goes away
    relay.kill(); relay.wait()
    pump(ALL, lambda: J(C, 'global.kfo.st') == 'failed' and J(B, 'global.kfo.st') == 'failed', 5)
    eq(J(C, 'global.kfo.st'), 'failed', 'C notices the server is gone')
    ok(J(C, 'global.kfo.err') != '', 'and says why (%s)' % J(C, 'global.kfo.err'))
finally:
    try:
        relay.kill()
    except Exception:
        pass
print('online net (relay) tests: %d checks, %d failed' % (N[0], len(FAILS)))
for f in FAILS:
    print('  -', f)
