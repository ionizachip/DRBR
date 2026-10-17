
// ===== Build 45: KNIGHT FIGHTS ONLINE over Steam (kf_steam.dll, app 480 "Spacewar") =====
// Chapter 3's runner has no Steam functions, so Knight Fights brings its own small DLL (kf_steam.dll, next to the game) that
// talks to Steam's own steam_api64.dll. A room is a Steam lobby: its owner is the host (Steam picks the next owner when
// the host leaves), its members are the players (their Steam account IDs are their player IDs), and the game's messages go
// as Steam peer-to-peer packets (reliable and in order, or unreliable for the SOUL positions) - the same messages as over
// the relay. Room codes are 7 letters made from the lobby's ID; joining by code looks the lobby up first and checks that it
// is a Knight Fights room of the same build.
// Everything here fails soft: no DLL, no steam_api64.dll, Steam not running -> the STEAM rows say why and the relay and
// practice work as before.

global.kfo_stm = undefined;

function kfo_steam_fn_list()
{
    // name, return type (0 real, 1 string), argument types (0 real, 1 string)
    return [
        ["kf_init", 0, []], ["kf_status", 1, []], ["kf_my_acct", 0, []], ["kf_my_name", 1, []], ["kf_name", 1, [0]],
        ["kf_lobby_create", 0, [0, 0]], ["kf_lobby_find", 0, [1]], ["kf_lobby_find_id", 0, [1]], ["kf_lobby_join_id", 0, [1]],
        ["kf_lobby_leave", 0, []], ["kf_lobby_id", 1, []], ["kf_lobby_code", 1, []], ["kf_lobby_owner", 0, []], ["kf_lobby_count", 0, []],
        ["kf_lobby_member", 0, [0]], ["kf_lobby_set", 0, [1, 1]], ["kf_lobby_get", 1, [1]], ["kf_lobby_joinable", 0, [0]],
        ["kf_lobby_limit", 0, [0]], ["kf_browse", 0, []], ["kf_browse_count", 0, []], ["kf_browse_info", 1, [0]], ["kf_found_info", 1, []],
        ["kf_invite_overlay", 0, []], ["kf_overlay_on", 0, []], ["kf_send", 0, [0, 1, 0]], ["kf_recv", 1, []], ["kf_recv_from", 0, []],
        ["kf_poll", 1, []], ["kf_launch_lobby", 1, []], ["kf_shutdown", 0, []]
    ];
}

// load the DLL once (the first time the ONLINE page asks): every function or nothing
function kfo_steam_load()
{
    if (is_struct(global.kfo_stm))
        return global.kfo_stm;
    var _s = { ok: false, init: 0, why: "", fns: {}, dll: "" };
    global.kfo_stm = _s;
    var _cands = [working_directory + "kf_steam.dll", "kf_steam.dll"];
    var _found = false;
    for (var _c = 0; _c < array_length(_cands) && !_found; _c++)
    {
        var _path = _cands[_c];
        if (_c == 0 && !file_exists(_path))
            continue;
        var _fns = {};
        var _all = true;
        var _l = kfo_steam_fn_list();
        for (var _i = 0; _i < array_length(_l); _i++)
        {
            var _e = _l[_i];
            var _id = -1;
            try
            {
                switch (array_length(_e[2]))
                {
                    case 0: _id = external_define(_path, _e[0], dll_cdecl, _e[1] ? ty_string : ty_real, 0); break;
                    case 1: _id = external_define(_path, _e[0], dll_cdecl, _e[1] ? ty_string : ty_real, 1, _e[2][0] ? ty_string : ty_real); break;
                    case 2: _id = external_define(_path, _e[0], dll_cdecl, _e[1] ? ty_string : ty_real, 2, _e[2][0] ? ty_string : ty_real, _e[2][1] ? ty_string : ty_real); break;
                    case 3: _id = external_define(_path, _e[0], dll_cdecl, _e[1] ? ty_string : ty_real, 3, _e[2][0] ? ty_string : ty_real, _e[2][1] ? ty_string : ty_real, _e[2][2] ? ty_string : ty_real); break;
                }
            }
            catch (_err)
            {
                _id = -1;
            }
            if (is_real(_id) && _id < 0)
            {
                _all = false;
                break;
            }
            variable_struct_set(_fns, _e[0], _id);
        }
        if (_all)
        {
            _found = true;
            _s.fns = _fns;
            _s.dll = _path;
            // build 49: the friends list and direct invites (only in build 49's DLL; optional)
            kfo_steam_opt_load(_s, _path);
        }
    }
    if (!_found)
    {
        _s.why = kdr_on() ? "kf_steam.dll is missing (DRBR Launcher > Repair Installation)." : "kf_steam.dll is missing (run PLAY_KNIGHT_HUB.bat again).";
        return _s;
    }
    var _r = kfo_sx("kf_init");
    _s.init = _r;
    _s.ok = (_r == 1);
    if (!_s.ok)
    {
        var _st = kfo_sx("kf_status");
        if (_r == 0)
            _s.why = "steam_api64.dll is missing next to the game.";
        else if (_r == -1)
            _s.why = "Steam is not running or not signed in" + ((is_string(_st) && _st != "") ? (": " + _st) : ".");
        else
            _s.why = "Steam could not start (" + (is_string(_st) ? _st : string(_r)) + ").";
    }
    return _s;
}

// call a DLL function by name (undefined when it is not there)
function kfo_sx(_name)
{
    var _s = global.kfo_stm;
    if (!is_struct(_s) || !variable_struct_exists(_s.fns, _name))
        return undefined;
    var _id = variable_struct_get(_s.fns, _name);
    switch (argument_count)
    {
        case 1: return external_call(_id);
        case 2: return external_call(_id, argument[1]);
        case 3: return external_call(_id, argument[1], argument[2]);
        case 4: return external_call(_id, argument[1], argument[2], argument[3]);
    }
    return undefined;
}

function kfo_steam_ready()
{
    var _s = kfo_steam_load();
    return _s.ok;
}

function kfo_steam_why()
{
    var _s = kfo_steam_load();
    return _s.ok ? "" : _s.why;
}

function kfo_steam_why_short()
{
    var _s = kfo_steam_load();
    if (_s.ok)
        return "READY";
    if (string_pos("kf_steam.dll", _s.why) > 0)
        return "NOT INSTALLED";
    if (string_pos("steam_api64", _s.why) > 0)
        return "STEAM_API64.DLL MISSING";
    return "STEAM IS NOT RUNNING";
}

function kfo_steam_name()
{
    if (!kfo_steam_ready())
        return "";
    var _n = kfo_sx("kf_my_name");
    return is_string(_n) ? string_upper(kfo_clean_name(_n)) : "";
}

// ---------- making / finding / joining a room ----------
function kfo_steam_begin(_want)
{
    var _o = kfo_get();
    kfo_close("");
    _o.M = undefined;
    _o.mode = "steam";
    _o.want = _want;
    _o.st = "joining";
    _o.t_conn = current_time;
    _o.t_rx = current_time;
    _o.err = "";
    _o.stm = { lobby: "", found: "", t_find: 0, t_host: current_time, members_n: 0 };
    return _o;
}

function kfo_steam_host()
{
    if (!kfo_steam_ready())
        return kfo_fail(kfo_steam_why());
    var _o = kfo_steam_begin("create");
    var _type = clamp(_o.vis, 0, 2);
    if (!kfo_sx("kf_lobby_create", _type, kfo_set_cap(_o.set)))
        return kfo_fail("Steam did not make the room.");
    kfo_log("steam: creating a lobby");
    return true;
}

// a code (7 letters) -> the lobby is looked up (found:... comes back), checked, then joined
function kfo_steam_join_code(_code)
{
    if (!kfo_steam_ready())
        return kfo_fail(kfo_steam_why());
    var _o = kfo_steam_begin("find");
    _o.wcode = _code;
    _o.stm.t_find = current_time;
    if (!kfo_sx("kf_lobby_find", _code))
        return kfo_fail("That is not a room code.");
    return true;
}

// a lobby from BROWSE (already checked there) or an invite (checked first)
function kfo_steam_join_id(_id)
{
    if (!kfo_steam_ready())
        return kfo_fail(kfo_steam_why());
    var _o = kfo_steam_begin("join");
    _o.stm.lobby = _id;
    if (!kfo_sx("kf_lobby_join_id", _id))
        return kfo_fail("Steam did not let us in.");
    return true;
}

function kfo_steam_join_checked(_id)
{
    if (!kfo_steam_ready())
        return kfo_fail(kfo_steam_why());
    var _o = kfo_steam_begin("find");
    _o.stm.t_find = current_time;
    if (!kfo_sx("kf_lobby_find_id", _id))
        return kfo_fail("Steam could not find that room.");
    return true;
}

function kfo_steam_browse()
{
    var _o = kfo_get();
    _o.browse = [];
    if (!kfo_steam_ready())
    {
        _o.browse_st = kfo_steam_why();
        return false;
    }
    _o.browse_st = "LOOKING FOR PUBLIC ROOMS...";
    _o.browse_t = current_time;
    kfo_sx("kf_browse");
    return true;
}

function kfo_steam_invite()
{
    if (!kfo_steam_ready() || global.kfo.mode != "steam" || !kfo_in_room())
        return false;
    if (!kfo_sx("kf_overlay_on"))
        return false;
    return kfo_sx("kf_invite_overlay") == 1;
}

function kfo_steam_close()
{
    if (is_struct(global.kfo_stm) && global.kfo_stm.ok)
        kfo_sx("kf_lobby_leave");
    return 0;
}

// the host writes what BROWSE and a code lookup show
function kfo_steam_lobby_meta()
{
    var _o = global.kfo;
    if (_o.mode != "steam" || !kfo_is_host() || !is_struct(_o.H))
        return 0;
    var _h = _o.H;
    kfo_sx("kf_lobby_set", "kfgame", "kfo");
    kfo_sx("kf_lobby_set", "ver", string(kfo_version()));
    kfo_sx("kf_lobby_set", "name", _o.name);
    kfo_sx("kf_lobby_set", "st", _h.st);
    kfo_sx("kf_lobby_set", "np", string(array_length(_h.pl)));
    kfo_sx("kf_lobby_set", "mx", string(kfo_host_cap()));
    kfo_sx("kf_lobby_set", "pre", _h.set.pre);
    kfo_sx("kf_lobby_limit", kfo_host_cap());
    return 1;
}

function kfo_steam_members_refresh()
{
    var _o = global.kfo;
    var _l = [];
    var _n = kfo_sx("kf_lobby_count");
    for (var _i = 0; _i < _n; _i++)
    {
        var _a = kfo_sx("kf_lobby_member", _i);
        if (_a > 0)
            array_push(_l, { pid: _a, name: kfo_clean_name(kfo_sx("kf_name", _a)) });
    }
    _o.members = _l;
    return _l;
}

// ---------- every step: Steam's events, then the packets ----------
function kfo_steam_tick()
{
    var _o = global.kfo;
    if (!is_struct(global.kfo_stm) || !global.kfo_stm.ok)
        return 0;
    var _n = 0;
    while (_n < 64)
    {
        var _ev = kfo_sx("kf_poll");
        if (!is_string(_ev) || _ev == "")
            break;
        _n++;
        kfo_steam_event(_ev);
        if (!is_struct(global.kfo) || global.kfo != _o)
            return 0;
    }
    // packets (at most 256 a step)
    _n = 0;
    while (_n < 256 && _o.mode == "steam")
    {
        var _txt = kfo_sx("kf_recv");
        if (!is_string(_txt) || _txt == "")
            break;
        _n++;
        var _from = kfo_sx("kf_recv_from");
        kfo_steam_packet(_from, _txt);
        if (!is_struct(global.kfo) || global.kfo != _o)
            return 0;
    }
    // time-outs: a lookup that never answers, a host that went quiet
    if (_o.mode == "steam")
    {
        if (_o.st == "joining" && current_time - _o.t_conn > 15000)
            kfo_fail((_o.want == "find") ? "No DRBR room with that code (it may be private)." : "Steam did not answer.");
        else if (_o.st == "room" && !kfo_is_host() && current_time - _o.t_rx > 20000)
            kfo_lost("The host stopped answering.");
    }
    return 1;
}

function kfo_steam_event(_ev)
{
    var _o = global.kfo;
    var _p = string_pos(":", _ev);
    var _k = (_p > 0) ? string_copy(_ev, 1, _p - 1) : _ev;
    var _v = (_p > 0) ? string_copy(_ev, _p + 1, string_length(_ev) - _p) : "";
    kfo_log("steam: " + _ev);
    // only BROWSE and an accepted invite matter outside a Steam room (or a Steam lookup / join in progress)
    if (_o.mode != "steam" && _k != "browse" && _k != "join_request" && _k != "invited")
        return 0;
    switch (_k)
    {
        case "joined":
            if (_o.mode != "steam")
                return 0;
            _o.st = "room";
            _o.err = "";
            _o.t_rx = current_time;
            _o.code = kfo_sx("kf_lobby_code");
            _o.my = kfo_sx("kf_my_acct");
            _o.hostid = kfo_sx("kf_lobby_owner");
            kfo_steam_members_refresh();
            _o.lastcode = _o.code;
            kfo_ini_save();
            if (_o.hostid == _o.my)
                kfo_host_begin(_o.code, false);
            else
                kfo_up({ k: "hi", name: _o.name, skin: _o.skin, ver: kfo_version(), ros: kbr_roster_sig(), cl: _o.look.col });
            break;
        case "create_failed":
            kfo_fail("Steam could not make the room (" + _v + ").");
            break;
        case "join_failed":
            kfo_fail(kfo_steam_join_why(kfo_num(_v, 0)));
            break;
        case "found":
            // id|ver|np|mx|st|name
            var _f = kfo_split(_v, "|");
            if (array_length(_f) < 6 || _o.want != "find")
                break;
            var _ver = kfo_num(_f[1], 0);
            if (_ver != kfo_version())
            {
                // DRBR (update 10): a room with a newer build is kept for after the update (kdr_pending_join)
                if (_ver > kfo_version())
                    kdr_pending_join(_f[0], _ver, (array_length(_f) > 5) ? _f[5] : "");
                kfo_fail(kdr_on() ? kdr_build_why(_ver) : ((_ver < kfo_version()) ? "That room's players have an older Knight Hub build (Client Is Newer)." : "That room's players have a newer Knight Hub build (Client Is Older)."));
                break;
            }
            if (kfo_num(_f[2], 0) >= kfo_num(_f[3], 8))
            {
                kfo_fail("That room is full.");
                break;
            }
            _o.want = "join";
            _o.stm.lobby = _f[0];
            if (!kfo_sx("kf_lobby_join_id", _f[0]))
                kfo_fail("Steam did not let us in.");
            break;
        case "notfound":
            if (_o.want == "find")
                kfo_fail("No DRBR room with that code (it may be private or gone).");
            break;
        case "invited":
            // build 49: a friend invited us (their game's INVITE page): the invite box / line
            kfo_inv_in(_v);
            break;
        case "join_request":
            // a friend's invite was accepted (Steam overlay / friends list): leave the room we are in, check the new one, join
            if (kfo_in_room())
                kfo_leave();
            kfo_steam_join_checked(_v);
            break;
        case "member_in":
            if (_o.st == "room")
            {
                var _acc = kfo_num(_v, 0);
                kfo_steam_members_refresh();
                if (kfo_is_host())
                    kfo_host_member("join", _acc, kfo_sx("kf_name", _acc));
            }
            break;
        case "member_out":
            if (_o.st == "room")
            {
                var _acc2 = kfo_num(_v, 0);
                kfo_steam_members_refresh();
                if (kfo_is_host())
                    kfo_host_member("leave", _acc2, "");
            }
            break;
        case "owner":
            if (_o.st == "room")
            {
                var _own = kfo_num(_v, 0);
                if (_own > 0 && _own != _o.hostid)
                {
                    kfo_steam_members_refresh();
                    kfo_on_promote(_own, _o.members);
                }
            }
            break;
        case "left":
            if (_o.st == "room")
                kfo_lost("You left the Steam room.");
            break;
        case "browse":
            _o.browse = [];
            var _bn = kfo_num(_v, 0);
            for (var _i = 0; _i < _bn && _i < 50; _i++)
            {
                var _b = kfo_split(kfo_sx("kf_browse_info", _i), "|");
                if (array_length(_b) < 7)
                    continue;
                array_push(_o.browse, { lid: _b[0], code: _b[1], host: kfo_clean_name(_b[2]), np: kfo_num(_b[3], 0), mx: max(1, kfo_num(_b[4], 8)),
                    ver: kfo_num(_b[5], 0), st: (_b[6] == "match") ? "match" : "lobby" });
            }
            _o.browse_st = (array_length(_o.browse) == 0) ? "" : (string(array_length(_o.browse)) + " PUBLIC ROOM" + ((array_length(_o.browse) == 1) ? "" : "S") + ".");
            break;
        case "p2p_fail":
            kfo_log("steam: no connection to " + _v);
            break;
    }
    return 1;
}

function kfo_steam_join_why(_r)
{
    switch (_r)
    {
        case 2: return "That room does not exist any more.";
        case 3: return "That room is not open to you (private, or friends only).";
        case 4: return "That room is full.";
        case 5: return "Steam had an error joining the room.";
        case 6: return "You are banned from that room.";
        case 7: return "That room is for a different game.";
    }
    return "Steam could not join that room (" + string(_r) + ").";
}

// a packet: one JSON message { t: "up" | "down", m }
function kfo_steam_packet(_from, _txt)
{
    var _o = global.kfo;
    if (_o.st != "room")
        return 0;
    var _m = kfo_json_in(_txt);
    if (!is_struct(_m))
        return 0;
    var _t = kfo_js(_m, "t", "");
    if (_t == "down")
    {
        // only the host speaks to the room
        if (_from != _o.hostid)
            return 0;
        _o.t_rx = current_time;
        kfo_client_on(kfo_jv(_m, "m"));
    }
    else if (_t == "up")
    {
        if (!kfo_is_host())
            return 0;
        var _mem = false;
        for (var _i = 0; _i < array_length(_o.members); _i++)
        {
            if (kfo_jn(_o.members[_i], "pid", -1) == _from)
                _mem = true;
        }
        if (_mem)
            kfo_host_on(_from, kfo_jv(_m, "m"));
    }
    return 1;
}

function kfo_steam_send(_to, _m, _rel)
{
    if (!is_struct(global.kfo_stm) || !global.kfo_stm.ok)
        return false;
    var _r = kfo_sx("kf_send", _to, json_stringify(_m), _rel ? 1 : 0);
    return _r == 1;
}

// the digits of a text from outside as a number (_d when there are none: real("") would stop the game)
function kfo_num(_s, _d)
{
    if (is_real(_s))
        return _s;
    if (!is_string(_s))
        return _d;
    var _g = string_digits(_s);
    if (_g == "" || string_length(_g) > 15)
        return _d;
    return real(_g);
}

function kfo_split(_s, _sep)
{
    var _l = [];
    if (!is_string(_s))
        return _l;
    var _cur = "";
    for (var _i = 1; _i <= string_length(_s); _i++)
    {
        var _c = string_char_at(_s, _i);
        if (_c == _sep)
        {
            array_push(_l, _cur);
            _cur = "";
        }
        else
            _cur += _c;
    }
    array_push(_l, _cur);
    return _l;
}

// the game was started from a Steam invite (+connect_lobby <lobby> on its command line): Steam starts at once (otherwise it
// only starts when the ONLINE page is opened) and the room is joined once the hub is up. Checked once.
global.kfo_launch_done = false;
function kfo_launch_lobby_arg()
{
    var _n = 0;
    try
    {
        _n = parameter_count();
    }
    catch (_e)
    {
        _n = 0;
    }
    for (var _i = 0; _i < _n; _i++)
    {
        var _a = parameter_string(_i + 1);
        if (is_string(_a) && string_pos("+connect_lobby", _a) > 0)
        {
            var _d = string_digits(string_delete(_a, 1, string_pos("+connect_lobby", _a) + 13));
            if (_d == "" && _i + 2 <= _n)
                _d = string_digits(parameter_string(_i + 2));
            return _d;
        }
    }
    return "";
}

function kfo_launch_check()
{
    if (global.kfo_launch_done)
        return 0;
    global.kfo_launch_done = true;
    if (kfo_launch_lobby_arg() == "")
        return 0;
    kfo_get();
    kfo_log("started from a Steam invite");
    return kfo_steam_launch_join();
}

function kfo_steam_launch_join()
{
    if (!kfo_steam_ready())
        return 0;
    var _id = kfo_sx("kf_launch_lobby");
    if (is_string(_id) && _id != "" && !kfo_in_room())
        kfo_steam_join_checked(_id);
    return 1;
}
