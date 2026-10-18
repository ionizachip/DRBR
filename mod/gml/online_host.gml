// ===== Build 45: KNIGHT FIGHTS ONLINE - the room, run by the host's game =====
// The host keeps the players, the settings and the match. It does NOT run anybody's fight: every game runs the same shared
// battle from the timeline (seed + settings + the final-two cycle) and decides its own hits. The host:
//   - starts the match (seed, frozen settings), waits until every player's battle is up, then gives the GO (tick 0);
//   - answers pings with its match clock (every game keeps its tick in step with the host's);
//   - passes the SOULs around (15 a second), the standings (4 a second), the skills (checked: alive, allowed, cooldown,
//     never twice), the outs (places, ties) and the results;
//   - steps in when a game falls out of step: a wrong cycle (a different knight, attack, seed or start) -> resync; a clock
//     that drifted -> resync; impossible HP / max HP / gauge -> fix. Nothing else is corrected: the rest is the player's.
//   - runs the bots (practice, or bots in an online room): bot SOULs in the host's own box that dodge the real bullets.
// It tells the players with "lobby" (the room) and "st" (the match). Every player's game keeps the last ones, so when the
// host leaves the next player takes the room (and a running match) over from them.

// ---------- a seeded random generator that gives the same numbers in every game (Park-Miller, exact in doubles) ----------
function kfo_rng(_seed)
{
    var _s = floor(abs(_seed)) mod 2147483647;
    if (_s <= 0)
        _s = 1;
    return { s: _s };
}

function kfo_rng_next(_g)
{
    _g.s = (_g.s * 48271) mod 2147483647;
    return _g.s;
}

function kfo_rng_int(_g, _n)
{
    return kfo_rng_next(_g) mod max(1, _n);
}

// ---------- the room ----------
function kfo_host_player_new(_id, _name, _skin, _bot)
{
    return { pid: _id, n: _name, s: _skin, rd: 0, bot: _bot, hi: _bot, inm: 0, al: 0, pl: 0, hp: 150, mh: 150, g: 0, ft: 0, rdy: 0,
        sg: 0, sr: 0, hits: 0, sk: 0, lat: -1, c: -1, t: 0, sigbad: 0, clk: 0, t_rs: 0, sq: 0, t_sk: -100000, fh: 0, t_s: 0,
        x: 0, y: 0, hx: 0, t_p: 0, ow: undefined, bt: undefined, skp: 0, outt: -1, tk: 0, hl: 0, t_rf: -100000, clks: [],
        cl: -1, sp: 0, gzn: 0, q: [], qs: -1, qh: -1, tm: 0, tmx: 0, tpk: -1, tg: [], tc: -1, tcl: -1, sh: 0, t_heal: -100000, lby: -1, kos: 0, sd: 0, dt: 0, t_ls: -100000 };
}

function kfo_host_begin(_code, _prac)
{
    var _o = global.kfo;
    var _h = { code: _code, prac: _prac, st: "lobby", mid: 0, seed: 0, set: kfo_set_clean(_o.set), mset: undefined, eff: undefined, pl: [], gone: [],
        feed: [], fseq: 0, dl: true, ds: false, t_s: 0, t_ps: 0, t_ow: 0, startn: 0, res: undefined, go: false, t0ms: 0, t_start: 0, tl: undefined,
        pend: [], ban: [], ftk: -1, ft_done: false, ft_t: -999999, desyncs: 0, clockfix: 0, fixes: 0, skills_ok: 0, skills_bad: 0, bc: {}, bc_same: 0, bc_diff: 0, ended_t: 0,
        log: [] };
    _o.H = _h;
    kfo_host_chat_init(_h);
    array_push(_h.pl, kfo_host_player_new(_o.my, _o.name, _o.skin, 0));
    _h.pl[0].cl = _o.look.col;
    // build 50: a practice room starts with no bots (BOTS on the room page adds them); you can start it on your own
    if (_prac)
        _h.set.bots = 0;
    kfo_host_bots(_h.set.bots);
    if (!_prac && _o.mode == "direct")
        kfo_raw({ t: "max", n: kfo_host_cap() });
    if (_o.mode == "steam")
        kfo_steam_lobby_meta();
    return _h;
}

// _n bots in the room (named after people of the Dark World)
function kfo_host_bots(_n)
{
    var _h = global.kfo.H;
    for (var _i = array_length(_h.pl) - 1; _i >= 0; _i--)
    {
        if (_h.pl[_i].bot)
            array_delete(_h.pl, _i, 1);
    }
    var _names = ["LANCER", "ROUXLS", "BERDLY", "TENNA", "QUEEN", "SPAMTON", "JEVIL"];
    var _room = _h.prac ? 7 : max(0, _h.set.maxp - kfo_host_humans());
    for (var _i = 0; _i < _n && _i < 7 && _i < _room; _i++)
    {
        var _b = kfo_host_player_new(101 + _i, _names[_i], 1 + ((_i + 1) mod 4), 1);
        _b.rd = 1;
        // build 49: its own settings (kept by its place among the bots)
        _b.bd = kfo_host_botcfg(_i).pre;
        array_push(_h.pl, _b);
    }
    _h.dl = true;
}

function kfo_host_humans()
{
    var _h = global.kfo.H;
    var _n = 0;
    for (var _i = 0; _i < array_length(_h.pl); _i++)
    {
        if (!_h.pl[_i].bot)
            _n++;
    }
    return _n;
}

function kfo_host_player(_id)
{
    var _h = global.kfo.H;
    if (!is_struct(_h))
        return undefined;
    for (var _i = 0; _i < array_length(_h.pl); _i++)
    {
        if (_h.pl[_i].pid == _id)
            return _h.pl[_i];
    }
    return undefined;
}

// a name nobody else in the room has (a number is added)
function kfo_host_unique(_name, _id)
{
    var _h = global.kfo.H;
    var _base = (_name == "") ? "Player" : _name;
    var _try = _base;
    for (var _n = 2; _n < 20; _n++)
    {
        var _taken = false;
        for (var _i = 0; _i < array_length(_h.pl); _i++)
        {
            if (_h.pl[_i].pid != _id && string_upper(_h.pl[_i].n) == string_upper(_try))
                _taken = true;
        }
        if (!_taken)
            return _try;
        _try = string_copy(_base, 1, 10) + string(_n);
    }
    return _try;
}

// a line for everybody's log (colour: white, yellow, blue, red as the design's log colours)
function kfo_host_feed(_t, _col)
{
    var _h = global.kfo.H;
    _h.fseq++;
    array_push(_h.feed, [_h.fseq, _t, _col]);
    if (array_length(_h.feed) > 30)
        array_delete(_h.feed, 0, array_length(_h.feed) - 30);
    _h.ds = true;
}

function kfo_host_alive()
{
    var _h = global.kfo.H;
    var _n = 0;
    for (var _i = 0; _i < array_length(_h.pl); _i++)
    {
        if (_h.pl[_i].inm && _h.pl[_i].al)
            _n++;
    }
    return _n;
}

function kfo_host_lobby_msg()
{
    var _o = global.kfo;
    var _h = _o.H;
    var _pl = [];
    for (var _i = 0; _i < array_length(_h.pl); _i++)
    {
        var _p = _h.pl[_i];
        array_push(_pl, { pid: _p.pid, n: _p.n, s: _p.s, rd: _p.rd, inm: _p.inm, bot: _p.bot, bd: variable_struct_exists(_p, "bd") ? _p.bd : 2, rj: kfo_host_may_watch(_p) ? 1 : 0,
            cl: _p.cl, lat: _p.lat, sp: _p.sp, al: _p.al, pl: _p.pl, why: kfo_host_watch_why(_p) });
    }
    return { k: "lobby", code: _h.code, host: _o.my, st: _h.st, mid: _h.mid, prac: _h.prac ? 1 : 0, set: _h.set, players: _pl,
        res: is_struct(_h.res) ? _h.res : 0, ver: kfo_version(), mode: _o.mode, sc: kfo_host_watchers(), cap: kfo_host_cap() };
}

// the match tick of the host now
function kfo_host_tick_now()
{
    var _h = global.kfo.H;
    if (!_h.go)
        return -999999;
    return (current_time - _h.t0ms) * 0.03;
}

function kfo_host_state_msg()
{
    var _h = global.kfo.H;
    var _pl = [];
    for (var _i = 0; _i < array_length(_h.pl); _i++)
    {
        var _p = _h.pl[_i];
        if (!_p.inm)
            continue;
        array_push(_pl, { pid: _p.pid, n: _p.n, s: _p.s, hp: _p.hp, mh: _p.mh, g: _p.g, al: _p.al, pl: _p.pl, sg: _p.sg, sr: _p.sr, bot: _p.bot,
            sk: _p.sk, lat: _p.lat, c: _p.c, rdy: _p.rdy, cl: _p.cl, tk: _p.tk, hl: _p.hl, gz: _p.gzn, ft: _p.ft, q: _p.q, qs: _p.qs, qh: _p.qh,
            tm: _p.tmx, tg: _p.tg, sh: _p.sh, sd: (_p.bot && is_struct(_p.bt)) ? _p.bt.shield : (variable_struct_exists(_p, "sd") ? _p.sd : 0), ti: (_p.al && kfo_host_tg_tired(_p)) ? 1 : 0, ko: _p.kos });
    }
    for (var _i = 0; _i < array_length(_h.gone); _i++)
    {
        var _g = _h.gone[_i];
        if (_g.mid == _h.mid)
            array_push(_pl, { pid: _g.pid, n: _g.n, s: _g.s, hp: 0, mh: _g.mh, g: 0, al: 0, pl: _g.pl, sg: _g.sg, sr: _g.sr, bot: 0, sk: 0, lat: -1, c: -1, rdy: 1,
                cl: _g.cl, tk: _g.tk, hl: _g.hl, gz: _g.gz, ft: _g.ft, q: [], qs: -1, qh: -1, gone: 1, tm: 0, tg: [], sh: variable_struct_exists(_g, "sh") ? _g.sh : 0, ti: 0,
                ko: variable_struct_exists(_g, "kos") ? _g.kos : 0 });
    }
    var _fd = [];
    for (var _i = max(0, array_length(_h.feed) - 8); _i < array_length(_h.feed); _i++)
        array_push(_fd, _h.feed[_i]);
    var _t = kfo_host_tick_now();
    var _ck = (_h.go ? kbr_tl_at(_h.tl, _t) : -1);
    // build 47: the cycle's knight and attack (the room's page shows them to the ones not playing), the watchers
    var _kn = -1;
    var _ai = -1;
    if (_ck >= 0)
    {
        var _cy = kbr_tl_get(_h.tl, _ck);
        _kn = _cy.ok;
        _ai = _cy.ai;
    }
    return { k: "st", mid: _h.mid, an: kfo_host_alive(), sn: _h.startn, t: round(_t), ck: _ck, ft: _h.ftk, pl: _pl, fd: _fd, go: _h.go ? 1 : 0,
        kn: _kn, ai: _ai, sc: kfo_host_watchers(), intro: is_struct(_h.tl) ? _h.tl.intro : 0, sd0: is_struct(_h.tl) ? kbr_tl_sd_t0(_h.tl) : -1,
        fg: round(kbr_fl_host_g() * 10), fp: kbr_tl_flph_list(_h.tl) };
}

// send what changed (the lobby at once, the standings at most 4 times a second, the SOULs 15 times a second)
function kfo_host_flush(_force)
{
    var _h = global.kfo.H;
    if (_h.dl)
    {
        _h.dl = false;
        kfo_down(0, kfo_host_lobby_msg());
        if (global.kfo.mode == "steam")
            kfo_steam_lobby_meta();
    }
    if (_h.st == "match" && (_force || current_time - _h.t_s >= 250))
    {
        _h.ds = false;
        _h.t_s = current_time;
        kfo_down(0, kfo_host_state_msg());
    }
    if (_h.st == "match" && current_time - _h.t_ps >= 66)
    {
        _h.t_ps = current_time;
        var _l = [];
        for (var _i = 0; _i < array_length(_h.pl); _i++)
        {
            var _p = _h.pl[_i];
            if (_p.inm && _p.al && _p.t_p > 0 && current_time - _p.t_p < 1500)
                array_push(_l, [_p.pid, round(_p.x * 10), round(_p.y * 10), _p.hx, variable_struct_exists(_p, "fd") ? _p.fd : 0, variable_struct_exists(_p, "ffa") ? _p.ffa : 0,
                    variable_struct_exists(_p, "gd") ? _p.gd : -1]);   // tenths of a pixel (build 47); DRBR 1.0.1: the green shield's direction
        }
        if (array_length(_l) > 0)
            kfo_down_fast(0, { k: "ps", mid: _h.mid, l: _l });
    }
    // the cold place: where everybody walks (10 a second)
    if (current_time - _h.t_ow >= 100)
    {
        _h.t_ow = current_time;
        var _w = [];
        for (var _i = 0; _i < array_length(_h.pl); _i++)
        {
            var _p = _h.pl[_i];
            if (is_array(_p.ow) && current_time - _p.ow[5] < 3000)
                array_push(_w, [_p.pid, _p.ow[0], _p.ow[1], _p.ow[2], _p.ow[3], _p.s, _p.ow[4], _p.rd, (array_length(_p.ow) > 6) ? _p.ow[6] : -1]);
        }
        if (array_length(_w) > 0)
            kfo_down_fast(0, { k: "ows", l: _w });
    }
}

function kfo_host_tick()
{
    var _h = global.kfo.H;
    if (!is_struct(_h))
        return 0;
    if (_h.st == "match")
    {
        kfo_host_match_tick();
        if (!is_struct(global.kfo.H))
            return 0;
        _h = global.kfo.H;
    }
    kfo_host_flush(false);
    return 0;
}

// a player came in (the relay / Steam told us) / went
function kfo_host_member(_ev, _id, _name)
{
    var _o = global.kfo;
    var _h = _o.H;
    if (!is_struct(_h))
        return 0;
    if (_ev == "join")
    {
        if (is_undefined(kfo_host_player(_id)))
        {
            // the room is full of bots: one bot makes room for a person
            if (array_length(_h.pl) >= _h.set.maxp && _h.st == "lobby")
            {
                for (var _i = array_length(_h.pl) - 1; _i >= 0; _i--)
                {
                    if (_h.pl[_i].bot)
                    {
                        array_delete(_h.pl, _i, 1);
                        break;
                    }
                }
            }
            array_push(_h.pl, kfo_host_player_new(_id, kfo_host_unique(kfo_clean_name(_name), _id), 1, 0));
        }
        _h.dl = true;
        if (_h.st == "match")
            _h.ds = true;
        return 1;
    }
    var _p = kfo_host_player(_id);
    if (is_undefined(_p))
        return 0;
    if (_p.hi && !_p.bot && _p.pid != _o.my)
        kfo_host_chat_sys(_p.n + " left the room.");
    if (_h.st == "match" && _p.inm && _p.al)
        kfo_host_out_now(_id, round(kfo_host_tick_now()), "left");
    if (_h.st == "match" && _p.inm)
        array_push(_h.gone, { mid: _h.mid, pid: _p.pid, n: _p.n, s: _p.s, mh: _p.mh, pl: _p.pl, sg: _p.sg, sr: _p.sr, ft: _p.ft, hits: _p.hits, sh: _p.sh, kos: _p.kos,
            cl: _p.cl, tk: _p.tk, hl: _p.hl, gz: _p.gzn });
    for (var _i = array_length(_h.pl) - 1; _i >= 0; _i--)
    {
        if (_h.pl[_i].pid == _id)
            array_delete(_h.pl, _i, 1);
    }
    _h.dl = true;
    _h.ds = true;
    if (_h.st == "match")
        kfo_host_check_end();
    return 1;
}

// the next player took over a room whose host left: rebuild the room from the last lobby / standings this game got
function kfo_host_takeover(_members)
{
    var _o = global.kfo;
    var _lb = _o.lobby;
    var _h = kfo_host_begin(_o.code, false);
    _h.pl = [];
    var _set = kfo_set_clean(is_struct(_lb) ? kfo_jv(_lb, "set") : _o.set);
    _h.set = _set;
    var _lp = is_struct(_lb) ? kfo_ja(_lb, "players") : [];
    for (var _i = 0; _i < array_length(_members); _i++)
    {
        var _mid = kfo_jn(_members[_i], "pid", -1);
        var _nm = kfo_clean_name(kfo_js(_members[_i], "name", ""));
        var _sk = 1;
        var _rd = 0;
        var _cl = -1;
        var _spw = 0;
        for (var _j = 0; _j < array_length(_lp); _j++)
        {
            if (kfo_jn(_lp[_j], "pid", -2) == _mid)
            {
                _nm = kfo_js(_lp[_j], "n", _nm);
                _sk = kfo_skin_ok(kfo_jn(_lp[_j], "s", 1));
                _rd = kfo_jn(_lp[_j], "rd", 0);
                _cl = kfo_col_ok(kfo_jn(_lp[_j], "cl", -1), -1);
                _spw = kfo_jn(_lp[_j], "sp", 0);
            }
        }
        if (_mid == _o.my)
        {
            _nm = _o.name;
            _sk = _o.skin;
            _cl = _o.look.col;
        }
        var _p = kfo_host_player_new(_mid, _nm, _sk, 0);
        _p.rd = _rd;
        _p.hi = 1;
        // build 47: the SOUL colour and watching come over too (a colour is never lost to a host change)
        _p.cl = _cl;
        _p.sp = _spw;
        array_push(_h.pl, _p);
    }
    // the room's bots come back (they are the host's)
    for (var _j = 0; _j < array_length(_lp); _j++)
    {
        if (kfo_jn(_lp[_j], "bot", 0) == 1 && is_undefined(kfo_host_player(kfo_jn(_lp[_j], "pid", -2))))
        {
            var _b = kfo_host_player_new(kfo_jn(_lp[_j], "pid", 101), kfo_js(_lp[_j], "n", "BOT"), kfo_skin_ok(kfo_jn(_lp[_j], "s", 1)), 1);
            _b.rd = 1;
            array_push(_h.pl, _b);
        }
    }
    // a match in progress goes on from the last standings and this game's own clock and timeline
    var _M = _o.M;
    if (is_struct(_lb) && kfo_js(_lb, "st", "lobby") == "match" && is_struct(_M) && is_struct(_M.st) && variable_struct_exists(_M, "tl"))
    {
        var _st = _M.st;
        _h.st = "match";
        _h.mid = kfo_jn(_st, "mid", _M.mid);
        _h.seed = _M.seed;
        _h.mset = _M.set;
        _h.eff = kbr_eff(_M.set);
        _h.tl = kbr_tl_new(_M.seed, _M.set);
        _h.ftk = _M.tl.ft;
        if (_h.ftk >= 0)
        {
            kbr_tl_set_ft(_h.tl, _h.ftk);
            _h.ft_done = true;
        }
        kbr_tl_flph_load(_h.tl, kbr_tl_flph_list(_M.tl));
        _h.flg = variable_struct_exists(_M, "flg") ? _M.flg : 0;
        _h.fl_next = 0;
        _h.go = _M.go;
        _h.t0ms = _M.t0ms;
        _h.t_start = current_time - 20000;
        _h.startn = kfo_jn(_st, "sn", 2);
        var _sp = kfo_ja(_st, "pl");
        for (var _j = 0; _j < array_length(_sp); _j++)
        {
            var _s = _sp[_j];
            var _p2 = kfo_host_player(kfo_jn(_s, "pid", -2));
            if (is_undefined(_p2))
            {
                // left before the takeover: kept for the results
                if (kfo_jn(_s, "al", 0) == 0)
                    array_push(_h.gone, { mid: _h.mid, pid: kfo_jn(_s, "pid", -2), n: kfo_js(_s, "n", "?"), s: kfo_jn(_s, "s", 1), mh: kfo_jn(_s, "mh", 150),
                        pl: kfo_jn(_s, "pl", 0), sg: kfo_jn(_s, "sg", 0), sr: kfo_jn(_s, "sr", 0), ft: 0, hits: 0 });
                continue;
            }
            _p2.inm = 1;
            _p2.rdy = 1;
            _p2.al = kfo_jn(_s, "al", 0);
            _p2.pl = kfo_jn(_s, "pl", 0);
            _p2.hp = kfo_jn(_s, "hp", 150);
            _p2.mh = kfo_jn(_s, "mh", 150);
            _p2.g = kfo_jn(_s, "g", 0);
            _p2.sg = kfo_jn(_s, "sg", 0);
            _p2.sr = kfo_jn(_s, "sr", 0);
            _p2.t_s = current_time;
            if (_p2.bot)
                kfo_bot_reset(_p2);
        }
        var _fd = kfo_ja(_st, "fd");
        for (var _j = 0; _j < array_length(_fd); _j++)
        {
            if (is_array(_fd[_j]) && array_length(_fd[_j]) >= 2)
            {
                array_push(_h.feed, [_fd[_j][0], _fd[_j][1], (array_length(_fd[_j]) > 2) ? _fd[_j][2] : c_white]);
                _h.fseq = max(_h.fseq, _fd[_j][0]);
            }
        }
        // whoever was in the match but is not in the room any more is out now (the old host among them)
        for (var _j = 0; _j < array_length(_sp); _j++)
        {
            var _sid = kfo_jn(_sp[_j], "pid", -2);
            if (kfo_jn(_sp[_j], "al", 0) == 1 && is_undefined(kfo_host_player(_sid)))
            {
                var _gp = kfo_host_player_new(_sid, kfo_js(_sp[_j], "n", "?"), kfo_jn(_sp[_j], "s", 1), 0);
                _gp.inm = 1;
                _gp.al = 1;
                array_push(_h.pl, _gp);
                kfo_host_member("leave", _sid, "");
            }
        }
    }
    kfo_host_feed(_o.name + " is now hosting.", c_white);
    if (_o.mode == "direct")
        kfo_raw({ t: "max", n: kfo_host_cap() });
    _h.dl = true;
    _h.ds = true;
    kfo_host_check_end();
    kfo_host_flush(true);
    return _h;
}

// the host changed the settings (lobby only)
function kfo_host_set(_s)
{
    var _o = global.kfo;
    var _h = _o.H;
    if (!is_struct(_h) || _h.st != "lobby")
        return false;
    var _old = _h.set.bots;
    _h.set = kfo_set_named(_s);
    _o.set = _h.set;
    kfo_ini_save();
    if (_h.set.bots != _old || kfo_host_count_bots() != _h.set.bots)
        kfo_host_bots(_h.set.bots);
    if (_o.mode == "direct")
        kfo_raw({ t: "max", n: kfo_host_cap() });
    _h.dl = true;
    return true;
}

function kfo_host_count_bots()
{
    var _h = global.kfo.H;
    var _n = 0;
    for (var _i = 0; _i < array_length(_h.pl); _i++)
    {
        if (_h.pl[_i].bot)
            _n++;
    }
    return _n;
}

// START (host). Returns "" or why it cannot start.
function kfo_host_start()
{
    var _o = global.kfo;
    var _h = _o.H;
    if (!is_struct(_h))
        return "You are not hosting a room.";
    if (_h.st == "match")
        return "A match is already running.";
    var _in = [];
    var _humans = 0;
    var _notready = 0;
    // build 47: at most PLAYERS in the match (the room can hold WATCH PLACES more): the host, the READY players in the
    // room's order, then the bots
    for (var _pass = 0; _pass < 3; _pass++)
    {
        for (var _i = 0; _i < array_length(_h.pl); _i++)
        {
            var _p = _h.pl[_i];
            var _want = (_pass == 0) ? (_p.pid == _o.my) : ((_pass == 1) ? (!_p.bot && _p.pid != _o.my && _p.rd && _p.hi) : _p.bot);
            if (_want && array_length(_in) < max(1, _h.set.maxp))
                array_push(_in, _p);
        }
    }
    for (var _i = 0; _i < array_length(_h.pl); _i++)
    {
        var _p = _h.pl[_i];
        if (!_p.bot && _p.pid != _o.my)
        {
            _humans++;
            if (!(_p.rd && _p.hi))
                _notready++;
        }
    }
    if (!_h.prac)
    {
        if (_h.set.ready == 1 && _notready > 0)
            return "Everyone has to be READY (" + string(_notready) + " not yet).";
        if (array_length(_in) < max(2, _h.set.minp))
            return "At least " + string(max(2, _h.set.minp)) + " players have to be in (READY, or bots).";
    }
    _h.mid++;
    _h.seed = 1 + irandom(2147483000);
    // the tests pick the seed (never set in the game)
    if (variable_global_exists("kfo_test_seed") && is_numeric(global.kfo_test_seed) && global.kfo_test_seed > 0)
        _h.seed = global.kfo_test_seed;
    _h.mset = kfo_set_clean(_h.set);
    _h.eff = kbr_eff(_h.mset);
    _h.tl = kbr_tl_new(_h.seed, _h.mset);
    _h.startn = array_length(_in);
    _h.res = undefined;
    _h.feed = [];
    _h.go = false;
    _h.t0ms = 0;
    _h.t_start = current_time;
    _h.pend = [];
    _h.ftk = -1;
    _h.ft_t = -999999;
    _h.ft_done = false;
    // DRBR: Flowery's GROUP MERCY (kbr_fl_host_tick)
    _h.flg = 0;
    _h.fl_next = 0;
    _h.bc = {};
    _h.ended_t = 0;
    var _pl = [];
    for (var _i = 0; _i < array_length(_h.pl); _i++)
        _h.pl[_i].inm = 0;
    var _mhp = _h.eff.mhp;
    for (var _i = 0; _i < array_length(_in); _i++)
    {
        var _p = _in[_i];
        _p.inm = 1;
        _p.al = 1;
        _p.pl = 0;
        _p.mh = _mhp;
        _p.hp = max(1, round((_mhp * _h.eff.hp0) / 100));
        _p.g = _h.eff.g0;
        _p.ft = 0;
        _p.sg = 0;
        _p.sr = 0;
        _p.hits = 0;
        _p.sk = 0;
        _p.c = -1;
        _p.sigbad = 0;
        _p.clk = 0;
        _p.t_rs = 0;
        _p.sq = 0;
        _p.t_sk = -100000;
        _p.fh = 0;
        _p.dt = 0;
        _p.t_ls = -100000;
        _p.t_s = current_time;
        _p.t_p = 0;
        _p.outt = -1;
        _p.clks = [];
        _p.gzn = 0;
        _p.tk = 0;
        _p.hl = 0;
        _p.q = [];
        _p.qs = -1;
        _p.qh = -1;
        _p.sp = 0;
        _p.rdy = _p.bot ? 1 : 0;
        // build 48: targeting (each player's game sends its own mode as the match starts)
        kfo_host_tg_reset(_p);
        if (_p.bot)
            kfo_bot_reset(_p);
        array_push(_pl, { pid: _p.pid, n: _p.n, s: _p.s, bot: _p.bot, cl: _p.cl });
    }
    _h.st = "match";
    kfo_host_feed((_h.prac ? "* PRACTICE" : "* THE MATCH") + " BEGINS: " + string(_h.startn) + ((_h.startn == 1) ? " SOUL." : " SOULS."), c_white);
    kfo_down(0, { k: "start", mid: _h.mid, seed: _h.seed, set: _h.mset, players: _pl, prac: _h.prac ? 1 : 0, ver: kfo_version() });
    kfo_host_chat_sys("The match begins: " + string(_h.startn) + ((_h.startn == 1) ? " SOUL." : " SOULs."));
    _h.dl = true;
    _h.ds = true;
    kfo_host_flush(true);
    return "";
}

// GO: tick 0 is 1.5 s from now (the message has time to reach everyone; the countdown follows)
function kfo_host_go()
{
    var _h = global.kfo.H;
    if (_h.go)
        return 0;
    _h.go = true;
    _h.t0ms = current_time + 1500;
    kfo_down(0, { k: "go", mid: _h.mid, h: -1500 });
    return 1;
}

// the match, every step of the host's game
function kfo_host_match_tick()
{
    var _h = global.kfo.H;
    // GO when every player's battle is up (bots always are), or after 15 seconds whatever happens
    if (!_h.go)
    {
        var _all = true;
        for (var _i = 0; _i < array_length(_h.pl); _i++)
        {
            var _p = _h.pl[_i];
            if (_p.inm && !_p.rdy)
                _all = false;
        }
        if (_all || current_time - _h.t_start > 15000)
            kfo_host_go();
        return 0;
    }
    var _t = kfo_host_tick_now();
    // players whose game never came up, or went silent for 20 seconds: out
    for (var _i = 0; _i < array_length(_h.pl); _i++)
    {
        var _p = _h.pl[_i];
        if (!_p.inm || !_p.al || _p.bot || _p.pid == global.kfo.my)
            continue;
        if ((!_p.rdy && current_time - _h.t_start > 60000) || (current_time - _p.t_s > 20000))
        {
            kfo_host_out_now(_p.pid, round(_t), "lost");
            if (!is_struct(global.kfo.H) || _h.st != "match")
                return 0;
        }
    }
    kfo_host_bots_tick();
    if (_h.st != "match")
        return 0;
    kbr_fl_host_tick();
    kfo_host_tg_tick();
    kfo_host_outs_settle(false);
    if (_h.st != "match")
        return 0;
    // the time limit: the most HP wins
    if (_h.eff.tlim > 0 && _t >= _h.tl.intro + (_h.eff.tlim * 60 * 30))
    {
        kfo_host_timeup();
        return 0;
    }
    return 1;
}

// a message from player _from
function kfo_host_on(_from, _m)
{
    var _o = global.kfo;
    var _h = _o.H;
    if (!is_struct(_h) || !is_struct(_m))
        return 0;
    var _p = kfo_host_player(_from);
    if (is_undefined(_p))
        return 0;
    var _k = kfo_js(_m, "k", "");
    var _inm = (_h.st == "match" && kfo_jn(_m, "mid", -1) == _h.mid && _p.inm);
    switch (_k)
    {
        case "hi":
            var _first_hi = (_p.hi == 0);
            if (kfo_host_banned(_p.pid, ""))
            {
                kfo_down(_p.pid, { k: "kick", why: "The host removed you from this room." });
                kfo_host_member("leave", _p.pid, "");
                break;
            }
            _p.n = kfo_host_unique(kfo_clean_name(kfo_js(_m, "name", "")), _p.pid);
            _p.s = kfo_skin_ok(kfo_jn(_m, "skin", 1));
            // build 47: the SOUL colour (any whole number 0..16777215; anything else: the player's list colour)
            _p.cl = kfo_col_ok(kfo_jn(_m, "cl", -1), -1);
            _p.hi = 1;
            _h.dl = true;
            if (_h.st == "match")
                _h.ds = true;
            if (kfo_jn(_m, "ver", kfo_version()) != kfo_version())
            {
                // another build cannot share the match (its timeline and attacks differ): told why and out of the room
                kfo_down(_p.pid, { k: "kick", why: kdr_other_build(kfo_jn(_m, "ver", 0) < kfo_version(), "The room's host has") });
                kfo_host_member("leave", _p.pid, "");
            }
            else if (kfo_js(_m, "ros", kbr_roster_sig()) != kbr_roster_sig())
            {
                // build 50: the same build with another list of online knights / bosses (a modded roster): not the same match
                kfo_down(_p.pid, { k: "kick", why: "The room's host has a different list of knights and bosses." });
                kfo_host_member("leave", _p.pid, "");
            }
            else if (_first_hi)
                kfo_host_chat_joined(_p);   // build 48: the room's recent chat for them, a notice for everyone
            break;
        case "chat":
            kfo_host_chat(_p, _m);
            break;
        case "nm":
            // build 52: a new name, any time (lobby or match): the player stays the same player (pid), only the name moves
            var _old = _p.n;
            var _new = kfo_host_unique(kfo_clean_name(kfo_js(_m, "name", "")), _p.pid);
            if (_new != "" && _new != _old)
            {
                _p.n = _new;
                _h.dl = true;
                if (_h.st == "match")
                    _h.ds = true;
                kfo_host_chat_sys(_old + " is now called " + _new + ".");
            }
            break;
        case "ready":
            if (_h.st == "lobby")
            {
                _p.rd = (kfo_jn(_m, "on", 0) == 1) ? 1 : 0;
                _h.dl = true;
            }
            break;
        case "skin":
            if (_h.st == "lobby")
            {
                _p.s = kfo_skin_ok(kfo_jn(_m, "skin", 1));
                _h.dl = true;
            }
            break;
        case "look":
            // build 47: a new SOUL colour (lobby or match: it is only how the SOUL looks)
            _p.cl = kfo_col_ok(kfo_jn(_m, "cl", -1), -1);
            _h.dl = true;
            if (_h.st == "match")
                _h.ds = true;
            break;
        case "unwatch":
            _p.sp = 0;
            _h.dl = true;
            _h.ds = true;
            break;
        case "lp":
            // build 47: a player's round trip in the room (the lobby's ping column), sent every few seconds
            if (_h.st != "match" || !_p.inm)
                _p.lat = clamp(floor(kfo_jn(_m, "r", -1)), -1, 9999);
            _h.dl = true;
            break;
        case "ow":
            var _ox = kfo_jn(_m, "x", 0);
            var _oy = kfo_jn(_m, "y", 0);
            _p.ow = [clamp(_ox, -2000, 10000), clamp(_oy, -2000, 10000), clamp(floor(kfo_jn(_m, "f", 0)), 0, 3), kfo_jn(_m, "m", 0) ? 1 : 0, kfo_jn(_m, "r", -1), current_time,
                clamp(floor(kfo_jn(_m, "a", -1)), -1, 31)];
            break;
        case "pi":
            kfo_down_fast(_p.pid, { k: "po", mid: kfo_jn(_m, "mid", -1), c: kfo_jn(_m, "c", 0), h: (_h.go && _h.st == "match") ? (current_time - _h.t0ms) : -999999,
                g: (_h.go && _h.st == "match") ? 1 : 0 });
            break;
        case "rdy":
            if (_inm)
            {
                _p.rdy = 1;
                _p.t_s = current_time;
                _h.ds = true;
            }
            break;
        case "watch":
            kfo_host_watch(_p);
            break;
        case "p":
            if (_inm && _p.al)
            {
                // in tenths of a pixel (build 47)
                _p.x = clamp(kfo_jn(_m, "x", _p.x * 10) / 10, -200, 1000);
                _p.y = clamp(kfo_jn(_m, "y", _p.y * 10) / 10, -200, 1000);
                _p.hx = kfo_jn(_m, "h", 0) ? 1 : 0;
                // DRBR: Flowery's board: the orange SOUL's dash and the board's dash speed (numbers only, clamped)
                _p.fd = kfo_jn(_m, "d", 0) ? 1 : 0;
                _p.ffa = clamp(floor(kfo_jn(_m, "fa", 0)), -400, 400);
                // DRBR 1.0.1: Gerson's green shield - where it points (one of its 8 directions, -1: none)
                _p.gd = kbr_hj_dir_ok(kfo_jn(_m, "gs", -1));
                _p.t_p = current_time;
            }
            break;
        case "s":
            if (_inm)
                kfo_host_on_status(_p, _m);
            break;
        case "sk":
            if (_inm)
                kfo_host_skill(_p, _m);
            break;
        case "tg":
            if (_inm && _p.al)
                kfo_host_on_tg(_p, _m);
            break;
        case "rf":
            if (_inm)
                kfo_host_reflect(_p, _m);
            break;
        case "sg":
            if (_inm && _p.al)
            {
                var _gid = kfo_jn(_m, "sid", 0);
                if (_gid == 16)
                {
                    _p.fh++;
                    if (_p.fh > 1 || !_h.eff.fullheal)
                    {
                        _h.skills_bad++;
                        break;
                    }
                }
                if (_gid == 15)
                    _p.t_rf = current_time;
                // build 52: LIFESTEAL's time (the host forwards the heals while it lasts); DETERMINATION once a match
                if (_gid == 24)
                    _p.t_ls = current_time;
                if (_gid == 25)
                {
                    _p.dt = (variable_struct_exists(_p, "dt") ? _p.dt : 0) + 1;
                    if (_p.dt > 1)
                    {
                        _h.skills_bad++;
                        break;
                    }
                }
                // build 48: a heal makes you TIRED for a moment (PACIFY)
                if (_gid == 11 || _gid == 12 || _gid == 14 || _gid == 16)
                    _p.t_heal = current_time;
                kfo_host_feed("* " + _p.n + " used " + kbr_skill_fname(_gid) + ".", c_white);
            }
            break;
        case "dg":
            // build 52: a player was hurt by someone's send (LIFESTEAL)
            if (_inm)
                kfo_host_dealt(kfo_jn(_m, "to", -1), kfo_jn(_m, "d", 0));
            break;
        case "dsv":
            if (_inm && _p.al)
                kfo_host_feed("* " + _p.n + " refused to fall!", make_color_rgb(255, 90, 90));
            break;
        case "out":
            if (_inm)
            {
                // build 50: an out that was not a hit says why in the feed
                var _why = kfo_js(_m, "why", "");
                if (kfo_host_out_report(_p.pid, kfo_jn(_m, "t", round(kfo_host_tick_now())), "out", kfo_jn(_m, "by", -1)) && _why != "")
                    kfo_host_feed("* " + _p.n + ": " + _why + ".", c_gray);
            }
            break;
        case "quit":
            if (_inm)
                kfo_host_out_report(_p.pid, kfo_jn(_m, "t", round(kfo_host_tick_now())), "quit");
            break;
    }
    return 1;
}

// a player's status (twice a second): kept for the standings; the checks for a game out of step and impossible numbers
function kfo_host_on_status(_p, _m)
{
    var _h = global.kfo.H;
    _p.t_s = current_time;
    if (!_p.rdy)
        _p.rdy = 1;
    var _e = _h.eff;
    _p.lat = kfo_jn(_m, "lat", _p.lat);
    _p.sk = kfo_jn(_m, "sk", 0);
    // build 50: the SHIELD hits left (the others' player lists draw them in blue)
    _p.sd = clamp(floor(kfo_jn(_m, "sd", 0)), 0, 9);
    _p.skp = kfo_jn(_m, "sp", _p.skp);
    _p.tk = kfo_jn(_m, "tk", _p.tk);
    var _hl = kfo_jn(_m, "hl", _p.hl);
    if (is_numeric(_hl) && _hl > _p.hl)
        _p.t_heal = current_time;
    _p.hl = _hl;
    // build 47: the grazes so far and the skill slots (the watching HUD and the stats); only numbers pass
    _p.gzn += clamp(floor(kfo_jn(_m, "gz", 0)), 0, 200);
    var _q = kfo_ja(_m, "q");
    _p.q = [];
    for (var _i = 0; _i < array_length(_q) && _i < 4; _i++)
        array_push(_p.q, is_numeric(_q[_i]) ? clamp(floor(_q[_i]), 0, 16) : 0);
    _p.qs = clamp(floor(kfo_jn(_m, "qs", -1)), -1, 3);
    _p.qh = clamp(floor(kfo_jn(_m, "qh", -1)), -1, 16);
    // DRBR: Flowery's GROUP MERCY - this game's FLOWERY TP in his last attack
    kbr_fl_host_fm(_p, _m);
    if (!_p.al)
        return 0;
    var _hp = kfo_jn(_m, "hp", _p.hp);
    var _mh = kfo_jn(_m, "mhp", _p.mh);
    var _g = kfo_jn(_m, "g", _p.g);
    var _t = kfo_host_tick_now();
    // impossible numbers: max HP above the room's (or above what sudden death has left), HP above max HP, a gauge off 0-100
    var _cap = _e.mhp;
    var _sd0 = kbr_tl_sd_t0(_h.tl);
    if (_sd0 >= 0 && _t > _sd0)
        _cap = max(_e.sdfloor, _e.mhp - (floor((_t - _sd0) / 30) * _e.sdrate)) + (3 * _e.sdrate);
    var _fix = false;
    if (!is_numeric(_mh) || _mh > _cap || _mh < 1)
    {
        _mh = clamp(is_numeric(_mh) ? _mh : _cap, 1, _cap);
        _fix = true;
    }
    if (!is_numeric(_hp) || _hp > _mh || _hp < 0)
    {
        _hp = clamp(is_numeric(_hp) ? _hp : _mh, 0, _mh);
        _fix = true;
    }
    if (!is_numeric(_g) || _g < 0 || _g > 100)
    {
        _g = clamp(is_numeric(_g) ? _g : 0, 0, 100);
        _fix = true;
    }
    _p.hp = _hp;
    _p.mh = _mh;
    _p.g = _g;
    if (_fix)
    {
        _h.fixes++;
        kfo_down(_p.pid, { k: "fix", mid: _h.mid, hp: _hp, mhp: _mh, g: _g });
    }
    // the cycle: the same knight / attack / seed / start / extras as the host's timeline, or a resync
    _p.c = kfo_jn(_m, "c", _p.c);
    _p.t = kfo_jn(_m, "t", _p.t);
    var _sig = kfo_js(_m, "sig", "");
    if (_sig != "" && _p.c >= 0 && _p.c < 100000)
    {
        var _want = kbr_tl_sig(kbr_tl_get(_h.tl, _p.c));
        var _sig2 = kfo_js(_m, "sig2", "");
        // the next cycle too (not for 3 seconds after the final two was announced: the message may still be on its way)
        var _bad2 = (_sig2 != "" && current_time - _h.ft_t >= 3000 && kbr_tl_sig(kbr_tl_get(_h.tl, _p.c + 1)) != _sig2);
        if (_want != _sig || _bad2)
            kfo_host_resync(_p, "sig");
    }
    // the clock: how far behind the host's tick the player's reported tick arrives. A message held up on the way (a lost
    // packet sent again) looks late, so the least late of the last 8 counts; more than half a second off (after the
    // half round trip) -> the player's game measures its clock again
    if (_h.go && _p.lat >= 0 && _p.pid != global.kfo.my && is_numeric(kfo_jv(_m, "t")))
    {
        array_push(_p.clks, _t - kfo_jn(_m, "t", _t));
        if (array_length(_p.clks) > 8)
            array_delete(_p.clks, 0, 1);
        if (array_length(_p.clks) >= 6)
        {
            var _lo = _p.clks[0];
            var _hi = _p.clks[0];
            for (var _i = 1; _i < array_length(_p.clks); _i++)
            {
                _lo = min(_lo, _p.clks[_i]);
                _hi = max(_hi, _p.clks[_i]);
            }
            var _half = (_p.lat / 2) * 0.03;
            // every sample off the same way: ahead (all negative beyond the latency) or behind (all late beyond it)
            if (_hi < _half - 15 || _lo > _half + 15)
            {
                _p.clk++;
                _h.clockfix++;
                _p.clks = [];
                kfo_host_resync(_p, "clock");
            }
        }
    }
    // the bullet counts 30 / 60 / 90 frames into the attack, against the other players' for the same cycle
    var _bc = kfo_ja(_m, "bc");
    if (array_length(_bc) == 4 && is_numeric(_bc[0]))
    {
        var _key = string(_bc[0]);
        if (!variable_struct_exists(_h.bc, _key))
            variable_struct_set(_h.bc, _key, { v: [_bc[1], _bc[2], _bc[3]], n: 1, who: [_p.pid] });
        else
        {
            var _b = variable_struct_get(_h.bc, _key);
            var _seen = false;
            for (var _i = 0; _i < array_length(_b.who); _i++)
            {
                if (_b.who[_i] == _p.pid)
                    _seen = true;
            }
            if (!_seen)
            {
                array_push(_b.who, _p.pid);
                if (_b.v[0] == _bc[1] && _b.v[1] == _bc[2] && _b.v[2] == _bc[3])
                    _h.bc_same++;
                else
                    _h.bc_diff++;
            }
        }
    }
    _h.ds = true;
    return 1;
}

// tell a player to make the timeline again from the host's numbers (at most once every 2 seconds each)
function kfo_host_resync(_p, _why)
{
    var _h = global.kfo.H;
    if (current_time - _p.t_rs < 2000)
        return 0;
    _p.t_rs = current_time;
    if (_why == "sig")
    {
        _p.sigbad++;
        _h.desyncs++;
    }
    array_push(_h.log, [round(kfo_host_tick_now()), _p.pid, _why]);
    if (array_length(_h.log) > 200)
        array_delete(_h.log, 0, 1);
    kfo_down(_p.pid, { k: "rs", mid: _h.mid, seed: _h.seed, set: _h.mset, ft: _h.ftk, fp: kbr_tl_flph_list(_h.tl), h: current_time - _h.t0ms, why: _why });
    return 1;
}

// a late watcher (or a player back after losing the connection): the match is sent, read-only
// the host removes a player (KICK on the room's page): told why, out of the room, and not let back in for this room
function kfo_host_kick(_pid)
{
    var _o = global.kfo;
    var _h = _o.H;
    if (!is_struct(_h) || _pid == _o.my)
        return false;
    var _p = kfo_host_player(_pid);
    if (is_undefined(_p) || _p.bot)
        return false;
    array_push(_h.ban, { pid: _p.pid, n: _p.n });
    kfo_down(_p.pid, { k: "kick", why: "The host removed you from the room." });
    kfo_host_feed("* " + _p.n + " was removed from the room.", c_white);
    kfo_host_member("leave", _p.pid, "");
    if (_o.mode == "direct")
        kfo_raw({ t: "kick", id: _p.pid, why: "The host removed you from the room." });
    return true;
}

function kfo_host_banned(_pid, _n)
{
    var _h = global.kfo.H;
    for (var _i = 0; _i < array_length(_h.ban); _i++)
    {
        if (_h.ban[_i].pid == _pid)
            return true;
    }
    return false;
}

// who may watch the match that is running: everyone when the room has SPECTATORS on; with it off, REJOIN still lets a
// player who was in this match and lost the connection come back to watch the rest (the same account, or the same name)
function kfo_host_may_watch(_p)
{
    var _h = global.kfo.H;
    if (!is_struct(_h) || _h.st != "match" || (_p.inm && _p.al) || _p.bot)
        return false;
    if (_h.eff.spec)
        return true;
    if (!_h.eff.rejoin)
        return false;
    if (_p.inm)
        return true;
    for (var _i = 0; _i < array_length(_h.gone); _i++)
    {
        var _g = _h.gone[_i];
        if (_g.mid == _h.mid && (_g.pid == _p.pid || _g.n == _p.n))
            return true;
    }
    return false;
}

// build 47: why player _p cannot watch now ("" = they can) - the room's page shows it beside SPECTATE MATCH
function kfo_host_watch_why(_p)
{
    var _h = global.kfo.H;
    if (!is_struct(_h) || _h.st != "match")
        return "No match is running.";
    if (_p.bot)
        return "Bots do not watch.";
    if (_p.inm && _p.al)
        return "You are playing in it.";
    if (_p.sp)
        return "";
    if (kfo_host_may_watch(_p))
        return "";
    if (!_h.eff.spec)
        return "The host turned SPECTATORS off.";
    return "You cannot watch this match.";
}

// the room's watchers right now
function kfo_host_watchers()
{
    var _h = global.kfo.H;
    var _n = 0;
    for (var _i = 0; _i < array_length(_h.pl); _i++)
    {
        if (_h.pl[_i].sp)
            _n++;
    }
    return _n;
}

// how many the room holds: PLAYERS, and WATCH PLACES more when SPECTATORS is on (practice: one)
function kfo_host_cap()
{
    var _h = global.kfo.H;
    if (!is_struct(_h))
        return 8;
    return kfo_set_cap(_h.set);
}

function kfo_set_cap(_s)
{
    var _c = kfo_set_clean(_s);
    return _c.maxp + (_c.spec ? _c.sps : 0);
}

function kfo_host_watch(_p)
{
    var _h = global.kfo.H;
    if (!kfo_host_may_watch(_p))
        return 0;
    var _pl = [];
    for (var _i = 0; _i < array_length(_h.pl); _i++)
    {
        var _q = _h.pl[_i];
        if (_q.inm)
            array_push(_pl, { pid: _q.pid, n: _q.n, s: _q.s, bot: _q.bot, cl: _q.cl });
    }
    kfo_down(_p.pid, { k: "start", mid: _h.mid, seed: _h.seed, set: _h.mset, players: _pl, prac: _h.prac ? 1 : 0, spec: 1, ft: _h.ftk, fp: kbr_tl_flph_list(_h.tl), fg: round(kbr_fl_host_g() * 10),
        h: _h.go ? (current_time - _h.t0ms) : -999999, ver: kfo_version() });
    // build 47: counted as WATCHING (the room's page, the watching HUD) until they go back to the room or the match ends
    _p.sp = 1;
    _h.dl = true;
    _h.ds = true;
    return 1;
}

// ---------- skills ----------
// an attack skill: checked (in the match, alive, an attack skill the room allows, cooldown kept, never the same one twice),
// then given to every other player still standing with one seed for its pattern
function kfo_host_skill(_p, _m)
{
    var _h = global.kfo.H;
    var _e = _h.eff;
    var _id = kfo_jn(_m, "sid", 0);
    var _seq = kfo_jn(_m, "seq", 0);
    var _ok = _p.al && is_numeric(_id) && _id == floor(_id) && _id >= 1 && _id < kbr_skill_count() && _id != 16 && kbr_skill_red(_id) && _e.skills && (kbr_skill_knight(_id) < 0 || kbr_kn_has(kbr_skill_knight(_id)));
    for (var _i = 0; _ok && _i < array_length(_e.skoff); _i++)
    {
        if (_e.skoff[_i] == _id)
            _ok = false;
    }
    // never twice (a repeated message), never faster than the cooldown allows (with 20% for the network)
    if (_seq <= _p.sq)
        _ok = false;
    var _cdms = ((90 * (_e.cdm / 100)) / 30) * 1000 * 0.8;
    if (current_time - _p.t_sk < _cdms)
        _ok = false;
    if (!_ok)
    {
        _h.skills_bad++;
        return false;
    }
    _p.sq = _seq;
    _p.t_sk = current_time;
    _p.sg++;
    _h.skills_ok++;
    // build 48: a targeted room sends it to the sender's targets
    if (kbr_tg_on(_e))
    {
        kfo_host_tg_send(_p, _id, _seq);
        return true;
    }
    var _sd = 1 + irandom(2147483000);
    var _n = 0;
    for (var _i = 0; _i < array_length(_h.pl); _i++)
    {
        var _t = _h.pl[_i];
        if (!_t.inm || !_t.al || _t.pid == _p.pid)
            continue;
        _t.sr++;
        _n++;
        if (_t.bot)
            kfo_bot_skill_hit(_t, _id, _p);
        else
            kfo_down(_t.pid, { k: "ska", mid: _h.mid, from: _p.pid, fname: _p.n, sid: _id, seq: _seq, sd: _sd, rf: 0, sh: _p.sh });
    }
    // build 52: the watchers get each one too, as a targeted copy (they build the ones at the player they follow)
    for (var _w = 0; _w < array_length(_h.pl); _w++)
    {
        var _wt = _h.pl[_w];
        if (_wt.bot || (_wt.inm && _wt.al))
            continue;
        for (var _i = 0; _i < array_length(_h.pl); _i++)
        {
            var _t = _h.pl[_i];
            if (_t.inm && _t.al && _t.pid != _p.pid && !_t.bot)
                kfo_down(_wt.pid, { k: "ska", mid: _h.mid, from: _p.pid, fname: _p.n, sid: _id, seq: _seq, sd: _sd, rf: 0, sh: _p.sh, tg: [_t.pid], tm: [1] });
        }
    }
    kfo_host_feed("* " + _p.n + " sent " + kbr_skill_name(_id) + ((_n == 0) ? ". Nobody to hit." : " to everyone."), c_yellow);
    return true;
}

// Reflection sent a skill back to its sender
function kfo_host_reflect(_p, _m)
{
    var _h = global.kfo.H;
    var _to = kfo_host_player(kfo_jn(_m, "to", -1));
    var _id = kfo_jn(_m, "sid", 0);
    var _refl = ((_p.sk & 4) != 0) || (current_time - _p.t_rf < ((_h.eff.rsec + 1) * 1000));
    if (is_undefined(_to) || !_to.inm || !_to.al || !_p.al || !kbr_skill_red(_id) || !_refl)
    {
        _h.skills_bad++;
        return false;
    }
    if (_to.bot)
        kfo_bot_skill_hit(_to, _id, _p);
    else
        kfo_down(_to.pid, { k: "ska", mid: _h.mid, from: _p.pid, fname: _p.n, sid: _id, seq: kfo_jn(_m, "seq", 0), sd: 1 + irandom(2147483000), rf: 1, sh: _p.sh });
    kfo_host_feed("* " + _p.n + " reflected " + kbr_skill_name(_id) + " at " + _to.n + ".", make_color_rgb(90, 160, 255));
    return true;
}

// ---------- outs, places, ties ----------
// an out is held for a moment (another player may have fallen in the same frames), then the places are given
function kfo_host_out_report(_id, _t, _how, _by)
{
    var _h = global.kfo.H;
    var _p = kfo_host_player(_id);
    if (is_undefined(_p) || !_p.inm || !_p.al || _h.st != "match")
        return false;
    for (var _i = 0; _i < array_length(_h.pend); _i++)
    {
        if (_h.pend[_i].pid == _id)
            return false;
    }
    // build 48: the knockout's credit (the sender of the hit that ended them, or the last player who hurt them)
    if (_how == "out")
    {
        if (!is_numeric(_by) || _by < 0)
            _by = _p.lby;
        kfo_host_tg_ko(_p, _by);
    }
    if (!is_numeric(_t))
        _t = round(kfo_host_tick_now());
    array_push(_h.pend, { pid: _id, t: _t, how: _how, at: current_time });
    _p.outt = _t;
    kfo_host_chat_sys(_p.n + ((_how == "left") ? " left the match." : ((_how == "quit") ? " gave up." : " is OUT.")));
    return true;
}

// out at once (left, lost, the time limit)
function kfo_host_out_now(_id, _t, _how)
{
    kfo_host_out_report(_id, _t, _how);
    kfo_host_outs_settle(true);
}

// the outs that waited long enough get their places: outs within 10 frames of each other share the better place
// (TIE RULE "LATER WINS": only the same frame ties, the one who fell later places higher)
function kfo_host_outs_settle(_now)
{
    var _h = global.kfo.H;
    if (array_length(_h.pend) == 0)
        return 0;
    var _oldest = current_time;
    for (var _i = 0; _i < array_length(_h.pend); _i++)
        _oldest = min(_oldest, _h.pend[_i].at);
    if (!_now && current_time - _oldest < 450)
        return 0;
    var _l = _h.pend;
    _h.pend = [];
    // earliest first
    for (var _i = 1; _i < array_length(_l); _i++)
    {
        var _x = _l[_i];
        var _j = _i - 1;
        while (_j >= 0 && _l[_j].t > _x.t)
        {
            _l[_j + 1] = _l[_j];
            _j--;
        }
        _l[_j + 1] = _x;
    }
    var _win = (_h.eff.tie == 0) ? 10 : 0;
    var _i = 0;
    while (_i < array_length(_l))
    {
        var _grp = [_l[_i]];
        var _j = _i + 1;
        while (_j < array_length(_l) && _l[_j].t - _l[_i].t <= _win)
        {
            array_push(_grp, _l[_j]);
            _j++;
        }
        var _alive = kfo_host_alive();
        var _place = max(1, (_alive - array_length(_grp)) + 1);
        for (var _g = 0; _g < array_length(_grp); _g++)
        {
            var _p = kfo_host_player(_grp[_g].pid);
            if (is_undefined(_p) || !_p.al)
                continue;
            _p.al = 0;
            _p.pl = _place;
            _p.hp = 0;
            _p.ft = max(0, _grp[_g].t - _h.tl.intro);
            var _txt = "* " + _p.n + " is OUT (#" + string(_place) + ")";
            if (_grp[_g].how == "left")
                _txt = "* " + _p.n + " left the match (#" + string(_place) + ")";
            else if (_grp[_g].how == "quit")
                _txt = "* " + _p.n + " gave up (#" + string(_place) + ")";
            else if (_grp[_g].how == "lost")
                _txt = "* " + _p.n + " lost the connection (#" + string(_place) + ")";
            kfo_host_feed(_txt, c_red);
        }
        _i = _j;
    }
    _h.ds = true;
    // build 47: the room's list too (each one's place, ALIVE / OUT, and whether they may SPECTATE now)
    _h.dl = true;
    kfo_host_check_end();
    return 1;
}

function kfo_host_check_end()
{
    var _h = global.kfo.H;
    if (!is_struct(_h) || _h.st != "match")
        return false;
    var _n = kfo_host_alive();
    // the final two: announced once, for a cycle a little ahead so every game makes it with the showdown
    if (_h.go && _n == 2 && _h.startn > 2 && !_h.ft_done)
    {
        _h.ft_done = true;
        var _ck = kbr_tl_at(_h.tl, kfo_host_tick_now() + KBR_ARM + 30) + 1;
        _h.ftk = _ck;
        _h.ft_t = current_time;
        kbr_tl_set_ft(_h.tl, _ck);
        kfo_down(0, { k: "ft", mid: _h.mid, ck: _ck });
        if (_h.eff.ft)
            kfo_host_feed("* FINAL TWO!", c_red);
    }
    if ((_h.startn >= 2 && _n <= 1) || _n == 0)
    {
        // practice alone: only when you are out
        kfo_host_end();
        return true;
    }
    return false;
}

// the time limit ran out: the most HP (in percent) wins; ties share the place
function kfo_host_timeup()
{
    var _h = global.kfo.H;
    var _left = [];
    for (var _i = 0; _i < array_length(_h.pl); _i++)
    {
        var _p = _h.pl[_i];
        if (_p.inm && _p.al)
            array_push(_left, _p);
    }
    for (var _i = 1; _i < array_length(_left); _i++)
    {
        var _x = _left[_i];
        var _j = _i - 1;
        while (_j >= 0 && (_left[_j].hp / max(1, _left[_j].mh)) < (_x.hp / max(1, _x.mh)))
        {
            _left[_j + 1] = _left[_j];
            _j--;
        }
        _left[_j + 1] = _x;
    }
    kfo_host_feed("* TIME! The most HP wins.", c_white);
    var _place = 1;
    for (var _i = 0; _i < array_length(_left); _i++)
    {
        if (_i > 0 && (_left[_i].hp / max(1, _left[_i].mh)) < (_left[_i - 1].hp / max(1, _left[_i - 1].mh)))
            _place = _i + 1;
        _left[_i].pl = _place;
        _left[_i].ft = round(kfo_host_tick_now() - _h.tl.intro);
        if (_place > 1)
            _left[_i].al = 0;
    }
    kfo_host_end();
}

function kfo_host_end()
{
    var _o = global.kfo;
    var _h = _o.H;
    var _wid = [];
    var _wn = "";
    var _dur = max(0, round(kfo_host_tick_now() - _h.tl.intro));
    // the ones still standing are 1st; when nobody is (the last ones fell together) the best place is
    for (var _i = 0; _i < array_length(_h.pl); _i++)
    {
        var _p = _h.pl[_i];
        if (_p.inm && _p.al)
        {
            _p.pl = 1;
            _p.ft = _dur;
        }
    }
    var _res = [];
    for (var _i = 0; _i < array_length(_h.pl); _i++)
    {
        var _p = _h.pl[_i];
        if (_p.inm)
        {
            array_push(_res, { pid: _p.pid, n: _p.n, s: _p.s, pl: _p.pl, al: _p.al, ft: _p.ft, sg: _p.sg, sr: _p.sr, bot: _p.bot });
            if (_p.pl == 1)
            {
                array_push(_wid, _p.pid);
                _wn = (_wn == "") ? _p.n : (_wn + " & " + _p.n);
            }
        }
    }
    for (var _i = 0; _i < array_length(_h.gone); _i++)
    {
        var _g = _h.gone[_i];
        if (_g.mid == _h.mid)
            array_push(_res, { pid: _g.pid, n: _g.n, s: _g.s, pl: _g.pl, al: 0, ft: _g.ft, sg: _g.sg, sr: _g.sr, bot: 0 });
    }
    // by place (1 first)
    for (var _i = 1; _i < array_length(_res); _i++)
    {
        var _x = _res[_i];
        var _j = _i - 1;
        while (_j >= 0 && ((_res[_j].pl == 0 && _x.pl > 0) || (_x.pl > 0 && _res[_j].pl > _x.pl)))
        {
            _res[_j + 1] = _res[_j];
            _j--;
        }
        _res[_j + 1] = _x;
    }
    if (array_length(_wid) == 0)
        kfo_host_feed("* NOBODY IS LEFT STANDING.", c_white);
    else if (array_length(_wid) > 1)
        kfo_host_feed("* A TIE! " + _wn + " WIN!", c_yellow);
    else
        kfo_host_feed("* " + _wn + " WINS!", c_yellow);
    _h.res = { mid: _h.mid, wid: _wid, wn: _wn, pl: _res, sn: _h.startn, dur: _dur, prac: _h.prac ? 1 : 0 };
    kfo_down(0, kfo_host_state_msg());
    kfo_down(0, { k: "end", mid: _h.mid, wid: _wid, wn: _wn, pl: _res, sn: _h.startn, dur: _dur, prac: _h.prac ? 1 : 0 });
    kfo_host_chat_sys("The match is over: " + ((array_length(_wid) == 0) ? "nobody is left standing." : (_wn + ((array_length(_wid) > 1) ? " win (a tie)." : " wins."))));
    _h.st = "lobby";
    _h.gone = [];
    _h.go = false;
    _h.ended_t = current_time;
    for (var _i = 0; _i < array_length(_h.pl); _i++)
    {
        var _p = _h.pl[_i];
        // build 52: READY stays as each player left it (it was cleared after every match, so whoever had not pressed READY
        // again was left out of the next START and put to watching - in a room of two, always the other player)
        _p.inm = 0;
        _p.al = 0;
        _p.sp = 0;
    }
    _h.ds = false;
    _h.dl = true;
    kfo_host_flush(true);
    return true;
}

// ---------- bots: SOULs in the host's own box that dodge the real bullets ----------
function kfo_bot_reset(_b)
{
    // ax / ay: the spot of the box this bot likes to stand on (each its own, so the bots do not all crowd the middle and fall
    // to the same bullet together); it moves now and then
    // build 49: the smart bots (online_bots.gml): buffs, skills, the danger of its last move
    _b.bt = { x: 320, y: 240, ix: 0, iy: 0, inv: 0, think: 0, tx: 0, ty: 0, alive_f: 0, gz: 0, skt: 120 + irandom(240), placed: false,
        ax: 0.2 + random(0.6), ay: 0.2 + random(0.6), lk: 0, owe: false, slow_t: 0, conf_t: 0, shield: 0, shield_t: 0, regen_t: 0, danger: 0, sk: kfo_bot_skill_new(), dark_t: 0, ls_t: 0, det_t: 0 };
    return _b;
}

// the box the bots are in: the host's own (the same box everyone has); undefined between two attacks
// build 50: a knight's Roaring (its finale) on screen: obj_knight_roaring2, the Violet Knight's obj_knight_roaring3
function kfo_bot_roaring()
{
    if (instance_exists(obj_knight_roaring2))
        return instance_find(obj_knight_roaring2, 0);
    // (the Violet Knight's by name: every merged game has it, a game without it simply has no such Roaring)
    var _r3 = asset_get_index("obj_knight_roaring3");
    if (_r3 >= 0 && instance_exists(_r3))
        return instance_find(_r3, 0);
    return noone;
}

function kfo_bot_box()
{
    // build 52: Jevil's BYE-BYE takes the box away: the SOUL has the screen (as a player's)
    if (kbr_jv_boxless())
        return [camerax() + 10, cameray() + 10, camerax() + 630, cameray() + 470];
    // build 50: in a Roaring the box first swells past the screen, then shrinks to nothing before the final slash - the SOUL
    // is held inside the screen instead (the Roaring's own clamp: camera x .. x + width - 20, y .. y + height - 20, its corner)
    if (kfo_bot_roaring() != noone)
    {
        var _cx = camerax();
        var _cy = cameray();
        var _cw = camerawidth();
        var _ch = cameraheight();
        if (_cw < 100 || _ch < 100)
        {
            _cw = 640;
            _ch = 480;
        }
        return [_cx + 10, _cy + 10, (_cx + _cw) - 10, (_cy + _ch) - 10];
    }
    var _b = instance_exists(obj_growtangle) ? instance_find(obj_growtangle, 0) : noone;
    // (build 49: no upper limit - the real arena's box is at x 2000+; build 48 took it for "no box" and the bots never moved)
    if (_b != noone && _b.x > -1000)
    {
        var _hw = max(12, (abs(_b.sprite_width) / 2) - 8);
        var _hh = max(12, (abs(_b.sprite_height) / 2) - 8);
        return [_b.x - _hw, _b.y - _hh, _b.x + _hw, _b.y + _hh];
    }
    // the box split in two (the battle box itself is moved away meanwhile): the bots stay inside what the halves cover
    var _x0 = 999999;
    var _y0 = 999999;
    var _x1 = -999999;
    var _y1 = -999999;
    var _sp = kbr_split_objs();
    for (var _i = 0; _i < array_length(_sp); _i++)
    {
        with (_sp[_i])
        {
            if (x > -1000)
            {
                var _w = max(12, (abs(sprite_width) / 2) - 8);
                var _h = max(12, (abs(sprite_height) / 2) - 8);
                if (sprite_index < 0)
                {
                    _w = 62;
                    _h = 62;
                }
                _x0 = min(_x0, x - _w);
                _y0 = min(_y0, y - _h);
                _x1 = max(_x1, x + _w);
                _y1 = max(_y1, y + _h);
            }
        }
    }
    if (_x1 < _x0)
        return undefined;
    return [_x0, _y0, _x1, _y1];
}

// the danger at point _x,_y: bullets near it (and where they will be in a few frames)
function kfo_bot_danger(_x, _y, _r, _look)
{
    var _d = 0;
    with (obj_bulletparent)
    {
        // not the box's own split halves (they hold the SOULs, they are not bullets to run from)
        if ((!(variable_instance_exists(id, "kbr") && kbr != 0) || (is_struct(global.kfo.H) && kbr_tg_on(global.kfo.H.eff))) && string_pos("growtangle", object_get_name(object_index)) == 0)
        {
            var _bx = x + (hspeed * _look);
            var _by = y + (vspeed * _look);
            var _dist = point_distance(_x, _y, _bx, _by);
            if (_dist < _r)
                _d += (_r - _dist) / _r;
            var _d0 = point_distance(_x, _y, x, y);
            if (_d0 < _r * 0.6)
                _d += 1;
        }
    }
    return _d;
}

// a bot is hit when a bullet touches its SOUL (8 x 8 around its middle): the engine's own precise collision, as for your
// SOUL (a rough box test made the battle box's split halves count as one big bullet over every bot)
function kfo_bot_hit_by(_x, _y, _self)
{
    var _tgr = is_struct(global.kfo.H) && kbr_tg_on(global.kfo.H.eff);
    var _hit = noone;
    var _l = ds_list_create();
    // build 49: the same hitbox as a player's SOUL (the host's own SOUL's box)
    var _hb = kfo_bot_hit_half();
    // build 49: only what can hurt a player's SOUL - Chapter 3's obj_heart takes damage from obj_collidebullet (and its
    // children) while active == 1 (obj_heart's collision event); other bullet objects (obj_heart_follower, markers) never
    var _n = collision_rectangle_list(_x - _hb[0], _y - _hb[1], _x + _hb[0], _y + _hb[1], obj_collidebullet, true, false, _l, false);
    for (var _i = 0; _i < _n && _hit == noone; _i++)
    {
        // ds_list_find_value, not the [| ] accessor: the compiler the mod is built with drops ds accessors (it made
        // them plain array reads, an error in the game)
        var _b = ds_list_find_value(_l, _i);
        if (!instance_exists(_b))
            continue;
        // the players' attack skills: only in a targeted room (they hurt anyone there), never the bot's own
        if (variable_instance_exists(_b, "kbr") && _b.kbr != 0 && (!_tgr || !variable_instance_exists(_b, "kbrf") || _b.kbrf == _self))
            continue;
        // (the host's own sends are never active in the host's game - they cannot hurt the host - but they do hit the bots:
        // live once they stopped waiting)
        if (variable_instance_exists(_b, "kbr") && _b.kbr != 0 && variable_instance_exists(_b, "wait"))
        {
            if (_b.wait > 0 || _b.life <= 0)
                continue;
        }
        else if (variable_instance_exists(_b, "active") && _b.active != 1)
            continue;
        // DRBR: Spamton NEO's walls are played by the odds (kbr_sn_bot_walls: a bot cannot shoot its way through)
        if (kbr_sn_bot_skip(_b))
            continue;
        // build 50: the stars (and the splitter's slash) hit a SOUL only on a precise test around its middle (scr_precise_hit:
        // the Roaring's stars 2 px, 1 px for the smaller SOUL) - not on the SOUL's whole box: the same test for a bot
        var _pr = kfo_bot_precise(_b);
        if (_pr >= 0)
        {
            var _pa = _pr / 2;
            var _ph = (_pa <= 0) ? collision_point(_x, _y, _b, true, false) : collision_rectangle(_x - _pa, _y - _pa, _x + _pa, _y + _pa, _b, true, false);
            if (_ph == noone)
                continue;
        }
        _hit = _b;
    }
    ds_list_destroy(_l);
    return _hit;
}

// the precise hitbox a bullet uses on a SOUL (its event 15's scr_precise_hit argument), -1: the SOUL's box
function kfo_bot_precise(_b)
{
    var _n = object_get_name(_b.object_index);
    var _small = instance_exists(obj_heart) && instance_find(obj_heart, 0).sprite_index == spr_dodgeheart_smaller_2px;
    if (_n == "obj_knight_roaring_star")
        return _small ? 0 : 2;
    if (_n == "obj_knight_pointing_starchild" || _n == "obj_knight_pointing_starchild_Copy")
    {
        if (kfo_bot_roaring() != noone)
            return _small ? 0 : 2;
        return _small ? 1 : 5;
    }
    if (_n == "obj_knight_pointing_star" || _n == "obj_knight_pointing_star_Copy" || _n == "obj_roaringknight_splitslash" || _n == "obj_roaringknight_splitslash_Copy")
        return 3;
    return -1;
}

// an attack skill hits a bot: it loses some HP (it cannot dodge what only its owner would see)
function kfo_bot_skill_hit(_b, _id, _from)
{
    var _h = global.kfo.H;
    if (!is_struct(_b.bt))
        kfo_bot_reset(_b);
    // REFLECTION: back to the sender
    if (current_time - _b.t_rf < ((_h.eff.rsec + 1) * 1000) && _from.pid != _b.pid)
    {
        kfo_host_feed("* " + _b.n + " reflected " + kbr_skill_name(_id) + " at " + _from.n + ".", make_color_rgb(90, 160, 255));
        if (_from.bot)
            return kfo_bot_skill_hit(_from, _id, _b);
        kfo_down(_from.pid, { k: "ska", mid: _h.mid, from: _b.pid, fname: _b.n, sid: _id, seq: 0, sd: 1 + irandom(2147483000), rf: 1, sh: _b.sh });
        return 1;
    }
    // SLOW / CONFUSE / DARKNESS / LOCK on a bot: as on a player
    kfo_bot_fx(_b, _id, 1);
    // build 52: 22-25 deal no damage (the table used to give any id past its end the last number)
    var _tab = [0, 12, 16, 10, 8, 8, 10, 8, 0, 0, 24, 0, 0, 0, 0, 0, 0, 10, 12, 8, 8, 10];
    var _dmg = (_id >= 0 && _id < array_length(_tab)) ? _tab[_id] : 0;
    _dmg = round(_dmg * (_h.eff.skdmg / 100) * (_h.eff.dmul / 100) * (0.5 + random(0.5)));
    if (_dmg <= 0)
        return 0;
    var _took = kfo_bot_take(_b, _dmg);
    _b.lby = _from.pid;
    kfo_host_dealt(_from.pid, _took);
    if (_b.hp <= 0)
        kfo_host_out_report(_b.pid, round(kfo_host_tick_now()), "out", _from.pid);
    return 1;
}


// build 52: an effect skill on a bot (_mul: a stronger send lasts longer) - SLOW, CONFUSE, DARKNESS (it only sees the bullets
// close to it), LOCK (no skills for 6 seconds)
function kfo_bot_fx(_b, _id, _mul)
{
    if (!is_struct(_b.bt))
        kfo_bot_reset(_b);
    var _s = _b.bt;
    switch (_id)
    {
        case 8: _s.slow_t = round(150 * _mul); break;
        case 9: _s.conf_t = round(120 * _mul); break;
        case 22: _s.dark_t = round(150 * _mul); break;
        case 23: _s.sk.cd = max(_s.sk.cd, round(180 * _mul)); break;
    }
    return 1;
}

// build 52: LIFESTEAL - player or bot _pid's send took _d HP from someone: while its LIFESTEAL lasts it gets a quarter back
// (a player is told; a bot heals here)
function kfo_host_dealt(_pid, _d)
{
    var _h = global.kfo.H;
    if (!is_struct(_h) || !is_numeric(_d) || _d <= 0)
        return 0;
    var _p = kfo_host_player(_pid);
    if (is_undefined(_p) || !_p.inm || !_p.al)
        return 0;
    if (_p.bot)
    {
        if (is_struct(_p.bt) && variable_struct_exists(_p.bt, "ls_t") && _p.bt.ls_t > 0)
            _p.hp = min(_p.mh, _p.hp + max(1, round(_d * 0.25 * (_h.eff.hmul / 100))));
        return 1;
    }
    if (!variable_struct_exists(_p, "t_ls") || current_time - _p.t_ls > 11000)
        return 0;
    kfo_down(_p.pid, { k: "lsh", mid: _h.mid, d: round(_d) });
    return 1;
}
