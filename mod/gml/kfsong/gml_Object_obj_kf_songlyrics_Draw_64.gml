if (song == undefined) exit;

var _gw = display_get_gui_width();
var _gh = display_get_gui_height();
var _gs = _gw / 640;
var _t  = kf_song_time(song);

if (font_lyric >= 0) draw_set_font(font_lyric);
draw_set_halign(fa_left);
draw_set_valign(fa_top);

// screen flash on powerful lines
// (Knight Fights: the flash belongs to the pack's lyric look - only with its lyrics on)
if (flash > 0 && show_lyrics)
{
    draw_set_alpha(flash * 0.5);
    draw_set_color(flash_col);
    draw_rectangle(0, 0, _gw, _gh, false);
    draw_set_alpha(1);
}

if (show_lyrics)
{
    var _cx = _gw * 0.5;
    var _y  = lyric_y * _gs;

    // soft dark band behind the lyrics for readability
    if (cur_lay != undefined || old_lay != undefined)
    {
        draw_set_alpha(0.35);
        draw_set_color(kf_pal(song, "shadow", c_black));
        draw_rectangle(0, _y - 8 * _gs, _gw, _y + 30 * _gs, false);
        draw_set_alpha(1);
    }

    // section banner
    if (banner_t < 1.6)
    {
        var _ba = min(1, banner_t / 0.15) * min(1, (1.6 - banner_t) / 0.4);
        var _bc = kf_pal(song, "purple", c_purple);
        var _bs = 0.5 * _gs;
        var _bt = "- " + banner_text + " -";
        draw_text_transformed_color(_cx - string_width(_bt) * _bs * 0.5, _y - 18 * _gs, _bt, _bs, _bs, 0, _bc, _bc, _bc, _bc, _ba);
    }

    if (old_lay != undefined)
        kf_lyrics_draw_line(song, old_lay, old_style, _cx, _y, _gs, 1, _t - old_start, 1, old_exit);

    if (cur_lay != undefined)
    {
        var _prog = (cur_exit >= 0) ? 1 : kf_song_line_progress(song);
        kf_lyrics_draw_line(song, cur_lay, cur_style, _cx, _y, _gs, 1, _t - cur_start, _prog, max(0, cur_exit));
    }
}

if (show_credit)
{
    // NOW PLAYING card
    var _k = 0;
    if (_t < credit_time) _k = min(1, _t / 0.4);
    else if (_t < credit_time + 0.5) _k = 1 - (_t - credit_time) / 0.5;
    kf_lyrics_draw_credit_card(song, _gs, _k);

    // small permanent credit, top right
    var _cs = 0.45 * _gs;
    var _ct = "MUSIC: " + song.meta.artist;
    var _cc = kf_pal(song, "cyan", c_aqua);
    draw_text_transformed_color(_gw - string_width(_ct) * _cs - 6 * _gs, 4 * _gs, _ct, _cs, _cs, 0, _cc, _cc, _cc, _cc, 0.6);
}

draw_set_color(c_white);
draw_set_alpha(1);
