"""Build 50: the music catalog (the Claude Music Handoff): 44 songs sorted by artist A-Z with ids and credits, moved accounts!! ->
lexxiemow, RANDOM's per-player on / off list (all on by default, kept in knighthub_songs.ini, never drawn when off, silence
when every song is off), the online KNIGHTMARE / FINAL TWO songs, the old online MUSIC number read by file, CREDITS > MUSIC.
Usage: python3 t_music50.py"""
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
    T = {'t': 0}
    sim.mock('get_timer', lambda sm: T['t'] * 1000)
    sim.mock('current_time', 0) if False else None
    ok_, err = auto(sim, lambda: sim.run('global.knight_run = 1; var _c = knight_cfg_default(); _c.party = [1,2,4];'
                                         'global.krun = knight_run_new({src: _c, cfg: _c, plan: [knight_find_key("%s")], reveal: ""}); global.krun.state = "arena";'
                                         'global.batmusic = [-1, -1]; global.knight_song_off = undefined;' % key))
    if not ok_:
        return ('run', err)
    n = sim.eval('array_length(global.knight_songs)')
    S = [[sim.eval('global.knight_songs[%d].%s' % (i, f)) for f in ('name', 'file', 'by', 'sid', 'src')] + [sim.py(sim.eval('global.knight_songs[%d].cl' % i))] for i in range(n)]
    res['S'] = S
    # every song file in the game's mus folder (and the pack song's folder) - small stand-ins
    for e in S:
        f = e[1]
        if f and not f.startswith('@'):
            p = os.path.join(sim.fs.root, 'mus', f)
            os.makedirs(os.path.dirname(p), exist_ok=True)
            open(p, 'wb').write(b'OggS')
    d = os.path.join(sim.fs.root, 'kfsongs', 'it_doesnt_end_here')
    os.makedirs(d, exist_ok=True)
    for f in ('song.json', 'lyrics.json'):
        shutil.copy(PACK + f, d)
    for f in ('inst.ogg', 'vocals.ogg'):
        open(os.path.join(d, f), 'wb').write(b'OggS')
    # (1.0.1: the game looks for files again at most every 3 seconds - knight_cache_get; here they are new at once)
    sim.run('knight_music_cache_clear();')
    ri = [i for i, e in enumerate(S) if e[1] == '@random'][0]
    res['ri'] = ri
    # a fresh player: every song in RANDOM
    res['fresh'] = [sim.eval('knight_song_on_count()'), os.path.exists(os.path.join(sim.fs.root, 'knighthub_songs.ini'))]
    # one song off: never drawn (300 draws at different times)
    vi = [i for i, e in enumerate(S) if e[1] == 'kh_venari.ogg'][0]
    sim.run('knight_song_set_on(%d, false);' % vi)
    drawn = set()
    for t in range(300):
        T['t'] = t * 7
        drawn.add(sim.eval('knight_song_random_index()'))
        drawn.add(sim.eval('knight_song_random_index_n(3)'))
    res['one_off'] = [vi in drawn, len(drawn), sim.eval('knight_song_on_count()')]
    # kept for next time (the list read again from the file)
    sim.run('global.knight_song_off = undefined;')
    res['kept'] = [sim.eval('knight_song_on(%d)' % vi), sim.eval('knight_song_on_count()'), open(os.path.join(sim.fs.root, 'knighthub_songs.ini')).read()]
    # every song off: RANDOM draws nothing - the fight is silent (its own song a muted stand-in, nothing of the pack)
    ok_, err = auto(sim, lambda: sim.run('knight_song_set_all(false); global.krun.cfg.song = %d; global.R0 = [knight_song_random_index(), knight_song_on_count(), knight_song_eff()];'
                                         'global.batmusic[0] = snd_init(knight_song_file("knight.ogg")); global.R1 = [is_struct(global.knight_kf) ? global.knight_kf.sid : "none"];' % ri))
    res['all_off'] = [sim.py(sim.eval('global.R0')), sim.py(sim.eval('global.R1'))] if ok_ else ('err', err)
    # the song list says so; ENABLE ALL brings them back; a song added later starts on
    ok_, err = auto(sim, lambda: sim.run('var _l = knight_songpick_list("off"); global.L1 = [_l[%d][2], _l[%d][0], _l[%d][0]];'
                                         'knight_song_set_all(true); global.L2 = knight_song_on_count();'
                                         'array_push(global.knight_songs, { name: "NEW", file: "kh_new_test.ogg", by: "x", src: "", sid: "kh_new_test.ogg", cl: [] }); global.L3 = knight_song_on(array_length(global.knight_songs) - 1); array_pop(global.knight_songs);' % (ri, ri + 1, ri + 2)))
    res['list'] = [sim.py(sim.eval('global.L1')), sim.eval('global.L2'), sim.eval('global.L3')] if ok_ else ('err', err)
    # the online songs: KNIGHTMARE stage, then the FINAL TWO (it wins), each once
    # (DRBR 1.0.1: only with MUSIC on DEFAULT - a song of your own, RANDOM too, plays on through the big moments: checked below)
    sim.run('global.krun.cfg.song = 0;')
    ok_, err = auto(sim, lambda: sim.run('global.kfo = { M: { situ: "" } }; global.knight_mus_q = []; global.knight_kf = undefined;'
                                         'with (obj_astream) instance_destroy(); var _a = instance_create(0, 0, obj_astream); _a.mystream = 77; _a.songname = "knight.ogg"; global.batmusic = [77, 78];'
                                         'global.Q = [];'
                                         'kfo_mus_situ("nm"); array_push(global.Q, array_length(global.knight_mus_q) > 0 ? global.knight_mus_q[array_length(global.knight_mus_q) - 1].file : "");'
                                         'var _b = instance_create(0, 0, obj_astream); _b.mystream = 79; _b.songname = "kh_forget_me_not.ogg"; global.batmusic = [79, 80];'
                                         'var _c0 = array_length(global.knight_mus_q); kfo_mus_situ("nm"); array_push(global.Q, array_length(global.knight_mus_q) - _c0);'
                                         'kfo_mus_situ("lms"); array_push(global.Q, global.knight_mus_q[array_length(global.knight_mus_q) - 1].file);'
                                         'var _d = instance_create(0, 0, obj_astream); _d.mystream = 81; _d.songname = "kh_close_to_inevitability.ogg"; global.batmusic = [81, 82];'
                                         'var _c1 = array_length(global.knight_mus_q); kfo_mus_situ("nm"); kfo_mus_situ("lms"); array_push(global.Q, array_length(global.knight_mus_q) - _c1);'))
    res['situ'] = sim.py(sim.eval('global.Q')) if ok_ else ('err', err)
    # 1.0.1: a song of your own (here RANDOM) is not replaced by the big moments' songs
    ok_, err = auto(sim, lambda: sim.run('global.krun.cfg.song = %d; global.kfo = { M: { situ: "" } }; global.knight_mus_q = []; var _q0 = array_length(global.knight_mus_q);'
                                         'kfo_mus_situ("nm"); kfo_mus_situ("lms"); global.Q2 = [array_length(global.knight_mus_q) - _q0, kbr_mus_own()]; global.krun.cfg.song = 0;' % ri))
    res['own'] = sim.py(sim.eval('global.Q2')) if ok_ else ('err', err)
    # an online MUSIC setting saved as a number by an older build (24: RANDOM then) is read as its song
    res['v49'] = [sim.eval('global.knight_songs_v49[24]'), sim.eval('knight_song_find_exact(global.knight_songs_v49[24])'), sim.eval('global.knight_songs_v49[12]'), sim.eval('global.knight_songs[knight_song_find_exact(global.knight_songs_v49[12])].file')]
    # CREDITS > MUSIC
    ok_, err = auto(sim, lambda: sim.run('var _e = knight_credit_entry(knight_count() + 1); global.CR = [_e.title, array_length(_e.credits), knight_credit_count(), knight_credit_pages(knight_count() + 1)];'))
    res['cr'] = sim.py(sim.eval('global.CR')) if ok_ else ('err', err)
    return ('ok', res)


import re
for key in (sys.argv[1:] or ['base']):
    t = time.time()
    r = run(key)
    print(key, r[0], str(r[1])[:300], round(time.time() - t, 1), flush=True)
    if r[0] != 'ok':
        ok(False, '%s: %s %s' % (key, r[0], str(r[1])[:300]))
        continue
    res = r[1]
    S = res['S']
    real = [e for e in S if e[1] not in ('', '@random')]
    ok(S[0][1] == '' and S[1][1] == '@random' and len(real) == 44, 'MOD DEFAULT and RANDOM first, then 44 songs (22 from the handoff: 20 new + TILL THE END and FORGET ME NOT already in) %r' % len(real))
    def sk(e):
        a = re.sub(r'^[^0-9A-Za-z]+', '', e[2]).lower()
        if e[1] == 'kh_dusttale_sonata.ogg':
            a = 'aman'
        return (a, re.sub(r'^[^0-9A-Za-z]+', '', e[0]).lower())
    ok([sk(e) for e in real] == sorted(sk(e) for e in real), 'sorted by artist A-Z (case-insensitive, leading symbols ignored), title A-Z within an artist')
    ok(len(set(e[3] for e in S)) == len(S) and all(e[3] == e[1] for e in real), 'every song has its own stable id (its file)')
    want = {'kh_dusttale_sonata.ogg', 'kh_close_to_inevitability.ogg', 'kh_deep_waters.ogg', 'kh_neo_chaos.ogg', 'kh_risen_up.ogg', 'kh_megalovania_itsaleccio.ogg', 'kh_wheel_of_misfortune.ogg', 'kh_ice_shock.ogg', 'kh_venari.ogg', 'kh_chrysalis.ogg', 'kh_hell_for_frandle.ogg', 'kh_fraight_fest.ogg', 'kh_our_flower_power.ogg', 'kh_petal_dance.ogg', 'kh_vs_susie_neo.ogg', 'kh_white_cell.ogg', 'kh_megalovania_sunhatgirl.ogg', 'kh_penumbra_phantasm.ogg', 'kh_heir_of_grief.ogg', 'kh_blood.ogg', 'kh_till_the_end.ogg', 'kh_forget_me_not.ogg'}
    files = set(e[1] for e in real)
    ok(want <= files, 'all 22 handoff songs are in the list %r' % sorted(want - files))
    ok(all(e[4] != '' and len(e[5]) > 0 for e in real if e[1] in want), 'each handoff song has its source and credit lines')
    ic = [e for e in real if e[1] == 'kh_identity_crisis.ogg'][0]
    ok(ic[2] == 'lexxiemow' and 'moved accounts!!' in ' '.join(ic[5]) and not any(e[2] == 'moved accounts!!' for e in S), 'moved accounts!! -> lexxiemow (formerly ... kept in its credits) %r' % ic[2])
    ok(not any(e[2] == 'lexxiemow' and e[1] in ('kh_chrysalis.ogg',) for e in real), 'lexycat stays lexycat')
    ok(res['fresh'] == [44, False], 'a fresh player: every song in RANDOM, no file needed %r' % res['fresh'])
    ok(res['one_off'][0] in (False, 0) and res['one_off'][2] == 43, 'one song turned off: never drawn by RANDOM (600 draws) %r' % res['one_off'])
    ok(res['kept'][0] in (False, 0) and res['kept'][1] == 43 and 's_kh_venari_ogg=1' in res['kept'][2].replace(' ', '').replace('"', ''), 'kept for next time (knighthub_songs.ini, by id) %r' % res['kept'][:2])
    ao = res['all_off']
    ok(ao != 'err' and ao[0][0] == -1 and ao[0][1] == 0 and ao[0][2] == res['ri'] and ao[1] == [''], 'every song off: nothing drawn, RANDOM itself - the fight silent (a muted stand-in) %r' % (ao,))
    li = res['list']
    ok(li != 'err' and li[0] == ['NO SONGS SELECTED', -10, -11] and li[1] == 44 and li[2] in (True, 1), 'the song list says NO SONGS SELECTED, has ENABLE ALL / DISABLE ALL rows; ENABLE ALL brings all back; a song added later starts on %r' % (li,))
    ok(res['situ'] == ['kh_forget_me_not.ogg', 0, 'kh_close_to_inevitability.ogg', 0], 'online: KNIGHTMARE stage -> FORGET ME NOT V3, once; FINAL TWO -> Close To Inevitability, once, and the stage does not take it back %r' % (res['situ'],))
    ok(res['own'] == [0, True], 'online (1.0.1): a song of your own (RANDOM) plays on - no big-moment song replaces it %r' % (res['own'],))
    v = res['v49']
    ok(v[0] == '@random' and v[1] == res['ri'] and v[2] == v[3], 'an online MUSIC number from an older build is read as its song (old 24 = RANDOM) %r' % v)
    ok(res['cr'] != 'err' and res['cr'][0] == 'MUSIC' and res['cr'][1] == 44 and res['cr'][3] > 1, 'CREDITS > MUSIC: all 44 songs one by one %r' % (res['cr'],))
print('%d checks, %d failed' % (N[0], len(FAILS)))
for f_ in FAILS:
    print('FAILED:', f_)
sys.exit(1 if FAILS else 0)
