
// ===== Build 45: KNIGHT FIGHTS ONLINE - the room's settings, presets and mutators =====
// One struct holds every setting of a room (the host's copy is sent with every lobby update and once more, frozen, with the
// match start). Every field is checked by kfo_set_clean, so a setting from the network, the ini or a pasted preset code can
// never hold a value the game does not know. The match reads the EFFECTIVE settings (kbr_eff): the struct with the mutators
// applied, worked out the same way in every game.
// Knights are online ids (kbr_ok_*): 0 NORMAL, 1 KAIZO, 2 ELECKNIGHT, 3 VIOLET, 4 THORN, 5 KNIGHTMARE. The Cyan Knight has no
// online id, so no setting, preset or pasted code can ever put it in a match.

// ---------- the option table (drives the settings page, the descriptions and the checks) ----------
// kind: "num" (lo..hi step st, fmt: "" plain, "%" percent, "s" seconds, "m" minutes, "f" frames), "enum" (names), "bool",
// "kn" (online knight on/off: kn array), "kw" (knight weight 0-9: kw array), "sk" (skill on/off: skoff list), "mut" (mutator)
function kfo_cats()
{
    // build 52: ten plain pages - the everyday ones first, the rarely touched ones in ADVANCED
    // DRBR: KNIGHTS became BOSSES (the knights and the secret bosses: who you fight)
    return ["BASICS", "BOSSES", "DIFFICULTY", "SKILLS", "SKILL LIST", "TARGETING", "MODIFIERS", "ENDGAME", "ADVANCED", "PRESETS"];
}

function kfo_opt(_id, _cat, _lab, _kind, _lo, _hi, _st, _def, _names, _fmt, _desc)
{
    return { oid: _id, cat: _cat, lab: _lab, kind: _kind, lo: _lo, hi: _hi, st: _st, def: _def, names: _names, fmt: _fmt, desc: _desc };
}

// build 52: the options, re-sorted onto the new pages with short names and plain descriptions (two lines at most, "#"
// breaks them). The ids, ranges and defaults are build 51's: saved rooms, presets and settings codes still work.
function kfo_opts()
{
    if (variable_global_exists("kfo_opt_cache") && is_array(global.kfo_opt_cache))
        return global.kfo_opt_cache;
    var _o = [];
    // 0 BASICS
    array_push(_o, kfo_opt("maxp", 0, "PLAYERS", "num", 2, 8, 1, 8, [], "", "How many SOULs fit in the room."));
    array_push(_o, kfo_opt("mhp", 0, "MAX HP", "num", 60, 300, 10, 150, [], "", "Everyone's HP. More HP = longer matches."));
    array_push(_o, kfo_opt("dmul", 0, "DAMAGE", "num", 25, 300, 25, 100, [], "%", "How much every hit hurts.#100% is normal."));
    array_push(_o, kfo_opt("hmul", 0, "HEALING", "num", 0, 300, 25, 100, [], "%", "How much heals give back.#0% turns healing off."));
    array_push(_o, kfo_opt("spd", 0, "SOUL SPEED", "num", 3, 6, 1, 4, [], "", "How fast SOULs move.#4 is normal Chapter 3 speed."));
    array_push(_o, kfo_opt("tlim", 0, "TIME LIMIT", "num", 0, 30, 5, 0, [], "m", "Ends the match after this long.#Most HP wins. OFF = no limit."));
    array_push(_o, kfo_opt("bots", 0, "BOTS", "num", 0, 7, 1, 0, [], "", "Computer players that dodge with you."));
    array_push(_o, kfo_opt("botp", 0, "BOT SKILL", "enum", 0, 5, 1, 2, ["DUMMY", "EASY", "NORMAL", "HARD", "EXPERT", "PERFECT"], "", "How good the bots are. Each bot can be#changed on its own on the room page."));
    // 1 KNIGHTS
    // build 52: ENCOUNTERS - a preset of the rows below (KNIGHTS, JEVIL, SECRET BOSSES, ALL BOSSES; CUSTOM when the rows are set
    // by hand). It is not a setting of its own: it reads and sets the rows (kfo_encp_*), so it travels with them.
    // DRBR: WHO FIGHTS (build 52's ENCOUNTERS); each row's description says what that boss is: its chapter, its SOUL, its sends
    array_push(_o, kfo_opt("encp", 1, "WHO FIGHTS", "encp", 0, 8, 1, 0, [], "", "Who you fight: the Knights, one boss, the#secret bosses or all. CUSTOM: the rows below."));
    for (var _k = 0; _k < kbr_ok_count(); _k++)
        array_push(_o, kfo_opt("kn" + string(_k), 1, kbr_ok_short(_k), "kn", 0, 1, 1, 1, [], "", kfo_kn_desc(_k)));
    array_push(_o, kfo_opt("open", 1, "FIRST BOSS", "open", 0, kbr_ok_count() - 1, 1, 0, [], "", "Who starts the match."));
    array_push(_o, kfo_opt("rush", 1, "BOSS ORDER", "enum", 0, 6, 1, 0, ["CLASSIC", "RUSH", "RAPID", "RANDOM", "PROGRESS", "WEIGHTED", "NIGHTMARE"], "",
        "CLASSIC: each one stays a while.#RUSH: a new one every attack."));
    array_push(_o, kfo_opt("stay", 1, "BOSS STAYS", "num", 1, 8, 1, 3, [], "", "CLASSIC: how many attacks each one does#before the next one steps in."));
    array_push(_o, kfo_opt("next", 1, "SHOW NEXT", "bool", 0, 1, 1, 1, [], "", "Show who comes next."));
    // 2 DIFFICULTY
    array_push(_o, kfo_opt("ramp", 2, "STAGE SPEED", "enum", 0, 3, 1, 1, ["SLOW", "NORMAL", "FAST", "INSTANT"], "", "How fast the match gets harder.#INSTANT starts at stage 3."));
    array_push(_o, kfo_opt("maxst", 2, "LAST STAGE", "num", 0, 4, 1, 4, [], "st", "How hard it can get. OVERDRIVE is the top."));
    array_push(_o, kfo_opt("twin", 2, "TWIN KNIGHT", "enum", 0, 2, 1, 0, ["STAGE 3", "ALWAYS", "NEVER"], "", "A second Knight attacking at the same time."));
    array_push(_o, kfo_opt("hyper", 2, "HYPER SPEED", "enum", 0, 2, 1, 0, ["STAGE 4", "ALWAYS", "NEVER"], "", "Everything runs 25% faster."));
    array_push(_o, kfo_opt("hard", 2, "HARD ATTACKS", "bool", 0, 1, 1, 1, [], "", "The Knights' toughest attacks.#OFF: they never use them."));
    array_push(_o, kfo_opt("speedup", 2, "FASTER SWAPS", "bool", 0, 1, 1, 0, [], "", "Knights swap faster as time goes on."));
    // 3 SKILLS
    array_push(_o, kfo_opt("skills", 3, "SKILLS", "bool", 0, 1, 1, 1, [], "", "Charge your TP to draw skills.#OFF: just dodging."));
    // build 52: SKILL FAMILIES - the knights' attack skills, Jevil's, or both (MATCH: whoever is in the match)
    // DRBR: SENDS (build 52's SKILL FAMILIES; same id and values: 0 MATCH CURRENT BOSS, 1 KNIGHT, 2 JEVIL, 3 ALL ENABLED, then the
    // other families by their fid) - steps only through the families this build has (kbr_sends_modes)
    array_push(_o, kfo_opt("skfam", 3, "SENDS", "enum", 0, 7, 1, 0, ["CURRENT BOSS", "KNIGHT ONLY", "JEVIL ONLY", "ALL ENABLED", "SPAMTON ONLY", "GERSON ONLY", "PINK ONLY", "FLOWERY ONLY"], "",
        "Whose attacks you send: CURRENT BOSS (the one#on stage), every boss in the match, or one."));
    array_push(_o, kfo_opt("fullheal", 3, "START WITH MAX", "bool", 0, 1, 1, 1, [], "", "Everyone starts with one MAX (a full heal)."));
    array_push(_o, kfo_opt("slots", 3, "SKILL SLOTS", "num", 1, 4, 1, 4, [], "", "How many skills you can carry."));
    array_push(_o, kfo_opt("scost", 3, "SKILL PRICE", "num", 50, 150, 25, 100, [], "%", "How much TP a skill costs.#Lower = more skills."));
    array_push(_o, kfo_opt("cdm", 3, "COOLDOWN", "num", 25, 300, 25, 100, [], "%", "The wait between two skills.#100% is 3 seconds."));
    array_push(_o, kfo_opt("skdmg", 3, "SKILL DAMAGE", "num", 50, 200, 25, 100, [], "%", "How much attack skills hurt."));
    array_push(_o, kfo_opt("shp", 3, "SHIELD HITS", "num", 1, 5, 1, 3, [], "", "How many hits one SHIELD blocks."));
    array_push(_o, kfo_opt("rsec", 3, "REFLECT TIME", "num", 2, 10, 1, 5, [], "s", "How long REFLECTION bounces attacks back."));
    // 4 SKILL LIST
    for (var _s = 1; _s < kbr_skill_count(); _s++)
    {
        if (_s != 16)
            array_push(_o, kfo_opt("sk" + string(_s), 4, string_upper(kbr_skill_name(_s)), "sk", 0, 1, 1, 1, [], "", kfo_skill_desc_short(_s)));
    }
    // 5 TARGETING
    array_push(_o, kfo_opt("tg", 5, "TARGETING", "bool", 0, 1, 1, 1, [], "", "ON: you pick who your attacks hit.#OFF: they hit everyone."));
    for (var _t = 0; _t < 7; _t++)
        array_push(_o, kfo_opt("tgm" + string(_t), 5, kbr_tg_name(_t), "bool", 0, 1, 1, 1, [], "", kbr_tg_desc(_t)));
    array_push(_o, kfo_opt("shards", 5, "SHADOW CRYSTALS", "bool", 0, 1, 1, 1, [], "", "Knockouts give SHADOW CRYSTALS,#and crystals make your attacks stronger."));
    array_push(_o, kfo_opt("outn", 5, "UNDERDOG TP", "bool", 0, 1, 1, 1, [], "", "Your TP fills faster for every player#who is aiming at you."));
    // 6 MODIFIERS
    var _m = kfo_mut_ids();
    for (var _i = 0; _i < array_length(_m); _i++)
        array_push(_o, kfo_opt(_m[_i], 6, kfo_mut_name(_m[_i]), "mut", 0, 1, 1, 0, [], "", kfo_mut_desc(_m[_i])));
    // 7 ENDGAME
    array_push(_o, kfo_opt("sd", 7, "SUDDEN DEATH", "bool", 0, 1, 1, 1, [], "", "Late in the match, max HP starts draining#and the Dog eats green skills."));
    array_push(_o, kfo_opt("fin", 7, "SD STARTS", "num", 1, 5, 1, 2, [], "m", "How long after the last stage begins."));
    array_push(_o, kfo_opt("sdrate", 7, "HP DRAIN", "num", 1, 3, 1, 1, [], "", "Max HP lost every second in sudden death."));
    array_push(_o, kfo_opt("sdfloor", 7, "HP FLOOR", "num", 10, 100, 10, 20, [], "", "Sudden death stops draining at this max HP."));
    array_push(_o, kfo_opt("sdgreen", 7, "KEEP GREEN", "bool", 0, 1, 1, 0, [], "", "ON: the Annoying Dog leaves your heals#and shields alone."));
    array_push(_o, kfo_opt("sdfast", 7, "SD RUSH", "bool", 0, 1, 1, 1, [], "", "A new Knight every attack in sudden death."));
    array_push(_o, kfo_opt("ft", 7, "FINAL TWO", "bool", 0, 1, 1, 1, [], "", "When two SOULs are left: a showdown#with harder attacks."));
    array_push(_o, kfo_opt("ftmus", 7, "FINAL MUSIC", "bool", 0, 1, 1, 1, [], "", "Special music for the final two."));
    array_push(_o, kfo_opt("fthyper", 7, "FINAL HYPER", "bool", 0, 1, 1, 0, [], "", "The final two fight at Hyper Speed."));
    array_push(_o, kfo_opt("tie", 7, "TIE RULE", "enum", 0, 1, 1, 0, ["BOTH WIN", "LAST WINS"], "", "The last two fall at the same moment:#both win, or the one who fell last."));
    // 8 ADVANCED
    array_push(_o, kfo_opt("minp", 8, "MIN PLAYERS", "num", 2, 8, 1, 2, [], "", "Players needed before the host can start."));
    array_push(_o, kfo_opt("ready", 8, "READY CHECK", "enum", 0, 1, 1, 0, ["READY ONES", "EVERYONE"], "", "Start with whoever is ready,#or wait for everyone."));
    array_push(_o, kfo_opt("spec", 8, "WATCHERS", "bool", 0, 1, 1, 1, [], "", "People not playing can watch the match."));
    array_push(_o, kfo_opt("sps", 8, "WATCH SPOTS", "num", 0, 4, 1, 2, [], "", "Extra room spots just for watchers."));
    array_push(_o, kfo_opt("rejoin", 8, "REJOIN", "bool", 0, 1, 1, 1, [], "", "A player who disconnects can come back#and watch the rest."));
    array_push(_o, kfo_opt("hp0", 8, "START HP", "num", 25, 100, 25, 100, [], "%", "Start the match with this much of your HP."));
    array_push(_o, kfo_opt("g0", 8, "START TP", "num", 0, 100, 10, 0, [], "%", "Start the match with this much TP."));
    array_push(_o, kfo_opt("cdn", 8, "COUNTDOWN", "num", 3, 10, 1, 3, [], "s", "The countdown before the first attack."));
    array_push(_o, kfo_opt("ifr", 8, "HIT FLASH", "num", 50, 200, 25, 100, [], "%", "How long you can't be hit again after a hit."));
    array_push(_o, kfo_opt("gmul", 8, "TP FILL", "num", 50, 300, 25, 100, [], "%", "How fast TP fills by itself."));
    array_push(_o, kfo_opt("grz", 8, "GRAZE TP", "num", 50, 300, 25, 100, [], "%", "How much TP a graze gives."));
    array_push(_o, kfo_opt("gap", 8, "ATTACK GAP", "num", 0, 30, 6, 18, [], "f", "The pause between two attacks."));
    array_push(_o, kfo_opt("trans", 8, "ENTRANCE", "num", 0, 90, 6, 36, [], "f", "How long a new boss's entrance takes."));
    array_push(_o, kfo_opt("rep", 8, "SAME TWICE", "bool", 0, 1, 1, 0, [], "", "Random orders: can the same boss#come twice in a row?"));
    array_push(_o, kfo_opt("recent", 8, "RECENT BLOCK", "num", 0, 3, 1, 0, [], "", "Random orders: the last few bosses#can't be picked again."));
    array_push(_o, kfo_opt("arep", 8, "REPEAT BLOCK", "num", 0, 5, 1, 3, [], "", "A boss won't repeat its last few attacks."));
    for (var _k = 0; _k < kbr_ok_count(); _k++)
        array_push(_o, kfo_opt("kw" + string(_k), 8, kbr_ok_short(_k) + " ODDS", "kw", 0, 9, 1, 3, [], "", "How often " + kbr_ok_name(_k) + " shows up in#the RANDOM, WEIGHTED and NIGHTMARE orders."));
    global.kfo_opt_cache = _o;
    return _o;
}

// build 52: a skill's description for SKILL LIST (the skill's own text without the pool details)
function kfo_skill_desc_short(_s)
{
    var _d = kbr_skill_desc(_s);
    var _c = string_pos(": ", _d);
    if (_c > 0 && _c < 40)
        _d = string_delete(_d, 1, _c + 1);
    _d = (kbr_skill_red(_s) ? "RED: " : "GREEN: ") + string_replace_all(_d, "#", " ");
    // two lines again, at the space nearest the middle
    if (string_length(_d) > 40)
    {
        var _best = -1;
        for (var _i = 16; _i <= min(40, string_length(_d)); _i++)
        {
            if (string_char_at(_d, _i) == " ")
                _best = _i;
        }
        if (_best > 0)
            _d = string_copy(_d, 1, _best - 1) + "#" + string_delete(_d, 1, _best);
    }
    return _d;
}

function kfo_opt_find(_id)
{
    var _o = kfo_opts();
    for (var _i = 0; _i < array_length(_o); _i++)
    {
        if (_o[_i].oid == _id)
            return _o[_i];
    }
    return undefined;
}

function kfo_opts_of(_cat)
{
    var _o = kfo_opts();
    var _l = [];
    for (var _i = 0; _i < array_length(_o); _i++)
    {
        if (_o[_i].cat == _cat)
            array_push(_l, _o[_i]);
    }
    return _l;
}

// ---------- mutators ----------
function kfo_mut_ids()
{
    return ["m_storm", "m_hyper", "m_dbl", "m_ohko", "m_giant", "m_tiny", "m_mirror", "m_rcost", "m_fast", "m_noheal", "m_shield", "m_rapid", "m_roul",
        "m_nmesc", "m_overlap", "m_sd0", "m_dgraze", "m_lowhp", "m_chaos"];
}

function kfo_mut_name(_id)
{
    switch (_id)
    {
        case "m_storm": return "BULLET STORM";
        case "m_hyper": return "HYPER SPEED";
        case "m_dbl": return "DOUBLE DAMAGE";
        case "m_ohko": return "ONE HIT OUT";
        case "m_giant": return "GIANT SOULS";
        case "m_tiny": return "TINY SOULS";
        case "m_mirror": return "MIRROR CONTROLS";
        case "m_rcost": return "RANDOM COSTS";
        case "m_fast": return "FAST CHARGE";
        case "m_noheal": return "NO HEALING";
        case "m_shield": return "SHIELD MADNESS";
        case "m_rapid": return "RAPID RUSH";
        case "m_roul": return "KNIGHT ROULETTE";
        case "m_nmesc": return "NIGHTMARE RISE";
        case "m_overlap": return "EXTREME OVERLAP";
        case "m_sd0": return "INSTANT SD";
        case "m_dgraze": return "DOUBLE GRAZE";
        case "m_lowhp": return "LOW HP SURVIVAL";
        case "m_chaos": return "MAXIMUM CHAOS";
    }
    return "?";
}

function kfo_mut_desc(_id)
{
    switch (_id)
    {
        case "m_storm": return "The Twin Knight joins every attack.";
        case "m_hyper": return "Everything runs 25% faster, all match.";
        case "m_dbl": return "Every hit hurts twice as much.";
        case "m_ohko": return "One hit and you're OUT.#(A SHIELD still saves you.)";
        case "m_giant": return "Every SOUL is bigger and easier to hit.";
        case "m_tiny": return "Every SOUL is smaller and harder to hit.";
        case "m_mirror": return "Left is right, up is down. For everyone.";
        case "m_rcost": return "Every skill costs a random amount of TP.";
        case "m_fast": return "TP fills twice as fast.";
        case "m_noheal": return "No healing at all. No heals, no MAX.";
        case "m_shield": return "Everyone starts shielded, and half of#all skills drawn are SHIELDs.";
        case "m_rapid": return "A new Knight every single attack.";
        case "m_roul": return "Any Knight, any time, totally random.";
        case "m_nmesc": return "Knightmare shows up more and more.";
        case "m_overlap": return "The Twin Knight and the hardest attacks#from the very start.";
        case "m_sd0": return "Sudden death from the first attack.";
        case "m_dgraze": return "Grazing gives twice the TP.";
        case "m_lowhp": return "Everyone has only 60 max HP.";
        case "m_chaos": return "BULLET STORM, HYPER SPEED, RAPID RUSH,#FAST CHARGE, RANDOM COSTS, DOUBLE GRAZE.";
    }
    return "";
}

// ---------- defaults and the checks ----------
function kfo_set_default()
{
    // build 52: the knights (the presets stay what they were: a secret boss joins through ENCOUNTERS or its own preset)
    var _s = { pre: "CLASSIC", kn: kfo_encp_rows(1), kw: kbr_ok_kw_default(), skoff: [] };
    var _o = kfo_opts();
    for (var _i = 0; _i < array_length(_o); _i++)
    {
        var _e = _o[_i];
        if (_e.kind == "num" || _e.kind == "enum" || _e.kind == "bool" || _e.kind == "mut" || _e.kind == "open")
            variable_struct_set(_s, _e.oid, _e.def);
    }
    return _s;
}

function kfo_num_in(_v, _lo, _hi, _st, _def)
{
    if (!is_numeric(_v) || is_nan(_v))
        return _def;
    var _x = clamp(_v, _lo, _hi);
    if (_st > 0)
        _x = _lo + (round((_x - _lo) / _st) * _st);
    return clamp(_x, _lo, _hi);
}

// any struct (from the network, the ini, a pasted code) -> a complete, valid settings struct
function kfo_set_clean(_s)
{
    var _o = kfo_set_default();
    if (!is_struct(_s))
        return _o;
    var _ops = kfo_opts();
    for (var _i = 0; _i < array_length(_ops); _i++)
    {
        var _e = _ops[_i];
        if (!(_e.kind == "num" || _e.kind == "enum" || _e.kind == "bool" || _e.kind == "mut"))
            continue;
        var _v = kfo_jv(_s, _e.oid);
        if (is_bool(_v))
            _v = _v ? 1 : 0;
        if (is_numeric(_v) && !is_string(_v))
            variable_struct_set(_o, _e.oid, kfo_num_in(real(_v), _e.lo, _e.hi, _e.st, _e.def));
    }
    // knights: online ids only (never the joke fight: kbr_ok_valid), roster order, at least one
    var _kn = kfo_ja(_s, "kn");
    var _l = [];
    for (var _k = 0; _k < kbr_ok_count(); _k++)
    {
        for (var _j = 0; _j < array_length(_kn); _j++)
        {
            if (is_numeric(_kn[_j]) && _kn[_j] == _k && kbr_ok_valid(_k))
            {
                array_push(_l, _k);
                break;
            }
        }
    }
    if (array_length(_l) > 0 || is_array(kfo_jv(_s, "kn")))
        _o.kn = (array_length(_l) > 0) ? _l : [0];
    var _kw = kfo_ja(_s, "kw");
    for (var _k = 0; _k < kbr_ok_count(); _k++)
    {
        if (_k < array_length(_kw))
            _o.kw[_k] = kfo_num_in(_kw[_k], 0, 9, 1, _o.kw[_k]);
    }
    var _op = kfo_jn(_s, "open", -1);
    _o.open = _o.kn[0];
    for (var _j = 0; _j < array_length(_o.kn); _j++)
    {
        if (_o.kn[_j] == _op)
            _o.open = _op;
    }
    var _sk = kfo_ja(_s, "skoff");
    _o.skoff = [];
    for (var _j = 0; _j < array_length(_sk); _j++)
    {
        if (is_numeric(_sk[_j]) && _sk[_j] >= 1 && _sk[_j] < kbr_skill_count() && _sk[_j] != 16 && _sk[_j] == floor(_sk[_j]))
            array_push(_o.skoff, _sk[_j]);
    }
    if (array_length(_o.skoff) >= kbr_skill_count() - 2)
    {
        _o.skoff = [];
        _o.skills = 0;
    }
    var _pre = kfo_js(_s, "pre", "CUSTOM");
    _o.pre = (string_length(_pre) > 0 && string_length(_pre) <= 16) ? string_upper(kfo_clean_name(_pre)) : "CUSTOM";
    if (_o.pre == "")
        _o.pre = "CUSTOM";
    // the rules between settings
    if (_o.minp > _o.maxp)
        _o.minp = _o.maxp;
    // DRBR: SENDS can only be a choice this build has (a family whose boss is not here: MATCH CURRENT BOSS)
    var _sm = kbr_sends_modes();
    var _smok = false;
    for (var _j = 0; _j < array_length(_sm); _j++)
    {
        if (_sm[_j] == _o.skfam)
            _smok = true;
    }
    if (!_smok)
        _o.skfam = 0;
    if (_o.m_giant && _o.m_tiny)
        _o.m_tiny = 0;
    // targeting: at least one mode stays on (CHAOS)
    var _any = false;
    for (var _t = 0; _t < 7; _t++)
    {
        if (variable_struct_get(_o, "tgm" + string(_t)) == 1)
            _any = true;
    }
    if (!_any)
        _o.tgm0 = 1;
    var _rush = 0;
    if (_o.m_rapid)
        _rush++;
    if (_o.m_roul)
        _rush++;
    if (_o.m_nmesc)
        _rush++;
    if (_rush > 1)
    {
        // one switching mutator at a time: the first one on the list stays
        if (_o.m_rapid)
        {
            _o.m_roul = 0;
            _o.m_nmesc = 0;
        }
        else
            _o.m_nmesc = 0;
    }
    return _o;
}

// the settings a match plays with: the mutators applied (the same in every game)
function kbr_eff(_s)
{
    var _e = kfo_set_clean(_s);
    if (_e.m_chaos)
    {
        _e.m_storm = 1;
        _e.m_hyper = 1;
        _e.m_rapid = 1;
        _e.m_fast = 1;
        _e.m_rcost = 1;
        _e.m_dgraze = 1;
        _e.m_roul = 0;
        _e.m_nmesc = 0;
    }
    if (_e.m_storm || _e.m_overlap)
        _e.twin = 1;
    if (_e.m_hyper)
        _e.hyper = 1;
    if (_e.m_dbl)
        _e.dmul *= 2;
    if (_e.m_fast)
        _e.gmul *= 2;
    if (_e.m_dgraze)
        _e.grz *= 2;
    if (_e.m_lowhp)
        _e.mhp = min(_e.mhp, 60);
    if (_e.m_rapid)
        _e.rush = 2;
    if (_e.m_roul)
        _e.rush = 3;
    if (_e.m_nmesc)
    {
        _e.rush = 6;
        var _has = false;
        for (var _i = 0; _i < array_length(_e.kn); _i++)
        {
            if (_e.kn[_i] == kbr_ok_nightmare_id())
                _has = true;
        }
        if (!_has)
            array_push(_e.kn, kbr_ok_nightmare_id());
    }
    if (_e.m_noheal)
    {
        _e.fullheal = 0;
        _e.hmul = 0;
        array_push(_e.skoff, 11, 12, 14);
    }
    _e.ohko = _e.m_ohko;
    _e.mirror = _e.m_mirror;
    _e.soul = _e.m_giant ? 1.5 : (_e.m_tiny ? 0.6 : 1);
    _e.sd0 = _e.m_sd0;
    _e.overlap = _e.m_overlap;
    _e.shieldmad = _e.m_shield;
    _e.rcost = _e.m_rcost;
    return _e;
}

// the value of option _e in settings _s, as the settings page shows it
function kfo_opt_text(_e, _s)
{
    switch (_e.kind)
    {
        case "kn":
            return kfo_set_has_kn(_s, real(string_digits(_e.oid))) ? "ON" : "OFF";
        case "kw":
            return string(_s.kw[real(string_digits(_e.oid))]);
        case "sk":
            return kfo_set_has_sk(_s, real(string_digits(_e.oid))) ? "ON" : "OFF";
        case "open":
            return kbr_ok_short(_s.open);
        case "encp":
            return kfo_encp_name(kfo_encp_of(_s));
        case "bool":
        case "mut":
            return variable_struct_get(_s, _e.oid) ? "ON" : "OFF";
        case "enum":
            return _e.names[clamp(variable_struct_get(_s, _e.oid), 0, array_length(_e.names) - 1)];
    }
    var _v = variable_struct_get(_s, _e.oid);
    switch (_e.fmt)
    {
        case "%": return string(_v) + "%";
        case "s": return string(_v) + " S";
        case "m": return (_v == 0) ? "OFF" : (string(_v) + " MIN");
        case "f": return (_v == 0) ? "NONE" : (string(round(_v / 3) / 10) + " S");
        case "st":
            var _sn = ["PURE", "GUESTS", "SHUFFLE", "KNGHTMARE", "OVERDRIVE"];
            return _sn[clamp(_v, 0, 4)];
    }
    return string(_v);
}

function kfo_set_has_kn(_s, _k)
{
    for (var _i = 0; _i < array_length(_s.kn); _i++)
    {
        if (_s.kn[_i] == _k)
            return true;
    }
    return false;
}

function kfo_set_has_sk(_s, _id)
{
    for (var _i = 0; _i < array_length(_s.skoff); _i++)
    {
        if (_s.skoff[_i] == _id)
            return false;
    }
    return true;
}

// change option _id of a copy of _s by _d (-1 / +1; Z toggles). Returns the new settings or a string saying why not.
function kfo_opt_change(_s, _id, _d)
{
    var _n = kfo_set_clean(_s);
    var _e = kfo_opt_find(_id);
    if (is_undefined(_e))
        return _n;
    switch (_e.kind)
    {
        case "kn":
            var _k = real(string_digits(_id));
            var _l = [];
            var _on = false;
            for (var _i = 0; _i < array_length(_n.kn); _i++)
            {
                if (_n.kn[_i] == _k)
                    _on = true;
                else
                    array_push(_l, _n.kn[_i]);
            }
            if (_on && array_length(_l) == 0)
                return "At least one knight has to stay in.";
            if (!_on)
                array_push(_l, _k);
            _n.kn = _l;
            break;
        case "encp":
            // the next preset that changes something (one with no encounter in this build is skipped)
            // DRBR: in the display order (kfo_encp_order), skipping presets with nothing in this build and ones that would not
            // change the rows (with one secret boss, JEVIL and SECRET BOSSES are the same rows)
            var _ord = kfo_encp_order();
            var _cur = kfo_encp_of(_n);
            var _pos = 0;
            for (var _i = 0; _i < array_length(_ord); _i++)
            {
                if (_ord[_i] == _cur)
                    _pos = _i;
            }
            for (var _step = 1; _step < array_length(_ord); _step++)
            {
                var _p = _ord[(((_pos + (_d * _step)) mod array_length(_ord)) + array_length(_ord)) mod array_length(_ord)];
                if (_p == 0)
                    continue;
                var _l2 = kfo_encp_rows(_p);
                if (array_length(_l2) > 0 && kfo_encp_of({ kn: _l2 }) == _p)
                {
                    _n.kn = _l2;
                    _n.open = _l2[0];
                    // DRBR: SENDS follows the boss on stage (ALL BOSSES: every family in the match); the host can change it after
                    _n.skfam = (_p == 4) ? KBR_FAM_ALL : 0;
                    break;
                }
            }
            break;
        case "kw":
            var _w = real(string_digits(_id));
            _n.kw[_w] = clamp(_n.kw[_w] + _d, 0, 9);
            break;
        case "sk":
            var _sid = real(string_digits(_id));
            var _sl = [];
            var _off = false;
            for (var _i = 0; _i < array_length(_n.skoff); _i++)
            {
                if (_n.skoff[_i] == _sid)
                    _off = true;
                else
                    array_push(_sl, _n.skoff[_i]);
            }
            if (!_off)
            {
                array_push(_sl, _sid);
                if (array_length(_sl) >= kbr_skill_count() - 2)
                    return "At least one skill has to stay on (or turn SKILLS off).";
            }
            _n.skoff = _sl;
            break;
        case "open":
            var _pos = 0;
            for (var _i = 0; _i < array_length(_n.kn); _i++)
            {
                if (_n.kn[_i] == _n.open)
                    _pos = _i;
            }
            _n.open = _n.kn[(_pos + array_length(_n.kn) + _d) mod array_length(_n.kn)];
            break;
        case "bool":
        case "mut":
            variable_struct_set(_n, _id, variable_struct_get(_n, _id) ? 0 : 1);
            if (string_copy(_id, 1, 3) == "tgm" && variable_struct_get(_n, _id) == 0)
            {
                var _left = 0;
                for (var _t = 0; _t < 7; _t++)
                    _left += variable_struct_get(_n, "tgm" + string(_t));
                if (_left == 0)
                    return "At least one targeting mode has to stay on.";
            }
            if (_id == "m_giant" && _n.m_giant)
                _n.m_tiny = 0;
            if (_id == "m_tiny" && _n.m_tiny)
                _n.m_giant = 0;
            if ((_id == "m_rapid" || _id == "m_roul" || _id == "m_nmesc") && variable_struct_get(_n, _id))
            {
                _n.m_rapid = (_id == "m_rapid") ? 1 : 0;
                _n.m_roul = (_id == "m_roul") ? 1 : 0;
                _n.m_nmesc = (_id == "m_nmesc") ? 1 : 0;
            }
            break;
        case "enum":
            if (_id == "skfam")
            {
                // DRBR: SENDS steps through the choices this build has, in their order (kbr_sends_modes)
                var _ml = kbr_sends_modes();
                var _mp = 0;
                for (var _i = 0; _i < array_length(_ml); _i++)
                {
                    if (_ml[_i] == _n.skfam)
                        _mp = _i;
                }
                _n.skfam = _ml[(_mp + array_length(_ml) + _d) mod array_length(_ml)];
                break;
            }
            var _cnt = array_length(_e.names);
            variable_struct_set(_n, _id, (variable_struct_get(_n, _id) + _cnt + _d) mod _cnt);
            break;
        default:
            var _v = variable_struct_get(_n, _id) + (_d * _e.st);
            if (_v > _e.hi)
                _v = _e.lo;
            if (_v < _e.lo)
                _v = _e.hi;
            variable_struct_set(_n, _id, _v);
            if (_id == "minp" && _n.minp > _n.maxp)
                _n.maxp = _n.minp;
            if (_id == "maxp" && _n.minp > _n.maxp)
                _n.minp = _n.maxp;
            break;
    }
    _n.pre = "CUSTOM";
    return kfo_set_clean(_n);
}

// ---------- presets ----------
function kfo_presets()
{
    // build 52: seven more (9-15); the first nine keep their places (saved rooms name them)
    // DRBR: 18 GERSON, 19 FLOWERY, 20 SPAMTON, 21 PINK (a boss preset is only listed when its boss is in this build: kfo_preset_ok)
    return ["CLASSIC", "CASUAL", "COMPETITIVE", "HARDCORE", "KNIGHT RUSH", "KAIZO", "CHAOS", "NIGHTMARE", "UNTARGETED",
        "THORN GARDEN", "STORM FRONT", "VIOLET DREAM", "SKILL BRAWL", "ONE HIT", "PARTY", "LAST STAND", "JEVIL", "ALL BOSSES",
        "GERSON", "FLOWERY", "SPAMTON", "PINK"];
}

// DRBR: preset _i can be picked in this build (a boss preset only when its boss is ready - no unfinished boss is offered)
function kfo_preset_ok(_i)
{
    switch (_i)
    {
        case 16: return kbr_fam_ready(KBR_FAM_JEVIL);
        case 18: return kbr_fam_ready(KBR_FAM_GERSON);
        case 19: return kbr_fam_ready(KBR_FAM_FLOWERY);
        case 20: return kbr_fam_ready(KBR_FAM_SPAMTON);
        case 21: return kbr_fam_ready(KBR_FAM_PINK);
    }
    return true;
}

// the name of built-in preset _i
function kfo_preset_name(_i)
{
    var _p = kfo_presets();
    return _p[clamp(floor(_i), 0, array_length(_p) - 1)];
}

function kfo_preset_desc(_i)
{
    switch (_i)
    {
        case 0: return "The default battle royale: every knight,#classic rotation, sudden death after 2 minutes.";
        case 1: return "Easier: 220 HP, slow ramp, more healing, no#hard attacks, a long breath between attacks.";
        case 2: return "Standard rules for serious matches: 150 HP,#normal ramp, no modifiers, ready check on all.";
        case 3: return "Less forgiving: 100 HP, fast ramp, damage#125%, less healing and invincibility.";
        case 4: return "A new knight with every attack, short#entrances, the switches are the show.";
        case 5: return "Kaizo Knight's tight dodging: Kaizo-heavy#weights, fast ramp, hard attacks, 120 HP.";
        case 6: return "Rapid switching and wild modifiers: Bullet#Storm, Hyper Speed, random costs, fast charge.";
        case 7: return "Knightmare more and more often, the Twin#Knight from the start, fast ramp.";
        case 8: return "CLASSIC without TARGETING: every attack#skill hits every rival (before build 48).";
        case 9: return "The Thorn Knight leads and comes most often.#Every hit stings a little more.";
        case 10: return "Elecknight's storm: it opens, it comes back#often, and everything runs at Hyper Speed.";
        case 11: return "The Violet Knight's dream: Violet most of the#time, a slow climb, extra healing.";
        case 12: return "Skills everywhere: half price, half cooldown,#half a bar to start, TP fills fast.";
        case 13: return "One hit and you're OUT. Shields still save#you. No MAX. Pure dodging.";
        case 14: return "A relaxed match with 3 bots: big HP, big#SOULs, lots of healing. Good for friends.";
        case 15: return "60 max HP and sudden death from the start.#Every second counts.";
        case 16: return "JEVIL, the secret boss of Chapter 1: his own#attacks, his carousel - and his to send.";
        case 17: return "Every knight and every boss, at random.#Every family of attacks to send.";
        case 18: return "GERSON, Chapter 4's Hammer of Justice: his#own attacks, the green SOUL - and his to send.";
        case 19: return "FLOWERY, Chapter 5's boss: the ORANGE SOUL,#his friends, GROUP MERCY - and his to send.";
        case 20: return "SPAMTON NEO, Chapter 2's secret boss: the#YELLOW SOUL - shoot! - and his to send.";
        case 21: return "PINK, Chapter 5's secret boss: the PURPLE#SOUL's lanes, her bombs - and hers to send.";
    }
    return "";
}

// build 52: each preset's colour (its knight's for the knight presets; the HUD's own colours for the rest)
function kfo_preset_col(_i)
{
    switch (_i)
    {
        case 0: return c_white;
        case 1: return make_color_rgb(120, 255, 140);
        case 2: return c_yellow;
        case 3: return make_color_rgb(255, 90, 90);
        case 4: return c_orange;
        case 5: return kbr_ok_color(1);
        case 6: return make_color_rgb(255, 110, 230);
        case 7: return kbr_ok_color(5);
        case 8: return c_ltgray;
        case 9: return kbr_ok_color(4);
        case 10: return kbr_ok_color(2);
        case 11: return kbr_ok_color(3);
        case 12: return make_color_rgb(90, 200, 255);
        case 13: return make_color_rgb(255, 60, 60);
        case 14: return make_color_rgb(255, 170, 220);
        case 15: return make_color_rgb(200, 40, 40);
        case 16: return make_color_rgb(200, 140, 255);
        case 17: return make_color_rgb(255, 220, 120);
        case 18: return kbr_fam_col(KBR_FAM_GERSON);
        case 19: return kbr_fam_col(KBR_FAM_FLOWERY);
        case 20: return kbr_fam_col(KBR_FAM_SPAMTON);
        case 21: return kbr_fam_col(KBR_FAM_PINK);
    }
    return c_white;
}

// the colour of a settings struct's preset name (CUSTOM: grey)
function kfo_preset_col_name(_n)
{
    var _p = kfo_presets();
    for (var _i = 0; _i < array_length(_p); _i++)
    {
        if (_p[_i] == _n)
            return kfo_preset_col(_i);
    }
    return c_gray;
}

function kfo_preset_apply(_i)
{
    var _s = kfo_set_default();
    switch (_i)
    {
        case 1:
            _s.mhp = 220;
            _s.ramp = 0;
            _s.maxst = 3;
            _s.hmul = 150;
            _s.dmul = 75;
            _s.hard = 0;
            _s.gap = 30;
            _s.fin = 4;
            _s.bots = 3;
            break;
        case 2:
            _s.ready = 1;
            _s.cdn = 5;
            _s.fin = 2;
            _s.rejoin = 1;
            break;
        case 3:
            _s.mhp = 100;
            _s.ramp = 2;
            _s.dmul = 125;
            _s.hmul = 50;
            _s.ifr = 75;
            _s.gap = 12;
            _s.fin = 1;
            _s.fullheal = 0;
            break;
        case 4:
            _s.rush = 1;
            _s.trans = 24;
            _s.next = 1;
            _s.ramp = 1;
            break;
        case 5:
            _s.kw = kbr_kw_with([2, 9, 3, 3, 3, 2]);
            _s.rush = 5;
            _s.open = 1;
            _s.mhp = 120;
            _s.ramp = 2;
            _s.dmul = 110;
            break;
        case 6:
            _s.rush = 2;
            _s.m_storm = 1;
            _s.m_hyper = 1;
            _s.m_rcost = 1;
            _s.m_fast = 1;
            _s.m_shield = 1;
            _s.ramp = 2;
            break;
        case 7:
            _s.rush = 6;
            _s.kw = kbr_kw_with([3, 3, 3, 3, 3, 4]);
            _s.twin = 1;
            _s.ramp = 2;
            _s.open = kbr_ok_nightmare_id();
            break;
        case 8:
            _s.tg = 0;
            break;
        case 9:
            _s.kw = kbr_kw_with([2, 2, 2, 2, 9, 2]);
            _s.rush = 5;
            _s.open = 4;
            _s.dmul = 115;
            break;
        case 10:
            _s.kw = kbr_kw_with([2, 2, 9, 2, 2, 2]);
            _s.rush = 5;
            _s.open = 2;
            _s.hyper = 1;
            break;
        case 11:
            _s.kw = kbr_kw_with([2, 2, 2, 9, 2, 2]);
            _s.rush = 5;
            _s.open = 3;
            _s.ramp = 0;
            _s.hmul = 125;
            break;
        case 12:
            _s.scost = 50;
            _s.cdm = 50;
            _s.g0 = 50;
            _s.gmul = 150;
            _s.slots = 4;
            break;
        case 13:
            _s.m_ohko = 1;
            _s.fullheal = 0;
            _s.shp = 1;
            break;
        case 14:
            _s.bots = 3;
            _s.botp = 1;
            _s.mhp = 220;
            _s.hmul = 150;
            _s.m_giant = 1;
            _s.ramp = 0;
            break;
        case 15:
            _s.m_lowhp = 1;
            _s.m_sd0 = 1;
            break;
        case 16:
            // build 52: JEVIL - the secret boss alone, his own attacks to send
            var _jl = kfo_encp_rows(2);
            if (array_length(_jl) > 0)
            {
                _s.kn = _jl;
                _s.open = _jl[0];
            }
            _s.skfam = 0;
            _s.ramp = 1;
            break;
        case 17:
            // build 52: ALL BOSSES - the knights and the secret bosses, at random; every family of attacks
            _s.kn = kfo_encp_rows(4);
            _s.rush = 3;
            _s.skfam = 3;
            break;
        case 18:
            // DRBR: GERSON alone (his attacks, his green SOUL), his attacks to send (MATCH CURRENT BOSS)
            var _gl = kfo_encp_rows(6);
            if (array_length(_gl) > 0)
            {
                _s.kn = _gl;
                _s.open = _gl[0];
            }
            _s.skfam = 0;
            _s.ramp = 1;
            break;
        case 19:
            // DRBR: FLOWERY alone: his phases move with the GROUP MERCY and the time (the slow ramp leaves room for MERCY);
            // his attacks to send (MATCH CURRENT BOSS)
            var _fl = kfo_encp_rows(8);
            if (array_length(_fl) > 0)
            {
                _s.kn = _fl;
                _s.open = _fl[0];
            }
            _s.skfam = 0;
            _s.ramp = 0;
            break;
        case 20:
            // DRBR: SPAMTON NEO alone (his attacks, the yellow SOUL), his attacks to send (MATCH CURRENT BOSS)
            var _sl = kfo_encp_rows(5);
            if (array_length(_sl) > 0)
            {
                _s.kn = _sl;
                _s.open = _sl[0];
            }
            _s.skfam = 0;
            _s.ramp = 1;
            break;
        case 21:
            // DRBR: PINK alone (her attacks, the purple SOUL's lanes), her attacks to send (MATCH CURRENT BOSS)
            var _pl = kfo_encp_rows(7);
            if (array_length(_pl) > 0)
            {
                _s.kn = _pl;
                _s.open = _pl[0];
            }
            _s.skfam = 0;
            _s.ramp = 1;
            break;
    }
    _s.pre = kfo_preset_name(clamp(_i, 0, array_length(kfo_presets()) - 1));
    return kfo_set_clean(_s);
}

// the name a settings struct really deserves: a built-in preset's name only while nothing in it was changed
function kfo_set_named(_s)
{
    var _c = kfo_set_clean(_s);
    var _p = kfo_presets();
    for (var _i = 0; _i < array_length(_p); _i++)
    {
        if (_p[_i] == _c.pre)
        {
            var _ref = kfo_preset_apply(_i);
            _ref.pre = _c.pre;
            if (json_stringify(_ref) != json_stringify(_c))
                _c.pre = "CUSTOM";
            return _c;
        }
    }
    return _c;
}

// ---------- export / import (a code to paste: "KF45:" + base64 of the settings JSON) ----------
function kfo_set_to_text(_s)
{
    return "KF45:" + base64_encode(json_stringify(kfo_set_clean(_s)));
}

// undefined when the text is not a settings code
function kfo_set_from_text(_t)
{
    if (!is_string(_t))
        return undefined;
    _t = kfo_trim(_t);
    if (string_pos("KF45:", _t) != 1 || string_length(_t) > 8000)
        return undefined;
    var _b = string_copy(_t, 6, string_length(_t) - 5);
    var _j = "";
    try
    {
        _j = base64_decode(_b);
    }
    catch (_e)
    {
        return undefined;
    }
    var _m = kfo_json_in(_j);
    if (!is_struct(_m))
        return undefined;
    var _s = kfo_set_clean(_m);
    _s.pre = "CUSTOM";
    return _s;
}

// ---------- the player's own presets (3 slots in knightfights_online.ini) ----------
function kfo_custom_save(_slot, _s)
{
    ossafe_ini_open(kfo_ini_file());
    ini_write_string("custom", "slot" + string(_slot), json_stringify(kfo_set_clean(_s)));
    ossafe_ini_close();
    return true;
}

function kfo_custom_load(_slot)
{
    ossafe_ini_open(kfo_ini_file());
    var _t = ini_read_string("custom", "slot" + string(_slot), "");
    ossafe_ini_close();
    if (_t == "")
        return undefined;
    var _m = kfo_json_in(_t);
    if (!is_struct(_m))
        return undefined;
    var _s = kfo_set_clean(_m);
    _s.pre = "CUSTOM " + string(_slot);
    return _s;
}

function kfo_custom_exists(_slot)
{
    ossafe_ini_open(kfo_ini_file());
    var _t = ini_read_string("custom", "slot" + string(_slot), "");
    ossafe_ini_close();
    return _t != "";
}

// a short line of the settings for the lobby (DRBR: the knights and the bosses counted apart)
function kfo_set_summary(_s)
{
    var _nk = 0;
    var _nb = 0;
    for (var _i = 0; _i < array_length(_s.kn); _i++)
    {
        if (is_struct(kbr_ok_enc(_s.kn[_i])))
            _nb++;
        else
            _nk++;
    }
    var _w = "";
    if (_nk > 0)
        _w = string(_nk) + ((_nk == 1) ? " KNIGHT" : " KNIGHTS");
    if (_nb > 0)
        _w += ((_w == "") ? "" : " + ") + string(_nb) + ((_nb == 1) ? " BOSS" : " BOSSES");
    return _w + "  " + kfo_opt_text(kfo_opt_find("rush"), _s) + "  " + string(_s.mhp) + " HP";
}

// DRBR: what roster row _k is, for its row in BOSSES (two lines): who, from where, the SOUL it gives you, whose sends come with it
function kfo_kn_desc(_k)
{
    var _d = kbr_ok_enc(_k);
    if (!is_struct(_d))
        return string_upper(kbr_ok_name(_k)) + ": a Knight of the hub. RED SOUL.#Sends: the KNIGHT family's attacks.";
    var _soul = string_upper(variable_struct_exists(_d, "soul") ? _d.soul : "red");
    var _what = ((variable_struct_exists(_d, "cat") && _d.cat == "secret") ? "secret boss" : "boss");
    var _l1 = string_upper(_d.name) + ": Chapter " + string(_d.chapter) + "'s " + _what + ". " + _soul + " SOUL.";
    if (!kbr_enc_ready(_d))
        return _l1 + "#Not in this copy of the game (its art is missing).";
    return _l1 + "#Sends: the " + kbr_fam_name(_d.fid) + " family's attacks.";
}

function kfo_set_muts_text(_s)
{
    var _m = kfo_mut_ids();
    var _t = "";
    for (var _i = 0; _i < array_length(_m); _i++)
    {
        if (variable_struct_get(_s, _m[_i]))
            _t += ((_t == "") ? "" : ", ") + kfo_mut_name(_m[_i]);
    }
    return _t;
}

function kfo_kn_short_list(_kn, _sep)
{
    var _t = "";
    for (var _i = 0; _i < array_length(_kn); _i++)
        _t += ((_i > 0) ? _sep : "") + kbr_ok_short(_kn[_i]);
    return _t;
}

// the PRESETS page (the last category)
function kfo_cat_pre()
{
    return array_length(kfo_cats()) - 1;
}

// DRBR: the BOSSES presets (build 52's ENCOUNTERS). 0 CUSTOM (the rows set by hand), 1 KNIGHTS (every knight row - the
// Knightmare too), 2 JEVIL, 3 SECRET BOSSES (every secret boss this build has), 4 ALL BOSSES (every row), 5 SPAMTON, 6 GERSON,
// 7 PINK, 8 FLOWERY (a boss family alone). The numbers are only for the menu (the rows themselves are what is saved).
function kfo_encp_name(_p)
{
    var _n = ["CUSTOM", "KNIGHTS", "JEVIL", "SECRET BOSSES", "ALL BOSSES", "SPAMTON", "GERSON", "PINK", "FLOWERY"];
    return _n[clamp(_p, 0, array_length(_n) - 1)];
}

// the order BOSSES steps through
function kfo_encp_order()
{
    return [1, 2, 5, 6, 7, 8, 3, 4, 0];
}

// the encounter rows of BOSSES preset _p, only the ones this build can run
function kfo_encp_rows(_p)
{
    var _l = [];
    var _fam = [0, KBR_FAM_KNIGHT, KBR_FAM_JEVIL, 0, 0, KBR_FAM_SPAMTON, KBR_FAM_GERSON, KBR_FAM_PINK, KBR_FAM_FLOWERY];
    for (var _k = 0; _k < kbr_ok_count(); _k++)
    {
        if (!kbr_ok_valid(_k))
            continue;
        var _en = kbr_ok_enc(_k);
        var _in = false;
        switch (_p)
        {
            case 3: _in = is_struct(_en) && _en.cat == "secret"; break;
            case 4: _in = true; break;
            default:
                if (_p >= 1 && _p < array_length(_fam))
                    _in = kbr_fam_of_ok(_k) == _fam[_p];
                break;
        }
        if (_in)
            array_push(_l, _k);
    }
    return _l;
}

// which preset settings _s are (0 CUSTOM when the rows match none)
function kfo_encp_of(_s)
{
    var _ord = kfo_encp_order();
    for (var _oi = 0; _oi < array_length(_ord); _oi++)
    {
        var _p = _ord[_oi];
        if (_p == 0)
            continue;
        var _l = kfo_encp_rows(_p);
        if (array_length(_l) != array_length(_s.kn) || array_length(_l) == 0)
            continue;
        var _same = true;
        for (var _i = 0; _i < array_length(_l); _i++)
        {
            if (!kfo_set_has_kn(_s, _l[_i]))
                _same = false;
        }
        if (_same)
            return _p;
    }
    return 0;
}
