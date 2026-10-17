"""Build 50: the SHIELD on the party's HP bar (scr_charbox, the merged game's own) and the TP bar as the skill meter, drawn with
the game's real fonts and sprites (uiharness / gmrender) - checked and rendered to PNGs (tests/logs49/hud50_*.png).

  - every party skin (Kris, Susie, Ralsei, Noelle) at full HP, low HP and HP + shield over max HP: the blue part sits after
    the coloured HP (or the bar is full with the blue on top), the blue +N is in the HP font, left of the HP numbers, never
    over the name or the numbers; nothing blue without a shield;
  - the TP bar: the 60 line (slanted like the bar's ends: from lower left to upper right), orange under it and gold above,
    the red preview while CHARGE is held (exactly the charge, from the top of the fill), white flashing and MAX at 100,
    the game's own TP sprites, YOU DREW A SKILL! beside it.
Usage: python3 t_hud50.py"""
import sys, re
sys.path.insert(0, '/home/claude/work/uiref')
sys.path.insert(0, '/home/claude/work/tests')
from uiharness import *
import gmrender as G

FAILS = []
N = [0]
OUT = '/home/claude/work/tests/logs49/'


def ok(c, msg):
    N[0] += 1
    print(('ok   ' if c else 'FAIL ') + msg, flush=True)
    if not c:
        FAILS.append(msg)


sim, rec = menu_sim()
for o in ('obj_tb', 'obj_rouxls_ch3_enemy', 'obj_tenna_board4_enemy', 'obj_battlecontroller', 'obj_tbar'):
    if o not in sim.objects:
        sim.define_object(o)
txt = open(M + 'gml_GlobalScript_scr_charbox.gml').read()
ok(txt.count('kbr_shield_draw(') >= 5, 'scr_charbox calls kbr_shield_draw after the HP bar in every knight\'s version (%d)' % txt.count('kbr_shield_draw('))
sim.load_source('gml_GlobalScript_scr_charbox', txt)
sim.mock('i_ex', lambda s, o: 0)
sim.mock('kbr_on', lambda s: 1)
sim.run('global.kbr_san = 1;')
sim.mock('snd_play', lambda s, *a: 0)
# surfaces: the ops drawn on a surface are moved to where the surface is drawn; the cutout (a subtract) is left out
SURF = {'stack': []}


def s_set(s, sf):
    rec.ops.append(('surf_begin',))
    return 1


def s_reset(s):
    rec.ops.append(('surf_end',))
    return 1


def s_draw(s, sf, x, y):
    rec.ops.append(('surf_draw', x, y))
    return 1


sim.mock('surface_set_target', s_set)
sim.mock('surface_reset_target', s_reset)
sim.mock('draw_surface', s_draw)
sim.mock('surface_exists', lambda s, sf: 1)
sim.mock('surface_create', lambda s, w, h: 1)
sim.mock('draw_clear_alpha', lambda s, c, a: 0)
sim.mock('stringsetloc', lambda s, t, k: t)
sim.mock('string_hash_to_newline', lambda s, t: t)


def flatten(ops):
    out = []
    i = 0
    while i < len(ops):
        o = ops[i]
        if o[0] == 'surf_begin':
            j = i + 1
            inner = []
            while j < len(ops) and ops[j][0] != 'surf_end':
                inner.append(ops[j])
                j += 1
            k = j + 1
            while k < len(ops) and ops[k][0] != 'surf_draw':
                k += 1
            dx, dy = (ops[k][1], ops[k][2]) if k < len(ops) else (0, 0)
            for q in inner:
                if q[0] == 'spr' and q[1] == 'spr_tensionbar_cutout':
                    continue
                if q[0] in ('rect', 'line'):
                    q = (q[0], q[1] + dx, q[2] + dy, q[3] + dx, q[4] + dy) + tuple(q[5:])
                elif q[0] == 'spr':
                    q = q[:3] + (q[3] + dx, q[4] + dy) + q[5:]
                out.append(q)
            out += [x for x in ops[j + 1:k] if x[0] not in ('surf_begin', 'surf_end')]
            i = k + 1
            continue
        if o[0] not in ('surf_end', 'surf_draw'):
            out.append(o)
        i += 1
    return out


SKIN = {1: 'Kris', 2: 'Susie', 3: 'Ralsei', 4: 'Noelle'}
BLUE = sim.eval('kbr_shield_col()')


def match(shield, hp, mh, char):
    sim.run('''global.TM = { me: true, out: false, eff: { dmul: 100, skills: 1, rcost: 0, scost: 100, skdmg: 100 },
        sk: { shield: %d, shield_t: 200, charging: false, charge: 0, need: -1, pop_t: 0, pop_n: 0 }, g: 0 };
        global.hp[%d] = %d; global.maxhp[%d] = %d;''' % (shield, char, hp, char, mh))
    sim.mock('kbr_match', lambda s: s.eval('global.TM'))
    sim.mock('kbr_char', lambda s, c=char: c)


def charbox(char):
    sim.run('''global.knight_variant = 0; global.char = [%d, 0, 0]; global.charturn = 9; global.myfight = 0; global.fighting = 0; global.bmenucoord = [array_create(12, 0), array_create(12, 0)]; global.monster = [0, 0, 0]; global.mercymod = [0, 0, 0]; global.monsterstatus = [0, 0, 0]; global.faceaction = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0];
    var o = instance_create_depth(0, 0, 0, obj_tb);
    with (o) { chartotal = 1; mmy = [0, 0, 0, 0]; charpos = [5, 6, 7, 8]; havechar = [1, 1, 1, 1]; hpcolor = [c_aqua, c_fuchsia, c_lime, c_yellow];
      rouxlsgridenabled = false; btc = array_create(40, 0); rouxlsbuttoncount_y = 0; xx = 0; yy = 0; bp = 0; bpoff = 0; b_offset = 336; }
    global.o = o;''' % char)
    for _ in range(80):
        try:
            rec.ops.clear()
            sim.run('with (global.o) { scr_charbox(); }')
            return flatten(rec.ops)
        except Exception as e:
            m = re.search(r'obj_tb\.(\w+) not set', str(e))
            if m:
                sim.run('global.o.%s = 0;' % m.group(1))
                continue
            u = re.search(r'undefined function (\w+)', str(e))
            if u:
                sim.mock(u.group(1), lambda s, *a: 0)
                continue
            v = re.search(r"variable '?(\w+)'? (?:not set|is not defined|undefined)", str(e))
            if v and v.group(1).startswith(('spr_', 'snd_')):
                sim.define_asset(v.group(1))
                continue
            g = re.search(r"global variable name '(\w+)'", str(e))
            if g:
                sim.run('global.%s = 0;' % g.group(1))
                continue
            raise
    raise RuntimeError('charbox')


def tbox(o):
    """a text op's box (real font metrics)"""
    _, fnt, x, y, t, xs, ys, a, sep, w, c, al, ha, va = o
    f = G.font(fnt)
    wd = f.line_width(str(t)) * xs
    x0 = x - wd / 2 if ha == 1 else (x - wd if ha == 2 else x)
    return (x0, y, x0 + wd, y + f.h * ys)


def render(ops, path):
    rec.ops[:] = ops
    rec.render(path)


for char in (1, 2, 3, 4):
    for name, hp, mh, sh in (('full', 160, 160, 3), ('low', 30, 160, 3), ('over', 150, 160, 3), ('none', 160, 160, 0), ('big', 999, 999, 2)):
        match(sh, hp, mh, char)
        ops = charbox(char)
        render(ops, OUT + 'hud50_charbox_%s_%s.png' % (SKIN[char], name))
        blue = [o for o in ops if o[0] == 'rect' and o[5] == BLUE]
        texts = [o for o in ops if o[0] == 'text']
        plus = [o for o in texts if str(o[4]).startswith('+')]
        tag = '%s %s (HP %d/%d, %d shield hits)' % (SKIN[char], name, hp, mh, sh)
        if sh == 0:
            ok(not blue and not plus, tag + ': nothing blue')
            continue
        shp = sim.eval('kbr_shield_hp(%d)' % sh)
        ok(len(plus) == 1 and plus[0][4] == '+%d' % shp and plus[0][1] == 'hpfont' and plus[0][10] == BLUE, tag + ': a blue +%d in the HP font %r' % (shp, [p[4] for p in plus]))
        maroon = [o for o in ops if o[0] == 'rect' and o[5] == sim.eval('c_maroon')]
        bx0 = maroon[0][1] if maroon else 128
        if hp + shp <= mh:
            a = math.ceil(hp / mh * 75)
            b = math.ceil((hp + shp) / mh * 75)
            ok(any(abs(o[1] - (bx0 + a)) <= 1 and abs(o[3] - (bx0 + b)) <= 1 for o in blue), tag + ': the blue runs from the HP (%d) to HP + shield (%d)' % (bx0 + a, bx0 + b))
        else:
            ok(any(abs(o[3] - (bx0 + 75)) <= 1 and o[1] > bx0 for o in blue), tag + ': over max: the bar is full, the blue on top (%r)' % [(o[1], o[3]) for o in blue])
        # +N: left of the HP numbers, right of the name, inside the box's top row
        hpnum = [o for o in texts if o[1] == 'hpfont' and str(o[4]) == str(hp)]
        pb = tbox(plus[0])
        hb = tbox(hpnum[0]) if hpnum else None
        names = [o for o in ops if o[0] == 'spr' and 'bname' in str(o[1])]
        nx1 = max([o[3] + (G.sprite(o[1]).w or 0) for o in names] or [105])
        ok(hb is not None and pb[2] <= hb[0] + 0.5, tag + ': +N ends before the HP numbers (%.0f <= %.0f)' % (pb[2], hb[0] if hb else -1))
        ok(pb[0] >= nx1 - 0.5, tag + ': +N starts after the name (%.0f >= %.0f)' % (pb[0], nx1))

# ---------- the TP bar ----------
sim.run('var o = instance_create_depth(40, 0, 0, obj_tbar); with (o) { healthbar_surf = 1; yoffset = 0; } global.tb = o;')


def tp(g, charging=False, charge=0, pop=0, kv=0):
    sim.run('global.knight_variant = %d;' % kv)
    sim.run('''global.TM = { me: true, out: false, eff: { dmul: 100, skills: 1, rcost: 0, scost: 100, skdmg: 100 },
        sk: { shield: 0, shield_t: 0, charging: %s, charge: %d, need: -1, pop_t: %d, pop_n: 1 }, g: %d };''' % ('true' if charging else 'false', charge, pop, g))
    sim.mock('kbr_match', lambda s: s.eval('global.TM'))
    rec.ops.clear()
    sim.run('with (global.tb) { kbr_tp_draw(global.TM); }')
    return flatten(rec.ops)


H = 196
for name, g, chg, c, pop in (('40', 40, False, 0, 0), ('60', 60, False, 0, 0), ('75_charging50', 75, True, 50, 0), ('85_charging70', 85, True, 70, 0),
                             ('100', 100, False, 0, 0), ('100_charging100', 100, True, 100, 0), ('drew', 30, False, 0, 40)):
    ops = tp(g, chg, c, pop)
    render(ops, OUT + 'hud50_tp_%s.png' % name)
    sprs = [o[1] for o in ops if o[0] == 'spr']
    ok('spr_tensionbar' in sprs and 'spr_tplogo' in sprs, 'TP %s: the game\'s own TP bar and logo (%r)' % (name, sorted(set(sprs))))
    lines = [o for o in ops if o[0] == 'line' and o[7] == 2]
    ok(len(lines) == 1 and lines[0][2] > lines[0][4] and lines[0][3] > lines[0][1], 'TP %s: the 60 line is slanted like the bar\'s "/" ends' % name)
    if lines:
        ln = lines[0]
        ymid = (ln[2] + ln[4]) / 2
        ok(abs(ymid - (96 + H - 0.6 * H) + 0.5) < 3, 'TP %s: the line sits at 60%% (%.1f; build 51: the bar is 56 px lower)' % (name, ymid))
        ok((ln[6] >= 0.99) == (g >= 60 or c >= 60), 'TP %s: the line is lit at/over 60, dim below (alpha %.2f)' % (name, ln[6]))
    rects = [o for o in ops if o[0] == 'rect']
    gold = sim.eval('make_color_rgb(255, 214, 64)')
    orange = sim.eval('c_orange')
    red = sim.eval('c_red')
    if 0 < g < 100:
        ok(any(o[5] == orange for o in rects), 'TP %s: orange under the line' % name)
        ok(any(o[5] == gold for o in rects) == (g >= 60), 'TP %s: gold only above the line' % name)
    if g >= 100:
        ok(not any(o[5] == orange for o in rects), 'TP %s: flashing towards white at 100' % name)
        ok(any(o[0] == 'text' and o[4] == 'M' for o in ops), 'TP %s: MAX' % name)
    if chg:
        rr = [o for o in rects if o[5] == red]
        ok(len(rr) == 1 and abs(abs(rr[0][4] - rr[0][2]) - c / 100 * H) <= 2, 'TP %s: the red preview is the charge (%d of the bar)' % (name, c))
    if pop:
        ok(any(o[0] == 'text' and 'YOU DREW A SKILL' in str(o[4]) for o in ops), 'TP %s: YOU DREW A SKILL! pops' % name)
for kv, spr in ((1, 'spr_tensionbar__v1'), (2, 'spr_tensionbar__v2')):
    ops = tp(70, kv=kv)
    ok(spr in [o[1] for o in ops if o[0] == 'spr'], 'TP: knight variant %d draws its own bar sprite %s' % (kv, spr))

print('%d checks, %d failed' % (N[0], len(FAILS)))
for f in FAILS:
    print('FAILED:', f)
sys.exit(1 if FAILS else 0)
