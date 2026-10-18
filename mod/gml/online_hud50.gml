
// ===== Build 50: the TP bar as the one skill meter, and the SHIELD in blue on the party's HP bar =====

// ---------- the TP bar (obj_tensionbar's Draw asks first: det_sent.py puts the call at its top) ----------
// One meter, drawn with the game's own TP bar art (the knight's bar sprite, its cutout, the TP logo, the marker, the
// percent in the game's font): the TP bar shows the skill gauge, 0 to 100% (it fills and is spent exactly as before - only where it is shown
// changed: the small charge bar under the skill slots is gone).
//   - the draw cost (60 at 100% SKILL COST) is a white line across the bar, slanted like the bar's own "/" ends: dim below it,
//     lit (and flashing a moment) once the bar reaches it, and flashing again when the charge you hold reaches it;
//   - orange under the line, a brighter gold above it, the whole bar flashing white at 100 (the percent reads MAX);
//   - Deltarune's red section shows what the bar will lose when you let go of CHARGE (the skills you draw), then runs down
//     after the drop as in the game;
//   - YOU DREW A SKILL! / YOU DREW TWO SKILLS! pops beside the bar when the skills are drawn.
function kbr_tp_hook()
{
    if (!kbr_on())
        return false;
    var _M = kbr_match();
    if (is_undefined(_M) || !_M.eff.skills)
        return false;
    // DRBR 1.0.3: watching someone - the bar is theirs (their gauge, as the standings say)
    var _wp = kbr_cb_watched_p(_M);
    if (is_struct(_wp))
    {
        kbr_tp_draw_g(_M, clamp(kfo_jn(_wp, "g", 0), 0, 100), 0, undefined);
        return true;
    }
    if (!_M.me || _M.out)
        return false;
    kbr_tp_draw(_M);
    return true;
}

function kbr_tp_draw(_M)
{
    var _S = _M.sk;
    return kbr_tp_draw_g(_M, clamp(_M.g, 0, 100), _S.charging ? floor(_S.charge) : 0, _S);
}

// the bar for gauge _g (0-100) with charge _ch held (0: none); _S the player's skills (YOU DREW A SKILL!), undefined when
// it is someone you watch
function kbr_tp_draw_g(_M, _g, _ch, _S)
{
    // the game's own TP bar art for the knight that is fighting (as obj_tensionbar's Draw picks it): Kaizo's, Elecknight's
    // (blue when its bar is), the Violet Knight's side B, the Chapter 3 bar for the others
    var _kv = global.knight_variant;
    var _bg = spr_tensionbar;
    var _bgi = 1;
    var _fg = spr_tensionbar;
    if (_kv == 1)
    {
        _bg = spr_tensionbar__v1;
        _fg = spr_tensionbar__v1;
    }
    else if (_kv == 2)
    {
        _bg = spr_tensionbar__v2;
        _fg = spr_tensionbar__v2;
        if (variable_instance_exists(id, "bluebar") && bluebar == true)
            _bgi = 2;
    }
    else if (_kv == 3 && violet_sideb())
        _bg = spr_tensionbar_c;
    var _w = sprite_get_width(_fg);
    var _h = sprite_get_height(_fg);
    var _need = clamp(kbr_skill_need(), 1, 100);
    var _need2 = clamp(kbr_skill_need2(), _need, 100);
    if (!variable_instance_exists(id, "kbrtp_red"))
    {
        kbrtp_red = _g;
        kbrtp_rt = 0;
        kbrtp_was = _g;
        kbrtp_cwas = 0;
        kbrtp_fl = 0;
        kbrtp_t = 0;
    }
    kbrtp_t++;
    // crossing the line: the bar reaching the draw cost, the held charge reaching it, the charge reaching two skills
    if ((kbrtp_was < _need && _g >= _need) || (kbrtp_cwas < _need && _ch >= _need) || (kbrtp_cwas < _need2 && _ch >= _need2))
        kbrtp_fl = 24;
    kbrtp_was = _g;
    kbrtp_cwas = _ch;
    if (kbrtp_fl > 0)
        kbrtp_fl--;
    // the red section after a drop: it waits a moment, then runs down to the bar (Deltarune's own)
    if (_g >= kbrtp_red)
    {
        kbrtp_red = _g;
        kbrtp_rt = 0;
    }
    else
    {
        kbrtp_rt++;
        if (kbrtp_rt > 15)
            kbrtp_red = max(_g, kbrtp_red - max(1, (kbrtp_red - _g) * 0.15));
    }
    // the bar's place (as obj_tensionbar's own Draw puts it)
    // build 51: 44 pixels lower than the game's own place, under the skill diamonds' staggered rows
    y = camera_get_view_y(view_camera[0]) + 96 + (variable_instance_exists(id, "yoffset") ? yoffset : 0);
    if (!surface_exists(healthbar_surf))
        healthbar_surf = surface_create(96, 250);
    surface_set_target(healthbar_surf);
    draw_clear_alpha(c_white, 0);
    draw_sprite(_bg, _bgi, 0, 0);
    var _yf = _h - ((_g / 100) * _h);
    var _yc = _h - ((_need / 100) * _h);
    var _max = (_g >= 100);
    var _wf = 0.5 + (0.5 * sin(kbrtp_t / 3));
    var _or = c_orange;
    var _gold = make_color_rgb(255, 214, 64);
    // the red section behind the fill: what a drop took (still running down)
    if (kbrtp_red > _g)
    {
        draw_set_color(c_red);
        draw_rectangle(3, _h - 1, _w - 1, _h - ((kbrtp_red / 100) * _h), false);
    }
    // the fill, column by column: orange under the slanted line, gold above it
    if (_g > 0)
    {
        for (var _x = 3; _x < _w; _x++)
        {
            var _yb = _yc + (12 - _x);
            var _co = _max ? merge_color(_or, c_white, _wf) : _or;
            var _cg = _max ? merge_color(_gold, c_white, _wf) : _gold;
            draw_set_color(_co);
            draw_rectangle(_x, _h - 1, _x, max(_yf, _yb), false);
            if (_yf < _yb)
            {
                draw_set_color(_cg);
                draw_rectangle(_x, _yb, _x, _yf, false);
            }
        }
    }
    // the red preview: what letting go of CHARGE takes off the bar (nothing is drawn below the cost: dim then)
    if (_ch > 0)
    {
        draw_set_alpha((_ch >= _need) ? 1 : 0.4);
        draw_set_color(c_red);
        draw_rectangle(3, _yf, _w - 1, _h - ((max(0, _g - _ch) / 100) * _h), false);
        draw_set_alpha(1);
    }
    // the draw cost's line, slanted like the bar's ends: dim below, lit above, flashing when crossed
    var _la = (_g >= _need || _ch >= _need) ? 1 : 0.35;
    if (kbrtp_fl > 0 && ((kbrtp_fl div 3) mod 2) == 0)
        _la = 1;
    draw_set_alpha(_la);
    draw_set_color((kbrtp_fl > 0) ? merge_color(c_white, c_yellow, ((kbrtp_fl div 3) mod 2) ? 0.6 : 0) : c_white);
    draw_line_width(3, _yc + 9, _w - 3, (_yc + 12) - (_w - 3), 2);
    draw_set_alpha(1);
    if (_g > 2 && _g < 100)
        draw_sprite(spr_tensionmarker, 0, 3, _yf);
    draw_sprite(_fg, 0, 0, 0);
    gpu_set_blendmode(bm_subtract);
    draw_sprite_ext(spr_tensionbar_cutout, 0, 0, 0, 1, 1, 0, c_white, 1);
    gpu_set_blendmode(bm_normal);
    surface_reset_target();
    draw_surface(healthbar_surf, x, y);
    draw_sprite(spr_tplogo, 0, x - 30, y + 30);
    // the percent, MAX at 100 (as the game writes them)
    draw_set_color(c_white);
    scr_84_set_draw_font("mainbig");
    if (!_max)
    {
        draw_text(x - 30, y + 70, string_hash_to_newline(string(floor(_g))));
        draw_text(x - 25, y + 95, string_hash_to_newline(stringsetloc("%", "obj_tensionbar_slash_Draw_0_gml_18_0")));
    }
    else
    {
        draw_set_color(merge_color(c_yellow, c_white, _wf));
        draw_text(x - 28, y + 70, string_hash_to_newline(stringsetloc("M", "obj_tensionbar_slash_Draw_0_gml_25_0")));
        draw_text(x - 24, y + 90, string_hash_to_newline(stringsetloc("A", "obj_tensionbar_slash_Draw_0_gml_26_0")));
        draw_text(x - 20, y + 110, string_hash_to_newline(stringsetloc("X", "obj_tensionbar_slash_Draw_0_gml_27_0")));
    }
    draw_set_color(c_white);
    if (is_struct(_S))
        kbr_tp_pop(_S, x + _w + 6, y + _yc);
    return 1;
}

// YOU DREW A SKILL! beside the bar, at the line: it pops in, holds, and fades
function kbr_tp_pop(_S, _x, _y)
{
    if (!variable_struct_exists(_S, "pop_t") || _S.pop_t <= 0)
        return 0;
    _S.pop_t--;
    var _u = 50 - _S.pop_t;
    var _sc = (_u < 4) ? (0.6 + (_u * 0.2)) : ((_u < 8) ? (1.4 - ((_u - 4) * 0.1)) : 1);
    var _a = min(1, _S.pop_t / 12);
    var _txt = (_S.pop_n > 1) ? "YOU DREW TWO SKILLS!" : "YOU DREW A SKILL!";
    scr_84_set_draw_font("main");
    draw_set_alpha(_a);
    draw_set_color(c_black);
    draw_text_transformed(_x + 1, _y - 8 + 1, _txt, _sc, _sc, 0);
    draw_set_color((_S.pop_n > 1) ? make_color_rgb(255, 214, 64) : c_white);
    draw_text_transformed(_x, _y - 8, _txt, _sc, _sc, 0);
    draw_set_alpha(1);
    draw_set_color(c_white);
    return 1;
}

// ---------- SHIELD on the party's HP bar ----------
// Each SHIELD hit is shown as one ordinary Knight hit (16 HP x the room's DAMAGE): a blue part after the coloured HP, the bar
// full with the blue on top when HP + shield is over max HP, a blue +N left of the HP numbers (the Deltarune HP font), the
// blue shrinking like HP loss and a short break (a flash, its pieces, a sound) when the last hit breaks it.
function kbr_shield_hp(_hits)
{
    var _M = kbr_match();
    var _dm = is_undefined(_M) ? 1 : (_M.eff.dmul / 100);
    return round(_hits * 16 * _dm);
}

function kbr_shield_col()
{
    return make_color_rgb(70, 140, 255);
}

// DRBR 1.0.3: the SHIELD of the one you watch on your (their) box: their hits left (the standings' sd), as it stands
function kbr_shield_draw_of(_x, _y, _p)
{
    var _sh = kbr_shield_hp(kfo_jn(_p, "sd", 0));
    if (_sh <= 0)
        return 0;
    var _hp = max(0, round(kfo_jn(_p, "hp", 0)));
    var _mh = max(1, round(kfo_jn(_p, "mh", 1)));
    var _bx0 = _x + 128;
    var _by0 = _y + 11;
    var _by1 = _y + 19;
    var _col = kbr_shield_col();
    var _tot = _hp + _sh;
    draw_set_color(_col);
    if (_tot <= _mh)
        draw_rectangle(_bx0 + max(0, ceil((_hp / _mh) * 75)), _by0, _bx0 + ceil((_tot / _mh) * 75), _by1, false);
    else
        draw_rectangle(_bx0 + floor((_hp / _tot) * 75), _by0, _bx0 + 75, _by1, false);
    draw_set_font(global.hpfont);
    var _txt = "+" + string(_sh);
    draw_set_halign(fa_right);
    draw_text(max(_x + 107 + string_width(_txt), (_x + 160) - string_width(string(_hp)) - 3), _y - 2, _txt);
    draw_set_halign(fa_left);
    return 1;
}

// from scr_charbox (det_sent.py adds the call after the HP bar): _x the box's left (xx + xchunk), _y its top line
// (bpoff + b_offset + mmy), _c the party slot's character - 1
function kbr_shield_draw(_x, _y, _c)
{
    if (global.kbr_san <= 0 || !kbr_on())
        return 0;
    var _M = kbr_match();
    // DRBR 1.0.3: watching someone - your box is theirs: their SHIELD on their HP
    if (!is_undefined(_M) && (_c + 1) == kbr_char())
    {
        var _wp = kbr_cb_watched(_c + 1);
        if (is_struct(_wp))
            return kbr_shield_draw_of(_x, _y, _wp);
    }
    if (is_undefined(_M) || !_M.me || _M.out || (_c + 1) != kbr_char())
        return 0;
    var _S = _M.sk;
    var _sh = kbr_shield_hp(_S.shield);
    if (!variable_struct_exists(_S, "shd"))
    {
        _S.shd = _sh;
        _S.shbrk = 0;
        _S.shwas = _S.shield;
    }
    // shrinks like HP loss (a moment, then down); a new shield shows at once
    if (_sh >= _S.shd)
        _S.shd = _sh;
    else
        _S.shd = max(_sh, _S.shd - max(1, (_S.shd - _sh) * 0.2));
    // the last hit of the shield: it breaks (not when it simply runs out of time)
    if (_S.shwas > 0 && _S.shield == 0)
    {
        // (it ran out of time: no break, the blue just runs down)
        if (variable_struct_exists(_S, "shlast") && _S.shlast <= 1)
            _S.shbrk = 0;
        else
        {
            _S.shbrk = 16;
            snd_play(snd_break1, 0.7, 1.2);
        }
    }
    _S.shwas = _S.shield;
    _S.shlast = _S.shield_t;
    var _hp = max(0, global.hp[_c + 1]);
    var _mh = max(1, global.maxhp[_c + 1]);
    var _bx0 = _x + 128;
    var _by0 = _y + 11;
    var _by1 = _y + 19;
    var _col = kbr_shield_col();
    if (_S.shd > 0.5)
    {
        var _tot = _hp + _S.shd;
        if (_tot <= _mh)
        {
            var _a = ceil((_hp / _mh) * 75);
            var _b = ceil((_tot / _mh) * 75);
            draw_set_color(_col);
            draw_rectangle(_bx0 + max(0, _a), _by0, _bx0 + _b, _by1, false);
        }
        else
        {
            // over max HP: the bar is full - the HP's colour, the blue on top of it
            var _a2 = floor((_hp / _tot) * 75);
            draw_set_color(_col);
            draw_rectangle(_bx0 + _a2, _by0, _bx0 + 75, _by1, false);
        }
        // +N in blue, in the HP numbers' own font, right before the HP (never over the name or the numbers)
        if (_sh > 0)
        {
            draw_set_font(global.hpfont);
            var _hw = string_width(string(global.hp[_c + 1]));
            var _txt = "+" + string(_sh);
            draw_set_halign(fa_right);
            draw_set_color(_col);
            draw_text(max(_x + 107 + string_width(_txt), (_x + 160) - _hw - 3), _y - 2, _txt);
            draw_set_halign(fa_left);
        }
    }
    // the break: a white flash where the blue was, and its pieces falling
    if (_S.shbrk > 0)
    {
        _S.shbrk--;
        var _u = 16 - _S.shbrk;
        var _xa = _bx0 + min(75, ceil((_hp / _mh) * 75));
        draw_set_alpha(_S.shbrk / 16);
        draw_set_color(c_white);
        draw_rectangle(_xa, _by0, min(_bx0 + 75, _xa + 20), _by1, false);
        draw_set_color(_col);
        for (var _k = 0; _k < 5; _k++)
        {
            var _px = _xa + 2 + (_k * 4) + (((_k mod 2) == 0) ? -1 : 1) * (_u * 0.6);
            var _py = _by0 + 2 + ((_u * _u) * 0.08) + (_k mod 3);
            draw_rectangle(_px, _py, _px + 1, _py + 1, false);
        }
        draw_set_alpha(1);
    }
    draw_set_color(c_white);
    return 1;
}

// the live player list: another player's shield as a blue part on their bar (sd: their shield hits, from the standings)
function kbr_shield_list(_bx, _y, _bw, _hp, _mh, _sd)
{
    if (_sd <= 0)
        return 0;
    var _s = kbr_shield_hp(_sd);
    var _tot = _hp + _s;
    draw_set_color(kbr_shield_col());
    if (_tot <= _mh)
        draw_rectangle(_bx + round((_hp / _mh) * _bw), _y + 3, _bx + max(1, round((_tot / _mh) * _bw)), _y + 9, false);
    else
        draw_rectangle(_bx + round((_hp / _tot) * _bw), _y + 3, _bx + _bw, _y + 9, false);
    return 1;
}
