// =====================================================================================================================
// DRBR SAVE PROFILE (build 51 update 10)
// Only in the separate DRBR install made by DRBR-Setup / DRBR Launcher: its chapter3_windows has
// drbr_data/drbr_profile.cfg (the launcher writes it). The in-place Knight Hub (Steam's own chapter3_windows, patched by
// INSTALL_KNIGHT_HUB.bat) has no such file - there nothing in this file changes anything.
// In DRBR mode:
//  * the game starts straight in the provided starting save (drbr_data/start_filech3: read-only, next to data.win,
//    checked by its SHA-1): no intro, no file menu - Chapter 3's room_dw_snow_zone (room id 30108) at story point 320,
//    the room right before the Roaring Knight, exactly as loading that save from the file menu would.
//  * every story file the game writes or reads (filechN_M, dr.ini, keyconfig_N.ini, config_N.ini) is in drbr_profile/
//    inside the save folder: the player's own DELTARUNE saves next to it are never read, written or deleted.
//  * the mod's own settings (knight_hub.ini, knightfights_online.ini, ...) stay where they always were: they persist.
//  * a chapter switch (the end of Chapter 3, the menu's chapter select) restarts at the DRBR start instead of going to a
//    chapter the DRBR install does not have.
//  * drbr_profile/last_start.ini says how the last start went (the launcher reads it).
// start_mode (drbr_profile.cfg): "template" (default) = every launch starts from the provided save; "continue" = the
// DRBR save in drbr_profile/ if it is a valid Chapter 3 save, else the provided save.
// =====================================================================================================================

#macro KDR_CFG "drbr_data/drbr_profile.cfg"
#macro KDR_TEMPLATE "drbr_data/start_filech3"
#macro KDR_DIR "drbr_profile"
#macro KDR_LIVE "drbr_profile/filech3_0"
#macro KDR_LOG "drbr_profile/last_start.ini"
#macro KDR_PENDING "drbr_profile/pending_join.ini"

// the starting saves this build accepts: [save_template_version, sha1 of the file, its size, room id, story point]
function kdr_template_list()
{
    return [[1, "e1b7086a53f5ac9ec46ecd23c1c465ae4f6a321b", 12385, 30108, 320]];
}

function kdr_on()
{
    if (!variable_global_exists("kdr_mode"))
        kdr_detect();
    return global.kdr_mode;
}

function kdr_detect()
{
    global.kdr_mode = 0;
    global.kdr_cfg = {};
    global.kdr_booted = 0;
    global.kdr_expect = 0;
    global.kdr_wait = 0;
    global.kdr_from = "";
    global.kdr_hint_t = 0;
    if (!file_exists(KDR_CFG))
        return 0;
    global.kdr_mode = 1;
    // read as plain text (never ini_open: ini_close would write a copy into the save folder that would then shadow it)
    var _f = file_text_open_read(KDR_CFG);
    if (_f == -1)
        return 1;
    var _n = 0;
    while (!file_text_eof(_f) && _n < 200)
    {
        var _l = kdr_strip(file_text_read_string(_f));
        file_text_readln(_f);
        _n++;
        if (_l == "" || string_char_at(_l, 1) == "#")
            continue;
        var _p = string_pos("=", _l);
        if (_p <= 1)
            continue;
        variable_struct_set(global.kdr_cfg, kdr_strip(string_copy(_l, 1, _p - 1)), kdr_strip(string_copy(_l, _p + 1, string_length(_l) - _p)));
    }
    file_text_close(_f);
    return 1;
}

// spaces, tabs and a CR off both ends
function kdr_strip(_s)
{
    var _a = 1;
    var _b = string_length(_s);
    while (_a <= _b)
    {
        var _c = string_char_at(_s, _a);
        if (_c != " " && _c != "\t" && _c != "\r" && _c != "\n")
            break;
        _a++;
    }
    while (_b >= _a)
    {
        var _c = string_char_at(_s, _b);
        if (_c != " " && _c != "\t" && _c != "\r" && _c != "\n")
            break;
        _b--;
    }
    return (_b >= _a) ? string_copy(_s, _a, (_b - _a) + 1) : "";
}

function kdr_cfg_get(_k, _d)
{
    if (!kdr_on() || !variable_struct_exists(global.kdr_cfg, _k))
        return _d;
    return variable_struct_get(global.kdr_cfg, _k);
}

// "digits" + _tail, e.g. "3.ini" after "keyconfig_"
function kdr_num_then(_s, _tail)
{
    var _l = string_length(_s);
    var _t = string_length(_tail);
    if (_l <= _t || string_copy(_s, (_l - _t) + 1, _t) != _tail)
        return false;
    var _d = string_copy(_s, 1, _l - _t);
    return string_digits(_d) == _d;
}

// the story files Chapter 3 keeps in the save folder (everything else - the mod's ini files, true_config.ini - is not)
function kdr_is_story_file(_n)
{
    if (!is_string(_n))
        return false;
    var _s = string_lower(_n);
    if (_s == "dr.ini")
        return true;
    if (string_copy(_s, 1, 6) == "filech")
        return string_pos("/", _s) == 0 && string_pos("\\", _s) == 0;
    if (string_copy(_s, 1, 10) == "keyconfig_")
        return kdr_num_then(string_copy(_s, 11, string_length(_s) - 10), ".ini");
    if (string_copy(_s, 1, 7) == "config_")
        return kdr_num_then(string_copy(_s, 8, string_length(_s) - 7), ".ini");
    return false;
}

// every story file name goes through here (the ossafe_* file functions and the config menu's own ini_open)
function kdr_path(_n)
{
    if (!kdr_on() || !kdr_is_story_file(_n))
        return _n;
    return KDR_DIR + "/" + _n;
}

// "" = drbr_data/start_filech3 is a starting save this build knows (its SHA-1 and size), else why it is not
function kdr_check_template()
{
    if (!file_exists(KDR_TEMPLATE))
        return "The DRBR starting save (drbr_data\\start_filech3) is missing.";
    var _b = buffer_load(KDR_TEMPLATE);
    if (!buffer_exists(_b))
        return "The DRBR starting save (drbr_data\\start_filech3) could not be read.";
    var _sz = buffer_get_size(_b);
    var _h = string_lower(buffer_sha1(_b, 0, _sz));
    buffer_delete(_b);
    var _L = kdr_template_list();
    for (var _i = 0; _i < array_length(_L); _i++)
    {
        if (_h == _L[_i][1] && _sz == _L[_i][2])
        {
            global.kdr_tver = _L[_i][0];
            return "";
        }
    }
    return "The DRBR starting save (drbr_data\\start_filech3) is damaged or is not one this DRBR version knows (" + string(_sz) + " bytes, SHA-1 " + _h + ").";
}

// "" = _name is a whole Chapter 3 PC save (3055 lines; the last three are the story point, a Chapter 3 room id and the
// play time), else what is wrong with it
function kdr_check_save(_name)
{
    if (!file_exists(_name))
        return "missing";
    var _f = file_text_open_read(_name);
    if (_f == -1)
        return "unreadable";
    var _n = 0;
    var _a = "";
    var _b = "";
    var _c = "";
    while (!file_text_eof(_f) && _n < 3100)
    {
        _a = _b;
        _b = _c;
        _c = file_text_read_string(_f);
        file_text_readln(_f);
        _n++;
    }
    file_text_close(_f);
    if (_n != 3055)
        return "not a Chapter 3 save (" + string(_n) + " lines, 3055 expected)";
    var _plot = kdr_strip(_a);
    var _rid = kdr_strip(_b);
    if (_plot == "" || string_digits(_plot) != _plot || _rid == "" || string_digits(_rid) != _rid)
        return "its story point / room are not numbers";
    var _r = real(_rid);
    if (_r < 30000 || _r >= 40000 || scr_get_room_by_id(_r) == -1)
        return "its room (" + _rid + ") is not a Chapter 3 room";
    return "";
}

// "" = drbr_profile/filech3_0 is what to load now (global.kdr_from says where it came from), else why DRBR cannot start
function kdr_prepare()
{
    if (!directory_exists(KDR_DIR))
        directory_create(KDR_DIR);
    var _t = kdr_check_template();
    if (_t != "")
        return _t;
    if (string_lower(kdr_cfg_get("start_mode", "template")) == "continue" && kdr_check_save(KDR_LIVE) == "")
    {
        global.kdr_from = "continue";
        return "";
    }
    // the provided save, byte for byte
    var _b = buffer_load(KDR_TEMPLATE);
    if (!buffer_exists(_b))
        return "The DRBR starting save could not be read.";
    buffer_save(_b, KDR_LIVE);
    buffer_delete(_b);
    var _c = kdr_check_save(KDR_LIVE);
    if (_c != "")
        return "The DRBR save folder could not be written (" + _c + ").";
    global.kdr_from = "template";
    return "";
}

// obj_initializer2, instead of going to the intro / file menu: 1 = DRBR started the game, 0 = not a DRBR install
function kdr_boot()
{
    if (!kdr_on())
        return 0;
    if (global.kdr_booted)
        return 1;
    global.kdr_booted = 1;
    var _err = kdr_prepare();
    kdr_log_start(_err);
    if (_err != "")
    {
        show_message("DRBR could not start.\n\n" + _err + "\n\nClose the game, open DRBR Launcher and choose REPAIR (or RESTORE STARTING SAVE).\nYour own DELTARUNE saves were not touched.");
        game_end();
        return 1;
    }
    // what the file menu's CONTINUE does (DEVICE_MENU), for the DRBR slot
    global.tempflag[10] = 1;
    global.filechoice = 0;
    snd_free_all();
    var _fd = instance_create(0, 0, obj_persistentfadein);
    _fd.image_xscale = 1000;
    _fd.image_yscale = 1000;
    kdr_load_keyconfig();
    global.kdr_expect = 1;
    global.kdr_wait = 0;
    global.kdr_hint_t = 0;
    scr_load();
    return 1;
}

// the DRBR slot's controls (drbr_profile/keyconfig_0.ini, written by the game's own CONFIG menu); none = the defaults
function kdr_load_keyconfig()
{
    var _k = "keyconfig_" + string(global.filechoice) + ".ini";
    if (!ossafe_file_exists(_k))
        return 0;
    ossafe_ini_open(_k);
    for (var _i = 0; _i < 10; _i++)
    {
        var _v = ini_read_real("KEYBOARD_CONTROLS", string(_i), -1);
        if (_v != -1)
            global.input_k[_i] = _v;
    }
    for (var _i = 0; _i < 10; _i++)
    {
        var _v = ini_read_real("GAMEPAD_CONTROLS", string(_i), -1);
        if (_v != -1)
            global.input_g[_i] = _v;
    }
    ini_close();
    return 1;
}

function kdr_log_start(_err)
{
    ini_open(KDR_LOG);
    ini_section_delete("start");
    ini_write_string("start", "result", (_err == "") ? "loading" : "error");
    ini_write_string("start", "error", _err);
    ini_write_string("start", "from", global.kdr_from);
    ini_write_real("start", "template_version", variable_global_exists("kdr_tver") ? global.kdr_tver : 0);
    ini_write_string("start", "profile", kdr_cfg_get("profile", ""));
    ini_write_string("start", "start_mode", kdr_cfg_get("start_mode", "template"));
    ini_write_string("start", "build", "51.12");
    ini_write_string("start", "when", date_datetime_string(date_current_datetime()));
    ini_close();
}

// obj_gamecontroller's Begin Step, every frame: after the DRBR start, the first room the game really reaches is written
// down (the launcher checks it is the starting room)
function kdr_frame()
{
    if (!variable_global_exists("kdr_expect") || global.kdr_expect <= 0)
        return 0;
    if (room == ROOM_INITIALIZE)
        return 0;
    global.kdr_wait++;
    if (!instance_exists(obj_mainchara) && global.kdr_wait < 120)
        return 0;
    global.kdr_expect = 0;
    var _rid = scr_get_id_by_room_index(room);
    var _want = real(kdr_cfg_get("starting_room_id", "30108"));
    ini_open(KDR_LOG);
    ini_write_string("start", "result", (_rid == _want || global.kdr_from == "continue") ? "ok" : "wrong_room");
    ini_write_string("start", "room", room_get_name(room));
    ini_write_real("start", "room_id", _rid);
    ini_write_real("start", "plot", global.plot);
    ini_write_real("start", "x", instance_exists(obj_mainchara) ? obj_mainchara.x : -1);
    ini_write_real("start", "y", instance_exists(obj_mainchara) ? obj_mainchara.y : -1);
    ini_write_real("start", "party", (global.char[0] * 100) + (global.char[1] * 10) + global.char[2]);
    ini_close();
    kdr_pending_offer();
    return 1;
}

// the chapter switch (scr_chapterswitch): the DRBR install has only Chapter 3 - back to the DRBR start instead
function kdr_chapter_switch(_ch)
{
    snd_free_all();
    global.kdr_booted = 0;
    global.kdr_expect = 0;
    game_restart();
}

// a short line on arrival (DRBR only, the first 8 seconds in the starting room): where the hub and ONLINE are
function kdr_hint_draw()
{
    if (!kdr_on() || room != room_dw_snow_zone || global.plot < 310 || global.plot >= 330)
        return 0;
    if (variable_global_exists("knight_run") && global.knight_run == 1)
        return 0;
    if (global.kdr_hint_t >= 240)
        return 0;
    global.kdr_hint_t++;
    var _a = (global.kdr_hint_t < 200) ? 1 : ((240 - global.kdr_hint_t) / 40);
    var _cx = camerax() + 320;
    var _cy = cameray() + 20;
    draw_set_alpha(0.7 * _a);
    draw_set_color(c_black);
    draw_rectangle(_cx - 250, _cy - 6, _cx + 250, _cy + 38, false);
    draw_set_alpha(_a);
    draw_set_halign(fa_center);
    draw_set_color(c_yellow);
    knight_txt_tiny(_cx, _cy, "DRBR - DELTARUNE BATTLE ROYALE");
    draw_set_color(c_white);
    knight_txt_tiny(_cx, _cy + 16, "The sign just ahead opens the hub. ONLINE is in its menu.");
    draw_set_halign(fa_left);
    draw_set_alpha(1);
    return 1;
}

// ---------------------------------------------------------------------------------------------------------------------
// UPDATE, THEN BACK TO THE ROOM. A Steam room the game could not join because its players have a NEWER DRBR build is
// written down (drbr_profile/pending_join.ini: only its lobby number and builds - nothing that could choose a download).
// DRBR Launcher sees it and offers the update (from DRBR's own GitHub releases, signed); the updated game, at its start,
// offers that room with the invite box - JOIN or NOT NOW: the player decides, the game never joins by itself.
function kdr_pending_join(_lid, _ver, _host)
{
    if (!kdr_on())
        return 0;
    if (!directory_exists(KDR_DIR))
        directory_create(KDR_DIR);
    ini_open(KDR_PENDING);
    ini_section_delete("join");
    ini_write_string("join", "lobby", string(_lid));
    ini_write_real("join", "their_build", _ver);
    ini_write_real("join", "my_build", kfo_version());
    ini_write_string("join", "host", is_string(_host) ? _host : "");
    ini_write_real("join", "stamp", date_current_datetime());
    ini_write_string("join", "when", date_datetime_string(date_current_datetime()));
    ini_close();
    return 1;
}

// the mod's name as the player knows it: "DRBR" in the DRBR install, "Knight Hub" in the in-place Knight Hub
function kdr_name()
{
    return kdr_on() ? "DRBR" : "Knight Hub";
}

// a room (relay code) or a host with another build: in DRBR it says how to update (no rejoin offer: that is for Steam rooms)
function kdr_other_build(_newer, _who)
{
    if (kdr_on())
        return _newer ? (_who + " a newer DRBR. Close the game and update it in DRBR Launcher.") : (_who + " an older DRBR (they need to update).");
    return _who + (_newer ? " a newer Knight Hub build." : " an older Knight Hub build.");
}

// the message for a room with a different build: in DRBR it says how to update
function kdr_build_why(_theirs)
{
    if (_theirs > kfo_version())
        return kdr_on() ? "That room has a newer DRBR. Close the game and open DRBR Launcher to update - it offers that room again after." : "That room's players have a newer Knight Hub build.";
    return kdr_on() ? "That room's players have an older DRBR (they need to update)." : "That room's players have an older Knight Hub build.";
}

// the DRBR start reached its room: a room kept from before an update becomes the invite box (fresh ones only, and only when
// this game now has that room's build)
function kdr_pending_offer()
{
    if (!kdr_on() || !file_exists(KDR_PENDING))
        return 0;
    ini_open(KDR_PENDING);
    var _lid = ini_read_string("join", "lobby", "");
    var _their = ini_read_real("join", "their_build", 0);
    var _stamp = ini_read_real("join", "stamp", 0);
    var _host = ini_read_string("join", "host", "");
    ini_close();
    file_delete(KDR_PENDING);
    if (_lid == "" || (date_current_datetime() - _stamp) > (1 / 24) || _their != kfo_version())
        return 0;
    var _o = kfo_get();
    _o.inv_in = { lobby: _lid, n: (_host != "") ? _host : "The room you tried to join", t: current_time, shown: false, back: true };
    return 1;
}
