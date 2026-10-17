
// ===== Knight Hub run lifecycle =====
// krun.state: "arena" (cutscene before the fight) -> "battle" -> "won" | "failed" (No-Hit) | "lost"
//             rush only: "rushwait" (between fights), "done"
// A run is committed to the records exactly once per fight (fcommitted) and once per rush (runcommitted).
global.knight_frozen = false;
global.knight_frozen_list = undefined;
global.knight_run_counter = 0;

function knight_flags_list()
{
    return [9, 50, 51, 52, 53, 54, 115, 456, 1263, 1264];
}

function knight_arr_copy(_a, _n)
{
    var _o = [];
    for (var _i = 0; _i < _n; _i++)
        _o[_i] = (_i < array_length(_a)) ? _a[_i] : 0;
    return _o;
}

// ---------- story-state snapshot ----------
function knight_snapshot_take()
{
    if (!is_undefined(global.knight_orig))
        return false;
    var _s = {};
    _s.char = [global.char[0], global.char[1], global.char[2]];
    _s.spell = [];
    for (var _c = 0; _c <= 5; _c++)
    {
        var _row = [];
        for (var _i = 0; _i < 12; _i++)
            _row[_i] = (_c < array_length(global.spell) && is_array(global.spell[_c]) && _i < array_length(global.spell[_c])) ? global.spell[_c][_i] : 0;
        _s.spell[_c] = _row;
    }
    _s.eq = [knight_arr_copy(global.charweapon, 6), knight_arr_copy(global.chararmor1, 6), knight_arr_copy(global.chararmor2, 6)];
    _s.hp = knight_arr_copy(global.hp, 6);
    _s.maxhp = knight_arr_copy(global.maxhp, 6);
    _s.at = knight_arr_copy(global.at, 6);
    _s.df = knight_arr_copy(global.df, 6);
    _s.mag = knight_arr_copy(global.mag, 6);
    _s.item = knight_arr_copy(global.item, 13);
    _s.tension = global.tension;
    _s.plot = global.plot;
    var _fl = knight_flags_list();
    _s.flags = [];
    for (var _i = 0; _i < array_length(_fl); _i++)
        _s.flags[_i] = global.flag[_fl[_i]];
    _s.tflags = [];
    for (var _i = 0; _i < 7; _i++)
        _s.tflags[_i] = global.tempflag[90 + _i];
    _s.orighp = [global.orighpkris, global.orighpsusie, global.orighpralsei];
    _s.losses = variable_global_exists("knight_battle_losses") ? global.knight_battle_losses : 0;
    global.knight_orig = _s;
    return true;
}

// kind: "leave"    = player walks away from the hub (everything back, snapshot dropped by the caller)
//       "hub"      = back to the hub between fights (party/items/HP/flags back; spells stay as configured)
//       "continue" = story goes on after a win (like "leave" but the story owns plot)
function knight_snapshot_restore(_kind)
{
    var _s = global.knight_orig;
    if (is_undefined(_s))
        return false;
    global.char = [_s.char[0], _s.char[1], _s.char[2]];
    if (_kind != "hub")
    {
        for (var _c = 0; _c <= 5; _c++)
        {
            for (var _i = 0; _i < 12; _i++)
                global.spell[_c][_i] = _s.spell[_c][_i];
        }
        // (the game's own four: a custom character's gear stays as the hub set it - it is not part of the story)
        for (var _i = 0; _i < 5; _i++)
        {
            global.charweapon[_i] = _s.eq[0][_i];
            global.chararmor1[_i] = _s.eq[1][_i];
            global.chararmor2[_i] = _s.eq[2][_i];
        }
    }
    for (var _i = 0; _i < 6; _i++)
    {
        global.hp[_i] = _s.hp[_i];
        global.maxhp[_i] = _s.maxhp[_i];
        global.at[_i] = _s.at[_i];
        global.df[_i] = _s.df[_i];
        global.mag[_i] = _s.mag[_i];
    }
    for (var _i = 0; _i < 13; _i++)
        global.item[_i] = _s.item[_i];
    global.tension = _s.tension;
    var _fl = knight_flags_list();
    for (var _i = 0; _i < array_length(_fl); _i++)
        global.flag[_fl[_i]] = _s.flags[_i];
    for (var _i = 0; _i < 7; _i++)
        global.tempflag[90 + _i] = _s.tflags[_i];
    global.orighpkris = _s.orighp[0];
    global.orighpsusie = _s.orighp[1];
    global.orighpralsei = _s.orighp[2];
    if (variable_global_exists("knight_battle_losses"))
        global.knight_battle_losses = _s.losses;
    if (_kind == "leave")
        global.plot = _s.plot;
    if (_kind != "hub")
        knight_equip_refresh();
    scr_refreshchar();
    return true;
}

// ---------- freeze: stop the whole game under a prompt ----------
function knight_freeze()
{
    if (global.knight_frozen)
        return 0;
    global.knight_frozen = true;
    knight_speed_reset();
    if (sprite_exists(global.knight_freeze_spr))
        sprite_delete(global.knight_freeze_spr);
    global.knight_freeze_spr = sprite_create_from_surface(application_surface, 0, 0, surface_get_width(application_surface), surface_get_height(application_surface), false, false, 0, 0);
    audio_pause_all();
    // with a Tag Team / Remix lineup only what is running now is switched off (and later back on): the knights waiting at the
    // back must stay off (knight_activate_all_safe)
    global.knight_frozen_list = undefined;
    // build 50: always only what is running now is switched off, and only that comes back on - a pause in the middle of a
    // cutscene used to wake up everything the cutscene had switched off itself (the party's followers with no player to
    // follow: "Unable to find any instance for object index ... obj_mainchara" in obj_caterpillarchara's End Step)
    if (true)
    {
        var _fl = [];
        with (all)
        {
            if (object_index != obj_knight_ctrl && object_index != obj_time && object_index != obj_gamecontroller && object_index != obj_border_controller)
                array_push(_fl, id);
        }
        global.knight_frozen_list = _fl;
        for (var _i = 0; _i < array_length(_fl); _i++)
            instance_deactivate_object(_fl[_i]);
        return 0;
    }
    with (obj_knight_ctrl)
    {
        instance_deactivate_all(true);
    }
    // the input / window machinery must keep running (same set the game's own pause keeps)
    instance_activate_object(obj_time);
    instance_activate_object(obj_gamecontroller);
    instance_activate_object(obj_border_controller);
}

function knight_unfreeze()
{
    if (global.knight_frozen)
    {
        knight_activate_all_safe();
        audio_resume_all();
    }
    global.knight_frozen = false;
    if (sprite_exists(global.knight_freeze_spr))
        sprite_delete(global.knight_freeze_spr);
    global.knight_freeze_spr = -1;
}

// ---------- run object ----------
function knight_run_new(_l)
{
    global.knight_run_counter++;
    var _r = {
        id: global.knight_run_counter, launch: _l, src: _l.src, cfg: _l.cfg, plan: _l.plan, pos: 0,
        mode: _l.cfg.mode, party: knight_party_compact(_l.cfg.party),
        state: "arena", frames: 0, dmg: 0, hits: 0, failed: false, fcommitted: false, attcounted: false,
        prevhp: [0, 0, 0, 0, 0, 0], hp1done: false, gprev: undefined, hp_after: [0, 0, 0, 0, 0, 0],
        fights: [], tot_t: 0, tot_dmg: 0, tot_hits: 0,
        result: "", story_result: 2, ui_done: false, runcommitted: false,
        reveal: _l.reveal, reveal_t: 0, practice: false, rec: false, msg: "", fx: 0, newrec: "", st: knight_stats_new(), stats_seen: false
    };
    knight_ch_reset(_r);
    return _r;
}

function knight_active()
{
    return (variable_global_exists("knight_run") && global.knight_run == 1 && is_struct(global.krun));
}

function knight_cur_knight()
{
    if (is_struct(global.knight_lu) && global.knight_lu.ready)
        return knight_lu_cur();
    return global.krun.plan[global.krun.pos];
}

// records are kept per knight; a Tag Team or an Attack Remix has its own table
function knight_run_rec_key(_r)
{
    var _kind = knight_lu_kind_of(_r.cfg);
    if (_kind != "")
        return _kind;
    return knight_reg(_r.plan[_r.pos]).key;
}

function knight_noheal_active()
{
    if (!knight_active())
        return false;
    return (global.krun.cfg.c_heal == 1 && global.krun.state == "battle");
}

function knight_reset_run_state()
{
    global.knight_lockslots = [0, 0, 0];
    if (variable_global_exists("knight_battle_losses"))
        global.knight_battle_losses = 0;
    if (variable_global_exists("knight_mode"))
        global.knight_mode = 0;
    global.flag[9] = 0;
    global.lightsplitter_active = false;
    global.lightsplitter_creating_backup = false;
    global.lightsplitter_orb_flash = 0;
    global.snowbreak = false;
    global.vipractice = false;
    global.turnskip = 0;
    global.jokat = 0;
    global.jokdf = 0;
    global.jokate = 0;
    global.jokdfe = 0;
    global.chapter_return = 0;
    global.knight_hits = 0;
    if (variable_global_exists("mnfight"))
        global.mnfight = 0;
    if (variable_global_exists("myfight"))
        global.myfight = 0;
}

function knight_goto_arena()
{
    knight_activate_all_safe();
    knight_mus_reset();
    snd_free_all();
    snd_stop_all();
    if (room == room_dw_snow_zone)
        room_restart();
    else
        room_goto(room_dw_snow_zone);
}

// ---------- per-fight setup (launch, rematch, next rush fight) ----------
function knight_fight_setup()
{
    var _r = global.krun;
    var _k = _r.plan[_r.pos];
    var _reg = knight_reg(_k);
    var _c = _r.cfg;
    _r.state = "arena";
    _r.frames = 0;
    _r.dmg = 0;
    _r.hits = 0;
    _r.failed = false;
    _r.fcommitted = false;
    _r.hp1done = false;
    _r.gprev = undefined;
    _r.ui_done = false;
    _r.msg = "";
    _r.newrec = "";
    _r.reveal_t = 0;
    _r.song_t = 0;
    knight_ch_reset(_r);
    var _kind = knight_lu_kind_of(_c);
    _r.practice = (_c.practice == 1 && _reg.has_practice && _r.mode == 0 && _kind == "");
    _r.rec = ((_r.mode == 1) || !_reg.joke) && !(variable_struct_exists(_c, "rparty") && _c.rparty == 1) && !knight_cfg_flag(_c, "infhp");
    if (_kind == "tag" && knight_reg(_c.knight2).joke)
        _r.rec = false;
    if (_kind == "remix")
        _r.rec = !(variable_struct_exists(_c, "rparty") && _c.rparty == 1) && !knight_cfg_flag(_c, "infhp");
    // an online match has its own results, not records
    if (_kind == "online")
        _r.rec = false;
    // START AT (anything but the first attack) and REPEAT are practice: not recorded
    var _pm = knight_pmode(_c);
    if (_pm == 2 || (_pm == 1 && knight_cfg_num(_c, "p_atk") > 0))
        _r.rec = false;
    knight_lu_clear();
    if (variable_struct_exists(_c, "rparty") && _c.rparty == 1 && (!variable_struct_exists(_r, "rp_pos") || _r.rp_pos != _r.pos))
    {
        _r.rp_pos = _r.pos;
        var _pool = [1, 2, 3, 4];
        for (var _si = 3; _si > 0; _si--)
        {
            var _sj = irandom(_si);
            var _st = _pool[_si];
            _pool[_si] = _pool[_sj];
            _pool[_sj] = _st;
        }
        var _rn = (_c.c_solo == 1) ? 1 : (1 + irandom(2));
        var _np = [0, 0, 0];
        for (var _q = 0; _q < _rn; _q++)
            _np[_q] = _pool[_q];
        _r.party = _np;
        _r.fl = -1;
        _c.party = [_np[0], _np[1], _np[2]];
        _r.reveal = (((_r.reveal != "") && (_r.pos == 0)) ? (_r.reveal + "  ") : "") + "RANDOM PARTY: " + knight_party_text(_np);
    }
    knight_reset_run_state();
    global.knight_variant_pending = _k;
    global.knight_run = 1;
    global.flag[456] = _c.weird;
    global.char = [_r.party[0], _r.party[1], _r.party[2]];
    knight_apply_stat_options(_c);
    scr_refreshchar();
    global.kaizo_practice = _r.practice ? 1 : 0;
    global.plot = 320;
    global.tempflag[90] = _reg.skip_flag;
    global.interact = 0;
    global.tension = 0;
    if (_c.c_items)
    {
        for (var _i = 0; _i < 13; _i++)
            global.item[_i] = 0;
    }
    // build 43: the online kit (the same HP, stats, items for every player; no spells or armour)
    if (_kind == "online")
    {
        kfo_kit_apply(_r.party[0]);
        scr_refreshchar();
    }
    // build 50: the custom characters (Flowery, ...): their MAGIC (their ACTION + chosen techniques), name and stats - not online
    // (there everybody has the same kit, whatever their SKIN)
    if (_kind != "online")
    {
        knight_cc_spells_apply();
        knight_cc_stats();
    }
    else if (knight_cc_ok(_r.party[0]))
        global.charname[_r.party[0]] = knight_cc(_r.party[0]).name;
}

// Stats at the start of EVERY fight: HP / AT / DF / MAG are rebuilt from the player's own values saved at launch, so nothing a
// fight does to them (the Weird Route finale adds 300-499 max HP to Kris, other fights set HP to 1 or 999) can carry into the next
// fight of a rush or a rematch and stack. WEIRD STATS and HALF MAX HP are then applied on top.
function knight_apply_stat_options(_c)
{
    var _ws = (_c.weird && variable_struct_exists(_c, "c_wstats") && _c.c_wstats == 1);
    var _hh = (variable_struct_exists(_c, "c_halfhp") && _c.c_halfhp == 1);
    var _o = global.knight_orig;
    if (!is_undefined(_o))
    {
        for (var _i = 0; _i < 6; _i++)
        {
            global.maxhp[_i] = _o.maxhp[_i];
            global.at[_i] = _o.at[_i];
            global.df[_i] = _o.df[_i];
            global.mag[_i] = _o.mag[_i];
        }
    }
    if (_ws)
        knight_apply_weird_stats(_c);
    // build 50: the custom characters' own stats (Flowery, ...), from the party's at this point
    knight_cc_stats();
    if (_hh)
    {
        for (var _i = 1; _i <= 5; _i++)
            global.maxhp[_i] = max(1, ceil(global.maxhp[_i] / 2));
    }
    for (var _i = 1; _i <= 5; _i++)
    {
        if (global.hp[_i] > global.maxhp[_i])
            global.hp[_i] = global.maxhp[_i];
    }
    return 1;
}

// Duplicate party members share ONE HP value, but the game marks only the slot that was hit as down (scr_dead). The other copy stayed
// selectable at -999 HP and could still pick a command. Every step: a copy of a downed member is marked down too, and when a sibling copy has been
// brought back up the others come back with it.
function knight_sync_downed()
{
    if (!variable_global_exists("chardead") || !variable_global_exists("charmove") || !variable_global_exists("charcantarget"))
        return 0;
    for (var _i = 0; _i < 3; _i++)
    {
        var _c = global.char[_i];
        if (_c < 1 || _c > 5)
            continue;
        if (global.hp[_c] <= 0)
        {
            if (global.chardead[_i] != 1)
                scr_dead(_i);
        }
        else if (global.chardead[_i] == 1)
        {
            for (var _j = 0; _j < 3; _j++)
            {
                if (_j != _i && global.char[_j] == _c && global.chardead[_j] == 0)
                {
                    global.chardead[_i] = 0;
                    global.charmove[_i] = 1;
                    global.charcantarget[_i] = 1;
                    break;
                }
            }
        }
    }
    return 0;
}

// a member who is already down takes no further damage, whatever the source (restores the HP they had last frame)
function knight_guard_downed(_r)
{
    if (!variable_struct_exists(_r, "gprev"))
        _r.gprev = undefined;
    if (!is_array(_r.gprev))
    {
        _r.gprev = [0, 0, 0, 0, 0, 0];
        for (var _i = 0; _i < 6; _i++)
            _r.gprev[_i] = global.hp[_i];
        return 0;
    }
    for (var _i = 1; _i <= 5; _i++)
    {
        if (_r.gprev[_i] <= 0 && global.hp[_i] < _r.gprev[_i])
            global.hp[_i] = _r.gprev[_i];
        _r.gprev[_i] = global.hp[_i];
    }
    return 0;
}

// Weird Route file stats (HP, AT, DF, MAG per character); the hub snapshot puts the player's own back afterwards
function knight_apply_weird_stats(_c)
{
    if (!_c.weird || !variable_struct_exists(_c, "c_wstats") || _c.c_wstats != 1)
        return 0;
    //            hp  at  df mag
    var _w = [0, [186, 15, 2, 0], [222, 19, 2, 3], [166, 13, 2, 12], [166, 8, 1, 16]];
    for (var _i = 1; _i <= 4; _i++)
    {
        var _s = _w[_i];
        global.maxhp[_i] = _s[0];
        global.at[_i] = _s[1];
        global.df[_i] = _s[2];
        global.mag[_i] = _s[3];
        global.hp[_i] = min(global.hp[_i], global.maxhp[_i]);
    }
    return 1;
}

// HP at the start of a fight: single fights and rematches start full; rush follows the recovery setting
function knight_party_full_heal()
{
    for (var _i = 1; _i <= 5; _i++)
        global.hp[_i] = global.maxhp[_i];
}

function knight_rush_recover(_r)
{
    var _c = _r.cfg;
    for (var _i = 1; _i <= 5; _i++)
    {
        var _mx = global.maxhp[_i];
        var _base = _r.hp_after[_i];
        if (_c.rush_heal == 0)
            global.hp[_i] = _mx;
        else if (_c.rush_heal == 1)
            global.hp[_i] = min(_mx, max(_base, 0) + ceil((_mx * _c.rush_pct) / 100));
        else
            global.hp[_i] = (_base > 0) ? min(_base, _mx) : max(1, ceil(_mx / 8));
    }
}

function knight_launch_go()
{
    var _l = global.knight_launch;
    knight_preview_stop();
    knight_snapshot_take();
    global.krun = knight_run_new(_l);
    // an online match brings its own setup: the player's own menu settings stay as they are
    if (!kfo_cfg_online(_l.src))
        global.knight_cfg = knight_cfg_copy(_l.src);
    knight_store_save();
    knight_fight_setup();
    knight_party_full_heal();
    knight_goto_arena();
}

function knight_rematch()
{
    var _r = global.krun;
    var _l = _r.launch;
    knight_run_teardown();
    global.krun = knight_run_new(_l);
    knight_fight_setup();
    knight_party_full_heal();
    knight_goto_arena();
}

function knight_can_reroll(_r)
{
    return (_r.src.random == 1 || _r.src.randchal == 1 || (_r.src.mode == 1 && _r.src.rush_shuffle == 1));
}

// new random selection from the same source settings; returns "" or an error text
function knight_reroll()
{
    var _r = global.krun;
    var _res = knight_resolve(_r.src);
    if (!_res.ok)
        return _res.errors[0];
    knight_run_teardown();
    global.krun = knight_run_new({ src: _res.src, cfg: _res.cfg, plan: _res.plan, reveal: _res.reveal, corr: _res.corr });
    knight_fight_setup();
    knight_party_full_heal();
    knight_goto_arena();
    return "";
}

function knight_rush_next()
{
    var _r = global.krun;
    _r.pos++;
    knight_run_teardown();
    knight_fight_setup();
    knight_rush_recover(_r);
    knight_goto_arena();
}

// remove prompts / freeze (not the controller)
function knight_run_teardown()
{
    knight_unfreeze();
    with (obj_knight_prompt)
        instance_destroy();
}

function knight_run_cleanup()
{
    // build 50: Flowery's Omega form never outlives its fight (his own poses back on his registry entry)
    knight_fl_om_reset();
    knight_kf_stop();
    knight_speed_reset();
    knight_run_teardown();
    global.knight_run = 0;
    global.krun = undefined;
    knight_lu_clear();
    global.knight_variant_pending = 0;
    knight_reset_run_state();
    global.tempflag[90] = 0;
    global.interact = 0;
    global.kaizo_practice = 0;
    knight_mus_reset();
    snd_free_all();
    snd_stop_all();
}

// ---------- ticking (called every frame from the controller) ----------
function knight_dmg_sample(_r)
{
    var _seen = [0, 0, 0, 0, 0, 0];
    for (var _i = 0; _i < 3; _i++)
    {
        var _c = _r.party[_i];
        if (_c < 1 || _c > 5 || _seen[_c])
            continue;
        _seen[_c] = 1;
        var _cur = global.hp[_c];
        var _prev = _r.prevhp[_c];
        if (_cur < _prev)
        {
            _r.dmg += max(0, _prev) - max(0, _cur);
            knight_stats_taken(_c, max(0, _prev) - max(0, _cur));
        }
        _r.prevhp[_c] = _cur;
    }
}

function knight_dmg_baseline(_r)
{
    for (var _i = 0; _i < 3; _i++)
    {
        var _c = _r.party[_i];
        if (_c >= 1 && _c <= 5)
            _r.prevhp[_c] = global.hp[_c];
    }
}

function knight_run_tick()
{
    if (!knight_active())
        return 0;
    var _r = global.krun;
    if (global.knight_frozen)
        return 0;
    // build 50: a KF Song Pack song in place of the battle music
    knight_kf_tick();
    if (_r.reveal != "" && _r.reveal_t < 1000)
        _r.reveal_t++;
    if (variable_struct_exists(_r, "song_t") && _r.song_t < 1000)
        _r.song_t++;
    if (_r.state != "battle")
        knight_speed_apply(_r);
    if (_r.state == "arena")
    {
        // build 50: an online match goes straight into the fight - no opening cutscene before it, every time
        if (knight_lu_kind_of(_r.cfg) == "online")
            kfo_skip_intro();
        if (instance_exists(obj_battlecontroller))
            knight_attempt_begin();
        return 0;
    }
    // build 50: a single fight won - once its ending cutscene is over and you could walk again (no battle, no cutscene, no
    // text for a second), the results show; no walk to the door first
    if (_r.state == "won" && _r.mode == 0)
    {
        if (!instance_exists(obj_battlecontroller) && !instance_exists(obj_cutscene_master) && instance_exists(obj_mainchara) && global.interact == 0 && !w_ex())
        {
            _r.won_t = (variable_struct_exists(_r, "won_t") ? _r.won_t : 0) + 1;
            if (_r.won_t >= 30)
            {
                knight_fight_finished(room_town_krisyard_dark);
                return 0;
            }
        }
        else
            _r.won_t = 0;
    }
    if (_r.state == "battle")
    {
        if (_r.cfg.c_hp1 && !_r.hp1done && instance_exists(obj_knight_enemy))
        {
            for (var _i = 0; _i < 3; _i++)
            {
                var _c = _r.party[_i];
                if (_c >= 1 && _c <= 5)
                    global.hp[_c] = 1;
            }
            _r.hp1done = true;
            knight_dmg_baseline(_r);
            knight_ch_baseline(_r);
        }
        knight_guard_downed(_r);
        knight_sync_downed();
        knight_lock_release();
        if (variable_struct_exists(_r.cfg, "c_notp") && _r.cfg.c_notp == 1)
            global.tension = 0;
        if (variable_struct_exists(_r.cfg, "c_onelife") && _r.cfg.c_onelife == 1)
        {
            for (var _ol = 0; _ol < 3; _ol++)
            {
                var _oc = _r.party[_ol];
                if (_oc >= 1 && _oc <= 5 && _r.prevhp[_oc] > 0 && global.hp[_oc] <= 0)
                {
                    knight_defeat_begin();
                    return 0;
                }
            }
        }
        if (knight_ch_tick(_r))
            return 0;
        knight_wr_tick(_r);
        knight_infhp_tick(_r);
        knight_lu_tick();
        if (knight_lu_over())
        {
            knight_dmg_sample(_r);
            knight_battle_won();
            if (_r.state == "won")
            {
                _r.state = "finished";
                knight_show_end();
            }
            return 0;
        }
        if (variable_global_exists("mnfight") && global.mnfight == 2)
        {
            // the bullets are flying: nothing is being chosen or cast (a double cast that never happened is forgotten)
            knight_dbl_clear();
            with (obj_knight_enemy)
                knight_hb_compact();
        }
        _r.frames += knight_frame_step();
        knight_dmg_sample(_r);
        return 0;
    }
    if (_r.state == "failed" && !_r.ui_done)
        knight_show_end();
}

function knight_attempt_begin()
{
    var _r = global.krun;
    _r.state = "battle";
    _r.hits = 0;
    global.knight_hits = 0;
    knight_dmg_baseline(_r);
    knight_ch_begin(_r);
    knight_lu_new(_r);
    // build 50: the custom characters' fight state (no turn-long effects left from a fight before)
    knight_cc_battle_begin();
    if (_r.mode == 0)
    {
        if (_r.rec)
        {
            var _rec = knight_rec_get(knight_run_rec_key(_r), knight_rec_category(_r));
            if (!is_undefined(_rec))
            {
                _rec.att++;
                knight_store_save();
            }
        }
    }
    else if (!_r.attcounted && !knight_cfg_flag(_r.cfg, "infhp"))
    {
        _r.attcounted = true;
        var _rr = knight_rec_get("rush", _r.cfg.c_nohit ? "rushnh" : "rush");
        _rr.att++;
        knight_store_save();
    }
}

// ---------- hit hook (scr_damage_cache): once per hostile hit that was not absorbed ----------
function knight_hit_event()
{
    global.knight_hits++;
    global.knight_hit_time = current_time;
    if (!knight_active())
        return 0;
    var _r = global.krun;
    if (_r.state != "battle")
        return 0;
    _r.hits++;
    knight_stats_hit();
    if (_r.cfg.c_nohit && !_r.failed)
    {
        _r.failed = true;
        _r.state = "failed";
        _r.result = "nohit";
        knight_dmg_sample(_r);
        if (_r.mode == 0)
            knight_fight_commit("nohit");
        else
            knight_rush_finish("nohit");
    }
}

// ---------- records ----------
function knight_fight_commit(_outcome)
{
    var _r = global.krun;
    if (_r.fcommitted || _r.mode != 0)
        return false;
    _r.fcommitted = true;
    if (!_r.rec)
        return false;
    var _cat = knight_rec_category(_r);
    var _rec = knight_rec_get(knight_run_rec_key(_r), _cat);
    if (is_undefined(_rec))
        return false;
    if (_outcome == "win")
    {
        if (_cat != "pr")
            _r.newrec = knight_rec_win(_rec, _r.frames, _r.dmg, _r.hits, knight_cfg_text(_r.cfg));
    }
    else if (_outcome == "abandon")
    {
        _rec.aband++;
        knight_rec_loss(_rec);
    }
    else
        knight_rec_loss(_rec);
    knight_store_save();
    return true;
}

function knight_rush_finish(_status)
{
    var _r = global.krun;
    if (_r.runcommitted)
        return false;
    _r.runcommitted = true;
    _r.result = _status;
    if (!_r.attcounted)
        return true;
    var _rec = knight_rec_get("rush", _r.cfg.c_nohit ? "rushnh" : "rush");
    var _n = array_length(_r.fights);
    if (_status == "complete")
    {
        _r.newrec = knight_rec_win(_rec, _r.tot_t, _r.tot_dmg, _r.tot_hits, knight_cfg_text(_r.cfg));
        _rec.far = max(_rec.far, _n);
    }
    else
    {
        _rec.far = max(_rec.far, _n);
        if (_status == "abandon")
            _rec.aband++;
        knight_rec_loss(_rec);
    }
    knight_store_save();
    return true;
}

// ---------- battle end hooks (patched into the fight objects) ----------
// first statement of PTB02 Step "con == 8": the battle was won (killed or spared)
function knight_battle_won()
{
    if (!knight_active())
        return 0;
    var _r = global.krun;
    if (_r.state != "battle")
        return 0;
    // the online Knight cannot be beaten (its ending never starts); should the battle end anyway, the match is over for us
    if (kfo_cfg_online(_r.cfg))
    {
        kfo_on_defeat("the battle ended on its own (the fight's win check)");
        return 0;
    }
    knight_dmg_sample(_r);
    for (var _i = 0; _i < 6; _i++)
        _r.hp_after[_i] = global.hp[_i];
    _r.story_result = (global.flag[50] == 1) ? 1 : 2;
    _r.state = "won";
    _r.won_t = 0;
    knight_fl_om_reset();
    knight_kf_stop();
    if (_r.mode == 0)
    {
        _r.result = "win";
        knight_fight_commit("win");
        return 0;
    }
    array_push(_r.fights, { k: _r.plan[_r.pos], t: _r.frames, dmg: _r.dmg, hits: _r.hits });
    _r.tot_t += _r.frames;
    _r.tot_dmg += _r.dmg;
    _r.tot_hits += _r.hits;
    if (_r.pos + 1 >= array_length(_r.plan))
    {
        _r.state = "done";
        knight_rush_finish("complete");
        knight_show_end();
    }
    else
    {
        _r.state = "rushwait";
        knight_show_clear();
    }
}

// end of the post-fight cutscene (replaces the room change)
function knight_fight_finished(_dest)
{
    if (!knight_active())
    {
        room_goto(_dest);
        return 0;
    }
    var _r = global.krun;
    global.knight_after_dest = _dest;
    if (_r.mode == 1)
        return 0;
    _r.state = "finished";
    knight_show_end();
}

// scr_gameover: party wiped
function knight_defeat_begin()
{
    var _r = global.krun;
    if (_r.state == "lost" || _r.state == "done" || _r.state == "won" || _r.state == "rushwait" || _r.state == "finished")
        return 0;
    // build 43: online, a fallen party is OUT of the match
    if (kfo_cfg_online(_r.cfg))
    {
        kfo_on_defeat("the game's own party-down check (GAME OVER)");
        return 0;
    }
    if (_r.state == "failed")
    {
        knight_show_end();
        return 0;
    }
    knight_dmg_sample(_r);
    knight_fl_om_reset();
    knight_kf_stop();
    _r.state = "lost";
    _r.result = "lost";
    if (_r.mode == 0)
        knight_fight_commit("lost");
    else
        knight_rush_finish("lost");
    knight_show_end();
    knight_mus_reset();
    audio_stop_all();
    snd_play(snd_hurt1);
}

// ---------- leaving ----------
function knight_leave_request()
{
    // Backspace during a run
    var _r = global.krun;
    if (kfo_cfg_online(_r.cfg))
        return kfo_leave_request();
    knight_freeze();
    var _p = instance_create_depth(0, 0, -99995, obj_knight_prompt);
    _p.title = (_r.mode == 1) ? "ABANDON KNIGHT RUSH?" : "LEAVE THE FIGHT?";
    var _l = [];
    if (_r.mode == 1)
    {
        array_push(_l, "Fight " + string(_r.pos + 1) + " of " + string(array_length(_r.plan)) + ".");
        array_push(_l, "The run will be recorded as abandoned.");
    }
    else
        array_push(_l, "You return to the Knight menu.");
    _p.lines = _l;
    _p.opts = [{ t: (_r.mode == 1) ? "Keep going" : "Keep fighting", a: "resume", cancel: true }, { t: (_r.mode == 1) ? "Abandon Rush" : "Leave", a: (_r.mode == 1) ? "abandon_rush" : "hub_menu" }];
    return _p;
}

// back to the snow zone. menu=true: Knight menu opens again; menu=false: hub menu stays closed (story state restored)
function knight_exit_run(_menu)
{
    var _r = global.krun;
    if (is_struct(_r))
    {
        if (_r.mode == 0 && !_r.fcommitted && _r.state == "battle")
            knight_fight_commit("abandon");
        if (_r.mode == 1 && !_r.runcommitted && (_r.state == "battle" || _r.state == "rushwait"))
            knight_rush_finish("abandon");
    }
    knight_run_cleanup();
    knight_snapshot_restore(_menu ? "hub" : "leave");
    // after an online match: the player's own spells and equipment (the online kit had none)
    kfo_kit_restore();
    if (_menu)
        global.plot = 320;
    else
        global.knight_orig = undefined;
    global.knight_reopen = _menu;
    knight_activate_all_safe();
    if (room == room_dw_snow_zone)
        room_restart();
    else
        room_goto(room_dw_snow_zone);
}

function knight_continue_story()
{
    var _r = global.krun;
    var _dest = global.knight_after_dest;
    var _res = is_struct(_r) ? _r.story_result : 2;
    knight_run_cleanup();
    knight_snapshot_restore("continue");
    global.knight_orig = undefined;
    global.knight_reopen = false;
    // the story's own result for this fight (written once, here, instead of during every hub fight)
    scr_flag_set(1047, _res);
    ossafe_ini_open("dr.ini");
    ini_write_real(scr_ini_chapter(global.chapter, global.filechoice), "UraBoss", _res);
    ossafe_ini_close();
    ossafe_savedata_save();
    global.interact = 0;
    knight_activate_all_safe();
    if (_dest != -4)
        room_goto(_dest);
}

// ---------- prompts ----------
function knight_prompt_new(_title, _lines, _opts)
{
    knight_freeze();
    var _p = instance_create_depth(0, 0, -99995, obj_knight_prompt);
    _p.title = _title;
    _p.lines = _lines;
    _p.opts = _opts;
    return _p;
}

function knight_result_lines(_r, _extra)
{
    var _l = [];
    var _reg = knight_reg(knight_cur_knight());
    var _kind = knight_lu_kind_of(_r.cfg);
    if (_kind == "tag")
        array_push(_l, ["^", "TAG TEAM: " + knight_reg(_r.cfg.knight).short + " + " + knight_reg(_r.cfg.knight2).short, c_yellow]);
    else if (_kind == "remix")
        array_push(_l, ["^", "ATTACK REMIX", c_yellow]);
    else
        array_push(_l, ["^", string_upper(_reg.name) + (_reg.joke ? "  (JOKE)" : ""), _reg.color]);
    array_push(_l, ["Battle time", knight_time_text(_r.frames), ""]);
    array_push(_l, ["Damage taken", string(floor(_r.dmg)), ""]);
    array_push(_l, ["Hits taken", string(_r.hits), ""]);
    if (_r.newrec != "")
        array_push(_l, ["^", _r.newrec, c_yellow]);
    if (_extra != "")
        array_push(_l, ["~", _extra]);
    return _l;
}

function knight_record_note(_r)
{
    if (_r.mode == 1)
        return "";
    var _kind = knight_lu_kind_of(_r.cfg);
    if (knight_cfg_flag(_r.cfg, "infhp"))
        return "Infinite HP: nothing is recorded.";
    if (_kind == "tag" && (knight_reg(_r.cfg.knight).joke || knight_reg(_r.cfg.knight2).joke))
        return "With a joke fight in it, this Tag Team is not recorded.";
    if (_kind != "")
        return "";
    var _reg = knight_reg(knight_cur_knight());
    if (_reg.joke)
        return "Joke fight: nothing is recorded.";
    if (_r.practice)
        return "Practice: attempts only, no clears.";
    var _pm = knight_pmode(_r.cfg);
    if (_pm == 2)
        return "Repeat practice: nothing is recorded.";
    if (_pm == 1 && knight_cfg_num(_r.cfg, "p_atk") > 0)
        return "Started part-way: nothing is recorded.";
    return "";
}

function knight_show_end()
{
    var _r = global.krun;
    if (_r.ui_done)
        return 0;
    // online fights have their own OUT / results prompts
    if (kfo_cfg_online(_r.cfg))
        return 0;
    _r.ui_done = true;
    var _opts = [];
    var _title = "";
    var _lines = [];
    var _rush = (_r.mode == 1);
    var _rr = knight_can_reroll(_r);
    if (_rush)
    {
        switch (_r.result)
        {
            case "complete": _title = "KNIGHT RUSH COMPLETE!"; break;
            case "lost": _title = "RUSH FAILED: DEFEATED"; break;
            case "nohit": _title = "NO-HIT FAILED"; break;
            case "time": _title = "RUSH FAILED: TIME UP"; break;
            default: _title = "KNIGHT RUSH ABANDONED"; break;
        }
        var _n = array_length(_r.plan);
        for (var _i = 0; _i < _n; _i++)
        {
            var _nm = knight_reg(_r.plan[_i]).short;
            if (_i < array_length(_r.fights))
                array_push(_lines, [string(_i + 1) + ". " + _nm, knight_time_text(_r.fights[_i].t), string(floor(_r.fights[_i].dmg)) + " dmg"]);
            else
                array_push(_lines, [string(_i + 1) + ". " + _nm, "--", "not reached"]);
        }
        array_push(_lines, ["CLEARED " + string(array_length(_r.fights)) + "/" + string(_n), knight_time_text(_r.tot_t), string(floor(_r.tot_dmg)) + " dmg", true]);
        if (_r.newrec != "")
            array_push(_lines, ["^", _r.newrec, c_yellow]);
        array_push(_opts, { t: "Restart Rush", a: "rematch" });
        if (_rr)
            array_push(_opts, { t: "Reroll", a: "reroll" });
        array_push(_opts, { t: "Rush stats", a: "stats" });
        array_push(_opts, { t: "Change settings", a: "hub_menu" });
        array_push(_opts, { t: "Return to Hub", a: "hub_leave" });
    }
    else
    {
        var _extra = knight_record_note(_r);
        if (_r.result == "win")
        {
            _title = (knight_lu_kind_of(_r.cfg) == "tag") ? "BOTH KNIGHTS DEFEATED!" : "KNIGHT DEFEATED!";
            _lines = knight_result_lines(_r, _extra);
            array_push(_opts, { t: "Rematch", a: "rematch" });
            if (_rr)
                array_push(_opts, { t: "Reroll", a: "reroll" });
            array_push(_opts, { t: "Fight stats", a: "stats" });
            array_push(_opts, { t: "Change settings", a: "hub_menu" });
            array_push(_opts, { t: "Return to Hub", a: "hub_leave" });
            // the story's own ending belongs to one knight's fight (it plays that knight's scene)
            if (knight_lu_kind_of(_r.cfg) == "")
                array_push(_opts, { t: "Continue story", a: "continue" });
        }
        else if (_r.result == "time")
        {
            _title = "TIME UP";
            _lines = knight_result_lines(_r, "The knight was still standing after " + string(_r.tlimit) + " turns.");
            array_push(_opts, { t: "Retry", a: "rematch" });
            if (_rr)
                array_push(_opts, { t: "Reroll", a: "reroll" });
            array_push(_opts, { t: "Fight stats", a: "stats" });
            array_push(_opts, { t: "Change settings", a: "hub_menu" });
            array_push(_opts, { t: "Return to Hub", a: "hub_leave" });
        }
        else if (_r.result == "nohit")
        {
            _title = "NO-HIT FAILED";
            _lines = knight_result_lines(_r, "You were hit, so this attempt is over.");
            array_push(_opts, { t: "Retry", a: "rematch" });
            if (_rr)
                array_push(_opts, { t: "Reroll", a: "reroll" });
            array_push(_opts, { t: "Fight stats", a: "stats" });
            array_push(_opts, { t: "Change settings", a: "hub_menu" });
            array_push(_opts, { t: "Return to Hub", a: "hub_leave" });
        }
        else
        {
            _title = "DEFEATED";
            _lines = knight_result_lines(_r, _extra);
            array_push(_opts, { t: "Rematch", a: "rematch" });
            if (_rr)
                array_push(_opts, { t: "Reroll", a: "reroll" });
            array_push(_opts, { t: "Fight stats", a: "stats" });
            array_push(_opts, { t: "Change settings", a: "hub_menu" });
            array_push(_opts, { t: "Return to Hub", a: "hub_leave" });
        }
    }
    var _p = knight_prompt_new(_title, _lines, _opts);
    _p.wide = _rush;
    if (!_rush && _r.result == "nohit" && _r.cfg.nh_retry && !_r.stats_seen)
    {
        _p.autoact = "rematch";
        _p.timer = 24;
    }
    return _p;
}

function knight_show_clear()
{
    var _r = global.krun;
    var _n = array_length(_r.plan);
    var _f = _r.fights[array_length(_r.fights) - 1];
    var _l = [];
    var _kr = knight_reg(_f.k);
    array_push(_l, ["^", string_upper(_kr.name), _kr.color]);
    array_push(_l, ["Battle time", knight_time_text(_f.t), ""]);
    array_push(_l, ["Damage taken", string(floor(_f.dmg)), ""]);
    array_push(_l, ["Next", knight_reg(_r.plan[_r.pos + 1]).short, "", true]);
    var _c = _r.cfg;
    var _rec = "Healing: ";
    if (_c.rush_heal == 0)
        _rec += "full HP.";
    else if (_c.rush_heal == 1)
        _rec += string(_c.rush_pct) + "% of max HP.";
    else
        _rec += "none.";
    array_push(_l, ["~", _rec + " TP resets, items carry over."]);
    var _p = knight_prompt_new("FIGHT " + string(_r.pos + 1) + "/" + string(_n) + " CLEARED", _l, [{ t: "Next fight", a: "next" }, { t: "Abandon Rush", a: "abandon_rush" }]);
    _p.wide = true;
    _p.autoact = "next";
    _p.timer = 36;
    return _p;
}

// run an action chosen in a prompt (called after the fade-out)
function knight_act_run(_a)
{
    // build 43: the online prompts (SEND, OUT, results)
    if (is_string(_a) && (string_pos("onl_", _a) == 1 || string_pos("kfo_", _a) == 1))
        return kfo_act(_a);
    switch (_a)
    {
        case "resume":
            knight_run_teardown();
            global.interact = 0;
            break;
        case "rematch":
            knight_rematch();
            break;
        case "reroll":
            var _e = knight_reroll();
            if (_e != "")
            {
                global.krun.msg = _e;
                return _e;
            }
            break;
        case "next":
            knight_rush_next();
            break;
        case "abandon_rush":
            knight_rush_finish("abandon");
            global.krun.ui_done = false;
            knight_run_teardown();
            global.krun.state = "done";
            knight_show_end();
            break;
        case "hub_menu":
            knight_exit_run(true);
            break;
        case "hub_leave":
            knight_exit_run(false);
            break;
        case "continue":
            knight_continue_story();
            break;
        case "stats":
            global.krun.st.page = 0;
            knight_show_stats();
            break;
        case "stats_more":
            var _st = global.krun.st;
            _st.page = (_st.page + 1) mod max(1, ceil(array_length(_st.atk) / knight_stats_per_page()));
            knight_show_stats();
            break;
        case "stats_back":
            with (obj_knight_prompt)
                instance_destroy();
            global.krun.ui_done = false;
            knight_show_end();
            break;
    }
    return "";
}

// ---------- in-fight overlay text ----------
function knight_hud_lines()
{
    var _l = [];
    if (!knight_active())
        return _l;
    var _r = global.krun;
    var _reg = knight_reg(knight_cur_knight());
    var _kind = knight_lu_kind_of(_r.cfg);
    if (_kind == "online")
    {
        // build 45: the battle royale HUD shows everything itself (online_br_hud.gml)
        return kfo_hud_lines(_l);
    }
    if (_r.mode == 1)
        array_push(_l, "KNIGHT RUSH " + string(_r.pos + 1) + "/" + string(array_length(_r.plan)));
    if (_kind == "tag")
        array_push(_l, "TAG TEAM");
    if (_kind == "remix")
        array_push(_l, "ATTACK REMIX");
    if (_reg.joke && _kind == "")
        array_push(_l, "JOKE FIGHT - NOT RECORDED");
    var _pm = knight_pmode(_r.cfg);
    if (_pm == 2)
        array_push(_l, "REPEAT: " + string_upper(knight_reg(_r.cfg.knight).atk[clamp(knight_cfg_num(_r.cfg, "p_atk"), 0, array_length(knight_reg(_r.cfg.knight).atk) - 1)][2]));
    if (_pm == 1 && knight_cfg_num(_r.cfg, "p_atk") > 0)
        array_push(_l, "STARTED AT " + string_upper(knight_reg(_r.cfg.knight).atk[clamp(knight_cfg_num(_r.cfg, "p_atk"), 0, array_length(knight_reg(_r.cfg.knight).atk) - 1)][2]));
    if (knight_ff_on())
        array_push(_l, ">> FAST-FORWARD");
    if (_r.practice)
        array_push(_l, "PRACTICE - NO CLEARS");
    if (knight_cfg_flag(_r.cfg, "infhp"))
        array_push(_l, "INFINITE HP - NOT RECORDED");
    if (_r.cfg.c_nohit)
        array_push(_l, "NO-HIT" + ((_r.failed && _r.result == "nohit") ? " FAILED" : ""));
    var _tags = [];
    if (_r.cfg.c_twin)
        array_push(_tags, "TWIN KNIGHT");
    if (_r.cfg.c_dark)
        array_push(_tags, "DARKNESS");
    if (_r.cfg.c_speed)
        array_push(_tags, "HYPER SPEED");
    if (_r.cfg.c_thorns)
        array_push(_tags, "THORNS");
    if (array_length(_tags) > 0)
        array_push(_l, knight_join(_tags, " + "));
    if (_r.cfg.c_time && _r.tlimit > 0)
    {
        if (_r.failed && _r.result == "time")
            array_push(_l, "TIME UP");
        else
            array_push(_l, "TURN " + string(max(1, _r.eturns)) + " OF " + string(_r.tlimit));
    }
    return _l;
}

// colour of an overlay line: red for failures and the last three turns of a Time limit
function knight_hud_line_color(_s)
{
    if (string_pos("JOKE", _s) > 0)
        return c_orange;
    if (string_pos("FAILED", _s) > 0 || string_pos("TIME UP", _s) > 0)
        return make_color_rgb(255, 96, 96);
    if (string_pos("TURN ", _s) == 1 && knight_active() && (global.krun.tlimit - global.krun.eturns) < 3)
        return make_color_rgb(255, 96, 96);
    return c_white;
}

// Backspace during a run offers to leave (online: the GIVE UP / LEAVE key of KEYBINDS, Backspace unless changed)
function knight_backspace_check()
{
    if (!knight_active() || global.knight_frozen)
        return 0;
    if (instance_exists(obj_knight_prompt) || instance_exists(obj_knight_menu))
        return 0;
    var _r = global.krun;
    if (_r.state != "arena" && _r.state != "battle" && _r.state != "won")
        return 0;
    // build 48: BACKSPACE while typing in the chat deletes a letter, never leaves the match
    if (kfo_cfg_online(_r.cfg) && kfo_chat_typing())
        return 0;
    if (keyboard_check_pressed(kfo_cfg_online(_r.cfg) ? kfo_key("quit") : vk_backspace))
    {
        knight_leave_request();
        return 0;
    }
    if (knight_hotkeys_on() && keyboard_check_pressed(ord("R")) && !kfo_cfg_online(_r.cfg))
        knight_quick_retry();
}

// ---------- inert stand-ins for absent Kris / Susie / Ralsei (variants that read obj_hero* without checking) ----------
function knight_spawn_ghosts()
{
    if (!knight_active())
        return 0;
    var _key = knight_reg(knight_cur_knight()).key;
    // Kaizo and Violet check for missing members themselves
    if (_key == "kaizo" || _key == "violet")
        return 0;
    var _p = global.krun.party;
    var _empty = 0;
    for (var _s = 2; _s >= 0; _s--)
    {
        if (_p[_s] == 0)
            _empty = _s;
    }
    var _objs = [obj_knight_ghost_kris, obj_knight_ghost_susie, obj_knight_ghost_ralsei];
    for (var _i = 0; _i < 3; _i++)
    {
        if (!knight_party_has_in(_p, _i + 1))
        {
            var _g = instance_create_depth(0, 0, 0, _objs[_i]);
            _g.myself = _empty;
        }
    }
}

// ---------- X-Slash and Red Buster cast from the spell menu ----------
// X-Slash is the Spamton NEO / knight "X-Slash" ACT as a spell: two slashes, Kris in their slash pose.
// Red Buster cast by anyone but Susie comes from the caster (Kris in their act pose).
global.knight_ks = undefined;

function knight_xslash_damage(_c, _star)
{
    var _d = round(((global.battleat[_c] * 160) / 20) - (global.monsterdf[_star] * 3));
    if (i_ex(obj_knight_enemy))
    {
        var _r = 0.15 + ((obj_knight_enemy.damagereduction - 0.15) * 1.25);
        if (_r > 1.05)
            _r = 1.05;
        _d = ceil(ceil(_d * _r) * 2);
        // Kaizo Knight's guard divides X-Slash like it divides Ice Shock (its FIGHT is divided by 5 unless the hit is perfect)
        _d = ceil(_d / knight_kaizo_div());
    }
    return max(0, _d);
}

// Kaizo Knight's guard: the divisor its Ice Shock code uses while kaizo_block is on (1 when there is no guard or another knight)
function knight_kaizo_div()
{
    if (global.knight_variant != 1 || !i_ex(obj_knight_enemy))
        return 1;
    var _e = instance_find(obj_knight_enemy, 0);
    if (!variable_instance_exists(_e, "kaizo_block") || !_e.kaizo_block)
        return 1;
    var _div;
    if (global.charweapon[4] == 13)
        _div = 7 - (_e.damagereduction * 9.5);
    else if (scr_havechar(2) && global.hp[2] > 0)
        _div = 6 - (_e.damagereduction * 7.5);
    else
        _div = 4.5 - (_e.damagereduction * 7.5);
    return max(1, _div);
}

// spell-phase length for the X-Slash scene (the game's own value is 30 frames; the two slashes need ~46)
function knight_ks_delay(_d)
{
    if (!is_undefined(global.knight_ks) && global.knight_ks.kind == 1)
        return max(_d, 46);
    return _d;
}

function knight_kspell_start(_kind, _caster, _star, _dmg)
{
    // build 50: a custom character's move still on screen is cleaned up first (its markers never stay behind)
    var _old = global.knight_ks;
    if (is_struct(_old) && variable_struct_exists(_old, "cc") && variable_struct_exists(_old, "fl"))
        knight_fl_end(_old);
    global.knight_ks = { kind: _kind, t: 0, caster: _caster, star: _star, dmg: _dmg, fb: noone, tn: 9, fx: 0, fy: 0, oss: -1, osf: 0, ice: -1, idmg: 0, blue: 0, fb2: noone, dbl: 0, fb3: noone };
    return true;
}

// Kris's own pose only when exactly one Kris is in the party (a pose swap would hide every clone)
function knight_kspell_krispose(_caster)
{
    if (global.char[_caster] != 1 || !i_ex(obj_herokris))
        return false;
    var _n = 0;
    for (var _i = 0; _i < 3; _i++)
    {
        if (global.char[_i] == 1)
            _n++;
    }
    return (_n == 1);
}

function knight_kspell_pos(_star)
{
    if (i_ex(obj_knight_enemy))
        return [obj_knight_enemy.x + 119, obj_knight_enemy.y + 76];
    return [global.monsterx[_star] + 57, global.monstery[_star] + 76];
}

function knight_kspell_tick()
{
    var _k = global.knight_ks;
    if (is_undefined(_k))
        return 0;
    // build 50: paused (the hub's pause switches the battle off): the move or scene waits - before, it went on counting, found
    // no battle and ended itself halfway (Flowery's transformation then left the fight held for good)
    if (global.knight_frozen)
        return 0;
    _k.t++;
    // build 50: the custom characters' techniques (Flowery, ...)
    if (_k.kind >= 20)
        return knight_cc_kspell_tick(_k);
    var _pose = knight_kspell_krispose(_k.caster);
    if (_k.kind == 8 || _k.kind == 9)
    {
        // RUDER BUSTER (Susie) / ICESTORM (Noelle), learned on the Weird Route: the member's own spell twice, at X-Slash's timing
        // (the second one 15 frames after the first). Susie's second swing restarts her Rude Buster animation like X-Slash's pose.
        if ((_k.t == 1 || _k.t == 16) && global.monster[_k.star] == 1 && i_ex(global.monsterinstance[_k.star]))
        {
            if (_k.kind == 8)
            {
                var _hs8 = (_k.caster >= 0 && _k.caster < 3) ? global.charinstance[_k.caster] : noone;
                if (_k.t == 16 && i_ex(_k.fb))
                {
                    with (_k.fb)
                        instance_destroy();
                }
                var _rx = i_ex(_hs8) ? _hs8.x : (i_ex(obj_herosusie) ? obj_herosusie.x : 0);
                var _ry = i_ex(_hs8) ? _hs8.y : (i_ex(obj_herosusie) ? obj_herosusie.y : 0);
                var _rb = instance_create(_rx, _ry, obj_rudebuster_anim);
                _rb.damage = _k.dmg;
                _rb.star = _k.star;
                _rb.caster = _k.caster;
                _rb.target = global.monsterinstance[_k.star];
                _k.fb = _rb;
                if (_k.t == 16)
                    snd_pitch(snd_play(snd_scytheburst), 0.8);
            }
            else
            {
                var _ic9 = instance_create(global.monsterx[_k.star], global.monstery[_k.star], obj_icespell);
                _ic9.damage = _k.dmg;
                _ic9.star = _k.star;
                _ic9.caster = _k.caster;
                _ic9.target = global.monsterinstance[_k.star];
            }
        }
        if (_k.t >= 48)
            global.knight_ks = undefined;
        return 0;
    }
    if (_k.kind == 1 && (_k.t == 1 || _k.t == 16))
    {
        // two slashes like the X-Slash ACT: pose, slash, 14 frames later the pose restarts and the reverse slash lands.
        // Each slash does its own hit (damage number, hurt flash); the first number sits under the second.
        var _first = (_k.t == 1);
        if (_pose)
        {
            if (!_first)
                scr_act_charsprite_end();
            var _krs = scr_act_charsprite("kris", spr_krisb_attack, 0.25, 1);
            _krs.depth = obj_herokris.depth + 1;
        }
        snd_pitch(snd_play(snd_scytheburst), _first ? 1.2 : 0.8);
        var _p = knight_kspell_pos(_k.star);
        var _att = instance_create(_p[0], _p[1], obj_basicattack);
        _att.image_xscale = _first ? 2 : -2;
        _att.image_yscale = 2;
        if (global.charweapon[1] == 26 && global.char[_k.caster] == 1)
            _att.sprite_index = spr_attack_shard;
        if (global.monster[_k.star] == 1 && global.monsterhp[_k.star] > 0)
        {
            caster = _k.caster;
            if (_first)
                global.hittarget[_k.star] = 0;
            scr_damage_enemy(_k.star, _k.dmg);
        }
    }
    if (_k.kind == 2 || _k.kind == 3 || _k.kind == 4 || _k.kind == 6)
    {
        // Kris shines their SOUL on Susie (Red Buster), Ralsei (Dual Heal) or Noelle (SoulShock), like the vanilla ACT: act pose,
        // soul heart, both flash; then the partner performs the spell with their own stats.
        var _ps = knight_soul_slot((_k.kind == 2) ? 2 : ((_k.kind == 3 || _k.kind == 6) ? 3 : 4));
        if (_k.t == 1)
        {
            if (_pose)
            {
                var _krs2 = scr_act_charsprite("kris", spr_krisb_act, 0.25, 1);
                _krs2.depth = obj_herokris.depth + 1;
            }
            snd_play(snd_boost);
            // the shining SOUL comes from Kris, or (Dual Heal without Kris) from Noelle
            var _src = noone;
            if (global.char[_k.caster] == 1)
                _src = obj_herokris;
            else if (_k.kind == 3)
            {
                var _nsr = knight_soul_slot(4);
                if (_nsr >= 0)
                    _src = global.charinstance[_nsr];
            }
            if (i_ex(_src))
            {
                var _heart = instance_create(_src.x + 30, _src.y + 50, obj_animation);
                with (_heart)
                {
                    depth = -20;
                    image_index = 0;
                    image_xscale = 2;
                    image_yscale = 2;
                    image_speed = 1;
                    sprite_index = spr_soulshining;
                }
                with (_src)
                    scr_oflash();
            }
            if (_ps >= 0 && i_ex(global.charinstance[_ps]))
            {
                with (global.charinstance[_ps])
                    scr_oflash();
            }
        }
        if (_k.t == 18 && _k.kind == 4 && _ps >= 0 && i_ex(global.charinstance[_ps]))
        {
            // Noelle drops the ACT pose and plays her own spell-cast animation (the hero object's state 2 draws spellsprite)
            global.faceaction[_ps] = 0;
            with (global.charinstance[_ps])
            {
                state = 2;
                itemed = 1;
                force = 0;
                attacktimer = 0;
            }
        }
        if (_k.t == 14 && _k.kind == 6)
        {
            _k.blue = 1;
            knight_fire_windup(_ps, _k);
        }
        if (_k.t == 20 && _k.kind == 6)
        {
            // hand over to the (blue) FireShock sequence, cast by Ralsei
            if (_pose)
                scr_act_charsprite_end();
            if (_ps >= 0)
            {
                _k.kind = 5;
                _k.t = 0;
                _k.caster = _ps;
                _k.blue = 1;
                return 0;
            }
            global.knight_ks = undefined;
            return 0;
        }
        if (_k.t == 20)
        {
            if (_k.kind == 2 && _ps >= 0 && i_ex(global.monsterinstance[_k.star]) && i_ex(global.charinstance[_ps]))
            {
                var _hs = global.charinstance[_ps];
                var _atk = instance_create(_hs.x, _hs.y, obj_rudebuster_anim);
                _atk.damage = _k.dmg;
                _atk.star = _k.star;
                _atk.caster = _ps;
                _atk.target = global.monsterinstance[_k.star];
                _atk.red = 1;
            }
            if (_k.kind == 3)
                knight_dualheal_apply(_ps, _k.dmg);
            if (_k.kind == 4 && _ps >= 0 && i_ex(global.monsterinstance[_k.star]) && i_ex(global.charinstance[_ps]))
            {
                // the game's own Ice Shock object, flagged red (tint in the hexagons and rings), cast by Noelle
                var _ice = instance_create(global.monsterx[_k.star], global.monstery[_k.star], obj_icespell);
                _ice.damage = _k.dmg;
                _ice.star = _k.star;
                _ice.caster = _ps;
                _ice.target = global.monsterinstance[_k.star];
                _ice.red = 1;
            }
        }
    }
    if (_k.kind == 7)
    {
        // FROSTFIRE: Noelle (Ice Shock) and Ralsei (FireShock) both cast. The chooser is already in their own cast pose; the partner drops the locked
        // ACT pose and winds up too. Then the FireShock sequence runs and the Ice Shock lands with it (kind 5 with _k.ice set).
        var _rs7 = knight_soul_slot(3);
        var _ns7 = knight_soul_slot(4);
        if (_k.t == 1)
        {
            if (_rs7 >= 0)
                knight_fire_windup(_rs7, _k);
            if (_ns7 >= 0)
                knight_ice_windup(_ns7);
        }
        if (_k.t >= 8)
        {
            if (_rs7 < 0 || _ns7 < 0)
            {
                global.knight_ks = undefined;
                return 0;
            }
            _k.kind = 5;
            _k.t = 0;
            _k.caster = _rs7;
            _k.ice = _ns7;
            _k.blue = 2;
            return 0;
        }
    }
    if (_k.kind == 5)
    {
        // FireShock (Chapter 5): the hero object already held the fireball (frames 0-2) during the normal cast pose (knight_fire_pose); here Ralsei throws it on frame 3, the fireball flies fast to the
        // knight (~36 px/tick), then the Chapter 5 flame burst (obj_firespell) lands. Timing follows the Chapter 5 cutscene.
        var _hero = global.charinstance[_k.caster];
        var _rp = (global.char[_k.caster] == 3);
        if (_k.t == 1 && _rp)
        {
            // the Chapter 5 sprites use a different origin than Ralsei's normal cast sprite; re-anchor them so he stays where he stands
            sprite_set_offset(spr_ralsei_spell_fireball_right, 7, -5);
            sprite_set_offset(spr_spell_fireball, 25, 10);
            if (_k.blue == 2)
                sprite_set_offset(spr_bluefire_ball, 25, 10);
            if (_k.blue == 1)
            {
                sprite_set_offset(spr_ralsei_spell_bluefireball_right, 7, -5);
                sprite_set_offset(spr_bluefire_ball, 25, 10);
            }
        }
        if (_k.t == 1 && i_ex(_hero) && _rp)
            knight_fire_windup(_k.caster, _k);
        if (_k.t == 1 && _k.ice >= 0)
            knight_ice_windup(_k.ice);
        if (i_ex(_hero) && _rp && _k.t <= 20 && !(_k.dbl && _k.t >= 17))
        {
            var _fr = min(5, 3 + ((_k.t - 1) / 6));
            with (_hero)
                attacktimer = _fr;
        }
        if (i_ex(_hero) && _rp && _k.dbl && _k.t >= 17 && _k.t <= 36)
        {
            // FIRESTORM: Ralsei throws again (the second fireball, 15 frames after the first like X-Slash's second slash)
            var _fr2 = min(5, 3 + ((_k.t - 17) / 6));
            with (_hero)
                attacktimer = _fr2;
        }
        var _tx = global.monsterx[_k.star];
        var _ty = global.monstery[_k.star];
        if (_k.t == 2 && i_ex(_hero))
        {
            _k.fx = _hero.x + (_rp ? 72 : 44);
            _k.fy = _hero.y + (_rp ? 32 : 30);
            _k.tn = max(2, ceil(point_distance(_k.fx, _k.fy, _tx, _ty) / 36));
            var _ang = point_direction(_k.fx, _k.fy, _tx, _ty);
            var _bs = (_k.blue == 1) ? spr_bluefire_ball : spr_spell_fireball;
            _k.fb = instance_create(_k.fx, _k.fy, obj_animation);
            with (_k.fb)
            {
                sprite_index = _bs;
                image_index = 0;
                image_speed = 0.2;
                image_xscale = 2;
                image_yscale = 2;
                image_angle = _ang;
                depth = -20;
            }
            if (_k.blue == 2)
            {
                // FROSTFIRE: an ice-blue fireball twin flies beside the red one (double helix)
                _k.fb2 = instance_create(_k.fx, _k.fy, obj_animation);
                with (_k.fb2)
                {
                    sprite_index = spr_bluefire_ball;
                    image_index = 1;
                    image_speed = 0.2;
                    image_xscale = 2;
                    image_yscale = 2;
                    image_angle = _ang;
                    depth = -20;
                }
            }
            for (var _b = 0; _b < 7; _b++)
                knight_fire_ember(_k.fx, _k.fy, _b * (360 / 7), 3.2, 1.2, (_k.blue == 2) ? (_b mod 2) : _k.blue);
        }
        if (_k.t >= 3 && _k.t <= (_k.dbl ? 35 : 20) && _rp && i_ex(_hero) && (_k.t mod 3) == 0)
            knight_fire_ember(_hero.x + 72, _hero.y + 36, random(360), 1.2, 0.8, _k.blue);
        if (_k.dbl)
        {
            // the second fireball of FIRESTORM: same flight as the first, launched 15 frames after it (t 17)
            var _t2 = _k.t - 17;
            if (_t2 == 0)
            {
                var _ang2 = point_direction(_k.fx, _k.fy, _tx, _ty);
                var _bs3 = (_k.blue == 1) ? spr_bluefire_ball : spr_spell_fireball;
                _k.fb3 = instance_create(_k.fx, _k.fy, obj_animation);
                with (_k.fb3)
                {
                    sprite_index = _bs3;
                    image_index = 0;
                    image_speed = 0.2;
                    image_xscale = 2;
                    image_yscale = 2;
                    image_angle = _ang2;
                    depth = -20;
                }
                snd_pitch(snd_play(snd_scytheburst), 0.8);
                for (var _b3 = 0; _b3 < 7; _b3++)
                    knight_fire_ember(_k.fx, _k.fy, _b3 * (360 / 7), 3.2, 1.2, _k.blue);
            }
            if (_t2 > 0 && _t2 < _k.tn && i_ex(_k.fb3))
            {
                var _kk3 = _t2 / _k.tn;
                _k.fb3.x = _k.fx + ((_tx - _k.fx) * _kk3);
                _k.fb3.y = _k.fy + ((_ty - _k.fy) * _kk3);
                _k.fb3.image_xscale = 2 + (sin(_k.t * 1.3) * 0.25);
                _k.fb3.image_yscale = _k.fb3.image_xscale;
                knight_fire_ember(_k.fb3.x, _k.fb3.y, point_direction(_tx, _ty, _k.fx, _k.fy) + random_range(-35, 35), 1.5 + random(1.5), 1, _k.blue);
            }
            if (_t2 == _k.tn)
            {
                if (i_ex(_k.fb3))
                {
                    with (_k.fb3)
                        instance_destroy();
                }
                _k.fb3 = noone;
                for (var _b4 = 0; _b4 < 10; _b4++)
                    knight_fire_ember(_tx, _ty, _b4 * 36, 4, 1.4, _k.blue);
                if (i_ex(global.monsterinstance[_k.star]))
                {
                    var _fire2 = instance_create(_tx, _ty, obj_firespell);
                    _fire2.damage = _k.dmg;
                    _fire2.star = _k.star;
                    _fire2.caster = _k.caster;
                    _fire2.target = global.monsterinstance[_k.star];
                    _fire2.blue = _k.blue;
                }
            }
        }
        if (_k.t > 2 && _k.t < (2 + _k.tn))
        {
            var _kk = (_k.t - 2) / _k.tn;
            var _cx = _k.fx + ((_tx - _k.fx) * _kk);
            var _cy = _k.fy + ((_ty - _k.fy) * _kk);
            var _bs2 = (_k.blue == 1) ? spr_bluefire_ball : spr_spell_fireball;
            if (!i_ex(_k.fb))
            {
                _k.fb = instance_create(_cx, _cy, obj_animation);
                with (_k.fb)
                {
                    sprite_index = _bs2;
                    image_speed = 0.2;
                    image_xscale = 2;
                    image_yscale = 2;
                    depth = -20;
                }
            }
            _k.fb.x = _cx;
            _k.fb.y = _cy;
            if (_k.blue == 2)
            {
                // the red ball and the blue twin swap sides as they fly
                var _pa = point_direction(_k.fx, _k.fy, _tx, _ty) + 90;
                var _hw = sin(_k.t * 0.9) * 16;
                _k.fb.x = _cx + lengthdir_x(_hw, _pa);
                _k.fb.y = _cy + lengthdir_y(_hw, _pa);
                if (!i_ex(_k.fb2))
                {
                    _k.fb2 = instance_create(_cx, _cy, obj_animation);
                    with (_k.fb2)
                    {
                        sprite_index = spr_bluefire_ball;
                        image_speed = 0.2;
                        image_xscale = 2;
                        image_yscale = 2;
                        depth = -20;
                    }
                }
                _k.fb2.x = _cx - lengthdir_x(_hw, _pa);
                _k.fb2.y = _cy - lengthdir_y(_hw, _pa);
                _k.fb2.image_angle = _k.fb.image_angle;
                _k.fb2.image_xscale = _k.fb.image_xscale;
                _k.fb2.image_yscale = _k.fb.image_xscale;
            }
            _k.fb.image_angle = point_direction(_k.fx, _k.fy, _tx, _ty);
            _k.fb.image_xscale = 2 + (sin(_k.t * 1.3) * 0.25);
            _k.fb.image_yscale = _k.fb.image_xscale;
            var _back = point_direction(_tx, _ty, _k.fx, _k.fy);
            knight_fire_ember(_cx, _cy, _back + random_range(-35, 35), 1.5 + random(1.5), 1, (_k.blue == 2) ? 0 : _k.blue);
            knight_fire_ember(_cx, _cy, _back + random_range(-60, 60), 1 + random(1), 0.8, (_k.blue == 2) ? 1 : _k.blue);
        }
        if (_k.ice >= 0 && _k.t == max(3, (2 + _k.tn) - 3) && i_ex(global.monsterinstance[_k.star]))
        {
            var _ic = instance_create(_tx, _ty, obj_icespell);
            _ic.damage = _k.idmg;
            _ic.star = _k.star;
            _ic.caster = _k.ice;
            _ic.target = global.monsterinstance[_k.star];
        }
        if (_k.t == (2 + _k.tn) && _k.t > 2)
        {
            if (i_ex(_k.fb))
                with (_k.fb)
                    instance_destroy();
            if (i_ex(_k.fb2))
                with (_k.fb2)
                    instance_destroy();
            for (var _b2 = 0; _b2 < 10; _b2++)
                knight_fire_ember(_tx, _ty, _b2 * 36, 4, 1.4, (_k.blue == 2) ? (_b2 mod 2) : _k.blue);
            if (i_ex(global.monsterinstance[_k.star]))
            {
                var _fire = instance_create(_tx, _ty, obj_firespell);
                _fire.damage = _k.dmg;
                _fire.star = _k.star;
                _fire.caster = _k.caster;
                _fire.target = global.monsterinstance[_k.star];
                _fire.blue = _k.blue;
            }
        }
        if (_k.t >= (_k.dbl ? max(43, 19 + _k.tn) : 26))
        {
            if (i_ex(_k.fb3))
            {
                with (_k.fb3)
                    instance_destroy();
            }
            if (i_ex(_k.fb))
                with (_k.fb)
                    instance_destroy();
            if (i_ex(_k.fb2))
                with (_k.fb2)
                    instance_destroy();
            if (i_ex(_hero) && _k.oss != -1)
            {
                var _oss = _k.oss;
                var _osf = _k.osf;
                with (_hero)
                {
                    spellsprite = _oss;
                    spellframes = _osf;
                    if (state == 2)
                        state = 0;
                    attacktimer = 0;
                    itemed = 0;
                }
            }
            if (_k.ice >= 0 && i_ex(global.charinstance[_k.ice]))
            {
                with (global.charinstance[_k.ice])
                {
                    if (state == 2)
                        state = 0;
                    attacktimer = 0;
                    itemed = 0;
                }
            }
            global.knight_ks = undefined;
            return 0;
        }
    }
    if (_k.t >= 32 && _k.kind != 5 && _k.kind != 7)
    {
        if (_k.kind == 4)
        {
            var _pe = knight_soul_slot(4);
            if (_pe >= 0 && i_ex(global.charinstance[_pe]))
            {
                global.faceaction[_pe] = 0;
                with (global.charinstance[_pe])
                {
                    if (state == 2 || state == 6)
                        state = 0;
                    attacktimer = 0;
                    acttimer = 0;
                }
            }
        }
        if (_pose)
            scr_act_charsprite_end();
        global.knight_ks = undefined;
    }
    return 0;
}

// In a hub fight Kris uses their magic list (ACT entry + spells) once they have X-Slash or Red Buster
// and the ACT entry (spell 7); without the ACT entry they keep the normal ACT list so ACT is never lost.
function knight_kris_menu()
{
    if (!(variable_global_exists("knight_run") && global.knight_run == 1))
        return false;
    var _act = false;
    var _sp = false;
    for (var _i = 0; _i < 12; _i++)
    {
        var _v = global.spell[1][_i];
        if (_v == 7)
            _act = true;
        if (_v == 1 || _v == 5 || _v == 6 || _v == 12 || _v == 14)
            _sp = true;
    }
    return (_act && _sp);
}

function knight_kris_actpick(_slot)
{
    // build 50: Flowery's ACT entry (27) opens his ACT list in his MAGIC menu
    if (global.char[global.charturn] == 5 && global.battlespell[_slot][global.bmenucoord[2][global.charturn]] == 27 && !knight_fl_act_on())
        return knight_fl_act_open();
    return (global.char[global.charturn] == 1 && knight_kris_menu() && global.battlespell[_slot][global.bmenucoord[2][global.charturn]] == 7);
}

// the menu an ACT entry opens: Kris's ACT list (11), Flowery's ACTs in his MAGIC menu (2)
function knight_actpick_menu(_slot)
{
    return (global.char[global.charturn] == 5) ? 2 : 11;
}

// true while Ralsei is in the normal cast pose of a FireShock (before the throw scene): the hero object then draws the Chapter 5 fireball frames
function knight_fire_pose(_slot)
{
    if (!(variable_global_exists("knight_run") && global.knight_run == 1))
        return false;
    if (_slot < 0 || _slot > 2 || (global.charspecial[_slot] != 13 && global.charspecial[_slot] != 15) || global.char[_slot] != 3)
        return false;
    return is_undefined(global.knight_ks);
}

// Noelle's own spells (Heal Prayer, SleepMist, IceShock): a Chapter 3 save carries none for her (she is not in the party
// there), so in the hub she had only Frostfire. When her list has none of the three, they are put first, then whatever
// else she had (SnowGrave, Frostfire, ...). A list that has any of them is the player's own choice and is left alone.
function knight_noelle_defaults()
{
    var _noe = [2, 8, 9];
    var _row = [];
    var _has = 0;
    for (var _i = 0; _i < 12; _i++)
    {
        _row[_i] = global.spell[4][_i];
        if (_row[_i] == 2 || _row[_i] == 8 || _row[_i] == 9)
            _has++;
    }
    if (_has > 0)
        return 0;
    var _k = 0;
    for (var _w = 0; _w < 3; _w++)
        global.spell[4][_k++] = _noe[_w];
    for (var _i = 0; _i < 12 && _k < 12; _i++)
    {
        if (_row[_i] != 0)
            global.spell[4][_k++] = _row[_i];
    }
    while (_k < 12)
        global.spell[4][_k++] = 0;
    return 1;
}

// Kris starts the hub with X-Slash and Red Buster in free spell slots (put back when the hub is left); Ralsei gets FireShock the same way
function knight_kris_defaults()
{
    var _has13 = false;
    for (var _fi = 0; _fi < 12; _fi++)
    {
        if (global.spell[3][_fi] == 13)
            _has13 = true;
    }
    if (!_has13)
    {
        for (var _fi = 0; _fi < 12; _fi++)
        {
            if (global.spell[3][_fi] == 0)
            {
                global.spell[3][_fi] = 13;
                break;
            }
        }
    }
    knight_noelle_defaults();
    // Frostfire (15) for both Ralsei and Noelle
    for (var _fc = 3; _fc <= 4; _fc++)
    {
        var _has15 = false;
        for (var _fi = 0; _fi < 12; _fi++)
        {
            if (global.spell[_fc][_fi] == 15)
                _has15 = true;
        }
        if (!_has15)
        {
            for (var _fi = 0; _fi < 12; _fi++)
            {
                if (global.spell[_fc][_fi] == 0)
                {
                    global.spell[_fc][_fi] = 15;
                    break;
                }
            }
        }
    }
    var _want = [7, 1, 5, 6, 12, 14];
    for (var _w = 0; _w < 6; _w++)
    {
        var _has = false;
        for (var _i = 0; _i < 12; _i++)
        {
            if (global.spell[1][_i] == _want[_w])
                _has = true;
        }
        if (_has)
            continue;
        for (var _i = 0; _i < 12; _i++)
        {
            if (global.spell[1][_i] == 0)
            {
                global.spell[1][_i] = _want[_w];
                break;
            }
        }
    }
}

// Red Buster and Dual Heal are Kris's SOUL power (hub fights only): Kris chooses them, Susie (Red Buster) or Ralsei (Dual Heal)
// performs, and that partner's own command for the turn is used up (like the ACT versions).
// True = the entry cannot be chosen: not Kris, partner missing or down, or the partner already chose (they act after Kris).
function knight_soul_partner(_spell)
{
    if (_spell == 5) return 2;
    if (_spell == 6) return 3;
    if (_spell == 12) return 4;
    if (_spell == 14) return 3;
    return 0;
}

// the character whose command a spell uses up when _ch chooses it (0 = none): Kris's SOUL spells -> Susie / Ralsei / Noelle / Ralsei;
// Frostfire (15, Ralsei or Noelle) -> the other one of the two
function knight_kris_in_party()
{
    for (var _i = 0; _i < 3; _i++)
    {
        if (global.char[_i] == 1)
            return true;
    }
    return false;
}

// Dual Heal without Kris in the party: Ralsei and Noelle do it together (the other one's command is used up)
function knight_duo_heal_mode()
{
    return (variable_global_exists("knight_run") && global.knight_run == 1 && !knight_kris_in_party());
}

function knight_partner_of(_spell, _ch)
{
    if (_spell == 6 && knight_duo_heal_mode())
    {
        if (_ch == 3) return 4;
        if (_ch == 4) return 3;
        return 0;
    }
    if (_spell == 15)
    {
        if (_ch == 3) return 4;
        if (_ch == 4) return 3;
        return 0;
    }
    if (_ch != 1)
        return 0;
    return knight_soul_partner(_spell);
}

// head icon of the partner a SOUL spell needs (Susie / Ralsei / Noelle), -1 for any other spell
function knight_soul_icon(_slot, _i)
{
    if (!(variable_global_exists("knight_run") && global.knight_run == 1))
        return -1;
    var _sp = knight_partner_of(global.battlespell[_slot][_i], global.char[_slot]);
    if (_sp == 2) return spr_headsusie;
    if (_sp == 3) return spr_headralsei;
    if (_sp == 4) return spr_headnoelle;
    return -1;
}

// A hit must land on a party slot that holds a living character. The knight's own redirect code in scr_damage looks at hp[1..3] by
// character and can pick an empty slot (e.g. after Ralsei is lost) or a downed one, so Noelle could never be hit properly.
function knight_fix_target(_t)
{
    if (_t < 0 || _t > 2)
        return _t;
    if (global.char[_t] > 0 && global.hp[global.char[_t]] > 0)
        return _t;
    var _n = 0;
    var _ok = [0, 0, 0];
    for (var _i = 0; _i < 3; _i++)
    {
        if (global.char[_i] > 0 && global.hp[global.char[_i]] > 0)
        {
            _ok[_n] = _i;
            _n++;
        }
    }
    if (_n == 0)
        return _t;
    return _ok[irandom(_n - 1)];
}

function knight_soul_slot(_char)
{
    for (var _i = 0; _i < 3; _i++)
    {
        if (global.char[_i] == _char && global.hp[_char] > 0)
            return _i;
    }
    return -1;
}

// first living member of that character in a party slot AFTER _after (so a duplicate in an earlier slot does not hide a usable partner)
function knight_soul_slot_after(_char, _after)
{
    for (var _i = _after + 1; _i < 3; _i++)
    {
        if (global.char[_i] == _char && global.hp[_char] > 0)
            return _i;
    }
    return -1;
}

// a living member of that character in any slot OTHER than _slot, preferring a later one (its command can then be used up); -1 if none
function knight_partner_slot(_char, _slot)
{
    var _l = knight_soul_slot_after(_char, _slot);
    if (_l >= 0)
        return _l;
    for (var _i = 0; _i < _slot; _i++)
    {
        if (global.char[_i] == _char && global.hp[_char] > 0)
            return _i;
    }
    return -1;
}

function knight_redbuster_blocked(_slot, _i)
{
    if (!(variable_global_exists("knight_run") && global.knight_run == 1))
        return false;
    var _spell = global.battlespell[_slot][_i];
    var _sp0 = knight_soul_partner(_spell);
    if (_sp0 == 0 && _spell != 15)
        return false;
    var _ch = global.char[_slot];
    if (_spell == 6 && knight_duo_heal_mode())
    {
        if (_ch != 3 && _ch != 4)
            return true;
    }
    else if (_sp0 != 0 && _ch != 1)
        return true;
    if (_spell == 15 && _ch != 3 && _ch != 4)
        return true;
    var _sp = knight_partner_of(_spell, _ch);
    return (knight_partner_slot(_sp, _slot) < 0);
}

// called when a spell is confirmed: Kris's SOUL spell uses up the partner's command
function knight_soul_lock()
{
    if (!(variable_global_exists("knight_run") && global.knight_run == 1))
        return 0;
    var _t = global.charturn;
    if (_t < 0 || _t > 2)
        return 0;
    var _sp = knight_partner_of(global.charspecial[_t], global.char[_t]);
    if (_sp == 0)
        return 0;
    var _ps = knight_soul_slot_after(_sp, _t);
    if (_ps < 0 || _ps == _t)
        return 0;
    global.acting[_ps] = 1;
    global.faceaction[_ps] = 6;
    global.charaction[_ps] = 9;
    if (!is_array(global.knight_lockslots))
        global.knight_lockslots = [0, 0, 0];
    global.knight_lockslots[_ps] = 1;
    return 1;
}

// The partner whose command was used up is held in the ACT pose only while the spell plays. Once the turn's actions are over (the
// battle moves on to the return / enemy phase) the pose is dropped, otherwise the partner stays posed through the whole attack.
function knight_lock_release()
{
    if (!is_array(global.knight_lockslots))
        return 0;
    if (!(variable_global_exists("myfight") && global.myfight >= 4))
        return 0;
    for (var _i = 0; _i < 3; _i++)
    {
        if (global.knight_lockslots[_i] != 1)
            continue;
        global.knight_lockslots[_i] = 0;
        global.faceaction[_i] = 0;
        if (i_ex(global.charinstance[_i]))
        {
            with (global.charinstance[_i])
            {
                if (state == 2 || state == 6)
                    state = 0;
                acttimer = 0;
                attacktimer = 0;
            }
        }
    }
    return 1;
}

// Ice Shock in the Chapter 3 knight fights: the game's own formula (30 per Magic point over 10, +90) is far stronger than the Rude Buster the
// knights are tuned around, so in the mods it uses Rude Buster's own formula and knight scaling, x1.2 (Ice Shock costs more TP).
// Kaizo Knight keeps the game's formula (it divides Ice Shock damage itself inside the Ice Shock object).
function knight_iceshock_damage(_slot, _star, _vanilla)
{
    if (global.knight_variant == 1)
        return _vanilla;
    if (!(global.chapter == 3 && i_ex(obj_knight_enemy)))
        return _vanilla;
    var _d = ceil(((global.battlemag[_slot] * 5) + (global.battleat[_slot] * 11)) - (global.monsterdf[_star] * 3));
    _d = ceil(_d * (obj_knight_enemy.damagereduction + 0.65));
    return max(1, ceil(_d * 0.5));
}

// FireShock spark (Chapter 5 small flame hexagon in its "burst" mode: spins, slows down, fades out and removes itself); _blue = Heatwave's blue copy
function knight_fire_ember(_x, _y, _dir, _spd, _sc, _blue)
{
    var _e = instance_create(_x, _y, obj_firespell_hexagon);
    _e.sprite_index = (_blue == 1) ? spr_bluefire_smallflame : spr_firespell_smallflame;
    _e.con = 1;
    _e.image_xscale = _sc;
    _e.image_yscale = _sc;
    _e.direction = _dir;
    _e.speed = _spd;
    _e.friction = 0.2;
    _e.depth = -19;
    return _e;
}

// Ralsei drops whatever pose he is in and winds up the fireball (Chapter 5 cast sprite, blue for Heatwave); remembers his normal cast sprite once
function knight_fire_windup(_slot, _k)
{
    if (_slot < 0 || !i_ex(global.charinstance[_slot]))
        return 0;
    var _h = global.charinstance[_slot];
    if (_k.oss == -1)
    {
        _k.oss = _h.spellsprite;
        _k.osf = _h.spellframes;
    }
    var _sp = (_k.blue == 1) ? spr_ralsei_spell_bluefireball_right : spr_ralsei_spell_fireball_right;
    sprite_set_offset(_sp, 7, -5);
    global.faceaction[_slot] = 0;
    with (_h)
    {
        spellsprite = _sp;
        spellframes = 5;
        state = 2;
        itemed = 1;
        force = 0;
        attacktimer = 0;
    }
    return 1;
}

// Noelle drops the (locked) ACT pose and plays her own spell-cast animation (the hero object's state 2 draws spellsprite)
function knight_ice_windup(_slot)
{
    if (_slot < 0 || !i_ex(global.charinstance[_slot]))
        return 0;
    global.faceaction[_slot] = 0;
    with (global.charinstance[_slot])
    {
        state = 2;
        itemed = 1;
        force = 0;
        attacktimer = 0;
    }
    return 1;
}

// FireShock (Chapter 5 spell, Ralsei): the Ice Shock number for Ralsei's stats; Kaizo Knight uses its own block division like its Ice Shock
function knight_fireshock_base(_slot, _star)
{
    var _v = ceil((clamp(global.battlemag[_slot] - 10, 1, 999) * 30) + 90 + random(10));
    if (global.knight_variant == 1)
        return ceil(_v / knight_kaizo_div());
    return knight_iceshock_damage(_slot, _star, _v);
}

// FireShock (Chapter 5 spell, Ralsei): Ice Shock's number for Ralsei's stats times a factor, and never below Noelle's own Ice Shock times a floor factor
// when she is alive in the party. Kaizo and Violet Knight get bigger factors (Kaizo divides it by its guard, Violet's HP is spread over more turns).
//   normal knights: x2.1, floor Noelle x1.5      Kaizo: x2.5, floor x2      Violet: x2.8, floor x2   (build 37: was 1.3 / 1.6 / 1.8)
function knight_fireshock_damage(_slot, _star)
{
    var _m = 2.1;
    var _fl = 1.5;
    if (global.knight_variant == 1)
    {
        _m = 2.5;
        _fl = 2;
    }
    if (global.knight_variant == 3)
    {
        _m = 2.8;
        _fl = 2;
    }
    var _f = ceil(knight_fireshock_base(_slot, _star) * _m);
    var _n = knight_soul_slot(4);
    if (_n >= 0 && _n != _slot)
        _f = max(_f, ceil(knight_fireshock_base(_n, _star) * _fl));
    return max(1, _f);
}

// SoulShock: Kris shines their SOUL on Noelle, who casts a red Ice Shock. Balanced as a combo: 1.3x what Kris's X-Slash plus
// Noelle's own Ice Shock would deal together (those two use two commands as well), so it beats them a little, not by a lot.
function knight_soulshock_damage(_nslot, _kslot, _star)
{
    var _ice = knight_iceshock_damage(_nslot, _star, ceil((clamp(global.battlemag[_nslot] - 10, 1, 999) * 30) + 90 + random(10)));
    var _xs = knight_xslash_damage(_kslot, _star);
    return ceil((_ice + _xs) * 1.3);
}

// Heatwave: Kris shines their SOUL on Ralsei, who throws a blue FireShock: 1.3x (X-Slash + FireShock), same idea as Permafrost
function knight_heatwave_damage(_rslot, _kslot, _star)
{
    return ceil((knight_fireshock_damage(_rslot, _star) + knight_xslash_damage(_kslot, _star)) * 1.3);
}

// Frostfire: Noelle's Ice Shock and Ralsei's FireShock together, 1.2x each (two commands' worth of casting in one). Returns the FireShock half;
// the Ice Shock half goes in the kspell struct (Kaizo divides the Ice Shock number inside the Ice Shock object, so it gets the game's raw number there)
function knight_frostfire_start(_caster, _star)
{
    var _rs = knight_soul_slot(3);
    var _ns = knight_soul_slot(4);
    if (_rs < 0 || _ns < 0)
        return false;
    var _fire = ceil(knight_fireshock_damage(_rs, _star) * 1.2);
    var _raw = ceil((clamp(global.battlemag[_ns] - 10, 1, 999) * 30) + 90 + random(10));
    var _ice = ceil(knight_iceshock_damage(_ns, _star, _raw) * 1.2);
    if (global.automiss[_star] == 1)
    {
        _fire = 0;
        _ice = 0;
    }
    knight_kspell_start(7, _caster, _star, _fire);
    global.knight_ks.idmg = _ice;
    return true;
}

// Dual Heal as the game does it (heals every party slot from the caster's magic), run when the soul scene reaches it
function knight_dualheal_apply(_ps, _mult)
{
    var _healnum = ceil(global.battlemag[(_ps >= 0) ? _ps : 0] * _mult);
    for (var _i = 0; _i < 3; _i++)
    {
        if (!i_ex(global.charinstance[_i]))
            continue;
        // Kaizo's freeze: a frozen character cannot be healed (same check the Kaizo heal spells make)
        if (i_ex(obj_knight_enemy) && variable_instance_exists(obj_knight_enemy, "k_freeze") && global.char[_i] >= 1 && global.char[_i] <= 3)
        {
            if (obj_knight_enemy.k_freeze[global.char[_i]])
                continue;
        }
        scr_heal(_i, _healnum);
        global.charinstance[_i].healnum = _healnum;
        with (global.charinstance[_i])
        {
            var _ha = instance_create(x, y, obj_healanim);
            _ha.target = id;
            var _dw = scr_dmgwriter_selfchar();
            with (_dw)
            {
                delay = 8;
                type = 3;
            }
            if (global.hp[global.char[myself]] >= global.maxhp[global.char[myself]])
            {
                with (_dw)
                    specialmessage = 3;
            }
            _dw.damage = _healnum;
            tu += 1;
        }
    }
}

// ---------- Party-size damage scaling (an ESTIMATE, not play-tested) ----------
// The fights are tuned for Kris + Susie + Ralsei. With fewer party slots filled, the party deals less damage per round
// and every hit lands on fewer bodies, so both are scaled. The full trio is exactly 1.0 (nothing changes).
// All tuning lives in this one function: [dealt, taken] multipliers for 1, 2 and 3 filled slots.
function knight_scale_factors(_n)
{
    if (_n >= 3) return [1, 1];
    if (_n == 2) return [1.5, 0.85];
    return [3, 0.7];
}

function knight_scale_dealt(_d)
{
    if (_d <= 0 || !knight_active()) return _d;
    var _n = knight_party_count();
    if (_n >= 3 || _n < 1) return _d;
    var _f = knight_scale_factors(_n);
    return max(1, ceil(_d * _f[0]));
}

// Number of party slots holding the same character as slot _slot (duplicates/clones). They share one HP bar,
// so each hit on a clone is split by this count; otherwise N clones would all pour their hits into one bar.
function knight_clone_count(_slot)
{
    if (_slot < 0 || _slot > 3) return 1;
    var _c = global.char[_slot];
    if (_c <= 0) return 1;
    var _k = 0;
    for (var _i = 0; _i < 3; _i++)
    {
        if (global.char[_i] == _c) _k++;
    }
    return max(1, _k);
}

function knight_scale_taken(_d, _slot)
{
    if (!knight_active()) return _d;
    // build 43: online, one flat scale for everybody
    if (knight_lu_kind_of(global.krun.cfg) == "online")
        return kfo_scale_taken(_d);
    knight_thorns_mark(_slot);
    var _m2 = (variable_struct_exists(global.krun.cfg, "c_dmg2") && global.krun.cfg.c_dmg2 == 1) ? 2 : 1;
    _m2 *= knight_wr_taken_mult();
    if (_d <= 1) return ceil(_d * _m2);
    var _out = _d;
    var _cc = knight_clone_count(_slot);
    if (_cc > 1) _out = max(1, ceil(_out / _cc));
    var _n = knight_party_count();
    if (_n < 3 && _n >= 1 && _cc <= 1)
    {
        var _f = knight_scale_factors(_n);
        _out = max(1, ceil(_out * _f[1]));
    }
    // build 50: the custom characters' guards (Flowery's Afinihug on that member, his Honey Kiss on the knight)
    _out = max(1, knight_cc_taken(_out, _slot));
    return ceil(_out * _m2);
}


// build 50: online, the Knight's opening scene in the cold place (obj_ch3_PTB02: the party walks up, the Knight draws its
// sword) is skipped - the scene jumps to where the fight starts (its con 4, with the Knight's battle marker made as the sword
// animation would leave it, the STANDARD mode the online fight always uses)
function kfo_skip_intro()
{
    if (!instance_exists(obj_ch3_PTB02) || instance_exists(obj_battlecontroller))
        return 0;
    with (obj_ch3_PTB02)
    {
        if (!variable_instance_exists(id, "con") || !variable_instance_exists(id, "knight_marker") || !variable_instance_exists(id, "roaring_knight"))
            continue;
        if (con < 3 || con >= 4 || !instance_exists(roaring_knight))
            continue;
        with (obj_dialoguer)
            instance_destroy();
        with (obj_writer)
            instance_destroy();
        if (knight_marker == -4)
        {
            var _kv = global.knight_variant;
            var _spr = spr_roaringknight_sword_appear_new;
            if (_kv == 1)
                _spr = spr_roaringknight_sword_appear_new__v1;
            else if (_kv == 3)
                _spr = spr_roaringknight_sword_appear_new__v3;
            else if (_kv == 4)
                _spr = spr_roaringknight_sword_appear_new__v4;
            else if (_kv == 5)
                _spr = spr_roaringknight_sword_appear_new__v5;
            knight_marker = scr_dark_marker(roaring_knight.x, roaring_knight.y, _spr);
            knight_marker.image_index = 11;
        }
        roaring_knight.visible = 0;
        roaring_knight.state = 99;
        sword_draw = false;
        sword_draw_ready = true;
        customcon = 1;
        global.msc = -1;
        global.knight_mode = 2;
        global.choice = 2;
        global.kaizo_intro = 1;
        kaizo_settings_save();
        con = 4;
    }
    return 1;
}

// build 50: SOLO in a hub fight - the one member stands level with the knight (the encounter's middle place, where the second
// member of a party of three stands), not at the top place. Runs in obj_battlecontroller's Create just before the heroes are made.
function knight_solo_lineup()
{
    if (!knight_active() || !is_struct(global.krun))
        return 0;
    if (!variable_global_exists("heromakex") || !is_array(global.heromakex) || array_length(global.heromakex) < 2)
        return 0;
    var _n = 0;
    var _s = -1;
    for (var _i = 0; _i < 3; _i++)
    {
        if (global.char[_i] != 0)
        {
            _n++;
            _s = _i;
        }
    }
    if (_n != 1 || _s == 1)
        return 0;
    global.heromakex[_s] = global.heromakex[1];
    global.heromakey[_s] = global.heromakey[1];
    return 1;
}


// build 50: practice mode keeps the party's HP up (the knights' own code does it for characters 1-4): the custom characters
// (Flowery, ...) in the party get the same - _m times their max HP
function knight_prac_hp_cc(_m)
{
    for (var _c = 5; _c < min(array_length(global.hp), array_length(global.maxhp)); _c++)
    {
        if (scr_havechar(_c))
            global.hp[_c] = global.maxhp[_c] * _m;
    }
    return 1;
}


// build 50: the Knight Hub's sign stands in the snow zone only while the story is at the Roaring Knight (Chapter 3 plot 310 -
// 329: the fight's own setup, obj_ch3_PTB02, exists only then). A save from before or after that has no sign: a note over the
// player says so and which save to load, instead of nothing (drawn by the player's own Draw, in the room, while no hub run is on)
function knight_hub_hint_draw()
{
    if (room != room_dw_snow_zone || (global.plot >= 310 && global.plot < 330))
        return 0;
    if (variable_global_exists("knight_run") && global.knight_run == 1)
        return 0;
    var _cx = camerax() + 320;
    var _cy = cameray() + 24;
    draw_set_alpha(0.75);
    draw_set_color(c_black);
    draw_rectangle(_cx - 300, _cy - 6, _cx + 300, _cy + 54, false);
    draw_set_alpha(1);
    draw_set_halign(fa_center);
    draw_set_color(c_yellow);
    knight_txt_small(_cx, _cy, kdr_on() ? "DRBR: no hub sign with this save." : "KNIGHT HUB: no sign with this save.");
    draw_set_color(c_white);
    knight_txt_small(_cx, _cy + 16, "It is only here right before the Roaring Knight fight.");
    // DRBR (update 10): the DRBR install starts in the right save by itself (continue mode can carry a later one)
    if (kdr_on())
        knight_txt_small(_cx, _cy + 32, "DRBR Launcher > SETTINGS: start from the DRBR starting save.");
    else
        knight_txt_small(_cx, _cy + 32, "Load SAVE SLOT 3 (the tester pack's \"Save file\").");
    draw_set_halign(fa_left);
    return 1;
}
