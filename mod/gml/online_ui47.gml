
// ===== Build 47: MORE OPTIONS pages - SOUL VISIBILITY ("SOULS"), SOUL APPEARANCE ("MY SOUL"), MATCH VIEW ("VIEW") =====
// One kind of page for all three: small rows on the left (label, value), the hot row's description in the top bar, a live
// preview on the right. < > (or Z) changes the hot row and it is kept at once (knightfights_online.ini). In a room a new SOUL
// colour goes to the host right away (everyone's room list and SOULs show it).

function kfo_ui_pg_rows(_pg)
{
    switch (_pg)
    {
        // build 48: SOUL SETTINGS is five rows (SOUL COLOR opens the colour page); the rest of build 47's SOUL rows are gone
        case "onl_view": return ["show", "vcol", "names", "sop", "hl", "done"];
        case "onl_look": return ["col", "r", "g", "b", "hex", "ol", "olc", "done"];
        case "onl_bots":
        case "onl_bot": return kfo_ui_bots_rows(_pg);
        case "onl_inv": return kfo_ui_inv_rows();
        case "onl_mview": return ["shake", "flash", "blines", "hints", "elim", "info", "net", "spv", "shud", "cam", "help", "zoom", "wnames", "chat", "reset", "done"];
    }
    return ["done"];
}

function kfo_ui_pg_caption(_pg)
{
    switch (_pg)
    {
        case "onl_view": return "SOULS";
        case "onl_look": return "MY SOUL";
        case "onl_mview": return "VIEW";
        case "onl_bots": return "BOTS";
        case "onl_bot": return "BOT";
        case "onl_inv": return "INVITE";
    }
    return "OPTIONS";
}

function kfo_onoff(_v)
{
    return _v ? "ON" : "OFF";
}

// [label, value] of a row
function kfo_ui_pg_label(_pg, _id)
{
    if (_pg == "onl_bots" || _pg == "onl_bot")
        return kfo_ui_bots_label(_pg, _id);
    if (_pg == "onl_inv")
        return kfo_ui_inv_label(_id);
    var _V = kfo_view();
    var _L = kfo_look();
    switch (_id)
    {
        case "reset": return ["DEFAULTS", ""];
        case "done": return ["DONE", ""];
    }
    if (_pg == "onl_look")
    {
        switch (_id)
        {
            case "col": return ["SOUL COLOR", kfo_col_name(_L.col)];
            case "r": return ["RED", string(colour_get_red(_L.col))];
            case "g": return ["GREEN", string(colour_get_green(_L.col))];
            case "b": return ["BLUE", string(colour_get_blue(_L.col))];
            case "hex": return ["HEX CODE", kfo_col_hex(_L.col)];
            case "ol": return ["MY OUTLINE", kfo_onoff(_L.ol)];
            case "olc": return ["OUTLINE COLOR", kfo_olc_name(_L.olc)];
            case "hli": return ["HIGHLIGHT", (_L.hli == 1) ? "LOW" : ((_L.hli == 2) ? "MEDIUM" : "HIGH")];
            case "gmc": return ["SOUL MODES", (_L.gmc == 0) ? "GAME'S COLOR" : "MINE + MARK"];
            case "sop": return ["OTHERS' OPACITY", string(_V.sop) + "%"];
        }
        return [_id, ""];
    }
    switch (_id)
    {
        case "show": return ["SHOW OTHER SOULS", kfo_onoff(_V.show)];
        case "vcol": return ["SOUL COLOR", kfo_col_name(kfo_look().col)];
        case "chat": return ["CHAT", _V.chat ? "SHOWN" : "HIDDEN"];
        case "sop": return ["OTHER SOUL OPACITY", string(_V.sop) + "%"];
        case "names": return ["SOUL NAMES", kfo_onoff(_V.names)];
        case "nop": return ["NAME OPACITY", string(_V.nop) + "%"];
        case "outl": return ["SHOW SOUL OUTLINES", kfo_onoff(_V.outl)];
        case "cmode": return ["SOUL COLOR MODE", (_V.cmode == 0) ? "THEIR COLORS" : ((_V.cmode == 1) ? "DISTINCT" : ((_V.cmode == 2) ? "ALL RED" : "SIMPLE"))];
        case "hl": return ["HIGHLIGHT MY SOUL", kfo_onoff(_V.hl)];
        case "dim": return ["DIM OTHER SOULS", kfo_onoff(_V.dim)];
        case "skfx": return ["REMOTE SKILL FX", (_V.skfx == 0) ? "OFF" : ((_V.skfx == 1) ? "REDUCED" : "FULL")];
        case "dmgfx": return ["REMOTE DAMAGE FX", kfo_onoff(_V.dmgfx)];
        case "nums": return ["PLAYER NUMBERS", kfo_onoff(_V.nums)];
        case "fade": return ["FADE OVERLAPS", kfo_onoff(_V.fade)];
        case "spv": return ["WHILE WATCHING", (_V.spv == 0) ? "ALL SOULS" : ((_V.spv == 1) ? "AS PLAYING" : "FOLLOWED")];
        case "mark": return ["SHAPE MARKERS", kfo_onoff(_V.mark)];
        case "shake": return ["REDUCED SHAKE", kfo_onoff(_V.shake)];
        case "flash": return ["REDUCED FLASHING", kfo_onoff(_V.flash)];
        case "simple": return ["SIMPLE EFFECTS", kfo_onoff(_V.simple)];
        case "hints": return ["KEY HINTS", kfo_onoff(_V.hints)];
        case "elim": return ["OUT NOTICES", (_V.elim == 0) ? "MINIMAL" : "FULL"];
        case "info": return ["MATCH INFO", kfo_onoff(_V.info)];
        case "net": return ["NETWORK STATS", kfo_onoff(_V.net)];
        case "shud": return ["WATCHING HUD", kbr_shud_name(_V.shud)];
        case "cam": return ["WATCH CAMERA", kbr_cam_name(_V.cam)];
        case "help": return ["WATCH KEYS BOX", kfo_onoff(_V.help)];
        case "zoom": return ["ZOOM", string(_V.zoom) + "X"];
        case "wnames": return ["ROOM NAMES", kfo_onoff(_V.wnames)];
        case "blines": return ["BOSS LINES", kfo_onoff(_V.blines)];
    }
    return [_id, ""];
}

function kfo_ui_pg_desc(_pg, _id)
{
    if (_pg == "onl_bots" || _pg == "onl_bot")
        return kfo_ui_bots_desc(_pg, _id);
    if (_pg == "onl_inv")
        return kfo_ui_inv_desc(_id);
    switch (_id)
    {
        case "reset":
            return (_pg == "onl_look") ? "Z: your SOUL back to the game's red, outline#on, medium highlight." : "Z: every setting on this page back to its#default.";
        case "done": return "Z: back.";
        case "show": return "< >: see the other players' SOULs in the box#(V in a match). Only on your screen.";
        case "vcol": return "< >: your SOUL's color (everyone sees it).#Z: all colors, your own mix, a color code.";
        case "chat": return "< >: the chat on your screen. T or ENTER opens it,#ENTER sends, ESC closes; /MUTE NAME hides one.";
        case "sop": return "< >: how solid the OTHER SOULs are, 15-100%;#hold it to slide. Yours always stays full.";
        case "names": return "< >: each player's name under their SOUL#(off: no names at all).";
        case "nop": return "< >: slide how strongly those names show, 0-100%.";
        case "outl": return "< >: an outline around every other SOUL#(light or dark, whichever stands out).";
        case "cmode": return "< >: THEIR COLORS (each player's own), DISTINCT#(one per place), ALL RED (the game's), SIMPLE.";
        case "hl": return "< >: your SOUL stays on top: others over it#show fainter (OUTLINE AUTO: a white edge).";
        case "dim": return "< >: the others' SOULs darker, so yours#stands out.";
        case "skfx": return "< >: the others' shield, regeneration and#reflection marks: OFF, REDUCED or FULL.";
        case "dmgfx": return "< >: another SOUL blinks while a hit's#invincibility lasts.";
        case "nums": return "< >: P1-P8 beside the SOULs (their place in#the player list).";
        case "fade": return "< >: SOULs on top of yours or of each other#show fainter. Nobody is moved.";
        case "spv": return "< >: while you watch: ALL SOULS (full), AS#PLAYING (these settings), FOLLOWED only.";
        case "col": return "< >: RED, ORANGE, YELLOW, GREEN, CYAN, BLUE,#PURPLE, PINK, WHITE (or your own mix below).";
        case "r": return "< >: the red of your SOUL (0-255, by 5).";
        case "g": return "< >: the green of your SOUL (0-255, by 5).";
        case "b": return "< >: the blue of your SOUL (0-255, by 5).";
        case "hex": return "Z: type a color code: 6 digits RRGGBB (or 3: RGB),#like A040FF.";
        case "ol": return "< >: an outline around your own SOUL.";
        case "olc": return "< >: its color (AUTO: dark on light colors,#light on dark ones).";
        case "hli": return "< >: how strong HIGHLIGHT MY SOUL is.";
        case "gmc": return "< >: when an attack gives SOULs a mode color:#show the game's color, or yours with a mark.";
        case "mark": return "< >: a shape beside every other SOUL (circle,#triangle...): players apart without colors.";
        case "shake": return "< >: the screen does not shake (the game's own#shake setting; the bullets stay the same).";
        case "flash": return "< >: the hub's screen flashes at a third,#steady warning edges.";
        case "simple": return "< >: no SOUL pieces, trails or extra glow from#the others.";
        case "hints": return "< >: the key lines in the countdown and the#watching keys box.";
        case "elim": return "< >: MINIMAL: a line in the log. FULL: also a#short notice over the box.";
        case "info": return "< >: the cycle, the players standing, the time,#the preset and sudden death (top middle).";
        case "net": return "< >: your ping and its quality, bottom right#(trouble shows either way).";
        case "shud": return "< >: the card of the player you watch: FULL,#SMALL or OFF (C while watching).";
        case "cam": return "< >: the camera you start watching with:#FOLLOW, FULL ARENA, AUTO or ZOOM.";
        case "help": return "< >: the watching keys box (H while watching):#< > follow, Z camera, X zoom, C card, V SOULs.";
        case "zoom": return "< >: how much ZOOM magnifies (2x or 3x;#X while watching).";
        case "wnames": return "< >: the players' names over their heads in#the cold place (NAME OPACITY applies).";
        case "blines": return "< >: the bosses' speech balloons, beside them#and off the box (their voices play either way).";
    }
    return "";
}

// a row changed (< > or Z); true when something changed
function kfo_ui_pg_change(_pg, _id, _d, _ok)
{
    if (_pg == "onl_bots" || _pg == "onl_bot")
        return kfo_ui_bots_change(_pg, _id, _d, _ok);
    if (_pg == "onl_inv")
        return kfo_ui_inv_change(_id, _ok);
    var _V = kfo_view();
    var _L = kfo_look();
    var _o = kfo_get();
    if (_id == "reset")
    {
        if (!_ok)
            return false;
        if (_pg == "onl_look")
            _o.look = kfo_look_default();
        else
        {
            var _df = kfo_view_default();
            var _rows = kfo_ui_pg_rows(_pg);
            for (var _i = 0; _i < array_length(_rows); _i++)
            {
                if (variable_struct_exists(_df, _rows[_i]))
                    variable_struct_set(_V, _rows[_i], variable_struct_get(_df, _rows[_i]));
            }
        }
        _o.sop = _o.view.sop;
        _o.names = _o.view.names;
        kfo_look_sent();
        return true;
    }
    if (_pg == "onl_look")
    {
        switch (_id)
        {
            case "col":
                var _p = kfo_col_presets();
                var _i = kfo_col_preset_of(_L.col);
                if (_i < 0)
                    _i = (_d > 0) ? -1 : 0;
                _i = (_i + _d + array_length(_p)) mod array_length(_p);
                _L.col = _p[_i][1];
                kfo_look_sent();
                return true;
            case "r":
            case "g":
            case "b":
                var _rgb = [colour_get_red(_L.col), colour_get_green(_L.col), colour_get_blue(_L.col)];
                var _k = (_id == "r") ? 0 : ((_id == "g") ? 1 : 2);
                _rgb[_k] = clamp(_rgb[_k] + (_d * 5), 0, 255);
                _L.col = make_color_rgb(_rgb[0], _rgb[1], _rgb[2]);
                kfo_look_sent();
                return true;
            case "hex":
                if (_ok)
                    kfo_ui_text("hex");
                return false;
            case "ol": _L.ol = 1 - _L.ol; return true;
            case "olc": _L.olc = (_L.olc + 6 + _d) mod 6; return true;
            case "hli": _L.hli = 1 + ((_L.hli - 1 + 3 + _d) mod 3); return true;
            case "gmc": _L.gmc = 1 - _L.gmc; return true;
            case "sop": _V.sop = clamp(_V.sop + (_d * 5), kfo_sop_min(), 100); _o.sop = _V.sop; return true;
        }
        return false;
    }
    switch (_id)
    {
        case "vcol":
            // Z: the colour page (all presets, your own mix, a code); < >: the presets right here
            if (_ok)
            {
                kfo_ui_pg_open("onl_look", _pg);
                return false;
            }
            return kfo_ui_pg_change("onl_look", "col", _d, false);
        case "sop": _V.sop = clamp(_V.sop + (_d * 5), kfo_sop_min(), 100); _o.sop = _V.sop; return true;
        case "nop": _V.nop = clamp(_V.nop + (_d * 5), 0, 100); return true;
        case "cmode": _V.cmode = (_V.cmode + 4 + _d) mod 4; return true;
        case "skfx": _V.skfx = (_V.skfx + 3 + _d) mod 3; return true;
        case "spv": _V.spv = (_V.spv + 3 + _d) mod 3; return true;
        case "shud": _V.shud = (_V.shud + 3 + _d) mod 3; return true;
        case "cam": _V.cam = (_V.cam + 4 + _d) mod 4; return true;
        case "zoom": _V.zoom = (_V.zoom == 2) ? 3 : 2; return true;
        case "elim": _V.elim = 1 - _V.elim; return true;
        case "names": _V.names = 1 - _V.names; _o.names = _V.names; return true;
    }
    if (variable_struct_exists(_V, _id))
    {
        variable_struct_set(_V, _id, 1 - variable_struct_get(_V, _id));
        return true;
    }
    return false;
}

// a new SOUL colour while in a room: the host passes it on (everybody's room list and the SOULs in the match)
function kfo_look_sent()
{
    var _o = kfo_get();
    if (kfo_in_room())
        kfo_up({ k: "look", cl: _o.look.col });
    return 1;
}

// open one of the pages (from MORE OPTIONS or the room)
function kfo_ui_pg_open(_pg, _from)
{
    var _u = global.knight_ui;
    // build 48: SOUL SETTINGS > SOUL COLOR opens the colour page; leaving it comes back to SOUL SETTINGS on that row
    _u.pg_back = (_from == "onl_view" || _from == "onl_bots") ? { from: _u.pg_from, row: variable_struct_exists(_u, "pg_row") ? _u.pg_row : 0 } : undefined;
    _u.sub = _pg;
    _u.pg_row = 0;
    _u.pg_scroll = 0;
    _u.pg_from = _from;
    snd_play(snd_select);
}

function kfo_ui_pg_leave()
{
    var _u = global.knight_ui;
    _u.sub = _u.pg_from;
    if ((_u.sub == "onl_view" || _u.sub == "onl_bots") && variable_struct_exists(_u, "pg_back") && is_struct(_u.pg_back))
    {
        _u.pg_from = _u.pg_back.from;
        _u.pg_row = _u.pg_back.row;
        _u.pg_back = undefined;
    }
    else
        _u.pg_row = 0;
    _u.pg_scroll = 0;
}

function kfo_ui_pg_shown(_pg)
{
    // (DRBR 1.0.1: rows in the menu's size - 10; 9 on the BOT page under the bot's name, and on INVITE over the room code)
    if (!is_undefined(_pg) && (_pg == "onl_bot" || _pg == "onl_inv"))
        return 9;
    return 10;
}

function kfo_ui_step_pg(_pg, _up, _down, _left, _right, _ok, _back)
{
    var _u = global.knight_ui;
    if (!variable_struct_exists(_u, "pg_row"))
    {
        _u.pg_row = 0;
        _u.pg_scroll = 0;
        _u.pg_from = "onl_opt";
    }
    var _rows = kfo_ui_pg_rows(_pg);
    var _n = array_length(_rows);
    if (_back)
    {
        kfo_ui_pg_leave();
        snd_play(snd_menumove);
        kfo_ini_save();
        return 0;
    }
    if (_up || _down)
    {
        _u.pg_row = knight_ui_cycle(_u.pg_row, _up ? -1 : 1, _n);
        snd_play(snd_menumove);
    }
    _u.pg_row = clamp(_u.pg_row, 0, _n - 1);
    _u.pg_scroll = clamp(_u.pg_scroll, max(0, _u.pg_row - (kfo_ui_pg_shown(_pg) - 1)), min(_u.pg_row, max(0, _n - kfo_ui_pg_shown(_pg))));
    var _id = _rows[_u.pg_row];
    if (_id == "done")
    {
        if (_ok)
        {
            kfo_ui_pg_leave();
            snd_play(snd_select);
            kfo_ini_save();
        }
        return 0;
    }
    // a slider: < > held keeps it moving (after a third of a second, a step every other frame)
    if (!variable_struct_exists(_u, "pg_hold"))
        _u.pg_hold = 0;
    var _rep = false;
    if ((kfo_is_slider(_id) || (_pg == "onl_bot" && kfo_ui_bots_is_slider(_id))) && (left_h() || right_h()))
    {
        _u.pg_hold++;
        if (!_left && !_right && _u.pg_hold >= 10 && (_u.pg_hold mod 2) == 0)
        {
            _left = left_h();
            _right = !_left;
            _rep = true;
        }
    }
    else
    {
        // let go after moving it: kept now (not at every step of the move)
        if (_u.pg_hold >= 10)
            kfo_ini_save();
        _u.pg_hold = 0;
    }
    if (!_ok && !_left && !_right)
        return 0;
    if (kfo_ui_pg_change(_pg, _id, _left ? -1 : 1, _ok))
    {
        if (!_rep)
            kfo_ini_save();
        snd_play(_ok ? snd_select : snd_menumove);
    }
    return 0;
}

// DRBR 1.0.1: every row in the game's menu size, 30 apart, 10 at a time (9 under the bot's name on BOT). SOULS and MY SOUL keep
// their pictures on the right (their rows' names short); the other pages use the whole width - what their side used to say is in
// the top bar's text now.
function kfo_ui_pg_split(_pg)
{
    return _pg == "onl_view" || _pg == "onl_look";
}

// the first rows' place: the BOT page has the bot's name over its rows
function kfo_ui_pg_top(_pg)
{
    return (_pg == "onl_bot") ? 136 : 100;
}

// a row's name as the page shows it (shorter beside a picture)
function kfo_ui_pg_short(_pg, _id, _lab)
{
    if (_pg == "onl_view")
    {
        switch (_id)
        {
            case "show": return "OTHER SOULS";
            case "vcol": return "MY COLOR";
            case "names": return "THEIR NAMES";
            case "sop": return "OPACITY";
            case "hl": return "HIGHLIGHT ME";
        }
    }
    if (_pg == "onl_look")
    {
        switch (_id)
        {
            case "col": return "COLOR";
            case "ol": return "OUTLINE";
        }
    }
    return _lab;
}

function kfo_ui_draw_pg(_pg, xx, yy)
{
    var _u = global.knight_ui;
    if (!variable_struct_exists(_u, "pg_row"))
    {
        _u.pg_row = 0;
        _u.pg_scroll = 0;
        _u.pg_from = "onl_opt";
    }
    var _split = kfo_ui_pg_split(_pg);
    // the values' right edge
    var _xr = _split ? (xx + 392) : (xx + 560);
    var _vmax = _split ? 130 : 220;
    if (_split)
    {
        draw_set_color(c_white);
        draw_rectangle(xx + 400, yy + 91, xx + 403, yy + 410, false);
    }
    knight_caption_hub(kfo_ui_pg_caption(_pg), xx + 112, yy + 84);
    var _rows = kfo_ui_pg_rows(_pg);
    var _shown = kfo_ui_pg_shown(_pg);
    var _top = kfo_ui_pg_top(_pg);
    var _sc = clamp(_u.pg_scroll, 0, max(0, array_length(_rows) - _shown));
    for (var _i = _sc; _i < array_length(_rows) && _i < _sc + _shown; _i++)
    {
        var _y = yy + _top + ((_i - _sc) * 30);
        var _hot = (_u.pg_row == _i);
        var _lv = kfo_ui_pg_label(_pg, _rows[_i]);
        var _bsl = (_pg == "onl_bot" && kfo_ui_bots_is_slider(_rows[_i]));
        var _sl = _bsl || kfo_is_slider(_rows[_i]);
        scr_84_set_draw_font("mainbig");
        var _vw = (_lv[1] != "") ? min(string_width(_lv[1]), _vmax) : 0;
        var _lw = (_xr - (xx + 96)) - _vw - (_sl ? 84 : 18);
        draw_set_color(_hot ? c_yellow : c_white);
        knight_txt(xx + 96, _y, knight_fit(kfo_ui_pg_short(_pg, _rows[_i], _lv[0]), _lw));
        if (_lv[1] != "")
        {
            draw_set_halign(fa_right);
            draw_set_color(_hot ? c_yellow : c_ltgray);
            knight_txt(_xr, _y, knight_fit(_lv[1], _vmax));
            draw_set_halign(fa_left);
        }
        // build 47: the opacities as sliders, 0 to 100 in steps of 5 (the bar before the number)
        if (_bsl)
            kfo_slider_draw(_xr - _vw - 72, _xr - _vw - 16, _y + 9, kfo_ui_bots_slider_v(_rows[_i]), _hot);
        else if (kfo_is_slider(_rows[_i]))
            kfo_slider_draw(_xr - _vw - 72, _xr - _vw - 16, _y + 9, real(string_digits(_lv[1])), _hot);
        if (_hot)
            knight_heart(xx + 72, _y + 8);
    }
    // more rows above / below: the game's arrows, in the heart's column
    knight_ui_arrows(xx + 80, yy + _top - 6, yy + _top + (_shown * 30) - 4, _sc > 0, _sc + _shown < array_length(_rows), _u.siner);
    switch (_pg)
    {
        case "onl_view": kfo_ui_prev_view(xx, yy); break;
        case "onl_look": kfo_ui_prev_look(xx, yy); break;
        case "onl_bot": kfo_ui_prev_bot_top(xx, yy); break;
        case "onl_inv": kfo_ui_prev_inv(xx, yy, _sc + min(_shown, array_length(_rows) - _sc)); break;
    }
    draw_set_color(c_white);
}

// SOUL SETTINGS' picture: a box with your SOUL and three others (one over yours, one blinking from a hit), drawn by the very
// function the match uses (build 48: no rings, no markers - the SOULs as the game draws them; their names in the match's own
// small print, as the match shows them). DRBR 1.0.1: beside the rows (170 wide), its line in the menu's size.
function kfo_ui_prev_view(xx, yy)
{
    var _V = kfo_view();
    var _L = kfo_look();
    var _bx = xx + 414;
    var _by = yy + 104;
    draw_set_color(c_black);
    draw_rectangle(_bx, _by, _bx + 160, _by + 150, false);
    draw_set_color(c_lime);
    draw_rectangle(_bx + 8, _by + 8, _bx + 152, _by + 142, true);
    draw_rectangle(_bx + 9, _by + 9, _bx + 151, _by + 141, true);
    var _demo = [["SUSIE", 1, make_color_rgb(165, 70, 255), 108, 34, 0, 0], ["RALSEI", 2, make_color_rgb(40, 220, 80), 72, 66, 0, 1], ["NOELLE", 3, make_color_rgb(255, 230, 40), 30, 96, 1, 0]];
    var _na = _V.nop / 100;
    draw_set_font(fnt_small);
    for (var _i = 0; _i < 3 && _V.show; _i++)
    {
        var _e = _demo[_i];
        var _c = _e[2];
        var _a = _V.sop / 100;
        if (_e[6] == 1)
            _a *= 0.45;
        if (_e[5] == 1 && ((current_time div 100) mod 2) == 1)
            _a *= 0.35;
        var _x = _bx + _e[3];
        var _y = _by + _e[4];
        kfo_soul_draw(_x, _y, 1, _c, _a, c_black);
        if (_V.names)
        {
            draw_set_halign(fa_center);
            draw_set_alpha(_na * max(0.35, _a));
            draw_set_color(kfo_col_shadow(_c));
            draw_text(_x + 9, _y + 21 + ((_e[6] == 1) ? 11 : 0), _e[0]);
            draw_set_color(kfo_col_text(_c));
            draw_text(_x + 8, _y + 20 + ((_e[6] == 1) ? 11 : 0), _e[0]);
            draw_set_alpha(1);
            draw_set_halign(fa_left);
        }
    }
    // yours (always full)
    kfo_soul_draw(_bx + 72, _by + 66, 1, _L.col, 1, kfo_my_edge());
    draw_set_halign(fa_center);
    draw_set_color(c_gray);
    knight_txt(_bx + 80, _by + 160, _V.show ? "OTHERS SHOWN" : "OTHERS HIDDEN");
    draw_set_halign(fa_left);
}

// SOUL COLOR's picture: your SOUL big, its color code and name, the palette with yours framed (two rows), your name as the room's
// list shows it. DRBR 1.0.1: beside the rows, in the menu's size.
function kfo_ui_prev_look(xx, yy)
{
    var _L = kfo_look();
    var _bx = xx + 414;
    var _by = yy + 100;
    var _cx = _bx + 80;
    kfo_soul_draw(_cx - 24, _by + 6, 3, _L.col, 1, kfo_my_edge());
    draw_set_halign(fa_center);
    draw_set_color(c_white);
    knight_txt(_cx, _by + 62, kfo_col_hex(_L.col));
    draw_set_color(c_ltgray);
    knight_txt(_cx, _by + 92, knight_fit(kfo_col_name(_L.col), 160));
    draw_set_halign(fa_left);
    // the palette: every preset, yours framed (5 a row)
    var _p = kfo_col_presets();
    var _cur = kfo_col_preset_of(_L.col);
    for (var _i = 0; _i < array_length(_p); _i++)
    {
        var _px = _bx + 18 + ((_i mod 5) * 26);
        var _py = _by + 132 + ((_i div 5) * 26);
        kfo_soul_draw(_px, _py, 1, _p[_i][1], 1, c_black);
        if (_i == _cur)
        {
            draw_set_color(c_white);
            draw_rectangle(_px - 4, _py - 4, _px + 19, _py + 19, true);
        }
    }
    var _ny = _by + 132 + (ceil(array_length(_p) / 5) * 26) + 6;
    draw_set_halign(fa_center);
    draw_set_color(kfo_col_shadow(_L.col));
    knight_txt(_cx + 1, _ny + 1, knight_fit(kfo_get().name, 160));
    draw_set_color(kfo_col_text(_L.col));
    knight_txt(_cx, _ny, knight_fit(kfo_get().name, 160));
    if (_cur < 0)
    {
        draw_set_color(c_gray);
        knight_txt(_cx, _ny + 32, "YOUR OWN MIX");
    }
    draw_set_halign(fa_left);
    draw_set_color(c_white);
}

// the BOT page's bot: its head, its name and skill over the rows
function kfo_ui_prev_bot_top(xx, yy)
{
    var _l = kfo_ui_bots_list();
    var _bi = kfo_ui_bot_i();
    if (_bi >= array_length(_l))
        return 0;
    var _b = _l[_bi];
    kfo_skin_head_draw(kfo_skin_ok(_b.s), xx + 96, yy + 96);
    var _c = kfo_host_botcfg(_bi);
    var _sk = kfo_bot_pre_name(_c.pre) + (_c.own ? "" : " (ROOM)");
    scr_84_set_draw_font("mainbig");
    var _skw = string_width(_sk);
    draw_set_color(c_white);
    knight_txt(xx + 140, yy + 100, knight_fit(_b.n, (xx + 560 - _skw - 16) - (xx + 140)));
    draw_set_halign(fa_right);
    draw_set_color(c_yellow);
    knight_txt(xx + 560, yy + 100, _sk);
    draw_set_halign(fa_left);
    return 1;
}

// CONNECTION HELP in the room: how this room connects, the ping, what to try
function kfo_ui_conn_help()
{
    var _o = kfo_get();
    var _l = [];
    var _m = (_o.mode == "steam") ? "STEAM (Spacewar, app 480)" : ((_o.mode == "local") ? "PRACTICE (this computer)" : ("RELAY " + kfo_server_text()));
    array_push(_l, "This room: " + _m + ".");
    if (kfo_is_host())
        array_push(_l, "You are the host: the others connect to you.");
    else
        array_push(_l, "Your ping to the host: " + ((_o.rtt >= 0) ? kbr_ping_text(_o.rtt) : "not measured yet") + ".");
    array_push(_l, "Cannot join? All need the same build (" + string(kfo_version()) + "),");
    array_push(_l, "and Steam running for Steam rooms.");
    array_push(_l, "Relay: the server's port must be open.");
    array_push(_l, "Lag: the best connection should host.");
    return _l;
}

// the room's line about the match running now (from the host's standings, which every room member gets)
function kfo_ui_match_line()
{
    var _o = kfo_get();
    var _s = _o.lst;
    if (!is_struct(_s) || current_time - _o.lst_t > 5000)
        return "A MATCH IS ON.";
    var _t = max(0, kfo_jn(_s, "t", 0) - kfo_jn(_s, "intro", 0));
    var _kn = kfo_jn(_s, "kn", -1);
    var _ai = kfo_jn(_s, "ai", -1);
    var _k = "";
    if (_kn >= 0)
        _k = string_upper(kbr_ok_name(_kn)) + ((_ai >= 0) ? (": " + string_upper(kbr_atk_name(_kn, _ai))) : "") + ". ";
    var _sd = "";
    var _sd0 = kfo_jn(_s, "sd0", -1);
    if (_sd0 >= 0 && kfo_jn(_s, "t", 0) >= _sd0)
        _sd = " SUDDEN DEATH.";
    return "MATCH ON " + kfo_time_text(_t) + ". " + _k + string(kfo_jn(_s, "an", 0)) + " OF " + string(kfo_jn(_s, "sn", 0)) + " STANDING, "
        + string(kfo_jn(_s, "sc", 0)) + " WATCHING." + _sd;
}

// a player's status in the room's list: [text, colour]
function kfo_ui_pstatus(_p, _hostid, _match)
{
    var _pid = kfo_jn(_p, "pid", -2);
    if (_match)
    {
        if (kfo_jn(_p, "inm", 0) == 1)
        {
            if (kfo_jn(_p, "al", 0) == 1)
                return ["ALIVE", c_lime];
            return [kbr_out_text(kfo_jn(_p, "pl", 0)), c_gray];
        }
        if (kfo_jn(_p, "sp", 0) == 1)
            return ["WATCHING", c_aqua];
        return ["WAITING", c_gray];
    }
    if (_pid == _hostid)
        return ["HOST", c_yellow];
    if (kfo_jn(_p, "bot", 0) == 1)
        return ["BOT", c_ltgray];
    if (kfo_jn(_p, "rd", 0) == 1)
        return [kfo_ui_after_match() ? "REMATCH" : "READY", c_lime];
    return ["...", c_gray];
}

// the room had a match already (READY is the rematch vote)
function kfo_ui_after_match()
{
    var _o = kfo_get();
    return is_struct(_o.lobby) && is_struct(kfo_jv(_o.lobby, "res"));
}
