// ===== Build 43: KNIGHT FIGHTS ONLINE - connection, rooms and the messages of this player =====
// A room lives on a relay server (server/relay.js) that only passes messages around. The room's HOST player's game runs the
// room itself (online_host.gml): the lobby, the settings, the match, who is out. Every player, the host included, talks to
// the room through the same two calls, so a match plays the same for everyone:
//   kfo_up(m)        this player -> the host            (the host's own messages are handled in its own game)
//   kfo_down(to, m)  the host -> one player (id) / everyone (0)
// PRACTICE is a room of your own with no server at all ("local"): the same host code runs in your game, with bots.
// The connection is a plain TCP socket (network_* functions). Its data arrives in the hub controller's Async - Networking
// event (kfo_async); everything else runs from the controller's Step (kfo_tick), which keeps running while the hub freezes
// the battle for a prompt. Messages are JSON, one per line.
global.kfo = undefined;

function kfo_version()
{
    // players need the same Knight Hub build to share a room (the relay and the Steam lobby compare it on join)
    return 51;
}

function kfo_default_port()
{
    return 7777;
}

function kfo_ini_file()
{
    return "knightfights_online.ini";
}

function kfo_max_players()
{
    return 8;
}

function kfo_state_new()
{
    return {
        name: "", skin: 1, srv: "127.0.0.1", port: 7777, lastcode: "", set: kfo_set_default(), sop: 65, names: 1, vis: 1, keys: kfo_keys_default(),
        view: kfo_view_default(), look: kfo_look_default(), lst: undefined, lst_t: 0, t_lp: 0, song: -1, t_newhost: -100000, newhost_n: "",
        mode: "off", st: "idle", sock: undefined, rx: undefined, rxn: 0, want: "", wcode: "", err: "", t_conn: 0, t_rx: 0, t_ping: 0,
        my: -1, code: "", hostid: -1, members: [], lobby: undefined, M: undefined, H: undefined, lq: [],
        prac: false, keep_spells: "", keep_equip: "", reopen: false, lost_note: "", log: [], ows: {}, t_ow: 0, t_owprune: 0, ow_last: undefined, ow_px: 0, ow_py: 0,
        stm: undefined, browse: [], browse_t: 0, browse_st: "", rtt: -1, t_lpi: 0, lpi_c: 0
    };
}

// the online state, made (and the player's settings read) on first use
function kfo_get()
{
    if (!is_struct(global.kfo))
    {
        global.kfo = kfo_state_new();
        kfo_ini_load();
    }
    return global.kfo;
}

// ---------- reading message fields safely (a message from the network can lack anything) ----------
function kfo_jv(_m, _k)
{
    if (!is_struct(_m) || !variable_struct_exists(_m, _k))
        return undefined;
    return variable_struct_get(_m, _k);
}

function kfo_jn(_m, _k, _d)
{
    var _v = kfo_jv(_m, _k);
    if (is_real(_v))
        return _v;
    if (!is_undefined(_v) && !is_string(_v) && !is_array(_v) && !is_struct(_v) && is_numeric(_v))
        return real(_v);
    return _d;
}

function kfo_js(_m, _k, _d)
{
    var _v = kfo_jv(_m, _k);
    return is_string(_v) ? _v : _d;
}

function kfo_ja(_m, _k)
{
    var _v = kfo_jv(_m, _k);
    return is_array(_v) ? _v : [];
}

// ---------- text the player types ----------
function kfo_trim(_s)
{
    while (string_length(_s) > 0 && string_char_at(_s, 1) == " ")
        _s = string_delete(_s, 1, 1);
    while (string_length(_s) > 0 && string_char_at(_s, string_length(_s)) == " ")
        _s = string_delete(_s, string_length(_s), 1);
    return _s;
}

// printable ASCII only (what the game's fonts draw), single spaces, at most 12 characters
function kfo_clean_name(_s)
{
    if (!is_string(_s))
        return "";
    var _o = "";
    var _sp = false;
    for (var _i = 1; _i <= string_length(_s); _i++)
    {
        var _c = string_char_at(_s, _i);
        var _n = ord(_c);
        if (_n < 32 || _n > 126)
            continue;
        if (_c == " ")
        {
            _sp = (_o != "");
            continue;
        }
        if (_sp)
            _o += " ";
        _sp = false;
        _o += _c;
    }
    _o = kfo_trim(_o);
    if (string_length(_o) > 12)
        _o = kfo_trim(string_copy(_o, 1, 12));
    return _o;
}

// room codes: 5 letters (the relay makes them from consonants), 7 letters (a Steam lobby), or LOCAL
function kfo_clean_code(_s)
{
    if (!is_string(_s))
        return "";
    var _u = string_upper(_s);
    var _o = "";
    for (var _i = 1; _i <= string_length(_u); _i++)
    {
        var _c = string_char_at(_u, _i);
        if (ord(_c) >= 65 && ord(_c) <= 90)
            _o += _c;
    }
    return string_copy(_o, 1, 7);
}

// "host" or "host:port" -> [host, port] (host: letters, digits, dots, dashes); undefined when it is not usable
function kfo_parse_server(_s)
{
    if (!is_string(_s))
        return undefined;
    _s = kfo_trim(_s);
    var _p = string_pos(":", _s);
    var _h = _s;
    var _port = kfo_default_port();
    if (_p > 0)
    {
        _h = string_copy(_s, 1, _p - 1);
        var _ps = string_copy(_s, _p + 1, string_length(_s) - _p);
        if (_ps == "" || string_digits(_ps) != _ps || string_length(_ps) > 5)
            return undefined;
        _port = real(_ps);
        if (_port < 1 || _port > 65535)
            return undefined;
    }
    if (_h == "" || string_length(_h) > 64)
        return undefined;
    for (var _i = 1; _i <= string_length(_h); _i++)
    {
        var _c = string_char_at(_h, _i);
        var _n = ord(_c);
        var _ok = (_n >= 48 && _n <= 57) || (_n >= 65 && _n <= 90) || (_n >= 97 && _n <= 122) || _c == "." || _c == "-";
        if (!_ok)
            return undefined;
    }
    return [_h, _port];
}

function kfo_server_text()
{
    var _o = kfo_get();
    return _o.srv + ((_o.port == kfo_default_port()) ? "" : (":" + string(_o.port)));
}

function kfo_skin_name(_s)
{
    // build 52: the registry's name (online_skin52.gml)
    return (is_numeric(_s) && _s >= 6) ? kfo_skin_def(kfo_skin_ok(_s)).name : knight_char_proper(clamp(_s, 1, 5));
}

// ---------- the player's online settings (knightfights_online.ini, next to the hub's own file) ----------
function kfo_ini_load()
{
    var _o = global.kfo;
    ossafe_ini_open(kfo_ini_file());
    var _nm = kfo_clean_name(ini_read_string("player", "name", ""));
    var _sk = ini_read_real("player", "skin", 1);
    var _srv = ini_read_string("server", "host", "127.0.0.1");
    var _pt = ini_read_real("server", "port", kfo_default_port());
    var _lc = ini_read_string("player", "last_code", "");
    var _sop = ini_read_real("player", "soul_opacity", 65);
    var _nms = ini_read_real("player", "name_labels", 1);
    var _vis = ini_read_real("player", "lobby_type", 1);
    var _sj = ini_read_string("room", "settings", "");
    // build 47: how the other SOULs look to you and how yours looks ([view], [look]), the online song; a file from build 46
    // has none of them: its SOUL OPACITY carries over, the rest starts at the defaults
    var _vw = kfo_view_read();
    // build 48: the other SOULs are seen by default now (70%); a file saved by build 47 (20%, or less) starts from that once
    if (ini_read_real("view", "v48", 0) != 1)
        _vw.sop = 70;
    var _lk = kfo_look_read();
    var _osong = ini_read_real("player", "song", -1);
    // build 50: the MUSIC setting is kept as its song's file (the list is sorted by artist now); a number from before is read
    // with the list's old order
    var _osf = ini_read_string("player", "songf", "~none");
    if (_osf == "~hub")
        _osong = -1;
    else if (_osf != "~none")
        _osong = max(-1, knight_song_find_exact(_osf));
    else if (is_real(_osong) && _osong == floor(_osong) && _osong >= 0 && _osong < array_length(global.knight_songs_v49))
        _osong = max(-1, knight_song_find_exact(global.knight_songs_v49[_osong]));
    var _kl = kfo_key_list();
    var _kr = {};
    for (var _i = 0; _i < array_length(_kl); _i++)
    {
        var _ke = _kl[_i];
        variable_struct_set(_kr, _ke[0], ini_read_real("keys", _ke[0], _ke[2]));
    }
    // build 48: a file from before TARGETING kept HOLD SLOT on A and QUICK SETTINGS on Q (now the targeting keys)
    if (ini_read_real("keys", "k48", 0) != 1)
    {
        if (_kr.hold == ord("A"))
            _kr.hold = ord("D");
        if (_kr.quick == ord("Q"))
            _kr.quick = ord("F");
    }
    ossafe_ini_close();
    if (_nm == "")
    {
        _nm = variable_global_exists("truename") ? kfo_clean_name(global.truename) : "";
        if (_nm == "" || _nm == " ")
            _nm = "Player";
    }
    _o.name = _nm;
    _o.skin = (is_real(_sk) && _sk >= 1 && _sk <= 5) ? floor(_sk) : 1;
    var _ps = kfo_parse_server(_srv + ":" + string(floor(is_real(_pt) ? _pt : kfo_default_port())));
    if (!is_undefined(_ps))
    {
        _o.srv = _ps[0];
        _o.port = _ps[1];
    }
    _o.lastcode = kfo_clean_code(_lc);
    _o.sop = is_real(_sop) ? kfo_num_in(_sop, 20, 100, 5, 65) : 65;
    _o.names = (is_real(_nms) && _nms == 0) ? 0 : 1;
    _o.vis = is_real(_vis) ? clamp(floor(_vis), 0, 2) : 1;
    var _m = (_sj != "") ? kfo_json_in(_sj) : undefined;
    _o.set = kfo_set_clean(_m);
    _o.keys = kfo_keys_clean(_kr);
    // (build 46's SOUL OPACITY is not carried over: the other SOULs start very see-through in build 47)
    _o.view = kfo_view_clean(_vw);
    _o.look = kfo_look_clean(_lk);
    _o.sop = _o.view.sop;
    _o.names = _o.view.names;
    _o.song = (is_real(_osong) && _osong == floor(_osong) && _osong >= -1 && _osong < array_length(global.knight_songs)) ? _osong : -1;
}

function kfo_ini_save()
{
    var _o = kfo_get();
    // build 47: the SOUL VISIBILITY settings ([view]) are the only source; build 46's two keys are written from them (a build
    // 46 game reading this file keeps its opacity and name labels)
    _o.view = kfo_view_clean(_o.view);
    _o.look = kfo_look_clean(_o.look);
    _o.sop = _o.view.sop;
    _o.names = _o.view.names;
    ossafe_ini_open(kfo_ini_file());
    ini_write_string("player", "name", _o.name);
    ini_write_real("player", "skin", _o.skin);
    ini_write_string("player", "last_code", _o.lastcode);
    ini_write_real("player", "soul_opacity", _o.sop);
    ini_write_real("player", "name_labels", _o.names);
    ini_write_real("player", "lobby_type", _o.vis);
    ini_write_string("server", "host", _o.srv);
    ini_write_real("server", "port", _o.port);
    ini_write_string("room", "settings", json_stringify(kfo_set_clean(_o.set)));
    kfo_view_write(_o.view);
    ini_write_real("view", "v48", 1);
    ini_write_real("keys", "k48", 1);
    kfo_look_write(_o.look);
    ini_write_real("player", "song", _o.song);
    ini_write_string("player", "songf", (_o.song < 0 || _o.song >= array_length(global.knight_songs)) ? "~hub" : global.knight_songs[_o.song].file);
    var _kl = kfo_key_list();
    for (var _i = 0; _i < array_length(_kl); _i++)
    {
        var _ke = _kl[_i];
        ini_write_real("keys", _ke[0], kfo_key(_ke[0]));
    }
    ossafe_ini_close();
}

// ---------- the match keys (build 46: MORE OPTIONS > KEYBINDS, kept in knightfights_online.ini [keys]) ----------
// [id, the KEYBINDS page's label, the default key]. The arrows move the SOUL and X is the game's own slow walk: those stay
// the game's and cannot be taken here (nor ENTER / ESC / F4). A controller: its confirm button uses (tap: next skill), its
// menu button charges, LT holds breath, RT is the hold slot, LB / RB change the TARGETING mode, BACK the player list.
function kfo_key_list()
{
    // build 48: TARGETING takes Q / E (the mode) and A (the next target): HOLD SLOT moves to D, QUICK SETTINGS to F
    return [["breath", "HOLD BREATH", ord("S")], ["use", "USE SKILL", ord("Z")], ["charge", "CHARGE", ord("C")], ["hold", "HOLD SLOT", ord("D")],
        ["list", "PLAYER LIST", vk_tab], ["quit", "GIVE UP", vk_backspace], ["quick", "QUICK SETTINGS", ord("F")], ["souls", "OTHER SOULS", ord("V")],
        ["tgl", "TARGET MODE <", ord("Q")], ["tgr", "TARGET MODE >", ord("E")], ["tgn", "NEXT TARGET", ord("A")],
        ["chat", "CHAT OPEN / SEND", 220]];
}

function kfo_keys_default()
{
    var _k = {};
    var _kl = kfo_key_list();
    for (var _i = 0; _i < array_length(_kl); _i++)
    {
        var _ke = _kl[_i];
        variable_struct_set(_k, _ke[0], _ke[2]);
    }
    return _k;
}

// a key set from the ini (or anywhere): every action gets a usable key, no key twice (a bad or doubled one goes back to
// its default, and when that is taken too, to the first free default)
function kfo_keys_clean(_in)
{
    var _out = {};
    var _kl = kfo_key_list();
    var _used = [];
    for (var _i = 0; _i < array_length(_kl); _i++)
    {
        var _ke = _kl[_i];
        var _v = is_struct(_in) ? kfo_jn(_in, _ke[0], _ke[2]) : _ke[2];
        _v = floor(_v);
        var _dup = false;
        for (var _j = 0; _j < array_length(_used); _j++)
        {
            if (_used[_j] == _v)
                _dup = true;
        }
        if (!kfo_key_ok(_v) || _dup)
            _v = _ke[2];
        for (var _j = 0; _j < array_length(_used); _j++)
        {
            if (_used[_j] == _v)
                _dup = true;
        }
        array_push(_used, _v);
        variable_struct_set(_out, _ke[0], _v);
    }
    // a default that was still taken by another action's custom key: the whole set back to the defaults
    for (var _i = 0; _i < array_length(_used); _i++)
    {
        for (var _j = _i + 1; _j < array_length(_used); _j++)
        {
            if (_used[_i] == _used[_j])
                return kfo_keys_default();
        }
    }
    return _out;
}

function kfo_key(_id)
{
    var _o = kfo_get();
    if (is_struct(_o.keys) && variable_struct_exists(_o.keys, _id))
        return variable_struct_get(_o.keys, _id);
    var _d = kfo_keys_default();
    return variable_struct_exists(_d, _id) ? variable_struct_get(_d, _id) : -1;
}

// why key _k cannot be a match key ("" = it can)
function kfo_key_why(_k)
{
    if (!is_real(_k) || _k < 8 || _k > 254)
        return "not a key";
    if (_k == vk_left || _k == vk_right || _k == vk_up || _k == vk_down)
        return "the arrows move your SOUL";
    if (_k == ord("X") || _k == vk_shift || _k == 160 || _k == 161)
        return "the game's own slow / cancel key";
    if (_k == vk_enter || _k == vk_escape)
        return "the game's own menu key";
    if (_k == vk_f4)
        return "the game's own full screen key";
    if (_k >= ord("1") && _k <= ord("8"))
        return "1-8 pick a target";
    return "";
}

function kfo_key_ok(_k)
{
    return kfo_key_why(_k) == "";
}

// give action _id key _k (another action that had _k gets this action's old key: the two swap)
function kfo_key_set(_id, _k)
{
    var _o = kfo_get();
    if (!kfo_key_ok(_k))
        return false;
    var _old = kfo_key(_id);
    var _kl = kfo_key_list();
    for (var _i = 0; _i < array_length(_kl); _i++)
    {
        var _ke = _kl[_i];
        if (_ke[0] != _id && kfo_key(_ke[0]) == _k)
            variable_struct_set(_o.keys, _ke[0], _old);
    }
    variable_struct_set(_o.keys, _id, _k);
    return true;
}

// a key's name as the pages show it
function kfo_key_name(_k)
{
    if (!is_real(_k))
        return "?";
    if ((_k >= ord("A") && _k <= ord("Z")) || (_k >= ord("0") && _k <= ord("9")))
        return chr(_k);
    if (_k >= 96 && _k <= 105)
        return "NUM " + string(_k - 96);
    if (_k >= 112 && _k <= 123)
        return "F" + string(_k - 111);
    switch (_k)
    {
        case vk_space: return "SPACE";
        case vk_tab: return "TAB";
        case vk_backspace: return "BACKSPACE";
        case vk_enter: return "ENTER";
        case vk_shift: return "SHIFT";
        case vk_control: return "CTRL";
        case vk_escape: return "ESC";
        case 18: return "ALT";
        case 19: return "PAUSE";
        case 20: return "CAPS LOCK";
        case 33: return "PAGE UP";
        case 34: return "PAGE DOWN";
        case 35: return "END";
        case 36: return "HOME";
        case 45: return "INSERT";
        case 46: return "DELETE";
        case 106: return "NUM *";
        case 107: return "NUM +";
        case 109: return "NUM -";
        case 110: return "NUM .";
        case 111: return "NUM /";
        case 160: return "LEFT SHIFT";
        case 161: return "RIGHT SHIFT";
        case 162: return "LEFT CTRL";
        case 163: return "RIGHT CTRL";
        case 164: return "LEFT ALT";
        case 165: return "RIGHT ALT";
        case 186: return ";";
        case 187: return "=";
        case 188: return ",";
        case 189: return "-";
        case 190: return ".";
        case 191: return "/";
        case 192: return "`";
        case 219: return "[";
        case 220: return chr(92);
        case 221: return "]";
        case 222: return "'";
    }
    return "KEY " + string(_k);
}

// the controller button of a match action (-1: none): USE and CHARGE are the confirm and menu buttons set in Chapter 3's own
// CONTROLS, HOLD BREATH is LB, the HOLD slot RB, the player list BACK (a controller's buttons are not changed in KEYBINDS)
function kbr_key_pad(_id)
{
    var _gi = -1;
    switch (_id)
    {
        case "use": _gi = 4; break;
        case "charge": _gi = 6; break;
        // build 48: the shoulder buttons change the TARGETING mode; HOLD BREATH and the HOLD slot move to the triggers
        case "breath": return gp_shoulderlb;
        case "hold": return gp_shoulderrb;
        case "tgl": return gp_shoulderl;
        case "tgr": return gp_shoulderr;
        case "list": return gp_select;
        case "quick": return gp_start;
    }
    if (_gi < 0)
        return -1;
    if (variable_global_exists("input_g") && is_array(global.input_g) && array_length(global.input_g) > _gi && is_real(global.input_g[_gi]))
        return global.input_g[_gi];
    return (_gi == 4) ? gp_face1 : gp_face4;
}

// DRBR (build 53): the ORANGE SOUL (Flowery, Chapter 5) charges and DASHES with the game's confirm key (Z, ENTER or the
// controller's confirm button), the YELLOW SOUL (Spamton NEO, Chapter 2) shoots with it (hold it for a BIG SHOT). While one is
// up, a USE SKILL on that same key moves to the HOLD BREATH key / button (S and LT unless changed), so charging a dash or a
// BIG SHOT never picks or fires a skill. HOLD BREATH itself is off meanwhile (the orange SOUL moves at its own speed, the
// yellow one at Chapter 2's 5). Every other key stays where it is.
function kbr_orange_on()
{
    return instance_exists(obj_fl_soul) || kbr_sn_yellow_on();
}

// key _k is one the game itself reads as CONFIRM (Chapter 3's CONTROLS: its confirm key, and ENTER)
function kbr_key_is_confirm(_k)
{
    if (_k == vk_enter)
        return true;
    if (variable_global_exists("input_k") && is_array(global.input_k) && array_length(global.input_k) > 4 && is_real(global.input_k[4]))
        return global.input_k[4] == _k;
    return _k == ord("Z");
}

// the keyboard key that does action _id right now (-1: none) - the orange SOUL's swap above
function kbr_key_now(_id)
{
    var _k = kfo_key(_id);
    if (kbr_orange_on())
    {
        if (_id == "breath")
            return -1;
        if (_id == "use" && kbr_key_is_confirm(_k))
            return kfo_key("breath");
    }
    return _k;
}

// the controller button that does action _id right now (-1: none): USE is the confirm button - the orange SOUL's dash
function kbr_pad_now(_id)
{
    if (kbr_orange_on())
    {
        if (_id == "breath")
            return -1;
        if (_id == "use")
            return kbr_key_pad("breath");
    }
    return kbr_key_pad(_id);
}

// a match key is down: its key (KEYBINDS) or its controller button
function kbr_key_held(_id)
{
    // build 48: while you type in the chat the keys are the chat's (no breath, skill, list, give-up, souls...)
    if (kfo_chat_typing())
        return false;
    var _k = kbr_key_now(_id);
    if (_k > 0 && keyboard_check(_k))
        return true;
    var _b = kbr_pad_now(_id);
    return _b > 0 && knight_pad_held(_b);
}

// a match key went down this step
function kbr_key_pressed(_id)
{
    if (kfo_chat_typing())
        return false;
    var _k = kbr_key_now(_id);
    if (_k > 0 && keyboard_check_pressed(_k))
        return true;
    var _b = kbr_pad_now(_id);
    return _b > 0 && knight_pad_pressed(_b);
}

// the key of an action as the HUD and the pages show it (in a match: the key that does it now - USE on HOLD BREATH's
// key while the orange SOUL is up)
function kfo_key_label(_id)
{
    var _k = kbr_key_now(_id);
    return (_k > 0) ? kfo_key_name(_k) : "-";
}

// DRBR 1.0.2: USE SKILL's key right now as the match HUD says it - the keyboard key, and the controller button too while one
// is in use ("S / LT" on the orange / yellow SOUL)
function kbr_use_key_label()
{
    var _l = kfo_key_label("use");
    if (knight_pad_on())
    {
        // (gp_shoulderlb / rb are the triggers - LT and RT, as KEYBINDS names them - gp_shoulderl / r the bumpers)
        var _b = kbr_pad_now("use");
        if (_b == gp_shoulderlb)
            _l += " / LT";
        else if (_b == gp_shoulderrb)
            _l += " / RT";
        else if (_b == gp_shoulderl)
            _l += " / LB";
        else if (_b == gp_shoulderr)
            _l += " / RB";
    }
    return _l;
}

// the KEYBINDS page's name of an action
function kfo_key_title(_id)
{
    var _kl = kfo_key_list();
    for (var _i = 0; _i < array_length(_kl); _i++)
    {
        var _ke = _kl[_i];
        if (_ke[0] == _id)
            return _ke[1];
    }
    return string_upper(_id);
}

// the controller button of an action as the KEYBINDS page shows it
function kfo_key_pad_name(_id)
{
    switch (_id)
    {
        case "use": return "CONFIRM";
        case "charge": return "MENU";
        case "breath": return "LT";
        case "hold": return "RT";
        case "tgl": return "LB";
        case "tgr": return "RB";
        case "tgn": return "R STICK";
        case "list": return "BACK";
        case "quick": return "START";
    }
    return "-";
}

// what an action does (the KEYBINDS page's top bar)
function kfo_key_desc(_id)
{
    switch (_id)
    {
        case "breath": return "HOLD BREATH: press once to hold your#breath (SOUL faster), again to let go.";
        // (DRBR 1.0.2: and where it goes while the SOUL itself uses Z)
        case "use": return "USE SKILL: tap: next skill, hold: use it.#Yellow / orange SOUL: on " + kfo_key_name(kfo_key("breath")) + ". Z: change it.";
        case "charge": return "CHARGE: hold it to charge the gauge, let go#to draw a skill. Z: change the key.";
        case "hold": return "HOLD SLOT: the picked skill into the hold#slot, and back. Z: change the key.";
        case "list": return "PLAYER LIST: hold it to see every player.#Z: change the key.";
        case "quit": return "GIVE UP: OUT and back to the room (it asks#first). Z: change the key.";
        case "quick": return "QUICK SETTINGS: the SOULs, effects, sound#and camera during a match. Z: change it.";
        case "souls": return "OTHER SOULS: show or hide the other players'#SOULs in the match. Z: change the key.";
        case "tgl": return "TARGET MODE <: the TARGETING mode to the#left. Z: change the key.";
        case "tgr": return "TARGET MODE >: the TARGETING mode to the#right. Z: change the key.";
        case "tgn": return "NEXT TARGET: CHECK the next player (1-8 pick#a slot). Z: change the key.";
        case "chat": return "CHAT: opens the chat and sends what you typed#(T and ENTER work too).";
    }
    return "";
}

// every key back to its default
function kfo_keys_reset()
{
    var _o = kfo_get();
    _o.keys = kfo_keys_default();
    kfo_ini_save();
    return 1;
}

// ---------- connection state ----------
function kfo_in_room()
{
    return is_struct(global.kfo) && global.kfo.st == "room";
}

function kfo_is_host()
{
    return is_struct(global.kfo) && global.kfo.st == "room" && global.kfo.hostid == global.kfo.my && global.kfo.my >= 0;
}

function kfo_busy()
{
    return is_struct(global.kfo) && (global.kfo.st == "connecting" || global.kfo.st == "hello" || global.kfo.st == "joining");
}

function kfo_log(_t)
{
    var _o = kfo_get();
    array_push(_o.log, _t);
    if (array_length(_o.log) > 40)
        array_delete(_o.log, 0, array_length(_o.log) - 40);
}

// close everything (no message to anyone); _err is shown on the ONLINE page when it is not ""
function kfo_close(_err)
{
    var _o = kfo_get();
    // the socket and the receive buffer are kept as the runtime gave them (a number, or a handle in newer GameMaker
    // runtimes); "none" is undefined, never -1, so nothing here compares a handle with a number
    if (!is_undefined(_o.sock))
        network_destroy(_o.sock);
    _o.sock = undefined;
    if (!is_undefined(_o.rx) && buffer_exists(_o.rx))
        buffer_delete(_o.rx);
    _o.rx = undefined;
    _o.rxn = 0;
    if (_o.mode == "steam")
        kfo_steam_close();
    _o.mode = "off";
    _o.st = (_err != "") ? "failed" : "idle";
    _o.err = _err;
    _o.my = -1;
    _o.code = "";
    _o.hostid = -1;
    _o.members = [];
    _o.lobby = undefined;
    _o.H = undefined;
    _o.lq = [];
    _o.prac = false;
    _o.ows = {};
    return 0;
}

// leave the room on purpose (LEAVE ROOM, closing the menu)
function kfo_leave()
{
    var _o = kfo_get();
    if (_o.mode == "direct" && !is_undefined(_o.sock) && _o.st == "room")
        kfo_raw({ t: "leave" });
    _o.M = undefined;
    kfo_close("");
}

function kfo_fail(_why)
{
    kfo_log("fail: " + _why);
    kfo_close(_why);
    return false;
}

// the connection broke: in a match the battle shows it (kfo_battle_lost), in the menu the ONLINE page does
function kfo_lost(_why)
{
    var _o = kfo_get();
    if (_o.mode != "direct" && _o.mode != "steam")
        return 0;
    var _inmatch = is_struct(_o.M) && _o.M.me && !_o.M.ended;
    kfo_log("lost: " + _why);
    kfo_close(_why);
    if (_inmatch)
        _o.lost_note = _why;
    return 1;
}

// ---------- DIRECT: a socket to the relay ----------
// _want "create" (new room), "join" (room _code), "local" (the LOCAL room of a LAN / Radmin server)
// network_create_socket / buffer_create give a number in older GameMaker runtimes and a typed handle in newer ones, so
// these never use is_real() on them or compare them with a number
function kfo_bad_handle(_h)
{
    if (is_undefined(_h))
        return true;
    return is_real(_h) && _h < 0;
}
// is the async_load id _a the socket _s? 1 yes, 0 no, -1 cannot tell (a handle against a plain number)
function kfo_same_socket(_a, _s)
{
    if (is_undefined(_a) || is_undefined(_s))
        return -1;
    var _r = -1;
    try
    {
        if (_a == _s)
            _r = 1;
    }
    catch (_e)
    {
        _r = -1;
    }
    if (_r == 1)
        return 1;
    if (is_real(_a) && is_real(_s))
        return 0;
    if (typeof(_a) == typeof(_s))
        return 0;
    try
    {
        _r = (real(_a) == real(_s)) ? 1 : 0;
    }
    catch (_e2)
    {
        _r = -1;
    }
    return _r;
}
function kfo_direct_start(_want, _code)
{
    var _o = kfo_get();
    kfo_close("");
    _o.M = undefined;
    _o.mode = "direct";
    _o.want = _want;
    _o.wcode = _code;
    network_set_config(network_config_connect_timeout, 6000);
    var _s = network_create_socket(network_socket_tcp);
    if (kfo_bad_handle(_s))
        return kfo_fail("Could not open a network socket.");
    _o.sock = _s;
    _o.rx = buffer_create(1024, buffer_grow, 1);
    _o.rxn = 0;
    _o.st = "connecting";
    _o.t_conn = current_time;
    _o.t_rx = current_time;
    _o.t_ping = current_time;
    var _r = network_connect_raw_async(_s, _o.srv, _o.port);
    if (is_real(_r) && _r < 0)
        return kfo_fail("Could not reach " + kfo_server_text() + ".");
    kfo_log("connecting to " + kfo_server_text());
    return true;
}

// one message to the relay
function kfo_raw(_m)
{
    var _o = global.kfo;
    if (!is_struct(_o) || _o.mode != "direct" || is_undefined(_o.sock))
        return false;
    var _s = json_stringify(_m) + "\n";
    var _n = string_byte_length(_s);
    var _b = buffer_create(_n, buffer_fixed, 1);
    buffer_write(_b, buffer_text, _s);
    var _r = network_send_raw(_o.sock, _b, _n);
    buffer_delete(_b);
    if (is_real(_r) && _r < 0)
    {
        kfo_lost("The connection was lost.");
        return false;
    }
    return true;
}

// Async - Networking event of the hub controller
function kfo_async()
{
    if (!is_struct(global.kfo))
        return 0;
    var _o = global.kfo;
    if (is_undefined(_o.sock))
        return 0;
    var _id = ds_map_find_value(async_load, "id");
    var _sk = ds_map_find_value(async_load, "socket");
    var _m1 = kfo_same_socket(_id, _o.sock);
    var _m2 = kfo_same_socket(_sk, _o.sock);
    // 1 = this socket, 0 = another one, -1 = cannot tell (only one socket is ever open, so that one is taken as ours)
    if (!(_m1 == 1 || _m2 == 1 || (_m1 == -1 && _m2 == -1)))
        return 0;
    var _type = ds_map_find_value(async_load, "type");
    if (!is_numeric(_type))
        return 0;
    if (_type == network_type_non_blocking_connect)
    {
        var _ok = ds_map_find_value(async_load, "succeeded");
        if (_o.st != "connecting")
            return 0;
        // "succeeded" is 1 / 0 or true / false depending on the runtime
        if (!is_undefined(_ok) && !is_string(_ok) && !_ok)
            return kfo_fail("Could not connect to " + kfo_server_text() + ".");
        _o.st = "hello";
        _o.t_rx = current_time;
        kfo_raw({ t: "hello", game: "kfo", ver: kfo_version(), name: _o.name });
        return 1;
    }
    if (_type == network_type_disconnect)
    {
        if (_o.st == "connecting")
            return kfo_fail("Could not connect to " + kfo_server_text() + ".");
        kfo_lost("The server closed the connection.");
        return 1;
    }
    if (_type == network_type_data)
    {
        var _buf = ds_map_find_value(async_load, "buffer");
        var _size = ds_map_find_value(async_load, "size");
        if (is_undefined(_buf) || !is_numeric(_size) || _size <= 0)
            return 0;
        if (_o.st == "connecting")
        {
            // data before the connect event: the connection is up
            _o.st = "hello";
            kfo_raw({ t: "hello", game: "kfo", ver: kfo_version(), name: _o.name });
        }
        kfo_rx_add(_buf, _size);
        return 1;
    }
    return 0;
}

// incoming bytes: kept until a whole line ("\n") is there, then each line is one message
function kfo_rx_add(_buf, _size)
{
    var _o = global.kfo;
    _o.t_rx = current_time;
    if (is_undefined(_o.rx) || !buffer_exists(_o.rx))
    {
        _o.rx = buffer_create(1024, buffer_grow, 1);
        _o.rxn = 0;
    }
    if (buffer_get_size(_o.rx) < _o.rxn + _size)
        buffer_resize(_o.rx, max(_o.rxn + _size, buffer_get_size(_o.rx) * 2));
    buffer_copy(_buf, 0, _size, _o.rx, _o.rxn);
    _o.rxn += _size;
    var _start = 0;
    for (var _i = _o.rxn - _size; _i < _o.rxn; _i++)
    {
        if (buffer_peek(_o.rx, _i, buffer_u8) != 10)
            continue;
        var _len = _i - _start;
        if (_len > 0)
        {
            var _t = buffer_create(_len + 1, buffer_fixed, 1);
            buffer_copy(_o.rx, _start, _len, _t, 0);
            buffer_poke(_t, _len, buffer_u8, 0);
            buffer_seek(_t, buffer_seek_start, 0);
            var _line = buffer_read(_t, buffer_string);
            buffer_delete(_t);
            kfo_line(_line);
            // a message can close the connection (refused, kicked)
            if (!is_struct(global.kfo) || is_undefined(global.kfo.rx) || is_undefined(_o.sock))
                return 0;
        }
        _start = _i + 1;
    }
    if (_start > 0)
    {
        var _left = _o.rxn - _start;
        var _nb = buffer_create(max(1024, _left), buffer_grow, 1);
        if (_left > 0)
            buffer_copy(_o.rx, _start, _left, _nb, 0);
        buffer_delete(_o.rx);
        _o.rx = _nb;
        _o.rxn = _left;
    }
    if (_o.rxn > 262144)
        kfo_lost("The server sent something this game cannot read.");
    return 1;
}

// text from outside (the network, a pasted code, the ini) -> a struct, or undefined: never a crash. Text that is too long
// or nested too deep for any message of ours (a parser could run out of stack on it) is not even parsed.
function kfo_json_in(_s)
{
    if (!is_string(_s) || string_length(_s) == 0 || string_length(_s) > 65536)
        return undefined;
    if (string_count("[", _s) + string_count("{", _s) > 1500)
        return undefined;
    var _m = undefined;
    try
    {
        _m = json_parse(_s);
    }
    catch (_e)
    {
        _m = undefined;
    }
    return is_struct(_m) ? _m : undefined;
}

function kfo_line(_s)
{
    var _m = kfo_json_in(_s);
    if (!is_struct(_m))
        return 0;
    kfo_relay_on(_m);
    return 1;
}

// a message from the relay
function kfo_relay_on(_m)
{
    var _o = global.kfo;
    var _t = kfo_js(_m, "t", "");
    switch (_t)
    {
        case "welcome":
            _o.my = kfo_jn(_m, "id", -1);
            _o.st = "joining";
            if (_o.want == "create")
                kfo_raw({ t: "create", max: kfo_set_cap(_o.set) });
            else
                kfo_raw({ t: "join", code: (_o.want == "local") ? "LOCAL" : _o.wcode });
            break;
        case "joined":
            kfo_on_joined(_m);
            break;
        case "refused":
            var _why = kfo_js(_m, "why", "Refused");
            if (_o.st == "room")
                kfo_lost(_why);
            else
                kfo_fail(kfo_refusal_text(_why));
            break;
        case "member":
            kfo_on_member(kfo_js(_m, "ev", ""), kfo_jn(_m, "id", -1), kfo_js(_m, "name", ""));
            break;
        case "promote":
            kfo_on_promote(kfo_jn(_m, "host", -1), kfo_ja(_m, "members"));
            break;
        case "up":
            if (kfo_is_host())
                kfo_host_on(kfo_jn(_m, "from", -1), kfo_jv(_m, "m"));
            break;
        case "down":
            kfo_client_on(kfo_jv(_m, "m"));
            break;
    }
    return 0;
}

// the relay's refusal reasons, as the ONLINE page says them
function kfo_refusal_text(_why)
{
    switch (_why)
    {
        case "No such room": return "There is no room with that code.";
        case "Full Player": return "That room is full.";
        case "Client Is Older": return kdr_other_build(true, "The room's players have");
        case "Client Is Newer": return kdr_other_build(false, "The room's players have");
        case "Kicked": return "The host removed you from the room.";
    }
    return _why;
}

function kfo_on_joined(_m)
{
    var _o = global.kfo;
    _o.st = "room";
    _o.err = "";
    _o.code = kfo_js(_m, "code", "");
    _o.my = kfo_jn(_m, "you", _o.my);
    _o.hostid = kfo_jn(_m, "host", -1);
    _o.members = kfo_members_norm(kfo_ja(_m, "members"));
    if (_o.code != "LOCAL")
        _o.lastcode = _o.code;
    kfo_ini_save();
    kfo_log("in room " + _o.code + " as " + string(_o.my) + ", host " + string(_o.hostid));
    if (_o.hostid == _o.my)
        kfo_host_begin(_o.code, false);
    else
        kfo_up({ k: "hi", name: _o.name, skin: _o.skin, ver: kfo_version(), ros: kbr_roster_sig(), cl: _o.look.col });
}

// The relay names players "id". GameMaker has a built-in (read-only) variable called id, so the game never makes a
// struct field with that name itself: relay messages are read by name (kfo_jn) and member lists are copied to "pid".
function kfo_members_norm(_list)
{
    var _out = [];
    if (!is_array(_list))
        return _out;
    for (var _i = 0; _i < array_length(_list); _i++)
        array_push(_out, { pid: kfo_jn(_list[_i], "pid", kfo_jn(_list[_i], "id", -1)), name: kfo_js(_list[_i], "name", "") });
    return _out;
}
function kfo_on_member(_ev, _id, _name)
{
    var _o = global.kfo;
    if (_ev == "join")
        array_push(_o.members, { pid: _id, name: _name });
    else
    {
        for (var _i = array_length(_o.members) - 1; _i >= 0; _i--)
        {
            if (kfo_jn(_o.members[_i], "pid", -2) == _id)
                array_delete(_o.members, _i, 1);
        }
    }
    if (kfo_is_host())
        kfo_host_member(_ev, _id, _name);
}

// the host left: the relay picked the next player by join order
function kfo_on_promote(_host, _members)
{
    var _o = global.kfo;
    var _was = kfo_is_host();
    if (_host != _o.hostid)
    {
        _o.t_rx = current_time;
        // build 47: the network line says who took the room over (HOST MIGRATION), for 5 seconds
        _o.t_newhost = current_time;
        _o.newhost_n = (_host == _o.my) ? "YOU" : kfo_member_name(_host);
    }
    _o.hostid = _host;
    _o.members = kfo_members_norm(_members);
    if (_host == _o.my && !_was)
        kfo_host_takeover(_o.members);
}

// a member's name from the last room list (the relay / Steam names them; "?" if not known)
function kfo_member_name(_id)
{
    var _pl = kfo_lobby_players();
    for (var _i = 0; _i < array_length(_pl); _i++)
    {
        if (kfo_jn(_pl[_i], "pid", -2) == _id)
            return kfo_js(_pl[_i], "n", "?");
    }
    return "?";
}

// ---------- the two directions of a room ----------
// this player -> the host (reliable, in order)
function kfo_up(_m)
{
    return kfo_up_ex(_m, true);
}

// this player -> the host, may be dropped (SOUL positions, pings: the next one replaces it)
function kfo_up_fast(_m)
{
    return kfo_up_ex(_m, false);
}

function kfo_up_ex(_m, _rel)
{
    var _o = global.kfo;
    if (!is_struct(_o) || _o.st != "room")
        return false;
    if (_o.hostid == _o.my)
    {
        array_push(_o.lq, { up: true, from: _o.my, m: _m });
        return true;
    }
    if (_o.mode == "steam")
        return kfo_steam_send(_o.hostid, { t: "up", m: _m }, _rel);
    return kfo_raw({ t: "up", m: _m });
}

// the host -> player _to (0 = everyone). The host's own copy and the bots' are handled in this game.
function kfo_down(_to, _m)
{
    return kfo_down_ex(_to, _m, true);
}

function kfo_down_fast(_to, _m)
{
    return kfo_down_ex(_to, _m, false);
}

function kfo_down_ex(_to, _m, _rel)
{
    var _o = global.kfo;
    if (!is_struct(_o) || _o.st != "room")
        return false;
    if (_to == 0 || _to == _o.my)
        array_push(_o.lq, { up: false, from: _o.my, m: _m });
    if (_to == _o.my)
        return true;
    if (_o.mode == "direct")
        return kfo_raw({ t: "down", to: _to, m: _m });
    if (_o.mode == "steam")
    {
        if (_to != 0)
            return kfo_steam_send(_to, { t: "down", m: _m }, _rel);
        var _ok = true;
        for (var _i = 0; _i < array_length(_o.members); _i++)
        {
            var _pid = kfo_jn(_o.members[_i], "pid", -1);
            if (_pid != _o.my && _pid >= 0)
                _ok = kfo_steam_send(_pid, { t: "down", m: _m }, _rel) && _ok;
        }
        return _ok;
    }
    return true;
}

// messages this game sends itself (the host's own player, practice): handled from the Step, never in the middle of the
// code that sent them, like the ones that come over the network
function kfo_local_run()
{
    var _o = global.kfo;
    var _n = 0;
    while (array_length(_o.lq) > 0 && _n < 64)
    {
        var _q = _o.lq[0];
        array_delete(_o.lq, 0, 1);
        _n++;
        if (_q.up)
        {
            if (kfo_is_host())
                kfo_host_on(_q.from, _q.m);
        }
        else
            kfo_client_on(_q.m);
        if (!is_struct(global.kfo) || global.kfo != _o)
            return false;
    }
    return true;
}

// ---------- every step (hub controller) ----------
function kfo_tick()
{
    // DRBR: the window's title while you are in a room (practice included); the game's own title back when you leave
    kfo_caption_tick();
    if (!is_struct(global.kfo))
        return 0;
    var _o = global.kfo;
    if (!kfo_local_run())
        return 0;
    if (_o.mode == "direct" && !is_undefined(_o.sock))
    {
        if (_o.st == "connecting" && current_time - _o.t_conn > 9000)
            kfo_fail("Could not connect to " + kfo_server_text() + " (no answer).");
        else if ((_o.st == "hello" || _o.st == "joining") && current_time - _o.t_rx > 9000)
            kfo_fail("The server did not answer.");
        else if (_o.st == "room" && current_time - _o.t_rx > 16000)
            kfo_lost("The server stopped answering.");
        else if (current_time - _o.t_ping > 3000 && _o.st != "connecting")
        {
            _o.t_ping = current_time;
            kfo_raw({ t: "ping" });
        }
    }
    // Steam's events come whenever kf_steam is up (BROWSE results and accepted invites arrive outside a Steam room too)
    if (is_struct(global.kfo_stm) && global.kfo_stm.ok)
    {
        kfo_steam_tick();
        if (!is_struct(global.kfo) || global.kfo != _o)
            return 0;
    }
    if (kfo_is_host())
        kfo_host_tick();
    if (!kfo_local_run())
        return 0;
    kfo_start_wait_tick();
    kfo_play_tick();
    kfo_world_tick();
    kfo_lobby_ping_tick();
    return 0;
}

// the network light in the room: a ping to the host every 2 seconds outside a match
function kfo_lobby_ping_tick()
{
    var _o = global.kfo;
    if (_o.st != "room" || kfo_is_host() || (is_struct(_o.M) && kfo_run_on()))
        return 0;
    if (current_time - _o.t_lpi >= 2000)
    {
        _o.t_lpi = current_time;
        kfo_up_fast({ k: "pi", mid: -1, c: current_time });
    }
    // build 47: the round trip, to the host every 5 seconds (everyone's ping in the room's list)
    if (_o.rtt >= 0 && current_time - _o.t_lp >= 5000)
    {
        _o.t_lp = current_time;
        kfo_up_fast({ k: "lp", r: round(_o.rtt) });
    }
    return 1;
}

// ---------- starting ----------
function kfo_practice_start()
{
    var _o = kfo_get();
    kfo_close("");
    _o.M = undefined;
    _o.mode = "local";
    _o.st = "room";
    _o.my = 1;
    _o.hostid = 1;
    _o.code = "PRACTICE";
    _o.members = [{ pid: 1, name: _o.name }];
    _o.prac = true;
    kfo_host_begin("PRACTICE", true);
    return true;
}

function kfo_create()
{
    return kfo_direct_start("create", "");
}

function kfo_join(_code)
{
    var _c = kfo_clean_code(_code);
    if (string_length(_c) != 5)
    {
        kfo_close("A room code is 5 letters.");
        return false;
    }
    return kfo_direct_start("join", _c);
}

function kfo_join_local()
{
    return kfo_direct_start("local", "LOCAL");
}

// ---------- what the players see of the room: the host's lobby message ----------
// lobby {code, host, st ("lobby" | "match"), mid, prac, set, players: [{id, n, s, rd, inm}], res (last results or 0)}
function kfo_lobby_players()
{
    var _o = kfo_get();
    if (!is_struct(_o.lobby))
        return [];
    return kfo_ja(_o.lobby, "players");
}

function kfo_lobby_set()
{
    var _o = kfo_get();
    if (is_struct(_o.lobby) && is_struct(kfo_jv(_o.lobby, "set")))
        return kfo_set_clean(_o.lobby.set);
    return _o.set;
}

function kfo_lobby_me()
{
    var _o = kfo_get();
    var _pl = kfo_lobby_players();
    for (var _i = 0; _i < array_length(_pl); _i++)
    {
        if (kfo_jn(_pl[_i], "pid", -2) == _o.my)
            return _pl[_i];
    }
    return undefined;
}

function kfo_lobby_matching()
{
    var _o = kfo_get();
    return is_struct(_o.lobby) && kfo_js(_o.lobby, "st", "lobby") == "match";
}
