// Tests for relay.js with plain TCP clients:  node test_relay.js
'use strict';
const net = require('net');
const assert = require('assert');
const { createRelay, cleanName, CODE_LETTERS } = require('./relay.js');

let PASS = 0;
let FAIL = 0;
function ok(cond, msg) {
    if (cond) PASS++;
    else {
        FAIL++;
        console.log('FAIL', msg);
    }
}

class Client {
    constructor(port) {
        this.port = port;
        this.inbox = [];
        this.waiters = [];
        this.buf = '';
        this.closed = false;
    }
    connect() {
        return new Promise((res, rej) => {
            this.sock = net.connect(this.port, '127.0.0.1', () => res(this));
            this.sock.setEncoding('utf8');
            this.sock.on('data', (d) => {
                this.buf += d;
                let i;
                while ((i = this.buf.indexOf('\n')) >= 0) {
                    const line = this.buf.slice(0, i);
                    this.buf = this.buf.slice(i + 1);
                    if (line.trim() !== '') this.push(JSON.parse(line));
                }
            });
            this.sock.on('close', () => {
                this.closed = true;
                this.push({ t: '__closed' });
            });
            this.sock.on('error', () => {});
        });
    }
    push(m) {
        this.inbox.push(m);
        const w = this.waiters.slice();
        this.waiters = [];
        for (const f of w) f();
    }
    send(obj) {
        this.sock.write(JSON.stringify(obj) + '\n');
    }
    raw(s) {
        this.sock.write(s);
    }
    // next message matching pred (removed from the inbox), or null after ms
    async next(pred, ms = 1500) {
        const until = Date.now() + ms;
        for (;;) {
            const i = this.inbox.findIndex((m) => !pred || pred(m));
            if (i >= 0) return this.inbox.splice(i, 1)[0];
            const left = until - Date.now();
            if (left <= 0) return null;
            await new Promise((res) => {
                const t = setTimeout(res, left);
                this.waiters.push(() => {
                    clearTimeout(t);
                    res();
                });
            });
        }
    }
    nextT(t, ms) {
        return this.next((m) => m.t === t, ms);
    }
    async quiet(ms = 150) {
        await new Promise((r) => setTimeout(r, ms));
        return this.inbox.filter((m) => m.t !== 'pong');
    }
    close() {
        this.sock.destroy();
    }
}

async function hello(port, name, ver = 43) {
    const c = await new Client(port).connect();
    c.send({ t: 'hello', game: 'kfo', ver, name });
    const w = await c.nextT('welcome');
    c.id = w ? w.id : -1;
    return c;
}

async function main() {
    const relay = createRelay({ quiet: true, timeoutMs: 800 });
    await new Promise((r) => relay.listen(0, '127.0.0.1', r));
    const port = relay.server.address().port;

    // ---- names
    ok(cleanName('  Kris  ') === 'Kris', 'trim');
    ok(cleanName('N\u00f6\u00ebl\u4e00le') === 'Nlle', 'non-ASCII removed');
    ok(cleanName('ABCDEFGHIJKLMNOPQRSTUVWXYZ') === 'ABCDEFGHIJKLMNOP', 'cut to 16');
    ok(cleanName(42) === '', 'non-string name');

    // ---- hello
    const raw = await new Client(port).connect();
    raw.send({ t: 'create' });
    let m = await raw.nextT('refused');
    ok(m && m.why === 'Say hello first', 'create before hello is refused');
    raw.send({ t: 'hello', game: 'other', ver: 1, name: 'x' });
    m = await raw.nextT('refused');
    ok(m && m.why === 'Not a Knight Fights client', 'wrong game refused');
    m = await raw.nextT('__closed');
    ok(m !== null, 'wrong game connection closed');

    const a = await hello(port, 'Kris');
    ok(a.id > 0, 'welcome id');
    a.send({ t: 'ping' });
    ok((await a.nextT('pong')) !== null, 'ping -> pong');

    // ---- create
    a.send({ t: 'create', max: 8 });
    m = await a.nextT('joined');
    ok(m && typeof m.code === 'string' && m.code.length === 5 && [...m.code].every((ch) => CODE_LETTERS.includes(ch)), 'room code: 5 consonants');
    ok(m && m.you === a.id && m.host === a.id && m.members.length === 1 && m.members[0].name === 'Kris', 'joined fields for the creator');
    const code = m.code;

    // ---- join by code (lower case accepted), member events
    const b = await hello(port, 'Susie');
    b.send({ t: 'join', code: code.toLowerCase() });
    m = await b.nextT('joined');
    ok(m && m.code === code && m.host === a.id && m.you === b.id && m.members.map((x) => x.name).join(',') === 'Kris,Susie', 'joiner gets the member list');
    m = await a.nextT('member');
    ok(m && m.ev === 'join' && m.id === b.id && m.name === 'Susie', 'host told about the join');

    const c = await hello(port, 'Ralsei');
    c.send({ t: 'join', code });
    m = await c.nextT('joined');
    ok(m && m.members.length === 3, 'third player joins');
    ok((await a.nextT('member')) !== null && (await b.nextT('member')) !== null, 'everyone told about the third join');

    // ---- up / down routing
    b.send({ t: 'up', m: { k: 'ready', on: 1 } });
    m = await a.nextT('up');
    ok(m && m.from === b.id && m.m.k === 'ready' && m.m.on === 1, 'up reaches the host with the sender id');
    ok((await c.quiet()).length === 0, 'up is not seen by other players');
    a.send({ t: 'up', m: { k: 'x' } });
    ok((await a.quiet()).length === 0, "the host's own up is not echoed");
    a.send({ t: 'down', to: c.id, m: { k: 'inc', n: 5 } });
    m = await c.nextT('down');
    ok(m && m.m.k === 'inc' && m.m.n === 5, 'down to one player');
    ok((await b.quiet()).length === 0, 'down to one player only');
    a.send({ t: 'down', to: 0, m: { k: 'state', r: 3 } });
    ok((await b.nextT('down')) !== null && (await c.nextT('down')) !== null, 'down to everyone else');
    ok((await a.quiet()).length === 0, 'the host does not get its own broadcast');
    b.send({ t: 'down', to: 0, m: { k: 'fake' } });
    ok((await c.quiet()).length === 0, 'only the host can send down');

    // ---- version checks and full rooms
    const old = await hello(port, 'Old', 42);
    old.send({ t: 'join', code });
    m = await old.nextT('refused');
    ok(m && m.why === 'Client Is Older', 'older client refused');
    const nw = await hello(port, 'New', 44);
    nw.send({ t: 'join', code });
    m = await nw.nextT('refused');
    ok(m && m.why === 'Client Is Newer', 'newer client refused');
    a.send({ t: 'max', n: 3 });
    await a.quiet(50);
    const d = await hello(port, 'Noelle');
    d.send({ t: 'join', code });
    m = await d.nextT('refused');
    ok(m && m.why === 'Full Player', 'full room refused');
    b.send({ t: 'max', n: 8 });
    d.send({ t: 'join', code });
    m = await d.nextT('refused');
    ok(m && m.why === 'Full Player', 'only the host changes the limit');
    d.send({ t: 'join', code: 'ZZZZZ' });
    m = await d.nextT('refused');
    ok(m && m.why === 'No such room', 'unknown code refused');

    // ---- kick
    a.send({ t: 'kick', id: c.id, why: 'Client Is Older' });
    m = await c.nextT('refused');
    ok(m && m.why === 'Client Is Older', 'kicked player told why');
    m = await b.nextT('member');
    ok(m && m.ev === 'leave' && m.id === c.id, 'others told about the kick');
    await a.nextT('member');
    c.send({ t: 'up', m: { k: 'x' } });
    m = await c.nextT('refused');
    ok(m && m.why === 'Not in a room', 'kicked player is out of the room');

    // ---- host leaves: promotion by join order
    a.send({ t: 'max', n: 8 });
    d.send({ t: 'join', code });
    ok((await d.nextT('joined')) !== null, 'join after the limit went back up');
    await b.nextT('member');
    await a.nextT('member');
    a.send({ t: 'leave' });
    m = await b.nextT('member');
    ok(m && m.ev === 'leave' && m.id === a.id, 'host leave announced');
    m = await b.nextT('promote');
    ok(m && m.host === b.id && m.members.map((x) => x.id).join(',') === [b.id, d.id].join(','), 'next player by join order hosts');
    m = await d.nextT('promote');
    ok(m && m.host === b.id, 'everyone told about the new host');
    d.send({ t: 'up', m: { k: 'hi' } });
    m = await b.nextT('up');
    ok(m && m.from === d.id, 'up goes to the new host');
    b.send({ t: 'down', to: d.id, m: { k: 'lobby' } });
    ok((await d.nextT('down')) !== null, 'the new host can send down');

    // ---- disconnect = leave; last one out closes the room
    b.close();
    m = await d.nextT('promote');
    ok(m && m.host === d.id, 'host disconnect promotes the last player');
    d.send({ t: 'leave' });
    await d.quiet(100);
    ok(!relay.rooms.has(code), 'room closed when empty');
    const e = await hello(port, 'Late');
    e.send({ t: 'join', code });
    m = await e.nextT('refused');
    ok(m && m.why === 'No such room', 'closed room cannot be joined');

    // ---- LOCAL room (direct IP play)
    e.send({ t: 'join', code: 'LOCAL' });
    m = await e.nextT('joined');
    ok(m && m.code === 'LOCAL' && m.host === e.id, 'LOCAL is made on first use');
    const f = await hello(port, 'Lan2');
    f.send({ t: 'join', code: 'local' });
    m = await f.nextT('joined');
    ok(m && m.code === 'LOCAL' && m.host === e.id && m.members.length === 2, 'second LOCAL player joins it');
    m = await e.nextT('member');
    ok(m && m.ev === 'join' && m.id === f.id, 'LOCAL host told about the join');
    f.send({ t: 'create' });
    m = await f.nextT('joined');
    ok(m && m.code !== 'LOCAL' && m.host === f.id, 'create leaves LOCAL for a new room');
    m = await e.nextT('member');
    ok(m && m.ev === 'leave' && m.id === f.id, 'LOCAL told the player left');

    // ---- robustness: bad JSON, unknown types, long lines
    e.raw('{not json}\n\n   \n');
    e.send({ t: 'whatever', x: 1 });
    e.send({ t: 'ping' });
    ok((await e.nextT('pong')) !== null, 'bad lines and unknown types are ignored');
    const g = await hello(port, 'Spammer');
    g.raw('x'.repeat(70 * 1024));
    ok((await g.nextT('__closed', 2000)) !== null, 'over-long line drops the connection');

    // ---- silent players time out (800 ms in this test, 20 s for real)
    const h = await hello(port, 'Host');
    h.send({ t: 'create' });
    const hc = (await h.nextT('joined')).code;
    const i2 = await hello(port, 'Guest');
    i2.send({ t: 'join', code: hc });
    await i2.nextT('joined');
    // only the guest keeps pinging
    const pinger = setInterval(() => i2.send({ t: 'ping' }), 200);
    m = await i2.nextT('promote', 3000);
    clearInterval(pinger);
    ok(m && m.host === i2.id, 'silent host dropped and the guest promoted');
    ok(h.closed || (await h.nextT('__closed', 1500)) !== null, 'silent host connection closed');

    for (const x of [raw, a, b, c, d, old, nw, e, f, g, h, i2]) {
        try {
            x.close();
        } catch (err) {}
    }
    relay.close();
    console.log('relay tests: ' + PASS + ' passed, ' + FAIL + ' failed');
    process.exit(FAIL ? 1 : 0);
}

main().catch((e) => {
    console.error(e);
    process.exit(2);
});
