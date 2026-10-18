
// ===== Build 47: how YOU see the online match - the other SOULs, your own SOUL's colour, watching, quick settings =====
// Everything in this file is this game's own presentation (knightfights_online.ini [view] and [look]). None of it changes
// the match: hits, grazes, skills, the timeline, the knights and every SOUL's real position are decided exactly as before,
// whatever is (or is not) drawn. The one thing other games learn is your SOUL colour (a number in your player state).

// ---------- the settings ----------
// [view]: the other SOULs (MORE OPTIONS > SOUL VISIBILITY), watching and the match screen (MORE OPTIONS > MATCH VIEW)
function kfo_view_default()
{
    return {
        show: 1,    // SHOW OTHER SOULS
        sop: 70,    // OTHER SOUL OPACITY, 0-100 (a slider in 5% steps); 70%: clearly seen, yours stays full (build 48)
        names: 0,   // SHOW PLAYER NAMES
        nop: 85,    // NAME OPACITY, 0-100
        outl: 1,    // SHOW SOUL OUTLINES
        cmode: 0,   // SOUL COLOR MODE: 0 THEIR COLOURS, 1 DISTINCT, 2 ALL RED (the game's own), 3 SIMPLE
        hl: 1,      // HIGHLIGHT MY SOUL
        dim: 0,     // DIM OTHER SOULS
        skfx: 0,    // REMOTE SKILL EFFECTS (build 48: none - no rings or marks around SOULs)
        dmgfx: 1,   // REMOTE DAMAGE EFFECTS
        nums: 0,    // PLAYER NUMBERS
        fade: 1,    // FADE OVERLAPPING SOULS
        spv: 0,     // WHILE WATCHING: 0 ALL SOULS, 1 AS WHILE PLAYING, 2 FOLLOWED ONLY
        mark: 0,    // SHAPE MARKERS (colour-blind friendly: a shape per player)
        shake: 0,   // REDUCED SHAKE
        flash: 0,   // REDUCED FLASHING
        simple: 0,  // SIMPLE EFFECTS
        hints: 1,   // KEY HINTS
        elim: 1,    // OUT NOTICES: 0 MINIMAL, 1 FULL
        info: 0,    // MATCH INFO overlay
        net: 0,     // NETWORK STATS
        shud: 0,    // WATCHING HUD: 0 FULL, 1 SMALL, 2 OFF
        cam: 0,     // CAMERA while watching: 0 FOLLOW, 1 FULL ARENA, 2 AUTO, 3 ZOOM
        help: 1,    // the watching keys box
        zoom: 2,    // ZOOM: 2 or 3 times
        wnames: 1,  // ROOM NAMES: the players' names over their heads in the cold place
        chat: 1,    // CHAT shown (build 48; messages still arrive while it is hidden)
        blines: 0   // BOSS LINES: the bosses' speech balloons (1.0.1: off unless chosen - they were over the battle)
    };
}

// [look]: your own SOUL (MORE OPTIONS > SOUL APPEARANCE)
function kfo_look_default()
{
    return {
        col: make_color_rgb(255, 0, 0), // your SOUL colour (the game's own red)
        ol: 1,      // MY OUTLINE: on / off
        olc: 0,     // OUTLINE COLOUR: 0 AUTO, 1 WHITE, 2 BLACK, 3 YELLOW, 4 CYAN, 5 MAGENTA
        hli: 2,     // HIGHLIGHT STRENGTH: 1 LOW, 2 MEDIUM, 3 HIGH
        gmc: 0      // GAMEPLAY COLOURS: 0 the game's colour first, 1 my colour + a mode mark
    };
}

// [field, lowest, highest, step] of every [view] setting (anything else read from a file goes back to its default)
function kfo_view_spec()
{
    return [["show", 0, 1, 1], ["sop", 0, 100, 5], ["names", 0, 1, 1], ["nop", 0, 100, 5], ["outl", 0, 1, 1], ["cmode", 0, 3, 1], ["hl", 0, 1, 1],
        ["dim", 0, 1, 1], ["skfx", 0, 2, 1], ["dmgfx", 0, 1, 1], ["nums", 0, 1, 1], ["fade", 0, 1, 1], ["spv", 0, 2, 1], ["mark", 0, 1, 1],
        ["shake", 0, 1, 1], ["flash", 0, 1, 1], ["simple", 0, 1, 1], ["hints", 0, 1, 1], ["elim", 0, 1, 1], ["info", 0, 1, 1], ["net", 0, 1, 1],
        ["shud", 0, 2, 1], ["cam", 0, 3, 1], ["help", 0, 1, 1], ["zoom", 2, 3, 1], ["wnames", 0, 1, 1], ["chat", 0, 1, 1], ["blines", 0, 1, 1]];
}

function kfo_look_spec()
{
    return [["ol", 0, 1, 1], ["olc", 0, 5, 1], ["hli", 1, 3, 1], ["gmc", 0, 1, 1]];
}

// a number from a file or a message: inside [lo, hi] on the step, else the default
function kfo_num_ok(_v, _lo, _hi, _st, _d)
{
    if (!is_real(_v) || is_nan(_v) || _v != floor(_v) || _v < _lo || _v > _hi)
        return _d;
    if (_st > 1 && ((_v - _lo) mod _st) != 0)
        return _d;
    return _v;
}

function kfo_view_clean(_in)
{
    var _d = kfo_view_default();
    var _sp = kfo_view_spec();
    for (var _i = 0; _i < array_length(_sp); _i++)
    {
        var _f = _sp[_i];
        var _v = (is_struct(_in) && variable_struct_exists(_in, _f[0])) ? variable_struct_get(_in, _f[0]) : variable_struct_get(_d, _f[0]);
        variable_struct_set(_d, _f[0], kfo_num_ok(_v, _f[1], _f[2], _f[3], variable_struct_get(_d, _f[0])));
    }
    // build 48: the SOUL settings are five (SHOW OTHER SOULS, SOUL COLOR, SOUL NAMES, OTHER SOUL OPACITY, HIGHLIGHT MY SOUL);
    // the others that were separate settings in build 47 are fixed as the game shows them now (a build 47 file cannot leave
    // one of them switched to something there is no row for any more)
    var _df = kfo_view_default();
    _d.nop = _df.nop;
    _d.outl = _df.outl;
    _d.cmode = 0;
    _d.dim = 0;
    _d.skfx = 0;
    _d.dmgfx = 1;
    _d.nums = 0;
    _d.fade = 1;
    _d.mark = 0;
    // build 49: OTHER SOUL OPACITY never below a level you can still see (a file or an old build at 0-10% made them vanish)
    _d.sop = max(kfo_sop_min(), _d.sop);
    return _d;
}

// the lowest OTHER SOUL OPACITY (build 49)
function kfo_sop_min()
{
    return 15;
}

function kfo_look_clean(_in)
{
    var _d = kfo_look_default();
    var _sp = kfo_look_spec();
    for (var _i = 0; _i < array_length(_sp); _i++)
    {
        var _f = _sp[_i];
        var _v = (is_struct(_in) && variable_struct_exists(_in, _f[0])) ? variable_struct_get(_in, _f[0]) : variable_struct_get(_d, _f[0]);
        variable_struct_set(_d, _f[0], kfo_num_ok(_v, _f[1], _f[2], _f[3], variable_struct_get(_d, _f[0])));
    }
    _d.col = kfo_col_ok((is_struct(_in) && variable_struct_exists(_in, "col")) ? _in.col : _d.col, _d.col);
    return _d;
}

// read while the ini is open (kfo_ini_load); a missing key gives back a value the clean step replaces with the default
function kfo_view_read()
{
    var _o = {};
    var _sp = kfo_view_spec();
    for (var _i = 0; _i < array_length(_sp); _i++)
        variable_struct_set(_o, _sp[_i][0], ini_read_real("view", _sp[_i][0], -99999));
    return _o;
}

function kfo_look_read()
{
    var _o = {};
    var _sp = kfo_look_spec();
    for (var _i = 0; _i < array_length(_sp); _i++)
        variable_struct_set(_o, _sp[_i][0], ini_read_real("look", _sp[_i][0], -99999));
    _o.col = kfo_hex_col(ini_read_string("look", "color", ""), -1);
    return _o;
}

function kfo_view_write(_v)
{
    var _sp = kfo_view_spec();
    for (var _i = 0; _i < array_length(_sp); _i++)
        ini_write_real("view", _sp[_i][0], variable_struct_get(_v, _sp[_i][0]));
}

function kfo_look_write(_l)
{
    var _sp = kfo_look_spec();
    for (var _i = 0; _i < array_length(_sp); _i++)
        ini_write_real("look", _sp[_i][0], variable_struct_get(_l, _sp[_i][0]));
    ini_write_string("look", "color", kfo_col_hex(_l.col));
}

function kfo_view()
{
    return kfo_get().view;
}

function kfo_look()
{
    return kfo_get().look;
}

// ---------- colours ----------
// a colour from a file or another game: a whole number 0..16777215 (GameMaker's own colour numbers), else _d
function kfo_col_ok(_c, _d)
{
    if (!is_real(_c) || is_nan(_c) || _c != floor(_c) || _c < 0 || _c > 16777215)
        return _d;
    return _c;
}

// the presets of SOUL APPEARANCE (Cyan is a SOUL colour like any other: only Cyan KNIGHT stays out of online matches)
function kfo_col_presets()
{
    return [["RED", make_color_rgb(255, 0, 0)], ["ORANGE", make_color_rgb(255, 140, 30)], ["YELLOW", make_color_rgb(255, 230, 40)],
        ["GREEN", make_color_rgb(40, 220, 80)], ["CYAN", make_color_rgb(30, 230, 230)], ["BLUE", make_color_rgb(50, 110, 255)],
        ["PURPLE", make_color_rgb(165, 70, 255)], ["PINK", make_color_rgb(255, 110, 200)], ["WHITE", make_color_rgb(240, 240, 240)]];
}

// the preset a colour is (-1: a colour of your own)
function kfo_col_preset_of(_c)
{
    var _p = kfo_col_presets();
    for (var _i = 0; _i < array_length(_p); _i++)
    {
        if (_p[_i][1] == _c)
            return _i;
    }
    return -1;
}

function kfo_col_name(_c)
{
    var _i = kfo_col_preset_of(_c);
    if (_i < 0)
        return "CUSTOM";
    var _p = kfo_col_presets();
    return _p[_i][0];
}

// how bright a colour looks (0-255)
function kfo_col_lum(_c)
{
    return (0.299 * colour_get_red(_c)) + (0.587 * colour_get_green(_c)) + (0.114 * colour_get_blue(_c));
}

// "#RRGGBB" of a colour
function kfo_col_hex(_c)
{
    var _h = "0123456789ABCDEF";
    var _v = [colour_get_red(_c), colour_get_green(_c), colour_get_blue(_c)];
    var _s = "#";
    for (var _i = 0; _i < 3; _i++)
        _s += string_char_at(_h, 1 + (_v[_i] div 16)) + string_char_at(_h, 1 + (_v[_i] mod 16));
    return _s;
}

// a typed hex colour ("#A040FF", "a040ff", "#FA4"): the colour, or _bad when it is not one
function kfo_hex_col(_s, _bad)
{
    if (!is_string(_s))
        return _bad;
    _s = string_upper(kfo_trim(_s));
    if (string_char_at(_s, 1) == "#")
        _s = string_delete(_s, 1, 1);
    if (string_length(_s) == 3)
        _s = string_char_at(_s, 1) + string_char_at(_s, 1) + string_char_at(_s, 2) + string_char_at(_s, 2) + string_char_at(_s, 3) + string_char_at(_s, 3);
    if (string_length(_s) != 6)
        return _bad;
    var _h = "0123456789ABCDEF";
    var _v = [0, 0, 0];
    for (var _i = 0; _i < 6; _i++)
    {
        var _d = string_pos(string_char_at(_s, _i + 1), _h) - 1;
        if (_d < 0)
            return _bad;
        _v[_i div 2] = (_v[_i div 2] * 16) + _d;
    }
    return make_color_rgb(_v[0], _v[1], _v[2]);
}

// the colour of a name over that colour: dark colours are lifted so the label stays readable on the dark box
function kfo_col_text(_c)
{
    if (kfo_col_lum(_c) < 90)
        return merge_color(_c, c_white, 0.55);
    return _c;
}

// the shadow under a label of colour _c (black under light text, white under the darkest)
function kfo_col_shadow(_c)
{
    return (kfo_col_lum(kfo_col_text(_c)) < 60) ? c_white : c_black;
}

// the outline colour of a SOUL of colour _c with OUTLINE COLOUR setting _olc
function kfo_col_outline(_c, _olc)
{
    switch (_olc)
    {
        case 1: return c_white;
        case 2: return c_black;
        case 3: return c_yellow;
        case 4: return c_aqua;
        case 5: return c_fuchsia;
    }
    return (kfo_col_lum(_c) > 150) ? c_black : c_white;
}

function kfo_olc_name(_i)
{
    switch (_i)
    {
        case 1: return "WHITE";
        case 2: return "BLACK";
        case 3: return "YELLOW";
        case 4: return "CYAN";
        case 5: return "MAGENTA";
    }
    return "AUTO";
}

// ---------- drawing a SOUL ----------
// Chapter 3's battle SOUL is spr_dodgeheart: a 16x16 heart (spr_heart's shape) with the game's own 2-pixel black edge, 20x20.
// Every SOUL the hub draws (yours in your colour, the other players' in theirs) uses spr_khub_soul, the same SOUL in WHITE
// (frame 0 the heart, frame 1 the edge), tinted with draw_sprite_ext's colour: white x colour = that colour exactly.
// Build 48: builds 47 drew it with gpu_set_fog (a flat colour over the sprite). Fog depends on the depth the drawing is at;
// the hub controller draws the other SOULs at depth -99000, where fog does not take, so in the real game the others' SOULs
// came out wrong or not at all (and only the rings drawn around them showed). No fog anywhere now, and no rings.
// _x, _y: the heart's own corner (16x16 box; the edge goes 2 pixels around it). _olc < 0: no edge.
function kfo_soul_draw(_x, _y, _sc, _col, _a, _olc)
{
    if (_a <= 0)
        return 0;
    var _sx = _x - (2 * _sc);
    var _sy = _y - (2 * _sc);
    if (_olc >= 0)
        draw_sprite_ext(spr_khub_soul, 1, _sx, _sy, _sc, _sc, 0, _olc, _a);
    draw_sprite_ext(spr_khub_soul, 0, _sx, _sy, _sc, _sc, 0, _col, _a);
    return 1;
}

// DRBR: a SOUL drawn upside down (the yellow SOUL's look: it points up), turned about its middle
function kfo_soul_draw_up(_x, _y, _sc, _col, _a, _olc)
{
    if (_a <= 0)
        return 0;
    var _sx = (_x - (2 * _sc)) + (20 * _sc);
    var _sy = (_y - (2 * _sc)) + (20 * _sc);
    if (_olc >= 0)
        draw_sprite_ext(spr_khub_soul, 1, _sx, _sy, _sc, _sc, 180, _olc, _a);
    draw_sprite_ext(spr_khub_soul, 0, _sx, _sy, _sc, _sc, 180, _col, _a);
    return 1;
}

// your SOUL's edge (SOUL COLOR > MY OUTLINE, OUTLINE COLOR): off -1, AUTO white with HIGHLIGHT MY SOUL (else dark on light
// colours, light on dark ones), or the colour chosen. The edge is the SOUL's own heart-shaped outline - nothing around it.
function kfo_my_edge()
{
    var _L = kfo_look();
    if (!_L.ol)
        return -1;
    if (_L.olc == 0 && kfo_view().hl)
        return c_white;
    return kfo_col_outline(_L.col, _L.olc);
}

// where the heart is inside a battle SOUL at x, y (obj_heart's own position: its sprite's corner): 2 pixels in for
// spr_dodgeheart, Chapter 3's SOUL (the positions the games send each other are obj_heart's)
function kbr_soul_in()
{
    return 2;
}

// a 0-100 slider (the opacities, the volumes): a track from _x0 to _x1 with a tick at every quarter, filled up to the value,
// and its handle; _hot: the row the cursor is on
function kfo_slider_draw(_x0, _x1, _y, _v, _hot)
{
    var _f = clamp(_v, 0, 100) / 100;
    var _hx = round(_x0 + ((_x1 - _x0) * _f));
    draw_set_color(c_dkgray);
    draw_rectangle(_x0, _y + 4, _x1, _y + 5, false);
    for (var _t = 0; _t <= 4; _t++)
    {
        var _tx = round(_x0 + (((_x1 - _x0) * _t) / 4));
        draw_rectangle(_tx, _y + 2, _tx, _y + 7, false);
    }
    draw_set_color(_hot ? c_yellow : c_ltgray);
    if (_hx > _x0)
        draw_rectangle(_x0, _y + 4, _hx, _y + 5, false);
    draw_set_color(c_black);
    draw_rectangle(_hx - 2, _y, _hx + 2, _y + 9, false);
    draw_set_color(_hot ? c_yellow : c_white);
    draw_rectangle(_hx - 1, _y + 1, _hx + 1, _y + 8, false);
    return 1;
}

// the rows that are sliders (0-100 in steps of 5; < > moves a step, held it keeps going)
function kfo_is_slider(_id)
{
    return _id == "sop" || _id == "nop" || _id == "sfx" || _id == "mus";
}

// a small shape for player slot _slot (SHAPE MARKERS: told apart without colours) - circle, triangle, square, diamond,
// plus, cross, ring, bar
function kfo_mark_draw(_x, _y, _slot, _col)
{
    var _s = _slot mod 8;
    draw_set_color(c_black);
    draw_rectangle(_x - 4, _y - 4, _x + 4, _y + 4, false);
    draw_set_color(_col);
    switch (_s)
    {
        case 0: draw_circle(_x, _y, 3, false); break;
        case 1: draw_triangle(_x, _y - 3, _x - 3, _y + 3, _x + 3, _y + 3, false); break;
        case 2: draw_rectangle(_x - 3, _y - 3, _x + 3, _y + 3, false); break;
        case 3: draw_triangle(_x, _y - 3, _x - 3, _y, _x + 3, _y, false); draw_triangle(_x, _y + 3, _x - 3, _y, _x + 3, _y, false); break;
        case 4: draw_rectangle(_x - 3, _y - 1, _x + 3, _y + 1, false); draw_rectangle(_x - 1, _y - 3, _x + 1, _y + 3, false); break;
        case 5: draw_line_width(_x - 3, _y - 3, _x + 3, _y + 3, 2); draw_line_width(_x - 3, _y + 3, _x + 3, _y - 3, 2); break;
        case 6: draw_circle(_x, _y, 3, true); draw_circle(_x, _y, 2, true); break;
        default: draw_rectangle(_x - 3, _y - 1, _x + 3, _y + 1, false); break;
    }
    return 1;
}

// ---------- your own SOUL (obj_heart's Draw asks first: br_patch / hub event heart_Draw_0) ----------
// Online, while you play, your SOUL is drawn in your colour, fully opaque, as the game draws it (heart + its edge). HIGHLIGHT
// MY SOUL makes its edge white instead of black (nothing around it: no rings). When the game itself shows a SOUL mode
// (another sprite, colour or tint: a yellow shooting SOUL, an attack's own tint) the game's own Draw runs, as always.
// Nothing here moves the SOUL or touches its collision (its mask is its sprite's, unchanged).
function kbr_heart_draw()
{
    if (!kbr_on())
        return false;
    var _M = kbr_match();
    if (is_undefined(_M) || !_M.me || _M.out)
        return false;
    var _plain = (sprite_index == spr_dodgeheart || sprite_index == spr_heart);
    var _mode = (variable_instance_exists(id, "color") && color != 0) || !_plain || image_blend != c_white;
    if (_mode)
        return false;
    var _in = (sprite_index == spr_heart) ? 0 : kbr_soul_in();
    var _col = kfo_look().col;
    // the game's hurt blink (the second frame) shows darker
    if (image_index >= 1)
        _col = merge_color(_col, c_black, 0.5);
    kfo_soul_draw(x + (_in * image_xscale), y + (_in * image_yscale), image_xscale, _col, image_alpha, kfo_my_edge());
    return true;
}

// ---------- the other SOULs ----------
// per player (by pid): what this game last drew and saw of them - the hit blink, the skill marks, the shatter when they go OUT
function kbr_rv(_M, _pid)
{
    var _k = string(_pid);
    if (!variable_struct_exists(_M.vw.rv, _k))
        variable_struct_set(_M.vw.rv, _k, { hp: -1, hit: 0, sk: 0, al: -1, x: -9999, y: -9999, seen: 0, skt: 0, lx: -9999, ly: -9999 });
    return variable_struct_get(_M.vw.rv, _k);
}

// the view's part of the match (made with the match: kbr_match_fill)
function kbr_vw_new()
{
    var _V = kfo_view();
    return { rv: {}, fx: [], cover: 0, hurt: 0, cam: _V.cam, auto_t: 0, auto_why: "", vhide: false, names_t: -1, banner: "", banner_t: 0,
        qs: false, qs_row: 0, stats: false, zoom_x: -1, zoom_y: -1, zoom: _V.zoom, out_t: -1, picked: false, lst_t: 0, pings: [], loss: 0,
        song_said: false, brk: [], ko: undefined };
}

// the colour a player's SOUL is drawn in: the colour they chose (their place's colour when it is unknown)
function kbr_soul_col(_p, _pid)
{
    return kfo_col_ok(kfo_jn(_p, "cl", -1), kbr_pcol(kbr_pslot(_pid)));
}

// what the host's standings say changed: a lower HP (a hit: the blink), a skill switched on (its mark, AUTO's interest),
// someone OUT (their SOUL shatters where it was last drawn; OUT NOTICES: FULL adds the banner)
function kbr_view_on_state(_M, _m)
{
    if (!variable_struct_exists(_M, "vw"))
        return 0;
    var _pl = kfo_ja(_m, "pl");
    var _V = kfo_view();
    for (var _i = 0; _i < array_length(_pl); _i++)
    {
        var _p = _pl[_i];
        var _pid = kfo_jn(_p, "pid", -2);
        var _r = kbr_rv(_M, _pid);
        var _hp = kfo_jn(_p, "hp", 0);
        var _al = kfo_jn(_p, "al", 0);
        var _sk = kfo_jn(_p, "sk", 0);
        if (_r.hp >= 0 && _hp < _r.hp && _al == 1)
            _r.hit = 30;
        if ((_sk & ~_r.sk & 7) != 0)
            _r.skt = 90;
        if (_r.al == 1 && _al == 0 && _pid != global.kfo.my)
        {
            if (_r.seen > 0 && _r.x > -9000)
                kbr_view_shatter(_M, _r.x, _r.y, kbr_soul_col(_p, _pid));
            if (_V.elim == 1)
            {
                _M.vw.banner = string_upper(kfo_js(_p, "n", "?")) + " IS OUT  #" + string(kfo_jn(_p, "pl", 0)) + "   " + string(kfo_jn(_m, "an", 0)) + " LEFT";
                _M.vw.banner_t = 75;
            }
        }
        _r.hp = _hp;
        _r.al = _al;
        _r.sk = _sk;
    }
    return 1;
}

// build 48: a SOUL breaking the way Chapter 3's GAME OVER breaks yours - the heart cracks in two (snd_break1), then bursts into
// six shards that fly out and fall (snd_break2) - in the player's own colour, where their SOUL was. Nothing else: the battle
// goes on (no GAME OVER for the others; yours: kbr_ko_me_start). _x, _y: the SOUL's drawn corner (2 px in).
function kbr_view_shatter(_M, _x, _y, _col)
{
    if (!variable_struct_exists(_M.vw, "brk"))
        _M.vw.brk = [];
    array_push(_M.vw.brk, kbr_brk_new(_x - kbr_soul_in(), _y - kbr_soul_in(), _col, 20, false));
    return 1;
}

// a breaking SOUL: sprite corner _x, _y; it cracks for _crack frames, then the shards fly (seeded by where it was: every
// game sees the same pieces); _me: the louder sounds of your own
function kbr_brk_new(_x, _y, _col, _crack, _me)
{
    return { x: _x, y: _y, col: _col, t: 0, crack: _crack, me: _me, sh: [] };
}

function kbr_brk_tick(_b)
{
    _b.t++;
    if (_b.t == 1)
    {
        if (_b.me)
            snd_play(snd_break1);
        else
            snd_play_x(snd_break1, 0.5, 1);
    }
    if (_b.t == _b.crack)
    {
        if (_b.me)
            snd_play(snd_break2);
        else
            snd_play_x(snd_break2, 0.5, 1);
        // the six pieces of Chapter 3's GAME OVER: from across the heart, out at speed 7 (a little less in the box), falling
        var _off = [[-2, 0], [0, 3], [2, 6], [8, 0], [10, 3], [12, 6]];
        var _g = kbr_rng(1 + abs(floor(_b.x * 31 + _b.y * 17)));
        for (var _i = 0; _i < 6; _i++)
        {
            var _d = kbr_rng_int(_g, 360);
            var _sp = _b.me ? 7 : 4.5;
            array_push(_b.sh, { x: _b.x + 4 + _off[_i][0], y: _b.y + 4 + _off[_i][1], vx: lengthdir_x(_sp, _d), vy: lengthdir_y(_sp, _d), a: kbr_rng_int(_g, 360) });
        }
    }
    for (var _i = 0; _i < array_length(_b.sh); _i++)
    {
        var _s = _b.sh[_i];
        _s.x += _s.vx;
        _s.y += _s.vy;
        _s.vy += _b.me ? 0.2 : 0.15;
        _s.a += 12;
    }
    return _b.t < _b.crack + (_b.me ? 70 : 45);
}

function kbr_brk_draw(_b)
{
    if (_b.t < _b.crack)
    {
        // the crack (spr_khub_soul frame 2, Chapter 3's spr_heartbreak shape)
        draw_sprite_ext(spr_khub_soul, 2, _b.x, _b.y, 1, 1, 0, _b.col, 1);
        return 1;
    }
    var _left = (_b.crack + (_b.me ? 70 : 45)) - _b.t;
    var _a = clamp(_left / 15, 0, 1);
    for (var _i = 0; _i < array_length(_b.sh); _i++)
    {
        var _s = _b.sh[_i];
        // the shard frame is drawn around its middle (10, 10 in the 20 x 20 frame)
        draw_sprite_ext(spr_khub_soul, 3, _s.x - lengthdir_x(14.142, _s.a + 315), _s.y - lengthdir_y(14.142, _s.a + 315), 1, 1, _s.a, _b.col, _a);
    }
    return 1;
}

// your SOUL broke: the same break where it was (your colour, the full sounds), then the GAME OVER - drawn over the battle, which
// goes on - with your place; then it fades and you watch the rest
function kbr_ko_me_start(_M)
{
    if (!variable_struct_exists(_M, "vw"))
        _M.vw = kbr_vw_new();
    var _x = -9999;
    var _y = -9999;
    if (instance_exists(obj_heart))
    {
        var _h = instance_find(obj_heart, 0);
        _x = _h.x;
        _y = _h.y;
    }
    _M.vw.ko = { t: 0, b: kbr_brk_new(_x, _y, kfo_look().col, 40, true) };
    return 1;
}

// the GAME OVER of a battle royale: its frames (after the break) - in 50, held, out 30
function kbr_ko_go_t0()
{
    return 75;
}

function kbr_ko_tick(_M)
{
    var _K = _M.vw.ko;
    if (is_undefined(_K))
        return 0;
    _K.t++;
    if (_K.b.x > -9000)
        kbr_brk_tick(_K.b);
    // the game's own GAME OVER sting over the battle music
    if (_K.t == kbr_ko_go_t0())
        snd_play(snd_hurt1);
    if (_K.t > kbr_ko_go_t0() + 210)
        _M.vw.ko = undefined;
    return 1;
}

// over the whole HUD: the darkening, Chapter 3's GAME OVER (spr_gameoverbg_neo, as its game over room fades it in), your place
function kbr_ko_draw(xx, yy, _M)
{
    var _K = _M.vw.ko;
    if (is_undefined(_K))
        return 0;
    if (_K.b.x > -9000)
        kbr_brk_draw(_K.b);
    var _t = _K.t - kbr_ko_go_t0();
    if (_t < 0)
        return 0;
    var _a = clamp(_t / 50, 0, 1);
    if (_t > 180)
        _a = clamp((210 - _t) / 30, 0, 1);
    draw_set_alpha(_a * 0.85);
    draw_set_color(c_black);
    draw_rectangle(xx - 10, yy - 10, xx + 650, yy + 490, false);
    draw_set_alpha(1);
    // (320 x 90: the game over room's own picture, at the battle's 2x scale - as wide as the screen)
    draw_sprite_ext(spr_gameoverbg_neo, 0, xx, yy + 40, 2, 2, 0, c_white, _a);
    if (_t >= 40)
    {
        var _b = clamp((_t - 40) / 20, 0, 1) * _a;
        draw_set_alpha(_b);
        draw_set_halign(fa_center);
        scr_84_set_draw_font("main");
        var _pl = _M.place;
        kbr_hud_text(xx + 320, yy + 330, (_pl > 0) ? ("YOU PLACED #" + string(_pl)) : "YOUR SOUL SHATTERED", c_white);
        draw_set_font(fnt_small);
        kbr_hud_text(xx + 320, yy + 362, "THE BATTLE GOES ON - YOU WILL WATCH THE REST", c_ltgray);
        draw_set_halign(fa_left);
        draw_set_alpha(1);
    }
    return 1;
}

// every step (kbr_me_tick): the effects run down, AUTO picks, the cover pulse of your SOUL
function kbr_view_tick(_M)
{
    var _vw = _M.vw;
    kbr_view_shake(_M);
    // the song's credit, once, when the match goes
    if (!_vw.song_said && _M.go)
    {
        _vw.song_said = true;
        var _sc = knight_song_credit();
        if (_sc != "")
            kbr_log("* MUSIC: " + _sc, c_ltgray);
    }
    for (var _i = array_length(_vw.fx) - 1; _i >= 0; _i--)
    {
        var _f = _vw.fx[_i];
        _f.x += _f.vx;
        _f.y += _f.vy;
        _f.vy += 0.15;
        _f.life--;
        if (_f.life <= 0)
            array_delete(_vw.fx, _i, 1);
    }
    var _keys = variable_struct_get_names(_vw.rv);
    for (var _i = 0; _i < array_length(_keys); _i++)
    {
        var _r = variable_struct_get(_vw.rv, _keys[_i]);
        if (_r.hit > 0)
            _r.hit--;
        if (_r.skt > 0)
            _r.skt--;
    }
    if (_vw.cover > 0)
        _vw.cover--;
    if (_vw.hurt > 0)
        _vw.hurt--;
    if (_M.hitfx == 8)
        _vw.hurt = 40;
    if (_vw.banner_t > 0)
        _vw.banner_t--;
    // build 48: the breaking SOULs, your GAME OVER
    if (variable_struct_exists(_vw, "brk"))
    {
        for (var _i = array_length(_vw.brk) - 1; _i >= 0; _i--)
        {
            if (!kbr_brk_tick(_vw.brk[_i]))
                array_delete(_vw.brk, _i, 1);
        }
    }
    if (variable_struct_exists(_vw, "ko"))
        kbr_ko_tick(_M);
    // DRBR 1.0.3: the skills the others used (kbr_view_on_su) and the YELLOW SOUL shots of the others (kbr_gshot_seen)
    if (variable_struct_exists(_vw, "su"))
    {
        for (var _i = array_length(_vw.su) - 1; _i >= 0; _i--)
        {
            _vw.su[_i].t++;
            if (_vw.su[_i].t > 48)
                array_delete(_vw.su, _i, 1);
        }
    }
    if (variable_struct_exists(_vw, "gs"))
    {
        for (var _i = array_length(_vw.gs) - 1; _i >= 0; _i--)
        {
            var _g = _vw.gs[_i];
            if (_g.big)
            {
                // Chapter 2's BIG SHOT: it grows into its shape and speeds up (friction -0.2 x 2)
                _g.sp += 0.4;
                _g.xs = min(1, _g.xs + 0.2);
                _g.ys = max(1, _g.ys - 0.2);
                _g.a = min(1, _g.a + 0.2);
            }
            _g.x += _g.sp;
            if (_g.x > 700)
                array_delete(_vw.gs, _i, 1);
        }
    }
    return 1;
}

// DRBR 1.0.3: a skill someone used (the host's "su": who, which, at whom): shown at their SOUL in kbr_draw_su
function kbr_view_on_su(_m)
{
    var _M = kbr_match();
    if (is_undefined(_M))
        return 0;
    if (!variable_struct_exists(_M, "vw"))
        _M.vw = kbr_vw_new();
    if (!variable_struct_exists(_M.vw, "su"))
        _M.vw.su = [];
    var _sid = kfo_jn(_m, "sid", 0);
    if (!is_numeric(_sid) || _sid != floor(_sid) || _sid < 1 || _sid >= kbr_skill_count())
        return 0;
    var _tg = kfo_ja(_m, "tg");
    var _l = [];
    for (var _i = 0; _i < array_length(_tg) && _i < 8; _i++)
    {
        if (is_numeric(_tg[_i]))
            array_push(_l, _tg[_i]);
    }
    array_push(_M.vw.su, { f: kfo_jn(_m, "f", -1), sid: _sid, tg: _l, t: 0 });
    if (array_length(_M.vw.su) > 24)
        array_delete(_M.vw.su, 0, 1);
    return 1;
}

// DRBR 1.0.3: the YELLOW SOUL's shots of another SOUL (a player's game counts its own, the host counts its bots'; the "ps" list
// carries the counts): each new one flies from that SOUL here, as theirs does in their game (what it hits is theirs - here it
// is only seen). _x, _y: their SOUL's corner, relative to the battle's camera
function kbr_gshot_seen(_M, _p, _pid, _ys, _yb, _x, _y)
{
    if (!is_numeric(_pid) || _pid == global.kfo.my)
        return 0;
    var _n = 0;
    var _nb = 0;
    if (_ys >= 0 && variable_struct_exists(_p, "ys0") && _p.ys0 >= 0)
        _n = (_ys - _p.ys0 + 1000) mod 1000;
    if (_yb >= 0 && variable_struct_exists(_p, "yb0") && _p.yb0 >= 0)
        _nb = (_yb - _p.yb0 + 1000) mod 1000;
    _p.ys0 = _ys;
    _p.yb0 = _yb;
    // (a count that went back - a new attack's SOUL - or a long gap: nothing to show)
    if (_n > 6)
        _n = 0;
    if (_nb > 2)
        _nb = 0;
    if ((_n + _nb) == 0 || !kbr_on())
        return 0;
    if (!variable_struct_exists(_M, "vw"))
        _M.vw = kbr_vw_new();
    if (!variable_struct_exists(_M.vw, "gs"))
        _M.vw.gs = [];
    var _st = kbr_st_player(_M, _pid);
    var _col = is_undefined(_st) ? c_yellow : kbr_soul_col(_st, _pid);
    for (var _i = 0; _i < min(_n, 3); _i++)
        array_push(_M.vw.gs, { x: (_x + 10) - (_i * 16), y: _y + 10, sp: 16, big: false, xs: 1, ys: 1, a: 1, col: _col });
    if (_nb > 0)
        array_push(_M.vw.gs, { x: _x + 10, y: _y + 10, sp: 8, big: true, xs: 0.1, ys: 2, a: 0.5, col: _col });
    while (array_length(_M.vw.gs) > 40)
        array_delete(_M.vw.gs, 0, 1);
    return 1;
}

// the others' shots (under the bullets, with their SOULs): the game's own yellow shot and BIG SHOT, a little of their colour
function kbr_draw_gshots(_M, _op)
{
    if (!variable_struct_exists(_M.vw, "gs"))
        return 0;
    var _a0 = clamp(_op, 0.35, 1) * 0.85;
    var _ox = kbr_ox();
    var _oy = kbr_oy();
    for (var _i = 0; _i < array_length(_M.vw.gs); _i++)
    {
        var _g = _M.vw.gs[_i];
        var _cl = merge_color(c_white, _g.col, 0.3);
        if (_g.big)
            draw_sprite_ext(spr_yheart_bigshot, 0, _g.x + _ox, _g.y + _oy, _g.xs, _g.ys, 0, _cl, _g.a * _a0);
        else
            draw_sprite_ext(spr_yheart_shot, 0, _g.x + _ox, _g.y + _oy, 1, 1, 0, _cl, _a0);
    }
    return 1;
}

// where a player's SOUL is drawn now (its middle): yours, or theirs as drawn this frame (undefined: not shown)
function kbr_su_pos(_M, _pid, _mx, _my)
{
    if (_pid == global.kfo.my)
        return (_mx > -9000) ? [_mx + 8, _my + 8] : undefined;
    var _k = string(_pid);
    if (!variable_struct_exists(_M.vw.rv, _k))
        return undefined;
    var _r = variable_struct_get(_M.vw.rv, _k);
    if (_r.seen <= 0 || current_time - _r.seen > 500 || _r.x < -9000)
        return undefined;
    return [_r.x + 8, _r.y + 8];
}

// DRBR 1.0.3: the skills the others used, at their SOULs: a ring bursts round the SOUL, the skill's name rises over it (red: an
// attack, green: on themselves) and an attack's diamond, with its picture, flies to each of its targets (you too)
function kbr_draw_su(_M, _mx, _my)
{
    if (!variable_struct_exists(_M.vw, "su") || array_length(_M.vw.su) == 0)
        return 0;
    var _simple = kfo_view().simple;
    draw_set_font(fnt_small);
    draw_set_halign(fa_center);
    for (var _i = 0; _i < array_length(_M.vw.su); _i++)
    {
        var _e = _M.vw.su[_i];
        // (your own: your HUD shows it)
        if (_e.f == global.kfo.my)
            continue;
        var _src = kbr_su_pos(_M, _e.f, _mx, _my);
        if (is_undefined(_src))
            continue;
        var _red = kbr_skill_red(_e.sid);
        var _col = _red ? make_color_rgb(255, 96, 96) : make_color_rgb(96, 255, 128);
        var _t = _e.t;
        if (_t < 14 && !_simple)
        {
            draw_set_alpha((1 - (_t / 14)) * 0.9);
            draw_set_color(_col);
            draw_circle(_src[0], _src[1], 6 + (_t * 1.6), true);
            draw_circle(_src[0], _src[1], 7 + (_t * 1.6), true);
        }
        var _a = (_t < 34) ? 1 : clamp((48 - _t) / 14, 0, 1);
        var _inf = kbr_skill_info(_e.sid);
        var _nm = _inf[1];
        var _ty = _src[1] - 22 - min(8, _t * 0.4);
        draw_set_alpha(_a);
        draw_set_color(c_black);
        draw_text(_src[0] + 1, _ty + 1, _nm);
        draw_set_color(_col);
        draw_text(_src[0], _ty, _nm);
        if (_red && _t >= 2 && _t <= 26)
        {
            for (var _j = 0; _j < array_length(_e.tg); _j++)
            {
                var _dst = kbr_su_pos(_M, _e.tg[_j], _mx, _my);
                if (is_undefined(_dst) || _e.tg[_j] == _e.f)
                    continue;
                if (_t <= 18)
                {
                    var _k = (_t - 2) / 16;
                    var _x = lerp(_src[0], _dst[0], _k);
                    var _y = lerp(_src[1], _dst[1], _k) - (sin(_k * pi) * 24);
                    draw_set_alpha(1);
                    kbr_diamond(_x, _y, 9, _col, false, false);
                    if (!_simple)
                        kbr_skill_icon(_e.sid, _x, _y, 1, 0.55);
                }
                else if (!_simple)
                {
                    draw_set_alpha(1 - ((_t - 18) / 8));
                    draw_set_color(_col);
                    draw_circle(_dst[0], _dst[1], 6 + ((_t - 18) * 2), true);
                }
            }
        }
    }
    draw_set_alpha(1);
    draw_set_halign(fa_left);
    draw_set_color(c_white);
    return 1;
}

// the others' SOULs, drawn by the hub controller under the bullets and under your own SOUL. In a stable order (their place in
// the match's player list), at the positions their games sent (between the last two, as before), faded where they overlap
// yours or each other (FADE OVERLAPPING SOULS) - the real positions never change.
function kbr_draw_souls()
{
    var _M = kbr_match();
    if (is_undefined(_M) || !kbr_on() || !is_struct(_M.st) || !_M.go)
        return 0;
    if (!variable_struct_exists(_M, "vw"))
        _M.vw = kbr_vw_new();
    var _V = kfo_view();
    var _spec = (_M.out || !_M.me);
    var _show = _V.show;
    var _op = _V.sop / 100;
    var _only = -1;
    if (_spec)
    {
        // WHILE WATCHING: every SOUL at full strength, as while playing, or only the one you follow; V hides the rest for now
        if (_V.spv == 0)
        {
            _show = 1;
            _op = 1;
        }
        else if (_V.spv == 2)
        {
            _show = 1;
            _op = 1;
            _only = _M.spect;
        }
        if (_M.vw.vhide)
            _only = _M.spect;
    }
    var _pl = kfo_ja(_M.st, "pl");
    var _mx = -9999;
    var _my = -9999;
    var _msc = 1;
    if (!_spec && instance_exists(obj_heart))
    {
        var _h = instance_find(obj_heart, 0);
        _mx = _h.x + kbr_soul_in();
        _my = _h.y + kbr_soul_in();
        _msc = _h.image_xscale;
    }
    var _cam = _M.vw.cam;
    var _drawn = [];
    var _labels = [];
    draw_set_font(fnt_small);
    // the stable order: by place in the match's player list (insertion sort of [slot, index])
    var _ord = [];
    for (var _i = 0; _i < array_length(_pl); _i++)
    {
        var _e = [kbr_pslot(kfo_jn(_pl[_i], "pid", -1)), _i];
        var _j = array_length(_ord);
        array_push(_ord, _e);
        while (_j > 0 && _ord[_j - 1][0] > _e[0])
        {
            _ord[_j] = _ord[_j - 1];
            _j--;
        }
        _ord[_j] = _e;
    }
    for (var _s = 0; _s < array_length(_ord); _s++)
    {
        {
            var _p = _pl[_ord[_s][1]];
            var _pid = kfo_jn(_p, "pid", -1);
            if (_pid == global.kfo.my || kfo_jn(_p, "al", 0) != 1)
                continue;
            var _id = string(_pid);
            if (!variable_struct_exists(_M.ps, _id))
                continue;
            var _q = variable_struct_get(_M.ps, _id);
            if (current_time - _q.t > 1500)
                continue;
            // their heart's own corner (the position sent is their obj_heart's: the sprite's corner, the heart 2 pixels in)
            var _x = kbr_ps_x(_q) + kbr_soul_in();
            var _y = kbr_ps_y(_q) + kbr_soul_in();
            var _r = kbr_rv(_M, _pid);
            _r.lx = _r.x;
            _r.ly = _r.y;
            _r.x = _x;
            _r.y = _y;
            _r.seen = current_time;
            var _foc = (_spec && _M.spect == _pid && _cam != 1);
            if (!_show && !_foc)
                continue;
            if (_only >= 0 && _pid != _only)
                continue;
            var _a = _foc ? 1 : _op;
            // over your SOUL or over one drawn before: fainter (and your SOUL pulses: it is covered); FULL ARENA (watching)
            // draws every SOUL alike
            if (!_foc && !(_spec && _cam == 1))
            {
                if (_mx > -9000 && abs(_x - _mx) < 12 && abs(_y - _my) < 12)
                {
                    _a *= 0.45;
                    _M.vw.cover = 20;
                }
                for (var _j = 0; _j < array_length(_drawn); _j++)
                {
                    if (abs(_x - _drawn[_j][0]) < 10 && abs(_y - _drawn[_j][1]) < 10)
                    {
                        _a *= 0.6;
                        break;
                    }
                }
            }
            else if (_mx > -9000 && abs(_x - _mx) < 12 && abs(_y - _my) < 12)
                _M.vw.cover = 20;
            // a hit: it blinks while the invincibility lasts (REMOTE DAMAGE EFFECTS)
            if (_r.hit > 0)
                _a *= ((_r.hit div (_V.flash ? 8 : 3)) mod 2 == 0) ? 1 : 0.35;
            var _col = kbr_soul_col(_p, _pid);
            // DRBR: in a mode of the encounter's (Flowery's ORANGE SOUL, Gerson's GREEN, Spamton's YELLOW, Pink's PURPLE), every
            // SOUL is that colour - the player's own colour stays as its edge (a cosmetic colour never hides a gameplay mode)
            var _md = kbr_soul_mode();
            if (_md == "orange")
                kfo_soul_draw(_x, _y, 1, make_color_rgb(255, 160, 40), _a, _col);
            else if (_md == "green")
                kfo_soul_draw(_x, _y, 1, make_color_rgb(70, 230, 110), _a, _col);
            else if (_md == "yellow")
                kfo_soul_draw_up(_x, _y, 1, make_color_rgb(255, 255, 0), _a, _col);
            else if (_md == "purple")
                kfo_soul_draw(_x, _y, 1, make_color_rgb(213, 53, 217), _a, _col);
            else
                kfo_soul_draw(_x, _y, 1, _col, _a, c_black);
            // build 49: for the DEBUG OVERLAY (F3): drawn now, at this alpha
            _r.da = _a;
            _r.dt = current_time;
            array_push(_drawn, [_x, _y]);
            array_push(_labels, [_x, _y, _p, _pid, _col, _a, _foc]);
        }
    }
    // DRBR 1.0.3: the others' YELLOW SOUL shots and the skills they used
    if (_show)
    {
        kbr_draw_gshots(_M, _op);
        kbr_draw_su(_M, _mx, _my);
    }
    kbr_view_labels(_M, _labels, _V, _spec);
    // build 48: the SOULs that broke (the crack, then the shards)
    if (variable_struct_exists(_M.vw, "brk"))
    {
        for (var _i = 0; _i < array_length(_M.vw.brk); _i++)
            kbr_brk_draw(_M.vw.brk[_i]);
    }
    // the pieces of SOULs that broke
    for (var _i = 0; _i < array_length(_M.vw.fx); _i++)
    {
        var _f = _M.vw.fx[_i];
        draw_set_alpha(min(1, _f.life / 20));
        draw_set_color(_f.col);
        draw_rectangle(_f.x - 1, _f.y - 1, _f.x + 1, _f.y + 1, false);
    }
    draw_set_alpha(1);
    draw_set_halign(fa_left);
    draw_set_color(c_white);
    return 1;
}


// the names (SHOW PLAYER NAMES, NAME OPACITY; while watching N switches them for now; nothing under any SOUL while they are off -
// build 47, your request - the one you follow is named in the watching card):
// in the SOUL list's order, each under its SOUL, pushed down past a label already there so none covers another
function kbr_view_labels(_M, _labels, _V, _spec)
{
    var _on = _V.names;
    if (_spec && _M.vw.names_t >= 0)
        _on = _M.vw.names_t;
    // not under the countdown (every SOUL starts in the same spot) nor under the player list
    if (_M.tab || kbr_now() < _M.tl.intro + 30)
        return 0;
    var _put = [];
    draw_set_halign(fa_center);
    for (var _i = 0; _i < array_length(_labels); _i++)
    {
        var _l = _labels[_i];
        // names under the SOULs only when SHOW PLAYER NAMES is on (off by default; the one you follow is named in the
        // watching card, not under their SOUL)
        if (!_on)
            continue;
        var _nm = string_copy(kfo_js(_l[2], "n", "?"), 1, 8);
        if (_V.nums)
            _nm = "P" + string(kbr_pslot(_l[3]) + 1) + " " + _nm;
        var _lx = _l[0] + 8;
        var _ly = _l[1] + 20;
        var _w = string_width(_nm) + 4;
        var _moved = true;
        var _guard = 0;
        while (_moved && _guard < 8)
        {
            _moved = false;
            _guard++;
            for (var _j = 0; _j < array_length(_put); _j++)
            {
                if (abs(_put[_j][0] - _lx) < ((_put[_j][2] + _w) / 2) && abs(_put[_j][1] - _ly) < 11)
                {
                    _ly = _put[_j][1] + 11;
                    _moved = true;
                }
            }
        }
        array_push(_put, [_lx, _ly, _w]);
        var _na = (_V.nop / 100) * (_l[6] ? 1 : max(0.35, _l[5]));
        draw_set_alpha(_na);
        draw_set_color(kfo_col_shadow(_l[4]));
        draw_text(_lx + 1, _ly + 1, _nm);
        draw_set_color(kfo_col_text(_l[4]));
        draw_text(_lx, _ly, _nm);
    }
    draw_set_alpha(1);
    draw_set_halign(fa_left);
    return 1;
}

// ---------- watching (OUT, or watching from the room) ----------
// the camera modes: FOLLOW one player, FULL ARENA (every SOUL alike), AUTO (whoever is interesting: the final two, a skill
// just switched on, the lowest HP), ZOOM (a magnifying lens you move over the box). None of them moves the game's camera:
// every watcher sees the very battle the players see, from the same timeline.
function kbr_cam_name(_c)
{
    switch (_c)
    {
        case 1: return "FULL ARENA";
        case 2: return "AUTO";
        case 3: return "ZOOM";
    }
    return "FOLLOW";
}

function kbr_shud_name(_c)
{
    switch (_c)
    {
        case 1: return "SMALL";
        case 2: return "OFF";
    }
    return "FULL";
}

// the standings entry of player _pid (undefined if none)
function kbr_st_player(_M, _pid)
{
    if (!is_struct(_M.st))
        return undefined;
    var _pl = kfo_ja(_M.st, "pl");
    for (var _i = 0; _i < array_length(_pl); _i++)
    {
        if (kfo_jn(_pl[_i], "pid", -2) == _pid)
            return _pl[_i];
    }
    return undefined;
}

// the living player with the most HP (ties: the first in the list)
function kbr_spec_leader(_M, _ids)
{
    var _best = (array_length(_ids) > 0) ? _ids[0] : -1;
    var _bf = -1;
    for (var _i = 0; _i < array_length(_ids); _i++)
    {
        var _p = kbr_st_player(_M, _ids[_i]);
        if (is_undefined(_p))
            continue;
        var _f = kfo_jn(_p, "hp", 0) / max(1, kfo_jn(_p, "mh", 1));
        if (_f > _bf)
        {
            _bf = _f;
            _best = _ids[_i];
        }
    }
    return _best;
}

// the next living player after _old in the match's list order (the one followed went OUT: the camera moves on, it does not
// jump back to the first)
function kbr_spec_after(_ids, _old)
{
    if (array_length(_ids) == 0)
        return -1;
    var _so = kbr_pslot(_old);
    var _best = -1;
    var _bs = 99;
    var _low = -1;
    var _ls = 99;
    for (var _i = 0; _i < array_length(_ids); _i++)
    {
        var _s = kbr_pslot(_ids[_i]);
        if (_s > _so && _s < _bs)
        {
            _bs = _s;
            _best = _ids[_i];
        }
        if (_s < _ls)
        {
            _ls = _s;
            _low = _ids[_i];
        }
    }
    return (_best >= 0) ? _best : _low;
}

// AUTO: who is worth watching now (kept at least 3 seconds; the final two take turns every 6)
function kbr_spec_auto(_M, _ids)
{
    var _vw = _M.vw;
    if (_vw.auto_t > 0)
    {
        _vw.auto_t--;
        var _still = false;
        for (var _i = 0; _i < array_length(_ids); _i++)
        {
            if (_ids[_i] == _M.spect)
                _still = true;
        }
        if (_still)
            return 0;
    }
    var _pick = -1;
    var _why = "";
    if (array_length(_ids) == 2 || (_M.ft_on && array_length(_ids) <= 2))
    {
        _pick = (_M.spect == _ids[0] && array_length(_ids) > 1) ? _ids[1] : _ids[0];
        _why = "FINAL TWO";
        _vw.auto_t = 180;
    }
    if (_pick < 0)
    {
        for (var _i = 0; _i < array_length(_ids); _i++)
        {
            var _r = kbr_rv(_M, _ids[_i]);
            if (_r.skt > 0)
            {
                _pick = _ids[_i];
                _why = "SKILL";
                _vw.auto_t = 120;
                break;
            }
        }
    }
    if (_pick < 0)
    {
        var _lf = 0.3;
        for (var _i = 0; _i < array_length(_ids); _i++)
        {
            var _p = kbr_st_player(_M, _ids[_i]);
            if (is_undefined(_p))
                continue;
            var _f = kfo_jn(_p, "hp", 0) / max(1, kfo_jn(_p, "mh", 1));
            if (_f < _lf)
            {
                _lf = _f;
                _pick = _ids[_i];
                _why = "LOW HP";
            }
        }
        if (_pick >= 0)
            _vw.auto_t = 120;
    }
    if (_pick < 0)
    {
        _pick = kbr_spec_leader(_M, _ids);
        _why = "LEADING";
        _vw.auto_t = 90;
    }
    _M.spect = _pick;
    _vw.auto_why = _why;
    return 1;
}

// a spectator key (fixed keys; a key a match action already uses there - PLAYER LIST, GIVE UP, QUICK SETTINGS - is left to it)
function kbr_spec_key(_ch)
{
    var _k = ord(_ch);
    if (_k == kfo_key("list") || _k == kfo_key("quit") || _k == kfo_key("quick"))
        return false;
    return keyboard_check_pressed(_k);
}

// every step while watching: the hidden SOUL, who is followed, the watching keys
function kbr_spectate_tick()
{
    // the hidden SOUL is untouchable every step - DRBR 1.0.3: typing in the chat too (this used to come after the chat's
    // return: a watcher typing could be hit, and the party-down check took them out of the match)
    global.inv = 9999;
    with (obj_heart)
    {
        visible = false;
        canmove = 0;
    }
    // build 48: the keys are the chat's while you type
    if (kfo_chat_typing())
        return 0;
    var _M = kbr_match();
    if (!variable_struct_exists(_M, "vw"))
        _M.vw = kbr_vw_new();
    var _vw = _M.vw;
    var _V = kfo_view();
    var _ids = kbr_alive_ids();
    // you just went OUT: your SOUL's shatter plays first, then the camera picks someone
    if (_M.me && _M.out && _vw.out_t < 0)
        _vw.out_t = 45;
    if (_vw.out_t > 0)
    {
        _vw.out_t--;
        if (_vw.out_t > 0)
            return 1;
    }
    if (array_length(_ids) == 0)
        return 0;
    var _at = -1;
    for (var _i = 0; _i < array_length(_ids); _i++)
    {
        if (_ids[_i] == _M.spect)
            _at = _i;
    }
    if (_at < 0)
    {
        // nobody followed yet: the leader (AUTO: its own pick); the one followed went OUT: the next one after them
        var _old = _M.spect;
        if (_vw.cam == 2)
        {
            _vw.auto_t = 0;
            kbr_spec_auto(_M, _ids);
        }
        else
            _M.spect = (_old >= 0 && _vw.picked) ? kbr_spec_after(_ids, _old) : kbr_spec_leader(_M, _ids);
        _vw.picked = true;
        var _p = kbr_st_player(_M, _M.spect);
        if (!is_undefined(_p))
        {
            _vw.banner = "WATCHING " + string_upper(kfo_js(_p, "n", "?"));
            _vw.banner_t = 60;
        }
        for (var _i = 0; _i < array_length(_ids); _i++)
        {
            if (_ids[_i] == _M.spect)
                _at = _i;
        }
        if (_at < 0)
            _at = 0;
    }
    if (_vw.cam == 2)
        kbr_spec_auto(_M, _ids);
    if (_vw.qs || _M.ended)
        return 1;
    // < >, LB / RB: the previous / next player (in ZOOM the arrows move the lens instead)
    var _prev = knight_pad_pressed(gp_shoulderl) || (_vw.cam != 3 && left_p());
    var _next = knight_pad_pressed(gp_shoulderr) || (_vw.cam != 3 && right_p());
    if (_M.tab && (up_p() || down_p()))
    {
        _prev = up_p();
        _next = down_p();
    }
    if (_prev || _next)
    {
        _at = (_at + (_next ? 1 : (array_length(_ids) - 1))) mod array_length(_ids);
        _M.spect = _ids[_at];
        if (_vw.cam == 2)
        {
            _vw.cam = 0;
            _vw.banner = "CAMERA: FOLLOW";
            _vw.banner_t = 45;
        }
        _vw.zoom_x = -1;
    }
    // Z / confirm: the next camera mode (remembered: MATCH VIEW > CAMERA)
    if (button1_p())
    {
        _vw.cam = (_vw.cam + 1) mod 4;
        _V.cam = _vw.cam;
        _vw.auto_t = 0;
        _vw.zoom_x = -1;
        _vw.banner = "CAMERA: " + kbr_cam_name(_vw.cam);
        _vw.banner_t = 45;
        kfo_ini_save();
    }
    // X / cancel in ZOOM: 2x <-> 3x
    if (_vw.cam == 3 && button2_p())
    {
        _vw.zoom = (_vw.zoom == 2) ? 3 : 2;
        _V.zoom = _vw.zoom;
        kfo_ini_save();
    }
    // C / menu: the watching HUD FULL / SMALL / OFF
    if (button3_p())
    {
        _V.shud = (_V.shud + 1) mod 3;
        kfo_ini_save();
    }
    if (kbr_spec_key("V"))
        _vw.vhide = !_vw.vhide;
    if (kbr_spec_key("N"))
        _vw.names_t = (_vw.names_t < 0) ? (1 - _V.names) : (1 - _vw.names_t);
    if (kbr_spec_key("I"))
        _vw.stats = !_vw.stats;
    if (kbr_spec_key("H"))
    {
        _V.help = 1 - _V.help;
        kfo_ini_save();
    }
    // ZOOM: the lens starts on the one followed; the arrows move it (inside the screen)
    if (_vw.cam == 3)
    {
        if (_vw.zoom_x < 0)
        {
            var _q = variable_struct_exists(_M.ps, string(_M.spect)) ? variable_struct_get(_M.ps, string(_M.spect)) : undefined;
            _vw.zoom_x = is_struct(_q) ? (kbr_ps_x(_q) + kbr_soul_in() + 8 - knight_cam_x()) : 320;
            _vw.zoom_y = is_struct(_q) ? (kbr_ps_y(_q) + kbr_soul_in() + 8 - knight_cam_y()) : 170;
        }
        var _sp = 4;
        if (left_h())
            _vw.zoom_x -= _sp;
        if (right_h())
            _vw.zoom_x += _sp;
        if (up_h())
            _vw.zoom_y -= _sp;
        if (down_h())
            _vw.zoom_y += _sp;
        var _hw = 100 / _vw.zoom;
        var _hh = 75 / _vw.zoom;
        _vw.zoom_x = clamp(_vw.zoom_x, _hw, 640 - _hw);
        _vw.zoom_y = clamp(_vw.zoom_y, _hh, 480 - _hh);
    }
    return 1;
}

// ---------- the watching HUD (top left, where a player's skills are) ----------
// FULL: the one you follow - name, place in the list, ALIVE / OUT, HP, gauge, their skill slots and hold slot, what they have
// switched on, their ping - the room's counts, the camera, sudden death. SMALL: name, HP, camera. OFF: nothing.
function kbr_hud_spec(xx, yy, _M)
{
    var _V = kfo_view();
    if (_V.shud == 2)
        return 0;
    var _vw = _M.vw;
    var _p = kbr_st_player(_M, _M.spect);
    var _x = xx + 8;
    var _y = yy + 8;
    var _w = 224;
    var _full = (_V.shud == 0);
    var _h = _full ? 104 : 44;
    draw_set_font(fnt_small);
    draw_set_alpha(0.75);
    draw_set_color(c_black);
    draw_rectangle(_x - 2, _y - 2, _x + _w, _y + _h, false);
    draw_set_alpha(1);
    var _cam = kbr_cam_name(_vw.cam) + ((_vw.cam == 2 && _vw.auto_why != "") ? (": " + _vw.auto_why) : "") + ((_vw.cam == 3) ? (" " + string(_vw.zoom) + "X") : "");
    if (is_undefined(_p))
    {
        kbr_hud_text(_x + 2, _y, "WATCHING", c_white);
        kbr_hud_text(_x + 2, _y + 14, kbr_fit("CAMERA: " + _cam, _w - 6), c_ltgray);
        return 1;
    }
    var _pid = kfo_jn(_p, "pid", -1);
    var _col = kbr_soul_col(_p, _pid);
    var _al = (kfo_jn(_p, "al", 0) == 1);
    kfo_soul_draw(_x + 1, _y + 1, 0.625, _col, 1, -1);
    var _st = _al ? "ALIVE" : kbr_out_text(kfo_jn(_p, "pl", 0));
    draw_set_halign(fa_right);
    kbr_hud_text(_x + _w - 4, _y, _st, _al ? c_lime : c_gray);
    draw_set_halign(fa_left);
    kbr_hud_text(_x + 16, _y, kbr_fit(kfo_js(_p, "n", "?") + "  P" + string(kbr_pslot(_pid) + 1), _w - 70), kfo_col_text(_col));
    // HP
    var _hp = round(kfo_jn(_p, "hp", 0));
    var _mh = max(1, round(kfo_jn(_p, "mh", 1)));
    var _f = clamp(_hp / _mh, 0, 1);
    kbr_hud_text(_x + 2, _y + 14, "HP", c_white);
    draw_set_color(c_maroon);
    draw_rectangle(_x + 24, _y + 17, _x + 144, _y + 23, false);
    draw_set_color((_f > 0.5) ? c_lime : ((_f > 0.25) ? c_yellow : c_red));
    if (_f > 0)
        draw_rectangle(_x + 24, _y + 17, _x + 24 + max(1, round(120 * _f)), _y + 23, false);
    kbr_hud_text(_x + 150, _y + 14, string(_hp) + "/" + string(_mh), c_white);
    if (!_full)
    {
        kbr_hud_text(_x + 2, _y + 28, kbr_fit("CAMERA: " + _cam, _w - 6), c_ltgray);
        return 1;
    }
    // the gauge
    var _g = clamp(kfo_jn(_p, "g", 0), 0, 100);
    kbr_hud_text(_x + 2, _y + 27, "TP", c_orange);
    draw_set_color(make_color_rgb(70, 50, 10));
    draw_rectangle(_x + 24, _y + 30, _x + 144, _y + 36, false);
    draw_set_color(c_orange);
    if (_g > 0)
        draw_rectangle(_x + 24, _y + 30, _x + 24 + max(1, round(1.2 * _g)), _y + 36, false);
    kbr_hud_text(_x + 150, _y + 27, string(floor(_g)), c_orange);
    // the skill slots and the hold slot as they have them (DRBR 1.0.3: their diamonds with the skills' pictures, the picked one
    // framed, its name beside them - it was a line of short names); what is switched on
    var _q = kfo_ja(_p, "q");
    var _qs = kfo_jn(_p, "qs", -1);
    var _qh = kfo_jn(_p, "qh", -1);
    var _dy = _y + 50;
    var _pk = "";
    for (var _i = 0; _i <= 4; _i++)
    {
        var _hold = (_i == 4);
        var _sid = _hold ? _qh : ((_i < array_length(_q) && is_numeric(_q[_i])) ? _q[_i] : -1);
        var _dx = _x + 12 + (_i * 21) + (_hold ? 8 : 0);
        var _has = (_sid > 0);
        var _pick = (!_hold && _i == _qs && _has);
        kbr_diamond(_dx, _dy, 9, _has ? (kbr_skill_red(_sid) ? make_color_rgb(235, 60, 60) : make_color_rgb(70, 220, 100)) : make_color_rgb(60, 60, 60), _pick, !_has);
        if (_has)
            kbr_skill_icon(_sid, _dx, _dy, 1, 0.5);
        if (_pick)
            _pk = kbr_skill_fname(_sid);
    }
    // (the fifth, a little apart, is the HOLD slot - as in your own row)
    draw_set_font(fnt_small);
    if (_pk != "")
        kbr_hud_text(_x + 124, _dy - 6, kbr_fit(_pk, _w - 128), c_yellow);
    var _sk = kfo_jn(_p, "sk", 0);
    var _on = "";
    if ((_sk & 1) != 0)
        _on += "SHIELD ";
    if ((_sk & 2) != 0)
        _on += "REGEN ";
    if ((_sk & 4) != 0)
        _on += "REFLECT ";
    if ((_sk & 8) != 0)
        _on += "BREATH ";
    var _lat = kfo_jn(_p, "lat", -1);
    kbr_hud_text(_x + 2, _y + 64, kbr_fit(((_on == "") ? "" : _on) + ((kfo_jn(_p, "bot", 0) == 1) ? "BOT" : ((_lat >= 0) ? ("PING " + kbr_ping_text(_lat)) : "")), _w - 6), c_aqua);
    // the room
    var _an = 0;
    var _out = 0;
    var _pl = kfo_ja(_M.st, "pl");
    for (var _i = 0; _i < array_length(_pl); _i++)
    {
        if (kfo_jn(_pl[_i], "al", 0) == 1)
            _an++;
        else
            _out++;
    }
    kbr_hud_text(_x + 2, _y + 77, kbr_fit(string(_an) + " ALIVE  " + string(_out) + " OUT  " + string(kfo_jn(_M.st, "sc", 0)) + " WATCHING", _w - 6), c_white);
    var _sd = kbr_sd_text(_M);
    kbr_hud_text(_x + 2, _y + 90, kbr_fit("CAMERA: " + _cam + ((_sd != "") ? ("   " + _sd) : ""), _w - 6), c_ltgray);
    return 1;
}

// "~60MS": a round trip in tens of milliseconds (never more precise than it is measured)
function kbr_ping_text(_ms)
{
    if (_ms < 0)
        return "?";
    return "~" + string(max(10, round(_ms / 10) * 10)) + "MS";
}

// sudden death now ("SUDDEN DEATH"), coming ("SD IN 1:20"), or "" when the room has none
function kbr_sd_text(_M)
{
    if (_M.sd_on)
        return "SUDDEN DEATH";
    var _t0 = kbr_tl_sd_t0(_M.tl);
    if (_t0 < 0)
        return "";
    var _t = kbr_now();
    if (_t < 0)
        return "";
    return "SD IN " + kfo_time_text(max(0, _t0 - _t));
}

// the watching keys (H hides it; KEY HINTS off hides it too)
function kbr_hud_help(xx, yy, _M)
{
    var _V = kfo_view();
    if (!_V.help || !_V.hints || _M.vw.qs)
        return 0;
    var _l = ["< >: FOLLOW ANOTHER   TAB: LIST", "Z: CAMERA   C: HUD   V: SOULS", "N: NAMES   I: STATS   H: HIDE", kfo_key_label("quick") + ": QUICK   " + kfo_key_label("quit") + ": ROOM"];
    if (_M.vw.cam == 3)
        _l[0] = "ARROWS: MOVE THE LENS   X: 2X / 3X";
    // the watching HUD HIDDEN: only the way back to it
    if (_V.shud == 2)
        _l = ["C: SHOW THE HUD"];
    var _x = xx + 8;
    // (DRBR: the box ends above the party panel - it used to reach into it, over the first name)
    var _y = (yy + 436) - (array_length(_l) * 13);
    draw_set_font(fnt_small);
    draw_set_alpha(0.6);
    draw_set_color(c_black);
    draw_rectangle(_x - 2, _y - 2, _x + 200, _y + (array_length(_l) * 13), false);
    draw_set_alpha(1);
    for (var _i = 0; _i < array_length(_l); _i++)
        kbr_hud_text(_x + 2, _y + (_i * 13), kbr_fit(_l[_i], 196), c_ltgray);
    return 1;
}

// I while watching: everybody's match so far (survival, damage taken, healing, grazes, skills, place)
function kbr_hud_stats(xx, yy, _M)
{
    if (!_M.vw.stats || !is_struct(_M.st))
        return 0;
    var _pl = kfo_rank(kfo_ja(_M.st, "pl"));
    var _x0 = xx + 70;
    // (DRBR 1.0.3: under the watching card - FULL is taller now, with the skill diamonds)
    var _sh = kfo_view().shud;
    var _y0 = yy + ((_sh == 0) ? 122 : 70);
    var _h = 40 + (array_length(_pl) * 20);
    // an overlay while it is open: solid, over the lists under it (nothing shows through)
    draw_set_alpha(1);
    draw_set_color(c_black);
    draw_rectangle(_x0, _y0, _x0 + 500, _y0 + _h, false);
    draw_set_alpha(1);
    draw_set_color(c_white);
    draw_rectangle(_x0, _y0, _x0 + 500, _y0 + _h, true);
    draw_set_font(fnt_small);
    var _cx = [10, 140, 200, 260, 320, 380, 440];
    var _hd = ["PLAYER", "TIME", "TAKEN", "HEALED", "GRAZES", "SKILLS", "PLACE"];
    for (var _c = 0; _c < 7; _c++)
        kbr_hud_text(_x0 + _cx[_c], _y0 + 8, _hd[_c], c_gray);
    var _now = max(0, kbr_now() - _M.tl.intro);
    for (var _i = 0; _i < array_length(_pl); _i++)
    {
        var _p = _pl[_i];
        var _y = _y0 + 28 + (_i * 20);
        var _al = (kfo_jn(_p, "al", 0) == 1);
        var _pid = kfo_jn(_p, "pid", -2);
        kbr_hud_text(_x0 + _cx[0], _y, kbr_fit(kfo_js(_p, "n", "?"), 124), (_pid == global.kfo.my) ? c_yellow : kfo_col_text(kbr_soul_col(_p, _pid)));
        var _ft = _al ? _now : kfo_jn(_p, "ft", 0);
        kbr_hud_text(_x0 + _cx[1], _y, kfo_time_text(_ft), c_white);
        kbr_hud_text(_x0 + _cx[2], _y, string(round(kfo_jn(_p, "tk", 0))), c_red);
        kbr_hud_text(_x0 + _cx[3], _y, string(round(kfo_jn(_p, "hl", 0))), c_lime);
        kbr_hud_text(_x0 + _cx[4], _y, string(round(kfo_jn(_p, "gz", 0))), c_aqua);
        kbr_hud_text(_x0 + _cx[5], _y, string(kfo_jn(_p, "sg", 0)), c_white);
        kbr_hud_text(_x0 + _cx[6], _y, _al ? "-" : ("#" + string(kfo_jn(_p, "pl", 0))), _al ? c_lime : c_gray);
    }
    return 1;
}

// a short notice over the box's top edge (who went OUT with FULL notices, who you watch, the camera) - never over the box
function kbr_hud_banner(xx, yy, _M)
{
    var _vw = _M.vw;
    if (_vw.banner_t <= 0 || _vw.banner == "")
        return 0;
    draw_set_font(fnt_small);
    draw_set_halign(fa_center);
    draw_set_alpha(min(1, _vw.banner_t / 15));
    var _t = kbr_fit(_vw.banner, 300);
    var _w = string_width(_t) + 12;
    // (DRBR: under the top middle's stack - kbr_hud_draw - and never lower than just over the box's top edge)
    var _by = clamp(variable_struct_exists(_M, "hud_ty") ? _M.hud_ty : (yy + 72), yy + 72, yy + 78);
    draw_set_color(c_black);
    draw_rectangle(xx + 320 - (_w / 2), _by, xx + 320 + (_w / 2), _by + 15, false);
    kbr_hud_text(xx + 320, _by + 1, _t, c_white);
    draw_set_alpha(1);
    draw_set_halign(fa_left);
    return 1;
}

// MATCH INFO: the cycle, how many are standing, the time, the room's preset and sudden death (under the knight's lines)
function kbr_hud_info(xx, yy, _M)
{
    if (!kfo_view().info || !_M.go || !is_struct(_M.st))
        return 0;
    draw_set_font(fnt_small);
    draw_set_halign(fa_center);
    var _k = (_M.R.ph == "arm") ? _M.R.arm_k : _M.R.k;
    var _t = max(0, kbr_now() - _M.tl.intro);
    var _l1 = "#" + string(max(0, _k) + 1) + "  " + string(kfo_alive_now()) + "/" + string(_M.sn) + " ALIVE  " + kfo_time_text(_t);
    var _sd = kbr_sd_text(_M);
    var _pre = variable_struct_exists(_M.set, "pre") ? string(_M.set.pre) : "";
    var _l2 = ((_pre != "") ? _pre : "CUSTOM") + ((_sd != "") ? ("  " + _sd) : "  NO SUDDEN DEATH");
    // (DRBR: the top middle's stack - kbr_hud_draw - its next two lines)
    var _iy = variable_struct_exists(_M, "hud_ty") ? _M.hud_ty : (yy + 36);
    kbr_hud_text(xx + 340, _iy, kbr_fit(_l1, 176), c_white);
    kbr_hud_text(xx + 340, _iy + 13, kbr_fit(_l2, 176), _M.sd_on ? make_color_rgb(255, 90, 90) : c_ltgray);
    _M.hud_ty = _iy + 28;
    draw_set_halign(fa_left);
    return 1;
}

// the connection, bottom right: NETWORK STATS shows the ping and its quality; trouble shows whatever the setting
// (no answer to a ping within 2 s counted as lost; the host's news late; the game measuring its clock again; a new host)
// the round trip to the host as shown to the player: the running average of the clock pings (-1: none yet)
function kbr_rtt_shown(_M)
{
    if (!is_struct(_M) || !variable_struct_exists(_M, "ck"))
        return -1;
    if (variable_struct_exists(_M.ck, "ra") && _M.ck.ra >= 0)
        return _M.ck.ra;
    return _M.ck.rtt;
}

function kbr_net_state(_M)
{
    var _o = global.kfo;
    var _s = { ping: -1, q: "", warn: "", col: c_lime, loss: -1 };
    if (kfo_is_host() || _o.mode == "local")
    {
        _s.q = kfo_is_host() ? "HOSTING" : "PRACTICE";
        return _s;
    }
    _s.ping = round(kbr_rtt_shown(_M));
    if (_s.ping < 0)
    {
        _s.q = "MEASURING";
        _s.col = c_gray;
    }
    else if (_s.ping < 100)
        _s.q = "GOOD";
    else if (_s.ping < 200)
    {
        _s.q = "OK";
        _s.col = c_yellow;
    }
    else
    {
        _s.q = "POOR";
        _s.col = c_red;
    }
    // lost pings among the last ones old enough to have an answer
    if (variable_struct_exists(_M.ck, "pl"))
    {
        var _n = 0;
        var _lost = 0;
        for (var _i = 0; _i < array_length(_M.ck.pl); _i++)
        {
            var _e = _M.ck.pl[_i];
            if (current_time - _e[0] < 2000)
                continue;
            _n++;
            if (!_e[1])
                _lost++;
        }
        if (_n >= 10)
        {
            _s.loss = round((_lost * 100) / _n);
            if (_s.loss >= 10)
            {
                _s.warn = "PACKET LOSS ~" + string(_s.loss) + "%";
                _s.col = c_orange;
            }
        }
    }
    if (variable_struct_exists(_M.vw, "lst_t") && _M.vw.lst_t > 0 && current_time - _M.vw.lst_t > 2500 && !_M.ended)
    {
        _s.warn = "NO NEWS FROM THE HOST (" + string(floor((current_time - _M.vw.lst_t) / 1000)) + "S)";
        _s.col = c_red;
    }
    if (_M.resyncs > 0 && variable_struct_exists(_M, "t_rs_local") && current_time - _M.t_rs_local < 3000)
        _s.warn = "SYNCING WITH THE HOST...";
    if (variable_struct_exists(_o, "t_newhost") && current_time - _o.t_newhost < 5000)
        _s.warn = "NEW HOST: " + string_upper(_o.newhost_n);
    return _s;
}

function kbr_hud_net(xx, yy, _M)
{
    var _s = kbr_net_state(_M);
    var _V = kfo_view();
    if (!_V.net && _s.warn == "")
        return 0;
    draw_set_font(fnt_small);
    draw_set_halign(fa_right);
    // DRBR: in the SOULS list's header, left of the network light it explains (it used to be drawn over Ralsei's HP in the
    // party panel, then over the chat): the warning when there is one, else the ping and its quality
    var _t = "";
    if (_s.warn != "")
        _t = _s.warn;
    else
        _t = ((_s.ping >= 0) ? (kbr_ping_text(_s.ping) + " ") : "") + _s.q + ((_s.loss >= 0 && _s.loss < 10) ? (" " + string(_s.loss) + "%") : "");
    var _hx0 = (xx + 628) - 157;
    var _ny = yy + 8;
    if (_s.warn != "")
    {
        // trouble: over the whole header (the SOULS count steps aside while it lasts)
        _t = kbr_fit(_t, (xx + 616) - _hx0);
        draw_set_color(c_black);
        draw_rectangle(_hx0 - 2, _ny - 1, xx + 617, _ny + 8, false);
    }
    else
    {
        var _hw = string_width("SOULS " + string(kfo_alive_now()) + "/" + string(_M.sn)) + 8;
        _t = kbr_fit(_t, max(40, (xx + 616) - (_hx0 + _hw)));
        draw_set_alpha(0.6);
        draw_set_color(c_black);
        draw_rectangle((xx + 616) - string_width(_t) - 2, _ny - 1, xx + 617, _ny + 8, false);
        draw_set_alpha(1);
    }
    kbr_hud_text(xx + 616, _ny, _t, _s.col);
    draw_set_halign(fa_left);
    return 1;
}

// ---------- QUICK SETTINGS (its key, Q unless changed in KEYBINDS; START on a controller) ----------
// A small box left of the bullet box: the other SOULs, their opacity, names, your highlight, the effects, the camera and HUD
// while watching, the game's own sound and music volume, the network stats and the match info. Every change shows at once
// and is kept (knightfights_online.ini; the volumes are the game's own settings, flag 15 / 16, as its CONFIG sets them).
// While it is open during play your SOUL stays where it is (the box says so) and your match keys wait.
function kbr_qs_rows(_M)
{
    var _spec = (_M.out || !_M.me);
    var _l = ["show", "sop", "names"];
    if (!_spec)
        array_push(_l, "hl");
    if (_spec)
        array_push(_l, "cam", "shud");
    array_push(_l, "chat", "sfx", "mus", "close");
    return _l;
}

function kbr_qs_label(_id, _M)
{
    var _V = kfo_view();
    switch (_id)
    {
        case "show": return ["OTHER SOULS", _V.show ? "SHOWN" : "HIDDEN"];
        case "sop": return ["SOUL OPACITY", string(_V.sop) + "%"];
        case "names": return ["SOUL NAMES", _V.names ? "ON" : "OFF"];
        case "chat": return ["CHAT", _V.chat ? "SHOWN" : "HIDDEN"];
        case "hl": return ["HIGHLIGHT ME", _V.hl ? "ON" : "OFF"];
        case "skfx": return ["EFFECTS", (_V.skfx == 0) ? "OFF" : ((_V.skfx == 1) ? "REDUCED" : "FULL")];
        case "cam": return ["CAMERA", kbr_cam_name(_M.vw.cam)];
        case "shud": return ["WATCH HUD", kbr_shud_name(_V.shud)];
        case "sfx": return ["SFX VOLUME", string(round(kbr_vol_get(15) * 100)) + "%"];
        case "mus": return ["MUSIC VOLUME", string(round(kbr_vol_get(16) * 100)) + "%"];
        case "net": return ["NETWORK STATS", _V.net ? "ON" : "OFF"];
        case "info": return ["MATCH INFO", _V.info ? "ON" : "OFF"];
    }
    return ["CLOSE", ""];
}

// the game's own volume flags (15: sound effects, 16: music), 0-1
function kbr_vol_get(_f)
{
    if (!variable_global_exists("flag") || !is_array(global.flag) || array_length(global.flag) <= _f || !is_real(global.flag[_f]))
        return 1;
    return clamp(global.flag[_f], 0, 1);
}

// set one as the game's CONFIG does: sound effects through their audio group, music on the songs playing now
function kbr_vol_set(_f, _v)
{
    _v = clamp(round(_v * 20) / 20, 0, 1);
    var _old = kbr_vol_get(_f);
    global.flag[_f] = _v;
    if (_f == 15)
        audio_group_set_gain(audio_sfx, _v, 0);
    else if (_f == 16)
    {
        var _l = [];
        if (variable_global_exists("batmusic") && is_array(global.batmusic) && array_length(global.batmusic) > 1)
            array_push(_l, global.batmusic[1]);
        if (variable_global_exists("currentsong") && is_array(global.currentsong) && array_length(global.currentsong) > 1)
            array_push(_l, global.currentsong[1]);
        for (var _i = 0; _i < array_length(_l); _i++)
        {
            var _s = _l[_i];
            if (is_real(_s) && _s >= 0 && audio_is_playing(_s))
                audio_sound_gain(_s, (_old > 0) ? (audio_sound_get_gain(_s) * (_v / _old)) : _v, 0);
        }
    }
    return _v;
}

// the keys of the box (true: it had the keys this step)
function kbr_qs_tick(_M)
{
    if (kfo_chat_typing())
        return false;
    var _vw = _M.vw;
    if (!_vw.qs)
    {
        // build 47: OTHER SOULS (V by default) shows / hides the other players' SOULs at once, for this game only
        if (_M.me && !_M.out && !_M.ended && kbr_key_pressed("souls"))
        {
            var _Vs = kfo_view();
            _Vs.show = 1 - _Vs.show;
            _vw.banner = _Vs.show ? ("OTHER SOULS SHOWN (" + string(_Vs.sop) + "%)") : "OTHER SOULS HIDDEN";
            _vw.banner_t = 60;
            kfo_ini_save();
        }
        if (kbr_key_pressed("quick") && !_M.ended && !kfo_tut_on())
        {
            _vw.qs = true;
            _vw.qs_row = 0;
            _vw.qs_hold = 0;
            return true;
        }
        return false;
    }
    var _rows = kbr_qs_rows(_M);
    var _n = array_length(_rows);
    if (kbr_key_pressed("quick") || button2_p() || _M.ended)
    {
        _vw.qs = false;
        kfo_ini_save();
        return true;
    }
    if (up_p())
        _vw.qs_row = (_vw.qs_row + _n - 1) mod _n;
    if (down_p())
        _vw.qs_row = (_vw.qs_row + 1) mod _n;
    _vw.qs_row = clamp(_vw.qs_row, 0, _n - 1);
    var _d = 0;
    if (left_p())
        _d = -1;
    if (right_p() || button1_p())
        _d = 1;
    // a slider: < > held keeps it moving (after a third of a second, a step every other frame)
    if (!variable_struct_exists(_vw, "qs_hold"))
        _vw.qs_hold = 0;
    if (kfo_is_slider(_rows[_vw.qs_row]) && (left_h() || right_h()))
    {
        _vw.qs_hold++;
        if (_d == 0 && _vw.qs_hold >= 10 && (_vw.qs_hold mod 2) == 0)
            _d = left_h() ? -1 : 1;
    }
    else
        _vw.qs_hold = 0;
    if (_d == 0)
        return true;
    var _V = kfo_view();
    var _o = global.kfo;
    switch (_rows[_vw.qs_row])
    {
        case "show": _V.show = 1 - _V.show; break;
        case "sop": _V.sop = clamp(_V.sop + (_d * 5), kfo_sop_min(), 100); _o.sop = _V.sop; break;
        case "names": _V.names = 1 - _V.names; _o.names = _V.names; _vw.names_t = -1; break;
        case "hl": _V.hl = 1 - _V.hl; break;
        case "chat": _V.chat = 1 - _V.chat; break;
        case "cam": _vw.cam = (_vw.cam + 4 + _d) mod 4; _V.cam = _vw.cam; _vw.auto_t = 0; _vw.zoom_x = -1; break;
        case "shud": _V.shud = (_V.shud + 3 + _d) mod 3; break;
        case "sfx": kbr_vol_set(15, kbr_vol_get(15) + (_d * 0.05)); break;
        case "mus": kbr_vol_set(16, kbr_vol_get(16) + (_d * 0.05)); break;
        case "net": _V.net = 1 - _V.net; break;
        case "info": _V.info = 1 - _V.info; break;
        case "close":
            if (button1_p())
            {
                _vw.qs = false;
                kfo_ini_save();
            }
            return true;
    }
    kfo_ini_save();
    return true;
}

function kbr_hud_qs(xx, yy, _M)
{
    var _vw = _M.vw;
    if (!_vw.qs)
        return 0;
    var _rows = kbr_qs_rows(_M);
    var _x = xx + 8;
    var _y = yy + 100;
    var _w = 228;
    var _play = (_M.me && !_M.out);
    var _h = 22 + (array_length(_rows) * 15) + (_play ? 16 : 0) + 14;
    draw_set_font(fnt_small);
    draw_set_alpha(0.88);
    draw_set_color(c_black);
    draw_rectangle(_x - 2, _y - 2, _x + _w, _y + _h, false);
    draw_set_alpha(1);
    draw_set_color(c_white);
    draw_rectangle(_x - 2, _y - 2, _x + _w, _y + _h, true);
    kbr_hud_text(_x + 4, _y + 2, "QUICK SETTINGS", c_yellow);
    for (var _i = 0; _i < array_length(_rows); _i++)
    {
        var _ly = _y + 20 + (_i * 15);
        var _lv = kbr_qs_label(_rows[_i], _M);
        var _hot = (_vw.qs_row == _i);
        kbr_hud_text(_x + 14, _ly, _lv[0], _hot ? c_yellow : c_white);
        if (_lv[1] != "")
        {
            draw_set_halign(fa_right);
            kbr_hud_text(_x + _w - 6, _ly, (_hot ? "< " : "") + _lv[1] + (_hot ? " >" : ""), _hot ? c_yellow : c_ltgray);
            draw_set_halign(fa_left);
        }
        if (kfo_is_slider(_rows[_i]))
            kfo_slider_draw(_x + 104, _x + 166, _ly + 1, real(string_digits(_lv[1])), _hot);
        if (_hot)
            kfo_soul_draw(_x + 3, _ly + 2, 0.5, c_red, 1, -1);
    }
    var _fy = _y + 22 + (array_length(_rows) * 15);
    if (_play)
    {
        kbr_hud_text(_x + 4, _fy, "YOUR SOUL STAYS STILL WHILE THIS IS OPEN", c_orange);
        _fy += 16;
    }
    kbr_hud_text(_x + 4, _fy, kbr_fit(kfo_key_label("quick") + " / X: CLOSE    < >: CHANGE", _w - 8), c_gray);
    return 1;
}

// the End Step while the box is open during play: the SOUL's own move of this step is taken back (an attack that moves the
// SOUL by itself still does: only the step's input move is undone, and the SOUL stays inside the box)
function kbr_qs_hold_soul(_M)
{
    if ((!_M.vw.qs && !kfo_chat_typing()) || _M.out || !_M.me || !instance_exists(obj_heart))
        return 0;
    with (obj_heart)
    {
        if (canmove && (x != xprevious || y != yprevious) && variable_instance_exists(id, "px") && (px != 0 || py != 0))
        {
            x = xprevious;
            y = yprevious;
        }
    }
    return 1;
}

// ---------- ZOOM: the lens ----------
// The finished frame is copied (Draw GUI End, kbr_zoom_capture) around the lens and drawn twice or three times as big in a
// corner on the next frame, away from the lens. The game's camera never moves: the bullets the watcher sees are the players'.
global.kbr_lens = -1;
global.kbr_lens_ok = false;

function kbr_zoom_capture()
{
    global.kbr_lens_ok = false;
    var _M = kbr_match();
    if (is_undefined(_M) || !kbr_on() || !variable_struct_exists(_M, "vw") || _M.vw.cam != 3 || !(_M.out || !_M.me) || _M.vw.zoom_x < 0)
        return 0;
    if (!surface_exists(application_surface))
        return 0;
    var _z = _M.vw.zoom;
    var _aw = surface_get_width(application_surface);
    var _ah = surface_get_height(application_surface);
    var _sw = _aw / 640;
    var _sh = _ah / 480;
    var _w = max(8, round((200 / _z) * _sw));
    var _h = max(8, round((150 / _z) * _sh));
    if (!surface_exists(global.kbr_lens) || surface_get_width(global.kbr_lens) != _w || surface_get_height(global.kbr_lens) != _h)
    {
        if (surface_exists(global.kbr_lens))
            surface_free(global.kbr_lens);
        global.kbr_lens = surface_create(_w, _h);
    }
    var _sx = clamp(round((_M.vw.zoom_x - (100 / _z)) * _sw), 0, max(0, _aw - _w));
    var _sy = clamp(round((_M.vw.zoom_y - (75 / _z)) * _sh), 0, max(0, _ah - _h));
    surface_copy_part(global.kbr_lens, 0, 0, application_surface, _sx, _sy, _w, _h);
    global.kbr_lens_ok = true;
    return 1;
}

function kbr_hud_zoom(xx, yy, _M)
{
    if (_M.vw.cam != 3 || _M.vw.zoom_x < 0)
        return 0;
    var _z = _M.vw.zoom;
    var _cw = 200 / _z;
    var _ch = 150 / _z;
    var _cx0 = _M.vw.zoom_x - (_cw / 2);
    var _cy0 = _M.vw.zoom_y - (_ch / 2);
    // the corner the lens is not in (DRBR: both clear of the party panel and of the watching keys' box bottom left)
    var _ix = 432;
    var _iy = 268;
    if (_cx0 + _cw > _ix - 4 && _cy0 + _ch > _iy - 4)
    {
        _ix = 8;
        _iy = 226;
    }
    draw_set_color(c_white);
    draw_set_alpha(0.6);
    draw_rectangle(xx + _cx0, yy + _cy0, xx + _cx0 + _cw, yy + _cy0 + _ch, true);
    draw_set_alpha(1);
    draw_set_color(c_black);
    draw_rectangle(xx + _ix - 2, yy + _iy - 2, xx + _ix + 202, yy + _iy + 152, false);
    if (global.kbr_lens_ok && surface_exists(global.kbr_lens))
        draw_surface_ext(global.kbr_lens, xx + _ix, yy + _iy, 200 / surface_get_width(global.kbr_lens), 150 / surface_get_height(global.kbr_lens), 0, c_white, 1);
    draw_set_color(c_white);
    draw_rectangle(xx + _ix - 2, yy + _iy - 2, xx + _ix + 202, yy + _iy + 152, true);
    draw_set_font(fnt_small);
    kbr_hud_text(xx + _ix + 4, yy + _iy + 2, "ZOOM " + string(_z) + "X", c_yellow);
    return 1;
}

// your skill slots for the others' watching HUD (their skill ids; a slot still spinning in is "?" there - 0)
function kbr_skill_q()
{
    var _M = kbr_match();
    var _o = [];
    if (is_undefined(_M))
        return _o;
    var _S = _M.sk;
    for (var _i = 0; _i < array_length(_S.slots) && _i < 4; _i++)
        array_push(_o, (_S.slots[_i].rev > 0) ? 0 : _S.slots[_i].sid);
    return _o;
}

// ---------- the camera the attacks see, REDUCED SHAKE ----------
// An online match reads the camera without a screen shake (camerax / cameray / __view_get: base overrides in gen_hub.py): an
// attack placing bullets "from the camera" during a shake puts them where every other game puts them, whether that game
// shakes or not. So REDUCED SHAKE (the game's own no-shake flag, 12, set only while your match runs) is only a look.
function kbr_cam_fix_on()
{
    return variable_global_exists("kbr_det") && is_struct(global.kbr_det) && global.kbr_det.on;
}

function kbr_cam_logical(_ax)
{
    var _v = (_ax == 0) ? camera_get_view_x(view_camera[0]) : camera_get_view_y(view_camera[0]);
    with (obj_shake)
    {
        if (active == 1 && beenset && camera == 0 && variable_instance_exists(id, "mycamerax"))
            _v = (_ax == 0) ? mycamerax : mycameray;
    }
    return _v;
}

// every step of a match: REDUCED SHAKE on -> the game's no-shake flag on (its old value kept); off -> the old value back
function kbr_view_shake(_M)
{
    var _V = kfo_view();
    if (!variable_global_exists("flag") || !is_array(global.flag) || array_length(global.flag) <= 12)
        return 0;
    if (_V.shake && !variable_struct_exists(_M.vw, "shk_old"))
    {
        _M.vw.shk_old = global.flag[12];
        global.flag[12] = 1;
    }
    else if (!_V.shake && variable_struct_exists(_M.vw, "shk_old"))
        kbr_view_shake_back(_M);
    return 1;
}

function kbr_view_shake_back(_M)
{
    if (is_struct(_M) && variable_struct_exists(_M, "vw") && variable_struct_exists(_M.vw, "shk_old"))
    {
        global.flag[12] = _M.vw.shk_old;
        variable_struct_remove(_M.vw, "shk_old");
    }
    return 1;
}
