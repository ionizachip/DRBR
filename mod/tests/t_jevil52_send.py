"""Build 52: JEVIL's sendable skills (ids 26-31) in a room of three games (br_multi: the real code in every game, the simulated
network). The host sends each one at player 2 (TARGETING: CHECK on player 2). Checked for each:
  - player 2's game builds it from Jevil's real pieces (obj_jv_*): a send group of that skill that made instances, every one
    marked as the host's send aimed at player 2;
  - its pieces in player 2's game are live hurting bullets (the emulator has no collision), player 3's game and the host's build none of its real pieces and
    take no hit from it (only the target is hurt);
  - no error in any game.
Also: SKILL FAMILIES - with JEVIL only Jevil's attack skills (and the effects / greens) are drawn, with KNIGHT none of his.
Usage: python3 t_jevil52_send.py"""
import sys, os, json, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from br_multi import *
import t_view47

FAILS = []
N = [0]


def ok(c, m):
    N[0] += 1
    print(('ok   ' if c else 'FAIL ') + m, flush=True)
    if not c:
        FAILS.append(m)


def J(s, e):
    return s.py(s.eval(e))


NAMES = {26: 'Spade Ring', 27: 'Diamond Rain', 28: 'Club Spiral', 29: 'Heart Carousel', 30: 'Devilsknife', 31: 'Chaos Bombs'}
t0 = time.time()
net, sims = make_room(3, 'lan', 5260, setx='_s.mhp = 999; _s.skfam = 3; _s.cdm = 10; _s.dmul = 25; _s.ifr = 25;', kn=(0, 6), open_ok=0)
H, C2, C3 = sims
# every hit, with its sender (-1: the shared attack), in every game
src = t_view47.func_src('kbr_dmg_taken').replace('function kbr_dmg_taken(', 'function kbr_dmg_taken__orig(', 1)
for s in sims:
    s.load_source('gml_GlobalScript_jvsend_wrap', src + '''
function kbr_dmg_taken(_d) { var _f = (variable_instance_exists(id, "kbr") && kbr != 0 && variable_instance_exists(id, "kbrf")) ? kbrf : -1;
  var _sid = -1; if (variable_instance_exists(id, "kbrx")) { var _G = kbr_sa_find(kbrx); if (is_struct(_G)) _sid = _G.sid; }
  if (!variable_global_exists("JVH") || !is_array(global.JVH)) global.JVH = [];
  array_push(global.JVH, [_f, _sid, object_get_name(object_index)]); return kbr_dmg_taken__orig(_d); }
''')
    s.run('global.JVH = [];')


def go(n):
    rec = run(net, sims, n, 'none', wall=900)
    errs = {c: rec[c]['errors'][:1] for c in range(1, 4) if rec[c]['errors']}
    if errs:
        ok(False, 'no errors in the games: %r' % errs)
        raise SystemExit(1)


def keep_hp():
    for s in sims:
        s.run('if (is_struct(global.kfo.M) && !global.kfo.M.out) global.hp[kbr_char()] = global.maxhp[kbr_char()];')


go(300)
ok(J(H, 'global.kfo.M.go'), 'the match runs')
p2 = J(C2, 'global.kfo.my')
hostp = J(H, 'global.kfo.my')
ok(J(H, 'kbr_skill_ok(26) && kbr_skill_ok(31) && kbr_skill_ok(1)'), 'SKILL FAMILIES ALL: Jevil\'s and the knights\' attacks can be drawn')
for sid in range(26, 32):
    for s in sims:
        s.run('global.JVH = [];')
    H.run('global.kfo.M.tg.mode = 4; global.kfo.M.tg.pick = %d; kbr_tg_send(global.kfo.M, true);' % p2)
    go(4)
    H.run('var _S = global.kfo.M.sk; array_push(_S.slots, { sid: %d, rev: 0 }); _S.sel = array_length(_S.slots) - 1; _S.cd = 0; global.U = kbr_skill_use();' % sid)
    made2 = 0
    seen2 = set()
    tagged_ok = True
    armed2 = 0
    for f in range(0, 160, 8):
        go(8)
        keep_hp()
        g = J(C2, '(function(){ var _o = []; for (var _i = 0; _i < array_length(global.kbr_sa); _i++) { var _G = global.kbr_sa[_i]; if (_G.sid == %d && !_G.watch) array_push(_o, [_G.made, variable_struct_get_names(_G.seen)]); } return _o; })()' % sid)
        for m, names in g:
            made2 = max(made2, m)
            seen2 |= set(names)
        bad = J(C2, '(function(){ var _n = 0; with (obj_bulletparent) { if (variable_instance_exists(id, "kbrx") && variable_instance_exists(id, "kbr") && kbr != 0 && (kbrf != %d || kbrt != %d)) _n++; } return _n; })()' % (hostp, p2))
        if bad:
            tagged_ok = False
        armed2 = max(armed2, J(C2, '(function(){ var _n = 0; with (obj_bulletparent) { if (variable_instance_exists(id, "kbrx") && variable_instance_exists(id, "kbr") && kbr != 0 && variable_instance_exists(id, "kbrd") && kbrd > 0) _n++; } return _n; })()'))
    other = [J(s, '(function(){ var _n = 0; for (var _i = 0; _i < array_length(global.kbr_sa); _i++) { var _G = global.kbr_sa[_i]; if (_G.sid == %d && !_G.watch && !_G.twin) _n++; } return _n; })()' % sid) for s in (H, C3)]
    hits = {c: J(s, 'global.JVH') for c, s in ((1, H), (2, C2), (3, C3))}
    from_host = {c: sum(1 for h in hits[c] if h[0] == hostp) for c in hits}
    ok(J(H, 'global.U') == 1, '%s: the host sent it' % NAMES[sid])
    ok(made2 > 0 and any(n.startswith('obj_jv_') for n in seen2), "%s: player 2's game built it from Jevil's pieces (%d made: %s)" % (NAMES[sid], made2, sorted(seen2)))
    ok(tagged_ok, "%s: every piece in player 2's game is the host's send aimed at player 2" % NAMES[sid])
    # (the emulator has no collision: the pieces are checked to be live, hurting bullets of the send - a hit goes through kbr_dmg_taken as the knights' sends do)
    ok(armed2 > 0, "%s: its pieces in player 2's game are live, hurting bullets (up to %d at once)" % (NAMES[sid], armed2))
    ok(other == [0, 0] and from_host[1] == 0 and from_host[3] == 0, '%s: the host and player 3 build none of it and take no hit from it (groups %r, hits %r)' % (NAMES[sid], other, [from_host[1], from_host[3]]))
    go(60)
# SKILL FAMILIES
H.run('global.kfo.M.eff.skfam = 2;')
fam_j = J(H, '[kbr_skill_ok(26), kbr_skill_ok(30), kbr_skill_ok(1), kbr_skill_ok(10), kbr_skill_ok(8), kbr_skill_ok(11)]')
ok(fam_j == [True, True, False, False, True, True], 'SKILL FAMILIES JEVIL: his attacks yes, the knights\' no, effects and greens yes %r' % fam_j)
H.run('global.kfo.M.eff.skfam = 1;')
fam_k = J(H, '[kbr_skill_ok(26), kbr_skill_ok(30), kbr_skill_ok(1), kbr_skill_ok(10), kbr_skill_ok(8), kbr_skill_ok(11)]')
ok(fam_k == [False, False, True, True, True, True], 'SKILL FAMILIES KNIGHT: his attacks no %r' % fam_k)
# DRBR: SENDS 0 is CURRENT BOSS (build 52's MATCH meant every family in the match): the family of the boss on stage - the
# lineup's active entry. Each kind of entry the lineup has is put on stage in turn (then the real one back).
H.run('global.kfo.M.eff.skfam = 0;')
ks = J(H, 'global.knight_lu.ks')
act0 = J(H, 'global.knight_lu.act')
seen_kinds = []
for i, k in enumerate(ks):
    kind = 'jevil' if k == 1000 else ('knight' if k < 1000 else None)
    if kind is None or kind in seen_kinds:
        continue
    seen_kinds.append(kind)
    H.run('global.knight_lu.act = %d;' % i)
    want = [True, False] if kind == 'jevil' else [False, True]
    got = J(H, '[kbr_skill_ok(26), kbr_skill_ok(1)]')
    ok(got == want, 'SENDS CURRENT BOSS, %s on stage: %s %r' % (kind, "his attacks, not the knights'" if kind == 'jevil' else "the knights', none of his", got))
H.run('global.knight_lu.act = %d;' % act0)
ok(len(seen_kinds) >= 1, 'SENDS CURRENT BOSS: checked with %r on stage' % seen_kinds)
# the draw: with JEVIL, a thousand draws never give a knight's attack
H.run('global.kfo.M.eff.skfam = 2; global.kfo.M.eff.kn = [0, 6]; global.DR = []; repeat (600) array_push(global.DR, kbr_skill_draw(100));')
dr = J(H, 'global.DR')
ok(all(not ((1 <= x <= 7) or x == 10 or 17 <= x <= 21) for x in dr) and any(26 <= x <= 31 for x in dr), 'SKILL FAMILIES JEVIL: 600 full draws, no knight attack, Jevil\'s drawn (%d of his)' % sum(1 for x in dr if 26 <= x <= 31))
print('jevil52 send: %d checks, %d failed (%.0fs)' % (N[0], len(FAILS), time.time() - t0))
for f in FAILS:
    print('  -', f)
sys.exit(1 if FAILS else 0)
