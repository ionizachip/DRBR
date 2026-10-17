// obj_kf_songlyrics  -  plays a kfsongs/ song and draws Nullscape-styled lyrics
// Song: "IT DOESN'T END HERE" by DIGITAL DESCENDANT (Nullscape Vol. 3).
// All rights to the song, recording and lyrics belong to DIGITAL DESCENDANT.
// Start it with kf_song_start("it_doesnt_end_here"), stop it with kf_song_end().

var _cfg = kf_song_settings();
var _req = global.kf_song_request;
global.kf_song_request = undefined;

song_id = is_struct(_req) ? _req.song_id : "it_doesnt_end_here";
vocals  = is_struct(_req) ? _req.vocals  : _cfg.vocals;

song = kf_song_load(song_id);
global.kf_song = song;
if (song != undefined) kf_song_set_volume(song, _cfg.volume);

started = false;
show_lyrics = _cfg.lyrics;
show_credit = _cfg.credit;
destroy_when_done = true;

lyric_y   = 34;    // top of the lyric line, in 640x480 GUI units
credit_time = 7;   // seconds the NOW PLAYING card stays up
font_lyric = asset_get_index("fnt_main");

// current line
cur_line  = -1;
cur_lay   = undefined;
cur_style = "null";
cur_start = 0;
cur_exit  = -1;    // -1 = not exiting, otherwise 0..1

// previous line (fading out underneath)
old_lay   = undefined;
old_style = "null";
old_start = 0;
old_exit  = 1;

banner_text = "";
banner_t    = 99;
flash       = 0;
flash_col   = c_white;
