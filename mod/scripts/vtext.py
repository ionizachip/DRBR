"""Extract one variant's code from a merged (switch-dispatched) object event file.
usage: python3 vtext.py <entry or file> <variant key|index> [outfile]
       python3 vtext.py --dump <outdir> [pattern]   (writes <outdir>/<key>/<entry>.gml for every merged object entry matching pattern)"""
import os, re, sys, json
M = '/home/claude/work/build/merged/'
KEYS = [v['key'] for v in json.load(open('/home/claude/scripts/knights.json'))['variants']]
HEAD = re.compile(r'^switch \((global\.knight_variant|\(variable_instance_exists\(id, "knight_v"\) \? knight_v : global\.knight_variant\))\)\s*$')


def split_cases(text):
    """-> ({variant index: body}, default body) or None when the file is not a dispatch switch"""
    lines = text.split('\n')
    # the switch may be preceded by 'knight_v = global.knight_variant;' (Create of objects that remember their variant)
    pre = []
    i = 0
    while i < len(lines) and not HEAD.match(lines[i]):
        pre.append(lines[i])
        i += 1
    if i >= len(lines) or i + 1 >= len(lines) or lines[i + 1].strip() != '{':
        return None
    i += 2
    out = {}
    labels = []
    dflt = None
    while i < len(lines):
        ln = lines[i]
        m = re.match(r'^    case (\d+):\s*$', ln)
        if m:
            labels.append(int(m.group(1)))
            i += 1
            continue
        if re.match(r'^    default:\s*$', ln):
            labels.append('default')
            i += 1
            continue
        if ln == '    {':
            body = []
            i += 1
            while i < len(lines) and lines[i] != '    }':
                body.append(lines[i][8:] if lines[i].startswith('        ') else lines[i].lstrip())
                i += 1
            txt = '\n'.join(pre + body)
            for lb in labels:
                if lb == 'default':
                    dflt = txt
                else:
                    out[lb] = txt
            labels = []
            i += 1
            continue
        if ln == '}':
            break
        i += 1
    return out, dflt


def vtext(entry, key):
    f = entry if entry.endswith('.gml') else M + entry + '.gml'
    if not os.path.exists(f):
        f = M + os.path.basename(f)
    t = open(f, encoding='utf8').read()
    idx = key if isinstance(key, int) else KEYS.index(key)
    r = split_cases(t)
    if r is None:
        return t
    cases, dflt = r
    return cases.get(idx, dflt)


if __name__ == '__main__':
    if sys.argv[1] == '--dump':
        od = sys.argv[2]
        pat = re.compile(sys.argv[3]) if len(sys.argv) > 3 else None
        n = 0
        for fn in sorted(os.listdir(M)):
            if not fn.startswith('gml_Object_') or (pat and not pat.search(fn)):
                continue
            for k in KEYS:
                os.makedirs(od + '/' + k, exist_ok=True)
                open(od + '/' + k + '/' + fn, 'w', encoding='utf8').write(vtext(fn, k))
            n += 1
        print('dumped', n)
    else:
        k = sys.argv[2]
        k = int(k) if k.isdigit() else k
        t = vtext(sys.argv[1], k)
        if len(sys.argv) > 3:
            open(sys.argv[3], 'w').write(t)
        else:
            print(t)
