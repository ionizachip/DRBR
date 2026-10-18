// ===== Build 48: TARGETING (the Tetris 99 way) =====
// Every player has one TARGETING MODE (the command row under the box). It only decides where your attack skills go: the
// skills themselves (Sword, Flurry, the mid-pool ones, Knightmare) are unchanged.
//   CHAOS    a random player still standing, a new one after every send (the default)
//   PROCEED  the player with the least HP
//   BIG SHOT the player with the most shards
//   DEFEND   everyone targeting you, the send split evenly between them (nobody targeting you: CHAOS)
//   CHECK    the player you picked (1-8: the slot in the player list, A: the next one, the right stick)
//   PACIFY   the players who are TIRED (healed in the last 4 s, or an empty gauge), split evenly (none TIRED: CHAOS)
//   ROARING  every other player at once, at reduced strength
// The host decides who is targeted (kfo_host_tg_tick, 4 times a second and at every send) and gives the knockout credit;
// every game draws what the host sent (the "st" standings carry each player's mode, targets, shards and TIRED flag).
// A sent attack starts around its target's SOUL (in every game: the target's own SOUL in the target's game, where the host
// last saw it everywhere else) and aimed swords aim at that SOUL, but its bullets hurt anyone who touches them - except the
// sender. They are tinted in the sender's colour (the colour square of the player list).
// The room's TARGETING page turns it all off (TARGETING OFF: every attack skill at every rival, as before build 48 - also the
// UNTARGETED preset), each mode on or off, SHARDS and OUTNUMBERED BONUS.

// ---------- balance: every number in one place ----------
function kbr_tg_bal()
{
    if (variable_global_exists("kbr_tg_bal_c") && is_struct(global.kbr_tg_bal_c))
        return global.kbr_tg_bal_c;
    global.kbr_tg_bal_c = {
        // SHARDS: the strength of your sends goes up a step at 2, 4, 8 and 16 shards
        shard_at: [0, 2, 4, 8, 16],
        shard_mul: [1.0, 1.15, 1.3, 1.5, 1.75],
        // a knockout: 1 shard, plus half of the fallen player's shards (rounded down)
        ko_shard: 1,
        ko_steal: 0.5,
        // ROARING: the send on each player, as a part of a single send
        roar_mul: 0.5,
        // DEFEND / PACIFY on several players: each gets 1/n of the send, never less than this
        split_min: 0.4,
        // OUTNUMBERED BONUS: your gauge fills this much faster for each player targeting you, up to outn_max
        outn_per: 0.25,
        outn_max: 1.0,
        // TIRED: for this long after a heal, or while the gauge is under tired_g
        tired_ms: 4000,
        tired_g: 1,
        // the callout ("* Susie's gaze sharpens on you."): a player targeting you with at least this much charge, at
        // most once per player this often
        call_g: 80,
        call_ms: 8000,
        // SLOW / CONFUSE sent with more strength last longer (never more than this many times)
        fx_max: 1.5
    };
    return global.kbr_tg_bal_c;
}

// ---------- the modes ----------
#macro KBR_TG_CHAOS 0
#macro KBR_TG_PROCEED 1
#macro KBR_TG_BIG 2
#macro KBR_TG_DEFEND 3
#macro KBR_TG_CHECK 4
#macro KBR_TG_PACIFY 5
#macro KBR_TG_ROAR 6

function kbr_tg_count()
{
    return 7;
}

function kbr_tg_name(_m)
{
    switch (_m)
    {
        // build 51: plain names (the modes and their ids 0-6 are unchanged; build 50 said CHAOS, PROCEED, BIG SHOT, DEFEND,
        // CHECK, PACIFY, ROARING)
        case 0: return "RANDOM";
        case 1: return "LOW HP";
        case 2: return "CRYSTALS";
        case 3: return "REVENGE";
        case 4: return "CHOOSE";
        case 5: return "TIRED";
        case 6: return "EVERYONE";
    }
    return "?";
}

function kbr_tg_desc(_m)
{
    switch (_m)
    {
        case 0: return "* A random player. New one after every send.";
        case 1: return "* Whoever has the least HP.";
        case 2: return "* Whoever has the most Shadow Crystals.";
        case 3: return "* Everyone targeting you. Nobody? Random.";
        case 4: return "* The player you pick.";
        case 5: return "* Players who just healed or have no charge.";
        case 6: return "* Everyone at once, at half strength.";
    }
    return "";
}

// targeting is on in the settings _e (effective or plain)
function kbr_tg_on(_e)
{
    return is_struct(_e) && variable_struct_exists(_e, "tg") && _e.tg == 1;
}

function kbr_tg_mode_ok(_e, _m)
{
    if (!is_struct(_e) || !is_numeric(_m) || _m < 0 || _m >= kbr_tg_count())
        return false;
    var _f = "tgm" + string(_m);
    return !variable_struct_exists(_e, _f) || variable_struct_get(_e, _f) == 1;
}

// mode _m, or the first mode the room allows (CHAOS first)
function kbr_tg_mode_fix(_e, _m)
{
    if (kbr_tg_mode_ok(_e, _m))
        return _m;
    for (var _i = 0; _i < kbr_tg_count(); _i++)
    {
        if (kbr_tg_mode_ok(_e, _i))
            return _i;
    }
    return 0;
}

// the next allowed mode from _m in direction _d
function kbr_tg_mode_step(_e, _m, _d)
{
    var _n = kbr_tg_count();
    var _x = _m;
    for (var _i = 0; _i < _n; _i++)
    {
        _x = (_x + _d + _n) mod _n;
        if (kbr_tg_mode_ok(_e, _x))
            return _x;
    }
    return _m;
}

// the strength step of _sh shards (0-4) and its multiplier
function kbr_tg_shard_step(_sh)
{
    var _B = kbr_tg_bal();
    var _s = 0;
    for (var _i = 0; _i < array_length(_B.shard_at); _i++)
    {
        if (_sh >= _B.shard_at[_i])
            _s = _i;
    }
    return _s;
}

function kbr_tg_shard_mul(_sh)
{
    var _B = kbr_tg_bal();
    return _B.shard_mul[kbr_tg_shard_step(_sh)];
}

function kbr_tg_has(_a, _v)
{
    if (!is_array(_a))
        return false;
    for (var _i = 0; _i < array_length(_a); _i++)
    {
        if (_a[_i] == _v)
            return true;
    }
    return false;
}

// the strength of each part of a send in mode _m with _n targets (the shards come on top)
function kbr_tg_part(_m, _n)
{
    var _B = kbr_tg_bal();
    if (_m == KBR_TG_ROAR)
        return _B.roar_mul;
    if (_n > 1)
        return max(_B.split_min, 1 / _n);
    return 1;
}

// ---------- the host: who targets whom ----------
function kfo_host_tg_reset(_p)
{
    _p.tm = 0;
    _p.tmx = 0;
    _p.tpk = -1;
    _p.tg = [];
    _p.tc = -1;
    _p.tcl = -1;
    _p.sh = 0;
    _p.t_heal = -100000;
    _p.lby = -1;
    _p.kos = 0;
    return _p;
}

// a player's message { k: "tg", m: mode, pk: picked pid }
function kfo_host_on_tg(_p, _m)
{
    var _h = global.kfo.H;
    var _md = kfo_jn(_m, "m", 0);
    if (!is_numeric(_md) || _md != floor(_md) || _md < 0 || _md >= kbr_tg_count())
        return false;
    var _pk = kfo_jn(_m, "pk", -1);
    if (!is_numeric(_pk))
        _pk = -1;
    var _ch = (_p.tm != _md || _p.tpk != _pk);
    _p.tm = _md;
    _p.tpk = _pk;
    if (_ch)
    {
        kfo_host_tg_resolve(_p);
        _h.ds = true;
    }
    return true;
}

// the players _p could target now (in the match, standing, not _p)
function kfo_host_tg_cands(_p)
{
    var _h = global.kfo.H;
    var _l = [];
    for (var _i = 0; _i < array_length(_h.pl); _i++)
    {
        var _t = _h.pl[_i];
        if (_t.inm && _t.al && _t.pid != _p.pid)
            array_push(_l, _t);
    }
    return _l;
}

function kfo_host_tg_tired(_t)
{
    var _B = kbr_tg_bal();
    return (current_time - _t.t_heal < _B.tired_ms) || (_t.g < _B.tired_g);
}

// CHAOS: the one picked before while it still stands, else a new one (not the last one when there is a choice)
function kfo_host_tg_chaos(_p, _c)
{
    var _n = array_length(_c);
    if (_n == 0)
        return [];
    for (var _i = 0; _i < _n; _i++)
    {
        if (_c[_i].pid == _p.tc)
            return [_p.tc];
    }
    var _pick = _c[irandom(_n - 1)];
    if (_n > 1 && _pick.pid == _p.tcl)
    {
        var _k = 0;
        for (var _i = 0; _i < _n; _i++)
        {
            if (_c[_i].pid == _p.tcl)
                _k = _i;
        }
        _pick = _c[(_k + 1 + irandom(_n - 2)) mod _n];
    }
    _p.tc = _pick.pid;
    return [_p.tc];
}

// works out _p's targets for its mode (the mode the room allows; fallbacks as the modes say). Sets _p.tg and _p.tmx.
function kfo_host_tg_resolve(_p)
{
    var _h = global.kfo.H;
    var _e = _h.eff;
    var _old = _p.tg;
    var _c = kfo_host_tg_cands(_p);
    var _m = kbr_tg_mode_fix(_e, _p.tm);
    var _tg = [];
    var _n = array_length(_c);
    if (_n > 0)
    {
        switch (_m)
        {
            case KBR_TG_PROCEED:
                var _best = _c[0];
                for (var _i = 1; _i < _n; _i++)
                {
                    if (_c[_i].hp < _best.hp || (_c[_i].hp == _best.hp && _c[_i].pid < _best.pid))
                        _best = _c[_i];
                }
                _tg = [_best.pid];
                break;
            case KBR_TG_BIG:
                var _big = _c[0];
                for (var _i = 1; _i < _n; _i++)
                {
                    if (_c[_i].sh > _big.sh || (_c[_i].sh == _big.sh && _c[_i].hp > _big.hp))
                        _big = _c[_i];
                }
                _tg = [_big.pid];
                break;
            case KBR_TG_DEFEND:
                for (var _i = 0; _i < _n; _i++)
                {
                    if (kbr_tg_has(_c[_i].tg, _p.pid))
                        array_push(_tg, _c[_i].pid);
                }
                break;
            case KBR_TG_CHECK:
                for (var _i = 0; _i < _n; _i++)
                {
                    if (_c[_i].pid == _p.tpk)
                        _tg = [_p.tpk];
                }
                // the picked one fell or left (or none picked yet): the next one standing in the player list's order
                if (array_length(_tg) == 0)
                {
                    var _after = -1;
                    var _first = -1;
                    var _seen = false;
                    for (var _i = 0; _i < array_length(_h.pl); _i++)
                    {
                        var _q = _h.pl[_i];
                        if (_q.pid == _p.tpk)
                            _seen = true;
                        if (!(_q.inm && _q.al && _q.pid != _p.pid))
                            continue;
                        if (_first < 0)
                            _first = _q.pid;
                        if (_seen && _after < 0)
                            _after = _q.pid;
                    }
                    var _np = (_after >= 0) ? _after : _first;
                    if (_np >= 0)
                    {
                        _tg = [_np];
                        _p.tpk = _np;
                    }
                }
                break;
            case KBR_TG_PACIFY:
                for (var _i = 0; _i < _n; _i++)
                {
                    if (kfo_host_tg_tired(_c[_i]))
                        array_push(_tg, _c[_i].pid);
                }
                break;
            case KBR_TG_ROAR:
                for (var _i = 0; _i < _n; _i++)
                    array_push(_tg, _c[_i].pid);
                break;
        }
        // CHAOS, and DEFEND / PACIFY with nobody to go for
        if (array_length(_tg) == 0)
            _tg = kfo_host_tg_chaos(_p, _c);
        else if (_m != KBR_TG_CHAOS)
            _p.tc = -1;
    }
    _p.tmx = _m;
    _p.tg = _tg;
    var _same = (array_length(_old) == array_length(_tg));
    for (var _i = 0; _same && _i < array_length(_tg); _i++)
    {
        if (_old[_i] != _tg[_i])
            _same = false;
    }
    if (!_same)
        _h.ds = true;
    return _tg;
}

// 10 times a second: everyone's targets (a target that fell or left is replaced at once, DEFEND follows who targets you)
function kfo_host_tg_tick()
{
    var _h = global.kfo.H;
    if (!is_struct(_h) || _h.st != "match" || !kbr_tg_on(_h.eff))
        return 0;
    if (!variable_struct_exists(_h, "t_tg"))
        _h.t_tg = 0;
    if (current_time - _h.t_tg < 100)
        return 0;
    _h.t_tg = current_time;
    // DEFEND last: it goes by the others' targets
    for (var _pass = 0; _pass < 2; _pass++)
    {
        for (var _i = 0; _i < array_length(_h.pl); _i++)
        {
            var _p = _h.pl[_i];
            if (!_p.inm)
                continue;
            if (!_p.al)
            {
                if (array_length(_p.tg) > 0)
                {
                    _p.tg = [];
                    _h.ds = true;
                }
                continue;
            }
            var _def = (kbr_tg_mode_fix(_h.eff, _p.tm) == KBR_TG_DEFEND);
            if ((_pass == 0) != _def)
                kfo_host_tg_resolve(_p);
        }
    }
    return 1;
}

// an attack skill in a targeted room: to the targets of the sender (the strength of each part from the mode and the
// sender's shards). Every game in the room gets it (each starts the patterns around the targets; the bullets hurt anyone).
function kfo_host_tg_send(_p, _id, _seq)
{
    var _h = global.kfo.H;
    var _e = _h.eff;
    var _tg0 = kfo_host_tg_resolve(_p);
    var _n = array_length(_tg0);
    if (_n == 0)
    {
        kfo_host_feed("* " + _p.n + " sent " + kbr_skill_name(_id) + ". Nobody to hit.", c_gray);
        return 0;
    }
    var _part = kbr_tg_part(_p.tmx, _n) * kbr_tg_shard_mul(_e.shards ? _p.sh : 0);
    var _tg = [];
    var _tm = [];
    var _names = "";
    for (var _i = 0; _i < _n; _i++)
    {
        var _t = kfo_host_player(_tg0[_i]);
        if (is_undefined(_t))
            continue;
        var _to = _t.pid;
        // Reflection: the part for a reflecting player goes back to the sender
        var _refl = (((_t.sk & 4) != 0) || (current_time - _t.t_rf < ((_e.rsec + 1) * 1000)));
        if (_refl)
        {
            _to = _p.pid;
            kfo_host_feed("* " + _t.n + " reflected " + kbr_skill_name(_id) + " at " + _p.n + ".", make_color_rgb(90, 160, 255));
        }
        else
            _t.sr++;
        array_push(_tg, _to);
        array_push(_tm, round(_part * 100) / 100);
        if (_i < 2)
            _names += ((_i > 0) ? " and " : "") + _t.n;
        // a bot hit while the host's own battle is not running: the old flat hit
        if (_t.bot && !kbr_on())
            kfo_bot_skill_hit(_t, _id, _p);
    }
    var _sd = 1 + irandom(2147483000);
    kfo_down(0, { k: "ska", mid: _h.mid, from: _p.pid, fname: _p.n, sid: _id, seq: _seq, sd: _sd, rf: 0, tg: _tg, tm: _tm, sh: _p.sh });
    kfo_host_su(_p, _id, _tg);
    if (_n > 2)
        _names = string(_n) + " SOULs";
    // build 51: one short line per send (the sender's and the targets' games no longer add their own copies of it)
    kfo_host_feed("* " + _p.n + " sent " + kbr_skill_name(_id) + " to " + _names + ".", c_yellow);
    // CHAOS: a new target after every send
    if (_p.tmx == KBR_TG_CHAOS || (array_length(_p.tg) == 1 && _p.tc >= 0))
    {
        _p.tcl = _p.tc;
        _p.tc = -1;
        kfo_host_tg_resolve(_p);
    }
    _h.ds = true;
    return _n;
}

// a knockout: player _v fell, credited to _by (the sender of the last skill that hit it, or the last player who hurt it)
function kfo_host_tg_ko(_v, _by)
{
    var _h = global.kfo.H;
    if (!kbr_tg_on(_h.eff) || !is_numeric(_by) || _by < 0 || _by == _v.pid)
        return false;
    var _k = kfo_host_player(_by);
    if (is_undefined(_k) || !_k.inm)
        return false;
    var _B = kbr_tg_bal();
    _k.kos++;
    var _gain = 0;
    if (_h.eff.shards)
    {
        _gain = _B.ko_shard + floor(_v.sh * _B.ko_steal);
        _k.sh += _gain;
    }
    kfo_host_feed("* " + _k.n + " knocked out " + _v.n + "." + ((_gain > 0) ? (" +" + string(_gain) + " CRYSTAL" + ((_gain == 1) ? "" : "S")) : ""), make_color_rgb(200, 120, 255));
    _h.ds = true;
    return true;
}

// ---------- this game ----------
function kbr_tg_new()
{
    var _o = global.kfo;
    if (!variable_struct_exists(_o, "tgm"))
        _o.tgm = 0;
    return { mode: _o.tgm, pick: -1, sent_m: -1, sent_pk: -2, t_sent: 0, att: [], att_seen: false, exc_t: 0, exc_n: 0, call: {}, call_t: 0, call_txt: "",
        stick: 0, mine: [], sh: 0, t_heal: -100000, desc_t: 0, desc_m: -1 };
}

function kbr_tg_room_on()
{
    var _M = kbr_match();
    return !is_undefined(_M) && kbr_tg_on(_M.eff);
}

// my row of the host's last standings (undefined before the first)
function kbr_tg_me_row(_M)
{
    if (!is_struct(_M.st))
        return undefined;
    var _pl = kfo_ja(_M.st, "pl");
    for (var _i = 0; _i < array_length(_pl); _i++)
    {
        if (kfo_jn(_pl[_i], "pid", -2) == global.kfo.my)
            return _pl[_i];
    }
    return undefined;
}

// the player list's order (the match's own slots: the numbers 1-8, the colours); standing ones only when _alive
function kbr_tg_slots(_M, _alive)
{
    var _o = [];
    if (!is_struct(_M.st))
        return _o;
    var _pl = kfo_ja(_M.st, "pl");
    for (var _s = 0; _s < 8; _s++)
    {
        for (var _i = 0; _i < array_length(_pl); _i++)
        {
            var _pid = kfo_jn(_pl[_i], "pid", -2);
            if (kbr_pslot(_pid) != _s)
                continue;
            if (_alive && (kfo_jn(_pl[_i], "al", 0) != 1 || _pid == global.kfo.my))
                continue;
            array_push(_o, _pl[_i]);
        }
    }
    return _o;
}

// the centre of player _pid's SOUL in this game (mine: my own SOUL; the others: where the host last put them), or undefined
function kbr_tg_pos(_pid)
{
    var _M = kbr_match();
    if (is_undefined(_M))
        return undefined;
    if (_pid == global.kfo.my && _M.me && !_M.out && instance_exists(obj_heart))
    {
        var _h = instance_find(obj_heart, 0);
        return [(_h.bbox_left + _h.bbox_right) / 2, (_h.bbox_top + _h.bbox_bottom) / 2];
    }
    var _id = string(_pid);
    if (variable_struct_exists(_M.ps, _id))
    {
        var _q = variable_struct_get(_M.ps, _id);
        return [kbr_ps_x(_q) + 10, kbr_ps_y(_q) + 10];
    }
    return undefined;
}

// OUTNUMBERED BONUS: the gauge fills faster for each player targeting me
function kbr_tg_outn_mul()
{
    var _M = kbr_match();
    if (is_undefined(_M) || !kbr_tg_on(_M.eff) || !_M.eff.outn || !variable_struct_exists(_M, "tg"))
        return 1;
    var _B = kbr_tg_bal();
    return 1 + min(_B.outn_max, array_length(_M.tg.att) * _B.outn_per);
}

// my mode / pick to the host (at once when they change, again every 3 s)
function kbr_tg_send(_M, _force)
{
    var _T = _M.tg;
    if (!_force && _T.sent_m == _T.mode && _T.sent_pk == _T.pick && current_time - _T.t_sent < 3000)
        return 0;
    _T.sent_m = _T.mode;
    _T.sent_pk = _T.pick;
    _T.t_sent = current_time;
    kfo_up({ k: "tg", mid: _M.mid, m: _T.mode, pk: _T.pick });
    return 1;
}

// CHECK: pick player _pid (switches to CHECK when the room allows it)
function kbr_tg_pick(_M, _pid)
{
    var _T = _M.tg;
    if (!kbr_tg_mode_ok(_M.eff, KBR_TG_CHECK))
    {
        snd_play(snd_cantselect);
        return 0;
    }
    if (_T.mode != KBR_TG_CHECK)
        kbr_tg_desc_show(_T, KBR_TG_CHECK);
    _T.mode = KBR_TG_CHECK;
    _T.pick = _pid;
    global.kfo.tgm = _T.mode;
    snd_play(snd_menumove);
    kbr_tg_send(_M, true);
    return 1;
}

// the next (_d 1) or previous (-1) standing player after my current pick, in the list's order
function kbr_tg_pick_next(_M, _d)
{
    var _l = kbr_tg_slots(_M, true);
    var _n = array_length(_l);
    if (_n == 0)
        return 0;
    var _cur = _M.tg.pick;
    if (_M.tg.mode != KBR_TG_CHECK && array_length(_M.tg.mine) == 1)
        _cur = _M.tg.mine[0];
    var _k = -1;
    for (var _i = 0; _i < _n; _i++)
    {
        if (kfo_jn(_l[_i], "pid", -2) == _cur)
            _k = _i;
    }
    _k = (_k < 0) ? ((_d > 0) ? 0 : (_n - 1)) : ((_k + _d + _n) mod _n);
    return kbr_tg_pick(_M, kfo_jn(_l[_k], "pid", -1));
}

// build 51: the mode's one-line description, shown for 2 seconds when the mode changes (never kept on screen)
function kbr_tg_desc_show(_T, _m)
{
    _T.desc_t = 60;
    _T.desc_m = _m;
    return 1;
}

// every step of a standing player (from kbr_me_tick): the keys
function kbr_tg_tick(_M)
{
    if (!kbr_tg_on(_M.eff))
        return 0;
    if (!variable_struct_exists(_M, "tg"))
        _M.tg = kbr_tg_new();
    var _T = _M.tg;
    var _fixed = kbr_tg_mode_fix(_M.eff, _T.mode);
    if (_fixed != _T.mode)
    {
        _T.mode = _fixed;
        global.kfo.tgm = _fixed;
    }
    if (_T.exc_t > 0)
        _T.exc_t--;
    if (_T.call_t > 0)
        _T.call_t--;
    if (variable_struct_exists(_T, "desc_t") && _T.desc_t > 0)
        _T.desc_t--;
    if (_M.out || !_M.me)
        return 0;
    var _busy = kfo_chat_typing() || (variable_struct_exists(_M, "vw") && _M.vw.qs) || _M.tab;
    if (!_busy)
    {
        if (kbr_key_pressed("tgl") || kbr_key_pressed("tgr"))
        {
            var _nm = kbr_tg_mode_step(_M.eff, _T.mode, kbr_key_pressed("tgl") ? -1 : 1);
            if (_nm != _T.mode)
            {
                _T.mode = _nm;
                global.kfo.tgm = _nm;
                snd_play(snd_menumove);
                kbr_tg_desc_show(_T, _nm);
            }
        }
        if (kbr_key_pressed("tgn"))
            kbr_tg_pick_next(_M, 1);
        // 1-8: the player in that slot of the list
        for (var _i = 0; _i < 8; _i++)
        {
            if (keyboard_check_pressed(ord("1") + _i))
            {
                var _l = kbr_tg_slots(_M, false);
                if (_i < array_length(_l))
                {
                    var _pid = kfo_jn(_l[_i], "pid", -1);
                    if (kfo_jn(_l[_i], "al", 0) == 1 && _pid != global.kfo.my)
                        kbr_tg_pick(_M, _pid);
                    else
                        snd_play(snd_cantselect);
                }
            }
        }
        // a controller: the right stick flicks between targets
        var _ax = 0;
        if (instance_exists(obj_gamecontroller))
        {
            var _g = instance_find(obj_gamecontroller, 0);
            if (variable_instance_exists(_g, "gamepad_id") && _g.gamepad_id >= 0)
                _ax = gamepad_axis_value(_g.gamepad_id, gp_axisrh);
        }
        if (abs(_ax) > 0.6)
        {
            if (_T.stick == 0)
                kbr_tg_pick_next(_M, (_ax > 0) ? 1 : -1);
            _T.stick = 1;
        }
        else if (abs(_ax) < 0.3)
            _T.stick = 0;
    }
    kbr_tg_send(_M, false);
    return 1;
}

// the host's new standings: my targets, who targets me (a new one: the "!" over my SOUL), my shards, the callouts
function kbr_tg_on_state(_M, _m)
{
    if (!kbr_tg_on(_M.eff))
        return 0;
    if (!variable_struct_exists(_M, "tg"))
        _M.tg = kbr_tg_new();
    var _T = _M.tg;
    var _my = global.kfo.my;
    var _pl = kfo_ja(_m, "pl");
    var _att = [];
    var _B = kbr_tg_bal();
    for (var _i = 0; _i < array_length(_pl); _i++)
    {
        var _p = _pl[_i];
        var _pid = kfo_jn(_p, "pid", -2);
        if (_pid == _my)
        {
            _T.mine = kfo_ja(_p, "tg");
            _T.sh = kfo_jn(_p, "sh", 0);
            // the host settled CHECK on someone else (the one I picked fell): keep the pick in step
            if (_T.mode == KBR_TG_CHECK && array_length(_T.mine) == 1 && kfo_jn(_p, "tm", 0) == KBR_TG_CHECK)
            {
                _T.pick = _T.mine[0];
                _T.sent_pk = _T.pick;
            }
            continue;
        }
        if (kfo_jn(_p, "al", 0) != 1 || !kbr_tg_has(kfo_ja(_p, "tg"), _my))
            continue;
        array_push(_att, _pid);
        // a high charge aimed at me: a callout (the sender's party member)
        var _key = string(_pid);
        var _last = variable_struct_exists(_T.call, _key) ? variable_struct_get(_T.call, _key) : -100000;
        // (build 49: the callouts are gone - they covered the party's HP bars)
        if (false && kfo_jn(_p, "g", 0) >= _B.call_g && current_time - _last >= _B.call_ms && _M.me && !_M.out)
        {
            variable_struct_set(_T.call, _key, current_time);
            _T.call_txt = kbr_tg_callout(kfo_jn(_p, "s", 1), _pid + floor(current_time / 1000));
            _T.call_t = 120;
        }
    }
    // somebody new locked onto me: the "!" (not for the first standings of the match)
    var _new = 0;
    for (var _i = 0; _i < array_length(_att); _i++)
    {
        if (!kbr_tg_has(_T.att, _att[_i]))
            _new++;
    }
    if (_new > 0 && _T.att_seen && _M.me && !_M.out)
    {
        _T.exc_t = 40;
        _T.exc_n = array_length(_att);
        snd_play(snd_b);
    }
    _T.att = _att;
    _T.att_seen = true;
    return 1;
}

// "* Susie's gaze sharpens on you." (Kris: they / them)
function kbr_tg_callout(_skin, _r)
{
    var _nm = kfo_skin_name(_skin);
    var _k = abs(floor(_r)) mod 3;
    switch (kfo_skin_ok(_skin))
    {
        case 1:
            if (_k == 1) return "* Kris raises their sword toward you.";
            if (_k == 2) return "* Kris has their eyes on you.";
            break;
        case 2:
            if (_k == 1) return "* Susie grins and points her axe at you.";
            if (_k == 2) return "* Susie cracks her knuckles at you.";
            break;
        case 3:
            if (_k == 1) return "* Ralsei hesitantly readies his magic at you.";
            if (_k == 2) return "* Ralsei adjusts his glasses at you.";
            break;
        case 4:
            if (_k == 1) return "* Noelle's ring glows, aimed at you.";
            if (_k == 2) return "* The air around Noelle turns cold.";
            break;
        case 5:
            if (_k == 1) return "* Flowery flashes you a winning smile. Uh oh.";
            if (_k == 2) return "* Flowery: Heh. Here I come, Sanfrandisco!";
            break;
        case 6:
            if (_k == 1) return "* Berdly pushes up his glasses. He has calculated you.";
            if (_k == 2) return "* Berdly: Prepare to be OUT-SMARTED!";
            break;
        case 7:
            if (_k == 1) return "* Aqua twirls a knife and smiles at you.";
            if (_k == 2) return "* Aqua's knife glints. It's pointing your way.";
            break;
        // DRBR: the other flowers, Pink and Spamton
        case 8:
            if (_k == 1) return "* Seth opens his notebook and writes down your name.";
            if (_k == 2) return "* Seth adjusts his glasses. You have been noted.";
            break;
        case 9:
            if (_k == 1) return "* Orange winds up a punch in your direction.";
            if (_k == 2) return "* Orange's fist is ready. It's pointed at you.";
            break;
        case 10:
            if (_k == 1) return "* Green raises his frying pan at you.";
            if (_k == 2) return "* Green waves at you. It feels like a warning.";
            break;
        case 11:
            if (_k == 1) return "* Yellow tips his hat. His aim is on you.";
            if (_k == 2) return "* Yellow's hand hovers over his holster.";
            break;
        case 12:
            if (_k == 1) return "* Blue pirouettes around to face you.";
            if (_k == 2) return "* Blue strikes a pose, aimed right at you.";
            break;
        case 13:
            if (_k == 1) return "* Pink points her cat wand at you. Mew!";
            if (_k == 2) return "* Pink giggles. Your turn is next, mew!";
            break;
        case 14:
            if (_k == 1) return "* Spamton has a [[Special Deal]] just for you!";
            if (_k == 2) return "* Spamton: HEY, [[Little Sponge]]! YOU'RE NEXT!";
            break;
    }
    return "* " + _nm + "'s gaze sharpens on you.";
}

// ---------- drawing ----------
// the threads: a thin line in the sender's colour from the box's edge to each target, brighter as the sender charges
function kbr_tg_threads(_M)
{
    if (!kbr_tg_on(_M.eff) || !is_struct(_M.st) || !instance_exists(obj_growtangle))
        return 0;
    var _b = instance_find(obj_growtangle, 0);
    if (_b.x < -1000)
        return 0;
    var _hw = abs(_b.sprite_width) / 2;
    var _hh = abs(_b.sprite_height) / 2;
    var _my = global.kfo.my;
    var _pl = kfo_ja(_M.st, "pl");
    for (var _i = 0; _i < array_length(_pl); _i++)
    {
        var _p = _pl[_i];
        if (kfo_jn(_p, "al", 0) != 1)
            continue;
        var _pid = kfo_jn(_p, "pid", -2);
        var _tg = kfo_ja(_p, "tg");
        var _slot = kbr_pslot(_pid);
        var _col = kbr_pcol(_slot);
        var _g = clamp(kfo_jn(_p, "g", 0), 0, 100) / 100;
        // the thread leaves the box's edge on the side of the sender's slot (8 places around the box)
        var _ang = 90 + (_slot * 45);
        var _ex = _b.x + clamp(lengthdir_x(_hw * 1.5, _ang), -_hw, _hw);
        var _ey = _b.y + clamp(lengthdir_y(_hh * 1.5, _ang), -_hh, _hh);
        for (var _j = 0; _j < array_length(_tg); _j++)
        {
            var _pos = kbr_tg_pos(_tg[_j]);
            if (is_undefined(_pos))
                continue;
            var _mine = (_pid == _my || _tg[_j] == _my);
            var _a = (_mine ? 0.3 : 0.12) + ((_mine ? 0.6 : 0.3) * _g);
            draw_set_alpha(_a);
            draw_set_color(_col);
            draw_line(_ex, _ey, _pos[0], _pos[1]);
            if (_g >= 0.8)
            {
                draw_set_alpha(_a * 0.5);
                draw_line(_ex + 1, _ey, _pos[0] + 1, _pos[1]);
            }
        }
    }
    draw_set_alpha(1);
    return 1;
}

// the "!" over my SOUL, with how many target me
function kbr_tg_exc(_M)
{
    var _T = _M.tg;
    if (_T.exc_t <= 0 || !_M.me || _M.out || !instance_exists(obj_heart))
        return 0;
    var _h = instance_find(obj_heart, 0);
    var _cx = (_h.bbox_left + _h.bbox_right) / 2;
    var _cy = _h.bbox_top - 4;
    var _pop = (_T.exc_t > 34) ? (1 + ((_T.exc_t - 34) * 0.1)) : 1;
    var _a = min(1, _T.exc_t / 10);
    draw_sprite_ext(spr_exc, 0, _cx - (sprite_get_width(spr_exc) * _pop * 0.5) + (sprite_get_xoffset(spr_exc) * _pop), _cy - (sprite_get_height(spr_exc) * _pop) + (sprite_get_yoffset(spr_exc) * _pop), _pop, _pop, 0, c_white, _a);
    if (_T.exc_n > 1)
    {
        draw_set_font(fnt_small);
        draw_set_alpha(_a);
        kbr_hud_text(_cx + 8, _cy - 14, string(_T.exc_n), c_red);
        draw_set_alpha(1);
    }
    return 1;
}

// build 50: the SHADOW CRYSTAL icon for shards (Deltarune's own item art)
function kbr_tg_shard_icon(_x, _y)
{
    // build 50: Deltarune's own SHADOW CRYSTAL (the item's pixel art, 7 x 9, its flat grey)
    var _rows = ["0010000", "0011000", "0011000", "0101100", "0100110", "0100111", "1001100", "1111000", "1100000"];
    draw_set_color(make_color_rgb(127, 127, 127));
    for (var _r = 0; _r < 9; _r++)
    {
        var _s = _rows[_r];
        for (var _c = 0; _c < 7; _c++)
        {
            if (string_char_at(_s, _c + 1) == "1")
                draw_rectangle(_x + _c, _y + _r, _x + _c, _y + _r, false);
        }
    }
    draw_set_color(c_white);
    return 1;
}

// the command row (under the box): the seven modes in the battle menu's colours, the active one yellow with the SOUL
// DRBR: whether the TARGETING strip is on screen (the network line goes over it then)
function kbr_hud_tg_shown(_M)
{
    return kbr_tg_on(_M.eff) && _M.me && !_M.out && variable_struct_exists(_M, "tg") && !_M.vw.qs && !kbr_hud_roaring();
}

function kbr_hud_tg(xx, yy, _M)
{
    if (!kbr_tg_on(_M.eff) || !_M.me || _M.out || !variable_struct_exists(_M, "tg"))
        return 0;
    var _T = _M.tg;
    var _n = kbr_tg_count();
    // build 51: one slim strip - TARGET (who your red skills hit now, with their SOUL colour) on the left, the seven modes as
    // small DELTARUNE command chips in the middle (the selected one yellow, raised, with a soft pulse; off modes grey), your
    // SHADOW CRYSTALS (and the strength they give) and how many players target you (a red !) on the right
    var _y0 = yy + 412;
    var _bh = 15;
    var _w = 50;
    var _gap = 3;
    var _cx0 = xx + 156;
    var _org = make_color_rgb(255, 160, 64);
    draw_set_font(fnt_small);
    // the strip's background
    draw_set_alpha(0.75);
    draw_set_color(c_black);
    draw_rectangle(xx + 14, _y0 - 4, xx + 626, _y0 + _bh + 3, false);
    draw_set_alpha(1);
    draw_set_color(make_color_rgb(70, 70, 70));
    draw_rectangle(xx + 14, _y0 - 4, xx + 626, _y0 + _bh + 3, true);
    draw_rectangle(xx + 15, _y0 - 3, xx + 625, _y0 + _bh + 2, true);
    draw_set_halign(fa_center);
    for (var _i = 0; _i < _n; _i++)
    {
        var _bx = _cx0 + (_i * (_w + _gap));
        var _ok = kbr_tg_mode_ok(_M.eff, _i);
        var _on = (_T.mode == _i);
        var _c = _on ? c_yellow : (_ok ? _org : make_color_rgb(70, 70, 70));
        var _by = _y0 - (_on ? 1 : 0);
        draw_set_color(c_black);
        draw_rectangle(_bx, _by, _bx + _w, _by + _bh, false);
        if (_on)
        {
            draw_set_alpha(0.2 + (0.1 * sin(current_time / 250)));
            draw_set_color(c_yellow);
            draw_rectangle(_bx + 2, _by + 2, _bx + _w - 2, _by + _bh - 2, false);
            draw_set_alpha(1);
        }
        draw_set_color(_c);
        draw_rectangle(_bx, _by, _bx + _w, _by + _bh, true);
        if (_on)
            draw_rectangle(_bx + 1, _by + 1, _bx + _w - 1, _by + _bh - 1, true);
        kbr_hud_text(_bx + (_w / 2) + 1, _by + 4, kbr_tg_name(_i), _ok ? (_on ? c_yellow : c_white) : make_color_rgb(90, 90, 90));
    }
    draw_set_halign(fa_left);
    var _ly = _y0 + 4;
    // build 51: no key hint here any more (the tutorial and the TAB box have the keys)
    // left: TARGET
    var _tx = "";
    var _nt = array_length(_T.mine);
    var _tcol = c_yellow;
    if (_nt == 1)
    {
        var _r = kbr_st_player(_M, _T.mine[0]);
        _tx = is_undefined(_r) ? "?" : string_upper(string_copy(kfo_js(_r, "n", "?"), 1, 8));
        _tcol = kbr_pcol(kbr_pslot(_T.mine[0]));
    }
    else if (_nt > 1)
        _tx = string(_nt) + " SOULS";
    kbr_hud_text(xx + 22, _ly, "TARGET", c_gray);
    if (_tx == "")
        kbr_hud_text(xx + 66, _ly, "-", c_gray);
    else
    {
        if (_nt == 1)
            draw_sprite_ext(spr_khub_soul, 0, xx + 64, _ly - 2, 0.5, 0.5, 0, _tcol, 1);
        kbr_hud_text(xx + ((_nt == 1) ? 77 : 66), _ly, kbr_fit(_tx, 74), c_yellow);
    }
    // right: SHADOW CRYSTALS and ON YOU
    var _rx = _cx0 + (_n * (_w + _gap)) + 4;
    var _na = array_length(_T.att);
    if (_M.eff.shards)
    {
        kbr_tg_shard_icon(_rx, _ly - 1);
        kbr_hud_text(_rx + 9, _ly, string(_T.sh) + " x" + string_format(kbr_tg_shard_mul(_T.sh), 1, 2), (_T.sh > 0) ? c_white : c_gray);
    }
    draw_set_halign(fa_right);
    kbr_hud_text(xx + 620, _ly, "!" + string(_na), (_na > 0) ? c_red : c_dkgray);
    draw_set_halign(fa_left);
    // the new mode's description for 2 seconds, in the game's dialogue font on a black strip above the row
    if (variable_struct_exists(_T, "desc_t") && _T.desc_t > 0 && _T.desc_m >= 0)
    {
        var _dt = kbr_tg_desc(_T.desc_m);
        scr_84_set_draw_font("main");
        var _dw = string_width(_dt);
        draw_set_alpha(min(1, _T.desc_t / 10));
        draw_set_color(c_black);
        draw_rectangle(xx + 320 - (_dw / 2) - 8, _y0 - 26, xx + 320 + (_dw / 2) + 8, _y0 - 8, false);
        draw_set_halign(fa_center);
        draw_set_color(c_white);
        draw_text(xx + 320, _y0 - 25, _dt);
        draw_set_halign(fa_left);
        draw_set_alpha(1);
        draw_set_font(fnt_small);
    }
    // the callout
    if (false && _T.call_t > 0 && _T.call_txt != "")
    {
        draw_set_alpha(min(1, _T.call_t / 15));
        scr_84_set_draw_font("main");
        var _txw = string_width(_T.call_txt);
        if (_txw > 560)
            draw_set_font(fnt_small);
        draw_set_halign(fa_center);
        kbr_hud_text(xx + 320, yy + 344, _T.call_txt, c_white);
        draw_set_halign(fa_left);
        draw_set_alpha(1);
        draw_set_font(fnt_small);
    }
    draw_set_color(c_white);
    return 1;
}
