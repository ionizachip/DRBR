"""DRBR: SPAMTON NEO's sendable skills (ids 45-50) in a room of three games (br_multi: the real code in every game, the simulated
network, SOUL / bullet collisions on: collide.py). The host sends each one at player 2 (TARGETING: CHECK on player 2), whose
SOUL walks into the send's pieces (a careless player). Checked for each:
  - player 2's game builds it from Spamton NEO's real Chapter 2 pieces (obj_sn_*): a send group of that skill that made instances,
    every bullet of it marked as the host's send aimed at player 2;
  - player 2 is hit by it (its own hits, through kbr_dmg_taken as every send's); the host and player 3 build none of it and take
    no hit from it;
  - when it is over nothing of it is left in player 2's game and the SOUL is as before; MAIL WALL: a SOUL that stays where it was when the walls came takes no hit from a wall (its row is the gap);
  - no error and no frame re-run in any game.
Usage: python3 t_spamton53_send.py [sid ...]"""
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


NAMES = {45: 'Pipis', 46: 'Flying Heads', 47: 'Heart Attack', 48: 'Kromer Rain', 49: 'Mail Wall', 50: 'BIG SHOT'}
want = [int(a) for a in sys.argv[1:]] or sorted(NAMES)
t0 = time.time()
net, sims = make_room(3, 'lan', 5350, setx='_s.mhp = 999; _s.skfam = 3; _s.cdm = 10; _s.dmul = 25; _s.ifr = 25;', kn=(0, 9), open_ok=0)
H, C2, C3 = sims
src = t_view47.func_src('kbr_dmg_taken').replace('function kbr_dmg_taken(', 'function kbr_dmg_taken__orig(', 1)
for s in sims:
    s.load_source('gml_GlobalScript_snsend_wrap', src + '''
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
LEFTS = ('(function(){ var _n = 0; var _l = ["obj_sn_pipegg","obj_sn_pipcone","obj_sn_pipfx","obj_sn_pippiece","obj_sn_lilguy","obj_sn_lilbullet","obj_sn_wireheart",'
         '"obj_sn_heartlaser","obj_sn_laser","obj_sn_heatbullet","obj_sn_dollar","obj_sn_wallctrl","obj_sn_wallcell","obj_sn_wallbomb","obj_sn_bombhit","obj_sn_biglaser",'
         '"obj_sn_laserfhb","obj_sn_armtel","obj_sn_cannonshot","obj_sn_dissolve","obj_sn_bullet","obj_sn_spreadshot","obj_sn_yshotanim"]; for (var _i = 0; _i < array_length(_l); _i++) { with (asset_get_index(_l[_i])) '
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
    H.run('var _S = global.kfo.M.sk; array_push(_S.slots, { sid: %d, rev: 0 }); _S.sel = array_length(_S.slots) - 1; _S.cd = 0; global.U = kbr_skill_use();' % sid)
    made2 = 0
    STILL = [0]
    still_hits = None
    seen2 = set()
    tagged_ok = True
    green = 0
    box_ok = [True, None, None, None, None]
    gx = None
    soul0 = None
    t_end = None

    def chase():
        # player 2 walks into the send's own pieces; no invincibility frames, so a one-frame strike counts whenever it lands
        # (MAIL WALL: player 2 stands still while the first wall passes - its row is the gap - and walks into the second's cells;
        # PIPIS: it stands still while the eggs come in and hatch)
        C2.run('global.inv = 0;')
        # (counted in frames: this runs once a frame)
        if (sid == 49 and STILL[0] < 60) or (sid == 45 and STILL[0] < 72):
            STILL[0] += 1
            if sid == 45:
                # out of the eggs' way while they come in (they come down over the box's right edge): the box's bottom left
                C2.run('if (instance_exists(obj_heart) && instance_exists(obj_growtangle)) { obj_heart.x = obj_growtangle.x - (abs(obj_growtangle.sprite_width) / 2) + 6; obj_heart.y = obj_growtangle.y + (abs(obj_growtangle.sprite_height) / 2) - 26; }')
            return
        collide.chase(C2, lambda b: b.vars.get('kbrx', 0) and b.vars.get('kbr', 0))
    for f in range(0, 480, 4):
        go(4, chase)
        keep_hp()
        if sid == 49 and still_hits is None and STILL[0] >= 60:
            still_hits = [h for h in J(C2, 'global.JVH') if h[1] == sid and h[0] == hostp and h[2] in ('obj_sn_wallcell', 'obj_sn_wallbomb', 'obj_sn_bombhit')]
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
    soul = J(C2, 'instance_exists(obj_heart) ? [obj_heart.color, sprite_get_name(obj_heart.sprite_index), kbr_sn_yellow_on()] : []')
    other = [J(s, '(function(){ var _n = 0; for (var _i = 0; _i < array_length(global.kbr_sa); _i++) { var _G = global.kbr_sa[_i]; if (_G.sid == %d && !_G.watch && !_G.twin) _n++; } return _n; })()' % sid) for s in (H, C3)]
    hits = {c: J(s, 'global.JVH') for c, s in ((1, H), (2, C2), (3, C3))}
    mine2 = [h for h in hits[2] if h[1] == sid and h[0] == hostp]
    from_host = {c: sum(1 for h in hits[c] if h[0] == hostp) for c in hits}
    ok(J(H, 'global.U') == 1, '%s: the host sent it' % NAMES[sid])
    ok(made2 > 0 and any(n.startswith('obj_sn_') for n in seen2), "%s: player 2's game built it from Spamton NEO's pieces (%d made: %s)" % (NAMES[sid], made2, sorted(seen2)))
    ok(tagged_ok, "%s: every bullet of it in player 2's game is the host's send aimed at player 2" % NAMES[sid])
    ok(len(mine2) > 0, "%s: player 2 was hit by it (%d hits: %s)" % (NAMES[sid], len(mine2), sorted(set(h[2] for h in mine2))))
    if sid == 45:
        ok('obj_sn_pipcone' in seen2, "%s: its eggs hatched into heads (%s)" % (NAMES[sid], sorted(seen2)))
    ok(other == [0, 0] and from_host[1] == 0 and from_host[3] == 0, '%s: the host and player 3 build none of it and take no hit from it (groups %r, hits %r)' % (NAMES[sid], other, [from_host[1], from_host[3]]))
    ok(t_end is not None and left == 0, "%s: it ended (after ~%s frames) and nothing of it is left in player 2's game (%s)" % (NAMES[sid], t_end, left))
    if sid == 49:
        ok(still_hits == [], '%s: a SOUL that stays on its row (the gap) is never hit by a wall %r' % (NAMES[sid], still_hits))
    ok(soul and soul[0] == 0 and (soul[1] == 'spr_dodgeheart' or soul[2]), "%s: player 2's SOUL is as before (red, or yellow in his own attack) %r" % (NAMES[sid], soul))

    for c, s in ((1, H), (2, C2), (3, C3)):
        rl = getattr(s, 'retrylog', [])
        if rl:
            ok(False, '%s: game %d ran every frame once %r' % (NAMES[sid], c, rl[:2]))
    go(30)
print('spamton53 send: %d checks, %d failed (%.0fs)' % (N[0], len(FAILS), time.time() - t0))
for f in FAILS:
    print('  -', f)
sys.exit(1 if FAILS else 0)
