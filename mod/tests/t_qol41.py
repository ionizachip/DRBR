"""Build 41 quality of life, in the real merged code (emulator): practice START AT / REPEAT forcing the chosen attack in every
fight, the fight stats (damage dealt per member, damage taken per member, attacks with their hits), the stats box, the hotkeys
(R restarts, TAB fast-forward and its game-time clock), the records tables of the new modes (old record files still load),
the Tag Team / Remix launch corrections and the knight attack lists in the registry."""
import sys, time, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lu_harness import *
from t_run_helpers import *

FAILS = []; N = [0]
def ok(c, msg):
    N[0] += 1
    if not c: FAILS.append(msg); print('FAIL', msg, flush=True)
def eq(a, b, msg):
    N[0] += 1
    if a != b: FAILS.append(msg); print('FAIL', msg, 'got', repr(a), 'want', repr(b), flush=True)

KEYS = ['base', 'kaizo', 'elec', 'violet', 'thorn', 'cyan']
t0 = time.time()

# ---------- registry attack lists ----------
sim, e = lu_battle('base', combo=0)
for k in range(6):
    n = sim.eval('array_length(knight_reg(%d).atk)' % k)
    ok(n >= 20, '%s: attack list (%d)' % (KEYS[k], n))
    fin = [sim.eval('knight_reg(%d).atk[%d][3]' % (k, i)) for i in range(n)]
    ok(any(f & 2 for f in fin), '%s: the finale attacks are marked' % KEYS[k])
eq(sim.eval('knight_reg(1).atk[0][1]'), 'atk_Starstorm1', 'kaizo: attacks are named variables')
eq(sim.eval('knight_reg(0).atk[5][3]'), 1, 'base: unused attacks are marked')

# ---------- START AT / REPEAT in every fight ----------
def pick(k, want_phase):
    n = sim.eval('array_length(knight_reg(%d).atk)' % k)
    for i in range(n):
        if sim.eval('knight_reg(%d).atk[%d][3]' % (k, i)) == 0 and sim.eval('knight_reg(%d).atk[%d][0]' % (k, i)) == want_phase and i > 2:
            return i
    return 3

for key in KEYS:
    k = KEYI[key]
    for mode in (1, 2):
        sim, e = lu_battle(key, combo=0)
        i = pick(k, 2)
        want = sim.eval('knight_reg(%d).atk[%d][2]' % (k, i))
        sim.run('global.krun.cfg.p_mode = %d; global.krun.cfg.p_atk = %d; global.krun.rec = false;' % (mode, i))
        frames(sim, 3)
        hp0 = sim.eval('global.monsterhp[0]')
        names = []
        for t in range(2):
            r = enemy_turn(sim)
            ok(r is None, '%s %s: enemy turn %d (%s)' % (key, ('', 'START AT', 'REPEAT')[mode], t + 1, r))
            names.append(sim.eval('global.krun.st.atk[global.krun.st.cur].n'))
            frames(sim, 2)
        if mode == 1:
            eq(names[0], want, '%s START AT: the fight starts with %s' % (key, want))
            ok(names[1] != want or key == 'kaizo', '%s START AT: then the list goes on (%s)' % (key, names))
            if key != 'cyan':
                ok(sim.eval('global.monsterhp[0]') < hp0, '%s START AT: HP set to where that attack comes (%s -> %s)' % (key, hp0, sim.eval('global.monsterhp[0]')))
                ok(sim.eval('global.krun.eturns') >= 2, '%s START AT: pacing moved on (%s)' % (key, sim.eval('global.krun.eturns')))
        else:
            eq(names, [want, want], '%s REPEAT: the same attack every turn' % key)
            eq(sim.eval('array_length(global.krun.st.atk)'), 1, '%s REPEAT: stats count one attack twice' % key)
            eq(sim.eval('global.krun.st.atk[0].seen'), 2, '%s REPEAT: seen twice' % key)
            sim.run('global.monsterhp[0] = 50;')
            d = sim.eval('knight_dmg_filter(0, 500)')
            ok(d <= 49, '%s REPEAT: the knight cannot fall (%s)' % (key, d))
    print(key, 'practice ok', round(time.time() - t0, 1), flush=True)

# ---------- fight stats ----------
sim, e = lu_battle('base', combo=0, party=(1, 2, 4))
frames(sim, 3)
sim.run('global.krun.st = knight_stats_new(); global.monsterhp[0] = 7000;')
# damage dealt: a hero hitting the knight, a spell (caster), the hub (no caster)
sim.run('with (global.charinstance[1]) { var _d = knight_dmg_filter(0, 100); }')
sim.run('global.SP = instance_create(0, 0, obj_heart); global.SP.caster = 2; with (global.SP) { var _d2 = knight_dmg_filter(0, 50); } with (global.SP) instance_destroy();')
sim.run('with (obj_knight_ctrl) { var _d3 = knight_dmg_filter(0, 30); }')
d = [sim.eval('global.krun.st.dealt[%d]' % i) for i in range(5)]
ok(d[2] > 0, 'stats: Susie (slot 2) is credited with her hit (%s)' % d)
ok(d[4] > 0, 'stats: Noelle (slot 3) is credited with her spell (%s)' % d)
ok(d[0] > 0, 'stats: the hub\'s own damage goes to Other (%s)' % d)
# damage taken per member
sim.run('knight_dmg_baseline(global.krun); global.hp[2] -= 37; global.hp[4] -= 12; knight_dmg_sample(global.krun);')
eq([sim.eval('global.krun.st.taken[%d]' % i) for i in (1, 2, 4)], [0, 37, 12], 'stats: damage taken per member')
# hits per attack
sim.run('knight_stats_atk_set("Stars 1"); global.mnfight = 2; knight_stats_turn_begin(); knight_hit_event(); knight_hit_event();')
sim.run('global.mnfight = 0; knight_stats_atk_set("Stars 2"); global.mnfight = 2; knight_stats_turn_begin(); global.mnfight = 0; knight_hit_event();')
eq([(sim.eval('global.krun.st.atk[%d].n' % i), sim.eval('global.krun.st.atk[%d].hits' % i)) for i in range(2)], [('Stars 1', 2), ('Stars 2', 0)],
   'stats: hits counted for the attack that was flying (not during the player turn)')
lines = sim.py(sim.eval('knight_stats_lines(global.krun)'))
txt = repr(lines)
ok('Susie' in txt and 'Noelle' in txt and 'Stars 1' in txt, 'stats box: members and attacks (%s)' % txt[:200])
ok(lines[1][0] == 's' and 'Kris' in lines[1][1], 'stats box: a row per member')
# many attacks: pages of 8, most hits first
for i in range(12):
    sim.run('knight_stats_atk_set("A%d"); global.mnfight = 2; knight_stats_turn_begin(); %s global.mnfight = 0;' % (i, 'knight_hit_event(); ' * (i % 3)))
lines = sim.py(sim.eval('knight_stats_lines(global.krun)'))
hdr = [i for i, l in enumerate(lines) if l[0] == 's' and l[1] == 'ATTACKS'][0]
rows = [l for l in lines[hdr + 1:] if l[0] == 's']
eq(len(rows), 8, 'stats box: 8 attacks a page')
ok(rows[0][3] == '2', 'stats box: most hits first (%s)' % rows[0])
sim.run('global.krun.st.page = 1;')
lines = sim.py(sim.eval('knight_stats_lines(global.krun)'))
ok(any('Page 2' in str(l) for l in lines), 'stats box: page 2')
# the box opens from the results and comes back
sim.run('global.krun.result = "win"; global.krun.state = "finished"; global.krun.ui_done = false; knight_show_end();')
opts = [sim.eval('obj_knight_prompt.opts[%d].a' % i) for i in range(sim.eval('array_length(obj_knight_prompt.opts)'))]
ok('stats' in opts, 'results offer the fight stats (%s)' % opts)
sim.run('knight_act_run("stats");')
eq(sim.eval('obj_knight_prompt.title'), 'FIGHT STATS', 'the stats box opens')
sim.run('knight_act_run("stats_more");'); eq(sim.eval('global.krun.st.page'), 1, 'next page')
sim.run('knight_act_run("stats_back");'); eq(sim.eval('obj_knight_prompt.title'), 'KNIGHT DEFEATED!', 'back to the results')
eq(sim.eval('instance_number(obj_knight_prompt)'), 1, 'one box at a time')

# ---------- hotkeys ----------
sim, e = lu_battle('base', combo=0)
frames(sim, 3)
sim.keys_down = set()
sim.mock('keyboard_check', lambda s, k: 1 if int(k) in s.keys_down else 0)
sim.keys_pressed = set()
sim.mock('keyboard_check_pressed', lambda s, k: 1 if int(k) in s.keys_pressed else 0)
TAB = 9; RKEY = ord('R')
sim.run('room_speed = 30; global.mnfight = 0;')
sim.keys_down = {TAB}
eq(sim.eval('knight_ff_on()'), True, 'TAB: fast-forward in the player turn')
sim.run('knight_speed_apply(global.krun);'); eq(sim.eval('room_speed'), 120, 'TAB: 4x speed')
eq(sim.eval('knight_frame_step()'), 1, 'fast-forward counts game time (records are not faster)')
sim.run('global.mnfight = 2;'); eq(sim.eval('knight_ff_on()'), False, 'TAB: never while bullets fly')
sim.run('knight_speed_apply(global.krun);'); eq(sim.eval('room_speed'), 30, 'back to normal speed')
sim.run('global.mnfight = 0; global.krun.cfg.nohotkeys = 1;'); eq(sim.eval('knight_ff_on()'), False, 'HOTKEYS OFF: no fast-forward')
sim.run('global.krun.cfg.nohotkeys = 0; global.krun.state = "arena";'); eq(sim.eval('knight_ff_on()'), True, 'TAB in the arena intro')
sim.keys_down = set()
sim.run('global.krun.state = "battle"; global.krun.rec = true; global.krun.fcommitted = false; global.krun.mode = 0;')
sim.called = []
sim.mock('knight_rematch', lambda s, *a: (s.called.append('rematch'), 0)[1])
sim.mock('knight_fight_commit', lambda s, *a: (s.called.append(('commit', s.py(a[0]))), 0)[1])
sim.keys_pressed = {RKEY}
sim.run('knight_backspace_check();')
eq(sim.called, [('commit', 'abandon'), 'rematch'], 'R: the attempt is left and the fight restarts at once')
sim.called = []
sim.run('global.krun.cfg.nohotkeys = 1; knight_backspace_check();')
eq(sim.called, [], 'HOTKEYS OFF: R does nothing')
sim.keys_pressed = set()

# ---------- records of the new modes; an old file still loads ----------
s2 = make_sim()
s2.run('knight_store_load();')
s2.run('var _r = knight_rec_get("tag", "st"); _r.win = 3; _r.att = 5; knight_store_save();')
s2.run('global.knight_loaded = false; knight_store_load();')
eq(s2.eval('knight_rec_get("tag", "st").win'), 3, 'records: Tag Team wins are kept')
eq(s2.eval('global.knight_store_status'), 'ok', 'records: file reads back fine')
# an older file: no tag / remix sections at all -> still valid, the new tables start blank
s2.run('ossafe_ini_open(knight_store_file()); ini_section_delete("rec_tag_st"); ini_section_delete("rec_tag_ch"); ini_section_delete("rec_tag_nh");'
       'ini_section_delete("rec_remix_st"); ini_section_delete("rec_remix_ch"); ini_section_delete("rec_remix_nh"); ossafe_ini_close();')
# the stored sum of the old file did not include them
s2.run('global.knight_rec.tag = undefined; variable_struct_remove(global.knight_rec, "tag"); variable_struct_remove(global.knight_rec, "remix");')
keys = s2.py(s2.eval('knight_rec_keys()'))
ok(keys[-2:] == ['tag', 'remix'], 'records: the new tables come last (%s)' % keys)
res = s2.eval('knight_store_parse(knight_store_file()).st')
ok(res in ('ok', 'corrupt'), 'records: parse of a file without the new tables (%s)' % res)

# ---------- launch corrections ----------
s3 = make_sim()
s3.run('knight_store_load(); var _c = knight_cfg_default(); _c.combo = 1; _c.knight = 0; _c.knight2 = 3; _c.weird = 1; _c.practice = 1; _c.c_twin = 1; global.R = knight_resolve(_c);')
eq(s3.eval('global.R.ok'), True, 'tag: launch ok')
eq((s3.eval('global.R.cfg.weird'), s3.eval('global.R.cfg.practice'), s3.eval('global.R.cfg.c_twin')), (0, 0, 0), 'tag: Weird Route, practice and Twin Knight are switched off')
eq(s3.eval('array_length(global.R.corr)'), 3, 'tag: and the player is told (%s)' % s3.py(s3.eval('global.R.corr')))
s3.run('var _c = knight_cfg_default(); _c.combo = 2; _c.knight = 4; global.R = knight_resolve(_c);')
eq((s3.eval('global.R.ok'), s3.eval('global.R.plan[0]')), (True, 0), 'remix: the Normal Knight hosts')
s3.run('var _c = knight_cfg_default(); _c.combo = 1; _c.knight = 2; _c.knight2 = 0; _c.c_notp = 1; global.R = knight_resolve(_c);')
eq(s3.eval('global.R.ok'), False, 'tag with Supercharged: No TP is refused (it needs TP)')
s3.run('var _c = knight_cfg_default(); _c.combo = 1; _c.knight = 0; _c.knight2 = 5; _c.c_nohit = 1; global.R = knight_resolve(_c);')
eq(s3.eval('global.R.ok'), False, 'tag with the joke fight: No-Hit is refused')
s3.run('var _c = knight_cfg_default(); _c.p_mode = 2; _c.p_atk = 4; _c.c_time = 1; global.R = knight_resolve(_c);')
eq((s3.eval('global.R.ok'), s3.eval('global.R.cfg.c_time')), (True, 0), 'repeat: Time Limit switched off')
s3.run('var _c = knight_cfg_default(); _c.p_mode = 1; _c.p_atk = 4; _c.mode = 1; global.R = knight_resolve(_c);')
eq(s3.eval('global.R.cfg.p_mode'), 0, 'rush: START AT switched off')
s3.run('var _c = knight_cfg_default(); _c.combo = 2; _c.p_atk = 999; _c.knight2 = 99; knight_cfg_sanitize(_c); global.C = _c;')
eq((s3.eval('global.C.p_atk'), s3.eval('global.C.knight2')), (0, 0), 'sanitize: out-of-range attack / partner fixed')
# records category and key
s3.run('var _c = knight_cfg_default(); _c.combo = 1; _c.knight = 0; _c.knight2 = 4; global.RR = knight_run_new({ src: _c, cfg: _c, plan: [0], reveal: "", corr: [] });')
eq(s3.eval('knight_run_rec_key(global.RR)'), 'tag', 'records: a Tag Team goes to its own table')
eq(s3.eval('knight_cfg_text(global.RR.cfg)').split(' ')[0], 'NORMAL+THORN', 'records: the pair is noted')

# TIME LIMIT of the lineups: the START box says the same number the battle uses
s3.run('var _c = knight_cfg_default(); _c.combo = 1; _c.knight = 0; _c.knight2 = 1; _c.c_time = 1; global.R = knight_resolve(_c); '
       'global.LL = knight_ui_launch_lines({ src: global.R.src, cfg: global.R.cfg, plan: global.R.plan, reveal: "", corr: [] });')
want = s3.eval('knight_turn_limit(0, false) + knight_turn_limit(1, false) - 10')
eq(want, 52, 'tag Normal+Kaizo: TIME LIMIT is both lists + 10 (25 + 37 - 10)')
ok(any(('Time limit: %d enemy turns.' % want) == l for l in s3.py(s3.eval('global.LL'))), 'tag: the START box shows it (%s)' % s3.py(s3.eval('global.LL')))
eq(s3.eval('knight_lu_turn_limit(global.R.cfg)'), want, 'tag: the battle uses the same number')
s3.run('var _c = knight_cfg_default(); _c.combo = 2; _c.c_time = 1; global.R = knight_resolve(_c); '
       'global.LL = knight_ui_launch_lines({ src: global.R.src, cfg: global.R.cfg, plan: global.R.plan, reveal: "", corr: [] });')
ok(any('Time limit: 34 enemy turns.' == l for l in s3.py(s3.eval('global.LL'))), 'remix: the START box shows 34 (%s)' % s3.py(s3.eval('global.LL')))
s3.run('var _c = knight_cfg_default(); _c.knight = 4; _c.c_time = 1; global.R = knight_resolve(_c); '
       'global.LL = knight_ui_launch_lines({ src: global.R.src, cfg: global.R.cfg, plan: global.R.plan, reveal: "", corr: [] });')
ok(any('Time limit: 30 enemy turns.' == l for l in s3.py(s3.eval('global.LL'))), 'single fight (Thorn): unchanged, 30 (%s)' % s3.py(s3.eval('global.LL')))

print('qol41 tests', N[0], 'fails', len(FAILS), round(time.time() - t0, 1))

# ---------- build 40 fix: the learned-moves text gets one box per line (it ran out of the bottom of the box) ----------
import re as _re
def lines_of(page, width=29):
    t = _re.sub(r'\\\\[cEFTf]\w|\\\\[a-zA-Z]|\^\d|/%|/|%', '', page)
    t = t.replace('\\cY', '').replace('\\cW', '')
    n = 0
    for part in t.split('&'):
        words = part.split(' ')
        cur = 0; n += 1
        for w in words:
            add = len(w) + (1 if cur else 0)
            if cur + add > width:
                n += 1; cur = 2 + len(w)
            else:
                cur += add
    return n
s4, e = lu_battle('violet', party=(3, 4, 2), combo=0)
s4.run('global.charname = ["", "The Cage", "The Girl", "The Prince", "The Angel"];')
s4.run('knight_learn_init(true); global.T = knight_learn_after(1, 0, false); knight_msg_pages(global.T);')
n = s4.eval('global.msgno')
pages = [s4.eval('global.msg[%d]' % i) for i in range(int(n) + 1)]
ok(len(pages) >= 4, 'learned moves: one page each (%s)' % pages)
ok(all(p.endswith('/') for p in pages[:-1]) and pages[-1].endswith('/%'), 'learned moves: every page waits, the last one closes the box')
ok(all(p.count('* ') == 1 for p in pages), 'learned moves: one line per page')
ok(all(lines_of(p) <= 3 for p in pages), 'learned moves: every page fits the 3-line box (%s)' % [lines_of(p) for p in pages])
ok('FIRESTORM' in ''.join(pages) and 'ICESTORM' in ''.join(pages) and 'courage' in ''.join(pages), 'learned moves: nothing lost')
print('qol41 tests (with text pages)', N[0], 'fails', len(FAILS))
