// =====================================================================
//  KF SONG SYSTEM  -  lyric-synced music for Knight Fights (Deltarune Ch.3)
//
//  SONG CREDIT
//    "IT DOESN'T END HERE" by DIGITAL DESCENDANT  (Nullscape Vol. 3)
//    All rights to the song, recording and lyrics belong to DIGITAL DESCENDANT.
//    Keep this credit (and the on-screen credit card) in any build you share.
//
//  Song files live next to data.win:
//    kfsongs/<song_id>/song.json    title, artist, credit, file names, sections
//    kfsongs/<song_id>/inst.ogg     instrumental
//    kfsongs/<song_id>/vocals.ogg   vocal stem (plays in sync, can be muted)
//    kfsongs/<song_id>/lyrics.json  timed lines (made by MERGE_LYRICS.bat)
//
//  Quick use:
//    global.kf_song = kf_song_load("it_doesnt_end_here");
//    kf_song_play(global.kf_song, true);      // true = vocals on
//    kf_song_update(global.kf_song);          // once per step (obj_kf_songlyrics does this)
//    kf_song_section(global.kf_song)          // "Chorus", "Bridge", ...
//    kf_song_section_changed(global.kf_song)  // true on the step a section begins
// =====================================================================

global.kf_song = undefined;          // the song currently loaded/playing
global.kf_song_request = undefined;  // used by kf_song_start -> obj_kf_songlyrics
global.kf_lyrics_shake = 0;          // optional camera shake amount (pixels) on powerful lines
global.kf_song_settings_data = {
    vocals : true,   // play the vocal stem
    lyrics : true,   // draw lyrics
    credit : true,   // show the credit card + corner credit (keep this on in shared builds)
    volume : 1       // 0..1
};

// ---------- mod-menu helpers ------------------------------------------

// (Knight Fights: the globals above are also made on first use, should this script's top-level code not have run yet)
function kf_song_init()
{
    if (variable_global_exists("kf_song_settings_data") && is_struct(global.kf_song_settings_data))
        return;
    global.kf_song = undefined;
    global.kf_song_request = undefined;
    global.kf_lyrics_shake = 0;
    global.kf_song_settings_data = { vocals : true, lyrics : true, credit : true, volume : 1 };
}

function kf_song_settings() { kf_song_init(); return global.kf_song_settings_data; }

// Every song folder in kfsongs/ that has a song.json.
// Returns an array of { song_id, title, artist, album, credit } for a picker menu.
function kf_song_catalog()
{
    var _out = [];
    var _base = "";
    if (directory_exists(working_directory + "kfsongs")) _base = working_directory + "kfsongs/";
    else if (directory_exists(program_directory + "kfsongs")) _base = program_directory + "kfsongs/";
    else return _out;

    var _names = [];
    var _f = file_find_first(_base + "*", fa_directory);
    while (_f != "")
    {
        if (_f != "." && _f != "..") array_push(_names, _f);
        _f = file_find_next();
    }
    file_find_close();

    for (var _i = 0; _i < array_length(_names); _i++)
    {
        var _p = _base + _names[_i] + "/song.json";
        if (!file_exists(_p)) continue;
        var _m = json_parse(kf_song_read_text(_p));
        array_push(_out, {
            song_id : _names[_i],
            title   : _m.title,
            artist  : _m.artist,
            album   : variable_struct_exists(_m, "album") ? _m.album : "",
            credit  : _m.credit
        });
    }
    return _out;
}

// One call to start a song with the Nullscape lyric display.
// Returns the obj_kf_songlyrics instance (or noone if the object is missing).
function kf_song_start(_song_id)
{
    kf_song_init();
    kf_song_end();
    var _obj = asset_get_index("obj_kf_songlyrics");
    if (_obj < 0) { show_debug_message("[KFSong] obj_kf_songlyrics not imported"); return noone; }
    global.kf_song_request = { song_id : _song_id, vocals : kf_song_settings().vocals };
    return instance_create_depth(0, 0, -99999, _obj);
}

// Stop the song and remove the lyric display.
function kf_song_end()
{
    kf_song_init();
    var _obj = asset_get_index("obj_kf_songlyrics");
    if (_obj >= 0) with (_obj) instance_destroy();
    if (global.kf_song != undefined) kf_song_stop(global.kf_song);
    global.kf_song = undefined;
}

// Style for a lyric line: "null", "void", "power", "rise" or "finale".
function kf_song_line_style(_s, _idx)
{
    if (_s == undefined || _idx < 0) return "null";
    var _m = _s.meta;
    var _key = string(_idx);
    if (variable_struct_exists(_m, "line_styles") && variable_struct_exists(_m.line_styles, _key))
        return variable_struct_get(_m.line_styles, _key);
    var _sec = _s.lines[_idx].section;
    if (variable_struct_exists(_m, "section_styles") && variable_struct_exists(_m.section_styles, _sec))
        return variable_struct_get(_m.section_styles, _sec);
    return "null";
}

function kf_song_is_keyword(_s, _word)
{
    if (_s == undefined || !variable_struct_exists(_s.meta, "keywords")) return false;
    var _w = string_lower(_word);
    var _clean = "";
    for (var _i = 1; _i <= string_length(_w); _i++)
    {
        var _c = string_char_at(_w, _i);
        var _o = ord(_c);
        if (_o >= 97 && _o <= 122) _clean += _c;
    }
    var _k = _s.meta.keywords;
    for (var _j = 0; _j < array_length(_k); _j++) if (_k[_j] == _clean) return true;
    return false;
}

// "#RRGGBB" -> GameMaker colour
function kf_hex(_h)
{
    var _d = "0123456789ABCDEF";
    var _u = string_upper(string_replace(_h, "#", ""));
    var _v = [0, 0, 0];
    for (var _i = 0; _i < 3; _i++)
        _v[_i] = (string_pos(string_char_at(_u, _i * 2 + 1), _d) - 1) * 16 + (string_pos(string_char_at(_u, _i * 2 + 2), _d) - 1);
    return make_color_rgb(_v[0], _v[1], _v[2]);
}

// ---------- files ----------------------------------------------------

function kf_song_path(_rel)
{
    var _c = [working_directory + _rel, program_directory + _rel, _rel];
    for (var _i = 0; _i < array_length(_c); _i++)
    {
        if (file_exists(_c[_i])) return _c[_i];
    }
    return "";
}

function kf_song_read_text(_path)
{
    var _f = file_text_open_read(_path);
    if (_f < 0) return "";
    var _s = "";
    // (Knight Fights: each line read with file_text_read_string, the classic way - the same text on every runner)
    while (!file_text_eof(_f))
    {
        _s += file_text_read_string(_f) + "\n";
        file_text_readln(_f);
    }
    file_text_close(_f);
    return _s;
}

// ---------- load -----------------------------------------------------

function kf_song_load(_song_id)
{
    var _dir = "kfsongs/" + _song_id + "/";
    var _meta_path = kf_song_path(_dir + "song.json");
    if (_meta_path == "")
    {
        show_debug_message("[KFSong] missing " + _dir + "song.json");
        return undefined;
    }
    var _meta = json_parse(kf_song_read_text(_meta_path));

    // timed lyric lines (optional - music still plays without them)
    var _lines = [];
    var _lyr_path = kf_song_path(_dir + _meta.lyrics);
    if (_lyr_path != "")
    {
        var _lyr = json_parse(kf_song_read_text(_lyr_path));
        _lines = _lyr.lines;
        for (var _i = 0; _i < array_length(_lines); _i++)
        {
            var _ln = _lines[_i];
            _ln.t0 = variable_struct_get(_ln, "start");
            _ln.t1 = variable_struct_get(_ln, "end");
            if (!variable_struct_exists(_ln, "text")) _ln.text = "";
        }
    }
    else
    {
        show_debug_message("[KFSong] no lyrics.json for " + _song_id + " (run MERGE_LYRICS.bat)");
    }

    var _sections = [];
    if (variable_struct_exists(_meta, "sections")) _sections = _meta.sections;

    return {
        song_id      : _song_id,
        meta         : _meta,
        lines        : _lines,
        sections     : _sections,
        inst_path    : kf_song_path(_dir + _meta.instrumental),
        vocal_path   : kf_song_path(_dir + _meta.vocals),
        inst_stream  : -1,
        vocal_stream : -1,
        inst         : -1,
        vocal        : -1,
        volume       : 1,
        vocals_on    : true,
        playing      : false,
        paused       : false,
        finished     : false,
        line         : -1,     // index of the latest line that has started
        line_active  : false,  // true while that line is being sung
        section      : -1,     // index into sections
        line_changed    : false,
        section_changed : false
    };
}

// ---------- playback -------------------------------------------------

function kf_song_play(_s, _vocals)
{
    if (_s == undefined) return false;
    kf_song_stop(_s);
    if (_s.inst_path == "")
    {
        show_debug_message("[KFSong] missing " + _s.meta.instrumental);
        return false;
    }
    _s.inst_stream = audio_create_stream(_s.inst_path);
    _s.inst = audio_play_sound(_s.inst_stream, 90, false);
    audio_sound_gain(_s.inst, _s.volume, 0);

    if (_s.vocal_path != "")
    {
        _s.vocal_stream = audio_create_stream(_s.vocal_path);
        _s.vocal = audio_play_sound(_s.vocal_stream, 90, false);
        audio_sound_gain(_s.vocal, _vocals ? _s.volume : 0, 0);
    }
    _s.vocals_on = _vocals;
    _s.playing = true;
    _s.paused = false;
    _s.finished = false;
    _s.line = -1;
    _s.line_active = false;
    _s.section = -1;
    return true;
}

function kf_song_stop(_s)
{
    if (_s == undefined) return;
    if (_s.inst != -1)  audio_stop_sound(_s.inst);
    if (_s.vocal != -1) audio_stop_sound(_s.vocal);
    if (_s.inst_stream != -1)  audio_destroy_stream(_s.inst_stream);
    if (_s.vocal_stream != -1) audio_destroy_stream(_s.vocal_stream);
    _s.inst = -1; _s.vocal = -1;
    _s.inst_stream = -1; _s.vocal_stream = -1;
    _s.playing = false;
    _s.paused = false;
}

function kf_song_pause(_s)
{
    if (_s == undefined || !_s.playing || _s.paused) return;
    audio_pause_sound(_s.inst);
    if (_s.vocal != -1) audio_pause_sound(_s.vocal);
    _s.paused = true;
}

function kf_song_resume(_s)
{
    if (_s == undefined || !_s.playing || !_s.paused) return;
    audio_resume_sound(_s.inst);
    if (_s.vocal != -1)
    {
        audio_sound_set_track_position(_s.vocal, audio_sound_get_track_position(_s.inst));
        audio_resume_sound(_s.vocal);
    }
    _s.paused = false;
}

function kf_song_seek(_s, _t)
{
    if (_s == undefined || !_s.playing) return;
    _t = clamp(_t, 0, _s.meta.length - 0.05);
    audio_sound_set_track_position(_s.inst, _t);
    if (_s.vocal != -1) audio_sound_set_track_position(_s.vocal, _t);
    _s.line = -1;      // recalculated next update
    _s.section = -1;
}

function kf_song_set_vocals(_s, _on)
{
    if (_s == undefined) return;
    _s.vocals_on = _on;
    if (_s.vocal != -1) audio_sound_gain(_s.vocal, _on ? _s.volume : 0, 200);
}

function kf_song_set_volume(_s, _vol)
{
    if (_s == undefined) return;
    _s.volume = _vol;
    if (_s.inst != -1)  audio_sound_gain(_s.inst, _vol, 0);
    if (_s.vocal != -1) audio_sound_gain(_s.vocal, _s.vocals_on ? _vol : 0, 0);
}

// ---------- per-step update ------------------------------------------

function kf_song_update(_s)
{
    if (_s == undefined) return;
    _s.line_changed = false;
    _s.section_changed = false;
    if (!_s.playing || _s.paused) return;

    if (!audio_is_playing(_s.inst))
    {
        _s.playing = false;
        _s.finished = true;
        _s.line_active = false;
        return;
    }

    var _t = audio_sound_get_track_position(_s.inst);

    // keep the vocal stream locked to the instrumental
    if (_s.vocal != -1 && audio_is_playing(_s.vocal))
    {
        if (abs(audio_sound_get_track_position(_s.vocal) - _t) > 0.08)
            audio_sound_set_track_position(_s.vocal, _t);
    }

    // current lyric line
    var _n = array_length(_s.lines);
    var _i = _s.line;
    if (_i >= 0 && _i < _n && _t < _s.lines[_i].t0) _i = -1;   // went backwards
    while (_i + 1 < _n && _s.lines[_i + 1].t0 <= _t) _i++;
    if (_i != _s.line) _s.line_changed = true;
    _s.line = _i;
    _s.line_active = (_i >= 0 && _t <= _s.lines[_i].t1);

    // current section
    var _m = array_length(_s.sections);
    var _k = _s.section;
    if (_k >= 0 && _k < _m && _t < _s.sections[_k].start) _k = -1;
    while (_k + 1 < _m && _s.sections[_k + 1].start <= _t) _k++;
    if (_k != _s.section) _s.section_changed = true;
    _s.section = _k;
}

// ---------- queries (use these to sync attacks) ----------------------

function kf_song_time(_s)
{
    if (_s == undefined || _s.inst == -1) return 0;
    return audio_sound_get_track_position(_s.inst);
}

function kf_song_frame(_s)           { return floor(kf_song_time(_s) * 30); }
function kf_song_progress(_s)        { return (_s == undefined) ? 0 : clamp(kf_song_time(_s) / _s.meta.length, 0, 1); }
function kf_song_is_playing(_s)      { return (_s != undefined && _s.playing); }
function kf_song_is_finished(_s)     { return (_s != undefined && _s.finished); }
function kf_song_line_changed(_s)    { return (_s != undefined && _s.line_changed); }
function kf_song_section_changed(_s) { return (_s != undefined && _s.section_changed); }

function kf_song_line_index(_s)
{
    return (_s == undefined || !_s.line_active) ? -1 : _s.line;
}

function kf_song_line_text(_s)
{
    if (_s == undefined || !_s.line_active || _s.line < 0) return "";
    return _s.lines[_s.line].text;
}

// 0..1 through the current sung line (for karaoke fill / attack ramps)
function kf_song_line_progress(_s)
{
    if (_s == undefined || !_s.line_active || _s.line < 0) return 0;
    var _ln = _s.lines[_s.line];
    var _len = max(0.25, (_ln.t1 - _ln.t0) - 0.3);
    return clamp((kf_song_time(_s) - _ln.t0) / _len, 0, 1);
}

function kf_song_section(_s)
{
    if (_s == undefined || _s.section < 0) return "";
    return _s.sections[_s.section].name;
}

// which time this section name has come up (Chorus 1 vs Chorus 2)
function kf_song_section_occurrence(_s)
{
    if (_s == undefined || _s.section < 0) return 0;
    return _s.sections[_s.section].occurrence;
}

function kf_song_credit(_s)
{
    if (_s == undefined) return "";
    return _s.meta.credit;
}

// ---------- online sync helpers --------------------------------------
// Host:   send kf_song_time(song) with your normal state packet.
// Client: kf_song_sync(song, host_time + estimated_one_way_latency)
function kf_song_sync(_s, _host_t)
{
    if (_s == undefined || !_s.playing) return;
    if (abs(kf_song_time(_s) - _host_t) > 0.15) kf_song_seek(_s, _host_t);
}
