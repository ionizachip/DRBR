// ===== Knight Hub drawing: DELTARUNE dark-world menu metrics =====
// Top bar 80 px (tab buttons at x 120 + 100*i, 2x), box scr_darkbox(50, 80, 590, 420), party panel at the bottom,
// menu text in the "mainbig" font at scale 1 (no fractional scaling), the "main" font for small print,
// heart cursor 25 px left of a row and 10 px down, yellow = chosen / active.
function knight_cam_x()
{
    return camera_get_view_x(view_camera[0]);
}

function knight_cam_y()
{
    return camera_get_view_y(view_camera[0]);
}

function knight_lh()
{
    return 30;
}

function knight_txt(_x, _y, _s)
{
    scr_84_set_draw_font("mainbig");
    draw_text(_x, _y, _s);
}

function knight_txt_small(_x, _y, _s)
{
    scr_84_set_draw_font("main");
    draw_text(_x, _y, _s);
}

function knight_fit(_s, _w)
{
    scr_84_set_draw_font("mainbig");
    if (string_width(_s) <= _w)
        return _s;
    while (string_length(_s) > 1 && string_width(_s + "..") > _w)
        _s = string_copy(_s, 1, string_length(_s) - 1);
    return _s + "..";
}

function knight_fit_small(_s, _w)
{
    scr_84_set_draw_font("main");
    if (string_width(_s) <= _w)
        return _s;
    while (string_length(_s) > 1 && string_width(_s + "..") > _w)
        _s = string_copy(_s, 1, string_length(_s) - 1);
    return _s + "..";
}

// word-wrap in the current font. "#" and "\n" force a break; runs of spaces inside a line are kept
function knight_wrap_font(_s, _w, _font)
{
    scr_84_set_draw_font(_font);
    _s = string_replace_all(_s, "#", "\n");
    var _lines = [];
    var _cur = "";
    var _word = "";
    var _sp = 0;
    var _n = string_length(_s);
    for (var _i = 1; _i <= (_n + 1); _i++)
    {
        var _ch = (_i <= _n) ? string_char_at(_s, _i) : "\n";
        if (_ch == " " || _ch == "\n")
        {
            if (_word != "")
            {
                var _try = (_cur == "") ? _word : (_cur + string_repeat(" ", max(1, _sp)) + _word);
                if (_cur != "" && string_width(_try) > _w)
                {
                    array_push(_lines, _cur);
                    _cur = _word;
                }
                else
                    _cur = _try;
                _word = "";
                _sp = 0;
            }
            if (_ch == " ")
                _sp++;
            else if (_i <= _n || _cur != "" || array_length(_lines) == 0)
            {
                array_push(_lines, _cur);
                _cur = "";
                _sp = 0;
            }
        }
        else
            _word += _ch;
    }
    return _lines;
}

function knight_wrap(_s, _w)
{
    return knight_wrap_font(_s, _w, "mainbig");
}

// up to _max wrapped lines; returns the height used
function knight_para(_x, _y, _s, _w, _max)
{
    var _l = knight_wrap(_s, _w);
    var _n = min(array_length(_l), _max);
    for (var _i = 0; _i < _n; _i++)
        knight_txt(_x, _y + (_i * knight_lh()), _l[_i]);
    return _n * knight_lh();
}

function knight_para_small(_x, _y, _s, _w, _max)
{
    var _l = knight_wrap_font(_s, _w, "main");
    var _n = min(array_length(_l), _max);
    for (var _i = 0; _i < _n; _i++)
    {
        var _t = _l[_i];
        // cut short: the last line shows that more follows
        if (_i == _n - 1 && array_length(_l) > _max)
            _t = knight_fit_small(_t + " ...", _w);
        knight_txt_small(_x, _y + (_i * 16), _t);
    }
    return _n * 16;
}

function knight_heart(_x, _y)
{
    draw_sprite(spr_heart, 0, _x, _y);
}

// left / right arrows beside a page title (records, credits)
function knight_ui_side_arrows(xx, _y, _siner)
{
    // spr_morearrow points down with its origin top-left: -90 turns it to point left (drawn below the
    // origin), 90 to point right (drawn above it), so the two y offsets differ to line up on the title
    var _o = sin(_siner / 12) * 3;
    draw_sprite_ext(spr_morearrow, 0, xx + 84 - _o, _y + 8, 1, 1, -90, c_white, 1);
    draw_sprite_ext(spr_morearrow, 0, xx + 556 + _o, _y + 21, 1, 1, 90, c_white, 1);
}

function knight_ui_arrows(_x, _top, _bottom, _canup, _candown, _siner)
{
    if (_canup)
        draw_sprite_ext(spr_morearrow, 0, _x, _top - (sin(_siner / 12) * 3), 1, -1, 0, c_white, 1);
    if (_candown)
        draw_sprite_ext(spr_morearrow, 0, _x, _bottom + (sin(_siner / 12) * 3), 1, 1, 0, c_white, 1);
}

// small boxed section caption (CHAR / STATS style). spr: the game's own sprite or the hub one
function knight_caption(_spr, _f, _x, _y)
{
    draw_sprite_ext(_spr, _f, _x, _y, 2, 2, 0, c_white, 1);
}

// hub caption frame by word (see make_hub_ui_assets.py)
function knight_capf(_w)
{
    switch (_w)
    {
        case "KNIGHTS": return 0;
        case "INFO": return 1;
        case "MEMBERS": return 2;
        case "RULES": return 3;
        case "OPTIONS": return 4;
        case "PRESETS": return 5;
        case "RECORDS": return 6;
        case "CREDITS": return 7;
        case "MUSIC": return 8;
        case "PARTY": return 9;
        case "SLOT": return 10;
        case "DETAILS": return 11;
        case "BEST": return 12;
        case "TOTAL": return 13;
        case "LOADOUTS": return 14;
        case "ATTACKS": return 15;
        case "TAG TEAM": return 16;
        case "REMIX": return 17;
        case "ONLINE": return 18;
        case "PLAYERS": return 19;
        case "ROOM": return 20;
        case "SETTINGS": return 21;
        case "KEYBINDS": return 22;
        case "SOULS": return 23;
        case "MY SOUL": return 24;
        case "VIEW": return 25;
        case "BOTS": return 26;
        case "BOT": return 27;
        case "INVITE": return 28;
        // DRBR: the skin page, the boss list
        case "SKINS": return 29;
        case "BOSSES": return 30;
    }
    return 0;
}

// width in pixels (at 2x) of a hub caption label, to centre it
function knight_capw(_w)
{
    var _n = string_length(_w);
    var _px = 6 + 8;
    for (var _i = 1; _i <= _n; _i++)
        _px += ((string_char_at(_w, _i) == "I" || string_char_at(_w, _i) == "T" || string_char_at(_w, _i) == "J") ? 5 : 6) + ((_i < _n) ? 2 : 0);
    return _px * 2;
}

function knight_caption_hub(_w, _x, _y)
{
    knight_caption(spr_khub_captions, knight_capf(_w), _x, _y);
}

function knight_caption_center(_w, _cx, _y)
{
    knight_caption_hub(_w, _cx - (knight_capw(_w) / 2), _y);
}

function knight_char_hpcolor(_c)
{
    switch (_c)
    {
        case 1: return c_aqua;
        case 2: return c_fuchsia;
        case 3: return c_lime;
        case 4: return c_yellow;
    }
    if (knight_cc_ok(_c))
        return knight_cc(_c).color;
    return c_white;
}

function knight_char_head(_c)
{
    switch (_c)
    {
        case 1: return spr_headkris;
        case 2: return spr_headsusie;
        case 3: return spr_headralsei;
        case 4: return spr_headnoelle;
    }
    if (knight_cc_ok(_c) && knight_cc_spr(knight_cc(_c).head))
        return knight_cc(_c).head;
    return -1;
}

// build 50: a member's head in a menu. A custom character's head can be another size (Flowery's is a 40x40 picture, the others
// 32x24): its registry's menu shift puts it centred where the others' are (Flowery: 4 left, 8 up)
function knight_head_draw(_c, _x, _y)
{
    var _hs = knight_char_head(_c);
    if (_hs < 0)
        return 0;
    var _d = knight_cc(_c);
    if (!is_undefined(_d))
        draw_sprite(_hs, 0, _x + _d.menu_dx, _y + _d.menu_dy);
    else
        draw_sprite(_hs, 0, _x, _y);
    return 1;
}

function knight_char_bname(_c)
{
    switch (_c)
    {
        case 1: return spr_bnamekris;
        case 2: return spr_bnamesusie;
        case 3: return spr_bnameralsei;
        case 4: return spr_bnamenoelle;
    }
    if (knight_cc_ok(_c) && knight_cc_spr(knight_cc(_c).bname))
        return knight_cc(_c).bname;
    return -1;
}

function knight_char_proper(_c)
{
    switch (_c)
    {
        case 1: return "Kris";
        case 2: return "Susie";
        case 3: return "Ralsei";
        case 4: return "Noelle";
        default: if (knight_cc_ok(_c)) return knight_cc(_c).name; break;
    }
    return "- - -";
}

// ================= main entry =================
function knight_ui_draw()
{
    var _u = global.knight_ui;
    var xx = knight_cam_x();
    var yy = knight_cam_y();
    draw_set_alpha(1);
    draw_set_halign(fa_left);
    draw_set_valign(fa_top);
    var _a = clamp(_u.tp / 80, 0, 1);
    knight_ui_draw_panel(xx, yy, _u.bp);
    knight_ui_draw_topbar(xx, yy, _u);
    if (_a > 0)
    {
        draw_set_alpha(_a);
        draw_set_color(c_black);
        draw_rectangle(xx + 60, yy + 90, xx + 580, yy + 410, false);
        draw_set_alpha(1);
        if (_a >= 1)
        {
            scr_darkbox(xx + 50, yy + 80, xx + 590, yy + 420);
            if (_u.sub == "presets")
                knight_ui_draw_presets(xx, yy);
            else if (_u.sub == "loadouts")
                knight_ui_draw_loadouts(xx, yy);
            else if (_u.sub == "records")
                knight_ui_draw_records(xx, yy);
            else if (_u.sub == "credits")
                knight_ui_draw_credits(xx, yy);
            else if (_u.sub == "tag")
                knight_ui_draw_tag(xx, yy);
            else if (_u.sub == "remix")
                knight_ui_draw_remix(xx, yy);
            else if (_u.sub == "attacks")
                knight_ui_draw_attacks(xx, yy);
            else if (kfo_ui_is_sub(_u.sub))
                kfo_ui_draw(xx, yy);
            else
            {
                switch (_u.tab)
                {
                    case 0: knight_ui_draw_knight(xx, yy); break;
                    case 1: knight_ui_draw_party(xx, yy); break;
                    case 2: knight_ui_draw_power(xx, yy); break;
                    case 3: knight_ui_draw_rules(xx, yy); break;
                    case 4: knight_ui_draw_config(xx, yy); break;
                }
            }
        }
    }
    // build 49: the build stamp (which data.win this is), bottom right under the page
    if (_a >= 1)
    {
        draw_set_font(fnt_small);
        draw_set_halign(fa_right);
        draw_set_color(c_ltgray);
        draw_text(xx + 636, yy + 466, knight_build_stamp());
        draw_set_halign(fa_left);
    }
    if (is_struct(_u.modal))
        knight_ui_draw_modal(xx, yy);
    else if (_u.notice != "" && _a >= 1)
        knight_modal_draw("NOTICE", [_u.notice], [{ t: "OK", a: "" }], 0, "");
    if (_u.go == 1)
    {
        draw_set_color(c_white);
        draw_set_alpha(min(1, _u.gotimer / 14));
        draw_rectangle(xx - 10, yy - 10, xx + 650, yy + 490, false);
        draw_set_alpha(1);
    }
    draw_set_color(c_white);
}

// ---------------- top bar: tab buttons, or the description of what is highlighted ----------------
function knight_ui_draw_topbar(xx, yy, _u)
{
    var _tp = _u.tp;
    draw_set_color(c_black);
    draw_rectangle(xx - 10, yy - 10, xx + 650, yy + _tp, false);
    if (_tp <= 0)
        return 0;
    var _by = yy + _tp - 60;
    var _inside = (_u.focus == 1 || _u.sub != "");
    if (_u.warntimer > 0)
    {
        draw_set_color(_u.warnok ? c_yellow : make_color_rgb(255, 96, 96));
        knight_para(xx + 20, _by - 10, _u.warn, 600, 2);
        draw_set_color(c_white);
        return 0;
    }
    if (_inside)
    {
        draw_set_color(c_white);
        knight_para(xx + 20, _by - 10, knight_ui_desc(), 600, 2);
        return 0;
    }
    var _btn = [spr_khub_bt_knight, spr_khub_bt_party, spr_darktechbt, spr_khub_bt_rules, spr_darkconfigbt];
    for (var _i = 0; _i < 5; _i++)
    {
        var _f = 1;
        if (_i == _u.tab)
            _f = is_struct(_u.modal) ? 2 : 0;
        draw_sprite_ext(_btn[_i], _f, xx + 120 + (_i * 100), _by, 2, 2, 0, c_white, 1);
    }
    var _cs = (_u.tab == 2 || _u.tab == 4) ? spr_darkmenudesc : spr_khub_menudesc;
    var _cf = [0, 1, 3, 2, 4];
    draw_sprite_ext(_cs, _cf[_u.tab], xx + 20, _by + 4, 2, 2, 0, c_white, 1);
}

// ---------------- party panel (the game's own battle / menu charbox) ----------------
function knight_ui_panel_sel()
{
    var _u = global.knight_ui;
    if (!is_struct(_u) || _u.sub != "" || _u.focus != 1)
        return -1;
    if (_u.tab == 1)
        return _u.pslot;
    if (_u.tab == 2)
        return _u.sslot;
    return -1;
}

function knight_ui_draw_panel(xx, yy, _bp)
{
    if (_bp <= 0)
        return 0;
    draw_set_color(c_black);
    draw_rectangle(xx - 10, (yy + 480) - _bp - 1, xx + 650, yy + 500, false);
    var _p = global.knight_cfg.party;
    var _n = knight_party_size(_p);
    if (_n == 0)
    {
        draw_set_color(c_gray);
        draw_set_halign(fa_center);
        knight_txt(xx + 320, (yy + 480) - _bp + 16, "NO PARTY");
        draw_set_halign(fa_left);
        return 0;
    }
    var _xs = (_n >= 3) ? [0, 213, 426] : ((_n == 2) ? [108, 322] : [213]);
    var _sel = knight_ui_panel_sel();
    var _bcol = merge_color(merge_color(c_purple, c_black, 0.7), c_dkgray, 0.5);
    var _top = (yy + 480) - _bp;
    var _by = _top + 10;
    for (var _i = 0; _i < _n; _i++)
    {
        var _cv = _p[_i];
        var _c = knight_ch_real(_cv);
        var _x = xx + _xs[_i];
        draw_set_color((_sel == _i) ? knight_char_hpcolor(_c) : _bcol);
        draw_rectangle(_x, _top - 3, _x + 212, _top - 2, false);
        draw_set_color(c_black);
        draw_rectangle(_x + 2, _top - 1, _x + 210, _top + 60, false);
        draw_sprite(knight_char_head(_cv), 0, _x + 13, _by + (knight_cc_ok(_cv) ? knight_cc(_cv).head_dy : 0));
        draw_sprite(knight_char_bname(_cv), 0, _x + 51, _by + 3);
        draw_sprite(spr_hpname, 0, _x + 109, _by + 11);
        var _hp = global.hp[_c];
        var _mx = max(1, global.maxhp[_c]);
        draw_set_color(c_white);
        if ((_hp / _mx) <= 0.25)
            draw_set_color(c_yellow);
        if (_hp <= 0)
            draw_set_color(c_red);
        draw_set_font(global.hpfont);
        draw_set_halign(fa_right);
        draw_text(_x + 160, _by - 2, string(_hp));
        draw_sprite(spr_hpslash, 0, _x + 159, _by - 4);
        draw_text(_x + 205, _by - 2, string(global.maxhp[_c]));
        draw_set_halign(fa_left);
        draw_set_color(c_maroon);
        draw_rectangle(_x + 128, _by + 11, _x + 203, _by + 19, false);
        if (_hp > 0)
        {
            draw_set_color(knight_char_hpcolor(_c));
            draw_rectangle(_x + 128, _by + 11, _x + 128 + ceil(clamp(_hp / _mx, 0, 1) * 75), _by + 19, false);
        }
    }
    draw_set_color(c_white);
}

// ---------------- KNIGHT tab ----------------
function knight_ui_portrait(_k)
{
    var _n = knight_reg(_k).portrait;
    if (_n == "")
        return -1;
    var _s = asset_get_index(_n);
    if (_s < 0 || !sprite_exists(_s))
        return -1;
    return _s;
}

// build 52: the KNIGHT page as a carousel - one knight at a time in the middle (< > to turn), its card under its name;
// the MODE strip under it (KNIGHT RUSH, RANDOM, TAG TEAM, ATTACK REMIX - ways to fight, not knights) and ONLINE, apart
function knight_ui_draw_knight(xx, yy)
{
    var _u = global.knight_ui;
    var _f = knight_ui_fights();
    var _n = array_length(_f);
    var _nk = knight_ui_nknights(_f);
    knight_caption_hub((knight_page_count() > 1) ? ("< " + knight_page_title(_u.kpage) + " >") : "KNIGHTS", xx + 112, yy + 84);
    var _sel = clamp(_u.krow, 0, _n - 1);
    var _sf = _f[_sel];
    if (_u.focus == 0)
    {
        for (var _i = 0; _i < _n; _i++)
        {
            if (knight_ui_fight_is_current(_f[_i]))
                _sf = _f[_i];
        }
    }
    var _onk = (_sf.kind == "k" || _sf.kind == "soon");
    // the card, centred in the whole box
    knight_ui_draw_card(xx - 123, yy - 6, _sf);
    // < > beside the name while the carousel has the cursor; where it is among the knights
    if (_u.focus == 1 && _onk && _nk > 1)
    {
        knight_ui_side_arrows(xx, yy + 98, _u.siner);
        var _ki = 0;
        for (var _i = 0; _i < _nk; _i++)
        {
            if (_f[_i] == _sf)
                _ki = _i;
        }
        for (var _i = 0; _i < _nk; _i++)
        {
            var _px = xx + 320 - ((_nk - 1) * 7) + (_i * 14);
            draw_set_color((_i == _ki) ? c_yellow : c_dkgray);
            draw_rectangle(_px - 2, yy + 348, _px + 2, yy + 352, false);
        }
    }
    // the MODE strip
    var _y = yy + 366;
    draw_set_color(c_white);
    draw_rectangle(xx + 70, _y - 6, xx + 570, _y - 5, false);
    var _cx = xx + 76;
    scr_84_set_draw_font("main");
    for (var _i = _nk; _i < _n; _i++)
    {
        var _lab = knight_ui_fight_label(_f[_i]);
        var _w = string_width(_lab);
        var _hot = (_u.focus == 1 && _sel == _i);
        var _cur = knight_ui_fight_is_current(_f[_i]);
        if (_f[_i].kind == "online")
            _cx = max(_cx + 10, xx + 564 - _w - (_hot ? 18 : 0));
        if (_hot)
            knight_heart(_cx - 2, _y + 6);
        var _tx = _cx + (_hot ? 18 : 0);
        draw_set_color(_hot ? c_yellow : ((_f[_i].kind == "online") ? make_color_rgb(120, 200, 255) : (_cur ? c_orange : c_white)));
        draw_text(_tx, _y, _lab);
        _cx = _tx + _w + 16;
    }
    draw_set_font(fnt_small);
    if (_u.focus == 1)
    {
        draw_set_halign(fa_center);
        draw_set_color(c_gray);
        knight_txt_small(xx + 320, yy + 392, _onk ? "< >: KNIGHT   DOWN: MODES   Z: FIGHT   C: START" : "< >: MODE   UP: KNIGHTS   Z: OPEN");
        draw_set_halign(fa_left);
    }
}

function knight_ui_draw_card(xx, yy, _f)
{
    var _cx = xx + 443;
    var _x = xx + 320;
    var _w = 250;
    if (_f.kind == "online")
    {
        kfo_ui_card(xx, yy);
        return 0;
    }
    if (_f.kind == "soon")
    {
        // build 50: a boss planned for this chapter's page
        var _pl = global.knight_planned[_f.p];
        draw_set_halign(fa_center);
        draw_set_color(c_gray);
        knight_txt(_cx, yy + 110, string_upper(_pl.name));
        draw_set_color(c_yellow);
        knight_txt(_cx, yy + 160, "COMING SOON");
        draw_set_color(c_gray);
        knight_para_small(_cx, yy + 210, "Planned for the hub: not in it yet.#It will be on this page, in RANDOM#and KNIGHT RUSH" + (_pl.online ? ", and online." : "."), 240, 2);
        draw_set_halign(fa_left);
        return 0;
    }
    draw_set_halign(fa_center);
    if (_f.kind == "rush")
    {
        draw_set_color(c_yellow);
        knight_txt(_cx, yy + 110, "KNIGHT RUSH");
        var _l = knight_rush_list();
        var _c = global.knight_cfg;
        draw_set_color(c_white);
        for (var _i = 0; _i < array_length(_l); _i++)
            knight_txt(_cx, yy + 150 + (_i * 30), _c.rush_shuffle ? "???" : knight_reg(_l[_i]).short);
        draw_set_color(c_gray);
        var _hv = "FULL";
        if (_c.rush_heal == 1)
            _hv = string(_c.rush_pct) + "%";
        if (_c.rush_heal == 2)
            _hv = "NONE";
        knight_txt(_cx, yy + 304, "HEALING: " + _hv);
        var _rec = knight_rec_get("rush", "rush");
        if (!is_undefined(_rec) && _rec.win > 0)
        {
            draw_set_color(c_yellow);
            knight_txt(_cx, yy + 340, "BEST " + knight_time_text(_rec.best));
        }
        else if (!is_undefined(_rec) && _rec.far > 0)
        {
            draw_set_color(c_ltgray);
            knight_txt(_cx, yy + 340, "FURTHEST " + string(_rec.far) + "/" + string(array_length(_l)));
        }
        draw_set_halign(fa_left);
        return 0;
    }
    if (_f.kind == "tag")
    {
        var _c2 = global.knight_cfg;
        draw_set_color(c_yellow);
        knight_txt(_cx, yy + 110, "TAG TEAM");
        knight_ui_tag_pair(_cx, yy + 150, _c2.knight, _c2.knight2, global.knight_ui.siner);
        draw_set_color(c_gray);
        knight_txt(_cx, yy + 304, "TAKING TURNS,");
        knight_txt(_cx, yy + 334, "BEAT BOTH");
        knight_ui_mode_best("tag", _cx, yy + 362);
        draw_set_halign(fa_left);
        return 0;
    }
    if (_f.kind == "remix")
    {
        draw_set_color(c_yellow);
        knight_txt(_cx, yy + 110, "ATTACK REMIX");
        var _rl = knight_ui_remix_rows();
        for (var _i = 0; _i < array_length(_rl); _i++)
        {
            var _on = knight_remix_on(global.knight_cfg, _rl[_i]);
            draw_set_color(_on ? knight_reg(_rl[_i]).color : c_dkgray);
            knight_txt_small(_cx, yy + 148 + (_i * 20), knight_reg(_rl[_i]).short + (_on ? "" : " (OFF)"));
        }
        draw_set_color(c_gray);
        knight_txt(_cx, yy + 280, "A RANDOM ATTACK");
        knight_txt(_cx, yy + 310, "EVERY TURN");
        knight_ui_mode_best("remix", _cx, yy + 350);
        draw_set_halign(fa_left);
        return 0;
    }
    if (_f.kind == "random")
    {
        draw_set_color(c_yellow);
        knight_txt(_cx, yy + 110, "RANDOM KNIGHT");
        draw_set_color(c_white);
        scr_84_set_draw_font("mainbig");
        draw_text_transformed(_cx, yy + 160, "?", 4, 4, 0);
        draw_set_color(c_gray);
        knight_txt(_cx, yy + 296, "ANY KNIGHT THAT");
        knight_txt(_cx, yy + 326, "FITS YOUR SETUP");
        draw_set_halign(fa_left);
        return 0;
    }
    var _k = _f.k;
    var _r = knight_reg(_k);
    draw_set_color(_r.color);
    var _tl = knight_wrap(_r.title, _w);
    var _ty = yy + 106;
    for (var _i = 0; _i < min(2, array_length(_tl)); _i++)
        knight_txt(_cx, _ty + (_i * 28), _tl[_i]);
    var _py = _ty + (min(2, array_length(_tl)) * 28) + 8;
    var _spr = knight_ui_portrait(_k);
    if (_spr >= 0)
    {
        // the knight battle sprites are drawn at 2x; their art sits in the box (24, 31)-(92, 96) of the frame
        var _fr = (global.knight_ui.siner / 8) mod max(1, sprite_get_number(_spr));
        draw_sprite_ext(_spr, _fr, _cx - (58 * 2) + (sprite_get_xoffset(_spr) * 2), _py - (31 * 2) + (sprite_get_yoffset(_spr) * 2), 2, 2, 0, _r.tint ? _r.color : c_white, 1);
        _py += 138;
    }
    draw_set_color(c_ltgray);
    var _al = knight_wrap("BY " + _r.author, _w);
    for (var _i = 0; _i < min(2, array_length(_al)); _i++)
    {
        knight_txt(_cx, _py, _al[_i]);
        _py += 28;
    }
    if (_r.joke)
    {
        draw_set_color(c_orange);
        knight_txt(_cx, _py, "JOKE FIGHT");
    }
    else
    {
        var _best = -1;
        var _wins = 0;
        var _cats = knight_rec_cats(_r.key);
        for (var _c = 0; _c < array_length(_cats); _c++)
        {
            var _rc = knight_rec_get(_r.key, _cats[_c]);
            if (is_undefined(_rc) || _cats[_c] == "pr")
                continue;
            _wins += _rc.win;
            if (_rc.best > 0 && (_best < 0 || _rc.best < _best))
                _best = _rc.best;
        }
        if (_best > 0)
        {
            draw_set_color(c_yellow);
            knight_txt(_cx, _py, "BEST " + knight_time_text(_best));
        }
        else
        {
            draw_set_color(c_gray);
            knight_txt(_cx, _py, "NOT CLEARED YET");
        }
    }
    draw_set_halign(fa_left);
}

// ---------------- PARTY tab (laid out like the EQUIP menu) ----------------
function knight_ui_draw_chars(xx, yy, _sel, _harrows, _siner, _nx, _ny)
{
    var _p = global.knight_cfg.party;
    for (var _i = 0; _i < 3; _i++)
        knight_cc_eqchar(_p[_i], 90 + xx + (_i * 50), 160 + yy, (_i == _sel) ? 1 : 0.4);
    if (_harrows)
        draw_sprite(spr_heart_harrows, _siner / 20, 100 + xx + (_sel * 50), 142 + yy);
    draw_set_color(c_white);
    knight_txt(xx + _nx, yy + _ny, knight_char_proper(_p[_sel]));
}

function knight_ui_draw_stats(xx, yy, _ch, _x0, _y0, _vx, _preview)
{
    var _lab = ["Attack:", "Defense:", "Magic:"];
    var _ic = [1, 4, 5];
    for (var _k = 0; _k < 3; _k++)
    {
        var _y = yy + _y0 + (_k * 25);
        draw_set_color(c_white);
        knight_txt(xx + _x0 + 26, _y, _lab[_k]);
        draw_item_icon(xx + _x0, _y + 6, _ic[_k]);
        if (_ch > 0)
        {
            var _v = knight_stat_sum(_ch, _k);
            knight_txt(xx + _vx, _y, string(_v));
            if (is_array(_preview))
            {
                var _nv = _preview[_k];
                if (_nv != _v)
                {
                    draw_set_color((_nv > _v) ? c_yellow : c_red);
                    knight_txt(xx + _vx + 36, _y, ">" + string(_nv));
                }
            }
        }
    }
}

// stats a member would have with item _id in equipment slot _k
function knight_stat_preview(_ch, _k, _id)
{
    var _old = knight_equip_get(_ch, _k);
    knight_equip_set(_ch, _k, _id);
    knight_equip_refresh();
    var _r = [knight_stat_sum(_ch, 0), knight_stat_sum(_ch, 1), knight_stat_sum(_ch, 2)];
    knight_equip_set(_ch, _k, _old);
    knight_equip_refresh();
    return _r;
}

function knight_ui_draw_party(xx, yy)
{
    var _u = global.knight_ui;
    var _c = global.knight_cfg;
    var _ch = knight_ch_real(_c.party[_u.pslot]);
    draw_set_color(c_white);
    draw_rectangle(xx + 270, yy + 91, xx + 275, yy + 226, false);
    draw_rectangle(xx + 59, yy + 221, xx + 580, yy + 226, false);
    draw_rectangle(xx + 323, yy + 221, xx + 328, yy + 411, false);
    knight_caption(spr_dmenu_captions, 0, xx + 118, yy + 86);
    knight_caption(spr_dmenu_captions, 1, xx + 376, yy + 86);
    knight_caption(spr_dmenu_captions, 4, xx + 116, yy + 216);
    var _onbody = (_u.focus == 1);
    knight_ui_draw_chars(xx, yy, _u.pslot, _onbody && _u.lv == 0, _u.siner, 135, 107);
    // equipment slots (top right)
    for (var _k = 0; _k < 3; _k++)
    {
        var _y = yy + 107 + (_k * 30);
        var _hot = (_onbody && _u.lv >= 1 && _u.prow == _k);
        if (_hot && _u.lv == 1)
            knight_heart(xx + 308, _y + 15);
        else
        {
            var _ic = (_k == 0) ? ((_ch == 4) ? 5 : max(0, _ch - 1)) : (_k + 2);
            draw_sprite_ext(spr_dmenu_equip, _ic, xx + 302, _y + 1, 2, 2, 0, c_white, (_ch > 0) ? 1 : 0.3);
        }
        if (_ch > 0)
        {
            var _inf = knight_equip_info(_k, knight_equip_get(_ch, _k), _ch);
            draw_set_color(_hot ? c_yellow : c_white);
            knight_txt(xx + 340, _y, knight_fit(_inf.name, 230));
        }
    }
    // the list (bottom right): items for the highlighted slot
    var _prev = undefined;
    if (_ch > 0)
    {
        var _row = (_u.lv >= 1) ? _u.prow : 0;
        knight_caption(spr_dmenu_captions, (_row == 0) ? 3 : 2, xx + 372, yy + 216);
        var _l = knight_ui_pick_list(_ch, _row);
        var _m = array_length(_l);
        var _s0 = (_u.lv == 2) ? _u.pscroll : 0;
        for (var _v = 0; _v < 6; _v++)
        {
            var _i = _s0 + _v;
            if (_i >= _m)
                break;
            var _y = yy + 230 + (_v * 27);
            var _inf2 = knight_equip_info(_row, _l[_i], _ch);
            var _hot2 = (_u.lv == 2 && _u.ppick == _i);
            var _worn = (_l[_i] == knight_equip_get(_ch, _row));
            draw_set_color(_hot2 ? c_yellow : (_worn ? c_ltgray : c_white));
            knight_txt(xx + 370, _y, knight_fit((_l[_i] == 0) ? "(nothing)" : _inf2.name, 200));
            if (_hot2)
            {
                knight_heart(xx + 344, _y + 10);
                _prev = knight_stat_preview(_ch, _row, _l[_i]);
            }
        }
        if (_u.lv == 2)
            knight_ui_arrows(xx + 556, yy + 236, yy + 384, _s0 > 0, _s0 + 6 < _m, _u.siner);
    }
    else
    {
        draw_set_color(c_gray);
        knight_txt(xx + 350, yy + 240, "EMPTY SLOT");
        knight_txt_small(xx + 350, yy + 276, "UP / DOWN ON THE CHAR ROW");
        knight_txt_small(xx + 350, yy + 294, "PUTS SOMEONE HERE.");
    }
    knight_ui_draw_stats(xx, yy, _ch, 74, 230, 224, _prev);
}

// ---------------- POWER tab (laid out like the POWER menu) ----------------
function knight_ui_draw_power(xx, yy)
{
    var _u = global.knight_ui;
    var _c = global.knight_cfg;
    var _chv = _c.party[_u.sslot];
    var _ch = knight_ch_real(_chv);
    var _spl = knight_cc_ok(_chv) ? knight_cc_spl(_chv) : ((_ch > 0) ? global.spell[_ch] : []);
    draw_set_color(c_white);
    draw_rectangle(xx + 60, yy + 216, xx + 580, yy + 221, false);
    draw_rectangle(xx + 294, yy + 220, xx + 299, yy + 411, false);
    knight_caption(spr_dmenu_captions, 0, xx + 124, yy + 84);
    knight_caption(spr_dmenu_captions, 4, xx + 124, yy + 210);
    knight_caption(spr_dmenu_captions, 5, xx + 380, yy + 210);
    draw_sprite_ext(spr_dmenu_captions, 6, xx + 340, yy + 225, 1, 1, 0, c_white, 1);
    var _onbody = (_u.focus == 1);
    knight_ui_draw_chars(xx, yy, _u.sslot, _onbody && _u.lv == 0, _u.siner, 130, 105);
    knight_ui_draw_stats(xx, yy, _ch, 74, 230, 230, undefined);
    // spells (bottom right)
    var _hy = -1;
    for (var _s = 0; _s < 6; _s++)
    {
        var _si = _u.sscroll + _s;
        var _y = yy + 230 + (_s * 25);
        var _id = (_ch > 0) ? _spl[_si] : 0;
        var _hot = (_onbody && _u.lv == 1 && _u.srow == _si);
        if (_id > 0)
        {
            scr_spellinfo(_id);
            draw_set_color(_hot ? c_yellow : c_white);
            knight_txt(xx + 340, _y, string(round((cost / global.maxtension) * 100)) + "%");
            knight_txt(xx + 410, _y, knight_fit(knight_spell_label(spellname), 160));
        }
        else
        {
            draw_set_color(_hot ? c_yellow : c_dkgray);
            knight_txt(xx + 410, _y, "- - -");
        }
        if (_hot)
            knight_heart(xx + 313, _y + 10);
    }
    if (_ch > 0)
        knight_ui_arrows(xx + 565, yy + 228, yy + 382, _u.sscroll > 0, _u.sscroll < 6, _u.siner);
    // highlighted spell (top right)
    var _sp = 0;
    if (_ch > 0 && _onbody && _u.lv == 1)
        _sp = _spl[_u.srow];
    if (_sp > 0)
    {
        scr_spellinfo(_sp);
        draw_set_color(c_yellow);
        knight_txt(xx + 320, yy + 105, knight_fit(knight_spell_label(spellname), 250));
        draw_set_color(c_white);
        knight_txt(xx + 320, yy + 137, string(round((cost / global.maxtension) * 100)) + "% TP");
        var _need = knight_spell_need(_sp, _ch);
        if (_need != "")
        {
            draw_set_color(c_ltgray);
            knight_txt(xx + 320, yy + 169, _need);
        }
    }
    else if (_ch > 0)
    {
        var _cnt = 0;
        for (var _i = 0; _i < 12; _i++)
        {
            if (_spl[_i] > 0)
                _cnt++;
        }
        draw_set_color(c_white);
        knight_txt(xx + 320, yy + 105, "SPELLS " + string(_cnt) + "/12");
        draw_set_color(c_gray);
        knight_txt_small(xx + 320, yy + 141, "Z: EDIT THIS LIST");
        knight_txt_small(xx + 320, yy + 159, "IN THE LIST  < >: CHANGE A SPELL");
        knight_txt_small(xx + 320, yy + 177, "IN THE LIST  Z: EMPTY THE SLOT");
    }
    else
    {
        draw_set_color(c_gray);
        knight_txt(xx + 320, yy + 105, "EMPTY SLOT");
    }
}

// who a spell needs, for the POWER page
function knight_spell_need(_sp, _ch)
{
    switch (_sp)
    {
        case 5: return "NEEDS SUSIE";
        case 6: return (_ch == 1) ? "NEEDS RALSEI" : "RALSEI + NOELLE";
        case 12: return "NEEDS NOELLE";
        case 14: return "NEEDS RALSEI";
        case 15: return "RALSEI + NOELLE";
        case 7: return (_ch == 1) ? "KRIS'S ACT LIST" : "";
    }
    return "";
}

// ---------------- RULES tab ----------------
function knight_ui_draw_rules(xx, yy)
{
    var _u = global.knight_ui;
    var _ids = knight_ui_rule_ids();
    draw_set_color(c_white);
    draw_rectangle(xx + 312, yy + 91, xx + 317, yy + 410, false);
    knight_caption_center("RULES", xx + 314, yy + 84);
    for (var _i = 0; _i < 16; _i++)
    {
        var _col = _i div 8;
        var _ln = _i mod 8;
        var _x = xx + ((_col == 0) ? 88 : 348);
        var _vx = xx + ((_col == 0) ? 300 : 572);
        var _y = yy + 108 + (_ln * 36);
        var _id = _ids[_i];
        var _on = variable_struct_get(global.knight_cfg, _id);
        var _blk = (knight_ui_block(_id) != "");
        var _hot = (_u.focus == 1 && _u.rrow == _i);
        draw_set_color(_blk ? c_dkgray : (_hot ? c_white : c_ltgray));
        if (_on)
            draw_set_color(c_white);
        knight_txt(_x, _y, knight_ui_rule_label(_id));
        draw_set_halign(fa_right);
        draw_set_color(_on ? c_yellow : (_blk ? c_dkgray : c_gray));
        knight_txt(_vx, _y, _on ? "ON" : (_blk ? "--" : "OFF"));
        draw_set_halign(fa_left);
        if (_hot)
            knight_heart(_x - 25, _y + 10);
    }
}

// ---------------- CONFIG tab ----------------
function knight_ui_draw_config(xx, yy)
{
    var _u = global.knight_ui;
    var _ids = knight_ui_cfg_ids();
    knight_caption_center("OPTIONS", xx + 320, yy + 84);
    // build 49: 14 rows (RESET MOD SETTINGS): 13 shown, the list scrolls with the heart
    var _shown = min(13, array_length(_ids));
    var _first = (_u.focus == 1) ? clamp(_u.crow - (_shown - 1), 0, array_length(_ids) - _shown) : 0;
    if (_first > 0)
    {
        draw_set_color(c_gray);
        knight_txt_small(xx + 88, yy + 92, "^");
    }
    if (_first + _shown < array_length(_ids))
    {
        draw_set_color(c_gray);
        knight_txt_small(xx + 88, yy + 392, "v");
    }
    for (var _i = _first; _i < _first + _shown; _i++)
    {
        var _id = _ids[_i];
        var _y = yy + ((_shown > 12) ? 100 : 104) + ((_i - _first) * ((_shown > 12) ? 23 : ((_shown > 11) ? 25 : 27)));
        var _blk = (knight_ui_block(_id) != "");
        var _hot = (_u.focus == 1 && _u.crow == _i);
        draw_set_color(_blk ? c_dkgray : c_white);
        knight_txt(xx + 110, _y, knight_ui_cfg_label(_id));
        var _v = knight_ui_cfg_value(_id);
        if (_v != "")
        {
            draw_set_halign(fa_right);
            var _col = c_white;
            if (_v == "ON")
                _col = c_yellow;
            if (_v == "OFF")
                _col = c_gray;
            if (_blk)
                _col = c_dkgray;
            if (_id == "song" && !knight_music_exists(knight_ui_song_file()))
                _col = make_color_rgb(255, 96, 96);
            draw_set_color(_col);
            knight_txt(xx + 556, _y, knight_fit(_v, 240));
            draw_set_halign(fa_left);
            if (_id == "song" && knight_preview_playing())
            {
                draw_set_color(c_yellow);
                knight_txt_small(xx + 300, _y + 8, "PLAYING");
            }
        }
        if (_hot)
            knight_heart(xx + 85, _y + 10);
    }
}

// ---------------- PRESETS ----------------
function knight_ui_draw_presets(xx, yy)
{
    var _u = global.knight_ui;
    draw_set_color(c_white);
    draw_rectangle(xx + 300, yy + 91, xx + 305, yy + 410, false);
    knight_caption_hub("PRESETS", xx + 100, yy + 84);
    knight_caption_hub("DETAILS", xx + 380, yy + 84);
    for (var _i = 0; _i < knight_preset_slots(); _i++)
    {
        var _y = yy + 110 + (_i * 36);
        var _p = global.knight_presets[_i];
        var _hot = (_u.subrow == _i);
        draw_set_color(_hot ? c_yellow : (is_undefined(_p) ? c_gray : c_white));
        knight_txt(xx + 100, _y, string(_i + 1) + " " + knight_fit(knight_ui_preset_label(_i), 168));
        if (_hot)
            knight_heart(xx + 75, _y + 10);
    }
    var _d = knight_ui_preset_detail(_u.subrow);
    var _yy = yy + 110;
    for (var _i = 0; _i < array_length(_d); _i++)
    {
        draw_set_color((_i == 0) ? c_yellow : c_white);
        var _l = knight_wrap(_d[_i], 250);
        for (var _j = 0; _j < array_length(_l); _j++)
        {
            if (_yy > yy + 370)
                break;
            knight_txt(xx + 320, _yy, _l[_j]);
            _yy += 30;
        }
    }
    if (global.knight_save_fail)
    {
        draw_set_color(make_color_rgb(255, 96, 96));
        knight_txt_small(xx + 320, yy + 384, "THE LAST SAVE FAILED!");
    }
}

// ---------------- LOADOUTS ----------------
function knight_ui_lr_arrows(_xl, _xr, _y, _siner)
{
    var _o = sin(_siner / 12) * 3;
    draw_sprite_ext(spr_morearrow, 0, _xl - _o, _y + 8, 1, 1, -90, c_white, 1);
    draw_sprite_ext(spr_morearrow, 0, _xr + _o, _y + 21, 1, 1, 90, c_white, 1);
}

function knight_ui_draw_loadouts(xx, yy)
{
    var _u = global.knight_ui;
    draw_set_color(c_white);
    draw_rectangle(xx + 300, yy + 91, xx + 305, yy + 410, false);
    knight_caption_center("LOADOUTS", xx + 180, yy + 84);
    knight_caption_center("DETAILS", xx + 442, yy + 84);
    // party group with its arrows, then who is in it
    var _g = _u.lo_g;
    draw_set_halign(fa_center);
    draw_set_color(c_yellow);
    knight_txt(xx + 180, yy + 106, knight_lo_group_label(_g));
    knight_ui_lr_arrows(xx + 88, xx + 272, yy + 106, _u.siner);
    if (knight_lo_is_clone(_g))
    {
        draw_set_color(c_gray);
        knight_txt_small(xx + 180, yy + 144, knight_lo_is_triple(_g) ? "THREE OF ONE MEMBER" : "TWO OF ONE MEMBER");
    }
    else
    {
        var _p = knight_lo_group_party(_g);
        var _n = knight_party_size(_p);
        var _hx = xx + 180 - ((_n * 44) / 2) + 6;
        for (var _i = 0; _i < _n; _i++)
            knight_head_draw(_p[_i], _hx + (_i * 44), yy + 140);
    }
    draw_set_halign(fa_left);
    // the loadouts of that group
    var _l = knight_lo_list(_g);
    for (var _i = 0; _i < array_length(_l); _i++)
    {
        var _y = yy + 182 + (_i * 36);
        var _hot = (_u.lo_i == _i);
        draw_set_color(_hot ? c_yellow : c_white);
        knight_txt(xx + 100, _y, knight_lo_label(_l[_i]));
        if (_hot)
            knight_heart(xx + 75, _y + 10);
    }
    draw_set_color(c_gray);
    knight_txt_small(xx + 80, yy + 388, "< > PARTY     Z LOAD");
    // details: each member's gear and spells
    var _lo = _l[clamp(_u.lo_i, 0, array_length(_l) - 1)];
    var _party = knight_lo_party(_g, _lo);
    var _yy = yy + 108;
    var _seen = [0, 0, 0, 0, 0, 0];
    for (var _i = 0; _i < 3; _i++)
    {
        var _c = _party[_i];
        if (_c < 1 || (_c > 4 && !knight_cc_ok(_c)) || _c >= array_length(_seen) || _seen[_c])
            continue;
        _seen[_c] = 1;
        var _gear = knight_lo_gear(_lo.kind, _c, _party);
        draw_set_color(c_white);
        knight_txt_small(xx + 320, _yy, string_upper(knight_char_proper(_c)));
        if (_gear[1] == 23 || _gear[2] == 23)
        {
            draw_set_color(c_yellow);
            knight_txt_small(xx + 400, _yy, "SHADOW MANTLE");
        }
        _yy += 16;
        draw_set_color(c_ltgray);
        _yy += knight_para_small(xx + 320, _yy, knight_lo_gear_names(_gear, _c), 252, 2);
        draw_set_color(c_gray);
        _yy += knight_para_small(xx + 320, _yy, knight_lo_spell_names(knight_lo_spells(_lo.kind, _c, _party)), 252, 3);
        _yy += 4;
    }
    if (_lo.kind == "triple" || _lo.kind == "double")
    {
        draw_set_color(c_gray);
        knight_para_small(xx + 320, _yy + 4, ((_lo.kind == "triple") ? "All three" : "Both") + " share one HP bar, one set of gear and one spell list.", 252, 2);
    }
}

// ---------------- TAG TEAM picker ----------------
// two knights side by side (portraits as on the KNIGHT page, a little smaller), FIRST and SECOND under them
function knight_ui_tag_pair(_cx, _y, _k1, _k2, _siner)
{
    var _ks = [_k1, _k2];
    for (var _i = 0; _i < 2; _i++)
    {
        var _x = _cx + ((_i == 0) ? -60 : 60);
        var _r = knight_reg(_ks[_i]);
        var _spr = knight_ui_portrait(_ks[_i]);
        if (_spr >= 0)
        {
            var _fr = (_siner / 8) mod max(1, sprite_get_number(_spr));
            draw_sprite_ext(_spr, _fr, _x - (58 * 1.5) + (sprite_get_xoffset(_spr) * 1.5), _y - (31 * 1.5) + (sprite_get_yoffset(_spr) * 1.5), 1.5, 1.5, 0, _r.tint ? _r.color : c_white, 1);
        }
        draw_set_halign(fa_center);
        draw_set_color(_r.color);
        knight_txt_small(_x, _y + 104, _r.short);
        draw_set_color(c_gray);
        knight_txt_small(_x, _y + 120, (_i == 0) ? "FIRST" : "SECOND");
    }
}

function knight_ui_mode_best(_key, _cx, _y)
{
    var _best = -1;
    var _cats = knight_rec_cats(_key);
    for (var _c = 0; _c < array_length(_cats); _c++)
    {
        var _rc = knight_rec_get(_key, _cats[_c]);
        if (!is_undefined(_rc) && _rc.best > 0 && (_best < 0 || _rc.best < _best))
            _best = _rc.best;
    }
    draw_set_halign(fa_center);
    if (_best > 0)
    {
        draw_set_color(c_yellow);
        knight_txt(_cx, _y, "BEST " + knight_time_text(_best));
    }
}

function knight_ui_draw_tag(xx, yy)
{
    var _u = global.knight_ui;
    var _c = global.knight_cfg;
    draw_set_color(c_white);
    draw_rectangle(xx + 300, yy + 91, xx + 305, yy + 410, false);
    knight_caption_hub("KNIGHTS", xx + 112, yy + 84);
    knight_caption_center("TAG TEAM", xx + 443, yy + 84);
    var _n = knight_count();
    for (var _i = 0; _i <= _n; _i++)
    {
        var _y = yy + 110 + (_i * 36);
        var _hot = (_u.tag_row == _i);
        if (_i == _n)
        {
            _y += 10;
            draw_set_color(_hot ? c_yellow : c_white);
            knight_txt(xx + 100, _y, "START");
        }
        else
        {
            var _r = knight_reg(_i);
            draw_set_color(_hot ? c_yellow : (_r.joke ? c_ltgray : c_white));
            knight_txt(xx + 100, _y, _r.short);
            var _mk = "";
            if (_c.knight == _i)
                _mk = "1";
            if (_c.knight2 == _i)
                _mk += ((_mk == "") ? "" : "+") + "2";
            if (_mk != "")
            {
                draw_set_halign(fa_right);
                draw_set_color(c_yellow);
                knight_txt_small(xx + 294, _y + 8, _mk);
                draw_set_halign(fa_left);
            }
        }
        if (_hot)
            knight_heart(xx + 75, _y + 10);
    }
    knight_ui_tag_pair(xx + 443, yy + 162, _c.knight, _c.knight2, _u.siner);
    // which slot Z fills
    draw_set_halign(fa_center);
    draw_set_color(c_yellow);
    knight_txt_small(xx + 443 + ((_u.tag_slot == 0) ? -60 : 60), yy + 302, (_u.tag_row < _n) ? "< Z PUTS IT HERE >" : "");
    draw_set_color(c_gray);
    var _note = (knight_reg(_c.knight).joke || knight_reg(_c.knight2).joke) ? "A JOKE FIGHT IN THE TEAM: NOT RECORDED" : "EACH KEEPS ITS OWN HP AND ROARING";
    knight_para_small(xx + 443, yy + 332, _note, 240, 2);
    knight_txt_small(xx + 443, yy + 384, "C: START");
    draw_set_halign(fa_left);
}

// ---------------- ATTACK REMIX: which knights take part ----------------
function knight_ui_draw_remix(xx, yy)
{
    var _u = global.knight_ui;
    var _c = global.knight_cfg;
    draw_set_color(c_white);
    draw_rectangle(xx + 300, yy + 91, xx + 305, yy + 410, false);
    knight_caption_hub("KNIGHTS", xx + 112, yy + 84);
    knight_caption_center("REMIX", xx + 443, yy + 84);
    var _rows = knight_ui_remix_rows();
    var _n = array_length(_rows);
    for (var _i = 0; _i <= _n; _i++)
    {
        var _y = yy + 110 + (_i * 36);
        var _hot = (_u.rmx_row == _i);
        if (_i == _n)
        {
            _y += 10;
            draw_set_color(_hot ? c_yellow : c_white);
            knight_txt(xx + 100, _y, "START");
        }
        else
        {
            var _k = _rows[_i];
            var _on = knight_remix_on(_c, _k);
            draw_set_color(_hot ? c_yellow : (_on ? c_white : c_gray));
            knight_txt(xx + 100, _y, knight_reg(_k).short);
            draw_set_halign(fa_right);
            draw_set_color(_on ? c_yellow : c_gray);
            knight_txt_small(xx + 294, _y + 8, _on ? "ON" : "OFF");
            draw_set_halign(fa_left);
        }
        if (_hot)
            knight_heart(xx + 75, _y + 10);
    }
    // the knights in the battle, the finale knight marked
    draw_set_halign(fa_center);
    var _p = knight_remix_pool(_c);
    for (var _i = 0; _i < array_length(_p); _i++)
    {
        draw_set_color(knight_reg(_p[_i]).color);
        knight_txt_small(xx + 443, yy + 120 + (_i * 22), knight_reg(_p[_i]).name);
    }
    draw_set_color(c_gray);
    knight_para_small(xx + 443, yy + 252, "EVERY TURN ONE OF THEM WITH A RANDOM ATTACK. THE NORMAL KNIGHT OPENS THE BATTLE AND TAKES THE FINALE" + (knight_remix_on(_c, 0) ? "." : " (OFF FOR THE TURNS)."), 250, 4);
    knight_txt_small(xx + 443, yy + 384, "C: START");
    draw_set_halign(fa_left);
}

// ---------------- PRACTICE: the knight's attack list ----------------
function knight_ui_draw_attacks(xx, yy)
{
    var _u = global.knight_ui;
    var _c = global.knight_cfg;
    var _r = knight_reg(_c.knight);
    var _l = _r.atk;
    var _n = array_length(_l);
    knight_caption_center("ATTACKS", xx + 320, yy + 84);
    draw_set_halign(fa_center);
    draw_set_color(_r.color);
    knight_txt(xx + 320, yy + 102, _r.title);
    draw_set_color(c_yellow);
    knight_txt_small(xx + 320, yy + 132, knight_fit_small(knight_ui_practice_value(_c), 480));
    draw_set_halign(fa_left);
    for (var _v = 0; _v < 9; _v++)
    {
        var _i = _u.at_scroll + _v;
        if (_i >= _n)
            break;
        var _y = yy + 152 + (_v * 28);
        var _hot = (_u.at_row == _i);
        var _sel = (_c.p_atk == _i && knight_ui_practice_index(_c) >= 2);
        var _unused = (_l[_i][3] & 1);
        draw_set_color(_hot ? c_yellow : (_sel ? c_white : (_unused ? c_dkgray : c_ltgray)));
        knight_txt_small(xx + 110, _y + 6, (_l[_i][3] & 2) ? "FINALE" : ("PHASE " + string(_l[_i][0])));
        knight_txt(xx + 200, _y, knight_fit(_l[_i][2], 330));
        if (_sel)
        {
            draw_set_color(c_yellow);
            knight_txt_small(xx + 536, _y + 6, "<");
        }
        if (_hot)
            knight_heart(xx + 85, _y + 10);
    }
    knight_ui_arrows(xx + 556, yy + 150, yy + 400, _u.at_scroll > 0, _u.at_scroll + 9 < _n, _u.siner);
}

// ---------------- RECORDS ----------------
function knight_ui_draw_records(xx, yy)
{
    var _u = global.knight_ui;
    var _keys = knight_rec_keys();
    var _key = _keys[clamp(_u.rec_i, 0, array_length(_keys) - 1)];
    knight_caption_center("RECORDS", xx + 320, yy + 84);
    var _nm = knight_rec_title(_key);
    draw_set_halign(fa_center);
    draw_set_color(c_yellow);
    knight_txt(xx + 320, yy + 106, _nm);
    draw_set_color(c_white);
    knight_ui_side_arrows(xx, yy + 106, _u.siner);
    draw_set_halign(fa_left);
    if (_u.rec_def)
    {
        var _d = knight_rec_defs();
        for (var _i = 0; _i < array_length(_d); _i++)
        {
            var _y = yy + 146 + (_i * 30);
            if (_d[_i][0] != "")
            {
                draw_set_color(c_yellow);
                knight_txt(xx + 80, _y, _d[_i][0]);
                draw_set_color(c_white);
                knight_txt(xx + 216, _y, _d[_i][1]);
            }
            else
            {
                draw_set_color(c_gray);
                knight_para_small(xx + 80, _y + 10, _d[_i][1], 480, 3);
            }
        }
        return 0;
    }
    var _cx = [290, 410, 490, 560];
    var _hd = ["WINS", "BEST", "LOW DMG", "STREAK"];
    draw_set_color(c_gray);
    draw_set_halign(fa_right);
    for (var _i = 0; _i < 4; _i++)
        knight_txt_small(xx + _cx[_i], yy + 146, _hd[_i]);
    draw_set_halign(fa_left);
    var _cats = knight_rec_cats(_key);
    var _lab = (_key == "rush") ? ["RUSH", "NO-HIT"] : ["NORMAL", "RULES", "NO-HIT", "PRACTICE"];
    for (var _r = 0; _r < array_length(_cats); _r++)
    {
        var _rec = knight_rec_get(_key, _cats[_r]);
        var _y = yy + 166 + (_r * 56);
        draw_set_color(c_white);
        knight_txt(xx + 80, _y, _lab[_r]);
        var _vals = [string(_rec.win) + "/" + string(_rec.att), (_rec.best > 0) ? knight_time_text(_rec.best) : "--", (_rec.lowdmg >= 0) ? string(_rec.lowdmg) : "--", string(_rec.streak)];
        if (_cats[_r] == "pr")
            _vals = [string(_rec.att) + " TRIES", "", "", ""];
        draw_set_halign(fa_right);
        for (var _i = 0; _i < 4; _i++)
        {
            draw_set_color((_i == 1 && _rec.best > 0) ? c_yellow : c_white);
            knight_txt(xx + _cx[_i], _y, _vals[_i]);
        }
        draw_set_halign(fa_left);
        var _sub = "";
        if (_rec.win > 0 && _rec.cfg != "")
            _sub = "BEST WITH " + _rec.cfg;
        if (_rec.aband > 0)
            _sub += ((_sub == "") ? "" : "   ") + "LEFT " + string(_rec.aband);
        if (_key == "rush" && _rec.far > 0)
            _sub += ((_sub == "") ? "" : "   ") + "FURTHEST " + string(_rec.far) + "/" + string(array_length(knight_rush_list()));
        draw_set_color(c_gray);
        knight_txt_small(xx + 80, _y + 28, knight_fit_small(string_upper(_sub), 480));
    }
    if (global.knight_save_fail)
    {
        draw_set_color(make_color_rgb(255, 96, 96));
        knight_txt_small(xx + 80, yy + 392, "RECORDS COULD NOT BE SAVED ON THE LAST WRITE.");
    }
    else if (global.knight_store_status != "ok" && global.knight_store_status != "new")
    {
        draw_set_color(c_orange);
        knight_txt_small(xx + 80, yy + 392, knight_fit_small(string_upper(global.knight_store_status), 480));
    }
}

// ---------------- CREDITS ----------------
function knight_ui_draw_credits(xx, yy)
{
    var _u = global.knight_ui;
    var _i = clamp(_u.cr_i, 0, knight_credit_count() - 1);
    var _e = knight_credit_entry(_i);
    knight_caption_center("CREDITS", xx + 320, yy + 84);
    draw_set_halign(fa_center);
    draw_set_color(c_yellow);
    knight_txt(xx + 320, yy + 106, _e.title);
    draw_set_color(c_white);
    knight_ui_side_arrows(xx, yy + 106, _u.siner);
    var _l = knight_credit_lines(_i);
    var _per = knight_credit_per_page();
    var _p0 = _u.cr_page * _per;
    var _gray = make_color_rgb(148, 148, 148);
    for (var _j = 0; _j < _per; _j++)
    {
        var _k = _p0 + _j;
        if (_k >= array_length(_l))
            break;
        var _y = yy + 146 + (_j * 19);
        var _ln = _l[_k];
        if (_ln[0] == "h")
        {
            draw_set_color(_gray);
            knight_txt_small(xx + 320, _y, string_upper(_ln[1]));
        }
        else
        {
            scr_84_set_draw_font("main");
            var _nm = _ln[1];
            var _role = (_ln[2] != "") ? ("  -  " + _ln[2]) : "";
            var _tw = string_width(_nm + _role);
            if (_tw > 500)
            {
                _role = knight_fit_small(_role, 500 - string_width(_nm));
                _tw = string_width(_nm + _role);
            }
            var _x0 = xx + 320 - (_tw / 2);
            draw_set_halign(fa_left);
            draw_set_color(c_white);
            knight_txt_small(_x0, _y, _nm);
            draw_set_color(_gray);
            knight_txt_small(_x0 + string_width(_nm), _y, _role);
            draw_set_halign(fa_center);
        }
    }
    var _pg = knight_credit_pages(_i);
    draw_set_color(c_gray);
    if (_pg > 1)
        knight_txt_small(xx + 320, yy + 392, "PAGE " + string(_u.cr_page + 1) + "/" + string(_pg));
    draw_set_halign(fa_left);
}

// ---------------- modal boxes (START, errors, presets, results) ----------------
function knight_ui_draw_modal(xx, yy)
{
    var _m = global.knight_ui.modal;
    if (_m.k == "name" || _m.k == "kfo_text")
    {
        var _cur = ((global.knight_ui.siner mod 30) < 15) ? "_" : " ";
        var _l = [];
        for (var _i = 0; _i < array_length(_m.lines); _i++)
            array_push(_l, _m.lines[_i]);
        // a long text (a pasted settings code, a server address) shows its end
        var _shown = _m.buf;
        if (string_length(_shown) > 30)
            _shown = ".." + string_copy(_shown, string_length(_shown) - 27, 28);
        array_push(_l, ["@", _shown + _cur]);
        knight_modal_draw(_m.title, _l, [], 0, "");
        return 0;
    }
    if (_m.k == "launch")
    {
        knight_ui_draw_launch(xx, yy, _m);
        return 0;
    }
    if (_m.k == "songs")
    {
        knight_songpick_draw(xx, yy, _m);
        return 0;
    }
    knight_modal_draw(_m.title, _m.lines, _m.opts, _m.sel, "");
}

// the START box: what will be fought, who fights, which rules
function knight_ui_draw_launch(xx, yy, _m)
{
    var _l = _m.data;
    var _c = _l.cfg;
    var _lines = _m.lines;
    // body height
    var _bh = 0;
    for (var _i = 0; _i < array_length(_lines); _i++)
        _bh += array_length(knight_wrap(_lines[_i], 440)) * 30;
    var _h = 60 + 40 + _bh + 70;
    _h = min(_h, 440);
    var _y0 = yy + 240 - (_h / 2);
    draw_set_alpha(0.6);
    draw_set_color(c_black);
    draw_rectangle(xx - 10, yy - 10, xx + 650, yy + 490, false);
    draw_set_alpha(1);
    scr_darkbox_black(xx + 60, _y0, xx + 580, _y0 + _h);
    draw_set_halign(fa_center);
    draw_set_color(c_yellow);
    knight_txt(xx + 320, _y0 + 24, _m.title);
    // party heads
    var _p = _c.party;
    var _n = knight_party_size(_p);
    var _hx = xx + 320 - ((_n * 44) / 2) + 6;
    for (var _i = 0; _i < _n; _i++)
        knight_head_draw(_p[_i], _hx + (_i * 44), _y0 + 60);
    if (_n == 0)
    {
        draw_set_color(c_gray);
        knight_txt(xx + 320, _y0 + 58, "NO PARTY");
    }
    draw_set_halign(fa_left);
    var _y = _y0 + 96;
    for (var _i = 0; _i < array_length(_lines); _i++)
    {
        var _s = _lines[_i];
        var _warn = (string_char_at(_s, 1) == "!");
        draw_set_color(_warn ? c_yellow : c_white);
        var _wl = knight_wrap(_s, 440);
        for (var _j = 0; _j < array_length(_wl); _j++)
        {
            if (_y > _y0 + _h - 76)
                break;
            knight_txt(xx + 100, _y, _wl[_j]);
            _y += 30;
        }
    }
    knight_modal_opts_h(xx, _y0 + _h - 52, _m.opts, _m.sel);
}

// options side by side (like Save / Return) when there are two, a list otherwise
function knight_modal_opts_h(xx, _y, _opts, _sel)
{
    // build 50: the options measured and centred as a row (each with room for its heart), so long labels never overlap
    var _n = array_length(_opts);
    scr_84_set_draw_font("mainbig");
    // DRBR: the gap shrinks for long labels (down to 24) so the row stays inside the box's 460 px (it used to touch the frame)
    var _lw = 0;
    for (var _i = 0; _i < _n; _i++)
        _lw += string_width(_opts[_i].t) + 28;
    var _gap = (_n > 1) ? clamp(floor((460 - _lw) / (_n - 1)), 24, 56) : 56;
    var _tw = _lw + ((_n - 1) * _gap);
    var _x = xx + max(40, round(320 - (_tw / 2))) + 28;
    for (var _i = 0; _i < _n; _i++)
    {
        draw_set_color((_i == _sel) ? c_yellow : c_white);
        knight_txt(_x, _y, _opts[_i].t);
        if (_i == _sel)
            knight_heart(_x - 28, _y + 10);
        _x += string_width(_opts[_i].t) + _gap + 28;
    }
}

// one centred box. lines: strings (a leading "!" is a warning), ["@", text] typed text, ["^", text, colour] a centred
// sub-title, ["~", text] small grey print, ["s", label, value, extra, highlight] a small-print table row (fight stats),
// or [label, value, extra, highlight] result rows. opts: [{t, a}]
function knight_modal_line_h(_ln, _iw)
{
    if (is_array(_ln))
    {
        if (_ln[0] == "~")
            return array_length(knight_wrap_font(_ln[1], _iw, "main")) * 16 + 6;
        if (_ln[0] == "s")
            return 19;
        return 30;
    }
    return array_length(knight_wrap(_ln, _iw)) * 30;
}

function knight_modal_draw(_title, _lines, _opts, _sel, _footer)
{
    var xx = knight_cam_x();
    var yy = knight_cam_y();
    var _w = 520;
    var _iw = 440;
    var _x0 = xx + 60;
    var _bh = 0;
    for (var _i = 0; _i < array_length(_lines); _i++)
        _bh += knight_modal_line_h(_lines[_i], _iw);
    var _horiz = (array_length(_opts) == 2);
    var _oh = _horiz ? 44 : (array_length(_opts) * 32 + 12);
    var _h = 26 + 34 + _bh + 10 + _oh + ((_footer != "") ? 24 : 0) + 20;
    _h = min(_h, 456);
    var _y0 = yy + 240 - (_h / 2);
    draw_set_alpha(0.6);
    draw_set_color(c_black);
    draw_rectangle(xx - 10, yy - 10, xx + 650, yy + 490, false);
    draw_set_alpha(1);
    scr_darkbox_black(_x0, _y0, _x0 + _w, _y0 + _h);
    draw_set_halign(fa_center);
    draw_set_color(c_white);
    knight_txt(xx + 320, _y0 + 24, _title);
    draw_set_halign(fa_left);
    var _y = _y0 + 62;
    var _oy = _y0 + _h - 20 - _oh - ((_footer != "") ? 24 : 0) + (_horiz ? 6 : 0);
    for (var _i = 0; _i < array_length(_lines); _i++)
    {
        if (_y + 14 > _oy)
            break;
        var _ln2 = _lines[_i];
        if (is_array(_ln2))
        {
            if (_ln2[0] == "@")
            {
                draw_set_color(c_yellow);
                knight_txt(_x0 + 40, _y, _ln2[1]);
                _y += 30;
            }
            else if (_ln2[0] == "^")
            {
                draw_set_halign(fa_center);
                draw_set_color((array_length(_ln2) > 2) ? _ln2[2] : c_yellow);
                knight_txt(xx + 320, _y, knight_fit(_ln2[1], _iw));
                draw_set_halign(fa_left);
                _y += 30;
            }
            else if (_ln2[0] == "~")
            {
                draw_set_color(c_gray);
                _y += 4;
                _y += knight_para_small(_x0 + 40, _y, _ln2[1], _iw, 3);
                _y += 2;
            }
            else if (_ln2[0] == "s")
            {
                draw_set_color(c_white);
                knight_txt_small(_x0 + 40, _y, knight_fit_small(_ln2[1], 300));
                draw_set_halign(fa_right);
                draw_set_color((array_length(_ln2) > 4 && _ln2[4]) ? c_yellow : c_white);
                knight_txt_small(_x0 + _w - 130, _y, _ln2[2]);
                draw_set_color(c_ltgray);
                knight_txt_small(_x0 + _w - 40, _y, _ln2[3]);
                draw_set_halign(fa_left);
                _y += 19;
            }
            else
            {
                var _three = (array_length(_ln2) > 2 && _ln2[2] != "");
                draw_set_color(c_white);
                knight_txt(_x0 + 40, _y, knight_fit(_ln2[0], _three ? 230 : 300));
                draw_set_halign(fa_right);
                draw_set_color((array_length(_ln2) > 3 && _ln2[3]) ? c_yellow : c_white);
                // build 50: the middle column ends a gap before the measured third one (a long third no longer overlaps it)
                scr_84_set_draw_font("mainbig");
                var _mx = _three ? (_w - 40 - string_width(_ln2[2]) - 24) : (_w - 40);
                knight_txt(_x0 + _mx, _y, _ln2[1]);
                if (_three)
                {
                    draw_set_color(c_gray);
                    knight_txt(_x0 + _w - 40, _y, _ln2[2]);
                }
                draw_set_halign(fa_left);
                _y += 30;
            }
        }
        else
        {
            draw_set_color((string_char_at(_ln2, 1) == "!") ? c_yellow : c_white);
            var _wl = knight_wrap(_ln2, _iw);
            for (var _j = 0; _j < array_length(_wl); _j++)
            {
                if (_y + 26 > _oy)
                    break;
                knight_txt(_x0 + 40, _y, _wl[_j]);
                _y += 30;
            }
        }
    }
    if (_horiz)
        knight_modal_opts_h(xx, _oy, _opts, _sel);
    else
    {
        for (var _i = 0; _i < array_length(_opts); _i++)
        {
            var _hot = (_i == _sel);
            draw_set_color(_hot ? c_yellow : c_white);
            knight_txt(_x0 + 110, _oy + (_i * 32), _opts[_i].t);
            if (_hot)
                knight_heart(_x0 + 82, _oy + (_i * 32) + 10);
        }
    }
    if (_footer != "")
    {
        draw_set_color(c_gray);
        draw_set_halign(fa_center);
        knight_txt_small(xx + 320, _y0 + _h - 40, _footer);
        draw_set_halign(fa_left);
    }
    draw_set_color(c_white);
}

// ---- prompt object (results, leave, rush) ----
function knight_prompt_draw()
{
    var xx = knight_cam_x();
    var yy = knight_cam_y();
    if (sprite_exists(global.knight_freeze_spr))
        draw_sprite_stretched(global.knight_freeze_spr, 0, xx, yy, camera_get_view_width(view_camera[0]), camera_get_view_height(view_camera[0]));
    else
    {
        draw_set_color(c_black);
        draw_rectangle(xx - 10, yy - 10, xx + 650, yy + 490, false);
    }
    var _footer = "";
    if (autoact != "" && timer > 0)
        _footer = (autoact == "next") ? "NEXT FIGHT..." : "RESTARTING...";
    knight_modal_draw(title, lines, opts, sel, _footer);
    if (msg != "")
    {
        draw_set_color(make_color_rgb(255, 96, 96));
        draw_set_halign(fa_center);
        knight_txt(xx + 320, yy + 448, knight_fit(msg, 600));
        draw_set_halign(fa_left);
    }
    if (fade > 0)
    {
        draw_set_color(c_white);
        draw_set_alpha(min(1, fade / 12));
        draw_rectangle(xx - 10, yy - 10, xx + 650, yy + 490, false);
        draw_set_alpha(1);
    }
    draw_set_color(c_white);
}

function knight_prompt_step()
{
    // build 43: an online OUT / results box follows the match; the SEND box describes the highlighted send
    if (variable_instance_exists(id, "kfo_live") && kfo_live)
        kfo_prompt_refresh();
    if (variable_instance_exists(id, "kfo_send") && kfo_send)
        kfo_send_refresh();
    if (delay > 0)
    {
        delay--;
        return 0;
    }
    if (fade_act != "")
    {
        fade++;
        if (fade >= 14)
        {
            var _a = fade_act;
            fade_act = "";
            fade = 0;
            var _e = knight_act_run(_a);
            if (_e != "")
                msg = _e;
        }
        return 0;
    }
    var _n = array_length(opts);
    if (autoact != "" && timer > 0)
    {
        timer--;
        if (timer == 0)
        {
            fade_act = autoact;
            return 0;
        }
    }
    if (up_p() == 1 || left_p() == 1)
    {
        sel = (sel + _n - 1) mod _n;
        snd_play(snd_menumove);
    }
    if (down_p() == 1 || right_p() == 1)
    {
        sel = (sel + 1) mod _n;
        snd_play(snd_menumove);
    }
    if (button2_p() == 1)
    {
        for (var _i = 0; _i < _n; _i++)
        {
            if (variable_struct_exists(opts[_i], "cancel") && opts[_i].cancel)
            {
                snd_play(snd_smallswing);
                knight_act_run(opts[_i].a);
                return 0;
            }
        }
    }
    if (button1_p() == 1)
    {
        snd_play(snd_select);
        var _a2 = opts[sel].a;
        // closing the box or turning a page of the stats happens at once (no white fade)
        if (_a2 == "resume" || _a2 == "stats" || _a2 == "stats_more" || _a2 == "stats_back" || string_pos("onl_", _a2) == 1)
        {
            knight_act_run(_a2);
            return 0;
        }
        autoact = "";
        fade_act = _a2;
    }
}

// in-fight overlay: mode tags and the random reveal (small print, top left)
function knight_hud_draw()
{
    if (!knight_active() || global.knight_frozen)
        return 0;
    var _r = global.krun;
    var xx = knight_cam_x();
    var yy = knight_cam_y();
    knight_ch_draw_overlay();
    var _l = knight_hud_lines();
    // build 50: none of the hub's lines over a knight's Roaring (its finale)
    if (kbr_hud_roaring())
        _l = [];
    for (var _i = 0; _i < array_length(_l); _i++)
    {
        draw_set_color(c_black);
        knight_txt_small(xx + 9, yy + 5 + (_i * 16), _l[_i]);
        draw_set_color(knight_hud_line_color(_l[_i]));
        knight_txt_small(xx + 8, yy + 4 + (_i * 16), _l[_i]);
    }
    // build 50: the fight song's lyrics (online in the strip at the bottom, offline under these lines)
    knight_lyr_hud(xx, yy, array_length(_l));
    // build 43: online - the players (top right), the room's feed and my notes (under these lines)
    if (kfo_cfg_online(_r.cfg))
        kfo_hud_draw(xx, yy, yy + 8 + (array_length(_l) * 16));
    else if (variable_struct_exists(_r, "song_t") && _r.song_t < 180)
    {
        // build 47: the song's credit for the first 6 seconds of a fight (top right; online it goes to the log)
        var _sc = knight_song_credit();
        if (_sc != "")
        {
            draw_set_halign(fa_right);
            draw_set_alpha(min(1, (180 - _r.song_t) / 30));
            draw_set_color(c_black);
            knight_txt_small(xx + 633, yy + 5, knight_fit_small("MUSIC: " + _sc, 400));
            draw_set_color(c_ltgray);
            knight_txt_small(xx + 632, yy + 4, knight_fit_small("MUSIC: " + _sc, 400));
            draw_set_alpha(1);
            draw_set_halign(fa_left);
        }
    }
    knight_lu_hud_draw(xx, yy);
    if (_r.reveal != "" && _r.reveal_t < 150)
    {
        var _rl = knight_wrap(_r.reveal, 600);
        var _ry = kfo_cfg_online(_r.cfg) ? (yy + 96) : (yy + 8 + max(32, array_length(_l) * 16));
        draw_set_halign(fa_center);
        draw_set_alpha(min(1, (150 - _r.reveal_t) / 20));
        for (var _i = 0; _i < array_length(_rl); _i++)
        {
            draw_set_color(c_black);
            knight_txt(xx + 322, _ry + 2 + (_i * 30), _rl[_i]);
            draw_set_color(c_yellow);
            knight_txt(xx + 320, _ry + (_i * 30), _rl[_i]);
        }
        draw_set_alpha(1);
        draw_set_halign(fa_left);
    }
    draw_set_color(c_white);
}

function knight_stat_sum(_c, _which)
{
    var _v = 0;
    switch (_which)
    {
        case 0: _v = global.at[_c] + global.itemat[_c][0] + global.itemat[_c][1] + global.itemat[_c][2]; break;
        case 1: _v = global.df[_c] + global.itemdf[_c][0] + global.itemdf[_c][1] + global.itemdf[_c][2]; break;
        case 2: _v = global.mag[_c] + global.itemmag[_c][0] + global.itemmag[_c][1] + global.itemmag[_c][2]; break;
    }
    return floor(_v);
}
