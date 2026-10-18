"""Static lint for the hub GML: every called name must be a GM builtin, a function defined in the merged output, or a code-entry script."""
import re,os,sys
M='/home/claude/work/build/merged/'
BL=open('/home/claude/underminersteam/undertalemodtool/UndertaleModLib/Compiler/BuiltinList.cs',encoding='utf8').read()
builtin=set(re.findall(r'"([A-Za-z_][A-Za-z0-9_]*)"',BL))
defined=set();text={}
for f in os.listdir(M):
    t=open(M+f,encoding='utf8').read();text[f]=t
    for m in re.finditer(r'(?m)^\s*function\s+([A-Za-z_]\w*)\s*\(',t):defined.add(m.group(1))
    if f.startswith('gml_GlobalScript_'):defined.add(f[len('gml_GlobalScript_'):-4])
B='/home/claude/work/gml/base/CodeEntries/'
for f in os.listdir(B):
    if f.startswith('gml_GlobalScript_'):
        defined.add(f[len('gml_GlobalScript_'):-4])
        for m in re.finditer(r'(?m)^\s*function\s+([A-Za-z_]\w*)\s*\(',open(B+f,encoding='utf8',errors='replace').read()):defined.add(m.group(1))
assets=set()
for l in open('/home/claude/work/idx/merged.tsv',encoding='utf8'):assets.add(l.rstrip('\n').split('\t')[2])
assets|={'obj_knight_menu','obj_knight_prompt','obj_knight_ctrl','obj_knight_ghost_kris','obj_knight_ghost_susie','obj_knight_ghost_ralsei','obj_knight_herocc','obj_knight_omega',
          'obj_knight_twin','obj_knight_twin_bullet','obj_knight_bench','obj_knight_skinart','obj_knight_saov'}
# assets the build adds: copied from the mods / Chapter 5 (manifest) and packed atlases
import json
_man=json.load(open('/home/claude/work/build/assets.json'))['manifest']
for _k in ('sprites','sounds','objects','shaders'):
    for _m in _man.get(_k,[]):assets.add(_m['new'])
for _a in ('blue_atlas','hub_atlas','fl_atlas'):
    _p='/home/claude/work/out/%s.json'%_a
    if os.path.exists(_p):assets|=set(json.load(open(_p))['sprites'])
# objects the build makes from code files alone (a gml_Object_<name>_<event> file and no object of that name: a shell)
for _f in text:
    _m=re.match(r'gml_Object_(.+?)_(Create|Step|Alarm|Other|Collision|Destroy|CleanUp|PreCreate|Draw|KeyPress|Keyboard|Mouse)_',_f)
    if _m:assets.add(_m.group(1))
kw={'if','for','while','switch','return','with','repeat','until','function','catch','try','do','case','else','new','not','div','mod','and','or','xor','exit','break','continue','var','static','globalvar','enum','default','throw','delete'}
hubfiles=[f for f in text if 'knight_core' in f or re.search(r'obj_knight_(menu|prompt|ctrl|ghost)',f)]
# DRBR (build 53): the boss ports' code (Chapter 1-5 objects made by make_*.py, and the scripts they bring) - a Chapter 5 name
# left in them (snd_play_flowery passed to scr_script_delayed) compiles as an instance variable and stops the game
bossfiles=[f for f in text if re.search(r'gml_Object_obj_(jv|hj|fl|sn|pk)_|gml_GlobalScript_(kbr_(fl|jv|hj|sn|pk)_|scr_marker_|scr_dark_marker|draw_self_ext|shader_replace_simple)',f)]
extra=sys.argv[1:]
# method variables (name = function ... / static name = function / name: function in a struct) and instance variables
# assigned somewhere (bg_con = 0): calls / reads of those are not unknown names
methods=set();assigned=set()
_basetexts={}
for _f in os.listdir(B):
    if _f.endswith('.gml') and _f not in text:
        _bt=open(B+_f,encoding='utf8',errors='replace').read()
        if 'function' in _bt:_basetexts[_f]=_bt
for f,t0 in list(text.items())+list(_basetexts.items()):
    for m in re.finditer(r'(?<![\w.])([A-Za-z_]\w*)\s*(?:=|:)\s*function\b',t0):methods.add(m.group(1))
    for m in re.finditer(r'(?m)^\s*(?:var\s+|static\s+)?([A-Za-z_]\w*)\s*(?:=|\+=|-=)(?!=)',t0):assigned.add(m.group(1))
bad={}
for f in hubfiles+bossfiles+extra:
    t=text.get(f) or open(f).read()
    t=re.sub(r'//[^\n]*','',t);t=re.sub(r'"(?:\\.|[^"\\])*"','""',t)
    for m in re.finditer(r'(?<![\w.])([A-Za-z_]\w*)\s*\(',t):
        n=m.group(1)
        if n in kw or n in builtin or n in defined or n in methods or n in assigned:continue
        bad.setdefault(n,set()).add(f)
badas={}
for f in hubfiles+bossfiles+extra:
    t=text.get(f) or open(f).read()
    t=re.sub(r'//[^\n]*','',t);t=re.sub(r'"(?:\\.|[^"\\])*"','""',t)
    for m in re.finditer(r'(?<![\w.])((?:obj|spr|snd|room|scr|fnt|bg|shd)_[A-Za-z0-9_]+)\b',t):
        n=m.group(1)
        if n in assets or n in defined or n in builtin or n in assigned or n in methods:continue
        badas.setdefault(n,set()).add(f)
# a function passed by name (scr_script_delayed(f, ...), script_execute(f, ...), method(x, f)): it must exist too
badfv={}
for f in hubfiles+bossfiles+extra:
    t=text.get(f) or open(f).read()
    t=re.sub(r'//[^\n]*','',t);t=re.sub(r'"(?:\\.|[^"\\])*"','""',t)
    for m in re.finditer(r'(?<![\w.])(?:scr_script_delayed|script_execute|script_execute_ext|scr_delay_func)\s*\(\s*([A-Za-z_]\w*)\s*[,)]',t):
        n=m.group(1)
        if n in kw or n in builtin or n in defined or n in methods or n in assigned or n.startswith('arg') or n=='function':continue
        badfv.setdefault(n,set()).add(f)
    for m in re.finditer(r'(?<![\w.])method\s*\([^,()]+,\s*([A-Za-z_]\w*)\s*\)',t):
        n=m.group(1)
        if n in kw or n in builtin or n in defined or n in methods or n in assigned:continue
        badfv.setdefault(n,set()).add(f)
for n,fs in sorted(badfv.items()):print('UNKNOWN FUNCTION VALUE',n,sorted(fs)[:3])
for n,fs in sorted(badas.items()):print('UNKNOWN ASSET',n,sorted(fs)[:3])
for n,fs in sorted(bad.items()):print('UNRESOLVED',n,sorted(fs)[:3])
print('lint done; unresolved names:',len(bad)+len(badas)+len(badfv))

# ---- name collisions (added in build 44) ----
# GameMaker binds every script function to a global variable of the same name, so global.X with X a function name reads
# (or overwrites) the function itself. Build 43 crashed in the real game because of exactly this (function kfo() and
# global.kfo). A local var / parameter named like a function also shadows that function inside its body.
def _strip(t):
    t=re.sub(r'/\*.*?\*/','',t,flags=re.S);t=re.sub(r'//[^\n]*','',t);return re.sub(r'"(?:\\.|[^"\\])*"','""',t)
hubfuncs=set()
for f in hubfiles:
    for m in re.finditer(r'(?m)^\s*function\s+([A-Za-z_]\w*)\s*\(',text[f]):hubfuncs.add(m.group(1))
basefuncs=set()
for f in os.listdir(B):
    if f.startswith('gml_GlobalScript_'):
        basefuncs.add(f[len('gml_GlobalScript_'):-4])
        for m in re.finditer(r'(?m)^\s*function\s+([A-Za-z_]\w*)\s*\(',open(B+f,encoding='utf8',errors='replace').read()):basefuncs.add(m.group(1))
allfuncs=hubfuncs|basefuncs|{f[len('gml_GlobalScript_'):-4] for f in text if f.startswith('gml_GlobalScript_')}
def _globals(t):
    s=set(re.findall(r'(?<![\w.])global\.([A-Za-z_]\w*)',t))
    for m in re.finditer(r'(?m)^\s*globalvar\s+([^;\n]+)',t):s|=set(re.findall(r'[A-Za-z_]\w*',m.group(1)))
    return s
hubglob={};baseglob={}
for f in hubfiles:
    for g in _globals(_strip(text[f])):hubglob.setdefault(g,f)
for f in text:
    if f in hubfiles:continue
    for g in _globals(_strip(text[f])):baseglob.setdefault(g,f)
for f in os.listdir(B):
    if f in text:continue
    for g in _globals(_strip(open(B+f,encoding='utf8',errors='replace').read())):baseglob.setdefault(g,f)
ncol=0
for g in sorted(hubglob):
    if g in allfuncs:print('COLLISION global.%s (used in %s) is also a function name'%(g,hubglob[g]));ncol+=1
for g in sorted(hubfuncs):
    if g in baseglob:print('COLLISION hub function %s is also a base-game global (global.%s in %s)'%(g,g,baseglob[g]));ncol+=1
basecol=sorted(g for g in baseglob if g in basefuncs and g not in hubfuncs)
if basecol:print('note: base-game global/function name overlaps (shipped that way, not checked):',len(basecol))
# locals, statics and parameters that shadow a function (hub, base or builtin)
shadow_ok={'argument'}
_blf=set(re.findall(r'DefineFunction\("([A-Za-z_]\w*)"',BL))|set(re.findall(r'Functions\["([A-Za-z_]\w*)"\]',BL))
_blc=set(re.findall(r'Constants\["([A-Za-z_]\w*)"\]',BL))|set(re.findall(r'DefineConstant\("([A-Za-z_]\w*)"',BL))
_blv=set(re.findall(r'Define(?:Global|GlobalAutoArray|InstanceVar)\("([A-Za-z_]\w*)"',BL))
for f in hubfiles:
    t=_strip(text[f])
    names=[]
    for m in re.finditer(r'(?<![\w.])(?:var|static)\s+([^;]+?)(?:;|\n)',t):
        decl=m.group(1);prev=None
        while prev!=decl:prev=decl;decl=re.sub(r'\([^()]*\)|\[[^\[\]]*\]|\{[^{}]*\}','',decl)
        for part in decl.split(','):
            mm=re.match(r'\s*([A-Za-z_]\w*)\s*(?:=|$)',part)
            if mm:names.append(mm.group(1))
    for m in re.finditer(r'(?m)^\s*function\s+[A-Za-z_]\w*\s*\(([^)]*)\)',t):
        for part in m.group(1).split(','):
            mm=re.match(r'\s*([A-Za-z_]\w*)',part)
            if mm:names.append(mm.group(1))
    for n in sorted(set(names)):
        if n in shadow_ok:continue
        if n in allfuncs or n in _blf:
            print('SHADOW local/param %s in %s is also a function name'%(n,f));ncol+=1
        elif n in _blc or n in _blv or n in assets:
            print('SHADOW local/param %s in %s is also a builtin constant/variable or an asset'%(n,f));ncol+=1
# a hub function named like an asset (sprite, sound, object, room...): the compiler would pick one of the two
for g in sorted(hubfuncs):
    if g in assets:print('COLLISION hub function %s is also an asset name'%g);ncol+=1
# bare assignments (instance variables) named like a function: in GameMaker the name then means the function
for f in hubfiles:
    t=_strip(text[f])
    for m in re.finditer(r'(?m)^\s*([A-Za-z_]\w*)\s*(?:=|\+=|-=|\*=|/=)(?!=)',t):
        n=m.group(1)
        if n in allfuncs or n in _blf:
            print('SHADOW instance variable %s in %s line %d is also a function name'%(n,f,t.count('\n',0,m.start())+1));ncol+=1
# reading .id off a struct: id is a read-only built-in instance variable, so the game's own structs never use it as a
# field (relay messages that carry "id" are read by name with kfo_jn)
for f in hubfiles:
    t=_strip(text[f])
    for m in re.finditer(r'(?<!\bother)\.id\b',t):
        # (build 50: other.id - the asking / making instance's id - is an instance read, not a struct field)
        print('BUILTIN-FIELD .id read in %s line %d'%(f,t.count('\n',0,m.start())+1));ncol+=1
# indexing what a call returns, f(...)[i]: the compiler the build uses (UndertaleModTool's) rejects it ("Invalid expression
# on accessor") and the whole script fails to import - build 45 found it this way. Put the result in a local first.
for f in hubfiles:
    t=_strip(text[f])
    for m in re.finditer(r'\)\s*\[(?!\|)',t):
        print('CALL-INDEX f(...)[i] in %s line %d (the build compiler rejects it)'%(f,t.count('\n',0,m.start())+1));ncol+=1
print('name collisions:',ncol)

# ---- ds accessors (added in build 46) ----
# The compiler the build uses (UndertaleModTool's) DROPS the ds accessors: l[| i], m[? k], g[# x, y], a[@ i], s[$ k] are
# compiled as plain array reads / writes (no error at build time), and the game then stops with "trying to index a variable
# which is not an array". Build 45 crashed in the real game this way (kbr_list_shuffle in the rotating slash attack). Every
# code entry the build imports is checked, not only the hub's: ds_list_find_value / ds_list_set / ds_map_find_value /
# ds_grid_get / variable_struct_get ... instead.
nacc=0
for f in sorted(text):
    t=_strip(text[f])
    for m in re.finditer(r'\[\s*[|?#@$]',t):
        print('DS-ACCESSOR %s in %s line %d (the build compiler drops it: use the ds_* / variable_struct_* function)'%(m.group(0),f,t.count('\n',0,m.start())+1));nacc+=1
print('ds accessors:',nacc)

# ---- Chapter 3's own runtime (added in build 45) ----
# UndertaleModTool's builtin list is GameMaker's newest; Chapter 3's runner (DELTARUNE.exe) is older. Every builtin the hub
# calls must be in the runner itself (its function names, read once from the exe as strings into runner_strings.txt).
# Build 45 found array_shuffle this way (not in Chapter 3's runtime).
RS='/home/claude/work/runner_strings.txt'
if os.path.exists(RS):
    _rs=set(l.strip() for l in open(RS,encoding='latin1'))
    _short={'abs','cos','sin','tan','exp','ln','max','min','ord','sqr','chr','mod','div','int','log'}  # under 4 letters: not in the strings dump
    nrun=0
    for f in hubfiles+extra:
        t=_strip(text.get(f) or open(f).read())
        for m in re.finditer(r'(?<![\w.])([A-Za-z_]\w*)\s*\(',t):
            n=m.group(1)
            if n in kw or n in defined or n not in builtin or n in _rs or n in _short:continue
            print('RUNNER-MISSING builtin %s (%s line %d) is not in Chapter 3\'s runner'%(n,f,t.count('\n',0,m.start())+1));nrun+=1
    print('runner builtins missing:',nrun)
else:
    print('runner check skipped (no runner_strings.txt)')
# Build 52: an enum read in a file that does not declare it (Chapter 1's e__VW in imported code): the compiler takes it for an
# instance variable and the game stops with "not set before reading it" (the emulator does not).
import glob as _g
nen=0
for f in sorted(_g.glob('/home/claude/work/build/merged/*.gml')):
    t=_strip(open(f,errors='ignore').read())
    for en in set(re.findall(r'\b(e__\w+)\.\w+',t)):
        if not re.search(r'\benum\s+'+en+r'\b',t):
            print('ENUM-UNDECLARED %s in %s'%(en,os.path.basename(f)));nen+=1
print('undeclared enums:',nen)
# DRBR: an accessor on an expression - an array literal or a call's result indexed directly ([1, 2][i], f()[i]): the
# emulator takes it, the build's compiler stops ("Invalid expression on accessor", Gerson's hair table in this update).
nexp=0
for f in sorted(_g.glob('/home/claude/work/build/merged/*.gml')):
    t=_strip(open(f,errors='ignore').read())
    for m in re.finditer(r'\]\s*\[',t):
        # walk back to the matching '[' of the first bracket pair: an array literal when what precedes it is not a name / ] / )
        i=m.start(); d=0; j=i
        while j>=0:
            c=t[j]
            if c==']': d+=1
            elif c=='[':
                d-=1
                if d==0: break
            j-=1
        k=j-1
        while k>=0 and t[k] in ' \t': k-=1
        if j>0 and k>=0 and not (t[k].isalnum() or t[k] in '_])'):
            print('ACCESSOR-ON-LITERAL in %s line %d'%(os.path.basename(f),t.count('\n',0,m.start())+1));nexp+=1
    for m in re.finditer(r'(?<![\w.])([A-Za-z_]\w*)\s*\(([^()]|\([^()]*\))*\)\s*\[',t):
        if m.group(1) in kw: continue
        print('ACCESSOR-ON-CALL %s( )[ in %s line %d'%(m.group(1),os.path.basename(f),t.count('\n',0,m.start())+1));nexp+=1
    # (a call's result's field, knight_reg(r).name, compiles: the build has hundreds)
print('accessors on expressions:',nexp)
# DRBR: the decompiler's raw asset numbers in the bosses' imported code - a number where an object belongs (Chapter 2's NEO
# finale had "instance_exists(obj_shake) ? 196 : instance_create(...)": object 196 is another object in the built game)
nraw=0
for f in bossfiles:
    t=_strip(text.get(f) or open(f,errors='ignore').read())
    for m in re.finditer(r'instance_exists\((obj_\w+)\)\s*\?\s*\d+\s*:|with\s*\(\s*\d+\s*\)|instance_(?:exists|find|number|destroy)\(\s*\d+\s*[,)]',t):
        print('RAW ASSET NUMBER in %s line %d: %s'%(os.path.basename(f),t.count('\n',0,m.start())+1,m.group(0)));nraw+=1
print('raw asset numbers:',nraw)
