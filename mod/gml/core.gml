// ===== Knight Hub core: registry, globals, party helpers =====
// Knight Fights Online: the value global.myfight holds online so the battle's command menu never opens (kbr_menu_block)
#macro KBR_NOMENU 99
global.knight_variant = 0;
global.knight_variant_pending = 0;
global.knight_sel = 0;
global.knight_song = 0;
global.knight_weird = 0;
global.knight_practice = 0;
global.knight_run = 0;
global.knight_party = [1, 2, 3];
global.knight_after_dest = -4;
global.knight_loaded = false;
global.knight_calc_loop = false;
global.knight_reopen = false;
global.knight_cfg = undefined;
global.knight_launch = undefined;
global.krun = undefined;
global.knight_orig = undefined;
global.knight_hits = 0;
global.knight_lockslots = [0, 0, 0];
global.knight_hit_time = 0;
global.knight_store_status = "";
global.knight_store_ok = true;
global.knight_freeze_spr = -1;
global.knight_resume_story = false;
global.chemg_show_room = 0;
global.chemg_show_val = 0;
global.kaizo_funni = 0;
global.kaizo_intro = 0;
global.kaizo_practice = 0;
global.kaizo_swordtype = 0;
global.elecyellow = 6354943;
global.eleccyan = 16775542;
global.elecpalette = 0;
global.electotalpalettes = 6;
global.orighpkris = 0;
global.orighpsusie = 0;
global.orighpralsei = 0;
global.vipractice = false;
global.snowbreak = false;
global.turnskip = 0;
global.jokat = 0;
global.jokdf = 0;
global.jokate = 0;
global.jokdfe = 0;
global.lightsplitter_active = false;
global.lightsplitter_orb_flash = 0;
global.lightsplitter_creating_backup = false;
global.chapter_return = 0;
global.knight_registry = [
@@REGISTRY@@
];
global.knight_songs = [
@@SONGS@@
];
// build 50: the song list's order before build 50 (files) - an online MUSIC setting saved as a list number then is read with it
global.knight_songs_v49 = @@SONGSV49@@;
global.knight_hub_credits = @@HUBCREDITS@@;
// build 50: the KNIGHT tab's pages - one per DELTARUNE chapter - and the bosses planned for each (knights.json "pages" /
// "planned"). A planned boss is shown as COMING SOON and cannot be picked; once it is added it is a registry entry like the
// knights (with its "chapter") and shows on its page, in RANDOM / RUSH and - with an online id - online (kbr_roster).
global.knight_pages = [
@@PAGES@@
];
global.knight_planned = [
@@PLANNED@@
];

// build 52: the other chapters' pages (their bosses are only planned so far) are hidden until a boss of theirs is in the
// hub: set KNIGHT_SHOW_PLANNED to true to show them (and their COMING SOON rows) again - nothing of theirs is deleted
#macro KNIGHT_SHOW_PLANNED false

function knight_pages_shown()
{
    var _l = [];
    for (var _i = 0; _i < array_length(global.knight_pages); _i++)
    {
        var _pg = global.knight_pages[_i];
        var _has = KNIGHT_SHOW_PLANNED;
        for (var _k = 0; _k < knight_count() && !_has; _k++)
        {
            if (knight_chapter_of(_k) == _pg.ch)
                _has = true;
        }
        if (_has)
            array_push(_l, _pg);
    }
    if (array_length(_l) == 0)
        array_push(_l, { ch: 3, title: "CHAPTER 3" });
    return _l;
}

function knight_page_count()
{
    return array_length(knight_pages_shown());
}

function knight_page_ch(_p)
{
    var _l = knight_pages_shown();
    return _l[clamp(_p, 0, array_length(_l) - 1)].ch;
}

function knight_page_title(_p)
{
    var _l = knight_pages_shown();
    return _l[clamp(_p, 0, array_length(_l) - 1)].title;
}

// the page of chapter _ch (the first page when it has none)
function knight_page_of_ch(_ch)
{
    var _l = knight_pages_shown();
    for (var _i = 0; _i < array_length(_l); _i++)
    {
        if (_l[_i].ch == _ch)
            return _i;
    }
    return 0;
}

// the chapter a registry knight belongs to (3 for the Roaring Knights)
function knight_chapter_of(_k)
{
    var _r = knight_reg(_k);
    return variable_struct_exists(_r, "chapter") ? _r.chapter : 3;
}

function knight_count()
{
    return array_length(global.knight_registry);
}

function knight_reg(_i)
{
    // build 52: an online encounter's lineup id (1000 + n, Jevil): its own entry (online_jevil52.gml); offline never uses one
    if (is_numeric(_i) && _i >= 1000)
        return kbr_enc_reg(_i);
    return global.knight_registry[clamp(_i, 0, array_length(global.knight_registry) - 1)];
}

// indices of the knights that take part in Knight Rush (never the joke fight)
function knight_rush_list()
{
    var _l = [];
    for (var _i = 0; _i < knight_count(); _i++)
    {
        if (knight_reg(_i).rush)
            array_push(_l, _i);
    }
    return _l;
}

function knight_find_key(_key)
{
    for (var _i = 0; _i < knight_count(); _i++)
    {
        if (knight_reg(_i).key == _key)
            return _i;
    }
    return -1;
}

// ---------- party helpers (used by the audited fight patches as well) ----------
function knight_party_has(_c)
{
    for (var _i = 0; _i < 3; _i++)
    {
        if (global.char[_i] == _c)
            return true;
    }
    return false;
}

function knight_party_count()
{
    var _n = 0;
    for (var _i = 0; _i < 3; _i++)
    {
        if (global.char[_i] != 0)
            _n++;
    }
    return _n;
}

function knight_slot_of(_c)
{
    for (var _i = 0; _i < 3; _i++)
    {
        if (global.char[_i] == _c)
            return _i;
    }
    return -1;
}

function knight_party_alive_any()
{
    for (var _i = 0; _i < 3; _i++)
    {
        var _c = global.char[_i];
        if (_c != 0 && global.hp[_c] > 0)
            return true;
    }
    return false;
}

function knight_canon_xy(_n, _a)
{
    if (_n == "kris")
        return (_a == "x") ? 2356 : 104;
    if (_n == "susie")
        return (_a == "x") ? 2310 : 142;
    return (_a == "x") ? 2288 : 190;
}

// invisible stand-ins for the after-fight scene when Susie / Ralsei are not in the hub party
function knight_actor_stubs()
{
    if (!(variable_global_exists("knight_run") && global.knight_run == 1))
        return 0;
    if (!variable_instance_exists(id, "su"))
        su = 1;
    if (!variable_instance_exists(id, "ra"))
        ra = 2;
    if (!variable_instance_exists(id, "no"))
        no = 3;
    knight_actors_ensure();
    return 0;
}

// Every kr_actor / su_actor / ra_actor the after-fight scenes touch must be a live instance.
// Missing, never-set or destroyed ones are replaced by invisible stand-ins (a write to a dead one crashes: "Variable set failed x").
function knight_actors_ensure()
{
    if (!(variable_global_exists("knight_run") && global.knight_run == 1))
        return 0;
    var _n = ["kr_actor", "su_actor", "ra_actor"];
    var _w = ["kris", "susie", "ralsei"];
    for (var _i = 0; _i < 3; _i++)
    {
        var _v = -4;
        if (variable_instance_exists(id, _n[_i]))
            _v = variable_instance_get(id, _n[_i]);
        var _ok = (!is_undefined(_v) && !is_string(_v) && i_ex(_v));
        if (!_ok)
        {
            var _a = instance_create(knight_canon_xy(_w[_i], "x"), knight_canon_xy(_w[_i], "y"), obj_actor);
            _a.visible = false;
            variable_instance_set(id, _n[_i], _a);
        }
    }
    return 0;
}

function knight_friends_down()
{
    var _ids = [1, 3, 4];
    for (var _i = 0; _i < 3; _i++)
    {
        if (scr_havechar(_ids[_i]) && global.hp[_ids[_i]] > 0)
            return false;
    }
    return true;
}

// Susie's balloon text for the current party (Noelle / absent Ralsei aware)
function knight_susie_line(_o)
{
    // friends still in the fight (build 39: not the ones the Knight has taken on a Weird Route)
    var _f = [], _nm = [], _pn = [];
    if (knight_wr_here(1)) { array_push(_f, 1); array_push(_nm, "Kris"); array_push(_pn, "them"); }
    if (knight_wr_here(3)) { array_push(_f, 3); array_push(_nm, "Ralsei"); array_push(_pn, "him"); }
    if (knight_wr_here(4)) { array_push(_f, 4); array_push(_nm, "Noelle"); array_push(_pn, "her"); }
    if (scr_havechar(5) && global.hp[5] > 0) { array_push(_f, 5); array_push(_nm, "Flowery"); array_push(_pn, "him"); }
    var _n = array_length(_f);
    if (_n == 2 && _f[0] == 1 && _f[1] == 3)
        return _o;
    var _p = (_n == 1) ? _pn[0] : "them";
    if (_n == 0 && _o == "Didn't... think&we'd still be&standing, did you?/%")
        return "Didn't... think&I'd still be&standing, did you?/%";
    if (_n == 0 && _o == "You actually messed up,&picking a fight with US!/%")
        return "You actually messed up,&picking a fight with ME!/%";
    if (_o == "Me? I got...&Kris and Ralsei&behind me./%")
    {
        if (_n == 0) return "Me? I've...&got friends I KNOW&would back me up./%";
        if (_n == 1) return "Me? I got...&" + _nm[0] + " here&behind me./%";
        return "Me? I got...&" + _nm[0] + " and " + _nm[1] + "&behind me./%";
    }
    if (_o == "As long as Kris,&Ralsei, are here.../%")
    {
        if (_n == 0) return "But as long as&I keep standing.../%";
        if (_n == 1) return "As long as " + _nm[0] + "&is right here.../%";
        return "As long as " + _nm[0] + ",&" + _nm[1] + ", are here.../%";
    }
    if (_o == "Even... even if&you knock them down.../%")
    {
        if (_n == 0) return "You... you can&hit me all you like.../%";
        return "Even... even if&you knock " + _p + " down.../%";
    }
    if (_o == "As long as Kris has got&a hand to lift me up with.../%")
    {
        if (_n == 0) return "As long as I can&still stand up.../%";
        if (_n == 1) return "As long as " + _nm[0] + " has got&a hand to lift me up with.../%";
        return "As long as my friends have got&a hand to lift me up with.../%";
    }
    if (_o == "As long as I'm here to&lift them back up.../%")
    {
        if (_n == 0) return "As long as I'm still&standing.../%";
        return "As long as I'm here to&lift " + _p + " back up.../%";
    }
    return _o;
}

function knight_char_short(_c)
{
    switch (_c)
    {
        case 1: return "K";
        case 2: return "S";
        case 3: return "R";
        case 4: return "N";
    }
    // build 50: the custom characters (Flowery "F", ...)
    var _d = knight_cc(_c);
    return is_undefined(_d) ? "-" : _d.short;
}

// party array with empty slots removed, order and duplicates kept
function knight_party_compact(_p)
{
    var _o = [0, 0, 0];
    var _n = 0;
    for (var _i = 0; _i < 3; _i++)
    {
        if (_p[_i] >= 1 && _p[_i] <= knight_cc_max_id())
        {
            _o[_n] = _p[_i];
            _n++;
        }
    }
    return _o;
}

function knight_party_size(_p)
{
    var _n = 0;
    for (var _i = 0; _i < 3; _i++)
    {
        if (_p[_i] >= 1 && _p[_i] <= knight_cc_max_id())
            _n++;
    }
    return _n;
}

function knight_party_is_trio(_p)
{
    var _k = 0, _s = 0, _r = 0;
    for (var _i = 0; _i < 3; _i++)
    {
        if (_p[_i] == 1) _k++;
        if (_p[_i] == 2) _s++;
        if (_p[_i] == 3) _r++;
    }
    return (_k >= 1 && _s >= 1 && _r >= 1);
}

function knight_party_has_in(_p, _c)
{
    for (var _i = 0; _i < 3; _i++)
    {
        if (_p[_i] == _c)
            return true;
    }
    return false;
}

function knight_party_text(_p)
{
    var _t = "";
    for (var _i = 0; _i < 3; _i++)
    {
        if (_p[_i] >= 1 && _p[_i] <= knight_cc_max_id())
        {
            if (_t != "")
                _t += " ";
            _t += knight_char_short(_p[_i]);
        }
    }
    if (_t == "")
        _t = "-";
    return _t;
}

// "m:ss.f" from frames (30 per second)
function knight_time_text(_f)
{
    if (_f < 0)
        return "--:--.-";
    var _s = floor(_f / 30);
    var _m = floor(_s / 60);
    var _ss = _s - (_m * 60);
    var _tenth = floor(((_f mod 30) * 10) / 30);
    return string(_m) + ":" + ((_ss < 10) ? "0" : "") + string(_ss) + "." + string(_tenth);
}

function knight_ensure_ctrl()
{
    if (!instance_exists(obj_knight_ctrl))
        instance_create_depth(0, 0, -99000, obj_knight_ctrl);
}

// Susie/Ralsei/... spell display name tweak for the hub menus: Rude Sword is the X-Slash
function knight_spell_label(_name)
{
    if (_name == "Rude Sword")
        return "X-Slash";
    return _name;
}
