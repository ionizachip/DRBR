"""Scan variant-dispatched objects: instance variables a variant's Create sets that other variants' Creates do not.
When the Tag Team / Attack Remix lineup switches global.knight_variant mid-battle, instances that were created under another
variant still exist (battle controller, heroes, the arena cutscene...). Their events now run the new variant's code, which may read
variables only that variant's Create sets. This lists them (and their initialisers) so they can be filled in on the switch.
usage: python3 lu_fill_scan.py [--json out.json] [--objects a,b,c]"""
import os, re, sys, json
sys.path.insert(0, '/home/claude/scripts')
from vtext import vtext, split_cases, KEYS, M

ASSIGN = re.compile(r'^(\s*)([A-Za-z_][A-Za-z0-9_]*)\s*=(?!=)\s*(.*)$')
SKIP = {'var', 'global', 'other', 'self', 'if', 'else', 'for', 'while', 'with', 'return', 'switch', 'case', 'repeat', 'do'}


def create_vars(text):
    """{name: (indent, rhs_first_line, is_method)} for assignments to plain instance variables (any depth)."""
    out = {}
    lines = text.split('\n')
    for i, ln in enumerate(lines):
        m = ASSIGN.match(ln)
        if not m:
            continue
        ind, name, rhs = m.group(1), m.group(2), m.group(3)
        if name in SKIP or name.startswith('_'):
            continue
        meth = rhs.strip().startswith('function')
        if name not in out:
            out[name] = (len(ind), rhs.strip(), meth, i)
    return out


def var_objects():
    objs = set()
    for fn in os.listdir(M):
        m = re.match(r'gml_Object_(.+)_Create_0\.gml$', fn)
        if not m:
            continue
        t = open(M + fn, encoding='utf8').read()
        if split_cases(t) is not None:
            objs.add(m.group(1))
    return sorted(objs)


SAFE_CALL = {'make_color_rgb', 'merge_color', 'make_colour_rgb', 'array_create', 'string', 'real', 'floor', 'ceil', 'round', 'abs', 'max', 'min',
             'irandom', 'random', 'choose', 'ds_list_create', 'ds_map_create', 'ds_grid_create', 'variable_instance_exists', 'i_ex', 'instance_exists',
             'sprite_get_width', 'sprite_get_height', 'camerax', 'cameray', 'is_english', 'pcolor', 'k_stringsetloc', 'stringsetloc', 'snd_init'}


def classify(rhs):
    r = rhs.rstrip(';').strip()
    if r.startswith('function'):
        return 'method'
    if re.fullmatch(r'-?\d+(\.\d+)?|true|false|noone|undefined|-4|"[^"]*"|c_[a-z_]+|pi', r):
        return 'lit'
    if r.startswith('[') or r.startswith('{'):
        if 'instance_create' in r or 'scr_' in r:
            return 'unsafe'
        return 'lit'
    calls = re.findall(r'\b([A-Za-z_][A-Za-z0-9_]*)\s*\(', r)
    bad = [c for c in calls if c not in SAFE_CALL]
    if bad:
        return 'unsafe:' + ','.join(sorted(set(bad)))
    return 'expr'


def scan(objs=None):
    res = {}
    for o in (objs or var_objects()):
        f = M + 'gml_Object_%s_Create_0.gml' % o
        if not os.path.exists(f):
            continue
        per = {k: create_vars(vtext(f, k)) for k in KEYS}
        allv = set().union(*[set(v) for v in per.values()])
        common = set.intersection(*[set(v) for v in per.values()])
        diff = sorted(allv - common)
        if not diff:
            continue
        res[o] = {}
        for k in KEYS:
            mine = [(n, per[k][n]) for n in diff if n in per[k]]
            if mine:
                res[o][k] = [{'name': n, 'depth': d[0], 'rhs': d[1], 'kind': classify(d[1])} for n, d in mine]
    return res


if __name__ == '__main__':
    objs = None
    if '--objects' in sys.argv:
        objs = sys.argv[sys.argv.index('--objects') + 1].split(',')
    r = scan(objs)
    if '--json' in sys.argv:
        json.dump(r, open(sys.argv[sys.argv.index('--json') + 1], 'w'), indent=1)
    for o, d in r.items():
        print('==', o)
        for k, l in d.items():
            print('   ', k, ', '.join('%s[%s]' % (x['name'], x['kind'][:12]) for x in l))
