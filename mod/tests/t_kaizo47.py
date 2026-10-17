"""Build 47 (P1): Kaizo Knight never overrides the online HP rules - and its own HP rules stay in its offline fight.

What Kaizo Knight's fight does to HP (found in the merged code):
  * its first frame (obj_knight_enemy Step, damagereductiontimer == 1): max HP / HP above Kris 200, Susie 230, Ralsei 180,
    Noelle 180 starts the "HP scene" (k_hpscene): the knight takes over the battle (mnfight / myfight 99) and at step 6 cuts
    max HP and HP down to those numbers;
  * its arena (obj_ch3_PTB02 Step, Kaizo's case, every frame): Noelle's max HP below 120 -> max HP and HP set to 120.
Build 47 puts knight_enc_hp_rules() (false only in an online fight) in front of both (br_patch.py), and online a hit that
takes a share of max HP (scr_damage_maxhp: the split slashes, the big quick slash) is an online hit (knight_direct_taken).

Parts (each check counted):
  entry     the mandatory table: Kaizo opening the match or switched in, Kris / Susie / Ralsei / Noelle, 100/100, 250/250,
            75/250, 300/300, Noelle 100/100 and 60/60 (the arena's floor), for 600 frames each - no HP or max HP change, no
            HP scene, the battle never taken over; and the same with the check removed (knight_enc_hp_rules -> true, build
            46's code path): the clamp / the floor DO happen (the test sees the bug)
  heal      healing during Kaizo goes up to the room's max HP (250), never stops at the encounter's 200
  maxhp     every MAX HP the room offers (60-300) x every skin: Kaizo keeps it
  thorn     Normal -> Kaizo -> Thorn (and back) with the HP ledger: no unexplained change at any switch
  offline   Kaizo's own offline fight: Kris 250 max HP is cut to 200 by its HP scene; Noelle 100 is raised to 120 - as before
  maxdmg    a split slash / big quick slash online takes the online damage (and counts as a hit), offline its share of max HP
  long      (python3 t_kaizo47.py long <kaizo cycles> <seed> <skin> <mhp>) the HP ledger over many Kaizo attack cycles and
            switches with hits, heals and sudden death: every HP / max HP change must come from a hit, a heal, sudden death
            or the host's fix - zero unexplained changes
Usage: python3 t_kaizo47.py [part ...]   (default: entry heal maxhp thorn offline maxdmg)"""
import sys, os, re, json, time, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from br_harness import *

FAILS = []
N = [0]
CORE = open(MDIR + 'gml_GlobalScript_knight_core.gml', encoding='utf8').read()


def ok(c, m):
    N[0] += 1
    if not c:
        FAILS.append(m)
        print('FAIL', m, flush=True)
    return c


def J(sim, e):
    return sim.py(sim.eval(e))


def func_src(name):
    """`function name(...) { ... }` out of the merged core (brace counting; the bodies used here have no braces in strings)"""
    m = re.search(r'(?m)^function %s\(' % re.escape(name), CORE)
    assert m, name
    i = CORE.index('{', m.end())
    d = 0
    j = i
    while True:
        c = CORE[j]
        if c == '{':
            d += 1
        elif c == '}':
            d -= 1
            if d == 0:
                break
        j += 1
    return CORE[m.start():j + 1]


# the ledger: every authorised HP source counts what it did this frame
LEDGER = ('global.LED = { dmg: 0, heal: 0, fix: 0, hits: 0 };\n' +
          func_src('kbr_dmg_taken').replace('function kbr_dmg_taken(', 'function kbr_dmg_taken__orig(', 1) + '\n' +
          'function kbr_dmg_taken(_d) { var _r = kbr_dmg_taken__orig(_d); global.LED.dmg += _r; global.LED.hits++; return _r; }\n' +
          func_src('kbr_heal').replace('function kbr_heal(', 'function kbr_heal__orig(', 1) + '\n' +
          'function kbr_heal(_n, _fx) { var _r = kbr_heal__orig(_n, _fx); global.LED.heal += _r; return _r; }\n' +
          func_src('kfo_on_fix').replace('function kfo_on_fix(', 'function kfo_on_fix__orig(', 1) + '\n' +
          'function kfo_on_fix(_m) { global.LED.fix++; return kfo_on_fix__orig(_m); }\n')
GATE_OFF = 'function knight_enc_hp_rules() { return true; }\n'
HPS = ('(function() { var _c = kbr_char(); var _s = -1; var _hs = 0; with (obj_knight_enemy) { if (variable_instance_exists(id, "k_hpscene") && k_hpscene != 0) _hs = k_hpscene; }'
       ' var _M = global.kfo.M; return [global.hp[_c], global.maxhp[_c], _hs, global.mnfight, global.knight_variant, _M.R.ph, _M.R.k, _M.alive_f, _M.sd_on,'
       ' global.LED.dmg, global.LED.heal, global.LED.fix, _M.out]; })()')
KZ = 1  # Kaizo Knight's place in the hub registry (and its online knight number)


def match(open_ok, kn, skin, mhp, hp=None, world=True, gate=True, setx='', seed=4242):
    sim, e = br_match(open_ok=open_ok, kn=kn, skin=skin, seed=seed, world=world,
                      setx='_s.mhp = %d; _s.rush = 1; _s.hp0 = 100; %s' % (mhp, setx))
    if e is not None:
        return None, e
    sim.load_source('gml_GlobalScript_kz47_ledger', LEDGER + ('' if gate else GATE_OFF))
    sim.run('global.LED = { dmg: 0, heal: 0, fix: 0, hits: 0 };')
    # the online kit as the launch gives it (MAX HP / START HP of the room), then the HP this case starts with. The room's
    # cutscene runner (made empty by the harness) goes: the arena cutscene waits in con 6 for the battle, which is all it does
    sim.run('with (obj_cutscene_master) instance_destroy(); kfo_kit_apply(kbr_char());')
    # Kaizo's arena puts Kris / Susie / Ralsei in the party for its own intro and back when its battle starts; the harness makes
    # it already waiting for the battle (con 6), so the party it had is put back here as the battle start does
    sim.run('global.char = [%d, 0, 0];' % skin)
    if hp is not None:
        sim.run('global.hp[kbr_char()] = %d;' % hp)
    return sim, None


def run_frames(sim, nf, on=None):
    rows = []
    for f in range(nf):
        sim.run('global.LED.dmg = 0; global.LED.heal = 0; global.LED.fix = 0;')
        if on:
            on(sim, f)
        err = step(sim, 1)
        if err is not None:
            return rows, err
        rows.append(J(sim, HPS))
    return rows, None


def part_entry():
    cases = [('Kris 100/100', 1, 100, None), ('Kris 250/250', 1, 250, None), ('Kris 75/250', 1, 250, 75), ('Kris 300/300', 1, 300, None),
             ('Susie 250/250', 2, 250, None), ('Ralsei 250/250', 3, 250, None), ('Noelle 250/250', 4, 250, None),
             ('Noelle 100/100', 4, 100, None), ('Noelle 60/60', 4, 60, None)]
    seen_bug = {'scene': 0, 'floor': 0}
    for name, skin, mhp, hp in cases:
        for how, open_ok, kn in (('opens', KZ, (KZ,)), ('switched in', 0, (0, KZ))):
            for gate in (True, False):
                sim, e = match(open_ok, kn, skin, mhp, hp, gate=gate)
                if not ok(e is None, '%s %s: setup %r' % (name, how, e)):
                    continue
                want_hp = hp if hp is not None else mhp
                rows, err = run_frames(sim, 650 if how == 'switched in' else 420)
                ok(err is None, '%s %s gate=%s: no error (%s)' % (name, how, gate, (err or '')[:200]))
                kz_frames = [r for r in rows if r[4] == KZ]
                if gate:
                    ok(len(kz_frames) > 100, '%s %s: Kaizo Knight fought (%d frames)' % (name, how, len(kz_frames)))
                    ok(all(r[0] == want_hp and r[1] == mhp for r in rows), '%s %s: HP %d/%d all along (seen %s)'
                       % (name, how, want_hp, mhp, sorted(set((r[0], r[1]) for r in rows))[:6]))
                    ok(all(r[2] == 0 for r in rows), '%s %s: no HP scene' % (name, how))
                    ok(all(r[3] != 99 for r in rows[5:]), '%s %s: the battle is never taken over (mnfight 99)' % (name, how))
                    ok(any(r[5] == 'run' and r[4] == KZ for r in rows), '%s %s: a Kaizo attack ran' % (name, how))
                else:
                    # build 46's path: the encounter's own rules run in the online match
                    over = (skin == 1 and mhp > 200) or (skin == 2 and mhp > 230) or (skin in (3, 4) and mhp > 180)
                    floor = (skin == 4 and mhp < 120 and how == 'opens')
                    changed = any(r[0] != want_hp or r[1] != mhp for r in rows)
                    if over:
                        seen_bug['scene'] += 1 if changed else 0
                        ok(changed, '%s %s, check removed: the HP scene cuts the HP (the bug, reproduced)' % (name, how))
                    if floor:
                        seen_bug['floor'] += 1 if changed else 0
                        ok(changed, '%s %s, check removed: the arena raises Noelle to 120 (the bug, reproduced)' % (name, how))
                    if not over and not floor:
                        ok(not changed, '%s %s, check removed: nothing to cut (HP under the encounter limits)' % (name, how))
                print('  entry', name, how, 'gate' if gate else 'NO GATE', 'frames', len(rows), 'kaizo', len(kz_frames),
                      'hp', sorted(set((r[0], r[1]) for r in rows))[:4], flush=True)
    print('entry: the bug seen with the check removed: HP scene %d cases, Noelle floor %d cases' % (seen_bug['scene'], seen_bug['floor']))


def part_heal():
    sim, e = match(KZ, (KZ,), 1, 250, 100)
    if not ok(e is None, 'heal: setup'):
        return
    rows, err = run_frames(sim, 200)
    ok(err is None, 'heal: frames run')
    sim.run('global.LED.heal = 0; global.HR = kbr_heal(500, false);')
    s = J(sim, HPS)
    ok(s[0] == 250 and s[1] == 250, 'heal during Kaizo: 100 + 500 -> 250/250 (the room\'s max), seen %r' % s[:2])
    ok(J(sim, 'global.HR') == 150, 'heal: 150 applied')
    rows, err = run_frames(sim, 120)
    ok(err is None and all(r[0] == 250 and r[1] == 250 for r in rows), 'heal: still 250/250 120 frames later')


def part_maxhp():
    for mhp in (60, 100, 120, 150, 180, 200, 230, 250, 300):
        for skin in (1, 2, 3, 4):
            sim, e = match(KZ, (KZ,), skin, mhp)
            if not ok(e is None, 'maxhp %d skin %d: setup' % (mhp, skin)):
                continue
            rows, err = run_frames(sim, 160)
            ok(err is None, 'maxhp %d skin %d: frames' % (mhp, skin))
            ok(all(r[1] == mhp and r[0] == mhp for r in rows), 'MAX HP %d, skin %d: kept (seen %s)' % (mhp, skin, sorted(set((r[0], r[1]) for r in rows))[:4]))
    print('maxhp: 9 room settings x 4 skins done', flush=True)


def ledger_check(prev, cur, sd_rate, sd_floor, tag):
    """one frame: every HP / max HP change explained by this frame's hits, heals, sudden death or the host's fix"""
    hp0, mh0 = prev[0], prev[1]
    hp1, mh1 = cur[0], cur[1]
    dmg, heal, fix = cur[9], cur[10], cur[11]
    if fix > 0 or cur[12]:
        return True
    mh_ok = (mh1 == mh0) or (cur[8] and mh1 == max(sd_floor, mh0 - sd_rate) and (cur[7] % 30) == 0)
    if not mh_ok:
        return ok(False, '%s: max HP %d -> %d with no sudden-death step or fix' % (tag, mh0, mh1))
    lo = min(hp0 - dmg + heal, mh1)
    hi = min(hp0 + heal, mh1)
    if not (lo <= hp1 <= hi):
        return ok(False, '%s: HP %d -> %d (max %d -> %d) not explained: hit %d, heal %d' % (tag, hp0, hp1, mh0, mh1, dmg, heal))
    return True


def inject(sim, f, rnd):
    """a hit through the game's own damage (a live bullet, else a test bullet), a split slash's share of max HP, a heal"""
    if f % 97 == 41:
        # a live bullet's own hit, its target / damage put back after (the Knight's pointing attack has a SOUL follower that is
        # a bullet child: its "target" is the SOUL it follows, so it is never the one picked)
        sim.run('global.inv = -1; var _b = noone; with (obj_bulletparent) { if (_b == noone && string_pos("follower", object_get_name(object_index)) == 0) _b = id; }'
                'if (!instance_exists(_b)) _b = global.TBI;'
                'with (_b) { var _t0 = variable_instance_exists(id, "target") ? target : 0; var _d0 = variable_instance_exists(id, "damage") ? damage : 0;'
                ' target = 0; damage = 40; scr_damage(); target = _t0; damage = _d0; }')
    if f % 331 == 177:
        sim.run('global.inv = -1; with (global.TSL) { target = 0; scr_damage_maxhp(0.66, false, true); }')
    if f % 151 == 90:
        sim.run('kbr_heal(%d, false);' % rnd.choice((20, 40, 80, 300)))


def part_thorn():
    sim, e = match(0, (0, KZ, 4), 1, 250)
    if not ok(e is None, 'thorn: setup %r' % (e,)):
        return
    sim.define_object('obj_testbullet')
    sim.define_object('obj_test_splitslash')   # a split slash's hit without the slash itself (the online table reads "slash" in the name)
    sim.run('global.TBI = instance_create(0, 0, obj_testbullet); global.TSL = instance_create(320, 200, obj_test_splitslash);')
    rnd = random.Random(7)
    prev = J(sim, HPS)
    order = []
    bad0 = len(FAILS)
    for f in range(2600):
        sim.run('global.LED.dmg = 0; global.LED.heal = 0; global.LED.fix = 0;')
        inject(sim, f, rnd)
        err = step(sim, 1)
        if not ok(err is None, 'thorn: frame %d (%s)' % (f, (err or '')[:200])):
            break
        cur = J(sim, HPS)
        if cur[4] != prev[4]:
            order.append(cur[4])
        ledger_check(prev, cur, 0, 0, 'Normal/Kaizo/Thorn frame %d (knight %d)' % (f, cur[4]))
        prev = cur
    ok(KZ in order and 4 in order and 0 in order, 'thorn: Normal, Kaizo and Thorn all fought (switches %s)' % order[:12])
    ok(len(FAILS) == bad0, 'thorn: no unexplained HP change over %d switches' % len(order))
    print('thorn: switches', order[:16], flush=True)


def part_offline():
    from lu_harness import lu_battle
    for name, skin, mh, want in (('Kris 250', 1, 250, 200), ('Noelle 100', 4, 100, 120), ('Kris 150', 1, 150, 150)):
        sim, e = lu_battle('kaizo', party=(skin,), combo=0, hp=mh, world=True)
        if not ok(e is None, 'offline %s: setup %r' % (name, e)):
            continue
        sim.run('with (obj_cutscene_master) instance_destroy();')
        preload_base(sim)
        sim.premocked = premock(sim)
        sim.define_event('obj_battlecontroller', 'Step', 0, BR_STUB)
        sim._snapauto = False
        seen = set()
        for f in range(160):
            err = step(sim, 1)
            if err is not None:
                ok(False, 'offline %s: frame %d %s' % (name, f, err[:200]))
                break
            seen.add((J(sim, 'global.hp[%d]' % skin), J(sim, 'global.maxhp[%d]' % skin)))
        mh_end = J(sim, 'global.maxhp[%d]' % skin)
        ok(mh_end == want, 'offline Kaizo, %s max HP: the fight\'s own rule gives %d (seen %s)' % (name, want, sorted(seen)[:6]))
        ok(J(sim, 'knight_enc_hp_rules()') in (1, True), 'offline %s: the encounter\'s HP rules are on' % name)


def part_maxdmg():
    for online in (True, False):
        if online:
            sim, e = match(0, (0,), 1, 150)
        else:
            from lu_harness import lu_battle
            sim, e = lu_battle('base', party=(1,), combo=0, hp=150, world=False)
            if e is None:
                preload_base(sim)
                sim.premocked = premock(sim)
                sim.define_event('obj_battlecontroller', 'Step', 0, BR_STUB)
                sim._snapauto = False
                sim.load_source('gml_GlobalScript_kz47_ledger', LEDGER)
                sim.run('global.LED = { dmg: 0, heal: 0, fix: 0, hits: 0 };')
        if not ok(e is None, 'maxdmg online=%s: setup' % online):
            continue
        err = None
        for f in range(150):
            err = step(sim, 1)
            if err:
                break
        ok(err is None, 'maxdmg online=%s: frames' % online)
        sim.define_object('obj_test_splitslash')
        sim.run('global.TSL = instance_create(320, 200, obj_test_splitslash); global.LED.dmg = 0; global.LED.hits = 0;')
        hp0 = J(sim, 'global.hp[1]')
        sim.run('global.inv = -1; with (global.TSL) { target = 0; scr_damage_maxhp(0.66, false, true); }')
        hp1 = J(sim, 'global.hp[1]')
        if online:
            ok(hp0 - hp1 == 24 and J(sim, 'global.LED.hits') == 1, 'online split slash: the online table (24 for a slash), a hit counted: %d -> %d' % (hp0, hp1))
            sim.run('global.hp[1] = 150; global.inv = -1; with (global.TSL) { target = 0; scr_damage_maxhp(1.25); }')
            ok(J(sim, 'global.hp[1]') == 126 and not J(sim, 'global.kfo.M.out'), 'online big quick slash: 24 off, not OUT (was 150 -> 1, never told)')
        else:
            ok(hp0 - hp1 == 99, 'offline split slash: 66%% of 150 = 99 as before (%d -> %d)' % (hp0, hp1))


def part_long(cycles, seed, skin, mhp):
    """the ledger over cycles: Kaizo alone (its cycles) and switching in and out of it (Normal, Thorn)"""
    rnd = random.Random(seed)
    kn = (KZ,) if seed % 2 == 0 else (0, KZ, 4)
    sim, e = match(KZ, kn, skin, mhp, setx='_s.sd = 1; _s.ramp = 2; _s.sdfloor = 100; ', seed=1000 + seed)
    if not ok(e is None, 'long: setup %r' % (e,)):
        return
    sim.define_object('obj_testbullet')
    sim.define_object('obj_test_splitslash')   # a split slash's hit without the slash itself (the online table reads "slash" in the name)
    sim.run('global.TBI = instance_create(0, 0, obj_testbullet); global.TSL = instance_create(320, 200, obj_test_splitslash);')
    eff = J(sim, '[global.kfo.M.eff.sdrate, global.kfo.M.eff.sdfloor]')
    prev = J(sim, HPS)
    kz = 0
    sw = 0
    f = 0
    bad0 = len(FAILS)
    t0 = time.time()
    last_k = -1
    while kz < cycles:
        sim.run('global.LED.dmg = 0; global.LED.heal = 0; global.LED.fix = 0;')
        inject(sim, f, rnd)
        # keep the player in the match: an authorised heal when low (the ledger counts it)
        if prev[0] < 60:
            sim.run('kbr_heal(400, false);')
        err = step(sim, 1)
        if not ok(err is None, 'long seed %d: frame %d (%s)' % (seed, f, (err or '')[:200])):
            break
        cur = J(sim, HPS)
        if cur[4] != prev[4]:
            sw += 1
        if cur[5] == 'run' and cur[6] != last_k:
            last_k = cur[6]
            if cur[4] == KZ:
                kz += 1
                if kz % 25 == 0:
                    print('  long seed %d: %d Kaizo cycles, %d switches, frame %d, %.0fs, HP %d/%d' % (seed, kz, sw, f, time.time() - t0, cur[0], cur[1]), flush=True)
        if cur[12]:
            ok(False, 'long seed %d: the player went OUT at frame %d (the run needs them in)' % (seed, f))
            break
        ledger_check(prev, cur, eff[0], eff[1], 'long seed %d frame %d (knight %d, %s)' % (seed, f, cur[4], cur[5]))
        if len(FAILS) - bad0 > 20:
            break
        prev = cur
        f += 1
    print('LONG seed %d skin %d mhp %d: %d Kaizo cycles, %d switches, %d frames, unexplained HP changes: %d, %.0fs'
          % (seed, skin, mhp, kz, sw, f, len(FAILS) - bad0, time.time() - t0), flush=True)


def part_skins():
    """a SKIN is only a look: the same hit takes the same HP from Kris, Susie, Ralsei and Noelle online, under every online
    knight (build 47 found Kaizo's fight halving every hit on Noelle - its own balance rule - after the online damage table)"""
    rows = {}
    for kn in (0, 1, 2, 3, 4):
        drops = []
        for skin in (1, 2, 3, 4):
            sim, e = match(kn, (kn,), skin, 250, hp=250, world=True)
            if not ok(e is None, 'skins: knight %d skin %d setup (%r)' % (kn, skin, e)):
                continue
            sim.define_object('obj_testbullet')
            sim.define_object('obj_test_splitslash')
            sim.run('global.TBI = instance_create(0, 0, obj_testbullet); global.TSL = instance_create(320, 200, obj_test_splitslash);')
            d = []
            for code in ('global.inv = -1; with (global.TBI) { target = 0; damage = 20; scr_damage(); }',
                         'global.inv = -1; with (global.TBI) { target = 0; damage = 60; element = 2; scr_damage(); }',
                         'global.inv = -1; with (global.TSL) { target = 0; scr_damage_maxhp(0.66, false, true); }'):
                h0 = J(sim, 'global.hp[kbr_char()]')
                sim.run(code)
                d.append(h0 - J(sim, 'global.hp[kbr_char()]'))
                sim.run('global.hp[kbr_char()] = 250;')
            drops.append(d)
        rows[kn] = drops
        ok(len(drops) == 4 and all(x == drops[0] for x in drops) and all(v > 0 for v in drops[0]),
           'skins: knight %d - the same hits take the same HP from every SKIN (Kris, Susie, Ralsei, Noelle: %s)' % (kn, drops))
    print('SKINS', rows, flush=True)


def part_eight(frames=1500):
    """eight players in one room, Kaizo Knight the only knight, each with their own HP (60 to 250 of the room's 250): every
    game's HP ledger over the match (hits, heals, the host's fix: nothing else), and each player's own account: their HP
    is always their start HP plus their own heals minus their own hits - nobody's HP follows anybody else's"""
    from br_multi import make_room, install
    t0 = time.time()
    hps = [250, 75, 100, 180, 200, 230, 120, 60]
    net, sims = make_room(8, 'lan', 4747, setx='_s.mhp = 250; _s.hp0 = 100; _s.rush = 0;', open_ok=KZ, kn=(KZ,), world=True)
    for i, s in enumerate(sims):
        s.load_source('gml_GlobalScript_kz47_ledger', LEDGER)
        s.define_object('obj_testbullet')
        s.run('global.LED = { dmg: 0, heal: 0, fix: 0, hits: 0 }; with (obj_cutscene_master) instance_destroy();'
              'kfo_kit_apply(kbr_char()); global.char = [kbr_char(), 0, 0]; global.hp[kbr_char()] = %d; global.TBI = instance_create(0, 0, obj_testbullet);' % hps[i])
    start = [J(s, HPS)[:2] for s in sims]
    ok(start == [[h, 250] for h in hps], 'eight: each player starts with their own HP (%s)' % start)
    prev = [J(s, HPS) for s in sims]
    pred = list(hps)
    acct_bad = 0
    bad0 = len(FAILS)
    rnd = random.Random(8)
    kz = 0
    last_k = -1
    hits = [0] * 8
    for f in range(frames):
        net.t += 1000.0 / 30.0
        for i, s in enumerate(sims):
            s.run('test_net_pump(); global.LED.dmg = 0; global.LED.heal = 0; global.LED.fix = 0;')
            s.kb = set([rnd.choice(['left', 'right', 'up', 'down'])]) if f % 9 < 6 else set()
            # each player their own hits (5, 10 ... 40 a time through the game's damage) and small heals
            if f % 97 == 11 + i * 9:
                s.run('global.inv = -1; with (global.TBI) { target = 0; damage = %d; scr_damage(); }' % (5 * (i + 1)))
            if f % 211 == 40 + i * 13:
                s.run('kbr_heal(%d, false);' % rnd.choice((15, 40)))
            err = step(s, 1)
            if not ok(err is None, 'eight: game %d frame %d (%s)' % (i + 1, f, (err or '')[:200])):
                return
            cur = J(s, HPS)
            if i == 0 and cur[5] == 'run' and cur[6] != last_k:
                last_k = cur[6]
                kz += 1
            if cur[12]:
                prev[i] = cur
                continue
            hits[i] += cur[9]
            ledger_check(prev[i], cur, 0, 0, 'eight: game %d frame %d' % (i + 1, f))
            # the player's own account (a host fix sets HP itself: the account follows it)
            if cur[11] > 0:
                pred[i] = cur[0]
            else:
                pred[i] = max(0, min(cur[1], pred[i] + cur[10]) - cur[9])
                if pred[i] != cur[0]:
                    acct_bad += 1
                    if acct_bad <= 3:
                        print('  eight: game %d frame %d: HP %d, own account %d' % (i + 1, f, cur[0], pred[i]), flush=True)
                    pred[i] = cur[0]
            prev[i] = cur
        if len(FAILS) - bad0 > 20:
            break
    fin = [J(s, HPS)[:2] for s in sims]
    print('EIGHT: %d frames, %d Kaizo cycles, unexplained %d, own-account mismatches %d, end HP %s, damage taken %s, %.0fs'
          % (frames, kz, len(FAILS) - bad0, acct_bad, fin, hits, time.time() - t0), flush=True)
    ok(len(FAILS) == bad0, 'eight: 8 players, %d Kaizo cycles - every HP change in every game explained (%d unexplained)' % (kz, len(FAILS) - bad0))
    ok(acct_bad == 0, 'eight: every player\'s HP is their own start + heals - hits at every frame (%d mismatches; end HP %s)' % (acct_bad, [h for h, m in fin]))
    ok(all(m == 250 for h, m in fin) and len(set(h for h, m in fin)) > 1, 'eight: max HP 250 kept by all, the HPs still their own (%s)' % fin)


if __name__ == '__main__':
    args = sys.argv[1:] or ['entry', 'heal', 'maxhp', 'thorn', 'offline', 'maxdmg', 'skins']
    t0 = time.time()
    if args[0] == 'long':
        part_long(int(args[1]), int(args[2]), int(args[3]), int(args[4]))
    else:
        for a in args:
            print('== part', a, flush=True)
            globals()['part_' + a]()
    print('t_kaizo47: %d checks, %d failed, %.0fs' % (N[0], len(FAILS), time.time() - t0))
    for m in FAILS[:30]:
        print('  ', m)
    sys.exit(1 if FAILS else 0)
