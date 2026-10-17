
// ===== Knight Hub persistence: records + presets + last settings =====
// File: knight_hub.ini (separate from dr.ini / story saves). knight_hub.bak is the last known-good copy.
global.knight_rec = {};
global.knight_presets = [];
global.knight_main_valid = false;
global.knight_save_fail = false;
// spell/equipment sets last used in the hub (restored whenever the hub menu is opened); "" = none saved yet
global.knight_last_spells = "";
global.knight_last_fl = "";
global.knight_last_equip = "";

function knight_store_file()
{
    return "knight_hub.ini";
}

function knight_store_bak()
{
    return "knight_hub.bak";
}

function knight_store_schema()
{
    return 1;
}

function knight_preset_slots()
{
    return 8;
}

function knight_rec_fields()
{
    return ["att", "win", "best", "lowdmg", "streak", "cur", "aband", "far"];
}

function knight_rec_blank()
{
    return { att: 0, win: 0, best: 0, lowdmg: -1, streak: 0, cur: 0, aband: 0, far: 0, cfg: "" };
}

function knight_rec_cats(_key)
{
    if (_key == "rush")
        return ["rush", "rushnh"];
    if (_key == "tag" || _key == "remix")
        return ["st", "ch", "nh"];
    return ["st", "ch", "nh", "pr"];
}

// record keys: every non-joke knight, then "rush", then the build 41 modes. Joke fights are never recorded.
function knight_rec_keys()
{
    var _l = [];
    for (var _i = 0; _i < knight_count(); _i++)
    {
        if (!knight_reg(_i).joke)
            array_push(_l, knight_reg(_i).key);
    }
    array_push(_l, "rush");
    array_push(_l, "tag");
    array_push(_l, "remix");
    return _l;
}

// record tables added after the first release: a file written before them simply has none (blank records, nothing to check)
function knight_rec_key_new(_key)
{
    return (_key == "tag" || _key == "remix");
}

function knight_rec_title(_key)
{
    if (_key == "rush")
        return "KNIGHT RUSH";
    if (_key == "tag")
        return "TAG TEAM";
    if (_key == "remix")
        return "ATTACK REMIX";
    var _k = knight_find_key(_key);
    return (_k >= 0) ? string_upper(knight_reg(_k).name) : string_upper(_key);
}

function knight_rec_reset()
{
    global.knight_rec = {};
    var _keys = knight_rec_keys();
    for (var _k = 0; _k < array_length(_keys); _k++)
    {
        var _e = {};
        var _cats = knight_rec_cats(_keys[_k]);
        for (var _c = 0; _c < array_length(_cats); _c++)
            variable_struct_set(_e, _cats[_c], knight_rec_blank());
        variable_struct_set(global.knight_rec, _keys[_k], _e);
    }
}

function knight_rec_get(_key, _cat)
{
    if (!variable_struct_exists(global.knight_rec, _key))
        return undefined;
    var _e = variable_struct_get(global.knight_rec, _key);
    if (!variable_struct_exists(_e, _cat))
        return undefined;
    return variable_struct_get(_e, _cat);
}

function knight_presets_reset()
{
    global.knight_presets = [];
    for (var _i = 0; _i < knight_preset_slots(); _i++)
        global.knight_presets[_i] = undefined;
}

// ---------- checksum ----------
function knight_sum_add(_s, _v)
{
    if (is_string(_v))
    {
        _s = (_s * 31 + string_length(_v)) mod 1000003;
        for (var _i = 1; _i <= string_length(_v); _i++)
            _s = (_s * 31 + ord(string_char_at(_v, _i))) mod 1000003;
        return _s;
    }
    return (_s * 31 + floor(abs(_v)) + (_v < 0 ? 7 : 0)) mod 1000003;
}

function knight_cfg_fields()
{
    return ["mode", "random", "randchal", "weird", "practice", "c_items", "c_heal", "c_hp1", "c_solo", "c_nohit", "nh_retry", "rush_shuffle", "rush_heal", "rush_pct"];
}

// config -> preset-shaped struct (knight/music by NAME so reordering never changes meaning)
function knight_cfg_to_preset(_cfg, _name)
{
    var _p = { used: true, name: _name, ver: 1 };
    _p.knight = knight_reg(_cfg.knight).key;
    _p.party = [_cfg.party[0], _cfg.party[1], _cfg.party[2]];
    _p.song = global.knight_songs[clamp(_cfg.song, 0, array_length(global.knight_songs) - 1)].file;
    var _f = knight_cfg_fields();
    for (var _i = 0; _i < array_length(_f); _i++)
        variable_struct_set(_p, _f[_i], variable_struct_get(_cfg, _f[_i]));
    var _fx = knight_cfg_fields_x();
    for (var _i = 0; _i < array_length(_fx); _i++)
        variable_struct_set(_p, _fx[_i], variable_struct_exists(_cfg, _fx[_i]) ? variable_struct_get(_cfg, _fx[_i]) : 0);
    return _p;
}

function knight_spells_to_string()
{
    var _h = "0123456789abcdef";
    var _s = "";
    for (var _c = 1; _c <= 4; _c++)
    {
        for (var _i = 0; _i < 12; _i++)
            _s += string_char_at(_h, clamp(global.spell[_c][_i], 0, 15) + 1);
    }
    return _s;
}

// ---------- ini helpers (every read reports "missing" through a sentinel) ----------
function knight_ini_num(_sec, _key)
{
    if (!ini_key_exists(_sec, _key))
        return undefined;
    var _v = ini_read_real(_sec, _key, 0);
    return _v;
}

function knight_ini_str(_sec, _key)
{
    if (!ini_key_exists(_sec, _key))
        return undefined;
    return ini_read_string(_sec, _key, "");
}

// ---------- parse a file into a result struct WITHOUT touching globals ----------
// result.st: "ok" | "missing" | "schema" | "incomplete" | "corrupt"
function knight_store_parse(_name)
{
    var _res = { st: "ok", rec: {}, pre: [], last: undefined, fixed: 0 };
    if (!file_exists(_name))
    {
        _res.st = "missing";
        return _res;
    }
    ossafe_ini_open(_name);
    var _schema = knight_ini_num("meta", "schema");
    if (is_undefined(_schema))
        _res.st = "corrupt";
    else if (_schema != knight_store_schema())
        _res.st = "schema";
    else if (is_undefined(knight_ini_num("meta", "done")) || knight_ini_num("meta", "done") != 1)
        _res.st = "incomplete";
    if (_res.st != "ok")
    {
        ossafe_ini_close();
        return _res;
    }
    var _sumrec = 0;
    var _keys = knight_rec_keys();
    var _flds = knight_rec_fields();
    for (var _k = 0; _k < array_length(_keys) && _res.st == "ok"; _k++)
    {
        var _e = {};
        var _cats = knight_rec_cats(_keys[_k]);
        if (knight_rec_key_new(_keys[_k]) && !ini_section_exists("rec_" + _keys[_k] + "_" + _cats[0]))
            continue;
        for (var _c = 0; _c < array_length(_cats) && _res.st == "ok"; _c++)
        {
            var _r = knight_rec_blank();
            var _sec = "rec_" + _keys[_k] + "_" + _cats[_c];
            for (var _f = 0; _f < array_length(_flds); _f++)
            {
                var _v = knight_ini_num(_sec, _flds[_f]);
                if (is_undefined(_v))
                {
                    _res.st = "incomplete";
                    break;
                }
                _sumrec = knight_sum_add(_sumrec, _v);
                var _ok = (_flds[_f] == "lowdmg") ? (_v >= -1 && _v < 100000000) : (_v >= 0 && _v < 100000000);
                if (!_ok || _v != floor(_v))
                {
                    _res.fixed++;
                    _v = (_flds[_f] == "lowdmg") ? -1 : 0;
                }
                variable_struct_set(_r, _flds[_f], _v);
            }
            var _s = knight_ini_str(_sec, "cfg");
            if (is_undefined(_s))
                _res.st = "incomplete";
            else
            {
                _sumrec = knight_sum_add(_sumrec, _s);
                _r.cfg = string_copy(_s, 1, 60);
            }
            variable_struct_set(_e, _cats[_c], _r);
        }
        variable_struct_set(_res.rec, _keys[_k], _e);
    }
    if (_res.st == "ok")
    {
        var _stored = knight_ini_num("meta", "sumrec");
        if (is_undefined(_stored) || _stored != _sumrec)
            _res.st = "corrupt";
    }
    // presets
    var _sumpre = 0;
    var _slots = knight_preset_slots();
    for (var _i = 0; _i < _slots && _res.st == "ok"; _i++)
    {
        var _sec = "preset" + string(_i);
        var _used = knight_ini_num(_sec, "used");
        if (is_undefined(_used))
        {
            _res.st = "incomplete";
            break;
        }
        _sumpre = knight_sum_add(_sumpre, _used);
        if (_used != 1)
        {
            _res.pre[_i] = undefined;
            continue;
        }
        var _p = { used: true };
        var _sn = knight_ini_str(_sec, "name");
        var _sv = knight_ini_num(_sec, "ver");
        if (is_undefined(_sn) || is_undefined(_sv))
        {
            _res.st = "incomplete";
            break;
        }
        _sumpre = knight_sum_add(_sumpre, _sn);
        _sumpre = knight_sum_add(_sumpre, _sv);
        _p.name = string_copy(_sn, 1, 12);
        _p.ver = _sv;
        if (_sv > 1)
        {
            // written by a newer version of the hub: keep the slot but mark unusable
            _p.future = true;
            _res.pre[_i] = _p;
            continue;
        }
        var _sk = knight_ini_str(_sec, "knight");
        var _ss = knight_ini_str(_sec, "song");
        var _sp = knight_ini_str(_sec, "spells");
        if (is_undefined(_sk) || is_undefined(_ss) || is_undefined(_sp))
        {
            _res.st = "incomplete";
            break;
        }
        _sumpre = knight_sum_add(_sumpre, _sk);
        _sumpre = knight_sum_add(_sumpre, _ss);
        _sumpre = knight_sum_add(_sumpre, _sp);
        _p.knight = _sk;
        _p.song = _ss;
        _p.spells = _sp;
        // optional (added later): presets saved without it simply keep the current equipment
        var _se = knight_ini_str(_sec, "equip");
        _p.equip = "";
        if (!is_undefined(_se))
        {
            _sumpre = knight_sum_add(_sumpre, _se);
            _p.equip = _se;
        }
        _p.party = [0, 0, 0];
        for (var _m = 0; _m < 3; _m++)
        {
            var _pv = knight_ini_num(_sec, "party" + string(_m));
            if (is_undefined(_pv))
            {
                _res.st = "incomplete";
                break;
            }
            _sumpre = knight_sum_add(_sumpre, _pv);
            _p.party[_m] = _pv;
        }
        var _cf = knight_cfg_fields();
        for (var _f = 0; _f < array_length(_cf) && _res.st == "ok"; _f++)
        {
            var _fv = knight_ini_num(_sec, _cf[_f]);
            if (is_undefined(_fv))
            {
                _res.st = "incomplete";
                break;
            }
            _sumpre = knight_sum_add(_sumpre, _fv);
            variable_struct_set(_p, _cf[_f], _fv);
        }
        var _cfx = knight_cfg_fields_x();
        for (var _f = 0; _f < array_length(_cfx); _f++)
        {
            var _fvx = knight_ini_num(_sec, _cfx[_f]);
            variable_struct_set(_p, _cfx[_f], (is_undefined(_fvx) || !is_real(_fvx)) ? 0 : _fvx);
        }
        _res.pre[_i] = _p;
    }
    if (_res.st == "ok")
    {
        var _stored2 = knight_ini_num("meta", "sumpre");
        if (is_undefined(_stored2) || _stored2 != _sumpre)
            _res.st = "corrupt";
    }
    // last-used settings (not checksummed: any damage just falls back to defaults field by field)
    if (_res.st == "ok" && ini_section_exists("last"))
    {
        var _l = { knight: "", song: "", party: [0, 0, 0], spells: "", equip: "" };
        var _lk = knight_ini_str("last", "knight");
        var _ls = knight_ini_str("last", "song");
        _l.knight = is_undefined(_lk) ? "" : _lk;
        _l.song = is_undefined(_ls) ? "" : _ls;
        for (var _m = 0; _m < 3; _m++)
        {
            var _pv = knight_ini_num("last", "party" + string(_m));
            _l.party[_m] = is_undefined(_pv) ? -1 : _pv;
        }
        var _cf2 = knight_cfg_fields();
        for (var _f = 0; _f < array_length(_cf2); _f++)
        {
            var _fv2 = knight_ini_num("last", _cf2[_f]);
            variable_struct_set(_l, _cf2[_f], is_undefined(_fv2) ? 0 : _fv2);
        }
        var _cf2x = knight_cfg_fields_x();
        for (var _f = 0; _f < array_length(_cf2x); _f++)
        {
            var _fv2x = knight_ini_num("last", _cf2x[_f]);
            variable_struct_set(_l, _cf2x[_f], (is_undefined(_fv2x) || !is_real(_fv2x)) ? 0 : _fv2x);
        }
        var _lsp = knight_ini_str("last", "spells");
        var _leq = knight_ini_str("last", "equip");
        _l.spells = (!is_undefined(_lsp) && string_length(_lsp) == 48) ? _lsp : "";
        _l.equip = (!is_undefined(_leq) && string_length(_leq) == 12) ? _leq : "";
        var _lfl = knight_ini_str("last", "flowery");
        _l.flowery = is_undefined(_lfl) ? "" : _lfl;
        _res.last = _l;
    }
    ossafe_ini_close();
    return _res;
}

// ---------- apply a parsed result to the live state ----------
function knight_store_apply(_r)
{
    knight_rec_reset();
    var _keys = knight_rec_keys();
    for (var _k = 0; _k < array_length(_keys); _k++)
    {
        if (!variable_struct_exists(_r.rec, _keys[_k]))
            continue;
        var _cats = knight_rec_cats(_keys[_k]);
        for (var _c = 0; _c < array_length(_cats); _c++)
        {
            var _src = variable_struct_get(variable_struct_get(_r.rec, _keys[_k]), _cats[_c]);
            variable_struct_set(variable_struct_get(global.knight_rec, _keys[_k]), _cats[_c], _src);
        }
    }
    knight_presets_reset();
    for (var _i = 0; _i < array_length(_r.pre) && _i < knight_preset_slots(); _i++)
        global.knight_presets[_i] = _r.pre[_i];
    global.knight_cfg = knight_cfg_default();
    if (!is_undefined(_r.last))
        knight_cfg_from_last(_r.last);
}

function knight_cfg_from_last(_l)
{
    var _c = global.knight_cfg;
    var _ki = knight_find_key(_l.knight);
    if (_ki >= 0)
        _c.knight = _ki;
    _c.song = knight_song_find(_l.song);
    for (var _m = 0; _m < 3; _m++)
    {
        if (_l.party[_m] >= 0 && _l.party[_m] <= knight_cc_max_id())
            _c.party[_m] = _l.party[_m];
    }
    var _cf = knight_cfg_fields();
    for (var _f = 0; _f < array_length(_cf); _f++)
        variable_struct_set(_c, _cf[_f], variable_struct_get(_l, _cf[_f]));
    var _cfx = knight_cfg_fields_x();
    for (var _f = 0; _f < array_length(_cfx); _f++)
        variable_struct_set(_c, _cfx[_f], variable_struct_exists(_l, _cfx[_f]) ? variable_struct_get(_l, _cfx[_f]) : 0);
    knight_cfg_sanitize(_c);
    global.knight_last_spells = variable_struct_exists(_l, "spells") ? _l.spells : "";
    global.knight_last_equip = variable_struct_exists(_l, "equip") ? _l.equip : "";
    global.knight_last_fl = variable_struct_exists(_l, "flowery") ? _l.flowery : "";
}

function knight_store_load()
{
    if (global.knight_loaded)
        return 0;
    global.knight_loaded = true;
    knight_rec_reset();
    knight_presets_reset();
    global.knight_cfg = knight_cfg_default();
    global.knight_main_valid = false;
    var _main = knight_store_parse(knight_store_file());
    var _st = "ok";
    if (_main.st == "ok")
    {
        knight_store_apply(_main);
        global.knight_main_valid = true;
        if (_main.fixed > 0)
            _st = "Some invalid saved values were reset.";
    }
    else
    {
        var _bak = knight_store_parse(knight_store_bak());
        if (_main.st == "missing" && _bak.st == "missing")
        {
            _st = "new";
        }
        else if (_bak.st == "ok")
        {
            knight_store_apply(_bak);
            _st = "Records were restored from the backup copy.";
            global.knight_main_valid = false;
            knight_store_save();
        }
        else
        {
            if (_main.st == "schema")
            {
                if (file_exists("knight_hub.old"))
                    file_delete("knight_hub.old");
                file_copy(knight_store_file(), "knight_hub.old");
                _st = "Saved data is from an unsupported version; started fresh (old file kept as knight_hub.old).";
            }
            else
            {
                if (file_exists("knight_hub.bad"))
                    file_delete("knight_hub.bad");
                if (file_exists(knight_store_file()))
                    file_copy(knight_store_file(), "knight_hub.bad");
                _st = "Saved records were damaged and could not be recovered; started fresh.";
            }
        }
    }
    global.knight_store_status = _st;
}

// ---------- save (verified; keeps last known-good copy) ----------
function knight_store_write_file(_name)
{
    ossafe_ini_open(_name);
    var _secs = ["meta", "last"];
    for (var _i = 0; _i < array_length(_secs); _i++)
        ini_section_delete(_secs[_i]);
    for (var _i = 0; _i < knight_preset_slots(); _i++)
        ini_section_delete("preset" + string(_i));
    var _keys = knight_rec_keys();
    var _flds = knight_rec_fields();
    var _sumrec = 0;
    for (var _k = 0; _k < array_length(_keys); _k++)
    {
        var _cats = knight_rec_cats(_keys[_k]);
        for (var _c = 0; _c < array_length(_cats); _c++)
        {
            var _sec = "rec_" + _keys[_k] + "_" + _cats[_c];
            var _r = knight_rec_get(_keys[_k], _cats[_c]);
            for (var _f = 0; _f < array_length(_flds); _f++)
            {
                var _v = variable_struct_get(_r, _flds[_f]);
                ini_write_real(_sec, _flds[_f], _v);
                _sumrec = knight_sum_add(_sumrec, _v);
            }
            ini_write_string(_sec, "cfg", _r.cfg);
            _sumrec = knight_sum_add(_sumrec, _r.cfg);
        }
    }
    var _sumpre = 0;
    for (var _i = 0; _i < knight_preset_slots(); _i++)
    {
        var _sec = "preset" + string(_i);
        var _p = global.knight_presets[_i];
        if (is_undefined(_p))
        {
            ini_write_real(_sec, "used", 0);
            _sumpre = knight_sum_add(_sumpre, 0);
            continue;
        }
        ini_write_real(_sec, "used", 1);
        _sumpre = knight_sum_add(_sumpre, 1);
        ini_write_string(_sec, "name", _p.name);
        ini_write_real(_sec, "ver", _p.ver);
        _sumpre = knight_sum_add(_sumpre, _p.name);
        _sumpre = knight_sum_add(_sumpre, _p.ver);
        if (variable_struct_exists(_p, "future") && _p.future)
        {
            // slot written by a newer hub: only its name and version survive a re-save (its settings are not readable here)
            continue;
        }
        ini_write_string(_sec, "knight", _p.knight);
        ini_write_string(_sec, "song", _p.song);
        ini_write_string(_sec, "spells", _p.spells);
        var _eq = variable_struct_exists(_p, "equip") ? _p.equip : "";
        ini_write_string(_sec, "equip", _eq);
        _sumpre = knight_sum_add(_sumpre, _p.knight);
        _sumpre = knight_sum_add(_sumpre, _p.song);
        _sumpre = knight_sum_add(_sumpre, _p.spells);
        _sumpre = knight_sum_add(_sumpre, _eq);
        for (var _m = 0; _m < 3; _m++)
        {
            ini_write_real(_sec, "party" + string(_m), _p.party[_m]);
            _sumpre = knight_sum_add(_sumpre, _p.party[_m]);
        }
        var _cf = knight_cfg_fields();
        for (var _f = 0; _f < array_length(_cf); _f++)
        {
            var _fv = variable_struct_get(_p, _cf[_f]);
            ini_write_real(_sec, _cf[_f], _fv);
            _sumpre = knight_sum_add(_sumpre, _fv);
        }
        var _cfx = knight_cfg_fields_x();
        for (var _f = 0; _f < array_length(_cfx); _f++)
            ini_write_real(_sec, _cfx[_f], variable_struct_exists(_p, _cfx[_f]) ? variable_struct_get(_p, _cfx[_f]) : 0);
    }
    var _cfg = global.knight_cfg;
    var _lp = knight_cfg_to_preset(_cfg, "");
    ini_write_string("last", "knight", _lp.knight);
    ini_write_string("last", "song", _lp.song);
    for (var _m = 0; _m < 3; _m++)
        ini_write_real("last", "party" + string(_m), _lp.party[_m]);
    var _cf2 = knight_cfg_fields();
    for (var _f = 0; _f < array_length(_cf2); _f++)
        ini_write_real("last", _cf2[_f], variable_struct_get(_lp, _cf2[_f]));
    var _cf2x = knight_cfg_fields_x();
    for (var _f = 0; _f < array_length(_cf2x); _f++)
        ini_write_real("last", _cf2x[_f], variable_struct_exists(_lp, _cf2x[_f]) ? variable_struct_get(_lp, _cf2x[_f]) : 0);
    if (!is_undefined(global.knight_orig))
    {
        global.knight_last_spells = knight_spells_to_string();
        global.knight_last_equip = knight_equip_to_string();
    }
    if (string_length(global.knight_last_spells) == 48)
        ini_write_string("last", "spells", global.knight_last_spells);
    if (string_length(global.knight_last_equip) == 12)
        ini_write_string("last", "equip", global.knight_last_equip);
    ini_write_string("last", "flowery", knight_cc_to_string());
    ini_write_real("meta", "schema", knight_store_schema());
    ini_write_real("meta", "sumrec", _sumrec);
    ini_write_real("meta", "sumpre", _sumpre);
    ini_write_real("meta", "done", 1);
    ossafe_ini_close();
}

// returns true when the data was written AND read back correctly
function knight_store_save()
{
    if (!global.knight_loaded)
        return false;
    var _f = knight_store_file();
    var _b = knight_store_bak();
    if (file_exists(_f) && global.knight_main_valid)
    {
        if (file_exists(_b))
            file_delete(_b);
        file_copy(_f, _b);
    }
    knight_store_write_file(_f);
    var _chk = knight_store_parse(_f);
    if (_chk.st == "ok")
    {
        global.knight_main_valid = true;
        global.knight_save_fail = false;
        return true;
    }
    // the write did not verify: put the last good copy back
    global.knight_main_valid = false;
    global.knight_save_fail = true;
    if (file_exists(_b))
    {
        if (file_exists(_f))
            file_delete(_f);
        file_copy(_b, _f);
        var _rb = knight_store_parse(_f);
        global.knight_main_valid = (_rb.st == "ok");
    }
    return false;
}

// ---------- records ----------
// a config flag that may be missing from configs written by older hubs
function knight_cfg_flag(_c, _f)
{
    return variable_struct_exists(_c, _f) && variable_struct_get(_c, _f) == 1;
}

function knight_rec_category(_run)
{
    // category a single-fight result is filed under
    if (_run.practice)
        return "pr";
    if (_run.cfg.c_nohit)
        return "nh";
    if (_run.cfg.c_items || _run.cfg.c_heal || _run.cfg.c_hp1 || _run.cfg.c_solo || _run.cfg.c_dmg2 || _run.cfg.c_halfhp || _run.cfg.c_notp || _run.cfg.c_onelife
        || knight_cfg_flag(_run.cfg, "c_twin") || knight_cfg_flag(_run.cfg, "c_dark") || knight_cfg_flag(_run.cfg, "c_speed") || knight_cfg_flag(_run.cfg, "c_thorns") || knight_cfg_flag(_run.cfg, "c_time"))
        return "ch";
    return "st";
}

function knight_cfg_text(_cfg)
{
    // short, human-readable description of what a record was set with
    var _s = knight_party_text(_cfg.party);
    if (knight_lu_kind_of(_cfg) == "tag")
        _s = knight_reg(_cfg.knight).short + "+" + knight_reg(_cfg.knight2).short + " " + _s;
    if (knight_lu_kind_of(_cfg) == "remix" && knight_remix_mask(_cfg) != knight_remix_default_mask())
        _s = knight_remix_names(_cfg, "+") + " " + _s;
    if (_cfg.weird)
        _s += " Weird";
    if (_cfg.c_nohit)
        _s += " NoHit";
    if (_cfg.c_items)
        _s += " NoItems";
    if (_cfg.c_heal)
        _s += " NoHeal";
    if (_cfg.c_hp1)
        _s += " 1HP";
    if (_cfg.c_solo)
        _s += " Solo";
    if (_cfg.c_dmg2)
        _s += " 2xDmg";
    if (_cfg.c_halfhp)
        _s += " HalfHP";
    if (_cfg.c_notp)
        _s += " NoTP";
    if (_cfg.c_onelife)
        _s += " OneLife";
    if (knight_cfg_flag(_cfg, "c_twin"))
        _s += " Twin";
    if (knight_cfg_flag(_cfg, "c_dark"))
        _s += " Dark";
    if (knight_cfg_flag(_cfg, "c_speed"))
        _s += " Speed";
    if (knight_cfg_flag(_cfg, "c_thorns"))
        _s += " Thorns";
    if (knight_cfg_flag(_cfg, "c_time"))
        _s += " Timed";
    return string_copy(_s, 1, 60);
}

// a clear (win) of one standard fight or one whole rush
// returns what this win improved, for the results box: "" or e.g. "NEW BEST TIME!  LEAST DAMAGE!"
function knight_rec_win(_r, _frames, _dmg, _hits, _cfgtext)
{
    var _new = "";
    var _first = (_r.win == 0);
    _r.win++;
    if (_r.best <= 0 || _frames < _r.best)
    {
        _r.best = max(1, floor(_frames));
        _r.cfg = _cfgtext;
        _new = _first ? "FIRST CLEAR!" : "NEW BEST TIME!";
    }
    if (_r.lowdmg < 0 || _dmg < _r.lowdmg)
    {
        if (!_first && _r.lowdmg >= 0)
            _new += ((_new == "") ? "" : "  ") + "LEAST DAMAGE!";
        _r.lowdmg = floor(_dmg);
    }
    if (_hits == 0)
    {
        _r.cur++;
        if (_r.cur > _r.streak)
            _r.streak = _r.cur;
    }
    else
        _r.cur = 0;
    return _new;
}

function knight_rec_loss(_r)
{
    _r.cur = 0;
}
