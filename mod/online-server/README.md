# Knight Fights Online: the relay server

`relay.js` is the small server that lets Knight Hub players find each other. It keeps the **rooms** (5-letter codes), who
is in them and who hosts them, and it passes messages between the players of a room. It does not run the match. The
**host's game** runs the room: the lobby, the settings, the sends, who is out and in what place. If the host leaves, the
next player who joined takes over. Nothing in this file has to change when the game's rules change.

You need **Node.js 18 or newer** (https://nodejs.org, the LTS installer is fine). The relay has no other dependencies.

## Run it

Windows: double-click `START_RELAY.bat` (it runs `node relay.js` and keeps the window open).

Any system:

```
node relay.js                 # port 7777
node relay.js --port 25565    # another port
node relay.js --quiet         # no join/leave lines
```

The window shows rooms being made, players joining and leaving, and who hosts. Close it (or Ctrl+C) to stop the server.

## Connect the games

In the game: walk to the Knight Hub sign, open the **KNIGHT** tab, choose **ONLINE**, then **SERVER**, and type the address
of the PC that runs the relay (for example `192.168.1.20` or `203.0.113.5:7777`). The address is saved in
`knightfights_online.ini`, in the game's save folder next to `knight_hub.ini`.

- **Same PC (testing):** `127.0.0.1` (the default).
- **Same network / Radmin VPN / Hamachi:** the relay PC's LAN or VPN address. Everyone picks **JOIN LAN ROOM** and lands in
  one room named LOCAL, or one player picks **CREATE ROOM** and the others **JOIN ROOM** with the code.
- **Over the internet:** the relay needs a public address. Pick one:
  - forward TCP port 7777 on the router of the relay PC to that PC (your home IP is then what friends type), or
  - a tunnel such as playit.gg or ngrok (TCP) pointing at port 7777 on the relay PC (friends type the address it gives you), or
  - a small rented server (VPS). Any Linux box with Node.js and TCP port 7777 open works. On Ubuntu:
    `apt install -y nodejs`, copy `relay.js` over, open port 7777 in the provider's firewall, then
    `npm install -g pm2 && pm2 start relay.js --name knightfights && pm2 save && pm2 startup`.

**PRACTICE** needs no server at all. It plays the online match on your own PC, against bots.

## Check that it works

`node test_relay.js` runs the relay's own tests with fake players (rooms, codes, joining, hosts leaving, full rooms,
timeouts). It should end with `0 failed`.

From another PC, `Test-NetConnection <address> -Port 7777` in PowerShell must say `TcpTestSucceeded : True`.

## What it refuses

| The game shows | Why |
| --- | --- |
| There is no room with that code. | The code is wrong, or everyone left that room. |
| That room is full. | The host set a player limit (2-8) and it is reached. |
| The room's players have a newer / older Knight Hub build. | Everyone in a room needs the same Knight Hub build. |
| Could not connect to ... | Nothing answered at that address and port (the relay is not running, a firewall, or a typo). |

A game that stops answering for 20 seconds is dropped from its room. The game pings every 3 seconds, so this only happens
when a game crashed or lost its connection.

## The protocol, for anyone extending it

One JSON object per line over plain TCP. A player sends `hello {game:"kfo", ver, name}`, then `create {max}` or
`join {code}`. Inside a room, `up {m}` goes to the host (delivered as `up {from, m}`). The host sends `down {to, m}`, where
`to` is one player's id, or 0 for everyone else. The relay announces `member {ev, id, name}` and
`promote {host, members}`, and refuses with `refused {why}`. `ping` gets `pong`. The game-level messages inside `m` are
described at the top of `online_net.gml` and `online_host.gml` in the toolkit.
