
// ===== Fight pacing and the battle rules (Twin Knight, Darkness, Hyper speed, Thorns, Time limit) =====

// ---------- pacing ----------
// Every knight fight plays a fixed list of attacks, one per enemy turn, and starts its Roaring finale at the end of the first
// enemy turn where the knight's HP is at or under a gate (Normal 80%, Kaizo 60%, Violet 65% / Side B 13%, Thorn 50%, ...).
// A strong party (hub spells, good gear, Noelle) used to pass the gate after a few turns and never see most of the list, and
// the mods put their new attacks at the end of it. So, until the list has been played, the knight follows a schedule line
// (straight from full HP down to the gate on the last listed turn):
//   - damage that keeps the knight above the line counts in full,
//   - the rest counts 35% at the line, less and less the further ahead of the line the knight already is, but never under 5%
//     (build 39: no hard stop at the gate any more, so a hit always deals damage - no MISS - and a very strong party simply
//     reaches the Roaring a little before the end of the list),
//   - the knight cannot fall before its Roaring (its last 5% of HP counts less, and a hit always leaves it at least 1 HP).
// Slow parties get a catch-up instead: past the end of the list, while the knight is still above the gate, every hit gains
// 12% per extra turn (up to x2). Practice, joke fights and everything after the Roaring keep the fight's own rules.

function knight_side_b()
{
    if (!i_ex(obj_knight_enemy))
        return false;
    var _e = instance_find(obj_knight_enemy, 0);
    if (variable_instance_exists(_e, "v_sideb") && _e.v_sideb)
        return true;
    if (variable_instance_exists(_e, "k_sideb") && _e.k_sideb)
        return true;
    return false;
}

function knight_pace_now(_k)
{
    var _p = knight_reg(_k).pace;
    if (knight_side_b())
        return { gate: _p.gate_b, tmin: _p.tmin_b };
    return { gate: _p.gate, tmin: _p.tmin };
}

function knight_roared()
{
    if (!i_ex(obj_knight_enemy))
        return false;
    var _e = instance_find(obj_knight_enemy, 0);
    return (variable_instance_exists(_e, "haveusedroaring") && _e.haveusedroaring);
}

// the part of _over (damage past a soft line) that counts when the knight is already _depth past that line: 35% at the line,
// falling smoothly (scale _s) to 5% the further past it the knight is, never under 5%. Worked out over the whole hit, so one big
// hit counts the same as several small ones adding up to it.
function knight_pace_take(_over, _depth, _s)
{
    var _k0 = 0.35;
    var _km = 0.05;
    _s = max(1, _s);
    _depth = max(0, _depth);
    var _dc = _s * ln(_k0 / _km);
    if (_depth >= _dc)
        return _km * _over;
    var _e = exp(_depth / _s);
    var _o1 = (_s / _k0) * ((_k0 / _km) - _e);
    if (_over <= _o1)
        return (_s * ln(_e + ((_k0 * _over) / _s))) - _depth;
    return (_dc - _depth) + (_km * (_over - _o1));
}

// a hit of _d on a knight at _hp with a soft line at _line (scale _s): full damage down to the line, the rest through
// knight_pace_take; always at least 1
function knight_pace_soft(_hp, _d, _line, _s)
{
    var _free = max(0, _hp - _line);
    if (_d <= _free)
        return _d;
    var _start = _hp - _free;
    return _free + max(1, ceil(knight_pace_take(_d - _free, _line - _start, _s)));
}

// called with every hit on the knight (scr_damage_enemy and the auto-attack); returns the damage to deal. The fight stats count
// what got through, for whoever dealt it.
function knight_dmg_filter(_t, _d)
{
    var _o = knight_dmg_filter_raw(_t, _d);
    _o = knight_lu_dmg_cap(_t, _o);
    knight_stats_dealt(_o);
    return _o;
}

// Tag Team / Attack Remix: a knight whose partner still stands (or any Remix knight before the finale) never drops to 0 HP - a
// knight at 0 counts as beaten for the whole battle. Its ending (after its Roaring) knocks it out instead (knight_lu_end_ok).
function knight_lu_dmg_cap(_t, _d)
{
    if (_d <= 0 || !knight_lu_ready() || _t != 0)
        return _d;
    var _lu = global.knight_lu;
    var _last = (_lu.kind == "tag") ? (knight_lu_next_alive(_lu.act) < 0) : _lu.finale;
    if (_last)
        return _d;
    return max(0, min(_d, ceil(global.monsterhp[0]) - 1));
}

function knight_dmg_filter_raw(_t, _d)
{
    _d = knight_scale_dealt(_d);
    if (_d <= 0 || !knight_active())
        return _d;
    // build 43: the online Knight takes every hit in full (it is full again every turn and never falls)
    if (knight_lu_kind_of(global.krun.cfg) == "online")
        return _d;
    var _r = global.krun;
    if (_r.state != "battle" || !i_ex(obj_knight_enemy))
        return _d;
    var _e = instance_find(obj_knight_enemy, 0);
    var _reg = knight_reg(knight_cur_knight());
    // Supercharged Knight: nothing gets through while it is phasing (UNLEASH first). The fight's own FIGHT and Rude Buster
    // code already checks this; the hub's spells (X-Slash, FireShock, ...) did not.
    if (_reg.key == "elec" && variable_instance_exists(_e, "phasing") && _e.phasing)
        return 0;
    var _roared = knight_roared();
    // Violet Knight Side B: after the Roaring the fight ends with the finisher (Kris's X-Slash, or the Kris-less finisher).
    // Hits still show their damage, but the Knight stays at the mod's own 8% floor (applied here first, as the mod does every
    // frame) and a hit never takes its last HP, so it cannot get the plain ending instead.
    if (_reg.key == "violet" && _roared && variable_instance_exists(_e, "v_sideb") && _e.v_sideb)
    {
        if (_t >= 0 && _t <= 2 && global.monstermaxhp[_t] > 0)
        {
            var _keep = global.monstermaxhp[_t] * 0.08;
            if (global.monsterhp[_t] < _keep)
                global.monsterhp[_t] = _keep;
            return max(0, min(_d, ceil(global.monsterhp[_t]) - 1));
        }
        return 0;
    }
    // REPEAT practice: the knight cannot fall (its HP is refilled every turn anyway)
    if (knight_pmode(_r.cfg) == 2 && _t >= 0 && _t <= 2)
        return min(_d, max(0, ceil(global.monsterhp[_t]) - 1));
    var _remix = knight_lu_ready() && global.knight_lu.kind == "remix";
    if (_r.practice || (_reg.joke && !_remix) || _roared)
        return _d;
    if (_t < 0 || _t > 2 || global.monstermaxhp[_t] <= 0)
        return _d;
    // a lineup paces each knight by its own turns (Tag Team) or the whole remix by all of them
    var _p = _remix ? knight_lu_remix_pace() : knight_pace_now(knight_cur_knight());
    if (_p.tmin <= 0)
        return _d;
    var _max = global.monstermaxhp[_t];
    var _hp = global.monsterhp[_t];
    var _done = knight_lu_ready() ? knight_lu_turns_now() : _r.eturns;
    var _gate = floor(_max * _p.gate);
    if (_done > _p.tmin && _hp > _gate)
        _d = ceil(_d * min(2, 1 + (0.12 * (_done - _p.tmin))));
    if (_done < _p.tmin)
    {
        // schedule line for the end of this player turn; the further it still is above the gate, the softer the slowdown
        var _line = floor(_max * (1 - ((1 - _p.gate) * ((_done + 1) / _p.tmin))));
        _d = knight_pace_soft(_hp, _d, _line, 0.25 * max(0, _line - _gate));
    }
    // the knight cannot fall before its Roaring: its last 5% counts less, and a hit always leaves it at least 1 HP
    var _low = floor(_max * 0.05);
    if ((_hp - _d) < _low)
        _d = knight_pace_soft(_hp, _d, _low, 0.25 * _low);
    if (_hp <= 1)
        return 0;
    return clamp(_d, 1, _hp - 1);
}

// ---------- per-fight state ----------
function knight_ch_reset(_r)
{
    _r.eturns = 0;
    _r.mnprev = -1;
    _r.thprev = [0, 0, 0, 0, 0, 0];
    _r.thbase = [0, 0, 0, 0, 0, 0];
    _r.thhit = [false, false, false, false, false, false];
    _r.dark_a = 0;
    _r.tlimit = 0;
    _r.started = false;
    knight_wr_reset(_r);
}

// Time limit: the knight's attack list plus 10 turns (Side B uses its own list)
function knight_turn_limit(_k, _sideb)
{
    var _p = knight_reg(_k).pace;
    var _t = (_sideb && _p.tmin_b > 0) ? _p.tmin_b : _p.tmin;
    if (_t <= 0)
        _t = 20;
    return _t + 10;
}

// TIME LIMIT of Tag Team (both attack lists + 10) and Attack Remix (its pacing + 16); -1 for the other fights
function knight_lu_turn_limit(_c)
{
    var _kind = knight_lu_kind_of(_c);
    if (_kind == "tag")
        return knight_turn_limit(_c.knight, false) + knight_turn_limit(_c.knight2, false) - 10;
    if (_kind == "remix")
        return knight_lu_remix_pace().tmin + 16;
    return -1;
}

// battle start (state "arena" -> "battle")
function knight_ch_begin(_r)
{
    knight_ch_reset(_r);
    if (variable_global_exists("mnfight"))
        _r.mnprev = global.mnfight;
    knight_ch_baseline(_r);
    for (var _i = 1; _i <= 5; _i++)
        _r.thbase[_i] = global.maxhp[_i];
    knight_wr_setup(_r);
    knight_dbl_clear();
}

// once the knight is there (its Side B flag is known): turn limit and the battle-start banner
function knight_ch_start(_r)
{
    if (_r.started)
        return 0;
    _r.started = true;
    var _tag = "";
    if (_r.cfg.c_twin)
        _tag = "A SECOND KNIGHT APPEARED!";
    if (_r.cfg.c_time)
    {
        _r.tlimit = knight_turn_limit(knight_cur_knight(), knight_side_b());
        var _lt = knight_lu_turn_limit(_r.cfg);
        if (_lt > 0)
            _r.tlimit = _lt;
        _tag += ((_tag == "") ? "" : "  ") + "WIN WITHIN " + string(_r.tlimit) + " TURNS!";
    }
    if (_tag != "")
    {
        _r.reveal = (_r.reveal == "" || _r.reveal_t >= 150) ? _tag : (_r.reveal + "  " + _tag);
        _r.reveal_t = 0;
    }
}

function knight_ch_baseline(_r)
{
    for (var _i = 1; _i <= 5; _i++)
        _r.thprev[_i] = global.hp[_i];
}

// every battle frame, before the damage sample. Returns true when the fight was just lost to a rule.
function knight_ch_tick(_r)
{
    var _c = _r.cfg;
    if (!_r.started && i_ex(obj_knight_enemy))
        knight_ch_start(_r);
    // enemy turns
    if (variable_global_exists("mnfight"))
    {
        var _mn = global.mnfight;
        if (_mn == 2 && _r.mnprev != 2)
        {
            _r.eturns++;
            knight_lu_count_turn();
            knight_stats_turn_begin();
            if (kfo_run_on())
                kfo_turn_begin();
            if (_c.c_time && _r.tlimit > 0 && _r.eturns > _r.tlimit && !knight_roared())
            {
                knight_ch_fail(_r, "time");
                return true;
            }
        }
        _r.mnprev = _mn;
    }
    // Thorns: a hit also takes 30% of the HP it removed off that member's max HP (never below a third of it). Only HP lost to a
    // hit counts (knight_scale_taken marks the member): the ThornRing's own drain and other non-hit losses never wear max HP down
    // (they did up to build 36: ring drain -> lower max HP -> lower ring threshold -> more drain, all the way to the floor).
    // Thorn Knight already does this itself, so the rule leaves that fight alone.
    if (_c.c_thorns && knight_reg(knight_cur_knight()).key != "thorn")
    {
        for (var _i = 0; _i < 3; _i++)
        {
            var _ch = _r.party[_i];
            if (_ch < 1 || _ch > 5)
                continue;
            var _prev = _r.thprev[_ch];
            var _cur = global.hp[_ch];
            if (_r.thhit[_ch] && _cur < _prev && _prev > 0)
            {
                var _cut = max(1, ceil((_prev - max(_cur, 0)) * 0.3));
                var _min = max(1, ceil(_r.thbase[_ch] / 3));
                global.maxhp[_ch] = max(_min, global.maxhp[_ch] - _cut);
                if (global.hp[_ch] > global.maxhp[_ch])
                    global.hp[_ch] = global.maxhp[_ch];
            }
            _r.thprev[_ch] = global.hp[_ch];
        }
    }
    for (var _i = 0; _i <= 5; _i++)
        _r.thhit[_i] = false;
    // Twin Knight: the second knight appears with the first
    if (_c.c_twin && i_ex(obj_knight_enemy) && !instance_exists(obj_knight_twin))
    {
        var _e = instance_find(obj_knight_enemy, 0);
        instance_create_depth(_e.x - 64, _e.y - 40, _e.depth + 1, obj_knight_twin);
    }
    knight_speed_apply(_r);
    return false;
}

// a rule ended the fight (Time limit): same path as a failed No-Hit
function knight_ch_fail(_r, _why)
{
    if (_r.failed)
        return 0;
    _r.failed = true;
    _r.state = "failed";
    _r.result = _why;
    knight_dmg_sample(_r);
    if (_r.mode == 0)
        knight_fight_commit(_why);
    else
        knight_rush_finish(_why);
}

// ---------- Hyper speed ----------
// the game runs at 38 steps a second instead of 30 while the battle is on (everything moves 25% faster); battle time in the
// records stays in real seconds
function knight_speed_want(_r)
{
    if (knight_ff_on())
        return 120;
    if (is_struct(_r) && _r.state == "battle" && _r.cfg.c_speed && !global.knight_frozen)
        return 38;
    return 30;
}

function knight_speed_apply(_r)
{
    var _s = knight_speed_want(_r);
    if (room_speed != _s && (room_speed == 30 || room_speed == 38 || room_speed == 120))
        room_speed = _s;
}

function knight_speed_reset()
{
    if (room_speed == 38 || room_speed == 120)
        room_speed = 30;
}

// battle time: real seconds (Hyper speed keeps real time); fast-forward counts game time, so holding TAB through talk never
// makes a record faster or slower
function knight_frame_step()
{
    if (room_speed == 120)
        return 1;
    return 30 / max(1, room_speed);
}

// ---------- overlay (drawn by the hub controller above everything) ----------
function knight_ch_draw_overlay()
{
    if (!knight_active())
        return 0;
    var _r = global.krun;
    var _want = 0;
    if (_r.cfg.c_dark && _r.state == "battle" && i_ex(obj_heart) && variable_global_exists("mnfight") && global.mnfight == 2)
        _want = 0.88;
    _r.dark_a = (_r.dark_a < _want) ? min(_want, _r.dark_a + 0.06) : max(_want, _r.dark_a - 0.06);
    if (_r.dark_a > 0.01 && i_ex(obj_heart))
        knight_dark_draw(_r.dark_a);
}

// Darkness: everything above the party panel goes dark except a soft circle of light around the SOUL
function knight_dark_ray(_hx, _hy, _dx, _dy, _x0, _y0, _x1, _y1)
{
    var _t = 100000;
    if (_dx > 0.0001)
        _t = min(_t, (_x1 - _hx) / _dx);
    if (_dx < -0.0001)
        _t = min(_t, (_x0 - _hx) / _dx);
    if (_dy > 0.0001)
        _t = min(_t, (_y1 - _hy) / _dy);
    if (_dy < -0.0001)
        _t = min(_t, (_y0 - _hy) / _dy);
    return max(_t, 0);
}

function knight_dark_draw(_a)
{
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
    var _r0 = 38;
    var _r1 = 70;
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
}

// ---------- Twin Knight ----------
// A second knight stands behind the first. In every knight turn it adds one pattern of its own on top of the knight's attack
// (falling stars, swords from the sides, star bursts or dashing swords) in the fight's own bullet art, appearing as a faint
// phantom where it attacks from. Its bullets hit like the knight's (a bit softer), can be grazed for TP and leave at the end
// of the turn. It holds back during the Roaring and the finale.
function knight_twin_art()
{
    var _reg = knight_reg(knight_cur_knight());
    var _a = { fig: asset_get_index(_reg.portrait), star: asset_get_index(_reg.twin_star), small: asset_get_index(_reg.twin_small), sword: asset_get_index(_reg.twin_sword), blend: _reg.twin_blend };
    if (!sprite_exists(_a.fig))
        _a.fig = spr_roaringknight_idle;
    if (!sprite_exists(_a.star))
        _a.star = spr_knight_bullet_star;
    if (!sprite_exists(_a.small))
        _a.small = spr_smallbullet;
    if (!sprite_exists(_a.sword))
        _a.sword = spr_roaringknight_sword_ol;
    return _a;
}

function knight_twin_init()
{
    art = knight_twin_art();
    siner = 0;
    t = 0;
    pat = -1;
    lastpat = -1;
    active = false;
    turnno = 0;
    lurk_a = 0;
    ph_x = x;
    ph_y = y;
    ph_a = 0;
    visible = true;
    // build 50: the figure itself goes round the box to each attack's spot and plays the attack's own animation (looks only:
    // where the bullets go is decided as before)
    fx = x;
    fy = y;
    fgx = x;
    fgy = y;
    fspr = art.fig;
    ft = 0;
    fgo = 0;
    fface = 1;
}

// a battle sprite of the twin's knight: its own version (the portrait's suffix, e.g. __v1) when the game has one
function knight_twin_spr(_base)
{
    var _suf = string_replace(sprite_get_name(art.fig), "spr_roaringknight_idle", "");
    if (_suf != "" && _suf != sprite_get_name(art.fig))
    {
        var _v = asset_get_index(_base + _suf);
        if (_v >= 0 && sprite_exists(_v))
            return _v;
    }
    var _b = asset_get_index(_base);
    return (_b >= 0 && sprite_exists(_b)) ? _b : art.fig;
}

function knight_twin_hold()
{
    if (!i_ex(obj_knight_enemy))
        return true;
    var _e = instance_find(obj_knight_enemy, 0);
    if (i_ex(obj_knight_roaring2) || knight_roared())
        return true;
    if (variable_instance_exists(_e, "phase") && _e.phase == 4)
        return true;
    if (global.monsterhp[0] <= 0)
        return true;
    return false;
}

function knight_twin_pick()
{
    // build 50: never the pattern it just did, nor the one before that (it mixes all four up)
    if (!variable_instance_exists(id, "lastpat2"))
        lastpat2 = -1;
    var _c = [];
    for (var _i = 0; _i < 4; _i++)
    {
        if (_i != lastpat && _i != lastpat2)
            array_push(_c, _i);
    }
    var _p = _c[kbr_irandom(array_length(_c) - 1)];
    lastpat2 = lastpat;
    lastpat = _p;
    return _p;
}

function knight_twin_step()
{
    if (!knight_active() || !i_ex(obj_knight_enemy) || global.krun.state != "battle")
    {
        // the battle is over: fade out and go
        lurk_a = max(0, lurk_a - 0.05);
        ph_a = 0;
        kbr_sa_twin_end(false);
        if (!knight_active() || lurk_a <= 0)
            instance_destroy();
        return 0;
    }
    var _e = instance_find(obj_knight_enemy, 0);
    knight_twin_tracked();
    knight_twin_tel_step();
    siner++;
    x = lerp(x, _e.x - 64, 0.12);
    y = lerp(y, _e.y - 40, 0.12);
    depth = _e.depth + 1;
    var _go = (variable_global_exists("mnfight") && global.mnfight == 2 && i_ex(obj_heart) && global.turntimer > 0 && !knight_twin_hold());
    if (_go)
    {
        if (!active)
        {
            active = true;
            t = 0;
            turnno++;
            // build 45: online the Twin Knight's count comes from the shared timeline (the same in every game)
            if (kbr_on())
                turnno = kbr_twin_turn();
            pat = knight_twin_pick();
        }
        t++;
        // build 50: it changes its attack during the Knight's turn (every 2.5 - 3.5 seconds, a short breath between)
        if (t > 31 + round(lerp(105, 75, min(1, turnno / 12))))
        {
            pat = knight_twin_pick();
            t = 11;
        }
        if (t > 30 && global.turntimer > 24)
            knight_twin_fire();
    }
    else
    {
        // build 50: its real attacks end with the Knight's turn
        if (active || global.turntimer < 1)
            kbr_sa_twin_end(false);
        tw_tel = [];
        active = false;
    }
    var _la = active ? 0.3 : 0.6;
    lurk_a = (lurk_a < _la) ? min(_la, lurk_a + 0.04) : max(_la, lurk_a - 0.04);
    ph_a = max(0, ph_a - 0.03);
    // build 50: the figure - at its attack spot while it attacks, warping back beside the knight between attacks
    if (!variable_instance_exists(id, "fgo"))
        knight_twin_fig_init();
    ft++;
    if (fgo > 0)
        fgo--;
    if ((!active || fgo <= 0) && fspr != art.fig)
    {
        knight_twin_warp(fx, fy, 1);
        fspr = art.fig;
        fface = 1;
        fx = x;
        fy = y;
        knight_twin_warp(fx, fy, 0);
    }
    if (fspr == art.fig)
    {
        fx = x;
        fy = y;
    }
    // the Knight's own afterimage while it attacks (as its attack managers make it: every 4 frames, 0.6, drifting right)
    if (fspr != art.fig && (ft mod 4) == 0)
    {
        var _ai = instance_create_depth(fx, fy, depth + 1, obj_afterimage);
        _ai.sprite_index = fspr;
        _ai.image_index = min(max(1, sprite_get_number(fspr)) - 1, ft div 3);
        _ai.image_xscale = 2 * fface;
        _ai.image_yscale = 2;
        _ai.image_blend = art.blend;
        _ai.image_alpha = 0.3;
        _ai.fadeSpeed = 0.04;
        _ai.hspeed = 4 * fface;
        _ai.kbrtwin = 1;
        knight_twin_place(_ai, fx, fy, fspr, fface);
    }
    // the flurry: its swing follows its windup
    if (fspr == knight_twin_spr("spr_roaringknight_flurry_prepare") && ft > 12)
    {
        fspr = knight_twin_spr("spr_roaringknight_flurry");
        ft = 0;
    }
}

// a sprite drawn 2x, its middle on the point (the knights' battle sprites have their origins in different places)
function knight_twin_place(_i, _x, _y, _spr, _face)
{
    var _cx = ((sprite_get_width(_spr) / 2) - sprite_get_xoffset(_spr)) * 2 * _face;
    var _cy = ((sprite_get_height(_spr) / 2) - sprite_get_yoffset(_spr)) * 2;
    _i.x = _x - _cx;
    _i.y = _y - _cy;
    return 1;
}

// a twin bullet: waits _wait frames (faint, harmless) then flies ldir at lspd
// build 50: one of the Knight's own attack objects for the Twin Knight (kept apart from the Knight's managers online)
function knight_twin_real(_x, _y, _obj)
{
    if (!variable_instance_exists(id, "tw_list"))
        tw_list = [];
    var _G = kbr_sa_twin_group();
    var _i = kbr_sa_mk(_G, _x, _y, _obj);
    with (_i)
        image_blend = merge_color(image_blend, other.art.blend, 0.35);
    return _i;
}

// a star the twin launches itself: after _f frames (or once it falls to _y), it stops and bursts (its con 1, as the
// Knight's pointing cone does it)
function knight_twin_track(_i, _f, _y)
{
    if (!variable_instance_exists(id, "tw_list"))
        tw_list = [];
    array_push(tw_list, { i: _i, f: _f, y: _y, t: 0 });
    return 1;
}

// a star's telegraph: kind 0 (rain: falls from _y0 at _sp to stop at _y) or 2 (burst: at _x, _y, drifts _dir at _sp), shown
// for _d frames before the star is made
function knight_twin_tel(_k, _x, _y, _d, _y0, _sp, _dir)
{
    if (!variable_instance_exists(id, "tw_tel"))
        tw_tel = [];
    array_push(tw_tel, { k: _k, x: _x, y: _y, d: _d, t: 0, y0: _y0, sp: _sp, dir: _dir });
    snd_play_x(snd_knight_drawpower, 0.35, 1.6);
    return 1;
}

function knight_twin_tel_step()
{
    if (!variable_instance_exists(id, "tw_tel"))
        return 0;
    for (var _i = array_length(tw_tel) - 1; _i >= 0; _i--)
    {
        var _e = tw_tel[_i];
        _e.t++;
        if (_e.t < _e.d)
            continue;
        array_delete(tw_tel, _i, 1);
        if (!active || !instance_exists(obj_heart))
            continue;
        if (_e.k == 0)
        {
            var _s0 = knight_twin_real(_e.x, _e.y0, obj_knight_pointing_star);
            _s0.direction = 270;
            _s0.speed = _e.sp;
            _s0.growspeed = 0.014;
            // (it stops once it is down there, or when it should be by its speed - some knights' stars steer themselves)
            knight_twin_track(_s0, ceil(max(10, (_e.y - _e.y0) / max(1, _e.sp))) + 4, _e.y);
        }
        else
        {
            var _s2 = knight_twin_real(_e.x, _e.y, obj_knight_pointing_star);
            _s2.direction = _e.dir;
            _s2.speed = _e.sp;
            knight_twin_track(_s2, 30, -1);
        }
    }
    return 1;
}

function knight_twin_tel_draw()
{
    if (!variable_instance_exists(id, "tw_tel"))
        return 0;
    var _col = merge_color(c_red, art.blend, 0.3);
    for (var _i = 0; _i < array_length(tw_tel); _i++)
    {
        var _e = tw_tel[_i];
        var _f = clamp(_e.t / _e.d, 0, 1);
        var _fl = ((_e.t div 3) mod 2) == 0;
        draw_set_color(_fl ? c_white : _col);
        if (_e.k == 0)
        {
            draw_set_alpha(0.25 + (0.45 * _f));
            draw_line_width(_e.x, _e.y0, _e.x, _e.y, 1 + (2 * _f));
            draw_set_alpha(0.5 + (0.5 * _f));
            draw_circle(_e.x, _e.y, 26 - (12 * _f), true);
            draw_circle(_e.x, _e.y, 27 - (12 * _f), true);
            draw_sprite_ext(art.star, 0, _e.x, _e.y0 + 6, 0.35 + (0.35 * _f), 0.35 + (0.35 * _f), 0, art.blend, 0.3 + (0.5 * _f));
        }
        else
        {
            draw_set_alpha(0.5 + (0.5 * _f));
            draw_circle(_e.x, _e.y, 48 - (34 * _f), true);
            draw_circle(_e.x, _e.y, 49 - (34 * _f), true);
            draw_set_alpha(0.25 + (0.4 * _f));
            draw_line_width(_e.x, _e.y, _e.x + lengthdir_x(60, _e.dir), _e.y + lengthdir_y(60, _e.dir), 1 + (2 * _f));
            draw_sprite_ext(art.star, 0, _e.x, _e.y, 0.3 + (0.5 * _f), 0.3 + (0.5 * _f), 0, art.blend, 0.25 + (0.5 * _f));
        }
    }
    draw_set_alpha(1);
    draw_set_color(c_white);
    return 1;
}

function knight_twin_tracked()
{
    if (!variable_instance_exists(id, "tw_list"))
        return 0;
    for (var _k = array_length(tw_list) - 1; _k >= 0; _k--)
    {
        var _e = tw_list[_k];
        _e.t++;
        if (!instance_exists(_e.i))
        {
            array_delete(tw_list, _k, 1);
            continue;
        }
        if (_e.t >= _e.f || (_e.y > -1 && _e.i.y >= _e.y))
        {
            with (_e.i)
            {
                if (con == 0)
                    con = 1;
            }
            array_delete(tw_list, _k, 1);
        }
    }
    return 1;
}

function knight_twin_shot(_x, _y, _spr, _wait, _ldir, _lspd)
{
    var _b = instance_create_depth(_x, _y, -10, obj_knight_twin_bullet);
    _b.sprite_index = _spr;
    _b.image_blend = art.blend;
    _b.wait = _wait;
    _b.ldir = _ldir;
    _b.lspd = _lspd;
    _b.image_angle = _ldir + _b.angoff;
    if (_wait <= 0)
    {
        _b.direction = _ldir;
        _b.speed = _lspd;
        _b.active = 1;
    }
    return _b;
}

function knight_twin_phantom(_x, _y)
{
    // the idle figure at 1x, centred on the point (content box 24..92 x 31..96, origin 7,23)
    ph_x = _x - 51;
    ph_y = _y - 41;
    ph_a = 0.75;
    // build 50: the twin goes there itself the way the Knight moves in its fight - it warps out where it was and warps in
    // there (obj_knight_warp: the Knight's warp frames and snd_knight_teleport) - and attacks with the sprite the Knight
    // uses for that attack (stars: its pointing pose, side swords: the flurry wind-up and swing, falling swords: its sword
    // raise), with the pose's own sound (the stars' snd_knight_drawpower)
    if (!variable_instance_exists(id, "fgo"))
        knight_twin_fig_init();
    var _moved = point_distance(fx, fy, _x, _y) > 24;
    if (_moved)
        knight_twin_warp(fx, fy, 1);
    fx = _x;
    fy = _y;
    fgx = _x;
    fgy = _y;
    ft = 0;
    fgo = 60;
    switch (pat)
    {
        case 0:
        case 2:
            fspr = knight_twin_spr("spr_roaringknight_point_ol");
            snd_play_x(snd_knight_drawpower, 0.8, 1.3);
            break;
        case 1: fspr = knight_twin_spr("spr_roaringknight_flurry_prepare"); break;
        case 3: fspr = knight_twin_spr("spr_roaringknight_attack_ol"); break;
        default: fspr = art.fig; break;
    }
    if (instance_exists(obj_heart))
    {
        var _hh = instance_find(obj_heart, 0);
        fface = (_x > _hh.x) ? 1 : -1;
    }
    if (_moved)
        knight_twin_warp(fx, fy, 0);
}

function knight_twin_fig_init()
{
    fx = x;
    fy = y;
    fgx = x;
    fgy = y;
    fspr = art.fig;
    ft = 0;
    fgo = 0;
    fface = 1;
    return 0;
}

// the Knight's own warp at the figure (0: in, 1: out), its sprite placed like the figure's
function knight_twin_warp(_x, _y, _out)
{
    var _w = instance_create_depth(_x, _y, depth - 1, obj_knight_warp);
    _w.kbrtwin = 1;
    with (_w)
    {
        image_blend = other.art.blend;
        image_alpha = 0.6;
        if (_out)
            event_user(1);
        else
            event_user(0);
    }
    knight_twin_place(_w, _x, _y, _w.sprite_index, 1);
    return _w;
}

function knight_twin_fire()
{
    var _h = instance_find(obj_heart, 0);
    var _hx = (_h.bbox_left + _h.bbox_right) / 2;
    var _hy = (_h.bbox_top + _h.bbox_bottom) / 2;
    var xx = knight_cam_x();
    var yy = knight_cam_y();
    var _lv = min(1, turnno / 12);
    var _tt = t - 31;
    switch (pat)
    {
        case 0:
            // build 50: STAR RAIN with the Knight's own stars - they fall from the top around the SOUL, growing, stop near
            // its height, then burst into starchildren that fly out (obj_knight_pointing_star)
            if (_tt == 0)
                knight_twin_phantom(_hx, yy + 40);
            if ((_tt mod round(lerp(30, 22, _lv))) == 0)
            {
                // build 50: telegraphed - a line down the star's column and a ring where it will stop show first (24 frames),
                // then the star falls (knight_twin_tel_step makes it)
                var _sx = clamp(_hx + kbr_random_range(-110, 110), xx + 30, xx + 610);
                var _ty0 = _hy + kbr_random_range(-50, 10);
                knight_twin_tel(0, _sx, _ty0, 24, yy + 10, lerp(3.4, 4.4, _lv), 270);
            }
            break;
        case 1:
            // swords from the sides at the SOUL's height, shown for a moment before they fly
            if ((_tt mod round(lerp(36, 26, _lv))) == 0)
            {
                var _sd = kbr_choose(-1, 1);
                var _x1 = clamp(_hx + (_sd * 250), xx + 10, xx + 630);
                var _y1 = clamp(_hy + kbr_random_range(-36, 36), yy + 10, yy + 300);
                knight_twin_phantom(_x1, _y1);
                // build 50: the Knight's own tracking sword on that side of the SOUL: it follows the SOUL's height while it
                // fades in, flashes, then slashes straight across (obj_tracking_sword1, its own sounds)
                var _d1 = (_sd > 0) ? 0 : 180;
                var _b1 = knight_twin_real(_hx + lengthdir_x(120, _d1), _hy, obj_tracking_sword1);
                _b1.direction = _d1;
                _b1.image_angle = _d1 + 180;
                _b1.variant = 0;
            }
            break;
        case 2:
            // build 50: STAR BURST with the Knight's own stars - the twin points, a star grows where it points and drifts at
            // the SOUL, stops, then breaks into its starchildren, which are thrown out (obj_knight_pointing_star ->
            // obj_knight_pointing_starchild), as in the Knight's Stars attack
            if ((_tt mod round(lerp(44, 34, _lv))) == 0)
            {
                var _ga = kbr_random(360);
                var _px = clamp(_hx + lengthdir_x(130, _ga), xx + 30, xx + 610);
                var _py = clamp(_hy + lengthdir_y(130, _ga), yy + 30, yy + 300);
                knight_twin_phantom(_px, _py);
                // build 50: telegraphed - a ring closes in on the spot with the star faint inside it and a line toward
                // where it will drift (24 frames), then the star appears (knight_twin_tel_step)
                knight_twin_tel(2, _px, _py, 24, 0, 2, point_direction(_px, _py, _hx, _hy));
            }
            break;
        case 3:
            // dashing swords: a sword turns to face the SOUL, then dashes at where it was
            if ((_tt mod round(lerp(32, 24, _lv))) == 0)
            {
                var _gb = kbr_random(360);
                var _qx = clamp(_hx + lengthdir_x(175, _gb), xx + 20, xx + 620);
                var _qy = clamp(_hy + lengthdir_y(175, _gb), yy + 20, yy + 300);
                // build 50: the Knight's own falling sword (Kaizo's Vortex / Frenzy): it flips in above the SOUL, rises a
                // little, then dives at it (obj_fallingsword__v1, with its own whoosh)
                var _fx3 = clamp(_hx + kbr_random_range(-48, 48), xx + 30, xx + 610);
                var _fy3 = max(yy + 20, _hy - 150 + kbr_random_range(0, 30));
                knight_twin_phantom(_fx3, _fy3 - 40);
                var _b3 = knight_twin_real(_fx3, _fy3, obj_fallingsword__v1);
                with (_b3)
                {
                    image_angle = point_direction(x, y, _hx, _hy);
                    direction = image_angle;
                    speed = -6;
                    speed_gain = 0.3;
                    image_xscale = 2;
                    scr_lerpvar("image_yscale", 0, -2, 8);
                    scr_script_delayed(scr_lerpvar, 8, "image_yscale", -2, 2, 8);
                    scr_lerpvar("image_angle", image_angle, image_angle + 360, 16, 1, "out");
                    scr_lerpvar("image_alpha", 0, 1, 16, 1, "out");
                    finalsword = true;
                    grazepoints = 30;
                }
            }
            break;
    }
}

function knight_twin_draw()
{
    knight_twin_tel_draw();
    var _fr = siner / 6;
    var _dim = merge_color(art.blend, c_black, 0.35);
    if (!variable_instance_exists(id, "fgo"))
    {
        if (lurk_a > 0.01)
            draw_sprite_ext(art.fig, _fr, x, y + (sin(siner / 20) * 4), 2, 2, 0, _dim, lurk_a);
        return 0;
    }
    // build 50: the twin itself, wherever it is: dim while it waits beside the knight, bright while it attacks
    var _att = (fspr != art.fig);
    // (see-through like the Twin Knight always is: never more than half)
    var _a = _att ? 0.5 : lurk_a;
    if (_a <= 0.01)
        return 0;
    var _n = max(1, sprite_get_number(fspr));
    var _fi = _att ? min(_n - 1, ft div 3) : _fr;
    var _cx = ((sprite_get_width(fspr) / 2) - sprite_get_xoffset(fspr)) * 2 * fface;
    var _cy = ((sprite_get_height(fspr) / 2) - sprite_get_yoffset(fspr)) * 2;
    if (_att)
        draw_sprite_ext(fspr, _fi, fx - _cx, (fy - _cy) + (sin(siner / 20) * 2), 2 * fface, 2, 0, art.blend, _a);
    else
        draw_sprite_ext(fspr, _fi, fx, fy + (sin(siner / 20) * 4), 2, 2, 0, _dim, _a);
}

// bullet object (child of obj_regularbullet): Create / Step
function knight_twin_bullet_init()
{
    damage = 144;
    element = 5;
    target = 4;
    grazepoints = 2;
    wait = 0;
    ldir = 0;
    lspd = 0;
    aim = false;
    spinme = 0;
    tt = 0;
    life = 240;
    active = 0;
    updateimageangle = 0;
    // the sword art points right (0 degrees), so image_angle = direction; round art does not care
    angoff = 0;
    // build 45: an online skill's bullet (kbr = 1) and its damage (kbrd)
    kbr = 0;
    kbrd = 0;
    // build 48: a targeted send - who sent it (its own bullets never hurt the sender) and whose SOUL it goes for
    kbrf = -1;
    kbrt = -1;
    kbrw = 0;
}

function knight_twin_bullet_step()
{
    // build 45: an online skill's bullets (kbr) live through the breath between two attacks
    if (kbr != 0)
    {
        if (!kbr_on() || !i_ex(obj_heart))
        {
            instance_destroy();
            return 0;
        }
    }
    else if (!knight_active() || global.turntimer < 1 || !variable_global_exists("mnfight") || global.mnfight != 2 || !i_ex(obj_heart))
    {
        instance_destroy();
        return 0;
    }
    tt++;
    if (wait > 0)
    {
        wait--;
        active = 0;
        speed = 0;
        image_alpha = ((tt div 3) mod 2) ? 0.7 : 0.35;
        if (aim)
        {
            var _h = instance_find(obj_heart, 0);
            var _ax = (_h.bbox_left + _h.bbox_right) / 2;
            var _ay = (_h.bbox_top + _h.bbox_bottom) / 2;
            // build 48: aimed at its target's SOUL (where this game sees it)
            if (kbr != 0 && kbrt >= 0)
            {
                var _tp = kbr_tg_pos(kbrt);
                if (!is_undefined(_tp))
                {
                    _ax = _tp[0];
                    _ay = _tp[1];
                }
            }
            ldir = point_direction(x, y, _ax, _ay);
            image_angle = ldir + angoff;
        }
        if (wait == 0)
        {
            active = 1;
            image_alpha = 1;
            direction = ldir;
            speed = lspd;
            if (spinme == 0)
                image_angle = ldir + angoff;
        }
    }
    if (spinme != 0)
        image_angle += spinme;
    life--;
    // build 48: the sender's own bullets are only shown (fainter), never a hit for the sender
    if (kbr != 0 && kbrf >= 0 && kbrf == global.kfo.my)
    {
        active = 0;
        image_alpha = min(image_alpha, 0.5);
    }
    // build 49: a send aimed at someone else (only the host's game makes these: the ones at its bots) - not shown, never a
    // hit for this game's SOUL (the bots' own hit test still sees it)
    if (kbr != 0 && kbrt >= 0 && kbrt != global.kfo.my && !(variable_instance_exists(id, "kbrw") && kbrw))
    {
        active = 0;
        visible = false;
    }
    if (life <= 0)
    {
        active = 0;
        image_alpha -= 0.2;
        if (image_alpha <= 0)
            instance_destroy();
    }
}
