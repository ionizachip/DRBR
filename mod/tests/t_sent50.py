"""Build 50: the players' attack skills are the Knights' REAL attack objects. Two emulated games in one room (the real merged
fight code and the real online code over the simulated network), one knight at a time (KN env: 0-5, default all):

  - every item the knight's pool allows is sent from game 1 to game 2: game 2 makes it from the real objects (the expected
    object is there, adopted into the send: kbr, kbrx, sender, target, damage, variant), game 1 makes nothing;
  - the send's instances are tinted in the sender's colour at End Step and get their own colour back at Begin Step;
  - a hit on game 2's SOUL is credited to the sender (lby) with the item's damage;
  - everything the send made is gone when it is over (no instance with kbrx, no send left, no surface);
  - the new items (17-21) are drawn only when their knight is in the pool;
  - the Knight's own fight is not changed: both games keep the same attack stream count and the same Knight bullets at
    30 / 60 / 90 frames of every attack (br_multi.compare), with no errors, while the sends run in game 2 only.
Usage: python3 t_sent50.py   (KN=1 python3 t_sent50.py: Kaizo only)"""
import sys, os, json, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from br_multi import *

FAILS = []
N = [0]


def ok(c, msg):
    N[0] += 1
    print(('ok   ' if c else 'FAIL ') + msg, flush=True)
    if not c:
        FAILS.append(msg)


def J(s, e):
    return s.py(s.eval(e))


# what each item must put up (one of these objects, adopted)
EXPECT = {1: ['obj_tracking_sword1'], 2: ['obj_tracking_sword1'], 3: ['obj_diagonal_bullet__v1'], 4: ['obj_roaringknight_split_bullet'],
          5: ['obj_knight_pointing_star'], 6: ['obj_knight_pointing_star'], 7: ['obj_knight_weird_circle'], 10: ['obj_knight_circle', 'obj_roaringknight_slash'],
          17: ['obj_bullet_knightcrescent'], 18: ['obj_fallingsword__v1'], 19: ['obj_knight_lightningshock'], 20: ['obj_roaringknight_fountain_bullet'],
          21: ['obj_knight_weird_circle']}
# what each item's children must include at some point (the real attack's own follow-ups)
LATER = {1: 'obj_tracking_sword_slash', 5: 'obj_knight_pointing_starchild', 6: 'obj_knight_pointing_starchild', 7: 'obj_knight_weird_circle_bullet',
         10: 'obj_roaringknight_slash', 21: 'obj_regularbullet'}
KNIGHT_OF = {17: 1, 18: 1, 19: 2, 20: 4, 21: 3}

SENT = ('global.SL = []; var _L = [obj_bulletparent, obj_bulletgenparent, obj_knight_circle, obj_particle_generic, obj_lerpvar, obj_script_delayed, obj_afterimage];'
        'for (var _j = 0; _j < array_length(_L); _j++) with (_L[_j]) { if (variable_instance_exists(id, "kbrx") && kbrx > 0 && !variable_instance_exists(id, "kbrtw")) array_push(global.SL, [object_get_name(object_index), kbrx, kbr, kbrf, kbrt, kbrd, kbrkv,'
        ' image_blend, (variable_instance_exists(id, "kbrtb") ? kbrtb : -2), (variable_instance_exists(id, "kbrb") ? kbrb : -2)]); }')


def sent(s):
    s.run(SENT)
    return J(s, 'global.SL')


def keep(f, sims, prev):
    if f % 10 == 0:
        for s in sims:
            s.run('if (is_struct(global.kfo.M) && !global.kfo.M.out) { global.hp[kbr_char()] = global.maxhp[kbr_char()]; }')
            s.log.clear()


def go(net, sims, n, allrec):
    rec = run(net, sims, n, 'none', on_frame=keep, wall=1800)
    errs = {c: rec[c]['errors'][:1] for c in range(1, len(sims) + 1) if rec[c]['errors']}
    allrec.append(rec)
    if errs:
        ok(False, 'no errors in the games: %r' % errs)
        raise SystemExit(1)
    return rec


def wait_run(net, sims, allrec):
    for _ in range(240):
        if all(J(s, 'global.kfo.M.R.ph') == 'run' and J(s, 'global.kfo.M.R.af') < 40 for s in sims) and J(sims[1], 'instance_exists(obj_growtangle) && instance_find(obj_growtangle, 0).x > -1000'):
            return True
        go(net, sims, 5, allrec)
    return False


def merge_recs(recs, n):
    out = {c: {'starts': [], 'snaps': {}, 'errors': []} for c in range(1, n + 1)}
    for r in recs:
        for c in range(1, n + 1):
            out[c]['starts'] += r[c]['starts']
            out[c]['snaps'].update(r[c]['snaps'])
            out[c]['errors'] += r[c]['errors']
    return out


def one_knight(K):
    t0 = time.time()
    net, sims = make_room(2, 'lan', 5050 + K, setx='_s.mhp = 300; _s.cdm = 25; _s.g0 = 50;', open_ok=K, kn=(K,))
    H, C = sims
    if os.environ.get('OTHER_SELF'):
        # a runner whose Create event does not name its maker (`other` is the new instance itself): the adoption falls back
        # to the side whose event is running (kbr_ev_in)
        for s in sims:
            def _ci(obj, x=0, y=0, depth=0, vars=None, creator=None, _o=s.create_instance):
                return _o(obj, x, y, depth, vars, None)
            s.create_instance = _ci
    allrec = []
    go(net, sims, 330, allrec)
    ok(J(C, 'global.kfo.M.go'), 'knight %d: the match runs (%.0fs)' % (K, time.time() - t0))
    # the pool: a knight's own items only with that knight in it
    for sid, k in KNIGHT_OF.items():
        ok(J(C, 'kbr_skill_ok(%d)' % sid) == (k == K), 'knight %d: item %d (%s) allowed = %r' % (K, sid, J(C, 'kbr_skill_name(%d)' % sid), k == K))
    items = [1, 2, 3, 4, 5, 6, 7, 10] + [sid for sid, k in KNIGHT_OF.items() if k == K]
    my2 = J(C, 'global.kfo.my')
    my1 = J(H, 'global.kfo.my')
    col1 = J(C, 'kbr_pcol(kbr_pslot(%d))' % my1)
    for sid in items:
        if not wait_run(net, sims, allrec):
            ok(False, 'knight %d: no running attack for item %d' % (K, sid))
            continue
        C.run('global.kfo.M.lby = -1; global.kfo.M.taken = 0;')
        H.run('var _S = global.kfo.M.sk; array_push(_S.slots, { sid: %d, rev: 0 }); _S.sel = array_length(_S.slots) - 1; _S.cd = 0; global.USED = kbr_skill_use();' % sid)
        ok(J(H, 'global.USED') == 1, 'knight %d: player 1 uses %s' % (K, J(H, 'kbr_skill_name(%d)' % sid)))
        seen = set()
        made = False
        tinted = False
        restored = True
        attrs_ok = True
        groups = 0
        hit_done = False
        hit_d = 0
        for f in range(0, 260, 2):
            go(net, sims, 2, allrec)
            sl = sent(C)
            seen |= set(J(C, 'is_struct(global.kbr_sa_last) ? variable_struct_get_names(global.kbr_sa_last.seen) : []'))
            groups = max(groups, J(C, '(function(){ var _n = 0; for (var _i = 0; _i < array_length(global.kbr_sa); _i++) if (!global.kbr_sa[_i].twin) _n++; return _n; })()'))
            for r in sl:
                seen.add(r[0])
                made = True
                if not (r[2] == 1 and r[3] == my1 and r[4] == my2 and r[5] > 0):
                    attrs_ok = False
                # tinted for drawing after End Step (the emulator's frame ends after End Step)
                if r[8] not in (-1, -2) and r[7] == r[8] and r[9] != r[7]:
                    tinted = True
            # a hit: the first live sent bullet touches the SOUL (its own hit event, as obj_heart's collision runs it)
            if not hit_done and any(r[2] == 1 for r in sl) and (sid not in LATER or LATER[sid] in seen):
                # (the emulator has no collision masks: the precise-hit test of the stars says yes, as when it touches)
                C.mock('scr_precise_hit', lambda s, *a: 1)
                C.run('global.HIT = -1; global.inv = -1; with (obj_collidebullet) { if (global.HIT == -1 && variable_instance_exists(id, "kbrx") && kbrx > 0 && !variable_instance_exists(id, "kbrtw") && active == 1 && object_index != obj_knight_pointing_star) { global.HIT = kbrd; event_user(5); } }')
                C.run('global.inv = -1;')
                if J(C, 'global.HIT') != -1:
                    hit_done = True
                    hit_d = J(C, 'global.HIT')
            if f > 40 and not sl and J(C, '(function(){ var _n = 0; for (var _i = 0; _i < array_length(global.kbr_sa); _i++) if (!global.kbr_sa[_i].twin) _n++; return _n; })()') == 0:
                break
        seen |= set(J(C, 'is_struct(global.kbr_sa_last) ? variable_struct_get_names(global.kbr_sa_last.seen) : []'))
        why = J(C, 'global.kbr_sa_why')
        if why:
            print('     (the send was ended early: %s)' % why)
        C.run('global.kbr_sa_why = "";')
        hs = sent(H)
        ok(made and any(o in seen for o in EXPECT[sid]), 'knight %d: %s is made of %s in the target\'s game (%s)' % (K, J(C, 'kbr_skill_name(%d)' % sid), '/'.join(EXPECT[sid]), sorted(seen)[:6]))
        if sid in LATER:
            ok(LATER[sid] in seen, 'knight %d: ... and its own follow-up %s comes (%s)' % (K, LATER[sid], sorted(seen)[:8]))
        ok(attrs_ok, 'knight %d: every instance of it is adopted (kbr, sender %d, target %d, damage)' % (K, my1, my2))
        ok(tinted, "knight %d: tinted in the sender's colour" % K)
        ok(len(hs) == 0, "knight %d: the sender's game makes none of it" % K)
        lby = J(C, 'global.kfo.M.lby')
        tk = J(C, 'global.kfo.M.taken')
        print('     hits: taken %s, last hit by %s' % (tk, lby))
        exp = round(hit_d * J(C, 'global.kfo.M.eff.skdmg') / 100 * J(C, 'global.kfo.M.eff.dmul') / 100)
        ok(hit_done and lby == my1 and tk == exp, 'knight %d: a hit takes the item\'s damage (%s, expected %s) and is credited to the sender (%r)' % (K, tk, exp, lby))
        # cleanup
        for _ in range(40):
            if J(C, '(function(){ var _n = 0; for (var _i = 0; _i < array_length(global.kbr_sa); _i++) if (!global.kbr_sa[_i].twin) _n++; return _n; })()') == 0 and J(C, '(function(){ var _n = 0; var _L = [obj_bulletparent, obj_bulletgenparent, obj_knight_circle]; for (var _j = 0; _j < 3; _j++) with (_L[_j]) if (variable_instance_exists(id, "kbrx") && kbrx > 0 && !variable_instance_exists(id, "kbrtw")) _n++; return _n; })()') == 0:
                break
            go(net, sims, 10, allrec)
        ok(J(C, '(function(){ var _n = 0; for (var _i = 0; _i < array_length(global.kbr_sa); _i++) if (!global.kbr_sa[_i].twin) _n++; return _n; })()') == 0 and J(C, '(function(){ var _n = 0; var _L = [obj_bulletparent, obj_bulletgenparent, obj_knight_circle]; for (var _j = 0; _j < 3; _j++) with (_L[_j]) if (variable_instance_exists(id, "kbrx") && kbrx > 0 && !variable_instance_exists(id, "kbrtw")) _n++; return _n; })()') == 0 and len(sent(C)) == 0,
           'knight %d: nothing of it is left (sends %d, instances %d)' % (K, J(C, '(function(){ var _n = 0; for (var _i = 0; _i < array_length(global.kbr_sa); _i++) if (!global.kbr_sa[_i].twin) _n++; return _n; })()'), len(sent(C))))
        ok(J(C, 'global.kbr_sa_surf') == -1 or J(C, '(function(){ var _n = 0; for (var _i = 0; _i < array_length(global.kbr_sa); _i++) if (!global.kbr_sa[_i].twin) _n++; return _n; })()') > 0, 'knight %d: no surface left' % K)
    # the Knight's own fight: the same in both games while the sends ran in game 2 only
    go(net, sims, 200, allrec)
    rec = merge_recs(allrec, 2)
    cmp = compare(rec, 2)
    ok(not cmp['logic_bad'], "knight %d: both games run the same attacks (%r)" % (K, cmp['logic_bad'][:2]))
    ok(not cmp['arena_bad'], "knight %d: the box is the same in both games (%r)" % (K, cmp['arena_bad'][:2]))
    ok(cmp['bul_diff'] == 0 and cmp['bul_same'] > 0, "knight %d: the Knight's own bullets are the same in both games at 30/60/90 frames (%d same, %d differ %r)"
       % (K, cmp['bul_same'], cmp['bul_diff'], cmp['bul_diff_list'][:2]))
    rn = []
    for k in rec[1]['snaps']:
        if k in rec[2]['snaps']:
            rn.append(rec[1]['snaps'][k]['rn'] == rec[2]['snaps'][k]['rn'])
    ok(rn and all(rn), "knight %d: the shared attack stream is drawn the same in both games (%d checks)" % (K, len(rn)))
    print('knight %d done in %.0fs' % (K, time.time() - t0), flush=True)


if __name__ == '__main__':
    kns = [int(x) for x in os.environ.get('KN', '0,1,2,3,4,5').split(',')]
    for K in kns:
        one_knight(K)
    print('%d checks, %d failed' % (N[0], len(FAILS)))
    for f in FAILS:
        print('FAILED:', f)
    sys.exit(1 if FAILS else 0)
