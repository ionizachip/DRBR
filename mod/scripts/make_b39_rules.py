"""Generate rules/b39_rules.json: build 39 - when Susie is not in the fight, Ralsei or Noelle speak where she would (the knights'
talk-phase lines, turns 6-14), Susie's own lines name the real party in every knight, and the narration before the Roaring names
whoever is there. The finds are checked against the text every earlier rule file leaves behind (b39 runs last)."""
import json, os, re, sys
sys.path.insert(0, '/home/claude/scripts')
import rules_apply
G = '/home/claude/work/gml/'
K = ['base', 'kaizo', 'elec', 'violet', 'thorn', 'cyan']
OUTF = '/home/claude/scripts/rules/b39_rules.json'

def ents(k):
    d = G + k + '/CodeEntries'
    return {f[:-4]: open(f'{d}/{f}', encoding='utf8', errors='replace').read() for f in os.listdir(d)}

_order = list(rules_apply.ORDER)
rules_apply.ORDER = _order[:_order.index('b39_rules.json')]   # only the rule files that run before this one
T = {k: ents(k) for k in K}
_ap, _pr = rules_apply.apply_all(T)
assert not _pr, _pr
rules_apply.ORDER = _order

rules = []
SC = ['solo', 'dup', 'noelle', 'nokris']
ST = 'gml_Object_obj_knight_enemy_Step_0'

def R(i, var, entry, find, rep, why, regex=False, count=None):
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
    r = {"id": i, "variants": [var], "entry": entry, "find": find, "replace": rep, "why": why, "scenarios": SC}
    if regex:
        r["regex"] = True
        r["count"] = count
    rules.append(r)

# Susie's talk-phase lines (as the GML source spells them) -> which beat they are
BEAT = {
    'Heheh.../%': '6a', 'Thing is,&you actually.../%': '7a', "You? You're all&damn alone.../%": '8a',
    'Even... even if&you knock me down.../%': '9a', 'Even... even if&you knock them down.../%': '9a',
    'As long as Kris has got&a hand to lift me up with.../%': '10a', "As long as I'm here to&lift them back up.../%": '10a',
    'So... give up./%': '11', "You know you can't&win... so... give up!/%": '12', "... You won't even.../%": '13a',
    '... heh... heheheh.../%': '14a', "Didn't... think&we'd still be&standing, did you?/%": '6b',
    'You actually messed up,&picking a fight with US!/%': '7b', 'Me? I got...&Kris and Ralsei&behind me./%': '8b',
    'As long as Kris,&Ralsei, are here.../%': '9b', "As long as&I'm here.../%": '9b', "Heh... you're never gonna&win, you hear me?!/%": '10b',
    '... say a thing, huh.../%': '13b', "Man, I'm done talking./%": '14b', '... people like you...&just piss me off./%': '14c',
}
CBEAT = {
    '\\\\c5So, uh.../%': 'c6a', "\\\\c5Well, it doesn't matter!/%": 'c7a', "\\\\c5Ralsei? He's all damn alone.../%": 'c8a',
    '\\\\c5Even... even if&you set gravity to 5.../%': 'c9a', '\\\\c5Even if you rotate&the tracking swords by&1 degree.../%': 'c9b',
    '\\\\c5As long as using a revivemint heals half of an alive party members max hp.../%': 'c10a',
    '\\\\c5And as long as ralsei obtains the thornring.../%': 'c10b', '\\\\c5So... give me a $1000 gift./%': 'c11',
    '\\\\c5The hell!?&How is it not dead&yet!? That was the&final attack!/%': 'c12', "\\\\c5... You won't even say.../%": 'c13a',
    '\\\\c5... heh... heheheh.../%': 'c14a', '\\\\c5Anyone gonna comment on&what the HELL the&Knight is doing...?/%': 'c6b',
    "\\\\c5I'm not scared! no matter how much reality bending you do!/%": 'c7b', "\\\\c5Me? I'm Goated With The Sauce./%": 'c8b',
    '\\\\c5As long as Papyrus is behind me.../%': 'c9c', '\\\\c5As long as&Kris is gambling.../%': 'c9x',
    "\\\\c5Heh... you're never gonna&win, you hear me?!/%": 'c10c', "\\\\c5Man, I'm done talking./%": 'c14b',
    '\\\\c5... people like you...&just piss^5       ./%': 'c14c',
}
KZJ = {'オレを倒したって…/%': '9a', 'クリスが オレを&起こしてくれるかぎり…/%': '10a', '見ろよ…&オレたち まだ&倒れてねーぞ？/%': '6b',
       'オレらに&ケンカ売ったのは&まちがいだぜ！/%': '7b', 'でも オレには…&クリスと ラルセイが&ついてる/%': '8b', 'クリスとラルセイが&いるかぎり…/%': '9b'}

STR = r'"((?:[^"\\]|\\.)*)"'
BALLOON = ('global.typer = 75;\n{i}scr_enemyblcon(obj_herosusie.x + 92, obj_herosusie.y + 38, 14);\n{i}scr_guardpeek(obj_herosusie);\n')

def region(t):
    a = t.index('    if (scr_isphase("enemytalk") && talked == 0 && end_cutscene_version == 0)')
    b = t.index('    if (talked == 1 && scr_isphase("enemytalk") && !i_ex(obj_writer))', a)
    return a, b

def wrap_lines(reg, var):
    """msgsetloc(0, "<Susie line>", id) / knight_susie_line("<line>") -> knight_taunt_line(beat, "<line>")"""
    n = [0]
    def sub_plain(m):
        s = m.group(1)
        beat = (CBEAT if var == 'cyan' else BEAT).get(s)
        if beat is None:
            if var == 'cyan' and s.startswith('\\\\c5\\"Hi! I'):
                beat = 'c13b'
            else:
                raise AssertionError((var, s))
        n[0] += 1
        return 'msgsetloc(0, knight_taunt_line("%s", "%s"), ' % (beat, s)
    reg = re.sub(r'msgsetloc\(0, knight_susie_line\(' + STR + r'\), ', sub_plain, reg)
    reg = re.sub(r'msgsetloc\(0, ' + STR + r', ', sub_plain, reg)
    return reg, n[0]

why_lines = ('Without Susie nobody spoke in the talk phase: the first of Ralsei / Noelle in party order who is still standing now says '
             'the same beats in their own words (Noelle as the Angel on a Weird Route save; Kris never speaks). Susie keeps her lines, '
             'naming the friends who are really there.')

# ---------- Normal, Supercharged, Thorn, Violet, Cyan: the talk phase ----------
for k in ['base', 'elec', 'thorn', 'violet', 'cyan']:
    t = T[k][ST]
    a, b = region(t)
    reg = t[a:b]
    new = reg
    if k == 'violet':
        g = 'if (scr_havechar(2) && global.hp[2] > 0 && practice == false && !ral_dead)'
        assert new.count(g) == 1, k
        new = new.replace(g, 'if (knight_taunt_begin(practice == false && !ral_dead))')
        new = new.replace('balloonturn == 9 && knight_friends_down()', 'balloonturn == 9 && knight_taunt_down()')
        new = new.replace('balloonturn == 10 && knight_friends_down()', 'balloonturn == 10 && knight_taunt_down()')
    else:
        g = 'if (scr_havechar(2) && global.hp[2] > 0 && !practicemode)'
        assert new.count(g) == 1, k
        new = new.replace(g, 'if (knight_taunt_begin(!practicemode))')
        if k != 'cyan':
            for bt in ('9', '10'):
                c0 = 'balloonturn == %s && global.hp[1] < 1 && global.hp[3] < 1' % bt
                assert new.count(c0) == 1, (k, bt)
                new = new.replace(c0, 'balloonturn == %s && knight_taunt_down()' % bt)
    assert 'knight_taunt_down' in new or k == 'cyan'
    new, nl = wrap_lines(new, k)
    assert nl == (22 if k == 'cyan' else 20), (k, nl)
    nb = 0
    for ind in ('            ',):
        old = BALLOON.format(i=ind)
        nb += new.count(old)
        new = new.replace(old, 'knight_taunt_balloon();\n')
    assert nb == 2, (k, nb)
    if k == 'cyan':
        assert new.count('cyandialoguecon = 1;') == 1
    R('D01-talk-' + k, k, ST, reg, new, why_lines)

# Cyan Knight: the joke narration after the first line names who is really there
R('D02-cyan-shake', 'cyan', ST,
  'global.battlemsg[0] = stringsetloc("* Ralsei shakes his head.&* Kris doesn\'t respond. They\'re dead.", "obj_knight_enemy_slash_Step_0_gml_518_0");',
  'global.battlemsg[0] = knight_cyan_shake(stringsetloc("* Ralsei shakes his head.&* Kris doesn\'t respond. They\'re dead.", "obj_knight_enemy_slash_Step_0_gml_518_0"));',
  'The joke narration after the first line ("Ralsei shakes his head. Kris doesn\'t respond.") names the members who are really there.')

# ---------- Kaizo Knight: the talk phase (its own party-aware Susie lines) ----------
t = T['kaizo'][ST]
a, b = region(t)
reg = t[a:b]
new = reg
g1 = '        if (practicemode || k_sideb || !scr_havechar(2))\n'
assert new.count(g1) == 1
new = new.replace(g1, '        if (practicemode || k_sideb || (!scr_havechar(2) && knight_taunt_who() == 0))\n')
g2 = '        if (scr_havechar(2) && (global.hp[2] > 0 || k_freeze[2]))\n'
assert new.count(g2) == 1
new = new.replace(g2, '        if (knight_taunt_begin_kz(!practicemode && !k_sideb, scr_havechar(2) && (global.hp[2] > 0 || k_freeze[2])))\n')
nk = [0]
def kz_plain(m):
    s = m.group(1)
    beat = BEAT.get(s)
    assert beat, s
    nk[0] += 1
    return 'msgsetloc(0, knight_taunt_line_kz("%s", "%s"), ' % (beat, s)
new = re.sub(r'msgsetloc\(0, ' + STR + r', ', kz_plain, new)
def kz_k(m):
    jp = m.group(1)
    beat = KZJ.get(jp)
    assert beat, jp
    nk[0] += 1
    return 'k_msgsetloc(0, knight_taunt_line_kz("%s", _line), "%s")' % (beat, jp)
new = re.sub(r'k_msgsetloc\(0, _line, ' + STR + r'\)', kz_k, new)
assert nk[0] == 17, nk[0]
g3 = '            if (k_freeze[2])\n            {\n                with (obj_herosusie)\n                {\n                    with (herofrozen)\n                    {\n                        scr_minishakeobj();\n                    }\n                }\n                createballoon = false;\n            }\n'
assert new.count(g3) == 1
new = new.replace(g3, '            if (knight_taunt_kz_frozen())\n            {\n                createballoon = false;\n            }\n')
nb = 0
for ind in ('                ', '            '):
    old = BALLOON.format(i=ind)
    nb += new.count(old)
    new = new.replace(old, 'knight_taunt_balloon();\n')
assert nb == 2, nb
R('D01-talk-kaizo', 'kaizo', ST, reg, new, why_lines + ' The Kaizo Knight\'s own frozen check applies to whoever speaks.')

# ---------- the narration before the Roaring ----------
why_pale = '"* Susie grew pale." / "struggled to give some kind of warning" named Susie even when she was not in the party: it names whoever is there.'
for k, cnt in (('base', 1), ('elec', 1), ('thorn', 2), ('cyan', 1)):
    R('D03-pale-cond-up-' + k, k, ST, r'phase4turn == 1 && global\.hp\[2\] > 0\)', 'phase4turn == 1 && knight_pale_up())', why_pale, regex=True, count=cnt)
    R('D03-pale-cond-down-' + k, k, ST, r'phase4turn == 1 && global\.hp\[2\] < 1\)', 'phase4turn == 1 && !knight_pale_up())', why_pale, regex=True, count=cnt)
    R('D03-pale-text-' + k, k, ST, r'stringsetloc\("\* Susie grew pale\.", "obj_knight_enemy_slash_Step_0_gml_548_0"\)', 'knight_pale_text(0, "Susie")', why_pale, regex=True, count=cnt)
    R('D03-pale-warn-' + k, k, ST, r'stringsetloc\("\* Susie struggled to give some kind of warning\.", "obj_knight_enemy_slash_Step_0_gml_317_0"\)', 'knight_pale_text(1, "Susie")', why_pale, regex=True, count=cnt)
R('D03-pale-cond-up-violet', 'violet', ST, r'phase4turn == 1 && global\.hp\[2\] > 0\)', 'phase4turn == 1 && knight_pale_up())', why_pale, regex=True, count=1)
R('D03-pale-cond-down-violet', 'violet', ST, r'phase4turn == 1 && global\.hp\[2\] < 1\)', 'phase4turn == 1 && !knight_pale_up())', why_pale, regex=True, count=1)
R('D03-pale-text-violet', 'violet', ST, 'stringsetsub("* ~1 grew pale.", susietitle)', 'stringsetsub("* ~1 grew pale.", knight_pale_name(susietitle))', why_pale)
R('D03-pale-warn-violet', 'violet', ST, 'stringsetsub("* ~1 struggled to give some kind of warning.", susietitle)',
  'stringsetsub("* ~1 struggled to give some kind of warning.", knight_pale_name(susietitle))', why_pale)

# ---------- Noelle's N-Action: the Angel's own words on a Weird Route save ----------
NA = ('        if (nactcount == 1)\n        {\n            msgset(0, "* " + global.charname[4] + " tried talking.../");\n'
      '            scr_anyface_next("noelle", "B");\n            msgnext("\\\\EB* U-um... h-hello? You d-don\'t have to do this...!/");\n'
      '            scr_anyface_next("noelle", "Y");\n            msgnext("\\\\EY* I don\'t know why you\'re so angry, but... p-please stop!/");\n'
      '            scr_anyface_next("none", 0);\n            msgnext("* (... but nothing happened.)/%");\n        }\n        else\n        {\n'
      '            msgset(0, "* " + global.charname[4] + " tried talking.../");\n            scr_anyface_next("noelle", "A");\n'
      '            msgnext("\\\\EA* U-umm... c-can we just talk about it...?/");\n            scr_anyface_next("none", 0);\n'
      '            msgnext("* (... but nothing happened.)/%");\n        }\n')
for k in K:
    R('D04-noe-act-' + k, k, ST, NA, '        knight_noe_act_text(nactcount);\n',
      'Noelle\'s N-Action: the same lines as before, and on a Weird Route save the Angel\'s own (her empty Chapter 2 faces).')

json.dump(rules, open(OUTF, 'w'), indent=1, ensure_ascii=False)
print(len(rules), 'rules')
