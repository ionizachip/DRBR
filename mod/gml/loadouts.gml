
// ===== Built-in loadouts (CONFIG > LOADOUTS) and the one-Shadow-Mantle rule =====
// Ready-made party + equipment + spells for every party layout:
//   BASE        the normal end-of-Chapter-3 gear and spells (the Kaizo Knight mod's own save file); its Shadow Mantle is
//               Susie's, and goes to Kris (else Ralsei) when she is not in the party
//   MAXED       the best gear and each member's own full set of moves for that party (see knight_lo_kit)
//   DUAL MOVES  BASE gear plus every two-person move the party can do (Kris's SOUL moves, Frostfire, Ralsei + Noelle's Dual Heal)
//   x2 / x3     two or three of one member (one shared HP bar, gear and spell list), MAXED
// Item ids: scr_weaponinfo / scr_armorinfo. Spell ids: scr_spellinfo (12-15 are the hub's own).

// party groups: trios, duos, solos, then the x2 group and the x3 group
function knight_lo_groups()
{
    // (build 50: the parties with Flowery, character 5, follow the game's four)
    return [[1, 2, 3], [1, 2, 4], [1, 3, 4], [2, 3, 4],
            [1, 2, 0], [1, 3, 0], [1, 4, 0], [2, 3, 0], [2, 4, 0], [3, 4, 0],
            [1, 0, 0], [2, 0, 0], [3, 0, 0], [4, 0, 0],
            [1, 2, 5], [1, 3, 5], [1, 4, 5], [2, 3, 5], [2, 4, 5], [3, 4, 5],
            [1, 5, 0], [2, 5, 0], [3, 5, 0], [4, 5, 0], [5, 0, 0],
            [0, 0, 0], [0, 0, 0]];
}

function knight_lo_group_count()
{
    return array_length(knight_lo_groups());
}

function knight_lo_is_triple(_g)
{
    return (_g == knight_lo_group_count() - 1);
}

function knight_lo_is_double(_g)
{
    return (_g == knight_lo_group_count() - 2);
}

// x2 or x3: one member several times
function knight_lo_is_clone(_g)
{
    return knight_lo_is_triple(_g) || knight_lo_is_double(_g);
}

function knight_lo_group_party(_g)
{
    var _l = knight_lo_groups();
    var _p = _l[clamp(_g, 0, array_length(_l) - 1)];
    return [_p[0], _p[1], _p[2]];
}

function knight_lo_letter(_c)
{
    switch (_c)
    {
        case 1: return "K";
        case 2: return "S";
        case 3: return "R";
        case 4: return "N";
        case 5: return "F";
    }
    return "";
}

// short name of a group: KSR, KN, KRIS (solo), TRIPLE
function knight_lo_group_label(_g)
{
    if (knight_lo_is_triple(_g))
        return "TRIPLE";
    if (knight_lo_is_double(_g))
        return "DOUBLE";
    var _p = knight_lo_group_party(_g);
    if (_p[1] == 0)
        return string_upper(knight_char_proper(_p[0]));
    return knight_lo_letter(_p[0]) + knight_lo_letter(_p[1]) + knight_lo_letter(_p[2]);
}

function knight_lo_has(_party, _c)
{
    return (_c > 0 && (_party[0] == _c || _party[1] == _c || _party[2] == _c));
}

// the loadouts of a group: { kind, ch } (ch only for x3)
function knight_lo_list(_g)
{
    if (knight_lo_is_triple(_g))
        return [{ kind: "triple", ch: 1 }, { kind: "triple", ch: 2 }, { kind: "triple", ch: 3 }, { kind: "triple", ch: 4 }];
    if (knight_lo_is_double(_g))
        return [{ kind: "double", ch: 1 }, { kind: "double", ch: 2 }, { kind: "double", ch: 3 }, { kind: "double", ch: 4 }];
    var _l = [{ kind: "base", ch: 0 }, { kind: "maxed", ch: 0 }];
    var _p = knight_lo_group_party(_g);
    if (knight_lo_has_dual(_p))
        array_push(_l, { kind: "dual", ch: 0 });
    return _l;
}

function knight_lo_label(_lo)
{
    switch (_lo.kind)
    {
        case "base": return "BASE";
        case "maxed": return "MAXED";
        case "dual": return "DUAL MOVES";
        case "triple": return string_upper(knight_char_proper(_lo.ch)) + " x3";
        case "double": return string_upper(knight_char_proper(_lo.ch)) + " x2";
    }
    return "";
}

function knight_lo_desc(_lo)
{
    switch (_lo.kind)
    {
        case "base": return "The normal Chapter 3 gear and spells,#as in the knight mods' own save file.";
        case "maxed": return "Best gear and each member's own full#set of moves for this party.";
        case "dual": return "Normal gear plus every two-person#move this party can do.";
        case "triple": return "Three " + knight_char_proper(_lo.ch) + " sharing one HP bar, with#the best gear and their own moves.";
        case "double": return "Two " + knight_char_proper(_lo.ch) + " sharing one HP bar, with#the best gear and their own moves.";
    }
    return "";
}

function knight_lo_party(_g, _lo)
{
    if (_lo.kind == "triple")
        return [_lo.ch, _lo.ch, _lo.ch];
    if (_lo.kind == "double")
        return [_lo.ch, _lo.ch, 0];
    return knight_lo_group_party(_g);
}

// ---------- gear ----------
// the Kaizo Knight mod's own end-of-Chapter-3 save: [weapon, armor 1, armor 2]
function knight_lo_base_gear(_c)
{
    switch (_c)
    {
        case 1: return [23, 27, 7];
        case 2: return [24, 21, 23];
        case 3: return [25, 22, 9];
        case 4: return [12, 14, 22];
    }
    // a custom character (Flowery): its own starting gear
    var _d = knight_cc(_c);
    if (!is_undefined(_d) && variable_struct_exists(_d, "gear") && variable_struct_exists(_d.gear, "start"))
        return [_d.gear.start[0], _d.gear.start[1], _d.gear.start[2]];
    return [0, 0, 0];
}

// best gear: BlackShard (Kris), EverybodyWeapon (Susie, Ralsei), ThornRing (Noelle: halves Ice Shock / SnowGrave TP,
// drains her HP down to a third), Dealmaker plus TennaTie (fighters) / RoyalPin (magic users), or plus the Shadow Mantle
function knight_lo_max_gear(_c, _mantle)
{
    if (_c >= 5)
        return knight_lo_base_gear(_c);
    var _w = [0, 26, 4, 4, 13];
    if (_mantle)
        return [_w[_c], 21, 23];
    if (_c == 1 || _c == 2)
        return [_w[_c], 21, 27];
    return [_w[_c], 21, 22];
}

// who wears the Shadow Mantle: every loadout has exactly one when someone can wear it, Susie first, else Kris, else Ralsei
// (Noelle cannot wear it, so solo Noelle and Noelle x3 have none)
function knight_lo_mantle(_party)
{
    var _pref = [2, 1, 3];
    for (var _i = 0; _i < 3; _i++)
    {
        if (knight_lo_has(_party, _pref[_i]))
            return _pref[_i];
    }
    return 0;
}

function knight_lo_gear(_kind, _c, _party)
{
    var _wear = (_c == knight_lo_mantle(_party));
    if (_kind == "base" || _kind == "dual")
    {
        // the save's mantle is Susie's; without her it goes to the next member in line (in place of their second armor)
        var _g = knight_lo_base_gear(_c);
        if (_wear)
            _g[2] = 23;
        return _g;
    }
    return knight_lo_max_gear(_c, _wear);
}

// ---------- spells ----------
function knight_lo_natural(_c)
{
    switch (_c)
    {
        case 1: return [7];
        case 2: return [4, 11];
        case 3: return [3, 2];
        case 4: return [2, 8, 9];
    }
    // a custom character (Flowery): all its techniques
    var _d = knight_cc(_c);
    if (!is_undefined(_d) && variable_struct_exists(_d, "spells"))
    {
        var _o = [];
        for (var _i = 0; _i < array_length(_d.spells); _i++)
            array_push(_o, _d.spells[_i]);
        return _o;
    }
    return [];
}

// two-person moves: [spell, partner it needs]
function knight_lo_duals(_c)
{
    switch (_c)
    {
        case 1: return [[5, 2], [6, 3], [14, 3], [12, 4]];
        case 3: return [[15, 4], [6, 4]];
        case 4: return [[15, 3], [6, 3]];
    }
    return [];
}

function knight_lo_has_dual(_party)
{
    for (var _i = 0; _i < 3; _i++)
    {
        var _d = knight_lo_duals(_party[_i]);
        for (var _j = 0; _j < array_length(_d); _j++)
        {
            if (knight_lo_has(_party, _d[_j][1]))
                return true;
        }
    }
    return false;
}

// each member's own full set of moves (MAXED / x3): their game spells, the hub moves that belong to them, and their
// two-person moves: [spell, partner it needs (0 = none)]
//   Kris   ACT, X-Slash, then the SOUL moves: Red Buster (Susie), Dual Heal and Heatwave (Ralsei), Permafrost (Noelle)
//   Susie  Rude Buster, UltraHeal
//   Ralsei Heal Prayer, Pacify, FireShock, then Frostfire and Dual Heal (with Noelle)
//   Noelle Heal Prayer, SleepMist, IceShock, SnowGrave, then Frostfire and Dual Heal (with Ralsei)
function knight_lo_kit(_c)
{
    switch (_c)
    {
        case 1: return [[7, 0], [1, 0], [5, 2], [6, 3], [14, 3], [12, 4]];
        case 2: return [[4, 0], [11, 0]];
        case 3: return [[2, 0], [3, 0], [13, 0], [15, 4], [6, 4]];
        case 4: return [[2, 0], [8, 0], [9, 0], [10, 0], [15, 3], [6, 3]];
    }
    var _n = knight_lo_natural(_c);
    var _o = [];
    for (var _i = 0; _i < array_length(_n); _i++)
        array_push(_o, [_n[_i], 0]);
    return _o;
}

function knight_lo_spells(_kind, _c, _party)
{
    var _o = [];
    if (_kind == "base" || _kind == "dual")
    {
        var _n = knight_lo_natural(_c);
        for (var _i = 0; _i < array_length(_n); _i++)
            array_push(_o, _n[_i]);
        if (_kind == "dual")
        {
            var _d = knight_lo_duals(_c);
            for (var _j = 0; _j < array_length(_d); _j++)
            {
                if (knight_lo_has(_party, _d[_j][1]))
                    array_push(_o, _d[_j][0]);
            }
        }
        return _o;
    }
    var _a = knight_lo_kit(_c);
    for (var _k = 0; _k < array_length(_a); _k++)
    {
        if (array_length(_o) >= 12)
            break;
        if (_a[_k][1] == 0 || knight_lo_has(_party, _a[_k][1]))
            array_push(_o, _a[_k][0]);
    }
    return _o;
}

// ---------- apply ----------
function knight_lo_apply(_g, _lo)
{
    var _party = knight_lo_party(_g, _lo);
    global.knight_cfg.party = [_party[0], _party[1], _party[2]];
    // one Shadow Mantle per setup: take it off everyone first, the loadout puts it on its wearer
    knight_mantle_clear(0);
    for (var _i = 0; _i < 3; _i++)
    {
        var _c = knight_ch_real(_party[_i]);
        if (knight_cc_ok(_c))
        {
            // a custom character (Flowery): its gear and its techniques (its own list; its ACTION comes first in a fight)
            var _cg = knight_lo_gear(_lo.kind, _c, _party);
            global.charweapon[_c] = _cg[0];
            global.chararmor1[_c] = _cg[1];
            global.chararmor2[_c] = _cg[2];
            var _cs = knight_lo_spells(_lo.kind, _c, _party);
            var _cn = array_length(knight_cc_spl(_c));
            for (var _s = 0; _s < _cn; _s++)
                global.knight_cc_spells[_c][_s] = (_s < array_length(_cs)) ? _cs[_s] : 0;
            continue;
        }
        if (_c < 1 || _c > 4)
            continue;
        var _gear = knight_lo_gear(_lo.kind, _c, _party);
        global.charweapon[_c] = _gear[0];
        global.chararmor1[_c] = _gear[1];
        global.chararmor2[_c] = _gear[2];
        var _sp = knight_lo_spells(_lo.kind, _c, _party);
        for (var _s = 0; _s < 12; _s++)
            global.spell[_c][_s] = (_s < array_length(_sp)) ? _sp[_s] : 0;
    }
    knight_mantle_fix();
    knight_equip_refresh();
}

// ---------- the Shadow Mantle (armor 23): only one in the whole setup ----------
// The knight fights treat it as one item (Kaizo picks a single wearer to draw the knight's hits; a second wearer would
// halve the damage again for another member).
function knight_mantle_clear(_keep_c)
{
    for (var _c = 1; _c <= 4; _c++)
    {
        if (_c == _keep_c)
            continue;
        if (global.chararmor1[_c] == 23)
            global.chararmor1[_c] = 0;
        if (global.chararmor2[_c] == 23)
            global.chararmor2[_c] = 0;
    }
}

// someone just put it on (slot _k of character _c): it comes off everyone else; returns who lost it ("" = nobody)
function knight_mantle_take(_c, _k)
{
    var _from = "";
    for (var _o = 1; _o <= 4; _o++)
    {
        for (var _s = 1; _s <= 2; _s++)
        {
            if (_o == _c && _s == _k)
                continue;
            if (knight_equip_get(_o, _s) == 23)
            {
                knight_equip_set(_o, _s, 0);
                if (_o != _c)
                    _from = knight_char_proper(_o);
            }
        }
    }
    knight_equip_refresh();
    return _from;
}

// more than one Shadow Mantle (an old preset, two slots of one member): keep the first in party order; returns the count removed
function knight_mantle_fix()
{
    var _order = [];
    var _p = global.knight_cfg.party;
    for (var _i = 0; _i < 3; _i++)
    {
        if (_p[_i] >= 1 && _p[_i] <= 4)
            array_push(_order, _p[_i]);
    }
    for (var _c = 1; _c <= 4; _c++)
        array_push(_order, _c);
    var _kept = false;
    var _removed = 0;
    var _done = [0, 0, 0, 0, 0, 0];
    for (var _j = 0; _j < array_length(_order); _j++)
    {
        var _ch = _order[_j];
        if (_done[_ch])
            continue;
        _done[_ch] = 1;
        for (var _s = 1; _s <= 2; _s++)
        {
            if (knight_equip_get(_ch, _s) == 23)
            {
                if (_kept)
                {
                    knight_equip_set(_ch, _s, 0);
                    _removed++;
                }
                else
                    _kept = true;
            }
        }
    }
    if (_removed > 0)
        knight_equip_refresh();
    return _removed;
}

// ---------- the LOADOUTS page ----------
function knight_ui_lo_cur()
{
    var _u = global.knight_ui;
    var _l = knight_lo_list(_u.lo_g);
    return _l[clamp(_u.lo_i, 0, array_length(_l) - 1)];
}

// opening the page shows the group of the current party (any order), MAXED highlighted
function knight_ui_lo_focus_party()
{
    var _u = global.knight_ui;
    var _p = global.knight_cfg.party;
    var _cnt = [0, 0, 0, 0, 0, 0];
    for (var _i = 0; _i < 3; _i++)
        _cnt[clamp(_p[_i], 0, 5)]++;
    for (var _c = 1; _c <= 4; _c++)
    {
        if (_cnt[_c] == 3)
        {
            _u.lo_g = knight_lo_group_count() - 1;
            _u.lo_i = _c - 1;
            return 0;
        }
        if (_cnt[_c] == 2 && _cnt[0] == 1)
        {
            _u.lo_g = knight_lo_group_count() - 2;
            _u.lo_i = _c - 1;
            return 0;
        }
    }
    for (var _g = 0; _g < knight_lo_group_count() - 2; _g++)
    {
        var _q = knight_lo_group_party(_g);
        var _k = [0, 0, 0, 0, 0, 0];
        for (var _j = 0; _j < 3; _j++)
            _k[_q[_j]]++;
        if (_k[1] == _cnt[1] && _k[2] == _cnt[2] && _k[3] == _cnt[3] && _k[4] == _cnt[4] && _k[5] == _cnt[5])
        {
            _u.lo_g = _g;
            _u.lo_i = 1;
            return 0;
        }
    }
    _u.lo_i = clamp(_u.lo_i, 0, array_length(knight_lo_list(_u.lo_g)) - 1);
}

function knight_ui_step_loadouts(_up, _down, _left, _right, _ok)
{
    var _u = global.knight_ui;
    if (_left || _right)
    {
        _u.lo_g = knight_ui_cycle(_u.lo_g, _left ? -1 : 1, knight_lo_group_count());
        _u.lo_i = clamp(_u.lo_i, 0, array_length(knight_lo_list(_u.lo_g)) - 1);
        snd_play(snd_menumove);
    }
    var _n = array_length(knight_lo_list(_u.lo_g));
    if (_up)
    {
        _u.lo_i = knight_ui_cycle(_u.lo_i, -1, _n);
        snd_play(snd_menumove);
    }
    if (_down)
    {
        _u.lo_i = knight_ui_cycle(_u.lo_i, 1, _n);
        snd_play(snd_menumove);
    }
    if (_ok)
    {
        snd_play(snd_select);
        var _lo = knight_ui_lo_cur();
        var _m = knight_ui_modal("confirm", "LOAD THIS LOADOUT?", [knight_lo_group_label(_u.lo_g) + "  " + knight_lo_label(_lo), "It replaces the party and their equipment and spells. The knight and the rules stay."], [{ t: "Load", a: "lo_load" }, { t: "Cancel", a: "close" }]);
        _m.data = { g: _u.lo_g, lo: _lo };
    }
}

// names for the details panel
function knight_lo_spell_names(_sp)
{
    var _s = "";
    for (var _i = 0; _i < array_length(_sp); _i++)
    {
        scr_spellinfo(_sp[_i]);
        _s += ((_s == "") ? "" : ", ") + knight_spell_label(spellname);
    }
    return _s;
}

function knight_lo_gear_names(_gear, _c)
{
    var _s = "";
    for (var _k = 0; _k < 3; _k++)
    {
        if (_gear[_k] <= 0)
            continue;
        _s += ((_s == "") ? "" : ", ") + knight_equip_info(_k, _gear[_k], _c).name;
    }
    return (_s == "") ? "no gear" : _s;
}
