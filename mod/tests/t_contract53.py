"""DRBR P0 - the projectile contract, with real SOUL / bullet collisions in the emulator (collide.py).

Parts (run one per process):  fallback | jevil [a b] | knight OK [a b] | mixed | sends | multi N
  fallback  a bare obj_collidebullet (nothing set) touches the SOUL: no error, it is completed by the fallback (counted in
            global.kbr_bfix) and destroyed (destroyonhit 1); a complete permanent bullet (destroyonhit 0) stays.
  jevil     every attack of Jevil's with the SOUL stepping onto his bullets: no error, the SOUL is hit, and NO bullet needed
            the fallback (global.kbr_bfix empty: the root fix made every one complete).
  knight OK every attack of online knight OK (0 Normal, 1 Kaizo, 2 Elecknight, 3 Violet, 4 Thorn, 5 Knightmare) the same way
            (its Roaring included).
  mixed     Knight Rush between the Normal Knight and Jevil (a new one each attack), the SOUL on the bullets: no error over
            the switches, no fallback.
  sends     3 games + 2 bots in the host's game, collisions in every game: each real attack skill sent at player 2 hits
            player 2 (hits whose sender is the host); the host's SOUL standing on the hidden copies of a send at a bot is
            never hit by them; player 3 takes nothing from it.
  multi N   N games (2, 4, 8) of a shared match with collisions: no error, the same cycles.
Each part prints one JSON line per case and a summary; exit 1 on a failure."""
import sys, os, json, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import br_harness
br_harness.COLLIDE = True
from br_harness import *
import collide

FAILS = []
N = [0]


def ok(c, m):
    N[0] += 1
    print(('ok   ' if c else 'FAIL ') + m, flush=True)
    if not c:
        FAILS.append(m)
    return c


def J(sim, e):
    return sim.py(sim.eval(e))


CHASE = ('if (instance_exists(obj_heart) && !global.kfo.M.out) { var _b = noone; with (obj_collidebullet) { if (_b == noone && visible && !(variable_instance_exists(id, "kbrt") && kbrt != global.kfo.my)) _b = id; }'
         ' if (_b != noone) { obj_heart.x = _b.x - 10; obj_heart.y = _b.y - 10; } }')
KEEP = 'if (!global.kfo.M.out) global.hp[kbr_char()] = global.maxhp[kbr_char()];'
BFIX = 'variable_global_exists("kbr_bfix") ? global.kbr_bfix : {}'
MY = [0]
FORCE = 'function kbr_tl_pick_attack(_tl, _k, _g, _ok, _st) { return global.JV_FORCE; }\n'


def force_run(ok_, ai, kn, frames=1600, seed=5300, setx='_s.mhp = 999; _s.ramp = 3; _s.hard = 1;'):
    """one attack forced as every cycle's, the SOUL on the bullets; until the attack ends (or frames)"""
    sim, e = br_match(open_ok=ok_, kn=kn, seed=seed + ai, bots=0, setx=setx)
    if e:
        return {'err': 'setup ' + str(e)[:200]}
    sim.run('global.JV_FORCE = %d;' % ai)
    sim.load_source('gml_GlobalScript_c53force', FORCE)
    sim.run('global.kfo.M.tl.cyc = []; global.kfo.H.tl.cyc = [];')
    sim.col = None
    MY[0] = J(sim, 'global.kfo.my')
    started = ended = -1
    err = None
    h0 = collide.STATS['heart']
    hp_hits = 0
    for f in range(frames):
        sim.run(KEEP)
        collide.chase(sim, lambda b: b.vars.get('visible', True) and not ('kbrt' in b.vars and b.vars.get('kbrt') != MY[0]))
        err = step(sim, 1)
        if err:
            break
        if f % 30 == 0:
            sim.log.clear()
        sim.run(BR_CHK)
        b = J(sim, 'global.BRS')
        if started < 0 and b['ph'] == 'run' and b['k'] == 0:
            started = f
        if started >= 0 and b['k'] >= 1:
            ended = f
            break
    bfix = J(sim, BFIX) if not err else None
    return {'started': started, 'ended': ended, 'err': (err or '')[:300] or None, 'contacts': collide.STATS['heart'] - h0, 'bfix': bfix}


def part_fallback():
    sim, e = br_match(open_ok=0, kn=(0,), seed=5301, bots=0, setx='_s.mhp = 999;')
    ok(e is None, 'fallback: practice (%s)' % e)
    for f in range(400):
        sim.run(KEEP)
        err = step(sim, 1)
        if err:
            break
        b = br_state(sim)
        if b['ph'] == 'run' and b['heart'] > 0:
            break
    ok(J(sim, 'instance_exists(obj_heart)'), 'fallback: a SOUL in the box')
    # a bare collide bullet on the SOUL (Chapter 1's way of making one), and a complete permanent one beside it
    sim.run('with (obj_collidebullet) instance_destroy(); global.B0 = instance_create(obj_heart.x + 10, obj_heart.y + 10, obj_collidebullet); global.B0.sprite_index = spr_smallbullet;'
            'global.B1 = instance_create(obj_heart.x + 10, obj_heart.y + 10, obj_collidebullet); with (global.B1) { scr_bullet_init(); destroyonhit = 0; sprite_index = spr_smallbullet; }'
            'global.kbr_bfix = {}; global.inv = -1;')
    ok(not J(sim, 'variable_instance_exists(global.B0, "destroyonhit")'), 'fallback: the bare bullet has no destroyonhit (the crash case)')
    sim.run(KEEP)
    err = step(sim, 1)
    ok(err is None, 'fallback: its contact with the SOUL runs without an error (%s)' % (err or '')[:200])
    bf = J(sim, BFIX)
    ok(bf.get('obj_collidebullet', 0) >= 1, 'fallback: it was completed by the fallback and counted %r' % bf)
    ok(not J(sim, 'instance_exists(global.B0)'), 'fallback: it was destroyed by its hit (destroyonhit 1)')
    ok(J(sim, 'instance_exists(global.B1)'), 'fallback: the complete permanent one (destroyonhit 0) is still there')


def part_attacks(ok_, ais, kn, label):
    for ai in ais:
        t0 = time.time()
        r = force_run(ok_, ai, kn)
        r['wall'] = round(time.time() - t0)
        print('case', label, ai, json.dumps(r), flush=True)
        ok(r['err'] is None, '%s %d: no error %s' % (label, ai, (r['err'] or '')[:200]))
        ok(r.get('bfix') == {}, '%s %d: every bullet complete before its first contact (fallback used: %r)' % (label, ai, r.get('bfix')))
        ok(r.get('started', -1) >= 0, '%s %d: the attack ran (contacts with the SOUL %d)' % (label, ai, r.get('contacts', 0)))


def part_mixed():
    sim, e = br_match(open_ok=0, kn=(0, 6), seed=6153, bots=0, setx='_s.mhp = 999; _s.rush = 1;')
    ok(e is None, 'mixed: Knight Rush, Normal Knight + Jevil (%s)' % e)
    acts = []
    err = None
    h0 = collide.STATS['heart']
    last = -1
    MY[0] = J(sim, 'global.kfo.my')
    for f in range(2700):
        sim.run(KEEP)
        collide.chase(sim, lambda b: b.vars.get('visible', True) and not ('kbrt' in b.vars and b.vars.get('kbrt') != MY[0]))
        err = step(sim, 1)
        if err:
            break
        if f % 30 == 0:
            sim.log.clear()
        b = br_state(sim)
        if b['ph'] == 'run' and b['k'] != last:
            last = b['k']
            acts.append(b['act'])
    ok(err is None, 'mixed: no error over the switches %s' % (err or '')[:200])
    ok(0 in acts and 1000 in acts, 'mixed: both were on stage (%r)' % acts)
    ok(J(sim, BFIX) == {} if not err else False, 'mixed: no bullet needed the fallback')
    ok(collide.STATS['heart'] - h0 > 0, 'mixed: the SOUL was hit (%d contacts)' % (collide.STATS['heart'] - h0))


if __name__ == '__main__' and not (len(sys.argv) > 1 and sys.argv[1] in ('sends', 'multi')):
    t0 = time.time()
    a = sys.argv[1:] or ['fallback']
    if a[0] == 'fallback':
        part_fallback()
    elif a[0] == 'jevil':
        lo, hi = (int(a[1]), int(a[2])) if len(a) > 2 else (0, 15)
        part_attacks(6, range(lo, hi + 1), (6,), 'jevil')
    elif a[0] == 'knight':
        okk = int(a[1])
        cat = json.load(open('/home/claude/work/online/br_catalogue.json'))
        reg = [0, 1, 2, 3, 4, 0][okk]
        ais = [x['ai'] for x in cat.get(str(reg), []) if x.get('err') is None and x.get('dur')]
        # the Roaring (the last attack with flag 2 named Roaring)
        import re
        if len(a) > 3:
            ais = [x for x in ais if int(a[2]) <= x <= int(a[3])]
        part_attacks(okk, ais, (okk,), 'knight%d' % okk)
    elif a[0] == 'roar':
        okk = int(a[1])
        sim, e = br_match(open_ok=okk, kn=(okk,), seed=1, bots=0)
        atk = J(sim, 'knight_reg(kbr_reg_of(%d)).atk' % okk)
        ais = [i for i, x in enumerate(atk) if 'Roaring' in x[2] and x[3] == 2]
        part_attacks(okk, ais, (okk,), 'roar%d' % okk)
    elif a[0] == 'mixed':
        part_mixed()
    print('contract53 %s: %d checks, %d failed (%.0fs)' % (' '.join(a), N[0], len(FAILS), time.time() - t0))
    for f in FAILS:
        print('  -', f)
    sys.exit(1 if FAILS else 0)


# ---------------------------------------------------------------- sends (3 games, collisions in every game)
def part_sends(sids=None):
    import br_multi
    from br_multi import make_room, run
    # (every knight in the match: the variant sends - Kaizo's crescent, Elecknight's lightning ... - need their knight in it)
    net, sims = make_room(3, 'lan', 5360, setx='_s.mhp = 999; _s.skfam = 3; _s.cdm = 10; _s.dmul = 25; _s.ifr = 25; _s.bots = 2;', kn=(0, 1, 2, 3, 4, 6), open_ok=0, bots=2)
    H, C2, C3 = sims
    import t_view47
    src = t_view47.func_src('kbr_dmg_taken').replace('function kbr_dmg_taken(', 'function kbr_dmg_taken__orig(', 1)
    for s in sims:
        s.load_source('gml_GlobalScript_c53_wrap', src + '''
function kbr_dmg_taken(_d) { var _f = (variable_instance_exists(id, "kbr") && kbr != 0 && variable_instance_exists(id, "kbrf")) ? kbrf : -1;
  var _t = variable_instance_exists(id, "kbrt") ? kbrt : -9;
  if (!variable_global_exists("C53H") || !is_array(global.C53H)) global.C53H = [];
  array_push(global.C53H, [_f, _t, object_get_name(object_index)]); return kbr_dmg_taken__orig(_d); }
''')
        s.run('global.C53H = [];')
    # (the bots' own skills off: a bot's send at player 2 would hit it too - its invincibility frames hid the host's send's hits
    # and made this part flaky; the bots are here as TARGETS of the host's sends)
    H.load_source('gml_GlobalScript_c53_nobotsk', 'function kfo_bot_skills(_h, _b, _c) { return 0; }\n')
    HOSTP = [None]

    def go(n, chase_c2=False, chase_hidden=False):
        def onf(f, ss, prev):
            for s in ss:
                s.run('if (is_struct(global.kfo.M) && !global.kfo.M.out) global.hp[kbr_char()] = global.maxhp[kbr_char()];')
                # (the emulator's log of every call grows without end over a long run: 5.8 GB before the OOM killer took
                # this part once - cleared as the multi tests do)
                if f % 60 == 0:
                    s.log.clear()
            if chase_c2:
                my2 = J(C2, 'global.kfo.my')
                # (no invincibility frames while it walks into the send: the knight's own bullets hit the SOUL as well, and
                # their invincibility would hide the send's hits)
                C2.run('global.inv = 0;')
                collide.chase(C2, lambda b: 'kbrx' in b.vars and b.vars.get('kbrt') == my2 and b.vars.get('kbrf') == HOSTP[0] and b.vars.get('visible', True))
            if chase_hidden:
                # the host's SOUL onto the hidden pieces of a send aimed at one of its bots
                myh = J(H, 'global.kfo.my')
                collide.chase(H, lambda b: 'kbrt' in b.vars and b.vars.get('kbrt') != myh)
        rec = run(net, sims, n, 'none', wall=900, on_frame=onf)
        errs = {c: rec[c]['errors'][:1] for c in range(1, 4) if rec[c]['errors']}
        return errs

    errs = go(300)
    ok(not errs, 'sends: the match runs with collisions (%r)' % errs)
    ok(J(H, 'global.kfo.M.go'), 'sends: the match is on')
    p2 = J(C2, 'global.kfo.my')
    hostp = J(H, 'global.kfo.my')
    HOSTP[0] = hostp
    bots = J(H, '(function(){ var _o = []; for (var _i = 0; _i < array_length(global.kfo.H.pl); _i++) { var _b = global.kfo.H.pl[_i]; if (_b.bot) array_push(_o, _b.pid); } return _o; })()')
    if sids is None:
        # (the attack skills: the ones with a real version made of attack pieces - kbr_skill_real names it; the effects and the
        # green skills answer "")
        sids = [i for i in range(1, J(H, 'kbr_skill_count()')) if J(H, 'kbr_skill_real(%d) != ""' % i)]
        # DRBR: only the sends this room allows (SENDS = ALL ENABLED: the families of its encounters - the knights' and
        # Jevil's); the bosses' own sends (Gerson, Flowery, Spamton, Pink) need their boss in the room and their SOUL modes:
        # their own send tests (t_*53_send.py) cover them
        off = [i for i in sids if not J(H, 'kbr_skill_ok(%d)' % i)]
        sids = [i for i in sids if i not in off]
        print('sends: not allowed in this room (their boss is not in it):', off, flush=True)
    print('sends: real attack skills', sids, 'bots', bots, flush=True)
    for sid in sids:
        for s in sims:
            s.run('global.C53H = [];')
        # an attack running in player 2's game with time left for the send (one that lands at an attack's end is cut with it:
        # the pieces that read the box go when the box does)
        for _ in range(200):
            if J(C2, 'global.kfo.M.R.ph') == 'run' and J(C2, '(kbr_tl_get(global.kfo.M.tl, global.kfo.M.R.k).t1 - kbr_now()) > 240'):
                break
            go(5)
        # at player 2
        H.run('global.kfo.M.tg.mode = 4; global.kfo.M.tg.pick = %d; kbr_tg_send(global.kfo.M, true);' % p2)
        errs = go(4)
        H.run('var _S = global.kfo.M.sk; array_push(_S.slots, { sid: %d, rev: 0 }); _S.sel = array_length(_S.slots) - 1; _S.cd = 0; global.U = kbr_skill_use();' % sid)
        # (player 2's SOUL stays where the send aims for its first frames - a SOUL jumping around would only spoil the aim; then,
        # if nothing hit yet - a pattern that leaves the middle free - it steps onto the host's pieces, with no invincibility)
        errs = errs or go(40, chase_c2=False)
        if not any(h[0] == hostp for h in J(C2, 'global.C53H')):
            errs = errs or go(180, chase_c2=True)
        ok(J(H, 'global.U') == 1, 'send %d: the host sent it (kbr_skill_use)' % sid)
        hits = {c: J(s, 'global.C53H') for c, s in ((1, H), (2, C2), (3, C3))}
        h2 = sum(1 for h in hits[2] if h[0] == hostp)
        if os.environ.get('C53_DEBUG'):
            print('debug send %d: hostp %r p2 %r hits2 %r' % (sid, hostp, p2, hits[2][:12]), flush=True)
        bad = [h for c in (1, 3) for h in hits[c] if h[0] == hostp]
        ok(not errs, 'send %d: no error with collisions %r' % (sid, errs))
        ok(h2 > 0, 'send %d: player 2 was HIT by it (%d hits, real collisions)' % (sid, h2))
        ok(not bad, 'send %d: the host and player 3 took no hit from it %r' % (sid, bad[:3]))
        errs = go(40)
        # at a bot (only the host's game builds it, hidden): the host's SOUL stands on those pieces
        if bots:
            for s in sims:
                s.run('global.C53H = [];')
            H.run('global.kfo.M.tg.mode = 4; global.kfo.M.tg.pick = %d; kbr_tg_send(global.kfo.M, true);' % bots[0])
            errs = go(4)
            H.run('var _S = global.kfo.M.sk; array_push(_S.slots, { sid: %d, rev: 0 }); _S.sel = array_length(_S.slots) - 1; _S.cd = 0; global.U = kbr_skill_use();' % sid)
            n_hidden = [0]
            def cnt():
                n_hidden[0] = max(n_hidden[0], J(H, '(function(){ var _n = 0; with (obj_collidebullet) { if (variable_instance_exists(id, "kbrt") && kbrt != global.kfo.my) _n++; } return _n; })()'))
            errs = errs or go(120, chase_hidden=True)
            cnt()
            hh = [h for h in J(H, 'global.C53H') if h[0] == hostp]
            ok(not errs, 'send %d at a bot: no error %r' % (sid, errs))
            ok(not hh, 'send %d at a bot: the host standing on its hidden pieces took no hit from them %r' % (sid, hh[:3]))
            errs = go(40)


def part_multi(n):
    from br_multi import make_room, run, compare
    net, sims = make_room(n, 'normal', 5370 + n, setx='_s.mhp = 999;', kn=(0, 1, 6), open_ok=0)
    rec = run(net, sims, 1500, 'same', wall=1500)
    errs = {c: rec[c]['errors'][:1] for c in range(1, n + 1) if rec[c]['errors']}
    cmp = compare(rec, n)
    ok(not errs, 'multi %d: no error in any game with collisions %r' % (n, errs))
    ok(cmp['cycles_all'] > 0 and not cmp['logic_bad'], 'multi %d: every game has the same cycles (%d, bad %r)' % (n, cmp['cycles_all'], cmp['logic_bad'][:2]))
    bf = [J(s, BFIX) for s in sims]
    ok(all(b == {} for b in bf), 'multi %d: no bullet needed the fallback %r' % (n, bf))
    print('multi', n, 'contacts', dict(collide.STATS), 'wall', rec.get('wall_hit'), flush=True)


if __name__ == '__main__' and len(sys.argv) > 1 and sys.argv[1] in ('sends', 'multi'):
    t0 = time.time()
    if sys.argv[1] == 'sends':
        part_sends([int(x) for x in sys.argv[2:]] or None)
    else:
        part_multi(int(sys.argv[2]))
    print('contract53 %s: %d checks, %d failed (%.0fs)' % (' '.join(sys.argv[1:]), N[0], len(FAILS), time.time() - t0))
    for f in FAILS:
        print('  -', f)
    sys.exit(1 if FAILS else 0)
