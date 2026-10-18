
// ===== Build 50: REAL KNIGHT ATTACKS - what a player's attack skill puts up in the target's game =====
// A skill sent to you is made in your game only (build 49). Since build 50 it is made of the Roaring Knights' own attack
// objects - the tracking sword, the pointing star, the rotating slash, the falling sword, the crescent, the lightning, the
// weird circle, the diagonal diamonds, the splitter's teeth, the fountain - with their own sprites, animations, telegraphs
// and sounds. det_sent.py wraps those objects so a sent one never touches the Knight's own fight (isolation, its own random
// stream, its own variant, no turn-timer change, quieter sounds); this file starts and times the sends ("groups"), adopts
// what they make, tints them in the sender's colour, draws the telegraphs the Knights' managers would draw, and cleans up.
// The host's game still makes the hidden twin-bullet copies for its bots (kbr_skill_land): the bots dodge those.

global.kbr_san = 0;
global.kbr_sa = [];
global.kbr_sa_n = 0;
global.kbr_sa_f = 0;
global.kbr_curx = undefined;
global.kbr_cur = 0;
global.kbr_sndf = {};
global.kbr_sa_surf = -1;
global.kbr_sa_last = undefined;
global.kbr_sa_why = "";

#macro KBR_SENT_GAIN 0.55
#macro KBR_SENT_TINT 0.42

// ---------- the wrappers (det_sent.py puts them into the attack objects' code) ----------
// the send an instance belongs to (0: the Knight's own)
function kbr_gx_of(_i)
{
    if (is_struct(_i) || is_undefined(_i))
        return 0;
    if (!instance_exists(_i))
        return 0;
    return variable_instance_exists(_i, "kbrx") ? _i.kbrx : 0;
}

// inside `with (X) if (kbr_ns())`: self is the X instance, other the code that asked - the same side only
function kbr_ns()
{
    if (global.kbr_san <= 0)
        return true;
    // (the asking instance read from inside it: `other` can be the instance as a struct in newer runners, or one that
    // destroyed itself earlier in its event)
    var _b = 0;
    with (other)
        _b = (variable_instance_exists(id, "kbrx") && kbrx > 0) ? kbrx : 0;
    var _a = (variable_instance_exists(id, "kbrx") && kbrx > 0) ? kbrx : 0;
    return _a == _b;
}

function kbr_inum(_o)
{
    if (global.kbr_san <= 0)
        return instance_number(_o);
    var _g = kbr_gx_of(id);
    var _n = 0;
    with (_o)
    {
        if (kbr_gx_of(id) == _g)
            _n++;
    }
    return _n;
}

function kbr_iex(_o)
{
    if (global.kbr_san <= 0)
        return instance_exists(_o);
    return kbr_inum(_o) > 0;
}

function kbr_ifind(_o, _k)
{
    if (global.kbr_san <= 0)
        return instance_find(_o, _k);
    var _g = kbr_gx_of(id);
    var _r = noone;
    var _c = 0;
    with (_o)
    {
        if (_r == noone && kbr_gx_of(id) == _g)
        {
            if (_c == _k)
                _r = id;
            _c++;
        }
    }
    return _r;
}

// 1 for the Knight's own code, 0 for a sent instance (it never changes the Knight's turn timer)
function kbr_mine()
{
    if (global.kbr_san <= 0)
        return 1;
    return (kbr_gx_of(id) == 0) ? 1 : 0;
}

// the turn timer as a sent instance reads it: always a running turn
function kbr_tt()
{
    if (global.kbr_san > 0 && kbr_gx_of(id) != 0 && !variable_instance_exists(id, "kbrtw"))
        return max(global.turntimer, 300);
    return global.turntimer;
}

// the knight variant: a sent instance keeps the one of the knight it came from
function kbr_kv()
{
    if (global.kbr_san > 0 && variable_instance_exists(id, "kbrkv"))
        return kbrkv;
    return global.knight_variant;
}

function kbr_sent_me()
{
    return global.kbr_san > 0 && variable_instance_exists(id, "kbrx") && kbrx > 0 && variable_instance_exists(id, "kbr") && kbr != 0;
}

// sounds: a send's are quieter, the same sound starts at most once every 4 frames (eight senders are not deafening), a send
// never stops or bends the Knight's own sounds and never loops
function kbr_snd_gate(_s)
{
    var _k = string(_s);
    var _l = variable_struct_exists(global.kbr_sndf, _k) ? variable_struct_get(global.kbr_sndf, _k) : -100;
    if (global.kbr_sa_f - _l < 4)
        return false;
    variable_struct_set(global.kbr_sndf, _k, global.kbr_sa_f);
    return true;
}

function kbr_snd_play(_s)
{
    var _v = (argument_count > 1) ? argument[1] : 1;
    var _p = (argument_count > 2) ? argument[2] : 1;
    if (!kbr_sent_me())
        return snd_play(_s, _v, _p);
    if (!kbr_snd_gate(_s))
        return -1;
    return snd_play(_s, _v * KBR_SENT_GAIN, _p);
}

function kbr_snd_play_x(_s, _v, _p)
{
    if (!kbr_sent_me())
        return snd_play_x(_s, _v, _p);
    if (!kbr_snd_gate(_s))
        return -1;
    return snd_play_x(_s, _v * KBR_SENT_GAIN, _p);
}

function kbr_snd_stop(_s)
{
    if (kbr_sent_me())
        return 0;
    snd_stop(_s);
    return 0;
}

function kbr_snd_pitch(_s, _p)
{
    if (kbr_sent_me() && (!is_numeric(_s) || _s < 0))
        return 0;
    snd_pitch(_s, _p);
    return 0;
}

function kbr_snd_volume(_s, _v, _t)
{
    if (kbr_sent_me())
    {
        if (!is_numeric(_s) || _s < 0)
            return 0;
        _v *= KBR_SENT_GAIN;
    }
    snd_volume(_s, _v, _t);
    return 0;
}

function kbr_snd_loop(_s)
{
    if (kbr_sent_me())
        return -1;
    return snd_loop(_s);
}

// the colours the attack code asks for: the sender's colour mixed in for a sent instance
function kbr_swordcolor()
{
    var _c = (argument_count > 0) ? get_swordcolor(argument[0]) : get_swordcolor();
    if (kbr_sent_me() && variable_instance_exists(id, "kbrcol"))
        return merge_color(_c, kbrcol, KBR_SENT_TINT);
    return _c;
}

function kbr_pcolor()
{
    var _c = pcolor();
    if (kbr_sent_me() && variable_instance_exists(id, "kbrcol"))
        return merge_color(_c, kbrcol, KBR_SENT_TINT);
    return _c;
}

// ---------- adoption: the first line of every reachable attack object's Create ----------
function kbr_ev_cr()
{
    if (variable_instance_exists(id, "kbrc"))
        return 0;
    kbrc = 1;
    if (object_index == obj_knight_twin_bullet)
        return 0;
    var _G = undefined;
    // the maker: the send being started (the runner says so), else `other` - the instance that called instance_create (the
    // runner this game uses) - else, should a runner not tell, the side whose event is running (kbr_ev_in)
    if (is_struct(global.kbr_curx))
        _G = global.kbr_curx;
    else
    {
        var _oid = noone;
        with (other)
            _oid = id;
        var _known = (_oid != noone && _oid != id && instance_exists(_oid));
        var _gx = _known ? kbr_gx_of(_oid) : global.kbr_cur;
        if (_gx > 0)
            _G = kbr_sa_find(_gx);
    }
    if (is_undefined(_G) || _G.dead)
    {
        global.kbr_cur = 0;
        return 0;
    }
    kbr_sa_tag(_G);
    global.kbr_cur = _G.gx;
    return 1;
}

// the first line of the attack objects' other events: whose side is running now
function kbr_ev_in()
{
    global.kbr_cur = (variable_instance_exists(id, "kbrx") && kbrx > 0) ? kbrx : 0;
    return 0;
}

// self joins send _G: its variant, damage, sender, target, colour, its own random stream (never the shared one)
function kbr_sa_tag(_G)
{
    kbrc = 1;
    kbrx = _G.gx;
    kbrkv = _G.kv;
    kbrg = _G.rg;
    kbrt0 = global.kbr_sa_f;
    _G.made++;
    variable_struct_set(_G.seen, object_get_name(object_index), 1);
    // the Twin Knight's own real attacks: kept apart and with their own variant and random stream, but the Knight's
    // bullets (its damage, no sender, no tint, its sounds)
    if (_G.twin)
    {
        kbrtw = 1;
        return 1;
    }
    kbr = 1;
    kbrd = _G.dmg;
    kbrf = _G.from;
    kbrt = _G.tg;
    kbrkv = _G.kv;
    kbrg = _G.rg;
    kbrcol = _G.col;
    kbrb = -1;
    kbrtb = -1;
    // DRBR 1.0.3: a boss's send (Jevil, Spamton NEO, Gerson, Pink, Flowery): its pictures get the sender's colour drawn over
    // them (kbr_ov_*), not the knights' light mix
    var _ft = kbr_skill_fams();
    kbrov = (_G.sid > 0 && _G.sid < array_length(_ft) && _ft[_G.sid] > KBR_FAM_KNIGHT) ? 1 : 0;
    // (a dark SOUL colour lifted as a name in it is - kfo_col_text - so a send in black or navy stays easy to see)
    kbrovc = kfo_col_text(_G.col);
    return 1;
}

function kbr_sa_find(_gx)
{
    for (var _i = 0; _i < array_length(global.kbr_sa); _i++)
    {
        if (global.kbr_sa[_i].gx == _gx)
            return global.kbr_sa[_i];
    }
    return undefined;
}

// ---------- the items ----------
// the online knight a new item comes from (-1: every match has it). New items are only drawn when their knight is in the
// match's knight pool (MATCH > KNIGHTS).
function kbr_skill_knight(_id)
{
    switch (_id)
    {
        case 17: return 1;
        case 18: return 1;
        case 19: return 2;
        case 20: return 4;
        case 21: return 3;
    }
    return -1;
}

// the base damage of one hit of item _id (as build 49's patterns: the balance does not change)
function kbr_skill_dmg(_id)
{
    switch (_id)
    {
        case 1: return 24;
        case 2: return 20;
        case 3: return 14;
        case 4: return 14;
        case 5: return 14;
        case 6: return 14;
        case 7: return 12;
        case 10: return 32;
        case 17: return 16;
        case 18: return 18;
        case 19: return 14;
        case 20: return 12;
        case 21: return 12;
        // build 52: Jevil's
        case 26: return 14;
        case 27: return 14;
        case 28: return 14;
        case 29: return 16;
        case 30: return 20;
        case 31: return 14;
        // DRBR: Gerson's
        case 32: return 14;
        case 33: return 14;
        case 34: return 18;
        case 35: return 16;
        case 36: return 12;
        case 37: return 22;
        // DRBR: Flowery's (online_flowery53.gml)
        case 38: return 16;
        case 39: return 10;
        case 40: return 14;
        case 41: return 12;
        case 42: return 18;
        case 43: return 16;
        case 44: return 24;
        // DRBR: Spamton NEO's (online_spamton53.gml)
        case 45: return 12;
        case 46: return 14;
        case 47: return 14;
        case 48: return 12;
        case 49: return 18;
        case 50: return 22;
        // DRBR: Pink's (online_pink53.gml)
        case 51: return 12;
        case 52: return 12;
        case 53: return 14;
        case 54: return 16;
        case 55: return 22;
        case 56: return 16;
    }
    return 14;
}

// the Knight attack each item is, and the real objects it uses (also in KNIGHT_FIGHTS_ONLINE.txt)
function kbr_skill_real(_id)
{
    switch (_id)
    {
        case 1: return "Tracking Swords: obj_tracking_sword1";
        case 2: return "Tracking Swords x5: obj_tracking_sword1";
        case 3: return "Kaizo Diamond Storm: obj_diagonal_bullet__v1";
        case 4: return "Splitters' teeth: obj_roaringknight_split_bullet";
        case 5: return "Stars (ring): obj_knight_pointing_star";
        case 6: return "Stars: obj_knight_pointing_star";
        case 7: return "Kaizo Rising Abyss: obj_knight_weird_circle";
        case 10: return "Spinning Slashes: obj_roaringknight_slash";
        case 17: return "Kaizo Crescent: obj_bullet_knightcrescent";
        case 18: return "Kaizo Vortex swords: obj_fallingsword__v1";
        case 19: return "Elecknight lightning: obj_knight_lightningshock";
        case 20: return "Thorn Fountain Split: obj_roaringknight_fountain_bullet";
        case 21: return "Violet Diamond Eruption: obj_knight_weird_circle";
        case 26: return "Jevil's spade ring: obj_jv_spadering (Chapter 1's obj_spadering)";
        case 27: return "Jevil's rising diamonds: obj_jv_dvert (obj_dbullet_vert)";
        case 28: return "Jevil's dark clubs: obj_jv_clubs (obj_clubsbullet_dark)";
        case 29: return "Jevil's carousel: obj_jv_carousel (obj_carouselbullet)";
        case 30: return "Jevil's Devilsknife: obj_jv_cscythe (obj_centerscythe)";
        case 31: return "Jevil's suit bombs: obj_jv_suitbomb (obj_suitbomb)";
        case 32: return "Gerson's thrown hammers: obj_hj_hammer (Chapter 4's obj_gerson_hammer_bro_hammer)";
        case 33: return "Gerson's shell: obj_hj_pinball (obj_gerson_shell_pinball)";
        case 34: return "Gerson's swing: obj_hj_swing2 + obj_hj_swinghit (obj_gerson_swing_down_new + its telegraph)";
        case 35: return "Gerson's green SOUL: obj_hj_shield + obj_hj_spear (obj_spearblocker + obj_spearshot)";
        case 36: return "Gerson's bells: obj_hj_bellctrl, obj_hj_bell, obj_hj_bellhit, obj_hj_note (the unused bell attack)";
        case 37: return "Gerson's giant hammer: obj_hj_hammer (gigahammer)";
        case 38: return "Flowery's JARONA: obj_fl_jarona (Chapter 5's obj_orangeheart_floweryjarona, mode 0, speed 20)";
        case 39: return "Flowery's bamboo: obj_fl_wall stalks (obj_orangeheart_wall, the controller's unused difficulty 11)";
        case 40: return "Aqua's knives: obj_fl_pad + obj_fl_bullet knife chains (obj_orangeheart_jumppad, difficulty 10)";
        case 41: return "Seth's books: obj_fl_book + obj_fl_word + obj_fl_wordflower (obj_orangeheart_word_manager, attack type 3)";
        case 42: return "Orange & Green: obj_fl_jarona with Orange (obj_fl_mfancy) and JUST KIDDING (type 638's tag team)";
        case 43: return "Blue & Yellow: obj_fl_bloom + obj_fl_beam + butterflies (obj_orangeheart_wallflower, obj_yellow_beam, difficulty 6)";
        case 44: return "LAST JARONA: obj_fl_jarona rushing four times (the Omega fight's obj_plat_finalflowery JARONA: voice, 80-frame charge, speed 24)";
        case 45: return "Spamton NEO's pipis: obj_sn_pipegg hatching into obj_sn_pipcone heads (Chapter 2's obj_pipis_egg_bullet, obj_pipis_bullet_cone)";
        case 46: return "Spamton NEO's flying heads: obj_sn_lilguy + obj_sn_lilbullet (obj_sneo_lilguy, obj_sneo_guymaker's rows 0 / 1)";
        case 47: return "Spamton NEO's wire heart: obj_sn_wireheart, type 1 (obj_sneo_wireheart)";
        case 48: return "Spamton NEO's [[KROMER]]: obj_sn_dollar (the finale's obj_sneo_dollar)";
        case 49: return "Spamton NEO's RECREW mail walls: obj_sn_wallctrl, obj_sn_wallcell, obj_sn_wallbomb (obj_sneo_wall_controller_new)";
        case 50: return "Spamton NEO's [[BIG SHOT]]: obj_sn_biglaser + obj_sn_cannonshot (obj_sneo_biglaser, obj_spamtonshot)";
        case 51: return "Pink's cats: obj_pk_cat (Chapter 5's obj_pinkcatbullet, type 200's rows)";
        case 52: return "Pink's falling cats: obj_pk_cat, mode 2 (obj_pinkcatbullet, the unused type 204's columns)";
        case 53: return "Pink's lane bullets: obj_pk_lanebullet (obj_pinklanebullet, the rolling box's type 202)";
        case 54: return "Pink's fuse bombs: obj_pk_bomb + obj_pk_boom (obj_fusebomb, obj_pinkbombexplosion)";
        case 55: return "Pink's big bomb: obj_pk_bigbomb + obj_pk_boom (obj_fusebomb_big)";
        case 56: return "Pink's concert: obj_pk_fan, obj_pk_fanheart, obj_pk_hater (obj_audience_hitbox, obj_audienceheart, obj_audiencehater)";
    }
    return "";
}

// is the real version of _id made (8 SLOW, 9 CONFUSE are effects, not bullets)
function kbr_sa_has(_id)
{
    return (_id >= 1 && _id <= 7) || _id == 10 || (_id >= 17 && _id <= 21) || (_id >= 26 && _id <= 56);
}

function kbr_kn_has(_k)
{
    var _M = kbr_match();
    if (is_undefined(_M) || !variable_struct_exists(_M, "set") || !variable_struct_exists(_M.set, "kn"))
        return true;
    var _l = _M.set.kn;
    for (var _i = 0; _i < array_length(_l); _i++)
    {
        if (_l[_i] == _k)
            return true;
    }
    return false;
}

// ---------- a send starts (kbr_skill_land, in the target's own game) ----------
function kbr_sa_start(_s, _hx, _hy, _wtg)
{
    var _M = kbr_match();
    // build 52: _wtg - built for a watcher, aimed at the followed player (their SOUL is where the watcher's hidden one is)
    var _w = !is_undefined(_wtg);
    global.kbr_sa_n++;
    var _mul = variable_struct_exists(_s, "mul") ? _s.mul : 1;
    var _from = variable_struct_exists(_s, "from") ? _s.from : -1;
    var _G = { gx: global.kbr_sa_n, sid: _s.sid, from: _from, tg: _w ? _wtg : global.kfo.my, watch: _w, col: kbr_pcol(kbr_pslot(_from)),
        dmg: kbr_skill_dmg(_s.sid) * _mul, kv: 0, rg: kbr_rng(_s.sd + 4099), g: kbr_rng(_s.sd), t: 0, dead: false, made: 0,
        hx: _hx, hy: _hy, tel: [], end_t: 120, loop: -1, a: 0, b: 0, c: 0, list: [], seen: {}, age: 0, twin: false };
    global.kbr_sa_last = _G;
    switch (_s.sid)
    {
        case 3: case 7: case 17: case 18: _G.kv = 1; break;
        case 19: _G.kv = 2; break;
        case 21: _G.kv = 3; break;
        case 20: _G.kv = 4; break;
    }
    array_push(global.kbr_sa, _G);
    global.kbr_san = 1;
    kbr_sa_step(_G);
    _G.t++;
    return _G;
}

// the Twin Knight's real attack objects (stars that burst into starchildren, tracking swords): each spawn its own group, kept
// apart from the Knight's managers (online), with a random stream seeded from the shared one (the same in every game)
function kbr_sa_twin_group()
{
    global.kbr_sa_n++;
    var _kv = global.knight_variant;
    if (_kv != 1 && _kv != 2 && _kv != 4)
        _kv = 0;
    var _sd = kbr_irandom(2147480000);
    // (DRBR: every field a send has - watch too: the INCOMING list reads it for every group, a Twin Knight's included)
    var _G = { gx: global.kbr_sa_n, sid: 0, from: -1, tg: -1, watch: false, col: c_white, dmg: 0, kv: _kv, rg: kbr_rng(_sd + 1), g: kbr_rng(_sd), t: 0, dead: false,
        made: 0, hx: 0, hy: 0, tel: [], end_t: 150, loop: -1, a: 0, b: 0, c: 0, list: [], seen: {}, age: 0, twin: true };
    array_push(global.kbr_sa, _G);
    global.kbr_san = 1;
    return _G;
}

// make one real attack object for send _G (its Create adopts it into the send)
function kbr_sa_mk(_G, _x, _y, _obj)
{
    global.kbr_curx = _G;
    var _i = instance_create(_x, _y, _obj);
    global.kbr_curx = undefined;
    if (instance_exists(_i) && !variable_instance_exists(_i, "kbrx"))
    {
        with (_i)
            kbr_sa_tag(_G);
    }
    return _i;
}

// a run of code inside send _G (what it makes joins the send)
function kbr_sa_in(_G)
{
    global.kbr_curx = _G;
}

function kbr_sa_out()
{
    global.kbr_curx = undefined;
}

function kbr_sa_box()
{
    var _b = instance_find(obj_growtangle, 0);
    return [_b.x, _b.y, abs(_b.sprite_width) / 2, abs(_b.sprite_height) / 2];
}

function kbr_sa_soul()
{
    var _h = instance_find(obj_heart, 0);
    return [_h.x + 10, _h.y + 10];
}

// a telegraph drawn by kbr_sa_draw: k "ph" (a phantom of the sender's knight, real sprite), "seam" (the box splitting),
// "mark" (the rotating slash's markers); from t0 for d frames
function kbr_sa_tel(_G, _k, _x, _y, _d, _a)
{
    array_push(_G.tel, { k: _k, x: _x, y: _y, t0: _G.t, d: _d, a: _a, n: 1, rot: 0, sp: 1 });
    return _G.tel[array_length(_G.tel) - 1];
}

// ---------- every frame (the hub controller's Step) ----------
function kbr_sa_frame()
{
    global.kbr_sa_f++;
    global.kbr_cur = 0;
    var _on = kbr_on();
    global.kbr_san = (_on || array_length(global.kbr_sa) > 0) ? 1 : 0;
    if (array_length(global.kbr_sa) == 0)
    {
        kbr_sa_surf_free();
        return 0;
    }
    var _M = kbr_match();
    // no SOUL: everything ends; no match / out: the players' sends end (the Twin Knight's own attacks stay theirs)
    if (!instance_exists(obj_heart))
    {
        global.kbr_sa_why = "nosoul";
        kbr_sa_clear();
        return 0;
    }
    if (!_on || is_undefined(_M) || _M.out || !_M.me)
    {
        var _had = false;
        // build 52: a watcher keeps the sends built for the player they follow
        var _wp = kbr_spec_pid(_M);
        for (var _i = array_length(global.kbr_sa) - 1; _i >= 0; _i--)
        {
            var _G0 = global.kbr_sa[_i];
            if (_on && !_G0.twin && variable_struct_exists(_G0, "watch") && _G0.watch && _wp >= 0 && _G0.tg == _wp)
                continue;
            if (!_G0.twin)
            {
                _had = true;
                kbr_sa_kill(_G0.gx);
                if (_G0.loop >= 0)
                    audio_stop_sound(_G0.loop);
                array_delete(global.kbr_sa, _i, 1);
            }
        }
        if (_had)
            global.kbr_sa_why = !_on ? "off" : (is_undefined(_M) ? "nomatch" : "out");
        if (array_length(global.kbr_sa) == 0)
        {
            kbr_sa_surf_free();
            return 0;
        }
    }
    // between two attacks the box is gone a moment (and a splitter moves it away): what reads the box goes, the sends'
    // timelines wait for it to come back (the rest - swords, stars, crescents... - flies on)
    var _boxok = instance_exists(obj_growtangle) && instance_find(obj_growtangle, 0).x > -1000;
    if (!_boxok)
        kbr_sa_boxless();
    for (var _i = array_length(global.kbr_sa) - 1; _i >= 0; _i--)
    {
        var _G = global.kbr_sa[_i];
        _G.age++;
        if (!_G.dead && _boxok)
        {
            kbr_sa_step(_G);
            _G.t++;
        }
        // DRBR: a boss's pieces leave with their turn in their own chapter (a send never ends one): the send's bullets far off
        // the screen (240 px past it, out for half a second) go, so a send ends when its last piece is gone
        if (!_G.dead && (_G.age mod 10) == 0 && _G.t > 20)
            kbr_sa_offscreen(_G.gx);
        // done: its time is up and nothing of it is left (checked every 10 frames), or 20 seconds at most
        if (_G.dead || (_G.t > _G.end_t && (_G.age mod 10) == 0 && kbr_sa_alive(_G.gx) == 0) || _G.age > 600)
        {
            kbr_sa_kill(_G.gx);
            if (_G.loop >= 0)
                audio_stop_sound(_G.loop);
            array_delete(global.kbr_sa, _i, 1);
        }
    }
    if (array_length(global.kbr_sa) == 0)
        kbr_sa_surf_free();
    return 1;
}

// send _gx's bullets 240 px or more off the screen, made at least 15 frames ago, go
function kbr_sa_offscreen(_gx)
{
    var _cx = camerax();
    var _cy = cameray();
    var _f = global.kbr_sa_f;
    with (obj_bulletparent)
    {
        if (variable_instance_exists(id, "kbrx") && kbrx == _gx && (x < _cx - 240 || x > _cx + 880 || y < _cy - 240 || y > _cy + 720)
            && (!variable_instance_exists(id, "kbrt0") || _f - kbrt0 >= 15))
            instance_destroy();
    }
    return 1;
}

// the Knight's turn is over: the Twin Knight's own attacks go with it (as the Knight's do)
function kbr_sa_twin_end(_all)
{
    // (_all: the cycle is over online - the Twin Knight's own warps and afterimages go too)
    if (_all == true)
    {
        with (obj_knight_warp)
        {
            if (variable_instance_exists(id, "kbrtwin"))
                instance_destroy();
        }
        with (obj_afterimage)
        {
            if (variable_instance_exists(id, "kbrtwin"))
                instance_destroy();
        }
    }
    for (var _i = array_length(global.kbr_sa) - 1; _i >= 0; _i--)
    {
        var _G = global.kbr_sa[_i];
        if (_G.twin)
        {
            kbr_sa_kill(_G.gx);
            array_delete(global.kbr_sa, _i, 1);
        }
    }
    return 1;
}

// what is left of send _gx (0: everything)
function kbr_sa_alive(_gx)
{
    var _n = 0;
    with (obj_bulletparent)
    {
        if (variable_instance_exists(id, "kbrx") && kbrx > 0 && (_gx == 0 || kbrx == _gx))
            _n++;
    }
    with (obj_bulletgenparent)
    {
        if (variable_instance_exists(id, "kbrx") && kbrx > 0 && (_gx == 0 || kbrx == _gx))
            _n++;
    }
    with (obj_knight_circle)
    {
        if (variable_instance_exists(id, "kbrx") && kbrx > 0 && (_gx == 0 || kbrx == _gx))
            _n++;
    }
    // DRBR: the bosses' non-bullet pieces (Gerson's shield, spears, swings, bells)
    _n += kbr_enc_sa_alive(_gx);
    return _n;
}

// destroy what send _gx made (0: every send's) - bullets, generators, the helpers it made, their surfaces with them
function kbr_sa_kill(_gx)
{
    // DRBR: a send's own end first (SPEAR VOLLEY puts your SOUL back), then the bosses' non-bullet pieces
    if (_gx > 0)
        kbr_sa_onend(kbr_sa_find(_gx));
    kbr_enc_sa_kill(_gx, false);
    var _l = [obj_bulletparent, obj_bulletgenparent, obj_knight_circle, obj_particle_generic, obj_lerpvar, obj_script_delayed, obj_afterimage, obj_afterimage_grow, obj_tracking_sword_slash_extra_graze];
    for (var _j = 0; _j < array_length(_l); _j++)
    {
        with (_l[_j])
        {
            if (variable_instance_exists(id, "kbrx") && kbrx > 0 && (_gx == 0 || kbrx == _gx))
                instance_destroy();
        }
    }
    return 1;
}

// the box is gone (between two attacks) or moved away (a splitter): the sent objects that read the box go, the others stay
function kbr_sa_boxless()
{
    if (array_length(global.kbr_sa) == 0)
        return 0;
    // (build 52: Jevil's carousel horses and spade rings read the box too)
    // DRBR: the bosses' pieces that read the box (their defs' objs and boxy)
    kbr_enc_sa_kill(0, true);
    var _l = [obj_diagonal_bullet__v1, obj_knight_circle, obj_knight_weird_circle, obj_jv_carousel, obj_jv_spadering, obj_jv_bscythe];
    for (var _j = 0; _j < array_length(_l); _j++)
    {
        with (_l[_j])
        {
            if (variable_instance_exists(id, "kbrx") && kbrx > 0)
                instance_destroy();
        }
    }
    return 1;
}

// every send ends now (the match ends, you are out)
function kbr_sa_clear()
{
    if (array_length(global.kbr_sa) == 0)
    {
        kbr_sa_surf_free();
        global.kbr_curx = undefined;
        return 0;
    }
    for (var _i = 0; _i < array_length(global.kbr_sa); _i++)
    {
        if (global.kbr_sa[_i].loop >= 0)
            audio_stop_sound(global.kbr_sa[_i].loop);
        kbr_sa_onend(global.kbr_sa[_i]);
        global.kbr_sa[_i].dead = true;
    }
    global.kbr_sa = [];
    kbr_sa_kill(0);
    kbr_sa_surf_free();
    global.kbr_curx = undefined;
    return 1;
}

function kbr_sa_surf_free()
{
    if (global.kbr_sa_surf != -1 && surface_exists(global.kbr_sa_surf))
        surface_free(global.kbr_sa_surf);
    global.kbr_sa_surf = -1;
    return 0;
}

// Begin Step: the sent instances' own colours back (End Step tinted them for drawing only)
function kbr_sa_begin()
{
    global.kbr_cur = 0;
    if (global.kbr_san <= 0 || array_length(global.kbr_sa) == 0)
        return 0;
    with (obj_bulletparent)
    {
        if (variable_instance_exists(id, "kbrtb") && kbrtb != -1)
        {
            if (image_blend == kbrtb)
                image_blend = kbrb;
            kbrtb = -1;
        }
    }
    with (obj_bulletgenparent)
    {
        if (variable_instance_exists(id, "kbrtb") && kbrtb != -1)
        {
            if (image_blend == kbrtb)
                image_blend = kbrb;
            kbrtb = -1;
        }
    }
    return 1;
}

// End Step: tinted in the sender's colour (the sprite's own colours stay: a mix, not a fill). DRBR 1.0.3: the knights' sends;
// a boss's send is coloured as it is drawn instead (kbr_ov_*, below)
function kbr_sa_end()
{
    global.kbr_cur = 0;
    if (global.kbr_san <= 0 || array_length(global.kbr_sa) == 0)
    {
        if (instance_exists(obj_knight_saov))
            instance_destroy(obj_knight_saov);
        return 0;
    }
    kbr_sa_fit_all();
    with (obj_bulletparent)
    {
        if (variable_instance_exists(id, "kbrcol") && variable_instance_exists(id, "kbrx") && kbrx > 0 && !(variable_instance_exists(id, "kbrov") && kbrov))
        {
            kbrb = image_blend;
            image_blend = merge_color(image_blend, kbrcol, KBR_SENT_TINT);
            kbrtb = image_blend;
        }
    }
    with (obj_bulletgenparent)
    {
        if (variable_instance_exists(id, "kbrcol") && variable_instance_exists(id, "kbrx") && kbrx > 0 && !(variable_instance_exists(id, "kbrov") && kbrov))
        {
            kbrb = image_blend;
            image_blend = merge_color(image_blend, kbrcol, KBR_SENT_TINT);
            kbrtb = image_blend;
        }
    }
    kbr_ov_drawers();
    return 1;
}

// ---------- DRBR 1.0.3: a boss's send in the sender's SOUL colour ----------
// Your request: "make the sent attacks from the other bosses be tinted your soul color ... and actually look nice when in attack
// ... like the actual graphic of the thing being sent". The knights' sends always were (their pieces are mostly white, mixed
// with the sender's colour), but a boss's pieces are his own coloured art: the same light mix hardly showed on them. Now every
// picture a piece of a boss's send draws is drawn once more right over itself, as a silhouette in the sender's colour at
// KBR_OV_A of its alpha (the game's own gpu fog, as its hit flashes): the art turns that colour and keeps its own lines and
// shading. Pieces with a Draw of their own: the generator routes the draw calls in the bosses' Draw events through kbr_ov_*
// (gen_hub.py); pieces drawn the default way (the game's obj_regularbullet / obj_collidebullet / obj_afterimage, a boss's
// pieces with no Draw): a drawer just above their depth (obj_knight_saov) draws it for them. Not over a piece's own flash
// (fog), glow (another blend mode) or shader. The boss's own bullets never get it: a send is always told apart.
#macro KBR_OV_A 0.5

// whether the picture just drawn gets the colour drawn over it: self is a piece of a boss's send, and nothing special (a fog
// flash, a glow, a shader) is drawing
function kbr_ov_on()
{
    if (!variable_instance_exists(id, "kbrov") || !kbrov)
        return false;
    if (shader_current() != -1 || gpu_get_blendmode() != bm_normal)
        return false;
    var _f = gpu_get_fog();
    return !(is_array(_f) && array_length(_f) > 0 && _f[0]);
}

function kbr_ov_dse(_s, _i, _x, _y, _xs, _ys, _r, _c, _a)
{
    draw_sprite_ext(_s, _i, _x, _y, _xs, _ys, _r, _c, _a);
    if (kbr_ov_on())
    {
        gpu_set_fog(true, kbrovc, 0, 0);
        draw_sprite_ext(_s, _i, _x, _y, _xs, _ys, _r, c_white, clamp(_a, 0, 1) * KBR_OV_A);
        gpu_set_fog(false, c_black, 0, 0);
    }
    return 0;
}

function kbr_ov_ds(_s, _i, _x, _y)
{
    draw_sprite(_s, _i, _x, _y);
    if (kbr_ov_on())
    {
        gpu_set_fog(true, kbrovc, 0, 0);
        draw_sprite_ext(_s, _i, _x, _y, 1, 1, 0, c_white, draw_get_alpha() * KBR_OV_A);
        gpu_set_fog(false, c_black, 0, 0);
    }
    return 0;
}

function kbr_ov_dself()
{
    draw_self();
    if (kbr_ov_on() && sprite_index >= 0)
    {
        gpu_set_fog(true, kbrovc, 0, 0);
        draw_sprite_ext(sprite_index, image_index, x, y, image_xscale, image_yscale, image_angle, c_white, clamp(image_alpha, 0, 1) * KBR_OV_A);
        gpu_set_fog(false, c_black, 0, 0);
    }
    return 0;
}

function kbr_ov_dspe(_s, _i, _l, _t, _w, _h, _x, _y, _xs, _ys, _c, _a)
{
    draw_sprite_part_ext(_s, _i, _l, _t, _w, _h, _x, _y, _xs, _ys, _c, _a);
    if (kbr_ov_on())
    {
        gpu_set_fog(true, kbrovc, 0, 0);
        draw_sprite_part_ext(_s, _i, _l, _t, _w, _h, _x, _y, _xs, _ys, c_white, clamp(_a, 0, 1) * KBR_OV_A);
        gpu_set_fog(false, c_black, 0, 0);
    }
    return 0;
}

function kbr_ov_dsp(_s, _i, _l, _t, _w, _h, _x, _y)
{
    draw_sprite_part(_s, _i, _l, _t, _w, _h, _x, _y);
    if (kbr_ov_on())
    {
        gpu_set_fog(true, kbrovc, 0, 0);
        draw_sprite_part_ext(_s, _i, _l, _t, _w, _h, _x, _y, 1, 1, c_white, draw_get_alpha() * KBR_OV_A);
        gpu_set_fog(false, c_black, 0, 0);
    }
    return 0;
}

// the shapes and words a piece draws (their colour): the sender's colour mixed in the same way
function kbr_ov_col(_c)
{
    draw_set_color((variable_instance_exists(id, "kbrov") && kbrov) ? merge_color(_c, kbrovc, KBR_OV_A) : _c);
    return 0;
}

// the pieces drawn the default way: the game's own bullet objects, and a boss's own piece whose Draw never ran (the generator
// marks every boss Draw: kbrovd)
function kbr_ov_dd()
{
    if (variable_instance_exists(id, "kbrovd"))
        return false;
    if (!variable_instance_exists(id, "kbrovb"))
    {
        var _n = object_get_name(object_index);
        kbrovb = (object_index == obj_regularbullet || object_index == obj_collidebullet || object_index == obj_afterimage || object_index == obj_bulletparent
            || string_pos("obj_jv_", _n) == 1 || string_pos("obj_hj_", _n) == 1 || string_pos("obj_sn_", _n) == 1 || string_pos("obj_pk_", _n) == 1
            || string_pos("obj_fl_", _n) == 1);
    }
    return kbrovb;
}

// End Step: one drawer just above every depth such pieces are at (made / moved / removed as they come and go)
function kbr_ov_drawers()
{
    var _deps = {};
    var _n = 0;
    with (all)
    {
        if (variable_instance_exists(id, "kbrov") && kbrov && visible && sprite_index >= 0 && kbr_ov_dd())
        {
            var _k = string(depth);
            if (!variable_struct_exists(_deps, _k) && _n < 8)
            {
                variable_struct_set(_deps, _k, depth);
                _n++;
            }
        }
    }
    with (obj_knight_saov)
    {
        var _k = string(dep);
        if (variable_struct_exists(_deps, _k))
            variable_struct_remove(_deps, _k);
        else
            instance_destroy();
    }
    var _ks = variable_struct_get_names(_deps);
    for (var _i = 0; _i < array_length(_ks); _i++)
    {
        var _d = variable_struct_get(_deps, _ks[_i]);
        with (instance_create_depth(0, 0, _d - 1, obj_knight_saov))
            dep = _d;
    }
    return _n;
}

// obj_knight_saov's Draw (just after the pieces at its depth): the colour over each default-drawn piece of a boss's send there
function kbr_ov_drawer()
{
    if (global.kbr_san <= 0 || !variable_instance_exists(id, "dep"))
    {
        instance_destroy();
        return 0;
    }
    if (shader_current() != -1 || gpu_get_blendmode() != bm_normal)
        return 0;
    var _dep = dep;
    var _on = false;
    with (all)
    {
        if (depth == _dep && visible && variable_instance_exists(id, "kbrov") && kbrov && sprite_index >= 0 && image_alpha > 0 && kbr_ov_dd())
        {
            _on = true;
            gpu_set_fog(true, kbrovc, 0, 0);
            draw_sprite_ext(sprite_index, image_index, x, y, image_xscale, image_yscale, image_angle, c_white, clamp(image_alpha, 0, 1) * KBR_OV_A);
        }
    }
    if (_on)
        gpu_set_fog(false, c_black, 0, 0);
    return 1;
}

// DRBR 1.0.3: a boss's send fits the box it lands in (your report: sent skills "need to visibly fit in the box, not be really
// really large"). Its pieces are the boss's own, made for his own battle: at the end of a piece's first step with a picture,
// one bigger than the box allows is scaled down once - its picture and its hitbox together (image_xscale / image_yscale; a
// piece that sizes itself every step by its scale_multiplier - Pink's bombs - has that scaled too). A long thin piece (a beam,
// a slash) keeps its length: its thickness is what is measured. The knights' sends are their own attacks' size: unchanged.
#macro KBR_SA_FIT 1.35

// a piece's own size factor for a send (kbrsz, set where a send makes it - the BIG SHOT laser), 1 for everything else
function kbr_fitv()
{
    return (variable_instance_exists(id, "kbrsz") && is_numeric(kbrsz)) ? kbrsz : 1;
}

function kbr_sa_fit_all()
{
    if (!instance_exists(obj_growtangle))
        return 0;
    var _B = kbr_sa_box();
    var _lim = max(32, min(_B[2], _B[3]) * KBR_SA_FIT);
    with (all)
    {
        if (variable_instance_exists(id, "kbrc") && variable_instance_exists(id, "kbrx") && kbrx > 0 && !variable_instance_exists(id, "kbrfit")
            && sprite_index >= 0 && visible && image_alpha > 0)
        {
            kbrfit = 1;
            var _G = kbr_sa_find(kbrx);
            if (is_struct(_G) && !_G.twin && _G.sid >= 26)
            {
                var _w = sprite_get_width(sprite_index) * abs(image_xscale);
                var _h = sprite_get_height(sprite_index) * abs(image_yscale);
                var _sz = max(_w, _h);
                if (_sz > (3 * min(_w, _h)))
                    _sz = min(_w, _h);
                if (_sz > _lim)
                {
                    kbrfit = _lim / _sz;
                    if (variable_instance_exists(id, "scale_multiplier") && is_numeric(scale_multiplier))
                        scale_multiplier *= kbrfit;
                    image_xscale *= kbrfit;
                    image_yscale *= kbrfit;
                }
            }
        }
    }
    return 1;
}

// ---------- each item's timeline (frame _G.t of the send) ----------
function kbr_sa_step(_G)
{
    var _t = _G.t;
    var _g = _G.g;
    var _B = kbr_sa_box();
    var _S = kbr_sa_soul();
    switch (_G.sid)
    {
        // DRBR: GERSON's (online_gerson53.gml)
        case 32:
        case 33:
        case 34:
        case 35:
        case 36:
        case 37:
            kbr_hj_sa_step(_G, _t, _g, _B, _S);
            break;
        // DRBR: FLOWERY's (online_flowery53.gml): on the target's orange board
        case 38:
        case 39:
        case 40:
        case 41:
        case 42:
        case 43:
        case 44:
            kbr_fl_sa_step(_G, _t);
            break;
        // DRBR: SPAMTON NEO's (online_spamton53.gml)
        case 45:
        case 46:
        case 47:
        case 48:
        case 49:
        case 50:
            kbr_sn_sa_step(_G, _t, _g, _B, _S);
            break;
        // DRBR: PINK's (online_pink53.gml)
        case 51:
        case 52:
        case 53:
        case 54:
        case 55:
        case 56:
            kbr_pk_sa_step(_G, _t, _g, _B, _S);
            break;
        // build 52: JEVIL's sends - his own Chapter 1 pieces around YOUR SOUL / in your box (make_jevil.py), smaller than his
        // own attacks (one ring, one row, a few bombs)
        case 26:
            // SPADE RING: eight spades appear on a ring round the box, close in, then fly off one after another
            if (_t == 0)
            {
                var _rg = kbr_sa_mk(_G, _B[0], _B[1], obj_jv_spadering);
                _rg.maxspade = 8;
                _rg.grav = 0.35;
                _rg.startang = kbr_rng_int(_g, 360);
                kbr_sa_sfx(snd_spearappear, 1.2);
            }
            _G.end_t = 120;
            break;
        case 27:
            // DIAMOND RAIN: diamonds rise up through the box under your SOUL, one every 5 frames
            if ((_t mod 5) == 0 && _t < 50)
            {
                var _dx = (kbr_rng_int(_g, 4) == 3) ? (kbr_rng_int(_g, 21) - 10) : (kbr_rng_int(_g, 201) - 100);
                var _dv = kbr_sa_mk(_G, _S[0] + _dx, _B[1] + 100, obj_jv_dvert);
                _dv.type = 1;
            }
            _G.end_t = 110;
            break;
        case 28:
            // CLUB SPIRAL: four dark clubs dive at your SOUL from the corners, each bursting into three club balls
            if ((_t mod 18) == 0 && _t < 72)
            {
                var _cd = ((_t div 18) mod 2 == 0) ? kbr_choose_g(_g, 45, 135) : kbr_choose_g(_g, 225, 315);
                var _cl = kbr_sa_mk(_G, _S[0] + lengthdir_x(360, _cd), _S[1] + lengthdir_y(360, _cd), obj_jv_clubs);
                _cl.direction = _cd + 180;
                _cl.speed = 20;
                _cl.friction = 1;
                _cl.type = 2;
                _cl.image_angle = _cl.direction;
            }
            _G.end_t = 130;
            break;
        case 29:
            // HEART CAROUSEL: a row of seven carousel horses at your SOUL's height, spinning round the box
            if (_t == 0)
            {
                for (var _j = 0; _j < 7; _j++)
                {
                    var _hr = kbr_sa_mk(_G, _B[0] + 150, _S[1], obj_jv_carousel);
                    _hr.siner = _j * 18;
                    _hr.vsin = _j * 9;
                    _hr.sinspeed = 1.15;
                    _hr.altmode = 3;
                }
                kbr_sa_sfx(snd_joker_oh, 1);
            }
            _G.end_t = 210;
            break;
        case 30:
            // DEVILSKNIFE: four Devilsknives swing round the box's middle (the first makes the other three). DRBR 1.0.2: with
            // Jevil's own "METAMORPHOSIS!" (Chapter 1's clip as he becomes the Devilsknife) - it came in silently
            if (_t == 0)
            {
                kbr_sa_mk(_G, _B[0], _B[1], obj_jv_cscythe);
                kbr_sa_sfx(snd_jv_joker_metamorphosis, 1);
                kbr_sa_sfx(snd_spearappear, 1);
            }
            _G.end_t = 200;
            break;
        case 31:
            // CHAOS BOMBS: three suit bombs fall in beside the box and burst (spades, diamonds at you, a heart, clubs at you)
            if (_t == 0 || _t == 14 || _t == 28)
            {
                var _bxx = kbr_rng_int(_g, 2) ? (_B[0] - 180 - kbr_rng_int(_g, 100)) : (_B[0] + 180 + kbr_rng_int(_g, 100));
                var _bm = kbr_sa_mk(_G, _bxx, cameray() - 20, obj_jv_suitbomb);
                _bm.type = kbr_rng_int(_g, 4);
            }
            _G.end_t = 140;
            break;
        case 1:
            // SWORD: one tracking sword - it follows your SOUL from one of eight sides, flashes, then slashes across
            if (_t == 0)
                kbr_sa_sword(_G, kbr_rng_int(_g, 8) * 45);
            _G.end_t = 60;
            break;
        case 2:
            // FLURRY: five tracking swords, one every 8 frames, from alternating sides
            if ((_t mod 8) == 0 && _t < 40)
            {
                var _k = _t div 8;
                var _d = (((_k mod 2) == 0) ? 0 : 180) + ((kbr_rng_int(_g, 3) - 1) * 45);
                kbr_sa_sword(_G, (_d + 360) mod 360);
            }
            _G.end_t = 90;
            break;
        case 3:
            // DIAMOND STORM: Kaizo's diagonal rows - two rows of diamonds slanting across the box, the second from the
            // other side (Kaizo's side B), as obj_diagonal_bullet_manager makes them
            if (_t == 0 || _t == 44)
            {
                var _vs = kbr_rng_int(_g, 2) ? 6 : -6;
                var _hs = -5;
                var _xx = 300;
                if (_t == 44)
                {
                    _xx = -300;
                    _hs = 5;
                }
                for (var _i = 0; _i < 24; _i++)
                {
                    var _b = kbr_sa_mk(_G, _B[0] + _xx, (_B[1] - 100) + (56 * _i), obj_diagonal_bullet__v1);
                    _b.hspeed = _hs;
                    _b.vspeed = _vs;
                    if (_vs > 0)
                        _b.y = (_b.y - (24 * 56)) + 300;
                }
            }
            _G.end_t = 200;
            break;
        case 4:
            // STREAMLINE: the Splitters' teeth - a phantom of the sender's knight on one side, then a stream of teeth sweeps
            // across the box from there
            if (_t == 0)
            {
                _G.a = kbr_rng_int(_g, 2);
                kbr_sa_tel(_G, "ph", _G.a ? (_B[0] + _B[2] + 46) : (_B[0] - _B[2] - 46), _B[1], 18, _G.a ? 180 : 0);
                kbr_sa_sfx(snd_knight_jump_quick, 1.1);
            }
            if (_t >= 16 && _t < 61 && ((_t - 16) mod 5) == 0)
            {
                var _k2 = (_t - 16) div 5;
                var _yy = (_B[1] - _B[3]) + ((_B[3] * 2 * (_k2 + 0.5)) / 9);
                var _tooth = kbr_sa_mk(_G, _G.a ? (_B[0] + _B[2] + 30) : (_B[0] - _B[2] - 30), _yy, obj_roaringknight_split_bullet);
                _tooth.direction = _G.a ? 180 : 0;
                _tooth.image_angle = _tooth.direction;
                _tooth.top_speed = 7;
                if (_k2 == 0)
                    kbr_sa_sfx(snd_knight_cut2, 1);
            }
            _G.end_t = 140;
            break;
        case 5:
            // RING: six stars grow on a ring around your SOUL, close in, stop, then burst into starchildren
            if (_t == 0)
            {
                var _a0 = kbr_rng_int(_g, 60);
                for (var _i = 0; _i < 6; _i++)
                {
                    var _ra = _a0 + (_i * 60);
                    var _st = kbr_sa_mk(_G, _S[0] + lengthdir_x(110, _ra), _S[1] + lengthdir_y(110, _ra), obj_knight_pointing_star);
                    _st.direction = point_direction(_st.x, _st.y, _S[0], _S[1]);
                    _st.playSound = (_i mod 2) == 0;
                    array_push(_G.list, _st);
                }
                kbr_sa_sfx(snd_knight_drawpower, 1.3);
            }
            if (_t == 24)
            {
                for (var _i = 0; _i < array_length(_G.list); _i++)
                {
                    if (instance_exists(_G.list[_i]))
                    {
                        with (_G.list[_i])
                        {
                            con = 1;
                            speed = 5;
                        }
                    }
                }
            }
            _G.end_t = 200;
            break;
        case 6:
            // STAR BURST: three stars appear near your SOUL, grow, and burst one after another
            if (_t == 0)
            {
                for (var _j = 0; _j < 3; _j++)
                {
                    var _ba = kbr_rng_int(_g, 360);
                    var _bd = 50 + kbr_rng_int(_g, 30);
                    var _sx = clamp(_S[0] + lengthdir_x(_bd, _ba), (_B[0] - _B[2]) - 20, _B[0] + _B[2] + 20);
                    var _sy = clamp(_S[1] + lengthdir_y(_bd, _ba), (_B[1] - _B[3]) - 20, _B[1] + _B[3] + 20);
                    var _st2 = kbr_sa_mk(_G, _sx, _sy, obj_knight_pointing_star);
                    _st2.timer = -12 * _j;
                    _st2.direction = _ba + 180;
                    array_push(_G.list, _st2);
                }
                kbr_sa_sfx(snd_knight_drawpower, 1.3);
            }
            if (_t == 30)
            {
                for (var _i = 0; _i < array_length(_G.list); _i++)
                {
                    if (instance_exists(_G.list[_i]))
                    {
                        with (_G.list[_i])
                            con = 1;
                    }
                }
            }
            _G.end_t = 200;
            break;
        case 7:
            // WEIRD CIRCLE: Kaizo's Rising Abyss - three weird circles open at the floor of the box under your SOUL, brighten,
            // and fire the weird shape and its diamonds upward
            if (_t == 0 || _t == 14 || _t == 28)
            {
                var _k3 = _t div 14;
                var _cx = clamp(_S[0] + ((_k3 - 1) * 46) + (kbr_rng_int(_g, 21) - 10), (_B[0] - _B[2]) + 12, (_B[0] + _B[2]) - 12);
                var _wc = kbr_sa_mk(_G, _cx, _B[1] + _B[3] - 2, obj_knight_weird_circle);
                _wc.alarm[1] = 24;
            }
            _G.end_t = 160;
            break;
        case 10:
            // KNIGHTMARE: the Spinning Slashes - a black flash, then three rounds of the rotating slash's turning markers
            // locked on your SOUL, each ending in its slashes through that spot (1, 2, then 3 at once)
            kbr_sa_knightmare(_G, _t, _B, _S);
            break;
        case 17:
            // CRESCENT SLASH: Kaizo's crescents - the knight swings at the right of the box, pairs of crescents split apart
            // and speed across, three volleys aimed at your SOUL's row
            if (_t == 0)
                kbr_sa_tel(_G, "ph", _B[0] + _B[2] + 50, _S[1], 70, 180);
            if (_t == 12 || _t == 36 || _t == 60)
            {
                var _rows = 6;
                var _bh = _B[3] * 2;
                var _row = clamp(floor(((_S[1] - (_B[1] - _B[3])) / _bh) * (_rows + 1)) - 1 + (kbr_rng_int(_g, 3) - 1), 0, _rows - 1);
                var _cy = (_B[1] - _B[3]) + ((_bh / (_rows + 1)) * (_row + 1));
                var _cxx = _B[0] + _B[2] + 40;
                var _c1 = kbr_sa_mk(_G, _cxx, _cy + 5, obj_bullet_knightcrescent);
                var _c2 = kbr_sa_mk(_G, _cxx, _cy - 5, obj_bullet_knightcrescent);
                kbr_sa_in(_G);
                scr_darksize(_c1);
                scr_darksize(_c2);
                _c2.image_yscale = -2;
                with (_c1)
                    scr_lerpvar("y", y, y - 14, 25);
                with (_c2)
                    scr_lerpvar("y", y, y + 14, 25);
                kbr_sa_out();
                _c1.hspeed = -1;
                _c1.friction = -0.35;
                _c2.hspeed = -1;
                _c2.friction = -0.35;
                kbr_sa_sfx(snd_knight_cut2, 1);
            }
            _G.end_t = 160;
            break;
        case 18:
            // SWORD RAIN: Kaizo's falling swords - five swords flip in above your SOUL, rise, then dive at it
            if ((_t mod 12) == 0 && _t < 60)
            {
                var _fx = (_S[0] + kbr_rng_int(_g, 97)) - 48;
                var _fy = (_B[1] - 110) + kbr_rng_int(_g, 30);
                var _fs = kbr_sa_mk(_G, _fx, _fy, obj_fallingsword__v1);
                kbr_sa_in(_G);
                with (_fs)
                {
                    image_angle = point_direction(x, y, _S[0], _S[1]);
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
                kbr_sa_out();
            }
            _G.end_t = 150;
            break;
        case 19:
            // THUNDER LINES: Elecknight's lightning - four lines cross the box near your SOUL, first as its thin cyan
            // telegraph, then as lightning
            if ((_t mod 10) == 0 && _t < 40)
            {
                var _la = kbr_rng_int(_g, 180);
                var _off = kbr_rng_int(_g, 41) - 20;
                var _px = _S[0] + lengthdir_x(_off, _la + 90);
                var _py = _S[1] + lengthdir_y(_off, _la + 90);
                var _ls = kbr_sa_mk(_G, _px + lengthdir_x(320, _la), _py + lengthdir_y(320, _la), obj_knight_lightningshock);
                _ls.xb = _px - lengthdir_x(320, _la);
                _ls.yb = _py - lengthdir_y(320, _la);
                _ls.activatetimer = 26;
                _ls.maxtimer = 36;
            }
            _G.end_t = 90;
            break;
        case 20:
            // FOUNTAIN SPLIT: Thorn's fountain - the box's seam flashes across the middle, then the fountain bullets burst
            // up and down out of it, column by column
            if (_t == 0)
            {
                _G.c = _B[1] + ((kbr_rng_int(_g, 3) - 1) * 16);
                kbr_sa_tel(_G, "seam", _B[0], _G.c, 20, _B[2]);
                kbr_sa_sfx(snd_knight_boxbreak, 1.1);
            }
            if (_t == 20)
            {
                kbr_sa_sfx(snd_chargeshot_fire, 1);
                var _xs = _B[0] - 66;
                var _bt = 0;
                var _bb = 0;
                for (var _i = 0; _i < 14; _i++)
                {
                    var _bal = ((_i mod 2) == 0) ? _bt : _bb;
                    var _ch = (_bal >= 3) ? -1 : ((_bal <= -3) ? 1 : (kbr_rng_int(_g, 2) ? 1 : -1));
                    if ((_i mod 2) == 0)
                        _bt += _ch;
                    else
                        _bb += _ch;
                    kbr_sa_fountain(_G, _xs, _G.c, (_ch > 0) ? 8 : 4, _i);
                    if (_ch > 0)
                        kbr_sa_fountain(_G, _xs, _G.c, 2, _i);
                    if ((_i mod 2) == 1)
                        _xs += 22;
                }
            }
            _G.end_t = 120;
            break;
        case 0:
            // the Twin Knight's own attack (knight_twin_real): it times its objects itself
            break;
        case 21:
            // DIAMOND ERUPTION: the Violet Knight's eruption - a violet weird circle opens at the floor of the box under
            // your SOUL and erupts in a full fan of diamonds
            if (_t == 0)
            {
                var _ex = clamp(_S[0] + (kbr_rng_int(_g, 41) - 20), (_B[0] - _B[2]) + 12, (_B[0] + _B[2]) - 12);
                var _ec = kbr_sa_mk(_G, _ex, _B[1] + _B[3] - 2, obj_knight_weird_circle);
                _ec.difficulty = 0;
                _ec.alarm[1] = 30;
            }
            _G.end_t = 160;
            break;
        default:
            _G.dead = true;
            break;
    }
    return 1;
}

function kbr_sa_sfx(_s, _p)
{
    if (!kbr_snd_gate(_s))
        return -1;
    return snd_play(_s, KBR_SENT_GAIN, _p);
}

// one tracking sword from direction _d (it holds _len from your SOUL while it fades in, as obj_tracking_swords_manager's)
function kbr_sa_sword(_G, _d)
{
    var _S = kbr_sa_soul();
    var _sw = kbr_sa_mk(_G, _S[0] + lengthdir_x(120, _d), _S[1] + lengthdir_y(120, _d), obj_tracking_sword1);
    _sw.direction = _d;
    _sw.image_angle = _d + 180;
    _sw.variant = 0;
    return _sw;
}

function kbr_sa_fountain(_G, _x, _y, _sp, _i)
{
    var _b = kbr_sa_mk(_G, _x, _y, obj_roaringknight_fountain_bullet);
    _b.speed = 0;
    _b.top_speed = _sp + ((kbr_rng_int(_G.g, 21) - 10) / 100);
    _b.image_speed = _sp / 8;
    if ((_i mod 2) == 0)
    {
        _b.direction = -90;
        _b.image_angle = 180;
    }
    else
        _b.direction = 90;
    return _b;
}

// KNIGHTMARE's rounds: the rotating slash's aim (its markers turn and redden), then its slashes, as
// obj_knight_rotating_slash does them (slash_base 18 -> 15, slash_offset 6 -> 0, 1 / 2 / 3 slashes)
function kbr_sa_knightmare(_G, _t, _B, _S)
{
    var _M = kbr_match();
    if (_t == 0)
    {
        _M.flash = 12;
        kbr_sa_sfx(snd_knight_jump_quick, 1);
        _G.a = 0;
        _G.b = 8;
        _G.c = 0;
    }
    // _G.a: the round (0-2), _G.b: when its aim starts, _G.c: its markers
    var _n = _G.a + 1;
    var _len = (_G.a == 0) ? 30 : ((_G.a == 1) ? 26 : 22);
    if (_G.a < 3 && _t == _G.b)
    {
        var _mk = kbr_sa_tel(_G, "mark", _S[0], _S[1], _len, kbr_rng_int(_G.g, 360));
        _mk.n = _n;
        _mk.sp = kbr_rng_int(_G.g, 2) ? 1 : -1;
        _G.c = _mk;
        var _ci = kbr_sa_mk(_G, _S[0], _S[1], obj_knight_circle);
        if (_G.loop >= 0)
            audio_stop_sound(_G.loop);
        _G.loop = audio_play_sound(snd_knight_rotatingslash_line, 50, true);
        audio_sound_gain(_G.loop, KBR_SENT_GAIN, 0);
    }
    if (_G.a < 3 && _t == _G.b + _len && is_struct(_G.c))
    {
        if (_G.loop >= 0)
        {
            audio_stop_sound(_G.loop);
            _G.loop = -1;
        }
        kbr_sa_sfx(snd_knight_cut, 1);
        kbr_sa_sfx(snd_explosion_firework, 1);
        var _mk2 = _G.c;
        for (var _a = 0; _a < _n; _a++)
        {
            var _dir = ((360 / (_n * 2)) * _a) + _mk2.a + _mk2.rot;
            var _sl = kbr_sa_mk(_G, _mk2.x, _mk2.y, obj_roaringknight_slash);
            _sl.direction = _dir;
            _sl.image_xscale = 2;
            _sl.image_angle = _dir;
            _sl.visible = false;
            _sl.width *= 2;
            _sl.aoe = true;
            kbr_sa_in(_G);
            with (instance_create(_mk2.x, _mk2.y, obj_particle_generic))
            {
                depth += 100;
                sprite_index = spr_knight_slash_mark;
                image_blend = merge_color(c_red, kbrcol, KBR_SENT_TINT);
                image_angle = _dir;
                image_xscale = 6;
                image_yscale = 2.5;
                scr_lerpvar("image_xscale", image_xscale, 0, 4);
                scr_lerpvar("image_yscale", image_yscale, 0, 4);
                scr_script_delayed(instance_destroy, 4);
            }
            kbr_sa_out();
        }
        _G.a++;
        _G.b = _t + 14;
        _G.c = 0;
    }
    _G.end_t = 150;
    return 1;
}

// ---------- the telegraphs and the sent slashes (the hub controller's Draw, under the HUD) ----------
function kbr_sa_draw()
{
    if (array_length(global.kbr_sa) == 0 || !instance_exists(obj_growtangle) || instance_find(obj_growtangle, 0).x < -1000)
        return 0;
    var _B = kbr_sa_box();
    var _slashes = false;
    for (var _i = 0; _i < array_length(global.kbr_sa); _i++)
    {
        var _G = global.kbr_sa[_i];
        for (var _j = array_length(_G.tel) - 1; _j >= 0; _j--)
        {
            var _T = _G.tel[_j];
            var _u = _G.t - _T.t0;
            if (_u > _T.d)
            {
                array_delete(_G.tel, _j, 1);
                continue;
            }
            switch (_T.k)
            {
                case "rainbow":
                    // DRBR: LAST JARONA's charge - Flowery at the copy's place, rainbow afterimages growing out of him every 4 frames
                    // (Chapter 5's make_bwoosh colours: make_color_hsv(((1 + ((t / 4) mod 6)) / 7) * 255, 255, 255))
                    var _al3 = min(1, _u / 6) * min(1, (_T.d - _u) / 4) * 0.9;
                    for (var _q = 0; _q < 3; _q++)
                    {
                        var _uu = (_u + (_q * 4)) mod 12;
                        var _amp = 1 + ((_uu / 12) * (0.25 + (_u / 160)));
                        var _hc = make_color_hsv(((1 + (((_u div 4) + _q) mod 6)) / 7) * 255, 255, 255);
                        draw_sprite_ext(_T.spr, 0, _T.x, _T.y, _T.xs * _amp, abs(_T.xs) * _amp, 0, _hc, _al3 * (1 - (_uu / 12)) * 0.7);
                    }
                    draw_sprite_ext(_T.spr, _u div 4, _T.x, _T.y + (random_range(-1, 1) * (_u / 40)), _T.xs, abs(_T.xs), 0, merge_color(c_white, _G.col, 0.35), _al3);
                    break;
                case "spr":
                    // DRBR: a boss's phantom (its real sprite) beside the box while its send starts - DRBR 1.0.3: in the sender's
                    // colour as the send's pieces are (its picture, the colour drawn over it)
                    var _al2 = min(1, _u / 6) * min(1, (_T.d - _u) / 6) * 0.75;
                    var _fr2 = min(sprite_get_number(_T.spr) - 1, _u div 4);
                    draw_sprite_ext(_T.spr, _fr2, _T.x, _T.y, _T.xs, abs(_T.xs), 0, c_white, _al2);
                    gpu_set_fog(true, kfo_col_text(_G.col), 0, 0);
                    draw_sprite_ext(_T.spr, _fr2, _T.x, _T.y, _T.xs, abs(_T.xs), 0, c_white, _al2 * KBR_OV_A);
                    gpu_set_fog(false, c_black, 0, 0);
                    break;
                case "ph":
                    // the sender's knight (its real sprite), fading in and out at its side of the box - in the sender's own colour
                    // (1.0.1: a pale one read as a grey creature beside the bosses)
                    var _al = min(1, _u / 6) * min(1, (_T.d - _u) / 6) * 0.75;
                    draw_sprite_ext(spr_roaringknight_attack_ol, min(5, _u div 3), _T.x, _T.y + (sin(_u * 0.2) * 2), (_T.a == 180) ? 2 : -2, 2, 0, merge_color(c_white, _G.col, 0.85), _al);
                    break;
                case "seam":
                    // the box splitting along the seam: a white line that thickens, then the break
                    var _w = 1 + ((_u / _T.d) * 3);
                    draw_set_alpha((((_u div 2) mod 2) == 0) ? 1 : 0.6);
                    draw_line_width_color(_T.x - _T.a, _T.y, _T.x + _T.a, _T.y, _w, c_white, merge_color(c_white, _G.col, 0.5));
                    draw_set_alpha(1);
                    break;
                case "mark":
                    // the rotating slash's markers: they turn (fast, then slow) and go from grey to red
                    var _rot = 0;
                    var _r = 16;
                    for (var _q = 0; _q < _u; _q++)
                    {
                        _rot += _r * _T.sp;
                        _r = max(2, _r - 1);
                    }
                    _T.rot = _rot;
                    var _cr = min(255, 128 + (_u * 9.142857));
                    var _cg = max(0, 128 - (_u * 9.142857));
                    var _col = merge_color(make_color_rgb(_cr, _cg, _cg), _G.col, KBR_SENT_TINT);
                    var _ys = 1 + (2 * (1 - (_u / _T.d)));
                    for (var _a = 0; _a < _T.n; _a++)
                    {
                        var _dir = ((360 / (_T.n * 2)) * _a) + _T.a + _rot;
                        draw_sprite_ext(spr_rk_quickslash_marker_gradient, 0, _T.x, _T.y, _u * 0.2, _ys, _dir, _col, 1);
                    }
                    for (var _a = 0; _a < _T.n; _a++)
                    {
                        var _dir = ((360 / (_T.n * 2)) * _a) + _T.a + _rot;
                        draw_sprite_ext(spr_rk_quickslash_marker, 0, _T.x, _T.y, _u * 0.2, _ys, _dir, c_black, 1);
                    }
                    break;
            }
        }
    }
    with (obj_roaringknight_slash)
    {
        if (variable_instance_exists(id, "kbrx") && kbrx > 0 && variable_instance_exists(id, "kbrcol"))
            _slashes = true;
    }
    if (!_slashes)
        return 1;
    // the sent slashes, drawn inside the box as the rotating slash draws its own
    var _l = _B[0] - _B[2];
    var _tp = _B[1] - _B[3];
    var _sw = max(8, (_B[2] * 2) - 8);
    var _sh = max(8, (_B[3] * 2) - 8);
    if (global.kbr_sa_surf == -1 || !surface_exists(global.kbr_sa_surf))
        global.kbr_sa_surf = surface_create(_sw, _sh);
    else if (surface_get_width(global.kbr_sa_surf) != _sw || surface_get_height(global.kbr_sa_surf) != _sh)
        surface_resize(global.kbr_sa_surf, _sw, _sh);
    surface_set_target(global.kbr_sa_surf);
    draw_clear_alpha(c_black, 0);
    var _ox = _l + 5;
    var _oy = _tp + 5;
    with (obj_roaringknight_slash)
    {
        if (variable_instance_exists(id, "kbrx") && kbrx > 0 && variable_instance_exists(id, "kbrcol"))
        {
            var hx = lengthdir_x(640, direction);
            var hy = lengthdir_y(640, direction);
            var hxoff = lengthdir_x(width, direction + 90);
            var hyoff = lengthdir_y(width, direction + 90);
            var color = merge_color(make_color_rgb(255, (1 - image_alpha) * 255, (1 - image_alpha) * 255), kbrcol, KBR_SENT_TINT);
            if (slashdir)
                draw_triangle_color((x - _ox) - (hx * image_alpha), (y - _oy) - (hy * image_alpha), (x - _ox) + hx + hxoff, (y - _oy) + hy + hyoff, ((x - _ox) + hx) - hxoff, ((y - _oy) + hy) - hyoff, color, color, color, false);
            else
                draw_triangle_color((x - _ox) + (hx * image_alpha), (y - _oy) + (hy * image_alpha), ((x - _ox) - hx) + hxoff, ((y - _oy) - hy) + hyoff, (x - _ox) - hx - hxoff, (y - _oy) - hy - hyoff, color, color, color, false);
        }
    }
    surface_reset_target();
    draw_surface(global.kbr_sa_surf, _ox, _oy);
    return 1;
}

// ---------- the host's hidden copies for its bots (they dodge these; nobody sees them) ----------
// the new items' patterns as twin bullets around a bot's SOUL (_hx, _hy): the same shapes and timings as the real ones
function kbr_sa_bot(_s, _hx, _hy, _bx, _g, _art)
{
    var _bw = abs(_bx.sprite_width) / 2;
    var _bh = abs(_bx.sprite_height) / 2;
    var _d = kbr_skill_dmg(_s.sid);
    // DRBR: Flowery's: a bot plays his attacks by the odds (kbr_fl_bot_tick) - a send at it is more of them
    if (kbr_fl_is_send(_s.sid))
    {
        kbr_fl_bot_send(_s, _d);
        return 1;
    }
    // DRBR: Spamton NEO's (online_spamton53.gml)
    if (kbr_sn_is_send(_s.sid))
    {
        kbr_sn_sa_bot(_s, _hx, _hy, _bx, _g, _d);
        return 1;
    }
    // DRBR: Pink's (online_pink53.gml)
    if (kbr_pk_is_send(_s.sid))
    {
        kbr_pk_sa_bot(_s, _hx, _hy, _bx, _g, _d);
        return 1;
    }
    switch (_s.sid)
    {
        // DRBR: Gerson's (his own sprites): hammers arcing in, a shell, swings along the bot's row / column, spears from the
        // four sides, notes from two bells, one giant hammer
        case 32:
            for (var _i = 0; _i < 6; _i++)
                kbr_skill_shot((_hx + 30) + kbr_rng_int(_g, 60), _bx.y - _bh - 40, spr_hj_gerson_hammer_throw, 8 + (_i * 7), 250 + kbr_rng_int(_g, 20), 6, _d);
            break;
        case 33:
            kbr_skill_shot(_bx.x + _bw + 60, _bx.y - 20, spr_hj_bounce_shell_idle, 14, point_direction(_bx.x + _bw + 60, _bx.y - 20, _hx, _hy), 8, _d);
            break;
        case 34:
            kbr_skill_shot(_bx.x + _bw + 20, _hy, spr_hj_gerson_swing_down_telegraph2, 24, 180, 14, _d);
            kbr_skill_shot(_hx, _bx.y - _bh - 20, spr_hj_gerson_swing_down_telegraph2, 48, 270, 14, _d);
            kbr_skill_shot(_bx.x - _bw - 20, _hy, spr_hj_gerson_swing_down_telegraph2, 72, 0, 14, _d);
            break;
        case 35:
            for (var _i = 0; _i < 8; _i++)
            {
                var _sd = kbr_rng_int(_g, 4) * 90;
                kbr_skill_shot(_hx + lengthdir_x(200, _sd + 180), _hy + lengthdir_y(200, _sd + 180), spr_hj_spear_arrow, 24 + (_i * 14), _sd, 5, _d);
            }
            break;
        case 36:
            for (var _j = 0; _j < 4; _j++)
            {
                var _bsx = (_j mod 2) ? (_bx.x + _bw + 40) : (_bx.x - _bw - 40);
                for (var _k = 0; _k < 7; _k++)
                    kbr_skill_shot(_bsx, _bx.y - _bh - 30, spr_hj_gerson_musical_note2, 16 + (_j * 38), ((_j mod 2) ? 200 : 340) + ((_k - 3) * 14), 4, _d);
            }
            break;
        case 37:
            kbr_skill_shot(_hx, _bx.y - _bh - 120, spr_hj_gerson_hammer_throw, 40, 270, 12, _d);
            break;
        // build 52: Jevil's (his own sprites)
        case 26:
            var _a0 = kbr_rng_int(_g, 360);
            for (var _i = 0; _i < 8; _i++)
            {
                var _sa = _a0 + (_i * 45);
                var _sh = kbr_skill_shot(_bx.x + lengthdir_x(110, _sa), _bx.y + lengthdir_y(110, _sa), spr_jv_spadebullet, 20 + (_i * 5), _sa + 180, 5, _d);
                _sh.aim = false;
            }
            break;
        case 27:
            for (var _i = 0; _i < 10; _i++)
                kbr_skill_shot((_hx + kbr_rng_int(_g, 201)) - 100, _bx.y + _bh + 30, spr_jv_diamondbullet_vert, 10 + (_i * 5), 90, 7, _d);
            break;
        case 28:
            for (var _i = 0; _i < 4; _i++)
            {
                var _ca = 45 + (90 * _i);
                for (var _q = -1; _q <= 1; _q++)
                    kbr_skill_shot(_hx + lengthdir_x(150, _ca), _hy + lengthdir_y(150, _ca), spr_jv_clubsball_b, 18 + (_i * 18), _ca + 180 + (_q * 17), 5, _d);
            }
            break;
        case 29:
            for (var _i = 0; _i < 7; _i++)
                kbr_skill_shot(_bx.x + _bw + 30 + (_i * 30), _hy, spr_jv_carousel, 20, 180, 4, _d);
            break;
        case 30:
            for (var _i = 0; _i < 4; _i++)
            {
                var _sa2 = (_i * 90) + kbr_rng_int(_g, 90);
                kbr_skill_shot(_bx.x + lengthdir_x(150, _sa2), _bx.y + lengthdir_y(150, _sa2), spr_jv_joker_scythebody, 24, _sa2 + 180, 4, _d);
            }
            break;
        case 31:
            for (var _j = 0; _j < 3; _j++)
            {
                var _ex = _bx.x + ((kbr_rng_int(_g, 2) ? 1 : -1) * (_bw + 30));
                var _ey = (_bx.y - _bh) + kbr_rng_int(_g, _bh * 2);
                var _aim = point_direction(_ex, _ey, _hx, _hy);
                for (var _k = 0; _k < 6; _k++)
                    kbr_skill_shot(_ex, _ey, spr_jv_spadebullet, 20 + (_j * 14), _aim + (_k * 60), 5, _d);
            }
            break;
        case 17:
            for (var _v = 0; _v < 3; _v++)
            {
                var _cy = _hy + ((kbr_rng_int(_g, 3) - 1) * 20);
                kbr_skill_shot(_bx.x + _bw + 40, _cy - 9, _art.sword, 12 + (_v * 24), 180, 6, _d);
                kbr_skill_shot(_bx.x + _bw + 40, _cy + 9, _art.sword, 12 + (_v * 24), 180, 6, _d);
            }
            break;
        case 18:
            for (var _k = 0; _k < 5; _k++)
            {
                var _fx = (_hx + kbr_rng_int(_g, 97)) - 48;
                var _fy = (_bx.y - 110) + kbr_rng_int(_g, 30);
                var _sh = kbr_skill_shot(_fx, _fy, _art.sword, 24 + (_k * 12), point_direction(_fx, _fy, _hx, _hy), 12, _d);
                _sh.aim = true;
            }
            break;
        case 19:
            for (var _k = 0; _k < 4; _k++)
            {
                var _la = kbr_rng_int(_g, 180);
                var _off = kbr_rng_int(_g, 41) - 20;
                var _px = _hx + lengthdir_x(_off, _la + 90);
                var _py = _hy + lengthdir_y(_off, _la + 90);
                for (var _q = -6; _q <= 6; _q++)
                {
                    var _b = kbr_skill_shot(_px + lengthdir_x(_q * 18, _la), _py + lengthdir_y(_q * 18, _la), _art.small, 26 + (_k * 10), _la, 0, _d);
                    _b.life = 36 + (_k * 10);
                }
            }
            break;
        case 20:
            var _sy = _bx.y + ((kbr_rng_int(_g, 3) - 1) * 16);
            for (var _i = 0; _i < 14; _i++)
                kbr_skill_shot((_bx.x - 66) + (22 * (_i div 2)), _sy, _art.small, 20, ((_i mod 2) == 0) ? 270 : 90, 4 + (kbr_rng_int(_g, 2) * 4), _d);
            break;
        case 21:
            var _ex = _hx + (kbr_rng_int(_g, 41) - 20);
            for (var _a = 0; _a < 23; _a++)
                kbr_skill_shot(_ex, _bx.y + _bh, _art.small, 30, 27.5 + ((31.25 * _a) / 2), 4, _d);
            for (var _a = 0; _a < 22; _a++)
                kbr_skill_shot(_ex, _bx.y + _bh, _art.small, 30, 40 + ((33.333333 * _a) / 2), 6, _d);
            break;
    }
    return 1;
}

// build 52: a choice from the send's own random stream (kbr_choose draws from the shared one)
function kbr_choose_g(_g, _a, _b)
{
    return kbr_rng_int(_g, 2) ? _b : _a;
}
