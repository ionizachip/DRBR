// ===== Build 49: SMART BOTS =====
// Bots are SOULs the host's game plays (PRACTICE and online rooms). They live by the players' rules: the same box, the same
// SOUL speed (and half speed for the slow walk), the same hitbox (the host's own SOUL's), the same damage table, the same
// gauge, skills, heals, cooldowns and TARGETING modes. Their positions go out exactly like a player's (camera-relative, in
// the host's "ps"), so every game draws them with the very code that draws the players' SOULs.
// Dodging works from what is in the box, never from a list of attacks: every frame the host records every bullet's place
// and how it moved (kfo_bot_track), each bot that is due to think scores 17 moves (stay, 8 ways at full speed, 8 at half)
// by where its SOUL would be on the next frames against where each bullet will be (its bounding box moved by its own speed,
// then the engine's precise collision for the frames where the boxes meet), the box's edges and corners, and picks the
// best. New knight mods work without changes.
// DIFFICULTY: kfo_bot_presets() below - one place for every number. Each bot has its own settings (the room's BOT SKILL for
// the ones the host did not change; MORE > BOTS on the room page for one bot).

// ---------- the numbers (edit here) ----------
// [name, reaction (frames before a new bullet is noticed), prediction (frames looked ahead), mistakes (%), precision (0-100:
// 100 = exact moves), healing smarts (0-100), charging smarts (0-100), aggression (0-100), thinks every N frames]
function kfo_bot_presets()
{
    return [
        ["DUMMY", 45, 0, 60, 10, 0, 0, 0, 20],
        ["EASY", 16, 6, 22, 55, 30, 20, 20, 4],
        ["NORMAL", 9, 12, 9, 80, 60, 50, 45, 2],
        ["HARD", 4, 18, 3, 92, 80, 75, 65, 1],
        ["EXPERT", 1, 28, 1, 98, 95, 90, 80, 1],
        ["PERFECT", 0, 40, 0, 100, 100, 100, 90, 1]
    ];
}

function kfo_bot_pre_count()
{
    return 6;
}

function kfo_bot_pre_name(_i)
{
    if (_i < 0)
        return "CUSTOM";
    var _p = kfo_bot_presets();
    return _p[clamp(_i, 0, array_length(_p) - 1)][0];
}

// a bot's settings from preset _i (own: changed by the host for this bot)
function kfo_bot_cfg(_i)
{
    var _p = kfo_bot_presets();
    var _e = _p[clamp(_i, 0, array_length(_p) - 1)];
    return { pre: clamp(_i, 0, array_length(_p) - 1), react: _e[1], pred: _e[2], miss: _e[3], prec: _e[4], heal: _e[5], chg: _e[6], aggr: _e[7],
        every: _e[8], own: false };
}

// the sliders: [id, label, lo, hi, step]
function kfo_bot_sliders()
{
    return [["react", "REACTION TIME", 0, 60, 1], ["pred", "PREDICTION", 0, 40, 2], ["miss", "MISTAKES", 0, 100, 5], ["prec", "PRECISION", 0, 100, 5],
        ["heal", "HEALING", 0, 100, 5], ["chg", "CHARGING", 0, 100, 5], ["aggr", "AGGRESSION", 0, 100, 5]];
}

function kfo_bot_cfg_clean(_c, _def)
{
    if (!is_struct(_c))
        return kfo_bot_cfg(_def);
    var _o = kfo_bot_cfg(is_numeric(kfo_jv(_c, "pre")) ? clamp(kfo_jn(_c, "pre", _def), -1, 5) : _def);
    _o.pre = clamp(floor(kfo_jn(_c, "pre", _def)), -1, 5);
    var _sl = kfo_bot_sliders();
    for (var _i = 0; _i < array_length(_sl); _i++)
    {
        var _v = kfo_jn(_c, _sl[_i][0], variable_struct_get(_o, _sl[_i][0]));
        if (!is_numeric(_v))
            _v = variable_struct_get(_o, _sl[_i][0]);
        variable_struct_set(_o, _sl[_i][0], clamp(_v, _sl[_i][2], _sl[_i][3]));
    }
    _o.every = (_o.pre >= 0) ? _o.every : max(1, round((100 - _o.prec) / 20));
    _o.own = kfo_jn(_c, "own", 0) ? true : false;
    return _o;
}

// the host's per-bot settings (index 0-6 = the bot's place among the bots)
function kfo_host_botcfg(_i)
{
    var _h = global.kfo.H;
    if (!variable_struct_exists(_h, "botcfg"))
        _h.botcfg = [];
    while (array_length(_h.botcfg) <= _i)
        array_push(_h.botcfg, kfo_bot_cfg(kfo_jn(_h.set, "botp", 2)));
    var _c = _h.botcfg[_i];
    // the room's BOT SKILL for the bots the host did not set one by one
    if (!_c.own && _c.pre != kfo_jn(_h.set, "botp", 2))
    {
        _c = kfo_bot_cfg(kfo_jn(_h.set, "botp", 2));
        _h.botcfg[_i] = _c;
    }
    return _c;
}

// ---------- every bullet in the host's box: its place, how it moved, when it was first seen ----------
function kfo_bot_track()
{
    if (!variable_global_exists("kfo_bt") || !is_struct(global.kfo_bt))
        global.kfo_bt = { f: 0, m: {}, l: [] };
    var _T = global.kfo_bt;
    _T.f++;
    var _F = _T.f;
    var _l = [];
    var _m = _T.m;
    // (obj_collidebullet: what can hurt a SOUL - see kfo_bot_hit_by)
    with (obj_collidebullet)
    {
        if (string_pos("growtangle", object_get_name(object_index)) > 0)
            continue;
        if (bbox_right < bbox_left)
            continue;
        // DRBR: Spamton NEO's RECREW walls are played by the odds (kbr_sn_bot_walls): never tracked nor dodged (a wall of
        // dozens of cells cost every bot's planning for nothing)
        if (kbr_sn_bot_skip(id))
            continue;
        var _k = string(real(id));
        var _e = variable_struct_exists(_m, _k) ? variable_struct_get(_m, _k) : undefined;
        if (is_undefined(_e))
        {
            _e = { i: id, x: x, y: y, vx: hspeed, vy: vspeed, f0: _F, seen: _F, gb: {}, a: image_angle, va: 0, xs: image_xscale, ys: image_yscale, vxs: 0, vys: 0, seg: -1, segw: 0, ax: 0, ay: 0, pax: 0, pay: 0, aok: false, tw: 0, ptw: 0, tok: false };
            variable_struct_set(_m, _k, _e);
        }
        else
        {
            // what it did since last frame (bullets moved by their own code as well as by speed)
            var _ovx = _e.vx;
            var _ovy = _e.vy;
            _e.vx = x - _e.x;
            _e.vy = y - _e.y;
            if (abs(_e.vx) > 60 || abs(_e.vy) > 60)
            {
                _e.vx = hspeed;
                _e.vy = vspeed;
            }
            // build 52: how its speed changes (a sword speeding up, a star slowing down, a curve): PERFECT bots follow it
            // when it changed the same way two frames running (a bounce or a jump is not a steady change)
            var _nax = _e.vx - _ovx;
            var _nay = _e.vy - _ovy;
            _e.aok = (_e.seen == _F - 1) && (abs(_nax - _e.pax) < 0.08) && (abs(_nay - _e.pay) < 0.08) && (abs(_nax) + abs(_nay) > 0.005) && (abs(_nax) < 3) && (abs(_nay) < 3);
            _e.pax = _nax;
            _e.pay = _nay;
            _e.ax = _e.aok ? _nax : 0;
            _e.ay = _e.aok ? _nay : 0;
            // build 52: a bullet going round (a vortex sword, a curve): how far its path turns a frame, when it turns the same
            // way two frames running at a steady speed - PERFECT follows the arc
            var _sp0 = sqrt((_ovx * _ovx) + (_ovy * _ovy));
            var _sp1 = sqrt((_e.vx * _e.vx) + (_e.vy * _e.vy));
            var _ntw = (_sp0 > 0.3 && _sp1 > 0.3) ? radtodeg(arctan2((_ovx * _e.vy) - (_ovy * _e.vx), (_ovx * _e.vx) + (_ovy * _e.vy))) : 0;
            _e.tok = (_e.seen == _F - 1) && (abs(_ntw) >= 0.3) && (abs(_ntw) <= 40) && (abs(_ntw - _e.ptw) < 1.5) && (abs(_sp1 - _sp0) < 0.6);
            _e.ptw = _ntw;
            _e.tw = _e.tok ? _ntw : 0;
            _e.x = x;
            _e.y = y;
            _e.seen = _F;
            // a turning bullet (a blade sweeping round): how fast it turns
            _e.va = angle_difference(image_angle, _e.a);
            _e.a = image_angle;
            // a growing one (a slash drawn out from nothing): how fast it grows
            _e.vxs = image_xscale - _e.xs;
            _e.vys = image_yscale - _e.ys;
            _e.xs = image_xscale;
            _e.ys = image_yscale;
        }
        // not active yet (a warning, a sword still rising): it may turn on - looked at, but it counts half
        _e.w = (variable_instance_exists(id, "active") && active != 1) ? 0.5 : 1;
        // build 52: the stars hit only on a small test round the SOUL's middle (kfo_bot_precise): the size PERFECT plans with
        _e.pr = kfo_bot_precise(id);
        // build 52: a vortex sword's exact path (its own Step, frame by frame): kfo_bot_vortex_path
        _e.vp = kfo_bot_vortex_path(id);
        _e.l = bbox_left;
        _e.t = bbox_top;
        _e.r = bbox_right;
        _e.b = bbox_bottom;
        // how far its shape reaches from its origin at scale 1 (its mask's farthest corner): what a turning or growing one
        // can reach
        _e.dyn = (abs(_e.va) > 0.5 || abs(_e.vxs) > 0.001 || abs(_e.vys) > 0.001);
        if (!variable_struct_exists(_e, "r1"))
        {
            var _ms = (mask_index >= 0) ? mask_index : sprite_index;
            _e.r1 = 0;
            if (_ms >= 0)
            {
                var _w = sprite_get_width(_ms);
                var _hh2 = sprite_get_height(_ms);
                var _ox = sprite_get_xoffset(_ms);
                var _oy = sprite_get_yoffset(_ms);
                _e.r1 = max(point_distance(0, 0, -_ox, -_oy), point_distance(0, 0, _w - _ox, -_oy), point_distance(0, 0, -_ox, _hh2 - _oy), point_distance(0, 0, _w - _ox, _hh2 - _oy));
            }
        }
        _e.rad = max(point_distance(x, y, bbox_left, bbox_top), point_distance(x, y, bbox_right, bbox_top), point_distance(x, y, bbox_left, bbox_bottom), point_distance(x, y, bbox_right, bbox_bottom));
        // build 50: a full-screen slash of a Roaring (Kaizo's Roaring DELTA): while it warns it is a short marker where it
        // was made, but it strikes along the whole line the player sees drawn (roaring2_x1,y1 - x2,y2) - the bots look at that
        // line
        _e.seg = -1;
        if (variable_instance_exists(id, "roaring2_fullscreen") && roaring2_fullscreen && variable_instance_exists(id, "roaring2_x1"))
        {
            if (!(variable_instance_exists(id, "slash") && slash && active != 1))
            {
                _e.seg = [roaring2_x1, roaring2_y1, roaring2_x2, roaring2_y2];
                _e.segw = 4;
                _e.w = 1;
            }
        }
        // a sent skill's sword waits, then flies: harmless until then, then at its own speed
        _e.wait = 0;
        _e.kf = -1;
        if (variable_instance_exists(id, "kbr") && kbr != 0)
        {
            _e.kf = variable_instance_exists(id, "kbrf") ? kbrf : -1;
            // (a sent sword is live for the bots once it stops waiting, whatever its active flag says in the host's game)
            _e.w = 1;
            if (variable_instance_exists(id, "wait") && wait > 0)
            {
                _e.wait = wait;
                _e.vx = lengthdir_x(lspd, ldir);
                _e.vy = lengthdir_y(lspd, ldir);
            }
        }
        array_push(_l, _e);
    }
    _T.l = _l;
    // build 52: what is about to strike (PERFECT reads the attacks' tells)
    _T.tl = kfo_bot_tells();
    // forget the ones that are gone
    if ((_F mod 30) == 0)
    {
        var _ks = variable_struct_get_names(_m);
        for (var _i = 0; _i < array_length(_ks); _i++)
        {
            var _e2 = variable_struct_get(_m, _ks[_i]);
            if (_e2.seen < _F - 2)
                variable_struct_remove(_m, _ks[_i]);
        }
    }
    return array_length(_l);
}

// build 52: the attacks' tells - lines that will strike, worked out from the attack objects' own numbers (the same ones their
// Step code uses), for PERFECT bots to plan round before anything is there:
//  - a tracking sword (obj_tracking_sword1*): it lines up on the SOUL along its direction, flashes (con 2) and slashes along
//    that line through the SOUL (con 3, its second frame) - the line and the frame it strikes;
//  - a rotating slash (obj_knight_rotating_slash*): it fixes its aim point, turns (aim_direction, rotation easing to
//    rotation_goal), then slashes slash_number lines through the aim point, one a frame, at
//    (360 / (2 * slash_number)) * a + random_offset + aim_direction; once the lines are drawn up (slash_list) they are exact.
// Each tell: { seg: [x1, y1, x2, y2], segw, wait (frames to the strike), life (frames it can hit) }.
function kfo_bot_tells()
{
    var _o = [];
    var _tn = ["obj_tracking_sword1", "obj_tracking_sword1_Copy", "obj_tracking_sword1_Copy_Copy"];
    for (var _j = 0; _j < array_length(_tn); _j++)
    {
        var _ob = asset_get_index(_tn[_j]);
        if (_ob < 0 || !instance_exists(_ob))
            continue;
        with (_ob)
        {
            if (!variable_instance_exists(id, "con") || !variable_instance_exists(id, "flashtime") || !variable_instance_exists(id, "timer"))
                continue;
            var _w = -1;
            if (con == 2)
                _w = max(0, (flashtime + 1) - timer) + 2;
            else if (con == 1 && variable_instance_exists(id, "waittime") && variable_instance_exists(id, "fadetofulltime"))
                _w = max(0, (waittime + fadetofulltime) - timer) + flashtime + 3;
            else if (con == 3 && timer < 2)
                _w = 2 - timer;
            if (_w < 0 || _w > 60)
                continue;
            array_push(_o, { seg: [x + lengthdir_x(40, direction), y + lengthdir_y(40, direction), x + lengthdir_x(900, direction + 180), y + lengthdir_y(900, direction + 180)], segw: 8, wait: _w, life: 6, w: 1, kf: -1, f0: -999, tele: 1, dyn: false, l: 0, t: 0, r: 0, b: 0, vx: 0, vy: 0 });
        }
    }
    var _rn = ["obj_knight_rotating_slash", "obj_knight_rotating_slash_Copy", "obj_knight_rotating_slash__v1", "obj_knight_rotating_slash__v2", "obj_knight_rotating_slash__v3", "obj_knight_rotating_slash__v4", "obj_knight_rotating_slash__v5"];
    for (var _j = 0; _j < array_length(_rn); _j++)
    {
        var _ob = asset_get_index(_rn[_j]);
        if (_ob < 0 || !instance_exists(_ob))
            continue;
        with (_ob)
        {
            if (!variable_instance_exists(id, "state") || !variable_instance_exists(id, "aim_x") || !variable_instance_exists(id, "aim_direction") || !variable_instance_exists(id, "slash_number"))
                continue;
            // how far the aim turned last frame (each knight's version turns at its own rate)
            var _pa = variable_instance_exists(id, "kfo_pa") ? kfo_pa : aim_direction;
            var _ra = angle_difference(aim_direction, _pa);
            kfo_pa = aim_direction;
            if (state == "aim" && variable_instance_exists(id, "slash_base") && variable_instance_exists(id, "slash_offset") && timer >= 1)
            {
                var _rem = (slash_base + 6 + slash_offset) - timer;
                if (_rem < 0 || _rem > 60)
                    continue;
                // the turn to come: the last frame's turn, easing as "rotation" eases to its goal
                var _fa = aim_direction;
                if (variable_instance_exists(id, "rotation") && variable_instance_exists(id, "rotation_goal") && variable_instance_exists(id, "rotation_change"))
                {
                    var _rot = rotation;
                    var _per = (abs(rotation) > 0.0001) ? (_ra / rotation) : 0;
                    for (var _k = 0; _k < _rem; _k++)
                    {
                        _rot = (_rot < rotation_goal) ? min(rotation_goal, _rot + rotation_change) : max(rotation_goal, _rot - rotation_change);
                        _fa += _rot * _per;
                    }
                }
                else
                    _fa += _ra * _rem;
                var _ro = variable_instance_exists(id, "random_offset") ? random_offset : 0;
                for (var _a = 0; _a < slash_number; _a++)
                {
                    var _d = ((360 / (slash_number * 2)) * _a) + _ro + _fa;
                    array_push(_o, { seg: [aim_x - lengthdir_x(640, _d), aim_y - lengthdir_y(640, _d), aim_x + lengthdir_x(640, _d), aim_y + lengthdir_y(640, _d)], segw: 14, wait: _rem + 1, life: slash_number + 3, w: 1, kf: -1, f0: -999, tele: 1, dyn: false, l: 0, t: 0, r: 0, b: 0, vx: 0, vy: 0 });
                }
            }
            else if (state == "slash" && variable_instance_exists(id, "slash_list") && ds_exists(slash_list, ds_type_list))
            {
                // drawn up: each line exact, the a-th at the slash state's frame a + 1
                for (var _a = max(0, timer - 1); _a < ds_list_size(slash_list); _a++)
                {
                    var _d = ds_list_find_value(slash_list, _a);
                    array_push(_o, { seg: [aim_x - lengthdir_x(640, _d), aim_y - lengthdir_y(640, _d), aim_x + lengthdir_x(640, _d), aim_y + lengthdir_y(640, _d)], segw: 10, wait: max(0, (_a + 1) - timer), life: 3, w: 1, kf: -1, f0: -999, tele: 1, dyn: false, l: 0, t: 0, r: 0, b: 0, vx: 0, vy: 0 });
                }
            }
        }
    }
    return _o;
}

// build 52: where a vortex sword (obj_sword_vortex) will be, frame by frame, for the next 40 frames: [x, y, image_angle] per
// frame, worked out with its own Step's numbers (every knight's version is the same):
//   dir -= spinspeed * lerp(2, 1, len / 120); image_angle = dir - 90;
//   len = lenstart + sin(manager.siner / sinspeed) * sinpower; x, y = the manager's centre + lengthdir(len, dir);
//   lenstart -= shrinkrate          (the manager: siner + 1 a frame; a moving centre eases to its target)
// -1 when it is not a vortex sword (or its manager is gone).
function kfo_bot_vortex_path(_i)
{
    if (object_get_name(_i.object_index) != "obj_sword_vortex")
        return -1;
    var _mo = asset_get_index("obj_sword_vortex_manager");
    if (_mo < 0 || !instance_exists(_mo))
        return -1;
    var _m = instance_find(_mo, 0);
    if (!variable_instance_exists(_i, "dir") || !variable_instance_exists(_i, "spinspeed") || !variable_instance_exists(_i, "lenstart") || !variable_instance_exists(_i, "sinspeed")
        || !variable_instance_exists(_i, "sinpower") || !variable_instance_exists(_i, "len") || !variable_instance_exists(_m, "siner") || _i.sinspeed == 0)
        return -1;
    var _shr = variable_instance_exists(_i, "shrinkrate") ? _i.shrinkrate : 0;
    // which manager frame its last step used (the manager may have stepped before or after it this frame)
    var _sn = _m.siner;
    if (abs(((_i.lenstart + _shr) + (sin((_m.siner - 1) / _i.sinspeed) * _i.sinpower)) - _i.len) < abs(((_i.lenstart + _shr) + (sin(_m.siner / _i.sinspeed) * _i.sinpower)) - _i.len))
        _sn = _m.siner - 1;
    var _dir = _i.dir;
    var _len = _i.len;
    var _ls = _i.lenstart;
    var _cx = _m.swordcirclecenterx;
    var _cy = _m.swordcirclecentery;
    var _mv = variable_instance_exists(_m, "centermoves") && _m.centermoves == 1 && variable_instance_exists(_m, "centermovescon") && _m.centermovescon == 1
        && variable_instance_exists(_m, "movespeed") && _m.movespeed > 0;
    var _o = array_create(120, 0);
    for (var _k = 1; _k <= 40; _k++)
    {
        _dir -= _i.spinspeed * lerp(2, 1, _len / 120);
        _len = _ls + (sin((_sn + _k) / _i.sinspeed) * _i.sinpower);
        _ls -= _shr;
        if (_mv)
        {
            // (the centre's clock is one frame behind too when the manager steps after its swords)
            var _u = min(_m.movespeed, _m.centermovestimer + _k + (_sn - _m.siner)) / _m.movespeed;
            _cx = lerp(_m.startx, _m.targetx, _u);
            _cy = lerp(_m.starty, _m.targety, _u);
        }
        _o[(_k - 1) * 3] = _cx + lengthdir_x(_len, _dir);
        _o[((_k - 1) * 3) + 1] = _cy + lengthdir_y(_len, _dir);
        _o[((_k - 1) * 3) + 2] = _dir - 90;
    }
    return _o;
}

// the SOUL's hitbox (half sizes): the host's own SOUL's, so a bot is as big a target as a player
function kfo_bot_hit_half()
{
    if (instance_exists(obj_heart))
    {
        var _h = instance_find(obj_heart, 0);
        var _w = (_h.bbox_right - _h.bbox_left) / 2;
        var _hh = (_h.bbox_bottom - _h.bbox_top) / 2;
        if (_w >= 1 && _w <= 20 && _hh >= 1 && _hh <= 20)
            return [_w, _hh];
    }
    return [4, 4];
}

// how bad it is for SOUL centre path (_x0, _y0) + (_dx, _dy) a frame (clamped to the box) for bot _b with settings _c:
// a hit sooner costs more; near misses and the box's edges / corners cost a little
function kfo_bot_cost(_b, _c, _box, _x0, _y0, _dx, _dy, _hw, _hh, _l, _bound, _k, _dx2, _dy2)
{
    var _H = max(1, _c.pred);
    var _cost = 0;
    var _near = 999;
    // build 49: a PERFECT bot (no delay, no mistakes, exact) also keeps its distance from every bullet over the whole
    // look-ahead, not only the next frames
    var _smart = (_c.prec >= 100 && _c.miss <= 0 && _c.react <= 0);
    var _n = array_length(_l);
    // build 52: PERFECT's path includes a Roaring's pull (every frame toward the knight: kfo_bot_think works it out)
    var _sux = (_smart && variable_global_exists("kfo_bot_suck")) ? global.kfo_bot_suck[0] : 0;
    var _suy = (_smart && variable_global_exists("kfo_bot_suck")) ? global.kfo_bot_suck[1] : 0;
    var _hw0 = _hw;
    var _hh0 = _hh;
    // the frames looked at: every one at first, then wider apart
    for (var _t = 1; _t <= _H; _t += ((_t < 8) ? 1 : ((_t < 16) ? 2 : 3)))
    {
        // a plan of two moves: (_dx, _dy) for _k frames, then (_dx2, _dy2)
        var _px = clamp((_t <= _k) ? (_x0 + (_dx * _t)) : (_x0 + (_dx * _k) + (_dx2 * (_t - _k))), _box[0], _box[2]);
        var _py = clamp((_t <= _k) ? (_y0 + (_dy * _t)) : (_y0 + (_dy * _k) + (_dy2 * (_t - _k))), _box[1], _box[3]);
        if (_sux != 0 || _suy != 0)
        {
            _px = clamp(_px + (_sux * _t), _box[0], _box[2]);
            _py = clamp(_py + (_suy * _t), _box[1], _box[3]);
        }
        for (var _i = 0; _i < _n; _i++)
        {
            var _e = _l[_i];
            // build 52: PERFECT plans with each bullet's real hit size: a star's small test (its own), every other bullet the
            // SOUL's box with half a pixel to spare from the second frame on (the farther ahead, the less sure)
            _hw = _hw0;
            _hh = _hh0;
            if (_smart)
            {
                if (variable_struct_exists(_e, "pr") && _e.pr >= 0)
                {
                    _hw = max(0.5, _e.pr / 2) + ((_t >= 2) ? 0.5 : 0);
                    _hh = _hw;
                }
                else if (_t >= 2)
                {
                    _hw = _hw0 + 0.5;
                    _hh = _hh0 + 0.5;
                }
            }
            // the bot's hit test runs right after its move, against the bullets where they are then: after _t moves of the
            // bot, the bullets have moved _t - 1 times
            var _tt = _t - 1;
            // build 50: a full-screen line (see kfo_bot_track): how far the SOUL is from it
            if (is_array(_e.seg))
            {
                // build 52: a tell (kfo_bot_tells): the line strikes from frame "wait" for "life" frames
                if (variable_struct_exists(_e, "life") && (_tt < _e.wait || _tt > _e.wait + _e.life))
                    continue;
                var _sg = max(0, kfo_seg_dist(_px, _py, _e.seg[0], _e.seg[1], _e.seg[2], _e.seg[3]) - _e.segw - max(_hw, _hh));
                if (_t <= 6)
                    _near = min(_near, _sg);
                if (_sg <= 0)
                    _cost += 1000 * ((_H + 2) - _t) * _e.w;
                continue;
            }
            var _mx = (_e.wait > _tt) ? 0 : (_e.vx * (_tt - _e.wait));
            var _my = (_e.wait > _tt) ? 0 : (_e.vy * (_tt - _e.wait));
            // build 52: PERFECT follows a vortex sword's exact path (kfo_bot_vortex_path), an arc (a steady turn: the sum of its
            // turning moves), or a steady change of speed (up to 12 frames of it, then the speed it reached)
            var _pang = undefined;
            if (_smart && _tt >= 1 && variable_struct_exists(_e, "vp") && is_array(_e.vp))
            {
                var _vk = (min(_tt, 40) - 1) * 3;
                _mx = _e.vp[_vk] - _e.x;
                _my = _e.vp[_vk + 1] - _e.y;
                _pang = _e.vp[_vk + 2];
            }
            else if (_smart && _e.wait <= _tt && _e.tok)
            {
                var _tm2 = min(_tt - _e.wait, 40);
                var _wr = degtorad(_e.tw);
                var _c1 = cos(_wr);
                var _s1 = sin(_wr);
                var _cn = cos(_wr * (_tm2 + 1));
                var _sn = sin(_wr * (_tm2 + 1));
                var _qa = _c1 - _cn;
                var _qb = _s1 - _sn;
                var _qc = 1 - _c1;
                var _dd = (_qc * _qc) + (_s1 * _s1);
                if (_dd > 0.0000001)
                {
                    var _qr = ((_qa * _qc) - (_qb * _s1)) / _dd;
                    var _qi = ((_qa * _s1) + (_qb * _qc)) / _dd;
                    _mx = (_e.vx * _qr) - (_e.vy * _qi);
                    _my = (_e.vx * _qi) + (_e.vy * _qr);
                }
            }
            else if (_smart && _e.wait <= _tt && _e.aok)
            {
                var _tm = _tt - _e.wait;
                var _ta = min(_tm, 12);
                var _af = ((_ta * (_ta + 1)) / 2) + (_ta * (_tm - _ta));
                _mx += _e.ax * _af;
                _my += _e.ay * _af;
            }
            var _turn = (_e.dyn && _e.wait <= _tt);
            var _gap = 0;
            // (growth looked at 12 frames ahead at most)
            var _gt = min(_tt, 12);
            var _pxs = _e.xs + (_e.vxs * _gt);
            var _pys = _e.ys + (_e.vys * _gt);
            if (_turn)
                _gap = max(0, point_distance(_px, _py, _e.x + _mx, _e.y + _my) - max(_e.rad, _e.r1 * max(abs(_pxs), abs(_pys))) - max(_hw, _hh) * 1.42);
            else
            {
                var _gx = max((_e.l + _mx) - (_px + _hw), (_px - _hw) - (_e.r + _mx), 0);
                var _gy = max((_e.t + _my) - (_py + _hh), (_py - _hh) - (_e.b + _my), 0);
                _gap = max(_gx, _gy);
            }
            if (_t <= 6)
                _near = min(_near, _gap);
            else if (_smart && _gap < 12 && _e.wait <= _tt)
                _cost += (8 / (1 + _gap)) * (((_H + 2) - _t) / (_H + 2));
            if (_gap > 0 || _e.wait > _tt)
                continue;
            // the boxes meet: the engine's precise shape (the bullet as it is now against the SOUL's box moved back by the
            // bullet's own motion - the same as the bullet moved on)
            if (instance_exists(_e.i))
            {
                var _miss = true;
                if (_turn)
                {
                    // a turning one: put it where and how it will be turned, ask the engine, put it back
                    var _i0 = _e.i;
                    var _sx = _i0.x;
                    var _sy = _i0.y;
                    var _sa = _i0.image_angle;
                    var _sxs = _i0.image_xscale;
                    var _sys = _i0.image_yscale;
                    _i0.x = _e.x + _mx;
                    _i0.y = _e.y + _my;
                    _i0.image_angle = is_undefined(_pang) ? (_e.a + (_e.va * _tt)) : _pang;
                    _i0.image_xscale = _pxs;
                    _i0.image_yscale = _pys;
                    _miss = (collision_rectangle(_px - _hw, _py - _hh, _px + _hw, _py + _hh, _i0, true, false) == noone);
                    _i0.x = _sx;
                    _i0.y = _sy;
                    _i0.image_angle = _sa;
                    _i0.image_xscale = _sxs;
                    _i0.image_yscale = _sys;
                }
                else
                    _miss = (collision_rectangle((_px - _hw) - _mx, (_py - _hh) - _my, (_px + _hw) - _mx, (_py + _hh) - _my, _e.i, true, false) == noone);
                if (_miss)
                    continue;
            }
            _cost += 1000 * ((_H + 2) - _t) * _e.w;
        }
        // already worse than the best move found: no need to look further (every part of the cost only adds)
        if (_cost > _bound)
            return _cost;
    }
    _hw = _hw0;
    _hh = _hh0;
    var _fx = clamp((3 <= _k) ? (_x0 + (_dx * 3)) : (_x0 + (_dx * _k) + (_dx2 * (3 - _k))), _box[0], _box[2]);
    var _fy = clamp((3 <= _k) ? (_y0 + (_dy * 3)) : (_y0 + (_dy * _k) + (_dy2 * (3 - _k))), _box[1], _box[3]);
    if (_near < 999)
        _cost += 40 / (1 + _near);
    // the walls: a little near an edge, more in a corner (no room left to dodge)
    // (room to move: within 24 px of an edge it costs more the closer it gets; a corner more again - never as much as a hit)
    var _dx0 = min(_fx - _box[0], _box[2] - _fx);
    var _dy0 = min(_fy - _box[1], _box[3] - _fy);
    if (_dx0 < 24)
        _cost += (24 - _dx0) * 1.5;
    if (_dy0 < 24)
        _cost += (24 - _dy0) * 1.5;
    if (_dx0 < 12 && _dy0 < 12)
        _cost += 30;
    // build 49: PERFECT stays off the host's own SOUL - the attacks that aim (tracking swords, slashes) aim at that SOUL in
    // the host's game, where the bots are, so the space around it is where aimed slashes land
    if (_smart && instance_exists(obj_heart))
    {
        var _hs = instance_find(obj_heart, 0);
        var _hd = point_distance(_fx, _fy, (_hs.bbox_left + _hs.bbox_right) / 2, (_hs.bbox_top + _hs.bbox_bottom) / 2);
        if (_hd < 56)
            _cost += (56 - _hd) * 0.6;
    }
    // the bot's own spot of the box (each its own, so they do not all crowd one place), very lightly
    var _sx = lerp(_box[0], _box[2], _b.bt.ax);
    var _sy = lerp(_box[1], _box[3], _b.bt.ay);
    _cost += point_distance(_fx, _fy, _sx, _sy) / 300;
    return _cost;
}

// the distance from point (_px, _py) to the segment (_x1, _y1) - (_x2, _y2)
function kfo_seg_dist(_px, _py, _x1, _y1, _x2, _y2)
{
    var _vx = _x2 - _x1;
    var _vy = _y2 - _y1;
    var _ll = (_vx * _vx) + (_vy * _vy);
    var _u = (_ll <= 0) ? 0 : clamp((((_px - _x1) * _vx) + ((_py - _y1) * _vy)) / _ll, 0, 1);
    return point_distance(_px, _py, _x1 + (_u * _vx), _y1 + (_u * _vy));
}

// the move of bot _b this frame
function kfo_bot_think(_b, _c, _box, _e)
{
    var _s = _b.bt;
    // build 50: in a Roaring a bot holds its breath as a player does (Hold Breath costs nothing: +2 in a Roaring)
    var _spd = max(1, _e.spd - ((_s.slow_t > 0) ? 1 : 0) + ((kfo_bot_roaring() != noone) ? kbr_breath_bonus(true) : 0) + kbr_jv_speed_bonus() + kbr_sn_bot_speed());
    var _hb = kfo_bot_hit_half();
    var _best = 99999999;
    var _smart = (_c.prec >= 100 && _c.miss <= 0 && _c.react <= 0);
    // build 52: a Roaring's pull this frame (as kfo_host_bots_tick applies it), for PERFECT's plans
    global.kfo_bot_suck = [0, 0];
    if (_smart)
    {
        var _ro = kfo_bot_roaring();
        if (_ro != noone && variable_instance_exists(_ro, "player_suck") && variable_instance_exists(_ro, "fake_x") && _ro.player_suck > 0)
        {
            var _sdir = point_direction(_s.x, _s.y, camerax() + _ro.fake_x, cameray() + _ro.fake_y + 55);
            global.kfo_bot_suck = [lengthdir_x(_ro.player_suck, _sdir), lengthdir_y(_ro.player_suck, _sdir)];
        }
    }
    var _bx = 0;
    var _by = 0;
    var _moves = [];
    // the bullets that matter: noticed already (REACTION TIME), not its own, and able to come near within the frames it looks at
    var _T = global.kfo_bt;
    var _F = _T.f;
    var _H = max(1, _c.pred);
    var _rel = [];
    var _rd = [];
    for (var _i = 0; _i < array_length(_T.l); _i++)
    {
        var _q = _T.l[_i];
        if (_q.f0 > _F - _c.react)
            continue;
        if (_q.kf >= 0 && _q.kf == _b.pid)
            continue;
        var _gx = max(_q.l - _s.x, _s.x - _q.r, 0);
        var _gy = max(_q.t - _s.y, _s.y - _q.b, 0);
        var _g = max(_gx, _gy);
        // build 52: DARKNESS - it only sees what is close to it
        if (variable_struct_exists(_s, "dark_t") && _s.dark_t > 0 && _g > 56)
            continue;
        if (_q.dyn)
            _g = max(0, point_distance(_s.x, _s.y, _q.x, _q.y) - max(_q.rad, _q.r1 * max(abs(_q.xs + (_q.vxs * 12)), abs(_q.ys + (_q.vys * 12)))));
        var _reach = ((abs(_q.vx) + abs(_q.vy) + (_spd * 1.5)) * (_H + 1)) + 24;
        if (_g <= _reach)
        {
            array_push(_rel, _q);
            array_push(_rd, _g / max(1, abs(_q.vx) + abs(_q.vy) + _spd));
        }
    }
    // build 52: PERFECT also plans round the lines about to strike (in DARKNESS only the ones it can see near it)
    if (_smart && variable_struct_exists(_T, "tl"))
    {
        for (var _i = 0; _i < array_length(_T.tl); _i++)
        {
            var _q = _T.tl[_i];
            if (variable_struct_exists(_s, "dark_t") && _s.dark_t > 0 && kfo_seg_dist(_s.x, _s.y, _q.seg[0], _q.seg[1], _q.seg[2], _q.seg[3]) > 56)
                continue;
            array_push(_rel, _q);
            array_push(_rd, _q.wait);
        }
    }
    // the 24 that can reach it soonest (a screen full of swords costs the host's game no more than that)
    if (array_length(_rel) > 24)
    {
        // (kept sorted by insertion: the 24 soonest so far)
        var _ord = [];
        for (var _i = 0; _i < array_length(_rel); _i++)
        {
            var _n = array_length(_ord);
            if (_n == 24 && _rd[_i] >= _ord[23][0])
                continue;
            var _j = min(_n, 23);
            if (_n < 24)
                array_push(_ord, [_rd[_i], _i]);
            while (_j > 0 && _ord[_j - 1][0] > _rd[_i])
            {
                _ord[_j] = _ord[_j - 1];
                _j--;
            }
            _ord[_j] = [_rd[_i], _i];
        }
        var _r2 = [];
        for (var _i = 0; _i < array_length(_ord); _i++)
            array_push(_r2, _rel[_ord[_i][1]]);
        _rel = _r2;
    }
    // the move it is making first (the best bound to start from), then the others
    var _ks = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16];
    if (variable_struct_exists(_s, "lk") && _s.lk > 0)
    {
        _ks[0] = _s.lk;
        _ks[_s.lk] = 0;
    }
    var _bk = 0;
    for (var _kk = 0; _kk < 17; _kk++)
    {
        var _k = _ks[_kk];
        var _m = (_k == 0) ? [0, 0] : [lengthdir_x(((_k <= 8) ? _spd : (_spd / 2)), ((_k - 1) mod 8) * 45), lengthdir_y(((_k <= 8) ? _spd : (_spd / 2)), ((_k - 1) mod 8) * 45)];
        // the slow walk: a dummy never uses it
        if (_k > 8 && _c.pre == 0)
            continue;
        var _cost = kfo_bot_cost(_b, _c, _box, _s.x, _s.y, _m[0], _m[1], _hb[0], _hb[1], _rel, _best + 0.5, 999, 0, 0);
        // the slow walk costs a hair more (it is only picked when it is safer)
        if (_k > 8)
            _cost += 0.5;
        array_push(_moves, [_cost, _m[0], _m[1], _k]);
        if (_cost < _best)
        {
            _best = _cost;
            _bk = _k;
            _bx = _m[0];
            _by = _m[1];
        }
    }
    // build 49: PERFECT plans two moves ahead when a single move is not safe (build 52: wider - the 6 best first moves, slow
    // walk too, each followed after 2, 4, 8 or 12 frames by any of the 17 moves). It only makes the first move now and plans
    // again next frame.
    var _wide = (_best >= 1000);
    if (_smart && _wide)
    {
        var _top = [];
        for (var _i = 0; _i < array_length(_moves); _i++)
        {
            if (!_wide && _moves[_i][3] > 8)
                continue;
            var _j = array_length(_top);
            array_push(_top, _moves[_i]);
            while (_j > 0 && _top[_j - 1][0] > _moves[_i][0])
            {
                _top[_j] = _top[_j - 1];
                _j--;
            }
            _top[_j] = _moves[_i];
        }
        var _kk2 = _wide ? [4, 8, 2, 12] : [4, 8];
        var _nd = _wide ? 17 : 9;
        // (2.5 ms at most for this bot's wider plans in the game: the most likely first moves are looked at first)
        var _tq0 = get_timer();
        for (var _a = 0; _a < min(_wide ? 6 : 3, array_length(_top)); _a++)
        {
            if (_a >= 4 && get_timer() - _tq0 > 2500)
                break;
            for (var _q = 0; _q < array_length(_kk2); _q++)
            {
                for (var _d = 0; _d < _nd; _d++)
                {
                    var _sp2 = (_d <= 8) ? _spd : (_spd / 2);
                    var _d2x = (_d == 0) ? 0 : lengthdir_x(_sp2, ((_d - 1) mod 8) * 45);
                    var _d2y = (_d == 0) ? 0 : lengthdir_y(_sp2, ((_d - 1) mod 8) * 45);
                    var _c2 = kfo_bot_cost(_b, _c, _box, _s.x, _s.y, _top[_a][1], _top[_a][2], _hb[0], _hb[1], _rel, _best - 0.01, _kk2[_q], _d2x, _d2y);
                    if (_c2 < _best)
                    {
                        _best = _c2;
                        _bk = _top[_a][3];
                        _bx = _top[_a][1];
                        _by = _top[_a][2];
                    }
                }
            }
        }
    }
    // MISTAKES: now and then a move that is not the best
    if (_c.miss > 0 && random(100) < _c.miss && array_length(_moves) > 0)
    {
        var _r = _moves[irandom(array_length(_moves) - 1)];
        _bx = _r[1];
        _by = _r[2];
    }
    // confused (a CONFUSE skill): the controls turn around, as for a player
    if (_s.conf_t > 0)
    {
        _bx = -_bx;
        _by = -_by;
    }
    _s.ix = _bx;
    _s.iy = _by;
    _s.lk = _bk;
    _s.danger = _best;
    return _best;
}

// ---------- the bots' skills: drawn, held, used like a player's ----------
function kfo_bot_skill_new()
{
    // build 51: a bot starts with its one MAX (FULL HEAL) too, as every player does (the room's STARTING FULL HEAL)
    var _sl = [];
    var _h = global.kfo.H;
    if (is_struct(_h) && variable_struct_exists(_h, "eff") && is_struct(_h.eff) && _h.eff.fullheal && _h.eff.skills)
        array_push(_sl, 16);
    return { slots: _sl, cd: 0, t: 0, fh: 0, det: 0 };
}

// the targeting mode a bot picks for its send
function kfo_bot_pick_mode(_h, _b)
{
    var _e = _h.eff;
    var _c = kfo_host_tg_cands(_b);
    var _low = false;
    var _rich = false;
    var _tired = 0;
    for (var _i = 0; _i < array_length(_c); _i++)
    {
        if (_c[_i].hp <= _c[_i].mh * 0.25)
            _low = true;
        if (_c[_i].sh >= 4 && _c[_i].sh > _b.sh)
            _rich = true;
        if (kfo_host_tg_tired(_c[_i]))
            _tired++;
    }
    var _on = 0;
    for (var _i = 0; _i < array_length(_h.pl); _i++)
    {
        var _p = _h.pl[_i];
        if (_p.inm && _p.al && _p.pid != _b.pid && kbr_tg_has(_p.tg, _b.pid))
            _on++;
    }
    var _m = KBR_TG_CHAOS;
    if (_on >= 2)
        _m = KBR_TG_DEFEND;
    else if (_low)
        _m = KBR_TG_PROCEED;
    else if (_rich)
        _m = KBR_TG_BIG;
    else if (_tired >= 2)
        _m = KBR_TG_PACIFY;
    else if (array_length(_c) >= 3 && random(100) < 15)
        _m = KBR_TG_ROAR;
    return kbr_tg_mode_fix(_e, _m);
}

// what a bot does with its gauge and its skills, every 10 frames
function kfo_bot_skills(_h, _b, _c)
{
    var _e = _h.eff;
    var _s = _b.bt;
    var _K = _s.sk;
    if (!_e.skills)
        return 0;
    var _safe = (_s.danger < 50);
    var _frac = _b.hp / max(1, _b.mh);
    // charge: a smart bot waits for two draws (100) when it is safe and has room, a careless one draws at the cost
    var _need = clamp(round((60 * _e.scost) / 100), 10, 100);
    var _need2 = clamp(round((100 * _e.scost) / 100), _need, 100);
    var _room = clamp(_e.slots, 1, 4) - array_length(_K.slots);
    // build 52: before each draw a bot picks how far it charges, as a player holding CHARGE does: to the price of one skill
    // (the low pool: Sword, Flurry, Heal 40), past the middle (the mid pool) or the full bar (two skills, the full pool).
    // Build 50's bots drew the moment they reached the price, so every draw came from the low pool - they only ever sent
    // swords. A bot whose slots are full, or that has waited 6 seconds, takes what it has.
    if (!variable_struct_exists(_K, "want") || _K.want < 0)
    {
        var _r = random(1);
        _K.want = (_r < 0.2) ? _need : ((_r < 0.6) ? ceil((_need + _need2) / 2) : _need2);
        _K.want_t = 0;
    }
    // CHARGING 100 (PERFECT): always the full bar - two skills, both from the full pool, is the best draw there is
    if (_c.chg >= 100)
        _K.want = _need2;
    // the 6 seconds count only once it could draw (from the price on), so a bot aiming high does wait for its charge
    _K.want_t = (_b.g >= _need) ? ((variable_struct_exists(_K, "want_t") ? _K.want_t : 0) + 10) : 0;
    var _ready = (_b.g >= _K.want) || (_b.g >= _need && _K.want_t >= 180) || (_b.g >= 100);
    if (_room > 0 && _b.g >= _need && _ready)
    {
        _K.want = -1;
        var _amt = floor(_b.g);
        _b.g = max(0, _b.g - _amt);
        var _n = (_amt >= _need2) ? 2 : 1;
        for (var _i = 0; _i < min(_n, _room); _i++)
        {
            var _id = is_struct(global.kfo.M) ? kbr_skill_draw(_amt) : (1 + irandom(9));
            // build 52: DETERMINATION once a match for a bot too (the draw above follows the host's own hand)
            if (_id == 25)
            {
                if (!variable_struct_exists(_K, "det"))
                    _K.det = 0;
                if (_K.det > 0)
                    _id = kbr_skill_ok(15) ? 15 : 13;
                else
                    _K.det++;
            }
            if (_id >= 1)
                array_push(_K.slots, _id);
        }
    }
    if (_K.cd > 0 || array_length(_K.slots) == 0)
        return 0;
    // build 50: how long its slots have been full (a bot never sits on a full hand for long)
    if (!variable_struct_exists(_K, "full_t"))
        _K.full_t = 0;
    _K.full_t = (_room <= 0) ? (_K.full_t + 10) : 0;
    // build 49: a heal it holds is used as soon as it would not be wasted (the HP it is missing is at least most of what
    // the heal gives back), FULL HEAL below half HP, REGENERATION when hurt at all - in danger too when HP is low
    var _pick = -1;
    var _miss = _b.mh - _b.hp;
    var _hm = _e.hmul / 100;
    if (_miss > 0 && (_safe || _frac < 0.5))
    {
        for (var _i = 0; _i < array_length(_K.slots) && _pick < 0; _i++)
        {
            var _id = _K.slots[_i];
            if ((_id == 16 && _frac < 0.5) || (_id == 12 && _miss >= 60 * _hm) || (_id == 11 && _miss >= 30 * _hm) || (_id == 14 && _miss >= 20 && _s.regen_t <= 0))
                _pick = _i;
        }
    }
    // a shield when it is in trouble, reflection when several target it
    if (_pick < 0)
    {
        for (var _i = 0; _i < array_length(_K.slots); _i++)
        {
            var _id = _K.slots[_i];
            if ((_id == 13 && !_safe && _c.heal >= 20) || (_id == 15 && _c.heal >= 20 && kfo_bot_attackers(_h, _b) >= 1))
                _pick = _i;
            // build 52: DETERMINATION when low and in trouble; LIFESTEAL when it also holds an attack to follow it
            if ((_id == 25 && _frac < 0.35 && _s.det_t <= 0) || (_id == 24 && _s.ls_t <= 0 && kfo_bot_has_red(_K, _i)))
                _pick = _i;
        }
    }
    // an attack skill now and then (AGGRESSION), with a targeting mode for the moment
    // (build 50: much more often than before - about every second or two for a NORMAL bot; even DUMMY now and then)
    if (_pick < 0 && random(100) < max(6, _c.aggr * 0.6))
    {
        for (var _i = 0; _i < array_length(_K.slots); _i++)
        {
            if (kbr_skill_red(_K.slots[_i]))
            {
                _pick = _i;
                break;
            }
        }
    }
    // build 50: a full hand held for 4 seconds: it plays something (an attack first, else a shield / reflection / regeneration,
    // a heal only when it is hurt)
    if (_pick < 0 && _K.full_t >= 120)
    {
        for (var _i = 0; _i < array_length(_K.slots) && _pick < 0; _i++)
        {
            if (kbr_skill_red(_K.slots[_i]))
                _pick = _i;
        }
        for (var _i = 0; _i < array_length(_K.slots) && _pick < 0; _i++)
        {
            var _id = _K.slots[_i];
            if (_id == 13 || _id == 15 || _id == 14 || _id == 24 || _id == 25 || ((_id == 11 || _id == 12 || _id == 16) && _miss > 0))
                _pick = _i;
        }
    }
    if (_pick < 0)
        return 0;
    _K.full_t = 0;
    var _sid = _K.slots[_pick];
    if (!kbr_skill_ok(_sid))
    {
        array_delete(_K.slots, _pick, 1);
        return 0;
    }
    array_delete(_K.slots, _pick, 1);
    _K.cd = round(90 * (_e.cdm / 100));
    if (kbr_skill_red(_sid))
    {
        _b.tm = kfo_bot_pick_mode(_h, _b);
        _b.t_sk = -100000;
        kfo_host_skill(_b, { sid: _sid, seq: _b.sq + 1 });
        return 1;
    }
    kfo_bot_green(_h, _b, _sid);
    return 1;
}

// build 52: PERFECT, when every move it can plan is hit within the next few frames: a SHIELD it holds goes up now (or,
// when that hit would put it out, DETERMINATION) - the same skills, cooldown and numbers as a player's
function kfo_bot_emergency(_h, _b, _c)
{
    var _e = _h.eff;
    var _s = _b.bt;
    var _K = _s.sk;
    if (!_e.skills || !(_c.prec >= 100 && _c.miss <= 0 && _c.react <= 0) || _s.inv > 0 || _K.cd > 0 || _s.danger < 1000 * (max(1, _c.pred) - 4))
        return 0;
    if (_s.shield > 0 || (variable_struct_exists(_s, "det_t") && _s.det_t > 0))
        return 0;
    var _pick = -1;
    for (var _i = 0; _i < array_length(_K.slots); _i++)
    {
        if (_K.slots[_i] == 13)
            _pick = _i;
    }
    if (_pick < 0 && _b.hp <= 40 * (_e.dmul / 100))
    {
        for (var _i = 0; _i < array_length(_K.slots); _i++)
        {
            if (_K.slots[_i] == 25)
                _pick = _i;
        }
    }
    if (_pick < 0 || !kbr_skill_ok(_K.slots[_pick]))
        return 0;
    var _sid = _K.slots[_pick];
    array_delete(_K.slots, _pick, 1);
    _K.cd = round(90 * (_e.cdm / 100));
    kfo_bot_green(_h, _b, _sid);
    return 1;
}

// build 52: an attack skill in the bot's hand other than slot _not
function kfo_bot_has_red(_K, _not)
{
    for (var _i = 0; _i < array_length(_K.slots); _i++)
    {
        if (_i != _not && kbr_skill_red(_K.slots[_i]))
            return true;
    }
    return false;
}

function kfo_bot_attackers(_h, _b)
{
    var _on = 0;
    for (var _i = 0; _i < array_length(_h.pl); _i++)
    {
        var _p = _h.pl[_i];
        if (_p.inm && _p.al && _p.pid != _b.pid && kbr_tg_has(_p.tg, _b.pid))
            _on++;
    }
    return _on;
}

// a green skill on a bot (the same numbers as a player's)
function kfo_bot_green(_h, _b, _sid)
{
    var _e = _h.eff;
    var _s = _b.bt;
    switch (_sid)
    {
        case 11: _b.hp = min(_b.mh, _b.hp + round(40 * (_e.hmul / 100))); _b.t_heal = current_time; break;
        case 12: _b.hp = min(_b.mh, _b.hp + round(80 * (_e.hmul / 100))); _b.t_heal = current_time; break;
        case 13: _s.shield = _e.shp; _s.shield_t = 300; break;
        case 14: _s.regen_t = 300; _b.t_heal = current_time; break;
        case 15: _b.t_rf = current_time; break;
        case 16: _b.hp = _b.mh; _b.t_heal = current_time; _s.sk.fh++; break;
        case 24: _s.ls_t = 300; break;
        case 25: _s.det_t = 450; break;
    }
    kfo_host_feed("* " + _b.n + " used " + kbr_skill_fname(_sid) + ".", c_white);
    return 1;
}

// the bots' marks for the others (1 shield, 2 regeneration, 4 reflection)
function kfo_bot_flags(_b)
{
    var _s = _b.bt;
    var _h = global.kfo.H;
    return ((_s.shield > 0) ? 1 : 0) + ((_s.regen_t > 0) ? 2 : 0) + ((current_time - _b.t_rf < ((_h.eff.rsec) * 1000)) ? 4 : 0)
        + ((variable_struct_exists(_s, "ls_t") && _s.ls_t > 0) ? 16 : 0) + ((variable_struct_exists(_s, "det_t") && _s.det_t > 0) ? 32 : 0);
}

// a hit on a bot (after its shield)
function kfo_bot_take(_b, _dmg)
{
    var _s = _b.bt;
    if (_s.shield > 0 && _dmg > 0)
    {
        _s.shield--;
        if (_s.shield <= 0)
            _s.shield_t = 0;
        return 0;
    }
    // build 52: DETERMINATION - a bot left at 1 HP instead of OUT
    if (_b.hp - _dmg <= 0 && variable_struct_exists(_s, "det_t") && _s.det_t > 0)
    {
        _s.det_t = 0;
        var _t1 = max(0, _b.hp - 1);
        _b.hp = 1;
        kfo_host_feed("* " + _b.n + " refused to fall!", make_color_rgb(255, 90, 90));
        return _t1;
    }
    var _took = min(_b.hp, _dmg);
    _b.hp = max(0, _b.hp - _dmg);
    return _took;
}

// ---------- every step of the host's match ----------
function kfo_host_bots_tick()
{
    var _h = global.kfo.H;
    var _e = _h.eff;
    var _box = kfo_bot_box();
    var _running = kbr_on() && is_struct(global.kfo.M) && global.kfo.M.R.ph == "run";
    var _tracked = false;
    // the bots' thinking shares 6 ms of a frame at most (seven PERFECT bots in a screen full of bullets): one that runs out
    // of time keeps its move and thinks first next frame (who goes first rotates)
    var _t0 = get_timer();
    if (!variable_struct_exists(_h, "bot_rr"))
        _h.bot_rr = 0;
    _h.bot_rr++;
    var _np = array_length(_h.pl);
    var _bix = [];
    var _nb = 0;
    for (var _i = 0; _i < _np; _i++)
    {
        array_push(_bix, _nb);
        if (_h.pl[_i].bot)
            _nb++;
    }
    for (var _ii = 0; _ii < _np; _ii++)
    {
        var _i = (_ii + _h.bot_rr) mod _np;
        var _b = _h.pl[_i];
        if (!_b.bot)
            continue;
        var _bi = _bix[_i];
        if (!_b.inm || !_b.al)
            continue;
        if (!is_struct(_b.bt))
            kfo_bot_reset(_b);
        var _s = _b.bt;
        var _c = kfo_host_botcfg(_bi);
        _b.bd = _c.pre;
        // the host's battle is not running this match (it should be): the bots take an average beating instead
        if (!kbr_on())
        {
            if (_h.go && current_time - _b.t_s > 3000)
            {
                _b.t_s = current_time;
                _b.hp -= irandom(10);
                if (_b.hp <= 0)
                    kfo_host_out_now(_b.pid, round(kfo_host_tick_now()), "out");
            }
            continue;
        }
        _b.t_s = current_time;
        if (is_undefined(_box))
            continue;
        if (!_s.placed)
        {
            _s.placed = true;
            _s.x = lerp(_box[0], _box[2], 0.2 + random(0.6));
            _s.y = lerp(_box[1], _box[3], 0.2 + random(0.6));
        }
        // keep inside the box (it changes with every attack)
        _s.x = clamp(_s.x, _box[0], _box[2]);
        _s.y = clamp(_s.y, _box[1], _box[3]);
        // the buffs and the cooldown run down
        if (_s.slow_t > 0)
            _s.slow_t--;
        if (_s.conf_t > 0)
            _s.conf_t--;
        if (variable_struct_exists(_s, "dark_t") && _s.dark_t > 0)
            _s.dark_t--;
        if (variable_struct_exists(_s, "ls_t") && _s.ls_t > 0)
            _s.ls_t--;
        if (variable_struct_exists(_s, "det_t") && _s.det_t > 0)
            _s.det_t--;
        if (_s.shield_t > 0)
        {
            _s.shield_t--;
            if (_s.shield_t <= 0)
                _s.shield = 0;
        }
        if (_s.regen_t > 0)
        {
            _s.regen_t--;
            if ((_s.regen_t mod 30) == 0)
                _b.hp = min(_b.mh, _b.hp + round(3 * (_e.hmul / 100)));
        }
        if (_s.sk.cd > 0)
            _s.sk.cd--;
        _b.sk = kfo_bot_flags(_b);
        if (_running)
        {
            if (!_tracked)
            {
                kfo_bot_track();
                _tracked = true;
            }
            _s.alive_f++;
            // DRBR: one of Flowery's attacks - an orange SOUL's board is the host player's own: the bots play it by the odds
            // (kbr_fl_bot_tick: their place, their hits, their FLOWERY TP)
            var _orange = kbr_fl_bot_tick(_h, _b, _c, _box, _e) || kbr_pk_bot_odds(_h, _b, _c, _box, _e);
            if (_orange && _b.hp <= 0)
                continue;
            if (!_orange)
            {
                // its own spot of the box moves now and then
                if ((_s.alive_f mod 150) == 0)
                {
                    _s.ax = 0.2 + random(0.6);
                    _s.ay = 0.2 + random(0.6);
                }
                if (((_s.alive_f mod max(1, _c.every)) == 0 || _s.owe) && _c.pre != -2)
                {
                    if (get_timer() - _t0 < 6000)
                    {
                        kfo_bot_think(_b, _c, _box, _e);
                        _s.owe = false;
                        kfo_bot_emergency(_h, _b, _c);
                    }
                    else
                        _s.owe = true;
                }
                // PRECISION: a wobble on every move
                var _wob = (100 - _c.prec) / 40;
                _s.x = clamp(_s.x + _s.ix + ((_wob > 0) ? random_range(-_wob, _wob) : 0), _box[0], _box[2]);
                _s.y = clamp(_s.y + _s.iy + ((_wob > 0) ? random_range(-_wob, _wob) : 0), _box[1], _box[3]);
                // build 50: a Roaring pulls every SOUL toward the knight (its player_suck), the bots' too
                var _ro = kfo_bot_roaring();
                if (_ro != noone && variable_instance_exists(_ro, "player_suck") && variable_instance_exists(_ro, "fake_x") && _ro.player_suck > 0)
                {
                    var _sdir = point_direction(_s.x, _s.y, camerax() + _ro.fake_x, cameray() + _ro.fake_y + 55);
                    _s.x = clamp(_s.x + lengthdir_x(_ro.player_suck, _sdir), _box[0], _box[2]);
                    _s.y = clamp(_s.y + lengthdir_y(_ro.player_suck, _sdir), _box[1], _box[3]);
                }
                // DRBR: Pink's purple SOUL - on her lanes / grid / rolling box's nodes (online_pink53.gml)
                kbr_pk_bot_snap(_s);
                // DRBR: Gerson's green attacks - every SOUL sits on the box's middle behind its shield (the spears: kbr_hj_bots_spear)
                if (kbr_hj_bots_green(_box))
                {
                    _s.x = lerp(_s.x, (_box[0] + _box[2]) / 2, 0.2);
                    _s.y = lerp(_s.y, (_box[1] + _box[3]) / 2, 0.2);
                }
                // hits (its own invincibility frames, the same damage table as everyone's)
                if (_s.inv > 0)
                    _s.inv--;
                else
                {
                    var _hb = kfo_bot_hit_by(_s.x, _s.y, _b.pid);
                    if (_hb != noone && instance_exists(_hb))
                    {
                        var _nm = (is_struct(global.kfo.M) && global.kfo.M.cur_ok >= 0 && kbr_nightmare(global.kfo.M.cur_ok));
                        var _t = kbr_hit_dmg(kbr_hit_kind(_hb.object_index), _nm);
                        var _dmg = max(1, round(_t[0] * (_e.dmul / 100)));
                        // a player's attack skill (a targeted room): its own damage, and the credit
                        if (variable_instance_exists(_hb, "kbr") && _hb.kbr != 0)
                        {
                            _dmg = max(1, round(_hb.kbrd * (_e.skdmg / 100) * (_e.dmul / 100)));
                            _t = [_dmg, 30];
                            if (variable_instance_exists(_hb, "kbrf") && _hb.kbrf >= 0)
                                _b.lby = _hb.kbrf;
                        }
                        if (_e.ohko)
                            _dmg = _b.hp;
                        var _tk = kfo_bot_take(_b, _dmg);
                        if (variable_instance_exists(_hb, "kbr") && _hb.kbr != 0 && variable_instance_exists(_hb, "kbrf") && _hb.kbrf >= 0)
                            kfo_host_dealt(_hb.kbrf, _tk);
                        _b.hits++;
                        _s.inv = round(_t[1] * (_e.ifr / 100));
                        if (_b.hp <= 0)
                        {
                            kfo_host_out_report(_b.pid, round(kfo_host_tick_now()), "out", _b.lby);
                            continue;
                        }
                    }
                    else
                        kfo_bot_graze(_b, _e);
                }
                // DRBR: Spamton NEO's RECREW walls, by the odds (online_spamton53.gml)
                if (kbr_sn_bot_walls(_b, _c, _e))
                    continue;
            }
            // the gauge, like a player's (about one point a second, CHARGE RATE; OUTNUMBERED BONUS)
            if ((_s.alive_f mod 30) == 0)
            {
                var _om = 1;
                if (kbr_tg_on(_e) && _e.outn)
                {
                    var _B = kbr_tg_bal();
                    _om = 1 + min(_B.outn_max, kfo_bot_attackers(_h, _b) * _B.outn_per);
                }
                _b.g = min(100, _b.g + ((_e.gmul / 100) * _om));
            }
            // sudden death takes the bots' max HP too
            if (is_struct(global.kfo.M) && global.kfo.M.sd_on && (_s.alive_f mod 30) == 0 && _b.mh > _e.sdfloor)
            {
                _b.mh = max(_e.sdfloor, _b.mh - _e.sdrate);
                _b.hp = min(_b.hp, _b.mh);
            }
            if ((_s.alive_f mod 10) == 0)
                kfo_bot_skills(_h, _b, _c);
        }
        // its position for everyone: like a player's, relative to the battle's camera
        _b.x = _s.x - 10 - kbr_ox();
        _b.y = _s.y - 10 - kbr_oy();
        _b.t_p = current_time;
    }
    return 0;
}

// a graze: a bullet close to a bot's SOUL for the first time (the room's GRAZE CHARGE, as for a player)
function kfo_bot_graze(_b, _e)
{
    if (!variable_global_exists("kfo_bt") || !is_struct(global.kfo_bt))
        return 0;
    var _s = _b.bt;
    var _l = global.kfo_bt.l;
    for (var _i = 0; _i < array_length(_l); _i++)
    {
        var _q = _l[_i];
        if ((_q.kf >= 0 && _q.kf == _b.pid) || variable_struct_exists(_q.gb, string(_b.pid)))
            continue;
        var _gx = max(_q.l - _s.x, _s.x - _q.r, 0);
        var _gy = max(_q.t - _s.y, _s.y - _q.b, 0);
        if (max(_gx, _gy) < 14)
        {
            variable_struct_set(_q.gb, string(_b.pid), 1);
            _b.g = min(100, _b.g + (_e.grz / 100));
        }
    }
    return 1;
}
