"""Build 50: the KF Song Pack ("IT DOESN'T END HERE" by DIGITAL DESCENDANT) in the hub's FIGHT SONG list. With the pack's
kfsongs folder next to data.win the song is in the list (and RANDOM), the fight's battle music is a silent stand-in and
kf_song_start plays the pack's song (instrumental + vocals, its lyrics, its credit) while the stand-in plays; it waits when the
fight cuts its music, goes on when it plays again, starts over at its end, ends with the fight. Without the folder the song
shows NOT FOUND and the knight's own music plays. Usage: python3 t_kfsong50.py"""
import sys, os, time, json, shutil
os.environ.setdefault('WALL', '200')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from emu_atk import *
FAILS = []
N = [0]
PACK = '/home/claude/work/deliver/kfsongs/it_doesnt_end_here/'


def ok(c, msg):
    N[0] += 1
    print(('ok   ' if c else 'FAIL ') + msg, flush=True)
    if not c:
        FAILS.append(msg)


def run(key):
    sim = mk(key, [1, 2, 4])
    for _m in ('scr_84_get_sprite', 'scr_84_get_font'):
        sim.mock(_m, 0)
    sim.run('for (var _i = array_length(global.flag); _i < 10000; _i++) global.flag[_i] = 0; global.flag[16] = 0.8; global.launcher = false;')
    for o in ('obj_kf_songlyrics', 'obj_astream'):
        try:
            sim.define_object(o)
        except Exception:
            pass
    M_ = os.environ.get('KH_MERGED', '/home/claude/work/build/merged/')
    for ev in ('Create_0', 'Step_0', 'CleanUp_0', 'Draw_64'):
        sim.load_file(M_ + 'gml_Object_obj_kf_songlyrics_%s.gml' % ev, entry='gml_Object_obj_kf_songlyrics_%s' % ev)
    for ev in ('Create_0',):
        try:
            sim.load_file(M_ + 'gml_Object_obj_astream_%s.gml' % ev, entry='gml_Object_obj_astream_%s' % ev)
        except Exception:
            pass
    # audio: streams / instances with ids, a set of playing instances, the calls recorded
    A = {'next': 100, 'playing': set(), 'pos': 0.0, 'gain': [], 'streams': [], 'plays': [], 'paused': set()}
    def cs(sm, p):
        A['next'] += 1
        A['streams'].append((A['next'], str(p)))
        return A['next']
    def play(sm, s, *a):
        A['next'] += 1
        A['playing'].add(A['next'])
        A['plays'].append((A['next'], s))
        return A['next']
    sim.mock('audio_create_stream', cs)
    sim.mock('audio_play_sound', play)
    sim.mock('audio_is_playing', lambda sm, i: i in A['playing'])
    sim.mock('audio_exists', lambda sm, i: True)
    sim.mock('audio_sound_gain', lambda sm, i, g, t: A['gain'].append((i, g)))
    sim.mock('audio_sound_get_track_position', lambda sm, i: A['pos'])
    sim.mock('audio_pause_sound', lambda sm, i: A['paused'].add(i))
    sim.mock('audio_resume_sound', lambda sm, i: A['paused'].discard(i))
    sim.mock('audio_stop_sound', lambda sm, i: A['playing'].discard(i))
    sim.mock('audio_destroy_stream', 0)
    sim.mock('audio_sound_set_track_position', 0)
    sim.mock('display_get_gui_width', 640)
    sim.mock('display_get_gui_height', 480)
    sim.mock('delta_time', 33333) if False else None
    D = []
    def dt(sm, x, y, s, *a):
        D.append(str(s))
    sim.mock('draw_text_transformed_color', dt)
    sim.mock('draw_text_transformed', dt)
    sim._snapauto = True
    res = {}
    ok_, err = auto(sim, lambda: sim.run('global.knight_run = 1; var _c = knight_cfg_default(); _c.party = [1,2,4];'
                                         'global.krun = knight_run_new({src: _c, cfg: _c, plan: [knight_find_key("%s")], reveal: ""}); global.krun.state = "arena";'
                                         'global.batmusic = [-1, -1];' % key))
    if not ok_:
        return ('run', err)
    n = sim.eval('knight_song_find_exact("@kf:it_doesnt_end_here")') + 1
    res['entry'] = [sim.eval('global.knight_songs[%d].name' % (n - 1)), sim.eval('global.knight_songs[%d].file' % (n - 1)), sim.eval('global.knight_songs[%d].by' % (n - 1)), sim.eval('global.knight_songs[%d].by' % (n - 2))]
    # no kfsongs folder: NOT FOUND, the knight's own song, no pack song asked for
    ok_, err = auto(sim, lambda: sim.run('global.krun.cfg.song = %d; global.F0 = knight_song_file("knight.ogg"); global.E0 = [knight_music_exists("@kf:it_doesnt_end_here"), is_undefined(global.knight_kf)];' % (n - 1)))
    if not ok_:
        return ('nofolder', err)
    res['nofolder'] = [sim.eval('global.F0'), sim.py(sim.eval('global.E0'))]
    # the pack's folder next to data.win (the oggs as small stand-ins)
    d = os.path.join(sim.fs.root, 'kfsongs', 'it_doesnt_end_here')
    os.makedirs(d, exist_ok=True)
    for f in ('song.json', 'lyrics.json'):
        shutil.copy(PACK + f, d)
    for f in ('inst.ogg', 'vocals.ogg'):
        open(os.path.join(d, f), 'wb').write(b'OggS')
    # (1.0.1: the game looks again at most every 3 seconds - knight_cache_get; here the files are new at once)
    ok_, err = auto(sim, lambda: sim.run('knight_music_cache_clear(); global.E1 = [knight_music_exists("@kf:it_doesnt_end_here"), knight_kf_inst("it_doesnt_end_here"), knight_song_credit()];'))
    if not ok_:
        return ('folder', err)
    res['folder'] = sim.py(sim.eval('global.E1'))
    # the fight starts its music: snd_init(knight_song_file(...)) - the stand-in; the battle starts it (mus_loop)
    A['streams'].clear()
    ok_, err = auto(sim, lambda: sim.run('global.batmusic[1] = 7; global.batmusic[0] = snd_init(knight_song_file("knight.ogg")); global.krun.state = "battle"; knight_kf_tick();'))
    if not ok_:
        return ('standin', err)
    res['req'] = [sim.eval('global.knight_kf.stream') == sim.eval('global.batmusic[0]'), sim.eval('global.knight_kf.started'), sim.eval('instance_number(obj_kf_songlyrics)'), A['streams'][-1][1].endswith('mus/knight.ogg')]
    g0 = list(A['gain'])
    ok_, err = auto(sim, lambda: sim.run('global.batmusic[1] = mus_loop(global.batmusic[0]); knight_kf_tick(); with (obj_kf_songlyrics) event_perform(ev_step, ev_step_normal);'))
    if not ok_:
        return ('start', err)
    bm1 = sim.eval('global.batmusic[1]')
    res['start'] = [sim.eval('global.knight_kf.started'), sim.eval('instance_number(obj_kf_songlyrics)'), sim.eval('is_struct(global.kf_song) ? array_length(global.kf_song.lines) : -1'),
                    sim.eval('is_struct(global.kf_song) ? global.kf_song.playing : -1'), (bm1, 0) in A['gain'], sim.eval('global.kf_song.volume'),
                    [os.path.basename(p) for _, p in A['streams'][-2:]], sim.eval('global.kf_song.meta.artist')]
    # its credit (NOW PLAYING card, the MUSIC tag) drawn - under the hub's lines
    A['pos'] = 2.0
    D.clear()
    ok_, err = auto(sim, lambda: sim.run('knight_kf_tick(); with (obj_kf_songlyrics) { event_perform(ev_step, ev_step_normal); event_perform(ev_draw, ev_gui); }'))
    if not ok_:
        return ('draw', err)
    res['credit'] = ['NOW PLAYING' not in D, not any(x.startswith('MUSIC:') for x in D), sim.eval('obj_kf_songlyrics.show_credit') in (False, 0),
                     sim.eval('knight_song_credit()'), sim.eval('obj_kf_songlyrics.lyric_y')]
    # 0:46: the first line is sung, drawn glyph by glyph (power style)
    A['pos'] = 46.0
    D.clear()
    ok_, err = auto(sim, lambda: sim.run('knight_kf_tick(); with (obj_kf_songlyrics) { event_perform(ev_step, ev_step_normal); event_perform(ev_draw, ev_gui); }'
                                         'global.L = [kf_song_line_index(global.kf_song), kf_song_line_style(global.kf_song, 0), kf_song_section(global.kf_song)];'))
    if not ok_:
        return ('lyric', err)
    res['lyric'] = [sim.py(sim.eval('global.L')), len(D) == 0, sim.eval('obj_kf_songlyrics.show_lyrics') in (False, 0)]
    # the hub's own lyric system (Raise Up Your Bat's look) shows the line, on the pack's clock
    ok_, err = auto(sim, lambda: sim.run('global.LX = instance_create(0, 0, obj_dummy) if false else 0;') if False else sim.run('var _o = instance_create(0, 0, obj_astream); with (_o) { knight_lyr_step(); global.HL = [klx_cur, klx_index, is_struct(klx_song) ? klx_song.flowery : -1, global.knight_lyr_on, klx_alpha]; } with (_o) instance_destroy();'
                                         'var _T = knight_lyr_kf(); var _w = 0; for (var _i = 0; _i < array_length(global.kf_song.lines); _i++) { var _x = string_replace_all(global.kf_song.lines[_i].text, "-", " "); var _p = string_split(_x, " ", true); _w += array_length(_p); } global.HT = [array_length(_T.nt), _w, array_length(_T.ne), _T.nt[0], _T.lt[1]];'))
    res['hub'] = [sim.py(sim.eval('global.HL')), sim.py(sim.eval('global.HT'))] if ok_ else ('err', err)
    # the fight cuts its music: the pack's song waits; the fight plays it again: it goes on
    A['playing'].discard(bm1)
    ok_, err = auto(sim, lambda: sim.run('knight_kf_tick(); global.P1 = global.kf_song.paused;'))
    A['playing'].add(bm1)
    ok_, err2 = auto(sim, lambda: sim.run('knight_kf_tick(); global.P2 = global.kf_song.paused;'))
    res['cut'] = [sim.eval('global.P1'), sim.eval('global.P2')]
    # still silent every frame
    A['gain'].clear()
    auto(sim, lambda: sim.run('knight_kf_tick();'))
    res['mute'] = (bm1, 0) in A['gain']
    # the end of the song: it starts over
    ok_, err = auto(sim, lambda: sim.run('global.kf_song.finished = true; with (obj_kf_songlyrics) instance_destroy(); knight_kf_tick(); global.LP = [instance_number(obj_kf_songlyrics), is_struct(global.kf_song)];'))
    res['loop'] = sim.py(sim.eval('global.LP')) if ok_ else ('err', err)
    # the hub's credit line steps aside for the pack's own; the menu says who made it
    ok_, err = auto(sim, lambda: sim.run('global.C = [knight_song_credit(), knight_song_credit_of(%d)];' % (n - 1)))
    res['hubcredit'] = sim.py(sim.eval('global.C'))
    # the fight is won: the pack's song ends with it
    ok_, err = auto(sim, lambda: sim.run('knight_battle_won(); global.W = [instance_number(obj_kf_songlyrics), is_undefined(global.knight_kf), is_undefined(global.kf_song)];'))
    res['won'] = sim.py(sim.eval('global.W')) if ok_ else ('err', err)
    # the song list's preview plays the instrumental
    A['streams'].clear()
    ok_, err = auto(sim, lambda: sim.run('global.PV = knight_preview_start("@kf:it_doesnt_end_here"); knight_preview_stop();'))
    res['preview'] = [sim.eval('global.PV') if ok_ else err, [p for _, p in A['streams']]]
    # RANDOM can draw it
    ok_, err = auto(sim, lambda: sim.run('global.RL = []; for (var _i = 0; _i < array_length(global.knight_songs); _i++) { var _f = global.knight_songs[_i].file; if (_f != "" && _f != "@random" && knight_music_exists(_f)) array_push(global.RL, _f); }'))
    res['random'] = sim.py(sim.eval('global.RL'))
    return ('ok', res)


for key in (sys.argv[1:] or ['base', 'kaizo']):
    t = time.time()
    r = run(key)
    print(key, r[0], str(r[1])[:1200], round(time.time() - t, 1), flush=True)
    if r[0] != 'ok':
        ok(False, '%s: %s %s' % (key, r[0], str(r[1])[:300]))
        continue
    res = r[1]
    ok(res['entry'][:3] == ["IT DOESN'T END HERE", '@kf:it_doesnt_end_here', 'DIGITAL DESCENDANT'] and res['entry'][3].lower() < 'digital', key + ': in the FIGHT SONG list under D (the list is sorted by artist), by DIGITAL DESCENDANT %r' % res['entry'])
    ok(res['nofolder'][0] != '' and not res['nofolder'][0].startswith('@') and res['nofolder'][1] == [False, True], key + ': no kfsongs folder: NOT FOUND, the knight\'s own music %r' % res['nofolder'])
    ok(res['folder'][0] in (True, 1) and res['folder'][1].endswith('kfsongs/it_doesnt_end_here/inst.ogg') and 'DIGITAL DESCENDANT' in res['folder'][2], key + ': kfsongs next to data.win: found (its instrumental), the hub\'s song card credits it %r' % res['folder'])
    ok(res['req'] == [True, False, 0, True], key + ': the fight opens its own song as a stand-in; nothing plays before the battle starts it %r' % res['req'])
    s = res['start']
    ok(s[0] in (True, 1) and s[1] == 1 and s[2] == 52 and s[3] in (True, 1) and s[4] and abs(s[5] - 0.8) < 1e-6 and s[6] == ['inst.ogg', 'vocals.ogg'] and s[7] == 'DIGITAL DESCENDANT',
       key + ': the battle starts its music: kf_song_start - instrumental + vocals, 52 timed lines, music volume setting; the stand-in silent %r' % s)
    c = res['credit']
    ok(all(c[:3]) and c[3] == "IT DOESN'T END HERE - DIGITAL DESCENDANT" and c[4] >= 26, key + ': its credit is the hub\'s own song card (MUSIC: IT DOESN\'T END HERE - DIGITAL DESCENDANT, the first seconds); no NOW PLAYING card, no always-on MUSIC tag; lyrics under the hub\'s lines %r' % c)
    ok(res['lyric'][0][0] == 0 and res['lyric'][0][2] == 'Verse 1' and res['lyric'][1] and res['lyric'][2], key + ': at 0:46 the first line is on; the pack draws nothing of its own (no band, no Nullscape lyrics, no flash) %r' % res['lyric'])
    h = res['hub']
    ok(h != 'err' and h[0][0] == 'Lost' and h[0][2] in (False, 0) and h[0][3] in (True, 1) and h[1][0] == h[1][1] == h[1][2] and abs(h[1][3] - 45.04) < 0.01 and abs(h[1][4] - 45.04) < 0.01,
       key + ': the hub\'s own lyrics (Raise Up Your Bat / Flower Man style, white with the sung part blue) show "Lost" at 0:46 on the pack\'s clock; one note per word %r' % (h,))
    ok(res['cut'] == [1, 0] or res['cut'] == [True, False], key + ': the fight cuts its music: the song waits; plays again: it goes on %r' % res['cut'])
    ok(res['mute'], key + ': the stand-in kept silent every frame')
    ok(res['loop'] == [1, True] or res['loop'] == [1, 1], key + ': at its end the song starts over (like battle music loops) %r' % (res['loop'],))
    ok('DIGITAL DESCENDANT' in res['hubcredit'][0] and 'DIGITAL DESCENDANT' in res['hubcredit'][1], key + ': the song list shows its artist %r' % res['hubcredit'])
    ok(res['won'] in ([0, True, True], [0, 1, 1]), key + ': the fight won: the song and its display end %r' % (res['won'],))
    ok(res['preview'][0] == '' and len(res['preview'][1]) == 1 and res['preview'][1][0].endswith('kfsongs/it_doesnt_end_here/inst.ogg'), key + ': the song list\'s preview plays its instrumental %r' % res['preview'])
    ok('@kf:it_doesnt_end_here' in res['random'], key + ': RANDOM can draw it %r' % len(res['random']))
print('%d checks, %d failed' % (N[0], len(FAILS)))
for f_ in FAILS:
    print('FAILED:', f_)
sys.exit(1 if FAILS else 0)
