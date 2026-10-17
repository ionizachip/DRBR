if (song == undefined) { instance_destroy(); exit; }

if (!started)
{
    started = true;
    kf_song_play(song, vocals);
}

kf_song_update(song);

var _dt = delta_time / 1000000;
var _t  = kf_song_time(song);

// new line started
if (kf_song_line_changed(song) && song.line >= 0 && song.line_active)
{
    if (cur_lay != undefined)
    {
        old_lay = cur_lay; old_style = cur_style; old_start = cur_start;
        old_exit = max(0, cur_exit);
    }
    cur_line  = song.line;
    cur_lay   = kf_lyrics_layout(song, cur_line, font_lyric);
    cur_style = kf_song_line_style(song, cur_line);
    cur_start = song.lines[cur_line].t0;
    cur_exit  = -1;

    if (cur_style == "power")  { flash = 0.22; flash_col = kf_pal(song, "violet", c_purple); global.kf_lyrics_shake = 3; }
    if (cur_style == "finale") { flash = 0.7;  flash_col = c_white;                          global.kf_lyrics_shake = 6; }
}

// current line finished -> exit animation (the finale holds 4 extra seconds)
if (cur_lay != undefined && cur_exit < 0)
{
    var _end = song.lines[cur_line].t1 + ((cur_style == "finale") ? 4 : 0);
    if (_t > _end || !kf_song_is_playing(song)) cur_exit = 0;
}
if (cur_exit >= 0)
{
    cur_exit += _dt / ((cur_style == "finale") ? 1.5 : 0.3);
    if (cur_exit >= 1) { cur_lay = undefined; cur_exit = -1; cur_line = -1; }
}
if (old_lay != undefined)
{
    old_exit += _dt / 0.25;
    if (old_exit >= 1) old_lay = undefined;
}

// section banner
if (kf_song_section_changed(song))
{
    var _sec = kf_song_section(song);
    if (_sec != "Intro" && _sec != "Ending") { banner_text = string_upper(_sec); banner_t = 0; }
}
banner_t += _dt;

flash = max(0, flash - _dt * 1.6);
global.kf_lyrics_shake = max(0, global.kf_lyrics_shake - _dt * 12);

if (destroy_when_done && kf_song_is_finished(song)) instance_destroy();
