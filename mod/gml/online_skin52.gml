// ===== Build 52: the online SKIN registry =====
// One table says everything about a SKIN (kfo_skin_def). Skins 1-5 are the hub's own playable characters (Kris, Susie,
// Ralsei, Noelle, Flowery: their battle hero is the real one). From 6 on they are ONLINE-ONLY LOOKS (cosmetic: they play
// as Kris underneath - the same HP, speed, SOUL and hitbox as everyone - and only change what is drawn):
//   ow       the overworld walking frames, facing [down, right, up, left] (the cold place, the room)
//   bt       the battle idle (drawn in place of the hero's sprite, feet on the hero's feet, at the hero's scale);
//            bt_flip: mirror it (only for art that faces left - checked per sprite, never assumed); bt_spd: frames a step
//   portrait the dialogue face shown in menus (optional: no portrait = none drawn, never someone else's); port_sc its
//            whole-number scale, port_img its frame, port_dark: white line art made for a black box
//   head     the small head for the HP panel and the lists: a crop [x, y, w, h] of the first down-walking frame (head_spr:
//            of that sprite's first frame instead)
//   col/col2 the UI colours (HP bar, name, selection, portrait frame)
//   cat      the skin page's group: "main" (the party), "flowers" (Chapter 5's flowers), "bosses" (secret bosses), "other"
//   ow_flip  optional, per facing [down, right, up, left]: draw that facing's frames mirrored (art that only faces one way)
//   ow_idle  optional, per facing: the sprite drawn while standing (a look whose walk is not a walk - Spamton's hop)
// Every sprite is looked up by name when used (asset_get_index): a missing one is reported once in the debug log and the
// look falls back to Kris for that part, so a half-installed skin never crashes. To add a skin: its sprites in the build
// (scripts/add_skin_assets.py), one entry below, kfo_skin_count() + 1. See SKINS.txt.

function kfo_skin_count()
{
    return 14;
}

function kfo_skin_defs()
{
    if (variable_global_exists("kfo_skin_cache") && is_array(global.kfo_skin_cache))
        return global.kfo_skin_cache;
    var _l = [undefined];
    array_push(_l, { num: 1, key: "kris", name: "Kris", own: true, cat: "main", col: make_color_rgb(0, 255, 255), col2: c_white });
    array_push(_l, { num: 2, key: "susie", name: "Susie", own: true, cat: "main", col: make_color_rgb(255, 0, 255), col2: c_white });
    array_push(_l, { num: 3, key: "ralsei", name: "Ralsei", own: true, cat: "main", col: make_color_rgb(0, 255, 0), col2: c_white });
    array_push(_l, { num: 4, key: "noelle", name: "Noelle", own: true, cat: "main", col: make_color_rgb(255, 255, 0), col2: c_white });
    array_push(_l, { num: 5, key: "flowery", name: "Flowery", own: true, cat: "flowers", col: make_color_rgb(255, 120, 200), col2: c_white });
    // BERDLY: Chapter 2's Dark World walk; his battle idle facing right (spr_berdlyb_idle_right - the party's side faces
    // right; his left-facing one is spr_berdlyb_idle); his Dark World dialogue face. Blue: #4A9DD9 / #8ED5F0.
    array_push(_l, { num: 6, key: "berdly", name: "Berdly", own: false, bchar: 1, cat: "other",
        ow: ["spr_berdly_walk_down_dw", "spr_berdly_walk_right_dw", "spr_berdly_walk_up_dw", "spr_berdly_walk_left_dw"],
        bt: "spr_berdlyb_idle_right", bt_flip: false, bt_spd: 0.2,
        portrait: "spr_face_berdly_dark", port_img: 0, port_sc: 1, port_dark: true,
        head: [0, 0, 24, 20], col: make_color_rgb(74, 157, 217), col2: make_color_rgb(142, 213, 240) });
    // AQUA: Chapter 5's walk; her battle idle facing right (spr_enemy_aqua_idle_r - spr_enemy_aqua_idle faces left, as an
    // enemy); her dialogue face - the knife (spr_miniface_aqua, the one scr_miniface_init_aquaseth gives her text).
    // Her colours are her art's: the knife's #46E3FF (her dress is #55FFFF), the bow's red #ED1C24.
    array_push(_l, { num: 7, key: "aqua", name: "Aqua", own: false, bchar: 1, cat: "flowers",
        ow: ["spr_aqua_walk_down", "spr_aqua_walk_right", "spr_aqua_walk_up", "spr_aqua_walk_left"],
        bt: "spr_enemy_aqua_idle_r", bt_flip: false, bt_spd: 0.2,
        portrait: "spr_miniface_aqua", port_img: 0, port_sc: 2, port_dark: false,
        head: [0, 0, 20, 19], col: make_color_rgb(70, 227, 255), col2: make_color_rgb(237, 28, 36) });
    // DRBR: the rest of Chapter 5's flowers (the six scr_miniface_init_flowers names: Aqua, Seth, Orange, Green, Yellow, Blue -
    // Flowery leads them as a character of his own, skin 5). Each from Chapter 5's own art; their text faces are the ones that
    // script gives their lines (the book, the fist, the pan, the hat; Blue's own dialogue face).
    // SETH: his four-way walk (his side walk is two frames in Chapter 5 too); battle: his idle facing right (spr_seth_idle_r).
    array_push(_l, { num: 8, key: "seth", name: "Seth", own: false, bchar: 1, cat: "flowers",
        ow: ["spr_seth_walk_down", "spr_seth_walk_right", "spr_seth_walk_up", "spr_seth_walk_left"],
        bt: "spr_seth_idle_r", bt_flip: false, bt_spd: 0.15,
        portrait: "spr_miniface_seth", port_img: 0, port_sc: 2, port_dark: false,
        head: [5, 0, 23, 20], col: make_color_rgb(186, 71, 174), col2: make_color_rgb(205, 143, 205) });
    // ORANGE: his four-way walk; battle: his idle (spr_enemy_orange_idle_base faces left, as an enemy: mirrored - no right-facing
    // idle exists).
    array_push(_l, { num: 9, key: "orange", name: "Orange", own: false, bchar: 1, cat: "flowers",
        ow: ["spr_enemy_orange_walk_down", "spr_enemy_orange_walk_right", "spr_enemy_orange_walk_up", "spr_enemy_orange_walk_left"],
        bt: "spr_enemy_orange_idle_base", bt_flip: true, bt_spd: 0.15,
        portrait: "spr_miniface_orange", port_img: 0, port_sc: 2, port_dark: false,
        head: [5, 0, 18, 15], col: make_color_rgb(249, 120, 77), col2: make_color_rgb(255, 173, 51) });
    // GREEN: Chapter 5 walks him with his two side walks (three-quarter views: spr_enemy_green_walk faces left, _right faces
    // right) and his back (spr_enemy_green_behind): facing down uses his left walk (his face towards you); battle: his wave
    // facing right.
    array_push(_l, { num: 10, key: "green", name: "Green", own: false, bchar: 1, cat: "flowers",
        ow: ["spr_enemy_green_walk", "spr_enemy_green_walk_right", "spr_enemy_green_behind", "spr_enemy_green_walk"],
        bt: "spr_enemy_green_wave_right", bt_flip: false, bt_spd: 0.15,
        portrait: "spr_miniface_green", port_img: 0, port_sc: 2, port_dark: false,
        head: [0, 1, 30, 21], col: make_color_rgb(121, 221, 123), col2: make_color_rgb(164, 248, 95) });
    // YELLOW: his four-way walk; battle: his gun-in-hand idle (spr_yellow_idle, facing right).
    array_push(_l, { num: 11, key: "yellow", name: "Yellow", own: false, bchar: 1, cat: "flowers",
        ow: ["spr_yellow_walk_down", "spr_yellow_walk_right", "spr_yellow_walk_up", "spr_yellow_walk_left"],
        bt: "spr_yellow_idle", bt_flip: false, bt_spd: 0.15,
        portrait: "spr_miniface_yellow", port_img: 0, port_sc: 2, port_dark: false,
        head: [1, 0, 24, 22], col: make_color_rgb(255, 166, 0), col2: make_color_rgb(255, 255, 68) });
    // BLUE: Chapter 5 walks her with her side walks (three-quarter views) and her back (spr_blue_walk_back): facing down uses
    // her right walk (her face towards you); battle: her pirouette facing right (spr_enemy_blue_ballet_r); her dialogue face
    // (spr_face_blue: white line art made for the black box).
    array_push(_l, { num: 12, key: "blue", name: "Blue", own: false, bchar: 1, cat: "flowers",
        ow: ["spr_blue_walk_r", "spr_blue_walk_r", "spr_blue_walk_back", "spr_blue_walk_l"],
        bt: "spr_enemy_blue_ballet_r", bt_flip: false, bt_spd: 0.2,
        portrait: "spr_face_blue", port_img: 0, port_sc: 1, port_dark: true,
        head: [8, 1, 30, 22], col: make_color_rgb(80, 96, 235), col2: make_color_rgb(183, 210, 255) });
    // PINK (Chapter 5's secret boss as a LOOK - never the boss, never her fight): her four-way walk; battle: her idle with the
    // wand (spr_pk_pink_idle, the copy her fight brings) faces left as an enemy: mirrored. Chapter 5 gives her no dialogue face
    // (none is drawn).
    array_push(_l, { num: 13, key: "pink", name: "Pink", own: false, bchar: 1, cat: "bosses",
        ow: ["spr_pink_walk_down", "spr_pink_walk_right", "spr_pink_walk_up", "spr_pink_walk_left"],
        bt: "spr_pk_pink_idle", bt_flip: true, bt_spd: 0.15,
        head: [2, 0, 30, 22], col: make_color_rgb(255, 138, 144), col2: make_color_rgb(167, 60, 92) });
    // SPAMTON - the small one of Chapter 2 (NOT Spamton NEO): Chapter 2 never walks him, he hops (his puppet jump,
    // spr_spamton_jump), so his walk is that hop and standing is his idle (spr_spamton_idle); his art faces left, so facing right
    // mirrors it; battle: his idle, mirrored to face the enemy; his head (spr_spamtonhead) as his face. All of it Chapter 3's own
    // copy (nothing imported). Pink / yellow: his glasses.
    array_push(_l, { num: 14, key: "spamton", name: "Spamton", own: false, bchar: 1, cat: "bosses",
        ow: ["spr_spamton_jump", "spr_spamton_jump", "spr_spamton_jump", "spr_spamton_jump"], ow_flip: [false, true, false, false],
        ow_idle: ["spr_spamton_idle", "spr_spamton_idle", "spr_spamton_idle", "spr_spamton_idle"],
        bt: "spr_spamton_idle", bt_flip: true, bt_spd: 0,
        portrait: "spr_spamtonhead", port_img: 0, port_sc: 2, port_dark: false,
        head_spr: "spr_spamton_idle", head: [0, 0, 25, 20], col: make_color_rgb(255, 174, 201), col2: make_color_rgb(255, 242, 0) });
    global.kfo_skin_cache = _l;
    return _l;
}

function kfo_skin_def(_s)
{
    var _l = kfo_skin_defs();
    if (!is_numeric(_s) || _s < 1 || _s >= array_length(_l))
        return _l[1];
    return _l[floor(_s)];
}

// an online-only look (6 and up)
function kfo_skin_cosmetic(_s)
{
    return !kfo_skin_def(_s).own;
}

// the character the look plays as in battle (its own for 1-5, Kris for the looks)
function kfo_skin_bchar(_s)
{
    var _d = kfo_skin_def(_s);
    return _d.own ? _d.num : _d.bchar;
}

function kfo_skin_col(_s)
{
    return kfo_skin_def(_s).col;
}

function kfo_skin_col2(_s)
{
    return kfo_skin_def(_s).col2;
}

// a sprite of a skin by name (-1 when this build does not have it: logged once)
function kfo_skin_spr(_name)
{
    if (!is_string(_name) || _name == "")
        return -1;
    var _i = asset_get_index(_name);
    if (_i >= 0 && sprite_exists(_i))
        return _i;
    if (!variable_global_exists("kfo_skin_missing"))
        global.kfo_skin_missing = {};
    if (!variable_struct_exists(global.kfo_skin_missing, _name))
    {
        variable_struct_set(global.kfo_skin_missing, _name, 1);
        if (variable_global_exists("kh_dbg_on"))
            kh_dbg_write("SKIN: missing sprite " + _name);
    }
    return -1;
}

// every sprite a look needs, checked (the ONLINE page shows it as MISSING ART instead of picking it)
function kfo_skin_ready(_s)
{
    var _d = kfo_skin_def(_s);
    if (_d.own)
        return true;
    for (var _i = 0; _i < 4; _i++)
    {
        if (kfo_skin_spr(_d.ow[_i]) < 0)
            return false;
    }
    return kfo_skin_spr(_d.bt) >= 0;
}

// its overworld frames (facing 0 down, 1 right, 2 up, 3 left), -1 when it has none (the caller uses Kris's)
function kfo_skin_ow(_s, _f)
{
    var _d = kfo_skin_def(_s);
    if (_d.own)
        return -1;
    return kfo_skin_spr(_d.ow[clamp(_f, 0, 3)]);
}

// DRBR: facing _f of a look drawn mirrored (its art faces one way only)
function kfo_skin_ow_flip(_s, _f)
{
    var _d = kfo_skin_def(_s);
    return !_d.own && variable_struct_exists(_d, "ow_flip") && _d.ow_flip[clamp(_f, 0, 3)];
}

// DRBR: the sprite a look stands in, facing _f (-1: its walk's first frame, as the game's own characters)
function kfo_skin_ow_idle(_s, _f)
{
    var _d = kfo_skin_def(_s);
    if (_d.own || !variable_struct_exists(_d, "ow_idle"))
        return -1;
    return kfo_skin_spr(_d.ow_idle[clamp(_f, 0, 3)]);
}

// DRBR: one overworld frame of skin _s (facing _f, walking _walk with walk frame _fr; standing: its own standing sprite when
// it has one) with its feet where a 2x Kris standing at _x, _y (his top left) has his - mirrored when its art faces the other
// way. _sc: the scale (2 in the rooms, 1 in the menus).
function kfo_skin_ow_draw(_s, _f, _walk, _fr, _x, _y, _sc, _col, _a)
{
    var _spr = kfo_world_skin_spr(_s, _f);
    if (!_walk)
    {
        var _id = kfo_skin_ow_idle(_s, _f);
        if (_id >= 0)
        {
            _spr = _id;
            _fr = 0;
        }
    }
    var _flip = kfo_skin_ow_flip(_s, _f);
    var _rw = sprite_get_width(spr_krisd_dark) * _sc;
    var _rh = sprite_get_height(spr_krisd_dark) * _sc;
    var _sw = sprite_get_width(_spr) * _sc;
    var _sh = sprite_get_height(_spr) * _sc;
    var _left = _x + ((_rw - _sw) / 2);
    var _dx = _flip ? (_left + _sw - (sprite_get_xoffset(_spr) * _sc)) : (_left + (sprite_get_xoffset(_spr) * _sc));
    var _dy = _y + (_rh - _sh) + (sprite_get_yoffset(_spr) * _sc);
    draw_sprite_ext(_spr, _fr mod max(1, sprite_get_number(_spr)), _dx, _dy, _flip ? -_sc : _sc, _sc, 0, _col, _a);
    return _sh;
}

// the small head (HP panel, lists): the game's own heads for 1-5, a crop of the look's first down frame for the rest
function kfo_skin_head_draw(_s, _x, _y)
{
    var _d = kfo_skin_def(_s);
    if (_d.own)
        return knight_head_draw(_d.num, _x, _y);
    var _sp = kfo_skin_spr(variable_struct_exists(_d, "head_spr") ? _d.head_spr : _d.ow[0]);
    if (_sp < 0)
        return knight_head_draw(1, _x, _y);
    var _h = _d.head;
    draw_sprite_part(_sp, 0, _h[0], _h[1], _h[2], _h[3], _x + max(0, (30 - _h[2]) div 2), _y + max(0, 22 - _h[3]));
    return 1;
}

// the portrait (menus): in a frame of the look's colour, whole-number scale, centred in _w x _h; nothing when it has none
function kfo_skin_portrait_draw(_s, _cx, _cy, _w, _h)
{
    var _d = kfo_skin_def(_s);
    if (_d.own || !variable_struct_exists(_d, "portrait"))
        return 0;
    var _sp = kfo_skin_spr(_d.portrait);
    if (_sp < 0)
        return 0;
    var _k = _d.port_sc;
    while (_k > 1 && (sprite_get_width(_sp) * _k > _w - 8 || sprite_get_height(_sp) * _k > _h - 8))
        _k--;
    var _pw = sprite_get_width(_sp) * _k;
    var _ph = sprite_get_height(_sp) * _k;
    var _x0 = round(_cx - (_w / 2));
    var _y0 = round(_cy - (_h / 2));
    draw_set_color(c_black);
    draw_rectangle(_x0, _y0, _x0 + _w, _y0 + _h, false);
    draw_set_color(_d.col);
    draw_rectangle(_x0, _y0, _x0 + _w, _y0 + _h, true);
    draw_rectangle(_x0 + 1, _y0 + 1, _x0 + _w - 1, _y0 + _h - 1, true);
    // the sprite's own origin taken out: its picture centred, on whole pixels
    var _px = round(_cx - (_pw / 2)) + (sprite_get_xoffset(_sp) * _k);
    var _py = round(_cy - (_ph / 2)) + (sprite_get_yoffset(_sp) * _k);
    draw_sprite_ext(_sp, _d.port_img, _px, _py, _k, _k, 0, c_white, 1);
    return 1;
}

// the battle idle, standing where hero _h stands (feet on its feet, its scale), animated; _hurt: a shake and a red flash
function kfo_skin_battle_draw(_s, _h, _hurt)
{
    var _d = kfo_skin_def(_s);
    if (!instance_exists(_h))
        return 0;
    // DRBR 1.0.3: the game's own heroes too (watching someone: their character in your hero's place) - their battle idle
    var _sp = _d.own ? kfo_skin_bt_spr(_s) : kfo_skin_spr(_d.bt);
    if (_sp < 0)
        return 0;
    var _k = abs(_h.image_xscale);
    if (_k <= 0)
        _k = 2;
    var _fx = (!_d.own && _d.bt_flip) ? -1 : 1;
    var _n = max(1, sprite_get_number(_sp));
    var _fr = floor((current_time / (1000 / 30)) * (_d.own ? 0.16 : _d.bt_spd)) mod _n;
    // the hero's feet and middle (its own picture's box), the look's picture's box
    var _hx = (_h.bbox_left + _h.bbox_right) / 2;
    var _hy = _h.bbox_bottom;
    if (_h.bbox_right <= _h.bbox_left)
    {
        _hx = _h.x + (sprite_get_width(_h.sprite_index) * _k / 2);
        _hy = _h.y + (sprite_get_height(_h.sprite_index) * _k);
    }
    var _l = sprite_get_bbox_left(_sp);
    var _r = sprite_get_bbox_right(_sp) + 1;
    var _b = sprite_get_bbox_bottom(_sp) + 1;
    var _ox = sprite_get_xoffset(_sp);
    var _oy = sprite_get_yoffset(_sp);
    var _mid = ((_l + _r) / 2) - _ox;
    var _dx = round(_hx - (_mid * _k * _fx));
    var _dy = round(_hy - ((_b - _oy) * _k));
    if (_hurt > 0)
        _dx += irandom_range(-2, 2);
    draw_sprite_ext(_sp, _fr, _dx, _dy, _k * _fx, _k, 0, c_white, _h.image_alpha <= 0 ? 1 : _h.image_alpha);
    if (_hurt > 0)
    {
        gpu_set_fog(true, c_red, 0, 0);
        draw_sprite_ext(_sp, _fr, _dx, _dy, _k * _fx, _k, 0, c_white, min(0.6, _hurt / 12));
        gpu_set_fog(false, c_black, 0, 0);
    }
    return 1;
}

// DRBR 1.0.3: what stands in your hero's place - watching someone (OUT, or in the room but not in the match): THEIR character
// (their skin: the game's own hero or an online-only look - your request: "whoever you're spectating it needs to show their
// character and stuff"); else your own online-only look; -1: your hero itself
function kbr_hero_look(_M)
{
    if (!variable_global_exists("kfo") || !is_struct(global.kfo))
        return -1;
    var _p = kbr_cb_watched_p(_M);
    if (is_struct(_p))
    {
        var _ws = kfo_skin_ok(kfo_jn(_p, "s", 1));
        return kfo_skin_ready(_ws) ? _ws : 1;
    }
    var _s = kfo_skin_ok(global.kfo.skin);
    return (kfo_skin_cosmetic(_s) && kfo_skin_ready(_s)) ? _s : -1;
}

// every step of an online battle (kbr_step): a look's hero is hidden (its look is drawn in its place by the HUD)
function kbr_skin_hero_tick(_M)
{
    var _s = kbr_hero_look(_M);
    var _hok = variable_global_exists("charinstance") && is_array(global.charinstance) && array_length(global.charinstance) > 0 && instance_exists(global.charinstance[0]);
    if (_s < 0)
    {
        // (no look any more - the one watched gone from the standings for a moment: your hero shows again)
        if (_hok && variable_global_exists("kbr_hero_hid") && global.kbr_hero_hid)
        {
            with (global.charinstance[0])
                image_alpha = 1;
        }
        global.kbr_hero_hid = false;
        return 0;
    }
    if (_hok)
    {
        var _h = global.charinstance[0];
        with (_h)
            image_alpha = 0;
        global.kbr_hero_hid = true;
        // build 52: the look is drawn by its own object at the hero's depth - under the box, the bullets and the HUD, as the
        // game's own heroes are (it used to be drawn with the HUD, over everything)
        if (!instance_exists(obj_knight_skinart))
            instance_create_depth(0, 0, _h.depth, obj_knight_skinart);
        with (obj_knight_skinart)
        {
            if (depth != _h.depth)
                depth = _h.depth;
        }
    }
    return 1;
}

// obj_knight_skinart's Draw: the look in the hero's place (gone with the battle: the object is not persistent, and it
// removes itself when there is no online battle or no hero)
function kbr_skin_art_draw()
{
    var _M = kbr_match();
    if (is_undefined(_M) || !kbr_on() || !variable_global_exists("kfo") || !is_struct(global.kfo))
    {
        instance_destroy();
        return 0;
    }
    var _s = kbr_hero_look(_M);
    if (_s < 0)
        return 0;
    if (!variable_global_exists("charinstance") || !is_array(global.charinstance) || array_length(global.charinstance) == 0)
        return 0;
    var _h = global.charinstance[0];
    if (!instance_exists(_h))
        return 0;
    // the hero hidden by the battle itself (a cut-in, the Roaring's own staging): the look hides too
    if (!_h.visible)
        return 0;
    var _hurt = _M.out ? 0 : _M.hitfx;
    // (the one you watch: their hit's blink - the standings' lower HP, kbr_view_on_state)
    if (kbr_spec_pid(_M) >= 0)
        _hurt = variable_struct_exists(_M, "vw") ? max(0, kbr_rv(_M, kbr_spec_pid(_M)).hit - 18) : 0;
    return kfo_skin_battle_draw(_s, _h, _hurt);
}

// ---------- the HP panel (scr_charbox, det_sent.py's hook): an online-only look's head and CHARACTER NAME ----------
// The game's own heroes (Kris ... Flowery) keep their own head and name art. An online-only look has no name art, so its
// name (BERDLY, AQUA) is written in the battle-name lettering (the sheet ionizachip supplied), narrower letters when it
// is long. Returns 1 when it drew them (the game's own head / name for that box are skipped then).
function kbr_charbox(_c, _face, _hx, _hy, _nx, _ny)
{
    global.kbr_cbx = 0;
    if (!kbr_on() || (_c) != kbr_char() || !variable_global_exists("kfo") || !is_struct(global.kfo))
        return 0;
    // DRBR 1.0.3: watching someone - your box is theirs: their character's head and name (the game's own art for the party,
    // the lettering for the others)
    var _wp = kbr_cb_watched(_c);
    if (is_struct(_wp))
    {
        var _ws = kfo_skin_ok(kfo_jn(_wp, "s", 1));
        var _wd = kfo_skin_def(_ws);
        if (_wd.own && _wd.num <= 4)
        {
            draw_sprite(knight_char_head(_wd.num), 0, _hx, _hy);
            draw_sprite(knight_char_bname(_wd.num), 0, _nx, _ny);
        }
        else
        {
            kfo_skin_head_draw(_ws, _hx - 2, _hy - 2);
            knight_bn_text(_nx - 2, _ny - 2, string_upper(_wd.name), c_white, 58);
        }
        global.kbr_cbx = 1;
        return 1;
    }
    var _s = kfo_skin_ok(global.kfo.skin);
    if (!kfo_skin_cosmetic(_s) || !kfo_skin_ready(_s))
        return 0;
    kfo_skin_head_draw(_s, _hx - 2, _hy - 2);
    knight_bn_text(_nx - 2, _ny - 2, string_upper(kfo_skin_def(_s).name), c_white, 58);
    global.kbr_cbx = 1;
    return 1;
}

// the HP bar's colour for the panel (a look's own colour; the rest keep theirs)
function kbr_charbox_col(_c, _col)
{
    if (!kbr_on() || _c != kbr_char() || !variable_global_exists("kfo") || !is_struct(global.kfo))
        return _col;
    // DRBR 1.0.3: watching someone - their character's colour (the party's own HP colours, a look's own)
    var _wp = kbr_cb_watched(_c);
    if (is_struct(_wp))
    {
        var _wd = kfo_skin_def(kfo_skin_ok(kfo_jn(_wp, "s", 1)));
        if (_wd.own && _wd.num <= 4 && variable_instance_exists(id, "hpcolor"))
            return hpcolor[_wd.num - 1];
        if (_wd.own && _wd.num >= 5)
            return knight_cc_hpcolor(_wd.num);
        return _wd.col;
    }
    var _s = kfo_skin_ok(global.kfo.skin);
    return kfo_skin_cosmetic(_s) ? kfo_skin_col(_s) : _col;
}

// ---------- the battle-name lettering (spr_khub_bnfont: the sheet ionizachip supplied, 66 glyphs in 3 widths, 14 x 19 cells) ----------
function knight_bn_order()
{
    return "ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890()[]-+!" + chr(1) + ".," + chr(2) + "?<>:;'\"=#_*$" + chr(3) + "~/\\|@" + chr(4);
}

// build 52: three widths of every letter - the sheet's own (0), and narrower ones made the way its example shows (1: two
// middle columns out, 2: four), so a long name gets narrower letters instead of stretched ones
function knight_bn_widths(_lv)
{
    switch (_lv)
    {
        case 1: return [6,  6,  5,  5,  5,  5,  7,  6,  6,  7,  9,  4,  11,  7,  6,  5,  9,  7,  6,  6,  6,  7,  11,  11,  9,  11,  5,  9,  6,  9,  7,  7,  10,  6,  7,  7,  3,  3,  3,  3,  6,  6,  2,  2,  2,  3,  7,  7,  5,  5,  2,  3,  1,  3,  6,  8,  6,  6,  7,  6,  7,  7,  7,  2,  9,  9];
        case 2: return [5,  5,  3,  4,  3,  3,  6,  4,  4,  7,  9,  3,  11,  7,  5,  5,  9,  5,  5,  4,  5,  7,  11,  11,  9,  11,  5,  9,  5,  9,  5,  5,  10,  5,  5,  7,  3,  3,  3,  3,  4,  4,  2,  2,  2,  3,  7,  7,  5,  5,  2,  3,  1,  3,  4,  6,  4,  5,  7,  4,  7,  7,  7,  2,  9,  9];
    }
    return [8,  8,  7,  7,  7,  7,  9,  8,  8,  8,  10,  6,  13,  9,  8,  7,  10,  9,  8,  8,  8,  8,  13,  12,  10,  11,  6,  9,  8,  10,  9,  9,  11,  8,  9,  7,  3,  3,  3,  3,  8,  8,  2,  2,  2,  3,  7,  7,  5,  5,  2,  3,  1,  3,  8,  10,  8,  8,  8,  8,  7,  7,  7,  2,  9,  10];
}

// the width of _t in the lettering at width _lv (1 pixel between letters, 4 for a space)
function knight_bn_width(_t, _lv)
{
    if (is_undefined(_lv))
        _lv = 0;
    var _o = knight_bn_order();
    var _w = knight_bn_widths(_lv);
    var _n = 0;
    _t = string_upper(_t);
    for (var _i = 1; _i <= string_length(_t); _i++)
    {
        var _ch = string_char_at(_t, _i);
        var _p = string_pos(_ch, _o);
        _n += ((_p > 0) ? _w[_p - 1] : 4) + 1;
    }
    return max(0, _n - 1);
}

// _t at _x, _y in the lettering, coloured _col; wider than _maxw: narrower letters (never stretched), and past the narrowest
// the end is cut
function knight_bn_text(_x, _y, _t, _col, _maxw)
{
    var _spr = asset_get_index("spr_khub_bnfont");
    _t = string_upper(_t);
    if (_spr < 0 || !sprite_exists(_spr))
    {
        draw_set_font(fnt_small);
        draw_set_color(_col);
        draw_text(_x, _y + 4, _t);
        return 0;
    }
    var _lv = 0;
    while (_lv < 2 && _maxw > 0 && knight_bn_width(_t, _lv) > _maxw)
        _lv++;
    while (_maxw > 0 && string_length(_t) > 1 && knight_bn_width(_t, _lv) > _maxw)
        _t = string_copy(_t, 1, string_length(_t) - 1);
    var _o = knight_bn_order();
    var _w = knight_bn_widths(_lv);
    var _base = _lv * string_length(_o);
    var _cx = _x;
    for (var _i = 1; _i <= string_length(_t); _i++)
    {
        var _ch = string_char_at(_t, _i);
        var _p = string_pos(_ch, _o);
        if (_p <= 0)
        {
            _cx += 5;
            continue;
        }
        draw_sprite_ext(_spr, _base + _p - 1, _cx, _y, 1, 1, 0, _col, draw_get_alpha());
        _cx += _w[_p - 1] + 1;
    }
    return 1;
}


// ---------- DRBR 1.0.3: the HP panel while you watch (scr_charbox reads HP through these: det_sent.py watch_hooks) ----------
// the standings entry of the one you watch (undefined when you are not watching)
function kbr_cb_watched_p(_M)
{
    if (is_undefined(_M) || !kbr_on())
        return undefined;
    var _w = kbr_spec_pid(_M);
    if (_w < 0)
        return undefined;
    return kbr_st_player(_M, _w);
}

// ... when HP box _c is yours (the box the one you watch takes)
function kbr_cb_watched(_c)
{
    if (!kbr_on() || _c != kbr_char())
        return undefined;
    return kbr_cb_watched_p(kbr_match());
}

// HP box _c's HP and max HP: the one you watch's in your box, else the game's own
function kbr_cb_hp(_c)
{
    var _p = kbr_cb_watched(_c);
    return is_struct(_p) ? max(0, round(kfo_jn(_p, "hp", 0))) : global.hp[_c];
}

function kbr_cb_mhp(_c)
{
    var _p = kbr_cb_watched(_c);
    return is_struct(_p) ? max(1, round(kfo_jn(_p, "mh", 1))) : global.maxhp[_c];
}
