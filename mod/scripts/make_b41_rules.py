"""Generate rules/b41_rules.json: build 41 - Tag Team / Attack Remix lineups and the practice START AT / REPEAT modes.
Hooks (every knight fight):
  - scr_mnendturn: the end of every enemy turn tells the lineup who fights the next round (knight_lu_turnend)
  - the knight's Draw: its ending (beaten after its Roaring) asks the lineup first (knight_lu_end_ok - a Tag Team knight whose
    partner still stands is knocked out instead; evaluated last, so only when the fight's own conditions hold)
  - the knight's Step: a knight that is about to be switched out does nothing for that frame (knight_lu_hold)
  - the attack choice (Other_10): an attack can be forced through the fight's own practice branch (knight_force_sel), Kaizo
    Knight through its named attacks (knight_force_kz); both also tell the fight stats which attack is coming.
The finds are checked against the text every earlier rule file leaves behind (b41 runs last)."""
import json, os, re, sys
sys.path.insert(0, '/home/claude/scripts')
import rules_apply
G = '/home/claude/work/gml/'
K = ['base', 'kaizo', 'elec', 'violet', 'thorn', 'cyan']
OUTF = '/home/claude/scripts/rules/b41_rules.json'


def ents(k):
    d = G + k + '/CodeEntries'
    return {f[:-4]: open(f'{d}/{f}', encoding='utf8', errors='replace').read() for f in os.listdir(d)}


_order = list(rules_apply.ORDER)
rules_apply.ORDER = _order[:_order.index('b41_rules.json')] if 'b41_rules.json' in _order else _order
T = {k: ents(k) for k in K}
_ap, _pr = rules_apply.apply_all(T)
assert not _pr, _pr
rules_apply.ORDER = _order

rules = []
SC = ['tag', 'remix', 'start_at', 'repeat']
ST = 'gml_Object_obj_knight_enemy_'


def R(i, var, entry, find, rep, why, regex=False, count=None, sc=None):
    t = T[var][entry]
    if regex:
        n = len(re.findall(find, t))
        assert n > 0 and (count is None or n == count), (i, var, n, count)
        t2 = re.sub(find, rep, t)
        count = n
    else:
        n = t.count(find)
        assert n == 1, (i, var, n, find[:80])
        t2 = t.replace(find, rep, 1)
    T[var][entry] = t2
    r = {"id": i, "variants": [var], "entry": entry, "find": find, "replace": rep, "why": why, "scenarios": sc or SC}
    if regex:
        r["regex"] = True
        r["count"] = count
    rules.append(r)


# ---------- end of every enemy turn: who fights the next round ----------
for v in K:
    t = T[v]['gml_GlobalScript_scr_mnendturn']
    # the function ends with the close of "if (techwon == 0) { ... }" and the function itself
    m = re.search(r'\n    \}\n\}\s*$', t)
    assert m, v
    tail = t[m.start():]
    R('B41-lu-turnend-' + v, v, 'gml_GlobalScript_scr_mnendturn', r'\n    \}\n\}\s*\Z',
      '\n        knight_lu_turnend();\n    }\n}\n',
      'Tag Team / Attack Remix: at the end of every enemy turn the lineup picks the knight for the next round (switched in at the '
      'start of the player turn, never while bullets fly).', regex=True, count=1)

# ---------- the knight's ending asks the lineup first ----------
COND = r'(if \([^\n]*haveusedroaring == true && end_cutscene_version == 0 && global\.monsterhp\[myself\] <= \(global\.monstermaxhp\[myself\] \* [0-9.]+\) && endcon != 1[^\n]*)\)\n'
for v in K:
    R('B41-lu-end-' + v, v, ST + 'Draw_0', COND, r'\1 && knight_lu_end_ok())\n',
      'Tag Team: a knight beaten after its Roaring is knocked out and its partner takes over while the partner still stands; the '
      'last knight ends the battle as usual. Attack Remix: only the finale knight ends it. Checked last (only when the fight\'s own '
      'ending conditions all hold).', regex=True, count=1)

# ---------- a knight about to be switched out skips its Step ----------
for v in K:
    R('B41-lu-hold-' + v, v, ST + 'Step_0', r'\A', 'if (knight_lu_hold())\n    exit;\n',
      'Tag Team / Attack Remix: the knight that is switched out at the end of this frame does not start a new turn or talk first.',
      regex=True, count=1)

# ---------- forced attacks (Remix, START AT, REPEAT) through the fight's own practice branch ----------
PB = 'if (practicemode)\n{\n    phase = prac_list[prac_sel][0];'
for v in ['base', 'elec', 'violet', 'thorn', 'cyan']:
    R('B41-force-' + v, v, ST + 'Other_10', PB, 'if (knight_force_sel() || practicemode)\n{\n    phase = prac_list[prac_sel][0];',
      'Attack Remix / START AT / REPEAT: the attack is picked through the same branch the in-fight attack picker uses (so it starts '
      'exactly as in practice); otherwise the fight\'s own list decides. Also names the attack for the fight stats.')
R('B41-force-kaizo', 'kaizo', ST + 'Other_10', r'\A', 'knight_force_kz();\n',
  'Attack Remix / START AT / REPEAT for Kaizo Knight: its attacks are named (kaizo_attack); also names the attack for the stats.',
  regex=True, count=1)

# ---------- Violet's Side B music: a short fade at the blow instead of a dead stop, the Side B song fades in ----------
KILL = '        if (kill_target != obj_herosusie)\n        {\n            snd_stop(global.batmusic[0]);\n'
R('B41-mus-cut-violet', 'violet', ST + 'Step_0', KILL,
  '        if (kill_target != obj_herosusie)\n        {\n            knight_mus_cut(10);\n',
  'Violet Side B: the battle song fades out in a third of a second at the blow instead of stopping dead.', sc=['weird'])
SB = '        global.batmusic[0] = violetknight_sideb;\n        global.batmusic[1] = mus_loop(global.batmusic[0]);\n'
R('B41-mus-sideb-violet', 'violet', ST + 'Step_0', SB, '        knight_mus_switch(violetknight_sideb, 60);\n',
  'Violet Side B: the Side B song fades in over two seconds instead of starting at full volume.', sc=['weird'])

json.dump(rules, open(OUTF, 'w'), indent=1)
print('b41 rules:', len(rules))
