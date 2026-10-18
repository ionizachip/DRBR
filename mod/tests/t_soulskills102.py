"""DRBR 1.0.2 - your report: "you can't use skills with other SOUL types". In a practice match against each boss, one of his
attacks forced (the SOUL mode on: Gerson's green, Flowery's orange board, Pink's purple lanes / tunnel, Spamton NEO's
yellow), with the real keys (KEYBINDS defaults): the TP charge fills over time, C charges and draws a skill, and holding
USE (Z; on the orange / yellow SOUL HOLD BREATH's key, S - the SOUL itself uses Z there) uses the picked skill. And where USE
went is on screen there: "SKILLS: HOLD S" beside the skill slots ("S / LT" with a controller: HOLD BREATH's left trigger),
the SOUL hint under the box, a blink when Z is held with a skill ready (Z itself uses no skill there), and the KEYBINDS page.
Usage: python3 t_soulskills102.py [boss:attack ...]"""
import sys, os, json, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('KH_CAM', '1000,320')
from br_harness import *
sys.path.insert(0, '/home/claude/work/uiref')
from uiharness import Recorder

FAILS = []
N = [0]
ROWS = {'jevil': 6, 'gerson': 7, 'flowery': 8, 'spamton': 9, 'pink': 10}
# (Spamton's Heart Attack, 780 frames: the checks take about 280 frames of one attack - his first is 270 long)
CASES = [('jevil', 4), ('gerson', 2), ('flowery', 1), ('pink', 0), ('pink', 7), ('spamton', 2)]
Z, S, C = ord('Z'), ord('S'), ord('C')


def ok(c, msg):
    N[0] += 1
    print(('ok   ' if c else 'FAIL ') + msg, flush=True)
    if not c:
        FAILS.append(msg)
    return c


def J(s, e):
    return s.py(s.eval(e))


SK = ('(function(){ var _M = global.kfo.M; var _S = _M.sk; var _l = []; for (var _i = 0; _i < array_length(_S.slots); _i++) array_push(_l, _S.slots[_i].sid);'
      ' return { sl: _l, used: _S.used, chg: _S.charging, charge: _S.charge, g: _M.g, alive: _M.alive_f, ph: _M.R.ph, heart: instance_exists(obj_heart),'
      ' orange: kbr_orange_on(), usekey: kbr_key_now("use"), cd: _S.cd, can: _M.eff.skills, frozen: global.knight_frozen,'
      ' prompt: instance_exists(obj_knight_prompt), qs: _M.vw.qs }; })()')


def run_case(boss, atk):
    print('== %s attack %d' % (boss, atk), flush=True)
    row = ROWS[boss]
    sim, e = br_match(open_ok=row, kn=(row,), seed=7700 + row, bots=0, setx='_s.mhp = 999; _s.skills = 1;')
    if e:
        ok(False, '%s: the practice match starts (%r)' % (boss, e))
        return
    sim.run('with (obj_battlecontroller) if (!variable_instance_exists(id, "mercytotal")) mercytotal = 0;')
    sim.run('global.SF = %d;' % atk)
    sim.load_source('gml_GlobalScript_sk102force', 'function kbr_tl_pick_attack(_tl, _k, _g, _ok, _st) { return global.SF; }\n')
    sim.run('global.kfo.M.tl.cyc = []; if (is_struct(global.kfo.H)) global.kfo.H.tl.cyc = [];')
    live_input(sim)
    sim.input.begin_frame = lambda fno: None

    def keys(held):
        held = set(held)
        sim.input.pressed = held - sim.input.held
        sim.input.released = sim.input.held - held
        sim.input.held = held
        sim.input.cleared = set()

    def frame(held=()):
        keys(held)
        sim.run('if (!global.kfo.M.out) global.hp[kbr_char()] = global.maxhp[kbr_char()];')
        return step(sim, 1)

    # into the attack, 60 frames
    t_run = 0
    for f in range(2400):
        err = frame()
        if err:
            ok(False, '%s %d: no error before the attack (%s)' % (boss, atk, err[:200]))
            return
        if J(sim, 'global.kfo.M.R.ph') == 'run':
            t_run += 1
            if t_run >= 60:
                break
        else:
            t_run = 0
    s0 = J(sim, SK)
    print('  at 60 frames into the attack:', s0, flush=True)
    # 1. the TP charge fills on its own (about a point a second)
    g0 = s0['g']
    for f in range(90):
        err = frame()
        if err:
            break
    s1 = J(sim, SK)
    ok(not err and s1['g'] > g0, '%s %d: the TP charge fills by itself during the attack (%s -> %s)' % (boss, atk, g0, s1['g']))
    # 2. charge (C held) and draw
    sim.run('global.kfo.M.g = 100; global.kfo.M.sk.slots = []; global.kfo.M.sk.cd = 0;')
    for f in range(50):
        err = frame([C])
        if err:
            break
    s2 = J(sim, SK)
    err = err or frame([])
    s3 = J(sim, SK)
    ok(not err and len(s3['sl']) >= 1, '%s %d: C charges (%s) and draws a skill (slots %r)' % (boss, atk, round(s2['charge'], 1), s3['sl']))
    # 3. use it: USE held 15 frames (Z, or S on the orange / yellow SOUL)
    sim.run('var _S = global.kfo.M.sk; _S.slots = [{ sid: 11, rev: 0 }]; _S.cd = 0; _S.sel = 0; global.hp[kbr_char()] = 1;')
    for f in range(30):
        frame([])
    sim.run('var _S = global.kfo.M.sk; _S.slots = [{ sid: 11, rev: 0 }]; _S.cd = 0; _S.sel = 0;')
    s4 = J(sim, SK)
    uk = s4['usekey']
    for f in range(15):
        err = frame([uk])
        if err:
            break
    s5 = J(sim, SK)
    frame([])
    ok(not err and s5['used'] == s4['used'] + 1 and s5['sl'] == [], '%s %d: holding USE (%s) uses the picked skill (used %d -> %d, slots %r)'
       % (boss, atk, 'Z' if uk == Z else ('S' if uk == S else uk), s4['used'], s5['used'], s5['sl']))
    # 4. DRBR 1.0.2: where USE went is on screen - beside the skill slots all the while, in the SOUL hint under the box - and
    #    holding the usual key (Z) with a skill ready blinks it
    moved = s4['orange']
    sim.run('var _S = global.kfo.M.sk; _S.slots = [{ sid: 11, rev: 0 }]; _S.cd = 0; _S.sel = 0; _S.mv_t = 0;')
    rec = Recorder(sim)
    rec.ops.clear()
    sim.run('kbr_hud_skills(knight_cam_x(), knight_cam_y(), global.kfo.M);')
    texts = [str(o[4]) for o in rec.ops if o[0] == 'text']
    side = 'SKILLS:' in texts and ('HOLD S' in texts or any(t.startswith('HOLD S') for t in texts))
    ok(side == bool(moved), '%s %d: beside the skill slots "SKILLS: HOLD S" %s (texts %r)' % (boss, atk, 'shown (Z is the SOUL\'s here)' if moved else 'not shown (Z uses skills here)', [t for t in texts if 'SKILL' in t or 'HOLD' in t]))
    hint = J(sim, 'kbr_soul_hint_text(kbr_soul_mode())')
    ok(('SKILLS: HOLD S' in hint) == bool(moved), '%s %d: the SOUL hint under the box: %r' % (boss, atk, hint))
    # with a controller in use the label names its button too: HOLD BREATH's, the left trigger (LT - KEYBINDS' own name for it)
    # (a stand-in controller object only for this question when the harness has none: it is gone before the next frame)
    # (Chapter 3's obj_gamecontroller: gamepad_id 0 from its Create, a controller or not - gamepad_active says one is connected)
    sim.run('global.kbr_t_mk = !instance_exists(obj_gamecontroller); if (global.kbr_t_mk) instance_create(0, 0, obj_gamecontroller);'
            ' with (obj_gamecontroller) { kbr_t_gp = variable_instance_exists(id, "gamepad_id") ? gamepad_id : -1;'
            ' kbr_t_ga = variable_instance_exists(id, "gamepad_active") ? gamepad_active : 0; gamepad_id = 0; gamepad_active = 0; }')
    lab0 = J(sim, 'kbr_use_key_label()')
    sim.run('with (obj_gamecontroller) gamepad_active = 1;')
    lab = J(sim, 'kbr_use_key_label()')
    sim.run('with (obj_gamecontroller) { gamepad_id = kbr_t_gp; gamepad_active = kbr_t_ga; } if (global.kbr_t_mk) { with (obj_gamecontroller) instance_destroy(); }')
    ok(lab == ('S / LT' if moved else 'Z') and lab0 == ('S' if moved else 'Z'), '%s %d: with a controller connected the label is %r (HOLD BREATH is LT), with none %r'
       % (boss, atk, lab, lab0))
    if moved:
        for f in range(14):
            err = frame([Z])
        mv = J(sim, 'global.kfo.M.sk.mv_t')
        used = J(sim, 'global.kfo.M.sk.used')
        frame([])
        ok(not err and mv > 0 and used == s5['used'], '%s %d: holding Z (the SOUL\'s) with a skill ready uses none and blinks the label (blink %r)' % (boss, atk, mv))


# the KEYBINDS page says it too
def keybinds():
    sim, e = br_match(open_ok=9, kn=(9,), seed=7709, bots=0, setx='_s.skills = 1;')
    d = J(sim, 'kfo_key_desc("use")')
    ok('Yellow / orange SOUL: on S' in d and d.count('#') == 1 and all(len(l) <= 46 for l in d.split('#')), 'KEYBINDS > USE SKILL says where it goes on the yellow / orange SOUL: %r' % d)


t0 = time.time()
keybinds()
want = [(a.split(':')[0], int(a.split(':')[1])) for a in sys.argv[1:]] or CASES
for b, a in want:
    try:
        run_case(b, a)
    except Exception as ex:
        ok(False, '%s %d: crashed: %s' % (b, a, str(ex)[:300]))
print('soulskills102: %d checks, %d failed (%.0fs)' % (N[0], len(FAILS), time.time() - t0))
for f in FAILS:
    print('  -', f)
sys.exit(1 if FAILS else 0)
