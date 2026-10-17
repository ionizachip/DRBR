"""Build 48: the room's CHAT over the real relay (relay.js, real sockets, the real GML of every game).
Parts: basic (3 games: host and clients send, every game the same messages in the same order, names from the host),
eight (8 games, everyone sends), guard (flood / duplicate / length / forged name / bad letters), mute, history (a late
joiner gets the recent messages; leaving and coming back: no duplicate), keys (typing: T opens, ENTER sends, ESC closes,
the match keys and the menu are blocked while typing, BACKSPACE never leaves), notices (joined / left).
The chat in a running match (and that it changes nothing in it) is t_view47's CHAT fixture."""
import sys, os, json, time, socket, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from t_net_common import *

RELAY = '/home/claude/work/online/server/relay.js'
NODE = '/opt/node22/bin/node'
STATS = {}


def free_port():
    s = socket.socket()
    s.bind(('127.0.0.1', 0))
    p = s.getsockname()[1]
    s.close()
    return p


def start_relay():
    port = free_port()
    p = subprocess.Popen([NODE, RELAY, '--port', str(port), '--host', '127.0.0.1', '--quiet'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    for _ in range(100):
        try:
            socket.create_connection(('127.0.0.1', port), timeout=0.2).close()
            return p, port
        except OSError:
            time.sleep(0.05)
    raise RuntimeError('relay did not start')


NAMES = ['Kris', 'Susie', 'Ralsei', 'Noelle', 'Berdly', 'Lancer', 'Rouxls', 'Tenna']


def room(port, n):
    sims = []
    for i in range(n):
        s = game(NAMES[i], 1 + i % 4)
        s.run('global.kfo.srv = "127.0.0.1"; global.kfo.port = %d;' % port)
        sims.append(s)
    A = sims[0]
    A.run('kfo_create();')
    ok(pump([A], lambda: J(A, 'global.kfo.st') == 'room', 5), 'the room is made')
    code = J(A, 'global.kfo.code')
    for s in sims[1:]:
        s.run('kfo_join("%s");' % code)
    ok(pump(sims, lambda: all(J(s, 'global.kfo.st') == 'room' and len(J(s, 'kfo_lobby_players()')) == n for s in sims), 10), '%d games in the room' % n)
    for s in sims:
        s.code = code
        s.run('kfo_chat_tick();')
    return sims


def chat(s):
    """the messages this game has: [name, text, sys]"""
    return [[e['n'], e['t'], e['sys']] for e in J(s, 'kfo_chat_s().l')]


def players_chat(s):
    return [[n, t] for n, t, y in chat(s) if y == 0]


def send(s, t):
    s.run('kfo_chat_s().t_send = -100000; kfo_chat_send(%s);' % json.dumps(t))


def leave_all(sims):
    for s in sims:
        try:
            s.run('kfo_leave();')
        except Exception:
            pass


def part_basic(port):
    A, B, C = room(port, 3)
    send(A, 'good luck everyone')
    send(B, 'nice dodge')
    send(C, 'kaizo next?')
    ok(pump([A, B, C], lambda: all(len(players_chat(s)) == 3 for s in (A, B, C)), 5), 'basic: every game has the 3 messages')
    l = [players_chat(s) for s in (A, B, C)]
    ok(l[0] == l[1] == l[2], 'basic: the same messages in the same order in every game (%s)' % l[0])
    ok(sorted(x[0] for x in l[0]) == ['Kris', 'Ralsei', 'Susie'], 'basic: each with its sender\'s name (%s)' % l[0])
    # host and clients alike
    ok(['Kris', 'good luck everyone'] in l[1] and ['Susie', 'nice dodge'] in l[0], 'basic: the host\'s message reaches the clients, a client\'s the host')
    leave_all([A, B, C])
    pump([A, B, C], None, 0.3)


def part_eight(port):
    sims = room(port, 8)
    for i, s in enumerate(sims):
        send(s, 'hello from %d' % (i + 1))
    ok(pump(sims, lambda: all(len(players_chat(s)) == 8 for s in sims), 8), 'eight: every game has all 8 messages')
    l = [players_chat(s) for s in sims]
    ok(all(x == l[0] for x in l), 'eight: the same order in all 8 games')
    STATS['eight'] = {'games': 8, 'messages': len(l[0])}
    leave_all(sims)
    pump(sims, None, 0.3)


def part_guard(port):
    A, B = room(port, 2)
    # flood: 7 at once - 5 pass, 2 refused (told why)
    for k in range(7):
        send(B, 'spam %d' % k)
    pump([A, B], None, 1.0)
    got = [t for n, t in players_chat(A) if t.startswith('spam')]
    refused = [t for n, t, y in chat(B) if y == 2 and 'Not sent' in t]
    ok(len(got) == 5 and len(refused) == 2, 'guard: 7 messages at once - %d reach the room, %d refused with a reason (%s)' % (len(got), len(refused), refused[:1]))
    pump([A, B], None, 5.2)
    # the same text again at once: refused
    send(B, 'same thing')
    send(B, 'same thing')
    pump([A, B], None, 0.5)
    ok(sum(1 for n, t in players_chat(A) if t == 'same thing') == 1, 'guard: the same message twice in a row - shown once')
    # a forged name / id: the host's own record wins
    B.run('kfo_chat_s().t_send = -100000; kfo_up({ k: "chat", t: "i am the host", n: "Kris", pid: 1 });')
    pump([A, B], None, 0.5)
    ok(['Susie', 'i am the host'] in players_chat(A), 'guard: a message claiming another name shows its real sender (%s)' % players_chat(A)[-1:])
    # length and letters
    B.run('kfo_chat_s().t_send = -100000; kfo_up({ k: "chat", t: "%s" });' % ('W' * 200))
    pump([A, B], None, 0.5)
    ok(any(t == 'W' * 80 for n, t in players_chat(A)), 'guard: 200 letters - cut to 80')
    send(B, 'café ♥ ok')
    pump([A, B], None, 0.5)
    ok(any(t == 'caf  ok' for n, t in players_chat(A)), 'guard: letters the font has not are left out (%s)' % players_chat(A)[-1:])
    B.run('kfo_chat_s().t_send = -100000; kfo_up({ k: "chat", t: "     " });')
    pump([A, B], None, 0.5)
    ok(all(t.strip() != '' for n, t in players_chat(A)), 'guard: an empty message is not sent')
    # the message kinds stay their own: the room's state is untouched by chat
    ok(J(A, 'global.kfo.st') == 'room' and J(B, 'global.kfo.st') == 'room', 'guard: both games still in the room')
    leave_all([A, B])
    pump([A, B], None, 0.3)


def part_mute(port):
    A, B, C = room(port, 3)
    C.run('kfo_chat_send("/mute Susie");')
    send(B, 'muted words')
    send(A, 'open words')
    pump([A, B, C], None, 1.0)
    C.run('global.LN = kfo_chat_lines(kfo_chat_s(), 400, 20, true);')
    shown = ' '.join(x['t'] for x in J(C, 'global.LN'))
    ok('muted words' not in shown and 'open words' in shown, 'mute: Ralsei muted Susie - her message not shown on Ralsei\'s screen (%s)' % shown[-80:])
    ok('muted words' in ' '.join(t for n, t in players_chat(A)), 'mute: only on Ralsei\'s screen (Kris still sees it)')
    C.run('kfo_chat_send("/unmute Susie");')
    C.run('global.LN = kfo_chat_lines(kfo_chat_s(), 400, 20, true);')
    ok('muted words' in ' '.join(x['t'] for x in J(C, 'global.LN')), 'mute: /unmute shows it again')
    leave_all([A, B, C])
    pump([A, B, C], None, 0.3)


def part_history(port):
    A, B = room(port, 2)
    for k in range(5):
        send(A if k % 2 == 0 else B, 'before %d' % k)
        pump([A, B], None, 0.3)
    C = game('Ralsei', 3)
    C.run('global.kfo.srv = "127.0.0.1"; global.kfo.port = %d;' % port)
    C.run('kfo_join("%s");' % A.code)
    ok(pump([A, B, C], lambda: J(C, 'global.kfo.st') == 'room' and len(players_chat(C)) >= 5, 6), 'history: a late joiner gets the recent messages (%d)' % len(players_chat(C)))
    ok(players_chat(C) == players_chat(A)[-len(players_chat(C)):], 'history: the same ones, in order')
    sysl = [t for n, t, y in chat(A) if y == 1]
    ok(any('Ralsei joined' in t for t in sysl), 'notices: "Ralsei joined the room." (%s)' % sysl[-2:])
    # leave and come back 5 times: never a message twice
    dup = 0
    for c in range(5):
        C.run('kfo_leave();')
        pump([A, B, C], None, 0.4)
        C.run('kfo_join("%s");' % A.code)
        pump([A, B, C], lambda: J(C, 'global.kfo.st') == 'room', 5)
        pump([A, B, C], None, 0.5)
        ids = [e['ci'] for e in J(C, 'kfo_chat_s().l')]
        if len(ids) != len(set(ids)):
            dup += 1
        txt = [t for n, t in players_chat(C)]
        if len(txt) != len(set(txt)):
            dup += 1
    ok(dup == 0, 'history: 5 leave / come back - no message shown twice (%d)' % dup)
    sysl = [t for n, t, y in chat(A) if y == 1]
    ok(any('Ralsei left' in t for t in sysl), 'notices: "Ralsei left the room."')
    leave_all([A, B, C])
    pump([A, B, C], None, 0.3)


def keys(s, held):
    held = set(held)
    s.input.pressed = held - s.input.held
    s.input.released = s.input.held - held
    s.input.held = held
    s.input.cleared = set()


def part_keys(port):
    A, B = room(port, 2)
    T_, ENT, ESC, BS = ord('T'), 13, 27, 8
    A.input.begin_frame = lambda fno: None
    keys(A, {T_})
    A.run('kfo_chat_tick();')
    ok(J(A, 'kfo_chat_typing()'), 'keys: T opens the chat')
    keys(A, set())
    A.run('kfo_chat_tick();')
    # typing: the match keys say nothing, BACKSPACE does not leave, the menu step waits
    keys(A, {BS, ord('S'), ord('Z'), ord('V'), ord('Q')})
    blocked = J(A, '[kbr_key_pressed("quit"), kbr_key_held("breath"), kbr_key_held("use"), kbr_key_pressed("souls"), kbr_key_pressed("quick")]')
    ok(not any(blocked), 'keys: while typing every match key is off (%s)' % blocked)
    keys(A, set())
    A.input.string = "hi from chat"
    A.run('keyboard_string = "hi from chat";')
    A.run('kfo_chat_tick();')
    print('  typed:', J(A, 'kfo_chat_s().buf'))
    keys(A, {ENT})
    A.run('kfo_chat_tick();')
    keys(A, set())
    ok(not J(A, 'kfo_chat_typing()'), 'keys: ENTER sends and closes')
    ok(pump([A, B], lambda: ['Kris', 'hi from chat'] in players_chat(B), 3), 'keys: the typed message reaches the other game')
    keys(A, {T_})
    A.run('kfo_chat_tick();')
    keys(A, set())
    A.run('kfo_chat_tick();')
    A.input.string = 'never sent'
    A.run('keyboard_string = "never sent";')
    A.run('kfo_chat_tick();')
    keys(A, {ESC})
    A.run('kfo_chat_tick();')
    keys(A, set())
    pump([A, B], None, 0.5)
    ok(not J(A, 'kfo_chat_typing()') and not any(t == 'never sent' for n, t in players_chat(B)), 'keys: ESC closes without sending')
    # ENTER in a match opens it; build 49: the CHAT key (\\) opens it too
    keys(A, {ENT})
    A.run('kfo_chat_tick();')
    keys(A, set())
    ok(not J(A, 'kfo_chat_typing()'), 'keys: ENTER outside a match does not open it (the menu\'s confirm key)')
    keys(A, {ESC})
    A.run('kfo_chat_tick();')
    keys(A, set())
    keys(A, {220})
    A.run('kfo_chat_tick();')
    keys(A, set())
    ok(J(A, 'kfo_chat_typing()') and J(A, 'kfo_chat_s().buf') == '', 'keys (build 49): the CHAT key (\\) opens it')
    keys(A, {ESC})
    A.run('kfo_chat_tick();')
    keys(A, set())
    # after closing, the match keys work again
    keys(A, {ord('S')})
    ok(J(A, 'kbr_key_held("breath")'), 'keys: closed - the keys are the match\'s again')
    keys(A, set())
    # the chat hidden (MATCH VIEW > CHAT): T does not open it
    A.run('global.kfo.view.chat = 0;')
    keys(A, {T_})
    A.run('kfo_chat_tick();')
    keys(A, set())
    ok(not J(A, 'kfo_chat_typing()'), 'keys: CHAT HIDDEN - T does nothing')
    A.run('global.kfo.view.chat = 1;')
    leave_all([A, B])
    pump([A, B], None, 0.3)


PARTS = {'basic': part_basic, 'eight': part_eight, 'guard': part_guard, 'mute': part_mute, 'history': part_history, 'keys': part_keys}

if __name__ == '__main__':
    t0 = time.time()
    p, port = start_relay()
    try:
        for k in (sys.argv[1:] or list(PARTS)):
            print('== part', k, flush=True)
            try:
                PARTS[k](port)
            except Exception as ex:
                import traceback
                traceback.print_exc()
                ok(False, '%s: crashed: %s' % (k, str(ex)[:300]))
    finally:
        p.kill()
    print('STATS', json.dumps(STATS))
    print('t_chat48: %d checks, %d failed, %.0fs' % (N[0], len(FAILS), time.time() - t0))
    for m in FAILS[:30]:
        print('  ', m)
    sys.exit(1 if FAILS else 0)
