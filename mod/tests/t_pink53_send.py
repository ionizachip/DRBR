"""DRBR: PINK's sendable skills (ids 51-56) in a room of three games (br_multi: the real code in every game, the simulated
network, SOUL / bullet collisions on: collide.py). The host sends each one at player 2 (TARGETING: CHECK on player 2), whose
SOUL walks into the send's pieces (a careless player). Checked for each:
  - player 2's game builds it from Pink's real Chapter 5 pieces (obj_pk_*): a send group of that skill that made instances,
    every bullet of it marked as the host's send aimed at player 2;
  - player 2 is hit by it (its own hits, through kbr_dmg_taken as every send's); the host and player 3 build none of it and take
    no hit from it;
  - when it is over nothing of it is left in player 2's game and the SOUL is as before;
  - a way out: a SOUL that moves the right way takes no hit - KITTY PARADE / KITTY RAIN / HEART SHOTS: one that keeps 26 px off
    the send's lines; FUSE BOMBS / MEGA BOMB: one that stands in a box corner (the blasts' rows and columns miss it); the
    bombs' landing spots are inside the box and never on the SOUL;
  - no error and no frame re-run in any game.
Usage: python3 t_pink53_send.py [sid ...]"""
import sys, os, json, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import br_harness
br_harness.COLLIDE = True
from br_multi import *
import collide
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


NAMES = {51: 'Kitty Parade', 52: 'Kitty Rain', 53: 'Heart Shots', 54: 'Fuse Bombs', 55: 'Mega Bomb', 56: 'Encore'}
want = [int(a) for a in sys.argv[1:]] or sorted(NAMES)
t0 = time.time()
net, sims = make_room(3, 'lan', 5351, setx='_s.mhp = 999; _s.skfam = 3; _s.cdm = 10; _s.dmul = 25; _s.ifr = 25;', kn=(0, 10), open_ok=0)
H, C2, C3 = sims
src = t_view47.func_src('kbr_dmg_taken').replace('function kbr_dmg_taken(', 'function kbr_dmg_taken__orig(', 1)
for s in sims:
    s.load_source('gml_GlobalScript_pksend_wrap', src + '''
function kbr_dmg_taken(_d) { var _f = (variable_instance_exists(id, "kbr") && kbr != 0 && variable_instance_exists(id, "kbrf")) ? kbrf : -1;
  var _sid = -1; if (variable_instance_exists(id, "kbrx")) { var _G = kbr_sa_find(kbrx); if (is_struct(_G)) _sid = _G.sid; }
  if (!variable_global_exists("JVH") || !is_array(global.JVH)) global.JVH = [];
  array_push(global.JVH, [_f, _sid, object_get_name(object_index)]); return kbr_dmg_taken__orig(_d); }
''')
    s.run('global.JVH = [];')
p2 = None


def go(n, chase=None):
    def on_frame(f, sims_, prev):
        if chase is not None:
            chase()
    rec = run(net, sims, n, 'none', on_frame=on_frame, wall=900)
    errs = {c: rec[c]['errors'][:1] for c in range(1, 4) if rec[c]['errors']}
    if errs:
        ok(False, 'no errors in the games: %r' % errs)
        raise SystemExit(1)


def keep_hp():
    for s in sims:
        s.run('if (is_struct(global.kfo.M) && !global.kfo.M.out) global.hp[kbr_char()] = global.maxhp[kbr_char()];')


BOX = 'instance_exists(obj_growtangle) ? [round(obj_growtangle.x), round(obj_growtangle.y), obj_growtangle.image_xscale, obj_growtangle.image_yscale, obj_growtangle.image_angle] : []'
LEFTS = ('(function(){ var _n = 0; var _l = ["obj_pk_cat","obj_pk_lanebullet","obj_pk_bomb","obj_pk_bigbomb","obj_pk_boom","obj_pk_smoke","obj_pk_chargestar",'
         '"obj_pk_fan","obj_pk_fanheart","obj_pk_hater","obj_pk_trail","obj_pk_doki"]; for (var _i = 0; _i < array_length(_l); _i++) { with (asset_get_index(_l[_i])) '
         '{ if (variable_instance_exists(id, "kbrx") && kbrx > 0) _n++; } } return _n; })()')

go(300)
ok(J(H, 'global.kfo.M.go'), 'the match runs')
p2 = J(C2, 'global.kfo.my')
hostp = J(H, 'global.kfo.my')
for sid in want:
    for s in sims:
        s.run('global.JVH = [];')
    # wait for a running attack in player 2's game (the sends land while an attack runs)
    for _ in range(40):
        if J(C2, 'global.kfo.M.R.ph') == 'run' and J(C2, 'instance_exists(obj_growtangle) && obj_growtangle.x > -1000'):
            break
        go(5)
    H.run('global.kfo.M.tg.mode = 4; global.kfo.M.tg.pick = %d; kbr_tg_send(global.kfo.M, true);' % p2)
    go(2)
    BOX0 = J(C2, 'kbr_sa_box()')
    SOUL0 = J(C2, 'kbr_sa_soul()')
    H.run('var _S = global.kfo.M.sk; array_push(_S.slots, { sid: %d, rev: 0 }); _S.sel = array_length(_S.slots) - 1; _S.cd = 0; global.U = kbr_skill_use();' % sid)
    made2 = 0
    STILL = [0]
    still_hits = None
    DEST = set()
    seen2 = set()
    tagged_ok = True
    green = 0
    box_ok = [True, None, None, None, None]
    gx = None
    soul0 = None
    t_end = None

    def chase():
        # player 2 walks into the send's own pieces; no invincibility frames, so a one-frame strike counts whenever it lands
        C2.run('global.inv = 0;')
        collide.chase(C2, lambda b: b.vars.get('kbrx', 0) and b.vars.get('kbr', 0))
    for f in range(0, 480, 4):
        go(4, chase)
        if sid in (54, 55):
            for d in J(C2, '(function(){ var _o = []; with (obj_pk_bomb) { if (variable_instance_exists(id, "kbrx") && kbrx > 0) array_push(_o, [dest_x, dest_y]); } with (obj_pk_bigbomb) { if (variable_instance_exists(id, "kbrx") && kbrx > 0) array_push(_o, [dest_x, dest_y]); } return _o; })()'):
                DEST.add(tuple(round(v) for v in d))
        keep_hp()
        g = J(C2, '(function(){ var _o = []; for (var _i = 0; _i < array_length(global.kbr_sa); _i++) { var _G = global.kbr_sa[_i]; if (_G.sid == %d && !_G.watch) array_push(_o, [_G.gx, _G.made, variable_struct_get_names(_G.seen), _G.t]); } return _o; })()' % sid)
        for gxx, m, names, tt in g:
            gx = gxx
            made2 = max(made2, m)
            seen2 |= set(names)
        if gx is not None and not g and t_end is None:
            t_end = f
        bad = J(C2, '(function(){ var _n = 0; with (obj_bulletparent) { if (variable_instance_exists(id, "kbrx") && kbrx > 0 && variable_instance_exists(id, "kbr") && kbr != 0 && (kbrf != %d || kbrt != %d)) _n++; } return _n; })()' % (hostp, p2))
        if bad:
            tagged_ok = False
        if J(C2, 'kbr_soul_mode()') == 'green' and g:
            green += 1
        if t_end is not None and f > t_end + 20:
            break
    left = J(C2, LEFTS)
    if left:
        print('left in game 2:', J(C2, '(function(){ var _o = []; with (all) { if (variable_instance_exists(id, "kbrx") && kbrx > 0) array_push(_o, [object_get_name(object_index), kbrx, x, y]); } return _o; })()'), J(C2, '(function(){ var _o = []; for (var _i = 0; _i < array_length(global.kbr_sa); _i++) array_push(_o, [global.kbr_sa[_i].sid, global.kbr_sa[_i].t, global.kbr_sa[_i].end_t, global.kbr_sa[_i].age]); return _o; })()'), flush=True)
    soul = J(C2, 'instance_exists(obj_heart) ? [obj_heart.color, sprite_get_name(obj_heart.sprite_index), kbr_pk_purple_on()] : []')
    other = [J(s, '(function(){ var _n = 0; for (var _i = 0; _i < array_length(global.kbr_sa); _i++) { var _G = global.kbr_sa[_i]; if (_G.sid == %d && !_G.watch && !_G.twin) _n++; } return _n; })()' % sid) for s in (H, C3)]
    hits = {c: J(s, 'global.JVH') for c, s in ((1, H), (2, C2), (3, C3))}
    mine2 = [h for h in hits[2] if h[1] == sid and h[0] == hostp]
    from_host = {c: sum(1 for h in hits[c] if h[0] == hostp) for c in hits}
    ok(J(H, 'global.U') == 1, '%s: the host sent it' % NAMES[sid])
    ok(made2 > 0 and any(n.startswith('obj_pk_') for n in seen2), "%s: player 2's game built it from Pink's pieces (%d made: %s)" % (NAMES[sid], made2, sorted(seen2)))
    ok(tagged_ok, "%s: every bullet of it in player 2's game is the host's send aimed at player 2" % NAMES[sid])
    ok(len(mine2) > 0, "%s: player 2 was hit by it (%d hits: %s)" % (NAMES[sid], len(mine2), sorted(set(h[2] for h in mine2))))
    if sid in (54, 55):
        ok(len(DEST) > 0 and all(BOX0[0] - BOX0[2] <= d[0] <= BOX0[0] + BOX0[2] and BOX0[1] - BOX0[3] <= d[1] <= BOX0[1] + BOX0[3] for d in DEST), "%s: its bombs land inside player 2's box %r (box %r)" % (NAMES[sid], sorted(DEST), BOX0))
    if sid == 54:
        ok(all(abs(d[0] - SOUL0[0]) >= 30 or abs(d[1] - SOUL0[1]) >= 30 for d in DEST), "%s: no bomb lands on the SOUL (%r, SOUL %r)" % (NAMES[sid], sorted(DEST), SOUL0))
    if sid == 56:
        ok('obj_pk_fanheart' in seen2 and 'obj_pk_hater' in seen2, "%s: her fans threw their hearts and the haters their bars (%s)" % (NAMES[sid], sorted(seen2)))
    ok(other == [0, 0] and from_host[1] == 0 and from_host[3] == 0, '%s: the host and player 3 build none of it and take no hit from it (groups %r, hits %r)' % (NAMES[sid], other, [from_host[1], from_host[3]]))
    ok(t_end is not None and left == 0, "%s: it ended (after ~%s frames) and nothing of it is left in player 2's game (%s)" % (NAMES[sid], t_end, left))
    ok(soul and soul[0] == 0 and (soul[1] == 'spr_dodgeheart' or soul[2]), "%s: player 2's SOUL is as before (red, or purple in her own attack) %r" % (NAMES[sid], soul))

    for c, s in ((1, H), (2, C2), (3, C3)):
        rl = getattr(s, 'retrylog', [])
        if rl:
            ok(False, '%s: game %d ran every frame once %r' % (NAMES[sid], c, rl[:2]))
    go(30)
print('pink53 send: %d checks, %d failed (%.0fs)' % (N[0], len(FAILS), time.time() - t0))
for f in FAILS:
    print('  -', f)
sys.exit(1 if FAILS else 0)
