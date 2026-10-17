if (song != undefined) kf_song_stop(song);
if (global.kf_song == song) global.kf_song = undefined;
global.kf_lyrics_shake = 0;
