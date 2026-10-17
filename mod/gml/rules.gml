
// ===== Knight Hub rules: config, validation, random, challenges, music =====
function knight_cfg_default()
{
    return {
        mode: 0, knight: 0, random: 0, randchal: 0,
        party: [1, 2, 3], song: 0, weird: 0, practice: 0,
        c_items: 0, c_heal: 0, c_hp1: 0, c_solo: 0, c_nohit: 0,
        nh_retry: 0, rush_shuffle: 0, rush_heal: 0, rush_pct: 50,
        c_dmg2: 0, c_halfhp: 0, c_notp: 0, c_onelife: 0, rparty: 0, c_wstats: 0,
        c_twin: 0, c_dark: 0, c_speed: 0, c_thorns: 0, c_time: 0, infhp: 0,
        combo: 0, knight2: 4, p_mode: 0, p_atk: 0, nohotkeys: 0, rmask: knight_remix_default_mask()
    };
}

// fields added after the first release: stored with presets but tolerant when an old file lacks them (not part of the checksum)
function knight_cfg_fields_x()
{
    return ["c_dmg2", "c_halfhp", "c_notp", "c_onelife", "rparty", "c_wstats", "c_twin", "c_dark", "c_speed", "c_thorns", "c_time", "infhp",
            "combo", "knight2", "p_mode", "p_atk", "nohotkeys", "rmask"];
}

function knight_cfg_copy(_c)
{
    var _n = knight_cfg_default();
    var _f = knight_cfg_fields();
    for (var _i = 0; _i < array_length(_f); _i++)
        variable_struct_set(_n, _f[_i], variable_struct_get(_c, _f[_i]));
    var _fx = knight_cfg_fields_x();
    for (var _i = 0; _i < array_length(_fx); _i++)
        variable_struct_set(_n, _fx[_i], variable_struct_exists(_c, _fx[_i]) ? variable_struct_get(_c, _fx[_i]) : 0);
    _n.knight = _c.knight;
    _n.song = _c.song;
    _n.party = [_c.party[0], _c.party[1], _c.party[2]];
    return _n;
}

function knight_flag01(_v)
{
    return (_v == 1) ? 1 : 0;
}

// Brings every field into range. Returns a list of human-readable corrections (empty when nothing changed).
function knight_cfg_sanitize(_c)
{
    var _corr = [];
    var _k = _c.knight;
    if (!is_real(_k) || _k != floor(_k) || _k < 0 || _k >= knight_count())
    {
        _c.knight = 0;
        array_push(_corr, "Unknown knight: Normal Knight selected.");
    }
    var _sg = _c.song;
    if (!is_real(_sg) || _sg != floor(_sg) || _sg < 0 || _sg >= array_length(global.knight_songs))
    {
        _c.song = 0;
        array_push(_corr, "Unknown song: Mod default selected.");
    }
    var _bad = false;
    for (var _i = 0; _i < 3; _i++)
    {
        var _v = _c.party[_i];
        if (!is_real(_v) || _v != floor(_v) || _v < 0 || (_v > 4 && !knight_cc_ok(_v)))
        {
            _c.party[_i] = 0;
            _bad = true;
        }
    }
    if (_bad)
        array_push(_corr, "Unknown party member removed.");
    var _cp = knight_party_compact(_c.party);
    if (_cp[0] != _c.party[0] || _cp[1] != _c.party[1] || _cp[2] != _c.party[2])
    {
        _c.party = _cp;
        array_push(_corr, "Empty party slot closed: members moved up.");
    }
    var _bools = ["mode", "random", "randchal", "weird", "practice", "c_items", "c_heal", "c_hp1", "c_solo", "c_nohit", "nh_retry", "rush_shuffle", "c_dmg2", "c_halfhp", "c_notp", "c_onelife", "rparty", "c_wstats", "c_twin", "c_dark", "c_speed", "c_thorns", "c_time", "infhp", "nohotkeys"];
    for (var _i = 0; _i < array_length(_bools); _i++)
    {
        var _bv = variable_struct_get(_c, _bools[_i]);
        variable_struct_set(_c, _bools[_i], knight_flag01(_bv));
    }
    var _rh = _c.rush_heal;
    if (!is_real(_rh) || _rh < 0 || _rh > 2 || _rh != floor(_rh))
        _c.rush_heal = 0;
    var _rp = _c.rush_pct;
    if (!is_real(_rp))
        _rp = 50;
    _rp = clamp(round(_rp / 10) * 10, 10, 90);
    _c.rush_pct = _rp;
    // build 41: Tag Team / Attack Remix, practice START AT / REPEAT
    var _cb = knight_cfg_num(_c, "combo");
    _c.combo = (_cb == 1 || _cb == 2) ? _cb : 0;
    var _k2 = knight_cfg_num(_c, "knight2");
    _c.knight2 = (_k2 == floor(_k2) && _k2 >= 0 && _k2 < knight_count()) ? _k2 : 0;
    var _pm = knight_cfg_num(_c, "p_mode");
    _c.p_mode = (_pm == 1 || _pm == 2) ? _pm : 0;
    var _pa = knight_cfg_num(_c, "p_atk");
    _c.p_atk = (_pa == floor(_pa) && _pa >= 0 && _pa < array_length(knight_reg(_c.knight).atk)) ? _pa : 0;
    // build 42: the Attack Remix knights (never the joke fight; none = all)
    _c.rmask = knight_remix_mask(_c);
    return _corr;
}

// ---------- fights a configuration will play ----------
function knight_rush_order_default()
{
    return knight_rush_list();
}

function knight_rush_order_shuffled()
{
    var _l = knight_rush_list();
    for (var _i = array_length(_l) - 1; _i > 0; _i--)
    {
        var _j = irandom(_i);
        var _t = _l[_i];
        _l[_i] = _l[_j];
        _l[_j] = _t;
    }
    return _l;
}

// ---------- validation ----------
// the knights a config fights in one battle (Tag Team: both; Attack Remix: the ones switched on and the Normal Knight, which
// opens it and takes the finale; otherwise the plan)
function knight_check_plan(_c, _plan)
{
    var _kind = knight_lu_kind_of(_c);
    if (_kind == "tag")
        return [_c.knight, _c.knight2];
    if (_kind == "remix")
        return knight_remix_list(_c);
    return _plan;
}

// Returns { errors: [], fixes: [], ok } for the fights the config would play.
function knight_check(_c, _plan)
{
    _plan = knight_check_plan(_c, _plan);
    var _r = { errors: [], fixes: [], ok: true };
    var _n = knight_party_size(_c.party);
    if (_n == 0)
        array_push(_r.errors, "The party is empty. Pick at least one member.");
    if (_c.c_solo && _n != 1)
        array_push(_r.errors, "Solo needs exactly one party member (the party has " + string(_n) + ").");
    for (var _i = 0; _i < array_length(_plan); _i++)
    {
        var _reg = knight_reg(_plan[_i]);
        var _where = (_c.mode == 1) ? ("Fight " + string(_i + 1) + " (" + _reg.name + ")") : _reg.name;
        if (_c.c_notp && _reg.key == "elec")
            array_push(_r.errors, _where + ": No TP cannot be used (the last phase needs TP for UNLEASH).");
        if (_c.c_onelife && _reg.key == "elec")
            array_push(_r.errors, _where + ": One life cannot be used (Kris is knocked down by the fight's own script).");
        if (_reg.needs_kris && _n > 0 && !knight_party_has_in(_c.party, 1))
            array_push(_r.errors, _where + " needs Kris in the party.");
        if (_reg.joke && _c.c_nohit)
            array_push(_r.errors, _reg.name + " is a joke fight: it has no No-Hit mode and no records.");
    }
    if (_c.c_nohit && _c.practice && _c.mode == 0 && knight_reg(_c.knight).has_practice)
        array_push(_r.errors, "No-Hit cannot be combined with Practice (practice never awards clears).");
    if (_c.c_time && _c.practice && _c.mode == 0 && knight_reg(_c.knight).has_practice)
        array_push(_r.errors, "Time Limit cannot be combined with Practice (practice never ends in a win).");
    if (_c.c_onelife && _c.weird)
        array_push(_r.errors, "One life cannot be combined with Weird Route (the route removes party members by script).");
    if (_c.c_hp1 && knight_cfg_flag(_c, "infhp"))
        array_push(_r.errors, "1 HP Start cannot be combined with Infinite HP (HP never goes down, so it would stay at 1).");
    // suggested compatible configuration
    var _f = knight_cfg_copy(_c);
    for (var _pass = 0; _pass < 4; _pass++)
    {
        var _sz = knight_party_size(_f.party);
        if (_sz == 0)
            _f.party = [1, 2, 3];
        else if (_f.c_solo && _sz != 1)
            _f.party = [_f.party[0], 0, 0];
        for (var _i = 0; _i < array_length(_plan); _i++)
        {
            var _reg2 = knight_reg(_plan[_i]);
            if (_reg2.needs_kris && !knight_party_has_in(_f.party, 1))
            {
                if (knight_party_size(_f.party) == 1)
                    _f.party = [1, 0, 0];
                else
                    _f.party[0] = 1;
            }
            if (_reg2.joke)
                _f.c_nohit = 0;
            if (_reg2.key == "elec")
            {
                _f.c_notp = 0;
                _f.c_onelife = 0;
            }
        }
        if ((_f.c_nohit || _f.c_time) && _f.practice)
            _f.practice = 0;
        if (_f.c_onelife && _f.weird)
            _f.c_onelife = 0;
        if (_f.c_hp1 && knight_cfg_flag(_f, "infhp"))
            _f.c_hp1 = 0;
    }
    _f.party = knight_party_compact(_f.party);
    if (array_length(_r.errors) > 0)
    {
        _r.fixcfg = _f;
        var _fc = knight_check_quiet(_f, _plan);
        if (_fc)
            array_push(_r.fixes, "Fix: " + knight_cfg_brief(_f) + ".");
        else
            _r.fixcfg = undefined;
    }
    _r.ok = (array_length(_r.errors) == 0);
    return _r;
}

function knight_check_quiet(_c, _plan)
{
    _plan = knight_check_plan(_c, _plan);
    var _n = knight_party_size(_c.party);
    if (_n == 0)
        return false;
    if (_c.c_solo && _n != 1)
        return false;
    for (var _i = 0; _i < array_length(_plan); _i++)
    {
        var _reg = knight_reg(_plan[_i]);
        if (_reg.needs_kris && !knight_party_has_in(_c.party, 1))
            return false;
        if (_reg.joke && _c.c_nohit)
            return false;
        if (_reg.key == "elec" && (_c.c_notp || _c.c_onelife))
            return false;
    }
    if ((_c.c_nohit || _c.c_time) && _c.practice && _c.mode == 0 && knight_reg(_c.knight).has_practice)
        return false;
    if (_c.c_onelife && _c.weird)
        return false;
    if (_c.c_hp1 && knight_cfg_flag(_c, "infhp"))
        return false;
    return true;
}

function knight_cfg_brief(_c)
{
    var _s = (_c.mode == 1) ? "Knight Rush" : knight_reg(_c.knight).name;
    if (knight_lu_kind_of(_c) == "tag")
        _s = "Tag Team " + knight_reg(_c.knight).short + " + " + knight_reg(_c.knight2).short;
    if (knight_lu_kind_of(_c) == "remix")
        _s = "Attack Remix" + ((knight_remix_mask(_c) != knight_remix_default_mask()) ? (" (" + knight_remix_names(_c, ", ") + ")") : "");
    var _names = [];
    for (var _i = 0; _i < 3; _i++)
    {
        if (_c.party[_i] >= 1 && _c.party[_i] <= 5)
            array_push(_names, knight_char_proper(_c.party[_i]));
    }
    _s += " with " + ((array_length(_names) > 0) ? knight_join(_names, ", ") : "nobody");
    var _ch = knight_challenge_names(_c);
    if (array_length(_ch) > 0)
        _s += "; " + knight_join(_ch, ", ");
    return _s;
}

function knight_join(_a, _sep)
{
    var _s = "";
    for (var _i = 0; _i < array_length(_a); _i++)
    {
        if (_i > 0)
            _s += _sep;
        _s += _a[_i];
    }
    return _s;
}

function knight_challenge_names(_c)
{
    var _l = [];
    if (_c.c_nohit) array_push(_l, "No-Hit");
    if (_c.c_items) array_push(_l, "No items");
    if (_c.c_heal) array_push(_l, "No healing");
    if (_c.c_hp1) array_push(_l, "Start at 1 HP");
    if (_c.c_solo) array_push(_l, "Solo");
    if (_c.c_dmg2) array_push(_l, "Double damage");
    if (_c.c_halfhp) array_push(_l, "Half max HP");
    if (_c.c_notp) array_push(_l, "No TP");
    if (_c.c_onelife) array_push(_l, "One life");
    if (_c.c_twin) array_push(_l, "Twin Knight");
    if (_c.c_dark) array_push(_l, "Darkness");
    if (_c.c_speed) array_push(_l, "Hyper speed");
    if (_c.c_thorns) array_push(_l, "Thorns");
    if (_c.c_time) array_push(_l, "Time limit");
    if (_c.c_wstats && _c.weird) array_push(_l, "Weird stats");
    return _l;
}

// ---------- visible, non-blocking adjustments applied at launch ----------
function knight_effective(_c, _k, _corr)
{
    // returns { weird, practice } for fight knight _k and appends notes to _corr
    var _reg = knight_reg(_k);
    var _e = { weird: _c.weird, practice: _c.practice };
    var _kind = knight_lu_kind_of(_c);
    if (_kind != "")
    {
        var _what = (_kind == "tag") ? "Tag Team" : "Attack Remix";
        if (_c.weird)
        {
            _e.weird = 0;
            array_push(_corr, "Weird Route is not part of " + _what + ": it is OFF.");
        }
        if (_c.practice || knight_cfg_num(_c, "p_mode") > 0)
        {
            _e.practice = 0;
            _c.p_mode = 0;
            array_push(_corr, "Practice is not part of " + _what + ": it is OFF.");
        }
        if (_c.c_twin)
        {
            _c.c_twin = 0;
            array_push(_corr, "Twin Knight does not combine with " + _what + ": it is OFF.");
        }
        return _e;
    }
    if (knight_cfg_num(_c, "p_mode") > 0)
    {
        if (_c.mode == 1)
        {
            _c.p_mode = 0;
            array_push(_corr, "Start At / Repeat are not available in Knight Rush: they are OFF.");
        }
        else if (_c.weird)
        {
            _c.p_mode = 0;
            array_push(_corr, "Start At / Repeat use the normal attack list: they are OFF with Weird Route.");
        }
        else if (_c.p_mode == 2 && _c.c_time)
        {
            _c.c_time = 0;
            array_push(_corr, "Repeat never ends the fight: Time Limit is OFF.");
        }
    }
    // Weird Route works with every party since build 37 (without Kris the member who stays to the end finishes the fight)
    if (_c.practice)
    {
        if (_c.mode == 1)
        {
            _e.practice = 0;
            array_push(_corr, "Practice is not available in Knight Rush: it is OFF.");
        }
        else if (!_reg.has_practice)
        {
            _e.practice = 0;
            array_push(_corr, "Practice is not available here: it is OFF.");
        }
    }
    return _e;
}

// ---------- random ----------
function knight_valid_single(_c, _k)
{
    var _t = knight_cfg_copy(_c);
    _t.mode = 0;
    _t.knight = _k;
    return knight_check_quiet(_t, [_k]);
}

function knight_random_knight(_c)
{
    var _l = knight_rush_list();
    var _ok = [];
    for (var _i = 0; _i < array_length(_l); _i++)
    {
        if (knight_valid_single(_c, _l[_i]))
            array_push(_ok, _l[_i]);
    }
    if (array_length(_ok) == 0)
        return -1;
    return _ok[irandom(array_length(_ok) - 1)];
}

function knight_random_challenge(_c, _plan)
{
    // returns the field name of a challenge compatible with the party and fights, or ""
    var _opt = ["c_items", "c_heal", "c_hp1", "c_nohit", "c_dmg2", "c_halfhp", "c_notp", "c_onelife", "c_twin", "c_dark", "c_speed", "c_thorns", "c_time"];
    if (knight_party_size(_c.party) == 1)
        array_push(_opt, "c_solo");
    var _ok = [];
    for (var _i = 0; _i < array_length(_opt); _i++)
    {
        var _t = knight_cfg_copy(_c);
        variable_struct_set(_t, _opt[_i], 1);
        if (knight_check_quiet(_t, _plan))
            array_push(_ok, _opt[_i]);
    }
    if (array_length(_ok) == 0)
        return "";
    return _ok[irandom(array_length(_ok) - 1)];
}

function knight_challenge_label(_f)
{
    switch (_f)
    {
        case "c_items": return "No items";
        case "c_heal": return "No healing";
        case "c_hp1": return "Start at 1 HP";
        case "c_nohit": return "No-Hit";
        case "c_solo": return "Solo";
        case "c_dmg2": return "Double damage";
        case "c_halfhp": return "Half max HP";
        case "c_notp": return "No TP";
        case "c_onelife": return "One life";
        case "c_twin": return "Twin Knight";
        case "c_dark": return "Darkness";
        case "c_speed": return "Hyper speed";
        case "c_thorns": return "Thorns";
        case "c_time": return "Time limit";
    }
    return _f;
}

// ---------- resolve a menu config into a concrete, launchable run ----------
// returns { ok, errors, fixes, fixcfg, corr, cfg, plan, reveal, src }
function knight_resolve(_src)
{
    var _res = { ok: false, errors: [], fixes: [], fixcfg: undefined, corr: [], cfg: undefined, plan: [], reveal: "", src: knight_cfg_copy(_src) };
    var _c = knight_cfg_copy(_src);
    _res.corr = knight_cfg_sanitize(_c);
    if (_c.mode == 0 && _c.random)
    {
        var _k = knight_random_knight(_c);
        if (_k < 0)
        {
            array_push(_res.errors, "No knight fits this party and these challenges, so Random Knight has nothing to pick.");
            _res.cfg = _c;
            _res.fixcfg = undefined;
            return _res;
        }
        // START AT / REPEAT name an attack of the knight picked in the menu: another knight starts over at its first attack
        // (as when the knight is changed in the menu)
        if (_k != _c.knight)
            _c.p_atk = 0;
        _c.knight = _k;
        _res.reveal = "RANDOM KNIGHT: " + knight_reg(_k).name;
    }
    if (knight_lu_kind_of(_c) != "")
        _c.random = 0;
    if (knight_lu_kind_of(_c) == "remix")
        _c.knight = 0;
    var _plan = (_c.mode == 1) ? ((_c.rush_shuffle) ? knight_rush_order_shuffled() : knight_rush_order_default()) : [_c.knight];
    if (_c.randchal)
    {
        var _f = knight_random_challenge(_c, _plan);
        if (_f == "")
        {
            array_push(_res.errors, "No random challenge fits this party and fight, so Random Challenge has nothing to pick.");
            _res.cfg = _c;
            return _res;
        }
        variable_struct_set(_c, _f, 1);
        _res.reveal += ((_res.reveal == "") ? "" : "  ") + "RANDOM CHALLENGE: " + knight_challenge_label(_f);
    }
    var _chk = knight_check(_c, _plan);
    if (!_chk.ok)
    {
        _res.errors = _chk.errors;
        _res.fixes = _chk.fixes;
        if (variable_struct_exists(_chk, "fixcfg"))
            _res.fixcfg = _chk.fixcfg;
        _res.cfg = _c;
        return _res;
    }
    // corrections that do not block the run (shown to the player before the fight starts)
    var _e = knight_effective(_c, _plan[0], _res.corr);
    _c.weird = _e.weird;
    _c.practice = _e.practice;
    _c.random = 0;
    _c.randchal = 0;
    _res.cfg = _c;
    _res.plan = _plan;
    _res.ok = true;
    return _res;
}

// ---------- music ----------
function knight_song_dir()
{
    if (global.launcher)
        return working_directory + "../mus/";
    return "mus/";
}

function knight_music_exists(_f)
{
    if (_f == "")
        return false;
    // build 50: a KF Song Pack song ("@kf:<song_id>": kfsongs/<song_id>/ next to data.win)
    if (knight_kf_id(_f) != "")
        return knight_kf_exists(knight_kf_id(_f));
    // build 48: RANDOM is there when any song file is
    if (_f == "@random")
        return knight_song_random_file() != "";
    var _d = knight_song_dir();
    if (file_exists(_d + _f))
        return true;
    if (!global.launcher && file_exists(working_directory + _d + _f))
        return true;
    return false;
}

// build 48: RANDOM - one of the song files that are there (not the knights' own), a new one each time it is asked for. No random
// call: the game's random numbers (which an online match keeps in step) are not touched
function knight_song_random_index()
{
    var _l = [];
    for (var _i = 0; _i < array_length(global.knight_songs); _i++)
    {
        var _f = global.knight_songs[_i].file;
        if (_f != "" && _f != "@random" && knight_song_on(_i) && knight_music_exists(_f))
            array_push(_l, _i);
    }
    if (array_length(_l) == 0)
        return -1;
    return _l[(current_time + floor(get_timer() / 1000)) mod array_length(_l)];
}

// the same draw as knight_song_random_index, shifted by _n (another pick when the first one repeats the last song)
function knight_song_random_index_n(_n)
{
    var _l = [];
    for (var _i = 0; _i < array_length(global.knight_songs); _i++)
    {
        var _f = global.knight_songs[_i].file;
        if (_f != "" && _f != "@random" && knight_song_on(_i) && knight_music_exists(_f))
            array_push(_l, _i);
    }
    if (array_length(_l) == 0)
        return -1;
    return _l[(current_time + floor(get_timer() / 1000) + _n) mod array_length(_l)];
}

function knight_song_random_file()
{
    var _i = knight_song_random_index();
    return (_i < 0) ? "" : global.knight_songs[_i].file;
}

// the song a fight plays: the one picked, or for RANDOM the one drawn for this run (kept for the whole run)
function knight_song_eff()
{
    var _i = clamp(global.krun.cfg.song, 0, array_length(global.knight_songs) - 1);
    if (global.knight_songs[_i].file != "@random")
        return _i;
    // build 50: KNIGHT RUSH draws a new song for every fight (not the same one twice in a row when there is a choice);
    // a single fight keeps the one drawn for it
    var _r = global.krun;
    var _pos = (_r.mode == 1 && variable_struct_exists(_r, "pos")) ? _r.pos : 0;
    if (!variable_struct_exists(_r, "rand_song") || !variable_struct_exists(_r, "rand_pos") || _r.rand_pos != _pos)
    {
        var _prev = variable_struct_exists(_r, "rand_song") ? _r.rand_song : -1;
        var _new = knight_song_random_index();
        for (var _try = 0; _try < 8 && _new == _prev && _new >= 0; _try++)
            _new = knight_song_random_index_n(_try + 1);
        _r.rand_song = _new;
        _r.rand_pos = _pos;
    }
    // (build 50: no song left for RANDOM - every one turned off, or none there: RANDOM itself, which plays nothing)
    return (_r.rand_song < 0) ? _i : _r.rand_song;
}

function knight_song_find(_file)
{
    for (var _i = 0; _i < array_length(global.knight_songs); _i++)
    {
        if (global.knight_songs[_i].file == _file)
            return _i;
    }
    return 0;
}

// the file the selected knight plays when "Mod default" is chosen
function knight_default_music(_k)
{
    var _reg = knight_reg(_k);
    if (_reg.key == "kaizo")
        return kaizo_set_music("knight.ogg");
    return _reg.music;
}

// called from the fight code: knight_song_file(<original file name>)
function knight_song_file(_f)
{
    if (!variable_global_exists("knight_run") || global.knight_run != 1 || !is_struct(global.krun))
    {
        // outside a hub run keep each mod's own behaviour
        return _f;
    }
    var _k = global.krun.plan[global.krun.pos];
    var _song = global.knight_songs[knight_song_eff()];
    // build 50: a KF Song Pack song plays in place of the battle music (kf_song_start, with its lyrics and credit); the fight
    // gets its own song as a stand-in, which the hub keeps silent (knight_kf_tick)
    // build 50: RANDOM with no song in it (all turned off in the song list): silence - the fight's own song is a silent stand-in
    if (_song.file == "@random")
        knight_kf_request("");
    var _kid = knight_kf_id(_song.file);
    var _kf = (_kid != "" && knight_kf_exists(_kid));
    if (_kf)
        knight_kf_request(_kid);
    if (!_kf && _song.file != "" && knight_music_exists(_song.file))
        return _song.file;
    var _reg = knight_reg(_k);
    var _ren = _reg.music_rename;
    var _r = _f;
    if (is_struct(_ren) && variable_struct_exists(_ren, _f))
        _r = variable_struct_get(_ren, _f);
    if (knight_music_exists(_r))
        return _r;
    return "knight.ogg";
}

// build 47: the credit line of the fight's song ("" for the knights' own music or a missing file)
function knight_song_credit_of(_i)
{
    var _s = global.knight_songs[clamp(_i, 0, array_length(global.knight_songs) - 1)];
    if (_s.file == "" || !variable_struct_exists(_s, "by") || _s.by == "")
        return "";
    return string_upper(_s.name) + " - " + _s.by;
}

function knight_song_credit()
{
    if (!knight_active())
        return "";
    var _i = knight_song_eff();
    if (!knight_music_exists(global.knight_songs[_i].file))
        return "";
    return knight_song_credit_of(_i);
}

// ---------- preview ----------
global.knight_pv_stream = -1;
global.knight_pv_inst = -1;
global.knight_pv_name = "";

function knight_preview_stop()
{
    if (global.knight_pv_inst >= 0)
        audio_stop_sound(global.knight_pv_inst);
    if (global.knight_pv_stream >= 0)
        audio_destroy_stream(global.knight_pv_stream);
    global.knight_pv_inst = -1;
    global.knight_pv_stream = -1;
    global.knight_pv_name = "";
}

function knight_preview_playing()
{
    return global.knight_pv_inst >= 0;
}

// returns "" when playing, else an error text
function knight_preview_start(_f)
{
    knight_preview_stop();
    if (_f == "@random")
    {
        _f = knight_song_random_file();
        if (_f == "")
            return "No songs selected for RANDOM.";
    }
    if (!knight_music_exists(_f))
        return "File not found: " + _f;
    // (a KF Song Pack song: its instrumental)
    var _kid = knight_kf_id(_f);
    var _s = audio_create_stream((_kid != "") ? knight_kf_inst(_kid) : (knight_song_dir() + _f));
    if (_s < 0)
        return "Could not open: " + _f;
    var _i = audio_play_sound(_s, 90, false);
    if (_i < 0)
    {
        audio_destroy_stream(_s);
        return "Could not play: " + _f;
    }
    audio_sound_gain(_i, global.flag[16], 0);
    global.knight_pv_stream = _s;
    global.knight_pv_inst = _i;
    global.knight_pv_name = _f;
    return "";
}

// stop the preview automatically when its file ends
function knight_preview_tick()
{
    if (global.knight_pv_inst >= 0 && !audio_is_playing(global.knight_pv_inst))
        knight_preview_stop();
}

// ---------- presets ----------
// Returns { ok, text, corrections[] } and fills outcfg/outspells when ok.
function knight_preset_decode(_p)
{
    var _out = { ok: false, text: "", corr: [], cfg: knight_cfg_default(), spells: "", equip: "" };
    if (is_undefined(_p))
    {
        _out.text = "Empty slot.";
        return _out;
    }
    if (variable_struct_exists(_p, "future") && _p.future)
    {
        _out.text = "This preset was saved by a newer " + kdr_name() + " and cannot be loaded.";
        return _out;
    }
    var _c = _out.cfg;
    var _ki = knight_find_key(_p.knight);
    if (_ki < 0)
    {
        array_push(_out.corr, "Knight '" + _p.knight + "' no longer exists: Normal Knight used.");
        _ki = 0;
    }
    _c.knight = _ki;
    var _si = knight_song_find(_p.song);
    if (_p.song != "" && global.knight_songs[_si].file != _p.song)
        array_push(_out.corr, "Song '" + _p.song + "' is not in the list: Mod default used.");
    else if (_p.song != "" && !knight_music_exists(_p.song))
        array_push(_out.corr, "Song file '" + _p.song + "' is missing: the knight's own music will play.");
    _c.song = _si;
    for (var _m = 0; _m < 3; _m++)
    {
        var _v = _p.party[_m];
        if (_v < 0 || _v > 4 || _v != floor(_v))
        {
            array_push(_out.corr, "Party slot " + string(_m + 1) + " held an unknown character: emptied.");
            _v = 0;
        }
        _c.party[_m] = _v;
    }
    var _cf = knight_cfg_fields();
    for (var _f = 0; _f < array_length(_cf); _f++)
        variable_struct_set(_c, _cf[_f], variable_struct_get(_p, _cf[_f]));
    var _cx = knight_cfg_fields_x();
    for (var _f = 0; _f < array_length(_cx); _f++)
        variable_struct_set(_c, _cx[_f], variable_struct_exists(_p, _cx[_f]) ? variable_struct_get(_p, _cx[_f]) : 0);
    var _sc = knight_cfg_sanitize(_c);
    for (var _i = 0; _i < array_length(_sc); _i++)
        array_push(_out.corr, _sc[_i]);
    if (_p.ver < 1)
        array_push(_out.corr, "Old preset format: settings it did not store use defaults.");
    // spells: 4 characters x 12 slots, one hex digit each
    var _h = "0123456789abcdef";
    var _s = _p.spells;
    var _fixed = 0;
    var _o = "";
    for (var _i = 0; _i < 48; _i++)
    {
        var _ch = (_i < string_length(_s)) ? string_char_at(_s, _i + 1) : "0";
        var _pos = string_pos(_ch, _h);
        if (_pos <= 0)
        {
            _fixed++;
            _ch = "0";
        }
        _o += _ch;
    }
    if (string_length(_s) != 48)
        _fixed++;
    if (_fixed > 0)
        array_push(_out.corr, "Some saved spells were invalid and were emptied.");
    _out.spells = _o;
    _out.equip = variable_struct_exists(_p, "equip") ? _p.equip : "";
    _out.ok = true;
    return _out;
}

function knight_spells_from_string(_s)
{
    var _h = "0123456789abcdef";
    for (var _c = 1; _c <= 4; _c++)
    {
        for (var _i = 0; _i < 12; _i++)
        {
            var _pos = string_pos(string_char_at(_s, ((_c - 1) * 12) + _i + 1), _h);
            global.spell[_c][_i] = max(0, _pos - 1);
        }
    }
}

function knight_preset_default_name(_slot)
{
    return string_copy("PRESET " + string(_slot + 1), 1, 12);
}

function knight_name_clean(_s)
{
    var _o = "";
    for (var _i = 1; _i <= string_length(_s) && string_length(_o) < 12; _i++)
    {
        var _ch = string_char_at(_s, _i);
        var _code = ord(_ch);
        if (_code >= 32 && _code < 127 && _ch != "=" && _ch != "[" && _ch != "]" && _ch != ";" && _ch != "\"" && _ch != "\\")
            _o += _ch;
    }
    while (string_length(_o) > 0 && string_char_at(_o, string_length(_o)) == " ")
        _o = string_copy(_o, 1, string_length(_o) - 1);
    while (string_length(_o) > 0 && string_char_at(_o, 1) == " ")
        _o = string_delete(_o, 1, 1);
    return _o;
}

function knight_preset_save(_slot, _name)
{
    var _n = knight_name_clean(_name);
    if (_n == "")
        _n = knight_preset_default_name(_slot);
    var _p = knight_cfg_to_preset(global.knight_cfg, _n);
    _p.spells = knight_spells_to_string();
    _p.equip = knight_equip_to_string();
    global.knight_presets[_slot] = _p;
    return knight_store_save();
}

function knight_preset_rename(_slot, _name)
{
    var _p = global.knight_presets[_slot];
    if (is_undefined(_p))
        return false;
    var _n = knight_name_clean(_name);
    if (_n == "")
        return false;
    _p.name = _n;
    return knight_store_save();
}

function knight_preset_delete(_slot)
{
    global.knight_presets[_slot] = undefined;
    return knight_store_save();
}

// apply a decoded preset to the live menu state
// returns a list of notes about anything that had to be corrected while applying
function knight_preset_apply(_dec)
{
    var _notes = [];
    global.knight_cfg = _dec.cfg;
    knight_spells_from_string(_dec.spells);
    var _bad = knight_equip_from_string(_dec.equip);
    if (_bad > 0)
        array_push(_notes, "Some saved equipment was not valid for its character and was emptied.");
    if (knight_mantle_fix() > 0)
        array_push(_notes, "Only one Shadow Mantle per setup: the extra one was taken off.");
    return _notes;
}

// is the Shadow Mantle worn anywhere but armor slot _k of character _c?
function knight_mantle_elsewhere(_c, _k)
{
    for (var _o = 1; _o <= 4; _o++)
    {
        for (var _s = 1; _s <= 2; _s++)
        {
            if ((_o != _c || _s != _k) && knight_equip_get(_o, _s) == 23)
                return true;
        }
    }
    return false;
}

// ---------- equipment ----------
// kinds: 0 weapon, 1 armor 1, 2 armor 2. Item ids come from the game's own scr_weaponinfo / scr_armorinfo.
function knight_equip_max(_k)
{
    // build 50: ids 30-35 are the custom characters' own gear (Flowery: WinningSmile; PetalMantle, SundayBest)
    return 35;
}

function knight_equip_get(_c, _k)
{
    if (_k == 0)
        return global.charweapon[_c];
    if (_k == 1)
        return global.chararmor1[_c];
    return global.chararmor2[_c];
}

function knight_equip_set(_c, _k, _v)
{
    if (_k == 0)
        global.charweapon[_c] = _v;
    else if (_k == 1)
        global.chararmor1[_c] = _v;
    else
        global.chararmor2[_c] = _v;
}

// { name, ok (this character can wear it), at, df, mag } for item _id of kind _k
function knight_equip_info(_k, _id, _c)
{
    var _r = { name: "", ok: false, at: 0, df: 0, mag: 0 };
    // build 50: past the game's last item only the custom characters' gear (ids 30-35) is an item
    if (((_k == 0 && _id > 26) || (_k > 0 && _id > 27)) && knight_cc_gear_owner(_k, _id) == 0)
    {
        _r.name = "(none)";
        return _r;
    }
    var _ccg = ((_k == 0 && _id > 26) || (_k > 0 && _id > 27));
    if (_k == 0)
    {
        if (_ccg)
            knight_cc_weaponinfo(_id);
        else
            scr_weaponinfo(_id);
        _r.name = weaponnametemp;
        _r.at = weaponattemp;
        _r.df = weapondftemp;
        _r.mag = weaponmagtemp;
        switch (_c)
        {
            case 1: _r.ok = (weaponchar1temp == 1); break;
            case 2: _r.ok = (weaponchar2temp == 1); break;
            case 3: _r.ok = (weaponchar3temp == 1); break;
            case 4: _r.ok = (weaponchar4temp == 1); break;
            default: _r.ok = knight_cc_ok(_c) && knight_cc_gear_ok(_c, 0, _id); break;
        }
    }
    else
    {
        if (_ccg)
            knight_cc_armorinfo(_id);
        else
            scr_armorinfo(_id);
        _r.name = armornametemp;
        _r.at = armorattemp;
        _r.df = armordftemp;
        _r.mag = armormagtemp;
        switch (_c)
        {
            case 1: _r.ok = (armorchar1temp == 1); break;
            case 2: _r.ok = (armorchar2temp == 1); break;
            case 3: _r.ok = (armorchar3temp == 1); break;
            case 4: _r.ok = (armorchar4temp == 1); break;
            default: _r.ok = knight_cc_ok(_c) && (knight_cc_gear_ok(_c, _k, _id) || (_id <= 27 && armorchar1temp == 1 && armorchar2temp == 1 && armorchar3temp == 1 && armorchar4temp == 1)); break;
        }
    }
    if (_id == 0)
        _r.ok = true;
    if (string_length(string_replace_all(_r.name, " ", "")) == 0)
        _r.name = "(none)";
    return _r;
}

// recompute the game's equipment totals (global.itemat / itemdf / itemmag ...) from the current choices
function knight_equip_refresh()
{
    scr_weaponinfo_mine();
    scr_armorinfo_mine();
}

// move to the next item of this slot that the character can use; returns the new id
function knight_equip_step(_c, _k, _dir)
{
    var _max = knight_equip_max(_k);
    var _v = knight_equip_get(_c, _k);
    for (var _t = 0; _t <= _max + 1; _t++)
    {
        _v = (_v + _dir + _max + 1) mod (_max + 1);
        // stepping past the Shadow Mantle never takes it from whoever wears it (picking it from the list does)
        if (_k > 0 && _v == 23 && knight_mantle_elsewhere(_c, _k))
            continue;
        if (knight_equip_info(_k, _v, _c).ok)
        {
            knight_equip_set(_c, _k, _v);
            knight_equip_refresh();
            return _v;
        }
    }
    return knight_equip_get(_c, _k);
}

function knight_equip_clear(_c, _k)
{
    knight_equip_set(_c, _k, 0);
    knight_equip_refresh();
}

// the item a character wore when the hub was opened (always allowed: the game's own starting gear is not always flagged as wearable)
function knight_equip_orig(_c, _k)
{
    if (is_undefined(global.knight_orig))
        return -1;
    return global.knight_orig.eq[_k][_c];
}

// 12 characters: Kris, Susie, Ralsei, Noelle x (weapon, armor 1, armor 2); one base-36 digit each
// (build 50: Flowery's gear and techniques are kept on their own - knight_fl_to_string)
function knight_equip_to_string()
{
    var _h = "0123456789abcdefghijklmnopqrstuvwxyz";
    var _s = "";
    for (var _c = 1; _c <= 4; _c++)
    {
        for (var _k = 0; _k < 3; _k++)
            _s += string_char_at(_h, clamp(knight_equip_get(_c, _k), 0, 35) + 1);
    }
    return _s;
}

// returns the number of entries that were not valid (emptied); "" leaves everything untouched
function knight_equip_from_string(_s)
{
    if (string_length(_s) == 0)
        return 0;
    var _h = "0123456789abcdefghijklmnopqrstuvwxyz";
    var _bad = 0;
    var _len = string_length(_s);
    if (_len != 12 && _len != 15)
        _bad++;
    for (var _c = 1; _c <= ((_len >= 15) ? 5 : 4); _c++)
    {
        for (var _k = 0; _k < 3; _k++)
        {
            var _ch = ((_c - 1) * 3) + _k + 1;
            var _id = 0;
            if (_ch <= string_length(_s))
            {
                var _pos = string_pos(string_char_at(_s, _ch), _h);
                if (_pos > 0)
                    _id = _pos - 1;
                else
                    _bad++;
            }
            if (_id > knight_equip_max(_k) || (!knight_equip_info(_k, _id, _c).ok && _id != knight_equip_orig(_c, _k)))
            {
                if (_id != 0)
                    _bad++;
                _id = 0;
            }
            knight_equip_set(_c, _k, _id);
        }
    }
    knight_cc_gear_default(false);
    knight_equip_refresh();
    return _bad;
}


// ===== build 50: the KF Song Pack (kfsongs/<song_id>/ next to data.win; scr_kf_song / scr_kf_lyrics_fx / obj_kf_songlyrics) =====
// A song of the list whose file is "@kf:<song_id>" plays through kf_song_start in place of the fight's battle music: the
// instrumental and the vocal stem in sync, its lyrics and its credit (the NOW PLAYING card, the MUSIC: tag - always on). The
// fight still starts its own song (the game's music code stays as it is), as a silent stand-in: while that stand-in plays the
// pack's song plays, when the fight cuts it the pack's song pauses, when the fight starts it again the pack's song goes on; at
// its end the pack's song starts over (like the battle music loops). It ends with the fight. Its credit is the hub's own song
// card (top right, the fight's first seconds), not the pack's NOW PLAYING card / MUSIC tag.
global.knight_kf = undefined;
global.kf_card_y = 12;

function knight_kf_id(_f)
{
    if (is_string(_f) && string_length(_f) > 4 && string_copy(_f, 1, 4) == "@kf:")
        return string_delete(_f, 1, 4);
    return "";
}

function knight_kf_exists(_id)
{
    return _id != "" && kf_song_path("kfsongs/" + _id + "/song.json") != "" && knight_kf_inst(_id) != "";
}

// the instrumental's path ("" when it is not there)
function knight_kf_inst(_id)
{
    var _p = kf_song_path("kfsongs/" + _id + "/song.json");
    if (_p == "")
        return "";
    var _m = undefined;
    try
    {
        _m = json_parse(kf_song_read_text(_p));
    }
    catch (_e)
    {
        return "";
    }
    if (!is_struct(_m) || !variable_struct_exists(_m, "instrumental"))
        return "";
    return kf_song_path("kfsongs/" + _id + "/" + _m.instrumental);
}

function knight_kf_on()
{
    return is_struct(global.knight_kf) && global.knight_kf.live;
}

// the fight asked for its battle song (knight_song_file): the stand-in it is about to start is taken as the pack song's
function knight_kf_request(_id)
{
    var _r = global.krun;
    var _key = string(global.knight_run_counter) + ":" + string(_r.pos);
    var _k = global.knight_kf;
    var _same = is_struct(_k) && _k.key == _key && _k.sid == _id;
    if (!_same)
    {
        knight_kf_stop();
        _k = { sid: _id, key: _key, live: true, started: false, stream: -1, inst: -1, old1: -1, afloor: -1, pend: true, paused: false };
        global.knight_kf = _k;
    }
    // (the same fight starting its song again - a phase's restart: the new stand-in is taken, the pack's song goes on)
    _k.pend = true;
    _k.live = true;
    _k.old1 = (knight_mus_ok() ? global.batmusic[1] : -1);
    // (snd_init makes an obj_astream for the stream it opens: the stand-in's is the first one made after this)
    var _fl = -1;
    with (obj_astream)
        _fl = max(_fl, id);
    _k.afloor = _fl;
    return 1;
}

function knight_kf_stop()
{
    var _k = global.knight_kf;
    if (is_struct(_k) && _k.started)
        kf_song_end();
    if (is_struct(_k) && is_real(_k.stream) && _k.stream >= 0 && audio_exists(_k.stream))
        audio_sound_gain(_k.stream, 1, 0);
    global.knight_kf = undefined;
    return 1;
}

// every frame of a run (not while paused: the pause pauses every sound itself)
function knight_kf_tick()
{
    var _k = global.knight_kf;
    if (!is_struct(_k))
        return 0;
    var _r = global.krun;
    if (!is_struct(_r) || (_r.state != "battle" && _r.state != "arena") || !_k.live)
        return knight_kf_stop();
    // the hub's lines stay readable: the credit card and the lyrics go under them
    var _n = array_length(knight_hud_lines());
    global.kf_card_y = 8 + (_n * 16);
    with (asset_get_index("obj_kf_songlyrics"))
        lyric_y = 26 + (_n * 16);
    if (!knight_mus_ok())
        return 0;
    // the stand-in: the stream the fight made right after it asked (silent from the start - its own gain - and every frame)
    if (_k.pend)
    {
        var _b0 = global.batmusic[0];
        var _hit = false;
        var _afl = _k.afloor;
        with (obj_astream)
        {
            if (id > _afl && mystream == _b0)
                _hit = true;
        }
        if (_hit && is_real(_b0) && _b0 >= 0)
        {
            _k.stream = _b0;
            _k.pend = false;
            audio_sound_gain(_k.stream, 0, 0);
        }
    }
    if (_k.stream == -1 || global.batmusic[0] != _k.stream)
    {
        // (the fight is on another song of its own now - a scene's: the pack's song waits)
        if (_k.started && !_k.paused && kf_song_is_playing(global.kf_song))
        {
            kf_song_pause(global.kf_song);
            _k.paused = true;
        }
        return 0;
    }
    var _i = global.batmusic[1];
    var _on = (is_real(_i) && _i != _k.old1 && _i >= 0 && audio_is_playing(_i));
    if (_on)
        audio_sound_gain(_i, 0, 0);
    // (silence: RANDOM with every song turned off - nothing of the pack's to play)
    if (_k.sid == "")
        return 1;
    if (!_on)
    {
        if (_k.started && !_k.paused && kf_song_is_playing(global.kf_song))
        {
            kf_song_pause(global.kf_song);
            _k.paused = true;
        }
        return 0;
    }
    // the stand-in plays: so does the pack's song (started, resumed, or started over at its end)
    if (!_k.started || is_undefined(global.kf_song) || !instance_exists(asset_get_index("obj_kf_songlyrics")))
    {
        var _cfg = kf_song_settings();
        // (the hub's own song card credits it - "MUSIC: <title> - DIGITAL DESCENDANT", the first seconds of the fight -
        // in place of the pack's NOW PLAYING card and its always-on MUSIC tag)
        _cfg.credit = false;
        // (and its lyrics are the hub's own - knight_lyr_kf, the Raise Up Your Bat / Flower Man style - not the pack's)
        _cfg.lyrics = false;
        _cfg.volume = global.flag[16];
        kf_song_start(_k.sid);
        _k.started = true;
        _k.paused = false;
        with (asset_get_index("obj_kf_songlyrics"))
            lyric_y = 26 + (_n * 16);
        return 1;
    }
    if (_k.paused)
    {
        kf_song_resume(global.kf_song);
        _k.paused = false;
    }
    if (global.kf_song.volume != global.flag[16])
        kf_song_set_volume(global.kf_song, global.flag[16]);
    return 1;
}


// ===== build 50: the songs in RANDOM - every player's own choice (the song list: A turns a song on / off for RANDOM) =====
// Every song is in RANDOM unless turned off; a song added later starts on. Kept in knighthub_songs.ini, section "off", one key
// per song turned off - the key is the song's id (its file, never its place in the list), so it survives the list changing.
// Only RANDOM's draw (offline and online) looks at it; a song picked by name plays, and the online KNIGHTMARE / FINAL TWO
// songs are their own (kfo_mus_situ). With every song off, RANDOM plays nothing.
global.knight_song_off = undefined;
function knight_song_ini()
{
    return "knighthub_songs.ini";
}

function knight_song_key(_id)
{
    var _o = "";
    for (var _c = 1; _c <= string_length(_id); _c++)
    {
        var _ch = string_char_at(_id, _c);
        var _a = ord(_ch);
        _o += ((_a >= 48 && _a <= 57) || (_a >= 65 && _a <= 90) || (_a >= 97 && _a <= 122)) ? _ch : "_";
    }
    return "s_" + _o;
}

// a song RANDOM can play (not MOD DEFAULT, not RANDOM)
function knight_song_real(_i)
{
    if (_i < 0 || _i >= array_length(global.knight_songs))
        return false;
    var _f = global.knight_songs[_i].file;
    return _f != "" && _f != "@random";
}

function knight_song_off_load()
{
    if (is_struct(global.knight_song_off))
        return global.knight_song_off;
    global.knight_song_off = {};
    if (file_exists(knight_song_ini()))
    {
        ini_open(knight_song_ini());
        for (var _i = 0; _i < array_length(global.knight_songs); _i++)
        {
            if (!knight_song_real(_i))
                continue;
            var _k = knight_song_key(global.knight_songs[_i].sid);
            if (ini_read_real("off", _k, 0) == 1)
                variable_struct_set(global.knight_song_off, _k, 1);
        }
        ini_close();
    }
    return global.knight_song_off;
}

function knight_song_off_save()
{
    var _off = knight_song_off_load();
    ini_open(knight_song_ini());
    ini_section_delete("off");
    var _ks = variable_struct_get_names(_off);
    for (var _j = 0; _j < array_length(_ks); _j++)
        ini_write_real("off", _ks[_j], 1);
    ini_write_real("meta", "v", 1);
    ini_close();
    return 1;
}

function knight_song_on(_i)
{
    if (!knight_song_real(_i))
        return true;
    return !variable_struct_exists(knight_song_off_load(), knight_song_key(global.knight_songs[_i].sid));
}

function knight_song_set_on(_i, _on)
{
    if (!knight_song_real(_i))
        return 0;
    var _off = knight_song_off_load();
    var _k = knight_song_key(global.knight_songs[_i].sid);
    if (_on && variable_struct_exists(_off, _k))
        variable_struct_remove(_off, _k);
    if (!_on)
        variable_struct_set(_off, _k, 1);
    knight_song_off_save();
    return 1;
}

function knight_song_set_all(_on)
{
    var _off = knight_song_off_load();
    var _ks = variable_struct_get_names(_off);
    for (var _j = 0; _j < array_length(_ks); _j++)
        variable_struct_remove(_off, _ks[_j]);
    if (!_on)
    {
        for (var _i = 0; _i < array_length(global.knight_songs); _i++)
        {
            if (knight_song_real(_i))
                variable_struct_set(_off, knight_song_key(global.knight_songs[_i].sid), 1);
        }
    }
    knight_song_off_save();
    return 1;
}

// how many songs RANDOM can draw now (turned on and there)
function knight_song_on_count()
{
    var _n = 0;
    for (var _i = 0; _i < array_length(global.knight_songs); _i++)
    {
        if (knight_song_real(_i) && knight_song_on(_i) && knight_music_exists(global.knight_songs[_i].file))
            _n++;
    }
    return _n;
}

// the exact list entry of a file (-1: none)
function knight_song_find_exact(_file)
{
    for (var _i = 0; _i < array_length(global.knight_songs); _i++)
    {
        if (global.knight_songs[_i].file == _file)
            return _i;
    }
    return -1;
}
