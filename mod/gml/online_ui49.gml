// ===== Build 49: the room page's BOTS (host): add / remove bots, each bot's difficulty =====
// BOTS lists the room's bots (name, preset), ADD A BOT, REMOVE A BOT, ALL BOTS (the room's BOT SKILL for every bot not set
// one by one). Z on a bot: its page - PRESET (DUMMY, EASY, NORMAL, HARD, EXPERT, PERFECT) and the sliders REACTION TIME,
// PREDICTION, MISTAKES, PRECISION, HEALING, CHARGING, AGGRESSION (moving one makes it CUSTOM), ROOM'S SKILL (back to the
// room's BOT SKILL). The numbers behind the presets: kfo_bot_presets() in online_bots.gml.

function kfo_ui_bots_list()
{
    var _o = kfo_get();
    var _l = [];
    if (!is_struct(_o.H))
        return _l;
    for (var _i = 0; _i < array_length(_o.H.pl); _i++)
    {
        if (_o.H.pl[_i].bot)
            array_push(_l, _o.H.pl[_i]);
    }
    return _l;
}

function kfo_ui_bots_rows(_pg)
{
    if (_pg == "onl_bot")
        return ["bpre", "react", "pred", "miss", "prec", "heal", "chg", "aggr", "bdef", "done"];
    var _r = [];
    var _l = kfo_ui_bots_list();
    for (var _i = 0; _i < array_length(_l); _i++)
        array_push(_r, "bot" + string(_i));
    array_push(_r, "badd", "bdel", "ball", "done");
    return _r;
}

function kfo_ui_bot_i()
{
    var _u = global.knight_ui;
    return variable_struct_exists(_u, "bot_i") ? _u.bot_i : 0;
}

function kfo_ui_bots_label(_pg, _id)
{
    var _o = kfo_get();
    switch (_id)
    {
        case "done": return ["DONE", ""];
        case "badd": return ["ADD A BOT", string(array_length(kfo_ui_bots_list())) + " / 7"];
        case "bdel": return ["REMOVE A BOT", ""];
        case "ball": return ["BOT SKILL (ROOM)", kfo_bot_pre_name(kfo_jn(_o.H.set, "botp", 2))];
        case "bdef": return ["ROOM'S SKILL", ""];
    }
    if (string_copy(_id, 1, 3) == "bot")
    {
        var _i = real(string_digits(_id));
        var _l = kfo_ui_bots_list();
        if (_i >= array_length(_l))
            return ["?", ""];
        var _c = kfo_host_botcfg(_i);
        return [_l[_i].n, kfo_bot_pre_name(_c.pre) + (_c.own ? "" : " (ROOM)")];
    }
    var _c2 = kfo_host_botcfg(kfo_ui_bot_i());
    if (_id == "bpre")
        return ["PRESET", kfo_bot_pre_name(_c2.pre)];
    var _sl = kfo_bot_sliders();
    for (var _k = 0; _k < array_length(_sl); _k++)
    {
        if (_sl[_k][0] == _id)
        {
            var _v = variable_struct_get(_c2, _id);
            var _t = string(_v);
            if (_id == "react" || _id == "pred")
                _t = string(_v) + " F";
            else
                _t = string(_v) + "%";
            return [_sl[_k][1], _t];
        }
    }
    return [_id, ""];
}

// a slider's place, 0-100
function kfo_ui_bots_slider_v(_id)
{
    var _c = kfo_host_botcfg(kfo_ui_bot_i());
    var _sl = kfo_bot_sliders();
    for (var _k = 0; _k < array_length(_sl); _k++)
    {
        if (_sl[_k][0] == _id)
            return ((variable_struct_get(_c, _id) - _sl[_k][2]) * 100) / max(1, _sl[_k][3] - _sl[_k][2]);
    }
    return 0;
}

function kfo_ui_bots_is_slider(_id)
{
    var _sl = kfo_bot_sliders();
    for (var _k = 0; _k < array_length(_sl); _k++)
    {
        if (_sl[_k][0] == _id)
            return true;
    }
    return false;
}

function kfo_ui_bots_desc(_pg, _id)
{
    switch (_id)
    {
        case "done": return "Z: back.";
        case "badd": return "Z: one more bot (up to 7). Bots play by the#players' rules: same SOUL, damage and skills.";
        case "bdel": return "Z: the last bot leaves the room (not while a#match runs).";
        case "ball": return "< >: the skill of every bot you did not set#one by one (DUMMY ... PERFECT).";
        case "bdef": return "Z: this bot plays at the room's BOT SKILL#again.";
        case "bpre": return "< >: DUMMY (barely moves), EASY, NORMAL, HARD,#EXPERT, PERFECT (dodges all it can).";
        case "react": return "< >: frames before it notices a new bullet#(0 = at once).";
        case "pred": return "< >: how many frames ahead it works out where#the bullets will be.";
        case "miss": return "< >: how often it makes a wrong move on#purpose.";
        case "prec": return "< >: how exactly it moves (less: a wobble in#its steps).";
        case "heal": return "< >: how well it heals: when HP is low enough,#and only when it is safe.";
        case "chg": return "< >: how well it uses its gauge (waits to draw#two skills when it can).";
        case "aggr": return "< >: how often it sends attack skills (and it#picks a TARGETING mode for the moment).";
    }
    if (string_copy(_id, 1, 3) == "bot")
        return "Z: this bot's difficulty (preset, reaction,#prediction, mistakes, precision...).";
    return "";
}

function kfo_ui_bots_change(_pg, _id, _d, _ok)
{
    var _o = kfo_get();
    if (!kfo_is_host() || !is_struct(_o.H))
    {
        knight_ui_warn("Only the host changes the bots.");
        return false;
    }
    var _h = _o.H;
    switch (_id)
    {
        case "badd":
        case "bdel":
            if (!_ok)
                return false;
            var _n = kfo_set_clean(_h.set);
            _n.bots = clamp(_n.bots + ((_id == "badd") ? 1 : -1), 0, 7);
            if (_n.bots == _h.set.bots)
                return false;
            return kfo_ui_set_apply(_n);
        case "ball":
            var _n2 = kfo_set_clean(_h.set);
            _n2.botp = (kfo_jn(_n2, "botp", 2) + kfo_bot_pre_count() + _d) mod kfo_bot_pre_count();
            return kfo_ui_set_apply(_n2);
    }
    if (_pg == "onl_bots" && string_copy(_id, 1, 3) == "bot")
    {
        if (_ok)
        {
            var _u = global.knight_ui;
            _u.bot_i = real(string_digits(_id));
            kfo_ui_pg_open("onl_bot", "onl_bots");
        }
        return false;
    }
    var _bi = kfo_ui_bot_i();
    var _c = kfo_host_botcfg(_bi);
    if (_id == "bdef")
    {
        if (!_ok)
            return false;
        _h.botcfg[_bi] = kfo_bot_cfg(kfo_jn(_h.set, "botp", 2));
        return true;
    }
    if (_id == "bpre")
    {
        var _np = ((max(0, _c.pre) + kfo_bot_pre_count() + _d) mod kfo_bot_pre_count());
        var _nc = kfo_bot_cfg(_np);
        _nc.own = true;
        _h.botcfg[_bi] = _nc;
        return true;
    }
    var _sl = kfo_bot_sliders();
    for (var _k = 0; _k < array_length(_sl); _k++)
    {
        if (_sl[_k][0] == _id)
        {
            variable_struct_set(_c, _id, clamp(variable_struct_get(_c, _id) + (_d * _sl[_k][4]), _sl[_k][2], _sl[_k][3]));
            _c.pre = -1;
            _c.own = true;
            _c.every = max(1, round((100 - _c.prec) / 20));
            return true;
        }
    }
    return false;
}
