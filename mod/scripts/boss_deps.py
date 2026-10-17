"""DRBR: what a set of source objects / scripts of another chapter needs (for make_<boss>.py).
Usage: python3 boss_deps.py <src c2|c4|c5> obj1 obj2 ... [--scripts scr_a,scr_b]
Prints, for every identifier the code uses: objects, sprites, sounds, scripts/functions - each marked
  IMPORT (in the set), CH3 (the built Chapter 3 mod has it), MISSING (needs importing or a stand-in);
and the raw numeric asset ids (where the decompiler wrote a number: instance_create(..., 745), snd_play(371) ...)."""
import os, re, sys, glob

SRC = '/home/claude/work/src/'
BUILT = '/home/claude/work/src/built/'
BASE = '/home/claude/work/gml/base/CodeEntries/'


def assets(p):
    t = {'obj': {}, 'spr': {}, 'snd': {}, 'shd': {}, 'bg': {}}
    idx = {'obj': [], 'spr': [], 'snd': [], 'shd': [], 'bg': []}
    for l in open(p, encoding='utf8'):
        r = l.rstrip('\n').split('\t')
        if r[0] in t:
            t[r[0]][r[1]] = r[2:]
            idx[r[0]].append(r[1])
    return t, idx


def strip(t):
    t = re.sub(r'"(?:\\.|[^"\\])*"', '""', t)
    t = re.sub(r'//[^\n]*', '', t)
    return re.sub(r'/\*.*?\*/', '', t, flags=re.S)


def main():
    src = sys.argv[1]
    objs = [a for a in sys.argv[2:] if not a.startswith('--')]
    scrs = []
    if '--scripts' in sys.argv:
        scrs = sys.argv[sys.argv.index('--scripts') + 1].split(',')
        objs = [o for o in objs if o not in scrs]
    S, SI = assets(SRC + src + '/assets.tsv')
    B, _ = assets(BUILT + 'assets.tsv')
    code = {}
    for o in objs:
        for f in glob.glob(SRC + src + '/code/gml_Object_%s_*.gml' % o):
            n = os.path.basename(f)[len('gml_Object_%s_' % o):-4]
            if re.match(r'^(Create|Step|Draw|Alarm|Other|Destroy|Collision|CleanUp)_', n):
                code['%s.%s' % (o, n)] = open(f, encoding='utf8', errors='replace').read()
    for s in scrs:
        f = SRC + src + '/code/gml_GlobalScript_%s.gml' % s
        if os.path.exists(f):
            code[s] = open(f, encoding='utf8', errors='replace').read()
    ch3_funcs = set()
    for f in glob.glob(BUILT + 'code/gml_GlobalScript_*.gml'):
        ch3_funcs |= set(re.findall(r'\bfunction\s+(\w+)', open(f, encoding='utf8', errors='replace').read()))
    rs = set(l.strip() for l in open('/home/claude/work/runner_strings.txt', encoding='latin1'))
    src_funcs = {}
    for f in glob.glob(SRC + src + '/code/gml_GlobalScript_*.gml'):
        for fn in re.findall(r'\bfunction\s+(\w+)', open(f, encoding='utf8', errors='replace').read()):
            src_funcs[fn] = os.path.basename(f)
    used = {'obj': {}, 'spr': {}, 'snd': {}, 'fn': {}}
    nums = []
    for k, t in code.items():
        s = strip(t)
        for m in re.finditer(r'\b(obj_\w+)\b', s):
            used['obj'].setdefault(m.group(1), set()).add(k)
        for m in re.finditer(r'\b(spr_\w+|bg_\w+|IMAGE_\w+)\b', s):
            used['spr'].setdefault(m.group(1), set()).add(k)
        for m in re.finditer(r'\b(snd_\w+|motor_\w+)\b', s):
            if not re.match(r'snd_(play|stop|loop|volume|pitch|free|init|is_playing|pause|resume)', m.group(1)):
                used['snd'].setdefault(m.group(1), set()).add(k)
        for m in re.finditer(r'(?<![.\w])([A-Za-z_]\w*)\s*\(', s):
            used['fn'].setdefault(m.group(1), set()).add(k)
        for i, l in enumerate(t.split('\n')):
            if re.search(r'(instance_create\w*\([^;]*,\s*\d{2,}\s*\)|instance_exists\(\d{2,}\)|i_ex\(\d{2,}\)|with \(\d{2,}\)|object_index == \d{2,}|snd_play\w*\(\d{2,}|sprite_index = \d{2,}|= \d{3,};\s*$|shader_set\(\d+|scr_var_delayed\("sprite_index", \d+)', l):
                nums.append('%s:%d: %s' % (k, i + 1, l.strip()[:140]))
    KW = set('if else while for do repeat until switch case default break continue return exit with var and or not div mod function new delete'.split())
    print('== objects')
    for o in sorted(used['obj']):
        st = 'IMPORT' if o in objs else ('CH3' if o in B['obj'] else ('MISSING' if o in S['obj'] else 'NOT-AN-OBJECT?'))
        print('  %-44s %-8s %s' % (o, st, sorted(used['obj'][o])[:2]))
    print('== sprites')
    for o in sorted(used['spr']):
        st = 'CH3' if o in B['spr'] else ('MISSING' if o in S['spr'] else 'NOT-A-SPRITE?')
        print('  %-44s %-8s %s %s' % (o, st, S['spr'].get(o, [''])[:3], sorted(used['spr'][o])[:1]))
    print('== sounds')
    for o in sorted(used['snd']):
        st = 'CH3' if o in B['snd'] else ('MISSING' if o in S['snd'] else 'NOT-A-SOUND?')
        print('  %-44s %-8s %s' % (o, st, sorted(used['snd'][o])[:1]))
    print('== functions (not runner builtins)')
    for f in sorted(used['fn']):
        if f in KW or f in rs:
            continue
        st = 'IMPORT' if f in scrs else ('CH3' if f in ch3_funcs else ('SRC:' + src_funcs[f] if f in src_funcs else '??'))
        if st == 'CH3' and '--all' not in sys.argv:
            continue
        print('  %-44s %-8s %s' % (f, st, sorted(used['fn'][f])[:2]))
    print('== numeric asset ids')
    for n in nums:
        print('  ' + n)


if __name__ == '__main__':
    main()
