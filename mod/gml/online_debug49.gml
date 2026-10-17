// ===== Build 49: the build stamp, the DEBUG OVERLAY (F3) and its log =====
// knight_build_stamp(): the mod's name, build number and build time - on the sign's menu (bottom right of every page), on the
// ONLINE page and on the overlay. F3 (in the cold place, the menus or a match; not one of Z X C V S D Q E A 1-8) turns the
// DEBUG OVERLAY on / off: the stamp, the room and camera, your SOUL, every other SOUL the match knows about and every bot the
// host runs (x, y in the room and relative to the camera, depth, drawn or not and why, alpha), with a plain coloured square
// drawn at each other SOUL's position whatever SOUL settings say. While it is on, the same lines go to knightfights_debug.log
// (once a second) in the game's save folder (%LOCALAPPDATA%\DELTARUNE - GameMaker only lets a game write there).

function knight_build_stamp()
{
    return (kdr_on() ? "DRBR - BUILD " : "KNIGHT HUB V2 - BUILD ") + string(kfo_version()) + " - @@BUILDTIME@@";
}

function kh_dbg_file()
{
    return "knightfights_debug.log";
}

function kh_dbg()
{
    if (!variable_global_exists("kh_dbg_s") || !is_struct(global.kh_dbg_s))
        global.kh_dbg_s = { on: false, t: 0, lines: 0, started: false };
    return global.kh_dbg_s;
}

function kh_dbg_on()
{
    return kh_dbg().on;
}

// the controller's Step: F3, and the log once a second while the overlay is on
function kh_dbg_tick()
{
    var _d = kh_dbg();
    if (keyboard_check_pressed(vk_f3))
    {
        _d.on = !_d.on;
        _d.t = 0;
        kh_dbg_write([_d.on ? "DEBUG OVERLAY ON (F3)" : "DEBUG OVERLAY OFF (F3)"]);
    }
    if (!_d.on)
        return 0;
    _d.t--;
    if (_d.t <= 0)
    {
        _d.t = 30;
        kh_dbg_write(kh_dbg_lines());
    }
    return 1;
}

// lines to the log (a new file once it passes 20000 lines, so it never grows without end)
function kh_dbg_write(_l)
{
    var _d = kh_dbg();
    var _f = -1;
    if (!_d.started || _d.lines > 20000)
    {
        _f = file_text_open_write(kh_dbg_file());
        _d.lines = 0;
        _d.started = true;
        file_text_write_string(_f, "===== " + knight_build_stamp() + " - log started " + date_datetime_string(date_current_datetime()) + " =====");
        file_text_writeln(_f);
    }
    else
        _f = file_text_open_append(kh_dbg_file());
    if (_f < 0)
        return 0;
    file_text_write_string(_f, "--- frame " + string(kh_dbg_frame()) + " ---");
    file_text_writeln(_f);
    for (var _i = 0; _i < array_length(_l); _i++)
    {
        file_text_write_string(_f, _l[_i]);
        file_text_writeln(_f);
    }
    file_text_close(_f);
    _d.lines += array_length(_l) + 1;
    return 1;
}

function kh_dbg_frame()
{
    var _d = kh_dbg();
    if (!variable_struct_exists(_d, "fr"))
        _d.fr = 0;
    return _d.fr;
}

function kh_dbg_n(_v)
{
    return string(round(_v * 10) / 10);
}

// why another SOUL is (not) drawn this frame - the same tests as kbr_draw_souls
function kh_dbg_why(_M, _p, _q)
{
    var _V = kfo_view();
    if (kfo_jn(_p, "al", 0) != 1)
        return "OUT";
    if (!is_struct(_q))
        return "NO POSITION YET";
    if (current_time - _q.t > 1500)
        return "POSITION OLD (" + string(current_time - _q.t) + " MS)";
    var _spec = (_M.out || !_M.me);
    if (!_spec && !_V.show)
        return "HIDDEN: SHOW OTHER SOULS OFF (V)";
    return "DRAWN";
}

// everything the overlay shows, as lines
function kh_dbg_lines()
{
    var _l = [];
    array_push(_l, knight_build_stamp());
    var _cx = camera_get_view_x(view_camera[0]);
    var _cy = camera_get_view_y(view_camera[0]);
    array_push(_l, "ROOM " + room_get_name(room) + " (" + string(room) + ")  CAMERA " + kh_dbg_n(_cx) + ", " + kh_dbg_n(_cy) + "  VIEW "
        + string(camera_get_view_width(view_camera[0])) + "x" + string(camera_get_view_height(view_camera[0])) + "  BATTLE ORIGIN " + kh_dbg_n(kbr_ox()) + ", " + kh_dbg_n(kbr_oy()));
    array_push(_l, "WINDOW " + string(window_get_width()) + "x" + string(window_get_height()) + "  FULLSCREEN " + string(window_get_fullscreen()));
    var _cd = "none";
    with (obj_knight_ctrl)
        _cd = "depth " + string(depth) + " visible " + string(visible);
    array_push(_l, "HUB CONTROLLER (draws the other SOULs): " + _cd);
    var _V = kfo_view();
    array_push(_l, "SOUL SETTINGS: SHOW OTHER SOULS " + string(_V.show) + "  OPACITY " + string(_V.sop) + "%  NAMES " + string(_V.names) + "  WHILE WATCHING " + string(_V.spv));
    var _o = global.kfo;
    if (!is_struct(_o))
    {
        array_push(_l, "ONLINE: not started");
        return _l;
    }
    array_push(_l, "ONLINE: mode " + string(_o.mode) + "  in room " + string(kfo_in_room()) + "  host " + string(kfo_is_host()) + "  my pid " + string(_o.my));
    if (instance_exists(obj_heart))
    {
        var _h = instance_find(obj_heart, 0);
        array_push(_l, "MY SOUL: room " + kh_dbg_n(_h.x) + ", " + kh_dbg_n(_h.y) + "  relative " + kh_dbg_n(_h.x - kbr_ox()) + ", " + kh_dbg_n(_h.y - kbr_oy())
            + "  depth " + string(_h.depth) + "  visible " + string(_h.visible) + "  alpha " + kh_dbg_n(_h.image_alpha));
    }
    else
        array_push(_l, "MY SOUL: no obj_heart");
    var _M = kbr_match();
    if (is_undefined(_M))
    {
        array_push(_l, "MATCH: none");
        return _l;
    }
    array_push(_l, "MATCH " + string(_M.mid) + ": battle on " + string(kbr_on()) + "  started " + string(_M.go) + "  phase " + string(_M.R.ph) + "  playing " + string(_M.me)
        + "  out " + string(_M.out));
    var _pl = is_struct(_M.st) ? kfo_ja(_M.st, "pl") : [];
    var _n = 0;
    var _nb = 0;
    for (var _i = 0; _i < array_length(_pl); _i++)
    {
        var _pid = kfo_jn(_pl[_i], "pid", -1);
        if (_pid == _o.my)
            continue;
        _n++;
        if (kfo_jn(_pl[_i], "bot", 0) == 1)
            _nb++;
    }
    array_push(_l, "OTHER SOULS: " + string(_n) + " (bots " + string(_nb) + ")");
    for (var _i = 0; _i < array_length(_pl); _i++)
    {
        var _p = _pl[_i];
        var _pid = kfo_jn(_p, "pid", -1);
        if (_pid == _o.my)
            continue;
        var _k = string(_pid);
        var _q = variable_struct_exists(_M.ps, _k) ? variable_struct_get(_M.ps, _k) : undefined;
        var _t = " P" + _k + " " + string_copy(kfo_js(_p, "n", "?"), 1, 8) + ((kfo_jn(_p, "bot", 0) == 1) ? " [BOT]" : "");
        if (is_struct(_q))
        {
            var _r = kbr_rv(_M, _pid);
            var _dr = variable_struct_exists(_r, "dt") && current_time - _r.dt < 500;
            _t += "  rel " + kh_dbg_n(kbr_ps_rx(_q)) + "," + kh_dbg_n(kbr_ps_ry(_q)) + "  room " + kh_dbg_n(kbr_ps_x(_q)) + "," + kh_dbg_n(kbr_ps_y(_q))
                + "  depth -99000  visible " + (_dr ? "1" : "0") + "  alpha " + (_dr ? kh_dbg_n(_r.da) : "0") + "  " + kh_dbg_why(_M, _p, _q);
        }
        else
            _t += "  " + kh_dbg_why(_M, _p, _q);
        array_push(_l, _t);
    }
    // the host's bots (where the host's game keeps them, and what it sends)
    if (kfo_is_host() && is_struct(_o.H))
    {
        var _bl = [];
        for (var _i = 0; _i < array_length(_o.H.pl); _i++)
        {
            if (_o.H.pl[_i].bot)
                array_push(_bl, _o.H.pl[_i]);
        }
        array_push(_l, "BOTS (this game hosts them): " + string(array_length(_bl)));
        for (var _i = 0; _i < array_length(_bl); _i++)
        {
            var _b = _bl[_i];
            var _s = is_struct(_b.bt) ? _b.bt : undefined;
            var _c = kfo_host_botcfg(_i);
            array_push(_l, " P" + string(_b.pid) + " " + _b.n + " " + kfo_bot_pre_name(_c.pre) + "  in match " + string(_b.inm) + " alive " + string(_b.al)
                + "  hp " + string(_b.hp) + (is_struct(_s) ? ("  placed " + string(_s.placed) + "  room " + kh_dbg_n(_s.x) + "," + kh_dbg_n(_s.y)) : "  (not started)")
                + "  sent " + kh_dbg_n(_b.x) + "," + kh_dbg_n(_b.y));
        }
        var _bx = kfo_bot_box();
        array_push(_l, "BOT BOX: " + (is_undefined(_bx) ? "none (no battle box found)" : (kh_dbg_n(_bx[0]) + "," + kh_dbg_n(_bx[1]) + " - " + kh_dbg_n(_bx[2]) + "," + kh_dbg_n(_bx[3]))));
    }
    return _l;
}

// the controller's Draw (over everything it draws): the lines top left on black, and a square at every other SOUL
function kh_dbg_draw()
{
    var _d = kh_dbg();
    _d.fr = kh_dbg_frame() + 1;
    if (!_d.on)
        return 0;
    var xx = camera_get_view_x(view_camera[0]);
    var yy = camera_get_view_y(view_camera[0]);
    var _M = kbr_match();
    var _l = kh_dbg_lines();
    draw_set_font(fnt_small);
    var _w = 0;
    for (var _i = 0; _i < array_length(_l); _i++)
        _w = max(_w, string_width(_l[_i]));
    draw_set_alpha(0.65);
    draw_set_color(c_black);
    draw_rectangle(xx + 2, yy + 2, xx + 8 + min(630, _w), yy + 10 + ((array_length(_l) + 1) * 11), false);
    draw_set_alpha(1);
    for (var _i = 0; _i < array_length(_l); _i++)
    {
        draw_set_color((_i == 0) ? c_yellow : c_white);
        draw_text(xx + 5, yy + 4 + (_i * 11), _l[_i]);
    }
    draw_set_color(c_gray);
    draw_text(xx + 5, yy + 6 + (array_length(_l) * 11), "F3: OVERLAY OFF   LOG: " + kh_dbg_file() + " (SAVE FOLDER)");
    // (over the text panel, so a SOUL under it still shows)
    // a plain square at each other SOUL's position (their colour, a black edge), drawn whatever the SOUL settings are
    if (!is_undefined(_M) && is_struct(_M.st))
    {
        var _pl = kfo_ja(_M.st, "pl");
        for (var _i = 0; _i < array_length(_pl); _i++)
        {
            var _pid = kfo_jn(_pl[_i], "pid", -1);
            if (_pid == global.kfo.my || kfo_jn(_pl[_i], "al", 0) != 1)
                continue;
            var _k = string(_pid);
            if (!variable_struct_exists(_M.ps, _k))
                continue;
            var _q = variable_struct_get(_M.ps, _k);
            var _x = kbr_ps_x(_q) + kbr_soul_in() + 8;
            var _y = kbr_ps_y(_q) + kbr_soul_in() + 8;
            draw_set_alpha(1);
            draw_set_color(c_black);
            draw_rectangle(_x - 7, _y - 7, _x + 7, _y + 7, false);
            draw_set_color(kbr_pcol(kbr_pslot(_pid)));
            draw_rectangle(_x - 5, _y - 5, _x + 5, _y + 5, false);
            draw_set_font(fnt_small);
            draw_set_color(c_white);
            draw_text(_x + 9, _y - 6, "P" + _k);
        }
    }
    // the host's bots where its own game keeps them: a yellow frame (it should sit on the bot's square)
    if (is_struct(global.kfo) && kfo_is_host() && is_struct(global.kfo.H))
    {
        for (var _i = 0; _i < array_length(global.kfo.H.pl); _i++)
        {
            var _b = global.kfo.H.pl[_i];
            if (!_b.bot || !_b.al || !_b.inm || !is_struct(_b.bt))
                continue;
            draw_set_color(c_yellow);
            draw_rectangle(_b.bt.x - 9, _b.bt.y - 9, _b.bt.x + 9, _b.bt.y + 9, true);
        }
    }

    draw_set_color(c_white);
    return 1;
}

// ---------- CONFIG > RESET MOD SETTINGS (build 49) ----------
// Every online setting back to the default: SOUL settings (others shown at 70%), your SOUL colour, MATCH VIEW, the match keys,
// the online song and the room settings you host with. Kept: your name, skin, relay server, the fight setup, records,
// loadouts and presets. Saved at once (knightfights_online.ini).
function kfo_settings_reset()
{
    var _o = kfo_get();
    _o.view = kfo_view_default();
    _o.look = kfo_look_default();
    _o.keys = kfo_keys_default();
    _o.song = -1;
    _o.vis = 1;
    _o.set = kfo_set_clean(kfo_set_default());
    _o.sop = _o.view.sop;
    _o.names = _o.view.names;
    kfo_ini_save();
    if (kfo_in_room())
        kfo_look_sent();
    return 1;
}

function knight_build_stamp_short()
{
    return "BUILD " + string(kfo_version());
}
