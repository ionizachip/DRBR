"""Build 45-47: the online screens laid out with the game's real font metrics (uiharness) at 640x480: the KNIGHT list with
ONLINE, the ONLINE page (idle / long names / connecting / Steam / failed), MORE OPTIONS, Steam BROWSE, the room (1-8 players,
host / player / practice, lobby / match, Steam / relay), the settings page (every category, both columns, scrolled, host and
player), the typing boxes, the battle HUD (2-8 players, playing / out and watching / TAB / charging / countdown / waiting /
final two / sudden death, long names and attack names), the result / out / lost boxes, and the cold-place lobby (the room box,
8 name tags); build 47: SOUL VISIBILITY / SOUL APPEARANCE / VIEW pages, the room with colours, watching and 12 places,
the watching HUD (every camera, HUD level, help, stats, zoom), QUICK SETTINGS, the banners and the network line. Every text on screen, inside its box, nothing overlapping, the top-bar description in two lines, the HUD never
over the battle box. Then real input through the pages. With an argument, screenshots go to /home/claude/work/uishots/."""
import sys, itertools, json, re
sys.path.insert(0, '/home/claude/work/uiref')
from uiharness import *
import gmrender as G
from br_shot import br_frame

FAILS = []
N = [0]
SHOTS = len(sys.argv) > 1


def ok(c, msg):
    N[0] += 1
    if not c:
        FAILS.append(msg)
        if len(FAILS) < 80:
            print('FAIL', msg, flush=True)


def eq(a, b, msg):
    ok(a == b, '%s (got %r want %r)' % (msg, a, b))


def setup():
    sim, rec = menu_sim()
    sim.run('knight_menu_open();')
    sim.step(1)
    sim.run('global.knight_ui.tp = 80; global.knight_ui.bp = 60; global.knight_ui.inputdelay = 0; global.knight_ui.notice = "";')
    sim.run('global.is_console = 0; kfo_get();')
    return sim, rec


def boxes(rec, modal=False):
    out = []
    ops = rec.ops
    if modal:
        last = max([i for i, o in enumerate(ops) if o[0] == 'darkbox'] or [0])
        ops = ops[last:]
    for o in ops:
        # build 47: a solid (alpha 1) filled box drawn over earlier texts hides them (an overlay such as MATCH STATS)
        if o[0] == 'rect' and len(o) >= 8 and not o[7] and o[6] >= 0.99 and (o[3] - o[1]) < 640:
            rx0, ry0, rx1, ry1 = min(o[1], o[3]), min(o[2], o[4]), max(o[1], o[3]), max(o[2], o[4])
            out = [b for b in out if not (b[0] >= rx0 - 1 and b[2] <= rx1 + 1 and b[1] >= ry0 - 1 and b[3] <= ry1 + 1)]
            continue
        if o[0] != 'text':
            continue
        _, fnt, x, y, t, xs, ys, a, sep, w, c, al, ha, va = o
        if t.strip() == '' or al <= 0.05:
            continue
        f = G.font(fnt)
        lines = t.split('\n')
        wd = max(f.line_width(l) for l in lines) * xs
        ht = f.h * len(lines) * ys
        x0 = x - wd / 2 if ha == 1 else (x - wd if ha == 2 else x)
        out.append((x0, y, x0 + wd, y + ht * 0.8, t, fnt))
    return out


def check(name, rec, body=True, modal=False, shadow_ok=False, min_ops=10, within=None):
    B = boxes(rec, modal)
    ok(len(rec.ops) > min_ops or (modal and len(B) >= 3), '%s: something is drawn' % name)
    if within:
        for (x0, y0, x1, y1, t, fnt) in B:
            ok(x0 >= within[0] and y0 >= within[1] and x1 <= within[2] and y1 <= within[3], '%s: "%s" leaves its box (%.0f,%.0f)-(%.0f,%.0f)' % (name, t, x0, y0, x1, y1))
    for (x0, y0, x1, y1, t, fnt) in B:
        ok(x0 >= -1 and x1 <= 641 and y0 >= -2 and y1 <= 482, '%s: "%s" off screen (%.0f,%.0f)-(%.0f,%.0f)' % (name, t, x0, y0, x1, y1))
        # DRBR: the frame's inside measured on a render (scr_darkbox(50, 80, 590, 420)): x 64-576, the bottom border from y 407
        if body and not modal and 88 <= y0 <= 400:
            ok(x0 >= 63 and x1 <= 577 and y1 <= 406, '%s: "%s" leaves the box (%.0f,%.0f)-(%.0f,%.0f)' % (name, t, x0, y0, x1, y1))
    # DRBR: the menu's heart inside the frame too (16x16, origin top left; the frame's inside is x 64-576)
    if body and not modal:
        for o in rec.ops:
            if o[0] == 'spr' and o[1] == 'spr_heart' and 88 <= o[4] <= 400:
                ok(o[3] >= 63 and o[3] + 16 <= 577, '%s: the heart leaves the frame (x %.0f)' % (name, o[3]))
    for a, b in itertools.combinations(B, 2):
        if shadow_ok and a[4] == b[4]:
            continue
        ix = min(a[2], b[2]) - max(a[0], b[0])
        iy = min(a[3], b[3]) - max(a[1], b[1])
        if ix > 3 and iy > 3:
            ok(False, '%s: "%s" overlaps "%s"' % (name, a[4][:30], b[4][:30]))
    return B


U = 'global.knight_ui'
nshot = [0]


def shot_if(rec, name):
    if SHOTS:
        rec.render('/home/claude/work/uishots/online_%s.png' % name)
        nshot[0] += 1


def draw(sim, rec, code):
    sim.run(code.replace('U.', U + '.'))
    rec.ops.clear()
    sim.run('knight_ui_draw();')


def desc_ok(sim, name):
    ok(sim.eval('array_length(knight_wrap(knight_ui_desc(), 600))') <= 2, '%s: description fits two lines (%s)' % (name, sim.eval('knight_ui_desc()')))


def steam(sim, ready, why='Steam is not running or not signed in.'):
    """Steam as the page sees it (the DLL is not loaded in the emulator)"""
    sim.run('global.kfo_stm = { ok: %s, init: %d, why: "%s", fns: {}, dll: "kf_steam.dll" };' % ('true' if ready else 'false', 1 if ready else -1, why))
    if ready:
        sim.mock('kfo_steam_name', lambda s: 'IONIZACHIP')


NAMES = ['ImperfectNOR', 'WWWWWWWWWWWW', 'Susie', 'Ralsei', 'Noelle', 'MMMMMMMMMMMM', 'Kris', 'Berdly']


def lobby_msg(n, host=1, st='lobby', prac=0, res=None, code='ABCDEFG'):
    pl = []
    for i in range(n):
        inm = 1 if (st == 'match' and i < 5) else 0
        pl.append({'pid': i + 1, 'n': NAMES[i], 's': 1 + i % 4, 'rd': 1 if i % 2 else 0, 'inm': inm, 'bot': 1 if (prac and i > 0) else 0,
                   'rj': 1 if (st == 'match' and not inm) else 0})
    s = {'kn': [0, 1, 2, 3, 4, 5], 'open': 2, 'rush': 6, 'mhp': 150, 'maxp': 8, 'bots': 7 if prac else 0, 'm_storm': 1, 'm_hyper': 1, 'm_dbl': 1, 'm_ohko': 1, 'pre': 'CUSTOM'}
    return {'k': 'lobby', 'code': 'PRACTICE' if prac else code, 'host': host, 'st': st, 'mid': 2, 'prac': prac, 'set': s, 'players': pl, 'res': res if res else 0}


def room(sim, n, host=1, me=1, st='lobby', prac=0, res=None, mode='direct'):
    code = 'ABCDE' if mode == 'direct' else 'ABCDEFG'
    m = lobby_msg(n, host, st, prac, res, code)
    sim.run('var _o = global.kfo; _o.st = "room"; _o.mode = "%s"; _o.my = %d; _o.hostid = %d; _o.code = "%s"; _o.prac = %s; _o.lobby = json_parse(@\'%s\');'
            % ('local' if prac else mode, me, host, m['code'], 'true' if prac else 'false', json.dumps(m)))
    if host == me:
        sim.run('kfo_host_begin(global.kfo.code, %s); global.kfo.H.set = kfo_set_clean(global.kfo.lobby.set); global.kfo.H.dl = false;' % ('true' if prac else 'false'))
        # the host's own list has the others too (REMOVE A PLAYER lists them)
        sim.run('var _pl = global.kfo.lobby.players; for (var _i = 0; _i < array_length(_pl); _i++) if (_pl[_i].pid != global.kfo.my && is_undefined(kfo_host_player(_pl[_i].pid)))'
                ' array_push(global.kfo.H.pl, kfo_host_player_new(_pl[_i].pid, _pl[_i].n, _pl[_i].s, _pl[_i].bot));')
    if st == 'match':
        sim.run('global.kfo.M = kfo_match_new({ mid: 2, seed: 9, set: global.kfo.lobby.set, players: global.kfo.lobby.players, prac: 0 });'
                'global.kfo.M.st = { an: 3, sn: 5, pl: [] };')


# ---------------------------------------------------------------- KNIGHT tab (DRBR 1.0.1: ONLINE is its own page, the first)
for focus in (0, 1):
    for row in range(10):
        sim, rec = setup()
        draw(sim, rec, 'U.tab=0; U.focus=%d; U.krow=%d;' % (focus, row))
        check('knight f%d r%d' % (focus, row), rec)
        if focus:
            desc_ok(sim, 'knight r%d' % row)
sim, rec = setup()
eq(sim.py(sim.eval('knight_ui_tab_order()')), [5, 0, 1, 2, 3, 4], '1.0.1: the top bar - ONLINE first, then KNIGHT, PARTY, POWER, RULES, CONFIG')
eq(sim.eval('global.knight_ui.tab'), 5, '1.0.1: the menu opens on the ONLINE page')
ok(all(sim.eval('knight_ui_fights()[%d].kind' % i) != 'online' for i in range(sim.eval('array_length(knight_ui_fights())'))), '1.0.1: no ONLINE on the KNIGHT page')
for row in range(10):
    sim, rec = setup()
    draw(sim, rec, 'U.tab=5; U.focus=0; U.onl_row=%d;' % row)
    check('online tab (top bar) r%d' % row, rec)
    ok(not any(o[0] == 'spr' and o[1] == 'spr_heart' and 88 <= o[4] <= 400 for o in rec.ops), 'online tab (top bar) r%d: no row picked (no heart)' % row)
    if row == 0:
        shot_if(rec, 'tab_online')
for mode in ('direct', 'steam', 'prac'):
    sim, rec = setup()
    room(sim, 3, mode=mode if mode != 'prac' else 'direct', prac=1 if mode == 'prac' else 0)
    draw(sim, rec, 'U.tab=5; U.focus=0;')
    check('online tab in room (%s)' % mode, rec)
    if mode == 'steam':
        shot_if(rec, 'tab_online_room')

# ---------------------------------------------------------------- ONLINE page
NROW = 10
for row in range(NROW):
    for variant in ('idle', 'long', 'busy', 'steambusy', 'failed', 'steam', 'nosteam'):
        sim, rec = setup()
        code = 'U.tab=5; U.focus=1; U.sub="online"; U.onl_row=%d; U.onl_scroll=%d;' % (row, max(0, row - 7))
        steam(sim, variant in ('steam', 'steambusy'), 'kf_steam.dll is missing (run Install Knight Fights again).' if variant == 'nosteam' else 'Steam is not running or not signed in: Steam client not running.')
        if variant == 'long':
            code += 'global.kfo.name = "WWWWWWWWWWWW"; global.kfo.srv = "relay-server.example-host.org"; global.kfo.port = 25565; global.kfo.skin = 3;'
        if variant == 'busy':
            code += 'global.kfo.st = "connecting"; global.kfo.mode = "direct"; global.kfo.srv = "203.0.113.250"; global.kfo.port = 25565;'
        if variant == 'steambusy':
            code += 'global.kfo.st = "joining"; global.kfo.mode = "steam";'
        if variant == 'failed':
            code += 'global.kfo.st = "failed"; global.kfo.err = "That room\'s players have an older Knight Hub build (Client Is Newer). Ask the host to update to build 45.";'
        draw(sim, rec, code)
        check('online r%d %s' % (row, variant), rec)
        desc_ok(sim, 'online r%d %s' % (row, variant))
        if row in (0, 9) and variant in ('idle', 'steam', 'failed', 'nosteam'):
            shot_if(rec, 'page_%d_%s' % (row, variant))

# ---------------------------------------------------------------- MORE OPTIONS
for row in range(8):
    for variant in ('plain', 'long'):
        sim, rec = setup()
        code = 'U.tab=5; U.focus=1; U.sub="onl_opt"; U.opt_row=%d;' % row
        if variant == 'long':
            code += ('global.kfo.srv = "relay-server.example-host.org"; global.kfo.port = 25565; global.kfo.view.names = 0; global.kfo.vis = 2; global.kfo.view.sop = 35;'
                     'global.kfo.view.show = 0; global.kfo.look.col = make_color_rgb(160, 64, 255); global.kfo.song = 9;'
                     'kfo_key_set("breath", 20); kfo_key_set("use", 34); kfo_key_set("charge", 220); kfo_key_set("hold", 111);')
        draw(sim, rec, code)
        check('options r%d %s' % (row, variant), rec)
        desc_ok(sim, 'options r%d %s' % (row, variant))
        if row == 0:
            shot_if(rec, 'options_' + variant)

# ---------------------------------------------------------------- DRBR: the SKINS page (every group, every skin under the cursor,
# worn or not, from the ONLINE page and from the room): on screen, nothing overlapping, the description in two lines; the keys
sim0, _ = setup()
cats = sim0.py(sim0.eval('kfo_skin_cats()'))
eq([c[0] for c in cats], ['main', 'flowers', 'bosses', 'other'], 'SKINS: four groups (PARTY, FLOWERS, BOSSES, OTHER)')
eq(sim0.py(sim0.eval('kfo_skin_cat_list("flowers")')), [5, 7, 8, 9, 10, 11, 12], 'SKINS: the flowers - Flowery, Aqua, Seth, Orange, Green, Yellow, Blue')
eq(sim0.py(sim0.eval('kfo_skin_cat_list("bosses")')), [13, 14], 'SKINS: the bosses - Pink, Spamton')
for ci, c in enumerate(cats):
    lst = sim0.py(sim0.eval('kfo_skin_cat_list("%s")' % c[0]))
    for i, s in enumerate(lst):
        for variant in ('online', 'lobby'):
            sim, rec = setup()
            if variant == 'lobby':
                room(sim, 5, mode='steam')
            draw(sim, rec, 'global.kfo.skin = %d; kfo_ui_skin_open("%s"); U.sk_cat = %d; U.sk_i = %d;' % (lst[0], variant, ci, i))
            name = 'skins %s %s %s' % (c[0], s, variant)
            check(name, rec, shadow_ok=True)
            desc_ok(sim, name)
            ok(sim.eval('kfo_skin_ready(%d)' % s), '%s: its art is in the game' % name)
            if variant == 'online' and (i == 0 or s in (8, 12, 13, 14)):
                shot_if(rec, 'skins_%s_%d' % (c[0], s))

# ---------------------------------------------------------------- DRBR: the BOSSES page (both groups, every boss under the cursor,
# outside a room, as the host and as a player of a room): on screen, nothing overlapping, the description in two lines, the card
sim0, _ = setup()
eq(sim0.py(sim0.eval('kfo_boss_cat_list(0)')), [0, 1, 2, 3, 4, 5], 'BOSSES: the six knights in the KNIGHTS group (Cyan is offline only)')
eq(sim0.py(sim0.eval('kfo_boss_cat_list(1)')), [6, 7, 8, 9, 10], 'BOSSES: Jevil, Gerson, Flowery, Spamton NEO, Pink in the BOSSES group')
eq(sim0.py(sim0.eval('[kfo_boss_soul(0), kfo_boss_soul(6), kfo_boss_soul(7), kfo_boss_soul(8), kfo_boss_soul(9), kfo_boss_soul(10)]')),
   ['red', 'red', 'green', 'orange', 'yellow', 'purple'], 'BOSSES: each one\'s SOUL mode')
for ci in (0, 1):
    lst = sim0.py(sim0.eval('kfo_boss_cat_list(%d)' % ci))
    for i, k in enumerate(lst):
        for variant in ('online', 'host', 'player'):
            sim, rec = setup()
            if variant != 'online':
                room(sim, 5, me=(1 if variant == 'host' else 2), mode='steam')
            draw(sim, rec, 'kfo_ui_boss_open("%s"); U.bs_cat = %d; U.bs_i = %d;' % ('online' if variant == 'online' else 'lobby', ci, i))
            name = 'bosses %d %s %s' % (ci, k, variant)
            check(name, rec, shadow_ok=True)
            desc_ok(sim, name)
            ok(sim.eval('kfo_boss_ready(%d)' % k), '%s: its art is in the game' % name)
            txt = ' '.join(b[4] for b in boxes(rec))
            ok('SOUL' in txt and 'SENDS' in txt and 'ATTACKS' in txt, '%s: the card has its SOUL, sends and attacks (%s)' % (name, txt[-200:]))
            if variant != 'online':
                ok(('IN THIS ROOM' in txt), '%s: the card says whether the room fights it' % name)
            if variant == 'online' or i == 0:
                shot_if(rec, 'bosses_%s_%d_%d' % (variant, ci, k))

# ---------------------------------------------------------------- build 47: SOUL VISIBILITY / SOUL APPEARANCE / VIEW pages
PAGES = {'onl_view': 6, 'onl_look': 8, 'onl_mview': 16}   # build 48: SOUL SETTINGS 5 rows + DONE; SOUL COLOR 7 (with the OUTLINE rows) + DONE; 1.0.1: VIEW + BOSS LINES
for pg, nrow in PAGES.items():
    sim0, _ = setup()
    eq(sim0.eval('array_length(kfo_ui_pg_rows("%s"))' % pg), nrow, '%s has %d rows' % (pg, nrow))
    for row in range(nrow):
        for variant in ('default', 'extreme', 'room'):
            sim, rec = setup()
            if variant == 'room':
                room(sim, 5, mode='steam')
            code = 'U.tab=5; U.focus=1; kfo_ui_pg_open("%s", "%s"); U.pg_row=%d; U.pg_scroll=%d;' % (pg, 'lobby' if variant == 'room' else 'onl_opt', row, max(0, row - 13))
            if variant == 'extreme':
                # every setting at its widest value
                code += ('var _V = global.kfo.view; _V.sop = 100; _V.nop = 100; _V.cmode = 3; _V.skfx = 2; _V.spv = 2; _V.shud = 2; _V.cam = 3; _V.zoom = 3;'
                         'var _L = global.kfo.look; _L.col = make_color_rgb(255, 255, 255); _L.olc = 5; _L.hli = 3; _L.gmc = 1;')
            draw(sim, rec, code)
            name = '%s r%d %s' % (pg, row, variant)
            check(name, rec, shadow_ok=True)
            desc_ok(sim, name)
            if row == 0 and variant != 'room':
                shot_if(rec, '%s_%s' % (pg, variant))
# the OPACITY slider (0-100 in steps of 5): drawn as a slider with the value; < > a step; held, it keeps sliding; saved once
SLD = ('global.SLD = [];\n' + 'function kfo_slider_draw(_x0, _x1, _y, _v, _hot) { array_push(global.SLD, [_x0, _x1, _y, _v, _hot]); return 1; }\n')
for v in (0, 20, 55, 100):
    sim, rec = setup()
    sim.load_source('gml_GlobalScript_sld_log', SLD)
    sim.run('global.SLD = [];')
    draw(sim, rec, 'U.tab=5; U.focus=1; kfo_ui_pg_open("onl_view", "onl_opt"); U.pg_row=3; global.kfo.view.sop = %d;' % v)
    sl = sim.py(sim.eval('global.SLD'))
    ok(any(x[3] == v and x[4] for x in sl), 'OPACITY %d%%: drawn as a slider: %s' % (v, sl))
sim, rec = setup()
sim.run('U.tab=5; U.focus=1; kfo_ui_pg_open("onl_view", "onl_opt"); U.pg_row=3; global.kfo.view.sop = 20; global.knight_ui.inputdelay = 0;'.replace('U.', U + '.'))
held_keys = {'right': 0}
sim.mock('right_p', lambda s: 1 if s.kp == 'right' else 0)
sim.mock('left_p', lambda s: 1 if s.kp == 'left' else 0)
sim.mock('right_h', lambda s: 1 if s.kh == 'right' else 0)
sim.mock('left_h', lambda s: 1 if s.kh == 'left' else 0)
writes = []
orig_save = None
sim.kp = ''
sim.kh = ''
sim.run('knight_ui_step();')
vals = []
for f in range(30):
    sim.kp = 'right' if f == 0 else ''
    sim.kh = 'right'
    sim.run('knight_ui_step();')
    vals.append(sim.eval('global.kfo.view.sop'))
sim.kp = ''
sim.kh = ''
sim.run('knight_ui_step();')
sim.run('global.KS = global.kfo; global.kfo = undefined; kfo_get(); global.KV = global.kfo.view.sop; global.kfo = global.KS;')
ok(vals[0] == 25 and vals[-1] > 60 and vals == sorted(vals) and all(b - a in (0, 5) for a, b in zip(vals, vals[1:])),
   'OPACITY slider: a press is one step (20 -> 25), held it keeps sliding in 5%% steps (%s)' % vals)
eq(sim.eval('global.KV'), vals[-1], 'OPACITY slider: let go, the value is saved')
for f in range(40):
    sim.kp = 'right' if f == 0 else ''
    sim.kh = 'right'
    sim.run('knight_ui_step();')
eq(sim.eval('global.kfo.view.sop'), 100, 'OPACITY slider: stops at 100')
for f in range(60):
    sim.kp = 'left' if f == 0 else ''
    sim.kh = 'left'
    sim.run('knight_ui_step();')
eq(sim.eval('global.kfo.view.sop'), 15, 'OPACITY slider: down to 15 (build 49: never below a visible level)')

# the SOUL color code box: a good code and a bad one
for txt, good in (('#A040FF', True), ('#GG0000', False), ('#12345', False), ('#FFF', True)):
    sim, rec = setup()
    sim.run('U.tab=5; U.focus=1; kfo_ui_pg_open("onl_look", "onl_opt"); kfo_ui_text("hex"); keyboard_string = "%s";'.replace('U.', U + '.') % txt)
    sim.run('kfo_ui_text_step(global.knight_ui.modal);')
    c0 = sim.eval('global.kfo.look.col')
    rec.ops.clear()
    sim.run('knight_ui_draw();')
    check('typing hex %s' % txt, rec, modal=True)
    sim.press('enter')
    sim.step(1)
    sim.run('if (is_struct(global.knight_ui.modal)) kfo_ui_text_step(global.knight_ui.modal);')
    c1 = sim.eval('global.kfo.look.col')
    if good:
        ok(c1 == sim.eval('kfo_hex_col("%s", -1)' % txt) and c1 >= 0, 'color code %s accepted (%s)' % (txt, c1))
    else:
        ok(c1 == c0 and 'Not a color code' in sim.eval('global.knight_ui.warn'), 'color code %s refused, the color kept (%s, "%s")' % (txt, c1, sim.eval('global.knight_ui.warn')))
    shot_if(rec, 'typing_hex_%s' % ('ok' if good else 'bad'))

# ---------------------------------------------------------------- BROWSE
for nb in (0, 1, 4, 9, 14):
    sim, rec = setup()
    steam(sim, True)
    rooms = []
    for i in range(nb):
        rooms.append({'lid': str(109775243592498246 + i), 'code': 'ABCDEF' + chr(65 + i % 26), 'host': NAMES[i % 8], 'np': [2, 8, 3, 5][i % 4], 'mx': 8,
                      'ver': [45, 45, 44, 46][i % 4], 'st': ['lobby', 'match'][i % 2]})
    sim.run('global.kfo.browse = json_parse(@\'%s\'); global.kfo.browse_st = "%s";' % (json.dumps(rooms), '' if nb == 0 else ('%d PUBLIC ROOMS.' % nb)))
    for row in (0, max(0, nb - 1)):
        draw(sim, rec, 'U.tab=5; U.focus=1; U.sub="onl_br"; U.br_row=%d;' % row)
        check('browse %d r%d' % (nb, row), rec)
        desc_ok(sim, 'browse %d' % nb)
    if nb in (0, 9):
        shot_if(rec, 'browse_%d' % nb)

# ---------------------------------------------------------------- the room
for n in (1, 2, 5, 8):
    for who in ('host', 'player', 'practice'):
        for st in ('lobby', 'match'):
            for mode in ('direct', 'steam'):
                if who == 'practice' and (st == 'match' or mode == 'steam'):
                    continue
                res = {'wid': 2, 'wn': 'WWWWWWWWWWWW', 'sn': 5} if n == 5 else None
                sim0, _ = setup()
                room(sim0, n, host=1, me=(1 if who != 'player' else 2), st=st, prac=(1 if who == 'practice' else 0), res=res, mode=mode)
                nrows = sim0.eval('array_length(kfo_ui_lobby_rows())')
                for row in range(nrows):
                    sim, rec = setup()
                    room(sim, n, host=1, me=(1 if who != 'player' else 2), st=st, prac=(1 if who == 'practice' else 0), res=res, mode=mode)
                    draw(sim, rec, 'U.tab=5; U.focus=1; U.sub="lobby"; U.lob_row=%d; U.lob_scroll=%d;' % (row, max(0, row - 5)))
                    name = 'lobby n%d %s %s %s r%d' % (n, who, st, mode, row)
                    check(name, rec)
                    desc_ok(sim, name)
                    if row == 0 and n in (5, 8):
                        shot_if(rec, 'lobby_%d_%s_%s_%s' % (n, who, st, mode))
sim, rec = setup()
room(sim, 3, mode='steam')
eq(sim.py(sim.eval('kfo_ui_lobby_rows()')), ['start', 'name', 'skin', 'look', 'keys', 'options', 'settings', 'bosses', 'bots', 'invite', 'copy', 'help', 'kick', 'leave'],
   'Steam room (host): START, SKIN, SOUL, KEYBINDS, MORE OPTIONS, SETTINGS, BOTS, INVITE, COPY CODE, CONNECTION HELP, REMOVE, LEAVE')
sim, rec = setup()
room(sim, 3, me=2, st='match', mode='direct')
sim.run('global.kfo.M.me = true; global.kfo.M.out = false;')
eq(sim.py(sim.eval('kfo_ui_lobby_rows()')), ['ready', 'name', 'skin', 'look', 'keys', 'options', 'settings', 'bosses', 'copy', 'help', 'leave'], 'a player in the match (relay): no SPECTATE for yourself')
sim, rec = setup()
room(sim, 8, me=7, st='match', mode='direct')
sim.run('global.kfo.M.me = false;')
eq(sim.py(sim.eval('kfo_ui_lobby_rows()')), ['ready', 'spectate', 'join', 'name', 'skin', 'look', 'keys', 'options', 'settings', 'bosses', 'copy', 'help', 'leave'],
   'a player waiting outside the match: SPECTATE MATCH and JOIN MATCH (greyed, with the reason)')
ok(sim.eval('kfo_ui_lobby_why("join")') != '', 'JOIN MATCH says why not (%s)' % sim.eval('kfo_ui_lobby_why("join")'))
# build 49: the room's BOTS page (host only) and one bot's page: every row laid out, the description in two lines; then real
# input: ADD / REMOVE, the room's BOT SKILL, a bot's preset, a slider (CUSTOM), ROOM'S SKILL
for n, prac in ((8, 1), (3, 1), (4, 0)):
    sim0, _ = setup()
    room(sim0, n, prac=prac)
    for pg in ('onl_bots', 'onl_bot'):
        nr = sim0.eval('array_length(kfo_ui_bots_rows("%s"))' % pg)
        for row in range(nr):
            sim, rec = setup()
            room(sim, n, prac=prac)
            draw(sim, rec, 'U.tab=5; U.focus=1; U.sub="%s"; U.pg_row=%d; U.pg_scroll=%d; U.pg_from="lobby"; U.bot_i=0;' % (pg, row, max(0, row - 13)))
            name = '%s n%d prac%d r%d' % (pg, n, prac, row)
            check(name, rec)
            desc_ok(sim, name)
            if row == 0:
                shot_if(rec, '%s_%d_%d' % (pg, n, prac))
sim, rec = setup()
room(sim, 3, prac=1)
eq(sim.py(sim.eval('kfo_ui_bots_rows("onl_bots")')), ['bot0', 'bot1', 'badd', 'bdel', 'ball', 'done'], 'BOTS page: each bot, ADD, REMOVE, ALL BOTS, DONE')
sim.run('global.kfo.H.set.bots = 2;')
sim.run('kfo_ui_bots_change("onl_bots", "badd", 1, true);')
eq(sim.eval('array_length(kfo_ui_bots_list())'), 3, 'ADD A BOT: three bots')
sim.run('kfo_ui_bots_change("onl_bots", "bdel", 1, true);')
eq(sim.eval('array_length(kfo_ui_bots_list())'), 2, 'REMOVE A BOT: two bots')
sim.run('kfo_ui_bots_change("onl_bots", "ball", 1, false);')
eq(sim.eval('kfo_host_botcfg(0).pre'), 3, 'ALL BOTS > : the room goes HARD, every bot follows')
sim.run('global.knight_ui.bot_i = 1; kfo_ui_bots_change("onl_bot", "bpre", 1, false); kfo_ui_bots_change("onl_bot", "bpre", 1, false);')
eq(sim.py(sim.eval('[kfo_host_botcfg(0).pre, kfo_host_botcfg(1).pre]')), [3, 5], 'bot 2 alone set to PERFECT (bot 1 stays HARD)')
sim.run('kfo_ui_bots_change("onl_bot", "react", 1, false);')
eq(sim.py(sim.eval('[kfo_host_botcfg(1).pre, kfo_host_botcfg(1).react]')), [-1, 1], 'a slider moved: bot 2 is CUSTOM, reaction 1 frame')
eq(sim.py(sim.eval('kfo_ui_bots_label("onl_bots", "bot1")'))[1], 'CUSTOM', 'the list shows CUSTOM')
sim.run('kfo_ui_bots_change("onl_bot", "bdef", 0, true);')
eq(sim.py(sim.eval('[kfo_host_botcfg(1).pre, kfo_host_botcfg(1).own]')), [3, False], "ROOM'S SKILL: bot 2 follows the room again")
sim, rec = setup()
room(sim, 4, me=2)
ok('bots' not in sim.py(sim.eval('kfo_ui_lobby_rows()')), 'a player who is not the host has no BOTS row')
# build 47: the room with SOUL colours, watchers and up to 12 places (8 players + 4 watch places: the compact rows)
for n in (8, 10, 12):
    sim, rec = setup()
    room(sim, min(n, 8), mode='steam')
    sim.run('var _pl = global.kfo.lobby.players; for (var _i = array_length(_pl); _i < %d; _i++) array_push(_pl, { pid: _i + 1, n: "WWWWWWWWWWWW", s: 1 + _i mod 4, rd: 0, inm: 0, bot: 0, sp: 1 });'
            'for (var _i = 0; _i < array_length(_pl); _i++) { _pl[_i].cl = kfo_col_presets()[_i mod 9][1]; _pl[_i].lat = 30 + _i * 40; }' % n)
    for row in (0, 3):
        draw(sim, rec, 'U.tab=5; U.focus=1; U.sub="lobby"; U.lob_row=%d; U.lob_scroll=0;' % row)
        check('lobby colours n%d r%d' % (n, row), rec)
    shot_if(rec, 'lobby_colours_%d' % n)

# the REMOVE A PLAYER box (8 players: 7 to pick from)
sim, rec = setup()
room(sim, 8, mode='steam')
rows = sim.py(sim.eval('kfo_ui_lobby_rows()'))
sim.run('U.tab=5; U.focus=1; U.sub="lobby"; U.lob_row=%d; U.lob_scroll=%d;'.replace('U.', U + '.') % (rows.index('kick'), max(0, rows.index('kick') - 5)))
sim.inp['ok'] = 1
sim.run('knight_ui_step();')
sim.inp['ok'] = 0
eq(sim.eval('global.knight_ui.modal.k'), 'kfo_kick', 'REMOVE A PLAYER opens its box')
rec.ops.clear()
sim.run('knight_ui_draw();')
check('kick box', rec, modal=True)
shot_if(rec, 'kick_box')

# ---------------------------------------------------------------- settings
for who in ('host', 'player'):
    sim0, _ = setup()
    room(sim0, 3, me=(2 if who == 'player' else 1))
    ncat = sim0.eval('array_length(kfo_cats())')
    eq(ncat, 10, 'ten settings pages (build 52: BASICS ... ADVANCED, PRESETS)')
    for cat in range(ncat):
        nit = sim0.eval('array_length(kfo_ui_set_items(%d))' % cat)
        ok(nit >= 2, 'category %d has items (%d)' % (cat, nit))
        for focus, opt in [(0, 0)] + [(1, o) for o in sorted(set([0, nit // 2, nit - 1]))]:
            sim, rec = setup()
            room(sim, 3, me=(2 if who == 'player' else 1))
            draw(sim, rec, 'U.tab=5; U.focus=1; U.sub="onl_set"; U.set_row=%d; U.set_focus=%d; U.set_opt=%d; U.set_scroll=%d;'
                 % (cat, focus, opt, max(0, opt - 12)))
            check('settings %s c%d f%d o%d' % (who, cat, focus, opt), rec)
            desc_ok(sim, 'settings %s c%d f%d o%d' % (who, cat, focus, opt))
            if opt == 0 and focus == 1:
                shot_if(rec, 'settings_%s_c%d' % (who, cat))
# every option's text in the widest form it can take (the max of every number, every enum name)
sim, rec = setup()
room(sim, 3)
sim.run('global.TW = []; var _o = kfo_opts(); for (var _i = 0; _i < array_length(_o); _i++) { var _e = _o[_i]; var _s = kfo_set_default();'
        ' if (_e.kind == "num" || _e.kind == "enum") { for (var _v = _e.lo; _v <= _e.hi; _v += max(1, _e.st)) { variable_struct_set(_s, _e.oid, _v);'
        ' scr_84_set_draw_font("main"); array_push(global.TW, [_e.oid, kfo_opt_text(_e, _s), string_width(kfo_opt_text(_e, _s)), string_width(_e.lab)]); } } }')
tw = sim.py(sim.eval('global.TW'))
wide = [t for t in tw if t[2] > 110]
ok(not wide, 'every option value fits its 110 px column (%r)' % wide[:5])
labs = [t for t in tw if t[3] > 220]
ok(not labs, 'every option label fits its 220 px column (%r)' % labs[:5])

# ---------------------------------------------------------------- KEYBINDS (build 46)
eq(setup()[0].eval('array_length(kfo_key_list())'), 12, 'KEYBINDS: twelve actions (build 48: + the three targeting keys; build 49: + CHAT)')
for row in range(10):
    for variant in ('default', 'long', 'room'):
        sim, rec = setup()
        if variant == 'room':
            room(sim, 5, mode='steam')
        code = 'U.tab=5; U.focus=1; U.sub="onl_keys"; U.keys_row=%d; U.keys_from="%s";' % (row, 'lobby' if variant == 'room' else 'onl_opt')
        if variant == 'long':
            code += ('kfo_key_set("breath", 20); kfo_key_set("use", 34); kfo_key_set("charge", 220); kfo_key_set("hold", 111); kfo_key_set("list", 162);'
                     'kfo_key_set("quit", 93); kfo_key_set("quick", 145);')
        draw(sim, rec, code)
        check('keybinds r%d %s' % (row, variant), rec)
        desc_ok(sim, 'keybinds r%d %s' % (row, variant))
        if row == 0:
            shot_if(rec, 'keybinds_' + variant)
# the box that waits for a key (with a refused key explained)
for k in (88, 161, 38, 115, 13):
    sim, rec = setup()
    sim.run('U.tab=5; U.focus=1; U.sub="onl_keys"; U.keys_row=1;'.replace('U.', U + '.'))
    sim.inp['ok'] = 1
    sim.run('knight_ui_step();')
    sim.inp['ok'] = 0
    sim.run('var _m = global.knight_ui.modal; _m.lines = ["Press the key you want (now " + kfo_key_label(_m.data) + ").", "ESC: cancel",'
            ' "Not " + kfo_key_name(%d) + ": " + kfo_key_why(%d) + "."];' % (k, k))
    rec.ops.clear()
    sim.run('knight_ui_draw();')
    check('keybinds box %d' % k, rec, modal=True)
    if k == 161:
        shot_if(rec, 'keybinds_box')

# ---------------------------------------------------------------- typing boxes
for what, txt in (('name', 'WWWWWWWWWWWW'), ('code', 'VNRTK'), ('scode', 'ABCDEFG'), ('server', 'relay-server.example-host.org:25565'),
                  ('import', 'KF45:' + 'eyJrbiI6WzAsMSwyLDMsNCw1XSwicnVzaCI6Nn0' * 6)):
    sim, rec = setup()
    sim.run('U.tab=5; U.focus=1; U.sub="online"; kfo_ui_text("%s"); keyboard_string = "%s";'.replace('U.', U + '.') % (what, txt))
    sim.run('kfo_ui_text_step(global.knight_ui.modal);')
    rec.ops.clear()
    sim.run('knight_ui_draw();')
    check('typing %s' % what, rec, modal=True)
    shot_if(rec, 'typing_' + what)

# ---------------------------------------------------------------- the battle HUD
BOX = (243, 95, 393, 245)
CENTER_OK = ('WAITING FOR', 'THE LAST SOUL', 'PRACTICE', 'FIGHT', '1', '2', '3')


def hud_check(name, rec, n, overlay=False, sim=None):
    B = check(name, rec, body=False, shadow_ok=True)
    if overlay:
        # MATCH STATS (I while watching) is an overlay over the battle while it is open
        return B
    for (x0, y0, x1, y1, t, fnt) in B:
        inbox = min(x1, BOX[2]) - max(x0, BOX[0]) > 2 and min(y1, BOX[3]) - max(y0, BOX[1]) > 2
        # inside the box only: the countdown / wait texts, and the other SOULs' name tags and numbers (they follow the SOULs)
        tag = re.sub(r'^P[1-8] ', '', t).upper()
        if inbox and not any(t.startswith(c) for c in CENTER_OK) and tag not in [x[:6].upper() for x in NAMES] + [x[:8].upper() for x in NAMES] and not re.match(r'^P[1-8]$', t):
            ok(False, '%s: "%s" is drawn over the battle box' % (name, t))
    if sim is not None:
        # DRBR: nothing of the HUD reaches into the party panel at the bottom (its names and HP bars start at y 440). The HUD
        # alone is drawn for this (the panel's own HP numbers are the game's); the frame's draw list is put back after.
        keep = list(rec.ops)
        rec.ops.clear()
        sim.run('kbr_hud_draw(0, 0);')
        for (x0, y0, x1, y1, t, fnt) in boxes(rec, False):
            # (the chat's line on the left, the SOULs' tags inside the box and the knight's name are all above it)
            ok(y1 <= 441, '%s: "%s" reaches into the party panel (bottom %d)' % (name, t, y1))
        for o in rec.ops:
            # (a full-width or full-height rectangle is a screen effect - the darkness, a flash, FINAL TWO's edges - not a box)
            if o[0] == 'rect' and not (min(o[1], o[3]) <= 0 and max(o[1], o[3]) >= 639) and abs(o[4] - o[2]) < 400:
                ok(max(o[2], o[4]) <= 444, '%s: a HUD box reaches into the party panel (%r)' % (name, o[:5]))
        rec.ops[:] = keep
    return B


for n in (2, 5, 8):
    for variant in ('run', 'out_watch', 'tab', 'charging', 'countdown', 'wait', 'ft', 'sd', 'arm', 'idle'):
        out = tuple(range(n - 2, n)) if n > 2 else ()
        kw = {'n': n, 'out': out, 'render': False}
        if variant == 'out_watch':
            kw.update(me_out=True, spect=2)
        if variant == 'tab':
            kw.update(tab=True)
        if variant == 'charging':
            kw.update(charging=True)
        if variant == 'countdown':
            kw.update(ph='idle', k=0, tick=40)
        if variant == 'wait':
            kw.update(go=False, ph='wait', k=0)
        if variant == 'ft':
            kw.update(out=tuple(range(2, n)), ft=True)
        if variant == 'sd':
            kw.update(sd=True)
        if variant in ('arm', 'idle'):
            kw.update(ph=variant)
        sim, rec = br_frame('t_%d_%s' % (n, variant), **kw)
        name = 'hud n%d %s' % (n, variant)
        if variant == 'tab':
            check(name, rec, body=False, shadow_ok=True)
        else:
            B = hud_check(name, rec, n, sim=sim)
            if variant == 'run':
                ok(any(b[4].startswith('SOULS ') for b in B), '%s: the SOULS header' % name)
                ok(len([b for b in B if b[0] >= 466]) >= n, '%s: a row per player on the right' % name)
        if SHOTS and n == 8:
            rec.render('/home/claude/work/uishots/online_hud_%s.png' % variant)
# build 47: watching (every camera, HUD level, help, stats), QUICK SETTINGS, the banner, MATCH INFO, the network line
W47 = [('watch_follow', dict(watcher=True, spect=2), 'global.kfo.M.vw.cam = 0;'),
       ('watch_full', dict(watcher=True, spect=2), 'global.kfo.M.vw.cam = 1;'),
       ('watch_auto', dict(watcher=True, spect=2), 'global.kfo.M.vw.cam = 2; global.kfo.M.vw.auto_why = "FINAL TWO";'),
       ('watch_zoom', dict(watcher=True, spect=2), 'global.kfo.M.vw.cam = 3; global.kfo.M.vw.zoom_x = 320; global.kfo.M.vw.zoom_y = 170;'),
       ('watch_minimal', dict(watcher=True, spect=2), 'global.kfo.view.shud = 1;'),
       ('watch_hidden', dict(watcher=True, spect=2), 'global.kfo.view.shud = 2;'),
       ('watch_help', dict(watcher=True, spect=2), 'global.kfo.view.help = 1; global.kfo.M.vw.stats = true;'),
       ('out_watch_stats', dict(me_out=True, spect=2), 'global.kfo.M.vw.stats = true; global.kfo.view.net = 1;'),
       ('qs_player', dict(), 'global.kfo.M.vw.qs = true; global.kfo.M.vw.qs_row = 3;'),
       ('qs_watcher', dict(watcher=True, spect=2), 'global.kfo.M.vw.qs = true; global.kfo.M.vw.qs_row = 8;'),
       ('banner', dict(), 'global.kfo.M.vw.banner = "MMMMMMMMMMMM IS OUT (#5) - WWWWWWWWWWWW TOOK THE LEAD"; global.kfo.M.vw.banner_t = 60;'),
       ('info_net', dict(), 'global.kfo.view.info = 1; global.kfo.view.net = 1; global.kfo.M.ck.rtt = 230; global.kfo.M.ck.ra = 230;'),
       ('labels', dict(), 'global.kfo.view.names = 1; global.kfo.view.nums = 1; global.kfo.view.mark = 1;'),
       ('colorblind', dict(), 'global.kfo.view.cmode = 3; global.kfo.view.mark = 1; global.kfo.view.names = 1;')]
for n in (2, 8):
    for variant, kw, pre in W47:
        kw2 = dict(kw)
        kw2.update(n=n, out=tuple(range(n - 2, n)) if n > 2 else (), render=False, pre=pre)
        if 'spect' in kw2 and kw2['spect'] > n:
            kw2['spect'] = 1
        sim, rec = br_frame('t47_%d_%s' % (n, variant), **kw2)
        name = 'hud47 n%d %s' % (n, variant)
        B = hud_check(name, rec, n, overlay=('stats = true' in pre), sim=sim)
        txt = ' '.join(b[4] for b in B)
        if variant.startswith('qs'):
            ok('QUICK SETTINGS' in txt, '%s: the QUICK SETTINGS box is drawn (%s)' % (name, txt[:120]))
        if variant == 'banner':
            ok(any(b[4].startswith('MMMMMMMMMMMM IS OUT') or b[4].startswith('MMMMMMMMMMMM') for b in B), '%s: the banner is drawn, fitted' % name)
        if variant == 'watch_hidden':
            ok(not any('CAMERA' in b[4] for b in B), '%s: HIDDEN shows no watching HUD' % name)
        if variant in ('watch_follow', 'watch_full', 'watch_auto') and n == 8:
            ok(any('CAMERA' in b[4] or 'FOLLOW' in b[4] or 'FULL' in b[4] or 'AUTO' in b[4] for b in B), '%s: the camera mode is shown (%s)' % (name, txt[:160]))
        if SHOTS and n == 8:
            rec.render('/home/claude/work/uishots/online_hud47_%s.png' % variant)

# DRBR: every notice at once - MATCH INFO, NETWORK STATS, a banner, the SOUL hint (yellow), five sends coming in while two players
# target you, the chat (its recent lines, typing, expanded with TAB); and Flowery's MERCY bar on top of the stack, a network
# warning over the SOULS header: nothing over another, over the box or in the party panel
BUSY = ('var _M = global.kfo.M; global.kfo.my = 2; global.kfo.hostid = 1; global.kfo.view.info = 1; global.kfo.view.net = 1; _M.ck.rtt = 230; _M.ck.ra = 230;'
        '_M.vw.banner = "MMMMMMMMMMMM IS OUT (#5) - WWWWWWWWWWWW TOOK THE LEAD"; _M.vw.banner_t = 60; _M.sh_mode = "red";'
        '_M.sk.pend = [{ from: 3, sid: 26 }, { from: 4, sid: 45 }, { from: 5, sid: 51 }, { from: 6, sid: 33 }, { from: 3, sid: 38 }]; _M.tg.att = [3, 4];'
        'for (var _i = 0; _i < 8; _i++) kfo_chat_add({ ci: "c" + string(_i), n: "MMMMMMMMMMMMMMMM", t: "WWWWWWWWWW WWWWWWWWWW WWWWWWWWWW WWWWWWWWWW message number " + string(_i), pid: 3 }, true);')
for variant, extra in (('recent', ''), ('typing', 'kfo_chat_s().typ = true; kfo_chat_s().buf = "hello everyone, this is a long line being typed";'),
                       ('expanded', 'kfo_chat_s().typ = true; kfo_chat_s().exp = true;'),
                       ('flowery', 'var _c = kbr_tl_get(_M.tl, 7); _c.reg = kbr_enc_by_key("flowery").lu; _c.ok = 8; _M.flg = 45;'),
                       ('warn', '_M.vw.lst_t = 1; global.kfo.t_newhost = current_time; global.kfo.newhost_n = "WWWWWWWWWWWW";')):
    sim, rec = br_frame('t_busy_' + variant, n=8, out=(6, 7), render=False, pre=BUSY + extra)
    sim.mock('kbr_soul_mode', lambda *a: 'yellow')
    rec.ops.clear()
    rec.ops.append(('rect', 0, 0, 640, 480, 0, 1.0, False))
    sim.run('draw_set_color(c_black); draw_rectangle(0, 328, 640, 480, false); draw_set_color(c_white); knight_ui_draw_panel(0, 0, 40); kbr_hud_draw(0, 0);')
    B = hud_check('hud busy %s' % variant, rec, 8, sim=sim)
    txt = ' '.join(b[4] for b in B)
    ok('YELLOW SOUL' in txt or variant == 'flowery', 'hud busy %s: the SOUL hint is shown (under the box)' % variant)
    ok('TARGETED BY 2' in txt, 'hud busy %s: the incoming list is shown' % variant)
    if variant == 'flowery':
        ok('MERCY 45%' in txt, 'hud busy flowery: Flowery\'s MERCY bar is on the stack')
    if variant == 'warn':
        ok('NEW HOST: WWWWWWWWWWWW' in txt, 'hud busy warn: the network warning over the SOULS header (%s)' % txt[:300])
    else:
        ok('230MS POOR' in txt or '~230MS POOR' in txt, 'hud busy %s: NETWORK STATS beside the network light' % variant)
    if SHOTS:
        rec.render('/home/claude/work/uishots/online_hud_busy_%s.png' % variant)

# the HUD with long key names (KEYBINDS): the countdown's key lines and the OUT line fit, nothing over the box
for variant in ('countdown', 'out_watch'):
    kw = {'n': 8, 'out': (6, 7), 'render': False}
    if variant == 'countdown':
        kw.update(ph='idle', k=0, tick=40)
    else:
        kw.update(me_out=True, spect=2)
    sim, rec = br_frame('t_keys_%s' % variant, **kw)
    sim.run('kfo_key_set("breath", 20); kfo_key_set("use", 34); kfo_key_set("charge", 220); kfo_key_set("hold", 111); kfo_key_set("list", 162); kfo_key_set("quit", 93);')
    rec.ops.clear()
    rec.ops.append(('rect', 0, 0, 640, 480, 0, 1.0, False))
    sim.run('draw_set_color(c_black); draw_rectangle(0, 328, 640, 480, false); draw_set_color(c_white); kbr_hud_draw(0, 0);')
    B = hud_check('hud long keys %s' % variant, rec, 8, sim=sim)
    txt = ' '.join(b[4] for b in B)
    if variant == 'countdown':
        ok('CAPS LOCK: HOLD BREATH' in txt and 'PAGE DOWN: TAP = NEXT SKILL' in txt, 'the countdown shows the player\'s keys (%s)' % txt[:200])
    else:
        ok('KEY 93' in txt or 'KEY 93' in sim.py(sim.eval('kfo_key_label("quit")')), 'the watching HUD knows the player\'s keys (%s)' % txt[:200])
    if SHOTS:
        rec.render('/home/claude/work/uishots/online_hud_keys_%s.png' % variant)
# the picked skill: the yellow frame and the USE key under it move with the pick
sim, rec = br_frame('t_pick', n=4, out=(), render=False)
# build 51: the diamonds - the picked one has the yellow frame and its name is written under the row
for sel, nm in ((0, 'MAX'), (1, 'Knightmare'), (2, 'Shield')):
    sim.run('global.kfo.M.sk.sel = %d;' % sel)
    rec.ops.clear()
    sim.run('kbr_hud_draw(0, 0);')
    names = [o[4] for o in rec.ops if o[0] == 'text' and o[4] == nm and o[10] != 0]
    cx = 14 + 23 + sel * 27
    yl = [o for o in rec.ops if o[0] == 'line' and o[5] == 65535 and abs(min(o[1], o[3]) - (cx - 26)) <= 2]
    ok(len(names) == 1 and len(yl) >= 1, 'the picked slot %d: its name (%r) and the yellow frame (%d lines)' % (sel, names, len(yl)))
# the longest attack name of every online knight fits its line
sim, rec = br_frame('t_names', render=False)
sim.run('global.AW = []; draw_set_font(fnt_small); for (var _ok = 0; _ok < 6; _ok++) { var _l = knight_reg(kbr_reg_of(_ok)).atk;'
        ' for (var _i = 0; _i < array_length(_l); _i++) array_push(global.AW, [_ok, _l[_i][2], string_width(kbr_fit(string_upper(_l[_i][2]), 192))]); }')
aw = sim.py(sim.eval('global.AW'))
ok(all(a[2] <= 192 for a in aw), 'every attack name is fitted to 192 px (%r)' % [a for a in aw if a[2] > 192][:3])
ok(len(aw) > 60, 'attack names checked (%d)' % len(aw))
# the banners (big font) under the box: fitted to the screen
sim.run('global.BW = []; scr_84_set_draw_font("mainbig"); for (var _ok = 0; _ok < 6; _ok++) array_push(global.BW, string_width(string_upper(kbr_ok_name(_ok)) + " STEPS IN!"));'
        'array_push(global.BW, string_width("STAGE 4: " + kfo_stage_banner(4)), string_width("YOU ARE OUT - WATCHING"), string_width("FINAL TWO!"), string_width("sudden death!!"));')
bw = sim.py(sim.eval('global.BW'))
ok(max(bw) <= 600, 'every battle banner fits in one line (%r)' % bw)

# ---------------------------------------------------------------- result / out / lost boxes
sim, rec = br_frame('t_boxes', n=8, out=(5, 6, 7), render=False)
for name, code in (('out', 'knight_modal_draw(kfo_out_title(), kfo_standing_lines(8), [{t: "Back to the room", a: ""}], 0, "");'),
                   ('results', 'global.kfo.M.res = { wid: [2], wn: "WWWWWWWWWWWW", sn: 8, ticks: 9000, pl: [] }; for (var _i = 0; _i < 8; _i++) array_push(global.kfo.M.res.pl,'
                               ' { pid: _i + 2, n: "MMMMMMMMMMMM", pl: _i + 1, al: (_i == 0), ft: 9000 - _i * 300, hits: 12, sg: 12, sr: 9, tk: 900, hl: 300 });'
                               ' global.kfo.M.out_why = "a hit from SPAMTON NEO\'s Mail Wall emptied your HP";'
                               ' knight_modal_draw(kfo_result_title(), kfo_result_lines(), [{t: "Back to the room", a: ""}, {t: "Leave the room", a: ""}], 0, "");'),
                   ('lost', 'knight_modal_draw("CONNECTION LOST", ["The host stopped answering.", "The match goes on without you."], [{t: "Back to the hub", a: ""}], 0, "");'),
                   ('giveup', 'knight_modal_draw("GIVE UP?", ["You will be OUT of this match and go back to the room."], [{t: "Keep fighting", a: ""}, {t: "Give up", a: ""}], 0, "");')):
    rec.ops.clear()
    sim.run(code)
    check('box ' + name, rec, modal=True)
    if SHOTS:
        rec.render('/home/claude/work/uishots/online_box_%s.png' % name)

# ---------------------------------------------------------------- the cold place: the room box and the name tags
for n in (1, 4, 8):
    for who in ('host', 'player'):
        sim, rec = setup()
        room(sim, n, me=(2 if (who == 'player' and n > 1) else 1))
        sim.run('global.kfo.ows = {}; for (var _i = 2; _i <= %d; _i++) variable_struct_set(global.kfo.ows, string(_i), { x: 100 + _i * 50, y: 200 + (_i mod 3) * 40,'
                ' px: 100 + _i * 50, py: 200 + (_i mod 3) * 40, t: current_time, pt: current_time - 100, f: 0, s: 1 + (_i mod 4), mv: 1, rm: room });' % n)
        rec.ops.clear()
        sim.run('kfo_world_box(0, 0);')
        check('cold place box n%d %s' % (n, who), rec, body=False, min_ops=3, within=(6, 6, 242, 62))
        if SHOTS and n == 8:
            rec.render('/home/claude/work/uishots/online_world_%s.png' % who)

# ---------------------------------------------------------------- real input through the pages
sim, rec = setup()


def frame():
    sim.run('knight_ui_step(); kfo_tick();')
    rec.ops.clear()
    sim.run('knight_ui_draw();')


def press(k, n=1):
    for _ in range(n):
        for kk in sim.inp:
            sim.inp[kk] = 0
        sim.inp[k] = 1
        frame()
        sim.inp[k] = 0
        frame()
        if sim.eval('is_struct(global.knight_ui) && is_struct(global.knight_ui.modal)'):
            frame()
            frame()


for _ in range(10):
    frame()
# DRBR 1.0.1: the menu opens on the ONLINE page (the first button): X from its menu goes back up to the top bar; RIGHT is the KNIGHT page
eq(sim.eval('global.knight_ui.tab'), 5, 'the menu opens on ONLINE')
press('ok')
eq(sim.eval('global.knight_ui.sub'), 'online', 'Z on ONLINE opens its menu')
press('back')
ok(sim.eval('global.knight_ui.sub') == '' and sim.eval('global.knight_ui.focus') == 0 and sim.eval('global.knight_ui.tab') == 5, 'X: back up to the top bar, on ONLINE')
press('right')
eq(sim.eval('global.knight_ui.tab'), 0, 'RIGHT from ONLINE: KNIGHT')
press('left')
eq(sim.eval('global.knight_ui.tab'), 5, 'LEFT back to ONLINE')
press('left')
eq(sim.eval('global.knight_ui.tab'), 4, 'LEFT from ONLINE wraps round to CONFIG')
press('right')
press('ok')
eq(sim.eval('global.knight_ui.sub'), 'online', 'Z opens the ONLINE page')
# build 51: HOW TO PLAY, PRACTICE, (DRBR: BOSSES,) HOST A ROOM, JOIN WITH CODE, FIND ROOMS, NAME, SKIN, MORE... (relay + SETTINGS under it)
eq(sim.py(sim.eval('kfo_ui_rows()')), ['howto', 'practice', 'bosses', 's_host', 's_join', 's_browse', 'name', 'skin', 'more'], 'the ONLINE page\'s rows (DRBR: BOSSES after PRACTICE)')
press('down', 7)
eq(sim.eval('global.knight_ui.onl_row'), 7, 'cursor on SKIN')
s0 = sim.eval('global.kfo.skin')
press('right')
eq(sim.eval('global.kfo.skin'), s0 % sim.eval('kfo_skin_count()') + 1, 'right changes the skin (build 52: 7 skins)')
press('down')
press('ok')
eq(sim.py(sim.eval('kfo_ui_rows()'))[9:], ['d_create', 'd_join', 'd_lan', 'opts'], 'build 51: MORE... unfolds the relay rows and SETTINGS')
press('down', 4)
press('ok')
eq(sim.eval('global.knight_ui.sub'), 'onl_opt', 'SETTINGS (the old MORE OPTIONS) opens')
press('down', 2)
press('ok')
eq(sim.eval('global.knight_ui.sub'), 'onl_view', 'SOUL SETTINGS opens from MORE OPTIONS')
s0 = sim.eval('global.kfo.view.show')
press('right')
eq(sim.eval('global.kfo.view.show'), 1 - s0, 'SHOW OTHER SOULS switches')
press('down')
c0 = sim.eval('global.kfo.look.col')
press('right')
ok(sim.eval('global.kfo.look.col') != c0, 'SOUL COLOR: right gives the next preset colour (%s -> %s)' % (c0, sim.eval('global.kfo.look.col')))
press('ok')
eq(sim.eval('global.knight_ui.sub'), 'onl_look', 'SOUL COLOR: Z opens the colour page')
press('back')
eq((sim.eval('global.knight_ui.sub'), sim.eval('global.knight_ui.pg_row')), ('onl_view', 1), 'X back to SOUL SETTINGS, on SOUL COLOR')
press('down', 2)
o0 = sim.eval('global.kfo.view.sop')
press('left')
eq(sim.eval('global.kfo.view.sop'), o0 - 5, 'OPACITY - 5')
press('back')
eq(sim.eval('global.knight_ui.sub'), 'onl_opt', 'X back to MORE OPTIONS')
press('back')
eq(sim.eval('global.knight_ui.sub'), 'online', 'X back to ONLINE')
sim.run('global.KS = global.kfo; global.kfo = undefined; kfo_get();')
eq(sim.eval('global.kfo.view.sop'), o0 - 5, 'the opacity was saved (a restarted game reads it)')
sim.run('global.kfo = global.KS;')
eq(sim.eval('global.knight_ui.onl_row'), 12, 'the cursor is still on SETTINGS')
press('down', 4)
eq(sim.eval('global.knight_ui.onl_row'), 3, 'down wraps round to HOST A ROOM')
sim.run('global.kfo_stm = { ok: false, init: -1, why: "Steam is not running or not signed in.", fns: {}, dll: "kf_steam.dll" };')
press('ok')
eq(sim.eval('global.knight_ui.sub'), 'online', 'STEAM HOST without Steam stays on the page')
ok('Steam' in sim.eval('global.knight_ui.warn'), 'STEAM HOST without Steam says why (%s)' % sim.eval('global.knight_ui.warn'))
ok(sim.eval('global.kfo.st') != 'room', 'STEAM HOST without Steam makes no room')
press('up', 2)
press('ok')
eq(sim.eval('global.kfo.st'), 'room', 'PRACTICE: in a practice room at once')
frame()
frame()
eq(sim.eval('global.knight_ui.sub'), 'lobby', 'the page turns into the room')
eq(sim.eval('array_length(kfo_lobby_players())'), 1 + sim.eval('global.kfo.H.set.bots'), 'me and the bots')
rows = sim.py(sim.eval('kfo_ui_lobby_rows()'))
press('down', rows.index('settings'))
press('ok')
eq(sim.eval('global.knight_ui.sub'), 'onl_set', 'SETTINGS opens')
press('ok')
eq(sim.eval('global.knight_ui.set_focus'), 1, 'Z goes into the GENERAL settings')
items = sim.py(sim.eval('kfo_ui_set_items(0)'))
b0 = sim.eval('global.kfo.H.set.bots')
press('down', items.index('bots'))
press('right')
eq(sim.eval('global.kfo.H.set.bots'), min(7, b0 + 1), 'BOTS + 1')
frame()
frame()
eq(sim.eval('array_length(kfo_lobby_players())'), 1 + min(7, b0 + 1), 'one more bot in the room')
press('back')
press('down')
press('ok')
press('down')   # (build 52: ENCOUNTERS is the page's first row, the Normal Knight's row the next)
press('ok')
ok(sim.py(sim.eval('global.kfo.H.set.kn')) == [1, 2, 3, 4, 5], 'Z switches the Normal Knight out (%s)' % sim.py(sim.eval('global.kfo.H.set.kn')))
eq(sim.eval('global.kfo.H.set.open'), 1, 'the opening knight moves to one that is in')
eq(sim.eval('global.kfo.H.set.pre'), 'CUSTOM', 'a changed preset is CUSTOM')
press('back')
press('down', 8)
eq(sim.eval('global.knight_ui.set_row'), 9, 'PRESETS is the last page (build 52: after ADVANCED)')
press('ok')
press('down', 4)
press('ok')
eq(sim.eval('global.kfo.H.set.pre'), 'KNIGHT RUSH', 'Z loads the KNIGHT RUSH preset')
eq(sim.eval('global.kfo.H.set.rush'), 1, 'the preset is really in use (KNIGHT RUSH switching)')
press('back')
press('back')
eq(sim.eval('global.knight_ui.sub'), 'lobby', 'X back to the room')
sim.mock('knight_launch_go', lambda s: 0)
press('alt')
frame()
frame()
eq(sim.eval('global.kfo.H.st'), 'match', 'C starts the practice match')
eq(sim.eval('global.knight_ui.go'), 1, 'the menu fades into the fight')
# leave: through the box
sim2, rec2 = setup()
sim, rec = sim2, rec2
for _ in range(4):
    frame()
sim.run('kfo_practice_start(); global.knight_ui.tab = 5; global.knight_ui.focus = 1; global.knight_ui.sub = "lobby";')
frame()
frame()
rows = sim.py(sim.eval('kfo_ui_lobby_rows()'))
press('down', rows.index('leave'))
press('ok')
eq(sim.eval('global.knight_ui.modal.k'), 'kfo_leave', 'LEAVE ROOM asks first')
press('right')
press('ok')
ok(not sim.eval('kfo_in_room()') and sim.eval('global.knight_ui.sub') == 'online', 'Leave: out of the room, on the ONLINE page')
# typing a name (the cursor put on NAME: the row the page left it on depends on where it was)
sim.run('global.knight_ui.onl_row = %d;' % sim.py(sim.eval('kfo_ui_rows()')).index('name'))
press('ok')
eq(sim.eval('global.knight_ui.modal.k'), 'kfo_text', 'NAME opens the typing box')
sim.run('keyboard_string = "  New  Name\\"x  ";')
frame()
sim.press('enter')
sim.step(1)
frame()
eq(sim.eval('global.kfo.name'), 'New Namex', 'typed name cleaned and kept')
# closing the menu keeps the room (the cold place is the room's lobby); practice ends with the menu
sim.run('kfo_practice_start();')
sim.run('knight_menu_finish_close();')
ok(not sim.eval('kfo_in_room()'), 'closing the menu ends a PRACTICE room')

# DRBR: the SKINS page's keys (the input section's game): < > a group, up / down a skin, Z wears it and goes back, X goes back
sim.run('global.kfo.skin = 1; global.knight_ui.sub = "online"; kfo_ui_skin_open("online");')
press('right')
eq(sim.py(sim.eval('[global.knight_ui.sk_cat, global.knight_ui.sk_i]')), [1, 0], 'SKINS: > goes to FLOWERS, its first skin')
press('down', 2)
eq(sim.eval('kfo_ui_skin_hot()'), 8, 'SKINS: two down is Seth')
press('ok')
eq((sim.eval('global.kfo.skin'), sim.eval('global.knight_ui.sub')), (8, 'online'), 'SKINS: Z wears Seth and goes back to ONLINE')
sim.run('kfo_ui_skin_open("online");')
press('left')
press('back')
eq((sim.eval('global.kfo.skin'), sim.eval('global.knight_ui.sub')), (8, 'online'), 'SKINS: X goes back without changing the skin')
sim.run('global.kfo.skin = 1; kfo_ini_save();')
# DRBR: the mouse wheel moves through a list like UP / DOWN (the SKINS list here, then the ONLINE page's rows)
sim.run('kfo_ui_skin_open("online");')
frame()
i0 = sim.eval('global.knight_ui.sk_i')
sim.input.wheel_down = 1
frame()
sim.input.wheel_down = 0
frame()
eq(sim.eval('global.knight_ui.sk_i'), i0 + 1, 'the wheel down moves one skin down')
sim.input.wheel_up = 1
frame()
sim.input.wheel_up = 0
frame()
eq(sim.eval('global.knight_ui.sk_i'), i0, 'the wheel up moves one skin up')
press('back')

print('online ui: %d checks, %d failed%s' % (N[0], len(FAILS), (', %d shots' % nshot[0]) if SHOTS else ''))
# DRBR: the BOSSES page's keys: from the ONLINE page, > to the BOSSES group, down to Gerson, Z: a practice room against him alone
# (your saved settings unchanged); in that room (the host) Z puts Jevil in and takes him out again; a player is told the host does it
sim, rec = setup()
for _ in range(4):
    frame()
sim.run('global.knight_ui.tab = 5; global.knight_ui.focus = 1; global.knight_ui.sub = "online"; global.knight_ui.onl_row = 2;')
frame()
saved_kn = sim.py(sim.eval('kfo_set_clean(global.kfo.set).kn'))
press('ok')
eq(sim.eval('global.knight_ui.sub'), 'onl_boss', 'BOSSES: Z on the ONLINE page\'s BOSSES row opens it')
press('right')
press('down')
eq(sim.eval('kfo_ui_boss_hot()'), 7, 'BOSSES: > then down is Gerson')
press('ok')
frame()
eq((sim.eval('global.kfo.st'), sim.eval('global.knight_ui.sub')), ('room', 'lobby'), 'BOSSES: Z starts a practice room (the room page)')
eq(sim.py(sim.eval('global.kfo.H.set.kn')), [7], 'BOSSES: the practice room fights Gerson alone')
eq(sim.eval('global.kfo.H.set.open'), 7, 'BOSSES: Gerson opens it')
eq(sim.py(sim.eval('kfo_set_clean(global.kfo.set).kn')), saved_kn, 'BOSSES: your saved room settings are unchanged')
rows = sim.py(sim.eval('kfo_ui_lobby_rows()'))
ok('bosses' in rows, 'the room has a BOSSES row (%r)' % rows)
sim.run('global.knight_ui.lob_row = %d;' % rows.index('bosses'))
frame()
press('ok')
eq(sim.eval('global.knight_ui.sub'), 'onl_boss', 'BOSSES: the room\'s row opens it')
sim.run('global.knight_ui.bs_cat = 1; global.knight_ui.bs_i = 0;')
frame()
press('ok')
frame()
eq(sim.py(sim.eval('global.kfo.H.set.kn')), [6, 7], 'BOSSES: the host\'s Z puts Jevil in the room')
press('ok')
frame()
eq(sim.py(sim.eval('global.kfo.H.set.kn')), [7], 'BOSSES: Z again takes him out')
sim.run('global.knight_ui.bs_i = 1;')
frame()
press('ok')
ok(sim.py(sim.eval('global.kfo.H.set.kn')) == [7] and 'stay' in sim.eval('global.knight_ui.warn'), 'BOSSES: the last boss stays in (%s)' % sim.eval('global.knight_ui.warn'))
press('back')
eq(sim.eval('global.knight_ui.sub'), 'lobby', 'BOSSES: X back to the room')
sim.run('kfo_practice_start(); knight_menu_finish_close();')

# every failure (only the first 80 are printed above)
open('/home/claude/work/tests/logs53/ui47_fails.txt', 'w').write('\n'.join(FAILS) + '\n')
sys.exit(1 if FAILS else 0)
