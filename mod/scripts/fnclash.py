"""DRBR 1.0.4: an imported boss's instance variables that Chapter 3 has a global FUNCTION of the same name for.

Chapter 3 (GameMaker 2023) has helper functions such as centerx() / centery(). Code taken from another chapter that keeps an
instance variable of that name (Chapter 1's obj_centerscythe: centerx / centery, the middle its Devilsknives swing round)
compiles in Chapter 3's data.win to a FUNCTION reference wherever it READS the name ("push.i [function]gml_Script_centerx"),
while its assignments still write the variable: Jevil's Devilsknives swung round a point about 100000 pixels away - off the
screen - in every real game (the emulator looks names up at run time, variable first, and never saw it).

This module finds such names in a port's code and renames them (bare reads and writes, and "inst.name" accesses) to
<prefix>name; names the code only CALLS (name(...)) are Chapter 3's functions and stay. The build itself is checked too:
fnclash_scan.csx disassembles every code entry of the built data.win and reports a function pushed where a variable of that
name is assigned anywhere in object / room code (the release scripts refuse a build with one)."""
import os, re, glob, sys
sys.path.insert(0, '/home/claude/scripts')
import names

VANILLA = '/mnt/user-data/uploads/data.win'
TEMPLATES = '/home/claude/scripts/gml_templates_v6'
_F = []


def target_functions():
    """every global function name the built game has: Chapter 3's (its SCPT chunk: gml_Script_<name>) and DRBR's own"""
    if not _F:
        d, ch = names.load(VANILLA)
        f = set(s[len('gml_Script_'):] for s in names.names(d, ch, 'SCPT') if s.startswith('gml_Script_'))
        for p in glob.glob(os.path.join(TEMPLATES, '*.gml')):
            f |= set(re.findall(r'^\s*function\s+(\w+)\s*\(', open(p, encoding='utf8').read(), re.M))
        _F.append(f)
    return _F[0]


def _strip(t):
    """the code without its strings and comments (same length: offsets stay)"""
    out = list(t)
    i = 0
    n = len(t)
    while i < n:
        c = t[i]
        if c == '"':
            j = i + 1
            while j < n and t[j] != '"':
                j += 2 if t[j] == '\\' else 1
            for k in range(i, min(j + 1, n)):
                if out[k] != '\n':
                    out[k] = ' '
            i = j + 1
        elif t.startswith('//', i):
            j = t.find('\n', i)
            j = n if j < 0 else j
            for k in range(i, j):
                out[k] = ' '
            i = j
        elif t.startswith('/*', i):
            j = t.find('*/', i + 2)
            j = n if j < 0 else j + 2
            for k in range(i, j):
                if out[k] != '\n':
                    out[k] = ' '
            i = j
        else:
            i += 1
    return ''.join(out)


_ASSIGN = re.compile(r'(?<![\w$])(?:(\w+)\s*\.\s*)?([A-Za-z_]\w*)\s*(?:\+\+|--|[-+*/|&^]?=(?!=))')


def clashes(texts, funcs=None):
    """the names the code keeps as instance variables (assigned: "name = ...", "name += ...", "inst.name = ...", "name++";
    not "var name") that are also global functions of the built game"""
    funcs = target_functions() if funcs is None else funcs
    found = set()
    for t in texts:
        s = _strip(t)
        local = set(re.findall(r'\bvar\s+([A-Za-z_]\w*)', s))
        for m in re.finditer(r'\bvar\s+([^;]*)', s):
            local |= set(re.findall(r'(?:^|,)\s*([A-Za-z_]\w*)', m.group(1)))
        for m in _ASSIGN.finditer(s):
            nm = m.group(2)
            if nm in funcs and nm not in local and not re.match(r'\s*function\b', s[max(0, m.start() - 9):m.start()]):
                found.add(nm)
    return found


def rename(t, ren):
    """every use of the names in ren that is not a call - bare or after a '.' - becomes the new name (strings and comments
    are left alone)"""
    if not ren:
        return t
    s = _strip(t)
    rx = re.compile(r'(?<![\w$])(%s)\b(?!\s*\()' % '|'.join(re.escape(k) for k in sorted(ren, key=len, reverse=True)))
    out = []
    last = 0
    for m in rx.finditer(s):
        out.append(t[last:m.start()])
        out.append(ren[m.group(1)])
        last = m.end()
    out.append(t[last:])
    return ''.join(out)


def fix_files(paths, prefix, report=None):
    """rename the clashing variables in a port's generated files (in place); returns {old: new}"""
    texts = {p: open(p, encoding='utf8').read() for p in paths}
    found = clashes(list(texts.values()))
    ren = {n: prefix + n for n in sorted(found)}
    for p, t in texts.items():
        u = rename(t, ren)
        if u != t:
            open(p, 'w', encoding='utf8').write(u)
    if report is not None:
        report.update(ren)
    return ren


if __name__ == '__main__':
    # a look at every generated port (nothing written): python3 fnclash.py
    for d in ('jevil_gen', 'gerson_gen', 'flowery_gen', 'spamton_gen', 'pink_gen'):
        fs = sorted(glob.glob('/home/claude/scripts/%s/*.gml' % d))
        print(d, len(fs), 'files: clashing variables', sorted(clashes([open(f, encoding='utf8').read() for f in fs])))
