"""DRBR (update 10): the DRBR install's save profile (drbr_save54.gml), in the emulator with the real merged code.
The save folder (%LOCALAPPDATA%\\DELTARUNE) is the sim's sandbox, pre-filled with stand-ins for the player's own DELTARUNE
saves; the DRBR install's chapter3_windows is the sim's read-only BUNDLE (drbr_data/drbr_profile.cfg + start_filech3 =
the provided save, byte for byte). Checks: DRBR mode only with the cfg; which names are redirected; the start (the
provided save copied into drbr_profile/ and loaded: story point 320, room 30108 = room_dw_snow_zone, the party, the
name); the start report the launcher reads; the game's own SAVE goes to drbr_profile/ only; a relaunch starts from the
provided save again (template) or keeps a valid DRBR save (continue); a damaged / missing / unknown starting save stops
the start with a message and writes nothing; the chapter switch restarts instead of leaving; without the cfg (the
in-place Knight Hub) nothing changes. The player's own files are compared byte for byte after every step.
Usage: python3 t_drbr_save54.py"""
import sys, os, hashlib, shutil, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('WALL', '300')
from emu_atk import *

SAVE = os.environ.get('DRBR_SAVE', '/home/claude/work/installer/extra/Save file/filech3_2')
TEMPLATE_SHA256 = 'fa956269ee3ee98e7df04356bb575e3afd5455a538bb5568b2ac931fdb0aa082'
FAILS = []
N = [0]


def ok(c, msg):
    N[0] += 1
    print(('ok   ' if c else 'FAIL ') + msg, flush=True)
    if not c:
        FAILS.append(msg)


def sha(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()


tpl = open(SAVE, 'rb').read()
ok(hashlib.sha256(tpl).hexdigest() == TEMPLATE_SHA256, 'the starting save used here is the provided one (sha256 %s)' % TEMPLATE_SHA256[:16])

CFG = ('# DRBR save profile (written by DRBR Launcher; read by the game when it starts)\r\n'
       'schema_version=1\r\nprofile=drbr_default\r\nstarting_location=room_dw_snow_zone\r\nstarting_room_id=30108\r\n'
       'starting_plot=320\r\nsave_template_version=1\r\nsave_template_sha256=%s\r\nstart_mode=%%s\r\nmigration_version=1\r\n' % TEMPLATE_SHA256)


def make_bundle(mode='template', template=tpl, cfg=True):
    d = tempfile.mkdtemp(prefix='drbr_bundle_')
    os.makedirs(os.path.join(d, 'drbr_data'))
    if cfg:
        open(os.path.join(d, 'drbr_data', 'drbr_profile.cfg'), 'wb').write((CFG % mode).encode())
    if template is not None:
        open(os.path.join(d, 'drbr_data', 'start_filech3'), 'wb').write(template)
    return d


def vanilla_fill(root):
    """stand-ins for the player's own saves (other content than the template), and the mod's own settings"""
    other = tpl.replace(b'ENDER', b'KRISS')
    files = {'filech3_0': other, 'filech3_1': other[:-5] + b'99999', 'filech3_9': other, 'filech3_3': other,
             'filech2_0': b'chapter 2 save\r\n', 'dr.ini': b'[G3_0]\r\nName="KRISS"\r\nLevel=1.000000\r\n',
             'keyconfig_0.ini': b'[KEYBOARD_CONTROLS]\r\n0=40.000000\r\n', 'config_0.ini': b'[x]\r\ny=1\r\n',
             'true_config.ini': b'[LANG]\r\nLANG="en"\r\n', 'knight_hub.ini': b'[hub]\r\nx=1\r\n',
             'knightfights_online.ini': b'[online]\r\nskin=3\r\n', 'keyconfig_mod.ini': b'[m]\r\nk=1\r\n'}
    for k, v in files.items():
        open(os.path.join(root, k), 'wb').write(v)
    return {k: hashlib.sha256(v).hexdigest() for k, v in files.items()}


def vanilla_same(root, before, what):
    now = {k: (sha(os.path.join(root, k)) if os.path.isfile(os.path.join(root, k)) else None) for k in before}
    # (the mod's own settings - knight_hub.ini and its .bak copy, knightfights_*.ini - are the mod's to keep up to date)
    bad = sorted(k for k in before if now[k] != before[k] and not k.startswith(('knight_hub.', 'knightfights_')))
    extra = sorted(f for f in os.listdir(root) if os.path.isfile(os.path.join(root, f)) and f not in before
                   and not f.startswith(('knight_hub.', 'knightfights_', 'knighthub_')))
    ok(not bad and not extra, "%s: the player's own files are untouched and nothing new is written next to them %r" % (what, (bad, extra)))


sim = mk('base', [1, 2, 3])
# a retry after an auto-defined missing name restores the state first (kdr_boot runs once per start)
sim._snapauto = True
for _m in ('snd_free_all', 'audio_group_set_gain', 'audio_set_master_gain', 'scr_84_get_sprite', 'scr_84_get_font'):
    sim.mock(_m, 0)
for o in ('obj_persistentfadein', 'obj_mainchara', 'obj_gamecontroller'):
    try:
        sim.define_object(o)
    except Exception:
        pass
# every room of the built game (scr_get_room_by_id names them all), in the built game's order
for _ln in open('/home/claude/work/idx/merged.tsv', encoding='utf8'):
    _p = _ln.rstrip('\n').split('\t')
    if len(_p) >= 3 and _p[0] == 'room' and _p[2] not in sim.rooms:
        sim.define_room(_p[2])
# (a newer GameMaker's console constant Chapter 3's scr_is_switch_os reads; os_type stays os_windows = 0)
try:
    sim.define_const('os_switch2', 9902)
except Exception:
    pass
GR = []
sim.mock('game_restart', lambda sm, *a: GR.append(1) or 0)
GC = []
sim.mock('game_change', lambda sm, *a: GC.append(a) or 0)
MSG = []
sim.mock('show_message', lambda sm, *a: MSG.append(str(a[0]) if a else '') or 0)
root = sim.fs.root
# the controls the game keeps (obj_gamecontroller makes them arrays at the start; scr_save writes them)
sim.run('global.input_k = array_create(10, 0); global.input_g = array_create(10, 0);')
# the game controller the save code reads (scr_save: its shoulder-button setting; scr_load: enable_loading)
sim.run('global.GCI = instance_create(40, 0, obj_gamecontroller); with (global.GCI) { gamepad_shoulderlb_reassign = 0; enable_loading = function() { return 0; }; }')
print('save folder (sandbox):', root)
before = vanilla_fill(root)


def fresh(mode='template', template=tpl, cfg=True):
    """a new launch: a new bundle, the DRBR globals forgotten (the game starts again)"""
    sim.fs.bundle = make_bundle(mode, template, cfg)
    sim.run('if (variable_global_exists("kdr_mode")) { global.kdr_mode = undefined; } global.kdr_booted = 0;')
    sim.run('global.kdr_mode = 0; global.__kdr_reset = 1;')
    # (the battle scaffolding of mk() left global.msg a string; the real game has it an array when scr_gamestart runs)
    sim.run('global.msg = [];')
    # kdr_on() detects again when kdr_mode is missing: emulate a fresh process by removing it
    sim.globals.pop('kdr_mode', None)
    sim.pending_room = None
    sim.game_ended = False
    MSG.clear()
    GR.clear()
    GC.clear()


def run(code):
    good, err = auto(sim, lambda: sim.run(code))
    return good, err


def ini(path):
    import configparser
    cp = configparser.ConfigParser(interpolation=None, strict=False)
    cp.read_string(open(path, encoding='utf8', errors='replace').read())
    return cp


LIVE = os.path.join(root, 'drbr_profile', 'filech3_0')
LOG = os.path.join(root, 'drbr_profile', 'last_start.ini')
SNOW = sim.eval('room_dw_snow_zone')

# ---- 1. DRBR mode is on only with the cfg in the bundle
fresh(cfg=False)
ok(sim.eval('kdr_on()') in (0, False), 'no drbr_data/drbr_profile.cfg next to data.win (the in-place Knight Hub): DRBR mode is off')
ok(sim.eval('kdr_path("filech3_0")') == 'filech3_0' and sim.eval('kdr_path("dr.ini")') == 'dr.ini', 'DRBR mode off: story files keep their own names')
fresh()
ok(sim.eval('kdr_on()') in (1, True), 'drbr_data/drbr_profile.cfg in the bundle: DRBR mode is on')
ok(sim.eval('kdr_cfg_get("start_mode", "")') == 'template' and sim.eval('kdr_cfg_get("starting_room_id", "")') == '30108', 'the cfg is read (CRLF lines, comments skipped) %r' % sim.eval('kdr_cfg_get("start_mode", "?")'))

# ---- 2. which names go to drbr_profile/
cases = {'filech3_0': 'drbr_profile/filech3_0', 'filech3_9': 'drbr_profile/filech3_9', 'filech3_5': 'drbr_profile/filech3_5',
         'filech2_3': 'drbr_profile/filech2_3', 'dr.ini': 'drbr_profile/dr.ini', 'DR.INI': 'drbr_profile/DR.INI',
         'keyconfig_0.ini': 'drbr_profile/keyconfig_0.ini', 'keyconfig_12.ini': 'drbr_profile/keyconfig_12.ini',
         'config_2.ini': 'drbr_profile/config_2.ini', 'keyconfig_mod.ini': 'keyconfig_mod.ini', 'knight_hub.ini': 'knight_hub.ini',
         'knight_hub.bak': 'knight_hub.bak', 'knightfights_online.ini': 'knightfights_online.ini', 'true_config.ini': 'true_config.ini',
         'drbr_profile/filech3_0': 'drbr_profile/filech3_0', 'lang/lang_ja.json': 'lang/lang_ja.json', 'keyconfig_.ini': 'keyconfig_.ini',
         'config_x.ini': 'config_x.ini', 'susieplayback.ini': 'susieplayback.ini'}
got = {k: sim.eval('kdr_path("%s")' % k) for k in cases}
bad = {k: (got[k], v) for k, v in cases.items() if got[k] != v}
ok(not bad, 'story files (filechN_M, dr.ini, keyconfig_N.ini, config_N.ini) go to drbr_profile/, the mod\'s and the game\'s settings do not %r' % bad)

# ---- 3. the start: the provided save, copied and loaded
good, err = run('global.R = kdr_boot();')
ok(good and sim.eval('global.R') in (1, True), 'kdr_boot() starts the game in DRBR mode %r' % (err,))
ok(os.path.isfile(LIVE) and sha(LIVE) == TEMPLATE_SHA256, 'drbr_profile/filech3_0 is the provided save, byte for byte')
ok(sim.eval('global.plot') == 320 and sim.eval('global.currentroom') == 30108, 'loaded: story point 320, room id 30108 (%r, %r)' % (sim.eval('global.plot'), sim.eval('global.currentroom')))
ok(sim.pending_room == SNOW, 'the game goes to room_dw_snow_zone, the room before the Roaring Knight (%r vs %r)' % (sim.pending_room, SNOW))
party = [sim.eval('global.char[%d]' % i) for i in range(3)]
ok(party == [1, 2, 3] and sim.eval('global.truename') == 'ENDER', 'the save\'s party (Kris, Susie, Ralsei) and name %r' % ([party, sim.eval('global.truename')],))
ok(sim.eval('global.filechoice') == 0 and sim.eval('global.tempflag[10]') == 1, 'as the file menu\'s CONTINUE does: slot 0, tempflag 10')
hp = [sim.eval('global.hp[%d]' % i) for i in range(1, 5)]
ok(hp == [160, 190, 140, 120], 'the party\'s HP from the save %r' % hp)
ok(not MSG and not sim.game_ended, 'no error message, the game goes on %r' % MSG)
lg = ini(LOG)
ok(lg.get('start', 'result').strip('"') == 'loading' and lg.get('start', 'from').strip('"') == 'template' and float(lg.get('start', 'template_version').strip('"')) == 1,
   'last_start.ini: loading the provided save (template version 1) %r' % dict(lg['start']))
vanilla_same(root, before, 'the DRBR start')

# ---- 4. the first room is written down for the launcher
sim.room_index = SNOW
sim.pending_room = None
run('with (obj_mainchara) instance_destroy(); instance_create(120, 240, obj_mainchara);')
for _ in range(3):
    run('kdr_frame();')
lg = ini(LOG)
st = {k: v.strip('"') for k, v in lg['start'].items()}
ok(st.get('result') == 'ok' and st.get('room') == 'room_dw_snow_zone' and float(st.get('room_id', 0)) == 30108 and float(st.get('plot', 0)) == 320,
   'last_start.ini after the room loads: ok, room_dw_snow_zone, 30108, story point 320 %r' % st)
ok(float(st.get('x', -9)) == 120 and float(st.get('y', -9)) == 240, 'the player stands where the room puts them after a load (120, 240) %r' % ([st.get('x'), st.get('y')],))

# ---- 5. the game's own SAVE (a save point) writes into drbr_profile/ only
run('global.plot = 320; global.lv = 1;')
good, err = run('scr_save();')
ok(good, 'scr_save() runs %r' % (err,))
wrote = sorted(os.listdir(os.path.join(root, 'drbr_profile')))
ok({'filech3_0', 'filech3_9', 'dr.ini', 'keyconfig_0.ini'} <= set(wrote), 'the SAVE wrote filech3_0, filech3_9 (its copy), dr.ini and keyconfig_0.ini into drbr_profile/ %r' % wrote)
ok(sim.eval('kdr_check_save("drbr_profile/filech3_0")') == '', 'the DRBR save written by the game is a whole Chapter 3 save (%r)' % sim.eval('kdr_check_save("drbr_profile/filech3_0")'))
d_ini = open(os.path.join(root, 'drbr_profile', 'dr.ini'), encoding='utf8', errors='replace').read()
ok('ENDER' in d_ini, 'drbr_profile/dr.ini names the DRBR slot (the save\'s name ENDER)')
vanilla_same(root, before, 'the game\'s SAVE in DRBR')

# ---- 6. GAME OVER -> CONTINUE: scr_load reads the DRBR save
run('global.plot = 0; global.currentroom = 0;')
good, err = run('scr_load();')
ok(good and sim.eval('global.plot') == 320 and sim.pending_room == SNOW, 'a load (game over -> continue) reads drbr_profile/filech3_0 %r' % (err,))

# ---- 7. a relaunch in template mode starts from the provided save again, even after a later DRBR save
run('global.plot = 340; global.currentroom = 30108;')
run('scr_saveprocess(0);')
ok(sim.eval('kdr_check_save("drbr_profile/filech3_0")') == '' and b'340 ' in open(LIVE, 'rb').read(), 'a DRBR save at story point 340 (after the Knight) was written')
fresh('template')
good, err = run('global.R = kdr_boot();')
ok(good and sha(LIVE) == TEMPLATE_SHA256 and sim.eval('global.plot') == 320, 'relaunch (template): back to the provided save, story point 320 %r' % (err,))
vanilla_same(root, before, 'a relaunch')

# ---- 8. continue mode keeps a valid DRBR save, and falls back to the provided save when it is not
run('global.plot = 340; scr_saveprocess(0);')
fresh('continue')
good, err = run('global.R = kdr_boot();')
ok(good and sim.eval('global.plot') == 340 and sim.eval('global.kdr_from') == 'continue', 'continue mode: the DRBR save (story point 340) is loaded %r' % ([sim.eval('global.plot'), sim.eval('global.kdr_from'), err],))
raw = open(LIVE, 'rb').read()
open(LIVE, 'wb').write(raw[: len(raw) // 2])
fresh('continue')
good, err = run('global.R = kdr_boot();')
ok(good and sim.eval('global.kdr_from') == 'template' and sha(LIVE) == TEMPLATE_SHA256 and sim.eval('global.plot') == 320,
   'continue mode with a cut-off DRBR save: the provided save is used instead (no crash) %r' % ([sim.eval('global.kdr_from'), err],))
open(LIVE, 'wb').write(raw.replace(b'30108 ', b'99999 '))
fresh('continue')
run('global.R = kdr_boot();')
ok(sim.eval('global.kdr_from') == 'template' and sim.eval('global.plot') == 320, 'continue mode with a save naming no Chapter 3 room: the provided save instead')

# ---- 9. a damaged / unknown / missing starting save: a message, the game ends, nothing is loaded or written
for what, t in (('one byte changed', tpl[:100] + bytes([tpl[100] ^ 1]) + tpl[101:]), ('another save (unknown hash)', tpl.replace(b'ENDER', b'NOELL')),
                ('empty', b''), ('missing', None)):
    open(LIVE, 'wb').write(tpl)
    live0 = sha(LIVE)
    fresh('template', template=t)
    good, err = run('global.R = kdr_boot();')
    ok(good and sim.game_ended and MSG and 'DRBR could not start' in MSG[0] and 'Repair'.upper() in MSG[0].upper() and sim.pending_room is None and sha(LIVE) == live0,
       'starting save %s: a clear message (REPAIR), the game ends, nothing loaded or overwritten %r' % (what, (MSG[:1], err)))
    lg = ini(LOG)
    ok(lg.get('start', 'result').strip('"') == 'error' and 'starting save' in lg.get('start', 'error'), '  ... and last_start.ini says error: %s' % lg.get('start', 'error')[:90])
vanilla_same(root, before, 'the failed starts')

# ---- 10. the chapter switch restarts at the DRBR start instead of leaving for a chapter the DRBR install does not have
fresh('template')
run('kdr_on();')
good, err = run('scr_chapterswitch(4);')
ok(good and GR and not GC, 'scr_chapterswitch(4) in DRBR: game_restart(), no game_change %r' % ((GR, GC, err),))
good, err = run('scr_chapterswitch(0);')
ok(good and len(GR) == 2 and not GC, 'scr_chapterswitch(0) (the chapter select) in DRBR: game_restart() too')

# ---- 11. the controls of the DRBR slot are loaded at the start
open(os.path.join(root, 'drbr_profile', 'keyconfig_0.ini'), 'wb').write(b'[KEYBOARD_CONTROLS]\r\n4=90.000000\r\n')
fresh('template')
run('global.input_k[4] = 13; global.R = kdr_boot();')
ok(sim.eval('global.input_k[4]') == 90, 'the DRBR slot\'s controls (drbr_profile/keyconfig_0.ini) are loaded (%r)' % sim.eval('global.input_k[4]'))

# ---- 12. not a DRBR install: the game's own behaviour (the in-place Knight Hub)
fresh(cfg=False)
good, err = run('global.R = kdr_boot();')
ok(good and sim.eval('global.R') in (0, False) and sim.pending_room is None, 'no cfg: kdr_boot() does nothing, the intro / file menu run as before')
good, err = run('scr_chapterswitch(4);')
ok(good and GC and not GR, 'no cfg: the chapter switch is the game\'s own (game_change)')
good, err = run('global.filechoice = 2; scr_saveprocess(2);')
ok(good and os.path.isfile(os.path.join(root, 'filech3_2')), 'no cfg: a save goes where the game always put it (filech3_2 next to the others)')
os.remove(os.path.join(root, 'filech3_2'))

# ---- 13. a newer room before an update -> after the update the invite box offers it (the player decides)
fresh('template')
run('kdr_on();')
PJ = os.path.join(root, 'drbr_profile', 'pending_join.ini')
if os.path.exists(PJ):
    os.remove(PJ)
good, err = run('global.KV = kfo_version(); kdr_pending_join("109775241234567890", global.KV + 1, "Tester");')
kv = sim.eval('global.KV')
ok(good and os.path.isfile(PJ), 'a room with a newer build is written down (drbr_profile/pending_join.ini) %r' % (err,))
pj = ini(PJ)
ok(pj.get('join', 'lobby').strip('"') == '109775241234567890' and int(float(pj.get('join', 'their_build'))) == kv + 1, '  ... its lobby number and build only %r' % dict(pj['join']))
ok('DRBR Launcher' in sim.eval('kdr_build_why(%d)' % (kv + 1)) and 'older DRBR' in sim.eval('kdr_build_why(%d)' % (kv - 1)), 'the messages say how to update / that the others must update')
good, err = run('global.PO = kdr_pending_offer();')
ok(good and sim.eval('global.PO') in (0, False) and not os.path.exists(PJ), 'still the old build (no update happened): nothing offered, the note is dropped')
run('kdr_pending_join("109775241234567890", global.KV, "Tester");')
good, err = run('global.PO = kdr_pending_offer(); global.IV = kfo_get().inv_in;')
iv = sim.py(sim.eval('global.IV')) if good else None
ok(good and sim.eval('global.PO') in (1, True) and isinstance(iv, dict) and iv.get('lobby') == '109775241234567890' and iv.get('back') in (1, True) and iv.get('shown') in (0, False),
   'after the update (same build now): the room is offered with the invite box (JOIN / NOT NOW) %r' % ((err, iv),))
ok(not os.path.exists(PJ), '  ... and the note is used up')
run('kdr_pending_join("1", global.KV, "");')
c = ini(PJ)
c.set('join', 'stamp', '1.0')
with open(PJ, 'w') as fh:
    c.write(fh)
good, err = run('kfo_get().inv_in = undefined; global.PO = kdr_pending_offer();')
ok(good and sim.eval('global.PO') in (0, False), 'a note older than an hour is not offered')
fresh(cfg=False)
if os.path.exists(PJ):
    os.remove(PJ)
run('kdr_pending_join("5", 99, "x");')
ok(not os.path.exists(PJ), 'not a DRBR install: nothing is written')
ok('Knight Hub build' in sim.eval('kdr_build_why(%d)' % (kv + 1)), 'not a DRBR install: the old message')

# ---- 14. the mod's name as the player sees it: DRBR in the DRBR install; the in-place Knight Hub keeps its own texts
TXT = []
sim.mock('draw_text', lambda sm, *a: TXT.append(str(a[2]) if len(a) > 2 else '') or 0)


def names():
    TXT.clear()
    sim.room_index = SNOW
    good_, err_ = run('global.plot = 340; global.knight_run = 0; global.HD = knight_hub_hint_draw();')
    return {'stamp': sim.eval('knight_build_stamp()'), 'name': sim.eval('kdr_name()'),
            'older': sim.eval('kfo_refusal_text("Client Is Older")'), 'newer': sim.eval('kfo_refusal_text("Client Is Newer")'),
            'host': sim.eval('kdr_other_build(true, "The room\'s host has")'), 'hint': list(TXT), 'err': err_}


fresh(cfg=False)
n0 = names()
ok(n0['stamp'].startswith('KNIGHT HUB V2 - BUILD %d - ' % kv) and n0['name'] == 'Knight Hub'
   and n0['older'] == "The room's players have a newer Knight Hub build." and n0['newer'] == "The room's players have an older Knight Hub build."
   and n0['host'] == "The room's host has a newer Knight Hub build." and n0['hint'][:1] == ['KNIGHT HUB: no sign with this save.'],
   'not a DRBR install: the Knight Hub\'s own names and messages, word for word %r' % n0)
fresh('template')
n1 = names()
ok(n1['stamp'].startswith('DRBR - BUILD %d - ' % kv) and n1['name'] == 'DRBR', 'DRBR: the build stamp on every page of the sign\'s menu says DRBR (%s)' % n1['stamp'])
ok('newer DRBR' in n1['older'] and 'DRBR Launcher' in n1['older'] and 'older DRBR' in n1['newer'] and 'DRBR Launcher' in n1['host'],
   'DRBR: a room or host with another build says how to update %r' % [n1['older'], n1['newer'], n1['host']])
ok(n1['hint'][:1] == ['DRBR: no hub sign with this save.'] and any('DRBR Launcher' in t for t in n1['hint']),
   'DRBR: a later DRBR save without the sign says so and how to get back to the starting save %r' % ((n1['hint'], n1['err']),))

print('%d checks, %d failed' % (N[0], len(FAILS)))
for f_ in FAILS:
    print('FAILED:', f_)
sys.exit(1 if FAILS else 0)
