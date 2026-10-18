// ===== Build 45: KNIGHT FIGHTS ONLINE - the menu pages (KNIGHT tab -> ONLINE, or the sign while you are in a room) =====
// "online":  PRACTICE / STEAM: HOST, JOIN, BROWSE / RELAY: CREATE, JOIN, LAN / NAME / SKIN / MORE OPTIONS
// "onl_opt": the player's own options (relay server, Steam lobby type, the others' SOULs: opacity, name labels, KEYBINDS)
// "onl_keys": KEYBINDS - the player's own match keys (from MORE OPTIONS or the room)
// "onl_br":  the public Steam rooms
// "lobby":   the room - its players on the left; READY or START, WATCH, SKIN, SETTINGS, INVITE, LEAVE ROOM on the right
// "onl_set": the room's settings by category, with the presets (the host changes them, everyone else can look)
// Typing (name, room code, server, a preset code) uses the hub's text box: ENTER keeps it, ESC cancels.

function kfo_ui_is_sub(_s)
{
    return _s == "online" || _s == "lobby" || string_pos("onl_", _s) == 1;
}

function kfo_ui_fields(_u)
{
    var _f = ["onl_scroll", "set_opt", "set_scroll", "set_focus", "br_row", "opt_row", "keys_row", "lob_scroll", "pg_row", "pg_scroll", "sk_cat", "sk_i", "sk_t0", "bs_cat", "bs_i", "bs_t0"];
    for (var _i = 0; _i < array_length(_f); _i++)
    {
        if (!variable_struct_exists(_u, _f[_i]))
            variable_struct_set(_u, _f[_i], 0);
    }
    if (!variable_struct_exists(_u, "keys_from"))
        _u.keys_from = "onl_opt";
    if (!variable_struct_exists(_u, "pg_from"))
        _u.pg_from = "onl_opt";
    if (!variable_struct_exists(_u, "opt_from"))
        _u.opt_from = "online";
    if (!variable_struct_exists(_u, "sk_from"))
        _u.sk_from = "online";
    if (!variable_struct_exists(_u, "bs_from"))
        _u.bs_from = "online";
}

function kfo_ui_open()
{
    var _u = global.knight_ui;
    kfo_get();
    kfo_ui_fields(_u);
    _u.sub = kfo_in_room() ? "lobby" : "online";
    _u.onl_row = 0;
    _u.onl_scroll = 0;
    _u.lob_row = 0;
    snd_play(snd_select);
}

// build 51: a shorter page - the everyday rows first, the relay server and the settings folded under MORE...
function kfo_ui_rows()
{
    // DRBR: BOSSES (every boss, its SOUL and sends, a practice against one) after PRACTICE
    var _l = ["howto", "practice", "bosses", "s_host", "s_join", "s_browse", "name", "skin", "more"];
    var _u = global.knight_ui;
    if (is_struct(_u) && variable_struct_exists(_u, "onl_more") && _u.onl_more)
        array_push(_l, "d_create", "d_join", "d_lan", "opts");
    return _l;
}

function kfo_ui_row_label(_id)
{
    switch (_id)
    {
        case "practice": return "PRACTICE";
        case "bosses": return "BOSSES";
        case "howto": return "HOW TO PLAY";
        case "s_host": return "HOST A ROOM";
        case "s_join": return "JOIN WITH CODE";
        case "s_browse": return "FIND ROOMS";
        case "d_create": return "RELAY: HOST";
        case "d_join": return "RELAY: JOIN";
        case "d_lan": return "RELAY: LAN";
        case "name": return "NAME";
        case "skin": return "SKIN";
        case "more": return (variable_struct_exists(global.knight_ui, "onl_more") && global.knight_ui.onl_more) ? "LESS..." : "MORE...";
        case "opts": return "SETTINGS";
    }
    return _id;
}

// build 47: the others' SOULs moved to SOUL VISIBILITY; SOUL APPEARANCE, MATCH VIEW and the online MUSIC are new
function kfo_ui_opt_rows()
{
    return ["server", "vis", "view", "mview", "keys", "song", "done"];
}

// the online MUSIC row: -1 = the hub's own SONG setting, 0 = DEFAULT (each knight's and boss's own music), then every song of
// the list (DRBR 1.0.1: a song picked plays through the whole match, over every boss - kbr_mus_own)
function kfo_song_name(_i)
{
    if (_i < 0)
        return "AS IN THE HUB";
    if (_i == 0)
        return "DEFAULT";
    var _s = global.knight_songs[clamp(_i, 0, array_length(global.knight_songs) - 1)];
    return string_upper(_s.name);
}

// the lobby's rows (the host has START where the others have READY)
// build 47: SPECTATE MATCH and JOIN MATCH while a match runs (greyed with the reason when they cannot be used), your SOUL
// COLOR, MORE OPTIONS, COPY CODE and CONNECTION HELP
function kfo_ui_lobby_rows()
{
    var _o = kfo_get();
    var _l = [kfo_is_host() ? "start" : "ready"];
    if (kfo_lobby_matching() && !kfo_ui_me_playing())
        array_push(_l, "spectate", "join");
    array_push(_l, "name", "skin", "look", "keys", "options", "settings", "bosses");
    // build 49: the host adds / removes bots and sets each one's difficulty
    if (kfo_is_host())
        array_push(_l, "bots");
    if (_o.mode == "steam")
        array_push(_l, "invite");
    if (!kfo_prac_room() && _o.code != "")
        array_push(_l, "copy");
    array_push(_l, "help");
    if (kfo_is_host() && !kfo_prac_room() && array_length(kfo_ui_kickable()) > 0)
        array_push(_l, "kick");
    array_push(_l, "leave");
    return _l;
}

// this game plays in the running match (still standing)
function kfo_ui_me_playing()
{
    var _me = kfo_lobby_me();
    return !is_undefined(_me) && kfo_jn(_me, "inm", 0) == 1 && is_struct(global.kfo.M) && !global.kfo.M.out && global.kfo.M.me;
}

// why a room row cannot be used now ("" = it can)
function kfo_ui_lobby_why(_id)
{
    var _me = kfo_lobby_me();
    switch (_id)
    {
        case "spectate":
            if (kfo_ui_can_watch())
                return "";
            var _w = is_undefined(_me) ? "" : kfo_js(_me, "why", "");
            return (_w != "") ? _w : "You cannot watch this match.";
        case "join":
            return "A match that started takes no new players. SPECTATE it - you can play the next one.";
        case "ready":
            if (kfo_lobby_matching())
                return "A match is running. You can play the next one.";
            return "";
        case "skin":
            if (kfo_lobby_matching() && !is_undefined(_me) && kfo_jn(_me, "inm", 0) == 1)
                return "Not during your match.";
            return "";
    }
    return "";
}

// the players the host can remove (not you, not bots)
function kfo_ui_kickable()
{
    var _o = kfo_get();
    var _l = [];
    if (!kfo_is_host() || !is_struct(_o.H))
        return _l;
    for (var _i = 0; _i < array_length(_o.H.pl); _i++)
    {
        var _p = _o.H.pl[_i];
        if (_p.pid != _o.my && !_p.bot)
            array_push(_l, _p);
    }
    return _l;
}

// WATCH is offered when the host says this player may watch (SPECTATORS on, or REJOIN for a player back in the room)
function kfo_ui_can_watch()
{
    var _me = kfo_lobby_me();
    if (!is_struct(_me))
        return false;
    if (kfo_jn(_me, "inm", 0) == 1 && is_struct(global.kfo.M) && !global.kfo.M.out)
        return false;
    return kfo_jn(_me, "rj", 0) == 1;
}

function kfo_prac_room()
{
    var _o = kfo_get();
    return _o.prac || (is_struct(_o.lobby) && kfo_jn(_o.lobby, "prac", 0) == 1);
}

// ---------- typing ----------
function kfo_ui_text(_what)
{
    var _o = kfo_get();
    var _t = "";
    var _lines = [];
    var _start = "";
    switch (_what)
    {
        case "name":
            _t = "YOUR NAME";
            _lines = ["The others see this name (12 letters max).", "ENTER: OK     ESC: cancel"];
            _start = _o.name;
            break;
        case "code":
            _t = "RELAY ROOM CODE";
            _lines = ["The 5 letters the host's screen shows.", "ENTER: join     ESC: cancel"];
            _start = (_o.lastcode == "LOCAL" || string_length(_o.lastcode) != 5) ? "" : _o.lastcode;
            break;
        case "scode":
            _t = "STEAM ROOM CODE";
            _lines = ["The 7 letters the host's screen shows.", "ENTER: join     ESC: cancel"];
            _start = (string_length(_o.lastcode) == 7) ? _o.lastcode : "";
            break;
        case "server":
            _t = "SERVER";
            _lines = ["The address of the relay server, e.g. 203.0.113.5:7777", "ENTER: OK     ESC: cancel"];
            _start = kfo_server_text();
            break;
        case "hex":
            _t = "SOUL COLOR CODE";
            _lines = ["6 digits RRGGBB or 3 digits RGB, e.g. A040FF (0-9 and A-F).", "ENTER: OK     ESC: cancel"];
            _start = kfo_col_hex(_o.look.col);
            break;
        case "import":
            _t = "PASTE A SETTINGS CODE";
            _lines = ["CTRL+V pastes (a code starts with KF45:).", "ENTER: use it     ESC: cancel"];
            _start = clipboard_has_text() ? clipboard_get_text() : "";
            break;
    }
    var _m = knight_ui_modal("kfo_text", _t, _lines, []);
    _m.data = _what;
    _m.buf = _start;
    keyboard_string = _start;
}

function kfo_ui_text_step(_m)
{
    var _what = _m.data;
    var _max = 12;
    switch (_what)
    {
        case "server": _max = 40; break;
        case "code": _max = 5; break;
        case "scode": _max = 7; break;
        case "import": _max = 4000; break;
        case "hex": _max = 7; break;
    }
    var _s = keyboard_string;
    if (_what == "hex")
    {
        // only # and the hex digits get in (anything else is not part of a color code)
        var _hf = "";
        for (var _i = 1; _i <= string_length(_s); _i++)
        {
            var _hc = string_upper(string_char_at(_s, _i));
            if (string_pos(_hc, "#0123456789ABCDEF") > 0)
                _hf += _hc;
        }
        _s = _hf;
    }
    else if (_what != "import")
        _s = knight_name_clean_live(keyboard_string);
    if (_what == "import" && keyboard_check(vk_control) && keyboard_check_pressed(ord("V")) && clipboard_has_text())
        _s = clipboard_get_text();
    if (_what == "code" || _what == "scode")
        _s = kfo_clean_code(_s);
    if (_what == "server")
    {
        var _f = "";
        for (var _i = 1; _i <= string_length(_s); _i++)
        {
            var _c = string_char_at(_s, _i);
            var _n = ord(_c);
            if ((_n >= 48 && _n <= 58) || (_n >= 65 && _n <= 90) || (_n >= 97 && _n <= 122) || _c == "." || _c == "-")
                _f += _c;
        }
        _s = _f;
    }
    _m.buf = string_copy(_s, 1, _max);
    if (keyboard_string != _m.buf)
        keyboard_string = _m.buf;
    if (keyboard_check_pressed(vk_enter) || knight_pad_pressed(gp_face1))
        kfo_ui_text_done(_what, _m.buf);
    else if (keyboard_check_pressed(vk_escape) || knight_pad_pressed(gp_face2))
        knight_ui_modal_close();
    return 0;
}

function kfo_ui_text_done(_what, _s)
{
    var _o = kfo_get();
    switch (_what)
    {
        case "name":
            var _nm = kfo_clean_name(_s);
            if (_nm == "")
            {
                knight_ui_warn("A name needs at least one letter.");
                return 0;
            }
            // build 52: in a room the others see it at once
            kfo_name_change(_nm);
            knight_ui_modal_close();
            snd_play(snd_select);
            break;
        case "code":
            var _c = kfo_clean_code(_s);
            if (string_length(_c) != 5)
            {
                knight_ui_warn("A relay room code is 5 letters.");
                return 0;
            }
            knight_ui_modal_close();
            snd_play(snd_select);
            kfo_join(_c);
            break;
        case "scode":
            var _sc = kfo_clean_code(_s);
            if (string_length(_sc) != 7)
            {
                knight_ui_warn("A Steam room code is 7 letters.");
                return 0;
            }
            knight_ui_modal_close();
            snd_play(snd_select);
            kfo_steam_join_code(_sc);
            break;
        case "server":
            var _p = kfo_parse_server(_s);
            if (is_undefined(_p))
            {
                knight_ui_warn("That is not a server address (name or IP, then :port).");
                return 0;
            }
            _o.srv = _p[0];
            _o.port = _p[1];
            kfo_ini_save();
            knight_ui_modal_close();
            snd_play(snd_select);
            break;
        case "hex":
            var _hc = kfo_hex_col(_s, -1);
            if (_hc < 0)
            {
                knight_ui_warn("Not a color code: 6 digits RRGGBB (or 3: RGB), each 0-9 or A-F.");
                return 0;
            }
            _o.look.col = _hc;
            kfo_ini_save();
            kfo_look_sent();
            knight_ui_modal_close();
            snd_play(snd_select);
            break;
        case "import":
            var _set = kfo_set_from_text(_s);
            if (is_undefined(_set))
            {
                knight_ui_warn("That is not a DRBR settings code.");
                return 0;
            }
            knight_ui_modal_close();
            if (kfo_ui_set_apply(_set))
                knight_ui_tell("Settings code used.");
            break;
    }
    return 1;
}

// ---------- input ----------
function kfo_ui_step(_up, _down, _left, _right, _ok, _back, _alt)
{
    var _u = global.knight_ui;
    var _o = kfo_get();
    kfo_ui_fields(_u);
    // the room is gone (connection lost, kicked): back to the ONLINE page, which says why
    if ((_u.sub == "lobby" || _u.sub == "onl_set") && !kfo_in_room())
    {
        _u.sub = "online";
        _u.onl_row = 0;
    }
    // joined: straight into the room
    if ((_u.sub == "online" || _u.sub == "onl_br") && kfo_in_room())
    {
        _u.sub = "lobby";
        _u.lob_row = 0;
        snd_play(snd_select);
        return 0;
    }
    switch (_u.sub)
    {
        case "online": return kfo_ui_step_online(_up, _down, _left, _right, _ok, _back, _alt);
        case "onl_opt": return kfo_ui_step_opt(_up, _down, _left, _right, _ok, _back);
        case "onl_br": return kfo_ui_step_browse(_up, _down, _left, _right, _ok, _back, _alt);
        case "lobby": return kfo_ui_step_lobby(_up, _down, _left, _right, _ok, _back, _alt);
        case "onl_set": return kfo_ui_step_set(_up, _down, _left, _right, _ok, _back);
        case "onl_keys": return kfo_ui_step_keys(_up, _down, _left, _right, _ok, _back);
        // DRBR: the SKINS page (online_skin53.gml) and the BOSSES page (online_boss53.gml)
        case "onl_skin": return kfo_ui_step_skin(_up, _down, _left, _right, _ok, _back, _alt);
        case "onl_boss": return kfo_ui_step_boss(_up, _down, _left, _right, _ok, _back, _alt);
        case "onl_view":
        case "onl_look":
        case "onl_bots":
        case "onl_bot":
        case "onl_inv":
        case "onl_mview": return kfo_ui_step_pg(_u.sub, _up, _down, _left, _right, _ok, _back);
    }
    return 0;
}

function kfo_ui_step_online(_up, _down, _left, _right, _ok, _back, _alt)
{
    var _u = global.knight_ui;
    var _o = kfo_get();
    if (kfo_busy())
    {
        // connecting: X stops it
        if (_back)
        {
            kfo_close("");
            snd_play(snd_menumove);
        }
        return 0;
    }
    if (_back)
    {
        _u.sub = "";
        // (DRBR 1.0.1: up to the top bar, on the ONLINE page)
        if (_u.tab == 5)
            _u.focus = 0;
        snd_play(snd_menumove);
        return 0;
    }
    var _rows = kfo_ui_rows();
    var _n = array_length(_rows);
    if (_up || _down)
    {
        _u.onl_row = knight_ui_cycle(_u.onl_row, _up ? -1 : 1, _n);
        snd_play(snd_menumove);
    }
    _u.onl_scroll = clamp(_u.onl_scroll, max(0, _u.onl_row - 7), min(_u.onl_row, max(0, _n - 8)));
    var _id = _rows[clamp(_u.onl_row, 0, _n - 1)];
    // DRBR: Z opens the SKINS page (every skin with a preview); < > still changes it right here
    if (_id == "skin" && _ok)
        return kfo_ui_skin_open("online");
    if (_id == "skin" && (_left || _right || _alt))
    {
        // build 47: C puts the default skin (Kris) back
        _o.skin = _alt ? 1 : (1 + knight_ui_cycle(_o.skin - 1, _left ? -1 : 1, kfo_skin_count()));
        kfo_ini_save();
        snd_play(snd_menumove);
        return 0;
    }
    if (!_ok)
        return 0;
    if (string_pos("s_", _id) == 1 && !kfo_steam_ready())
    {
        knight_ui_warn(kfo_steam_why());
        return 0;
    }
    switch (_id)
    {
        case "practice":
            _o.err = "";
            kfo_practice_start();
            snd_play(snd_select);
            break;
        case "bosses":
            kfo_ui_boss_open("online");
            break;
        case "more":
            _u.onl_more = !(variable_struct_exists(_u, "onl_more") && _u.onl_more);
            snd_play(snd_select);
            break;
        case "howto":
            _o.err = "";
            var _tw = kfo_tut_start();
            if (_tw != "")
                knight_ui_warn(_tw);
            else
                snd_play(snd_select);
            break;
        case "s_host":
            _o.err = "";
            kfo_steam_host();
            snd_play(snd_select);
            break;
        case "s_join":
            kfo_ui_text("scode");
            break;
        case "s_browse":
            _u.sub = "onl_br";
            _u.br_row = 0;
            kfo_steam_browse();
            snd_play(snd_select);
            break;
        case "d_create":
            _o.err = "";
            kfo_create();
            snd_play(snd_select);
            break;
        case "d_join":
            kfo_ui_text("code");
            break;
        case "d_lan":
            _o.err = "";
            kfo_join_local();
            snd_play(snd_select);
            break;
        case "name":
            kfo_ui_text("name");
            break;
        case "opts":
            _u.sub = "onl_opt";
            _u.opt_row = 0;
            snd_play(snd_select);
            break;
    }
    return 0;
}

function kfo_ui_step_opt(_up, _down, _left, _right, _ok, _back)
{
    var _u = global.knight_ui;
    var _o = kfo_get();
    var _rows = kfo_ui_opt_rows();
    var _n = array_length(_rows);
    if (_back)
    {
        _u.sub = _u.opt_from;
        snd_play(snd_menumove);
        knight_preview_stop();
        return 0;
    }
    if (_up || _down)
    {
        _u.opt_row = knight_ui_cycle(_u.opt_row, _up ? -1 : 1, _n);
        snd_play(snd_menumove);
    }
    var _id = _rows[clamp(_u.opt_row, 0, _n - 1)];
    var _d = _left ? -1 : 1;
    if (!_ok && !_left && !_right)
        return 0;
    switch (_id)
    {
        case "server":
            if (_ok)
                kfo_ui_text("server");
            return 0;
        case "vis":
            _o.vis = knight_ui_cycle(_o.vis, _d, 3);
            break;
        case "view":
        case "look":
        case "mview":
            if (_ok)
                kfo_ui_pg_open("onl_" + _id, "onl_opt");
            return 0;
        case "song":
            // < >: the next song; Z: the song list (build 48: title and artist of every song, C listens there)
            if (_ok)
            {
                knight_preview_stop();
                knight_songpick_open("onl");
                return 0;
            }
            knight_preview_stop();
            _o.song = ((_o.song + 1 + _d + array_length(global.knight_songs) + 1) mod (array_length(global.knight_songs) + 1)) - 1;
            break;
        case "keys":
            if (_ok)
                kfo_ui_keys_open("onl_opt");
            return 0;
        case "done":
            if (_ok)
            {
                _u.sub = _u.opt_from;
                knight_preview_stop();
                snd_play(snd_select);
            }
            return 0;
    }
    kfo_ini_save();
    snd_play(snd_menumove);
    return 0;
}

function kfo_vis_name(_v)
{
    switch (_v)
    {
        case 0: return "PRIVATE";
        case 2: return "PUBLIC";
    }
    return "FRIENDS";
}

function kfo_ui_step_browse(_up, _down, _left, _right, _ok, _back, _alt)
{
    var _u = global.knight_ui;
    var _o = kfo_get();
    if (_back)
    {
        _u.sub = "online";
        snd_play(snd_menumove);
        return 0;
    }
    if (_alt)
    {
        kfo_steam_browse();
        snd_play(snd_select);
        return 0;
    }
    var _n = array_length(_o.browse);
    if (_n == 0)
        return 0;
    if (_up || _down)
    {
        _u.br_row = knight_ui_cycle(_u.br_row, _up ? -1 : 1, _n);
        snd_play(snd_menumove);
    }
    if (_ok)
    {
        var _e = _o.browse[clamp(_u.br_row, 0, _n - 1)];
        if (_e.ver != kfo_version())
        {
            // DRBR (update 10): a newer room is kept for after the update; the warning says how to update
            if (_e.ver > kfo_version() && variable_struct_exists(_e, "lid"))
                kdr_pending_join(_e.lid, _e.ver, variable_struct_exists(_e, "host") ? _e.host : "");
            knight_ui_warn(kdr_build_why(_e.ver));
            return 0;
        }
        if (_e.np >= _e.mx)
        {
            knight_ui_warn("That room is full.");
            return 0;
        }
        snd_play(snd_select);
        kfo_steam_join_id(_e.lid);
    }
    return 0;
}

function kfo_ui_step_lobby(_up, _down, _left, _right, _ok, _back, _alt)
{
    var _u = global.knight_ui;
    var _o = kfo_get();
    if (_back)
    {
        // back up to the top bar (the ONLINE page shows the room); you stay in the room (not ready)
        kfo_ui_unready();
        _u.sub = "";
        if (_u.tab == 5)
            _u.focus = 0;
        snd_play(snd_menumove);
        return 0;
    }
    var _rows = kfo_ui_lobby_rows();
    var _n = array_length(_rows);
    if (_up || _down)
    {
        _u.lob_row = knight_ui_cycle(_u.lob_row, _up ? -1 : 1, _n);
        snd_play(snd_menumove);
    }
    _u.lob_row = clamp(_u.lob_row, 0, _n - 1);
    _u.lob_scroll = clamp(_u.lob_scroll, max(0, _u.lob_row - (kfo_ui_lobby_shown() - 1)), min(_u.lob_row, max(0, _n - kfo_ui_lobby_shown())));
    var _id = _rows[_u.lob_row];
    // C: START for the host from anywhere on the page
    if (_alt && kfo_is_host())
    {
        kfo_ui_start();
        return 0;
    }
    // your SOUL COLOR: < > the presets right here, Z the whole SOUL APPEARANCE page
    if (_id == "look" && (_left || _right))
    {
        kfo_ui_pg_change("onl_look", "col", _left ? -1 : 1, false);
        kfo_ini_save();
        snd_play(snd_menumove);
        return 0;
    }
    // DRBR: Z opens the SKINS page (wearing one there is checked the same way)
    if (_id == "skin" && _ok)
        return kfo_ui_skin_open("lobby");
    if (_id == "skin" && (_left || _right))
    {
        if (kfo_ui_lobby_why("skin") != "")
        {
            knight_ui_warn(kfo_ui_lobby_why("skin"));
            return 0;
        }
        _o.skin = 1 + knight_ui_cycle(_o.skin - 1, _left ? -1 : 1, kfo_skin_count());
        kfo_ini_save();
        kfo_up({ k: "skin", skin: _o.skin });
        snd_play(snd_menumove);
        return 0;
    }
    // build 52: CHANGE NAME (the typing box; kfo_ui_text_done sends it to the room)
    if (_id == "name" && _ok)
    {
        kfo_ui_text("name");
        snd_play(snd_select);
        return 0;
    }
    if (_id == "ready" && (_ok || _left || _right))
    {
        if (kfo_lobby_matching())
        {
            knight_ui_warn("A match is running. You can play the next one.");
            return 0;
        }
        var _me = kfo_lobby_me();
        var _on = is_undefined(_me) ? 0 : kfo_jn(_me, "rd", 0);
        kfo_up({ k: "ready", on: _on ? 0 : 1 });
        snd_play(snd_select);
        return 0;
    }
    if (!_ok)
        return 0;
    switch (_id)
    {
        case "start":
            kfo_ui_start();
            break;
        case "spectate":
            if (kfo_ui_lobby_why("spectate") != "")
            {
                knight_ui_warn(kfo_ui_lobby_why("spectate"));
                break;
            }
            kfo_up({ k: "watch" });
            snd_play(snd_select);
            knight_ui_tell("Joining the match as a watcher...");
            break;
        case "join":
            knight_ui_warn(kfo_ui_lobby_why("join"));
            break;
        case "look":
            kfo_ui_pg_open("onl_look", "lobby");
            break;
        case "options":
            _u.sub = "onl_opt";
            _u.opt_row = 0;
            _u.opt_from = "lobby";
            snd_play(snd_select);
            break;
        case "copy":
            clipboard_set_text(_o.code);
            snd_play(snd_select);
            knight_ui_tell("Room code " + _o.code + " copied (CTRL+V to paste it).");
            break;
        case "help":
            knight_ui_modal("kfo_help", "CONNECTION HELP", kfo_ui_conn_help(), [{ t: "OK", a: "close" }]);
            break;
        case "keys":
            kfo_ui_keys_open("lobby");
            break;
        case "bots":
            kfo_ui_pg_open("onl_bots", "lobby");
            break;
        case "settings":
            _u.sub = "onl_set";
            _u.set_row = 0;
            _u.set_opt = 0;
            _u.set_scroll = 0;
            _u.set_focus = 0;
            snd_play(snd_select);
            break;
        case "bosses":
            kfo_ui_boss_open("lobby");
            break;
        case "invite":
            // build 49: the in-game friends list (Z invites one); STEAM OVERLAY is a row there
            kfo_ui_inv_open("lobby");
            break;
        case "kick":
            var _kl = kfo_ui_kickable();
            var _opts = [];
            for (var _i = 0; _i < array_length(_kl) && _i < 7; _i++)
                array_push(_opts, { t: knight_fit(_kl[_i].n, 300), a: "kfo_kick:" + string(_kl[_i].pid) });
            array_push(_opts, { t: "Nobody", a: "close" });
            knight_ui_modal("kfo_kick", "REMOVE A PLAYER?", ["They leave the room and cannot come back into it."], _opts);
            break;
        case "leave":
            var _m = knight_ui_modal("kfo_leave", "LEAVE THE ROOM?", [kfo_is_host() ? "You are the host: the next player takes the room over." : "You can join again with the code."],
                [{ t: "Stay", a: "close" }, { t: "Leave", a: "kfo_leave" }]);
            break;
    }
    return 0;
}

function kfo_ui_unready()
{
    var _me = kfo_lobby_me();
    if (!is_undefined(_me) && kfo_jn(_me, "rd", 0) == 1 && !kfo_is_host())
        kfo_up({ k: "ready", on: 0 });
}

function kfo_ui_start()
{
    var _why = kfo_host_start();
    if (_why != "")
    {
        knight_ui_warn(_why);
        return 0;
    }
    return 1;
}

// the room's rows shown at once (the rest scroll, as on the ONLINE page)
function kfo_ui_lobby_shown()
{
    return 6;
}

// ---------- KEYBINDS (build 46): the player's own keys for the match ----------
// rows: every action of kfo_key_list, RESET KEYS, DONE. Z on an action waits for the new key (kfo_ui_key_step). A key
// another action had: the two swap. The arrows, X / SHIFT (the game's own slow walk), ENTER, ESC and F4 are refused.
function kfo_ui_keys_rows()
{
    var _l = [];
    var _kl = kfo_key_list();
    for (var _i = 0; _i < array_length(_kl); _i++)
    {
        var _ke = _kl[_i];
        array_push(_l, _ke[0]);
    }
    array_push(_l, "reset", "done");
    return _l;
}

function kfo_ui_keys_open(_from)
{
    var _u = global.knight_ui;
    kfo_ui_fields(_u);
    _u.keys_from = _from;
    _u.sub = "onl_keys";
    _u.keys_row = 0;
    snd_play(snd_select);
    return 1;
}

function kfo_ui_keys_back()
{
    var _u = global.knight_ui;
    _u.sub = (_u.keys_from == "lobby" && kfo_in_room()) ? "lobby" : ((_u.keys_from == "lobby") ? "online" : "onl_opt");
    return 1;
}

function kfo_ui_step_keys(_up, _down, _left, _right, _ok, _back)
{
    var _u = global.knight_ui;
    var _rows = kfo_ui_keys_rows();
    var _n = array_length(_rows);
    if (_back)
    {
        kfo_ui_keys_back();
        snd_play(snd_menumove);
        return 0;
    }
    if (_up || _down)
    {
        _u.keys_row = knight_ui_cycle(_u.keys_row, _up ? -1 : 1, _n);
        snd_play(snd_menumove);
    }
    _u.keys_row = clamp(_u.keys_row, 0, _n - 1);
    if (!_ok)
        return 0;
    var _id = _rows[_u.keys_row];
    switch (_id)
    {
        case "reset":
            kfo_keys_reset();
            snd_play(snd_select);
            knight_ui_tell("Every key is back to its default.");
            return 0;
        case "done":
            kfo_ui_keys_back();
            snd_play(snd_select);
            return 0;
    }
    // wait for the new key
    var _m = knight_ui_modal("kfo_key", kfo_key_title(_id), ["Press the key you want (now " + kfo_key_label(_id) + ").", "ESC: cancel"], []);
    _m.data = _id;
    _m.buf = "";
    _m.free = false;
    snd_play(snd_select);
    return 0;
}

// the first key that went down this step (-1: none)
function kfo_key_scan()
{
    if (!keyboard_check_pressed(vk_anykey))
        return -1;
    for (var _k = 8; _k <= 254; _k++)
    {
        if (keyboard_check_pressed(_k))
            return _k;
    }
    return -1;
}

// the KEYBINDS box waiting for a key: the key that opened it is let go first; ESC (or a controller's cancel) gives up
function kfo_ui_key_step(_m)
{
    if (_m.t < 2)
        return 0;
    if (!_m.free)
    {
        if (!keyboard_check(vk_anykey))
            _m.free = true;
        return 0;
    }
    if (keyboard_check_pressed(vk_escape) || knight_pad_pressed(gp_face2))
    {
        knight_ui_modal_close();
        snd_play(snd_menumove);
        return 0;
    }
    var _k = kfo_key_scan();
    if (_k < 0)
        return 0;
    var _id = _m.data;
    var _why = kfo_key_why(_k);
    if (_why != "")
    {
        _m.lines = ["Press the key you want (now " + kfo_key_label(_id) + ").", "ESC: cancel", "Not " + kfo_key_name(_k) + ": " + _why + "."];
        snd_play(snd_cantselect);
        return 0;
    }
    // the action that had this key (it gets this one's old key)
    var _other = "";
    var _kl = kfo_key_list();
    for (var _i = 0; _i < array_length(_kl); _i++)
    {
        var _ke = _kl[_i];
        if (_ke[0] != _id && kfo_key(_ke[0]) == _k)
            _other = _ke[0];
    }
    kfo_key_set(_id, _k);
    kfo_ini_save();
    knight_ui_modal_close();
    snd_play(snd_select);
    if (_other != "")
        knight_ui_tell(kfo_key_title(_id) + ": " + kfo_key_name(_k) + ". " + kfo_key_title(_other) + " is now " + kfo_key_label(_other) + ".");
    else
        knight_ui_tell(kfo_key_title(_id) + ": " + kfo_key_name(_k) + ".");
    return 1;
}

// ---------- the settings page ----------
// the rows of the right column for the category _cat (option ids, or the preset actions)
function kfo_ui_set_items(_cat)
{
    var _l = [];
    if (_cat == kfo_cat_pre())
    {
        var _p = kfo_presets();
        for (var _i = 0; _i < array_length(_p); _i++)
        {
            // DRBR: a boss preset only when its boss is in this build
            if (kfo_preset_ok(_i))
                array_push(_l, "p" + string(_i));
        }
        array_push(_l, "c1", "c2", "c3", "s1", "s2", "s3", "export", "import", "reset");
        return _l;
    }
    var _o = kfo_opts_of(_cat);
    for (var _i = 0; _i < array_length(_o); _i++)
        array_push(_l, _o[_i].oid);
    return _l;
}

function kfo_ui_set_item_label(_id)
{
    if (string_char_at(_id, 1) == "p" && string_length(_id) <= 3)
        return kfo_preset_name(real(string_digits(_id)));
    switch (_id)
    {
        case "c1": return "LOAD CUSTOM 1";
        case "c2": return "LOAD CUSTOM 2";
        case "c3": return "LOAD CUSTOM 3";
        case "s1": return "SAVE AS CUSTOM 1";
        case "s2": return "SAVE AS CUSTOM 2";
        case "s3": return "SAVE AS CUSTOM 3";
        case "export": return "COPY SETTINGS CODE";
        case "import": return "PASTE SETTINGS CODE";
        case "reset": return "RESET TO CLASSIC";
    }
    var _e = kfo_opt_find(_id);
    return is_undefined(_e) ? _id : _e.lab;
}

// the settings the page shows: the host's own (being changed), everyone else's from the lobby
function kfo_ui_set_cur()
{
    var _o = kfo_get();
    if (kfo_is_host() && is_struct(_o.H))
        return _o.H.set;
    return kfo_lobby_set();
}

// the host uses new settings (lobby only); false and a warning when it cannot
function kfo_ui_set_apply(_s)
{
    if (!kfo_is_host())
    {
        knight_ui_warn("Only the host changes the settings.");
        return false;
    }
    if (kfo_lobby_matching())
    {
        knight_ui_warn("Not while a match is running.");
        return false;
    }
    kfo_host_set(_s);
    return true;
}

function kfo_ui_step_set(_up, _down, _left, _right, _ok, _back)
{
    var _u = global.knight_ui;
    var _cats = kfo_cats();
    var _nc = array_length(_cats);
    _u.set_row = clamp(_u.set_row, 0, _nc - 1);
    var _items = kfo_ui_set_items(_u.set_row);
    var _ni = array_length(_items);
    if (_u.set_focus == 0)
    {
        if (_back)
        {
            _u.sub = "lobby";
            snd_play(snd_menumove);
            return 0;
        }
        if (_up || _down)
        {
            _u.set_row = knight_ui_cycle(_u.set_row, _up ? -1 : 1, _nc);
            _u.set_opt = 0;
            _u.set_scroll = 0;
            snd_play(snd_menumove);
        }
        if (_ok || _right)
        {
            _u.set_focus = 1;
            _u.set_opt = 0;
            _u.set_scroll = 0;
            snd_play(snd_select);
        }
        return 0;
    }
    if (_back)
    {
        _u.set_focus = 0;
        snd_play(snd_menumove);
        return 0;
    }
    if (_up || _down)
    {
        _u.set_opt = knight_ui_cycle(_u.set_opt, _up ? -1 : 1, _ni);
        snd_play(snd_menumove);
    }
    _u.set_opt = clamp(_u.set_opt, 0, _ni - 1);
    _u.set_scroll = clamp(_u.set_scroll, max(0, _u.set_opt - 7), min(_u.set_opt, max(0, _ni - 8)));
    var _id = _items[_u.set_opt];
    var _s = kfo_ui_set_cur();
    // presets
    if (_u.set_row == kfo_cat_pre())
    {
        if (!_ok)
            return 0;
        var _n = undefined;
        if (string_char_at(_id, 1) == "p")
            _n = kfo_preset_apply(real(string_digits(_id)));
        else if (_id == "c1" || _id == "c2" || _id == "c3")
        {
            _n = kfo_custom_load(real(string_digits(_id)));
            if (is_undefined(_n))
            {
                knight_ui_warn("That custom slot is empty.");
                return 0;
            }
        }
        else if (_id == "s1" || _id == "s2" || _id == "s3")
        {
            kfo_custom_save(real(string_digits(_id)), _s);
            knight_ui_tell("Saved as CUSTOM " + string_digits(_id) + ".");
            snd_play(snd_select);
            return 0;
        }
        else if (_id == "export")
        {
            clipboard_set_text(kfo_set_to_text(_s));
            knight_ui_tell("Settings code copied - paste it to a friend.");
            snd_play(snd_select);
            return 0;
        }
        else if (_id == "import")
        {
            if (!kfo_is_host())
            {
                knight_ui_warn("Only the host changes the settings.");
                return 0;
            }
            kfo_ui_text("import");
            return 0;
        }
        else if (_id == "reset")
            _n = kfo_preset_apply(0);
        if (!is_undefined(_n) && kfo_ui_set_apply(_n))
        {
            knight_ui_tell("Now playing with " + _n.pre + ".");
            snd_play(snd_select);
        }
        return 0;
    }
    if (!_ok && !_left && !_right)
        return 0;
    var _r = kfo_opt_change(_s, _id, _left ? -1 : 1);
    if (is_string(_r))
    {
        knight_ui_warn(_r);
        return 0;
    }
    if (kfo_ui_set_apply(_r))
        snd_play(_ok ? snd_select : snd_menumove);
    return 0;
}

// modal buttons of the online pages
function kfo_ui_modal_do(_a)
{
    var _u = global.knight_ui;
    if (string_pos("kfo_kick:", _a) == 1)
    {
        knight_ui_modal_close();
        var _pid = kfo_num(string_delete(_a, 1, 9), -1);
        if (kfo_host_kick(_pid))
        {
            knight_ui_tell("Removed from the room.");
            snd_play(snd_select);
        }
        _u.lob_row = 0;
        return true;
    }
    if (_a == "kfo_inv_join")
    {
        knight_ui_modal_close();
        kfo_inv_join();
        snd_play(snd_select);
        return true;
    }
    if (_a == "kfo_inv_no")
    {
        knight_ui_modal_close();
        global.kfo.inv_in = undefined;
        snd_play(snd_menumove);
        return true;
    }
    if (_a == "kh_reset")
    {
        knight_ui_modal_close();
        kfo_settings_reset();
        snd_play(snd_select);
        knight_ui_tell("Mod settings reset: other SOULs shown at 70%, default keys.");
        return true;
    }
    if (_a == "kfo_leave")
    {
        knight_ui_modal_close();
        kfo_leave();
        _u.sub = "online";
        _u.onl_row = 0;
        snd_play(snd_smallswing);
        return true;
    }
    return false;
}

// ---------- the description in the top bar ----------
function kfo_ui_desc()
{
    var _u = global.knight_ui;
    var _o = kfo_get();
    kfo_ui_fields(_u);
    if (_u.sub == "online")
    {
        if (kfo_busy())
            return (_o.mode == "steam") ? "Talking to Steam...#X: stop." : ("Connecting to " + kfo_server_text() + "...#X: stop.");
        var _rows = kfo_ui_rows();
        switch (_rows[clamp(_u.onl_row, 0, array_length(_rows) - 1)])
        {
            case "practice": return "The battle royale with bots, on your own.#No server needed. Z: start a practice room.";
            case "bosses": return "Z: every boss you can fight - its SOUL, its#sends - and a practice match against one.";
            case "howto": return kfo_tut_done() ? "The guided lesson (you finished it).#Z: play it again." : "New here? A guided practice match, one#step at a time. Z: start.";
            case "s_host": return "Make a room on Steam and get a code to#give your friends. Z: host.";
            case "s_join": return "Got a code from a friend? Z: type it#(7 letters).";
            case "s_browse": return "Z: see open rooms on Steam and join one.";
            case "more": return "Z: other ways to connect (a relay server,#LAN) and the online SETTINGS.";
            case "d_create": return "No Steam? Host a room on a relay server#and get a code. Z: create.";
            case "d_join": return "Z: type a relay room code (5 letters).";
            case "d_lan": return "Everyone on the same relay server (LAN,#Radmin) meets in one room. Z: join it.";
            case "name": return "Z: type the name the others see.";
            case "skin": return "Z: every skin, with a preview. < >: the next#one here. C: back to Kris.";
            case "opts": return "Z: the relay server, the room type, how the#others' SOULs look, your keys (KEYBINDS).";
        }
        return "";
    }
    if (_u.sub == "onl_opt")
    {
        var _or = kfo_ui_opt_rows();
        switch (_or[clamp(_u.opt_row, 0, array_length(_or) - 1)])
        {
            case "server": return "Z: type the relay server's address#(name or IP, then :port).";
            case "vis": return "< >: the Steam rooms you host: PRIVATE (invite#only), FRIENDS, or PUBLIC (in BROWSE).";
            case "view": return "Z: show the other SOULs, your SOUL COLOR,#names, their opacity, highlight yours.";
            case "look": return "Z: your own SOUL's color (presets, RGB, hex),#outline and highlight. Others see the color.";
            case "mview": return "Z: watching (camera, HUD), the match info and#network stats, shake, flashing, key hints.";
            case "song": return (kfo_get().song == 0) ? "DEFAULT: each boss brings its own music.#< >: or a song of your own, over every boss. Z: list." : "< >: your match music, over every boss (only on#your computer). DEFAULT: the bosses' own. Z: list.";
            case "keys": return "Z: your keys for the match (Hold Breath,#skills, the player list, quick settings...).";
            case "done": return "Z: back.";
        }
        return "";
    }
    if (_u.sub == "onl_view" || _u.sub == "onl_look" || _u.sub == "onl_mview" || _u.sub == "onl_bots" || _u.sub == "onl_bot" || _u.sub == "onl_inv")
    {
        var _pr = kfo_ui_pg_rows(_u.sub);
        return kfo_ui_pg_desc(_u.sub, _pr[clamp(_u.pg_row, 0, array_length(_pr) - 1)]);
    }
    if (_u.sub == "onl_keys")
    {
        var _kr = kfo_ui_keys_rows();
        var _kid = _kr[clamp(_u.keys_row, 0, array_length(_kr) - 1)];
        switch (_kid)
        {
            case "reset": return "Z: every key back to S, Z, C, A, TAB,#BACKSPACE, Q and V.";
            case "done": return "Z: back. The arrows move your SOUL and X#slows it: those are the game's own keys.";
        }
        return kfo_key_desc(_kid);
    }
    if (_u.sub == "onl_br")
        return "Z: join the room.   C: look again.   X: back";
    if (_u.sub == "onl_skin")
        return kfo_ui_skin_desc();
    if (_u.sub == "onl_boss")
        return kfo_ui_boss_desc();
    if (_u.sub == "lobby")
    {
        var _lr = kfo_ui_lobby_rows();
        switch (_lr[clamp(_u.lob_row, 0, array_length(_lr) - 1)])
        {
            case "start": return kfo_prac_room() ? "Z or C: start the practice match.#X: back." : "Z or C: start the match.   X: back#(the room's READY CHECK decides who plays)";
            case "ready": return kfo_ui_after_match() ? "Z: vote for a rematch (the host starts it when#the votes are in). X: back." : "Z: ready for the next match.#X: back (not ready).";
            case "spectate": return (kfo_ui_lobby_why("spectate") == "") ? "Z: watch the match that is running (you play#the next one). It goes on as it is." : ("NOT NOW: " + kfo_ui_lobby_why("spectate"));
            case "join": return "NOT NOW: a match takes no new players once it#started. SPECTATE it, play the next one.";
            case "look": return "< >: your SOUL's color (everyone sees it).#Z: all colors, your own mix, a color code.";
            case "options": return "Z: MORE OPTIONS (the others' SOULs, your SOUL,#watching, music, keys).";
            case "copy": return "Z: copy the room code " + kfo_get().code + "#(paste it to your friends).";
            case "help": return "Z: what to check when someone cannot join#or the match lags.";
            case "skin": return "Z: every skin, with a preview. < >: the next#one here. Only a look: everyone has the same HP.";
            case "name": return "Z: a new name. Everyone sees it at once#(in a match too: chat /name NEW NAME).";
            case "keys": return "Z: your keys for the match (Hold Breath,#skills, the player list, giving up).";
            case "settings": return kfo_is_host() ? "Z: the room's settings, presets and#mutators." : "Z: look at the room's settings#(the host changes them).";
            case "bosses": return kfo_is_host() ? "Z: every boss - its SOUL, its sends. Z there#puts one in the room or takes it out." : "Z: every boss - its SOUL, its sends - and#which ones this room fights.";
            case "bots": return "Z: add or remove bots and set each bot's#difficulty (DUMMY ... PERFECT, sliders).";
            case "invite": return "Z: your Steam friends - pick one and Z sends#a Steam invite to this room.";
            case "kick": return "Z: remove a player from the room#(they cannot come back into it).";
            case "leave": return "Z: leave the room." + (kfo_is_host() ? "#The next player becomes the host." : "");
        }
        return "";
    }
    if (_u.sub == "onl_set")
    {
        // (DRBR 1.0.1: not the host - they can look; only the host changes them: said here, it was small print under the title)
        if (!kfo_is_host() && _u.set_focus == 0 && _u.set_row != kfo_cat_pre())
            return "Only the host changes these settings.#Z: look at them.   X: back";
        if (_u.set_focus == 0)
            return kfo_cat_desc(_u.set_row);
        var _items = kfo_ui_set_items(_u.set_row);
        var _id = _items[clamp(_u.set_opt, 0, array_length(_items) - 1)];
        if (_u.set_row == kfo_cat_pre())
        {
            if (string_char_at(_id, 1) == "p" && string_length(_id) <= 3)
                return kfo_preset_desc(real(string_digits(_id)));
            switch (_id)
            {
                case "c1":
                case "c2":
                case "c3": return kfo_custom_exists(real(string_digits(_id))) ? "Z: use the settings you saved here." : "This slot is empty (SAVE AS CUSTOM fills it).";
                case "s1":
                case "s2":
                case "s3": return "Z: keep the room's settings in this slot#(on this computer).";
                case "export": return "Z: copy the room's settings as a code#to paste to a friend.";
                case "import": return "Z: paste a settings code (KF45:...).";
                case "reset": return "Z: back to CLASSIC.";
            }
            return "";
        }
        // DRBR: SENDS says which families that is in this room (CURRENT BOSS: the bosses it fights)
        if (_id == "skfam")
            return kfo_sends_desc(kfo_ui_set_cur());
        var _e = kfo_opt_find(_id);
        return is_undefined(_e) ? "" : _e.desc;
    }
    return "";
}

// ---------- drawing ----------
// DRBR 1.0.1: the ONLINE page on the top bar (before Z opens it): its menu as it is, with no row picked - the room's while you are
// in one
function kfo_ui_draw_tab(xx, yy)
{
    var _u = global.knight_ui;
    kfo_get();
    kfo_ui_fields(_u);
    global.kfo_ui_pvf = true;
    if (kfo_in_room())
        kfo_ui_draw_lobby(xx, yy);
    else
        kfo_ui_draw_online(xx, yy);
    global.kfo_ui_pvf = false;
    return 1;
}

// the ONLINE page drawn on the top bar: no row is picked (kfo_ui_draw_tab)
global.kfo_ui_pvf = false;
function kfo_ui_pv()
{
    return variable_global_exists("kfo_ui_pvf") && global.kfo_ui_pvf;
}

function kfo_ui_draw(xx, yy)
{
    var _u = global.knight_ui;
    kfo_ui_fields(_u);
    switch (_u.sub)
    {
        case "online": kfo_ui_draw_online(xx, yy); break;
        case "onl_opt": kfo_ui_draw_opt(xx, yy); break;
        case "onl_br": kfo_ui_draw_browse(xx, yy); break;
        case "lobby": kfo_ui_draw_lobby(xx, yy); break;
        case "onl_set": kfo_ui_draw_set(xx, yy); break;
        case "onl_keys": kfo_ui_draw_keys(xx, yy); break;
        case "onl_skin": kfo_ui_draw_skin(xx, yy); break;
        case "onl_boss": kfo_ui_draw_boss(xx, yy); break;
        case "onl_view":
        case "onl_look":
        case "onl_bots":
        case "onl_bot":
        case "onl_inv":
        case "onl_mview": kfo_ui_draw_pg(_u.sub, xx, yy); break;
    }
}

function kfo_ui_draw_online(xx, yy)
{
    var _u = global.knight_ui;
    var _o = kfo_get();
    var _pv = kfo_ui_pv();
    draw_set_color(c_white);
    draw_rectangle(xx + 300, yy + 91, xx + 305, yy + 410, false);
    knight_caption_hub("ONLINE", xx + 112, yy + 84);
    var _rows = kfo_ui_rows();
    var _busy = kfo_busy();
    var _steam = kfo_steam_ready();
    for (var _i = _u.onl_scroll; _i < array_length(_rows) && _i < _u.onl_scroll + 8; _i++)
    {
        var _y = yy + 104 + ((_i - _u.onl_scroll) * 36);
        // (DRBR 1.0.1: on the top bar - the ONLINE page before Z - no row is picked)
        var _hot = (_u.onl_row == _i) && !_pv;
        var _dim = _busy || (string_pos("s_", _rows[_i]) == 1 && !_steam);
        draw_set_color(_dim ? (_hot ? c_orange : c_gray) : (_hot ? c_yellow : c_white));
        knight_txt(xx + 100, _y, knight_fit(kfo_ui_row_label(_rows[_i]), 190));
        if (_hot && !_busy)
            knight_heart(xx + 75, _y + 10);
    }
    // more rows above / below: the game's arrows
    knight_ui_arrows(xx + 284, yy + 98, yy + 392, _u.onl_scroll > 0, _u.onl_scroll + 8 < array_length(_rows), _u.siner);
    // DRBR 1.0.1: the right side in the menu's size - DRBR, your name, your skin, then Steam and the relay server (or the skin /
    // the bosses while their row is picked), then what DRBR is or what is happening
    var _cx = xx + 443;
    var _id = _pv ? "" : _rows[clamp(_u.onl_row, 0, array_length(_rows) - 1)];
    draw_set_halign(fa_center);
    draw_set_color(c_yellow);
    knight_txt(_cx, yy + 96, "DRBR");
    draw_set_color(c_white);
    knight_txt(_cx, yy + 124, "BATTLE ROYALE");
    draw_set_color((_id == "name") ? c_yellow : c_white);
    knight_txt(_cx, yy + 160, knight_fit(_o.name, 250));
    var _sk = kfo_skin_ok(_o.skin);
    kfo_skin_head_draw(_sk, _cx - 96, yy + 198);
    // build 52: the look's own colour for its name (yellow while picked)
    draw_set_color((_id == "skin") ? c_yellow : (kfo_skin_cosmetic(_sk) ? kfo_skin_col(_sk) : c_white));
    knight_txt(_cx + 4, yy + 196, knight_fit("< " + string_upper(kfo_skin_name(_sk)) + " >", 160));
    // build 47: how you walk around the room with it (the skin's own walking frames)
    var _ws = kfo_world_skin_spr(_sk, 0);
    draw_sprite_ext(_ws, (current_time div 200) mod max(1, sprite_get_number(_ws)), _cx + 100, yy + 188, 1, 1, 0, c_white, 1);
    var _side = false;
    // build 52: picking a skin - its preview in place of the STEAM / RELAY lines
    if (_id == "skin")
    {
        kfo_ui_skin_preview(_sk, _cx, yy + 236);
        _side = true;
    }
    // DRBR: BOSSES picked: who there is to fight, in place of the STEAM / RELAY lines
    if (_id == "bosses")
    {
        kfo_ui_boss_teaser(_cx, yy + 240);
        _side = true;
    }
    if (!_side)
    {
        draw_set_color(_steam ? c_lime : make_color_rgb(255, 150, 120));
        knight_txt(_cx, yy + 236, knight_fit(_steam ? "STEAM: READY" : kfo_steam_why_short(), 262));
        draw_set_color(c_ltgray);
        knight_txt(_cx, yy + 268, knight_fit("RELAY: " + kfo_server_text(), 262));
        // status: connecting, or why the last try failed, or what DRBR is
        var _st = "";
        var _col = c_white;
        if (_busy)
        {
            _st = (_o.mode == "steam") ? "Talking to Steam..." : ((_o.st == "connecting") ? ("Connecting to " + kfo_server_text() + "...") : "Asking for the room...");
            _col = c_yellow;
        }
        else if (_o.err != "")
        {
            _st = _o.err;
            _col = make_color_rgb(255, 110, 110);
        }
        else
        {
            _st = "Up to 8 players. The last SOUL standing wins.";
            _col = c_gray;
        }
        draw_set_color(_col);
        knight_para_fit(_cx, yy + 308, _st, 262, 3);
    }
    draw_set_halign(fa_left);
}

function kfo_ui_draw_opt(xx, yy)
{
    var _u = global.knight_ui;
    var _o = kfo_get();
    draw_set_color(c_white);
    draw_rectangle(xx + 300, yy + 91, xx + 305, yy + 410, false);
    knight_caption_hub("OPTIONS", xx + 112, yy + 84);
    var _rows = kfo_ui_opt_rows();
    for (var _i = 0; _i < array_length(_rows); _i++)
    {
        var _y = yy + 108 + (_i * 36);
        var _hot = (_u.opt_row == _i);
        var _lab = "";
        var _val = "";
        switch (_rows[_i])
        {
            case "server": _lab = "SERVER"; _val = kfo_server_text(); break;
            case "vis": _lab = "STEAM ROOMS"; _val = kfo_vis_name(_o.vis); break;
            case "view": _lab = "SOUL SETTINGS"; _val = (_o.view.show ? "OTHERS SHOWN " : "OTHERS HIDDEN ") + string(_o.view.sop) + "%"; break;
            case "look": _lab = "SOUL APPEARANCE"; _val = kfo_col_name(_o.look.col); break;
            case "mview": _lab = "MATCH VIEW"; _val = "CAMERA " + kbr_cam_name(_o.view.cam); break;
            case "song": _lab = "MUSIC"; _val = kfo_song_name(_o.song) + (knight_preview_playing() ? "  (PLAYING)" : ""); break;
            case "keys": _lab = "KEYBINDS"; _val = kfo_key_label("breath") + " / " + kfo_key_label("use") + " / " + kfo_key_label("charge") + " / " + kfo_key_label("hold"); break;
            case "done": _lab = "DONE"; break;
        }
        draw_set_color(_hot ? c_yellow : c_white);
        knight_txt(xx + 100, _y, knight_fit(_lab, 195));
        if (_val != "")
        {
            draw_set_color(c_yellow);
            knight_txt(xx + 336, _y, knight_fit(_val, 236));
        }
        if (_hot)
            knight_heart(xx + 75, _y + 10);
    }
    // build 47: SOUL VISIBILITY / SOUL APPEARANCE have their own previews (the pages behind those rows)
}

function kfo_ui_draw_keys(xx, yy)
{
    // DRBR 1.0.1: in the menu's size - 10 rows at a time (the list scrolls with the heart), the key and the controller's button
    // beside each action
    var _u = global.knight_ui;
    draw_set_color(c_white);
    draw_rectangle(xx + 326, yy + 91, xx + 329, yy + 410, false);
    knight_caption_hub("KEYBINDS", xx + 112, yy + 84);
    var _rows = kfo_ui_keys_rows();
    var _n = array_length(_rows);
    var _shown = min(10, _n);
    var _first = clamp(_u.keys_row - (_shown - 1), 0, _n - _shown);
    draw_set_color(c_gray);
    knight_txt(xx + 342, yy + 90, "KEY");
    draw_set_halign(fa_right);
    knight_txt(xx + 572, yy + 90, "CONTROLLER");
    draw_set_halign(fa_left);
    for (var _i = _first; _i < _first + _shown; _i++)
    {
        var _id = _rows[_i];
        var _y = yy + 120 + ((_i - _first) * 28);
        var _hot = (_u.keys_row == _i);
        var _lab = "";
        switch (_id)
        {
            case "reset": _lab = "RESET KEYS"; break;
            case "done": _lab = "DONE"; break;
            default: _lab = kfo_key_title(_id); break;
        }
        draw_set_color(_hot ? c_yellow : c_white);
        knight_txt(xx + 100, _y, knight_fit(_lab, 220));
        if (_id != "reset" && _id != "done")
        {
            draw_set_color(_hot ? c_yellow : c_white);
            knight_txt(xx + 342, _y, knight_fit(kfo_key_label(_id), 130));
            draw_set_halign(fa_right);
            draw_set_color(c_gray);
            knight_txt(xx + 572, _y, knight_fit(kfo_key_pad_name(_id), 92));
            draw_set_halign(fa_left);
        }
        if (_hot)
            knight_heart(xx + 75, _y + 8);
    }
    knight_ui_arrows(xx + 84, yy + 116, yy + 120 + (_shown * 28) - 6, _first > 0, _first + _shown < _n, _u.siner);
}

function kfo_ui_draw_browse(xx, yy)
{
    // DRBR 1.0.1: in the menu's size (a room of another build: OLD or NEW)
    var _u = global.knight_ui;
    var _o = kfo_get();
    knight_caption_hub("ONLINE", xx + 112, yy + 84);
    var _l = _o.browse;
    draw_set_color(c_gray);
    knight_txt(xx + 100, yy + 96, "CODE");
    knight_txt(xx + 214, yy + 96, "HOST");
    draw_set_halign(fa_right);
    knight_txt(xx + 466, yy + 96, "PLAYERS");
    knight_txt(xx + 566, yy + 96, "STATE");
    draw_set_halign(fa_left);
    // (8 at a time: the list scrolls with the heart)
    var _first = clamp(_u.br_row - 7, 0, max(0, array_length(_l) - 8));
    knight_ui_arrows(xx + 84, yy + 124, yy + 128 + (8 * 30) - 6, _first > 0, _first + 8 < array_length(_l), _u.siner);
    for (var _i = _first; _i < array_length(_l) && _i < _first + 8; _i++)
    {
        var _e = _l[_i];
        var _y = yy + 128 + ((_i - _first) * 30);
        var _hot = (_u.br_row == _i);
        var _bad = (_e.ver != kfo_version()) || _e.np >= _e.mx;
        draw_set_color(_bad ? c_gray : (_hot ? c_yellow : c_white));
        knight_txt(xx + 100, _y, _e.code);
        knight_txt(xx + 214, _y, knight_fit(_e.host, 150));
        draw_set_halign(fa_right);
        knight_txt(xx + 466, _y, string(_e.np) + "/" + string(_e.mx));
        knight_txt(xx + 566, _y, (_e.ver != kfo_version()) ? ((_e.ver < kfo_version()) ? "OLD" : "NEW") : knight_fit(string_upper(_e.st), 90));
        draw_set_halign(fa_left);
        if (_hot)
            knight_heart(xx + 75, _y + 8);
    }
    draw_set_halign(fa_center);
    draw_set_color(c_ltgray);
    var _msg = _o.browse_st;
    if (_msg == "" && array_length(_l) == 0)
        _msg = "No public rooms right now. C: look again.";
    // (DRBR: above the frame's bottom edge - it used to be drawn over it)
    knight_para_fit(xx + 320, yy + 372, _msg, 500, 1);
    draw_set_halign(fa_left);
}

// DRBR 1.0.1: a player's status as the room's list shows it (5 letters at most - the names stay readable beside it)
function kfo_ui_pstatus_short(_t)
{
    switch (_t)
    {
        case "WATCHING": return "WATCH";
        case "WAITING": return "WAIT";
        case "REMATCH": return "VOTED";
    }
    if (string_copy(_t, 1, 5) == "OUT #")
        return "OUT " + string_delete(_t, 1, 5);
    return _t;
}

function kfo_ui_draw_lobby(xx, yy)
{
    var _u = global.knight_ui;
    var _o = kfo_get();
    var _pv = kfo_ui_pv();
    draw_set_color(c_white);
    draw_rectangle(xx + 300, yy + 91, xx + 305, yy + 410, false);
    knight_caption_hub("PLAYERS", xx + 112, yy + 84);
    knight_caption_center("ROOM", xx + 443, yy + 84);
    var _pl = kfo_lobby_players();
    var _hostid = is_struct(_o.lobby) ? kfo_jn(_o.lobby, "host", _o.hostid) : _o.hostid;
    var _match = kfo_lobby_matching();
    // build 47: each player's skin, SOUL color (the small SOUL), name, status (HOST / READY / VOTED / ALIVE / OUT / WATCH) and
    // ping; more than 8 (watch places) in shorter rows. DRBR 1.0.1: all in the menu's size - the status short, the ping a bar
    // (green / yellow / red) at the row's end
    var _many = (array_length(_pl) > 8);
    var _rh = _many ? 25 : 37;
    for (var _i = 0; _i < array_length(_pl) && _i < 12; _i++)
    {
        var _p = _pl[_i];
        var _y = yy + (_many ? 96 : 104) + (_i * _rh);
        var _pid = kfo_jn(_p, "pid", -2);
        if (!_many)
            kfo_skin_head_draw(kfo_skin_ok(kfo_jn(_p, "s", 1)), xx + 64, _y + 4);
        var _pc = kfo_col_ok(kfo_jn(_p, "cl", -1), kbr_pcol(_i));
        if (kfo_jn(_p, "bot", 0) == 1)
            _pc = kbr_pcol(_i);
        kfo_soul_draw(xx + (_many ? 66 : 88), _y + (_many ? 6 : 9), 0.625, _pc, 1, kfo_col_outline(_pc, 0));
        var _ps = kfo_ui_pstatus(_p, _hostid, _match);
        var _st = kfo_ui_pstatus_short(_ps[0]);
        scr_84_set_draw_font("mainbig");
        var _sw = string_width(_st);
        var _nx = xx + (_many ? 84 : 104);
        draw_set_color((_pid == _o.my) ? c_yellow : c_white);
        knight_txt(_nx, _y, knight_fit(kfo_js(_p, "n", "?"), (xx + 286 - _sw - 8) - _nx));
        draw_set_halign(fa_right);
        draw_set_color(_ps[1]);
        knight_txt(xx + 286, _y, _st);
        draw_set_halign(fa_left);
        var _lat = kfo_jn(_p, "lat", -1);
        if (kfo_jn(_p, "bot", 0) != 1 && _pid != _hostid && _lat >= 0)
        {
            draw_set_color((_lat < 100) ? c_lime : ((_lat < 200) ? c_yellow : c_red));
            draw_rectangle(xx + 291, _y + 6, xx + 293, _y + 20, false);
        }
    }
    if (array_length(_pl) == 0)
    {
        draw_set_color(c_gray);
        knight_para(xx + 80, yy + 110, "WAITING FOR THE HOST...", 210, 2);
    }
    // the room: code, my rows, the settings in short, what is going on
    var _cx = xx + 443;
    draw_set_halign(fa_center);
    draw_set_color(c_yellow);
    knight_txt(_cx, yy + 98, (_o.code == "PRACTICE") ? "PRACTICE" : ("CODE  " + _o.code));
    draw_set_halign(fa_left);
    kfo_net_light(xx + 582, yy + 112);
    var _rows = kfo_ui_lobby_rows();
    var _me = kfo_lobby_me();
    var _shown = kfo_ui_lobby_shown();
    var _sc = clamp(_u.lob_scroll, 0, max(0, array_length(_rows) - _shown));
    // DRBR: 28 px rows (the room's info and status below them used to run into the frame's bottom edge)
    var _rh2 = kfo_ui_lobby_rh();
    for (var _i = _sc; _i < array_length(_rows) && _i < _sc + _shown; _i++)
    {
        var _y = yy + 132 + ((_i - _sc) * _rh2);
        var _hot = (_u.lob_row == _i) && !_pv;
        var _t = "";
        switch (_rows[_i])
        {
            case "start": _t = "START"; break;
            case "ready": _t = (kfo_ui_after_match() ? "REMATCH: " : "READY: ") + ((!is_undefined(_me) && kfo_jn(_me, "rd", 0) == 1) ? "ON" : "OFF"); break;
            case "spectate": _t = "SPECTATE MATCH"; break;
            case "join": _t = "JOIN MATCH"; break;
            case "look": _t = "SOUL: " + kfo_col_name(_o.look.col); break;
            case "options": _t = "MORE OPTIONS"; break;
            case "copy": _t = "COPY CODE"; break;
            case "help": _t = "CONNECTION HELP"; break;
            case "skin": _t = "SKIN: " + string_upper(kfo_skin_name(_o.skin)); break;
            case "name": _t = "CHANGE NAME"; break;
            case "keys": _t = "KEYBINDS"; break;
            case "settings": _t = "SETTINGS"; break;
            case "bosses": _t = "BOSSES"; break;
            case "bots": _t = "BOTS: " + string(array_length(kfo_ui_bots_list())); break;
            case "invite": _t = "INVITE FRIENDS"; break;
            case "kick": _t = "REMOVE A PLAYER"; break;
            case "leave": _t = "LEAVE ROOM"; break;
        }
        var _dim = (_match && (_rows[_i] == "start" || _rows[_i] == "ready")) || (kfo_ui_lobby_why(_rows[_i]) != "");
        draw_set_color(_dim ? (_hot ? c_orange : c_gray) : (_hot ? c_yellow : c_white));
        // (the labels end before the scroll arrows at the right edge)
        knight_txt(xx + 345, _y, knight_fit(_t, (_rows[_i] == "look") ? 192 : 212));
        // your SOUL color beside its row
        if (_rows[_i] == "look")
            kfo_soul_draw(xx + 545, _y + 2, 1, _o.look.col, 1, kfo_col_outline(_o.look.col, 0));
        if (_hot)
            knight_heart(xx + 320, _y + 10);
    }
    // more rows above / below: the game's arrows at the rows' right end, inside the frame
    knight_ui_arrows(xx + 566, yy + 130, yy + 132 + (min(_shown, array_length(_rows)) * _rh2) - 6, _sc > 0, _sc + _shown < array_length(_rows), _u.siner);
    // the settings in short (the preset; its modifiers, else its summary), then what the room is doing
    var _s = kfo_lobby_set();
    var _ty = yy + 132 + (min(_shown, array_length(_rows)) * _rh2) + 2;
    draw_set_halign(fa_center);
    draw_set_color(c_yellow);
    knight_txt(_cx, _ty, knight_fit("PRESET: " + _s.pre, 262));
    var _mt = kfo_set_muts_text(_s);
    draw_set_color((_mt != "") ? c_orange : c_ltgray);
    knight_txt(_cx, _ty + 28, knight_fit((_mt != "") ? _mt : kfo_set_summary(_s), 262));
    draw_set_color(c_white);
    // the room's status under it: as many lines as fit above the frame's bottom edge (y 406)
    var _sy = _ty + 58;
    knight_para_fit(_cx, _sy, kfo_ui_lobby_status(), 262, clamp(floor(((yy + 406) - _sy) / 30), 1, 2));
    draw_set_halign(fa_left);
}

// DRBR: the room's rows, 28 px apart
function kfo_ui_lobby_rh()
{
    return 28;
}

// what the room is doing, in one or two lines
function kfo_ui_lobby_status()
{
    var _o = kfo_get();
    if (!is_struct(_o.lobby))
        return "JOINING...";
    var _M = _o.M;
    if (kfo_lobby_matching())
        return kfo_ui_match_line();
    var _res = kfo_jv(_o.lobby, "res");
    var _last = "";
    if (is_struct(_res))
    {
        var _wn = kfo_js(_res, "wn", "");
        if (_wn != "")
            _last = "LAST MATCH: " + string_upper(_wn) + " WON. ";
    }
    if (kfo_prac_room())
        return _last + "START WHEN YOU ARE.";
    var _pl = kfo_lobby_players();
    var _rd = 0;
    var _hum = 0;
    for (var _i = 0; _i < array_length(_pl); _i++)
    {
        if (kfo_jn(_pl[_i], "bot", 0) == 1)
            continue;
        _hum++;
        if (kfo_jn(_pl[_i], "rd", 0) == 1)
            _rd++;
    }
    if (_hum < 2)
        return _last + "SHARE THE CODE " + _o.code + " (OR INVITE). WALK AROUND THE COLD PLACE WHILE YOU WAIT.";
    // build 47: after a match READY is the rematch vote
    if (kfo_ui_after_match())
        return _last + "REMATCH: " + string(_rd) + " OF " + string(_hum - 1) + " VOTED" + ((_rd >= _hum - 1) ? " - THE HOST CAN START." : ".");
    return _last + string(_rd) + " OF " + string(_hum - 1) + " READY.";
}

// build 52: the settings page in the menu's own big font, like Deltarune's CONFIG: the pages on the left, the options on the
// right - the name, its value right-aligned, "< >" around the value of the picked one; 9 rows at a time; what the picked
// option does in the top bar (kfo_ui_desc)
function kfo_ui_draw_set(xx, yy)
{
    var _u = global.knight_ui;
    var _s = kfo_ui_set_cur();
    var _host = kfo_is_host();
    draw_set_color(c_white);
    draw_rectangle(xx + 228, yy + 91, xx + 233, yy + 410, false);
    knight_caption_hub("OPTIONS", xx + 72, yy + 84);
    knight_caption_center((_u.set_row == kfo_cat_pre()) ? "PRESETS" : "SETTINGS", xx + 410, yy + 84);
    var _cats = kfo_cats();
    for (var _i = 0; _i < array_length(_cats); _i++)
    {
        var _y = yy + 100 + (_i * 30);
        var _hot = (_u.set_row == _i);
        draw_set_color(_hot ? ((_u.set_focus == 0) ? c_yellow : c_orange) : c_white);
        // (DRBR: the names 16 px further right so the heart sits inside the frame - it used to cover its left edge)
        knight_txt_fit(xx + 84, _y, _cats[_i], 140);
        if (_hot && _u.set_focus == 0)
            knight_heart(xx + 66, _y + 9);
    }
    var _items = kfo_ui_set_items(_u.set_row);
    var _ni = array_length(_items);
    // DRBR 1.0.1: the preset line in the menu's size (only the host changes them: the top bar says so), 8 rows under it
    var _rows = 8;
    var _y0 = yy + 132;
    draw_set_halign(fa_center);
    draw_set_color((_u.set_row == kfo_cat_pre()) ? c_gray : kfo_preset_col_name(_s.pre));
    knight_txt(xx + 410, yy + 98, (_u.set_row == kfo_cat_pre()) ? "PICK ONE, PRESS Z" : knight_fit("PRESET: " + _s.pre, 320));
    draw_set_halign(fa_left);
    var _vx = xx + 558;
    for (var _i = _u.set_scroll; _i < _ni && _i < _u.set_scroll + _rows; _i++)
    {
        var _id = _items[_i];
        var _y = _y0 + ((_i - _u.set_scroll) * 31);
        var _hot = (_u.set_focus == 1 && _u.set_opt == _i);
        var _lab = kfo_ui_set_item_label(_id);
        var _val = "";
        var _arrows = false;
        if (_u.set_row == kfo_cat_pre())
        {
            if ((_id == "c1" || _id == "c2" || _id == "c3") && !kfo_custom_exists(real(string_digits(_id))))
                _val = "EMPTY";
            if (string_char_at(_id, 1) == "p" && string_length(_id) <= 3 && kfo_preset_name(real(string_digits(_id))) == _s.pre)
                _val = "IN USE";
        }
        else
        {
            var _e = kfo_opt_find(_id);
            if (!is_undefined(_e))
            {
                _val = kfo_opt_text(_e, _s);
                _arrows = (_e.kind == "num" || _e.kind == "enum" || _e.kind == "kw" || _e.kind == "open");
            }
        }
        // the value first (its width decides how much room the name gets)
        var _vw = 0;
        if (_val != "")
        {
            scr_84_set_draw_font("mainbig");
            var _vmax = 118;
            _vw = min(_vmax, string_width(_val));
            var _on = (_val != "OFF" && _val != "EMPTY" && _val != "NONE");
            var _vc = _on ? ((_val == "ON" || _val == "IN USE") ? make_color_rgb(120, 255, 140) : c_white) : c_gray;
            if (_hot && _host)
                _vc = c_yellow;
            draw_set_color(_vc);
            knight_txt_fit_r(_vx, _y, _val, _vmax);
            if (_hot && _arrows && _host)
            {
                var _bob = round(sin(current_time / 160) * 1.5);
                draw_set_color(c_yellow);
                knight_txt(_vx - _vw - 16 - _bob, _y, "<");
                knight_txt(_vx + 2 + _bob, _y, ">");
            }
        }
        // build 52: a preset in its own colour (the picked one yellow)
        var _lc = (_host || _u.set_row == kfo_cat_pre()) ? c_white : c_ltgray;
        if (_u.set_row == kfo_cat_pre() && string_char_at(_id, 1) == "p" && string_length(_id) <= 3)
            _lc = kfo_preset_col(real(string_digits(_id)));
        draw_set_color(_hot ? c_yellow : _lc);
        knight_txt_fit(xx + 262, _y, _lab, max(80, (_vx - (xx + 262)) - _vw - ((_hot && _arrows) ? 26 : 12)));
        if (_hot)
            knight_heart(xx + 240, _y + 9);
    }
    // more above / below
    draw_set_color(c_white);
    if (_u.set_scroll > 0)
        draw_sprite_ext(spr_morearrow, 0, xx + 560, yy + 128 - round(abs(sin(current_time / 200)) * 3), 1, -1, 0, c_white, 1);
    if (_u.set_scroll + _rows < _ni)
        draw_sprite_ext(spr_morearrow, 0, xx + 560, yy + 396 + round(abs(sin(current_time / 200)) * 3), 1, 1, 0, c_white, 1);
    // (DRBR: that only the host changes them is said in the line under the title - it used to sit on the box's frame here)
}

// build 52: the big menu font in _w at _x (left-aligned / centred / right-aligned). DRBR 1.0.1: a text too long for _w scrolls by
// itself (knight_fit) - it was squeezed sideways
function knight_txt_fit(_x, _y, _s, _w)
{
    draw_set_halign(fa_left);
    knight_txt(_x, _y, knight_fit(_s, _w));
}

// (it leaves the alignment centred, as where it is used)
function knight_txt_fit_c(_x, _y, _s, _w)
{
    draw_set_halign(fa_center);
    knight_txt(_x, _y, knight_fit(_s, _w));
}

function knight_txt_fit_r(_x, _y, _s, _w)
{
    draw_set_halign(fa_right);
    knight_txt(_x, _y, knight_fit(_s, _w));
    draw_set_halign(fa_left);
}

// the KNIGHT tab card for ONLINE
function kfo_ui_card(xx, yy)
{
    var _o = kfo_get();
    var _cx = xx + 443;
    draw_set_halign(fa_center);
    draw_set_color(c_yellow);
    // DRBR (it was KNIGHT FIGHTS ONLINE)
    knight_txt(_cx, yy + 110, "DRBR");
    knight_txt(_cx, yy + 140, "BATTLE ROYALE");
    draw_set_color(c_white);
    knight_txt(_cx, yy + 186, "2 TO 8 SOULS");
    knight_txt(_cx, yy + 216, "ONE SHARED BOSS");
    draw_set_color(c_gray);
    knight_txt(_cx, yy + 262, "DODGE, SEND ATTACKS,");
    knight_txt(_cx, yy + 292, "OUTLAST THEM ALL");
    if (kfo_in_room())
    {
        draw_set_color(c_lime);
        knight_txt(_cx, yy + 340, (_o.code == "PRACTICE") ? "IN PRACTICE" : ("IN ROOM " + _o.code));
    }
    draw_set_halign(fa_left);
}


// build 52: what each settings page is for (the top bar while the page list is picked)
function kfo_cat_desc(_c)
{
    switch (_c)
    {
        case 0: return "The main rules: players, HP, damage, bots.#Z: open.  X: back to the room.";
        case 1: return "Which bosses fight, and in what order.#Z: open.  X: back to the room.";
        case 2: return "How hard the match gets over time.#Z: open.  X: back to the room.";
        case 3: return "How skills work: price, slots, cooldown.#Z: open.  X: back to the room.";
        case 4: return "Turn single skills on or off.#Z: open.  X: back to the room.";
        case 5: return "Who your attack skills hit.#Z: open.  X: back to the room.";
        case 6: return "Fun twists on the rules. Mix and match!#Z: open.  X: back to the room.";
        case 7: return "Sudden death and the final two.#Z: open.  X: back to the room.";
        case 8: return "Fine-tuning most rooms never need.#Z: open.  X: back to the room.";
        case 9: return "Ready-made rule sets, and your own saves.#Z: open.  X: back to the room.";
    }
    return "";
}


// build 52: the skin being picked - its dialogue portrait (only when it has one: never a stand-in), its battle pose (the
// look's own battle art; the game's own heroes show their head), and what it is
function kfo_ui_skin_preview(_sk, _cx, _y)
{
    var _d = kfo_skin_def(_sk);
    var _hasp = !_d.own && variable_struct_exists(_d, "portrait") && kfo_skin_spr(_d.portrait) >= 0;
    var _bx = _hasp ? (_cx + 52) : _cx;
    if (_hasp)
        kfo_skin_portrait_draw(_sk, _cx - 60, _y + 34, 76, 60);
    if (!_d.own)
    {
        var _bs = kfo_skin_spr(_d.bt);
        if (_bs >= 0)
        {
            var _n = max(1, sprite_get_number(_bs));
            var _fr = floor((current_time / (1000 / 30)) * _d.bt_spd) mod _n;
            var _fx = _d.bt_flip ? -1 : 1;
            var _l = sprite_get_bbox_left(_bs);
            var _r = sprite_get_bbox_right(_bs) + 1;
            var _b = sprite_get_bbox_bottom(_bs) + 1;
            var _mid = ((_l + _r) / 2) - sprite_get_xoffset(_bs);
            // twice its size when it fits (whole-number scale: the battle draws it at 2x too)
            var _k = ((_r - _l) * 2 <= 120) ? 2 : 1;
            draw_sprite_ext(_bs, _fr, round(_bx - (_mid * _fx * _k)), round(_y + 66 - ((_b - sprite_get_yoffset(_bs)) * _k)), _fx * _k, _k, 0, c_white, 1);
        }
        else
        {
            draw_set_color(make_color_rgb(255, 150, 120));
            draw_set_halign(fa_center);
            knight_txt(_bx, _y + 30, "MISSING ART");
        }
    }
    draw_set_halign(fa_center);
    draw_set_color(_d.own ? c_gray : _d.col);
    knight_para_fit(_cx, _y + 72, _d.own ? "THE GAME'S OWN HERO" : "ONLINE LOOK: SAME HP AND SOUL", 262, 2);
    return 1;
}
