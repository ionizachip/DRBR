// ===== DRBR: the BOSSES page (ONLINE > BOSSES, or the room's BOSSES row) =====
// Every boss of the online roster in two groups - KNIGHTS (the hub's own knights) and BOSSES (the other chapters' bosses) -
// with a card for the one under the cursor: its look, its chapter and what it is, its SOUL (and what that SOUL does), its sends,
// how many attacks it has, its music, and whether this copy of the game has it.
// Z: outside a room, a PRACTICE match against that boss alone (your saved room settings are not changed); in a room, the host
// puts it in the room's bosses or takes it out (the same as SETTINGS > BOSSES), a player just looks. < > the other group,
// up / down a boss, X back.

// the groups: [key, title]
function kfo_boss_cats()
{
    return [["knights", "KNIGHTS"], ["bosses", "BOSSES"]];
}

// the online ids (roster rows) of group _c: 0 the knights, 1 the other bosses
function kfo_boss_cat_list(_c)
{
    var _o = [];
    for (var _k = 0; _k < kbr_ok_count(); _k++)
    {
        var _en = kbr_ok_enc(_k);
        if ((_c == 0) == !is_struct(_en))
            array_push(_o, _k);
    }
    return _o;
}

// the boss under the cursor (an online id)
function kfo_ui_boss_hot()
{
    var _u = global.knight_ui;
    var _c = clamp(variable_struct_exists(_u, "bs_cat") ? _u.bs_cat : 0, 0, 1);
    var _l = kfo_boss_cat_list(_c);
    if (array_length(_l) == 0)
        return 0;
    return _l[clamp(variable_struct_exists(_u, "bs_i") ? _u.bs_i : 0, 0, array_length(_l) - 1)];
}

// this copy of the game can run boss _k (a knight: its registry entry; a boss: its battle object and look)
function kfo_boss_ready(_k)
{
    var _en = kbr_ok_enc(_k);
    if (is_struct(_en))
        return kbr_enc_ready(_en);
    return kbr_ok_valid(_k);
}

// its SOUL mode ("red" for the knights)
function kfo_boss_soul(_k)
{
    var _en = kbr_ok_enc(_k);
    if (is_struct(_en) && variable_struct_exists(_en, "soul"))
        return _en.soul;
    return "red";
}

function kfo_boss_soul_col(_m)
{
    return (_m == "red") ? c_red : kbr_soul_hint_col(_m);
}

// what it is, in a line: "CHAPTER 2 - SECRET BOSS", "CHAPTER 3 - KNIGHT (A MOD)"
function kfo_boss_what(_k)
{
    var _en = kbr_ok_enc(_k);
    if (is_struct(_en))
    {
        var _cat = variable_struct_exists(_en, "cat") ? _en.cat : "";
        return "CHAPTER " + string(_en.chapter) + " - " + ((_cat == "secret") ? "SECRET BOSS" : "BOSS");
    }
    var _r = kbr_ok_row(_k);
    if (_r.nm)
        return "CHAPTER 3 - KNIGHT, DARKER";
    return (_r.key == "base") ? "CHAPTER 3 - KNIGHT" : "CHAPTER 3 - KNIGHT (A MOD)";
}

// what it is about, in the top bar's two lines (its own description: "#" between the lines)
function kfo_boss_line(_k)
{
    var _en = kbr_ok_enc(_k);
    if (is_struct(_en))
        return _en.desc;
    if (kbr_ok_row(_k).nm)
        return "The Normal Knight's own fight, darker#and faster: the KNIGHTMARE.";
    if (kbr_ok_valid(_k))
        return knight_reg(kbr_reg_of(_k)).desc;
    return "";
}

// its music's title ("" when it has none of its own)
function kfo_boss_song(_k)
{
    var _en = kbr_ok_enc(_k);
    var _s = "";
    if (is_struct(_en))
        _s = variable_struct_exists(_en, "song") ? _en.song : "";
    else if (kbr_ok_valid(_k))
        _s = knight_reg(kbr_reg_of(_k)).songcredit;
    if (!is_string(_s))
        return "";
    var _p = string_pos(" - ", _s);
    return string_upper((_p > 0) ? string_copy(_s, 1, _p - 1) : _s);
}

// who made it (the knights' mods; "" for the game's own)
function kfo_boss_author(_k)
{
    if (is_struct(kbr_ok_enc(_k)) || !kbr_ok_valid(_k))
        return "";
    var _a = knight_reg(kbr_reg_of(_k)).author;
    return (is_string(_a) && _a != "Toby Fox") ? _a : "";
}

// how many attacks it has
function kfo_boss_natk(_k)
{
    var _en = kbr_ok_enc(_k);
    if (is_struct(_en))
        return array_length(_en.atk);
    if (!kbr_ok_valid(_k))
        return 0;
    return array_length(knight_reg(kbr_reg_of(_k)).atk);
}

// its sends: [family name, how many]
function kfo_boss_sends(_k)
{
    var _en = kbr_ok_enc(_k);
    if (is_struct(_en))
        return [kbr_fam_name(_en.fid), array_length(_en.sends)];
    var _n = 0;
    for (var _i = 1; _i < kbr_skill_count(); _i++)
    {
        if (kbr_skill_family(_i) == KBR_FAM_KNIGHT)
            _n++;
    }
    return [kbr_fam_name(KBR_FAM_KNIGHT), _n];
}

// its look: [sprite, frame count] (-1 when this copy does not have it)
function kfo_boss_look(_k)
{
    var _en = kbr_ok_enc(_k);
    var _s = -1;
    if (is_struct(_en))
        _s = asset_get_index(_en.spr);
    else if (kbr_ok_valid(_k))
        _s = knight_ui_portrait(kbr_reg_of(_k));
    if (_s < 0 || !sprite_exists(_s))
        return -1;
    return _s;
}

// in the room's bosses (WHO FIGHTS)
function kfo_boss_in_room(_k)
{
    if (!kfo_in_room())
        return false;
    return kfo_set_has_kn(kfo_lobby_set(), _k);
}

function kfo_ui_boss_open(_from)
{
    var _u = global.knight_ui;
    _u.bs_from = _from;
    if (!variable_struct_exists(_u, "bs_cat"))
        _u.bs_cat = 0;
    if (!variable_struct_exists(_u, "bs_i"))
        _u.bs_i = 0;
    _u.bs_t0 = current_time;
    _u.sub = "onl_boss";
    snd_play(snd_select);
    return 1;
}

function kfo_ui_boss_back()
{
    var _u = global.knight_ui;
    _u.sub = (variable_struct_exists(_u, "bs_from") && _u.bs_from == "lobby" && kfo_in_room()) ? "lobby" : "online";
    snd_play(snd_menumove);
    return 1;
}

// a practice room against boss _k alone (the room's settings, not your saved ones: they stay as they were)
function kfo_boss_practice(_k)
{
    var _u = global.knight_ui;
    var _o = kfo_get();
    _o.err = "";
    kfo_practice_start();
    if (!is_struct(_o.H))
        return 0;
    var _s = kfo_set_clean(_o.H.set);
    _s.kn = [_k];
    _s.open = _k;
    // its own sends while it is out (SENDS: CURRENT BOSS)
    _s.skfam = 0;
    _o.H.set = kfo_set_named(_s);
    _o.H.dl = true;
    _u.sub = "lobby";
    _u.lob_row = 0;
    _u.lob_scroll = 0;
    snd_play(snd_select);
    knight_ui_tell("Practice against " + kbr_ok_name(_k) + ": START when you are ready.");
    return 1;
}

function kfo_ui_step_boss(_up, _down, _left, _right, _ok, _back, _alt)
{
    var _u = global.knight_ui;
    if (_back)
        return kfo_ui_boss_back();
    _u.bs_cat = clamp(_u.bs_cat, 0, 1);
    if (_left || _right)
    {
        _u.bs_cat = knight_ui_cycle(_u.bs_cat, _left ? -1 : 1, 2);
        _u.bs_i = 0;
        _u.bs_t0 = current_time;
        snd_play(snd_menumove);
        return 0;
    }
    var _l = kfo_boss_cat_list(_u.bs_cat);
    var _n = max(1, array_length(_l));
    if (_up || _down)
    {
        _u.bs_i = knight_ui_cycle(clamp(_u.bs_i, 0, _n - 1), _up ? -1 : 1, _n);
        _u.bs_t0 = current_time;
        snd_play(snd_menumove);
        return 0;
    }
    if (!_ok || array_length(_l) == 0)
        return 0;
    var _k = kfo_ui_boss_hot();
    if (!kfo_boss_ready(_k))
        return knight_ui_warn("This boss's art is missing from this copy of the game.");
    // in a room: the host puts it in / takes it out of the room's bosses
    if (kfo_in_room())
    {
        if (!kfo_is_host())
            return knight_ui_warn("Only the host chooses the room's bosses.");
        var _r = kfo_opt_change(kfo_ui_set_cur(), "kn" + string(_k), 1);
        if (is_string(_r))
            return knight_ui_warn(_r);
        if (kfo_ui_set_apply(_r))
            snd_play(snd_select);
        return 0;
    }
    return kfo_boss_practice(_k);
}

function kfo_ui_boss_desc()
{
    var _k = kfo_ui_boss_hot();
    if (!kfo_boss_ready(_k))
        return "Not in this copy of the game#(its art is missing).";
    return kfo_boss_line(_k);
}

// the page's keys, under the list: [line 1, line 2]
function kfo_ui_boss_keys()
{
    var _k = kfo_ui_boss_hot();
    var _l1 = "Z: PRACTICE AGAINST IT ALONE";
    if (kfo_in_room())
        _l1 = kfo_is_host() ? (kfo_boss_in_room(_k) ? "Z: TAKE IT OUT OF THE ROOM" : "Z: PUT IT IN THE ROOM") : "THE HOST PICKS THE ROOM'S BOSSES";
    return [_l1, "< >: KNIGHTS / BOSSES   X: BACK"];
}

function kfo_ui_draw_boss(xx, yy)
{
    var _u = global.knight_ui;
    var _ci = clamp(_u.bs_cat, 0, 1);
    var _cats = kfo_boss_cats();
    var _l = kfo_boss_cat_list(_ci);
    draw_set_color(c_white);
    draw_rectangle(xx + 306, yy + 91, xx + 309, yy + 410, false);
    knight_caption_hub("BOSSES", xx + 112, yy + 84);
    // the groups: both names, the chosen one yellow and underlined
    var _tx = xx + 84;
    for (var _i = 0; _i < array_length(_cats); _i++)
    {
        var _t = _cats[_i][1] + " (" + string(array_length(kfo_boss_cat_list(_i))) + ")";
        scr_84_set_draw_font("main");
        var _tw = string_width(_t);
        draw_set_color((_i == _ci) ? c_yellow : c_gray);
        knight_txt_small(_tx, yy + 100, _t);
        if (_i == _ci)
            draw_rectangle(_tx, yy + 116, _tx + _tw - 1, yy + 117, false);
        _tx += _tw + 14;
    }
    // its bosses: the name (the knights by their short names), the SOUL it gives you at the end of the row; in a room the ones
    // it fights are white, the others grey
    var _sel = clamp(_u.bs_i, 0, max(0, array_length(_l) - 1));
    var _inr = kfo_in_room();
    for (var _i = 0; _i < array_length(_l) && _i < 8; _i++)
    {
        var _k = _l[_i];
        var _y = yy + 126 + (_i * 34);
        var _hot = (_i == _sel);
        var _rd = kfo_boss_ready(_k);
        var _on = !_inr || kfo_boss_in_room(_k);
        draw_set_color(!_rd ? c_dkgray : (_hot ? (_on ? c_yellow : c_orange) : (_on ? c_white : c_gray)));
        knight_txt(xx + 90, _y, knight_fit((_ci == 0) ? kbr_ok_short(_k) : string_upper(kbr_ok_name(_k)), 170));
        var _sm = kfo_boss_soul(_k);
        if (_sm == "yellow")
            kfo_soul_draw_up(xx + 274, _y + 7, 1, kfo_boss_soul_col(_sm), _rd ? 1 : 0.35, c_black);
        else
            kfo_soul_draw(xx + 274, _y + 7, 1, kfo_boss_soul_col(_sm), _rd ? 1 : 0.35, c_black);
        if (_hot)
            knight_heart(xx + 66, _y + 8);
    }
    // the keys
    var _ky = kfo_ui_boss_keys();
    draw_set_halign(fa_center);
    draw_set_color(c_gray);
    knight_txt_small(xx + 185, yy + 360, knight_fit_small(_ky[0], 228));
    knight_txt_small(xx + 185, yy + 376, knight_fit_small(_ky[1], 228));
    draw_set_halign(fa_left);
    if (array_length(_l) > 0)
        kfo_ui_boss_card(_l[_sel], xx, yy);
    draw_set_color(c_white);
}

// the card of boss _k, right of the list
function kfo_ui_boss_card(_k, xx, yy)
{
    var _bx = xx + 330;
    var _by = yy + 100;
    var _bw = 238;
    var _bh = 300;
    var _col = kbr_ok_color(_k);
    draw_set_color(c_black);
    draw_rectangle(_bx, _by, _bx + _bw, _by + _bh, false);
    draw_set_color(_col);
    draw_rectangle(_bx, _by, _bx + _bw, _by + _bh, true);
    var _cx = _bx + (_bw / 2);
    draw_set_halign(fa_center);
    knight_txt(_cx, _by + 8, knight_fit(string_upper(kbr_ok_name(_k)), _bw - 16));
    draw_set_color(c_ltgray);
    knight_txt_small(_cx, _by + 36, knight_fit_small(kfo_boss_what(_k), _bw - 12));
    var _rd = kfo_boss_ready(_k);
    // its look: the whole sprite at the largest whole scale that fits 212 x 136 (half size for a big one); the Knightmare is the
    // Normal Knight's look in its own red
    var _s = _rd ? kfo_boss_look(_k) : -1;
    if (_s >= 0)
    {
        var _l = sprite_get_bbox_left(_s);
        var _r = sprite_get_bbox_right(_s) + 1;
        var _t = sprite_get_bbox_top(_s);
        var _b = sprite_get_bbox_bottom(_s) + 1;
        var _sc = clamp(floor(min(212 / max(1, _r - _l), 136 / max(1, _b - _t))), 1, 3);
        if ((_r - _l) > 212 || (_b - _t) > 136)
            _sc = 0.5;
        var _fr = floor(((current_time - (variable_struct_exists(global.knight_ui, "bs_t0") ? global.knight_ui.bs_t0 : 0)) / 1000) * 6) mod max(1, sprite_get_number(_s));
        var _mx = ((_l + _r) / 2) - sprite_get_xoffset(_s);
        var _my = ((_t + _b) / 2) - sprite_get_yoffset(_s);
        draw_sprite_ext(_s, _fr, round(_cx - (_mx * _sc)), round((_by + 120) - (_my * _sc)), _sc, _sc, 0, kbr_ok_row(_k).nm ? _col : c_white, 1);
    }
    else
    {
        draw_set_color(make_color_rgb(255, 150, 120));
        knight_txt_small(_cx, _by + 112, "MISSING ART");
    }
    draw_set_halign(fa_left);
    draw_set_color(c_dkgray);
    draw_line(_bx + 12, _by + 190, _bx + _bw - 12, _by + 190);
    // what it means for you: its SOUL (and what that SOUL does), its sends, its attacks, its music
    var _x0 = _bx + 14;
    var _y0 = _by + 198;
    var _sm = kfo_boss_soul(_k);
    if (_sm == "yellow")
        kfo_soul_draw_up(_x0, _y0, 1, kfo_boss_soul_col(_sm), 1, c_black);
    else
        kfo_soul_draw(_x0, _y0, 1, kfo_boss_soul_col(_sm), 1, c_black);
    draw_set_color(kfo_boss_soul_col(_sm));
    knight_txt_small(_x0 + 24, _y0 + 1, string_upper(_sm) + " SOUL");
    var _hint = kbr_soul_hint_text(_sm);
    draw_set_color(c_ltgray);
    knight_txt_small(_x0, _y0 + 20, knight_fit_small((_hint != "") ? _hint : "ARROWS MOVE, X SLOWS - DODGE!", _bw - 28));
    var _sn = kfo_boss_sends(_k);
    draw_set_color(c_white);
    knight_txt_small(_x0, _y0 + 40, knight_fit_small("SENDS: " + string_upper(_sn[0]) + " (" + string(_sn[1]) + ")", _bw - 28));
    knight_txt_small(_x0, _y0 + 56, knight_fit_small(string(kfo_boss_natk(_k)) + " ATTACKS", _bw - 28));
    var _song = kfo_boss_song(_k);
    if (_song != "")
    {
        draw_set_color(c_gray);
        knight_txt_small(_x0, _y0 + 72, knight_fit_small("MUSIC: " + _song, _bw - 28));
    }
    var _au = kfo_boss_author(_k);
    if (_au != "")
    {
        draw_set_color(c_gray);
        knight_txt_small(_x0, _y0 + 88, knight_fit_small("MOD BY " + string_upper(_au), _bw - 28));
    }
    // in a room: whether it fights there (the room's SETTINGS > BOSSES)
    if (kfo_in_room())
    {
        draw_set_halign(fa_right);
        draw_set_color(kfo_boss_in_room(_k) ? c_lime : c_gray);
        knight_txt_small(_bx + _bw - 10, _y0 + 1, kfo_boss_in_room(_k) ? "IN THIS ROOM" : "NOT IN THIS ROOM");
        draw_set_halign(fa_left);
    }
    return 1;
}

// the ONLINE page's right side while BOSSES is picked: who there is to fight, in their colours (drawn centred on _cx; the
// alignment is left centred, as the page had it)
function kfo_ui_boss_teaser(_cx, _y)
{
    draw_set_halign(fa_center);
    draw_set_color(c_gray);
    knight_txt_small(_cx, _y, "WHO YOU CAN FIGHT");
    var _l0 = kfo_boss_cat_list(0);
    var _l1 = kfo_boss_cat_list(1);
    draw_set_color(c_white);
    knight_txt_small(_cx, _y + 18, string(array_length(_l0)) + " KNIGHTS AND " + string(array_length(_l1)) + " BOSSES");
    // the bosses' names, two lines, each in its colour
    var _w = 0;
    scr_84_set_draw_font("main");
    for (var _i = 0; _i < array_length(_l1); _i++)
        _w += string_width(kbr_ok_short(_l1[_i])) + ((_i > 0) ? 10 : 0);
    var _x = _cx - (_w / 2);
    draw_set_halign(fa_left);
    for (var _i = 0; _i < array_length(_l1); _i++)
    {
        var _t = kbr_ok_short(_l1[_i]);
        draw_set_color(kfo_boss_ready(_l1[_i]) ? kbr_ok_color(_l1[_i]) : c_dkgray);
        knight_txt_small(_x, _y + 38, _t);
        _x += string_width(_t) + 10;
    }
    draw_set_halign(fa_center);
    draw_set_color(c_gray);
    knight_txt_small(_cx, _y + 58, "Z: EACH ONE'S SOUL AND SENDS");
    // (left centred: the ONLINE page goes on drawing centred under it)
    return 1;
}
