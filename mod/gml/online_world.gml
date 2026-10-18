
// ===== Build 45: the cold place is the room's lobby =====
// While you are in a room (online or practice) the cold place is where the room meets: every other player walks around it
// as their SKIN, with their name over their head (positions 10 times a second through the host). The sign is the room's
// menu: READY / START, the settings, LEAVE. Closing the menu keeps you in the room; walking around is waiting for the match.

function kfo_world_skin_spr(_s, _f)
{
    // build 52: an online-only look's own walking frames (Kris's when its art is missing)
    if (is_numeric(_s) && _s >= 6)
    {
        var _ow = kfo_skin_ow(_s, _f);
        if (_ow >= 0)
            return _ow;
        _s = 1;
    }
    // build 50: a custom character's own walking frames (Flowery's)
    if (knight_cc_ok(_s) && knight_cc_spr(knight_cc_walk_spr(_s, _f)))
        return knight_cc_walk_spr(_s, _f);
    switch (clamp(_s, 1, 4))
    {
        case 2:
            switch (_f)
            {
                case 1: return spr_susie_walk_right_dw;
                case 2: return spr_susie_walk_up_dw;
                case 3: return spr_susie_walk_left_dw;
            }
            return spr_susie_walk_down_dw;
        case 3:
            switch (_f)
            {
                case 1: return spr_ralsei_walk_right;
                case 2: return spr_ralsei_walk_up;
                case 3: return spr_ralsei_walk_left;
            }
            return spr_ralsei_walk_down;
        case 4:
            switch (_f)
            {
                case 1: return spr_noelle_walk_right_dw;
                case 2: return spr_noelle_walk_up_dw;
                case 3: return spr_noelle_walk_left_dw;
            }
            return spr_noelle_walk_down_dw;
    }
    switch (_f)
    {
        case 1: return spr_krisr_dark;
        case 2: return spr_krisu_dark;
        case 3: return spr_krisl_dark;
    }
    return spr_krisd_dark;
}

// build 47: the online room's overworld rules are on - you are in a room (online or practice), outside a fight, walking around
// (any overworld room: the party stays asleep and you keep your SKIN if you walk out of the cold place and back)
function kfo_ow_online()
{
    if (!variable_global_exists("kfo") || !is_struct(global.kfo))
        return false;
    return kfo_in_room() && !knight_active() && instance_exists(obj_mainchara);
}

// build 47: a SKIN number from another game, checked against the skins this build has (1 Kris, 2 Susie, 3 Ralsei, 4 Noelle);
// anything else (another build's skin, a broken message) is shown as Kris - their own choice on their computer is not changed
function kfo_skin_ok(_v)
{
    // build 52: every skin in the registry (online_skin52.gml)
    if (is_numeric(_v) && _v == floor(_v) && _v >= 1 && _v <= kfo_skin_count())
        return _v;
    return 1;
}

// the room is in the cold place right now (not a fight, not the arena)
function kfo_world_here()
{
    return kfo_ow_online() && room == room_dw_snow_zone;
}

// ---------- build 47: the cold place as a multiplayer room ----------
// While you are in a room there: no party following you (Susie / Ralsei's followers are put to sleep - deactivated, not
// destroyed - and woken again when you leave the room or a fight starts), you look like your SKIN (drawn in Kris's place:
// Kris's collision box and speed stay), and the way to the original Knight encounter is closed: a wall (the game's own
// collision block) and the encounter's start refusing (kfo_ow_encounter_ok in its trigger, every knight's version).
// Offline none of it exists.

// the original encounter may start (false only while you are in an online / practice room outside a fight)
function kfo_ow_encounter_ok()
{
    if (!variable_global_exists("kfo") || !is_struct(global.kfo))
        return true;
    return !(kfo_in_room() && !knight_active());
}

// the wall in front of the encounter (x 1800 onward, the room's whole height) and the followers asleep; undone off-line
global.kfo_wall = noone;
global.kfo_wall_msg = 0;
global.kfo_wall_armed = true;
global.kfo_party_asleep = false;
global.kfo_party_wake = false;

// the hub controller's Step (every frame, online or not: leaving a room always wakes the party)
// the party to sleep at once (deactivated - never destroyed): in a room's first step (kfo_world_room_tick) and right after
// the network's messages (ctrl's Async event): a join that completes there would otherwise show the party for one frame
// (found by the overworld soak: 2 followers seen in 1 of 1,432 checks, the frame a game came back into the room)
// build 50: online at all (connecting, a lobby, a room, a match, practice) and walking around outside a fight: your party does
// not follow you - you are only you (your SKIN). Back as soon as you are off-line.
function kfo_ow_party_off()
{
    if (!variable_global_exists("kfo") || !is_struct(global.kfo) || !instance_exists(obj_mainchara) || instance_exists(obj_battlecontroller))
        return false;
    var _o = global.kfo;
    return kfo_in_room() || _o.prac || (variable_struct_exists(_o, "mode") && _o.mode != "off") || (_o.st != "idle" && _o.st != "failed" && _o.st != "");
}

function kfo_world_sleep_now()
{
    if (!kfo_ow_party_off())
        return false;
    if (instance_exists(obj_caterpillarchara))
    {
        instance_deactivate_object(obj_caterpillarchara);
        global.kfo_party_asleep = true;
    }
    global.kfo_party_wake = false;
    return true;
}

function kfo_world_room_tick()
{
    var _on = kfo_ow_online();
    var _here = _on && room == room_dw_snow_zone;
    // the party: asleep in any overworld room while you are in a room (deactivated - never destroyed, their data and the
    // game's follower scripts untouched); a new room's followers (the dark world controller makes them at the room's start)
    // go to sleep in the room's first step, before anything is drawn. (Chapter 3's followers are not persistent and no
    // Chapter 3 room is: each room makes its own, so the ones asleep in a room you leave go with that room, as the
    // game's own would.)
    if (kfo_ow_party_off())
        kfo_world_sleep_now();
    else if (global.kfo_party_asleep)
    {
        instance_activate_object(obj_caterpillarchara);
        global.kfo_party_asleep = false;
        // back beside Kris in this frame's End Step (kfo_world_end_step), once they are active again
        global.kfo_party_wake = true;
    }
    if (_here)
    {
        if (!instance_exists(global.kfo_wall))
        {
            global.kfo_wall = instance_create_depth(1800, -200, 0, obj_solidblock);
            with (global.kfo_wall)
            {
                kfo_wall = true;
                visible = false;
                var _w = max(1, sprite_get_width(sprite_index));
                var _h = max(1, sprite_get_height(sprite_index));
                image_xscale = 40 / _w;
                image_yscale = (room_height + 400) / _h;
            }
        }
        // nobody stays inside the wall or past it (there when the wall came, or put there): back to this side of it, on a
        // free spot of the room's own floor nearest to where they were
        var _mc = instance_find(obj_mainchara, 0);
        var _wall = global.kfo_wall;
        with (_mc)
        {
            if (x >= 1800 || place_meeting(x, y, _wall))
            {
                x = 1760;
                if (place_meeting(x, y, obj_solidblock))
                {
                    for (var _d = 2; _d < 480; _d += 2)
                    {
                        if (!place_meeting(x, y + _d, obj_solidblock))
                        {
                            y += _d;
                            break;
                        }
                        if (!place_meeting(x, y - _d, obj_solidblock))
                        {
                            y -= _d;
                            break;
                        }
                    }
                }
            }
        }
        // the notice: once when you come close, again only after you walked away
        if (_mc.x >= 1690 && global.kfo_wall_armed)
        {
            global.kfo_wall_msg = 150;
            global.kfo_wall_armed = false;
        }
        else if (_mc.x < 1600)
            global.kfo_wall_armed = true;
        if (global.kfo_wall_msg > 0)
            global.kfo_wall_msg--;
    }
    else
    {
        if (instance_exists(global.kfo_wall))
            instance_destroy(global.kfo_wall);
        global.kfo_wall = noone;
        global.kfo_wall_msg = 0;
    }
    return 1;
}

// the hub controller's End Step: the party just woken (you left the room / a fight began) stands behind Kris again, as the
// game puts them when a room starts, and follows from there (the game's own scr_caterpillar_interpolate)
function kfo_world_end_step()
{
    if (!global.kfo_party_wake)
        return 0;
    global.kfo_party_wake = false;
    if (!instance_exists(obj_mainchara))
        return 0;
    var _mc = instance_find(obj_mainchara, 0);
    with (obj_caterpillarchara)
    {
        x = _mc.x - 4;
        y = _mc.y - ((global.darkzone == 1) ? 16 : 6);
        scr_caterpillar_interpolate();
    }
    return 1;
}

// obj_mainchara's Draw asks this first (base override in gen_hub.py): in the room, your SKIN in Kris's place - the same
// facing and walk frame, feet where Kris's feet are; Kris (skin 1), a special pose or offline: the game draws Kris
function kfo_world_self_draw()
{
    // build 50: the SKIN you picked stays yours after you leave the menu - online or not, wherever you walk in the Dark World
    // (it used to apply only while kfo_ow_online(), so closing the menu turned you back into Kris); with the plain Kris skin,
    // Flowery leading the hub's party walks around as himself
    var _skin = 1;
    if (variable_global_exists("kfo") && is_struct(global.kfo) && (kfo_ow_online() || (variable_global_exists("darkzone") && global.darkzone == 1)))
        _skin = kfo_skin_ok(global.kfo.skin);
    // build 52: the online-only looks only while you are in an online / practice room (never in the hub's own game)
    if (kfo_skin_cosmetic(_skin) && !kfo_ow_online())
        _skin = 1;
    if (_skin == 1 && knight_cc_ok(knight_cc_lead_ow()))
        _skin = knight_cc_lead_ow();
    if (_skin == 1)
        return false;
    if (!(sprite_index == dsprite || sprite_index == rsprite || sprite_index == usprite || sprite_index == lsprite))
        return false;
    var _f = variable_global_exists("facing") ? clamp(global.facing, 0, 3) : 0;
    var _spr = kfo_world_skin_spr(_skin, _f);
    // DRBR: a look with a standing sprite of its own uses it while you stand (Spamton: his hop is his walk); one whose art faces
    // one way only is mirrored for the other (kfo_skin_ow_flip)
    var _walk = variable_instance_exists(id, "walkbuffer") && walkbuffer > 3;
    var _idl = _walk ? -1 : kfo_skin_ow_idle(_skin, _f);
    if (_idl >= 0)
        _spr = _idl;
    var _flip = kfo_skin_ow_flip(_skin, _f);
    var _sc = image_xscale;
    var _rw = sprite_get_width(sprite_index) * _sc;
    var _rh = sprite_get_height(sprite_index) * _sc;
    var _sw = sprite_get_width(_spr) * _sc;
    var _sh = sprite_get_height(_spr) * _sc;
    var _left = (x - (sprite_get_xoffset(sprite_index) * _sc)) + ((_rw - _sw) / 2);
    var _dx = _flip ? ((_left + _sw) - (sprite_get_xoffset(_spr) * _sc)) : (_left + (sprite_get_xoffset(_spr) * _sc));
    var _dy = (y - (sprite_get_yoffset(sprite_index) * _sc)) + (_rh - _sh) + (sprite_get_yoffset(_spr) * _sc);
    var _fr = (_idl >= 0) ? 0 : (floor(image_index) mod max(1, sprite_get_number(_spr)));
    draw_sprite_ext(_spr, _fr, _dx, _dy, _flip ? -_sc : _sc, image_yscale, 0, image_blend, image_alpha);
    return true;
}

// every step: where I am, to the host (when I moved, or once a second)
function kfo_world_tick()
{
    var _o = global.kfo;
    // the ones who left the room (or went silent for 5 seconds): their entry goes, no ghost is ever drawn for them
    if (current_time - _o.t_owprune >= 1000)
    {
        _o.t_owprune = current_time;
        var _keys = variable_struct_get_names(_o.ows);
        for (var _i = 0; _i < array_length(_keys); _i++)
        {
            var _p = variable_struct_get(_o.ows, _keys[_i]);
            if (current_time - _p.t > 5000 || is_undefined(kfo_world_member(real(_keys[_i]))))
                variable_struct_remove(_o.ows, _keys[_i]);
        }
    }
    if (!kfo_ow_online())
        return 0;
    var _mc = instance_find(obj_mainchara, 0);
    var _f = variable_global_exists("facing") ? clamp(global.facing, 0, 3) : 0;
    // walking: the game's own walk (its step keeps the walk frames turning while walkbuffer > 3) or moved since the last
    // frame (this runs before Kris's own step: x / xprevious would always be the same here). The walk frame itself goes too,
    // so the others see your steps with your timing
    var _wb = variable_instance_exists(_mc, "walkbuffer") ? _mc.walkbuffer : 0;
    var _mv = (_wb > 3 || _mc.x != _o.ow_px || _mc.y != _o.ow_py) ? 1 : 0;
    _o.ow_px = _mc.x;
    _o.ow_py = _mc.y;
    var _a = floor(_mc.image_index) mod 4;
    var _now = current_time;
    var _last = _o.ow_last;
    var _changed = !is_array(_last) || array_length(_last) < 5 || _last[0] != round(_mc.x) || _last[1] != round(_mc.y) || _last[2] != _f || _last[3] != _mv || _last[4] != _a;
    if ((_changed && _now - _o.t_ow >= 100) || _now - _o.t_ow >= 1000)
    {
        _o.t_ow = _now;
        _o.ow_last = [round(_mc.x), round(_mc.y), _f, _mv, _a];
        kfo_up_fast({ k: "ow", x: round(_mc.x), y: round(_mc.y), f: _f, m: _mv, r: room, a: _a });
    }
    return 1;
}

// the host's list: [[pid, x, y, facing, moving, skin, room, ready], ...]
function kfo_world_on(_m)
{
    var _o = global.kfo;
    var _l = kfo_ja(_m, "l");
    for (var _i = 0; _i < array_length(_l); _i++)
    {
        var _e = _l[_i];
        if (!is_array(_e) || array_length(_e) < 8)
            continue;
        if (!is_numeric(_e[0]) || !is_numeric(_e[1]) || !is_numeric(_e[2]))
            continue;
        var _k = string(_e[0]);
        var _p = variable_struct_exists(_o.ows, _k) ? variable_struct_get(_o.ows, _k) : undefined;
        if (is_undefined(_p))
        {
            _p = { x: _e[1], y: _e[2], px: _e[1], py: _e[2], t: current_time, pt: current_time, f: 0, m: 0, s: 1, r: -1, rd: 0, anim: 0, born: current_time, a: -1 };
            variable_struct_set(_o.ows, _k, _p);
        }
        _p.px = kbr_ps_rx(_p);
        _p.py = kbr_ps_ry(_p);
        // back after a while (another room, a match) or a jump of more than a few steps: shown there at once, faded in again
        if (current_time - _p.t > 1000 || (is_numeric(_e[6]) && _e[6] != _p.r) || abs(_e[1] - _p.x) > 64 || abs(_e[2] - _p.y) > 64)
        {
            _p.px = _e[1];
            _p.py = _e[2];
            if (current_time - _p.t > 1000 || (is_numeric(_e[6]) && _e[6] != _p.r))
                _p.born = current_time;
        }
        _p.pt = current_time;
        _p.t = current_time + 100;
        _p.x = _e[1];
        _p.y = _e[2];
        _p.f = is_numeric(_e[3]) ? clamp(_e[3], 0, 3) : 0;
        _p.m = is_numeric(_e[4]) ? _e[4] : 0;
        // a skin this build does not have (another build, a broken message): drawn as Kris; their own choice is not changed
        _p.s = kfo_skin_ok(_e[5]);
        _p.r = is_numeric(_e[6]) ? _e[6] : -1;
        _p.rd = is_numeric(_e[7]) ? _e[7] : 0;
        // build 47: their walk frame (-1: an older host's list without it - the frames then turn on this game's clock)
        _p.a = (array_length(_e) >= 9 && is_numeric(_e[8])) ? clamp(floor(_e[8]), -1, 31) : -1;
    }
    return 1;
}

// the room's member _pid as the lobby lists them (name, host?, ready?)
function kfo_world_member(_pid)
{
    var _pl = kfo_lobby_players();
    for (var _i = 0; _i < array_length(_pl); _i++)
    {
        if (kfo_jn(_pl[_i], "pid", -2) == _pid)
            return _pl[_i];
    }
    return undefined;
}

// the hub controller's Draw: the other players in the cold place, then the room's box in the corner
function kfo_world_draw()
{
    if (!kfo_ow_online())
        return 0;
    var _o = global.kfo;
    var _ref = spr_krisd_dark;
    var _rw = sprite_get_width(_ref) * 2;
    var _rh = sprite_get_height(_ref) * 2;
    var _keys = variable_struct_get_names(_o.ows);
    draw_set_font(fnt_small);
    for (var _i = 0; _i < array_length(_keys); _i++)
    {
        var _pid = real(_keys[_i]);
        if (_pid == _o.my)
            continue;
        var _p = variable_struct_get(_o.ows, _keys[_i]);
        if (current_time - _p.t > 3000 || (_p.r >= 0 && _p.r != room))
            continue;
        var _mem = kfo_world_member(_pid);
        // (DRBR 1.0.3: the room's bots too - the host sends them walking behind it, in their skins)
        if (is_undefined(_mem))
            continue;
        var _x = kbr_ps_rx(_p);
        var _y = kbr_ps_ry(_p);
        var _spr = kfo_world_skin_spr(_p.s, _p.f);
        var _fn = max(1, sprite_get_number(_spr));
        var _fr = (_p.a >= 0) ? (_p.a mod _fn) : (_p.m ? ((current_time div 160) mod _fn) : 0);
        // a player who just came in fades in (a third of a second) instead of popping up
        var _fa = clamp((current_time - _p.born) / 300, 0, 1);
        // feet where Kris's feet are (DRBR: kfo_skin_ow_draw - mirrored / standing sprites for the looks that need them)
        var _sh = kfo_skin_ow_draw(_p.s, _p.f, _p.m, _fr, _x, _y, 2, c_white, 0.92 * _fa);
        var _nm = kfo_js(_mem, "n", "?");
        var _tag = (kfo_jn(_mem, "rd", 0) == 1) ? " (READY)" : "";
        var _hid = is_struct(_o.lobby) ? kfo_jn(_o.lobby, "host", -1) : -1;
        if (_pid == _hid)
            _tag = " (HOST)";
        if (kfo_jn(_mem, "bot", 0) == 1)
            _tag = " (BOT)";
        // their name (MATCH VIEW > ROOM NAMES; NAME OPACITY), over the head of whatever skin they wear
        if (kfo_view().wnames)
        {
            draw_set_alpha(max(0.2, kfo_view().nop / 100) * _fa);
            draw_set_halign(fa_center);
            draw_set_color(c_black);
            draw_text(_x + (_rw / 2) + 1, _y + (_rh - _sh) - 15, _nm + _tag);
            draw_set_color((_tag == " (READY)") ? c_lime : ((_tag == " (HOST)") ? c_yellow : c_white));
            draw_text(_x + (_rw / 2), _y + (_rh - _sh) - 16, _nm + _tag);
            draw_set_halign(fa_left);
            draw_set_alpha(1);
        }
        // build 52: what they just said, in a bubble over their head (over their name)
        kfo_bubble_draw(_pid, _x + (_rw / 2), _y + (_rh - _sh) - (kfo_view().wnames ? 18 : 4));
    }
    // build 52: your own bubble
    var _mb = instance_find(obj_mainchara, 0);
    if (instance_exists(_mb))
    {
        var _bs = kfo_world_skin_spr(_o.skin, variable_global_exists("facing") ? clamp(global.facing, 0, 3) : 0);
        kfo_bubble_draw(_o.my, _mb.x + ((sprite_get_width(spr_krisd_dark) * 2) / 2), _mb.y + (sprite_get_height(spr_krisd_dark) * 2) - (sprite_get_height(_bs) * 2) - 12);
    }
    // you: a small marker over your head (HIGHLIGHT MY SOUL), so you are told apart from a player in the same skin
    var _me = instance_find(obj_mainchara, 0);
    if (kfo_view().hl && instance_exists(_me))
    {
        var _ms = kfo_world_skin_spr(_o.skin, variable_global_exists("facing") ? clamp(global.facing, 0, 3) : 0);
        var _mx = _me.x + ((sprite_get_width(spr_krisd_dark) * 2) / 2);
        var _my = _me.y + (sprite_get_height(spr_krisd_dark) * 2) - (sprite_get_height(_ms) * 2) - 8;
        draw_set_color(kfo_col_text(_o.look.col));
        draw_triangle(_mx - 4, _my - 6, _mx + 4, _my - 6, _mx, _my, false);
    }
    // the closed way to the original encounter (the cold place only): a faint snowy wall, and its notice once when you come near
    if (room == room_dw_snow_zone)
    {
        var _wx = 1800;
        draw_set_alpha(0.18 + (0.06 * sin(current_time / 400)));
        draw_set_color(make_color_rgb(170, 200, 255));
        draw_rectangle(_wx, knight_cam_y(), _wx + 40, knight_cam_y() + 480, false);
        draw_set_alpha(1);
        if (global.kfo_wall_msg > 0)
            kfo_world_notice(knight_cam_x(), knight_cam_y(), "The way forward is blocked during online play.");
    }
    // the room box (not while the hub menu is open: it shows the room itself)
    if (!instance_exists(obj_knight_menu))
        kfo_world_box(knight_cam_x(), knight_cam_y());
    draw_set_color(c_white);
    return 1;
}

function kfo_world_box(xx, yy)
{
    var _o = global.kfo;
    var _pl = kfo_lobby_players();
    var _rd = 0;
    for (var _i = 0; _i < array_length(_pl); _i++)
    {
        if (kfo_jn(_pl[_i], "rd", 0) == 1 || kfo_jn(_pl[_i], "bot", 0) == 1)
            _rd++;
    }
    var _l1 = (_o.code == "PRACTICE") ? "PRACTICE ROOM" : (((_o.mode == "steam") ? "STEAM ROOM " : "ROOM ") + _o.code);
    var _l2 = string(array_length(_pl)) + ((array_length(_pl) == 1) ? " PLAYER" : " PLAYERS") + "  " + string(_rd) + " READY";
    var _l3 = kfo_lobby_matching() ? "A MATCH IS ON - WATCH IT AT THE SIGN" : (kfo_is_host() ? "THE SIGN: START THE MATCH" : "THE SIGN: GET READY");
    var _w = 236;
    draw_set_alpha(0.75);
    draw_set_color(c_black);
    draw_rectangle(xx + 6, yy + 6, xx + 6 + _w, yy + 62, false);
    draw_set_alpha(1);
    draw_set_color(c_white);
    draw_rectangle(xx + 6, yy + 6, xx + 6 + _w, yy + 62, true);
    draw_set_color(c_yellow);
    knight_txt_tiny(xx + 12, yy + 10, _l1);
    draw_set_color(c_white);
    knight_txt_tiny(xx + 12, yy + 26, _l2);
    draw_set_color(c_ltgray);
    knight_txt_tiny(xx + 12, yy + 42, _l3);
    kfo_net_light(xx + _w - 8, yy + 14);
    return 1;
}

// the network light: green under 100 ms, yellow under 200, red above; grey when not known (practice: always green)
function kfo_net_light(_x, _y)
{
    var _o = global.kfo;
    var _rtt = _o.rtt;
    if (is_struct(_o.M) && variable_struct_exists(_o.M, "ck") && kbr_rtt_shown(_o.M) >= 0)
        _rtt = kbr_rtt_shown(_o.M);
    var _col = c_gray;
    if (_o.mode == "local" || kfo_is_host())
        _col = c_lime;
    else if (_rtt >= 0)
        _col = (_rtt < 100) ? c_lime : ((_rtt < 200) ? c_yellow : c_red);
    draw_set_color(c_black);
    draw_circle(_x, _y, 5, false);
    draw_set_color(_col);
    draw_circle(_x, _y, 4, false);
    draw_set_color(c_white);
    return _col;
}

// a short notice in a box at the bottom of the screen (the game's look: black, white edge)
function kfo_world_notice(xx, yy, _t)
{
    draw_set_font(fnt_main);
    var _w = min(600, string_width(_t) + 40);
    var _x0 = xx + 320 - (_w / 2);
    var _y0 = yy + 380;
    draw_set_alpha(min(1, global.kfo_wall_msg / 20));
    draw_set_color(c_black);
    draw_rectangle(_x0, _y0, _x0 + _w, _y0 + 44, false);
    draw_set_color(c_white);
    draw_rectangle(_x0, _y0, _x0 + _w, _y0 + 44, true);
    draw_rectangle(_x0 + 1, _y0 + 1, _x0 + _w - 1, _y0 + 43, true);
    draw_set_halign(fa_center);
    draw_text(xx + 320, _y0 + 12, _t);
    draw_set_halign(fa_left);
    draw_set_alpha(1);
    return 1;
}


// build 52: a chat bubble over a player in the room (the cold place): their last message for 6 seconds (fading out in the
// last half second), Deltarune's box (black, a white edge, a little tail), the game's main font, wrapped at 180 pixels,
// 3 lines at most, kept inside the screen. Muted players' messages are not shown. One bubble per player: a new message
// replaces the old one.
function kfo_bubble_draw(_pid, _cx, _by)
{
    if (!variable_struct_exists(global.kfo, "chat") || !is_struct(global.kfo.chat))
        return 0;
    var _c = global.kfo.chat;
    var _e = undefined;
    for (var _i = array_length(_c.l) - 1; _i >= 0; _i--)
    {
        var _l = _c.l[_i];
        if (current_time - _l.tm > 6000)
            break;
        if (_l.pid == _pid && _l.sys == 0)
        {
            _e = _l;
            break;
        }
    }
    if (is_undefined(_e) || kfo_chat_muted(_e.n))
        return 0;
    var _age = current_time - _e.tm;
    var _a = clamp((6000 - _age) / 500, 0, 1) * clamp(_age / 120, 0, 1);
    var _lines = knight_wrap_font(_e.t, 180, "main");
    if (array_length(_lines) > 3)
    {
        array_resize(_lines, 3);
        _lines[2] = string_copy(_lines[2], 1, max(1, string_length(_lines[2]) - 2)) + "..";
    }
    scr_84_set_draw_font("main");
    var _w = 0;
    for (var _i = 0; _i < array_length(_lines); _i++)
        _w = max(_w, string_width(_lines[_i]));
    var _lh = 16;
    var _h = (array_length(_lines) * _lh) + 8;
    var _bw = _w + 12;
    var _vx = knight_cam_x();
    var _vy = knight_cam_y();
    var _x0 = clamp(round(_cx - (_bw / 2)), _vx + 4, _vx + 636 - _bw);
    var _y1 = round(_by - 6);
    var _y0 = _y1 - _h;
    if (_y0 < _vy + 4)
    {
        _y0 = _vy + 4;
        _y1 = _y0 + _h;
    }
    draw_set_alpha(0.9 * _a);
    draw_set_color(c_black);
    draw_rectangle(_x0, _y0, _x0 + _bw, _y1, false);
    var _tx = clamp(round(_cx), _x0 + 6, _x0 + _bw - 6);
    draw_triangle(_tx - 4, _y1, _tx + 4, _y1, _tx, _y1 + 5, false);
    draw_set_alpha(_a);
    draw_set_color(c_white);
    draw_rectangle(_x0, _y0, _x0 + _bw, _y1, true);
    draw_rectangle(_x0 + 1, _y0 + 1, _x0 + _bw - 1, _y1 - 1, true);
    draw_line(_tx - 4, _y1, _tx, _y1 + 5);
    draw_line(_tx + 4, _y1, _tx, _y1 + 5);
    for (var _i = 0; _i < array_length(_lines); _i++)
        draw_text(_x0 + 6, _y0 + 3 + (_i * _lh), _lines[_i]);
    draw_set_alpha(1);
    draw_set_font(fnt_small);
    return 1;
}
