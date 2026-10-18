
// ===== Build 41: practice from any attack, instant retry, fast-forward, fight stats =====

function knight_cfg_num(_c, _f)
{
    if (!is_struct(_c) || !variable_struct_exists(_c, _f))
        return 0;
    var _v = variable_struct_get(_c, _f);
    if (is_real(_v))
        return _v;
    // build 43: bitwise operators give int64 values, and is_real() is false for those (the Remix knight switches were
    // stored that way and then read back as 0 = "all on")
    if (is_string(_v) || is_undefined(_v) || is_array(_v) || is_struct(_v))
        return 0;
    return real(_v);
}

// ---------- practice: START AT / REPEAT ----------
// cfg.p_mode: 0 = normal, 1 = START AT (the real fight starts at attack p_atk), 2 = REPEAT (the knight uses only that attack and
// cannot fall). The attack is forced through the fight's own practice code path (Other_10's practice branch, Kaizo's named
// attacks), the same one the in-fight attack picker uses, so every attack starts exactly as it does there.
function knight_pmode(_c)
{
    if (knight_lu_kind_of(_c) != "" || _c.mode != 0 || _c.practice)
        return 0;
    return clamp(knight_cfg_num(_c, "p_mode"), 0, 2);
}

// position of attack _i in the fight's natural order (unused and finale attacks left out) - used for START AT's HP and pacing
function knight_atk_pos(_k, _i)
{
    var _l = knight_reg(_k).atk;
    if (_i < 0 || _i >= array_length(_l))
        return 0;
    if (_l[_i][3] & 2)
        return -1;
    var _n = 0;
    for (var _j = 0; _j < _i; _j++)
    {
        if (_l[_j][3] == 0)
            _n++;
    }
    return _n;
}

function knight_atk_label(_k, _i)
{
    var _l = knight_reg(_k).atk;
    if (_i < 0 || _i >= array_length(_l))
        return "?";
    return ((_l[_i][3] & 2) ? "FINALE" : ("P" + string(_l[_i][0]))) + "  " + _l[_i][2];
}

// the attack this knight has to use now (index into its list), or -1 when its own list decides. self = the knight.
function knight_force_want()
{
    if (!knight_active())
        return -1;
    var _r = global.krun;
    if (_r.state != "battle")
        return -1;
    if (is_struct(global.knight_lu) && global.knight_lu.ready)
    {
        var _lu = global.knight_lu;
        if ((_lu.kind != "remix" && _lu.kind != "online") || _lu.finale || id != _lu.inst[_lu.act] || _lu.plan_k != _lu.act)
            return -1;
        return _lu.plan_i;
    }
    var _pm = knight_pmode(_r.cfg);
    if (_pm == 0)
        return -1;
    var _l = knight_reg(knight_cur_knight()).atk;
    var _i = knight_cfg_num(_r.cfg, "p_atk");
    if (_i < 0 || _i >= array_length(_l))
        return -1;
    if (_pm == 2)
    {
        // REPEAT: the knight never falls (full HP every turn)
        global.monsterhp[0] = global.monstermaxhp[0];
        return _i;
    }
    if (variable_instance_exists(id, "kh_started") && kh_started)
        return -1;
    kh_started = true;
    knight_start_at_apply(_i);
    return _i;
}

// START AT: the knight's HP and the fight's pacing jump to where that attack comes in a full fight
function knight_start_at_apply(_i)
{
    var _r = global.krun;
    var _k = knight_cur_knight();
    var _p = knight_pace_now(_k);
    var _pos = knight_atk_pos(_k, _i);
    var _max = global.monstermaxhp[0];
    if (_pos < 0)
    {
        _r.eturns = max(_r.eturns, _p.tmin);
        global.monsterhp[0] = min(global.monsterhp[0], max(1, floor(_max * _p.gate) - 1));
        return 0;
    }
    if (_p.tmin <= 0 || _pos <= 0)
        return 0;
    _r.eturns = max(_r.eturns, _pos);
    var _line = floor(_max * (1 - ((1 - _p.gate) * min(1, _pos / _p.tmin))));
    global.monsterhp[0] = min(global.monsterhp[0], max(1, _line));
    return 1;
}

// Other_10 of Normal / Supercharged / Violet / Thorn / Cyan: "if (knight_force_sel() || practicemode)" before the practice branch
function knight_force_sel()
{
    if (!variable_instance_exists(id, "prac_list"))
        return false;
    if (variable_instance_exists(id, "practicemode") && practicemode)
    {
        if (prac_sel >= 0 && prac_sel < array_length(prac_list))
            knight_stats_atk_set(prac_list[prac_sel][2]);
        return false;
    }
    var _i = knight_force_want();
    if (_i < 0 || _i >= array_length(prac_list))
    {
        knight_stats_atk_set(knight_atk_natural());
        return false;
    }
    prac_sel = _i;
    knight_stats_atk_set(prac_list[_i][2]);
    return true;
}

// the attack the fight's own list is about to pick (phase / turn already counted up by Other_10)
function knight_atk_natural()
{
    if (!variable_instance_exists(id, "prac_list") || !variable_instance_exists(id, "phase"))
        return "";
    var _ph = phase;
    var _t = variable_instance_exists(id, "phaseturn") ? phaseturn : 0;
    if (_ph == 4)
        _t = (variable_instance_exists(id, "phase4turn") ? phase4turn : 0) + 1;
    for (var _j = 0; _j < array_length(prac_list); _j++)
    {
        if (prac_list[_j][0] == _ph && prac_list[_j][1] == _t)
            return prac_list[_j][2];
    }
    if (_ph == 4)
        return (_t == 2) ? "The glow" : "Phase 4";
    return "Phase " + string(_ph) + ", turn " + string(_t);
}

// top of Kaizo Knight's Other_10: its attacks are named structs (kaizo_attack)
function knight_force_kz()
{
    var _i = knight_force_want();
    var _l = knight_reg(knight_cur_knight()).atk;
    if (_i >= 0 && _i < array_length(_l) && is_string(_l[_i][1]) && variable_instance_exists(id, _l[_i][1]))
        kaizo_attack = _l[_i][1];
    if (variable_instance_exists(id, "kaizo_attack") && is_string(kaizo_attack) && variable_instance_exists(id, kaizo_attack))
    {
        var _at = variable_instance_get(id, kaizo_attack);
        if (is_struct(_at) && variable_struct_exists(_at, "attackName"))
            knight_stats_atk_set(_at.attackName);
    }
    return 0;
}

// ---------- fight stats ----------
function knight_stats_new()
{
    return { dealt: [0, 0, 0, 0, 0, 0], taken: [0, 0, 0, 0, 0, 0], atk: [], cur: -1, pend: "", turns: 0, page: 0 };
}

function knight_stats_on()
{
    return knight_active() && is_struct(global.krun) && variable_struct_exists(global.krun, "st");
}

// the attack chosen for the coming enemy turn
function knight_stats_atk_set(_n)
{
    if (!knight_stats_on())
        return 0;
    global.krun.st.pend = is_string(_n) ? _n : "";
    return 0;
}

// an enemy turn starts (mnfight -> 2): count the attack it uses
function knight_stats_turn_begin()
{
    if (!knight_stats_on())
        return 0;
    var _st = global.krun.st;
    var _n = _st.pend;
    if (_n == "")
    {
        _n = "Turn " + string(_st.turns + 1);
        if (variable_global_exists("monsterattackname") && is_string(global.monsterattackname[0]) && string_length(string_replace_all(global.monsterattackname[0], " ", "")) > 0)
            _n = global.monsterattackname[0];
    }
    var _who = "";
    if (knight_lu_ready() || global.krun.mode == 1)
        _who = knight_reg(knight_cur_knight()).short + ": ";
    _n = _who + _n;
    _st.pend = "";
    _st.turns++;
    for (var _i = 0; _i < array_length(_st.atk); _i++)
    {
        if (_st.atk[_i].n == _n)
        {
            _st.atk[_i].seen++;
            _st.cur = _i;
            return _i;
        }
    }
    array_push(_st.atk, { n: _n, seen: 1, hits: 0 });
    _st.cur = array_length(_st.atk) - 1;
    return _st.cur;
}

function knight_stats_hit()
{
    if (!knight_stats_on())
        return 0;
    var _st = global.krun.st;
    if (_st.cur >= 0 && _st.cur < array_length(_st.atk) && variable_global_exists("mnfight") && global.mnfight == 2)
        _st.atk[_st.cur].hits++;
    return 0;
}

// a hit on the knight that got through (self = whoever dealt it: a hero, a spell, the hub)
function knight_stats_dealt(_d)
{
    if (_d <= 0 || !knight_stats_on())
        return 0;
    var _c = 0;
    if (is_struct(self))
        _c = 0;
    else if (variable_instance_exists(id, "caster") && is_real(caster) && caster >= 0 && caster < 3)
        _c = global.char[caster];
    else if (variable_instance_exists(id, "myself") && is_real(myself) && myself >= 0 && myself < 3 && global.charinstance[myself] == id)
        _c = global.char[myself];
    if (!is_real(_c) || _c < 0 || _c > 5)
        _c = 0;
    global.krun.st.dealt[_c] += _d;
    return _c;
}

function knight_stats_taken(_c, _d)
{
    if (!knight_stats_on() || _c < 1 || _c > 5 || _d <= 0)
        return 0;
    global.krun.st.taken[_c] += _d;
    return 0;
}

// the FIGHT STATS box: damage per member, then the attacks (most hits first), 4 per page (8 before 1.0.1)
function knight_stats_per_page()
{
    // (DRBR 1.0.1: 4 - the box's lines are in the menu's size)
    return 4;
}

function knight_stats_lines(_r)
{
    var _st = _r.st;
    var _l = [];
    array_push(_l, ["s", "DAMAGE", "DEALT", "TAKEN", false]);
    var _seen = [0, 0, 0, 0, 0, 0];
    for (var _i = 0; _i < 3; _i++)
    {
        var _c = _r.party[_i];
        if (_c < 1 || _c > 5 || _seen[_c])
            continue;
        _seen[_c] = 1;
        array_push(_l, ["s", "  " + knight_char_proper(_c), string(floor(_st.dealt[_c])), string(floor(_st.taken[_c])), false]);
    }
    if (_st.dealt[0] > 0)
        array_push(_l, ["s", "  Other", string(floor(_st.dealt[0])), "-", false]);
    var _n = array_length(_st.atk);
    array_push(_l, ["s", "ATTACKS", "USED", "HITS", false]);
    if (_n == 0)
    {
        array_push(_l, ["~", "No enemy turns were played."]);
        return _l;
    }
    var _ord = knight_stats_order(_st);
    var _per = knight_stats_per_page();
    var _pages = max(1, ceil(_n / _per));
    var _p0 = clamp(_st.page, 0, _pages - 1) * _per;
    for (var _i = _p0; _i < min(_n, _p0 + _per); _i++)
    {
        var _a = _st.atk[_ord[_i]];
        array_push(_l, ["s", "  " + _a.n, "x" + string(_a.seen), string(_a.hits), _a.hits == 0]);
    }
    var _foot = string(_st.turns) + " turns, " + string(_n) + ((_n == 1) ? " attack." : " attacks.") + " Yellow: never hit you.";
    if (_pages > 1)
        _foot = "Page " + string((_p0 div _per) + 1) + "/" + string(_pages) + ". " + _foot;
    array_push(_l, ["~", _foot]);
    return _l;
}

// attack indices: most hits first, then most used, then first seen
function knight_stats_order(_st)
{
    var _n = array_length(_st.atk);
    var _o = [];
    for (var _i = 0; _i < _n; _i++)
        _o[_i] = _i;
    for (var _i = 1; _i < _n; _i++)
    {
        var _j = _i;
        while (_j > 0)
        {
            var _a = _st.atk[_o[_j - 1]];
            var _b = _st.atk[_o[_j]];
            if (_b.hits > _a.hits || (_b.hits == _a.hits && _b.seen > _a.seen))
            {
                var _t = _o[_j];
                _o[_j] = _o[_j - 1];
                _o[_j - 1] = _t;
                _j--;
            }
            else
                break;
        }
    }
    return _o;
}

function knight_show_stats()
{
    var _r = global.krun;
    with (obj_knight_prompt)
        instance_destroy();
    _r.stats_seen = true;
    var _n = array_length(_r.st.atk);
    var _opts = [{ t: "Back", a: "stats_back", cancel: true }];
    if (_n > knight_stats_per_page())
        array_push(_opts, { t: "Next page", a: "stats_more" });
    var _p = knight_prompt_new((_r.mode == 1) ? "KNIGHT RUSH STATS" : "FIGHT STATS", knight_stats_lines(_r), _opts);
    _p.wide = true;
    return _p;
}

// ---------- hotkeys: R = restart the fight, hold TAB = fast-forward ----------
function knight_hotkeys_on()
{
    return knight_active() && !knight_cfg_flag(global.krun.cfg, "nohotkeys");
}

function knight_quick_retry()
{
    var _r = global.krun;
    if (_r.mode == 0 && !_r.fcommitted && _r.state == "battle")
        knight_fight_commit("abandon");
    if (_r.mode == 1 && !_r.runcommitted && (_r.state == "battle" || _r.state == "rushwait"))
        knight_rush_finish("abandon");
    snd_play(snd_select);
    knight_rematch();
    return 1;
}

// fast-forward: talk, scenes, the arena intro and the walk after the fight run four times as fast while TAB is held. Never while
// bullets are flying or the FIGHT bars are up.
function knight_ff_on()
{
    if (!knight_active() || global.knight_frozen || !knight_hotkeys_on())
        return false;
    // never online: the shared match runs on the shared clock (TAB is the player list there)
    if (kfo_cfg_online(global.krun.cfg))
        return false;
    if (!keyboard_check(vk_tab))
        return false;
    if (instance_exists(obj_knight_prompt) || instance_exists(obj_knight_menu))
        return false;
    var _r = global.krun;
    if (_r.state == "arena" || _r.state == "won" || _r.state == "finished")
        return true;
    if (_r.state != "battle")
        return false;
    if (variable_global_exists("mnfight") && global.mnfight == 2)
        return false;
    if (instance_exists(obj_heart) || instance_exists(obj_attackpress))
        return false;
    return true;
}

// ---------- music: short fades instead of dead stops, new songs fade in ----------
// The battle song is global.batmusic[0] (the sound or the stream from snd_init) and global.batmusic[1] (its playing copy), as
// everywhere in the game; the fades are the game's own mus_volume (frames, times the music volume setting). Stops that wait for a
// fade to end and song changes wait in global.knight_mus_q and run from the hub controller's Step (knight_mus_tick).
global.knight_mus_q = [];

function knight_mus_ok()
{
    return variable_global_exists("batmusic") && is_array(global.batmusic) && array_length(global.batmusic) >= 2;
}

// nothing pending any more: fades still running end now (their songs stop), song changes still to come are dropped (the hub
// stops every sound itself when it leaves or restarts a fight; a new room has no battle song to change)
function knight_mus_reset()
{
    var _q = global.knight_mus_q;
    global.knight_mus_q = [];
    for (var _i = 0; _i < array_length(_q); _i++)
    {
        if (_q[_i].k == "stop")
            knight_mus_run(_q[_i]);
    }
}

// the battle song fades out over _frames and stops when the fade is over, where the fight used to stop it dead
function knight_mus_cut(_frames)
{
    return knight_mus_cut_ext(_frames, false);
}

// the same; _free: the stream is also freed after the fade (a song that is replaced for good)
function knight_mus_cut_ext(_frames, _free)
{
    if (!knight_mus_ok())
        return 0;
    var _snd = global.batmusic[0];
    var _inst = global.batmusic[1];
    // (without the hub controller, which runs the queue, the fight's own dead stop)
    if (_frames <= 0 || !audio_is_playing(_inst) || !instance_exists(obj_knight_ctrl))
    {
        snd_stop(_snd);
        if (_free)
            snd_free(_snd);
        return 1;
    }
    mus_volume(_inst, 0, _frames);
    array_push(global.knight_mus_q, { k: "stop", snd: _snd, inst: _inst, dofree: _free, t: _frames + 1 });
    return 1;
}

// _snd (a sound, or a stream from snd_init) becomes the battle song, fading in from silence over _fadein frames. A different
// song that is still playing then (a path that never stopped it) fades out over a second instead of playing on under it.
function knight_mus_switch(_snd, _fadein)
{
    if (knight_mus_ok() && global.batmusic[0] != _snd && audio_is_playing(global.batmusic[1]))
        knight_mus_cut(30);
    global.batmusic[0] = _snd;
    global.batmusic[1] = mus_loop(_snd);
    if (_fadein > 0)
    {
        mus_volume(global.batmusic[1], 0, 0);
        mus_volume(global.batmusic[1], 1, _fadein);
    }
    return global.batmusic[1];
}

function knight_mus_battle_on()
{
    var _on = false;
    with (obj_battlecontroller)
    {
        if (!variable_instance_exists(id, "intro") || intro != 2)
            _on = true;
    }
    return _on;
}

function knight_mus_run(_e)
{
    if (_e.k == "stop")
    {
        // the same song started again meanwhile: only the old copy stops; else the whole song, as the fight did
        if (knight_mus_ok() && global.batmusic[0] == _e.snd && global.batmusic[1] != _e.inst)
            audio_stop_sound(_e.inst);
        else
            snd_stop(_e.snd);
        if (_e.dofree && !(knight_mus_ok() && global.batmusic[0] == _e.snd && global.batmusic[1] != _e.inst))
            snd_free(_e.snd);
        return 1;
    }
    if (_e.k == "song")
    {
        // still wanted: the battle goes on, the lineup is still there and nobody changed the song meanwhile
        if (!knight_mus_ok() || global.batmusic[0] != _e.old || !knight_lu_on() || !knight_mus_battle_on())
            return 0;
        knight_mus_switch(snd_init(_e.file), _e.fin);
        return 1;
    }
    return 0;
}

function knight_mus_tick()
{
    if (global.knight_frozen || array_length(global.knight_mus_q) == 0)
        return 0;
    var _i = 0;
    while (_i < array_length(global.knight_mus_q))
    {
        var _e = global.knight_mus_q[_i];
        _e.t -= 1;
        if (_e.t > 0)
        {
            _i++;
            continue;
        }
        array_delete(global.knight_mus_q, _i, 1);
        knight_mus_run(_e);
    }
    return 1;
}

// the song knight _k plays with SONG: MOD DEFAULT (the same file its fight would start)
function knight_mus_default_file(_k)
{
    var _f = knight_default_music(_k);
    var _ren = knight_reg(_k).music_rename;
    if (is_struct(_ren) && variable_struct_exists(_ren, _f))
        _f = variable_struct_get(_ren, _f);
    if (knight_music_exists(_f))
        return _f;
    return "knight.ogg";
}

// the file the battle song was started from ("" when it is not a stream from snd_init)
function knight_mus_cur_file()
{
    if (!knight_mus_ok())
        return "";
    var _s0 = global.batmusic[0];
    var _f = "";
    with (obj_astream)
    {
        if (mystream == _s0)
            _f = songname;
    }
    return _f;
}

// Tag Team: the knight who takes over brings their own song (with SONG: MOD DEFAULT; a chosen song plays on). The old song
// fades out over a second, the new one fades in over two.
function knight_mus_takeover(_k)
{
    if (!knight_active() || !knight_mus_ok() || knight_cfg_num(global.krun.cfg, "song") != 0)
        return 0;
    var _f = knight_mus_default_file(_k);
    var _cur = knight_mus_cur_file();
    if (_cur == "" || _cur == _f)
        return 0;
    var _old = global.batmusic[0];
    knight_mus_cut_ext(30, true);
    array_push(global.knight_mus_q, { k: "song", file: _f, old: _old, fin: 60, t: 33 });
    return 1;
}
