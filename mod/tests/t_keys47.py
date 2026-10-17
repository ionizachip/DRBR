"""Build 47 (was t_keys46: + QUICK SETTINGS, Hold Breath as the fights' own): the match keys (your report: "x is used to slow, just make s do hold breath", "tap z to switch between
heals/items and hold z to actually use one", "you can keep the hold slot", "also add keybinds", no menu sounds, no "five
clean seconds").
  A. the key table: the defaults (S breath, Z use, C charge, A hold slot, TAB list, BACKSPACE give up), the refused keys
     (arrows, X / SHIFT - the game's own slow -, ENTER, ESC, F4, non-keys), a key taken from another action swaps the two,
     every key set read from the ini cleaned to six usable different keys (300 random / broken sets), the ini round trip,
     the key names.
  B. the keys in the match (the player's own code, the real keyboard functions): S = Hold Breath (X alone never), a tap of Z
     picks the next skill (round to the first), Z held 12 frames uses the picked one (and only that one, once), a Z still
     held from a box does nothing until let go, A = the hold slot (in, back, swapped when the slots are full, not a spinning
     slot), C charges and draws, TAB the player list, BACKSPACE gives up (online), every key moved in KEYBINDS works where
     the old one no longer does, a controller (confirm / menu buttons, LB, RB, BACK), no menu sound from picking, holding,
     drawing or watching, no fast-forward online.
  C. the KEYBINDS page through real input: MORE OPTIONS > KEYBINDS, a key waited for (the Z that opened the box let go
     first), a refused key explained, the new key saved to the ini, a swap told, ESC cancels, RESET KEYS, back to where it
     came from (MORE OPTIONS or the room)."""
import sys, os, json, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from harness import *
sys.path.insert(0, '/home/claude/work/uiref')
from br_shot import br_frame

FAILS = []
N = [0]


def ok(c, m):
    N[0] += 1
    if not c:
        FAILS.append(m)
        print('FAIL', m, flush=True)


def eq(a, b, m):
    ok(a == b, '%s (got %r, want %r)' % (m, a, b))


def J(sim, e):
    return sim.py(sim.eval(e))


S_, Z_, C_, A_, X_, P_, L_, Q_, W_, V_, B_ = (ord(c) for c in 'SZCAXPLQWVB')
D_, F_ = ord('D'), ord('F')   # build 48: HOLD SLOT on D, QUICK SETTINGS on F (Q / E / A are the targeting keys)
TAB, BKSP = 9, 8
KEYS = ['breath', 'use', 'charge', 'hold', 'list', 'quit', 'quick', 'souls']


def keys_of(sim):
    return [J(sim, 'kfo_key("%s")' % k) for k in KEYS]


# ---------------------------------------------------------------- A. the key table
sim = make_sim()
sim.run('kfo_get();')
eq(keys_of(sim), [S_, Z_, C_, D_, TAB, BKSP, F_, V_], 'the default keys: S, Z, C, D, TAB, BACKSPACE, F (QUICK SETTINGS), V (OTHER SOULS) - build 48')
for k, why in ((37, 'arrows'), (38, 'arrows'), (39, 'arrows'), (40, 'arrows'), (X_, 'slow'), (16, 'slow'), (160, 'slow'), (161, 'slow'),
               (13, 'menu'), (27, 'menu'), (115, 'full screen'), (7, 'not a key'), (255, 'not a key'), (0, 'not a key')):
    w = J(sim, 'kfo_key_why(%d)' % k)
    ok(why in w, 'key %d refused (%s): %r' % (k, why, w))
for k in (P_, 32, 112, 101, 188, ord('0'), ord('9'), 17, 18, 46):
    eq(J(sim, 'kfo_key_why(%d)' % k), '', 'key %d can be a match key' % k)
ok(J(sim, 'kfo_key_set("breath", %d)' % P_) in (True, 1), 'HOLD BREATH -> Q')
eq(keys_of(sim), [P_, Z_, C_, D_, TAB, BKSP, F_, V_], 'only HOLD BREATH changed')
sim.run('kfo_key_set("breath", %d);' % Z_)
eq(keys_of(sim), [Z_, P_, C_, D_, TAB, BKSP, F_, V_], 'HOLD BREATH takes Z from USE SKILL: USE SKILL gets Q (the two swap)')
ok(J(sim, 'kfo_key_set("use", 38)') in (False, 0), 'an arrow is refused')
ok(J(sim, 'kfo_key_set("use", %d)' % X_) in (False, 0), 'X is refused')
eq(keys_of(sim), [Z_, P_, C_, D_, TAB, BKSP, F_, V_], 'a refused key changes nothing')
sim.run('kfo_keys_reset();')
eq(keys_of(sim), [S_, Z_, C_, D_, TAB, BKSP, F_, V_], 'kfo_keys_reset: the defaults back')
# every set the ini (or anything) can hold is cleaned to six usable, different keys
R = random.Random(46)
bad = []
for i in range(300):
    d = {}
    for k in KEYS:
        r = R.random()
        if r < 0.15:
            continue
        d[k] = R.choice([S_, Z_, C_, A_, TAB, BKSP, X_, 37, 13, 27, 0, -5, 300, 115, 999999, P_, L_, 32, 16, 1.5, 81.7]) if r < 0.8 else R.randint(-50, 400)
    sim.run('global.KC = kfo_keys_clean(json_parse(%s));' % json.dumps(json.dumps(d)))
    out = [J(sim, 'variable_struct_get(global.KC, "%s")' % k) for k in KEYS]
    good = len(set(out)) == 8 and all(J(sim, 'kfo_key_ok(%r)' % v) in (True, 1) for v in out)
    if not good:
        bad.append((d, out))
ok(not bad, '300 random / broken key sets: always eight usable different keys (%r)' % bad[:2])
sim.run('global.KC = kfo_keys_clean({ breath: %d, use: %d, charge: %d, hold: %d, list: %d, quit: %d, quick: %d, souls: %d });' % (P_, S_, L_, 32, 112, 46, W_, B_))
eq([J(sim, 'variable_struct_get(global.KC, "%s")' % k) for k in KEYS], [P_, S_, L_, 32, 112, 46, W_, B_], 'a good custom set is kept as it is')
# a build 46 ini (seven keys, no OTHER SOULS key): the seven kept, the eighth gets its default V
sim.run('global.KC = kfo_keys_clean({ breath: %d, use: %d, charge: %d, hold: %d, list: %d, quit: %d, quick: %d });' % (P_, S_, L_, 32, 112, 46, W_))
eq([J(sim, 'variable_struct_get(global.KC, "%s")' % k) for k in KEYS], [P_, S_, L_, 32, 112, 46, W_, V_], 'a build 46 set (no OTHER SOULS key): kept, OTHER SOULS gets V')
sim.run('global.KC = kfo_keys_clean(undefined);')
eq([J(sim, 'variable_struct_get(global.KC, "%s")' % k) for k in KEYS], [S_, Z_, C_, D_, TAB, BKSP, F_, V_], 'no set: the defaults')
# the ini: saved, read back by a new game state; a broken [keys] section read clean
sim.run('kfo_key_set("breath", %d); kfo_key_set("list", %d); kfo_ini_save(); global.kfo = undefined; kfo_get();' % (P_, L_))
eq(keys_of(sim), [P_, Z_, C_, D_, L_, BKSP, F_, V_], 'the keys come back from knightfights_online.ini')
sim.run('ini_open(kfo_ini_file()); ini_write_string("keys", "breath", "abc"); ini_write_real("keys", "use", 37); ini_write_real("keys", "charge", %d);'
        ' ini_write_real("keys", "hold", -3); ini_close(); global.kfo = undefined; kfo_get();' % L_)
kk = keys_of(sim)
ok(len(set(kk)) == 8 and all(J(sim, 'kfo_key_ok(%d)' % v) in (True, 1) for v in kk), 'a broken [keys] section: eight usable different keys (%r)' % kk)
sim.run('kfo_keys_reset();')
for k, nm in ((S_, 'S'), (ord('7'), '7'), (TAB, 'TAB'), (BKSP, 'BACKSPACE'), (32, 'SPACE'), (112, 'F1'), (123, 'F12'), (96, 'NUM 0'), (105, 'NUM 9'),
              (188, ','), (220, chr(92)), (17, 'CTRL'), (46, 'DELETE'), (93, 'KEY 93')):
    eq(J(sim, 'kfo_key_name(%d)' % k), nm, 'the name of key %d' % k)
eq(J(sim, 'kfo_key_title("use")'), 'USE SKILL', 'the KEYBINDS name of USE')

# ---------------------------------------------------------------- B. the keys in the match
def match_sim(slots=None, setx=None):
    m, _ = br_frame('t_keys', n=4, out=(), render=False)
    m.played = []
    m.mock('snd_play', lambda s, a, *r: (s.played.append(a), 0)[1])
    xin = {'x': 0, 'l': 0, 'r': 0}
    m.xin = xin
    m.mock('button2_h', lambda s: xin['x'])
    m.mock('button1_h', lambda s: 0)
    m.mock('button3_h', lambda s: 0)
    m.mock('left_p', lambda s: xin['l'])
    m.mock('right_p', lambda s: xin['r'])
    for b in ('left_h', 'right_h', 'up_h', 'down_h'):
        m.mock(b, lambda s: 0)
    m.define_object('obj_testbullet')
    m.run('global.TBI = instance_create(0, 0, obj_testbullet); global.kfo.hostid = 1; global.kfo.mode = "local"; var _M = global.kfo.M;'
          'var _s = kfo_set_clean(json_parse(%s)); _M.set = _s; _M.eff = kbr_eff(_s); _M.sk = kbr_skills_new(_M.eff); _M.out = false; _M.me = true;'
          'global.hp[1] = 1000; global.maxhp[1] = 1000; _M.g = 50; _M.alive_f = 0; _M.hold = false; _M.hold_was = false; _M.R.ph = "run";'
          'global.knight_frozen = false; global.HI = instance_create(300, 160, obj_heart); global.kfo.lq = [];' % json.dumps(json.dumps(setx or {'slots': 4})))
    if slots is not None:
        m.run('global.kfo.M.sk.slots = json_parse(%s);' % json.dumps(json.dumps([{'sid': s, 'rev': 0} for s in slots])))
    m.input.begin_frame = lambda fno: None
    return m


def press(m, held, x=0):
    held = set(held)
    m.input.pressed = held - m.input.held
    m.input.released = m.input.held - held
    m.input.held = held
    m.input.cleared = set()
    m.xin['x'] = x


def tick(m, held, n=1, x=0):
    for _ in range(n):
        press(m, held, x)
        m.run('kbr_me_tick();')


def sk(m):
    return J(m, '(function() { var _S = global.kfo.M.sk; var _l = []; for (var _i = 0; _i < array_length(_S.slots); _i++) array_push(_l, _S.slots[_i].sid);'
                ' return { sl: _l, sel: _S.sel, hold: is_undefined(_S.hold) ? -1 : _S.hold.sid, used: _S.used, chg: _S.charging }; })()')


def sent(m):
    return J(m, '(function() { var _o = []; for (var _i = 0; _i < array_length(global.kfo.lq); _i++) { var _q = global.kfo.lq[_i];'
                ' if (_q.up) array_push(_o, [kfo_js(_q.m, "k", ""), kfo_jn(_q.m, "sid", -1)]); } return _o; })()')


MENU = ('snd_menumove', 'snd_select', 'snd_cantselect')


def menu_sounds(m):
    inv = {v: k for k, v in m.assets.items()}
    return [inv.get(a, a) for a in m.played if inv.get(a, a) in MENU]


# Hold Breath
m = match_sim()
tick(m, {S_}, 5)
ok(J(m, 'global.kfo.M.hold') in (True, 1), 'S pressed: Hold Breath')
tick(m, set(), 2)
ok(J(m, 'global.kfo.M.hold') in (True, 1), 'build 50: a toggle - S let go: still holding the breath')
tick(m, {S_}, 1)
tick(m, set(), 2)
ok(J(m, 'global.kfo.M.hold') in (False, 0), 'build 50: S pressed again: breathing out')
tick(m, set(), 30, x=1)
ok(J(m, 'global.kfo.M.hold') in (False, 0), 'X held alone (the game\'s slow walk): no Hold Breath')
m.run('global.kfo.M.g = 0;')
tick(m, {S_}, 3)
ok(J(m, 'global.kfo.M.hold') in (True, 1), 'build 47: an empty gauge: S still holds (no gauge needed, as in the fights)')
# build 47 (your report: "make it like the fights own"): Hold Breath = the fights' own HoldBreath - the SOUL moves faster
# (one more than the room's SOUL SPEED, two more in a Roaring attack) and nothing else
m = match_sim()
spd = J(m, 'global.kfo.M.eff.spd')
tick(m, set(), 2)
eq(J(m, 'global.HI.wspeed'), spd, 'breathing: the SOUL at the room speed (%d)' % spd)
tick(m, {S_}, 2)
eq(J(m, 'global.HI.wspeed'), spd + 1, 'Hold Breath: one faster (5 at the Chapter 3 speed of 4, as the fights\' HoldBreath)')
m.run('global.RR = instance_create(0, 0, obj_knight_roaring2);')
tick(m, {S_}, 1)
eq(J(m, 'global.HI.wspeed'), spd + 2, 'Hold Breath in a Roaring attack: two faster (6, as the fights)')
m.run('with (obj_knight_roaring2) instance_destroy(); global.RR = instance_create(0, 0, obj_knight_roaring3);')
tick(m, {S_}, 1)
eq(J(m, 'global.HI.wspeed'), spd + 2, 'Hold Breath in Violet Knight\'s Roaring (obj_knight_roaring3): two faster')
m.run('with (obj_knight_roaring3) instance_destroy();')
tick(m, set(), 1)
eq(J(m, 'global.HI.wspeed'), spd + 1, 'build 50: S let go - still holding the breath (a toggle)')
tick(m, {S_}, 1)
tick(m, set(), 1)
eq(J(m, 'global.HI.wspeed'), spd, 'S pressed again: the room speed again')
tick(m, {S_}, 1, x=1)
eq(J(m, 'global.HI.wspeed'), spd + 1, 'S with X (the game\'s slow): still +1 (the slow halves the move itself, as in the fights)')
m.run('global.kfo.M.sk.slow_t = 100;')
tick(m, {S_}, 1)
eq(J(m, 'global.HI.wspeed'), spd, 'SLOW (a rival\'s skill) and Hold Breath: -1 +1')
m.run('global.kfo.M.sk.slow_t = 0;')
# nothing else: the gauge, the damage, the grazes, the log
m1 = match_sim()
m2 = match_sim()
for mm in (m1, m2):
    mm.run('global.kfo.M.g = 37; global.kfo.M.alive_f = 0;')
nlog1 = J(m1, 'array_length(global.kfo.M.log)')
for i in range(240):
    tick(m1, {S_} if (i // 13) % 2 == 0 else set(), 1)
    tick(m2, set(), 1)
eq(J(m1, 'global.kfo.M.g'), J(m2, 'global.kfo.M.g'), 'Hold Breath on and off for 240 frames: the gauge as without it (no drain)')
eq(J(m1, 'array_length(global.kfo.M.log)'), nlog1, 'Hold Breath on and off 18 times: no log lines (no flicker spam)')
tick(m1, {S_}, 1)
d1 = J(m1, 'kbr_dmg_taken(0)') if False else None
m1.run('with (global.TBI) global.D1 = kbr_dmg_taken(0);')
tick(m2, set(), 1)
m2.run('with (global.TBI) global.D2 = kbr_dmg_taken(0);')
eq(J(m1, 'global.D1'), J(m2, 'global.D2'), 'a hit while holding the breath: the same damage (no halving any more)')
m1.run('global.G0 = global.kfo.M.g; kbr_gauge_add(1, true); global.G1 = global.kfo.M.g;')
eq(J(m1, 'global.G1 - global.G0'), 1, 'a graze while holding the breath: counts once (no doubling)')
# tap / hold Z
m = match_sim(slots=[11, 13, 10])
eq(sk(m)['sel'], 0, 'the first skill is picked at the start')
for want in (1, 2, 0, 1):
    tick(m, {Z_}, 3)
    tick(m, set(), 1)
    eq(sk(m)['sel'], want, 'a tap of Z: the next skill (%d)' % want)
eq(sk(m)['sl'], [11, 13, 10], 'taps use nothing')
m.lq = None
tick(m, {Z_}, 11)
eq(sk(m)['sl'], [11, 13, 10], 'Z held 11 frames: nothing used yet')
tick(m, {Z_}, 1)
s = sk(m)
eq(s['sl'], [11, 10], 'Z held 12 frames: the picked skill (Shield, slot 2) is used')
eq(s['used'], 1, 'once')
ok(['sg', 13] in sent(m), 'the host is told (sg 13): %r' % sent(m))
tick(m, {Z_}, 40)
eq(sk(m)['sl'], [11, 10], 'still held: nothing more')
tick(m, set(), 1)
eq(sk(m)['sel'], 1, 'let go after the use: no tap (the pick stays on the slot)')
m.run('global.kfo.M.sk.cd = 0;')
tick(m, {Z_}, 12)
tick(m, set(), 1)
s = sk(m)
eq(s['sl'], [11], 'the next hold uses the skill now in the picked slot (Knightmare)')
ok(['sk', 10] in sent(m), 'a red skill goes to the rivals (sk 10)')
eq(s['sel'], 0, 'the pick moves back onto a skill that is there')
tick(m, {Z_}, 3)
tick(m, set(), 1)
eq(sk(m)['sel'], 0, 'one skill: a tap keeps it')
ok(not menu_sounds(m), 'picking and using: no menu sound (%r)' % menu_sounds(m))
# held through the cooldown: it goes off as soon as the cooldown ends, once
m = match_sim(slots=[11, 12])
m.run('global.kfo.M.sk.cd = 30;')
tick(m, {Z_}, 20)
eq(sk(m)['sl'], [11, 12], 'Z held during the cooldown: not yet')
tick(m, {Z_}, 15)
eq(sk(m)['sl'], [12], 'still held: used as soon as the cooldown ends')
tick(m, {Z_}, 150)
eq(sk(m)['sl'], [12], 'once per hold')
# a skill the room does not allow now (sudden death: no green skills): told once, not every frame of the hold
m = match_sim(slots=[11])
m.run('global.kfo.M.sd_on = true; global.kfo.M.eff.sdgreen = false;')
tick(m, {Z_}, 60)
logs = J(m, '(function() { var _o = []; for (var _i = 0; _i < array_length(global.kfo.M.log); _i++) array_push(_o, global.kfo.M.log[_i].t); return _o; })()')
eq(len([l for l in logs if "can't be used" in l]), 1, 'a refused skill is told once per hold (%r)' % logs)
eq(sk(m)['sl'], [11], 'and stays in its slot')
# a Z still held from a box does nothing until it is let go
m = match_sim(slots=[11, 12])
m.run('global.PR = instance_create(0, 0, obj_knight_prompt);')
tick(m, {Z_}, 5)
m.run('with (global.PR) instance_destroy();')
tick(m, {Z_}, 30)
eq(sk(m)['sl'], [11, 12], 'Z held from a closed box: nothing used')
tick(m, set(), 1)
eq(sk(m)['sel'], 0, 'and no pick when it is let go')
tick(m, {Z_}, 12)
eq(sk(m)['sl'], [12], 'pressed again and held: used')
# the hold slot
m = match_sim(slots=[11, 13, 10, 2])
tick(m, {Z_}, 2)
tick(m, set(), 1)
eq(sk(m)['sel'], 1, 'Shield picked')
tick(m, {D_}, 1)
s = sk(m)
eq((s['sl'], s['hold']), ([11, 10, 2], 13), 'A: the picked skill (Shield) into the hold slot')
tick(m, {D_}, 5)
eq(sk(m)['hold'], 13, 'A held: once')
tick(m, set(), 1)
tick(m, {D_}, 1)
s = sk(m)
eq((s['sl'], s['hold'], s['sel']), ([11, 13, 10, 2], -1, 1), 'A again: Shield back where the pick is, and picked')
tick(m, set(), 1)
tick(m, {D_}, 1)
tick(m, set(), 1)
m.run('array_push(global.kfo.M.sk.slots, { sid: 5, rev: 0 });')
eq(sk(m)['sl'], [11, 10, 2, 5], 'four slots full')
tick(m, {D_}, 1)
s = sk(m)
eq((s['sl'], s['hold']), ([11, 13, 2, 5], 10), 'full slots: A swaps the held Shield with the picked skill')
tick(m, set(), 1)
m.run('global.kfo.M.sk.slots[1].rev = 20;')
tick(m, {D_}, 1)
eq(sk(m)['hold'], 10, 'a spinning slot is not swapped')
ok(not menu_sounds(m), 'the hold slot: no menu sound (%r)' % menu_sounds(m))
# charge and draw (C), silent
m = match_sim(slots=[])
m.run('global.kfo.M.g = 100;')
tick(m, {C_}, 50)
ok(sk(m)['chg'] in (True, 1), 'C held: charging')
tick(m, set(), 1)
ok(len(sk(m)['sl']) >= 1, 'C let go past the cost: a skill drawn (%r)' % sk(m)['sl'])
ok(not menu_sounds(m), 'drawing: no menu sound (%r)' % menu_sounds(m))
# the player list
m = match_sim()
tick(m, {TAB}, 1)
ok(J(m, 'global.kfo.M.tab') in (True, 1), 'TAB held: the player list')
tick(m, set(), 1)
ok(J(m, 'global.kfo.M.tab') in (False, 0), 'TAB let go: closed')
# watching: Left / Right silent
m = match_sim()
m.run('global.kfo.M.out = true; global.kfo.M.spect = -1;')
for i in range(4):
    m.xin['r'] = 1
    m.run('kbr_me_tick();')
    m.xin['r'] = 0
ok(not menu_sounds(m), 'watching: Left / Right make no menu sound (%r)' % menu_sounds(m))
# every key moved in KEYBINDS
m = match_sim(slots=[11, 13, 10])
m.run('kfo_key_set("breath", %d); kfo_key_set("use", %d); kfo_key_set("hold", 32); kfo_key_set("list", %d); kfo_key_set("charge", 112);' % (P_, ord('J'), L_))
tick(m, {S_}, 5)
ok(J(m, 'global.kfo.M.hold') in (False, 0), 'HOLD BREATH moved to Q: S does nothing')
tick(m, {P_}, 5)
ok(J(m, 'global.kfo.M.hold') in (True, 1), 'Q holds the breath')
tick(m, set(), 1)
tick(m, {Z_}, 20)
tick(m, set(), 1)
eq(sk(m)['sl'], [11, 13, 10], 'USE moved to J: Z does nothing')
tick(m, {ord('J')}, 2)
tick(m, set(), 1)
eq(sk(m)['sel'], 1, 'a tap of J picks the next skill')
tick(m, {32}, 1)
tick(m, set(), 1)
eq(sk(m)['hold'], 13, 'SPACE is the hold slot now')
tick(m, {L_}, 1)
ok(J(m, 'global.kfo.M.tab') in (True, 1), 'L opens the player list')
tick(m, {TAB}, 1)
ok(J(m, 'global.kfo.M.tab') in (False, 0), 'TAB does not any more')
m.run('global.kfo.M.g = 100;')
tick(m, {112}, 30)
ok(sk(m)['chg'] in (True, 1), 'F1 charges')
tick(m, set(), 1)
tick(m, {C_}, 5)
ok(sk(m)['chg'] in (False, 0), 'C does not')
# a controller
m = match_sim(slots=[11, 13, 10])
m.run('global.input_g = [gp_padu, gp_padd, gp_padl, gp_padr, gp_face1, gp_face2, gp_face4, 0, 0, 0]; global.GC = instance_create(0, 0, obj_gamecontroller); global.GC.gamepad_id = 0;')
GP = {'face1': 32769, 'face4': 32772, 'lb': 32773, 'rb': 32774, 'lt': 32775, 'rt': 32776, 'back': 32777}
tick(m, {GP['lt']}, 4)
ok(J(m, 'global.kfo.M.hold') in (True, 1), 'a controller: LT holds the breath (build 48: LB / RB are the targeting mode)')
tick(m, set(), 1)
tick(m, {GP['face1']}, 2)
tick(m, set(), 1)
eq(sk(m)['sel'], 1, 'a controller: a tap of the confirm button picks the next skill')
tick(m, {GP['rt']}, 1)
tick(m, set(), 1)
eq(sk(m)['hold'], 13, 'a controller: RT is the hold slot')
m0 = J(m, 'global.kfo.M.tg.mode')
tick(m, {GP['rb']}, 1)
tick(m, set(), 1)
eq(J(m, 'global.kfo.M.tg.mode'), (m0 + 1) % 7, 'a controller: RB is the next targeting mode')
tick(m, {GP['lb']}, 1)
tick(m, set(), 1)
eq(J(m, 'global.kfo.M.tg.mode'), m0, 'a controller: LB the previous one')
tick(m, {GP['back']}, 1)
ok(J(m, 'global.kfo.M.tab') in (True, 1), 'a controller: BACK opens the player list')
tick(m, set(), 1)
m.run('global.kfo.M.sk.cd = 0;')
tick(m, {GP['face1']}, 12)
eq(len(sk(m)['sl']), 1, 'a controller: the confirm button held 12 frames uses the picked skill')
tick(m, set(), 1)
m.run('global.kfo.M.g = 100;')
tick(m, {GP['face4']}, 20)
ok(sk(m)['chg'] in (True, 1), 'a controller: the menu button charges')
tick(m, set(), 1)
# give up: BACKSPACE online (the leave box), and the key of KEYBINDS
m = match_sim()
m.run('global.krun.state = "battle"; with (obj_knight_prompt) instance_destroy(); global.knight_frozen = false;')
ok(J(m, 'kfo_cfg_online(global.krun.cfg)') in (True, 1), 'the battle is an online one')
press(m, {BKSP})
m.run('knight_backspace_check();')
eq(J(m, 'instance_number(obj_knight_prompt)'), 1, 'BACKSPACE: the GIVE UP box')
m.run('with (obj_knight_prompt) instance_destroy(); global.knight_frozen = false; kfo_key_set("quit", %d);' % P_)
press(m, set())
press(m, {BKSP})
m.run('knight_backspace_check();')
eq(J(m, 'instance_number(obj_knight_prompt)'), 0, 'GIVE UP moved to Q: BACKSPACE does nothing')
press(m, set())
press(m, {P_})
m.run('knight_backspace_check();')
eq(J(m, 'instance_number(obj_knight_prompt)'), 1, 'Q: the GIVE UP box')
m.run('with (obj_knight_prompt) instance_destroy(); global.knight_frozen = false; kfo_keys_reset();')
# no fast-forward online (TAB is the player list there)
press(m, {TAB})
for st in ('battle', 'arena', 'won'):
    m.run('global.krun.state = "%s";' % st)
    ok(J(m, 'knight_ff_on()') in (False, 0), 'TAB never fast-forwards an online match (%s)' % st)
m.run('global.krun.state = "battle";')
# no clean-seconds bonus: 20 seconds without a hit add the CHARGE RATE ticks only
m = match_sim()
m.run('global.kfo.M.g = 0; global.kfo.M.alive_f = 0;')
tick(m, set(), 600)
eq(J(m, 'global.kfo.M.g'), 20, '20 seconds without a hit: +20 (one a second, no +5 bonus)')
logs = J(m, '(function() { var _o = []; for (var _i = 0; _i < array_length(global.kfo.M.log); _i++) array_push(_o, global.kfo.M.log[_i].t); return _o; })()')
ok(not [l for l in logs if 'clean' in l.lower()], 'no clean-seconds line (%r)' % logs)

# ---------------------------------------------------------------- C. the KEYBINDS page
from uiharness import menu_sim
sim, rec = menu_sim()
sim.run('knight_menu_open();')
sim.step(1)
sim.run('global.knight_ui.tp = 80; global.knight_ui.bp = 60; global.knight_ui.inputdelay = 0; global.knight_ui.notice = ""; global.is_console = 0; kfo_get(); kfo_keys_reset();')
sim.input.begin_frame = lambda fno: None
U = 'global.knight_ui'


def ui(k=None, held=()):
    for kk in sim.inp:
        sim.inp[kk] = 0
    if k:
        sim.inp[k] = 1
    held = set(held)
    sim.input.pressed = held - sim.input.held
    sim.input.released = sim.input.held - held
    sim.input.held = held
    sim.input.cleared = set()
    sim.run('if (is_struct(global.knight_ui.modal)) global.knight_ui.modal.t++; knight_ui_step();')


sim.run('%s.tab = 0; %s.focus = 1; %s.krow = 10; %s.sub = "onl_opt"; %s.opt_row = 0;' % ((U,) * 5))
rows = J(sim, 'kfo_ui_opt_rows()')
eq(rows, ['server', 'vis', 'view', 'mview', 'keys', 'song', 'done'], 'MORE OPTIONS (build 48): SOUL SETTINGS (the colour page inside it), MATCH VIEW, KEYBINDS, MUSIC')
sim.run('%s.opt_row = 4;' % U)
ui('ok', {Z_})
eq(J(sim, U + '.sub'), 'onl_keys', 'Z on KEYBINDS opens the page')
eq(J(sim, 'kfo_ui_keys_rows()'), KEYS + ['tgl', 'tgr', 'tgn', 'chat', 'reset', 'done'], 'the rows: every action (build 48: + the three targeting keys; build 49: + CHAT), RESET KEYS, DONE')
ui(None, {Z_})
ui('ok', {Z_})
eq(J(sim, U + '.modal.k'), 'kfo_key', 'Z on HOLD BREATH: the box waits for a key')
for i in range(4):
    ui(None, {Z_})
eq(J(sim, 'kfo_key("breath")'), S_, 'the Z that opened the box, still held: not taken')
ui(None, set())
ui(None, {X_})
lines = J(sim, U + '.modal.lines')
ok(J(sim, 'is_struct(%s.modal)' % U) in (True, 1) and any('Not X' in l for l in lines), 'X refused and explained (%r)' % lines)
ui(None, set())
ui(None, {38})
ok(any('Not' in l and 'SOUL' in l for l in J(sim, U + '.modal.lines')), 'an arrow refused and explained')
ui(None, set())
ui(None, {P_})
ok(J(sim, 'is_struct(%s.modal)' % U) in (False, 0), 'Q taken: the box closes')
eq(J(sim, 'kfo_key("breath")'), P_, 'HOLD BREATH is Q')
sim.run('global.KS = global.kfo; global.kfo = undefined; kfo_get(); global.KB = kfo_key("breath"); global.kfo = global.KS;')
eq(J(sim, 'global.KB'), P_, 'and saved: a new game reads Q from the ini')
ui(None, set())
ui('down', set())
ui('ok', {Z_})
ui(None, set())
ui(None, {P_})
eq([J(sim, 'kfo_key("breath")'), J(sim, 'kfo_key("use")')], [Z_, P_], 'USE SKILL takes Q: HOLD BREATH gets Z (swapped)')
w = J(sim, U + '.warn')
ok('HOLD BREATH is now Z' in w, 'the swap is told (%r)' % w)
ui(None, set())
ui('ok', {Z_})
ui(None, set())
ui(None, {27})
ok(J(sim, 'is_struct(%s.modal)' % U) in (False, 0) and J(sim, 'kfo_key("use")') == P_, 'ESC cancels, nothing changes')
ui(None, set())
sim.run('%s.keys_row = 12;' % U)   # build 49: RESET KEYS after the 12 actions
ui('ok', {Z_})
eq(keys_of(sim), [S_, Z_, C_, D_, TAB, BKSP, F_, V_], 'RESET KEYS: the defaults')
ui(None, set())
ui('back', set())
eq(J(sim, U + '.sub'), 'onl_opt', 'X: back to MORE OPTIONS')
print('match keys: %d checks, %d failed' % (N[0], len(FAILS)))
sys.exit(1 if FAILS else 0)
