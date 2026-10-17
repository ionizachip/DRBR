// ===== DRBR: the SKINS page (ONLINE > SKIN, or the room's SKIN row: Z) =====
// Every skin in four groups - PARTY (Kris, Susie, Ralsei, Noelle), FLOWERS (Chapter 5's flowers: Flowery, Aqua, Seth, Orange,
// Green, Yellow, Blue), BOSSES (Pink, Spamton) and OTHER (Berdly) - with a preview of the one under the cursor: how it walks
// in the cold place (round its four facings), its battle pose, its dialogue face when it has one, and what it is.
// < > another group, up / down a skin, Z wears it (and goes back), X goes back as you were, C wears Kris. The ONLINE page and the
// room keep < > on their SKIN row for a quick change. A skin is a number to the room (the "skin" message): nothing else changes.

// the groups that have skins: [key, title]
function kfo_skin_cats()
{
    var _all = [["main", "PARTY"], ["flowers", "FLOWERS"], ["bosses", "BOSSES"], ["other", "OTHER"]];
    var _o = [];
    for (var _i = 0; _i < array_length(_all); _i++)
    {
        if (array_length(kfo_skin_cat_list(_all[_i][0])) > 0)
            array_push(_o, _all[_i]);
    }
    return _o;
}

// the skins of group _k, in the registry's order
function kfo_skin_cat_list(_k)
{
    var _o = [];
    for (var _s = 1; _s <= kfo_skin_count(); _s++)
    {
        var _d = kfo_skin_def(_s);
        if ((variable_struct_exists(_d, "cat") ? _d.cat : "other") == _k)
            array_push(_o, _s);
    }
    return _o;
}

// [group index, place in it] of skin _s
function kfo_skin_cat_pos(_s)
{
    var _c = kfo_skin_cats();
    for (var _i = 0; _i < array_length(_c); _i++)
    {
        var _l = kfo_skin_cat_list(_c[_i][0]);
        for (var _j = 0; _j < array_length(_l); _j++)
        {
            if (_l[_j] == _s)
                return [_i, _j];
        }
    }
    return [0, 0];
}

// what a skin is, in a line (the preview's second line)
function kfo_skin_what(_s)
{
    var _d = kfo_skin_def(_s);
    switch (_d.key)
    {
        case "kris":
        case "susie":
        case "ralsei":
        case "noelle": return "THE PARTY";
        case "flowery": return "CHAPTER 5 - THE FLOWERS' LEADER";
        case "berdly": return "CHAPTER 2 - THE SMARTEST ONE";
        case "aqua":
        case "seth":
        case "orange":
        case "green":
        case "yellow":
        case "blue": return "CHAPTER 5 - FLOWER";
        case "pink": return "CHAPTER 5 - SECRET BOSS";
        case "spamton": return "CHAPTER 2 - [[SALESMAN]]";
    }
    return "";
}

// the battle pose of skin _s: an online-only look's own (registry), the game's own heroes' battle idles
function kfo_skin_bt_spr(_s)
{
    var _d = kfo_skin_def(_s);
    if (!_d.own)
        return kfo_skin_spr(_d.bt);
    switch (_d.key)
    {
        case "kris": return kfo_skin_spr("spr_krisb_idle");
        case "susie": return kfo_skin_spr("spr_susieb_idle");
        case "ralsei": return kfo_skin_spr("spr_ralseib_idle");
        case "noelle": return kfo_skin_spr("spr_noelleb_idle");
        case "flowery": return kfo_skin_spr("spr_knfl_idle");
    }
    return -1;
}

function kfo_ui_skin_open(_from)
{
    var _u = global.knight_ui;
    var _o = kfo_get();
    var _p = kfo_skin_cat_pos(kfo_skin_ok(_o.skin));
    _u.sk_from = _from;
    _u.sk_cat = _p[0];
    _u.sk_i = _p[1];
    _u.sk_t0 = current_time;
    _u.sub = "onl_skin";
    snd_play(snd_select);
    return 1;
}

function kfo_ui_skin_back()
{
    var _u = global.knight_ui;
    _u.sub = (variable_struct_exists(_u, "sk_from") && _u.sk_from == "lobby" && kfo_in_room()) ? "lobby" : "online";
    snd_play(snd_menumove);
    return 1;
}

// the skin under the cursor
function kfo_ui_skin_hot()
{
    var _u = global.knight_ui;
    var _c = kfo_skin_cats();
    var _ci = clamp(variable_struct_exists(_u, "sk_cat") ? _u.sk_cat : 0, 0, array_length(_c) - 1);
    var _l = kfo_skin_cat_list(_c[_ci][0]);
    return _l[clamp(variable_struct_exists(_u, "sk_i") ? _u.sk_i : 0, 0, array_length(_l) - 1)];
}

// wear skin _s: saved on this computer, told to the room
function kfo_skin_wear(_s)
{
    var _o = kfo_get();
    _o.skin = kfo_skin_ok(_s);
    kfo_ini_save();
    if (kfo_in_room())
        kfo_up({ k: "skin", skin: _o.skin });
    return 1;
}

function kfo_ui_step_skin(_up, _down, _left, _right, _ok, _back, _alt)
{
    var _u = global.knight_ui;
    if (_back)
        return kfo_ui_skin_back();
    var _c = kfo_skin_cats();
    var _nc = array_length(_c);
    _u.sk_cat = clamp(_u.sk_cat, 0, _nc - 1);
    if (_left || _right)
    {
        _u.sk_cat = knight_ui_cycle(_u.sk_cat, _left ? -1 : 1, _nc);
        // the group's first skin, or the one you wear when it is in it
        var _p = kfo_skin_cat_pos(kfo_skin_ok(kfo_get().skin));
        _u.sk_i = (_p[0] == _u.sk_cat) ? _p[1] : 0;
        _u.sk_t0 = current_time;
        snd_play(snd_menumove);
        return 0;
    }
    var _l = kfo_skin_cat_list(_c[_u.sk_cat][0]);
    if (_up || _down)
    {
        _u.sk_i = knight_ui_cycle(clamp(_u.sk_i, 0, array_length(_l) - 1), _up ? -1 : 1, array_length(_l));
        _u.sk_t0 = current_time;
        snd_play(snd_menumove);
        return 0;
    }
    // the room may say no (a match running: you change it between matches)
    var _why = (_u.sk_from == "lobby" && kfo_in_room()) ? kfo_ui_lobby_why("skin") : "";
    if (_alt)
    {
        if (_why != "")
            return knight_ui_warn(_why);
        kfo_skin_wear(1);
        snd_play(snd_select);
        return kfo_ui_skin_back();
    }
    if (_ok)
    {
        var _s = kfo_ui_skin_hot();
        if (!kfo_skin_ready(_s))
            return knight_ui_warn("This skin's art is missing from this copy of the game.");
        if (_why != "")
            return knight_ui_warn(_why);
        kfo_skin_wear(_s);
        snd_play(snd_select);
        return kfo_ui_skin_back();
    }
    return 0;
}

function kfo_ui_skin_desc()
{
    var _s = kfo_ui_skin_hot();
    var _d = kfo_skin_def(_s);
    var _l1 = ((kfo_skin_ok(kfo_get().skin) == _s) ? "You wear it." : "Z: wear it.") + "  < >: another group.  X: back.";
    // (DRBR: online every skin is cosmetic - the same HP, stats and SOUL for everyone; a hero of the game's own shows its
    // own battle art, a look is drawn over Kris's)
    if (_d.own)
        return _l1 + "#Their own battle art - same HP and SOUL as all.";
    return _l1 + "#Only a look, over Kris - same HP and SOUL as all.";
}

function kfo_ui_draw_skin(xx, yy)
{
    var _u = global.knight_ui;
    var _o = kfo_get();
    var _c = kfo_skin_cats();
    var _ci = clamp(_u.sk_cat, 0, array_length(_c) - 1);
    var _l = kfo_skin_cat_list(_c[_ci][0]);
    var _wear = kfo_skin_ok(_o.skin);
    draw_set_color(c_white);
    draw_rectangle(xx + 306, yy + 91, xx + 309, yy + 410, false);
    knight_caption_hub("SKINS", xx + 112, yy + 84);
    // the groups: every one's name, the chosen one yellow and underlined
    var _tx = xx + 78;
    for (var _i = 0; _i < array_length(_c); _i++)
    {
        var _t = _c[_i][1];
        scr_84_set_draw_font("main");
        var _tw = string_width(_t);
        draw_set_color((_i == _ci) ? c_yellow : c_gray);
        knight_txt_small(_tx, yy + 100, _t);
        if (_i == _ci)
            draw_rectangle(_tx, yy + 116, _tx + _tw - 1, yy + 117, false);
        _tx += _tw + 10;
    }
    // its skins: the head, the name, ON for the one you wear
    var _sel = clamp(_u.sk_i, 0, array_length(_l) - 1);
    for (var _i = 0; _i < array_length(_l) && _i < 8; _i++)
    {
        var _s = _l[_i];
        var _y = yy + 126 + (_i * 34);
        var _hot = (_i == _sel);
        kfo_skin_head_draw(_s, xx + 84, _y);
        var _rd = kfo_skin_ready(_s);
        draw_set_color(!_rd ? c_dkgray : (_hot ? c_yellow : c_white));
        knight_txt(xx + 122, _y, knight_fit(string_upper(kfo_skin_def(_s).name), 124));
        if (_s == _wear)
        {
            draw_set_halign(fa_right);
            draw_set_color(c_lime);
            knight_txt_small(xx + 298, _y + 8, "ON");
            draw_set_halign(fa_left);
        }
        if (_hot)
            knight_heart(xx + 65, _y + 8);
    }
    kfo_ui_skin_preview2(_l[_sel], xx, yy);
    draw_set_color(c_white);
}

// the preview of skin _s, right of the list: its name, what it is, how it walks (round its four facings), its battle pose,
// its dialogue face, and whether it is a look or a character of its own
function kfo_ui_skin_preview2(_s, xx, yy)
{
    var _u = global.knight_ui;
    var _d = kfo_skin_def(_s);
    var _bx = xx + 330;
    var _by = yy + 100;
    var _bw = 238;
    var _bh = 300;
    draw_set_color(c_black);
    draw_rectangle(_bx, _by, _bx + _bw, _by + _bh, false);
    var _col = _d.own ? knight_char_hpcolor(_d.num) : _d.col;
    draw_set_color(_col);
    draw_rectangle(_bx, _by, _bx + _bw, _by + _bh, true);
    var _cx = _bx + (_bw / 2);
    draw_set_halign(fa_center);
    draw_set_color(_col);
    knight_txt(_cx, _by + 8, knight_fit(string_upper(_d.name), _bw - 16));
    draw_set_color(c_ltgray);
    knight_txt_small(_cx, _by + 36, knight_fit_small(kfo_skin_what(_s), _bw - 12));
    draw_set_halign(fa_left);
    if (!kfo_skin_ready(_s))
    {
        draw_set_halign(fa_center);
        draw_set_color(make_color_rgb(255, 150, 120));
        knight_txt_small(_cx, _by + 130, "MISSING ART");
        draw_set_halign(fa_left);
        return 0;
    }
    // how it walks: round down, right, up, left (a facing a second), its walk frames turning
    var _el = max(0, current_time - (variable_struct_exists(_u, "sk_t0") ? _u.sk_t0 : 0));
    var _f = (_el div 1000) mod 4;
    var _fr = (_el div 160) mod 4;
    var _ws = kfo_world_skin_spr(_s, _f);
    var _wh = sprite_get_height(_ws) * 2;
    // (a 2x Kris standing with his top left here has his feet on the floor line, y + 196)
    var _kh = sprite_get_height(spr_krisd_dark) * 2;
    var _kw = sprite_get_width(spr_krisd_dark) * 2;
    var _floor = _by + 196;
    kfo_skin_ow_draw(_s, _f, true, _fr, _bx + 62 - (_kw / 2), _floor - _kh, (_wh > 150) ? 1 : 2, c_white, 1);
    // its battle pose (2x when it fits), feet on the same line
    var _bs = kfo_skin_bt_spr(_s);
    if (_bs >= 0)
    {
        var _n = max(1, sprite_get_number(_bs));
        var _spd = _d.own ? 0.2 : _d.bt_spd;
        var _bfr = floor((current_time / (1000 / 30)) * _spd) mod _n;
        var _fx = (!_d.own && _d.bt_flip) ? -1 : 1;
        var _l = sprite_get_bbox_left(_bs);
        var _r = sprite_get_bbox_right(_bs) + 1;
        var _t = sprite_get_bbox_top(_bs);
        var _b = sprite_get_bbox_bottom(_bs) + 1;
        var _k = (((_r - _l) * 2) <= 120 && ((_b - _t) * 2) <= 150) ? 2 : 1;
        var _mid = ((_l + _r) / 2) - sprite_get_xoffset(_bs);
        draw_sprite_ext(_bs, _bfr, round((_bx + 172) - (_mid * _fx * _k)), round(_floor - ((_b - sprite_get_yoffset(_bs)) * _k)), _fx * _k, _k, 0, c_white, 1);
    }
    draw_set_color(c_dkgray);
    draw_line(_bx + 12, _floor + 2, _bx + _bw - 12, _floor + 2);
    draw_set_color(c_gray);
    draw_set_halign(fa_center);
    knight_txt_small(_bx + 62, _floor + 6, "WALKING");
    knight_txt_small(_bx + 172, _floor + 6, "BATTLE");
    draw_set_halign(fa_left);
    // its dialogue face, when it has one (never a stand-in)
    if (!_d.own && variable_struct_exists(_d, "portrait") && kfo_skin_spr(_d.portrait) >= 0)
        kfo_skin_portrait_draw(_s, _bx + 44, _by + 248, 64, 52);
    // a look or a character of its own
    var _nx = (!_d.own && variable_struct_exists(_d, "portrait")) ? (_bx + 84) : (_bx + 12);
    draw_set_color(_d.own ? c_white : make_color_rgb(150, 210, 255));
    if (_d.own)
    {
        knight_txt_small(_nx, _by + 236, "THE GAME'S OWN");
        knight_txt_small(_nx, _by + 252, "HERO, IN THEIR");
        knight_txt_small(_nx, _by + 268, "OWN BATTLE ART.");
    }
    else
    {
        knight_txt_small(_nx, _by + 236, "ONLINE ONLY. A");
        knight_txt_small(_nx, _by + 252, "LOOK OVER KRIS:");
        knight_txt_small(_nx, _by + 268, "SAME HP, SOUL.");
    }
    draw_set_color(c_white);
    return 1;
}
