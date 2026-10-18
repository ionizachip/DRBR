// ===== DRBR - DELTARUNE BATTLE ROYALE (build 51 update 9) =====
// The projectile contract. Every bullet a SOUL can touch (obj_collidebullet and its children) must have the fields that
// obj_collidebullet's events read before its first contact: destroyonhit, damage, target, inv, element, grazed, grazetimer,
// grazepoints, timepoints, active, updateimageangle (Chapter 3 sets them in scr_bullet_init, from each bullet's Create).
//
// THE CRASH THIS IS FOR ("Variable obj_collidebullet.destroyonhit not set before reading it", obj_collidebullet's user
// event 5, from obj_heart's collision): Jevil's pieces come from Chapter 1, where a plain obj_collidebullet made by
// instance_create was a complete bullet - Chapter 1's user event 5 always destroyed it and never read destroyonhit. Chapter
// 3's user event 5 reads destroyonhit, which only scr_bullet_init sets; obj_collidebullet has no Create of its own. So the
// spade ring's spades, the teleport's diamonds / spades and the Devilsknife's blade (all plain obj_collidebullet) and the
// Diamond Rain diamonds (Chapter 1's obj_dbullet_vert Create, without scr_bullet_init) had no destroyonhit, and the first
// touch stopped the game. The emulator ran no collisions, so the tests never touched them.
// ROOT FIX: every bullet of Jevil's is made complete when it is made (kbr_jv_adopt for the plain ones, kbr_jv_vars in every
// piece's Create): Chapter 1's rule, destroyed on a hit, unless the piece has its own user event 5 (the permanent ones).
// FALLBACK (kept as well): obj_heart's and obj_grazebox's collisions and obj_collidebullet's user event 5 fill in any field
// still missing, with scr_bullet_init's values, and count it (global.kbr_bfix: object -> times; the tests fail on any).

function kbr_bullet_contract(_dh)
{
    // the missing fields only (a bullet's own values stay), Chapter 3's scr_bullet_init values; _dh: destroyed on a hit
    if (!variable_instance_exists(id, "destroyonhit"))
        destroyonhit = _dh;
    if (!variable_instance_exists(id, "grazed") || grazed == -1)
        grazed = 0;
    if (!variable_instance_exists(id, "grazetimer") || grazetimer == -1)
        grazetimer = 0;
    if (!variable_instance_exists(id, "target"))
        target = 0;
    if (!variable_instance_exists(id, "inv"))
        inv = 60;
    if (!variable_instance_exists(id, "damage"))
        damage = 10;
    if (!variable_instance_exists(id, "element"))
        element = 0;
    if (!variable_instance_exists(id, "grazepoints"))
        grazepoints = 1;
    if (!variable_instance_exists(id, "timepoints"))
        timepoints = 1;
    if (!variable_instance_exists(id, "active"))
        active = 1;
    if (!variable_instance_exists(id, "updateimageangle"))
        updateimageangle = 0;
    return id;
}

// the fallback at the moment of contact: the same fields, counted when one was missing (a bullet that breaks the contract)
function kbr_bullet_fix()
{
    if (variable_instance_exists(id, "destroyonhit") && variable_instance_exists(id, "active") && variable_instance_exists(id, "target")
        && variable_instance_exists(id, "grazed") && variable_instance_exists(id, "grazepoints") && variable_instance_exists(id, "timepoints")
        && variable_instance_exists(id, "inv") && variable_instance_exists(id, "damage") && variable_instance_exists(id, "element")
        && variable_instance_exists(id, "grazetimer"))
        return 0;
    if (!variable_global_exists("kbr_bfix") || !is_struct(global.kbr_bfix))
        global.kbr_bfix = {};
    var _n = object_get_name(object_index);
    variable_struct_set(global.kbr_bfix, _n, (variable_struct_exists(global.kbr_bfix, _n) ? variable_struct_get(global.kbr_bfix, _n) : 0) + 1);
    kbr_bullet_contract(1);
    return 1;
}

// ---------- DRBR branding: the window title while in a room (the game's own one is put back on leaving) ----------
function kfo_caption_tick()
{
    var _want = "";
    if (variable_global_exists("kfo") && is_struct(global.kfo) && kfo_in_room())
        _want = "DRBR - DELTARUNE Battle Royale";
    if (!variable_global_exists("kfo_cap_was"))
    {
        global.kfo_cap_was = "";
        global.kfo_cap_base = "";
    }
    if (_want != global.kfo_cap_was)
    {
        if (global.kfo_cap_was == "")
            global.kfo_cap_base = window_get_caption();
        window_set_caption((_want != "") ? _want : global.kfo_cap_base);
        global.kfo_cap_was = _want;
    }
    return _want;
}

// ---------- DRBR: boss FAMILIES (who you fight, and whose attacks you send) ----------
// fid: 1 KNIGHT (every Roaring Knight row), 2 JEVIL, 4 SPAMTON, 5 GERSON, 6 PINK, 7 FLOWERY. In SENDS (the skfam setting) 0 is
// MATCH CURRENT BOSS and 3 is ALL ENABLED, so a fixed family's setting value is its fid (1 / 2 were build 52's KNIGHT / JEVIL:
// saved rooms keep their meaning).
#macro KBR_FAM_KNIGHT 1
#macro KBR_FAM_JEVIL 2
#macro KBR_FAM_ALL 3
#macro KBR_FAM_SPAMTON 4
#macro KBR_FAM_GERSON 5
#macro KBR_FAM_PINK 6
#macro KBR_FAM_FLOWERY 7

function kbr_fam_defs()
{
    if (variable_global_exists("kbr_fam_t") && is_array(global.kbr_fam_t))
        return global.kbr_fam_t;
    global.kbr_fam_t = [
        { fid: KBR_FAM_KNIGHT, key: "knight", name: "KNIGHT", long: "THE KNIGHTS", col: make_color_rgb(150, 190, 255), chapter: 3 },
        { fid: KBR_FAM_JEVIL, key: "jevil", name: "JEVIL", long: "JEVIL", col: make_color_rgb(200, 140, 255), chapter: 1 },
        { fid: KBR_FAM_SPAMTON, key: "spamton", name: "SPAMTON", long: "SPAMTON NEO", col: make_color_rgb(255, 120, 200), chapter: 2 },
        { fid: KBR_FAM_GERSON, key: "gerson", name: "GERSON", long: "GERSON", col: make_color_rgb(120, 220, 140), chapter: 4 },
        { fid: KBR_FAM_PINK, key: "pink", name: "PINK", long: "PINK", col: make_color_rgb(255, 150, 210), chapter: 5 },
        { fid: KBR_FAM_FLOWERY, key: "flowery", name: "FLOWERY", long: "FLOWERY", col: make_color_rgb(255, 210, 90), chapter: 5 }
    ];
    return global.kbr_fam_t;
}

function kbr_fam_def(_fid)
{
    var _l = kbr_fam_defs();
    for (var _i = 0; _i < array_length(_l); _i++)
    {
        if (_l[_i].fid == _fid)
            return _l[_i];
    }
    return undefined;
}

function kbr_fam_name(_fid)
{
    var _f = kbr_fam_def(_fid);
    return is_struct(_f) ? _f.name : "?";
}

function kbr_fam_col(_fid)
{
    var _f = kbr_fam_def(_fid);
    return is_struct(_f) ? _f.col : c_white;
}

// a family can be fought / sent in this build: the knights always; a boss family when one of its encounters is ready
function kbr_fam_ready(_fid)
{
    if (_fid == KBR_FAM_KNIGHT)
        return true;
    var _d = kbr_enc_defs();
    for (var _i = 0; _i < array_length(_d); _i++)
    {
        if (_d[_i].fid == _fid && kbr_enc_ready(_d[_i]))
            return true;
    }
    return false;
}

// the family of an online id (a roster row)
function kbr_fam_of_ok(_ok)
{
    var _en = kbr_ok_enc(_ok);
    return is_struct(_en) ? _en.fid : KBR_FAM_KNIGHT;
}

// the family of the boss on stage now (the lineup's active entry); before a battle: the match's opening boss
function kbr_fam_now(_e)
{
    if (variable_global_exists("knight_lu") && is_struct(global.knight_lu) && variable_struct_exists(global.knight_lu, "ready") && global.knight_lu.ready)
    {
        var _lu = global.knight_lu;
        var _ks = _lu.ks[clamp(_lu.act, 0, array_length(_lu.ks) - 1)];
        if (is_numeric(_ks) && _ks >= KBR_ENC_BASE)
        {
            var _d = kbr_enc_of_lu(_ks);
            return is_struct(_d) ? _d.fid : KBR_FAM_KNIGHT;
        }
        return KBR_FAM_KNIGHT;
    }
    var _ok = (is_struct(_e) && variable_struct_exists(_e, "open")) ? _e.open : 0;
    return kbr_fam_of_ok(_ok);
}

// the SENDS setting's choices in this build, in the order the setting steps through them
function kbr_sends_modes()
{
    var _l = [0, KBR_FAM_ALL];
    var _f = kbr_fam_defs();
    for (var _i = 0; _i < array_length(_f); _i++)
    {
        if (kbr_fam_ready(_f[_i].fid))
            array_push(_l, _f[_i].fid);
    }
    return _l;
}

function kbr_sends_label(_v)
{
    if (_v == 0)
        return "MATCH CURRENT BOSS";
    if (_v == KBR_FAM_ALL)
        return "ALL ENABLED";
    return kbr_fam_name(_v) + " ONLY";
}

// which family each skill id belongs to (0: an effect / a green skill - any family): the knights' attack skills, and every
// boss's "sends" list from its encounter entry
function kbr_skill_fams()
{
    if (variable_global_exists("kbr_skfam_t") && is_array(global.kbr_skfam_t) && array_length(global.kbr_skfam_t) == kbr_skill_count())
        return global.kbr_skfam_t;
    var _t = array_create(kbr_skill_count(), 0);
    var _kn = [1, 2, 3, 4, 5, 6, 7, 10, 17, 18, 19, 20, 21];
    for (var _i = 0; _i < array_length(_kn); _i++)
    {
        if (_kn[_i] < array_length(_t))
            _t[_kn[_i]] = KBR_FAM_KNIGHT;
    }
    var _d = kbr_enc_defs();
    for (var _i = 0; _i < array_length(_d); _i++)
    {
        if (!variable_struct_exists(_d[_i], "sends"))
            continue;
        for (var _j = 0; _j < array_length(_d[_i].sends); _j++)
        {
            var _sid = _d[_i].sends[_j];
            if (_sid >= 0 && _sid < array_length(_t))
                _t[_sid] = _d[_i].fid;
        }
    }
    global.kbr_skfam_t = _t;
    return _t;
}

// ---------- DRBR: the INCOMING indicator (the sends aimed at you), left of the box under your skills ----------
// One compact list, only while something is coming: who sent it (their colour and name), its family, the attack, and how
// long it has left (a bar; WAITING while it waits for the boss's next attack to run). Its header: how many players target
// you now, and the pressure (the damage of everything incoming: green / yellow / red). Players' sends are drawn in their
// sender's colour in the box as well - the boss's own bullets never are, so the two can always be told apart.
function kbr_pname(_pid)
{
    var _M = kbr_match();
    if (is_undefined(_M))
        return "?";
    for (var _i = 0; _i < array_length(_M.players); _i++)
    {
        if (kfo_jn(_M.players[_i], "pid", -2) == _pid)
            return kfo_js(_M.players[_i], "n", "?");
    }
    return "?";
}

// what is coming at me: [{ from, sid, t (0..1 done; -1 waiting) }], the oldest first
function kbr_incoming_list(_M)
{
    var _o = [];
    var _S = _M.sk;
    if (variable_struct_exists(_S, "pend"))
    {
        for (var _i = 0; _i < array_length(_S.pend); _i++)
        {
            var _p = _S.pend[_i];
            var _f = variable_struct_exists(_p, "from") ? _p.from : -1;
            if (_f != global.kfo.my)
                array_push(_o, { from: _f, sid: _p.sid, t: -1 });
        }
    }
    if (variable_global_exists("kbr_sa") && is_array(global.kbr_sa))
    {
        for (var _i = 0; _i < array_length(global.kbr_sa); _i++)
        {
            var _G = global.kbr_sa[_i];
            if (_G.dead || _G.twin || (variable_struct_exists(_G, "watch") && _G.watch) || _G.tg != global.kfo.my || _G.from == global.kfo.my)
                continue;
            array_push(_o, { from: _G.from, sid: _G.sid, t: clamp(_G.t / max(1, _G.end_t), 0, 1) });
        }
    }
    return _o;
}

function kbr_hud_incoming(xx, yy, _M)
{
    if (!_M.me || _M.out || !variable_struct_exists(_M, "sk"))
        return 0;
    var _l = kbr_incoming_list(_M);
    var _natt = (variable_struct_exists(_M, "tg") && is_struct(_M.tg)) ? array_length(_M.tg.att) : 0;
    if (array_length(_l) == 0 && _natt == 0)
        return 0;
    // never over the box: the list ends 10 px left of it
    var _x = xx + 16;
    var _w = 214;
    with (obj_growtangle)
        _w = clamp((bbox_left - xx) - 10 - 16, 120, 214);
    var _y = yy + 122;
    draw_set_font(fnt_small);
    draw_set_halign(fa_left);
    // the header: who has you targeted, the pressure
    var _pr = 0;
    for (var _i = 0; _i < array_length(_l); _i++)
        _pr += kbr_skill_dmg(_l[_i].sid);
    var _pc = (_pr >= 60) ? make_color_rgb(255, 80, 80) : ((_pr >= 25) ? make_color_rgb(255, 210, 70) : make_color_rgb(110, 230, 120));
    var _hd = (_natt > 0) ? ("TARGETED BY " + string(_natt)) : "INCOMING";
    kbr_hud_text(_x, _y, _hd, (_natt > 0) ? make_color_rgb(255, 120, 120) : c_white);
    if (array_length(_l) > 0)
    {
        // the pressure bar after the header
        var _bx = _x + string_width(_hd) + 8;
        var _bw = max(20, (_x + _w) - _bx);
        draw_set_color(c_dkgray);
        draw_rectangle(_bx, _y + 3, _bx + _bw, _y + 8, false);
        draw_set_color(_pc);
        draw_rectangle(_bx, _y + 3, _bx + (_bw * clamp(_pr / 90, 0.08, 1)), _y + 8, false);
    }
    _y += 14;
    var _shown = min(array_length(_l), 4);
    for (var _i = 0; _i < _shown; _i++)
    {
        var _e = _l[_i];
        var _pc2 = kbr_pcol(kbr_pslot(_e.from));
        var _fam = kbr_skill_family(_e.sid);
        // the sender's colour, their name, then the attack in its family's colour
        draw_set_color(_pc2);
        draw_rectangle(_x, _y + 2, _x + 7, _y + 9, false);
        var _nm = kbr_fit(string_upper(kbr_pname(_e.from)), 64);
        kbr_hud_text(_x + 11, _y, _nm, _pc2);
        var _sx = _x + 11 + 66;
        kbr_hud_text(_sx, _y, kbr_fit(kbr_skill_short(_e.sid), 52), (_fam != 0) ? kbr_fam_col(_fam) : c_white);
        // its time: a bar running down (WAITING: it lands when the boss's next attack starts)
        var _tx = _sx + 56;
        var _tw = max(16, (_x + _w) - _tx);
        if (_e.t < 0)
        {
            draw_set_alpha(0.55 + (0.45 * abs(sin(current_time / 180))));
            kbr_hud_text(_tx, _y, kbr_fit("WAITING", _tw), c_gray);
            draw_set_alpha(1);
        }
        else
        {
            draw_set_color(c_dkgray);
            draw_rectangle(_tx, _y + 3, _tx + _tw, _y + 8, false);
            draw_set_color(_pc2);
            draw_rectangle(_tx, _y + 3, _tx + (_tw * (1 - _e.t)), _y + 8, false);
        }
        _y += 13;
    }
    if (array_length(_l) > _shown)
        kbr_hud_text(_x + 11, _y, "+" + string(array_length(_l) - _shown) + " MORE", c_gray);
    draw_set_color(c_white);
    draw_set_alpha(1);
    return 1;
}

// ---------- DRBR: the encounter table's shared helpers (every boss after Jevil uses these) ----------
// an encounter by its key (undefined when this build has none)
function kbr_enc_by_key(_k)
{
    var _d = kbr_enc_defs();
    for (var _i = 0; _i < array_length(_d); _i++)
    {
        if (_d[_i].key == _k)
            return _d[_i];
    }
    return undefined;
}

// the encounter on stage is _k
function kbr_enc_is(_k)
{
    var _d = kbr_enc_now();
    return is_struct(_d) && _d.key == _k;
}

// every piece of a boss ends its Create with this: what Chapter 3's battle code reads (scr_bullet_inherit reads them from its
// caller; -1 = "not passed on", as Chapter 3's obj_dbulletcontroller sets them) - and a bullet is complete (the contract)
function kbr_bvars()
{
    var _l = ["damage", "grazepoints", "timepoints", "inv", "target", "grazed", "grazetimer"];
    for (var _i = 0; _i < array_length(_l); _i++)
    {
        if (!variable_instance_exists(id, _l[_i]))
            variable_instance_set(id, _l[_i], -1);
    }
    if (!variable_instance_exists(id, "element"))
        element = 0;
    if (!variable_instance_exists(id, "creatorid"))
        creatorid = id;
    if (!variable_instance_exists(id, "creator"))
        creator = id;
    if (object_is_ancestor(object_index, obj_collidebullet))
        kbr_bullet_contract(1);
    return 1;
}

// DRBR 1.0.1: your own music plays over everything. With a song picked (MORE OPTIONS > MUSIC, or the hub's FIGHT SONG left on
// AS IN THE HUB) the bosses and the match's big moments do not change it; DEFAULT lets each boss bring its own music (as Tag
// Team's knight_mus_takeover: a chosen song plays on)
function kbr_mus_own()
{
    return is_struct(global.krun) && variable_struct_exists(global.krun, "cfg") && is_struct(global.krun.cfg) && knight_cfg_num(global.krun.cfg, "song") != 0;
}

// the boss's music while it is on stage, the match's song after - every encounter with a "music" file, Jevil's too (1.0.1: one
// place decides, so one boss after another never queues two songs at once). Back with the knights: the match's song, or the
// song of a big moment that came while a boss was on (kfo_mus_situ keeps the boss's music meanwhile)
function kbr_enc_music()
{
    var _M = kbr_match();
    if (is_undefined(_M) || kbr_mus_own())
        return 0;
    if (!variable_struct_exists(_M, "encmus"))
    {
        _M.encmus = "";
        _M.encmus_old = "";
    }
    var _d = kbr_enc_now();
    var _want = (is_struct(_d) && variable_struct_exists(_d, "music")) ? _d.music : "";
    if (_want == _M.encmus || !knight_mus_ok())
        return 0;
    if (_want != "")
    {
        if (!knight_music_exists(_want))
        {
            _M.encmus = _want;
            return 0;
        }
        if (_M.encmus == "")
            _M.encmus_old = knight_mus_cur_file();
        _M.encmus = _want;
        var _old = global.batmusic[0];
        knight_mus_cut_ext(15, true);
        array_push(global.knight_mus_q, { k: "song", file: _want, old: _old, fin: 30, t: 16 });
    }
    else
    {
        _M.encmus = "";
        var _back = _M.encmus_old;
        if (variable_struct_exists(_M, "situ") && _M.situ != "")
            _back = kfo_mus_situ_file(_M.situ);
        // (no song was known when the boss came on: the knight's own, as its fight starts it)
        if ((_back == "" || !knight_music_exists(_back)) && is_struct(global.knight_lu) && global.knight_lu.ready)
        {
            var _k = global.knight_lu.ks[global.knight_lu.act];
            if (is_numeric(_k) && _k < KBR_ENC_BASE)
                _back = knight_mus_default_file(_k);
        }
        if (_back == "" || !knight_music_exists(_back))
            return 0;
        var _old2 = global.batmusic[0];
        knight_mus_cut_ext(15, true);
        array_push(global.knight_mus_q, { k: "song", file: _back, old: _old2, fin: 30, t: 16 });
    }
    return 1;
}

// the attack's end (kbr_cut) and the match's end (kbr_end_clean): every boss's pieces that are not bullets (no parent: the
// cut's own clean-up never sees them), then its own clean-up (the SOUL's mode, the box) - a player's send (kbrx) lives on
function kbr_enc_cut(_all)
{
    var _d = kbr_enc_defs();
    for (var _i = 0; _i < array_length(_d); _i++)
    {
        var _e = _d[_i];
        if (variable_struct_exists(_e, "objs"))
        {
            for (var _j = 0; _j < array_length(_e.objs); _j++)
            {
                with (_e.objs[_j])
                {
                    if (_all || !(variable_instance_exists(id, "kbrx") && kbrx > 0))
                        instance_destroy();
                }
            }
        }
        if (variable_struct_exists(_e, "cut"))
            script_execute(_e.cut, _all);
    }
    return 1;
}

// ---------- a boss's speech balloon (1.0.1) ----------
// Off unless VIEW > BOSS LINES is on (the balloons were over the battle; the bosses' voices play either way). On: Deltarune's
// own balloon (spr_battleblcon_long's shape at any size: white, rounded, its curved tail pointing at the speaker; black DotumChe
// in the battle balloons' 9 x 20 spacing), put beside the speaker where it covers neither the battle box nor the HUD: left of
// them (the game's own side), else below, right or above them - else wherever it covers the box least.
// (_l, _t, _r, _b): the speaker's body on the screen; "&" breaks lines; faded by _a.
function kbr_blines_on()
{
    return (kfo_view().blines == 1);
}

// the battle box as the balloon keeps away from it (with its frame and a little room), or undefined
function kbr_bl_box()
{
    if (kbr_jv_boxless() || !instance_exists(obj_growtangle))
        return undefined;
    var _g = instance_find(obj_growtangle, 0);
    if (_g.x < -1000 || !_g.visible)
        return undefined;
    var _hw = (abs(_g.sprite_width) / 2) + 10;
    var _hh = (abs(_g.sprite_height) / 2) + 10;
    return [_g.x - _hw, _g.y - _hh, _g.x + _hw, _g.y + _hh];
}

// what the instance's sprite covers drawn at (_xx, _yy) with its scale (mirrored: it reaches the other way) - a stand-in that
// shows a boss during an attack (its balloon points there)
function kbr_bl_spr_rect(_xx, _yy)
{
    var _sw = sprite_get_width(sprite_index);
    var _sh = sprite_get_height(sprite_index);
    var _ox = sprite_get_xoffset(sprite_index);
    var _oy = sprite_get_yoffset(sprite_index);
    var _l = (image_xscale >= 0) ? (_xx - (_ox * image_xscale)) : (_xx - ((_sw - _ox) * -image_xscale));
    var _t = (image_yscale >= 0) ? (_yy - (_oy * image_yscale)) : (_yy - ((_sh - _oy) * -image_yscale));
    return [_l, _t, _l + max(40, _sw * abs(image_xscale)), _t + max(40, _sh * abs(image_yscale))];
}

// how much two [l, t, r, b] rectangles cover of each other
function kbr_bl_ov(_p, _q)
{
    if (is_undefined(_p) || is_undefined(_q))
        return 0;
    var _w = min(_p[2], _q[2]) - max(_p[0], _q[0]);
    var _h = min(_p[3], _q[3]) - max(_p[1], _q[1]);
    return (_w > 0 && _h > 0) ? (_w * _h) : 0;
}

// a balloon's place: [left, top, kind (0 left of the speaker, the tail pointing right; 1 below, tail up; 2 right, tail left; 3
// above, tail down), how much it covers (0: nothing)] for a body _bw x _bh; _sl: the body centred on the tail (0) or slid
// along it as far as the tail allows, to one end (1) or the other (2)
function kbr_bl_place(_k, _sl, _bw, _bh, _me, _box, _hud, _cx, _cy)
{
    var _l = _me[0];
    var _t = _me[1];
    var _r = _me[2];
    var _b = _me[3];
    var _mx = (_l + _r) / 2;
    var _my = _t + ((_b - _t) * 0.3);
    var _L = _mx - ((_sl == 0) ? (_bw / 2) : ((_sl == 1) ? 17 : (_bw - 16)));
    var _T = _my - ((_sl == 0) ? (_bh / 2) : ((_sl == 1) ? 17 : (_bh - 16)));
    if (_k == 0)
        _L = _l - 23 - _bw;
    else if (_k == 1)
        _T = _b + 23;
    else if (_k == 2)
        _L = _r + 23;
    else
        _T = _t - 23 - _bh;
    // on the screen, above the bottom bar (the tail stays with the body)
    _L = floor(clamp(_L, _cx + 6 + ((_k == 2) ? 21 : 0), _cx + 634 - _bw - ((_k == 0) ? 21 : 0)));
    _T = floor(clamp(_T, _cy + 6 + ((_k == 1) ? 21 : 0), _cy + 398 - _bh - ((_k == 3) ? 21 : 0)));
    var _all = [_L - ((_k == 2) ? 21 : 0), _T - ((_k == 1) ? 21 : 0), _L + _bw + ((_k == 0) ? 21 : 0), _T + _bh + ((_k == 3) ? 21 : 0)];
    var _s = (kbr_bl_ov(_all, _box) * 100) + (kbr_bl_ov(_all, _me) * 50);
    for (var _h = 0; _h < array_length(_hud); _h++)
        _s += kbr_bl_ov(_all, _hud[_h]) * 10;
    return [_L, _T, _k, _s];
}

function kbr_enc_say(_l, _t, _r, _b, _txt, _a)
{
    if (_txt == "" || _a <= 0 || !kbr_blines_on())
        return 0;
    draw_set_font(fnt_dotumche);
    var _cx = camerax();
    var _cy = cameray();
    var _me = [_l, _t, _r, _b];
    var _box = kbr_bl_box();
    // the skill slots, the boss's name, the player list (the bottom bar is below the balloon's lowest place)
    var _hud = [[_cx, _cy, _cx + 215, _cy + 140], [_cx + 240, _cy, _cx + 400, _cy + 34], [_cx + 462, _cy, _cx + 640, _cy + 70]];
    // the line exactly as the chapter has it (its own "&" breaks). A place found for this line stays while it covers nothing
    // (no jumping about as the speaker sways)
    var _keep = variable_instance_exists(id, "kbr_bl_txt") && kbr_bl_txt == _txt;
    var _best = undefined;
    var _bl = string_split(_txt, "&");
    var _tw = 0;
    for (var _i = 0; _i < array_length(_bl); _i++)
        _tw = max(_tw, string_width(_bl[_i]));
    var _bw = max(48, ceil(_tw) + 20);
    var _bh = (array_length(_bl) * 20) + 15;
    for (var _k = 0; _k < 4; _k++)
    {
        for (var _sl = 0; _sl < 3; _sl++)
        {
            if (_keep && (_k != kbr_bl_k || _sl != kbr_bl_sl))
                continue;
            var _p = kbr_bl_place(_k, _sl, _bw, _bh, _me, _box, _hud, _cx, _cy);
            var _sc = _p[3] + _k + (_sl * 0.25);
            if (is_undefined(_best) || _sc < _best[4])
                _best = [_p[0], _p[1], _k, _p[3], _sc, _bw, _bh, 0, _sl];
        }
    }
    if (_keep && _best[3] > kbr_bl_ov0)
    {
        // the kept place covers more than when it was chosen (the box moved): choose again
        kbr_bl_txt = "";
        return kbr_enc_say(_l, _t, _r, _b, _txt, _a);
    }
    if (!_keep)
        kbr_bl_ov0 = _best[3];
    kbr_bl_txt = _txt;
    kbr_bl_k = _best[2];
    kbr_bl_sl = _best[8];
    var _bL = _best[0];
    var _bT = _best[1];
    var _bk = _best[2];
    var _R = (_bL + _bw) - 1;
    var _B = (_bT + _bh) - 1;
    // the body: its rounded corners row by row, the middle in one piece (no piece over another: the fade stays even)
    var _P = [6, 4, 3, 2, 2, 1, 1];
    for (var _i = 0; _i < 7; _i++)
    {
        draw_sprite_ext(spr_pxwhite, 0, _bL + _P[_i], _bT + _i, _bw - (2 * _P[_i]), 1, 0, c_white, _a);
        draw_sprite_ext(spr_pxwhite, 0, _bL + _P[_i], _B - _i, _bw - (2 * _P[_i]), 1, 0, c_white, _a);
    }
    draw_sprite_ext(spr_pxwhite, 0, _bL, _bT + 7, _bw, _bh - 14, 0, c_white, _a);
    // the tail: how far each of its 19 rows reaches past the body (21: its tip), at the speaker's height / middle as far as the
    // straight part of that edge goes
    var _E = [1, 3, 5, 8, 8, 10, 13, 15, 19, 21, 21, 21, 21, 17, 14, 12, 9, 7, 4];
    var _ty = floor(clamp(_t + ((_b - _t) * 0.3), _bT + 17, (_bT + _bh) - 16));
    var _tx = floor(clamp((_l + _r) / 2, _bL + 17, (_bL + _bw) - 16));
    for (var _j = 0; _j < 19; _j++)
    {
        var _e = _E[_j];
        if (_bk == 0)
            draw_sprite_ext(spr_pxwhite, 0, _R + 1, (_ty - 10) + _j, _e, 1, 0, c_white, _a);
        else if (_bk == 1)
            draw_sprite_ext(spr_pxwhite, 0, (_tx - 10) + _j, _bT - _e, 1, _e, 0, c_white, _a);
        else if (_bk == 2)
            draw_sprite_ext(spr_pxwhite, 0, _bL - _e, (_ty - 10) + _j, _e, 1, 0, c_white, _a);
        else
            draw_sprite_ext(spr_pxwhite, 0, (_tx - 10) + _j, _B + 1, 1, _e, 0, c_white, _a);
    }
    draw_set_alpha(_a);
    draw_set_color(c_black);
    draw_set_halign(fa_left);
    draw_set_valign(fa_top);
    for (var _i = 0; _i < array_length(_bl); _i++)
        draw_text(_bL + 10, _bT + 10 + (_i * 20), _bl[_i]);
    draw_set_alpha(1);
    draw_set_color(c_white);
    return 1;
}

// ---------- DRBR: the bosses' pieces in the sends ----------
// Each boss def's objs are its non-bullet pieces (the knights' sends are all bullets): a send waits while one of its own is
// alive and takes them with it when it ends; when the box goes between two attacks, the pieces that read the box go (the
// def's boxy). _gx 0: every send's.
function kbr_enc_sa_alive(_gx)
{
    var _n = 0;
    var _d = kbr_enc_defs();
    for (var _i = 0; _i < array_length(_d); _i++)
    {
        if (!variable_struct_exists(_d[_i], "objs"))
            continue;
        var _l = _d[_i].objs;
        for (var _j = 0; _j < array_length(_l); _j++)
        {
            with (_l[_j])
            {
                if (variable_instance_exists(id, "kbrx") && kbrx > 0 && (_gx == 0 || kbrx == _gx))
                    _n++;
            }
        }
    }
    return _n;
}

function kbr_enc_sa_kill(_gx, _boxless)
{
    var _d = kbr_enc_defs();
    for (var _i = 0; _i < array_length(_d); _i++)
    {
        // (the send's end: all its pieces; the box gone: the ones that read it)
        var _ls = [];
        if (!_boxless && variable_struct_exists(_d[_i], "objs"))
            array_push(_ls, _d[_i].objs);
        if (_boxless && variable_struct_exists(_d[_i], "boxy"))
            array_push(_ls, _d[_i].boxy);
        for (var _k = 0; _k < array_length(_ls); _k++)
        {
            var _l = _ls[_k];
            for (var _j = 0; _j < array_length(_l); _j++)
            {
                with (_l[_j])
                {
                    if (variable_instance_exists(id, "kbrx") && kbrx > 0 && (_gx == 0 || kbrx == _gx))
                        instance_destroy();
                }
            }
        }
    }
    return 1;
}

// a send's own end (its onend, e.g. SPEAR VOLLEY putting your SOUL back) - before its pieces go
function kbr_sa_onend(_G)
{
    if (is_struct(_G) && variable_struct_exists(_G, "onend") && !variable_struct_exists(_G, "ended"))
    {
        _G.ended = true;
        script_execute(_G.onend, _G);
    }
    return 1;
}

// the SOUL's mode in this game: "red", "green" (Gerson's shield is up), "orange" (Flowery's board), "yellow" (Chapter 3's
// yellow SOUL), "other", "none"
// DRBR: the SOUL's own keys (the orange dash, the yellow shots) are off - while you watch (your SOUL is the one you follow), type
// in the chat or have the quick settings open
function kbr_soul_keys_off()
{
    if (kfo_chat_typing())
        return true;
    var _M = kbr_match();
    if (is_undefined(_M) || !kbr_on())
        return false;
    return _M.out || !_M.me || (variable_struct_exists(_M, "vw") && _M.vw.qs);
}

function kbr_soul_mode()
{
    if (!instance_exists(obj_heart))
        return "none";
    // DRBR: Flowery's orange SOUL (it drags the hidden red one)
    if (instance_exists(obj_fl_soul))
        return "orange";
    // DRBR: Spamton NEO's yellow SOUL (its driver, not the heart's colour field: see online_spamton53.gml)
    if (kbr_sn_yellow_on())
        return "yellow";
    // DRBR: Pink's purple SOUL (her lanes hold it: online_pink53.gml)
    if (kbr_pk_purple_on())
        return "purple";
    var _h = instance_find(obj_heart, 0);
    var _c = variable_instance_exists(_h, "color") ? _h.color : 0;
    if (_c != 0 && instance_exists(obj_hj_shield))
        return "green";
    if (_c == 0)
        return "red";
    if (_c == 1)
        return "yellow";
    return "other";
}

// ---------- DRBR: a boss piece's own random stream (Spamton NEO's and Pink's pieces: make_spamton.py / make_pink.py rewrite their
// random calls) ----------
// A piece draws from its own stream, seeded when it is made: from the stream of the piece that made it (one draw), or - made by
// something without a stream (the boss's battle object, the hub's SOUL drivers) - from the cycle's seed, the piece's OBJECT and
// how many of that object were made so in this attack. So a piece makes the same choices in every game as long as its maker
// did, and what a player does locally (a shot fired, a lane changed, an egg broken) only moves the streams of what it makes or
// breaks - never the cats or hearts made by the attack itself. A sent piece draws from its send's stream.
global.kbr_p_seed = 1;
global.kbr_p_cnt = {};

// a new cycle's attack (self: the boss's battle object): the root seed - every game the same, the cycle's own seed; the
// battle object's own stream starts over from it
function kbr_p_cycle(_seed)
{
    global.kbr_p_seed = _seed;
    global.kbr_p_cnt = {};
    if (id != noone && object_index >= 0)
        kbrpg = kbr_rng(kbr_mix(_seed, 1));
    return 1;
}

// the stream of the next object_index instance made from the root in this attack
function kbr_p_root()
{
    if (!variable_global_exists("kbr_p_cnt") || !is_struct(global.kbr_p_cnt))
        global.kbr_p_cnt = {};
    var _k = string(object_index);
    var _n = (variable_struct_exists(global.kbr_p_cnt, _k) ? variable_struct_get(global.kbr_p_cnt, _k) : 0) + 1;
    variable_struct_set(global.kbr_p_cnt, _k, _n);
    return kbr_rng(kbr_mix(kbr_mix(global.kbr_p_seed, (object_index * 7919) + 13), _n));
}

// the first line of a piece's Create (after kbr_ev_cr): its stream from its maker's (other), or from the root
function kbr_p_born()
{
    if (variable_instance_exists(id, "kbrpg"))
        return 0;
    if (variable_instance_exists(id, "kbrg") && is_struct(kbrg))
        return 0;
    var _src = undefined;
    var _me = id;
    with (other)
    {
        if (id != _me && variable_instance_exists(id, "kbrpg") && is_struct(kbrpg))
            _src = kbrpg;
    }
    if (!is_undefined(_src))
        kbrpg = kbr_rng(kbr_mix(kbr_rng_int(_src, 2147480000), 131));
    else
        kbrpg = kbr_p_root();
    return 1;
}

function kbr_pg()
{
    if (variable_instance_exists(id, "kbrg") && is_struct(kbrg))
        return kbrg;
    if (!variable_instance_exists(id, "kbrpg"))
        kbrpg = kbr_p_root();
    return kbrpg;
}

function kbr_p_random(_n)
{
    return kbr_rng_unit(kbr_pg()) * _n;
}

function kbr_p_irandom(_n)
{
    return kbr_rng_int(kbr_pg(), floor(_n) + 1);
}

function kbr_p_random_range(_a, _b)
{
    return _a + (kbr_rng_unit(kbr_pg()) * (_b - _a));
}

function kbr_p_irandom_range(_a, _b)
{
    var _lo = floor(min(_a, _b));
    var _hi = floor(max(_a, _b));
    return _lo + kbr_rng_int(kbr_pg(), (_hi - _lo) + 1);
}

function kbr_p_choose()
{
    return argument[kbr_rng_int(kbr_pg(), argument_count)];
}

function kbr_p_list_shuffle(_l)
{
    var _n = ds_list_size(_l);
    for (var _i = _n - 1; _i > 0; _i--)
    {
        var _j = kbr_rng_int(kbr_pg(), _i + 1);
        var _a = ds_list_find_value(_l, _i);
        ds_list_replace(_l, _i, ds_list_find_value(_l, _j));
        ds_list_replace(_l, _j, _a);
    }
    return _l;
}

// ---------- DRBR: the SOUL's mode in a line, when a special SOUL turns on ----------
// The bosses give your SOUL their own rules for their attacks (Spamton yellow, Gerson green, Flowery orange, Pink purple):
// when yours turns into one, the line under the boss's name says what it does - for four seconds, in that SOUL's colour - and
// again each time it turns on. Nothing for the red SOUL (the knights, Jevil).
function kbr_soul_hint_text(_m)
{
    switch (_m)
    {
        // (DRBR 1.0.2: and where USE SKILL went - Z is the SOUL's on these two)
        case "yellow": return "Z SHOOTS, HOLD Z: BIG SHOT. SKILLS: HOLD " + kbr_use_key_label();
        case "green": return "THE ARROWS TURN YOUR SHIELD";
        case "orange": return "HOLD Z, LET GO TO DASH. SKILLS: HOLD " + kbr_use_key_label();
        case "purple": return "THE ARROWS CHANGE LANES";
    }
    return "";
}

function kbr_soul_hint_col(_m)
{
    switch (_m)
    {
        case "yellow": return make_color_rgb(255, 255, 0);
        case "green": return make_color_rgb(0, 192, 0);
        case "orange": return make_color_rgb(255, 160, 64);
        case "purple": return make_color_rgb(213, 53, 217);
    }
    return c_white;
}

// DRBR: the SOUL hint right under the battle box (centred on it); while Flowery's own ORANGE SOUL lines are shown there (his
// first two attacks: kbr_fl_hud), his lines say it and this one waits
function kbr_hud_soulhint_box(xx, yy, _M)
{
    var _cx = xx + 320;
    var _y = yy + 253;
    if (instance_exists(obj_growtangle))
    {
        var _g = instance_find(obj_growtangle, 0);
        _cx = round((_g.bbox_left + _g.bbox_right) / 2);
        _y = _g.bbox_bottom + 8;
    }
    // (DRBR 1.0.2: kept on screen and in the battle's middle band, as Flowery's own lines are - a box that is not where it
    // usually is, or not measured yet, put it in the top left corner)
    _cx = clamp(_cx, xx + 160, xx + 480);
    _y = clamp(_y, yy + 250, yy + 330);
    if (instance_exists(obj_fl_soul) && kfo_view().hints && (!variable_global_exists("kbr_fl_turns") || global.kbr_fl_turns <= 2))
        return 0;
    draw_set_halign(fa_center);
    var _r = kbr_hud_soulhint(_cx, _y, 300, _M);
    draw_set_halign(fa_left);
    return _r;
}

function kbr_hud_soulhint(_cx, _y, _w, _M)
{
    if (!variable_struct_exists(_M, "sh_mode"))
    {
        _M.sh_mode = "red";
        _M.sh_t = 0;
    }
    var _m = (_M.me && !_M.out) ? kbr_soul_mode() : "red";
    if (_m != _M.sh_mode)
    {
        _M.sh_mode = _m;
        // the first two times each special SOUL turns on in a match (every attack of that boss would be too often)
        if (!variable_struct_exists(_M, "sh_n"))
            _M.sh_n = {};
        var _n = variable_struct_exists(_M.sh_n, _m) ? variable_struct_get(_M.sh_n, _m) : 0;
        _M.sh_t = (kbr_soul_hint_text(_m) != "" && _n < 2) ? 120 : 0;
        if (_M.sh_t > 0)
            variable_struct_set(_M.sh_n, _m, _n + 1);
    }
    if (_M.sh_t <= 0)
        return 0;
    _M.sh_t--;
    var _a = clamp(_M.sh_t / 20, 0, 1);
    draw_set_font(fnt_small);
    draw_set_alpha(_a);
    kbr_hud_text(_cx, _y, string_upper(_m) + " SOUL", kbr_soul_hint_col(_m));
    kbr_hud_text(_cx, _y + 12, kbr_fit(kbr_soul_hint_text(_m), _w), c_white);
    draw_set_alpha(1);
    return 1;
}

// DRBR: a player's OUT label with their place ("OUT #3"); a place not known yet (0: the host's standings not in) is just "OUT"
function kbr_out_text(_pl)
{
    if (is_numeric(_pl) && _pl > 0)
        return "OUT #" + string(_pl);
    return "OUT";
}

// DRBR: the SENDS row's description in the room's settings: what the value means in THIS room (its bosses' families)
function kfo_sends_desc(_s)
{
    var _m = variable_struct_exists(_s, "skfam") ? _s.skfam : 0;
    var _kn = variable_struct_exists(_s, "kn") ? _s.kn : [0];
    var _f = "";
    var _n = 0;
    var _seen = {};
    for (var _i = 0; _i < array_length(_kn); _i++)
    {
        var _fid = kbr_fam_of_ok(_kn[_i]);
        if (!variable_struct_exists(_seen, string(_fid)))
        {
            variable_struct_set(_seen, string(_fid), 1);
            _f += ((_f == "") ? "" : ", ") + kbr_fam_name(_fid);
            _n++;
        }
    }
    // (the families by name while they fit the line, else how many)
    var _here = (string_length(_f) <= 34) ? ("Here: " + _f + ".") : ("Here: " + string(_n) + " families, one per kind of boss.");
    if (_m == 0)
        return "CURRENT BOSS: the boss on stage's attacks.#" + _here;
    if (_m == KBR_FAM_ALL)
        return "ALL ENABLED: every family in the match.#" + _here;
    return "Only " + kbr_fam_name(_m) + "'s attacks, whoever is on#stage. < >: CURRENT BOSS, ALL or one family.";
}
