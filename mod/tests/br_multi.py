"""Build 45: several emulated games in one shared battle royale, over a simulated network.

Each game is its own emulator (the real merged fight code + the real online code), with its own clock (current_time offset)
and its own built-in random seed. The games talk through Net: a model of the room's links (one-way latency, jitter, loss;
reliable messages arrive in order and late when lost, unreliable ones - SOUL positions, pings - may be dropped or come out of
order), carrying the real messages of kfo_raw (the relay protocol).

The host game starts the match (the real kfo_host_start), every game gets the same START, and from there everything runs as
in the game: ready, GO, the clock sync, the timeline, positions, status, outs, the final two, the end.

record(): every game's attack starts (cycle, knight, attack, seed, tick, the frame it really started) and, 30 / 60 / 90 frames
into each attack, the arena (box) and every bullet (object, x, y) - to compare the games."""
import sys, os, json, time, random, hashlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from br_harness import *

PROFILES = {
    'lan': (2, 0.0, 1),
    'excellent': (20, 0.0, 5),
    'normal': (60, 0.005, 10),
    'moderate': (120, 0.01, 20),
    'poor': (200, 0.03, 40),
    'extreme': (300, 0.05, 60),
}
FAST = {'p', 'ps', 'pi', 'po', 'ows', 'ow'}


class Net:
    """the room's links: client <-> host, one hop each way (a Steam peer-to-peer or LAN relay picture)"""

    def __init__(self, profile='lan', seed=7):
        self.rtt, self.loss, self.jit = PROFILES[profile]
        self.rng = random.Random(seed)
        self.t = 0.0
        self.q = {}
        self.last_rel = {}
        self.sims = {}
        self.host = 1
        self.sent = 0
        self.dropped = 0
        self.retrans = 0
        self.seq = 0
        self.down_links = set()
        self.log_start = {}

    def add(self, cid, sim):
        self.sims[cid] = sim
        self.q.setdefault(cid, [])

    def one_way(self):
        return max(0.0, self.rtt / 2.0 + self.rng.uniform(-self.jit, self.jit))

    def push(self, to, obj, reliable, frm):
        if to not in self.q:
            return
        if (frm, to) in self.down_links or (to, frm) in self.down_links:
            self.dropped += 1
            return
        self.sent += 1
        txt = json.dumps(obj)
        if to == frm:
            # a game's message to itself (never happens through the relay; kept for completeness)
            self.q[to].append((self.t, self.seq, txt))
        elif reliable:
            d = self.t + self.one_way()
            if self.rng.random() < self.loss:
                # lost on the wire: resent after a timeout (and everything behind it waits: in-order delivery)
                d += 200 + self.rtt
                self.retrans += 1
            d = max(d, self.last_rel.get((frm, to), 0.0))
            self.last_rel[(frm, to)] = d
            self.q[to].append((d, self.seq, txt))
        else:
            if self.rng.random() < self.loss:
                self.dropped += 1
                return
            self.q[to].append((self.t + self.one_way(), self.seq, txt))
        self.seq += 1

    def send(self, cid, m):
        t = m.get('t')
        if t == 'ping':
            self.push(cid, {'t': 'pong'}, True, cid)
        elif t == 'up':
            inner = m.get('m') or {}
            rel = inner.get('k') not in FAST
            self.push(self.host, {'t': 'up', 'from': cid, 'm': inner}, rel, cid)
        elif t == 'down':
            inner = m.get('m') or {}
            rel = inner.get('k') not in FAST
            to = m.get('to', 0)
            if to == 0:
                for c in self.sims:
                    if c != cid:
                        self.push(c, {'t': 'down', 'm': inner}, rel, cid)
            else:
                self.push(to, {'t': 'down', 'm': inner}, rel, cid)

    def due(self, cid):
        q = self.q[cid]
        if not q:
            return None
        q.sort()
        if q[0][0] <= self.t:
            return q.pop(0)[2]
        return None


def install(sim, net, cid):
    """the mocks that put one emulated game on the Net"""
    sim.cid = cid
    sim.kb = set()
    sim.start_text = ''

    def raw(s, m):
        net.send(cid, s.py(m))
        return True
    sim.mock('kfo_raw', raw)

    def nxt(s):
        t = net.due(cid)
        return t if t is not None else ''
    sim.mock('test_net_next', nxt)
    sim.mock('test_start_text', lambda s: s.start_text)
    sim.mock('network_destroy', 0)
    for k in ('left', 'right', 'up', 'down'):
        sim.mock(k + '_h', (lambda kk: (lambda s: 1 if kk in s.kb else 0))(k))
        sim.mock(k + '_p', (lambda kk: (lambda s: 1 if ('p_' + kk) in s.kb else 0))(k))
    for b, nm in ((1, 'z'), (2, 'x'), (3, 'c')):
        sim.mock('button%d_h' % b, (lambda kk: (lambda s: 1 if kk in s.kb else 0))(nm))
        sim.mock('button%d_p' % b, (lambda kk: (lambda s: 1 if ('p_' + kk) in s.kb else 0))(nm))
    sim.define_script('test_net', 'function test_net_pump() { var _t = test_net_next(); var _n = 0; '
                      'while (is_string(_t) && _t != "" && _n < 400) { if (is_struct(global.kfo)) global.kfo.t_rx = current_time; kfo_line(_t); _t = test_net_next(); _n++; } return _n; }')


ROOM = ('global.is_console = 0; kfo_get(); var _o = global.kfo; _o.name = "%s"; _o.skin = %d; _o.mode = "direct"; _o.sock = 1; _o.st = "room";'
        '_o.my = %d; _o.hostid = 1; _o.code = "TESTS"; _o.members = %s; _o.t_rx = current_time;')


def members_gml(n, names):
    return '[' + ', '.join('{ pid: %d, name: "%s" }' % (i + 1, names[i]) for i in range(n)) + ']'


def make_room(n=3, profile='lan', seed=4242, setx='', open_ok=0, kn=(0, 1, 2, 3, 4, 5), ct_offsets=None, rng_seeds=None, bots=0, netseed=7,
              stub=None, world=False):
    """n games in one room; game 1 hosts and starts the match. Returns (net, [sims]) or raises."""
    names = ['Kris', 'Susie', 'Ralsei', 'Noelle', 'Berdly', 'Lancer', 'Rouxls', 'Tenna'][:n]
    net = Net(profile, netseed)
    ct_offsets = ct_offsets or [0, 7777, -3333, 123456, 500, 999, 31337, 42][:n]
    rng_seeds = rng_seeds or [11, 22, 33, 44, 55, 66, 77, 88][:n]
    host = KN[OKREG[open_ok if open_ok in kn else kn[0]]]
    sims = []
    # the host: its room (the others already in it and READY), its START with the test seed
    ex = (ROOM % (names[0], 1, 1, members_gml(n, names)) +
          'var _s = kfo_set_clean({ kn: %s, open: %d, bots: %d }); %s _o.set = kfo_set_clean(_s);'
          'kfo_host_begin("TESTS", false); var _H = _o.H;'
          'for (var _i = 2; _i <= %d; _i++) { var _p = kfo_host_player_new(_i, global.TNAMES[_i - 1], 1 + ((_i - 1) mod 4), 0); _p.hi = 1; _p.rd = 1; array_push(_H.pl, _p); }'
          'global.kfo_test_seed = %d; global.BRWHY = kfo_host_start();'
          'var _q = _o.lq; var _st = undefined; var _keep = [];'
          'for (var _i = 0; _i < array_length(_q); _i++) { if (!_q[_i].up && kfo_js(_q[_i].m, "k", "") == "start") _st = _q[_i].m; else array_push(_keep, _q[_i]); }'
          '_o.lq = _keep; global.kfo.M = kfo_match_new(_st); global.kfo.M.launched = true;') % (json.dumps(list(kn)), open_ok, bots, setx, n, seed)

    def pre_host(s):
        jv_assets(s)
        s.ct_offset = ct_offsets[0]
        install(s, net, 1)
        s.run('global.TNAMES = %s;' % json.dumps(names))
    sim, e = lu_battle(host, party=(1,), combo=3, extra_cfg=ex, world=world, pre=pre_host)
    if e is not None:
        raise RuntimeError('host setup: %r' % (e,))
    net.add(1, sim)
    sims.append(sim)
    # the START the host sent to the others (through kfo_raw -> Net)
    start = None
    for cid, q in net.q.items():
        pass
    # it was sent before the others were added: rebuild it from the host's own copy
    start_txt = json.dumps(sim.py(sim.eval('global.kfo.M.players')))
    st = {'k': 'start', 'mid': sim.eval('global.kfo.H.mid'), 'seed': sim.eval('global.kfo.H.seed'), 'set': sim.py(sim.eval('global.kfo.H.mset')),
          'players': sim.py(sim.eval('global.kfo.M.players')), 'prac': 0, 'ver': sim.eval('kfo_version()')}
    for i in range(2, n + 1):
        exc = (ROOM % (names[i - 1], 1 if os.environ.get('SAMESKIN') else 1 + ((i - 1) % 4), i, members_gml(n, names)) +
               'global.kfo.M = kfo_match_new(json_parse(test_start_text())); global.kfo.M.launched = true;')

        def pre_c(s, i=i):
            jv_assets(s)
            s.ct_offset = ct_offsets[i - 1]
            install(s, net, i)
            s.start_text = json.dumps(st)
        # SAMESKIN=1: every game plays as Kris (a check that differences come from the players' own characters)
        csk = 1 if os.environ.get('SAMESKIN') else 1 + ((i - 1) % 4)
        c, e = lu_battle(host, party=(csk,), combo=3, extra_cfg=exc, world=world, pre=pre_c)
        if e is not None:
            raise RuntimeError('client %d setup: %r' % (i, e))
        net.add(i, c)
        sims.append(c)
    for i, s in enumerate(sims):
        s.rng.seed(rng_seeds[i])
        preload_base(s)
        s.premocked = premock(s)
        s.define_event('obj_battlecontroller', 'Step', 0, stub or BR_STUB)
        s._snapauto = False
        s.retrylog = []
    return net, sims


# ---------- recording what every game does ----------
SNAP = ('var _M = global.kfo.M; var _L = []; with (obj_bulletparent) { if (!(variable_instance_exists(id, "kbr") && kbr != 0))'
        ' array_push(_L, object_get_name(object_index) + "@" + string(round(x)) + "," + string(round(y))); }'
        'var _bx = ""; with (obj_growtangle) _bx += string(round(x)) + "," + string(round(y)) + "," + string(image_xscale) + "," + string(image_yscale) + ";";'
        'var _kx = ""; with (obj_knight_enemy) _kx += string(round(x)) + "," + string(round(y)) + ";"; with (obj_knight_twin) _kx += "T" + string(round(x)) + "," + string(round(y)) + ";";'
        'global.SNAPV = { n: array_length(_L), box: _bx, kx: _kx, rn: global.kbr_det.n, l: _L, hx: (instance_exists(obj_heart) ? round(obj_heart.x) : -1), hy: (instance_exists(obj_heart) ? round(obj_heart.y) : -1) };')


def snapshot(sim):
    sim.run(SNAP)
    v = sim.py(sim.eval('global.SNAPV'))
    l = sorted(v['l'])
    v['h'] = hashlib.md5(('|'.join(l)).encode()).hexdigest()[:12]
    v['l'] = l if os.environ.get('BR_KEEPL') else None
    return v


STATE = ('var _M = global.kfo.M; var _R = _M.R; global.ST = { ph: _R.ph, k: _R.k, af: _R.af, arm: _R.arm_k, ns: array_length(_R.started),'
         ' last: (array_length(_R.started) > 0) ? _R.started[array_length(_R.started) - 1] : -1, tsp: _R.t_spawn, sk: _R.skipped, go: _M.go,'
         ' out: _M.out, ended: _M.ended, act: (is_struct(global.knight_lu) && global.knight_lu.ready) ? global.knight_lu.ks[global.knight_lu.act] : -1,'
         ' now: kbr_now(), rs: _M.resyncs, t0ms: _M.t0ms, ct: current_time };')


def state(sim):
    sim.run(STATE)
    return sim.py(sim.eval('global.ST'))


def inputs(sim, mode, idx, af, ph):
    """the SOUL's keys for this frame: 'same' - every game the same, by the attack's own frame; 'diff' - each game its own"""
    sim.kb = set()
    if ph != 'run':
        return
    if mode == 'none':
        return
    shift = 0 if mode == 'same' else idx * 23
    p = ((af + shift) // 25) % 6
    keys = [('right',), ('up',), ('left',), ('down',), ('right', 'down'), ()][p]
    sim.kb = set(keys)


def run(net, sims, frames, mode='same', on_frame=None, wall=600, stall=None):
    """step every game frame by frame (each game: its messages, its keys, one frame). Returns the record."""
    rec = {i + 1: {'starts': [], 'snaps': {}, 'errors': []} for i in range(len(sims))}
    prev = [state(s) for s in sims]
    t0 = time.time()
    for f in range(frames):
        net.t += 1000.0 / 30.0
        for i, s in enumerate(sims):
            cid = i + 1
            if rec[cid]['errors']:
                continue
            if stall and stall(cid, f):
                # this game froze (a lag spike): its time runs on, no frame
                s.frame_no += 1
                continue
            try:
                s.run('test_net_pump();')
            except Exception as ex:
                rec[cid]['errors'].append([f, 'net', str(ex)[:300]])
                continue
            inputs(s, mode, i, prev[i]['af'], prev[i]['ph'])
            err = step(s, 1)
            if err is not None:
                rec[cid]['errors'].append([f, prev[i]['ph'], err[:400]])
                continue
            st = state(s)
            if st['last'] >= 0 and (st['ns'] > prev[i]['ns'] or st['last'] != prev[i]['last']):  # the game keeps only its last 64 starts
                c = s.py(s.eval('kbr_tl_get(global.kfo.M.tl, %d)' % st['last']))
                rec[cid]['starts'].append({'k': st['last'], 'ok': c['ok'], 'ai': c['ai'], 'seed': c['seed'], 't0': c['t0'], 'tw': c['twin'], 'hy': c['hyper'],
                                           'st': c['st'], 'sd': c['sd'], 'ft': c['ft'], 'tsp': round(st['tsp'], 3), 'net_ms': round(net.t, 1), 'act': st['act'],
                                           'prev_act': prev[i]['act']})
            if st['ph'] == 'run' and st['af'] in (30, 60, 90):
                rec[cid]['snaps']['%d:%d' % (st['k'], st['af'])] = snapshot(s)
            prev[i] = st
        if on_frame:
            on_frame(f, sims, prev)
        if time.time() - t0 > wall:
            rec['wall_hit'] = f
            break
    rec['frames'] = f + 1
    rec['net'] = {'sent': net.sent, 'dropped': net.dropped, 'retrans': net.retrans}
    return rec


def compare(rec, n):
    """logical agreement (knight, attack, seed, start tick, switch sequence), presentation offsets, arena and bullets"""
    out = {'cycles_all': 0, 'logic_bad': [], 'onset_ms': [], 'arena_bad': [], 'bul_same': 0, 'bul_diff': 0, 'bul_diff_list': [], 'dupes': 0}
    by = {}
    for cid in range(1, n + 1):
        ks = [s['k'] for s in rec[cid]['starts']]
        out['dupes'] += len(ks) - len(set(ks))
        for s in rec[cid]['starts']:
            by.setdefault(s['k'], {})[cid] = s
    for k in sorted(by):
        d = by[k]
        if len(d) < n:
            continue
        out['cycles_all'] += 1
        ref = d[1]
        for cid in range(2, n + 1):
            o = d[cid]
            for fld in ('ok', 'ai', 'seed', 't0', 'tw', 'hy', 'st', 'sd', 'ft', 'act', 'prev_act'):
                if o[fld] != ref[fld]:
                    out['logic_bad'].append([k, cid, fld, ref[fld], o[fld]])
        tms = [d[c]['net_ms'] for c in d]
        out['onset_ms'].append(max(tms) - min(tms))
        for af in (30, 60, 90):
            key = '%d:%d' % (k, af)
            sn = [rec[c]['snaps'].get(key) for c in range(1, n + 1)]
            if any(x is None for x in sn):
                continue
            if any(x['box'] != sn[0]['box'] for x in sn):
                out['arena_bad'].append([key, [x['box'] for x in sn]])
            if all(x['h'] == sn[0]['h'] for x in sn):
                out['bul_same'] += 1
            else:
                out['bul_diff'] += 1
                out['bul_diff_list'].append([key, [x['n'] for x in sn], [x['rn'] for x in sn], [x['h'] for x in sn], [x['kx'] for x in sn], [(x['hx'], x['hy']) for x in sn]])
    o = sorted(out['onset_ms'])
    out['onset_p95'] = o[int(len(o) * 0.95) - 1] if o else None
    out['onset_max'] = o[-1] if o else None
    return out
