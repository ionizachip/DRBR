"""Generate rules/b37_rules.json: build 37 fixes (SOUL position without Kris, ACT rows by slot, Susie's balloons only when she is there,
Shadow Mantle by slot, Thorn Knight max-HP erosion for whoever is hit, Weird Route for every fight and party).
The finds are checked against the text the earlier rule files leave behind (b37 runs last)."""
import json, os, re, sys
sys.path.insert(0, '/home/claude/scripts')
import rules_apply
G = '/home/claude/work/gml/'
K = ['base', 'kaizo', 'elec', 'violet', 'thorn', 'cyan']
OUTF = '/home/claude/scripts/rules/b37_rules.json'

def ents(k):
    d = G + k + '/CodeEntries'
    return {f[:-4]: open(f'{d}/{f}', encoding='utf8', errors='replace').read() for f in os.listdir(d)}

# text after every earlier rule file (b37 excluded)
_order = list(rules_apply.ORDER)
rules_apply.ORDER = _order[:_order.index('b37_rules.json')]   # only the rule files that run before this one
T = {k: ents(k) for k in K}
_ap, _pr = rules_apply.apply_all(T)
assert not _pr, _pr
rules_apply.ORDER = _order

rules = []
SC = ['solo', 'dup', 'noelle', 'nokris']

def R(i, var, entry, find, rep, why, regex=False, count=None):
    t = T[var][entry]
    if regex:
        n = len(re.findall(find, t))
        assert n > 0 and (count is None or n == count), (i, var, n, count)
        t2 = re.sub(find, rep, t)
    else:
        n = t.count(find)
        assert n == 1, (i, var, n, find[:80])
        t2 = t.replace(find, rep, 1)
    T[var][entry] = t2          # later rules see this rule's result, exactly as rules_apply does
    r = {"id": i, "variants": [var], "entry": entry, "find": find, "replace": rep, "why": why, "scenarios": SC}
    if regex:
        r["regex"] = True
        if count is not None:
            r["count"] = count
    rules.append(r)

ST = 'gml_Object_obj_knight_enemy_'

# ---------- the battle heart without Kris ----------
R('B01-moveheart-violet', 'violet', 'gml_GlobalScript_scr_moveheart',
  'return instance_create(obj_herokris.x + 10, obj_herokris.y + 40, obj_moveheart);',
  'return instance_create(knight_soul_x(), knight_soul_y(), obj_moveheart);',
  'CRASH without Kris in Violet Knight ("Unable to find any instance for object obj_herokris" at gml_Script_scr_moveheart): the heart comes out of the leader.')
R('B01-moveheart-kaizo', 'kaizo', 'gml_GlobalScript_scr_moveheart',
  '    var _hX = camerax() - 120;\n    var _hY = cameray() + 170;\n    if (i_ex(obj_herokris))\n    {\n        _hX = obj_herokris.x + 10;\n        _hY = obj_herokris.y + 40;\n    }\n',
  '    var _hX = knight_soul_x();\n    var _hY = knight_soul_y();\n',
  'Kaizo flew the heart in from off-screen when Kris was missing; now from the leader.')
R('B02-returnheart-violet', 'violet', 'gml_Object_obj_returnheart_Create_0',
  'distx = obj_herokris.x + 10;\ndisty = obj_herokris.y + 40;\n',
  'distx = knight_soul_x();\ndisty = knight_soul_y();\n',
  'CRASH without Kris in Violet Knight at the end of every enemy turn (same as scr_moveheart).')
R('B02-returnheart-kaizo', 'kaizo', 'gml_Object_obj_returnheart_Create_0',
  'distx = camerax() - 120;\ndisty = cameray() + 170;\nif (i_ex(obj_herokris))\n{\n    distx = obj_herokris.x + 10;\n    disty = obj_herokris.y + 40;\n}\n',
  'distx = knight_soul_x();\ndisty = knight_soul_y();\n',
  'Kaizo: the heart went back off-screen when Kris was missing; now to the leader.')

# ---------- ACT rows when a member's ACT is used up (slot 2 hard-coded) ----------
for v in K:
    R('B03-actcount-' + v, v, ST + 'Step_0', r'global\.battleactcount\[1\] = 0;', 'knight_actcount_fix();',
      'The fights reset the ACT row count of party slot 2 (Susie in the story party) when an S/R-Action is used up; with another party the '
      'real member kept a blank first row and slot 2 lost its count. All slots are recounted by scr_spellmenu_setup right after.', regex=True)

# ---------- Susie's speech bubbles only when Susie is there (and not while practising) ----------
for v in ['base', 'elec', 'thorn', 'cyan']:
    R('B04-susie-balloons-' + v, v, ST + 'Step_0', r'if \(global\.hp\[2\] > 0\)(\s*\{\s*balloonturn\+\+;)',
      r'if (scr_havechar(2) && global.hp[2] > 0 && !practicemode)\1',
      'Susie\'s taunts to the Knight played from an empty spot when she was not in the party (her HP is kept while she is away), '
      'practice included. Kaizo and Violet already check this.', regex=True, count=1)

# ---------- Thorn Knight: the max-HP erosion hits whoever was hit ----------
t = T['thorn']['gml_GlobalScript_scr_damage']
a = t.index('                var _hplost_mantle = ceil(random_range(5, 10));\n') + len('                var _hplost_mantle = ceil(random_range(5, 10));\n')
b = t.index('                snd_stop(snd_hurt1);', a)
blk = t[a:b]
assert blk.startswith('                var _tc = (target < 3) ? global.char[target] : 0;\n') and blk.count('global.maxhp[') == 12 and '_tc == 4' not in blk, blk[:200]
R('B05-thorn-erode', 'thorn', 'gml_GlobalScript_scr_damage', blk,
  '                target = knight_fix_target(target);\n                knight_thorn_erode(target, _hplost, _hplost_mantle);\n',
  'Thorn Knight\'s max-HP erosion (already by character since an engine rule) had no case for Noelle: she never lost max HP. '
  'Now whoever is actually hit (after the knight\'s retarget) loses it, Noelle included (floor 50), and the mantle is checked on that slot.')

# ---------- Shadow Mantle by slot ----------
MANTLE = [
    ('a', r'if \(global\.chararmor1\[1\] == 23 \|\| global\.chararmor2\[1\] == 23 \|\| global\.chararmor1\[2\] == 23 \|\| global\.chararmor2\[2\] == 23 \|\| global\.chararmor1\[3\] == 23 \|\| global\.chararmor2\[3\] == 23\)',
     'if (knight_mantle_party())'),
    ('b', r'if \(global\.hp\[([123])\] > 0 && \(global\.chararmor1\[\1\] == 23 \|\| global\.chararmor2\[\1\] == 23\)\)',
     r'if (knight_slot_up(\1 - 1) && knight_mantle_slot(\1 - 1))'),
    ('c', r'if \(global\.hp\[([123])\] < 1 && target == (\d)\)', r'if (knight_slot_down(\2) && target == \2)'),
    ('d', r'if \(\(target == (\d) && global\.chararmor1\[([123])\] == 23\) \|\| global\.chararmor2\[\2\] == 23\)', r'if (target == \1 && knight_mantle_slot(\1))'),
    ('e', r'if \(target == (\d) && \(global\.chararmor1\[([123])\] == 23 \|\| global\.chararmor2\[\2\] == 23\)\)', r'if (target == \1 && knight_mantle_slot(\1))'),
    ('f', r'if \(\(global\.chararmor1\[([123])\] == 23 \|\| global\.chararmor2\[\1\] == 23\) && (target|hpi) == (\d)\)', r'if (knight_mantle_slot(\3) && \2 == \3)'),
]
for v in K:
    for e in ['gml_GlobalScript_scr_damage', 'gml_GlobalScript_scr_damage_maxhp']:
        if e not in T[v]:
            continue
        for tag, pat, rep in MANTLE:
            n = len(re.findall(pat, T[v][e]))
            if n:
                R('B06-mantle-%s-%s-%s' % (tag, v, e.replace('gml_GlobalScript_scr_', '')), v, e, pat, rep,
                  'Shadow Mantle (draws hits, takes a third of the damage) was checked on Kris for slot 1, Susie for slot 2 and Ralsei for slot 3 '
                  'whoever stood there: with any other party it protected the wrong member (or nobody, or redirected hits to an empty slot). '
                  'Now it is the mantle of the member in that slot.', regex=True, count=n)

# ---------- a member the Knight took (Weird Route) cannot be healed back ----------
H05 = '    if (knight_noheal_active())\n    {\n        abovemaxhp = 0;\n        belowzero = 0;\n        return 0;\n    }\n'
for v in K:
    R('B07-wr-noheal-' + v, v, 'gml_GlobalScript_scr_heal', H05,
      H05 + '    if (knight_wr_noheal(arg0))\n    {\n        abovemaxhp = 0;\n        belowzero = 0;\n        return 0;\n    }\n',
      'Weird Route: the member the Knight takes stays down for the rest of the fight.')

# ---------- Weird Route for the knights without a Side B: the scene starts at the end of an enemy turn ----------
END = '                tempitem[i][j] = global.item[i];\n            }\n        }\n    }\n}'
for v in ['base', 'elec', 'thorn', 'cyan']:
    t = T[v]['gml_GlobalScript_scr_mnendturn']
    assert t.rstrip().endswith(END), v
    R('B08-wr-turnend-' + v, v, 'gml_GlobalScript_scr_mnendturn', END,
      '                tempitem[i][j] = global.item[i];\n            }\n        }\n        knight_wr_turnend();\n    }\n}',
      'Weird Route on a knight without a Side B: halfway through its attack list the Knight takes one member (hub scene, knight_wr_*).')

# ---------- Noelle looks like the Angel on a Weird Route save in every fight (Kaizo already did) ----------
for v in ['base', 'elec', 'violet', 'thorn', 'cyan']:
    R('B09-noelle-sideb-look-' + v, v, 'gml_Object_obj_heroparent_Create_0', '    _sideb = 0;\n    if (_sideb == 1)\n',
      '    _sideb = global.flag[456] > 0;\n    if (_sideb == 1)\n',
      'Weird Route: Noelle uses her Side B battle sprites (the game\'s own) in every fight, like Kaizo Knight shows her.')

# ---------- Violet Knight Side B for any party ----------
R('B10-vb-init', 'violet', ST + 'Create_0', 'kill_skipped = 0;\n', 'kill_skipped = 0;\nknight_vb_init();\n',
  'Side B state for parties without Kris (who finishes the fight, the extra S/R/N-Actions).')
a = ('    if (kill_target == 1410)\n    {\n        knightkillcon = 30;\n    }\n    else if (!scr_havechar(2))\n    {\n        knightkillcon = 10;\n    }\n'
     '    else if (global.hp[2] > 0)\n    {\n        knightkillcon = 11;\n    }\n    else\n    {\n        knightkillcon = 50;\n    }\n')
R('B11-vb-route9', 'violet', ST + 'Step_0', a, '    knightkillcon = knight_vb_route9();\n',
  'After the loss: Ralsei reacts first when the Angel falls (no Kris), Susie\'s second reaction when she loses Ralsei too (no Kris), '
  'otherwise the mod\'s own route (Kris scene, Susie scene, or straight on).')
a = 'if (knightkillcon == 10 && kill_target == obj_heroralsei && !kill_skipped && scr_havechar(4)'
R('B12-vb-endkill', 'violet', ST + 'Step_0', a,
  'if (knightkillcon == 10 && !knight_vb_kris())\n{\n    knight_vb_end_kill();\n}\n' + a,
  'Without Kris the consequences of a loss are the hub\'s (Susie\'s own RED BUSTER, then the finisher scene) instead of the mod\'s Kris ACTs.')
R('B13-vb-extra', 'violet', ST + 'Step_0', 'if (knight_marker != -4)\n', 'knight_vb_extra();\nif (knight_marker != -4)\n',
  'Scenes added for parties without Kris: Ralsei\'s reaction, Susie\'s second reaction, the finisher\'s power-up flurry.')
a = 'if (global.myfight == 3)\n{\n    xx = __view_get(e__VW.XView, 0);\n    yy = __view_get(e__VW.YView, 0);\n'
R('B14-vb-acts', 'violet', ST + 'Step_0', a, a + '    knight_vb_acts();\n',
  'The S/R/N-Actions added without Kris (RED BUSTER, the finisher) run before the mod\'s own ACT handlers and use the action up.')
a = '        global.maxhp[1] += _krisiscomicallypowerfulnow;\n        global.hp[1] += _krisiscomicallypowerfulnow;\n'
R('B15-vb-finhp', 'violet', ST + 'Step_0', a,
  '        var _vbfc = knight_vb_fin_char();\n        global.maxhp[_vbfc] += _krisiscomicallypowerfulnow;\n        global.hp[_vbfc] += _krisiscomicallypowerfulnow;\n',
  'The finale\'s joke max-HP reward goes to whoever finished the Knight.')
a = '        global.specialbattle = 0;\n        scr_endcombat();\n    }\n'
R('B16-vb-won', 'violet', ST + 'Step_0', a, '        knight_battle_won();\n' + a,
  'A Side B clear never reached the battle-won hook (it skips the PTB02 con 8 step), so it was not recorded as a win.')

# ---------- Kaizo Knight Side B without Kris: Susie's RudeBuster S-Action in place of Kris's X-Slash ACT ----------
a = '        global.actcost[myself][2] = 62.5;\n        k_tpscene = 0;\n'
R('B17-kz-init', 'kaizo', ST + 'Step_0', a, '        global.actcost[myself][2] = 62.5;\n        knight_kz_init();\n        k_tpscene = 0;\n',
  'Side B without Kris: Susie gets a RudeBuster S-Action (25% TP) in place of the X-Slash ACT only Kris could use.')
a = '    yy = __view_get(e__VW.YView, 0);\n'
R('B18-kz-acts', 'kaizo', ST + 'Step_0', a, a + '    knight_kz_acts();\n',
  'The RudeBuster S-Action runs before the mod\'s own S-Action handlers (which read index 1 as HoldBreath without Kris) and uses the action up.')

json.dump(rules, open(OUTF, 'w'), indent=1)
print(len(rules), 'rules')
