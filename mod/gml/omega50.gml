// ===== Build 50: OMEGA FLOWERY's rendering (obj_knight_omega) =====
// Recreated from Chapter 5's own drawing of Omega Flowery and his flowers (obj_plat_finalflowery: its Draw and draw_ghost):
//   - Omega Flowery: an outline 2 px around him in a hue that cycles (scr_draw_outline(2, hsv colour) - make_color_hsv of
//     hsvslider, +0.3 a frame), his white sprite at alpha 0.8, then an ADDITIVE pass of shd_chromatic_reflection: a rainbow
//     that runs diagonally across the screen (hue = 0.5 + frac((time + (x + y) * 0.01) * 0.5), full saturation), only
//     where the sprite is (its alpha), at iAlpha 0.5;
//   - a flower (draw_ghost): its OVERLAY sprite (_o: the solid shape behind it) in its colour darkened 20%, its main sprite
//     (white with grey details) in #EEEEEE mixed half with its colour, then the same additive rainbow pass.
// The chromatic pass is done without a custom shader (Chapter 5's shader is not in Chapter 3's game file): the sprite is
// drawn into a surface, the diagonal rainbow is multiplied onto it by the surface's own alpha (colour writes only), and the
// surface is added onto the screen. The rainbow is in screen space like the shader's, so it flows across him as he moves;
// the sprite's own alpha decides where it shows (no rectangle, nothing outside the sprite).
// kinds: 0 Omega Flowery (srcspr: another of his sprites whose frame is mapped onto his Omega frames; -1: Omega frames as
// they are), 1 a flower (spr + ovl + col), 2 a ring (a ripple: radius r0 -> r1 over life, width w), 3 an orb (filled
// circle, white, growing and fading), 4 his permanent Omega form following his battle hero (the Violet Knight's last stand).

global.knight_om_surf = -1;

function knight_om_hue()
{
    // Chapter 5: hsvslider += 0.3 a frame, colour = make_color_hsv(((hsvslider / 14) * 255) % 255, 255, 255)
    return make_color_hsv((((current_time / 33.3) * 0.3 / 14) * 255) mod 255, 255, 255);
}

// the diagonal rainbow's colour at screen position _s (= x - y, the shader's fragment x + y with y from the bottom)
function knight_om_band(_s)
{
    var _t = current_time * 0.035 * 2 * 0.033;
    var _h = 0.5 + frac((_t + (_s * 0.01)) * 0.5);
    _h = frac(_h);
    return make_color_hsv(_h * 255, 255, 255);
}

// the additive rainbow pass over sprite _spr frame _f drawn at x, y (scale _xs, _ys), strength _a
function knight_om_chroma(_spr, _f, _x, _y, _xs, _ys, _a)
{
    if (_a <= 0 || !sprite_exists(_spr))
        return 0;
    if (!surface_exists(global.knight_om_surf))
        global.knight_om_surf = surface_create(320, 320);
    var _S = global.knight_om_surf;
    surface_set_target(_S);
    draw_clear_alpha(c_black, 0);
    draw_sprite_ext(_spr, _f, 160, 160, _xs, _ys, 0, c_white, 1);
    gpu_set_colorwriteenable(true, true, true, false);
    gpu_set_blendmode_ext(bm_dest_alpha, bm_zero);
    var _base = (_x - 160) - (_y - 160);
    draw_primitive_begin(pr_trianglelist);
    for (var _u = -336; _u < 336; _u += 16)
    {
        var _c0 = knight_om_band(_base + _u);
        var _c1 = knight_om_band(_base + _u + 16);
        // the band between the lines px - py = _u and px - py = _u + 16, across the whole surface
        draw_vertex_colour(_u - 336, -336, _c0, 1);
        draw_vertex_colour(_u + 656, 656, _c0, 1);
        draw_vertex_colour(_u + 16 + 656, 656, _c1, 1);
        draw_vertex_colour(_u - 336, -336, _c0, 1);
        draw_vertex_colour(_u + 16 + 656, 656, _c1, 1);
        draw_vertex_colour(_u + 16 - 336, -336, _c1, 1);
    }
    draw_primitive_end();
    gpu_set_colorwriteenable(true, true, true, true);
    gpu_set_blendmode(bm_normal);
    surface_reset_target();
    gpu_set_blendmode(bm_add);
    draw_surface_ext(_S, _x - 160, _y - 160, 1, 1, 0, c_white, _a);
    gpu_set_blendmode(bm_normal);
    return 1;
}

// the outline: the sprite as a solid colour 2 px off in four directions (scr_draw_outline)
function knight_om_outline(_spr, _f, _x, _y, _xs, _ys, _col, _a)
{
    gpu_set_fog(true, _col, 0, 0);
    draw_sprite_ext(_spr, _f, _x + 2, _y, _xs, _ys, 0, c_white, _a);
    draw_sprite_ext(_spr, _f, _x - 2, _y, _xs, _ys, 0, c_white, _a);
    draw_sprite_ext(_spr, _f, _x, _y + 2, _xs, _ys, 0, c_white, _a);
    draw_sprite_ext(_spr, _f, _x, _y - 2, _xs, _ys, 0, c_white, _a);
    gpu_set_fog(false, c_white, 0, 0);
    return 1;
}

// his Omega frame for a frame of one of his other sprites (so every move of his shows as Omega Flowery once he has
// transformed): spr_knfl_omega = pose 0-2, power-up 3-5, rush 6-8, clash 9-11, wind-up 12-16, punch 17-19, idle 20-22,
// hurt 23, deflect 24-26
function knight_om_frame(_src, _i)
{
    var _a = knight_fl_a();
    var _n = max(0, floor(_i));
    var _t3 = (current_time div 120) mod 3;
    if (_src < 0 || _src == _a.omega)
        return _n mod 27;
    if (_src == _a.jarona)
    {
        if (_n <= 4)
            return 12 + _n;
        if (_n == 5)
            return 17 + _t3;
        return 24 + _t3;
    }
    if (_src == _a.attack)
        return (_n <= 3) ? (12 + _n) : ((_n >= 6) ? (20 + _t3) : (17 + (_n - 4)));
    if (_src == _a.ready)
        return 12;
    if (_src == _a.flashkick)
        return (_n == 0) ? (6 + _t3) : ((_n == 1) ? 12 : 17);
    if (_src == _a.runner)
        return (_n <= 3) ? (6 + (_n mod 3)) : ((_n == 4) ? 12 : 17);
    if (_src == _a.spell || _src == _a.spellready || _src == asset_get_index("spr_knfl_powerup"))
        return 3 + _t3;
    if (_src == _a.hurt || _src == _a.defeat)
        return 23;
    if (_src == _a.defend)
        return 24 + _t3;
    if (_src == _a.idle || _src == _a.walk)
        return 20 + _t3;
    return _t3;
}

// a new Omega drawing (depth -5 like the move markers); _kind as above
function knight_om_make(_kind, _x, _y)
{
    var _o = instance_create_depth(_x, _y, -5, obj_knight_omega);
    _o.kind = _kind;
    return _o;
}

// a ripple ring (Chapter 5's make_bwoosh: scr_make_ripple in a flower colour)
function knight_om_ring(_x, _y, _r0, _r1, _w, _col, _life)
{
    var _o = knight_om_make(2, _x, _y);
    _o.r0 = _r0;
    _o.r1 = _r1;
    _o.w = _w;
    _o.col = _col;
    _o.life = _life;
    _o.depth = -21;
    return _o;
}

function knight_om_orb(_x, _y, _r0, _r1, _col, _life)
{
    var _o = knight_om_make(3, _x, _y);
    _o.r0 = _r0;
    _o.r1 = _r1;
    _o.col = _col;
    _o.life = _life;
    _o.depth = -22;
    return _o;
}

// Chapter 5's Omega explosions: white, then a random flower hue after 2 or 4 frames
function knight_om_boom(_x, _y, _sc)
{
    var _a = knight_fl_a();
    var _e = knight_fl_fx1(_a.o_ex[irandom(2)], _x, _y, _sc, c_white, 0.5);
    if (i_ex(_e))
    {
        var _hc = make_color_hsv((irandom_range(1, 6) / 7) * 255, 255, 255);
        with (_e)
            scr_delay_var("image_blend", _hc, choose(2, 4));
    }
    return _e;
}

// --- obj_knight_omega's events ---
function knight_om_create()
{
    kind = 0;
    srcspr = -1;
    ovl = -1;
    col = c_white;
    a = 1;
    t = 0;
    life = 20;
    r0 = 0;
    r1 = 40;
    w = 6;
    hero = noone;
    gone = false;
    front = false;
    image_xscale = 2;
    image_yscale = 2;
    image_speed = 0;
    return 1;
}

function knight_om_step()
{
    t++;
    if ((kind == 2 || kind == 3) && t >= life)
    {
        instance_destroy();
        return 0;
    }
    if (kind == 5 || kind == 6)
    {
        // a guard on someone (5: Afinihug's shield on a member; 6: Honey Kiss's charm on the foe): it follows them, fades in,
        // and fades out once it is let go (gone = true)
        if (!i_ex(hero))
        {
            instance_destroy();
            return 0;
        }
        x = (hero.bbox_left + hero.bbox_right) / 2;
        y = (hero.bbox_top + hero.bbox_bottom) / 2;
        depth = hero.depth - 2;
        a = gone ? max(0, a - 0.1) : min(1, a + 0.1);
        if (gone && a <= 0)
            instance_destroy();
    }
    if (kind == 4)
    {
        // his permanent Omega form's aura on his battle hero (which wears the Omega poses): behind it, or in front of it
        if (!i_ex(hero))
        {
            instance_destroy();
            return 0;
        }
        x = hero.x;
        y = hero.y;
        depth = front ? (hero.depth - 1) : (hero.depth + 1);
    }
    return 1;
}

function knight_om_draw()
{
    if (kind == 5 || kind == 6)
        return knight_om_draw_guard();
    if (kind == 2)
    {
        var _p = t / max(1, life);
        var _e = 1 - power(1 - _p, 3);
        var _r = lerp(r0, r1, _e);
        var _ww = max(1, w * (1 - (_p * 0.7)));
        draw_set_alpha(1 - _p);
        draw_primitive_begin(pr_trianglestrip);
        for (var _i = 0; _i <= 32; _i++)
        {
            var _an = (_i / 32) * 360;
            draw_vertex_colour(x + lengthdir_x(_r, _an), y + lengthdir_y(_r, _an), col, 1 - _p);
            draw_vertex_colour(x + lengthdir_x(_r + _ww, _an), y + lengthdir_y(_r + _ww, _an), col, 1 - _p);
        }
        draw_primitive_end();
        draw_set_alpha(1);
        return 1;
    }
    if (kind == 3)
    {
        var _p3 = t / max(1, life);
        draw_set_alpha(1 - _p3);
        draw_set_colour(col);
        draw_circle(x, y, lerp(r0, r1, 1 - power(1 - _p3, 2)), false);
        draw_set_alpha(1);
        draw_set_colour(c_white);
        return 1;
    }
    if (a <= 0 || !sprite_exists(sprite_index))
        return 0;
    if (kind == 1)
    {
        // a flower (draw_ghost)
        var _f1 = floor(image_index) mod max(1, sprite_get_number(sprite_index));
        if (sprite_exists(ovl))
            draw_sprite_ext(ovl, _f1, x, y, image_xscale, image_yscale, 0, merge_color(col, c_black, 0.2), a * image_alpha);
        draw_sprite_ext(sprite_index, _f1, x, y, image_xscale, image_yscale, 0, merge_color(make_color_rgb(238, 238, 238), col, 0.5), a * image_alpha);
        knight_om_chroma(sprite_index, _f1, x, y, image_xscale, image_yscale, 0.45 * a * image_alpha);
        return 1;
    }
    if (kind == 4)
    {
        // the aura: the hero's own pose (thissprite / index, what obj_heroparent draws) - the cycling outline behind, the
        // chroma shine in front; nothing while he is hidden (in a move, his Omega drawing is the move's own)
        if (knight_fl_busy() || !i_ex(hero) || !hero.visible || hero.image_alpha <= 0)
            return 0;
        var _hs = variable_instance_exists(hero, "thissprite") ? hero.thissprite : hero.sprite_index;
        var _hi = variable_instance_exists(hero, "index") ? hero.index : hero.image_index;
        if (!sprite_exists(_hs))
            return 0;
        var _hf = floor(_hi) mod max(1, sprite_get_number(_hs));
        if (front)
            knight_om_chroma(_hs, _hf, hero.x, hero.y, hero.image_xscale, hero.image_yscale, 0.4 * hero.image_alpha);
        else
            knight_om_outline(_hs, _hf, hero.x, hero.y, hero.image_xscale, hero.image_yscale, knight_om_hue(), hero.image_alpha);
        return 1;
    }
    // Omega Flowery
    var _src = srcspr;
    var _fi = image_index;
    var _f = knight_om_frame(_src, _fi);
    var _al = a * image_alpha;
    knight_om_outline(sprite_index, _f, x, y, image_xscale, image_yscale, knight_om_hue(), _al);
    draw_sprite_ext(sprite_index, _f, x, y, image_xscale, image_yscale, 0, c_white, 0.8 * _al);
    knight_om_chroma(sprite_index, _f, x, y, image_xscale, image_yscale, 0.45 * _al);
    return 1;
}

// Afinihug's shield (kind 5): a golden bubble round the member - a soft fill that breathes, a bright rim, two glints
// running round it, little sparkles rising; Honey Kiss's charm (kind 6): a pink ring round the foe with hearts drifting up
function knight_om_draw_guard()
{
    if (!i_ex(hero) || a <= 0 || (variable_instance_exists(hero, "visible") && !hero.visible))
        return 0;
    var _r = max(28, min(64, (hero.bbox_right - hero.bbox_left) * 0.6 + 10));
    var _ry = max(_r, min(80, (hero.bbox_bottom - hero.bbox_top) * 0.55 + 6));
    var _col = (kind == 5) ? make_color_rgb(255, 214, 80) : make_color_rgb(255, 120, 190);
    var _br = 0.12 + 0.06 * sin(t / 10);
    // the fill
    draw_set_alpha(_br * a);
    draw_set_colour(_col);
    draw_ellipse(x - _r, y - _ry, x + _r, y + _ry, false);
    // the rim (3 px)
    draw_set_alpha(0.75 * a);
    for (var _w = 0; _w < 3; _w++)
        draw_ellipse(x - _r - _w, y - _ry - _w, x + _r + _w, y + _ry + _w, true);
    // two glints running round the rim
    draw_set_colour(c_white);
    for (var _g = 0; _g < 2; _g++)
    {
        var _an = (t * 4) + (_g * 180);
        draw_set_alpha(0.9 * a);
        draw_circle(x + lengthdir_x(_r + 1, _an), y + lengthdir_y(_ry + 1, _an), 3, false);
    }
    draw_set_alpha(1);
    draw_set_colour(c_white);
    // sparkles (or hearts) rising every so often
    if ((t mod 12) == 0 && !gone)
    {
        var _ss = asset_get_index((kind == 5) ? "spr_sparestar_anim" : "spr_heart");
        if (_ss >= 0 && sprite_exists(_ss))
        {
            var _e = knight_fl_fx1(_ss, x + irandom_range(-_r, _r), y + irandom_range(-_ry div 2, _ry), (kind == 5) ? 2 : 0.5, _col, 0.2);
            if (i_ex(_e))
            {
                _e.vspeed = -1.2;
                _e.depth = depth - 1;
            }
        }
    }
    return 1;
}

// make sure the guard of kind _kind is on _who while _on (one each), and let it go when not
function knight_om_guard_set(_slot, _kind, _who, _on)
{
    if (!variable_global_exists("knight_om_guards") || !is_array(global.knight_om_guards))
        global.knight_om_guards = [noone, noone, noone, noone];
    var _g = global.knight_om_guards[_slot];
    if (_on && i_ex(_who))
    {
        if (!i_ex(_g) || _g.gone || _g.hero != _who)
        {
            if (i_ex(_g))
                _g.gone = true;
            _g = knight_om_make(_kind, _who.x, _who.y);
            _g.hero = _who;
            _g.a = 0;
            global.knight_om_guards[_slot] = _g;
            knight_om_ring((_who.bbox_left + _who.bbox_right) / 2, (_who.bbox_top + _who.bbox_bottom) / 2, 10, 60, 4, (_kind == 5) ? make_color_rgb(255, 214, 80) : make_color_rgb(255, 120, 190), 14);
            snd_play(snd_bell);
        }
        return _g;
    }
    if (i_ex(_g))
        _g.gone = true;
    global.knight_om_guards[_slot] = noone;
    return noone;
}
