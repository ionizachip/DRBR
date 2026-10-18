"""Build 50: the players' attack skills use the Roaring Knights' REAL attack objects - wrapped, never changed for the fight.

A skill sent to you is made in your game only (build 49), from the Knights' own attack objects (the tracking sword, the
pointing star, the rotating slash, the falling sword, the crescent, ...). Those objects were written for the Knight's own
turn, so this step wraps them (the wrappers live in online_sent50.gml) without changing what the Knight's fight does:

  1. ISOLATION. A sent instance carries kbrx (its send's number). Every `with (X)`, instance_number(X), instance_exists(X),
     i_ex(X) and instance_find(X, n) on one of the reachable attack objects X - in ANY object's code - only sees the
     instances of the caller's own side: the Knight's managers never see (move, launch, count, destroy) a sent instance and a
     sent instance never sees the Knight's. Offline (global.kbr_san == 0) every wrapper is the plain built-in.
  2. In the code of the reachable attack objects themselves:
     - the first line of every Create event adopts the new instance into its maker's send (kbr_ev_cr: the maker is `other`,
       the instance that called instance_create, or the send being started); its variant, colour, damage, sender, target and
       its own random stream come with it;
     - global.knight_variant reads become kbr_kv() (a sent instance keeps the variant of the knight it came from, whatever
       knight is fighting now);
     - snd_* calls go through kbr_snd_* (sent sounds are quieter and never pile up; a sent instance never stops the
       Knight's own sounds);
     - global.turntimer: a sent instance never changes the Knight's turn timer (a graze on a sent sword took time off the
       Knight's attack) and always reads a running turn;
     - get_swordcolor() / pcolor(): the sender's colour mixed in for a sent instance;
     - `with (obj_growtangle)` / `with (obj_knight_enemy)`: a sent instance never shakes the box or touches the Knight.
Idempotent (build/merged is kept between runs). Writes the changed entries into build/merged (vanilla ones copied in).
"""
import os, re, json

M = '/home/claude/work/build/merged/'
B = '/home/claude/work/gml/base/CodeEntries/'
REPORT = '/home/claude/work/online/det_sent_report.json'

# the objects a send creates itself (online_sent50.gml); the reachable set is computed from them
LEAVES = ['obj_tracking_sword1', 'obj_knight_pointing_star', 'obj_roaringknight_slash', 'obj_knight_circle', 'obj_diagonal_bullet__v1',
          'obj_roaringknight_split_bullet', 'obj_knight_weird_circle', 'obj_bullet_knightcrescent', 'obj_fallingsword__v1',
          'obj_knight_lightningshock', 'obj_roaringknight_fountain_bullet']
# build 52: Jevil's pieces that his sends put up (online_sent50.gml, ids 26-31; make_jevil.py)
LEAVES += ['obj_jv_spadering', 'obj_jv_dvert', 'obj_jv_clubs', 'obj_jv_carousel', 'obj_jv_cscythe', 'obj_jv_suitbomb']
# helpers the attack code makes for its sent instances (adopted, so they are cleaned up with the send)
HELP = ['obj_lerpvar', 'obj_script_delayed', 'obj_afterimage', 'obj_afterimage_grow', 'obj_particle_generic']

EV = re.compile(r'^gml_Object_(.+?)_(Create|Step|Draw|Alarm|Other|Collision|Destroy|CleanUp|PreCreate)_(.+)\.gml$')
CR = re.compile(r'(?:instance_create(?:_depth|_layer)?|scr_childbullet|scr_fire_bullet|scr_bulletspawner)\s*\([^;]*?\b(obj_[A-Za-z0-9_]+)')
PRO = 'if (global.kbr_san > 0)\n    kbr_ev_cr();\n'
# every other event (not Draw) of the attack objects says whose side is running now (kbr_ev_in): the adoption's fallback
# when the runner does not tell a Create who made it
PRO2 = 'if (global.kbr_san > 0)\n    kbr_ev_in();\n'
SND = {'snd_play': 'kbr_snd_play', 'snd_play_x': 'kbr_snd_play_x', 'snd_stop': 'kbr_snd_stop', 'snd_pitch': 'kbr_snd_pitch',
       'snd_volume': 'kbr_snd_volume', 'snd_loop': 'kbr_snd_loop', 'get_swordcolor': 'kbr_swordcolor', 'pcolor': 'kbr_pcolor'}
SNDRE = re.compile(r'(?<![\w.$@])(' + '|'.join(sorted(SND, key=len, reverse=True)) + r')(\s*\()')


def all_files():
    files = {}
    for d in (B, M):
        for f in os.listdir(d):
            files[f] = d + f
    return files


def parents():
    par = {}
    for ln in open('/home/claude/work/idx/objparents.tsv'):
        p = ln.rstrip('\n').split('\t')
        if len(p) >= 3 and p[2]:
            par[p[1]] = p[2]
    return par


def sent_set(files):
    code = {}
    for f in files:
        m = EV.match(f)
        if m:
            code.setdefault(m.group(1), []).append(f)
    seen = set()
    st = list(LEAVES)
    while st:
        o = st.pop()
        if o in seen:
            continue
        seen.add(o)
        for f in code.get(o, []):
            for c in CR.findall(open(files[f], encoding='utf8', errors='replace').read()):
                if c not in seen and c in code:
                    st.append(c)
    return seen, code


def code_only(text, fn):
    """apply fn to the code parts of text (not strings, not comments)"""
    out = []
    i = 0
    n = len(text)
    s = 0
    while i < n:
        c = text[i]
        if c == '"' or (c == '@' and i + 1 < n and text[i + 1] in '"\''):
            out.append(fn(text[s:i]))
            j = i + (2 if c == '@' else 1)
            q = text[j - 1]
            while j < n:
                if text[j] == '\\' and c != '@':
                    j += 2
                    continue
                if text[j] == q:
                    j += 1
                    break
                j += 1
            out.append(text[i:j])
            i = s = j
            continue
        if c == '/' and i + 1 < n and text[i + 1] in '/*':
            out.append(fn(text[s:i]))
            if text[i + 1] == '/':
                j = text.find('\n', i)
                j = n if j < 0 else j
            else:
                j = text.find('*/', i + 2)
                j = n if j < 0 else j + 2
            out.append(text[i:j])
            i = s = j
            continue
        i += 1
    out.append(fn(text[s:]))
    return ''.join(out)


def isolate(seg, names):
    alt = '|'.join(sorted(names, key=len, reverse=True))
    seg = re.sub(r'\bwith\s*\(\s*(' + alt + r')\s*\)(?!\s*if \(kbr_ns\(\)\))', lambda m: 'with (' + m.group(1) + ') if (kbr_ns())', seg)
    seg = re.sub(r'(?<![\w.])(instance_number|instance_exists|i_ex)\s*\(\s*(' + alt + r')\s*\)',
                 lambda m: ('kbr_inum(' if m.group(1) == 'instance_number' else 'kbr_iex(') + m.group(2) + ')', seg)
    seg = re.sub(r'(?<![\w.])instance_find\s*\(\s*(' + alt + r')\s*,', lambda m: 'kbr_ifind(' + m.group(1) + ',', seg)
    return seg


def own(seg):
    seg = re.sub(r'global\.knight_variant(?!\s*=[^=])', 'kbr_kv()', seg)
    seg = SNDRE.sub(lambda m: SND[m.group(1)] + m.group(2), seg)
    seg = re.sub(r'global\.turntimer\s*([-+])=\s*(?![ \t]|kbr_mine\(\))([^;\n]+);', lambda m: 'global.turntimer ' + m.group(1) + '= kbr_mine() * (' + m.group(2) + ');', seg)
    seg = re.sub(r'global\.turntimer(?!\s*[-+*/]?=[^=])', 'kbr_tt()', seg)
    # the Roaring routes a hit through the Knight (its event_user(2)): a sent instance's hit is an ordinary hit
    seg = re.sub(r'(?<![\w.])i_ex\(\s*(obj_knight_roaring[23])\s*\)(?! && kbr_mine\(\)\))', lambda m: '(i_ex(' + m.group(1) + ') && kbr_mine())', seg)
    return seg


def main(check=False):
    files = all_files()
    S, code = sent_set(files)
    par = parents()
    anc = set()
    for o in S:
        q = par.get(o)
        while q:
            anc.add(q)
            q = par.get(q)
    pro_objs = S | anc | set(HELP)
    import det_rewrite
    side_objs = S | det_rewrite.objects()
    rep = {'sent': sorted(S), 'prologue': [], 'isolated': [], 'own': []}
    # (assignments to global.turntimer that are not -= / += would need a statement guard: there must be none)
    for o in S:
        for f in code.get(o, []):
            t = open(files[f], encoding='utf8', errors='replace').read()
            assert not re.search(r'global\.turntimer\s*[*/]?=[^=]', t), 'a plain turntimer write in ' + f
    for f in sorted(files):
        m = EV.match(f)
        if not m:
            continue
        o = m.group(1)
        t = open(files[f], encoding='utf8', errors='replace').read()
        t2 = code_only(t, lambda s: isolate(s, S))
        if o in S:
            t2 = code_only(t2, lambda s: isolate(own(s), {'obj_growtangle', 'obj_knight_enemy'}))
        if o in pro_objs and m.group(2) == 'Create' and 'kbr_ev_cr()' not in t2:
            t2 = PRO + t2
            rep['prologue'].append(f)
        if o in side_objs and m.group(2) not in ('Create', 'Draw', 'PreCreate') and 'kbr_ev_in()' not in t2:
            t2 = PRO2 + t2
            rep.setdefault('side', []).append(f)
        if t2 != t:
            if o in S:
                rep['own'].append(f)
            else:
                rep['isolated'].append(f)
            if not check:
                open(M + f, 'w', encoding='utf8').write(t2)
    rep['hooks'] = hooks(check)
    if not check:
        json.dump(rep, open(REPORT, 'w'), indent=1)
    print('det sent: %d reachable attack objects, %d Create prologues, %d own entries, %d other entries isolated%s'
          % (len(S), len(rep['prologue']), len(rep['own']), len(rep['isolated']), ' (check only)' if check else ''))
    return rep


def hooks(check):
    """build 50: the TP bar asks kbr_tp_hook first (online it is the skill meter); the party's HP bar draws the SHIELD"""
    out = []
    files = all_files()
    f = 'gml_Object_obj_tensionbar_Draw_0.gml'
    t = open(files[f], encoding='utf8').read()
    if 'kbr_tp_hook()' not in t:
        t = 'if (kbr_tp_hook())\n    exit;\n' + t
        out.append(f)
        if not check:
            open(M + f, 'w', encoding='utf8').write(t)
    f = 'gml_GlobalScript_scr_charbox.gml'
    t = open(files[f], encoding='utf8').read()
    if 'kbr_shield_draw(' not in t:
        line = 'draw_rectangle(xx + 128 + xchunk, bpoff + b_offset + 11 + mmy[_sl], xx + xchunk + 128 + ceil((global.hp[c + 1] / global.maxhp[c + 1]) * 75), bpoff + b_offset + 19 + mmy[_sl], false);'
        n = t.count(line)
        assert n >= 5, 'scr_charbox HP bar lines: %d' % n
        t = re.sub(r'([ \t]*)' + re.escape(line), lambda m: m.group(0) + '\n' + m.group(1) + 'kbr_shield_draw(xx + xchunk, bpoff + b_offset + mmy[_sl], c);', t)
        out.append(f)
        if not check:
            open(M + f, 'w', encoding='utf8').write(t)
    out += flowery_hooks(check)
    out += skin_hooks(check)
    out += watch_hooks(check)
    return out


def watch_hooks(check):
    """DRBR 1.0.3: the HP panel while you watch someone - your box is theirs: its HP numbers, their colour at a quarter, the
    red at 0 and the bar read their HP through kbr_cb_hp / kbr_cb_mhp (online_skin52.gml; the game's own HP everywhere else).
    Reads build/merged (after skin_hooks)."""
    out = []
    f = 'gml_GlobalScript_scr_charbox.gml'
    t = open(M + f, encoding='utf8').read()
    if 'kbr_cb_hp(' in t:
        return out
    pairs = [
        ('if ((global.hp[c + 1] / global.maxhp[c + 1]) <= 0.25)', 'if ((kbr_cb_hp(c + 1) / kbr_cb_mhp(c + 1)) <= 0.25)'),
        ('if (global.hp[c + 1] <= 0)', 'if (kbr_cb_hp(c + 1) <= 0)'),
        ('string_hash_to_newline(global.hp[c + 1])', 'string_hash_to_newline(kbr_cb_hp(c + 1))'),
        ('string_hash_to_newline(global.maxhp[c + 1])', 'string_hash_to_newline(kbr_cb_mhp(c + 1))'),
        ('if (global.hp[c + 1] > 0 && global.maxhp[c + 1] > 0)', 'if (kbr_cb_hp(c + 1) > 0 && kbr_cb_mhp(c + 1) > 0)'),
        ('ceil((global.hp[c + 1] / global.maxhp[c + 1]) * 75)', 'ceil((kbr_cb_hp(c + 1) / kbr_cb_mhp(c + 1)) * 75)'),
    ]
    for a, b in pairs:
        n = t.count(a)
        assert n >= 5, 'watch hook %r: %d' % (a, n)
        t = t.replace(a, b)
    out.append(f)
    if not check:
        open(M + f, 'w', encoding='utf8').write(t)
    return out


def skin_hooks(check):
    """build 52: the HP panel online - your own head (the look's for an online-only skin) and YOUR NAME in the battle-name
    lettering (kbr_charbox: when it drew them, the game's own head / name sprites for that box are skipped), and an
    online-only look's own HP colour (kbr_charbox_col). Reads build/merged (after flowery_hooks)."""
    out = []
    f = 'gml_GlobalScript_scr_charbox.gml'
    t = open(M + f, encoding='utf8').read()
    if 'kbr_charbox(' in t:
        return out
    hd = re.compile(r'( *)if \(c == 0\)\n\1\{\n\1    draw_sprite\(spr_headkris, ')
    n = len(hd.findall(t))
    assert n >= 5, 'skin hook heads %d' % n
    t = hd.sub(lambda m: m.group(1) + 'kbr_charbox(c + 1, global.faceaction[charpos[c]], xx + 13 + xchunk, bpoff + b_offset + mmy[_sl], xx + 51 + xchunk, bpoff + b_offset + 3 + mmy[_sl]);\n' + m.group(0).replace('if (c == 0)', 'if (c == 0 && !global.kbr_cbx)'), t)
    for k in (1, 2, 3):
        t = re.sub(r'if \(c == %d\)(\n *\{\n *draw_sprite\(spr_head)' % k, lambda m: 'if (c == %d && !global.kbr_cbx)' % k + m.group(1), t)
    t = t.replace('if (c >= 4)\n', 'IFCC\n')
    # the custom characters' box (c >= 4) only where it draws the head: its colour line stays as it was
    t = re.sub(r'IFCC(\n *\{\n *knight_cc_charbox\()', lambda m: 'if (c >= 4 && !global.kbr_cbx)' + m.group(1), t)
    t = t.replace('IFCC\n', 'if (c >= 4)\n')
    col = re.compile(r'( *)if \(c >= 4\)\n\1\{\n\1    charcolor = knight_cc_hpcolor\(c \+ 1\);\n\1\}\n')
    n = len(col.findall(t))
    assert n >= 5, 'skin hook colour %d' % n
    t = col.sub(lambda m: m.group(0) + m.group(1) + 'charcolor = kbr_charbox_col(c + 1, charcolor);\n', t)
    out.append(f)
    if not check:
        open(M + f, 'w', encoding='utf8').write(t)
    return out


def flowery_hooks(check):
    """build 50: CUSTOM CHARACTERS (char ids 5 and up; Flowery is 5) - their own place in the game's battle code, looked up in
    one registry (cc50.gml), so a new character needs no new engine hook:
      - technique ids 16-39 in scr_spellinfo / scr_spell / scr_spelltext -> knight_cc_spellinfo / _spell / _spelltext;
      - gear ids 30-35 in scr_weaponinfo / scr_armorinfo -> knight_cc_weaponinfo / _armorinfo;
      - the battle makes the hero (obj_knight_herocc, a child of obj_heroparent) for a char >= 5;
      - their HP-bar colour (hpcolor[id - 1]), head and name in the HP-bar box, their FIGHT bar colour, damage-number colour;
      - their first MAGIC entry (their own ACTION, e.g. Flowery's F-Action) in the ACT colour;
      - the knights' per-character arrays (k_gloom, k_freeze, ...) get room for them.
    Upgrades build/merged from the earlier Flowery-in-Noelle's-slot hooks (those are taken out)."""
    out = []
    files = all_files()
    OLD = ''.join('        case %d:\n' % i for i in range(16, 22))
    CASES = ''.join('        case %d:\n' % i for i in range(16, 40))
    GCASES = ''.join('        case %d:\n' % i for i in range(30, 36))
    def put(name, t):
        out.append(name)
        if not check:
            open(M + name, 'w', encoding='utf8').write(t)
    for name, sw, oldbody, body in (
            ('gml_GlobalScript_scr_spellinfo.gml', '    switch (arg0)\n    {\n', '            knight_fl_spellinfo(arg0);\n            break;\n', '            knight_cc_spellinfo(arg0);\n            break;\n'),
            ('gml_GlobalScript_scr_spell.gml', '    switch (spell)\n    {\n', '            knight_fl_spell(spell, caster, star);\n            break;\n', '            knight_cc_spell(spell, caster, star);\n            break;\n'),
            ('gml_GlobalScript_scr_spelltext.gml', '    switch (spell)\n    {\n', '            global.msg[0] = knight_fl_spelltext(spell);\n            break;\n', '            global.msg[0] = knight_cc_spelltext(spell);\n            break;\n')):
        t = open(files[name], encoding='utf8').read()
        if 'knight_cc_' in t:
            continue
        if OLD + oldbody in t:
            t = t.replace(OLD + oldbody, CASES + body)
        else:
            assert t.count(sw) >= 1, name
            t = t.replace(sw, sw + CASES + body)
        put(name, t)
    for name, body in (('gml_GlobalScript_scr_weaponinfo.gml', '            knight_cc_weaponinfo(arg0);\n            break;\n'),
                       ('gml_GlobalScript_scr_armorinfo.gml', '            knight_cc_armorinfo(arg0);\n            break;\n')):
        t = open(files[name], encoding='utf8').read()
        if 'knight_cc_' in t:
            continue
        sw = '    switch (arg0)\n    {\n'
        assert t.count(sw) >= 3, name
        t = t.replace(sw, sw + GCASES + body)
        put(name, t)
    # the HP-bar box: the old hooks out (Noelle's own head and name again), the custom characters' colour, head and name in
    f = 'gml_GlobalScript_scr_charbox.gml'
    t = open(files[f], encoding='utf8').read()
    if 'knight_cc_charbox(' not in t:
        t = t.replace('knight_fl_head(_sl, spr_headnoelle, ', 'draw_sprite(spr_headnoelle, ')
        t = t.replace('knight_fl_bname(_sl, scr_84_get_sprite("spr_bnamenoelle"), ', 'draw_sprite(scr_84_get_sprite("spr_bnamenoelle"), ')
        col = re.compile(r'( *)if \(c == 3\)\n\1\{\n\1    charcolor = hpcolor\[3\];\n\1\}\n')
        n = len(col.findall(t))
        assert n >= 5, 'charbox colour %d' % n
        t = col.sub(lambda m: m.group(0) + m.group(1) + 'if (c >= 4)\n' + m.group(1) + '{\n' + m.group(1) + '    charcolor = knight_cc_hpcolor(c + 1);\n' + m.group(1) + '}\n', t)
        hd = re.compile(r'( *)draw_sprite\(scr_84_get_sprite\("spr_bnamenoelle"\), 0, xx \+ 51 \+ xchunk, bpoff \+ b_offset \+ 3 \+ mmy\[_sl\]\);\n( *)\}\n')
        n = len(hd.findall(t))
        assert n >= 5, 'charbox heads %d' % n
        def _hd(m):
            ind = m.group(2)
            return (m.group(0) + ind + 'if (c >= 4)\n' + ind + '{\n' + ind + '    knight_cc_charbox(c + 1, global.faceaction[charpos[c]], xx + 13 + xchunk, bpoff + b_offset + mmy[_sl], xx + 51 + xchunk, bpoff + b_offset + 3 + mmy[_sl]);\n' + ind + '}\n')
        t = hd.sub(_hd, t)
        put(f, t)
    # the battle: the hero of a custom character; the HP-bar colours (battle and dark menu)
    f = 'gml_Object_obj_battlecontroller_Create_0.gml'
    t = open(files[f], encoding='utf8').read()
    if 'knight_cc_hero_make(' not in t:
        mk = re.compile(r'( *)global\.charinstance\[i\]\.char = 4;\n\1global\.charinstance\[i\]\.depth = 200 - \(i \* 20\);\n( *)\}\n')
        n = len(mk.findall(t))
        assert n >= 2, 'hero make %d' % n
        t = mk.sub(lambda m: m.group(0) + m.group(2) + 'if (global.char[i] >= 5)\n' + m.group(2) + '{\n' + m.group(2) + '    knight_cc_hero_make(i);\n' + m.group(2) + '}\n', t)
        put(f, t)
    # build 50: a solo party stands level with the knight (the middle place), not at the top place
    for f in ('gml_Object_obj_battlecontroller_Create_0.gml',):
        t = open(M + f if f in out and not check else files[f], encoding='utf8').read()
        if 'knight_solo_lineup()' in t:
            continue
        sl = re.compile(r'( *)mmy\[0\] = 0;\n')
        n = len(sl.findall(t))
        assert n >= 2, 'solo lineup %d' % n
        t = sl.sub(lambda m: m.group(1) + 'knight_solo_lineup();\n' + m.group(0), t)
        put(f, t)
    for f in ('gml_Object_obj_battlecontroller_Create_0.gml',):
        t = open(M + f if f in out and not check else files[f], encoding='utf8').read()
        if 'knight_cc_hpcolors()' in t:
            continue
        hc = re.compile(r'( *)hpcolor\[3\] = c_yellow;\n\1for \(i = 0; i < 4; i\+\+\)\n')
        n = len(hc.findall(t))
        assert n >= 2, 'hpcolor %s %d' % (f, n)
        t = hc.sub(lambda m: m.group(1) + 'hpcolor[3] = c_yellow;\n' + m.group(1) + 'knight_cc_hpcolors();\n' + m.group(1) + 'for (i = 0; i < array_length(hpcolor); i++)\n', t)
        put(f, t)
    # damage numbers: a custom character's own colour type
    for f in sorted(files):
        if not f.endswith('.gml'):
            continue
        t = open(M + f if (f in out and not check) else files[f], encoding='utf8').read()
        if 'knight_cc_dmtype(' in t:
            continue
        t2 = re.sub(r'\b(\w+)\.type = (char|global\.char\[\w+\]) - 1;', r'\1.type = knight_cc_dmtype(\2);', t)
        if t2 != t:
            put(f, t2)
    # the FIGHT bar box colour
    f = 'gml_Object_obj_attackpress_Draw_0.gml'
    t = open(files[f], encoding='utf8').read()
    if 'knight_cc_barcolor(' not in t:
        br = re.compile(r'( *)draw_rectangle\(x \+ 78, y \+ \(38 \* i\), x \+ 80 \+ \(15 \* boltspeed\), y \+ \(38 \* i\) \+ 36, true\);\n')
        n = len(br.findall(t))
        assert n >= 2, 'attackpress %d' % n
        t = br.sub(lambda m: m.group(1) + 'if (j >= 5)\n' + m.group(1) + '    draw_set_color(knight_cc_barcolor(j));\n' + m.group(0), t)
        put(f, t)
    # the FIGHT bar panel: a custom character's own head picture and bar end (the game's frame for its number would wrap to Kris)
    f = 'gml_Object_obj_attackpress_Draw_0.gml'
    t = open(M + f if (f in out and not check) else files[f], encoding='utf8').read()
    if 'knight_cc_pressfront(' not in t:
        n1 = t.count('draw_sprite(spr_pressfront, j - 1, x, y + (38 * i));')
        n2 = t.count('draw_sprite(spr_pressspot, j - 1, x + 80, y + (38 * i));')
        assert n1 >= 2 and n2 >= 2, 'pressfront %d %d' % (n1, n2)
        t = t.replace('draw_sprite(spr_pressfront, j - 1, x, y + (38 * i));', 'knight_cc_pressfront(j, x, y + (38 * i));')
        t = t.replace('draw_sprite(spr_pressspot, j - 1, x + 80, y + (38 * i));', 'knight_cc_pressspot(j, x + 80, y + (38 * i));')
        put(f, t)
    # a FIGHT hit by a custom character: its own hit effect and swing sound (where the game picks Susie's / Ralsei's / Noelle's)
    for f in ('gml_Object_obj_heroparent_Step_0.gml', 'gml_Object_obj_heroparent_Other_10.gml'):
        t = open(M + f if (f in out and not check) else files[f], encoding='utf8').read()
        if 'knight_cc_attack_fx(' in t:
            continue
        fx = re.compile(r'( *)if \(object_index == obj_heronoelle\)\n\1\{\n\1    attack\.sprite_index = spr_attack_slap2;')
        sd = re.compile(r'( *)if \(object_index == obj_heronoelle\)\n\1\{\n\1    ls = snd_play\(snd_laz_c\);')
        n1 = len(fx.findall(t)); n2 = len(sd.findall(t))
        assert n1 >= 2, 'attack fx %s %d' % (f, n1)
        t = fx.sub(lambda m: m.group(1) + 'if (char >= 5)\n' + m.group(1) + '    knight_cc_attack_fx(attack, char);\n' + m.group(0), t)
        t = sd.sub(lambda m: m.group(1) + 'if (char >= 5)\n' + m.group(1) + '    knight_cc_attack_snd(char);\n' + m.group(0), t)
        put(f, t)
    # MAGIC menu: the character's own ACTION (first entry) in the ACT colour
    f = 'gml_GlobalScript_scr_spellmenu_setup.gml'
    t = open(files[f], encoding='utf8').read()
    if 'knight_cc_menu_special(' not in t:
        ms = re.compile(r'( *)global\.battlespell\[__i\]\[__fj\] = 0;\n')
        n = len(ms.findall(t))
        assert n >= 2, 'spellmenu %d' % n
        t = ms.sub(lambda m: m.group(0) + m.group(1) + 'knight_cc_menu_special(__i, __fj);\n', t)
        put(f, t)
    # the overworld followers: a custom character in the party (hub fights only) follows as itself - the game would make
    # nothing for it (obj_darkcontroller) or Berdly (scr_makecaterpillar's number 5)
    f = 'gml_Object_obj_darkcontroller_Create_0.gml'
    t = open(M + f if (f in out and not check) else files[f], encoding='utf8').read()
    if 'knight_cc_follower(' not in t:
        fo = re.compile(r'( *)global\.faceaction\[i\] = 0;\n')
        n = len(fo.findall(t))
        assert n >= 3, 'darkcontroller followers %d' % n
        t = fo.sub(lambda m: m.group(0) + m.group(1) + 'knight_cc_follower(i);\n', t)
        put(f, t)
    f = 'gml_GlobalScript_scr_makecaterpillar.gml'
    t = open(M + f if (f in out and not check) else files[f], encoding='utf8').read()
    if 'knight_cc_cater_dress(' not in t:
        a0 = '    global.cinstance[arg3].target = 12 + (arg3 * 12);\n'
        assert t.count(a0) == 1, 'makecaterpillar'
        t = t.replace(a0, a0 + '    if (knight_cc_ok(arg2) && knight_active())\n    {\n        knight_cc_cater_dress(global.cinstance[arg3], arg2);\n        return global.cinstance[arg3];\n    }\n')
        put(f, t)
    # the text system: a custom character's face (\\F code, fc 23 = Flowery, Chapter 5's number) and voice (\\T code: typer
    # 300 / 301 / 302 = his voice in the light world / dark world / a fight), his face drawn, his voice blip (Chapter 5's)
    for f in ('gml_Object_obj_writer_Draw_0.gml', 'gml_Object_obj_writer_Other_15.gml'):
        t = open(M + f if (f in out and not check) else files[f], encoding='utf8').read()
        if 'knight_cc_face_code(' in t:
            continue
        fq = re.compile(r'( *)if \(nextchar2 == "Q"\)\n\1\{\n\1    global\.fc = 21;\n\1\}\n')
        n = len(fq.findall(t))
        assert n >= 1, 'writer face %s %d' % (f, n)
        t = fq.sub(lambda m: m.group(0) + m.group(1) + 'knight_cc_face_code(nextchar2);\n', t)
        tq = re.compile(r'( *)if \(nextchar2 == "N"\)\n\1\{\n\1    global\.typer = 12;\n')
        t = tq.sub(lambda m: m.group(1) + 'if (knight_cc_typer_code(nextchar2))\n' + m.group(1) + '{\n' + m.group(1) + '    scr_texttype();\n' + m.group(1) + '}\n' + m.group(0), t)
        put(f, t)
    f = 'gml_Object_obj_face_Draw_0.gml'
    t = open(M + f if (f in out and not check) else files[f], encoding='utf8').read()
    if 'knight_cc_face_draw(' not in t:
        a0 = '\nnowface = global.fc;'
        assert t.count(a0) == 1, 'face draw'
        t = t.replace(a0, '\nknight_cc_face_draw(x, y, f);' + a0)
        put(f, t)
    f = 'gml_GlobalScript_scr_texttype.gml'
    t = open(M + f if (f in out and not check) else files[f], encoding='utf8').read()
    if 'knight_cc_texttype(' not in t:
        c12 = re.compile(r'( *)case 12:\n')
        n = len(c12.findall(t))
        assert n >= 2, 'texttype %d' % n
        t = c12.sub(lambda m: m.group(1) + 'case 300:\n' + m.group(1) + 'case 301:\n' + m.group(1) + 'case 302:\n' + m.group(1) + 'case 303:\n' + m.group(1) + '    knight_cc_texttype(global.typer);\n' + m.group(1) + '    break;\n' + m.group(0), t)
        put(f, t)
    if 'case 303:' not in t:
        a3 = re.compile(r'( *)case 302:\n')
        assert a3.search(t), 'texttype 303'
        t = a3.sub(lambda m: m.group(0) + m.group(1) + 'case 303:\n', t)
        put(f, t)
    f = 'gml_GlobalScript_scr_textsound.gml'
    t = open(M + f if (f in out and not check) else files[f], encoding='utf8').read()
    if 'knight_cc_textsound(' not in t:
        a0 = '            else\n            {\n                snd_play(textsound);\n            }\n'
        assert t.count(a0) == 1, 'textsound'
        t = t.replace(a0, '            else if (!knight_cc_textsound(textsound))\n            {\n                snd_play(textsound);\n            }\n')
        put(f, t)
    # a custom character's spell line in battle: the battle writer made with its face, expression and voice from the start
    # (a face switched on mid-text puts only the first line beside the face)
    for f in ('gml_Object_obj_spellphase_Step_0.gml', 'gml_Object_obj_spellphase_Alarm_0.gml'):
        t = open(M + f if (f in out and not check) else files[f], encoding='utf8').read()
        if 'knight_cc_battletext(' not in t:
            a0 = 'spellwriter = scr_battletext_default();'
            assert t.count(a0) >= 1, 'spellwriter ' + f
            t = t.replace(a0, 'spellwriter = knight_cc_battletext();')
            put(f, t)
    # ... and its narration ("(Everyone's TP went up!)") as a page of its own, after the line is closed: no face, the
    # battle's own text voice
    f = 'gml_Object_obj_spellphase_Step_0.gml'
    t = open(M + f if (f in out and not check) else files[f], encoding='utf8').read()
    if 'knight_cc_narrate(' not in t:
        t = 'knight_cc_narrate();\n' + t
        put(f, t)
    # the knights' per-character arrays: room for char 5
    for f in ('gml_Object_obj_knight_enemy_Create_0.gml', 'gml_Object_obj_knight_enemy_Step_0.gml'):
        t = open(M + f if (f in out and not check) else files[f], encoding='utf8').read()
        t2 = re.sub(r'\b(k_freeze|k_gemit|k_gloom|k_glt|k_gtext) = \[0, 0, 0, 0, 0\];', r'\1 = [0, 0, 0, 0, 0, 0];', t)
        if t2 != t:
            put(f, t2)
    return out


if __name__ == '__main__':
    import sys
    main('--check' in sys.argv)
