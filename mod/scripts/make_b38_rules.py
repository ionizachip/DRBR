"""Generate rules/b38_rules.json: build 38 (HoldBreath for everyone without Kris, the Violet Knight's Side B by party order with
Kris as a possible victim and the lone member's parry, the learned double moves cast in the spell phase, INFINITE HP).
The finds are checked against the text every earlier rule file leaves behind (b38 runs last)."""
import json, os, re, sys
sys.path.insert(0, '/home/claude/scripts')
import rules_apply
G = '/home/claude/work/gml/'
K = ['base', 'kaizo', 'elec', 'violet', 'thorn', 'cyan']
OUTF = '/home/claude/scripts/rules/b38_rules.json'

def ents(k):
    d = G + k + '/CodeEntries'
    return {f[:-4]: open(f'{d}/{f}', encoding='utf8', errors='replace').read() for f in os.listdir(d)}

_order = list(rules_apply.ORDER)
rules_apply.ORDER = _order[:_order.index('b38_rules.json')]   # only the rule files that run before this one
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

ST = 'gml_Object_obj_knight_enemy_'
NK = ['base', 'elec', 'violet', 'thorn', 'cyan']

# ---------- HoldBreath for everyone without Kris; the hub's S / R / N-Actions ----------
for k in NK:
    a = '        global.actcostnoe[myself][0] = 0;\n    }\n    if (global.monstertype[myself] == 105)'
    R('C01-hb-setup-' + k, k, 'gml_GlobalScript_scr_monstersetup', a,
      '        global.actcostnoe[myself][0] = 0;\n        knight_hb_setup("%s");\n    }\n    if (global.monstertype[myself] == 105)' % k,
      'Without Kris, Susie / Ralsei / Noelle each get HoldBreath on their own S / R / N-Action list (only Kris had it).')
for k in ['base', 'elec', 'thorn', 'cyan']:
    a = 'if (global.myfight == 3)\n{\n    xx = __view_get(e__VW.XView, 0);\n    yy = __view_get(e__VW.YView, 0);\n'
    R('C02-member-acts-' + k, k, ST + 'Step_0', a, a + '    knight_member_acts();\n',
      'HoldBreath and the learned moves (RUDER BUSTER, ICESTORM, FIRESTORM) run before the fight\'s own ACT code and use the action up.')
R('C02-member-acts-violet', 'violet', ST + 'Step_0', '    knight_vb_acts();\n', '    knight_vb_acts();\n    knight_member_acts();\n',
  'HoldBreath and the learned moves run right after the finisher (which may be the same learned move) and use the action up.')

# ---------- the Violet Knight's Side B by party order ----------
a = '    else\n    {\n        if (kill_target == obj_heronoelle)\n        {\n            with (obj_heronoelle)'
R('C03-vb-kris-hurt', 'violet', ST + 'Step_0', a, '    else if (kill_target == obj_herokris)\n    {\n        knight_vb_hurt_kris();\n    }\n' + a,
  'Kris can be taken when Kris is not on top: Kris\'s own hurt stance (the mod only knew Susie / Noelle / Ralsei here).')
a = '        var personwhosgonnadie = "ralsei";\n'
R('C04-vb-kris-who', 'violet', ST + 'Step_0', a, a + '        if (kill_target == obj_herokris)\n        {\n            personwhosgonnadie = "kris";\n        }\n',
  'Kris can be taken when Kris is not on top.')
a = '    if (personwhosabouttosuperdie == "noelle")\n    {\n        _cid = 4;\n        _obj = obj_heronoelle;\n    }\n'
R('C05-vb-kris-kill', 'violet', 'gml_GlobalScript_scr_complete_save_file', a,
  a + '    if (personwhosabouttosuperdie == "kris")\n    {\n        _cid = 1;\n        _obj = obj_herokris;\n    }\n',
  'Kris can be taken when Kris is not on top (the kill script defaulted to Ralsei).')
a = ('if (knightkillcon == 2 && kill_target == -4)\n{\n    kill_skipped = 1;\n    if (knight_vb_kris())\n    {\n        if (phase == 3)\n        {\n'
     '            kill_target = obj_herosusie;\n            knightkillcon = 30;\n        }\n        else\n        {\n            kill_target = obj_heroralsei;\n'
     '            snd_stop(global.batmusic[0]);\n            knightkillcon = 10;\n        }\n    }\n    else\n    {\n        if (phase < 3)\n'
     '            snd_stop(global.batmusic[0]);\n        knightkillcon = 10;\n    }\n}\n')
R('C06-vb-deflect', 'violet', ST + 'Step_0', a, 'if (knightkillcon == 2 && kill_target == -4)\n{\n    knight_vb_deflect_start();\n}\n',
  'Only the member on top is left: the Knight charges them and they knock the blade back (then what the mod did when nobody was left).')
a = ('        if (scr_havechar(2))\n        {\n            global.canact[myself][2] = 1;\n            global.actactor[myself][2] = 2;\n'
     '            global.actname[myself][2] = stringset("RedBuster");\n            global.actdesc[myself][2] = stringset("Red#Damage");\n'
     '            global.actcost[myself][2] = 150;\n            whatsact3 = "redbuster";\n        }\n')
R('C07-vb-no-redbuster', 'violet', ST + 'Step_0', a, '',
  'Susie learns RUDER BUSTER herself when Ralsei falls (build 38): no Kris RedBuster ACT after a loss any more.')
a = '        ralseidownmessage = true;\n        ral_dead = true;\n        with (obj_herosusie)'
R('C08-vb-raldead', 'violet', ST + 'Step_0', a,
  '        if (kill_target == obj_heroralsei || kill_skipped)\n        {\n            ralseidownmessage = true;\n            ral_dead = true;\n        }\n        with (obj_herosusie)',
  'With the party order the Angel can fall while Ralsei is still up: only mark Ralsei dead when it was him.')

# ---------- the learned double moves: the spell phase casts them twice ----------
for k in K:
    sp = 'gml_GlobalScript_scr_spell'
    a = ('                attack = instance_create(obj_herosusie.x, obj_herosusie.y, obj_rudebuster_anim);\n                attack.damage = damage;\n'
         '                attack.star = star;\n                attack.caster = caster;\n                attack.target = global.monsterinstance[star];\n')
    R('C09-ruder-' + k, k, sp, a,
      '                if (knight_dbl_take(caster, 4))\n                {\n                    global.spelldelay = 95;\n'
      '                    knight_kspell_start(8, caster, star, damage);\n                }\n                else\n                {\n'
      + ''.join('    ' + l + '\n' for l in a.rstrip('\n').split('\n')) + '                }\n',
      'RUDER BUSTER: two Rude Busters, the second 15 frames after the first (X-Slash\'s timing).')
    a = ('                attack = instance_create(global.monsterx[star], global.monstery[star], obj_icespell);\n                attack.damage = damage;\n'
         '                attack.star = star;\n                attack.caster = caster;\n                attack.target = global.monsterinstance[star];\n')
    R('C10-icestorm-' + k, k, sp, a,
      '                if (knight_dbl_take(caster, 9))\n                {\n                    global.spelldelay = 70;\n'
      '                    knight_kspell_start(9, caster, star, damage);\n                }\n                else\n                {\n'
      + ''.join('    ' + l + '\n' for l in a.rstrip('\n').split('\n')) + '                }\n',
      'ICESTORM: two Ice Shocks at X-Slash\'s timing.')
    a = '                global.spelldelay = 80;\n                knight_kspell_start(5, caster, star, damage);\n'
    R('C11-firestorm-' + k, k, sp, a,
      a + '                if (knight_dbl_take(caster, 13))\n                {\n                    global.knight_ks.dbl = 1;\n                    global.spelldelay = 100;\n                }\n',
      'FIRESTORM: Ralsei throws a second fireball 15 frames after the first.')
    for ev in ('Alarm_0', 'Step_0'):
        R('C12-dbl-text-%s-%s' % (ev, k), k, 'gml_Object_obj_spellphase_' + ev, r'scr_spelltext\(global\.charspecial\[(\w+)\], (\w+)\);',
          r'scr_spelltext(global.charspecial[\1], \2);\n knight_dbl_text(\2);',
          'The spell phase\'s line names the learned move (RUDER BUSTER, ICESTORM, FIRESTORM).', regex=True, count=2)

# ---------- Supercharged Knight: a Kris the Weird Route took counts as gone (UNLEASH, RaiseKris) ----------
R('C18-elec-kris-create', 'elec', ST + 'Create_0', r'scr_havechar\(1\)', 'knight_kris_here()',
  'When the Weird Route has taken Kris (not on top), the last phase hands UNLEASH to the others like a party without Kris.', regex=True, count=2)
R('C19-elec-kris-step', 'elec', ST + 'Step_0', r'scr_havechar\(1\)', 'knight_kris_here()',
  'A Kris the Weird Route took cannot be raised by RaiseKris / ReviveKris; the S/R-Actions work as without Kris.', regex=True, count=6)

# ---------- INFINITE HP ----------
for k in K:
    for e in ('scr_damage', 'scr_damage_fixed', 'scr_damage_maxhp', 'scr_damage_proportional', 'scr_damage_sneo_final_attack'):
        ent = 'gml_GlobalScript_' + e
        if ent not in T[k] or not re.search(r'global\.hp\[chartarget\] -= ([^;\n]+);', T[k][ent]):
            continue
        R('C13-infhp-%s-%s' % (e, k), k, ent, r'global\.hp\[chartarget\] -= ([^;\n]+);', r'global.hp[chartarget] -= knight_infhp_cut(\1);',
          'INFINITE HP: a hit still lands (number, flash, No-Hit) but takes no HP, so nobody goes down.', regex=True)
    bc = 'gml_Object_obj_battlecontroller_Step_0'
    R('C14-infhp-drain-' + k, k, bc, r'global\.hp\[(\d)\]--;', r'global.hp[\1] -= knight_infhp_cut(1);',
      'INFINITE HP: the ThornRing\'s drain takes nothing.', regex=True)
R('C15-infhp-kz-snowgrave', 'kaizo', ST + 'Step_0', 'global.hp[_char] -= _frdmg;', 'global.hp[_char] -= knight_infhp_cut(_frdmg);',
  'INFINITE HP: the SnowGrave the Kaizo Knight turns back takes nothing.')
R('C16-infhp-kz-gloom', 'kaizo', ST + 'Step_2', 'global.hp[i]--;', 'global.hp[i] -= knight_infhp_cut(1);',
  'INFINITE HP: GLOOM drains nothing.')
for e in ('scr_damage', 'scr_damage_maxhp'):
    R('C17-infhp-kz-gloomadd-' + e, 'kaizo', 'gml_GlobalScript_' + e, 'obj_knight_enemy.k_gloom[chartarget] += _gloomdmg;',
      'obj_knight_enemy.k_gloom[chartarget] += knight_infhp_cut(_gloomdmg);', 'INFINITE HP: hits build no GLOOM.')

json.dump(rules, open(OUTF, 'w'), indent=1)
print(len(rules), 'rules')
