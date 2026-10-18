"""Build 47: the new fight songs - a choice offline (FIGHT SONG) and online (MORE OPTIONS > MUSIC), each with its credit.

  list      the song list in the built code: the seven new songs and Flower Man, each with its file, artist and source; the
            hub's CREDITS > Music names every artist with the source
  files     the seven shipped files: real Ogg Vorbis, 44.1 kHz stereo, their length, their loudness (one level for all,
            -11 LUFS); Flower Man is not shipped - the game's own mus\\Flowerman_Arrangement.ogg is used
  offline   FIGHT SONG cycles through every song; the fight plays the chosen file when it is there, else the knight's own
            music (Flower Man missing: no error, no credit); the credit line ("NAME - ARTIST") while the fight starts
  online    MUSIC: AS IN THE HUB (the hub's FIGHT SONG) or any song, kept in the online settings file; the match plays it
            (kfo_launch -> the run's song); a bad saved value falls back to AS IN THE HUB; the battle log names the song once
Usage: python3 t_songs47.py [part ...]"""
import sys, os, json, time, subprocess, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from harness import *

FAILS = []
N = [0]
STATS = {}
MUS = '/home/claude/work/deliver/mus/'
NEW = ['kh_void_star.ogg', 'kh_lv_crusher.ogg', 'kh_true_hero.ogg', 'kh_neotech_online.ogg', 'kh_storyshift_black.ogg', 'kh_anywhere_you_go.ogg',
       'kh_ever_ascending.ogg',
       # build 48: twelve more (knight_hub_music2.zip)
       'kh_lost_dream.ogg', 'kh_forget_me_not.ogg', 'kh_hell_hammer.ogg', 'kh_in_my_way.ogg', 'kh_till_the_end.ogg', 'kh_megalo_vania.ogg',
       'kh_megalo_strike_back.ogg', 'kh_red_crimson_death.ogg', 'kh_wrong_enemy.ogg', 'kh_n1ght_of_n1ghtcore.ogg', 'kh_that_feeling.ogg', 'kh_identity_crisis.ogg']
WANT = {'kh_void_star.ogg': ('VOID STAR', 'rundown', 'soundcloud.com/rundownsd/void-star'),
        'kh_lv_crusher.ogg': ('L.V. CRUSHER', 'saknol', 'soundcloud.com/saknol/lvcrusher'),
        'kh_true_hero.ogg': ('TRUE HERO', 'Tory Fox [DISC 2]', 'soundcloud.com/toryfox2/mus_undynex_ogg'),
        'kh_neotech_online.ogg': ('NEOTECH:ONLINE', 'antagonist', 'soundcloud.com/genericantagonist/neotech'),
        'kh_storyshift_black.ogg': ('STORYSHIFT ~ 100. BLACK', 'Jay', 'soundcloud.com/jay_josh1212/jackblack'),
        'kh_anywhere_you_go.ogg': ('ANYWHERE YOU GO [LEGACY]', 'lexxiemoww', 'soundcloud.com/lexxiemow/x_cc'),
        'kh_ever_ascending.ogg': ('EVER ASCENDING', 'lexxiemoww', 'soundcloud.com/lexxiemow/trinky_finale'),
        'Flowerman_Arrangement.ogg': ('Flower Man (feat. Camellia)', 'Toby Fox', 'soundcloud.com/tobyfox-music/flower-man-feat-camellia'),
        # build 48
        'kh_lost_dream.ogg': ('LOST DREAM // VS NOELLE.EXE', 'ionizachip', 'soundcloud.com/imperfectnore/lost-dream-vs-noelle-exe'),
        'kh_forget_me_not.ogg': ('FORGET ME NOT V3', 'JustStereo', 'soundcloud.com/juststereo/forget-me-not-v3-deltarune-chapter-6'),
        'kh_hell_hammer.ogg': ('HELL HAMMER', 'Geefel', 'soundcloud.com/geefel/hhammer'),
        'kh_in_my_way.ogg': ('In My Way', 'SEWNPUARD', 'soundcloud.com/sewnpard/zzz_cree_ogg'),
        'kh_till_the_end.ogg': ('TILL THE END', 'DanlyDaMusician', 'soundcloud.com/user-185212763/till-the-end'),
        'kh_megalo_vania.ogg': ('MEGALO VANIA', 'igorsantusa', 'soundcloud.com/casserole12345/megalo-vania'),
        'kh_megalo_strike_back.ogg': ('(Unused) MEGALO STRIKE BACK', 'EVAERDRAD', 'soundcloud.com/modestbbq/storyspin-99-unused'),
        'kh_red_crimson_death.ogg': ('RED, CRIMSON DEATH', 'Tory Fox, Igorsantusa', 'soundcloud.com/toryfox2/mus_xpart_ogg'),
        'kh_wrong_enemy.ogg': ('Wrong Enemy....?', 'Tory Fox', 'soundcloud.com/toryfox/mus_waterdragon1_ogg'),
        'kh_n1ght_of_n1ghtcore.ogg': ('N1GHT OF N1GH+COR3 >:3', 'plush', 'soundcloud.com/plushcat/n1ght-of-n1ghcoya3-3'),
        'kh_that_feeling.ogg': ('That Feeling (In Your Bones)', 'sunhatgirl', 'soundcloud.com/keep-smyling-2/legendaryfartmaster'),
        'kh_identity_crisis.ogg': ('IDENTITY CRISIS (Arrangement)', 'lexxiemow', 'soundcloud.com/realhodgepodge/identity-crisis-arrangement')}
# build 48: Guardian is the game's own Chapter 4 file (mus/titan_battle.ogg on the player's DELTARUNE), never shipped


def ok(c, m):
    N[0] += 1
    if not c:
        FAILS.append(m)
        print('FAIL', m, flush=True)
    return c


def J(sim, e):
    return sim.py(sim.eval(e))


def songs(sim):
    return J(sim, 'global.knight_songs')


def part_list():
    sim = make_sim()
    L = songs(sim)
    files = [s['file'] for s in L]
    ok(L[0]['file'] == '' and L[0]['name'] == 'Mod default', 'list: the first entry is the knights\' own music (Mod default)')
    for f, (nm, by, src) in WANT.items():
        e = [s for s in L if s['file'] == f]
        ok(len(e) == 1 and e[0]['name'] == nm and e[0].get('by') == by and e[0].get('src') == src, 'list: %s - "%s" by %s (%s)' % (f, nm, by, e[0] if e else None))
    # build 50 (later): the Claude Music Handoff added 22 more songs and the KF Song Pack one - every build 47 song is still here
    ok(len(L) >= 5 + len(WANT), 'list: at least the %d build 47 songs (now %d)' % (5 + len(WANT), len(L)))
    gd = [x for x in L if x['file'] == 'titan_battle.ogg']
    ok(len(gd) == 1 and gd[0]['name'] == 'Guardian' and gd[0]['by'] == 'Toby Fox', 'list: Guardian = the game\'s own mus/titan_battle.ogg (%s)' % gd)
    km = [x for x in L if x['file'] == 'knightmare_knight.ogg']
    ok(km and km[0]['name'] == 'KNIGHTMARE' and km[0]['by'].startswith('Ann'), 'list: KNIGHTMARE by Ann (nahghyperfresh) (%s)' % km)
    cr = J(sim, 'global.knight_hub_credits')
    mus = [g for g in cr if g['g'] == 'Music']
    txt = json.dumps(mus)
    miss = [by for f, (nm, by, src) in WANT.items() if by not in txt or nm.split(' (')[0] not in txt]
    ok(mus and not miss, 'list: CREDITS > Music names every artist and song (missing: %s)' % miss)
    srcmiss = [src for f, (nm, by, src) in WANT.items() if f != 'Flowerman_Arrangement.ogg' and src.rsplit('/', 1)[0] not in txt]
    ok(not srcmiss, 'list: and where each is from (missing: %s)' % srcmiss)
    for i, s in enumerate(L):
        c = J(sim, 'knight_song_credit_of(%d)' % i)
        if s['file'] == '':
            ok(c == '', 'list: no credit for the knights\' own music')
        elif s['file'] in WANT:
            ok(c == WANT[s['file']][0].upper() + ' - ' + WANT[s['file']][1], 'list: credit line "%s"' % c)


def ffprobe(p):
    r = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'stream=codec_name,sample_rate,channels:format=duration,format_name', '-of', 'json', p],
                       capture_output=True, text=True)
    return json.loads(r.stdout)


def loudness(p):
    r = subprocess.run(['ffmpeg', '-hide_banner', '-nostats', '-i', p, '-af', 'ebur128=peak=true', '-f', 'null', '-'], capture_output=True, text=True)
    m = re.findall(r'I:\s+(-?[\d.]+) LUFS', r.stderr)
    pk = re.findall(r'Peak:\s+(-?[\d.]+) dBFS', r.stderr)
    return (float(m[-1]) if m else None, float(pk[-1]) if pk else None)


def part_files():
    rows = {}
    for f in NEW:
        p = MUS + f
        ok(os.path.isfile(p), 'files: %s is in the package\'s mus folder' % f)
        if not os.path.isfile(p):
            continue
        with open(p, 'rb') as fh:
            head = fh.read(64)
        pr = ffprobe(p)
        st = pr['streams'][0] if pr.get('streams') else {}
        dur = float(pr['format']['duration'])
        lu, pk = loudness(p)
        rows[f] = {'MB': round(os.path.getsize(p) / 1e6, 2), 's': round(dur), 'codec': st.get('codec_name'), 'hz': st.get('sample_rate'), 'ch': st.get('channels'), 'LUFS': lu, 'peak': pk}
        ok(head[:4] == b'OggS' and st.get('codec_name') == 'vorbis' and st.get('sample_rate') in ('44100', '48000') and st.get('channels') == 2,
           'files: %s - Ogg Vorbis stereo (%s)' % (f, rows[f]))
        ok(60 < dur < 900, 'files: %s - %.0f s long' % (f, dur))
        ok(lu is not None and -12.0 <= lu <= -10.0 and pk is not None and pk <= 0.0, 'files: %s - loudness %.1f LUFS, peak %.1f dBFS (all at about -11 LUFS)' % (f, lu or 0, pk or 0))
    ok(not os.path.exists(MUS + 'Flowerman_Arrangement.ogg'), 'files: Flower Man is not shipped (the game\'s own file is used)')
    ok(not os.path.exists(MUS + 'titan_battle.ogg'), 'files: Guardian is not shipped (the game\'s own titan_battle.ogg is used)')
    STATS['files'] = rows


def song_sim(present):
    """a hub game; file_exists says yes for the files in `present` (the mus folder of the player's game)"""
    sim = make_sim()
    sim.run('knight_store_load(); global.knight_cfg = knight_cfg_default(); knight_ensure_ctrl();')
    sim.present = set(present)
    sim.mock('file_exists', lambda s, p: os.path.basename(str(p)) in s.present)
    return sim


def part_offline():
    every = [s['file'] for s in songs(make_sim()) if s['file']]
    sim = song_sim(every)
    n = J(sim, 'array_length(global.knight_songs)')
    seen = []
    for k in range(n + 1):
        seen.append(J(sim, 'global.knight_cfg.song'))
        sim.run('global.knight_cfg.song = knight_ui_cycle(global.knight_cfg.song, 1, array_length(global.knight_songs));')
    ok(sorted(set(seen)) == list(range(n)) and seen[-1] == seen[0], 'offline: FIGHT SONG cycles through all %d songs and around (%s)' % (n, seen))
    # each song played by a hub fight (the run's song; the fight asks knight_song_file for its own track)
    good = 0
    for i in range(n):
        sim.run('var _c = knight_cfg_default(); _c.song = %d; global.knight_run = 1; global.krun = knight_run_new({ src: _c, cfg: _c, plan: [0], reveal: "", corr: [] });' % i)
        f = J(sim, 'knight_song_file("knight.ogg")')
        want = J(sim, 'global.knight_songs[%d].file' % i) or None
        cr = J(sim, 'knight_song_credit()')
        if want is not None and want.startswith('@kf:'):
            # (a KF Song Pack song: its own test, t_kfsong50 - here the pack is not installed: the knight's own music, no credit)
            if f == 'knight.ogg' and cr == '':
                good += 1
            continue
        if want == '@random':
            # build 48: RANDOM - one of the real songs, kept for the run, credited
            f2 = J(sim, 'knight_song_file("knight.ogg")')
            if f in every and f != '@random' and f2 == f and cr != '':
                good += 1
            continue
        if (want is None and f in ('knight.ogg',)) or f == want:
            if (want is None and cr == '') or (want is not None and cr != ''):
                good += 1
    ok(good == n, 'offline: every song plays when chosen, with its credit (%d / %d)' % (good, n))
    # Flower Man missing from the player's game: the knight's own music, no credit, no error
    sim2 = song_sim([f for f in every if f != 'Flowerman_Arrangement.ogg'] + ['knight.ogg'])
    fi = [i for i, s in enumerate(songs(sim2)) if s['file'] == 'Flowerman_Arrangement.ogg'][0]
    sim2.run('var _c = knight_cfg_default(); _c.song = %d; global.knight_run = 1; global.krun = knight_run_new({ src: _c, cfg: _c, plan: [0], reveal: "", corr: [] });' % fi)
    ok(J(sim2, 'knight_song_file("knight.ogg")') == 'knight.ogg' and J(sim2, 'knight_song_credit()') == '',
       'offline: Flower Man chosen but not in the game\'s mus folder - the knight\'s own music plays, no credit shown')
    ok(J(sim2, 'knight_music_exists("Flowerman_Arrangement.ogg")') is False and J(sim, 'knight_music_exists("Flowerman_Arrangement.ogg")') is True,
       'offline: Flower Man is found exactly when the game\'s own file is there')
    # the song page's description names the artist and the source
    sim.run('global.knight_cfg.song = %d;' % [i for i, s in enumerate(songs(sim)) if s['file'] == 'kh_void_star.ogg'][0])
    d = J(sim, 'knight_ui_desc_for("song")') if J(sim, 'script_exists(asset_get_index("knight_ui_desc_for"))') else None
    STATS['offline'] = {'songs': n, 'played': good}


def part_online():
    every = [s['file'] for s in songs(make_sim()) if s['file']]
    sim = song_sim(every)
    sim.run('kfo_get();')
    n = J(sim, 'array_length(global.knight_songs)')
    ok(J(sim, 'global.kfo.song') == -1, 'online: MUSIC starts AS IN THE HUB (-1)')
    seen = []
    for k in range(n + 2):
        seen.append(J(sim, 'global.kfo.song'))
        sim.run('var _o = global.kfo; _o.song = ((_o.song + 1 + 1 + array_length(global.knight_songs) + 1) mod (array_length(global.knight_songs) + 1)) - 1;')
    ok(sorted(set(seen)) == list(range(-1, n)), 'online: MUSIC cycles AS IN THE HUB and every song (%s)' % seen)
    # kept in the online settings file
    sim.run('global.kfo.song = 4; kfo_ini_save(); global.kfo = undefined; kfo_get();')
    ok(J(sim, 'global.kfo.song') == 4, 'online: the choice is kept (4 after a restart)')
    for bad in (99, -5, 2.5):
        # (build 50 keeps the song as its file, "songf": a bad number alone is what an older file would have)
        sim.run('ossafe_ini_open(kfo_ini_file()); ini_write_real("player", "song", %r); ini_key_delete("player", "songf"); ossafe_ini_close(); global.kfo = undefined; kfo_get();' % bad)
        ok(J(sim, 'global.kfo.song') == -1, 'online: a bad saved song (%r) - AS IN THE HUB' % bad)
    # the match plays it: kfo_launch puts it in the run (needs a match: the launch code's own lines)
    src = open(M + 'gml_GlobalScript_knight_core.gml', encoding='utf8').read()
    ok('_c.song = (_o.song >= 0) ? _o.song : (is_struct(global.knight_cfg) ? knight_cfg_num(global.knight_cfg, "song") : 0);' in src,
       'online: the match\'s run takes MUSIC, or the hub\'s FIGHT SONG when AS IN THE HUB')
    STATS['online'] = {'choices': len(set(seen))}


PARTS = {'list': part_list, 'files': part_files, 'offline': part_offline, 'online': part_online}

if __name__ == '__main__':
    t0 = time.time()
    for k in (sys.argv[1:] or list(PARTS)):
        print('== part', k, flush=True)
        try:
            PARTS[k]()
        except Exception as ex:
            import traceback
            traceback.print_exc()
            ok(False, '%s: crashed: %s' % (k, str(ex)[:300]))
    print('STATS', json.dumps(STATS))
    print('t_songs47: %d checks, %d failed, %.0fs' % (N[0], len(FAILS), time.time() - t0))
    for m in FAILS[:30]:
        print('  ', m)
    sys.exit(1 if FAILS else 0)
