"""Build 41 music transitions, in the real merged code (emulator, sound calls recorded instead of played):
  - the helpers: a cut fades the battle song out and stops it when the fade is over (a dead stop without the hub controller or
    when nothing plays), a switch starts the new song from silence and fades it in, a still-playing different song is faded out
    under it, a restarted same song keeps its new copy, pending stops wait while the hub is frozen, knight_mus_reset drops them;
  - Violet's Side B in the Weird Route (the mod's own Kris path, the hub's no-Kris path, the parry path): the battle song fades out
    in a third of a second at the blow instead of stopping dead, the Side B song fades in over two seconds;
  - Tag Team: the knight who takes over after a KO brings their own song (SONG: MOD DEFAULT only): the old song fades out over a
    second and is freed, the new one fades in over two; nothing changes with a chosen song, with the same song, or when the battle
    or the lineup is over before the new song is due."""
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lu_harness import *
import emu_atk

FAILS = []; N = [0]
def ok(c, msg):
    N[0] += 1
    if not c: FAILS.append(msg); print('FAIL', msg, flush=True)
def eq(a, b, msg):
    N[0] += 1
    if a != b: FAILS.append(msg); print('FAIL', msg, 'got', repr(a), 'want', repr(b), flush=True)

t0 = time.time()
SIDEB = 4242
if os.environ.get('KH_MERGED'):
    # the round trip: the decompiled code has Side B's song as its data.win number (the decompiler cannot know that
    # knight_mus_switch takes a sound), so the song is that number here too
    from harness import _rt_tables
    SIDEB = _rt_tables()['asset'].get('violetknight_sideb', SIDEB)


def music_mocks(sim, exists=()):
    """record the sound calls; audio_is_playing answers from the copies started and not stopped"""
    sim.mlog = []
    sim.playing = {}          # copy -> sound
    nxt = [5000]
    def mus_volume(s, inst, v, fr): s.mlog.append(('vol', inst, v, fr)); return 0
    def snd_stop(s, snd):
        s.mlog.append(('stop', snd))
        for i in [i for i, a in s.playing.items() if a == snd or i == snd]:
            del s.playing[i]
        return 0
    def audio_stop_sound(s, inst):
        s.mlog.append(('istop', inst)); s.playing.pop(inst, None); return 0
    def audio_is_playing(s, inst): return 1 if inst in s.playing else 0
    def mus_loop(s, snd):
        nxt[0] += 1; s.mlog.append(('loop', snd, nxt[0])); s.playing[nxt[0]] = snd; return nxt[0]
    def snd_free(s, snd): s.mlog.append(('free', snd)); return 0
    def snd_init(s, f):
        nxt[0] += 1; s.mlog.append(('init', f, nxt[0])); return nxt[0]
    for n, f in (('mus_volume', mus_volume), ('snd_stop', snd_stop), ('audio_stop_sound', audio_stop_sound), ('audio_is_playing', audio_is_playing),
                 ('mus_loop', mus_loop), ('snd_free', snd_free), ('snd_init', snd_init)):
        sim.mock(n, f)
    ex = set(exists)
    sim.mock('knight_music_exists', lambda s, f: 1 if f in ex else 0)


def start_song(sim, snd=100, inst=200, name='knight.ogg'):
    """the battle song as the fight starts it: a stream from snd_init (with its obj_astream) and its playing copy"""
    sim.run('global.batmusic = [%d, %d]; with (obj_astream) instance_destroy(); global.AS = instance_create(0, 0, obj_astream); '
            'global.AS.mystream = %d; global.AS.songname = "%s";' % (snd, inst, snd, name))
    sim.playing[inst] = snd


def ev(sim, kind):
    return [e for e in sim.mlog if e[0] == kind]


def run_frames(sim, n):
    r = frames(sim, n)
    ok(r is None, 'frames run (%s)' % (r,))


# ======================= the helpers =======================
sim, e = lu_battle('base', combo=0)
ok(e is None, 'battle set up (%s)' % (e,))
music_mocks(sim)
run_frames(sim, 3)   # (the harness enters its room on the first frame)
ok(sim.eval('instance_exists(obj_knight_ctrl)'), 'the hub controller runs the queue')

# a cut: fade, then the stop when the fade is over
start_song(sim)
sim.run('knight_mus_cut(10);')
eq(sim.mlog, [('vol', 200, 0, 10)], 'cut: the song fades out over 10 frames (no dead stop)')
run_frames(sim, 10)
eq(ev(sim, 'stop'), [], 'cut: still fading after 10 frames')
run_frames(sim, 1)
eq(ev(sim, 'stop'), [('stop', 100)], 'cut: stopped when the fade is over (the whole song, as the fight did)')
eq(sim.eval('array_length(global.knight_mus_q)'), 0, 'cut: nothing left pending')

# nothing playing: the fight's own dead stop
sim.mlog.clear(); sim.playing.clear()
sim.run('global.batmusic = [100, 200]; knight_mus_cut(10);')
eq(sim.mlog, [('stop', 100)], 'cut with nothing playing: stopped at once')

# without the hub controller: the fight's own dead stop
sim.mlog.clear(); start_song(sim)
sim.run('with (obj_knight_ctrl) instance_destroy(); knight_mus_cut(10);')
eq(sim.mlog, [('stop', 100)], 'cut without the hub controller: stopped at once')
sim.run('knight_ensure_ctrl();')

# frozen (hub pause): the stop waits
sim.mlog.clear(); start_song(sim)
sim.run('knight_mus_cut(10); global.knight_frozen = true;')
run_frames(sim, 20)
eq(ev(sim, 'stop'), [], 'frozen: the pending stop waits')
sim.run('global.knight_frozen = false;')
run_frames(sim, 11)
eq(ev(sim, 'stop'), [('stop', 100)], 'unfrozen: then it stops')

# reset: a fade still running ends now (its song stops), a song change still to come is dropped
sim.mlog.clear(); start_song(sim)
sim.run('knight_mus_cut(10); array_push(global.knight_mus_q, { k: "song", file: "x.ogg", old: 100, fin: 60, t: 5 }); knight_mus_reset();')
eq(ev(sim, 'stop'), [('stop', 100)], 'reset: the fading song stops at once')
run_frames(sim, 15)
eq(ev(sim, 'init') + ev(sim, 'loop'), [], 'reset: the song change is dropped')
eq(sim.eval('array_length(global.knight_mus_q)'), 0, 'reset: nothing pending')

# a switch: from silence, fading in
sim.mlog.clear(); sim.playing.clear()
sim.run('global.batmusic = [100, 200]; knight_mus_switch(%d, 60);' % SIDEB)
lp = ev(sim, 'loop')
eq(len(lp), 1, 'switch: one copy started')
X = lp[0][2] if lp else -1
eq(sim.mlog, [('loop', SIDEB, X), ('vol', X, 0, 0), ('vol', X, 1, 60)], 'switch: starts silent, fades in over 60 frames')
eq(sim.py(sim.eval('global.batmusic')), [SIDEB, X], 'switch: it is the battle song now')
sim.mlog.clear()
sim.run('knight_mus_switch(%d, 0);' % SIDEB)
eq([e[0] for e in sim.mlog], ['loop'], 'switch without a fade: just started')

# a switch while another song still plays: that one fades out under it
sim.mlog.clear(); sim.playing.clear(); start_song(sim)
sim.run('knight_mus_switch(%d, 60);' % SIDEB)
eq(sim.mlog[0], ('vol', 200, 0, 30), 'switch over a playing song: the old one fades out over a second')
ok(ev(sim, 'loop') and ev(sim, 'loop')[0][1] == SIDEB, 'switch over a playing song: the new one starts')
run_frames(sim, 31)
eq(ev(sim, 'stop'), [('stop', 100)], 'switch over a playing song: the old one stops after its fade')
ok(any(i for i, a in sim.playing.items() if a == SIDEB), 'switch over a playing song: the new one plays on')

# the same song started again during a fade: only the old copy stops
sim.mlog.clear(); sim.playing.clear(); start_song(sim)
sim.run('knight_mus_cut(10); knight_mus_switch(100, 20);')
Y = sim.eval('global.batmusic[1]')
run_frames(sim, 11)
eq(ev(sim, 'stop'), [], 'same song again: not stopped as a whole')
eq(ev(sim, 'istop'), [('istop', 200)], 'same song again: only the old copy stops')
ok(Y in sim.playing, 'same song again: the new copy plays on')

# ======================= Tag Team: the knight who takes over brings their own song =======================
SONGS = {'base': 'knight.ogg', 'elec': 'superchargedknight/cleaver.ogg', 'thorn': 'thorn_knight.ogg', 'cyan': 'its_nothing_but_garbage_noise.ogg',
         'violet': 'knight.ogg'}
EXIST = set(SONGS.values())


def tag(host, partner, song=0):
    sim, e = lu_battle(host, combo=1, partner=partner, extra_cfg='_c.song = %d;' % song)
    ok(e is None, 'tag %s+%s set up (%s)' % (host, partner, e))
    music_mocks(sim, EXIST)
    r = frames(sim, 4)
    ok(r is None and sim.eval('knight_lu_ready()'), 'tag %s+%s: lineup ready (%s)' % (host, partner, r))
    start_song(sim, name=SONGS[host])
    return sim


for host, partner in (('base', 'elec'), ('base', 'thorn'), ('elec', 'cyan'), ('thorn', 'base')):
    sim = tag(host, partner)
    sim.mlog.clear()
    sim.run('knight_lu_ko();')
    eq(sim.eval('global.knight_lu.want'), 1, '%s+%s: the partner takes over' % (host, partner))
    eq(sim.mlog, [('vol', 200, 0, 30)], '%s+%s KO: the old song fades out over a second' % (host, partner))
    run_frames(sim, 31)
    eq(ev(sim, 'stop') + ev(sim, 'free'), [('stop', 100), ('free', 100)], '%s+%s: then it is stopped and freed' % (host, partner))
    eq(ev(sim, 'init'), [], '%s+%s: the new song not yet' % (host, partner))
    run_frames(sim, 2)
    ini = ev(sim, 'init')
    eq([i[1] for i in ini], [SONGS[partner]], '%s+%s: %s starts' % (host, partner, SONGS[partner]))
    if ini:
        S = ini[0][2]
        lp = ev(sim, 'loop')
        ok(lp and lp[-1][1] == S, '%s+%s: its copy loops' % (host, partner))
        if lp:
            I = lp[-1][2]
            ok(('vol', I, 0, 0) in sim.mlog and ('vol', I, 1, 60) in sim.mlog, '%s+%s: from silence, fading in over two seconds' % (host, partner))
            eq(sim.py(sim.eval('global.batmusic')), [S, I], '%s+%s: it is the battle song now' % (host, partner))
    eq(sim.eval('array_length(global.knight_mus_q)'), 0, '%s+%s: nothing left pending' % (host, partner))

# the same song (Normal and Violet both play knight.ogg): nothing changes
sim = tag('base', 'violet')
sim.mlog.clear()
sim.run('knight_lu_ko();')
run_frames(sim, 40)
eq(sim.mlog, [], 'base+violet: the same song plays on')

# a chosen song plays through
sim = tag('base', 'elec', song=1)
sim.mlog.clear()
sim.run('knight_lu_ko();')
run_frames(sim, 40)
eq(sim.mlog, [], 'chosen song: no change at the takeover')

# the battle is over before the new song is due (the results freeze the game): no new song; leaving stops the old one
sim = tag('base', 'elec')
sim.mlog.clear()
sim.run('knight_lu_ko(); obj_battlecontroller.intro = 2;')
run_frames(sim, 40)
eq(sim.eval('global.knight_frozen'), 1, 'battle over: the results are up (game frozen)')
eq(ev(sim, 'init') + ev(sim, 'loop'), [], 'battle over: no new song')
sim.run('knight_mus_reset();')   # what leaving / restarting does first
eq(ev(sim, 'stop'), [('stop', 100)], 'battle over, leaving: the old song is stopped')
eq(ev(sim, 'init') + ev(sim, 'loop'), [], 'battle over, leaving: still no new song')

# the lineup is gone (left / restarted) before the new song is due
sim = tag('base', 'elec')
sim.mlog.clear()
sim.run('knight_lu_ko(); knight_lu_clear();')
run_frames(sim, 40)
eq(ev(sim, 'init'), [], 'lineup gone: no new song')

# ======================= Violet's Side B in the Weird Route (the real merged Violet code) =======================
OBJ = {1: 'obj_herokris', 2: 'obj_herosusie', 3: 'obj_heroralsei', 4: 'obj_heronoelle'}


def vsetup(party, phase):
    sim = mk('violet', party); emu_atk.LAST = sim
    sim.define_object('obj_dummy_bl'); sim.define_const('violetknight_sideb', SIDEB)
    sim.calls = []
    for _m in ['scr_84_get_sprite', 'scr_84_get_font', 'scr_speaker', 'scr_damage_enemy', 'scr_spellmenu_setup', 'scr_endcombat', 'scr_spellget',
               'scr_mnendturn', 'knight_battle_won', 'scr_enemyblcon', 'scr_nextact', 'scr_attackphase', 'scr_battletext', 'scr_battletext_default']:
        sim.mock(_m, 0)
    sim._snapauto = True
    sim.run('global.charinstance = [noone, noone, noone]; global.battlemag = [6,6,6]; global.battleat = [12,12,12];')
    made = {}
    for i, c in enumerate(party):
        if c in OBJ:
            if c not in made:
                auto(sim, lambda: sim.run('global.HI = instance_create(100 + %d * 10, 100 + %d * 40, %s);' % (i, i, OBJ[c])))
                made[c] = sim.eval('global.HI')
            sim.run('global.charinstance[%d] = %d; with (%d) { if (!variable_instance_exists(id, "myself")) myself = %d; }' % (i, made[c], made[c], i))
    IDL = {1: 'spr_krisb_idle', 2: 'spr_susieb_idle', 3: 'spr_ralsei_idle', 4: 'spr_noelleb_idle'}
    for c in made:
        sim.run('with (%s) { idlesprite = %s; attacksprite = %s; }' % (OBJ[c], IDL[c], IDL[c]))
    sim.run('global.flag[456]=1; global.char=[%d,%d,%d];' % tuple(party))
    for i in (1, 2, 3, 4):
        sim.run('global.hp[%d]=140; global.maxhp[%d]=140;' % (i, i))
    sim.run('global.monster=[1,0,0];global.monsterattackname=["","",""];global.monstername=["","",""];global.monstergold=[0,0,0,0];global.monsterexp=[0,0,0,0];'
            'global.monsterdef=[0,0,0];global.monsterinstance=[0,0,0];global.monsterhp=[99999,0,0];global.monstermaxhp=[99999,0,0];global.monsterat=[10,0,0];'
            'global.monsterdf=[0,0,0];global.monstertype=[0,0,0];global.monsterstatus=[0,0,0];global.charcantarget=[1,1,1];global.targeted=[0,0,0,0,0];'
            'global.charaction=[0,0,0];global.charspecial=[0,0,0];global.chartarget=[0,0,0];global.acting=[0,0,0,0,0];global.faceaction=[0,0,0];global.charmove=[0,0,0];'
            'global.mnfight=1.5;global.inv=0;global.invc=1;global.turntimer=0;global.TT_f=0;global.TT_end=-1;global.TT_active=0;global.bmenuno=0;global.myfight=0;'
            'global.fighting=0;global.msc=0;global.typer=5;global.battleactcount=[0,0,0];global.batmusic=[0,0];')
    for nm in ['canact', 'actname', 'actdesc', 'actcost', 'actsimul', 'actactor']:
        for sfx in ['', 'sus', 'ral', 'noe']:
            z = '""' if nm in ('actname', 'actdesc') else '0'
            sim.run('global.%s%s = [[%s]];' % (nm, sfx, ','.join([z] * 6)) + 'for (var _m = 1; _m < 3; _m++) global.%s%s[_m] = [%s];' % (nm, sfx, ','.join([z] * 6)))
    sim.run('global.actingsingle=[0,0,0,0]; global.actingsimul=[0,0,0,0]; global.actingtarget=[0,0,0,0]; global.currentactingchar=0; global.charauto=[0,0,0,0,0]; global.chardead=[0,0,0]; global.monsterinstance=[noone,noone,noone];')
    sim.run('global.canactsus[0][0] = 1; global.actnamesus[0][0] = "S-Action"; global.canactral[0][0] = 1; global.actnameral[0][0] = "R-Action"; global.canactnoe[0][0] = 1; global.actnamenoe[0][0] = "N-Action";')
    sim.run('global.canact[0][0] = 1; global.actname[0][0] = "Check"; global.canact[0][1] = 1; global.actname[0][1] = "HoldBreath";')
    good, err = auto(sim, lambda: sim.run('with(obj_battlecontroller) instance_destroy(); instance_create(0,0,obj_battlecontroller); '
                                         'global.K=instance_create(300,100,obj_knight_enemy); global.K.myself=0; instance_create(300,300,obj_heart); knight_ensure_ctrl();'))
    assert good, err
    sim.run('with (global.K) knight_hb_setup("violet");')
    sim.run('global.K.phase=%d; global.K.phaseturn=0; global.K.turn=0; global.mnfight=99; global.myfight=99; global.charturn=-1; global.K.attackchosen=false; '
            'global.K.talked=1; global.K.rtimer=0; global.K.myblcon=instance_create(0,0,obj_dummy_bl); with(obj_herokris) myself=0;' % phase)
    music_mocks(sim)
    start_song(sim)
    return sim


def vkill(sim, n, maxf=5000):
    """loss n the way the fight starts it; runs until the scene is over. Returns (states seen, frame of each sound call, error)"""
    sim.run('with (global.K) { knightkillcon = 2; kill_target = knight_vb_victim(%d); }' % n)
    seen = []; last = None; at = []
    for f in range(maxf):
        before = len(sim.mlog)
        good, err = auto(sim, lambda: sim.step(1))
        for x in sim.mlog[before:]:
            if (f, x) not in at:     # (the emulator re-runs a frame after filling in a missing variable: one call per frame)
                at.append((f, x))
        if not good:
            return seen, at, 'ERR %s' % err
        k = sim.eval('global.K.knightkillcon')
        if k != last:
            seen.append(k); last = k
        if k == 0 and f > 5:
            # let a pending stop run out
            for g in range(40):
                before = len(sim.mlog)
                auto(sim, lambda: sim.step(1))
                at += [(f + 1 + g, x) for x in sim.mlog[before:]]
            break
    return seen, at, None


def check_sideb(tag, at, cut_expected=True):
    calls = [x for _, x in at]
    if cut_expected:
        fade = [(f, x) for f, x in at if x == ('vol', 200, 0, 10)]
        ok(len(fade) == 1, '%s: at the blow the battle song fades out over a third of a second (%s)' % (tag, calls[:6]))
        stops = [(f, x) for f, x in at if x == ('stop', 100)]
        ok(len(stops) >= 1, '%s: and is stopped when the fade is over (%s)' % (tag, calls[:8]))
        if fade and stops:
            ok(stops[0][0] - fade[0][0] >= 10, '%s: not before the fade is over (frames %d -> %d)' % (tag, fade[0][0], stops[0][0]))
        first = calls[0] if calls else None
        eq(first, ('vol', 200, 0, 10), '%s: no dead stop first' % tag)
    lp = [x for x in calls if x[0] == 'loop']
    eq([x[1] for x in lp], [SIDEB], '%s: the Side B song starts once' % tag)
    if lp:
        X = lp[0][2]
        i = calls.index(lp[0])
        eq(calls[i + 1:i + 3], [('vol', X, 0, 0), ('vol', X, 1, 60)], '%s: from silence, fading in over two seconds' % tag)
        eq(sim.py(sim.eval('global.batmusic')), [SIDEB, X], '%s: Side B is the battle song' % tag)
    ok(not [k for k, v in sim.playing.items() if v == 100], '%s: the old song does not play on under Side B' % tag)


# Kris on top, Susie, Ralsei at the bottom: the mod's own Kris path (Ralsei falls)
sim = vsetup([1, 2, 3], 2)
seen, at, err = vkill(sim, 1)
ok(err is None, 'KSR loss 1 runs (%s)' % err)
check_sideb('KSR (mod path)', at)

# no Kris: Ralsei on top, Noelle at the bottom: the hub's path (the Angel falls)
sim = vsetup([3, 4, 0], 2)
seen, at, err = vkill(sim, 1)
ok(err is None, 'RN loss 1 runs (%s)' % err)
check_sideb('RN (hub path)', at)

# no Kris: Ralsei on top, Susie at the bottom: Susie falls (the fight never stopped the song for her) - crossfade, never both
sim = vsetup([3, 2, 0], 2)
seen, at, err = vkill(sim, 1)
ok(err is None, 'RS loss 1 runs (%s)' % err)
calls = [x for _, x in at]
ok(('vol', 200, 0, 30) in calls, 'RS (Susie falls): the battle song fades out under the Side B song (%s)' % calls[:6])
check_sideb('RS (Susie falls)', at, cut_expected=False)

# Susie alone: she parries (nobody falls): the song still fades at the charge, Side B fades in
sim = vsetup([2, 0, 0], 2)
seen, at, err = vkill(sim, 1)
ok(err is None and 95 in seen, 'S alone loss 1: parry (%s) %s' % (seen[:8], err))
check_sideb('S alone (parry)', at)

print('music tests', N[0], 'fails', len(FAILS), '%.1f' % (time.time() - t0))
sys.exit(1 if FAILS else 0)
