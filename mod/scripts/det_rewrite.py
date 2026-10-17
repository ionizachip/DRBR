"""Build 45: the Knight attacks' randomness, made shareable.

Every online game runs the Knights' attack code itself. For the parts of an attack that are not aimed at your SOUL to land
in the same places in every game, the attack code must draw its random numbers from one stream that every game seeds the
same way at the start of each attack - not from GameMaker's own generator, which the rest of the game (party animations,
graze sparkles, hits...) also uses, differently in every game.

This step rewrites the attack objects' code (the objects the online attacks really make, measured in the emulator by
tests/br_measure.py, plus the knight and the bullet controller) so that random / irandom / random_range / irandom_range /
choose / ds_list_shuffle / array_shuffle / randomize / random_set_seed call kbr_random & co. (online_br.gml). Those behave
exactly like the built-ins outside an online battle, so the offline fights do not change.

Left alone on purpose: Draw events (looks only), the hit event (Other_15: runs only in the game whose SOUL was hit),
collisions with the SOUL, and every object of the player's own side (SOUL, graze box, damage numbers, heroes...).

Writes the rewritten code entries into build/merged (vanilla entries get copied in), idempotent.
Usage: python3 det_rewrite.py [--check]   (--check: report only, write nothing)
"""
import json, os, re, sys

M = '/home/claude/work/build/merged/'
B = '/home/claude/work/gml/base/CodeEntries/'
CAT = '/home/claude/work/online/br_catalogue.json'
REPORT = '/home/claude/work/online/det_rewrite_report.json'

RNG = {'random': 'kbr_random', 'irandom': 'kbr_irandom', 'random_range': 'kbr_random_range', 'irandom_range': 'kbr_irandom_range',
       'choose': 'kbr_choose', 'ds_list_shuffle': 'kbr_list_shuffle', 'array_shuffle': 'kbr_array_shuffle',
       'randomize': 'kbr_randomize', 'random_set_seed': 'kbr_random_set_seed'}
CALL = re.compile(r'(?<![\w.$@])(' + '|'.join(sorted(RNG, key=len, reverse=True)) + r')(\s*\()')

# the player's side, the battle's frame and the hub's own objects: never part of the shared stream
EXCLUDE = {'obj_heart', 'obj_grazebox', 'obj_dmgwriter', 'obj_healanim', 'obj_moveheart', 'obj_returnheart', 'obj_heroparent',
           'obj_herokris', 'obj_herosusie', 'obj_heroralsei', 'obj_heronoelle', 'obj_writer', 'obj_face', 'obj_smallface',
           'obj_battlecontroller', 'obj_shake', 'obj_knight_ctrl', 'obj_knight_menu', 'obj_knight_prompt', 'obj_knight_bench',
           'obj_knight_ghost_kris', 'obj_knight_ghost_susie', 'obj_knight_ghost_ralsei', 'obj_knight_herocc', 'obj_knight_omega', 'obj_darkener', 'obj_fadein',
           'obj_deathanim', 'obj_battle_cleanup', 'obj_tensionbar', 'obj_battleback', 'obj_mainchara', 'obj_caterpillarchara',
           'obj_knight_twin', 'obj_knight_twin_bullet', 'obj_dmgwriter_boss', 'obj_heart_follower', 'obj_heart_follower_overshoot',
           'obj_heartburst', 'obj_hurtbox'}
# the knight and the bullet controller are always in, whatever the catalogue says
ALWAYS = {'obj_knight_enemy', 'obj_dbulletcontroller'}
# Draw events are looks only - except these, whose Draw fires bullets (Light Orb's star bullets)
DRAW_LOGIC = {'obj_knight_lightorb'}
# global scripts only the attack code calls that pick something at random for it
SCRIPTS = ['gml_GlobalScript_scr_getlaunchdirection.gml']

EV = re.compile(r'^gml_Object_(.+?)_(Create|Step|Draw|Alarm|Other|Collision|Destroy|CleanUp|PreCreate)_(.+)\.gml$')


def knight_reach():
    """objects the knight's own code (not the shared bullet controller) can make, transitively"""
    files = {}
    for d in (B, M):
        for f in os.listdir(d):
            files[f] = d + f
    code = {}
    for f in files:
        m = EV.match(f)
        if m:
            code.setdefault(m.group(1), []).append(f)
    seen = set()
    stack = ['obj_knight_enemy']
    while stack:
        o = stack.pop()
        if o in seen:
            continue
        seen.add(o)
        for f in code.get(o, []):
            t = open(files[f], encoding='utf8', errors='replace').read()
            for c in re.findall(r'(?:instance_create(?:_depth|_layer)?|scr_bulletspawner|scr_fire_bullet)\s*\([^;]*?\b(obj_[A-Za-z0-9_]+)', t):
                if c not in seen and c != 'obj_dbulletcontroller':
                    stack.append(c)
    return seen


def objects():
    objs = set(ALWAYS) | knight_reach()
    if os.path.exists(CAT):
        cat = json.load(open(CAT))
        for reg, lst in cat.items():
            for a in lst:
                objs |= set(a.get('objs', []))
    # parents (their inherited events run as part of the child)
    par = {}
    for ln in open('/home/claude/work/idx/objparents.tsv'):
        p = ln.rstrip('\n').split('\t')
        if len(p) >= 3 and p[2]:
            par[p[1]] = p[2]
    more = set()
    for o in objs:
        q = par.get(o)
        while q and q not in more and q not in objs:
            more.add(q)
            q = par.get(q)
    objs |= more
    return {o for o in objs if o not in EXCLUDE and not o.startswith('obj_hero')}


def skip_event(obj, ev, sub):
    if ev == 'Draw':
        return obj not in DRAW_LOGIC
    if ev == 'Other' and sub == '15':
        return True
    if ev == 'Collision' and ('obj_heart' in sub or 'obj_grazebox' in sub):
        return True
    return False


def rewrite(text):
    """replace RNG calls outside strings and comments; returns (new_text, count)"""
    out = []
    i = 0
    n = len(text)
    cnt = 0
    code_start = 0

    def flush(seg):
        nonlocal cnt
        def rep(m):
            nonlocal cnt
            cnt += 1
            return RNG[m.group(1)] + m.group(2)
        return CALL.sub(rep, seg)

    while i < n:
        c = text[i]
        if c == '"' or (c == '@' and i + 1 < n and text[i + 1] in '"\''):
            out.append(flush(text[code_start:i]))
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
            i = j
            code_start = i
            continue
        if c == '/' and i + 1 < n and text[i + 1] == '/':
            out.append(flush(text[code_start:i]))
            j = text.find('\n', i)
            j = n if j < 0 else j
            out.append(text[i:j])
            i = j
            code_start = i
            continue
        if c == '/' and i + 1 < n and text[i + 1] == '*':
            out.append(flush(text[code_start:i]))
            j = text.find('*/', i + 2)
            j = n if j < 0 else j + 2
            out.append(text[i:j])
            i = j
            code_start = i
            continue
        i += 1
    out.append(flush(text[code_start:]))
    return ''.join(out), cnt


def main(check=False):
    objs = objects()
    files = {}
    for d in (B, M):
        for f in os.listdir(d):
            files[f] = d + f
    rep = {'objects': sorted(objs), 'files': {}, 'skipped_events': [], 'total': 0}
    nfiles = 0
    for f in sorted(files):
        m = EV.match(f)
        if not m or m.group(1) not in objs:
            continue
        if skip_event(m.group(1), m.group(2), m.group(3)):
            t = open(files[f], encoding='utf8', errors='replace').read()
            if CALL.search(t):
                rep['skipped_events'].append(f)
            continue
        t = open(files[f], encoding='utf8', errors='replace').read()
        t2, cnt = rewrite(t)
        if cnt == 0:
            continue
        rep['files'][f] = cnt
        rep['total'] += cnt
        nfiles += 1
        if not check:
            open(M + f, 'w', encoding='utf8').write(t2)
    for f in SCRIPTS:
        t = open(files[f], encoding='utf8', errors='replace').read()
        t2, cnt = rewrite(t)
        if cnt:
            rep['files'][f] = cnt
            rep['total'] += cnt
            nfiles += 1
            if not check:
                open(M + f, 'w', encoding='utf8').write(t2)
    json.dump(rep, open(REPORT, 'w'), indent=1)
    print('det rewrite: %d objects, %d files, %d random calls -> kbr_*%s' % (len(objs), nfiles, rep['total'], ' (check only)' if check else ''))
    return rep


if __name__ == '__main__':
    main('--check' in sys.argv)
