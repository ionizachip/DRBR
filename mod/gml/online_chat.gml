// ===== Build 48: the room's CHAT (lobby, the cold place, the match, watching) =====
// T or the CHAT key (build 49: \ by default, not ENTER) opens it anywhere in a room; the CHAT key sends, ESC closes, TAB makes it bigger, the mouse wheel
// scrolls. While you type, your keys go to the chat only: your SOUL holds still (as with QUICK SETTINGS), no skill, no
// breath, no give-up key, the cold place's Kris stands still and the hub's menu waits - the match itself never pauses.
// Network: a message is its own kind ("chat" up, "ch" down) on the reliable channel; the host checks it (the sender is
// the connection it came from, its name the host's own record of that player), limits its length and rate, gives it an id
// and sends it to everyone in the room (players, watchers, the ones in the lobby). The host keeps the last 30 and sends
// them to whoever joins. /mute NAME and /unmute NAME hide a player's messages on your screen only.

function kfo_chat_s()
{
    var _o = global.kfo;
    if (!variable_struct_exists(_o, "chat") || !is_struct(_o.chat))
        _o.chat = { l: [], ids: {}, typ: false, buf: "", t_new: 0, unread: 0, scroll: 0, exp: false, ilock: false, ilock_t: 0,
            mute: [], t_send: -100000, st: 0, open_st: -1, ln: 0 };
    return _o.chat;
}

function kfo_chat_typing()
{
    if (!variable_global_exists("kfo") || !is_struct(global.kfo) || !variable_struct_exists(global.kfo, "chat") || !is_struct(global.kfo.chat))
        return false;
    return global.kfo.chat.typ;
}

// the letters the game's fonts have (printable ASCII); anything else is left out
function kfo_chat_clean(_s)
{
    var _o = "";
    var _n = string_length(_s);
    for (var _i = 1; _i <= _n; _i++)
    {
        var _c = string_char_at(_s, _i);
        var _k = ord(_c);
        if (_k >= 32 && _k <= 126)
            _o += _c;
    }
    return _o;
}

function kfo_chat_trim(_s)
{
    while (string_length(_s) > 0 && string_char_at(_s, 1) == " ")
        _s = string_delete(_s, 1, 1);
    while (string_length(_s) > 0 && string_char_at(_s, string_length(_s)) == " ")
        _s = string_delete(_s, string_length(_s), 1);
    return _s;
}

function kfo_chat_max()
{
    return 80;
}

// ---------- the player's side ----------
function kfo_chat_can_open()
{
    if (!kfo_in_room() || kfo_view().chat == 0)
        return false;
    // a typing box of the hub's own menu (a room code, a name, a colour code) keeps its keys
    if (instance_exists(obj_knight_menu) && variable_global_exists("knight_ui") && is_struct(global.knight_ui) && is_struct(global.knight_ui.modal))
        return false;
    if (knight_active() || instance_exists(obj_knight_menu))
        return true;
    // the cold place: only while Kris is free (not talking, no menu of the game's open)
    return variable_global_exists("interact") && global.interact == 0;
}

function kfo_chat_open()
{
    var _c = kfo_chat_s();
    _c.typ = true;
    _c.buf = "";
    _c.scroll = 0;
    _c.unread = 0;
    _c.open_st = _c.st;
    keyboard_string = "";
    // the cold place: Kris stands still while you type (the game's own "busy" state), given back when the chat closes
    if (!knight_active() && !instance_exists(obj_knight_menu) && variable_global_exists("interact") && global.interact == 0)
    {
        global.interact = 1;
        _c.ilock = true;
        _c.ilock_t = 0;
    }
}

function kfo_chat_close()
{
    var _c = kfo_chat_s();
    _c.typ = false;
    _c.buf = "";
    keyboard_string = "";
    // the key that closed it is still down this step: Kris is free again a few steps later
    if (_c.ilock)
        _c.ilock_t = 4;
}

// every step (the hub controller, after the network)
function kfo_chat_tick()
{
    if (!variable_global_exists("kfo") || !is_struct(global.kfo))
        return 0;
    var _c = kfo_chat_s();
    _c.st++;
    if (_c.ilock_t > 0)
    {
        _c.ilock_t--;
        if (_c.ilock_t == 0 && _c.ilock)
        {
            if (variable_global_exists("interact") && global.interact == 1)
                global.interact = 0;
            _c.ilock = false;
        }
    }
    if (!kfo_in_room())
    {
        if (_c.typ)
            kfo_chat_close();
        return 0;
    }
    // another room: its own chat (a rejoin of the same room gets its recent messages again, once each)
    if (!variable_struct_exists(_c, "room") || _c.room != global.kfo.code)
    {
        _c.room = global.kfo.code;
        _c.l = [];
        _c.ids = {};
        _c.unread = 0;
    }
    if (!_c.typ)
    {
        // build 49: T, the CHAT key (\ unless changed in KEYBINDS), or ENTER in a match opens it (there is no mouse pointer in the game)
        var _open = keyboard_check_pressed(kfo_key("chat")) || keyboard_check_pressed(ord("T")) || (kbr_on() && keyboard_check_pressed(vk_enter) && !kfo_tut_on());
        if (_open && kfo_chat_can_open())
            kfo_chat_open();
        return 0;
    }
    // a fight began or the menu opened a typing box meanwhile: still typing (the chat keeps its keys)
    var _s = string_copy(kfo_chat_clean(keyboard_string), 1, kfo_chat_max());
    if (keyboard_string != _s)
        keyboard_string = _s;
    _c.buf = _s;
    if (keyboard_check_pressed(vk_tab))
        _c.exp = !_c.exp;
    if (mouse_wheel_up())
        _c.scroll = min(_c.scroll + 1, max(0, array_length(_c.l) - 1));
    if (mouse_wheel_down())
        _c.scroll = max(0, _c.scroll - 1);
    if (keyboard_check_pressed(vk_escape))
    {
        kfo_chat_close();
        return 1;
    }
    // build 49: ENTER or the CHAT key sends; the CHAT key's own character, typed into the box this step, is taken off again
    if ((keyboard_check_pressed(kfo_key("chat")) || keyboard_check_pressed(vk_enter)) && _c.st != _c.open_st)
    {
        var _kc = kfo_key_name(kfo_key("chat"));
        if (string_length(_kc) == 1 && string_length(_c.buf) > 0 && string_upper(string_char_at(_c.buf, string_length(_c.buf))) == _kc)
            _c.buf = string_copy(_c.buf, 1, string_length(_c.buf) - 1);
        var _t = kfo_chat_trim(_c.buf);
        kfo_chat_close();
        if (_t != "")
            kfo_chat_send(_t);
    }
    return 1;
}

// a line only this game shows (a refusal, a command's answer)
function kfo_chat_local(_t)
{
    var _c = kfo_chat_s();
    _c.ln++;
    kfo_chat_add({ ci: "local-" + string(_c.ln), pid: -1, n: "", t: _t, sys: 2 }, true);
}

function kfo_chat_send(_t)
{
    var _c = kfo_chat_s();
    _t = string_copy(kfo_chat_trim(kfo_chat_clean(_t)), 1, kfo_chat_max());
    if (_t == "")
        return false;
    // commands: on this screen only
    if (string_char_at(_t, 1) == "/")
    {
        var _sp = string_pos(" ", _t);
        var _cmd = string_lower((_sp > 0) ? string_copy(_t, 1, _sp - 1) : _t);
        var _arg = (_sp > 0) ? kfo_chat_trim(string_delete(_t, 1, _sp)) : "";
        switch (_cmd)
        {
            case "/mute":
                if (_arg == "")
                    kfo_chat_local("/mute NAME hides that player's messages (yours only).");
                else
                {
                    if (!kfo_chat_muted(_arg))
                        array_push(_c.mute, string_lower(_arg));
                    kfo_chat_local(_arg + " is muted (on your screen).");
                }
                return true;
            case "/unmute":
                for (var _i = array_length(_c.mute) - 1; _i >= 0; _i--)
                {
                    if (_c.mute[_i] == string_lower(_arg))
                        array_delete(_c.mute, _i, 1);
                }
                kfo_chat_local(_arg + " is not muted.");
                return true;
            case "/name":
                // build 52: a new name, at once, in the lobby or in a match (the host keeps you by your player number)
                if (_arg == "")
                    kfo_chat_local("/name NEW NAME changes the name everyone sees.");
                else
                    kfo_name_change(_arg);
                return true;
            default:
                kfo_chat_local("ENTER sends, ESC closes, TAB bigger, /name NEW NAME, /mute NAME, /unmute NAME.");
                return true;
        }
    }
    if (current_time - _c.t_send < 400)
    {
        kfo_chat_local("Not sent: wait a moment between messages.");
        return false;
    }
    _c.t_send = current_time;
    if (!kfo_up({ k: "chat", t: _t }))
    {
        kfo_chat_local("Not sent: not connected to the room.");
        return false;
    }
    return true;
}

// build 52: your name changed (the ONLINE page, the room's CHANGE NAME, /name): kept, and told to the room when you are in one
function kfo_name_change(_s)
{
    var _o = kfo_get();
    var _nm = kfo_clean_name(_s);
    if (_nm == "")
    {
        kfo_chat_local("A name needs at least one letter.");
        return false;
    }
    _o.name = _nm;
    kfo_ini_save();
    if (kfo_in_room())
        kfo_up({ k: "nm", name: _nm });
    return true;
}

function kfo_chat_muted(_n)
{
    var _c = kfo_chat_s();
    var _l = string_lower(_n);
    for (var _i = 0; _i < array_length(_c.mute); _i++)
    {
        if (_c.mute[_i] == _l)
            return true;
    }
    return false;
}

// a message from the host (or a local line): once per id, the list kept short
function kfo_chat_add(_e, _quiet)
{
    if (!is_struct(_e))
        return false;
    var _c = kfo_chat_s();
    var _id = kfo_js(_e, "ci", "");
    if (_id == "" || variable_struct_exists(_c.ids, _id))
        return false;
    var _t = string_copy(kfo_chat_clean(kfo_js(_e, "t", "")), 1, 120);
    if (_t == "")
        return false;
    variable_struct_set(_c.ids, _id, 1);
    var _n = string_copy(kfo_chat_clean(kfo_js(_e, "n", "")), 1, 16);
    array_push(_c.l, { ci: _id, pid: kfo_jn(_e, "pid", -1), n: _n, t: _t, sys: kfo_jn(_e, "sys", 0), tm: current_time, cl: kfo_jn(_e, "cl", -1) });
    while (array_length(_c.l) > 60)
    {
        variable_struct_remove(_c.ids, _c.l[0].ci);
        array_delete(_c.l, 0, 1);
    }
    if (!_quiet && !_c.typ && !(kfo_jn(_e, "sys", 0) == 0 && kfo_chat_muted(_n)))
        _c.unread++;
    _c.t_new = current_time;
    return true;
}

// the host's messages: "ch" one message, "chh" the room's recent ones (on joining), "chx" yours was refused
function kfo_chat_on(_m)
{
    switch (kfo_js(_m, "k", ""))
    {
        case "ch":
            kfo_chat_add(kfo_jv(_m, "e"), false);
            break;
        case "chh":
            var _l = kfo_ja(_m, "l");
            for (var _i = 0; _i < array_length(_l) && _i < 30; _i++)
                kfo_chat_add(_l[_i], true);
            break;
        case "chx":
            kfo_chat_local("Not sent: " + string_copy(kfo_chat_clean(kfo_js(_m, "why", "refused")), 1, 60));
            break;
    }
    return 1;
}

// ---------- the host ----------
function kfo_host_chat_init(_h)
{
    _h.chat = [];
    _h.chat_n = 0;
    _h.chat_rate = {};
    // a new host (the old one left): the room's recent messages are the ones this game has
    if (is_struct(global.kfo) && variable_struct_exists(global.kfo, "chat") && is_struct(global.kfo.chat))
    {
        var _l = global.kfo.chat.l;
        for (var _i = max(0, array_length(_l) - 30); _i < array_length(_l); _i++)
        {
            if (_l[_i].sys != 2)
                array_push(_h.chat, { ci: _l[_i].ci, pid: _l[_i].pid, n: _l[_i].n, t: _l[_i].t, sys: _l[_i].sys, cl: _l[_i].cl });
        }
    }
    return _h;
}

// a message for the room (_sys 0 a player's, 1 the room's own notice)
function kfo_host_chat_add(_pid, _n, _t, _sys, _cl)
{
    var _h = global.kfo.H;
    if (!is_struct(_h))
        return 0;
    if (!variable_struct_exists(_h, "chat"))
        kfo_host_chat_init(_h);
    _h.chat_n++;
    var _e = { ci: string(global.kfo.my) + "-" + string(_h.chat_n), pid: _pid, n: _n, t: _t, sys: _sys, cl: _cl };
    array_push(_h.chat, _e);
    while (array_length(_h.chat) > 30)
        array_delete(_h.chat, 0, 1);
    kfo_down(0, { k: "ch", e: _e });
    return 1;
}

function kfo_host_chat_sys(_t)
{
    return kfo_host_chat_add(0, "", _t, 1, -1);
}

// a player's message: checked here, never trusted as sent (who sent it is the connection, the name the host's)
function kfo_host_chat(_p, _m)
{
    var _h = global.kfo.H;
    if (_p.bot)
        return 0;
    if (!variable_struct_exists(_h, "chat"))
        kfo_host_chat_init(_h);
    var _t = string_copy(kfo_chat_trim(kfo_chat_clean(kfo_js(_m, "t", ""))), 1, kfo_chat_max());
    if (_t == "")
        return 0;
    var _k = string(_p.pid);
    if (!variable_struct_exists(_h.chat_rate, _k))
        variable_struct_set(_h.chat_rate, _k, { ts: [], last: "", last_t: -100000 });
    var _r = variable_struct_get(_h.chat_rate, _k);
    var _now = current_time;
    // the last 5 seconds
    for (var _i = array_length(_r.ts) - 1; _i >= 0; _i--)
    {
        if (_now - _r.ts[_i] > 5000)
            array_delete(_r.ts, _i, 1);
    }
    var _why = "";
    if (array_length(_r.ts) >= 5)
        _why = "too many messages (5 in 5 seconds).";
    else if (_t == _r.last && _now - _r.last_t < 4000)
        _why = "the same message again.";
    if (_why != "")
    {
        if (_p.pid == global.kfo.my)
            kfo_chat_local("Not sent: " + _why);
        else
            kfo_down(_p.pid, { k: "chx", why: _why });
        return 0;
    }
    array_push(_r.ts, _now);
    _r.last = _t;
    _r.last_t = _now;
    return kfo_host_chat_add(_p.pid, _p.n, _t, 0, _p.cl);
}

// someone joined: the recent messages for them, and a notice for everyone
function kfo_host_chat_joined(_p)
{
    var _h = global.kfo.H;
    if (!variable_struct_exists(_h, "chat"))
        kfo_host_chat_init(_h);
    if (_p.pid != global.kfo.my)
        kfo_down(_p.pid, { k: "chh", l: _h.chat });
    if (!_p.bot && _p.pid != global.kfo.my)
        kfo_host_chat_sys(_p.n + " joined the room.");
    return 1;
}

// ---------- drawing ----------
// the lines of the newest messages that fit (word-wrapped to _w in fnt_small), newest at the bottom; _all: also the old ones
function kfo_chat_lines(_c, _w, _max, _all)
{
    var _out = [];
    var _end = array_length(_c.l) - 1 - (_c.typ ? _c.scroll : 0);
    for (var _i = _end; _i >= 0 && array_length(_out) < _max; _i--)
    {
        var _e = _c.l[_i];
        if (_e.sys == 0 && kfo_chat_muted(_e.n))
            continue;
        var _age = current_time - _e.tm;
        if (!_all && _age > 10000)
            break;
        var _a = _all ? 1 : clamp((10000 - _age) / 1000, 0, 1);
        var _head = (_e.sys == 0) ? (_e.n + ": ") : "";
        var _col = (_e.sys == 0) ? c_white : ((_e.sys == 2) ? make_color_rgb(255, 120, 120) : c_ltgray);
        var _hc = (_e.sys == 0) ? kfo_col_text(kfo_col_ok(_e.cl, c_yellow)) : _col;
        // word-wrap
        var _words = kfo_chat_words(_e.t);
        var _rows = [];
        var _cur = _head;
        var _first = true;
        for (var _k = 0; _k < array_length(_words); _k++)
        {
            var _wd = _words[_k];
            var _try = (_cur == "" || (_first && _cur == _head)) ? (_cur + _wd) : (_cur + " " + _wd);
            if (string_width(_try) > _w && _cur != "" && !(_first && _cur == _head))
            {
                array_push(_rows, _cur);
                _cur = "  " + _wd;
                _first = false;
            }
            else
                _cur = _try;
            // a word longer than the line: cut it
            while (string_width(_cur) > _w && string_length(_cur) > 3)
            {
                var _cut = string_length(_cur);
                while (_cut > 1 && string_width(string_copy(_cur, 1, _cut)) > _w)
                    _cut--;
                array_push(_rows, string_copy(_cur, 1, _cut));
                _cur = "  " + string_delete(_cur, 1, _cut);
                _first = false;
            }
        }
        array_push(_rows, _cur);
        for (var _k = array_length(_rows) - 1; _k >= 0 && array_length(_out) < _max; _k--)
            array_insert(_out, 0, { t: _rows[_k], c: _col, h: (_k == 0) ? string_length(_head) : 0, hc: _hc, a: _a });
    }
    return _out;
}

function kfo_chat_words(_s)
{
    var _out = [];
    var _cur = "";
    for (var _i = 1; _i <= string_length(_s); _i++)
    {
        var _ch = string_char_at(_s, _i);
        if (_ch == " ")
        {
            if (_cur != "")
                array_push(_out, _cur);
            _cur = "";
        }
        else
            _cur += _ch;
    }
    if (_cur != "")
        array_push(_out, _cur);
    return _out;
}

// _x0, _yb: the panel's left and bottom; _w its width; _n the lines it shows while you type (twice with TAB)
function kfo_chat_panel(_x0, _yb, _w, _n)
{
    var _c = kfo_chat_s();
    if (kfo_view().chat == 0 || !kfo_in_room())
        return 0;
    draw_set_font(fnt_small);
    draw_set_halign(fa_left);
    var _lh = 12;
    if (_c.typ)
    {
        var _nn = _c.exp ? (_n * 2) : _n;
        var _lines = kfo_chat_lines(_c, _w - 12, _nn, true);
        var _h = ((_nn + 2) * _lh) + 8;
        var _y0 = _yb - _h;
        draw_set_alpha(0.75);
        draw_set_color(c_black);
        draw_rectangle(_x0, _y0, _x0 + _w, _yb, false);
        draw_set_alpha(1);
        draw_set_color(c_white);
        draw_rectangle(_x0, _y0, _x0 + _w, _yb, true);
        kbr_hud_text(_x0 + 6, _y0 + 4, "CHAT" + ((_c.scroll > 0) ? ("  (" + string(_c.scroll) + " UP)") : "") + "   ENTER SEND  ESC CLOSE", c_yellow);
        var _y = _y0 + 4 + _lh + ((_nn - array_length(_lines)) * _lh);
        for (var _i = 0; _i < array_length(_lines); _i++)
        {
            kfo_chat_line(_x0 + 6, _y, _lines[_i], 1);
            _y += _lh;
        }
        // the line being typed (its end when it is longer than the box), a blinking cursor
        var _in = "> " + _c.buf;
        while (string_width(_in + "_") > _w - 12 && string_length(_in) > 3)
            _in = "> " + string_delete(_in, 1, 3);
        kbr_hud_text(_x0 + 6, _yb - _lh - 4, _in + (((current_time div 400) mod 2 == 0) ? "_" : ""), c_white);
        return 1;
    }
    // not typing: the last messages for 10 seconds, fading; then a small tag when there is something unread
    var _lines = kfo_chat_lines(_c, _w - 12, 4, false);
    var _y = _yb - (array_length(_lines) * _lh) - 2;
    for (var _i = 0; _i < array_length(_lines); _i++)
    {
        kfo_chat_line(_x0 + 6, _y, _lines[_i], _lines[_i].a);
        _y += _lh;
    }
    if (array_length(_lines) == 0 && _c.unread > 0)
        kbr_hud_text(_x0 + 6, _yb - _lh - 2, "CHAT (" + string(_c.unread) + " NEW)  T / ENTER", c_yellow);
    draw_set_alpha(1);
    return 1;
}


function kfo_chat_line(_x, _y, _l, _a)
{
    draw_set_alpha(_a);
    if (_l.h > 0)
    {
        var _head = string_copy(_l.t, 1, _l.h);
        kbr_hud_text(_x, _y, _head, _l.hc);
        kbr_hud_text(_x + string_width(_head), _y, string_delete(_l.t, 1, _l.h), _l.c);
    }
    else
        kbr_hud_text(_x, _y, _l.t, _l.c);
    draw_set_alpha(1);
}

// in a match: left of the box, above the party's panel (clear of the box, the log and the HP list)
function kfo_chat_draw_match(xx, yy)
{
    // build 51: never over the box (a wide box moves the right edge in) and always above the targeting row (y 324 < 373)
    // build 51: bottom right, over the targeting strip (the feed is bottom left)
    var _x0 = xx + 420;
    with (obj_growtangle)
    {
        if (bbox_right - xx + 6 > _x0 - xx)
            _x0 = min(xx + 470, bbox_right + 6);
    }
    return kfo_chat_panel(_x0, yy + 404, (xx + 626) - _x0, 6);
}

// the cold place (no menu): bottom left
function kfo_chat_draw_world()
{
    if (knight_active() || instance_exists(obj_knight_menu) || !kfo_in_room())
        return 0;
    return kfo_chat_panel(knight_cam_x() + 6, knight_cam_y() + 472, 300, 8);
}

// over the hub's menu (the room's page is the lobby): bottom left, over the menu
function kfo_chat_draw_menu()
{
    if (knight_active() || !kfo_in_room())
        return 0;
    return kfo_chat_panel(knight_cam_x() + 6, knight_cam_y() + 474, 320, 8);
}
