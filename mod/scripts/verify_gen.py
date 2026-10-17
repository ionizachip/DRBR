"""DRBR: every object / sprite / sound / function a generated boss folder names exists (in the build, in the manifest's new names,
as an object of the folder, or as a function of the hub's templates). Usage: python3 verify_gen.py <gen dir> [<gen dir> ...]"""
import os, re, sys, glob, json
sys.path.insert(0, '/home/claude/scripts')
from make_boss import table, CH3, ASSETS
B = table(CH3)
A = json.load(open(ASSETS))['manifest']
new = {'obj': set(m['new'] for m in A['objects']), 'spr': set(m['new'] for m in A['sprites']), 'snd': set(m['new'] for m in A['sounds'])}
funcs = set()
for f in glob.glob('/home/claude/scripts/gml_templates_v6/*.gml') + glob.glob('/home/claude/work/src/built/code/gml_GlobalScript_*.gml'):
    funcs |= set(re.findall(r'\bfunction\s+(\w+)', open(f, encoding='utf8', errors='replace').read()))
rs = set(l.strip() for l in open('/home/claude/work/runner_strings.txt', encoding='latin1'))
bad = 0
for d in sys.argv[1:]:
    files = {os.path.basename(f): open(f, encoding='utf8').read() for f in glob.glob(os.path.join(d, '*.gml'))}
    objs_here = set(re.match(r'gml_Object_(.+?)_(Create|Step|Draw|Alarm|Other|Destroy|Collision|CleanUp)_', n).group(1) for n in files if n.startswith('gml_Object_'))
    for n, t in files.items():
        funcs |= set(re.findall(r'\bfunction\s+(\w+)', t))
    for n, t in sorted(files.items()):
        s = re.sub(r'"(?:\\.|[^"\\])*"', '""', t)
        s = re.sub(r'//[^\n]*', '', s)
        for o in sorted(set(re.findall(r'\b(obj_\w+)\b', s))):
            if o not in B['obj'] and o not in new['obj'] and o not in objs_here:
                print('OBJ  ', n, o); bad += 1
        for o in sorted(set(re.findall(r'\b(spr_\w+|bg_\w+|IMAGE_\w+)\b', s))):
            if o not in B['spr'] and o not in new['spr']:
                print('SPR  ', n, o); bad += 1
        for o in sorted(set(re.findall(r'\b(snd_\w+|motor_\w+)\b', s))):
            if re.match(r'snd_(play|stop|loop|volume|pitch|free|init|is_playing|pause|resume)\w*$', o):
                continue
            if o not in B['snd'] and o not in new['snd']:
                print('SND  ', n, o); bad += 1
        for f in sorted(set(re.findall(r'(?<![.\w])([A-Za-z_]\w*)\s*\(', s))):
            if f in funcs or f in rs or f in ('if', 'while', 'for', 'with', 'switch', 'return', 'repeat', 'until', 'abs', 'min', 'max', 'sin', 'cos', 'tan', 'sqr', 'sqrt', 'exp', 'ln', 'log', 'ord', 'chr', 'int', 'mod', 'div', 'not', 'and', 'or'):
                continue
            print('FN   ', n, f); bad += 1
print('verify_gen: %d problems' % bad)
sys.exit(1 if bad else 0)
