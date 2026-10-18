"""DRBR 1.0.3 - your requests: being OUT "needs to be the game over thing and let us spectate after", and "whoever you're
spectating it needs to show their character and stuff". A practice room with three bots (LANCER, ROUXLS and BERDLY wear their
own skins: Susie, Ralsei, Berdly), the real code, drawn with the recorder:
  - OUT (a hit takes the last HP, and the game's own party-down check): no OUT box, no "Back to the room" - your SOUL breaks,
    the GAME OVER (Chapter 3's picture, "THE BATTLE GOES ON - YOU WILL WATCH THE REST"), then you watch: the camera follows a
    player;
  - watching someone, the battle is theirs to see:
      their character stands in your hero's place (the game's own battle pose for Susie / Ralsei, Berdly's look) and
        blinks when they are hit; your own hero is hidden;
      the HP panel is theirs: their head and character name, their HP and max HP, their colour, their SHIELD;
      the TP bar is their gauge;
      the watching card shows their skill slots as diamonds with the skills' pictures (the picked one framed) - and still
        their name and HP, the camera;
  - switching to someone else (RIGHT) switches all of it; playing (not OUT): your own hero, HP, gauge as always.
Usage: python3 t_watch103.py"""
import sys, os, json, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('KH_CAM', '2063,0')
import br_harness
br_harness.COLLIDE = True
from br_harness import *
sys.path.insert(0, '/home/claude/work/uiref')
from uiharness import Recorder

FAILS = []
N = [0]
CX, CY = br_harness.CAM


def ok(c, msg):
    N[0] += 1
    print(('ok   ' if c else 'FAIL ') + msg, flush=True)
    if not c:
        FAILS.append(msg)
    return c


def J(s, e):
    return s.py(s.eval(e))


INFO = '[global.kfo.M.out, global.krun.state, instance_number(obj_knight_prompt), global.hp[kbr_char()]]'


def recorder(sim):
    rec = Recorder(sim)
    sim.mock('camera_get_view_x', lambda s, *a: CX)
    sim.mock('camera_get_view_y', lambda s, *a: CY)
    return rec


def spr_names(rec):
    return [o[1] for o in rec.ops if o[0] == 'spr']


def texts(rec):
    return [str(o[4]) for o in rec.ops if o[0] == 'text']


# ---------------- 1. OUT by a hit: the GAME OVER, then watching (no OUT box)
sim, e = br_match(open_ok=0, kn=(0,), seed=7301, bots=3, setx='_s.mhp = 200; _s.skills = 1;')
ok(e is None, 'a practice room with 3 bots starts (%r)' % (e,))
# (the emulator knows an asset by a name the code uses: these are looked up by their names - asset_get_index - in the game)
for a_ in ('spr_ralseib_idle', 'spr_noelleb_idle', 'spr_krisb_idle', 'hpfont'):
    try:
        sim.define_asset(a_)
    except Exception:
        pass
sim.run('if (!variable_global_exists("hpfont")) global.hpfont = hpfont;')
bots = J(sim, '(function(){ var _o = []; for (var _i = 0; _i < array_length(global.kfo.H.pl); _i++) { var _b = global.kfo.H.pl[_i]; if (_b.bot) array_push(_o, [_b.pid, _b.n, _b.s]); } return _o; })()')
ok(len(bots) == 3, 'the bots and their skins %r' % bots)
for f in range(900):
    step(sim, 1)
    if sim.eval('global.kfo.M.R.ph') == 'run':
        break
for f in range(60):
    step(sim, 1)
# the bots' skill slots (as a bot that drew skills has them): every game's standings carry them
sim.run('var _qq = [[1, 13, 26, 45], [3, 11, 32, 51], [5, 14, 30, 47]]; var _k = 0; for (var _i = 0; _i < array_length(global.kfo.H.pl); _i++) { var _b = global.kfo.H.pl[_i]; if (_b.bot) { _b.q = _qq[_k]; _b.qs = 2; _b.qh = 16; _k++; } }')
# the playing view first: your own hero, your HP
look0 = J(sim, 'kbr_hero_look(global.kfo.M)')
hp0 = J(sim, '[kbr_cb_hp(kbr_char()), global.hp[kbr_char()], kbr_cb_mhp(kbr_char()), global.maxhp[kbr_char()]]')
ok(look0 == -1 and hp0[0] == hp0[1] and hp0[2] == hp0[3], 'playing: your own hero and HP (look %r, HP %r)' % (look0, hp0))
# a hit that takes the last HP
sim.run('global.hp[kbr_char()] = 1; global.inv = -1; with (obj_heart) { with (instance_create(x, y, obj_regularbullet)) { kbr_bullet_contract(1); damage = 30; target = 0; scr_damage(); instance_destroy(); } }')
st = J(sim, INFO)
ok(st[0] and st[1] == 'battle' and st[2] == 0, 'a hit at 1 HP: OUT, still in the battle, no OUT box (%r)' % st)
rec = recorder(sim)
saw_break = saw_go = saw_text = False
watch_at = None
for f in range(420):
    err = step(sim, 1)
    if err:
        ok(False, 'no error after OUT (%s)' % err[:200])
        break
    if f % 5 == 0:
        rec.ops.clear()
        sim.run('kbr_ko_draw(%d, %d, global.kfo.M);' % (CX, CY))
        nm = spr_names(rec)
        saw_go = saw_go or ('spr_gameoverbg_neo' in nm)
        saw_text = saw_text or any('WATCH THE REST' in t for t in texts(rec))
        saw_break = saw_break or any(o[0] in ('spr', 'rect', 'tri') for o in rec.ops) and not saw_go
    if watch_at is None and J(sim, 'kbr_spec_pid(global.kfo.M)') >= 0:
        watch_at = f
st = J(sim, INFO)
ok(saw_go and saw_text, 'then the GAME OVER (Chapter 3\'s picture: %r, "THE BATTLE GOES ON - YOU WILL WATCH THE REST": %r)' % (saw_go, saw_text))
ok(watch_at is not None and st[1] == 'battle' and st[2] == 0, 'then you watch a player (from frame %r after OUT), still no OUT box (%r)' % (watch_at, st))

# ---------------- 2. watching: their character, their HP panel, their TP, their skills
by_name = {b[1]: b for b in bots}


def watch(pid):
    sim.run('global.kfo.M.spect = %d; global.kfo.M.vw.cam = 0;' % pid)
    for f in range(8):
        step(sim, 1)


def check_view(b, own_skin_spr, head_spr, bname_spr):
    pid, name, skin = b
    p = J(sim, 'kbr_st_player(global.kfo.M, %d)' % pid)
    ok(J(sim, 'kbr_spec_pid(global.kfo.M)') == pid, 'watching %s' % name)
    ok(J(sim, 'kbr_hero_look(global.kfo.M)') == skin, '%s: their character (skin %d) stands in your hero\'s place (look %r)' % (name, skin, J(sim, 'kbr_hero_look(global.kfo.M)')))
    ok(J(sim, 'global.charinstance[0].image_alpha') == 0 and J(sim, 'instance_exists(obj_knight_skinart)'), '%s: your own hero hidden, the look drawn by its object' % name)
    rec.ops.clear()
    sim.run('with (obj_knight_skinart) kbr_skin_art_draw();')
    nm = spr_names(rec)
    ok(own_skin_spr in nm, '%s: drawn in their battle pose (%s): %r' % (name, own_skin_spr, nm[:3]))
    # the HP panel
    hp = J(sim, '[kbr_cb_hp(kbr_char()), kbr_cb_mhp(kbr_char())]')
    ok(hp == [max(0, round(p['hp'])), max(1, round(p['mh']))], '%s: the HP panel reads their HP %r (the standings: %r / %r; yours %r)' % (name, hp, p['hp'], p['mh'], J(sim, 'global.hp[kbr_char()]')))
    rec.ops.clear()
    sim.run('kbr_charbox(kbr_char(), 0, 2076, 400, 2114, 403);')
    nm = spr_names(rec)
    if head_spr:
        ok(head_spr in nm and bname_spr in nm, '%s: their head and name in the panel (%r)' % (name, nm[:4]))
    else:
        ok(len(nm) >= 1 and J(sim, 'global.kbr_cbx') == 1, '%s: their look\'s head and name in the panel (%r)' % (name, nm[:4]))
    sim.run('global.CC = c_white; with (obj_battlecontroller) { global.CC = kbr_charbox_col(kbr_char(), c_white); }')
    col = J(sim, 'global.CC')
    want = J(sim, 'kfo_skin_col(%d)' % skin) if skin >= 6 else None
    ok((want is None and col != 16777215) or col == want, '%s: the HP bar in their colour (%r)' % (name, col))
    # the TP bar: their gauge
    drawn = []
    sim.mock('kbr_tp_draw_g', lambda s, M, g, ch, S: (drawn.append((g, ch)), 1)[1])
    r = J(sim, 'kbr_tp_hook()')
    ok(r and drawn and drawn[0][0] == min(100, max(0, p['g'])) and drawn[0][1] == 0, '%s: the TP bar is their gauge (%r, the standings %r)' % (name, drawn[:1], p['g']))
    # the watching card: their skills as diamonds with the skills' pictures
    icons = []
    sim.mock('kbr_skill_icon', lambda s, sid, x, y, a, sc=1: (icons.append(int(sid)), 0)[1])
    tx = []
    sim.mock('kbr_hud_text', lambda s, x, y, t, c: (tx.append(str(t)), 0)[1])
    rec.ops.clear()
    sim.run('global.kfo.view.shud = 0; kbr_hud_spec(%d, %d, global.kfo.M);' % (0, 0))
    tri = sum(1 for o in rec.ops if o[0] == 'tri')
    q = [s for s in p['q'] if isinstance(s, (int, float)) and s > 0] + ([p['qh']] if p['qh'] > 0 else [])
    ok(tri >= 10 and sorted(icons) == sorted(int(s) for s in q), '%s: the card shows their 5 slots as diamonds (%d triangles) with their skills\' pictures %r (theirs %r)' % (name, tri, icons, q))
    want_hp = '%d/%d' % (round(p['hp']), round(p['mh']))
    ok(any(p['n'] in t for t in tx) and any(want_hp in t for t in tx) and any('CAMERA' in t for t in tx), '%s: and their name, %s, the camera (%r)' % (name, want_hp, tx[:4]))
    return p


# skins: LANCER wears Susie (2), ROUXLS Ralsei (3), BERDLY his own look (6)
for nm_, spr_, head_, bname_ in (('LANCER', 'spr_susieb_idle', 'spr_headsusie', 'spr_bnamesusie'), ('BERDLY', None, None, None), ('ROUXLS', 'spr_ralseib_idle', 'spr_headralsei', 'spr_bnameralsei')):
    b = by_name.get(nm_)
    if b is None:
        ok(False, 'bot %s in the room (%r)' % (nm_, bots))
        continue
    watch(b[0])
    if spr_ is None:
        spr_ = J(sim, 'sprite_get_name(kfo_skin_bt_spr(%d))' % b[2])
    check_view(b, spr_, head_, bname_)
# a hit on the one watched: their character blinks
b = by_name.get('LANCER')
watch(b[0])
sim.run('kbr_rv(global.kfo.M, %d).hit = 30;' % b[0])
rec.ops.clear()
sim.run('with (obj_knight_skinart) kbr_skin_art_draw();')
fl = [o for o in rec.ops if o[0] == 'spr' and isinstance(o[8], tuple) and o[8][1] == 255]
ok(len(fl) >= 1, 'LANCER hit: their character blinks red (%d)' % len(fl))
# their SHIELD on the panel
sim.run('for (var _i = 0; _i < array_length(global.kfo.H.pl); _i++) if (global.kfo.H.pl[_i].pid == %d) global.kfo.H.pl[_i].bt.shield = 2;' % b[0])
for f in range(20):
    step(sim, 1)
rec.ops.clear()
sim.run('kbr_shield_draw(2063, 400, kbr_char() - 1);')
blue = [o for o in rec.ops if o[0] == 'rect' and o[5] == J(sim, 'kbr_shield_col()')]
ok(len(blue) >= 1, 'their SHIELD on their HP bar (%d blue parts, sd %r)' % (len(blue), J(sim, 'kbr_st_player(global.kfo.M, %d).sd' % b[0])))
# RIGHT: the next one - all of it switches
before = J(sim, 'global.kfo.M.spect')
sim.kb = {'p_right'}
sim.mock('right_p', lambda s, *a: 1)
sim.run('kbr_spectate_tick();')
sim.mock('right_p', lambda s, *a: 0)
after = J(sim, 'global.kfo.M.spect')
look = J(sim, 'kbr_hero_look(global.kfo.M)')
p2 = J(sim, 'kbr_st_player(global.kfo.M, %d)' % after)
ok(after != before and look == p2['s'] and J(sim, 'kbr_cb_hp(kbr_char())') == max(0, round(p2['hp'])), 'RIGHT: watching the next one - their look %r and HP %r' % (look, J(sim, 'kbr_cb_hp(kbr_char())')))

# ---------------- 3. the party-down check in a running match: OUT, the GAME OVER, watching
s2, e2 = br_match(open_ok=0, kn=(0,), seed=7302, bots=2, setx='_s.mhp = 200;')
for f in range(900):
    step(s2, 1)
    if s2.eval('global.kfo.M.R.ph') == 'run':
        break
s2.run('global.hp[kbr_char()] = -5; scr_dead(0); scr_gameover();')
st = J(s2, INFO)
ok(st[0] and st[1] == 'battle' and st[2] == 0 and J(s2, 'is_struct(global.kfo.M.vw.ko)'), 'the game\'s own GAME OVER call in a running match (scr_gameover): OUT, the GAME OVER starts, no OUT box (%r)' % st)
w = None
for f in range(300):
    step(s2, 1)
    if J(s2, 'kbr_spec_pid(global.kfo.M)') >= 0:
        w = f
        break
ok(w is not None and J(s2, 'kbr_hero_look(global.kfo.M)') >= 1, 'then you watch (frame %r), their character in your hero\'s place' % w)

print('\n%d checks, %d failed' % (N[0], len(FAILS)))
for f in FAILS:
    print('  FAIL', f)
sys.exit(1 if FAILS else 0)
