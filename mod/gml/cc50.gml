// ===== Build 50: CUSTOM CHARACTERS - party members of the hub's own, beyond the game's four =====
// A custom character is a real party member with its own character id (5, 6, ...): its own HP / AT / DF / MAG, its own hero
// in battle (obj_knight_herocc, a child of obj_heroparent like the game's own heroes), its own HP-bar box (head, name, colour),
// its own MAGIC (techniques + its own ACTION as the first entry, where Noelle has N-Action), its own gear, its own lines.
// The game's battle code reaches them through ONE registry - adding a character means adding one definition here:
//
//   knight_cc_register({
//       cid: 6, key: "name", name: "Name", short: "N", pron: "him",
//       color: <HP-bar colour>, bar: <FIGHT-bar box colour>, dmtype: <damage-number type 0-6>,
//       head: <spr>, head_dy: <battle box y shift>, menu_dx / menu_dy: <menu head shift>, bname / bname_ja: <spr>,
//       eqchar / eq_dx / eq_dy: <hub EQUIP picture>, walk: [down, right, up, left],
//       poses: { normal, idle, act, actready, attack, attackready, defend, hurt, defeat, item, itemready, spell, spellready, victory },
//       spells: [technique ids 16-39], action: <its ACTION's technique id>,
//       gear: { weapon: [ids 30-35], armor: [ids 30-35], start: [weapon, armor1, armor2] },
//       stats: <script: fills global.maxhp/at/df/mag[id]>, onbegin: <script: a fight starts>,
//       spellinfo / spell / spelltext / kspell / weaponinfo / armorinfo / tick / taken: <scripts>
//   });
//
// Reserved ranges for them: technique ids 16-39 (scr_spellinfo / scr_spell / scr_spelltext send these to knight_cc_*), gear ids
// 30-35 (scr_weaponinfo / scr_armorinfo), knight_kspell kinds 20 and up (the registry's kspell script runs the move).

global.knight_ccs = [];

function knight_cc_register(_d)
{
    global.knight_ccs[_d.cid] = _d;
    return _d.cid;
}

function knight_cc(_c)
{
    if (!is_real(_c) || _c < 5 || _c >= array_length(global.knight_ccs))
        return undefined;
    var _d = global.knight_ccs[_c];
    return is_struct(_d) ? _d : undefined;
}

function knight_cc_ok(_c)
{
    return !is_undefined(knight_cc(_c));
}

function knight_cc_count()
{
    var _n = 0;
    for (var _i = 5; _i < array_length(global.knight_ccs); _i++)
    {
        if (is_struct(global.knight_ccs[_i]))
            _n++;
    }
    return _n;
}

// the last character id there is (4 without custom ones): the hub's party picker cycles 0 .. this
function knight_cc_max_id()
{
    var _m = 4;
    for (var _i = 5; _i < array_length(global.knight_ccs); _i++)
    {
        if (is_struct(global.knight_ccs[_i]))
            _m = _i;
    }
    return _m;
}

function knight_cc_spr(_s)
{
    return is_numeric(_s) && _s >= 0 && sprite_exists(_s);
}

// who owns technique _id (16-39), 0 if nobody
function knight_cc_spell_owner(_id)
{
    for (var _i = 5; _i < array_length(global.knight_ccs); _i++)
    {
        var _d = global.knight_ccs[_i];
        if (!is_struct(_d))
            continue;
        if (_id == _d.action)
            return _i;
        if (variable_struct_exists(_d, "extra"))
        {
            for (var _j = 0; _j < array_length(_d.extra); _j++)
            {
                if (_d.extra[_j] == _id)
                    return _i;
            }
        }
        for (var _j = 0; _j < array_length(_d.spells); _j++)
        {
            if (_d.spells[_j] == _id)
                return _i;
        }
        // its optional techniques (not in its starting set; given on the POWER page)
        if (variable_struct_exists(_d, "opt"))
        {
            for (var _j = 0; _j < array_length(_d.opt); _j++)
            {
                if (_d.opt[_j] == _id)
                    return _i;
            }
        }
    }
    return 0;
}

// who owns gear _id of kind _k (0 weapon, 1/2 armor), 0 if nobody
function knight_cc_gear_owner(_k, _id)
{
    for (var _i = 5; _i < array_length(global.knight_ccs); _i++)
    {
        var _d = global.knight_ccs[_i];
        if (!is_struct(_d))
            continue;
        var _l = (_k == 0) ? _d.gear.weapon : _d.gear.armor;
        for (var _j = 0; _j < array_length(_l); _j++)
        {
            if (_l[_j] == _id)
                return _i;
        }
    }
    return 0;
}

// can character _c wear gear _id (kind _k)? (a custom character: only gear of its own; any armor every member can wear too)
function knight_cc_gear_ok(_c, _k, _id)
{
    if (_id == 0)
        return true;
    return knight_cc_gear_owner(_k, _id) == _c;
}

// a custom character's gear: whatever it wears that is not for it goes back to its own start gear
function knight_cc_gear_default(_force)
{
    for (var _i = 5; _i < array_length(global.knight_ccs); _i++)
    {
        var _d = global.knight_ccs[_i];
        if (!is_struct(_d))
            continue;
        for (var _k = 0; _k < 3; _k++)
        {
            var _v = knight_equip_get(_i, _k);
            if (_force || !knight_equip_info(_k, _v, _i).ok)
                knight_equip_set(_i, _k, _d.gear.start[_k]);
        }
    }
    return 1;
}

// their stats for the fight to come (and once when the hub opens: their HP full)
function knight_cc_stats()
{
    for (var _i = 5; _i < array_length(global.knight_ccs); _i++)
    {
        var _d = global.knight_ccs[_i];
        if (!is_struct(_d))
            continue;
        // the first time (this game session): its own start gear on, its HP full
        if (!variable_global_exists("knight_cc_inited") || !is_array(global.knight_cc_inited))
            global.knight_cc_inited = [];
        if (_i >= array_length(global.knight_cc_inited) || global.knight_cc_inited[_i] != true)
        {
            global.knight_cc_inited[_i] = true;
            for (var _k = 0; _k < 3; _k++)
                knight_equip_set(_i, _k, _d.gear.start[_k]);
            knight_equip_refresh();
            script_execute(_d.stats);
            global.hp[_i] = global.maxhp[_i];
        }
        else
            script_execute(_d.stats);
        if (global.hp[_i] > global.maxhp[_i])
            global.hp[_i] = global.maxhp[_i];
        global.charname[_i] = _d.name;
        global.charauto[_i] = 0;
    }
    return 1;
}

// ---------- the battle code's hooks ----------
// scr_spellinfo / scr_spell / scr_spelltext, ids 16-39 (self: the calling instance, as for the game's own spells)
function knight_cc_spellinfo(_id)
{
    var _d = knight_cc(knight_cc_spell_owner(_id));
    if (is_undefined(_d))
    {
        spellname = " ";
        spellnameb = " ";
        spelldescb = " ";
        spelldesc = " ";
        spelltarget = 0;
        cost = 0;
        spellusable = 0;
        return 0;
    }
    return script_execute(_d.spellinfo, _id);
}

function knight_cc_spell(_id, _caster, _star)
{
    var _d = knight_cc(knight_cc_spell_owner(_id));
    if (is_undefined(_d))
        return 0;
    return script_execute(_d.spell, _id, _caster, _star);
}

function knight_cc_spelltext(_id)
{
    var _d = knight_cc(knight_cc_spell_owner(_id));
    if (is_undefined(_d))
        return "* .../%";
    return script_execute(_d.spelltext, _id);
}

// scr_weaponinfo / scr_armorinfo, ids 30-35 (self: the caller; the game's temp variables)
function knight_cc_weaponinfo(_id)
{
    var _d = knight_cc(knight_cc_gear_owner(0, _id));
    weaponnametemp = " ";
    weapondesctemp = " ";
    wmessage2temp = " ";
    wmessage3temp = " ";
    wmessage4temp = " ";
    weaponattemp = 0;
    weapondftemp = 0;
    weaponmagtemp = 0;
    weaponboltstemp = 0;
    weaponstyletemp = " ";
    weapongrazeamttemp = 0;
    weapongrazesizetemp = 0;
    weaponchar1temp = 0;
    weaponchar2temp = 0;
    weaponchar3temp = 0;
    weaponchar4temp = 0;
    weaponabilitytemp = " ";
    weaponabilityicontemp = 0;
    weaponicontemp = 0;
    value = 0;
    if (!is_undefined(_d))
        script_execute(_d.weaponinfo, _id);
    return 1;
}

function knight_cc_armorinfo(_id)
{
    var _d = knight_cc(knight_cc_gear_owner(1, _id));
    armornametemp = " ";
    armordesctemp = " ";
    amessage2temp = " ";
    amessage3temp = " ";
    amessage4temp = " ";
    armorattemp = 0;
    armordftemp = 0;
    armormagtemp = 0;
    armorboltstemp = 0;
    armorgrazeamttemp = 0;
    armorgrazesizetemp = 0;
    armorchar1temp = 0;
    armorchar2temp = 0;
    armorchar3temp = 0;
    armorchar4temp = 0;
    armorabilitytemp = " ";
    armorabilityicontemp = 0;
    armoricontemp = 0;
    armorelementtemp = 0;
    armorelementamounttemp = 0;
    value = 0;
    if (!is_undefined(_d))
        script_execute(_d.armorinfo, _id);
    return 1;
}

// obj_battlecontroller's Create: the hero of a custom character in party slot _i (self: the battle controller)
function knight_cc_hero_make(_i)
{
    var _c = global.char[_i];
    if (!knight_cc_ok(_c))
        return noone;
    havechar[_c - 1] = 1;
    charpos[_c - 1] = _i;
    global.charinstance[_i] = instance_create(global.heromakex[_i], global.heromakey[_i], obj_knight_herocc);
    global.charinstance[_i].myself = _i;
    global.charinstance[_i].char = _c;
    global.charinstance[_i].depth = 200 - (_i * 20);
    with (global.charinstance[_i])
        knight_cc_dress();
    return global.charinstance[_i];
}

// obj_knight_herocc's Create (after obj_heroparent's): its character comes with the next knight_cc_dress
function knight_cc_hero_init()
{
    ccdressed = -1;
    return 1;
}

// its poses (self: the hero); again when the character changes
function knight_cc_dress()
{
    var _d = knight_cc(char);
    if (is_undefined(_d) || ccdressed == char)
        return 0;
    ccdressed = char;
    var _p = _d.poses;
    if (knight_cc_spr(_p.normal)) normalsprite = _p.normal;
    if (knight_cc_spr(_p.idle)) idlesprite = _p.idle;
    if (knight_cc_spr(_p.actready)) actreadysprite = _p.actready;
    if (knight_cc_spr(_p.act)) actsprite = _p.act;
    if (knight_cc_spr(_p.hurt)) hurtsprite = _p.hurt;
    if (knight_cc_spr(_p.defend)) defendsprite = _p.defend;
    if (knight_cc_spr(_p.attackready)) attackreadysprite = _p.attackready;
    if (knight_cc_spr(_p.attack)) attacksprite = _p.attack;
    if (knight_cc_spr(_p.itemready)) itemreadysprite = _p.itemready;
    if (knight_cc_spr(_p.item)) itemsprite = _p.item;
    if (knight_cc_spr(_p.spellready)) spellreadysprite = _p.spellready;
    if (knight_cc_spr(_p.spell)) spellsprite = _p.spell;
    // (scr_spellconsumeb puts spellsprite back from remspellsprite on every cast: obj_heroparent's Create filled it in with
    // Ralsei's Chapter 1 spell pose - this is what turned him into Ralsei when he cast)
    remspellsprite = spellsprite;
    if (knight_cc_spr(_p.defeat)) defeatsprite = _p.defeat;
    if (knight_cc_spr(_p.victory)) victorysprite = _p.victory;
    if (knight_cc_spr(_p.idle))
        sprite_index = _p.idle;
    myheight = _d.height;
    mywidth = _d.width;
    // obj_heroparent plays a pose's frames up to these (its Create set the defaults for a Kris-sized set)
    if (variable_struct_exists(_d, "frames"))
    {
        attackframes = _d.frames.attack;
        attackspeed = _d.frames.attackspeed;
        itemframes = _d.frames.item;
        spellframes = _d.frames.spell;
        remspellframes = _d.frames.spell;
    }
    return 1;
}

// obj_heroparent's FIGHT hit on the foe (self: the hero): a custom character's own hit effect
function knight_cc_attack_fx(_att, _c)
{
    var _d = knight_cc(_c);
    if (is_undefined(_d) || !i_ex(_att) || !variable_struct_exists(_d, "hitfx") || !knight_cc_spr(_d.hitfx))
        return 0;
    _att.sprite_index = _d.hitfx;
    _att.image_index = 0;
    _att.maxindex = sprite_get_number(_d.hitfx) - 1;
    _att.image_speed = 0.5;
    _att.image_blend = _d.color;
    return 1;
}

// obj_heroparent's FIGHT swing sound (the game's own, at the character's pitch)
function knight_cc_attack_snd(_c)
{
    var _d = knight_cc(_c);
    if (is_undefined(_d))
        return 0;
    var _ls = snd_play(snd_laz_c);
    snd_pitch(_ls, variable_struct_exists(_d, "sound_pitch") ? _d.sound_pitch : 1);
    return 1;
}

// the FIGHT bar panel (obj_attackpress): a custom character's head picture and its coloured bar end
function knight_cc_pressfront(_j, _x, _y)
{
    var _d = knight_cc(_j);
    if (!is_undefined(_d) && variable_struct_exists(_d, "pressfront") && knight_cc_spr(_d.pressfront))
        draw_sprite(_d.pressfront, 0, _x, _y);
    else
        draw_sprite(spr_pressfront, clamp(_j - 1, 0, 3), _x, _y);
    return 1;
}

function knight_cc_pressspot(_j, _x, _y)
{
    if (knight_cc_ok(_j))
        draw_sprite_ext(spr_pressspot, 3, _x, _y, 1, 1, 0, merge_color(knight_cc(_j).color, c_white, 0.2), 1);
    else
        draw_sprite(spr_pressspot, clamp(_j - 1, 0, 3), _x, _y);
    return 1;
}

// the battle and dark menu's hpcolor[] (self: the controller): every custom character's colour at hpcolor[id - 1]
function knight_cc_hpcolors()
{
    for (var _i = 5; _i < array_length(global.knight_ccs); _i++)
    {
        var _d = global.knight_ccs[_i];
        hpcolor[_i - 1] = is_struct(_d) ? _d.color : c_white;
    }
    return 1;
}

// a custom character's head on the Kaizo Knight's Roaring HP strip (its own icons only go up to Noelle)
function knight_cc_roar_head(_c, _x, _y)
{
    var _d = knight_cc(_c);
    if (is_undefined(_d) || !knight_cc_spr(_d.head))
        return 0;
    draw_sprite_ext(_d.head, 0, _x, _y, 1, 1, 0, c_white, 1);
    return 1;
}

function knight_cc_hpcolor(_c)
{
    var _d = knight_cc(_c);
    return is_undefined(_d) ? c_white : _d.color;
}

// the HP-bar box: head (with its own shift) and name
function knight_cc_charbox(_c, _face, _hx, _hy, _nx, _ny)
{
    var _d = knight_cc(_c);
    if (is_undefined(_d))
        return 0;
    // (Flowery in his last-stand Omega form: his head and name in Omega Flowery's colours - the cycling outline hue)
    var _om = (_c == 5 && knight_fl_om_on());
    var _bl = _om ? merge_color(knight_om_hue(), c_white, 0.45) : c_white;
    if (knight_cc_spr(_d.head))
    {
        if (_om)
            knight_om_outline(_d.head, _face, _hx, _hy + _d.head_dy, 1, 1, knight_om_hue(), 1);
        draw_sprite_ext(_d.head, _face, _hx, _hy + _d.head_dy, 1, 1, 0, _bl, 1);
    }
    var _b = (global.lang == "ja" && knight_cc_spr(_d.bname_ja)) ? _d.bname_ja : _d.bname;
    if (knight_cc_spr(_b))
        draw_sprite_ext(_b, 0, _nx, _ny, 1, 1, 0, _bl, 1);
    return 1;
}

// the damage numbers' colour type (char - 1 for the game's own; Noelle's code sets 6 itself afterwards)
function knight_cc_dmtype(_c)
{
    var _d = knight_cc(_c);
    if (!is_undefined(_d))
        return _d.dmtype;
    return _c - 1;
}

function knight_cc_barcolor(_c)
{
    var _d = knight_cc(_c);
    return is_undefined(_d) ? c_white : _d.bar;
}

// scr_spellmenu_setup: the character's own ACTION (its first MAGIC entry) is drawn in the ACT colour
function knight_cc_menu_special(_i, _fj)
{
    var _d = knight_cc(global.char[_i]);
    if (is_undefined(_d))
        return 0;
    var _sp = global.spell[global.char[_i]][_fj];
    // (build 50: Flowery's ACT entry, and every row of his ACT list, in the ACT colour)
    global.battlespellspecial[_i][_fj] = ((_sp != 0 && _sp == _d.action) || (global.char[_i] == 5 && _sp != 0 && knight_fl_act_on())) ? 1 : 0;
    return 1;
}

// is character _c in the party (any slot)
function knight_cc_here(_c)
{
    if (!variable_global_exists("char") || !is_array(global.char))
        return false;
    for (var _i = 0; _i < min(3, array_length(global.char)); _i++)
    {
        if (global.char[_i] == _c)
            return true;
    }
    return false;
}

// every frame of a fight (the registry's tick script of every custom character in the party)
function knight_cc_tick()
{
    // (paused: nothing of theirs moves on)
    if (global.knight_frozen)
        return 0;
    for (var _i = 5; _i < array_length(global.knight_ccs); _i++)
    {
        var _d = global.knight_ccs[_i];
        if (is_struct(_d) && knight_cc_here(_i))
            script_execute(_d.tick);
    }
    if (instance_exists(obj_knight_herocc))
    {
        with (obj_knight_herocc)
            knight_cc_dress();
    }
    return 1;
}

// the damage a hit does to party slot _slot (knight_scale_taken): the custom characters' guards (Afinihug, ...)
function knight_cc_taken(_d0, _slot)
{
    var _out = _d0;
    for (var _i = 5; _i < array_length(global.knight_ccs); _i++)
    {
        var _d = global.knight_ccs[_i];
        if (is_struct(_d))
            _out = script_execute(_d.taken, _out, _slot);
    }
    return _out;
}

// knight_kspell kinds 20 and up: the move of the character that started it (global.knight_ks.cc)
function knight_cc_kspell_tick(_k)
{
    var _d = knight_cc(variable_struct_exists(_k, "cc") ? _k.cc : 0);
    if (is_undefined(_d))
    {
        global.knight_ks = undefined;
        return 0;
    }
    return script_execute(_d.kspell, _k);
}

// ---------- their techniques as the hub's POWER page edits them ----------
// every technique its POWER page offers: its own set, then its optional ones (registry "opt": never in the starting list)
function knight_cc_pickable(_c)
{
    var _d = knight_cc(_c);
    var _o = [];
    if (is_undefined(_d))
        return _o;
    for (var _i = 0; _i < array_length(_d.spells); _i++)
        array_push(_o, _d.spells[_i]);
    if (variable_struct_exists(_d, "opt"))
    {
        for (var _i = 0; _i < array_length(_d.opt); _i++)
            array_push(_o, _d.opt[_i]);
    }
    return _o;
}

// the chosen list (12 rows, technique ids or 0); in a fight their MAGIC is [their ACTION] + this list
function knight_cc_spl(_c)
{
    if (!variable_global_exists("knight_cc_spells") || !is_array(global.knight_cc_spells))
        global.knight_cc_spells = [];
    if (_c >= array_length(global.knight_cc_spells) || !is_array(global.knight_cc_spells[_c]))
    {
        var _d = knight_cc(_c);
        var _l = array_create(12, 0);
        if (!is_undefined(_d))
        {
            for (var _i = 0; _i < min(12, array_length(_d.spells)); _i++)
                _l[_i] = _d.spells[_i];
        }
        global.knight_cc_spells[_c] = _l;
    }
    return global.knight_cc_spells[_c];
}

// each fight: the game's spell list of every custom character = its ACTION, then its chosen techniques (empty rows closed up)
function knight_cc_spells_apply()
{
    for (var _i = 5; _i < array_length(global.knight_ccs); _i++)
    {
        var _d = global.knight_ccs[_i];
        if (!is_struct(_d))
            continue;
        var _l = knight_cc_spl(_i);
        var _n = 0;
        global.spell[_i][_n++] = _d.action;
        for (var _j = 0; _j < 12 && _n < 12; _j++)
        {
            if (_l[_j] != 0)
                global.spell[_i][_n++] = _l[_j];
        }
        while (_n < 12)
            global.spell[_i][_n++] = 0;
    }
    return 1;
}

// saved with the hub's other last-used settings: per character "<id>:<12 technique digits><3 gear digits>;" (base 36)
function knight_cc_to_string()
{
    var _h = "0123456789abcdefghijklmnopqrstuvwxyz";
    var _s = "";
    for (var _i = 5; _i < array_length(global.knight_ccs); _i++)
    {
        if (!is_struct(global.knight_ccs[_i]))
            continue;
        var _l = knight_cc_spl(_i);
        _s += string(_i) + ":";
        for (var _j = 0; _j < 12; _j++)
            _s += string_char_at(_h, clamp(_l[_j], 0, 35) + 1);
        for (var _k = 0; _k < 3; _k++)
            _s += string_char_at(_h, clamp(knight_equip_get(_i, _k), 0, 35) + 1);
        _s += ";";
    }
    return _s;
}

function knight_cc_from_string(_s)
{
    var _h = "0123456789abcdefghijklmnopqrstuvwxyz";
    if (!is_string(_s))
        return 0;
    var _parts = string_split(_s, ";");
    var _n = 0;
    for (var _p = 0; _p < array_length(_parts); _p++)
    {
        var _e = _parts[_p];
        var _c = string_pos(":", _e);
        if (_c < 2)
            continue;
        var _id = real(string_digits(string_copy(_e, 1, _c - 1)));
        var _d = knight_cc(_id);
        var _body = string_copy(_e, _c + 1, string_length(_e) - _c);
        if (is_undefined(_d) || string_length(_body) != 15)
            continue;
        var _l = knight_cc_spl(_id);
        for (var _j = 0; _j < 12; _j++)
        {
            var _v = max(0, string_pos(string_char_at(_body, _j + 1), _h) - 1);
            global.knight_cc_spells[_id][_j] = (knight_cc_spell_owner(_v) == _id && _v != _d.action) ? _v : 0;
        }
        for (var _k = 0; _k < 3; _k++)
        {
            var _g = max(0, string_pos(string_char_at(_body, 13 + _k), _h) - 1);
            if (knight_equip_info(_k, _g, _id).ok)
                knight_equip_set(_id, _k, _g);
        }
        _n++;
    }
    knight_cc_gear_default(false);
    knight_equip_refresh();
    return _n;
}

// a fight starts: every custom character's own start script (turn-long effects cleared)
function knight_cc_battle_begin()
{
    global.knight_cc_line = undefined;
    global.knight_cc_narr = "";
    for (var _i = 5; _i < array_length(global.knight_ccs); _i++)
    {
        var _d = global.knight_ccs[_i];
        if (is_struct(_d))
            script_execute(_d.onbegin);
    }
    return 1;
}

// ---------- in the hub's menus and the overworld ----------
// the EQUIP-menu picture of a member (a custom character's own, with its shift)
function knight_cc_eqchar(_v, _x, _y, _alpha)
{
    var _d = knight_cc(_v);
    if (!is_undefined(_d) && knight_cc_spr(_d.eqchar))
        draw_sprite_ext(_d.eqchar, 0, _x + _d.eq_dx, _y + _d.eq_dy, 2, 2, 0, c_white, _alpha);
    else
        draw_sprite_ext(spr_equipchar_ch2, _v, _x, _y, 2, 2, 0, c_white, _alpha);
    return 1;
}

// walking frames: facing 0 down, 1 right, 2 up, 3 left
function knight_cc_walk_spr(_c, _f)
{
    var _d = knight_cc(_c);
    if (is_undefined(_d))
        return -1;
    return _d.walk[clamp(_f, 0, 3)];
}

// offline, outside a fight in the Dark World: the custom character leading the hub's party (0 if the leader is not one) -
// you walk around as them
function knight_cc_lead_ow()
{
    if (variable_global_exists("darkzone") && global.darkzone != 1)
        return 0;
    // in a hub fight's cold place (before / after the battle): the fight's party leader
    if (knight_active() && variable_global_exists("char") && is_array(global.char))
        return knight_cc_ok(global.char[0]) ? global.char[0] : 0;
    if (!variable_global_exists("knight_cfg") || !is_struct(global.knight_cfg))
        return 0;
    var _c = global.knight_cfg.party[0];
    return knight_cc_ok(_c) ? _c : 0;
}

// ---------- the overworld around a hub fight ----------
// obj_darkcontroller's Create, party slot _i (self: the dark controller): a custom character in the party follows as itself
// (the game makes nobody for a number it does not know)
function knight_cc_follower(_i)
{
    var _c = global.char[_i];
    if (!knight_cc_ok(_c) || !knight_active())
        return 0;
    havechar[_c - 1] = 1;
    charpos[_c - 1] = _i;
    if (_i > 0 && instance_exists(obj_mainchara))
    {
        global.cinstance[_i - 1] = instance_create(obj_mainchara.x - 4, obj_mainchara.y - 20, obj_caterpillarchara);
        global.cinstance[_i - 1].target = _i * 12;
        knight_cc_cater_dress(global.cinstance[_i - 1], _c);
    }
    return 1;
}

// a follower of a custom character: its own walking frames and name
function knight_cc_cater_dress(_ci, _c)
{
    var _d = knight_cc(_c);
    if (is_undefined(_d) || !i_ex(_ci))
        return 0;
    with (_ci)
    {
        name = _d.key;
        dsprite = _d.walk[0];
        rsprite = _d.walk[1];
        usprite = _d.walk[2];
        lsprite = _d.walk[3];
        slidesprite = _d.walk[0];
        sprite_index = dsprite;
    }
    return 1;
}

// ---------- the text system: their face and their voice in any dialogue (battle box, cutscenes) ----------
// a character's registry entry may carry: face_code (the letter after \F and \T, e.g. "F" for Flowery), fc (the face number:
// Flowery's is Chapter 5's own, 23), face (its face sprite, one frame per expression \E), face_dx / face_dy, voice (its text
// blips, played in turn at a slightly random pitch, as Chapter 5 plays Flowery's)
function knight_cc_by_code(_ch)
{
    for (var _i = 5; _i < array_length(global.knight_ccs); _i++)
    {
        var _d = global.knight_ccs[_i];
        if (is_struct(_d) && variable_struct_exists(_d, "face_code") && _d.face_code == _ch)
            return _d;
    }
    return undefined;
}

function knight_cc_by_fc(_fc)
{
    for (var _i = 5; _i < array_length(global.knight_ccs); _i++)
    {
        var _d = global.knight_ccs[_i];
        if (is_struct(_d) && variable_struct_exists(_d, "fc") && _d.fc == _fc)
            return _d;
    }
    return undefined;
}

// obj_writer: \F<letter>
function knight_cc_face_code(_ch)
{
    var _d = knight_cc_by_code(_ch);
    if (!is_undefined(_d))
        global.fc = _d.fc;
    return 1;
}

// obj_writer: \T<letter> - true when it was a custom character's (its typer is then set)
function knight_cc_typer_code(_ch)
{
    var _d = knight_cc_by_code(_ch);
    if (is_undefined(_d))
        return false;
    global.typer = (variable_global_exists("fighting") && global.fighting == 1) ? 302 : ((variable_global_exists("darkzone") && global.darkzone == 1) ? 301 : 300);
    global.knight_cc_typer = _d.cid;
    return true;
}

// a custom character's spell line, set by its spelltext: { cid, e (face expression), narr (a narration page after it) }
global.knight_cc_line = undefined;
global.knight_cc_narr = "";
global.knight_cc_narr_w = noone;
global.knight_cc_bal = noone;

function knight_cc_say(_cid, _e, _txt, _bal)
{
    global.knight_cc_line = { cid: _cid, e: _e, txt: _txt, bal: _bal, narr: "" };
    return 1;
}

// obj_spellphase (self): the spell line's battle writer. A custom character's line is made with its face, expression and
// voice from the start (the face set before the writer lays out its lines: every line sits beside the face)
function knight_cc_battletext()
{
    var _l = global.knight_cc_line;
    global.knight_cc_line = undefined;
    // (only for the line it was set for: anything else in the box is the game's own text)
    var _d = (is_struct(_l) && global.msg[0] == _l.txt) ? knight_cc(_l.cid) : undefined;
    if (is_undefined(_d) || !variable_struct_exists(_d, "fc"))
    {
        global.knight_cc_narr = "";
        return scr_battletext_default();
    }
    // the battle box: what he did, in the battle's own text; his line: a speech balloon in front of him (like Susie's), in his
    // own voice - it closes with the box
    var _w = scr_battletext_default();
    global.knight_cc_narr = "";
    global.knight_cc_narr_w = _w;
    if (variable_struct_exists(_l, "bal") && _l.bal != "")
        global.knight_cc_bal = knight_say(_l.cid, _l.bal, 1);
    return _w;
}

// obj_spellphase's Step (self): once the line is closed, its narration as a page of its own (no face, the battle's voice)
function knight_cc_narrate()
{
    // a custom character's move is still playing: the spell phase waits for it (the next member's spell never starts on
    // top of it - its spelldelay counts from the text, the move from the cast)
    if (knight_fl_busy() && variable_instance_exists(id, "spelltimer"))
        spelltimer = min(spelltimer, global.spelldelay - 1);
    // his balloon goes when the battle box does
    if (variable_global_exists("knight_cc_bal") && i_ex(global.knight_cc_bal) && !i_ex(global.knight_cc_narr_w))
    {
        if (variable_instance_exists(global.knight_cc_bal, "mywriter") && i_ex(global.knight_cc_bal.mywriter))
        {
            with (global.knight_cc_bal.mywriter)
                instance_destroy();
        }
        with (global.knight_cc_bal)
            instance_destroy();
        global.knight_cc_bal = noone;
    }
    if (global.knight_cc_narr == "" || i_ex(global.knight_cc_narr_w))
        return 0;
    global.msg[0] = global.knight_cc_narr;
    global.knight_cc_narr = "";
    global.knight_cc_narr_w = noone;
    spellwriter = scr_battletext_default();
    return 1;
}

// scr_texttype, typers 300-302 (self: the writer): the fonts and spacing of the game's own party typers, the character's voice
function knight_cc_texttype(_t)
{
    var _d = knight_cc(variable_global_exists("knight_cc_typer") ? global.knight_cc_typer : 5);
    var _snd = (is_undefined(_d) || !variable_struct_exists(_d, "voice")) ? snd_text : _d.voice[0];
    if (!is_numeric(_snd) || _snd < 0 || !audio_exists(_snd))
        _snd = snd_text;
    if (_t == 300)
        scr_textsetup(scr_84_get_font("main"), c_white, x, y, 33, 0, 1, _snd, 8, 18, 0);
    else if (_t == 301)
        scr_textsetup(scr_84_get_font("mainbig"), c_white, x, y, 33, 0, 1, _snd, 16, 36, 1);
    else if (_t == 303)
    {
        // a speech balloon in a fight (like Susie's / Ralsei's typers 74-76): small black text, its own voice
        scr_textsetup(scr_84_get_font("dotumche"), c_black, x, y, 33, 0, 1, _snd, 9, 20, 0);
        extra_ja_vspace = 2;
    }
    else
    {
        scr_textsetup(scr_84_get_font("mainbig"), c_white, x, y, 33, 0, 1, _snd, 16, 28, 1);
        extra_ja_vspace = 2;
    }
    return 1;
}

// scr_textsound (self: the writer): a custom character's voice - one of its blips, never two at once
function knight_cc_textsound(_s)
{
    for (var _i = 5; _i < array_length(global.knight_ccs); _i++)
    {
        var _d = global.knight_ccs[_i];
        if (!is_struct(_d) || !variable_struct_exists(_d, "voice") || _d.voice[0] != _s)
            continue;
        for (var _j = 0; _j < array_length(_d.voice); _j++)
            audio_stop_sound(_d.voice[_j]);
        var _v = snd_play(_d.voice[irandom(array_length(_d.voice) - 1)]);
        snd_pitch(_v, 0.9 + random(0.15));
        return true;
    }
    return false;
}

// obj_face's Draw (self: the face): a custom character's face
function knight_cc_face_draw(_x, _y, _f)
{
    if (!variable_instance_exists(id, "facechange") || facechange > 0)
        return 0;
    var _d = knight_cc_by_fc(global.fc);
    if (is_undefined(_d) || !knight_cc_spr(_d.face))
        return 0;
    draw_sprite_ext(_d.face, global.fe, _x + _d.face_dx, _y + _d.face_dy, _f, _f, 0, c_white, 1);
    return 1;
}

// ---------- a custom character's pose in a scene of the game's (the Violet Knight's parry and power-up) ----------
// The game shows the four's poses with scr_act_charsprite (by name, on Kris / Susie / Ralsei / Noelle); a custom character
// gets a marker of its own pose on its own hero instead (its hero hidden meanwhile).
global.knight_cc_pm = undefined;

function knight_cc_pose_marker(_h, _spr, _spd)
{
    knight_cc_pose_marker_end();
    if (!i_ex(_h) || !knight_cc_spr(_spr))
        return 0;
    var _m = scr_dark_marker(_h.x, _h.y, _spr);
    _m.image_index = 0;
    _m.image_speed = _spd;
    _m.depth = _h.depth - 1;
    _h.image_alpha = 0;
    global.knight_cc_pm = { m: _m, h: _h };
    return 1;
}

function knight_cc_pose_marker_end()
{
    var _p = global.knight_cc_pm;
    global.knight_cc_pm = undefined;
    if (!is_struct(_p))
        return 0;
    if (i_ex(_p.m))
    {
        with (_p.m)
            instance_destroy();
    }
    if (i_ex(_p.h))
        _p.h.image_alpha = 1;
    return 1;
}

// the pose of a custom character's power-up flurry (Flowery: his Jarona punch)
function knight_cc_flurry_spr(_c)
{
    var _d = knight_cc(_c);
    if (is_undefined(_d))
        return -1;
    if (variable_struct_exists(_d, "flurry") && knight_cc_spr(_d.flurry))
        return _d.flurry;
    return _d.poses.attack;
}
