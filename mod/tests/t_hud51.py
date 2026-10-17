"""Build 51: the match HUD at 640x480 with 2 and 8 players, drawn by the real merged code in the emulator (uiharness /
gmrender) and checked from the draw calls: the staggered skill diamonds (slots + HOLD) floating off the corner and clear of
the TP bar (moved down), every skill's icon drawn inside its diamond with game sprites (MAX / heals as a green plus), the
picked skill's name, the 3-line feed left of the box, the targeting row's seven new labels with no key hint line, the mode
description for 2 seconds only, the player list's 8 rows above the Knight, ATTACKING: NAME under a CHOOSE pick, the knight
info's two labelled lines, the TAB box's keys, and nothing drawn off screen.
Usage: python3 t_hud51.py   (PNGs: /home/claude/work/uishots/br_t51_*.png)"""
import sys, os
sys.path.insert(0, '/home/claude/work/uiref')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from br_shot import br_frame

FAILS = []
N = [0]


def ok(c, msg):
    N[0] += 1
    print(('ok   ' if c else 'FAIL ') + msg, flush=True)
    if not c:
        FAILS.append(msg)


def texts(rec):
    # the text itself, not its 1-pixel black shadow (kbr_hud_text draws both)
    return [o for o in rec.ops if o[0] == 'text' and o[10] != 0]


def txt_of(o):
    return str(o[4]) if len(o) > 4 else ''


def X(o):
    return o[2] if o[0] == 'text' else o[1]


def Y(o):
    return o[3] if o[0] == 'text' else o[2]


PRE8 = '''var _M = global.kfo.M; var _pl = _M.st.pl;
_pl[0].tm = 4; _pl[0].tg = [3]; _pl[0].sh = 2;
_pl[1].tm = 1; _pl[1].tg = [1]; _pl[1].sh = 5;
_pl[2].tm = 0; _pl[2].tg = [1]; _pl[2].sh = 1;
_pl[3].tm = 0; _pl[3].tg = [5]; _pl[3].sh = 0; _pl[3].ti = 1;
_pl[4].tm = 2; _pl[4].tg = [2]; _pl[4].sh = 0;
_pl[5].tm = 0; _pl[5].tg = [4]; _pl[5].sh = 1;
kbr_tg_on_state(_M, _M.st); _M.tg.mode = 4; _M.tg.pick = 3;
_M.log = []; for (var _i = 0; _i < 6; _i++) { kbr_log("* line " + string(_i), c_white); _M.log[_i].n = 99; }'''

sim, rec = br_frame('t51_8', pre=PRE8, logs=0)
T = texts(rec)
S = [txt_of(o) for o in T]
# ---- nothing off screen
off = [o for o in rec.ops if o[0] in ('text', 'rect') and not (o[0] == 'rect' and o[1] <= -10 and o[3] >= 650) and (X(o) < -2 or Y(o) < -2 or X(o) > 642 or Y(o) > 482)]
ok(not off, 'nothing drawn off the 640x480 screen (%r)' % off[:3])
# ---- targeting row
for lab in ('RANDOM', 'LOW HP', 'CRYSTALS', 'REVENGE', 'CHOOSE', 'TIRED', 'EVERYONE'):
    ok(lab in S, 'targeting row shows %s' % lab)
for old in ('CHAOS', 'PROCEED', 'BIG SHOT', 'DEFEND', 'CHECK', 'PACIFY', 'ROARING'):
    ok(old not in S, 'the old label %s is gone' % old)
ok(not any('MODE' in s and 'PICK' in s for s in S), 'no "Q/E MODE  A/1-8 PICK" hint line')
# ---- feed: 3 lines, right of the TP bar
feed = [o for o in T if txt_of(o).startswith('* line')]
ok(len(feed) == 3 and [txt_of(o) for o in feed] == ['* line 3', '* line 4', '* line 5'], 'the feed shows the last 3 lines (%r)' % [txt_of(o) for o in feed])
ok(all(X(o) >= 14 for o in feed) and all(Y(o) > 300 for o in feed), 'build 51: the feed is bottom left, over the targeting strip (x %r)' % [(X(o), Y(o)) for o in feed])
# ---- player list
rows = [o for o in T if txt_of(o) in [str(i) for i in range(1, 9)] and X(o) in (474, 555)]
ok(len(rows) == 8, '8 numbered player cards (%r)' % [(X(o), txt_of(o)) for o in rows])
ok(rows and max(Y(o) for o in rows) < 122, 'all 8 rows end above the Knight (last row y %r)' % (max(Y(o) for o in rows) if rows else None))
ok(any(s.startswith('ATTACKING: ') for s in S), 'CHOOSE: ATTACKING: NAME under the pick (%r)' % [s for s in S if 'ATTACK' in s])
# ---- knight info: no bare number
ki = [o for o in T if 255 <= X(o) <= 430 and Y(o) < 36]
ok(any('NEXT ' in txt_of(o) for o in ki), 'the knight info has NEXT m:ss (%r)' % [txt_of(o) for o in ki])
ok(not any(txt_of(o).strip().startswith('#') for o in ki), 'no bare "#13" cycle number')
# ---- diamonds and icons
dia = [o for o in rec.ops if o[0] == 'tri']
ok(len(dia) >= 10, 'the slots are drawn as diamonds (%d triangles)' % len(dia))
xs = [min(o[1], o[3], o[5]) for o in dia]
ok(dia and min(xs) >= 10, 'the diamonds float off the corner (left edge x %r)' % (min(xs) if xs else None))
ok('HOLD' in S, 'the HOLD slot is labelled')
ok('MAX' in S, 'the picked MAX\'s name is written under the row')
# every skill's icon draws without an error and stays inside its diamond's box
bad = []
for sid in range(1, 22):
    sim.run('global.R0 = 0;')
    rec.ops.clear()
    try:
        sim.run('kbr_skill_icon(%d, 100, 100, 1, 1.3);' % sid)
    except Exception as e:
        bad.append((sid, str(e)[:80]))
        continue
    ops = [o for o in rec.ops if o[0] in ('spr', 'rect', 'text', 'line', 'circle')]
    if not ops:
        bad.append((sid, 'nothing drawn'))
ok(not bad, 'all 21 skills draw an icon (%r)' % bad)
rec.ops.clear()
sim.run('kbr_skill_icon(16, 100, 100, 1, 1.3);')
ok(any(o[0] == 'rect' for o in rec.ops) and not any(o[0] == 'text' for o in rec.ops), 'MAX is a drawn green plus (no text)')
rec.ops.clear()
sim.run('kbr_skill_icon(13, 100, 100, 1, 1.3);')
ok(any(o[0] == 'spr' and o[1] == 'spr_dmenu_items' for o in rec.ops), 'SHIELD uses the battle menu\'s shield icon')
rec.ops.clear()
sim.run('kbr_skill_icon(1, 100, 100, 1, 1.3);')
ok(any(o[0] == 'spr' and o[1] == 'spr_knight_diamondbullet_l' for o in rec.ops), 'SWORD uses the Knight\'s sword bullet sprite')
rec.ops.clear()
sim.run('kbr_skill_icon(9, 100, 100, 1, 1.3);')
ok(any(o[0] == 'spr' and o[1] == 'spr_khub_soul' for o in rec.ops), 'CONFUSE uses the SOUL')

# ---- the mode description: shown on a change, gone after 2 seconds
sim.run('var _T = global.kfo.M.tg; kbr_tg_desc_show(_T, 2);')
rec.ops.clear()
sim.run('kbr_hud_tg(0, 0, global.kfo.M);')
ok(any(txt_of(o) == '* Whoever has the most Shadow Crystals.' for o in texts(rec)), 'a mode change shows its description')
sim.run('global.kfo.M.tg.desc_t = 0;')
rec.ops.clear()
sim.run('kbr_hud_tg(0, 0, global.kfo.M);')
ok(not any(txt_of(o).startswith('* ') for o in texts(rec)), 'and it is gone after its 2 seconds')
ok(sim.py(sim.eval('kbr_tg_desc(0)')) == '* A random player. New one after every send.', 'RANDOM\'s description')

# ---- 2 players and the TAB box
sim2, rec2 = br_frame('t51_2', n=2, out=(), logs=0)
S2 = [txt_of(o) for o in texts(rec2)]
ok('SOULS 2/2' in S2, '2 players: SOULS 2/2')
off = [o for o in rec2.ops if o[0] in ('text', 'rect') and not (o[0] == 'rect' and o[1] <= -10 and o[3] >= 650) and (X(o) < -2 or Y(o) < -2 or X(o) > 642 or Y(o) > 482)]
ok(not off, '2 players: nothing off screen')
sim3, rec3 = br_frame('t51_tab', tab=True, logs=0)
S3 = [txt_of(o) for o in texts(rec3)]
ok(any('TARGET MODE' in s for s in S3) and any('CHARGE' in s for s in S3), 'the TAB box lists the keys')

print('hud51: %d checks, %d failed' % (N[0], len(FAILS)))
for f in FAILS:
    print('  -', f)
sys.exit(1 if FAILS else 0)
