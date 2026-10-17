// ===== Build 49: STEAM INVITES in the game - your Steam friends in a DELTARUNE-style list, a Steam invite with Z =====
// The room page's INVITE FRIENDS (Steam rooms) opens the INVITE page: your friends (playing Knight Fights / Spacewar first,
// then online, away, offline), Z sends one a Steam invite to this room (kf_invite_user: Steam's InviteUserToLobby - it also
// lets them into a PRIVATE room). A friend whose game is open gets an invite box (JOIN / NOT NOW) when the sign's menu is
// open, and a line on screen otherwise; Steam's own notification works as before (its JOIN comes in as join_request).
// Needs kf_steam.dll from build 49 (an older DLL: the page offers only the Steam overlay's invite list).

// the DLL's build 49 functions: loaded on their own (an older kf_steam.dll keeps every build 45 function working)
function kfo_steam_opt_list()
{
    return [["kf_friends_refresh", 0, []], ["kf_friend_info", 1, [0]], ["kf_invite_user", 0, [0]]];
}

function kfo_steam_opt_load(_s, _path)
{
    var _l = kfo_steam_opt_list();
    for (var _i = 0; _i < array_length(_l); _i++)
    {
        var _e = _l[_i];
        var _id = -1;
        try
        {
            if (array_length(_e[2]) == 0)
                _id = external_define(_path, _e[0], dll_cdecl, _e[1] ? ty_string : ty_real, 0);
            else
                _id = external_define(_path, _e[0], dll_cdecl, _e[1] ? ty_string : ty_real, 1, _e[2][0] ? ty_string : ty_real);
        }
        catch (_err)
        {
            _id = -1;
        }
        if (is_real(_id) && _id >= 0)
            variable_struct_set(_s.fns, _e[0], _id);
    }
    return 1;
}

function kfo_friends_ok()
{
    var _s = global.kfo_stm;
    return is_struct(_s) && _s.ok && variable_struct_exists(_s.fns, "kf_friends_refresh") && variable_struct_exists(_s.fns, "kf_invite_user");
}

// the friends list from Steam (at most every 4 seconds unless _now)
function kfo_friends_refresh(_now)
{
    var _o = kfo_get();
    if (!variable_struct_exists(_o, "fr"))
    {
        _o.fr = [];
        _o.fr_t = -100000;
        _o.inv_sent = {};
    }
    if (!kfo_friends_ok())
        return _o.fr;
    if (!_now && current_time - _o.fr_t < 4000)
        return _o.fr;
    _o.fr_t = current_time;
    var _n = kfo_sx("kf_friends_refresh");
    var _l = [];
    for (var _i = 0; _i < _n && _i < 200; _i++)
    {
        var _f = kfo_split(kfo_sx("kf_friend_info", _i), "|");
        if (array_length(_f) < 4)
            continue;
        var _nm = kfo_clean_name(_f[3]);
        if (_nm == "" || _nm == " ")
            _nm = "FRIEND " + string(_i + 1);
        array_push(_l, { acct: kfo_num(_f[0], 0), st: kfo_num(_f[1], 0), g: kfo_num(_f[2], 0), n: _nm });
    }
    _o.fr = _l;
    return _l;
}

function kfo_friend_state(_f)
{
    if (_f.st != 0 && _f.g)
        return "IN GAME";
    switch (_f.st)
    {
        case 0: return "OFFLINE";
        case 1: return "ONLINE";
        case 2: return "BUSY";
        case 3: return "AWAY";
        case 4: return "SNOOZE";
    }
    return "ONLINE";
}

// ---------- the INVITE page (the hub's page system: kfo_ui_pg_*) ----------
function kfo_ui_inv_open(_from)
{
    kfo_friends_refresh(true);
    kfo_ui_pg_open("onl_inv", _from);
}

function kfo_ui_inv_rows()
{
    var _r = [];
    var _l = kfo_friends_refresh(false);
    for (var _i = 0; _i < array_length(_l); _i++)
        array_push(_r, "f" + string(_i));
    array_push(_r, "refresh", "ovl", "done");
    return _r;
}

function kfo_ui_inv_friend(_id)
{
    var _o = kfo_get();
    if (string_char_at(_id, 1) != "f" || !variable_struct_exists(_o, "fr"))
        return undefined;
    var _i = real(string_digits(_id));
    return (_i < array_length(_o.fr)) ? _o.fr[_i] : undefined;
}

function kfo_ui_inv_sent_ago(_f)
{
    var _o = kfo_get();
    var _k = string(_f.acct);
    return variable_struct_exists(_o.inv_sent, _k) ? (current_time - variable_struct_get(_o.inv_sent, _k)) : -1;
}

function kfo_ui_inv_label(_id)
{
    switch (_id)
    {
        case "refresh": return ["REFRESH", ""];
        case "ovl": return ["STEAM OVERLAY", ""];
        case "done": return ["DONE", ""];
    }
    var _f = kfo_ui_inv_friend(_id);
    if (is_undefined(_f))
        return ["?", ""];
    var _ago = kfo_ui_inv_sent_ago(_f);
    return [_f.n, (_ago >= 0 && _ago < 60000) ? "INVITED" : kfo_friend_state(_f)];
}

function kfo_ui_inv_desc(_id)
{
    switch (_id)
    {
        case "refresh": return "Z: read your Steam friends list again.";
        case "ovl": return "Z: Steam's own invite list (the Steam overlay,#Shift+Tab).";
        case "done": return "Z: back.";
    }
    var _f = kfo_ui_inv_friend(_id);
    if (is_undefined(_f))
        return "";
    return "Z: send " + _f.n + " a Steam invite to this#room" + ((_f.st == 0) ? " (offline: they see it later)." : ".");
}

function kfo_ui_inv_change(_id, _ok)
{
    if (!_ok)
        return false;
    var _o = kfo_get();
    switch (_id)
    {
        case "refresh":
            kfo_friends_refresh(true);
            knight_ui_tell("Friends list read again (" + string(array_length(_o.fr)) + ").");
            return true;
        case "ovl":
            if (!kfo_steam_invite())
                knight_ui_warn("The Steam overlay is off: send your friends the code " + _o.code + ".");
            return false;
    }
    var _f = kfo_ui_inv_friend(_id);
    if (is_undefined(_f))
        return false;
    if (!kfo_in_room() || _o.mode != "steam")
    {
        knight_ui_warn("Invites are for Steam rooms (relay rooms: give them the code).");
        return false;
    }
    var _ago = kfo_ui_inv_sent_ago(_f);
    if (_ago >= 0 && _ago < 3000)
        return false;
    if (kfo_sx("kf_invite_user", _f.acct) == 1)
    {
        variable_struct_set(_o.inv_sent, string(_f.acct), current_time);
        knight_ui_tell("Steam invite sent to " + _f.n + ".");
        return true;
    }
    knight_ui_warn("Steam did not send the invite (try STEAM OVERLAY).");
    return false;
}

// the right side: the friend, what an invite does, the room's code
function kfo_ui_prev_inv(xx, yy)
{
    var _u = global.knight_ui;
    var _o = kfo_get();
    var _bx = xx + 330;
    var _by = yy + 104;
    draw_set_color(c_black);
    draw_rectangle(_bx, _by, _bx + 236, _by + 200, false);
    var _rows = kfo_ui_inv_rows();
    var _id = _rows[clamp(_u.pg_row, 0, array_length(_rows) - 1)];
    var _f = kfo_ui_inv_friend(_id);
    draw_set_color(c_white);
    if (!kfo_friends_ok())
    {
        knight_txt_small(_bx + 8, _by + 6, "THE FRIENDS LIST NEEDS BUILD 49'S");
        knight_txt_small(_bx + 8, _by + 22, kdr_on() ? "KF_STEAM.DLL (DRBR LAUNCHER > REPAIR)." : "KF_STEAM.DLL (RUN PLAY_KNIGHT_HUB.BAT).");
        draw_set_color(c_ltgray);
        knight_txt_small(_bx + 8, _by + 46, "STEAM OVERLAY STILL WORKS.");
    }
    else if (is_struct(_f))
    {
        draw_set_color(c_yellow);
        knight_txt_small(_bx + 8, _by + 6, knight_fit_small(_f.n, 220));
        var _st = kfo_friend_state(_f);
        draw_set_color((_st == "IN GAME") ? c_lime : ((_st == "OFFLINE") ? c_gray : c_white));
        knight_txt_small(_bx + 8, _by + 24, _st);
        var _ago = kfo_ui_inv_sent_ago(_f);
        if (_ago >= 0)
        {
            draw_set_color(c_aqua);
            knight_txt_small(_bx + 8, _by + 42, "INVITED " + string(floor(_ago / 1000)) + " S AGO");
        }
    }
    else
    {
        draw_set_color(c_white);
        knight_txt_small(_bx + 8, _by + 6, string(array_length(_o.fr)) + " FRIENDS");
    }
    draw_set_color(c_ltgray);
    var _t = ["Z SENDS A STEAM INVITE. THEY GET", "STEAM'S NOTIFICATION; WITH DRBR", "OPEN, AN INVITE BOX TOO.", "IT ALSO LETS THEM INTO A PRIVATE", "ROOM.", "", "ROOM CODE: " + _o.code];
    for (var _i = 0; _i < array_length(_t); _i++)
        knight_txt_small(_bx + 8, _by + 70 + (_i * 16), _t[_i]);
    draw_set_color(c_white);
    return 1;
}

// ---------- an invite that came in ("invited:<lobby>|<acct>") ----------
function kfo_inv_in(_v)
{
    var _o = kfo_get();
    var _f = kfo_split(_v, "|");
    if (array_length(_f) < 2)
        return 0;
    // already in that room: nothing to do
    if (kfo_in_room() && _o.mode == "steam" && kfo_sx("kf_lobby_id") == _f[0])
        return 0;
    var _nm = kfo_clean_name(kfo_sx("kf_name", kfo_num(_f[1], 0)));
    if (_nm == "" || _nm == " ")
        _nm = "A friend";
    _o.inv_in = { lobby: _f[0], n: _nm, t: current_time, shown: false };
    snd_play(snd_b);
    if (kfo_in_room())
        kfo_chat_local("* " + _nm + " invited you to their room. Open the sign's menu to join.");
    return 1;
}

// the sign's menu is open (no other box): the invite box
function kfo_inv_modal_check()
{
    if (!variable_global_exists("kfo") || !is_struct(global.kfo) || !variable_struct_exists(global.kfo, "inv_in") || !is_struct(global.kfo.inv_in))
        return 0;
    var _iv = global.kfo.inv_in;
    if (current_time - _iv.t > 120000)
    {
        global.kfo.inv_in = undefined;
        return 0;
    }
    if (_iv.shown)
        return 0;
    _iv.shown = true;
    if (variable_struct_exists(_iv, "back") && _iv.back)
        knight_ui_modal("kfo_invite", "DRBR IS UPDATED", ["Join the room you tried to join", "before the update? (" + knight_fit(_iv.n, 300) + ")"],
            [{ t: "Join", a: "kfo_inv_join" }, { t: "Not now", a: "kfo_inv_no" }]);
    else
        knight_ui_modal("kfo_invite", "STEAM INVITE", [knight_fit(_iv.n, 420) + " invited you to their", "DRBR room." + (kfo_in_room() ? " (You leave this one.)" : "")],
            [{ t: "Join", a: "kfo_inv_join" }, { t: "Not now", a: "kfo_inv_no" }]);
    snd_play(snd_select);
    return 1;
}

function kfo_inv_join()
{
    var _o = kfo_get();
    var _iv = _o.inv_in;
    _o.inv_in = undefined;
    if (!is_struct(_iv))
        return 0;
    if (kfo_in_room())
        kfo_leave();
    var _u = global.knight_ui;
    _u.sub = "online";
    _u.onl_row = 0;
    kfo_steam_join_checked(_iv.lobby);
    return 1;
}

// outside the menu: a line at the top of the screen for 8 seconds
function kfo_inv_draw()
{
    if (!variable_global_exists("kfo") || !is_struct(global.kfo) || !variable_struct_exists(global.kfo, "inv_in") || !is_struct(global.kfo.inv_in))
        return 0;
    var _iv = global.kfo.inv_in;
    if (_iv.shown || current_time - _iv.t > 8000 || instance_exists(obj_knight_menu))
        return 0;
    var xx = camera_get_view_x(view_camera[0]);
    var yy = camera_get_view_y(view_camera[0]);
    var _t = (variable_struct_exists(_iv, "back") && _iv.back) ? "* DRBR IS UPDATED - OPEN THE SIGN TO REJOIN THAT ROOM" : ("* " + _iv.n + " INVITED YOU - OPEN THE SIGN TO JOIN");
    draw_set_font(fnt_small);
    var _w = min(600, string_width(_t) + 16);
    draw_set_alpha(1);
    draw_set_color(c_black);
    draw_rectangle(xx + 320 - (_w / 2), yy + 4, xx + 320 + (_w / 2), yy + 20, false);
    draw_set_color(c_white);
    draw_rectangle(xx + 320 - (_w / 2), yy + 4, xx + 320 + (_w / 2), yy + 20, true);
    draw_set_halign(fa_center);
    draw_set_color(c_yellow);
    draw_text(xx + 320, yy + 7, knight_fit_small(_t, _w - 12));
    draw_set_halign(fa_left);
    draw_set_color(c_white);
    return 1;
}
