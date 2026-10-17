
// ===== Knight Hub menu: logic (state in global.knight_ui) =====
// Built like DELTARUNE's own dark-world menu: five tab buttons on the top bar (KNIGHT, PARTY, POWER, RULES,
// CONFIG), the box in the middle, the party panel at the bottom. While a tab is open the top bar shows the
// description of the highlighted row. Z = confirm, X = back, C = start the fight from any page.
global.knight_ui = undefined;

function knight_ui_tabs()
{
    return 5;
}

function knight_ui_open_state()
{
    return {
        tab: 0, focus: 0, lv: 0,
        krow: 0, kpage: knight_page_of_ch(3),
        pslot: 0, prow: 0, ppick: 0, pscroll: 0,
        sslot: 0, srow: 0, sscroll: 0,
        rrow: 0, crow: 0,
        sub: "", subrow: 0, rec_i: 0, rec_def: false, cr_i: 0, cr_page: 0, lo_g: 0, lo_i: 1, tag_row: 0, tag_slot: 0, at_row: 0, at_scroll: 0, rmx_row: 0,
        onl_row: 0, lob_row: 0, set_row: 0, set_preset: 0,
        modal: undefined, warn: "", warnok: false, warntimer: 0, go: 0, gotimer: 0, inputdelay: 3, siner: 0,
        tp: 0, bp: 0, closing: 0, pv_msg: "", notice: "", cache_t: -1, cache_conf: ""
    };
}

function knight_ui_init()
{
    knight_store_load();
    global.knight_ui = knight_ui_open_state();
    global.knight_ui.notice = (global.knight_store_status == "new" || global.knight_store_status == "ok") ? "" : global.knight_store_status;
    knight_cfg_sanitize(global.knight_cfg);
    // build 50: the page of the knight that is set up
    global.knight_ui.kpage = knight_page_of_ch(knight_chapter_of(global.knight_cfg.knight));
    // the cursor starts on the fight that is set up
    var _f = knight_ui_fights();
    for (var _i = 0; _i < array_length(_f); _i++)
    {
        if (knight_ui_fight_is_current(_f[_i]))
            global.knight_ui.krow = _i;
    }
    // build 43: back from an online match - straight to the room; build 45: the sign opens on the room while you are in one
    if (is_struct(global.kfo) && (global.kfo.reopen || kfo_in_room()))
    {
        global.kfo.reopen = false;
        var _u = global.knight_ui;
        _u.tab = 0;
        _u.focus = 1;
        _u.krow = array_length(_f) - 1;
        _u.sub = kfo_in_room() ? "lobby" : "online";
        _u.notice = "";
    }
}

function knight_menu_open(_sign)
{
    knight_ensure_ctrl();
    // build 49: Steam starts with the hub's menu (not only with the ONLINE page), so invites from friends arrive
    kfo_get();
    kfo_steam_load();
    knight_store_load();
    if (knight_snapshot_take())
    {
        knight_kris_defaults();
        // bring back the spell and equipment sets from the last time the hub was used
        if (string_length(global.knight_last_spells) == 48)
            knight_spells_from_string(global.knight_last_spells);
        knight_noelle_defaults();
        if (string_length(global.knight_last_equip) == 12)
            knight_equip_from_string(global.knight_last_equip);
        // build 50: Flowery's own techniques and gear
        knight_cc_from_string(global.knight_last_fl);
    }
    knight_cc_stats();
    knight_mantle_fix();
    if (!instance_exists(obj_knight_menu))
        instance_create_depth(0, 0, -99990, obj_knight_menu);
}

// starts the slide-out; the menu object removes itself once the bars are gone (knight_ui_step)
function knight_menu_close()
{
    var _u = global.knight_ui;
    knight_preview_stop();
    if (is_struct(_u) && _u.closing == 0)
    {
        _u.closing = 1;
        snd_play(snd_smallswing);
        return 0;
    }
    knight_menu_finish_close();
}

function knight_menu_finish_close()
{
    knight_preview_stop();
    // build 45: closing the menu keeps you in an online room - the cold place is its lobby (LEAVE ROOM leaves it); a
    // connection that is still being made stops, and a PRACTICE room (you and bots) ends
    if (kfo_busy() || (kfo_in_room() && kfo_prac_room()))
        kfo_close("");
    knight_store_save();
    knight_snapshot_restore("leave");
    global.knight_orig = undefined;
    global.interact = 0;
    with (obj_mainchara)
        onebuffer = 5;
    with (obj_knight_menu)
        instance_destroy();
}

function knight_ui_warn(_t)
{
    global.knight_ui.warn = _t;
    global.knight_ui.warnok = false;
    global.knight_ui.warntimer = 90;
    snd_play(snd_cantselect);
}

// a short confirmation in the top bar (yellow)
function knight_ui_tell(_t)
{
    global.knight_ui.warn = _t;
    global.knight_ui.warnok = true;
    global.knight_ui.warntimer = 100;
}

function knight_ui_onoff(_v)
{
    return _v ? "ON" : "OFF";
}

function knight_ui_cycle(_v, _d, _n)
{
    return (_v + _d + _n) mod _n;
}

// ---------- KNIGHT tab: the fights you can pick ----------
function knight_ui_fights()
{
    // build 50: the page's chapter - its knights / bosses, then the ones planned for it (COMING SOON); the modes on every page
    var _pg = (is_struct(global.knight_ui) && variable_struct_exists(global.knight_ui, "kpage")) ? global.knight_ui.kpage : knight_page_of_ch(3);
    var _ch = knight_page_ch(_pg);
    var _l = [];
    for (var _k = 0; _k < knight_count(); _k++)
    {
        if (knight_chapter_of(_k) == _ch)
            array_push(_l, { kind: "k", k: _k });
    }
    for (var _p = 0; _p < array_length(global.knight_planned) && KNIGHT_SHOW_PLANNED; _p++)
    {
        var _pl = global.knight_planned[_p];
        if (_pl.ch == _ch && knight_find_key(_pl.key) < 0)
            array_push(_l, { kind: "soon", k: -1, p: _p });
    }
    array_push(_l, { kind: "rush", k: -1 });
    array_push(_l, { kind: "random", k: -1 });
    array_push(_l, { kind: "tag", k: -1 });
    array_push(_l, { kind: "remix", k: -1 });
    array_push(_l, { kind: "online", k: -1 });
    return _l;
}

// build 52: how many of the page's fights are knights (the carousel; the rest are the MODE strip)
function knight_ui_nknights(_f)
{
    var _n = 0;
    for (var _i = 0; _i < array_length(_f); _i++)
    {
        if (_f[_i].kind == "k" || _f[_i].kind == "soon")
            _n++;
    }
    return _n;
}

function knight_ui_fight_label(_f)
{
    if (_f.kind == "rush")
        return "KNIGHT RUSH";
    if (_f.kind == "random")
        return "RANDOM";
    if (_f.kind == "tag")
        return "TAG TEAM";
    if (_f.kind == "remix")
        return "ATTACK REMIX";
    if (_f.kind == "online")
        return "ONLINE";
    if (_f.kind == "soon")
        return global.knight_planned[_f.p].short;
    return knight_reg(_f.k).short;
}

function knight_ui_fight_is_current(_f)
{
    var _c = global.knight_cfg;
    var _cb = knight_cfg_num(_c, "combo");
    if (_f.kind == "rush")
        return (_c.mode == 1);
    if (_f.kind == "tag")
        return (_c.mode == 0 && _cb == 1);
    if (_f.kind == "remix")
        return (_c.mode == 0 && _cb == 2);
    if (_f.kind == "online" || _f.kind == "soon")
        return false;
    if (_f.kind == "random")
        return (_c.mode == 0 && _c.random == 1 && _cb == 0);
    return (_c.mode == 0 && _c.random == 0 && _cb == 0 && _c.knight == _f.k);
}

function knight_ui_fight_select(_f)
{
    var _c = global.knight_cfg;
    if (_f.kind == "rush")
    {
        _c.mode = 1;
        _c.random = 0;
        _c.combo = 0;
    }
    else if (_f.kind == "random")
    {
        _c.mode = 0;
        _c.random = 1;
        _c.combo = 0;
    }
    else if (_f.kind == "tag" || _f.kind == "remix")
    {
        _c.mode = 0;
        _c.random = 0;
        _c.combo = (_f.kind == "tag") ? 1 : 2;
    }
    else
    {
        // another knight: its own attack list, so START AT / REPEAT start over at its first attack
        if (_c.knight != _f.k)
            _c.p_atk = 0;
        _c.mode = 0;
        _c.random = 0;
        _c.combo = 0;
        _c.knight = _f.k;
    }
}

// ---------- RULES tab ----------
// display order: two columns of eight
function knight_ui_rule_ids()
{
    return ["c_nohit", "c_items", "c_heal", "c_hp1", "c_solo", "c_dmg2", "c_halfhp", "c_notp",
            "c_onelife", "c_twin", "c_dark", "c_speed", "c_thorns", "c_time", "rparty", "randchal"];
}

function knight_ui_rule_label(_id)
{
    switch (_id)
    {
        case "c_nohit": return "NO-HIT";
        case "c_items": return "NO ITEMS";
        case "c_heal": return "NO HEALING";
        case "c_hp1": return "1 HP START";
        case "c_solo": return "SOLO";
        case "c_dmg2": return "2X DAMAGE";
        case "c_halfhp": return "HALF MAX HP";
        case "c_notp": return "NO TP";
        case "c_onelife": return "ONE LIFE";
        case "c_twin": return "TWIN KNIGHT";
        case "c_dark": return "DARKNESS";
        case "c_speed": return "HYPER SPEED";
        case "c_thorns": return "THORNS";
        case "c_time": return "TIME LIMIT";
        case "rparty": return "RANDOM PARTY";
        case "randchal": return "RANDOM RULE";
    }
    return string_upper(_id);
}

function knight_ui_rule_desc(_id)
{
    switch (_id)
    {
        case "c_nohit": return "One hit and the attempt is over.#Grazing is fine. Kept in its own records.";
        case "c_items": return "Your items are put away for the#fight and given back afterwards.";
        case "c_heal": return "Healing spells, healing items and#healing bullets do nothing.";
        case "c_hp1": return "The whole party starts the battle#at 1 HP. Healing still works.";
        case "c_solo": return "Fight with exactly one party#member.";
        case "c_dmg2": return "Every hit you take does twice#the damage.";
        case "c_halfhp": return "Everyone's max HP is halved for#the fight.";
        case "c_notp": return "TP stays at 0: no spells and no TP#ACTs. Not for Supercharged Knight.";
        case "c_onelife": return "The fight is lost as soon as#anyone is knocked down.";
        case "c_twin": return "A second knight joins the battle#and attacks at the same time!";
        case "c_dark": return "In the knight's turn only a small#light around your SOUL remains.";
        case "c_speed": return "The whole battle runs 25% faster.#Battle times stay in real seconds.";
        case "c_thorns": return "Each hit also lowers that member's#max HP for the rest of the fight.";
        case "c_time": return "Win before the knight's attack list#plus 10 turns runs out, or lose.";
        case "rparty": return "A random party of 1-3 members for#every fight. Not kept in records.";
        case "randchal": return "One random rule that fits your#party is added when the fight starts.";
    }
    return "";
}

// why a row can't be used right now ("" = usable)
function knight_ui_block(_id)
{
    var _c = global.knight_cfg;
    var _reg = knight_reg(_c.knight);
    var _single = (_c.mode == 0 && _c.random == 0);
    switch (_id)
    {
        case "c_nohit":
            if (_single && _reg.joke) return "Joke fight: no No-Hit, no records.";
            if (_c.practice && _single && _reg.has_practice) return "Not with Practice (CONFIG page).";
            break;
        case "c_time":
            if (_c.practice && _single && _reg.has_practice) return "Not with Practice (CONFIG page).";
            if (knight_cfg_num(_c, "p_mode") == 2 && _single) return "Not with Repeat practice (CONFIG page).";
            break;
        case "c_notp":
            if (_single && _reg.key == "elec") return "Supercharged Knight needs TP to UNLEASH.";
            break;
        case "c_onelife":
            if (_single && _reg.key == "elec") return "Supercharged Knight knocks Kris down by script.";
            if (_c.weird) return "Not with Weird Route (it removes members).";
            break;
        case "c_twin":
            if (knight_cfg_num(_c, "combo") > 0) return "Not with Tag Team or Attack Remix.";
            break;
        case "practice":
            if (_c.mode == 1) return "Practice is not available in Knight Rush.";
            if (knight_cfg_num(_c, "combo") > 0) return "Not in Tag Team or Attack Remix.";
            if (!_reg.has_practice) return "Practice is not available for this knight.";
            if (_c.weird && knight_cfg_num(_c, "p_mode") > 0) return "Start At / Repeat use the normal list: not with Weird Route.";
            break;
        case "c_wstats":
            if (!_c.weird) return "Only used with WEIRD ROUTE on.";
            break;
        case "c_hp1":
            if (knight_cfg_flag(_c, "infhp")) return "Not with INFINITE HP (CONFIG page).";
            break;
        case "infhp":
            if (_c.c_hp1) return "Not with 1 HP START (RULES page).";
            break;
        case "rush_shuffle":
        case "rush_rec":
            if (_c.mode == 0) return "Pick KNIGHT RUSH on the KNIGHT page first.";
            break;
    }
    return "";
}

function knight_ui_rule_toggle(_id)
{
    var _blk = knight_ui_block(_id);
    var _c = global.knight_cfg;
    if (_blk != "" && variable_struct_get(_c, _id) == 0)
    {
        knight_ui_warn(_blk);
        return 0;
    }
    variable_struct_set(_c, _id, 1 - variable_struct_get(_c, _id));
    snd_play(snd_menumove);
}

// ---------- CONFIG tab ----------
function knight_ui_cfg_ids()
{
    return ["song", "weird", "c_wstats", "practice", "infhp", "nh_retry", "hotkeys", "rush_shuffle", "rush_rec", "loadouts", "presets", "records", "credits", "modreset"];
}

function knight_ui_cfg_label(_id)
{
    switch (_id)
    {
        case "song": return "FIGHT SONG";
        case "weird": return "WEIRD ROUTE";
        case "c_wstats": return "WEIRD STATS";
        case "practice": return "PRACTICE";
        case "infhp": return "INFINITE HP";
        case "nh_retry": return "QUICK RETRY";
        case "hotkeys": return "HOTKEYS";
        case "rush_shuffle": return "RUSH ORDER";
        case "rush_rec": return "RUSH HEALING";
        case "loadouts": return "LOADOUTS";
        case "presets": return "PRESETS";
        case "records": return "RECORDS";
        case "credits": return "CREDITS";
        case "modreset": return "RESET MOD SETTINGS";
    }
    return string_upper(_id);
}

// rush healing between fights: one value that maps onto rush_heal / rush_pct
function knight_ui_rushrec_index(_c)
{
    if (_c.rush_heal == 0) return 0;
    if (_c.rush_heal == 2) return 4;
    if (_c.rush_pct >= 70) return 1;
    if (_c.rush_pct >= 40) return 2;
    return 3;
}

function knight_ui_rushrec_set(_c, _i)
{
    switch (_i)
    {
        case 0: _c.rush_heal = 0; break;
        case 1: _c.rush_heal = 1; _c.rush_pct = 75; break;
        case 2: _c.rush_heal = 1; _c.rush_pct = 50; break;
        case 3: _c.rush_heal = 1; _c.rush_pct = 25; break;
        default: _c.rush_heal = 2; break;
    }
}

function knight_ui_cfg_value(_id)
{
    var _c = global.knight_cfg;
    switch (_id)
    {
        case "song": return string_upper(global.knight_songs[_c.song].name);
        case "weird": return knight_ui_onoff(_c.weird);
        case "c_wstats": return knight_ui_onoff(_c.c_wstats);
        case "practice": return knight_ui_practice_value(_c);
        case "hotkeys": return knight_ui_onoff(!knight_cfg_flag(_c, "nohotkeys"));
        case "infhp": return knight_ui_onoff(knight_cfg_flag(_c, "infhp") ? 1 : 0);
        case "nh_retry": return knight_ui_onoff(_c.nh_retry);
        case "rush_shuffle": return _c.rush_shuffle ? "SHUFFLE" : "IN ORDER";
        case "rush_rec":
            if (_c.rush_heal == 0) return "FULL";
            if (_c.rush_heal == 2) return "NONE";
            return string(_c.rush_pct) + "%";
    }
    return "";
}

function knight_ui_cfg_desc(_id)
{
    switch (_id)
    {
        case "song":
            // build 47: the song's credit (artist, where it is from)
            var _sg = global.knight_songs[clamp(global.knight_cfg.song, 0, array_length(global.knight_songs) - 1)];
            if (_sg.file == "@random")
                return (knight_song_on_count() > 0) ? "RANDOM: one of your songs (+ in the song#list, A turns them on / off), new each fight." : "RANDOM: NO SONGS SELECTED - the fight is#silent. Z: the song list, A turns songs on.";
            if (variable_struct_exists(_sg, "by") && _sg.by != "")
                return "BY " + string_upper(_sg.by) + ((_sg.src != "") ? ("#" + _sg.src) : "#< > picks, Z plays a preview.");
            return "Battle song. < > picks, Z: the song list#(C listens). MOD DEFAULT = the mod's own song.";
        case "weird": return "Weird Route save, any party: Side B in#Kaizo/Violet (only Violet takes members).";
        case "c_wstats": return "With WEIRD ROUTE: fight with the#Weird Route file's stats, not yours.";
        case "practice": return "< >: OFF, PICKER (any attack, in the fight),#START AT, REPEAT. Z: choose the attack.";
        case "hotkeys": return "In a fight: R restarts it at once,#hold TAB to fast-forward talk and scenes.";
        case "infhp": return "Party HP never goes down (story#losses still happen). Not recorded.";
        case "nh_retry": return "After a No-Hit or Time Limit loss#the fight restarts right away.";
        case "rush_shuffle": return "KNIGHT RUSH: fight the knights in#menu order or in a shuffled order.";
        case "rush_rec": return "HP restored between Rush fights.#TP resets, items carry over.";
        case "loadouts": return "Ready-made parties: BASE, MAXED and#DUAL MOVES for every party, and x3.";
        case "presets": return "Save and load up to 8 setups#(fight, party, spells, rules, song).";
        case "records": return "Wins, best times, least damage and#no-hit streaks for every knight.";
        case "credits": return "Who made each knight fight#and its music.";
        case "modreset": return "Z: the online settings (SOULs, colour, view,#keys) back to the defaults. " + knight_build_stamp_short();
    }
    return "";
}

function knight_ui_cfg_act(_id, _dir)
{
    var _u = global.knight_ui;
    var _c = global.knight_cfg;
    var _blk = knight_ui_block(_id);
    switch (_id)
    {
        case "song":
            // build 48: Z opens the song list (title and artist of every song; C listens there)
            if (_dir == 0)
            {
                knight_preview_stop();
                knight_songpick_open("off");
                return 0;
            }
            _c.song = knight_ui_cycle(_c.song, _dir, array_length(global.knight_songs));
            knight_preview_stop();
            _u.pv_msg = "";
            snd_play(snd_menumove);
            return 0;
        case "practice":
            if (_dir == 0)
            {
                knight_ui_open_attacks();
                return 0;
            }
            var _pv = knight_ui_practice_index(_c);
            var _nv = knight_ui_cycle(_pv, _dir, 4);
            // skip settings that can't be used now (OFF always can)
            for (var _t = 0; _t < 4 && knight_ui_practice_block(_nv) != ""; _t++)
                _nv = knight_ui_cycle(_nv, _dir, 4);
            if (_nv == _pv)
            {
                knight_ui_warn(knight_ui_practice_block(knight_ui_cycle(_pv, _dir, 4)));
                return 0;
            }
            knight_ui_practice_set(_c, _nv);
            snd_play(snd_menumove);
            return 0;
        case "hotkeys":
            _c.nohotkeys = knight_cfg_flag(_c, "nohotkeys") ? 0 : 1;
            snd_play(snd_menumove);
            return 0;
        case "weird":
        case "c_wstats":
        case "infhp":
        case "nh_retry":
        case "rush_shuffle":
            if (!variable_struct_exists(_c, _id))
                variable_struct_set(_c, _id, 0);
            if (_blk != "" && variable_struct_get(_c, _id) == 0)
            {
                knight_ui_warn(_blk);
                return 0;
            }
            variable_struct_set(_c, _id, 1 - variable_struct_get(_c, _id));
            snd_play(snd_menumove);
            return 0;
        case "rush_rec":
            if (_blk != "")
            {
                knight_ui_warn(_blk);
                return 0;
            }
            knight_ui_rushrec_set(_c, knight_ui_cycle(knight_ui_rushrec_index(_c), (_dir == 0) ? 1 : _dir, 5));
            snd_play(snd_menumove);
            return 0;
        case "modreset":
            // build 49: asks first
            if (_dir != 0)
                return 0;
            knight_ui_modal("kh_reset", "RESET MOD SETTINGS?", ["SOUL settings, your SOUL colour, MATCH VIEW, match keys,", "online song and room settings go back to the defaults.",
                "Kept: name, skin, server, fight setup, records, presets."], [{ t: "Cancel", a: "close" }, { t: "Reset", a: "kh_reset" }]);
            snd_play(snd_select);
            return 0;
        case "loadouts":
        case "presets":
        case "records":
        case "credits":
            if (_dir != 0)
                return 0;
            _u.sub = _id;
            _u.subrow = 0;
            _u.rec_def = false;
            _u.cr_page = 0;
            if (_id == "records")
                _u.rec_i = 0;
            if (_id == "credits")
                _u.cr_i = (global.knight_cfg.mode == 0) ? global.knight_cfg.knight : 0;
            if (_id == "loadouts")
                knight_ui_lo_focus_party();
            snd_play(snd_select);
            return 0;
    }
}

// ---------- PRACTICE: OFF / PICKER / START AT / REPEAT ----------
function knight_ui_practice_index(_c)
{
    if (_c.practice)
        return 1;
    var _pm = knight_cfg_num(_c, "p_mode");
    if (_pm == 1)
        return 2;
    if (_pm == 2)
        return 3;
    return 0;
}

function knight_ui_practice_set(_c, _i)
{
    _c.practice = (_i == 1) ? 1 : 0;
    _c.p_mode = (_i == 2) ? 1 : ((_i == 3) ? 2 : 0);
}

// why a PRACTICE setting can't be used right now ("" = fine): the in-fight PICKER never ends in a win, so not with No-Hit or a
// Time Limit; REPEAT never ends either (no Time Limit)
function knight_ui_practice_block(_i)
{
    var _c = global.knight_cfg;
    if (_i == 0)
        return "";
    var _b = knight_ui_block("practice");
    if (_b != "")
        return _b;
    if (_i == 1 && _c.c_nohit)
        return "The picker: not with No-Hit (RULES page).";
    if (_i == 1 && _c.c_time)
        return "The picker: not with Time Limit (RULES page).";
    if (_i == 3 && _c.c_time)
        return "Repeat: not with Time Limit (RULES page).";
    if (_i >= 2 && _c.weird)
        return "Start At / Repeat use the normal list: not with Weird Route.";
    return "";
}

function knight_ui_practice_value(_c)
{
    switch (knight_ui_practice_index(_c))
    {
        case 1: return "PICKER";
        case 2: return "START AT " + string_upper(knight_reg(_c.knight).atk[clamp(_c.p_atk, 0, array_length(knight_reg(_c.knight).atk) - 1)][2]);
        case 3: return "REPEAT " + string_upper(knight_reg(_c.knight).atk[clamp(_c.p_atk, 0, array_length(knight_reg(_c.knight).atk) - 1)][2]);
    }
    return "OFF";
}

// the attack list page (Z on PRACTICE)
function knight_ui_open_attacks()
{
    var _u = global.knight_ui;
    var _c = global.knight_cfg;
    var _blk = knight_ui_block("practice");
    if (_blk != "")
    {
        knight_ui_warn(_blk);
        return 0;
    }
    _u.sub = "attacks";
    _u.at_row = clamp(_c.p_atk, 0, array_length(knight_reg(_c.knight).atk) - 1);
    _u.at_scroll = clamp(_u.at_row - 4, 0, max(0, array_length(knight_reg(_c.knight).atk) - 9));
    snd_play(snd_select);
    return 1;
}

function knight_ui_step_attacks(_up, _down, _left, _right, _ok)
{
    var _u = global.knight_ui;
    var _c = global.knight_cfg;
    var _l = knight_reg(_c.knight).atk;
    var _n = array_length(_l);
    if (_up || _down)
    {
        _u.at_row = knight_ui_cycle(_u.at_row, _up ? -1 : 1, _n);
        if (_u.at_row < _u.at_scroll)
            _u.at_scroll = _u.at_row;
        if (_u.at_row >= _u.at_scroll + 9)
            _u.at_scroll = _u.at_row - 8;
        snd_play(snd_menumove);
    }
    if (_left || _right)
    {
        var _d = _left ? -1 : 1;
        var _pv = knight_ui_practice_index(_c);
        var _nv = knight_ui_cycle(_pv, _d, 4);
        for (var _t = 0; _t < 4 && knight_ui_practice_block(_nv) != ""; _t++)
            _nv = knight_ui_cycle(_nv, _d, 4);
        if (_nv != _pv)
        {
            knight_ui_practice_set(_c, _nv);
            snd_play(snd_menumove);
        }
        else
            knight_ui_warn(knight_ui_practice_block(knight_ui_cycle(_pv, _d, 4)));
    }
    if (_ok)
    {
        _c.p_atk = _u.at_row;
        if (knight_ui_practice_index(_c) == 0)
        {
            if (knight_ui_practice_block(2) == "")
                knight_ui_practice_set(_c, 2);
        }
        snd_play(snd_select);
        knight_ui_tell(knight_ui_practice_value(_c));
    }
}

// ---------- TAG TEAM: pick the two knights ----------
function knight_ui_open_tag()
{
    var _u = global.knight_ui;
    var _c = global.knight_cfg;
    _u.sub = "tag";
    _u.tag_slot = 0;
    _u.tag_row = clamp(_c.knight, 0, knight_count() - 1);
    snd_play(snd_select);
}

function knight_ui_step_tag(_up, _down, _left, _right, _ok)
{
    var _u = global.knight_ui;
    var _c = global.knight_cfg;
    var _n = knight_count() + 1;
    if (_up || _down)
    {
        _u.tag_row = knight_ui_cycle(_u.tag_row, _up ? -1 : 1, _n);
        snd_play(snd_menumove);
    }
    if (_left || _right)
    {
        _u.tag_slot = 1 - _u.tag_slot;
        snd_play(snd_menumove);
    }
    if (_ok)
    {
        if (_u.tag_row >= knight_count())
        {
            knight_ui_fight_select({ kind: "tag", k: -1 });
            knight_ui_try_go();
            return 0;
        }
        if (_u.tag_slot == 0)
            _c.knight = _u.tag_row;
        else
            _c.knight2 = _u.tag_row;
        _c.combo = 1;
        _c.mode = 0;
        _c.random = 0;
        snd_play(snd_select);
        _u.tag_slot = 1 - _u.tag_slot;
    }
}

// ---------- ATTACK REMIX: which knights take part ----------
// the rows of the page: every knight that can be in a Remix (never the joke fight), then START
function knight_ui_remix_rows()
{
    var _l = [];
    for (var _k = 0; _k < knight_count(); _k++)
    {
        if (knight_remix_eligible(_k))
            array_push(_l, _k);
    }
    return _l;
}

function knight_ui_open_remix()
{
    var _u = global.knight_ui;
    var _c = global.knight_cfg;
    _c.rmask = knight_remix_mask(_c);
    _u.sub = "remix";
    _u.rmx_row = 0;
    snd_play(snd_select);
}

function knight_ui_step_remix(_up, _down, _left, _right, _ok)
{
    var _u = global.knight_ui;
    var _c = global.knight_cfg;
    var _rows = knight_ui_remix_rows();
    var _n = array_length(_rows) + 1;
    if (_up || _down)
    {
        _u.rmx_row = knight_ui_cycle(_u.rmx_row, _up ? -1 : 1, _n);
        snd_play(snd_menumove);
    }
    if ((_ok || _left || _right) && _u.rmx_row < array_length(_rows))
    {
        var _k = _rows[_u.rmx_row];
        var _m = knight_remix_mask(_c);
        // plain numbers only (a bitwise result is an int64, which the settings code reads as 0)
        var _bit = real(1 << _k);
        if (knight_remix_on(_c, _k))
        {
            if (array_length(knight_remix_pool(_c)) <= 1)
            {
                knight_ui_warn("At least one knight has to stay in the Remix.");
                return 0;
            }
            _c.rmask = _m - _bit;
        }
        else
            _c.rmask = _m + _bit;
        _c.combo = 2;
        _c.mode = 0;
        _c.random = 0;
        snd_play(snd_select);
        return 0;
    }
    if (_ok)
    {
        knight_ui_fight_select({ kind: "remix", k: -1 });
        knight_ui_try_go();
    }
}

// the file shown / previewed for the selected song
function knight_ui_song_file()
{
    var _c = global.knight_cfg;
    var _s = global.knight_songs[_c.song];
    if (_s.file != "")
        return _s.file;
    return knight_default_music(_c.knight);
}

function knight_ui_preview_toggle()
{
    var _u = global.knight_ui;
    if (knight_preview_playing())
    {
        knight_preview_stop();
        _u.pv_msg = "";
        return 0;
    }
    var _e = knight_preview_start(knight_ui_song_file());
    _u.pv_msg = _e;
    if (_e != "")
        snd_play(snd_cantselect);
}

// ---------- PARTY tab (EQUIP-menu layout) ----------
// lv 0: < > picks a slot, UP / DOWN changes who is in it, Z opens the slot's equipment
// lv 1: the three equipment rows (weapon, armor, armor); < > cycles quickly, Z opens the list
// lv 2: the list of items this member can wear
function knight_ui_pick_list(_ch, _k)
{
    var _l = [];
    var _cur = knight_equip_get(_ch, _k);
    for (var _i = 0; _i <= knight_equip_max(_k); _i++)
    {
        if (knight_equip_info(_k, _i, _ch).ok || _i == _cur)
            array_push(_l, _i);
    }
    return _l;
}

// put _ch in party slot _slot (0 = empty); empty slots close up so the party has no holes
function knight_ui_set_member(_slot, _ch)
{
    var _c = global.knight_cfg;
    var _u = global.knight_ui;
    var _n0 = knight_party_size(_c.party);
    var _p = [_c.party[0], _c.party[1], _c.party[2]];
    // a new member always goes into the first free slot
    if (_p[_slot] == 0 && _ch != 0)
        _slot = min(_slot, _n0);
    _p[_slot] = _ch;
    _c.party = knight_party_compact(_p);
    _u.pslot = clamp((_ch == 0) ? min(_slot, knight_party_size(_c.party)) : _slot, 0, 2);
}

function knight_ui_step_party(_up, _down, _left, _right, _ok, _back)
{
    var _u = global.knight_ui;
    var _c = global.knight_cfg;
    var _chv = _c.party[_u.pslot];
    var _ch = knight_ch_real(_chv);
    if (_u.lv == 0)
    {
        if (_left || _right)
        {
            _u.pslot = knight_ui_cycle(_u.pslot, _left ? -1 : 1, 3);
            snd_play(snd_menumove);
        }
        if (_up || _down)
        {
            // build 50: the custom characters (Flowery = 5, ...) after Noelle - members of their own (duplicates allowed)
            var _nv = knight_ui_cycle(_chv, _up ? -1 : 1, knight_cc_max_id() + 1);
            knight_ui_set_member(_u.pslot, _nv);
            snd_play(snd_menumove);
        }
        if (_ok)
        {
            if (_c.party[_u.pslot] <= 0)
            {
                knight_ui_warn("Nobody is in this slot. UP / DOWN puts someone here.");
                return 0;
            }
            _u.lv = 1;
            _u.prow = 0;
            snd_play(snd_select);
        }
        if (_back)
        {
            _u.focus = 0;
            snd_play(snd_menumove);
        }
        return 0;
    }
    if (_ch <= 0)
    {
        _u.lv = 0;
        return 0;
    }
    if (_u.lv == 1)
    {
        if (_up && _u.prow > 0)
        {
            _u.prow--;
            snd_play(snd_menumove);
        }
        if (_down && _u.prow < 2)
        {
            _u.prow++;
            snd_play(snd_menumove);
        }
        if (_left || _right)
        {
            knight_equip_step(_ch, _u.prow, _left ? -1 : 1);
            snd_play(snd_menumove);
        }
        if (_ok)
        {
            var _l = knight_ui_pick_list(_ch, _u.prow);
            var _cur = knight_equip_get(_ch, _u.prow);
            _u.ppick = 0;
            for (var _i = 0; _i < array_length(_l); _i++)
            {
                if (_l[_i] == _cur)
                    _u.ppick = _i;
            }
            _u.pscroll = clamp(_u.ppick - 2, 0, max(0, array_length(_l) - 6));
            _u.lv = 2;
            snd_play(snd_select);
        }
        if (_back)
        {
            _u.lv = 0;
            snd_play(snd_menumove);
        }
        return 0;
    }
    // lv 2: the item list
    var _l2 = knight_ui_pick_list(_ch, _u.prow);
    var _m = array_length(_l2);
    if (_up)
    {
        _u.ppick = knight_ui_cycle(_u.ppick, -1, _m);
        snd_play(snd_menumove);
    }
    if (_down)
    {
        _u.ppick = knight_ui_cycle(_u.ppick, 1, _m);
        snd_play(snd_menumove);
    }
    if (_u.ppick < _u.pscroll)
        _u.pscroll = _u.ppick;
    if (_u.ppick > _u.pscroll + 5)
        _u.pscroll = _u.ppick - 5;
    if (_ok)
    {
        var _pick = _l2[clamp(_u.ppick, 0, _m - 1)];
        knight_equip_set(_ch, _u.prow, _pick);
        knight_equip_refresh();
        _u.lv = 1;
        snd_play(snd_select);
        // one Shadow Mantle per setup: picking it takes it off whoever had it
        if (_u.prow > 0 && _pick == 23)
        {
            var _from = knight_mantle_take(_ch, _u.prow);
            if (_from != "")
                knight_ui_tell("Shadow Mantle taken from " + _from + ": only one member can wear it.");
        }
    }
    if (_back)
    {
        _u.lv = 1;
        snd_play(snd_menumove);
    }
}

// ---------- POWER tab ----------
function knight_ui_step_power(_up, _down, _left, _right, _ok, _back)
{
    var _u = global.knight_ui;
    var _c = global.knight_cfg;
    var _chv = _c.party[_u.sslot];
    var _ch = knight_ch_real(_chv);
    if (_u.lv == 0)
    {
        if (_left || _right)
        {
            _u.sslot = knight_ui_cycle(_u.sslot, _left ? -1 : 1, 3);
            snd_play(snd_menumove);
        }
        if (_ok)
        {
            if (_ch <= 0)
            {
                knight_ui_warn("This party slot is empty.");
                return 0;
            }
            _u.lv = 1;
            _u.srow = 0;
            _u.sscroll = 0;
            snd_play(snd_select);
        }
        if (_back)
        {
            _u.focus = 0;
            snd_play(snd_menumove);
        }
        return 0;
    }
    if (_ch <= 0)
    {
        _u.lv = 0;
        return 0;
    }
    if (_up && _u.srow > 0)
    {
        _u.srow--;
        snd_play(snd_menumove);
    }
    if (_down && _u.srow < 11)
    {
        _u.srow++;
        snd_play(snd_menumove);
    }
    if (_u.srow < _u.sscroll)
        _u.sscroll = _u.srow;
    if (_u.srow > _u.sscroll + 5)
        _u.sscroll = _u.srow - 5;
    if (knight_cc_ok(_chv))
    {
        // a custom character's list (Flowery, ...): only its own techniques or empty (its ACTION is always its first MAGIC entry)
        var _ccl = knight_cc_spl(_chv);
        if (_left || _right)
        {
            var _own = knight_cc_pickable(_chv);
            var _fi = 0;
            for (var _q = 0; _q < array_length(_own); _q++)
            {
                if (_own[_q] == _ccl[_u.srow])
                    _fi = _q + 1;
            }
            _fi = knight_ui_cycle(_fi, _left ? -1 : 1, array_length(_own) + 1);
            global.knight_cc_spells[_chv][_u.srow] = (_fi == 0) ? 0 : _own[_fi - 1];
            snd_play(snd_menumove);
        }
        if (_ok && _ccl[_u.srow] != 0)
        {
            global.knight_cc_spells[_chv][_u.srow] = 0;
            snd_play(snd_smallswing);
        }
    }
    else
    {
        if (_left || _right)
        {
            global.spell[_ch][_u.srow] = knight_ui_cycle(global.spell[_ch][_u.srow], _left ? -1 : 1, 16);
            snd_play(snd_menumove);
        }
        if (_ok && global.spell[_ch][_u.srow] != 0)
        {
            global.spell[_ch][_u.srow] = 0;
            snd_play(snd_smallswing);
        }
    }
    if (_back)
    {
        _u.lv = 0;
        snd_play(snd_menumove);
    }
}

// ---------- description shown on the top bar while a page is open ----------
function knight_ui_desc()
{
    var _u = global.knight_ui;
    var _c = global.knight_cfg;
    if (_u.sub == "presets")
        return "Z: save, load, rename or delete#the highlighted slot.   X: back";
    if (_u.sub == "loadouts")
        return knight_lo_desc(knight_ui_lo_cur());
    if (_u.sub == "records")
        return _u.rec_def ? "What each number counts.#Z: back to the table.   X: back" : "< >: other knight.   Z: what the numbers mean.#X: back";
    if (_u.sub == "credits")
        return "< >: other fight." + ((knight_credit_pages(_u.cr_i) > 1) ? "   Z: next page." : "") + "#X: back";
    if (_u.sub == "tag")
    {
        if (_u.tag_row >= knight_count())
            return "Z: start the Tag Team.   C works too.#X: back";
        return "Z: this knight goes " + ((_u.tag_slot == 0) ? "FIRST" : "SECOND") + ".   < >: other slot.#X: back";
    }
    if (_u.sub == "remix")
    {
        var _rr = knight_ui_remix_rows();
        if (_u.rmx_row >= array_length(_rr))
            return "Z: start the Attack Remix.   C works too.#X: back";
        return "Z: switch the " + knight_reg(_rr[_u.rmx_row]).name + " on or off.#C: start.   X: back";
    }
    if (_u.sub == "attacks")
        return "Z: practise this attack.   X: back#< >: OFF, PICKER, START AT or REPEAT.";
    if (kfo_ui_is_sub(_u.sub))
        return kfo_ui_desc();
    switch (_u.tab)
    {
        case 0:
            var _fl = knight_ui_fights();
            var _f = _fl[clamp(_u.krow, 0, array_length(_fl) - 1)];
            if (_f.kind == "rush")
                return "Fight every knight in a row.#Z: set it up and start.";
            if (_f.kind == "random")
                return "A random knight that fits your#party and rules. Z: start.";
            if (_f.kind == "tag")
                return "Two knights take turns. Each has its own#HP and Roaring: beat both. Z: pick them.";
            if (_f.kind == "remix")
                return "Every turn a random attack from the#knights you pick. Z: pick them.";
            if (_f.kind == "online")
                return "Battle royale for up to 8 players, or#practice against bots. Z: open.";
            if (_f.kind == "soon")
                return global.knight_planned[_f.p].name + ": coming soon.#Q / E: the other chapters.";
            return knight_reg(_f.k).desc;
        case 1:
            var _ch = knight_ch_real(_c.party[_u.pslot]);
            if (_u.lv == 0)
                return "< >: slot.   UP/DOWN: change member.#Z: equipment. Duplicates are allowed.";
            var _id = knight_equip_get(_ch, _u.prow);
            if (_u.lv == 2)
            {
                var _l = knight_ui_pick_list(_ch, _u.prow);
                _id = _l[clamp(_u.ppick, 0, array_length(_l) - 1)];
            }
            return knight_equip_desc(_u.prow, _id);
        case 2:
            var _ch2 = knight_ch_real(_c.party[_u.sslot]);
            if (_u.lv == 0)
                return "< >: choose a party member.#Z: edit their spells.";
            var _spl2 = knight_cc_ok(_c.party[_u.sslot]) ? knight_cc_spl(_c.party[_u.sslot]) : [];
            var _sp = knight_cc_ok(_c.party[_u.sslot]) ? _spl2[_u.srow] : ((_ch2 > 0) ? global.spell[_ch2][_u.srow] : 0);
            if (_sp == 0)
                return "Empty slot. < > puts a spell here.";
            scr_spellinfo(_sp);
            return knight_spell_desc(_sp, spelldesc);
        case 3:
            var _rl = knight_ui_rule_ids();
            var _id3 = _rl[_u.rrow];
            return knight_ui_rule_desc(_id3);
        case 4:
            var _cl = knight_ui_cfg_ids();
            var _id4 = _cl[_u.crow];
            return knight_ui_cfg_desc(_id4);
    }
    return "";
}

function knight_equip_desc(_k, _id)
{
    if (_id == 0)
        return "Nothing equipped here.";
    if (_k == 0)
    {
        scr_weaponinfo(_id);
        return weapondesctemp;
    }
    scr_armorinfo(_id);
    return armordesctemp;
}

// hub spells whose game description is blank or too long
function knight_spell_desc(_sp, _d)
{
    switch (_sp)
    {
        case 1: return "Two quick slashes at one foe.#Depends on Attack.";
        case 5: return "Kris shines their SOUL on Susie,#who casts Red Buster. Needs Susie.";
        case 6: return "Kris shines their SOUL on Ralsei:#heals everyone. Needs Ralsei.";
        case 12: return "Kris shines their SOUL on Noelle,#who casts a red Ice Shock. Needs Noelle.";
        case 13: return "Deals magical FIRE damage to#one enemy.";
        case 14: return "Kris shines their SOUL on Ralsei,#who throws a blue FireShock.";
        case 15: return "Ralsei and Noelle cast FireShock#and Ice Shock together.";
    }
    return _d;
}

// ---------- modal ----------
function knight_ui_modal(_kind, _title, _lines, _opts)
{
    global.knight_ui.modal = { k: _kind, title: _title, lines: _lines, opts: _opts, sel: 0, data: undefined, buf: "", t: 0 };
    return global.knight_ui.modal;
}

function knight_ui_modal_close()
{
    global.knight_ui.modal = undefined;
}

function knight_ui_msg(_title, _lines)
{
    knight_ui_modal("msg", _title, _lines, [{ t: "OK", a: "close" }]);
}

// ---------- start ----------
// short text of what will be played (used by the START box and the records)
function knight_ui_fight_title(_c)
{
    if (_c.mode == 1)
        return "KNIGHT RUSH";
    if (knight_lu_kind_of(_c) == "tag")
        return "TAG TEAM";
    if (knight_lu_kind_of(_c) == "remix")
        return "ATTACK REMIX";
    if (_c.random)
        return "RANDOM KNIGHT";
    return string_upper(knight_reg(_c.knight).name);
}

function knight_ui_try_go()
{
    var _u = global.knight_ui;
    knight_preview_stop();
    var _c = global.knight_cfg;
    var _res = knight_resolve(_c);
    if (!_res.ok)
    {
        var _lines = [];
        for (var _i = 0; _i < array_length(_res.errors); _i++)
            array_push(_lines, "! " + _res.errors[_i]);
        for (var _i = 0; _i < array_length(_res.fixes); _i++)
            array_push(_lines, _res.fixes[_i]);
        var _opts = [];
        if (!is_undefined(_res.fixcfg))
            array_push(_opts, { t: "Use fix", a: "applyfix" });
        array_push(_opts, { t: "Back", a: "close" });
        var _m = knight_ui_modal("errors", "CAN'T START", _lines, _opts);
        _m.data = _res.fixcfg;
        snd_play(snd_cantselect);
        return 0;
    }
    global.knight_launch = { src: _res.src, cfg: _res.cfg, plan: _res.plan, reveal: _res.reveal, corr: _res.corr };
    var _m2 = knight_ui_modal("launch", knight_ui_fight_title(_c), knight_ui_launch_lines(global.knight_launch), [{ t: "START", a: "start" }, { t: "BACK", a: "close" }]);
    _m2.data = global.knight_launch;
    snd_play(snd_select);
}

function knight_ui_launch_lines(_l)
{
    var _c = _l.cfg;
    var _o = [];
    if (_c.mode == 1)
    {
        var _t = "";
        for (var _i = 0; _i < array_length(_l.plan); _i++)
            _t += ((_t == "") ? "" : ", ") + knight_reg(_l.plan[_i]).short;
        array_push(_o, (_c.rush_shuffle ? "Shuffled: " : "Order: ") + _t);
    }
    var _kind = knight_lu_kind_of(_c);
    if (_kind == "tag")
        array_push(_o, knight_reg(_c.knight).name + " first, then " + knight_reg(_c.knight2).name + ". They take turns; beat both.");
    if (_kind == "remix")
    {
        array_push(_o, "Knights: " + knight_remix_names(_c, ", ") + ".");
        array_push(_o, "Every enemy turn one of them with a random attack. Below 30% HP the Normal Knight takes the finale.");
    }
    var _pm = knight_pmode(_c);
    // the attack is looked up in this knight's own list (build 45 fuzz: an index from another knight's longer list crashed here)
    var _pal = knight_reg(_c.knight).atk;
    var _pa = clamp(knight_cfg_num(_c, "p_atk"), 0, array_length(_pal) - 1);
    if (_pm == 1 && _pa > 0)
        array_push(_o, "Starts at " + _pal[_pa][2] + " (not recorded).");
    if (_pm == 2)
        array_push(_o, "Repeat: " + _pal[_pa][2] + " every turn (not recorded).");
    var _ch = knight_challenge_names(_c);
    if (variable_struct_exists(_l.src, "randchal") && _l.src.randchal)
        array_push(_ch, "+1 random rule");
    if (variable_struct_exists(_l.src, "rparty") && _l.src.rparty)
        array_push(_ch, "Random party");
    array_push(_o, (array_length(_ch) > 0) ? ("Rules: " + knight_join(_ch, ", ")) : "Rules: none");
    if (_c.c_time)
    {
        var _lt = knight_lu_turn_limit(_c);
        if (_lt <= 0)
            _lt = knight_turn_limit(_c.knight, _c.weird && knight_reg(_c.knight).weird);
        array_push(_o, (_c.mode == 1) ? "Time limit: each knight's attack list + 10 turns." : ("Time limit: " + string(_lt) + " enemy turns."));
    }
    if (_c.weird)
        array_push(_o, "Weird Route" + ((variable_struct_exists(_c, "c_wstats") && _c.c_wstats) ? " with Weird stats" : ""));
    if (_c.practice)
        array_push(_o, "Practice mode: no clears.");
    if (knight_cfg_flag(_c, "infhp"))
        array_push(_o, "Infinite HP: nothing is recorded.");
    for (var _i = 0; _i < array_length(_l.corr); _i++)
        array_push(_o, "! " + _l.corr[_i]);
    return _o;
}

// ---------- presets ----------
function knight_ui_preset_label(_i)
{
    var _p = global.knight_presets[_i];
    if (is_undefined(_p))
        return "- - -";
    if (variable_struct_exists(_p, "future") && _p.future)
        return _p.name + " (new)";
    return _p.name;
}

function knight_ui_preset_detail(_i)
{
    var _p = global.knight_presets[_i];
    if (is_undefined(_p))
        return ["Empty slot.", "Z: save the current", "setup here."];
    if (variable_struct_exists(_p, "future") && _p.future)
        return ["Saved by a newer", kdr_name() + ": it can be", "deleted, not loaded."];
    var _ki = knight_find_key(_p.knight);
    var _l = [];
    if (_p.mode == 1)
        array_push(_l, "KNIGHT RUSH");
    else if (variable_struct_exists(_p, "random") && _p.random)
        array_push(_l, "RANDOM KNIGHT");
    else
        array_push(_l, (_ki >= 0) ? string_upper(knight_reg(_ki).name) : ("? " + _p.knight));
    array_push(_l, "Party: " + knight_party_text(_p.party));
    var _cs = knight_challenge_names(knight_preset_cfgview(_p));
    if (array_length(_cs) > 0)
        array_push(_l, knight_join(_cs, ", "));
    else
        array_push(_l, "No rules");
    if (_p.weird)
        array_push(_l, "Weird Route");
    if (variable_struct_exists(_p, "infhp") && _p.infhp == 1)
        array_push(_l, "Infinite HP");
    return _l;
}

// a config-shaped view of a stored preset (missing new fields count as off)
function knight_preset_cfgview(_p)
{
    var _c = knight_cfg_default();
    var _f = knight_cfg_fields();
    for (var _i = 0; _i < array_length(_f); _i++)
    {
        if (variable_struct_exists(_p, _f[_i]))
            variable_struct_set(_c, _f[_i], variable_struct_get(_p, _f[_i]));
    }
    var _fx = knight_cfg_fields_x();
    for (var _i = 0; _i < array_length(_fx); _i++)
        variable_struct_set(_c, _fx[_i], variable_struct_exists(_p, _fx[_i]) ? variable_struct_get(_p, _fx[_i]) : 0);
    _c.party = _p.party;
    return _c;
}

function knight_ui_preset_menu(_slot)
{
    var _p = global.knight_presets[_slot];
    var _has = !is_undefined(_p);
    var _future = _has && variable_struct_exists(_p, "future") && _p.future;
    var _opts = [{ t: "Save here", a: "p_save" }];
    if (_has && !_future)
        array_push(_opts, { t: "Load", a: "p_load" });
    if (_has && !_future)
        array_push(_opts, { t: "Rename", a: "p_rename" });
    if (_has)
        array_push(_opts, { t: "Delete", a: "p_delete" });
    array_push(_opts, { t: "Back", a: "close" });
    var _m = knight_ui_modal("presetact", "PRESET " + string(_slot + 1), [_has ? knight_ui_preset_label(_slot) : "Empty slot"], _opts);
    _m.data = _slot;
}

function knight_ui_name_modal(_slot, _mode, _start)
{
    var _m = knight_ui_modal("name", (_mode == "rename") ? "RENAME PRESET" : "NAME THE PRESET", ["Type a name (12 letters max).", "ENTER: OK     ESC: cancel"], []);
    _m.data = { slot: _slot, mode: _mode };
    _m.buf = _start;
    keyboard_string = _start;
}

function knight_ui_modal_do(_a)
{
    var _u = global.knight_ui;
    var _m = _u.modal;
    if (kfo_ui_modal_do(_a))
        return 0;
    switch (_a)
    {
        case "close":
            knight_ui_modal_close();
            break;
        case "applyfix":
            var _f = _m.data;
            knight_ui_modal_close();
            if (!is_undefined(_f))
            {
                global.knight_cfg = knight_cfg_copy(_f);
                global.knight_cfg.random = 0;
                global.knight_cfg.randchal = 0;
                snd_play(snd_select);
            }
            break;
        case "start":
            knight_ui_modal_close();
            _u.go = 1;
            _u.gotimer = 0;
            break;
        case "p_save":
            var _slot = _m.data;
            knight_ui_modal_close();
            var _old = global.knight_presets[_slot];
            knight_ui_name_modal(_slot, "save", is_undefined(_old) ? knight_preset_default_name(_slot) : _old.name);
            break;
        case "p_rename":
            var _slot2 = _m.data;
            knight_ui_modal_close();
            knight_ui_name_modal(_slot2, "rename", global.knight_presets[_slot2].name);
            break;
        case "p_delete":
            var _slot3 = _m.data;
            knight_ui_modal_close();
            var _dm = knight_ui_modal("confirm", "DELETE PRESET?", [string(_slot3 + 1) + ". " + global.knight_presets[_slot3].name, "This can't be undone."], [{ t: "No", a: "close" }, { t: "Delete", a: "p_delete_yes" }]);
            _dm.data = _slot3;
            break;
        case "p_delete_yes":
            var _slot4 = _m.data;
            knight_ui_modal_close();
            if (knight_preset_delete(_slot4))
                snd_play(snd_smallswing);
            else
                knight_ui_msg("COULD NOT SAVE", ["The preset file could not be written."]);
            break;
        case "p_load":
            var _slot5 = _m.data;
            knight_ui_modal_close();
            var _dec = knight_preset_decode(global.knight_presets[_slot5]);
            if (!_dec.ok)
            {
                knight_ui_msg("CAN'T LOAD", [_dec.text]);
                break;
            }
            if (array_length(_dec.corr) == 0)
            {
                knight_preset_apply(_dec);
                knight_ui_msg("LOADED", [knight_ui_preset_label(_slot5)]);
                break;
            }
            var _lines = ["This preset needs changes:"];
            for (var _i = 0; _i < array_length(_dec.corr); _i++)
                array_push(_lines, "! " + _dec.corr[_i]);
            var _lm = knight_ui_modal("confirm", "LOAD WITH CHANGES?", _lines, [{ t: "Load", a: "p_load_yes" }, { t: "Cancel", a: "close" }]);
            _lm.data = _dec;
            break;
        case "p_load_yes":
            var _d2 = _m.data;
            knight_ui_modal_close();
            knight_preset_apply(_d2);
            snd_play(snd_select);
            break;
        case "lo_load":
            var _ld = _m.data;
            knight_ui_modal_close();
            knight_lo_apply(_ld.g, _ld.lo);
            snd_play(snd_select);
            knight_ui_tell("Loaded " + knight_lo_group_label(_ld.g) + " " + knight_lo_label(_ld.lo) + ": party, gear and spells are set.");
            break;
        case "name_ok":
            var _nd = _m.data;
            var _nm = knight_name_clean(_m.buf);
            knight_ui_modal_close();
            var _good = false;
            if (_nd.mode == "save")
                _good = knight_preset_save(_nd.slot, _nm);
            else if (_nm == "")
            {
                knight_ui_msg("NAME NEEDED", ["A preset name can't be empty."]);
                break;
            }
            else
                _good = knight_preset_rename(_nd.slot, _nm);
            if (!_good)
                knight_ui_msg("COULD NOT SAVE", ["The preset file could not be written."]);
            else
                snd_play(snd_select);
            break;
    }
}

// ---------- step ----------
function knight_ui_step()
{
    // build 48: the room's chat is open: the menu waits (its keys are letters being typed)
    if (kfo_chat_typing())
        return 0;
    var _u = global.knight_ui;
    knight_preview_tick();
    _u.siner++;
    if (_u.warntimer > 0)
        _u.warntimer--;
    if (is_struct(_u.modal))
        _u.modal.t++;
    // bars slide in / out like DELTARUNE's own menu
    if (_u.closing)
    {
        _u.tp = (_u.tp >= 40) ? (_u.tp - round(_u.tp / 2.5)) : max(0, _u.tp - 30);
        _u.bp = (_u.bp >= 30) ? (_u.bp - round(_u.bp / 2.5)) : max(0, _u.bp - 30);
        if (_u.tp <= 0 && _u.bp <= 0)
            knight_menu_finish_close();
        return 0;
    }
    _u.tp = (80 - _u.tp <= 40) ? min(80, _u.tp + max(1, round((80 - _u.tp) / 2.5))) : (_u.tp + 30);
    _u.bp = (60 - _u.bp <= 40) ? min(60, _u.bp + max(1, round((60 - _u.bp) / 2.5))) : (_u.bp + 30);
    // build 49: a Steam invite that came in: its box (JOIN / NOT NOW) once the menu is open
    if (!is_struct(_u.modal) && _u.tp >= 80)
        kfo_inv_modal_check();
    if (_u.inputdelay > 0)
    {
        _u.inputdelay--;
        return 0;
    }
    global.interact = 1;
    if (_u.go == 1)
    {
        _u.gotimer++;
        if (_u.gotimer >= 18)
        {
            knight_launch_go();
            with (obj_knight_menu)
                instance_destroy();
        }
        return 0;
    }
    // DRBR: the mouse wheel moves through a list like UP / DOWN (every page and box of the menu; the game has no mouse
    // pointer in its menus, so clicks stay the keyboard's / controller's)
    var _up = (up_p() == 1) || mouse_wheel_up();
    var _down = (down_p() == 1) || mouse_wheel_down();
    var _left = (left_p() == 1);
    var _right = (right_p() == 1);
    var _ok = (button1_p() == 1);
    var _back = (button2_p() == 1) || keyboard_check_pressed(vk_backspace);
    var _alt = (button3_p() == 1);
    if (is_struct(_u.modal))
    {
        knight_ui_step_modal(_up, _down, _left, _right, _ok, _back);
        return 0;
    }
    if (_u.notice != "")
    {
        if (_ok || _back)
            _u.notice = "";
        return 0;
    }
    if (kfo_ui_is_sub(_u.sub))
    {
        kfo_ui_step(_up, _down, _left, _right, _ok, _back, _alt);
        return 0;
    }
    if (_u.sub != "")
    {
        if (_alt && (_u.sub == "tag" || _u.sub == "remix" || _u.sub == "attacks"))
        {
            knight_ui_try_go();
            return 0;
        }
        knight_ui_step_sub(_up, _down, _left, _right, _ok, _back);
        return 0;
    }
    if (_alt)
    {
        knight_ui_try_go();
        return 0;
    }
    if (_u.focus == 0)
    {
        if (_left || _right)
        {
            _u.tab = knight_ui_cycle(_u.tab, _left ? -1 : 1, knight_ui_tabs());
            _u.lv = 0;
            snd_play(snd_menumove);
        }
        if (_ok || _down)
        {
            _u.focus = 1;
            _u.lv = 0;
            snd_play(snd_select);
        }
        if (_back)
            knight_menu_close();
        return 0;
    }
    switch (_u.tab)
    {
        case 0:
            var _f = knight_ui_fights();
            var _n = array_length(_f);
            // build 52: the KNIGHT carousel (LEFT / RIGHT: the knights) over the MODE strip (LEFT / RIGHT: the modes and
            // ONLINE); UP / DOWN between the two (each remembers where it was)
            _u.krow = clamp(_u.krow, 0, _n - 1);
            var _nk = knight_ui_nknights(_f);
            var _onk = (_f[_u.krow].kind == "k" || _f[_u.krow].kind == "soon");
            if (!variable_struct_exists(_u, "kk"))
            {
                _u.kk = 0;
                _u.km = 0;
            }
            if (_onk)
                _u.kk = _u.krow;
            else
                _u.km = _u.krow - _nk;
            if ((_up || _down) && _nk > 0)
            {
                _u.krow = _onk ? (_nk + clamp(_u.km, 0, (_n - _nk) - 1)) : clamp(_u.kk, 0, _nk - 1);
                snd_play(snd_menumove);
                break;
            }
            if (_left || _right)
            {
                if (_onk)
                    _u.krow = knight_ui_cycle(_u.krow, _left ? -1 : 1, _nk);
                else
                    _u.krow = _nk + knight_ui_cycle(_u.krow - _nk, _left ? -1 : 1, _n - _nk);
                snd_play(snd_menumove);
                break;
            }
            // more than one chapter page (KNIGHT_SHOW_PLANNED): Q / E turn the page
            if (knight_page_count() > 1 && (keyboard_check_pressed(ord("Q")) || keyboard_check_pressed(ord("E"))))
            {
                _u.kpage = knight_ui_cycle(_u.kpage, keyboard_check_pressed(ord("Q")) ? -1 : 1, knight_page_count());
                _u.krow = 0;
                snd_play(snd_menumove);
                break;
            }
            if (_ok)
            {
                if (_f[_u.krow].kind == "soon")
                {
                    knight_ui_warn(global.knight_planned[_f[_u.krow].p].name + " is not in the hub yet - coming soon.");
                }
                else if (_f[_u.krow].kind == "tag")
                {
                    knight_ui_fight_select(_f[_u.krow]);
                    knight_ui_open_tag();
                }
                else if (_f[_u.krow].kind == "remix")
                {
                    knight_ui_fight_select(_f[_u.krow]);
                    knight_ui_open_remix();
                }
                else if (_f[_u.krow].kind == "online")
                    kfo_ui_open();
                else
                {
                    knight_ui_fight_select(_f[_u.krow]);
                    knight_ui_try_go();
                }
            }
            if (_back)
            {
                _u.focus = 0;
                snd_play(snd_menumove);
            }
            break;
        case 1:
            knight_ui_step_party(_up, _down, _left, _right, _ok, _back);
            break;
        case 2:
            knight_ui_step_power(_up, _down, _left, _right, _ok, _back);
            break;
        case 3:
            var _ids = knight_ui_rule_ids();
            var _col = _u.rrow div 8;
            var _ln = _u.rrow mod 8;
            if (_up)
            {
                _ln = knight_ui_cycle(_ln, -1, 8);
                snd_play(snd_menumove);
            }
            if (_down)
            {
                _ln = knight_ui_cycle(_ln, 1, 8);
                snd_play(snd_menumove);
            }
            if (_left || _right)
            {
                _col = 1 - _col;
                snd_play(snd_menumove);
            }
            _u.rrow = (_col * 8) + _ln;
            if (_ok)
                knight_ui_rule_toggle(_ids[_u.rrow]);
            if (_back)
            {
                _u.focus = 0;
                snd_play(snd_menumove);
            }
            break;
        case 4:
            var _cids = knight_ui_cfg_ids();
            var _cn = array_length(_cids);
            if (_up)
            {
                _u.crow = knight_ui_cycle(_u.crow, -1, _cn);
                snd_play(snd_menumove);
            }
            if (_down)
            {
                _u.crow = knight_ui_cycle(_u.crow, 1, _cn);
                snd_play(snd_menumove);
            }
            if (_left)
                knight_ui_cfg_act(_cids[_u.crow], -1);
            if (_right)
                knight_ui_cfg_act(_cids[_u.crow], 1);
            if (_ok)
                knight_ui_cfg_act(_cids[_u.crow], 0);
            if (_back)
            {
                _u.focus = 0;
                snd_play(snd_menumove);
            }
            break;
    }
}

function knight_ui_step_sub(_up, _down, _left, _right, _ok, _back)
{
    var _u = global.knight_ui;
    if (_back)
    {
        _u.sub = "";
        snd_play(snd_menumove);
        return 0;
    }
    if (_u.sub == "loadouts")
    {
        knight_ui_step_loadouts(_up, _down, _left, _right, _ok);
        return 0;
    }
    if (_u.sub == "tag")
    {
        knight_ui_step_tag(_up, _down, _left, _right, _ok);
        return 0;
    }
    if (_u.sub == "remix")
    {
        knight_ui_step_remix(_up, _down, _left, _right, _ok);
        return 0;
    }
    if (_u.sub == "attacks")
    {
        knight_ui_step_attacks(_up, _down, _left, _right, _ok);
        return 0;
    }
    if (_u.sub == "presets")
    {
        var _n = knight_preset_slots();
        if (_up)
        {
            _u.subrow = knight_ui_cycle(_u.subrow, -1, _n);
            snd_play(snd_menumove);
        }
        if (_down)
        {
            _u.subrow = knight_ui_cycle(_u.subrow, 1, _n);
            snd_play(snd_menumove);
        }
        if (_ok)
        {
            snd_play(snd_select);
            knight_ui_preset_menu(_u.subrow);
        }
        return 0;
    }
    if (_u.sub == "records")
    {
        var _rn = array_length(knight_rec_keys());
        if (_left || _right)
        {
            _u.rec_i = knight_ui_cycle(_u.rec_i, _left ? -1 : 1, _rn);
            snd_play(snd_menumove);
        }
        if (_ok)
        {
            _u.rec_def = !_u.rec_def;
            snd_play(snd_menumove);
        }
        return 0;
    }
    if (_u.sub == "credits")
    {
        var _cn = knight_credit_count();
        if (_left || _right)
        {
            _u.cr_i = knight_ui_cycle(_u.cr_i, _left ? -1 : 1, _cn);
            _u.cr_page = 0;
            snd_play(snd_menumove);
        }
        if (_ok)
        {
            var _pg = knight_credit_pages(_u.cr_i);
            if (_pg > 1)
            {
                _u.cr_page = (_u.cr_page + 1) mod _pg;
                snd_play(snd_menumove);
            }
        }
    }
}

function knight_ui_step_modal(_up, _down, _left, _right, _ok, _back)
{
    var _u = global.knight_ui;
    var _m = _u.modal;
    if (_m.k == "kfo_text")
    {
        kfo_ui_text_step(_m);
        return 0;
    }
    if (_m.k == "kfo_key")
    {
        kfo_ui_key_step(_m);
        return 0;
    }
    if (_m.k == "songs")
    {
        knight_songpick_step(_m, _up, _down, _left, _right, _ok, _back);
        return 0;
    }
    if (_m.k == "name")
    {
        _m.buf = string_copy(knight_name_clean_live(keyboard_string), 1, 12);
        if (string_length(keyboard_string) > 12)
            keyboard_string = _m.buf;
        // ENTER / ESC on a keyboard; a controller's confirm / cancel buttons keep the suggested name or back out
        if (keyboard_check_pressed(vk_enter) || knight_pad_pressed(gp_face1))
            knight_ui_modal_do("name_ok");
        else if (keyboard_check_pressed(vk_escape) || knight_pad_pressed(gp_face2))
            knight_ui_modal_close();
        return 0;
    }
    var _n = array_length(_m.opts);
    if (_m.t < 3)
        return 0;
    if (_n == 0)
    {
        if (_ok || _back)
            knight_ui_modal_close();
        return 0;
    }
    if (_up || _left)
    {
        _m.sel = (_m.sel + _n - 1) mod _n;
        snd_play(snd_menumove);
    }
    if (_down || _right)
    {
        _m.sel = (_m.sel + 1) mod _n;
        snd_play(snd_menumove);
    }
    if (_back)
    {
        knight_ui_modal_close();
        snd_play(snd_menumove);
        return 0;
    }
    if (_ok)
    {
        snd_play(snd_select);
        knight_ui_modal_do(_m.opts[_m.sel].a);
    }
}

function knight_pad_pressed(_b)
{
    if (!instance_exists(obj_gamecontroller))
        return false;
    var _g = instance_find(obj_gamecontroller, 0);
    if (!variable_instance_exists(_g, "gamepad_id") || _g.gamepad_id < 0)
        return false;
    return gamepad_button_check_pressed(_g.gamepad_id, _b);
}

// a controller button is down (the online match keys: LB / RB / BACK)
function knight_pad_held(_b)
{
    if (!instance_exists(obj_gamecontroller))
        return false;
    var _g = instance_find(obj_gamecontroller, 0);
    if (!variable_instance_exists(_g, "gamepad_id") || _g.gamepad_id < 0)
        return false;
    return gamepad_button_check(_g.gamepad_id, _b);
}

// typed text while editing: printable ASCII only (the final clean-up also trims spaces)
function knight_name_clean_live(_s)
{
    var _o = "";
    for (var _i = 1; _i <= string_length(_s); _i++)
    {
        var _ch = string_char_at(_s, _i);
        var _code = ord(_ch);
        if (_code >= 32 && _code < 127 && _ch != "=" && _ch != "[" && _ch != "]" && _ch != ";" && _ch != "\"" && _ch != "\\")
            _o += _ch;
    }
    return _o;
}

// ---------- records page ----------
function knight_rec_defs()
{
    return [
        ["WINS", "clears / attempts"],
        ["BEST", "fastest win (battle only)"],
        ["LOW DMG", "least HP lost in a win"],
        ["STREAK", "no-hit wins in a row"],
        ["LEFT", "fights you left early"],
        ["", "Normal, Rules, No-Hit and Practice runs are kept apart. Joke fights and random parties are not recorded."]
    ];
}

// ---------- credits ----------
// one page per fight plus the hub page; long credit lists continue on a second page
function knight_credit_count()
{
    return knight_count() + 2;
}

function knight_credit_entry(_i)
{
    if (_i < knight_count())
    {
        var _r = knight_reg(_i);
        return { title: _r.title, credits: _r.credits, song: _r.songcredit };
    }
    if (_i == knight_count() + 1)
        return { title: "MUSIC", credits: knight_credit_music(), song: "" };
    return { title: kdr_on() ? "DRBR" : "KNIGHT HUB", credits: global.knight_hub_credits, song: "" };
}

// build 50: every song of the FIGHT SONG list, one by one: its title, its artist, its credits, where it is from
function knight_credit_music()
{
    var _g = [];
    for (var _i = 0; _i < array_length(global.knight_songs); _i++)
    {
        var _s = global.knight_songs[_i];
        if (!knight_song_real(_i))
            continue;
        var _n = [[_s.by, ""]];
        for (var _j = 0; _j < array_length(_s.cl); _j++)
            array_push(_n, [_s.cl[_j], ""]);
        if (_s.src != "")
            array_push(_n, [_s.src, ""]);
        array_push(_g, { g: _s.name, n: _n });
    }
    return _g;
}

// lines of one credit entry: ["h", text] header (gray), ["n", name, role] name lines
function knight_credit_lines(_i)
{
    var _e = knight_credit_entry(_i);
    var _l = [];
    for (var _g = 0; _g < array_length(_e.credits); _g++)
    {
        var _grp = _e.credits[_g];
        array_push(_l, ["h", _grp.g, ""]);
        for (var _n = 0; _n < array_length(_grp.n); _n++)
            array_push(_l, ["n", _grp.n[_n][0], _grp.n[_n][1]]);
    }
    if (_e.song != "")
    {
        array_push(_l, ["h", "Music", ""]);
        array_push(_l, ["n", _e.song, ""]);
    }
    return _l;
}

function knight_credit_per_page()
{
    return 13;
}

function knight_credit_pages(_i)
{
    return max(1, ceil(array_length(knight_credit_lines(_i)) / knight_credit_per_page()));
}

// ---------- build 48: the song list (FIGHT SONG offline, MUSIC online) ----------
// A scrollable list of every song with its title and artist: up / down (left / right: a page), Z picks, C listens (C again:
// stop), X goes back. A song whose file is not in the game's mus folder is shown greyed with "NOT FOUND" (it can still be
// picked: the fight then plays its own music, as before).
function knight_songpick_list(_from)
{
    var _l = [];
    if (_from == "onl")
        array_push(_l, [-1, "AS IN THE HUB", "the hub's FIGHT SONG", ""]);
    for (var _i = 0; _i < array_length(global.knight_songs); _i++)
    {
        var _s = global.knight_songs[_i];
        var _t = string_upper(_s.name);
        if (_i == 0)
            _t = (_from == "onl") ? "THE KNIGHTS' OWN" : "MOD DEFAULT";
        var _by = _s.by;
        if (_i == 0)
            _by = "each knight's own song";
        else if (_s.file == "@random")
            _by = (knight_song_on_count() > 0) ? "a new one every fight" : "NO SONGS SELECTED";
        array_push(_l, [_i, _t, _by, _s.file]);
        // build 50: right under RANDOM, every song back in RANDOM / every song out of it
        if (_s.file == "@random")
        {
            array_push(_l, [-10, "ALL SONGS IN RANDOM", "enable all", ""]);
            array_push(_l, [-11, "NO SONGS IN RANDOM", "disable all", ""]);
        }
    }
    return _l;
}

function knight_songpick_cur(_from)
{
    if (_from == "onl")
        return kfo_get().song;
    return global.knight_cfg.song;
}

function knight_songpick_open(_from)
{
    var _l = knight_songpick_list(_from);
    var _cur = knight_songpick_cur(_from);
    var _sel = 0;
    for (var _i = 0; _i < array_length(_l); _i++)
    {
        if (_l[_i][0] == _cur)
            _sel = _i;
    }
    var _m = knight_ui_modal("songs", (_from == "onl") ? "ONLINE MUSIC" : "FIGHT SONG", [], []);
    _m.data = { from: _from, sel: _sel, scroll: max(0, _sel - 5), msg: "" };
    snd_play(snd_select);
    return _m;
}

#macro KNIGHT_SONGPICK_ROWS 10

function knight_songpick_step(_m, _up, _down, _left, _right, _ok, _back)
{
    var _d = _m.data;
    var _l = knight_songpick_list(_d.from);
    var _n = array_length(_l);
    if (_m.t < 3)
        return 0;
    if (_back)
    {
        knight_ui_modal_close();
        snd_play(snd_menumove);
        return 0;
    }
    var _old = _d.sel;
    if (_up)
        _d.sel = (_d.sel + _n - 1) mod _n;
    if (_down)
        _d.sel = (_d.sel + 1) mod _n;
    if (_left)
        _d.sel = max(0, _d.sel - KNIGHT_SONGPICK_ROWS);
    if (_right)
        _d.sel = min(_n - 1, _d.sel + KNIGHT_SONGPICK_ROWS);
    if (_d.sel != _old)
    {
        snd_play(snd_menumove);
        _d.msg = "";
    }
    _d.scroll = clamp(_d.scroll, max(0, _d.sel - (KNIGHT_SONGPICK_ROWS - 1)), min(_d.sel, max(0, _n - KNIGHT_SONGPICK_ROWS)));
    var _e = _l[_d.sel];
    // build 50: A - the highlighted song in / out of RANDOM (yours only; kept for next time)
    if (keyboard_check_pressed(ord("A")) && _e[0] >= 0 && knight_song_real(_e[0]))
    {
        knight_song_set_on(_e[0], !knight_song_on(_e[0]));
        _d.msg = knight_song_on(_e[0]) ? "IN RANDOM: " + string_upper(global.knight_songs[_e[0]].name) : "NOT IN RANDOM: " + string_upper(global.knight_songs[_e[0]].name);
        snd_play(snd_select);
    }
    // C: listen to the highlighted song (C again: stop)
    if (button3_p())
    {
        if (knight_preview_playing())
            knight_preview_stop();
        else if (_e[3] != "")
        {
            var _why = knight_preview_start(_e[3]);
            _d.msg = _why;
        }
    }
    if (_ok && (_e[0] == -10 || _e[0] == -11))
    {
        knight_song_set_all(_e[0] == -10);
        _d.msg = (_e[0] == -10) ? "EVERY SONG IS IN RANDOM." : "NO SONGS SELECTED: RANDOM PLAYS NOTHING.";
        snd_play(snd_select);
        return 0;
    }
    if (_ok)
    {
        if (_d.from == "onl")
        {
            var _o = kfo_get();
            _o.song = _e[0];
            kfo_ini_save();
        }
        else
            global.knight_cfg.song = _e[0];
        knight_preview_stop();
        snd_play(snd_select);
        knight_ui_modal_close();
    }
    return 0;
}

function knight_songpick_draw(xx, yy, _m)
{
    var _d = _m.data;
    var _l = knight_songpick_list(_d.from);
    var _n = array_length(_l);
    var _cur = knight_songpick_cur(_d.from);
    draw_set_alpha(0.6);
    draw_set_color(c_black);
    draw_rectangle(xx - 10, yy - 10, xx + 650, yy + 490, false);
    draw_set_alpha(1);
    var _x0 = xx + 40;
    var _x1 = xx + 600;
    var _y0 = yy + 34;
    var _y1 = yy + 446;
    scr_darkbox_black(_x0, _y0, _x1, _y1);
    draw_set_halign(fa_center);
    draw_set_color(c_white);
    knight_txt(xx + 320, _y0 + 20, _m.title);
    draw_set_color(c_gray);
    knight_txt_small(xx + 320, _y0 + 50, string(_d.sel + 1) + " / " + string(_n));
    draw_set_halign(fa_left);
    knight_txt_small(_x0 + 54, _y0 + 50, "SONG");
    draw_set_halign(fa_right);
    knight_txt_small(_x1 - 26, _y0 + 50, "ARTIST");
    draw_set_halign(fa_left);
    var _ry = _y0 + 72;
    for (var _i = _d.scroll; _i < _n && _i < _d.scroll + KNIGHT_SONGPICK_ROWS; _i++)
    {
        var _e = _l[_i];
        var _y = _ry + ((_i - _d.scroll) * 30);
        var _hot = (_i == _d.sel);
        var _miss = (_e[3] != "" && !knight_music_exists(_e[3]));
        draw_set_color(_miss ? c_gray : (_hot ? c_yellow : c_white));
        // (the menu's big text, as you asked; the artist in the small text on the right)
        knight_txt(_x0 + 54, _y, knight_fit(_e[1], 330));
        draw_set_halign(fa_right);
        draw_set_color(_miss ? c_dkgray : (_hot ? c_yellow : c_ltgray));
        knight_txt_small(_x1 - 26, _y + 6, knight_fit_small(_miss ? "NOT FOUND" : _e[2], 150));
        draw_set_halign(fa_left);
        if (_e[0] == _cur)
        {
            draw_set_color(c_lime);
            knight_txt_small(_x0 + 22, _y + 6, "*");
        }
        if (_hot)
            knight_heart(_x0 + 30, _y + 6);
        // build 50: in RANDOM (+) or turned off (-)
        if (_e[0] >= 0 && knight_song_real(_e[0]))
        {
            var _in = knight_song_on(_e[0]);
            draw_set_color(_in ? c_lime : c_red);
            knight_txt_small(_x0 + 8, _y + 6, _in ? "+" : "-");
        }
    }
    // more above / below
    draw_set_color(c_gray);
    draw_set_halign(fa_center);
    if (_d.scroll > 0)
        knight_txt_small(xx + 320, _ry - 18, "^");
    if (_d.scroll + KNIGHT_SONGPICK_ROWS < _n)
        knight_txt_small(xx + 320, _ry + (KNIGHT_SONGPICK_ROWS * 30) - 4, "v");
    var _foot = "Z: PICK   C: " + (knight_preview_playing() ? "STOP" : "LISTEN") + "   A: IN RANDOM +/-   X: BACK   < >: PAGE";
    if (_d.msg != "")
        _foot = _d.msg;
    draw_set_color(c_white);
    knight_txt_small(xx + 320, _y1 - 26, knight_fit_small(_foot, 520));
    draw_set_halign(fa_left);
    return 1;
}
