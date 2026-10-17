
// ===== Build 45: KNIGHT FIGHTS ONLINE - one shared battle royale =====
// Every game runs the same battle: the same Knight, the same attack, at the same moment, from one match TIMELINE that every
// game works out for itself from the host's seed and settings (kbr_tl_*). Each game simulates its own screen (the attacks
// aim at your own SOUL, your hits, your HP, your gauge and skills); the attack's randomness comes from a stream seeded for
// that attack (kbr_random & co. - the attack code calls them instead of random()), so the parts of an attack that are not
// aimed land in the same places for everyone. The host passes the players' states around and only steps in when a game
// falls out of step (wrong attack, clock drift, impossible numbers): see online_host.gml.
// Online knight ids (ok): 0 NORMAL, 1 KAIZO, 2 ELECKNIGHT (Supercharged), 3 VIOLET, 4 THORN, 5 KNIGHTMARE (the Normal
// Knight's own fight, darker and faster). The joke fight (Cyan Knight) has no online id and can never be picked online; it
// stays exactly as it was everywhere else.

// ---------- roster ----------
// build 50: ONE table for the online knights (and, later, the bosses of the other chapters): an online id is its row. To add a
// boss online: add its hub registry entry (knights.json, with its "chapter"), then a row here with its registry key - its
// MATCH SETTINGS rows (in the match or not, weight), the rushes, the HUD names and the colours all follow from the table.
// Rows are only ever ADDED at the end (an id is what a room sends), and every player of a room has the same build (the
// version check on join), so they all have the same table. A row whose registry key is not in this build is never valid.
function kbr_roster()
{
    if (variable_global_exists("kbr_roster_t") && is_array(global.kbr_roster_t))
        return global.kbr_roster_t;
    global.kbr_roster_t = [
        { key: "base", short: "NORMAL", name: "Normal Knight", col: make_color_rgb(150, 190, 255), kw: 3, nm: false },
        { key: "kaizo", short: "KAIZO", name: "Kaizo Knight", col: make_color_rgb(255, 120, 40), kw: 3, nm: false },
        { key: "elec", short: "ELECKNIGHT", name: "Elecknight", col: make_color_rgb(255, 230, 60), kw: 3, nm: false },
        { key: "violet", short: "VIOLET", name: "Violet Knight", col: make_color_rgb(190, 110, 255), kw: 3, nm: false },
        { key: "thorn", short: "THORN", name: "Thorn Knight", col: make_color_rgb(110, 220, 110), kw: 3, nm: false },
        // the Normal Knight's own fight, darker and faster
        { key: "base", short: "KNIGHTMARE", name: "Knightmare", col: make_color_rgb(230, 40, 60), kw: 2, nm: true },
        // (other chapters' bosses go here, after the knights)
        // build 52: the SECRET BOSSES (online_jevil52.gml: kbr_enc_defs) - Jevil, Chapter 1
        { key: "jevil", enc: "jevil", short: "JEVIL", name: "Jevil", col: make_color_rgb(200, 140, 255), kw: 2, nm: false, cat: "secret" },
        // DRBR: Gerson, the Hammer of Justice (Chapter 4; online_gerson53.gml)
        { key: "gerson", enc: "gerson", short: "GERSON", name: "Gerson", col: make_color_rgb(120, 220, 140), kw: 2, nm: false, cat: "secret" },
        // DRBR: Flowery (Chapter 5's boss; online_flowery53.gml)
        { key: "flowery", enc: "flowery", short: "FLOWERY", name: "Flowery", col: make_color_rgb(255, 170, 60), kw: 2, nm: false, cat: "story" },
        // DRBR: Spamton NEO (Chapter 2's secret boss; online_spamton53.gml)
        { key: "spamton", enc: "spamton", short: "NEO", name: "Spamton NEO", col: make_color_rgb(255, 120, 200), kw: 2, nm: false, cat: "secret" },
        // DRBR: Pink (Chapter 5's secret boss; online_pink53.gml)
        { key: "pink", enc: "pink", short: "PINK", name: "Pink", col: make_color_rgb(230, 36, 123), kw: 2, nm: false, cat: "secret" }
    ];
    return global.kbr_roster_t;
}

// the roster as one string (online ids and the registry knights they run, in order): sent on joining a room, so two games
// with different rosters - a boss added on one side only - never share a match even with the same build number
function kbr_roster_sig()
{
    var _s = "";
    for (var _k = 0; _k < kbr_ok_count(); _k++)
        _s += kbr_ok_row(_k).key + (kbr_ok_row(_k).nm ? "!" : "") + (kbr_ok_valid(_k) ? "" : "?") + ";";
    return _s;
}

function kbr_ok_count()
{
    return array_length(kbr_roster());
}

function kbr_ok_row(_ok)
{
    var _r = kbr_roster();
    return _r[clamp(floor(_ok), 0, array_length(_r) - 1)];
}

// the hub registry knight that runs an online knight's attacks (-1: not in this build)
function kbr_reg_of(_ok)
{
    // build 52: a secret boss runs under its lineup id (1000 + n)
    var _en = kbr_ok_enc(_ok);
    if (is_struct(_en))
        return _en.lu;
    var _g = knight_find_key(kbr_ok_row(_ok).key);
    return (_g < 0) ? 0 : _g;
}

function kbr_ok_valid(_ok)
{
    if (!is_numeric(_ok) || _ok != floor(_ok) || _ok < 0 || _ok >= kbr_ok_count())
        return false;
    // build 52: a secret boss is valid when its pieces are in this build
    if (variable_struct_exists(kbr_ok_row(_ok), "enc"))
        return kbr_enc_ready(kbr_ok_enc(_ok));
    var _g = knight_find_key(kbr_ok_row(_ok).key);
    return _g >= 0 && _g < knight_count() && !knight_reg(_g).joke;
}

function kbr_ok_short(_ok)
{
    return kbr_ok_row(_ok).short;
}

function kbr_ok_name(_ok)
{
    return kbr_ok_row(_ok).name;
}

function kbr_ok_color(_ok)
{
    return kbr_ok_row(_ok).col;
}

// the default MATCH SETTINGS weights of every row (RANDOM / WEIGHTED / NIGHTMARE rushes)
function kbr_ok_kw_default()
{
    var _l = [];
    for (var _k = 0; _k < kbr_ok_count(); _k++)
        array_push(_l, kbr_ok_row(_k).kw);
    return _l;
}

// every row that is in this build, in roster order (the default "in the match" list)
function kbr_ok_all()
{
    var _l = [];
    for (var _k = 0; _k < kbr_ok_count(); _k++)
    {
        if (kbr_ok_valid(_k))
            array_push(_l, _k);
    }
    return _l;
}

// a preset's weights for the first rows, the rest from the roster's defaults (a boss added later gets its default)
function kbr_kw_with(_first)
{
    var _l = kbr_ok_kw_default();
    for (var _i = 0; _i < min(array_length(_first), array_length(_l)); _i++)
        _l[_i] = _first[_i];
    return _l;
}

// the darker, faster Normal Knight (Knightmare)
function kbr_nightmare(_ok)
{
    return is_numeric(_ok) && _ok >= 0 && _ok < kbr_ok_count() && kbr_ok_row(_ok).nm;
}

// its online id (the NIGHTMARE rush and its mutator put it in the match)
function kbr_ok_nightmare_id()
{
    for (var _k = 0; _k < kbr_ok_count(); _k++)
    {
        if (kbr_ok_row(_k).nm)
            return _k;
    }
    return 0;
}

// ---------- deterministic numbers (the same in every game) ----------
// Park-Miller (modulus the prime 2^31 - 1, multiplier 48271): every product stays below 2^53, so a GameMaker real holds it
// exactly on every machine.
// (_a * _b) mod 2^31 - 1 for 0 <= _a, _b < 2^31, exact in doubles: _b is split into two 16-bit halves
function kbr_mulmod(_a, _b)
{
    var _m = 2147483647;
    var _hi = floor(_b / 65536);
    var _lo = _b - (_hi * 65536);
    return ((((_a * _hi) mod _m) * 65536) + (_a * _lo)) mod _m;
}

// two numbers -> a seed (1 .. 2^31 - 2). Three squaring rounds make it non-linear, so the seeds of neighbouring cycles
// (k, k + 1) start unrelated streams (a linear mix made the RANDOM / WEIGHTED / NIGHTMARE rushes favour some knights).
function kbr_mix(_a, _b)
{
    var _m = 2147483647;
    var _x = (((abs(floor(_a)) mod _m) * 48271) + 12345) mod _m;
    _x = (_x + kbr_mulmod((abs(floor(_b)) mod _m) + 1, 69621)) mod _m;
    for (var _r = 0; _r < 3; _r++)
    {
        _x = (kbr_mulmod(_x, _x) + 1013904223 + (_r * 7919)) mod _m;
        _x = (_x * 48271) mod _m;
        if (_x <= 0)
            _x = 1;
    }
    return _x;
}

function kbr_rng(_seed)
{
    return { s: kbr_mix(_seed, 1) };
}

function kbr_rng_next(_g)
{
    _g.s = (_g.s * 48271) mod 2147483647;
    return _g.s;
}

// 0 <= x < 1
function kbr_rng_unit(_g)
{
    return (kbr_rng_next(_g) - 1) / 2147483646;
}

// 0 .. _n - 1
function kbr_rng_int(_g, _n)
{
    return min(_n - 1, floor(kbr_rng_unit(_g) * _n));
}

// an index picked with weights (_w: array of numbers >= 0); -1 when every weight is 0
function kbr_rng_weighted(_g, _w)
{
    var _tot = 0;
    for (var _i = 0; _i < array_length(_w); _i++)
        _tot += max(0, _w[_i]);
    if (_tot <= 0)
        return -1;
    var _x = kbr_rng_unit(_g) * _tot;
    for (var _i = 0; _i < array_length(_w); _i++)
    {
        _x -= max(0, _w[_i]);
        if (_x < 0)
            return _i;
    }
    for (var _i = array_length(_w) - 1; _i >= 0; _i--)
    {
        if (_w[_i] > 0)
            return _i;
    }
    return -1;
}

// ---------- the attack stream: what the Knights' attack code uses instead of random() ----------
// Outside an online battle these behave exactly like the built-ins. In one, they draw from the current attack's stream
// (reseeded at every attack's start, so a game that drifted is back in step at the next attack).
global.kbr_det = { on: false, g: { s: 1 }, n: 0 };
// how many times the scheduler had to refuse a knight that is not allowed online (the tests expect 0)
global.kbr_assert_n = 0;

function kbr_det_seed(_seed)
{
    global.kbr_det.g = kbr_rng(_seed);
    global.kbr_det.n = 0;
}

function kbr_det_unit()
{
    // build 50: a player's sent attack draws from its own stream, never the shared one (only the target's game makes it)
    if (global.kbr_san > 0 && variable_instance_exists(id, "kbrg"))
        return kbr_rng_unit(kbrg);
    global.kbr_det.n++;
    return kbr_rng_unit(global.kbr_det.g);
}

function kbr_random(_x)
{
    if (!global.kbr_det.on)
        return random(_x);
    return kbr_det_unit() * _x;
}

function kbr_irandom(_x)
{
    if (!global.kbr_det.on)
        return irandom(_x);
    var _n = floor(_x);
    if (_n <= 0)
        return 0;
    return min(_n, floor(kbr_det_unit() * (_n + 1)));
}

function kbr_random_range(_a, _b)
{
    if (!global.kbr_det.on)
        return random_range(_a, _b);
    return _a + (kbr_det_unit() * (_b - _a));
}

function kbr_irandom_range(_a, _b)
{
    if (!global.kbr_det.on)
        return irandom_range(_a, _b);
    var _lo = min(floor(_a), floor(_b));
    var _hi = max(floor(_a), floor(_b));
    return _lo + min(_hi - _lo, floor(kbr_det_unit() * (_hi - _lo + 1)));
}

function kbr_choose()
{
    if (argument_count <= 0)
        return undefined;
    if (!global.kbr_det.on)
        return argument[irandom(argument_count - 1)];
    return argument[min(argument_count - 1, floor(kbr_det_unit() * argument_count))];
}

function kbr_list_shuffle(_l)
{
    if (!global.kbr_det.on)
    {
        ds_list_shuffle(_l);
        return 0;
    }
    // ds_list_find_value / ds_list_set, never the [| ] accessor: the compiler the mod is built with drops ds accessors and
    // makes them plain array reads ("trying to index a variable which is not an array" in the game - build 45's crash in
    // the rotating slash attack)
    for (var _i = ds_list_size(_l) - 1; _i > 0; _i--)
    {
        var _j = min(_i, floor(kbr_det_unit() * (_i + 1)));
        var _t = ds_list_find_value(_l, _i);
        ds_list_set(_l, _i, ds_list_find_value(_l, _j));
        ds_list_set(_l, _j, _t);
    }
    return 0;
}

// (Chapter 3's GameMaker runtime has no array_shuffle built-in: a shuffled copy, made here both ways - offline from the
// built-in generator, online from the stream. No attack uses it today; it is here for det_rewrite's table.)
function kbr_array_shuffle(_a)
{
    var _o = [];
    array_copy(_o, 0, _a, 0, array_length(_a));
    for (var _i = array_length(_o) - 1; _i > 0; _i--)
    {
        var _j = global.kbr_det.on ? min(_i, floor(kbr_det_unit() * (_i + 1))) : irandom(_i);
        var _t = _o[_i];
        _o[_i] = _o[_j];
        _o[_j] = _t;
    }
    return _o;
}

// the attack code reseeding the built-in generator (a few attacks do it) must not break the stream
function kbr_randomize()
{
    if (!global.kbr_det.on)
        randomize();
    return 0;
}

function kbr_random_set_seed(_s)
{
    if (!global.kbr_det.on)
        random_set_seed(_s);
    return 0;
}

// ---------- the match settings (the host's; every game gets the same copy) ----------
// rush: 0 CLASSIC ROTATION (a knight stays 'stay' attacks), 1 KNIGHT RUSH (a new knight every attack, in order),
// 2 RAPID RUSH (every attack, short transitions), 3 RANDOM RUSH, 4 PROGRESSIVE RUSH (switches come faster as the match
// goes on), 5 WEIGHTED RUSH (knight weights), 6 NIGHTMARE RUSH (Knightmare more and more often)
function kbr_rush_name(_r)
{
    switch (_r)
    {
        case 0: return "CLASSIC ROTATION";
        case 1: return "KNIGHT RUSH";
        case 2: return "RAPID RUSH";
        case 3: return "RANDOM RUSH";
        case 4: return "PROGRESSIVE RUSH";
        case 5: return "WEIGHTED RUSH";
        case 6: return "NIGHTMARE RUSH";
    }
    return "?";
}

// the enabled knights in roster order (never empty, never the joke fight)
function kbr_set_roster(_set)
{
    var _o = [];
    for (var _k = 0; _k < kbr_ok_count(); _k++)
    {
        for (var _i = 0; _i < array_length(_set.kn); _i++)
        {
            if (_set.kn[_i] == _k && kbr_ok_valid(_k))
            {
                array_push(_o, _k);
                break;
            }
        }
    }
    if (array_length(_o) == 0)
        _o = [0];
    return _o;
}

// seconds per stage of the ramp: slow 90, normal 60, fast 40; instant starts at stage 3
function kbr_ramp_secs(_ramp)
{
    switch (_ramp)
    {
        case 0: return 90;
        case 2: return 40;
    }
    return 60;
}

// ---------- the attack catalogue (per hub knight: duration in frames at 30 a second, measured in the emulator) ----------
global.kbr_cat_dur = @@KBRCAT@@;
// every object an online attack can leave behind (measured): the end of an attack takes them all away (kbr_cut)
function kbr_atk_objs()
{
    return @@KBRATKOBJS@@;
}

function kbr_atk_frames(_reg, _ai)
{
    // build 52: a secret boss's attacks run their own turn timer
    var _en = kbr_enc_of_lu(_reg);
    if (is_struct(_en))
        return clamp(_en.tt[clamp(_ai, 0, array_length(_en.tt) - 1)], 60, 1200);
    var _d = 0;
    if (_reg >= 0 && _reg < array_length(global.kbr_cat_dur) && is_array(global.kbr_cat_dur[_reg]) && _ai >= 0 && _ai < array_length(global.kbr_cat_dur[_reg]))
        _d = global.kbr_cat_dur[_reg][_ai];
    if (!is_numeric(_d) || _d < 60)
        _d = 330;
    return min(_d, 1200);
}

// the attacks of hub knight _reg that the timeline may use at stage _st: phase 1 at stage 0, phases 1-2 at stage 1,
// every phase (1-3) from stage 2 (phases 1-2 only when HARD ATTACKS is off); never an unused attack or a finale, never one
// the catalogue could not run
function kbr_atk_pool(_reg, _st, _hard)
{
    var _l = knight_reg(_reg).atk;
    var _maxph = (_st <= 0) ? 1 : ((_st == 1) ? 2 : 3);
    if (!_hard)
        _maxph = min(_maxph, 2);
    var _o = [];
    for (var _i = 0; _i < array_length(_l); _i++)
    {
        if (_l[_i][3] == 0 && _l[_i][0] <= _maxph && kbr_atk_ok(_reg, _i))
            array_push(_o, _i);
    }
    if (array_length(_o) == 0)
    {
        for (var _i = 0; _i < array_length(_l); _i++)
        {
            if (_l[_i][3] == 0 && kbr_atk_ok(_reg, _i))
                array_push(_o, _i);
        }
    }
    if (array_length(_o) == 0)
        _o = [0];
    return _o;
}

// the Roaring: 3 minutes into a match (ticks are 1/30 s)
#macro KBR_ROAR_T 5400

// the index of hub knight _reg's Roaring in its attack list (its finale attack named Roaring), -1 when it has none
function kbr_roar_ai(_reg)
{
    // build 52: a secret boss's finale (Jevil's BYE-BYE)
    var _en = kbr_enc_of_lu(_reg);
    if (is_struct(_en))
        return _en.roar;
    var _l = knight_reg(_reg).atk;
    for (var _i = array_length(_l) - 1; _i >= 0; _i--)
    {
        if ((_l[_i][3] & 2) && string_pos("Roaring", _l[_i][2]) > 0)
            return _i;
    }
    return -1;
}

// how long the Roaring of hub knight _reg runs (frames, measured in the emulator for build 48)
function kbr_roar_frames(_reg)
{
    var _en = kbr_enc_of_lu(_reg);
    if (is_struct(_en))
        return _en.roar_dur;
    var _d = @@ROARDUR@@;
    if (_reg >= 0 && _reg < array_length(_d))
        return _d[_reg];
    return 600;
}

// the attack ran cleanly in the catalogue run (a duration was measured)
function kbr_atk_ok(_reg, _ai)
{
    if (_reg < 0 || _reg >= array_length(global.kbr_cat_dur) || !is_array(global.kbr_cat_dur[_reg]))
        return true;
    if (_ai < 0 || _ai >= array_length(global.kbr_cat_dur[_reg]))
        return false;
    return global.kbr_cat_dur[_reg][_ai] > 0;
}

function kbr_atk_name(_ok, _ai)
{
    var _l = knight_reg(kbr_reg_of(_ok)).atk;
    if (_ai < 0 || _ai >= array_length(_l))
        return "?";
    return _l[_ai][2];
}

// ---------- the timeline ----------
// A match is a run of attack CYCLES. Cycle k: { k, ok (online knight), reg (hub knight), ai (attack in its list), seed,
// t0 (the tick its attack starts - ticks are 1/30 s since the match's tick 0), dur, t1 (it is over by then), st (stage),
// sw (the knight changed), tr (its entrance before the attack), twin / hyper (the Twin Knight layer, Hyper speed), ft (final
// two), sd (sudden death), nm (Knightmare) }. Everything comes from the match seed, the settings (kbr_eff) and the one event
// the host announces (the final two, from cycle ft), so every game gets the same cycles, whatever happens on its screen.
function kbr_tl_new(_seed, _set)
{
    var _e = kbr_eff(_set);
    // flph: the host's GROUP MERCY announcements for a boss whose phases move with it (Flowery: [cycle, phase], online_flowery53.gml)
    return { seed: _seed, set: _e, cyc: [], ft: -1, flph: [], sd_t: kbr_sd_tick(_e), intro: kbr_tl_intro(_e) };
}

// the tick sudden death starts at (-1: never)
function kbr_sd_tick(_e)
{
    if (!_e.sd)
        return -1;
    if (_e.sd0)
        return 0;
    var _to4 = (_e.ramp == 3) ? 0 : (kbr_ramp_secs(_e.ramp) * max(0, _e.maxst));
    return kbr_tl_intro(_e) + ((_to4 + (max(1, _e.fin) * 60)) * 30);
}

// the tick the first sudden-death attack starts at (-1: never). Sudden death goes on with the first cycle that starts after
// sd_t; its max HP loss counts from that cycle's start in every game (and in the host's check of the numbers)
function kbr_tl_sd_t0(_tl)
{
    if (_tl.sd_t < 0)
        return -1;
    var _k = kbr_tl_at(_tl, _tl.sd_t);
    for (var _j = max(0, _k - 1); _j < _k + 4; _j++)
    {
        var _c = kbr_tl_get(_tl, _j);
        if (_c.sd)
            return _c.t0;
    }
    return _tl.sd_t;
}

// the countdown before the first attack
function kbr_tl_intro(_e)
{
    return clamp(_e.cdn, 3, 10) * 30;
}

function kbr_tl_stage(_tl, _t0)
{
    var _set = _tl.set;
    var _st = (_set.ramp == 3) ? 3 : floor(max(0, _t0 - _tl.intro) / (kbr_ramp_secs(_set.ramp) * 30));
    return clamp(min(_st, _set.maxst), 0, 4);
}

// how many attacks a knight stays for (classic, progressive, faster over time)
function kbr_tl_stay(_tl, _t0)
{
    var _set = _tl.set;
    var _stay = clamp(_set.stay, 1, 8);
    if (_set.rush == 4 || _set.speedup)
        _stay = max(1, _stay - floor(max(0, _t0 - _tl.intro) / (45 * 30)));
    return _stay;
}

function kbr_tl_weights(_tl, _ros, _t0, _st)
{
    var _set = _tl.set;
    var _w = [];
    for (var _i = 0; _i < array_length(_ros); _i++)
    {
        var _k = _ros[_i];
        // (a weight list shorter than the roster - an older preset: the row's own default)
        var _x = clamp((_k < array_length(_set.kw)) ? _set.kw[_k] : kbr_ok_row(_k).kw, 0, 9);
        if (_set.rush == 6 && kbr_nightmare(_k))
            _x = max(_x, 1) * (1 + (_st * 2) + floor(max(0, _t0 - _tl.intro) / (30 * 30)));
        array_push(_w, _x);
    }
    return _w;
}

// the switching mode in force at tick _t0 (sudden death speeds the rush up when the room wants it)
function kbr_tl_rush(_tl, _t0)
{
    var _set = _tl.set;
    if (_set.sdfast && _tl.sd_t >= 0 && _t0 >= _tl.sd_t && (_set.rush == 0 || _set.rush == 4))
        return 1;
    return _set.rush;
}

// the knight of cycle _k (needs cycle _k - 1)
function kbr_tl_pick_knight(_tl, _k, _g, _t0, _st)
{
    var _set = _tl.set;
    var _ros = kbr_set_roster(_set);
    var _n = array_length(_ros);
    if (_k == 0)
    {
        for (var _i = 0; _i < _n; _i++)
        {
            if (_ros[_i] == _set.open)
                return _set.open;
        }
        return _ros[0];
    }
    var _prev = _tl.cyc[_k - 1];
    if (_n == 1)
        return _ros[0];
    // how long the knight in front has stayed
    var _run = 0;
    for (var _j = _k - 1; _j >= 0; _j--)
    {
        if (_tl.cyc[_j].ok != _prev.ok)
            break;
        _run++;
    }
    var _pos = 0;
    for (var _i = 0; _i < _n; _i++)
    {
        if (_ros[_i] == _prev.ok)
            _pos = _i;
    }
    var _next_in_order = _ros[(_pos + 1) mod _n];
    var _rush = kbr_tl_rush(_tl, _t0);
    switch (_rush)
    {
        case 0:
        case 4:
            if (_run < kbr_tl_stay(_tl, _t0))
                return _prev.ok;
            return _next_in_order;
        case 1:
        case 2:
            return _next_in_order;
    }
    // 3 RANDOM, 5 WEIGHTED, 6 NIGHTMARE: a weighted draw
    var _w = kbr_tl_weights(_tl, _ros, _t0, _st);
    if (_rush == 3)
    {
        for (var _i = 0; _i < _n; _i++)
            _w[_i] = 1;
    }
    var _blocked = [];
    if (!_set.rep)
        array_push(_blocked, _prev.ok);
    // RECENT BLOCK: the last N different knights sit out (when enough knights are left to pick from)
    var _rb = min(_set.recent, _n - 1);
    for (var _j = _k - 1; _j >= 0 && array_length(_blocked) < max(_rb, _set.rep ? 0 : 1); _j--)
    {
        var _seen = false;
        for (var _b = 0; _b < array_length(_blocked); _b++)
        {
            if (_blocked[_b] == _tl.cyc[_j].ok)
                _seen = true;
        }
        if (!_seen)
            array_push(_blocked, _tl.cyc[_j].ok);
    }
    var _w2 = [];
    var _any = false;
    for (var _i = 0; _i < _n; _i++)
    {
        var _x = _w[_i];
        for (var _b = 0; _b < array_length(_blocked); _b++)
        {
            if (_blocked[_b] == _ros[_i])
                _x = 0;
        }
        if (_x > 0)
            _any = true;
        array_push(_w2, _x);
    }
    if (!_any)
        _w2 = _w;
    var _x = kbr_rng_weighted(_g, _w2);
    return (_x < 0) ? _next_in_order : _ros[_x];
}

// the attack of cycle _k for knight _ok: from its pool for the stage, never one of the last few this knight used
function kbr_tl_pick_attack(_tl, _k, _g, _ok, _st)
{
    var _set = _tl.set;
    var _reg = kbr_reg_of(_ok);
    var _pool = kbr_atk_pool(_reg, _st, _set.hard);
    // DRBR: an encounter with its own pool (Flowery: the attacks of his phase - the friends on stage have their own)
    var _en = kbr_enc_of_lu(_reg);
    if (is_struct(_en) && variable_struct_exists(_en, "pool"))
        _pool = script_execute(_en.pool, _tl, _k, _st, _set.hard);
    var _n = array_length(_pool);
    // stage 0 of a classic match plays the opening knight's own fight in its own order
    if (_st == 0 && _ok == _set.open && _set.rush == 0 && !_set.overlap)
    {
        var _own = 0;
        for (var _j = 0; _j < _k; _j++)
        {
            if (_tl.cyc[_j].ok == _ok)
                _own++;
        }
        return _pool[_own mod _n];
    }
    var _recent = [];
    var _keep = min(_set.arep, _n - 1);
    for (var _j = _k - 1; _j >= 0 && array_length(_recent) < _keep; _j--)
    {
        if (kbr_reg_of(_tl.cyc[_j].ok) == _reg)
            array_push(_recent, _tl.cyc[_j].ai);
    }
    var _cand = [];
    for (var _i = 0; _i < _n; _i++)
    {
        var _used = false;
        for (var _j = 0; _j < array_length(_recent); _j++)
        {
            if (_recent[_j] == _pool[_i])
                _used = true;
        }
        if (!_used)
            array_push(_cand, _pool[_i]);
    }
    if (array_length(_cand) == 0)
        _cand = _pool;
    return _cand[kbr_rng_int(_g, array_length(_cand))];
}

function kbr_tl_make(_tl, _k)
{
    var _set = _tl.set;
    var _g = kbr_rng(kbr_mix(_tl.seed, (_k * 7) + 3));
    var _t0;
    if (_k == 0)
        _t0 = _tl.intro;
    else
        _t0 = _tl.cyc[_k - 1].t1;
    var _b0 = _t0;
    // the final two has started (cycle _tl.ft on): its showdown (stage, Twin, Hyper, music) only with the FINAL TWO setting on;
    // the Roaring that opens it always
    var _lms = (_tl.ft >= 0 && _k >= _tl.ft);
    var _ft = _lms && _set.ft;
    var _sd = (_tl.sd_t >= 0 && _t0 >= _tl.sd_t);
    var _st = kbr_tl_stage(_tl, _t0);
    if (_ft && _set.maxst >= 3)
        _st = max(_st, 3);
    var _ok = kbr_tl_pick_knight(_tl, _k, _g, _t0, _st);
    // the scheduler's own check: an online cycle never runs the joke fight (the Cyan Knight) or anything off the roster
    if (!kbr_ok_valid(_ok) || knight_reg(kbr_reg_of(_ok)).joke)
    {
        global.kbr_assert_n++;
        _ok = 0;
    }
    var _nm = kbr_nightmare(_ok);
    var _sw = (_k > 0 && _ok != _tl.cyc[_k - 1].ok);
    // the breath between two attacks, and the knight's entrance when it changes
    var _gap = (_k == 0) ? 0 : clamp(_set.gap, 0, 30);
    var _tr = 0;
    if (_sw)
    {
        _tr = clamp(_set.trans, 0, 90);
        if (_set.rush == 2 || _ft || _sd)
            _tr = min(_tr, 14);
    }
    _t0 += _gap + _tr;
    // the attack pool: every phase in sudden death and with EXTREME OVERLAP
    var _pst = (_sd || _set.overlap) ? 3 : _st;
    var _ai = kbr_tl_pick_attack(_tl, _k, _g, _ok, _pst);
    // build 48: the Roaring. Whichever knight has the cycle uses its own Roaring (the finale attack) on the first cycle of the
    // final two, and on the first cycle that starts once the match has gone on for 3 minutes
    var _roar = false;
    var _ra = kbr_roar_ai(kbr_reg_of(_ok));
    if (_ra >= 0)
    {
        var _th = _tl.intro + KBR_ROAR_T;
        if (_lms && _k == _tl.ft)
            _roar = true;
        if (_b0 >= _th && (_k == 0 || _tl.cyc[_k - 1].b0 < _th))
            _roar = true;
    }
    // DRBR: an encounter's own finale rule (Flowery: the first of his cycles once the GROUP MERCY finished Susie's Idea)
    if (!_roar && _ra >= 0)
    {
        var _en = kbr_enc_of_lu(kbr_reg_of(_ok));
        if (is_struct(_en) && variable_struct_exists(_en, "finale") && script_execute(_en.finale, _tl, _k))
            _roar = true;
    }
    if (_roar)
        _ai = _ra;
    var _twin = (_set.twin == 1) || (_set.twin == 0 && _st >= 3) || _nm || (_ft && _set.twin != 2);
    // the Roaring is the knight's alone: no Twin Knight layer over it (build 52: nor over a secret boss - the Twin Knight is
    // a Roaring Knight's, standing at the knight's place)
    if (_roar || kbr_reg_of(_ok) >= KBR_ENC_BASE)
        _twin = false;
    var _hyper = (_set.hyper == 1) || (_set.hyper == 0 && _st >= 4) || _nm || (_ft && _set.fthyper);
    var _dur = _roar ? kbr_roar_frames(kbr_reg_of(_ok)) : kbr_atk_frames(kbr_reg_of(_ok), _ai);
    // Hyper speed runs the battle at 38 frames a second: the attack takes less real time
    if (_hyper)
        _dur = ceil((_dur * 30) / 38);
    var _c = { k: _k, ok: _ok, reg: kbr_reg_of(_ok), ai: _ai, seed: kbr_mix(_tl.seed, (_k * 13) + 5), t0: _t0, dur: _dur, t1: _t0 + _dur,
        st: _st, sw: _sw, tr: _tr, ft: _ft, sd: _sd, nm: _nm, twin: _twin, hyper: _hyper, roar: _roar, b0: _b0 };
    return _c;
}

// cycle _k (made, with every cycle before it, on first use)
function kbr_tl_get(_tl, _k)
{
    while (array_length(_tl.cyc) <= _k)
        array_push(_tl.cyc, kbr_tl_make(_tl, array_length(_tl.cyc)));
    return _tl.cyc[_k];
}

// the first cycle whose attack has not ended by tick _t
function kbr_tl_at(_tl, _t)
{
    var _k = 0;
    // binary search over the cycles made so far, then make more as needed
    var _n = array_length(_tl.cyc);
    if (_n > 0 && _tl.cyc[_n - 1].t1 > _t)
    {
        var _lo = 0;
        var _hi = _n - 1;
        while (_lo < _hi)
        {
            var _mid = (_lo + _hi) div 2;
            if (_tl.cyc[_mid].t1 > _t)
                _hi = _mid;
            else
                _lo = _mid + 1;
        }
        return _lo;
    }
    _k = max(0, _n - 1);
    while (_k < 100000)
    {
        var _c = kbr_tl_get(_tl, _k);
        if (_c.t1 > _t)
            return _k;
        _k++;
    }
    return _k;
}

// the host announced the final two from cycle _k: cycles from _k on are made again with it
function kbr_tl_set_ft(_tl, _k)
{
    if (_tl.ft >= 0 && _tl.ft <= _k)
        return 0;
    _tl.ft = _k;
    if (array_length(_tl.cyc) > _k)
        array_resize(_tl.cyc, _k);
    return 1;
}

// DRBR: the host announced phase _ph (GROUP MERCY) from cycle _k: cycles from _k on are made again with it. Each phase is
// announced once (a second announcement of the same phase is ignored); false when nothing changed
function kbr_tl_set_flph(_tl, _k, _ph)
{
    if (!variable_struct_exists(_tl, "flph"))
        _tl.flph = [];
    if (!is_numeric(_k) || !is_numeric(_ph) || _k < 0 || _ph < 1 || _ph > 9)
        return false;
    for (var _i = 0; _i < array_length(_tl.flph); _i++)
    {
        if (_tl.flph[_i][1] == _ph)
            return false;
    }
    array_push(_tl.flph, [floor(_k), floor(_ph)]);
    if (array_length(_tl.cyc) > _k)
        array_resize(_tl.cyc, _k);
    return true;
}

// the announcements as a message carries them ([[cycle, phase], ...])
function kbr_tl_flph_list(_tl)
{
    var _o = [];
    if (is_struct(_tl) && variable_struct_exists(_tl, "flph"))
    {
        for (var _i = 0; _i < array_length(_tl.flph); _i++)
            array_push(_o, [_tl.flph[_i][0], _tl.flph[_i][1]]);
    }
    return _o;
}

// a message's announcements into timeline _tl (numbers only); the first cycle that changed (-1: none)
function kbr_tl_flph_load(_tl, _l)
{
    var _first = -1;
    if (!is_array(_l))
        return -1;
    for (var _i = 0; _i < array_length(_l) && _i < 12; _i++)
    {
        var _e = _l[_i];
        if (!is_array(_e) || array_length(_e) < 2 || !is_numeric(_e[0]) || !is_numeric(_e[1]))
            continue;
        if (kbr_tl_set_flph(_tl, _e[0], _e[1]))
            _first = (_first < 0) ? floor(_e[0]) : min(_first, floor(_e[0]));
    }
    return _first;
}

// a short text that pins a cycle (the host compares it to catch a game that fell out of step)
function kbr_tl_sig(_c)
{
    return string(_c.k) + ":" + string(_c.ok) + ":" + string(_c.ai) + ":" + string(_c.seed) + ":" + string(_c.t0) + ":" + string(_c.st)
        + (_c.twin ? "T" : "") + (_c.hyper ? "H" : "") + (_c.ft ? "F" : "") + (_c.sd ? "S" : "") + (_c.roar ? "R" : "");
}

// how many Twin Knight cycles came before cycle _k (the Twin Knight gets harder with them, the same in every game)
function kbr_tl_twin_n(_tl, _k)
{
    var _n = 0;
    for (var _j = 0; _j < _k && _j < array_length(_tl.cyc); _j++)
    {
        if (_tl.cyc[_j].twin)
            _n++;
    }
    return _n;
}

// build 48: the Supercharged Knight's Roaring starts its extra phase 5 offline only (online the Roaring is one cycle)
function kbr_phase5_ok()
{
    return !kbr_on();
}
