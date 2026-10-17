"""Layout check of every hub screen with the game's real font metrics (uiharness): every text stays on screen, menu-body text
stays inside the box, no two texts overlap, the top-bar description fits its two lines, and something is drawn."""
import sys, itertools
sys.path.insert(0, '/home/claude/work/uiref')
from uiharness import *
import gmrender as G
FAILS = []; N = [0]
def ok(c, msg):
    N[0] += 1
    if not c:
        FAILS.append(msg)
        if len(FAILS) < 40: print('FAIL', msg)

def setup():
    sim, rec = menu_sim()
    sim.run('knight_menu_open();')
    sim.step(1)
    sim.run('global.knight_ui.tp = 80; global.knight_ui.bp = 60; global.knight_ui.inputdelay = 0; global.knight_ui.notice = "";')
    return sim, rec

def boxes(rec, modal=False):
    out = []
    ops = rec.ops
    if modal:
        # only what is drawn on top of the modal box (the menu behind it is dimmed and covered)
        last = max([i for i, o in enumerate(ops) if o[0] == 'darkbox'] or [0])
        ops = ops[last:]
    for o in ops:
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

def check(name, rec, body=True, modal=False):
    B = boxes(rec, modal)
    ok(len(rec.ops) > 10, '%s: something is drawn' % name)
    for (x0, y0, x1, y1, t, fnt) in B:
        ok(x0 >= -1 and x1 <= 641 and y0 >= -2 and y1 <= 482, '%s: "%s" off screen (%.0f,%.0f)-(%.0f,%.0f)' % (name, t, x0, y0, x1, y1))
        # DRBR: the frame's inside measured on a render (scr_darkbox(50, 80, 590, 420)): x 64-576, the bottom border from y 407
        if body and not modal and 88 <= y0 <= 400:
            ok(x0 >= 63 and x1 <= 577 and y1 <= 406, '%s: "%s" leaves the box (%.0f,%.0f)-(%.0f,%.0f)' % (name, t, x0, y0, x1, y1))
    # the menu's heart inside the frame too (16x16, origin top left)
    if body and not modal:
        for o in rec.ops:
            if o[0] == 'spr' and o[1] == 'spr_heart' and 88 <= o[4] <= 400:
                ok(o[3] >= 63 and o[3] + 16 <= 577, '%s: the heart leaves the frame (x %.0f)' % (name, o[3]))
    # overlaps (same draw order layer); tiny touches allowed
    for a, b in itertools.combinations(B, 2):
        ix = min(a[2], b[2]) - max(a[0], b[0])
        iy = min(a[3], b[3]) - max(a[1], b[1])
        if ix > 3 and iy > 3:
            ok(False, '%s: "%s" overlaps "%s"' % (name, a[4][:30], b[4][:30]))

U = 'global.knight_ui'
def state(code):
    sim, rec = setup()
    sim.run(code.replace('U.', U + '.'))
    rec.ops.clear()
    sim.run('knight_ui_draw();')
    return sim, rec

n_states = 0
# KNIGHT tab
for focus in (0, 1):
    for row in range(11):
        sim, rec = state('U.tab=0; U.focus=%d; U.krow=%d;' % (focus, row)); n_states += 1
        check('knight f%d r%d' % (focus, row), rec)
        if focus:
            ok(sim.eval('array_length(knight_wrap(knight_ui_desc(), 600))') <= 2, 'knight r%d: description fits two lines' % row)
# PARTY tab: every slot x level x row, with each member in slot 0
for member in (1, 2, 3, 4):
    for lv in (0, 1, 2):
        for row in range(3):
            for pick in ((0, 3, 7) if lv == 2 else (0,)):
                sim, rec = state('global.knight_cfg.party=[%d,2,3]; U.tab=1; U.focus=1; U.pslot=0; U.lv=%d; U.prow=%d; U.ppick=%d; U.pscroll=max(0, %d-5);' % (member, lv, row, pick, pick)); n_states += 1
                check('party m%d lv%d r%d p%d' % (member, lv, row, pick), rec)
                ok(sim.eval('array_length(knight_wrap(knight_ui_desc(), 600))') <= 2, 'party m%d lv%d r%d: description fits' % (member, lv, row))
# POWER tab
for member in (1, 2, 3, 4):
    for lv in (0, 1):
        for row in ((0, 5, 11) if lv else (0,)):
            sim, rec = state('global.knight_cfg.party=[%d,2,3]; U.tab=2; U.focus=1; U.sslot=0; U.lv=%d; U.srow=%d; U.sscroll=clamp(%d-5,0,6);' % (member, lv, row, row)); n_states += 1
            check('power m%d lv%d r%d' % (member, lv, row), rec)
            ok(sim.eval('array_length(knight_wrap(knight_ui_desc(), 600))') <= 2, 'power m%d lv%d r%d: description fits' % (member, lv, row))
# RULES tab, each row, all on
for row in range(16):
    for allon in (0, 1):
        on = ''.join('global.knight_cfg.%s=1; ' % r for r in ('c_nohit', 'c_items', 'c_heal', 'c_hp1', 'c_dmg2', 'c_halfhp', 'c_notp', 'c_twin', 'c_dark', 'c_speed', 'c_thorns', 'c_time')) if allon else ''
        sim, rec = state(on + 'U.tab=3; U.focus=1; U.rrow=%d;' % row); n_states += 1
        check('rules r%d on%d' % (row, allon), rec)
        ok(sim.eval('array_length(knight_wrap(knight_ui_desc(), 600))') <= 2, 'rules r%d: description fits' % row)
# CONFIG tab (build 41: 13 rows; PRACTICE shows its attack in each setting)
sim0c, _ = setup()
for row in range(sim0c.eval('array_length(knight_ui_cfg_ids())')):
    sim, rec = state('U.tab=4; U.focus=1; U.crow=%d;' % row); n_states += 1
    check('config r%d' % row, rec)
    ok(sim.eval('array_length(knight_wrap(knight_ui_desc(), 600))') <= 2, 'config r%d: description fits' % row)
for pm in ('global.knight_cfg.practice=1;', 'global.knight_cfg.p_mode=1; global.knight_cfg.p_atk=19;', 'global.knight_cfg.p_mode=2; global.knight_cfg.p_atk=20;'):
    sim, rec = state(pm + 'U.tab=4; U.focus=1; U.crow=3;'); n_states += 1
    check('config practice %s' % pm[:30], rec)
# build 41: TAG TEAM picker (every row, both slots, a joke knight in the team) and every knight's attack list
for row in range(7):
    for slot in (0, 1):
        for pair in ((0, 4), (5, 3)):
            sim, rec = state('global.knight_cfg.combo=1; global.knight_cfg.knight=%d; global.knight_cfg.knight2=%d; U.tab=0; U.focus=1; U.krow=8; U.sub="tag"; U.tag_row=%d; U.tag_slot=%d;' % (pair[0], pair[1], row, slot)); n_states += 1
            check('tag r%d s%d %s' % (row, slot, pair), rec)
            ok(sim.eval('array_length(knight_wrap(knight_ui_desc(), 600))') <= 2, 'tag r%d: description fits' % row)
# build 42: the ATTACK REMIX picker (every row; all on, a few on, one on) and the KNIGHT page card with knights switched off
for row in range(6):
    for mask in (31, 18, 8, 1):
        sim, rec = state('global.knight_cfg.combo=2; global.knight_cfg.rmask=%d; U.tab=0; U.focus=1; U.krow=9; U.sub="remix"; U.rmx_row=%d;' % (mask, row)); n_states += 1
        check('remix r%d m%d' % (row, mask), rec)
        ok(sim.eval('array_length(knight_wrap(knight_ui_desc(), 600))') <= 2, 'remix r%d m%d: description fits' % (row, mask))
for mask in (31, 18, 1):
    sim, rec = state('global.knight_cfg.combo=2; global.knight_cfg.rmask=%d; U.tab=0; U.focus=1; U.krow=9;' % mask); n_states += 1
    check('knight card remix m%d' % mask, rec)
for k in range(6):
    n = sim0c.eval('array_length(knight_reg(%d).atk)' % k)
    for row in sorted({0, n // 2, n - 1}):
        for pm in (0, 2, 3):
            sim, rec = state('global.knight_cfg.knight=%d; knight_ui_practice_set(global.knight_cfg, %d); global.knight_cfg.p_atk=%d; U.tab=4; U.focus=1; U.crow=3; U.sub="attacks"; U.at_row=%d; U.at_scroll=clamp(%d-4,0,max(0,%d-9));' % (k, pm, row, row, row, n)); n_states += 1
            check('attacks k%d r%d m%d' % (k, row, pm), rec)
            ok(sim.eval('array_length(knight_wrap(knight_ui_desc(), 600))') <= 2, 'attacks k%d r%d: description fits' % (k, row))
# sub pages
for r in range(8):
    sim, rec = state('U.tab=4; U.focus=1; U.sub="presets"; U.subrow=%d;' % r); n_states += 1
    check('presets %d' % r, rec)
sim0, _ = setup()
# loadouts: every group and row, and its confirm box
for g in range(sim0.eval('knight_lo_group_count()')):
    for i in range(sim0.eval('array_length(knight_lo_list(%d))' % g)):
        sim, rec = state('U.tab=4; U.focus=1; U.sub="loadouts"; U.lo_g=%d; U.lo_i=%d;' % (g, i)); n_states += 1
        check('loadouts %d/%d' % (g, i), rec)
        ok(sim.eval('array_length(knight_wrap(knight_ui_desc(), 600))') <= 2, 'loadouts %d/%d: description fits' % (g, i))
sim, rec = state('U.tab=4; U.focus=1; U.sub="loadouts"; U.lo_g=0; U.lo_i=1; knight_ui_step_loadouts(false, false, false, false, true);'); n_states += 1
check('loadout confirm', rec, modal=True)
nk = sim0.eval('array_length(knight_rec_keys())')
for i in range(nk):
    for d in ('false', 'true'):
        sim, rec = state('U.tab=4; U.focus=1; U.sub="records"; U.rec_i=%d; U.rec_def=%s;' % (i, d)); n_states += 1
        check('records %d %s' % (i, d), rec)
nc = sim0.eval('knight_credit_count()')
for i in range(nc):
    pages = sim0.eval('knight_credit_pages(%d)' % i)
    for p in range(pages):
        sim, rec = state('U.tab=4; U.focus=1; U.sub="credits"; U.cr_i=%d; U.cr_page=%d;' % (i, p)); n_states += 1
        check('credits %d p%d' % (i, p), rec)
# modals: START for every fight with rules, errors
for k in range(10):
    sim, rec = state('global.knight_cfg.c_twin=1; global.knight_cfg.c_time=1; global.knight_cfg.c_dark=1; global.knight_cfg.weird=1; U.tab=0; U.focus=1; U.krow=%d; knight_ui_fight_select(knight_ui_fights()[%d]); knight_ui_try_go();' % (k, k)); n_states += 1
    check('start %d' % k, rec, modal=True)
for pm in ('global.knight_cfg.p_mode=1; global.knight_cfg.p_atk=14;', 'global.knight_cfg.p_mode=2; global.knight_cfg.p_atk=19;'):
    sim, rec = state(pm + 'global.knight_cfg.knight=2; U.tab=0; U.focus=1; U.krow=2; knight_ui_try_go();'); n_states += 1
    check('start practice %s' % pm[:28], rec, modal=True)
sim, rec = state('U.tab=0; U.focus=1; global.knight_cfg.party=[0,0,0]; knight_ui_try_go();'); n_states += 1
check('errors', rec, modal=True)
# results boxes (prompt drawing)
for title, lines, opts in [
    ('KNIGHT DEFEATED!', '[["^", "SUPERCHARGED KNIGHT", c_yellow], ["Battle time", "14:31.2", ""], ["Damage taken", "1312", ""], ["Hits taken", "29", ""], ["^", "NEW BEST TIME!  LEAST DAMAGE!", c_yellow], ["~", "Practice: attempts only, no clears."]]', 5),
    ('KNIGHT RUSH COMPLETE!', '[["1. NORMAL", "13:10.0", "1120 dmg"], ["2. KAIZO", "16:41.3", "4021 dmg"], ["3. SUPERCHARGED", "14:55.9", "2500 dmg"], ["4. VIOLET", "17:12.4", "3900 dmg"], ["5. THORN", "15:20.1", "3100 dmg"], ["CLEARED 5/5", "77:19.7", "14720 dmg", true], ["^", "FIRST CLEAR!", c_yellow]]', 4),
    ('TIME UP', '[["^", "VIOLET KNIGHT", c_purple], ["Battle time", "9:02.5", ""], ["Damage taken", "480", ""], ["Hits taken", "11", ""], ["~", "The knight was still standing after 32 turns."]]', 4)]:
    sim, rec = setup()
    o = ', '.join('{t: "Option %d", a: ""}' % i for i in range(opts))
    rec.ops.clear(); sim.run('knight_modal_draw("%s", %s, [%s], 0, "NEXT FIGHT...");' % (title, lines, o)); n_states += 1
    check('result %s' % title, rec, modal=True)
# build 41: the results box with every option and the FIGHT STATS box (8 attacks, long names, three members + Other)
sim, rec = setup()
rec.ops.clear(); sim.run('knight_modal_draw("BOTH KNIGHTS DEFEATED!", [["^", "TAG TEAM: SUPERCHARGED + VIOLET", c_yellow], ["Battle time", "24:31.2", ""], ["Damage taken", "2312", ""], ["Hits taken", "49", ""], ["^", "NEW BEST TIME!  LEAST DAMAGE!", c_yellow], ["~", "With a joke fight in it, this Tag Team is not recorded."]], [{t: "Rematch", a: ""}, {t: "Reroll", a: ""}, {t: "Fight stats", a: ""}, {t: "Change settings", a: ""}, {t: "Return to Hub", a: ""}], 0, "");'); n_states += 1
check('result tag', rec, modal=True)
sim, rec = setup()
sim.run('global.SR = { party: [1, 3, 4], st: knight_stats_new() }; global.SR.st.dealt = [120, 8000, 0, 2400, 950]; global.SR.st.taken = [0, 310, 0, 1200, 44]; global.SR.st.turns = 31;'
        'var _nm = ["SUPERCHARGED: Spinning Slashes (Phase 4)", "VIOLET: Crescent Slash 2", "KAIZO: Piercing Blades", "THORN: Lightsplitter", "NORMAL: Combination Attack (unused)", "CYAN: Spinning Slashes 2", "KAIZO: Evil and Fucked Up Tunnel 2", "ELEC: Box Cluster", "VIOLET: Diamond Eruption", "THORN: Quickstorm"];'
        'for (var _i = 0; _i < 10; _i++) array_push(global.SR.st.atk, { n: _nm[_i], seen: _i + 1, hits: (_i * 7) mod 4 });')
for page in (0, 1):
    sim.run('global.SR.st.page = %d;' % page)
    rec.ops.clear(); sim.run('knight_modal_draw("FIGHT STATS", knight_stats_lines(global.SR), [{t: "Back", a: ""}, {t: "Next page", a: ""}], 0, "");'); n_states += 1
    check('stats page %d' % page, rec, modal=True)
    B = boxes(rec, True)
    ok(max(b[3] for b in B) < 472, 'stats page %d: everything above the bottom of the screen' % page)
# the in-battle lineup HUD (two bars + a banner; the Remix bar)
for kind in ('tag', 'remix'):
    sim, rec = setup()
    sim.run('var _c = knight_cfg_default(); _c.combo = %d; _c.knight = 2; _c.knight2 = 3; _c.c_time = 1; _c.c_twin = 0; global.knight_run = 1;'
            'global.krun = knight_run_new({ src: _c, cfg: _c, plan: [2], reveal: "", corr: [] }); global.krun.state = "battle"; global.krun.tlimit = 40; global.krun.eturns = 3;'
            'knight_lu_new(global.krun); global.knight_lu.ready = true; global.knight_lu.slot[1] = { hp: 3000, maxhp: 6000 };'
            'global.monsterhp = [5000, 0, 0]; global.monstermaxhp = [7300, 0, 0]; knight_lu_banner("SUPERCHARGED KNIGHT IS DOWN!  VIOLET KNIGHT TAKES OVER!");' % (1 if kind == 'tag' else 2))
    rec.ops.clear(); sim.run('knight_hud_draw();'); n_states += 1
    B = boxes(rec, False)
    ok(len(B) >= 2, 'hud %s: drawn' % kind)
    for (x0, y0, x1, y1, t, fnt) in B:
        ok(x0 >= -1 and x1 <= 641 and y0 >= -2 and y1 <= 482, 'hud %s: "%s" off screen' % (kind, t))
    for a, b in itertools.combinations(B, 2):
        ix = min(a[2], b[2]) - max(a[0], b[0]); iy = min(a[3], b[3]) - max(a[1], b[1])
        if ix > 3 and iy > 3 and a[4] != b[4]:
            ok(False, 'hud %s: "%s" overlaps "%s"' % (kind, a[4][:30], b[4][:30]))
print('layout states', n_states, 'checks', N[0], 'fails', len(FAILS)); sys.exit(1 if FAILS else 0)
