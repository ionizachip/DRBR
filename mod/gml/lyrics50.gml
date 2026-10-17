// the lyrics and their timing (seconds into the song's own file)
//   Flower Man: Chapter 5's obj_flowery_lyrics, as the game has it (Flowerman_Arrangement.ogg, the Flowery fight)
//   Raise Up Your Bat: Chapter 3's karaoke chart (scr_rhythmgame_notechart, song 0: the lines Tenna's karaoke shows for
//   ch3_karaoke_full.ogg); its syllables spread evenly over each line (the chart has no vocal notes)
function knight_lyr_songs()
{
    return [
        { file: "Flowerman_Arrangement.ogg", len: 192.024, bpm: 160, flowery: true,
          lt: [0.0, 24.0, 27.38, 30.75, 33.75, 36.0, 39.38, 42.75, 45.75, 47.25, 50.25, 53.06, 55.12, 57.94, 59.25, 62.25, 65.06, 67.12, 70.5, 72.0, 144.0, 147.38, 150.75, 153.75, 156.0, 159.38, 162.75, 165.75, 167.25, 170.25, 173.06, 175.12, 177.94, 179.25, 182.25, 185.06, 187.12, 190.5, 192.0], ly: ["", "Ten feet twen-ty the Flow-er Man", "Is wai-ting for the touch of his hand", "Straight-en-ing pe-tals out with-out a plan", "Like the eve-ry dai-ly", "Wish that both-ers the Flow-er Man", "Could I do some-thing to make him laugh", "In-side my lit-tle cham-ber made of glass", "So he lived the", "Flow-er Man, Flow-er Man", "With his heart in the sand", "So he stands", "To watch the whole wide world", "From a can", "Way up high in the sky", "With the sun in his eyes", "Ain't it nice", "The life for-ev-er for", "Flow-ers", "", "Ten feet twen-ty the Flow-er Man", "Is wait-ing for the touch of his hand", "Fall-en to pie-ces still with-out a plan", "Yet the eve-ry dai-ly", "Hope that pow-ered the Flow-er Man", "Would nev-er cow-er off of its path", "Even if bro-ken I am more than glass", "So he lived the", "Flow-er Man, Flow-er Man", "With his heart in the sand", "So he stands", "To watch the whole wide world", "From a can", "Way up high in the sky", "With the sun in your eyes", "Ain't it nice", "The life for-ev-er for", "Flow-ers", ""],
          nt: [24, 24.38, 24.75, 25.03, 25.31, 25.5, 25.88, 26.25, 27.38, 27.75, 28.12, 28.5, 28.78, 29.06, 29.44, 29.62, 30, 30.75, 31.03, 31.31, 31.5, 31.78, 32.06, 32.44, 32.62, 32.81, 33, 33.75, 34.12, 34.5, 34.88, 35.25, 35.62, 36, 36.38, 36.75, 37.03, 37.31, 37.5, 37.88, 38.25, 39.38, 39.75, 40.12, 40.5, 40.78, 41.06, 41.44, 41.62, 42, 42.75, 43.03, 43.31, 43.5, 43.78, 44.06, 44.44, 44.62, 44.81, 45, 45.75, 46.12, 46.5, 46.88, 47.25, 47.62, 48, 48.75, 49.12, 49.5, 50.25, 50.53, 50.81, 51.75, 52.03, 52.31, 53.06, 53.62, 54, 55.12, 55.5, 55.88, 56.25, 56.62, 56.91, 57.94, 58.12, 58.31, 59.25, 59.62, 60, 60.75, 61.12, 61.5, 62.25, 62.53, 62.81, 63.75, 64.03, 64.31, 65.06, 65.62, 66, 67.12, 67.5, 67.88, 68.25, 68.62, 69, 70.5, 71.25, 144, 144.38, 144.75, 145.03, 145.31, 145.5, 145.88, 146.25, 147.38, 147.75, 148.12, 148.5, 148.78, 149.06, 149.44, 149.62, 150, 150.75, 151.03, 151.31, 151.5, 151.78, 152.06, 152.44, 152.62, 152.81, 153, 153.75, 154.12, 154.5, 154.88, 155.25, 155.62, 156, 156.38, 156.75, 157.03, 157.31, 157.5, 157.88, 158.25, 159.38, 159.75, 160.12, 160.5, 160.78, 161.06, 161.44, 161.62, 162, 162.75, 163.03, 163.31, 163.5, 163.78, 164.06, 164.44, 164.62, 164.81, 165, 165.75, 166.12, 166.5, 166.88, 167.25, 167.62, 168, 168.75, 169.12, 169.5, 170.25, 170.53, 170.81, 171.75, 172.03, 172.31, 173.06, 173.62, 174, 175.12, 175.5, 175.88, 176.25, 176.62, 176.91, 177.94, 178.12, 178.31, 179.25, 179.62, 180, 180.75, 181.12, 181.5, 182.25, 182.53, 182.81, 183.75, 184.03, 184.31, 185.06, 185.62, 186, 187.12, 187.5, 187.88, 188.25, 188.62, 189, 190.5, 191.25], ne: [24.09, 24.47, 25.03, 25.31, 25.5, 25.88, 25.97, 27, 27.75, 28.12, 28.5, 28.69, 28.88, 29.44, 29.62, 30, 30.75, 31.03, 31.31, 31.5, 31.78, 31.88, 32.44, 32.62, 32.81, 33, 33.75, 34.12, 34.5, 34.88, 35.25, 35.62, 36, 36.09, 36.47, 37.03, 37.31, 37.5, 37.88, 37.97, 39, 39.75, 40.12, 40.5, 40.69, 40.88, 41.44, 41.62, 42, 42.75, 43.03, 43.31, 43.5, 43.78, 43.88, 44.44, 44.62, 44.81, 45, 45.75, 46.12, 46.5, 46.88, 47.25, 47.62, 48, 48.75, 49.12, 49.5, 50.25, 50.44, 50.72, 51.38, 51.94, 52.22, 52.88, 53.62, 54, 54.75, 55.5, 55.88, 56.25, 56.62, 56.91, 57.75, 58.12, 58.31, 59.25, 59.62, 60, 60.75, 61.12, 61.5, 62.25, 62.44, 62.72, 63.38, 63.94, 64.22, 64.88, 65.62, 66, 66.75, 67.5, 67.88, 68.25, 68.62, 69, 70.5, 71.25, 72, 144.09, 144.47, 145.03, 145.31, 145.5, 145.88, 145.97, 147, 147.75, 148.12, 148.5, 148.69, 148.88, 149.44, 149.62, 150, 150.75, 151.03, 151.31, 151.5, 151.78, 151.88, 152.44, 152.62, 152.81, 153, 153.75, 154.12, 154.5, 154.88, 155.25, 155.62, 156, 156.09, 156.47, 157.03, 157.31, 157.5, 157.88, 157.97, 159, 159.75, 160.12, 160.5, 160.69, 160.88, 161.44, 161.62, 162, 162.75, 163.03, 163.31, 163.5, 163.78, 163.88, 164.44, 164.62, 164.81, 165, 165.75, 166.12, 166.5, 166.88, 167.25, 167.62, 168, 168.75, 169.12, 169.5, 170.25, 170.44, 170.72, 171.38, 171.94, 172.22, 172.88, 173.62, 174, 174.75, 175.5, 175.88, 176.25, 176.62, 176.91, 177.75, 178.12, 178.31, 179.25, 179.62, 180, 180.75, 181.12, 181.5, 182.25, 182.44, 182.72, 183.38, 183.94, 184.22, 184.88, 185.62, 186, 186.75, 187.5, 187.88, 188.25, 188.62, 189, 190.5, 191.25, 192],
          bt: [48.19, 48.56, 48.94, 49.31, 49.67, 50.04, 50.42, 50.79, 51.17, 51.54, 51.92, 52.29, 52.67, 53.04, 53.42, 53.79, 54.17, 54.54, 54.92, 55.29, 55.67, 56.04, 56.42, 56.79, 57.17, 57.54, 57.92, 58.29, 58.5, 58.78, 59.25, 59.53, 60.17, 60.54, 60.92, 61.29, 61.67, 62.04, 62.42, 62.79, 63.17, 63.54, 63.92, 64.29, 64.67, 65.04, 65.42, 65.79, 66.17, 66.54, 66.92, 67.29, 67.67, 68.04, 68.42, 68.79, 69, 69.09, 69.19, 69.28, 69.38, 69.47, 69.56, 69.66, 69.75, 69.84, 69.94, 70.03, 70.12, 70.22, 70.31, 70.41, 70.5, 71.25, 168.19, 168.56, 168.94, 169.31, 169.67, 170.04, 170.42, 170.79, 171.17, 171.54, 171.92, 172.29, 172.67, 173.04, 173.42, 173.79, 174.17, 174.54, 174.92, 175.29, 175.67, 176.04, 176.42, 176.79, 177.17, 177.54, 177.92, 178.29, 178.5, 178.78, 179.25, 179.53, 180.17, 180.54, 180.92, 181.29, 181.67, 182.04, 182.42, 182.79, 183.17, 183.54, 183.92, 184.29, 184.67, 185.04, 185.42, 185.79, 186.17, 186.54, 186.92, 187.29, 187.67, 188.04, 188.42, 188.79, 189, 189.09, 189.19, 189.28, 189.38, 189.47, 189.56, 189.66, 189.75, 189.84, 189.94, 190.03, 190.12, 190.22, 190.31, 190.41, 190.5] },
        { file: "ch3_karaoke_full.ogg", len: 174.26, bpm: 230, flowery: false,
          lt: [0, 15.92, 18.26, 20.87, 24.4, 26.6, 29.34, 33.26, 33.53, 37.66, 100.16, 102.77, 104.86, 108.51, 111.13, 113.08, 115.69, 116.95, 119.46, 121.42, 125.3, 127.82, 129.76, 132.34, 133.81, 149.48, 151.73, 154.42, 157.95, 160.08, 162.8, 166.95, 172], ly: ["", "WHEN THE DE-MON HEART IS CRY-ING", "AND THE BLOOD IS GUSH-ING BRIGHT", "RAISE UP YOUR BAT FOR THE BURN-ING FIGHT", "WHEN YOUR HOPE IS SLOW-LY DY-ING", "AND YOUR FU-TURE'S LOST ITS RIGHTS", "RAISE UP YOUR BAT AND FACE THE FRIGHT", "", "LET'S KNOCK EM DEAD IN-TO THE NIGHT", "", "Come fol-low me in-to the dark", "With your heart as the ark", "Which shall shine you the way", "Be-cause I'm with you in the dark", "With your heart as my mark", "Which shall guide you the way,", "through the waves", "Come fol-low me in-to the dark", "With your heart as the ark", "Which shall shine you the way", "Be-cause I'm with you in the dark", "With your heart as my mark", "Which shall guide you the way,", "through the waves", "", "WHEN THE DE-MON HEART IS CRY-ING", "AND THE BLOOD IS GUSH-ING BRIGHT", "RAISE UP YOUR BAT FOR THE BURN-ING FIGHT", "WHEN YOUR HOPE IS SLOW-LY DY-ING", "AND YOUR FU-TURE'S LOST ITS RIGHTS", "RAISE UP YOUR BAT AND FACE THE FRIGHT", "LET'S KNOCK EM DEAD IN-TO THE NIGHT", ""],
          nt: [15.92, 16.194, 16.468, 16.741, 17.015, 17.289, 17.563, 17.836, 18.26, 18.611, 18.963, 19.314, 19.666, 20.017, 20.369, 20.87, 21.246, 21.621, 21.997, 22.372, 22.748, 23.123, 23.499, 23.874, 24.4, 24.656, 24.913, 25.169, 25.425, 25.681, 25.938, 26.194, 26.6, 26.97, 27.34, 27.71, 28.08, 28.45, 28.82, 29.34, 29.76, 30.18, 30.6, 31.02, 31.44, 31.86, 32.28, 33.53, 33.95, 34.37, 34.79, 35.21, 35.63, 36.05, 36.47, 100.16, 100.468, 100.775, 101.082, 101.39, 101.697, 102.005, 102.312, 102.77, 103.093, 103.417, 103.74, 104.063, 104.387, 104.86, 105.28, 105.7, 106.12, 106.54, 106.96, 108.51, 108.819, 109.127, 109.436, 109.745, 110.054, 110.362, 110.671, 111.13, 111.43, 111.73, 112.03, 112.33, 112.63, 113.08, 113.49, 113.9, 114.31, 114.72, 115.13, 115.69, 116.06, 116.43, 116.95, 117.245, 117.54, 117.835, 118.13, 118.425, 118.72, 119.015, 119.46, 119.762, 120.063, 120.365, 120.667, 120.968, 121.42, 121.84, 122.26, 122.68, 123.1, 123.52, 125.3, 125.596, 125.892, 126.189, 126.485, 126.781, 127.077, 127.374, 127.82, 128.118, 128.417, 128.715, 129.013, 129.312, 129.76, 130.165, 130.57, 130.975, 131.38, 131.785, 132.34, 132.76, 133.18, 149.48, 149.742, 150.005, 150.267, 150.53, 150.792, 151.055, 151.317, 151.73, 152.093, 152.456, 152.819, 153.181, 153.544, 153.907, 154.42, 154.796, 155.171, 155.547, 155.922, 156.298, 156.673, 157.049, 157.424, 157.95, 158.197, 158.445, 158.692, 158.94, 159.188, 159.435, 159.683, 160.08, 160.447, 160.814, 161.181, 161.549, 161.916, 162.283, 162.8, 163.22, 163.64, 164.06, 164.48, 164.9, 165.32, 165.74, 166.95, 167.37, 167.79, 168.21, 168.63, 169.05, 169.47, 169.89], ne: [16.174, 16.448, 16.721, 16.995, 17.269, 17.543, 17.816, 18.09, 18.591, 18.943, 19.294, 19.646, 19.997, 20.349, 20.7, 21.226, 21.601, 21.977, 22.352, 22.728, 23.103, 23.479, 23.854, 24.23, 24.636, 24.893, 25.149, 25.405, 25.661, 25.918, 26.174, 26.43, 26.95, 27.32, 27.69, 28.06, 28.43, 28.8, 29.17, 29.74, 30.16, 30.58, 31.0, 31.42, 31.84, 32.26, 32.68, 33.93, 34.35, 34.77, 35.19, 35.61, 36.03, 36.45, 36.87, 100.448, 100.755, 101.062, 101.37, 101.677, 101.985, 102.292, 102.6, 103.073, 103.397, 103.72, 104.043, 104.367, 104.69, 105.26, 105.68, 106.1, 106.52, 106.94, 107.36, 108.799, 109.108, 109.416, 109.725, 110.034, 110.343, 110.651, 110.96, 111.41, 111.71, 112.01, 112.31, 112.61, 112.91, 113.47, 113.88, 114.29, 114.7, 115.11, 115.52, 116.04, 116.41, 116.78, 117.225, 117.52, 117.815, 118.11, 118.405, 118.7, 118.995, 119.29, 119.742, 120.043, 120.345, 120.647, 120.948, 121.25, 121.82, 122.24, 122.66, 123.08, 123.5, 123.92, 125.576, 125.873, 126.169, 126.465, 126.761, 127.057, 127.354, 127.65, 128.098, 128.397, 128.695, 128.993, 129.292, 129.59, 130.145, 130.55, 130.955, 131.36, 131.765, 132.17, 132.74, 133.16, 133.58, 149.722, 149.985, 150.247, 150.51, 150.772, 151.035, 151.297, 151.56, 152.073, 152.436, 152.799, 153.161, 153.524, 153.887, 154.25, 154.776, 155.151, 155.527, 155.902, 156.278, 156.653, 157.029, 157.404, 157.78, 158.177, 158.425, 158.672, 158.92, 159.167, 159.415, 159.662, 159.91, 160.427, 160.794, 161.161, 161.529, 161.896, 162.263, 162.63, 163.2, 163.62, 164.04, 164.46, 164.88, 165.3, 165.72, 166.14, 167.35, 167.77, 168.19, 168.61, 169.03, 169.45, 169.87, 170.29], bt: [] }
    ];
}

// ===== Build 50: SONG LYRICS in the fight (the games' own lyric system) =====
// When the fight's song is Flower Man (Flowerman_Arrangement.ogg) or Raise Up Your Bat (ch3_karaoke_full.ogg, Chapter 3's own
// karaoke track), its lyrics run with the song: online in the strip at the bottom of the screen (under the TARGETING row),
// offline at the top, under the hub's lines. It is Chapter 5's obj_flowery_lyrics, line for line: the same monospace lyric
// font and syllable sweep (scr_draw_text_monospace, which Chapter 3 has too), the line lit syllable by syllable on the song's
// own notes - Flower Man yellow turning green with its glow on the choruses and the beat, Raise Up Your Bat white turning blue
// like Tenna's karaoke. It follows the song's real position (audio_sound_get_track_position), so a loop starts it over.
// State lives on the hub's controller (scr_draw_text_monospace writes lyric_start / lyric_end on the instance that draws).

function knight_lyr_song_now()
{
    if (!knight_active() || !is_struct(global.krun) || global.krun.state != "battle")
        return undefined;
    var _f = global.knight_songs[knight_song_eff()].file;
    // (Flowery's last stand puts Flower Man on in place of the fight's song)
    if (variable_global_exists("knight_fl_song") && global.knight_fl_song != "")
        _f = global.knight_fl_song;
    if (_f == "" || !knight_music_exists(_f))
        return undefined;
    // (a KF Song Pack song: its timed lines, in this same lyric style)
    if (knight_kf_id(_f) != "")
        return knight_lyr_kf();
    var _l = knight_lyr_songs();
    for (var _i = 0; _i < array_length(_l); _i++)
    {
        if (_l[_i].file == _f)
            return _l[_i];
    }
    return undefined;
}

function knight_lyr_reset(_S)
{
    klx_song = _S;
    klx_index = 0;
    klx_start_index = 0;
    klx_cur = "";
    klx_timed = "";
    klx_update = true;
    klx_track = 0;
    klx_last = 0;
    klx_beat = 0;
    klx_beat_i = 0;
    klx_strength = 0;
    klx_alpha = 0;
    lyric_start = [0];
    lyric_end = [0];
    return 1;
}

function knight_lyr_strip(_s)
{
    _s = string_replace_all(_s, "-", "");
    _s = string_replace_all(_s, "<", "");
    _s = string_replace_all(_s, ">", "");
    _s = string_replace_all(_s, "+", "");
    return _s;
}

// every step (the hub controller's Step)
global.knight_lyr_on = false;
function knight_lyr_step()
{
    var _S = knight_lyr_song_now();
    global.knight_lyr_on = !is_undefined(_S) || (variable_instance_exists(id, "klx_alpha") && klx_alpha > 0);
    if (!variable_instance_exists(id, "klx_song"))
        knight_lyr_reset(undefined);
    if (is_undefined(_S))
    {
        klx_alpha = max(0, klx_alpha - 0.1);
        if (klx_alpha <= 0 && !is_undefined(klx_song))
            knight_lyr_reset(undefined);
        return 0;
    }
    if (is_undefined(klx_song) || klx_song.file != _S.file)
        knight_lyr_reset(_S);
    var _snd = (variable_global_exists("batmusic") && is_array(global.batmusic) && array_length(global.batmusic) > 1) ? global.batmusic[1] : -1;
    var _pos = (is_numeric(_snd) && _snd >= 0 && audio_exists(_snd) && audio_is_playing(_snd)) ? audio_sound_get_track_position(_snd) : -1;
    // (a KF Song Pack song: the pack's own clock - its instrumental's position)
    if (variable_struct_exists(_S, "kf") && _S.kf)
        _pos = (is_struct(global.kf_song) && kf_song_is_playing(global.kf_song) && !global.kf_song.paused) ? kf_song_time(global.kf_song) : -1;
    if (_pos < 0)
    {
        // no song playing (paused, between songs): the lyrics fade
        klx_alpha = max(0, klx_alpha - 0.1);
        return 0;
    }
    klx_alpha = min(1, klx_alpha + 0.1);
    klx_track = _pos;
    var _lt = _S.lt;
    var _n = array_length(_lt);
    // the song looped (or jumped back): from the top
    if (klx_track < klx_last)
    {
        klx_index = 0;
        klx_start_index = 0;
        klx_beat_i = 0;
        klx_cur = "";
        klx_timed = "";
        klx_update = true;
    }
    klx_last = klx_track;
    // the beat (Flower Man's own beat list pulses the glow)
    var _bt = _S.bt;
    if (klx_beat_i < array_length(_bt) && klx_track > _bt[klx_beat_i])
    {
        klx_beat = 1;
        klx_beat_i++;
    }
    else if (klx_beat > 0)
        klx_beat = clamp(klx_beat - (delta_time / 1000000 / (60 / _S.bpm)), 0, 1);
    // the line now (each line's time a touch early, as obj_flowery_lyrics adds them)
    if ((klx_index + 1) < _n && klx_track >= (_lt[klx_index + 1] - 0.02))
    {
        klx_index++;
        while ((klx_index + 1) < _n && klx_track >= (_lt[klx_index + 1] - 0.02))
            klx_index++;
        klx_timed = _S.ly[klx_index];
        klx_cur = knight_lyr_strip(klx_timed);
        klx_update = true;
    }
    return 1;
}

// the hub HUD's draw (the camera's corner _xx, _yy): where the lyrics go and drawing them
function knight_lyr_draw(_xx, _yy, _cy)
{
    if (!variable_instance_exists(id, "klx_song") || is_undefined(klx_song) || klx_alpha <= 0)
        return 0;
    var _S = klx_song;
    if (!variable_instance_exists(id, "klx_surf") || !is_array(klx_surf))
        klx_surf = [-1, -1, -1];
    var _refresh = false;
    if (klx_surf[0] == -1 || !surface_exists(klx_surf[0]) || !surface_exists(klx_surf[1]))
    {
        if (klx_surf[0] != -1 && surface_exists(klx_surf[0]))
            surface_free(klx_surf[0]);
        if (klx_surf[1] != -1 && surface_exists(klx_surf[1]))
            surface_free(klx_surf[1]);
        klx_surf[0] = surface_create(640, 100);
        klx_surf[1] = surface_create(640, 100);
        _refresh = true;
    }
    if (klx_surf[2] == -1 || !surface_exists(klx_surf[2]))
        klx_surf[2] = surface_create(640, 100);
    var _x = _xx + 320;
    var _y = _cy;
    // build 52: the online feed reads this to step out of the lyrics' way
    global.klx_vis_ms = current_time;
    if (klx_cur != "")
    {
        var _len = string_length(klx_cur);
        var _len2 = 0;
        if (string_pos("#", klx_cur) > 0)
        {
            _len = string_pos("#", klx_cur) - 1;
            _len2 = string_length(klx_cur) - (_len + 1);
        }
        var _nt = _S.nt;
        var _ne = _S.ne;
        var _maxnote = array_length(_nt);
        draw_set_halign(fa_center);
        draw_set_valign(fa_middle);
        draw_set_font(scr_84_get_font("main"));
        var _hspace = (global.lang == "ja") ? 16 : 8;
        if (klx_update || _refresh)
        {
            if (klx_update)
            {
                var _t0 = max(0, _S.lt[klx_index] - 0.02);
                for (var _i = klx_start_index; _i < _maxnote; _i++)
                {
                    if ((_t0 + 0.03) < _ne[_i])
                    {
                        klx_start_index = _i;
                        break;
                    }
                }
            }
            // the timing pass fills lyric_start / lyric_end: where each syllable starts and ends on the line
            scr_draw_text_monospace(320, 50, klx_timed, _hspace, 18, _len, true, 2, 2, _len2);
            surface_set_target(klx_surf[0]);
            draw_clear_alpha(c_black, 0);
            draw_set_alpha(1);
            draw_set_color(c_white);
            scr_draw_text_monospace(320, 50, klx_cur, _hspace, 18, _len, false, 2, 2, _len2);
            surface_reset_target();
            surface_set_target(klx_surf[1]);
            draw_clear_alpha(c_black, 0);
            draw_set_color(c_white);
            scr_draw_text_monospace(320, 50, klx_timed, _hspace, 18, _len, false, 2, 2, _len2);
            surface_reset_target();
            klx_update = false;
        }
        var _max = array_length(lyric_end);
        if (_max == 0 || array_length(lyric_start) == 0)
            return 0;
        var _note = max(0, _max - 1);
        var _lerp = 1;
        for (var _i = 0; _i < _max; _i++)
        {
            var _ix = _i + klx_start_index;
            if (_ix >= _maxnote)
                break;
            if (klx_track < _ne[_ix])
            {
                _note = clamp(_i, 0, _max - 1);
                _lerp = clamp((klx_track - _nt[_ix]) / max(0.001, _ne[_ix] - _nt[_ix]), 0, 1);
                break;
            }
        }
        _note = clamp(_note, 0, min(array_length(lyric_start), _max) - 1);
        var _prog = lerp(lyric_start[_note], lyric_end[_note], _lerp);
        if (_note == 0 && klx_start_index < _maxnote && klx_track < _nt[klx_start_index])
            _prog = 0;
        _prog = round(_prog / 2) * 2;
        // the line: its outline, the part still to sing, then the sung part over it
        surface_set_target(klx_surf[2]);
        draw_clear_alpha(c_black, 0);
        var _base = _S.flowery ? c_yellow : c_white;
        var _sung = _S.flowery ? c_green : c_blue;
        var _out = _S.flowery ? c_white : c_black;
        draw_surface_ext(klx_surf[0], -2, 0, 1, 1, 0, c_black, 1);
        draw_surface_ext(klx_surf[0], 2, 0, 1, 1, 0, c_black, 1);
        draw_surface_ext(klx_surf[0], 0, -2, 1, 1, 0, c_black, 1);
        draw_surface_ext(klx_surf[0], 0, 2, 1, 1, 0, c_black, 1);
        draw_surface_ext(klx_surf[0], 0, 0, 1, 1, 0, _base, 1);
        var _glow = 0;
        if (_S.flowery && (klx_index == 18 || klx_index == 37))
        {
            _glow = clamp(klx_track - ((klx_index == 37) ? 191 : 71), 0, 1);
            _sung = merge_color(c_green, c_white, _glow);
        }
        if (_prog > 0)
        {
            draw_surface_part_ext(klx_surf[1], 0, 2, max(1, _prog - 2), 100, 2, 2, 1, 1, _out, 1);
            draw_surface_part_ext(klx_surf[1], 0, 2, _prog + 2, 100, -2, 2, 1, 1, _out, 1);
            draw_surface_part_ext(klx_surf[1], 0, 2, _prog, 100, 0, 0, 1, 1, _out, 1);
            draw_surface_part_ext(klx_surf[1], 0, 2, _prog, 100, 0, 4, 1, 1, _out, 1);
            draw_surface_part_ext(klx_surf[1], 0, 2, _prog, 100, 0, 2, 1, 1, _sung, 1);
        }
        surface_reset_target();
        draw_set_halign(fa_left);
        draw_set_valign(fa_top);
        // Flower Man's choruses glow (its own sections: 46 - 120 s and from 166 s) and pulse on the beat
        if (_S.flowery && ((klx_track >= 46 && klx_track < 120) || klx_track >= 166))
            klx_strength = min(1, klx_strength + 0.015);
        else
            klx_strength = 0;
        var _a = klx_alpha * lerp(0.6, 1, klx_strength);
        if (!_S.flowery)
            _a = klx_alpha;
        draw_surface_ext(klx_surf[2], _x - 320, _y - 50, 1, 1, 0, c_white, _a);
        if (klx_strength > 0)
        {
            gpu_set_blendmode(bm_add);
            for (var _i = 0; _i < 8; _i++)
            {
                var _p = (_i + 1) / 8;
                var _sc = 1 + ((klx_strength * _p) / 2) + (klx_beat / 10);
                draw_surface_ext(klx_surf[2], _x - (320 * _sc), _y - (50 * _sc), _sc, _sc, 0, c_white, ((0.2 * klx_strength * (1 - _p)) + (_glow / 5)) * _a);
            }
            gpu_set_blendmode(bm_normal);
        }
    }
    draw_set_color(c_white);
    draw_set_alpha(1);
    return 1;
}

// where the lyrics sit: online the strip under the TARGETING row (the bottom of the screen), offline under the hub's lines
function knight_lyr_hud(_xx, _yy, _nlines)
{
    if (!variable_global_exists("knight_lyr_on") || !global.knight_lyr_on)
        return 0;
    if (!variable_instance_exists(id, "klx_song"))
        return 0;
    // build 52: online, just above the TARGETING strip (the party panel is at the very bottom now); the feed moves up for them
    var _cy = kfo_cfg_online(global.krun.cfg) ? (_yy + 384) : (_yy + 30 + (16 * _nlines));
    return knight_lyr_draw(_xx, _yy, _cy);
}


// build 50: a KF Song Pack song's lyrics in the hub's own lyric style (Raise Up Your Bat's: white, sung part blue, black
// outline - no band behind them): its timed lines (kfsongs/<id>/lyrics.json, as kf_song_load read them) made into the
// same table as the songs above - a gap line wherever the song pauses between lines, each word one note, the notes of a
// line spread over its time by their length. Made once per song (global.knight_kf_lyr).
global.knight_kf_lyr = undefined;
function knight_lyr_kf()
{
    if (!is_struct(global.kf_song) || !is_array(global.kf_song.lines) || array_length(global.kf_song.lines) == 0)
        return undefined;
    var _id = global.kf_song.song_id;
    if (is_struct(global.knight_kf_lyr) && global.knight_kf_lyr.file == ("@kf:" + _id))
        return global.knight_kf_lyr;
    var _L = global.kf_song.lines;
    var _lt = [0];
    var _ly = [""];
    var _nt = [];
    var _ne = [];
    for (var _i = 0; _i < array_length(_L); _i++)
    {
        var _t0 = _L[_i].t0;
        var _t1 = _L[_i].t1;
        // (the lyric script's own codes taken out: < > + ~ [ ] #)
        var _tx = _L[_i].text;
        var _bad = "<>+~[]#";
        for (var _b = 1; _b <= string_length(_bad); _b++)
            _tx = string_replace_all(_tx, string_char_at(_bad, _b), "");
        array_push(_lt, _t0);
        array_push(_ly, _tx);
        // its notes: one per word (a "-" splits a word too, as in the game's lyric lines)
        var _w = [];
        var _cur = "";
        for (var _c = 1; _c <= string_length(_tx) + 1; _c++)
        {
            var _ch = (_c <= string_length(_tx)) ? string_char_at(_tx, _c) : " ";
            if (_ch == " " || _ch == "-")
            {
                if (_cur != "")
                    array_push(_w, string_length(_cur));
                _cur = "";
            }
            else
                _cur += _ch;
        }
        var _tot = 0;
        for (var _j = 0; _j < array_length(_w); _j++)
            _tot += _w[_j];
        var _len = max(0.2, (_t1 - _t0) - 0.15);
        var _t = _t0;
        for (var _j = 0; _j < array_length(_w); _j++)
        {
            var _d = _len * (_w[_j] / max(1, _tot));
            array_push(_nt, _t);
            array_push(_ne, _t + _d);
            _t += _d;
        }
        // a pause before the next line: the line goes away when it is sung
        var _next = (_i + 1 < array_length(_L)) ? _L[_i + 1].t0 : (_t1 + 1);
        if (_next - _t1 > 0.6)
        {
            array_push(_lt, _t1 + 0.3);
            array_push(_ly, "");
        }
    }
    global.knight_kf_lyr = { file: "@kf:" + _id, len: global.kf_song.meta.length, bpm: 120, flowery: false, kf: true, lt: _lt, ly: _ly, nt: _nt, ne: _ne, bt: [] };
    return global.knight_kf_lyr;
}
