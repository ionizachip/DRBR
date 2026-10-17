"""Real buffers and plain TCP client sockets, so GML netcode can be run against a real server (Knight Hub build 43).

buffer_*  : a bytearray per buffer (fixed / grow / wrap) with a read/write position, little-endian numbers.
network_* : client TCP sockets (network_create_socket(network_socket_tcp), network_connect_raw / _async, network_send_raw,
            network_destroy, network_set_config). Connects, incoming data and disconnects are queued and delivered once per
            frame (after End Step) as the Async - Networking event (Other 68) to every instance that has one, with
            async_load set to a ds_map shaped like GameMaker's: type, id, socket, buffer, size, succeeded, ip, port.
            The data buffer and the map exist only during the event, as in GameMaker.
"""
import errno
import os
import select
import socket
import struct

from .errors import GMError
from .registry import builtin, const
from .values import GMHandle

const(network_socket_tcp=0, network_socket_udp=1, network_socket_bluetooth=2, network_socket_ws=6, network_socket_wss=7,
      network_type_connect=1, network_type_disconnect=2, network_type_data=3, network_type_non_blocking_connect=4,
      network_config_connect_timeout=0, network_config_use_non_blocking_socket=1, network_config_enable_reliable_udp=2,
      network_config_disable_reliable_udp=3, network_config_avoid_time_wait=4, network_config_websocket_protocol=5,
      buffer_seek_start=0, buffer_seek_relative=1, buffer_seek_end=2, buffer_vbuffer=4, buffer_network=5)

_FMT = {1: '<B', 2: '<b', 3: '<H', 4: '<h', 5: '<I', 6: '<i', 7: '<e', 8: '<f', 9: '<d', 10: '<B', 12: '<Q'}


class Buf:
    __slots__ = ('data', 'kind', 'pos')

    def __init__(self, size, kind):
        self.data = bytearray(max(0, int(size)))
        self.kind = int(kind)
        self.pos = 0


# Handle mode (GMLSIM_NET_HANDLES or sim.net_handles): 0 = plain numbers (default); 1 = buffers and sockets are typed
# handles everywhere, async_load included; 2 = handles, but async_load gives the socket as a plain number and real()
# refuses handles. Netcode has to work in all three, since which one a given GameMaker runtime does is not known here.
def _hmode(sim):
    m = getattr(sim, 'net_handles', None)
    if m is None:
        try:
            m = int(os.environ.get('GMLSIM_NET_HANDLES', '0') or 0)
        except ValueError:
            m = 0
        sim.net_handles = m
    return m


def _ix(i):
    if i.__class__ is GMHandle:
        return i.index
    return int(i)


def _bufs(sim):
    b = getattr(sim, '_net_bufs', None)
    if b is None:
        b = sim._net_bufs = {}
        sim._net_next_buf = 0
    return b


def _buf(sim, i, fn):
    try:
        if i.__class__ is GMHandle and i.kind != 'buffer':
            raise KeyError(i)
        return _bufs(sim)[_ix(i)]
    except (KeyError, TypeError, ValueError):
        raise GMError('%s(): buffer %r does not exist' % (fn, i), 'buffer')


def _new_buf(sim, size, kind):
    bufs = _bufs(sim)
    i = sim._net_next_buf
    sim._net_next_buf += 1
    bufs[i] = Buf(size, kind)
    return i


def _bh(sim, i):
    """the GML value for buffer i"""
    return GMHandle('buffer', i) if _hmode(sim) else i


def _ensure(b, end, fn):
    """room for writing up to byte `end`: grow buffers grow, fixed ones fail like GameMaker's do"""
    if end <= len(b.data):
        return True
    if b.kind == 1:
        b.data.extend(bytes(end - len(b.data)))
        return True
    return False


def _encode(t, v):
    t = int(t)
    if t == 11:
        return (v if isinstance(v, str) else str(v)).encode('utf8') + b'\0'
    if t == 13:
        return (v if isinstance(v, str) else str(v)).encode('utf8')
    if t not in _FMT:
        raise GMError('buffer: unknown data type %r' % (t,), 'buffer')
    if t in (1, 2, 3, 4, 5, 6, 10, 12):
        v = int(v)
        if t == 10:
            v = 1 if v else 0
        bits = {1: 8, 2: 8, 3: 16, 4: 16, 5: 32, 6: 32, 10: 8, 12: 64}[t]
        if t in (2, 4, 6):
            v = ((v + (1 << (bits - 1))) % (1 << bits)) - (1 << (bits - 1))
        else:
            v %= (1 << bits)
    else:
        v = float(v)
    return struct.pack(_FMT[t], v)


def _decode(b, t, pos, fn):
    t = int(t)
    if t in (11, 13):
        end = b.data.find(b'\0', pos)
        if end < 0:
            end = len(b.data)
        s = bytes(b.data[pos:end]).decode('utf8', errors='replace')
        return s, (end + 1 if (t == 11 and end < len(b.data)) else end)
    if t not in _FMT:
        raise GMError('%s(): unknown data type %r' % (fn, t), 'buffer')
    n = struct.calcsize(_FMT[t])
    if pos + n > len(b.data):
        raise GMError('%s(): read past the end of the buffer (pos %d, size %d)' % (fn, pos, len(b.data)), 'buffer')
    v = struct.unpack_from(_FMT[t], b.data, pos)[0]
    if t == 10:
        v = 1 if v else 0
    return (float(v) if t in (7, 8, 9) else v), pos + n


@builtin()
def buffer_create(sim, size, kind, align=1):
    return _bh(sim, _new_buf(sim, size, kind))


@builtin()
def buffer_exists(sim, i):
    if i.__class__ is GMHandle:
        return i.kind == 'buffer' and i.index in _bufs(sim)
    return i.__class__ in (int, float) and int(i) in _bufs(sim)


@builtin()
def buffer_delete(sim, i):
    _buf(sim, i, 'buffer_delete')
    del _bufs(sim)[_ix(i)]
    return 0


@builtin()
def buffer_get_size(sim, i):
    return len(_buf(sim, i, 'buffer_get_size').data)


@builtin()
def buffer_tell(sim, i):
    return _buf(sim, i, 'buffer_tell').pos


@builtin()
def buffer_seek(sim, i, base, off):
    b = _buf(sim, i, 'buffer_seek')
    base, off = int(base), int(off)
    p = off if base == 0 else (b.pos + off if base == 1 else len(b.data) + off)
    b.pos = max(0, min(len(b.data), p))
    return 0


@builtin()
def buffer_resize(sim, i, size):
    b = _buf(sim, i, 'buffer_resize')
    size = max(0, int(size))
    if size < len(b.data):
        del b.data[size:]
    else:
        b.data.extend(bytes(size - len(b.data)))
    b.pos = min(b.pos, size)
    return 0


@builtin()
def buffer_write(sim, i, t, v):
    b = _buf(sim, i, 'buffer_write')
    raw = _encode(t, v)
    if b.kind == 2 and len(b.data) > 0:
        for byte in raw:
            b.data[b.pos % len(b.data)] = byte
            b.pos = (b.pos + 1) % len(b.data)
        return 0
    if not _ensure(b, b.pos + len(raw), 'buffer_write'):
        raise GMError('buffer_write(): %d bytes do not fit at %d in a fixed buffer of %d' % (len(raw), b.pos, len(b.data)), 'buffer')
    b.data[b.pos:b.pos + len(raw)] = raw
    b.pos += len(raw)
    return 0


@builtin()
def buffer_read(sim, i, t):
    b = _buf(sim, i, 'buffer_read')
    v, b.pos = _decode(b, t, b.pos, 'buffer_read')
    return v


@builtin()
def buffer_peek(sim, i, off, t):
    b = _buf(sim, i, 'buffer_peek')
    v, _ = _decode(b, t, int(off), 'buffer_peek')
    return v


@builtin()
def buffer_poke(sim, i, off, t, v):
    b = _buf(sim, i, 'buffer_poke')
    raw = _encode(t, v)
    off = int(off)
    if off < 0 or off + len(raw) > len(b.data):
        return -1
    b.data[off:off + len(raw)] = raw
    return 0


@builtin()
def buffer_copy(sim, src, src_off, size, dest, dest_off):
    a = _buf(sim, src, 'buffer_copy')
    d = _buf(sim, dest, 'buffer_copy')
    src_off, size, dest_off = int(src_off), int(size), int(dest_off)
    chunk = bytes(a.data[src_off:src_off + size])
    if not _ensure(d, dest_off + len(chunk), 'buffer_copy'):
        chunk = chunk[:max(0, len(d.data) - dest_off)]
    d.data[dest_off:dest_off + len(chunk)] = chunk
    return 0


@builtin()
def buffer_base64_encode(sim, i, off, size):
    import base64
    b = _buf(sim, i, 'buffer_base64_encode')
    return base64.b64encode(bytes(b.data[int(off):int(off) + int(size)])).decode('ascii')


# ------------------------------------------------------------------ sockets
class Sock:
    __slots__ = ('s', 'state', 'host', 'port')

    def __init__(self):
        self.s = None
        self.state = 'new'      # new / connecting / up / closed
        self.host = ''
        self.port = 0


def _socks(sim):
    s = getattr(sim, '_net_socks', None)
    if s is None:
        s = sim._net_socks = {}
        sim._net_next_sock = 0
        sim._net_events = []
        sim._net_timeout = 4.0
        sim.net_log = []
        hooks = getattr(sim, 'async_hooks', None)
        if hooks is None:
            hooks = sim.async_hooks = []
        hooks.append(_poll)
    return s


@builtin()
def network_set_config(sim, what, value):
    _socks(sim)
    if int(what) == 0:
        sim._net_timeout = max(0.1, float(value) / 1000.0)
    return 0


@builtin()
def network_create_socket(sim, kind):
    socks = _socks(sim)
    if int(kind) != 0:
        return -1
    i = sim._net_next_sock
    sim._net_next_sock += 1
    socks[i] = Sock()
    return GMHandle('socket', i) if _hmode(sim) else i


def _sock(sim, i, fn):
    try:
        if i.__class__ is GMHandle and i.kind != 'socket':
            raise KeyError(i)
        return _socks(sim)[_ix(i)]
    except (KeyError, TypeError, ValueError):
        raise GMError('%s(): socket %r does not exist' % (fn, i), 'network')


def _open(k, host, port):
    k.host, k.port = str(host), int(port)
    k.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    k.s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)


@builtin()
def network_connect_raw_async(sim, i, host, port):
    k = _sock(sim, i, 'network_connect_raw_async')
    try:
        _open(k, host, port)
        k.s.setblocking(False)
        r = k.s.connect_ex((socket.gethostbyname(str(host)), int(port)))
    except OSError:
        sim._net_events.append({'type': 4, 'id': _ix(i), 'socket': _ix(i), 'succeeded': 0, 'ip': str(host), 'port': int(port)})
        k.state = 'closed'
        return 0
    if r in (0, errno.EINPROGRESS, errno.EWOULDBLOCK, errno.EALREADY):
        k.state = 'connecting'
    else:
        k.state = 'closed'
        sim._net_events.append({'type': 4, 'id': _ix(i), 'socket': _ix(i), 'succeeded': 0, 'ip': str(host), 'port': int(port)})
    return 0


@builtin("network_connect_raw", "network_connect")
def network_connect_raw(sim, i, host, port):
    k = _sock(sim, i, 'network_connect_raw')
    try:
        _open(k, host, port)
        k.s.settimeout(sim._net_timeout)
        k.s.connect((str(host), int(port)))
        k.s.setblocking(False)
        k.state = 'up'
        return 0
    except OSError:
        k.state = 'closed'
        return -1


@builtin("network_send_raw", "network_send_packet")
def network_send_raw(sim, i, buf, size):
    k = _sock(sim, i, 'network_send_raw')
    if k.state != 'up' or k.s is None:
        return -1
    b = _buf(sim, buf, 'network_send_raw')
    data = bytes(b.data[:int(size)])
    try:
        k.s.setblocking(True)
        k.s.sendall(data)
        k.s.setblocking(False)
    except OSError:
        return -1
    sim.net_log.append(('send', _ix(i), data))
    return len(data)


@builtin()
def network_destroy(sim, i):
    socks = _socks(sim)
    k = socks.pop(_ix(i), None)
    if k is not None and k.s is not None:
        try:
            k.s.close()
        except OSError:
            pass
    return 0


def _poll(sim):
    socks = getattr(sim, '_net_socks', None)
    if not socks and not getattr(sim, '_net_events', None):
        return
    ev = sim._net_events
    for i, k in list(socks.items()):
        if k.s is None or k.state in ('closed', 'new'):
            continue
        if k.state == 'connecting':
            _, w, _ = select.select([], [k.s], [], 0)
            if w:
                err = k.s.getsockopt(socket.SOL_SOCKET, socket.SO_ERROR)
                ok = (err == 0)
                k.state = 'up' if ok else 'closed'
                ev.append({'type': 4, 'id': i, 'socket': i, 'succeeded': 1 if ok else 0, 'ip': k.host, 'port': k.port})
            continue
        while True:
            r, _, _ = select.select([k.s], [], [], 0)
            if not r:
                break
            try:
                data = k.s.recv(65536)
            except BlockingIOError:
                break
            except OSError:
                data = b''
            if not data:
                k.state = 'closed'
                ev.append({'type': 2, 'id': i, 'socket': i, 'ip': k.host, 'port': k.port})
                break
            ev.append({'type': 3, 'id': i, 'socket': i, 'data': data, 'ip': k.host, 'port': k.port})
    # deliver
    while ev:
        e = ev.pop(0)
        _dispatch(sim, e)


def _dispatch(sim, e):
    from .lib_core import ds_map_create, ds_map_destroy
    m = ds_map_create(sim)
    mp = sim.ds_maps[m]
    bid = None
    hm = _hmode(sim)
    for k, v in e.items():
        if k != 'data':
            mp[k] = GMHandle('socket', v) if (hm == 1 and k in ('id', 'socket')) else v
    if 'data' in e:
        bid = _new_buf(sim, len(e['data']), 0)
        _bufs(sim)[bid].data[:] = e['data']
        mp['buffer'] = _bh(sim, bid)
        mp['size'] = len(e['data'])
    sim.net_log.append(('event', e.get('type'), e.get('id'), len(e.get('data', b''))))
    old = sim.builtin_vars.get('async_load', -1)
    sim.builtin_vars['async_load'] = m
    try:
        for inst in list(sim.instances.values()):
            if inst.dead:
                continue
            found = sim.find_event(inst.obj, ('Other', 68))
            if found is not None:
                sim._run_entry(inst, found[0], ('Other', 68), found[1], None)
    finally:
        sim.builtin_vars['async_load'] = old
        if bid is not None and bid in _bufs(sim):
            del _bufs(sim)[bid]
        if m in sim.ds_maps:
            ds_map_destroy(sim, m)


# ---------------------------------------------------------------- DRBR: buffers from / to files, and their hashes
# buffer_load(name): the file (save area first, then the bundle - FS.read) as a new grow buffer, alignment 1, its whole
# length; a missing file gives -1 (GameMaker returns -1 and logs). buffer_save(buffer, name): the WHOLE buffer
# (buffer_get_size bytes) into the save area. buffer_sha1 / buffer_md5(buffer, offset, size): lowercase hex of those bytes.
@builtin()
def buffer_load(sim, name):
    if not isinstance(name, str):
        raise GMError('buffer_load(): file name must be a string', 'type')
    if not sim.fs.exists(name):
        return -1
    data = sim.fs.read(name)
    i = _new_buf(sim, 0, 1)
    _bufs(sim)[i].data = bytearray(data)
    return _bh(sim, i)


@builtin()
def buffer_save(sim, i, name):
    b = _buf(sim, i, 'buffer_save')
    if not isinstance(name, str):
        raise GMError('buffer_save(): file name must be a string', 'type')
    sim.fs.write(name, bytes(b.data))
    return 0


def _hash_range(sim, i, off, size, fn, algo):
    import hashlib
    b = _buf(sim, i, fn)
    off = max(0, int(off))
    size = int(size)
    end = len(b.data) if size < 0 else min(len(b.data), off + size)
    return hashlib.new(algo, bytes(b.data[off:end])).hexdigest()


@builtin()
def buffer_sha1(sim, i, off, size):
    return _hash_range(sim, i, off, size, 'buffer_sha1', 'sha1')


@builtin()
def buffer_md5(sim, i, off, size):
    return _hash_range(sim, i, off, size, 'buffer_md5', 'md5')
