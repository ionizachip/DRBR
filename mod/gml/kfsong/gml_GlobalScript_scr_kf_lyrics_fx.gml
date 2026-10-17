// =====================================================================
//  KF LYRICS FX  -  Nullscape-styled lyric rendering
//  Song: "IT DOESN'T END HERE" by DIGITAL DESCENDANT (Nullscape Vol. 3).
//  All rights to the song, recording and lyrics belong to DIGITAL DESCENDANT.
//
//  Styles (set per section / per line in song.json):
//    null    blue -> purple gradient, gentle wave
//    void    purple, jittering, glitch letters before they are sung
//    power   gold, purple glow, punch-in, chromatic split, screen flash
//    rise    yellow -> white, letters float upward
//    finale  big pulsing gold, wide spacing, big flash, holds after the line
//  Keywords (song.json "keywords") burn yellow inside any line.
// =====================================================================

// Build the glyph layout for one line (measured once, when the line starts).
function kf_lyrics_layout(_s, _idx, _font)
{
    if (_font >= 0) draw_set_font(_font);
    var _txt = _s.lines[_idx].text;
    var _g = [];
    var _x = 0;
    var _word = "";
    var _word_start = 0;
    var _n = string_length(_txt);
    for (var _i = 1; _i <= _n + 1; _i++)
    {
        var _c = (_i <= _n) ? string_char_at(_txt, _i) : " ";
        if (_c == " ")
        {
            // close the word: mark its glyphs as keyword or not
            if (_word != "")
            {
                var _kw = kf_song_is_keyword(_s, _word);
                for (var _k = _word_start; _k < array_length(_g); _k++) _g[_k].kw = _kw;
            }
            _word = "";
            if (_i <= _n) { array_push(_g, { c : " ", x : _x, kw : false }); _x += string_width(" "); }
            _word_start = array_length(_g);
        }
        else
        {
            _word += _c;
            array_push(_g, { c : _c, x : _x, kw : false });
            _x += string_width(_c);
        }
    }
    return { glyphs : _g, w : _x, h : string_height("A") };
}

function kf_pal(_s, _name, _fallback)
{
    if (_s != undefined && variable_struct_exists(_s.meta, "palette") && variable_struct_exists(_s.meta.palette, _name))
        return kf_hex(variable_struct_get(_s.meta.palette, _name));
    return _fallback;
}

// Draw one lyric line.
//  _lay   layout from kf_lyrics_layout      _style  style name
//  _cx,_y centre x / top y (GUI pixels)      _gs     GUI scale (gui width / 640)
//  _alpha overall alpha                      _age    seconds since the line started
//  _prog  0..1 how much has been sung        _exit   0..1 exit animation amount
function kf_lyrics_draw_line(_s, _lay, _style, _cx, _y, _gs, _alpha, _age, _prog, _exit)
{
    var _blue   = kf_pal(_s, "blue",   make_color_rgb(58, 107, 255));
    var _cyan   = kf_pal(_s, "cyan",   make_color_rgb(92, 200, 255));
    var _purple = kf_pal(_s, "purple", make_color_rgb(138, 61, 255));
    var _violet = kf_pal(_s, "violet", make_color_rgb(194, 77, 255));
    var _yellow = kf_pal(_s, "yellow", make_color_rgb(255, 217, 61));
    var _gold   = kf_pal(_s, "gold",   make_color_rgb(255, 182, 39));
    var _white  = kf_pal(_s, "white",  make_color_rgb(255, 246, 214));
    var _dim    = kf_pal(_s, "dim",    make_color_rgb(27, 31, 77));
    var _shadow = kf_pal(_s, "shadow", make_color_rgb(5, 3, 15));

    var _g = _lay.glyphs;
    var _n = array_length(_g);
    if (_n == 0) return;

    // base scale + punch-in
    var _sc = 1;
    var _track = 0;          // extra spacing per glyph (px, pre-scale)
    var _delay = 0.018;      // per-letter reveal delay
    switch (_style)
    {
        case "power":  _sc = 1.15 + 0.35 * max(0, 1 - _age / 0.22); break;
        case "finale": _sc = 1.6 + 0.9 * max(0, 1 - _age / 0.35); _track = 2 + min(_age, 3) * 0.6; _delay = 0.05; break;
        case "rise":   _sc = 1.05; break;
    }

    // fit to screen width
    var _full_w = (_lay.w + _track * (_n - 1)) * _sc;
    var _max_w = 600;
    if (_full_w > _max_w) { var _f = _max_w / _full_w; _sc *= _f; _track *= _f; _full_w = _max_w; }

    var _lit = floor(_prog * _n + 0.001);
    var _x0 = _cx - (_full_w * 0.5) * _gs;
    var _t = current_time / 1000;
    var _pulse = 0.5 + 0.5 * sin(_t * 6);
    var _o = 2 * _gs;        // outline/glow offset

    for (var _i = 0; _i < _n; _i++)
    {
        var _gl = _g[_i];
        var _c = _gl.c;
        if (_c == " ") continue;

        // reveal + exit
        var _ga = clamp((_age - _i * _delay) / 0.12, 0, 1);
        var _a = _alpha * _ga * (1 - _exit);
        if (_a <= 0.01) continue;

        var _px = _x0 + (_gl.x * _sc + _i * _track * _sc) * _gs;
        var _py = _y + (1 - _ga) * 8 * _gs - _exit * 10 * _gs;
        var _u = _i / max(1, _n - 1);            // 0..1 across the line
        var _is_lit = (_i < _lit);
        var _col = _blue;
        var _glow = -1;
        var _glow_a = 0;
        var _chroma = false;

        switch (_style)
        {
            case "void":
                _col = merge_color(_purple, _violet, _u);
                _px += random_range(-1.2, 1.2) * _gs;
                _py += random_range(-1.2, 1.2) * _gs;
                if (!_is_lit && random(1) < 0.04) _c = string_char_at("#%&@$!?/<>", irandom_range(1, 10));
                _glow = _blue; _glow_a = 0.25;
                break;
            case "power":
                _col = merge_color(_gold, _yellow, _u);
                _glow = _purple; _glow_a = 0.55;
                _chroma = true;
                break;
            case "rise":
                _col = merge_color(_yellow, _white, _u);
                _py -= min(_age, 1.5) * 3 * _gs + sin(_t * 3 + _i * 0.4) * 1.5 * _gs;
                _glow = _gold; _glow_a = 0.25;
                break;
            case "finale":
                _col = merge_color(_gold, _white, _pulse * 0.6);
                _py += sin(_t * 2.5 + _i * 0.35) * 2 * _gs;
                _glow = merge_color(_purple, _blue, _pulse); _glow_a = 0.6;
                _chroma = true;
                break;
            default: // "null"
                _col = merge_color(_blue, _purple, _u);
                _py += sin(_t * 4 + _i * 0.5) * 1.2 * _gs;
                _glow = _cyan; _glow_a = 0.15;
                break;
        }

        // keyword burn
        if (_gl.kw)
        {
            if (_style == "power" || _style == "finale") { _col = _white; _glow = _yellow; _glow_a = 0.7; }
            else { _col = _yellow; _glow = _gold; _glow_a = 0.5 + 0.2 * _pulse; }
        }

        // not sung yet -> dim
        if (!_is_lit)
        {
            var _dimk = (_style == "power" || _style == "finale") ? 0.35 : 0.6;
            _col = merge_color(_col, _dim, _dimk);
            _glow_a *= 0.3;
            _a *= 0.75;
        }

        var _s2 = _sc * _gs;

        // shadow / outline
        draw_text_transformed_color(_px + _o, _py + _o, _c, _s2, _s2, 0, _shadow, _shadow, _shadow, _shadow, _a * 0.9);
        draw_text_transformed_color(_px - _o * 0.5, _py, _c, _s2, _s2, 0, _shadow, _shadow, _shadow, _shadow, _a * 0.6);
        draw_text_transformed_color(_px + _o * 0.5, _py, _c, _s2, _s2, 0, _shadow, _shadow, _shadow, _shadow, _a * 0.6);

        // glow
        if (_glow != -1 && _glow_a > 0)
        {
            var _ga2 = _a * _glow_a;
            draw_text_transformed_color(_px - _o, _py - _o, _c, _s2, _s2, 0, _glow, _glow, _glow, _glow, _ga2);
            draw_text_transformed_color(_px + _o, _py - _o, _c, _s2, _s2, 0, _glow, _glow, _glow, _glow, _ga2);
            draw_text_transformed_color(_px - _o, _py + _o, _c, _s2, _s2, 0, _glow, _glow, _glow, _glow, _ga2);
            draw_text_transformed_color(_px + _o, _py + _o, _c, _s2, _s2, 0, _glow, _glow, _glow, _glow, _ga2);
        }

        // chromatic split (blue left, purple right)
        if (_chroma && _is_lit)
        {
            var _cs = (1.5 + 2.5 * max(0, 1 - _age / 0.3)) * _gs;
            draw_text_transformed_color(_px - _cs, _py, _c, _s2, _s2, 0, _blue, _blue, _blue, _blue, _a * 0.45);
            draw_text_transformed_color(_px + _cs, _py, _c, _s2, _s2, 0, _violet, _violet, _violet, _violet, _a * 0.45);
        }

        // main glyph
        draw_text_transformed_color(_px, _py, _c, _s2, _s2, 0, _col, _col, _col, _col, _a);
    }
}

// Small "NOW PLAYING" credit card. _k = 0..1 slide-in amount.
function kf_lyrics_draw_credit_card(_s, _gs, _k)
{
    if (_s == undefined || _k <= 0) return;
    var _navy   = kf_pal(_s, "shadow", make_color_rgb(5, 3, 15));
    var _purple = kf_pal(_s, "purple", make_color_rgb(138, 61, 255));
    var _yellow = kf_pal(_s, "yellow", make_color_rgb(255, 217, 61));
    var _cyan   = kf_pal(_s, "cyan",   make_color_rgb(92, 200, 255));
    var _white  = kf_pal(_s, "white",  make_color_rgb(255, 246, 214));

    var _e = 1 - power(1 - _k, 3);
    var _w = 230 * _gs, _h = 62 * _gs;
    var _x = -_w + (12 * _gs + _w) * _e;
    // (Knight Fights: the card goes under the hub's own lines - global.kf_card_y, set by the hub every step)
    var _y = (variable_global_exists("kf_card_y") ? global.kf_card_y : 12) * _gs;
    var _a = _e;

    draw_set_alpha(0.85 * _a);
    draw_set_color(_navy);
    draw_rectangle(_x, _y, _x + _w, _y + _h, false);
    draw_set_alpha(_a);
    draw_set_color(_purple);
    draw_rectangle(_x, _y, _x + _w, _y + _h, true);
    draw_rectangle(_x + 1, _y + 1, _x + _w - 1, _y + _h - 1, true);
    draw_set_color(_yellow);
    draw_rectangle(_x, _y, _x + 3 * _gs, _y + _h, false);
    draw_set_alpha(1);

    var _tx = _x + 10 * _gs;
    draw_text_transformed_color(_tx, _y + 5 * _gs,  "NOW PLAYING", 0.5 * _gs, 0.5 * _gs, 0, _cyan, _cyan, _cyan, _cyan, _a);
    draw_text_transformed_color(_tx, _y + 16 * _gs, _s.meta.title, 0.75 * _gs, 0.75 * _gs, 0, _yellow, _yellow, _yellow, _yellow, _a);
    draw_text_transformed_color(_tx, _y + 33 * _gs, _s.meta.artist, 0.6 * _gs, 0.6 * _gs, 0, _white, _white, _white, _white, _a);
    draw_text_transformed_color(_tx, _y + 47 * _gs, _s.meta.album, 0.5 * _gs, 0.5 * _gs, 0, _purple, _purple, _purple, _purple, _a);
}
