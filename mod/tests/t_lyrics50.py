"""Build 50: the fight songs' LYRICS (Flower Man, Raise Up Your Bat) and Flowery's menu basics as a custom character.
(The lyric checks of the first build-50 Flowery test, kept when that test - Flowery in Noelle's slot - was retired.)
  - the menus know character 5 (name, letter, party tools), his walking frames as a SKIN;
  - lyrics: the right line at the right moment of Flower Man and of Raise Up Your Bat, the syllable sweep set up by the game's
    own lyric code, back to the start when the song loops, nothing for another song."""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from harness import *

FAILS = []
N = [0]


def ok(c, msg):
    N[0] += 1
    print(('ok   ' if c else 'FAIL ') + msg, flush=True)
    if not c:
        FAILS.append(msg)


J = lambda s, e: s.py(s.eval(e))
SPR = ['spr_knfl_idle', 'spr_knfl_walk', 'spr_knfl_act', 'spr_knfl_attackready', 'spr_knfl_attack', 'spr_knfl_defend', 'spr_knfl_hurt', 'spr_knfl_defeat',
       'spr_knfl_item', 'spr_knfl_victory', 'spr_knfl_spell', 'spr_headflowery', 'spr_bnameflowery', 'spr_flowery_equipchar', 'spr_flowery_walk_down',
       'spr_flowery_walk_up', 'spr_flowery_walk_left', 'spr_flowery_walk_right']


def load_base(sim, names):
    for n in names:
        for d in ('/home/claude/work/build/merged/', '/home/claude/work/gml/base/CodeEntries/'):
            f = d + 'gml_GlobalScript_' + n + '.gml'
            if os.path.exists(f):
                sim.load_source('gml_GlobalScript_' + n, open(f, encoding='utf8').read())
                break



sim = make_sim()
load_base(sim, ['scr_rhythmgame_lyrics'])
for a in SPR:
    try:
        sim.define_asset(a)
    except Exception:
        pass
sim.run('global.knight_fl = undefined; global.knight_ccs = []; knight_fl_register();')
ok(J(sim, 'knight_char_proper(5)') == 'Flowery' and J(sim, 'knight_char_short(5)') == 'F', 'his name in the menus')
ok(J(sim, 'knight_party_size([5, 2, 0])') == 2 and J(sim, 'knight_party_compact([0, 5, 2])') == [5, 2, 0], 'the party tools count him')
ok(J(sim, 'knight_cc_max_id()') == 5 and J(sim, 'knight_char_hpcolor(5)') == 189950, 'he is custom character 5, his HP-bar colour')
ok(J(sim, 'kfo_world_skin_spr(5, 2)') == J(sim, 'spr_flowery_walk_up'), 'his walking frames as a SKIN')
# ---- lyrics ----
sim2 = make_sim()
load_base(sim2, ['scr_rhythmgame_lyrics', 'scr_dark_marker'])
sim2.run('global.krun = { state: "battle", mode: 0, cfg: knight_cfg_default() }; global.knight_run = 1;')
S = J(sim2, 'knight_lyr_songs()')
fm = S[0]
ok(len(fm['ly']) == 39 and fm['ly'][1] == 'Ten feet twen-ty the Flow-er Man', 'Flower Man: its 38 lines from Chapter 5')
ok(S[1]['file'] == 'ch3_karaoke_full.ogg' and 'RAISE UP YOUR BAT FOR THE BURN-ING FIGHT' in S[1]['ly'], 'Raise Up Your Bat: its lines from Chapter 3')
# the syllables: one note per syllable of every Raise Up Your Bat line
segs = sum(len([x for w in l.split(' ') for x in w.split('-') if x]) for l in S[1]['ly'] if l)
ok(segs == len(S[1]['nt']) == len(S[1]['ne']), 'one note per syllable (%d / %d)' % (segs, len(S[1]['nt'])))
pos = [0]
sim2.mock('audio_sound_get_track_position', lambda s, a: pos[0])
sim2.mock('audio_exists', lambda s, a: 1)
sim2.mock('audio_is_playing', lambda s, a: 1)
sim2.mock('knight_music_exists', lambda s, f: 1)
sim2.mock('knight_active', lambda s: 1)
sim2.mock('scr_84_get_font', lambda s, n: 0)
sim2.run('global.batmusic = [1, 2]; global.LC = instance_create(0, 0, obj_marker); global.lang = "en";')
# (the song list's order changed with the build 50 music update: the songs are found by file)
_files = [x['file'] for x in J(sim2, 'global.knight_songs')]
for song_i, f, checks in ((_files.index('Flowerman_Arrangement.ogg'), 'Flowerman_Arrangement.ogg', [(10, ''), (24.5, 'Ten feet twenty the Flower Man'), (51, 'With his heart in the sand'), (150.8, 'Fallen to pieces still without a plan')]),
                          (_files.index('ch3_karaoke_full.ogg'), 'ch3_karaoke_full.ogg', [(16.5, 'WHEN THE DEMON HEART IS CRYING'), (35, "LET'S KNOCK EM DEAD INTO THE NIGHT"), (40, ''), (101, 'Come follow me into the dark')])):
    sim2.run('global.krun.cfg.song = %d;' % song_i)
    ok(J(sim2, 'global.knight_songs[knight_song_eff()].file') == f, '%s is in the song list' % f)
    pos[0] = 0
    sim2.run('with (global.LC) knight_lyr_step();')
    got = []
    for t, want in checks:
        pos[0] = t
        sim2.run('with (global.LC) knight_lyr_step();')
        got.append(J(sim2, 'global.LC.klx_cur'))
    ok(got == [c[1] for c in checks], '%s: the right line at the right time %r' % (f, got))
    pos[0] = 1
    sim2.run('with (global.LC) knight_lyr_step();')
    ok(J(sim2, 'global.LC.klx_cur') == '' and J(sim2, 'global.LC.klx_index') == 0, '%s: back to the start when the song loops' % f)
    pos[0] = checks[1][0]
    sim2.run('with (global.LC) { knight_lyr_step(); knight_lyr_draw(0, 0, 446); }')
    ok(len(J(sim2, 'global.LC.lyric_end')) >= 3, "%s: the game's syllable sweep is set up (%d syllables)" % (f, len(J(sim2, 'global.LC.lyric_end'))))
sim2.run('global.krun.cfg.song = 1; with (global.LC) knight_lyr_step();')
ok(J(sim2, 'is_undefined(global.LC.klx_song)') or J(sim2, 'global.LC.klx_alpha') < 1, 'another song: no lyrics')
print('%d checks, %d failed' % (N[0], len(FAILS)))
for f_ in FAILS:
    print('FAILED:', f_)
sys.exit(1 if FAILS else 0)
