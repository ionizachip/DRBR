// ===== Build 45: KNIGHT FIGHTS ONLINE - the match on this player's screen =====
// One shared battle royale: every game runs the same battle from the same timeline (online_br*.gml). This file is the
// player's side of the match: the start, the shared clock (ping / pong with the host), the messages from the host, the
// fallbacks, the results.
//   start  -> the battle launches; once it is up the game tells the host ("rdy")
//   go     -> the host's tick 0: the countdown runs and the attacks come on the timeline
//   ps/st  -> the others' SOULs and the standings; ska -> a rival's skill; ft -> the final two; rs -> resync (desync seen)
//   end    -> the results (Z or 10 seconds: back to the room)

function kfo_match()
{
    if (!is_struct(global.kfo) || !is_struct(global.kfo.M))
        return undefined;
    return global.kfo.M;
}

// an online fight is running in this game
function kfo_run_on()
{
    return knight_active() && knight_lu_kind_of(global.krun.cfg) == "online" && is_struct(kfo_match());
}

function kfo_cfg_online(_c)
{
    return knight_lu_kind_of(_c) == "online";
}

// ---------- messages from the host ----------
function kfo_client_on(_m)
{
    var _o = global.kfo;
    if (!is_struct(_m))
        return 0;
    switch (kfo_js(_m, "k", ""))
    {
        case "ch":
        case "chh":
        case "chx":
            kfo_chat_on(_m);   // build 48: the room's chat
            break;
        case "lobby":
            _o.lobby = _m;
            break;
        case "start":
            kfo_on_start(_m);
            break;
        case "go":
            kfo_on_go(_m);
            break;
        case "po":
            if (kfo_jn(_m, "mid", -1) < 0)
                _o.rtt = current_time - kfo_jn(_m, "c", current_time);
            else
                kfo_on_po(_m);
            break;
        case "ps":
            if (kfo_mid_ok(_m))
                kbr_on_ps(_m);
            break;
        case "st":
            // build 47: the room's page shows the running match too (who is standing, the knight, the time, the watchers)
            _o.lst = _m;
            _o.lst_t = current_time;
            kfo_on_state(_m);
            break;
        case "ska":
            if (kfo_mid_ok(_m))
                kbr_on_ska(_m);
            break;
        // DRBR 1.0.3: someone used a skill (shown at their SOUL)
        case "su":
            if (kfo_mid_ok(_m))
                kbr_view_on_su(_m);
            break;
        case "lsh":
            if (kfo_mid_ok(_m))
                kbr_on_lsh(_m);
            break;
        case "ft":
            kfo_on_ft(_m);
            break;
        case "flph":
            kbr_fl_on_flph(_m);
            break;
        case "rs":
            kfo_on_resync(_m);
            break;
        case "fix":
            kfo_on_fix(_m);
            break;
        case "end":
            kfo_on_end(_m);
            break;
        case "ows":
            kfo_world_on(_m);
            break;
        case "kick":
            kfo_lost(kfo_js(_m, "why", "The host removed you from the room."));
            break;
    }
    return 1;
}

function kfo_mid_ok(_m)
{
    var _M = kfo_match();
    return !is_undefined(_M) && kfo_jn(_m, "mid", -1) == _M.mid;
}

function kfo_match_new(_m)
{
    var _o = global.kfo;
    var _pl = kfo_ja(_m, "players");
    var _me = false;
    for (var _i = 0; _i < array_length(_pl); _i++)
    {
        if (kfo_jn(_pl[_i], "pid", -2) == _o.my)
            _me = true;
    }
    var _M = { mid: kfo_jn(_m, "mid", 0), seed: kfo_jn(_m, "seed", 1), set: kfo_set_clean(kfo_jv(_m, "set")), players: _pl, me: _me,
        prac: (kfo_jn(_m, "prac", 0) == 1), st: undefined, ended: false, res: undefined, out: false, launched: false, sn: array_length(_pl),
        t_start: current_time, t_rdy: 0, rdy: false, res_t: -1, spec: (kfo_jn(_m, "spec", 0) == 1), place: 0 };
    kbr_match_fill(_M, _m);
    if (_M.spec)
        _M.me = false;
    return _M;
}

function kfo_on_start(_m)
{
    var _o = global.kfo;
    // build 52: a new match while this game still shows the last one's results (the host pressed START during this
    // player's 10 seconds of results): the results close now and this game joins the new match as a player once it is back
    // in the room (kfo_start_wait_tick) - it used to stay out of it and watch, every time
    if (knight_active() && !variable_struct_exists(_m, "kfo_late") && kfo_start_has_me(_m))
    {
        _o.start_wait = { m: _m, t: current_time, f: 0, go: undefined, go_t: 0 };
        kfo_back_to_lobby();
        return 0;
    }
    // a new match while this game still runs a fight of the last one (it should not happen): stay out of it
    if (knight_active())
    {
        var _M0 = kfo_match_new(_m);
        _M0.me = false;
        _M0.spec = false;
        _o.M = _M0;
        return 0;
    }
    _o.M = kfo_match_new(_m);
    var _M = _o.M;
    // a spectator coming in late gets the host's match time with the start
    if (_M.spec && kfo_jn(_m, "h", -999999) > -999999)
    {
        _M.go = true;
        _M.t0ms = current_time - kfo_jn(_m, "h", 0);
    }
    if (_M.me || _M.spec)
        kfo_launch();
    return 1;
}

// build 52: is this game's player one of the new match's players
function kfo_start_has_me(_m)
{
    var _pl = kfo_ja(_m, "players");
    if (kfo_jn(_m, "spec", 0) == 1)
        return false;
    for (var _i = 0; _i < array_length(_pl); _i++)
    {
        if (kfo_jn(_pl[_i], "pid", -2) == global.kfo.my)
            return true;
    }
    return false;
}

// build 52: a START that came while the last match's results were up: once this game has left the last fight (and 15 frames
// went by for the trip back to the room) the match starts here as for everyone else; the host's GO that came meanwhile follows, its time moved on by
// the wait (so the shared clock is right). After 8 seconds without getting back it watches instead (as before).
function kfo_start_wait_tick()
{
    var _o = global.kfo;
    if (!variable_struct_exists(_o, "start_wait") || !is_struct(_o.start_wait))
        return 0;
    var _w = _o.start_wait;
    if (knight_active())
    {
        _w.f = 0;
        if (current_time - _w.t > 8000)
        {
            _o.start_wait = undefined;
            var _m = _w.m;
            _m.kfo_late = 1;
            kfo_on_start(_m);
        }
        return 0;
    }
    _w.f++;
    if (_w.f < 15)
        return 0;
    _o.start_wait = undefined;
    kfo_on_start(_w.m);
    if (is_struct(_w.go))
    {
        var _g = _w.go;
        _g.h = kfo_jn(_g, "h", 0) + (current_time - _w.go_t);
        kfo_on_go(_g);
    }
    return 1;
}

// the host's GO: tick 0 is "in" ms after the host sent it (h: the host's match time then, negative)
function kfo_on_go(_m)
{
    // build 52: the GO of a match this game is about to join (kfo_start_wait_tick): kept until it has started
    if (variable_struct_exists(global.kfo, "start_wait") && is_struct(global.kfo.start_wait) && kfo_jn(_m, "mid", -1) == kfo_jn(global.kfo.start_wait.m, "mid", -2))
    {
        global.kfo.start_wait.go = _m;
        global.kfo.start_wait.go_t = current_time;
        return 0;
    }
    var _M = kfo_match();
    if (!kfo_mid_ok(_m))
        return 0;
    if (kfo_is_host() && is_struct(global.kfo.H))
        _M.t0ms = global.kfo.H.t0ms;
    else
    {
        var _h = kfo_jn(_m, "h", 0);
        var _half = (_M.ck.rtt >= 0) ? (_M.ck.rtt / 2) : 0;
        _M.t0ms = current_time - _half - _h;
        _M.ck.target = _M.t0ms;
    }
    _M.go = true;
    return 1;
}

// ---------- the shared clock ----------
// every ping's answer gives one estimate of this game's time of the host's tick 0; the one with the shortest round trip of
// the last 16 is the best (NTP's idea). Small differences are slewed in 1 ms a step, big ones (a lag spike) jump.
function kfo_ping_tick()
{
    var _M = kfo_match();
    if (is_undefined(_M) || kfo_is_host() || _M.ended)
        return 0;
    var _gap = (_M.ck.n < 8 || current_time - _M.t_start < 8000) ? 250 : 1000;
    if (current_time - _M.ck.t_ping >= _gap)
    {
        _M.ck.t_ping = current_time;
        _M.ck.n++;
        kfo_up_fast({ k: "pi", mid: _M.mid, c: current_time });
        // build 47: the last 20 pings and whether each was answered (PACKET LOSS in the network stats)
        if (!variable_struct_exists(_M.ck, "pl"))
            _M.ck.pl = [];
        array_push(_M.ck.pl, [current_time, false]);
        if (array_length(_M.ck.pl) > 20)
            array_delete(_M.ck.pl, 0, 1);
    }
    // slew toward the best estimate
    if (_M.go && variable_struct_exists(_M.ck, "target"))
    {
        var _d = _M.ck.target - _M.t0ms;
        if (abs(_d) > 150)
        {
            _M.t0ms = _M.ck.target;
            _M.ck.jumps++;
        }
        else if (_d != 0)
            _M.t0ms += clamp(_d, -1, 1);
    }
    return 1;
}

function kfo_on_po(_m)
{
    var _M = kfo_match();
    if (!kfo_mid_ok(_m) || kfo_is_host())
        return 0;
    var _now = current_time;
    var _rtt = _now - kfo_jn(_m, "c", _now);
    if (_rtt < 0 || _rtt > 5000)
        return 0;
    _M.ck.rtt = _rtt;
    // build 47: the ping shown (network line, the room's light, the standings): a running average, not the last sample
    if (!variable_struct_exists(_M.ck, "ra") || _M.ck.ra < 0)
        _M.ck.ra = _rtt;
    else
        _M.ck.ra = lerp(_M.ck.ra, _rtt, 0.2);
    if (variable_struct_exists(_M.ck, "pl"))
    {
        var _c0 = kfo_jn(_m, "c", -1);
        for (var _i = 0; _i < array_length(_M.ck.pl); _i++)
        {
            if (_M.ck.pl[_i][0] == _c0)
                _M.ck.pl[_i][1] = true;
        }
    }
    // the host has no match clock yet (before its GO): the round trip counts, the time does not
    if (kfo_jn(_m, "g", 0) != 1)
        return 0;
    var _h = kfo_jn(_m, "h", 0);
    var _est = _now - (_rtt / 2) - _h;
    array_push(_M.ck.samples, [_rtt, _est, _now]);
    if (array_length(_M.ck.samples) > 16)
        array_delete(_M.ck.samples, 0, 1);
    var _bi = 0;
    for (var _i = 1; _i < array_length(_M.ck.samples); _i++)
    {
        if (_M.ck.samples[_i][0] < _M.ck.samples[_bi][0])
            _bi = _i;
    }
    _M.ck.best = _M.ck.samples[_bi][0];
    _M.ck.target = _M.ck.samples[_bi][1];
    // the match is on and this game missed the GO (or joined to watch): start from the estimate
    if (!_M.go && kfo_jn(_m, "g", 0) == 1)
    {
        _M.go = true;
        _M.t0ms = _M.ck.target;
    }
    return 1;
}

// this game's battle is up: the host waits for everyone before its GO
function kfo_ready_up()
{
    var _M = kfo_match();
    if (is_undefined(_M) || _M.rdy)
        return 0;
    _M.rdy = true;
    _M.t_rdy = current_time;
    if (_M.me)
        kfo_up({ k: "rdy", mid: _M.mid });
    return 1;
}

function kfo_on_state(_m)
{
    var _M = kfo_match();
    if (!kfo_mid_ok(_m))
        return 0;
    // build 47: what changed for the view (hits, skills, OUTs) before the new standings replace the old
    if (variable_struct_exists(_M, "vw"))
    {
        _M.vw.lst_t = current_time;
        kbr_view_on_state(_M, _m);
    }
    // build 48: targeting (who targets me now, my shards, the callouts)
    if (variable_struct_exists(_M, "eff"))
        kbr_tg_on_state(_M, _m);
    _M.st = _m;
    _M.sn = kfo_jn(_m, "sn", _M.sn);
    // DRBR: Flowery's GROUP MERCY (and any phase announcement this game missed)
    kbr_fl_on_st(_M, _m);
    // the room's feed: new lines go to the log
    var _fd = kfo_ja(_m, "fd");
    if (!variable_struct_exists(_M, "fseen"))
        _M.fseen = 0;
    for (var _i = 0; _i < array_length(_fd); _i++)
    {
        var _e = _fd[_i];
        if (!is_array(_e) || array_length(_e) < 2 || !is_numeric(_e[0]) || !is_string(_e[1]))
            continue;
        if (_e[0] > _M.fseen)
        {
            _M.fseen = _e[0];
            var _col = (array_length(_e) > 2 && is_numeric(_e[2])) ? _e[2] : c_white;
            kbr_log(_e[1], _col);
        }
    }
    // my place, once the host decided it
    var _pl = kfo_ja(_m, "pl");
    for (var _i = 0; _i < array_length(_pl); _i++)
    {
        if (kfo_jn(_pl[_i], "pid", -2) == global.kfo.my)
            _M.place = kfo_jn(_pl[_i], "pl", 0);
    }
    return 1;
}

// the final two: the host names the first cycle of the showdown (a little ahead, so every game makes that cycle with it)
function kfo_on_ft(_m)
{
    var _M = kfo_match();
    if (!kfo_mid_ok(_m))
        return 0;
    var _ck = kfo_jn(_m, "ck", -1);
    if (_ck < 0)
        return 0;
    // a cycle this game already armed or ran cannot change any more: the host's check will resync it if it differs
    var _busy = (_M.R.ph == "run" || _M.R.ph == "arm") ? ((_M.R.ph == "run") ? _M.R.k : _M.R.arm_k) : -1;
    if (_busy >= _ck)
    {
        kbr_tl_set_ft(_M.tl, _ck);
        kfo_resync_local("ft");
        return 1;
    }
    kbr_tl_set_ft(_M.tl, _ck);
    return 1;
}

// the host saw this game out of step: the timeline is made again from the host's numbers, the attack on screen stops, and
// the game joins at the next cycle it can arm in time
function kfo_on_resync(_m)
{
    var _M = kfo_match();
    if (!kfo_mid_ok(_m))
        return 0;
    // the clock only: measure it again (fast pings, the best of the new answers) - the attack on screen goes on
    if (kfo_js(_m, "why", "") == "clock")
    {
        _M.ck.samples = [];
        _M.ck.n = 0;
        _M.ck.fixes++;
        return 1;
    }
    _M.seed = kfo_jn(_m, "seed", _M.seed);
    _M.set = kfo_set_clean(kfo_jv(_m, "set"));
    _M.eff = kbr_eff(_M.set);
    _M.tl = kbr_tl_new(_M.seed, _M.set);
    var _ft = kfo_jn(_m, "ft", -1);
    if (_ft >= 0)
        kbr_tl_set_ft(_M.tl, _ft);
    kbr_tl_flph_load(_M.tl, kfo_ja(_m, "fp"));
    var _h = kfo_jn(_m, "h", -999999);
    if (_h > -999999 && !kfo_is_host())
    {
        var _half = (_M.ck.rtt >= 0) ? (_M.ck.rtt / 2) : 0;
        _M.ck.target = current_time - _half - _h;
        _M.t0ms = _M.ck.target;
        _M.go = true;
    }
    kfo_resync_local(kfo_js(_m, "why", "resync"));
    return 1;
}

function kfo_resync_local(_why)
{
    var _M = kfo_match();
    _M.resyncs++;
    _M.t_rs_local = current_time;
    if (kbr_on() && (_M.R.ph == "run" || _M.R.ph == "arm"))
        kbr_cut();
    if (_M.R.ph != "boot" && _M.R.ph != "wait")
    {
        _M.R.ph = "idle";
        _M.R.k = kbr_next_armable(_M.tl, kbr_now() + 2);
        _M.R.swapped_k = -1;
    }
    kfo_log("resync: " + _why);
    return 1;
}

// impossible numbers (the host's check): this game takes the host's
function kfo_on_fix(_m)
{
    var _M = kfo_match();
    if (!kfo_mid_ok(_m) || !kfo_run_on())
        return 0;
    var _c = kbr_char();
    var _mh = kfo_jn(_m, "mhp", global.maxhp[_c]);
    global.maxhp[_c] = clamp(_mh, 1, 999);
    global.hp[_c] = clamp(kfo_jn(_m, "hp", global.hp[_c]), 1, global.maxhp[_c]);
    _M.g = clamp(kfo_jn(_m, "g", _M.g), 0, 100);
    return 1;
}

function kfo_on_end(_m)
{
    var _M = kfo_match();
    if (!kfo_mid_ok(_m))
        return 0;
    _M.ended = true;
    _M.res = _m;
    global.kbr_det.on = false;
    // still in the battle (the winner, the watchers): the results show
    if (kfo_run_on() && (global.krun.state == "battle" || global.krun.state == "arena"))
        kfo_show_results();
    return 1;
}

// a line for the log (sends, heals, warnings)
function kfo_note(_t, _col)
{
    return kbr_log(_t, _col);
}

// ---------- starting the fight ----------
function kfo_launch()
{
    var _o = global.kfo;
    var _M = _o.M;
    var _c = knight_cfg_default();
    _c.mode = 0;
    _c.combo = 3;
    var _first = kfo_host_reg(kbr_reg_of(kbr_tl_get(_M.tl, 0).ok));
    _c.knight = _first;
    _c.knight2 = _first;
    // build 52: an online-only look plays as Kris underneath (the same HP, speed and SOUL); its art is drawn over him
    _c.party = [kfo_skin_bchar(kfo_skin_ok(_o.skin)), 0, 0];
    // build 47: the online MUSIC (MORE OPTIONS) or, left on AS IN THE HUB, the hub's FIGHT SONG - only on this computer
    _c.song = (_o.song >= 0) ? _o.song : (is_struct(global.knight_cfg) ? knight_cfg_num(global.knight_cfg, "song") : 0);
    if (_c.song < 0 || _c.song >= array_length(global.knight_songs))
        _c.song = 0;
    var _rv = _M.spec ? "WATCHING THE MATCH" : (_M.prac ? "PRACTICE: THE LAST SOUL STANDING WINS!" : "DRBR: THE LAST SOUL STANDING WINS!");
    global.knight_launch = { src: _c, cfg: _c, plan: [_first], reveal: _rv, corr: [] };
    _M.launched = true;
    with (obj_knight_prompt)
        instance_destroy();
    if (instance_exists(obj_knight_menu) && is_struct(global.knight_ui))
    {
        var _u = global.knight_ui;
        _u.modal = undefined;
        _u.go = 1;
        _u.gotimer = 0;
        snd_play(snd_select);
    }
    else
        knight_launch_go();
    return 1;
}

// the online kit: the same for every player whatever their own save holds (MAX HP and START HP are the room's).
// Spells and equipment are put back afterwards.
function kfo_kit_apply(_c)
{
    var _o = global.kfo;
    var _M = _o.M;
    _o.keep_spells = knight_spells_to_string();
    _o.keep_equip = knight_equip_to_string();
    _o.keep_cc = knight_cc_to_string();
    for (var _i = 0; _i < 12; _i++)
        global.spell[_c][_i] = 0;
    // each member's own first weapon (none of them adds anything), no armour
    // (a custom character's SKIN - Flowery: no weapon, the kit is the same for everybody)
    var _w = [0, 1, 2, 3, 12];
    global.charweapon[_c] = (_c >= 0 && _c < array_length(_w)) ? _w[_c] : 0;
    global.chararmor1[_c] = 0;
    global.chararmor2[_c] = 0;
    knight_equip_refresh();
    var _mhp = is_struct(_M) ? _M.eff.mhp : 150;
    var _hp0 = is_struct(_M) ? _M.eff.hp0 : 100;
    global.maxhp[_c] = _mhp;
    global.hp[_c] = max(1, round((_mhp * _hp0) / 100));
    global.at[_c] = 14;
    global.df[_c] = 0;
    global.mag[_c] = 0;
    // no items: online, heals come from skills
    for (var _i = 0; _i < 13; _i++)
        global.item[_i] = 0;
    global.tension = 0;
    return 1;
}

function kfo_kit_restore()
{
    if (!is_struct(global.kfo))
        return 0;
    var _o = global.kfo;
    if (string_length(_o.keep_spells) == 48)
        knight_spells_from_string(_o.keep_spells);
    if (string_length(_o.keep_equip) == 12)
        knight_equip_from_string(_o.keep_equip);
    if (variable_struct_exists(_o, "keep_cc") && _o.keep_cc != "")
        knight_cc_from_string(_o.keep_cc);
    _o.keep_cc = "";
    _o.keep_spells = "";
    _o.keep_equip = "";
    global.kbr_det.on = false;
    return 1;
}

// every hit taken in an online fight (knight_scale_taken): the online damage table
function kfo_scale_taken(_d)
{
    return kbr_dmg_taken(_d);
}

// build 47: the battle context of a fight's OWN HP rules. Kaizo Knight's fight has two: its "HP scene" (on its first frame,
// max HP above Kris 200 / Susie 230 / Ralsei 180 / Noelle 180 starts a cutscene that cuts max HP and HP down to those numbers
// and takes over the battle for ~100 frames) and its arena raising Noelle to 120 max HP and 120 HP whenever her max HP is
// lower. Online the room's HP rules are the only ones (MAX HP, START HP, heals, the damage table, sudden death, the host's
// fixes), so both are off there (br_patch.py puts this check in front of them). Offline it is true: nothing changes.
// The same check keeps the game's own cuts off an online hit after the damage table (one Knight attack's 66%, DEFEND's 2/3,
// a member's element resistance - Noelle's ring halved some hits: a SKIN must only be a look).
function knight_enc_hp_rules()
{
    return !(knight_active() && knight_lu_kind_of(global.krun.cfg) == "online");
}

// build 47: a hit that takes a share of max HP (the split slashes, the big quick slash: scr_damage_maxhp's one-member branch)
// never went through scr_damage_calculation, so online it skipped the room's damage rules (66% or 125% of max HP instead of the
// online table, no DAMAGE %, no shield, no OUT: a 125% slash left 1 HP and the match never heard of the hit). Online it is an
// online hit now (the slash's kind in the table); offline the number is returned unchanged.
function knight_direct_taken(_d)
{
    if (knight_active() && knight_lu_kind_of(global.krun.cfg) == "online")
        return kfo_scale_taken(_d);
    return _d;
}

// ---------- the lineup: every hub knight the match's roster can use, the first cycle's first ----------
function kfo_lu_knights()
{
    var _M = kfo_match();
    if (is_undefined(_M))
        return [0];
    // build 52: the battle is always a knight's (the host knight of the lineup); a secret boss is another slot
    var _first = kfo_host_reg(kbr_reg_of(kbr_tl_get(_M.tl, 0).ok));
    var _l = [_first];
    var _ros = kbr_set_roster(_M.eff);
    for (var _i = 0; _i < array_length(_ros); _i++)
    {
        var _g = kbr_reg_of(_ros[_i]);
        var _has = false;
        for (var _j = 0; _j < array_length(_l); _j++)
        {
            if (_l[_j] == _g)
                _has = true;
        }
        if (!_has)
            array_push(_l, _g);
    }
    return _l;
}

function kfo_alive_now()
{
    var _M = kfo_match();
    if (is_undefined(_M) || !is_struct(_M.st))
        return is_undefined(_M) ? 1 : _M.sn;
    return kfo_jn(_M.st, "an", _M.sn);
}

// the lineup's first plan: the timeline arms every attack itself (kbr_arm)
function kfo_lu_plan()
{
    var _lu = global.knight_lu;
    _lu.plan_k = _lu.act;
    _lu.plan_i = -1;
    _lu.plan_name = "";
    _lu.want = _lu.act;
    _lu.pend = false;
    // build 52: a match that opens with a secret boss: it steps in during the countdown (the host knight never shows)
    var _M = kfo_match();
    if (!is_undefined(_M) && is_struct(_M.tl))
    {
        var _s0 = kbr_lu_slot(kbr_tl_get(_M.tl, 0).ok);
        if (_s0 != _lu.act)
        {
            _lu.want = _s0;
            _lu.pend = true;
        }
    }
    return 1;
}

// build 52: the hub knight a match's battle is made with: the first cycle's knight, or (a secret boss first) the Normal Knight
function kfo_host_reg(_reg)
{
    return (is_numeric(_reg) && _reg >= KBR_ENC_BASE) ? 0 : _reg;
}

// stage 3 / the final two: the Knightmare Knight song takes over (when it is in the game's mus folder)
function kfo_mus_knightmare()
{
    return kfo_mus_situ("nm");
}

// build 50: the online match's own songs for its two big moments (the Claude Music Handoff's assignments):
//   "nm"  - stage 3, KNIGHTMARE: FORGET ME NOT V3 (JustStereo)
//   "lms" - the FINAL TWO, the last SOULs standing: Close To Inevitability (Andrimal)
// Each switches once (the song it brings is checked against the one playing); the final two wins over the Knightmare
// stage: once its song is on, the stage does not take it away. A missing file falls back to KNIGHTMARE (Ann), as before.
// Fixed songs: RANDOM's on / off list is not used here.
function kfo_mus_situ_file(_kind)
{
    var _f = (_kind == "lms") ? "kh_close_to_inevitability.ogg" : "kh_forget_me_not.ogg";
    if (!knight_music_exists(_f))
        _f = "knightmare_knight.ogg";
    return _f;
}

function kfo_mus_situ(_kind)
{
    // (DRBR 1.0.1: a song of your own plays on - kbr_mus_own)
    if (kbr_mus_own())
        return 0;
    var _M = (variable_global_exists("kfo") && is_struct(global.kfo) && variable_struct_exists(global.kfo, "M") && is_struct(global.kfo.M)) ? global.kfo.M : undefined;
    var _now = (is_struct(_M) && variable_struct_exists(_M, "situ")) ? _M.situ : "";
    if (_now == _kind || (_now == "lms" && _kind == "nm"))
        return 0;
    // DRBR 1.0.1: a boss on stage keeps its own music; the moment's song comes when the knights are back (kbr_enc_music)
    var _en = kbr_enc_now();
    if (is_struct(_en) && variable_struct_exists(_en, "music") && knight_music_exists(_en.music))
    {
        if (is_struct(_M))
            _M.situ = _kind;
        return 0;
    }
    var _f = kfo_mus_situ_file(_kind);
    if (!knight_music_exists(_f) || !knight_mus_ok())
        return 0;
    // (a KF Song Pack song picked: it plays on)
    if (knight_kf_on() && global.knight_kf.sid != "")
        return 0;
    var _cur = knight_mus_cur_file();
    if (_cur == "" || _cur == _f)
        return 0;
    if (is_struct(_M))
        _M.situ = _kind;
    var _old = global.batmusic[0];
    knight_mus_cut_ext(30, true);
    array_push(global.knight_mus_q, { k: "song", file: _f, old: _old, fin: 60, t: 33 });
    return 1;
}

// an enemy turn starts / ends: the shared battle has no turns (kept for the hooks in the fight code)
function kfo_turn_begin()
{
    return 0;
}

function kfo_turn_end()
{
    return 0;
}

// DRBR 1.0.3: the party fell some other way than a hit the room took (a piece that takes HP itself; a hidden SOUL touched while
// watching): in a running match this is an OUT like any other - the SOUL breaks, the GAME OVER over the battle, then you watch
// the rest of the round; already OUT, you just keep watching. HP goes back to 1 (hidden) so the battle never sees the party
// down. False when this game is not in a running match (kfo_on_defeat then ends the run as before).
function kfo_on_party_down(_why)
{
    var _M = kfo_match();
    if (is_undefined(_M) || _M.ended || !_M.me || !kfo_run_on() || global.krun.state != "battle")
        return false;
    for (var _s = 0; _s < 3; _s++)
    {
        var _ch = global.char[_s];
        if (_ch > 0 && global.hp[_ch] < 1)
        {
            global.hp[_ch] = 1;
            scr_revive(_s);
        }
    }
    if (!_M.out)
        kbr_local_death(_why);
    else
        kh_dbg_write(["(OUT already: a hit on the hidden SOUL took the last HP - ignored, still watching)"]);
    return true;
}

// the battle ended anyway (the party fell some other way, or the Knight did): this player is out of the match
function kfo_on_defeat(_why)
{
    if (is_undefined(_why))
        _why = "the battle ended";
    var _r = global.krun;
    var _M = kfo_match();
    // build 50: why - on the results, in the host's feed and always in knightfights_debug.log (overlay on or not)
    if (!is_undefined(_M) && !_M.out && _M.me)
        kfo_out_note(_M, _why);
    knight_dmg_sample(_r);
    _r.state = "lost";
    _r.result = "lost";
    _r.ui_done = true;
    global.kbr_det.on = false;
    if (!is_undefined(_M) && !_M.out && _M.me)
    {
        _M.out = true;
        kfo_up({ k: "out", mid: _M.mid, t: round(kbr_now()), ck: _M.R.k, hits: _M.hits, why: _why });
    }
    knight_mus_reset();
    audio_stop_all();
    snd_play(snd_hurt1);
    kbr_end_clean();
    kfo_show_out();
    return 1;
}

// build 50: how this player went out, kept for the results and written to knightfights_debug.log with what the battle
// looked like at that moment (so an out that was not a hit can be traced)
function kfo_out_note(_M, _why)
{
    _M.out_why = _why;
    var _l = ["===== OUT: " + _why + " ====="];
    var _c = (_M.cur_k >= 0) ? kbr_tl_get(_M.tl, _M.cur_k) : undefined;
    array_push(_l, "match time " + kfo_time_text(max(0, kbr_now() - _M.tl.intro)) + "  cycle #" + string(_M.R.k + 1) + "  phase " + string(_M.R.ph)
        + (is_undefined(_c) ? "" : ("  knight " + kbr_ok_name(_c.ok) + "  attack " + kbr_atk_name(_c.ok, _c.ai) + "  stage " + string(_c.st))));
    var _hp = "party:";
    for (var _i = 0; _i < 3; _i++)
    {
        var _ch = global.char[_i];
        _hp += " [" + string(_ch) + ": " + ((_ch > 0) ? (string(global.hp[_ch]) + "/" + string(global.maxhp[_ch])) : "-") + "]";
    }
    var _mf = variable_global_exists("mnfight") ? string(global.mnfight) : "-";
    var _tt = variable_global_exists("turntimer") ? string(global.turntimer) : "-";
    array_push(_l, _hp + "  mnfight " + _mf + "  turntimer " + _tt);
    var _bc = "no battlecontroller";
    with (obj_battlecontroller)
        _bc = "battlecontroller intro " + string(variable_instance_exists(id, "intro") ? intro : "?");
    var _pt = "";
    var _ptb = asset_get_index("obj_ch3_PTB02");
    if (_ptb >= 0 && instance_exists(_ptb))
        _pt = "  PTB02 con " + string(variable_instance_exists(instance_find(_ptb, 0), "con") ? instance_find(_ptb, 0).con : "?");
    var _ke = "  knight_enemy x" + string(instance_number(obj_knight_enemy));
    var _mh = (variable_global_exists("monsterhp") && is_array(global.monsterhp)) ? (string(global.monsterhp[0]) + "/" + string(global.monstermaxhp[0])) : "-";
    var _mo = (variable_global_exists("monster") && is_array(global.monster)) ? string(global.monster[0]) : "-";
    array_push(_l, _bc + _pt + _ke + "  monsterhp " + _mh + "  monster " + _mo);
    kh_dbg_write(_l);
    return 1;
}

// ---------- every step ----------
function kfo_play_tick()
{
    var _o = global.kfo;
    var _M = _o.M;
    if (!is_struct(_M))
        return 0;
    if (!kfo_run_on())
        return 0;
    var _r = global.krun;
    // the connection broke during the match
    if (_o.lost_note != "" && !_M.ended)
    {
        var _why = _o.lost_note;
        _o.lost_note = "";
        _M.ended = true;
        _M.out = true;
        global.kbr_det.on = false;
        kfo_show_lost(_why);
        return 0;
    }
    if (_r.state != "battle")
        return 0;
    kfo_ping_tick();
    if (!_M.ended)
    {
        kbr_step();
        kbr_me_tick();
        // build 51: HOW TO PLAY
        kfo_tut_tick(_M);
    }
    // the results: Z or 10 seconds, then back to the room
    if (_M.ended && _M.res_t >= 0)
    {
        _M.res_t++;
        if (_M.res_t >= 300)
        {
            _M.res_t = -1;
            kfo_back_to_lobby();
        }
    }
    return 1;
}

// the actions of the online prompts: "onl_..." right away, "kfo_..." after the white fade
function kfo_act(_a)
{
    var _o = global.kfo;
    var _M = kfo_match();
    if (_a == "kfo_lobby")
    {
        kfo_back_to_lobby();
        return "";
    }
    // REMATCH: back to the room and READY for the next match (the host sees who wants it: n OF m READY)
    if (_a == "kfo_rematch")
    {
        kfo_back_to_lobby();
        if (kfo_in_room() && !kfo_is_host())
            kfo_up({ k: "ready", on: 1 });
        _o.reopen = true;
        return "";
    }
    // DRBR 1.0.3: END ROUND (the host's GIVE UP box: asked again, then the round ends for everyone)
    if (_a == "onl_endround_ask")
    {
        knight_run_teardown();
        global.interact = 0;
        kfo_endround_prompt();
        return "";
    }
    if (_a == "onl_endround")
    {
        knight_run_teardown();
        global.interact = 0;
        if (!kfo_host_end_round())
            kbr_log("* The round is already over.", c_ltgray);
        return "";
    }
    if (_a == "kfo_quit")
    {
        if (!is_undefined(_M) && !_M.out && !_M.ended && _M.me)
        {
            kfo_out_note(_M, "you gave up (BACKSPACE)");
            _M.out = true;
            kfo_up({ k: "quit", mid: _M.mid, t: round(kbr_now()) });
        }
        kfo_back_to_lobby();
        return "";
    }
    return "";
}

// back to the room (the cold place, or the hub menu on the room's page)
function kfo_back_to_lobby()
{
    var _o = global.kfo;
    // build 47: a watcher from the room tells the host it stopped watching (the room's WATCHING count); the view's settings
    // changed during the match are kept
    if (is_struct(_o.M) && _o.M.spec && !_o.M.ended)
        kfo_up({ k: "unwatch", mid: _o.M.mid });
    kbr_view_shake_back(_o.M);
    kfo_ini_save();
    _o.reopen = false;
    global.kbr_det.on = false;
    knight_exit_run(false);
    return 1;
}

// Backspace in an online fight
function kfo_leave_request()
{
    var _M = kfo_match();
    var _l = ["You will be OUT of this match and go back to the room."];
    var _t = "GIVE UP?";
    if (_M.prac)
    {
        _l = ["The practice ends here and you go back to the room."];
        _t = "END THE PRACTICE?";
    }
    if (_M.out || !_M.me || _M.ended)
    {
        _l = ["You stop watching and go back to the room."];
        _t = "BACK TO THE ROOM?";
    }
    var _opts = [{ t: "Stay", a: "resume", cancel: true }, { t: "Leave", a: "kfo_quit" }];
    // DRBR 1.0.3: the host can end the round for everyone here (it asks again first)
    if (kfo_host_can_end_round() && !_M.ended)
    {
        array_push(_l, "HOST: END ROUND ends it for everyone.");
        array_push(_opts, { t: "END ROUND", a: "onl_endround_ask" });
    }
    var _p = knight_prompt_new(_t, _l, _opts);
    return _p;
}

// DRBR 1.0.3: END ROUND, asked again (the host's GIVE UP box; the room's END ROUND row asks with its own box)
function kfo_endround_prompt()
{
    return knight_prompt_new("END THE ROUND?", ["The round ends now for everyone.", "The players still standing are placed by HP", "(the most HP in % wins), as when the time runs out."],
        [{ t: "Keep playing", a: "resume", cancel: true }, { t: "End the round", a: "onl_endround" }]);
}

// ---------- OUT / results / lost ----------
// standing order: still in (most HP first), then out (best place first)
function kfo_rank(_pl)
{
    var _l = [];
    for (var _i = 0; _i < array_length(_pl); _i++)
        array_push(_l, _pl[_i]);
    for (var _i = 1; _i < array_length(_l); _i++)
    {
        var _x = _l[_i];
        var _j = _i - 1;
        while (_j >= 0 && kfo_rank_before(_x, _l[_j]))
        {
            _l[_j + 1] = _l[_j];
            _j--;
        }
        _l[_j + 1] = _x;
    }
    return _l;
}

function kfo_rank_before(_a, _b)
{
    var _aa = kfo_jn(_a, "al", 0);
    var _ba = kfo_jn(_b, "al", 0);
    if (_aa != _ba)
        return _aa > _ba;
    if (_aa == 1)
    {
        var _fa = kfo_jn(_a, "hp", 0) / max(1, kfo_jn(_a, "mh", 150));
        var _fb = kfo_jn(_b, "hp", 0) / max(1, kfo_jn(_b, "mh", 150));
        if (_fa != _fb)
            return _fa > _fb;
        return kfo_jn(_a, "g", 0) > kfo_jn(_b, "g", 0);
    }
    var _ap = kfo_jn(_a, "pl", 0);
    var _bp = kfo_jn(_b, "pl", 0);
    if (_ap == 0)
        return false;
    return (_bp == 0) || (_ap < _bp);
}

function kfo_time_text(_ticks)
{
    var _s = max(0, floor(_ticks / 30));
    var _ss = _s mod 60;
    return string(_s div 60) + ":" + ((_ss < 10) ? "0" : "") + string(_ss);
}

function kfo_result_lines()
{
    var _o = global.kfo;
    var _M = kfo_match();
    var _l = [];
    if (is_undefined(_M) || !is_struct(_M.res))
        return _l;
    var _pl = kfo_ja(_M.res, "pl");
    for (var _i = 0; _i < array_length(_pl) && _i < 8; _i++)
    {
        var _p = _pl[_i];
        var _place = kfo_jn(_p, "pl", 0);
        var _rank = (_place > 0) ? (string(_place) + ". ") : "- ";
        var _surv = (kfo_jn(_p, "al", 0) == 1) ? "ALIVE" : kfo_time_text(kfo_jn(_p, "ft", 0));
        array_push(_l, [_rank + knight_fit(kfo_js(_p, "n", "?"), 190), _surv, string(kfo_jn(_p, "sg", 0)) + " SKILLS", kfo_jn(_p, "pid", -2) == _o.my]);
    }
    // build 50: how you went out (a hit that emptied your HP, giving up, or the battle itself ending)
    if (variable_struct_exists(_M, "out_why") && _M.out_why != "")
        array_push(_l, ["~", "You went out: " + _M.out_why + "."]);
    return _l;
}

function kfo_result_title()
{
    var _o = global.kfo;
    var _M = kfo_match();
    if (is_undefined(_M) || !is_struct(_M.res))
        return "MATCH OVER";
    var _r = _M.res;
    var _w = kfo_ja(_r, "wid");
    if (kfo_jn(_r, "sn", 2) <= 1 && array_length(_w) <= 1 && _M.prac)
        return "PRACTICE OVER: " + kfo_time_text(kfo_jn(_r, "dur", 0));
    var _iw = false;
    for (var _i = 0; _i < array_length(_w); _i++)
    {
        if (_w[_i] == _o.my)
            _iw = true;
    }
    if (_iw)
        return (array_length(_w) > 1) ? "A TIE - YOU WIN TOO!" : "YOU WIN!";
    if (array_length(_w) == 0)
        return "NOBODY WINS";
    if (array_length(_w) > 1)
        return "A TIE: " + string(array_length(_w)) + " WINNERS!";
    return string_upper(knight_fit(kfo_js(_r, "wn", "?"), 300)) + " WINS!";
}

function kfo_out_title()
{
    var _M = kfo_match();
    if (_M.place > 0)
        return "OUT!  #" + string(_M.place) + " OF " + string(_M.sn);
    return "OUT!";
}

function kfo_show_out()
{
    var _p = knight_prompt_new(kfo_out_title(), kfo_standing_lines(8), [{ t: "Back to the room", a: "kfo_lobby" }]);
    _p.kfo_live = true;
    _p.delay = 20;
    return _p;
}

function kfo_standing_lines(_max)
{
    var _o = global.kfo;
    var _M = kfo_match();
    var _out = [];
    if (is_undefined(_M) || !is_struct(_M.st))
        return _out;
    var _pl = kfo_rank(kfo_ja(_M.st, "pl"));
    for (var _i = 0; _i < array_length(_pl) && _i < _max; _i++)
    {
        var _p = _pl[_i];
        var _me = (kfo_jn(_p, "pid", -2) == _o.my);
        var _st = (kfo_jn(_p, "al", 0) == 1) ? (string(round(kfo_jn(_p, "hp", 0))) + " HP") : kbr_out_text(kfo_jn(_p, "pl", 0));
        array_push(_out, [knight_fit(kfo_js(_p, "n", "?"), 220), _st, "", _me]);
    }
    return _out;
}

function kfo_show_results()
{
    var _r = global.krun;
    var _M = kfo_match();
    kbr_end_clean();
    _r.state = "finished";
    _r.ui_done = true;
    global.kbr_det.on = false;
    knight_mus_reset();
    snd_play(snd_won);
    with (obj_knight_prompt)
        instance_destroy();
    var _rem = "Rematch (READY)";
    if (kfo_is_host())
        _rem = "Rematch (to the room)";
    var _lines = kfo_result_lines();
    var _p = knight_prompt_new(kfo_result_title(), _lines, [{ t: _rem, a: "kfo_rematch" }, { t: "Back to the room", a: "kfo_lobby" }]);
    _p.kfo_live = true;
    _p.delay = 20;
    _M.res_t = 0;
    return _p;
}

function kfo_show_lost(_why)
{
    var _r = global.krun;
    if (kfo_run_on())
        kbr_end_clean();
    _r.state = "finished";
    _r.ui_done = true;
    with (obj_knight_prompt)
        instance_destroy();
    knight_unfreeze();
    var _p = knight_prompt_new("CONNECTION LOST", [_why, "The match goes on without you."], [{ t: "Back to the hub", a: "kfo_lobby" }]);
    _p.delay = 20;
    return _p;
}

// (the SEND box of build 43-44 is gone: skills replace it)
function kfo_send_refresh()
{
    return 0;
}

// the OUT / results prompt follows the match while it is open
function kfo_prompt_refresh()
{
    var _M = kfo_match();
    if (is_undefined(_M))
        return 0;
    if (_M.ended && is_struct(_M.res))
    {
        title = kfo_result_title();
        lines = kfo_result_lines();
    }
    else if (_M.out)
    {
        title = kfo_out_title();
        lines = kfo_standing_lines(8);
    }
    return 1;
}

// ---------- the battle HUD (online_br_hud.gml draws it) ----------
function kfo_hud_lines(_l)
{
    return _l;
}

function kfo_hud_draw(xx, yy, _y0)
{
    return kbr_hud_draw(xx, yy);
}
