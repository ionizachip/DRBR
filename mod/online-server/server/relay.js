#!/usr/bin/env node
// Knight Fights Online - relay server (Knight Hub build 43)
//
// The relay is a router. It keeps rooms (5-letter codes), who is in them and who hosts them, and passes messages between
// the players of a room. The match itself (lobby, settings, sends, who is out, results) runs in the HOST player's game, the
// same way it will over Steam, so this file never needs to change when the game's rules do.
//
// Wire format: one JSON object per line ("\n"), UTF-8, over plain TCP. No dependencies: Node 18 or newer.
//
//   node relay.js                 listens on port 7777
//   node relay.js --port 25565    another port
//   node relay.js --quiet         no join/leave log lines
//
// Messages (t = type). From a player:
//   hello  {game:"kfo", ver, name}       first message; answered by welcome {id}
//   create {max}                         make a room; answered by joined {code, you, host, members}
//   join   {code}                        enter a room ("LOCAL" is created on first use, for LAN / Radmin play)
//   leave                                leave the room
//   up     {m}                           to the host of the room (delivered as up {from, m})
//   ping                                 answered by pong
// From the host only:
//   down   {to, m}                       to one player (to = id) or to everyone else (to = 0); delivered as down {m}
//   kick   {id, why}                     removes a player from the room (they get refused {why})
//   max    {n}                          member limit of the room (2-12: players + watch places)
// From the relay:
//   member {ev: "join" | "leave", id, name}     promote {host, members}     refused {why}
'use strict';
const net = require('net');

const RELAY_VERSION = 1;
const CODE_LETTERS = 'BCDFGHJKLMNPQRSTVWXZ';   // no vowels (and no Y), so a code never spells a word
const CODE_LEN = 5;
const MAX_PLAYERS = 12;                         // build 47: 8 players + up to 4 watch places
const MAX_LINE = 64 * 1024;                     // a longer line without "\n" drops the connection
const NAME_MAX = 16;

function argOf(argv, name, dflt) {
    const i = argv.indexOf(name);
    return (i >= 0 && i + 1 < argv.length) ? argv[i + 1] : dflt;
}

function cleanName(s) {
    if (typeof s !== 'string') return '';
    // printable ASCII only (the game's font has nothing else), trimmed, at most NAME_MAX characters
    let out = '';
    for (const ch of s) {
        const c = ch.charCodeAt(0);
        if (c >= 32 && c < 127) out += ch;
    }
    out = out.trim().replace(/\s+/g, ' ');
    return out.slice(0, NAME_MAX);
}

function toInt(v, dflt) {
    const n = Number(v);
    return Number.isFinite(n) ? Math.trunc(n) : dflt;
}

function createRelay(opts) {
    opts = opts || {};
    const timeoutMs = opts.timeoutMs || 20000;
    const log = opts.quiet ? () => {} : (...a) => console.log(new Date().toISOString(), ...a);
    const rooms = new Map();      // code -> room
    const clients = new Map();    // id -> client
    let nextId = 1;
    const stats = { connections: 0, rooms: 0, messages: 0, dropped: 0 };

    function send(c, obj) {
        if (!c || c.closed) return;
        try {
            c.sock.write(JSON.stringify(obj) + '\n');
        } catch (e) {
            // the socket is going away; its 'close' handler cleans up
        }
    }

    function memberList(room) {
        return room.members.map((m) => ({ id: m.id, name: m.name }));
    }

    function newCode() {
        for (let tries = 0; tries < 1000; tries++) {
            let s = '';
            for (let i = 0; i < CODE_LEN; i++) s += CODE_LETTERS[Math.floor(Math.random() * CODE_LETTERS.length)];
            if (!rooms.has(s)) return s;
        }
        return null;
    }

    function makeRoom(code, host, max) {
        const room = { code, ver: host.ver, members: [host], host, max: Math.max(2, Math.min(MAX_PLAYERS, toInt(max, MAX_PLAYERS))), made: Date.now() };
        rooms.set(code, room);
        host.room = room;
        stats.rooms++;
        log('room', code, 'made by', host.id, JSON.stringify(host.name));
        return room;
    }

    function joinedMsg(room, c) {
        return { t: 'joined', code: room.code, you: c.id, host: room.host.id, max: room.max, members: memberList(room) };
    }

    function leaveRoom(c, why) {
        const room = c.room;
        if (!room) return;
        c.room = null;
        const i = room.members.indexOf(c);
        if (i >= 0) room.members.splice(i, 1);
        log('room', room.code, 'leave', c.id, why || '');
        if (room.members.length === 0) {
            rooms.delete(room.code);
            log('room', room.code, 'closed');
            return;
        }
        for (const m of room.members) send(m, { t: 'member', ev: 'leave', id: c.id, name: c.name });
        if (room.host === c) {
            // the next player by join order hosts; their game takes the room over from the last state it got
            room.host = room.members[0];
            log('room', room.code, 'host is now', room.host.id);
            for (const m of room.members) send(m, { t: 'promote', host: room.host.id, members: memberList(room) });
        }
    }

    function refuse(c, why) {
        send(c, { t: 'refused', why });
    }

    function handle(c, msg) {
        stats.messages++;
        const t = msg.t;
        if (t === 'ping') {
            send(c, { t: 'pong' });
            return;
        }
        if (t === 'hello') {
            if (msg.game !== 'kfo') {
                refuse(c, 'Not a Knight Fights client');
                c.sock.end();
                return;
            }
            const name = cleanName(msg.name);
            c.name = (name === '') ? ('Player' + c.id) : name;
            c.ver = toInt(msg.ver, 0);
            c.hello = true;
            send(c, { t: 'welcome', id: c.id, relay: RELAY_VERSION });
            return;
        }
        if (!c.hello) {
            refuse(c, 'Say hello first');
            return;
        }
        switch (t) {
            case 'create': {
                if (c.room) leaveRoom(c, 'create');
                const code = newCode();
                if (!code) {
                    refuse(c, 'Server full');
                    return;
                }
                const room = makeRoom(code, c, msg.max);
                send(c, joinedMsg(room, c));
                return;
            }
            case 'join': {
                const code = String(msg.code || '').toUpperCase().replace(/[^A-Z]/g, '');
                if (c.room && c.room.code === code) {
                    send(c, joinedMsg(c.room, c));
                    return;
                }
                let room = rooms.get(code);
                if (!room && code === 'LOCAL') {
                    if (c.room) leaveRoom(c, 'join');
                    room = makeRoom('LOCAL', c, MAX_PLAYERS);
                    send(c, joinedMsg(room, c));
                    return;
                }
                if (!room) {
                    refuse(c, 'No such room');
                    return;
                }
                if (c.ver < room.ver) {
                    refuse(c, 'Client Is Older');
                    return;
                }
                if (c.ver > room.ver) {
                    refuse(c, 'Client Is Newer');
                    return;
                }
                if (room.members.length >= room.max) {
                    refuse(c, 'Full Player');
                    return;
                }
                if (c.room) leaveRoom(c, 'join');
                for (const m of room.members) send(m, { t: 'member', ev: 'join', id: c.id, name: c.name });
                room.members.push(c);
                c.room = room;
                log('room', room.code, 'join', c.id, JSON.stringify(c.name));
                send(c, joinedMsg(room, c));
                return;
            }
            case 'leave':
                leaveRoom(c, 'left');
                return;
            case 'up': {
                const room = c.room;
                if (!room) {
                    refuse(c, 'Not in a room');
                    return;
                }
                if (room.host === c) return;      // the host handles its own messages in its game
                send(room.host, { t: 'up', from: c.id, m: msg.m });
                return;
            }
            case 'down': {
                const room = c.room;
                if (!room || room.host !== c) return;
                const to = toInt(msg.to, -1);
                if (to === 0) {
                    for (const m of room.members) if (m !== c) send(m, { t: 'down', m: msg.m });
                    return;
                }
                const target = room.members.find((m) => m.id === to);
                if (target && target !== c) send(target, { t: 'down', m: msg.m });
                return;
            }
            case 'kick': {
                const room = c.room;
                if (!room || room.host !== c) return;
                const target = room.members.find((m) => m.id === toInt(msg.id, -1));
                if (!target || target === c) return;
                refuse(target, (typeof msg.why === 'string' && msg.why !== '') ? msg.why.slice(0, 60) : 'Kicked');
                leaveRoom(target, 'kicked');
                return;
            }
            case 'max': {
                const room = c.room;
                if (!room || room.host !== c) return;
                room.max = Math.max(2, Math.min(MAX_PLAYERS, toInt(msg.n, MAX_PLAYERS)));
                return;
            }
            default:
                // unknown types are ignored, so newer clients can add messages without breaking older relays
                return;
        }
    }

    const server = net.createServer((sock) => {
        const c = { id: nextId++, sock, name: '', ver: 0, hello: false, room: null, last: Date.now(), buf: '', closed: false };
        clients.set(c.id, c);
        stats.connections++;
        sock.setNoDelay(true);
        sock.setEncoding('utf8');
        sock.on('data', (chunk) => {
            c.last = Date.now();
            c.buf += chunk;
            let nl;
            while ((nl = c.buf.indexOf('\n')) >= 0) {
                const line = c.buf.slice(0, nl).replace(/\r$/, '');
                c.buf = c.buf.slice(nl + 1);
                if (line.trim() === '') continue;
                let msg;
                try {
                    msg = JSON.parse(line);
                } catch (e) {
                    stats.dropped++;
                    continue;
                }
                if (msg && typeof msg === 'object' && typeof msg.t === 'string') handle(c, msg);
                if (c.closed) return;
            }
            if (c.buf.length > MAX_LINE) {
                log('client', c.id, 'sent an over-long line: dropped');
                sock.destroy();
            }
        });
        const gone = () => {
            if (c.closed) return;
            c.closed = true;
            leaveRoom(c, 'disconnected');
            clients.delete(c.id);
        };
        sock.on('close', gone);
        sock.on('error', gone);
    });

    // players that went silent (crashed game, pulled cable) are dropped after timeoutMs; the game pings every few seconds
    const sweep = setInterval(() => {
        const now = Date.now();
        for (const c of clients.values()) {
            if (now - c.last > timeoutMs) {
                log('client', c.id, 'timed out');
                c.sock.destroy();
            }
        }
    }, Math.max(250, Math.min(5000, Math.floor(timeoutMs / 4))));
    sweep.unref();

    return {
        server,
        rooms,
        clients,
        stats,
        listen(port, host, cb) {
            server.listen(port, host, cb);
            return this;
        },
        close(cb) {
            clearInterval(sweep);
            for (const c of clients.values()) c.sock.destroy();
            server.close(cb);
        }
    };
}

module.exports = { createRelay, cleanName, CODE_LETTERS, CODE_LEN, RELAY_VERSION };

if (require.main === module) {
    const argv = process.argv.slice(2);
    if (argv.includes('--help') || argv.includes('-h')) {
        console.log('usage: node relay.js [--port 7777] [--host 0.0.0.0] [--quiet]');
        process.exit(0);
    }
    const port = toInt(argOf(argv, '--port', process.env.KF_PORT || '7777'), 7777);
    const host = argOf(argv, '--host', '0.0.0.0');
    const relay = createRelay({ quiet: argv.includes('--quiet') });
    relay.server.on('error', (e) => {
        console.error('relay: ' + e.message + (e.code === 'EADDRINUSE' ? ' (is another relay already running on this port?)' : ''));
        process.exit(1);
    });
    relay.listen(port, host, () => console.log('Knight Fights relay listening on ' + host + ':' + port));
    const stop = () => {
        console.log('relay: shutting down');
        relay.close(() => process.exit(0));
        setTimeout(() => process.exit(0), 1000).unref();
    };
    process.on('SIGINT', stop);
    process.on('SIGTERM', stop);
}
