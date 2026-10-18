
// ===== Build 45: the battle royale HUD (drawn by the hub controller over the battle) =====
// top left: the skill slots (4 and the hold slot), the charge and cooldown bars, the log
// top middle: the knight that attacks now (and the one that comes next), the stage, the clock
// top right: the players (alive first: HP bar, shield / regeneration / reflection marks; OUT #n), the network light
// over the box: the countdown (with the player's keys), WAITING FOR PLAYERS, the switch / hit / Knightmare flashes,
// OUT - WATCHING
// PLAYER LIST key (TAB unless changed): every player in full

function kbr_hud_draw(xx, yy)
{
    var _M = kbr_match();
    if (is_undefined(_M) || !kbr_on())
        return 0;
    if (!variable_struct_exists(_M, "vw"))
        _M.vw = kbr_vw_new();
    var _spec = (_M.out || !_M.me);
    if (!variable_struct_exists(_M, "tg"))
        _M.tg = kbr_tg_new();
    // DRBR: the top middle is one stack under the boss's two lines (Flowery's MERCY, MATCH INFO, then the banner): each one
    // takes the next free line from here, so none of them is drawn over another
    _M.hud_ty = yy + 36;
    // build 52: DARKNESS first (it hides the battle, never the HUD)
    kbr_dark_overlay(_M);
    // build 48: the targeting threads under the SOULs, the "!" over mine
    // (build 49: no threads between the SOULs any more)
    kbr_draw_souls();
    kbr_tg_exc(_M);
    kbr_hud_fx(xx, yy, _M);
    // build 50: a knight's Roaring (its finale) is a full-screen moment: the HUD steps aside for it (the SOULs, a hit's
    // flash, your GAME OVER and QUICK SETTINGS stay)
    var _roar = kbr_hud_roaring();
    if (!_roar)
    {
        // build 47: a player has the skill slots top left; a watcher has the card of the one they follow there
        if (!_spec)
        {
            kbr_hud_skills(xx, yy, _M);
            // DRBR: the sends aimed at you (drbr53.gml)
            kbr_hud_incoming(xx, yy, _M);
        }
        else if (!_M.vw.qs)
            kbr_hud_spec(xx, yy, _M);
        if (!_M.tab && !_M.vw.qs && !(_spec && _M.vw.stats))
            kbr_hud_log(xx, yy, _M);
        kbr_hud_knight(xx, yy, _M);
        kbr_hud_info(xx, yy, _M);
        // TAB: the full list instead of the short one
        if (_M.tab)
            kbr_hud_tab(xx, yy, _M);
        else
            kbr_hud_players(xx, yy, _M);
        kbr_hud_center(xx, yy, _M);
        // DRBR: a special SOUL just turned on - what it does, right under the box (drbr53.gml)
        if (!_spec)
            kbr_hud_soulhint_box(xx, yy, _M);
        kbr_hud_banner(xx, yy, _M);
        // build 48: the TARGETING command row under the box
        if (!_M.vw.qs)
            kbr_hud_tg(xx, yy, _M);
        if (_spec)
        {
            kbr_hud_zoom(xx, yy, _M);
            kbr_hud_help(xx, yy, _M);
            kbr_hud_stats(xx, yy, _M);
        }
    }
    // build 48: your SOUL's break and the GAME OVER (over everything but QUICK SETTINGS)
    kbr_ko_draw(xx, yy, _M);
    kbr_bn_tick(_M);
    kbr_bn_draw(xx, yy, _M);
    kfo_tut_draw(xx, yy);
    kbr_hud_qs(xx, yy, _M);
    if (!_roar)
    {
        kbr_hud_net(xx, yy, _M);
        // build 48: the room's chat (left of the box, above the party panel)
        kfo_chat_draw_match(xx, yy);
    }
    draw_set_alpha(1);
    draw_set_color(c_white);
    draw_set_halign(fa_left);
    return 1;
}

function kbr_hud_roaring()
{
    if (instance_exists(obj_knight_roaring2))
        return true;
    var _r3 = asset_get_index("obj_knight_roaring3");
    return _r3 >= 0 && instance_exists(_r3);
}

function kbr_hud_text(_x, _y, _t, _col)
{
    draw_set_color(c_black);
    draw_text(_x + 1, _y + 1, _t);
    draw_set_color(_col);
    draw_text(_x, _y, _t);
}

// the screen flashes: a knight stepping in (white), a hit (red), Knightmare / the final two (dark red)
function kbr_hud_fx(xx, yy, _M)
{
    var _a = 0;
    // REDUCED FLASHING (MATCH VIEW): the hub's own flashes at a third, the red edge steady
    var _fk = kfo_view().flash ? 0.3 : 1;
    if (_M.swfx > 0)
    {
        draw_set_alpha((_M.swfx / 20) * 0.18 * _fk);
        draw_set_color(c_white);
        draw_rectangle(xx, yy, xx + 640, yy + 480, false);
    }
    if (_M.hitfx > 0)
    {
        draw_set_alpha((_M.hitfx / 8) * 0.16 * _fk);
        draw_set_color(c_red);
        draw_rectangle(xx, yy, xx + 640, yy + 480, false);
    }
    if (_M.flash > 0)
    {
        draw_set_alpha((_M.flash / 12) * 0.5 * _fk);
        draw_set_color(c_black);
        draw_rectangle(xx, yy, xx + 640, yy + 480, false);
    }
    var _c = (_M.cur_k >= 0) ? kbr_tl_get(_M.tl, _M.cur_k) : undefined;
    if ((!is_undefined(_c) && _c.nm && _M.R.ph == "run") || _M.ft_on)
    {
        // a red edge around the screen
        draw_set_alpha(0.12 + ((_fk < 1) ? 0 : (0.05 * sin(current_time / 300))));
        draw_set_color(make_color_rgb(200, 0, 30));
        draw_rectangle(xx, yy, xx + 640, yy + 10, false);
        draw_rectangle(xx, yy + 470, xx + 640, yy + 480, false);
        draw_rectangle(xx, yy, xx + 10, yy + 480, false);
        draw_rectangle(xx + 630, yy, xx + 640, yy + 480, false);
    }
    draw_set_alpha(1);
    return _a;
}

// the skill slots - build 51: a row of DELTARUNE-style diamonds (same slots, same order, the HOLD slot last), each with a
// clear picture of what the skill does - the game's own bullet sprites for the attacks, simple drawn symbols for the rest
// (a green plus for MAX / the heals, a blue shield, a blue mirror heart). The picked one pulses gently with the yellow frame,
// a skill that just arrived pops in, and the picked skill's name is written under the row in the dialogue font.
function kbr_hud_skills(xx, yy, _M)
{
    var _S = _M.sk;
    var _e = _M.eff;
    if (!_e.skills)
        return 0;
    var _n = clamp(_e.slots, 1, 4);
    var _r = 23;
    // build 51: floating off the corner (a margin and a slow drift of a pixel or two)
    var _fx = xx + 14;
    var _cy0 = yy + 36 + round(sin(current_time / 900) * 1.5);
    var _pickname = "";
    var _pickcol = c_white;
    for (var _i = 0; _i <= _n; _i++)
    {
        var _hold = (_i == _n);
        // build 51: the slots interlock in a staggered zigzag (top, bottom, top, bottom), edge to edge; HOLD on the top row
        // after a gap
        var _cx = _fx + _r + (_i * 27) + (_hold ? 16 : 0);
        var _cy = _cy0 + ((!_hold && (_i mod 2) == 1) ? 26 : 0);
        var _sl = undefined;
        if (_hold)
            _sl = _S.hold;
        else if (_i < array_length(_S.slots))
            _sl = _S.slots[_i];
        var _fc = make_color_rgb(60, 60, 60);
        var _sid = 0;
        var _spin = false;
        var _sc = 1;
        if (!is_undefined(_sl))
        {
            _sid = _sl.sid;
            _fc = kbr_skill_red(_sid) ? make_color_rgb(235, 60, 60) : make_color_rgb(70, 220, 100);
            // still spinning in: a slot machine of pictures, then a small pop
            if (_sl.rev > 0)
            {
                _sid = 1 + ((current_time div 90) mod 15);
                _fc = c_white;
                _spin = true;
                _sc = 0.85 + (0.15 * ((_sl.rev mod 6) / 6));
            }
        }
        var _pick = (!_hold && _i == _S.sel && _i < array_length(_S.slots));
        if (_pick && !_spin)
            _sc = 1 + (0.06 * sin(current_time / 140));
        kbr_diamond(_cx, _cy, round(_r * _sc), _fc, _pick, is_undefined(_sl));
        if (_sid > 0)
        {
            var _lkd = (!_spin && kbr_slot_locked(_sl));
            var _dim = (!_spin && (!kbr_skill_ok(_sl.sid) || _lkd)) ? 0.35 : 1;
            kbr_skill_icon(_sid, _cx, _cy, _dim, _sc * 1.3);
            // build 52: padlocked by a rival's LOCK - the padlock over it and its seconds
            if (_lkd)
            {
                kbr_padlock(_cx, _cy - 6, 1.1, 1);
                scr_84_set_draw_font("main");
                draw_set_halign(fa_center);
                kbr_hud_text(_cx, _cy + 6, string(ceil(_sl.lk / 30)), c_yellow);
                draw_set_halign(fa_left);
            }
        }
        if (_hold)
        {
            scr_84_set_draw_font("main");
            draw_set_halign(fa_center);
            kbr_hud_text(_cx, _cy + _r + 2, "HOLD", c_ltgray);
            draw_set_halign(fa_left);
        }
        if (_pick && !_spin)
        {
            _pickname = kbr_skill_fname(_sl.sid);
            _pickcol = kbr_skill_red(_sl.sid) ? make_color_rgb(255, 120, 120) : make_color_rgb(120, 255, 150);
        }
    }
    // the picked skill's name under the row (right of the TP bar), and the cooldown bar under it
    if (_pickname != "")
    {
        scr_84_set_draw_font("main");
        var _nx = _fx + 66;
        var _ny = _cy0 + 52;
        kbr_hud_text(_nx, _ny, kbr_fit(_pickname, 120), _pickcol);
        if (_S.cd > 0)
        {
            var _f = _S.cd / max(1, round(90 * (_e.cdm / 100)));
            draw_set_color(c_gray);
            draw_rectangle(_nx, _ny + 14, _nx + round(100 * _f), _ny + 15, false);
        }
    }
    // DRBR 1.0.2: while the orange / yellow SOUL has Z (its dash, its shots), USE SKILL is on HOLD BREATH's key - said right
    // of the slots all the while (it blinks as it comes and when the usual key is held: kbr_skills_tick)
    if (kbr_orange_on() && _M.me && !_M.out)
    {
        var _lx = _fx + _r + (_n * 27) + 16 + _r + 8;
        var _ly = _cy0 - 12;
        scr_84_set_draw_font("main");
        var _hot = variable_struct_exists(_S, "mv_t") && _S.mv_t > 0 && ((_S.mv_t div 6) mod 2) == 0;
        kbr_hud_text(_lx, _ly, "SKILLS:", c_ltgray);
        kbr_hud_text(_lx, _ly + 14, "HOLD " + kbr_use_key_label(), _hot ? c_white : c_yellow);
    }
    // build 52: what is on you right now, with its seconds (SLOW, CONFUSE, DARKNESS, REGENERATION, REFLECTION, LIFESTEAL,
    // DETERMINATION)
    kbr_hud_status(_fx + 66, _cy0 + 76, _M);
    draw_set_font(fnt_small);
    // build 50: no separate charge bar - the TP bar is the one meter (online_hud50.gml)
    return 1;
}

function kbr_hud_status(_x0, _y0, _M)
{
    var _S = _M.sk;
    var _l = [[8, _S.slow_t], [9, _S.conf_t], [22, _S.dark_t], [14, _S.regen_t], [15, _S.reflect_t], [24, _S.ls_t], [25, _S.det_t]];
    var _n = 0;
    draw_set_font(fnt_small);
    for (var _i = 0; _i < array_length(_l); _i++)
    {
        var _f = _l[_i][1];
        if (_f <= 0)
            continue;
        var _sid = _l[_i][0];
        var _x = _x0 + ((_n mod 3) * 42);
        var _y = _y0 + ((_n div 3) * 20);
        var _red = kbr_skill_red(_sid);
        // a small dark chip, red-edged for a rival's skill on you, green for your own; it blinks in its last second
        var _al = (_f < 30 && ((current_time div 120) mod 2) == 0) ? 0.45 : 1;
        draw_set_alpha(0.75 * _al);
        draw_set_color(c_black);
        draw_rectangle(_x, _y, _x + 38, _y + 17, false);
        draw_set_alpha(_al);
        draw_set_color(_red ? make_color_rgb(235, 60, 60) : make_color_rgb(70, 220, 100));
        draw_rectangle(_x, _y, _x + 38, _y + 17, true);
        kbr_skill_icon(_sid, _x + 10, _y + 9, _al, 0.7);
        kbr_hud_text(_x + 21, _y + 3, string(ceil(_f / 30)) + "s", c_white);
        draw_set_alpha(1);
        _n++;
    }
    return _n;
}

// build 52: DARKNESS on you - black everywhere but a circle of light around your SOUL (over the battle, under the HUD)
function kbr_dark_overlay(_M)
{
    var _S = _M.sk;
    // build 52: a watcher sees the DARKNESS on the one they follow (dark_w)
    var _wd = variable_struct_exists(_S, "dark_w") && _S.dark_w && kbr_spec_pid(_M) >= 0;
    if (_S.dark_t <= 0 || ((_M.out || !_M.me) && !_wd) || !instance_exists(obj_heart))
        return 0;
    var _in = clamp((_S.dark_max - _S.dark_t) / 10, 0, 1);
    var _outa = clamp(_S.dark_t / 15, 0, 1);
    var _a = min(_in, _outa) * 0.97;
    var _r1 = _S.dark_r + (sin(current_time / 200) * 2);
    var _r0 = max(8, _r1 - 22);
    var xx = knight_cam_x();
    var yy = knight_cam_y();
    var _bp = 152;
    if (i_ex(obj_battlecontroller))
    {
        var _bc = instance_find(obj_battlecontroller, 0);
        if (variable_instance_exists(_bc, "bp"))
            _bp = _bc.bp;
    }
    var _x0 = xx - 10;
    var _x1 = xx + 650;
    var _y0 = yy - 10;
    var _y1 = yy + 480 - max(0, _bp) - 4;
    var _h = instance_find(obj_heart, 0);
    var _hx = (_h.bbox_left + _h.bbox_right) / 2;
    var _hy = (_h.bbox_top + _h.bbox_bottom) / 2;
    if (_hy >= _y1)
        _y1 = yy + 490;
    var _ang = [];
    for (var _i = 0; _i < 48; _i++)
        array_push(_ang, _i * 7.5);
    array_push(_ang, point_direction(_hx, _hy, _x0, _y0), point_direction(_hx, _hy, _x1, _y0), point_direction(_hx, _hy, _x0, _y1), point_direction(_hx, _hy, _x1, _y1));
    array_sort(_ang, true);
    var _n = array_length(_ang);
    draw_primitive_begin(pr_trianglestrip);
    for (var _i = 0; _i <= _n; _i++)
    {
        var _g = _ang[_i mod _n];
        var _dx = lengthdir_x(1, _g);
        var _dy = lengthdir_y(1, _g);
        var _t = knight_dark_ray(_hx, _hy, _dx, _dy, _x0, _y0, _x1, _y1);
        var _ri = min(_r1, _t);
        draw_vertex_color(_hx + (_dx * _ri), _hy + (_dy * _ri), c_black, _a);
        draw_vertex_color(_hx + (_dx * _t), _hy + (_dy * _t), c_black, _a);
    }
    draw_primitive_end();
    draw_primitive_begin(pr_trianglestrip);
    for (var _i = 0; _i <= 48; _i++)
    {
        var _g2 = _i * 7.5;
        var _dx2 = lengthdir_x(1, _g2);
        var _dy2 = lengthdir_y(1, _g2);
        var _t2 = knight_dark_ray(_hx, _hy, _dx2, _dy2, _x0, _y0, _x1, _y1);
        draw_vertex_color(_hx + (_dx2 * min(_r0, _t2)), _hy + (_dy2 * min(_r0, _t2)), c_black, 0);
        draw_vertex_color(_hx + (_dx2 * min(_r1, _t2)), _hy + (_dy2 * min(_r1, _t2)), c_black, _a);
    }
    draw_primitive_end();
    draw_set_alpha(1);
    draw_set_color(c_white);
    return 1;
}

// one diamond slot: black inside, a 2-pixel outline in _c (dim and dashed-looking when empty); the picked one gets a yellow
// outer frame
function kbr_diamond(_cx, _cy, _r, _c, _pick, _empty)
{
    draw_set_alpha(_empty ? 0.55 : 0.9);
    draw_set_color(c_black);
    draw_triangle(_cx - _r, _cy, _cx, _cy - _r, _cx + _r, _cy, false);
    draw_triangle(_cx - _r, _cy, _cx, _cy + _r, _cx + _r, _cy, false);
    draw_set_alpha(_empty ? 0.6 : 1);
    // build 51: a thick 4-pixel edge (the picked one gets a 2-pixel yellow frame outside it)
    var _rs = _pick ? [_r + 3, _r + 2, _r, _r - 1, _r - 2, _r - 3] : [_r, _r - 1, _r - 2, _r - 3];
    for (var _k = 0; _k < array_length(_rs); _k++)
    {
        var _q = _rs[_k];
        draw_set_color((_pick && _k < 2) ? c_yellow : _c);
        draw_line(_cx - _q, _cy, _cx, _cy - _q);
        draw_line(_cx, _cy - _q, _cx + _q, _cy);
        draw_line(_cx + _q, _cy, _cx, _cy + _q);
        draw_line(_cx, _cy + _q, _cx - _q, _cy);
    }
    draw_set_alpha(1);
    return 1;
}

// the picture inside a diamond - build 51: only the game's own art, moving a little, and always centred on the diamond:
// the SOUL (the mod's white copy of the game's heart, spr_khub_soul, recoloured), the Knight's own bullets (its sword
// bullets, red slash, stars, diamonds, teeth, fountain, crescent, lightning), the battle menu's item icons (spr_dmenu_items:
// the shield, the arrows) and the heal sparkle. _sc: the icon's size (1.3 in the HUD's diamonds).
function kbr_skill_icon(_sid, _x, _y, _a, _sc)
{
    if (is_undefined(_sc))
        _sc = 1;
    var _k = _sc;
    var _kb = _sc * 0.7;
    var _w = c_white;
    var _gr = make_color_rgb(70, 230, 110);
    var _bl = make_color_rgb(90, 170, 255);
    var _t = current_time;
    var _bob = sin(_t / 300) * 1.5 * _k;
    var _f4 = (_t div 120) mod 4;
    switch (_sid)
    {
        case 1:
            // SWORD: one of the Knight's sword bullets, aimed
            kbr_spr_c(spr_knight_diamondbullet_l, 0, _x + (_bob * 0.5), _y + (_bob * 0.5), 0.3 * _k, 0.36 * _k, 45, _w, _a);
            break;
        case 2:
            // FLURRY: three sword bullets sliding in from alternating sides
            for (var _i = 0; _i < 3; _i++)
            {
                var _d = (_i == 1) ? -1 : 1;
                kbr_spr_c(spr_knight_diamondbullet_l, 0, _x + (sin((_t / 260) + _i) * 3 * _k * _d), _y + ((_i - 1) * 8 * _k), 0.2 * _k, 0.28 * _k, (_d < 0) ? 180 : 0, _w, _a);
            }
            break;
        case 3:
            // DIAMOND STORM: two of the Knight's diamond bullets drifting
            for (var _i = 0; _i < 2; _i++)
            {
                var _s = (_i == 0) ? -1 : 1;
                kbr_spr_c(spr_diamondbullet, 0, _x + (_s * 5 * _k) + (sin(_t / 400) * 2 * _k), _y + (_s * 5 * _k), 0.34 * _k, 0.34 * _k, 0, _w, _a);
            }
            break;
        case 21:
            // DIAMOND ERUPTION: violet diamonds bursting out of the middle
            for (var _i = 0; _i < 3; _i++)
            {
                var _ph = ((_t / 900) + (_i / 3)) mod 1;
                var _rr = (5 + (sin((_t / 300) + _i) * 2)) * _k;
                kbr_spr_c(spr_diamondbullet, 0, _x + lengthdir_x(_rr, 90 + (_i * 120)), _y + lengthdir_y(_rr, 90 + (_i * 120)), 0.3 * _k, 0.3 * _k, 0, make_color_rgb(200, 140, 255), _a);
            }
            break;
        case 4:
            // STREAMLINE: the Splitters' teeth streaming across
            for (var _i = 0; _i < 2; _i++)
            {
                kbr_spr_c(spr_roaringknight_tooth, 0, _x + (((_i == 0) ? -5 : 5) * _k) + (sin((_t / 250) + (_i * 3)) * 1.5), _y + (((_i == 0) ? -3 : 3) * _k), 0.36 * _k, 0.36 * _k, 0, _w, _a);
            }
            break;
        case 5:
            // RING: stars circling
            for (var _i = 0; _i < 6; _i++)
                kbr_spr_c(spr_knight_bullet_star, 0, _x + lengthdir_x(9 * _k, (_i * 60) + (_t / 12)), _y + lengthdir_y(9 * _k, (_i * 60) + (_t / 12)), 0.1 * _k, 0.1 * _k, 0, _w, _a);
            break;
        case 6:
            // STAR BURST: one star, turning
            kbr_spr_c(spr_knight_bullet_star, 0, _x, _y, 0.3 * _k, 0.3 * _k, _t / 10, _w, _a);
            break;
        case 7:
            // WEIRD CIRCLE: its shadow on the floor, a star rising out of it
            kbr_spr_c(spr_knight_weird_shadow, 0, _x, _y + (6 * _k), 0.36 * _k, 0.6 * _k, 0, _w, _a);
            var _ph = (_t / 900) mod 1;
            kbr_spr_c(spr_knight_bullet_star, 0, _x, _y - (3 * _k) + (sin(_t / 300) * 2), 0.15 * _k, 0.15 * _k, _t / 8, _w, _a);
            break;
        case 8:
            // SLOW: a blue SOUL sinking, the menu's down arrow beside it
            kbr_soul_icon(_x - (3 * _k), _y + (abs(_bob) * 0.6), _k * 0.9, _bl, _a);
            kbr_spr_c(spr_dmenu_items, 8, _x + (8 * _k), _y + (sin(_t / 300) * 2), 1, 1, 0, _w, _a);
            break;
        case 9:
            // CONFUSE: a pink SOUL turning upside down (the controls flip)
            kbr_soul_icon(_x, _y, _k, make_color_rgb(255, 140, 220), _a, 180 + (sin(_t / 250) * 25));
            break;
        case 10:
            // KNIGHTMARE: the Knight's own red slash, playing
            kbr_spr_c(spr_roaringknight_slash_red, 2 + ((_t div 110) mod 4), _x, _y, 0.24 * _k, 0.24 * _k, 0, _w, _a);
            break;
        case 11:
        case 12:
            // HEAL 40 / 80: a green plus and the amount
            kbr_plus(_x, _y - (6 * _k), 4 * _k, 1.5 * _k, _a);
            scr_84_set_draw_font("main");
            draw_set_halign(fa_center);
            draw_set_alpha(_a);
            kbr_hud_text(_x + 1, _y + 1, (_sid == 11) ? "40" : "80", _gr);
            draw_set_alpha(1);
            draw_set_halign(fa_left);
            break;
        case 13:
            // SHIELD: the battle menu's shield icon at twice its size, blue with a white edge, on whole pixels
            var _sx = round(_x);
            var _sy = round(_y);
            for (var _i = 0; _i < 4; _i++)
                kbr_spr_c(spr_dmenu_items, 4, _sx + lengthdir_x(1, _i * 90), _sy + lengthdir_y(1, _i * 90), 2, 2, 0, _w, _a);
            kbr_spr_c(spr_dmenu_items, 4, _sx, _sy, 2, 2, 0, _bl, _a);
            break;
        case 14:
            // REGENERATION: small green pluses rising one after another
            for (var _i = 0; _i < 3; _i++)
            {
                var _ph = ((_t / 1100) + (_i / 3)) mod 1;
                kbr_plus(_x + ((_i - 1) * 8 * _k), _y + ((7 - (_ph * 12)) * _k), 3 * _k, 1, _a * min(1, (1 - _ph) * 3));
            }
            break;
        case 15:
            // REFLECTION: a light-blue SOUL with the menu's arrow bouncing off it
            kbr_soul_icon(_x - (3 * _k), _y + (2 * _k), _k * 0.9, make_color_rgb(140, 220, 255), _a);
            var _ph = (_t / 700) mod 1;
            var _o = (_ph < 0.5) ? (_ph * 2) : ((1 - _ph) * 2);
            kbr_spr_c(spr_dmenu_items, (_ph < 0.5) ? 6 : 7, _x + ((5 + (_o * 1.5)) * _k), _y - ((4 + (_o * 1.5)) * _k), 1, 1, 0, _w, _a);
            break;
        case 16:
            // MAX (FULL HEAL): one big green plus, breathing a little
            var _pk = (1 + (0.06 * sin(_t / 220))) * _k;
            kbr_plus(_x, _y, 9 * _pk, 3 * _pk, _a);
            break;
        case 22:
            // DARKNESS: a red SOUL alone in the dark, a dim circle of light breathing around it
            draw_set_alpha(_a * 0.35);
            draw_set_color(make_color_rgb(255, 235, 170));
            draw_circle(round(_x), round(_y), (8 + (sin(_t / 260) * 1.5)) * _k, false);
            draw_set_alpha(_a);
            draw_set_color(make_color_rgb(255, 235, 170));
            draw_circle(round(_x), round(_y), (10 + (sin(_t / 260) * 1.5)) * _k, true);
            kbr_soul_icon(_x, _y, 0.5 * _k, c_red, _a);
            break;
        case 23:
            // LOCK: a padlock, rattling now and then
            var _jig = ((((_t div 90) mod 9) == 0) ? (((_t div 30) mod 2) ? 1 : -1) : 0) * _k;
            kbr_padlock(_x + _jig, _y, _k, _a);
            break;
        case 24:
            // LIFESTEAL: a red SOUL, a green plus pulsing out of it
            kbr_soul_icon(_x - (3 * _k), _y + (3 * _k), 0.65 * _k, c_red, _a);
            var _ph2 = (_t / 900) mod 1;
            kbr_plus(_x + ((5 + (_ph2 * 2)) * _k), _y - ((5 + (_ph2 * 3)) * _k), 3.5 * _k, 1.2 * _k, _a * min(1, (1 - _ph2) * 2.5));
            break;
        case 25:
            // DETERMINATION: the SOUL breaks... and refuses to - the game's own broken heart, then whole again with a flash
            var _ph3 = (_t / 1500) mod 1;
            if (_ph3 < 0.3)
                kbr_spr_c(spr_heartbreak, 0, _x, _y, 0.8 * _k, 0.8 * _k, 0, c_red, _a);
            else
            {
                kbr_soul_icon(_x, _y, 0.8 * _k, c_red, _a);
                if (_ph3 < 0.42)
                    kbr_soul_icon(_x, _y, 0.8 * _k, c_white, _a * (1 - ((_ph3 - 0.3) / 0.12)));
            }
            break;
        case 17:
            // CRESCENT SLASH: the Kaizo Knight's crescent
            kbr_spr_c(spr_bullet_knightcrescent, 0, _x, _y + (_bob * 0.5), 0.45 * _k, 0.45 * _k, 0, _w, _a);
            break;
        case 18:
            // SWORD RAIN: sword bullets diving down
            for (var _i = 0; _i < 3; _i++)
            {
                kbr_spr_c(spr_knight_diamondbullet_l, 0, _x + ((_i - 1) * 7 * _k), _y + (sin((_t / 220) + (_i * 2)) * 2), 0.13 * _k, 0.2 * _k, 270, _w, _a);
            }
            break;
        case 19:
            // THUNDER LINES: a lightning bolt, flickering
            kbr_spr_c(spr_coaster_lightning, (_t div 120) mod 2, _x, _y, 0.67 * _k, 0.9 * _k, 0, _w, _a * ((((_t div 80) mod 7) == 0) ? 0.45 : 1));
            break;
        case 20:
            // FOUNTAIN SPLIT: the Thorn Knight's fountain bullet
            kbr_spr_c(spr_rk_fountain_bullet, _f4, _x, _y + _bob, 0.55 * _k, 0.55 * _k, 0, _w, _a);
            break;
        // DRBR: the bosses' sends - their own sprites (Chapter 1 Jevil, Chapter 4 Gerson, Chapter 5 Flowery). DRBR 1.0.1: at 70% of
        // the size they had (_kb), as big as the knights' pictures in the slots - they filled the slots past their edges
        case 26:
            // SPADE RING: three spades going round
            for (var _i = 0; _i < 3; _i++)
            {
                var _ra = (_t / 6) + (_i * 120);
                kbr_icon_fit(spr_jv_spadebullet, 0, _x + lengthdir_x(6 * _kb, _ra), _y + lengthdir_y(6 * _kb, _ra), 9 * _kb, 0, _w, _a);
            }
            break;
        case 27:
            // DIAMOND RAIN: two diamonds rising
            for (var _i = 0; _i < 2; _i++)
                kbr_icon_fit(spr_jv_diamondbullet_vert, 0, _x + ((_i - 0.5) * 9 * _kb), _y + 4 - (((_t / 40) + (_i * 9)) mod 12) * _kb, 12 * _kb, 0, _w, _a);
            break;
        case 28:
            kbr_icon_fit(spr_jv_clubsball_b, _f4 mod max(1, sprite_get_number(spr_jv_clubsball_b)), _x, _y + _bob, 18 * _kb, 0, _w, _a);
            break;
        case 29:
            kbr_icon_fit(spr_jv_carousel, _f4 mod max(1, sprite_get_number(spr_jv_carousel)), _x, _y + _bob, 20 * _kb, 0, _w, _a);
            break;
        case 30:
            kbr_icon_fit(spr_jv_joker_scythebody, 0, _x, _y, 22 * _kb, (_t / 4) mod 360, _w, _a);
            break;
        case 31:
            kbr_icon_fit(spr_jv_suitsbomb, _f4 mod max(1, sprite_get_number(spr_jv_suitsbomb)), _x, _y + _bob, 18 * _kb, 0, _w, _a);
            break;
        case 32:
            kbr_icon_fit(spr_hj_gerson_hammer_trowable4, 0, _x, _y, 20 * _kb, (_t / 3) mod 360, _w, _a);
            break;
        case 33:
            kbr_icon_fit(spr_hj_bounce_shell_idle, _f4 mod max(1, sprite_get_number(spr_hj_bounce_shell_idle)), _x, _y + _bob, 20 * _kb, 0, _w, _a);
            break;
        case 34:
            kbr_icon_fit(spr_hj_gerson_red_hammer, 0, _x, _y, 22 * _kb, -30 + (sin(_t / 140) * 40), _w, _a);
            break;
        case 35:
            kbr_icon_fit(spr_hj_greenheart, 0, _x, _y, 12 * _kb, 0, _w, _a);
            kbr_icon_fit(spr_hj_spear_arrow, 0, _x + (10 * _kb) - (((_t / 50) mod 6) * _kb), _y, 12 * _kb, 180, _w, _a);
            break;
        case 36:
            kbr_icon_fit(spr_hj_gerson_bell, 0, _x - (3 * _kb), _y + (sin(_t / 120) * 2), 16 * _kb, sin(_t / 160) * 15, _w, _a);
            kbr_icon_fit(spr_hj_gerson_musical_note2, 0, _x + (7 * _kb), _y - (5 * _kb) + _bob, 9 * _kb, 0, _w, _a);
            break;
        case 37:
            kbr_icon_fit(spr_hj_gerson_red_hammer, 0, _x, _y + _bob, 26 * _kb, 180, make_color_rgb(255, 200, 200), _a);
            break;
        case 38:
            // JARONA: his lunge
            kbr_icon_fit(spr_fl_flowery_puuunch_left, _f4 mod max(1, sprite_get_number(spr_fl_flowery_puuunch_left)), _x - (((_t / 60) mod 4) * _kb), _y, 22 * _kb, 0, _w, _a);
            break;
        case 39:
            // BAMBOO RUSH: two stalks, blue joints
            kbr_icon_fit(spr_fl_bamboo_wall, 0, _x - (4 * _kb), _y, 20 * _kb, 0, _w, _a);
            kbr_icon_fit(spr_fl_bamboo_wall, 0, _x + (5 * _kb), _y + (2 * _kb), 18 * _kb, 0, make_color_rgb(120, 190, 255), _a);
            break;
        case 40:
            kbr_icon_fit(spr_fl_orangeheart_lillypad, 0, _x, _y + (5 * _kb), 16 * _kb, 0, _w, _a);
            kbr_icon_fit(spr_fl_attack_knifechain, _f4 mod max(1, sprite_get_number(spr_fl_attack_knifechain)), _x, _y - (3 * _kb), 16 * _kb, 90, _w, _a);
            break;
        case 41:
            kbr_icon_fit(spr_fl_omega_book, _f4 mod max(1, sprite_get_number(spr_fl_omega_book)), _x, _y + _bob, 20 * _kb, 0, _w, _a);
            break;
        case 42:
            kbr_icon_fit(spr_fl_orange_animepunch_finished_cent, _f4 mod max(1, sprite_get_number(spr_fl_orange_animepunch_finished_cent)), _x - (3 * _kb), _y, 18 * _kb, 0, _w, _a);
            kbr_icon_fit(spr_fl_bullet_green_flame, _f4 mod max(1, sprite_get_number(spr_fl_bullet_green_flame)), _x + (7 * _kb), _y + (4 * _kb), 10 * _kb, 0, _w, _a);
            break;
        case 43:
            kbr_icon_fit(spr_fl_enemy_yellow_reticle, 0, _x, _y, 20 * _kb, (_t / 8) mod 360, _w, _a * 0.8);
            kbr_icon_fit(spr_fl_enemy_blue_bullet_butterfly, _f4 mod max(1, sprite_get_number(spr_fl_enemy_blue_bullet_butterfly)), _x, _y + _bob, 13 * _kb, 0, _w, _a);
            break;
        case 44:
            // LAST JARONA: his lunge, round the rainbow
            kbr_icon_fit(spr_fl_flowery_puuunch_left, _f4 mod max(1, sprite_get_number(spr_fl_flowery_puuunch_left)), _x, _y, 24 * _kb, 0, make_color_hsv((_t / 6) mod 255, 160, 255), _a);
            break;
        // DRBR: Spamton NEO's (his own Chapter 2 sprites)
        case 45:
            // PIPIS: the egg, rocking
            kbr_icon_fit(spr_pipis_egg, 0, _x, _y + _bob, 18 * _kb, sin(_t / 90) * 20, _w, _a);
            break;
        case 46:
            // FLYING HEADS: two of them, one behind the other
            kbr_icon_fit(spr_sneo_crew, _f4 mod max(1, sprite_get_number(spr_sneo_crew)), _x + (4 * _kb), _y - (3 * _kb), 14 * _kb, 0, _w, _a * 0.7);
            kbr_icon_fit(spr_sneo_crew, _f4 mod max(1, sprite_get_number(spr_sneo_crew)), _x - (2 * _kb), _y + (2 * _kb) + _bob, 18 * _kb, 0, _w, _a);
            break;
        case 47:
            kbr_icon_fit(spr_sneo_wireheart_smaller, _f4 mod max(1, sprite_get_number(spr_sneo_wireheart_smaller)), _x, _y + _bob, 20 * _kb, 0, _w, _a);
            break;
        case 48:
            // KROMER RAIN: a bill drifting right
            kbr_icon_fit(spr_spamton_dollar, 0, _x + ((((_t / 40) mod 6) - 3) * _kb), _y, 20 * _kb, 0, _w, _a);
            break;
        case 49:
            // MAIL WALL: a mail cell over a crew head
            kbr_icon_fit(spr_sneo_mail, 0, _x, _y - (5 * _kb), 12 * _kb, 0, _w, _a);
            kbr_icon_fit(spr_sneo_crew, _f4 mod max(1, sprite_get_number(spr_sneo_crew)), _x, _y + (6 * _kb), 12 * _kb, 0, _w, _a);
            break;
        // DRBR: Pink's (her own Chapter 5 sprites)
        case 51:
            kbr_icon_fit(spr_pk_bullet_catface, _f4 mod max(1, sprite_get_number(spr_pk_bullet_catface)), _x + (((_t / 40) mod 6) - 3) * _kb, _y, 18 * _kb, 0, _w, _a);
            break;
        case 52:
            kbr_icon_fit(spr_pk_bullet_catface, _f4 mod max(1, sprite_get_number(spr_pk_bullet_catface)), _x - (4 * _kb), _y - (4 * _kb) + _bob, 14 * _kb, 0, _w, _a);
            kbr_icon_fit(spr_pk_bullet_catface, _f4 mod max(1, sprite_get_number(spr_pk_bullet_catface)), _x + (4 * _kb), _y + (4 * _kb) - _bob, 14 * _kb, 0, _w, _a);
            break;
        case 53:
            kbr_icon_fit(spr_pk_pinklanebullet_animation, _f4 mod max(1, sprite_get_number(spr_pk_pinklanebullet_animation)), _x, _y, 20 * _kb, (_t / 3) mod 360, _w, _a);
            break;
        case 54:
            kbr_icon_fit(spr_pk_fusebomb, _f4 mod max(1, sprite_get_number(spr_pk_fusebomb)), _x, _y + _bob, 18 * _kb, 0, _w, _a);
            break;
        case 55:
            kbr_icon_fit(spr_pk_fusebomb_big, 0, _x, _y + _bob, 24 * _kb, 0, make_color_rgb(255, 210, 230), _a);
            break;
        case 56:
            kbr_icon_fit(spr_heartbullet, 0, _x, _y + _bob, 16 * _kb, 0, make_color_rgb(255, 120, 200), _a);
            break;
        case 50:
            // BIG SHOT: his big shot, flaring
            kbr_icon_fit(spr_sneo_bigshot_s, _f4 mod max(1, sprite_get_number(spr_sneo_bigshot_s)), _x, _y, 24 * _kb, 0, make_color_rgb(255, 255, 140 + (sin(_t / 60) * 100)), _a);
            break;
        default:
            scr_84_set_draw_font("main");
            draw_set_halign(fa_center);
            kbr_hud_text(_x + 1, _y - 6, string_copy(kbr_skill_short(_sid), 1, 4), c_white);
            draw_set_halign(fa_left);
            break;
    }
    draw_set_alpha(1);
    return 1;
}

// build 52: a padlock (LOCK): a grey shackle over a gold body with a keyhole, centred on _x, _y; _k its size (1: 14 x 18)
function kbr_padlock(_x, _y, _k, _a)
{
    _x = round(_x);
    _y = round(_y);
    var _w = max(3, round(6 * _k));
    var _bh = max(4, round(6 * _k));
    var _sw = max(2, round(4 * _k));
    var _sh = max(3, round(6 * _k));
    var _th = max(1, round(1.5 * _k));
    draw_set_alpha(_a);
    // shackle (a dark edge, then grey)
    draw_set_color(c_black);
    draw_rectangle(_x - _sw - _th - 1, _y - _sh - _th - 1, _x + _sw + _th + 1, _y - _sh + _th + 1, false);
    draw_rectangle(_x - _sw - _th - 1, _y - _sh - _th - 1, _x - _sw + _th + 1, _y, false);
    draw_rectangle(_x + _sw - _th - 1, _y - _sh - _th - 1, _x + _sw + _th + 1, _y, false);
    draw_set_color(make_color_rgb(200, 200, 210));
    draw_rectangle(_x - _sw - _th, _y - _sh - _th, _x + _sw + _th, _y - _sh + _th, false);
    draw_rectangle(_x - _sw - _th, _y - _sh - _th, _x - _sw + _th, _y, false);
    draw_rectangle(_x + _sw - _th, _y - _sh - _th, _x + _sw + _th, _y, false);
    // body
    draw_set_color(c_black);
    draw_rectangle(_x - _w - 1, _y - 1, _x + _w + 1, _y + (_bh * 2) - (_bh div 2) + 1, false);
    draw_set_color(make_color_rgb(255, 200, 40));
    draw_rectangle(_x - _w, _y, _x + _w, _y + (_bh * 2) - (_bh div 2), false);
    draw_set_color(make_color_rgb(255, 240, 150));
    draw_rectangle(_x - _w, _y, _x + _w, _y, false);
    // keyhole
    draw_set_color(make_color_rgb(60, 30, 0));
    var _ky = _y + round(_bh * 0.45);
    draw_rectangle(_x - max(1, round(_k)), _ky, _x + max(1, round(_k)) - 1, _ky + max(2, round(3 * _k)), false);
    draw_set_alpha(1);
    return 1;
}

// a chunky green plus (the heal symbol): arm length _l, half thickness _t, a dark edge
function kbr_plus(_x, _y, _l, _t, _a)
{
    _x = round(_x);
    _y = round(_y);
    _l = round(_l);
    _t = max(1, round(_t));
    draw_set_alpha(_a);
    draw_set_color(make_color_rgb(10, 60, 25));
    draw_rectangle(_x - _l - 1, _y - _t - 1, _x + _l + 1, _y + _t + 1, false);
    draw_rectangle(_x - _t - 1, _y - _l - 1, _x + _t + 1, _y + _l + 1, false);
    draw_set_color(make_color_rgb(70, 230, 110));
    draw_rectangle(_x - _l, _y - _t, _x + _l, _y + _t, false);
    draw_rectangle(_x - _t, _y - _l, _x + _t, _y + _l, false);
    draw_set_color(make_color_rgb(190, 255, 205));
    draw_rectangle(_x - _l, _y - _t, _x - _l + 1, _y - _t, false);
    draw_rectangle(_x - _t, _y - _l, _x - _t, _y - _l + 1, false);
    draw_set_alpha(1);
    return 1;
}

// a sprite drawn with the middle of its own picture at _x, _y, whatever its origin, scale and rotation
function kbr_spr_c(_spr, _img, _x, _y, _xs, _ys, _rot, _col, _a)
{
    // the middle of the sprite's visible pixels (its bounding box), not of its canvas
    var _dx = (((sprite_get_bbox_left(_spr) + sprite_get_bbox_right(_spr) + 1) / 2) - sprite_get_xoffset(_spr)) * _xs;
    var _dy = (((sprite_get_bbox_top(_spr) + sprite_get_bbox_bottom(_spr) + 1) / 2) - sprite_get_yoffset(_spr)) * _ys;
    var _c = dcos(_rot);
    var _s = dsin(_rot);
    var _rx = (_dx * _c) + (_dy * _s);
    var _ry = (-_dx * _s) + (_dy * _c);
    // whole pixels: the game's pixel art stays sharp (no half-pixel smear)
    draw_sprite_ext(_spr, _img, round(_x - _rx), round(_y - _ry), _xs, _ys, _rot, _col, _a);
    return 1;
}

// DRBR: a boss sprite as an icon - centred on its visible pixels, scaled to fit _px (its bigger side), whole pixels
function kbr_icon_fit(_spr, _img, _x, _y, _px, _rot, _col, _a)
{
    if (!sprite_exists(_spr))
        return 0;
    var _w = max(1, (sprite_get_bbox_right(_spr) - sprite_get_bbox_left(_spr)) + 1);
    var _h = max(1, (sprite_get_bbox_bottom(_spr) - sprite_get_bbox_top(_spr)) + 1);
    var _s = _px / max(_w, _h);
    return kbr_spr_c(_spr, _img, _x, _y, _s, _s, _rot, _col, _a);
}

// the SOUL (spr_khub_soul: the game's heart in white, with its outline frame) in colour _c, centred on _x, _y
function kbr_soul_icon(_x, _y, _s, _c, _a, _rot)
{
    if (is_undefined(_rot))
        _rot = 0;
    var _ox = lengthdir_x(10 * _s, _rot + 180) - lengthdir_x(10 * _s, _rot + 270);
    var _oy = lengthdir_y(10 * _s, _rot + 180) - lengthdir_y(10 * _s, _rot + 270);
    draw_sprite_ext(spr_khub_soul, 0, _x + _ox, _y + _oy, _s, _s, _rot, _c, _a);
    return 1;
}

// the log: the last lines, newest at the bottom, typed in; under the skills (left of the box, never over it)
function kbr_hud_log(xx, yy, _M)
{
    draw_set_font(fnt_small);
    var _y = yy + 108;
    // a watcher: under the card of the one they follow (FULL / SMALL / OFF)
    if (_M.out || !_M.me)
    {
        var _sh = kfo_view().shud;
        _y = yy + ((_sh == 0) ? 106 : ((_sh == 1) ? 58 : 8));
    }
    // build 51: 3 lines at most (older ones fainter), right of the TP bar and never over the box: cut to the space left of it
    var _x = xx + 8;
    var _w = 228;
    if (_M.me && !_M.out)
    {
        // build 51: bottom left, just over the targeting strip (the announcements take that place while they show)
        // build 52: and HOW TO PLAY's box
        if ((variable_struct_exists(_M, "bn") && is_struct(_M.bn)) || kfo_tut_on())
            return 1;
        _x = xx + 20;
        _w = 380;
        _y = yy + 366;
        with (obj_growtangle)
        {
            if (bbox_bottom - yy > 360)
                _y = max(_y, bbox_bottom - yy + 4);
        }
        _y = min(_y, yy + 366);
        // build 52: song lyrics on (they sit just over the strip): the feed goes over them
        if (variable_global_exists("klx_vis_ms") && current_time - global.klx_vis_ms < 300)
            _y = yy + 336;
    }
    var _n = array_length(_M.log);
    var _from = max(0, _n - 3);
    for (var _i = _from; _i < _n; _i++)
    {
        var _l = _M.log[_i];
        var _age = (_n - 1) - _i;
        draw_set_alpha(min(1, _l.life / 30) * ((_age == 0) ? 1 : ((_age == 1) ? 0.75 : 0.5)));
        kbr_hud_text(_x, _y, kbr_fit(string_copy(_l.t, 1, _l.n), _w), _l.c);
        _y += 13;
    }
    draw_set_alpha(1);
    return 1;
}

// a line in _w pixels in the font that is set (DRBR 1.0.1: too long, it scrolls by itself - knight_scroll_fit; it was cut "..")
function kbr_fit(_s, _w)
{
    return knight_scroll_fit(_s, _w);
}

// the knight that attacks now, its attack, the stage, the next knight and the clock: between the skills (left) and the
// players (right), every line fitted to that space
function kbr_hud_knight(xx, yy, _M)
{
    draw_set_font(fnt_small);
    draw_set_halign(fa_center);
    var _cx = xx + 363;
    var _w = 192;
    var _t = kbr_now();
    var _k = -1;
    if (_M.R.ph == "run")
        _k = _M.R.k;
    else if (_M.R.ph == "arm")
        _k = _M.R.arm_k;
    else if (_M.R.ph == "idle")
        _k = _M.R.k;
    // build 51: two short lines, nothing unlabelled: the knight (and FINAL TWO / SUDDEN DEATH), then the attack and the time
    // until the next knight or stage (NEXT 0:18); kept left of the Knight's sprite
    _cx = xx + 340;
    _w = 176;
    if (_k >= 0 && _M.go)
    {
        var _c = kbr_tl_get(_M.tl, _k);
        var _l1 = string_upper(kbr_ok_name(_c.ok));
        if (_c.sd)
            _l1 += " - SUDDEN DEATH";
        else if (_c.ft)
            _l1 += " - FINAL TWO";
        scr_84_set_draw_font("main");
        kbr_hud_text(_cx, yy + 4, kbr_fit(_l1, _w), (_c.sd || _c.ft) ? make_color_rgb(255, 90, 90) : kbr_ok_color(_c.ok));
        draw_set_font(fnt_small);
        var _l2 = (_M.R.ph == "run") ? string_upper(kbr_atk_name(_c.ok, _c.ai)) : "";
        var _nt = kbr_hud_next_t(_M, _k);
        if (_M.eff.next && _nt >= 0)
            _l2 += ((_l2 != "") ? "   " : "") + "NEXT " + kfo_time_text(_nt);
        kbr_hud_text(_cx, yy + 22, kbr_fit(_l2, _w), c_white);
        // DRBR: Flowery's GROUP MERCY and the group's ACT (online_flowery53.gml), the stack's first line
        kbr_fl_hud(xx, yy, _M);
    }
    draw_set_halign(fa_left);
    return 1;
}

// build 51: how long until the next knight or stage after cycle _k (ticks, from now), -1 when not known
function kbr_hud_next_t(_M, _k)
{
    var _c = kbr_tl_get(_M.tl, _k);
    var _now = kbr_now();
    for (var _j = _k + 1; _j < _k + 40; _j++)
    {
        var _n = kbr_tl_get(_M.tl, _j);
        if (is_undefined(_n))
            return -1;
        if (_n.ok != _c.ok || _n.st != _c.st)
            return max(0, _n.t0 - _now);
    }
    return -1;
}

// the players: alive first (by HP), then out by place
// build 51: a grid of small player cards (two columns, a gap between them): on top the slot number, the player's SOUL in
// their colour, the name, their SHADOW CRYSTALS (+N when it goes up) and three connection bars; under it a thin HP bar (green /
// yellow / red, the SHIELD in blue, TIRED over it). The card's edge says the rest: yellow = you target them, red = they
// target you, cyan = REFLECTION on; OUT cards are grey with their place. ATTACKING: NAME under the grid for a CHOOSE pick.
function kbr_hud_players(xx, yy, _M)
{
    if (!is_struct(_M.st))
        return 0;
    draw_set_font(fnt_small);
    var _o = global.kfo;
    var _tgon = kbr_tg_on(_M.eff);
    var _pl = _tgon ? kbr_tg_slots(_M, false) : kfo_rank(kfo_ja(_M.st, "pl"));
    var _n = min(8, array_length(_pl));
    var _mine = _tgon ? _M.tg.mine : [];
    var _att = _tgon ? _M.tg.att : [];
    var _choose = _tgon && _M.me && !_M.out && (_M.tg.mode == KBR_TG_CHECK) && array_length(_mine) == 1;
    var _cw = 76;
    var _ch = 19;
    var _gx = 5;
    var _gy = 4;
    var _x0 = xx + 628 - ((2 * _cw) + _gx);
    var _y0 = yy + 8;
    // the least HP of the ones standing (its name pulses red)
    var _low = -1;
    var _lowhp = 999999;
    for (var _i = 0; _i < _n; _i++)
    {
        if (kfo_jn(_pl[_i], "al", 0) == 1 && kfo_jn(_pl[_i], "hp", 0) < _lowhp)
        {
            _lowhp = kfo_jn(_pl[_i], "hp", 0);
            _low = kfo_jn(_pl[_i], "pid", -2);
        }
    }
    if (!variable_struct_exists(_M, "shpop"))
        _M.shpop = {};
    kbr_hud_text(_x0, _y0, "SOULS " + string(kfo_alive_now()) + "/" + string(_M.sn), c_white);
    kfo_net_light(_x0 + (2 * _cw) + _gx - 4, _y0 + 4);
    var _gy0 = _y0 + 12;
    var _pickname = "";
    for (var _i = 0; _i < _n; _i++)
    {
        var _p = _pl[_i];
        var _pid = kfo_jn(_p, "pid", -2);
        var _me = (_pid == _o.my);
        var _al = (kfo_jn(_p, "al", 0) == 1);
        var _col = kbr_pcol(kbr_pslot(_pid));
        var _sk = kfo_jn(_p, "sk", 0);
        var _cx = _x0 + ((_i mod 2) * (_cw + _gx));
        var _cy = _gy0 + ((_i div 2) * (_ch + _gy));
        // the card
        var _edge = make_color_rgb(80, 80, 80);
        if (_al && _tgon && kbr_tg_has(_att, _pid))
            _edge = merge_color(c_red, c_maroon, 0.5 + (0.5 * sin(current_time / 160)));
        if (_al && (_sk & 4) != 0)
            _edge = c_aqua;
        if (_al && _tgon && kbr_tg_has(_mine, _pid))
            _edge = c_yellow;
        if (_me)
            _edge = _al ? merge_color(_edge, c_white, 0.35) : _edge;
        draw_set_alpha(0.8);
        draw_set_color(c_black);
        draw_rectangle(_cx, _cy, _cx + _cw, _cy + _ch, false);
        draw_set_alpha(1);
        draw_set_color(_al ? _edge : make_color_rgb(50, 50, 50));
        draw_rectangle(_cx, _cy, _cx + _cw, _cy + _ch, true);
        draw_rectangle(_cx + 1, _cy + 1, _cx + _cw - 1, _cy + _ch - 1, true);
        // top line: number, SOUL, name, crystals, connection
        if (_tgon)
            kbr_hud_text(_cx + 3, _cy + 3, string(_i + 1), _al ? c_gray : c_dkgray);
        draw_sprite_ext(spr_khub_soul, _al ? 0 : 2, _cx + 8, _cy + 1, 0.45, 0.45, 0, _al ? _col : c_dkgray, 1);
        var _isbot = (kfo_jn(_p, "bot", 0) == 1);
        var _nm = string_upper(string_copy(kfo_js(_p, "n", "?"), 1, _isbot ? 4 : 6));
        var _nc = _me ? c_yellow : (_al ? c_white : c_gray);
        if (_tgon && _al && _pid == _low && array_length(_pl) > 1)
            _nc = merge_color(_nc, c_red, 0.5 + (0.5 * sin(current_time / 140)));
        kbr_hud_text(_cx + 19, _cy + 3, _nm, _nc);
        if (_isbot)
            kbr_hud_text(_cx + 19 + string_width(_nm) + 2, _cy + 3, "B", c_gray);
        if (_tgon && _M.eff.shards && _al)
        {
            var _sh = min(9, kfo_jn(_p, "sh", 0));
            kbr_tg_shard_icon(_cx + 55, _cy + 2);
            kbr_hud_text(_cx + 63, _cy + 3, string(_sh), (_sh > 0) ? c_white : c_dkgray);
            var _key = string(_pid);
            var _pp = variable_struct_exists(_M.shpop, _key) ? variable_struct_get(_M.shpop, _key) : { v: _sh, t: 0, d: 0 };
            if (_sh > _pp.v)
            {
                _pp.d = _sh - _pp.v;
                _pp.t = 45;
            }
            _pp.v = _sh;
            if (_pp.t > 0)
            {
                _pp.t--;
                draw_set_alpha(min(1, _pp.t / 15));
                kbr_hud_text(_cx + 58, _cy - 6 + round(_pp.t / 15), "+" + string(_pp.d), make_color_rgb(200, 140, 255));
                draw_set_alpha(1);
            }
            variable_struct_set(_M.shpop, _key, _pp);
        }
        // the connection: three bars (a bot's are full)
        var _lat = kfo_jn(_p, "lat", -1);
        var _q = _isbot ? 3 : ((_lat < 0) ? 0 : ((_lat < 90) ? 3 : ((_lat < 180) ? 2 : 1)));
        for (var _b = 0; _b < 3; _b++)
        {
            draw_set_color((_b < _q && _al) ? make_color_rgb(70, 230, 110) : make_color_rgb(50, 50, 50));
            draw_rectangle(_cx + 69 + (_b * 2), _cy + 8 - (_b * 2), _cx + 69 + (_b * 2), _cy + 8, false);
        }
        // bottom line: the HP bar
        var _bx = _cx + 4;
        var _bw = _cw - 8;
        var _by = _cy + 12;
        if (_al)
        {
            var _f = clamp(kfo_jn(_p, "hp", 0) / max(1, kfo_jn(_p, "mh", 150)), 0, 1);
            var _hc = (_f > 0.5) ? make_color_rgb(70, 230, 110) : ((_f > 0.25) ? c_yellow : c_red);
            if ((_sk & 2) != 0)
                _hc = merge_color(_hc, c_white, 0.25 + (0.15 * sin(current_time / 200)));
            draw_set_color(make_color_rgb(90, 0, 0));
            draw_rectangle(_bx, _by, _bx + _bw, _by + 3, false);
            // build 50: a SHIELD is a blue part after the HP (the bar full with the blue on top past max HP)
            var _sd = kfo_jn(_p, "sd", 0);
            if ((_sk & 1) != 0 && _sd <= 0)
                _sd = 1;
            var _hpv = kfo_jn(_p, "hp", 0);
            var _mhv = max(1, kfo_jn(_p, "mh", 150));
            var _fs = _f;
            if (_sd > 0 && _hpv + kbr_shield_hp(_sd) > _mhv)
                _fs = _hpv / (_hpv + kbr_shield_hp(_sd));
            if (_f > 0)
            {
                draw_set_color(_hc);
                draw_rectangle(_bx, _by, _bx + max(1, round(_fs * _bw)), _by + 3, false);
                draw_set_color(merge_color(_hc, c_white, 0.45));
                draw_rectangle(_bx, _by, _bx + max(1, round(_fs * _bw)), _by, false);
            }
            if (_sd > 0)
            {
                var _tot = _hpv + kbr_shield_hp(_sd);
                draw_set_color(kbr_shield_col());
                if (_tot <= _mhv)
                    draw_rectangle(_bx + round((_hpv / _mhv) * _bw), _by, _bx + max(1, round((_tot / _mhv) * _bw)), _by + 3, false);
                else
                    draw_rectangle(_bx + round((_hpv / _tot) * _bw), _by, _bx + _bw, _by + 3, false);
            }
            // TIRED (just healed or no charge): the bar striped pale blue, and a small Z where the crystals' count ends
            if (_tgon && kfo_jn(_p, "ti", 0) == 1)
            {
                draw_set_color(make_color_rgb(150, 190, 255));
                for (var _z = 0; _z < _bw; _z += 4)
                    draw_rectangle(_bx + _z, _by + 1, _bx + min(_bw, _z + 1), _by + 2, false);
                kbr_hud_text(_cx + 48, _cy + 3, "z", make_color_rgb(150, 190, 255));
            }
        }
        else
            kbr_hud_text(_bx, _by - 2, kbr_out_text(kfo_jn(_p, "pl", 0)), c_gray);
        if (_choose && _al && _pid == _mine[0])
            _pickname = string_upper(string_copy(kfo_js(_p, "n", "?"), 1, 10));
    }
    if (_pickname != "")
        kbr_hud_text(_x0, _gy0 + ((((_n + 1) div 2)) * (_ch + _gy)), "ATTACKING: " + _pickname, c_yellow);
    return 1;
}

// over the box: the countdown, the wait, OUT - WATCHING
function kbr_hud_center(xx, yy, _M)
{
    var _t = kbr_now();
    var _cx = xx + 320;
    draw_set_halign(fa_center);
    if (_M.R.ph == "wait" || !_M.go)
    {
        var _rd = 0;
        var _all = 0;
        if (is_struct(_M.st))
        {
            var _pl = kfo_ja(_M.st, "pl");
            for (var _i = 0; _i < array_length(_pl); _i++)
            {
                _all++;
                if (kfo_jn(_pl[_i], "rdy", 0) == 1)
                    _rd++;
            }
        }
        draw_set_font(fnt_small);
        kbr_hud_text(_cx, yy + 200, "WAITING FOR EVERYONE'S BATTLE" + ((_all > 0) ? (" (" + string(_rd) + "/" + string(_all) + ")") : "") + "...", c_white);
    }
    else if (_t < _M.tl.intro)
    {
        var _left = ceil((_M.tl.intro - _t) / 30);
        scr_84_set_draw_font("mainbig");
        var _s = (_left > 3) ? string(_left) : ((_left > 0) ? string(_left) : "");
        if (_left <= 3 && _left > 0)
            _s = string(_left) + "...";
        kbr_hud_text(_cx, yy + 190, _s, c_yellow);
        draw_set_font(fnt_small);
        kbr_hud_text(_cx, yy + 226, _M.prac ? "PRACTICE" : "THE LAST SOUL STANDING WINS", c_white);
        // the player's keys (MORE OPTIONS > KEYBINDS changes them; MATCH VIEW > KEY HINTS hides them)
        if (_M.me && kfo_view().hints)
        {
            kbr_hud_text(_cx, yy + 246, kbr_fit(kfo_key_label("breath") + ": HOLD BREATH (TOGGLE)    " + kfo_key_label("charge") + ": CHARGE    " + kfo_key_label("hold") + ": HOLD SLOT", 600), c_ltgray);
            kbr_hud_text(_cx, yy + 260, kbr_fit(kfo_key_label("use") + ": TAP = NEXT SKILL, HOLD = USE IT    X: SLOW (THE GAME'S OWN)", 600), c_ltgray);
            if (kbr_tg_on(_M.eff))
                kbr_hud_text(_cx, yy + 274, kbr_fit(kfo_key_label("tgl") + " / " + kfo_key_label("tgr") + ": TARGETING MODE    " + kfo_key_label("tgn") + " OR 1-8: PICK A TARGET (CHECK)", 600), c_ltgray);
        }
    }
    else if (_t < _M.tl.intro + 30)
    {
        scr_84_set_draw_font("mainbig");
        kbr_hud_text(_cx, yy + 190, "FIGHT!", c_red);
    }
    if (_M.out || !_M.me)
    {
        draw_set_font(fnt_small);
        var _who = "";
        if (_M.spect >= 0 && is_struct(_M.st))
        {
            var _pl2 = kfo_ja(_M.st, "pl");
            for (var _i = 0; _i < array_length(_pl2); _i++)
            {
                if (kfo_jn(_pl2[_i], "pid", -2) == _M.spect)
                    _who = kfo_js(_pl2[_i], "n", "?") + " (" + string(round(kfo_jn(_pl2[_i], "hp", 0))) + " HP)";
            }
        }
        var _head = _M.me ? ((_M.place > 0) ? ("OUT #" + string(_M.place) + " - WATCHING") : "OUT - WATCHING") : "WATCHING";
        kbr_hud_text(_cx, yy + 298, kbr_fit(_head + ((_who != "") ? (": " + _who + "  < >") : ""), 600), c_white);
        if (!kfo_view().help || !kfo_view().hints)
            kbr_hud_text(_cx, yy + 312, kbr_fit(kfo_key_label("quit") + ": BACK TO THE ROOM    " + kfo_key_label("list") + ": EVERYONE", 600), c_gray);
    }
    draw_set_halign(fa_left);
    return 1;
}

// the PLAYER LIST key: everyone in full
function kbr_hud_tab(xx, yy, _M)
{
    if (!is_struct(_M.st))
        return 0;
    var _pl = kfo_rank(kfo_ja(_M.st, "pl"));
    var _x0 = xx + 120;
    var _y0 = yy + 90;
    // build 51: the keys live here now (the hint line under the box is gone): two lines at the bottom
    var _h = 40 + (array_length(_pl) * 22) + 30;
    draw_set_alpha(0.85);
    draw_set_color(c_black);
    draw_rectangle(_x0, _y0, _x0 + 400, _y0 + _h, false);
    draw_set_alpha(1);
    draw_set_color(c_white);
    draw_rectangle(_x0, _y0, _x0 + 400, _y0 + _h, true);
    draw_set_font(fnt_small);
    kbr_hud_text(_x0 + 10, _y0 + _h - 28, kbr_fit("ARROWS MOVE  X SLOW  " + kfo_key_label("breath") + " HOLD BREATH  " + kfo_key_label("charge") + " CHARGE  " + kfo_key_label("use") + " PICK / HOLD: USE  " + kfo_key_label("hold") + " HOLD SLOT", 380), c_ltgray);
    kbr_hud_text(_x0 + 10, _y0 + _h - 15, kbr_fit(kfo_key_label("tgl") + " / " + kfo_key_label("tgr") + " TARGET MODE  " + kfo_key_label("tgn") + " OR 1-8 CHOOSE A PLAYER  T CHAT  BACKSPACE GIVE UP", 380), c_ltgray);
    kbr_hud_text(_x0 + 10, _y0 + 8, "PLAYER", c_gray);
    kbr_hud_text(_x0 + 150, _y0 + 8, "HP", c_gray);
    kbr_hud_text(_x0 + 230, _y0 + 8, "GAUGE", c_gray);
    kbr_hud_text(_x0 + 290, _y0 + 8, "SKILLS", c_gray);
    kbr_hud_text(_x0 + 350, _y0 + 8, "PING", c_gray);
    for (var _i = 0; _i < array_length(_pl); _i++)
    {
        var _p = _pl[_i];
        var _y = _y0 + 28 + (_i * 22);
        var _al = (kfo_jn(_p, "al", 0) == 1);
        var _me = (kfo_jn(_p, "pid", -2) == global.kfo.my);
        kbr_hud_text(_x0 + 10, _y, kfo_js(_p, "n", "?") + ((kfo_jn(_p, "bot", 0) == 1) ? " (BOT)" : ""), _me ? c_yellow : (_al ? c_white : c_gray));
        kbr_hud_text(_x0 + 150, _y, _al ? (string(round(kfo_jn(_p, "hp", 0))) + "/" + string(round(kfo_jn(_p, "mh", 0)))) : (kbr_out_text(kfo_jn(_p, "pl", 0))), _al ? c_white : c_gray);
        kbr_hud_text(_x0 + 230, _y, string(floor(kfo_jn(_p, "g", 0))), c_orange);
        kbr_hud_text(_x0 + 290, _y, string(kfo_jn(_p, "sg", 0)) + "/" + string(kfo_jn(_p, "sr", 0)), c_white);
        var _lat = kfo_jn(_p, "lat", -1);
        kbr_hud_text(_x0 + 350, _y, (kfo_jn(_p, "bot", 0) == 1) ? "-" : ((_lat >= 0) ? (string(_lat) + "ms") : "?"), c_ltgray);
    }
    return 1;
}
