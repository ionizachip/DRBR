"""DRBR 1.0.4 - the class of bug behind "DEVILSKNIFE ATTACK IS STILL BUGGED": a variable that the game's compiled code reads as a
FUNCTION (or an asset) of the same name. Chapter 3 has global functions centerx() / centery(); code taken from Chapter 1 kept
instance variables of those names - in the built data.win each read of them is "push.i [function]gml_Script_centerx".
  STATIC (the built data.win, disassembled with the release's own tools - fnclash_scan.csx):
    - the 1.0.4 build: no variable read as a function / an asset anywhere (FNCLASH: 0);
    - the 1.0.3 build: exactly the Devilsknives' two (centerx, centery in obj_jv_cscythe) - the bug, found by the check;
    - the 1.0.4 Devilsknife's code reads its middle as variables (push.v self.jv_centerx) and never the function;
  GENERATOR (fnclash.py over every boss port's generated code): no clashing variable left;
  EMULATOR: an instance variable named like a global function, read bare, is an error when the check is on (the harness has
  it on for every suite) and the variable when it is off.
Usage: python3 t_fnclash104.py [built.win] [1.0.3 built.win]"""
import sys, os, re, glob, subprocess, time, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, '/home/claude/scripts')
sys.path.insert(0, '/home/claude/gmlsim')
import fnclash
from gmlsim import Sim, GMError

NEW = sys.argv[1] if len(sys.argv) > 1 else '/home/claude/work/out/merged_full51.win'
OLD = sys.argv[2] if len(sys.argv) > 2 else '/home/claude/work/out/merged_full51_103.win'
FAILS = []
N = [0]


def ok(c, msg):
    N[0] += 1
    print(('ok   ' if c else 'FAIL ') + msg, flush=True)
    if not c:
        FAILS.append(msg)
    return c


def utmt(win, script, **env):
    e = dict(os.environ, DOTNET_ROOT='/home/claude/dotnet', PATH=os.environ['PATH'] + ':/home/claude/dotnet', **env)
    return subprocess.run(['/home/claude/utmt_cli/UndertaleModCli', 'load', win, '-s', script], env=e, capture_output=True, text=True,
                          stdin=subprocess.DEVNULL, timeout=1800)


t0 = time.time()
tmp = tempfile.mkdtemp(prefix='fnclash104_')
for win, label, want in ((NEW, '1.0.4 build', 0), (OLD, '1.0.3 build', 2)):
    if not os.path.exists(win):
        print('     (%s not found: %s NOT RUN)' % (win, label))
        continue
    out = os.path.join(tmp, os.path.basename(win) + '.txt')
    utmt(win, '/home/claude/scripts/fnclash_scan.csx', OUTF=out)
    t = open(out).read() if os.path.exists(out) else ''
    m = re.search(r'^FNCLASH: (\d+)$', t, re.M)
    names = sorted(re.findall(r'^FUNC-VS-VAR (\w+)', t, re.M) + re.findall(r'^ASSET-VS-VAR (\w+)', t, re.M))
    if want == 0:
        ok(m and int(m.group(1)) == 0, '%s: no variable the compiled code reads as a function or an asset (%s %s)' % (label, m.group(0) if m else 'no scan', names))
    else:
        ok(m and names == ['centerx', 'centery'] and 'gml_Object_obj_jv_cscythe_Step_0' in t,
           '%s: the check finds the bug - centerx / centery of the Devilsknives read as Chapter 3\'s functions (%s)' % (label, names))
# the Devilsknife's own code in the 1.0.4 build
dis = os.path.join(tmp, 'dis.csx')
open(dis, 'w').write('using System.IO;\nvar sb = new System.Text.StringBuilder();\nforeach (var n in new[] { "gml_Object_obj_jv_cscythe_Create_0", "gml_Object_obj_jv_cscythe_Step_0" })\n'
                     '{ var c = Data.Code.ByName(n); sb.AppendLine("==== " + n); sb.AppendLine(c.Disassemble(Data.Variables, Data.CodeLocals?.For(c))); }\n'
                     'File.WriteAllText(System.Environment.GetEnvironmentVariable("OUTF"), sb.ToString());\n')
if os.path.exists(NEW):
    o = os.path.join(tmp, 'dis.txt')
    utmt(NEW, dis, OUTF=o)
    d = open(o).read() if os.path.exists(o) else ''
    reads = len(re.findall(r'push\.v self\.jv_center[xy]', d))
    fn = re.findall(r'\[function\]gml_Script_center[xy]', d)
    ok(reads >= 8 and not fn, '1.0.4 build: the Devilsknives read their middle as variables (%d reads of jv_centerx / jv_centery, %d function references)' % (reads, len(fn)))
# the generators' own check over every boss port
for g in ('jevil_gen', 'gerson_gen', 'flowery_gen', 'spamton_gen', 'pink_gen'):
    fs = sorted(glob.glob('/home/claude/scripts/%s/*.gml' % g))
    c = fnclash.clashes([open(f, encoding='utf8').read() for f in fs])
    ok(fs and not c, '%s (%d files): no variable named like one of the game\'s functions (%s)' % (g, len(fs), sorted(c)))
jv = open('/home/claude/scripts/jevil_gen/gml_Object_obj_jv_cscythe_Step_0.gml', encoding='utf8').read()
ok('jv_centerx - lengthdir_x(length, dir)' in jv and not re.search(r'(?<![\w.])centerx\b', jv), 'jevil_gen: the Devilsknife swings round jv_centerx / jv_centery')
# the emulator's check
sim = Sim(seed=1)
sim.define_script('fnshadow', 'function centerx()\n{\n    return 12345;\n}\n')
sim.define_object('obj_t')
i = sim.create_instance('obj_t', 0, 0)
sim.run('with (%d) centerx = 320;' % i.id)
sim.fn_shadow_check = True
try:
    v = sim.eval('(function(){ var _v = 0; with (%d) _v = centerx; return _v; })()' % i.id)
    ok(False, 'emulator: the read of a variable named like a function is an error with the check on (it read %r)' % (v,))
except GMError as e:
    ok('global function' in str(e), 'emulator: the read of a variable named like a function is an error with the check on (%s)' % str(e)[:90])
sim.fn_shadow_check = False
v = sim.eval('(function(){ var _v = 0; with (%d) _v = centerx; return _v; })()' % i.id)
ok(v == 320, 'emulator: with the check off the variable is read (%r)' % (v,))
v = sim.eval('(function(){ var _v = 0; with (%d) _v = centerx(); return _v; })()' % i.id)
ok(v == 12345, 'emulator: a call is the function either way (%r)' % (v,))
print('fnclash104: %d checks, %d failed (%.0fs)' % (N[0], len(FAILS), time.time() - t0))
for f in FAILS:
    print('  -', f)
sys.exit(1 if FAILS else 0)
