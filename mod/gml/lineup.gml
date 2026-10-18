
// ===== Build 41: knight lineups - TAG TEAM (two knights take turns) and ATTACK REMIX (a random knight's attack every turn) =====
// Every knight fight is the same battle object (obj_knight_enemy) running a different mod's code, picked by global.knight_variant.
// A lineup keeps one obj_knight_enemy per knight, all made under their own variant; only ONE is active at a time and
// global.knight_variant always names the active one, so everything that looks up "the knight" (obj_knight_enemy.x, with(...),
// the battle controller's per-mod code) finds the knight that is actually fighting. The others are deactivated together with the
// objects that belong to them (their fountain background, Supercharged's drawer, Violet's vignette...).
//   - the battle's slot 0 (name, HP, attack, defence, ACTs...) is saved and loaded with each switch, so every knight keeps its own
//     HP bar and ACTs (Tag Team); Attack Remix shares one HP pool;
//   - switches happen at the start of the player's turn (scr_mnendturn -> knight_lu_turnend), never while bullets are flying;
//   - the switch itself runs in the hub controller's Draw GUI End: GameMaker applies (de)activation at the end of the event that
//     asks for it, and nothing else runs after Draw GUI End in that frame, so no object ever sees zero or two knights;
//   - a knight that is about to be switched out stops its own Step for that frame (knight_lu_hold), so it never starts a turn;
//   - objects shared by every fight (battle controller, heroes, the arena cutscene...) were made under the first knight: the
//     variables another mod's code expects from its own Create are filled in on the switch (knight_lu_fill).
// Tag Team: when a knight's ending would start (it was beaten after its Roaring) and its partner still stands, it is knocked out
// instead (knight_lu_end_ok) and the partner takes over; beating the last knight ends the battle normally.
// Attack Remix: the Normal Knight hosts; each player turn ends with a random knight and a random attack from its list being
// chosen for the next enemy turn (forced through the fight's own practice code path, knight_force_sel). At 30% of the shared HP
// the Normal Knight takes over for the finale (its own Roaring and ending).
global.knight_lu = undefined;
// true from the moment a lineup switches knights off until the next room (cleared by the hub controller's Room Start): while it is
// true the hub never reactivates "everything" (that would wake the knights at the back), see knight_activate_all_safe
global.knight_lu_inroom = false;

function knight_lu_kind_of(_c)
{
    if (!is_struct(_c) || !variable_struct_exists(_c, "combo") || _c.mode != 0)
        return "";
    if (_c.combo == 1)
        return "tag";
    if (_c.combo == 2)
        return "remix";
    // build 43: Knight Fights Online (online_play.gml)
    if (_c.combo == 3)
        return "online";
    return "";
}

function knight_lu_on()
{
    return is_struct(global.knight_lu) && knight_active();
}

function knight_lu_ready()
{
    return knight_lu_on() && global.knight_lu.ready;
}

// the registry index of the knight that is fighting right now (the run's own knight outside a lineup)
function knight_lu_cur()
{
    var _lu = global.knight_lu;
    return _lu.ks[_lu.act];
}

// ---------- Attack Remix: which knights take part ----------
// build 42: never a joke fight (Cyan Knight), and the player picks the knights (cfg.rmask: bit k = knight k; none left on = all)
function knight_remix_eligible(_k)
{
    return (_k >= 0 && _k < knight_count() && !knight_reg(_k).joke);
}

function knight_remix_default_mask()
{
    var _m = 0;
    for (var _k = 0; _k < knight_count(); _k++)
    {
        if (knight_remix_eligible(_k))
            _m += real(1 << _k);
    }
    return _m;
}

function knight_remix_mask(_c)
{
    var _all = knight_remix_default_mask();
    var _v = knight_cfg_num(_c, "rmask");
    if (_v <= 0 || _v != floor(_v))
        return _all;
    var _m = real(_v & _all);
    return (_m == 0) ? _all : _m;
}

function knight_remix_on(_c, _k)
{
    return knight_remix_eligible(_k) && ((knight_remix_mask(_c) & (1 << _k)) != 0);
}

// "NORMAL, KAIZO" - the knights switched on (short names)
function knight_remix_names(_c, _sep)
{
    var _p = knight_remix_pool(_c);
    var _t = "";
    for (var _i = 0; _i < array_length(_p); _i++)
        _t += ((_i > 0) ? _sep : "") + knight_reg(_p[_i]).short;
    return _t;
}

// the knights the player switched on, in menu order
function knight_remix_pool(_c)
{
    var _m = knight_remix_mask(_c);
    var _l = [];
    for (var _k = 0; _k < knight_count(); _k++)
    {
        if ((_m & (1 << _k)) != 0)
            array_push(_l, _k);
    }
    return _l;
}

// the knights in a Remix battle: the Normal Knight first - it opens the battle and takes the finale (its own Roaring and
// ending) even when it is switched off for the random turns - then the others that are switched on
function knight_remix_list(_c)
{
    var _l = [0];
    var _p = knight_remix_pool(_c);
    for (var _i = 0; _i < array_length(_p); _i++)
    {
        if (_p[_i] != 0)
            array_push(_l, _p[_i]);
    }
    return _l;
}

// Attack Remix pacing: the shared HP follows a schedule down to 30% over 18 enemy turns, then the finale starts
function knight_lu_remix_pace()
{
    return { gate: 0.3, tmin: 18 };
}

function knight_lu_new(_r)
{
    var _kind = knight_lu_kind_of(_r.cfg);
    if (_kind == "")
    {
        global.knight_lu = undefined;
        return undefined;
    }
    var _ks = (_kind == "tag") ? [_r.cfg.knight, _r.cfg.knight2] : ((_kind == "online") ? kfo_lu_knights() : knight_remix_list(_r.cfg));
    var _n = array_length(_ks);
    // Remix: the knights that take the random turns (the Normal Knight only when it is switched on)
    var _inpool = array_create(_n, true);
    if (_kind == "remix")
    {
        for (var _i = 0; _i < _n; _i++)
            _inpool[_i] = knight_remix_on(_r.cfg, _ks[_i]);
    }
    var _lu = {
        kind: _kind, ks: _ks, n: _n, ready: false, act: 0, want: 0, pend: false, fresh: false,
        inst: array_create(_n, noone), slot: array_create(_n, undefined), ent: array_create(_n, undefined), ko: array_create(_n, false),
        turns: array_create(_n, 0), home: array_create(_n, undefined), msg: array_create(_n, ""), look: array_create(_n, undefined),
        fade: array_create(_n, 0), hp: 0, maxhp: 1, finale: false, ended: false, plan_k: -1, plan_i: -1, plan_name: "",
        anim_from: -1, anim_t: 99, banner: "", banner_t: 999, bench: noone, kod: -1, total: 0, inpool: _inpool
    };
    global.knight_lu = _lu;
    return _lu;
}

function knight_lu_clear()
{
    global.knight_lu = undefined;
}

// ---------- battle slot 0: everything the battle keeps about "the enemy" ----------
function knight_lu_acts_save(_a)
{
    var _o = [];
    for (var _j = 0; _j < 6; _j++)
        _o[_j] = _a[0][_j];
    return _o;
}

function knight_lu_slot_save()
{
    var _s = {
        name: global.monstername[0], hp: global.monsterhp[0], maxhp: global.monstermaxhp[0], at: global.monsterat[0], df: global.monsterdf[0],
        exp: global.monsterexp[0], gold: global.monstergold[0], spare: global.sparepoint[0], mmod: global.mercymod[0], mmax: global.mercymax[0],
        type: global.monstertype[0], mx: global.monsterx[0], my: global.monstery[0], status: variable_global_exists("monsterstatus") ? global.monsterstatus[0] : 0,
        canact: knight_lu_acts_save(global.canact), actname: knight_lu_acts_save(global.actname), actactor: knight_lu_acts_save(global.actactor),
        actdesc: knight_lu_acts_save(global.actdesc), actcost: knight_lu_acts_save(global.actcost), actsimul: knight_lu_acts_save(global.actsimul),
        canactsus: knight_lu_acts_save(global.canactsus), actnamesus: knight_lu_acts_save(global.actnamesus), actdescsus: knight_lu_acts_save(global.actdescsus),
        actcostsus: knight_lu_acts_save(global.actcostsus), actsimulsus: knight_lu_acts_save(global.actsimulsus),
        canactral: knight_lu_acts_save(global.canactral), actnameral: knight_lu_acts_save(global.actnameral), actdescral: knight_lu_acts_save(global.actdescral),
        actcostral: knight_lu_acts_save(global.actcostral), actsimulral: knight_lu_acts_save(global.actsimulral),
        canactnoe: knight_lu_acts_save(global.canactnoe), actnamenoe: knight_lu_acts_save(global.actnamenoe), actdescnoe: knight_lu_acts_save(global.actdescnoe),
        actcostnoe: knight_lu_acts_save(global.actcostnoe), actsimulnoe: knight_lu_acts_save(global.actsimulnoe)
    };
    return _s;
}

function knight_lu_slot_load(_s)
{
    if (!is_struct(_s))
        return 0;
    global.monstername[0] = _s.name;
    global.monsterhp[0] = _s.hp;
    global.monstermaxhp[0] = _s.maxhp;
    global.monsterat[0] = _s.at;
    global.monsterdf[0] = _s.df;
    global.monsterexp[0] = _s.exp;
    global.monstergold[0] = _s.gold;
    global.sparepoint[0] = _s.spare;
    global.mercymod[0] = _s.mmod;
    global.mercymax[0] = _s.mmax;
    global.monstertype[0] = _s.type;
    global.monsterx[0] = _s.mx;
    global.monstery[0] = _s.my;
    if (variable_global_exists("monsterstatus"))
        global.monsterstatus[0] = _s.status;
    // written through the globals themselves (an array passed into a function may be a copy when written to)
    for (var _j = 0; _j < 6; _j++)
    {
        global.canact[0][_j] = _s.canact[_j];
        global.actname[0][_j] = _s.actname[_j];
        global.actactor[0][_j] = _s.actactor[_j];
        global.actdesc[0][_j] = _s.actdesc[_j];
        global.actcost[0][_j] = _s.actcost[_j];
        global.actsimul[0][_j] = _s.actsimul[_j];
        global.canactsus[0][_j] = _s.canactsus[_j];
        global.actnamesus[0][_j] = _s.actnamesus[_j];
        global.actdescsus[0][_j] = _s.actdescsus[_j];
        global.actcostsus[0][_j] = _s.actcostsus[_j];
        global.actsimulsus[0][_j] = _s.actsimulsus[_j];
        global.canactral[0][_j] = _s.canactral[_j];
        global.actnameral[0][_j] = _s.actnameral[_j];
        global.actdescral[0][_j] = _s.actdescral[_j];
        global.actcostral[0][_j] = _s.actcostral[_j];
        global.actsimulral[0][_j] = _s.actsimulral[_j];
        global.canactnoe[0][_j] = _s.canactnoe[_j];
        global.actnamenoe[0][_j] = _s.actnamenoe[_j];
        global.actdescnoe[0][_j] = _s.actdescnoe[_j];
        global.actcostnoe[0][_j] = _s.actcostnoe[_j];
        global.actsimulnoe[0][_j] = _s.actsimulnoe[_j];
    }
    if (variable_global_exists("knight_actcount"))
        knight_actcount_fix();
    return 1;
}

// what a knight's Create changes about the party and the screen (Cyan Knight sets Kris to 1 HP / -99 DF, Kaizo Knight fills HP,
// Violet Knight renames everyone, every knight resets a few flags): put back after the extra knights are made, so the first
// knight's setup stays the one that counts
function knight_lu_party_save()
{
    var _s = { hp: knight_arr_copy(global.hp, 5), maxhp: knight_arr_copy(global.maxhp, 5), at: knight_arr_copy(global.at, 5), df: knight_arr_copy(global.df, 5),
        mag: knight_arr_copy(global.mag, 5), tension: global.tension, names: knight_arr_copy(global.charname, 5), tf96: global.tempflag[96], tf41: global.tempflag[41],
        invc: variable_global_exists("invc") ? global.invc : 1, kmode: variable_global_exists("knight_mode") ? global.knight_mode : 0,
        fkb: variable_global_exists("firstknightbattle") ? global.firstknightbattle : 0, heroes: [] };
    with (obj_heroparent)
    {
        var _h = { who: id };
        var _f = ["normalsprite", "idlesprite", "defendsprite", "actreadysprite", "attacksprite", "itemsprite", "itemreadysprite", "spellreadysprite", "spellsprite", "defeatsprite"];
        for (var _i = 0; _i < array_length(_f); _i++)
        {
            if (variable_instance_exists(id, _f[_i]))
                variable_struct_set(_h, _f[_i], variable_instance_get(id, _f[_i]));
        }
        array_push(_s.heroes, _h);
    }
    return _s;
}

function knight_lu_party_load(_s)
{
    for (var _i = 0; _i < 5; _i++)
    {
        global.hp[_i] = _s.hp[_i];
        global.maxhp[_i] = _s.maxhp[_i];
        global.at[_i] = _s.at[_i];
        global.df[_i] = _s.df[_i];
        global.mag[_i] = _s.mag[_i];
        global.charname[_i] = _s.names[_i];
    }
    global.tension = _s.tension;
    global.tempflag[96] = _s.tf96;
    global.tempflag[41] = _s.tf41;
    global.invc = _s.invc;
    if (variable_global_exists("knight_mode"))
        global.knight_mode = _s.kmode;
    if (variable_global_exists("firstknightbattle"))
        global.firstknightbattle = _s.fkb;
    for (var _i = 0; _i < array_length(_s.heroes); _i++)
    {
        var _h = _s.heroes[_i];
        if (!instance_exists(_h.who))
            continue;
        var _names = variable_struct_get_names(_h);
        for (var _j = 0; _j < array_length(_names); _j++)
        {
            if (_names[_j] != "who")
                variable_instance_set(_h.who, _names[_j], variable_struct_get(_h, _names[_j]));
        }
    }
}

// ---------- what belongs to a knight (switched out with it) ----------
// Its fight's own objects: backgrounds, drawers, attack helpers that live across turns. Everything else (battle controller,
// heroes, text, damage numbers, the arena cutscene, the hub's own objects) is shared and stays.
function knight_lu_owned(_o)
{
    var _n = object_get_name(_o);
    if (_n == "obj_knight_enemy" || _n == "obj_knight_ctrl" || _n == "obj_knight_menu" || _n == "obj_knight_prompt" || _n == "obj_knight_bench"
        || _n == "obj_knight_twin" || _n == "obj_knight_twin_bullet" || string_pos("obj_knight_ghost", _n) == 1 || _n == "obj_knight_herocc")
        return false;
    var _pre = ["obj_knight_", "obj_roaringknight_", "obj_tracking_sword", "obj_sword_tunnel", "obj_sword_vortex", "obj_bullet_knight", "obj_diagonal_bullet",
        "obj_elecknight", "obj_bgfountaintest", "obj_glitchyknight", "obj_kaizoknight", "obj_blocktree_bg", "obj_deathanim", "obj_not_stolen_from_kaizo",
        "obj_violet_insert_text", "obj_forcefield", "obj_fallingsword", "obj_endthefuckingturn", "obj_purify_event", "obj_dbullet_maker"];
    for (var _i = 0; _i < array_length(_pre); _i++)
    {
        if (string_pos(_pre[_i], _n) == 1)
            return true;
    }
    return false;
}

// ---------- variables another fight's code expects on the shared objects (from its own Create) ----------
function knight_lu_noop()
{
    return 0;
}

function knight_lu_dse(_spr, _img, _x, _y, _xs, _ys, _rot, _col, _a)
{
    draw_sprite_ext(_spr, _img, _x, _y, _xs, _ys, _rot, _col, _a);
}

function knight_lu_fill(_k)
{
    switch (knight_reg(_k).key)
    {
        case "kaizo":
            with (obj_heroparent)
            {
                if (!variable_instance_exists(id, "herofrozen"))
                    herofrozen = -4;
            }
            with (obj_darkcontroller)
            {
                if (!variable_instance_exists(id, "swordtype_con"))
                    swordtype_con = 0;
                if (!variable_instance_exists(id, "swordtype_cur"))
                    swordtype_cur = global.kaizo_swordtype;
            }
            with (obj_npc_sign)
            {
                if (!variable_instance_exists(id, "con"))
                    con = 0;
            }
            with (obj_tensionbar)
            {
                if (!variable_instance_exists(id, "deadtp"))
                    deadtp = -4;
            }
            with (obj_ch3_PTB02)
            {
                if (!variable_instance_exists(id, "ralsei_fakeout"))
                    ralsei_fakeout = false;
                if (!variable_instance_exists(id, "kaizosign"))
                    kaizosign = -4;
                if (!variable_instance_exists(id, "lightb"))
                    lightb = 255;
                if (!variable_instance_exists(id, "ouchie_display"))
                    ouchie_display = method(id, knight_lu_noop);
            }
            break;
        case "elec":
            with (obj_tensionbar)
            {
                if (!variable_instance_exists(id, "bluebar"))
                    bluebar = 0;
                if (!variable_instance_exists(id, "c_lightblue"))
                    c_lightblue = merge_color(c_blue, c_teal, 0.5);
            }
            with (obj_ch3_PTB02)
            {
                if (!variable_instance_exists(id, "makedrawer"))
                    makedrawer = false;
            }
            with (obj_ch3_PTB02_roaringknight)
            {
                if (!variable_instance_exists(id, "drawer"))
                    drawer = -4;
                if (!variable_instance_exists(id, "draw_sprite_ext_or_elec"))
                    draw_sprite_ext_or_elec = method(id, knight_lu_dse);
            }
            break;
        case "violet":
            with (obj_ch3_PTB02)
            {
                if (!variable_instance_exists(id, "itstime"))
                    itstime = false;
                if (!variable_instance_exists(id, "kaizo_actor"))
                    kaizo_actor = -4;
                if (!variable_instance_exists(id, "make_npcs_sideb"))
                    make_npcs_sideb = false;
                if (!variable_instance_exists(id, "nokaizo"))
                    nokaizo = false;
                if (!variable_instance_exists(id, "proceeded"))
                    proceeded = false;
                if (!variable_instance_exists(id, "ptb02_sideb"))
                    ptb02_sideb = global.flag[456];
                if (!variable_instance_exists(id, "remove_shiny_sideb"))
                    remove_shiny_sideb = false;
                if (!variable_instance_exists(id, "swoontype"))
                    swoontype = 4;
                if (!variable_instance_exists(id, "v_sideb_complete"))
                    v_sideb_complete = false;
            }
            break;
        case "cyan":
            with (obj_dbulletcontroller)
            {
                if (!variable_instance_exists(id, "misery"))
                    misery = 0;
            }
            break;
    }
    return 0;
}

// ---------- making the other knights (once, at the first player turn) ----------
function knight_lu_can_setup()
{
    if (!instance_exists(obj_knight_enemy) || !instance_exists(obj_battlecontroller))
        return false;
    // the first player turn (online the command menu is held shut there: myfight is KBR_NOMENU, see kbr_menu_block)
    if (!variable_global_exists("mnfight") || global.mnfight != 0 || !(global.myfight == 0 || (global.myfight == KBR_NOMENU && kbr_on())))
        return false;
    var _e = instance_find(obj_knight_enemy, 0);
    if (!variable_instance_exists(_e, "damagereductiontimer") || _e.damagereductiontimer < 2)
        return false;
    with (obj_battlecontroller)
    {
        if (variable_instance_exists(id, "intro") && intro == 2)
            return false;
    }
    return true;
}

function knight_lu_make(_i)
{
    var _lu = global.knight_lu;
    var _k = _lu.ks[_i];
    var _slot0 = knight_lu_slot_save();
    var _party = knight_lu_party_save();
    var _seen = {};
    with (all)
        variable_struct_set(_seen, string(id), 1);
    var _v0 = global.knight_variant;
    global.knight_variant = _k;
    // the battle room's objects were made by the host's fight: before this knight's Create runs, give them what its own fight
    // would have set on them (build 41 crash: Violet Knight's Create reads obj_ch3_PTB02.nokaizo)
    knight_lu_fill(_k);
    // Kaizo Knight's Create reads how its own intro was left (0 would be its Practice): a standard fight
    if (knight_reg(_k).key == "kaizo")
        global.knight_mode = 2;
    var _e = instance_create(global.monstermakex[0], global.monstermakey[0], obj_knight_enemy);
    _e.myself = 0;
    with (_e)
        event_user(12);
    with (_e)
        event_user(15);
    var _mine = [];
    with (all)
    {
        if (id != _e && !variable_struct_exists(_seen, string(id)))
            array_push(_mine, id);
    }
    _lu.inst[_i] = _e;
    _lu.home[_i] = [_e.x, _e.ystart];
    _lu.slot[_i] = knight_lu_slot_save();
    _lu.ent[_i] = _mine;
    _lu.look[_i] = knight_lu_look_of(_e, _k);
    for (var _j = 0; _j < array_length(_mine); _j++)
        instance_deactivate_object(_mine[_j]);
    instance_deactivate_object(_e);
    knight_lu_slot_load(_slot0);
    knight_lu_party_load(_party);
    global.knight_variant = _v0;
    return _e;
}

function knight_lu_look_of(_e, _k)
{
    var _r = knight_reg(_k);
    var _spr = variable_instance_exists(_e, "idlesprite") ? _e.idlesprite : _e.sprite_index;
    return { spr: _spr, xs: (_e.image_xscale == 0) ? 2 : _e.image_xscale, ys: (_e.image_yscale == 0) ? 2 : _e.image_yscale,
        blend: _r.tint ? _r.color : _e.image_blend, x: _e.x, y: _e.y };
}

function knight_lu_setup()
{
    var _lu = global.knight_lu;
    var _host = instance_find(obj_knight_enemy, 0);
    _lu.inst[0] = _host;
    _lu.home[0] = [_host.x, _host.ystart];
    _lu.ent[0] = [];
    _lu.look[0] = knight_lu_look_of(_host, _lu.ks[0]);
    // every knight's variables on the room's objects first (only the ones still missing), then the knights themselves
    for (var _i = 0; _i < _lu.n; _i++)
        knight_lu_fill(_lu.ks[_i]);
    for (var _i = 1; _i < _lu.n; _i++)
    {
        // build 52: an online secret boss (lineup id 1000 + n) is its own battle object (online_jevil52.gml)
        if (_lu.ks[_i] >= KBR_ENC_BASE)
            kbr_enc_make(_i);
        else
            knight_lu_make(_i);
    }
    _lu.ready = true;
    _lu.fresh = true;
    global.knight_lu_inroom = true;
    _lu.act = 0;
    _lu.want = 0;
    _lu.bench = instance_create_depth(0, 0, _host.depth + 1, obj_knight_bench);
    if (_lu.kind == "tag")
    {
        knight_lu_banner(string_upper(knight_reg(_lu.ks[1]).name) + " JOINS THE FIGHT!");
    }
    else if (_lu.kind == "online")
    {
        // build 43: one shared HP bar that is full again every turn; the first enemy turn comes from the match schedule
        _lu.maxhp = global.monstermaxhp[0];
        _lu.hp = global.monsterhp[0];
        kfo_lu_plan();
    }
    else
    {
        _lu.maxhp = global.monstermaxhp[0];
        _lu.hp = global.monsterhp[0];
        var _np = 0;
        var _only = 0;
        for (var _i = 0; _i < _lu.n; _i++)
        {
            if (_lu.inpool[_i])
            {
                _np++;
                _only = _i;
            }
        }
        knight_lu_banner((_np > 1) ? "ATTACK REMIX: EVERY TURN A NEW KNIGHT!" : ("ATTACK REMIX: " + string_upper(knight_reg(_lu.ks[_only]).name) + ", RANDOM ATTACKS!"));
        // the very first enemy turn is already a random one
        knight_lu_plan_next();
        if (_lu.plan_k != _lu.act)
        {
            _lu.want = _lu.plan_k;
            _lu.pend = true;
        }
    }
    return 1;
}

function knight_lu_banner(_t)
{
    var _lu = global.knight_lu;
    if (!is_struct(_lu))
        return 0;
    _lu.banner = _t;
    _lu.banner_t = 0;
}

// ---------- the switch ----------
function knight_lu_swap(_to)
{
    var _lu = global.knight_lu;
    var _from = _lu.act;
    _lu.pend = false;
    if (_to < 0 || _to >= _lu.n || _to == _from)
        return 0;
    var _a = _lu.inst[_from];
    var _b = _lu.inst[_to];
    if (!instance_exists(_a))
        return 0;
    _lu.slot[_from] = knight_lu_slot_save();
    if (_lu.kind != "tag")
        _lu.hp = global.monsterhp[0];
    _lu.look[_from] = knight_lu_look_of(_a, _lu.ks[_from]);
    var _own = [];
    with (all)
    {
        if (knight_lu_owned(object_index))
            array_push(_own, id);
    }
    // DRBR: a boss going off stage takes its own objects with it (kbr_enc_entourage), as a knight does
    if (_lu.ks[_from] >= KBR_ENC_BASE)
    {
        var _be = kbr_enc_entourage(_lu.ks[_from], _a);
        for (var _i = 0; _i < array_length(_be); _i++)
            array_push(_own, _be[_i]);
    }
    _lu.ent[_from] = _own;
    for (var _i = 0; _i < array_length(_own); _i++)
        instance_deactivate_object(_own[_i]);
    instance_deactivate_object(_a);
    instance_activate_object(_b);
    var _eb = _lu.ent[_to];
    if (is_array(_eb))
    {
        for (var _i = 0; _i < array_length(_eb); _i++)
            instance_activate_object(_eb[_i]);
    }
    _lu.ent[_to] = [];
    // build 52: a secret boss keeps the battle's knight variant (the battle controller, the SOUL and the box run their
    // knight-variant code: a variant of 1000 would switch them off)
    if (_lu.ks[_to] < KBR_ENC_BASE)
        global.knight_variant = _lu.ks[_to];
    knight_lu_slot_load(_lu.slot[_to]);
    global.monsterinstance[0] = _b;
    if (_lu.kind != "tag")
    {
        global.monstermaxhp[0] = _lu.maxhp;
        global.monsterhp[0] = _lu.hp;
    }
    knight_lu_fill(_lu.ks[_to]);
    _lu.act = _to;
    _lu.anim_from = _from;
    _lu.anim_t = 0;
    // build 45: the shared battle - the knight that steps in waits for the timeline to arm its first attack
    if (kbr_on())
        kbr_after_swap(_b);
    // the incoming knight flashes in (every fight's own white flash); a deactivated instance's variables can be set by id
    if (variable_instance_exists(_b, "whiteflash"))
        _b.whiteflash = 10;
    // HoldBreath is the party's: it keeps working whoever attacks
    if (variable_instance_exists(_a, "holdbreathcount") && variable_instance_exists(_b, "holdbreathcount"))
        _b.holdbreathcount = _a.holdbreathcount;
    if (_lu.kind == "remix" && _lu.finale && _to == 0)
        knight_lu_finale_arm(_b);
    return 1;
}

// the Normal Knight takes the Remix finale: its own phase 4 (Spinning Slashes, the glow, the Roaring) and its own ending
function knight_lu_finale_arm(_e)
{
    _e.phase = 4;
    _e.phase4turn = 0;
    _e.rotatingslash3used = false;
    _e.haveusedroaring = false;
}

// called by the hub controller's Draw GUI End (see the header)
function knight_lu_late()
{
    if (!knight_lu_on() || global.knight_frozen)
        return 0;
    var _lu = global.knight_lu;
    if (global.krun.state != "battle")
        return 0;
    if (!_lu.ready)
    {
        if (knight_lu_can_setup())
            knight_lu_setup();
        return 0;
    }
    // a knight made in this same event is still switching off: wait one frame before switching to it
    if (_lu.fresh)
    {
        _lu.fresh = false;
        return 0;
    }
    // build 45: online the SOUL never leaves and the battle never goes back to the menu - the knight changes between two
    // attacks of the shared timeline (kbr_swap_ok)
    if (_lu.pend && (kbr_on() ? kbr_swap_ok() : (global.mnfight != 2 && !instance_exists(obj_heart))))
        knight_lu_swap(_lu.want);
    return 0;
}

// every Step of the knight starts with this: a knight that is about to be switched out does nothing (no new turn, no talk)
function knight_lu_hold()
{
    if (!is_struct(global.knight_lu))
        return false;
    var _lu = global.knight_lu;
    return (_lu.ready && _lu.pend && variable_global_exists("mnfight") && global.mnfight != 2 && id == _lu.inst[_lu.act]);
}

// per-step upkeep from the run tick: shared HP, the knight's name in the menus, the animations
function knight_lu_tick()
{
    if (!knight_lu_ready())
        return 0;
    var _lu = global.knight_lu;
    if (_lu.anim_t < 99)
        _lu.anim_t++;
    if (_lu.banner_t < 999)
        _lu.banner_t++;
    for (var _i = 0; _i < _lu.n; _i++)
    {
        if (_lu.ko[_i] && _i != _lu.act)
            _lu.fade[_i] = min(60, _lu.fade[_i] + 1);
    }
    if (instance_exists(_lu.inst[_lu.act]))
    {
        global.monstername[0] = knight_reg(_lu.ks[_lu.act]).name;
        if (_lu.kind != "tag")
            _lu.hp = global.monsterhp[0];
    }
    // the battle must not end before the last knight: a knight that could now be spared (Cyan Knight at 5%) or that dropped to
    // 0 HP some other way counts as beaten while its partner stands (Tag Team); in a Remix only the finale knight can end it
    var _last = (_lu.kind == "tag") ? (knight_lu_next_alive(_lu.act) < 0) : _lu.finale;
    if (!_last)
    {
        var _beaten = false;
        if (global.mercymax[0] > 0 && global.mercymod[0] >= global.mercymax[0])
        {
            global.mercymod[0] = 0;
            _beaten = true;
        }
        if (global.monster[0] == 0 || global.monsterhp[0] <= 0)
        {
            global.monster[0] = 1;
            global.monsterhp[0] = max(1, global.monsterhp[0]);
            _beaten = true;
        }
        if (_beaten && _lu.kind == "tag")
            knight_lu_ko();
    }
    return 0;
}

// a new enemy turn begins (mnfight -> 2): count it for the knight that is fighting
function knight_lu_count_turn()
{
    if (!knight_lu_ready())
        return 0;
    var _lu = global.knight_lu;
    _lu.turns[_lu.act]++;
    _lu.total++;
    return 0;
}

// enemy turns the knight that is fighting has taken (pacing)
function knight_lu_turns_now()
{
    var _lu = global.knight_lu;
    if (_lu.kind != "tag")
        return _lu.total;
    return _lu.turns[_lu.act];
}

function knight_lu_next_alive(_from)
{
    var _lu = global.knight_lu;
    for (var _d = 1; _d < _lu.n; _d++)
    {
        var _i = (_from + _d) mod _lu.n;
        if (!_lu.ko[_i])
            return _i;
    }
    return -1;
}

// end of every enemy turn (scr_mnendturn): who fights the next round
function knight_lu_turnend()
{
    // build 50: Flowery left alone - his last stand (OMEGA FLOWERY). Here because every knight's own end of turn calls this
    // (the Kaizo and Violet Knights' versions of it have no Weird Route hook)
    if (knight_fl_laststand_check())
        return 0;
    if (!knight_lu_ready())
        return 0;
    var _lu = global.knight_lu;
    _lu.msg[_lu.act] = global.battlemsg[0];
    if (_lu.kind == "online")
    {
        kfo_turn_end();
        return 0;
    }
    if (_lu.kind == "tag")
    {
        var _nx = _lu.pend ? _lu.want : knight_lu_next_alive(_lu.act);
        if (_nx >= 0 && _nx != _lu.act)
        {
            _lu.want = _nx;
            _lu.pend = true;
            var _nm = knight_reg(_lu.ks[_nx]).name;
            global.battlemsg[0] = (_lu.msg[_nx] != "" && _lu.msg[_nx] != " ") ? _lu.msg[_nx] : ("* The " + _nm + " steps forward!");
        }
        return 0;
    }
    if (_lu.finale)
        return 0;
    var _p = knight_lu_remix_pace();
    if (global.monsterhp[0] <= floor(global.monstermaxhp[0] * _p.gate))
    {
        _lu.finale = true;
        _lu.want = 0;
        _lu.plan_k = 0;
        _lu.plan_i = -1;
        _lu.pend = (_lu.act != 0);
        if (!_lu.pend)
            knight_lu_finale_arm(_lu.inst[0]);
        knight_lu_banner("FINALE: THE NORMAL KNIGHT RETURNS!");
        global.battlemsg[0] = "* The Normal Knight returns for the finale!";
        return 0;
    }
    knight_lu_plan_next();
    _lu.want = _lu.plan_k;
    _lu.pend = (_lu.plan_k != _lu.act);
    global.battlemsg[0] = "* The " + knight_reg(_lu.ks[_lu.plan_k]).name + (_lu.pend ? " steps in." : " keeps fighting.") + "&* Next: " + _lu.plan_name + ".";
    return 0;
}

// Attack Remix: the next enemy turn's knight (a different one from the last when possible) and attack
function knight_lu_plan_next()
{
    var _lu = global.knight_lu;
    var _cand = [];
    for (var _i = 0; _i < _lu.n; _i++)
    {
        if (_lu.inpool[_i])
            array_push(_cand, _i);
    }
    if (array_length(_cand) == 0)
        _cand = [0];
    var _pick = [];
    for (var _i = 0; _i < array_length(_cand); _i++)
    {
        if (_cand[_i] != _lu.plan_k || array_length(_cand) == 1)
            array_push(_pick, _cand[_i]);
    }
    var _ki = _pick[irandom(array_length(_pick) - 1)];
    var _l = knight_reg(_lu.ks[_ki]).atk;
    var _ok = [];
    for (var _i = 0; _i < array_length(_l); _i++)
    {
        if (_l[_i][3] == 0)
            array_push(_ok, _i);
    }
    var _ai = (array_length(_ok) > 0) ? _ok[irandom(array_length(_ok) - 1)] : 0;
    _lu.plan_k = _ki;
    _lu.plan_i = _ai;
    _lu.plan_name = _l[_ai][2];
    return _ki;
}

// ---------- endings ----------
// Draw_0 of every fight: the knight would start its ending now. Tag Team: unless it is the last one standing it is knocked out
// instead and its partner takes over. Remix: only the finale knight can end the battle.
function knight_lu_end_ok()
{
    if (!knight_lu_ready())
        return true;
    var _lu = global.knight_lu;
    // build 43: the online Knight never falls (the match ends when the players do)
    if (_lu.kind == "online")
        return false;
    if (_lu.kind == "remix")
    {
        if (_lu.finale && _lu.act == 0)
        {
            _lu.ended = true;
            return true;
        }
        return false;
    }
    var _other = knight_lu_next_alive(_lu.act);
    if (_other < 0 || _other == _lu.act)
    {
        _lu.ended = true;
        return true;
    }
    knight_lu_ko();
    return false;
}

// Tag Team: the knight that is fighting is beaten while its partner still stands - the partner takes over at once (or at the
// end of this enemy turn when it happens while bullets fly)
function knight_lu_ko()
{
    var _lu = global.knight_lu;
    if (_lu.ko[_lu.act])
        return 0;
    var _other = knight_lu_next_alive(_lu.act);
    if (_other < 0)
        return 0;
    _lu.ko[_lu.act] = true;
    _lu.kod = _lu.act;
    _lu.want = _other;
    _lu.pend = true;
    knight_lu_banner(string_upper(knight_reg(_lu.ks[_lu.act]).name) + " IS DOWN!  " + string_upper(knight_reg(_lu.ks[_other]).name) + " TAKES OVER!");
    snd_play(snd_knight_hurt);
    knight_mus_takeover(_lu.ks[_other]);
    return 1;
}

// the battle is over after the last knight's ending (the battle controller says so): results straight away, before the arena
// cutscene of the first knight would play on with another fight's code
function knight_lu_over()
{
    if (!knight_lu_ready())
        return false;
    var _lu = global.knight_lu;
    var _last = (_lu.kind == "tag") ? (knight_lu_next_alive(_lu.act) < 0) : _lu.finale;
    if (!_lu.ended && !_last)
        return false;
    var _over = false;
    with (obj_battlecontroller)
    {
        if (variable_instance_exists(id, "intro") && intro == 2)
            _over = true;
    }
    return _over;
}

// ---------- drawing: the knights waiting at the back, the HP bars ----------
function knight_lu_bench_pos(_i)
{
    var _lu = global.knight_lu;
    var _h = _lu.home[_i];
    if (!is_array(_h))
        _h = _lu.home[0];
    return [_h[0] + 96, _h[1] - 34];
}

function knight_lu_bench_draw()
{
    if (!knight_lu_ready() || global.knight_lu.kind != "tag")
        return 0;
    var _lu = global.knight_lu;
    var _t = current_time / 1000;
    for (var _i = 0; _i < _lu.n; _i++)
    {
        if (_i == _lu.act)
            continue;
        var _lk = _lu.look[_i];
        if (!is_struct(_lk) || !sprite_exists(_lk.spr))
            continue;
        var _a = 0.7;
        if (_lu.ko[_i])
            _a = 0.7 * (1 - (_lu.fade[_i] / 60));
        if (_a <= 0.01)
            continue;
        var _bp = knight_lu_bench_pos(_i);
        var _x = _bp[0];
        var _y = _bp[1] + (cos(_t * 2) * 6);
        // just switched out: slide from the front to the back
        if (_i == _lu.anim_from && _lu.anim_t < 16)
        {
            var _k = _lu.anim_t / 16;
            var _h = _lu.home[_i];
            _x = lerp(_h[0], _x, _k);
            _y = lerp(_h[1], _y, _k);
        }
        var _col = merge_color(_lk.blend, c_black, _lu.ko[_i] ? 0.6 : 0.4);
        draw_sprite_ext(_lk.spr, floor(_t * 6) mod max(1, sprite_get_number(_lk.spr)), _x, _y, _lk.xs, _lk.ys, 0, _col, _a);
    }
    return 0;
}

// top right: one bar per knight (Tag Team) or the shared bar and who is fighting (Remix); a banner when something changes
function knight_lu_hud_draw(xx, yy)
{
    if (!knight_lu_ready())
        return 0;
    var _lu = global.knight_lu;
    var _rows = [];
    if (_lu.kind == "tag")
    {
        for (var _i = 0; _i < _lu.n; _i++)
        {
            var _s = _lu.slot[_i];
            var _hp = (_i == _lu.act) ? global.monsterhp[0] : (is_struct(_s) ? _s.hp : 1);
            var _mx = (_i == _lu.act) ? global.monstermaxhp[0] : (is_struct(_s) ? _s.maxhp : 1);
            array_push(_rows, { nm: knight_reg(_lu.ks[_i]).short, f: clamp(_hp / max(1, _mx), 0, 1), on: (_i == _lu.act), ko: _lu.ko[_i], col: knight_reg(_lu.ks[_i]).color });
        }
    }
    else if (_lu.kind == "remix")
    {
        array_push(_rows, { nm: "REMIX", f: clamp(global.monsterhp[0] / max(1, global.monstermaxhp[0]), 0, 1), on: true, ko: false, col: knight_reg(_lu.ks[_lu.act]).color });
    }
    var _x1 = xx + 632;
    var _y = yy + 6;
    for (var _i = 0; _i < array_length(_rows); _i++)
    {
        var _rw = _rows[_i];
        var _bx0 = _x1 - 100;
        draw_set_halign(fa_right);
        draw_set_color(c_black);
        knight_txt_tiny(_bx0 - 5, _y + 1, _rw.nm);
        draw_set_color(_rw.ko ? c_dkgray : (_rw.on ? c_yellow : c_ltgray));
        knight_txt_tiny(_bx0 - 6, _y, _rw.nm);
        draw_set_halign(fa_left);
        draw_set_color(c_black);
        draw_rectangle(_bx0 - 1, _y + 3, _x1 + 1, _y + 13, false);
        draw_set_color(c_maroon);
        draw_rectangle(_bx0, _y + 4, _x1, _y + 12, false);
        if (!_rw.ko && _rw.f > 0)
        {
            draw_set_color(_rw.on ? merge_color(_rw.col, c_white, 0.3) : merge_color(_rw.col, c_gray, 0.5));
            draw_rectangle(_bx0, _y + 4, _bx0 + max(1, round(_rw.f * 100)), _y + 12, false);
        }
        if (_rw.ko)
        {
            draw_set_color(c_white);
            draw_set_halign(fa_center);
            knight_txt_tiny(_bx0 + 50, _y, "DOWN");
            draw_set_halign(fa_left);
        }
        _y += 17;
    }
    if (_lu.kind == "remix")
    {
        draw_set_halign(fa_right);
        draw_set_color(c_black);
        knight_txt_tiny(_x1 + 1, _y + 1, knight_reg(_lu.ks[_lu.act]).short + (_lu.finale ? "  FINALE" : ""));
        draw_set_color(knight_reg(_lu.ks[_lu.act]).color);
        knight_txt_tiny(_x1, _y, knight_reg(_lu.ks[_lu.act]).short + (_lu.finale ? "  FINALE" : ""));
        draw_set_halign(fa_left);
    }
    if (_lu.banner != "" && _lu.banner_t < 120)
    {
        var _ba = min(1, (120 - _lu.banner_t) / 20);
        draw_set_alpha(_ba);
        draw_set_halign(fa_center);
        var _bl = knight_wrap(_lu.banner, 600);
        // online: under the battle box (the top of the screen is the skills, the knight lines and the players)
        var _by = (_lu.kind == "online") ? 256 : 44;
        for (var _i = 0; _i < array_length(_bl); _i++)
        {
            draw_set_color(c_black);
            knight_txt(xx + 322, yy + _by + 2 + (_i * 30), _bl[_i]);
            draw_set_color(c_yellow);
            knight_txt(xx + 320, yy + _by + (_i * 30), _bl[_i]);
        }
        draw_set_halign(fa_left);
        draw_set_alpha(1);
    }
    draw_set_color(c_white);
    return 0;
}

// ---------- activation outside the lineup's own switches ----------
// The hub reactivates "everything" in a few places (closing a prompt, leaving, restarting). With a lineup that would wake the
// knights at the back too (two knights, each running the other's code). These activate only what the hub itself switched off.
function knight_activate_all_safe()
{
    // build 50: back from a pause - exactly what the pause switched off (knight_freeze keeps the list)
    var _l = global.knight_frozen_list;
    if (!is_array(_l) && !global.knight_lu_inroom)
    {
        instance_activate_all();
        return 0;
    }
    if (is_array(_l))
    {
        for (var _i = 0; _i < array_length(_l); _i++)
            instance_activate_object(_l[_i]);
    }
    global.knight_frozen_list = undefined;
    return 1;
}
