"""Cross-variant variable scan for the Tag Team / Attack Remix lineups (build 42).

In a lineup battle the host knight's fight made every world object (the arena cutscene obj_ch3_PTB02, the battle controller,
the heroes, the tension bar, the sign ...) under the host's variant. A partner knight is then made under its own variant, and
while it is in front global.knight_variant is the partner's, so every variant-dispatched event of those host-made objects runs
the partner's code. Whatever the partner's code reads on them that only the partner's own code would have set is a
"not set before reading it" crash in the real game (build 41: obj_ch3_PTB02.nokaizo in Violet Knight's Create).

This scan lists, for every partner variant v and host h != v, the instance variables v's code READS on an object Q that h's code
(and the shared base-game / hub code) never ASSIGNS on Q. It also lists globals v reads that are only assigned in v-specific code.
Reads are found in: Q's own events under v, `Q.var` anywhere in v's code, `with (Q) { ... }` blocks in v's code, and (unknown
target) v's script code.

usage: python3 lu_cross_scan.py [--json out.json] [--brief]"""
import os, re, sys, json
from collections import defaultdict
sys.path.insert(0, '/home/claude/scripts')
from vtext import split_cases, KEYS, M

B = '/home/claude/work/gml/base/CodeEntries/'
EVRE = re.compile(r'^gml_Object_(.+?)_(Create|Step|Draw|Alarm|Other|Destroy|CleanUp|Collision|PreCreate|KeyPress|KeyRelease|Keyboard|Mouse|Gesture)_(.+)\.gml$')
KW = {'var', 'global', 'other', 'self', 'if', 'else', 'for', 'while', 'with', 'return', 'switch', 'case', 'repeat', 'do', 'until', 'break',
      'continue', 'exit', 'default', 'function', 'new', 'delete', 'true', 'false', 'undefined', 'noone', 'all', 'and', 'or', 'not', 'div',
      'mod', 'static', 'try', 'catch', 'finally', 'throw', 'enum', 'constructor', 'argument', 'argument_count', 'infinity', 'NaN', 'pi',
      'begin', 'end', 'then', 'xor'}
BUILTIN = set('''x y xstart ystart xprevious yprevious depth visible persistent solid sprite_index image_index image_speed image_xscale
image_yscale image_angle image_alpha image_blend image_number sprite_width sprite_height sprite_xoffset sprite_yoffset mask_index direction
speed hspeed vspeed gravity gravity_direction friction alarm id object_index layer path_index path_position path_speed path_scale
path_orientation path_endaction path_positionprevious timeline_index timeline_position timeline_speed timeline_running timeline_loop
bbox_left bbox_right bbox_top bbox_bottom instance_count room room_speed room_width room_height fps fps_real current_time delta_time
mouse_x mouse_y keyboard_key keyboard_lastkey keyboard_lastchar keyboard_string event_type event_number event_object event_action
async_load os_type working_directory program_directory temp_directory game_save_id application_surface health score lives
in_sequence drawn_by_sequence image_number view_current view_xview view_yview view_wview view_hview'''.split())


def strip_code(t):
    """comments and string contents removed (strings become "")"""
    out = []
    i = 0
    n = len(t)
    while i < n:
        c = t[i]
        if c == '/' and i + 1 < n and t[i + 1] == '/':
            j = t.find('\n', i)
            i = n if j < 0 else j
            continue
        if c == '/' and i + 1 < n and t[i + 1] == '*':
            j = t.find('*/', i + 2)
            i = n if j < 0 else j + 2
            continue
        if c == '"' or (c == '@' and i + 1 < n and t[i + 1] == '"'):
            if c == '@':
                i += 1
            j = i + 1
            while j < n and t[j] != '"':
                if t[j] == '\\' and c != '@':
                    j += 1
                j += 1
            out.append('""')
            i = j + 1
            continue
        out.append(c)
        i += 1
    return ''.join(out)


def script_units(text):
    """GlobalScript file -> ({variant index: [function bodies]} for dispatched names, [shared bodies])"""
    lines = text.split('\n')
    funcs = {}
    order = []
    i = 0
    while i < len(lines):
        m = re.match(r'^function (\w+)\s*\(([^)]*)\)', lines[i])
        if m:
            name = m.group(1)
            j = i + 1
            while j < len(lines) and lines[j] != '}':
                j += 1
            funcs[name] = '\n'.join(lines[i:j + 1])
            order.append(name)
            i = j + 1
            continue
        i += 1
    per = defaultdict(list)
    shared = []
    used = set()
    for name in order:
        body = funcs[name]
        if 'switch (global.knight_variant)' in body and 'script_execute_ext(' in body:
            cases = re.findall(r'case (\d+):\s*\n\s*return script_execute_ext\((\w+), _a\);', body)
            dm = re.search(r'default:\s*\n\s*return script_execute_ext\((\w+), _a\);', body)
            got = {int(a): b for a, b in cases}
            for vi in range(len(KEYS)):
                g = got.get(vi, dm.group(1) if dm else None)
                if g and g in funcs:
                    per[vi].append(funcs[g])
                    used.add(g)
            used.add(name)
    for name in order:
        if name not in used:
            shared.append(funcs[name])
    # top-level statements (outside functions) run once at game start for every variant
    top = []
    depth = 0
    for ln in lines:
        if re.match(r'^function \w+', ln):
            depth = 1
            continue
        if depth:
            if ln == '}':
                depth = 0
            continue
        top.append(ln)
    shared.append('\n'.join(top))
    return per, shared


IDENT = re.compile(r'[A-Za-z_][A-Za-z0-9_]*')


class Unit:
    """one piece of code and the object its bare names belong to (None = unknown caller)"""
    def __init__(self, text, obj, where):
        self.text = strip_code(text)
        self.obj = obj
        self.where = where


def analyse(unit, objects, scripts, sink_r, sink_w, sink_gr, sink_gw):
    """record reads / writes: sink_r[obj][name] -> [where], sink_w[obj] -> {names}; obj None = unknown target"""
    lines = unit.text.split('\n')
    # locals: every `var` name in the unit (GML locals are function-wide; units are whole events / functions)
    locs = set()
    for m in re.finditer(r'\bvar\s+([^;]+);', unit.text):
        for part in re.split(r',(?![^(\[]*[)\]])', m.group(1)):
            mm = re.match(r'\s*([A-Za-z_]\w*)', part)
            if mm:
                locs.add(mm.group(1))
    for m in re.finditer(r'\bfunction\s*\w*\s*\(([^)]*)\)', unit.text):
        for a in m.group(1).split(','):
            a = a.split('=')[0].strip()
            if a:
                locs.add(a)
    for m in re.finditer(r'\bcatch\s*\(\s*(\w+)\s*\)', unit.text):
        locs.add(m.group(1))
    stack = []          # (kind, target) per open brace
    pending = None      # target of a `with` whose block / statement comes next
    single = None       # target for exactly one following statement line (with without braces)
    for ln_no, raw in enumerate(lines):
        ln = raw.strip()
        if not ln:
            continue
        cur_target = unit.obj
        for k, tg in stack:
            if k == 'with':
                cur_target = tg
        line_target = cur_target
        if single is not None and ln != '{':
            line_target = single
            single = None
        mw = re.match(r'^with \((.*)\)$', ln)
        if mw:
            e = mw.group(1).strip()
            if e in objects:
                pending = e
            elif e in ('self',):
                pending = line_target
            else:
                pending = '?'
            continue
        if ln == '{':
            if pending is not None:
                stack.append(('with', pending))
                pending = None
            else:
                stack.append(('blk', None))
            continue
        if ln.startswith('}'):
            if stack:
                stack.pop()
            continue
        if pending is not None:
            # with without braces: this line runs on the with target
            line_target = pending
            pending = None
        tgt = line_target
        # a method body defined inside an event runs on the instance it is bound to (the event's object): keep tgt
        # writes at statement start
        wm = re.match(r'^(?:var\s+)?([A-Za-z_]\w*)\s*(=|\+=|-=|\*=|/=|\|=|&=|\^=|\+\+|--)(?!=)', ln)
        written = None
        if wm and not ln.startswith('var '):
            nm = wm.group(1)
            if nm not in KW and nm not in locs and nm not in objects and nm not in scripts:
                written = nm
                sink_w[tgt].add(nm)
                if wm.group(2) not in ('=',):
                    sink_r[tgt][nm].append('%s:%d' % (unit.where, ln_no + 1))
        for gm in re.finditer(r'\bglobal\.([A-Za-z_]\w*)\s*(=(?!=)|\+=|-=|\+\+|--)?', ln):
            if gm.group(2) == '=':
                # assignment unless it is a comparison inside an expression (the decompiler always writes == there)
                sink_gw.add(gm.group(1))
            else:
                sink_gr[gm.group(1)].append('%s:%d' % (unit.where, ln_no + 1))
        # obj.member reads / writes
        for om in re.finditer(r'(?<![\w.])([A-Za-z_]\w*)\.([A-Za-z_]\w*)(\s*(?:=(?!=)|\+=|-=|\*=|/=))?', ln):
            a, b, asg = om.group(1), om.group(2), om.group(3)
            if a in objects:
                if asg and asg.strip() == '=':
                    sink_w[a].add(b)
                else:
                    sink_r[a][b].append('%s:%d' % (unit.where, ln_no + 1))
            elif a == 'self':
                if asg and asg.strip() == '=':
                    sink_w[tgt].add(b)
                else:
                    sink_r[tgt][b].append('%s:%d' % (unit.where, ln_no + 1))
        # bare reads
        body = ln
        if written:
            body = re.sub(r'^\s*' + re.escape(written) + r'\s*(=|\+=|-=|\*=|/=|\|=|&=|\^=|\+\+|--)', ' ', body, count=1)
        body = re.sub(r'^var\s+', '', body)
        # drop struct-literal keys  { key: ... , key2: ... }
        body = re.sub(r'([{,]\s*)([A-Za-z_]\w*)\s*:(?!=)', r'\1 :', body)
        for im in IDENT.finditer(body):
            nm = im.group(0)
            s, e = im.start(), im.end()
            if s > 0 and body[s - 1] == '.':
                continue                     # member of something else
            rest = body[e:].lstrip()
            if rest.startswith('('):
                # a call: a script / built-in function, or a method kept in an instance variable (a read of that variable)
                if nm in scripts or nm in KW or nm in locs or nm in objects or nm not in METHOD_NAMES:
                    continue
                sink_r[tgt][nm].append('%s:%d' % (unit.where, ln_no + 1))
                continue
            if rest.startswith('.') and nm in objects:
                continue                     # obj.member (handled above)
            if nm in KW or nm in locs or nm in objects or nm in scripts or nm in BUILTIN or nm == 'global' or nm[0].isdigit():
                continue
            if re.match(r'^(case|default)\b', ln) and nm == ln.split()[1:2]:
                continue
            sink_r[tgt][nm].append('%s:%d' % (unit.where, ln_no + 1))


METHOD_NAMES = set()


def find_method_names():
    """instance variables that are assigned a method somewhere (name = function(...) / method(...))"""
    out = set()
    for d in (M, B):
        for fn in os.listdir(d):
            if not fn.endswith('.gml'):
                continue
            t = open(d + fn, encoding='utf8', errors='replace').read()
            for m in re.finditer(r'^\s*(?:self\.)?([A-Za-z_]\w*)\s*=\s*(?:function\b|method\()', t, re.M):
                out.add(m.group(1))
            for m in re.finditer(r'\b[A-Za-z_]\w*\.([A-Za-z_]\w*)\s*=\s*(?:function\b|method\()', t):
                out.add(m.group(1))
    return out


def collect():
    METHOD_NAMES.update(find_method_names())
    objects = set()
    scripts = set()
    for ln in open('/home/claude/work/idx/merged.tsv'):
        p = ln.rstrip('\n').split('\t')
        if len(p) >= 3:
            (objects if p[0] == 'obj' else scripts).add(p[2])
    for fn in os.listdir(M):
        m = EVRE.match(fn)
        if m:
            objects.add(m.group(1))
    for d in (M, B):
        for fn in os.listdir(d):
            for f in re.findall(r'^function (\w+)', open(d + fn, encoding='utf8', errors='replace').read(), re.M) if fn.startswith('gml_GlobalScript_') else []:
                scripts.add(f)
    parents = {}
    for ln in open('/home/claude/work/idx/objparents.tsv'):
        p = ln.rstrip('\n').split('\t')
        if len(p) >= 3 and p[2]:
            parents[p[1]] = p[2]
    merged_files = set(os.listdir(M))
    # per variant reads/writes
    R = {k: defaultdict(lambda: defaultdict(list)) for k in KEYS}
    W = {k: defaultdict(set) for k in KEYS}
    GR = {k: defaultdict(list) for k in KEYS}
    GW = {k: set() for k in KEYS}
    CR = defaultdict(lambda: defaultdict(list))
    CW = defaultdict(set)
    CGR = defaultdict(list)
    CGW = set()
    global HR, HW, HGR, HGW
    HR = defaultdict(lambda: defaultdict(list))
    HW = defaultdict(set)
    HGR = defaultdict(list)
    HGW = set()
    for fn in sorted(merged_files):
        t = open(M + fn, encoding='utf8', errors='replace').read()
        m = EVRE.match(fn)
        if m:
            obj = m.group(1)
            sc = split_cases(t)
            if sc is None:
                analyse(Unit(t, obj, fn[:-4]), objects, scripts, CR, CW, CGR, CGW)
            else:
                cases, dflt = sc
                for vi, k in enumerate(KEYS):
                    body = cases.get(vi, dflt)
                    if body is not None:
                        analyse(Unit(body, obj, fn[:-4] + '@' + k), objects, scripts, R[k], W[k], GR[k], GW[k])
        elif fn.startswith('gml_GlobalScript_'):
            per, shared = script_units(t)
            if fn == 'gml_GlobalScript_knight_core.gml':
                # the hub: its function writes are timing-dependent (the lineup fill), so they are kept apart; its top-level
                # statements run at game start (the last shared unit) and count as shared
                for body in shared[:-1]:
                    analyse(Unit(body, None, fn[:-4]), objects, scripts, HR, HW, HGR, HGW)
                analyse(Unit(shared[-1], None, fn[:-4] + ':top'), objects, scripts, CR, CW, CGR, CGW)
                continue
            for body in shared:
                analyse(Unit(body, None, fn[:-4]), objects, scripts, CR, CW, CGR, CGW)
            for vi, bodies in per.items():
                k = KEYS[vi]
                for body in bodies:
                    analyse(Unit(body, None, fn[:-4] + '@' + k), objects, scripts, R[k], W[k], GR[k], GW[k])
    # base-game code that the merge did not replace: the same for every variant
    for fn in sorted(os.listdir(B)):
        if fn in merged_files:
            continue
        t = open(B + fn, encoding='utf8', errors='replace').read()
        m = EVRE.match(fn)
        if m:
            analyse(Unit(t, m.group(1), 'base:' + fn[:-4]), objects, scripts, CR, CW, CGR, CGW)
        elif fn.startswith('gml_GlobalScript_'):
            analyse(Unit(t, None, 'base:' + fn[:-4]), objects, scripts, CR, CW, CGR, CGW)
    return objects, scripts, parents, R, W, GR, GW, CR, CW, CGR, CGW


def chain(o, parents):
    out = [o]
    seen = {o}
    while o in parents and parents[o] not in seen:
        o = parents[o]
        out.append(o)
        seen.add(o)
    return out


OWNED_PREFIX = ('obj_knight_enemy', 'obj_roaringknight_', 'obj_tracking_sword', 'obj_sword_tunnel', 'obj_sword_vortex', 'obj_bullet_knight',
                'obj_diagonal_bullet', 'obj_elecknight', 'obj_bgfountaintest', 'obj_glitchyknight', 'obj_kaizoknight', 'obj_blocktree_bg',
                'obj_deathanim', 'obj_not_stolen_from_kaizo', 'obj_violet_insert_text', 'obj_forcefield', 'obj_fallingsword',
                'obj_endthefuckingturn', 'obj_purify_event', 'obj_dbullet_maker')


def report(brief=False):
    objects, scripts, parents, R, W, GR, GW, CR, CW, CGR, CGW = collect()
    out = {'inst': [], 'glob': []}
    # instance variables
    allobjs = set()
    for k in KEYS:
        allobjs |= set(R[k].keys())
    for q in sorted(o for o in allobjs if o):
        if q.startswith(OWNED_PREFIX) and q != 'obj_knight_enemy':
            continue
        if q == 'obj_knight_enemy':
            continue
        anc = chain(q, parents)
        for v in KEYS:
            reads = R[v].get(q, {})
            if not reads:
                continue
            for h in KEYS:
                if h == v:
                    continue
                have = set(BUILTIN)
                for a in anc:
                    have |= W[h].get(a, set()) | CW.get(a, set())
                miss = sorted(n for n in reads if n not in have)
                # only names some code assigns on this object (else it is not an instance variable of it: a constant / asset)
                assigned_any = set()
                for a in anc:
                    for k in KEYS:
                        assigned_any |= W[k].get(a, set())
                    assigned_any |= CW.get(a, set())
                miss = [n for n in miss if n in assigned_any]
                for n in miss:
                    out['inst'].append({'partner': v, 'host': h, 'obj': q, 'var': n, 'at': reads[n][:4]})
    # globals
    for v in KEYS:
        for g, locs in GR[v].items():
            if g in CGW:
                continue
            for h in KEYS:
                if h == v or g in GW[h]:
                    continue
                if g in GW[v]:
                    out['glob'].append({'partner': v, 'host': h, 'var': g, 'at': locs[:4]})
    return out


if __name__ == '__main__':
    r = report()
    if '--json' in sys.argv:
        json.dump(r, open(sys.argv[sys.argv.index('--json') + 1], 'w'), indent=1)
    by = defaultdict(set)
    for e in r['inst']:
        by[(e['partner'], e['obj'], e['var'])].add(e['host'])
    print('INSTANCE VARIABLES a partner reads on host-made objects (partner, object, var: hosts):')
    for (v, q, n), hs in sorted(by.items()):
        ex = next(e['at'] for e in r['inst'] if e['partner'] == v and e['obj'] == q and e['var'] == n)
        print('  %-7s %-34s %-28s hosts=%s  at %s' % (v, q, n, ','.join(sorted(hs)), ex[0]))
    gb = defaultdict(set)
    for e in r['glob']:
        gb[(e['partner'], e['var'])].add(e['host'])
    print('GLOBALS a partner reads that only its own code assigns (partner, var: hosts):')
    for (v, n), hs in sorted(gb.items()):
        ex = next(e['at'] for e in r['glob'] if e['partner'] == v and e['var'] == n)
        print('  %-7s %-34s hosts=%s  at %s' % (v, n, ','.join(sorted(hs)), ex[0]))


# ---------- focused report: the objects that live through a lineup battle ----------
MECH = ['obj_battlecontroller', 'obj_tensionbar', 'obj_heroparent', 'obj_herokris', 'obj_herosusie', 'obj_heroralsei', 'obj_heronoelle',
        'obj_writer', 'obj_face', 'obj_battleback', 'obj_knight_ctrl', 'obj_mainchara', 'obj_caterpillarchara']
WORLD = ['obj_ch3_PTB02', 'obj_ch3_PTB02_roaringknight', 'obj_ch3_PTB02_roaringknight_pull_test', 'obj_ch3_PTB02_roaringknight_speardodge_sequence',
         'obj_npc_sign', 'obj_darkcontroller', 'obj_cutscene_master', 'obj_savepoint', 'obj_marker', 'obj_actor']


def focused():
    objects, scripts, parents, R, W, GR, GW, CR, CW, CGR, CGW = collect()
    rows = []
    for q in MECH + WORLD:
        anc = chain(q, parents)
        for v in KEYS:
            reads = R[v].get(q, {})
            for n, locs in reads.items():
                if n in BUILTIN:
                    continue
                # pinned world objects run their creator's code: only reads from outside the object's own events count
                if q in WORLD:
                    locs = [l for l in locs if not l.startswith('gml_Object_%s_' % q)]
                    if not locs:
                        continue
                hosts = []
                for h in KEYS:
                    if h == v:
                        continue
                    have = set()
                    for a in anc:
                        have |= W[h].get(a, set()) | CW.get(a, set())
                    if n not in have:
                        hosts.append(h)
                if not hosts:
                    continue
                anyw = set()
                for a in anc:
                    for k in KEYS:
                        anyw |= W[k].get(a, set())
                    anyw |= CW.get(a, set())
                if n not in anyw and n not in HW.get(q, set()):
                    continue
                cov = any(n in HW.get(a, set()) for a in anc)
                rows.append((q, v, n, hosts, cov, locs[:3]))
    return rows


if __name__ == '__main__' and '--focused' in sys.argv:
    for q, v, n, hosts, cov, locs in focused():
        print('%-34s %-7s %-26s hosts=%-30s %s %s' % (q, v, n, ','.join(hosts), 'FILLED' if cov else 'MISSING', locs))
